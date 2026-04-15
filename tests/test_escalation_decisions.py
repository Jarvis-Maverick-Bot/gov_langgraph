"""
tests/test_escalation_decisions.py
V1.9 Sprint 2, Task T7.3
Tests for escalation decision recording (record_decision, get_decision, get_decision_for_escalation).
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure local transport mode for tests
os.environ["QUEUE_TRANSPORT"] = "local"

with patch("governance.queue.nats_transport._bypass_nats", True):
    with patch("governance.queue.nats_transport.publish", MagicMock()):
        from governance.escalation import decision_record as dr
        from governance.escalation.decision_record import (
            DecisionValue,
            DecisionRecord,
            record_decision,
            get_decision,
            get_decision_for_escalation,
            DATA_DIR,
            DECISIONS_FILE,
        )
        from governance.escalation import hold_state as hs
        from governance.escalation.hold_state import (
            EscalationState,
            hold_escalation,
        )

import pytest


@pytest.fixture(autouse=True)
def clean_decision_data():
    """Clean decisions data files before and after each test."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DECISIONS_FILE.exists():
        DECISIONS_FILE.unlink()
    yield
    if DECISIONS_FILE.exists():
        DECISIONS_FILE.unlink()


@pytest.fixture(autouse=True)
def clean_escalation_data():
    """Clean escalation data files before and after each test."""
    from governance.escalation.hold_state import ESCALATIONS_FILE, DATA_DIR as HS_DATA_DIR
    HS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ESCALATIONS_FILE.exists():
        ESCALATIONS_FILE.unlink()
    yield
    if ESCALATIONS_FILE.exists():
        ESCALATIONS_FILE.unlink()


class TestDecisionRecord:
    """Tests for decision recording."""

    def test_record_decision_approve(self):
        """record_decision with APPROVE creates a DecisionRecord."""
        # First create an escalation
        esc_record = hold_escalation("esc-001", "item-001", "approval needed")

        decision = record_decision("esc-001", DecisionValue.APPROVE, "looks good, proceed")

        assert decision is not None
        assert decision.escalation_id == "esc-001"
        assert decision.decision == DecisionValue.APPROVE
        assert decision.note == "looks good, proceed"
        assert decision.decided_by == "Alex"
        assert decision.decided_at is not None

    def test_record_decision_reject(self):
        """record_decision with REJECT creates a DecisionRecord."""
        hold_escalation("esc-002", "item-002", "scope concern")

        decision = record_decision("esc-002", DecisionValue.REJECT, "too risky, rework required")

        assert decision.decision == DecisionValue.REJECT
        assert decision.note == "too risky, rework required"

    def test_record_decision_continue(self):
        """record_decision with CONTINUE creates a DecisionRecord."""
        hold_escalation("esc-003", "item-003", "minor issue")

        decision = record_decision("esc-003", DecisionValue.CONTINUE, "minor, continue anyway")

        assert decision.decision == DecisionValue.CONTINUE

    def test_record_decision_stop(self):
        """record_decision with STOP creates a DecisionRecord."""
        hold_escalation("esc-004", "item-004", "critical blocker")

        decision = record_decision("esc-004", DecisionValue.STOP, "halt immediately")

        assert decision.decision == DecisionValue.STOP

    def test_record_decision_transitions_escalation(self):
        """record_decision transitions escalation from ESCALATED to DECIDED."""
        hold_escalation("esc-005", "item-005", "test")

        record_decision("esc-005", DecisionValue.APPROVE, "approved")

        escalation = hs.get_escalation("esc-005")
        assert escalation is not None
        assert escalation.state == EscalationState.DECIDED

    def test_record_decision_links_decision_id_to_escalation(self):
        """record_decision links decision_id to escalation record."""
        hold_escalation("esc-006", "item-006", "test")

        decision = record_decision("esc-006", DecisionValue.APPROVE, "ok")

        escalation = hs.get_escalation("esc-006")
        assert escalation.decision_id == decision.decision_id

    def test_record_decision_unique_ids(self):
        """Each decision has a unique decision_id."""
        hold_escalation("esc-007", "item-007", "test 1")
        hold_escalation("esc-008", "item-008", "test 2")

        dec1 = record_decision("esc-007", DecisionValue.APPROVE, "first")
        dec2 = record_decision("esc-008", DecisionValue.REJECT, "second")

        assert dec1.decision_id != dec2.decision_id

    def test_get_decision_found(self):
        """get_decision retrieves existing decision by decision_id."""
        hold_escalation("esc-010", "item-010", "test")
        decision = record_decision("esc-010", DecisionValue.APPROVE, "ok")

        retrieved = get_decision(decision.decision_id)

        assert retrieved is not None
        assert retrieved.decision_id == decision.decision_id
        assert retrieved.decision == DecisionValue.APPROVE

    def test_get_decision_not_found(self):
        """get_decision returns None for nonexistent decision_id."""
        retrieved = get_decision("nonexistent-decision-id")
        assert retrieved is None

    def test_get_decision_for_escalation_found(self):
        """get_decision_for_escalation retrieves decision by escalation_id."""
        hold_escalation("esc-020", "item-020", "test")
        created = record_decision("esc-020", DecisionValue.REJECT, "rejected")

        retrieved = get_decision_for_escalation("esc-020")

        assert retrieved is not None
        assert retrieved.decision_id == created.decision_id
        assert retrieved.escalation_id == "esc-020"

    def test_get_decision_for_escalation_not_found(self):
        """get_decision_for_escalation returns None for nonexistent escalation_id."""
        retrieved = get_decision_for_escalation("nonexistent-esc")
        assert retrieved is None

    def test_decision_record_to_dict_roundtrip(self):
        """DecisionRecord serializes and deserializes correctly."""
        hold_escalation("esc-030", "item-030", "test")
        original = record_decision("esc-030", DecisionValue.STOP, "full stop")

        retrieved = get_decision(original.decision_id)

        assert retrieved is not None
        assert retrieved.decision == original.decision
        assert retrieved.note == original.note
        assert retrieved.decided_by == original.decided_by

    def test_decision_record_decided_at_is_iso_timestamp(self):
        """DecisionRecord.decided_at is a valid ISO format timestamp."""
        import datetime

        hold_escalation("esc-040", "item-040", "test")
        decision = record_decision("esc-040", DecisionValue.APPROVE, "ok")

        # Should not raise
        parsed = datetime.datetime.fromisoformat(decision.decided_at)
        assert parsed is not None


class TestDecisionEvidenceLog:
    """Tests for decision evidence logging."""

    def test_decision_recorded_logs_evidence(self):
        """decision_recorded event is logged to evidence/escalation/YYYY-MM-DD.jsonl."""
        from governance.escalation.hold_state import EVIDENCE_DIR
        import datetime
        import json

        hold_escalation("esc-050", "item-050", "test")
        record_decision("esc-050", DecisionValue.APPROVE, "ok")


        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        evidence_file = EVIDENCE_DIR / f"{today_str}.jsonl"

        # File should exist (may have entries from previous tests too)
        assert evidence_file.exists()

        # Read and check lines contain decision_recorded event
        with open(evidence_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Find the decision_recorded event (should appear before escalation_state_decided)
        events = [json.loads(l) for l in lines]
        decision_events = [e for e in events if e.get("event_type") == "decision_recorded"]
        assert len(decision_events) >= 1
        assert decision_events[-1]["escalation_id"] == "esc-050"

    def test_decision_note_preserved_in_evidence(self):
        """Decision note is preserved in evidence log."""
        from governance.escalation.hold_state import EVIDENCE_DIR
        import datetime
        import json

        hold_escalation("esc-060", "item-060", "test")
        record_decision("esc-060", DecisionValue.REJECT, "scope too wide, narrow down")

        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        evidence_file = EVIDENCE_DIR / f"{today_str}.jsonl"


        with open(evidence_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        events = [json.loads(l) for l in lines]
        decision_events = [e for e in events if e.get("event_type") == "decision_recorded"]
        assert len(decision_events) >= 1
        # Note is in the 'after' dict of decision_recorded event
        last_decision = decision_events[-1]
        assert "scope too wide" in str(last_decision.get("after", {}))
