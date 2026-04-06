"""
langgraph_engine.nodes.viper_sa — Viper SA stage node

SA stage: performs SA work, signals DEV-ready.

Node contract:
- Receives GovernanceState
- Loads workitem from StateStore (if not already in state)
- Executes SA work via AgentExecutor (governance enforcement layers 1-3)
- Handoff to DEV via StateMachine
- Returns command: advance (done) or halt (blocked/error)
"""

from __future__ import annotations

from gov_langgraph.langgraph_engine.state import GovernanceState
from gov_langgraph.langgraph_engine.nodes.base import NodeCommand
from gov_langgraph.langgraph_engine.runtime import get_runtime
from gov_langgraph.langgraph_engine.agent import make_viper_sa
from gov_langgraph.langgraph_engine.executor import AgentExecutor
from gov_langgraph.platform_model import get_v1_pipeline_workflow, TaskStatus
from gov_langgraph.platform_model.state_machine import StateMachine


def viper_sa_node(state: GovernanceState) -> NodeCommand:
    """
    SA stage node — executes SA work with governance enforcement,
    then advances workitem from SA to DEV.
    """
    rt = get_runtime()

    workitem = state.workitem
    if workitem is None:
        return {
            "current_action": "halt",
            "halt_reason": "SA: workitem not in state",
        }

    # Use AgentExecutor for governance enforcement
    agent = make_viper_sa()
    executor = AgentExecutor(agent)

    try:
        # Execute with all 3 enforcement layers
        # SA action: create_artifact (produces SPEC)
        handoff = executor.execute_with_enforcement(
            task_id=workitem.task_id,
            project_id=state.project_id,
            stage="SA",
            action="create_artifact",
            initiator=state.actor or "system",
        )

        # Advance workitem from SA to DEV via StateMachine
        sm = StateMachine(
            workflow=get_v1_pipeline_workflow(),
            checkpointer=rt.checkpointer,
            event_journal=rt.event_journal,
        )
        sm.advance_stage(
            work_item=workitem,
            target_stage="DEV",
            actor_role="viper_sa",
            project_id=state.project_id,
        )

        rt.store.save_workitem(workitem)

        ts = rt.store.load_taskstate(workitem.task_id)
        ts.current_stage = "DEV"
        ts.state_status = TaskStatus.IN_PROGRESS
        rt.store.save_taskstate(ts)

        return {"current_action": "advance"}

    except PermissionError:
        return {
            "current_action": "halt",
            "halt_reason": f"SA authority denied: {executor.halt_reason()}",
        }
    except ValueError as e:
        return {
            "current_action": "halt",
            "halt_reason": f"SA completion denied: {e}",
        }
    except Exception as e:
        return {
            "current_action": "halt",
            "halt_reason": f"SA: {e}",
        }
