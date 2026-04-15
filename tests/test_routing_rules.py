"""
tests/test_routing_rules.py
V1.9 Sprint 2, FB3 — Unit tests for governance.routing.rules
"""

import pytest
from governance.routing.rules import (
    PendingItemType,
    OwnershipDecision,
    determine_ownership,
    _determine_clarification_ownership,
    _determine_implementation_handoff_ownership,
    _determine_blocker_ownership,
    _determine_approval_ownership,
    _determine_validation_failure_ownership,
)


class TestPendingItemType:
    """Tests for PendingItemType enum."""

    def test_all_types_present(self):
        assert PendingItemType.CLARIFICATION_REQUEST.value == "clarification_request"
        assert PendingItemType.IMPLEMENTATION_TASK_HANDOFF.value == "implementation_task_handoff"
        assert PendingItemType.BLOCKER_REPORT.value == "blocker_report"
        assert PendingItemType.APPROVAL_REQUIRED_TRANSITION.value == "approval_required_transition"
        assert PendingItemType.VALIDATION_FAILURE.value == "validation_failure"


class TestDetermineOwnership:
    """Tests for determine_ownership() routing decisions."""

    # ---- Clarification Request ----

    def test_clarification_routes_to_planner_by_default(self):
        decision = determine_ownership(
            PendingItemType.CLARIFICATION_REQUEST,
            {"planner": "Planner", "sender": "Agent"}
        )
        assert decision.owner == "Planner"
        assert decision.should_escalate is False
        assert "Planner" in decision.reason

    def test_clarification_routes_to_originating_agent_owner(self):
        decision = determine_ownership(
            PendingItemType.CLARIFICATION_REQUEST,
            {"originating_agent": "DevAgent", "sender": "OtherAgent"}
        )
        assert decision.owner == "DevAgent"
        assert decision.should_escalate is False

    def test_clarification_escalates_when_ambiguity_exceeds_authority(self):
        decision = determine_ownership(
            PendingItemType.CLARIFICATION_REQUEST,
            {"planner": "Planner", "ambiguity_exceeds_authority": True, "sender": "Agent"}
        )
        assert decision.owner == "governance"
        assert decision.should_escalate is True
        assert decision.return_target == "Agent"

    # ---- Implementation Task Handoff ----

    def test_implementation_handoff_routes_to_tdd(self):
        decision = determine_ownership(
            PendingItemType.IMPLEMENTATION_TASK_HANDOFF,
            {"tdd": "TDD", "sender": "Coordinator"}
        )
        assert decision.owner == "TDD"
        assert decision.should_escalate is False
        assert decision.return_target == "Coordinator"

    def test_implementation_handoff_routes_to_assigned_executor(self):
        decision = determine_ownership(
            PendingItemType.IMPLEMENTATION_TASK_HANDOFF,
            {"tdd": "TDD", "assigned_executor": "WorkerBot", "sender": "Coordinator"}
        )
        assert decision.owner == "WorkerBot"
        assert decision.should_escalate is False

    def test_implementation_handoff_escalates_when_blocked_by_approval(self):
        decision = determine_ownership(
            PendingItemType.IMPLEMENTATION_TASK_HANDOFF,
            {"tdd": "TDD", "blocked_by_approval": True, "sender": "Coordinator"}
        )
        assert decision.owner == "governance"
        assert decision.should_escalate is True
        assert "approval" in decision.reason

    def test_implementation_handoff_escalates_when_blocked_by_scope(self):
        decision = determine_ownership(
            PendingItemType.IMPLEMENTATION_TASK_HANDOFF,
            {"tdd": "TDD", "blocked_by_scope": True, "sender": "Coordinator"}
        )
        assert decision.owner == "governance"
        assert decision.should_escalate is True
        assert "scope boundary" in decision.reason

    # ---- Blocker Report ----

    def test_blocker_routes_to_governance_by_default(self):
        decision = determine_ownership(
            PendingItemType.BLOCKER_REPORT,
            {"sender": "Agent"}
        )
        assert decision.owner == "governance"
        assert decision.should_escalate is False
        assert decision.return_target == "Agent"

    def test_blocker_escalates_to_alex_when_exceeds_authority(self):
        decision = determine_ownership(
            PendingItemType.BLOCKER_REPORT,
            {"exceeds_resolution_authority": True, "alex": "Alex", "sender": "Agent"}
        )
        assert decision.owner == "Alex"
        assert decision.should_escalate is True
        assert decision.return_target == "Agent"

    # ---- Approval Required Transition ----

    def test_approval_routes_to_alex_when_human_owned(self):
        decision = determine_ownership(
            PendingItemType.APPROVAL_REQUIRED_TRANSITION,
            {"alex": "Alex", "waiting_participant": "Worker", "authority_gate_human_owned": True}
        )
        assert decision.owner == "Alex"
        assert decision.should_escalate is False
        assert decision.return_target == "Worker"

    def test_approval_routes_to_governance_when_not_human_owned(self):
        decision = determine_ownership(
            PendingItemType.APPROVAL_REQUIRED_TRANSITION,
            {"alex": "Alex", "waiting_participant": "Worker", "authority_gate_human_owned": False}
        )
        assert decision.owner == "governance"
        assert decision.should_escalate is False

    # ---- Validation Failure ----

    def test_validation_failure_routes_to_jarvis_qa_by_default(self):
        decision = determine_ownership(
            PendingItemType.VALIDATION_FAILURE,
            {"sender": "Agent"}
        )
        assert decision.owner == "jarvis-qa"
        assert decision.should_escalate is False
        assert decision.return_target == "Agent"

    def test_validation_failure_escalates_when_requires_scope_decision(self):
        decision = determine_ownership(
            PendingItemType.VALIDATION_FAILURE,
            {"requires_scope_decision": True, "planner": "Planner", "sender": "Agent"}
        )
        assert decision.owner == "Planner"
        assert decision.should_escalate is True
        assert "scope" in decision.reason

    def test_validation_failure_escalates_when_requires_authority_decision(self):
        decision = determine_ownership(
            PendingItemType.VALIDATION_FAILURE,
            {"requires_authority_decision": True, "planner": "Planner", "sender": "Agent"}
        )
        assert decision.owner == "Planner"
        assert decision.should_escalate is True
        assert "authority" in decision.reason

    # ---- String input ----

    def test_determine_ownership_accepts_string_item_type(self):
        decision = determine_ownership("clarification_request", {"planner": "Planner", "sender": "Agent"})
        assert decision.owner == "Planner"
        assert decision.should_escalate is False

    def test_determine_ownership_raises_on_unknown_type(self):
        with pytest.raises(ValueError) as exc_info:
            determine_ownership("unknown_type", {})
        assert "Unknown pending item type" in str(exc_info.value)


class TestOwnershipDecision:
    """Tests for OwnershipDecision dataclass."""

    def test_ownership_decision_fields(self):
        decision = OwnershipDecision(
            owner="TestOwner",
            should_escalate=True,
            return_target="Caller",
            reason="Test reason",
        )
        assert decision.owner == "TestOwner"
        assert decision.should_escalate is True
        assert decision.return_target == "Caller"
        assert decision.reason == "Test reason"

    def test_ownership_decision_has_reason(self):
        decision = determine_ownership(
            PendingItemType.CLARIFICATION_REQUEST,
            {"planner": "Planner", "sender": "Agent"}
        )
        assert isinstance(decision.reason, str)
        assert len(decision.reason) > 0
