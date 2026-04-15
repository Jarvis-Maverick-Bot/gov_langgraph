"""
governance/queue/local_state.py
V1.9 Sprint 1, Task T1.2
Local JSON cache + evidence log for governance queue.

Cache: governance/queue/data/messages.json (persists across CLI restarts)
Evidence: evidence/queue/YYYY-MM-DD.jsonl (append-only, one file per day)

NOT the primary queue — NATS is the primary transport.
This layer provides CLI inspection and audit trail.
"""

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import Message, MessageState


# Default paths — used as fallback when store module is not available
_DEFAULT_DATA_DIR = Path(__file__).parent / "data"
_DEFAULT_MESSAGES_FILE = _DEFAULT_DATA_DIR / "messages.json"
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence" / "queue"

_lock = threading.RLock()


def _get_store_module():
    """Get the store module (for deferred DATA_DIR lookup)."""
    # Import lazily to avoid circular import at module load time
    try:
        return sys.modules["governance.queue.store"]
    except KeyError:
        return None


def _get_data_dir() -> Path:
    """Get DATA_DIR from store module if available, else default."""
    store = _get_store_module()
    if store is not None:
        return store.DATA_DIR
    return _DEFAULT_DATA_DIR


def _get_messages_file() -> Path:
    """Get MESSAGES_FILE from store module if available, else default."""
    store = _get_store_module()
    if store is not None:
        return store.MESSAGES_FILE
    return _DEFAULT_MESSAGES_FILE


def _ensure_data_dir() -> None:
    """Ensure the data and evidence directories exist."""
    _get_data_dir().mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _read_cache() -> List[dict]:
    """Read raw JSON list from messages.json. Returns [] if file missing."""
    _ensure_data_dir()
    messages_file = _get_messages_file()
    if not messages_file.exists():
        return []
    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_cache(data: List[dict]) -> None:
    """Write raw JSON list to messages.json atomically."""
    _ensure_data_dir()
    messages_file = _get_messages_file()
    tmp = messages_file.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(messages_file)


def _evidence_file() -> Path:
    """Get the evidence file path for today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return EVIDENCE_DIR / f"{today}.jsonl"


def cache_message(message: Message) -> None:
    """
    Write a message to the local JSON cache.

    Args:
        message: Message to cache
    """
    with _lock:
        data = _read_cache()
        data.append(message.to_dict())
        _write_cache(data)


def get_cached_message(message_id: str) -> Optional[Message]:
    """
    Retrieve a message from local cache by message_id.

    Args:
        message_id: the message ID to look up

    Returns:
        Message if found, None otherwise
    """
    with _lock:
        data = _read_cache()
        for item in data:
            if item["message_id"] == message_id:
                return Message.from_dict(item)
        return None


def update_cached_message(message: Message) -> None:
    """
    Update a message in the local cache.

    Args:
        message: Message with updated fields

    Raises:
        KeyError: if message_id not found in cache
    """
    with _lock:
        data = _read_cache()
        for i, item in enumerate(data):
            if item["message_id"] == message.message_id:
                data[i] = message.to_dict()
                _write_cache(data)
                return
        raise KeyError(f"Message {message.message_id} not found in cache")


def list_cached_messages() -> List[Message]:
    """
    List all messages in the local cache.

    Returns:
        List of all cached Messages
    """
    with _lock:
        data = _read_cache()
        return [Message.from_dict(item) for item in data]


def list_cached_by_state(state: MessageState) -> List[Message]:
    """
    List all messages in the local cache filtered by state.

    Args:
        state: MessageState to filter by

    Returns:
        List of Messages in the given state
    """
    with _lock:
        data = _read_cache()
        return [Message.from_dict(item) for item in data if item["state"] == state.value]


def list_cached_by_receiver(receiver: str) -> List[Message]:
    """
    List all messages in the local cache for a specific receiver.

    Args:
        receiver: receiver name to filter by

    Returns:
        List of Messages for the given receiver
    """
    with _lock:
        data = _read_cache()
        return [Message.from_dict(item) for item in data if item["receiver"] == receiver]


def append_evidence(
    event_type: str,
    before: Optional[dict],
    after: dict,
    metadata: Optional[dict] = None
) -> None:
    """
    Append an evidence event to today's JSONL evidence log.

    Event format:
        {
            "ts": "<iso>",
            "event_type": "state_change|create|update|delete",
            "message_id": "<id>",
            "before": {...} | null,
            "after": {...},
            "metadata": {...} | {}
        }

    Args:
        event_type: one of "state_change", "create", "update", "delete"
        before: state before the event (None for create)
        after: state after the event
        metadata: extra context (optional)
    """
    with _lock:
        _ensure_data_dir()
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "message_id": after.get("message_id"),
            "before": before,
            "after": after,
            "metadata": metadata or {},
        }
        with open(_evidence_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def get_evidence(message_id: str) -> List[dict]:
    """
    Retrieve all evidence events for a message across all evidence files.

    Searches evidence/queue/ directory for matching message_id.

    Args:
        message_id: the message ID to look up

    Returns:
        List of evidence event dicts in chronological order
    """
    with _lock:
        results: List[dict] = []
        if not EVIDENCE_DIR.exists():
            return results
        for evidence_file in sorted(EVIDENCE_DIR.iterdir()):
            if not evidence_file.suffix == ".jsonl":
                continue
            try:
                with open(evidence_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                            if event.get("message_id") == message_id:
                                results.append(event)
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue
        return results


# Re-export DATA_DIR/MESSAGES_FILE for backward compatibility
# These are used by tests that patch store.DATA_DIR
DATA_DIR = _DEFAULT_DATA_DIR
MESSAGES_FILE = _DEFAULT_MESSAGES_FILE
