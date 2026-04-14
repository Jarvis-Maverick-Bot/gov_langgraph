# V1.8 Execution Plan

**Version:** 1.18
**Date:** 2026-04-14
**Last Updated:** Final cleanup pass — duplicate headers removed, status table corrected, historical vs baseline intent separated

---

## Purpose

This document has two layers that must not be conflated:

1. **Historical V1.8 delivery record** — what was actually delivered, proven, and signed off
2. **Corrected governance baseline** — the target state for future work, incorporating V1.8 lessons learned

Status entries are keyed to which layer they belong to.

---

## 1. Scope Traceability Overview

Every sprint task maps to one or more Scope Functions (F-scale from V1_8_SCOPE.md). No task exists without a Function root. Functions out-of-scope are explicitly excluded.

**Function reference prefix key:**
- F1.x = First AI-native game delivery proof (Grid Escape)
- F2.x = Agent game interaction via standardized CLI
- F3.x = Governance / PMO CLI-native operating path
- F4.x = Thin governance visibility UI
- F5.x = Governance event routing
- F6.x = Bounded command/control execution loop
- F7.x = Claw Studio Agent seats and components
- F8.x = Real Claw ↔ Viper handoff and return path
- F9.x = Validation and acceptance evidence
- F10.x = Delivery-grade artifact chain
- F11.x = Structured delivery decomposition model

---

## 2. Sprint-to-Function Map

| Sprint | Functions Targeted | Primary Goal | Status |
|--------|-------------------|--------------|--------|
| M1-R1 | F1.1.1–F1.2.4, F2.1.1–F2.2.5, F2.3.1–F2.3.3, F9.1.1, F10.1.1–F10.1.2 | Grid Escape engine + CLI working | DONE |
| M1-R2 | F1.3.1–F1.3.4, F2.3.1–F2.3.3, F9.1.2 | Real Agent gameplay proof | DONE |
| M2-R1 | F3.1.1–F3.1.3, F3.2.1–F3.2.6, F9.1.3, F10.1.3 | Governance CLI surface delivered | DONE |
| M2-R2 | F3.3.1–F3.3.3, F9.1.3, F10.2.2 | Governance CLI integration proof | DONE |
| M3-R1 | F5.1.1–F5.3.4, F6.3.1–F6.3.3 | Governance event routing core | DONE |
| M3-R2 | F6.1.1–F6.3.3, F9.1.4 | Bounded command/control loop | DONE |
| M4-R1 | F7.1.1–F7.4.5, F9.2.1–F9.2.3 | Claw Studio Agent seats (Planner + TDD) | DONE |
| M4-R2 | F4.1.1–F4.3.3, F9.2.1–F9.2.3 | Thin governance visibility UI | DONE |
| M4-R3 | F8.1.1–F8.3.3, F10.2.3 | Real Claw ↔ Viper handoff exercised | DONE |
| M4-R4 | F9.1.1–F9.3.3, F10.1.1–F10.3.3, F11.2.1–F11.2.3 | Validation evidence + delivery package | DONE |

**V1.8 Result:** 10/10 sprints complete. All signed off by Nova (2026-04-14T18:53 GMT+8).

**Nova approval:** V1_8_EXECUTION_PLAN.md → APPROVED | V1_8_SPEC.md → APPROVED WITH NOTE (hybrid corrected governance spec, not frozen as-built)

**Total:** 48 tasks across 10 sprints, ~13 days.

---

## 3. Sprint Details

### Sprint M1-R1 — Grid Escape Engine + CLI Surface
**Functions:** F1.1.1, F1.1.3, F1.1.5, F1.2.1–F1.2.4, F2.1.1–F2.2.5, F2.3.1–F2.3.3, F9.1.1, F10.1.1–F10.1.2
**Duration:** 2 days
**Exit gate:** Game completable via CLI without error

**Tasks:** T1.1 (grid data model) → T1.9 (README)
**DoD:** Grid class, cell types, BFS path, ASCII renderer, 5 commands, completion detection, scoring tiers, 3 starter grids, unit tests, README

**Verification:**
- `python games/grid_escape.py --grid ge-001` runs without error
- `python games/grid_escape.py --grid ge-002` runs without error
- `python games/grid_escape.py --grid ge-003` runs without error
- `python -m pytest games/grid_escape/tests/ -v` — 53 tests PASSED
- `games/grid_escape/README.md` exists with interactive + batch usage

**Historical note:** `python -m games.grid_escape` failed in some environments (ModuleNotFoundError). Official run path: `python games/grid_escape.py --grid ge-001`.

**Exit gate:** 2026-04-14T14:00 GMT+8 — all verified

---

### Sprint M1-R2 — Agent Gameplay Proof
**Functions:** F1.3.1–F1.3.4, F2.3.1–F2.3.3, F9.1.2
**Duration:** 1 day
**Exit gate:** Jarvis completes ge-001 and ge-002 via CLI with evidence

**Tasks:** T2.1 (ge-001 run) → T2.3 (evidence compilation)

**Results:**
- ge-001: 8 steps (optimal=8) → **PERFECT** tier
- ge-002: 12 steps (optimal=12) → **PERFECT** tier

**Verification:**
- `evidence/gameplay/ge-001_completion.log` exists with valid `ESCAPED|8|ge-001|...`
- `evidence/gameplay/ge-002_completion.log` exists with valid `ESCAPED|12|ge-002|...`

**Exit gate:** 2026-04-14T13:40 GMT+8 — all verified

---

### Sprint M2-R1 — Governance CLI Surface
**Functions:** F3.1.1–F3.1.3, F3.2.1–F3.2.6, F9.1.3, F10.1.3, F10.2.2
**Duration:** 2 days
**Exit gate:** All 7 governance CLI commands respond correctly to valid input

**Tasks:** T3.1 (action inventory) → T3.5 (integration smoke test)

**7 Governance CLI Commands (Category A — governance/record):**
- `governance create-work-item <name>`
- `governance submit-artifact <item_id> <path>`
- `governance request-transition <item_id> <stage>`
- `governance record-validation <item_id> <result>`
- `governance signal-blocker <item_id> <desc>`
- `governance package-delivery <item_id>`
- `governance status [item_id]`

**State store:** `governance/data/pmo_state.json`

**Verification:**
- `V1_8_PMO_ACTION_INVENTORY.md` exists and lists all 7 commands
- `V1_8_PMO_CLI_REFERENCE.md` exists with all 7 commands documented
- All 7 commands produce valid JSON output
- `python governance/cli/cli.py --help` works for all 7 commands
- `evidence/pmo_cli/pmo_cli_trace.log` exists with 7 command traces

**Nova verdict: M2-R1 APPROVED** (2026-04-14T14:55 GMT+8)

---

### Sprint M2-R2 — Governance CLI Integration Proof
**Functions:** F3.3.1–F3.3.3, F9.1.3, F10.2.2
**Duration:** 1 day
**Exit gate:** Full delivery lifecycle trace via CLI without UI dependency

**Tasks:** T4.1 → T4.5

**Full lifecycle executed:**
```
create-work-item WI-001
submit-artifact (3x): grid_escape.py, engine.py, grids.py
request-transition: BACKLOG → IN_PROGRESS → IN_REVIEW
record-validation: PASS
signal-blocker: "Awaiting Nova final review"
package-delivery: PKG-673b25b3
governance status WI-001 → final state confirmed
```

**State store:** `governance/data/pmo_state.json`

**Verification:**
- Item created via CLI; item_id WI-001 returned
- Artifact submitted, stage transitioned, validation recorded
- `governance status WI-001` reflects all changes (verified live)
- `evidence/pmo_cli/M2_R2_trace.log` contains complete lifecycle

**Nova verdict: M2-R2 APPROVED WITH NOTES** (2026-04-14T14:55 GMT+8)
**Carry-forward cleanup noted:** artifact trace/state mismatch, stale delivery package snapshot, state carryover noise — cleaned before M4 delivery packaging.

---

### Sprint M3-R1 — Governance Event Routing Core
**Functions:** F5.1.1–F5.3.4, F6.3.1–F6.3.3
**Duration:** 2 days
**Exit gate:** Routing engine resolves one real ownership/handling uncertainty case end-to-end

**Tasks:** T5.1 → T5.5

**Routing rules (V1.8 deterministic set):**

| Event Type | Destination |
|------------|-------------|
| UNKNOWN_TOOL | Most recent Agent in context |
| BLOCKER_ESCALATION | PMO |
| CLARIFICATION_NEEDED | Nova |
| (default) | PMO |

**Implementation:** `governance/routing/engine.py`
**Event log:** `governance/data/pmo_event_log.json`

**Verification:**
- `governance route-event <json>` accepts valid JSON, returns event_id
- Event log: INTAKE → DETERMINE → ROUTE → RESOLVE → RELAY
- `evidence/routing/routing_proof_case.log` exists with complete trace

**Nova verdict: M3-R1 APPROVED WITH NOTES** (2026-04-14T15:24 GMT+8)
**Note:** Bounded V1.8 proof, not a mature routing runtime.

---

### Sprint M3-R2 — Bounded Command/Control Loop
**Functions:** F6.1.1–F6.3.3, F9.1.4
**Duration:** 1 day
**Exit gate:** At least one sub-agent task launched and controlled via CLI

**Tasks:** T6.1 → T6.3

**5 Control Commands (Category B — execution/dispatch):**
- `governance launch-subagent <task_id> <type>`
- `governance invoke-command <task_id> <command>`
- `governance pause-task <task_id>`
- `governance resume-task <task_id>`
- `governance terminate-task <task_id>`

**Authority gating:** Out-of-scope actions return `{"ok": false, "error": "FORBIDDEN"}`

**Verification:**
- All 5 control commands return valid JSON
- Full control loop: launch → inspect → pause → inspect → terminate
- `evidence/routing/control_loop_trace.log` exists

**Nova verdict: M3-R2 APPROVED WITH NOTES** (2026-04-14T15:24 GMT+8)
**Note:** Controlled synthetic trace, not live runtime.

---

### Sprint M4-R1 — Claw Studio Agent Seats (Planner + TDD)
**Functions:** F7.1.1–F7.3.3, F7.4.1, F7.4.2, F7.4.4, F9.2.1–F9.2.3
**Duration:** 2 days
**Exit gate:** Planner → TDD → code handoff chain proven in real V1.8 delivery task

**Pre-sprint artifact:** 5 role stubs (Architect, CodeReviewer, Security, Docs, DBExpert) documented in `V1_8_AGENT_ROLES.md` as V1.9 targets — not sprint work.

**Tasks:** T7.1 → T7.7

**Verification:**
- Planner skill spec: `OpenClaw agent config: jarvis-planner/` + `V1_8_AGENT_ROLES.md`
- TDD skill spec: `OpenClaw agent config: jarvis-tdd/` + `V1_8_AGENT_ROLES.md`
- Planner trace: `evidence/governance/planner_trace.md`
- TDD trace: `evidence/governance/tdd_trace.md`
- Handoff chain trace: `evidence/governance/handoff_chain_trace.md`
- 55 tests passing
- Nova sign-off recorded

**Nova Design Correction (non-blocking):** Source docs must explicitly distinguish foundational capability (/pmo/ prefix) from V1.8-bounded proof slice (/v1.8/ prefix).

**Nova verdict: M4-R1 APPROVED** (2026-04-14T16:30 GMT+8)

---

### Sprint M4-R2 — Thin Governance Visibility UI
**Functions:** F4.1.1–F4.3.3, F9.2.1–F9.2.3
**Duration:** 1 day
**Exit gate:** Governance UI accessible on port 8000; CLI works if UI is offline

**Tasks:** T8.1 → T8.3

**UI routes:** `/pmo/health`, `/pmo/workflow`, `/pmo/queue`, `/pmo/artifacts`, `/pmo/approvals`

**Verification:**
- Governance UI serves on port 8000 (`uvicorn governance/ui/main:app --port 8000`)
- All 5 routes return valid content
- UI process stopped — all governance CLI commands still function
- Grid Escape game runs without UI

**Nova Design Correction (non-blocking):** /v1.8 prefix encodes version ownership; conflicts with foundational/global capability interpretation. Distinguish: foundational (/pmo/) vs V1.8-bounded (/v1.8/).

**Nova verdict: M4-R2 APPROVED WITH DESIGN CORRECTION** (2026-04-14T17:29 GMT+8)

---

### Sprint M4-R3 — Real Claw ↔ Viper Handoff
**Functions:** F8.1.1–F8.3.3, F10.2.3
**Duration:** 1 day
**Exit gate:** Claw → Viper handoff exercised with real Grid Escape engineering work

**Tasks:** T9.1 → T9.3

**Acceptance standard — real handoff vs. pseudo-handoff:**

| | Pseudo-handoff (insufficient) | Real operational handoff (required) |
|---|---|---|
| Viper execution | Work acknowledged but not executed | Viper executes bounded work, returns real outputs |
| Return receipt | Document created, no real outputs | Real outputs (code, evidence) returned across boundary |
| Evidence | Document alignment | Cross-team trace showing actual work crossing boundary |

**Handoff evidence:**
- `handoff/evidence/handoff_001.md` — handoff package delivered
- `handoff/evidence/return_receipt_001.md` — real Viper outputs returned
- `V1_8_CLAW_VIPER_HANDOFF.md` — master handoff/return trace doc

**Exit gate:** 2026-04-14T17:56 GMT+8 — COMPLETE

---

### Sprint M4-R4 — Validation Evidence + Delivery Package
**Functions:** F9.1.1–F9.3.3, F10.1.1–F10.3.3, F11.2.1–F11.2.3
**Duration:** 1 day
**Exit gate:** All 10 V1.8 Foundation closure test questions answerable "yes" with real evidence

**Tasks:** T10.1 → T10.6

**Delivery artifacts:**
- `DELIVERABLES/V1.8-Grid-Escape-v1.0.zip`
- `DELIVERABLES/V1.8-PMO-CLI-v1.0.zip`
- `DELIVERABLES/V1.8-Routing-Engine-v1.0.zip`
- `DELIVERABLES/V1.8-Closure-Record.md`

**Nova sign-off:** 2026-04-14T18:53 GMT+8 — V1.8 FORMALLY CLOSED

---

## 4. Dependencies Map

```
M1-R1 [T1.1–T1.9] ──────────────────────────────────────────────┐
                                                              ↓
M1-R2 [T2.1–T2.3] ─────────────────────────────────────────────┐
                                                              ↓
M2-R1 [T3.1–T3.5] ─────────────────────────────────────────────┤
                                                              ↓
M2-R2 [T4.1–T4.5] ─────────────────────────────────────────────┤
                                                              ↓
M3-R1 [T5.1–T5.5] ─────────────────────────────────────────────┤
                                                              ↓
M3-R2 [T6.1–T6.3] ─────────────────────────────────────────────┤
                                                              ↓
M4-R1 [T7.1–T7.7] ─────────────────────────────────────────────┤
                                                              ↓
M4-R2 [T8.1–T8.3] ─┐                                           │
                   ├───────────────────────────────────────────┤
M4-R3 [T9.1–T9.3] ─┤ ── Claw ↔ Viper (exercised after M1+M2+M3) ┤
                   │                                           ↓
M4-R4 [T10.1–T10.6] ←──────────────────────────────────────────┘
```

---

## 5. Out of Scope

The following are explicitly out of scope for V1.8:

| Excluded Item | Reason |
|--------------|--------|
| AI-powered routing inference as primary routing mechanism | V1.8 uses deterministic rule lookup only |
| F4.x heavy UI features | UI must remain thin; heavy UI would block V1.8 closure |
| F7.4.3 instantiation of Architect/CodeReviewer/Security/Docs/DBExpert | Documented as V1.9 targets; not instantiated in V1.8 |
| F10.2.1 multi-game support | Portfolio operations belong to V1.9+ |
| Pub/Sub as generalized infrastructure | Formal Pub/Sub is V1.9 scope |
| Commercial launch/store/promotion | V2.0 territory |

---

## 6. Closure Test Reminder

V1.8 does not close unless all 10 questions below answer **yes** using real evidence:

1. Was a first real AI-native game delivered through the defined governed structure?
2. Is the delivered game materially agent-playable rather than only conceptually described?
3. Can at least one real Agent participant actually play and complete the game through the defined agent-facing interface?
4. Did Claw and Viper function together through a real handoff/execution path where needed?
5. Can all required governance interaction scenarios be performed through CLI commands without depending on UI interaction?
6. Does the CLI also support the specific command set required for the first AI-native game itself?
7. Did Governance Event Routing successfully handle at least one real ownership/handling uncertainty case through a bounded routed-resolution loop?
8. Is UI dependency kept thin enough that the release is not blocked by heavy frontend buildout?
9. Are governance and oversight still explicit at the right authority points?
10. Is the release strong enough to count as first-product proof without borrowing closure language from later versions?

Each sprint exit gate produces evidence directly addressable against these 10 questions.

---

## Appendix: Corrected Governance Baseline (Post-V1.8)

**This section captures the target state incorporating V1.8 lessons. It is NOT the historical V1.8 delivery record.**

### Folder structure (corrected target):
```
governance/
├── cli/          # Category A commands (governance/record) + CLI entry point
│   ├── store.py  # Work-item governance state
│   └── cli.py    # Unified CLI
├── routing/      # Category C (event routing engine)
│   └── engine.py
├── control/      # Category B (execution/dispatch + task lifecycle)
│   ├── control.py
│   └── task_store.py
├── ui/           # Thin visibility UI (/pmo/* routes)
└── data/        # All state files consolidated
```

### Command prefix: `governance` (not `pmo`)

### Planner + TDD seats: persistent OpenClaw agents
- Location: `C:\Users\John\.openclaw\agents\jarvis-planner/` and `jarvis-tdd/`
- Status: re-implementation identified as needed post-V1.8 (M4-R1 course correction, 2026-04-14T19:30 GMT+8)
- Both must augment the Jarvis team as persistent agents, alongside jarvis-core/qa/ui

### UI route naming: `/pmo/` (foundational), NOT `/v1.8/` (version-locked)
- Foundational capabilities (workflow, queue, artifacts, approvals) use `/pmo/` prefix
- This distinction must be maintained in source docs going forward

### Governance state vs execution state separation:
- Work Item state (stage, artifacts, blockers) — `governance/cli/store.py`
- Task execution state (lifecycle, executor, result) — `governance/control/task_store.py`
- These two concerns must NOT be conflated
