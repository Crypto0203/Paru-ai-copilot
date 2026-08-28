import subprocess
import os
import psutil

# Common Windows App mappings
APP_SHORTCUTS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "settings": "start ms-settings:",
    "chrome": "start chrome",
    "edge": "start msedge",
    "firefox": "start firefox",
    "spotify": "start spotify:",
    "discord": "start discord:",
    "vs code": "code",
    "code": "code"
}


def open_application(app_name: str) -> str:
    """Opens a Windows application by name."""
    clean_name = app_name.lower().strip()
    
    # Check direct shortcut map
    for key, cmd in APP_SHORTCUTS.items():
        if key in clean_name or clean_name in key:
            try:
                subprocess.Popen(cmd, shell=True)
                return f"Successfully opened {app_name}."
            except Exception as e:
                return f"Error opening {app_name}: {e}"

    # Fallback to Windows 'start' command
    try:
        subprocess.Popen(f"start {clean_name}", shell=True)
        return f"Dispatched launch command for {app_name}."
    except Exception as e:
        return f"Could not find or launch {app_name}: {e}"


def close_application(app_name: str) -> str:
    """Closes running processes matching app_name."""
    clean_name = app_name.lower().strip()
    terminated = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            p_name = proc.info['name'].lower()
            if clean_name in p_name or (clean_name + ".exe") == p_name:
                proc.terminate()
                terminated += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if terminated > 0:
        return f"Closed {terminated} instance(s) of {app_name}."
    return f"No active process found matching '{app_name}'."
