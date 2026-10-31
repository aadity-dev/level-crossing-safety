# System Limitations and Operational Boundaries (V3.1)

## 1. Safety and Functional Limitations

1. **Non-Safety-Critical Portfolio System:**
   - This software is not SIL-4 (Safety Integrity Level 4) certified under CENELEC EN 50126, EN 50128, or EN 50129 railway safety standards.
   - It is strictly an advisory video monitoring and notification prototype. It must not control barrier mechanisms, interlocking circuits, or automatic train protection (ATP).

2. **Environmental & Sensor Boundaries:**
   - **Adverse Weather:** Dense fog, severe snow accumulation, torrential rain, or lens water droplets can cause object detector miss rates or false track terminations.
   - **Night Lighting & Glare:** Extreme contrast caused by oncoming locomotive high-intensity headlights or road vehicle high beams can cause sensor saturation and temporary track loss.
   - **Camera Vibration & Wind Induced Motion:** If the camera mounting experiences severe mechanical displacement, configured normalized polygon zones may become misaligned with physical rails.

3. **Detector-Specific Failure Modes:**
   - **Merged Bounding Boxes:** A cyclist riding a bicycle or two people walking close together can be detected as a single composite object. The tracker maintains tracking on the composite box, but rule classification may alternate between `person` and `bicycle`.
   - **Stationary Occlusion:** If an entity enters a zone and is occluded behind a stopped freight train for longer than `max_lost_frames` (30 frames / 1.0s), the track identity is dropped and re-registered upon emergence.

4. **Crossing State Oracle Requirement:**
   - Unless integrated with physical track circuit telemetry or external SCADA feeds, the crossing state (`OPEN`, `TRAIN_APPROACHING`, `TRAIN_PASSING`, `UNKNOWN`) is provided by input metadata or manual selection. Automatic visual train approach estimation is an advisory signal and not an absolute ground-truth guarantee.
