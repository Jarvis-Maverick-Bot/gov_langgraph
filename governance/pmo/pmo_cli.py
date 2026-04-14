"""PMO Smart Agent — State store and CLI for V1.8 delivery management."""

import json
import os
import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "pmo_state.json"
EVENT_LOG_FILE = DATA_DIR / "pmo_event_log.json"
TASK_LOG_FILE = DATA_DIR / "pmo_task_log.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_state():
    _ensure_data_dir()
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"items": {}, "sequences": {"work_item": 0}}


def _save_state(state):
    _ensure_data_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _load_event_log():
    _ensure_data_dir()
    if EVENT_LOG_FILE.exists():
        return json.loads(EVENT_LOG_FILE.read_text())
    return []


def _save_event_log(log):
    _ensure_data_dir()
    EVENT_LOG_FILE.write_text(json.dumps(log, indent=2))


def _load_task_log():
    _ensure_data_dir()
    if TASK_LOG_FILE.exists():
        return json.loads(TASK_LOG_FILE.read_text())
    return []


def _save_task_log(log):
    _ensure_data_dir()
    TASK_LOG_FILE.write_text(json.dumps(log, indent=2))


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─── Authority: V1.8 Bounded Control ────────────────────────────────────────

AUTHORIZED_ACTIONS = {
    "launch-subagent": ["Jarvis", "Nova", "Alex"],
    "pause-task":     ["Jarvis", "Nova", "Alex"],
    "inspect-task":   ["Jarvis", "Nova", "Alex", "AGENT", "SUB_AGENT"],
    "terminate-task":  ["Jarvis", "Nova", "Alex"],
    "invoke-command": ["Jarvis", "Nova", "Alex"],
}

AUTHORIZED_AGENT_TYPES = {"TDD", "Planner", "CodeReviewer", "Security", "Docs", "DBExpert"}


def _check_authority(action: str, actor: str) -> bool:
    """Check if actor is authorized for action in V1.8 bounded scope."""
    if actor in AUTHORIZED_ACTIONS.get(action, []):
        return True
    # V1.8: no autonomous expansion — unknown actors are FORBIDDEN
    return False


# ─── Routing Rules ───────────────────────────────────────────────────────────

DESTINATIONS = {"AGENT", "SUB_AGENT", "PMO", "NOVA", "ALEX"}

ROUTING_RULES = {
    "UNKNOWN_TOOL": "AGENT",
    "BLOCKER_ESCALATION": "PMO",
    "CLARIFICATION_NEEDED": "NOVA",
    "TASK_COMPLETE": "PMO",
    "TASK_FAILED": "PMO",
    "DELIVERY_REQUEST": "PMO",
}


def route_event(event_json: str) -> dict:
    """Accept a routing request, determine destination, forward, log."""
    try:
        event = json.loads(event_json)
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid JSON"}

    event_type = event.get("type", "UNKNOWN")
    context = event.get("context", {})
    initiator = event.get("initiator", "unknown")
    payload = event.get("payload", {})

    event_id = f"EVT-{uuid.uuid4().hex[:8]}"
    determined_destination = ROUTING_RULES.get(event_type, "PMO")
    timestamp = _now()

    routing_record = {
        "event_id": event_id,
        "type": event_type,
        "initiator": initiator,
        "context": context,
        "payload": payload,
        "determined_destination": determined_destination,
        "status": "FORWARDED",
        "forwarded_at": timestamp,
    }

    log = _load_event_log()
    log.append(routing_record)
    _save_event_log(log)

    return {
        "ok": True,
        "event_id": event_id,
        "status": "FORWARDED",
        "destination": determined_destination,
        "at": timestamp,
    }


def get_event_log(event_id: str | None = None) -> dict:
    """Return full event log or single event."""
    log = _load_event_log()
    if event_id:
        for entry in log:
            if entry["event_id"] == event_id:
                return {"ok": True, "event": entry}
        return {"ok": False, "error": f"Event not found: {event_id}"}
    return {"ok": True, "events": log, "total": len(log)}


# ─── Control Commands ─────────────────────────────────────────────────────────


def _log_task_action(task_id: str, action: str, actor: str, result: dict):
    log = _load_task_log()
    log.append({
        "task_id": task_id,
        "action": action,
        "actor": actor,
        "result": result,
        "at": _now(),
    })
    _save_task_log(log)


def launch_subagent(task_id: str, agent_type: str, actor: str = "Jarvis") -> dict:
    if not _check_authority("launch-subagent", actor):
        return {"ok": False, "error": "FORBIDDEN", "reason": f"{actor} not authorized for launch-subagent in V1.8"}
    if agent_type not in AUTHORIZED_AGENT_TYPES:
        return {"ok": False, "error": f"Unknown agent type: {agent_type}. Valid: {', '.join(AUTHORIZED_AGENT_TYPES)}"}

    state = _load_state()
    if task_id in state.get("tasks", {}):
        return {"ok": False, "error": f"Task already exists: {task_id}"}

    if "tasks" not in state:
        state["tasks"] = {}
    state["tasks"][task_id] = {
        "id": task_id,
        "agent_type": agent_type,
        "status": "RUNNING",
        "created_at": _now(),
        "updated_at": _now(),
        "actions": [],
    }
    state["updated_at"] = _now()
    _save_state(state)

    result = {"ok": True, "task_id": task_id, "agent_type": agent_type, "status": "RUNNING"}
    _log_task_action(task_id, "launch-subagent", actor, result)
    return result


def pause_task(task_id: str, actor: str = "Jarvis") -> dict:
    if not _check_authority("pause-task", actor):
        return {"ok": False, "error": "FORBIDDEN", "reason": f"{actor} not authorized for pause-task in V1.8"}
    state = _load_state()
    tasks = state.get("tasks", {})
    if task_id not in tasks:
        return {"ok": False, "error": f"Task not found: {task_id}"}
    if tasks[task_id]["status"] == "TERMINATED":
        return {"ok": False, "error": f"Cannot pause terminated task: {task_id}"}

    tasks[task_id]["status"] = "PAUSED"
    tasks[task_id]["updated_at"] = _now()
    state["updated_at"] = _now()
    _save_state(state)

    result = {"ok": True, "task_id": task_id, "status": "PAUSED"}
    _log_task_action(task_id, "pause-task", actor, result)
    return result


def inspect_task(task_id: str, actor: str = "Jarvis") -> dict:
    if not _check_authority("inspect-task", actor):
        return {"ok": False, "error": "FORBIDDEN", "reason": f"{actor} not authorized for inspect-task in V1.8"}
    state = _load_state()
    tasks = state.get("tasks", {})
    if task_id not in tasks:
        return {"ok": False, "error": f"Task not found: {task_id}"}
    task = tasks[task_id]
    result = {"ok": True, "task": task}
    _log_task_action(task_id, "inspect-task", actor, result)
    return result


def terminate_task(task_id: str, actor: str = "Jarvis") -> dict:
    if not _check_authority("terminate-task", actor):
        return {"ok": False, "error": "FORBIDDEN", "reason": f"{actor} not authorized for terminate-task in V1.8"}
    state = _load_state()
    tasks = state.get("tasks", {})
    if task_id not in tasks:
        return {"ok": False, "error": f"Task not found: {task_id}"}
    if tasks[task_id]["status"] == "TERMINATED":
        return {"ok": False, "error": f"Task already terminated: {task_id}"}
    tasks[task_id]["status"] = "TERMINATED"
    tasks[task_id]["updated_at"] = _now()
    state["updated_at"] = _now()
    _save_state(state)

    result = {"ok": True, "task_id": task_id, "status": "TERMINATED"}
    _log_task_action(task_id, "terminate-task", actor, result)
    return result


def invoke_command(task_id: str, cmd: str, actor: str = "Jarvis") -> dict:
    if not _check_authority("invoke-command", actor):
        return {"ok": False, "error": "FORBIDDEN", "reason": f"{actor} not authorized for invoke-command in V1.8"}
    state = _load_state()
    tasks = state.get("tasks", {})
    if task_id not in tasks:
        return {"ok": False, "error": f"Task not found: {task_id}"}
    task = tasks[task_id]
    if task["status"] == "TERMINATED":
        return {"ok": False, "error": f"Cannot invoke on terminated task: {task_id}"}

    cmd_id = f"CMD-{uuid.uuid4().hex[:8]}"
    cmd_record = {
        "id": cmd_id,
        "task_id": task_id,
        "command": cmd,
        "invoked_at": _now(),
    }
    task.setdefault("actions", []).append(cmd_record)
    task["updated_at"] = _now()
    state["updated_at"] = _now()
    _save_state(state)

    result = {"ok": True, "command_id": cmd_id, "task_id": task_id, "command": cmd}
    _log_task_action(task_id, "invoke-command", actor, result)
    return result


def get_task_log() -> dict:
    log = _load_task_log()
    return {"ok": True, "log": log, "total": len(log)}


# ─── PMO Commands ────────────────────────────────────────────────────────────


def create_work_item(name: str) -> dict:
    state = _load_state()
    state["sequences"]["work_item"] += 1
    seq = state["sequences"]["work_item"]
    item_id = f"WI-{seq:03d}"
    item = {
        "id": item_id,
        "name": name,
        "stage": "BACKLOG",
        "created_at": _now(),
        "updated_at": _now(),
        "artifacts": [],
        "validations": [],
        "blockers": [],
        "transitions": [],
        "delivery_package": None,
    }
    state["items"][item_id] = item
    _save_state(state)
    return {"ok": True, "item_id": item_id, "name": name, "stage": "BACKLOG"}


def submit_artifact(item_id: str, path: str) -> dict:
    state = _load_state()
    if item_id not in state["items"]:
        return {"ok": False, "error": f"Item not found: {item_id}"}
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"Artifact path does not exist: {path}"}
    artifact = {
        "id": f"ART-{uuid.uuid4().hex[:8]}",
        "item_id": item_id,
        "path": str(p.resolve()),
        "name": p.name,
        "submitted_at": _now(),
    }
    state["items"][item_id]["artifacts"].append(artifact)
    state["items"][item_id]["updated_at"] = _now()
    _save_state(state)
    return {"ok": True, "artifact_id": artifact["id"], "item_id": item_id, "path": artifact["path"]}


def request_transition(item_id: str, stage: str) -> dict:
    state = _load_state()
    if item_id not in state["items"]:
        return {"ok": False, "error": f"Item not found: {item_id}"}
    valid_stages = ["BACKLOG", "IN_PROGRESS", "IN_REVIEW", "APPROVED", "DELIVERED"]
    if stage not in valid_stages:
        return {"ok": False, "error": f"Invalid stage. Valid: {', '.join(valid_stages)}"}
    item = state["items"][item_id]
    old_stage = item["stage"]
    item["stage"] = stage
    item["transitions"].append({"from": old_stage, "to": stage, "at": _now()})
    item["updated_at"] = _now()
    _save_state(state)
    return {"ok": True, "item_id": item_id, "from": old_stage, "to": stage}


def record_validation(item_id: str, result: str) -> dict:
    state = _load_state()
    if item_id not in state["items"]:
        return {"ok": False, "error": f"Item not found: {item_id}"}
    valid_results = ["PASS", "FAIL", "PENDING"]
    if result not in valid_results:
        return {"ok": False, "error": f"Invalid result. Valid: {', '.join(valid_results)}"}
    validation = {
        "id": f"VAL-{uuid.uuid4().hex[:8]}",
        "item_id": item_id,
        "result": result,
        "recorded_at": _now(),
    }
    state["items"][item_id]["validations"].append(validation)
    state["items"][item_id]["updated_at"] = _now()
    _save_state(state)
    return {"ok": True, "validation_id": validation["id"], "item_id": item_id, "result": result}


def signal_blocker(item_id: str, desc: str) -> dict:
    state = _load_state()
    if item_id not in state["items"]:
        return {"ok": False, "error": f"Item not found: {item_id}"}
    blocker = {
        "id": f"BLK-{uuid.uuid4().hex[:8]}",
        "item_id": item_id,
        "description": desc,
        "signaled_at": _now(),
        "resolved": False,
    }
    state["items"][item_id]["blockers"].append(blocker)
    state["items"][item_id]["updated_at"] = _now()
    _save_state(state)
    return {"ok": True, "blocker_id": blocker["id"], "item_id": item_id, "description": desc}


def package_delivery(item_id: str) -> dict:
    state = _load_state()
    if item_id not in state["items"]:
        return {"ok": False, "error": f"Item not found: {item_id}"}
    item = state["items"][item_id]
    pkg_id = f"PKG-{uuid.uuid4().hex[:8]}"
    package = {
        "id": pkg_id,
        "item_id": item_id,
        "name": item["name"],
        "stage": item["stage"],
        "artifacts": [a["id"] for a in item["artifacts"]],
        "validations": [v["id"] for v in item["validations"]],
        "blockers": [b["id"] for b in item["blockers"] if not b["resolved"]],
        "created_at": _now(),
    }
    item["delivery_package"] = package
    item["updated_at"] = _now()
    _save_state(state)
    return {"ok": True, "package_id": pkg_id, "item_id": item_id, "stage": item["stage"]}


def status(item_id: str | None = None) -> dict:
    state = _load_state()
    if item_id:
        if item_id not in state["items"]:
            return {"ok": False, "error": f"Item not found: {item_id}"}
        return {"ok": True, "item": state["items"][item_id]}
    return {"ok": True, "items": list(state["items"].values()), "total": len(state["items"])}


# ─── CLI entry point ─────────────────────────────────────────────────────────


COMMANDS = {
    "create-work-item":  (create_work_item,  "<name>"),
    "submit-artifact":    (submit_artifact,   "<item_id> <path>"),
    "request-transition": (request_transition, "<item_id> <stage>"),
    "record-validation":  (record_validation,  "<item_id> <result>"),
    "signal-blocker":     (signal_blocker,     "<item_id> <description>"),
    "package-delivery":   (package_delivery,   "<item_id>"),
    "status":             (status,             "[item_id]"),
    "route-event":        (route_event,        "<json_string>"),
    "event-log":          (get_event_log,       "[event_id]"),
    "launch-subagent":    (launch_subagent,    "<task_id> <agent_type>"),
    "pause-task":         (pause_task,          "<task_id>"),
    "inspect-task":       (inspect_task,        "<task_id>"),
    "terminate-task":      (terminate_task,      "<task_id>"),
    "invoke-command":      (invoke_command,      "<task_id> <command>"),
    "task-log":           (get_task_log,         ""),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("PMO CLI — V1.8 Delivery Management")
        print()
        print("=== Delivery Management ===")
        for cmd in ["create-work-item", "submit-artifact", "request-transition",
                    "record-validation", "signal-blocker", "package-delivery", "status"]:
            fn, usage = COMMANDS[cmd]
            print(f"  pmo {cmd} {usage}")
        print()
        print("=== Event Routing ===")
        for cmd in ["route-event", "event-log"]:
            fn, usage = COMMANDS[cmd]
            print(f"  pmo {cmd} {usage}")
        print()
        print("=== Task Control ===")
        for cmd in ["launch-subagent", "pause-task", "inspect-task", "terminate-task", "invoke-command", "task-log"]:
            fn, usage = COMMANDS[cmd]
            print(f"  pmo {cmd} {usage}")
        print()
        print("  pmo --help   Show this message")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"ERROR: Unknown command '{cmd}'")
        print(f"Valid: {', '.join(sorted(COMMANDS))}")
        sys.exit(1)

    fn, usage = COMMANDS[cmd]
    args = sys.argv[2:]

    if cmd == "create-work-item":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "submit-artifact":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], args[1])
    elif cmd == "request-transition":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], args[1])
    elif cmd == "record-validation":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], args[1])
    elif cmd == "signal-blocker":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], " ".join(args[1:]))
    elif cmd == "package-delivery":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "status":
        result = fn(args[0] if args else None)
    elif cmd == "route-event":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "event-log":
        result = fn(args[0] if args else None)
    elif cmd == "launch-subagent":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], args[1])
    elif cmd == "pause-task":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "inspect-task":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "terminate-task":
        if len(args) < 1:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0])
    elif cmd == "invoke-command":
        if len(args) < 2:
            print(f"EXPECTED: {usage}"); sys.exit(1)
        result = fn(args[0], " ".join(args[1:]))
    elif cmd == "task-log":
        result = fn()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
