from src.evaluation.evaluator import (
    classification_metrics,
    detection_latency_seconds,
    grouping_accuracy,
    narrative_grounding_score,
    summarize_runs,
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
    assert grouping_accuracy(["A", "A", "B"], ["A", "A", "C"]) == 0.6667
    assert narrative_grounding_score(
        "database connection pool exhausted; requests failed",
        ["database connection pool exhausted", "requests failed"],
    ) == 1.0


def test_summarize_runs():
    result = summarize_runs(
        [
            {
                "precision": 1.0,
                "recall": 0.5,
                "f1": 0.6667,
                "false_positive_rate": 0.0,
            },
            {
                "precision": 0.5,
                "recall": 1.0,
                "f1": 0.6667,
                "false_positive_rate": 0.1,
            },
        ]
    )
    assert result == {
        "precision": 0.75,
        "recall": 0.75,
        "f1": 0.6667,
        "false_positive_rate": 0.05,
    }
