"""Duplicate file and annotation check via cryptographic SHA-256 hashing."""

import hashlib
from pathlib import Path
import argparse
from typing import Dict, List


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_duplicates(directory: Path) -> None:
    print(f"Scanning for duplicates in {directory}...")
    hashes: Dict[str, List[Path]] = {}

    for file_path in directory.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            sha = compute_sha256(file_path)
            hashes.setdefault(sha, []).append(file_path)

    duplicates_found = 0
    for sha, paths in hashes.items():
        if len(paths) > 1:
            duplicates_found += 1
            print(f"Duplicate content found ({len(paths)} copies):")
            for p in paths:
                print(f"  - {p}")

    if duplicates_found == 0:
        print("No duplicate files found. Dataset cleanliness verified.")
    else:
        print(f"Total duplicate groups: {duplicates_found}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="data")
    args = parser.parse_args()
    check_duplicates(Path(args.dir))
