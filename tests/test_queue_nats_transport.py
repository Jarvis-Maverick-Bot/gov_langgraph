"""
tests/test_queue_nats_transport.py
V1.9 Sprint 1, Task T1.2
Unit tests for governance.queue.nats_transport
"""

import pytest
import threading
from unittest.mock import patch, MagicMock

import governance.queue.nats_transport as nats_transport


class TestNATSConnectionError:
    """Tests for NATSConnectionError exception."""

    def test_error_message(self):
        err = nats_transport.NATSConnectionError("test message")
        assert str(err) == "test message"
        assert "test message" in str(err)


class TestBypassMode:
    """Tests for QUEUE_TRANSPORT=local bypass mode."""

    def test_bypass_flag_default(self):
        # Default depends on QUEUE_TRANSPORT env var; this test runs with QUEUE_TRANSPORT=local
        # so it will be True. Test the flag is a boolean.
        assert isinstance(nats_transport._bypass_nats, bool)

    def test_bypass_flag_can_be_set(self):
        nats_transport._bypass_nats = True
        assert nats_transport._bypass_nats is True
        nats_transport._bypass_nats = False  # reset


class TestPublishWithBypass:
    """Tests for publish() with NATS bypass enabled."""

    def test_publish_skips_nats_when_bypassed(self):
        nats_transport._bypass_nats = True
        # Should not raise - just returns silently
        nats_transport.publish("test.subject", b"payload")
        nats_transport._bypass_nats = False  # reset


class TestSubjectConstants:
    """Tests for NATS subject constants."""

    def test_subjects_defined(self):
        assert nats_transport.SUBJ_MESSAGES == "gov.queue.messages"
        assert nats_transport.SUBJ_RESPONSES == "gov.queue.responses"
        assert nats_transport.SUBJ_CLAIMS == "gov.queue.claims"
        assert nats_transport.SUBJ_ESCALATIONS == "gov.escalations"


class TestRunSync:
    """Tests for run_sync helper."""

    def test_run_sync_simple_coro(self):
        async def coro():
            return 42
        result = nats_transport.run_sync(coro())
        assert result == 42

    def test_run_sync_with_args(self):
        async def coro(x, y):
            return x + y
        result = nats_transport.run_sync(coro(3, 4))
        assert result == 7


class TestNATSConnection:
    """Tests for NATS connection behavior."""

    def test_connect_failure_raises_nats_connection_error(self):
        """When NATS is not available, should raise NATSConnectionError."""
        # Force re-connection attempt by resetting singleton
        nats_transport._client = None
        with pytest.raises(nats_transport.NATSConnectionError) as exc_info:
            nats_transport._get_client()
        assert "Failed to connect to NATS" in str(exc_info.value)
