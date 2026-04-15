"""
governance/routing/multihop.py
V1.9 Sprint 2, Task T6.4 — Multi-Hop Support

Item can move through 2+ participants; ownership traceability preserved:
    1. Each hop recorded with: hop_number, from_owner, to_owner, timestamp
    2. Full chain queryable: get_hop_chain(message_id) -> List[HopRecord]
    3. NATS subjects for multi-hop: extend with gov.queue.{receiver}.inbox pattern

PRD Reference: V1.9_PRD_V0_3.md §5.C (Req 22-27)
"""

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from governance.queue import nats_transport


@dataclass
class HopRecord:
    """
    Record of a single hop in a multi-owner chain.

    Fields:
        hop_id: Unique identifier for this hop
        message_id: The item/message this hop applies to
        hop_number: Sequential position in the chain (1-indexed)
        from_owner: Owner handing off this hop (None for first hop)
        to_owner: Owner receiving this hop
        hop_reason: Why the hop occurred
        timestamp: ISO timestamp of the hop
    """
    hop_id: str
    message_id: str
    hop_number: int
    from_owner: Optional[str]
    to_owner: str
    hop_reason: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "hop_id": self.hop_id,
            "message_id": self.message_id,
            "hop_number": self.hop_number,
            "from_owner": self.from_owner,
            "to_owner": self.to_owner,
            "hop_reason": self.hop_reason,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HopRecord":
        return cls(
            hop_id=data["hop_id"],
            message_id=data["message_id"],
            hop_number=data["hop_number"],
            from_owner=data.get("from_owner"),
            to_owner=data["to_owner"],
            hop_reason=data.get("hop_reason", ""),
            timestamp=data["timestamp"],
        )


# Hop chain storage
_DATA_DIR = Path(__file__).parent / "data"
HOP_CHAINS_FILE = _DATA_DIR / "hop_chains.json"
_lock = threading.RLock()


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_hops() -> list:
    _ensure_data_dir()
    if not HOP_CHAINS_FILE.exists():
        return []
    try:
        with open(HOP_CHAINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_hops(data: list) -> None:
    _ensure_data_dir()
    tmp = HOP_CHAINS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(HOP_CHAINS_FILE)


def record_hop(message_id: str, from_owner: Optional[str], to_owner: str) -> HopRecord:
    """
    Record a hop in a multi-owner chain.

    Args:
        message_id: The item/message being routed
        from_owner: Owner handing off (None for initial routing)
        to_owner: Owner receiving this hop

    Returns:
        HopRecord for the recorded hop
    """
    import uuid

    with _lock:
        hops = _read_hops()

        # Count existing hops for this message to determine hop_number
        existing_for_msg = [h for h in hops if h["message_id"] == message_id]
        hop_number = len(existing_for_msg) + 1

        hop_record = HopRecord(
            hop_id=f"HOP-{uuid.uuid4().hex[:8]}",
            message_id=message_id,
            hop_number=hop_number,
            from_owner=from_owner,
            to_owner=to_owner,
            hop_reason="multi_hop_routing",
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

        hops.append(hop_record.to_dict())
        _write_hops(hops)

    return hop_record


def get_hop_chain(message_id: str) -> List[HopRecord]:
    """
    Get the full hop chain for a message.

    Args:
        message_id: The message/item to get hop chain for

    Returns:
        List of HopRecords in chronological order (by hop_number)
    """
    with _lock:
        hops = _read_hops()
        matching = [
            HopRecord.from_dict(h)
            for h in hops
            if h["message_id"] == message_id
        ]
        # Sort by hop_number
        matching.sort(key=lambda r: r.hop_number)
        return matching


def get_latest_hop(message_id: str) -> Optional[HopRecord]:
    """
    Get the most recent hop for a message.

    Args:
        message_id: The message/item to get the latest hop for

    Returns:
        Latest HopRecord if any hops exist, None otherwise
    """
    chain = get_hop_chain(message_id)
    return chain[-1] if chain else None


# NATS multi-hop subject pattern
def get_inbox_subject(receiver: str) -> str:
    """
    Get the NATS inbox subject for a specific receiver.

    Pattern: gov.queue.{receiver}.inbox

    Args:
        receiver: The participant/receiver name

    Returns:
        NATS subject string
    """
    return f"gov.queue.{receiver}.inbox"


def deliver_multihop(item: dict, from_owner: Optional[str], to_owner: str) -> HopRecord:
    """
    Deliver an item via NATS to a new owner in a multi-hop chain.
    Publishes to the receiver's inbox subject.

    Args:
        item: The item dict (must contain 'message_id' or 'item_id')
        from_owner: Current owner handing off (None for initial delivery)
        to_owner: Next owner to receive the item

    Returns:
        HopRecord for the hop
    """
    import uuid

    message_id = item.get("message_id") or item.get("item_id") or str(uuid.uuid4())

    # Build hop metadata payload
    hop_payload = {
        "message_id": message_id,
        "from_owner": from_owner,
        "to_owner": to_owner,
        "hop_reason": item.get("hop_reason", "multi_hop_routing"),
        "payload": item.get("payload", item),
    }

    # Publish to the receiver's inbox subject
    subject = get_inbox_subject(to_owner)
    payload_bytes = json.dumps(hop_payload).encode("utf-8")
    nats_transport.publish(subject, payload_bytes)

    # Record the hop
    return record_hop(message_id, from_owner, to_owner)
