"""Generate a controllable live application log for the project demo."""
import argparse, random, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data/sample_logs/application.log"
NORMAL = [
    "INFO api-service Request accepted request_id=req-{id} endpoint=/health",
    "INFO api-service Health check completed latency_ms={lat}",
    "INFO worker Job completed job_id=job-{id}",
    "INFO cache Cache lookup completed key=user-{id}",
]
FAILURE = [
    "WARN api-service Connection latency increased latency_ms=850",
    "ERROR database Connection pool exhausted active=50 max=50",
    "ERROR api-service Database request failed error=timeout",
    "CRITICAL api-service Requests failing error=database_unavailable",
]

def write(line):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(datetime.now(timezone.utc).isoformat(timespec="seconds") + " " + line + "\n")
        f.flush()

def inject_incident():
    for template in FAILURE:
        write(template)
        time.sleep(1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=float, default=2)
    p.add_argument("--incident-every", type=int, default=20)
    args = p.parse_args()
    i = 0
    print(f"Writing live logs to {LOG}")
    while True:
        i += 1
        if args.incident_every and i % args.incident_every == 0:
            inject_incident()
        else:
            write(random.choice(NORMAL).format(id=random.randint(1000,9999), lat=random.randint(10,80)))
        time.sleep(args.interval)

if __name__ == "__main__": main()
