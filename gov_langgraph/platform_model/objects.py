"""
platform_model.objects — Step 2 Frozen Objects

V1 minimum governed object model.
All 7 first-class objects defined in Step 2.

Objects defined here are the source of truth.
LangGraph, Harness, and PMO surface all reference these — not replace them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CLOSED = "closed"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class GateDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    HELD = "held"
    STOPPED = "stopped"
    RETURNED = "returned"


# ---------------------------------------------------------------------------
# Role Enum — V1 Authority Model
# ---------------------------------------------------------------------------


class Role(str, Enum):
    """
    V1 role enum — authority/system identity only.

    Roles are governance labels for permission enforcement.
    Full agent definitions (Soul, Memory, Scope) are defined
    separately when agents are actually embodied.

    Resolved: ALEX, NOVA, JARVIS, MAVERICK, VIPER_BA, VIPER_SA,
    VIPER_DEV, VIPER_QA
    """

    ALEX = "alex"
    NOVA = "nova"
    JARVIS = "jarvis"
    MAVERICK = "maverick"
    VIPER_BA = "viper_ba"
    VIPER_SA = "viper_sa"
    VIPER_DEV = "viper_dev"
    VIPER_QA = "viper_qa"


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


@dataclass
class Project:
    """
    Top-level governed delivery container.
    Anchors workflow context, status visibility, and PMO tracking.

    Step 2 fields: project_id, project_name, project_goal, domain_type,
    workflow_template_id, project_status, created_at, project_summary,
    project_owner
    """

    project_name: str
    project_goal: str
    domain_type: str
    project_owner: str
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_template_id: Optional[str] = None
    project_status: ProjectStatus = ProjectStatus.ACTIVE
    project_summary: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Optional fields
    closed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.project_name:
            raise ValueError("project_name is required")
        if not self.project_goal:
            raise ValueError("project_goal is required")

    def close(self) -> None:
        self.project_status = ProjectStatus.CLOSED
        self.closed_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# TaskState — separate from WorkItem per Step 2
# ---------------------------------------------------------------------------


@dataclass
class TaskState:
    """
    Current actionable operational condition of a WorkItem.
    Separate from the task definition itself (Step 2 requirement).

    Step 2 fields: task_id, current_stage, state_status, current_owner,
    current_blocker, next_expected_action, last_updated_at
    """

    task_id: str
    current_stage: str  # BA | SA | DEV | QA (Step 2 resolved stages)
    state_status: TaskStatus = TaskStatus.BACKLOG
    current_owner: Optional[str] = None
    current_blocker: Optional[str] = None
    next_expected_action: Optional[str] = None
    last_updated_at: datetime = field(default_factory=datetime.utcnow)

    def advance_stage(self, next_stage: str) -> None:
        """Advance to next stage. Does NOT validate — caller must validate first."""
        self.current_stage = next_stage
        self.last_updated_at = datetime.utcnow()

    def block(self, reason: str) -> None:
        self.current_blocker = reason
        self.state_status = TaskStatus.BLOCKED
        self.last_updated_at = datetime.utcnow()

    def unblock(self) -> None:
        self.current_blocker = None
        if self.state_status == TaskStatus.BLOCKED:
            self.state_status = TaskStatus.IN_PROGRESS
        self.last_updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# WorkItem
# ---------------------------------------------------------------------------


@dataclass
class WorkItem:
    """
    Minimum governed delivery unit.
    Step 2 keeps Task/WorkItem as one merged object.

    Step 2 fields: task_id, project_id, task_title, task_description,
    current_owner, dependency_task_ids, expected_deliverable, workflow_id,
    current_stage, task_status, handoff_target, priority
    """

    task_title: str
    project_id: str
    task_description: str = ""
    workflow_id: Optional[str] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_owner: Optional[str] = None
    dependency_task_ids: list[str] = field(default_factory=list)
    expected_deliverable: Optional[str] = None
    current_stage: str = "BA"  # Default start stage
    task_status: TaskStatus = TaskStatus.BACKLOG
    handoff_target: Optional[str] = None
    priority: int = 0  # Higher = more urgent
    created_at: datetime = field(default_factory=datetime.utcnow)

    # V1 does NOT include: task_workflow_status, task_completion_percentage,
    # actual_hours, estimated_hours — these are deferred

    def __post_init__(self):
        if not self.task_title:
            raise ValueError("task_title is required")
        if not self.project_id:
            raise ValueError("project_id is required")

    def assign(self, owner: str) -> None:
        self.current_owner = owner

    def complete(self) -> None:
        self.task_status = TaskStatus.DONE
