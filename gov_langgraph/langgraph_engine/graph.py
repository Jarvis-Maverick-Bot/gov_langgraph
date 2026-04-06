"""
langgraph_engine.graph — LangGraph StateGraph

V1 Pipeline graph: START -> maverick -> stage nodes -> END

Edge routing (explicit, governed):
  maverick routes to current stage based on workitem.current_stage

  After stage node executes, _stage_router maps current_action:
    - "advance"  -> next stage (BA->SA->DEV->QA)
    - "block"    -> END (blocked, workflow-visible, awaiting escalation)
    - "halt"     -> END (halt, checkpoint saved)
    - "done"     -> END (normal completion at QA)
    - "gate_approved" -> advance to next stage
    - "gate_rejected"  -> END (halt, await intervention)
    - "handoff"  -> END (awaiting acceptance)
    - (unknown)   -> END (halt for safety)

GovernanceState carries blocker/halt_reason for visibility.
No automatic re-routing on rejection — halt is explicit.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from gov_langgraph.langgraph_engine.state import GovernanceState
from gov_langgraph.platform_model import V1_PIPELINE_STAGES


# Valid stage sequence — imported from central V1 workflow source
STAGE_SEQUENCE = V1_PIPELINE_STAGES


# ─────────────────────────────────────────────────────────────────
# _make_stage_stub() removed — stage nodes are now in nodes/viper_*.py
# ─────────────────────────────────────────────────────────────────


def _next_stage(current: str) -> str | type[END]:
    """Return the next stage after current, or END if at terminal."""
    idx = STAGE_SEQUENCE.index(current)
    if idx + 1 < len(STAGE_SEQUENCE):
        return f"__stage_{STAGE_SEQUENCE[idx + 1]}__"
    return END


def build_graph() -> StateGraph:
    """
    Build the V1 pipeline StateGraph.

    Uses real stage nodes (viper_ba, viper_sa, viper_dev, viper_qa)
    wired to StateMachine + Harness.
    """
    graph = StateGraph(state_schema=GovernanceState)

    # Import nodes
    from gov_langgraph.langgraph_engine.nodes.maverick import maverick_node
    from gov_langgraph.langgraph_engine.nodes.viper_ba import viper_ba_node
    from gov_langgraph.langgraph_engine.nodes.viper_sa import viper_sa_node
    from gov_langgraph.langgraph_engine.nodes.viper_dev import viper_dev_node
    from gov_langgraph.langgraph_engine.nodes.viper_qa import viper_qa_node

    # Stage nodes mapped to graph node names
    stage_nodes = {
        "BA": viper_ba_node,
        "SA": viper_sa_node,
        "DEV": viper_dev_node,
        "QA": viper_qa_node,
    }

    # Register stage nodes
    for stage, node_fn in stage_nodes.items():
        graph.add_node(f"__stage_{stage}__", node_fn)

    # Entry point: maverick
    graph.add_node("__maverick__", maverick_node)
    graph.add_edge(START, "__maverick__")

    # Maverick routes to the current stage node
    graph.add_conditional_edges(
        "__maverick__",
        _maverick_router,
        {
            "__stage_BA__": "__stage_BA__",
            "__stage_SA__": "__stage_SA__",
            "__stage_DEV__": "__stage_DEV__",
            "__stage_QA__": "__stage_QA__",
            "__end__": END,  # END returned directly when halting
        },
    )

    # Each stage node routes based on its action
    for stage in STAGE_SEQUENCE:
        node_name = f"__stage_{stage}__"
        next_node = _next_stage(stage)
        edge_map = {
            "__advance__": next_node,       # advance -> next stage
            "__done__": END,                 # done -> END
            "__halt__": END,                # halt -> END
            "__block__": END,               # block -> END
            "__gate_rejected__": END,       # gate_rejected -> END (halt)
            "__handoff__": END,             # handoff -> END (await acceptance)
        }
        graph.add_conditional_edges(node_name, _stage_router, edge_map)

    return graph


def _maverick_router(state: GovernanceState) -> str:
    """
    Maverick routes to the current stage.

    Routing rules (checked in order):
    - halt_reason present -> END (already halted, no routing needed)
    - current_action=halt -> END
    - current_action=block -> END (blocked, awaiting escalation)
    - workitem missing -> END
    - otherwise -> current stage node

    Note: done/gate_rejected/handoff are NOT checked here.
    Those are handled by stage_router after the stage node executes.
    """
    if state.halt_reason:
        return END
    if state.current_action == "halt":
        return END
    if state.current_action == "block":
        return END
    if state.workitem is None:
        return END
    return f"__stage_{state.workitem.current_stage}__"


def _stage_router(state: GovernanceState) -> str:
    """
    Stage node routes based on the action set by the node.

    Routing:
    - advance / gate_approved -> next stage
    - done -> END (normal completion)
    - halt -> END (error halt)
    - block -> END (blocked, awaiting escalation)
    - gate_rejected -> END (await intervention)
    - handoff -> END (await acceptance)
    - unknown -> END (safety)
    """
    action = state.current_action
    if action == "advance":
        return "__advance__"
    elif action == "done":
        return "__done__"
    elif action == "halt":
        return "__halt__"
    elif action == "block":
        return "__block__"
    elif action == "gate_approved":
        return "__advance__"
    elif action == "gate_rejected":
        return "__gate_rejected__"
    elif action == "handoff":
        return "__handoff__"
    else:
        return "__halt__"
