"""
Telegram notification helper for governed execution loop.
Sends proactive notifications to Alex when required events occur.
"""

import os


def send_telegram_notification(message: str, chat_id: str = None):
    """
    Send a Telegram notification via OpenClaw message tool.
    This is called from the daemon context when a "must notify" event occurs.
    """
    try:
        # Use OpenClaw's built-in message tool via subprocess
        # The message tool is available in the main session — here we use it via agent context
        # For daemon context, we write to a notification queue file instead
        # which the main session reads and sends
        notification_queue_path = os.path.join(
            os.environ.get('COLLAB_DATA_DIR', str(__file__).rsplit('governance', 1)[0] + 'governance\\data'),
            'pending_notifications.jsonl'
        )

        import json
        from datetime import datetime, timezone

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "chat_id": chat_id or "8231866924"  # Alex's Telegram chat ID
        }

        with open(notification_queue_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    except Exception as e:
        # Silently fail — notification failure should not crash the executor
        print(f"[WARN] Telegram notification failed: {e}")


def read_pending_notifications() -> list:
    """Read and return pending notifications, then clear the queue."""
    notification_queue_path = os.path.join(
        os.environ.get('COLLAB_DATA_DIR', str(__file__).rsplit('governance', 1)[0] + 'governance\\data'),
        'pending_notifications.jsonl'
    )
    try:
        with open(notification_queue_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Clear the queue
        open(notification_queue_path, 'w', encoding='utf-8').close()
        import json
        return [json.loads(line) for line in lines if line.strip()]
    except Exception:
        return []