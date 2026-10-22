from pathlib import Path

from src.log_generator import live_log_generator
from src.telemetry import host_metrics_collector


def test_live_generator_defaults_to_runtime_log_not_tracked_fixture():
    assert live_log_generator.LOG == (
        Path(__file__).resolve().parents[1] / "data" / "runtime" / "application.log"
    )
    assert live_log_generator.LOG != (
        Path(__file__).resolve().parents[1] / "data" / "sample_logs" / "application.log"
    )


def test_host_collector_defaults_to_runtime_log_not_tracked_fixture():
    root = Path(__file__).resolve().parents[1]
    assert host_metrics_collector.DEFAULT_LOG_PATH == (
        root / "data" / "runtime" / "application.log"
    )
    assert host_metrics_collector.DEFAULT_LOG_PATH != (
        root / "data" / "sample_logs" / "application.log"
    )
