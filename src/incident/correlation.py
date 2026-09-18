def correlate(events):
    """Return events grouped by incident type for offline analysis."""
    groups={}
    for e in events: groups.setdefault(e.get("incident_type") or "unknown", []).append(e)
    return groups
