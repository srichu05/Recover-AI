import React from 'react';
import {
  Shield,
  Activity,
  Sliders,
  BarChart2,
  Clock,
  FileText,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeIncidentCount: number;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  activeIncidentCount,
  onRefresh,
  isRefreshing
}) => {
  return (
    <header className="navbar">
      <div className="nav-brand">
        <div className="brand-icon">
          <Shield size={18} strokeWidth={2.2} />
        </div>
        <div>
          <div className="brand-title">RecoverAI</div>
          <div className="brand-subtitle">Autonomous Revenue Recovery</div>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity size={15} />
          <span>Overview</span>
        </button>

        <button
          className={`nav-tab ${activeTab === 'simulator' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulator')}
        >
          <Sliders size={15} />
          <span>Simulator</span>
          {activeIncidentCount > 0 && (
            <span
              style={{
                background: 'var(--danger-bg)',
                color: 'var(--danger)',
                border: '1px solid var(--danger-border)',
                fontSize: '0.68rem',
                fontWeight: 700,
                padding: '1px 5px',
                borderRadius: 'var(--radius-sm)'
              }}
            >
              {activeIncidentCount}
            </span>
          )}
        </button>

        <button
          className={`nav-tab ${activeTab === 'incident_detail' ? 'active' : ''}`}
          onClick={() => setActiveTab('incident_detail')}
        >
          <BarChart2 size={15} />
          <span>Incidents</span>
        </button>

        <button
          className={`nav-tab ${activeTab === 'agent_replay' ? 'active' : ''}`}
          onClick={() => setActiveTab('agent_replay')}
        >
          <Clock size={15} />
          <span>Replay</span>
        </button>

        <button
          className={`nav-tab ${activeTab === 'audit_trail' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit_trail')}
        >
          <FileText size={15} />
          <span>Audit</span>
        </button>

        <button
          className={`nav-tab ${activeTab === 'evaluation' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluation')}
        >
          <CheckCircle2 size={15} />
          <span>Evaluation</span>
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="status-dot status-dot-success" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Policy Engine Active
          </span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          title="Refresh Data"
        >
          <RefreshCw size={13} className={isRefreshing ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
};
