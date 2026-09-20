"""Compatibility wrapper for evidence-backed incident timelines."""
from src.core.incident_intelligence import build_timeline as _build_timeline


def build_timeline(incident):
    """Return the historical list-shaped timeline API.

    The richer lifecycle representation is available from
    src.core.incident_intelligence.build_timeline.
    """
    return _build_timeline(incident)["events"]
