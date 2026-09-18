# AI-Powered Infrastructure Incident Narrative Generator

**Author / Project Lead:** Madhusudhan V  
**Project:** Final Year Capstone  
**Team:** 4 members (member details to be added later)

## Overview
A local, explainable incident-analysis platform that consumes a live application log, detects suspicious/error events, correlates them into incidents, reconstructs a timeline, and generates a human-readable incident narrative.

## Demo flow
`Live Log Generator → Log Watcher → Rule/Anomaly Detector → Incident Manager → Timeline → Narrative Generator → Streamlit Dashboard + Notification`

## Design goals
- Works locally without a paid LLM API.
- Rule-based detection is the deterministic baseline.
- Optional anomaly detection can be enabled later.
- Narrative generation has a deterministic fallback and optional Ollama integration.
- Every incident keeps evidence from the original log events.

## Run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m src.log_generator.live_log_generator
# in another terminal
streamlit run src/dashboard/app.py
```

The dashboard tails `data/sample_logs/application.log`. Use **Inject Demo Incident** in the dashboard to append a controlled failure sequence.

## Project owner
**Madhusudhan V**

## Team
See `team/TEAM.md`. Four placeholders are intentionally provided so the remaining members can be added later.
