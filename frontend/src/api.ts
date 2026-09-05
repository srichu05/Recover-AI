import type {
  DashboardSummary,
  Incident,
  Transaction,
  AuditRecord,
  AgentReplayStep,
  EvaluationSummary
} from './types';

const API_BASE = '/api';

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function createIncident(data: {
  title?: string;
  incident_type: string;
  payment_method: string;
  severity_pct: number;
  affected_count: number;
  random_seed?: number;
}): Promise<Incident> {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create incident');
  return res.json();
}

export async function fetchIncidentDetail(incidentId: string): Promise<{
  incident: Incident;
  health_points: Array<{ time: string; success_rate: number; state: string }>;
  total_transactions: number;
  failed_count: number;
  recovered_count: number;
  escalated_count: number;
  replay_steps: AgentReplayStep[];
}> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
  if (!res.ok) throw new Error('Failed to fetch incident detail');
  return res.json();
}

export async function executeIncidentRecovery(
  incidentId: string,
  seed: number = 42
): Promise<{
  incident_id: string;
  status: string;
  revenue_at_risk_paise: number;
  recoverai_recovered_paise: number;
  baseline_recovered_paise: number;
  recoverai_recovery_rate: number;
  baseline_recovery_rate: number;
  improvement_pct: number;
  successful_recoveries: number;
  escalations: number;
  policy_stops: number;
  replay_steps: AgentReplayStep[];
  root_cause?: string;
  root_cause_confidence: number;
  root_cause_evidence: string[];
}> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/recover?seed=${seed}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to execute recovery');
  return res.json();
}

export async function fetchIncidentReplay(incidentId: string): Promise<AgentReplayStep[]> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/replay`);
  if (!res.ok) throw new Error('Failed to fetch incident replay');
  return res.json();
}

export async function fetchTransactions(params?: {
  limit?: number;
  incident_id?: string;
  status?: string;
  payment_method?: string;
}): Promise<Transaction[]> {
  const query = new URLSearchParams();
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.incident_id) query.append('incident_id', params.incident_id);
  if (params?.status) query.append('status', params.status);
  if (params?.payment_method) query.append('payment_method', params.payment_method);

  const res = await fetch(`${API_BASE}/transactions?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch transactions');
  return res.json();
}

export async function fetchAuditLogs(params?: {
  incident_id?: string;
  transaction_id?: string;
  limit?: number;
}): Promise<AuditRecord[]> {
  const query = new URLSearchParams();
  if (params?.incident_id) query.append('incident_id', params.incident_id);
  if (params?.transaction_id) query.append('transaction_id', params.transaction_id);
  if (params?.limit) query.append('limit', params.limit.toString());

  const res = await fetch(`${API_BASE}/audit-logs?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

export async function runEvaluation(seed: number = 42): Promise<EvaluationSummary> {
  const res = await fetch(`${API_BASE}/evaluation/run?seed=${seed}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to run evaluation');
  return res.json();
}

export async function fetchEvaluationResults(): Promise<EvaluationSummary> {
  const res = await fetch(`${API_BASE}/evaluation/results`);
  if (!res.ok) throw new Error('Failed to fetch evaluation results');
  return res.json();
}

export function formatINR(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2
  }).format(rupees);
}
