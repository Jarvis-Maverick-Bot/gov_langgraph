# V1_8_DELIVERY_PACKAGE.md

**Version:** 1.0  
**Date:** 2026-04-14  
**Status:** COMPLETE — V1.8 Sprint Closed

---

## Game: Grid Escape

Grid Escape is an AI-native maze navigation game. The agent starts in a grid and must find the exit using navigation commands.

**CLI:** `python games/grid_escape.py --grid ge-001`  
**Grids:** ge-001 (7x7), ge-002 (8x8), ge-003 (10x10)  
**Commands:** look, move <n/s/e/w>, status, restart, quit

---

## Package Contents

### 1. Game Brief

Grid Escape is the V1.8 game product — first AI-native game through the Claw Studio + Viper operating model. CLI-first, governed by PMO event routing and bounded command/control loop.

Full spec: `governance/V1.8/V1_8_SPEC.md`

### 2. Production Handoff Package

- `games/grid_escape.py` — top-level runner script
- `games/grid_escape/engine.py` — game engine with `_signal_escaped`
- `games/grid_escape/__main__.py` — CLI with `_display_escaped` (tier display)
- `games/grid_escape/grids.py` — grid definitions (ge-001, ge-002, ge-003)
- `games/grid_escape/scoring.py` — `compute_tier(steps, optimal)` function

### 3. Build/Output Evidence

- `evidence/gameplay/M1_R2_EVIDENCE.md` — ge-001 and ge-002 completion logs
- `games/grid_escape/tests/` — 55 tests, all passing

### 4. PMO CLI Reference

- `governance/pmo/V1_8_PMO_CLI_REFERENCE.md` — full command reference
- `governance/pmo/V1_8_PMO_ACTION_INVENTORY.md` — action inventory

### 5. PMO Event Routing Evidence

- `evidence/routing/routing_proof_case.log` — routing decision trace (INTAKE→DETERMINE→ROUTE→RESOLVE→RELAY)
- `evidence/routing/control_loop_trace.log` — command/control loop trace (LAUNCH→INSPECT→PAUSE→INSPECT→INVOKE→TERMINATE→INSPECT)
- `governance/pmo/data/pmo_event_log.json` — live event log
- `governance/pmo/data/pmo_task_log.json` — live task log

### 6. Agent Seats Evidence

- `V1_8_AGENT_ROLES.md` — Planner and TDD role definitions, approved by Nova
- `evidence/governance/planner_trace.md` — Planner seat trace
- `evidence/governance/tdd_trace.md` — TDD seat trace
- `evidence/governance/handoff_chain_trace.md` — seat handoff chain

### 7. Claw <> Viper Handoff Evidence

- `handoff/evidence/handoff_001.md` — HANDOVER-001 (Claw→Viper, WI-003)
- `handoff/evidence/return_receipt_001.md` — RETURN-001 (Viper→Claw, real outputs delivered)

### 8. Closure Test (10 Foundation Questions)

| # | Question | Answer | Evidence |
|---|----------|--------|---------|
| 1 | Grid Escape is deliverable and runnable | YES | `games/grid_escape.py`, `evidence/gameplay/M1_R2_EVIDENCE.md` |
| 2 | CLI commands work (look/move/status/restart/quit) | YES | 55 tests passing |
| 3 | Completion signal is correct (ESCAPED format) | YES | `compute_tier` wired into engine, 5-field format |
| 4 | Scoring tiers computed correctly | YES | `scoring.py`, 55 tests passing |
| 5 | PMO CLI commands work (7 base ops) | YES | `governance/pmo/pmo_cli.py`, evidence/pmo_cli/pmo_cli_trace.log |
| 6 | PMO event routing rules work | YES | routing_proof_case.log, pmo_event_log.json |
| 7 | Bounded command/control loop operational | YES | control_loop_trace.log, pmo_task_log.json |
| 8 | Planner + TDD seats instantiated and proven | YES | planner_trace.md, tdd_trace.md, V1_8_AGENT_ROLES.md |
| 9 | Claw <> Viper handoff exercised (real, not pseudo) | YES | handoff_001.md + return_receipt_001.md |
| 10 | All evidence linked and accessible | YES | This document, all files referenced |

---

**V1.8 closed 2026-04-14T17:58 GMT+8.**  
Execution plan: `\\192.168.31.124\Nova-Jarvis-Shared\working\gov_langgraph\V1.8\V1_8_EXECUTION_PLAN.md` (v1.12)