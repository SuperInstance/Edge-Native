# NEXUS Research Expansion Guide

**Version:** 1.0 | **Date:** 2025-07-15 | **Classification:** Research Strategy — Deep Reference
**Audience:** AI research agents beginning work on NEXUS Iteration 2+ (and beyond)
**Purpose:** Provide the definitive map for continuing the NEXUS research program. This document does not repeat what I1 established — it extends it. Every section contains actionable instructions specific enough that a research agent could begin work immediately.

**Foundation Documents (READ FIRST):**
1. [[context-map.md]] — I1 context map with 15 research threads
2. [[research-frontiers.md]] — I1 frontiers: 29 problems expanded + 10 frontier directions
3. [[methodology.md]] — I1 methodology: evidence standards, quality gates, communication protocols
4. [[open_problems_catalog.md]] — Original 29 open problems with success criteria
5. [[final_synthesis.md]] — A2A grand thesis: Three Pillars, 20 open questions, 36-month roadmap
6. [[claude.md]] — Master project context

---

## Table of Contents

1. [Research Thread Deep-Dives (15 Threads)](#1-research-thread-deep-dives)
2. [The 10 Frontier Directions — Detailed Research Briefs](#2-frontier-direction-research-briefs)
3. [Research Dependency DAG](#3-research-dependency-dag)
4. [Research Agent Assignment Guide (10 Agents, 3 Months)](#4-research-agent-assignment-guide)
5. [Cross-Iteration Research Continuity Protocol](#5-cross-iteration-research-continuity-protocol)

---

## 1. Research Thread Deep-Dives

For each of the 15 threads identified in [[context-map.md]] Section 3, this section provides: a three-paragraph state summary, three critical open questions, recommended approach, key dependencies, estimated difficulty/time, and a specific deliverable. These deep-dives build on the summaries in the context map — they do not repeat them.

### Thread 1: Trust as a Mathematical Concept

**Current State (What's Known):** The INCREMENTS trust algorithm is fully specified with 12 parameters, 6 autonomy levels (L0–L5), and a 25:1 loss-to-gain ratio that encodes a deliberate 22× asymmetry favoring trust loss over trust gain. Fixed-point analysis has proven that T=0, T=1, and T=t_floor are the only stable fixed points. A 365-day simulation validates convergence under stationary event rates, with gain time constant τ_g ≈ 658 windows (27.4 days) and loss time constant τ_l ≈ 29 windows (1.2 days). Cross-domain calibration maps the α_gain/α_loss ratio from 1.3:1 (Home) to 200:1 (Healthcare), encoding the entire domain risk profile in a single number. The 0.5× trust multiplier for agent-generated code is formally proposed and constitutes the single most important A2A-specific safety mechanism.

**Current State (What's Debated):** Whether the trust score's exclusive focus on safety (absence of bad events) rather than utility (presence of good outcomes) is a feature or a bug. The Alignment-Utility Gap (Open Problem 22) argues it is a bug: a system that achieves L5 by never doing anything dangerous passes all checks while being useless. Proponents of the safety-only design counter that mixing safety and utility metrics creates a specification-gaming surface that agents can exploit. The seasonal reset problem — whether bytecode confidence should persist across idle periods while deployment trust decays — is also actively debated with no resolution.

**Current State (What's Unknown):** Whether trust always converges under non-stationary event rates (seasonal changes, A2A-triggered trust events, adversarial manipulation). The fixed-point proof assumes stationarity; the A2A paradigm guarantees non-stationarity. How per-vessel trust divergence affects fleet coordination when vessels at different autonomy levels must execute synchronized maneuvers. Whether trust can be meaningfully "transferred" between agents or vessels without enabling trust inflation attacks. Whether the 25:1 ratio is optimal or merely sufficient.

**Three Critical Open Questions:**
1. **Q-T1-1:** Can we prove Lyapunov stability of the trust dynamics under arbitrary non-stationary inputs (switched dynamical systems with seasonal and adversarial switching), or find a specific counterexample demonstrating bounded oscillation?
2. **Q-T1-2:** Can a utility metric be integrated into the autonomy promotion criteria (beyond L2) without creating a specification-gaming surface that agents exploit?
3. **Q-T1-3:** Can trust evidence be propagated through a fleet-wide trust graph while preventing trust inflation attacks (cycles of mutual endorsement among colluding agents)?

**Recommended Research Approach:** Formal proof (Q-T1-1), simulation-based parameter sweep with game-theoretic adversarial agents (Q-T1-2), and graph-theoretic analysis with cryptographic commitment schemes (Q-T1-3). Q-T1-1 is the highest priority because it is self-contained (no hardware access needed) and its resolution unblocks fleet coordination research.

**Key Dependencies:** Q-T1-2 depends on Thread 4 (Agent as Compiler) for utility metric design. Q-T1-3 depends on Thread 8 (Swarm Intelligence) for fleet-scale validation. Q-T1-1 has no dependencies — it can begin immediately.

**Estimated Difficulty and Time:** Q-T1-1: MEDIUM, 3–4 months (mathematical analysis, well-bounded). Q-T1-2: HIGH, 6–9 months (requires careful metric design and extensive simulation). Q-T1-3: MEDIUM-HIGH, 4–6 months (graph theory is mature, but NEXUS constraints are novel).

**Specific Deliverable:** `trust_dynamics_analysis.md` — A document containing: (a) a Lyapunov stability proof or counterexample for the INCREMENTS algorithm under switched dynamics, (b) a proposed utility-aware autonomy promotion formula with formal gameability analysis, (c) a trust propagation algorithm with formal anti-inflation guarantees. All three should include simulation code (Python) and be structured per [[methodology.md]] Section 4.6 (Simulation Study Pattern).

---

### Thread 2: Bytecode as Lingua Franca

**Current State (What's Known):** The 32-opcode stack-machine ISA is proven Turing-complete for all continuous piecewise-polynomial functions (Stone-Weierstrass theorem applied to {ADD_F, SUB_F, MUL_F, DIV_F, PUSH_F32, CLAMP_F, JUMP_IF_TRUE, WRITE_PIN}). Theorem 3 proves that NaN and Infinity never reach actuator outputs. Compilation from JSON to bytecode is semantics-preserving by structural induction. The Agent-Annotated Bytecode (AAB) format extends bytecode with variable-length TLV metadata at zero execution overhead — agents read metadata, ESP32s receive only the stripped 8-byte core. The 29 proposed new opcodes (intent, communication, capability negotiation, safety augmentation) are all NOP on existing firmware, ensuring backward compatibility.

**Current State (What's Debated):** Whether the 29 new opcodes are sufficient for the A2A paradigm or whether additional opcodes will be needed once multi-agent negotiation is implemented. Whether the intention block concept ( DECLARE_INTENT + ASSERT_GOAL + VERIFY_OUTCOME + EXPLAIN_FAILURE) adequately captures agent intention or whether a richer formalism is needed. Whether the bytecode should carry additional metadata for runtime verification (Direction 9) beyond the current TLV tags.

**Current State (What's Unknown):** Whether the minimum opcode set (8 opcodes) can express all real-world control patterns within acceptable program size bounds (the existing analysis shows trigonometric functions require ~50–100 instruction sequences, but no systematic benchmark of real reflex programs exists). Whether the AAB format's TLV metadata can support the provenance chain requirements for fleet-scale bytecode distribution (Direction 4). Whether the bytecode instruction encoding can be extended to 16-byte instructions without breaking the ESP32's cache-line-aligned parsing.

**Three Critical Open Questions:**
1. **Q-T2-1:** What is the minimum opcode set required to express every control pattern in a benchmark of 500+ real-world reflexes with ≤15% total instruction count increase over the full 32-opcode ISA?
2. **Q-T2-2:** Can the AAB TLV format support a Merkle-tree-based provenance chain for fleet bytecode distribution without exceeding the ESP32's flash storage budget for metadata?
3. **Q-T2-3:** Does the intention block formalism (DECLARE_INTENT + ASSERT_GOAL + VERIFY_OUTCOME) provide sufficient expressiveness for all agent negotiation patterns identified in Frontier Direction 1?

**Recommended Research Approach:** Mechanical opcode elimination analysis (Q-T2-1), storage budget analysis with actual ESP32 flash partition sizes (Q-T2-2), and formal negotiation scenario enumeration against the intention block vocabulary (Q-T2-3). Q-T2-1 can be automated with a script that synthesizes each non-essential opcode from the 8 essential opcodes and measures program size increase.

**Key Dependencies:** Q-T2-3 depends on Frontier Direction 1 (Agent-Agent Bytecode Negotiation) for the negotiation scenario catalog. Q-T2-2 depends on Frontier Direction 4 (Cryptographic Provenance Chains). Q-T2-1 has no dependencies.

**Estimated Difficulty and Time:** Q-T2-1: LOW-MEDIUM, 2–3 months (mechanical analysis). Q-T2-2: MEDIUM, 3–4 months (requires hardware storage specifications). Q-T2-3: MEDIUM, 4–5 months (requires formal negotiation model).

**Specific Deliverable:** `bytecode_lingua_franca_analysis.md` — A document containing: (a) an exhaustive opcode elimination table (24 non-essential opcodes × program size increase), (b) an AAB storage budget analysis with Merkle tree overhead calculations, (c) an intention block expressiveness analysis with gap identification. Include a recommendation for which opcodes to add, remove, or modify.

---

### Thread 3: Safety as Structural Invariant

**Current State (What's Known):** The four-tier defense-in-depth system (hardware interlock, firmware ISR/watchdog, FreeRTOS supervisory task, application-level trust gating) is formally specified with three independence proofs (each tier detects and responds to failures independently). Monte Carlo simulation (1000 iterations) demonstrates SIL 1 compliance (PFH < 10⁻⁷/h) with 97.06% system availability and ~96% diagnostic coverage. The kill switch achieves 0.93ms mechanical response time. Ten universal safety rules plus 40 domain-specific rules (5 per domain) are codified in `safety_policy.json` with a 6-stage validation pipeline.

**Current State (What's Debated):** Whether the SIL 1 target is sufficient for all domains. Healthcare (SIL 3 equivalent) and mining (SIL 2 equivalent) may require higher safety integrity levels that the current architecture cannot achieve without significant redesign. Whether the four-tier model needs a fifth tier for A2A-specific threats (adversarial bytecode, emergent communication, trust score manipulation). Whether the Monte Carlo simulation adequately models common-cause failures that could defeat the independence assumption.

**Current State (What's Unknown):** How to certify continuously evolving bytecode against standards that assume static software artifacts (the Certification Paradox, Open Problem 1). Whether an agent can craft bytecode that passes all structural validation but violates safety at runtime through composition effects (adversarial bytecode, Open Problem 9). The exact per-rule miss rate of the cross-validation pipeline — we know the aggregate is 4.9% but not which specific rules are most likely missed. The behavior under arbitrary multi-node failure combinations beyond the 5 stress scenarios simulated.

**Three Critical Open Questions:**
1. **Q-T3-1:** Can a Predetermined Change Control Plan (PCCP) satisfy IEC 61508 SIL 1 requirements for the A2A bytecode evolution process, given that individual bytecodes cannot be statically certified?
2. **Q-T3-2:** What is the per-rule miss rate of the cross-validation pipeline (Claude 3.5 Sonnet validating Qwen2.5-Coder-7B), and can triangulated validation (3 validators, majority vote) reduce the worst-case per-rule miss rate below 0.5%?
3. **Q-T3-3:** Can composition analysis (verifying joint safety of all concurrently executing bytecodes, not just individual safety) be implemented within the ESP32's computational and memory budget?

**Recommended Research Approach:** Regulatory engagement + formal process modeling (Q-T3-1), systematic adversarial benchmark construction and calibration (Q-T3-2), and abstract interpretation over composed bytecodes with resource constraint analysis (Q-T3-3). Q-T3-2 is the highest priority because it produces actionable data within 3 months that directly improves system safety.

**Key Dependencies:** Q-T3-1 depends on Thread 12 (Regulatory Compliance). Q-T3-3 depends on Thread 2 (Bytecode) for the composition model. Q-T3-2 depends on Thread 4 (Agent as Compiler) for the bytecode generation pipeline.

**Estimated Difficulty and Time:** Q-T3-1: HIGH, 12–18 months (regulatory engagement is slow and uncertain). Q-T3-2: MEDIUM, 3–4 months (benchmarking is straightforward). Q-T3-3: HIGH, 6–9 months (abstract interpretation over composed programs is theoretically challenging).

**Specific Deliverable:** `safety_invariant_analysis.md` — A document containing: (a) a PCCP draft suitable for Lloyd's Register pre-assessment, (b) a per-rule miss rate calibration table with 5,000-bytecode benchmark results, (c) a composition analysis feasibility study with resource budget calculations for ESP32 implementation.

---

### Thread 4: Agent as Compiler

**Current State (What's Known):** The system-prompt-as-compiler concept is formalized: the system prompt defines input grammar (natural language), output grammar (JSON reflex schema), semantic constraints (safety rules), and compilation guarantees (semantic preservation, determinism, type safety). Current performance: 96% schema compliance (enabled by GBNF grammar constraints), 87% semantic correctness, 82% safety adherence, 92% structural quality. Cross-agent validation (Qwen2.5-Coder-7B generates, Claude 3.5 Sonnet validates) achieves 93.3% catch rate on safety issues. The 0.5× trust multiplier for agent-generated code provides an explicit epistemic humility margin.

**Current State (What's Debated):** Whether the system prompt should be treated as a single monolithic entity or decomposed into modular components (domain context, safety rules, trust state, constraint language). Monolithic prompts are simpler but harder to optimize; modular prompts enable domain-specific tuning but introduce composition complexity. Whether few-shot examples in the prompt improve or degrade generalization — they may cause the model to overfit to the provided examples.

**Current State (What's Unknown):** The optimal system prompt configuration (currently ad-hoc, no systematic optimization has been conducted). Whether Bayesian optimization over the prompt space can achieve ≥99% schema compliance and ≥90% safety adherence. Whether cultural bias in the LLM's training data produces systematically unsafe bytecodes for non-Western regulatory contexts. Whether the NL→JSON compilation stage loses more information than the JSON→bytecode stage (information-theoretic analysis needed).

**Three Critical Open Questions:**
1. **Q-T4-1:** Can Bayesian optimization over the system prompt space achieve ≥99% schema compliance and ≥90% safety adherence on a benchmark of 500 reflex generation tasks?
2. **Q-T4-2:** What is the per-stage information loss in the NL→JSON→bytecode→assembly→hardware pipeline, measured by mutual information between the natural-language intent and each intermediate representation?
3. **Q-T4-3:** Does cultural bias in LLM training data produce measurable compliance gaps when generating bytecodes for non-Western regulatory contexts (IMO, Indonesian maritime, EU machinery directive)?

**Recommended Research Approach:** Bayesian optimization with Optuna (Q-T4-1), information-theoretic pipeline audit with paired intent-bytecode samples (Q-T4-2), and controlled cultural bias audit across 4 regulatory contexts (Q-T4-3). Q-T4-1 is the highest-leverage intervention because the system prompt controls the quality of all generated bytecodes — a 1% improvement in safety adherence across the fleet has outsized implications.

**Key Dependencies:** Q-T4-3 depends on Thread 5 (Safety as Cultural Universal) for cultural context. Q-T4-1 depends on access to the Qwen2.5-Coder-7B inference pipeline. All three can proceed in parallel.

**Estimated Difficulty and Time:** Q-T4-1: MEDIUM, 3–4 months (requires inference infrastructure but methodology is well-established). Q-T4-2: MEDIUM, 3–4 months (requires paired samples and information-theoretic analysis). Q-T4-3: MEDIUM, 4–5 months (requires regulatory domain expertise).

**Specific Deliverable:** `agent_compiler_analysis.md` — A document containing: (a) an optimized system prompt with documented improvement metrics, (b) an information-theoretic pipeline audit with mutual information calculations per stage, (c) a cultural bias audit report with per-context compliance rates and mitigation strategies.

---

### Thread 5: Safety as Cultural Universal

**Current State (What's Known):** Eight cultural traditions (Western Analytic, Daoist, Confucian, Soviet Engineering, African Ubuntu, Indigenous, Japanese, Islamic Golden Age) have been analyzed through the NEXUS design lens. Five universal themes emerged with 7–8/8 consensus: (1) Intelligence is relational, not atomic; (2) Purpose must be earned, not declared; (3) Constraints enable rather than restrict; (4) Knowledge must include narrative context; (5) Balance requires oscillation, not static equilibrium. Eight concrete specification changes have been proposed based on this analysis. The 150× variation in trust α_gain/α_loss ratios across domains correlates with cultural risk tolerance profiles.

**Current State (What's Debated):** Whether the five universal themes represent genuine universals or an artifact of the eight traditions selected for analysis. Adding a ninth or tenth tradition (e.g., Andean, Pacific Islander) might reveal additional themes or contradict existing ones. Whether the proposed specification changes would measurably improve trust calibration in practice, or whether they are theoretically sound but practically negligible.

**Current State (What's Unknown):** Whether Japanese and Islamic Golden Age lenses should be expanded from summaries within the eight-lenses analysis to standalone documents (as Greek, Chinese, Soviet, and African lenses already are). Whether the Indigenous lens analysis (marked "phase 1") can be completed to phase 2 depth. Whether the cultural design principles produce measurable differences in operator trust and system acceptance across cultures.

**Three Critical Open Questions:**
1. **Q-T5-1:** Do the 8 proposed specification changes from cultural analysis measurably improve trust calibration and operator acceptance when deployed across multiple cultural contexts?
2. **Q-T5-2:** Does adding a ninth cultural lens (e.g., Andean "buen vivir" philosophy) reveal any themes not captured by the existing five universals, or does it merely reinforce them?
3. **Q-T5-3:** Can cultural risk tolerance profiles be quantified precisely enough to derive trust α parameters algorithmically, rather than by expert judgment?

**Recommended Research Approach:** Survey-based validation study with operators from 4+ cultures (Q-T5-1), systematic cultural lens expansion and comparative analysis (Q-T5-2), and cross-cultural psychometric calibration against existing risk tolerance instruments (Q-T5-3). Q-T5-1 is the most impactful because it tests whether the philosophical analysis translates to practical engineering benefit.

**Key Dependencies:** Q-T5-1 depends on Thread 1 (Trust) for trust calibration methodology. Q-T5-3 depends on Thread 7 (Cross-Domain) for domain-specific parameter values. All three can proceed in parallel with limited dependencies.

**Estimated Difficulty and Time:** Q-T5-1: MEDIUM-HIGH, 6–9 months (requires human subjects, IRB approval, multi-site coordination). Q-T5-2: MEDIUM, 3–4 months (philosophical analysis). Q-T5-3: HIGH, 6–9 months (requires psychometric expertise and cross-cultural data).

**Specific Deliverable:** `cultural_safety_analysis.md` — A document containing: (a) a survey instrument for measuring operator trust calibration across cultures, (b) an expanded cultural lens analysis with 9th tradition, (c) a proposed algorithmic trust parameter derivation method with validation criteria.

---

### Thread 6: Evolutionary Code

**Current State (What's Known):** The NEXUS knowledge base maps the full space of evolutionary computation (GA/GP/ES/DE) to NEXUS concepts: bytecode is a "genotype," the fleet is a "population," seasonal mutation rates (Spring 30% → Autumn 5%) map to Langton's Lambda parameter on the order-chaos spectrum. The "adaptive safety" concept proposes that 2–3% of nodes operate with reduced safety rules as evolutionary probes. The Griot narrative layer serves as "genetic memory," preserving knowledge across bytecode generations. The AAB format's intention blocks provide a natural genotype-phenotype mapping.

**Current State (What's Debated):** Whether genetic algorithms can compete with LLM-based program synthesis for bytecode quality and convergence speed. GAs are theoretically well-grounded but slow on complex control tasks; LLMs are fast but probabilistically unreliable. Whether the "evolutionary safety boundary" experiment (2–3% probe nodes with reduced rules) is compatible with the four-tier safety system — Tier 1 hardware safety is non-negotiable, but the boundary between Tier 2 firmware safety and Tier 3 application safety is debated.

**Current State (What's Unknown):** The protocol for safe fleet-level bytecode sharing — how an evolved bytecode on Vessel A is validated, transferred, and deployed on Vessel B while preserving per-vessel trust independence and preventing cascade contamination. Whether fleet-level learning converges to fleet-optimal bytecodes or fragments into per-vessel local optima. Whether the GA approach can discover solutions that LLM synthesis cannot (novel control strategies beyond the training distribution).

**Three Critical Open Questions:**
1. **Q-T6-1:** What protocol enables safe fleet-level bytecode sharing while preserving per-vessel trust independence and preventing cascade contamination of unsafe bytecodes across the fleet?
2. **Q-T6-2:** Can a safety-constrained genetic algorithm (mutation within safe ranges, crossover preserving intention blocks) produce bytecodes of comparable quality to LLM synthesis for well-characterized control tasks?
3. **Q-T6-3:** Does fleet-level bytecode sharing converge to fleet-optimal solutions, or does per-vessel environmental diversity cause fragmentation into local optima?

**Recommended Research Approach:** Protocol design with formal verification of safety properties (Q-T6-1), head-to-head comparison of GA and LLM synthesis on benchmark tasks (Q-T6-2), and fleet simulation with environmental diversity parameters (Q-T6-3). Q-T6-1 is the most critical because fleet-level sharing is essential for the NEXUS value proposition but currently has no protocol.

**Key Dependencies:** Q-T6-1 depends on Thread 8 (Swarm Intelligence) for fleet communication infrastructure. Q-T6-2 depends on Thread 2 (Bytecode) for the fitness function specification. Q-T6-3 depends on Thread 1 (Trust) for convergence metrics.

**Estimated Difficulty and Time:** Q-T6-1: MEDIUM-HIGH, 6–9 months (protocol design + formal verification). Q-T6-2: MEDIUM, 4–6 months (GA implementation + benchmarking). Q-T6-3: MEDIUM, 3–4 months (simulation study).

**Specific Deliverable:** `evolutionary_code_analysis.md` — A document containing: (a) a fleet bytecode sharing protocol specification with formal safety guarantees, (b) a GA vs. LLM synthesis comparison on 10 benchmark control tasks with quality and convergence metrics, (c) a fleet convergence analysis under varying environmental diversity conditions.

---

### Thread 7: Cross-Domain Generalization

**Current State (What's Known):** Eighty percent code reuse is validated across 8 domains via a 25-attribute comparison matrix. Four natural domain clusters are identified (Extreme Safety, Industrial Safety, Moderate Automation, Consumer/Low-Risk). Trust α_gain/α_loss ratios are calibrated for all 8 domains. Forty domain-specific safety rules are defined (5 per domain). Maximum agent code autonomy levels range from L1 (Healthcare) to L5 (Home). Thirteen MCU compatibility evaluations with porting effort estimates are complete.

**Current State (What's Debated):** Whether the 80/20 split (80% universal / 20% domain-specific) is a fundamental architectural property or an artifact of the current analysis granularity. A finer-grained analysis might reveal that some domains share domain-specific components (e.g., marine and agriculture both need GPS-based navigation) that could be factored into the universal core. Whether domain-specific protocol adapters (ISOBUS, BACnet, Matter) should be implemented as Jetson-side services or ESP32-side firmware.

**Current State (What's Unknown):** Whether specialized agents (fine-tuned on domain data) produce meaningfully better bytecodes than general agents with domain-specific system prompt prefixes. No formal study has been conducted. Whether bytecodes evolved for one domain can be safely transferred to another (domain transfer learning). Whether the healthcare domain's extreme regulatory requirements (200:1 trust ratio, L1 maximum autonomy) make A2A-native programming economically viable in that domain.

**Three Critical Open Questions:**
1. **Q-T7-1:** Can a general-purpose agent with domain-specific system prompt prefixes match the bytecode quality of a domain-specialized fine-tuned agent across all 8 domains?
2. **Q-T7-2:** What validation protocol is required when transferring a bytecode from one domain to another, and does the transferred bytecode maintain safety compliance in the target domain?
3. **Q-T7-3:** Is A2A-native programming economically viable in the Healthcare domain given the 200:1 trust ratio and L1 maximum autonomy ceiling?

**Recommended Research Approach:** Controlled fine-tuning experiment with quality benchmarks (Q-T7-1), formal transfer analysis with domain-specific safety rule verification (Q-T7-2), and economic viability model with cost-benefit analysis (Q-T7-3). Q-T7-1 is the most impactful because it determines the development and deployment strategy for the entire agent ecology.

**Key Dependencies:** Q-T7-1 depends on Thread 4 (Agent as Compiler) for the prompt optimization infrastructure. Q-T7-2 depends on Thread 3 (Safety) for the safety rule verification pipeline. Q-T7-3 depends on Thread 12 (Regulatory Compliance) for healthcare regulatory requirements.

**Estimated Difficulty and Time:** Q-T7-1: MEDIUM, 4–6 months (requires fine-tuning infrastructure). Q-T7-2: MEDIUM, 3–4 months (formal analysis). Q-T7-3: LOW-MEDIUM, 2–3 months (economic modeling).

**Specific Deliverable:** `cross_domain_analysis.md` — A document containing: (a) a comparative quality analysis of specialized vs. general agents with benchmark results, (b) a domain transfer protocol specification with safety verification requirements, (c) an economic viability model for each domain with cost-benefit projections.

---

### Thread 8: Swarm Intelligence and Multi-Agent Coordination

**Current State (What's Known):** The self-organizing systems knowledge base provides the theoretical framework (CAS, swarm intelligence, emergence, autopoiesis, free energy principle). Three agent communication patterns are proposed: Proposal-Validation-Deployment (sequential pipeline), Peer Negotiation (resource allocation), Communal Veto (ESP32 collective rejection). Network architecture analysis recommends 5-Jetson topology with Raft consensus. Five concrete coordination scenarios are documented. The A2A wire protocol extensions include AGENT_PROPOSE, AGENT_VALIDATE, VOTE_REJECT, PALAVER_FLAG messages.

**Current State (What's Debated):** Whether the A/B testing bottleneck (60 minutes = 99.96% of deployment latency) is a feature (ensuring thorough validation) or a bug (preventing rapid agent coordination in time-critical scenarios). The current design treats this as a feature, but collision avoidance and formation maneuvers may require faster coordination. Whether hierarchical fleet organization (sub-fleets of 10–20 vessels with elected representatives) is necessary for scalability beyond 50 vessels.

**Current State (What's Unknown):** The minimum viable coordination primitives for safe fleet-scale operation. Whether emergent communication channels (agents encoding information in telemetry, event ring buffers, or shared registers) can bypass the designed safety infrastructure. Whether the communal veto mechanism can reach consensus fast enough to prevent deployment of unsafe bytecodes in time-critical scenarios.

**Three Critical Open Questions:**
1. **Q-T8-1:** What are the minimum viable multi-agent coordination primitives that enable safe fleet-scale operation without exhaustive interaction analysis?
2. **Q-T8-2:** Can the A/B testing duration be dynamically calibrated based on domain risk level and bytecode complexity (60 minutes for Marine collision avoidance, 5 minutes for Home thermostat adjustment)?
3. **Q-T8-3:** Does information-theoretic anomaly detection on inter-agent communication channels reliably detect emergent communication that bypasses the designed protocol?

**Recommended Research Approach:** Coordination primitive enumeration and minimal-sufficient-set analysis (Q-T8-1), risk-based A/B test duration calibration with simulation (Q-T8-2), and entropy-rate monitoring with adversarial agent simulation (Q-T8-3). Q-T8-1 is the most critical because the current coordination infrastructure exists only as proposals — nothing has been implemented.

**Key Dependencies:** Q-T8-1 depends on Thread 2 (Bytecode) for the bytecode negotiation model. Q-T8-2 depends on Thread 3 (Safety) for risk classification. Q-T8-3 depends on Thread 6 (Evolutionary Code) for the adversarial agent model.

**Estimated Difficulty and Time:** Q-T8-1: HIGH, 6–9 months (protocol design + formal verification + implementation). Q-T8-2: MEDIUM, 3–4 months (simulation study). Q-T8-3: MEDIUM, 4–5 months (anomaly detection development + testing).

**Specific Deliverable:** `swarm_coordination_analysis.md` — A document containing: (a) a minimal coordination primitive set with formal safety properties, (b) a dynamic A/B test duration calibration formula with validation results, (c) an emergent communication detection system with entropy-rate monitoring specifications.

---

### Thread 9: Formal Verification vs. Learning-Based Assurance

**Current State (What's Known):** Formal verification is achievable for structural properties: stack balance, jump targets, NaN/Inf freedom (Theorem 3), cycle budget compliance. The 32-opcode VM enables single-pass validation in O(n) time. The Curry-Howard correspondence is identified as a theoretical bridge but NEXUS bytecode operates below the Curry-Howard threshold (no dependent types, no proof terms). The 6-step agent validation pipeline (generate → structural check → semantic check → A/B test → trust gate → deploy) combines formal and empirical methods. Cross-model validation (93.3% catch rate) provides practical but not principled assurance.

**Current State (What's Debated):** Whether abstract interpretation over the 32-opcode ISA can provide bounded output ranges that serve as lightweight formal verification for behavioral safety properties. Proponents argue that interval arithmetic on sensor inputs and actuator outputs is decidable and efficient; skeptics note that PID_COMPUTE (an opaque syscall) cannot be analyzed without modeling the controller as a linear transfer function, which may introduce unacceptable approximation errors. Whether proof-carrying bytecode is feasible given the ESP32's computational constraints.

**Current State (What's Unknown):** Whether the gap between formal verification (strong but narrow) and learning-based assurance (broad but weak) can be bridged by a hybrid approach. Whether any existing neural network verification tool (Marabou, Reluplex, NNenum) can scale to the 7-billion-parameter Qwen model. Whether runtime verification (Direction 9) can catch behavioral anomalies that static validation misses within the ESP32's resource budget.

**Three Critical Open Questions:**
1. **Q-T9-1:** Can interval arithmetic over the 32-opcode ISA (extended to model PID_COMPUTE as a linear transfer function) provide bounded actuator output ranges for all reflex programs within 60 seconds per reflex on Jetson hardware?
2. **Q-T9-2:** Can a hybrid verification approach (formal structural checks + abstract interpretation for output bounds + runtime monitoring for behavioral anomalies) achieve a combined false-negative rate below 0.1%?
3. **Q-T9-3:** Is proof-carrying bytecode feasible for the NEXUS ISA, given that the proof must be verifiable on the Jetson (not the ESP32) and the proof size must not exceed the wire protocol's payload limit?

**Recommended Research Approach:** Abstract interpretation implementation with interval arithmetic (Q-T9-1), hybrid verification architecture design with false-negative rate analysis (Q-T9-2), and proof-carrying bytecode feasibility study (Q-T9-3). Q-T9-1 is the highest priority because it is the most concrete path to "safe by construction" rather than "safe by validation."

**Key Dependencies:** Q-T9-1 depends on Thread 2 (Bytecode) for the ISA specification. Q-T9-2 depends on Q-T9-1. Q-T9-3 depends on Thread 3 (Safety) for certification requirements.

**Estimated Difficulty and Time:** Q-T9-1: MEDIUM-HIGH, 4–6 months (implementation + benchmarking). Q-T9-2: HIGH, 6–9 months (architecture design + integration). Q-T9-3: HIGH, 6–9 months (theoretical analysis + prototype).

**Specific Deliverable:** `verification_hybrid_analysis.md` — A document containing: (a) an abstract interpretation implementation with benchmark results on 500 reflexes, (b) a hybrid verification architecture specification with false-negative rate projections, (c) a proof-carrying bytecode feasibility report with complexity analysis.

---

### Thread 10: The Ribosome Metaphor and Biological Computation

**Current State (What's Known):** The ribosome metaphor is the project's founding principle: distribute cognition to the periphery rather than centralizing it in a "brain." The biological computation knowledge base maps DNA→RNA→protein to intention→bytecode→action. The MYCELIUM architecture provides a detailed biological metaphor. IoT-as-protein architecture maps sensors/actuators to biological proteins. The universal principle — "distributed local > centralized" — is validated across biology, computing, organization theory, and philosophy (7–8/8 cultural consensus).

**Current State (What's Debated):** Whether the biological metaphor is merely inspirational or whether it suggests specific computational mechanisms that should be implemented. Epigenetic regulation (environment-dependent gene expression), immune system analogues (detecting and rejecting "foreign" bytecodes), and horizontal gene transfer (fleet-level bytecode sharing) have been identified as biological analogues but not formally mapped to NEXUS mechanisms.

**Current State (What's Unknown):** Whether biological metaphors suggest any computational mechanisms not yet explored in NEXUS. Whether the "evolutionary safety boundary" concept (2–3% probe nodes) has a biological analogue or is a novel engineering concept without biological grounding. Whether the Griot narrative layer can be formalized as a "genetic memory" with proper encoding/decoding specifications.

**Three Critical Open Questions:**
1. **Q-T10-1:** Do biological mechanisms (epigenetic regulation, immune rejection, horizontal gene transfer, apoptotic cell death) suggest computational mechanisms that would improve NEXUS safety, learning, or coordination?
2. **Q-T10-2:** Can the Griot narrative layer be formalized as a genetic memory with a proper encoding specification (what information is preserved, how it is compressed, how it is retrieved)?
3. **Q-T10-3:** Does the ribosome metaphor provide a formal optimization principle (e.g., minimize communication between levels, maximize local computation) that can guide NEXUS architecture decisions?

**Recommended Research Approach:** Systematic biological-computational mapping exercise (Q-T10-1), narrative encoding specification design (Q-T10-2), and formal optimization principle derivation (Q-T10-3). This thread is primarily conceptual — its value lies in generating novel architectural ideas rather than producing directly implementable specifications.

**Key Dependencies:** Q-T10-2 depends on Thread 6 (Evolutionary Code) for the Griot narrative context. Q-T10-3 depends on Thread 13 (Hardware-Software Co-Design) for architectural trade-off analysis.

**Estimated Difficulty and Time:** Q-T10-1: MEDIUM, 3–4 months (literature analysis + creative synthesis). Q-T10-2: MEDIUM, 3–4 months (specification design). Q-T10-3: LOW-MEDIUM, 2–3 months (theoretical analysis).

**Specific Deliverable:** `biological_metaphor_analysis.md` — A document containing: (a) a systematic mapping of 10+ biological mechanisms to NEXUS computational analogues with implementation feasibility assessment, (b) a Griot narrative encoding specification, (c) a formal optimization principle derived from the ribosome metaphor with application to NEXUS architecture decisions.

---

### Thread 11: Post-Coding Paradigm and the Role of Humans

**Current State (What's Known):** NEXUS operates at L4–L5 coding autonomy: humans describe intent, agents generate code. The operator's role shifts from programmer to supervisor/governor. The 0.5× trust rule creates explicit epistemic humility about agent-generated code. The Griot narrative layer preserves human-readable explanations. The kill switch provides absolute human override capability.

**Current State (What's Debated):** Whether the elimination of human code review creates an ethical obligation for enhanced transparency and explainability. Whether the governance framework should include human-in-the-loop checkpoints beyond the kill switch (e.g., requiring human approval for L4+ deployments, not just L5). Whether the "many hands" responsibility chain (9+ agents) is legally manageable or requires a statutory innovation.

**Current State (What's Unknown):** What governance framework assigns proportional responsibility across the 9+ agent chain while maintaining A2A efficiency. Whether human operators can effectively supervise 50–500 autonomous vessels generating and deploying bytecodes in real-time (cognitive load question). Whether a "digital constitution" (Frontier Direction 10) can provide machine-checkable governance for agent autonomy.

**Three Critical Open Questions:**
1. **Q-T11-1:** What governance framework assigns proportional responsibility across the 9+ agent chain while maintaining the efficiency benefits of A2A-native programming?
2. **Q-T11-2:** Can a fleet supervision interface designed using cognitive load theory enable a single human operator to effectively supervise 50+ autonomous vessels?
3. **Q-T11-3:** Does a "digital constitution" expressed in machine-checkable logic provide adequate governance for agent autonomy without over-constraining useful agent behavior?

**Recommended Research Approach:** Legal-philosophical analysis with engagement from maritime law and AI ethics scholars (Q-T11-1), cognitive load theory-based interface design with human-in-the-loop testing (Q-T11-2), and constitutional logic design with formal verification (Q-T11-3).

**Key Dependencies:** Q-T11-1 depends on Thread 12 (Regulatory Compliance) for legal frameworks. Q-T11-2 depends on Thread 8 (Swarm Intelligence) for fleet supervision requirements. Q-T11-3 depends on Frontier Direction 10.

**Estimated Difficulty and Time:** Q-T11-1: HIGH, 6–9 months (requires legal expertise and multi-stakeholder engagement). Q-T11-2: MEDIUM-HIGH, 4–6 months (requires human subjects testing). Q-T11-3: MEDIUM-HIGH, 6–9 months (constitutional logic design is novel).

**Specific Deliverable:** `post_coding_governance_analysis.md` — A document containing: (a) a proportional responsibility framework for the 9+ agent chain with legal analysis, (b) a fleet supervision interface specification with cognitive load budgets, (c) a digital constitution draft in machine-checkable logic with expressiveness analysis.

---

### Thread 12: Regulatory Compliance and Certification

**Current State (What's Known):** Six safety standards analyzed (IEC 61508, ISO 26262, DO-178C, IEC 62061, ISO 13849, IEC 60945). Ninety-three compliance gaps identified with 25% current certification readiness. Eighteen-month SIL 1 certification path mapped. NEXUS targets IEC 61508 SIL 1. EU AI Act compliance requires ~€180K–€480K. The PCCP concept is identified as a potential bridge for the certification paradox.

**Current State (What's Debated):** Whether a single certification approach can satisfy multiple regulatory frameworks simultaneously (regulatory convergence). Whether the PCCP concept will be accepted by certification bodies for an A2A system (no precedent exists). Whether the EU AI Act's requirement for human oversight of high-risk AI systems is compatible with A2A-native programming's L4–L5 autonomy levels.

**Current State (What's Unknown):** Whether Lloyd's Register (or any maritime certification body) will accept a PCCP-based certification for continuously evolving bytecodes. How to satisfy the EU AI Act's "human oversight" requirement for systems that operate at L4+ autonomy. Whether the 93 identified gaps can be reduced to ≤20 within 18 months through targeted specification development.

**Three Critical Open Questions:**
1. **Q-T12-1:** Will Lloyd's Register accept a PCCP-based SIL 1 certification for A2A-generated bytecodes, and if not, what modifications to the PCCP are required?
2. **Q-T12-2:** How can the EU AI Act's "human oversight" requirement be satisfied for A2A systems operating at L3+ autonomy, given that the human cannot meaningfully review agent-generated bytecodes at deployment speed?
3. **Q-T12-3:** Can a harmonized safety case architecture satisfy the evidence requirements of IEC 61508, ISO 26262, and EU AI Act simultaneously, reducing the total certification effort by ≥30%?

**Recommended Research Approach:** Regulatory engagement with Lloyd's Register for pre-assessment (Q-T12-1), legal analysis of EU AI Act human oversight requirements with proposed compliance architecture (Q-T12-2), and safety case harmonization study mapping evidence requirements across standards (Q-T12-3). Q-T12-1 is the most impactful because a positive pre-assessment unblocks the entire certification path.

**Key Dependencies:** Q-T12-1 depends on Thread 3 (Safety) for the safety case evidence. Q-T12-2 depends on Thread 11 (Post-Coding Paradigm) for the governance framework. Q-T12-3 depends on Thread 7 (Cross-Domain) for multi-domain requirements.

**Estimated Difficulty and Time:** Q-T12-1: HIGH, 12–18 months (regulatory engagement is slow and uncertain). Q-T12-2: MEDIUM-HIGH, 6–9 months (legal analysis + compliance architecture). Q-T12-3: MEDIUM, 4–6 months (comparative analysis).

**Specific Deliverable:** `regulatory_compliance_analysis.md` — A document containing: (a) a Lloyd's Register pre-assessment request package with draft PCCP, (b) an EU AI Act human oversight compliance architecture, (c) a harmonized safety case template mapping evidence requirements across IEC 61508, ISO 26262, and EU AI Act.

---

### Thread 13: Hardware-Software Co-Design

**Current State (What's Known):** ESP32-S3 selected as Tier 1 ($6–10, best price/performance/IO). Jetson Orin Nano as Tier 2 (40 TOPS, 8GB, 8–15W). Complete memory map with SRAM/PSRAM budgets. Thirteen MCU compatibility evaluations. BOM at $684 per vessel. Zero-heap design. Power/thermal analysis complete. Qwen2.5-Coder-7B runs at Q4_K_M quantization (4.2GB VRAM, 17.2 tok/s).

**Current State (What's Debated):** Whether the Jetson Orin Nano Super (67 TOPS, $249) provides enough headroom for future model upgrades without exceeding the BOM budget. Whether TensorRT optimization can improve inference speed beyond 17.2 tok/s without sacrificing accuracy. Whether porting to ARM Cortex-M4 MCUs (STM32H7) would provide sufficient performance at lower cost.

**Current State (What's Unknown):** The minimum Jetson-class hardware that can run Qwen2.5-Coder-7B at ≥10 tok/s while leaving resources for the learning pipeline. Whether the ESP32-S3's 512KB SRAM is sufficient for the runtime verification task (Direction 9). Whether hardware-in-the-loop testing validates the timing and power budgets assumed in the specifications.

**Three Critical Open Questions:**
1. **Q-T13-1:** What is the minimum Tier 2 hardware (TOPS, RAM, storage, power) that can run the full A2A agent ecology (inference + learning pipeline + validation + coordination) without performance degradation?
2. **Q-T13-2:** Can runtime verification be added to the ESP32-S3's firmware within the 5,280-byte runtime memory budget and 10% CPU utilization ceiling?
3. **Q-T13-3:** Does hardware-in-the-loop testing validate the assumed timing budgets (44μs VM execution, <20ms sensor-to-actuator pipeline) under worst-case conditions (I²C contention, UART queuing, dual-core contention)?

**Recommended Research Approach:** Hardware benchmarking with TensorRT optimization (Q-T13-1), memory and CPU budget analysis with firmware prototype (Q-T13-2), and HIL testing with logic analyzers (Q-T13-3).

**Key Dependencies:** Q-T13-2 depends on Thread 9 (Formal Verification) for the runtime verification logic. Q-T13-3 depends on Thread 3 (Safety) for the timing requirements. Q-T13-1 has no dependencies.

**Estimated Difficulty and Time:** Q-T13-1: MEDIUM, 3–4 months (requires hardware access). Q-T13-2: MEDIUM, 3–4 months (firmware prototype). Q-T13-3: MEDIUM, 4–5 months (requires HIL test rig).

**Specific Deliverable:** `hw_sw_codesign_analysis.md` — A document containing: (a) a minimum hardware specification table for Tier 2 with TensorRT optimization results, (b) a runtime verification memory/CPU budget analysis, (c) HIL timing validation results with comparison to specified worst-case bounds.

---

### Thread 14: Learning and Pattern Discovery

**Current State (What's Known):** Five pattern discovery algorithms specified (cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference). A/B testing framework with 60-minute minimum duration. End-to-end pipeline: 44μs execution, 20–40× faster than traditional development. The 60-minute A/B test is 99.96% of deployment latency — the natural throttle. Six-stage pipeline: Observe → Record → Discover → Synthesize → A/B Test → Deploy.

**Current State (What's Debated):** Whether the 60-minute A/B test is too conservative for low-risk domains (Home, HVAC) where faster iteration would accelerate learning. Whether inverse reinforcement learning (identified but LOW confidence) should be pursued or abandoned. Whether the multi-reflex variable collision problem (73% rate) should be solved by namespace isolation (per-reflex variable tables, 256 bytes) or by a more sophisticated approach.

**Current State (What's Unknown):** Whether dynamic A/B test duration calibration (based on domain risk and bytecode complexity) can maintain safety while reducing deployment latency. Whether online/incremental learning (updating pattern models in real-time rather than batch processing) is feasible on Jetson hardware. Whether the pattern discovery algorithms can detect and adapt to non-stationary environments (seasonal changes, equipment degradation).

**Three Critical Open Questions:**
1. **Q-T14-1:** Can the A/B testing duration be dynamically calibrated based on domain risk level and bytecode complexity while maintaining the same safety assurance level as the fixed 60-minute test?
2. **Q-T14-2:** Can online/incremental learning be implemented on Jetson Orin Nano hardware for the BOCPD and cross-correlation algorithms without exceeding the 8GB RAM budget?
3. **Q-T14-3:** Do the pattern discovery algorithms maintain detection quality under non-stationary conditions (seasonal changes, sensor drift, actuator degradation)?

**Recommended Research Approach:** Statistical analysis of A/B test duration vs. safety event detection rate (Q-T14-1), memory and compute profiling of online learning algorithms (Q-T14-2), and non-stationary detection quality benchmarking (Q-T14-3). Q-T14-1 is the most impactful because reducing A/B test duration directly increases the system's learning speed.

**Key Dependencies:** Q-T14-1 depends on Thread 3 (Safety) for risk classification. Q-T14-2 depends on Thread 13 (Hardware-Software Co-Design) for resource budgets. Q-T14-3 depends on Thread 7 (Cross-Domain) for domain-specific non-stationarity patterns.

**Estimated Difficulty and Time:** Q-T14-1: MEDIUM, 3–4 months (statistical analysis). Q-T14-2: MEDIUM, 3–4 months (profiling + optimization). Q-T14-3: MEDIUM, 3–4 months (benchmarking).

**Specific Deliverable:** `learning_pipeline_analysis.md` — A document containing: (a) a dynamic A/B test duration calibration formula with safety validation, (b) an online learning feasibility study with memory/compute budgets, (c) a non-stationary detection quality report with recommendations.

---

### Thread 15: Documentation as Living System

**Current State (What's Known):** The Rosetta Stone concept creates dual-lens documentation (human specs + agent-native specs). Wiki-links connect documents into a knowledge graph. The A2A-native specs are machine-readable. The 310-term glossary provides shared vocabulary. The open problems catalog provides a research roadmap. The `claude.md` file is both a reference document and a functional system prompt.

**Current State (What's Debated):** Whether automated documentation consistency checking is feasible given the repository's size (~1.1M words across ~167 documents). Whether wiki-links should be bidirectional (if document A links to B, should B automatically link back to A?). Whether the genesis-colony documents should be actively maintained or archived as historical reference.

**Current State (What's Unknown):** How to automatically update the Rosetta Stone when human specs change (currently manual). How to detect and flag broken or stale wiki-links. How to index the genesis-colony documents so their valuable ideas are discoverable by research agents.

**Three Critical Open Questions:**
1. **Q-T15-1:** Can an automated documentation consistency checker be implemented that detects contradictions, broken links, and stale cross-references across the ~167-document repository?
2. **Q-T15-2:** Can a bidirectional link maintenance system be implemented that automatically updates wiki-links when documents are added, renamed, or restructured?
3. **Q-T15-3:** Can the genesis-colony documents be systematically indexed to extract actionable ideas that feed into the active research threads?

**Recommended Research Approach:** Build a link-graph crawler with consistency checking rules (Q-T15-1), implement a wiki-link maintenance tool with git hooks (Q-T15-2), and conduct a systematic review of genesis-colony documents with idea extraction (Q-T15-3). This thread is lower priority than the others but provides essential infrastructure for long-term knowledge management.

**Key Dependencies:** No significant dependencies — this thread operates on the documentation layer independently of the research content.

**Estimated Difficulty and Time:** Q-T15-1: MEDIUM, 2–3 months (link crawler + rule engine). Q-T15-2: LOW-MEDIUM, 1–2 months (tooling). Q-T15-3: MEDIUM, 3–4 months (manual review + extraction).

**Specific Deliverable:** `documentation_system_analysis.md` — A document containing: (a) a documentation consistency checker specification with rule catalog, (b) a wiki-link maintenance tool design, (c) a genesis-colony idea extraction report with 20+ actionable ideas mapped to active research threads.

---

## 2. The 10 Frontier Directions — Detailed Research Briefs

### Direction 1: Formal Semantics of Agent-Agent Bytecode Negotiation

**Full Problem Statement:**
Given two agents A and B that both write to actuator register R with priorities p_A and p_B, the current resolution is last-writer-wins within a tick cycle. We require a negotiation calculus N such that:
- Each proposal π is a bytecode delta: π ∈ Δ(bytecode) where Δ is the space of instruction additions, removals, and modifications.
- Composition: π₁ ∘ π₂ = merge(π₁, π₂) must be confluent: ∀π₁,π₂,π₃, (π₁ ∘ π₂) ∘ π₃ = π₁ ∘ (π₂ ∘ π₃).
- Termination: ∀ initial bytecode B, ∀ sequence of proposals [π₁,...,π_n], the negotiation process N(B, [π₁,...,π_n]) terminates in finite steps.
- Safety preservation: ∀ B safe, ∀ π, N(B, [π]) safe.

**Literature Landscape:**
Contract negotiation in multi-agent systems (Kraus et al., 1998; Sandholm, 1999) provides game-theoretic frameworks but not bytecode-level negotiation. The π-calculus (Milner, 1999) provides formal channel-based communication but not instruction-level composition. Confluence results from term rewriting (Baader & Nipkow, 1998) are directly applicable. Session types (Honda, 1993) provide a framework for protocol-level negotiation. No existing work combines these for bytecode negotiation in safety-critical embedded systems.

**Proposed Methodology:**
1. **Month 1–2:** Define the bytecode delta algebra (Δ). Formalize instruction addition, removal, and modification as algebraic operations. Prove basic algebraic properties (associativity, commutativity for independent instructions).
2. **Month 3–4:** Define the negotiation calculus N as a term rewriting system. Prove confluence using Knuth-Bendix completion. Prove termination using a weight-based ordering (each proposal reduces the "conflict weight" of the bytecode).
3. **Month 5–6:** Define the safety preservation theorem: if B is safe (passes the validator) and π is a valid delta (passes structural checks), then N(B, [π]) is safe. Prove by induction on the negotiation sequence.
4. **Month 7–9:** Implement the negotiation service as a Jetson-side gRPC service. Integrate with the A2A wire protocol extensions (AGENT_PROPOSE, AGENT_VALIDATE). Test with 3 negotiation scenarios (resource conflict, temporal arbitration, conditional delegation).
5. **Month 10–12:** Adversarial testing: develop a negotiation adversary that attempts to produce unsafe bytecodes through negotiation. Measure the adversary's success rate. Iterate on the calculus if needed.

**Success Criteria:**
- Confluence and termination proofs accepted by peer review (formal or informal).
- Zero unsafe bytecodes produced in 10,000 adversarial negotiation trials.
- Negotiation concludes in <100ms for proposals involving ≤5 instruction modifications.
- Integration test with 3 simultaneously negotiating agents passes.

**Risk Assessment:**
- **HIGH:** LLMs may not reliably produce well-formed proposals in the delta algebra. Mitigation: the system prompt generates proposals, but a structural validator ensures well-formedness before negotiation begins.
- **MEDIUM:** The calculus may be too rigid for practical use — real negotiation may require common-sense reasoning about control semantics. Mitigation: allow "human escalation" as a fallback when negotiation fails.
- **LOW:** Performance may be insufficient for time-critical negotiation (collision avoidance). Mitigation: pre-negotiated arbitration tables for time-critical actuator conflicts.

**Connections to NEXUS Implementation:**
- Extends the A2A wire protocol with negotiation-specific message types.
- Requires the actuator write registry with priority arbitration (SP-03 from final_synthesis.md).
- Feeds into the digital constitution (Direction 10) as the operational mechanism for conflict resolution.
- Integrates with the trust system: negotiated bytecodes inherit the minimum trust of the negotiating agents.

---

### Direction 2: Optimal Trust Dynamics for Heterogeneous Agent Swarms

**Full Problem Statement:**
Define a trust graph G = (V, E, w) where V is the set of agents, E ⊆ V × V is the set of trust relationships, and w: E → [0, 1] is the trust weight function. The INCREMENTS algorithm currently operates on individual agents (|V| = 1). We require an extension that:
- Allows trust evidence to propagate through G: if agent A trusts agent B (w(A,B) = 0.9) and agent B has accumulated trust evidence E_B, then A should partially benefit from E_B.
- Prevents trust inflation: there exists no cycle C = (v₁, v₂, ..., v_n, v₁) in G such that traversing C inflates trust beyond what the individual evidence supports. Formally: ∀C, ∏_{e∈C} w(e) < 1 (cycle decay property).
- Converges: the propagated trust scores reach equilibrium in bounded time regardless of the network topology.
- Is robust to adversarial agents: a malicious agent cannot inflate its trust by creating trust cycles with colluding agents.

**Literature Landscape:**
Web-of-trust systems (PGP, Advogato) provide graph-based trust propagation but without the safety-critical constraints of NEXUS. EigenTrust (Kamvar et al., 2003) provides a principled trust propagation algorithm with convergence guarantees. However, EigenTrust assumes a single global trust score per node, while NEXUS requires per-subsystem, per-vessel trust scores. Sybil-resistant trust propagation (Yu et al., 2006) addresses the colluding agent problem but adds computational overhead. No existing work combines graph-based trust propagation with the INCREMENTS-style temporal dynamics (windowed event rates, 25:1 loss-to-gain ratio).

**Proposed Methodology:**
1. **Month 1–2:** Formalize the trust graph model. Define trust propagation rules (weighted averaging, decay with path length, cycle detection). Prove the cycle decay property.
2. **Month 3–4:** Extend the INCREMENTS algorithm to incorporate propagated trust evidence. Define the formula: T_agent = α · T_local + (1-α) · Σ_{neighbors} w(agent, neighbor) · T_neighbor. Analyze the optimal value of α (mixing parameter).
3. **Month 5–6:** Prove convergence under arbitrary network topologies using matrix analysis (the trust graph's adjacency matrix must be row-stochastic with spectral radius < 1).
4. **Month 7–9:** Implement the trust propagation algorithm in a fleet simulator. Simulate a 100-agent fleet with varying network topologies (star, mesh, hierarchical). Measure convergence time, trust score accuracy, and robustness to adversarial agents.
5. **Month 10–12:** Develop countermeasures for adversarial trust inflation (Sybil attacks, trust cycles, event manipulation). Validate against a red-team adversary.

**Success Criteria:**
- Convergence proof: trust scores reach equilibrium within O(diameter(G)) time steps for any connected graph G.
- Cycle decay: ∏_{e∈C} w(e) ≤ 0.5 for all cycles C (strong decay).
- Simulation: 100-agent fleet converges within 100 time steps with <5% trust score deviation from individual evidence.
- Adversarial robustness: a coalition of 10 colluding agents cannot inflate any agent's trust by more than 0.1.

**Risk Assessment:**
- **MEDIUM:** The mixing parameter α may be difficult to calibrate — too high and propagation is useless, too low and local evidence is overwhelmed. Mitigation: make α adaptive based on the quality and quantity of local evidence.
- **LOW:** Computational cost of trust propagation may be high for large fleets. Mitigation: hierarchical propagation (sub-fleet representatives) reduces complexity to O(n log n).

**Connections to NEXUS Implementation:**
- Extends the trust_score_algorithm_spec.md with graph-based propagation.
- Requires the fleet communication infrastructure (MQTT topics, gRPC cluster API).
- Integrates with the CRDT-based trust score synchronization mechanism.
- Informs the fleet hierarchy design (Direction 8 in research-frontiers.md, hierarchical fleet architecture).

---

### Direction 3: A2A-Native Type Inference from Bytecode Execution Traces

**Full Problem Statement:**
Given a bytecode program B executing on the NEXUS VM and a set of execution traces T = {(s_i, a_i)}_{i=1}^N where s_i ∈ ℝ^{64} is the sensor vector and a_i ∈ ℝ^{64} is the actuator vector at time step i, infer a behavioral type signature τ(B) = (S_B → A_B) where S_B ⊆ [1..64] is the set of sensor registers read, A_B ⊆ [1..64] is the set of actuator registers written, and each register has an inferred range constraint: for register r, inf_{i}(s_i[r]) ≤ s_i[r] ≤ sup_{i}(s_i[r]) for all i ∈ T.

The inferred type must satisfy: if the DECLARE_INTENT metadata declares intention τ_I, then τ(B) should be compatible with τ_I (sensor subsets should match, output ranges should be consistent with the declared goal). A type mismatch indicates a semantic bug.

**Literature Landscape:**
Behavioral typing in process calculi (Ghica & Bernardo, 2015) infers types from communication behavior. Abstract interpretation (Cousot & Cousot, 1977) provides the theoretical foundation for computing bounded ranges from program analysis. Type inference from traces is well-studied in dynamic languages (Anderson et al., 2016; Furr et al., 2009) but not for low-level bytecode in safety-critical embedded systems. The NEXUS 32-opcode ISA's simplicity (no heap, no recursion, bounded stack) makes this more tractable than general program analysis.

**Proposed Methodology:**
1. **Month 1–2:** Define the behavioral type language. Specify the type signature format, compatibility relation, and mismatch detection rules.
2. **Month 3–4:** Implement the trace collector (extract sensor/actuator pairs from VM execution logs). Implement the type inference algorithm (compute ranges, detect active registers, infer relationships).
3. **Month 5–6:** Validate on a benchmark of 200 bytecodes with known intentions. Measure: true positive rate (correctly infers type), false positive rate (flags non-existent mismatches), and coverage (fraction of edge cases detected with N traces).
4. **Month 7–9:** Integrate with the A/B testing pipeline. Run type inference on candidate bytecodes during A/B testing. If the inferred type diverges from the declared intention, flag for human review.
5. **Month 10–12:** Extend to composition analysis: infer the behavioral type of composed bytecodes (multiple reflexes running simultaneously) and check for inter-reflex conflicts.

**Success Criteria:**
- ≥95% true positive rate on 200-bytecode benchmark with N ≥ 1000 traces.
- ≤2% false positive rate.
- Detection of ≥80% of semantic bugs in a curated set of 50 intentionally buggy bytecodes.
- Integration with A/B testing pipeline adds <10% computational overhead.

**Risk Assessment:**
- **MEDIUM:** Traces may not cover all edge cases (cold-start problem). Mitigation: use interval arithmetic to complement trace-based inference — if traces cover 90% of the input space, interval analysis covers the remaining 10% analytically.
- **LOW:** The type language may be too expressive, leading to unresolvable ambiguities. Mitigation: start with a minimal type language (input/output subsets + range constraints) and extend incrementally.

**Connections to NEXUS Implementation:**
- Implements the "runtime verification" concept from Direction 9 as a software layer on the Jetson.
- Feeds into the agent type system (Problem 2) by providing empirical type signatures.
- Integrates with the AAB format — the inferred type can be stored as a TLV metadata tag.
- Supports the Griot narrative layer by providing evidence for or against the declared intention.

---

### Direction 4: Cryptographic Provenance Chains for Fleet Bytecode Distribution

**Full Problem Statement:**
Design a Merkle-tree-based provenance chain C for fleet bytecode distribution such that:
- Each bytecode version v has a hash h(v) = SHA-256(v || h(v_parent) || metadata).
- The chain is append-only: modifications create new versions, never mutate existing ones.
- Fleet-wide root hash H = Merkle_Root({h(v₁), h(v₂), ..., h(v_n)}) is updated via Raft consensus among Jetson nodes.
- Verification complexity: O(log n) per vessel, O(n) per regulatory audit.
- Storage overhead: ≤64 bytes per bytecode version on ESP32 (hash + parent pointer).

**Literature Landscape:**
Certificate transparency (Laurie et al., 2013) provides the architectural pattern for append-only logs with efficient verification. Git's content-addressable storage model is directly applicable. The WireGuard protocol's noise framework provides a model for cryptographic identity in distributed systems. Merkle trees (Merkle, 1980) are well-understood. The challenge is not cryptographic — it is integration: fitting the provenance chain into the ESP32's constrained storage and the wire protocol's payload limits.

**Proposed Methodology:**
1. **Month 1–2:** Define the provenance data structure. Specify the hash function (Ed25519 for signatures, SHA-256 for content hashing), chain format, and metadata encoding (who generated, who validated, when, trust score at deployment, A/B test results).
2. **Month 3–4:** Analyze storage requirements. Calculate total storage per bytecode version (estimated 32–64 bytes). Compare against ESP32 flash partition sizes (minimum 16KB partition for provenance chain). Design a chain pruning strategy (keep last N versions, archive older ones to Jetson).
3. **Month 5–6:** Implement the provenance chain on Jetson (Python service with SQLite backend). Integrate with the wire protocol (PROVENANCE_QUERY message type).
4. **Month 7–9:** Implement fleet-wide root hash consensus using Raft. Test with 5-Jetson topology. Measure consensus latency and bandwidth overhead.
5. **Month 10–12:** Develop the regulatory audit tool. Given a bytecode hash, extract the complete provenance chain (generation → validation → deployment → modifications) in human-readable format. Test with a simulated 6-month fleet history (10,000 bytecode versions across 50 vessels).

**Success Criteria:**
- Provenance chain supports ≥10,000 bytecode versions per vessel with ≤64KB storage on Jetson.
- Verification of any bytecode's provenance takes <10ms.
- Fleet-wide root hash consensus achieved in <5 seconds under normal network conditions.
- Regulatory audit tool produces a complete provenance report in <60 seconds for any deployed bytecode.

**Risk Assessment:**
- **LOW:** Merkle trees and append-only logs are well-understood. The main risk is integration complexity, not cryptographic novelty.
- **LOW:** ESP32 storage constraints are tight but manageable with chain pruning. The Jetson provides ample storage for the full chain.

**Connections to NEXUS Implementation:**
- Addresses the Black Box Provenance problem (Problem 24) with cryptographic guarantees.
- Required for regulatory compliance (Thread 12) — certification bodies will require provenance tracking.
- Integrates with the fleet API (cluster_api.proto) for provenance queries.
- Supports the Griot narrative layer by providing a tamper-evident record of the narrative chain.

---

### Direction 5: Self-Organizing Safety Policy Evolution

**Full Problem Statement:**
Define a safety policy mutation operator M and safety fitness function F such that:
- M: Policy × Environment → Policy' where Policy' differs from Policy by at most one rule (add, remove, or modify a single safety rule).
- F: Policy × Environment → [0, 1] where F measures the system's performance under the mutated policy in the given environment.
- The hardware safety envelope (Tier 1 kill switch, MAX6818 watchdog, output clamping) is immutable — M can only modify software safety rules (those checked by the validator, not those enforced by hardware).
- The evolutionary process is bounded: at most k = 3% of fleet vessels operate with mutated policies at any time (probe nodes).
- If F(Policy', Environment) > F(Policy, Environment) and no hardware safety event occurred on probe nodes, the mutated rule is flagged for human review.

**Literature Landscape:**
Evolutionary safety in autonomous systems is almost entirely unexplored in the literature. The closest analogues are: evolutionary robotics (Nolfi & Floreano, 2000), which evolves robot controllers but without safety constraints; safety-constrained reinforcement learning (Achiam et al., 2017), which adds safety constraints to RL but not to policy evolution; and runtime verification with adaptation (Bauer et al., 2018), which adapts monitors but not the safety policy itself. This is genuinely novel research territory.

**Proposed Methodology:**
1. **Month 1–3:** Formalize the safety policy mutation operator. Define the mutation space (what rules can be added, removed, modified). Define the invariants (hardware safety envelope must never be violated). Specify the fitness function as a weighted combination of utility (task performance) and safety (absence of hardware safety events).
2. **Month 4–6:** Implement a simulated fleet with 50 vessels. 3% (1–2 vessels) operate with mutated policies. Run 1000 evolutionary iterations (each iteration = 60 minutes of simulated operation). Measure: fitness improvement, hardware safety event rate, convergence behavior.
3. **Month 7–9:** Analyze the evolved policies. Do they represent genuine safety improvements (e.g., tighter rate limits that prevent oscillation) or trivial changes (e.g., relaxing non-critical thresholds)? Develop a "meaningful mutation" filter that rejects trivial changes.
4. **Month 10–12:** Risk analysis: simulate adversarial scenarios where the evolutionary process is manipulated (e.g., an adversary controls the fitness function or the probe node selection). Develop countermeasures.

**Success Criteria:**
- No hardware safety event occurs on any probe node across 1000 evolutionary iterations.
- At least 5% of evolved policies represent "meaningful" safety improvements (as judged by a human safety engineer).
- The evolutionary process converges (fitness improvement plateaus) within 200 iterations for well-characterized environments.
- Adversarial manipulation is detected and rejected in ≥95% of attempts.

**Risk Assessment:**
- **HIGH:** Safety policy evolution is inherently risky. Even with hardware safety invariants, software safety rule changes could enable behaviors that stress the hardware safety envelope in unexpected ways. Mitigation: the 3% probe fleet must be physically isolated from production vessels; all mutations require human approval before fleet-wide deployment.
- **HIGH:** Regulatory bodies may reject any form of safety policy evolution, even with hardware safety invariants. Mitigation: frame the evolutionary process as "safety policy optimization" rather than "safety policy evolution" — emphasize that the hardware envelope is immutable.

**Connections to NEXUS Implementation:**
- Extends the `safety_policy.json` with a mutation operator specification.
- Requires the probe node infrastructure (flagged vessels with reduced safety rules).
- Integrates with the trust system — probe node trust should not influence fleet trust.
- Addresses the Certification Paradox (Problem 1) by demonstrating that the safety policy can improve over time without compromising hardware safety.

---

### Direction 6: Quantum-Resilient Trust Score Algorithm

**Full Problem Statement:**
Analyze the INCREMENTS trust algorithm for adversarial robustness under a threat model where the adversary can:
- (A1) Suppress bad events: prevent safety events from being recorded in the event log.
- (A2) Inject false good events: insert fabricated good event records.
- (A3) Manipulate timestamps: alter the timing of events to affect window boundaries.
- (A4) Replay trust scores: force the system to accept a previously valid trust score.

For each attack vector, determine the maximum trust deviation ΔT_max achievable by the adversary, and develop countermeasures that reduce ΔT_max to <0.05 (trust level boundaries are spaced ~0.15 apart).

**Literature Landscape:**
Secure aggregation in federated learning (Bonawitz et al., 2017) addresses event injection. Byzantine fault-tolerant consensus (Castro & Liskov, 1999) addresses event suppression. Commitment schemes and hash chains (Haber & Stornetta, 1991) address timestamp manipulation. The combination of these techniques for trust score integrity in embedded systems is novel.

**Proposed Methodology:**
1. **Month 1–2:** Formalize the threat model. For each attack vector (A1–A4), define the adversary's capabilities and objectives. Compute ΔT_max for the current (unmodified) INCREMENTS algorithm.
2. **Month 3–4:** Develop countermeasure (a): cryptographic event attestation. Each event is signed by the generating ESP32 (Ed25519) and verified by the Jetson. Analyze the overhead (signature size, verification time, key management).
3. **Month 5–6:** Develop countermeasure (b): trust score commitment schemes. The trust score is periodically committed to a hash chain, preventing retroactive manipulation. Analyze the commitment frequency needed to bound ΔT_max.
4. **Month 7–9:** Develop countermeasure (c): anomaly detection on event streams. Use statistical methods (CUSUM, EWMA) to detect event injection or suppression. Measure detection latency and false positive rate.
5. **Month 10–12:** Integrate all countermeasures. Simulate a 50-vessel fleet under adversarial conditions. Measure the combined ΔT_max with all countermeasures active.

**Success Criteria:**
- ΔT_max < 0.05 for all four attack vectors with all countermeasures active.
- Event attestation adds <100 bytes per event and <1ms verification time on ESP32.
- Commitment scheme adds <5% computational overhead on Jetson.
- Anomaly detection achieves ≥95% detection rate with ≤1% false positive rate.

**Risk Assessment:**
- **MEDIUM:** The INCREMENTS algorithm's 25:1 loss-to-gain ratio already provides significant robustness against transient manipulation. The remaining vulnerability is sustained, patient adversaries — these are harder to detect but also harder to execute in practice.
- **LOW:** The countermeasures are based on well-established cryptographic techniques.

**Connections to NEXUS Implementation:**
- Extends the trust_score_algorithm_spec.md with adversarial robustness guarantees.
- Requires Ed25519 key generation and management on ESP32 (hardware support for ECC is available).
- Integrates with the provenance chain (Direction 4) for trust score commitment.
- Informs the fleet security architecture (network authentication, encrypted channels).

---

### Direction 7: Cognitive Load Management for Human Operators of A2A Fleets

**Full Problem Statement:**
Design a fleet supervision interface I that enables a single human operator to effectively supervise N vessels (N ∈ [10, 500]) each running A2A agents that generate, validate, and deploy bytecodes autonomously. The interface must:
- Present critical information (fleet trust status, anomaly alerts, deployment approvals) with minimal cognitive load.
- Filter non-critical information (individual bytecode details, routine validation reports) by default.
- Escalate to the operator only when human judgment is required (trust drops, safety cascades, regulatory events).
- Adapt information granularity based on the operator's current cognitive capacity (measured via response time and decision quality metrics).

**Literature Landscape:**
Cognitive load theory (Sweller, 1988) provides the theoretical framework. Situation awareness models (Endsley, 1995) define the three levels of awareness (perception, comprehension, projection) needed for effective supervision. Adaptive automation (Parasuraman & Riley, 1997) addresses the dynamic allocation of tasks between humans and automation. Multi-agent visualization (van der Vecht et al., 2019) provides techniques for fleet-scale displays. No existing work specifically addresses cognitive load for operators supervising A2A code-generation fleets.

**Proposed Methodology:**
1. **Month 1–2:** Conduct a task analysis: enumerate all information the operator needs, classify by urgency and cognitive load, and identify the critical subset. Use the Endsley model to define information requirements at each awareness level.
2. **Month 3–4:** Design the interface architecture. Define the dashboard layout, information hierarchy, and escalation rules. Specify the adaptive filtering algorithm (what information is shown at each cognitive load level).
3. **Month 5–7:** Implement a prototype dashboard (web-based, accessible from any device). Connect to the fleet simulation (50 simulated vessels with A2A agents).
4. **Month 8–10:** Conduct human-in-the-loop testing with 5–10 operators. Measure: situation awareness (SAGAT questionnaire), cognitive load (NASA-TLX), decision quality, and response time. Iterate on the interface design.
5. **Month 11–12:** Document the interface specification. Define cognitive load budgets for each information category. Specify the adaptive filtering rules.

**Success Criteria:**
- Operators achieve ≥80% situation awareness score on SAGAT questionnaire with 50 simulated vessels.
- Cognitive load (NASA-TLX) remains below 50/100 for fleet sizes up to 50 vessels.
- Critical anomaly detection time <10 seconds (from event to operator awareness).
- Operator approval rate for deployment decisions ≥95% agreement with post-hoc analysis.

**Risk Assessment:**
- **MEDIUM:** Cognitive load measurement is imprecise and context-dependent. Mitigation: use multiple measurement methods (NASA-TLX, response time, decision quality) and triangulate.
- **MEDIUM:** The interface may need significant iteration with human operators. Mitigation: allocate 3 months for iterative testing rather than 1.

**Connections to NEXUS Implementation:**
- Defines the human-facing component of the NEXUS fleet management system.
- Integrates with the MQTT topics (fleet status, anomaly alerts) and gRPC cluster API.
- Supports the EU AI Act "human oversight" requirement (Thread 12, Q-T12-2).
- Informs the digital constitution (Direction 10) by defining the human governance layer.

---

### Direction 8: Bytecode Genetic Algorithms with Safety-Constrained Search

**Full Problem Statement:**
Develop a genetic algorithm GA = (P, M, C, S, F) for evolving NEXUS bytecodes where:
- P is a population of bytecodes (each ≤256 instructions, ≤10,000 cycles).
- M is a mutation operator that only modifies instructions within the safety envelope (e.g., adjusts PUSH_F32 immediates to values within the actuator's safe range, modifies CLAMP_F bounds but never removes clamping).
- C is a crossover operator that preserves intention blocks (never crosses intention block boundaries).
- S is a selection operator that penalizes bytecodes that trigger safety events during A/B testing.
- F is a fitness function: F(b) = w_u · Utility(b) + w_s · Safety(b) where Utility measures task performance and Safety measures the absence of safety events.

**Literature Landscape:**
Genetic programming for control systems (Koza, 1992; Pennachin et al., 2010) has evolved PID controllers and robotic behaviors, but typically without safety constraints. Safe genetic programming (Anand et al., 2020) adds constraint handling but not for the specific case of bytecode on embedded hardware. The NEXUS context is unique: the genotype (bytecode) maps directly to a hardware-executable phenotype via the 32-opcode VM, and the fitness function includes a physical safety component measured by A/B testing on actual hardware.

**Proposed Methodology:**
1. **Month 1–2:** Define the genetic operators. Specify the mutation operator's safety envelope (which instructions can be modified, by how much). Specify the crossover operator's intention block preservation rule. Define the fitness function's weights for 3 domains (Marine, HVAC, Home).
2. **Month 3–5:** Implement the GA in Python. Use the VM benchmark ([[vm_benchmark.py]]) as the evaluation engine. Develop a simulated environment for fitness evaluation (simulated sensor inputs, simulated actuator responses).
3. **Month 6–9:** Run head-to-head comparison: GA vs. LLM synthesis on 10 benchmark control tasks (5 per domain). Measure: final fitness, convergence speed, safety event rate, novelty of solutions.
4. **Month 10–12:** Analyze results. Does the GA discover solutions that the LLM cannot? Does the LLM produce better solutions faster? Is the combination (LLM seeds the initial population, GA refines it) superior to either alone?

**Success Criteria:**
- GA-evolved bytecodes achieve ≥80% of the fitness of LLM-synthesized bytecodes on benchmark tasks.
- GA produces at least one solution that the LLM cannot (novel control strategy).
- Zero safety events during 10,000 GA evaluation cycles.
- Combined LLM+GA approach achieves ≥10% better fitness than either alone.

**Risk Assessment:**
- **MEDIUM-HIGH:** GAs are notoriously slow to converge on complex control tasks. Mitigation: the safety constraints dramatically reduce the search space, potentially improving convergence.
- **MEDIUM:** The fitness function may be poorly designed, leading to specification gaming. Mitigation: use the Griot narrative layer to provide human-interpretable explanations of evolved behaviors, enabling human evaluation of fitness.

**Connections to NEXUS Implementation:**
- Provides an alternative bytecode generation path for environments where LLM inference is unavailable (underground mining, satellite links).
- Integrates with the learning pipeline as an alternative to LLM-based reflex synthesis.
- Supports fleet-level learning (Thread 6) — evolved bytecodes can be shared across the fleet.
- Informs the evolutionary safety boundary experiment (Direction 5) by providing a concrete evolution mechanism.

---

### Direction 9: Distributed Runtime Verification of Multi-Agent Bytecode

**Full Problem Statement:**
Implement a lightweight runtime monitor M as a FreeRTOS task on the ESP32-S3 that checks four properties:
- (P1) Actuator bounds: ∀ tick t, ∀ actuator register r, min_r ≤ actuator[r] ≤ max_r (already partially implemented by output clamping, but M adds logging and alerting).
- (P2) Sensor plausibility: ∀ tick t, ∀ sensor register r, min_r ≤ sensor[r] ≤ max_r (detect stale or drifting sensors).
- (P3) Cycle budget: ∀ tick t, cycle_count(t) ≤ 10,000 (already partially implemented by the VM, but M adds violation tracking).
- (P4) Behavioral consistency: every 100 ticks, compare actual (sensor, actuator) pairs against the declared intention type (from Direction 3). If the behavioral type diverges from the declared type, flag an anomaly.

Resource budget: M must add <5% CPU overhead and <1KB RAM to the existing firmware.

**Literature Landscape:**
Runtime verification (Leucker & Schallhart, 2009) is a well-established technique in safety-critical systems. Lightweight monitors for embedded systems (Bunei et al., 2018; D'Ippolito et al., 2019) have been implemented on ARM Cortex-M platforms with <5% overhead. The NEXUS context is novel in that the monitor must check behavioral consistency (P4) against a declared intention type, not just structural properties.

**Proposed Methodology:**
1. **Month 1–2:** Define the monitor's specification. Formalize each property as a temporal logic formula (LTL or MTL). Define the violation response (log event, trigger SAFE_STATE, escalate to Jetson).
2. **Month 3–4:** Implement P1–P3 as a FreeRTOS task on ESP32-S3. Measure CPU overhead (target <2%) and RAM usage (target <256 bytes).
3. **Month 5–7:** Implement P4 (behavioral consistency). Integrate with the type inference results from Direction 3. The monitor maintains a sliding window of (sensor, actuator) pairs and periodically checks against the declared intention type.
4. **Month 8–9:** Measure the total resource overhead of M (P1–P4 combined). Optimize to meet the <5% CPU, <1KB RAM target.
5. **Month 10–12:** Develop a violation response protocol. When P4 detects a behavioral anomaly, the monitor: (a) logs the event, (b) flags the reflex for review, (c) optionally degrades to a safe fallback reflex. Test the response protocol with intentionally buggy bytecodes.

**Success Criteria:**
- P1–P3 implemented with <2% CPU and <256 bytes RAM.
- P4 implemented with <5% CPU total and <1KB RAM total.
- P4 detects ≥80% of behavioral anomalies in a curated set of 50 buggy bytecodes.
- Violation response protocol triggers within 1 tick of detection.

**Risk Assessment:**
- **LOW:** Runtime monitoring is a well-established technique. The main challenge is fitting within the ESP32's resource constraints, which is manageable given the monitor's simplicity.
- **LOW:** P4 depends on Direction 3 (type inference) for the declared intention type. If Direction 3 fails, P4 can be implemented with manually declared types.

**Connections to NEXUS Implementation:**
- Adds a fifth verification layer to the safety system (runtime verification in addition to the existing four tiers).
- Integrates with the VM firmware (reflex_bytecode_vm_spec.md) as an additional FreeRTOS task.
- Supports the certification case (Thread 12) by providing evidence of runtime safety monitoring.
- Addresses Problem 9 (adversarial bytecode) by detecting behavioral anomalies at runtime.

---

### Direction 10: The "Digital Constitution" — Formal Governance of Agent Autonomy

**Full Problem Statement:**
Develop a constitutional logic L = (R, O, P, D) where:
- R (Rules): At autonomy level L_i, action A is permitted/denied under condition C. Formally: R(L_i, A, C) → {PERMIT, DENY}.
- O (Obligations): Actions that agents MUST perform at each level. Formally: O(L_i) = {A : agent must perform A at level L_i}.
- P (Prohibitions): Actions that agents MUST NOT perform at any level. Formally: P = {A : ∀L_i, R(L_i, A, ⊤) = DENY}. Example: disable the kill switch.
- D (Delegation): What agents can delegate to other agents. Formally: D(L_i, A) → {PERMIT_DELEGATE, DENY_DELEGATE}.

The constitution must be machine-checkable (every agent action can be verified against L in real-time) and human-readable (operators can understand the governance rules without formal training).

**Literature Landscape:**
Normative multi-agent systems (Dignum et al., 2000) provide frameworks for expressing permissions, obligations, and prohibitions in multi-agent systems. Deontic logic (Hilpinen, 2001) provides the formal foundation for reasoning about norms. Constitutional AI (Bai et al., 2022; Anthropic) applies constitutional principles to LLM behavior but does not address autonomy levels or hardware safety constraints. The NEXUS context is unique in that the constitution must govern agents that control physical actuators with safety-critical consequences.

**Proposed Methodology:**
1. **Month 1–3:** Define the constitutional logic. Specify the grammar for rules, obligations, prohibitions, and delegation. Map each of the 6 autonomy levels (L0–L5) to a set of permitted, obligated, and prohibited actions.
2. **Month 4–6:** Implement the constitutional checker as a Jetson-side service. The checker intercepts every agent action (bytecode proposal, deployment request, trust modification, fleet communication) and verifies it against the constitution. Measure verification latency (target <10ms per action).
3. **Month 7–9:** Test the constitution against 20 adversarial scenarios (agents attempting actions beyond their autonomy level, agents delegating prohibited actions, agents colluding to circumvent the constitution). Measure the checker's effectiveness.
4. **Month 10–12:** Develop the human-readable constitution document. Map the formal rules to plain-language descriptions. Test readability with 5 non-expert readers. Iterate until ≥80% of rules are correctly understood on first reading.

**Success Criteria:**
- Constitutional checker verifies every agent action in <10ms.
- Zero constitutional violations in 10,000 adversarial scenario trials.
- Human readability: ≥80% of rules correctly understood by non-expert readers.
- The constitution covers all agent actions identified in the 5 coordination scenarios from [[agent_communication_and_runtime_model.md]].

**Risk Assessment:**
- **MEDIUM:** The constitution may over-constrain useful agent behavior, reducing the system's capability. Mitigation: the constitution should be conservative initially and relaxed based on operational experience. Include a "constitutional amendment" process for relaxing rules.
- **MEDIUM:** The formal logic may be too expressive, making verification expensive. Mitigation: restrict the logic to a decidable fragment (propositional deontic logic with bounded quantifiers).

**Connections to NEXUS Implementation:**
- Provides the governance layer for the entire A2A-native programming paradigm.
- Integrates with the trust system — autonomy levels are already defined; the constitution specifies what each level permits.
- Supports regulatory compliance (Thread 12) by providing a machine-checkable governance framework.
- Informs the EU AI Act "human oversight" requirement by defining exactly what agents can and cannot do at each autonomy level.

---

## 3. Research Dependency DAG

The following textual dependency graph maps all research tasks across the 15 threads and 10 frontier directions. Arrows indicate "blocks" (must complete first), "enables" (makes easier but not required), and "informs" (provides useful context).

```
╔══════════════════════════════════════════════════════════════════════╗
║                    CRITICAL PATH (longest chain)                     ║
║                                                                      ║
║  T1-Q1 (Trust Lyapunov) ──blocks──> T8-Q1 (Coordination Primitives)  ║
║       ──enables──> T6-Q1 (Fleet Sharing Protocol)                    ║
║                         ──blocks──> FD1 (Negotiation Calculus)       ║
║                                        ──informs──> FD10 (Constitution)║
║                                                  ──enables──> T12-Q1  ║
║                                                  (Lloyd's Register) ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║                 PARALLEL TRACK A: SAFETY VERIFICATION                 ║
║                                                                      ║
║  T2-Q1 (Min Opcode Set) ──enables──> T9-Q1 (Abstract Interpretation) ║
║                                              ──blocks──> T9-Q2       ║
║                                              (Hybrid Verification)   ║
║                                                      ──enables──>    ║
║  T3-Q2 (Validator Calibration) ──────────────────> FD9 (Runtime Verif)║
║  T3-Q3 (Composition Analysis) ──enables──> FD1 (Negotiation Safety)   ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║                 PARALLEL TRACK B: AGENT COMPILER                     ║
║                                                                      ║
║  T4-Q1 (Prompt Optimization) ──enables──> T7-Q1 (Specialization)     ║
║  T4-Q3 (Cultural Bias) ──informs──> T5-Q1 (Cultural Validation)      ║
║  T4-Q2 (Info Preservation) ──informs──> FD3 (Type Inference)         ║
║  T3-Q2 (Per-Rule Miss Rate) ──enables──> T4-Q1 (Targeted Improvement)║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║                 PARALLEL TRACK C: REGULATORY & GOVERNANCE              ║
║                                                                      ║
║  T11-Q1 (Responsibility Framework) ──informs──> FD10 (Constitution)  ║
║  T12-Q1 (Lloyd's Register PCCP) ──depends──> T3-Q1 (Process Model)   ║
║  T12-Q2 (EU AI Act Compliance) ──depends──> T11-Q2 (Cognitive Load)  ║
║  T7-Q3 (Healthcare Viability) ──informs──> T12-Q3 (Harmonization)    ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║                 PARALLEL TRACK D: EVOLUTION & LEARNING                 ║
║                                                                      ║
║  T6-Q1 (Fleet Sharing) ──enables──> T6-Q3 (Fleet Convergence)        ║
║  T6-Q2 (GA vs LLM) ──informs──> T14-Q1 (A/B Duration)               ║
║  T14-Q3 (Non-Stationary Detection) ──informs──> T1-Q1 (Trust Lyapunov)║
║  FD8 (Safety-Constrained GA) ──informs──> FD5 (Policy Evolution)      ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║                 PARALLEL TRACK E: INFRASTRUCTURE                      ║
║                                                                      ║
║  T13-Q1 (Min Hardware Spec) ──enables──> T9-Q1 (Abstract Interp.)    ║
║  T13-Q2 (Runtime Verif Budget) ──enables──> FD9 (Runtime Verification)║
║  T13-Q3 (HIL Timing Validation) ──enables──> T3-Q1 (Process Model)   ║
║  T15-Q1 (Doc Consistency) ──enables──> T15-Q2 (Link Maintenance)      ║
║  FD4 (Provenance Chain) ──enables──> T12-Q1 (Certification)          ║
║  FD6 (Trust Adversarial) ──enables──> FD2 (Trust Propagation)        ║
╚══════════════════════════════════════════════════════════════════════╝

NO-DEPENDENCY TASKS (can start immediately):
  • T1-Q1 (Trust Lyapunov Stability)
  • T2-Q1 (Minimum Opcode Set)
  • T5-Q2 (9th Cultural Lens)
  • T10-Q1 (Biological Mechanism Mapping)
  • T13-Q1 (Minimum Hardware Spec)
  • T15-Q1 (Doc Consistency Checker)
  • T17-Q2 (Emergent Communication Detection)
  • T14-Q1 (A/B Duration Calibration — theoretical part)
```

**Critical Path Analysis:**
The critical path runs: T1-Q1 → T8-Q1 → T6-Q1 → FD1 → FD10 → T12-Q1, with an estimated total duration of 24–30 months. This path addresses the fundamental question: "Can we govern a fleet of autonomous A2A agents safely enough for regulatory certification?" Every other task either supports this path or operates in parallel on complementary questions.

**Parallel Execution Strategy:**
The five parallel tracks (A–E) plus the no-dependency tasks can proceed simultaneously, enabling 10+ research agents to work in parallel without blocking each other. The key coordination points are: (a) T3-Q2 (validator calibration) produces data that multiple downstream tasks need, (b) T1-Q1 (trust Lyapunov) unblocks the fleet coordination track, and (c) T13-Q3 (HIL timing) unblocks the regulatory track.

---

## 4. Research Agent Assignment Guide

If we had 10 research agents and 3 months, here is the concrete assignment plan. This plan is designed so that each agent's output feeds into other agents' work, creating a knowledge accumulation cascade.

### Agent Assignments

**Agent 1: "TRUST-MATH" — Trust Dynamics Theorist**
- **Focus:** Thread 1, Question T1-Q1 (Lyapunov stability)
- **Months 1–2:** Formalize the INCREMENTS algorithm as a switched dynamical system. Prove Lyapunov stability under arbitrary switching, or construct a counterexample.
- **Month 3:** If stable: produce the proof document. If unstable: identify the pathological switching sequences and propose constraints.
- **Read first:** `trust_score_algorithm_spec.md` Section 4, `trust_deep_analysis.md` Section 3
- **Produce:** `trust_dynamics_analysis.md` with formal proof/simulation code
- **Feeds into:** Agent 3 (Fleet Coordination), Agent 8 (Trust Propagation)

**Agent 2: "BYTECODE-MIN" — Bytecode Formal Analyst**
- **Focus:** Thread 2, Questions T2-Q1 (Min opcodes) and T9-Q1 (Abstract interpretation)
- **Months 1–2:** Exhaustive opcode elimination: for each of 24 non-essential opcodes, synthesize from 8 essential opcodes. Measure program size increase.
- **Month 3:** Begin abstract interpretation implementation: interval arithmetic over the 32-opcode ISA.
- **Read first:** `reflex_bytecode_vm_spec.md`, `vm_deep_analysis.md`, `type_systems_and_formal_languages.md`
- **Produce:** `bytecode_lingua_franca_analysis.md` (Q1) + `abstract_interpretation_prototype.py` (Q9)
- **Feeds into:** Agent 4 (Safety Verifier), Agent 9 (Runtime Verification)

**Agent 3: "SWARM-COORD" — Swarm Coordination Designer**
- **Focus:** Thread 8, Questions T8-Q1 (Coordination primitives), T8-Q2 (A/B duration)
- **Months 1–2:** Enumerate all coordination scenarios. Define the minimum viable primitive set (PROPOSE, VALIDATE, VOTE, DELEGATE, ESCALATE).
- **Month 3:** Design dynamic A/B test duration calibration formula. Simulate with varying domain risk levels.
- **Read first:** `agent_communication_and_runtime_model.md`, `self_organizing_systems.md`, `multireflex_analysis.md`
- **Produce:** `swarm_coordination_analysis.md`
- **Depends on:** Agent 1 (trust stability results needed for coordination safety model)
- **Feeds into:** Agent 6 (Negotiation Calculus), Agent 10 (Digital Constitution)

**Agent 4: "SAFETY-VAL" — Safety Validation Engineer**
- **Focus:** Thread 3, Questions T3-Q2 (Validator calibration), T3-Q3 (Composition analysis)
- **Months 1–2:** Build the 5,000-bytecode adversarial benchmark. Run per-rule miss rate calibration for Claude, GPT-4o, Gemini, self-validation.
- **Month 3:** Test triangulated validation (3 validators, majority vote). Measure miss rate reduction and cost.
- **Read first:** `safety_system_spec.md`, `ai_model_analysis.md`, `program_synthesis_and_ai_codegen.md`
- **Produce:** `safety_invariant_analysis.md` with calibration tables and cost analysis
- **Feeds into:** Agent 5 (Prompt Optimizer), Agent 9 (Runtime Verification)

**Agent 5: "PROMPT-OPT" — System Prompt Optimizer**
- **Focus:** Thread 4, Questions T4-Q1 (Prompt optimization), T4-Q3 (Cultural bias)
- **Months 1–2:** Implement Bayesian optimization over system prompts using Optuna. Optimize against schema compliance × safety adherence × semantic correctness.
- **Month 3:** Cultural bias audit: generate bytecodes under 4 regulatory contexts, measure compliance gaps.
- **Read first:** `language_design_and_semantics.md`, `eight_lenses_analysis.md`, `cross_domain_a2a_applicability.md`
- **Produce:** `agent_compiler_analysis.md` with optimized prompt and bias report
- **Depends on:** Agent 4 (per-rule miss rates needed to target prompt improvements)
- **Feeds into:** Agent 7 (Cross-Domain Agent), Agent 10 (Digital Constitution)

**Agent 6: "NEGOTIATE" — Negotiation Calculus Designer**
- **Focus:** Frontier Direction 1 (Agent-Agent Bytecode Negotiation)
- **Months 1–2:** Define the bytecode delta algebra. Prove confluence and termination for the negotiation calculus.
- **Month 3:** Specify the negotiation service interface. Define 3 test scenarios (resource conflict, temporal arbitration, conditional delegation).
- **Read first:** `language_design_and_semantics.md` Section 9, `agent_communication_and_runtime_model.md`
- **Produce:** `negotiation_calculus_spec.md` with formal proofs
- **Depends on:** Agent 2 (composition safety from abstract interpretation), Agent 3 (coordination primitives)
- **Feeds into:** Agent 10 (Digital Constitution), Agent 8 (Trust Propagation)

**Agent 7: "DOMAIN-GEN" — Cross-Domain Generalization Analyst**
- **Focus:** Thread 7, Questions T7-Q1 (Specialization vs. generalization), T7-Q2 (Domain transfer)
- **Months 1–2:** Design the specialization experiment. Define quality benchmarks for all 8 domains. Specify the transfer validation protocol.
- **Month 3:** Produce the experimental design document. Note: actual fine-tuning requires compute infrastructure beyond this 3-month window — this agent produces the protocol for a future implementation phase.
- **Read first:** `cross_domain_analysis.md`, `domain_comparison_matrix.md`, `ai_model_analysis.md`
- **Produce:** `cross_domain_analysis.md` with experimental protocol
- **Depends on:** Agent 5 (optimized prompt for baseline quality measurements)
- **Feeds into:** Agent 10 (Digital Constitution), Agent 3 (Domain-specific coordination)

**Agent 8: "TRUST-GRAPH" — Fleet Trust Propagation Designer**
- **Focus:** Frontier Direction 2 (Trust Propagation) and FD6 (Trust Adversarial)
- **Months 1–2:** Define the trust graph model. Prove the cycle decay property. Design the propagation algorithm.
- **Month 3:** Analyze adversarial robustness. Identify attack surfaces. Propose countermeasures (event attestation, commitment schemes).
- **Read first:** `trust_score_algorithm_spec.md`, `trust_deep_analysis.md`, `self_organizing_systems.md`
- **Produce:** `trust_propagation_analysis.md` with formal proofs and adversarial analysis
- **Depends on:** Agent 1 (trust stability results)
- **Feeds into:** Agent 6 (Negotiation trust integration), Agent 10 (Digital Constitution)

**Agent 9: "RUNTIME-VERIFY" — Runtime Verification Engineer**
- **Focus:** Frontier Direction 9 (Runtime Verification) and Thread 13 Q13-Q2
- **Months 1–2:** Define the monitor specification (P1–P4). Implement P1–P3 (actuator bounds, sensor plausibility, cycle budget) in a firmware prototype.
- **Month 3:** Resource budget analysis: measure CPU and RAM overhead. Determine feasibility of P4 (behavioral consistency) on ESP32.
- **Read first:** `reflex_bytecode_vm_spec.md` Section 8, `memory_map_and_partitions.md`, `safety_system_spec.md`
- **Produce:** `runtime_verification_spec.md` with resource budget analysis
- **Depends on:** Agent 2 (type inference from abstract interpretation for P4)
- **Feeds into:** Agent 4 (Safety validation data), Agent 10 (Digital Constitution)

**Agent 10: "CONSTITUTION" — Digital Constitution Architect**
- **Focus:** Frontier Direction 10 (Digital Constitution) and Thread 11 Q11-Q3
- **Months 1–2:** Define the constitutional logic (rules, obligations, prohibitions, delegation). Map autonomy levels to governance rules.
- **Month 3:** Synthesize inputs from Agents 3, 5, 6, 7, 8 into a comprehensive governance framework. Produce the human-readable constitution.
- **Read first:** `final_synthesis.md` Section 6, `trust_score_algorithm_spec.md`, `ethics_analysis.md`, `autonomous_systems_law.md`
- **Produce:** `digital_constitution_draft.md` with formal logic and human-readable version
- **Depends on:** Agents 3, 5, 6, 7, 8 (constitutional rules must reflect their findings)
- **Feeds into:** Agent 1 (trust governance integration), Agent 4 (safety policy), Agent 7 (domain governance)

### Coordination Protocol

**Week 1:** All agents read their assigned documents and produce a 1-page "Prior Work Summary" following [[methodology.md]] Section 2.1. This ensures no duplication.

**Week 2:** Cross-agent dependency check. Agent 10 identifies all governance questions that depend on other agents' outputs and communicates requirements. Agent 3 identifies coordination primitive requirements from Agent 1 and Agent 2. Agent 5 identifies prompt improvement targets from Agent 4.

**Weeks 3–8:** Independent work. Agents produce their primary deliverables. Weekly status updates (1 paragraph each) posted to a shared coordination document.

**Week 9:** Integration phase. Agent 10 synthesizes all agents' outputs into the digital constitution draft. Agent 4 and Agent 5 cross-validate their calibration results. Agent 2 and Agent 9 validate the abstract interpretation implementation against the runtime verification requirements.

**Weeks 10–12:** Review and revision. All agents review each other's outputs using the Contradiction Pattern (Section 4.1 of [[methodology.md]]). Any contradictions are documented and resolved. Final deliverables are produced.

### Output Flow Diagram

```
Agent 1 ──trust_stability──> Agent 3 ──coordination──> Agent 6 ──negotiation──> Agent 10
              │                      │                                        ↑
              v                      v                                        │
Agent 8 ──propagation──> Agent 10 <──── Agent 5 ──prompt──> Agent 7 ─────────┘
                                     ↑
Agent 4 ──calibration──> Agent 5     │
      │                               │
      v                               │
Agent 9 ←──abstract_interp── Agent 2 ─┘
      │
      v
  runtime_verif_spec
```

---

## 5. Cross-Iteration Research Continuity Protocol

This section establishes the protocols for ensuring that research findings flow seamlessly from one iteration to the next, even when the agents producing the findings are different from the agents consuming them.

### 5.1 The Finding Registry

Every research finding that may be referenced by future agents must be registered in the Finding Registry. The registry is a structured document maintained at:

```
/home/z/my-project/Edge-Native/onboarding/research/finding_registry.md
```

**Finding Registry Format:**

```markdown
## F-{TOPIC}-{NUMBER}: {Title}

**Date discovered:** YYYY-MM-DD
**Discovered by:** {Agent designation, e.g., "I2-Agent-4 (SAFETY-VAL)"}
**Source document:** [[source_document.md]] Section X.Y
**Evidence level:** L1–L7 (per [[methodology.md]] Section 3.1)
**Statement:** {Precise, unambiguous claim}
**Scope:** {What the finding applies to — be specific about limitations}
**Dependencies:** {What assumptions this finding depends on}
**Contradictions:** {Any contradictions with prior findings, with C-identifier}
**Implications:** {What this finding enables or blocks}
**Status:** [Active | Superseded by F-{TOPIC}-{NUMBER} | Challenged by C-{TOPIC}-{NUMBER}]

---
```

**Registration Rules:**
1. Only findings at evidence level L2 (Rigorous Argument) or above may be registered.
3. Hypotheses (H-identifiers) may be registered at any evidence level but must be explicitly labeled as hypotheses.
4. Contradictions (C-identifiers) must be registered within 48 hours of discovery.
5. Every finding must cross-reference all related findings (by identifier).

### 5.2 The Open-Thread Tracking System

Active research threads are tracked in the Thread Tracker:

```
/home/z/my-project/Edge-Native/onboarding/research/thread_tracker.md
```

**Thread Tracker Format:**

```markdown
## Thread {N}: {Name}

**Current status:** [Active | Paused | Closed]
**Last updated:** YYYY-MM-DD
**Assigned to:** {Agent designation or "unassigned"}
**Phase:** [Exploration | Analysis | Proof/Simulation | Writing | Review]
**Progress:** {1-2 sentence summary of current state}

**Key findings this iteration:**
- F-{topic}-{number}: {finding} (evidence level)
- H-{topic}-{number}: {hypothesis} (status: confirmed/refuted/open)

**Open questions:**
- Q-{thread}-{number}: {question} (priority: HIGH/MEDIUM/LOW)

**Blocked by:** {List of dependencies}

**Next agent should:** {Specific instruction for the next agent working on this thread}
```

**Tracking Rules:**
1. Every thread must have an entry in the tracker, even if status is "Closed."
2. The tracker is updated at the end of each agent's work session (minimum weekly).
3. When a thread is paused, the "Next agent should" field provides enough context for a new agent to resume.
4. Closed threads are archived after 2 iterations of inactivity.

### 5.3 The Contradiction Resolution Process

When a new finding contradicts a registered finding:

**Step 1: Document the contradiction.**
Create a contradiction entry with C-identifier:
```markdown
## C-{TOPIC}-{NUMBER}: {Title}

**Date identified:** YYYY-MM-DD
**Identified by:** {Agent designation}
**Finding A:** F-{topic}-{number}: "{exact quote}" — [[source.md]] Section X.Y
**Finding B:** {new finding or claim}: "{exact quote}" — [[source.md]] Section W.Z
**Why they conflict:** {Explanation of the logical incompatibility}
**Evidence for A:** {Evidence level and summary}
**Evidence for B:** {Evidence level and summary}
**Proposed resolution:** [Correction | Scope Restriction | New Finding | Open for Future Research]
**Impact:** {List of affected documents, findings, and specifications}
**Confidence in resolution:** [High | Medium | Low]
**Status:** [Open | Resolved]
```

**Step 2: Notify affected agents.**
Within 24 hours, notify all agents whose work depends on the contradicted finding. Post a brief summary to the thread tracker.

**Step 3: Resolve within 2 weeks.**
Contradictions must be resolved within 2 weeks of identification. If resolution requires new evidence (simulation, proof), the timeline extends to 4 weeks. If the contradiction remains unresolved after 4 weeks, escalate to the project lead.

**Step 4: Update the Finding Registry.**
Once resolved, update the contradicted finding's status to "Superseded by F-{topic}-{number}" or "Challenged by C-{topic}-{number}." If the resolution produces a new finding, register it.

**Step 5: Preserve the original.**
Never edit the original document containing the contradicted finding. The contradiction document serves as the authoritative record.

### 5.4 The Knowledge Accumulation Pattern

Each iteration should produce a **Synthesis Document** that integrates all findings from that iteration. The synthesis follows the Synthesis Pattern from [[methodology.md]] Section 4.7.

**Synthesis Document Format:**

```markdown
# I{N} Research Synthesis

**Version:** 1.0 | **Date:** YYYY-MM-DD
**Scope:** Integration of all research findings from Iteration {N}

## New Findings ({count})
{List of all F-identifiers established in this iteration}

## Hypotheses Tested ({count})
{List of all H-identifiers tested, with confirmed/refuted/open status}

## Contradictions Resolved ({count})
{List of all C-identifiers resolved, with resolution type}

## Updated Open Questions
{List of questions that remain open, with updated priority based on new evidence}

## Revised Thread Status
{For each of the 15 threads, state: progress made, what changed, what remains}

## Implications for Next Iteration
{Specific instructions for the next generation of research agents}

## Appendix: Full Finding Registry Update
{Complete listing of all registered findings with status changes}
```

**Accumulation Pattern:**

```
I1: context-map.md + research-frontiers.md + methodology.md
     ↓ (produces 15 threads, 29 problems, 10 directions)
I2: expansion-guide.md + finding_registry.md + thread_tracker.md
     ↓ (produces deep-dives, briefs, DAG, assignments, protocols)
I3: [Synthesis of I2 findings] + updated finding_registry.md + updated thread_tracker.md
     ↓ (resolves contradictions, advances threads, identifies new questions)
I4: [Synthesis of I3 findings] + ...
     ...
```

Each iteration's synthesis document replaces the previous iteration's context map as the primary entry point for new agents. The finding registry grows monotonically — findings are never deleted, only superseded. The thread tracker provides the current state of every active thread at a glance.

### 5.5 Agent Onboarding Checklist for Each Iteration

Every research agent beginning work on a new iteration must complete the following checklist before producing any deliverable:

1. **Read the synthesis document** from the previous iteration (highest priority).
2. **Read the finding registry** — understand all active findings and their evidence levels.
3. **Read the thread tracker** — identify your assigned thread's current state and open questions.
4. **Read your assigned thread's deep-dive** from the most recent expansion guide.
5. **Read all source documents** referenced in the thread's "Contributing documents" list.
6. **Produce a Prior Work Summary** (per [[methodology.md]] Section 2.1).
7. **Check for contradictions** between the prior work and any new evidence you have.
8. **Begin work** only after steps 1–7 are complete.

This protocol ensures that every iteration builds on the last, that contradictions are caught and resolved systematically, and that no research is duplicated or lost.

---

## Appendix: Quick Reference — Research Task Summary

| Task ID | Thread | Question | Difficulty | Time | Dependencies |
|---------|--------|----------|------------|------|-------------|
| T1-Q1 | Trust | Lyapunov stability | MEDIUM | 3–4 mo | None |
| T1-Q2 | Trust | Utility metric | HIGH | 6–9 mo | T4 |
| T1-Q3 | Trust | Trust propagation | MED-HIGH | 4–6 mo | T8 |
| T2-Q1 | Bytecode | Min opcode set | LOW-MED | 2–3 mo | None |
| T2-Q2 | Bytecode | AAB storage budget | MEDIUM | 3–4 mo | FD4 |
| T2-Q3 | Bytecode | Intention expressiveness | MEDIUM | 4–5 mo | FD1 |
| T3-Q1 | Safety | PCCP for SIL 1 | HIGH | 12–18 mo | T12, T2, T9 |
| T3-Q2 | Safety | Validator calibration | MEDIUM | 3–4 mo | T4 |
| T3-Q3 | Safety | Composition analysis | HIGH | 6–9 mo | T2 |
| T4-Q1 | Compiler | Prompt optimization | MEDIUM | 3–4 mo | T3 |
| T4-Q2 | Compiler | Info preservation | MEDIUM | 3–4 mo | None |
| T4-Q3 | Compiler | Cultural bias | MEDIUM | 4–5 mo | T5 |
| T5-Q1 | Culture | Spec validation | MED-HIGH | 6–9 mo | T1 |
| T5-Q2 | Culture | 9th lens | MEDIUM | 3–4 mo | None |
| T5-Q3 | Culture | Algorithmic trust params | HIGH | 6–9 mo | T7 |
| T6-Q1 | Evolution | Fleet sharing protocol | MED-HIGH | 6–9 mo | T8 |
| T6-Q2 | Evolution | GA vs LLM | MEDIUM | 4–6 mo | T2 |
| T6-Q3 | Evolution | Fleet convergence | MEDIUM | 3–4 mo | T1 |
| T7-Q1 | Domain | Specialization experiment | MEDIUM | 4–6 mo | T4 |
| T7-Q2 | Domain | Domain transfer | MEDIUM | 3–4 mo | T3 |
| T7-Q3 | Domain | Healthcare viability | LOW-MED | 2–3 mo | T12 |
| T8-Q1 | Swarm | Coordination primitives | HIGH | 6–9 mo | T2 |
| T8-Q2 | Swarm | Dynamic A/B duration | MEDIUM | 3–4 mo | T3 |
| T8-Q3 | Swarm | Emergent communication | MEDIUM | 4–5 mo | T6 |
| T9-Q1 | Verification | Abstract interpretation | MED-HIGH | 4–6 mo | T2 |
| T9-Q2 | Verification | Hybrid verification | HIGH | 6–9 mo | T9-Q1 |
| T9-Q3 | Verification | Proof-carrying bytecode | HIGH | 6–9 mo | T3 |
| T10-Q1 | Bio metaphor | Biological mechanisms | MEDIUM | 3–4 mo | None |
| T10-Q2 | Bio metaphor | Griot encoding | MEDIUM | 3–4 mo | T6 |
| T10-Q3 | Bio metaphor | Optimization principle | LOW-MED | 2–3 mo | T13 |
| T11-Q1 | Post-coding | Responsibility framework | HIGH | 6–9 mo | T12 |
| T11-Q2 | Post-coding | Cognitive load | MED-HIGH | 4–6 mo | T8 |
| T11-Q3 | Post-coding | Digital constitution | MED-HIGH | 6–9 mo | FD10 |
| T12-Q1 | Regulatory | Lloyd's Register | HIGH | 12–18 mo | T3 |
| T12-Q2 | Regulatory | EU AI Act | MED-HIGH | 6–9 mo | T11 |
| T12-Q3 | Regulatory | Harmonization | MEDIUM | 4–6 mo | T7 |
| T13-Q1 | HW/SW | Min hardware spec | MEDIUM | 3–4 mo | None |
| T13-Q2 | HW/SW | Runtime verif budget | MEDIUM | 3–4 mo | T9 |
| T13-Q3 | HW/SW | HIL timing | MEDIUM | 4–5 mo | T3 |
| T14-Q1 | Learning | Dynamic A/B duration | MEDIUM | 3–4 mo | T3 |
| T14-Q2 | Learning | Online learning | MEDIUM | 3–4 mo | T13 |
| T14-Q3 | Learning | Non-stationary detection | MEDIUM | 3–4 mo | T7 |
| T15-Q1 | Documentation | Consistency checker | MEDIUM | 2–3 mo | None |
| T15-Q2 | Documentation | Link maintenance | LOW-MED | 1–2 mo | T15-Q1 |
| T15-Q3 | Documentation | Genesis index | MEDIUM | 3–4 mo | None |
| FD1 | Frontier | Negotiation calculus | HIGH | 18–24 mo | T2, T9, T8 |
| FD2 | Frontier | Trust propagation | MED-HIGH | 12–18 mo | T1, T6, T8 |
| FD3 | Frontier | Type inference | MEDIUM | 9–12 mo | T2, T9 |
| FD4 | Frontier | Provenance chains | MEDIUM | 9–12 mo | T24, T1 |
| FD5 | Frontier | Safety policy evolution | HIGH | 18–24 mo | T1, T9, T22 |
| FD6 | Frontier | Trust adversarial | MED-HIGH | 12–18 mo | T1, T9 |
| FD7 | Frontier | Cognitive load | MEDIUM | 9–12 mo | T25, T28 |
| FD8 | Frontier | Safety-constrained GA | MED-HIGH | 12–18 mo | T9, T22 |
| FD9 | Frontier | Runtime verification | MEDIUM | 6–9 mo | T9, T11, FD3 |
| FD10 | Frontier | Digital constitution | MED-HIGH | 12–18 mo | T1, T22, T23, T25 |

---

*This expansion guide is a living document. It should be updated at the end of each iteration based on the findings produced. The next research agent to encounter this document should treat it as the starting point for their work, not as gospel — challenge assumptions, extend findings, and push the boundaries.*
