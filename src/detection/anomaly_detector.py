"""Lightweight unsupervised anomaly detection for infrastructure metrics.

The detector learns rolling healthy baselines with Isolation Forest. Metric
types are modelled separately so missing CPU/latency values are not treated
as synthetic numeric anomalies. A candidate event is scored against the
existing baseline before it can update that baseline.
"""
import re
from collections import defaultdict, deque
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

    if latency is None and cpu is None:
        return None

    return np.array([
        -1.0 if latency is None else latency,
        -1.0 if cpu is None else cpu,
    ], dtype=float)


def _signature(features):
    """Identify which metric dimensions are actually present."""
    return tuple(i for i, value in enumerate(features) if value >= 0)


class InfrastructureAnomalyDetector:
    """Online-style rolling Isolation Forest with metric-aware baselines."""

    def __init__(self, window=100, min_samples=20, contamination=0.05, random_state=42):
        self.window = window
        self.min_samples = min_samples
        self.contamination = contamination
        self.random_state = random_state
        self.samples_by_signature = defaultdict(lambda: deque(maxlen=window))
        self.models_by_signature = {}

    def update(self, event):
        """Score an event against its existing healthy baseline."""
        features = extract_features(event)
        if features is None:
            return {
                "available": False,
                "anomaly": False,
                "score": 0.0,
                "features": None,
            }

        signature = _signature(features)
        values = features[list(signature)]

        if hasattr(event, "severity"):
            severity = event.severity
        elif isinstance(event, dict):
            severity = event.get("severity", 0)
        else:
            severity = 0

        samples = self.samples_by_signature[signature]

        # Warm the baseline before a model is available.
        if len(samples) < self.min_samples:
            if severity < 2:
                samples.append(values)
            return {
                "available": False,
                "anomaly": False,
                "score": 0.0,
                "features": features.tolist(),
            }

        X = np.asarray(samples)
        model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        model.fit(X)
        self.models_by_signature[signature] = model

        prediction = int(model.predict([values])[0])
        raw_score = float(model.decision_function([values])[0])
        anomaly = prediction == -1

        # Convert the signed decision score into a bounded anomaly score.
        # This is a confidence-like score, not a probability.
        score = max(0.0, min(1.0, 0.5 - raw_score))

        # Only healthy, non-error, non-anomalous observations update the
        # baseline. The candidate itself must never train the model before
        # being scored, and anomalies are deliberately excluded from it.
        if severity < 2 and not anomaly:
            samples.append(values)

        return {
            "available": True,
            "anomaly": anomaly,
            "score": score,
            "features": features.tolist(),
        }
