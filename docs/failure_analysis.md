# Failure Analysis and Mitigation Strategies (V3.1)

## 1. Failure Modes and Automated Mitigations

| Failure Mode | Root Cause | Observable Symptom | Automated Mitigation |
| :--- | :--- | :--- | :--- |
| **Train Carriage Misclassified as Truck/Bus** | Visual appearance of long freight wagons or flatcars resembles cargo trucks in COCO-trained YOLO models. | False high-severity alert during active train movement. | **Train Misclassification Mitigation:** During `TRAIN_APPROACHING` and `TRAIN_PASSING`, any vehicle box overlapping a detected train ($\text{IoU} \ge 0.25$) or exceeding 35% of frame area is suppressed and logged with full audit metadata. |
| **Boundary Jitter / Flutter** | Pedestrian standing near zone border has bounding box bottom-center oscillating across polygon boundary. | Repeated enter/exit events causing alert flood. | **Boundary Hysteresis:** An adaptive $1.5\%$ margin is maintained around zone polygons. A track currently assigned to a zone remains locked to it unless it moves beyond the hysteresis band. |
| **Camera Feed Drop or Corruption** | Network RTSP drop or corrupted video frame buffer. | Decoder crash or empty image passed to detector. | **Explicit Exception Handling:** `VideoProcessingError` and `DetectionError` are caught gracefully. Consecutive corrupt frames set system health to `DEGRADED`. |
| **Loss of Crossing Telemetry** | Signal feed disconnected or ambiguous crossing status. | Undefined risk level. | **`UNKNOWN` State Fail-Safe:** The system automatically drops into safe degraded mode. System health transitions from `HEALTHY` to `DEGRADED`, and danger track rules escalate to `CRITICAL` severity. |
| **Alert Storms on Persistent Hazard** | An entity remains stopped on track for multiple minutes. | Thousands of duplicate alerts flooding operator dashboard. | **Alert Engine Cooldown:** Configured 5-second cooldown timer prevents duplicate alerts on the same track while emitting auditable `ESCALATION` notifications at defined intervals. |
