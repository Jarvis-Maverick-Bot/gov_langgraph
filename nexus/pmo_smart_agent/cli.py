"""
pmo_smart_agent.cli — PMO Smart Agent Command Line Interface

Operator-facing management/visibility/control surface for V1.
Reads backed by StateStore (explicit query paths).
Writes go through Platform Core methods.

Usage:
    python -m pmo_smart_agent.cli status <task_id>
    python -m pmo_smart_agent.cli list <project_id>
    python -m pmo_smart_agent.cli events <task_id> [--project <project_id>]
    python -m pmo_smart_agent.cli checkpoint <task_id>
    python -m pmo_smart_agent.cli evidence <task_id> [--project <project_id>]
    python -m pmo_smart_agent.cli pipeline <project_id>
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from nexus.harness import HarnessConfig, StateStore, Checkpointer, EventJournal, EvidenceStore
from nexus.platform_model import Project, WorkItem, TaskState, Workflow, V1_PIPELINE_STAGES


# ---------------------------------------------------------------------------
# Config (singleton for CLI)
# ---------------------------------------------------------------------------

_cfg: HarnessConfig | None = None
_store: StateStore | None = None
_ckpt: Checkpointer | None = None
_journal: EventJournal | None = None
_evstore: EvidenceStore | None = None


def _get_config() -> HarnessConfig:
    global _cfg
    if _cfg is None:
        _cfg = HarnessConfig()
        _cfg.ensure_dirs()
    return _cfg


def _get_store() -> StateStore:
    global _store
    if _store is None:
        _store = StateStore(_get_config().state_dir)
    return _store


def _get_journal() -> EventJournal:
    global _journal
    if _journal is None:
        _journal = EventJournal(_get_config().event_dir)
    return _journal


def _get_evidence() -> EvidenceStore:
    global _evstore
    if _evstore is None:
        _evstore = EvidenceStore(_get_config().state_dir / "evidence")
    return _evstore


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _fmt_workitem(w: WorkItem, store: StateStore) -> str:
    lines = [
        f"  Task:      {w.task_title}",
        f"  ID:        {w.task_id}",
        f"  Stage:     {w.current_stage}",
        f"  Status:    {w.task_status.value}",
        f"  Owner:     {w.current_owner or '(unassigned)'}",
        f"  Priority:  {w.priority}",
    ]
    # Check TaskState for blocker
    try:
        ts = store.load_taskstate(w.task_id)
        if ts.current_blocker:
            lines.append(f"  Blocked:   {ts.current_blocker}")
    except Exception:
        pass
    if w.handoff_target:
        lines.append(f"  Handoff:   {w.handoff_target}")
    return "\n".join(lines)


def _fmt_checkpoint_info(task_id: str, store: StateStore, ckpt: Checkpointer) -> str:
    try:
        ckpt_record = ckpt.get_latest_completed_checkpoint(task_id)
        if ckpt_record is None:
            return f"  No checkpoint found for task '{task_id}'"
        lines = [
            f"  Checkpoint ID: {ckpt_record.checkpoint_id}",
            f"  Stage:         {ckpt_record.from_stage} -> {ckpt_record.to_stage}",
            f"  Actor:         {ckpt_record.actor_role}",
            f"  Completed:     {ckpt_record.completed}",
            f"  Created:       {ckpt_record.created_at.isoformat()}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"  Error loading checkpoint: {e}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_status(task_id: str) -> str:
    """Show current stage, owner, blocker, status for a task."""
    store = _get_store()
    try:
        w = store.load_workitem(task_id)
        return f"Task status for '{w.task_title}':\n{_fmt_workitem(w, store)}"
    except Exception as e:
        return f"Error: {e}"


def cmd_list(project_id: str) -> str:
    """List all workitems for a project."""
    store = _get_store()
    try:
        task_ids = store.list_workitems(project_id=project_id)
        if not task_ids:
            return f"No workitems found for project '{project_id}'"
        lines = [f"Workitems for project '{project_id}':"]
        for tid in task_ids:
            w = store.load_workitem(tid)
            # Check TaskState for blocker
            blocker_str = ""
            try:
                ts = store.load_taskstate(tid)
                if ts.current_blocker:
                    blocker_str = f" [BLOCKED: {ts.current_blocker}]"
            except Exception:
                pass
            lines.append(
                f"  [{w.current_stage}] {w.task_title} "
                f"| {w.task_status.value} | owner={w.current_owner}{blocker_str}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def cmd_events(task_id: str, project_id: Optional[str] = None) -> str:
    """Show event history for a task."""
    journal = _get_journal()
    if project_id is None:
        # Try to derive from workitem
        try:
            w = _get_store().load_workitem(task_id)
            project_id = w.project_id
        except Exception:
            return f"Error: please provide --project <project_id>"
    try:
        events = journal.get_for_task(task_id, project_id, limit=20)
        if not events:
            return f"No events found for task '{task_id}'"
        lines = [f"Event history for task '{task_id}' ({len(events)} events):"]
        for e in events:
            lines.append(f"  [{e.timestamp.isoformat()}] {e.event_type} | {e.actor} | {e.event_summary[:60]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def cmd_checkpoint(task_id: str) -> str:
    """Show latest checkpoint info for a task."""
    cfg = _get_config()
    ckpt = Checkpointer(cfg)
    store = _get_store()
    try:
        w = store.load_workitem(task_id)
        info = _fmt_checkpoint_info(task_id, store, ckpt)
        return f"Checkpoint info for '{w.task_title}':\n{info}"
    except Exception as e:
        return f"Error: {e}"


def cmd_evidence(task_id: str, project_id: Optional[str] = None) -> str:
    """Show evidence links for a task."""
    evstore = _get_evidence()
    if project_id is None:
        try:
            w = _get_store().load_workitem(task_id)
            project_id = w.project_id
        except Exception:
            return f"Error: please provide --project <project_id>"
    try:
        records = evstore.get_for_task(task_id)
        if not records:
            return f"No evidence found for task '{task_id}'"
        lines = [f"Evidence for task '{task_id}' ({len(records)} records):"]
        for r in records:
            lines.append(
                f"  [{r.evidence_type.value}] {r.description} "
                f"| actor={r.actor_role} | path={r.path}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def cmd_pipeline(project_id: str) -> str:
    """Show pipeline view — all workitems and their current stages."""
    store = _get_store()
    try:
        task_ids = store.list_workitems(project_id=project_id)
        if not task_ids:
            return f"No workitems found for project '{project_id}'"

        # Load project for workflow info
        try:
            p = store.load_project(project_id)
        except Exception:
            return f"Error: project '{project_id}' not found"

        lines = [
            f"Pipeline view for project '{p.project_name}':",
            f"  Goal: {p.project_goal}",
            f"  Status: {p.project_status.value}",
            f"",
        ]

        # Group by stage
        by_stage: dict[str, list[WorkItem]] = {}
        for tid in task_ids:
            w = store.load_workitem(tid)
            stage = w.current_stage
            if stage not in by_stage:
                by_stage[stage] = []
            by_stage[stage].append(w)

        for stage in V1_PIPELINE_STAGES:
            items = by_stage.get(stage, [])
            if items:
                lines.append(f"  {stage}:")
                for w in items:
                    blocker_str = ""
                    try:
                        ts = store.load_taskstate(w.task_id)
                        if ts.current_blocker:
                            blocker_str = f" [BLOCKED: {ts.current_blocker}]"
                    except Exception:
                        pass
                    lines.append(
                        f"    - {w.task_title} | {w.task_status.value} | owner={w.current_owner}{blocker_str}"
                    )
            else:
                lines.append(f"  {stage}: (empty)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="PMO Smart Agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="list <project_id>")
    list_p.add_argument("project_id", help="Project ID")

    pipe_p = sub.add_parser("pipeline", help="pipeline <project_id>")
    pipe_p.add_argument("project_id", help="Project ID")

    status_p = sub.add_parser("status", help="status <task_id>")
    status_p.add_argument("task_id", help="Task ID")

    events_p = sub.add_parser("events", help="events <task_id>")
    events_p.add_argument("task_id", help="Task ID")
    events_p.add_argument("--project", dest="project_id", help="Project ID")

    ckpt_p = sub.add_parser("checkpoint", help="checkpoint <task_id>")
    ckpt_p.add_argument("task_id", help="Task ID")

    ev_p = sub.add_parser("evidence", help="evidence <task_id>")
    ev_p.add_argument("task_id", help="Task ID")
    ev_p.add_argument("--project", dest="project_id", help="Project ID")

    args = parser.parse_args()

    handlers = {
        "status": lambda: cmd_status(args.task_id),
        "list": lambda: cmd_list(args.project_id),
        "pipeline": lambda: cmd_pipeline(args.project_id),
        "events": lambda: cmd_events(args.task_id, args.project_id),
        "checkpoint": lambda: cmd_checkpoint(args.task_id),
        "evidence": lambda: cmd_evidence(args.task_id, args.project_id),
    }

    try:
        output = handlers[args.command]()
        print(output)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
