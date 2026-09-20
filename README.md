# Sentinel — AI-Powered Infrastructure Incident Narrative Generator

> **Real-time incident intelligence for infrastructure operations**

Sentinel is a local-first platform that turns live infrastructure logs into structured, evidence-backed incident intelligence. It combines deterministic rules with an Isolation Forest anomaly detector, correlates related events, reconstructs incident timelines, generates an AI-assisted narrative, persists incident state in SQLite, and presents the result through a live Streamlit operations dashboard.

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
               SQLite
                  │
                  ▼
          AI Incident Narrative
                  │
                  ▼
        Sentinel Operations UI
```

The system is designed around a practical operations workflow:

1. **Ingest** new log events from a live log stream.
2. **Detect** known failure signatures with rules.
3. **Detect** statistical anomalies with Isolation Forest.
4. **Fuse** the signals and promote sufficiently strong anomalies to actionable events.
5. **Correlate** related events into incidents.
6. **Reconstruct** an evidence-backed timeline and severity.
7. **Persist** incidents and review state in SQLite.
8. **Generate** a grounded incident narrative.
9. **Review** and resolve incidents through the operations dashboard.

---

## Key features

### Detection
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

The benchmark is **synthetic and controlled**. These numbers should not be interpreted as production or real-world accuracy. See the evaluation documentation for methodology and limitations.

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
├── evaluation/       # reproducible benchmark
├── incident/         # compatibility incident interfaces
├── ingestion/        # log watching
├── log_generator/    # live infrastructure log simulator
├── narrative/        # narrative generation
└── notification/     # notification interface

tests/                # automated tests
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

### 6. Run the evaluation

```bash
python -m src.evaluation.run
```

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
- [Dataset notes](docs/dataset.md)
- [Roadmap](docs/roadmap.md)
- [Team contributions](team/TEAM.md)

---

## Project status

**Final engineering prototype**

The core detection, incident intelligence, persistence, AI narrative, dashboard, testing, and reproducible synthetic evaluation pipeline are implemented.
