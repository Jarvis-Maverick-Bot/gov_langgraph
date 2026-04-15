"""
tests/test_queue_local_state.py
V1.9 Sprint 1, Task T1.2
Unit tests for governance.queue.local_state
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

# Import module
import governance.queue.local_state as local_state
import governance.queue.store as store_module


class TestLocalStateCache:
    """Tests for local cache operations."""

    @pytest.fixture(autouse=True)
    def temp_dir(self, tmp_path):
        """Use temp directory for all local_state tests."""
        # Point store.DATA_DIR to temp, and reset singleton
        original_data_dir = store_module.DATA_DIR
        original_messages = store_module.MESSAGES_FILE
        original_default_store = store_module._default_store

        store_module.DATA_DIR = tmp_path / "queue_data"
        store_module.MESSAGES_FILE = store_module.DATA_DIR / "messages.json"
        store_module._default_store = None

        # Ensure clean state
        yield tmp_path

        # Restore
        store_module.DATA_DIR = original_data_dir
        store_module.MESSAGES_FILE = original_messages
        store_module._default_store = original_default_store

    def test_cache_message(self):
        from governance.queue.models import Message, MessageType
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={"n": 1},
        )
        local_state.cache_message(msg)
        retrieved = local_state.get_cached_message(msg.message_id)
        assert retrieved is not None
        assert retrieved.sender == "A"
        assert retrieved.payload == {"n": 1}

    def test_update_cached_message(self):
        from governance.queue.models import Message, MessageType, MessageState
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={},
        )
        local_state.cache_message(msg)
        msg.state = MessageState.ROUTED
        local_state.update_cached_message(msg)
        updated = local_state.get_cached_message(msg.message_id)
        assert updated.state == MessageState.ROUTED

    def test_update_cached_message_not_found_raises(self):
        from governance.queue.models import Message, MessageType
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={},
        )
        with pytest.raises(KeyError):
            local_state.update_cached_message(msg)

    def test_list_cached_messages(self):
        from governance.queue.models import Message, MessageType
        msg1 = Message(sender="A", receiver="B", type=MessageType.REQUEST, payload={})
        msg2 = Message(sender="B", receiver="A", type=MessageType.REQUEST, payload={})
        local_state.cache_message(msg1)
        local_state.cache_message(msg2)
        all_msgs = local_state.list_cached_messages()
        assert len(all_msgs) == 2

    def test_list_cached_by_state(self):
        from governance.queue.models import Message, MessageType, MessageState
        msg1 = Message(sender="A", receiver="B", type=MessageType.REQUEST, payload={})
        msg2 = Message(sender="B", receiver="C", type=MessageType.REQUEST, payload={})
        msg1.state = MessageState.ROUTED
        local_state.cache_message(msg1)
        local_state.cache_message(msg2)
        routed = local_state.list_cached_by_state(MessageState.ROUTED)
        assert len(routed) == 1
        assert routed[0].message_id == msg1.message_id

    def test_list_cached_by_receiver(self):
        from governance.queue.models import Message, MessageType
        msg1 = Message(sender="A", receiver="B", type=MessageType.REQUEST, payload={})
        msg2 = Message(sender="A", receiver="C", type=MessageType.REQUEST, payload={})
        local_state.cache_message(msg1)
        local_state.cache_message(msg2)
        b_msgs = local_state.list_cached_by_receiver("B")
        assert len(b_msgs) == 1
        assert b_msgs[0].receiver == "B"


class TestEvidenceLog:
    """Tests for evidence log operations."""

    @pytest.fixture(autouse=True)
    def temp_dir(self, tmp_path):
        """Use temp directory for evidence tests."""
        original_evidence_dir = local_state.EVIDENCE_DIR
        local_state.EVIDENCE_DIR = tmp_path / "evidence" / "queue"
        yield tmp_path
        local_state.EVIDENCE_DIR = original_evidence_dir

    def test_append_evidence_creates_file(self):
        from governance.queue.models import Message, MessageType
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={},
        )
        local_state.append_evidence(
            event_type="create",
            before=None,
            after=msg.to_dict(),
            metadata={"test": True},
        )
        evidence_file = local_state._evidence_file()
        assert evidence_file.exists()
        with open(evidence_file) as f:
            line = f.readline()
        event = json.loads(line)
        assert event["event_type"] == "create"
        assert event["message_id"] == msg.message_id
        assert event["before"] is None
        assert event["metadata"]["test"] is True

    def test_get_evidence_for_message(self):
        from governance.queue.models import Message, MessageType
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={},
        )
        local_state.append_evidence("create", None, msg.to_dict())
        local_state.append_evidence("update", msg.to_dict(), msg.to_dict())
        evidence = local_state.get_evidence(msg.message_id)
        assert len(evidence) == 2
        assert evidence[0]["event_type"] == "create"
        assert evidence[1]["event_type"] == "update"

    def test_get_evidence_nonexistent(self):
        evidence = local_state.get_evidence("nonexistent-id")
        assert evidence == []

    def test_evidence_jsonl_format(self):
        """Verify each line in evidence file is valid JSON."""
        from governance.queue.models import Message, MessageType
        msg = Message(
            sender="A", receiver="B",
            type=MessageType.REQUEST, payload={},
        )
        local_state.append_evidence("create", None, msg.to_dict())
        evidence_file = local_state._evidence_file()
        with open(evidence_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Should not raise
                event = json.loads(line)
                assert "ts" in event
                assert "event_type" in event
                assert "message_id" in event
