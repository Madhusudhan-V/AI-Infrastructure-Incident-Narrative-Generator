import re
from collections import deque
from .schema import Event

SEVERITY={"INFO":0,"DEBUG":0,"WARN":1,"WARNING":1,"ERROR":2,"CRITICAL":3,"FATAL":3}
RULES={
 "database_failure":[r"connection pool exhausted",r"database.*failed",r"database_unavailable",r"db.*unavailable"],
 "network_failure":[r"connection refused",r"connection reset",r"network unreachable"],
 "latency_degradation":[r"latency increased",r"timeout",r"response time"],
 "authentication_failure":[r"authentication failed",r"invalid token",r"unauthorized"],
 "resource_pressure":[r"out of memory",r"oom",r"cpu usage.*(9[0-9]|100)",r"disk.*(9[0-9]|100)%"],
}

def parse_and_detect(line:str):
    parts=line.split(maxsplit=3)
    if len(parts)<4: return None
    timestamp,level,service,message=parts
    low=message.lower()
    matches=[]
    for kind,patterns in RULES.items():
        if any(re.search(p,low) for p in patterns): matches.append(kind)
    sev=SEVERITY.get(level.upper(),0)
    detected=sev>=2 or bool(matches)
    confidence=min(0.50 + .12*len(matches) + .10*max(sev-1,0),.99) if detected else 0
    return Event(timestamp,level.upper(),service,message,line,detected,matches[0] if matches else None,sev,confidence,matches)

class BurstDetector:
    def __init__(self,window=20,threshold=3):
        self.window=deque(maxlen=window); self.threshold=threshold
    def update(self,event):
        self.window.append(event)
        return sum(e.severity>=2 for e in self.window)>=self.threshold
