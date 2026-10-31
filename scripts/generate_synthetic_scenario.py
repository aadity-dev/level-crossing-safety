"""Generates synthetic video scenarios and ground-truth event CSVs for testing and evaluation."""

import cv2
import numpy as np
import csv
from pathlib import Path
from typing import Tuple
from level_crossing.common.types import CrossingState, RuleClass, ZoneType


def generate_scenario_1_person_intrusion(output_dir: Path) -> Tuple[Path, Path]:
    """Generates Scenario 1:
    - 150 frames @ 30fps (5.0 seconds).
    - Resolution: 640x480.
    - A person enters the Danger Track at t=1.0s (frame 30) while crossing state is TRAIN_APPROACHING.
    - Stays in danger track until t=4.0s (frame 120).
    - Generates ground-truth CSV according to V3.1 schema.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "scenario_01_person_danger_track.mp4"
    csv_path = output_dir / "ground_truth.csv"

    width, height, fps = 640, 480, 30.0
    num_frames = 150

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    # Danger track zone is around [0.15, 0.40] to [0.85, 0.65] (y: 192 to 312, x: 96 to 544)
    # Background road and tracks
    for f in range(num_frames):
        img = np.full((height, width, 3), 40, dtype=np.uint8)

        # Draw road
        cv2.rectangle(img, (150, 0), (490, height), (70, 70, 70), -1)
        # Draw rails (parallel horizontal lines)
        cv2.line(img, (0, 220), (width, 220), (160, 160, 160), 4)
        cv2.line(img, (0, 280), (width, 280), (160, 160, 160), 4)
        # Sleepers
        for x in range(0, width, 40):
            cv2.line(img, (x, 210), (x, 290), (100, 70, 40), 6)

        # Person enters from top-left, walks into rails (frame 30 to 120)
        # At frame 0-29: outside danger zone
        # At frame 30-120: inside danger zone (y=250)
        if f >= 15:
            # Animate person walking
            px = int(200 + min(f - 15, 60) * 2.0)
            py = int(120 + min(f - 15, 45) * 3.0)  # reaches py=255 around frame 60

            # Draw person representation
            cv2.circle(img, (px, py - 30), 12, (220, 200, 180), -1)  # head
            cv2.rectangle(img, (px - 14, py - 18), (px + 14, py + 10), (50, 120, 200), -1)  # body
            cv2.line(img, (px - 8, py + 10), (px - 10, py + 35), (30, 30, 30), 4)  # left leg
            cv2.line(img, (px + 8, py + 10), (px + 10, py + 35), (30, 30, 30), 4)  # right leg

        out.write(img)

    out.release()

    # Write ground-truth CSV
    # V3.1 Schema: video_id,event_id,start_time,end_time,event_type,object_type,crossing_state,zone_entry_time,unsafe_state_start_time
    # zone_entry_time = 1.2s (frame 36)
    # unsafe_state_start_time = 0.0s (crossing was already TRAIN_APPROACHING)
    # GT start_time = max(1.2, 0.0) = 1.2s
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
            "4.2",
            "INTRUSION",
            "person",
            "TRAIN_APPROACHING",
            "1.2",
            "0.0",
        ])

    return video_path, csv_path


if __name__ == "__main__":
    vpath, cpath = generate_scenario_1_person_intrusion(Path("data/controlled/validation"))
    print(f"Generated synthetic scenario: {vpath} and ground truth: {cpath}")
