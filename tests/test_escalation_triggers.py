"""
tests/test_escalation_triggers.py
V1.9 Sprint 2, Task T7.1
Tests for escalation triggers (check_escalation, escalate, get_active_escalation).
"""

import json
import os
import sys
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure local transport mode for tests
os.environ["QUEUE_TRANSPORT"] = "local"

# Patch NATS before importing escalation
_mock_publish = MagicMock()
with patch("governance.queue.nats_transport._bypass_nats", True):
    with patch("governance.queue.nats_transport.publish", _mock_publish):
        from governance.escalation import triggers
        from governance.escalation.triggers import (
            check_escalation,
            escalate,
            get_active_escalation,
        )
        from governance.escalation.hold_state import (
            EscalationState,
            EscalationRecord,
            hold_escalation,
            get_escalation,
            list_escalations,
            DATA_DIR,
            ESCALATIONS_FILE,
        )
        from governance.queue.models import Message, MessageState, MessageType
        from governance.task.models import Task, TaskLifecycleState

import pytest


@pytest.fixture(autouse=True)
def clean_escalation_data():
    """Clean escalation data files before and after each test."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ESCALATIONS_FILE.exists():
        ESCALATIONS_FILE.unlink()
    yield
    if ESCALATIONS_FILE.exists():
        ESCALATIONS_FILE.unlink()


class TestEscalationTriggers:
    """Tests for check_escalation and escalate."""

    def test_check_escalation_approval_required_triggers(self):
        """Approval-required transition triggers escalation."""
        msg = Message(
            sender="planner",
            receiver="tdd",
            type=MessageType.REQUEST,
            payload={"metadata": {"requires_approval": True}},
            state=MessageState.WAITING,
        )
        context = {"escalated_by": "planner", "delegated_authority": {}}

        result = check_escalation(msg, context)

        assert result is not None
        assert isinstance(result, EscalationRecord)
        assert result.item_id == msg.message_id
        assert result.state == EscalationState.ESCALATED

    def test_check_escalation_no_trigger_when_authority_sufficient(self):
        """No escalation when item is within delegated authority."""
        msg = Message(
            sender="planner",
            receiver="tdd",
            type=MessageType.REQUEST,
            payload={"metadata": {"requires_approval": False}},
            state=MessageState.CLAIMED,
        )
        context = {
            "escalated_by": "planner",
            "delegated_authority": {
                "max_blocker_severity": "high",
                "max_approval_scope": "high",
            },
        }

        result = check_escalation(msg, context)

        assert result is None

    def test_check_escalation_blocker_exceeds_authority(self):
        """Blocker with severity above threshold triggers escalation."""
        msg = Message(
            sender="planner",
            receiver="tdd",
            type=MessageType.REQUEST,
            payload={},
            state=MessageState.WAITING,
        )
        context = {
            "escalated_by": "planner",
            "delegated_authority": {"max_blocker_severity": "low"},
            "blocker": {"severity": "critical"},
        }

        result = check_escalation(msg, context)

        assert result is not None
        assert result.item_id == msg.message_id
        assert "critical" in result.reason.lower() or "blocker" in result.reason.lower()

    def test_check_escalation_validation_failure_exceeds_authority(self):
        """Validation failure with scope above threshold triggers escalation."""
        msg = Message(
            sender="planner",
            receiver="tdd",
            type=MessageType.REQUEST,
            payload={},
            state=MessageState.NEW,
        )
        context = {
            "escalated_by": "planner",
            "delegated_authority": {"max_approval_scope": "low"},
            "validation_failed": True,
            "validation_error": {"required_scope": "high", "message": "scope_too_wide"},
        }

        result = check_escalation(msg, context)

        assert result is not None
        assert result.item_id == msg.message_id

    def test_check_escalation_validation_failure_safe_with_strong_authority(self):
        """Validation failure within authority does NOT trigger escalation."""
        msg = Message(
            sender="planner",
            receiver="tdd",
            type=MessageType.REQUEST,
            payload={},
            state=MessageState.NEW,
        )
        context = {
            "escalated_by": "planner",
            "delegated_authority": {"max_approval_scope": "critical"},
            "validation_failed": True,
            "validation_error": {"required_scope": "high"},
        }

        result = check_escalation(msg, context)

        assert result is None

    def test_escalate_creates_record(self):
        """escalate() creates an escalation record and publishes to NATS."""
        item_id = "test-item-001"
        reason = "test escalation reason"
        context = {"escalated_by": "planner"}

        with patch("governance.escalation.triggers.nats_transport.publish", MagicMock()) as mock_pub:
            record = escalate(item_id, reason, context)

        assert record is not None
        assert record.item_id == item_id
        assert record.reason == reason
        assert record.escalated_by == "planner"
        assert record.state == EscalationState.ESCALATED

    def test_escalate_publishes_to_nats(self):
        """escalate() publishes to gov.escalations NATS subject."""
        item_id = "test-item-002"
        reason = "test reason"
        context = {"escalated_by": "tdd"}

        with patch("governance.escalation.triggers.nats_transport.publish", MagicMock()) as mock_pub:
            record = escalate(item_id, reason, context)
            mock_pub.assert_called_once()
            call_args = mock_pub.call_args
            assert call_args[0][0] == "gov.escalations"

    def test_get_active_escalation_found(self):
        """get_active_escalation returns record when one exists for item_id."""
        item_id = "test-item-active"
        hold_escalation("esc-001", item_id, "test reason")

        active = get_active_escalation(item_id)

        assert active is not None
        assert active.item_id == item_id
        assert active.state == EscalationState.ESCALATED

    def test_get_active_escalation_not_found(self):
        """get_active_escalation returns None when no active escalation."""
        active = get_active_escalation("nonexistent-item")
        assert active is None

    def test_get_active_escalation_decided_not_returned(self):
        """get_active_escalation returns None for DECIDED escalation."""
        item_id = "test-item-decided"
        hold_escalation("esc-002", item_id, "test reason")

        from governance.escalation.hold_state import update_escalation_state
        update_escalation_state("esc-002", EscalationState.DECIDED, decision_id="dec-001")

        active = get_active_escalation(item_id)
        assert active is None


class TestEscalationHoldState:
    """Tests for hold_state storage (escalation records)."""

    def test_hold_escalation_creates_new_record(self):
        """hold_escalation creates a new ESCALATED record."""
        record = hold_escalation("esc-100", "item-100", "test reason")

        assert record.escalation_id == "esc-100"
        assert record.item_id == "item-100"
        assert record.reason == "test reason"
        assert record.state == EscalationState.ESCALATED
        assert record.decision_id is None

    def test_hold_escalation_idempotent_for_same_item(self):
        """hold_escalation returns existing active escalation for same item."""
        record1 = hold_escalation("esc-101", "item-101", "first reason")
        record2 = hold_escalation("esc-102", "item-101", "second reason")

        # Returns first, does not create duplicate
        assert record1.item_id == record2.item_id
        all_recs = list_escalations()
        assert len(all_recs) == 1

    def test_get_escalation_found(self):
        """get_escalation retrieves existing record."""
        hold_escalation("esc-200", "item-200", "test reason")
        record = get_escalation("esc-200")

        assert record is not None
        assert record.escalation_id == "esc-200"

    def test_get_escalation_not_found(self):
        """get_escalation returns None for nonexistent ID."""
        record = get_escalation("nonexistent")
        assert record is None

    def test_list_escalations_all(self):
        """list_escalations returns all records."""
        hold_escalation("esc-300", "item-300", "reason 1")
        hold_escalation("esc-301", "item-301", "reason 2")

        records = list_escalations()
        assert len(records) == 2

    def test_list_escalations_filtered_by_state(self):
        """list_escalations filters by EscalationState."""
        hold_escalation("esc-400", "item-400", "reason 1")
        hold_escalation("esc-401", "item-401", "reason 2")

        from governance.escalation.hold_state import update_escalation_state
        update_escalation_state("esc-401", EscalationState.DECIDED, decision_id="dec-401")

        escalated = list_escalations(status=EscalationState.ESCALATED)
        decided = list_escalations(status=EscalationState.DECIDED)

        assert len(escalated) == 1
        assert escalated[0].escalation_id == "esc-400"
        assert len(decided) == 1
        assert decided[0].escalation_id == "esc-401"

    def test_update_escalation_state_transitions(self):
        """update_escalation_state transitions ESCALATED -> DECIDED."""
        hold_escalation("esc-500", "item-500", "reason")

        from governance.escalation.hold_state import (
            update_escalation_state,
            EscalationState,
        )
        update_escalation_state("esc-500", EscalationState.DECIDED, decision_id="dec-500")

        record = get_escalation("esc-500")
        assert record is not None
        assert record.state == EscalationState.DECIDED
        assert record.decision_id == "dec-500"

    def test_update_escalation_state_decided_to_returned(self):
        """update_escalation_state transitions DECIDED -> RETURNED."""
        hold_escalation("esc-600", "item-600", "reason")
        from governance.escalation.hold_state import (
            update_escalation_state,
            EscalationState,
        )
        update_escalation_state("esc-600", EscalationState.DECIDED, decision_id="dec-600")
        update_escalation_state("esc-600", EscalationState.RETURNED)

        record = get_escalation("esc-600")
        assert record is not None
        assert record.state == EscalationState.RETURNED

    def test_update_escalation_state_illegal_transition(self):
        """Illegal escalation state transition raises ValueError."""
        hold_escalation("esc-700", "item-700", "reason")
        from governance.escalation.hold_state import (
            update_escalation_state,
            EscalationState,
        )
        update_escalation_state("esc-700", EscalationState.DECIDED, decision_id="dec-700")

        with pytest.raises(ValueError):
            update_escalation_state("esc-700", EscalationState.ESCALATED)

    def test_update_escalation_state_not_found(self):
        """update_escalation_state raises KeyError for nonexistent escalation."""
        from governance.escalation.hold_state import (
            update_escalation_state,
            EscalationState,
        )
        with pytest.raises(KeyError):
            update_escalation_state("nonexistent", EscalationState.DECIDED)

    def test_evidence_log_created(self):
        """Escalation events are logged to evidence/escalation/YYYY-MM-DD.jsonl."""
        from governance.escalation.hold_state import EVIDENCE_DIR

        hold_escalation("esc-800", "item-800", "reason")

        today = Path(__file__).resolve().parent.parent / "evidence" / "escalation"
        import datetime
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        evidence_file = today / f"{date_str}.jsonl"

        assert evidence_file.exists()
