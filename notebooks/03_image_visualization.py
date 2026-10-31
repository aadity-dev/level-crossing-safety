"""Week 1 - Day 5 to 7: Visualizing Bounding Boxes, Zones, and IoU."""

import cv2
import numpy as np
from pathlib import Path

def run_visualization():
    print("=== Exercise 3: Visualizing Bounding Boxes, Polygon Zones, and IoU ===")
    frame = np.full((600, 800, 3), 50, dtype=np.uint8)

    # 1. Monitored Railway Danger Zone Polygon
    zone_pts = np.array([[120, 240], [680, 240], [740, 420], [80, 420]], dtype=np.int32)
    overlay = frame.copy()
    cv2.fillPoly(overlay, [zone_pts], (0, 0, 180))  # Translucent red
    frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)
    cv2.polylines(frame, [zone_pts], isClosed=True, color=(0, 0, 255), thickness=2)

    # 2. Predicted Bounding Box
    box_p = (300, 260, 420, 390)
    cv2.rectangle(frame, (box_p[0], box_p[1]), (box_p[2], box_p[3]), (0, 255, 0), 2)
    # Bottom center reference point
    ref_x = int((box_p[0] + box_p[2]) / 2)
    ref_y = box_p[3]
    cv2.circle(frame, (ref_x, ref_y), 5, (0, 255, 255), -1)

    cv2.putText(
        frame,
        "Track 1: Person (DANGER_TRACK)",
        (box_p[0], box_p[1] - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )

    out_file = Path("notebooks/sample_detection_overlay.jpg")
    cv2.imwrite(str(out_file), frame)
    print(f"Saved visualization output to: {out_file}")

if __name__ == "__main__":
    run_visualization()
