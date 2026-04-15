"""
tests/test_routing_delivery.py
V1.9 Sprint 2, FB3 — Unit tests for governance.routing.delivery
"""

import json
import os
import pytest

# Set local transport mode before importing modules
os.environ["QUEUE_TRANSPORT"] = "local"

import governance.routing.delivery as delivery_module
from governance.routing.delivery import (
    DeliveryRecord,
    RoutingDeliveryStore,
    deliver_routed,
    get_store,
)


@pytest.fixture(autouse=True)
def temp_store(tmp_path):
    """Use temp directory for routing delivery store."""
    original_data_dir = delivery_module.DATA_DIR
    original_file = delivery_module.ROUTING_DECISIONS_FILE
    original_default_store = delivery_module._default_store

    delivery_module.DATA_DIR = tmp_path / "routing_data"
    delivery_module.ROUTING_DECISIONS_FILE = delivery_module.DATA_DIR / "routing_decisions.json"
    delivery_module._default_store = None

    delivery_module.DATA_DIR.mkdir(parents=True, exist_ok=True)

    yield tmp_path

    delivery_module.DATA_DIR = original_data_dir
    delivery_module.ROUTING_DECISIONS_FILE = original_file
    delivery_module._default_store = original_default_store


class TestDeliveryRecord:
    """Tests for DeliveryRecord dataclass."""

    def test_to_dict(self):
        record = DeliveryRecord(
            delivery_id="DEL-001",
            item_id="MSG-001",
            owner="TestOwner",
            routed_at="2026-04-15T12:00:00Z",
            reason="Test reason",
            subject="gov.queue.messages",
        )
        d = record.to_dict()
        assert d["delivery_id"] == "DEL-001"
        assert d["item_id"] == "MSG-001"
        assert d["owner"] == "TestOwner"
        assert d["routed_at"] == "2026-04-15T12:00:00Z"
        assert d["reason"] == "Test reason"
        assert d["subject"] == "gov.queue.messages"

    def test_from_dict(self):
        data = {
            "delivery_id": "DEL-002",
            "item_id": "MSG-002",
            "owner": "OwnerB",
            "routed_at": "2026-04-15T13:00:00Z",
            "reason": "Reason B",
            "subject": "gov.queue.messages",
        }
        record = DeliveryRecord.from_dict(data)
        assert record.delivery_id == "DEL-002"
        assert record.item_id == "MSG-002"
        assert record.owner == "OwnerB"


class TestRoutingDeliveryStore:
    """Tests for RoutingDeliveryStore."""

    def test_add_and_get(self):
        store = get_store()
        record = DeliveryRecord(
            delivery_id="DEL-TEST-001",
            item_id="MSG-TEST-001",
            owner="TestOwner",
            routed_at="2026-04-15T14:00:00Z",
            reason="Add test",
        )
        store.add(record)
        retrieved = store.get("DEL-TEST-001")
        assert retrieved is not None
        assert retrieved.delivery_id == "DEL-TEST-001"
        assert retrieved.owner == "TestOwner"

    def test_get_nonexistent(self):
        store = get_store()
        result = store.get("NONEXISTENT")
        assert result is None

    def test_list_all(self):
        store = get_store()
        record1 = DeliveryRecord(
            delivery_id="DEL-LIST-001",
            item_id="MSG-001",
            owner="OwnerA",
            routed_at="2026-04-15T15:00:00Z",
            reason="Reason A",
        )
        record2 = DeliveryRecord(
            delivery_id="DEL-LIST-002",
            item_id="MSG-002",
            owner="OwnerB",
            routed_at="2026-04-15T15:01:00Z",
            reason="Reason B",
        )
        store.add(record1)
        store.add(record2)
        all_records = store.list_all()
        assert len(all_records) == 2

    def test_list_by_owner(self):
        store = get_store()
        store.add(DeliveryRecord(
            delivery_id="DEL-FILTER-001",
            item_id="MSG-001",
            owner="SpecificOwner",
            routed_at="2026-04-15T16:00:00Z",
            reason="Filter test",
        ))
        store.add(DeliveryRecord(
            delivery_id="DEL-FILTER-002",
            item_id="MSG-002",
            owner="OtherOwner",
            routed_at="2026-04-15T16:01:00Z",
            reason="Filter test",
        ))
        filtered = store.list_by_owner("SpecificOwner")
        assert len(filtered) == 1
        assert filtered[0].owner == "SpecificOwner"

    def test_clear(self):
        store = get_store()
        store.add(DeliveryRecord(
            delivery_id="DEL-CLEAR-001",
            item_id="MSG-001",
            owner="Owner",
            routed_at="2026-04-15T17:00:00Z",
            reason="Clear test",
        ))
        store.clear()
        assert len(store.list_all()) == 0


class TestDeliverRouted:
    """Tests for deliver_routed()."""

    def test_deliver_routed_returns_delivery_record(self, monkeypatch):
        # Patch nats_transport.publish to avoid actual NATS calls
        def mock_publish(subject, payload):
            pass
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        from governance.routing.rules import OwnershipDecision
        ownership = OwnershipDecision(
            owner="TestExecutor",
            should_escalate=False,
            return_target="CallerAgent",
            reason="Test delivery",
        )
        item = {"message_id": "MSG-DELIVER-001", "payload": {"data": "test"}}

        record = deliver_routed(item, ownership)

        assert record is not None
        assert record.item_id == "MSG-DELIVER-001"
        assert record.owner == "TestExecutor"
        assert "Test delivery" in record.reason
        assert record.subject == "gov.queue.messages"
        assert record.delivery_id.startswith("DEL-")

    def test_deliver_routed_publishes_to_nats(self, monkeypatch):
        call_log = []
        def mock_publish(subject, payload):
            call_log.append((subject, payload))
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        from governance.routing.rules import OwnershipDecision
        ownership = OwnershipDecision(
            owner="Executor",
            should_escalate=False,
            return_target="Caller",
            reason="NATS test",
        )
        item = {"message_id": "MSG-NASTEST", "payload": {"key": "value"}}

        deliver_routed(item, ownership)

        assert len(call_log) == 1
        subject, payload_bytes = call_log[0]
        assert subject == "gov.queue.messages"
        payload = json.loads(payload_bytes.decode("utf-8"))
        assert payload["owner"] == "Executor"
        assert payload["message_id"] == "MSG-NASTEST"

    def test_deliver_routed_records_delivery(self, monkeypatch):
        def mock_publish(subject, payload):
            pass
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        from governance.routing.rules import OwnershipDecision
        ownership = OwnershipDecision(
            owner="RecordedOwner",
            should_escalate=True,
            return_target="ReturnTarget",
            reason="Recording test",
        )
        item = {"message_id": "MSG-RECORD", "payload": {}}

        record = deliver_routed(item, ownership)

        store = get_store()
        retrieved = store.get(record.delivery_id)
        assert retrieved is not None
        assert retrieved.owner == "RecordedOwner"

    def test_deliver_routed_without_message_id_uses_item_id(self, monkeypatch):
        def mock_publish(subject, payload):
            pass
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        from governance.routing.rules import OwnershipDecision
        ownership = OwnershipDecision(
            owner="Owner",
            should_escalate=False,
            return_target="Target",
            reason="Item ID test",
        )
        item = {"item_id": "TASK-001", "payload": {}}

        record = deliver_routed(item, ownership)

        assert record.item_id == "TASK-001"

    def test_deliver_routed_without_any_id_generates_uuid(self, monkeypatch):
        def mock_publish(subject, payload):
            pass
        monkeypatch.setattr("governance.queue.nats_transport.publish", mock_publish)

        from governance.routing.rules import OwnershipDecision
        ownership = OwnershipDecision(
            owner="Owner",
            should_escalate=False,
            return_target="Target",
            reason="UUID test",
        )
        item = {"payload": {}}

        record = deliver_routed(item, ownership)

        assert record.item_id is not None
        assert len(record.item_id) > 0
