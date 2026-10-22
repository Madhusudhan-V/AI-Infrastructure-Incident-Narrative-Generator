from src.evaluation.repeated_experiments import run_experiments, summarize


def test_summary_reports_mean_and_variation_for_each_setting():
    rows = [
        {"contamination": 0.05, "precision": 0.8, "recall": 0.9, "f1": 0.84, "false_positive_rate": 0.1},
        {"contamination": 0.05, "precision": 0.9, "recall": 0.8, "f1": 0.84, "false_positive_rate": 0.2},
        {"contamination": 0.08, "precision": 0.7, "recall": 0.9, "f1": 0.78, "false_positive_rate": 0.15},
    ]

    result = summarize(rows)

    assert len(result) == 2
    assert result[0]["contamination"] == 0.05
    assert result[0]["runs"] == 2
    assert result[0]["precision_mean"] == 0.85
    assert result[0]["precision_stdev"] == 0.05


def test_repeat_experiment_rejects_invalid_repeat_count():
    try:
        run_experiments(repeats=0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected invalid repeat count to raise ValueError")


def test_repeat_experiment_rejects_invalid_contamination():
    try:
        run_experiments(repeats=1, contamination_values=(0.0,))
    except ValueError as exc:
        assert "contamination values" in str(exc)
    else:
        raise AssertionError("Expected invalid contamination to raise ValueError")
