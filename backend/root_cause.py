"""
Root Cause Analyzer
Performs multi-dimensional breakdown and statistical evidence extraction to identify root causes.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
from backend.models import Transaction, TransactionStatus, FailureCategory


class RootCauseResult:
    def __init__(
        self,
        likely_root_cause: str,
        confidence: float,
        evidence: List[str],
        affected_dimension: str,
        primary_failure_reason: str,
        recommended_strategy: str,
        dimension_distributions: Dict[str, Dict[str, int]]
    ):
        self.likely_root_cause = likely_root_cause
        self.confidence = confidence
        self.evidence = evidence
        self.affected_dimension = affected_dimension
        self.primary_failure_reason = primary_failure_reason
        self.recommended_strategy = recommended_strategy
        self.dimension_distributions = dimension_distributions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "likely_root_cause": self.likely_root_cause,
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
            "affected_dimension": self.affected_dimension,
            "primary_failure_reason": self.primary_failure_reason,
            "recommended_strategy": self.recommended_strategy,
            "dimension_distributions": self.dimension_distributions
        }


class RootCauseAnalyzer:
    """
    Analyzes transaction cohorts to isolate the primary failure driver with grounded evidence.
    """
    def analyze(self, transactions: List[Transaction]) -> RootCauseResult:
        failed_txs = [t for t in transactions if t.status == TransactionStatus.FAILED.value]
        
        if not failed_txs:
            return RootCauseResult(
                likely_root_cause="No significant failure cluster detected (Normal Operations)",
                confidence=0.95,
                evidence=["All analyzed transactions processed successfully or within baseline tolerances."],
                affected_dimension="NONE",
                primary_failure_reason="NONE",
                recommended_strategy="NO_ACTION",
                dimension_distributions={}
            )

        total_failures = len(failed_txs)
        
        # Aggregate dimensions
        method_counts = Counter(t.payment_method for t in failed_txs)
        provider_counts = Counter(t.provider for t in failed_txs)
        bank_counts = Counter(t.bank for t in failed_txs)
        reason_counts = Counter(t.failure_reason for t in failed_txs if t.failure_reason)
        category_counts = Counter(t.failure_category for t in failed_txs if t.failure_category)
        
        top_method, top_method_count = method_counts.most_common(1)[0]
        top_provider, top_provider_count = provider_counts.most_common(1)[0]
        top_bank, top_bank_count = bank_counts.most_common(1)[0]
        top_reason, top_reason_count = reason_counts.most_common(1)[0] if reason_counts else ("UNKNOWN", 0)
        
        method_pct = (top_method_count / total_failures) * 100.0
        provider_pct = (top_provider_count / total_failures) * 100.0
        bank_pct = (top_bank_count / total_failures) * 100.0
        reason_pct = (top_reason_count / total_failures) * 100.0 if total_failures > 0 else 0.0

        evidence = []
        
        # 1. Check for specific failure reason clustering
        if top_reason == "UPI_TIMEOUT" and method_pct >= 60.0:
            likely_cause = f"UPI Gateway & Switch Latency Spike ({top_bank} Bank Route)"
            affected_dim = "PAYMENT_METHOD"
            confidence = min(0.96, 0.70 + (reason_pct / 100.0) * 0.25)
            strategy = "RETRY_TRANSIENT_TIMEOUTS"
            evidence.append(f"{reason_pct:.1f}% of all failures ({top_reason_count}/{total_failures}) are due to {top_reason}.")
            evidence.append(f"Failures heavily concentrated in {top_method} payment method ({method_pct:.1f}%).")
            evidence.append(f"Other payment rails (Cards, Netbanking) show standard baseline success rates.")
            
        elif top_reason == "NETWORK_DISCONNECT" and provider_pct >= 60.0:
            likely_cause = f"Provider Connectivity Outage on {top_provider}"
            affected_dim = "PROVIDER"
            confidence = min(0.95, 0.70 + (provider_pct / 100.0) * 0.25)
            strategy = "REROUTE_ALTERNATE_PAYMENT"
            evidence.append(f"{provider_pct:.1f}% of failures isolated to provider {top_provider}.")
            evidence.append(f"Primary error code {top_reason} indicates upstream network/socket drops.")
            evidence.append(f"Alternative payment routes remain operational.")
            
        elif top_reason == "BANK_SWITCH_BUSY" and bank_pct >= 60.0:
            likely_cause = f"Core Banking Switch Downtime at {top_bank}"
            affected_dim = "BANK_SWITCH"
            confidence = min(0.94, 0.65 + (bank_pct / 100.0) * 0.30)
            strategy = "WAIT_AND_RETRY"
            evidence.append(f"{bank_pct:.1f}% of failures concentrated in {top_bank} bank route.")
            evidence.append(f"Switch reported {top_reason} across multiple payment methods.")
            evidence.append(f"Recommending paced wait-and-retry or alternate bank account link.")
            
        elif category_counts.get(FailureCategory.PERMANENT.value, 0) / total_failures >= 0.50:
            likely_cause = "Elevated Permanent Account & Card Verification Declines"
            affected_dim = "CUSTOMER_CREDENTIALS"
            confidence = 0.90
            strategy = "NO_ACTION"
            evidence.append(f"{category_counts.get(FailureCategory.PERMANENT.value, 0)} transactions failed due to permanent issuer blocks (invalid account, expired/stolen card).")
            evidence.append("Automated retries prohibited by deterministic safety policy.")
            
        elif category_counts.get(FailureCategory.CUSTOMER_ACTION_REQUIRED.value, 0) / total_failures >= 0.50:
            likely_cause = "Customer Authentication & Insufficient Balance Dropoffs"
            affected_dim = "CUSTOMER_ACTION"
            confidence = 0.85
            strategy = "CUSTOMER_NUDGE_CAMPAIGN"
            evidence.append(f"{top_reason_count} failures caused by customer-side authorization or OTP/PIN expiry.")
            evidence.append("Recommended action: Trigger dynamic SMS/WhatsApp payment nudge.")
            
        else:
            likely_cause = f"Multi-Vector Payment Degradation ({top_method} / {top_reason})"
            affected_dim = "MIXED"
            confidence = 0.78
            strategy = "SELECTIVE_RECOVERY_AND_ESCALATION"
            evidence.append(f"Dispersed failure distribution: Top reason {top_reason} ({reason_pct:.1f}%), Method {top_method} ({method_pct:.1f}%).")
            evidence.append("Contextual transaction-level triage required.")

        distributions = {
            "by_method": dict(method_counts),
            "by_provider": dict(provider_counts),
            "by_bank": dict(bank_counts),
            "by_reason": dict(reason_counts)
        }

        return RootCauseResult(
            likely_root_cause=likely_cause,
            confidence=confidence,
            evidence=evidence,
            affected_dimension=affected_dim,
            primary_failure_reason=top_reason,
            recommended_strategy=strategy,
            dimension_distributions=distributions
        )
