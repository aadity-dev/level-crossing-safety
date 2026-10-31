"""CLI runner for evaluation benchmarks and ablation studies."""

import argparse
import json
from pathlib import Path

from level_crossing.common.config import SystemConfig
from level_crossing.evaluation.ablation import AblationStudyRunner


def main():
    parser = argparse.ArgumentParser(description="Evaluate Safety System & Run Ablations")
    parser.add_argument("--video", default="data/controlled/validation/scenario_01_person_danger_track.mp4")
    parser.add_argument("--gt", default="data/controlled/validation/ground_truth.csv")
    parser.add_argument("--config-dir", default="configs")
    parser.add_argument("--out-json", default="experiments/EXP-001/metrics.json")
    args = parser.parse_args()

    config = SystemConfig.load_from_dir(args.config_dir)
    runner = AblationStudyRunner(base_config=config)

    print(f"Running 4-way ablation evaluation on {args.video} with ground truth {args.gt}...")
    results = runner.run_ablation(video_path=args.video, ground_truth_path=args.gt)

    out_data = {}
    print("\n================== ABLATION STUDY RESULTS ==================")
    for config_key, metrics in results.items():
        m_dict = metrics.to_dict()
        out_data[config_key] = m_dict
        print(f"\nConfiguration: [{config_key}]")
        print(f"  Event Recall:          {m_dict['event_recall'] * 100:.1f}%")
        print(f"  Precision:             {m_dict['event_precision'] * 100:.1f}%")
        print(f"  False Alerts:          {m_dict['false_positives']}")
        print(f"  False Alerts / Hour:   {m_dict['false_alerts_per_hour']:.2f}")
        print(f"  Mean Decision Latency: {m_dict['mean_decision_latency_sec']:.3f}s")
        print(f"  P95 Decision Latency:  {m_dict['p95_decision_latency_sec']:.3f}s")

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nSaved metrics to {out_path}")


if __name__ == "__main__":
    main()
