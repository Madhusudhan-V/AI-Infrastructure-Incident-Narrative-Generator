from src.core.detector import parse_and_detect
from src.telemetry.host_metrics_collector import format_metric_line, write_sample


def test_metric_line_is_parseable_and_contains_all_host_signals():
    line = format_metric_line(
        96.0,
        42.5,
        71.0,
        timestamp="2026-10-22T10:00:00+00:00",
    )

    event = parse_and_detect(line)

    assert event is not None
    assert event.service == "host-metrics"
    assert "cpu_pct=96.0" in event.message
    assert "memory_pct=42.5%" in event.message
    assert "disk_pct=71.0%" in event.message
    assert event.detected is True
    assert event.severity >= 2
    assert event.incident_type == "resource_pressure"


def test_memory_pressure_is_detected_even_when_cpu_is_normal():
    line = format_metric_line(
        30.0,
        94.0,
        40.0,
        timestamp="2026-10-22T10:00:00+00:00",
    )

    event = parse_and_detect(line)

    assert event is not None
    assert event.detected is True
    assert event.incident_type == "resource_pressure"


def test_write_sample_appends_a_parseable_line(tmp_path):
    path = tmp_path / "nested" / "host.log"

    line = write_sample(
        path,
        15.0,
        35.0,
        60.0,
        timestamp="2026-10-22T10:00:00+00:00",
    )

    assert path.read_text(encoding="utf-8").strip() == line
    assert parse_and_detect(line) is not None
