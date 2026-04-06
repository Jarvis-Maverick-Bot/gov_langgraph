"""
langgraph_engine.nodes.viper_dev — Viper DEV stage node

DEV stage: performs DEV work, signals QA-ready.

Node contract:
- Receives GovernanceState
- Loads workitem from StateStore (if not already in state)
- Executes DEV work via AgentExecutor (governance enforcement layers 1-3)
- Handoff to QA via StateMachine
- Returns command: advance (done) or halt (blocked/error)
"""

from __future__ import annotations

from gov_langgraph.langgraph_engine.state import GovernanceState
from gov_langgraph.langgraph_engine.nodes.base import NodeCommand
from gov_langgraph.langgraph_engine.runtime import get_runtime
from gov_langgraph.langgraph_engine.agent import make_viper_dev
from gov_langgraph.langgraph_engine.executor import AgentExecutor
from gov_langgraph.platform_model import get_v1_pipeline_workflow, TaskStatus
from gov_langgraph.platform_model.state_machine import StateMachine


def viper_dev_node(state: GovernanceState) -> NodeCommand:
    """
    DEV stage node — executes viper_dev agent with governance enforcement,
    then advances workitem from DEV to QA.
    """
    rt = get_runtime()

    workitem = state.workitem
    if workitem is None:
        return {
            "current_action": "halt",
            "halt_reason": "DEV: workitem not in state",
        }

    # Use AgentExecutor for governance enforcement
    agent = make_viper_dev()
    executor = AgentExecutor(agent)

    try:
        # Execute with all 3 enforcement layers:
        #   Layer 1: pre_execution_check — is viper_dev allowed in DEV?
        #   Layer 2: enforce_action — is "create_artifact" allowed for viper_dev?
        #   Layer 3: review_completion — does handoff satisfy governance?
        handoff = executor.execute_with_enforcement(
            task_id=workitem.task_id,
            project_id=state.project_id,
            stage="DEV",
            action="create_artifact",
            initiator=state.actor or "system",
        )

        # Advance workitem from DEV to QA via StateMachine
        sm = StateMachine(
            workflow=get_v1_pipeline_workflow(),
            checkpointer=rt.checkpointer,
            event_journal=rt.event_journal,
        )
        sm.advance_stage(
            work_item=workitem,
            target_stage="QA",
            actor_role="viper_dev",
            project_id=state.project_id,
        )

        rt.store.save_workitem(workitem)

        ts = rt.store.load_taskstate(workitem.task_id)
        ts.current_stage = "QA"
        ts.state_status = TaskStatus.IN_PROGRESS
        rt.store.save_taskstate(ts)

        return {"current_action": "advance"}

    except PermissionError as e:
        return {
            "current_action": "halt",
            "halt_reason": f"DEV authority denied: {e}",
        }
    except ValueError as e:
        return {
            "current_action": "halt",
            "halt_reason": f"DEV governance failure: {e}",
        }
    except Exception as e:
        return {
            "current_action": "halt",
            "halt_reason": f"DEV: {e}",
        }
