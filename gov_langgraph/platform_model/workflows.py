"""
platform_model.workflows — V1 Approved Default Workflow

Single source of truth for the V1 pipeline workflow definition.
All integration and PMO layers must import from here — no scattered literals.

V1 Pipeline: BA -> SA -> DEV -> QA
"""

from __future__ import annotations

from .objects import Workflow


# ---------------------------------------------------------------------------
# V1 Pipeline — DO NOT MODIFY WITHOUT GOVERNANCE APPROVAL
# ---------------------------------------------------------------------------

V1_PIPELINE_STAGES = ["BA", "SA", "DEV", "QA"]

V1_PIPELINE_TRANSITIONS = {
    "BA": ["SA"],
    "SA": ["DEV"],
    "DEV": ["QA"],
    "QA": [],
}


def get_v1_pipeline_workflow() -> Workflow:
    """
    Return the V1 Pipeline workflow instance.
    This is the governance-approved default for V1.
    """
    return Workflow(
        workflow_name="V1 Pipeline",
        domain_type="internal",
        stage_list=V1_PIPELINE_STAGES,
        allowed_transitions=V1_PIPELINE_TRANSITIONS,
    )
