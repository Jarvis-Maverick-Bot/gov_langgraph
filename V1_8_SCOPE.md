# V1.8 Scope Draft

## 1. Purpose

This document defines the bounded scope of V1.8 based on the approved V1.8 Foundation Document.

V1.8 is not a broad platform-maturity release.
It is a focused first-delivery release.

### V1.8 objective
**Deliver the first real AI-native game through the Claw Studio + Viper operating model using a CLI-native operating surface, with only a thin human oversight / governance layer where needed.**

The scope below must stay tightly aligned to that objective.

---

## 2. In-scope outcome

By the end of V1.8, the system should be able to support one real AI-native game delivery path where:
- the primary intended players are AI agents
- the game is actually executable / playable, not merely documented
- at least one real Agent participant can actually play and complete the game through the defined interface
- Claw Studio + Viper function together through a real delivery path
- PMO Smart Agent operations required for delivery are handled through CLI commands rather than UI interact# V1.8 Scope Draft

## 1. Purpose

This document defines the bounded scope of V1.8 based on the approved V1.8 Foundation Document.

V1.8 is not a broad platform-maturity release.
It is a focused first-delivery release.

### V1.8 objective
**Deliver the first real AI-native game through the Claw Studio + Viper operating model using a CLI-native operating surface, with only a thin human oversight / governance layer where needed.**

The scope below must stay tightly aligned to that objective.

---

## 2. In-scope outcome

By the end of V1.8, the system should be able to support one real AI-native game delivery path where:
- the primary intended players are AI agents
- the game is actually executable / playable, not merely documented
- at least one real Agent participant can actually play and complete the game through the defined interface
- Claw Studio + Viper function together through a real delivery path
- PMO Smart Agent operations required for delivery are handled through CLI commands rather than UI interaction dependency
- PMO Event Routing can resolve at least one real ownership/handling uncertainty case through a bounded routed-resolution loop
- the work is structurally decomposed from Functional Block → Feature → Function before sprint backlog selection begins
- the required artifacts and evidence exist in real form

This is the release outcome.

---

## 3. Scope structure rule

For V1.8, every major in-scope functional area must be decomposed using the following structure:

- **Functional Block** = a major delivery capability or major release work area
- **Feature** = a coherent capability set within a Functional Block
- **Function** = a concrete behavior, command, action, or bounded system capability that can later support implementation planning, testing, and acceptance

This is a mandatory V1.8 structuring rule.
No major Functional Block should remain only as a headline label.
Each major block must be broken down into Features, and each Feature into Functions.

---

## 4. Core in-scope Functional Blocks

## Functional Block 1. First AI-native game delivery proof

- **Feature 1.1 Game definition and completion model
  - **Function 1.1.1 Define one bounded real game concept for V1.8
  - **Function 1.1.2 Define the game objective and completion condition
  - **Function 1.1.3 Define the game rules and interaction constraints
  - **Function 1.1.4 Define what counts as successful Agent completion
  - **Function 1.1.5 Define the minimum acceptable playable form for delivery proof

- **Feature 1.2 Executable/playable game output
  - **Function 1.2.1 Produce a real executable or runnable game output
  - **Function 1.2.2 Ensure the delivered output is not merely a paper design or static artifact set
  - **Function 1.2.3 Ensure the game can be invoked through the intended interaction interface
  - **Function 1.2.4 Ensure the build/output can be reviewed and replayed for validation

- **Feature 1.3 Agent gameplay proof
  - **Function 1.3.1 Select at least one real Agent participant for gameplay proof
  - **Function 1.3.2 Execute at least one real Agent play/completion run
  - **Function 1.3.3 Capture evidence that the Agent could actually complete the game
  - **Function 1.3.4 Distinguish real completion proof from simulated or theoretical completion claims

---

## Functional Block 2. Agent game interaction via standardized CLI

- **Feature 2.1 Game command surface definition
  - **Function 2.1.1 Define the first standardized CLI command set for Agent game interaction
  - **Function 2.1.2 Define command inputs, outputs, and expected invocation shape
  - **Function 2.1.3 Define minimum command coverage required for gameplay/completion
  - **Function 2.1.4 Define command behavior expectations and failure handling boundaries

- **Feature 2.2 Agent-facing gameplay operations
  - **Function 2.2.1 Support game start/initiation through CLI
  - **Function 2.2.2 Support in-game action submission through CLI
  - **Function 2.2.3 Support status/state retrieval through CLI
  - **Function 2.2.4 Support game completion/result retrieval through CLI
  - **Function 2.2.5 Support bounded error reporting for failed or invalid game actions

- **Feature 2.3 Gameplay proof usability
  - **Function 2.3.1 Ensure the CLI is usable by a real Agent, not only by a human operator
  - **Function 2.3.2 Ensure the command surface is stable enough for repeatable validation
  - **Function 2.3.3 Ensure the command set is explicit enough to support test and acceptance evidence

---

## Functional Block 3. PMO Smart Agent CLI-native operating path

- **Feature 3.1 PMO action inventory migration
  - **Function 3.1.1 Identify the PMO Smart Agent interaction scenarios required for V1.8 delivery
  - **Function 3.1.2 Identify which of those scenarios currently depend on UI interaction
  - **Function 3.1.3 Define the CLI replacement path for each required delivery-critical scenario

- **Feature 3.2 PMO command surface
  - **Function 3.2.1 Support work-item or delivery-item creation/initiation via CLI
  - **Function 3.2.2 Support artifact submission/update via CLI
  - **Function 3.2.3 Support stage transition request/recording via CLI
  - **Function 3.2.4 Support validation-result recording via CLI
  - **Function 3.2.5 Support blocker/escalation signaling via CLI
  - **Function 3.2.6 Support delivery candidate packaging or registration via CLI
  - **Function 3.2.7 Distinguish governance/record commands from execution/orchestration commands at the CLI contract level
  - **Function 3.2.8 Ensure command names truthfully reflect whether they record intent, dispatch real action, or retrieve results

- **Feature 3.3 CLI-first operational proof
  - **Function 3.3.1 Demonstrate that required PMO operations can be completed without UI dependency
  - **Function 3.3.2 Demonstrate that the CLI path is real operating infrastructure, not demo-only scaffolding
  - **Function 3.3.3 Demonstrate that UI remains optional or oversight-oriented for routine delivery-driving work
  - **Function 3.3.4 Ensure execution-labeled commands trigger tangible bounded action or fail explicitly
  - **Function 3.3.5 Ensure observation/result commands can return meaningful runtime status and outcome

---

## Functional Block 4. Thin oversight / governance UI

- **Feature 4.1 Visibility surfaces
  - **Function 4.1.1 Provide workflow/status visibility where materially useful
  - **Function 4.1.2 Provide queue/progress visibility where materially useful
  - **Function 4.1.3 Provide artifact/review visibility where materially useful

- **Feature 4.2 Governance authority surfaces
  - **Function 4.2.1 Provide human approval surfaces at required governance points
  - **Function 4.2.2 Provide escalation/review visibility for governance-relevant cases
  - **Function 4.2.3 Provide lightweight inspection/comparison surfaces if needed for review

- **Feature 4.3 UI dependency control
  - **Function 4.3.1 Ensure UI is not the main operating dependency for delivery-driving work
  - **Function 4.3.2 Ensure UI remains thin enough that V1.8 closure is not blocked by heavy frontend buildout
  - **Function 4.3.3 Define what UI surfaces are retained versus deliberately excluded in V1.8

---

## Functional Block 5. PMO Event Routing

- **Feature 5.1 Routed-event intake
  - **Function 5.1.1 Support submission of an issue/request/exception when ownership is unclear
  - **Function 5.1.2 Capture the initiating Agent/Sub-agent and routing context
  - **Function 5.1.3 Record the event in a governance-visible way

- **Feature 5.2 Ownership/handling determination
  - **Function 5.2.1 Determine the correct responsible destination through explicit routing logic
  - **Function 5.2.2 Distinguish destination types such as Agent, Sub-agent, PMO, or Alex
  - **Function 5.2.3 Preserve authority-awareness during routing decisions
  - **Function 5.2.4 Keep routing deterministic/rule-led rather than inference-led for V1.8

- **Feature 5.3 Routed resolution completion
  - **Function 5.3.1 Route the event to the selected responsible destination
  - **Function 5.3.2 Support result return from the destination back into PMO routing flow
  - **Function 5.3.3 Relay the resolved result back to the initiating Agent/Sub-agent
  - **Function 5.3.4 Capture evidence that at least one real routed-resolution loop completed successfully

---

## Functional Block 6. Bounded PMO command/control loop

- **Feature 6.1 Operational control actions
  - **Function 6.1.1 Launch bounded sub-agent tasks where approved
  - **Function 6.1.2 Invoke commands where approved within the routing/control surface
  - **Function 6.1.3 Request task or work status where needed
  - **Function 6.1.4 Pause tasks where needed
  - **Function 6.1.5 Terminate tasks where needed and authorized

- **Feature 6.2 Coordination return path
  - **Function 6.2.1 Relay returned results from commanded actions
  - **Function 6.2.2 Return the final routed result to the initiating requester
  - **Function 6.2.3 Preserve governance visibility across the routed control loop
  - **Function 6.2.4 Expose meaningful execution progress states for bounded dispatched tasks
  - **Function 6.2.5 Expose completion, failure, cancellation, timeout, or waiting states truthfully rather than only request-state markers

- **Feature 6.3 Boundedness and authority control
  - **Function 6.3.1 Keep command/control actions within explicitly approved V1.8 boundaries
  - **Function 6.3.2 Prevent the control loop from expanding into broad autonomous PMO claims
  - **Function 6.3.3 Keep the mechanism coordination-scoped rather than platform-generalized
  - **Function 6.3.4 Separate work-item governance state from runtime execution state so command/control semantics remain clean

---

## Functional Block 7. Claw Studio Agent seats/components required for delivery

- **Feature 7.1 Required seat/component definition
  - **Function 7.1.1 Identify the minimum Claw Studio Agent seats/components required for V1.8 delivery
  - **Function 7.1.2 Distinguish required seats/components from optional or future seats/components
  - **Function 7.1.3 Define the role of each required seat/component in the V1.8 delivery path

- **Feature 7.2 Seat/component creation and readiness
  - **Function 7.2.1 Create the required Claw Studio Agent seats/components
  - **Function 7.2.2 Confirm those seats/components are usable in the real delivery path
  - **Function 7.2.3 Ensure the created seats/components match the intended operating structure

- **Feature 7.3 Governance review of created seats/components
  - **Function 7.3.1 Expose the created seats/components for Governance Layer review
  - **Function 7.3.2 Distinguish approved operating structure from draft or unreviewed setup
  - **Function 7.3.3 Prevent unreviewed seat/component sprawl from entering accepted V1.8 structure

---

## Functional Block 8. Real Claw ↔ Viper handoff and return path

- **Feature 8.1 Handoff initiation
  - **Function 8.1.1 Define the real trigger condition for Claw to hand work to Viper
  - **Function 8.1.2 Package the handoff in a usable operational form
  - **Function 8.1.3 Ensure the handoff contains the required engineering-enablement context

- **Feature 8.2 Viper execution response
  - **Function 8.2.1 Receive the handoff on the Viper side
  - **Function 8.2.2 Execute the bounded engineering-enablement work required
  - **Function 8.2.3 Return outputs/results back across the delivery boundary

- **Feature 8.3 Real boundary proof
  - **Function 8.3.1 Exercise the handoff in actual work rather than paper-only definition
  - **Function 8.3.2 Capture evidence that the cross-team boundary worked in practice
  - **Function 8.3.3 Confirm the return path is real, not omitted

---

## Functional Block 9. Validation and acceptance evidence

- **Feature 9.1 Validation evidence generation
  - **Function 9.1.1 Produce a real validation/test record for the delivered game
  - **Function 9.1.2 Produce evidence for Agent gameplay/completion proof
  - **Function 9.1.3 Produce evidence for PMO CLI operation proof
  - **Function 9.1.4 Produce evidence for PMO Event Routing proof

- **Feature 9.2 Acceptance support
  - **Function 9.2.1 Define the minimum evidence set required for honest V1.8 acceptance
  - **Function 9.2.2 Ensure acceptance can be based on real evidence rather than broad claims
  - **Function 9.2.3 Preserve reviewability of the evidence chain

- **Feature 9.3 Closure integrity
  - **Function 9.3.1 Prevent closure on theoretical-only completion claims
  - **Function 9.3.2 Prevent closure if core proof areas remain untested or weakly evidenced
  - **Function 9.3.3 Ensure V1.8 can close without borrowing proof language from later versions

---

## Functional Block 10. Delivery-grade artifact chain

- **Feature 10.1 Core delivery artifacts
  - **Function 10.1.1 Produce Game Brief
  - **Function 10.1.2 Produce Game Specification
  - **Function 10.1.3 Produce Production Handoff Package
  - **Function 10.1.4 Produce Build/output candidate evidence
  - **Function 10.1.5 Produce Validation/Test Record
  - **Function 10.1.6 Produce Game Delivery Package

- **Feature 10.2 Operational traceability artifacts
  - **Function 10.2.1 Produce production queue/status trace showing actual work movement
  - **Function 10.2.2 Produce CLI command or command-set definition showing real operating capability
  - **Function 10.2.3 Produce routed-event evidence where PMO Event Routing is exercised

- **Feature 10.3 Artifact completeness and integrity
  - **Function 10.3.1 Ensure the artifact chain supports review, validation, and acceptance
  - **Function 10.3.2 Ensure artifacts are real and materially connected to actual delivery work
  - **Function 10.3.3 Prevent artifact-only formalism from being mistaken for delivery proof

---

## Functional Block 11. Structured delivery decomposition model

- **Feature 11.1 Scope decomposition rule
  - **Function 11.1.1 Require every major Functional Block to be broken into Features
  - **Function 11.1.2 Require every Feature to be broken into Functions
  - **Function 11.1.3 Prevent major work from remaining at vague headline level

- **Feature 11.2 Planning decomposition rule
  - **Function 11.2.1 Require delivery work to be decomposed before sprint backlog selection begins
  - **Function 11.2.2 Prevent direct jump from high-level scope block to sprint implementation
  - **Function 11.2.3 Ensure Functions are concrete enough to support selection into sprint work

- **Feature 11.3 Governance and planning usability
  - **Function 11.3.1 Make the decomposition reviewable by Governance/Nova
  - **Function 11.3.2 Make the decomposition usable by Jarvis for implementation planning
  - **Function 11.3.3 Make the decomposition usable for later testcase and acceptance design

---

## 5. Priority-decision items still needing explicit closure

These items are directionally in-scope, but still need explicit precision/closure decisions in later refinement:

1. exact CLI command inventory for PMO Smart Agent
2. exact CLI command inventory for game-side Agent integration
3. minimum required routed-event scenarios for PMO Event Routing proof
4. minimum required Claw Studio Agent/component inventory
5. minimum governance/approval UI surfaces that remain after CLI migration
6. exact form of validation evidence for Agent-completion proof
7. exact form of delivery package for the first real AI-native game
8. exact acceptance threshold for “materially playable” game output
9. exact acceptance threshold for “real routed-resolution loop” sufficiency
10. exact execution lifecycle and result-return contract for bounded PMO command/control tasks
11. final command-surface split between governance commands, execution commands, and observation/result commands
12. naming convention and module boundary rule for peer architectural folders/components

---

## 6. Out of scope

To protect closure, the following are explicitly out of scope for V1.8 unless directly required for first real delivery proof:

- formal Publish/Subscribe (Pub/Sub) as generalized infrastructure
- multi-game portfolio operation
- mature PMO coordination platform breadth beyond minimum delivery need
- broad end-user UI expansion
- polished consumer-facing platform experience
- AI-powered routing inference as the primary routing mechanism
- autonomous PMO maturity claims
- company-scale autonomy
- commercial launch/store/promotion workflow
- high-fidelity art/audio polish as a closure requirement
- advanced gameplay balancing / fun optimization as a closure requirement
- consumer-ready product polish as a closure requirement

---

## 7. Scope boundary statement

V1.8 is a **first real delivery release**, not a broad platform-completion release.

It should prove:
- one real AI-native game can be delivered
- Agents can interact with and complete that game through a defined CLI-based interface
- PMO Smart Agent can operate through CLI-native delivery interactions
- PMO Event Routing can resolve real routing uncertainty cases
- bounded PMO command/control actions have truthful semantics, observable progress, and result return
- Claw + Viper can function together in real delivery work

It does not need to prove:
- generalized messaging infrastructure maturity
- polished UI/platform maturity
- broad portfolio management
- autonomous company operation
- consumer-grade game polish

---

## 8. Success criteria

V1.8 scope is successful only if:
- the defining objective is materially realized
- the delivered game is real and executable
- at least one real Agent participant can complete it through the defined interface
- the required CLI-native operation path is real
- PMO Event Routing is real in at least one bounded routed-resolution case
- bounded execution-bearing CLI actions are truthful, observable, and capable of returning meaningful results
- the Claw ↔ Viper boundary is exercised in actual delivery
- the Functional Block → Feature → Function decomposition is real and used before sprint backlog construction
- the artifact/evidence chain is sufficient for honest acceptance
- the result is strong enough to support V1.9 without reopening the V1.8 foundation

---

## 9. Final scope rule

No item should enter V1.8 unless it directly helps prove one of these:
- first real AI-native game delivery is real
- Agent game interaction through standardized CLI is real
- PMO Smart Agent CLI-native operation is real
- PMO Event Routing is real
- bounded PMO execution/control semantics are real rather than record-only placeholders
- Claw + Viper delivery cooperation is real
- the first delivery evidence chain is real

If an item does not help prove one of those, it should stay out.

- **Feature 7.4 V1.8 instantiation vs. skill-definition split
  - **Function 7.4.1 Define all 7 candidate roles (Planner, Architect, TDD, CodeReviewer, Security, Docs, DBExpert) as skill specifications with clear capability definitions
  - **Function 7.4.2 Instantiate Planner and TDD as live sub-agents in V1.8 to prove the pattern
  - **Function 7.4.3 Keep Architect, CodeReviewer, Security, Docs, DBExpert as documented skill specs only — target for V1.9 instantiation
  - **Function 7.4.4 Prove the Planner -> TDD -> code handoff chain works in actual V1.8 delivery
  - **Function 7.4.5 Ensure skill-spec definitions are concrete enough to support later V1.9 instantiation without re-architecture
