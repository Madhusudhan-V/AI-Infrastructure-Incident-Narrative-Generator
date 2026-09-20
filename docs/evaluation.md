# Evaluation

## Purpose

Sentinel's evaluation measures how well the fused detection pipeline identifies actionable infrastructure incidents while limiting false alarms. The benchmark is intentionally deterministic and synthetic so that the experiment can be reproduced from the repository.

## How to run

From the repository root:

```bash
python -m src.evaluation.run
```

The evaluation uses the same production detection path:

```text
Synthetic events
    -> Rule detection + Isolation Forest
    -> Detection fusion (threshold = 0.56)
    -> Ground-truth comparison
    -> Metrics
```

The Isolation Forest uses a fixed random seed, making the experiment repeatable.

## Final synthetic benchmark

The current benchmark contains **400 events**:

| Dataset component | Count |
|---|---:|
| Healthy latency observations | 100 |
| Healthy CPU observations | 100 |
| Database failure incidents | 20 |
| Network failure incidents | 20 |
| Authentication failure incidents | 20 |
| Resource-pressure incidents | 20 |
| ML latency anomalies | 20 |
| **Total** | **400** |

The ML latency anomalies are intentionally generated without deterministic failure vocabulary so that they exercise the statistical anomaly-detection path.

### Overall actionable detection

| Metric | Result |
|---|---:|
| True positives | 98 |
| True negatives | 290 |
| False positives | 10 |
| False negatives | 2 |
| **Precision** | **90.74%** |
| **Recall** | **98.00%** |
| **F1** | **94.23%** |
| **False-positive rate** | **3.33%** |

These results mean that, on this synthetic benchmark, the fused system detected 98 of 100 labelled incident events while producing 10 false alarms among 300 negative examples.

### ML anomaly signal evaluation

The ML signal is evaluated separately from the final actionable decision because an Isolation Forest anomaly signal can be useful for investigation without necessarily being promoted to an actionable incident.

| Metric | Result |
|---|---:|
| True positives | 20 |
| True negatives | 233 |
| False positives | 27 |
| False negatives | 0 |
| **Precision** | **42.55%** |
| **Recall** | **100.00%** |
| **F1** | **59.70%** |
| **False-positive rate** | **10.38%** |

The distinction is important: the ML detector is deliberately used as a statistical signal, while deterministic rules and the fusion threshold decide when an anomaly becomes actionable.

## Per-scenario results

The benchmark produced the following results:

| Scenario | TP | TN | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Database failure | 20 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Network failure | 20 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Authentication failure | 20 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Resource pressure | 20 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| ML latency anomaly | 18 | 0 | 0 | 2 | 1.00 | 0.90 | 0.9474 |

**Interpretation:** these scenario slices contain only positive examples, so their true-negative counts are zero. They should not be interpreted as standalone accuracy tests. The overall 400-event benchmark is the primary classification result.

## Threshold selection

The detection-fusion threshold was calibrated using the same controlled synthetic benchmark. A candidate threshold of **0.56** produced the selected operating point:

- Precision: **90.74%**
- Recall: **98.00%**
- F1: **94.23%**
- False-positive rate: **3.33%**

The threshold is an engineering calibration for this benchmark, not a universally optimal value. A production deployment should recalibrate it against representative labelled operational data.

## Other evaluation dimensions

The project also exposes additional incident-intelligence signals that can be evaluated independently:

- Correlation score for event-to-incident association.
- Incident grouping and timeline reconstruction.
- Severity escalation based on observed evidence.
- Affected-service count.
- Resolution duration for incidents marked `RESOLVED`.
- Detection-source mix: rule, ML, or rule+ML.
- Narrative grounding against supplied incident evidence.

The narrative grounding score is a lightweight automated check and does not replace human review.

## Limitations

This benchmark is **synthetic** and should not be presented as production or real-world accuracy.

Important limitations:

1. The generated events are controlled and may not represent the diversity of real infrastructure failures.
2. The rule detector uses deterministic signatures that are easier to detect than ambiguous production incidents.
3. Isolation Forest performance depends on the baseline distribution and feature availability.
4. The ML anomaly score is a confidence-like score, **not a calibrated probability**.
5. Correlation and severity logic use heuristic weights and thresholds.
6. The benchmark does not establish performance on the HDFS dataset.
7. The HDFS dataset is not part of this final 400-event benchmark.

For a stronger research evaluation, future work should use labelled production-like logs, multiple workload distributions, repeated random seeds, and a held-out test set.

## Reproducibility

The benchmark can be regenerated with:

```bash
python -m src.evaluation.run
```

The evaluation code is intentionally separate from the Streamlit dashboard so that detection experiments remain reproducible and independent of the UI.
