"""
Stateful Recovery Agent Workflow Engine
Orchestrates the entire recovery lifecycle:
DETECT -> DIAGNOSE -> IDENTIFY_AFFECTED_TRANSACTIONS -> PLAN -> VALIDATE_POLICY -> EXECUTE -> VERIFY -> MEASURE -> COMPLETE.
Strictly separates AI decision proposal from deterministic guardrail validation and execution.
"""

from typing import List, Dict, Any, Tuple, Optional
import uuid
import copy
from datetime import datetime
from backend.models import (
    Transaction, Customer, Incident, AgentDecision, RecoveryActionType,
    PolicyDecisionType, ExecutionStatus, TransactionStatus, FailureCategory
)
from backend.detector import PaymentHealthDetector, AnomalyDetectionResult
from backend.root_cause import RootCauseAnalyzer, RootCauseResult
from backend.guardrails import FinancialGuardrailEngine
from backend.tools import RecoveryTools
from backend.audit import audit_manager, AuditTrailManager
from backend.config import settings
from backend.llm import GroqLLMClient, groq_llm_client


class RecoveryAgentWorkflow:
    """
    Autonomous stateful recovery agent operating under deterministic financial guardrails.
    """
    def __init__(
        self,
        guardrail_engine: Optional[FinancialGuardrailEngine] = None,
        audit_logger: Optional[AuditTrailManager] = None,
        llm_client: Optional[GroqLLMClient] = None
    ):
        self.guardrails = guardrail_engine or FinancialGuardrailEngine()
        self.audit_logger = audit_logger or audit_manager
        self.detector = PaymentHealthDetector()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.llm = llm_client or groq_llm_client

    def _generate_candidate_decision(
        self,
        tx: Transaction,
        cust: Optional[Customer],
        root_cause_info: RootCauseResult
    ) -> AgentDecision:
        """
        Contextual decision proposal model.
        Evaluates transaction context, customer history, and root cause evidence via GroqCloud LLM or deterministic fallback.
        """
        return self.llm.propose_candidate_decision(
            tx=tx,
            cust=cust,
            root_cause_info=root_cause_info,
            autonomous_limit_paise=self.guardrails.autonomous_limit_paise
        )

    def run_recovery_workflow(
        self,
        incident: Incident,
        transactions: List[Transaction],
        customers: Optional[List[Customer]] = None,
        random_seed: int = 42
    ) -> Tuple[List[Transaction], Dict[str, Any]]:
        """
        Executes the complete RecoverAI workflow on the incident transaction cohort.
        Returns (updated_transactions, recovery_metrics).
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        batch_copy = [copy.deepcopy(t) for t in transactions]
        tx_map = {t.id: t for t in batch_copy}
        cust_map = {c.id: c for c in customers} if customers else {}
        
        tools = RecoveryTools(tx_map, cust_map, random_seed=random_seed)
        self.guardrails.reset_locks()

        # PHASE 1: DETECT
        self.audit_logger.add_replay_step(
            incident_id=incident.id,
            phase="DETECT",
            title="Revenue Risk & Degradation Detected",
            description=(
                f"Statistical anomaly detected on {incident.payment_method} channel. "
                f"Success rate dropped by {incident.degradation_pct:.1f}% "
                f"(Baseline: {incident.baseline_success_rate:.1f}% -> Current: {incident.current_success_rate:.1f}%). "
                f"Identified ₹{incident.revenue_at_risk_paise / 100:,.2f} revenue exposure."
            ),
            metadata={
                "degradation_pct": incident.degradation_pct,
                "revenue_at_risk_paise": incident.revenue_at_risk_paise,
                "affected_count": incident.affected_count
            }
        )

        # PHASE 2: DIAGNOSE
        root_cause_result = self.root_cause_analyzer.analyze(batch_copy)
        incident.root_cause = root_cause_result.likely_root_cause
        incident.root_cause_confidence = root_cause_result.confidence
        incident.root_cause_evidence = root_cause_result.evidence
        
        self.audit_logger.add_replay_step(
            incident_id=incident.id,
            phase="DIAGNOSE",
            title="Root Cause Diagnosed",
            description=(
                f"Identified primary driver: '{root_cause_result.likely_root_cause}' "
                f"with {root_cause_result.confidence * 100:.0f}% confidence. "
                f"Recommended strategy: {root_cause_result.recommended_strategy}."
            ),
            metadata={
                "likely_root_cause": root_cause_result.likely_root_cause,
                "confidence": root_cause_result.confidence,
                "evidence": root_cause_result.evidence,
                "affected_dimension": root_cause_result.affected_dimension
            }
        )

        # PHASE 3: IDENTIFY_AFFECTED_TRANSACTIONS
        failed_txs = [t for t in batch_copy if t.status == TransactionStatus.FAILED.value]
        recoverable_candidates = [
            t for t in failed_txs 
            if t.failure_category != FailureCategory.PERMANENT.value
        ]
        
        self.audit_logger.add_replay_step(
            incident_id=incident.id,
            phase="IDENTIFY_AFFECTED_TRANSACTIONS",
            title="Affected Cohort Classified",
            description=(
                f"Segmented {len(failed_txs)} failed payments: {len(recoverable_candidates)} candidate recoverable transactions, "
                f"{len(failed_txs) - len(recoverable_candidates)} permanent failures."
            ),
            metadata={
                "total_failed": len(failed_txs),
                "recoverable_candidates": len(recoverable_candidates)
            }
        )

        # PHASE 4-8: PLAN -> VALIDATE_POLICY -> EXECUTE -> VERIFY -> MEASURE
        total_actions_proposed = 0
        actions_allowed = 0
        actions_denied = 0
        actions_escalated = 0
        successful_recoveries = 0
        failed_actions = 0
        total_recovered_paise = 0
        prohibited_retries_prevented = 0
        duplicate_prevented = 0
        high_value_escalations = 0

        for tx in failed_txs:
            cust = cust_map.get(tx.customer_id)
            
            # STEP A: AGENT PROPOSES ACTION
            decision = self._generate_candidate_decision(tx, cust, root_cause_result)
            total_actions_proposed += 1
            
            # STEP B: POLICY ENGINE VALIDATES
            policy_val = self.guardrails.validate_action(
                transaction=tx,
                proposed_action=decision.action,
                agent_confidence=decision.confidence
            )
            decision.policy_validation = policy_val

            # Track guardrail metrics
            if policy_val.rule_triggered == "PERMANENT_FAILURE_PROTECTION":
                prohibited_retries_prevented += 1
            elif policy_val.rule_triggered == "RETRY_LIMIT_EXCEEDED":
                prohibited_retries_prevented += 1
            elif policy_val.rule_triggered == "HIGH_VALUE_THRESHOLD":
                high_value_escalations += 1
            elif policy_val.rule_triggered == "DUPLICATE_ACTION_PROTECTION":
                duplicate_prevented += 1

            # STEP C: EXECUTION BOUNDARY
            tool_name = "NONE"
            exec_status = "SKIPPED"
            outcome_desc = policy_val.reason
            recovered_amount = 0

            if policy_val.decision == PolicyDecisionType.ALLOW:
                actions_allowed += 1
                self.guardrails.lock_transaction(tx.id)
                
                # Call respective controlled tool
                if policy_val.allowed_action == RecoveryActionType.RETRY:
                    tool_name = "retry_payment"
                    res = tools.retry_payment(tx.id)
                elif policy_val.allowed_action == RecoveryActionType.ALTERNATE_PAYMENT:
                    tool_name = "create_alternate_payment_link"
                    res = tools.create_alternate_payment_link(tx.id)
                elif policy_val.allowed_action == RecoveryActionType.CUSTOMER_NUDGE:
                    tool_name = "send_customer_notification"
                    res = tools.send_customer_notification(tx.id, message_type="RECOVERY_NUDGE")
                elif policy_val.allowed_action == RecoveryActionType.WAIT_AND_RETRY:
                    tool_name = "retry_payment"
                    res = tools.retry_payment(tx.id)
                elif policy_val.allowed_action == RecoveryActionType.ESCALATE:
                    tool_name = "escalate_case"
                    res = tools.escalate_case(tx.id, reason=decision.reasoning_summary)
                else:  # NO_ACTION
                    tool_name = "no_op"
                    res = None

                self.guardrails.unlock_transaction(tx.id)

                if res:
                    exec_status = res.status.value
                    outcome_desc = res.reason
                    recovered_amount = res.recovered_amount_paise
                    
                    if res.status == ExecutionStatus.SUCCESS:
                        successful_recoveries += 1
                        total_recovered_paise += recovered_amount
                    elif res.status == ExecutionStatus.ESCALATED:
                        actions_escalated += 1
                    else:
                        failed_actions += 1

            elif policy_val.decision == PolicyDecisionType.ESCALATE:
                actions_escalated += 1
                tool_name = "escalate_case"
                res = tools.escalate_case(tx.id, reason=policy_val.reason)
                exec_status = ExecutionStatus.ESCALATED.value
                outcome_desc = f"Policy Escalation: {policy_val.reason}"

            else:  # DENY
                actions_denied += 1
                tool_name = "BLOCKED_BY_POLICY"
                exec_status = ExecutionStatus.BLOCKED.value
                outcome_desc = f"Policy Block: {policy_val.reason}"

            # STEP D: APPEND TO AUDIT TRAIL
            self.audit_logger.record_audit(
                incident_id=incident.id,
                transaction_id=tx.id,
                agent_run_id=run_id,
                proposed_action=decision.action.value,
                confidence=decision.confidence,
                policy_decision=policy_val.decision.value,
                policy_reason=policy_val.reason,
                tool_called=tool_name,
                execution_status=exec_status,
                outcome=outcome_desc,
                amount_paise=tx.amount_paise,
                recovered_amount_paise=recovered_amount,
                details={
                    "customer_id": tx.customer_id,
                    "failure_reason": tx.failure_reason,
                    "payment_method": tx.payment_method,
                    "rule_triggered": policy_val.rule_triggered
                }
            )

        # PHASE 9: COMPLETE & SUMMARY REPLAY MILESTONE
        incident.actual_recovered_paise = total_recovered_paise
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.now().isoformat()
        
        recovery_rate = (total_recovered_paise / incident.revenue_at_risk_paise * 100.0) if incident.revenue_at_risk_paise > 0 else 0.0

        self.audit_logger.add_replay_step(
            incident_id=incident.id,
            phase="MEASURE",
            title="Recovery Execution & Verification Completed",
            description=(
                f"Successfully recovered ₹{total_recovered_paise / 100:,.2f} ({recovery_rate:.1f}% recovery rate) "
                f"across {successful_recoveries} recovered payments. "
                f"Policy Engine enforced {actions_denied} policy blocks and {actions_escalated} compliant escalations."
            ),
            metadata={
                "total_recovered_paise": total_recovered_paise,
                "successful_recoveries": successful_recoveries,
                "actions_escalated": actions_escalated,
                "actions_denied": actions_denied,
                "recovery_rate": round(recovery_rate, 2)
            }
        )

        metrics = {
            "strategy": "RECOVER_AI",
            "run_id": run_id,
            "incident_id": incident.id,
            "total_transactions": len(batch_copy),
            "failed_transactions": len(failed_txs),
            "revenue_at_risk_paise": incident.revenue_at_risk_paise,
            "total_recovered_paise": total_recovered_paise,
            "recovery_rate": round(recovery_rate, 2),
            "actions_proposed": total_actions_proposed,
            "actions_allowed": actions_allowed,
            "actions_denied": actions_denied,
            "actions_escalated": actions_escalated,
            "successful_recoveries": successful_recoveries,
            "failed_actions": failed_actions,
            "prohibited_retries_prevented": prohibited_retries_prevented,
            "duplicate_prevented": duplicate_prevented,
            "high_value_escalations": high_value_escalations
        }

        return batch_copy, metrics
