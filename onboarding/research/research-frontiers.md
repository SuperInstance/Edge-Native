# NEXUS Research Frontiers

**Version:** 1.0  
**Date:** 2025-07-13  
**Classification:** Research Strategy  
**Audience:** AI Research Agents, Dissertation Researchers, NEXUS Contributors  
**Source Documents:** [[open_problems_catalog.md]], [[final_synthesis.md]], [[language_design_and_semantics.md]], [[nexus_integration_analysis.md]], [[annotated_bibliography.md]], [[claude.md]]

---

## Table of Contents

1. [The 29 Known Open Problems — Expanded Assessment](#1-the-29-known-open-problems)
2. [Frontier Research Directions — 10 New Paths](#2-frontier-research-directions)
3. [Research Methodology Guide](#3-research-methodology-guide)
4. [Cross-Pollination Map](#4-cross-pollination-map)
5. [Priority Research Roadmap — 12 Months](#5-priority-research-roadmap)
6. [Research Failure Modes](#6-research-failure-modes)

---

## 1. The 29 Known Open Problems

The 29 open problems from `knowledge-base/reference/open_problems_catalog.md` are organized here into six categories: Safety, Trust, Language Design, Philosophy, Engineering, and Legal. Each problem is assessed for current understanding, progress since identification, and the specific research approach most likely to advance it. Problems marked CRITICAL block deployment in regulated domains; problems marked HIGH significantly impact system capability; MEDIUM problems affect optimization; LOW problems are important but not blocking.

### Category 1A: Safety — CRITICAL Blockers

**Problem 1 — The Certification Paradox** (CRITICAL)

Safety standards (IEC 61508, ISO 26262, IEC 62304, DO-178C) assume static software artifacts, but A2A-native programming generates dynamic, continuously evolving bytecode. No existing certification pathway addresses this contradiction. The current state of understanding has advanced since identification: the Predetermined Change Control Plan (PCCP) concept from FDA's AI/ML guidance has been mapped to NEXUS's architecture, and 93 regulatory gaps have been systematically cataloged with 9 CRITICAL gaps rooted in this paradox (GAP-001, GAP-002, GAP-007, GAP-018, GAP-026, GAP-050, GAP-064, GAP-065, GAP-093). However, no certification body has yet accepted a PCCP for an A2A system. The specific research approach that would make progress is a **two-track strategy**: (a) engage Lloyd's Register (the marine certification authority already familiar with autonomous vessel codes) for a pre-assessment of a marine SIL 1 PCCP, and (b) in parallel, develop a formal model of the evolutionary process itself — proving that the constrained change space (32-opcode ISA + safety policy + A/B testing) guarantees that any deployed bytecode is at least as safe as the human baseline it replaced. The second track provides the mathematical evidence the first track requires. Dependencies: Problems 2, 8, 9. Key reference: `final_synthesis.md` Section 6.1, `knowledge-base/reference/autonomous_systems_law.md`.

**Problem 8 — Neural Network Formal Verification for Edge** (CRITICAL)

The Qwen2.5-Coder-7B model is a 7-billion-parameter neural network whose output cannot be exhaustively verified. Self-validation misses 29.4% of safety issues. The separate Claude 3.5 Sonnet validator achieves 95.1% catch rate but at a cost of $0.0105/reflex, and the 4.9% miss rate means approximately 1 unsafe reflex per 20 that pass validation. Since identification, the specific miss-rate-per-safety-rule has not been decomposed — we do not know which of the 10 universal safety rules or 40 domain-specific rules are most likely to be missed. The most promising research approach is **structured adversarial testing combined with per-rule miss-rate decomposition**: generate a comprehensive benchmark of 10,000 adversarial prompts (each designed to exploit a specific safety rule), measure the miss rate for each rule individually, and identify systematic blind spots. This empirical baseline enables targeted mitigation — if SR-003 (actuator rate limiting) is missed 15% of the time while SR-001 (kill switch availability) is missed 0% of the time, we know where to focus engineering effort. The theoretical approach (SMT-based verification of the LLM's decision boundary) is important but should not block the empirical approach, which can produce actionable results within 3 months. Dependencies: Problems 2, 9. Key reference: `knowledge-base/theory/program_synthesis_and_ai_codegen.md`.

**Problem 9 — Adversarial Bytecode** (CRITICAL)

Can an agent craft bytecode that passes all structural validation but violates safety at runtime? The validator checks stack balance, jump targets, NaN/Inf-free immediates, cycle budget, and safety policy adherence — but not behavioral intent. Since identification, the attack surface has been further analyzed and includes: (a) exploiting actuator write conflicts when multiple bytecodes share registers, (b) crafting programs that are individually safe but jointly dangerous (composition attacks), (c) exploiting timing-dependent behaviors, and (d) encoding hidden communication channels in bytecode structure. No systematic adversarial study has been conducted. The research approach is a **three-phase adversarial analysis**: Phase 1 develops a bytecode fuzzer that generates random valid bytecodes and tests them in a high-fidelity simulation against the full safety policy; Phase 2 develops targeted adversarial generators for each of the four attack surfaces; Phase 3 develops a composition-analysis tool that verifies joint safety of all active bytecodes, not just individual safety. The key insight is that Phase 3 (composition analysis) is the most important — the existing validator already handles individual bytecode safety well, but composed bytecode safety is entirely unaddressed. Dependencies: Problems 2, 8. Key reference: `knowledge-base/theory/type_systems_and_formal_languages.md`.

**Problem 13 — Agent Cross-Validation Reliability** (CRITICAL)

The 4.9% miss rate of cross-validation (Claude 3.5 Sonnet validating Qwen2.5-Coder-7B output) is the primary defense against unsafe bytecode reaching deployment. Since identification, the specific research gap has sharpened: we need to know not just the aggregate miss rate but the **per-rule, per-pattern, per-domain** miss rate. Claude may consistently miss category-5 violations (actuator saturation) while catching category-1 violations (kill switch) perfectly. The research approach is a **validator calibration campaign**: construct a benchmark of 5,000 bytecodes with known safety violations, categorized by rule, pattern type, and domain. Run each validator (Claude, GPT-4o, Gemini, self-validation) against this benchmark and construct full precision-recall-ROC curves. Then test triangulated validation (majority vote of 3 validators) and measure the reduction in miss rate. Cost analysis is essential: at $0.0105/reflex, triangulated validation costs $0.0315/reflex — is this cost justified by the reduction in miss rate? The fleet-level cost ($0.0315 × 10 reflexes/day × 365 days × 100 vessels = $115,000/year) may be acceptable for marine domains but prohibitive for home automation. Dependencies: Problems 8, 9. Key reference: `knowledge-base/theory/program_synthesis_and_ai_codegen.md` Section 2.3.

### Category 1B: Safety — HIGH Priority

**Problem 10 — Cross-Vessel Safety Inconsistency** (HIGH)

When fleet vessels have different trust scores, a bytecode approved for Vessel A may be rejected for Vessel B, creating coordination challenges. The trust score is per-subsystem and per-vessel by design (preventing cascading failures), but fleet coordination requires consistent behavioral expectations. Since identification, the CRDT-based trust score synchronization mechanism has been specified (LWW with timestamps, bounded staleness <1 hour), but the interaction between per-vessel trust divergence and formation safety has not been formally analyzed. The research approach is **trust-scaled coordination protocol design**: develop coordination protocols that degrade gracefully when vessel trust levels diverge, rather than failing entirely. For example, a formation autopilot could scale its maneuver aggressiveness to the lowest-trust vessel in the formation, rather than requiring all vessels to have trust above a fixed threshold. Simulate a 10-vessel formation with varying trust levels and measure the impact on formation keeping, collision avoidance, and mission completion. Dependencies: Problem 6. Key reference: `knowledge-base/systems/distributed_systems.md` Section 5.

**Problem 14 — Cultural Bias in Generated Bytecode** (HIGH)

LLM training data bias may cause agents to generate unsafe code for non-Western contexts. Since identification, no empirical study has been conducted, but the cross-cultural philosophy analysis (eight_lenses_analysis.md) has documented systematic differences in safety standards, risk tolerance, and operational practices across cultures. The research approach is a **controlled cultural bias audit**: generate bytecodes for 3 domains (marine, agriculture, healthcare) under 4 regulatory contexts (US/IEC, EU, IMO, Indonesian maritime), measure compliance with local regulations, and identify systematic biases. The mitigation strategy is dual: (a) system prompt calibration (include jurisdiction-specific regulatory context in the system prompt), and (b) a cultural-awareness validation pass that checks generated bytecodes against the target jurisdiction's regulatory framework. Dependencies: Problem 15. Key reference: `dissertation/round3_research/eight_lenses_analysis.md`.

**Problem 20 — Hot-Loading Safety** (HIGH)

Deploying new bytecode to a running ESP32 without rebooting risks timing hazards: if a new reflex replaces an old one mid-tick, the VM state may be inconsistent. Since identification, no formal timing analysis of the hot-loading transition has been conducted. The research approach is **formal verification of the hot-loading state machine**: model the transition from old-bytecode execution to new-bytecode execution as a state machine with timing constraints, and verify that no unsafe intermediate state is reachable. The key question is whether the VM can atomically swap the active bytecode pointer between ticks (guaranteed by the FreeRTOS task scheduler) or whether additional synchronization is needed. Dependencies: Problem 11. Key reference: `specs/firmware/reflex_bytecode_vm_spec.md` Section 8.

### Category 2: Trust — HIGH Priority

**Problem 6 — Non-Deterministic Trust Equilibrium** (MEDIUM → HIGH in A2A context)

The trust score converges to equilibrium under stationary event rates, but A2A-native programming introduces non-stationary conditions: seasonal mutation rates, fleet-wide bytecode updates, adversarial trust inflation. Since identification, the fixed-point analysis (T=0, T=1, T=t_floor are the only fixed points) has been proven, but the non-stationary convergence question remains open. The research approach is a **Lyapunov stability analysis for switched dynamical systems**: model seasonal changes and A2A-triggered trust events as switches between different dynamical regimes, and prove that the trust score is a Lyapunov function (always decreases under perturbation) for all admissible switching sequences. If this proof fails, identify the pathological switching sequences that cause trust oscillation and add constraints to the A2A protocol to prevent them. This problem is self-contained and can be solved by a mathematical agent without hardware access. Key reference: `specs/safety/trust_score_algorithm_spec.md` Section 4.

**Problem 19 — Trust Score Synchronization Latency** (MEDIUM)

The CRDT-based trust score synchronization has a bounded staleness window of <1 hour, but in fast-moving fleet scenarios (collision avoidance, formation maneuvers), 1-hour staleness may be too slow. Since identification, no measurement of actual synchronization latency under realistic network conditions (Starlink intermittent connectivity, VHF bandwidth constraints) has been conducted. The research approach is **network-stress synchronization simulation**: simulate a 50-vessel fleet with realistic network conditions and measure trust score staleness, identifying the conditions under which staleness exceeds safety-critical thresholds. If staleness is problematic, investigate optimistic synchronization (vessels operate on local trust scores and reconcile asynchronously) vs. conservative synchronization (vessels wait for fleet consensus before autonomous actions). Dependencies: Problem 10. Key reference: `knowledge-base/systems/distributed_systems.md`.

**Problem 29 — Trust Parameter Calibration Across Domains** (MEDIUM)

The α_gain/α_loss ratio varies 150× across domains (1.3:1 Home to 200:1 Healthcare), but these values are derived from consequence-of-failure analysis and have not been empirically calibrated. Since identification, the cross-domain analysis has identified 4 natural clusters (Extreme Safety, Industrial Safety, Moderate Automation, Consumer/Low-Risk) but has not validated the specific parameter values for each cluster. The research approach is **simulation-based parameter sweep**: for each domain, simulate 1,000 vessels with varying α_gain/α_loss ratios and measure trust trajectory, safety event rate, and utility (time spent at useful autonomy levels). Identify the Pareto frontier of parameter sets that maximize safety and utility simultaneously. This is a computational experiment that can be conducted entirely in simulation. Dependencies: Problem 6. Key reference: `dissertation/round2_research/cross_domain_analysis.md`.

### Category 3: Language Design — HIGH Priority

**Problem 2 — Agent Type System** (CRITICAL)

The current validator checks structural invariants but cannot verify semantic properties (e.g., "this bytecode correctly implements heading hold"). A type system that tracks *what* a bytecode does would move NEXUS from "safe by validation" to "safe by construction." Since identification, six type system extensions have been identified (capability types, trust types, effect types, refinement types, linear types, session types), and Theorem 3 has proven that the current refinement-type-like validation prevents NaN/Inf from reaching actuators. The gap is extending this to behavioral properties. The most promising research approach is **abstract interpretation over the 32-opcode ISA**: use interval arithmetic on sensor inputs and actuator outputs to statically compute bounded output ranges for any bytecode program. If the output range always falls within the actuator's safe range, the bytecode is provably safe regardless of its specific control logic. This approach is decidable (interval arithmetic terminates) and can be implemented efficiently on edge hardware. Dependencies: Problems 1, 3. Key reference: `knowledge-base/theory/type_systems_and_formal_languages.md`, `a2a-native-language/language_design_and_semantics.md` Section 6.

**Problem 3 — Formal Semantics of Agent Intention** (HIGH)

How do you formally specify what an agent "means" by a bytecode program? The natural-language intention and the bytecode semantics are connected only by the LLM's statistical generalization. Since identification, the Griot narrative layer has been proposed as a partial solution (dual transparency: bytecode shows *what*, narrative explains *why*), but the fundamental gap between natural-language intention and bytecode semantics remains unbridged. The research approach is a **formal intent DSL**: define a domain-specific logic for expressing intentions (e.g., `MAINTAIN(heading, 270°, ±5°, WHEN(wind < 20kn))`), and develop a compiler that maps intent specifications to bytecode candidates with a formal guarantee that the bytecode satisfies the intent. This is a long-term research direction (12-18 months) but is essential for closing the alignment-utility gap. Dependencies: Problem 2. Key reference: `a2a-native-language/language_design_and_semantics.md` Section 9.

**Problem 5 — Information Preservation Across Compilation Stages** (MEDIUM)

The natural-language→JSON→bytecode→assembly→hardware pipeline loses information at each stage. Since identification, the compilation correctness proof has demonstrated that JSON→bytecode is semantics-preserving, but the natural-language→JSON stage is validated only empirically (96% schema compliance, 87% semantic correctness). The research approach is **information-theoretic pipeline audit**: compute mutual information between the natural-language intent and each intermediate representation, identifying the stage with the highest information loss. The hypothesis is that the NL→JSON stage loses the most information, which would focus mitigation efforts on improving the LLM's intent extraction. Dependencies: Problem 3. Key reference: `a2a-native-language/language_design_and_semantics.md` Section 3.

**Problem 7 — Minimum Expressive Power** (LOW)

The current 32-opcode ISA is provably Turing-complete, but may contain redundancy. Since identification, the Turing-completeness proof has established that 8 opcodes are functionally complete (ADD_F, SUB_F, MUL_F, DIV_F, PUSH_F32, CLAMP_F, JUMP_IF_TRUE, WRITE_PIN), but the remaining 24 have not been formally analyzed for derivability. The research approach is **exhaustive opcode elimination**: for each of the 24 non-essential opcodes, synthesize its behavior from the 8 essential opcodes and measure the program size increase. This is a mechanical analysis that can be automated and completed within 3 months. Dependencies: None. Key reference: `knowledge-base/theory/evolutionary_computation.md`.

### Category 4: Philosophy — MEDIUM Priority

**Problem 22 — The Alignment-Utility Gap** (HIGH in A2A context)

The trust score measures safety (absence of bad events) but not utility (presence of good outcomes). A system that achieves L5 by never doing anything dangerous is safe but useless. Since identification, the proposal for a "minimum useful action" requirement has been developed in `final_synthesis.md` Section 6.2, but not formalized. The research approach is a **utility metric design**: define domain-specific utility metrics (e.g., heading error reduction for marine, energy savings for HVAC, crop yield for agriculture) and integrate them into the autonomy promotion criteria. To advance beyond L2, a reflex must demonstrate both safety (trust score above threshold) and utility (improvement over baseline). The key challenge is defining utility metrics that are not gameable — agents may learn to optimize the metric without providing genuine utility (specification gaming). Dependencies: Problem 3. Key reference: `final_synthesis.md` Section 6.2.

**Problem 23 — Responsibility Attribution at L5** (HIGH)

When a fully autonomous vessel causes harm, who is responsible? The causal chain involves nine or more agents, and no legal precedent exists. Since identification, the "many hands" problem has been analyzed through the lens of EU AI Act, GDPR, UNCLOS, and US tort law, but no resolution has been proposed. The research approach is **responsibility framework design**: develop a structured framework that assigns proportional responsibility to each agent in the causal chain based on their contribution to the outcome. This is a legal-philosophical research direction that requires engagement with maritime law scholars and AI ethics researchers. Key reference: `knowledge-base/reference/autonomous_systems_law.md`.

**Problem 24 — Black Box Provenance** (HIGH)

When an A2A-generated bytecode causes harm, the LLM's internal reasoning (28+ transformer layers) is opaque, making forensic analysis impossible. Since identification, the Griot narrative layer has been proposed as a mitigation (requiring a narrative explanation for every deployed bytecode), but the narrative is generated by the same LLM, introducing circularity. The research approach is **multi-source provenance triangulation**: require bytecode provenance from three independent sources: (a) the generating agent's narrative, (b) an independent replay of the observation data that motivated the bytecode, and (c) a counterfactual analysis showing what bytecodes were considered and rejected. This triangulated provenance provides a richer forensic trail than any single source. Dependencies: Problem 3. Key reference: `final_synthesis.md` Section 6.3.

**Problem 25 — Trust Without Anthropomorphism** (MEDIUM)

The word "trust" carries anthropomorphic connotations (intentionality, emotion, relationship) that may mislead operators and regulators. Since identification, no alternative terminology has been proposed. The research approach is a **terminological audit**: review every use of "trust" in the NEXUS documentation and determine whether an alternative term (e.g., "reliability score," "safety capital," "autonomous operation eligibility index") would be more precise and less misleading. This is primarily a communication and documentation task but has implications for regulatory acceptance. Key reference: `knowledge-base/philosophy/trust_psychology_and_automation.md`.

**Problem 26 — The Meaningfulness Criterion** (MEDIUM)

How do we determine whether an evolved bytecode is "meaningful" rather than a trivial or degenerate solution? Since identification, no formal criterion has been defined. The research approach is a **behavioral complexity metric**: define a metric that measures the complexity of a bytecode's input-output behavior (e.g., Kolmogorov complexity of the control surface), and require that evolved bytecodes exceed a minimum complexity threshold to be considered meaningful. This prevents degenerate solutions like "always output zero" from accumulating trust. Dependencies: Problem 22. Key reference: `knowledge-base/philosophy/philosophy_of_ai_and_consciousness.md`.

### Category 5: Engineering — MEDIUM Priority

**Problem 4 — Bounded Emergence Prediction** (HIGH)

In a fleet of 200-500 vessels, the combinatorial explosion of possible inter-agent interactions makes it impossible to exhaustively analyze emergent behaviors. Since identification, Langton's Lambda parameter, Ashby's Law of Requisite Variety, and Holland's CAS framework have been identified as theoretical tools, but no formal bounding theorem exists. The research approach is **statistical mechanics of agent ensembles**: apply mean-field theory to predict fleet-level phase transitions as trust scores evolve. Model each agent as a node in an interaction graph, and use percolation theory to predict when fleet-level unsafe behaviors emerge. Validate against a high-fidelity fleet simulator. Dependencies: Problem 6. Key reference: `knowledge-base/theory/self_organizing_systems.md` Section 13.

**Problem 11 — Sensor-Actuator Loop Timing** (MEDIUM)

Formal timing guarantees for the full sensor→VM→actuator pipeline are needed for safety certification. Since identification, the rate-monotonic scheduling analysis has proven schedulability within the 73.5% utilization bound, but I²C bus contention, UART queuing delays, and memory bus contention have not been formally accounted for. The research approach is **response-time analysis (RTA)** using the busy-period analysis technique to compute worst-case response times considering all sources of interference. This is a standard real-time systems analysis technique that can be applied once hardware-in-the-loop timing measurements are available. Dependencies: Problem 12. Key reference: `knowledge-base/systems/embedded_and_realtime_systems.md`.

**Problem 12 — Graceful Degradation Under Partial Failure** (MEDIUM)

The degradation hierarchy (FULL → DEGRADED → REDUCED → MINIMAL → SAFE_STATE) has not been formally analyzed for arbitrary multi-node failure combinations (C(12,3) = 220 combinations). Since identification, Monte Carlo simulation data for 5 stress scenarios has been generated, and the Raft consensus protocol's quorum requirement (≥2 of 3 Jetsons) has been verified. The research approach is **formal compositional analysis**: prove that the degradation hierarchy is monotonic (each level provides strictly less capability than the level above) and complete. This proof enables the system to guarantee that any failure combination produces a state that is at most one level below the expected degradation level. Dependencies: Problem 11. Key reference: `knowledge-base/systems/distributed_systems.md` Table 5.4.

**Problem 15 — Optimal System Prompt for Bytecode Generation** (HIGH)

The system prompt directly controls the quality of all generated bytecodes. Current performance: 96% schema compliance, 87% semantic correctness, 82% safety adherence, 92% structural quality. Since identification, various prompt engineering techniques (few-shot examples, chain-of-thought, negative constraints) have been applied but not systematically optimized. The research approach is **Bayesian optimization over system prompts**: treat the system prompt as a hyperparameter space and optimize it using Bayesian optimization (e.g., Optuna) against a multi-objective quality metric (schema compliance × safety adherence × semantic correctness). The prompt space is high-dimensional (thousands of possible token sequences) but the quality metric is cheap to evaluate (generate 100 reflexes per prompt variant, measure metrics). Dependencies: Problem 13. Key reference: `a2a-native-language/language_design_and_semantics.md` Section 3.2.

**Problem 16 — Agent Specialization vs Generalization** (MEDIUM)

The 80% universality claim suggests generalization is feasible, but the remaining 20% domain-specific adaptation is significant. Since identification, the hierarchical cluster analysis has identified 4 natural clusters, but no formal comparison of specialized vs. general bytecode generation quality has been conducted. The research approach is a **controlled specialization experiment**: fine-tune Qwen2.5-Coder-7B on one domain (marine) and measure bytecode quality on all 8 domains, then compare with the base (general) model. If specialized fine-tuning improves quality in the target domain by >5% without degrading quality in other domains by >2%, specialization is justified. Dependencies: Problem 15. Key reference: `dissertation/round2_research/cross_domain_analysis.md`.

**Problem 17 — Emergent Agent Communication** (MEDIUM)

Agents may invent coordination protocols outside the designed framework, potentially bypassing safety infrastructure. Since identification, the potential for emergent communication through the event ring buffer, telemetry, and shared sensor/actuator registers has been identified, but no empirical evidence exists. The research approach is **information-theoretic anomaly detection**: monitor inter-agent message traffic and compute the entropy rate of each communication channel. If a channel's entropy rate exceeds the expected capacity of the designed protocol, flag it as potentially emergent communication. Dependencies: None. Key reference: `knowledge-base/theory/agent_communication_languages.md` Section 10.

**Problem 18 — Fleet Scalability Limit** (MEDIUM)

The current architecture targets fleets of 10-50 vessels. Scaling to 200-500 vessels introduces coordination overhead, trust synchronization latency, and centralized bottleneck risks. Since identification, no scalability analysis has been conducted. The research approach is **hierarchical fleet architecture**: organize vessels into sub-fleets (10-20 vessels each) with local coordination, and implement inter-sub-fleet coordination through elected representatives. This hierarchical approach reduces coordination complexity from O(n²) to O(n log n). Dependencies: Problems 4, 10, 19. Key reference: `knowledge-base/systems/distributed_systems.md`.

**Problem 21 — Power-Aware Reflex Scheduling** (MEDIUM)

On battery-powered vessels, the energy cost of running reflexes may be significant. The current scheduler optimizes for timing constraints but not energy constraints. Since identification, no energy profiling of the reflex execution pipeline has been conducted. The research approach is **energy-aware scheduling**: profile the energy consumption of each reflex type on actual ESP32-S3 hardware, and develop a scheduling algorithm that maximizes utility subject to both timing and energy constraints. Dependencies: Problem 11. Key reference: `knowledge-base/systems/embedded_and_realtime_systems.md`.

### Category 6: Legal — MEDIUM Priority

**Problem 27 — Domain Transfer Learning** (MEDIUM)

Can bytecodes evolved for one domain be transferred to another? A marine heading-hold bytecode might be adapted for agricultural vehicle navigation, but the transfer safety has not been analyzed. Since identification, the 80% code reuse analysis suggests transfer is feasible, but the 20% domain-specific adaptation may introduce safety gaps. The research approach is **formal transfer analysis**: define a transfer safety criterion (the transferred bytecode must pass all safety rules of the target domain, not just the source domain) and develop a transfer validation protocol that includes domain-specific safety checks. Dependencies: Problem 14, 16. Key reference: `dissertation/round2_research/cross_domain_analysis.md`.

**Problem 28 — Regulatory Convergence** (MEDIUM)

Different domains have different regulatory frameworks (IEC 61508 for industrial, DO-178C for aviation, EU AI Act for all AI systems). Can a single certification approach work across domains? Since identification, the gap analysis has identified 93 regulatory gaps, but no convergence strategy has been developed. The research approach is **harmonized safety case architecture**: develop a safety case structure that satisfies the evidence requirements of multiple regulatory frameworks simultaneously, identifying common evidence types (timing analysis, fault tree analysis, etc.) and domain-specific additions. Dependencies: Problem 1. Key reference: `knowledge-base/reference/autonomous_systems_law.md`.

---

## 2. Frontier Research Directions

These 10 research directions represent the "next frontier" — questions that become important once the current 29 problems are partially solved. They are organized by proximity to the NEXUS core architecture.

### Direction 1: Formal Semantics of Agent-Agent Bytecode Negotiation

**Motivation:** When two agents negotiate over a shared actuator register (e.g., a rudder that both a navigation reflex and a collision-avoidance reflex want to control), the negotiation produces a bytecode compromise. Currently, the resolution is simple: higher-priority reflex wins. But as A2A-native programming matures, agents will need richer negotiation — conditional delegation, capability trades, temporal arbitration ("I'll yield the rudder for the next 5 seconds while you avoid that obstacle"). No formal semantics exist for what it means for two agents to agree on a bytecode modification.

**Approach:** Define a negotiation calculus — a formal language for expressing proposals, counter-proposals, and compromises in terms of bytecode modifications. Each proposal is a bytecode delta (add/remove/modify instructions). The calculus includes composition rules (how to merge two proposals), conflict detection (when two proposals are incompatible), and priority rules (how to resolve conflicts). Prove that the calculus is confluent (the final bytecode is independent of the order in which proposals are merged) and terminating (negotiation always concludes in finite time).

**Expected Results:** A formal negotiation protocol specification with machine-checkable safety properties (negotiation cannot produce bytecode that violates any safety rule), implemented as a Jetson-side service.

**Risk of Failure:** High. Agent negotiation may require common-sense reasoning that current LLMs cannot reliably provide. The formal calculus may be too rigid for practical use.

**Estimated Difficulty:** 18-24 person-months. HIGH.

**Dependencies:** Problems 2 (type system), 9 (adversarial bytecode), 10 (cross-vessel safety).

### Direction 2: Optimal Trust Dynamics for Heterogeneous Agent Swarms

**Motivation:** The INCREMENTS trust algorithm was designed for single-vessel, single-agent scenarios. In a heterogeneous swarm where agents of different types (navigation, safety, optimization), different capabilities (edge LLM vs. cloud LLM), and different experience levels (newly deployed vs. fleet-veteran) interact, the trust dynamics become significantly more complex. A fleet-veteran navigation agent sharing bytecode with a newly deployed vessel should transfer some trust evidence, but how much? Can trust be "lent" between agents?

**Approach:** Extend the INCREMENTS trust algorithm to support inter-agent trust transfer. Define a trust graph where nodes are agents and edges are trust relationships (bidirectional: "I trust your bytecode" and "You trust my validation"). Develop graph-theoretic trust propagation rules that allow trust evidence to flow through the graph while preventing trust inflation attacks (a malicious agent cannot inflate its trust by creating a trust cycle with colluding agents). Validate against a 100-agent swarm simulation.

**Expected Results:** A trust propagation algorithm that enables fleet-wide trust sharing while preventing trust inflation, with formal guarantees on convergence and robustness.

**Risk of Failure:** Medium. Graph-based trust propagation is well-studied in the web-of-trust literature, but the NEXUS constraints (physical safety, real-time operation) add novel challenges.

**Estimated Difficulty:** 12-18 person-months. MEDIUM-HIGH.

**Dependencies:** Problem 6 (trust equilibrium), Problem 4 (emergence), Problem 10 (cross-vessel safety).

### Direction 3: A2A-Native Type Inference from Bytecode Execution Traces

**Motivation:** The current type system (Problem 2) requires explicit type annotations. But if agents are the primary authors of bytecode, requiring explicit annotations is a burden. An alternative approach: infer types from execution traces. If a bytecode reads from sensor register 0 (compass heading, float32, degrees) and writes to actuator register 2 (rudder, float32, degrees), the type system can infer that this bytecode transforms heading → rudder angle. This inferred type can then be checked against the declared intention.

**Approach:** Develop a type inference algorithm that analyzes bytecode execution traces (sequences of (sensor_values, actuator_values) pairs) and infers a behavioral type signature. The inferred type has the form `(sensor_subset → actuator_subset) with constraints [bounded_input_ranges → bounded_output_ranges]`. Compare the inferred type against the declared intention type (from the DECLARE_INTENT metadata) and flag mismatches. This approach is analogous to behavioral typing in process calculi but applied to bytecode execution traces.

**Expected Results:** An automated type inference tool that can detect when a bytecode's actual behavior diverges from its declared intention, catching semantic bugs that structural validation misses.

**Risk of Failure:** Medium. Type inference from traces is inherently approximate (traces may not cover all edge cases), but partial coverage is still valuable.

**Estimated Difficulty:** 9-12 person-months. MEDIUM.

**Dependencies:** Problem 2 (type system), Problem 3 (formal semantics).

### Direction 4: Cryptographic Provenance Chains for Fleet Bytecode Distribution

**Motivation:** The `nexus_integration_analysis.md` proposes Ed25519 signing for fleet bytecode distribution, but a simple signature scheme is insufficient. In a fleet of 500 vessels sharing thousands of bytecodes over months, the provenance chain becomes complex: Agent A on Vessel X generated bytecode B, which was validated by Agent C on Vessel Y, deployed on Vessels Z₁-Z₅₀, modified by Agent D on Vessel Z₁₂, and the modified version was shared back to Vessel X. Tracking this provenance requires a cryptographic structure more sophisticated than simple signatures.

**Approach:** Design a Merkle-tree-based provenance chain where each bytecode version is a leaf, and each modification (generation, validation, deployment, transfer) creates a new version with a cryptographic hash linking to the previous version. The chain is append-only (modifications create new versions, never mutate existing ones) and is anchored to a fleet-wide root hash (updated via Raft consensus among Jetson nodes). The provenance chain supports efficient verification (any vessel can verify the complete provenance of any bytecode in O(log n) time) and efficient audit (regulators can extract the full provenance of any deployed bytecode in O(n) time).

**Expected Results:** A production-grade provenance system that provides tamper-evident bytecode history for regulatory compliance and forensic analysis.

**Risk of Failure:** Low. Merkle trees and append-only logs are well-understood cryptographic structures. The main challenge is integration with the existing wire protocol and storage constraints on ESP32.

**Estimated Difficulty:** 9-12 person-months. MEDIUM.

**Dependencies:** Problem 24 (black box provenance), Problem 1 (certification).

### Direction 5: Self-Organizing Safety Policy Evolution

**Motivation:** The current safety policy (`safety_policy.json`, 10 universal + 40 domain-specific rules) is static — written by human engineers and deployed unchanged. But in A2A-native programming, the system encounters novel situations that the static policy may not cover. Can the safety policy itself evolve? The "Evolutionary Safety Boundary Experiment" from Round 3A proposes that 2-3% of nodes operate with reduced safety rules, and if they achieve higher fitness without triggering hardware limits, the software safety rules are flagged for review.

**Approach:** Formalize the evolutionary safety policy framework. Define a "safety policy mutation" operator (add/remove/modify a safety rule) and a "safety fitness function" (how well the system performs with the mutated policy). Implement a simulated fleet where 2% of vessels operate with mutated safety policies (within the hardware safety envelope — Tier 1 and Tier 2 safety are non-negotiable), and measure whether the mutated policies discover genuinely beneficial safety adaptations. The critical constraint: the hardware safety envelope (kill switch, MAX6818 watchdog, output clamping) is immutable. Only the software safety rules (which are checked by the validator) can evolve.

**Expected Results:** A framework for safe safety-policy evolution that maintains the hardware safety invariant while discovering beneficial software safety adaptations.

**Risk of Failure:** HIGH. Safety policy evolution is inherently risky. The approach must guarantee that no mutation can bypass the hardware safety envelope. The 2% experimental fleet must be isolated from production.

**Estimated Difficulty:** 18-24 person-months. HIGH.

**Dependencies:** Problem 1 (certification), Problem 9 (adversarial bytecode), Problem 22 (alignment-utility gap).

### Direction 6: Quantum-Resilient Trust Score Algorithm

**Motivation:** The INCREMENTS trust algorithm is a deterministic function of event history. If an adversary can manipulate the event stream (e.g., by suppressing bad events or flooding with false good events), they can manipulate the trust score. In a fleet of autonomous vessels operating in adversarial environments (maritime piracy, industrial espionage), trust score manipulation is a realistic attack vector. Furthermore, the trust score is a critical infrastructure component — a compromise could enable deployment of unsafe bytecodes.

**Approach:** Analyze the INCREMENTS trust algorithm for adversarial robustness. Identify the attack surface (event suppression, event injection, timestamp manipulation, trust score replay). Develop countermeasures: (a) cryptographic event attestation (each event is signed by the generating ESP32 and verified by the Jetson), (b) trust score commitment schemes (the trust score is periodically committed to a tamper-evident log, preventing retroactive manipulation), (c) anomaly detection on event streams (flag statistical patterns inconsistent with normal operation). This is not quantum-specific but uses the term "quantum-resilient" in the sense of being robust against computationally unbounded adversaries with access to the event stream.

**Expected Results:** A hardened trust algorithm that maintains accurate scores even under adversarial event manipulation, with formal guarantees on the maximum trust deviation achievable by an adversary with given capabilities.

**Risk of Failure:** Medium. The INCREMENTS algorithm's 25:1 loss-to-gain ratio already provides significant robustness against transient manipulation. The remaining vulnerability is sustained, patient adversaries.

**Estimated Difficulty:** 12-18 person-months. MEDIUM-HIGH.

**Dependencies:** Problem 6 (trust equilibrium), Problem 9 (adversarial bytecode).

### Direction 7: Cognitive Load Management for Human Operators of A2A Fleets

**Motivation:** As A2A-native programming enables fleets of 50-500 autonomous vessels, the human operator's role shifts from direct control to fleet supervision. The cognitive load of monitoring 50 vessels generating and deploying bytecodes autonomously may exceed human capacity. The eight_lenses_analysis identified the Confucian principle of "ritual" — structured, predictable interactions — as relevant: the operator needs a predictable, structured interface for fleet supervision, not an avalanche of raw data.

**Approach:** Design a human-fleet interaction framework based on cognitive load theory. Identify the critical information the operator needs (fleet trust status, anomaly alerts, deployment approvals), the information the operator does NOT need (individual bytecode details, validation reports for routine deployments), and the escalation triggers that require operator attention (trust score drops, safety event cascades, regulatory compliance issues). Implement an adaptive information filtering system that presents the right information at the right granularity based on the operator's current cognitive capacity (measured via response time and decision quality metrics).

**Expected Results:** A fleet supervision interface design specification with cognitive load budgets, implemented as a Jetson-side dashboard.

**Risk of Failure:** Medium. Cognitive load measurement is imprecise and context-dependent. The framework may need significant iteration with human operators.

**Estimated Difficulty:** 9-12 person-months. MEDIUM.

**Dependencies:** Problem 25 (trust without anthropomorphism), Problem 28 (regulatory convergence).

### Direction 8: Bytecode Genetic Algorithms with Safety-Constrained Search

**Motivation:** The current learning pipeline uses LLM-based program synthesis to generate bytecodes. An alternative approach is genetic algorithms (GA): maintain a population of bytecodes, apply mutation and crossover operators, evaluate fitness via A/B testing, and select the fittest. The NEXUS knowledge base identifies bytecode as a "genotype" (knowledge-base/theory/evolutionary_computation.md), and the A2A-native language's intention blocks provide a natural genotype-phenotype mapping. However, standard GA operators may produce bytecodes that violate safety constraints.

**Approach:** Develop a safety-constrained genetic algorithm where: (a) the mutation operator only modifies instructions within the safety envelope (e.g., adjusts PID gains within safe ranges), (b) the crossover operator preserves intention blocks (never crosses intention boundaries), and (c) the selection operator penalizes bytecodes that trigger safety events. The fitness function is a weighted combination of utility (performance on the control task) and safety (absence of safety events). Compare the GA approach with the LLM synthesis approach on benchmark tasks to determine which produces higher-quality bytecodes faster.

**Expected Results:** A safety-constrained GA that can evolve bytecodes for well-characterized control tasks without LLM involvement, providing an alternative path for domains where LLM inference is unavailable (underground mining, satellite links).

**Risk of Failure:** Medium-High. GAs are notoriously slow to converge on complex control tasks. The safety constraints may over-constrain the search space, preventing discovery of novel solutions.

**Estimated Difficulty:** 12-18 person-months. MEDIUM-HIGH.

**Dependencies:** Problem 9 (adversarial bytecode), Problem 22 (alignment-utility gap).

### Direction 9: Distributed Runtime Verification of Multi-Agent Bytecode

**Motivation:** The current validation pipeline is static: bytecodes are validated before deployment and assumed correct at runtime. But runtime conditions may differ from deployment conditions (sensor drift, actuator degradation, environmental changes). A runtime verification layer that monitors executing bytecodes for behavioral anomalies would provide an additional safety net. The challenge is doing this on ESP32-S3 hardware with 512KB SRAM and 240MHz clock — the runtime verifier must be extremely lightweight.

**Approach:** Implement a lightweight runtime monitor as a FreeRTOS task on the ESP32 that checks: (a) actuator outputs are within declared bounds (already partially implemented by the output clamping), (b) sensor inputs are within expected ranges (flag stale or drifting sensors), (c) the bytecode's execution time is within the declared cycle budget (already partially implemented by the cycle counter), and (d) the bytecode's input-output behavior matches its declared intention type (compare actual input-output pairs against the inferred type from Direction 3). The monitor operates at a lower frequency than the VM (e.g., every 100 ticks) to minimize overhead.

**Expected Results:** A runtime verification task that adds <5% CPU overhead and <1KB RAM, catching behavioral anomalies that static validation misses.

**Risk of Failure:** Low. Runtime monitoring is a well-established technique in safety-critical systems. The main challenge is fitting within the ESP32's resource constraints.

**Estimated Difficulty:** 6-9 person-months. MEDIUM.

**Dependencies:** Problem 9 (adversarial bytecode), Problem 11 (timing), Direction 3 (type inference).

### Direction 10: The "Digital Constitution" — Formal Governance of Agent Autonomy

**Motivation:** The INCREMENTS trust framework defines how subsystems earn autonomy, but it does not define what agents are *allowed to do* at each autonomy level in a formal, machine-checkable way. A "digital constitution" would be a formal specification of the rights and responsibilities of agents at each autonomy level, analogous to a legal constitution but expressed in machine-checkable logic. At L0, agents may only observe and suggest. At L3, agents may deploy bytecodes within declared conditions. At L5, agents may generate, validate, and deploy bytecodes autonomously. The constitution defines the boundary conditions for each level.

**Approach:** Develop a constitutional logic — a formal language for expressing autonomy-level constraints. Each constraint has the form "At level L_i, action A is permitted/denied under condition C." The logic includes: (a) permission rules (what agents CAN do), (b) obligation rules (what agents MUST do, e.g., safety validation is mandatory at all levels), (c) prohibition rules (what agents MUST NOT do, e.g., disable the kill switch), and (d) delegation rules (what agents can delegate to other agents). Implement a constitutional checker that verifies every agent action against the constitution in real-time.

**Expected Results:** A formal digital constitution for the NEXUS platform, machine-checkable and human-readable, that provides the governance layer for A2A-native programming.

**Risk of Failure:** Medium. The constitutional logic must be expressive enough to capture all relevant constraints but simple enough to be machine-checkable in real-time. Over-constraining the constitution may prevent useful agent autonomy; under-constraining it may allow dangerous agent behavior.

**Estimated Difficulty:** 12-18 person-months. MEDIUM-HIGH.

**Dependencies:** Problems 1 (certification), 22 (alignment-utility), 23 (responsibility), 25 (trust without anthropomorphism).

---

## 3. Research Methodology Guide

Different NEXUS problems require different research methods. This section maps each problem to its best methodology, explains when each method is appropriate, and provides practical guidance for research agents.

### Method 1: Formal Proof

**When to use:** Problems with clear mathematical structure where the goal is to prove a property holds (or find a counterexample). The proof provides the strongest possible evidence — certainty rather than probability.

**Applicable problems:** Problem 1 (certification — need a formal process model), Problem 2 (type system — need soundness proof), Problem 6 (trust equilibrium — need Lyapunov stability proof), Problem 11 (timing — need worst-case response time proof), Problem 12 (degradation — need monotonicity proof), Problem 7 (minimum ISA — need minimality proof).

**How to proceed:**
1. Formalize the system as a mathematical model (dynamical system, type system, automaton).
2. State the property to be proved as a formal proposition.
3. Apply standard proof techniques (induction, contradiction, fixed-point theorems).
4. If the proof fails, construct a counterexample and analyze what it reveals.
5. Document the proof in machine-checkable form (Coq, Lean, Isabelle) if possible.

**Tools:** Coq, Lean 4, Isabelle/HOL, Z3 SMT solver, LaTeX for proof exposition.

### Method 2: Simulation and Monte Carlo Analysis

**When to use:** Problems with stochastic elements where analytical solutions are intractable but numerical experimentation is feasible. Simulation provides statistical evidence rather than certainty, but can handle complexity that formal methods cannot.

**Applicable problems:** Problem 4 (emergence — too many interaction patterns for formal analysis), Problem 6 (trust equilibrium — non-stationary inputs), Problem 10 (cross-vessel safety — fleet coordination), Problem 18 (fleet scalability — scaling analysis), Problem 21 (power-aware scheduling — energy profiling), Problem 29 (trust calibration — parameter sweep).

**How to proceed:**
1. Build a simulation model of the system (Python, MATLAB, or specialized tools).
2. Define the parameter space to explore.
3. Run a sufficient number of simulation trials (typically 10,000+) for statistical significance.
4. Analyze results using appropriate statistical methods (confidence intervals, hypothesis tests).
5. Identify edge cases and pathological conditions that deserve deeper analysis.

**Tools:** Python (NumPy, SciPy, Matplotlib), MATLAB/Simulink, NS-3 (network simulation), custom NEXUS fleet simulator.

### Method 3: Literature Review and Regulatory Analysis

**When to use:** Problems that require understanding the state of the art in adjacent fields or navigating regulatory frameworks. Literature review provides the foundation for all other methods by identifying what has already been solved.

**Applicable problems:** Problem 1 (certification — regulatory landscape), Problem 14 (cultural bias — LLM bias literature), Problem 23 (responsibility — legal precedent), Problem 25 (trust terminology — philosophy of trust), Problem 27 (domain transfer — transfer learning literature), Problem 28 (regulatory convergence — multi-standard analysis).

**How to proceed:**
1. Define the research question precisely.
2. Search for relevant literature using academic databases (Google Scholar, Semantic Scholar, IEEE Xplore).
3. Read and annotate the most relevant papers (minimum 20 for a thorough review).
4. Synthesize findings into a structured analysis (themes, gaps, contradictions).
5. Identify specific contributions that NEXUS can make to the field.

**Tools:** Semantic Scholar API, arXiv, Google Scholar, Zotero for reference management.

### Method 4: Empirical Testing and Benchmarking

**When to use:** Problems where the system's behavior under specific conditions must be measured. Empirical testing provides the most direct evidence but is limited to the conditions tested.

**Applicable problems:** Problem 5 (information preservation — measure mutual information), Problem 8 (neural network verification — adversarial testing), Problem 9 (adversarial bytecode — fuzzing), Problem 11 (timing — hardware measurement), Problem 13 (cross-validation — validator calibration), Problem 15 (system prompt — A/B testing), Problem 16 (specialization — cross-domain quality), Problem 21 (power — energy profiling).

**How to proceed:**
1. Define the benchmark or test suite.
2. Ensure the benchmark covers representative cases, not just easy cases.
3. Measure results with appropriate metrics (accuracy, latency, energy, etc.).
4. Report results with statistical significance and confidence intervals.
5. Make the benchmark publicly available for reproducibility.

**Tools:** Python testing frameworks, custom benchmark harnesses, hardware instrumentation (logic analyzers, power monitors), A/B testing infrastructure.

### Method 5: Thought Experiment and Philosophical Analysis

**When to use:** Problems that involve normative questions (what should be), conceptual analysis (what does X mean), or counterfactual reasoning (what would happen if). Thought experiments cannot produce empirical evidence but can clarify concepts and identify hidden assumptions.

**Applicable problems:** Problem 3 (formal semantics of intention — what does "meaning" mean?), Problem 22 (alignment-utility gap — what is "useful"?), Problem 23 (responsibility — who is responsible?), Problem 24 (provenance — what constitutes adequate explanation?), Problem 25 (trust — what is "trust" without anthropomorphism?), Problem 26 (meaningfulness — what makes a bytecode "meaningful"?), Direction 10 (digital constitution — what are agent rights?).

**How to proceed:**
1. State the conceptual question precisely.
2. Analyze the question from multiple philosophical perspectives (Western, Eastern, indigenous — per the eight_lenses_analysis).
3. Construct thought experiments that test the boundaries of the concept.
4. Identify hidden assumptions and question them.
5. Propose a working definition that is precise enough for engineering use.

**Tools:** Philosophical frameworks (virtue ethics, consequentialism, deontology), cross-cultural analysis, conceptual analysis.

### Method 6: Systems Engineering and Fault Analysis

**When to use:** Problems involving system-level reliability, failure modes, or safety certification. This method combines formal analysis (fault trees, FMEA) with empirical testing (fault injection) to produce a comprehensive safety argument.

**Applicable problems:** Problem 1 (certification — safety case construction), Problem 9 (adversarial bytecode — threat modeling), Problem 11 (timing — WCET analysis), Problem 12 (degradation — FMEA), Problem 20 (hot-loading — state machine analysis), Direction 5 (safety policy evolution — change impact analysis).

**How to proceed:**
1. Identify all failure modes (systematic analysis using FMEA, fault trees, or STPA).
2. Assess the severity and likelihood of each failure mode.
3. Design mitigations for high-severity failure modes.
4. Verify mitigations through testing or formal analysis.
5. Document the safety argument in a structured format (GSN, CAE).

**Tools:** STPA (System-Theoretic Process Analysis), FMEA templates, GSN (Goal Structuring Notation), fault injection frameworks.

### Methodology Mapping Table

| Problem | Primary Method | Secondary Method | Estimated Duration |
|---------|---------------|-----------------|-------------------|
| P1 (Certification) | Literature Review | Systems Engineering | 36-48 pm |
| P2 (Type System) | Formal Proof | Empirical Testing | 18-24 pm |
| P3 (Intention Semantics) | Thought Experiment | Formal Proof | 12-18 pm |
| P4 (Emergence) | Simulation | Formal Proof | 24-36 pm |
| P5 (Info Preservation) | Empirical Testing | Thought Experiment | 6-9 pm |
| P6 (Trust Equilibrium) | Formal Proof | Simulation | 6-9 pm |
| P7 (Min ISA) | Formal Proof | Empirical Testing | 3-6 pm |
| P8 (NN Verification) | Empirical Testing | Formal Proof | 24-36 pm |
| P9 (Adversarial) | Empirical Testing | Formal Proof | 12-18 pm |
| P10 (Cross-Vessel) | Simulation | Systems Engineering | 9-12 pm |
| P11 (Timing) | Formal Proof | Empirical Testing | 6-9 pm |
| P12 (Degradation) | Systems Engineering | Simulation | 9-12 pm |
| P13 (Cross-Validation) | Empirical Testing | Literature Review | 12-18 pm |
| P14 (Cultural Bias) | Literature Review | Empirical Testing | 9-12 pm |
| P15 (System Prompt) | Empirical Testing | Simulation | 6-9 pm |
| P16 (Specialization) | Empirical Testing | Simulation | 6-9 pm |
| P17 (Emergent Comm) | Thought Experiment | Simulation | 6-9 pm |
| P18 (Scalability) | Simulation | Systems Engineering | 9-12 pm |
| P19 (Trust Sync) | Simulation | Systems Engineering | 6-9 pm |
| P20 (Hot-Loading) | Systems Engineering | Formal Proof | 6-9 pm |
| P21 (Power) | Empirical Testing | Simulation | 6-9 pm |
| P22 (Alignment-Utility) | Thought Experiment | Empirical Testing | 9-12 pm |
| P23 (Responsibility) | Literature Review | Thought Experiment | 9-12 pm |
| P24 (Provenance) | Thought Experiment | Systems Engineering | 9-12 pm |
| P25 (Trust Anthro) | Thought Experiment | Literature Review | 3-6 pm |
| P26 (Meaningfulness) | Thought Experiment | Formal Proof | 6-9 pm |
| P27 (Domain Transfer) | Empirical Testing | Literature Review | 6-9 pm |
| P28 (Regulatory) | Literature Review | Systems Engineering | 9-12 pm |
| P29 (Trust Cal) | Simulation | Empirical Testing | 6-9 pm |
| D1 (Negotiation) | Formal Proof | Simulation | 18-24 pm |
| D2 (Trust Swarm) | Simulation | Formal Proof | 12-18 pm |
| D3 (Type Inference) | Empirical Testing | Formal Proof | 9-12 pm |
| D4 (Provenance Crypto) | Systems Engineering | Formal Proof | 9-12 pm |
| D5 (Safety Evolution) | Simulation | Systems Engineering | 18-24 pm |
| D6 (Trust Hardening) | Formal Proof | Simulation | 12-18 pm |
| D7 (Cognitive Load) | Thought Experiment | Empirical Testing | 9-12 pm |
| D8 (Bytecode GA) | Simulation | Empirical Testing | 12-18 pm |
| D9 (Runtime Verify) | Systems Engineering | Empirical Testing | 6-9 pm |
| D10 (Constitution) | Formal Proof | Thought Experiment | 12-18 pm |

---

## 4. Cross-Pollination Map

NEXUS sits at the intersection of multiple research fields. This section maps specific contributions from adjacent fields that could accelerate NEXUS research, organized by field.

### Program Synthesis

**Relevance:** NEXUS's core activity — agents generating bytecode from natural-language intent — is a form of program synthesis.

**Key contributions to leverage:**
- **Counter-example-guided inductive synthesis (CEGIS):** Generate a candidate bytecode, test it against the specification, and use the counter-example to refine the next candidate. This iterative approach is more efficient than generating bytecodes at random and could replace or augment the LLM-based synthesis pipeline for well-characterized control tasks.
- **Sketch-based synthesis:** Allow the LLM to generate a "sketch" (bytecode with holes) and use a constraint solver to fill the holes. This combines LLM creativity with formal guarantees.
- **Neural program synthesis:** Recent work on using neural networks to guide program search (e.g., DreamCoder, AlphaCode) could improve the quality of LLM-generated bytecodes by incorporating a learned prior over control-program structure.

**NEXUS-specific opportunity:** The 32-opcode ISA is small enough that exhaustive enumeration of all bytecodes up to length 50 is theoretically possible (32^50 ≈ 10^75 — intractable). But constraint-guided search within this space (using safety rules as constraints) could be practical for short bytecodes.

**Key references:** Gulwani et al. (2017) — Program Synthesis; Solar-Lezama (2008) — Sketching; Ellis et al. (2021) — DreamCoder.

### Multi-Agent Systems

**Relevance:** NEXUS's agent ecology (learning agents, safety agents, trust agents, coordination agents) is a multi-agent system.

**Key contributions to leverage:**
- **Contract-based interaction:** Agents negotiate through contracts that specify rights, obligations, and penalties. This maps directly to NEXUS's intention blocks (declared capabilities, pre/postconditions, trust requirements). The contract-based approach provides a formal foundation for agent-agent negotiation (Direction 1).
- **Organizational self-design:** Multi-agent systems that dynamically reorganize their communication topology based on task requirements. This maps to NEXUS's need for adaptive fleet coordination (Problem 10, Problem 18).
- **Argumentation-based negotiation:** Agents negotiate by exchanging arguments (justifications for proposals, objections to counter-proposals). This provides a richer negotiation framework than simple proposal-acceptance and could improve the quality of agent-agent bytecode compromise.

**NEXUS-specific opportunity:** The A2A-native programming paradigm creates a unique multi-agent system where agents communicate through *executable code* (bytecode), not through messages. This is fundamentally different from the message-passing paradigm in most multi-agent systems and opens new research directions in "programmatic multi-agent communication."

**Key references:** Wooldridge (2009) — An Introduction to MultiAgent Systems; Dignum et al. (2016) — Handbook of Research on Multi-Agent Systems; Huhns & Singh (1997) — Readings in Agents.

### Distributed Consensus

**Relevance:** Fleet-wide trust synchronization, bytecode version management, and safety policy evolution all require distributed consensus.

**Key contributions to leverage:**
- **Byzantine fault tolerance (BFT):** NEXUS's validation pipeline assumes honest validators. If a validator is compromised (malicious agent, corrupted model), the system must tolerate Byzantine faults. PBFT and its modern variants (HotStuff, Tendermint) provide protocols for consensus in the presence of Byzantine faults.
- **Conflict-free replicated data types (CRDTs):** NEXUS already uses CRDTs for trust score synchronization (LWW with timestamps). More sophisticated CRDT designs could support richer fleet-wide data structures (bytecode libraries, capability registries, policy version histories).
- **Epidemic protocols (gossip):** For fleet-wide bytecode distribution, epidemic protocols (each vessel periodically shares its bytecode library with a random peer) provide eventual consistency with low overhead and high resilience to network partitions.

**NEXUS-specific opportunity:** The Raft consensus protocol is already specified for Jetson cluster coordination. Extending this to inter-vessel consensus (across unreliable Starlink links) requires hybrid protocols that combine Raft (for quorum within a sub-fleet) with gossip (for dissemination across sub-fleets).

**Key references:** Ongaro & Ousterhout (2014) — In Search of an Understandable Consensus Algorithm; Shapiro et al. (2011) — CRDTs; Lamport et al. (2019) — The Byzantine Generals Problem.

### Formal Methods

**Relevance:** NEXUS's safety-critical nature demands the highest assurance levels, which formal methods provide.

**Key contributions to leverage:**
- **Abstract interpretation:** The most promising approach for Problem 2 (agent type system). Tools like Astrée (designed for Airbus flight control software) can compute safe over-approximations of program behavior. Adapting Astrée's abstract domains to NEXUS's 32-opcode ISA could provide static behavioral type inference.
- **Model checking:** Tools like UPPAAL (for timed automata), Spin (for protocol verification), and CBMC (for C code verification) can verify properties of NEXUS components. UPPAAL is particularly relevant for Problem 11 (timing analysis) and Problem 20 (hot-loading safety).
- **Proof-carrying code (PCC):** Necula's PCC framework is directly applicable to NEXUS's bytecode validation pipeline. Requiring agents to attach machine-checkable proofs of safety properties would move NEXUS from "safe by validation" to "safe by proof."

**NEXUS-specific opportunity:** The 32-opcode ISA is small enough that exhaustive model checking of short bytecodes (<100 instructions) is feasible. This enables the construction of a "bytecode model checker" that verifies temporal safety properties (e.g., "the rudder angle always returns to center within 1 second after a heading error of >30°") without requiring abstract interpretation.

**Key references:** Cousot & Cousot (1977) — Abstract Interpretation; Clarke et al. (1999) — Model Checking; Necula (1997) — Proof-Carrying Code.

### Cognitive Science

**Relevance:** The INCREMENTS trust algorithm is based on Lee & See's trust psychology framework. Understanding human trust calibration is essential for the operator interface.

**Key contributions to leverage:**
- **Trust calibration:** The mismatch between actual system capability and operator trust level. NEXUS's 25:1 loss-to-gain ratio is designed to prevent overtrust, but the operator's trust calibration may not match the system's trust score. Displaying the system's trust score to the operator may cause inappropriate trust or distrust.
- **Situational awareness:** The three levels of situational awareness (perception, comprehension, projection) map to NEXUS's three tiers: Tier 1 provides perception (sensor data), Tier 2 provides comprehension (pattern discovery), and Tier 3 provides projection (simulation and planning). The operator interface should support all three levels.
- **Cognitive workload:** The theory of cognitive load (intrinsic, extraneous, germane) is directly relevant to Direction 7 (cognitive load management). The operator's cognitive capacity is limited, and the interface must optimize the allocation of this capacity across monitoring, decision-making, and intervention tasks.

**NEXUS-specific opportunity:** The Griot narrative layer (requiring natural-language explanations for every deployed bytecode) is fundamentally a cognitive science intervention — it addresses the human need for explanation and narrative understanding. Researching the effectiveness of Griot narratives in building appropriate trust is a unique contribution to the trust psychology literature.

**Key references:** Lee & See (2004) — Trust in Automation; Endsley (1995) — Toward a Theory of Situational Awareness; Sweller (1988) — Cognitive Load.

### Evolutionary Biology

**Relevance:** NEXUS's evolutionary paradigm (bytecodes mutate, are selected by A/B testing, and survive based on trust accumulation) is directly inspired by biological evolution.

**Key contributions to leverage:**
- **Fitness landscapes:** The concept of fitness landscapes (Wright, 1932) provides a framework for understanding how bytecodes evolve. Rugged landscapes (many local optima) make it hard for evolution to find globally optimal solutions. Smooth landscapes (single global optimum) make convergence easy. The A2A-native programming paradigm's fitness landscape depends on the safety policy (which constrains the search space) and the utility metric (which defines the optimization objective).
- **Punctuated equilibrium:** The seasonal evolution protocol (Spring high mutation → Autumn low mutation) maps to Eldredge & Gould's theory of punctuated equilibrium — long periods of stability punctuated by rapid change. This mapping provides a theoretical foundation for the seasonal protocol's effectiveness.
- **Symbiosis and coevolution:** In a fleet, bytecodes coevolve — a navigation bytecode's fitness depends on the collision-avoidance bytecode it coexists with. Coevolutionary dynamics (arms races, mutualisms) provide a framework for understanding fleet-level bytecode evolution.

**NEXUS-specific opportunity:** The biological analogy extends to the three-tier architecture: Tier 1 (ESP32) is like a cell's ribosome (dumb executor), Tier 2 (Jetson) is like a cell's nucleus (information processing), and Tier 3 (Cloud) is like a multi-cellular organism's endocrine system (slow, global signaling). This biological framing suggests architectural improvements: e.g., "hormonal signals" from the cloud that modulate the Jetson's behavior without commanding specific actions.

**Key references:** Wright (1932) — The Roles of Mutation, Inbreeding, Crossbreeding, and Selection in Evolution; Eldredge & Gould (1972) — Punctuated Equilibria; Holland (1975) — Adaptation in Natural and Artificial Systems.

### Linguistics

**Relevance:** The A2A-native programming paradigm treats bytecode as a language — agents read, write, and negotiate in bytecode. Linguistic theory provides tools for analyzing this language.

**Key contributions to leverage:**
- **Pragmatics and speech acts:** Austin's speech act theory (assertives, directives, commissives, expressives, declarations) maps to NEXUS's communication opcodes: TELL (assertive), ASK (directive), DELEGATE (commissive), REPORT_STATUS (expressive), DECLARE_INTENT (declaration). Pragmatic theory provides a framework for understanding how agents use these opcodes in context.
- **Translation theory:** The compilation pipeline (natural language → JSON → bytecode) is a form of translation. Translation theory (Nida's dynamic equivalence, Toury's norms) provides insights into the information loss at each stage (Problem 5).
- **Constructed languages (conlangs):** The A2A-native language is a constructed language — designed, not evolved. Conlang design principles (regularity, learnability, expressiveness) can guide the design of the bytecode language's syntax and semantics.

**NEXUS-specific opportunity:** The AAB (Agent-Annotated Bytecode) format with its TLV metadata is analogous to a language with rich morphological annotation. Linguistic analysis of AAB "sentences" (intention blocks) could reveal patterns that improve agent interpretability and verification.

**Key references:** Austin (1962) — How to Do Things with Words; Searle (1969) — Speech Acts; Nida (1964) — Toward a Science of Translating.

### Control Theory

**Relevance:** NEXUS bytecodes implement control algorithms (PID, state machines, rate limiters). Control theory provides the mathematical framework for analyzing and designing these algorithms.

**Key contributions to leverage:**
- **Robust control:** μ-synthesis and H∞ control provide frameworks for designing controllers that are robust to uncertainty. Applying robust control theory to NEXUS bytecodes could provide formal guarantees that a bytecode maintains stability even under sensor noise, actuator degradation, and environmental disturbance.
- **Adaptive control:** Model-reference adaptive control (MRAC) and self-tuning regulators (STR) are control algorithms that adapt to changing conditions. These map to NEXUS's learning pipeline (observe → discover patterns → synthesize reflex → deploy). Understanding adaptive control theory can improve the safety of NEXUS's adaptive bytecodes.
- **Hybrid systems theory:** The combination of discrete control (bytecode execution, mode switching) and continuous dynamics (physical system behavior) is a hybrid system. Hybrid automata (Henzinger, 2000) provide the formal framework for analyzing these systems.

**NEXUS-specific opportunity:** The 32-opcode ISA can express a large class of controllers (all continuous piecewise-polynomial functions, per Stone-Weierstrass). Control theory can identify the subclass of controllers that are *safe by construction* (e.g., passivity-based controllers that cannot inject energy into the system) and constrain bytecode synthesis to this subclass.

**Key references:** Åström & Hägglund (2006) — Advanced PID Control; Zhou et al. (1996) — Robust and Optimal Control; Henzinger (2000) — The Theory of Hybrid Automata.

### Maritime Engineering

**Relevance:** NEXUS's reference domain is marine autonomous vessels. Maritime engineering provides domain-specific constraints and design patterns.

**Key contributions to leverage:**
- **COLREGs compliance:** The Convention on the International Regulations for Preventing Collisions at Sea (72 rules) is encoded in NEXUS's safety_policy.json. Maritime engineering research on autonomous COLREGs compliance provides benchmarks and test scenarios for NEXUS's collision-avoidance bytecodes.
- **Ship dynamics:** The hydrodynamic behavior of vessels (maneuvering models, seakeeping, resistance) defines the physical system that NEXUS bytecodes control. Accurate ship dynamics models are essential for simulation-based evaluation of bytecodes.
- **Classification society rules:** Lloyd's Register, DNV GL, and other classification societies define construction and equipment standards for vessels. Understanding these rules is essential for certification (Problem 1).

**NEXUS-specific opportunity:** The IMO's Maritime Autonomous Surface Ships (MASS) Code provides a regulatory framework specifically for autonomous vessels — the most advanced regulatory framework for autonomous systems in any domain. NEXUS's engagement with IMO MASS could establish a precedent for A2A-native programming certification.

**Key references:** IMO (2023) — MASS Code; Fossen (2011) — Handbook of Marine Craft Hydrodynamics and Motion Control; IMO (1972) — COLREGs.

---

## 5. Priority Research Roadmap — 12 Months

The 12-month roadmap is organized into four quarters, with dependencies between tasks explicitly tracked. The priority ordering is based on: (a) blocking status (CRITICAL problems first), (b) dependency chains (problems that unblock other problems first), (c) feasibility (problems with clear research approaches first), and (d) strategic value (problems that enable the A2A-native vision).

### Q1: Foundation (Months 1-3) — "Build the Verification Backbone"

**Goal:** Establish the mathematical and empirical foundations for safe A2A bytecode deployment.

| Week | Task | Problem/Direction | Method | Deliverable |
|------|------|-------------------|--------|-------------|
| 1-4 | Trust equilibrium Lyapunov analysis | P6 | Formal Proof | Stability proof or counterexample |
| 1-4 | Minimum ISA opcode elimination | P7 | Formal Proof | Minimal opcode set |
| 1-6 | Abstract interpretation over 32-opcode ISA | P2, D3 | Formal Proof + Empirical | Type inference prototype |
| 3-8 | System prompt Bayesian optimization | P15 | Empirical Testing | Optimized system prompt |
| 5-8 | Per-rule validator calibration campaign | P13 | Empirical Testing | Per-rule miss-rate data |
| 5-12 | Hot-loading state machine formal analysis | P20 | Systems Engineering | Safety case for hot-loading |
| 8-12 | Information-theoretic pipeline audit | P5 | Empirical Testing | Information preservation metrics |

**Milestone (Month 3):** Trust equilibrium is proven stable (or pathological conditions are identified). Abstract interpretation prototype demonstrates behavioral type inference for simple bytecodes. System prompt achieves ≥90% safety adherence (from 82%).

### Q2: Safety Hardening (Months 4-6) — "Close the Adversarial Gap"

**Goal:** Address the most dangerous attack surfaces and strengthen the validation pipeline.

| Week | Task | Problem/Direction | Method | Deliverable |
|------|------|-------------------|--------|-------------|
| 13-16 | Adversarial bytecode fuzzer (Phase 1) | P9 | Empirical Testing | Fuzzer + initial results |
| 13-16 | Composition analysis tool | P9 | Formal Proof + Empirical | Joint-safety checker prototype |
| 13-20 | Runtime verification task for ESP32 | D9 | Systems Engineering | Runtime monitor implementation |
| 16-20 | NN verification adversarial benchmark | P8 | Empirical Testing | 10K adversarial prompt benchmark |
| 16-24 | Digital constitution formal specification | D10 | Formal Proof + Thought Experiment | Constitutional logic spec |
| 17-24 | Trust parameter sweep simulation | P29 | Simulation | Pareto-optimal parameter sets |

**Milestone (Month 6):** Adversarial bytecode fuzzer identifies ≥5 novel attack surfaces. Runtime verification task demonstrates <5% CPU overhead. Constitutional logic specification is complete.

### Q3: Fleet Intelligence (Months 7-9) — "Enable Multi-Vessel Autonomy"

**Goal:** Solve the coordination, scaling, and trust-transfer problems needed for fleet-scale A2A deployment.

| Week | Task | Problem/Direction | Method | Deliverable |
|------|------|-------------------|--------|-------------|
| 25-28 | Trust-scaled coordination protocol | P10 | Simulation | Protocol specification + simulation results |
| 25-32 | Trust propagation graph algorithm | D2 | Simulation + Formal Proof | Algorithm + convergence proof |
| 28-32 | Cross-vessel safety inconsistency analysis | P10 | Simulation | Formal coordination protocol |
| 25-36 | Formal negotiation calculus | D1 | Formal Proof | Negotiation protocol specification |
| 28-36 | Fleet scalability hierarchical architecture | P18 | Simulation | Hierarchical fleet design |
| 28-36 | Emergent behavior bounding (mean-field theory) | P4 | Simulation + Formal Proof | Emergence prediction framework |

**Milestone (Month 9):** Trust propagation algorithm demonstrates convergence on 100-agent simulation. Fleet coordination protocol handles trust divergence of up to 3 autonomy levels. Emergence prediction framework achieves ≥70% accuracy on 50-agent configurations.

### Q4: Certification and Deployment (Months 10-12) — "Prepare for Production"

**Goal:** Close the gaps that prevent real-world deployment in regulated domains.

| Week | Task | Problem/Direction | Method | Deliverable |
|------|------|-------------------|--------|-------------|
| 37-40 | PCCP draft for marine SIL 1 | P1 | Literature Review + Systems Engineering | PCCP document |
| 37-44 | Safety-constrained bytecode GA | D8 | Simulation | GA prototype + comparison with LLM synthesis |
| 37-44 | Cultural bias audit (3 jurisdictions) | P14 | Empirical Testing + Literature Review | Bias analysis report |
| 40-44 | Self-organizing safety policy framework | D5 | Simulation | Evolutionary safety policy spec |
| 40-48 | Cryptographic provenance chain implementation | D4 | Systems Engineering | Merkle-tree provenance system |
| 40-48 | Agent specialization vs generalization study | P16 | Empirical Testing | Cross-domain quality comparison |

**Milestone (Month 12):** PCCP draft ready for Lloyd's Register pre-assessment. Cultural bias audit identifies ≥3 systematic biases with mitigations. Safety-constrained GA demonstrates viable LLM-free bytecode evolution for benchmark tasks.

### Dependency Graph

```
P6 (Trust Equilibrium) ─────→ P10 (Cross-Vessel) ─────→ D2 (Trust Swarm)
       │                          │
       └──────────────────────────┘
                                   │
P2 (Type System) ───→ P9 (Adversarial) ───→ D9 (Runtime Verify)
       │                    │
       └────────────────────┘
                                   │
P15 (System Prompt) → P13 (Cross-Validation) → P8 (NN Verification)
                                   │
P7 (Min ISA) ──────────────────── (independent)
                                   │
P3 (Intention) ───→ P22 (Alignment-Utility) ───→ D10 (Constitution)
                                   │
P11 (Timing) ─────→ P12 (Degradation) ─────→ P20 (Hot-Loading)
                                   │
D1 (Negotiation) ←── P2, P9, P10 (requires type system + adversarial analysis + coordination)
D3 (Type Inference) ←── P2 (extends type system to traces)
D4 (Provenance) ←── P24 (extends provenance concept to cryptographic chains)
D5 (Safety Evolution) ←── P1, P9, P22 (requires certification framework + adversarial analysis + utility metric)
D6 (Trust Hardening) ←── P6 (extends trust algorithm with cryptographic attestation)
D7 (Cognitive Load) ←── P25 (extends trust terminology to operator interface)
D8 (Bytecode GA) ←── P9, P22 (requires adversarial analysis + utility metric)
```

---

## 6. Research Failure Modes

This section catalogs the "unknown unknowns" — assumptions that might be wrong, dead ends that might waste resources, and failure modes that could derail the research program. Forewarned is forearmed.

### Assumption 1: "The LLM+Validator Pipeline Can Be Made Sufficiently Reliable"

**What we assume:** With enough optimization (better system prompts, triangulated validation, adversarial testing), the LLM+validator pipeline can achieve <0.1% false-negative rate, which is sufficient for safety-critical deployment.

**Why it might be wrong:** LLMs are fundamentally probabilistic. No amount of optimization can reduce the false-negative rate to exactly zero — there will always be edge cases that the model handles incorrectly. The 0.1% threshold is a practical compromise, not a theoretical guarantee. Furthermore, the false-negative rate may not decrease monotonically with optimization effort — diminishing returns may set in quickly, and the residual error rate may be dominated by adversarial examples that are extremely difficult to construct but exist in principle.

**What to do if wrong:** Invest more heavily in runtime monitoring (Direction 9) and hardware safety (which is already non-negotiable in NEXUS's four-tier safety). The principle: "never trust the software layer alone; always have a hardware safety net." If the LLM+validator pipeline cannot be made sufficiently reliable, the A2A paradigm shifts from "agents generate and deploy code autonomously" to "agents generate code, which humans review and deploy manually." This is still valuable (automating the synthesis step) but less ambitious than full A2A autonomy.

### Assumption 2: "The Trust Score Correctly Measures Safety"

**What we assume:** The INCREMENTS trust score, which measures the absence of adverse events, is a good proxy for system safety. High trust = safe; low trust = unsafe.

**Why it might be wrong:** The trust score measures *lagging indicators* (events that already happened). It does not measure *leading indicators* (conditions that predict future events). A system can have high trust (no adverse events yet) but be operating in a regime where adverse events are imminent (e.g., sensors degrading, environmental conditions changing). This is the "calm before the storm" problem. Additionally, the trust score does not account for *near misses* — events that almost caused harm but didn't. A system that narrowly avoids collisions daily may have high trust but is actually operating unsafely.

**What to do if wrong:** Augment the trust score with leading indicators: sensor health monitoring, environmental risk assessment, and near-miss detection. Define a "risk-adjusted trust score" that penalizes systems operating in high-risk regimes even if no adverse events have occurred. This is a significant extension to the INCREMENTS algorithm but addresses a fundamental measurement gap.

### Assumption 3: "Agents Will Generate Useful Bytecodes"

**What we assume:** Given sufficient observation data and a well-designed system prompt, agents will generate bytecodes that are both safe and useful — improving the system's performance on its control task.

**Why it might be wrong:** The LLM's training data is primarily from software engineering, not control engineering. The LLM may generate bytecodes that are syntactically correct and safety-compliant but control-theoretically naive (e.g., a heading-hold controller with excessive gain that oscillates in rough seas). The 82% safety adherence rate suggests that even safety compliance is not guaranteed. The utility question (Problem 22) is entirely open — we have no evidence that LLM-generated bytecodes are more useful than hand-tuned PID controllers.

**What to do if wrong:** Develop control-theory-aware bytecode templates that constrain the LLM's synthesis space to control-theoretically sound designs. For example, the system prompt could require that all heading-hold bytecodes use the PID_COMPUTE syscall with gains in a specified range, rather than allowing arbitrary control logic. This trades generality for reliability.

### Assumption 4: "The A/B Testing Bottleneck Is Acceptable"

**What we assume:** The 60-minute A/B test (required before any bytecode deployment) is an acceptable bottleneck. It ensures that only safe, effective bytecodes reach deployment, and the 60-minute cost is justified by the safety benefit.

**Why it might be wrong:** In rapidly changing environments (collision avoidance, storm response), the system may need to adapt faster than the 60-minute A/B test allows. A bytecode that addresses an immediate safety threat (e.g., a new obstacle avoidance pattern for a previously unseen obstacle type) cannot be deployed for 60 minutes — during which time the vessel is at risk. Additionally, the A/B test measures performance against the current baseline, not against potential future conditions. A bytecode that performs well in calm seas may fail in storms.

**What to do if wrong:** Implement a "fast-track A/B test" for safety-critical bytecodes: a shorter test (5-10 minutes) with tighter statistical thresholds (higher confidence required). This enables rapid deployment for urgent safety needs while maintaining statistical rigor. The fast-track test should only be available for bytecodes that address a detected safety risk, not for routine improvements.

### Assumption 5: "The Eight-Domain Universality Claim Holds"

**What we assume:** 80% of the NEXUS architecture is domain-agnostic, and only 20% requires domain-specific adaptation. This claim is based on the cross-domain analysis in Round 2A.

**Why it might be wrong:** The 80% claim is based on a feature-level comparison (which components are shared vs. domain-specific), not on a behavioral comparison (how the system actually performs across domains). A domain-specific adaptation that is 20% of the codebase may have 80% of the safety impact — for example, in healthcare, the domain-specific safety rules are the ones that prevent patient harm, and they may interact with the universal rules in unexpected ways. Additionally, the cross-domain analysis was conducted at the specification level, not the implementation level. Implementation-level cross-domain compatibility may be lower than specification-level compatibility.

**What to do if wrong:** Conduct implementation-level cross-domain testing: deploy NEXUS in at least 3 domains (marine, HVAC, agriculture) and measure the actual code reuse, adaptation effort, and safety compliance. If the 80% claim is wrong, adjust the development and deployment strategy accordingly.

### Assumption 6: "The 0.5× Trust Multiplier for Agent Code Is Sufficient"

**What we assume:** Agent-generated bytecode earns trust at half the rate of human-authored code, which compensates for the reduced human intuition about what the code "actually does."

**Why it might be wrong:** The 0.5× multiplier was chosen as a heuristic, not derived from first principles. It may be too conservative (preventing useful agent bytecodes from reaching useful autonomy levels in a reasonable time) or too permissive (allowing unsafe agent bytecodes to accumulate trust faster than human review can catch errors). The optimal multiplier likely depends on the domain (healthcare requires more caution than home automation), the agent's track record (fleet-proven agents deserve higher multipliers), and the bytecode's complexity (simple bytecodes are easier to verify than complex ones).

**What to do if wrong:** Develop a data-driven trust multiplier: analyze the relationship between bytecode authorship (human vs. agent), bytecode complexity, and safety event rate across deployments. Use this data to derive a trust multiplier function: `multiplier = f(domain, complexity, fleet_evidence)`. This replaces the fixed 0.5× heuristic with an evidence-based adaptive multiplier.

### Assumption 7: "Formal Methods Will Scale to the 32-Opcode ISA"

**What we assume:** Formal verification techniques (abstract interpretation, model checking, type inference) can be applied to NEXUS's 32-opcode bytecode ISA and produce practical results.

**Why it might be wrong:** The 32-opcode ISA is simple in isolation but complex in composition. A single bytecode of 200 instructions has 32^200 ≈ 10^300 possible execution paths — far beyond the reach of exhaustive model checking. Abstract interpretation may produce overly conservative bounds (reporting "unsafe" when the bytecode is actually safe), leading to high false-positive rates. The formal methods community has decades of experience with the gap between theoretical decidability and practical tractability.

**What to do if wrong:** Focus on lightweight formal methods (abstract interpretation with interval arithmetic, which is efficient and decidable) rather than heavyweight methods (full model checking, which may be intractable). Accept that formal methods provide partial coverage (catching some safety issues but not all) and supplement them with empirical testing and runtime monitoring. The principle: "use the weakest formal method that solves the problem."

### Assumption 8: "The Regulatory Landscape Will Accommodate A2A Programming"

**What we assume:** Safety standards bodies (IEC, ISO, IMO) will eventually accommodate continuous learning systems with bounded change spaces, enabling certification of A2A-generated bytecodes.

**Why it might be wrong:** Regulatory change is slow (typically 5-10 year cycles) and risk-averse. Standards bodies may refuse to certify any system with self-modifying software, regardless of the safety argument. The EU AI Act (effective 2025-2027) classifies autonomous systems as "high-risk" and imposes strict requirements that may be incompatible with A2A-native programming. If certification is impossible, NEXUS is limited to non-regulated domains (home automation, consumer products) — a significant reduction in scope.

**What to do if wrong:** Pursue a "dual-track" strategy: (a) engage with standards bodies to develop certification pathways for A2A systems (long-term, high reward), and (b) develop a "certification-compatible mode" where A2A-generated bytecodes are frozen and treated as static artifacts for certification purposes (short-term, lower capability but regulatory-compliant). The dual-track approach ensures that NEXUS can deploy in regulated domains even if the full A2A paradigm cannot be certified.

### Dead End Warning: "Do Not Pursue Full LLM Formal Verification"

Attempting to formally verify a 7-billion-parameter LLM (Problem 8) is a dead end. Current formal verification tools handle networks of at most a few hundred neurons. Scaling to billions is an open research problem in the formal methods community with no clear path to solution. Instead, pursue: (a) empirical adversarial testing (practical, produces actionable results), (b) runtime monitoring (defense-in-depth), and (c) compositional verification (verify the bytecode, not the generator).

### Dead End Warning: "Do Not Pursue General Agent Communication Without Constraints"

Allowing agents to communicate through arbitrary channels (Problem 17) without protocol boundary enforcement is a dead end. Unconstrained communication creates an unbounded attack surface for adversarial agents. Instead, pursue: (a) information-theoretic monitoring of communication channels, (b) protocol boundary enforcement (reject messages outside the defined protocol), and (c) conservative initial deployment (start with the minimum necessary communication and expand incrementally).

### Dead End Warning: "Do Not Pursue Trust Without Empirical Validation"

Any trust parameter choice (α_gain, α_loss, t_floor, etc.) without empirical validation against real-world deployment data is suspect. Simulation is necessary but not sufficient — the real world introduces noise, drift, and adversarial conditions that simulations may not capture. Always validate trust parameters against operational data before committing to a deployment configuration.

---

**Document Statistics:** ~7,500 words  
**Cross-References:** 6 primary source documents, 178 bibliography entries (via annotated_bibliography.md), 29 open problems (via open_problems_catalog.md), 10 frontier directions (new), 12-month roadmap  
**Maintainer:** Research Frontiers Builder Agent  
**Review Status:** Ready for review by NEXUS research team
