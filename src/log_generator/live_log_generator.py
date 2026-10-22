"""Generate reproducible live-demo logs into the runtime log stream."""
import argparse
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = ROOT / "data" / "runtime" / "application.log"
LOG = Path(os.getenv("SENTINEL_LOG_PATH", str(DEFAULT_LOG)))

SCENARIOS = {
    "database": [
        "WARN api-service Connection latency increased latency_ms=850",
        "ERROR database Connection pool exhausted active=50 max=50",
        "ERROR api-service Database request failed error=timeout",
        "CRITICAL api-service Requests failing error=database_unavailable",
    ],
    "network": [
        "WARN gateway Packet retransmission rate increased",
        "ERROR gateway Connection refused upstream=payments",
        "ERROR api-service Upstream network unreachable",
        "CRITICAL gateway Requests dropped error=network_unavailable",
    ],
    "auth": [
        "WARN auth Invalid token rate increased",
        "ERROR auth Authentication failed user_batch=42",
        "ERROR api-service Unauthorized requests increased",
        "CRITICAL auth Authentication service unavailable",
    ],
    "resource": [
        "WARN metrics CPU usage increased cpu_pct=94",
        "ERROR worker Out of memory while processing batch",
        "CRITICAL worker OOM killer terminated process",
    ],
}
NORMAL = [
    "INFO api-service Request completed latency_ms={lat}",
    "INFO worker Job completed job_id=job-{id}",
    "INFO cache Cache lookup completed key=user-{id}",
    "INFO metrics CPU usage sampled cpu_pct={cpu}",
]


def write(message):
    """Append one event to the runtime stream, never the tracked fixture."""
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f'{datetime.now(timezone.utc).isoformat(timespec="seconds")} {message}\n'
        )


def inject_incident(kind="database"):
    """Append one controlled multi-event incident."""
    for message in SCENARIOS.get(kind, SCENARIOS["database"]):
        write(message)
        time.sleep(0.7)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--incident-every", type=int, default=25)
    parser.add_argument(
        "--scenario", choices=list(SCENARIOS), default="database"
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.incident_every < 0:
        parser.error("--incident-every must be zero (disable) or positive")

    index = 0
    print(f"Live logs: {LOG}")
    print("Stop with Ctrl+C. The tracked sample fixture is not modified.")
    try:
        while True:
            index += 1
            if args.incident_every and index % args.incident_every == 0:
                inject_incident(args.scenario)
            else:
                write(
                    random.choice(NORMAL).format(
                        id=random.randint(1000, 9999),
                        lat=random.randint(10, 120),
                        cpu=random.randint(10, 80),
                    )
                )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nLive log generator stopped.")


if __name__ == "__main__":
    main()
