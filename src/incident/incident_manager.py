"""Group related detected events into incidents."""
class IncidentManager:
    def __init__(self, window_seconds=30):
        self.window=window_seconds
        self.incidents=[]
    def add(self,event):
        if not event or event["score"] < 2: return None
        incident=self.incidents[-1] if self.incidents else None
        if incident and (event["incident_type"] == incident["type"] or not incident["type"]):
            incident["events"].append(event)
            incident["severity"] = max(incident["severity"], event["score"])
            return incident
        incident={"id":f"INC-{len(self.incidents)+1:04d}","created_at":event["timestamp"],"type":event["incident_type"] or "unknown","severity":event["score"],"events":[event]}
        self.incidents.append(incident)
        return incident
