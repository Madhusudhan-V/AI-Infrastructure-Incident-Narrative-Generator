# Sentinel — AI-Powered Infrastructure Incident Narrative Generator

> **Real-time incident intelligence for infrastructure operations**

Sentinel is a local-first infrastructure incident-intelligence platform. It combines deterministic rules, an Isolation Forest anomaly detector, incident correlation, cross-signal diagnosis, AI-assisted narratives, SQLite persistence, and a live Streamlit operations dashboard. It can consume simulated incident logs and a new local-host telemetry collector for CPU, memory, and disk utilization.

**Project Lead:** Madhusudhan V  
**Team:** Madhusudhan V · Lifda Nashan · Nishmitha-Krishna · Kalpithaa

---

## What the system does

```text
Live Infrastructure Logs
          │
          ▼
      Log Parser
          │
          ├───────────────┐
          ▼               ▼
   Rule Detection    Isolation Forest
          │               │
          └───────┬───────┘
                  ▼
          Detection Fusion
           threshold = 0.56
                  │
                  ▼
       Incident Correlation
                  │
                  ▼
       Severity + Timeline
                  │
                  ▼
       Cross-Signal Diagnosis
                  │
                  ▼
          AI Incident Narrative
                  │
                  ▼
        Sentinel Operations UI

SQLite persists incident records and review state.
```

The system is designed around a practical operations workflow:

1. **Ingest** new log events from a live log stream.
2. **Detect** known failure signatures with rules.
3. **Detect** statistical anomalies with Isolation Forest.
4. **Fuse** the signals and promote sufficiently strong anomalies to actionable events.
5. **Correlate** related events into incidents.
6. **Reconstruct** an evidence-backed timeline and severity.
7. **Persist** incidents and review state in SQLite.
8. **Diagnose** cross-signal candidate explanations from related incident evidence.
9. **Generate** a grounded incident narrative that includes the ranked hypotheses.
10. **Review** and resolve incidents through the operations dashboard.

---

## Key features

### Telemetry and detection
- Synthetic scenario log generation for repeatable incident demonstrations.
- Optional local-host CPU, memory, and disk utilization collector using psutil.
- Actual host telemetry is clearly labelled as `host-metrics`; it describes the machine running the collector, not remote services.
- Rule-based detection for database, network, authentication, and resource failures.
- Isolation Forest for statistical latency/CPU anomalies.
- Separate ML anomaly signal and actionable incident decision.
- Current benchmark fusion threshold: **0.56**.

### Incident intelligence
- Event-to-incident correlation.
- Incident severity escalation.
- Evidence stream and affected-service tracking.
- Incident lifecycle: active → reviewed/resolved.
- Timeline reconstruction with detection, escalation, peak, and last-observed phases.

### AI narrative
- Evidence-grounded incident summaries.
- Local Ollama support for optional generative output.
- Deterministic fallback when a local model is unavailable.
- Avoids presenting an unverified root cause as confirmed fact.

### Cross-signal incident diagnosis

- Rule-based ranking of candidate explanations from the incident's existing log evidence.
- Uses event ordering, available CPU/latency values, service names, and an optional configured dependency map.
- Displays supporting evidence, a heuristic ranking score, uncertainty, and investigation checks.
- Ranking scores are not calibrated probabilities and do not prove causation.
- Returns an insufficient-evidence state when no supported pattern matches.
- This first version uses signals already present in the log stream; it does not add live host telemetry, packet capture, or distributed tracing.
- Initial controlled benchmark: 5/5 labelled synthetic scenarios matched the expected top-ranked explanation (100% top-1 and top-3 on this small test set only; not production accuracy).
- GitHub Actions runs the automated test suite and controlled detection/diagnosis benchmarks; use the final validation command below for a fresh local report.

Start real local-host metrics collection in a separate terminal:

```bash
python -m src.telemetry.host_metrics_collector --interval 2
```

Stop it with Ctrl+C. Both the host collector and live log generator write by default to the ignored runtime file `data/runtime/application.log`, not the tracked fixture `data/sample_logs/application.log`. To use another log stream for both, set `SENTINEL_LOG_PATH` before starting the dashboard and producer processes. The host collector measures only the machine running it; it is not remote-service telemetry.

Run the controlled synthetic diagnosis benchmark with:

```bash
python -m src.evaluation.diagnosis_eval
```

The benchmark measures top-1 and top-3 ranking accuracy on five labelled synthetic scenarios. These results are controlled prototype measurements, not production accuracy.
### Repeated training and model evaluation

Sentinel includes a repeatable experiment runner that trains fresh Isolation Forest models using multiple random seeds and compares contamination settings.

Quick run:

```bash
python -m src.evaluation.repeated_experiments --repeats 1 --contamination 0.05
```

Default sensitivity experiment:

```bash
python -m src.evaluation.repeated_experiments
```

Per-run metrics are saved to `experiments/results/repeated_detection_runs.csv`. The runner reports precision, recall, F1, false-positive rate, and mean/standard deviation across runs. These are controlled synthetic experiments; a separate held-out public-data evaluation remains a planned milestone.

### Research plan and real-time use case

See [Final-Year Project Scope and Research Plan](docs/final_year_project_plan.md) for the architecture roadmap, real-time demonstration scenario, IDS distinction, repeated-experiment design, and external validation plan.

### Persistence and operations
- SQLite incident persistence.
- Dashboard recovery after restart.
- Incident Commander review fields for status, owner, and resolution notes.
- Detection-source analytics: rule, ML, or rule+ML.

---

## Evaluation

The final controlled benchmark contains **400 synthetic events**:

| Component | Events |
|---|---:|
| Healthy latency | 100 |
| Healthy CPU | 100 |
| Database failures | 20 |
| Network failures | 20 |
| Authentication failures | 20 |
| Resource-pressure incidents | 20 |
| ML latency anomalies | 20 |
| **Total** | **400** |

### Overall actionable detection

| Metric | Result |
|---|---:|
| Precision | **90.74%** |
| Recall | **98.00%** |
| F1 | **94.23%** |
| False-positive rate | **3.33%** |

Confusion counts: **98 TP, 290 TN, 10 FP, 2 FN**.

### ML anomaly signal

| Metric | Result |
|---|---:|
| Precision | **42.55%** |
| Recall | **100.00%** |
| F1 | **59.70%** |
| False-positive rate | **10.38%** |

The benchmark is **synthetic and controlled**. These recorded baseline numbers should not be interpreted as production or real-world accuracy. Run `python -m src.evaluation.final_validation` to regenerate current results and preserve the report artifacts. See the evaluation documentation for methodology and limitations.

---

## Tech stack

- **Python**
- **Streamlit** — operations dashboard
- **scikit-learn** — Isolation Forest
- **pandas** — data handling
- **SQLite** — incident persistence
- **Plotly** — dashboard analytics
- **pytest** — automated tests
- **Ollama** *(optional)* — local AI narrative generation

No paid API is required for the core system.

---

## Project structure

```text
src/
├── core/             # schemas, fusion, correlation, persistence, AI
├── detection/        # rule engine + anomaly detector
├── dashboard/        # Streamlit operations dashboard
├── evaluation/       # benchmarks and repeated model experiments
├── telemetry/        # local-host metrics collector
├── incident/         # compatibility incident interfaces
├── ingestion/        # log watching
├── log_generator/    # live infrastructure log simulator
├── narrative/        # narrative generation
└── notification/     # notification interface

tests/                # automated tests
experiments/          # selected development experiments
docs/                 # architecture, methodology, evaluation
data/sample_logs/     # sample log data
config/               # project configuration
team/                 # team responsibilities
```

---

## Run the project locally

### 1. Create and activate the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the live log generator

Terminal 1:

```bash
python -m src.log_generator.live_log_generator --interval 2 --incident-every 25 --scenario database
```

Available scenarios:

- `database`
- `network`
- `auth`
- `resource`

### 4. Start the dashboard

Terminal 2:

```bash
PYTHONPATH=. streamlit run src/dashboard/app.py
```

The dashboard refreshes automatically and displays new events, detections, incidents, timelines, evidence, AI narratives, and operations analytics.

### 5. Run tests

```bash
pytest -q
```

### 6. Run final validation (recommended)

Run the complete local validation from the repository root with one command:

```bash
python -m src.evaluation.final_validation
```

This runs the automated test suite, the 400-event synthetic detection benchmark, the five-scenario cross-signal diagnosis benchmark, and repeated Isolation Forest sensitivity experiments (3 runs per contamination setting by default). It writes a Markdown report, JSON metrics, and a per-run CSV under `experiments/results/final_validation/`. Existing experiment CSVs are left untouched.

For a quick smoke run, use `python -m src.evaluation.final_validation --repeats 1 --contamination 0.05`.

---

## Demo flow

For a final project demonstration:

1. Start Sentinel's dashboard.
2. Start the live log generator.
3. Show healthy events entering the system.
4. Inject a database/network/auth/resource incident.
5. Show the detector flagging the event.
6. Show related events being correlated into one incident.
7. Open the incident timeline and evidence.
8. Show the generated AI narrative.
9. Review the incident as an Incident Commander.
10. Resolve it and show the updated operations analytics.
11. Run the evaluation to show the reproducible benchmark.

This demonstrates the complete path from **raw logs → detection → incident → evidence → narrative → human review**.

---

## Engineering notes and limitations

- The Isolation Forest score is a **confidence-like anomaly score, not a calibrated probability**.
- Correlation and severity use heuristic weights and thresholds.
- The live notification module currently provides a console-level notification interface rather than an external paging integration.
- The benchmark is synthetic and controlled.
- The HDFS dataset is not part of the final 400-event benchmark.
- Production deployment would require representative labelled operational data, threshold recalibration, stronger observability, authentication, and external notification integrations.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Methodology](docs/methodology.md)
- [Evaluation](docs/evaluation.md)
- [Experiments](experiments/README.md)
- [Team](team/TEAM.md)

---

## Project status

**Final engineering prototype**

The core detection, incident intelligence, persistence, AI narrative, dashboard, testing, and reproducible synthetic evaluation pipeline are implemented.
