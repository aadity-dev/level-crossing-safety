# Ground-Truth Event Annotation Protocol (V3.1)

## CSV Annotation Schema

Ground-truth files (`ground_truth.csv`) in `data/controlled/*/` adhere to the schema:

```csv
video_id,event_id,start_time,end_time,event_type,object_type,crossing_state,zone_entry_time,unsafe_state_start_time
```

### Column Definitions

1. `video_id` (string): Stem identifier of the corresponding video clip (e.g. `scenario_01_person_danger_track`).
2. `event_id` (string): Unique identifier for the ground-truth event (e.g. `GT-EVT-001`).
3. `start_time` (float, seconds): Formula-calculated ground-truth start timestamp:
   $$\text{start\_time} = \max(\text{zone\_entry\_time}, \text{unsafe\_state\_start\_time})$$
4. `end_time` (float, seconds): Video timestamp when entity clears danger zone or situation resolves.
5. `event_type` (string): `INTRUSION`, `TRAPPED_VEHICLE`, `OBSTRUCTION`.
6. `object_type` (string): Normalized rule class (`person`, `vehicle`, `bicycle`).
7. `crossing_state` (string): Active state during hazard (`OPEN`, `TRAIN_APPROACHING`, `TRAIN_PASSING`, `UNKNOWN`).
8. `zone_entry_time` (float, seconds): Timestamp when entity reference point (bottom-center) crosses zone polygon.
9. `unsafe_state_start_time` (float, seconds): Timestamp when crossing state changed to an unsafe mode (e.g. `0.0` if already approaching).

---

## State Transition Edge-Case Handling

### Case 1: Entity Enters Already Unsafe Zone
- $t_{\text{entry}} = 12.4\text{s}$
- Crossing state already `TRAIN_APPROACHING` since $t = 5.0\text{s}$.
- $\text{unsafe\_state\_start\_time} = 5.0\text{s}$.
- $\text{start\_time} = \max(12.4, 5.0) = 12.4\text{s}$.

### Case 2: Entity Inside Zone When State Transitions
- Entity enters pedestrian path at $t = 2.0\text{s}$ during `OPEN` (safe condition).
- Crossing state transitions to `TRAIN_APPROACHING` at $t = 15.0\text{s}$.
- $t_{\text{entry}} = 2.0\text{s}$.
- $\text{unsafe\_state\_start\_time} = 15.0\text{s}$.
- $\text{start\_time} = \max(2.0, 15.0) = 15.0\text{s}$.
- **Principle:** The unsafe event begins when the risk begins ($t = 15.0\text{s}$), not at the benign entry time ($t = 2.0\text{s}$).
