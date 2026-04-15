"""
governance/queue/nats_transport.py
V1.9 Sprint 1, Task T1.2
NATS transport wrapper for governance queue.

Provides publish/subscribe/request over NATS subjects.
Subjects:
    gov.queue.messages   — main queue inbox
    gov.queue.responses  — return-path responses
    gov.queue.claims     — claim acknowledgments
    gov.escalations      — escalation events
"""

import asyncio
import os
import threading
from typing import Callable, Optional

import nats
from nats import NATS


class NATSConnectionError(Exception):
    """Raised when NATS connection is unavailable and auto-reconnect fails."""
    pass


# Bypass flag — set to True to skip NATS operations (for testing/CI without NATS)
# Tests can patch this via: governance.queue.nats_transport._bypass_nats = True
_bypass_nats: bool = os.environ.get("QUEUE_TRANSPORT") == "local"

# Singleton client state
_client: Optional[NATS] = None
_client_lock = threading.RLock()
_loop: Optional[asyncio.AbstractEventLoop] = None
_loop_lock = threading.RLock()

# Default NATS URL
DEFAULT_URL = "nats://127.0.0.1:4222"


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get or create the event loop for async operations."""
    with _loop_lock:
        global _loop
        if _loop is None:
            try:
                _loop = asyncio.get_running_loop()
            except RuntimeError:
                _loop = asyncio.new_event_loop()
                asyncio.set_event_loop(_loop)
        return _loop


def run_sync(coro) -> any:
    """
    Run an async coroutine synchronously in a dedicated loop.

    Bridge for calling async NATS methods from sync store operations.
    """
    loop = _get_loop()
    if loop.is_running():
        # If loop is already running (e.g., in a notebook or another thread),
        # we need a different approach - create a new loop in this thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


async def _connect_client(url: str = DEFAULT_URL) -> NATS:
    """Internal async connect with auto-reconnect."""
    return await nats.connect(url, reconnect_time_wait=2, max_reconnect_attempts=5)


def _get_client() -> NATS:
    """Get the singleton NATS client, connecting if necessary."""
    global _client
    with _client_lock:
        if _client is None:
            try:
                _client = run_sync(_connect_client())
            except Exception as e:
                raise NATSConnectionError(
                    f"Failed to connect to NATS at {DEFAULT_URL}: {e}. "
                    "Ensure NATS server is running or set NATS_URL env var."
                ) from e
        return _client


def publish(subject: str, payload: bytes) -> None:
    """
    Publish a message to a NATS subject.

    Args:
        subject: NATS subject name (e.g., 'gov.queue.messages')
        payload: bytes payload to send

    Raises:
        NATSConnectionError: if NATS is unavailable and not in bypass mode
    """
    if _bypass_nats:
        return  # Skip NATS in local/test mode

    async def _pub():
        client = await _connect_client()
        try:
            await client.publish(subject, payload)
            await client.flush()
        finally:
            await client.close()

    try:
        run_sync(_pub())
    except NATSConnectionError:
        raise
    except Exception as e:
        raise NATSConnectionError(
            f"Failed to publish to {subject}: {e}"
        ) from e


def subscribe(subject: str, callback: Callable[[str, bytes], None]) -> None:
    """
    Subscribe to a NATS subject with a callback.

    The callback receives (subject: str, payload: bytes).

    Args:
        subject: NATS subject name
        callback: synchronous callback(subject, payload)

    Raises:
        NATSConnectionError: if NATS is unavailable
    """
    def _wrap(msg):
        callback(msg.subject, msg.data)

    async def _sub():
        client = await _connect_client()
        await client.subscribe(subject, cb=_wrap)

    try:
        run_sync(_sub())
    except NATSConnectionError:
        raise
    except Exception as e:
        raise NATSConnectionError(
            f"Failed to subscribe to {subject}: {e}"
        ) from e


def request(subject: str, payload: bytes, timeout: float = 5.0) -> bytes:
    """
    Send a request and wait for a response (request-reply pattern).

    Args:
        subject: NATS subject name
        payload: bytes payload to send
        timeout: seconds to wait for response

    Returns:
        Response payload as bytes

    Raises:
        NATSConnectionError: if NATS is unavailable or times out
        asyncio.TimeoutError: if request times out
    """
    async def _req():
        client = await _connect_client()
        try:
            msg = await client.request(subject, payload, timeout=timeout)
            return msg.data
        finally:
            await client.close()

    try:
        return run_sync(_req())
    except NATSConnectionError:
        raise
    except Exception as e:
        if isinstance(e, asyncio.TimeoutError):
            raise NATSConnectionError(
                f"Request to {subject} timed out after {timeout}s"
            ) from e
        raise NATSConnectionError(
            f"Request to {subject} failed: {e}"
        ) from e


def get_client() -> NATS:
    """
    Get the underlying NATS client for advanced use.

    Returns:
        The singleton nats.client.NATS instance

    Raises:
        NATSConnectionError: if client is not connected
    """
    try:
        return _get_client()
    except NATSConnectionError:
        raise
    except Exception as e:
        raise NATSConnectionError(
            f"Cannot get NATS client: {e}"
        ) from e


# Convenience subject constants
SUBJ_MESSAGES = "gov.queue.messages"
SUBJ_RESPONSES = "gov.queue.responses"
SUBJ_CLAIMS = "gov.queue.claims"
SUBJ_ESCALATIONS = "gov.escalations"
