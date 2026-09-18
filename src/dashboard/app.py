import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from src.core.detector import parse_and_detect
from src.core.incident_engine import IncidentEngine
from src.core.storage import init,save
from src.core.ai import generate
from src.log_generator.live_log_generator import inject_incident

ROOT=Path(__file__).resolve().parents[2]; LOG=ROOT/'data/sample_logs/application.log'; load_dotenv(ROOT/'.env')
DB=os.getenv('DATABASE_PATH',str(ROOT/'data/runtime/incidents.db')); init(DB)
st.set_page_config(page_title='Sentinel Incident Center',page_icon='◉',layout='wide')
st.markdown('<style>.block-container{max-width:1500px;padding-top:1.5rem}.hero{padding:1.4rem;border:1px solid #263247;border-radius:20px;background:linear-gradient(135deg,#0d1420,#182235);margin-bottom:1rem}.hero h1{margin:0}.hero p{color:#9ba9bb}.section{font-weight:700;letter-spacing:.08em}</style>',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>◉ SENTINEL INCIDENT INTELLIGENCE CENTER</h1><p>Live infrastructure observability • detection • correlation • AI-assisted incident analysis</p></div>',unsafe_allow_html=True)
if 'engine' not in st.session_state: st.session_state.engine=IncidentEngine(); st.session_state.seen=0; st.session_state.events=[]
with st.sidebar:
 st.header('CONTROL ROOM'); st.write('Project Lead: Madhusudhan V')
 scenario=st.selectbox('Demo scenario',['database','network','auth','resource'])
 if st.button('⚡ Inject Incident',type='primary',use_container_width=True): inject_incident(scenario); st.rerun()
 if st.button('Reset session',use_container_width=True): st.session_state.clear(); st.rerun()
lines=LOG.read_text(encoding='utf-8').splitlines() if LOG.exists() else []
for line in lines[st.session_state.seen:]:
 e=parse_and_detect(line)
 if e:
  st.session_state.events.append(e); result=st.session_state.engine.add(e)
  if result: save(DB,result[0])
st.session_state.seen=len(lines)
events=st.session_state.events; incs=st.session_state.engine.incidents; active=[i for i in incs if i['status']!='RESOLVED']
cols=st.columns(5)
for col,label,value in zip(cols,['LOG EVENTS','ERRORS','INCIDENTS','CRITICAL','SYSTEM'],[len(events),sum(e.severity>=2 for e in events),len(incs),sum(e.severity>=3 for e in events),'INCIDENT' if active else 'HEALTHY']): col.metric(label,value)
st.divider()
left,right=st.columns([1.35,.65])
with left:
 st.subheader('LIVE EVENT STREAM'); st.code('\n'.join(lines[-28:]) or 'Waiting for logs...',language='text')
with right:
 st.subheader('DETECTION ANALYTICS')
 if events:
  df=pd.DataFrame([{'type':e.incident_type or 'normal','severity':e.severity} for e in events]); counts=df['type'].value_counts().reset_index(); counts.columns=['type','count']; st.plotly_chart(px.bar(counts,x='type',y='count'),use_container_width=True)
 else: st.info('No detected events yet.')
if incs:
 i=incs[-1]; st.divider(); st.subheader('🔴 INCIDENT '+i['id'])
 a,b,c,d=st.columns(4); a.metric('TYPE',i['type'].replace('_',' ').upper()); b.metric('SEVERITY',i['severity']); c.metric('CONFIDENCE',f"{i['confidence']:.0%}"); d.metric('STATUS',i['status'])
 t1,t2,t3=st.tabs(['TIMELINE','AI NARRATIVE','RAW EVIDENCE'])
 with t1:
  for e in i['events']: st.markdown(f"**{e['timestamp']}**  `{e['level']}`  `{e['service']}` — {e['message']}")
 with t2: st.markdown(generate(i)); st.caption('AI output is grounded in observed evidence; verify operational conclusions.')
 with t3: st.json(i)
 st.subheader('INCIDENT COMMANDER REVIEW')
 status=st.selectbox('Status',['DETECTED','INVESTIGATING','RESOLVED'],index=['DETECTED','INVESTIGATING','RESOLVED'].index(i['status']))
 owner=st.text_input('Owner',i['owner']); resolution=st.text_area('Resolution / analyst notes',i['resolution'])
 if st.button('Save Review'): st.session_state.engine.update(i,status,owner,resolution); save(DB,i); st.rerun()
 st.divider(); st.subheader('INCIDENT HISTORY'); st.dataframe(pd.DataFrame([{'ID':x['id'],'TYPE':x['type'],'SEVERITY':x['severity'],'EVENTS':len(x['events']),'STATUS':x['status']} for x in incs]),hide_index=True,use_container_width=True)
else: st.info('🟢 No active incidents. Start the generator or inject a controlled incident.')
st.divider(); st.caption('Madhusudhan V • AI-Powered Infrastructure Incident Narrative Generator • Final-year capstone')
