from datetime import datetime

def notify(incident):
    print(f"INCIDENT {incident['id']} severity={incident['severity']} type={incident['type']} at {datetime.now().isoformat()}")
