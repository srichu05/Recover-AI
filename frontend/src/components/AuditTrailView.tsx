import React, { useState, useEffect } from 'react';
import type { AuditRecord } from '../types';
import { fetchAuditLogs, formatINR } from '../api';
import {
  Search,
  Download
} from 'lucide-react';

interface AuditTrailViewProps {
  currentIncidentId?: string;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ currentIncidentId }) => {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [filterDecision, setFilterDecision] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    loadLogs();
  }, [currentIncidentId]);

  const loadLogs = async () => {
    try {
      const data = await fetchAuditLogs({ incident_id: currentIncidentId, limit: 300 });
      setLogs(data);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredLogs = logs.filter((log) => {
    const matchesDecision = filterDecision === 'ALL' || log.policy_decision === filterDecision;
    const matchesSearch =
      log.transaction_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.proposed_action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.tool_called.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.policy_reason.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDecision && matchesSearch;
  });

  const exportCSV = () => {
    const headers = [
      'Timestamp',
      'Audit ID',
      'Transaction ID',
      'Proposed Action',
      'Confidence',
      'Policy Decision',
      'Policy Reason',
      'Tool Called',
      'Execution Status',
      'Outcome',
      'Amount (INR)',
      'Recovered (INR)'
    ];

    const rows = filteredLogs.map((l) => [
      l.timestamp,
      l.audit_id,
      l.transaction_id,
      l.proposed_action,
      l.confidence,
      l.policy_decision,
      `"${l.policy_reason.replace(/"/g, '""')}"`,
      l.tool_called,
      l.execution_status,
      `"${l.outcome.replace(/"/g, '""')}"`,
      (l.amount_paise / 100).toFixed(2),
      (l.recovered_amount_paise / 100).toFixed(2)
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `recoverai_audit_trail_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Header & Export */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Financial Audit Trail
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Immutable append-only record of all candidate recovery proposals, deterministic guardrail verdicts, and settlement results.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={exportCSV}>
          <Download size={14} />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '14px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <Search size={15} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by transaction ID, action, rule, or tool..."
              className="form-control"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', maxWidth: '420px' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Policy Gate:</span>
            {['ALL', 'ALLOW', 'DENY', 'ESCALATE'].map((d) => (
              <button
                key={d}
                className={`btn ${filterDecision === d ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilterDecision(d)}
                style={{ padding: '5px 10px', fontSize: '0.75rem' }}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Transaction ID</th>
                <th>Action</th>
                <th>Confidence</th>
                <th>Policy Verdict</th>
                <th>Validation Rule</th>
                <th>Tool</th>
                <th>Status</th>
                <th className="text-right">Amount</th>
                <th className="text-right">Recovered</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.audit_id}>
                  <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="mono" style={{ fontSize: '0.78rem', color: 'var(--primary)', fontWeight: 600 }}>
                    {log.transaction_id}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                      {log.proposed_action}
                    </span>
                  </td>
                  <td>
                    <span className="mono" style={{ fontSize: '0.8rem' }}>
                      {(log.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        log.policy_decision === 'ALLOW'
                          ? 'badge-success'
                          : log.policy_decision === 'ESCALATE'
                          ? 'badge-warning'
                          : 'badge-danger'
                      }`}
                    >
                      {log.policy_decision}
                    </span>
                  </td>
                  <td style={{ maxWidth: '260px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {log.policy_reason}
                  </td>
                  <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {log.tool_called}
                  </td>
                  <td>
                    <span className={`badge ${log.execution_status === 'SUCCESS' ? 'badge-success' : 'badge-neutral'}`}>
                      {log.execution_status}
                    </span>
                  </td>
                  <td className="mono text-right" style={{ fontWeight: 600 }}>
                    {formatINR(log.amount_paise)}
                  </td>
                  <td className="mono text-right" style={{ fontWeight: 700, color: log.recovered_amount_paise > 0 ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {formatINR(log.recovered_amount_paise)}
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
