"""
Unit Tests for Stateful Recovery Agent Workflow & Accounting
"""

import pytest
from backend.agent import RecoveryAgentWorkflow
from backend.baseline import StaticBaselineRunner
from backend.synthetic_data import (
    generate_synthetic_customers, generate_incident_scenario, IncidentType
)
from backend.models import TransactionStatus


def test_recovery_workflow_execution():
    workflow = RecoveryAgentWorkflow()
    customers = generate_synthetic_customers(50, seed=42)
    incident, txs = generate_incident_scenario(
        incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
        severity_pct=70.0,
        affected_count=200,
        customers=customers,
        seed=42
    )
    
    updated_txs, metrics = workflow.run_recovery_workflow(
        incident=incident,
        transactions=txs,
        customers=customers,
        random_seed=42
    )
    
    assert metrics["strategy"] == "RECOVER_AI"
    assert metrics["total_recovered_paise"] > 0
    assert metrics["successful_recoveries"] > 0
    assert metrics["recovery_rate"] > 0.0
    # Invariant: Recovered amount must not exceed revenue at risk
    assert metrics["total_recovered_paise"] <= metrics["revenue_at_risk_paise"]
    assert incident.status == "RESOLVED"


def test_baseline_vs_recoverai_batch_invariants():
    customers = generate_synthetic_customers(50, seed=42)
    incident, txs = generate_incident_scenario(
        incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
        severity_pct=70.0,
        affected_count=200,
        customers=customers,
        seed=42
    )
    
    baseline = StaticBaselineRunner()
    workflow = RecoveryAgentWorkflow()
    
    # Run Baseline
    base_txs, base_metrics = baseline.run_baseline(txs, random_seed=42)
    # Run RecoverAI on the same batch
    agent_txs, agent_metrics = workflow.run_recovery_workflow(incident, txs, customers, random_seed=42)
    
    # Verify invariants
    assert base_metrics["recovered_paise"] <= incident.revenue_at_risk_paise
    assert agent_metrics["total_recovered_paise"] <= incident.revenue_at_risk_paise
    
    # Verify no double recoveries
    rec_agent = [t for t in agent_txs if t.status == TransactionStatus.RECOVERED.value]
    assert len(rec_agent) == agent_metrics["successful_recoveries"]
