"""
Unit Tests for Payment Health & Anomaly Detection
"""

import pytest
from backend.detector import PaymentHealthDetector
from backend.synthetic_data import (
    generate_synthetic_customers, generate_baseline_transactions,
    generate_incident_scenario, IncidentType
)
from backend.models import Transaction, TransactionStatus, FailureCategory


def test_normal_traffic_no_anomaly():
    detector = PaymentHealthDetector(degradation_threshold_pct=15.0, z_score_threshold=2.5)
    customers = generate_synthetic_customers(50, seed=42)
    normal_batch = generate_baseline_transactions(200, customers, seed=42)
    
    result = detector.analyze_batch(normal_batch, historical_baseline_sr=93.5)
    assert not result.is_anomaly
    assert result.current_success_rate >= 88.0
    assert result.degradation_pct_points < 15.0
    assert result.severity == "NORMAL"


def test_severe_degradation_detected():
    detector = PaymentHealthDetector(degradation_threshold_pct=15.0, z_score_threshold=2.5)
    customers = generate_synthetic_customers(50, seed=42)
    incident, inc_batch = generate_incident_scenario(
        incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
        severity_pct=70.0,
        affected_count=300,
        customers=customers,
        seed=42
    )
    
    result = detector.analyze_batch(inc_batch, historical_baseline_sr=93.5)
    assert result.is_anomaly
    assert result.degradation_pct_points >= 15.0
    assert result.z_score >= 2.5
    assert result.severity in ("HIGH", "CRITICAL")
    assert result.revenue_at_risk_paise > 0
    assert result.failed_transactions_count > 0


def test_revenue_at_risk_excludes_permanent_failures():
    detector = PaymentHealthDetector()
    txs = [
        Transaction(
            id="tx_1",
            customer_id="c1",
            timestamp="2026-09-05T12:00:00",
            amount_paise=100000,  # ₹1,000
            payment_method="UPI",
            provider="RAZORPAY_DIRECT",
            bank="HDFC",
            status=TransactionStatus.FAILED.value,
            failure_reason="UPI_TIMEOUT",
            failure_category=FailureCategory.TRANSIENT.value,
            is_transient=True
        ),
        Transaction(
            id="tx_2",
            customer_id="c2",
            timestamp="2026-09-05T12:00:00",
            amount_paise=250000,  # ₹2,500
            payment_method="CARD",
            provider="ICICI_GATEWAY",
            bank="ICICI",
            status=TransactionStatus.FAILED.value,
            failure_reason="INVALID_ACCOUNT",
            failure_category=FailureCategory.PERMANENT.value,
            is_transient=False
        )
    ]
    
    result = detector.analyze_batch(txs, historical_baseline_sr=93.5)
    # Total volume: ₹3,500 (350000 paise).
    # Revenue at risk should ONLY include tx_1 (₹1,000 / 100000 paise), excluding permanent failure tx_2!
    assert result.total_volume_paise == 350000
    assert result.revenue_at_risk_paise == 100000
