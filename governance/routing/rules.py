"""
governance/routing/rules.py
V1.9 Sprint 2, Task T6.1 — Ownership Determination Rules

Implements the routing decision table for pending items.
Each rule is an explicit function (not hardcoded conditionals).
Returns an OwnershipDecision with: owner, should_escalate, return_target, reason.

PRD Reference: V1.9_PRD_V0_3.md §5.C (Req 22-26)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PendingItemType(str, Enum):
    """Classification of pending item types that require routing."""
    CLARIFICATION_REQUEST = "clarification_request"
    IMPLEMENTATION_TASK_HANDOFF = "implementation_task_handoff"
    BLOCKER_REPORT = "blocker_report"
    APPROVAL_REQUIRED_TRANSITION = "approval_required_transition"
    VALIDATION_FAILURE = "validation_failure"


@dataclass
class OwnershipDecision:
    """
    Routing decision returned by determine_ownership().

    Fields:
        owner: primary owner participant name
        should_escalate: True if item should be escalated rather than handled at current level
        return_target: participant to return result to (originating Agent, upstream coordinator, etc.)
        reason: human-readable justification for the decision
    """
    owner: str
    should_escalate: bool
    return_target: str
    reason: str


def _determine_clarification_ownership(context: dict) -> OwnershipDecision:
    """
    Routing for clarification requests.

    Primary Owner: Planner or originating Agent owner
    Escalate When: requirement ambiguity exceeds delegated authority
    Return Target: originating Agent
    """
    planner = context.get("planner", "Planner")
    sender = context.get("sender", "Agent")
    originating_agent = context.get("originating_agent", sender)
    ambiguity_exceeds_authority = context.get("ambiguity_exceeds_authority", False)

    # Determine primary owner:
    # - assigned_owner takes precedence if set and differs from planner
    # - originating_agent is used when it was explicitly set (key present)
    #   AND differs from planner
    # - planner is the default primary owner
    _assigned_owner = context.get("assigned_owner")
    _orig_in_context = "originating_agent" in context

    if _assigned_owner is not None and _assigned_owner != planner:
        owner = _assigned_owner
    elif _orig_in_context and originating_agent != planner:
        owner = originating_agent
    else:
        owner = planner

    should_escalate = ambiguity_exceeds_authority
    return_target = originating_agent

    if should_escalate:
        reason = (
            f"Requirement ambiguity exceeds delegated authority; "
            f"escalated from {owner} to governance/PMO surface."
        )
        return OwnershipDecision(
            owner="governance",
            should_escalate=True,
            return_target=return_target,
            reason=reason,
        )

    reason = (
        f"Clarification request routed to {owner}; "
        f"return to {return_target} when resolved."
    )
    return OwnershipDecision(
        owner=owner,
        should_escalate=False,
        return_target=return_target,
        reason=reason,
    )


def _determine_implementation_handoff_ownership(context: dict) -> OwnershipDecision:
    """
    Routing for implementation task handoffs.

    Primary Owner: TDD / assigned executor
    Escalate When: execution path blocked by approval or scope boundary
    Return Target: upstream coordinator
    """
    tdd = context.get("tdd", "TDD")
    assigned_executor = context.get("assigned_executor", tdd)
    upstream_coordinator = context.get("upstream_coordinator", context.get("sender", "Coordinator"))
    blocked_by_approval = context.get("blocked_by_approval", False)
    blocked_by_scope = context.get("blocked_by_scope", False)

    owner = assigned_executor
    should_escalate = blocked_by_approval or blocked_by_scope
    return_target = upstream_coordinator

    if should_escalate:
        blocks = []
        if blocked_by_approval:
            blocks.append("approval")
        if blocked_by_scope:
            blocks.append("scope boundary")
        reason = (
            f"Implementation handoff blocked by {', '.join(blocks)}; "
            f"escalated from {owner} to governance surface."
        )
        return OwnershipDecision(
            owner="governance",
            should_escalate=True,
            return_target=return_target,
            reason=reason,
        )

    reason = (
        f"Implementation task handoff routed to {owner}; "
        f"return to {return_target} when complete."
    )
    return OwnershipDecision(
        owner=owner,
        should_escalate=False,
        return_target=return_target,
        reason=reason,
    )


def _determine_blocker_ownership(context: dict) -> OwnershipDecision:
    """
    Routing for blocker reports.

    Primary Owner: governance / PMO surface
    Escalate When: blocker exceeds delegated resolution authority
    Return Target: originating Agent or Alex
    """
    governance = context.get("governance_surface", "governance")
    originating_agent = context.get("originating_agent", context.get("sender", "Agent"))
    alex = context.get("alex", "Alex")
    exceeds_resolution_authority = context.get("exceeds_resolution_authority", False)

    if exceeds_resolution_authority:
        # Blocker too significant for governance — escalate to Alex
        reason = (
            f"Blocker exceeds delegated resolution authority; "
            f"escalated from {governance} to Alex."
        )
        return OwnershipDecision(
            owner=alex,
            should_escalate=True,
            return_target=originating_agent,
            reason=reason,
        )

    reason = (
        f"Blocker report routed to {governance} PMO surface; "
        f"return to {originating_agent} when resolved."
    )
    return OwnershipDecision(
        owner=governance,
        should_escalate=False,
        return_target=originating_agent,
        reason=reason,
    )


def _determine_approval_ownership(context: dict) -> OwnershipDecision:
    """
    Routing for approval-required transitions.

    Primary Owner: Alex
    Escalate When: always, if authority gate is human-owned
    Return Target: waiting participant
    """
    alex = context.get("alex", "Alex")
    waiting_participant = context.get("waiting_participant", context.get("sender", "Agent"))
    authority_gate_human_owned = context.get("authority_gate_human_owned", True)

    if authority_gate_human_owned:
        # Always route to Alex for human-owned authority gates
        reason = (
            f"Approval-required transition: authority gate is human-owned; "
            f"routed to {alex} for decision."
        )
        return OwnershipDecision(
            owner=alex,
            should_escalate=False,  # Alex is the destination, not an escalation
            return_target=waiting_participant,
            reason=reason,
        )

    # If not human-owned, could route differently (governance decision)
    reason = (
        f"Approval-required transition for non-human gate; "
        f"routed to governance for decision."
    )
    return OwnershipDecision(
        owner="governance",
        should_escalate=False,
        return_target=waiting_participant,
        reason=reason,
    )


def _determine_validation_failure_ownership(context: dict) -> OwnershipDecision:
    """
    Routing for validation failures.

    Primary Owner: jarvis-qa / responsible executor
    Escalate When: failure requires scope or authority decision
    Return Target: originating Agent / Planner
    """
    jarvis_qa = context.get("jarvis_qa", "jarvis-qa")
    responsible_executor = context.get("responsible_executor", jarvis_qa)
    originating_agent = context.get("originating_agent", context.get("sender", "Agent"))
    planner = context.get("planner", "Planner")
    requires_scope_decision = context.get("requires_scope_decision", False)
    requires_authority_decision = context.get("requires_authority_decision", False)

    owner = responsible_executor
    should_escalate = requires_scope_decision or requires_authority_decision
    return_target = context.get("return_target", originating_agent)

    if should_escalate:
        decision_points = []
        if requires_scope_decision:
            decision_points.append("scope")
        if requires_authority_decision:
            decision_points.append("authority")
        reason = (
            f"Validation failure requires {', '.join(decision_points)} decision; "
            f"escalated from {owner} to {planner}."
        )
        return OwnershipDecision(
            owner=planner,
            should_escalate=True,
            return_target=return_target,
            reason=reason,
        )

    reason = (
        f"Validation failure routed to {owner}; "
        f"return to {return_target} when resolved."
    )
    return OwnershipDecision(
        owner=owner,
        should_escalate=False,
        return_target=return_target,
        reason=reason,
    )


def determine_ownership(item_type: PendingItemType, context: dict) -> OwnershipDecision:
    """
    Determine routing ownership for a pending item.

    Args:
        item_type: The type of pending item from PendingItemType enum
        context: Dict containing contextual information for routing decision.
                 Expected keys vary by item_type (see individual rule functions).

    Returns:
        OwnershipDecision with owner, should_escalate, return_target, reason.

    Raises:
        ValueError: if item_type is not a valid PendingItemType
    """
    if not isinstance(item_type, PendingItemType):
        try:
            item_type = PendingItemType(item_type)
        except ValueError:
            raise ValueError(
                f"Unknown pending item type: {item_type!r}. "
                f"Valid types: {[t.value for t in PendingItemType]}"
            )

    if item_type == PendingItemType.CLARIFICATION_REQUEST:
        return _determine_clarification_ownership(context)
    elif item_type == PendingItemType.IMPLEMENTATION_TASK_HANDOFF:
        return _determine_implementation_handoff_ownership(context)
    elif item_type == PendingItemType.BLOCKER_REPORT:
        return _determine_blocker_ownership(context)
    elif item_type == PendingItemType.APPROVAL_REQUIRED_TRANSITION:
        return _determine_approval_ownership(context)
    elif item_type == PendingItemType.VALIDATION_FAILURE:
        return _determine_validation_failure_ownership(context)
    else:
        # Should not reach here, but defensive
        raise ValueError(f"Unhandled pending item type: {item_type.value}")
