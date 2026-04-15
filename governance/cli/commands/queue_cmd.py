"""
governance/cli/commands/queue_cmd.py
V1.9 Sprint 1, Task T5.2
Implement `governance queue-list` command.

Lists all queue messages with their state.
Reads from governance/queue/data/messages.json.

Usage: python -m governance.cli.cli queue-list
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from governance.queue.store import get_store as _get_queue_store
from governance.queue.store import MESSAGES_FILE as _default_messages_file


def queue_list() -> list[dict]:
    """
    List all messages in the queue store.

    Returns:
        List of message dicts with id, sender, receiver, type, state, created_at
    """
    # Read directly from store's file path (supports temp store overrides in tests)
    from governance.queue.store import MESSAGES_FILE as _mf
    messages_file = _mf
    if not messages_file.exists():
        return []

    with open(messages_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    messages = raw if isinstance(raw, list) else []

    # Return summary view (not full payload to keep output clean)
    return [
        {
            "message_id": m["message_id"],
            "sender": m["sender"],
            "receiver": m["receiver"],
            "type": m["type"],
            "state": m["state"],
            "created_at": m["created_at"],
            "linked_response_id": m.get("linked_response_id"),
        }
        for m in messages
    ]


def format_queue_list(messages: list[dict]) -> str:
    """
    Format queue list for terminal output.

    Returns plain-text table format.
    """
    if not messages:
        return "Queue: no messages"

    header = f"{'MESSAGE_ID':<38} {'FROM':<12} {'TO':<12} {'TYPE':<10} {'STATE':<10} {'CREATED_AT':<28}"
    separator = "-" * len(header)

    lines = [header, separator]
    for m in messages:
        lines.append(
            f"{m['message_id']:<38} "
            f"{m['sender']:<12} "
            f"{m['receiver']:<12} "
            f"{m['type']:<10} "
            f"{m['state']:<10} "
            f"{m['created_at']:<28}"
        )

    lines.append(f"\n{len(messages)} message(s) in queue")
    return "\n".join(lines)


def run(args: list[str]) -> None:
    """CLI entry point for queue-list command."""
    messages = queue_list()
    print(format_queue_list(messages))


if __name__ == "__main__":
    run([])