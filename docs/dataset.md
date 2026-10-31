# Dataset Strategy, Provenance & Verification

## 1. Candidate Dataset Evaluation

### Roboflow Railway Level Crossing Dataset
- **Candidate:** `railway-level-crossing/railway_level_crossing`
- **Classes:** `person`, `car`, `train`, `barrier`
- **Format:** YOLOv8 format (normalized `class x_center y_center width height`)
- **Inspection Protocol:** Verified for split leakage, image corruption, and missing labels via `scripts/inspect_dataset.py`.
- **License:** Verify non-commercial / research terms prior to external distribution.

### RailSem19 & Railway Pedestrian Datasets
- Secondary research datasets for multi-class rail infrastructure validation.
- Kept in `data/public/` as read-only immutable source data.

---

## 2. Controlled Event-Footage Strategy

Public datasets offer isolated images suitable for detector bounding-box tuning, but cannot evaluate temporal safety events, zone dwell, crossing transitions, or alert latency.

### Controlled Footage Protocol
- **Location:** Private pavement, driveways, or simulated model crossings.
- **Safety Directive:** **Never record on live railway tracks.**
- **Splits:**
  - `data/controlled/validation/`: $\ge 15$ staged hazard events, $\ge 2.0$ hours negative footage.
  - `data/controlled/test/`: $\ge 15$ staged hazard events, $\ge 2.0$ hours negative footage.
- **Scenarios Covered:**
  1. Pedestrian traversing crossing during `OPEN` (safe baseline).
  2. Pedestrian lingering in `DANGER_TRACK` during `OPEN` (medium hazard).
  3. Pedestrian in `DANGER_TRACK` during `TRAIN_APPROACHING` (critical hazard).
  4. Hazard state transition: Entity already inside danger zone when crossing signals active approach.
  5. Vehicle trapped between lowered gates.
  6. Train occlusion hard negatives (train carriages misclassified as trucks/buses).
