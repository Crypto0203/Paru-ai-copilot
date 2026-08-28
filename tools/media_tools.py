"""
PARU Media & Screenshot Tools.
Screenshot uses raw Win32 GDI API via ctypes - works from ANY background thread or server process,
no display handle or desktop session required.
"""

import os
import sys
import ctypes
import struct
import time
import threading
from pathlib import Path
import config


# ──────────────────────────────────────────
#  Win32 GDI screenshot via ctypes
# ──────────────────────────────────────────

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          ctypes.c_uint32),
        ("biWidth",         ctypes.c_int32),
        ("biHeight",        ctypes.c_int32),
        ("biPlanes",        ctypes.c_uint16),
        ("biBitCount",      ctypes.c_uint16),
        ("biCompression",   ctypes.c_uint32),
        ("biSizeImage",     ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed",       ctypes.c_uint32),
        ("biClrImportant",  ctypes.c_uint32),
    ]


def _capture_screen_to_bmp(bmp_path: str) -> bool:
    """Captures the full primary screen using raw Win32 GDI and saves as BMP."""
    try:
        user32 = ctypes.windll.user32
        gdi32  = ctypes.windll.gdi32

        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)

        hwnd    = user32.GetDesktopWindow()
        hdc     = user32.GetWindowDC(hwnd)
        hdc_mem = gdi32.CreateCompatibleDC(hdc)
        hbmp    = gdi32.CreateCompatibleBitmap(hdc, w, h)
        gdi32.SelectObject(hdc_mem, hbmp)

        SRCCOPY = 0x00CC0020
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc, 0, 0, SRCCOPY)

        bmi           = BITMAPINFOHEADER()
        bmi.biSize    = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth   = w
        bmi.biHeight  = -h   # negative = top-down
        bmi.biPlanes  = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        buf   = ctypes.create_string_buffer(w * h * 4)
        lines = gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(hwnd, hdc)

        if lines == 0:
            return False

        # Write BMP file (54-byte header + pixel data)
        file_size = 54 + len(buf)
        bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
        dib_header = bytes(bmi)

        with open(bmp_path, "wb") as f:
            f.write(bmp_header)
            f.write(dib_header)
            f.write(buf)

        return os.path.exists(bmp_path) and os.path.getsize(bmp_path) > 10000

    except Exception as e:
        print(f"[Win32 screenshot error] {e}")
        return False


def take_screenshot(save_filename: str = "") -> str:
    """
    Takes a full desktop screenshot.
    Returns path to saved PNG file, or empty string on failure.
    Works from any thread / background server process.
    """
    if not save_filename:
        save_filename = f"screenshot_{int(time.time())}.png"

    png_path  = str(config.SCREENSHOTS_DIR / save_filename)
    bmp_path  = png_path.replace(".png", ".bmp")

    # Step 1: Capture raw BMP via Win32 GDI
    if _capture_screen_to_bmp(bmp_path):
        # Step 2: Convert BMP -> PNG via Pillow
        try:
            from PIL import Image
            with Image.open(bmp_path) as img:
                img.save(png_path, "PNG")
            os.remove(bmp_path)   # clean up BMP
            if os.path.exists(png_path) and os.path.getsize(png_path) > 1000:
                print(f"[Screenshot] Saved: {png_path} ({os.path.getsize(png_path)//1024}KB)")
                return png_path
        except Exception as e:
            print(f"[Screenshot PNG convert error] {e}")
            # Return the BMP directly if PNG conversion fails
            if os.path.exists(bmp_path):
                return bmp_path

    # Fallback: pyautogui (works if we have a display session)
    try:
        import pyautogui
        img = pyautogui.screenshot()
        img.save(png_path)
        if os.path.exists(png_path) and os.path.getsize(png_path) > 1000:
            return png_path
    except Exception as e:
        print(f"[pyautogui fallback error] {e}")

    print("[Screenshot] All methods failed.")
    return ""


# ──────────────────────────────────────────
#  Hardware Media Controls (Win32 API)
# ──────────────────────────────────────────

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP       = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

def _send_vk(vk_code: int):
    """Sends a raw Windows virtual key press & release."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
        return True
    except Exception as e:
        print(f"[VK Error] {e}")
        return False


def media_control(action: str) -> str:
    """Controls master media playback: playpause, next, prev, stop."""
    action = action.lower().strip()
    if action in ["playpause", "play", "pause", "resume", "toggle"]:
        _send_vk(VK_MEDIA_PLAY_PAUSE)
        return "Toggled play/pause."
    elif action in ["stop", "kill", "halt", "silence"]:
        _send_vk(VK_MEDIA_STOP)
        _send_vk(VK_MEDIA_PLAY_PAUSE)
        return "Stopped all audio playback."
    elif action in ["next", "nexttrack", "skip"]:
        _send_vk(VK_MEDIA_NEXT_TRACK)
        return "Skipped to next track."
    elif action in ["prev", "previous", "prevtrack", "back"]:
        _send_vk(VK_MEDIA_PREV_TRACK)
        return "Went to previous track."
    else:
        _send_vk(VK_MEDIA_PLAY_PAUSE)
        return f"Sent media command for '{action}'."


def stop_all_audio() -> str:
    """Instantly halts any music, video, or background sound playing across Windows."""
    _send_vk(VK_MEDIA_STOP)
    _send_vk(VK_MEDIA_PLAY_PAUSE)
    return "All media and music stopped."

