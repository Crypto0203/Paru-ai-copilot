"""
PARU PRO — Web Tools
High-priority browser launcher with foreground window focus, direct YouTube search & autoplay,
Google search, and website navigation.
"""

import os
import sys
import ctypes
import subprocess
import urllib.parse
import urllib.request
import re
import requests

def get_direct_youtube_video_url(query: str) -> str:
    """Searches YouTube and returns direct video watch URL with autoplay=1."""
    try:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        html = urllib.request.urlopen(req, timeout=3.5).read().decode("utf-8")
        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
    except Exception as e:
        print(f"[YouTube Video Scraper Notice] {e}")

    # Fallback to search list
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"


_last_open_time = 0.0
_last_open_url = ""

def open_url_windows(url: str) -> bool:
    """
    Guarantees the URL opens in the FOREGROUND on the user's screen.
    Uses native Windows Shell (os.startfile) -> Chrome direct -> ShellExecute.
    """
    global _last_open_time, _last_open_url
    import time
    now = time.time()
    if now - _last_open_time < 3.0 and _last_open_url == url:
        return True
    _last_open_time = now
    _last_open_url = url

    # 1. Native Windows Shell association (opens default browser immediately in front)
    try:
        os.startfile(url)
        time.sleep(0.3)
        try:
            from tools.system_tools import bring_window_to_front
            bring_window_to_front("Chrome")
            bring_window_to_front("YouTube")
        except Exception:
            pass
        return True
    except Exception:
        pass

    # 2. Chrome direct execution
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            try:
                subprocess.Popen([cp, url])
                time.sleep(0.3)
                try:
                    from tools.system_tools import bring_window_to_front
                    bring_window_to_front("Chrome")
                    bring_window_to_front("YouTube")
                except Exception:
                    pass
                return True
            except Exception:
                pass

    # 3. Windows Start command fallback
    try:
        subprocess.Popen(f'start "" "{url}"', shell=True)
        return True
    except Exception:
        pass

    return False


def play_youtube(query: str) -> dict:
    """Finds top YouTube video, launches it in foreground, and returns URL."""
    direct_video_url = get_direct_youtube_video_url(query)
    open_url_windows(direct_video_url)
    
    # Extract video ID for frontend embedding if applicable
    video_id = None
    vid_match = re.search(r'v=([a-zA-Z0-9_-]{11})', direct_video_url)
    if vid_match:
        video_id = vid_match.group(1)

    return {
        "url": direct_video_url,
        "video_id": video_id,
        "action": "open_tab",
        "message": f"Playing '{query}' on YouTube now."
    }


def search_web(query: str) -> dict:
    """Instant zero-latency Google search dispatch in foreground."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    open_url_windows(url)
    return {"url": url, "action": "open_tab", "message": f"Opened Google search results for '{query}'."}


def open_website(url: str) -> dict:
    """Instant website launcher in foreground."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    open_url_windows(url)
    return {"url": url, "action": "open_tab", "message": f"Opened website: {url}"}


def quick_wikipedia_summary(topic: str) -> str:
    """Fetches factual summary of a topic from Wikipedia API."""
    try:
        endpoint = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
        headers = {"User-Agent": "ParuAssistant/1.0"}
        resp = requests.get(endpoint, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract", "")
            if extract:
                return extract[:400] + ("..." if len(extract) > 400 else "")
        return f"Could not find a Wikipedia summary for '{topic}'."
    except Exception as e:
        return f"Wikipedia lookup error: {e}"
