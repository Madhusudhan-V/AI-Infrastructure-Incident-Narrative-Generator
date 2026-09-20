"""Lightweight unsupervised anomaly detection for infrastructure metrics.

The detector learns a rolling baseline from non-error observations and uses
Isolation Forest to flag unusual latency/CPU combinations. Rule-based
detection remains the deterministic safety net for known failures.
"""
import re
from collections import deque
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest


def _number(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_features(event):
    """Return [latency_ms, cpu_pct] when either metric is present."""
    message = getattr(event, "message", "") or event.get("message", "")
    latency = _number(r"latency_ms=(\d+(?:\.\d+)?)", message)
    cpu = _number(r"cpu_pct=(\d+(?:\.\d+)?)", message)

    # Keep a stable two-dimensional feature vector. Missing values are -1.
    if latency is None and cpu is None:
        return None
    return np.array([
        -1.0 if latency is None else latency,
        -1.0 if cpu is None else cpu,
    ], dtype=float)


class InfrastructureAnomalyDetector:
    """Online-style rolling Isolation Forest for infrastructure metrics."""

    def __init__(self, window=100, min_samples=20, contamination=0.05, random_state=42):
        self.samples = deque(maxlen=window)
        self.min_samples = min_samples
        self.contamination = contamination
        self.random_state = random_state
        self.model = None

    def update(self, event):
        """Return a result dict describing whether the event is anomalous."""
        features = extract_features(event)
        if features is None:
            return {
                "available": False,
                "anomaly": False,
                "score": 0.0,
                "features": None,
            }

        # Only healthy/non-error observations train the baseline.
        if hasattr(event, "severity"):
            severity = event.severity
        elif isinstance(event, dict):
            severity = event.get("severity", 0)
        else:
            severity = 0
        if severity < 2:
            self.samples.append(features)

        if len(self.samples) < self.min_samples:
            return {
                "available": False,
                "anomaly": False,
                "score": 0.0,
                "features": features.tolist(),
            }

        X = np.asarray(self.samples)
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.model.fit(X)

        prediction = int(self.model.predict([features])[0])
        raw_score = float(self.model.decision_function([features])[0])
        anomaly = prediction == -1

        # Convert the signed decision score into a simple confidence-like
        # anomaly score for UI/evaluation. It is not a probability.
        score = max(0.0, min(1.0, 0.5 - raw_score))

        return {
            "available": True,
            "anomaly": anomaly,
            "score": score,
            "features": features.tolist(),
        }
