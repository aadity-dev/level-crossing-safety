"""Deterministic replay processing pipeline for repeatable scenario validation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Tuple
import time
import numpy as np
import cv2

from level_crossing.common.types import CrossingState, SeverityLevel, HealthStatus, ZoneType
from level_crossing.common.config import SystemConfig
from level_crossing.common.logger import get_logger
from level_crossing.detection.detector import BaseDetector, YOLOv8Detector
from level_crossing.detection.train_approach_estimator import TrainApproachEstimator
from level_crossing.analytics.hazard_heatmap import HazardHeatmapGenerator
from level_crossing.tracking.tracker import ByteTracker
from level_crossing.scene_state.zone_manager import ZoneManager, TrackSceneState
from level_crossing.severity.matrix import SeverityMatrix
from level_crossing.severity.evaluator import SeverityEvaluator
from level_crossing.events.event_manager import EventManager
from level_crossing.events.train_suppression import TrainMisclassificationMitigation
from level_crossing.alerts.alert_engine import AlertEngine
from level_crossing.alerts.alert import AlertRecord
from level_crossing.video.video_reader import VideoReader
from level_crossing.video.video_writer import VideoWriter, VideoAnnotator
from level_crossing.database.db import DatabaseManager
from level_crossing.database.repository import EventRepository, AlertRepository, SystemLogRepository

logger = get_logger("replay_pipeline")


@dataclass
class ReplaySummary:
    video_source: str
    total_frames_processed: int
    duration_seconds: float
    events_generated: int
    alerts_generated: int
    highest_severity_observed: SeverityLevel
    system_health: HealthStatus
    elapsed_wall_time_sec: float
    average_fps: float
    heatmap_path: Optional[str] = None
    heatmap_analytics: Optional[Dict[str, Any]] = None
    optical_train_detected: bool = False


class ReplayPipeline:
    """Full-featured deterministic pipeline executing video replay with V3.1 safety engine."""

    def __init__(
        self,
        config: SystemConfig,
        detector: Optional[BaseDetector] = None,
        db_path: str | Path = "data/level_crossing.sqlite3",
        snapshots_dir: str | Path = "data/snapshots",
        save_to_db: bool = True,
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
            overlap_iou_threshold=config.thresholds.train_suppression.overlap_iou_threshold,
            area_ratio_threshold=config.thresholds.train_suppression.area_ratio_threshold,
        )
        self.alert_engine = AlertEngine(snapshots_dir=snapshots_dir)

        self.save_to_db = save_to_db
        if self.save_to_db:
            self.db_manager = DatabaseManager(db_path=db_path)
            self.event_repo = EventRepository(self.db_manager)
            self.alert_repo = AlertRepository(self.db_manager)
            self.log_repo = SystemLogRepository(self.db_manager)
        else:
            self.db_manager = None

    def run(
        self,
        video_path: str | Path,
        crossing_state_timeline: Optional[Callable[[float], CrossingState]] = None,
        output_video_path: Optional[str | Path] = None,
        on_frame_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_frames: Optional[int] = None,
        autonomous_train_sensing: bool = False,
    ) -> ReplaySummary:
        """Executes full replay pipeline over the input video or live stream."""
        reader = VideoReader(video_path, realtime_mode=False)
        metadata = reader.metadata
        logger.info(f"Starting replay on {video_path} ({metadata.total_frames} frames @ {metadata.fps:.1f}fps)")

        writer: Optional[VideoWriter] = None
        if output_video_path:
            writer = VideoWriter(
                output_path=output_video_path,
                fps=metadata.fps,
                width=metadata.width,
                height=metadata.height + 36,  # extra height for telemetry banner
            )

        start_wall_time = time.perf_counter()
        highest_severity = SeverityLevel.IGNORE
        system_health = HealthStatus.HEALTHY
        processed_frames = 0
        last_timestamp = 0.0

        # Tier 2 Analytics & Optical Estimators
        heatmap_gen = HazardHeatmapGenerator(width=metadata.width, height=metadata.height)
        train_estimator = TrainApproachEstimator()
        optical_train_approaching_seen = False
        first_frame_bgr: Optional[np.ndarray] = None

        for frame in reader.frames():
            processed_frames += 1
            if max_frames is not None and processed_frames > max_frames:
                break
            timestamp = frame.timestamp_sec
            last_timestamp = timestamp

            if first_frame_bgr is None:
                first_frame_bgr = frame.image.copy()

            # 1. Detection
            det_result = self.detector.detect(frame.image, frame.frame_idx, timestamp)

            # Optical train approach evaluation
            train_status = train_estimator.update(det_result.detections, timestamp)
            if train_status.is_approaching:
                optical_train_approaching_seen = True

            # Determine crossing state from timeline, optical autonomous sensor, or default OPEN
            if crossing_state_timeline:
                current_crossing_state = crossing_state_timeline(timestamp)
            else:
                current_crossing_state = CrossingState.OPEN

            # Unmanned Crossing Autonomous Override
            if autonomous_train_sensing and train_status.is_approaching:
                current_crossing_state = CrossingState.TRAIN_APPROACHING

            if current_crossing_state == CrossingState.UNKNOWN:
                system_health = HealthStatus.DEGRADED

            # 2. Tracking
            tracks = self.tracker.update(det_result.detections, frame.frame_idx, timestamp)

            # 3. Scene State
            scene_states = self.zone_manager.evaluate_tracks(
                tracks=tracks,
                crossing_state=current_crossing_state,
                frame_width=frame.width,
                frame_height=frame.height,
                timestamp=timestamp,
            )

            # 4. Train Misclassification Suppression Mitigation
            filtered_scene_states = self.train_suppression.filter_tracks(
                track_states=scene_states,
                frame_width=frame.width,
                frame_height=frame.height,
                timestamp=timestamp,
            )

            # Spatial Hazard Heatmap Accumulation
            for trk in tracks:
                if trk.is_confirmed:
                    is_in_danger = False
                    for ss in filtered_scene_states:
                        if ss.track_id == trk.track_id and ss.zone_type == ZoneType.DANGER_TRACK:
                            is_in_danger = True
                            break
                    foot = trk.reference_point
                    heatmap_gen.add_point(foot.x, foot.y, weight=2.5 if is_in_danger else 1.0, in_danger=is_in_danger)

            # 5. Severity Evaluation (Stateless)
            evaluated_pairs: List[Tuple[TrackSceneState, SeverityLevel]] = []
            for ss in filtered_scene_states:
                sev = self.severity_evaluator.evaluate_track(ss)
                evaluated_pairs.append((ss, sev))
                if sev > highest_severity:
                    highest_severity = sev

            # 6. Event Manager (Stateful)
            actions = self.event_manager.process(
                evaluated_states=evaluated_pairs,
                crossing_state=current_crossing_state,
                timestamp=timestamp,
            )

            # 7. Alert Engine
            dispatched_alerts = self.alert_engine.dispatch(
                actions=actions,
                current_frame=frame.image,
                timestamp=timestamp,
            )

            # 8. Persistence
            if self.save_to_db:
                for action in actions:
                    self.event_repo.save(action.event)
                for alert in dispatched_alerts:
                    self.alert_repo.save(alert)

            # 9. Visualization & Writing
            if writer:
                annotated = frame.image.copy()
                annotated = VideoAnnotator.draw_zones(annotated, self.zone_manager.zones)

                track_draw_data = []
                for ss, sev in evaluated_pairs:
                    track_draw_data.append({
                        "track_id": ss.track_id,
                        "rule_class": ss.rule_class.value,
                        "bbox": ss.bbox,
                        "zone_type": ss.zone_type.value if ss.zone_type else "OUTSIDE",
                        "dwell_sec": ss.dwell_seconds,
                        "severity": sev,
                    })
                annotated = VideoAnnotator.draw_tracks(annotated, track_draw_data)
                annotated = VideoAnnotator.draw_telemetry_banner(
                    image=annotated,
                    frame_idx=frame.frame_idx,
                    timestamp_sec=timestamp,
                    crossing_state=current_crossing_state,
                    highest_severity=highest_severity,
                    active_alert_count=len(self.alert_engine.alerts_history),
                )
                writer.write_frame(annotated)

            if on_frame_callback:
                on_frame_callback({
                    "frame_idx": frame.frame_idx,
                    "timestamp": timestamp,
                    "crossing_state": current_crossing_state,
                    "active_events": list(self.event_manager.active_events.values()),
                    "dispatched_alerts": dispatched_alerts,
                    "highest_severity": highest_severity,
                })

        # Close all remaining active events at end of replay
        for event in list(self.event_manager.active_events.values()):
            event.close(last_timestamp, recovered=False)
            if self.save_to_db:
                self.event_repo.save(event)

        if writer:
            writer.close()

        total_wall_time = time.perf_counter() - start_wall_time
        fps = processed_frames / total_wall_time if total_wall_time > 0 else 0.0

        all_events = list(self.event_manager.closed_events) + list(self.event_manager.active_events.values())

        # Synthesize Spatial Hazard Density Heatmap
        heatmap_path = None
        heatmap_analytics = heatmap_gen.get_analytics()
        if output_video_path and first_frame_bgr is not None:
            out_p = Path(output_video_path)
            heatmap_file = out_p.with_name(f"heatmap_{out_p.stem}.png")
            bg_rgb = cv2.cvtColor(first_frame_bgr, cv2.COLOR_BGR2RGB)
            heatmap_rgb = heatmap_gen.generate_heatmap(bg_rgb, alpha=0.6)
            heatmap_bgr = cv2.cvtColor(heatmap_rgb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(heatmap_file), heatmap_bgr)
            heatmap_path = str(heatmap_file)
            logger.info(f"Spatial Hazard Heatmap saved to {heatmap_path}")

        return ReplaySummary(
            video_source=str(video_path),
            total_frames_processed=processed_frames,
            duration_seconds=metadata.duration_sec,
            events_generated=len(all_events),
            alerts_generated=len(self.alert_engine.alerts_history),
            highest_severity_observed=highest_severity,
            system_health=system_health,
            elapsed_wall_time_sec=total_wall_time,
            average_fps=fps,
            heatmap_path=heatmap_path,
            heatmap_analytics=heatmap_analytics,
            optical_train_detected=optical_train_approaching_seen,
        )
