# Evaluation Plan

## Detection metrics

The evaluation layer reports:

- Precision — proportion of predicted detections that are true positives.
- Recall — proportion of labelled incidents/events detected.
- F1 — harmonic mean of precision and recall.
- False-positive rate — false alarms divided by all negative examples.
- Detection latency — time from labelled ground-truth event to first detection.

## Incident intelligence

The live incident engine also measures:

- Correlation score for each event-to-incident association.
- Incident grouping accuracy against labelled expected groups.
- Severity escalation based on observed severity, repeated evidence, and strong ML anomaly scores.
- Affected-service count.
- Resolution duration for incidents marked RESOLVED.
- Detection-source mix: rule, ML, or rule+ML.

## Narrative grounding

The narrative_grounding_score function measures how much supplied evidence is represented in a generated narrative. This is a lightweight automated check, not a substitute for human review.

## Repeatable experiments

Use controlled synthetic scenarios first because their ground truth is known. Run the same scenarios before and after detector changes and compare the metrics. The HDFS dataset can then be used as a separate research experiment when it is reacquired and documented.

The evaluation code lives in src/evaluation/evaluator.py and is intentionally independent from the Streamlit UI so experiments remain reproducible.
