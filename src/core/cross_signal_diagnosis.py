"""Explainable, rule-based cross-signal incident diagnosis.

Scores are ranking scores, not calibrated probabilities or proof of causation.
The module deliberately consumes the incident events already available in Sentinel.
"""
from __future__ import annotations

import re


DEFAULT_DEPENDENCIES = {
    "api": ("database", "worker"),
    "api-service": ("database", "worker"),
    "checkout-api": ("database", "payment-service"),
    "checkout": ("database", "payment-service"),
}

PATTERNS = {
    "database_connection_exhaustion": {
        "label": "Database connection exhaustion",
        "direct": re.compile(
            r"connection pool exhausted|pool exhausted|too many connections|"
            r"database connection limit|connection limit reached|db connection exhausted",
            re.I,
        ),
        "support": re.compile(r"database|\bdb\b|sql|query", re.I),
        "contradiction": re.compile(r"pool healthy|connections normal|database healthy|no database errors", re.I),
        "checks": [
            "Inspect database connection-pool utilization and configured limits.",
            "Compare database response times with API latency over the incident window.",
            "Check for leaked connections, slow queries, and recent connection-pool changes.",
        ],
    },
    "network_connectivity_failure": {
        "label": "Network connectivity failure",
        "direct": re.compile(
            r"connection refused|network unreachable|upstream unavailable|"
            r"host unreachable|socket error|connection reset|dns resolution failed",
            re.I,
        ),
        "support": re.compile(r"network|gateway|upstream|timeout|connection", re.I),
        "contradiction": re.compile(r"network healthy|connectivity verified|upstream healthy|connection successful", re.I),
        "checks": [
            "Check connectivity between the affected service and its dependency.",
            "Inspect gateway, DNS, and upstream error logs for the same time window.",
            "Verify whether the dependency was reachable from the affected service.",
        ],
    },
    "resource_pressure": {
        "label": "Resource pressure",
        "direct": re.compile(
            r"out of memory|oom killed|memory pressure|cpu pressure|"
            r"high cpu|resource exhausted|cpu_pct\s*[=:]\s*(?:8[5-9]|9\d|100)(?:\.\d+)?",
            re.I,
        ),
        "support": re.compile(r"cpu|memory|resource|worker|latency_ms", re.I),
        "contradiction": re.compile(r"cpu normal|memory normal|resource usage normal|no resource pressure", re.I),
        "checks": [
            "Inspect CPU and memory utilization for the affected service.",
            "Check workload volume, recent deployments, and resource limits.",
            "Compare resource saturation with the start of the latency increase.",
        ],
    },
    "authentication_failure": {
        "label": "Authentication or authorization failure",
        "direct": re.compile(
            r"authentication failed|auth failed|unauthorized|invalid credentials|"
            r"permission denied|access denied|token expired",
            re.I,
        ),
        "support": re.compile(r"auth|login|token|permission|credential", re.I),
        "contradiction": re.compile(r"authentication succeeded|auth successful|authorized successfully", re.I),
        "checks": [
            "Inspect authentication-provider and authorization logs.",
            "Check token expiry, credential rotation, and recent access-policy changes.",
            "Confirm whether failures affect one identity or many requests.",
        ],
    },
    "latency_degradation": {
        "label": "Latency degradation",
        "direct": re.compile(
            r"latency(?: increased| high| degradation| spike)|slow response|"
            r"request timed out|latency_ms\s*[=:]\s*(?:[5-9]\d\d|\d{4,})(?:\.\d+)?",
            re.I,
        ),
        "support": re.compile(r"latency|slow|timeout|response time", re.I),
        "contradiction": re.compile(r"latency normal|response time normal|latency returned to normal", re.I),
        "checks": [
            "Compare latency across affected and healthy services.",
            "Inspect dependency response times and recent workload changes.",
            "Check whether latency recovers when the related signal clears.",
        ],
    },
}


def _event_text(event):
    return " ".join(
        str(event.get(key, "") or "")
        for key in ("message", "raw", "incident_type", "level", "service")
    )


def _metric_values(events):
    metrics = []
    for event in events:
        message = str(event.get("message", "") or "") + " " + str(event.get("raw", "") or "")
        item = {"timestamp": event.get("timestamp"), "service": event.get("service", "unknown")}
        latency = re.search(r"latency_ms\s*[=:]\s*(\d+(?:\.\d+)?)", message, re.I)
        cpu = re.search(r"cpu_pct\s*[=:]\s*(\d+(?:\.\d+)?)", message, re.I)
        if latency:
            item["latency_ms"] = float(latency.group(1))
        if cpu:
            item["cpu_pct"] = float(cpu.group(1))
        if len(item) > 2:
            metrics.append(item)
    return metrics


def diagnose_incident(incident, dependencies=None, top_k=3):
    """Return ranked hypotheses and evidence for an existing incident dictionary.

    The score is a transparent heuristic used only to rank candidates. It is
    intentionally not described as a probability or a confirmed root cause.
    """
    incident = incident or {}
    events = sorted(
        list(incident.get("events", []) or []),
        key=lambda event: str(event.get("timestamp", "") or ""),
    )
    if not events:
        return {
            "status": "insufficient_evidence",
            "summary": "No incident events are available for cross-signal diagnosis.",
            "ranking_note": "Scores rank candidate explanations; they are not probabilities.",
            "signals": [],
            "candidates": [],
        }

    dependencies = dependencies or DEFAULT_DEPENDENCIES
    event_texts = [_event_text(event) for event in events]
    all_text = "\n".join(event_texts)
    services = sorted({str(e.get("service")) for e in events if e.get("service")})
    metrics = _metric_values(events)

    latency_present = bool(re.search(
        r"latency|slow response|request timed out|latency_ms\s*[=:]\s*\d+",
        all_text, re.I
    ))
    cpu_high = any(item.get("cpu_pct", 0) >= 85 for item in metrics)
    if not cpu_high:
        cpu_high = bool(re.search(r"high cpu|cpu pressure|cpu utilization.{0,12}(?:8[5-9]|9\d|100)%", all_text, re.I))

    candidates = []
    for key, spec in PATTERNS.items():
        direct_events = [
            event for event, text in zip(events, event_texts)
            if spec["direct"].search(text)
        ]
        if not direct_events:
            continue

        support_events = [
            event for event, text in zip(events, event_texts)
            if event not in direct_events
            and not spec["contradiction"].search(text)
            and spec["support"].search(text)
        ]
        contradictory_events = [
            event for event, text in zip(events, event_texts)
            if spec["contradiction"].search(text)
        ]
        corroboration = 0
        if key != "latency_degradation" and latency_present:
            corroboration += 1
        if key != "resource_pressure" and cpu_high:
            corroboration += 1

        # A small, explainable ranking heuristic; not a probability.
        score = max(
            20,
            min(
                95,
                48
                + min(18, (len(direct_events) - 1) * 8)
                + min(20, len(support_events) * 7)
                + corroboration * 5
                - min(20, len(contradictory_events) * 10),
            ),
        )
        evidence = []
        for event in direct_events + support_events:
            evidence.append({
                "timestamp": event.get("timestamp", "unknown"),
                "service": event.get("service", "unknown"),
                "message": event.get("message", event.get("raw", "")),
                "role": "direct" if event in direct_events else "supporting",
            })

        candidates.append({
            "key": key,
            "hypothesis": spec["label"],
            "ranking_score": score,
            "score_interpretation": "Heuristic evidence-ranking score; not a probability.",
            "supporting_evidence": evidence,
            "contradictory_evidence": [
                {
                    "timestamp": event.get("timestamp", "unknown"),
                    "service": event.get("service", "unknown"),
                    "message": event.get("message", event.get("raw", "")),
                }
                for event in contradictory_events
            ],
            "uncertainty": (
                "The observed signals are consistent with this explanation, but the evidence "
                "does not establish causation."
            ),
            "next_checks": spec["checks"],
        })

    # Explicit dependency context can add a small ranking bonus where both
    # a known upstream and downstream service appear in the same incident.
    service_lower = {s.lower() for s in services}
    for candidate in candidates:
        linked = False
        for upstream, downstreams in dependencies.items():
            if upstream.lower() in service_lower and any(d.lower() in service_lower for d in downstreams):
                if candidate["key"] in {"database_connection_exhaustion", "network_connectivity_failure", "latency_degradation"}:
                    linked = True
                    break
        if linked:
            candidate["ranking_score"] = min(100, candidate["ranking_score"] + 5)
            candidate["dependency_context"] = "A configured service dependency is present in the incident."
        else:
            candidate["dependency_context"] = "No configured cross-service dependency was identified."

    candidates.sort(key=lambda item: (-item["ranking_score"], item["key"]))
    candidates = candidates[:max(1, int(top_k))]
    if candidates:
        status = "ranked_hypotheses"
        summary = (
            f"Ranked {len(candidates)} candidate explanation(s) from {len(events)} incident event(s). "
            "Review the evidence and validate the leading hypothesis before acting."
        )
    else:
        status = "insufficient_evidence"
        summary = (
            "The available incident signals do not match a supported diagnosis pattern. "
            "Collect more evidence rather than inferring a cause."
        )

    return {
        "status": status,
        "summary": summary,
        "ranking_note": "Scores rank candidate explanations; they are not probabilities or proof of causation.",
        "incident_id": incident.get("id"),
        "services": services,
        "metrics": metrics,
        "event_count": len(events),
        "candidates": candidates,
    }
