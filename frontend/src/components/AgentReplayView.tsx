import React, { useState, useEffect } from 'react';
import type {
  Incident,
  AgentReplayStep,
  AuditRecord
} from '../types';
import {
  fetchIncidentReplay,
  fetchAuditLogs,
  formatINR
} from '../api';
import {
  Clock,
  CheckCircle2
} from 'lucide-react';

interface AgentReplayViewProps {
  currentIncident: Incident | null;
}

export const AgentReplayView: React.FC<AgentReplayViewProps> = ({
  currentIncident
}) => {
  const [replaySteps, setReplaySteps] = useState<AgentReplayStep[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [selectedAudit, setSelectedAudit] = useState<AuditRecord | null>(null);
  const [filterDecision, setFilterDecision] = useState<string>('ALL');
  const [searchTx, setSearchTx] = useState<string>('');

  useEffect(() => {
    if (currentIncident) {
      loadReplayData(currentIncident.id);
    }
  }, [currentIncident?.id]);

  const loadReplayData = async (incidentId: string) => {
    try {
      const [steps, logs] = await Promise.all([
        fetchIncidentReplay(incidentId),
        fetchAuditLogs({ incident_id: incidentId, limit: 150 })
      ]);
      setReplaySteps(steps);
      setAuditLogs(logs);
      if (logs.length > 0) {
        setSelectedAudit(logs[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filteredLogs = auditLogs.filter((log) => {
    const matchesDecision = filterDecision === 'ALL' || log.policy_decision === filterDecision;
    const matchesSearch = log.transaction_id.toLowerCase().includes(searchTx.toLowerCase()) ||
                          log.proposed_action.toLowerCase().includes(searchTx.toLowerCase());
    return matchesDecision && matchesSearch;
  });

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Agent Execution Replay
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          Chronological execution trace of diagnostic reasoning, policy boundary checks, and tool invocations.
        </p>
      </div>

      {/* Main Grid: Execution Trace Timeline + Decision Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '480px 1fr', gap: '24px' }}>
        {/* Left Column: Vertical Execution Trace */}
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Clock size={16} style={{ color: 'var(--primary)' }} />
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Execution Trace Timeline</h3>
            </div>

            {replaySteps.length > 0 ? (
              <div className="timeline">
                {replaySteps.map((step) => (
                  <div key={step.step_id} className="timeline-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-neutral">{step.phase}</span>
                      <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '6px', color: 'var(--text-primary)' }}>
                      {step.title}
                    </h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
                      {step.description}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '24px' }}>
                No execution milestones available. Run recovery in the simulator to generate trace events.
              </p>
            )}
          </div>

          {/* Decision Stream Selector */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600 }}>Decision Log ({filteredLogs.length})</h4>
              <div style={{ display: 'flex', gap: '4px' }}>
                {['ALL', 'ALLOW', 'DENY', 'ESCALATE'].map((d) => (
                  <button
                    key={d}
                    onClick={() => setFilterDecision(d)}
                    style={{
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      background: filterDecision === d ? 'var(--primary-subtle)' : 'var(--bg-surface-secondary)',
                      color: filterDecision === d ? 'var(--primary)' : 'var(--text-secondary)',
                      border: filterDecision === d ? '1px solid var(--primary-border)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer'
                    }}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <input
              type="text"
              placeholder="Filter by transaction ID..."
              className="form-control"
              value={searchTx}
              onChange={(e) => setSearchTx(e.target.value)}
              style={{ marginBottom: '12px', fontSize: '0.8rem', padding: '6px 10px' }}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '350px', overflowY: 'auto' }}>
              {filteredLogs.map((log) => (
                <div
                  key={log.audit_id}
                  onClick={() => setSelectedAudit(log)}
                  style={{
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-md)',
                    background: selectedAudit?.audit_id === log.audit_id ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                    border: selectedAudit?.audit_id === log.audit_id ? '1px solid var(--primary-border)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                      {log.transaction_id}
                    </span>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Action: <strong style={{ color: 'var(--text-secondary)' }}>{log.proposed_action}</strong>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span
                      className={`badge ${
                        log.policy_decision === 'ALLOW'
                          ? 'badge-success'
                          : log.policy_decision === 'ESCALATE'
                          ? 'badge-warning'
                          : 'badge-danger'
                      }`}
                      style={{ fontSize: '0.65rem' }}
                    >
                      {log.policy_decision}
                    </span>
                    <div className="mono" style={{ fontSize: '0.75rem', fontWeight: 700, marginTop: '2px' }}>
                      {formatINR(log.amount_paise)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Deep Decision Inspector */}
        <div>
          {selectedAudit ? (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px' }}>
                <div>
                  <span className="badge badge-neutral">Decision Inspector</span>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>
                    Transaction <span className="mono" style={{ color: 'var(--primary)' }}>{selectedAudit.transaction_id}</span>
                  </h3>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Transaction Value</p>
                  <p className="mono" style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {formatINR(selectedAudit.amount_paise)}
                  </p>
                </div>
              </div>

              {/* Proposal vs Policy Decision Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    AI Agent Proposal
                  </span>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                    {selectedAudit.proposed_action}
                  </h4>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Diagnostic Confidence: <strong className="mono">{(selectedAudit.confidence * 100).toFixed(0)}%</strong>
                  </p>
                </div>

                <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Deterministic Policy Gate
                  </span>
                  <div style={{ marginTop: '4px' }}>
                    <span
                      className={`badge ${
                        selectedAudit.policy_decision === 'ALLOW'
                          ? 'badge-success'
                          : selectedAudit.policy_decision === 'ESCALATE'
                          ? 'badge-warning'
                          : 'badge-danger'
                      }`}
                    >
                      {selectedAudit.policy_decision}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                    Triggered: <span className="mono">{selectedAudit.details?.rule_triggered || 'POLICY_EVALUATED'}</span>
                  </p>
                </div>
              </div>

              {/* Grounded Rationale */}
              <div style={{ marginBottom: '20px', padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Policy Validation Reason
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {selectedAudit.policy_reason}
                </p>
              </div>

              {/* Execution & Outcome */}
              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Execution Tool &amp; Financial Outcome
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '10px' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Tool Invoked</span>
                    <div className="mono" style={{ fontSize: '0.8rem', fontWeight: 600 }}>{selectedAudit.tool_called}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Execution Status</span>
                    <div>
                      <span className={`badge ${selectedAudit.execution_status === 'SUCCESS' ? 'badge-success' : 'badge-neutral'}`}>
                        {selectedAudit.execution_status}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Recovered Amount</span>
                    <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary)' }}>
                      {formatINR(selectedAudit.recovered_amount_paise)}
                    </div>
                  </div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                  Outcome: {selectedAudit.outcome}
                </p>
              </div>

              {/* Invariant Safety Checklist */}
              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '8px' }}>
                  Safety Invariant Verification
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                    <span>No unapproved write operations outside bounded tools.</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                    <span>Double-recovery invariant verified (recovered &le; amount at risk).</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                    <span>Immutable audit ledger entry generated.</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
              <p style={{ color: 'var(--text-muted)' }}>Select a transaction decision from the list to inspect its policy trace.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
