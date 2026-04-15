"""
governance/routing/return_path.py
V1.9 Sprint 2, Task T6.3 — Return-Path Handling

Response/clarification returns to originating participant via explicit chain:
    1. Publish response to gov.queue.responses
    2. Link to originating message via linked_response_id
    3. Trace return path

PRD Reference: V1.9_PRD_V0_3.md §5.C (Req 22-27)
"""

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from governance.queue import nats_transport


@dataclass
class ReturnRecord:
    """
    Record of a return-path operation.

    Fields:
        return_id: Unique identifier for this return
        response_message_id: message_id of the returned response
        originating_message_id: message_id of the originating message being responded to
        returned_at: ISO timestamp of the return
        return_reason: justification for the return
    """
    return_id: str
    response_message_id: str
    originating_message_id: str
    returned_at: str
    return_reason: str

    def to_dict(self) -> dict:
        return {
            "return_id": self.return_id,
            "response_message_id": self.response_message_id,
            "originating_message_id": self.originating_message_id,
            "returned_at": self.returned_at,
            "return_reason": self.return_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReturnRecord":
        return cls(
            return_id=data["return_id"],
            response_message_id=data["response_message_id"],
            originating_message_id=data["originating_message_id"],
            returned_at=data["returned_at"],
            return_reason=data.get("return_reason", ""),
        )


# Return-path trace storage
_DATA_DIR = Path(__file__).parent / "data"
_RETURN_RECORDS_FILE = _DATA_DIR / "return_records.json"
_lock = threading.RLock()


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_returns() -> list:
    _ensure_data_dir()
    if not _RETURN_RECORDS_FILE.exists():
        return []
    try:
        with open(_RETURN_RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_returns(data: list) -> None:
    _ensure_data_dir()
    tmp = _RETURN_RECORDS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(_RETURN_RECORDS_FILE)


def route_return(response_message: dict, originating_message_id: str) -> ReturnRecord:
    """
    Route a response back to its originating participant.

    Args:
        response_message: The response message dict. Must contain 'message_id'.
        originating_message_id: The message_id of the originating message being responded to.

    Returns:
        ReturnRecord tracking the return operation.

    Raises:
        ValueError: if response_message does not contain 'message_id'
    """
    import uuid

    response_id = response_message.get("message_id")
    if not response_id:
        raise ValueError("response_message must contain 'message_id'")

    # Build the linked response payload
    linked_payload = {
        "message_id": response_id,
        "linked_response_id": originating_message_id,
        "return_reason": response_message.get("return_reason", "response_return"),
        "payload": response_message.get("payload", response_message),
    }

    # Publish to NATS responses subject
    payload_bytes = json.dumps(linked_payload).encode("utf-8")
    nats_transport.publish(nats_transport.SUBJ_RESPONSES, payload_bytes)

    # Record the return path
    return_record = ReturnRecord(
        return_id=f"RET-{uuid.uuid4().hex[:8]}",
        response_message_id=response_id,
        originating_message_id=originating_message_id,
        returned_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        return_reason=response_message.get("return_reason", "response_return"),
    )

    with _lock:
        data = _read_returns()
        data.append(return_record.to_dict())
        _write_returns(data)

    return return_record


def get_return_record(return_id: str) -> Optional[ReturnRecord]:
    """
    Retrieve a return record by return_id.

    Args:
        return_id: The return record identifier

    Returns:
        ReturnRecord if found, None otherwise
    """
    with _lock:
        for item in _read_returns():
            if item["return_id"] == return_id:
                return ReturnRecord.from_dict(item)
        return None


def list_returns_for_message(originating_message_id: str) -> list:
    """
    List all return records for a specific originating message.

    Args:
        originating_message_id: The message_id to query returns for

    Returns:
        List of ReturnRecords for the given originating message
    """
    with _lock:
        return [
            ReturnRecord.from_dict(item)
            for item in _read_returns()
            if item["originating_message_id"] == originating_message_id
        ]
