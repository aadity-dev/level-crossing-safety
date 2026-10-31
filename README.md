# Railway Level Crossing Safety Monitoring System (V3.1)
### Automated Intruder Alerting via Edge Computer Vision

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.15](https://img.shields.io/badge/PyTorch-2.15-orange.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-red.svg)](https://streamlit.io/)
[![Architecture: V3.1](https://img.shields.io/badge/Spec-V3.1_Master-purple.svg)](DECISIONS.md)

> **SAFETY DISCLAIMER:** This system is a research and portfolio prototype. It is **NOT** a certified railway safety instrument (CENELEC SIL-4) and must **NEVER** interface with or control railway barriers, signals, interlocking circuits, or train operations.

---

## 1. System Overview & Architecture

The system monitors railway level crossings using edge vision to detect intruders, evaluate contextual risk based on geometric safety zones and crossing operational states, manage temporal hazard lifecycles, and generate auditable alerts.

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

---

## 2. Key Engineering Principles

1. **Strict Separation of Concerns:**
   - Object detection produces raw bounding boxes; it never makes safety decisions.
   - Tracking manages object IDs and motion trajectories; it does not own zones or severity.
   - Scene State owns geometric zone membership and continuous **zone dwell**.
   - Severity Evaluator is **purely stateless**: `(crossing_state, zone_type, rule_class) -> severity`.
   - Event Manager is **stateful**, owning the **unsafe-condition timer**, lifecycle transitions, and cooldown.
2. **Two Separate Clocks & Timers:**
   - **Zone dwell timer:** Continuous time inside a zone polygon.
   - **Unsafe-condition timer:** Begins when the condition becomes hazardous. When a pedestrian is already in a zone and the crossing switches to `TRAIN_APPROACHING`, the unsafe timer begins **at the state transition**, not the zone entry time.
3. **Severity Matrix Completeness:**
   - All 64 combinations ($4\text{ crossing states} \times 4\text{ zone types} \times 4\text{ rule classes}$) are explicitly defined and validated on startup.
   - Unhandled cases trigger a fallback to `HIGH` with an audit log to SQLite.
   - `UNKNOWN` crossing state automatically sets system health to `DEGRADED`.
4. **Train Misclassification Suppression:**
   - Vehicles (trucks/buses) overlapping a train bounding box during `TRAIN_APPROACHING` / `TRAIN_PASSING` are suppressed as train cars and recorded in the audit log.
5. **Edge Deployment Benchmarking:**
   - Apple Silicon Metal Performance Shaders (MPS): **16.4 ms (60.9 FPS)**.
   - ONNX Runtime CPU (Edge-Proxy): **37.0 ms (27.0 FPS)**.

---

## 3. Quickstart & Installation

### Prerequisites
- macOS (Apple Silicon M-series recommended) or Linux (x86_64 / aarch64)
- Python 3.12

### Setup Virtual Environment
```bash
# Clone or navigate to the project directory
cd ~/Desktop/level-crossing-safety

# Create and activate Python 3.12 environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install package in editable development mode
pip install -e .
```

---

## 4. Running the System

### 1. Execute End-to-End Replay Pipeline
Run a deterministic replay scenario that performs detection, tracking, zone analysis, risk evaluation, and exports an annotated video:
```bash
python scripts/run_pipeline.py \
  --video data/controlled/validation/scenario_01_person_danger_track.mp4 \
  --state TRAIN_APPROACHING \
  --output data/controlled/validation/annotated_scenario_01.mp4
```

### 2. Launch the FastAPI REST Service
```bash
uvicorn level_crossing.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health endpoint: `GET /api/v1/health`
- Events endpoint: `GET /api/v1/events`
- Alerts endpoint: `GET /api/v1/alerts`

### 3. Launch the Streamlit Monitoring Dashboard
```bash
streamlit run src/level_crossing/dashboard/app.py
```
Opens an interactive UI showing:
- Real-time crossing operational state switcher.
- Active system health indicator (`HEALTHY` vs `DEGRADED`).
- Live active events table with escalation counters.
- Auditable alerts dispatch stream.
- Evidence snapshot image gallery.
- Interactive zone and matrix rule inspector.

---

## 5. Testing & Verification

Run the complete 31-test suite covering unit, integration, regression, and end-to-end replay pipelines:
```bash
pytest -v
```

### Run Multi-Target Benchmark
```bash
python scripts/run_benchmark.py
```

### Run 4-Way Ablation Study
```bash
python scripts/run_evaluation.py
```

---

## 6. Project Structure

```text
level-crossing-safety/
├── configs/
│   ├── zones.yaml               # Polygon safety zones
│   ├── severity_matrix.yaml     # 64-combination V3.1 risk matrix
│   ├── thresholds.yaml          # Detector, tracker, and dwell thresholds
│   └── logging.yaml             # Structured logging configuration
├── data/
│   ├── controlled/validation/   # Validation video scenarios and ground truth CSV
│   └── snapshots/               # Event evidence snapshots
├── docs/
│   ├── architecture.md          # Full V3.1 architecture documentation
│   ├── dataset.md               # Dataset provenance and footage plan
│   ├── annotation_protocol.md   # Ground-truth schema & dual-timestamp formula
│   ├── evaluation.md            # Evaluation metrics and 4-way ablation
│   ├── deployment.md            # Edge benchmark numbers & deployment guides
│   ├── limitations.md           # Sensor boundaries and failure modes
│   └── failure_analysis.md      # Automated mitigation strategies
├── notebooks/
│   ├── 01_image_fundamentals.py # NumPy array manipulation
│   ├── 02_opencv_basics.py      # Transforms, filters, drawing
│   └── 03_image_visualization.py# Bounding boxes, polygon zones, IoU
├── scripts/
│   ├── generate_synthetic_scenario.py
│   ├── inspect_dataset.py
│   ├── validate_annotations.py
│   ├── check_duplicates.py
│   ├── run_pipeline.py
│   ├── run_evaluation.py
│   └── run_benchmark.py
├── src/level_crossing/
│   ├── common/                  # Types, exceptions, config loader, logging
│   ├── detection/               # YOLOv8, class mapping, detection result
│   ├── tracking/                # ByteTrack, IoU association, track lifecycle
│   ├── scene_state/             # Polygon zones, dwell tracker, kinematics
│   ├── severity/                # Stateless V3.1 severity matrix evaluator
│   ├── events/                  # Stateful event manager, train suppression
│   ├── alerts/                  # Alert engine, sound simulator, snapshots
│   ├── video/                   # Reader, annotator, MP4 encoder
│   ├── database/                # SQLite V3.1 schema, repositories
│   ├── pipeline/                # Deterministic replay & realtime pipelines
│   ├── evaluation/              # 1-to-1 matcher, metrics, ablation runner
│   ├── deployment/              # ONNX exporter, multi-target benchmark
│   ├── api/                     # FastAPI app, routes, schemas, services
│   └── dashboard/               # Streamlit monitoring UI
├── tests/
│   ├── unit/                    # 25 unit tests
│   ├── integration/             # Pipeline & API integration tests
│   ├── regression/              # Invariant & configuration tests
│   └── end_to_end/              # End-to-end replay test
├── DECISIONS.md                 # Frozen design choices & scope boundaries
├── pyproject.toml               # Package build metadata
└── README.md                    # System documentation
```
