# LangGraph Integration Plan — V1

**Author:** Jarvis
**Date:** 2026-04-09
**Status:** V1 ARCHIVE — part of v1.0.0 freeze set

---

## Purpose

This document describes how LangGraph is integrated into the PMO Smart Agent V1 runtime: what role it plays, how it fits relative to Harness and the PMO shell, and what was deferred beyond V1.

---

## LangGraph Role in V1

LangGraph is the **pipeline execution engine** — it drives workitems through the BA → SA → DEV → QA stage sequence.

It is not the API surface (PMO shell), not the state store (Harness), and not the governance rules (Platform Model). It is the sequencing and routing layer.

---

## Layer Placement

```
Layer 1: PMO Shell         — External interface (HTTP API)
Layer 2: Harness            — State + events + checkpoints
Layer 3: Platform Model     — Governance rules and objects
Layer 4: LangGraph Engine   — Pipeline execution ← THIS
```

---

## Core Components

### Graph (`langgraph_engine/graph.py`)
- `build_graph()` constructs the LangGraph directed graph
- Nodes: `maverick`, `viper_ba`, `viper_sa`, `viper_dev`, `viper_qa`
- Edges: INTAKE → BA → SA → DEV → QA → DONE
- Conditional edges for terminal state detection

### Pipeline (`langgraph_engine/pipeline.py`)
- `compile()` — builds the graph once, returns executable pipeline
- `run_workitem(task_id)` — executes a workitem through the graph
- `get_pipeline()` — returns the compiled graph instance

### AgentExecutor (`langgraph_engine/executor.py`)
Enforces governance at 3 layers:

1. **Pre-execution check**: validates current stage and actor authority before agent runs
2. **Action-level enforcement**: validates each individual action against authority matrix
3. **Completion check**: validates handoff document completeness before stage advance

If any layer fails → `HaltNode` triggered → workitem halts → Alex notified.

### Role-Shaped Agents (`langgraph_engine/agent.py`)
Factory functions that produce stage-specific agents:

| Factory | Role | Responsibility |
|---------|------|----------------|
| `make_viper_ba()` | Business Analyst | Requirements framing, spec drafting |
| `make_viper_sa()` | Systems Analyst | Technical analysis, architecture |
| `make_viper_dev()` | Developer | Implementation |
| `make_viper_qa()` | QA | Verification |

Each agent is a `RoleShapedAgent` instance with a `Soul`-guided prompt and a governance boundary. They run within the LangGraph node context.

### Runtime Context (`langgraph_engine/runtime.py`)
Singleton runtime context holding:
- `HarnessConfig` reference
- Active `Checkpointer`
- Stage-specific context

Initialised once at startup via `init_runtime()`.

---

## LangGraph → Harness Boundary

LangGraph **reads from and writes to** Harness for state:

```
LangGraph run_workitem()
  → Checkpointer.load(task_id, stage)
  → StateStore.load_workitem(task_id)
  → Execute stage node
  → StateStore.save_workitem(updated)
  → Checkpointer.save(task_id, new_stage)
  → EventJournal.append(event)
  → EvidenceStore.put(evidence)
```

Harness is the **state substrate** for LangGraph. LangGraph does not hold its own state — it uses Harness APIs at each step.

---

## LangGraph → Platform Model Boundary

LangGraph **imports and enforces** Platform Model rules:

```
Platform Model (Layer 3):
  - Tier enum, Action enums, check_authority()
  - StateMachine (stage transition rules)
  - HandoffDocument (10-field schema)
  - Exception hierarchy

LangGraph Engine (Layer 4):
  - AgentExecutor calls check_authority() before each action
  - HandoffDocument validated before stage advance
  - HaltNode triggered on StateMachine violations
  - Typed exceptions from platform_model raised by LangGraph nodes
```

Platform Model defines **what** is valid. LangGraph enforces **when** it is checked.

---

## PMO Shell → LangGraph Boundary

The PMO shell does NOT call LangGraph directly in V1.

```
PMO Shell (tools.py):
  → Harness API (workitem/taskstate)
  → Returns result to caller

LangGraph is NOT in the V1 external API path.
```

LangGraph is **internal pipeline infrastructure**. It is invoked when a workitem needs to advance through stages — triggered by the `run_workitem()` call in the pipeline module.

**In V1:** The full pipeline is not wired to external triggers. The PMO shell exposes 3 functions (kickoff, status, gate) that maintain workitem state but do not automatically advance workitems through the LangGraph pipeline. This is a V1 simplification.

---

## What V1 Does NOT Include

### Not wired: External pipeline trigger
External tools (kickoff/status/gate) do not automatically invoke `run_workitem()`. Pipeline advance requires a separate internal call.

**Deferred:** Full LangGraph ↔ PMO shell integration with automatic stage advance on gate approval.

### Not wired: Viper agent execution
`make_viper_ba/sa/dev/qa()` agent factories exist but the actual agent execution (prompting, tool calls, response parsing) is not fully implemented in V1. Agents are defined but the runtime call path is stubbed.

**Deferred:** Full Viper agent runtime integration.

### Not wired: LangGraph checkpoint/resume
LangGraph's native checkpointing is not connected to Harness `Checkpointer`. Resumability across process restarts is handled by Harness state files, not LangGraph checkpoint state.

**Deferred:** Unified checkpoint model across LangGraph and Harness.

### Not wired: Maverick advisory node
The `maverick` node in the graph is defined but not wired to the advisory team (Lyra, Meridian, Echo, Solon, Atlas).

**Deferred:** Maverick advisory workflow integration.

---

## V1 LangGraph Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Stage nodes: BA → SA → DEV → QA | Reflects Viper external delivery pipeline |
| HaltNode on authority failure | Governance-first: stop rather than proceed wrong |
| Role-shaped agent factories | Reusable pattern; avoids per-agent duplication |
| `run_workitem()` as entry point | Single entry for pipeline execution |
| Pipeline compiled once at startup | `compile()` called once, reused across workitems |

---

## Archive Reference

Source in repo: `D:\Projects\gov_langgraph\gov_langgraph\langgraph_engine\`

Key files:
- `graph.py` — LangGraph construction
- `pipeline.py` — execution entry point
- `executor.py` — 3-layer enforcement
- `agent.py` — RoleShapedAgent factories
- `runtime.py` — RuntimeContext singleton
- `nodes/` — stage node implementations
