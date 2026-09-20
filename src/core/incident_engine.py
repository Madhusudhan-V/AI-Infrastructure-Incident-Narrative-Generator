from datetime import datetime, timezone

from .incident_intelligence import calculate_severity, correlation_score


class IncidentEngine:
    """Correlate actionable detections into bounded, explainable incidents."""

    def __init__(self, window_seconds=45):
        self.window_seconds = window_seconds
        self.incidents = []
        self._counter = 0

    def restore(self, incidents):
        """Restore persisted incidents chronologically."""
        self.incidents = sorted(
            list(incidents or []),
            key=lambda item: self._timestamp(item.get("created_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        numbers = []
        for incident in self.incidents:
            try:
                numbers.append(int(str(incident["id"]).split("-")[-1]))
            except (KeyError, ValueError):
                continue
        self._counter = max(numbers, default=0)

    @staticmethod
    def _timestamp(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError):
            return None

    def add(self, event):
        if not event or not event.detected or event.severity < 2:
            return None

        current = self.incidents[-1] if self.incidents else None
        score = correlation_score(event, current, self.window_seconds) if current else 0.0
        same = bool(
            current
            and current["status"] != "RESOLVED"
            and score >= 0.50
        )

        if same:
            current["events"].append(event.__dict__)
            current["updated_at"] = event.timestamp
            current["severity"] = max(
                current["severity"],
                calculate_severity(event, event_count=len(current["events"])),
            )
            current["confidence"] = max(
                current["confidence"], event.confidence, score
            )
            current["correlation_score"] = score
            current["services"] = sorted({
                item.get("service")
                for item in current["events"]
                if item.get("service")
            })
            return current, False

        self._counter += 1
        incident = {
            "id": f"INC-{self._counter:04d}",
            "created_at": event.timestamp,
            "updated_at": event.timestamp,
            "type": event.incident_type or "anomaly",
            "severity": calculate_severity(event, event_count=1),
            "confidence": event.confidence,
            "status": "DETECTED",
            "owner": "Unassigned",
            "resolution": "",
            "correlation_score": 1.0,
            "services": [event.service],
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
        incident["updated_at"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
