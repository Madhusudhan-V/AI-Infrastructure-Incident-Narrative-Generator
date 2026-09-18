from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import streamlit as st
import pandas as pd
from src.detection.rule_engine import classify
from src.incident.incident_manager import IncidentManager
from src.narrative.narrative_generator import generate
from src.notification.notifier import notify

ROOT=Path(__file__).resolve().parents[2]
LOG=ROOT/"data/sample_logs/application.log"

st.set_page_config(page_title="Sentinel Incident Intelligence",page_icon="◉",layout="wide")

st.markdown("""
<style>
.block-container{padding-top:2rem;max-width:1500px}
.hero{padding:1.2rem 1.4rem;border:1px solid #263042;border-radius:18px;background:linear-gradient(135deg,#101722,#151c2b);margin-bottom:1rem}
.hero h1{margin:0;font-size:2.1rem}
.hero p{color:#9aa7b8;margin:.35rem 0 0}
.card{padding:1rem;border:1px solid #263042;border-radius:16px;background:#111722}
.status{font-size:1.4rem;font-weight:700}
.small{color:#8d9aac;font-size:.85rem}
.timeline{border-left:2px solid #38475c;padding-left:1rem;margin-left:.4rem}
.event{padding:.55rem .8rem;margin:.45rem 0;border-radius:10px;background:#151d29}
</style>
""",unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>◉ SENTINEL — INCIDENT INTELLIGENCE CENTER</h1>
<p>AI-powered infrastructure observability • evidence → incident → timeline → narrative</p>
</div>
""",unsafe_allow_html=True)

if "events" not in st.session_state: st.session_state.events=[]
if "manager" not in st.session_state: st.session_state.manager=IncidentManager()
if "last_size" not in st.session_state: st.session_state.last_size=0

top1,top2,top3=st.columns([2,1,1])
with top1:
    st.markdown("**SYSTEM CONTROL**")
    if st.button("⚡ INJECT CONTROLLED INCIDENT",type="primary",use_container_width=True):
        from src.log_generator.live_log_generator import inject_incident
        inject_incident()
        st.rerun()
with top2:
    st.markdown("**PROJECT LEAD**")
    st.markdown("Madhusudhan V")
with top3:
    st.markdown("**PIPELINE**")
    st.markdown("LIVE • LOCAL-FIRST")

lines=LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else ""
if isinstance(lines,str): lines=lines.splitlines()
new_lines=lines[st.session_state.last_size:]
for line in new_lines:
    event=classify(line)
    if event:
        st.session_state.events.append(event)
        incident=st.session_state.manager.add(event)
        if incident: notify(incident)
st.session_state.last_size=len(lines)

events=st.session_state.events
incidents=st.session_state.manager.incidents
errors=[e for e in events if e.get("score",0)>=2]
critical=[e for e in events if e.get("score",0)>=3]
active=[i for i in incidents if i.get("status","DETECTED")!="RESOLVED"]

st.divider()
a,b,c,d,e=st.columns(5)
a.metric("LOG EVENTS",len(events))
b.metric("ERROR EVENTS",len(errors))
c.metric("INCIDENTS",len(incidents))
d.metric("CRITICAL",len(critical))
e.metric("SYSTEM STATUS","INCIDENT" if active else "HEALTHY")

left,right=st.columns([1.35,.85])
with left:
    st.subheader("LIVE EVENT STREAM")
    st.code("\n".join(lines[-22:]) or "Waiting for live logs...",language="text")
with right:
    st.subheader("SERVICE PULSE")
    service_rows=[]
    for name in ["api-service","database","worker","cache"]:
        related=[x for x in events if name in x.get("message","")]
        sev=max([x.get("score",0) for x in related],default=0)
        state="CRITICAL" if sev>=3 else "DEGRADED" if sev>=2 else "HEALTHY"
        service_rows.append({"SERVICE":name,"STATE":state,"EVENTS":len(related)})
    st.dataframe(pd.DataFrame(service_rows),hide_index=True,use_container_width=True)

st.divider()
if incidents:
    incident=incidents[-1]
    st.subheader(f"🔴 ACTIVE INCIDENT  /  {incident['id']}")
    q1,q2,q3,q4=st.columns(4)
    q1.metric("TYPE",incident["type"].replace("_"," ").upper())
    q2.metric("SEVERITY",incident["severity"])
    q3.metric("EVIDENCE",len(incident["events"]))
    q4.metric("STATUS",incident.get("status","DETECTED"))

    tab1,tab2,tab3=st.tabs(["TIMELINE","AI NARRATIVE","EVIDENCE"])
    with tab1:
        st.markdown('<div class="timeline">',unsafe_allow_html=True)
        for ev in incident["events"]:
            st.markdown(f'<div class="event"><b>{ev["timestamp"]}</b> &nbsp; <code>{ev["level"]}</code><br>{ev["message"]}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with tab2:
        st.markdown("### AI-generated incident narrative")
        st.info(generate(incident))
        st.caption("Narrative is grounded in observed log evidence. Root cause should be verified by an analyst.")
    with tab3:
        st.json(incident)

    st.divider()
    st.subheader("INCIDENT HISTORY")
    history=pd.DataFrame([{
        "ID":i["id"],"TYPE":i["type"].replace("_"," ").title(),
        "SEVERITY":i["severity"],"EVENTS":len(i["events"]),
        "STATUS":i.get("status","DETECTED")
    } for i in incidents])
    st.dataframe(history,hide_index=True,use_container_width=True)
else:
    st.info("🟢 No active incidents. Start the live generator or inject a controlled incident to test the pipeline.")

st.divider()
st.markdown("**Architecture:** Live Logs → Detection → Correlation → Timeline → AI Narrative → Analyst Review")
st.caption("Madhusudhan V • AI-Powered Infrastructure Incident Narrative Generator • Final-year capstone")
