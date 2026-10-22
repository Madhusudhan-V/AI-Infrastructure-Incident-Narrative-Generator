# Architecture

```text
Live Log Generator / Existing Log Stream
                  |
                  v
           Log Watcher / Parser
                  |
                  v
      Rule Engine + Isolation Forest
                  |
                  v
            Detection Fusion
                  |
                  v
       Incident Correlation Engine
                  |
                  v
       Timeline + Evidence Assembly
                  |
                  v
       Cross-Signal Diagnosis Module
                  |
                  v
       AI-Assisted Incident Narrative
                  |
                  v
          Streamlit Dashboard
```

SQLite persists incident records and review state for recovery across dashboard restarts.

The cross-signal diagnosis module consumes the incident events and metrics already present in the log stream. It ranks candidate explanations using transparent rules, timing, service names, and a small configurable dependency map. Its scores are heuristic rankings, not probabilities, and its output is not proof of causation.

The deterministic detection and diagnosis pipeline remains separate from the optional LLM layer so model failures cannot hide evidence or stop incident detection. The LLM may explain structured findings but must not override them or invent evidence.


## Planned research extensions

The current source stream is a local synthetic log generator. Before claiming real host monitoring, add a separately tested host-metrics collector and label live telemetry clearly. Next, validate detection against a suitable public log dataset and expand the experiment harness to compare repeated seeds, hyperparameters, ablations, and held-out results. These are planned extensions until implemented and measured.

Research context:
- Google SRE Workbook, Monitoring: https://sre.google/workbook/monitoring/
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/
- NIST SP 800-94 (IDS/IDPS): https://csrc.nist.gov/pubs/sp/800/94/final
- LogHub public log datasets: https://github.com/logpai/loghub
- Wang and Qi, survey of microservice root-cause analysis: https://arxiv.org/abs/2408.00803
