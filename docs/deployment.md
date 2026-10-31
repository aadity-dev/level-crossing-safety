# Deployment and Edge-Proxy Benchmarking (V3.1)

## 1. Edge-Proxy Benchmark Results

Benchmarked on Apple M2 Silicon (ARM64) with YOLOv8 Nano ($640 \times 640$):

| Target Acceleration | Mean Latency | P50 Latency | P95 Latency | Throughput | Edge Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple Silicon MPS (Metal)** | **16.43 ms** | **14.63 ms** | **23.23 ms** | **60.9 FPS** | Production Edge Metal Accelerator |
| **ONNX Runtime (CPU)** | **36.98 ms** | **36.38 ms** | **38.83 ms** | **27.0 FPS** | **Edge-Proxy Benchmark** |
| **PyTorch (Host CPU)** | 41.98 ms | 41.04 ms | 44.69 ms | 23.8 FPS | Baseline Unaccelerated |

- **Model Parameters:** 3,151,904
- **Model Size:** 6.2 MB (PyTorch `.pt`), 12.3 MB (ONNX `.onnx`)
- **System Memory RSS:** ~704 MB during continuous batch inference

> **Note on Edge-Proxy Methodology:** Per V3.1 specification, results gathered using ONNX Runtime on development host CPU are explicitly classified as an **Edge-Proxy Benchmark**, reflecting expected performance on embedded ARM64 SoCs (e.g. NVIDIA Jetson Orin Nano, Raspberry Pi 5 with NPU).

---

## 2. Service Deployment

### FastAPI Backend Server
To launch the REST API service:
```bash
source .venv/bin/activate
uvicorn level_crossing.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at: `http://localhost:8000/docs`.

### Streamlit Monitoring Dashboard
To launch the interactive monitoring dashboard:
```bash
source .venv/bin/activate
streamlit run src/level_crossing/dashboard/app.py --server.port 8501
```
Web console accessible at: `http://localhost:8501`.

### Background Worker Replay Execution
```bash
python scripts/run_pipeline.py \
  --video data/controlled/validation/scenario_01_person_danger_track.mp4 \
  --state TRAIN_APPROACHING \
  --output data/controlled/validation/annotated_scenario_01.mp4
```
