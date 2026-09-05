"""
Storage Layer for RecoverAI
Provides fast, reliable thread-safe in-memory caching and JSON/SQLite persistence
for transactions, incidents, audit records, and evaluation runs.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import sqlite3
from backend.models import (
    Transaction, Customer, Incident, AuditRecord,
    AgentReplayStep, EvaluationSummary, ScenarioResult
)
from backend.config import settings, DATA_DIR
from backend.synthetic_data import (
    generate_synthetic_customers, generate_baseline_transactions,
    generate_incident_scenario, IncidentType
)


class DataStore:
    """
    Central storage repository for RecoverAI backend.
    """
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.incidents: Dict[str, Incident] = {}
        self.latest_evaluation: Optional[EvaluationSummary] = None
        self._initialize_seed_data()

    def _initialize_seed_data(self):
        """Pre-populates realistic baseline environment data."""
        cust_list = generate_synthetic_customers(120, seed=42)
        for c in cust_list:
            self.customers[c.id] = c

        # Generate baseline transactions
        base_txs = generate_baseline_transactions(300, cust_list, seed=42)
        for t in base_txs:
            self.transactions[t.id] = t

        # Pre-seed one primary incident for immediate demo availability
        incident, inc_txs = generate_incident_scenario(
            incident_type=IncidentType.UPI_TIMEOUT_SPIKE,
            severity_pct=70.0,
            affected_count=500,
            customers=cust_list,
            seed=42
        )
        self.incidents[incident.id] = incident
        for t in inc_txs:
            self.transactions[t.id] = t

    def get_customers(self) -> List[Customer]:
        return list(self.customers.values())

    def get_transactions(self, limit: int = 500, incident_id: Optional[str] = None) -> List[Transaction]:
        txs = list(self.transactions.values())
        if incident_id:
            txs = [t for t in txs if t.incident_id == incident_id]
        return sorted(txs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        return self.transactions.get(tx_id)

    def save_transaction(self, tx: Transaction):
        self.transactions[tx.id] = tx

    def get_incidents(self) -> List[Incident]:
        return sorted(list(self.incidents.values()), key=lambda x: x.created_at, reverse=True)

    def get_incident(self, inc_id: str) -> Optional[Incident]:
        return self.incidents.get(inc_id)

    def save_incident(self, incident: Incident):
        self.incidents[incident.id] = incident

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates dashboard hero summary metrics."""
        incidents_list = list(self.incidents.values())
        resolved_incidents = [i for i in incidents_list if i.status == "RESOLVED"]
        
        total_at_risk = sum(i.revenue_at_risk_paise for i in incidents_list)
        total_recovered = sum(i.actual_recovered_paise for i in incidents_list)
        total_baseline_recovered = sum(i.baseline_recovered_paise for i in incidents_list)
        
        recovery_rate = (total_recovered / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
        
        # Improvement vs baseline
        if total_baseline_recovered > 0:
            improvement_pct = ((total_recovered - total_baseline_recovered) / total_baseline_recovered) * 100.0
        else:
            improvement_pct = 0.0

        all_failed = [t for t in self.transactions.values() if t.status == "FAILED"]
        all_recovered = [t for t in self.transactions.values() if t.status == "RECOVERED"]
        all_escalated = [t for t in self.transactions.values() if t.status == "ESCALATED"]

        return {
            "total_revenue_at_risk_paise": total_at_risk,
            "total_recovered_paise": total_recovered,
            "total_baseline_recovered_paise": total_baseline_recovered,
            "recovery_rate": round(recovery_rate, 2),
            "improvement_pct": round(improvement_pct, 2),
            "active_incidents_count": sum(1 for i in incidents_list if i.status in ("ACTIVE", "RECOVERING")),
            "resolved_incidents_count": len(resolved_incidents),
            "total_transactions_count": len(self.transactions),
            "affected_transactions_count": len(all_failed) + len(all_recovered) + len(all_escalated),
            "successful_recoveries_count": len(all_recovered),
            "escalated_count": len(all_escalated)
        }


db = DataStore()
