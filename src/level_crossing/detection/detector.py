"""Object detection pipeline with YOLO and fallback implementations."""

from abc import ABC, abstractmethod
import time
from typing import List, Dict, Optional
import numpy as np

from level_crossing.common.types import BoundingBox, RuleClass
from level_crossing.common.exceptions import DetectionError
from level_crossing.common.logger import get_logger
from level_crossing.detection.class_mapping import ClassMapper
from level_crossing.detection.detection_result import DetectionResult, FrameDetections

logger = get_logger("detector")


class BaseDetector(ABC):
    """Abstract interface for object detectors."""

    @abstractmethod
    def detect(self, image: np.ndarray, frame_idx: int = 0, timestamp_sec: float = 0.0) -> FrameDetections:
        """Runs detection on a single frame."""
        pass


class YOLOv8Detector(BaseDetector):
    """Production YOLOv8 detector with class filtering, confidence gates, and timing."""

    def __init__(
        self,
        weights_path: str = "yolov8n.pt",
        confidence_thresholds: Optional[Dict[str, float]] = None,
        device: str = "mps",
        class_mapper: Optional[ClassMapper] = None,
    ):
        self.weights_path = weights_path
        self.conf_thresholds = confidence_thresholds or {"default": 0.35}
        self.default_conf = self.conf_thresholds.get("default", 0.35)
        self.class_mapper = class_mapper or ClassMapper()
        self.device = device
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from ultralytics import YOLO
            import torch

            # Validate device availability
            if self.device == "mps" and not torch.backends.mps.is_available():
                logger.warning("Apple MPS requested but not available. Falling back to CPU.")
                self.device = "cpu"

            logger.info(f"Loading YOLO weights from {self.weights_path} on device '{self.device}'")
            self._model = YOLO(self.weights_path)
        except Exception as e:
            raise DetectionError(f"Failed to initialize YOLO model: {e}") from e

    def detect(self, image: np.ndarray, frame_idx: int = 0, timestamp_sec: float = 0.0) -> FrameDetections:
        if image is None or image.size == 0:
            raise DetectionError(f"Received empty or null image at frame {frame_idx}")

        h, w = image.shape[:2]
        t0 = time.perf_counter()

        try:
            # Run inference
            results = self._model(image, conf=self.default_conf, device=self.device, verbose=False)
            dt_ms = (time.perf_counter() - t0) * 1000.0

            detections: List[DetectionResult] = []
            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    class_name = self._model.names.get(cls_id, "unknown")
                    rule_class = self.class_mapper.map_class(class_name)

                    # Check per-class threshold
                    req_conf = self.conf_thresholds.get(
                        rule_class.value,
                        self.conf_thresholds.get(class_name, self.default_conf),
                    )
                    if conf < req_conf:
                        continue

                    xyxy = box.xyxy[0].cpu().numpy()
                    x1 = float(max(0.0, min(float(xyxy[0]), float(w))))
                    y1 = float(max(0.0, min(float(xyxy[1]), float(h))))
                    x2 = float(max(0.0, min(float(xyxy[2]), float(w))))
                    y2 = float(max(0.0, min(float(xyxy[3]), float(h))))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    detections.append(
                        DetectionResult(
                            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                            confidence=conf,
                            raw_class_name=class_name,
                            rule_class=rule_class,
                            raw_class_id=cls_id,
                        )
                    )

            return FrameDetections(
                frame_idx=frame_idx,
                timestamp_sec=timestamp_sec,
                detections=detections,
                inference_time_ms=dt_ms,
            )
        except Exception as e:
            logger.error(f"Detection failed on frame {frame_idx}: {e}")
            raise DetectionError(f"Detection inference failure: {e}") from e


class MockDetector(BaseDetector):
    """Deterministic mock detector for tests and scenario generation."""

    def __init__(self, predefined_detections: Optional[Dict[int, List[DetectionResult]]] = None):
        self.predefined = predefined_detections or {}

    def set_frame_detections(self, frame_idx: int, detections: List[DetectionResult]) -> None:
        self.predefined[frame_idx] = detections

    def detect(self, image: np.ndarray, frame_idx: int = 0, timestamp_sec: float = 0.0) -> FrameDetections:
        dets = self.predefined.get(frame_idx, [])
        return FrameDetections(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            detections=dets,
            inference_time_ms=1.5,
        )
