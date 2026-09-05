export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  success_rate: number;
  payment_count: number;
  failure_count: number;
  is_high_value: boolean;
}

export interface Transaction {
  id: string;
  merchant_id: string;
  customer_id: string;
  timestamp: string;
  amount_paise: number;
  currency: string;
  payment_method: string;
  provider: string;
  bank: string;
  status: "SUCCESS" | "FAILED" | "RECOVERED" | "ESCALATED" | "PENDING";
  failure_reason?: string;
  failure_category?: string;
  is_transient: boolean;
  retry_count: number;
  cart_value_paise: number;
  customer_success_rate: number;
  customer_payment_count: number;
  customer_failure_count: number;
  ground_truth_recovery_prob: number;
  is_recovered: boolean;
  recovered_amount_paise: number;
  incident_id?: string;
  customer_declined: boolean;
}

export interface Incident {
  id: string;
  title: string;
  incident_type: string;
  payment_method: string;
  status: "ACTIVE" | "INVESTIGATING" | "RECOVERING" | "RESOLVED";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  severity_pct: number;
  affected_count: number;
  baseline_success_rate: number;
  current_success_rate: number;
  degradation_pct: number;
  total_volume_paise: number;
  revenue_at_risk_paise: number;
  estimated_recoverable_paise: number;
  actual_recovered_paise: number;
  baseline_recovered_paise: number;
  root_cause?: string;
  root_cause_confidence: number;
  root_cause_evidence: string[];
  created_at: string;
  resolved_at?: string;
  metadata?: Record<string, any>;
}

export interface AuditRecord {
  audit_id: string;
  timestamp: string;
  incident_id: string;
  transaction_id: string;
  agent_run_id: string;
  proposed_action: string;
  confidence: number;
  policy_decision: "ALLOW" | "DENY" | "ESCALATE";
  policy_reason: string;
  tool_called: string;
  execution_status: "SUCCESS" | "FAILURE" | "SKIPPED" | "ESCALATED" | "BLOCKED";
  outcome: string;
  amount_paise: number;
  recovered_amount_paise: number;
  details: Record<string, any>;
}

export interface AgentReplayStep {
  step_id: string;
  step_number: number;
  timestamp: string;
  phase: string;
  title: string;
  description: string;
  metadata: Record<string, any>;
}

export interface ScenarioResult {
  scenario_id: string;
  scenario_name: string;
  description: string;
  total_transactions: number;
  revenue_at_risk_paise: number;
  baseline_actions: number;
  baseline_recovered_paise: number;
  baseline_recovery_rate: number;
  recoverai_actions: number;
  recoverai_recovered_paise: number;
  recoverai_recovery_rate: number;
  improvement_pct: number;
  successful_recoveries: number;
  failed_actions: number;
  escalations: number;
  policy_stops: number;
  prohibited_retries_prevented: number;
  duplicate_actions_prevented: number;
  high_value_escalations: number;
  invariants_passed: boolean;
}

export interface EvaluationSummary {
  dataset_size: number;
  total_transaction_value_paise: number;
  revenue_at_risk_paise: number;
  baseline_actions: number;
  baseline_recovered_paise: number;
  baseline_recovery_rate: number;
  recoverai_actions: number;
  recoverai_recovered_paise: number;
  recoverai_recovery_rate: number;
  improvement_pct: number;
  successful_recoveries: number;
  failed_recoveries: number;
  escalations: number;
  policy_stops: number;
  duplicate_actions_prevented: number;
  prohibited_retries_prevented: number;
  high_value_escalations: number;
  scenarios: ScenarioResult[];
  generated_at: string;
  invariants_passed: boolean;
}

export interface DashboardSummary {
  total_revenue_at_risk_paise: number;
  total_recovered_paise: number;
  total_baseline_recovered_paise: number;
  recovery_rate: number;
  improvement_pct: number;
  active_incidents_count: number;
  resolved_incidents_count: number;
  total_transactions_count: number;
  affected_transactions_count: number;
  successful_recoveries_count: number;
  escalations_count: number;
  policy_stops_count: number;
}
