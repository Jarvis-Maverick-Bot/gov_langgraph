"""
governance/cli/commands/task_cmd.py
V1.9 Sprint 1, Task T5.3
Implement `governance task-list` command.

Lists all tasks with their lifecycle state.
Reads from governance/task/data/tasks.json.

Usage: python -m governance.cli.cli task-list
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from governance.task.store import TASKS_FILE


def task_list() -> list[dict]:
    """
    List all tasks in the task store.

    Returns:
        List of task dicts with id, source_message_id, executor, state, created_at
    """
    # Read directly from store's file path (supports temp store overrides in tests)
    from governance.task.store import TASKS_FILE as _tf
    tasks_file = _tf
    if not tasks_file.exists():
        return []

    with open(tasks_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    tasks = raw if isinstance(raw, list) else []

    # Return summary view
    result = []
    for t in tasks:
        record = t.get("result_record")
        result_summary = ""
        if record:
            result_summary = f"[{record.get('status', '?')}] {record.get('summary', '')}"

        result.append({
            "task_id": t["task_id"],
            "source_message_id": t.get("source_message_id"),
            "assigned_executor": t.get("assigned_executor"),
            "lifecycle_state": t.get("lifecycle_state"),
            "created_at": t.get("created_at"),
            "result_summary": result_summary,
        })

    return result


def format_task_list(tasks: list[dict]) -> str:
    """
    Format task list for terminal output.

    Returns plain-text table format.
    """
    if not tasks:
        return "Task store: no tasks"

    header = (
        f"{'TASK_ID':<38} {'STATE':<14} {'EXECUTOR':<16} "
        f"{'SOURCE_MSG':<38} {'RESULT'}"
    )
    separator = "-" * 120

    lines = [header, separator]
    for t in tasks:
        src = (t.get("source_message_id") or "")[:37]
        executor = (t.get("assigned_executor") or "")[:15]
        result = t.get("result_summary", "")[:40]
        lines.append(
            f"{t['task_id']:<38} "
            f"{t['lifecycle_state']:<14} "
            f"{executor:<16} "
            f"{src:<38} "
            f"{result}"
        )

    lines.append(f"\n{len(tasks)} task(s) in store")
    return "\n".join(lines)


def run(args: list[str]) -> None:
    """CLI entry point for task-list command."""
    tasks = task_list()
    print(format_task_list(tasks))


if __name__ == "__main__":
    run([])