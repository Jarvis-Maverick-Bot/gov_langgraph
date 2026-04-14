# V1.8 Foundation Document

## 1. Purpose

This document defines the intended foundation for V1.8 without reopening or retroactively changing the approved purpose of V1.7.

V1.7 remains the foundation-and-workflow validation release.
V1.8 builds on that foundation.

The V1.8 objective should be framed as:

> **Deliver the first real AI-native game through the Claw Studio + Viper operating model using a CLI-native operating surface, with a thin human oversight layer for visibility and governance where needed.**

This wording is deliberate.
V1.8 should prove first-product delivery reality, not expand prematurely into heavy UI scope.

---

## 2. Relationship to V1.7

## 2.1 No retroactive scope change

V1.8 must not redefine V1.7 after the fact.

V1.7 still closes on its own terms:
- minimum viable Claw Studio operating model
- one simple governed workflow path
- explicit Claw / PMO / Governance / Viper boundaries
- minimum mandatory artifacts
- proof that the structure is real enough to support later delivery

V1.8 starts only after that foundation is considered real enough to build on.

## 2.2 What V1.8 inherits from V1.7

V1.8 assumes the following are already established:
- Claw Studio as the game-native production unit
- the six-stage game production workflow
- the Viper trigger rule and handoff boundary
- the minimum product and operating artifacts
- the AI-native thesis that agents are the primary players
- minimum governance touchpoints at concept approval, escalations, and final acceptance

So V1.8 is not the version that proves the studio can exist.
It is the version that proves the studio can deliver.

---

## 3. Core V1.8 thesis

## 3.1 First delivery, not only first theory

V1.8 must produce the **first materially real AI-native game delivery**.

This means the output cannot remain:
- conceptual only
- artifact-only without executable use
- workflow-only without product reality
- UI mockup-driven without actual operating delivery path

The product must be real enough that the organization can honestly say:

> a first AI-native game was delivered through the defined governed production system.

## 3.2 CLI-first operating direction

For V1.8, the preferred operating shape is:
- **CLI layer** for workflow-driving actions, build/test execution, artifact submission, stage movement, and operator control
- **thin oversight UI layer** for visibility, review, approvals, and status surfaces where useful

This is the key directional refinement for V1.8.

The reason is simple:
- most production-driving actions are naturally structured commands
- CLI-first reduces unnecessary frontend expansion pressure
- it speeds iteration and testing
- it keeps the real operating contract explicit
- it allows the UI to stay lightweight and governance-oriented instead of becoming the entire operating substrate

## 3.3 AI-native product meaning in V1.8

In V1.8, AI-native still means:
- the primary intended players are AI agents
- the real gameplay interface is agent-facing
- human interaction is secondary to agent participation

But unlike V1.7, V1.8 must now prove **real delivery of that product**, not only foundational readiness.

---

## 4. What V1.8 must establish

By the end of V1.8, the following should be materially true:

### A. First AI-native game delivery is real
- one real game has moved through the defined system and reached delivery form
- the delivered output is agent-playable in a meaningful way
- the game has a clear objective structure, such as time-based completion, score maximization, or a similarly explicit challenge condition
- the game exposes a first standardized CLI command set sufficient for Agent integration
- at least one real Agent participant, such as Nova or Jarvis acting in the capacity of an Agent, can actually play and complete the game rather than only interact with it theoretically
- the delivery is reviewable, testable, and governable

### B. Claw + Viper function as a real delivery combination
- Claw defines the game product, game rules, and agent participation contract
- Viper supports the explicitly handed-off enablement and engineering surfaces
- the handoff is not abstract, but exercised in actual delivery
- the Jarvis team is responsible for creating the required Claw Studio Agent seats/components needed for V1.8 delivery, subject to Governance Layer review before they are treated as accepted operating structure

### C. CLI-first operation is proven in practice
- all PMO Smart Agent interaction scenarios that currently require human interaction are extracted into CLI commands
- PMO Smart Agent interaction no longer depends on UI as the operational interaction layer
- routine workflow-driving actions can be executed through a coherent command surface
- stage advancement, artifact handling, validation-triggering, and delivery-driving actions do not depend on a large custom UI
- the operating path is usable for internal production reality, not only demos
- the CLI also supports the specific command set required for the first AI-native game itself

### D. Human oversight remains explicit but lightweight
- governance approvals remain human-controlled at authority points
- PMO visibility and escalation still exist
- UI, when used, serves oversight and visibility more than primary execution

### E. PMO Event Routing exists as a governed coordination mechanism
- when an Agent or Sub-agent encounters an issue, request, or exception but does not know the correct responsible destination, it can forward that event to PMO
- PMO determines the appropriate destination and routes the event to the correct Agent, Sub-agent, or Alex
- PMO Event Routing is not only forwarding, but a bounded command-mediated coordination loop
- at minimum, PMO routing must support operational control actions needed to complete the routing loop, such as launching sub-agents, invoking commands, pausing tasks, requesting status updates, terminating tasks where necessary, relaying returned results, and sending the final response back to the initiating Agent/Sub-agent
- the first-pass routing basis should be deterministic rule lookup / explicit routing logic rather than AI-powered inference
- this mechanism is authority-aware and governance-visible
- this is a bounded routing mechanism, not yet a full formal message bus

### F. The product loop becomes more concrete
- game definition leads to executable build/output
- agent participation can be run and evaluated
- validation produces real acceptance evidence
- the system demonstrates first-product reality rather than only organizational readiness

---

## 5. Recommended V1.8 operating model

## 5.1 Surface split

Recommended split:

### CLI surface
Owns actions such as:
- create or register game work item
- submit or update artifact
- trigger stage transition request
- record validation result
- package delivery candidate
- flag blocker or escalation
- trigger Viper handoff or receive return package
- run test/play/evaluation commands
- send a governed event/request into PMO Event Routing when ownership or handling destination is unclear
- launch, pause, inspect, and terminate bounded sub-agent tasks where those controls are part of the approved PMO operating surface

### UI surface
Owns surfaces such as:
- workflow visibility
- production queue view
- artifact/review visibility
- approval screens
- status and risk display
- lightweight inspection and comparison surfaces

### Hard direction rule
The UI should not become a dependency for every routine operation in V1.8.
The CLI is the primary and required operating path.
The UI is an oversight/visibility path and must not remain an interaction dependency for PMO Smart Agent operations.

## 5.2 Why this split is strategically cleaner

This split preserves long-term system clarity:
- operations remain scriptable and testable
- interfaces stay explicit
- delivery logic is less coupled to frontend construction speed
- later versions can add stronger UI safely without making UI the hidden operating core

---

## 6. V1.8 scope boundary

## 6.1 In scope

V1.8 should include:
- first real AI-native game delivery through the governed workflow
- first standardized CLI command set for Agent integration into the game
- CLI-native operating capability for all PMO Smart Agent interaction scenarios that matter to delivery
- thin UI support where visibility or approvals materially help, without remaining an interaction dependency
- PMO Event Routing for authority-aware handling of issues/events whose destination is initially unclear
- bounded PMO command/control routing sufficient to complete routed resolution loops
- real Claw ↔ Viper delivery exercise
- real validation and acceptance evidence for the delivered game
- enough product reality to count as first delivery proof

## 6.2 Out of scope

To protect closure, V1.8 should avoid becoming a broad platform-expansion release.
The following should remain out of scope unless directly required for first delivery:
- heavy end-user-facing UI expansion
- polished consumer-grade training dashboard breadth
- broad multi-game support
- large-scale portfolio operations
- commercial launch/store/promotion pipeline
- formal Publish/Subscribe (Pub/Sub) infrastructure as a generalized platform mechanism
- autonomous PMO maturity claims that belong to V1.9
- company-scale autonomy claims that belong to V2.0

## 6.3 Important boundary note

V1.8 is **first delivery proof**, not final market-ready product maturity.

It must prove that the production system can produce and deliver the first real AI-native game.
It does not need to prove:
- polished end-user platform maturity
- broad user self-service completeness
- final commercial packaging depth
- autonomous operating company behavior

---

## 7. Artifact and evidence implications

V1.8 should still use the V1.7 artifact spine, but now with delivery-grade evidence.

At minimum, evidence should include:
- Game Brief
- Game Specification
- Production Handoff Package
- Build/output candidate evidence
- Validation / Test Record
- Game Delivery Package
- production queue / status trace showing actual movement
- CLI command or command-set definition sufficient to show real operating capability
- evidence that at least one real Agent participant completed the game through the defined agent-facing interface
- evidence that PMO Event Routing handled at least one real ownership/handling uncertainty case through a bounded routed-resolution loop

If a thin UI exists, it should be demonstrated as an oversight companion, not mistaken for the primary proof of operation.

---

## 8. V1.8 closure test

V1.8 should not close unless the following can all be answered **yes**:

1. Was a first real AI-native game delivered through the defined governed structure?
2. Is the delivered game materially agent-playable rather than only conceptually described?
3. Can at least one real Agent participant actually play and complete the game through the defined agent-facing interface?
4. Did Claw and Viper function together through a real handoff/execution path where needed?
5. Can all required PMO Smart Agent interaction scenarios be performed through CLI commands without depending on UI interaction?
6. Does the CLI also support the specific command set required for the first AI-native game itself?
7. Did PMO Event Routing successfully handle at least one real ownership/handling uncertainty case through a bounded routed-resolution loop?
8. Is UI dependency kept thin enough that the release is not blocked by heavy frontend buildout?
9. Are governance and PMO oversight still explicit at the right authority points?
10. Is the release strong enough to count as first-product proof without borrowing closure language from later versions?

If any of these are still theoretical, V1.8 is not complete.

---

## 9. Strategic role in the version ladder

The version ladder should now be read like this:
- **V1.7** = foundation and governed workflow proof
- **V1.8** = first AI-native game delivery proof, CLI-first, with PMO Event Routing
- **V1.9** = PMO coordination maturity under more live operating load, including formal Publish/Subscribe (Pub/Sub) mechanism
- **V2.0** = autonomous game company operation

This keeps the ladder disciplined.

V1.7 proves the production foundation.
V1.8 proves the foundation can actually deliver a first product.
V1.9 proves the coordinating operating layer becomes mature under real conditions.
V2.0 proves autonomous continuity.

---

## 10. Final note

The key sentence for V1.8 is:

> **V1.8 proves that the Claw Studio + Viper system can deliver the first real AI-native game through a governed CLI-first operating model, without requiring heavy UI expansion to make routine production work possible.**

That is the cleanest foundation for the next step.

### Document-layer note
The Foundation Document establishes the direction and boundary.
The exact game completion criteria, exact CLI command set, exact PMO Event Routing proof cases, exact UI-to-CLI migration inventory, explicit game-quality exclusions, and exact Claw Studio Agent/component creation requirements should be fully elaborated in the Scope / Specification / Testcase documents rather than over-expanded here.

---

## 11. Messaging mechanism boundary note

To avoid overlap/confusion between V1.8 and V1.9, the messaging boundary should be read as follows:

### V1.8 — PMO Event Routing
V1.8 introduces a governed routing mechanism for cases where an Agent or Sub-agent encounters an issue, request, or exception but does not know the correct responsible destination.

In those cases:
- the event is sent to PMO
- PMO determines ownership/handling destination
- PMO routes the event to the correct Agent, Sub-agent, or Alex

This solves an authority/ownership uncertainty problem.
It is routing-led, governance-visible, and bounded.

### V1.9 — Formal Publish/Subscribe (Pub/Sub)
V1.9 may later introduce a formal Publish/Subscribe mechanism for structured event distribution where publishers emit known event types and specific subscribers or subscriber groups receive them.

This solves a distribution problem rather than an ownership-resolution problem.
It is more suitable for:
- cluster-internal broadcasting
- designated-consumer event delivery
- reusable event channels/topics
- more mature multi-agent coordination patterns

### Boundary rule
PMO Event Routing is for authority/ownership uncertainty and governed coordination.
Formal Pub/Sub is for structured event distribution after ownership/routing rules are already stable.
