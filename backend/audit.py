"""
Audit Trail & Agent Replay Logger
Maintains append-only chronological records of all agent proposals, policy guardrail decisions,
tool executions, and financial outcomes.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from backend.models import AuditRecord, AgentReplayStep


class AuditTrailManager:
    """
    In-memory and persistent append-only audit trail logger.
    """
    def __init__(self):
        self._audit_records: List[AuditRecord] = []
        self._replay_steps: Dict[str, List[AgentReplayStep]] = {}  # keyed by incident_id or run_id

    def record_audit(
        self,
        incident_id: str,
        transaction_id: str,
        agent_run_id: str,
        proposed_action: str,
        confidence: float,
        policy_decision: str,
        policy_reason: str,
        tool_called: str,
        execution_status: str,
        outcome: str,
        amount_paise: int,
        recovered_amount_paise: int,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        """Appends a new immutable audit record."""
        record = AuditRecord(
            audit_id=f"aud_{uuid.uuid4().hex[:10]}",
            timestamp=datetime.now().isoformat(),
            incident_id=incident_id,
            transaction_id=transaction_id,
            agent_run_id=agent_run_id,
            proposed_action=proposed_action,
            confidence=round(confidence, 2),
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            tool_called=tool_called,
            execution_status=execution_status,
            outcome=outcome,
            amount_paise=amount_paise,
            recovered_amount_paise=recovered_amount_paise,
            details=details or {}
        )
        self._audit_records.append(record)
        return record

    def add_replay_step(
        self,
        incident_id: str,
        phase: str,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentReplayStep:
        """Appends a high-level chronological replay milestone."""
        if incident_id not in self._replay_steps:
            self._replay_steps[incident_id] = []
            
        step_num = len(self._replay_steps[incident_id]) + 1
        step = AgentReplayStep(
            step_id=f"step_{incident_id}_{step_num}",
            step_number=step_num,
            timestamp=datetime.now().isoformat(),
            phase=phase,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        self._replay_steps[incident_id].append(step)
        return step

    def get_audit_trail(
        self,
        incident_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        limit: int = 200
    ) -> List[AuditRecord]:
        """Queries audit records with optional filters."""
        records = self._audit_records
        if incident_id:
            records = [r for r in records if r.incident_id == incident_id]
        if transaction_id:
            records = [r for r in records if r.transaction_id == transaction_id]
        return records[-limit:]

    def get_replay_steps(self, incident_id: str) -> List[AgentReplayStep]:
        """Retrieves chronological replay steps for an incident."""
        return self._replay_steps.get(incident_id, [])

    def clear(self) -> None:
        """Clears logs (used for test resets)."""
        self._audit_records.clear()
        self._replay_steps.clear()


audit_manager = AuditTrailManager()
