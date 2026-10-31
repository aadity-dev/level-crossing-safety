"""Week 1 - Day 1 to 3: Image Fundamentals and NumPy Array Manipulation.

Covers:
- Loading images as NumPy multi-dimensional arrays (H, W, C)
- Pixel coordinates, uint8 dynamic range [0, 255]
- Channels: BGR vs RGB color spaces
- Slicing, cropping, color channel splitting, and statistics
"""

import cv2
import numpy as np

def run_fundamentals():
    print("=== Exercise 1: Image Representation as NumPy Arrays ===")
    # Create synthetic test canvas
    canvas = np.zeros((480, 640, 3), dtype=np.uint8)
    # Paint top half sky blue (BGR: 235, 206, 135)
    canvas[:240, :] = [235, 206, 135]
    # Paint bottom half asphalt road (BGR: 60, 60, 60)
    canvas[240:, :] = [60, 60, 60]

    print(f"Canvas Shape (H, W, C): {canvas.shape}")
    print(f"Data Type: {canvas.dtype}")
    print(f"Min Pixel Value: {canvas.min()}, Max Pixel Value: {canvas.max()}")
    print(f"Memory size in bytes: {canvas.nbytes} bytes (~{canvas.nbytes / 1024:.1f} KB)")

    # Color space conversion: BGR to RGB
    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    print(f"BGR pixel at (100, 100): {canvas[100, 100]} -> RGB pixel: {rgb[100, 100]}")

    # Channel splitting
    b, g, r = cv2.split(canvas)
    print(f"Blue channel mean: {b.mean():.2f}, Green channel mean: {g.mean():.2f}, Red channel mean: {r.mean():.2f}")

    print("Image fundamentals verified successfully.")

if __name__ == "__main__":
    run_fundamentals()
