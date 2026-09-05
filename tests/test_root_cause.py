"""
Unit Tests for Root Cause Analysis
"""

import pytest
from backend.root_cause import RootCauseAnalyzer
from backend.synthetic_data import (
    generate_synthetic_customers, generate_incident_scenario, IncidentType
)


def test_upi_timeout_root_cause_diagnosis():
    analyzer = RootCauseAnalyzer()
    customers = generate_synthetic_customers(50, seed=42)
    incident, txs = generate_incident_scenario(
        incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
        severity_pct=70.0,
        affected_count=300,
        customers=customers,
        seed=42
    )
    
    result = analyzer.analyze(txs)
    assert result.confidence >= 0.80
    assert "UPI" in result.likely_root_cause
    assert result.affected_dimension == "PAYMENT_METHOD"
    assert result.primary_failure_reason == "UPI_TIMEOUT"
    assert len(result.evidence) >= 2


def test_provider_outage_root_cause_diagnosis():
    analyzer = RootCauseAnalyzer()
    customers = generate_synthetic_customers(50, seed=42)
    incident, txs = generate_incident_scenario(
        incident_type=IncidentType.PROVIDER_OUTAGE,
        severity_pct=60.0,
        affected_count=200,
        customers=customers,
        seed=42
    )
    
    result = analyzer.analyze(txs)
    assert result.confidence >= 0.80
    assert result.affected_dimension == "PROVIDER"
    assert result.primary_failure_reason == "NETWORK_DISCONNECT"
    assert result.recommended_strategy == "REROUTE_ALTERNATE_PAYMENT"
