"""
governance/escalation/return_to_flow.py
V1.9 Sprint 2, Task T7.4
Post-decision: item routed back to downstream participant via NATS (gov.queue.responses).

On return-to-flow:
    1. Look up decision for escalation
    2. Publish outcome to gov.queue.responses (continuation, closure, or rejection)
    3. Update escalation state to RETURNED
    4. Link to original item

Export: return_to_flow(escalation_id) -> ReturnRecord
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from ..queue import nats_transport
from ..queue.models import Message, MessageState
from . import hold_state as hs
from . import decision_record as dr


class ReturnOutcome(str, Enum):
    """
    Outcome of return-to-flow, mapped from decision value.
    
    CONTINUE / APPROVE → routed back as continuation
    STOP / REJECT → routed back as terminal closure
    """
    CONTINUATION = "CONTINUATION"
    CLOSURE = "CLOSURE"
    REJECTION = "REJECTION"


@dataclass
class ReturnRecord:
    """
    Record of a return-to-flow action.

    Fields:
        return_id: Unique identifier (UUID)
        escalation_id: linked escalation
        decision_id: linked decision
        outcome: ReturnOutcome
        item_id: original item that was escalated
        returned_at: ISO timestamp
        published_to: NATS subject the response was published to
    """
    escalation_id: str
    decision_id: str
    item_id: str
    outcome: ReturnOutcome
    return_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    returned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_to: str = ""

    def to_dict(self) -> dict:
        return {
            "return_id": self.return_id,
            "escalation_id": self.escalation_id,
            "decision_id": self.decision_id,
            "item_id": self.item_id,
            "outcome": self.outcome.value,
            "returned_at": self.returned_at,
            "published_to": self.published_to,
        }


EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence" / "escalation"


def _ensure_evidence_dir() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _append_evidence(event_type: str, before: Optional[dict], after: dict) -> None:
    """Append a return-to-flow evidence event to today's JSONL log."""
    _ensure_evidence_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_file = EVIDENCE_DIR / f"{today}.jsonl"
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "return_id": after.get("return_id"),
        "escalation_id": after.get("escalation_id"),
        "item_id": after.get("item_id"),
        "before": before,
        "after": after,
    }
    with open(evidence_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def return_to_flow(escalation_id: str) -> ReturnRecord:
    """
    Return a decision to the downstream flow via NATS gov.queue.responses.

    Steps:
    1. Look up decision for escalation
    2. Map decision to ReturnOutcome
    3. Publish outcome to gov.queue.responses
    4. Update escalation state to RETURNED
    5. Link to original item

    Args:
        escalation_id: ID of the escalation to return to flow

    Returns:
        ReturnRecord capturing the return action

    Raises:
        KeyError: if escalation or decision not found
    """
    # 1. Look up escalation
    escalation = hs.get_escalation(escalation_id)
    if escalation is None:
        raise KeyError(f"Escalation {escalation_id} not found")

    # 2. Look up decision
    decision = dr.get_decision_for_escalation(escalation_id)
    if decision is None:
        raise KeyError(f"No decision found for escalation {escalation_id}")

    # 3. Map decision to outcome
    if decision.decision in (dr.DecisionValue.APPROVE, dr.DecisionValue.CONTINUE):
        outcome = ReturnOutcome.CONTINUATION
    elif decision.decision == dr.DecisionValue.STOP:
        outcome = ReturnOutcome.CLOSURE
    else:  # REJECT
        outcome = ReturnOutcome.REJECTION

    # 4. Build return record
    record = ReturnRecord(
        escalation_id=escalation_id,
        decision_id=decision.decision_id,
        item_id=escalation.item_id,
        outcome=outcome,
    )

    # 5. Publish to NATS gov.queue.responses
    # The payload includes: item_id, outcome, decision note, escalation_id
    response_payload = {
        "item_id": escalation.item_id,
        "escalation_id": escalation_id,
        "decision_id": decision.decision_id,
        "outcome": outcome.value,
        "note": decision.note,
        "decided_by": decision.decided_by,
        "decided_at": decision.decided_at,
    }
    try:
        nats_transport.publish(
            nats_transport.SUBJ_RESPONSES,
            json.dumps(response_payload).encode("utf-8"),
        )
        record.published_to = nats_transport.SUBJ_RESPONSES
    except nats_transport.NATSConnectionError:
        # Record locally even if NATS publish fails
        record.published_to = "local_only"

    # 6. Update escalation state to RETURNED
    try:
        hs.update_escalation_state(escalation_id, hs.EscalationState.RETURNED)
    except (KeyError, ValueError):
        # State transition may fail if already returned — proceed anyway
        pass

    # 7. Log evidence
    _append_evidence("return_to_flow", None, record.to_dict())

    return record
