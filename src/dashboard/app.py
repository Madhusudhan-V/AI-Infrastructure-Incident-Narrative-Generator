import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src.core.ai import generate
from src.core.detection_fusion import fuse
from src.detection.anomaly_detector import InfrastructureAnomalyDetector
from src.core.detector import parse_and_detect
from src.core.incident_engine import IncidentEngine
from src.core.incident_intelligence import build_timeline, incident_metrics
from src.core.storage import init, load, save
from src.log_generator.live_log_generator import inject_incident

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data/sample_logs/application.log"
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_PATH", str(ROOT / "data/runtime/incidents.db"))
init(DB)

st.set_page_config(page_title="Sentinel Incident Center", page_icon="◉", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1500px;padding-top:1.5rem}
.hero{padding:1.4rem;border:1px solid #263247;border-radius:20px;
background:linear-gradient(135deg,#0d1420,#182235);margin-bottom:1rem}
.hero h1{margin:0}.hero p{color:#9ba9bb}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>◉ SENTINEL INCIDENT INTELLIGENCE CENTER</h1>
<p>Live infrastructure observability • detection • correlation • AI-assisted incident analysis</p>
</div>
""", unsafe_allow_html=True)

if "engine" not in st.session_state:
    st.session_state.engine = IncidentEngine()
    st.session_state.engine.restore(load(DB))
    st.session_state.events = []
    st.session_state.anomaly_detector = InfrastructureAnomalyDetector()
    st.session_state.anomalies = []

    existing_lines = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    for historical_line in existing_lines:
        historical_event = parse_and_detect(historical_line)
        if historical_event:
            st.session_state.anomaly_detector.update(historical_event)
    st.session_state.seen = len(existing_lines)

with st.sidebar:
    st.header("CONTROL ROOM")
    st.write("Project Lead: Madhusudhan V")
    scenario = st.selectbox("Demo scenario", ["database", "network", "auth", "resource"])
    if st.button("⚡ Inject Incident", type="primary", use_container_width=True):
        inject_incident(scenario)
        st.rerun()
    if st.button("Reset session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

@st.fragment(run_every=2)
def live_control_room():
    """Refresh the observability surface every two seconds."""
    lines = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    if len(lines) < st.session_state.seen:
        st.session_state.seen = 0

    for line in lines[st.session_state.seen:]:
        event = parse_and_detect(line)
        if event:
            ml_result = st.session_state.anomaly_detector.update(event)
            event = fuse(event, ml_result)
            st.session_state.events.append(event)

            if ml_result["available"] and ml_result["anomaly"]:
                st.session_state.anomalies.append({
                    "timestamp": event.timestamp,
                    "service": event.service,
                    "score": round(ml_result["score"], 3),
                    "promoted": bool(event.ml_anomaly and event.severity >= 2),
                    "features": ml_result["features"],
                })

            result = st.session_state.engine.add(event)
            if result:
                save(DB, result[0])

    st.session_state.seen = len(lines)
    events = st.session_state.events
    incidents = st.session_state.engine.incidents
    active = [i for i in incidents if i["status"] != "RESOLVED"]
    stats = incident_metrics(incidents)

    cols = st.columns(6)
    values = [
        len(events),
        sum(e.severity >= 2 for e in events),
        len(incidents),
        len(st.session_state.anomalies),
        stats["services_affected"],
        "INCIDENT" if active else "HEALTHY",
    ]
    labels = ["LOG EVENTS", "ERRORS", "INCIDENTS", "ML ANOMALIES", "SERVICES", "SYSTEM"]
    for col, label, value in zip(cols, labels, values):
        col.metric(label, value)

    st.divider()
    left, right = st.columns([1.35, 0.65])

    with left:
        st.subheader("LIVE EVENT STREAM")
        st.code("\n".join(lines[-28:]) or "Waiting for logs...", language="text")

    with right:
        st.subheader("DETECTION ANALYTICS")
        if events:
            df = pd.DataFrame([
                {"type": e.incident_type or "normal", "severity": e.severity}
                for e in events
            ])
            counts = df["type"].value_counts().reset_index()
            counts.columns = ["type", "count"]
            st.plotly_chart(
                px.bar(counts, x="type", y="count", title="Detection categories"),
                use_container_width=True,
            )
        else:
            st.info("No detected events yet.")

    if st.session_state.anomalies:
        st.divider()
        st.subheader("🧠 ML ANOMALY SIGNALS")
        st.dataframe(
            pd.DataFrame(st.session_state.anomalies[-10:]),
            hide_index=True,
            use_container_width=True,
        )

    if incidents:
        incident = incidents[-1]
        timeline = build_timeline(incident)

        st.divider()
        st.subheader("🔴 INCIDENT " + incident["id"])

        a, b, c, d = st.columns(4)
        a.metric("TYPE", incident["type"].replace("_", " ").upper())
        b.metric("SEVERITY", incident["severity"])
        c.metric("CONFIDENCE", f'{incident["confidence"]:.0%}')
        d.metric("STATUS", incident["status"])

        st.caption(
            f'Correlation: {incident.get("correlation_score", 1.0):.0%} • '
            f'Services: {", ".join(incident.get("services", [])) or "Unknown"} • '
            f'Duration: {timeline["duration_seconds"]}s'
        )

        t1, t2, t3, t4 = st.tabs([
            "TIMELINE", "AI NARRATIVE", "ANALYTICS", "RAW EVIDENCE"
        ])

        with t1:
            st.markdown("**INCIDENT LIFECYCLE**")
            for phase in timeline["phases"]:
                st.markdown(
                    f'**{phase["phase"]}** — {phase["timestamp"]} — {phase["detail"]}'
                )

            st.markdown("**EVIDENCE STREAM**")
            for event in timeline["events"]:
                st.markdown(
                    f'**{event["timestamp"]}**  '
                    f'<code>{event["level"]}</code>  '
                    f'<code>{event["service"]}</code> — {event["message"]}',
                    unsafe_allow_html=True,
                )

        with t2:
            st.markdown(generate(incident))
            st.caption(
                "AI output is grounded in observed evidence; verify operational conclusions."
            )

        with t3:
            x, y, z = st.columns(3)
            x.metric("EVENTS", len(incident["events"]))
            y.metric(
                "AFFECTED SERVICES",
                len(incident.get("services", [])) or len({
                    e.get("service") for e in incident["events"]
                }),
            )
            z.metric("DURATION", f'{timeline["duration_seconds"]}s')

            source_rows = []
            for event in incident["events"]:
                source_rows.append({
                    "timestamp": event["timestamp"],
                    "service": event["service"],
                    "rule": ", ".join(event.get("rule_matches", [])) or "—",
                    "ML anomaly": "Yes" if event.get("ml_anomaly") else "No",
                    "ML score": round(event.get("anomaly_score", 0.0), 3),
                })
            st.dataframe(
                pd.DataFrame(source_rows),
                hide_index=True,
                use_container_width=True,
            )

        with t4:
            st.json(incident)

        st.subheader("INCIDENT COMMANDER REVIEW")
        status_options = ["DETECTED", "INVESTIGATING", "RESOLVED"]
        status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(incident["status"]),
            key=f'status_{incident["id"]}',
        )
        owner = st.text_input(
            "Owner", incident["owner"], key=f'owner_{incident["id"]}'
        )
        resolution = st.text_area(
            "Resolution / analyst notes",
            incident["resolution"],
            key=f'resolution_{incident["id"]}',
        )

        if st.button("Save Review", key=f'review_{incident["id"]}'):
            st.session_state.engine.update(incident, status, owner, resolution)
            save(DB, incident)
            st.rerun()

        st.divider()
        st.subheader("INCIDENT HISTORY")
        history_rows = [{
            "ID": item["id"],
            "TYPE": item["type"],
            "SEVERITY": item["severity"],
            "CONFIDENCE": f'{item.get("confidence", 0):.0%}',
            "EVENTS": len(item["events"]),
            "SERVICES": len(item.get("services", [])) or len({
                e.get("service") for e in item["events"]
            }),
            "STATUS": item["status"],
        } for item in incidents]
        st.dataframe(
            pd.DataFrame(history_rows),
            hide_index=True,
            use_container_width=True,
        )

        st.divider()
        st.subheader("📊 OPERATIONS ANALYTICS")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ACTIVE", stats["active"])
        m2.metric("RESOLVED", stats["resolved"])
        m3.metric("AVG CONFIDENCE", f'{stats["avg_confidence"]:.0%}')
        avg_minutes = (
            stats["avg_resolution_seconds"] / 60
            if stats["avg_resolution_seconds"]
            else 0
        )
        m4.metric("AVG RESOLUTION", f'{avg_minutes:.1f}m')

        source_df = pd.DataFrame([
            {"source": key, "incidents": value}
            for key, value in stats["detection_sources"].items()
        ])
        if not source_df.empty:
            st.plotly_chart(
                px.bar(
                    source_df,
                    x="source",
                    y="incidents",
                    title="Detection source mix",
                ),
                use_container_width=True,
            )
    else:
        st.info(
            "🟢 No active incidents. Start the generator or inject a controlled incident."
        )

    st.divider()
    st.caption(
        "Live refresh: 2s • Rule + Isolation Forest + correlation intelligence • "
        "Madhusudhan V • AI-Powered Infrastructure Incident Narrative Generator"
    )


live_control_room()
