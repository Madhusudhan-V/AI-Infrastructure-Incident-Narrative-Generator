"""Repeat training/evaluation across seeds and Isolation Forest settings.

Run from the repository root:
    python -m src.evaluation.repeated_experiments
For a shorter check:
    python -m src.evaluation.repeated_experiments --repeats 1 --contamination 0.05

Each run constructs a fresh detector, warms its baseline from the healthy portion
of the deterministic synthetic stream, and then evaluates the stream. This is a
repeatability/sensitivity experiment, not a held-out real-world benchmark.
"""
from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from src.evaluation.run import evaluate


METRICS = ("precision", "recall", "f1", "false_positive_rate")


def run_experiments(repeats=3, contamination_values=(0.03, 0.05), seed_start=17):
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if not contamination_values:
        raise ValueError("provide at least one contamination value")
    if any(not 0 < value <= 0.5 for value in contamination_values):
        raise ValueError("contamination values must be in the range (0, 0.5]")

    rows = []
    for contamination in contamination_values:
        for repeat_index in range(repeats):
            seed = seed_start + repeat_index * 17
            result = evaluate(random_state=seed, contamination=contamination)
            metrics = result["classification"]
            rows.append({
                "repeat": repeat_index + 1,
                "random_state": seed,
                "contamination": contamination,
                "event_count": result["counts"]["total_events"],
                **{metric: metrics[metric] for metric in METRICS},
            })
    return rows


def summarize(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["contamination"], []).append(row)
    summaries = []
    for contamination, runs in sorted(grouped.items()):
        summary = {
            "contamination": contamination,
            "runs": len(runs),
        }
        for metric in METRICS:
            values = [float(run[metric]) for run in runs]
            summary[f"{metric}_mean"] = round(statistics.mean(values), 4)
            summary[f"{metric}_stdev"] = round(statistics.pstdev(values), 4)
        summaries.append(summary)
    return summaries


def write_csv(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3, help="fresh model runs per contamination setting")
    parser.add_argument(
        "--contamination",
        type=float,
        nargs="+",
        default=[0.03, 0.05],
        help="Isolation Forest contamination values to compare",
    )
    parser.add_argument("--seed-start", type=int, default=17)
    parser.add_argument(
        "--output",
        default="experiments/results/repeated_detection_runs.csv",
        help="CSV path for per-run results",
    )
    args = parser.parse_args()

    rows = run_experiments(
        repeats=args.repeats,
        contamination_values=tuple(args.contamination),
        seed_start=args.seed_start,
    )
    summaries = summarize(rows)
    write_csv(args.output, rows)

    print("Repeated Isolation Forest evaluation")
    print(f"Fresh model runs: {len(rows)}")
    print(f"Contamination settings: {args.contamination}")
    print(f"Per-run CSV: {args.output}")
    print("\nAggregate metrics (mean ± population standard deviation)")
    for summary in summaries:
        print(f"\ncontamination={summary['contamination']} runs={summary['runs']}")
        for metric in METRICS:
            print(
                f"{metric}: {summary[f'{metric}_mean']:.4f} "
                f"+/- {summary[f'{metric}_stdev']:.4f}"
            )


if __name__ == "__main__":
    main()
