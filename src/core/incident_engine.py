from datetime import datetime, timezone

class IncidentEngine:
    def __init__(self,window_seconds=45):
        self.window_seconds=window_seconds
        self.incidents=[]
        self._counter=0

    def add(self,event):
        if not event or not event.detected: return None
        now=datetime.now(timezone.utc).isoformat(timespec="seconds")
        current=self.incidents[-1] if self.incidents else None
        same=(current and current["status"]!="RESOLVED" and
              (event.incident_type==current["type"] or event.severity>=3))
        if same:
            current["events"].append(event.__dict__)
            current["severity"]=max(current["severity"],event.severity)
            current["confidence"]=max(current["confidence"],event.confidence)
            current["updated_at"]=event.timestamp
            return current,False
        self._counter+=1
        incident={"id":f"INC-{self._counter:04d}","created_at":event.timestamp,
                  "updated_at":event.timestamp,"type":event.incident_type or "anomaly",
                  "severity":event.severity,"confidence":event.confidence,
                  "status":"DETECTED","owner":"Unassigned","resolution":"",
                  "events":[event.__dict__]}
        self.incidents.append(incident)
        return incident,True

    def update(self,incident,status,owner=None,resolution=None):
        incident["status"]=status
        if owner is not None: incident["owner"]=owner
        if resolution is not None: incident["resolution"]=resolution
        incident["updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
