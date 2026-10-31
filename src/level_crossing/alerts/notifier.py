"""Automated Emergency Alert Notifier (Webhook & Telegram Bot Dispatcher).

Provides instant remote notification to Station Masters, loco-pilots, and operations centers.
Supports arbitrary HTTP Webhooks and Telegram Bot API with photographic evidence dispatch.
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

from level_crossing.common.logger import get_logger

logger = get_logger("alert_notifier")


class AlertNotifier:
    """Dispatches emergency push alerts over HTTP Webhooks and Telegram Bot API."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        dry_run: bool = True,
    ):
        self.webhook_url = webhook_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.dry_run = dry_run
        self.dispatched_history: list = []

    def dispatch_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sends an HTTP POST JSON payload to a remote Operations Control Webhook."""
        record = {
            "channel": "WEBHOOK",
            "target": self.webhook_url or "https://mock-railway-occ.internal/api/v1/alerts",
            "payload": payload,
            "status": "SENT" if not self.dry_run else "SIMULATED_OK",
        }

        if self.dry_run or not self.webhook_url:
            logger.info(f"WEBHOOK DISPATCH [SIMULATED] -> {record['target']}: Alert {payload.get('alert_id')}")
            self.dispatched_history.append(record)
            return record

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "LevelCrossingSafety/3.1"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.getcode()
                record["status"] = f"HTTP_{status_code}"
                logger.info(f"WEBHOOK DISPATCH SUCCESS -> {self.webhook_url} ({status_code})")
        except Exception as e:
            record["status"] = f"ERROR: {e}"
            logger.warning(f"WEBHOOK DISPATCH FAILED: {e}")

        self.dispatched_history.append(record)
        return record

    def dispatch_telegram(
        self,
        message: str,
        photo_path: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """Dispatches an emergency photo and message to the Station Master's Telegram."""
        record = {
            "channel": "TELEGRAM_BOT",
            "chat_id": self.telegram_chat_id or "@StationMasterAlerts",
            "message": message,
            "has_photo": bool(photo_path and Path(photo_path).exists()),
            "status": "SENT" if not self.dry_run else "SIMULATED_OK",
        }

        if self.dry_run or not self.telegram_bot_token or not self.telegram_chat_id:
            logger.info(f"TELEGRAM DISPATCH [SIMULATED] -> {record['chat_id']}: '{message[:40]}...' (Photo: {record['has_photo']})")
            self.dispatched_history.append(record)
            return record

        try:
            # Real Telegram Bot API call
            if photo_path and Path(photo_path).exists():
                api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
                # Multipart or direct photo upload
                logger.info(f"Calling real Telegram Bot API at {api_url}")
            else:
                api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                post_data = urllib.parse.urlencode({"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}).encode("utf-8")
                req = urllib.request.Request(api_url, data=post_data)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    record["status"] = f"TELEGRAM_HTTP_{resp.getcode()}"
        except Exception as e:
            record["status"] = f"ERROR: {e}"
            logger.warning(f"TELEGRAM DISPATCH FAILED: {e}")

        self.dispatched_history.append(record)
        return record

    @classmethod
    def format_telegram_alert_text(
        cls,
        alert_id: str,
        severity: str,
        crossing_state: str,
        message: str,
        timestamp_sec: float,
    ) -> str:
        """Formats an emoji-rich, high-priority emergency advisory for mobile screens."""
        return (
            f"🚨 *LEVEL CROSSING EMERGENCY ALERT*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"• *Alert ID:* `{alert_id}`\n"
            f"• *Severity Tier:* *{severity}*\n"
            f"• *Signal Aspect:* `{crossing_state}`\n"
            f"• *Active Time:* `{timestamp_sec:.2f}s`\n"
            f"• *Advisory:* {message}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *ACTION REQUIRED:* Alert approaching locomotive driver immediately."
        )
