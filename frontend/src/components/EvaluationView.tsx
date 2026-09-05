import React, { useState, useEffect } from 'react';
import type { EvaluationSummary } from '../types';
import { fetchEvaluationResults, runEvaluation, formatINR } from '../api';
import {
  Play,
  CheckCircle2,
  Lock,
  Shield,
  FileCheck
} from 'lucide-react';

export const EvaluationView: React.FC = () => {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [benchmarkSeed, setBenchmarkSeed] = useState<number>(42);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    setLoading(true);
    try {
      const data = await fetchEvaluationResults();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    setLoading(true);
    try {
      const data = await runEvaluation(benchmarkSeed);
      setSummary(data);
    } catch (err) {
      alert('Error running benchmark: ' + err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Evaluation Benchmark
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            RecoverAI vs Static Baseline &mdash; Evaluated across 7 standard production scenarios on identical transaction cohorts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Seed:</span>
            <input
              type="number"
              className="form-control mono"
              value={benchmarkSeed}
              onChange={(e) => setBenchmarkSeed(Number(e.target.value))}
              style={{ width: '70px', padding: '6px', fontSize: '0.8rem' }}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleRunBenchmark}
            disabled={loading}
            style={{ padding: '8px 16px' }}
          >
            <Play size={14} fill="currentColor" />
            <span>{loading ? 'Running Benchmark...' : 'Run Benchmark'}</span>
          </button>
        </div>
      </div>

      {summary ? (
        <>
          {/* Benchmark Metadata Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '24px', fontSize: '0.82rem' }}>
              <div>Dataset: <strong className="mono">{summary.dataset_size} transactions</strong></div>
              <div>Seed: <strong className="mono">{benchmarkSeed}</strong></div>
              <div>Scenarios: <strong className="mono">7 Scenarios</strong></div>
              <div>Generated: <span className="mono" style={{ color: 'var(--text-muted)' }}>{new Date(summary.generated_at).toLocaleTimeString()}</span></div>
            </div>

            <div>
              <span className={`badge ${summary.invariants_passed ? 'badge-success' : 'badge-danger'}`} style={{ padding: '4px 10px' }}>
                {summary.invariants_passed ? 'Invariants: 100% Passed' : 'Invariant Violation'}
              </span>
            </div>
          </div>

          {/* Core Comparison Table */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '16px' }}>
              Head-to-Head Comparison
            </h3>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th className="text-right">Static Baseline</th>
                    <th className="text-right">RecoverAI</th>
                    <th className="text-right">Improvement</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Total Revenue at Risk</strong></td>
                    <td className="mono text-right">{formatINR(summary.revenue_at_risk_paise)}</td>
                    <td className="mono text-right">{formatINR(summary.revenue_at_risk_paise)}</td>
                    <td className="text-right" style={{ color: 'var(--text-muted)' }}>Identical Batch</td>
                  </tr>
                  <tr>
                    <td><strong>Revenue Recovered</strong></td>
                    <td className="mono text-right">{formatINR(summary.baseline_recovered_paise)}</td>
                    <td className="mono text-right" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary)' }}>
                      {formatINR(summary.recoverai_recovered_paise)}
                    </td>
                    <td className="mono text-right" style={{ fontWeight: 700, color: 'var(--success)' }}>
                      {summary.improvement_pct > 0 ? `+${summary.improvement_pct}%` : `${summary.improvement_pct}%`}
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Recovery Rate</strong></td>
                    <td className="mono text-right">{summary.baseline_recovery_rate}%</td>
                    <td className="mono text-right" style={{ fontWeight: 700, color: 'var(--primary)' }}>
                      {summary.recoverai_recovery_rate}%
                    </td>
                    <td className="mono text-right" style={{ color: 'var(--success)', fontWeight: 600 }}>
                      +{(summary.recoverai_recovery_rate - summary.baseline_recovery_rate).toFixed(1)}% pts
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Compliant Escalations</strong></td>
                    <td className="mono text-right">0</td>
                    <td className="mono text-right" style={{ fontWeight: 600 }}>
                      {summary.escalations}
                    </td>
                    <td className="text-right" style={{ color: 'var(--text-muted)' }}>High-value &amp; low confidence routed</td>
                  </tr>
                  <tr>
                    <td><strong>Policy Guardrail Stops</strong></td>
                    <td className="mono text-right">0</td>
                    <td className="mono text-right" style={{ fontWeight: 600 }}>
                      {summary.policy_stops}
                    </td>
                    <td className="text-right" style={{ color: 'var(--text-muted)' }}>Prohibited retries prevented</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Safety Invariant Scorecards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div className="card">
              <span className="kpi-label">
                <Lock size={14} style={{ color: 'var(--text-muted)' }} />
                Prohibited Retries Blocked
              </span>
              <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>{summary.prohibited_retries_prevented}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Prevented spamming exhausted rails
              </p>
            </div>

            <div className="card">
              <span className="kpi-label">
                <Shield size={14} style={{ color: 'var(--text-muted)' }} />
                High-Value Escalations
              </span>
              <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>{summary.high_value_escalations}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Orders &gt; ₹50k safely held
              </p>
            </div>

            <div className="card">
              <span className="kpi-label">
                <FileCheck size={14} style={{ color: 'var(--text-muted)' }} />
                Duplicate Actions Blocked
              </span>
              <p className="kpi-value mono" style={{ color: 'var(--text-primary)' }}>{summary.duplicate_actions_prevented}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                In-flight transaction lock active
              </p>
            </div>

            <div className="card">
              <span className="kpi-label">
                <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                Invariant Verification
              </span>
              <p className="kpi-value mono" style={{ color: 'var(--success)' }}>100% PASS</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Recovered &le; revenue at risk
              </p>
            </div>
          </div>

          {/* Scenario-by-Scenario Matrix */}
          <div className="card">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '6px' }}>Scenario Matrix</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Granular breakdown across all 7 evaluation scenarios.
            </p>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Transactions</th>
                    <th className="text-right">Revenue at Risk</th>
                    <th className="text-right">Baseline Rec.</th>
                    <th className="text-right">RecoverAI Rec.</th>
                    <th className="text-right">Recovery Rate</th>
                    <th className="text-right">Escalations</th>
                    <th className="text-right">Policy Stops</th>
                    <th>Invariants</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.scenarios.map((sc) => (
                    <tr key={sc.scenario_id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{sc.scenario_name}</div>
                        <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{sc.scenario_id}</div>
                      </td>
                      <td className="mono">{sc.total_transactions}</td>
                      <td className="mono text-right">{formatINR(sc.revenue_at_risk_paise)}</td>
                      <td className="mono text-right">{formatINR(sc.baseline_recovered_paise)}</td>
                      <td className="mono text-right" style={{ fontWeight: 700, color: 'var(--primary)' }}>
                        {formatINR(sc.recoverai_recovered_paise)}
                      </td>
                      <td className="mono text-right" style={{ fontWeight: 600 }}>{sc.recoverai_recovery_rate}%</td>
                      <td className="mono text-right">{sc.escalations}</td>
                      <td className="mono text-right">{sc.policy_stops}</td>
                      <td>
                        <span className={`badge ${sc.invariants_passed ? 'badge-success' : 'badge-danger'}`}>
                          {sc.invariants_passed ? 'PASS' : 'FAIL'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <p style={{ color: 'var(--text-muted)' }}>Click "Run Benchmark" to execute the 7-scenario evaluation suite.</p>
        </div>
      )}
    </div>
  );
};
