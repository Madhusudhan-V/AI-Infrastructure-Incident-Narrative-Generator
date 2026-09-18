from pathlib import Path
import streamlit as st
from src.detection.rule_engine import classify
from src.incident.incident_manager import IncidentManager
from src.narrative.narrative_generator import generate
from src.notification.notifier import notify

ROOT=Path(__file__).resolve().parents[2]
LOG=ROOT/"data/sample_logs/application.log"
st.set_page_config(page_title="Incident Narrative Generator",layout="wide")
st.title("AI-Powered Infrastructure Incident Narrative Generator")
st.caption("Project Lead: Madhusudhan V | Local-first final-year capstone")

if "events" not in st.session_state: st.session_state.events=[]
if "manager" not in st.session_state: st.session_state.manager=IncidentManager()
if "last_size" not in st.session_state: st.session_state.last_size=0

if st.button("Inject Demo Incident"):
    from src.log_generator.live_log_generator import inject_incident
    inject_incident()
    st.success("Controlled incident injected into the live log.")

text=LOG.read_text(encoding="utf-8") if LOG.exists() else ""
lines=text.splitlines()
new_lines=lines[st.session_state.last_size:]
for line in new_lines:
    event=classify(line)
    if event:
        st.session_state.events.append(event)
        incident=st.session_state.manager.add(event)
        if incident: notify(incident)
st.session_state.last_size=len(lines)

all_events=st.session_state.events
incidents=st.session_state.manager.incidents
c1,c2,c3,c4=st.columns(4)
c1.metric("Events",len(all_events))
c2.metric("Errors",sum(e["score"]>=2 for e in all_events))
c3.metric("Incidents",len(incidents))
c4.metric("Status","Incident" if incidents else "Healthy")

st.subheader("Live Log")
st.code("\n".join(lines[-20:]) or "Waiting for logs...", language="text")
if incidents:
    incident=incidents[-1]
    st.subheader(f"Latest Incident — {incident['id']}")
    st.write({"type":incident["type"],"severity":incident["severity"],"events":len(incident["events"])})
    st.markdown("### Timeline")
    for e in incident["events"]:
        st.write(f"{e['timestamp']} [{e['level']}] — {e['message']}")
    st.markdown("### AI Incident Narrative")
    st.info(generate(incident))

st.divider()
st.caption("Refresh the page after new log events. Start the generator in another terminal for continuous live-feed behavior.")
