"""Run a small deterministic evaluation experiment.

Usage:
    python -m src.evaluation.run
"""
from src.core.detector import parse_and_detect
from src.core.detection_fusion import fuse
from src.detection.anomaly_detector import InfrastructureAnomalyDetector
from src.evaluation.evaluator import classification_metrics


def main():
    detector = InfrastructureAnomalyDetector(min_samples=20, contamination=0.05)
    truth = []
    predicted = []

    # Healthy baseline.
    for i in range(30):
        line = (
            f"2026-09-20T00:00:{i:02d}+00:00 INFO metrics "
            f"Request completed latency_ms={40 + (i % 10)}"
        )
        event = parse_and_detect(line)
        result = detector.update(event)
        event = fuse(event, result)
        truth.append(False)
        predicted.append(bool(event.detected))

    # A metric anomaly not covered by the deterministic error vocabulary.
    anomaly = parse_and_detect(
        "2026-09-20T00:01:00+00:00 INFO metrics Request completed latency_ms=900"
    )
    result = detector.update(anomaly)
    anomaly = fuse(anomaly, result)
    truth.append(True)
    predicted.append(bool(anomaly.detected))

    print("Sentinel synthetic evaluation")
    for key, value in classification_metrics(truth, predicted).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
