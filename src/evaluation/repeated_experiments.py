"""Run repeated Sentinel detection experiments.

Usage:
    python -m src.evaluation.repeated_experiments
"""

import argparse
import csv
import statistics
from pathlib import Path

from src.evaluation.run import evaluate

METRICS = ("precision", "recall", "f1", "false_positive_rate")


def summarize(rows):
    """Group runs by contamination and calculate means and variation."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row["contamination"], []).append(row)

    summaries = []
    for contamination in sorted(grouped):
        group = grouped[contamination]
        summary = {"contamination": contamination, "runs": len(group)}

        for metric in METRICS:
            values = [float(row[metric]) for row in group]
            summary[f"{metric}_mean"] = round(statistics.mean(values), 10)
            summary[f"{metric}_stdev"] = (
                round(statistics.pstdev(values), 10) if len(values) > 1 else 0.0
            )

        summaries.append(summary)

    return summaries


def run_experiments(repeats=3, contamination_values=(0.03, 0.05), seed_start=17):
    """Run evaluations with fresh detectors across seeds and settings."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")

    contamination_values = tuple(contamination_values)
    if not contamination_values or any(
        not 0.0 < value <= 0.5 for value in contamination_values
    ):
        raise ValueError(
            "contamination values must be greater than 0 and at most 0.5"
        )

    rows = []
    for contamination in contamination_values:
        for run_index in range(repeats):
            seed = seed_start + run_index
            result = evaluate(random_state=seed, contamination=contamination)
            row = {
                "contamination": contamination,
                "seed": seed,
                **{
                    metric: result["ml_signal"].get(metric, 0.0)
                    for metric in METRICS
                },
            }
            rows.append(row)

            print(
                f"contamination={contamination:.3f} seed={seed} "
                f"precision={row['precision']:.4f} "
                f"recall={row['recall']:.4f} f1={row['f1']:.4f} "
                f"false_positive_rate={row['false_positive_rate']:.4f}"
            )

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Repeat Sentinel anomaly detection experiments."
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--contamination", type=float, nargs="+", default=[0.03, 0.05]
    )
    parser.add_argument("--seed-start", type=int, default=17)
    parser.add_argument(
        "--output", default="experiments/results/repeated_detection_runs.csv"
    )
    args = parser.parse_args()

    rows = run_experiments(
        repeats=args.repeats,
        contamination_values=args.contamination,
        seed_start=args.seed_start,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("\nExperiment summary")
    for summary in summarize(rows):
        print(summary)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
