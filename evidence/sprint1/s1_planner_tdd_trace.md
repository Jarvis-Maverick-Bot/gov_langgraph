# Sprint 1 Additional: Planner→TDD→Result Trace

## Scenario Definition
Full Planner→NATS→TDD→result trace for the ESCAPED tier feature: user story → task plan → failing test → passing code → production artifact.

## Evidence

### User Story Input

**Source:** `evidence/governance/planner_trace.md`

"As a player, I want the ESCAPED message to include my tier, so I immediately know how well I played."

### Planner → NATS Output

**Source:** `evidence/governance/planner_trace.md` (16:14 GMT+8)

```
task_plan: [
  TASK-001: Update ESCAPED format in engine.py to include tier as sixth field
  TASK-002: Wire compute_tier into escape path
  TASK-003: Add end-to-end integration test for ESCAPED with tier
]
recommended_order: [TASK-001, TASK-002, TASK-003]
```

### TDD → NATS Response

**Source:** `evidence/governance/tdd_trace.md` (16:23 GMT+8)

**Failing test (run against current codebase before code change):**
```python
assert result.startswith('ESCAPED|')
parts = result.split('|')
assert len(parts) == 5, f'Expected 5 fields, got {len(parts)}: {result}'
# FAILED: got 4 fields — tier not yet in ESCAPED
```

**Failing test output:**
```
FAILED — len(parts)==5 assertion failed (got 4): ESCAPED|8|Grid(7x7, seed=3)|2026-04-14T16:20:20
```

### Passing Code Applied

**Source:** `evidence/governance/tdd_trace.md`

```
Changes to 3 files:
- grid.py: Added grid_id param + property to Grid class
- grids.py: Pass grid_id to Grid() constructor
- engine.py: compute_tier wired into escape path; tier appended as 5th field
  Old: f'ESCAPED|{self.step_count}|{self.grid}|{ts}'
  New: f'ESCAPED|{self.step_count}|{self.grid}|{ts}|{tier}'
```

### Test Results After Code Applied

```
55 tests pass — new tier field in ESCAPED, pre-existing test_completion updated to expect 5 fields
```

### Production Artifact

**Source:** `evidence/governance/handoff_chain_trace.md`

```
ESCAPED|8|Grid(7x7, seed=3)|2026-04-14T16:22:14|PERFECT
```

## End-to-End Trace

```
User Story → [Planner @ 16:14] → TASK-001/002/003
           → [NATS publish]
           → [TDD @ 16:23] → failing test FAILS on current code
           → minimal passing code applied to engine.py, grid.py, grids.py
           → 55 tests pass
           → ESCAPED|<steps>|<grid>|<ts>|<tier> = PERFECT
```

## Conclusion

Full Planner→NATS→TDD→result trace proven end-to-end. Real user story, real gap (compute_tier not called), real task spec (TASK-001/002/003), real failing test (fails on current code), real passing code (3 files modified), real test suite pass (55 tests). ESCAPED message now includes tier.

## Source Files
- `evidence/governance/planner_trace.md`
- `evidence/governance/tdd_trace.md`
- `evidence/governance/handoff_chain_trace.md`
