# V1.8 Architectural Design Proposal

**Version:** 1.3
**Date:** 2026-04-14
**Status:** Approved (v1.1) / Revised (v1.2) / Reworked (v1.3) — scope correction per Nova requirement doc
**Game:** Grid Escape

---

## Scope Rework Notes (v1.3)

This revision addresses Nova's `V1_8_SCOPE_REWORK_REQUIREMENTS_FOR_JARVIS.md` (2026-04-14):

- **R1:** Command semantics classified as governance / execution / observation
- **R2:** Execution commands must cause tangible action; silent JSON success not acceptable
- **R3:** Task lifecycle expanded to full state set: QUEUED/DISPATCHED/RUNNING/WAITING/SUCCEEDED/FAILED/CANCELED/TIMED_OUT
- **R4:** Result return required for execution commands (status, summary, failure reason, timestamps, output ref)
- **R5:** Governance state vs execution state explicitly separated
- **R6:** Folder naming normalized under `governance/` parent (was mixed `pmo_*/governance_ui/agent_seats/`)
- **R7:** Foundational PMO capability vs V1.8 proof slice explicitly distinguished in docs

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Version Control Strategy](#2-version-control-strategy)
3. [Code Directory Structure (Git Repository)](#3-code-directory-structure-git-repository)
4. [Governance Documents (Shared Drive)](#4-governance-documents-shared-drive)
5. [Game Platform -- Open Issue for M1-R1 Resolution](#5-game-platform--open-issue-for-m1-r1-resolution)
6. [Pseudocode -- Grid Escape Engine](#6-pseudocode--grid-escape-engine)
7. [Pseudocode -- PMO CLI Engine](#7-pseudocode--pmo-cli-engine)
8. [Pseudocode -- PMO Event Routing Engine](#8-pseudocode--pmo-event-routing-engine)
9. [Claw <-> Viper Boundary Architecture](#9-claw--viper-boundary-architecture)
10. [Risk Register](#10-risk-register)
11. [Interface Summary](#11-interface-summary)
12. [Technology Choices](#12-technology-choices)

---

## 1. System Architecture Overview

```
+---------------------------------------------------------------+
|                         CLAW STUDIO                            |
+-------------------+--------------------+------------------------+
|     Planner       |        TDD         |   (Future Seats)       |
|   (jarvis-planner)|   (jarvis-tdd)     |  Architect/Sec/...      |
+--------+----------+--------+----------+------------------------+
|                      [Handoff Chain]                           |
+--------------------------------------------------------------------+
|                    GOVERNANCE LAYER (foundational)               |
|   +------------------+-------------------+--------------------+   |
|   |  CLI (governance)|  Routing          |  Control           |   |
|   |  Category A/B/C  |  (F5.x)           |  (F6.x)            |   |
|   +------------------+-------------------+--------------------+   |
|   +------------------------------------------------------------+   |
|   |  Governance UI (port 8000, /pmo/* routes)                  |   |
|   +------------------------------------------------------------+   |
+--------------------------------------------------------------------+
                         |    ^                                    |
                  [PMO Smart Agent]                                |
                         |    ^                                    |
+--------------------------------------------------------------------+
|                    VIPER OPERATING SURFACE                       |
+---------------+---------------------------+------------------------+---------+
| Grid Escape   |   Execution results       |   Event Routing        |         |
|   Engine       |   (task lifecycle)         |      Engine            |         |
+---------------+---------------------------+------------------------+---------+
```

**Foundational vs V1.8 slice:** The `governance/` layer is foundational PMO infrastructure. V1.8 is the first bounded proof slice. Code-level interfaces do not encode false version ownership.

### Component Description

| Component | Responsibility | Delivery Artifact |
|-----------|---------------|-------------------|
| **Grid Escape Engine** | Maze navigation game, CLI interface, completion detection | `games/grid_escape/` |
| **Governance CLI** | Category A (governance/record), B (execution/dispatch), C (observation) | `governance/cli/` |
| **Governance Routing** | Intake, route, resolve events with ownership ambiguity | `governance/routing/` |
| **Governance Control** | Task lifecycle, execution orchestration, result return | `governance/control/` |
| **Governance UI** | Visibility, approvals, oversight (port 8000) | `governance/ui/` |
| **Planner Seat** *(V1.8 instantiated)* | Decompose user stories into task plans | OpenClaw agent + skill spec |
| **TDD Seat** *(V1.8 instantiated)* | Failing-test-first -> minimal passing code | OpenClaw agent + skill spec |
| **5 Roles** *(V1.9 targets, documented only)* | Architect, CodeReviewer, Security, Docs, DBExpert | Skill spec stubs only |

### Data Flow -- Grid Escape (Agent Play)

```
Agent (Jarvis)
    |
    | echo -e "look\nmove east\n..." | python grid_escape.py --grid ge-001
    |
Grid Escape Engine (grid_escape.py)
    |
    |---- parse command
    |---- update grid state (agent position, step count)
    |---- detect completion (agent on EXIT?)
    |
    |---- look --------------------------> Agent (ASCII grid)
    |---- move --------------------------> Agent (updated grid or BLOCKED)
    |---- status -------------------------> Agent (step/state output)
    |---- ESCAPED line (batch mode) ------> Agent (completion signal)
    v
Session end
```

### Data Flow -- PMO Event Routing

```
Event occurs (ownership unclear)
    |
    | pmo route-event <event_json>
    v
Event Routing Engine
    |
    |---- INTAKE ------ log event, capture timestamp + context
    |---- DETERMINE ---- rule lookup -> destination (Agent/PMO/Nova)
    |---- ROUTE -------- forward to destination
    |---- RESOLVE ------ receive resolution result
    |---- RELAY -------- return result to initiator
    v
Governance Event Log (full trace)
```

---


## 2. Version Control Strategy

**Branch model:**
```
stable master
    |---- release/v1.8-dev   < V1.8 integration branch (forked from stable master)
            |---- feature/grid-escape-engine
            |---- feature/governance-cli
            |---- feature/governance-routing
            |---- feature/governance-control
            |---- feature/governance-ui
            |---- (merged) -> release/v1.8-dev -> master (after V1.8 closure)
```

**Rules:**
- master = stable release baseline. Never merged into until a version is fully accepted.
- 
elease/v1.8-dev = V1.8 integration branch, branched from stable master at V1.8 start.
- Feature branches are cut from and merged back into 
elease/v1.8-dev.
- 
elease/v1.8-dev merges to master only after V1.8 closes with Nova + Alex sign-off.
- The shared drive \\192.168.31.124\Nova-Jarvis-Shared\working\gov_langgraph\V1.8\ holds **governance documents only**. All code lives in Git.

---

## 3. Code Directory Structure (Git Repository -- release/v1.8-dev)

**Naming convention:** `governance/` as parent for all PMO/governance code. Short semantic peers (`cli/`, `routing/`, `control/`, `ui/`) under one roof. Matches architectural grammar of `games/`.

**Agent seats** (Planner, TDD) live in OpenClaw agent config (`C:\Users\John\.openclaw\agents\jarvis-planner/`, `jarvis-tdd/`), not in this repo. Their skill specs are in the governance docs.

```
repository root/
|---- games/                          # Standalone game products (V1.8: Grid Escape only)
|   |---- grid_escape/               # Grid Escape game package
|       |---- __init__.py
|       |---- engine.py              # Core grid model, movement, pathfinding, completion
|       |---- cli.py                # CLI interface, batch mode
|       |---- grids.py              # Grid generation + ge-001/002/003 starter grids
|       |---- scoring.py            # BFS optimal path + tier assignment
|       |---- main.py               # Entry: python games/grid_escape.py --grid <id>
|       |---- tests/
|           |---- test_pathfinding.py
|           |---- test_movement.py
|           |---- test_completion.py
|           |---- test_scoring.py
|
|---- governance/                    # PMO governance layer (foundational capability)
|   |---- cli/                       # Governance / record commands (F3.2.x)
|   |   |---- __init__.py
|   |   |---- cli.py
|   |   |---- commands/
|   |   |   |---- create_work_item.py    # record-only
|   |   |   |---- submit_artifact.py      # record-only
|   |   |   |---- request_transition.py  # record-only
|   |   |   |---- record_validation.py   # record-only
|   |   |   |---- signal_blocker.py       # record-only
|   |   |   |---- package_delivery.py    # record-only
|   |   |   |---- status.py               # observation
|   |   |---- models.py
|   |   |---- store.py
|   |   |---- output.py
|   |
|   |---- routing/                   # Event routing (F5.x)
|   |   |---- __init__.py
|   |   |---- engine.py             # intake -> determine -> route -> resolve -> relay
|   |   |---- rules.py              # Rule table: event type -> destination
|   |   |---- intake.py
|   |   |---- relay.py
|   |   |---- tests/
|   |       |---- test_rules.py
|   |       |---- test_routing_flow.py
|   |
|   |---- control/                  # Execution orchestration (F6.x)
|   |   |---- __init__.py
|   |   |---- control.py            # launch/pause/resume/terminate/invoke + lifecycle
|   |   |---- authority.py          # V1.8 scope gating, FORBIDDEN returns
|   |   |---- task_store.py         # Task lifecycle state (separate from work-item state)
|   |   |---- result.py             # Result payload model (F6.2.x)
|   |   |---- tests/
|   |       |---- test_control_loop.py
|   |       |---- test_lifecycle.py
|   |       |---- test_result_return.py
|   |
|   |---- ui/                       # Thin governance UI (F4.x) — optional, port 8000
|       |---- __init__.py
|       |---- main.py
|       |---- routes/
|           |---- workflow.py
|           |---- queue.py
|           |---- artifacts.py
|           |---- approvals.py
|
|---- handoff/                      # Claw <-> Viper handoff (F8.x)
|   |---- claw_to_viper.py
|   |---- viper_response.py
|   |---- evidence/
|       |---- handoff_001.md
|       |---- return_receipt_001.md
|
|---- evidence/                     # Runtime evidence from execution
    |---- gameplay/
    |   |---- ge-001_completion.log
    |   |---- ge-002_completion.log
    |---- governance/
    |   |---- pmo_cli_trace.log
    |   |---- routing_proof_case.log
    |   |---- planner_trace.md
    |   |---- tdd_trace.md
    |   |---- handoff_chain_trace.md
```

---

## 3.1 Governance State vs Execution State (Explicit Separation)

**R5 requirement:** These two concerns must not be conflated.

| Concept | Type | Lives in | Examples |
|---------|------|----------|----------|
| **Work Item** | Governance state | `governance/cli/store.py` | WI-001, stage=IN_REVIEW, artifact refs |
| **Task** | Execution state | `governance/control/task_store.py` | TASK-xxxx, status=RUNNING, executor=viper |
| **Result** | Execution output | `governance/control/result.py` | task result, failure reason, output ref |

**A work item is NOT a task:**
- A work item tracks delivery governance (stage, artifacts, blockers)
- A task tracks a bounded execution (lifecycle, executor, result)
- Stage transitions on a work item do NOT automatically create or complete tasks
- Task completion does NOT automatically advance work-item stage

**Command categories (R1):**

| Category | Effect | Examples |
|----------|--------|----------|
| **Governance / record** | Writes PMO governance state only | create-work-item, submit-artifact, record-validation, signal-blocker, request-transition, package-delivery |
| **Execution / dispatch** | Triggers real bounded backend action, returns result | launch-subagent, invoke-command, pause-task, resume-task, terminate-task |
| **Observation / result** | Returns current state or stored result | status, event-log, inspect-task, get-task-result |

**Execution command rule (R2):** Execution commands MUST either:
1. Trigger a real bounded backend action, OR
2. Fail explicitly with error + reason

Silent `{"ok": true}` without tangible action is NOT acceptable for execution-labeled commands.

**Result payload (R4 — minimum required fields):**
```
- task_id, task_type, requested_by, executor
- input_payload
- status: QUEUED | DISPATCHED | RUNNING | WAITING | SUCCEEDED | FAILED | CANCELED | TIMED_OUT
- created_at, started_at, updated_at, completed_at
- result_summary, output_ref (or output_payload), error, logs_ref
```
---

## 4. Governance Documents (Shared Drive -- governance-only baseline)
```
\\192.168.31.124\Nova-Jarvis-Shared\working\gov_langgraph\V1.8\
|---- docs/                          # Version-controlled governance documents
|   |---- V1_8_FOUNDATION_DOCUMENT.md
|   |---- V1_8_SCOPE.md
|   |---- V1_8_SPEC.md
|   |---- V1_8_EXECUTION_PLAN.md
|   |---- V1_8_ARCHITECTURAL_DESIGN.md  < this file
|   |---- V1_8_PMO_CLI_REFERENCE.md
|   |---- V1_8_AGENT_ROLES.md
|   |---- V1_8_DELIVERY_PACKAGE.md
|
|---- DELIVERABLES/                  # Final packaged deliverables (zips produced from Git repo)
    |---- V1.8-Grid-Escape-v1.0.zip
    |---- V1.8-PMO-CLI-v1.0.zip
    |---- V1.8-Routing-Engine-v1.0.zip
    |---- V1.8-Agent-Seats.zip
    |---- V1.8-Governance-UI-v1.0.zip
    |---- V1.8-Evidence-Package.zip
    |---- V1.8-Closure-Record.md
```
**Separation principle:** Git repository = source of truth for code. Shared drive = source of truth for governance documents. Games output lives in games/ in the Git repository, not in the governance directory.

---

## 5. Game Platform -- Open Issue for M1-R1 Resolution

**Status:** OPEN -- must be resolved before M1-R1 can close.

**Problem:** Grid Escape (and future games) are standalone products. The Agent (Jarvis) needs a known, accessible location to discover and invoke games. No Game Platform currently exists.

**Options for M1-R1 sprint planning:**

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A. Games registry (JSON manifest)** | games/registry.json listing available games + invocation paths | Simple, version-controlled | Static, manual update per game |
| **B. Games API endpoint** | HTTP endpoint listing and serving games | Agent-queryable at runtime | Infrastructure required |
| **C. Shared path convention** | ./games/ on a known shared path the Agent checks | Zero infrastructure | Requires fixed path; no runtime discovery |

**Minimum V1.8 requirement:** Agent must be able to locate and invoke Grid Escape via a defined path or registry without per-session manual setup.

**Decision owner:** Nova or Alex -- to decide platform approach during M1-R1 sprint planning.

## 6. Pseudocode -- Grid Escape Engine

### 6.1 Grid Model

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple

class CellType(Enum):
    WALL = "#"
    OPEN = "."
    START = "S"
    EXIT = "E"
    AGENT = "A"

@dataclass
class Grid:
    width: int
    height: int
    cells: List[List[CellType]]  # [row][col]
    start: Tuple[int, int]
    exit: Tuple[int, int]
    seed: int
    optimal_steps: int = 0       # BFS-computed

    def cell_at(self, row: int, col: int) -> CellType:
        if not (0 <= row < self.height and 0 <= col < self.width):
            return CellType.WALL
        return self.cells[row][col]

    def is_walkable(self, row: int, col: int) -> bool:
        c = self.cell_at(row, col)
        return c in (CellType.OPEN, CellType.START, CellType.EXIT)

@dataclass
class GameState:
    grid: Grid
    agent_pos: Tuple[int, int]
    step_count: int = 0
    state: str = "playing"  # "playing" | "escaped"
    visited: List[Tuple[int, int]] = field(default_factory=list)

    def move(self, direction: str) -> Tuple[bool, str]:
        delta = {"north": (-1, 0), "n": (-1, 0),
                 "south": (1, 0),  "s": (1, 0),
                 "east":  (0, 1),  "e": (0, 1),
                 "west":  (0, -1), "w": (0, -1)}.get(direction.lower())

        if delta is None:
            return False, "INVALID DIRECTION"

        new_row = self.agent_pos[0] + delta[0]
        new_col = self.agent_pos[1] + delta[1]

        if not self.grid.is_walkable(new_row, new_col):
            return False, "BLOCKED"

        self.visited.append(self.agent_pos)
        self.agent_pos = (new_row, new_col)
        self.step_count += 1

        if self.agent_pos == self.grid.exit:
            self.state = "escaped"
            return True, f"ESCAPED|{self.step_count}|{self.grid.seed}|{timestamp()}"

        return True, self.render()

    def render(self) -> str:
        lines = []
        for r in range(self.grid.height):
            row_str = "".join(
                "A" if (r, c) == self.agent_pos else self.grid.cell_at(r, c).value
                for c in range(self.grid.width)
            )
            lines.append(row_str)
        return "\n".join(lines) + f"\nStep: {self.step_count} | State: {self.state}"

    def restart(self):
        self.agent_pos = self.grid.start
        self.step_count = 0
        self.state = "playing"
        self.visited.clear()
```

### 6.2 BFS Optimal Path

```python
def compute_optimal_path(grid: Grid) -> int:
    queue = [(grid.start[0], grid.start[1], 0)]
    visited = {grid.start}
    directions = [(-1, 0), (1, 0), (0, 1), (0, -1)]

    while queue:
        r, c, steps = queue.pop(0)
        if (r, c) == grid.exit:
            return steps
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in visited and grid.is_walkable(nr, nc):
                visited.add((nr, nc))
                queue.append((nr, nc, steps + 1))
    return -1

def assign_tier(steps: int, optimal: int) -> str:
    diff = steps - optimal
    if diff <= 0:   return "PERFECT"
    if diff <= 2:  return "EXCELLENT"
    if diff <= 5:  return "GOOD"
    if diff <= 10: return "COMPLETED"
    return "OVERMOVED"
```

### 6.3 CLI Entry Point

```python
import sys

GRIDS = {}  # grid_id -> Grid

def main():
    args = sys.argv[1:]
    grid_id = "ge-001"
    batch_mode = not sys.stdin.isatty()

    i = 0
    while i < len(args):
        if args[i] == "--grid" and i+1 < len(args):
            grid_id = args[i+1]; i += 2
        else:
            i += 1

    state = GameState(grid=GRIDS[grid_id], agent_pos=GRIDS[grid_id].start)

    if batch_mode:
        for line in sys.stdin.read().splitlines():
            line = line.strip()
            if not line: continue
            parts = line.split(maxsplit=1)
            cmd, arg = parts[0], parts[1] if len(parts) > 1 else None
            print(handle_command(state, cmd, arg))
    else:
        print("==== GRID ESCAPE ====")
        print(f"Grid: {grid_id} | Optimal: {state.grid.optimal_steps}")
        print(state.render())
        while state.state == "playing":
            cmd = input("> ").strip()
            if not cmd: continue
            parts = cmd.split(maxsplit=1)
            cmd_name, arg = parts[0], parts[1] if len(parts) > 1 else None
            print(handle_command(state, cmd_name, arg))

def handle_command(state: GameState, cmd: str, arg):
    if cmd == "look":    return state.render()
    if cmd == "move":     _, out = state.move(arg or ""); return out
    if cmd == "status":   return f"Step: {state.step_count} | State: {state.state}"
    if cmd == "restart":  state.restart(); return state.render()
    if cmd == "quit":     return f"Quit. Steps: {state.step_count}"
    return "UNKNOWN COMMAND"
```

---

## 7. Pseudocode -- PMO CLI Engine

### 7.1 Main Entry

```python
import sys
import json

COMMAND_MAP = {
    "create-work-item":   create_work_item,
    "submit-artifact":    submit_artifact,
    "request-transition": request_transition,
    "record-validation":  record_validation,
    "signal-blocker":     signal_blocker,
    "package-delivery":   package_delivery,
    "status":             status,
}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"})); sys.exit(1)
    cmd_name, args = sys.argv[1], sys.argv[2:]
    handler = COMMAND_MAP.get(cmd_name)
    if not handler:
        print(json.dumps({"error": f"Unknown command '{cmd_name}'"})); sys.exit(1)
    print(json.dumps(handler(args)))

if __name__ == "__main__":
    main()
```

### 7.2 Representative Handler -- create-work-item

```python
import uuid
from datetime import datetime

def create_work_item(args: list) -> dict:
    if len(args) < 1:
        return {"error": "EXPECTED: pmo create-work-item <name>"}
    item = {
        "id": f"WI-{str(uuid.uuid4())[:8]}",
        "name": args[0],
        "stage": "BACKLOG",
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }
    save_item(item)
    return {"ok": True, "item_id": item["id"], "name": item["name"], "stage": item["stage"]}
```

---

## 8. Pseudocode -- PMO Event Routing Engine

### 8.1 Routing Engine

```python
import json
import uuid
from datetime import datetime

ROUTING_RULES = {
    "UNKNOWN_TOOL":          {"destination": "most_recent_agent"},
    "BLOCKER_ESCALATION":    {"destination": "PMO"},
    "CLARIFICATION_NEEDED":  {"destination": "Nova"},
    "AGENT_CAPACITY_WARNING":{"destination": "PMO"},
}

class RoutingEvent:
    def __init__(self, event_json: str):
        self.raw = json.loads(event_json)
        self.event_type = self.raw.get("type")
        self.context = self.raw.get("context", {})
        self.initiator = self.raw.get("initiator")
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()

    def determine_destination(self) -> str:
        rule = ROUTING_RULES.get(self.event_type)
        return rule["destination"] if rule else "PMO"

def route_event(event_json: str) -> dict:
    event = RoutingEvent(event_json)
    intake = {"event_id": event.id, "type": event.event_type, "at": event.timestamp}
    destination = event.determine_destination()
    route_result = {"status": "forwarded", "destination": destination, "at": event.timestamp}
    resolution = {"event_id": event.id, "status": "resolved", "by": destination}
    relay_result(event.initiator, resolution)
    return {"event_id": event.id, "intake": intake, "destination": destination,
            "route": route_result, "resolution": resolution}

def relay_result(initiator, resolution):
    pass  # V1.8: relay back to initiating Agent
```

---

## 9. Claw <-> Viper Boundary Architecture

### 9.1 Handoff Package Structure

```json
{
  "handoff_id": "H001",
  "from": "Claw Studio",
  "to": "Viper",
  "timestamp": "2026-04-14T00:00:00Z",
  "game_definition": {
    "name": "Grid Escape",
    "type": "CLI-native maze navigation",
    "objective": "Agent navigates from S to E in NxM grid",
    "completion": "ESCAPED|<steps>|<grid_id>|<timestamp>",
    "grids": ["ge-001 (7x7)", "ge-002 (8x8)", "ge-003 (10x10)"],
    "cli_commands": ["look", "move <dir>", "status", "restart", "quit"]
  },
  "engineering_constraints": [
    "Must be completable by a CLI-driven Agent (no visual UI)",
    "Grid generation must be deterministic (seed -> identical grid)",
    "Completion detection must fire unambiguously",
    "Step count must be accurate to +/-0",
    "Batch mode STDIN/STDOUT required for agent execution"
  ],
  "success_criteria": [
    "Grid Escape engine runs without error on ge-001",
    "Agent can reach exit from start using CLI commands",
    "ESCAPED line fires when agent reaches exit tile",
    "Step count matches actual moves taken"
  ],
  "participant": "Jarvis"
}
```

### 9.2 Return Receipt Structure

```json
{
  "return_receipt_id": "RR001",
  "handoff_id": "H001",
  "from": "Viper",
  "to": "Claw Studio",
  "timestamp": "2026-04-14T00:00:00Z",
  "status": "completed",
  "output": {
    "delivered": ["grid_escape.py", "ge-001.grid", "ge-002.grid", "ge-003.grid"],
    "validation": "All grids verified solvable via BFS",
    "cli_tests_passed": true
  },
  "evidence_ref": "handoff/evidence/return_receipt_001.md"
}
```

---

## 10. Risk Register

| # | Risk | L | I | Mitigation | Owner |
|---|------|---|---|------------|-------|
| R1 | Agent cannot complete Grid Escape | M | H | Pre-build verified-solvable grids with known optimal paths | Jarvis |
| R2 | PMO CLI is scaffolding only -- no live system behind it | M | H | Smoke-test against live PMO in M2-R2; JSON store as fallback | Jarvis |
| R3 | Event Routing proof case cannot be triggered organically | M | M | Synthetic trigger injection in M3-R1 | Jarvis |
| R4 | Claw <-> Viper handoff stalls -- Viper side unavailable | M | H | Identify Viper contact in M4-R3 planning; doc-only fallback | Nova |
| R5 | Governance UI becomes required dependency | L | H | Verify CLI works with UI offline in M4-R2 | Nova |
| R6 | Planner -> TDD handoff breaks -- ambiguous skill contracts | M | M | Write explicit input/output contracts in skill specs | Jarvis |
| R7 | Optimal path BFS is wrong -- scoring tiers fail | L | H | BFS-verify each grid before shipping | Jarvis |
| R8 | Agent completion evidence not accepted as proof | L | M | Capture batch output verbatim with seed+timestamp; Nova signs off | Nova |
| R9 | "Architectural design" balloons into full design doc project | M | M | Scope to Grid Escape + PMO routing only; full arch is V1.9 | Alex |
| R10 | Too many skill seats instantiated -- maintenance burden | L | L | Only Planner + TDD instantiated in V1.8; 5 others are V1.9 | Jarvis |

---

## 11. Interface Summary

### 11.1 Grid Escape CLI

```bash
python games/grid_escape.py --grid <ge-001|ge-002|ge-003> [--seed <int>]

Commands: look | move <n|s|e|w> | status | restart | quit
Batch completion: ESCAPED|<steps>|<grid_id>|<timestamp>
```

### 11.2 Governance CLI -- Category A: Governance / Record Commands

These write PMO governance state only. They record intent or facts; they do not execute work.

```bash
governance create-work-item <name>          # Creates WI-xxx, stage=BACKLOG
governance submit-artifact <item_id> <path>  # Attaches artifact ref to work item
governance request-transition <item_id> <stage>  # Requests stage change (BACKLOG|IN_PROGRESS|IN_REVIEW|APPROVED|DELIVERED)
governance record-validation <item_id> <pass|fail>  # Records validation result
governance signal-blocker <item_id> <desc>   # Records blocker with description
governance package-delivery <item_id>       # Creates delivery package record
```

### 11.3 Governance CLI -- Category B: Execution / Dispatch Commands

These trigger real bounded backend actions. Result return is REQUIRED (R4).
Execution commands MUST cause tangible action or fail explicitly.

```bash
governance launch-subagent <task_id> <agent_type>  # Dispatches task -> QUEUED -> DISPATCHED -> RUNNING
governance invoke-command <task_id> <command>        # Executes approved command, returns result
governance pause-task <task_id>                     # -> WAITING
governance resume-task <task_id>                    # WAITING -> RUNNING
governance terminate-task <task_id>                # -> CANCELED
```

**Result payload returned:**
```json
{
  "task_id": "TASK-xxx",
  "status": "SUCCEEDED | FAILED | CANCELED | TIMED_OUT",
  "result_summary": "...",
  "output_ref": "...",
  "error": "...",
  "created_at": "...",
  "started_at": "...",
  "completed_at": "...",
  "logs_ref": "..."
}
```

### 11.4 Governance CLI -- Category C: Observation / Result Commands

These return current state or stored results. No side effects.

```bash
governance status [item_id]                  # Work-item state or list
governance route-event <event_json>           # Route event -> destination
governance event-log [event_id]              # Event log or single event
governance inspect-task <task_id>            # Full task lifecycle state
governance get-task-result <task_id>         # Stored result payload
```

### 11.5 Task Lifecycle States (R3)

Every executable task MUST transition through these states:

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

**Note:** RUNNING / PAUSED / TERMINATED alone are NOT sufficient for serious orchestration.

### 11.6 Governance UI

```bash
uvicorn governance.ui.main:app --port 8000
# Routes: /pmo/health, /pmo/workflow, /pmo/queue, /pmo/artifacts, /pmo/approvals, /pmo/events, /pmo/tasks
# Optional -- CLI works if UI is offline
```

**Foundational vs V1.8 slice (R7):** UI routes are foundational PMO capability. V1.8 is the first proof slice. Routes do not encode version ownership at the code level.

---

## 12. Technology Choices

| Component | Language | Rationale |
|-----------|----------|-----------|
| Grid Escape Engine | Python 3 | CLI-native, stdio, simple deployment |
| PMO CLI | Python 3 | Aligns with V1.7 PMO stack |
| PMO Event Routing | Python 3 | Deterministic rule engine; no inference needed |
| PMO Control | Python 3 | Bounded command surface |
| Agent Seats | Markdown skill specs + OpenClaw | Leverage existing Claw Studio framework |
| Governance UI | FastAPI/uvicorn | Already running on port 8000 in V1.7 |

**Runtime Reality Note:** Data flow diagrams represent architecture intent, not proven runtime truth. Relay paths (e.g., relayResult() in SS6) are stubs in V1.8 -- synchronous resolution is assumed but not yet exercised. Runtime proof is required at sprint exit gates via actual trace evidence, not diagram alignment.

---

*Scoped to Grid Escape + PMO CLI/Routing proof. Full system architecture for Claw Studio + VIPER belongs to V1.9.*