"""Fuse deterministic rules and ML anomaly signals into one event decision."""


def fuse(event, ml_result, threshold=0.56):
    """Enrich an Event with an ML signal and promote strong anomalies to incidents.

    Rules remain the primary deterministic signal. A sufficiently strong Isolation Forest
    anomaly can promote an otherwise non-error metric event to a severity-2
    statistical anomaly so it enters the normal incident correlation flow.
    """
    if not ml_result or not ml_result.get("available"):
        return event

    score = float(ml_result.get("score", 0.0))
    anomaly = bool(ml_result.get("anomaly"))
    event.anomaly_score = score
    event.ml_anomaly = anomaly

    if anomaly and score >= threshold:
        event.detected = True
        if not event.incident_type:
            event.incident_type = "statistical_anomaly"
        event.severity = max(event.severity, 2)
        event.confidence = max(event.confidence, score)

    return event
