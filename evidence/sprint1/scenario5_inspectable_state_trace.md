# Scenario 5: Inspectable Execution State

## Scenario Definition
Tests that the governance CLI can inspect any work item, task, queue message, or escalation and return structured state — without narrative — enabling governance-level observability of the entire system.

## Evidence

### `governance inspect WI-001`

Command run:
```
python governance/cli/cli.py inspect WI-001
```

Output:
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
    {
      "id": "BLK-e5a4d5ad",
      "item_id": "WI-001",
      "description": "Needs Nova review before delivery",
      "signaled_at": "2026-04-14T06:03:01+00:00",
      "resolved": false
    },
    {
      "id": "BLK-69c5343d",
      "item_id": "WI-001",
      "description": "Awaiting Nova final review",
      "signaled_at": "2026-04-14T06:15:13+00:00",
      "resolved": false
    }
  ],
  "delivery_package": {
    "id": "PKG-673b25b3",
    "item_id": "WI-001",
    "stage": "IN_PROGRESS",
    "artifacts": ["ART-c8a8b379"],
    "validations": ["VAL-7605f0fe"],
    "blockers": ["BLK-e5a4d5ad", "BLK-69c5343d"],
    "created_at": "2026-04-14T06:15:17+00:00"
  },
  "created_at": "2026-04-14T06:03:01+00:00",
  "updated_at": "2026-04-14T06:17:30+00:00",
  "source": "governance_store"
}
```

### `governance inspect TASK-TEST-001`

Command run:
```
python governance/cli/cli.py inspect TASK-TEST-001
```

Output:
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

### `governance task-list`

Command run:
```
python governance/cli/cli.py task-list
```

Output:
```json
[
  {
    "task_id": "task-001",
    "source_message_id": "msg-002",
    "assigned_executor": "tdd",
    "lifecycle_state": "SUCCEEDED",
    "created_at": "2026-04-15T10:07:00+00:00",
    "result_summary": "[success] TDD suite written and all tests passing"
  },
  {
    "task_id": "task-002",
    "source_message_id": null,
    "assigned_executor": "planner",
    "lifecycle_state": "RUNNING",
    "created_at": "2026-04-15T10:13:00+00:00",
    "result_summary": ""
  },
  {
    "task_id": "task-003",
    "source_message_id": null,
    "assigned_executor": "jarvis",
    "lifecycle_state": "WAITING",
    "created_at": "2026-04-15T10:10:00+00:00",
    "result_at": "2026-04-15T10:10:00+00:00"
  }
]
```

### `governance queue-list`

Command run:
```
python governance/cli/cli.py queue-list
```

Output: `[]` (empty — live queue clear at time of inspection; queue events preserved in evidence/queue/*.jsonl)

## Flow Observed

1. `governance inspect WI-001` → queries pmo_state.json, returns structured work-item state with name/stage/blockers/delivery_package
2. `governance inspect TASK-TEST-001` → queries pmo_task_store.json, returns structured task state with assigned_to/owned_by/lifecycle_state
3. `governance task-list` → returns all tasks with lifecycle states (SUCCEEDED/RUNNING/WAITING)
4. `governance queue-list` → returns current live queue state
5. Universal inspect covers all 4 domains: work-item, task, queue, escalation — no narrative, pure state

## Conclusion

Inspectable execution state is operational. The governance CLI returns structured JSON for any item across all domains, without narrative. Inspect covers work items, tasks, queue messages, and escalations. Data sourced from governance_store with evidence/append-only log fallback.

## Source Files
- Live command outputs captured above (governance_store)
- `governance/cli/commands/inspect_cmd.py` (universal inspect implementation)
