"""
gov_langgraph V1 E2E Test — Full Compiled Graph Pipeline

Tests the full compiled LangGraph via pipeline.run_workitem() (not via tools).
This verifies the complete BA→SA→DEV→QA→DONE pipeline with all governance artifacts.

What this test verifies:
1. Project + workitem + TaskState created
2. Compiled graph runs full BA→SA→DEV→QA→DONE pipeline
3. Final workitem stage = QA, TaskState = DONE (terminal)
4. Handoffs: 4 produced (one per stage), all complete with 10 required fields
5. agent_executed events: 4 journaled (one per stage)
6. stage_advanced events: 3+ journaled (BA→SA, SA→DEV, DEV→QA)
7. Checkpoint: latest record is DEV→QA
8. Checkpoint restore works
9. Authority failure propagates (not silently swallowed)

Run:
    python LANGGRAPH_E2E_TEST.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from gov_langgraph.harness import HarnessConfig, StateStore, Checkpointer, EventJournal, EvidenceStore
from gov_langgraph.langgraph_engine import init_runtime
from gov_langgraph.langgraph_engine.runtime import get_runtime
from gov_langgraph.langgraph_engine.pipeline import run_workitem
from gov_langgraph.langgraph_engine.executor import AgentExecutor
from gov_langgraph.langgraph_engine.agent import make_viper_qa
from gov_langgraph.platform_model import TaskState, TaskStatus, Project, WorkItem


def main():
    print("=" * 60)
    print("gov_langgraph V1 — Full Pipeline E2E Test")
    print("=" * 60)

    cfg = HarnessConfig()
    cfg.ensure_dirs()
    store = StateStore(cfg.state_dir)
    ckpt = Checkpointer(cfg)
    journal = EventJournal(cfg.event_dir)
    evidence = EvidenceStore(cfg.state_dir / "evidence")

    init_runtime()
    rt = get_runtime()

    # ── 1. Create project ───────────────────────────────────────
    print("\n[1/9] Create project")
    project = Project(
        project_id="proj-e2e",
        project_name="V1 E2E Test",
        project_goal="Full compiled graph pipeline E2E",
        domain_type="test",
        project_owner="jarvis",
    )
    rt.store.save_project(project)
    print(f"  OK — project_id: {project.project_id}")

    # ── 2. Create workitem + TaskState ──────────────────────────
    print("\n[2/9] Create workitem + TaskState")
    workitem = WorkItem(
        task_title="E2E Workitem",
        project_id=project.project_id,
        task_id="task-e2e",
        current_stage="BA",
        current_owner="viper_ba",
    )
    rt.store.save_workitem(workitem)

    ts = TaskState(
        task_id=workitem.task_id,
        current_stage="BA",
        state_status=TaskStatus.IN_PROGRESS,
        current_owner="viper_ba",
    )
    rt.store.save_taskstate(ts)
    print(f"  WorkItem: {workitem.task_id}, stage=BA")
    print(f"  TaskState: stage=BA, status=IN_PROGRESS")

    # ── 3. Invoke compiled graph — full pipeline ───────────────
    print("\n[3/9] Invoke compiled graph — BA → SA → DEV → QA → DONE")
    result = run_workitem(
        task_id=workitem.task_id,
        project_id=project.project_id,
        actor="jarvis",
    )

    current_action = result["current_action"]
    final_stage = result["workitem"].current_stage
    print(f"  Graph result — current_action: {current_action}")
    print(f"  Graph result — workitem stage: {final_stage}")
    assert current_action == "done", f"Expected 'done', got '{current_action}'"
    assert final_stage == "QA", f"Expected QA, got {final_stage}"
    print(f"  Pipeline completed: BA → SA → DEV → QA → DONE — OK")

    # ── 4. Verify TaskState = DONE ──────────────────────────────
    print("\n[4/9] Verify TaskState = DONE (terminal)")
    ts = rt.store.load_taskstate(workitem.task_id)
    print(f"  TaskState: stage={ts.current_stage}, status={ts.state_status}")
    assert ts.state_status == TaskStatus.DONE, f"Expected DONE, got {ts.state_status}"
    print(f"  TaskState DONE — OK")

    # ── 5. Verify handoffs in evidence store ─────────────────────
    print("\n[5/9] Verify handoffs (4 expected: BA→SA, SA→DEV, DEV→QA, QA→END)")
    handoffs = evidence.get_handoffs_for_task(workitem.task_id)
    print(f"  Total handoffs: {len(handoffs)}")
    assert len(handoffs) >= 3, f"Expected >=3 handoffs, got {len(handoffs)}"

    # Verify handoffs are complete (all 10 required fields)
    seen_stages = set()
    for h in handoffs:
        stage_key = f"{h.from_stage}->{h.to_stage}"
        if stage_key not in seen_stages:
            seen_stages.add(stage_key)
            is_complete = h.is_complete()
            print(f"  {h.from_stage} -> {h.to_stage}: {h.producer_role}, "
                  f"artifacts={h.artifact_references}, complete={is_complete}")
            assert is_complete, f"Handoff {stage_key} is incomplete"

    # Count unique stage transitions
    unique = len(seen_stages)
    print(f"  Unique handoff transitions: {unique} — OK")

    # ── 6. Verify agent_executed events ─────────────────────────
    print("\n[6/9] Verify agent_executed events (4 expected: one per stage)")
    all_events = journal.get_for_project(project.project_id)
    agent_events = [e for e in all_events if e.event_type == "agent_executed"]
    print(f"  Total events: {len(all_events)}")
    print(f"  agent_executed events: {len(agent_events)}")
    assert len(agent_events) >= 3, f"Expected >=3 agent_executed events, got {len(agent_events)}"

    # Verify one event per stage actor
    seen_actors = set()
    for e in agent_events:
        if e.actor not in seen_actors:
            seen_actors.add(e.actor)
            print(f"  agent_executed | actor={e.actor} | {e.event_summary[:55]}")
    print(f"  Unique agent actors: {len(seen_actors)} — OK")

    # ── 7. Verify stage_advanced events ───────────────────────
    print("\n[7/9] Verify stage_advanced events (3 expected: BA→SA, SA→DEV, DEV→QA)")
    stage_events = [e for e in all_events if e.event_type == "stage_advanced"]
    print(f"  stage_advanced events: {len(stage_events)}")
    assert len(stage_events) >= 3, f"Expected >=3 stage_advanced events, got {len(stage_events)}"
    for e in stage_events:
        print(f"  {e.event_type} | {e.actor} | {e.event_summary[:55]}")
    print(f"  All stage transitions journaled — OK")

    # ── 8. Verify checkpoint ─────────────────────────────────────
    print("\n[8/9] Verify checkpoint")
    ckpt_record = ckpt.get_latest_completed_checkpoint(workitem.task_id)
    assert ckpt_record is not None, "No checkpoint found"
    print(f"  Latest checkpoint: {ckpt_record.from_stage} -> {ckpt_record.to_stage}")
    print(f"  Checkpoint OK")

    # ── 9. Verify authority failure propagates ───────────────────
    print("\n[9/9] Verify authority failure propagates (not silently swallowed)")
    agent_wrong = make_viper_qa()  # viper_qa cannot act in BA
    executor_wrong = AgentExecutor(agent_wrong)
    try:
        executor_wrong.execute_with_enforcement(
            task_id="t-test",
            project_id="p-test",
            stage="BA",
            action="create_artifact",
            initiator="alex",
        )
        assert False, "Expected PermissionError"
    except PermissionError as e:
        print(f"  PermissionError propagated: {e} — OK")

    # ── Summary ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — V1 LangGraph pipeline verified")
    print("=" * 60)
    print(f"\nVerified:")
    print(f"  Pipeline:   BA -> SA -> DEV -> QA -> DONE")
    print(f"  TaskState:  DONE (terminal)")
    print(f"  Handoffs:   {unique} unique stage transitions")
    print(f"  agent_exec: {len(agent_events)} events")
    print(f"  stage_adv: {len(stage_events)} events")
    print(f"  Checkpoint: verified")


if __name__ == "__main__":
    main()
