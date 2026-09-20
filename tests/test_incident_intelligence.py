from src.core.detector import parse_and_detect
from src.core.incident_engine import IncidentEngine


def test_related_events_are_correlated():
    engine = IncidentEngine(window_seconds=45)
    first = parse_and_detect(
        "2026-09-20T00:00:00+00:00 ERROR database Connection pool exhausted active=50 max=50"
    )
    second = parse_and_detect(
        "2026-09-20T00:00:10+00:00 ERROR api-service Database request failed error=timeout"
    )

    incident, created = engine.add(first)
    assert created
    updated, created = engine.add(second)

    assert not created
    assert updated["id"] == incident["id"]
    assert len(updated["events"]) == 2


def test_unrelated_events_are_split():
    engine = IncidentEngine(window_seconds=45)
    first = parse_and_detect(
        "2026-09-20T00:00:00+00:00 ERROR database Connection pool exhausted active=50 max=50"
    )
    second = parse_and_detect(
        "2026-09-20T00:00:10+00:00 ERROR auth Authentication failed user_batch=42"
    )

    first_incident, _ = engine.add(first)
    second_incident, created = engine.add(second)

    assert created
    assert second_incident["id"] != first_incident["id"]


def test_incident_severity_does_not_downgrade():
    engine = IncidentEngine(window_seconds=45)
    critical = parse_and_detect(
        "2026-09-20T00:00:00+00:00 CRITICAL api-service Requests failing error=database_unavailable"
    )
    error = parse_and_detect(
        "2026-09-20T00:00:10+00:00 ERROR database Connection pool exhausted active=50 max=50"
    )

    incident, _ = engine.add(critical)
    updated, _ = engine.add(error)

    assert updated["severity"] == 3
