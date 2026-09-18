from datetime import datetime, timezone


class IncidentEngine:
    """Group related detections into incidents within a bounded time window."""

    def __init__(self, window_seconds=45):
        self.window_seconds = window_seconds
        self.incidents = []
        self._counter = 0

    @staticmethod
    def _timestamp(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            return None

    def add(self, event):
        if not event or not event.detected:
            return None

        current = self.incidents[-1] if self.incidents else None
        event_time = self._timestamp(event.timestamp)
        current_time = self._timestamp(current["updated_at"]) if current else None
        within_window = False
        if event_time and current_time:
            within_window = abs((event_time - current_time).total_seconds()) <= self.window_seconds

        same = (
            current
            and current["status"] != "RESOLVED"
            and within_window
            and (event.incident_type == current["type"] or event.severity >= 3)
        )

        if same:
            current["events"].append(event.__dict__)
            current["severity"] = max(current["severity"], event.severity)
            current["confidence"] = max(current["confidence"], event.confidence)
            current["updated_at"] = event.timestamp
            return current, False

        self._counter += 1
        incident = {
            "id": f"INC-{self._counter:04d}",
            "created_at": event.timestamp,
            "updated_at": event.timestamp,
            "type": event.incident_type or "anomaly",
            "severity": event.severity,
            "confidence": event.confidence,
            "status": "DETECTED",
            "owner": "Unassigned",
            "resolution": "",
            "events": [event.__dict__],
        }
        self.incidents.append(incident)
        return incident, True

    def update(self, incident, status, owner=None, resolution=None):
        incident["status"] = status
        if owner is not None:
            incident["owner"] = owner
        if resolution is not None:
            incident["resolution"] = resolution
        incident["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
