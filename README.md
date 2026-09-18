# AI-Powered Infrastructure Incident Narrative Generator

Project Lead: Madhusudhan V

Team: Madhusudhan V, Lifda Nashan, Nishmitha-Krishna, Kalpithaa

## Overview
A local-first incident intelligence platform that watches infrastructure logs, detects failures and anomaly bursts, correlates related events into incidents, reconstructs evidence-backed timelines, generates an AI-assisted incident narrative, persists incidents, and presents an operations dashboard.

## Architecture
Live Logs -> Parser -> Rule and Statistical Detection -> Incident Correlation -> Timeline -> AI Narrative -> SQLite -> Streamlit Dashboard -> Analyst Review

## Demo
Terminal 1:
python -m src.log_generator.live_log_generator --interval 2 --incident-every 25 --scenario database

Terminal 2:
PYTHONPATH=. streamlit run src/dashboard/app.py

Use the dashboard incident button for a controlled failure. Other simulator scenarios are database, network, auth, and resource.

## AI
The narrative layer supports a local Ollama model. If Ollama is unavailable, the application produces an evidence-based deterministic report.

## Two-month engineering scope
Foundation; detection; correlation and persistence; local AI; HDFS research and evaluation; dashboard productization; testing; final report and demonstration.

See docs/roadmap.md and team/TEAM.md.
