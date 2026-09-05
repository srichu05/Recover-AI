import React, { useState, useEffect } from 'react';
import type {
  Incident,
  Transaction
} from '../types';
import {
  fetchIncidentDetail,
  fetchTransactions,
  formatINR
} from '../api';

interface IncidentDetailViewProps {
  currentIncident: Incident | null;
  incidents: Incident[];
  onSelectIncident: (inc: Incident) => void;
  setActiveTab: (tab: string) => void;
}

export const IncidentDetailView: React.FC<IncidentDetailViewProps> = ({
  currentIncident,
  incidents,
  onSelectIncident,
  setActiveTab
}) => {
  const activeInc = currentIncident || (incidents.length > 0 ? incidents[0] : null);

  const [detailData, setDetailData] = useState<any>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  useEffect(() => {
    if (activeInc) {
      loadIncidentData(activeInc.id);
    }
  }, [activeInc?.id]);

  const loadIncidentData = async (incidentId: string) => {
    try {
      const [detail, txs] = await Promise.all([
        fetchIncidentDetail(incidentId),
        fetchTransactions({ incident_id: incidentId, limit: 300 })
      ]);
      setDetailData(detail);
      setTransactions(txs);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredTxs = transactions.filter((t) => {
    return statusFilter === 'ALL' || t.status === statusFilter;
  });

  if (!activeInc) {
    return (
      <div style={{ maxWidth: '1200px', margin: '40px auto', textAlign: 'center' }}>
        <h3>No Incident Selected</h3>
        <button className="btn btn-primary" onClick={() => setActiveTab('simulator')} style={{ marginTop: '16px' }}>
          Go to Incident Simulator
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Incident Switcher & Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-neutral">{activeInc.payment_method}</span>
            <span className={`badge ${activeInc.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}`}>
              {activeInc.status}
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '6px' }}>{activeInc.title}</h1>
          <p className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Incident #{activeInc.id} &bull; Detected {new Date(activeInc.created_at).toLocaleTimeString()}
          </p>
        </div>

        {incidents.length > 1 && (
          <select
            className="form-control mono"
            value={activeInc.id}
            onChange={(e) => {
              const selected = incidents.find((i) => i.id === e.target.value);
              if (selected) onSelectIncident(selected);
            }}
            style={{ maxWidth: '300px' }}
          >
            {incidents.map((i) => (
              <option key={i.id} value={i.id}>
                {i.title} ({i.severity})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Financial Story Metric Cards */}
      <div className="kpi-grid" style={{ marginBottom: '24px' }}>
        <div className="kpi-card">
          <span className="kpi-label">Revenue at Risk</span>
          <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>
            {formatINR(activeInc.revenue_at_risk_paise)}
          </p>
          <div className="kpi-sub">
            <span>{activeInc.affected_count} affected transactions</span>
          </div>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Affected Transactions</span>
          <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>
            {activeInc.affected_count}
          </p>
          <div className="kpi-sub">
            <span>Payment drop: -{activeInc.degradation_pct.toFixed(1)}%</span>
          </div>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Recovered Revenue</span>
          <p className="kpi-value mono" style={{ color: 'var(--primary)' }}>
            {formatINR(activeInc.actual_recovered_paise)}
          </p>
          <div className="kpi-sub">
            <span>
              {activeInc.revenue_at_risk_paise > 0
                ? ((activeInc.actual_recovered_paise / activeInc.revenue_at_risk_paise) * 100).toFixed(1)
                : 0}% recovery rate
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Static Baseline Rec.</span>
          <p className="kpi-value mono" style={{ color: 'var(--text-secondary)' }}>
            {formatINR(activeInc.baseline_recovered_paise)}
          </p>
          <div className="kpi-sub">
            <span style={{ color: 'var(--success)', fontWeight: 600 }}>
              {activeInc.actual_recovered_paise > activeInc.baseline_recovered_paise && activeInc.baseline_recovered_paise > 0
                ? `+${(((activeInc.actual_recovered_paise - activeInc.baseline_recovered_paise) / activeInc.baseline_recovered_paise) * 100).toFixed(1)}% improvement`
                : 'Identical batch'}
            </span>
          </div>
        </div>
      </div>

      {/* Degradation Telemetry + Root Cause Diagnosis */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 440px', gap: '24px', marginBottom: '24px' }}>
        {/* Telemetry Bar Chart */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Success Rate Telemetry</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real-time Gateway Polling</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '160px', padding: '16px 12px', background: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            {detailData?.health_points?.map((pt: any, idx: number) => {
              const heightPct = Math.max(15, (pt.success_rate / 100) * 120);
              const isDrop = pt.state === 'DEGRADING' || pt.state === 'INCIDENT_PEAK' || pt.state === 'CRITICAL';
              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 1 }}>
                  <span className="mono" style={{ fontSize: '0.72rem', color: isDrop ? 'var(--danger)' : 'var(--text-primary)', fontWeight: 700 }}>
                    {pt.success_rate.toFixed(1)}%
                  </span>
                  <div
                    style={{
                      width: '24px',
                      height: `${heightPct}px`,
                      borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                      background: isDrop ? 'var(--danger)' : 'var(--primary)',
                      opacity: isDrop ? 0.9 : 0.8
                    }}
                  />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>{pt.time}</span>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '14px', fontSize: '0.8rem' }}>
            <div>Baseline Health: <strong className="mono">{activeInc.baseline_success_rate}%</strong></div>
            <div>Degradation: <strong className="mono" style={{ color: 'var(--danger)' }}>-{activeInc.degradation_pct.toFixed(1)}%</strong></div>
            <div>Incident Success Rate: <strong className="mono" style={{ color: 'var(--warning)' }}>{activeInc.current_success_rate}%</strong></div>
          </div>
        </div>

        {/* Root Cause & Interventions */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Root Cause Analysis</h3>
            <span className="badge badge-neutral">
              {Math.round((activeInc.root_cause_confidence || 0.9) * 100)}% Confidence
            </span>
          </div>

          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            {activeInc.root_cause || 'Transient Gateway Degradation'}
          </h4>

          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
            Diagnostic Evidence:
          </p>
          <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {activeInc.root_cause_evidence?.length ? (
              activeInc.root_cause_evidence.map((ev, i) => <li key={i}>{ev}</li>)
            ) : (
              <>
                <li>Elevated failure rate isolated to UPI payment rail.</li>
                <li>Cards and Netbanking processing near healthy baseline.</li>
                <li>Failure category dominated by transient upstream timeout code.</li>
              </>
            )}
          </ul>

          <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Recommended Intervention:
            </span>
            <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
              Segment cohort &rarr; Apply smart retry with exponential backoff &rarr; Route high-value to ops &rarr; Block permanent declines.
            </p>
          </div>
        </div>
      </div>

      {/* Cohort Transactions Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Cohort Transactions ({transactions.length})</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Inspect individual payment amounts, customer history, failure categories, and recovery outcomes.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'FAILED', 'RECOVERED', 'ESCALATED'].map((s) => (
              <button
                key={s}
                className={`btn ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setStatusFilter(s)}
                style={{ padding: '5px 10px', fontSize: '0.75rem' }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th className="text-right">Amount</th>
                <th>Method / Provider</th>
                <th>Failure Reason</th>
                <th>Customer Score</th>
                <th>Retries</th>
                <th>Status</th>
                <th className="text-right">Recovered</th>
              </tr>
            </thead>
            <tbody>
              {filteredTxs.slice(0, 50).map((tx) => (
                <tr key={tx.id}>
                  <td className="mono" style={{ fontSize: '0.78rem', color: 'var(--primary)' }}>
                    {tx.id}
                  </td>
                  <td className="mono text-right" style={{ fontWeight: 600 }}>
                    {formatINR(tx.amount_paise)}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem' }}>{tx.payment_method}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>{tx.provider}</span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontSize: '0.78rem', color: tx.is_transient ? 'var(--warning)' : 'var(--text-muted)' }}>
                      {tx.failure_reason || 'SUCCESS'}
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontSize: '0.8rem' }}>
                      {(tx.customer_success_rate * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="mono">{tx.retry_count}</td>
                  <td>
                    <span
                      className={`badge ${
                        tx.status === 'RECOVERED'
                          ? 'badge-success'
                          : tx.status === 'ESCALATED'
                          ? 'badge-warning'
                          : tx.status === 'FAILED'
                          ? 'badge-danger'
                          : 'badge-neutral'
                      }`}
                    >
                      {tx.status}
                    </span>
                  </td>
                  <td className="mono text-right" style={{ fontWeight: 700, color: tx.recovered_amount_paise > 0 ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {formatINR(tx.recovered_amount_paise)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
