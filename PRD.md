# RecoverAI --- Product Requirements Document (PRD)

**Version:** 1.0\
**Status:** Buildathon MVP --- Implementation Source of Truth\
**Track:** Razorpay AI Revenue Recovery --- Track 03\
**Project:** RecoverAI\
**Primary Objective:** Build a credible, measurable, agentic
revenue-recovery prototype that can be implemented and demonstrated
within a very limited build window.

------------------------------------------------------------------------

## 1. Executive Summary

RecoverAI is an AI-powered revenue recovery system for merchants.

The system detects payment degradation and revenue at risk, investigates
the likely cause, identifies affected transactions, determines the
safest recovery intervention, executes that intervention through bounded
tools, verifies the outcome, and measures the revenue actually
recovered.

The product is deliberately designed around Razorpay's Track 03
requirement:

> Detect revenue at risk → determine the right intervention → execute a
> bounded recovery workflow.

The primary demonstration scenario is **payment degradation → root cause
→ recovery action**.

RecoverAI is not intended to process real money or operate against
production payment infrastructure. It uses a controlled synthetic
payment environment and simulated/test actions so that the complete
recovery loop can be demonstrated safely and reproducibly.

### Core product loop

``` text
Payment Events
    ↓
Revenue Risk Detection
    ↓
Incident Detection
    ↓
Root Cause Analysis
    ↓
Affected Transaction Identification
    ↓
Recovery Agent
    ↓
Policy / Guardrail Validation
    ↓
Bounded Recovery Action
    ↓
Outcome Verification
    ↓
Revenue Recovered
    ↓
Audit Trail + Evaluation
```

------------------------------------------------------------------------

# 2. Challenge Alignment

RecoverAI must explicitly satisfy the requirements visible in Razorpay
Buildathon Track 03.

## Razorpay Track 03: AI Revenue Recovery

The track asks builders to create an agent that:

1.  Detects revenue at risk.
2.  Determines the appropriate intervention.
3.  Executes a bounded recovery workflow.
4.  Demonstrates measured money recovered across a batch.
5.  Implements compliant escalation.
6.  Implements stopping rules.
7.  Maintains an audit trail.

Razorpay's example direction for this track includes:

**Payment degradation → root cause → recovery action**

RecoverAI uses this as its primary use case.

### Official reference

Razorpay Buildathon:\
https://razorpay.com/buildathon/

------------------------------------------------------------------------

# 3. Problem Statement

## 3.1 Real-world problem

Payment revenue loss rarely happens as a single obvious event.

A merchant may experience:

-   sudden payment success-rate degradation,
-   payment-provider or bank-specific failures,
-   transient network/time-out failures,
-   customer payment abandonment,
-   repeated payment failures,
-   recoverable versus permanently failed transactions,
-   high-value transactions requiring additional care.

Traditional dashboards can detect that payment performance has
deteriorated, but detection alone does not recover the lost revenue.

The merchant needs a system that can move from:

``` text
Something is wrong
```

to:

``` text
What happened?
Why did it happen?
Which revenue is at risk?
Which transactions can be recovered?
What is the safest action?
Did that action work?
How much money did we recover?
```

## 3.2 Product opportunity

RecoverAI closes this loop by combining:

-   deterministic transaction analytics,
-   anomaly detection,
-   root-cause analysis,
-   agentic decision-making,
-   bounded financial-action policies,
-   simulated recovery tools,
-   outcome verification,
-   quantitative evaluation.

The goal is not to maximize actions.

The goal is:

> **Maximize recoverable revenue while minimizing unnecessary or unsafe
> recovery actions.**

------------------------------------------------------------------------

# 4. Product Vision

> **RecoverAI turns payment failures from passive alerts into
> measurable, controlled revenue-recovery workflows.**

The system should feel like an intelligent operations agent rather than
a chatbot.

A merchant should be able to see:

``` text
₹X revenue at risk
        ↓
Why?
        ↓
What should we do?
        ↓
Why is this action safe?
        ↓
Execute
        ↓
How much did we recover?
```

------------------------------------------------------------------------

# 5. Target User

## Primary user

A merchant/operator responsible for payment performance and revenue.

The user needs to:

-   understand payment degradation,
-   prioritize revenue at risk,
-   recover eligible payments,
-   avoid repeated or unnecessary retries,
-   escalate exceptional cases,
-   measure recovery performance.

## Secondary user

A technical/evaluation reviewer who needs to inspect:

-   agent behavior,
-   architecture,
-   decision reasoning,
-   guardrails,
-   evaluation methodology,
-   measurable results,
-   auditability.

------------------------------------------------------------------------

# 6. Product Goals

## Primary goals

### G1 --- Detect revenue at risk

Identify abnormal payment degradation and calculate the associated
revenue exposure.

### G2 --- Diagnose the problem

Determine likely causes using transaction-level and aggregate
payment-health signals.

### G3 --- Select appropriate interventions

Choose an intervention based on transaction context, failure type,
customer/payment history, system health, and policy constraints.

### G4 --- Execute bounded recovery

Perform recovery actions only through controlled tools and deterministic
policies.

### G5 --- Verify outcomes

Determine whether the recovery action succeeded, failed, or requires
escalation.

### G6 --- Quantify recovered revenue

Measure revenue recovered across a complete evaluation batch.

### G7 --- Demonstrate safety

Show stopping rules, escalation, duplicate-action protection, and policy
enforcement.

### G8 --- Make the agent observable

Provide a replayable record of how the system reached and executed each
decision.

------------------------------------------------------------------------

# 7. Non-Goals

The MVP must NOT attempt to:

-   process real customer money,
-   perform real financial transactions,
-   connect to production Razorpay payment infrastructure,
-   store real customer PII,
-   build a full production payment gateway,
-   build a mobile application,
-   implement voice recovery,
-   implement every revenue-recovery scenario,
-   build a large multi-agent ecosystem,
-   add RAG without a demonstrated requirement,
-   train a large/deep model solely for novelty.

The system should be a **safe, reproducible prototype** demonstrating
the required product behavior.

------------------------------------------------------------------------

# 8. Primary Use Case

## Payment Degradation → Root Cause → Recovery

A merchant's payment success rate suddenly drops.

Example:

``` text
Normal UPI success rate: 93%
Current UPI success rate: 67%

Revenue at risk: ₹4,82,000
```

RecoverAI should:

1.  Detect the degradation.
2.  Confirm it is statistically abnormal.
3.  Identify the affected payment segment.
4.  Investigate failure reasons.
5.  Identify likely root cause.
6.  Identify recoverable transactions.
7.  Create a recovery plan.
8.  Validate each proposed action against policy.
9.  Execute permitted actions.
10. Verify outcomes.
11. Stop or escalate when required.
12. Calculate recovered revenue.
13. Record every material decision in the audit trail.

------------------------------------------------------------------------

# 9. Secondary Recovery Scenarios

The architecture should support additional recovery scenarios without
requiring them for the MVP.

Potential future scenarios:

-   checkout abandonment,
-   failed subscription recovery,
-   mandate retry sequencing,
-   B2B receivables chasing,
-   promise-to-pay tracking,
-   alternate payment recovery.

The implementation must not allow these optional scenarios to delay the
core payment-degradation workflow.

------------------------------------------------------------------------

# 10. Standout Feature --- Incident Simulator

## 10.1 Purpose

The Incident Simulator is the primary showcase feature.

It allows a reviewer to create a controlled payment incident and watch
RecoverAI detect and recover revenue in real time.

This converts the demo from a static dashboard into an interactive
experiment.

## 10.2 Scenario controls

The simulator should allow controlled configuration of:

-   payment method,
-   failure type,
-   incident severity,
-   number of affected transactions,
-   approximate transaction value,
-   customer history characteristics,
-   incident duration where practical.

Example:

``` text
Payment method: UPI
Failure type: Timeout
Severity: 70%
Affected transactions: 500
```

## 10.3 Simulation lifecycle

``` text
Configure Incident
      ↓
Generate Affected Transactions
      ↓
Inject Payment Degradation
      ↓
Detect Incident
      ↓
Run RecoverAI
      ↓
Execute Recovery
      ↓
Verify Results
      ↓
Compare Against Baseline
```

## 10.4 Baseline comparison

Every incident should support comparison between:

### Static baseline

A simple predefined recovery strategy.

Example:

``` text
Retry every eligible transient failure once.
```

### RecoverAI

Context-aware recovery strategy.

The UI should show:

-   revenue at risk,
-   baseline revenue recovered,
-   RecoverAI revenue recovered,
-   recovery-rate difference,
-   unnecessary actions,
-   escalations,
-   policy stops.

The comparison must be computed from the actual simulation.

------------------------------------------------------------------------

# 11. Agent Replay

The system should provide a human-readable replay of an incident.

Example:

``` text
14:05:03  Revenue degradation detected
14:05:04  Payment health analyzed
14:05:05  UPI timeout spike identified
14:05:06  276 transactions classified as recoverable
14:05:07  Recovery plan generated
14:05:08  Policy validation completed
14:05:09  Recovery actions executed
14:05:11  Outcomes verified
14:05:12  Recovery completed
```

The replay should allow inspection of individual transaction decisions.

------------------------------------------------------------------------

# 12. Individual Decision Explanation

For every recovery decision, RecoverAI should be able to show:

-   transaction ID,
-   amount,
-   failure reason,
-   retry count,
-   relevant customer/payment context,
-   incident context,
-   selected action,
-   confidence,
-   policy result,
-   tool invoked,
-   execution result,
-   recovered amount.

Example:

``` text
Decision: RETRY

Reason:
Transient UPI timeout.
Customer has strong historical payment success.
Transaction has not previously been retried.
Current payment-health incident indicates temporary degradation.

Confidence: 94%

Policy:
Retry allowed
Retry limit not reached
Amount within autonomous-action threshold

Execution:
retry_payment()

Result:
SUCCESS

Revenue recovered:
₹2,499
```

The explanation must be grounded in actual structured state. It must not
invent transaction facts.

------------------------------------------------------------------------

# 13. System Architecture

``` text
                    ┌───────────────────────┐
                    │ Synthetic Transaction │
                    │ Environment           │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Revenue Risk Detector  │
                    │                        │
                    │ Success-rate anomaly   │
                    │ Failure spike          │
                    │ Revenue exposure       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Root Cause Analyzer    │
                    │                        │
                    │ Method                 │
                    │ Provider / bank        │
                    │ Failure reason         │
                    │ Time window            │
                    │ Transaction patterns   │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Recovery Agent         │
                    │                        │
                    │ Contextual planning    │
                    │ Structured decision    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Policy / Guardrail     │
                    │ Engine                 │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
              RETRY       ALTERNATE PAY       ESCALATE
                │               │                │
                └───────────────┼────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Execution Simulator   │
                    │ / Controlled Tools    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Outcome Verification  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Evaluation + Audit    │
                    └───────────────────────┘
```

------------------------------------------------------------------------

# 14. Architectural Principle

The LLM/agent must NOT directly control financial actions.

The intended control boundary is:

``` text
Agent proposes action
        ↓
Deterministic policy validates action
        ↓
Approved action executes
```

This provides a clean separation between:

-   AI reasoning,
-   deterministic financial constraints,
-   execution,
-   measurement.

------------------------------------------------------------------------

# 15. Agent Workflow

The agent should implement a stateful workflow conceptually equivalent
to:

``` text
DETECT
  ↓
DIAGNOSE
  ↓
IDENTIFY_AFFECTED_TRANSACTIONS
  ↓
PLAN
  ↓
VALIDATE_POLICY
  ↓
EXECUTE
  ↓
VERIFY
  ↓
MEASURE
  ↓
STOP / ESCALATE / COMPLETE
```

The agent framework may use LangGraph or another suitable orchestration
approach.

The implementation choice must prioritize reliability and clarity over
framework novelty.

------------------------------------------------------------------------

# 16. Agent Responsibilities

The recovery agent is responsible for:

1.  Reading structured incident context.
2.  Investigating relevant signals through tools.
3.  Producing a structured diagnosis.
4.  Selecting an allowed recovery action.
5.  Providing a grounded rationale.
6.  Providing confidence.
7.  Respecting policy constraints.
8.  Calling tools only through the defined interface.
9.  Verifying outcomes.
10. Escalating uncertain or restricted cases.
11. Stopping when recovery is no longer appropriate.

The agent is NOT responsible for:

-   calculating final financial metrics from untrusted text,
-   overriding policy,
-   changing retry limits,
-   changing monetary thresholds,
-   bypassing escalation,
-   inventing transaction information.

------------------------------------------------------------------------

# 17. Recovery Tools

The MVP should expose a small, controlled toolset.

## `get_transaction(transaction_id)`

Returns structured transaction information.

## `get_customer_history(customer_id)`

Returns relevant historical payment behavior.

## `get_payment_health()`

Returns aggregate payment-health information.

## `retry_payment(transaction_id)`

Attempts a simulated retry.

## `create_alternate_payment_link(transaction_id)`

Creates a simulated alternate payment path.

## `send_customer_notification(transaction_id, message_type)`

Records a simulated customer notification.

## `escalate_case(transaction_id, reason)`

Creates a human-review case.

The exact implementation can be adapted by the coding agent, but the
tool contracts and safety behavior must remain equivalent.

------------------------------------------------------------------------

# 18. Recovery Actions

The core actions are:

### RETRY

Use for eligible transient failures.

### ALTERNATE_PAYMENT

Use when an alternate payment route is appropriate.

### CUSTOMER_NUDGE

Use when customer action is required.

### WAIT_AND_RETRY

Use when immediate retry is inappropriate but recovery may still be
possible.

### ESCALATE

Use when autonomous recovery is not safe or confidence is insufficient.

### NO_ACTION

Use when recovery is inappropriate or the transaction is permanently
unrecoverable.

------------------------------------------------------------------------

# 19. Guardrail Requirements

Guardrails are mandatory.

## 19.1 Retry limit

A transaction cannot be retried beyond a configurable maximum.

Default MVP value:

``` text
MAX_RETRIES = 2
```

## 19.2 Monetary threshold

High-value transactions should require escalation or additional
approval.

Default example:

``` text
AUTONOMOUS_ACTION_LIMIT = ₹50,000
```

The exact value should be configurable.

## 19.3 Confidence threshold

Low-confidence autonomous decisions should be escalated.

Default example:

``` text
MIN_AUTONOMOUS_CONFIDENCE = 0.80
```

## 19.4 Failure-type policy

Permanent failures must not be blindly retried.

## 19.5 Duplicate-action protection

The system must prevent accidental duplicate execution of the same
recovery action.

## 19.6 Success stop condition

Once a transaction is recovered, further recovery actions must stop.

## 19.7 Customer-decline stop condition

If the simulated customer declines the recovery path, the workflow must
stop or escalate.

## 19.8 Human escalation

Cases outside autonomous policy must create an auditable escalation
rather than silently failing.

------------------------------------------------------------------------

# 20. Revenue-at-Risk Detection

The system should calculate revenue at risk from affected/recoverable
transactions.

A simple MVP definition:

``` text
Revenue at Risk =
sum(value of transactions that are currently unsuccessful
and have a plausible recovery path)
```

The implementation may use a more rigorous definition if it can be
explained and reproduced.

Aggregate indicators should include:

-   baseline success rate,
-   current success rate,
-   degradation magnitude,
-   affected transaction count,
-   gross transaction value affected,
-   estimated recoverable value,
-   revenue at risk.

------------------------------------------------------------------------

# 21. Payment Degradation Detection

The system should identify abnormal changes using deterministic
statistical logic.

Acceptable MVP approaches include:

-   rolling baseline,
-   percentage-point degradation threshold,
-   z-score,
-   moving average deviation,
-   statistical anomaly detection,
-   Isolation Forest where useful.

The implementation should prefer a simple explainable detector over
unnecessary model complexity.

Example:

``` text
Baseline UPI success: 93.4%
Current UPI success: 68.2%

Degradation:
25.2 percentage points

Status:
HIGH-SEVERITY INCIDENT
```

------------------------------------------------------------------------

# 22. Root Cause Analysis

The root-cause system should investigate dimensions such as:

-   payment method,
-   failure reason,
-   provider,
-   bank/route where available in synthetic data,
-   time window,
-   transaction volume,
-   historical baseline,
-   customer segment.

Example output:

``` text
Likely root cause:
Transient UPI payment-route degradation.

Evidence:
- UPI failures increased sharply.
- Card and netbanking remain near baseline.
- Timeout failures account for most incremental failures.
- The degradation is concentrated in the incident window.
```

The system should distinguish:

-   high-confidence root cause,
-   probable root cause,
-   insufficient evidence.

------------------------------------------------------------------------

# 23. Synthetic Data Environment

The system must generate synthetic payment data.

Suggested fields:

``` text
transaction_id
merchant_id
customer_id
timestamp
amount
currency
payment_method
provider
bank
status
failure_reason
retry_count
customer_payment_success_rate
previous_payment_count
previous_failure_count
cart_value
```

Additional fields may be added if they improve the core workflow.

------------------------------------------------------------------------

# 24. Synthetic Incident Generator

The simulator should support controlled incidents.

Examples:

### UPI timeout degradation

-   elevated timeout failures,
-   UPI-specific,
-   temporary,
-   recoverable subset.

### Provider degradation

-   failures concentrated around one provider.

### Bank-specific degradation

-   failures concentrated around one bank/route.

### Mixed failure incident

-   transient failures,
-   permanent failures,
-   customer-action-required failures.

The generator must preserve enough ground truth to evaluate whether
RecoverAI made appropriate decisions.

------------------------------------------------------------------------

# 25. Ground Truth

The simulator must know, internally, whether an action is likely to
succeed.

For example:

``` text
Transient timeout + first retry
→ high probability of recovery

Permanent decline
→ no recovery through retry

Retry limit reached
→ retry prohibited

High-value transaction
→ escalation required
```

Ground truth is for evaluation and simulation, not exposed directly to
the agent.

------------------------------------------------------------------------

# 26. Recovery Outcome Simulation

Recovery tools should simulate realistic outcomes.

Example:

``` text
retry_payment()
    ↓
eligible?
    ↓
ground-truth recovery probability
    ↓
SUCCESS / FAILURE
```

The simulator must produce deterministic results when a fixed random
seed is supplied.

This enables reproducible evaluation.

------------------------------------------------------------------------

# 27. Evaluation Framework

Evaluation is a first-class product feature.

The system must compare:

## Baseline

A simple static recovery policy.

Example:

``` text
Retry every eligible transient failure once.
```

## RecoverAI

Context-aware agentic strategy with guardrails.

Both must be evaluated against the same batch.

------------------------------------------------------------------------

# 28. Required Metrics

At minimum:

### Revenue metrics

-   total revenue at risk,
-   revenue eligible for recovery,
-   revenue attempted,
-   revenue recovered,
-   recovery rate,
-   baseline recovery rate,
-   improvement over baseline.

### Operational metrics

-   number of recovery actions,
-   successful actions,
-   failed actions,
-   escalations,
-   policy-blocked actions,
-   stopping-rule activations,
-   duplicate actions prevented.

### Agent metrics

-   decision distribution,
-   low-confidence decisions,
-   escalation rate,
-   tool execution success rate.

### Safety metrics

-   unauthorized actions prevented,
-   retries beyond limit prevented,
-   high-value autonomous actions prevented,
-   permanent-failure retries prevented.

------------------------------------------------------------------------

# 29. Core Evaluation Metric

The headline metric should be:

# Revenue Recovered

The demo should make this highly visible.

The second headline metric should be:

# Improvement Over Baseline

Example format:

``` text
Revenue at Risk       ₹X
Baseline Recovered    ₹Y
RecoverAI Recovered   ₹Z
Improvement            +N%
```

All values must be generated by actual evaluation runs.

No fabricated results are permitted.

------------------------------------------------------------------------

# 30. Reproducibility

The repository must provide a single evaluation entry point.

Example:

``` bash
python evaluation/run_evaluation.py
```

It should:

1.  Generate/load evaluation data.
2.  Run baseline.
3.  Run RecoverAI.
4.  Calculate metrics.
5.  Save results.
6.  Print a concise summary.

Suggested outputs:

``` text
evaluation/results.json
evaluation/results.csv
evaluation/report.md
```

The exact filenames can be changed if the implementation agent has a
better structure.

------------------------------------------------------------------------

# 31. Evaluation Scenarios

At minimum evaluate:

### Scenario A --- Normal traffic

The system should not generate unnecessary incidents.

### Scenario B --- Mild degradation

The system should detect a meaningful degradation and recover eligible
transactions.

### Scenario C --- Severe degradation

The system should recover aggressively within policy while avoiding
unsafe actions.

### Scenario D --- Permanent failures

The system should not blindly retry.

### Scenario E --- Retry-limit cases

The system should stop.

### Scenario F --- High-value transactions

The system should escalate according to policy.

### Scenario G --- Low-confidence diagnosis

The system should escalate rather than take unsupported autonomous
action.

------------------------------------------------------------------------

# 32. Dashboard Requirements

The dashboard should prioritize clarity over visual complexity.

## Page 1 --- Overview

Display:

-   revenue at risk,
-   revenue recovered,
-   recovery rate,
-   active incidents,
-   transactions affected,
-   escalations,
-   policy stops.

## Page 2 --- Incident Simulator

Allow creation and execution of an incident.

Show:

-   incident configuration,
-   generated impact,
-   agent progress,
-   recovery results.

## Page 3 --- Incident Detail

Show:

-   payment-health graph,
-   degradation,
-   root cause,
-   affected transactions,
-   recovery plan,
-   baseline versus RecoverAI.

## Page 4 --- Agent Replay

Show chronological agent actions and reasoning.

## Page 5 --- Audit Trail

Show:

-   transaction,
-   proposed action,
-   policy decision,
-   execution,
-   result,
-   timestamp,
-   revenue recovered.

## Page 6 --- Evaluation

Show:

-   baseline,
-   RecoverAI,
-   metrics,
-   scenario results,
-   overall revenue improvement.

------------------------------------------------------------------------

# 33. UX Principles

The UI should communicate the financial impact immediately.

A reviewer should understand within seconds:

1.  How much revenue is at risk?
2.  What caused it?
3.  What is RecoverAI doing?
4.  How much did it recover?
5.  Why were some transactions not recovered?

Avoid excessive animations and decorative components.

Prioritize:

-   readable numbers,
-   clear state,
-   visible agent activity,
-   explainability,
-   evaluation results.

------------------------------------------------------------------------

# 34. Recommended Technology Stack

## Frontend

-   Next.js
-   TypeScript
-   React
-   clean dashboard UI

## Backend

-   Python
-   FastAPI

## Agent orchestration

-   LangGraph or equivalent stateful orchestration

## Data / ML

-   pandas
-   NumPy
-   scikit-learn where appropriate

## Database

-   PostgreSQL preferred
-   SQLite acceptable if it materially reduces setup complexity and
    still supports the complete demo

## LLM

Use a structured-output-capable LLM available to the implementation
environment.

The model should be used for reasoning/diagnosis/planning, not for
deterministic financial calculations.

## Testing

-   pytest for backend/agent logic
-   frontend tests where practical
-   end-to-end smoke test for the primary incident flow

------------------------------------------------------------------------

# 35. API Requirements

The backend should expose clean APIs for:

-   dashboard summary,
-   transactions,
-   incidents,
-   incident creation,
-   incident execution,
-   agent status,
-   agent replay,
-   recovery actions,
-   audit logs,
-   evaluation results.

Exact endpoint naming is implementation-flexible.

All APIs should use structured JSON.

------------------------------------------------------------------------

# 36. Data Integrity

Financial values must be represented safely.

Prefer integer minor units (for example, paise) internally rather than
floating-point currency arithmetic.

Example:

``` text
₹2,499.50
→ 249950 paise
```

Formatting to rupees should happen at presentation boundaries.

The evaluation system must avoid floating-point rounding errors in
financial totals.

------------------------------------------------------------------------

# 37. Security and Secrets

The repository must never contain:

-   API keys,
-   model provider secrets,
-   database passwords,
-   access tokens,
-   real customer data.

Provide:

``` text
.env.example
```

with placeholder configuration.

The application must fail clearly when required credentials are missing.

------------------------------------------------------------------------

# 38. Failure Handling

The system must handle:

-   LLM failure,
-   malformed LLM output,
-   tool failure,
-   database failure,
-   policy rejection,
-   unknown failure reason,
-   missing customer history,
-   duplicate execution attempt,
-   low-confidence decision.

The system must prefer:

``` text
fail safely → escalate
```

rather than:

``` text
guess → execute
```

------------------------------------------------------------------------

# 39. Structured Agent Output

The LLM should return structured data rather than free-form
instructions.

Conceptual schema:

``` json
{
  "diagnosis": "...",
  "action": "RETRY",
  "confidence": 0.94,
  "reasoning_summary": "...",
  "transaction_ids": ["..."],
  "requires_escalation": false
}
```

The actual schema may be expanded as needed.

The policy engine must validate the structured output before execution.

------------------------------------------------------------------------

# 40. Observability

Every meaningful agent run should produce:

-   run ID,
-   incident ID,
-   timestamps,
-   current state,
-   inputs,
-   model decision,
-   policy decision,
-   tool call,
-   tool result,
-   final outcome.

This information should power Agent Replay and the audit trail.

------------------------------------------------------------------------

# 41. Audit Trail Requirements

The audit trail is mandatory.

Each action record should contain at minimum:

``` text
audit_id
timestamp
incident_id
transaction_id
agent_run_id
proposed_action
policy_decision
policy_reason
tool_called
execution_status
outcome
amount
recovered_amount
```

The audit trail must be append-oriented and must not silently overwrite
previous decisions.

------------------------------------------------------------------------

# 42. Baseline Definition

The baseline must be intentionally simple and deterministic.

Recommended baseline:

``` text
IF failure is classified as transient
AND retry_count < 1
THEN retry once
ELSE no recovery
```

The baseline should not use the LLM.

This gives a fair comparison between a static recovery strategy and
RecoverAI's contextual strategy.

------------------------------------------------------------------------

# 43. What Constitutes a Successful Recovery

A transaction counts as recovered only if the simulated payment outcome
becomes successful after an intervention.

Revenue recovered is:

``` text
sum(amount of successfully recovered transactions)
```

Do not count:

-   merely proposed actions,
-   notifications,
-   escalations,
-   failed retries,
-   transactions that were already successful,
-   duplicate recovery attempts.

------------------------------------------------------------------------

# 44. Demo Flow

The final demo should follow this sequence:

### Step 1

Open RecoverAI dashboard.

### Step 2

Show healthy payment baseline.

### Step 3

Open Incident Simulator.

### Step 4

Create a UPI degradation incident.

### Step 5

Show revenue at risk.

### Step 6

Run RecoverAI.

### Step 7

Show live agent progression.

### Step 8

Show root-cause diagnosis.

### Step 9

Show recovery plan.

### Step 10

Show guardrail decisions.

### Step 11

Show recovered revenue.

### Step 12

Show baseline comparison.

### Step 13

Show Agent Replay.

### Step 14

Show why certain transactions were stopped/escalated.

### Step 15

Open evaluation results.

------------------------------------------------------------------------

# 45. Demo Narrative

The central narrative should be:

> A merchant experiences a sudden payment degradation.

> RecoverAI detects that revenue is at risk.

> It identifies the likely root cause instead of merely reporting a
> failure spike.

> It determines which transactions are recoverable and selects
> appropriate interventions.

> Every action passes through deterministic financial guardrails.

> RecoverAI executes the recovery workflow.

> The system verifies the outcomes and calculates exactly how much
> revenue was recovered.

> Finally, the system compares its performance against a static baseline
> and exposes the full decision trail.

This narrative should drive the UI, README, video, and presentation.

------------------------------------------------------------------------

# 46. GitHub Requirements

The final repository must be clean and commit-ready.

Recommended structure:

``` text
recover-ai/
├── frontend/
├── backend/
├── evaluation/
├── data/
├── docs/
├── tests/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

The implementation agent may alter the exact structure when there is a
clear engineering reason.

------------------------------------------------------------------------

# 47. README Requirements

README must contain:

1.  Project title.
2.  One-line value proposition.
3.  Problem statement.
4.  Solution.
5.  Why this matters.
6.  Architecture diagram.
7.  Agent workflow.
8.  Guardrails.
9.  Incident Simulator.
10. Evaluation methodology.
11. Baseline.
12. Actual results.
13. Screenshots/GIFs where available.
14. Tech stack.
15. Setup instructions.
16. How to run.
17. How to run evaluation.
18. Example output.
19. Limitations.
20. Future scope.

The README must clearly distinguish:

-   simulated/test behavior,
-   actual implementation,
-   future production integrations.

------------------------------------------------------------------------

# 48. Architecture Diagram

The repository must include a polished architecture diagram showing:

``` text
Data
 ↓
Detection
 ↓
Diagnosis
 ↓
Agent
 ↓
Policy
 ↓
Tools
 ↓
Verification
 ↓
Evaluation
```

The diagram must clearly show that the agent cannot bypass the policy
layer.

------------------------------------------------------------------------

# 49. Testing Requirements

At minimum:

## Unit tests

Test:

-   anomaly detection,
-   revenue-at-risk calculation,
-   policy engine,
-   retry limits,
-   monetary thresholds,
-   failure classification,
-   recovery outcome calculation.

## Agent tests

Test:

-   valid structured output,
-   malformed output,
-   low confidence,
-   escalation,
-   tool selection.

## Integration test

Run the complete:

``` text
incident → detection → diagnosis → plan → policy → execution → verification → audit
```

flow.

## Evaluation smoke test

Run a small deterministic batch and confirm metrics are produced.

------------------------------------------------------------------------

# 50. Definition of Done

RecoverAI is considered complete only when ALL of the following are
true.

## Product

-   [ ] Dashboard runs.
-   [ ] Incident Simulator works.
-   [ ] Payment degradation can be generated.
-   [ ] Revenue at risk is displayed.
-   [ ] Root cause is produced.
-   [ ] Recovery plan is produced.
-   [ ] Recovery actions execute in simulation.
-   [ ] Outcomes are verified.
-   [ ] Revenue recovered is displayed.
-   [ ] Baseline comparison works.
-   [ ] Agent Replay works.
-   [ ] Audit trail works.

## AI

-   [ ] Agent uses structured state.
-   [ ] Agent uses tools.
-   [ ] Agent produces structured decisions.
-   [ ] Agent cannot bypass policy.
-   [ ] Low-confidence decisions escalate.

## Safety

-   [ ] Retry limit enforced.
-   [ ] Monetary threshold enforced.
-   [ ] Permanent failures are not blindly retried.
-   [ ] Duplicate actions prevented.
-   [ ] Success stops recovery.
-   [ ] Escalations are recorded.

## Evaluation

-   [ ] Baseline implemented.
-   [ ] RecoverAI evaluated on same batch.
-   [ ] Revenue at risk calculated.
-   [ ] Revenue recovered calculated.
-   [ ] Recovery rate calculated.
-   [ ] Baseline comparison calculated.
-   [ ] Safety metrics calculated.
-   [ ] Results reproducible.

## Engineering

-   [ ] Tests pass.
-   [ ] Application starts successfully.
-   [ ] Evaluation runs successfully.
-   [ ] No secrets committed.
-   [ ] No junk/dead code.
-   [ ] README complete.
-   [ ] Architecture diagram included.
-   [ ] Repository is clean and commit-ready.

------------------------------------------------------------------------

# 51. Priority Model

Because the build window is extremely short, implementation must follow
this priority order.

## P0 --- Mandatory

1.  Synthetic data.
2.  Incident generation.
3.  Degradation detection.
4.  Revenue-at-risk calculation.
5.  Root-cause analysis.
6.  Recovery agent.
7.  Policy engine.
8.  Recovery tools.
9.  Outcome simulation.
10. Revenue recovered calculation.
11. Baseline comparison.
12. Audit trail.
13. Incident Simulator.
14. Basic dashboard.
15. Evaluation script.

## P1 --- High value

1.  Agent Replay.
2.  Decision explanations.
3.  Rich evaluation dashboard.
4.  Better incident visualization.
5.  Comprehensive tests.
6.  Polished README.
7.  Architecture diagram.

## P2 --- Only if all P0/P1 work

1.  More sophisticated ML.
2.  More incident types.
3.  Customer segmentation.
4.  Advanced visualizations.
5.  Additional recovery strategies.

## Explicitly deprioritized

-   voice,
-   mobile application,
-   production payment integration,
-   RAG,
-   unnecessary multi-agent complexity,
-   large model training.

------------------------------------------------------------------------

# 52. Engineering Quality Standard

The system should look like a serious engineering prototype, not a
disposable hackathon script.

Priorities:

1.  Correctness.
2.  Reproducibility.
3.  Explainability.
4.  Safety.
5.  Measurable outcomes.
6.  Clean architecture.
7.  Demo quality.
8.  Visual polish.

Do not sacrifice core correctness for decorative UI.

------------------------------------------------------------------------

# 53. Implementation Guidance for the Coding Agent

The coding agent must:

1.  Inspect the existing workspace before modifying it.
2.  Reuse useful existing infrastructure where appropriate.
3.  Avoid unnecessary dependencies.
4.  Prefer simple, robust implementations.
5.  Keep interfaces modular.
6.  Use deterministic simulation seeds for evaluation.
7.  Validate all agent outputs.
8.  Never allow the LLM to bypass policy.
9.  Keep financial calculations deterministic.
10. Add tests while implementing.
11. Run the application before declaring completion.
12. Run the evaluation before declaring completion.
13. Generate actual metrics.
14. Inspect the generated metrics for sanity.
15. Clean the repository.
16. Update README with actual implementation details.
17. Never invent completed features or evaluation results.

------------------------------------------------------------------------

# 54. Final Results Artifact

Before the project is considered complete, the implementation must
produce a final machine-readable and human-readable results report.

The report should include:

``` text
Dataset size
Total transaction value
Revenue at risk
Baseline actions
Baseline revenue recovered
RecoverAI actions
RecoverAI revenue recovered
Recovery-rate comparison
Improvement over baseline
Escalations
Policy stops
Successful recoveries
Failed recoveries
Duplicate actions prevented
```

It should also summarize scenario-level results.

------------------------------------------------------------------------

# 55. Sanity Checks on Results

The evaluation system must detect obvious inconsistencies.

Examples:

-   recovered revenue cannot exceed revenue at risk,
-   recovered transaction cannot exceed its transaction amount,
-   an escalated transaction cannot simultaneously count as an
    autonomous successful recovery,
-   a transaction cannot be recovered twice,
-   policy-blocked actions cannot be counted as executed actions,
-   successful transactions cannot be counted as newly recovered
    revenue.

If an invariant fails, the evaluation should report an error rather than
silently producing results.

------------------------------------------------------------------------

# 56. Submission Readiness

The final project should support creation of:

### Public GitHub repository

Containing clean, reproducible code.

### 5-minute pitch video

Centered on the Incident Simulator.

### Architecture presentation

Showing:

``` text
Detect
→ Diagnose
→ Decide
→ Guardrail
→ Execute
→ Verify
→ Measure
```

### Quantitative evidence

Showing actual evaluation results.

------------------------------------------------------------------------

# 57. Final Product Positioning

RecoverAI should be positioned as:

> **An autonomous, bounded revenue-recovery agent that turns payment
> degradation into measurable recovery actions.**

The product's differentiation is not merely the use of an LLM.

The differentiation is the complete controlled loop:

``` text
Detection
+
Root Cause
+
Agentic Decision
+
Financial Guardrails
+
Execution
+
Verification
+
Measured Revenue Recovery
```

------------------------------------------------------------------------

# 58. Core Product Principle

The system should optimize for:

``` text
MAXIMIZE

Recoverable Revenue

WHILE MINIMIZING

Unnecessary Actions
+
Unsafe Actions
+
Repeated Actions
+
Unsupported Decisions
```

This principle should be reflected in the agent, policy engine,
evaluation metrics, UI, README, and final pitch.

------------------------------------------------------------------------

# 59. Final One-Sentence Definition

> **RecoverAI is an AI-powered payment recovery agent that detects
> revenue-threatening payment degradation, diagnoses its root cause,
> chooses and executes bounded recovery actions under deterministic
> financial guardrails, and proves its effectiveness through
> reproducible revenue-recovery evaluation.**

------------------------------------------------------------------------

# 60. Source of Truth

This PRD is the primary product and implementation specification for
RecoverAI.

Any implementation decision should be evaluated against:

1.  Razorpay Track 03 requirements.
2.  This PRD.
3.  Safety and correctness.
4.  Demonstrable measurable business value.
5.  Time-constrained MVP feasibility.

When requirements conflict, preserve the core objective:

> **Build the smallest complete system that convincingly demonstrates
> safe, measurable, agentic revenue recovery.**
