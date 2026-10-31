"""Week 1 - Day 4: OpenCV Basics - Reading, Resizing, Drawing, and Saving."""

import cv2
import numpy as np
from pathlib import Path

def run_opencv_basics():
    print("=== Exercise 2: OpenCV Image Transforms & Drawing primitives ===")
    img = np.full((500, 500, 3), 245, dtype=np.uint8)

    # 1. Drawing a railway crossbuck warning symbol
    cv2.line(img, (100, 100), (400, 400), (0, 0, 200), thickness=16, lineType=cv2.LINE_AA)
    cv2.line(img, (100, 400), (400, 100), (0, 0, 200), thickness=16, lineType=cv2.LINE_AA)
    cv2.circle(img, (250, 250), 30, (0, 0, 0), -1)

    # 2. Resizing
    resized = cv2.resize(img, (250, 250), interpolation=cv2.INTER_AREA)
    print(f"Original: {img.shape} -> Resized: {resized.shape}")

    # 3. Gaussian Blur filter
    blurred = cv2.GaussianBlur(img, (15, 15), 0)
    print("Applied 15x15 Gaussian kernel smoothing")

    output_path = Path("notebooks/sample_crossbuck.jpg")
    cv2.imwrite(str(output_path), img)
    print(f"Saved exercise output to {output_path}")

if __name__ == "__main__":
    run_opencv_basics()
