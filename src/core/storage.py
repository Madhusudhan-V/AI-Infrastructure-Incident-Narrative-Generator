import json, sqlite3
from pathlib import Path

SCHEMA="""CREATE TABLE IF NOT EXISTS incidents (
id TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT, type TEXT, severity INTEGER,
confidence REAL, status TEXT, owner TEXT, resolution TEXT, events TEXT)"""

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    return sqlite3.connect(path)

def init(path):
    with connect(path) as db:
        db.execute(SCHEMA); db.commit()

def save(path,incident):
    init(path)
    with connect(path) as db:
        db.execute("""INSERT OR REPLACE INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (incident["id"],incident["created_at"],incident["updated_at"],incident["type"],
         incident["severity"],incident["confidence"],incident["status"],incident["owner"],
         incident["resolution"],json.dumps(incident["events"])))
        db.commit()

def load(path):
    init(path)
    with connect(path) as db:
        rows=db.execute("SELECT * FROM incidents ORDER BY created_at ASC").fetchall()
    return [{"id":r[0],"created_at":r[1],"updated_at":r[2],"type":r[3],"severity":r[4],
             "confidence":r[5],"status":r[6],"owner":r[7],"resolution":r[8],"events":json.loads(r[9])} for r in rows]
