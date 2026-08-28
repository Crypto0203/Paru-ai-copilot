"""
Telegram Remote Bridge for PARU AI Assistant.
Allows full PC control from your phone via Telegram bot.
All errors are logged clearly and responded to gracefully.
"""

import time
import os
import sys
import threading
import requests as req_lib
import config
from core.brain import brain
from tools.media_tools import take_screenshot


class TelegramBridge:
    """Remote phone bridge via Telegram Bot API polling."""

    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.is_running = False
        self.last_update_id = 0
        self.thread = None

    def start(self):
        # Reload token from config in case it was just updated
        if not self.bot_token:
            self.bot_token = config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not self.bot_token:
            print("[Telegram] No bot token found - skipping.")
            return
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True, name="TelegramPoller")
        self.thread.start()
        print(f"[PARU] 📱 Telegram Bridge ONLINE — Bot token ends in ...{self.bot_token[-6:]}")

    def stop(self):
        self.is_running = False

    def _api(self, method: str, **kwargs):
        """Makes a Telegram API call, returns parsed JSON or None on failure."""
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        try:
            resp = req_lib.post(url, timeout=12, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Telegram API Error] {method}: {e}")
            return None

    def _send_message(self, chat_id, text: str):
        """Sends a plain text message."""
        # Escape markdown to avoid parse errors
        safe_text = text.replace("*", "").replace("`", "").replace("_", "")
        self._api("sendMessage", json={"chat_id": chat_id, "text": safe_text})

    def _send_photo(self, chat_id, photo_path: str, caption: str = ""):
        """Sends a photo file."""
        try:
            with open(photo_path, "rb") as f:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                resp = req_lib.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": f},
                    timeout=30
                )
                if not resp.ok:
                    print(f"[Telegram Photo Error] {resp.text}")
        except Exception as e:
            print(f"[Telegram Photo Send Error] {e}")
            self._send_message(chat_id, f"Could not send screenshot: {e}")

    def _handle_message(self, chat_id, text: str):
        """Processes one incoming message and sends a reply."""
        text_lower = text.lower().strip()

        # Handle /start
        if text_lower in ["/start", "start"]:
            self._send_message(chat_id, "Hello Suresh! I'm PARU, your AI assistant. I'm connected to your PC right now. Try: 'take a screenshot', 'open YouTube and play trending songs', 'what is my battery?', or 'lock my pc'.")
            return

        # Handle screenshot requests
        if any(w in text_lower for w in ["screenshot", "screen shot", "screen capture", "my screen", "what's on screen"]):
            self._send_message(chat_id, "Taking a screenshot of your PC now...")
            shot_path = take_screenshot(f"telegram_{int(time.time())}.png")
            if shot_path and os.path.exists(shot_path) and os.path.getsize(shot_path) > 1000:
                self._send_photo(chat_id, shot_path, "Here is your PC screen!")
            else:
                self._send_message(chat_id, "Sorry, screenshot failed. Your PC might be locked or the screen is off.")
            return

        # All other commands go to the AI brain
        try:
            result = brain.process_query(text)
            response_text = result.get("text", "Done.")
            tool_called = result.get("tool_called")
            screenshot_path = result.get("screenshot_path")

            # If a screenshot was taken, send it as a photo
            if screenshot_path and os.path.exists(screenshot_path):
                self._send_photo(chat_id, screenshot_path, f"PARU: {response_text}")
                return

            # Build text reply
            reply = f"PARU: {response_text}"
            if tool_called:
                for t in tool_called:
                    r = t.get("result", "")
                    if r and "error" not in str(r).lower():
                        reply += f"\n✅ {t['name']}: {str(r)[:80]}"

            self._send_message(chat_id, reply)
        except Exception as e:
            print(f"[Telegram brain error] {e}")
            self._send_message(chat_id, f"Sorry, I ran into an error: {str(e)[:100]}")

    def _poll_loop(self):
        """Long-polling loop with exponential backoff on errors."""
        backoff = 1
        while self.is_running:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 20, "limit": 10}
                resp = req_lib.get(url, params=params, timeout=25)

                if resp.status_code == 200:
                    data = resp.json()
                    backoff = 1  # reset on success
                    for update in data.get("result", []):
                        self.last_update_id = update["update_id"]
                        msg = update.get("message") or update.get("edited_message", {})
                        if not msg:
                            continue
                        chat_id = msg.get("chat", {}).get("id")
                        text = msg.get("text", "").strip()
                        if chat_id and text:
                            # Handle in a separate thread so polling doesn't block
                            threading.Thread(
                                target=self._handle_message,
                                args=(chat_id, text),
                                daemon=True
                            ).start()
                elif resp.status_code == 401:
                    print("[Telegram] Invalid bot token! Stopping bridge.")
                    self.is_running = False
                    break
                else:
                    print(f"[Telegram] Unexpected status {resp.status_code}")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30)

            except req_lib.exceptions.ConnectionError:
                print("[Telegram] Network error. Retrying in", backoff, "s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
            except Exception as e:
                print(f"[Telegram Poll Error] {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)


telegram_bridge = TelegramBridge()
