import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewView } from './components/OverviewView';
import { SimulatorView } from './components/SimulatorView';
import { IncidentDetailView } from './components/IncidentDetailView';
import { AgentReplayView } from './components/AgentReplayView';
import { AuditTrailView } from './components/AuditTrailView';
import { EvaluationView } from './components/EvaluationView';

import type {
  DashboardSummary,
  Incident
} from './types';
import {
  fetchDashboardSummary,
  fetchIncidents
} from './api';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('simulator');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setIsRefreshing(true);
    try {
      const [sumData, incData] = await Promise.all([
        fetchDashboardSummary(),
        fetchIncidents()
      ]);
      setSummary(sumData);
      setIncidents(incData);
      if (incData.length > 0 && !currentIncident) {
        setCurrentIncident(incData[0]);
      }
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const activeIncCount = incidents.filter((i) => i.status === 'ACTIVE' || i.status === 'RECOVERING').length;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-page)' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeIncidentCount={activeIncCount}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
      />

      <main style={{ flex: 1, paddingBottom: '40px' }}>
        {activeTab === 'overview' && (
          <OverviewView
            summary={summary}
            incidents={incidents}
            onSelectIncident={(inc) => setCurrentIncident(inc)}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'simulator' && (
          <SimulatorView
            incidents={incidents}
            currentIncident={currentIncident}
            setCurrentIncident={setCurrentIncident}
            onRefresh={loadAllData}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'incident_detail' && (
          <IncidentDetailView
            currentIncident={currentIncident}
            incidents={incidents}
            onSelectIncident={(inc) => setCurrentIncident(inc)}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'agent_replay' && (
          <AgentReplayView
            currentIncident={currentIncident}
          />
        )}

        {activeTab === 'audit_trail' && (
          <AuditTrailView currentIncidentId={currentIncident?.id} />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationView />
        )}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 28px',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          background: 'var(--bg-surface)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1380px', margin: '0 auto' }}>
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>RecoverAI</strong> &mdash; Autonomous Revenue Recovery
          </div>
          <div>
            Control Boundary: <span className="mono" style={{ color: 'var(--text-secondary)' }}>Agent Proposes &rarr; Policy Engine Validates &rarr; Controlled Execution</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
