"""
Deterministic Policy & Guardrails Engine
Enforces non-negotiable financial constraints, retry limits, confidence floors,
and permanent failure safeguards. The AI Agent cannot bypass this engine.
All amounts are evaluated in integer paise.
"""

from typing import Set, Dict, Any, Optional
from backend.models import (
    Transaction, RecoveryActionType, PolicyDecisionType,
    PolicyValidationResult, FailureCategory, TransactionStatus
)
from backend.config import settings


class FinancialGuardrailEngine:
    """
    Deterministic validator for all proposed recovery actions.
    """
    def __init__(
        self,
        max_retries: int = settings.MAX_RETRIES,
        autonomous_limit_paise: int = settings.AUTONOMOUS_ACTION_LIMIT_PAISE,
        min_confidence: float = settings.MIN_AUTONOMOUS_CONFIDENCE
    ):
        self.max_retries = max_retries
        self.autonomous_limit_paise = autonomous_limit_paise
        self.min_confidence = min_confidence
        # Active transaction locks to prevent duplicate concurrent actions
        self._active_action_locks: Set[str] = set()

    def reset_locks(self) -> None:
        """Clears in-flight execution locks."""
        self._active_action_locks.clear()

    def validate_action(
        self,
        transaction: Transaction,
        proposed_action: RecoveryActionType,
        agent_confidence: float
    ) -> PolicyValidationResult:
        """
        Validates an agent-proposed recovery action against deterministic safety rules.
        Returns PolicyValidationResult with ALLOW, DENY, or ESCALATE.
        """
        # RULE 1: Already Settled / Success Stop Condition
        if transaction.status in (TransactionStatus.SUCCESS.value, TransactionStatus.RECOVERED.value) or transaction.is_recovered:
            return PolicyValidationResult(
                decision=PolicyDecisionType.DENY,
                reason="Transaction is already successfully settled. Further recovery stopped.",
                rule_triggered="SUCCESS_STOP_CONDITION",
                allowed_action=RecoveryActionType.NO_ACTION,
                is_safe=False
            )

        # RULE 2: Customer Decline Stop Condition
        if transaction.customer_declined:
            return PolicyValidationResult(
                decision=PolicyDecisionType.DENY,
                reason="Customer previously declined payment continuation. Recovery stopped.",
                rule_triggered="CUSTOMER_DECLINE_STOP",
                allowed_action=RecoveryActionType.NO_ACTION,
                is_safe=False
            )

        # RULE 3: Duplicate Action Protection
        if transaction.id in self._active_action_locks:
            return PolicyValidationResult(
                decision=PolicyDecisionType.DENY,
                reason=f"Active recovery action is already in-flight for transaction {transaction.id}.",
                rule_triggered="DUPLICATE_ACTION_PROTECTION",
                allowed_action=None,
                is_safe=False
            )

        # RULE 4: Permanent Failure Protection (Never blindly retry permanent declines)
        if transaction.failure_category == FailureCategory.PERMANENT.value:
            if proposed_action in (RecoveryActionType.RETRY, RecoveryActionType.WAIT_AND_RETRY):
                return PolicyValidationResult(
                    decision=PolicyDecisionType.DENY,
                    reason=f"Prohibited retry on permanent failure ({transaction.failure_reason}). Permanent declines cannot recover via retry.",
                    rule_triggered="PERMANENT_FAILURE_PROTECTION",
                    allowed_action=RecoveryActionType.NO_ACTION,
                    is_safe=False
                )

        # RULE 5: High-Value Autonomous Action Threshold (Monetary Guardrail)
        if transaction.amount_paise > self.autonomous_limit_paise:
            # Autonomous financial action prohibited above ₹50,000
            if proposed_action != RecoveryActionType.ESCALATE:
                return PolicyValidationResult(
                    decision=PolicyDecisionType.ESCALATE,
                    reason=(
                        f"Transaction amount ₹{transaction.amount_paise / 100:,.2f} exceeds "
                        f"autonomous threshold ₹{self.autonomous_limit_paise / 100:,.2f}. Mandatory human escalation."
                    ),
                    rule_triggered="HIGH_VALUE_THRESHOLD",
                    allowed_action=RecoveryActionType.ESCALATE,
                    is_safe=True
                )

        # RULE 6: Confidence Floor Guardrail
        if agent_confidence < self.min_confidence:
            if proposed_action not in (RecoveryActionType.ESCALATE, RecoveryActionType.NO_ACTION):
                return PolicyValidationResult(
                    decision=PolicyDecisionType.ESCALATE,
                    reason=(
                        f"Agent confidence ({agent_confidence:.2f}) is below minimum autonomous threshold "
                        f"({self.min_confidence:.2f}). Escalated to human operator."
                    ),
                    rule_triggered="CONFIDENCE_FLOOR",
                    allowed_action=RecoveryActionType.ESCALATE,
                    is_safe=True
                )

        # RULE 7: Retry Limit Guardrail
        if proposed_action in (RecoveryActionType.RETRY, RecoveryActionType.WAIT_AND_RETRY):
            if transaction.retry_count >= self.max_retries:
                return PolicyValidationResult(
                    decision=PolicyDecisionType.DENY,
                    reason=(
                        f"Maximum retry attempts reached ({transaction.retry_count}/{self.max_retries}). "
                        "Further automated retries blocked to prevent payment spam."
                    ),
                    rule_triggered="RETRY_LIMIT_EXCEEDED",
                    allowed_action=RecoveryActionType.NO_ACTION,
                    is_safe=False
                )

        # RULE 8: Valid Escalation
        if proposed_action == RecoveryActionType.ESCALATE:
            return PolicyValidationResult(
                decision=PolicyDecisionType.ALLOW,
                reason="Escalation proposed and approved under policy guidelines.",
                rule_triggered="EXPLICIT_ESCALATION_APPROVED",
                allowed_action=RecoveryActionType.ESCALATE,
                is_safe=True
            )

        # RULE 9: Valid No Action
        if proposed_action == RecoveryActionType.NO_ACTION:
            return PolicyValidationResult(
                decision=PolicyDecisionType.ALLOW,
                reason="No-action policy confirmed for non-recoverable transaction.",
                rule_triggered="NO_ACTION_APPROVED",
                allowed_action=RecoveryActionType.NO_ACTION,
                is_safe=True
            )

        # Approved Autonomous Action
        return PolicyValidationResult(
            decision=PolicyDecisionType.ALLOW,
            reason=f"Action {proposed_action.value} satisfies all deterministic financial guardrails.",
            rule_triggered="POLICY_APPROVED",
            allowed_action=proposed_action,
            is_safe=True
        )

    def lock_transaction(self, transaction_id: str) -> None:
        """Acquires lock for transaction."""
        self._active_action_locks.add(transaction_id)

    def unlock_transaction(self, transaction_id: str) -> None:
        """Releases lock for transaction."""
        self._active_action_locks.discard(transaction_id)
