"""
Controlled Recovery Tools
Implements strictly bounded, simulated recovery actions.
Never fabricates success without simulator confirmation.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.models import (
    Transaction, Customer, ToolExecutionResult,
    ExecutionStatus, TransactionStatus
)


class RecoveryTools:
    """
    Simulated tool suite for executing approved recovery actions.
    """
    def __init__(
        self,
        transactions_map: Dict[str, Transaction],
        customers_map: Dict[str, Customer],
        random_seed: Optional[int] = None
    ):
        self.transactions_map = transactions_map
        self.customers_map = customers_map
        self.rng = random.Random(random_seed) if random_seed is not None else random.Random()

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves structured transaction context."""
        tx = self.transactions_map.get(transaction_id)
        return tx.model_dump() if tx else None

    def get_customer_history(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves customer payment track record."""
        cust = self.customers_map.get(customer_id)
        return cust.model_dump() if cust else None

    def get_payment_health(self) -> Dict[str, Any]:
        """Calculates current aggregate health across known transactions."""
        txs = list(self.transactions_map.values())
        if not txs:
            return {"total": 0, "success_rate": 100.0}
        success_count = sum(1 for t in txs if t.status in (TransactionStatus.SUCCESS.value, TransactionStatus.RECOVERED.value))
        return {
            "total_transactions": len(txs),
            "successful_count": success_count,
            "failed_count": len(txs) - success_count,
            "success_rate": round((success_count / len(txs)) * 100.0, 2)
        }

    def retry_payment(self, transaction_id: str) -> ToolExecutionResult:
        """
        Executes an automated payment retry on the primary route.
        Direct retries succeed on transient timeouts, but fail if the provider is down,
        if customer authentication is missing, or on permanent declines.
        """
        now_str = datetime.now().isoformat()
        tx = self.transactions_map.get(transaction_id)
        if not tx:
            return ToolExecutionResult(
                action="retry_payment",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason=f"Transaction {transaction_id} not found in environment.",
                recovered_amount_paise=0,
                timestamp=now_str
            )

        # Increment retry count
        tx.retry_count += 1
        
        # Calculate realistic success probability based on failure mechanism
        if tx.failure_category == "PERMANENT":
            success_prob = 0.0
        elif tx.failure_category == "CUSTOMER_ACTION_REQUIRED":
            # Direct retry without customer present fails
            success_prob = 0.05
        elif tx.failure_reason == "NETWORK_DISCONNECT":
            # Direct retry to same downed provider fails
            success_prob = 0.10
        elif tx.retry_count > 2:
            success_prob = 0.0
        else:
            # Transient timeout on operational route
            success_prob = max(0.60, tx.ground_truth_recovery_prob)
            
        is_success = self.rng.random() < success_prob
        
        if is_success:
            tx.status = TransactionStatus.RECOVERED.value
            tx.is_recovered = True
            tx.recovered_amount_paise = tx.amount_paise
            return ToolExecutionResult(
                action="retry_payment",
                transaction_id=transaction_id,
                status=ExecutionStatus.SUCCESS,
                reason="Payment retry succeeded at provider switch. Funds captured.",
                recovered_amount_paise=tx.amount_paise,
                timestamp=now_str,
                tool_metadata={
                    "gateway_response": "200_CAPTURE_SUCCESS",
                    "auth_code": f"AUTH_{self.rng.randint(100000, 999999)}"
                }
            )
        else:
            return ToolExecutionResult(
                action="retry_payment",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason=f"Payment retry failed at switch ({tx.failure_reason or 'TIMEOUT'}).",
                recovered_amount_paise=0,
                timestamp=now_str,
                tool_metadata={
                    "gateway_response": "504_GATEWAY_TIMEOUT",
                    "retry_count": tx.retry_count
                }
            )

    def create_alternate_payment_link(self, transaction_id: str) -> ToolExecutionResult:
        """
        Creates an alternate payment pathway (e.g. Card/Netbanking fallback when UPI/Provider is degraded).
        Bypasses broken provider switches.
        """
        now_str = datetime.now().isoformat()
        tx = self.transactions_map.get(transaction_id)
        if not tx:
            return ToolExecutionResult(
                action="create_alternate_payment_link",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason=f"Transaction {transaction_id} not found.",
                recovered_amount_paise=0,
                timestamp=now_str
            )

        if tx.failure_category == "PERMANENT":
            conversion_prob = 0.0
        else:
            # Alternate link successfully reroutes around degraded provider/method
            base_prob = 0.85 if tx.customer_success_rate >= 0.70 else 0.65
            conversion_prob = base_prob

        is_success = self.rng.random() < conversion_prob
        
        if is_success:
            tx.status = TransactionStatus.RECOVERED.value
            tx.is_recovered = True
            tx.recovered_amount_paise = tx.amount_paise
            return ToolExecutionResult(
                action="create_alternate_payment_link",
                transaction_id=transaction_id,
                status=ExecutionStatus.SUCCESS,
                reason="Customer completed checkout via alternate payment route.",
                recovered_amount_paise=tx.amount_paise,
                timestamp=now_str,
                tool_metadata={
                    "payment_link_id": f"plink_{self.rng.randint(10000, 99999)}",
                    "alternate_method": "CARD" if tx.payment_method == "UPI" else "UPI"
                }
            )
        else:
            return ToolExecutionResult(
                action="create_alternate_payment_link",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason="Alternate payment link created but customer session timed out.",
                recovered_amount_paise=0,
                timestamp=now_str,
                tool_metadata={"payment_link_id": f"plink_{self.rng.randint(10000, 99999)}"}
            )

    def send_customer_notification(self, transaction_id: str, message_type: str = "PAYMENT_NUDGE") -> ToolExecutionResult:
        """
        Dispatches a customer recovery notification / push nudge for auth dropoffs and balance retries.
        """
        now_str = datetime.now().isoformat()
        tx = self.transactions_map.get(transaction_id)
        if not tx:
            return ToolExecutionResult(
                action="send_customer_notification",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason=f"Transaction {transaction_id} not found.",
                recovered_amount_paise=0,
                timestamp=now_str
            )

        if tx.failure_category == "PERMANENT":
            nudge_prob = 0.0
        elif tx.failure_category == "CUSTOMER_ACTION_REQUIRED":
            nudge_prob = 0.72 if tx.customer_success_rate >= 0.75 else 0.45
        else:
            nudge_prob = 0.60

        is_success = self.rng.random() < nudge_prob
        
        if is_success:
            tx.status = TransactionStatus.RECOVERED.value
            tx.is_recovered = True
            tx.recovered_amount_paise = tx.amount_paise
            return ToolExecutionResult(
                action="send_customer_notification",
                transaction_id=transaction_id,
                status=ExecutionStatus.SUCCESS,
                reason="Customer responded to nudge and authorized payment capture.",
                recovered_amount_paise=tx.amount_paise,
                timestamp=now_str,
                tool_metadata={"channel": "WHATSAPP_SMS", "message_type": message_type}
            )
        else:
            return ToolExecutionResult(
                action="send_customer_notification",
                transaction_id=transaction_id,
                status=ExecutionStatus.FAILURE,
                reason="Customer notification delivered but authorization was not received.",
                recovered_amount_paise=0,
                timestamp=now_str,
                tool_metadata={"channel": "WHATSAPP_SMS", "delivery_status": "DELIVERED"}
            )

    def escalate_case(self, transaction_id: str, reason: str) -> ToolExecutionResult:
        """
        Routes transaction to human merchant ops case queue.
        """
        now_str = datetime.now().isoformat()
        tx = self.transactions_map.get(transaction_id)
        if tx:
            tx.status = TransactionStatus.ESCALATED.value
            
        return ToolExecutionResult(
            action="escalate_case",
            transaction_id=transaction_id,
            status=ExecutionStatus.ESCALATED,
            reason=f"Escalation queued for human operator: {reason}",
            recovered_amount_paise=0,
            timestamp=now_str,
            tool_metadata={"case_priority": "P1" if tx and tx.amount_paise > 5000000 else "P2"}
        )
