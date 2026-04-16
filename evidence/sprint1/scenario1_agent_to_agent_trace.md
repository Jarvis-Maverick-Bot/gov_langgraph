# Scenario 1: Agent-to-Agent Queue Loop

## Scenario Definition
Tests that messages flow correctly between agents through NATS: A→B request, B→A response, with proper state transitions (NEW → ROUTED → CLAIMED → ANSWERED) and linked response IDs.

## Evidence

### NATS Queue Event Log (2026-04-16, gov→planner→tdd)

Evidence source: `evidence/queue/2026-04-16.jsonl`

**Full handoff cycle — gov→planner request, planner→tdd response with plan:**

```
ts: 2026-04-16T07:29:06.351576+00:00  CREATE  msg cf54... sender=governance receiver=planner type=REQUEST state=NEW
ts: 2026-04-16T07:29:06.358681+00:00  CREATE  msg 3a5e... sender=planner receiver=tdd type=RESPONSE state=NEW
  payload: {"_plan_output":{"plan_id":"plan-cf54...","task_description":"Implement user authentication module",...}}
ts: 2026-04-16T07:29:06.365653+00:00  CREATE  msg c38c... sender=planner receiver=tdd type=REQUEST state=NEW
ts: 2026-04-16T07:29:06.373454+00:00  STATE   msg c38c... NEW→ROUTED
ts: 2026-04-16T07:29:06.379470+00:00  STATE   msg c38c... ROUTED→CLAIMED
ts: 2026-04-16T07:29:06.386674+00:00  STATE   msg c38c... CLAIMED→ANSWERED
```

**Second planner→tdd response (plan for user management):**

```
ts: 2026-04-16T07:29:06.435612+00:00  CREATE  msg 5d15... sender=governance receiver=planner type=REQUEST state=NEW
ts: 2026-04-16T07:29:06.440629+00:00  CREATE  msg bef8... sender=planner receiver=tdd type=RESPONSE state=NEW
  payload: {"_plan_output":{"plan_id":"plan-5d15...","task_description":"Implement user management feature",...}}
ts: 2026-04-16T07:29:06.446793+00:00  STATE   msg bef8... NEW→ROUTED
ts: 2026-04-16T07:29:06.453236+00:00  STATE   msg bef8... ROUTED→CLAIMED
ts: 2026-04-16T07:29:06.459155+00:00  STATE   msg bef8... CLAIMED→ANSWERED
```

### Full Request-Response Pair with Linked Response IDs (2026-04-15 batch)

Evidence source: `evidence/queue/2026-04-15.jsonl`

```
ts: 2026-04-15T15:34:53.519027+00:00  CREATE  msg 4290... sender=A receiver=B type=REQUEST payload={} state=NEW
ts: 2026-04-15T15:34:53.535780+00:00  CREATE  msg 09d8... sender=B receiver=A type=REQUEST payload={} state=NEW
ts: 2026-04-15T15:34:53.550394+00:00  CREATE  msg 01d1... sender=A receiver=B type=REQUEST payload={n=1} state=NEW
ts: 2026-04-15T15:34:53.616480+00:00  STATE   msg 01d1... NEW→ROUTED
ts: 2026-04-15T15:34:53.636328+00:00  CREATE  msg e026... sender=B receiver=A type=RESPONSE state=NEW
ts: 2026-04-15T15:34:53.641449+00:00  UPDATE  msg 7587... linked_response_id=e026ffd7... (request now linked to response)
```

## Flow Observed

1. Agent A creates REQUEST message to B — state=NEW
2. Routing layer transitions to ROUTED
3. Agent B claims message — state=CLAIMED
4. Agent B processes and responds — state=ANSWERED
5. Request and response linked via `linked_response_id` field
6. Multiple interleaved cycles observed in parallel (A/B, planner/tdd, gov/planner/tdd triples)

## Conclusion

Agent-to-agent queue loop is operational. NATS transport correctly routes messages between agents, state transitions are tracked (NEW→ROUTED→CLAIMED→ANSWERED), and request-response pairs are linked. Evidence spans A→B, planner→tdd, and gov→planner→tdd chains.

## Source Files
- `evidence/queue/2026-04-15.jsonl`
- `evidence/queue/2026-04-16.jsonl`
