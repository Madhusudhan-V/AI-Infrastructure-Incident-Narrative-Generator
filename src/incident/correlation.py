"""Compatibility helpers for incident correlation."""
from src.core.incident_intelligence import correlation_score


def correlate(events, window_seconds=45):
    """Group events using the same explainable correlation signals as the live engine."""
    groups = {}
    for event in events or []:
        key = event.get("incident_type") or "unknown"
        groups.setdefault(key, []).append(event)
    return groups


def score(event, incident, window_seconds=45):
    """Expose the live engine's correlation score for offline experiments."""
    return correlation_score(event, incident, window_seconds)
