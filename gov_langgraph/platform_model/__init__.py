"""
platform_model — Platform Core

Source of truth for V1 governance model.
Exports only public interfaces; internal helpers stay in their modules.

Day 1 exports: Project, WorkItem, TaskState + enums
Full exports (after Day 2): Workflow, Handoff, Gate, Event + all remaining
"""

from platform_model.objects import (
    HandoffStatus,
    ProjectStatus,
    Role,
    TaskStatus,
)

# Objects — Day 1
from platform_model.objects import Project
from platform_model.objects import WorkItem
from platform_model.objects import TaskState

__all__ = [
    # Objects (Day 1)
    "Project",
    "WorkItem",
    "TaskState",
    # Enums
    "ProjectStatus",
    "TaskStatus",
    "HandoffStatus",
    "Role",
]
