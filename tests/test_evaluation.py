from src.evaluation.evaluator import (
    classification_metrics,
    detection_latency_seconds,
    grouping_accuracy,
    narrative_grounding_score,
)


def test_classification_metrics():
    result = classification_metrics(
        [True, True, False, False],
        [True, False, True, False],
    )
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["false_positive_rate"] == 0.5


def test_detection_latency():
    assert detection_latency_seconds(
        "2026-09-20T00:00:00+00:00",
        "2026-09-20T00:00:03+00:00",
    ) == 3.0


def test_grouping_and_grounding():
    assert grouping_accuracy(["A", "A", "B"], ["A", "A", "C"]) == 2 / 3
    assert narrative_grounding_score(
        "database connection pool exhausted; requests failed",
        ["database connection pool exhausted", "requests failed"],
    ) == 1.0
