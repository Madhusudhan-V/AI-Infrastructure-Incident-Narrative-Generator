"""Optional lightweight anomaly detector. The rules remain the project baseline."""
from collections import deque
class RateAnomalyDetector:
    def __init__(self, window=20, threshold=3): self.events=deque(maxlen=window); self.threshold=threshold
    def update(self, event):
        self.events.append(event)
        errors=sum(e.get("score",0)>=2 for e in self.events)
        return errors >= self.threshold
