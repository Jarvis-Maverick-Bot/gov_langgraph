"""
langgraph_engine.edges — Edge Routing Definitions

Formal definition of V1 pipeline edge routing.
All routing is deterministic, based on GovernanceState fields only.

═══════════════════════════════════════════════════════════════════
V1 PIPELINE EDGE MAP
═══════════════════════════════════════════════════════════════════

START
  └─> __maverick__

__maverick__  (conditional on GovernanceState)
  ├─ halt_reason or current_action="halt"  ──────────────────> __END__
  ├─ current_action="block"               ──────────────────> __END__
  ├─ current_action="done"                ──────────────────> __END__
  ├─ current_action="gate_rejected"      ──────────────────> __END__
  ├─ current_action="handoff"            ──────────────────> __END__
  ├─ workitem is None                    ──────────────────> __END__
  └─ otherwise (route to current_stage) ──────────────────> __stage_{stage}__

__stage_BA__  (conditional on current_action)
  ├─ "advance" ────────────────────────────> __stage_SA__
  ├─ "halt"   ────────────────────────────> __END__
  ├─ "done"   ────────────────────────────> __END__
  ├─ "block"  ────────────────────────────> __END__
  ├─ "gate_approved" ────────────────────> __stage_SA__
  ├─ "gate_rejected" ────────────────────> __END__
  ├─ "handoff" ───────────────────────────> __END__
  └─ (unknown) ───────────────────────────> __END__

__stage_SA__  (conditional on current_action)
  ├─ "advance" ────────────────────────────> __stage_DEV__
  ├─ "halt"   ────────────────────────────> __END__
  ├─ "done"   ────────────────────────────> __END__
  ├─ "block"  ────────────────────────────> __END__
  ├─ "gate_approved" ────────────────────> __stage_DEV__
  ├─ "gate_rejected" ────────────────────> __END__
  ├─ "handoff" ───────────────────────────> __END__
  └─ (unknown) ───────────────────────────> __END__

__stage_DEV__  (conditional on current_action)
  ├─ "advance" ────────────────────────────> __stage_QA__
  ├─ "halt"   ────────────────────────────> __END__
  ├─ "done"   ────────────────────────────> __END__
  ├─ "block"  ────────────────────────────> __END__
  ├─ "gate_approved" ────────────────────> __stage_QA__
  ├─ "gate_rejected" ────────────────────> __END__
  ├─ "handoff" ───────────────────────────> __END__
  └─ (unknown) ───────────────────────────> __END__

__stage_QA__  (conditional on current_action)
  ├─ "advance" ────────────────────────────> __END__  (terminal)
  ├─ "halt"   ────────────────────────────> __END__
  ├─ "done"   ────────────────────────────> __END__  (normal completion)
  ├─ "block"  ────────────────────────────> __END__
  ├─ "gate_approved" ────────────────────> __END__  (no next stage)
  ├─ "gate_rejected" ────────────────────> __END__
  ├─ "handoff" ────────────────────────────> __END__
  └─ (unknown) ───────────────────────────> __END__

═══════════════════════════════════════════════════════════════════
GOVERNANCE RULES
═══════════════════════════════════════════════════════════════════

1. NO auto-return on gate_rejected
   → gate_rejected always halts. Await intervention.

2. Blockers are workflow-visible
   → GovernanceState.blocked=True, GovernanceState.blocker=<reason>
   → maverick detects blocker and sets current_action="block"

3. Handoff is explicit halt
   → current_action="handoff" halts at END
   → Await outside acceptance before re-running graph

4. Unknown action always halts
   → Safety default: unknown action -> END

5. Stage sequence: BA -> SA -> DEV -> QA -> END
   → Defined in platform_model.V1_PIPELINE_STAGES (single source)
"""

from __future__ import annotations

# Re-export router functions for documentation
from gov_langgraph.langgraph_engine.graph import _maverick_router, _stage_router

__all__ = ["_maverick_router", "_stage_router"]
