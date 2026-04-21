"""
NATS Collaboration Mechanism - Message Handler
Event-driven skill dispatch from listener callback.
Phase 2: handlers are concrete, worker is recovery sweep only.

Layer C binding for: "Start V2.0 Foundation Create" command.
Command intent: start_foundation_delivery
Workflow: v2_0 / stage: foundation_create
"""

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from .envelope import CollabEnvelope, AckEnvelope, VALID_MESSAGE_TYPES
from .state_store import CollabStateStore


# ── Subjects ───────────────────────────────────────────────────────────────────
_SUBJECTS = {
    'command': 'gov.collab.command',
    'ack': 'gov.collab.ack',
    'event': 'gov.collab.event',
    'notify': 'gov.collab.notify',
}


class _SubjectDict(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


SUBJECTS = _SubjectDict(_SUBJECTS)


# ── Skill Handler Registry (Phase 2) ─────────────────────────────────────────
# Maps message_type → async handler function.
# Each handler: async def handler(handler: CollabHandler, envelope: CollabEnvelope) -> str
# Returns a result description string.

async def _handle_open(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'open' — create new collab, no further action."""
    handler.store.update_collab(
        envelope.collab_id,
        status='open',
        current_owner=envelope.from_
    )
    return 'collab_opened'


async def _handle_start_foundation_create(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """
    Handle 'start_foundation_create' — initiates V2.0 Foundation delivery workflow.
    Layer C binding for: "Start V2.0 Foundation Create" command.
    Command intent: start_foundation_delivery

    Ownership model (corrected):
    - Nova is primary owner — collab owned by 'nova' (from_ field)
    - Jarvis receives the message but does NOT own this workflow
    - pending_action = 'awaiting_foundation_draft' means Nova must produce the draft
    - artifact_path is NOT set here — comes from review_request payload

    Completion criteria:
    - collab.status = 'open'
    - collab.current_owner = 'nova' (from Alex's kickoff, not Jarvis)
    - collab.pending_action = 'awaiting_foundation_draft'
    - collab.last_event = 'foundation_create_started'
    - collab.artifact_path = '' (unset — comes from review_request)
    """
    handler.store.update_collab(
        envelope.collab_id,
        status='open',
        current_owner=envelope.from_,  # Nova owns this workflow
        artifact_type='foundation',
        artifact_path='',  # No artifact yet — draft path comes from review_request
        pending_action='awaiting_foundation_draft',
        last_event='foundation_create_started'
    )
    handler.store.emit_event(
        envelope.collab_id,
        'foundation_create_started',
        message_id=envelope.message_id,
        artifact_type='foundation',
        from_=envelope.from_
    )
    return 'foundation_create_started'


async def _handle_foundation_draft_ready(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """
    Handle 'foundation_draft_ready' — Nova signals draft is complete.
    artifact_path comes from payload, not hardcoded.
    """
    payload = envelope.payload or {}
    artifact_path = payload.get('artifact_path', '')

    handler.store.update_collab(
        envelope.collab_id,
        status='in_progress',
        pending_action='',
        last_event='foundation_draft_ready',
        artifact_path=artifact_path
    )
    handler.store.emit_event(
        envelope.collab_id,
        'foundation_draft_ready',
        message_id=envelope.message_id,
        artifact_type='foundation',
        artifact_path=artifact_path
    )
    return 'foundation_draft_ready'


async def _handle_review_request(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """
    Handle 'review_request' — Nova hands over draft to Jarvis for review.

    Nova (primary executor) has produced a real Foundation draft.
    Jarvis (reviewer) receives it here and sets up review task.

    Ownership model (corrected):
    - current_owner = 'jarvis' — Jarvis is the reviewer for this stage
    - artifact_path sourced from payload (Nova's real draft path)
    - pending_action = 'awaiting_review_execution' triggers worker

    Payload expected:
      - command_intent: 'foundation_review_handover'
      - artifact_path: real path to Nova's draft  ← used for actual review
      - artifact_type: 'foundation'
      - review_scope: what Jarvis is judging
      - expected_output: 'review_response'
      - workflow: 'v2_0'
      - stage: 'foundation_create_review'
    """
    payload = envelope.payload or {}
    artifact_path = payload.get('artifact_path', '')
    review_scope = payload.get('review_scope', 'foundation completeness and governance alignment')
    expected_output = payload.get('expected_output', 'review_response')
    workflow = payload.get('workflow', 'v2_0')
    stage = payload.get('stage', 'foundation_create_review')

    handler.store.update_collab(
        envelope.collab_id,
        status='in_progress',
        current_owner=handler.my_id,  # Jarvis owns the review stage
        artifact_type=payload.get('artifact_type', 'foundation'),
        artifact_path=artifact_path,  # From Nova's draft payload — NOT hardcoded
        pending_action='awaiting_review_execution',
        last_event='review_handover_received'
    )
    handler.store.emit_event(
        envelope.collab_id,
        'review_handover_received',
        message_id=envelope.message_id,
        skill='review_request',
        summary=envelope.summary,
        artifact_path=artifact_path,
        review_scope=review_scope,
        expected_output=expected_output,
        workflow=workflow,
        stage=stage
    )
    return 'review_handover_received'


def _build_envelope(
    message_type: str,
    collab_id: str,
    from_: str,
    to: str,
    summary: str,
    payload: dict,
    artifact_type: Optional[str] = None,
    artifact_path: Optional[str] = None
) -> CollabEnvelope:
    """Build a standard CollabEnvelope. Used for all outbound messages."""
    return CollabEnvelope(
        message_id=f"msg-{uuid.uuid4().hex[:12]}",
        collab_id=collab_id,
        message_type=message_type,
        from_=from_,
        to=to,
        artifact_type=artifact_type,
        artifact_path=artifact_path,
        payload=payload,
        summary=summary,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


async def _send_envelope(handler: 'CollabHandler', envelope: CollabEnvelope,
                          subject: str = 'gov.collab.command') -> bool:
    """
    Send a CollabEnvelope via NATS and wait for ACK.
    Returns True if ACK received within timeout, False otherwise.
    """
    key = f"{envelope.collab_id}:{envelope.message_id}"
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    handler._pending_ack[key] = future

    try:
        await handler.nc.publish(subject, envelope.to_json())
        await handler.nc.flush()
        handler._log("SEND", f"[{envelope.collab_id}] {envelope.message_type} sent -> {envelope.to}")
    except Exception as e:
        handler._log("ERROR", f"[{envelope.collab_id}] send failed: {e}")
        return False

    try:
        await asyncio.wait_for(future, timeout=15.0)
        handler._log("ACK", f"[{envelope.collab_id}] ACK received for {envelope.message_type}")
        return True
    except asyncio.TimeoutError:
        handler._log("WARN", f"[{envelope.collab_id}] ACK timeout for {envelope.message_type}")
        return False
    finally:
        handler._pending_ack.pop(key, None)


async def _handle_review_response(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """
    Handle 'review_response' — record review result.

    Behavior differs by agent:
    - Jarvis receives review_response from Nova (should not happen in normal flow)
    - Nova receives review_response from Jarvis: auto-decide next step based on review_result

    Nova auto-follow-up logic (review_result-based):
    - approved: send complete to Jarvis + Telegram notify Alex
    - revision_required: update state for Nova's next draft iteration
    - blocked: Telegram notify Alex with blocker summary
    """
    payload = envelope.payload or {}
    review_result = payload.get('review_result', 'unknown')
    review_notes = payload.get('review_notes', '')
    review_judgment_path = payload.get('review_artifact_path', '')

    handler.store.update_collab(
        envelope.collab_id,
        last_event='review_received',
        pending_action=''
    )
    handler.store.emit_event(
        envelope.collab_id,
        'review_received',
        message_id=envelope.message_id,
        review_result=review_result,
        review_notes=review_notes
    )

    if handler.my_id == 'nova':
        if review_result == 'approved':
            # Step 6: send complete to Jarvis using unified envelope
            complete_env = _build_envelope(
                message_type='complete',
                collab_id=envelope.collab_id,
                from_='nova',
                to='jarvis',
                summary='Foundation Create workflow complete — approved by Jarvis review',
                payload={
                    'workflow': 'v2_0',
                    'stage': 'foundation_create_review',
                    'review_result': review_result,
                    'review_judgment_path': review_judgment_path
                }
            )
            await _send_envelope(handler, complete_env)

            # Step 7: Telegram notify Alex
            try:
                from governance.collab.notify import send_telegram_notification_async
                send_telegram_notification_async(
                    f"*Foundation Create — Complete*\n"
                    f"Collab: `{envelope.collab_id}`\n"
                    f"Result: *APPROVED*\n"
                    f"Review judgment: {review_judgment_path or 'N/A'}\n"
                    f"Status: Ready for next stage"
                )
            except Exception as e:
                handler._log("WARN", f"[{envelope.collab_id}] Telegram notification failed: {e}")

        elif review_result == 'revision_required':
            handler.store.update_collab(envelope.collab_id, status='in_progress', pending_action='awaiting_revision')
            try:
                from governance.collab.notify import send_telegram_notification_async
                send_telegram_notification_async(
                    f"*Foundation Create — Revision Required*\n"
                    f"Collab: `{envelope.collab_id}`\n"
                    f"Notes: {review_notes[:200]}\n"
                    f"Next: Nova revises draft and re-hands over"
                )
            except Exception:
                pass

        elif review_result == 'blocked':
            try:
                from governance.collab.notify import send_telegram_notification_async
                send_telegram_notification_async(
                    f"*Foundation Create — BLOCKED*\n"
                    f"Collab: `{envelope.collab_id}`\n"
                    f"Reason: {review_notes[:200]}\n"
                    f"Human decision required"
                )
            except Exception:
                pass

    return 'review_received'


async def _handle_decision_proposal(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'decision_proposal' — record proposal, set pending_action."""
    handler.store.update_collab(
        envelope.collab_id,
        last_event='decision_proposed',
        pending_action='awaiting_decision'
    )
    handler.store.emit_event(
        envelope.collab_id,
        'decision_proposed',
        message_id=envelope.message_id
    )
    return 'decision_proposal_received'


async def _handle_decision_response(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'decision_response' — record decision, clear pending_action."""
    handler.store.update_collab(
        envelope.collab_id,
        last_event='decision_received',
        pending_action=''
    )
    handler.store.emit_event(
        envelope.collab_id,
        'decision_received',
        message_id=envelope.message_id
    )
    return 'decision_received'


async def _handle_complete(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'complete' — mark collab completed."""
    handler.store.update_collab(
        envelope.collab_id,
        status='completed',
        last_event='collab_completed',
        pending_action=''
    )
    handler.store.emit_event(
        envelope.collab_id,
        'collab_completed',
        message_id=envelope.message_id
    )
    return 'collab_completed'


async def _handle_exit(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'exit' — mark collab exited."""
    handler.store.update_collab(
        envelope.collab_id,
        status='exited',
        last_event='collab_exited',
        pending_action=''
    )
    handler.store.emit_event(
        envelope.collab_id,
        'collab_exited',
        message_id=envelope.message_id
    )
    return 'collab_exited'


async def _handle_notify(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'notify' — log notification, no state change needed."""
    handler.store.emit_event(
        envelope.collab_id,
        'notification_sent',
        message_id=envelope.message_id,
        payload=envelope.payload
    )
    return 'notification_sent'


async def _handle_ping(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Handle 'ping' — respond with pong."""
    return 'acknowledged'


async def _handle_unknown(handler: 'CollabHandler', envelope: CollabEnvelope) -> str:
    """Fallback for unknown message types."""
    handler.store.emit_event(
        envelope.collab_id,
        'unknown_message_type',
        message_id=envelope.message_id,
        message_type=envelope.message_type
    )
    return 'unknown_message_type'


# Registry — maps message_type to skill handler
SKILL_REGISTRY: Dict[str, Callable] = {
    'open': _handle_open,
    'start_foundation_create': _handle_start_foundation_create,
    'foundation_draft_ready': _handle_foundation_draft_ready,
    'review_request': _handle_review_request,
    'review_response': _handle_review_response,
    'decision_proposal': _handle_decision_proposal,
    'decision_response': _handle_decision_response,
    'complete': _handle_complete,
    'exit': _handle_exit,
    'notify': _handle_notify,
    'ping': _handle_ping,
    'pong': _handle_ping,
}


class CollabHandler:
    """
    Main handler for inbound collaboration messages.

    Responsibilities:
    1. Validate incoming envelope
    2. Persist to durable store
    3. Emit received ACK
    4. Dispatch to skill handler (Phase 2: event-driven)
    5. Emit processed ACK
    """

    def __init__(self, nats_client, state_store: CollabStateStore, my_id: str):
        self.nc = nats_client
        self.store = state_store
        self.my_id = my_id  # 'jarvis' or 'nova'
        self._pending_ack: Dict[str, asyncio.Future] = {}

    def _log(self, level: str, line: str):
        """Log via daemon's log path (uses store's log path)."""
        from governance.collab.collab_daemon import _log_to_file, _paths
        try:
            p = _paths()
            _log_to_file(level, f"[{self.my_id}] {line}", p['daemon_log'])
        except Exception:
            print(f"[{level}] [{self.my_id}] {line}")

    async def handle_inbound(self, envelope: CollabEnvelope) -> bool:
        """
        Main entry point for inbound messages.
        Returns True if processed, False otherwise.
        """
        try:
            if not envelope.validate():
                self._log("WARN", f"Invalid envelope: {envelope.message_id}")
                return False

            self.store.log_message(envelope.as_dict(), direction='IN')
            await self._send_ack(envelope, 'received')

            handler_fn = SKILL_REGISTRY.get(envelope.message_type, _handle_unknown)
            try:
                result = await handler_fn(self, envelope)
                self._log("HANDLER", f"[{envelope.collab_id}] {envelope.message_type} -> {result}")
            except Exception as e:
                self._log("ERROR", f"Handler error for {envelope.message_type}: {e}")
                result = f'error: {e}'

            await self._send_ack(envelope, 'processed', result=result)
            return True

        except Exception as e:
            self._log("ERROR", f"handle_inbound fatal: {e}")
            return False

    async def handle_ack(self, ack: AckEnvelope) -> bool:
        """
        Handle an ACK message — complete the pending Future.
        Returns True if this ACK was expected and matched, False otherwise.
        """
        key = f"{ack.collab_id}:{ack.ack_for}"
        if key in self._pending_ack:
            self._pending_ack[key].set_result(ack)
            del self._pending_ack[key]
            return True
        return False

    async def _send_ack(self, envelope: CollabEnvelope, ack_type: str, result: str = ''):
        """Emit an ACK for this envelope.
        
        ack_type: 'received' or 'processed'
        For 'received': use AckEnvelope.received() — acknowledges receipt
        For 'processed': use AckEnvelope.processed() — acknowledges business logic completion
        """
        if ack_type == 'received':
            ack = AckEnvelope.received(envelope, envelope.from_)
        else:
            ack = AckEnvelope.processed(envelope, envelope.from_, result)
        try:
            await self.nc.publish(SUBJECTS['ack'], ack.to_json())
            await self.nc.flush()
            self._log("ACK", f"[{envelope.collab_id}] sent {ack_type} ACK for {envelope.message_id} -> {envelope.from_}")
        except Exception as e:
            self._log("ERROR", f"Failed to send ACK: {e}")
