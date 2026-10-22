from types import SimpleNamespace

import pytest

from src.detection.anomaly_detector import (
    InfrastructureAnomalyDetector,
    extract_features,
)


def make_event(message, severity=0):
    return SimpleNamespace(message=message, severity=severity)


def test_extract_features_from_object_and_dictionary():
    assert extract_features(make_event("INFO latency_ms=12.5")).tolist() == [
        12.5,
        -1.0,
    ]
    assert extract_features(
        {"message": "INFO cpu_pct=42", "severity": 0}
    ).tolist() == [-1.0, 42.0]


def test_missing_or_non_text_message_returns_no_features():
    assert extract_features(make_event("")) is None
    assert extract_features({"message": None}) is None
    assert extract_features({"other": "latency_ms=20"}) is None


def test_negative_metric_is_not_accepted_as_positive_value():
    assert extract_features(make_event("INFO latency_ms=-12")) is None


def test_missing_metrics_are_unavailable():
    detector = InfrastructureAnomalyDetector(min_samples=2)

    result = detector.update(make_event("INFO service started"))

    assert result["available"] is False
    assert result["anomaly"] is False
    assert result["features"] is None


def test_warmup_uses_healthy_observations():
    detector = InfrastructureAnomalyDetector(min_samples=3)

    detector.update(make_event("INFO metrics latency_ms=20"))
    detector.update(make_event("INFO metrics latency_ms=30"))

    assert len(detector.samples_by_signature[(0,)]) == 2


def test_error_events_do_not_enter_warmup_baseline():
    detector = InfrastructureAnomalyDetector(min_samples=3)

    detector.update(make_event("INFO metrics latency_ms=20"))
    detector.update(make_event("ERROR metrics latency_ms=900", severity=2))

    samples = detector.samples_by_signature[(0,)]
    assert len(samples) == 1
    assert all(float(sample[0]) != 900.0 for sample in samples)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"window": 0}, "window"),
        ({"min_samples": 1}, "min_samples"),
        ({"contamination": 0.0}, "contamination"),
        ({"contamination": 0.6}, "contamination"),
    ],
)
def test_invalid_detector_configuration_is_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        InfrastructureAnomalyDetector(**kwargs)
