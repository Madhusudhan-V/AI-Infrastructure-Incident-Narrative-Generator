import os, requests

def fallback(incident):
    events=incident.get("events",[])
    evidence="; ".join(f"{e['timestamp']} [{e['level']}] {e['service']}: {e['message']}" for e in events)
    impact="High" if incident.get("severity",0)>=3 else "Moderate"
    return f"""### Incident summary
**{incident['id']}** is a **{incident['type'].replace('_',' ')}** incident with {len(events)} detected events and maximum severity **{incident['severity']}**.

### Observed impact
The evidence indicates a {impact.lower()} operational impact. The log stream shows the affected service events listed below.

### Evidence
{evidence}

### Investigation leads
Validate the affected dependency, connection/resource capacity, recent configuration changes, and downstream service health.

> This is an evidence-based summary. It does not claim a confirmed root cause."""

def generate(incident):
    enabled=os.getenv("OLLAMA_ENABLED","false").lower()=="true"
    if not enabled: return fallback(incident)
    base=os.getenv("OLLAMA_BASE_URL","http://localhost:11434")
    model=os.getenv("OLLAMA_MODEL","llama3.2:3b")
    prompt=("Act as an SRE incident analyst. Use ONLY the supplied evidence. Return sections: "
            "Summary, Observed Impact, Evidence, Investigation Leads. Never invent facts or "
            "state an unverified root cause. Incident evidence:\n"+str(incident))
    try:
        r=requests.post(base+"/api/generate",json={"model":model,"prompt":prompt,"stream":False},timeout=25)
        r.raise_for_status()
        return r.json().get("response") or fallback(incident)
    except Exception:
        return fallback(incident)
