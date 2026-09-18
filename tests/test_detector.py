from src.detection.rule_engine import classify
def test_error_detected():
    e=classify("2026-09-19T00:00:00 ERROR database Connection pool exhausted active=50 max=50")
    assert e["score"]==2 and e["incident_type"]=="database_failure"
