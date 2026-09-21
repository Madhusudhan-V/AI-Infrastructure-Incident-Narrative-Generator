import argparse
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data/sample_logs/application.log"

SERVICE_NORMAL = {
    "api-service": [
        "INFO api-service Request completed latency_ms={lat}",
    ],
    "database": [
        "INFO database Query completed duration_ms={lat}",
    ],
    "worker": [
        "INFO worker Job completed job_id=job-{id}",
    ],
    "gateway": [
        "INFO gateway Health check completed status=200",
    ],
    "auth": [
        "INFO auth Token validation completed result=success",
    ],
    "metrics": [
        "INFO metrics CPU usage sampled cpu_pct={cpu}",
    ],
}

SCENARIO_SERVICES = {
    "database": ["api-service", "database", "worker"],
    "network": ["gateway", "api-service", "worker"],
    "auth": ["auth", "api-service", "worker"],
    "resource": ["metrics", "worker", "api-service"],
}

SCENARIO_EVENTS = {
    "database": {
        "api-service": [
            "WARN api-service Connection latency increased latency_ms=850",
            "ERROR api-service Database request failed error=timeout",
            "CRITICAL api-service Requests failing error=database_unavailable",
        ],
        "database": [
            "ERROR database Connection pool exhausted active=50 max=50",
        ],
    },
    "network": {
        "gateway": [
            "WARN gateway Packet retransmission rate increased",
            "ERROR gateway Connection refused upstream=payments",
            "CRITICAL gateway Requests dropped error=network_unavailable",
        ],
        "api-service": [
            "ERROR api-service Upstream network unreachable",
        ],
    },
    "auth": {
        "auth": [
            "WARN auth Invalid token rate increased",
            "ERROR auth Authentication failed user_batch=42",
            "CRITICAL auth Authentication service unavailable",
        ],
        "api-service": [
            "ERROR api-service Unauthorized requests increased",
        ],
    },
    "resource": {
        "metrics": [
            "WARN metrics CPU usage increased cpu_pct=94",
            "ERROR metrics CPU usage critical cpu_pct=99",
        ],
        "worker": [
            "ERROR worker Out of memory while processing batch",
            "CRITICAL worker OOM killer terminated process",
        ],
    },
}


def write_log(message):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}\\n"
    fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def child_loop(service, scenario, interval, incident_every):
    pid = os.getpid()
    print(f"[child] service={service} pid={pid}", flush=True)

    cycle = 0
    event_index = 0
    events = SCENARIO_EVENTS.get(scenario, {}).get(service, [])

    while True:
        cycle += 1

        if incident_every and cycle % incident_every == 0 and events:
            write_log(events[event_index % len(events)])
            event_index += 1
        else:
            template = SERVICE_NORMAL[service][0]
            write_log(
                template.format(
                    id=os.getpid() % 10000,
                    lat=os.getpid() % 100 + 20,
                    cpu=20 + (os.getpid() % 60),
                )
            )

        time.sleep(interval)


def run_forked(scenario, interval, incident_every):
    if os.name != "posix":
        raise SystemExit("Fork mode requires a POSIX/Unix environment.")

    services = SCENARIO_SERVICES[scenario]
    children = []

    print(f"Fork mode: parent pid={os.getpid()}", flush=True)
    print(f"Spawning service processes: {', '.join(services)}", flush=True)

    try:
        for service in services:
            pid = os.fork()

            if pid == 0:
                child_loop(service, scenario, interval, incident_every)
                os._exit(0)

            children.append(pid)

        print(f"Parent process {os.getpid()} supervising {len(children)} children.", flush=True)
        print(f"Live logs: {LOG}", flush=True)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping forked service processes...", flush=True)
    finally:
        for pid in children:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        for pid in children:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass

        print("All child processes stopped.", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Fork-based multi-process live log generator for Sentinel."
    )
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--incident-every", type=int, default=5)
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIO_SERVICES),
        default="database",
    )
    args = parser.parse_args()

    run_forked(args.scenario, args.interval, args.incident_every)


if __name__ == "__main__":
    main()
