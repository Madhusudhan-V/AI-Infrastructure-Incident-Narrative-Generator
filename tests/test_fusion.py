from src.core.detector import parse_and_detect
from src.core.detection_fusion import fuse
from src.core.incident_engine import IncidentEngine


def test_strong_ml_anomaly_is_promoted():
    event = parse_and_detect(
        "2026-09-20T00:00:00+00:00 INFO metrics CPU usage sampled cpu_pct=99"
    )
    result = {"available": True, "anomaly": True, "score": 0.82, "features": [-1, 99]}
    fuse(event, result)

    assert event.detected
    assert event.incident_type == "statistical_anomaly"
    assert event.severity == 2
    assert event.confidence == 0.82


def test_weak_ml_anomaly_is_not_promoted():
    event = parse_and_detect(
        "2026-09-20T00:00:00+00:00 INFO metrics CPU usage sampled cpu_pct=91"
    )
    result = {"available": True, "anomaly": True, "score": 0.40, "features": [-1, 91]}
    fuse(event, result)

    assert not event.detected
    assert event.severity == 0
    assert event.ml_anomaly


def test_restored_incidents_are_chronological():
    engine = IncidentEngine()
    engine.restore([
        {"id": "INC-0002", "created_at": "2026-09-20T00:02:00+00:00"},
        {"id": "INC-0001", "created_at": "2026-09-20T00:01:00+00:00"},
    ])

    assert [item["id"] for item in engine.incidents] == ["INC-0001", "INC-0002"]
