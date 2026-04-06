"""
langgraph_engine.nodes.maverick — Maverick coordinator node

PMO coordinator — routes workitems, assigns owners, monitors health.
Does NOT make sovereign governance decisions.

Maverick's role:
- Load workitem state from StateStore
- Check for blockers
- Monitor handoffs
- Route to appropriate stage node
- Emit monitor events
"""

from __future__ import annotations

from gov_langgraph.langgraph_engine.state import GovernanceState
from gov_langgraph.langgraph_engine.nodes.base import NodeCommand


def maverick_node(state: GovernanceState) -> NodeCommand:
    """
    Maverick coordinator node — runs at start of each graph step.

    Responsibilities:
    - Verify workitem is loaded
    - Check for blockers and halt conditions
    - Route to the appropriate stage node

    Routing:
    Maverick checks halt/block conditions first.
    If none, it returns advance and the maverick_router routes to the current stage node.
    The stage node's current_action controls what happens after it executes.

    Returns:
        NodeCommand: block (halt with blocker visibility) or advance (route to stage)
    """
    if state.workitem is None:
        return {
            "current_action": "halt",
            "halt_reason": "maverick: workitem not loaded",
        }

    # Check halt conditions — these stop before even reaching a stage
    if state.halt_reason:
        return {
            "current_action": "halt",
        }

    # Detect blocker — set block action for visibility, halt via maverick_router
    if state.blocked and state.blocker:
        return {
            "current_action": "block",
            "blocked": True,
            "blocker": state.blocker,
        }

    # Route to current stage node
    return {
        "current_action": "advance",
    }
