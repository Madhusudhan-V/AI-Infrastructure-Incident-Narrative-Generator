# Sentinel: Final-Year Project Scope and Research Plan

## 1. Project positioning

**Proposed title:** Sentinel: An Adaptive, Multi-Signal Infrastructure Incident Detection, Diagnosis and Learning Platform.

**Problem:** Infrastructure operators receive logs and metrics from multiple services. An alert may reveal that something is wrong without showing which related events matter, what explanation is best supported, what evidence contradicts it, or which investigation step should come next.

**Goal:** Build and evaluate a local-first incident-intelligence prototype that detects operational anomalies, groups related events, ranks evidence-backed explanations, and improves through repeatable experiments.

This is a proposed scope. Features in the roadmap are not considered implemented until their code, tests, and evaluation results exist in the repository.

## 2. How it differs from a conventional IDS

NIST describes an IDS as software that looks for suspicious activity and alerts administrators. Network IDS products analyze network traffic for suspicious activity. Sentinel's primary target is operational reliability: performance degradation, resource pressure, database connection exhaustion, service failures, and related symptoms. Its output is an incident investigation package rather than a security verdict.

Sentinel is **not a replacement for an IDS**. It does not currently capture packets, detect malware, or establish whether activity is malicious. Security systems and Sentinel can complement one another; security-related log events can be operational evidence, but do not by themselves turn Sentinel into a security detector.

## 3. Proposed system layers

1. **Telemetry ingestion:** timestamped logs and metric samples; add a real local-host metrics collector before claiming host-level real-time telemetry.
2. **Signal normalization:** parse timestamps, service identity, severity, CPU/latency/resource fields, and missing-data status into a consistent event model.
3. **Detection:** existing deterministic rules plus Isolation Forest anomaly signals.
4. **Signal fusion:** retain transparent rules and a separately configurable fusion threshold.
5. **Incident correlation:** group related events using time, service identity, incident type, and configured dependencies.
6. **Cross-signal diagnosis:** rank candidate explanations, list direct/supporting/contradictory evidence, and propose operator checks.
7. **Narrative and response guidance:** generate an evidence-grounded report; keep hypotheses distinct from confirmed causes.
8. **Incident workbench:** timeline, signal trends, affected services, ranked hypotheses, evidence, uncertainty, and review/resolution status.
9. **Experiment pipeline:** rerun training/evaluation with different seeds and hyperparameters; store per-run results and aggregate mean/variation.
10. **Reproducible validation:** automated tests, controlled fault scenarios, documented limitations, and a held-out public log evaluation.

The current repository has the core rule/ML detector, incident correlation, dashboard, persistence, synthetic log generator, an initial rule-based diagnosis module, a repeated experiment runner, and a local-host CPU/memory/disk collector. The collector reports the machine running it; remote service telemetry, external dataset evaluation, and stronger learned diagnosis remain future milestones.

## 4. Repeated training, testing, and improvement loop

The existing Isolation Forest detector fits a model on a rolling baseline and scores each new event against the existing baseline. The repeated experiment runner creates a fresh detector for each run, varies the random seed and contamination setting, and reports precision, recall, F1, false-positive rate, mean, and standard deviation.

Run a short experiment first:

```bash
python -m src.evaluation.repeated_experiments --repeats 1 --contamination 0.05
```

Run the default multi-run sensitivity experiment:

```bash
python -m src.evaluation.repeated_experiments
```

Per-run results are written to `experiments/results/repeated_detection_runs.csv`. This output is generated locally and should be reviewed before committing any result file.

**Important methodological limitation:** the current synthetic evaluator warms its baseline on a healthy prefix and then evaluates a generated stream. Repeating this experiment measures stability against seeds and contamination settings; it is not yet a strict independent train/validation/test split and does not demonstrate generalization to unseen production systems. The next research step is a chronological held-out evaluation on a public dataset.

### Experiment matrix

| Experiment | Change | Measurements | Question |
|---|---|---|---|
| E0 — Baseline | Existing rules + Isolation Forest | Precision, recall, F1, FPR | What does the current pipeline achieve? |
| E1 — Repeatability | Several random seeds | Mean and standard deviation | Are results stable across model seeds? |
| E2 — Sensitivity | Contamination 0.03, 0.05, 0.08 | F1, recall, FPR | How does the anomaly threshold setting affect false alarms? |
| E3 — Ablation | Rules only vs ML only vs fused | Same labelled scenarios | Does fusion add measurable value? |
| E4 — Diagnosis | Cross-signal ranking | Top-1/top-3, evidence support, false causal claims | Does diagnosis rank plausible candidates and preserve uncertainty? |
| E5 — Generalization | Held-out public logs | Per-dataset metrics and error analysis | Does performance transfer beyond synthetic patterns? |
| E6 — Regression | Full tests and prior benchmark | Test count, baseline metric drift | Did a change improve one area while breaking another? |

Each experiment should have a hypothesis, configuration, dataset/version, seed, results, error analysis, and decision. Do not claim improvement unless a comparable baseline and measured result support it.

## 5. Real-time demonstration scenario

Use the following as a **controlled demonstration scenario**, not a claim that this exact failure has already been observed in a real deployment.

1. Normal API latency and CPU metrics are recorded as a baseline.
2. A database connection-pool exhaustion event is injected.
3. API latency rises shortly afterward and additional database/API errors appear.
4. Rule detection and/or the anomaly detector flags events.
5. The correlation engine groups related events into one incident.
6. Cross-signal diagnosis ranks database connection exhaustion as a candidate explanation and shows the log evidence, timestamps, service names, uncertainty, and investigation checks.
7. The dashboard suggests checking pool utilization, slow queries, connection leaks, and API dependency timings.
8. An operator reviews the evidence and records the actual resolution.
9. The run is stored with the scenario label and used to compare detection latency, false alarms, diagnosis ranking, and resolution workflow.

A timestamp sequence is evidence of association, not proof of causality. A real deployment would require actual telemetry and a controlled fault-injection environment with ground-truth records.

## 6. Research grounding and external evaluation

Use these public sources as starting points, while keeping claims about Sentinel tied to its own measurements:

- Google SRE Workbook, Monitoring: https://sre.google/workbook/monitoring/
- OpenTelemetry signal concepts: https://opentelemetry.io/docs/concepts/signals/
- NIST SP 800-94, Guide to Intrusion Detection and Prevention Systems: https://csrc.nist.gov/pubs/sp/800/94/final
- LogHub dataset collection and citation guidance: https://github.com/logpai/loghub
- Wang and Qi, *A Comprehensive Survey on Root Cause Analysis in (Micro) Services: Methodologies, Challenges, and Trends*: https://arxiv.org/abs/2408.00803

LogHub provides public system logs for research, including labeled HDFS logs. Select a dataset only after checking its labels, license/usage instructions, data format, and whether it supports the question being evaluated. A log-only dataset can evaluate log anomaly detection but cannot validate CPU-based diagnosis if it has no corresponding metric ground truth.

OpenTelemetry's demo is a possible later integration target for a more realistic multi-service environment, but it adds setup complexity. It should be an optional stretch milestone, not a dependency for the first stable final-year demonstration.

## 7. Milestones and acceptance criteria

### Milestone A — Stable baseline
- Preserve the existing `main` branch.
- Record the baseline test and 400-event evaluation results.
- Keep every enhancement on a feature branch.

### Milestone B — Repeatable experiments
- Parameterize seed and contamination without changing default baseline behavior.
- Save per-run CSV results.
- Test aggregation and invalid configurations.
- Record mean and standard deviation, not just the best run.

### Milestone C — Real signal ingestion
- [x] Add a local-host metrics collector for CPU, memory, and disk using psutil.
- [x] Append real host measurements to the existing log stream in the parser's expected format.
- [x] Add tests for metric formatting, parser integration, and high resource utilization.
- [ ] Keep validating behavior on macOS/Linux and clearly distinguish local-host telemetry from simulated remote-service events.
- [ ] Consider remote/container metrics only after the local collector is stable.

### Milestone D — Diagnosis evaluation
- Expand labelled fault scenarios and include negative/ambiguous cases.
- Report top-1/top-3, evidence support, and unsupported-cause claims.
- Test contradictory evidence and insufficient-evidence behavior.

### Milestone E — External validation and presentation
- Evaluate against one appropriately labelled public log dataset.
- Separate training/baseline windows from held-out evaluation windows.
- Report limitations and errors, not just aggregate scores.
- Prepare a reproducible demo, architecture, ablation results, and live incident walkthrough.

### Definition of done

The project is ready for the final review when a guide can see the system ingesting signals, detecting a controlled incident, correlating it, ranking evidence-backed explanations, viewing the evidence in the dashboard, reproducing evaluation results, and comparing model configurations. Real telemetry and external-data claims must be demonstrated, not merely listed in the README.
