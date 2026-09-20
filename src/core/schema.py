from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Event:
    timestamp: str
    level: str
    service: str
    message: str
    raw: str
    detected: bool = False
    incident_type: Optional[str] = None
    severity: int = 0
    confidence: float = 0.0
    rule_matches: list[str] = field(default_factory=list)
    ml_anomaly: bool = False
    anomaly_score: float = 0.0

@dataclass
class Incident:
    id: str
    created_at: str
    updated_at: str
    incident_type: str
    severity: int
    confidence: float
    status: str = "DETECTED"
    owner: str = "Unassigned"
    resolution: str = ""
    events: list[dict] = field(default_factory=list)
    correlation_score: float = 1.0
    services: list[str] = field(default_factory=list)
