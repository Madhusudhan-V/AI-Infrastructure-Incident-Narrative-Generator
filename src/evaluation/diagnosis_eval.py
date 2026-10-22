"""Small deterministic benchmark for cross-signal diagnosis.

Run with: python -m src.evaluation.diagnosis_eval
This is a controlled synthetic evaluation, not a production benchmark.
"""
from src.core.cross_signal_diagnosis import diagnose_incident


SCENARIOS = [
    {
        "name": "database plus API latency",
        "expected": "database_connection_exhaustion",
        "events": [
            {"timestamp": "2026-09-20T10:02:01+00:00", "service": "database", "message": "Connection pool exhausted active=50 max=50"},
            {"timestamp": "2026-09-20T10:02:04+00:00", "service": "api-service", "message": "Request completed latency_ms=900"},
        ],
    },
    {
        "name": "network connectivity failure",
        "expected": "network_connectivity_failure",
        "events": [
            {"timestamp": "2026-09-20T10:03:01+00:00", "service": "gateway", "message": "Connection refused upstream=payments"},
            {"timestamp": "2026-09-20T10:03:04+00:00", "service": "api-service", "message": "Request timed out latency_ms=800"},
        ],
    },
    {
        "name": "resource pressure",
        "expected": "resource_pressure",
        "events": [
            {"timestamp": "2026-09-20T10:04:01+00:00", "service": "worker", "message": "CPU usage sampled cpu_pct=96"},
            {"timestamp": "2026-09-20T10:04:04+00:00", "service": "worker", "message": "Resource pressure high CPU"},
            {"timestamp": "2026-09-20T10:04:06+00:00", "service": "api-service", "message": "Slow response latency_ms=700"},
        ],
    },
    {
        "name": "authentication failure",
        "expected": "authentication_failure",
        "events": [
            {"timestamp": "2026-09-20T10:05:01+00:00", "service": "auth", "message": "Authentication failed user_batch=42"},
        ],
    },
    {
        "name": "latency degradation",
        "expected": "latency_degradation",
        "events": [
            {"timestamp": "2026-09-20T10:06:01+00:00", "service": "api-service", "message": "Request completed latency_ms=900"},
        ],
    },
]


def evaluate():
    rows = []
    for scenario in SCENARIOS:
        result = diagnose_incident({"id": scenario["name"], "events": scenario["events"]})
        ranked = [item["key"] for item in result["candidates"]]
        rows.append({
            "scenario": scenario["name"],
            "expected": scenario["expected"],
            "top1": ranked[0] if ranked else None,
            "top3": scenario["expected"] in ranked[:3],
            "top1_correct": bool(ranked and ranked[0] == scenario["expected"]),
        })
    count = len(rows)
    return {
        "scenario_count": count,
        "top1_accuracy": sum(row["top1_correct"] for row in rows) / count if count else 0.0,
        "top3_accuracy": sum(row["top3"] for row in rows) / count if count else 0.0,
        "rows": rows,
    }


def main():
    result = evaluate()
    print("Synthetic cross-signal diagnosis evaluation")
    print(f"Scenarios: {result['scenario_count']}")
    print(f"Top-1 accuracy: {result['top1_accuracy']:.1%}")
    print(f"Top-3 accuracy: {result['top3_accuracy']:.1%}")
    for row in result["rows"]:
        print(
            f"- {row['scenario']}: expected={row['expected']}, "
            f"top1={row['top1']}, top3_match={row['top3']}"
        )


if __name__ == "__main__":
    main()
