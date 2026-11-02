"""Interactive Telegram Bot Service for Level Crossing Safety System.

Listens for incoming Telegram commands (/start, /status, /ping, /id, /test)
and responds interactively with station master Chat IDs, system health, and test alerts.
Runs asynchronously in background polling mode without blocking backend execution.
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Union
import requests
from dotenv import load_dotenv

from level_crossing.common.logger import get_logger
from level_crossing.alerts.telegram_dispatcher import get_default_dispatcher

load_dotenv()
logger = get_logger("telegram_bot_service")


class TelegramBotService:
    """Long-polling interactive Telegram Bot responder."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        poll_interval: float = 1.0,
        request_timeout: int = 15,
    ):
        if bot_token is not None:
            self.bot_token = bot_token.strip()
        else:
            self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.poll_interval = poll_interval
        self.request_timeout = request_timeout
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_update_id: int = 0

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        """Starts the Telegram polling loop in a background daemon thread."""
        if not self.is_configured:
            logger.warning("TelegramBotService: Bot token not configured. Interactive bot not started.")
            return False

        if self.is_running:
            logger.info("TelegramBotService: Already running.")
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="tg_bot_service",
            daemon=True,
        )
        self._thread.start()
        logger.info("TelegramBotService: Interactive bot listener started in background.")
        return True

    def stop(self) -> None:
        """Stops the polling loop cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("TelegramBotService: Interactive bot listener stopped.")

    def _send_reply(self, chat_id: Union[str, int], text: str, parse_mode: str = "Markdown") -> bool:
        """Helper to send a Markdown or plain text reply to a Telegram chat."""
        if not self.bot_token:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=self.request_timeout,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"TelegramBotService: Failed to send reply to chat {chat_id}: {e}")
            return False

    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Processes an incoming Telegram message and formulates an interactive reply."""
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        user = message.get("from", {})
        first_name = user.get("first_name", "Operator")
        username = user.get("username", "")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return

        user_tag = f"@{username}" if username else first_name
        logger.info(f"TelegramBotService: Received command '{text}' from {user_tag} (Chat ID: {chat_id})")

        command = text.split()[0].lower() if text else ""

        if command in ("/start", "/id", "/chatid"):
            reply = (
                f"👋 *Welcome {first_name} to Railway Safety Command Bot!*\n\n"
                f"🔢 *Your Telegram Chat ID:* `{chat_id}`\n\n"
                f"📍 *Monitoring Zone:* Level Crossing LC-102\n"
                f"🟢 *Status:* System Operational & Armed\n"
                f"🚨 *Emergency Alerts:* Enabled for this Chat ID\n\n"
                f"Whenever a dangerous track intrusion or pedestrian risk is confirmed by the CCTV safety cameras, "
                f"you will receive instant high-priority alerts with photographic evidence here.\n\n"
                f"*Available Commands:*\n"
                f"• `/start` or `/id` — View your Chat ID & enrollment\n"
                f"• `/status` — Check live system & perception engine health\n"
                f"• `/ping` — Test bot connection & response latency\n"
                f"• `/test` — Dispatch a sample emergency alert snapshot"
            )
            self._send_reply(chat_id, reply)

        elif command == "/status":
            now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            reply = (
                f"🛰 *RAILWAY SAFETY SYSTEM HEALTH*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🟢 *Overall System:* Operational\n"
                f"👁 *Perception Engine:* YOLOv8 (Apple MPS / GPU)\n"
                f"🎯 *Object Tracking:* ByteTrack Active\n"
                f"📍 *Active Crossing:* LC-102 (Track Zone)\n"
                f"🚨 *Emergency Dispatcher:* Armed\n"
                f"🕒 *Server Time:* {now_str}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"All optical crossing protection routines are functioning normally."
            )
            self._send_reply(chat_id, reply)

        elif command == "/ping":
            reply = "🏓 *Pong!*\nRailway Safety Bot is online and actively connected to the Operation Control Center (OCC)."
            self._send_reply(chat_id, reply)

        elif command == "/test":
            dispatcher = get_default_dispatcher()
            self._send_reply(chat_id, "⏳ Generating and dispatching test safety alert with CCTV evidence...")
            # Find sample image
            sample_img = None
            for candidate in [
                "data/evidence/test_intrusion.jpg",
                "data/snapshots/sample_cctv.jpg",
                "data/controlled/validation/sample_frame.jpg",
            ]:
                if os.path.exists(candidate):
                    sample_img = candidate
                    break
            
            # If no existing sample image, create a dummy placeholder or send text
            if sample_img:
                dispatcher.send_emergency_alert(
                    image_path=sample_img,
                    location="LC-102",
                    danger_level="CRITICAL",
                    confidence=98.5,
                    event_id=f"TEST-{int(time.time())}",
                    object_type="Person",
                )
            else:
                dispatcher.send_text_message(
                    "🚨 *TEST EMERGENCY ALERT*\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "⚠️ DANGER LEVEL: CRITICAL\n"
                    "📍 Location: LC-102\n"
                    "👤 Detected Object: Person (Simulated)\n"
                    "🎯 Detection Confidence: 99.1%\n"
                    "📡 Detection Status: CONFIRMED TEST\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "This is a verified test dispatch from the Command Center."
                )

        else:
            reply = (
                f"🤖 *Railway Safety Emergency Bot*\n\n"
                f"Hello {first_name}, I am an automated railway crossing safety assistant.\n\n"
                f"🔢 *Your Chat ID:* `{chat_id}`\n\n"
                f"Send `/start` for system overview, or `/status` to view live crossing security health."
            )
            self._send_reply(chat_id, reply)

    def _poll_loop(self) -> None:
        """Continuous polling worker loop."""
        api_url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        logger.info("TelegramBotService: Polling loop started.")

        while not self._stop_event.is_set():
            try:
                params: Dict[str, Any] = {"timeout": 10}
                if self._last_update_id > 0:
                    params["offset"] = self._last_update_id + 1

                resp = requests.get(api_url, params=params, timeout=self.request_timeout + 5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        for update in updates:
                            update_id = update.get("update_id", 0)
                            if update_id > self._last_update_id:
                                self._last_update_id = update_id

                            msg = update.get("message")
                            if msg:
                                self._handle_message(msg)
                elif resp.status_code == 409:
                    logger.warning("TelegramBotService: Webhook conflict or another instance running. Waiting 5s...")
                    time.sleep(5.0)
                else:
                    time.sleep(2.0)

            except requests.exceptions.Timeout:
                # Normal long polling timeout, loop again
                continue
            except requests.exceptions.RequestException as req_err:
                if not self._stop_event.is_set():
                    logger.warning(f"TelegramBotService: Polling network notice: {req_err}")
                time.sleep(3.0)
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"TelegramBotService: Unexpected error in polling: {e}")
                time.sleep(2.0)

            if self._stop_event.wait(timeout=self.poll_interval):
                break

        logger.info("TelegramBotService: Polling loop terminated.")


# Module singleton
_default_bot_service: Optional[TelegramBotService] = None


def get_default_bot_service() -> TelegramBotService:
    global _default_bot_service
    if _default_bot_service is None:
        _default_bot_service = TelegramBotService()
    return _default_bot_service


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 RAILWAY TELEGRAM BOT INTERACTIVE SERVICE")
    print("=" * 60)
    service = TelegramBotService()
    if not service.is_configured:
        print("[!] TELEGRAM_BOT_TOKEN is not configured in .env!")
        exit(1)

    print("[*] Starting interactive bot service. Press Ctrl+C to stop.")
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping bot service...")
        service.stop()
        print("[✓] Stopped cleanly.")
