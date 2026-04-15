"""
governance/queue/store.py
V1.9 Sprint 1, Task T1.2
NATS-backed queue store with local JSON cache.

Transport: NATS (nats-io/nats.py) — primary message transport
Storage: Local JSON cache (governance/queue/data/messages.json) — for CLI inspection + evidence

Public API unchanged from JSON-backed version:
    add, get, update, delete, list_all, list_by_state, list_by_receiver, count, clear
    get_store() — singleton accessor

Queue-state boundary rule:
    Local cache is updated ONLY after NATS delivery confirmed.
    If NATS publish fails, cache must NOT be updated.
"""

import json
import threading
from typing import List, Optional

from .models import Message, MessageState
from . import nats_transport
from . import local_state


_lock = threading.RLock()

# Re-exported for backward compatibility with existing tests
DATA_DIR = local_state.DATA_DIR
MESSAGES_FILE = local_state.MESSAGES_FILE

# Default store instance
_default_store: Optional["QueueStore"] = None


class QueueStore:
    """
    Thread-safe NATS-backed queue store with local JSON cache.

    - add(): publishes to NATS first, THEN caches locally on success
    - get/list/count/update/delete: operate on local cache
    - All state transitions are evidence-logged to evidence/queue/YYYY-MM-DD.jsonl
    """

    def __init__(self) -> None:
        pass

    def add(self, message: Message) -> None:
        """
        Add a message: publish to NATS first, then cache locally.

        Raises NATSConnectionError if NATS publish fails (cache not updated).
        """
        with _lock:
            # Serialize message for NATS transport
            payload = json.dumps(message.to_dict()).encode("utf-8")

            # Publish to NATS — if this fails, cache must NOT be updated
            try:
                nats_transport.publish(nats_transport.SUBJ_MESSAGES, payload)
            except nats_transport.NATSConnectionError:
                raise  # propagate with original error context

            # NATS delivery confirmed — now update local cache
            before = local_state.get_cached_message(message.message_id)
            local_state.cache_message(message)
            local_state.append_evidence(
                event_type="create",
                before=before.to_dict() if before else None,
                after=message.to_dict(),
                metadata={"subject": nats_transport.SUBJ_MESSAGES},
            )

    def get(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by message_id from local cache. Returns None if not found."""
        with _lock:
            return local_state.get_cached_message(message_id)

    def update(self, message: Message) -> None:
        """
        Update an existing message in the local cache.

        Also logs evidence for state transitions (detected by state change).
        """
        with _lock:
            # Capture before state for evidence
            before = local_state.get_cached_message(message.message_id)
            before_dict = before.to_dict() if before else None

            # Detect state transition
            is_state_change = (
                before is not None
                and before.state != message.state
            )

            local_state.update_cached_message(message)

            if is_state_change:
                local_state.append_evidence(
                    event_type="state_change",
                    before=before_dict,
                    after=message.to_dict(),
                    metadata={"from_state": before.state.value, "to_state": message.state.value},
                )
            else:
                local_state.append_evidence(
                    event_type="update",
                    before=before_dict,
                    after=message.to_dict(),
                )

    def delete(self, message_id: str) -> bool:
        """
        Delete a message from local cache. Returns True if deleted, False if not found.
        """
        with _lock:
            before = local_state.get_cached_message(message_id)
            if before is None:
                return False

            data = local_state.list_cached_messages()
            data = [item for item in data if item.message_id != message_id]

            # Rewrite cache without the deleted message
            _write_all_to_cache(data)

            local_state.append_evidence(
                event_type="delete",
                before=before.to_dict(),
                after={"message_id": message_id},
            )
            return True

    def list_all(self) -> List[Message]:
        """List all messages from local cache."""
        with _lock:
            return local_state.list_cached_messages()

    def list_by_state(self, state: str) -> List[Message]:
        """List all messages in a specific state from local cache."""
        with _lock:
            try:
                ms = MessageState(state)
            except ValueError:
                return []
            return local_state.list_cached_by_state(ms)

    def list_by_receiver(self, receiver: str) -> List[Message]:
        """List all messages for a specific receiver from local cache."""
        with _lock:
            return local_state.list_cached_by_receiver(receiver)

    def count(self) -> int:
        """Return total message count from local cache."""
        with _lock:
            return len(local_state.list_cached_messages())

    def clear(self) -> None:
        """Clear all messages from local cache. Use with caution."""
        with _lock:
            # Capture before state for evidence
            before = local_state.list_cached_messages()
            _write_all_to_cache([])
            if before:
                local_state.append_evidence(
                    event_type="delete",
                    before=[m.to_dict() for m in before],
                    after={},
                    metadata={"action": "clear_all"},
                )


def _write_all_to_cache(messages: List[Message]) -> None:
    """Rewrite the entire cache with a list of messages."""
    import json as _json

    messages_file = local_state._get_messages_file()
    data_dir = local_state._get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    data = [m.to_dict() if hasattr(m, "to_dict") else m for m in messages]
    tmp = messages_file.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        _json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(messages_file)


def get_store() -> QueueStore:
    """Get the default store instance (singleton)."""
    global _default_store
    if _default_store is None:
        _default_store = QueueStore()
    return _default_store
