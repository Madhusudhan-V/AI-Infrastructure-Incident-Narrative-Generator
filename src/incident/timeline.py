def build_timeline(incident):
    return [{"timestamp":e["timestamp"],"level":e["level"],"message":e["message"]} for e in incident.get("events",[])]
