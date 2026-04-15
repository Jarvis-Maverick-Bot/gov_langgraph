"""
governance/escalation/decision_record.py
V1.9 Sprint 2, Task T7.3
Alex decision captured as governed state (not informal chat).

Decision fields:
    decision_id: unique ID
    escalation_id: linked escalation
    decision: APPROVE | REJECT | CONTINUE | STOP
    note: Alex's reasoning
    decided_by: Alex (hardcoded for now)
    decided_at: ISO timestamp

Storage: governance/escalation/data/decisions.json
"""

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional


class DecisionValue(str, Enum):
    """Valid decision values from Alex."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CONTINUE = "CONTINUE"
    STOP = "STOP"


@dataclass
class DecisionRecord:
    """
    Alex's decision on an escalation.

    Fields:
        decision_id: Unique identifier (UUID)
        escalation_id: ID of the linked escalation
        decision: DecisionValue (APPROVE | REJECT | CONTINUE | STOP)
        note: Alex's reasoning
        decided_by: "Alex" (hardcoded)
        decided_at: ISO timestamp when decision was recorded
    """
    escalation_id: str
    decision: DecisionValue
    note: str
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decided_by: str = field(default_factory=lambda: "Alex")
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "escalation_id": self.escalation_id,
            "decision": self.decision.value,
            "note": self.note,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionRecord":
        return cls(
            decision_id=data["decision_id"],
            escalation_id=data["escalation_id"],
            decision=DecisionValue(data["decision"]),
            note=data["note"],
            decided_by=data.get("decided_by", "Alex"),
            decided_at=data.get("decided_at"),
        )


# Storage paths
DATA_DIR = Path(__file__).parent / "data"
DECISIONS_FILE = DATA_DIR / "decisions.json"
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
    if not DECISIONS_FILE.exists():
        return []
    try:
        with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_all(records: List[dict]) -> None:
    _ensure_dirs()
    tmp = DECISIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    tmp.replace(DECISIONS_FILE)


def _append_evidence(event_type: str, before: Optional[dict], after: dict) -> None:
    """Append a decision evidence event to today's JSONL log."""
    with _lock:
        _ensure_dirs()
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "decision_id": after.get("decision_id"),
            "escalation_id": after.get("escalation_id"),
            "before": before,
            "after": after,
        }
        with open(_evidence_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def record_decision(escalation_id: str, decision: DecisionValue, note: str) -> DecisionRecord:
    """
    Record Alex's decision on an escalation.

    Also transitions the escalation record from ESCALATED to DECIDED.

    Args:
        escalation_id: ID of the escalation to record a decision for
        decision: DecisionValue (APPROVE | REJECT | CONTINUE | STOP)
        note: Alex's reasoning

    Returns:
        DecisionRecord
    """
    with _lock:
        # Create the decision record
        record = DecisionRecord(
            escalation_id=escalation_id,
            decision=decision,
            note=note,
        )

        # Persist to decisions store
        data = _read_all()
        data.append(record.to_dict())
        _write_all(data)

        # Log evidence
        _append_evidence("decision_recorded", None, record.to_dict())

        # Transition escalation record to DECIDED
        from . import hold_state as hs

        try:
            hs.update_escalation_state(
                escalation_id,
                hs.EscalationState.DECIDED,
                decision_id=record.decision_id,
            )
        except KeyError:
            # Escalation may not exist yet; decision can be recorded standalone
            pass

        return record


def get_decision(decision_id: str) -> Optional[DecisionRecord]:
    """
    Retrieve a decision record by decision_id.

    Args:
        decision_id: the decision ID to look up

    Returns:
        DecisionRecord if found, None otherwise
    """
    with _lock:
        data = _read_all()
        for item in data:
            if item["decision_id"] == decision_id:
                return DecisionRecord.from_dict(item)
        return None


def get_decision_for_escalation(escalation_id: str) -> Optional[DecisionRecord]:
    """
    Retrieve the decision for a given escalation.

    Args:
        escalation_id: the escalation ID to look up

    Returns:
        DecisionRecord if found, None otherwise
    """
    with _lock:
        data = _read_all()
        for item in data:
            if item["escalation_id"] == escalation_id:
                return DecisionRecord.from_dict(item)
        return None
