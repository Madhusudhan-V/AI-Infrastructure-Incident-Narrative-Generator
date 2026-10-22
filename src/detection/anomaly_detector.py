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
    """Extract a non-negative numeric metric, if present."""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None

    value = float(match.group(1))
    return value if np.isfinite(value) and value >= 0 else None


def extract_features(event):
    """Return [latency_ms, cpu_pct] when either valid metric is present.

    Both dictionary-based events and objects with a message attribute are
    supported. Missing, non-text, negative, and non-finite values are ignored
    rather than being converted into misleading numeric features.
    """
    if isinstance(event, dict):
        message = event.get("message", "")
    else:
        message = getattr(event, "message", "")

    if not isinstance(message, str) or not message:
        return None

    latency = _number(r"\blatency_ms\s*=\s*(-?\d+(?:\.\d+)?)\b", message)
    cpu = _number(r"\bcpu_pct\s*=\s*(-?\d+(?:\.\d+)?)\b", message)

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
        if window < 1:
            raise ValueError("window must be at least 1")
        if min_samples < 2:
            raise ValueError("min_samples must be at least 2")
        if not 0.0 < contamination <= 0.5:
            raise ValueError("contamination must be greater than 0 and at most 0.5")

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

        # This transformed decision score is not a calibrated probability.
        score = max(0.0, min(1.0, 0.5 - raw_score))

        # Only healthy, non-error, non-anomalous observations update the
        # baseline. The candidate itself is scored before any update.
        if severity < 2 and not anomaly:
            samples.append(values)

        return {
            "available": True,
            "anomaly": anomaly,
            "score": score,
            "features": features.tolist(),
        }
