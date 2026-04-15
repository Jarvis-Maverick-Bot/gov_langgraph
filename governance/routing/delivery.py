"""
governance/routing/delivery.py
V1.9 Sprint 2, Task T6.2 — Routing Delivery

Routes to correct owner via NATS.
On routing decision:
    1. Publish message to gov.queue.messages with owner metadata in payload
    2. Record delivery: owner, timestamp, reason
    3. Return delivery record

PRD Reference: V1.9_PRD_V0_3.md §5.C (Req 22-27)
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from governance.queue import nats_transport


# Data file for routing decisions (owned by routing layer, not queue store)
DATA_DIR = Path(__file__).parent / "data"
ROUTING_DECISIONS_FILE = DATA_DIR / "routing_decisions.json"

_lock = threading.RLock()
_default_store: Optional["RoutingDeliveryStore"] = None


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_decisions() -> list:
    """Read routing decisions from JSON file. Returns [] if file missing."""
    _ensure_data_dir()
    if not ROUTING_DECISIONS_FILE.exists():
        return []
    try:
        with open(ROUTING_DECISIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_decisions(data: list) -> None:
    """Write routing decisions list to JSON file atomically."""
    _ensure_data_dir()
    tmp = ROUTING_DECISIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(ROUTING_DECISIONS_FILE)


@dataclass
class DeliveryRecord:
    """
    Record of a routing delivery operation.

    Fields:
        delivery_id: Unique identifier for this delivery
        item_id: message_id or task_id of the routed item
        owner: owner the item was routed to
        routed_at: ISO timestamp of delivery
        reason: justification for routing decision
        subject: NATS subject the message was published to
    """
    delivery_id: str
    item_id: str
    owner: str
    routed_at: str
    reason: str
    subject: str = "gov.queue.messages"

    def to_dict(self) -> dict:
        return {
            "delivery_id": self.delivery_id,
            "item_id": self.item_id,
            "owner": self.owner,
            "routed_at": self.routed_at,
            "reason": self.reason,
            "subject": self.subject,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeliveryRecord":
        return cls(
            delivery_id=data["delivery_id"],
            item_id=data["item_id"],
            owner=data["owner"],
            routed_at=data["routed_at"],
            reason=data["reason"],
            subject=data.get("subject", "gov.queue.messages"),
        )


class RoutingDeliveryStore:
    """
    Thread-safe store for routing delivery records.

    Implements the same pattern as QueueStore:
        - RLock for thread safety
        - JSON file persistence via get_store() singleton
    """

    def add(self, record: DeliveryRecord) -> None:
        """Persist a delivery record to local JSON store."""
        with _lock:
            data = _read_decisions()
            data.append(record.to_dict())
            _write_decisions(data)

    def get(self, delivery_id: str) -> Optional[DeliveryRecord]:
        """Retrieve a delivery record by delivery_id. Returns None if not found."""
        with _lock:
            data = _read_decisions()
            for item in data:
                if item["delivery_id"] == delivery_id:
                    return DeliveryRecord.from_dict(item)
            return None

    def list_all(self) -> list:
        """List all delivery records."""
        with _lock:
            return [DeliveryRecord.from_dict(item) for item in _read_decisions()]

    def list_by_owner(self, owner: str) -> list:
        """List all delivery records for a specific owner."""
        with _lock:
            return [
                DeliveryRecord.from_dict(item)
                for item in _read_decisions()
                if item["owner"] == owner
            ]

    def clear(self) -> None:
        """Clear all delivery records. Use with caution."""
        with _lock:
            _write_decisions([])


def get_store() -> RoutingDeliveryStore:
    """Get the default RoutingDeliveryStore instance (singleton)."""
    global _default_store
    if _default_store is None:
        _default_store = RoutingDeliveryStore()
    return _default_store


def deliver_routed(item: dict, ownership_decision) -> DeliveryRecord:
    """
    Route an item to its owner via NATS and record the delivery.

    Args:
        item: The pending item dict (must contain 'message_id' or 'item_id')
        ownership_decision: OwnershipDecision from determine_ownership()

    Returns:
        DeliveryRecord with delivery details
    """
    import uuid

    # Resolve item_id from item dict
    item_id = item.get("message_id") or item.get("item_id") or str(uuid.uuid4())

    # Build owner metadata payload
    delivery_payload = {
        "message_id": item_id,
        "owner": ownership_decision.owner,
        "should_escalate": ownership_decision.should_escalate,
        "return_target": ownership_decision.return_target,
        "reason": ownership_decision.reason,
        "payload": item.get("payload", item),
    }

    # Publish to NATS with owner metadata
    payload_bytes = json.dumps(delivery_payload).encode("utf-8")
    nats_transport.publish(nats_transport.SUBJ_MESSAGES, payload_bytes)

    # Record the delivery
    delivery_record = DeliveryRecord(
        delivery_id=f"DEL-{uuid.uuid4().hex[:8]}",
        item_id=item_id,
        owner=ownership_decision.owner,
        routed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        reason=ownership_decision.reason,
        subject=nats_transport.SUBJ_MESSAGES,
    )

    store = get_store()
    store.add(delivery_record)

    return delivery_record
