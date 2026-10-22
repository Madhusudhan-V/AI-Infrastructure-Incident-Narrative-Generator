from src.core.cross_signal_diagnosis import diagnose_incident


def test_database_connection_exhaustion_ranks_above_latency_symptom():
    incident = {
        "id": "INC-0001",
        "events": [
            {
                "timestamp": "2026-09-20T10:02:01+00:00",
                "service": "database",
                "message": "Connection pool exhausted active=50 max=50",
            },
            {
                "timestamp": "2026-09-20T10:02:04+00:00",
                "service": "api-service",
                "message": "Request completed latency_ms=900",
            },
        ],
    }

    result = diagnose_incident(incident)

    assert result["status"] == "ranked_hypotheses"
    assert result["candidates"][0]["key"] == "database_connection_exhaustion"
    assert result["candidates"][0]["supporting_evidence"]
    assert "not probabilities" in result["ranking_note"]


def test_resource_pressure_is_detected_from_cpu_metric():
    incident = {
        "events": [
            {
                "timestamp": "2026-09-20T10:02:01+00:00",
                "service": "worker",
                "message": "CPU usage sampled cpu_pct=96",
            },
            {
                "timestamp": "2026-09-20T10:02:04+00:00",
                "service": "api-service",
                "message": "Slow response latency_ms=700",
            },
            {
                "timestamp": "2026-09-20T10:02:07+00:00",
                "service": "worker",
                "message": "Resource pressure high CPU",
            },
        ],
    }

    result = diagnose_incident(incident)

    assert any(c["key"] == "resource_pressure" for c in result["candidates"])


def test_empty_incident_returns_insufficient_evidence():
    result = diagnose_incident({"id": "INC-EMPTY", "events": []})

    assert result["status"] == "insufficient_evidence"
    assert result["candidates"] == []


def test_unrecognized_events_do_not_invent_a_diagnosis():
    incident = {
        "events": [
            {
                "timestamp": "2026-09-20T10:02:01+00:00",
                "service": "api-service",
                "message": "Request completed successfully",
            }
        ]
    }

    result = diagnose_incident(incident)

    assert result["status"] == "insufficient_evidence"
    assert result["candidates"] == []


def test_authentication_failure_is_not_mislabeled_as_database_failure():
    incident = {
        "events": [
            {
                "timestamp": "2026-09-20T10:02:01+00:00",
                "service": "auth",
                "message": "Authentication failed user_batch=42",
            }
        ]
    }

    result = diagnose_incident(incident)

    assert result["candidates"][0]["key"] == "authentication_failure"
