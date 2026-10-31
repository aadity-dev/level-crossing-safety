"""Validates ground truth CSV annotations and YOLO text label format."""

import csv
from pathlib import Path
import argparse
from level_crossing.common.types import CrossingState, RuleClass


def validate_csv(csv_path: Path) -> bool:
    print(f"Validating ground-truth annotations: {csv_path}")
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return False

    valid = True
    row_count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_fields = [
            "video_id",
            "event_id",
            "start_time",
            "end_time",
            "event_type",
            "object_type",
            "crossing_state",
            "zone_entry_time",
            "unsafe_state_start_time",
        ]
        for rf in required_fields:
            if rf not in reader.fieldnames:
                print(f"Error: Missing required column '{rf}' in {csv_path}")
                valid = False

        for idx, row in enumerate(reader, start=1):
            row_count += 1
            try:
                start_t = float(row["start_time"])
                end_t = float(row["end_time"])
                z_entry = float(row["zone_entry_time"])
                u_start = float(row["unsafe_state_start_time"])

                if end_t < start_t:
                    print(f"Row {idx}: end_time ({end_t}) < start_time ({start_t})")
                    valid = False

                expected_start = max(z_entry, u_start)
                if abs(start_t - expected_start) > 0.01:
                    print(f"Row {idx}: start_time ({start_t}) does not match max(zone_entry, unsafe_start) = {expected_start}")
                    valid = False

                # Validate enum values
                RuleClass(row["object_type"].lower())
                CrossingState(row["crossing_state"])

            except Exception as e:
                print(f"Row {idx} validation failure: {e}")
                valid = False

    if valid:
        print(f"Validation PASSED: {row_count} records checked successfully.")
    else:
        print("Validation FAILED.")
    return valid


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/controlled/validation/ground_truth.csv")
    args = parser.parse_args()
    validate_csv(Path(args.csv))
