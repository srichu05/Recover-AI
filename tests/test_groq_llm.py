"""
Tests for GroqCloud LLM Integration, Tool Calling, Structured Outputs, and Fallback
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from backend.models import (
    Transaction, Customer, AgentDecision, RecoveryActionType, Incident
)
from backend.root_cause import RootCauseResult
from backend.llm import GroqLLMClient, RECOVERY_TOOLS_SCHEMA, DecisionResponseSchema
from backend.agent import RecoveryAgentWorkflow
from backend.synthetic_data import generate_synthetic_customers, generate_incident_scenario, IncidentType
from backend.config import settings


def test_groq_client_init_and_mock_fallback_when_no_key():
    """Verify that when GROQ_API_KEY is empty, client initializes in fallback mode safely."""
    client = GroqLLMClient(api_key="", base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")
    assert not client.is_available

    tx = Transaction(
        id="tx_test_1",
        customer_id="cust_1",
        amount_paise=150000,
        payment_method="UPI",
        provider="PHONEPE",
        bank="HDFC",
        status="FAILED",
        failure_reason="UPI_TIMEOUT",
        failure_category="TRANSIENT",
        is_transient=True,
        customer_success_rate=0.85,
        timestamp=datetime.now().isoformat()
    )
    rc = RootCauseResult(
        likely_root_cause="UPI Gateway Timeout",
        confidence=0.92,
        evidence=["High UPI timeout cluster"],
        affected_dimension="PAYMENT_METHOD",
        primary_failure_reason="UPI_TIMEOUT",
        recommended_strategy="RETRY_TRANSIENT_TIMEOUTS",
        dimension_distributions={}
    )

    decision = client.propose_candidate_decision(tx, None, rc)
    assert decision.action == RecoveryActionType.RETRY
    assert decision.confidence >= 0.80
    assert not decision.requires_escalation


def test_groq_structured_output_json_parsing():
    """Verify that structured output from Groq is parsed into valid AgentDecision."""
    client = GroqLLMClient(api_key="gsk_mock_test_key", base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps({
            "action": "ALTERNATE_PAYMENT",
            "confidence": 0.88,
            "diagnosis": "ICICI Provider network drop detected",
            "reasoning_summary": "Rerouting to alternate HDFC card gateway rail.",
            "requires_escalation": False
        })))
    ]

    with patch.object(client._client.chat.completions, "create", return_value=mock_response) as mock_create:
        tx = Transaction(
            id="tx_test_2",
            customer_id="cust_2",
            amount_paise=250000,
            payment_method="CARD",
            provider="ICICI",
            bank="ICICI",
            status="FAILED",
            failure_reason="NETWORK_DISCONNECT",
            failure_category="TRANSIENT",
            is_transient=True,
            timestamp=datetime.now().isoformat()
        )
        rc = RootCauseResult(
            likely_root_cause="Provider Connectivity Outage",
            confidence=0.90,
            evidence=["Socket drops"],
            affected_dimension="PROVIDER",
            primary_failure_reason="NETWORK_DISCONNECT",
            recommended_strategy="REROUTE_ALTERNATE_PAYMENT",
            dimension_distributions={}
        )

        decision = client.propose_candidate_decision(tx, None, rc)
        assert decision.action == RecoveryActionType.ALTERNATE_PAYMENT
        assert decision.confidence == 0.88
        assert "ICICI" in decision.diagnosis
        assert mock_create.called
        assert mock_create.call_args.kwargs["model"] == "openai/gpt-oss-120b"
        assert mock_create.call_args.kwargs["response_format"] == {"type": "json_object"}


def test_groq_tool_calling_schema_validity():
    """Verify standard OpenAI/Groq function calling tool definitions schema."""
    assert len(RECOVERY_TOOLS_SCHEMA) == 4
    tool_names = [t["function"]["name"] for t in RECOVERY_TOOLS_SCHEMA]
    assert "retry_payment" in tool_names
    assert "create_alternate_payment_link" in tool_names
    assert "send_customer_notification" in tool_names
    assert "escalate_case" in tool_names

    for tool in RECOVERY_TOOLS_SCHEMA:
        assert tool["type"] == "function"
        assert "parameters" in tool["function"]
        assert "required" in tool["function"]["parameters"]


def test_groq_error_graceful_fallback():
    """Verify that if Groq API throws a network/rate limit error, execution falls back cleanly."""
    client = GroqLLMClient(api_key="gsk_mock_test_key", base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")

    with patch.object(client._client.chat.completions, "create", side_effect=Exception("Groq Rate Limit")):
        tx = Transaction(
            id="tx_test_3",
            customer_id="cust_3",
            amount_paise=100000,
            payment_method="UPI",
            provider="PHONEPE",
            bank="HDFC",
            status="FAILED",
            failure_reason="UPI_TIMEOUT",
            failure_category="TRANSIENT",
            is_transient=True,
            customer_success_rate=0.90,
            timestamp=datetime.now().isoformat()
        )
        rc = RootCauseResult(
            likely_root_cause="UPI Timeout",
            confidence=0.90,
            evidence=[],
            affected_dimension="PAYMENT_METHOD",
            primary_failure_reason="UPI_TIMEOUT",
            recommended_strategy="RETRY_TRANSIENT_TIMEOUTS",
            dimension_distributions={}
        )

        # Should NOT raise an exception, but gracefully return deterministic decision
        decision = client.propose_candidate_decision(tx, None, rc)
        assert decision.action == RecoveryActionType.RETRY
        assert decision.confidence > 0.80


def test_agent_recovery_workflow_with_groq_client():
    """Verify full end-to-end recovery agent workflow with Groq client."""
    client = GroqLLMClient(api_key="", base_url="https://api.groq.com/openai/v1", model="openai/gpt-oss-120b")
    workflow = RecoveryAgentWorkflow(llm_client=client)

    customers = generate_synthetic_customers(10, seed=42)
    incident, txs = generate_incident_scenario(
        incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
        severity_pct=60.0,
        affected_count=20,
        customers=customers,
        seed=42
    )

    updated_txs, metrics = workflow.run_recovery_workflow(incident, txs, customers, random_seed=42)
    assert metrics["strategy"] == "RECOVER_AI"
    assert metrics["actions_proposed"] > 0
    assert metrics["successful_recoveries"] > 0
    assert metrics["total_recovered_paise"] > 0
    assert incident.status == "RESOLVED"
