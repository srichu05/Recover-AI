"""
GroqCloud LLM Integration Module for RecoverAI
Uses the standard OpenAI SDK configured with GroqCloud API endpoint:
Base URL: https://api.groq.com/openai/v1
Model: openai/gpt-oss-120b (or configured GROQ_MODEL)
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel, Field

from backend.config import settings
from backend.models import (
    Transaction, Customer, AgentDecision, RecoveryActionType, FailureCategory
)
from backend.root_cause import RootCauseResult

logger = logging.getLogger("recoverai.llm")

# Tool definitions in standard OpenAI/Groq function calling format
RECOVERY_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "retry_payment",
            "description": "Trigger an immediate or scheduled smart retry on the same payment rail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Unique transaction identifier."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for retry (e.g. transient gateway timeout)."
                    }
                },
                "required": ["transaction_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_alternate_payment_link",
            "description": "Generate an alternate payment link on a secondary healthy payment rail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Unique transaction identifier."
                    },
                    "suggested_rail": {
                        "type": "string",
                        "enum": ["CARD", "NETBANKING", "UPI"],
                        "description": "Alternate healthy payment method."
                    }
                },
                "required": ["transaction_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_customer_notification",
            "description": "Send an interactive WhatsApp/SMS nudge to customer for authentication/OTP re-entry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Unique transaction identifier."
                    },
                    "channel": {
                        "type": "string",
                        "enum": ["WHATSAPP", "SMS"],
                        "description": "Notification delivery channel."
                    }
                },
                "required": ["transaction_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_case",
            "description": "Escalate high-value transaction or ambiguous failure to human operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Unique transaction identifier."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Detailed escalation justification."
                    }
                },
                "required": ["transaction_id", "reason"]
            }
        }
    }
]


class DecisionResponseSchema(BaseModel):
    action: str = Field(description="One of: RETRY, ALTERNATE_PAYMENT, CUSTOMER_NUDGE, WAIT_AND_RETRY, ESCALATE, NO_ACTION")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    diagnosis: str = Field(description="Short diagnostic explanation")
    reasoning_summary: str = Field(description="Detailed step-by-step reasoning for the proposed recovery")
    requires_escalation: bool = Field(description="True if transaction exceeds autonomous limits or requires human review")


class GroqLLMClient:
    """
    GroqCloud LLM Client configured via OpenAI SDK compatibility.
    Falls back to deterministic contextual reasoning if API key is absent or API is unreachable.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self.base_url = base_url if base_url is not None else settings.GROQ_BASE_URL
        self.model = model if model is not None else settings.GROQ_MODEL
        self._client: Optional[OpenAI] = None
        
        if self.api_key:
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Groq OpenAI client: {e}")
                self._client = None

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    def propose_candidate_decision(
        self,
        tx: Transaction,
        cust: Optional[Customer],
        root_cause_info: RootCauseResult,
        autonomous_limit_paise: int = 5000000
    ) -> AgentDecision:
        """
        Proposes a candidate recovery action for a failed transaction.
        Attempts GroqCloud LLM structured call first if configured; falls back to deterministic model.
        """
        if self.is_available:
            try:
                llm_decision = self._call_groq_decision(tx, cust, root_cause_info, autonomous_limit_paise)
                if llm_decision:
                    return llm_decision
            except Exception as e:
                logger.warning(f"GroqCloud LLM call failed, using deterministic fallback: {e}")

        # Deterministic Contextual Reasoner (Fallback / Offline Mode)
        return self._deterministic_fallback_decision(tx, cust, root_cause_info, autonomous_limit_paise)

    def _call_groq_decision(
        self,
        tx: Transaction,
        cust: Optional[Customer],
        root_cause_info: RootCauseResult,
        autonomous_limit_paise: int
    ) -> Optional[AgentDecision]:
        """
        Executes real GroqCloud ChatCompletion with JSON structured output.
        """
        if not self._client:
            return None

        system_prompt = (
            "You are RecoverAI's Autonomous Revenue Recovery Decision Agent. "
            "Your role is to analyze a failed payment transaction, evaluate merchant risk, customer profile, "
            "and active payment rail root causes, and propose a candidate recovery action.\n\n"
            "Allowed actions:\n"
            "- RETRY (for transient timeouts on healthy customer profiles)\n"
            "- ALTERNATE_PAYMENT (for provider/gateway outages)\n"
            "- CUSTOMER_NUDGE (for customer-side auth/OTP/session timeout)\n"
            "- WAIT_AND_RETRY (for bank switch congestion / temporary rate limits)\n"
            "- ESCALATE (for high-value transactions > ₹50,000, permanent declines, or ambiguous anomalies)\n"
            "- NO_ACTION (if no recovery is feasible)\n\n"
            "Return valid JSON matching this structure exactly:\n"
            "{\n"
            '  "action": "RETRY",\n'
            '  "confidence": 0.92,\n'
            '  "diagnosis": "Short diagnostic summary",\n'
            '  "reasoning_summary": "Detailed contextual reasoning",\n'
            '  "requires_escalation": false\n'
            "}"
        )

        user_content = {
            "transaction_id": tx.id,
            "amount_inr": tx.amount_paise / 100.0,
            "amount_paise": tx.amount_paise,
            "payment_method": tx.payment_method,
            "provider": tx.provider,
            "bank": tx.bank,
            "failure_reason": tx.failure_reason,
            "failure_category": tx.failure_category,
            "retry_count": tx.retry_count,
            "customer_success_rate": tx.customer_success_rate,
            "customer_vip": cust.is_vip if cust else False,
            "active_root_cause": root_cause_info.likely_root_cause,
            "root_cause_confidence": root_cause_info.confidence,
            "autonomous_monetary_limit_inr": autonomous_limit_paise / 100.0
        }

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content, indent=2)}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )

        raw_output = response.choices[0].message.content
        data = json.loads(raw_output)

        action_str = data.get("action", "RETRY").upper()
        try:
            action_enum = RecoveryActionType(action_str)
        except ValueError:
            action_enum = RecoveryActionType.RETRY

        return AgentDecision(
            transaction_id=tx.id,
            diagnosis=data.get("diagnosis", "GroqCloud diagnostic classification"),
            action=action_enum,
            confidence=float(data.get("confidence", 0.85)),
            reasoning_summary=data.get("reasoning_summary", "GroqCloud proposed recovery."),
            requires_escalation=bool(data.get("requires_escalation", False))
        )

    def _deterministic_fallback_decision(
        self,
        tx: Transaction,
        cust: Optional[Customer],
        root_cause_info: RootCauseResult,
        autonomous_limit_paise: int
    ) -> AgentDecision:
        """
        Deterministic rule-based reasoning engine ensuring 100% reliability offline or without API keys.
        """
        if tx.amount_paise > autonomous_limit_paise:
            return AgentDecision(
                transaction_id=tx.id,
                diagnosis=f"High-value transaction at risk (₹{tx.amount_paise / 100:,.2f})",
                action=RecoveryActionType.RETRY if tx.is_transient else RecoveryActionType.ESCALATE,
                confidence=0.92,
                reasoning_summary=(
                    f"Transaction value ₹{tx.amount_paise / 100:,.2f} exceeds standard autonomous intervention limit. "
                    "Policy engine will validate autonomous threshold and route to human VIP ops."
                ),
                requires_escalation=True
            )

        if tx.failure_category == FailureCategory.PERMANENT.value:
            return AgentDecision(
                transaction_id=tx.id,
                diagnosis=f"Issuer decline code: {tx.failure_reason}",
                action=RecoveryActionType.RETRY,
                confidence=0.60,
                reasoning_summary=f"Permanent failure code {tx.failure_reason}. Submitted to policy engine for verification.",
                requires_escalation=False
            )

        if tx.payment_method == "UPI" and tx.failure_reason == "UPI_TIMEOUT":
            if tx.customer_success_rate >= 0.70:
                return AgentDecision(
                    transaction_id=tx.id,
                    diagnosis="Transient UPI route timeout on healthy customer profile",
                    action=RecoveryActionType.RETRY,
                    confidence=0.93,
                    reasoning_summary=(
                        f"Customer has {tx.customer_success_rate * 100:.0f}% historical success rate. "
                        f"Failure reason {tx.failure_reason} is transient. First-line automated retry proposed."
                    ),
                    requires_escalation=False
                )
            else:
                return AgentDecision(
                    transaction_id=tx.id,
                    diagnosis="UPI Timeout with lower customer historical payment score",
                    action=RecoveryActionType.ALTERNATE_PAYMENT,
                    confidence=0.86,
                    reasoning_summary="Customer history has intermittent failures. Proposing alternate payment link instead of direct retry.",
                    requires_escalation=False
                )

        if tx.failure_reason == "NETWORK_DISCONNECT" or "Provider Connectivity Outage" in root_cause_info.likely_root_cause:
            return AgentDecision(
                transaction_id=tx.id,
                diagnosis=f"Provider {tx.provider} network outage",
                action=RecoveryActionType.ALTERNATE_PAYMENT,
                confidence=0.89,
                reasoning_summary=f"Primary gateway {tx.provider} is experiencing upstream socket drops. Rerouting checkout to alternate rail.",
                requires_escalation=False
            )

        if tx.failure_reason == "BANK_SWITCH_BUSY":
            return AgentDecision(
                transaction_id=tx.id,
                diagnosis=f"Bank switch congestion on {tx.bank}",
                action=RecoveryActionType.WAIT_AND_RETRY,
                confidence=0.84,
                reasoning_summary="Bank switch reports temporary load congestion. Scheduling exponential backoff retry.",
                requires_escalation=False
            )

        if tx.failure_category == FailureCategory.CUSTOMER_ACTION_REQUIRED.value:
            return AgentDecision(
                transaction_id=tx.id,
                diagnosis=f"Customer authentication dropoff: {tx.failure_reason}",
                action=RecoveryActionType.CUSTOMER_NUDGE,
                confidence=0.85,
                reasoning_summary="Failure is customer-side auth/session timeout. Proposing WhatsApp/SMS interactive payment nudge.",
                requires_escalation=False
            )

        return AgentDecision(
            transaction_id=tx.id,
            diagnosis=f"Unclassified payment exception: {tx.failure_reason or 'UNKNOWN'}",
            action=RecoveryActionType.RETRY,
            confidence=0.65,
            reasoning_summary="Failure pattern is unclassified. Low confidence proposal submitted for policy validation.",
            requires_escalation=True
        )


# Global default LLM client singleton
groq_llm_client = GroqLLMClient()
