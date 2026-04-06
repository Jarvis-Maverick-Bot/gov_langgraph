# gov_langgraph — V1 Implementation

**Version:** V1 Phase 1 + Phase 2 (Week 1–2)
**Status:** Harness layer complete. Ready for Week 3 (LangGraph Engine).

---

## What is this?

`gov_langgraph` is the governance graph engine for THE ONE enterprise governance layer.

It provides:
- **Platform Core** — objects, authority rules, state machine for a BA→SA→DEV→QA pipeline
- **Harness Layer** — persistence, checkpointing, event journaling, evidence storage
- **PMO CLI** — command-line visibility into project/task state
- **OpenClaw Integration** — tool functions + coordinator for Telegram-based operation

---

## Quick Start

```bash
cd D:\Projects\gov_langgraph
```

### Run the E2E test

```bash
python E2E_TEST.py
```

### Use the PMO CLI

```bash
python -m gov_langgraph.pmo_smart_agent.cli list <project_id>
python -m gov_langgraph.pmo_smart_agent.cli pipeline <project_id>
python -m gov_langgraph.pmo_smart_agent.cli status <task_id>
python -m gov_langgraph.pmo_smart_agent.cli events <task_id> --project <project_id>
python -m gov_langgraph.pmo_smart_agent.cli checkpoint <task_id>
```

### Use the OpenClaw tools (Python)

```python
from gov_langgraph.openclaw_integration import Coordinator, init_harness
from gov_langgraph.harness import HarnessConfig

HarnessConfig().ensure_dirs()
c = Coordinator()

# Create project
r = c.handle('create_project', {
    'project_name': 'My Project',
    'project_goal': 'Build something',
    'actor': 'alex',
})

# Create task
r = c.handle('create_task', {
    'task_title': 'My Task',
    'project_id': r['data']['project_id'],
    'current_owner': 'viper_ba',
    'actor': 'alex',
})

# Advance stage
r = c.handle('advance_stage', {
    'task_id': r['data']['task_id'],
    'target_stage': 'SA',
    'actor': 'viper_ba',
})
```

---

## Project Structure

```
gov_langgraph/
├── platform_model/          # Layer 3: Platform Core
│   ├── __init__.py         # Public API exports
│   ├── objects.py          # Project, WorkItem, TaskState, Workflow, Handoff, Gate, Event
│   ├── authority.py        # Role-based authority (Tier 1/2/3)
│   ├── state_machine.py    # Stage transition validation
│   ├── exceptions.py       # Exception hierarchy
│   └── workflows.py        # V1 Pipeline definition (single source of truth)
│
├── harness/                # Layer 2 + Layer 3: Persistence
│   ├── config.py          # HarnessConfig — paths and settings
│   ├── state_store.py      # JSON file I/O for Project/WorkItem/TaskState/Gate/Handoff
│   ├── checkpointer.py     # Before/after checkpointing + restore
│   ├── events.py          # Append-only event journal
│   └── evidence.py        # Evidence reference storage
│
├── pmo_smart_agent/        # PMO visibility layer
│   ├── cli.py             # 6 commands: status, list, pipeline, events, checkpoint, evidence
│   └── dashboard.py       # get_pipeline_view() + render_pipeline_text()
│
└── openclaw_integration/   # OpenClaw tool layer
    ├── tools.py           # 8 tool functions
    └── coordinator.py     # Routes Telegram → tool, formats response
```

---

## V1 Pipeline

**Stages:** `BA → SA → DEV → QA`

**Transitions:**
- `BA` → `SA`
- `SA` → `DEV`
- `DEV` → `QA`

**Roles:**
- `alex` — final escalation (TIER 1)
- `nova` — chief auditing officer (TIER 2)
- `jarvis` — coordinator (TIER 2)
- `maverick` — PMO (TIER 3 management)
- `viper_ba`, `viper_sa`, `viper_dev`, `viper_qa` — stage owners (TIER 3)

---

## Week 2 Deliverables (Harness Layer)

| Day | Module | Status |
|-----|--------|--------|
| Day 1 | Config + StateStore + Checkpointer + Events + Evidence | ✅ Nova approved |
| Day 2 | StateMachine wired with Checkpointer + EventJournal | ✅ Nova approved |
| Day 3 | PMO CLI + Dashboard | ✅ Nova approved |
| Day 4 | OpenClaw Integration (Tools + Coordinator) | ✅ Nova approved |
| Day 5 | End-to-End Test + README | ✅ Complete |

---

## Key Design Decisions

- **Harness = persistence only** — no governance semantics
- **Events are append-only** — never modify or delete
- **Dependency injection** — harness instances passed in, not globals
- **Single workflow source** — `platform_model/workflows.py` defines V1 pipeline
- **JSONL format** — one record per line, no indent, for event/evidence logs
- **Checkpoints are sequential, not atomic** — discipline required

---

## Data Storage

| Layer | Storage |
|-------|---------|
| Projects, WorkItems, TaskStates, Gates, Handoffs | `~/.gov_langgraph/state/*.json` |
| Checkpoints | `~/.gov_langgraph/checkpoints/*.json` |
| Event journal | `~/.gov_langgraph/events/*.jsonl` |
| Evidence | `~/.gov_langgraph/state/evidence/*.jsonl` |

---

## Running on Windows

```powershell
cd D:\Projects\gov_langgraph
python E2E_TEST.py
```

SSH is configured for GitHub push (no credential popups).

---

## Next: Week 3

**LangGraph Engine** — GovernanceState, nodes (maverick, viper_*), edges, pipeline compilation.
