import React, { useState } from 'react';
import type { Incident } from '../types';
import {
  createIncident,
  executeIncidentRecovery,
  formatINR
} from '../api';
import {
  Sliders,
  Play,
  CheckCircle,
  ArrowRight,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';

interface SimulatorViewProps {
  incidents: Incident[];
  currentIncident: Incident | null;
  setCurrentIncident: (inc: Incident | null) => void;
  onRefresh: () => void;
  setActiveTab: (tab: string) => void;
}

export const SimulatorView: React.FC<SimulatorViewProps> = ({
  incidents,
  currentIncident,
  setCurrentIncident,
  onRefresh,
  setActiveTab
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('UPI_TIMEOUT_SPIKE');
  const [severityPct, setSeverityPct] = useState<number>(70);
  const [affectedCount, setAffectedCount] = useState<number>(500);
  const [paymentMethod, setPaymentMethod] = useState<string>('UPI');
  const [randomSeed, setRandomSeed] = useState<number>(42);

  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isRunningRecovery, setIsRunningRecovery] = useState<boolean>(false);
  const [lastRecoveryResult, setLastRecoveryResult] = useState<any>(null);

  const handlePresetSelect = (preset: string) => {
    setSelectedPreset(preset);
    if (preset === 'UPI_TIMEOUT_SPIKE') {
      setPaymentMethod('UPI');
      setSeverityPct(70);
      setAffectedCount(500);
    } else if (preset === 'PROVIDER_OUTAGE') {
      setPaymentMethod('CARD');
      setSeverityPct(60);
      setAffectedCount(400);
    } else if (preset === 'BANK_SWITCH_DEGRADATION') {
      setPaymentMethod('NETBANKING');
      setSeverityPct(50);
      setAffectedCount(350);
    } else if (preset === 'MIXED_FAILURE_INCIDENT') {
      setPaymentMethod('ALL');
      setSeverityPct(65);
      setAffectedCount(500);
    }
  };

  const handleCreateIncident = async () => {
    setIsGenerating(true);
    try {
      const newInc = await createIncident({
        incident_type: selectedPreset,
        payment_method: paymentMethod,
        severity_pct: severityPct,
        affected_count: affectedCount,
        random_seed: randomSeed
      });
      setCurrentIncident(newInc);
      setLastRecoveryResult(null);
      onRefresh();
    } catch (err) {
      alert('Error creating incident: ' + err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunRecovery = async () => {
    if (!currentIncident) return;
    setIsRunningRecovery(true);
    try {
      const res = await executeIncidentRecovery(currentIncident.id, randomSeed);
      setLastRecoveryResult(res);
      setCurrentIncident({
        ...currentIncident,
        status: 'RESOLVED',
        actual_recovered_paise: res.recoverai_recovered_paise,
        baseline_recovered_paise: res.baseline_recovered_paise,
        root_cause: res.root_cause,
        root_cause_confidence: res.root_cause_confidence,
        root_cause_evidence: res.root_cause_evidence
      });
      onRefresh();
    } catch (err) {
      alert('Error running recovery: ' + err);
    } finally {
      setIsRunningRecovery(false);
    }
  };

  const activeInc = currentIncident || (incidents.length > 0 ? incidents[0] : null);

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Incident Simulator
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          Simulate payment rail degradation scenarios, evaluate revenue at risk, and execute contextual recovery.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Left: Scenario Configuration */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Sliders size={18} style={{ color: 'var(--primary)' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Scenario Configuration</h3>
          </div>

          {/* Scenario Type Selection */}
          <div className="form-group">
            <label className="form-label">Scenario Type</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {[
                { id: 'UPI_TIMEOUT_SPIKE', name: 'UPI Gateway Timeout Spike', method: 'UPI' },
                { id: 'PROVIDER_OUTAGE', name: 'ICICI Provider Network Drop', method: 'CARD' },
                { id: 'BANK_SWITCH_DEGRADATION', name: 'SBI Bank Switch Congestion', method: 'NETBANKING' },
                { id: 'MIXED_FAILURE_INCIDENT', name: 'Multi-Vector Payment Spike', method: 'ALL' }
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => handlePresetSelect(p.id)}
                  style={{
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'left',
                    background: selectedPreset === p.id ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                    border: selectedPreset === p.id ? '1px solid var(--primary-border)' : '1px solid var(--border-subtle)',
                    color: selectedPreset === p.id ? 'var(--primary)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontWeight: selectedPreset === p.id ? 700 : 500
                  }}
                >
                  <span style={{ fontSize: '0.82rem' }}>{p.name}</span>
                  <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>
                    {p.method}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Payment Method */}
          <div className="form-group">
            <label className="form-label">Payment Method</label>
            <select
              className="form-control"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
            >
              <option value="UPI">UPI</option>
              <option value="CARD">Card</option>
              <option value="NETBANKING">Netbanking</option>
              <option value="ALL">All Methods</option>
            </select>
          </div>

          {/* Severity */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label">Severity Drop</label>
              <span className="mono" style={{ fontSize: '0.82rem', fontWeight: 700 }}>
                {severityPct}%
              </span>
            </div>
            <input
              type="range"
              min={20}
              max={90}
              step={5}
              value={severityPct}
              onChange={(e) => setSeverityPct(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span>20% (Mild)</span>
              <span>60% (Moderate)</span>
              <span>90% (Critical)</span>
            </div>
          </div>

          {/* Transaction Volume */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label">Transaction Volume</label>
              <span className="mono" style={{ fontSize: '0.82rem', fontWeight: 700 }}>
                {affectedCount} txs
              </span>
            </div>
            <input
              type="range"
              min={100}
              max={1000}
              step={50}
              value={affectedCount}
              onChange={(e) => setAffectedCount(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Seed */}
          <div className="form-group">
            <label className="form-label">Seed (Reproducibility)</label>
            <input
              type="number"
              className="form-control mono"
              value={randomSeed}
              onChange={(e) => setRandomSeed(Number(e.target.value))}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={handleCreateIncident}
            disabled={isGenerating || isRunningRecovery}
            style={{ width: '100%', marginTop: '8px' }}
          >
            <span>{isGenerating ? 'Generating...' : 'Run Simulation'}</span>
          </button>
        </div>

        {/* Right: Generated Incident Summary & Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {activeInc ? (
            <>
              {/* Incident Header Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`badge ${activeInc.status === 'ACTIVE' ? 'badge-warning' : 'badge-success'}`}>
                        {activeInc.status === 'ACTIVE' ? 'Active Degradation' : 'Resolved'}
                      </span>
                      <span className="badge badge-neutral">{activeInc.payment_method}</span>
                      <span className="badge badge-neutral">{activeInc.severity}</span>
                    </div>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 700, marginTop: '8px' }}>
                      {activeInc.title}
                    </h2>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Incident ID: <span className="mono">{activeInc.id}</span>
                    </p>
                  </div>

                  <button
                    className="btn btn-primary"
                    onClick={handleRunRecovery}
                    disabled={isRunningRecovery || isGenerating || activeInc.status === 'RESOLVED'}
                    style={{ padding: '9px 18px' }}
                  >
                    <Play size={15} fill="currentColor" />
                    <span>{isRunningRecovery ? 'Executing Recovery...' : activeInc.status === 'RESOLVED' ? 'Recovery Completed' : 'Execute Recovery'}</span>
                  </button>
                </div>

                {/* 4 Clean Metric Summary Blocks */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginTop: '20px' }}>
                  <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Revenue at Risk</p>
                    <p className="mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                      {formatINR(activeInc.revenue_at_risk_paise)}
                    </p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {activeInc.affected_count} transactions
                    </p>
                  </div>

                  <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Failure Rate Drop</p>
                    <p className="mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--warning)', marginTop: '4px' }}>
                      -{activeInc.degradation_pct.toFixed(1)}%
                    </p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {activeInc.baseline_success_rate}% &rarr; {activeInc.current_success_rate}%
                    </p>
                  </div>

                  <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>RecoverAI Recovered</p>
                    <p className="mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)', marginTop: '4px' }}>
                      {formatINR(activeInc.actual_recovered_paise)}
                    </p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {activeInc.revenue_at_risk_paise > 0 ? ((activeInc.actual_recovered_paise / activeInc.revenue_at_risk_paise) * 100).toFixed(1) : 0}% recovery rate
                    </p>
                  </div>

                  <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Static Baseline</p>
                    <p className="mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {formatINR(activeInc.baseline_recovered_paise)}
                    </p>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Naive single retry
                    </p>
                  </div>
                </div>

                {/* Workflow Lifecycle Stepper */}
                <div style={{ marginTop: '24px', borderTop: '1px solid var(--border-subtle)', paddingTop: '18px' }}>
                  <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '12px' }}>
                    Control Boundary Lifecycle
                  </p>
                  <div className="step-track">
                    <div className="step-line" />
                    {[
                      { num: 1, label: 'Detect Anomaly', done: true },
                      { num: 2, label: 'Root Cause', done: true },
                      { num: 3, label: 'Segment Cohort', done: true },
                      { num: 4, label: 'Agent Proposes', done: activeInc.status === 'RESOLVED' || isRunningRecovery },
                      { num: 5, label: 'Policy Validates', done: activeInc.status === 'RESOLVED' || isRunningRecovery },
                      { num: 6, label: 'Tools Execute', done: activeInc.status === 'RESOLVED' },
                      { num: 7, label: 'Audit & Measure', done: activeInc.status === 'RESOLVED' }
                    ].map((st) => (
                      <div key={st.num} className={`step-item ${st.done ? (activeInc.status === 'RESOLVED' ? 'completed' : 'active') : ''}`}>
                        <div className="step-bubble">
                          {st.done && activeInc.status === 'RESOLVED' ? <CheckCircle size={16} /> : st.num}
                        </div>
                        <span className="step-label">{st.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Resolved Comparison & Evidence Section */}
              {activeInc.status === 'RESOLVED' && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <ShieldCheck size={18} style={{ color: 'var(--primary)' }} />
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Comparative Financial Results</h3>
                    </div>
                    <button
                      className="btn btn-secondary"
                      onClick={() => setActiveTab('agent_replay')}
                      style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                    >
                      <span>View Execution Replay</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    {/* Baseline */}
                    <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="badge badge-neutral">Static Baseline</span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Naive single retry</span>
                      </div>
                      <p className="mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '12px' }}>
                        {formatINR(activeInc.baseline_recovered_paise)}
                      </p>
                      <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        <div>Escalations: <strong className="mono">0</strong></div>
                        <div>Policy Stops: <strong className="mono">0</strong></div>
                      </div>
                    </div>

                    {/* RecoverAI */}
                    <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--primary-subtle)', border: '1px solid var(--primary-border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="badge badge-primary">RecoverAI Engine</span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--primary)', fontWeight: 600 }}>Bounded Autonomy</span>
                      </div>
                      <p className="mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary)', marginTop: '12px' }}>
                        {formatINR(activeInc.actual_recovered_paise)}
                      </p>
                      <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        <div>Escalations: <strong className="mono">{lastRecoveryResult?.escalations || 0}</strong></div>
                        <div>Policy Blocks: <strong className="mono">{lastRecoveryResult?.policy_stops || 0}</strong></div>
                      </div>
                    </div>
                  </div>

                  {/* Diagnostic Root Cause */}
                  {activeInc.root_cause && (
                    <div style={{ marginTop: '16px', padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          Root Cause Finding
                        </span>
                        <span className="badge badge-neutral">
                          {Math.round((activeInc.root_cause_confidence || 0.9) * 100)}% Confidence
                        </span>
                      </div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
                        {activeInc.root_cause}
                      </h4>
                      <ul style={{ marginTop: '8px', paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {activeInc.root_cause_evidence?.map((ev, i) => (
                          <li key={i} style={{ marginBottom: '3px' }}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
              <AlertCircle size={36} style={{ color: 'var(--text-muted)', margin: '0 auto 12px' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>No Active Incident</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                Select a scenario on the left and click "Run Simulation" to generate payment degradation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
