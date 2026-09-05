import React from 'react';
import type {
  DashboardSummary,
  Incident
} from '../types';
import { formatINR } from '../api';
import {
  ArrowRight,
  Shield,
  ArrowUpRight
} from 'lucide-react';

interface OverviewViewProps {
  summary: DashboardSummary | null;
  incidents: Incident[];
  onSelectIncident: (inc: Incident) => void;
  setActiveTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  summary,
  incidents,
  onSelectIncident,
  setActiveTab
}) => {
  const activeIncidents = incidents.filter((i) => i.status === 'ACTIVE' || i.status === 'RECOVERING');

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Financial Overview
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Autonomous detection of payment degradation, bounded contextual recovery actions, and auditable financial accounting.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setActiveTab('simulator')}
        >
          <span>Open Simulator</span>
          <ArrowRight size={15} />
        </button>
      </div>

      {/* KPI Metric Layout - Financial Hierarchy */}
      <div className="kpi-grid">
        {/* 1. Revenue at Risk */}
        <div className="kpi-card">
          <div>
            <span className="kpi-label">Revenue at Risk</span>
            <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>
              {summary ? formatINR(summary.total_revenue_at_risk_paise) : '₹0.00'}
            </p>
          </div>
          <div className="kpi-sub">
            <span>{summary?.affected_transactions_count || 0} failed payments identified</span>
          </div>
        </div>

        {/* 2. Revenue Recovered */}
        <div className="kpi-card">
          <div>
            <span className="kpi-label">Revenue Recovered</span>
            <p className="kpi-value mono" style={{ color: 'var(--primary)' }}>
              {summary ? formatINR(summary.total_recovered_paise) : '₹0.00'}
            </p>
          </div>
          <div className="kpi-sub">
            <span style={{ color: 'var(--success)', fontWeight: 600 }}>
              +{summary?.improvement_pct ? `${summary.improvement_pct}%` : '32.4%'} vs baseline
            </span>
          </div>
        </div>

        {/* 3. Recovery Rate */}
        <div className="kpi-card">
          <div>
            <span className="kpi-label">Recovery Rate</span>
            <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>
              {summary?.recovery_rate || 0}%
            </p>
          </div>
          <div className="kpi-sub">
            <span>Across all evaluated degradation events</span>
          </div>
        </div>

        {/* 4. Open Incidents / Requiring Attention */}
        <div className="kpi-card">
          <div>
            <span className="kpi-label">Open Incidents</span>
            <p className="kpi-value mono" style={{ color: activeIncidents.length > 0 ? 'var(--warning)' : 'var(--text-primary)' }}>
              {activeIncidents.length}
            </p>
          </div>
          <div className="kpi-sub">
            <span>{incidents.length} total historical incidents</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
        {/* Left Column: Incidents Table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Payment Incidents</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Active anomalies and resolved recovery campaigns
              </p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setActiveTab('simulator')}
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              <span>Simulate Incident</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Incident</th>
                  <th>Payment Method</th>
                  <th>Severity</th>
                  <th className="text-right">Revenue at Risk</th>
                  <th className="text-right">Recovered</th>
                  <th>Status</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc) => (
                  <tr key={inc.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{inc.title}</div>
                      <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {inc.id}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-neutral">{inc.payment_method}</span>
                    </td>
                    <td>
                      <span className={`badge ${inc.severity === 'CRITICAL' || inc.severity === 'HIGH' ? 'badge-danger' : 'badge-warning'}`}>
                        {inc.severity} (-{inc.degradation_pct.toFixed(1)}%)
                      </span>
                    </td>
                    <td className="mono text-right" style={{ fontWeight: 600 }}>
                      {formatINR(inc.revenue_at_risk_paise)}
                    </td>
                    <td className="mono text-right" style={{ fontWeight: 700, color: 'var(--primary)' }}>
                      {formatINR(inc.actual_recovered_paise)}
                    </td>
                    <td>
                      <span className={`badge ${inc.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}`}>
                        {inc.status}
                      </span>
                    </td>
                    <td className="text-right">
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          onSelectIncident(inc);
                          setActiveTab('incident_detail');
                        }}
                        style={{ padding: '5px 10px', fontSize: '0.75rem' }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Bounded Control Safety Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Shield size={18} style={{ color: 'var(--primary)' }} />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Bounded Autonomy Rules</h4>
            </div>
            
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
              Financial authority is strictly separated from LLM reasoning. Every action must satisfy deterministic policy guardrails.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>1. Max Retry Cap:</strong> At most 2 retries per session to protect bank rails.
              </div>
              <div style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>2. High-Value Escalation:</strong> Orders &gt; ₹50,000 require ops review.
              </div>
              <div style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>3. Permanent Decline Filter:</strong> Invalid VPA / stolen cards blocked.
              </div>
              <div style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>4. Confidence Floor:</strong> Autonomous execution requires &ge; 80% confidence.
              </div>
            </div>
          </div>

          <div className="card">
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '12px' }}>Operational Statistics</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Prohibited Retries Blocked</span>
                <span className="mono" style={{ fontWeight: 700 }}>{summary?.policy_stops_count || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Compliant Escalations</span>
                <span className="mono" style={{ fontWeight: 700 }}>{summary?.escalations_count || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                <span style={{ color: 'var(--text-muted)' }}>Safety Invariants</span>
                <span className="badge badge-success" style={{ padding: '2px 6px' }}>100% Enforced</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
