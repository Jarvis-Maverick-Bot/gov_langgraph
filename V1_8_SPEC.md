# V1.8 Scope-to-Spec Mapping

**Version:** 1.3
**Date:** 2026-04-14
**Rework basis:** `V1_8_SCOPE_REWORK_REQUIREMENTS_FOR_JARVIS.md` (Nova, 2026-04-14)

**Purpose:** Ensures every SPEC element traces to a defined Scope Function. No orphaned specification items.

**Two layers in this document — must not be conflated:**
- **Baseline spec** — the target governance model (command names, lifecycle states, folder structure)
- **Implementation note** — where current code/stated intent diverges from baseline, marked with [IMPLEMENTATION NOTE]

---

| Scope Function | SPEC Element |
|---------------|-------------|
| **F1.1.1** Define one bounded real game concept | → Grid Escape (7×7, 8×8, 10×10 grids) |
| **F1.1.2** Define game objective and completion condition | → Reach exit tile; `ESCAPED|<steps>|<grid_id>|<timestamp>` |
| **F1.1.3** Define game rules and interaction constraints | → Grid cell types (S/E/#/./A), move semantics, wall blocking |
| **F1.1.4** Define what counts as successful Agent completion | → Agent occupies exit tile; completion event fires |
| **F1.1.5** Define minimum acceptable playable form | → Standalone Python engine, 3 validated grids, CLI interface |
| **F2.1.1** Define first standardized CLI command set | → `look`, `move`, `status`, `restart`, `quit` + aliases (n/s/e/w) |
| **F2.1.2** Define command inputs/outputs/invocation shape | → Section 3 command table; batch mode STDIN/STDOUT |
| **F2.1.3** Define minimum command coverage for gameplay | → look + move + status + restart + quit = minimum set |
| **F2.1.4** Define command behavior expectations and failure handling | → `BLOCKED`, `UNKNOWN COMMAND`, error formats |
| **F2.2.1** Support game start/initiation via CLI | → `look` renders grid; game begins on first `move` |
| **F2.2.2** Support in-game action submission via CLI | → `move <dir>` via STDIN |
| **F2.2.3** Support status/state retrieval via CLI | → `status` returns step count + position + state |
| **F2.2.4** Support game completion/result retrieval via CLI | → `ESCAPED|<steps>|<grid_id>|<timestamp>` |
| **F2.2.5** Support bounded error reporting | → `BLOCKED` for invalid moves; `UNKNOWN COMMAND` for bad input |
| **F2.3.1** CLI usable by real Agent, not only human | → Batch mode: `echo -e "look\nmove..." \| python grid_escape.py` |
| **F2.3.2** Command surface stable for repeatable validation | → Deterministic grid; same seed = identical grid every run |
| **F2.3.3** Command set explicit for test/acceptance evidence | → Structured completion line enables automated pass/fail |
| **F3.2.1** Support work-item creation via CLI | → `governance create-work-item <name>` |
| **F3.2.2** Support artifact submission via CLI | → `governance submit-artifact <item_id> <path>` |
| **F3.2.3** Support stage transition request via CLI | → `governance request-transition <item_id> <stage>` |
| **F3.2.4** Support validation-result recording via CLI | → `governance record-validation <item_id> <result>` |
| **F3.2.5** Support blocker/escalation signaling via CLI | → `governance signal-blocker <item_id> <desc>` |
| **F3.2.6** Support delivery candidate packaging via CLI | → `governance package-delivery <item_id>` |
| **F3.3.1** Operations complete without UI dependency | → All 7 commands via CLI; no browser required |
| **F3.3.2** CLI path is real infrastructure, not demo scaffolding | → Commands produce actual state changes |
| **F3.3.3** UI remains optional/oversight-oriented | → UI is visibility layer only |
| **F4.1.1–4.1.3** Workflow/queue/artifact visibility | → Thin governance UI (port 8000): workflow, queue, artifact views |
| **F4.2.1–4.2.3** Governance authority surfaces | → Human approval screens at authority points; escalation visibility |
| **F4.3.1–4.3.3** UI dependency control | → UI confirmed optional; CLI works if UI is offline |
| **F5.1.1–5.1.3** Routed-event intake | → `governance route-event <event_json>` accepts event; logs to governance |
| **F5.2.1–5.2.4** Ownership determination | → Rule-based deterministic lookup; no AI inference in V1.8 |
| **F5.3.1–5.3.4** Routed resolution completion | → Intake → determine → route → execute → relay → confirm |
| **F6.1.1–6.1.5** Operational control actions | → `governance launch/pause/inspect/terminate-task` + `governance invoke-command` |
| **F6.2.1–6.2.3** Coordination return path | → Results relayed through routing engine to initiator |
| **F6.3.1–6.3.3** Boundedness and authority control | → All actions scoped to V1.8 approved boundaries |
| **F7.1.1–7.1.3** Required seat/component definition | → 7 roles defined in V1_8_AGENT_ROLES.md |
| **F7.2.1–7.2.3** Seat/component creation | → Planner + TDD instantiated for V1.8; others documented |
| **F7.3.1–7.3.3** Governance review | → Nova reviews and approves seat config before acceptance |
| **F7.4.1** Define all 7 roles as skill specs | → Skills documented in V1_8_AGENT_ROLES.md |
| **F7.4.2** Instantiate Planner + TDD as live sub-agents | → [IMPLEMENTATION NOTE] — M4-R1 course correction: Planner + TDD must be persistent OpenClaw agents, not one-shot sub-agents |
| **F7.4.3** Keep others as V1.9 targets | → Architect/CodeReviewer/Security/Docs/DBExpert documented as V1.9 targets |
| **F7.4.4** Prove Planner→TDD→code handoff | → Evidence: handoff chain trace |
| **F7.4.5** Skill specs support V1.9 instantiation | → Specs concrete enough to instantiate without re-architecture |
| **F8.1.1–8.1.3** Real Claw→Viper handoff initiation | → Handoff package with game definition, constraints, criteria |
| **F8.2.1–8.2.3** Viper execution response | → Viper executes engineering work, returns output |
| **F8.3.1–8.3.3** Real boundary proof | → Exercised in Grid Escape delivery; evidence captured |
| **F9.1.1–9.1.4** Validation evidence generation | → Test record + completion logs + CLI logs + routing logs |
| **F9.2.1–9.2.3** Acceptance support | → Minimum evidence set defined; real evidence chain |
| **F9.3.1–9.3.3** Closure integrity | → No theoretical-only claims; all proof areas tested |
| **F10.1.1–10.1.6** Core delivery artifacts | → Game Brief + SPEC + Handoff Package + Build evidence + Test Record + Delivery Package |
| **F10.2.1–10.2.3** Operational traceability artifacts | → Production queue trace + CLI command set + routed-event evidence |
| **F10.3.1–10.3.3** Artifact completeness and integrity | → All artifacts linked to actual delivery work |
| **F11.1.1–11.1.3** Scope decomposition rule | → Functional Block → Feature → Function mapping maintained |
| **F11.2.1–11.2.3** Planning decomposition rule | → All Functions resolved to sprint tasks before backlog |
| **F11.3.1–11.3.3** Governance and planning usability | → Decomposition reviewable by Nova; usable by Jarvis |

---

## Grid Escape — Technical Specification

**Mapped Functions:** F1.1.1–F1.3.4, F2.1.1–F2.3.3

### 1. Game Concept

**Grid Escape** — bounded maze-navigation, single-objective, CLI-native.

**Grid Model:**
- Cell types: `S` start, `E` exit, `#` wall, `.` open, `A` agent
- Grid sizes: 7×7 (ge-001), 8×8 (ge-002), 10×10 (ge-003)
- BFS-verified solvable path for every grid

**Completion:** Agent lands on `E` → `ESCAPED|<steps>|<grid_id>|<timestamp>`

---

### 2. CLI Command Surface

| Command | Input | Output | Function |
|---------|-------|--------|----------|
| `look` | — | ASCII grid with agent position | F2.2.1 |
| `move <dir>` | north/n/south/s/east/e/west/w | Grid update or `BLOCKED` | F2.2.2 |
| `status` | — | `Step: N \| State: playing/escaped \| Pos: (x,y)` | F2.2.3 |
| `restart` | — | Grid reset to initial state | F2.2.1 |
| `quit` | — | Final step count, session ends | F2.2.5 |

**Error outputs:**
- Unknown command → `UNKNOWN COMMAND`
- Invalid direction → `INVALID DIRECTION`
- Move into wall/boundary → `BLOCKED`

---

### 3. Scoring

- **Primary metric:** Step count (lower is better)
- **Tiers:** PERFECT / EXCELLENT / GOOD / COMPLETED / OVERMOVED
- Optimal path pre-computed via BFS per grid

---

### 4. Agent Playability

- All interaction via STDIN/STDOUT — no browser, no visual UI
- Deterministic grid generation (seed → identical grid every run)
- `look` always returns full grid state — no hidden information
- Clear completion signal: `ESCAPED` line
- Repeatable: `restart` resets same grid

---

### 5. Invocation

```bash
python games/grid_escape.py --grid <grid_id> [--seed <seed>]
```

**Interactive:** `python games/grid_escape.py --grid ge-001`
**Batch/Agent:** `echo -e "look\nmove east\n..." | python games/grid_escape.py --grid ge-001`

Completion line: `ESCAPED|<steps>|<grid_id>|<timestamp>`

---

### 6. Starter Grids

| Grid ID | Size | Optimal | Status |
|---------|------|---------|--------|
| ge-001 | 7×7 | 8 steps | Verified solvable |
| ge-002 | 8×8 | 12 steps | Verified solvable |
| ge-003 | 10×10 | 18 steps | Verified solvable |

---

## Governance CLI Reference

**Command naming:** All commands use `governance` prefix (baseline). Current code uses `governance` prefix. [IMPLEMENTATION NOTE] Historical evidence references `pmo` prefix — preserved as historical record.

**Command categories (R1):**

| Category | Semantic | Examples |
|----------|----------|----------|
| A: Governance/Record | Writes intent or facts, no execution | create-work-item, submit-artifact, request-transition |
| B: Execution/Dispatch | Triggers real bounded backend action; result return required | launch-subagent, invoke-command, pause-task |
| C: Observation | Returns current state or stored results; no side effects | status, route-event, inspect-task |

---

### 7. Category A — Governance / Record Commands

Writes governance state only. Records intent or facts. Does NOT execute work.

| Command | Description | Function |
|---------|-------------|----------|
| governance create-work-item <name> | Create delivery work item | F3.2.1 |
| governance submit-artifact <item_id> <path> | Submit artifact to item | F3.2.2 |
| governance request-transition <item_id> <stage> | Request stage advancement | F3.2.3 |
| governance record-validation <item_id> <result> | Record validation result | F3.2.4 |
| governance signal-blocker <item_id> <desc> | Flag blocker or escalation | F3.2.5 |
| governance package-delivery <item_id> | Register delivery candidate | F3.2.6 |
| governance status [item_id] | Show work-item state or list | F3.2.6 |

**UI dependency:** All Category A commands work without UI (F3.3.1).

---

### 8. Category B — Execution / Dispatch Commands

[SPEC NOTE — target-state spec:] These commands are defined to trigger real bounded backend action and return result payloads. Whether fully implemented as real execution or as bounded synthetic proof is an implementation question; the spec defines the target.

**Rule (R2):** Execution commands MUST either (a) trigger a real bounded backend action, or (b) fail explicitly with error + reason.

| Command | Description | Function | Lifecycle Effect |
|---------|-------------|----------|-----------------|
| governance launch-subagent <task_id> <type> | Launch bounded sub-agent task | F6.1.1 | → QUEUED → DISPATCHED → RUNNING |
| governance invoke-command <task_id> <command> | Execute approved command | F6.1.2 | → RUNNING → SUCCEEDED/FAILED |
| governance pause-task <task_id> | Pause active task | F6.1.4 | RUNNING → WAITING |
| governance resume-task <task_id> | Resume paused task | F6.1.4 | WAITING → RUNNING |
| governance terminate-task <task_id> | Terminate authorized task | F6.1.5 | → CANCELED |

**Authority gating:** Out-of-scope actions return `{"ok": false, "error": "FORBIDDEN"}`.

---

### 9. Category C — Observation / Result Commands

Returns current state or stored results. No side effects.

| Command | Description | Function |
|---------|-------------|----------|
| governance status [item_id] | Show work-item state or list | F3.2.6 |
| governance route-event <event_json> | Route event to destination | F5.1.1–F5.1.3 |
| governance event-log [event_id] | Return event log or single event | F5.3.1–F5.3.4 |
| governance inspect-task <task_id> | Full task lifecycle state | F6.1.3 |
| governance get-task-result <task_id> | Stored result payload | F6.2.1–F6.2.3 |

**Routing rules (F5.2.1–F5.2.4) — V1.8 deterministic set:**

| Event Type | Destination |
|------------|-------------|
| UNKNOWN_TOOL | Most recent Agent in context |
| BLOCKER_ESCALATION | Governance |
| CLARIFICATION_NEEDED | Nova |

---

### 10. Task Lifecycle States

**Minimum required semantic statuses (R3):**

| State | Meaning |
|-------|---------|
| QUEUED | Task created, not yet dispatched to executor |
| DISPATCHED | Sent to executor, executor has acknowledged |
| RUNNING | Executor actively working |
| WAITING | Paused (awaiting input, resource, or gate) |
| SUCCEEDED | Completed successfully with result |
| FAILED | Completed with error |
| CANCELED | Terminated by authorized request before completion |
| TIMED_OUT | Exceeded allocated execution window |

---

### 11. Governance State vs Execution State (R5)

**These two concerns must NOT be conflated:**
- **Work Item** — governance state (stage, artifacts, blockers). Lives in `governance/cli/store.py`
- **Task** — execution state (lifecycle, executor, result). Lives in `governance/control/task_store.py`
- A work item transition does NOT automatically create or complete a task
- Task completion does NOT automatically advance work-item stage

---

## Agent Roles

### V1.8 instantiated seats

- **Planner** — Persistent OpenClaw agent (`C:\Users\John\.openclaw\agents\jarvis-planner/`). Decomposes user stories into task plans with acceptance criteria.
- **TDD** — Persistent OpenClaw agent (`C:\Users\John\.openclaw\agents\jarvis-tdd/`). Given task spec → produces failing test first → minimal passing code.

[IMPLEMENTATION NOTE — M4-R1 course correction, 2026-04-14T19:30 GMT+8:]
M4-R1 initially treated Planner + TDD as one-shot sub-agents. Corrected intent: both must be persistent OpenClaw agents, augmenting the Jarvis team alongside jarvis-core/qa/ui. Re-implementation is a post-V1.8 correction item, not a V1.8 delivery claim.

### Organizational placement

```
Jarvis Team (governance/management layer)
├── jarvis-core   — persistent OpenClaw agent
├── jarvis-qa     — persistent OpenClaw agent
├── jarvis-ui     — persistent OpenClaw agent
├── Planner       — persistent OpenClaw agent [CORRECTION PENDING]
└── TDD           — persistent OpenClaw agent [CORRECTION PENDING]

Viper (execution layer)
├── VIPER_BA / VIPER_SA / VIPER_DEV / VIPER_QA

Maverick (governance agent)
```

### V1.8 documented skill specs (V1.9 targets)

Architect, CodeReviewer, Security, Docs, DBExpert — documented in V1_8_AGENT_ROLES.md as V1.9 targets, not instantiated in V1.8.

### Handoff chain (F7.4.4)

BA/SA → Planner → TDD → CodeReviewer → Security (if needed) → QA → Delivery

---

## Validation Evidence Requirements

| Evidence Type | Source | Function |
|---------------|--------|----------|
| Game completion log (ge-001 + ge-002) | `games/grid_escape.py` batch run | F9.1.1 |
| Agent gameplay proof | Jarvis batch run log | F9.1.2 |
| Governance CLI operation log | `governance` command invocations | F9.1.3 |
| Governance Event Routing log | Routing engine events | F9.1.4 |
| Production queue trace | Governance system | F10.2.1 |
| Artifact chain | All delivery artifacts | F10.3.1–F10.3.3 |

---

## Closure Traceability

V1.8 closure requires all 10 Foundation closure test questions answerable "yes" from real evidence — no theoretical claims permitted.

All 10 closure test questions map to Functions above. No Function is left without a corresponding evidence artifact.
