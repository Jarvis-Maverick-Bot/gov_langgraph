"""
langgraph_engine.nodes.viper_qa — Viper QA stage node

QA stage: performs QA work, signals completion (terminal stage).

QA is the terminal stage — workitem is complete when it reaches QA.
Node explicitly returns "done" (halts at END, not via invalid transition).

Node contract:
- Receives GovernanceState
- Loads workitem from StateStore (if not already in state)
- Executes QA work via AgentExecutor (governance enforcement layers 1-3)
- Marks task as DONE (terminal — no further stage advance)
- Returns command: done (halt at END) or halt (blocked/error)
"""

from __future__ import annotations

from nexus.langgraph_engine.state import GovernanceState
from nexus.langgraph_engine.nodes.base import NodeCommand
from nexus.langgraph_engine.runtime import get_runtime
from nexus.langgraph_engine.agent import make_viper_qa
from nexus.langgraph_engine.executor import AgentExecutor
from nexus.platform_model import TaskStatus


def viper_qa_node(state: GovernanceState) -> NodeCommand:
    """
    QA stage node — executes viper_qa agent with governance enforcement.

    QA is terminal: does NOT call StateMachine.advance_stage().
    Instead, marks task as DONE and returns "done" to halt at END.
    """
    rt = get_runtime()

    workitem = state.workitem
    if workitem is None:
        return {
            "current_action": "halt",
            "halt_reason": "QA: workitem not in state",
        }

    # Use AgentExecutor for governance enforcement
    agent = make_viper_qa()
    executor = AgentExecutor(agent)

    try:
        # Execute with all 3 enforcement layers:
        #   Layer 1: pre_execution_check — is viper_qa allowed in QA?
        #   Layer 2: enforce_action — is "create_artifact" allowed for viper_qa?
        #   Layer 3: review_completion — does handoff satisfy governance?
        # executor.execute_with_enforcement() saves handoff to evidence store internally
        # handoff return value is intentionally unused here — node only needs done/halt
        _ = executor.execute_with_enforcement(
            task_id=workitem.task_id,
            project_id=state.project_id,
            stage="QA",
            action="create_artifact",
            initiator=state.actor or "system",
        )

        # QA is terminal — mark task as DONE, don't advance further
        ts = rt.store.load_taskstate(workitem.task_id)
        ts.current_stage = "QA"
        ts.state_status = TaskStatus.DONE
        rt.store.save_taskstate(ts)

        # Persist workitem as complete
        workitem.current_stage = "QA"
        rt.store.save_workitem(workitem)

        return {"current_action": "done"}

    except PermissionError as e:
        return {
            "current_action": "halt",
            "halt_reason": f"QA authority denied: {e}",
        }
    except ValueError as e:
        return {
            "current_action": "halt",
            "halt_reason": f"QA governance failure: {e}",
        }
    except Exception as e:
        return {
            "current_action": "halt",
            "halt_reason": f"QA: {e}",
        }
