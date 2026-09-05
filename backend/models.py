"""
RecoverAI Data Models & Enums
All monetary amounts are represented as integer paise (1 INR = 100 paise).
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"


class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RECOVERED = "RECOVERED"
    ESCALATED = "ESCALATED"
    PENDING = "PENDING"


class FailureCategory(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    CUSTOMER_ACTION_REQUIRED = "CUSTOMER_ACTION_REQUIRED"


class RecoveryActionType(str, Enum):
    RETRY = "RETRY"
    ALTERNATE_PAYMENT = "ALTERNATE_PAYMENT"
    CUSTOMER_NUDGE = "CUSTOMER_NUDGE"
    WAIT_AND_RETRY = "WAIT_AND_RETRY"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"


class PolicyDecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentType(str, Enum):
    UPI_TIMEOUT_SPIKE = "UPI_TIMEOUT_SPIKE"
    PROVIDER_OUTAGE = "PROVIDER_OUTAGE"
    BANK_SWITCH_DEGRADATION = "BANK_SWITCH_DEGRADATION"
    MIXED_FAILURE_INCIDENT = "MIXED_FAILURE_INCIDENT"
    NORMAL_TRAFFIC = "NORMAL_TRAFFIC"


class Customer(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    success_rate: float = 0.90
    payment_count: int = 10
    failure_count: int = 1
    is_high_value: bool = False


class Transaction(BaseModel):
    id: str
    merchant_id: str = "merch_razor_01"
    customer_id: str
    timestamp: str
    amount_paise: int
    currency: str = "INR"
    payment_method: str
    provider: str
    bank: str
    status: str
    failure_reason: Optional[str] = None
    failure_category: Optional[str] = None
    is_transient: bool = False
    retry_count: int = 0
    cart_value_paise: int = 0
    customer_success_rate: float = 0.90
    customer_payment_count: int = 10
    customer_failure_count: int = 1
    ground_truth_recovery_prob: float = 0.0
    is_recovered: bool = False
    recovered_amount_paise: int = 0
    incident_id: Optional[str] = None
    customer_declined: bool = False


class Incident(BaseModel):
    id: str
    title: str
    incident_type: str
    payment_method: str
    status: str = "ACTIVE"
    severity: str = "HIGH"
    severity_pct: float = 70.0
    affected_count: int = 0
    baseline_success_rate: float = 93.5
    current_success_rate: float = 68.0
    degradation_pct: float = 25.5
    total_volume_paise: int = 0
    revenue_at_risk_paise: int = 0
    estimated_recoverable_paise: int = 0
    actual_recovered_paise: int = 0
    baseline_recovered_paise: int = 0
    root_cause: Optional[str] = None
    root_cause_confidence: float = 0.0
    root_cause_evidence: List[str] = []
    created_at: str
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PolicyValidationResult(BaseModel):
    decision: PolicyDecisionType
    reason: str
    rule_triggered: str
    allowed_action: Optional[RecoveryActionType] = None
    is_safe: bool


class AgentDecision(BaseModel):
    transaction_id: str
    diagnosis: str
    action: RecoveryActionType
    confidence: float
    reasoning_summary: str
    requires_escalation: bool = False
    policy_validation: Optional[PolicyValidationResult] = None


class ToolExecutionResult(BaseModel):
    action: str
    transaction_id: str
    status: ExecutionStatus
    reason: str
    recovered_amount_paise: int = 0
    timestamp: str
    tool_metadata: Dict[str, Any] = {}


class AuditRecord(BaseModel):
    audit_id: str
    timestamp: str
    incident_id: str
    transaction_id: str
    agent_run_id: str
    proposed_action: str
    confidence: float
    policy_decision: str
    policy_reason: str
    tool_called: str
    execution_status: str
    outcome: str
    amount_paise: int
    recovered_amount_paise: int
    details: Dict[str, Any] = {}


class AgentReplayStep(BaseModel):
    step_id: str
    step_number: int
    timestamp: str
    phase: str
    title: str
    description: str
    metadata: Dict[str, Any] = {}


class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    total_transactions: int
    revenue_at_risk_paise: int
    baseline_actions: int
    baseline_recovered_paise: int
    baseline_recovery_rate: float
    recoverai_actions: int
    recoverai_recovered_paise: int
    recoverai_recovery_rate: float
    improvement_pct: float
    successful_recoveries: int
    failed_actions: int
    escalations: int
    policy_stops: int
    prohibited_retries_prevented: int
    duplicate_actions_prevented: int
    high_value_escalations: int
    invariants_passed: bool
    details: Dict[str, Any] = {}


class EvaluationSummary(BaseModel):
    dataset_size: int
    total_transaction_value_paise: int
    revenue_at_risk_paise: int
    baseline_actions: int
    baseline_recovered_paise: int
    baseline_recovery_rate: float
    recoverai_actions: int
    recoverai_recovered_paise: int
    recoverai_recovery_rate: float
    improvement_pct: float
    successful_recoveries: int
    failed_recoveries: int
    escalations: int
    policy_stops: int
    duplicate_actions_prevented: int
    prohibited_retries_prevented: int
    high_value_escalations: int
    scenarios: List[ScenarioResult] = []
    generated_at: str
    invariants_passed: bool = True
