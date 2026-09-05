"""
Static Baseline Recovery Engine
A deterministic, rule-based baseline against which RecoverAI is objectively evaluated.
Rule: IF failure is transient AND retry_count < 1 THEN retry once ELSE no recovery.
"""

from typing import List, Dict, Tuple, Any
import copy
from backend.models import Transaction, TransactionStatus, FailureCategory
from backend.tools import RecoveryTools


class StaticBaselineRunner:
    """
    Executes the static baseline strategy on a transaction batch.
    """
    def run_baseline(
        self,
        transactions: List[Transaction],
        random_seed: int = 42
    ) -> Tuple[List[Transaction], Dict[str, Any]]:
        """
        Runs static single-retry baseline on a cloned batch of transactions.
        Returns (updated_transactions, baseline_metrics).
        """
        # Deep clone transactions so we don't mutate input
        batch_copy = [copy.deepcopy(t) for t in transactions]
        tx_map = {t.id: t for t in batch_copy}
        tools = RecoveryTools(tx_map, {}, random_seed=random_seed)
        
        attempted_actions = 0
        successful_actions = 0
        failed_actions = 0
        recovered_paise = 0
        
        failed_txs = [t for t in batch_copy if t.status == TransactionStatus.FAILED.value]
        
        # Calculate revenue at risk across all recoverable categories
        revenue_at_risk_paise = sum(
            t.amount_paise for t in failed_txs
            if t.failure_category != FailureCategory.PERMANENT.value
        )
        
        for tx in failed_txs:
            # Baseline rule: Only retry if classified as transient AND not previously retried
            if tx.failure_category == FailureCategory.TRANSIENT.value and tx.retry_count < 1:
                attempted_actions += 1
                res = tools.retry_payment(tx.id)
                if res.status.value == "SUCCESS":
                    successful_actions += 1
                    recovered_paise += res.recovered_amount_paise
                else:
                    failed_actions += 1
            else:
                # No recovery attempted by baseline
                pass

        recovery_rate = (recovered_paise / revenue_at_risk_paise * 100.0) if revenue_at_risk_paise > 0 else 0.0

        metrics = {
            "strategy": "STATIC_BASELINE",
            "attempted_actions": attempted_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "revenue_at_risk_paise": revenue_at_risk_paise,
            "recovered_paise": recovered_paise,
            "recovery_rate": round(recovery_rate, 2),
            "escalations": 0,
            "policy_stops": 0
        }
        
        return batch_copy, metrics
