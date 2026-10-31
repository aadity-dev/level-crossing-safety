"""Generates realistic video scenarios and ground-truth event CSVs using high-fidelity sprites."""

import cv2
import numpy as np
import csv
from pathlib import Path
from typing import Tuple
from level_crossing.common.types import CrossingState, RuleClass, ZoneType


def get_pedestrian_sprite() -> np.ndarray:
    """Extracts a real pedestrian cutout from bundled assets."""
    asset_paths = [
        Path(".venv/lib/python3.12/site-packages/ultralytics/assets/bus.jpg"),
        Path("tests/fixtures/pedestrian.jpg"),
    ]
    for p in asset_paths:
        if p.exists():
            bus = cv2.imread(str(p))
            # Person crop from bus.jpg: x: 50..240, y: 400..900
            crop = bus[400:900, 50:240]
            return cv2.resize(crop, (55, 140))

    # Fallback realistic gradient silhouette
    sprite = np.full((140, 55, 3), 40, dtype=np.uint8)
    cv2.circle(sprite, (27, 20), 14, (180, 150, 130), -1)
    cv2.rectangle(sprite, (12, 34), (43, 85), (30, 80, 160), -1)
    cv2.rectangle(sprite, (15, 85), (25, 138), (30, 30, 30), -1)
    cv2.rectangle(sprite, (30, 85), (40, 138), (30, 30, 30), -1)
    return sprite


def generate_scenario_1_person_intrusion(output_dir: Path) -> Tuple[Path, Path]:
    """Generates Scenario 1:
    - 150 frames @ 30fps (5.0s).
    - Resolution: 640x480.
    - Person walks into Danger Track at t=1.2s (frame 36) during TRAIN_APPROACHING.
    - Stays in danger track until t=4.0s (frame 120).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "scenario_01_person_danger_track.mp4"
    csv_path = output_dir / "ground_truth.csv"

    width, height, fps = 640, 480, 30.0
    num_frames = 150
    sprite = get_pedestrian_sprite()
    sw, sh = sprite.shape[1], sprite.shape[0]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    # Danger track zone polygon in pixel space:
    # y: 192 to 312, x: 96 to 544
    for f in range(num_frames):
        # Background: Railway Crossing Scene
        img = np.full((height, width, 3), 45, dtype=np.uint8)

        # Asphalt Road crossing through rails
        cv2.rectangle(img, (140, 0), (500, height), (60, 60, 60), -1)
        # White road boundary lines
        cv2.line(img, (140, 0), (140, height), (220, 220, 220), 3)
        cv2.line(img, (500, 0), (500, height), (220, 220, 220), 3)
        # Center dashed road line
        for y in range(0, height, 40):
            cv2.line(img, (320, y), (320, y + 20), (240, 240, 240), 2)

        # Parallel Railway Tracks
        # Rail sleepers
        for x in range(0, width, 32):
            cv2.line(img, (x, 195), (x, 310), (85, 60, 35), 5)
        # Steel Rails
        cv2.line(img, (0, 215), (width, 215), (170, 175, 180), 4)
        cv2.line(img, (0, 290), (width, 290), (170, 175, 180), 4)

        # Barrier gates (horizontal red/white stripes)
        cv2.rectangle(img, (100, 170), (130, 185), (0, 0, 200), -1)
        cv2.rectangle(img, (510, 170), (540, 185), (0, 0, 200), -1)

        # Pedestrian Trajectory
        # Frame 0..20: Enters approach road (y=80, x=280)
        # Frame 21..50: Walks into Danger Track (y reaches 210, bottom at 350)
        # Frame 51..115: Lingers inside rails (bottom at 270 inside danger zone)
        # Frame 116..150: Walks out of tracks towards bottom
        if f < 20:
            px = 280
            py = int(50 + f * 4.0)
        elif f < 50:
            px = 280 + int((f - 20) * 1.5)
            py = int(130 + (f - 20) * 2.5)  # reaches py=205 (bottom y=345)
        elif f < 115:
            px = 325
            py = 180  # bottom y = 180 + 140 = 320 -> inside danger track (y=192..312)
        else:
            px = 325
            py = int(180 + (f - 115) * 5.0)

        # Place pedestrian sprite
        if 0 <= py < height - sh and 0 <= px < width - sw:
            # Alpha blend sprite edges for natural realism
            roi = img[py : py + sh, px : px + sw]
            mask = np.ones((sh, sw), dtype=np.float32)
            cv2.rectangle(mask, (0, 0), (sw, sh), 0.95, -1)
            mask = cv2.GaussianBlur(mask, (7, 7), 2)
            mask_3c = np.repeat(mask[:, :, np.newaxis], 3, axis=2)

            img[py : py + sh, px : px + sw] = (
                sprite.astype(np.float32) * mask_3c + roi.astype(np.float32) * (1.0 - mask_3c)
            ).astype(np.uint8)

        out.write(img)

    out.release()

    # Ground-truth CSV
    # Person is in Danger Track from frame 36 (1.2s) to frame 120 (4.0s)
    # State is TRAIN_APPROACHING
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "video_id",
            "event_id",
            "start_time",
            "end_time",
            "event_type",
            "object_type",
            "crossing_state",
            "zone_entry_time",
            "unsafe_state_start_time",
        ])
        writer.writerow([
            "scenario_01_person_danger_track",
            "GT-EVT-001",
            "1.2",
            "4.0",
            "INTRUSION",
            "person",
            "TRAIN_APPROACHING",
            "1.2",
            "0.0",
        ])

    return video_path, csv_path


def generate_scenario_2_multi_person_intrusion(output_dir: Path) -> Path:
    """Generates Scenario 2 (Multi-Person Intrusion):
    - 150 frames @ 30fps (5.0s).
    - Resolution: 640x480.
    - Person 1 (left to right) enters Danger Track at t=1.0s, lingers until t=3.8s.
    - Person 2 (right to left) enters Danger Track at t=1.6s, crosses until t=4.2s.
    - Tests simultaneous multi-target ByteTrack association and multi-event arbitration.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "scenario_02_multi_person_intrusion.mp4"

    width, height, fps = 640, 480, 30.0
    num_frames = 150
    sprite1 = get_pedestrian_sprite()
    # Person 2: slightly scaled and horizontally flipped sprite for visual diversity
    sprite2 = cv2.flip(cv2.resize(sprite1, (48, 128)), 1)
    s1_w, s1_h = sprite1.shape[1], sprite1.shape[0]
    s2_w, s2_h = sprite2.shape[1], sprite2.shape[0]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for f in range(num_frames):
        img = np.full((height, width, 3), 115, dtype=np.uint8)

        # Draw road
        cv2.rectangle(img, (200, 0), (440, height), (75, 75, 75), -1)
        cv2.line(img, (320, 0), (320, height), (220, 220, 220), 2)

        # Draw rails
        cv2.rectangle(img, (0, 210), (width, 226), (45, 45, 45), -1)
        cv2.rectangle(img, (0, 290), (width, 306), (45, 45, 45), -1)

        # Sleepers
        for sx in range(0, width, 25):
            cv2.rectangle(img, (sx, 195), (sx + 10, 320), (90, 60, 40), -1)

        # Boom barrier posts
        cv2.circle(img, (185, 170), 12, (200, 30, 30), -1)
        cv2.circle(img, (455, 340), 12, (200, 30, 30), -1)

        # --- Trajectory for Person 1 (walking from top-left into center track) ---
        if f < 30:
            p1_x = int(220 + f * 1.5)
            p1_y = int(40 + f * 4.6)
        elif f < 110:
            p1_x = int(265 + (f - 30) * 0.4)
            p1_y = 180  # bottom y = 180 + 140 = 320 (in danger track)
        else:
            p1_x = int(297 + (f - 110) * 1.5)
            p1_y = int(180 + (f - 110) * 5.0)

        # --- Trajectory for Person 2 (walking from bottom-right into center track) ---
        if f < 45:
            p2_x = int(410 - f * 1.8)
            p2_y = int(350 - f * 2.8)
        elif f < 125:
            p2_x = int(330 - (f - 45) * 0.5)
            p2_y = int(190 + np.sin(f * 0.1) * 3)  # lingering around track
        else:
            p2_x = int(290 - (f - 125) * 3.0)
            p2_y = int(190 - (f - 125) * 4.0)

        # Composite Person 1
        if 0 <= p1_y < height - s1_h and 0 <= p1_x < width - s1_w:
            roi1 = img[p1_y : p1_y + s1_h, p1_x : p1_x + s1_w]
            m1 = cv2.GaussianBlur(np.full((s1_h, s1_w, 3), 0.95, dtype=np.float32), (7, 7), 2)
            img[p1_y : p1_y + s1_h, p1_x : p1_x + s1_w] = (
                sprite1.astype(np.float32) * m1 + roi1.astype(np.float32) * (1.0 - m1)
            ).astype(np.uint8)

        # Composite Person 2
        if 0 <= p2_y < height - s2_h and 0 <= p2_x < width - s2_w:
            roi2 = img[p2_y : p2_y + s2_h, p2_x : p2_x + s2_w]
            m2 = cv2.GaussianBlur(np.full((s2_h, s2_w, 3), 0.95, dtype=np.float32), (7, 7), 2)
            img[p2_y : p2_y + s2_h, p2_x : p2_x + s2_w] = (
                sprite2.astype(np.float32) * m2 + roi2.astype(np.float32) * (1.0 - m2)
            ).astype(np.uint8)

        out.write(img)

    out.release()
    return video_path


if __name__ == "__main__":
    vpath1, cpath1 = generate_scenario_1_person_intrusion(Path("data/controlled/validation"))
    print(f"Generated single-person scenario video: {vpath1}")
    vpath2 = generate_scenario_2_multi_person_intrusion(Path("data/controlled/validation"))
    print(f"Generated multi-person scenario video: {vpath2}")
