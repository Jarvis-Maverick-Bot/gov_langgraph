"""
governance/escalation/triggers.py
V1.9 Sprint 2, Task T7.1
Explicit escalation triggers — fires when item exceeds delegated authority.

Per escalation-return flow:
    1. Item detected → check if within delegated authority
    2. If NO → escalate to Alex via NATS (gov.escalations)
    3. Return escalation record

Trigger conditions:
    - approval-required transition (always escalate if authority gate is human-owned)
    - blocker exceeds delegated resolution authority
    - validation failure requires scope/authority decision

Export:
    check_escalation(item, context) -> Optional[EscalationRecord]
    escalate(item_id, reason, context) -> EscalationRecord
"""

from typing import Any, Optional

from ..queue import nats_transport
from ..queue.models import Message, MessageState
from ..task.models import Task, TaskLifecycleState
from .hold_state import (
    EscalationRecord,
    hold_escalation,
    get_escalation,
    list_escalations,
    EscalationState,
)


# Singleton store — avoids repeated module-level singleton calls
_default_escalations_store: Optional[Any] = None


def _get_item_id(item: Any) -> str:
    """Extract the stable ID from a message or task."""
    if isinstance(item, Message):
        return item.message_id
    if isinstance(item, Task):
        return item.task_id
    # Fallback: assume item has an 'id' or 'message_id' field
    return getattr(item, "message_id", None) or getattr(item, "task_id", None) or str(item)


def _check_approval_required(item: Any) -> bool:
    """
    Check if the item has a transition or property indicating human approval is required.

    Examples:
    - A Message with payload.metadata.get("requires_approval") == True
    - A transition to a state that requires human gate
    - Any explicit flag in context
    """
    if isinstance(item, Message):
        payload = getattr(item, "payload", {}) or {}
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        if metadata.get("requires_approval"):
            return True
        # Also check if current state requires human authority
        if getattr(item, "state", None) == MessageState.WAITING:
            wait_reason = metadata.get("wait_reason", "")
            if "approval" in wait_reason.lower():
                return True
    if isinstance(item, Task):
        metadata = getattr(item, "metadata", {}) or {}
        if metadata.get("requires_approval"):
            return True
    return False


def _check_blocker_authority(item: Any, context: dict) -> bool:
    """
    Check if a blocker on the item exceeds what the delegated authority can resolve.

    A blocker exceeds authority if:
    - The item is blocked and resolution requires scope/time/resource beyond threshold
    - context["delegated_authority"] is exceeded
    """
    delegated_authority = context.get("delegated_authority", {})
    if not delegated_authority:
        # No delegated authority means everything must be escalated
        return True

    # Check blocker severity against authority thresholds
    blocker = context.get("blocker", {})
    if not blocker:
        return False

    severity = blocker.get("severity", "low")
    threshold = delegated_authority.get("max_blocker_severity", "low")

    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    sev_level = severity_order.get(severity, 0)
    threshold_level = severity_order.get(threshold, 0)

    return sev_level > threshold_level


def _check_validation_authority(item: Any, context: dict) -> bool:
    """
    Check if a validation failure on the item requires a scope/authority decision.

    Validation failure requires authority decision when:
    - Item failed validation and remediation requires scope expansion
    - Item failed validation and time/scope exceeds thresholds
    """
    if not context.get("validation_failed"):
        return False

    delegated_authority = context.get("delegated_authority", {})
    if not delegated_authority:
        return True

    error = context.get("validation_error", {})
    if not error:
        return True  # Unknown error, escalate to be safe

    error_scope = error.get("required_scope", "medium")
    threshold = delegated_authority.get("max_approval_scope", "medium")

    scope_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    err_level = scope_order.get(error_scope, 0)
    threshold_level = scope_order.get(threshold, 0)

    return err_level > threshold_level


def check_escalation(item: Any, context: dict) -> Optional[EscalationRecord]:
    """
    Check if an item should be escalated based on authority constraints.

    Evaluates three trigger conditions:
    1. Approval-required transition (human gate detected)
    2. Blocker exceeds delegated resolution authority
    3. Validation failure requires scope/authority decision

    If any condition is met, escalates the item and returns the EscalationRecord.

    Args:
        item: Message or Task that may need escalation
        context: dict with keys:
            - escalated_by: str (participant name)
            - delegated_authority: dict (optional, authority thresholds)
            - blocker: dict (optional, blocker info)
            - validation_failed: bool (optional)
            - validation_error: dict (optional)

    Returns:
        EscalationRecord if escalation was triggered, None otherwise
    """
    # Trigger 1: approval-required
    if _check_approval_required(item):
        item_id = _get_item_id(item)
        reason = context.get("escalation_reason", "approval_required")
        return escalate(item_id, reason, context)

    # Trigger 2: blocker exceeds authority
    if _check_blocker_authority(item, context):
        item_id = _get_item_id(item)
        reason = context.get("escalation_reason", "blocker_exceeds_authority")
        return escalate(item_id, reason, context)

    # Trigger 3: validation failure
    if _check_validation_authority(item, context):
        item_id = _get_item_id(item)
        reason = context.get(
            "escalation_reason",
            context.get("validation_error", {}).get("message", "validation_failure"),
        )
        return escalate(item_id, reason, context)

    return None


def escalate(item_id: str, reason: str, context: dict) -> EscalationRecord:
    """
    Escalate an item to Alex via NATS (gov.escalations).

    1. Create escalation record in ESCALATED state
    2. Publish to NATS gov.escalations subject
    3. Return the escalation record

    Args:
        item_id: ID of the item being escalated
        reason: Human-readable reason for escalation
        context: dict with escalated_by key (participant name)

    Returns:
        EscalationRecord in ESCALATED state
    """
    escalated_by = context.get("escalated_by", "system")
    escalation_id = context.get("escalation_id", None)

    # Import here to avoid circular import
    from . import hold_state as hs

    # If no escalation_id provided, generate one
    if not escalation_id:
        import uuid
        escalation_id = str(uuid.uuid4())

    # Create escalation record
    record = hs.hold_escalation(escalation_id, item_id, reason)
    # Override escalated_by with the actual participant
    record.escalated_by = escalated_by

    # Publish to NATS — escalation events go to gov.escalations
    import json
    payload = json.dumps(record.to_dict()).encode("utf-8")
    try:
        nats_transport.publish(nats_transport.SUBJ_ESCALATIONS, payload)
    except nats_transport.NATSConnectionError:
        # Escalation is still recorded locally; NATS failure doesn't block the record
        pass

    return record


def get_active_escalation(item_id: str) -> Optional[EscalationRecord]:
    """
    Check if an item has an active (ESCALATED) escalation.

    Args:
        item_id: the item ID to check

    Returns:
        EscalationRecord if found and active, None otherwise
    """
    active = list_escalations(status=EscalationState.ESCALATED)
    for rec in active:
        if rec.item_id == item_id:
            return rec
    return None
