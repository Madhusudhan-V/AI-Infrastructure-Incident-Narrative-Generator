# Methodology

1. Generate or ingest timestamped application logs.
2. Parse severity, service identity, and message content.
3. Detect known failure signatures with deterministic rules.
4. Use Isolation Forest to flag statistical anomalies from available CPU/latency signals.
5. Fuse detection signals and correlate related events into an incident.
6. Reconstruct an evidence-backed timeline and incident context.
7. Run Cross-Signal Incident Diagnosis over the incident's existing events, metrics, and service names.
8. Rank candidate explanations, show supporting and explicit contradictory evidence, describe uncertainty, and suggest investigation checks.
9. Generate an AI-assisted narrative grounded in the incident and structured diagnosis.
10. Present the incident, diagnosis, narrative, and evidence in the Streamlit dashboard.

The diagnosis module is deterministic and independently testable. The ranking score is a heuristic for ordering candidates; it is not a calibrated probability. A diagnosis candidate must be treated as a hypothesis until an operator validates it.

The diagnosis evaluation uses labelled synthetic scenarios and reports top-1 and top-3 ranking accuracy. This controlled benchmark is a prototype check, not a substitute for testing on representative production data.


## Repeated experiments and improvement discipline

For each detector change, preserve a baseline and record the configuration, random seed, contamination setting, dataset/scenario version, precision, recall, F1, false-positive rate, and failure examples. Use multiple runs and report mean plus variation instead of cherry-picking the best result. Compare rules-only, ML-only, and fused configurations as an ablation study. Keep tuning data separate from held-out evaluation data when public or real-world data is added. Every claimed improvement must be tied to a measured comparison.
