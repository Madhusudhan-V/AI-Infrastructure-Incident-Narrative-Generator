"""Generate a grounded narrative; optionally use a local Ollama model."""
import os, requests

def deterministic(incident):
    events=incident.get("events",[])
    typ=incident.get("type","unknown").replace("_"," ")
    return (f"Incident {incident['id']} was detected as a {typ} event. "
            f"The incident contains {len(events)} high-severity log events. "
            f"The observed sequence was: " + " → ".join(e["message"] for e in events) + ". "
            "The immediate evidence indicates a service/database failure; this is an evidence-based summary, not a confirmed root-cause claim.")

def generate(incident, enabled=False, base_url=None, model=None):
    if not enabled: return deterministic(incident)
    base_url=base_url or os.getenv("OLLAMA_BASE_URL","http://localhost:11434")
    model=model or os.getenv("OLLAMA_MODEL","llama3.2:3b")
    prompt="Write a concise incident narrative using only the supplied evidence. Do not invent root cause.\n"+str(incident)
    try:
        r=requests.post(f"{base_url}/api/generate",json={"model":model,"prompt":prompt,"stream":False},timeout=20)
        r.raise_for_status()
        return r.json().get("response", deterministic(incident))
    except Exception:
        return deterministic(incident)
