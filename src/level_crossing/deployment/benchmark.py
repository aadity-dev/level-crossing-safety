"""Multi-target inference latency, throughput, and edge-proxy benchmarking."""

import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import psutil

from level_crossing.common.logger import get_logger

logger = get_logger("benchmark")


class InferenceBenchmark:
    """Benchmarks detector across PyTorch CPU, Apple Silicon MPS, and ONNX Runtime CPU (Edge-Proxy)."""

    def __init__(self, weights_path: str = "yolov8n.pt", num_warmup: int = 5, num_iterations: int = 30):
        self.weights_path = weights_path
        self.num_warmup = num_warmup
        self.num_iterations = num_iterations

    def run_benchmark(self, input_shape: tuple = (640, 640, 3)) -> Dict[str, Any]:
        from ultralytics import YOLO
        import torch

        dummy_frame = np.random.randint(0, 255, input_shape, dtype=np.uint8)
        results: Dict[str, Any] = {}

        # 1. PyTorch CPU
        logger.info("Running PyTorch CPU benchmark...")
        pt_cpu_model = YOLO(self.weights_path)
        latencies_cpu = []
        for i in range(self.num_warmup + self.num_iterations):
            t0 = time.perf_counter()
            pt_cpu_model(dummy_frame, device="cpu", verbose=False)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            if i >= self.num_warmup:
                latencies_cpu.append(dt_ms)

        results["pytorch_cpu"] = {
            "target": "PyTorch CPU",
            "mean_ms": round(float(np.mean(latencies_cpu)), 2),
            "p50_ms": round(float(np.percentile(latencies_cpu, 50)), 2),
            "p95_ms": round(float(np.percentile(latencies_cpu, 95)), 2),
            "fps": round(1000.0 / float(np.mean(latencies_cpu)), 1),
        }

        # 2. Apple Silicon MPS (if available)
        if torch.backends.mps.is_available():
            logger.info("Running Apple Silicon MPS benchmark...")
            pt_mps_model = YOLO(self.weights_path)
            latencies_mps = []
            for i in range(self.num_warmup + self.num_iterations):
                t0 = time.perf_counter()
                pt_mps_model(dummy_frame, device="mps", verbose=False)
                dt_ms = (time.perf_counter() - t0) * 1000.0
                if i >= self.num_warmup:
                    latencies_mps.append(dt_ms)

            results["apple_silicon_mps"] = {
                "target": "Apple Silicon MPS (Metal)",
                "mean_ms": round(float(np.mean(latencies_mps)), 2),
                "p50_ms": round(float(np.percentile(latencies_mps, 50)), 2),
                "p95_ms": round(float(np.percentile(latencies_mps, 95)), 2),
                "fps": round(1000.0 / float(np.mean(latencies_mps)), 1),
            }

        # 3. ONNX Runtime CPU (Edge-Proxy)
        try:
            import onnxruntime as ort
            onnx_path = Path("models/yolov8n.onnx")
            if not onnx_path.exists():
                pt_model = YOLO(self.weights_path)
                exported = pt_model.export(format="onnx", imgsz=[640, 640], simplify=True)
                onnx_path = Path(exported)

            session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
            input_name = session.get_inputs()[0].name
            # Prepare CHW float32 input
            chw_input = np.transpose(dummy_frame, (2, 0, 1))[None, ...].astype(np.float32) / 255.0

            latencies_onnx = []
            for i in range(self.num_warmup + self.num_iterations):
                t0 = time.perf_counter()
                session.run(None, {input_name: chw_input})
                dt_ms = (time.perf_counter() - t0) * 1000.0
                if i >= self.num_warmup:
                    latencies_onnx.append(dt_ms)

            results["onnx_runtime_edge_proxy"] = {
                "target": "ONNX Runtime CPU (Edge-Proxy Benchmark)",
                "mean_ms": round(float(np.mean(latencies_onnx)), 2),
                "p50_ms": round(float(np.percentile(latencies_onnx, 50)), 2),
                "p95_ms": round(float(np.percentile(latencies_onnx, 95)), 2),
                "fps": round(1000.0 / float(np.mean(latencies_onnx)), 1),
                "classification": "Edge-Proxy Benchmark (ARM64/x86 host CPU surrogate)",
            }
        except Exception as e:
            logger.warning(f"Could not run ONNX benchmark: {e}")

        # Memory usage
        process = psutil.Process()
        results["memory_footprint_mb"] = round(process.memory_info().rss / (1024 * 1024), 2)

        return results
