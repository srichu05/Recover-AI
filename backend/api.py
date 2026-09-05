"""
FastAPI Route Handlers for RecoverAI
Provides clean, structured REST endpoints for the Fintech Dashboard and Incident Simulator.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from backend.models import (
    Incident, Transaction, Customer, AuditRecord,
    AgentReplayStep, EvaluationSummary, ScenarioResult,
    IncidentType, PaymentMethod, IncidentSeverity
)
from backend.storage import db
from backend.synthetic_data import generate_incident_scenario
from backend.agent import RecoveryAgentWorkflow
from backend.baseline import StaticBaselineRunner
from backend.audit import audit_manager
from backend.config import settings
from evaluation.run_evaluation import EvaluationEngine

router = APIRouter(prefix="/api")
agent_workflow = RecoveryAgentWorkflow()
baseline_runner = StaticBaselineRunner()


class CreateIncidentRequest(BaseModel):
    title: Optional[str] = None
    incident_type: str = "UPI_TIMEOUT_SPIKE"
    payment_method: str = "UPI"
    severity_pct: float = 70.0
    affected_count: int = 500
    random_seed: Optional[int] = 42


class RecoveryRunResponse(BaseModel):
    incident_id: str
    status: str
    revenue_at_risk_paise: int
    recoverai_recovered_paise: int
    baseline_recovered_paise: int
    recoverai_recovery_rate: float
    baseline_recovery_rate: float
    improvement_pct: float
    successful_recoveries: int
    escalations: int
    policy_stops: int
    replay_steps: List[AgentReplayStep]
    root_cause: Optional[str]
    root_cause_confidence: float
    root_cause_evidence: List[str]


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/dashboard/summary")
def get_dashboard_summary():
    """Returns hero metrics for executive dashboard overview."""
    metrics = db.get_summary_metrics()
    # Add audit log counts
    all_audits = audit_manager.get_audit_trail(limit=1000)
    policy_stops = sum(1 for a in all_audits if a.policy_decision == "DENY")
    escalations = sum(1 for a in all_audits if a.policy_decision == "ESCALATE" or a.execution_status == "ESCALATED")
    metrics["policy_stops_count"] = policy_stops
    metrics["escalations_count"] = escalations
    return metrics


@router.get("/incidents", response_model=List[Incident])
def list_incidents():
    """Returns all payment degradation incidents."""
    return db.get_incidents()


@router.post("/incidents", response_model=Incident)
def create_incident(req: CreateIncidentRequest):
    """
    Creates and injects a new synthetic payment degradation incident.
    """
    try:
        inc_type_enum = IncidentType(req.incident_type)
    except ValueError:
        inc_type_enum = IncidentType.UPI_TIMEOUT_SPIKE

    cust_list = db.get_customers()
    incident, transactions = generate_incident_scenario(
        incident_type=inc_type_enum,
        severity_pct=req.severity_pct,
        affected_count=req.affected_count,
        customers=cust_list,
        seed=req.random_seed
    )

    if req.title:
        incident.title = req.title

    db.save_incident(incident)
    for t in transactions:
        db.save_transaction(t)

    return incident


@router.get("/incidents/{incident_id}")
def get_incident_detail(incident_id: str):
    """Retrieves full incident detail, diagnosis, and performance curve."""
    inc = db.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    txs = db.get_transactions(incident_id=incident_id, limit=1000)
    failed_txs = [t for t in txs if t.status == "FAILED"]
    recovered_txs = [t for t in txs if t.status == "RECOVERED"]
    escalated_txs = [t for t in txs if t.status == "ESCALATED"]
    replay_steps = audit_manager.get_replay_steps(incident_id)

    # Generate synthetic time-series points for health chart
    health_points = [
        {"time": "T-30m", "success_rate": inc.baseline_success_rate, "state": "HEALTHY"},
        {"time": "T-20m", "success_rate": inc.baseline_success_rate - 1.2, "state": "HEALTHY"},
        {"time": "T-15m", "success_rate": inc.current_success_rate + 4.0, "state": "DEGRADING"},
        {"time": "T-10m", "success_rate": inc.current_success_rate, "state": "INCIDENT_PEAK"},
        {"time": "T-5m", "success_rate": inc.current_success_rate + (20.0 if inc.status == "RESOLVED" else 0.0), "state": "RECOVERING" if inc.status == "RESOLVED" else "CRITICAL"},
        {"time": "NOW", "success_rate": inc.baseline_success_rate if inc.status == "RESOLVED" else inc.current_success_rate, "state": "RESOLVED" if inc.status == "RESOLVED" else "ACTIVE"}
    ]

    return {
        "incident": inc,
        "health_points": health_points,
        "total_transactions": len(txs),
        "failed_count": len(failed_txs),
        "recovered_count": len(recovered_txs),
        "escalated_count": len(escalated_txs),
        "replay_steps": replay_steps
    }


@router.post("/incidents/{incident_id}/recover", response_model=RecoveryRunResponse)
def execute_incident_recovery(incident_id: str, seed: int = 42):
    """
    Executes the full RecoverAI stateful workflow AND the static baseline
    on the incident transaction batch, providing an objective comparison.
    """
    inc = db.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    txs = db.get_transactions(incident_id=incident_id, limit=2000)
    cust_list = db.get_customers()

    # 1. Run Baseline on clone
    _, base_metrics = baseline_runner.run_baseline(txs, random_seed=seed)
    inc.baseline_recovered_paise = base_metrics["recovered_paise"]

    # 2. Run RecoverAI
    updated_txs, agent_metrics = agent_workflow.run_recovery_workflow(
        incident=inc,
        transactions=txs,
        customers=cust_list,
        random_seed=seed
    )

    # Save updated transactions back to DB
    for t in updated_txs:
        db.save_transaction(t)
    db.save_incident(inc)

    replay_steps = audit_manager.get_replay_steps(incident_id)

    # Calculate metrics
    base_rec = inc.baseline_recovered_paise
    agent_rec = inc.actual_recovered_paise
    base_rate = (base_rec / inc.revenue_at_risk_paise * 100.0) if inc.revenue_at_risk_paise > 0 else 0.0
    agent_rate = (agent_rec / inc.revenue_at_risk_paise * 100.0) if inc.revenue_at_risk_paise > 0 else 0.0

    if base_rec > 0:
        improvement = ((agent_rec - base_rec) / base_rec) * 100.0
    elif agent_rec > 0:
        improvement = 100.0
    else:
        improvement = 0.0

    return RecoveryRunResponse(
        incident_id=inc.id,
        status=inc.status,
        revenue_at_risk_paise=inc.revenue_at_risk_paise,
        recoverai_recovered_paise=agent_rec,
        baseline_recovered_paise=base_rec,
        recoverai_recovery_rate=round(agent_rate, 2),
        baseline_recovery_rate=round(base_rate, 2),
        improvement_pct=round(improvement, 2),
        successful_recoveries=agent_metrics["successful_recoveries"],
        escalations=agent_metrics["actions_escalated"],
        policy_stops=agent_metrics["actions_denied"],
        replay_steps=replay_steps,
        root_cause=inc.root_cause,
        root_cause_confidence=inc.root_cause_confidence,
        root_cause_evidence=inc.root_cause_evidence
    )


@router.get("/incidents/{incident_id}/replay", response_model=List[AgentReplayStep])
def get_incident_replay(incident_id: str):
    """Returns chronological decision replay steps for an incident."""
    return audit_manager.get_replay_steps(incident_id)


@router.get("/transactions", response_model=List[Transaction])
def list_transactions(
    limit: int = 100,
    incident_id: Optional[str] = None,
    status: Optional[str] = None,
    payment_method: Optional[str] = None
):
    """Queries transactions with optional filters."""
    txs = db.get_transactions(limit=limit * 2, incident_id=incident_id)
    if status:
        txs = [t for t in txs if t.status == status]
    if payment_method:
        txs = [t for t in txs if t.payment_method == payment_method]
    return txs[:limit]


@router.get("/transactions/{transaction_id}")
def get_transaction_detail(transaction_id: str):
    """Returns single transaction record with customer profile and audit decisions."""
    tx = db.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    cust = db.customers.get(tx.customer_id)
    audits = audit_manager.get_audit_trail(transaction_id=transaction_id)
    
    return {
        "transaction": tx,
        "customer": cust,
        "audits": audits
    }


@router.get("/audit-logs", response_model=List[AuditRecord])
def get_audit_logs(
    incident_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    limit: int = 100
):
    """Queries the append-only audit trail."""
    return audit_manager.get_audit_trail(incident_id=incident_id, transaction_id=transaction_id, limit=limit)


@router.post("/evaluation/run", response_model=EvaluationSummary)
def run_evaluation_benchmark(seed: int = 42):
    """
    Executes all 7 evaluation benchmark scenarios and returns verified summary.
    """
    engine = EvaluationEngine(random_seed=seed)
    summary = engine.run_all_scenarios()
    engine.save_artifacts(summary)
    db.latest_evaluation = summary
    return summary


@router.get("/evaluation/results", response_model=EvaluationSummary)
def get_evaluation_results():
    """Returns the latest evaluation benchmark results."""
    if db.latest_evaluation:
        return db.latest_evaluation
    
    # Try reading from disk
    results_path = settings.DATA_DIR.parent / "evaluation" / "results.json"
    if results_path.exists():
        import json
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            summary = EvaluationSummary(**data)
            db.latest_evaluation = summary
            return summary
            
    # Run evaluation if no results exist yet
    return run_evaluation_benchmark()
