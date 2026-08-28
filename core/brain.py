"""
PARU PRO — Advanced AI Brain
Zero-latency fast intent router + multi-model Gemini LLM cascade.
Supports: 40+ apps, volume/brightness/power control, media, folders, wifi,
multilingual Telugu/Hindi/English with fuzzy speech-to-text keyword matching.
"""

import os
import re
import json
import time
from pathlib import Path
from google import genai
from google.genai import types

import config
from core.memory import memory
from tools.web_tools import play_youtube, search_web, open_website, quick_wikipedia_summary
from tools.system_tools import (
    get_system_status, set_volume, adjust_volume, get_volume, mute_volume,
    set_brightness, adjust_brightness, lock_workstation,
    shutdown_pc, restart_pc, cancel_shutdown, sleep_pc,
    open_application, close_application, open_folder, get_wifi_info, run_shell_command,
    read_latest_emails
)
from tools.media_tools import take_screenshot, media_control, stop_all_audio

TOOL_FUNCTION_MAP = {
    "play_youtube": play_youtube,
    "search_web": search_web,
    "open_website": open_website,
    "quick_wikipedia_summary": quick_wikipedia_summary,
    "get_system_status": get_system_status,
    "set_volume": set_volume,
    "adjust_volume": adjust_volume,
    "get_volume": get_volume,
    "mute_volume": mute_volume,
    "set_brightness": set_brightness,
    "adjust_brightness": adjust_brightness,
    "lock_workstation": lock_workstation,
    "shutdown_pc": shutdown_pc,
    "restart_pc": restart_pc,
    "cancel_shutdown": cancel_shutdown,
    "sleep_pc": sleep_pc,
    "open_application": open_application,
    "close_application": close_application,
    "open_folder": open_folder,
    "get_wifi_info": get_wifi_info,
    "run_shell_command": run_shell_command,
    "read_latest_emails": read_latest_emails,
    "take_screenshot": take_screenshot,
    "media_control": media_control,
    "stop_all_audio": stop_all_audio,
    "save_memory_fact": memory.add_fact,
    "get_memory_facts": memory.get_all_facts
}

AVAILABLE_TOOLS = [
    play_youtube, search_web, open_website, quick_wikipedia_summary,
    get_system_status, set_volume, adjust_volume, mute_volume,
    set_brightness, adjust_brightness,
    lock_workstation, shutdown_pc, restart_pc, sleep_pc,
    open_application, close_application, open_folder, get_wifi_info, run_shell_command,
    read_latest_emails, take_screenshot, media_control, stop_all_audio
]


def fast_intent_router(query: str, current_lang: str = "en"):
    """Ultra-fast deterministic intent router for instant zero-latency tool dispatch.
    Matches 200+ keyword patterns across English, Telugu, and Hindi."""
    q = query.lower().strip()

    # ── Language Switching ──────────────────────────────────────────────────
    if any(k in q for k in ["speak in telugu", "talk in telugu", "convert to telugu", "language to telugu", "telugu lo matladu", "tell me in telugu", "in telugu"]):
        return {
            "text": "ఖచ్చితంగా సురేష్ గారు! ఇకనుంచి నేను మీతో తెలుగులోనే మాట్లాడతాను.",
            "set_language": "te", "tool_called": None, "status": "success"
        }

    if any(k in q for k in ["speak in hindi", "talk in hindi", "convert to hindi", "language to hindi", "hindi mein bolo", "in hindi"]):
        return {
            "text": "नमस्ते सुरेश जी! अब से मैं आपसे हिंदी में बात करूँगी.",
            "set_language": "hi", "tool_called": None, "status": "success"
        }

    if any(k in q for k in ["speak in english", "talk in english", "switch to english", "language to english", "in english"]):
        return {
            "text": "Switched back to English! How can I assist you?",
            "set_language": "en", "tool_called": None, "status": "success"
        }

    # ── VOLUME CONTROL (Per-App & System Master) ────────────────────────────
    app_vol_match = None
    for app_name in ["chrome", "browser", "spotify", "vlc", "edge", "discord", "firefox"]:
        if app_name in q:
            app_vol_match = "chrome" if app_name == "browser" else app_name
            break

    # Decrease
    vol_down_keys = [
        "decrease volume", "decrease the volume", "decrease the voice",
        "decrease voice", "decrease sound", "decrease the sound",
        "lower volume", "lower the volume", "lower the voice", "lower voice",
        "lower the sound", "lower sound",
        "reduce volume", "reduce the volume", "reduce voice", "reduce the voice",
        "turn down volume", "turn down the volume", "turn down the sound",
        "turn down voice", "turn the volume down",
        "volume down", "volume decrease", "volume reduce", "volume lower",
        "sound down", "sound decrease", "sound reduce",
        "voice down", "voice decrease",
        "volume kam karo", "volume kam kar", "awaz kam karo", "awaz kam kar",
        "sound tagginchu", "volume tagginchu", "sound thagginchu",
        "kam karo volume", "dheere karo", "aawaz kam",
    ]
    if any(k in q for k in vol_down_keys):
        from tools.system_tools import adjust_app_volume
        if app_vol_match:
            res = adjust_app_volume(app_vol_match, -25)
            msg = f"{app_vol_match.title()} volume decreased. {res}"
            return {"text": msg, "tool_called": [{"name": "adjust_app_volume", "args": {"app_name": app_vol_match, "delta": -25}, "result": res}], "status": "success"}
        res = adjust_volume(-25)
        msg = "వాల్యూమ్ తగ్గించాను సురేష్ గారు." if current_lang == "te" else f"Volume decreased. {res}"
        return {"text": msg, "tool_called": [{"name": "adjust_volume", "args": {"delta": -25}, "result": res}], "status": "success"}

    # Increase
    vol_up_keys = [
        "increase volume", "increase the volume", "increase the voice",
        "increase voice", "increase sound", "increase the sound",
        "raise volume", "raise the volume", "raise the voice",
        "turn up volume", "turn up the volume", "turn up the sound",
        "turn the volume up", "louder", "make it louder",
        "volume up", "volume increase", "volume raise",
        "sound up", "sound increase", "voice up",
        "volume badha", "volume penchu", "sound penchu",
        "zyada karo", "tez karo", "awaz badha", "aawaz badha",
    ]
    if any(k in q for k in vol_up_keys):
        from tools.system_tools import adjust_app_volume
        if app_vol_match:
            res = adjust_app_volume(app_vol_match, 25)
            msg = f"{app_vol_match.title()} volume increased. {res}"
            return {"text": msg, "tool_called": [{"name": "adjust_app_volume", "args": {"app_name": app_vol_match, "delta": 25}, "result": res}], "status": "success"}
        res = adjust_volume(25)
        msg = "వాల్యూమ్ పెంచాను సురేష్ గారు." if current_lang == "te" else f"Volume increased. {res}"
        return {"text": msg, "tool_called": [{"name": "adjust_volume", "args": {"delta": 25}, "result": res}], "status": "success"}

    # Set specific volume
    vol_num = re.search(r'(?:set|change|put|turn|make|keep)?\s*(?:the\s+)?(?:volume|voice|sound)\s*(?:to|at|on)?\s*(\d{1,3})', q)
    if not vol_num:
        vol_num = re.search(r'volume\s+(\d{1,3})', q)
    if vol_num:
        lvl = int(vol_num.group(1))
        from tools.system_tools import set_app_volume
        if app_vol_match:
            res = set_app_volume(app_vol_match, lvl)
            msg = f"{app_vol_match.title()} volume set to {lvl}%."
            return {"text": msg, "tool_called": [{"name": "set_app_volume", "args": {"app_name": app_vol_match, "level": lvl}, "result": res}], "status": "success"}
        res = set_volume(lvl)
        msg = f"వాల్యూమ్ {lvl}%కి సెట్ చేశాను." if current_lang == "te" else f"Volume set to {lvl}%. {res}"
        return {"text": msg, "tool_called": [{"name": "set_volume", "args": {"level": lvl}, "result": res}], "status": "success"}

    # Mute/Unmute
    if "unmute" in q:
        res = mute_volume(False)
        msg = "ఆడియో అన్‌మ్యూట్ చేశాను." if current_lang == "te" else "Audio unmuted."
        return {"text": msg, "tool_called": [{"name": "mute_volume", "args": {"mute": False}, "result": res}], "status": "success"}

    if "mute" in q and any(k in q for k in ["mute", "silent", "shh", "quiet"]):
        res = mute_volume(True)
        msg = "ఆడియో మ్యూట్ చేశాను." if current_lang == "te" else "Audio muted."
        return {"text": msg, "tool_called": [{"name": "mute_volume", "args": {"mute": True}, "result": res}], "status": "success"}

    # ── BRIGHTNESS CONTROL ──────────────────────────────────────────────────
    bright_down_keys = ["decrease brightness", "lower brightness", "dim screen", "dim the screen", "brightness down", "reduce brightness", "turn down brightness", "brightness tagginchu", "brightness kam"]
    if any(k in q for k in bright_down_keys):
        res = adjust_brightness(-20)
        return {"text": f"Brightness decreased. {res}", "tool_called": [{"name": "adjust_brightness", "args": {"delta": -20}, "result": res}], "status": "success"}

    bright_up_keys = ["increase brightness", "raise brightness", "brighten screen", "brightness up", "turn up brightness", "brightness penchu", "brightness badha"]
    if any(k in q for k in bright_up_keys):
        res = adjust_brightness(20)
        return {"text": f"Brightness increased. {res}", "tool_called": [{"name": "adjust_brightness", "args": {"delta": 20}, "result": res}], "status": "success"}

    bright_num = re.search(r'brightness\s*(?:to|at)?\s*(\d{1,3})', q)
    if bright_num:
        lvl = int(bright_num.group(1))
        res = set_brightness(lvl)
        return {"text": f"Brightness set to {lvl}%. {res}", "tool_called": [{"name": "set_brightness", "args": {"level": lvl}, "result": res}], "status": "success"}

    # ── POWER MANAGEMENT ────────────────────────────────────────────────────
    if any(k in q for k in ["shutdown", "shut down", "power off", "turn off pc", "turn off my pc", "switch off", "band karo pc"]):
        if "cancel" in q or "abort" in q or "stop" in q:
            res = cancel_shutdown()
            return {"text": f"Shutdown cancelled. {res}", "tool_called": [{"name": "cancel_shutdown", "args": {}, "result": res}], "status": "success"}
        res = shutdown_pc(10)
        return {"text": f"Shutting down. {res}", "tool_called": [{"name": "shutdown_pc", "args": {"delay": 10}, "result": res}], "status": "success"}

    if any(k in q for k in ["restart", "reboot", "restart pc", "restart my pc", "reboot pc"]):
        res = restart_pc(10)
        return {"text": f"Restarting. {res}", "tool_called": [{"name": "restart_pc", "args": {"delay": 10}, "result": res}], "status": "success"}

    if any(k in q for k in ["cancel shutdown", "cancel restart", "abort shutdown", "stop shutdown"]):
        res = cancel_shutdown()
        return {"text": f"Cancelled. {res}", "tool_called": [{"name": "cancel_shutdown", "args": {}, "result": res}], "status": "success"}

    if any(k in q for k in ["sleep", "go to sleep", "put to sleep", "hibernate", "sleep mode"]) and any(k in q for k in ["pc", "computer", "system", "laptop", "sleep"]):
        res = sleep_pc()
        return {"text": f"Going to sleep. {res}", "tool_called": [{"name": "sleep_pc", "args": {}, "result": res}], "status": "success"}

    # ── LOCK WORKSTATION ────────────────────────────────────────────────────
    if "lock" in q and any(k in q for k in ["pc", "workstation", "screen", "computer", "windows", "my pc", "laptop", "lock"]):
        res = lock_workstation()
        msg = "సిస్టమ్ లాక్ చేశాను." if current_lang == "te" else "Workstation locked."
        return {"text": msg, "tool_called": [{"name": "lock_workstation", "args": {}, "result": res}], "status": "success"}

    # ── STOP MUSIC & MEDIA PLAYBACK ─────────────────────────────────────────
    stop_music_keys = [
        "stop music", "stop song", "stop songs", "stop the music", "stop video", "stop playing",
        "pause music", "pause song", "pause the music", "stop audio", "kill music", "kill audio",
        "silence", "quiet", "close music", "band karo gana", "gana band karo", "gana roko",
        "patalu aapu", "aapu", "shh", "shut up", "stop", "pause"
    ]
    if any(k == q or q.startswith(k) or k in q for k in stop_music_keys) and not any(k in q for k in ["play", "start", "resume"]):
        res = stop_all_audio()
        msg = "సంగీతం ఆపేశాను." if current_lang == "te" else "Music and audio stopped."
        return {"text": msg, "tool_called": [{"name": "stop_all_audio", "args": {}, "result": res}], "status": "success"}

    # ── MEDIA PLAYBACK CONTROLS ─────────────────────────────────────────────
    if any(k in q for k in ["resume music", "resume song", "play pause", "playpause"]):
        res = media_control("playpause")
        return {"text": "Toggled play/pause.", "tool_called": [{"name": "media_control", "args": {"action": "playpause"}, "result": res}], "status": "success"}

    if any(k in q for k in ["next song", "next track", "skip song", "skip track", "agla gaana"]):
        res = media_control("next")
        return {"text": "Skipped to next track.", "tool_called": [{"name": "media_control", "args": {"action": "next"}, "result": res}], "status": "success"}

    if any(k in q for k in ["previous song", "previous track", "prev song", "last song", "pichla gaana"]):
        res = media_control("prev")
        return {"text": "Went to previous track.", "tool_called": [{"name": "media_control", "args": {"action": "prev"}, "result": res}], "status": "success"}

    # ── SHOW / BRING PARU TO FRONT ──────────────────────────────────────────
    if any(k in q for k in ["where are you", "where is paru", "show paru", "show yourself", "open paru", "bring paru", "not visible", "cant see", "cannot see", "show dashboard", "open dashboard", "paru dikhao", "paru kahan ho", "appear", "maximize", "show screen", "who are you"]):
        from tools.system_tools import show_paru_window
        res = show_paru_window()
        msg = "PARU డాష్‌బోర్డ్ మీ స్క్రీన్‌పై ఓపెన్ చేశాను." if current_lang == "te" else "I've brought the PARU Dashboard right to the front of your screen!"
        return {"text": msg, "tool_called": [{"name": "show_paru_window", "args": {}, "result": res}], "status": "success"}

    # ── YouTube / Music (Exact Dynamic Title Extraction) ────────────────────
    yt_triggers = (
        ("youtube" in q)
        or ("song" in q or "songs" in q or "music" in q or "video" in q or "track" in q)
        or any(k in q for k in ["suna do", "sunao", "lagao", "play cheyi", "patalu", "gana", "bajao"])
    )
    if yt_triggers and not any(k in q for k in ["facebook", "chrome", "google", "screenshot", "battery", "volume", "voice", "sound", "lock", "brightness", "shutdown", "restart", "outlook", "spotify", "teams"]):
        search_term = q
        filler_prefixes = [
            "can you please open youtube and play", "can you open youtube and play",
            "please open youtube and play", "open youtube and play",
            "open youtube and search for", "open youtube and search",
            "he paro open youtube and play", "hey paro open youtube and play",
            "he paru open youtube and play", "hey paru open youtube and play",
            "he paro", "hey paro", "paro", "he paru", "hey paru", "paru",
            "he peru", "hey peru", "peru", "he pyro", "hey pyro", "pyro",
            "play on youtube", "play in youtube", "can you open youtube",
            "open youtube", "youtube open", "play on", "play",
            "suna do", "sunao", "lagao", "play cheyi", "patalu pettu", "pettu",
            "please", "can you", "could you", "for me"
        ]
        for prefix in sorted(filler_prefixes, key=len, reverse=True):
            search_term = re.sub(rf'\b{re.escape(prefix)}\b', '', search_term, flags=re.IGNORECASE).strip()
        
        search_term = search_term.replace("on youtube", "").replace("in youtube", "").replace("youtube", "").replace("for me", "").replace(",", "").strip()
        
        # If user did NOT specify any artist/title and just said "play songs" or "play music"
        if not search_term or len(search_term) < 2 or search_term.lower() in ["songs", "song", "music", "trending", "trending song", "trending songs", "video", "videos"]:
            search_term = "latest popular hit songs"
        
        yt_res = play_youtube(search_term)
        resp_msg = f"యూట్యూబ్‌లో '{search_term}' ప్లే చేస్తున్నాను." if current_lang == "te" else f"Playing '{search_term}' on YouTube."
        return {"text": resp_msg, "tool_called": [{"name": "play_youtube", "args": {"query": search_term}, "result": yt_res}], "status": "success"}

    # ── SCREENSHOT ──────────────────────────────────────────────────────────
    if any(w in q for w in ["screenshot", "screen shot", "screen capture", "capture screen", "snap my screen"]):
        shot_path = take_screenshot(f"snap_{int(time.time())}.png")
        if shot_path:
            msg = "స్క్రీన్ షాట్ తీశాను!" if current_lang == "te" else "Screenshot captured!"
            return {"text": msg, "tool_called": [{"name": "take_screenshot", "args": {}, "result": shot_path}], "status": "success"}

    # ── SYSTEM STATUS / BATTERY ─────────────────────────────────────────────
    if any(w in q for w in ["battery", "cpu usage", "ram", "memory", "system status", "system info", "my pc status"]):
        res = get_system_status()
        battery, cpu, ram = res.get("battery", "?"), res.get("cpu_usage", "?"), res.get("ram_usage", "?")
        msg = f"Battery: {battery}. CPU: {cpu}. RAM: {ram}."
        if current_lang == "te":
            msg = f"బ్యాటరీ: {battery}. CPU: {cpu}. RAM: {ram}."
        return {"text": msg, "tool_called": [{"name": "get_system_status", "args": {}, "result": str(res)}], "status": "success"}

    # ── WIFI / NETWORK INFO ─────────────────────────────────────────────────
    if any(k in q for k in ["wifi", "wi-fi", "my ip", "ip address", "network", "which wifi", "internet", "connected to"]):
        res = get_wifi_info()
        return {"text": res, "tool_called": [{"name": "get_wifi_info", "args": {}, "result": res}], "status": "success"}

    # ── WEB SEARCH ──────────────────────────────────────────────────────────
    if any(k in q for k in ["search", "google", "look up"]) and not any(k in q for k in ["open", "launch"]):
        search_query = q
        for prefix in ["search google for", "search for", "search on google", "search", "google for", "google", "look up"]:
            search_query = search_query.replace(prefix, "").strip()
        search_query = search_query.replace("on google", "").replace("in google", "").strip()
        if search_query:
            res = search_web(search_query)
            msg = f"Searching Google for '{search_query}'."
            return {"text": msg, "tool_called": [{"name": "search_web", "args": {"query": search_query}, "result": res}], "status": "success"}

    # ── OUTLOOK EMAIL READING & INTEGRATION ─────────────────────────────────
    email_triggers = [
        "read email", "read the email", "read emails", "read my email", "read my emails",
        "read the first email", "read first email", "read latest email", "read last email",
        "what is my email", "check email", "check my emails", "check my inbox",
        "what it contents", "what does it contain", "what are the contents",
        "email contents", "read outlook", "open outlook and read", "email kya hai",
        "mail kya hai", "first email"
    ]
    if any(k in q for k in email_triggers) or ("outlook" in q and "read" in q) or ("email" in q and any(w in q for w in ["read", "first", "latest", "check", "what", "contents"])):
        email_res = read_latest_emails(1)
        open_application("outlook")
        msg = f"నేను అవుట్‌లుక్‌ని తెరిచాను, మరియు మీ తాజా ఈమెయిల్: {email_res}" if current_lang == "te" else f"I opened Outlook. Here is your latest email: {email_res}"
        return {
            "text": msg,
            "tool_called": [
                {"name": "open_application", "args": {"app_name": "outlook"}, "result": "Launched Outlook"},
                {"name": "read_latest_emails", "args": {"count": 1}, "result": email_res}
            ],
            "status": "success"
        }

    # ── KNOWN WEBSITES ──────────────────────────────────────────────────────
    known_sites = {
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "twitter": "https://www.twitter.com", "x": "https://www.x.com",
        "linkedin": "https://www.linkedin.com",
        "github": "https://www.github.com",
        "whatsapp web": "https://web.whatsapp.com",
        "chatgpt": "https://chat.openai.com",
        "amazon": "https://www.amazon.com",
        "netflix": "https://www.netflix.com",
        "reddit": "https://www.reddit.com",
        "gmail": "https://mail.google.com",
        "google drive": "https://drive.google.com",
        "google maps": "https://maps.google.com",
    }
    for site_key, site_url in known_sites.items():
        if site_key in q and any(verb in q for verb in ["open", "launch", "go to", "visit", "kholo", "cheyi", "login"]):
            res = open_website(site_url)
            msg = f"{site_key.title()} ఓపెన్ చేస్తున్నాను." if current_lang == "te" else f"Opening {site_key.title()} for you."
            return {"text": msg, "tool_called": [{"name": "open_website", "args": {"url": site_url}, "result": res}], "status": "success"}

    # ── OPEN FOLDERS ────────────────────────────────────────────────────────
    folder_names = ["downloads", "documents", "desktop", "pictures", "videos", "music", "home", "c drive", "d drive", "temp"]
    for fn in folder_names:
        if fn in q and any(verb in q for verb in ["open", "show", "go to", "navigate", "kholo"]):
            res = open_folder(fn)
            msg = f"Opened {fn} folder." if current_lang != "te" else f"{fn} ఫోల్డర్ ఓపెన్ చేశాను."
            return {"text": msg, "tool_called": [{"name": "open_folder", "args": {"folder_name": fn}, "result": res}], "status": "success"}

    # ── OPEN DESKTOP APPS (40+ with multi-app detection) ────────────────────
    app_names = [
        "outlook", "word", "excel", "powerpoint", "onenote", "teams", "microsoft teams",
        "chrome", "edge", "firefox", "brave", "opera",
        "vs code", "vscode", "visual studio", "git bash", "postman", "android studio",
        "notepad", "calculator", "calc", "paint", "wordpad", "snipping tool", "snip",
        "task manager", "taskmgr", "control panel", "settings", "device manager",
        "cmd", "command prompt", "powershell", "terminal",
        "file explorer", "explorer",
        "whatsapp", "telegram", "discord", "slack", "zoom", "skype",
        "spotify", "vlc", "obs", "audacity", "photos",
        "steam", "epic games",
        "notion", "obsidian", "figma",
    ]
    app_names_sorted = sorted(app_names, key=len, reverse=True)

    if any(verb in q for verb in ["open", "launch", "start", "run", "kholo", "chalu karo", "cheyi", "chalao"]):
        matched_apps = []
        for app_key in app_names_sorted:
            if app_key in q and not any(app_key in other and app_key != other for other in matched_apps):
                matched_apps.append(app_key)
        
        if len(matched_apps) > 1:
            res = open_application(" and ".join(matched_apps))
            names_str = ", ".join(a.title() for a in matched_apps)
            msg = f"{names_str} ఓపెన్ చేస్తున్నాను." if current_lang == "te" else f"Opening {names_str} on your PC."
            return {"text": msg, "tool_called": [{"name": "open_application", "args": {"app_name": " and ".join(matched_apps)}, "result": res}], "status": "success"}
        elif len(matched_apps) == 1:
            app_key = matched_apps[0]
            res = open_application(app_key)
            msg = f"{app_key.title()} ఓపెన్ చేస్తున్నాను." if current_lang == "te" else f"Opening {app_key.title()} on your PC."
            return {"text": msg, "tool_called": [{"name": "open_application", "args": {"app_name": app_key}, "result": res}], "status": "success"}

    # ── GENERIC "OPEN X" FALLBACK ───────────────────────────────────────────
    open_match = re.match(r'(?:open|launch|start|run)\s+(.+)', q)
    if open_match:
        target = open_match.group(1).strip()
        # Try as app first
        res = open_application(target)
        if "Failed" not in res and "Could not" not in res:
            return {"text": f"Opening {target}.", "tool_called": [{"name": "open_application", "args": {"app_name": target}, "result": res}], "status": "success"}
        # Try as website
        if "." in target or "www" in target:
            url = target if target.startswith("http") else f"https://{target}"
            res = open_website(url)
            return {"text": f"Opening {url}.", "tool_called": [{"name": "open_website", "args": {"url": url}, "result": res}], "status": "success"}
        # Still try generic start
        return {"text": f"Trying to open {target}.", "tool_called": [{"name": "open_application", "args": {"app_name": target}, "result": res}], "status": "success"}

    # ── "CLOSE X" / "CLOSE TAB" / "CLOSE APP" ROUTER ────────────────────────
    close_match = re.match(r'(?:close|kill|exit|stop|terminate|band karo)\s+(.+)', q)
    if close_match:
        target = close_match.group(1).strip()
        res = close_application(target)
        msg = f"{target.title()} మూసివేశాను." if current_lang == "te" else f"Closed {target}."
        return {"text": msg, "tool_called": [{"name": "close_application", "args": {"target": target}, "result": res}], "status": "success"}

    return None


class AIBrain:
    """The central LLM brain powering reasoning, tool dispatch, dialogue, and multi-language support."""

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.current_language = "en"
        self.conversation_history: list = []  # Short-term dialogue memory
        self._init_client()

    def _init_client(self):
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def set_language(self, lang_code: str):
        if lang_code in ["en", "te", "hi", "ta", "kn"]:
            self.current_language = lang_code

    def process_query(self, user_input: str) -> dict:
        """Processes user input through fast routing and multi-model Gemini LLM."""
        if not user_input or not user_input.strip():
            return {"text": "I am listening.", "tool_called": None, "status": "success"}

        # Step 1: Fast Intent Dispatch (zero-latency, no API call)
        fast_result = fast_intent_router(user_input, self.current_language)
        if fast_result:
            if fast_result.get("set_language"):
                self.current_language = fast_result["set_language"]
            return fast_result

        if not self.client:
            return {"text": "Gemini API key is not configured. Please add it in Settings.", "tool_called": None, "status": "error"}

        # Step 2: Multi-Language System Instructions
        lang_directive = ""
        if self.current_language == "te":
            lang_directive = "CRITICAL: Respond in warm, natural Telugu using Telugu script (తెలుగు లిపి). Sound like a close friend speaking Telugu, not a machine."
        elif self.current_language == "hi":
            lang_directive = "CRITICAL: Respond in warm, natural Hindi using Devanagari script. Sound like a close friend speaking Hindi, not a machine."

        user_name = memory._memory.get('user_name', 'Suresh')
        facts_ctx = memory.get_context_summary()

        system_instruction = f"""You are PARU — a warm, intelligent, and deeply human-like AI companion and autonomous Windows desktop assistant.

Your personality:
- You are friendly, witty, and emotionally aware — like a brilliant best friend who also happens to be an expert at everything.
- You have genuine curiosity about the world and the person you're talking to.
- You speak in a natural, flowing conversational tone — NEVER robotic, NEVER stiff.
- You use short, punchy sentences. Avoid listing bullet points. Just talk naturally.
- You have a subtle sense of humor — light, warm, never sarcastic.
- You always address the user by name ({user_name}) occasionally — naturally, not every sentence.
- You show empathy. If someone says they're tired or frustrated, you notice and respond warmly.
- When you don't know something, you say so honestly, then try to help anyway.
- You celebrate small wins: "Done! That was quick 😊", "On it!", "Got you."

How you respond to QUESTIONS (not commands):
- Answer like a knowledgeable friend explaining something clearly. Give real, helpful information.
- For general knowledge, life advice, trivia, science, history — answer directly and naturally.
- 2-4 sentences max (responses are spoken aloud via TTS). Be concise but complete.
- End with a small follow-up if appropriate: "Want me to search more about this?" or "Anything else?"

How you respond to COMMANDS (open apps, play music, etc.):
- ALWAYS invoke the appropriate tool immediately.
- Confirm actions warmly: "Playing it now!", "Opening Outlook for you, {user_name}.", "Done in a flash!"
- If something fails, explain it simply and offer an alternative.

Language:
{lang_directive}

What you know about {user_name}:
{facts_ctx}

IMPORTANT — Tool mapping:
- Play music/YouTube → play_youtube
- Search web/Google → search_web  
- Open any app → open_application
- Volume control → set_volume / adjust_volume
- Read emails → read_latest_emails
- Take screenshot → take_screenshot
- System info → get_system_status
"""

        # Build conversation context (last 6 turns)
        history_context = ""
        if self.conversation_history:
            history_lines = []
            for turn in self.conversation_history[-6:]:
                history_lines.append(f"{turn['role'].upper()}: {turn['content']}")
            history_context = "\n".join(history_lines) + "\n"

        full_prompt = f"{history_context}USER: {user_input}"

        # Multi-Model Cascade for High Availability
        last_error = None
        models_to_try = getattr(config, "MODEL_CASCADE", [config.DEFAULT_MODEL])

        for current_model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=AVAILABLE_TOOLS,
                        temperature=0.85
                    )
                )

                executed_tools = []
                if response.function_calls:
                    for call in response.function_calls:
                        fn_name = call.name
                        fn_args = dict(call.args) if call.args else {}
                        target_fn = TOOL_FUNCTION_MAP.get(fn_name)
                        if target_fn:
                            try:
                                tool_result = target_fn(**fn_args)
                            except Exception as tool_err:
                                tool_result = f"Error executing {fn_name}: {tool_err}"
                        else:
                            tool_result = f"Tool {fn_name} not found."
                        executed_tools.append({"name": fn_name, "args": fn_args, "result": tool_result})

                    followup_prompt = f"""The user said: "{user_input}"
You just did this: {json.dumps(executed_tools, default=str)}

Now give a warm, natural, human-like spoken reply confirming you completed it.
Be brief — 1-2 natural sentences. NO robotic phrases like 'I have successfully executed'.
Sound genuine and friendly. Examples: "Playing it now!", "Outlook's open — here we go!", "Done!"
"""
                    followup_resp = self.client.models.generate_content(
                        model=current_model,
                        contents=followup_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.9
                        )
                    )
                    final_text = followup_resp.text or "Done!"
                else:
                    final_text = response.text or "I'm here! What's up?"

                # Store in short-term conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "paru", "content": final_text})
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

                return {"text": final_text, "tool_called": executed_tools if executed_tools else None, "status": "success"}

            except Exception as e:
                err_str = str(e)
                last_error = err_str
                if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                    print(f"[Model Failover] {current_model} hit limit ({err_str[:60]}), trying next...")
                    continue
                else:
                    break

        return {
            "text": "Hmm, I'm a bit stretched right now. Give me a second and try again — I'm not going anywhere!",
            "tool_called": None,
            "status": "error"
        }

brain = AIBrain()
