"""Run a repeatable multi-scenario evaluation experiment.

Usage:
    python -m src.evaluation.run
"""
from src.core.detector import parse_and_detect
from src.core.detection_fusion import fuse
from src.detection.anomaly_detector import InfrastructureAnomalyDetector
from src.evaluation.evaluator import classification_metrics


def evaluate():
    detector = InfrastructureAnomalyDetector(
        min_samples=20,
        contamination=0.05,
        random_state=42,
    )

    truth = []
    predicted = []
    ml_truth = []
    ml_predicted = []
    rows = []

    def process(line, expected_incident, label):
        event = parse_and_detect(line)
        result = detector.update(event)
        event = fuse(event, result)

        truth.append(expected_incident)
        predicted.append(bool(event.detected))

        if result.get("available"):
            ml_truth.append(expected_incident and label.startswith("ml_"))
            ml_predicted.append(bool(result.get("anomaly")))

        rows.append(
            {
                "label": label,
                "expected_incident": expected_incident,
                "detected": bool(event.detected),
                "ml_available": bool(result.get("available")),
                "ml_anomaly": bool(result.get("anomaly")),
                "ml_score": round(float(result.get("score", 0.0)), 4),
            }
        )
        return event, result

    # 40 latency-only and 20 CPU-only healthy observations establish
    # metric-specific baselines. Values mirror the live generator's
    # normal latency range (10-120ms) rather than a narrow fixed cluster.
    for i in range(40):
        latency = 10 + ((i * 17) % 111)
        process(
            f"2026-09-20T00:00:{i:02d}+00:00 INFO metrics "
            f"Request completed latency_ms={latency}",
            False,
            "healthy_latency",
        )

    for i in range(20):
        cpu = 20 + (i % 35)
        process(
            f"2026-09-20T00:00:{40 + i:02d}+00:00 INFO metrics "
            f"CPU usage sampled cpu_pct={cpu}",
            False,
            "healthy_cpu",
        )

    # Known failure vocabulary: four independent rule-based scenarios.
    rule_cases = [
        ("database_failure", "ERROR database Connection pool exhausted active=50 max=50"),
        ("network_failure", "ERROR gateway Connection refused upstream=payments"),
        ("authentication_failure", "ERROR auth Authentication failed user_batch=42"),
        ("resource_pressure", "ERROR worker Out of memory while processing batch"),
    ]
    for label, message in rule_cases:
        process(
            f"2026-09-20T00:01:{len(rows):02d}+00:00 {message}",
            True,
            f"rule_{label}",
        )

    # Statistical anomaly intentionally avoids known rule vocabulary.
    process(
        "2026-09-20T00:02:00+00:00 INFO metrics Request completed latency_ms=900",
        True,
        "ml_latency_anomaly",
    )

    # Benign latency observations after the anomaly exercise the false-positive
    # path without changing the learned baseline with the anomaly itself.
    for i, latency in enumerate([52, 61, 73, 88, 96, 105, 112, 119]):
        process(
            f"2026-09-20T00:03:{i:02d}+00:00 INFO metrics "
            f"Request completed latency_ms={latency}",
            False,
            "healthy_after_anomaly",
        )

    return {
        "classification": classification_metrics(truth, predicted),
        "ml_signal": classification_metrics(ml_truth, ml_predicted)
        if ml_truth
        else {},
        "rows": rows,
    }


def main():
    result = evaluate()
    print("Sentinel multi-scenario synthetic evaluation")
    print()
    print("Overall actionable detection")
    for key, value in result["classification"].items():
        print(f"{key}: {value}")

    print()
    print("ML anomaly signal evaluation")
    if result["ml_signal"]:
        for key, value in result["ml_signal"].items():
            print(f"{key}: {value}")
    else:
        print("No ML predictions were available.")

    print()
    print("Scenario summary")
    for row in result["rows"]:
        if row["label"].startswith(("rule_", "ml_")):
            print(
                f'{row["label"]}: detected={row["detected"]} '
                f'ml_anomaly={row["ml_anomaly"]} ml_score={row["ml_score"]}'
            )


if __name__ == "__main__":
    main()
