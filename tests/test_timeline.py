from src.incident.timeline import build_timeline
def test_timeline():
    inc={"events":[{"timestamp":"t","level":"ERROR","message":"x"}]}
    assert build_timeline(inc)[0]["message"]=="x"
