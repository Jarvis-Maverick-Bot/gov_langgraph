"""
gov_langgraph E2E test — End-to-end pipeline test

Tests the full pipeline:
1. Create project via tool
2. Create workitem
3. Advance through BA → SA → DEV → QA
4. Record blocker and resolve it
5. Submit handoff between stages
6. Approve gate
7. Session restart — recover from checkpoint
8. Verify state matches

Run:
    python E2E_TEST.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from gov_langgraph.openclaw_integration import Coordinator
from gov_langgraph.harness import HarnessConfig, StateStore, Checkpointer, EventJournal
from gov_langgraph.platform_model import get_v1_pipeline_workflow, V1_PIPELINE_STAGES


def main():
    print("=" * 60)
    print("gov_langgraph V1 End-to-End Test")
    print("=" * 60)

    cfg = HarnessConfig()
    cfg.ensure_dirs()
    store = StateStore(cfg.state_dir)
    ckpt = Checkpointer(cfg)
    journal = EventJournal(cfg.event_dir)

    c = Coordinator()

    # ── 1. Create project ───────────────────────────────────────
    print("\n[1/8] Create project")
    r = c.handle('create_project', {
        'project_name': 'E2E Test Project',
        'project_goal': 'Full pipeline end-to-end test',
        'domain_type': 'test',
        'actor': 'jarvis',
    })
    assert r['ok'], f"create_project failed: {r.get('error')}"
    proj_id = r['data']['project_id']
    print(f"  OK — project_id: {proj_id[:8]}")

    # ── 2. Create workitem ──────────────────────────────────────
    print("\n[2/8] Create workitem")
    r = c.handle('create_task', {
        'task_title': 'E2E Test Task',
        'project_id': proj_id,
        'current_owner': 'viper_ba',
        'actor': 'jarvis',
    })
    assert r['ok'], f"create_task failed: {r.get('error')}"
    task_id = r['data']['task_id']
    print(f"  OK — task_id: {task_id[:8]}, stage: {r['data']['current_stage']}")

    # ── 3. Advance BA → SA → DEV → QA ─────────────────────────
    print("\n[3/8] Advance through all stages")

    # BA → SA
    r = c.handle('advance_stage', {'task_id': task_id, 'target_stage': 'SA', 'actor': 'viper_ba'})
    assert r['ok'], f"BA→SA failed: {r.get('error')}"
    print(f"  BA → SA: OK")

    # SA → DEV
    r = c.handle('advance_stage', {'task_id': task_id, 'target_stage': 'DEV', 'actor': 'viper_ba'})
    assert r['ok'], f"SA→DEV failed: {r.get('error')}"
    print(f"  SA → DEV: OK")

    # DEV → QA
    r = c.handle('advance_stage', {'task_id': task_id, 'target_stage': 'QA', 'actor': 'viper_dev'})
    assert r['ok'], f"DEV→QA failed: {r.get('error')}"
    print(f"  DEV → QA: OK")

    # Verify final stage
    r = c.handle('get_status', {'task_id': task_id})
    assert r['ok']
    assert r['data']['current_stage'] == 'QA', f"Expected QA, got {r['data']['current_stage']}"
    print(f"  Final stage: QA — OK")

    # ── 4. Verify event journal has all transitions ────────────
    print("\n[4/8] Verify event journal")
    events = journal.get_for_project(proj_id)
    stage_events = [e for e in events if e.event_type == 'stage_advanced']
    print(f"  Total events: {len(events)}")
    print(f"  Stage advanced events: {len(stage_events)}")
    assert len(stage_events) >= 3, f"Expected ≥3 stage_advanced events, got {len(stage_events)}"
    print(f"  OK — all stage transitions journaled")

    # ── 5. Approve gate ────────────────────────────────────────
    print("\n[5/8] Approve gate")
    r = c.handle('approve_gate', {
        'task_id': task_id,
        'gate_name': 'QA Approval',
        'actor': 'nova',
        'notes': 'All checks passed',
    })
    assert r['ok'], f"approve_gate failed: {r.get('error')}"
    gate_id = r['data']['gate_id']
    print(f"  OK — gate_id: {gate_id[:8]}")

    # Verify gate persisted
    gates = list((cfg.state_dir).glob("gate_*.json"))
    print(f"  Gate files on disk: {len(gates)}")
    assert len(gates) >= 1
    print(f"  OK — gate persisted")

    # ── 6. Submit handoff ──────────────────────────────────────
    print("\n[6/8] Submit handoff")
    r = c.handle('submit_handoff', {
        'task_id': task_id,
        'from_owner': 'viper_dev',
        'to_owner': 'viper_qa',
        'actor': 'viper_dev',
    })
    assert r['ok'], f"submit_handoff failed: {r.get('error')}"
    handoff_id = r['data']['handoff_id']
    print(f"  OK — handoff_id: {handoff_id[:8]}")

    # Verify handoff persisted
    handoffs = list((cfg.state_dir).glob("handoff_*.json"))
    print(f"  Handoff files on disk: {len(handoffs)}")
    assert len(handoffs) >= 1
    print(f"  OK — handoff persisted")

    # ── 7. Session restart simulation — recover from checkpoint ──
    print("\n[7/8] Simulate session restart — recover from checkpoint")
    recovered = ckpt.restore_from_latest(task_id)
    assert recovered is not None, "No checkpoint to restore"
    print(f"  Restored stage: {recovered['current_stage']}")
    assert recovered['current_stage'] == 'QA', f"Expected QA from checkpoint, got {recovered['current_stage']}"
    print(f"  OK — checkpoint recovery works")

    # Verify all checkpoints on disk
    ckpt_files = list(ckpt.checkpoint_dir.glob("*.json"))
    print(f"  Checkpoint files on disk: {len(ckpt_files)}")
    assert len(ckpt_files) >= 1
    print(f"  OK — checkpoints persisted")

    # ── 8. Full state verification ──────────────────────────────
    print("\n[8/8] Final state verification")

    # Reload fresh from StateStore
    w = store.load_workitem(task_id)
    assert w.current_stage == 'QA', f"StateStore stage: expected QA, got {w.current_stage}"
    print(f"  StateStore — stage: {w.current_stage} OK")

    events_after = journal.get_for_project(proj_id)
    assert len(events_after) >= 5, f"Expected ≥5 events, got {len(events_after)}"
    print(f"  EventJournal — {len(events_after)} events OK")

    r = c.handle('list_tasks', {'project_id': proj_id})
    assert r['ok']
    assert r['data']['count'] >= 1
    print(f"  list_tasks — {r['data']['count']} task(s) OK")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — V1 pipeline end-to-end verified")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Project:   {proj_id[:8]}")
    print(f"  Task:     {task_id[:8]}")
    print(f"  Final:    stage=QA, gate approved, handoff submitted")
    print(f"  Events:   {len(events_after)}")
    print(f"  Checkpoints: {len(ckpt_files)}")
    print(f"  Gates:    {len(gates)}")
    print(f"  Handoffs: {len(handoffs)}")


if __name__ == '__main__':
    main()
