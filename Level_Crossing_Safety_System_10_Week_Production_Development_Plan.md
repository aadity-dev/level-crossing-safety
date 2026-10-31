# Level Crossing Safety Monitoring System with Automated Intruder Alerting via Edge Vision

## 10-Week Production-Oriented Development Plan

**Project location:** `~/Desktop/level-crossing-safety/`\
**Environment:** macOS Apple M2, VS Code, Python 3.12, `.venv`\
**Specification authority:** V3.1 Master Implementation Specification

> This is a research/portfolio prototype, not a railway-certified safety
> system. It must not control railway barriers, signals, or train
> operations.

------------------------------------------------------------------------

# 1. Project Goal and Architecture

Build a state-aware computer-vision system that detects and tracks
people and vehicles, understands their location relative to configured
crossing zones, evaluates contextual risk, manages safety events over
time, and generates auditable alerts.

``` text
VIDEO
  -> Video Ingestion
  -> Object Detection (YOLO)
  -> Object Tracking (ByteTrack)
  -> Scene State (zone membership, zone dwell, movement, crossing state)
  -> Severity Evaluator (STATELESS)
  -> Event Manager (STATEFUL)
  -> Alert Engine
       -> Snapshots / SQLite / API
       -> Dashboard
```

  ------------------------------------------------------------------------------------------------
  Component               Owns                                             Must not own
  ----------------------- ------------------------------------------------ -----------------------
  Detection               Raw class, confidence, bounding box              Safety decisions

  Tracking                Track ID, bbox history, lifetime, last-seen      Zone, dwell, severity

  Scene State             Zone membership, zone dwell, movement, crossing  Severity, event
                          state                                            lifecycle

  Severity Evaluator      Stateless                                        Time or history
                          `(state, zone_type, object_class) -> severity`   

  Event Manager           Unsafe-condition timer, persistence, lifecycle,  Geometry
                          escalation, cooldown, alert decision             

  Alert Engine            Alert simulation/delivery and status             Detection or risk logic

  Persistence             Durable events, alerts, zones and system logs    Safety decisions

  API/Dashboard           Read and present system state                    Core business logic
  ------------------------------------------------------------------------------------------------

Keep two timers separate: - **Zone dwell:** continuous time inside a
zone; owned by Scene State. - **Unsafe-condition time:** continuous time
at an alert-relevant severity; owned by Event Manager. It starts when
the condition becomes unsafe, including after a crossing-state
transition.

------------------------------------------------------------------------

# 2. Environment Setup

## Python version

Use **Python 3.12**, not the existing Python 3.9.6 environment. Keep
system Python intact.

Official installer: https://www.python.org/downloads/macos/

With Homebrew:

``` bash
brew install python@3.12
python3.12 --version
uname -m
```

Expected architecture on Apple Silicon: `arm64`.

## Create the virtual environment

``` bash
cd ~/Desktop/level-crossing-safety

# If .venv already exists and was created with Python 3.9, preserve it:
mv .venv .venv-py39-backup

python3.12 -m venv .venv
source .venv/bin/activate

python --version
which python
```

`which python` must point inside this project's `.venv`.

Install initial learning dependencies:

``` bash
python -m pip install --upgrade pip
pip install numpy matplotlib opencv-python pandas jupyter ipykernel
```

Open in VS Code:

``` bash
code .
```

Select interpreter: `.venv/bin/python`.

For every new terminal:

``` bash
cd ~/Desktop/level-crossing-safety
source .venv/bin/activate
```

Do not install every future dependency now. Add and pin compatible
packages as each stage begins.

------------------------------------------------------------------------

# 3. Ten-Week Development Roadmap

Weeks are planning targets, not deadlines. Each week has a completion
gate. Do not advance while a critical gate is failing.

## Week 1 --- CV Fundamentals and Phase 0

**Goal:** Learn image fundamentals, verify dataset feasibility, and
freeze engineering decisions.

### Learning plan

  Day   Topic
  ----- -------------------------------------------------
  1     What Computer Vision is; how images become data
  2     Pixels, dimensions, RGB and BGR
  3     NumPy arrays and image manipulation
  4     OpenCV: read, display, resize, convert and save
  5     Classification vs object detection
  6     Bounding boxes, confidence and IoU
  7     YOLO fundamentals

### Exercises

Create:

``` text
notebooks/
    01_image_fundamentals.ipynb
    02_opencv_basics.ipynb
    03_image_visualization.ipynb
```

Load and display images; inspect width, height, channels, dtype and
pixel values; resize/crop; convert BGR/RGB/grayscale; draw boxes and
polygons; save outputs.

### Dataset acquisition

First candidate: [Railway Level Crossing dataset on
Roboflow](https://universe.roboflow.com/railway-level-crossing/railway_level_crossing).

Verify the exact version, access, license, classes, annotation format
and actual downloadable content. Record image/label counts, class
distribution, missing labels, invalid boxes, corrupt files, duplicates
and potential split leakage.

Other sources such as RailSem19 or railway pedestrian datasets are
**unverified candidates** until their access and licenses are checked.
Do not merge datasets merely to increase volume.

### Event-footage plan

Public images are mainly for detector development. Event-level
validation/test requires timestamped videos and ground-truth event
annotations.

Plan safe controlled footage using a mock crossing on private property
or safe pavement/road. **Never film or stage scenarios on or near live
railway tracks.** Address consent, privacy and retention.

### Phase 0 decisions

Create:

``` text
docs/dataset.md
docs/annotation_protocol.md
docs/architecture.md
DECISIONS.md
```

Freeze: - Problem, scope and limitations - Dataset sources, versions,
access and licenses - Safe video scenarios and recording plan - Zone
taxonomy and crossing-state definitions - Severity matrix and alert
policy - Ground-truth event definition and matching protocol -
Validation/test split strategy - Replay scenario format - Experiment ID
convention - Model/library licensing decisions

**Deliverables:** working Python environment, fundamentals notebooks,
dataset inspection report, footage plan, `DECISIONS.md`, frozen Phase 0
decisions.

**Gate:** A usable detection-data source and feasible safe event-video
strategy must exist. If not, switch to staged/model-railway fallback and
document limitations.

## Week 2 --- YOLO Detection and Video Processing

**Goal:** Build a reliable pretrained detection pipeline.

### Learn

-   Object detection and YOLO
-   CNN concepts at a practical level
-   Backbone/neck/head conceptually
-   Bounding-box prediction
-   Confidence thresholds and NMS
-   IoU, precision, recall and mAP

Do not implement YOLO from scratch.

### Implement

``` text
src/level_crossing/detection/
    detector.py
    detection_result.py
    class_mapping.py
src/level_crossing/video/
    video_reader.py
    frame.py
    video_metadata.py
```

Build model loading, image/video inference, box visualization,
class/confidence filtering, inference timing, output-video writing and
explicit error handling.

Test invalid images, corrupt video, empty detections, unknown classes,
invalid thresholds, missing weights and coordinate validity.

**Deliverable:** pretrained detector running on images and videos with a
documented output interface.

**Gate:** reliable image/video inference and tested output contracts.

## Week 3 --- Dataset Engineering and Detector Evaluation

**Goal:** Validate the data and establish an honest baseline.

### Learn

-   Train/validation/test splits
-   YOLO annotation format
-   Augmentation and class imbalance
-   Overfitting/underfitting
-   Transfer learning and leakage

### Implement

``` text
src/level_crossing/dataset/
    dataset_loader.py
    dataset_validator.py
    annotation_parser.py
    dataset_statistics.py

scripts/
    inspect_dataset.py
    validate_annotations.py
    visualize_annotations.py
    check_duplicates.py
```

Report image/annotation counts, class counts, split counts,
missing/empty labels, invalid boxes, corrupt images, duplicates,
dimensions and imbalance.

### Experiments

A: evaluate pretrained YOLO.\
B: fine-tune on training data only, if justified, then compare on
validation.

Measure precision, recall, mAP50, optionally mAP50-95, per-class
performance, person/vehicle/train recall, inference speed and model
size. Select using validation only; keep final test untouched.

**Deliverable:** validated dataset, statistics, baseline, fine-tuned
candidate if useful, model comparison and selected model rationale.

**Gate:** Select the model based on validation evidence, not
assumptions.

## Week 4 --- Object Tracking and Scene State

**Goal:** Maintain identities across frames and determine zone
relationships.

### Learn

-   Detection vs tracking
-   Multi-object tracking and association
-   Track IDs/history
-   IoU association and Kalman-filter concepts
-   ByteTrack, occlusion, track loss/recovery

### Implement

``` text
src/level_crossing/tracking/
    tracker.py
    track.py
    track_manager.py
src/level_crossing/scene_state/
    zone.py
    zone_manager.py
    zone_membership.py
    dwell_tracker.py
    movement_analyzer.py
```

Implement ByteTrack integration, track IDs/history/lifetime/last-seen,
polygon zones, point-in-polygon membership, documented object reference
point (e.g. bottom-center), zone dwell using the active clock, boundary
hysteresis, track-loss grace and recovery.

Test entering/leaving zones, boundary cases, multiple objects,
occlusion, track loss/recovery, out-of-zone objects and replay timing.

**Deliverable:** video overlay and structured track output,
e.g. `Track 7 | person | DANGER_TRACK | dwell 2.5s | stationary`.

**Gate:** Tracking and Scene State work independently of severity/event
logic. Tracker must not own zones or dwell.

## Week 5 --- Crossing State, Severity Evaluator and Event Manager

**Goal:** Implement the central safety reasoning.

### Learn

-   Finite-state machines
-   Stateless vs stateful components
-   Temporal reasoning and persistence
-   Escalation, cooldown, recovery

Crossing states:

``` text
OPEN
TRAIN_APPROACHING
TRAIN_PASSING
UNKNOWN
```

Initially state is supplied manually or by replay metadata. Do not claim
automatic train-state prediction unless separately implemented and
evaluated. `UNKNOWN` must set health to `DEGRADED`, never NORMAL.

### Severity Evaluator

Implement the complete versioned V3.1 matrix: - Stateless lookup using
state, zone type and rule class - Exactly one applicable rule for every
combination - Mandatory coverage test before any run - Config errors for
missing/ambiguous/tied rules - Runtime missing-rule fallback to `HIGH`
plus system log - `train` rule class maps to `IGNORE`

### Event Manager

Own unsafe-condition timer, persistence, lifecycle, initial alert
decision, severity escalation, cooldown, track-loss grace interaction,
recovery and closure.

### Train misclassification mitigation

In `TRAIN_APPROACHING`/`TRAIN_PASSING`, detect suspected trains
misclassified as truck/bus using train-box overlap and/or configured
box-area criteria. Tune on validation only. Log every suppression and
its reason. Never silently discard detections.

### Essential tests

-   Person in normal crossing with `OPEN`
-   Person in `DANGER_TRACK` with `OPEN`
-   Person in `DANGER_TRACK` with train approaching
-   Person already in zone when state changes
-   Train labelled truck/bus
-   Real vehicle stopped in danger zone with no train present
-   `UNKNOWN` state
-   HIGH-to-CRITICAL escalation
-   Track loss and recovery
-   Matrix coverage, tie and missing-rule cases

**Deliverable:** tested crossing-state component, matrix, stateless
evaluator, stateful event manager and audited train suppression.

**Gate:** Matrix combinations and key event transitions pass automated
tests.

## Week 6 --- Replay, SQLite and Alerts

**Goal:** Integrate a deterministic end-to-end pipeline.

### Replay mode

-   Process every frame; never drop frames.
-   Use video timestamps as the clock.
-   Use video timestamps for dwell and persistence.
-   Support scenario metadata and crossing-state timelines.
-   Produce repeatable results.
-   Never report replay timing as processing latency.

### Real-time mode

-   Bounded queue and documented old-frame drop policy.
-   Wall-clock timestamps.
-   Per-stage processing time and capture-to-alert latency.
-   Keep benchmark results separate from replay.

### Latency definitions

  ------------------------------------------------------------------------------------------
  Metric                  Mode                    Definition
  ----------------------- ----------------------- ------------------------------------------
  Decision latency        Replay                  `alert_video_time - gt_event_start_time`

  Processing latency      Real-time               Per-frame wall-clock processing and
                                                  `alert_wall_time - capture_wall_time`
  ------------------------------------------------------------------------------------------

An estimated combined latency may be decision + processing latency,
explicitly labelled as an estimate.

### SQLite

Implement V3.1 tables: - `events` - `alerts` (multiple alerts per event,
including escalation) - `zones` - `system_logs`

Add initialization, versioned migrations, repositories, transactions,
parameterized queries, error handling and persistence.

### Alert engine

Start with console alert and local sound simulation. Support
initial/escalation alerts, cooldown and statuses. Defer external
SMS/email/webhooks.

**Deliverable:**
`video -> detection -> tracking -> scene state -> severity -> event manager -> alert -> SQLite`.

**Gate:** A replayed scenario reproducibly generates the expected event
and database records.

## Week 7 --- Ground Truth, Evaluation and Ablation

**Goal:** Prove system behavior with measurable evidence.

Ground-truth CSV:

``` csv
video_id,event_id,start_time,end_time,event_type,object_type,crossing_state,zone_entry_time,unsafe_state_start_time
```

Definition:

``` text
GT start_time = max(zone_entry_time, unsafe_state_start_time)
```

For an object already inside when state becomes unsafe, use the
state-change timestamp.

### Event matching

-   One-to-one matching
-   Compatible event type and object class
-   Temporal overlap
-   Frozen start-time tolerance
-   Record fragmentation
-   Define merged-prediction handling

Proposed tolerance is 2.0 seconds, subject to Phase 0 review and freeze.

### Metrics

Detection: precision, recall, mAP50, optionally mAP50-95, per-class
metrics.\
Tracking: ID switches, fragmentation, IDF1 or justified alternative.\
Safety events: event recall, false alerts/hour, missed events, decision
latency, fragmentation/merge counts.

### Footage planning targets

  Split          Intrusion events   Negative footage
  ------------ ------------------ ------------------
  Validation               \>= 15        \>= 2 hours
  Test                     \>= 15        \>= 2 hours

Each split should include person and vehicle events, a state-transition
hazard, multiple-object scenes and train hard-negative. Record actual
counts/hours; if targets cannot be reached, narrow claims accordingly.
Negative footage is necessary for false-alerts/hour.

### Thresholds and ablation

-   Tune only on validation.
-   Keep sweep grid small; consider clip-level cross-validation.
-   Freeze thresholds, then run final test once.
-   Never tune on test.

Ablation: - A: raw detection + zone check - B: detection + tracking - C:
detection + tracking + dwell - D: detection + tracking + dwell + event
manager/cooldown

Compare event recall, false alerts, false alerts/hour and decision
latency.

**Deliverable:** annotations, matcher, evaluation scripts, validation
sweep, frozen test report, ablation and failure analysis.

**Gate:** Explicit denominators, reproducible runs and untouched test
data.

## Week 8 --- Edge-Compatible Inference and Backend

**Goal:** Benchmark deployable inference and expose system data via API.

Benchmark on Mac M2: - CPU inference - Apple MPS where supported - ONNX
Runtime CPU

Call ONNX/CPU results an **edge-proxy benchmark** unless actual target
hardware is used. Validate exported outputs against the original model.

Measure average, P50/P95 latency, FPS, memory, model size, processing
latency and available CPU/GPU utilization.

Build FastAPI:

``` text
src/level_crossing/api/
    main.py
    routes/events.py
    routes/alerts.py
    routes/health.py
    routes/videos.py
    schemas/
    services/
```

Implement health/system status, event list/detail, alert history, replay
control if appropriate, validated configuration, consistent schemas,
errors and API tests. API routes call application services; do not
duplicate business logic.

**Deliverable:** ONNX export/parity validation, edge-proxy report,
minimal FastAPI and API tests/docs.

## Week 9 --- Dashboard, Robustness, Security

**Goal:** Make the system usable and test difficult conditions.

Streamlit dashboard: 1. Video playback 2. Detection overlays 3. Tracking
IDs 4. Zone visualization 5. Crossing state 6. Severity 7. Active events
8. Alert history 9. System health 10. Evidence snapshots

Robustness tests: - Poor/night lighting and headlight glare -
Shadows/reflections - Occlusion and crowds - Person+bicycle and
person+motorcycle - Rider/vehicle merged detections - Train
misclassified as truck/bus - Zone boundary and out-of-zone vehicles -
Track loss/recovery - Camera shift if implemented - Corrupt video -
Missing/invalid crossing state - Invalid config - Database/model
failures

Security/privacy: - Input and configuration validation - Safe file
handling - No hardcoded credentials - Restricted API access where
appropriate - Retention policy and privacy-conscious logs -
Dependency/license review

**Deliverable:** functional dashboard, robustness report, failure tests
and security/privacy review.

## Week 10 --- Hardening and Final Delivery

Review type hints, module boundaries, interfaces, configuration,
structured logs, error handling, migrations, dependency pinning,
documentation and test coverage.

Run unit, integration, regression, end-to-end replay, configuration,
failure and API tests. Add CI for tests and static checks where
feasible.

Record each experiment:

``` text
experiments/EXP-001/
    config.yaml
    model_info.json
    metrics.json
    logs/
```

Record experiment ID, dataset version/split, model/version/weight hash,
config version, Git commit, environment, thresholds, metrics and output
references.

Complete:

``` text
README.md
DECISIONS.md
docs/
    architecture.md
    dataset.md
    annotation_protocol.md
    evaluation.md
    deployment.md
    limitations.md
    failure_analysis.md
```

Prepare a 3--5 minute demo: input video, detection, tracking, zones,
state transition, severity, event confirmation, alert, SQLite records
and dashboard.

**Deliverable:** tested repository, reproducible setup, data/license
docs, model/event evaluation, ablation, edge benchmark, API/dashboard,
technical docs and demo.

------------------------------------------------------------------------

# 4. Target Repository Structure

Build this incrementally; do not create empty modules just to match a
tree.

``` text
level-crossing-safety/
├── configs/
│   ├── zones.yaml
│   ├── severity_matrix.yaml
│   ├── thresholds.yaml
│   └── logging.yaml
├── data/
│   ├── public/
│   ├── controlled/validation/
│   ├── controlled/test/
│   ├── negative/validation/
│   └── negative/test/
├── models/
├── notebooks/
├── src/
│   └── level_crossing/
│       ├── detection/
│       ├── tracking/
│       ├── scene_state/
│       ├── severity/
│       ├── events/
│       ├── alerts/
│       ├── video/
│       ├── database/
│       ├── api/
│       ├── dashboard/
│       ├── evaluation/
│       ├── deployment/
│       └── common/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── end_to_end/
├── experiments/
├── docs/
├── pyproject.toml
├── requirements/
├── .gitignore
├── .env.example
├── DECISIONS.md
└── README.md
```

Data hygiene: - Never commit `.venv/`. - Do not commit large datasets or
weights unless license and repository strategy permit it. - Keep
acquisition instructions and checksums in docs. - Keep raw data
immutable; derived data goes elsewhere. - Record provenance, license,
version and preprocessing. - Keep secrets out of Git.

------------------------------------------------------------------------

# 5. Engineering Standards

  -----------------------------------------------------------------------
  Area                                Standard
  ----------------------------------- -----------------------------------
  Architecture                        Modular components and explicit
                                      interfaces

  Python                              Type hints and documented public
                                      interfaces

  Configuration                       Validated, versioned configuration

  Logging                             Structured logs with
                                      timestamps/component context

  Errors                              Explicit and predictable failure
                                      behavior

  Database                            Transactions, migrations,
                                      repository layer

  Testing                             Unit, integration, regression and
                                      end-to-end

  Reproducibility                     Dataset/model/config/code version
                                      tracking

  Video                               Separate replay and real-time modes

  Evaluation                          Validation-only tuning and frozen
                                      test

  Performance                         Latency, FPS and resource
                                      benchmarks

  Security                            Input validation, safe files,
                                      secret hygiene

  Deployment                          Repeatable setup

  Documentation                       Architecture, data, evaluation,
                                      limitations, failures
  -----------------------------------------------------------------------

Non-negotiable: - No hardcoded zone coordinates or severity
thresholds. - No business logic in the dashboard. - No database queries
scattered through detection code. - No silent suppression of
detections. - No untracked model/config changes. - No fabricated metrics
or test-set tuning. - Never mix replay decision latency and real-time
processing latency. - Do not claim automatic train-state prediction
unless implemented and evaluated. - Never film/stage near live railway
tracks.

Verify the current license terms of any model library (including
Ultralytics) and record implications for intended distribution/use in
`DECISIONS.md`.

------------------------------------------------------------------------

# 6. Git and Project Management

Initialize:

``` bash
cd ~/Desktop/level-crossing-safety
git init
```

Use focused feature branches, for example:

``` text
main
  feature/dataset-inspection
  feature/yolo-detection
  feature/object-tracking
  feature/scene-state
  feature/severity-engine
  feature/event-manager
  feature/alert-engine
```

For each feature: 1. Understand and record the requirement. 2. Create a
focused branch. 3. Implement a small change. 4. Add/update tests. 5. Run
tests and quality checks. 6. Review the diff. 7. Merge only when
working.

Maintain `DECISIONS.md`, issues/task list, experiment IDs and weekly
progress notes.

------------------------------------------------------------------------

# 7. Final Expected Outcomes

  Area                  Result
  --------------------- --------------------------------------------------
  CV                    Working object detector
  Model development     Pretrained/fine-tuned comparison where justified
  Tracking              Persistent object IDs
  Scene understanding   Configurable zones, movement and zone dwell
  Risk reasoning        Context-dependent severity
  Event processing      Stateful lifecycle and unsafe-condition timer
  Alerts                Initial/escalation alerts with audit records
  Database              Persistent events, alerts, zones and logs
  Evaluation            Detection, tracking and event metrics
  Research              Threshold sweep and ablation
  Edge                  ONNX/CPU edge-proxy benchmark
  Backend               FastAPI
  Frontend              Streamlit
  Engineering           Tests, logs, configuration and documentation
  Portfolio             GitHub, report and demo

Only report capabilities and metrics that have actually been
implemented, tested and measured.

------------------------------------------------------------------------

# 8. Working Method

For every component:

1.  **Concept:** What it does and why it is needed.
2.  **Theory:** Learn the necessary CV/engineering concepts.
3.  **Design:** Define inputs, outputs, ownership and failure cases.
4.  **Implementation:** Write small, modular code.
5.  **Execution:** Run on real images/video.
6.  **Debugging:** Find root causes.
7.  **Testing:** Add automated tests.
8.  **Documentation:** Record decisions, commands, results and
    limitations.

Do not copy a complete GitHub project and modify everything at once.
Verify each layer independently before integration.

The 10-week schedule is a planning framework. Dataset acquisition,
annotation, tracking and evaluation may take longer. Do not skip a
completion gate to meet a calendar target.

------------------------------------------------------------------------

# 9. Immediate Next Steps

Run:

``` bash
brew install python@3.12

cd ~/Desktop/level-crossing-safety

# Only if .venv already exists:
mv .venv .venv-py39-backup

python3.12 -m venv .venv
source .venv/bin/activate

python --version
which python
uname -m
```

Expected: - Python `3.12.x` - Python executable inside
`level-crossing-safety/.venv/` - Architecture `arm64`

If Homebrew is unavailable, use the official Python macOS installer.

Then:

``` bash
python -m pip install --upgrade pip
pip install numpy matplotlib opencv-python pandas jupyter ipykernel
```

Create `notebooks/01_image_fundamentals.ipynb`.

**Immediate milestone:** Complete Week 1, Day 1: understand what
Computer Vision is and load an image with OpenCV. Do not begin model
training yet.

------------------------------------------------------------------------

# 10. Definition of Success

The project is complete when the V3.1 Definition of Done is met,
including:

-   Severity matrix coverage test passes.
-   `UNKNOWN` is handled and sets health to `DEGRADED`.
-   Suspected-train suppression is implemented, logged and tested with
    real and synthetic cases.
-   Replay decision latency and real-time processing latency are
    reported separately.
-   Ground truth includes zone-entry and unsafe-state timestamps.
-   Actual event counts and negative-footage hours are recorded for each
    split.
-   Alerts table supports multiple alerts per event, including
    escalation.
-   Dataset availability, access and licenses are verified and
    documented.
-   Replay, event, failure and regression tests pass.
-   Evaluation is reproducible and test data has not been used for
    tuning.
-   Limitations and safety boundaries are explicit.

**Final principle:** Build a system that can explain what it detected,
why it considered a situation unsafe, when the unsafe condition began,
what alert it generated, and how well that behavior was evaluated.
