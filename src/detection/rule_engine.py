"""Deterministic baseline rules for infrastructure log events."""
import re
SEVERITY = {"INFO":0,"WARN":1,"ERROR":2,"CRITICAL":3}
PATTERNS = {
    "database_failure": [r"connection pool exhausted", r"database request failed", r"database_unavailable"],
    "timeout": [r"timeout", r"latency increased"],
}

def classify(line):
    parts = line.split(maxsplit=2)
    if len(parts) < 3: return None
    timestamp, level, rest = parts
    incident_type = None
    low = rest.lower()
    for name, pats in PATTERNS.items():
        if any(re.search(p, low) for p in pats): incident_type = name; break
    return {"timestamp":timestamp,"level":level,"message":rest,"incident_type":incident_type,"score":SEVERITY.get(level,0)}
