from src.core.detector import parse_and_detect
from src.core.incident_engine import IncidentEngine

def test_database_detection():
    e=parse_and_detect('2026-09-19T00:00:00+00:00 ERROR database Connection pool exhausted active=50 max=50')
    assert e.detected and e.incident_type=='database_failure'

def test_incident_lifecycle():
    e=parse_and_detect('2026-09-19T00:00:00+00:00 CRITICAL api-service Requests failing error=database_unavailable')
    m=IncidentEngine(); i,new=m.add(e)
    assert new and i['id']=='INC-0001'
    m.update(i,'RESOLVED','Madhusudhan V','Service restored')
    assert i['status']=='RESOLVED'
