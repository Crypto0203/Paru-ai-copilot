"""
PARU PRO — Advanced System Tools
Full Windows PC control: 40+ app launchers, power management, volume, brightness,
Wi-Fi info, folder navigation, and generic command execution.
"""

import os
import re
import time
import ctypes
import subprocess
import datetime
import socket
import psutil

# Safe imports for audio/brightness
try:
    from pycaw.pycaw import AudioUtilities
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except Exception:
    SBC_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════

def get_system_status() -> dict:
    """Returns current battery, CPU usage, RAM usage, and current time."""
    now = datetime.datetime.now()
    battery = psutil.sensors_battery()
    battery_info = f"{battery.percent}% ({'Charging' if battery.power_plugged else 'On Battery'})" if battery else "Desktop (AC Powered)"
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    ram_info = f"{ram.percent}% ({round(ram.used / (1024**3), 1)}GB / {round(ram.total / (1024**3), 1)}GB)"

    return {
        "status": "success",
        "current_time": now.strftime("%I:%M %p, %A, %B %d, %Y"),
        "battery": battery_info,
        "cpu_usage": f"{cpu_percent}%",
        "ram_usage": ram_info
    }


# ══════════════════════════════════════════════════════════════════════════════
#  VOLUME CONTROL (Modern pycaw EndpointVolume API)
# ══════════════════════════════════════════════════════════════════════════════

def _init_com():
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass


def set_volume(level: int) -> str:
    """Sets master system volume level (0 to 100)."""
    level = max(0, min(100, int(level)))
    _init_com()
    if not PYCAW_AVAILABLE:
        return f"[Simulated] Volume set to {level}% (pycaw not loaded)"
    try:
        speakers = AudioUtilities.GetSpeakers()
        speakers.EndpointVolume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"System volume set to {level}%"
    except Exception as e:
        return f"Failed to set volume: {e}"


def adjust_volume(delta: int = -20) -> str:
    """Increases or decreases system volume by delta percentage (e.g. -20 for decrease, +20 for increase)."""
    _init_com()
    if not PYCAW_AVAILABLE:
        return f"[Simulated] Volume adjusted by {delta}%"
    try:
        speakers = AudioUtilities.GetSpeakers()
        current = round(speakers.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
        new_val = max(0, min(100, current + int(delta)))
        speakers.EndpointVolume.SetMasterVolumeLevelScalar(new_val / 100.0, None)
        return f"System volume adjusted from {current}% to {new_val}%"
    except Exception as e:
        return f"Failed to adjust volume: {e}"


def adjust_app_volume(app_name: str, delta: int = -20) -> str:
    """Adjusts volume for a specific running application (e.g. Chrome, Spotify, Edge, VLC)."""
    _init_com()
    if not PYCAW_AVAILABLE:
        return adjust_volume(delta)
    try:
        sessions = AudioUtilities.GetAllSessions()
        target = app_name.lower().replace(".exe", "").strip()
        matched = False
        res_msg = []
        for session in sessions:
            if session.Process:
                pname = session.Process.name().lower()
                if target in pname:
                    vol_ctrl = session.SimpleAudioVolume
                    curr = round(vol_ctrl.GetMasterVolume() * 100)
                    new_v = max(0, min(100, curr + delta))
                    vol_ctrl.SetMasterVolume(new_v / 100.0, None)
                    matched = True
                    display_name = session.Process.name().replace(".exe", "").title()
                    res_msg.append(f"{display_name} volume adjusted to {new_v}%")
        if matched:
            return "; ".join(res_msg)
        # Fallback to system volume if app is not actively generating audio
        return adjust_volume(delta)
    except Exception as e:
        return adjust_volume(delta)


def set_app_volume(app_name: str, level: int) -> str:
    """Sets exact volume level (0-100) for a specific running application."""
    _init_com()
    level = max(0, min(100, int(level)))
    if not PYCAW_AVAILABLE:
        return set_volume(level)
    try:
        sessions = AudioUtilities.GetAllSessions()
        target = app_name.lower().replace(".exe", "").strip()
        matched = False
        for session in sessions:
            if session.Process and target in session.Process.name().lower():
                session.SimpleAudioVolume.SetMasterVolume(level / 100.0, None)
                matched = True
        if matched:
            return f"{app_name.title()} volume set to {level}%"
        return set_volume(level)
    except Exception:
        return set_volume(level)


def get_volume() -> str:
    """Gets current master system volume level."""
    _init_com()
    if not PYCAW_AVAILABLE:
        return "Volume info unavailable (pycaw not loaded)"
    try:
        speakers = AudioUtilities.GetSpeakers()
        current = round(speakers.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
        return f"Current system volume is {current}%"
    except Exception as e:
        return f"Failed to get volume: {e}"


def mute_volume(mute: bool = True) -> str:
    """Mutes or unmutes master audio."""
    _init_com()
    if not PYCAW_AVAILABLE:
        return f"[Simulated] Volume {'muted' if mute else 'unmuted'}"
    try:
        speakers = AudioUtilities.GetSpeakers()
        speakers.EndpointVolume.SetMute(1 if mute else 0, None)
        return "Audio muted" if mute else "Audio unmuted"
    except Exception as e:
        return f"Failed to toggle mute: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  BRIGHTNESS CONTROL
# ══════════════════════════════════════════════════════════════════════════════

def set_brightness(level: int) -> str:
    """Sets screen brightness percentage (0 to 100)."""
    level = max(0, min(100, level))
    if not SBC_AVAILABLE:
        return f"[Simulated] Brightness set to {level}%"
    try:
        sbc.set_brightness(level)
        return f"Screen brightness set to {level}%"
    except Exception as e:
        return f"Failed to set brightness: {e}"


def adjust_brightness(delta: int = -20) -> str:
    """Increases or decreases screen brightness by delta percentage."""
    if not SBC_AVAILABLE:
        return f"[Simulated] Brightness adjusted by {delta}%"
    try:
        current = sbc.get_brightness()[0]
        new_val = max(0, min(100, current + int(delta)))
        sbc.set_brightness(new_val)
        return f"Screen brightness adjusted from {current}% to {new_val}%"
    except Exception as e:
        return f"Failed to adjust brightness: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  POWER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def lock_workstation() -> str:
    """Locks the Windows PC."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked successfully."
    except Exception as e:
        return f"Failed to lock workstation: {e}"


def shutdown_pc(delay: int = 5) -> str:
    """Shuts down the PC after a delay (in seconds)."""
    try:
        subprocess.Popen(f"shutdown /s /t {delay}", shell=True)
        return f"PC will shut down in {delay} seconds. Say 'cancel shutdown' to abort."
    except Exception as e:
        return f"Failed to shutdown: {e}"


def restart_pc(delay: int = 5) -> str:
    """Restarts the PC after a delay (in seconds)."""
    try:
        subprocess.Popen(f"shutdown /r /t {delay}", shell=True)
        return f"PC will restart in {delay} seconds. Say 'cancel shutdown' to abort."
    except Exception as e:
        return f"Failed to restart: {e}"


def cancel_shutdown() -> str:
    """Cancels a pending shutdown or restart."""
    try:
        subprocess.Popen("shutdown /a", shell=True)
        return "Shutdown/restart cancelled successfully."
    except Exception as e:
        return f"Failed to cancel shutdown: {e}"


def sleep_pc() -> str:
    """Puts the PC to sleep."""
    try:
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return "PC is going to sleep."
    except Exception as e:
        return f"Failed to sleep: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  APPLICATION LAUNCHER — 40+ Windows Apps
# ══════════════════════════════════════════════════════════════════════════════

# Comprehensive app map with multiple launch strategies
APP_REGISTRY = {
    # Microsoft Office Suite
    "outlook": [
        r'"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"',
        r'"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE"',
        os.path.expandvars(r'"%LOCALAPPDATA%\Microsoft\WindowsApps\olk.exe"'),
        "OUTLOOK.EXE",
        "start outlook:",
        'powershell -Command "Start-Process outlook:"'
    ],
    "teams": [
        os.path.expandvars(r'"%LOCALAPPDATA%\Microsoft\WindowsApps\ms-teams.exe"'),
        "ms-teams.exe",
        "msteams.exe",
        "start msteams:",
        'powershell -Command "Start-Process ms-teams.exe"',
        'powershell -Command "Start-Process msteams:"'
    ],
    "microsoft teams": [
        os.path.expandvars(r'"%LOCALAPPDATA%\Microsoft\WindowsApps\ms-teams.exe"'),
        "ms-teams.exe",
        "start msteams:"
    ],
    "word":          [r'"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"', "start winword:", "WINWORD.EXE"],
    "excel":         [r'"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"', "start excel:", "EXCEL.EXE"],
    "powerpoint":    [r'"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"', "start powerpnt:", "POWERPNT.EXE"],
    "onenote":       ["start onenote:", "ONENOTE.EXE"],
    "access":        ["MSACCESS.EXE"],

    # Browsers
    "chrome":        [r'"C:\Program Files\Google\Chrome\Application\chrome.exe"', "chrome.exe", "start chrome:"],
    "edge":          [r'"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"', "msedge.exe", "start microsoft-edge:"],
    "firefox":       ["firefox.exe"],
    "brave":         ["brave.exe"],
    "opera":         ["opera.exe"],

    # Development Tools
    "vs code":       ["code.cmd", "code"],
    "vscode":        ["code.cmd", "code"],
    "visual studio": ["devenv.exe"],
    "git bash":      ["git-bash.exe"],
    "postman":       ["Postman.exe"],
    "android studio":["studio64.exe"],

    # System & Utilities
    "notepad":       ["notepad.exe"],
    "calculator":    ["calc.exe"],
    "calc":          ["calc.exe"],
    "paint":         ["mspaint.exe"],
    "wordpad":       ["wordpad.exe"],
    "snipping tool": ["SnippingTool.exe", "snippingtool.exe"],
    "snip":          ["SnippingTool.exe"],
    "task manager":  ["taskmgr.exe"],
    "taskmgr":       ["taskmgr.exe"],
    "control panel": ["control.exe"],
    "settings":      ["start ms-settings:"],
    "device manager":["devmgmt.msc"],
    "disk management":["diskmgmt.msc"],
    "registry":      ["regedit.exe"],
    "event viewer":  ["eventvwr.msc"],
    "services":      ["services.msc"],
    "cmd":           ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell":    ["powershell.exe"],
    "terminal":      ["wt.exe", "cmd.exe"],
    "file explorer":  ["explorer.exe"],
    "explorer":      ["explorer.exe"],

    # Communication & Social
    "whatsapp":      ["start whatsapp:", "WhatsApp.exe"],
    "telegram":      ["start tg:", "Telegram.exe"],
    "discord":       ["Discord.exe", "start discord:"],
    "slack":         ["slack.exe"],
    "zoom":          ["Zoom.exe"],
    "skype":         ["Skype.exe", "start skype:"],

    # Media & Entertainment
    "spotify":       ["start spotify:", "Spotify.exe"],
    "vlc":           ["vlc.exe"],
    "obs":           ["obs64.exe"],
    "audacity":      ["Audacity.exe"],
    "photos":        ["start ms-photos:"],

    # Gaming
    "steam":         ["steam.exe", "start steam:"],
    "epic games":    ["EpicGamesLauncher.exe"],

    # Productivity
    "notion":        ["Notion.exe"],
    "obsidian":      ["Obsidian.exe"],
    "figma":         ["Figma.exe"],
}


def bring_window_to_front(keyword: str) -> bool:
    """
    Finds any running window matching keyword and forces it into the active foreground.
    Uses Win32 AllowSetForegroundWindow + ShowWindow(RESTORE) + Alt-key release trick.
    """
    try:
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        found = []

        def callback(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if keyword.lower() in buff.value.lower():
                        found.append(hwnd)
            return True

        cb = WNDENUMPROC(callback)
        user32.EnumWindows(cb, 0)
        for hwnd in found:
            # Grant foreground permission
            user32.AllowSetForegroundWindow(-1)
            # Restore window if minimized
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            # Alt-key trick to bypass Windows foreground lock
            VK_MENU = 0x12
            KEYEVENTF_EXTENDEDKEY = 0x0001
            KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY, 0)
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SwitchToThisWindow(hwnd, True)
            return True
    except Exception:
        pass
    return False


def show_paru_window() -> str:
    """Opens or brings the PARU Holographic Desktop Dashboard right in front of the user."""
    if bring_window_to_front("PARU PRO") or bring_window_to_front("PARU AI") or bring_window_to_front("127.0.0.1:8765"):
        return "Brought PARU Dashboard to the front."

    url = "http://127.0.0.1:8765/"
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            try:
                subprocess.Popen([cp, f"--app={url}", "--window-size=1280,820"])
                time.sleep(0.4)
                bring_window_to_front("PARU")
                return "Launched PARU Dashboard in dedicated desktop window."
            except Exception:
                pass

    try:
        os.startfile(url)
        time.sleep(0.4)
        bring_window_to_front("PARU")
        return "Opened PARU Dashboard in browser."
    except Exception as e:
        return f"Failed to open dashboard: {e}"


def open_application(app_name: str) -> str:
    """Launches desktop applications cleanly with Windows start and brings them to focus."""
    key = app_name.lower().strip()

    # Check for multiple apps in one command (e.g. "teams and outlook", "teams outlook", "chrome and vs code")
    found_apps = [a for a in APP_REGISTRY.keys() if a in key]
    if len(found_apps) > 1:
        launched = []
        for a in found_apps:
            strategies = APP_REGISTRY.get(a, [])
            for cmd in strategies:
                try:
                    final_cmd = cmd if cmd.startswith("start ") or cmd.startswith("powershell") else f'start "" {cmd}'
                    subprocess.Popen(final_cmd, shell=True)
                    launched.append(a.title())
                    time.sleep(0.3)
                    bring_window_to_front(a)
                    break
                except Exception:
                    continue
        if launched:
            return f"Launched {', '.join(set(launched))} in front."

    # Look up single app in registry
    strategies = APP_REGISTRY.get(key, None)
    if not strategies:
        for reg_k, reg_v in APP_REGISTRY.items():
            if key in reg_k or reg_k in key:
                strategies = reg_v
                app_name = reg_k
                break

    if strategies:
        for cmd in strategies:
            try:
                final_cmd = cmd if cmd.startswith("start ") or cmd.startswith("powershell") else f'start "" {cmd}'
                subprocess.Popen(final_cmd, shell=True)
                time.sleep(0.4)
                bring_window_to_front(app_name)
                return f"Launched {app_name.title()} successfully in front."
            except Exception:
                continue
        return f"Could not launch {app_name}."

    # Generic fallback
    try:
        subprocess.Popen(f'start "" "{key}"', shell=True)
        time.sleep(0.4)
        bring_window_to_front(key)
        return f"Launched {app_name}."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  OUTLOOK / EMAIL INTEGRATION (Universal: Classic COM + New Outlook + Web)
# ══════════════════════════════════════════════════════════════════════════════

def read_latest_emails(count: int = 1) -> str:
    """Reads latest unread or received emails from Microsoft Outlook inbox with universal fallback."""
    _init_com()
    # 1. Try classic desktop Outlook MAPI COM dispatch
    try:
        import win32com.client
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        if len(messages) == 0:
            open_application("outlook")
            return "Your Outlook inbox is open and currently empty."

        results = []
        for i in range(min(count, len(messages))):
            msg = messages.Item(i + 1)
            sender = getattr(msg, "SenderName", "Unknown Sender")
            subject = getattr(msg, "Subject", "(No Subject)")
            body = getattr(msg, "Body", "")
            clean_body = re.sub(r'\s+', ' ', body).strip()[:180]
            results.append(f"Email from {sender}: '{subject}'. Summary: {clean_body}")

        open_application("outlook")
        return "\n".join(results)
    except Exception:
        pass

    # 2. Universal fallback: Open Outlook application or web interface directly
    open_res = open_application("outlook")
    if "Launched" in open_res:
        return "I have opened Outlook in the foreground on your screen so you can view your latest messages."

    # 3. Web Outlook fallback
    try:
        os.startfile("https://outlook.office.com/mail/")
        return "Opened Outlook Web in your browser to check your latest emails."
    except Exception as e:
        return f"Outlook is ready. Please check your inbox window on screen: {e}"



# ══════════════════════════════════════════════════════════════════════════════
#  FOLDER NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def open_folder(folder_name: str) -> str:
    """Opens common user folders in File Explorer."""
    user_home = os.path.expanduser("~")
    folder_map = {
        "downloads": os.path.join(user_home, "Downloads"),
        "documents": os.path.join(user_home, "Documents"),
        "desktop":   os.path.join(user_home, "Desktop"),
        "pictures":  os.path.join(user_home, "Pictures"),
        "videos":    os.path.join(user_home, "Videos"),
        "music":     os.path.join(user_home, "Music"),
        "appdata":   os.path.join(user_home, "AppData"),
        "home":      user_home,
        "c drive":   "C:\\",
        "d drive":   "D:\\",
        "temp":      os.environ.get("TEMP", os.path.join(user_home, "AppData", "Local", "Temp")),
    }
    target = folder_map.get(folder_name.lower().strip(), folder_name)
    try:
        if os.path.isdir(target):
            subprocess.Popen(f'explorer "{target}"')
            return f"Opened folder: {target}"
        else:
            return f"Folder not found: {target}"
    except Exception as e:
        return f"Failed to open folder: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  NETWORK / WIFI INFO
# ══════════════════════════════════════════════════════════════════════════════

def get_wifi_info() -> str:
    """Gets current Wi-Fi SSID and local IP address."""
    info_parts = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[1].strip()
                info_parts.append(f"Wi-Fi: {ssid}")
                break
    except Exception:
        info_parts.append("Wi-Fi: unknown")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        info_parts.append(f"Local IP: {local_ip}")
    except Exception:
        info_parts.append("Local IP: unknown")

    return ". ".join(info_parts) if info_parts else "Network info unavailable."


# ══════════════════════════════════════════════════════════════════════════════
#  GENERIC COMMAND EXECUTION (with safety)
# ══════════════════════════════════════════════════════════════════════════════

DANGEROUS_PATTERNS = ["format", "del /s", "rd /s", "rmdir", "rm -rf", ":(){", "mkfs"]

def run_shell_command(command: str) -> str:
    """Runs a shell command on the user's PC. Blocks dangerous patterns."""
    cmd_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return f"Blocked dangerous command containing '{pattern}' for safety."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15
        )
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip()[:500] if output.strip() else f"Command executed: {command}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Command failed: {e}"
