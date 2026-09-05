"""
Payment Health & Revenue Risk Detector
Statistical anomaly detection and revenue-at-risk calculation.
All monetary calculations are performed in integer paise.
"""

from typing import List, Dict, Any, Optional
import math
from backend.models import Transaction, TransactionStatus, FailureCategory
from backend.config import settings


class AnomalyDetectionResult:
    def __init__(
        self,
        is_anomaly: bool,
        baseline_success_rate: float,
        current_success_rate: float,
        degradation_pct_points: float,
        z_score: float,
        total_transactions: int,
        failed_transactions_count: int,
        total_volume_paise: int,
        revenue_at_risk_paise: int,
        estimated_recoverable_paise: int,
        severity: str,
        detection_summary: str,
        method_breakdown: Dict[str, Dict[str, Any]]
    ):
        self.is_anomaly = is_anomaly
        self.baseline_success_rate = baseline_success_rate
        self.current_success_rate = current_success_rate
        self.degradation_pct_points = degradation_pct_points
        self.z_score = z_score
        self.total_transactions = total_transactions
        self.failed_transactions_count = failed_transactions_count
        self.total_volume_paise = total_volume_paise
        self.revenue_at_risk_paise = revenue_at_risk_paise
        self.estimated_recoverable_paise = estimated_recoverable_paise
        self.severity = severity
        self.detection_summary = detection_summary
        self.method_breakdown = method_breakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "baseline_success_rate": round(self.baseline_success_rate, 2),
            "current_success_rate": round(self.current_success_rate, 2),
            "degradation_pct_points": round(self.degradation_pct_points, 2),
            "z_score": round(self.z_score, 2),
            "total_transactions": self.total_transactions,
            "failed_transactions_count": self.failed_transactions_count,
            "total_volume_paise": self.total_volume_paise,
            "revenue_at_risk_paise": self.revenue_at_risk_paise,
            "estimated_recoverable_paise": self.estimated_recoverable_paise,
            "severity": self.severity,
            "detection_summary": self.detection_summary,
            "method_breakdown": self.method_breakdown
        }


class PaymentHealthDetector:
    """
    Deterministic statistical detector that monitors success rates and quantifies revenue risk.
    """
    def __init__(
        self,
        degradation_threshold_pct: float = settings.DEGRADATION_THRESHOLD_PCT,
        z_score_threshold: float = settings.Z_SCORE_THRESHOLD
    ):
        self.degradation_threshold_pct = degradation_threshold_pct
        self.z_score_threshold = z_score_threshold

    def analyze_batch(
        self,
        current_batch: List[Transaction],
        historical_baseline_sr: float = 93.5,
        historical_std_dev: float = 2.0
    ) -> AnomalyDetectionResult:
        """
        Analyzes a batch of transactions against baseline payment health.
        """
        if not current_batch:
            return AnomalyDetectionResult(
                is_anomaly=False,
                baseline_success_rate=historical_baseline_sr,
                current_success_rate=historical_baseline_sr,
                degradation_pct_points=0.0,
                z_score=0.0,
                total_transactions=0,
                failed_transactions_count=0,
                total_volume_paise=0,
                revenue_at_risk_paise=0,
                estimated_recoverable_paise=0,
                severity="NORMAL",
                detection_summary="No transaction data in current analysis window.",
                method_breakdown={}
            )

        total_txs = len(current_batch)
        successful_txs = [t for t in current_batch if t.status in (TransactionStatus.SUCCESS.value, TransactionStatus.RECOVERED.value)]
        failed_txs = [t for t in current_batch if t.status == TransactionStatus.FAILED.value]
        
        current_sr = (len(successful_txs) / total_txs) * 100.0
        degradation = max(0.0, historical_baseline_sr - current_sr)
        
        # Calculate standard normal z-score for binomial success rate
        p0 = historical_baseline_sr / 100.0
        p_hat = current_sr / 100.0
        se = math.sqrt((p0 * (1.0 - p0)) / total_txs) if total_txs > 0 else 0.01
        z_score = (p0 - p_hat) / se if se > 0 else 0.0
        
        is_anomaly = (degradation >= self.degradation_threshold_pct) or (z_score >= self.z_score_threshold)
        
        # Financial exposure calculations
        total_volume_paise = sum(t.amount_paise for t in current_batch)
        
        # Revenue at risk: Unsuccessful transactions with plausible recovery path
        # (Excludes permanent failures like invalid accounts or closed banks which are unrecoverable by definition)
        revenue_at_risk_paise = sum(
            t.amount_paise for t in failed_txs
            if t.failure_category != FailureCategory.PERMANENT.value
        )
        
        # Estimated recoverable value based on ground-truth recovery expectation
        estimated_recoverable_paise = int(sum(
            t.amount_paise * t.ground_truth_recovery_prob for t in failed_txs
        ))

        # Severity classification
        if degradation >= 30.0 or z_score >= 8.0:
            severity = "CRITICAL"
        elif degradation >= 20.0 or z_score >= 5.0:
            severity = "HIGH"
        elif degradation >= 10.0 or z_score >= 2.5:
            severity = "MEDIUM"
        elif is_anomaly:
            severity = "LOW"
        else:
            severity = "NORMAL"

        # Breakdown by payment method
        method_breakdown: Dict[str, Dict[str, Any]] = {}
        for method in set(t.payment_method for t in current_batch):
            method_txs = [t for t in current_batch if t.payment_method == method]
            m_success = sum(1 for t in method_txs if t.status in (TransactionStatus.SUCCESS.value, TransactionStatus.RECOVERED.value))
            m_failed = sum(1 for t in method_txs if t.status == TransactionStatus.FAILED.value)
            m_total = len(method_txs)
            m_sr = (m_success / m_total * 100.0) if m_total > 0 else 0.0
            m_at_risk = sum(t.amount_paise for t in method_txs if t.status == TransactionStatus.FAILED.value and t.failure_category != FailureCategory.PERMANENT.value)
            
            method_breakdown[method] = {
                "total": m_total,
                "successful": m_success,
                "failed": m_failed,
                "success_rate": round(m_sr, 2),
                "revenue_at_risk_paise": m_at_risk
            }

        # Summary text
        if is_anomaly:
            summary = (
                f"Abnormal payment degradation detected: Success rate dropped by {degradation:.1f}% "
                f"(Baseline: {historical_baseline_sr:.1f}% -> Current: {current_sr:.1f}% | Z-score: {z_score:.2f}). "
                f"{len(failed_txs)} failed transactions detected with ₹{revenue_at_risk_paise / 100:,.2f} revenue at risk."
            )
        else:
            summary = (
                f"Payment health is within normal operational bounds (Current: {current_sr:.1f}% vs Baseline: {historical_baseline_sr:.1f}%)."
            )

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            baseline_success_rate=historical_baseline_sr,
            current_success_rate=current_sr,
            degradation_pct_points=degradation,
            z_score=z_score,
            total_transactions=total_txs,
            failed_transactions_count=len(failed_txs),
            total_volume_paise=total_volume_paise,
            revenue_at_risk_paise=revenue_at_risk_paise,
            estimated_recoverable_paise=estimated_recoverable_paise,
            severity=severity,
            detection_summary=summary,
            method_breakdown=method_breakdown
        )
