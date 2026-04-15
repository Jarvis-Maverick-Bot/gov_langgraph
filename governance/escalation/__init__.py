"""
governance/escalation/__init__.py
V1.9 Sprint 2, Task T7.1-T7.4
Escalation + Authority Return — distinct governed layer.

Escalation doctrine is a distinct governed layer, not collapsed into queue semantics.
Observable state, governed decisions, explicit hold.
"""

from .triggers import check_escalation, escalate
from .hold_state import (
    EscalationState,
    EscalationRecord,
    hold_escalation,
    get_escalation,
    list_escalations,
)
from .decision_record import (
    DecisionValue,
    DecisionRecord,
    record_decision,
    get_decision,
)
from .return_to_flow import return_to_flow, ReturnRecord

__all__ = [
    "check_escalation",
    "escalate",
    "EscalationState",
    "EscalationRecord",
    "hold_escalation",
    "get_escalation",
    "list_escalations",
    "DecisionValue",
    "DecisionRecord",
    "record_decision",
    "get_decision",
    "return_to_flow",
    "ReturnRecord",
]
