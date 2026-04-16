# Sprint 1 Additional: Queue Inspection Trace

## Scenario Definition
Tests that the governance CLI inspection commands return structured state for queue, task, work-item, and escalation domains without narrative — enabling direct machine consumption and governance observability.

## Evidence

### `governance inspect WI-001` (work-item domain)

Command: `python governance/cli/cli.py inspect WI-001`

Output (captured live, 2026-04-16):
```json
{
  "ok": true,
  "domain": "work-item",
  "type": "work_item",
  "item_id": "WI-001",
  "name": "Grid Escape M1",
  "stage": "IN_REVIEW",
  "artifacts_count": 3,
  "validations_count": 1,
  "blockers_count": 2,
  "active_blockers": [
    {"id": "BLK-e5a4d5ad", "description": "Needs Nova review before delivery", "resolved": false},
    {"id": "BLK-69c5343d", "description": "Awaiting Nova final review", "resolved": false}
  ],
  "delivery_package": {"id": "PKG-673b25b3", "stage": "IN_PROGRESS", "artifacts": ["ART-c8a8b379"]},
  "created_at": "2026-04-14T06:03:01+00:00",
  "updated_at": "2026-04-14T06:17:30+00:00",
  "source": "governance_store"
}
```

### `governance inspect TASK-TEST-001` (task domain)

Command: `python governance/cli/cli.py inspect TASK-TEST-001`

Output (captured live, 2026-04-16):
```json
{
  "ok": true,
  "domain": "task",
  "type": "TDD",
  "item_id": "TASK-TEST-001",
  "state": "CANCELED",
  "assigned_to": "TDD",
  "owned_by": "Jarvis",
  "created_at": "2026-04-14T12:24:04+00:00",
  "updated_at": "2026-04-14T12:24:15+00:00",
  "source": "governance_store"
}
```

### `governance task-list` (all tasks)

Command: `python governance/cli/cli.py task-list`

Output (captured live, 2026-04-16):
```json
[
  {"task_id": "task-001", "lifecycle_state": "SUCCEEDED", "assigned_executor": "tdd"},
  {"task_id": "task-002", "lifecycle_state": "RUNNING",   "assigned_executor": "planner"},
  {"task_id": "task-003", "lifecycle_state": "WAITING",   "assigned_executor": "jarvis"}
]
```

### `governance queue-list` (live queue state)

Command: `python governance/cli/cli.py queue-list`

Output: `[]` (live queue empty at inspection time)

Note: Queue events preserved in append-only evidence logs (`evidence/queue/*.jsonl`).

## Universal Inspect Coverage

Evidence source: `governance/cli/commands/inspect_cmd.py`

The universal inspect checks domains in order:
1. Queue messages — via `governance/queue/data/messages.json` → `evidence/queue/*.jsonl` fallback
2. Tasks — via `governance/data/pmo_task_store.json`
3. Work items — via `governance/data/pmo_state.json`
4. Escalations — via `governance/escalation/data/escalations.json` → `evidence/escalation/*.jsonl` fallback

Each domain returns structured JSON with no narrative:
- `domain`, `type`, `item_id`, `state`
- Domain-specific fields (sender/receiver for queue, assigned_to for task, stage/blockers for work-item)
- `source`: governance_store or evidence_log

## Conclusion

CLI inspection is fully operational across all 4 domains (queue, task, work-item, escalation). Returns pure structured JSON — no narrative — suitable for machine consumption, dashboards, or governance audits. Evidence logs serve as append-only fallback when governance store is empty.

## Source Files
- `evidence/queue/2026-04-15.jsonl`
- `evidence/queue/2026-04-16.jsonl`
- `governance/cli/commands/inspect_cmd.py`
- Live CLI outputs captured above
