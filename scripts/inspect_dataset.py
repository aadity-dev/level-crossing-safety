"""Dataset inspection and integrity assessment script."""

import argparse
from pathlib import Path
import cv2
import pandas as pd
from typing import Dict, Any


def inspect_dataset(data_dir: Path) -> Dict[str, Any]:
    print(f"=== Inspecting dataset directory: {data_dir} ===")
    results = {
        "image_count": 0,
        "video_count": 0,
        "csv_count": 0,
        "splits": {},
    }

    if not data_dir.exists():
        print(f"Warning: Directory {data_dir} does not exist.")
        return results

    for split in ["controlled/validation", "controlled/test", "negative/validation", "negative/test", "public"]:
        split_dir = data_dir / split
        if split_dir.exists():
            videos = list(split_dir.glob("*.mp4")) + list(split_dir.glob("*.avi"))
            images = list(split_dir.glob("*.jpg")) + list(split_dir.glob("*.png"))
            csvs = list(split_dir.glob("*.csv"))

            results["splits"][split] = {
                "videos": len(videos),
                "images": len(images),
                "csv_annotations": len(csvs),
            }
            results["video_count"] += len(videos)
            results["image_count"] += len(images)
            results["csv_count"] += len(csvs)

            print(f"Split [{split:22}]: {len(videos)} videos, {len(images)} images, {len(csvs)} CSV files")

    print(f"\nTotal: {results['video_count']} videos, {results['image_count']} images, {results['csv_count']} annotation CSVs.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="data", help="Root data directory")
    args = parser.parse_args()
    inspect_dataset(Path(args.dir))
