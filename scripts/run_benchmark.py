"""CLI runner for deployment inference benchmarking across Apple MPS, CPU, and ONNX."""

import argparse
import json
from pathlib import Path

from level_crossing.deployment.benchmark import InferenceBenchmark


def main():
    parser = argparse.ArgumentParser(description="Run Inference Performance Benchmarks")
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--out-json", default="experiments/EXP-001/benchmark.json")
    args = parser.parse_args()

    benchmark = InferenceBenchmark(
        weights_path=args.weights,
        num_warmup=args.warmup,
        num_iterations=args.iterations,
    )

    print(f"Executing multi-target inference benchmark with {args.weights}...")
    results = benchmark.run_benchmark()

    print("\n=== Benchmark Latency & Throughput Results ===")
    for target, stats in results.items():
        if isinstance(stats, dict):
            print(f"\nTarget: {stats.get('target', target)}")
            print(f"  Mean Latency: {stats['mean_ms']} ms")
            print(f"  P50 Latency:  {stats['p50_ms']} ms")
            print(f"  P95 Latency:  {stats['p95_ms']} ms")
            print(f"  Throughput:   {stats['fps']} FPS")
            if "classification" in stats:
                print(f"  Note:         {stats['classification']}")
        else:
            print(f"\n{target}: {stats} MB")

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nBenchmark report written to: {out_path}")


if __name__ == "__main__":
    main()
