"""
Live / Direct verification script for GroqCloud API endpoint.
Tests:
1. Normal ChatCompletion
2. Tool/Function Calling
3. Structured Output (JSON Object)
"""

import os
import sys
import json
from openai import OpenAI
from backend.config import settings
from backend.llm import RECOVERY_TOOLS_SCHEMA

def run_live_groq_test():
    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    base_url = settings.GROQ_BASE_URL
    model = settings.GROQ_MODEL

    print("=" * 60)
    print("GROQCLOUD PROVIDER VERIFICATION SUITE")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Model:    {model}")
    print(f"API Key:  {'[CONFIGURED]' if api_key else '[NOT SET - USING DETERMINISTIC MOCK]'}")
    print("-" * 60)

    if not api_key:
        print("\n[MOCK / OFFLINE VERIFICATION]")
        print("GROQ_API_KEY is not set. Testing client deterministic fallback mode...")
        from backend.llm import groq_llm_client
        from backend.models import Transaction, FailureCategory
        from backend.root_cause import RootCauseResult
        from datetime import datetime

        tx = Transaction(
            id="tx_verify_1",
            customer_id="cust_1",
            amount_paise=150000,
            payment_method="UPI",
            provider="PHONEPE",
            bank="HDFC",
            status="FAILED",
            failure_reason="UPI_TIMEOUT",
            failure_category=FailureCategory.TRANSIENT.value,
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
        decision = groq_llm_client.propose_candidate_decision(tx, None, rc)
        print(f"Fallback Decision Action: {decision.action.value}")
        print(f"Fallback Confidence:      {decision.confidence}")
        print(f"Fallback Diagnosis:       {decision.diagnosis}")
        print("Mock mode test: SUCCESS\n")
        return

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 1. Normal ChatCompletion
    print("\n1. Testing Normal Chat Completion...")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are RecoverAI financial recovery assistant."},
                {"role": "user", "content": "Respond with 'GROQ_ONLINE' if you are functioning."}
            ],
            max_tokens=20
        )
        print(f"Response: {resp.choices[0].message.content.strip()}")
        print("Normal generation: SUCCESS")
    except Exception as e:
        print(f"Normal generation error: {e}")

    # 2. Tool / Function Calling
    print("\n2. Testing Tool / Function Calling...")
    try:
        tool_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are RecoverAI execution agent. Use the retry_payment tool for transaction tx_1001."},
                {"role": "user", "content": "Execute retry for transaction tx_1001 because of transient gateway timeout."}
            ],
            tools=RECOVERY_TOOLS_SCHEMA,
            tool_choice="auto",
            max_tokens=150
        )
        msg = tool_resp.choices[0].message
        if msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"Tool called: {tc.function.name}")
                print(f"Arguments:   {tc.function.arguments}")
            print("Tool-calling: SUCCESS")
        else:
            print("No tool call returned.")
    except Exception as e:
        print(f"Tool-calling error: {e}")

    # 3. Structured Output (JSON Object)
    print("\n3. Testing Structured Output (JSON Object)...")
    try:
        struct_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Analyze payment failure and output valid JSON with keys 'action', 'confidence', 'diagnosis', 'reasoning_summary', 'requires_escalation'."},
                {"role": "user", "content": "UPI payment of Rs. 150 failed with UPI_TIMEOUT on HDFC route. Customer historical success rate is 95%."}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=200
        )
        content = struct_resp.choices[0].message.content
        parsed = json.loads(content)
        print(f"Structured JSON output:\n{json.dumps(parsed, indent=2)}")
        print("Structured output: SUCCESS")
    except Exception as e:
        print(f"Structured output error: {e}")

    print("\n" + "=" * 60)
    print("ALL GROQCLOUD VERIFICATION TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    run_live_groq_test()
