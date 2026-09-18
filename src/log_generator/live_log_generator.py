import argparse,random,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; LOG=ROOT/'data/sample_logs/application.log'
SCENARIOS={'database':['WARN api-service Connection latency increased latency_ms=850','ERROR database Connection pool exhausted active=50 max=50','ERROR api-service Database request failed error=timeout','CRITICAL api-service Requests failing error=database_unavailable'],'network':['WARN gateway Packet retransmission rate increased','ERROR gateway Connection refused upstream=payments','ERROR api-service Upstream network unreachable','CRITICAL gateway Requests dropped error=network_unavailable'],'auth':['WARN auth Invalid token rate increased','ERROR auth Authentication failed user_batch=42','ERROR api-service Unauthorized requests increased','CRITICAL auth Authentication service unavailable'],'resource':['WARN metrics CPU usage increased cpu_pct=94','ERROR worker Out of memory while processing batch','CRITICAL worker OOM killer terminated process']}
NORMAL=['INFO api-service Request completed latency_ms={lat}','INFO worker Job completed job_id=job-{id}','INFO cache Cache lookup completed key=user-{id}','INFO metrics CPU usage sampled cpu_pct={cpu}']
def write(msg):
 LOG.parent.mkdir(parents=True,exist_ok=True)
 with LOG.open('a',encoding='utf-8') as f:f.write(f'{datetime.now(timezone.utc).isoformat(timespec="seconds")} {msg}\n')
def inject_incident(kind='database'):
 for msg in SCENARIOS.get(kind,SCENARIOS['database']):write(msg);time.sleep(.7)
def main():
 p=argparse.ArgumentParser();p.add_argument('--interval',type=float,default=2);p.add_argument('--incident-every',type=int,default=25);p.add_argument('--scenario',choices=list(SCENARIOS),default='database');a=p.parse_args();i=0
 print(f'Live logs: {LOG}')
 while True:
  i+=1
  if a.incident_every and i%a.incident_every==0:inject_incident(a.scenario)
  else:write(random.choice(NORMAL).format(id=random.randint(1000,9999),lat=random.randint(10,120),cpu=random.randint(10,80)))
  time.sleep(a.interval)
if __name__=='__main__':main()
