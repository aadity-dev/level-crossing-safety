"""Instant Emergency Dispatcher using Telegram Bot API.

Provides non-blocking, priority-aware push notification of confirmed railway intrusions
with attached CCTV photographic evidence directly to Station Master mobile terminals.
"""

from __future__ import annotations

import os
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import requests
from dotenv import load_dotenv

from level_crossing.common.logger import get_logger

# Load environment configuration from .env if present
load_dotenv()

logger = get_logger("telegram_dispatcher")

# Numeric severity ranking for escalation logic
SEVERITY_RANKS: Dict[str, int] = {
    "IGNORE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


class TelegramDispatcher:
    """Asynchronous, thread-safe Telegram Bot emergency dispatcher with evidence uploading."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[Union[str, int]] = None,
        location: Optional[str] = None,
        timeout: int = 15,
        max_workers: int = 2,
    ):
        self.bot_token = (bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = str(chat_id or os.getenv("TELEGRAM_CHAT_ID", "")).strip()
        self.location = (location or os.getenv("CROSSING_LOCATION", "LC-102")).strip()
        self.timeout = timeout
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="tg_dispatch"
        )
        # Event suppression tracker: event_id -> {"severity": str, "timestamp": float}
        self._dispatched_events: Dict[str, Dict[str, Any]] = {}
        self.stats = {"dispatched": 0, "failed": 0, "suppressed": 0}

    @property
    def is_configured(self) -> bool:
        """Returns True if both bot token and chat ID are configured."""
        return bool(self.bot_token and self.chat_id)

    @staticmethod
    def format_alert_caption(
        location: str,
        danger_level: str,
        confidence: float,
        event_id: str,
        timestamp_str: str,
        object_type: str = "Person",
    ) -> str:
        """Formats the official Telegram emergency notification according to railway specs."""
        return (
            "🚨 RAILWAY EMERGENCY ALERT\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ DANGER LEVEL: {danger_level.upper()}\n"
            f"📍 Location: {location}\n"
            f"👤 Detected Object: {object_type.capitalize()}\n"
            f"🎯 Detection Confidence: {confidence:.1f}%\n"
            f"🆔 Event ID: {event_id}\n"
            f"🕒 Timestamp: {timestamp_str}\n"
            "📡 Detection Status: CONFIRMED\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🚨 IMMEDIATE ACTION REQUIRED\n"
            "Intrusion detected on railway track.\n"
            "📸 CCTV evidence attached."
        )

    def should_dispatch(self, event_id: str, severity: str) -> bool:
        """Evaluates duplicate suppression and severity priority.
        
        Rules:
        - LOW and IGNORE are suppressed.
        - CRITICAL and HIGH are immediately approved for genuine new intrusions.
        - Duplicate frames for the same confirmed intrusion event are suppressed.
        - Escalations to higher severity tiers (e.g. MEDIUM -> HIGH, HIGH -> CRITICAL) are permitted.
        """
        sev_upper = severity.upper()
        if sev_upper in ("LOW", "IGNORE"):
            return False

        if event_id not in self._dispatched_events:
            return True

        prev_sev = self._dispatched_events[event_id].get("severity", "LOW")
        prev_rank = SEVERITY_RANKS.get(prev_sev, 0)
        curr_rank = SEVERITY_RANKS.get(sev_upper, 0)

        # Allow dispatch only if severity significantly increased
        if curr_rank > prev_rank:
            return True

        return False

    def send_emergency_alert(
        self,
        image_path: Union[str, Path],
        location: Optional[str] = None,
        danger_level: str = "CRITICAL",
        confidence: float = 95.0,
        event_id: str = "EVT-UNKNOWN",
        timestamp: Optional[Union[str, datetime]] = None,
        object_type: str = "Person",
    ) -> Dict[str, Any]:
        """Dispatches a confirmed railway intrusion alert with CCTV photographic evidence.
        
        Parameters:
            image_path: Path to the CCTV evidence JPEG/PNG snapshot.
            location: Level crossing identifier (e.g. 'LC-102').
            danger_level: Risk classification ('CRITICAL', 'HIGH', 'MEDIUM').
            confidence: Object detection confidence percentage (0.0 to 100.0).
            event_id: Unique safety event identifier.
            timestamp: Time of detection (string or datetime).
            object_type: Classified entity ('Person', 'Vehicle', etc.).
            
        Returns:
            Structured dictionary reporting delivery outcome, HTTP status, and message ID.
        """
        # Format timestamp
        if isinstance(timestamp, datetime):
            ts_str = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        elif isinstance(timestamp, str):
            ts_str = timestamp
        else:
            ts_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        loc = location or self.location

        # Credential validation
        if not self.bot_token:
            err = "Telegram Bot Token is not configured."
            logger.error(f"[ERROR] Telegram dispatch failed: {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": 401,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }

        if not self.chat_id:
            err = "Telegram Chat ID is not configured."
            logger.error(f"[ERROR] Telegram dispatch failed: {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": 400,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }

        # Validate image evidence
        p_image = Path(image_path)
        if not p_image.exists() or not p_image.is_file():
            err = f"Missing CCTV image at '{image_path}'"
            logger.error(f"[ERROR] Telegram dispatch failed: {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": 404,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }

        caption = self.format_alert_caption(
            location=loc,
            danger_level=danger_level,
            confidence=confidence,
            event_id=event_id,
            timestamp_str=ts_str,
            object_type=object_type,
        )

        logger.info(f"Telegram dispatch initiated: Event {event_id}")

        # Dispatch via Telegram sendPhoto API (Never log the bot token)
        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            with open(p_image, "rb") as photo_file:
                resp = requests.post(
                    api_url,
                    data={"chat_id": self.chat_id, "caption": caption},
                    files={"photo": photo_file},
                    timeout=self.timeout,
                )

            if resp.status_code == 200:
                resp_json = resp.json()
                msg_id = resp_json.get("result", {}).get("message_id")
                logger.info(f"[SUCCESS] Telegram alert delivered: Event {event_id}, Message ID {msg_id}")
                self._dispatched_events[event_id] = {
                    "severity": danger_level.upper(),
                    "timestamp": datetime.now().timestamp(),
                    "message_id": msg_id,
                }
                self.stats["dispatched"] += 1
                return {
                    "success": True,
                    "status_code": 200,
                    "message_id": msg_id,
                    "event_id": event_id,
                    "error": None,
                    "timestamp": ts_str,
                }
            else:
                try:
                    resp_data = resp.json()
                    err_msg = resp_data.get("description", resp.text)
                except Exception:
                    err_msg = resp.text
                logger.error(f"[ERROR] Telegram dispatch failed: Event {event_id}, HTTP {resp.status_code} ({err_msg})")
                self.stats["failed"] += 1
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "message_id": None,
                    "event_id": event_id,
                    "error": f"Telegram API error: {err_msg}",
                    "timestamp": ts_str,
                }

        except requests.exceptions.Timeout:
            err = f"Network timeout ({self.timeout}s) connecting to Telegram API."
            logger.error(f"[ERROR] Telegram dispatch failed: Event {event_id}, {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": -1,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }
        except requests.exceptions.RequestException as req_err:
            err = f"Network connection error: {req_err}"
            logger.error(f"[ERROR] Telegram dispatch failed: Event {event_id}, {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": -1,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }
        except Exception as ex:
            err = f"Unexpected failure: {ex}"
            logger.error(f"[ERROR] Telegram dispatch failed: Event {event_id}, {err}")
            self.stats["failed"] += 1
            return {
                "success": False,
                "status_code": 500,
                "message_id": None,
                "event_id": event_id,
                "error": err,
                "timestamp": ts_str,
            }

    def send_text_message(self, message: str) -> Dict[str, Any]:
        """Dispatches a text message (e.g., system status, test ping, recovery)."""
        if not self.bot_token or not self.chat_id:
            return {"success": False, "status_code": 401, "error": "Unconfigured credentials"}

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(
                api_url,
                data={"chat_id": self.chat_id, "text": message},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                msg_id = resp.json().get("result", {}).get("message_id")
                return {"success": True, "status_code": 200, "message_id": msg_id, "error": None}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "status_code": -1, "error": str(e)}

    def dispatch_async(
        self,
        image_path: Union[str, Path],
        location: Optional[str] = None,
        danger_level: str = "CRITICAL",
        confidence: float = 95.0,
        event_id: str = "EVT-UNKNOWN",
        timestamp: Optional[Union[str, datetime]] = None,
        object_type: str = "Person",
    ) -> concurrent.futures.Future:
        """Asynchronously dispatches an emergency alert without blocking the video loop."""
        return self.executor.submit(
            self.send_emergency_alert,
            image_path=image_path,
            location=location,
            danger_level=danger_level,
            confidence=confidence,
            event_id=event_id,
            timestamp=timestamp,
            object_type=object_type,
        )

    def shutdown(self, wait: bool = False) -> None:
        """Shuts down the background thread worker."""
        self.executor.shutdown(wait=wait)


# Singleton / Global default instance
_default_dispatcher: Optional[TelegramDispatcher] = None


def get_default_dispatcher() -> TelegramDispatcher:
    global _default_dispatcher
    if _default_dispatcher is None:
        _default_dispatcher = TelegramDispatcher()
    return _default_dispatcher


def send_emergency_alert(
    image_path: Union[str, Path],
    location: Optional[str] = None,
    danger_level: str = "CRITICAL",
    confidence: float = 95.0,
    event_id: str = "EVT-UNKNOWN",
    timestamp: Optional[Union[str, datetime]] = None,
    object_type: str = "Person",
) -> Dict[str, Any]:
    """Module-level convenience function fulfilling the prompt API contract."""
    dispatcher = get_default_dispatcher()
    return dispatcher.send_emergency_alert(
        image_path=image_path,
        location=location,
        danger_level=danger_level,
        confidence=confidence,
        event_id=event_id,
        timestamp=timestamp,
        object_type=object_type,
    )
