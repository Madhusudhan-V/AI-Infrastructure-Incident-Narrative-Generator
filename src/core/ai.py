import json
import os

import requests

from src.core.cross_signal_diagnosis import diagnose_incident


def fallback(incident, diagnosis=None):
    events = incident.get("events", [])
    evidence = "; ".join(
        f"{e.get('timestamp', 'unknown')} [{e.get('level', 'UNKNOWN')}] "
        f"{e.get('service', 'unknown')}: {e.get('message', '')}"
        for e in events
    )
    impact = "High" if incident.get("severity", 0) >= 3 else "Moderate"
    diagnosis = diagnosis or diagnose_incident(incident)

    if diagnosis.get("candidates"):
        leading = diagnosis["candidates"][0]
        candidate_text = (
            f"**Leading candidate (not confirmed):** {leading['hypothesis']} "
            f"(evidence ranking score {leading['ranking_score']}/100).\n\n"
            f"**Why it was ranked:** " + "; ".join(
                f"{item['service']} at {item['timestamp']}: {item['message']}"
                for item in leading["supporting_evidence"][:4]
            ) + "\n\n**Uncertainty:** " + leading["uncertainty"] + "\n\n"
            "**Suggested checks:**\n" + "\n".join(
                f"- {check}" for check in leading["next_checks"]
            )
        )
    else:
        candidate_text = (
            "No supported diagnosis pattern matched the current evidence. "
            "Collect more signals rather than inferring a cause."
        )

    return f"""### Incident summary
**{incident.get('id', 'Unknown incident')}** is a **{str(incident.get('type', 'incident')).replace('_', ' ')}** incident with {len(events)} detected events and maximum severity **{incident.get('severity', 0)}**.

### Observed impact
The available evidence indicates a {impact.lower()} operational impact. This is an operational assessment, not a measurement of customer impact.

### Cross-signal diagnosis
{candidate_text}

> The evidence-ranking score is a heuristic, not a probability. Temporal association does not prove causation.

### Evidence
{evidence}

### Investigation leads
Validate the affected dependency, connection/resource capacity, recent configuration changes, and downstream service health.

> This is an evidence-based summary. It does not claim a confirmed root cause."""


def generate(incident, diagnosis=None):
    diagnosis = diagnosis or diagnose_incident(incident)
    enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
    if not enabled:
        return fallback(incident, diagnosis)

    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    prompt = (
        "Act as an SRE incident analyst. Use ONLY the supplied incident evidence and "
        "structured diagnosis. Return sections: Summary, Observed Impact, Cross-Signal "
        "Diagnosis, Evidence, Investigation Leads. Never invent facts, never state an "
        "unverified root cause, and never treat ranking scores as probabilities. Explain "
        "that a candidate is a hypothesis and include uncertainty.\nIncident evidence:\n"
        + json.dumps(incident, ensure_ascii=False, default=str)
        + "\nStructured cross-signal diagnosis:\n"
        + json.dumps(diagnosis, ensure_ascii=False, default=str)
    )
    try:
        response = requests.post(
            base + "/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=25,
        )
        response.raise_for_status()
        return response.json().get("response") or fallback(incident, diagnosis)
    except Exception:
        return fallback(incident, diagnosis)
