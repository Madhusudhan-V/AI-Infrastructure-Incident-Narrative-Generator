"""Run a repeatable large synthetic evaluation experiment.

Usage:
    python -m src.evaluation.run
"""

from datetime import datetime, timedelta, timezone

from src.core.detector import parse_and_detect
from src.core.detection_fusion import fuse
from src.detection.anomaly_detector import InfrastructureAnomalyDetector
from src.evaluation.evaluator import classification_metrics


def evaluate(
    healthy_latency_count=100,
    healthy_cpu_count=100,
    rule_repeats=20,
    ml_anomaly_count=20,
):
    """Evaluate rules, ML anomaly signals, and fused actionable detection."""
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
    base_time = datetime(2026, 9, 20, tzinfo=timezone.utc)
    sequence = 0

    def process(message, expected_incident, label, scenario):
        nonlocal sequence
        timestamp = (base_time + timedelta(seconds=sequence)).isoformat(timespec="seconds")
        sequence += 1

        event = parse_and_detect(f"{timestamp} {message}")
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
                "scenario": scenario,
                "expected_incident": expected_incident,
                "detected": bool(event.detected),
                "ml_available": bool(result.get("available")),
                "ml_anomaly": bool(result.get("anomaly")),
                "ml_score": round(float(result.get("score", 0.0)), 4),
            }
        )
        return event, result

    # Healthy baseline: realistic ranges from the live generator.
    for i in range(healthy_latency_count):
        latency = 10 + ((i * 17) % 111)
        process(
            f"INFO metrics Request completed latency_ms={latency}",
            False,
            "healthy_latency",
            "healthy",
        )

    for i in range(healthy_cpu_count):
        cpu = 10 + ((i * 13) % 71)
        process(
            f"INFO metrics CPU usage sampled cpu_pct={cpu}",
            False,
            "healthy_cpu",
            "healthy",
        )

    # Repeated rule-based incidents across all four supported scenarios.
    rule_cases = [
        ("database_failure", "ERROR database Connection pool exhausted active=50 max=50"),
        ("network_failure", "ERROR gateway Connection refused upstream=payments"),
        ("authentication_failure", "ERROR auth Authentication failed user_batch=42"),
        ("resource_pressure", "ERROR worker Out of memory while processing batch"),
    ]

    for scenario, message in rule_cases:
        for _ in range(rule_repeats):
            process(message, True, f"rule_{scenario}", scenario)

    # Repeated statistical anomalies with benign observations between them.
    # The anomaly vocabulary intentionally avoids deterministic rule matches.
    for i in range(ml_anomaly_count):
        process(
            "INFO metrics Request completed latency_ms=900",
            True,
            "ml_latency_anomaly",
            "ml_latency_anomaly",
        )

        # Healthy post-anomaly observations test recovery and false positives.
        for offset in range(5):
            latency = 20 + ((i * 19 + offset * 11) % 91)
            process(
                f"INFO metrics Request completed latency_ms={latency}",
                False,
                "healthy_after_anomaly",
                "healthy",
            )

    overall = classification_metrics(truth, predicted)
    ml_signal = classification_metrics(ml_truth, ml_predicted) if ml_truth else {}

    scenario_metrics = {}
    for scenario in [
        "database_failure",
        "network_failure",
        "authentication_failure",
        "resource_pressure",
        "ml_latency_anomaly",
    ]:
        scenario_rows = [row for row in rows if row["scenario"] == scenario]
        scenario_metrics[scenario] = classification_metrics(
            [row["expected_incident"] for row in scenario_rows],
            [row["detected"] for row in scenario_rows],
        )

    return {
        "classification": overall,
        "ml_signal": ml_signal,
        "scenario_metrics": scenario_metrics,
        "counts": {
            "healthy_latency": healthy_latency_count,
            "healthy_cpu": healthy_cpu_count,
            "rule_incidents_per_scenario": rule_repeats,
            "ml_anomalies": ml_anomaly_count,
            "total_events": len(rows),
        },
        "rows": rows,
    }


def _print_metrics(metrics):
    for key, value in metrics.items():
        print(f"{key}: {value}")


def main():
    result = evaluate()

    print("Sentinel large-scale synthetic evaluation")
    print("=" * 42)

    print()
    print("Evaluation dataset")
    for key, value in result["counts"].items():
        print(f"{key}: {value}")

    print()
    print("Overall actionable detection")
    _print_metrics(result["classification"])

    print()
    print("ML anomaly signal evaluation")
    if result["ml_signal"]:
        _print_metrics(result["ml_signal"])
    else:
        print("No ML predictions were available.")

    print()
    print("Per-scenario detection")
    for scenario, metrics in result["scenario_metrics"].items():
        print(f"\n{scenario}")
        _print_metrics(metrics)

    print()
    print("ML anomaly examples")
    examples = [
        row for row in result["rows"] if row["label"] == "ml_latency_anomaly"
    ][:5]
    for row in examples:
        print(
            f'detected={row["detected"]} '
            f'ml_anomaly={row["ml_anomaly"]} '
            f'ml_score={row["ml_score"]}'
        )


if __name__ == "__main__":
    main()
