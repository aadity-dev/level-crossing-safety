"""Alert generation engine managing dispatch, snapshots, and event correlation."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from level_crossing.common.types import AlertStatus, SeverityLevel
from level_crossing.common.logger import get_logger
from level_crossing.events.event_manager import EventAction
from level_crossing.alerts.alert import AlertRecord
from level_crossing.alerts.sound_simulator import SoundSimulator
from level_crossing.alerts.telegram_dispatcher import TelegramDispatcher

logger = get_logger("alert_engine")


class AlertEngine:
    """Consumes event state actions, captures snapshots, and persists alerts."""

    def __init__(
        self,
        snapshots_dir: str | Path = "data/snapshots",
        enable_audio: bool = False,
        telegram_dispatcher: Optional[TelegramDispatcher] = None,
    ):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.sound_simulator = SoundSimulator(enable_audio=enable_audio)
        self.telegram_dispatcher = telegram_dispatcher
        self.alerts_history: List[AlertRecord] = []

    def dispatch(
        self,
        actions: List[EventAction],
        current_frame: Optional[np.ndarray] = None,
        timestamp: float = 0.0,
    ) -> List[AlertRecord]:
        """Dispatches alerts corresponding to event actions."""
        dispatched: List[AlertRecord] = []

        for action in actions:
            event = action.event
            snapshot_path: Optional[str] = None

            # Capture evidence snapshot on CONFIRMED or ESCALATED
            if current_frame is not None and action.alert_type.value in ("INITIAL", "ESCALATION"):
                snap_filename = f"{event.event_id}_{action.alert_type.value}_{int(timestamp * 1000)}.jpg"
                snap_full_path = self.snapshots_dir / snap_filename
                try:
                    cv2.imwrite(str(snap_full_path), current_frame)
                    snapshot_path = str(snap_full_path)
                    logger.info(f"CCTV evidence captured: {snapshot_path}")
                except Exception as e:
                    logger.error(f"Failed to save evidence snapshot: {e}")

            alert = AlertRecord.create(
                event_id=event.event_id,
                alert_type=action.alert_type,
                severity=event.current_severity,
                timestamp=timestamp,
                message=action.message,
                snapshot_path=snapshot_path,
            )
            alert.status = AlertStatus.DISPATCHED

            # Correlate alert with event
            event.alert_ids.append(alert.alert_id)
            self.alerts_history.append(alert)
            dispatched.append(alert)

            # Trigger acoustic simulation
            self.sound_simulator.play_alert(event.current_severity)

            # Structured logging per specification
            logger.info(f"Intrusion confirmed: Event {event.event_id}, Track {event.track_id}")
            logger.info(f"Danger level calculated: {event.current_severity.value}")

            logger.warning(
                f"ALERT DISPATCHED: [{alert.alert_id}] ({alert.alert_type.value} - {alert.severity.value}) {alert.message}"
            )

            # Automated Telegram Emergency Dispatch Integration
            if self.telegram_dispatcher and snapshot_path:
                if self.telegram_dispatcher.should_dispatch(event.event_id, event.current_severity.value):
                    conf = event.confidence
                    conf_pct = conf * 100.0 if (0.0 < conf <= 1.0) else (conf if conf > 1.0 else 95.0)
                    self.telegram_dispatcher.dispatch_async(
                        image_path=snapshot_path,
                        danger_level=event.current_severity.value,
                        confidence=conf_pct,
                        event_id=event.event_id,
                        object_type=event.rule_class.value,
                    )

        return dispatched

    def reset(self) -> None:
        self.alerts_history.clear()
