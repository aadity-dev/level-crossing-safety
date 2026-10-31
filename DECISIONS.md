# Engineering Decisions and System Architecture Freezes (V3.1)

**Specification Authority:** V3.1 Master Implementation Specification  
**Project:** Level Crossing Safety Monitoring System with Automated Intruder Alerting via Edge Vision  
**Target Environment:** macOS Apple Silicon (M2), Python 3.12, PyTorch / MPS / ONNX Runtime  

---

## 1. Safety Scope and Regulatory Boundaries

> **CRITICAL BOUNDARY:** This system is an advisory research and engineering prototype. It is **NOT** a certified SIL-4 railway safety instrument. It must **NEVER** interface with or directly control railway signaling, barrier arm interlocks, track circuits, or rolling stock traction systems.

1. **Controlled Footage Only:**
   - Testing and video validation are conducted strictly using synthetic renderings or safe staged pavement footage on private property.
   - **Absolute Rule:** Under no circumstances are scenarios recorded, staged, or filmed on or near live active railway rights-of-way.
2. **Advisory Alerts:**
   - Alert notifications are dispatched for visual and acoustic operator advisory and forensic event auditing only.

---

## 2. Decoupled Pipeline Architecture & Component Ownership

The architecture strictly follows single-responsibility separation:

```text
VIDEO STREAM
  │
  ▼
[Video Ingestion]       (Replay vs Real-Time clock modes)
  │
  ▼
[Object Detection]      (Raw class, confidence, bounding box; no safety logic)
  │
  ▼
[Object Tracking]       (ByteTrack IoU association, track IDs, trajectory, loss grace)
  │
  ▼
[Scene State]           (Polygon zone membership, bottom-center ref point, zone dwell)
  │
  ▼
[Severity Evaluator]    (Purely STATELESS: (state, zone, rule_class) -> Severity)
  │
  ▼
[Event Manager]         (STATEFUL: Unsafe-condition timer, lifecycle, escalation, cooldown)
  │
  ▼
[Alert Engine]          (Multi-alert dispatch, evidence snapshots, sound simulation)
  │
  ▼
[Persistence & API]     (SQLite relational schema V3.1, FastAPI, Streamlit Dashboard)
```

### Component Responsibility Table

| Component | Owns | MUST NOT Own |
| :--- | :--- | :--- |
| **Detection** | Raw class, confidence, bounding box | Safety decisions |
| **Tracking** | Track ID, bbox history, lifetime, last-seen | Zone, dwell, severity |
| **Scene State** | Zone membership, zone dwell, movement, crossing state | Severity, event lifecycle |
| **Severity Evaluator** | Stateless `(state, zone_type, class) -> severity` | Time, history, counters |
| **Event Manager** | Unsafe-condition timer, lifecycle, escalation, cooldown | Geometry, image pixels |
| **Alert Engine** | Dispatch simulation, snapshots, acoustic simulation | Detection or risk logic |
| **Persistence** | Relational events, alerts, zones, system logs | Safety decisions |
| **API / Dashboard** | Read and present system state and telemetry | Core business heuristics |

---

## 3. Strict Two-Timer Separation

To eliminate race conditions and temporal ambiguity, two separate clocks and timers are maintained:

1. **Zone Dwell Timer (Owned by Scene State):**
   - Measures continuous wall/video time spent inside a geometric zone boundary.
   - Resets to `0.0` immediately if the tracked reference point leaves the zone.
2. **Unsafe-Condition Timer (Owned by Event Manager):**
   - Measures continuous elapsed time in an **alert-relevant unsafe condition** (e.g., `MEDIUM`, `HIGH`, `CRITICAL`).
   - Starts when the condition becomes unsafe.
   - **State Transition Rule:** If an object is already occupying a zone when the crossing state transitions into danger (e.g., person in pedestrian path during `OPEN` when crossing switches to `TRAIN_APPROACHING`), the unsafe-condition timer starts **at the exact timestamp of the state transition**, not the zone entry time.

---

## 4. Latency Definitions

| Metric | Applicable Mode | Strict Mathematical Definition |
| :--- | :--- | :--- |
| **Decision Latency** | Replay Mode | `alert_video_timestamp - gt_event_start_time` |
| **Processing Latency** | Real-Time Mode | `alert_wall_clock_time - capture_wall_clock_time` |

Replay decision latency must **never** be cited as runtime inference latency.

---

## 5. Ground Truth Event Matching Formula

Ground truth intrusion events are parameterized by:
$$\text{GT start\_time} = \max(\text{zone\_entry\_time}, \text{unsafe\_state\_start\_time})$$

Matching criteria:
- 1-to-1 matching with Hungarian / greedy temporal alignment.
- Compatible rule class and event type.
- Temporal overlap > 0.5s.
- Start-time tolerance $\le 2.0\text{s}$.

---

## 6. Train Misclassification Mitigation Protocol

In states `TRAIN_APPROACHING` and `TRAIN_PASSING`:
- Any detected `vehicle` (truck/bus) that overlaps with a detected `train` bounding box with $\text{IoU} \ge 0.25$ is suppressed as a carriage/locomotive component.
- Any vehicle bounding box exceeding 35% of total frame area during train transit is flagged as an oversized train body.
- **Audit Rule:** Suppressions are never silent; each suppression is logged with timestamp, track ID, and reason into `suppression_history` and `system_logs`.

---

## 7. Model and Library Licensing

- **Ultralytics YOLOv8:** Licensed under AGPLv3. For internal evaluation, research, and non-commercial portfolio prototyping. Commercial distributions must either obtain an enterprise commercial license from Ultralytics or deploy using open Apache-2.0 ONNX / Torchvision surrogates.
- **OpenCV / PyTorch / Shapely / FastAPI / Streamlit:** Permissive BSD / MIT / Apache 2.0 licenses.
