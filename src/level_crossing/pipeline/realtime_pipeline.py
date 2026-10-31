"""Real-time pipeline with bounded queue, frame-drop policy, and processing latency tracking."""

import queue
import threading
import time
from typing import Optional, Dict, Any, List
import numpy as np

from level_crossing.common.types import CrossingState, SeverityLevel, HealthStatus
from level_crossing.common.config import SystemConfig
from level_crossing.common.logger import get_logger
from level_crossing.detection.detector import BaseDetector, YOLOv8Detector
from level_crossing.tracking.tracker import ByteTracker
from level_crossing.scene_state.zone_manager import ZoneManager
from level_crossing.severity.matrix import SeverityMatrix
from level_crossing.severity.evaluator import SeverityEvaluator
from level_crossing.events.event_manager import EventManager
from level_crossing.events.train_suppression import TrainMisclassificationMitigation
from level_crossing.alerts.alert_engine import AlertEngine
from level_crossing.video.frame import Frame

logger = get_logger("realtime_pipeline")


class RealtimePipeline:
    """Multi-threaded real-time inference pipeline with bounded frame queue and drop metrics."""

    def __init__(
        self,
        config: SystemConfig,
        detector: Optional[BaseDetector] = None,
        queue_maxsize: int = 5,
        snapshots_dir: str = "data/snapshots",
    ):
        self.config = config
        self.detector = detector or YOLOv8Detector(
            weights_path=config.thresholds.detection.model_weights,
            confidence_thresholds=config.thresholds.detection.confidence_thresholds,
            device=config.thresholds.detection.device,
        )
        self.tracker = ByteTracker(
            iou_threshold=config.thresholds.tracking.iou_threshold,
            max_lost_frames=config.thresholds.tracking.max_lost_frames,
        )
        self.zone_manager = ZoneManager(
            config=config.zones,
            hysteresis_normalized=config.thresholds.scene_state.boundary_hysteresis_normalized,
        )
        self.severity_matrix = SeverityMatrix(config=config.severity_matrix)
        self.severity_evaluator = SeverityEvaluator(matrix=self.severity_matrix)
        self.event_manager = EventManager(thresholds=config.thresholds.event_manager)
        self.train_suppression = TrainMisclassificationMitigation(
            enabled=config.thresholds.train_suppression.enabled,
        )
        self.alert_engine = AlertEngine(snapshots_dir=snapshots_dir)

        self.frame_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)
        self.dropped_frames: int = 0
        self.processed_frames: int = 0
        self.processing_latencies_ms: List[float] = []
        self._running: bool = False
        self._worker_thread: Optional[threading.Thread] = None
        self.crossing_state: CrossingState = CrossingState.OPEN

    def set_crossing_state(self, state: CrossingState) -> None:
        self.crossing_state = state

    def push_frame(self, image: np.ndarray, frame_idx: int) -> bool:
        """Pushes a new captured frame to the pipeline. Drops if queue is full."""
        capture_wall_time = time.perf_counter()
        item = (image, frame_idx, capture_wall_time)
        try:
            self.frame_queue.put_nowait(item)
            return True
        except queue.Full:
            self.dropped_frames += 1
            return False

    def start(self) -> None:
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Real-time pipeline worker started")

    def stop(self) -> None:
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
        logger.info("Real-time pipeline worker stopped")

    def _worker_loop(self) -> None:
        while self._running:
            try:
                image, frame_idx, capture_time = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            t_start = time.perf_counter()
            wall_timestamp = time.time()
            h, w = image.shape[:2]

            # 1. Detect
            det_result = self.detector.detect(image, frame_idx, wall_timestamp)

            # 2. Track
            tracks = self.tracker.update(det_result.detections, frame_idx, wall_timestamp)

            # 3. Scene State
            scene_states = self.zone_manager.evaluate_tracks(
                tracks, self.crossing_state, w, h, wall_timestamp
            )

            # 4. Suppression
            filtered_states = self.train_suppression.filter_tracks(
                scene_states, w, h, wall_timestamp
            )

            # 5. Severity
            evaluated_pairs = []
            for ss in filtered_states:
                sev = self.severity_evaluator.evaluate_track(ss)
                evaluated_pairs.append((ss, sev))

            # 6. Event Manager
            actions = self.event_manager.process(evaluated_pairs, self.crossing_state, wall_timestamp)

            # 7. Alert Engine
            if actions:
                self.alert_engine.dispatch(actions, image, wall_timestamp)
                # Processing latency: capture to alert decision
                proc_lat_ms = (time.perf_counter() - capture_time) * 1000.0
                self.processing_latencies_ms.append(proc_lat_ms)

            self.processed_frames += 1
            self.frame_queue.task_done()
