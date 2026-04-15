"""
tests/test_routing_multihop.py
V1.9 Sprint 2, FB3 — Unit tests for governance.routing.multihop
"""

import json
import os
import pytest
from pathlib import Path

# Set local transport mode before importing modules
os.environ["QUEUE_TRANSPORT"] = "local"

import governance.routing.multihop as multihop_module
from governance.routing.multihop import (
    HopRecord,
    record_hop,
    get_hop_chain,
    get_latest_hop,
    get_inbox_subject,
    deliver_multihop,
    HOP_CHAINS_FILE,
    _lock,
)


@pytest.fixture(autouse=True)
def temp_store(tmp_path):
    """Use temp directory for hop chain store."""
    original_data_dir = multihop_module._DATA_DIR
    original_file = multihop_module.HOP_CHAINS_FILE
    multihop_module._DATA_DIR = tmp_path / "hop_data"
    multihop_module.HOP_CHAINS_FILE = multihop_module._DATA_DIR / "hop_chains.json"
    multihop_module._DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    multihop_module._DATA_DIR = original_data_dir
    multihop_module.HOP_CHAINS_FILE = original_file


class TestHopRecord:
    """Tests for HopRecord dataclass."""

    def test_to_dict(self):
        record = HopRecord(
            hop_id="HOP-001",
            message_id="MSG-001",
            hop_number=1,
            from_owner=None,
            to_owner="AgentA",
            hop_reason="initial_routing",
            timestamp="2026-04-15T12:00:00Z",
        )
        d = record.to_dict()
        assert d["hop_id"] == "HOP-001"
        assert d["message_id"] == "MSG-001"
        assert d["hop_number"] == 1
        assert d["from_owner"] is None
        assert d["to_owner"] == "AgentA"

    def test_from_dict(self):
        data = {
            "hop_id": "HOP-002",
            "message_id": "MSG-002",
            "hop_number": 2,
            "from_owner": "AgentA",
            "to_owner": "AgentB",
            "hop_reason": "re-routing",
            "timestamp": "2026-04-15T13:00:00Z",
        }
        record = HopRecord.from_dict(data)
        assert record.hop_id == "HOP-002"
        assert record.hop_number == 2
        assert record.from_owner == "AgentA"
        assert record.to_owner == "AgentB"


class TestRecordHop:
    """Tests for record_hop()."""

    def test_record_hop_first_hop(self):
        record = record_hop("MSG-FIRST", from_owner=None, to_owner="AgentA")

        assert record is not None
        assert record.message_id == "MSG-FIRST"
        assert record.hop_number == 1
        assert record.from_owner is None
        assert record.to_owner == "AgentA"
        assert record.hop_id.startswith("HOP-")

    def test_record_hop_increments_hop_number(self):
        record_hop("MSG-SECOND", from_owner=None, to_owner="AgentA")
        record2 = record_hop("MSG-SECOND", from_owner="AgentA", to_owner="AgentB")
        record3 = record_hop("MSG-SECOND", from_owner="AgentB", to_owner="AgentC")

        assert record2.hop_number == 2
        assert record3.hop_number == 3

    def test_record_hop_same_message_consecutive(self):
        record1 = record_hop("MSG-CONSEC", from_owner=None, to_owner="First")
        record2 = record_hop("MSG-CONSEC", from_owner="First", to_owner="Second")
        record3 = record_hop("MSG-CONSEC", from_owner="Second", to_owner="Third")

        assert record1.hop_number == 1
        assert record2.hop_number == 2
        assert record3.hop_number == 3

    def test_record_hop_different_messages_independent(self):
        record1a = record_hop("MSG-X", from_owner=None, to_owner="OwnerX")
        record1b = record_hop("MSG-X", from_owner="OwnerX", to_owner="NextX")
        record2a = record_hop("MSG-Y", from_owner=None, to_owner="OwnerY")

        assert record1a.hop_number == 1
        assert record1b.hop_number == 2
        assert record2a.hop_number == 1  # Independent for MSG-Y


class TestGetHopChain:
    """Tests for get_hop_chain()."""

    def test_get_hop_chain_empty(self):
        chain = get_hop_chain("NONEXISTENT-MSG")
        assert chain == []

    def test_get_hop_chain_returns_ordered(self):
        record_hop("MSG-ORDER", from_owner=None, to_owner="A")
        record_hop("MSG-ORDER", from_owner="A", to_owner="B")
        record_hop("MSG-ORDER", from_owner="B", to_owner="C")

        chain = get_hop_chain("MSG-ORDER")

        assert len(chain) == 3
        assert chain[0].hop_number == 1
        assert chain[0].to_owner == "A"
        assert chain[1].hop_number == 2
        assert chain[1].to_owner == "B"
        assert chain[2].hop_number == 3
        assert chain[2].to_owner == "C"

    def test_get_hop_chain_sorted_by_hop_number(self):
        # Add out of order
        record_hop("MSG-SORTED", from_owner="B", to_owner="C")
        record_hop("MSG-SORTED", from_owner=None, to_owner="A")
        record_hop("MSG-SORTED", from_owner="A", to_owner="B")

        chain = get_hop_chain("MSG-SORTED")

        assert [r.hop_number for r in chain] == [1, 2, 3]


class TestGetLatestHop:
    """Tests for get_latest_hop()."""

    def test_get_latest_hop_none(self):
        result = get_latest_hop("NONEXISTENT")
        assert result is None

    def test_get_latest_hop_returns_last(self):
        record_hop("MSG-LATEST", from_owner=None, to_owner="First")
        record_hop("MSG-LATEST", from_owner="First", to_owner="Second")
        record_hop("MSG-LATEST", from_owner="Second", to_owner="Last")

        latest = get_latest_hop("MSG-LATEST")

        assert latest is not None
        assert latest.hop_number == 3
        assert latest.to_owner == "Last"


class TestGetInboxSubject:
    """Tests for get_inbox_subject()."""

    def test_inbox_subject_pattern(self):
        subject = get_inbox_subject("AgentA")
        assert subject == "gov.queue.AgentA.inbox"

    def test_inbox_subject_with_hyphen(self):
        subject = get_inbox_subject("jarvis-qa")
        assert subject == "gov.queue.jarvis-qa.inbox"


class TestDeliverMultihop:
    """Tests for deliver_multihop()."""

    def test_deliver_multihop_returns_hop_record(self, monkeypatch):
        call_log = []
        def mock_publish(subject, payload):
            call_log.append((subject, payload))
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        record = deliver_multihop(
            item={"message_id": "MSG-MH-001", "payload": {}},
            from_owner=None,
            to_owner="Executor"
        )

        assert record is not None
        assert record.message_id == "MSG-MH-001"
        assert record.to_owner == "Executor"
        assert record.hop_number == 1

    def test_deliver_multihop_publishes_to_inbox_subject(self, monkeypatch):
        call_log = []
        def mock_publish(subject, payload):
            call_log.append((subject, payload))
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        deliver_multihop(
            item={"message_id": "MSG-INBOX-001", "payload": {}},
            from_owner="Coordinator",
            to_owner="Executor"
        )

        assert len(call_log) == 1
        subject, _ = call_log[0]
        assert subject == "gov.queue.Executor.inbox"

    def test_deliver_multihop_includes_from_owner_metadata(self, monkeypatch):
        call_log = []
        def mock_publish(subject, payload):
            call_log.append((subject, payload))
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        deliver_multihop(
            item={"message_id": "MSG-FROM-001", "payload": {}},
            from_owner="Upstream",
            to_owner="Downstream"
        )

        _, payload_bytes = call_log[0]
        payload = json.loads(payload_bytes.decode("utf-8"))
        assert payload["from_owner"] == "Upstream"
        assert payload["to_owner"] == "Downstream"

    def test_deliver_multihop_records_hop(self, monkeypatch):
        def mock_publish(subject, payload):
            pass
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        record = deliver_multihop(
            item={"message_id": "MSG-REC-HOP", "payload": {}},
            from_owner=None,
            to_owner="NewOwner"
        )

        chain = get_hop_chain("MSG-REC-HOP")
        assert len(chain) == 1
        assert chain[0].to_owner == "NewOwner"
