"""
governance/escalation/hold_state.py
V1.9 Sprint 2, Task T7.2
Escalated item enters explicit hold; state is observable, not silent stall.

Escalation states:
    ESCALATED — waiting for Alex decision
    DECIDED  — Alex has decided
    RETURNED — decision returned to downstream

Storage: governance/escalation/data/escalations.json (local cache, not primary queue)
"""

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

from ..queue import nats_transport


# Escalation state machine
class EscalationState(str, Enum):
    ESCALATED = "ESCALATED"   # Waiting for Alex decision
    DECIDED = "DECIDED"      # Alex has decided
    RETURNED = "RETURNED"    # Decision returned to downstream


@dataclass
class EscalationRecord:
    """
    Escalation record for an item that exceeded delegated authority.

    Fields:
        escalation_id: Unique identifier (UUID)
        item_id: ID of the item (message_id or task_id) that was escalated
        reason: Human-readable reason for escalation
        escalated_by: Name of the participant or system that triggered escalation
        escalated_at: ISO timestamp when escalation was created
        state: Current EscalationState
        decision_id: ID of the linked decision once decided
    """
    item_id: str
    reason: str
    escalated_by: str
    escalation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    escalated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: EscalationState = EscalationState.ESCALATED
    decision_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "escalation_id": self.escalation_id,
            "item_id": self.item_id,
            "reason": self.reason,
            "escalated_by": self.escalated_by,
            "escalated_at": self.escalated_at,
            "state": self.state.value,
            "decision_id": self.decision_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EscalationRecord":
        return cls(
            escalation_id=data["escalation_id"],
            item_id=data["item_id"],
            reason=data["reason"],
            escalated_by=data["escalated_by"],
            escalated_at=data["escalated_at"],
            state=EscalationState(data["state"]),
            decision_id=data.get("decision_id"),
        )

    def transition_to(self, new_state: EscalationState) -> None:
        valid = {
            EscalationState.ESCALATED: [EscalationState.DECIDED],
            EscalationState.DECIDED: [EscalationState.RETURNED],
            EscalationState.RETURNED: [],
        }
        if new_state in valid.get(self.state, []):
            self.state = new_state
        else:
            raise ValueError(
                f"Illegal escalation state transition: {self.state.value} -> {new_state.value}"
            )


# Storage paths
DATA_DIR = Path(__file__).parent / "data"
ESCALATIONS_FILE = DATA_DIR / "escalations.json"
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence" / "escalation"

_lock = threading.RLock()


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _evidence_file() -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return EVIDENCE_DIR / f"{today}.jsonl"


def _read_all() -> List[dict]:
    _ensure_dirs()
    if not ESCALATIONS_FILE.exists():
        return []
    try:
        with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_all(records: List[dict]) -> None:
    _ensure_dirs()
    tmp = ESCALATIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    tmp.replace(ESCALATIONS_FILE)


def _append_evidence(event_type: str, before: Optional[dict], after: dict) -> None:
    """Append an escalation evidence event to today's JSONL log."""
    with _lock:
        _ensure_dirs()
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "escalation_id": after.get("escalation_id"),
            "item_id": after.get("item_id"),
            "before": before,
            "after": after,
        }
        with open(_evidence_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def hold_escalation(escalation_id: str, item_id: str, reason: str) -> EscalationRecord:
    """
    Create or update an escalation record in ESCALATED state.

    If an active escalation already exists for the same item_id, returns that record.

    Args:
        escalation_id: Unique escalation ID (UUID)
        item_id: ID of the item being escalated
        reason: Reason for escalation

    Returns:
        EscalationRecord in ESCALATED state
    """
    with _lock:
        data = _read_all()
        # Check for existing active escalation for this item
        for item in data:
            rec = EscalationRecord.from_dict(item)
            if rec.item_id == item_id and rec.state == EscalationState.ESCALATED:
                return rec

        record = EscalationRecord(
            escalation_id=escalation_id,
            item_id=item_id,
            reason=reason,
            escalated_by="system",  # default until participant info is passed
            state=EscalationState.ESCALATED,
        )
        data.append(record.to_dict())
        _write_all(data)
        _append_evidence("escalation_create", None, record.to_dict())
        return record


def get_escalation(escalation_id: str) -> Optional[EscalationRecord]:
    """
    Retrieve an escalation record by escalation_id.

    Args:
        escalation_id: the escalation ID to look up

    Returns:
        EscalationRecord if found, None otherwise
    """
    with _lock:
        data = _read_all()
        for item in data:
            if item["escalation_id"] == escalation_id:
                return EscalationRecord.from_dict(item)
        return None


def list_escalations(status: Optional[EscalationState] = None) -> List[EscalationRecord]:
    """
    List all escalation records, optionally filtered by state.

    Args:
        status: if provided, filter to this EscalationState

    Returns:
        List of EscalationRecords
    """
    with _lock:
        data = _read_all()
        if status is None:
            return [EscalationRecord.from_dict(item) for item in data]
        return [
            EscalationRecord.from_dict(item)
            for item in data
            if item["state"] == status.value
        ]


def update_escalation_state(escalation_id: str, new_state: EscalationState, decision_id: Optional[str] = None) -> None:
    """
    Update an escalation record's state.

    Args:
        escalation_id: the escalation ID to update
        new_state: new EscalationState
        decision_id: optional decision ID to link (for DECIDED state)
    """
    with _lock:
        data = _read_all()
        for i, item in enumerate(data):
            if item["escalation_id"] == escalation_id:
                before = item.copy()
                rec = EscalationRecord.from_dict(item)
                rec.transition_to(new_state)
                if decision_id is not None:
                    rec.decision_id = decision_id
                data[i] = rec.to_dict()
                _write_all(data)
                _append_evidence(
                    f"escalation_state_{new_state.value.lower()}",
                    before,
                    rec.to_dict(),
                )
                return
        raise KeyError(f"Escalation {escalation_id} not found")
