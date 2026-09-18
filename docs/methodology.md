# Methodology

1. Generate or ingest timestamped logs.
2. Parse severity and message content.
3. Detect known failure signatures with deterministic rules.
4. Optionally flag bursts with a lightweight anomaly detector.
5. Correlate related events into an incident.
6. Reconstruct an evidence-backed timeline.
7. Generate a narrative from structured incident evidence.
8. Present the result on the dashboard and emit a local notification.

Research/evaluation can later compare this baseline against DeepLog, LogAnomaly, LogBERT, or another selected approach using the prepared HDFS data.
