"""
pmo_smart_agent.dashboard — PMO Smart Agent Dashboard

Pipeline view — shows all workitems and their current stages.
Blocked workitems highlighted.
"""

from __future__ import annotations

from gov_langgraph.harness import HarnessConfig, StateStore
from gov_langgraph.platform_model import Project, V1_PIPELINE_STAGES


def get_pipeline_view(project_id: str) -> dict:
    """
    Return a structured pipeline view for a project.

    Returns:
        dict with project info and workitems grouped by stage
    """
    cfg = HarnessConfig()
    cfg.ensure_dirs()
    store = StateStore(cfg.state_dir)

    p = store.load_project(project_id)
    task_ids = store.list_workitems(project_id=project_id)

    by_stage: dict[str, list[dict]] = {}
    for stage in V1_PIPELINE_STAGES:
        by_stage[stage] = []

    for tid in task_ids:
        w = store.load_workitem(tid)
        blocked = False
        blocker = None
        try:
            ts = store.load_taskstate(tid)
            blocked = bool(ts.current_blocker)
            blocker = ts.current_blocker
        except Exception:
            pass
        item = {
            "task_id": w.task_id,
            "title": w.task_title,
            "stage": w.current_stage,
            "status": w.task_status.value,
            "owner": w.current_owner,
            "blocked": blocked,
            "blocker": blocker,
            "priority": w.priority,
        }
        if w.current_stage in by_stage:
            by_stage[w.current_stage].append(item)
        else:
            by_stage.setdefault(w.current_stage, []).append(item)

    return {
        "project_id": p.project_id,
        "project_name": p.project_name,
        "project_goal": p.project_goal,
        "project_status": p.project_status.value,
        "stages": by_stage,
        "total_tasks": len(task_ids),
    }


def render_pipeline_text(project_id: str) -> str:
    """
    Render pipeline view as plain text.
    """
    try:
        view = get_pipeline_view(project_id)
    except Exception as e:
        return f"Error loading pipeline: {e}"

    lines = [
        f"Pipeline: {view['project_name']}",
        f"Goal: {view['project_goal']}",
        f"Status: {view['project_status']}",
        f"Total tasks: {view['total_tasks']}",
        "",
    ]

    blocked_total = 0
    for stage in V1_PIPELINE_STAGES:
        items = view["stages"].get(stage, [])
        if not items:
            lines.append(f"[{stage}] (empty)")
            continue

        stage_blocked = sum(1 for i in items if i["blocked"])
        blocked_total += stage_blocked
        lines.append(f"[{stage}] {len(items)} task(s) {f'({stage_blocked} blocked)' if stage_blocked else ''}")

        for item in items:
            blocker = f" | BLOCKED: {item['blocker']}" if item["blocked"] else ""
            lines.append(
                f"  - {item['title']} "
                f"| {item['status']} "
                f"| owner={item['owner']}"
                f"{blocker}"
            )
        lines.append("")

    if blocked_total:
        lines.append(f"{blocked_total} task(s) blocked overall")

    return "\n".join(lines)
