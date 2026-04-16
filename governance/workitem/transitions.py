# governance/workitem/transitions.py
# WorkItem stage transitions — per V1.9 Architecture Doc S3.1
#
# WorkItem stages: BACKLOG -> IN_PROGRESS -> IN_REVIEW -> APPROVED -> DELIVERED
# These are managed by the workitem store (governance/workitem/store.py).
# This module provides transition validation and rule definitions.

from enum import Enum


class WorkItemStage(str, Enum):
    """Valid WorkItem stages — per Execution Plan V0.4."""
    BACKLOG = "BACKLOG"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    DELIVERED = "DELIVERED"


# Forward edges only — no backward transitions in normal flow
VALID_TRANSITIONS = {
    WorkItemStage.BACKLOG: [WorkItemStage.IN_PROGRESS],
    WorkItemStage.IN_PROGRESS: [WorkItemStage.IN_REVIEW],
    WorkItemStage.IN_REVIEW: [WorkItemStage.APPROVED, WorkItemStage.IN_PROGRESS],
    WorkItemStage.APPROVED: [WorkItemStage.DELIVERED],
    WorkItemStage.DELIVERED: [],  # terminal
}


def can_transition(from_stage: str, to_stage: str) -> bool:
    """Check if a stage transition is valid."""
    try:
        from_enum = WorkItemStage(from_stage)
        to_enum = WorkItemStage(to_stage)
    except ValueError:
        return False
    return to_enum in VALID_TRANSITIONS.get(from_enum, [])
