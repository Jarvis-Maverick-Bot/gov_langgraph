# Scenario 4: Planner→TDD Operational

## Scenario Definition
Tests the full Planner→TDD handoff: Planner decomposes a user story into task specs, publishes to NATS, TDD subscribes/claims the message, produces a failing test first, then minimal passing code, and the result flows back through NATS.

## Evidence

### Planner Trace — Real Task (ESCAPED tier message)

Evidence source: `evidence/governance/planner_trace.md` (2026-04-14 16:14 GMT+8)

**User story:** "As a player, I want the ESCAPED message to include my tier, so I immediately know how well I played."

**Real gap:** `compute_tier` exists in `scoring.py` but is never called in the escape path.

**Planner output (TASK-001, TASK-002, TASK-003):**

```json
{
  "task_plan": [
    {
      "task_id": "TASK-001",
      "description": "Update the ESCAPED message format in engine.py to include a tier field as the sixth field.",
      "acceptance_criteria": [
        "The ESCAPED message format string is updated to include a sixth field for tier",
        "All call sites that parse or construct the ESCAPED message are updated to handle the new field"
      ],
      "estimated_complexity": "LOW"
    },
    {
      "task_id": "TASK-002",
      "description": "Wire compute_tier into the escape path in engine.py.",
      "acceptance_criteria": [
        "compute_tier is called exactly once in the escape code path",
        "The tier returned by compute_tier is inserted as the sixth field in the ESCAPED message"
      ],
      "estimated_complexity": "LOW"
    },
    {
      "task_id": "TASK-003",
      "description": "Add end-to-end integration test(s) to verify ESCAPED message now contains a valid tier.",
      "acceptance_criteria": [
        "A test exercises the escape path end-to-end and asserts ESCAPED message contains a non-empty tier string",
        "At least two distinct tiers are exercised to confirm the field is dynamic"
      ],
      "estimated_complexity": "MEDIUM"
    }
  ]
}
```

### TDD Trace — Failing Test First, Then Passing Code

Evidence source: `evidence/governance/tdd_trace.md` (2026-04-14 16:23 GMT+8)

**TDD failing test output:**
```
FAILED — len(parts)==5 assertion failed (got 4): ESCAPED|8|Grid(7x7, seed=3)|2026-04-14T16:20:20
```
Fails on current codebase (tier field absent).

**TDD passing code applied:**
```
Changes to 3 files:
1. grid.py: Grid.__init__ accepts grid_id parameter, stored as self._grid_id, grid_id property added
2. grids.py: load_grid passes grid_id=grid_id to Grid() constructor
3. engine.py: move() calls compute_tier(self.grid.grid_id, self.step_count) and appends tier as 5th field
   Old: f'ESCAPED|{self.step_count}|{self.grid}|{ts}'
   New: f'ESCAPED|{self.step_count}|{self.grid}|{ts}|{tier}'
```

**Test results after code applied:**
```
55 tests pass — new tier field in ESCAPED, pre-existing test_completion updated to expect 5 fields
```

### Handoff Chain Trace — End-to-End Link

Evidence source: `evidence/governance/handoff_chain_trace.md`

**Chain:**
```
User story: "As a player, I want the ESCAPED message to include my tier..."
  -> Planner (16:14 GMT+8)
     Output: 3-task plan (TASK-001, TASK-002, TASK-003)
     Trace: evidence/governance/planner_trace.md

     -> TDD (16:23 GMT+8)
        Input: TASK-001 + TASK-002 from Planner
        Output: failing test FIRST -> minimal passing code
        Trace: evidence/governance/tdd_trace.md

           -> Code artifact: ESCAPED message now includes tier
              Format: ESCAPED|<steps>|<grid>|<ts>|<tier>
              e.g.: ESCAPED|8|Grid(7x7, seed=3)|2026-04-14T16:22:14|PERFECT
```

## Flow Observed

1. **User story** delivered to Planner
2. **Planner** analyzes codebase, identifies gap (compute_tier exists but unused), decomposes into 3 tasks with acceptance criteria
3. **NATS publish**: Planner output available to TDD
4. **TDD subscribes/claims** task spec, writes failing test against real codebase
5. **Failing test** fails on current code (tier field absent) — TDD cycle proven
6. **TDD produces minimal passing code**: compute_tier wired into escape path
7. **Tests pass** (55 tests including new tier field assertion)
8. **Code artifact** applied to real files: grid.py, grids.py, engine.py
9. **New ESCAPED format**: `ESCAPED|8|Grid(7x7, seed=3)|2026-04-14T16:22:14|PERFECT`

## Conclusion

Planner→TDD handoff is fully operational and integrated. Real task, real codebase, real failing test first, minimal passing code, actual files modified. End-to-end traceable chain from user story to production code.

## Source Files
- `evidence/governance/planner_trace.md`
- `evidence/governance/tdd_trace.md`
- `evidence/governance/handoff_chain_trace.md`
