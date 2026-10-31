"""CLI runner for Replay Pipeline execution."""

import argparse
from pathlib import Path
from level_crossing.common.config import SystemConfig
from level_crossing.common.types import CrossingState
from level_crossing.pipeline.replay_pipeline import ReplayPipeline


def main():
    parser = argparse.ArgumentParser(description="Level Crossing Replay Pipeline")
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument("--output", default=None, help="Output annotated video path")
    parser.add_argument("--state", default="OPEN", choices=[s.value for s in CrossingState], help="Crossing state")
    parser.add_argument("--config-dir", default="configs", help="Configuration directory")
    parser.add_argument("--db", default="data/level_crossing.sqlite3", help="Database file path")
    args = parser.parse_args()

    config = SystemConfig.load_from_dir(args.config_dir)
    target_state = CrossingState(args.state)

    pipeline = ReplayPipeline(
        config=config,
        db_path=args.db,
    )

    print(f"Running replay on {args.video} with Crossing State: {target_state.value}")
    summary = pipeline.run(
        video_path=args.video,
        crossing_state_timeline=lambda t: target_state,
        output_video_path=args.output,
    )

    print("\n=== Replay Execution Summary ===")
    print(f"Video Source:             {summary.video_source}")
    print(f"Frames Processed:         {summary.total_frames_processed}")
    print(f"Duration:                 {summary.duration_seconds:.2f}s")
    print(f"Events Generated:         {summary.events_generated}")
    print(f"Alerts Dispatched:        {summary.alerts_generated}")
    print(f"Max Severity Observed:    {summary.highest_severity_observed.value}")
    print(f"System Health Status:     {summary.system_health.value}")
    print(f"Processing Wall Time:     {summary.elapsed_wall_time_sec:.2f}s")
    print(f"Throughput:               {summary.average_fps:.1f} FPS")


if __name__ == "__main__":
    main()
