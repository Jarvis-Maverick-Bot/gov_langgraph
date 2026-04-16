# governance/workitem/models.py
# WorkItem domain model — per V1.9 Architecture Doc S3.1
#
# WorkItem is a governance tracking object, not an execution object.
# It tracks: stage, artifacts, validations, blockers, delivery package.
# Not to be confused with Task (execution unit) or Message (queue unit).

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Blocker:
    id: str
    item_id: str
    description: str
    signaled_at: str
    resolved: bool = False


@dataclass
class Artifact:
    id: str
    item_id: str
    name: str
    path: str
    submitted_at: str


@dataclass
class Validation:
    id: str
    item_id: str
    result: str  # PASS | FAIL | PENDING
    recorded_at: str


@dataclass
class DeliveryPackage:
    id: str
    item_id: str
    name: str
    stage: str
    artifacts: list[str]
    validations: list[str]
    blockers: list[str]
    created_at: str


@dataclass
class WorkItem:
    id: str
    name: str
    stage: str
    created_at: str
    updated_at: str
    artifacts: list[Artifact] = field(default_factory=list)
    validations: list[Validation] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    transitions: list[dict] = field(default_factory=list)
    delivery_package: Optional[DeliveryPackage] = None

    @classmethod
    def from_dict(cls, data: dict) -> "WorkItem":
        """Deserialize from store dict."""
        artifacts = [Artifact(**a) for a in data.get("artifacts", [])]
        validations = [Validation(**v) for v in data.get("validations", [])]
        blockers = [Blocker(**b) for b in data.get("blockers", [])]
        pkg = None
        if data.get("delivery_package"):
            pkg = DeliveryPackage(**data["delivery_package"])
        return cls(
            id=data["id"],
            name=data["name"],
            stage=data["stage"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            artifacts=artifacts,
            validations=validations,
            blockers=blockers,
            transitions=data.get("transitions", []),
            delivery_package=pkg,
        )

    def to_dict(self) -> dict:
        """Serialize to store dict."""
        return {
            "id": self.id,
            "name": self.name,
            "stage": self.stage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "artifacts": [
                {"id": a.id, "item_id": a.item_id, "name": a.name,
                 "path": a.path, "submitted_at": a.submitted_at}
                for a in self.artifacts
            ],
            "validations": [
                {"id": v.id, "item_id": v.item_id, "result": v.result,
                 "recorded_at": v.recorded_at}
                for v in self.validations
            ],
            "blockers": [
                {"id": b.id, "item_id": b.item_id, "description": b.description,
                 "signaled_at": b.signaled_at, "resolved": b.resolved}
                for b in self.blockers
            ],
            "transitions": self.transitions,
            "delivery_package": self.delivery_package.__dict__ if self.delivery_package else None,
        }
