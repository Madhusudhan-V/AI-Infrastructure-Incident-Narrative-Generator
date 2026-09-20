"""Repeatable evaluation metrics for the detection and incident pipeline."""
from collections import Counter
from datetime import datetime


def classification_metrics(y_true, y_pred):
    """Calculate precision, recall, F1, and false-positive rate."""
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    tn = sum((not t) and (not p) for t, p in zip(y_true, y_pred))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    return {
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
    }


def detection_latency_seconds(first_event, detection_event):
    """Return seconds between ground-truth event and first detection."""
    start = datetime.fromisoformat(first_event.replace("Z", "+00:00"))
    end = datetime.fromisoformat(detection_event.replace("Z", "+00:00"))
    return max(0.0, (end - start).total_seconds())


def grouping_accuracy(expected_groups, predicted_groups):
    """Compare expected incident labels with predicted group assignments."""
    if not expected_groups:
        return 0.0
    correct = sum(
        expected == predicted
        for expected, predicted in zip(expected_groups, predicted_groups)
    )
    return round(correct / len(expected_groups), 4)


def narrative_grounding_score(narrative, evidence_messages):
    """Measure how many evidence messages are represented in a generated narrative."""
    text = (narrative or "").lower()
    evidence = [message.lower().strip() for message in evidence_messages if message]
    if not evidence:
        return 0.0
    matched = sum(message in text for message in evidence)
    return round(matched / len(evidence), 4)


def summarize_runs(runs):
    """Aggregate metric dictionaries from repeated evaluation runs."""
    if not runs:
        return {}
    keys = ["precision", "recall", "f1", "false_positive_rate"]
    return {
        key: round(sum(run.get(key, 0.0) for run in runs) / len(runs), 4)
        for key in keys
    }
