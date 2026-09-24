# Experiments

This directory contains selected development experiments and earlier working versions that were tested before the final implementation.

They are kept separately from `src/` so the production path stays clean while the development process remains visible.

## Anomaly detection iterations

- `anomaly_detector_v1.py` — initial lightweight rate-based anomaly check.
- `anomaly_detector_v2.py` — first Isolation Forest implementation using a shared latency/CPU feature space.
- `anomaly_detector_v3.py` — metric-aware Isolation Forest using separate baselines for latency-only, CPU-only, and combined observations.

The final detector in `src/detection/anomaly_detector.py` builds on these iterations.

## Process experiment

- `fork_log_generator.py` — Unix `fork()` based multi-process log generator tested during development. It was useful for exploring service-level process simulation, but the simpler live generator was retained for the final demo.

These files are experimental snapshots, not part of the runtime pipeline.
