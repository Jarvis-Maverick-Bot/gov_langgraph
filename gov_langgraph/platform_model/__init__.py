"""
platform_model — Platform Core

Source of truth for V1 governance model.
Exports only public interfaces; internal helpers stay in their modules.
"""

from .authority import (
    Action,
    AuthorizationRecord,
    AuthorityViolation,
    Tier,
    check_authority,
)

from .objects import (
    Event,
    Gate,
    GateDecision,
    Handoff,
    HandoffStatus,
    Project,
    ProjectStatus,
    Role,
    TaskState,
    TaskStatus,
    WorkItem,
    Workflow,
)

__all__ = [
    # Objects
    "Project",
    "WorkItem",
    "TaskState",
    "Workflow",
    "Handoff",
    "Gate",
    "Event",
    # Enums
    "ProjectStatus",
    "TaskStatus",
    "HandoffStatus",
    "GateDecision",
    "Role",
    # Authority
    "Tier",
    "Action",
    "check_authority",
    "AuthorityViolation",
    "AuthorizationRecord",
]
