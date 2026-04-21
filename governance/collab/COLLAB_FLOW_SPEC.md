# Collaboration Flow Specification v0.1

## Channel Topology

| Channel | Purpose |
|---------|---------|
| `gov.collab.command` | All business messages: command, response, event |
| `gov.collab.ack` | Transport-layer ACK only — not business response |
| Telegram | Human-facing notifications from Jarvis only |

**原则：ACK 是传输层确认，业务响应必须是独立的 command 消息。**

---

## Message Taxonomy

### Command Messages (→ gov.collab.command)
- `start_foundation_create` — Nova → Jarvis
- `review_request` — Nova → Jarvis (handing over draft)
- `review_response` — Jarvis → Nova (judgment result)
- `complete` — Nova → Jarvis (workflow closed)
- `exit` — Nova → Jarvis (abort)
- `notify` — either → either (operational signal)

### ACK Messages (→ gov.collab.ack) — never business responses
- `received` — "I got your message"
- `processed` — "I finished handling your message"

---

## State Schema

```
CollabState:
  collab_id           # immutable
  status              # open | in_progress | completed | exited
  opened_by           # who initiated this collab
  current_owner       # business workflow owner
  receiver            # NATS routing target (envelope.to)
  pending_action      # what worker should do next
  last_event          # last business event
  last_message_id
  last_acknowledged_message_id  # for stale detection
```

---

## Flow 1: start_foundation_create

**Trigger:** Alex → Nova: "Start V2.0 Foundation Create"

**Step 1:** Nova handler: `_handle_start_foundation_create`
- State: `status=open`, `current_owner=nova`, `pending_action=awaiting_foundation_draft`
- **Business response sent:** `review_request` → Jarvis (after draft is ready)
- Transport: `received ACK` → Nova

**DoD for Step 1:**
- [ ] `review_request` message delivered to Jarvis on gov.collab.command
- [ ] Nova state: `status=in_progress`, `pending_action=awaiting_review_execution`
- [ ] Nova has sent `received ACK` for the inbound command

**Problem 1 (fixed):** Nova must send `review_request` as its business response, not wait for manual intervention.

**Implementation:**
```python
async def _handle_start_foundation_create(handler, envelope):
    handler.store.update_collab(envelope.collab_id,
        status='open',
        current_owner=envelope.from_,
        pending_action='awaiting_foundation_draft',
        last_event='foundation_create_started')

    # Nova's business response: write draft + send review_request to Jarvis
    draft_path = await _nova_write_foundation_draft(envelope.collab_id)

    review_req = _build_envelope(
        message_type='review_request',
        collab_id=envelope.collab_id,
        from_='nova',
        to='jarvis',
        payload={
            'command_intent': 'foundation_review_handover',
            'artifact_path': draft_path,
            'artifact_type': 'foundation',
            'review_scope': 'foundation completeness and governance alignment',
            'workflow': 'v2_0',
            'stage': 'foundation_create_review',
            'expected_output': 'review_response'
        },
        summary=f'Foundation draft ready for review: {draft_path}'
    )
    await _send_envelope(handler, review_req)
    return 'review_request_sent'
```

---

## Flow 2: review_request → review_response

**Trigger:** Nova → Jarvis: `review_request`

**Step 2a:** Jarvis handler: `_handle_review_request`
- State: `status=in_progress`, `current_owner=jarvis`, `pending_action=awaiting_review_execution`
- Transport: `received ACK` → Nova

**Step 2b:** Jarvis handler: review execution (inline, not worker)
- Load doctrine files
- Judge draft against doctrine
- Produce review judgment

**Step 2c:** Jarvis handler: business response
- **Business response sent:** `review_response` → Nova
  - `review_result`: 'approved' | 'revision_required' | 'blocked'
  - `review_notes`: judgment notes
  - `review_artifact_path`: path to written judgment doc (if any)
- Transport: `processed ACK` → Nova

**DoD for review_request:**
- [ ] `review_response` message delivered to Nova on gov.collab.command
- [ ] Jarvis state: `status=in_progress`, `pending_action=''`, `last_event=review_sent`
- [ ] `review_response` carries concrete `review_result` (not just ACK)

**Problem 2 (fixed):** Handler must await executor and send `review_response` as business response. Worker sweep must not double-process `awaiting_review_execution` while handler is running.

**Implementation:**
```python
async def _handle_review_request(handler, envelope):
    handler.store.update_collab(envelope.collab_id,
        current_owner='jarvis',
        pending_action='awaiting_review_execution',
        last_event='review_handover_received')

    # Execute review inline (not via worker)
    from governance.collab.review_executor import execute_review
    result = await execute_review(handler, envelope.collab_id,
        artifact_path=envelope.payload.get('artifact_path', ''),
        review_scope=envelope.payload.get('review_scope', ''),
        doctrine_loading_set=['v2_0_foundation_baseline', 'v2_0_scope', 'v2_0_prd'])

    # Send business response to Nova
    review_resp = _build_envelope(
        message_type='review_response',
        collab_id=envelope.collab_id,
        from_='jarvis',
        to='nova',
        payload={
            'review_result': result['review_result'],
            'review_notes': result['review_notes'],
            'review_artifact_path': result.get('review_artifact_path', ''),
            'workflow': 'v2_0',
            'stage': 'foundation_create_review'
        },
        summary=f'Foundation review: {result["review_result"]}'
    )
    await _send_envelope(handler, review_resp)
    return 'review_response_sent'
```

**Worker guard:** Worker skips `pending_action=awaiting_review_execution` if message_id matches last processed (dedup).

---

## Flow 3: exit / stop

**Trigger:** Nova → Jarvis: `exit`

**Step 3:** Jarvis handler: `_handle_exit`
- State: `status=exited`, `pending_action=''`, `last_event=collab_exited`
- **Business response sent:** `notify` + **Telegram notification to Alex**
- Transport: `processed ACK` → Nova

**DoD for exit:**
- [ ] Jarvis state: `status=exited`
- [ ] Telegram message delivered to Alex: "Foundation Create — EXITED by Nova"
- [ ] `processed ACK` sent to Nova

**Problem 3 (fixed):** Exit must produce human-visible Telegram notification. Not just state change.

---

## Worker Sweep Behavior (revised)

Worker sweep is **recovery only**, not primary path:

```
pending_action = 'awaiting_foundation_draft'  → Nova does this (not worker)
pending_action = 'awaiting_review_execution' → Jarvis handler owns this (not worker)
pending_action = 'awaiting_artifact'         → Worker sweep (legacy dedup)
pending_action = 'process_review'            → Worker sweep (if handler skipped)
pending_action = 'awaiting_revision'         → Nova does this
```

**Rule:** If a handler is responsible for a pending_action, worker MUST NOT process it unless handler left it stuck for > threshold (e.g., 60s).

---

## ACK Discipline (per SOUL.md rule)

- No ACK means no receive claim
- Handler sends `received ACK` before processing
- Handler sends `processed ACK` after business response is sent
- ACK is always from `to` back to `from_`

```
Nova sends message X to Jarvis
  → Jarvis receives X → sends [received ACK] to Nova
  → Jarvis processes → sends [processed ACK] to Nova
  → Jarvis sends business response Y to Nova (via command channel)
  → Nova receives Y → sends [received ACK] to Jarvis
```

---

## Observable Results by Step

| Step | Observable Result |
|------|------------------|
| start_foundation_create | Nova sends `review_request` to Jarvis; state shows `pending_action=awaiting_review_execution` |
| review_request | Jarvis sends `review_response` to Nova; Telegram notification to Alex |
| exit | Jarvis sends `exit ACK` to Nova; Telegram: "EXITS by Nova"; state `status=exited` |

---

## Files to Change

1. `governance/collab/handler.py` — `_handle_start_foundation_create` sends `review_request`; `_handle_review_request` executes inline + sends `review_response`
2. `governance/collab/review_executor.py` — returns structured `review_result` dict; does NOT send messages
3. `governance/collab/collab_daemon.py` — worker guard: skip `awaiting_review_execution` if handler is running (use instance_id or lock)
4. `governance/collab/notify.py` — Telegram send for exit notification
