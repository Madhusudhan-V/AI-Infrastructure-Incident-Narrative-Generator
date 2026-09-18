# Architecture

Live Log Generator
       |
application.log
       |
Log Watcher / Parser
       |
Rule Engine + Optional Anomaly Detector
       |
Incident Manager / Correlation
       |
Timeline Reconstruction
       |
Narrative Generator (local-first)
       |
Streamlit Dashboard + Notifications

The deterministic pipeline is intentionally separated from the LLM layer so model failures cannot hide the evidence or stop incident detection.
