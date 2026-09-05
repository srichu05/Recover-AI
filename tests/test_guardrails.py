"""
Unit Tests for Deterministic Policy & Financial Guardrails
"""

import pytest
from backend.guardrails import FinancialGuardrailEngine
from backend.models import (
    Transaction, RecoveryActionType, PolicyDecisionType,
    TransactionStatus, FailureCategory
)


@pytest.fixture
def guardrails():
    engine = FinancialGuardrailEngine(
        max_retries=2,
        autonomous_limit_paise=5000000,  # ₹50,000
        min_confidence=0.80
    )
    engine.reset_locks()
    return engine


def test_retry_limit_enforced(guardrails):
    tx = Transaction(
        id="tx_retry_limit",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=249900,  # ₹2,499
        payment_method="UPI",
        provider="RAZORPAY_DIRECT",
        bank="HDFC",
        status=TransactionStatus.FAILED.value,
        failure_reason="UPI_TIMEOUT",
        failure_category=FailureCategory.TRANSIENT.value,
        retry_count=2,  # Maximum reached
        is_transient=True
    )
    
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.95)
    assert val.decision == PolicyDecisionType.DENY
    assert val.rule_triggered == "RETRY_LIMIT_EXCEEDED"
    assert not val.is_safe


def test_monetary_threshold_escalates_high_value(guardrails):
    tx = Transaction(
        id="tx_high_val",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=7500000,  # ₹75,000 (> ₹50,000 limit)
        payment_method="UPI",
        provider="RAZORPAY_DIRECT",
        bank="HDFC",
        status=TransactionStatus.FAILED.value,
        failure_reason="UPI_TIMEOUT",
        failure_category=FailureCategory.TRANSIENT.value,
        retry_count=0,
        is_transient=True
    )
    
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.95)
    assert val.decision == PolicyDecisionType.ESCALATE
    assert val.rule_triggered == "HIGH_VALUE_THRESHOLD"
    assert val.allowed_action == RecoveryActionType.ESCALATE


def test_low_confidence_escalates(guardrails):
    tx = Transaction(
        id="tx_low_conf",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=150000,  # ₹1,500
        payment_method="UPI",
        provider="RAZORPAY_DIRECT",
        bank="HDFC",
        status=TransactionStatus.FAILED.value,
        failure_reason="UNKNOWN_CODE_99",
        failure_category=FailureCategory.TRANSIENT.value,
        retry_count=0,
        is_transient=True
    )
    
    # Confidence is 0.65 (< 0.80 floor)
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.65)
    assert val.decision == PolicyDecisionType.ESCALATE
    assert val.rule_triggered == "CONFIDENCE_FLOOR"
    assert val.allowed_action == RecoveryActionType.ESCALATE


def test_permanent_failure_retry_denied(guardrails):
    tx = Transaction(
        id="tx_perm",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=150000,
        payment_method="CARD",
        provider="ICICI_GATEWAY",
        bank="ICICI",
        status=TransactionStatus.FAILED.value,
        failure_reason="STOLEN_OR_BLOCKED_CARD",
        failure_category=FailureCategory.PERMANENT.value,
        retry_count=0,
        is_transient=False
    )
    
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.90)
    assert val.decision == PolicyDecisionType.DENY
    assert val.rule_triggered == "PERMANENT_FAILURE_PROTECTION"


def test_duplicate_action_lock_protection(guardrails):
    tx = Transaction(
        id="tx_duplicate_lock",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=150000,
        payment_method="UPI",
        provider="RAZORPAY_DIRECT",
        bank="HDFC",
        status=TransactionStatus.FAILED.value,
        failure_reason="UPI_TIMEOUT",
        failure_category=FailureCategory.TRANSIENT.value,
        retry_count=0,
        is_transient=True
    )
    
    # Lock the transaction
    guardrails.lock_transaction(tx.id)
    
    # Attempt second simultaneous recovery action
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.95)
    assert val.decision == PolicyDecisionType.DENY
    assert val.rule_triggered == "DUPLICATE_ACTION_PROTECTION"
    
    # Unlock and verify permitted
    guardrails.unlock_transaction(tx.id)
    val2 = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.95)
    assert val2.decision == PolicyDecisionType.ALLOW


def test_success_stop_condition(guardrails):
    tx = Transaction(
        id="tx_already_success",
        customer_id="c1",
        timestamp="2026-09-05T12:00:00",
        amount_paise=150000,
        payment_method="UPI",
        provider="RAZORPAY_DIRECT",
        bank="HDFC",
        status=TransactionStatus.RECOVERED.value,
        is_recovered=True,
        recovered_amount_paise=150000
    )
    
    val = guardrails.validate_action(tx, RecoveryActionType.RETRY, agent_confidence=0.95)
    assert val.decision == PolicyDecisionType.DENY
    assert val.rule_triggered == "SUCCESS_STOP_CONDITION"
