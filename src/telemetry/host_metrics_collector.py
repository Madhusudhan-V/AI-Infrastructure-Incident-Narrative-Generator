"""Collect real local-host CPU, memory, and disk metrics into Sentinel's log stream.

This collector reports metrics for the machine on which it runs. It does not
claim to collect metrics from remote hosts or individual application containers.
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = Path(
    os.getenv("SENTINEL_LOG_PATH", str(ROOT / "data" / "runtime" / "application.log"))
)


def format_metric_line(cpu_pct, memory_pct, disk_pct, timestamp=None):
    """Format one parseable Sentinel log line from supplied metric values."""
    timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    level = "WARN" if cpu_pct >= 90 or memory_pct >= 90 or disk_pct >= 95 else "INFO"
    return (
        f"{timestamp} {level} host-metrics "
        f"CPU usage sampled cpu_pct={cpu_pct:.1f} "
        f"memory_pct={memory_pct:.1f}% disk_pct={disk_pct:.1f}%"
    )


def write_sample(log_path, cpu_pct, memory_pct, disk_pct, timestamp=None):
    """Append a single host-metric sample to the configured log file."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = format_metric_line(cpu_pct, memory_pct, disk_pct, timestamp)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return line


def collect_once(log_path=DEFAULT_LOG_PATH, interval=1.0):
    """Collect one sample. The interval lets psutil measure CPU over a period."""
    cpu_pct = psutil.cpu_percent(interval=max(0.1, interval))
    memory_pct = psutil.virtual_memory().percent
    disk_pct = psutil.disk_usage(str(Path.home())).percent
    return write_sample(log_path, cpu_pct, memory_pct, disk_pct)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between host samples")
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH), help="path to append metric samples")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    log_path = Path(args.log_path)
    print(f"Collecting local host metrics to: {log_path}")
    print("Metrics are real measurements from this machine, not remote service telemetry.")
    try:
        while True:
            print(collect_once(log_path=log_path, interval=args.interval))
    except KeyboardInterrupt:
        print("\nHost metrics collector stopped.")


if __name__ == "__main__":
    main()
