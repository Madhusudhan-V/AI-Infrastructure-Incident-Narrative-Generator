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

The `narrative_grounding_score` function measures how much supplied evidence is represented in a generated narrative. This is a lightweight automated check, not a substitute for human review.

## Repeatable multi-scenario experiment

Run:

```bash
python -m src.evaluation.run
```

The current synthetic experiment contains:

- 60 healthy baseline observations.
- 4 known failure cases covering database, network, authentication, and resource rules.
- 1 latency anomaly that intentionally avoids the deterministic failure vocabulary.
- 8 healthy observations after the anomaly to exercise the false-positive path.

The output reports two views:

1. **Overall actionable detection** — whether the fused system marked each labelled incident as detected.
2. **ML anomaly signal evaluation** — whether the Isolation Forest produced an anomaly signal when ML predictions were available.

The experiment is deterministic because the Isolation Forest uses a fixed random seed. It is still a controlled synthetic benchmark, not a claim of real-world accuracy. Results should be reported with the scenario count and limitations.

The HDFS dataset can then be used as a separate research experiment when it is reacquired and documented.

The evaluation code lives in `src/evaluation/evaluator.py` and is intentionally independent from the Streamlit UI so experiments remain reproducible.
