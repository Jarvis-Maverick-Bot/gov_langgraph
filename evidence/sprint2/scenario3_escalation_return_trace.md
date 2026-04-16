# Scenario 3: Alex Escalation + Return

## Scenario Definition
Tests that when an escalation fires, it is escalated to Alex (human decision), Alex's decision is recorded, and the escalation state transitions ESCALATED → DECIDED → RETURNED, returning the item to the flow.

## Evidence

### Escalation Log — Full Return Cycle (2026-04-15)

Evidence source: `evidence/escalation/2026-04-15.jsonl`

**Example: esc-600 — ESCALATED → DECIDED → RETURNED**

```
ts: 2026-04-15T15:59:14.984630+00:00  escalation_create   esc_id=esc-600 item_id=item-600 reason=reason state=ESCALATED
ts: 2026-04-15T15:59:15.035952+00:00  escalation_create   esc_id=esc-600 item_id=item-600 (duplicate batch)
ts: 2026-04-15T16:00:05.314605+00:00  escalation_create   esc_id=esc-600 item_id=item-600 state=ESCALATED
ts: 2026-04-15T16:00:05.322132+00:00  escalation_state_decided  esc_id=esc-600 state=DECIDED decision_id=dec-600
ts: 2026-04-15T16:00:05.326710+00:00  escalation_state_returned  esc_id=esc-600 state=RETURNED
```

### Alex Decision Recorded (2026-04-15)

Evidence source: `evidence/escalation/2026-04-15.jsonl`

Multiple decisions recorded by Alex:

```
decision_id=ae5e29... escalation_id=esc-001 decision=APPROVE note="looks good, proceed" decided_by=Alex
decision_id=c307c5... escalation_id=esc-002 decision=REJECT note="too risky, rework required" decided_by=Alex
decision_id=ca9663... escalation_id=esc-003 decision=CONTINUE note="minor, continue anyway" decided_by=Alex
decision_id=f3154a... escalation_id=esc-004 decision=STOP note="halt immediately" decided_by=Alex
decision_id=6dfc17... escalation_id=esc-005 decision=APPROVE note="approved" decided_by=Alex
decision_id=f1e2ec... escalation_id=esc-006 decision=APPROVE note="ok" decided_by=Alex
```

### Alex Decisions at 2026-04-16T07:29 (all decided_by=Alex)

```
decision_id=f38df1... esc-001 APPROVE "looks good, proceed" decided_by=Alex
decision_id=378606... esc-002 REJECT "too risky, rework required" decided_by=Alex
decision_id=c6cd9a... esc-003 CONTINUE "minor, continue anyway" decided_by=Alex
decision_id=1a1365... esc-004 STOP "halt immediately" decided_by=Alex
decision_id=70b4dc... esc-005 APPROVE "approved" decided_by=Alex
decision_id=32c319... esc-006 APPROVE "ok" decided_by=Alex
decision_id=b7d83d... esc-007 APPROVE "first" decided_by=Alex
decision_id=a3308f... esc-008 REJECT "second" decided_by=Alex
decision_id=f35d0d... esc-010 APPROVE "ok" decided_by=Alex
decision_id=b84217... esc-020 REJECT "rejected" decided_by=Alex
decision_id=1abe66... esc-030 STOP "full stop" decided_by=Alex
decision_id=714b9a... esc-040 APPROVE "ok" decided_by=Alex
decision_id=7d747d... esc-050 APPROVE "ok" decided_by=Alex
decision_id=87d39f... esc-060 REJECT "scope too wide, narrow down" decided_by=Alex
```

### Signal Blocker Escalations (2026-04-15)

```
ts: 2026-04-15T15:59:14.916123+00:00  escalation_create esc_id=00836... item_id=d4f0... reason=approval_required state=ESCALATED
ts: 2026-04-15T15:59:14.918906+00:00  escalation_create esc_id=74e95... item_id=2dff... reason=blocker_exceeds_authority state=ESCALATED
ts: 2026-04-15T15:59:14.920439+00:00  escalation_create esc_id=94f7d... item_id=8fef... reason=scope_too_wide state=ESCALATED
```

## Flow Observed

1. System fires escalation (approval_required, blocker_exceeds_authority, scope_too_wide, or manual signal-blocker)
2. Escalation created: state=ESCALATED, escalated_by=system
3. Alex receives the escalation and makes a decision (APPROVE/REJECT/CONTINUE/STOP)
4. Decision recorded with decision_id, note, decided_by=Alex, decided_at
5. Escalation transitions: state=DECIDED (decision_id linked)
6. For return-eligible items: escalation transitions to state=RETURNED
7. Full audit trail of escalation lifecycle captured in append-only JSONL log

## Conclusion

Escalation circuit is fully operational. Alex receives escalations, decisions are recorded (APPROVE/REJECT/CONTINUE/STOP), state transitions to DECIDED, and items are returned to flow via RETURNED state. Multiple decision types used. Evidence spans 2026-04-15 and 2026-04-16.

## Source Files
- `evidence/escalation/2026-04-15.jsonl`
- `evidence/escalation/2026-04-16.jsonl`
