"""
Telegram + NATS notification helpers for governed execution loop.
Sends proactive notifications to Alex via Telegram Bot HTTP API.
Sends workflow messages to Nova via NATS gov.collab.command subject.
"""

import urllib.request
import urllib.error
import json
import os
import threading
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_TELEGRAM_BOT_TOKEN = "8599695108:AAEFpu_ij3eSR4obBKfgfkrQejhnl2hkabQ"
_TELEGRAM_API_URL = f"https://api.telegram.org/bot{_TELEGRAM_BOT_TOKEN}"


def _send_telegram_sync(message: str, chat_id: str = "8231866924") -> bool:
    """
    Send a Telegram message via Bot HTTP API.
    Returns True if sent successfully, False otherwise.
    """
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{_TELEGRAM_API_URL}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                print(f"[NOTIFY] Telegram sent OK: {message[:60]}...")
                return True
            else:
                print(f"[NOTIFY] Telegram API error: {result}")
                return False
    except urllib.error.HTTPError as e:
        print(f"[NOTIFY] HTTP error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"[NOTIFY] Telegram send failed: {e}")
        return False


def send_telegram_notification(message: str, chat_id: str = "8231866924") -> bool:
    """
    Send a Telegram notification.
    Called from daemon context (executor) when a "must notify" event occurs.
    """
    return _send_telegram_sync(message, chat_id)


def send_telegram_notification_async(message: str, chat_id: str = "8231866924"):
    """
    Fire-and-forget version: send Telegram notification without blocking.
    Runs in a background thread.
    """
    t = threading.Thread(target=_send_telegram_sync, args=(message, chat_id))
    t.start()


async def send_review_response_to_nova(
    nc,  # NATS connection (asyncio nats client)
    collab_id: str,
    from_agent: str,
    to_agent: str,
    workflow: str,
    stage: str,
    review_result: str,  # "approved" | "revision_required" | "blocked"
    review_artifact_path: str,
    review_notes: str,
    subject: str = "gov.collab.command"
) -> bool:
    """
    Send review_response from Jarvis back to Nova via NATS command subject.
    review_response is a real workflow state-transition message — Nova consumes it
    as the next business step.
    """
    payload = {
        "message_type": "review_response",
        "collab_id": collab_id,
        "from": from_agent,
        "to": to_agent,
        "summary": f"Foundation review completed: {review_result}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "workflow": workflow,
            "stage": stage,
            "review_result": review_result,
            "review_artifact_path": review_artifact_path,
            "review_notes": review_notes
        }
    }

    data = json.dumps(payload).encode("utf-8")

    try:
        await nc.publish(subject, data)
        await nc.flush()
        print(f"[NOTIFY] review_response sent to {to_agent}: {review_result}")
        return True
    except Exception as e:
        print(f"[NOTIFY] review_response send failed: {e}")
        return False
