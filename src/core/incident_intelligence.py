"""Incident intelligence: correlation, severity, timelines, and analytics."""
from datetime import datetime, timezone


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None


def correlation_score(event, incident, window_seconds=45):
    """Score how strongly an event belongs to an existing incident."""
    if not event or not incident:
        return 0.0
    event_time = parse_time(getattr(event, "timestamp", None))
    incident_time = parse_time(incident.get("updated_at"))
    if not event_time or not incident_time:
        return 0.0

    delta = abs((event_time - incident_time).total_seconds())
    if delta > window_seconds:
        return 0.0

    time_score = max(0.0, 1.0 - delta / window_seconds) * 0.35
    type_score = 0.35 if getattr(event, "incident_type", None) == incident.get("type") else 0.0
    service_score = 0.20 if any(
        getattr(event, "service", None) == item.get("service")
        for item in incident.get("events", [])
    ) else 0.0

    event_rules = set(getattr(event, "rule_matches", []) or [])
    incident_rules = {
        rule
        for item in incident.get("events", [])
        for rule in item.get("rule_matches", [])
    }
    rule_score = 0.10 if event_rules & incident_rules else 0.0

    return round(min(1.0, time_score + type_score + service_score + rule_score), 3)


def calculate_severity(event, event_count=1):
    """Return a bounded 1-3 operational severity."""
    base = int(getattr(event, "severity", 0) or 0)
    score = float(getattr(event, "anomaly_score", 0.0) or 0.0)
    severity = max(1, min(3, base))

    if base >= 3:
        return 3
    if severity >= 2 and (event_count >= 3 or score >= 0.85):
        return 3
    return severity


def build_timeline(incident):
    """Build event-level timeline plus lifecycle phase markers."""
    events = sorted(
        incident.get("events", []),
        key=lambda item: parse_time(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc),
    )
    if not events:
        return {"events": [], "phases": [], "duration_seconds": 0}

    first = parse_time(events[0].get("timestamp"))
    last = parse_time(events[-1].get("timestamp"))
    duration = max(0, int((last - first).total_seconds())) if first and last else 0

    peak_index = max(range(len(events)), key=lambda i: int(events[i].get("severity", 0)))
    phases = [
        {"phase": "FIRST_DETECTED", "timestamp": events[0]["timestamp"], "detail": "First correlated detection"},
    ]
    if len(events) > 1:
        phases.append({
            "phase": "ESCALATION",
            "timestamp": events[min(peak_index, len(events) - 1)]["timestamp"],
            "detail": "Highest observed severity reached",
        })
    phases.append({
        "phase": "PEAK",
        "timestamp": events[peak_index]["timestamp"],
        "detail": f"Severity {events[peak_index].get('severity', 0)}",
    })
    phases.append({
        "phase": "LAST_OBSERVED",
        "timestamp": events[-1]["timestamp"],
        "detail": "Latest correlated evidence",
    })
    if incident.get("status") == "RESOLVED":
        phases.append({
            "phase": "RESOLVED",
            "timestamp": incident.get("updated_at", events[-1]["timestamp"]),
            "detail": incident.get("resolution") or "Analyst marked incident resolved",
        })

    return {
        "events": events,
        "phases": phases,
        "duration_seconds": duration,
    }


def incident_metrics(incidents):
    """Return dashboard-ready operational metrics."""
    incidents = incidents or []
    resolved = [i for i in incidents if i.get("status") == "RESOLVED"]
    durations = []
    for incident in resolved:
        start = parse_time(incident.get("created_at"))
        end = parse_time(incident.get("updated_at"))
        if start and end:
            durations.append(max(0, (end - start).total_seconds()))

    source_counts = {"rule": 0, "ml": 0, "rule+ml": 0}
    services = set()
    for incident in incidents:
        has_ml = any(e.get("ml_anomaly") for e in incident.get("events", []))
        has_rule = any(e.get("rule_matches") for e in incident.get("events", []))
        key = "rule+ml" if has_rule and has_ml else "ml" if has_ml else "rule"
        source_counts[key] += 1
        services.update(e.get("service") for e in incident.get("events", []) if e.get("service"))

    return {
        "total": len(incidents),
        "active": sum(i.get("status") != "RESOLVED" for i in incidents),
        "resolved": len(resolved),
        "avg_resolution_seconds": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "avg_confidence": round(sum(i.get("confidence", 0.0) for i in incidents) / len(incidents), 3) if incidents else 0.0,
        "services_affected": len(services),
        "detection_sources": source_counts,
    }
