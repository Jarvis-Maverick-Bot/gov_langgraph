"""
platform_model.handoff_schema — V1 Minimum Handoff Schema

Every stage handoff must include these 10 required fields.
Next stage should never have to guess what it received,
what is complete, what is missing, or what risk remains.

Nova decision (2026-04-06): LOCKED for V1.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class HandoffDocument:
    """
    Minimum required handoff for V1 stage transitions.

    Fields:
        task_id / project_id  — identity
        from_stage / to_stage — stage context
        producer_role          — who produced it
        artifact_references    — what was produced
        handoff_summary        — what was done
        known_limitations     — open issues / risk
        next_expected_action   — what happens next
        timestamp              — when
        status                 — acceptance state
    """

    task_id: str
    project_id: str
    from_stage: str           # BA | SA | DEV | QA
    to_stage: str
    producer_role: str         # viper_ba | viper_sa | viper_dev | viper_qa
    artifact_references: list[str] = field(default_factory=list)
    handoff_summary: str = ""
    known_limitations: str = ""
    next_expected_action: str = ""
    timestamp: str = ""       # ISO 8601
    status: str = "pending_review"  # pending_review | accepted | rejected

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "producer_role": self.producer_role,
            "artifact_references": self.artifact_references,
            "handoff_summary": self.handoff_summary,
            "known_limitations": self.known_limitations,
            "next_expected_action": self.next_expected_action,
            "timestamp": self.timestamp,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> HandoffDocument:
        return cls(
            task_id=d["task_id"],
            project_id=d["project_id"],
            from_stage=d["from_stage"],
            to_stage=d["to_stage"],
            producer_role=d["producer_role"],
            artifact_references=d.get("artifact_references", []),
            handoff_summary=d.get("handoff_summary", ""),
            known_limitations=d.get("known_limitations", ""),
            next_expected_action=d.get("next_expected_action", ""),
            timestamp=d.get("timestamp", ""),
            status=d.get("status", "pending_review"),
        )

    def is_complete(self) -> bool:
        """True if all required fields are non-empty."""
        return bool(
            self.task_id
            and self.project_id
            and self.from_stage
            and self.to_stage
            and self.producer_role
            and self.handoff_summary
            and self.next_expected_action
            and self.timestamp
            and self.status
        )
