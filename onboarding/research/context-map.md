# NEXUS Research Context Map

**Version:** 1.0 | **Date:** 2025-07-14 | **Classification:** Research Onboarding — Agent Reference
**Audience:** AI research agents continuing work on the NEXUS project
**Purpose:** Provide a complete intellectual map of the NEXUS project so that any agent, encountering this codebase for the first time, can immediately orient itself, understand what has been done, and identify what remains.

---

## Table of Contents

1. [Project Genome](#1-project-genome)
2. [Document Atlas](#2-document-atlas)
3. [Research Topology](#3-research-topology)
4. [Concept Dependency Graph](#4-concept-dependency-graph)
5. [Where We Left Off](#5-where-we-left-off)

---

## 1. Project Genome

### 1.1 The Central Idea

NEXUS is a distributed intelligence platform for industrial robotics where LLM agents — not humans — are the primary authors, interpreters, and validators of control code. The system executes on a bytecode virtual machine running on embedded hardware (ESP32-S3) with AI cognition provided by edge GPUs (Jetson Orin Nano), governed by a mathematical trust algorithm that requires 27 days of safe operation before any subsystem earns full autonomy. The founding metaphor is **"The Ribosome, Not the Brain"** — intelligence is distributed to the periphery rather than centralized. Each limb runs a bytecode VM that executes reflex programs at 1ms ticks, like a biological ribosome translating mRNA into proteins without comprehension.

### 1.2 The Three Architecture Tiers

The system is organized into three independent tiers, each capable of operating when higher tiers fail:

- **Tier 1 (Reflex Layer):** ESP32-S3 microcontrollers (Xtensa LX7, 240MHz, 512KB SRAM, $6-10/unit). Runs the 32-opcode stack VM at 1kHz ticks. Handles sensor I/O, actuator control, and safety enforcement. Operates independently — maintains safe control even when all higher tiers are unreachable.
- **Tier 2 (Cognitive Layer):** NVIDIA Jetson Orin Nano (40 TOPS, 8GB LPDDR5, 8-15W, $249/unit). Runs LLM inference (Qwen2.5-Coder-7B at Q4_K_M quantization, 4.2GB VRAM, 17.2 tok/s), pattern discovery, reflex synthesis, A/B testing, MQTT bridge to cloud, and wire protocol to ESP32s.
- **Tier 3 (Cloud Layer):** Starlink / 5G connectivity. Heavy training, large-model simulation, fleet management, historical analytics. Latency: seconds to hours. Cloud is **advisory only** — it cannot command actuators directly.

**Design principle:** Each tier operates independently. Tier 1 maintains safe control even when Tiers 2 and 3 are completely unreachable. This is not a fallback — it is the primary design constraint.

### 1.3 The 32-Opcodes Virtual Machine

A stack machine with 8-byte fixed-width instructions, 256-entry float32 stack, deterministic execution, zero heap allocation. Organized into six categories:

| Category | Opcodes | Key Properties |
|----------|---------|---------------|
| Stack (0x00-0x07) | NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT | Stack manipulation, 1-2 cycles each |
| Arithmetic (0x08-0x10) | ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F | Float32 only, DIV by zero returns 0.0f (no NaN trap) |
| Comparison (0x11-0x15) | EQ_F, LT_F, GT_F, LTE_F, GTE_F | Returns 1.0 or 0.0 |
| Logic (0x16-0x19) | AND_B, OR_B, XOR_B, NOT_B | Bitwise operations on integer representation |
| I/O (0x1A-0x1C) | READ_PIN, WRITE_PIN, READ_TIMER_MS | 64 sensor registers, 64 actuator registers |
| Control (0x1D-0x1F) | JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE | CALL/RET implemented via JUMP flag bit |

Plus syscalls via NOP+flags: HALT, PID_COMPUTE (8 hardware PID controllers), RECORD_SNAPSHOT (128-byte state snapshots), EMIT_EVENT (32-event ring buffer).

**Critical invariants proven:**
- Turing-complete: {ADD_F, SUB_F, MUL_F, DIV_F, PUSH_F32, CLAMP_F, JUMP_IF_TRUE, WRITE_PIN} is functionally complete for all continuous piecewise-polynomial functions (Stone-Weierstrass).
- Type-safe: No NaN or Infinity reaches actuator outputs (Theorem 3).
- Execution budget: Max 10,000 cycles per tick; measured worst case 368 cycles (3.7%).
- Memory budget: 5,280 bytes total VM runtime.

### 1.4 The Wire Protocol (Jetson ↔ ESP32)

RS-422 full-duplex serial at 921,600 baud, COBS framing (0.4% worst-case overhead), CRC-16/CCITT-FALSE integrity checking. 28 message types covering the full lifecycle: DEVICE_IDENTITY, ROLE_ASSIGN, HEARTBEAT, TELEMETRY, COMMAND, REFLEX_DEPLOY, OBS_RECORD_START/STOP/DUMP, FIRMWARE_UPDATE (3-phase OTA), SAFETY_EVENT, ERROR, and more. 75 error codes defined. The protocol is the transport layer for all A2A communication between cognitive and reflex layers.

### 1.5 Four-Tier Safety System (Non-Negotiable)

Defense-in-depth with four independent layers, each capable of detecting and responding to failures:

1. **Hardware Tier:** Mechanical MOSFET kill switch (0.93ms response), pull-down resistors on all actuators, current sensing (INA219), MAX6818 watchdog timer.
2. **Firmware Tier:** ISR guard (interrupt-level safety check), hardware watchdog (MAX6818, 0x55/0xAA pattern every 200ms), software watchdog (FreeRTOS task monitoring).
3. **Supervisory Tier:** FreeRTOS task at priority 24 monitoring heartbeat, task health, safety state machine (NORMAL → DEGRADED → SAFE_STATE → FAULT).
4. **Application Tier:** Trust-score-gated autonomy (L0-L5), per-reflex safety validation, kill-switch availability check.

Monte Carlo simulation (1000 iterations) shows SIL 1 compliance (PFH < 10⁻⁷/h), 97.06% system availability, ~96% diagnostic coverage.

### 1.6 INCREMENTS Trust Algorithm

A mathematical trust system with 12 parameters, 6 autonomy levels (L0 Manual → L1 Advisory → L2 Assisted → L3 Supervised → L4 Autonomous → L5 Full), and a 25:1 loss-to-gain ratio. Core parameters: `alpha_gain` (0.002 per good window), `alpha_loss` (0.05 per bad window), `t_floor` (0.10), `t_max` (0.99), `window_seconds` (3600). Trust gain time constant τ_g ≈ 658 windows (27.4 days); loss time constant τ_l ≈ 29 windows (1.2 days). Takes 45 days ideal to reach L4; 83 days to reach L5. Per-subsystem independence: steering trust is independent of engine trust. Five independent trust scores per vessel.

The trust score measures **safety** (absence of bad events). It does not measure **utility** (whether the system does useful things). This is the Alignment-Utility Gap (Open Problem 22).

### 1.7 The A2A-Native Programming Paradigm

This is the project's frontier research contribution. The existing system has humans in the loop at multiple points. The A2A-native paradigm removes humans from the code path entirely, making agents first-class authors and interpreters of control code. It is founded on **Three Pillars:**

**Pillar 1 — System Prompt as Compiler:** An LLM's system prompt becomes the compilation pipeline. It translates natural-language intentions into bytecode, enforces safety constraints, optimizes for the target hardware. The system prompt defines input grammar (natural language), output grammar (JSON reflex schema), semantic constraints (safety rules), and compilation guarantees (semantic preservation, determinism, type safety).

**Pillar 2 — Equipment as Runtime:** The execution environment between bytecode and metal. The VM, the OS (FreeRTOS), the drivers, the sensor I/O system. Defined by the ROLE_ASSIGN configuration that maps abstract sensor/actuator names to physical hardware. The runtime contract guarantees sensor register population, actuator register draining, timing budgets, safety clamping, reliable delivery, and failure responses.

**Pillar 3 — Vessel as Hardware:** The physical platform. Its capabilities define what bytecode can accomplish. The vessel capability descriptor tells agents what they have to work with. Hardware ranges from $500 (home controller) to $65,800+ (mining haul truck).

### 1.8 Agent-Annotated Bytecode (AAB) Format

Extended bytecode format: 8-byte core instruction + variable-length TLV (Type-Length-Value) metadata trailer. The core instruction is what the ESP32 VM executes. The TLV trailer is what agents read — it carries provenance, intention, capability requirements, safety constraints, trust implications, and failure narratives. Agents read the metadata; ESP32 receives only the stripped 8-byte core. Zero execution overhead on the target hardware.

### 1.9 The 29 Proposed New Opcodes

All new opcodes are in the range 0x20+ and are NOP on the existing ESP32 VM (zero firmware changes for backward compatibility):

- **Intent Opcodes (0x20-0x26):** DECLARE_INTENT, ASSERT_GOAL, VERIFY_OUTCOME, EXPLAIN_FAILURE — encode *what* the bytecode is trying to achieve and *why*.
- **Agent Communication Opcodes (0x30-0x34):** TELL, ASK, DELEGATE, REPORT_STATUS, REQUEST_OVERRIDE — inter-agent coordination.
- **Capability Negotiation Opcodes (0x40-0x44):** REQUIRE_CAPABILITY, DECLARE_SENSOR_NEED, DECLARE_ACTUATOR_USE — resource negotiation.
- **Safety Augmentation Opcodes (0x50-0x56):** TRUST_CHECK, AUTONOMY_LEVEL_ASSERT, SAFE_BOUNDARY, RATE_LIMIT — runtime safety gates.

### 1.10 The 0.5× Trust Rule

Agent-generated bytecode earns trust at HALF the rate of human-authored code. This compensates for the reduced human intuition about what the code "actually does." The trust score formula's `alpha_gain` is multiplied by 0.5 when `origin == AGENT_GENERATED`. This is the single most important A2A-specific safety mechanism.

### 1.11 The Swarm Architecture

NEXUS operates as a swarm of intelligent nodes. Within a vessel, multiple ESP32 nodes execute different bytecodes (navigation, engine, payload) while agents on the Jetson coordinate via gRPC and shared memory. Across vessels in a fleet, agents communicate via the TELL, ASK, and DELEGATE opcodes. Trust scores propagate: individual node → subsystem → vessel → fleet. The AAB format ensures that any agent can read, verify, and modify bytecode targeted at any node.

### 1.12 The Learning Pipeline

Five-stage pipeline: Observe → Record → Discover Patterns → Synthesize Reflex → A/B Test → Deploy. Five pattern discovery algorithms: cross-correlation (causal relationships), BOCPD (change point detection), HDBSCAN (state clustering), temporal mining (recurring patterns), Bayesian reward inference (learning from demonstrations). The A/B test constitutes 99.96% of deployment latency (60 minutes), providing a natural throttle on agent-generated proposals.

### 1.13 Cross-Domain Architecture

Eight target domains: Marine (reference), Agriculture, Factory Automation, Mining, HVAC, Home Automation, Healthcare Robotics, Autonomous Ground Vehicles. ~80% of the architecture is domain-agnostic. ~20% is domain-specific. The trust α_gain/α_loss ratio varies 150× across domains (1.3:1 for Home to 200:1 for Healthcare), encoding the entire domain risk profile in a single number.

### 1.14 Cross-Cultural Philosophical Foundation

NEXUS's design was analyzed through 8 cultural lenses (Western Analytic, Daoist, Confucian, Soviet Engineering, African Ubuntu, Indigenous, Japanese, Islamic Golden Age). Five universal themes emerged with 7-8/8 consensus: (1) Intelligence is relational, not atomic; (2) Purpose must be earned, not declared; (3) Constraints enable rather than restrict; (4) Knowledge must include narrative context; (5) Balance requires oscillation, not static equilibrium.

### 1.15 Concept Relationship Map (Textual Dependency Graph)

The following shows which core concepts depend on which others:

```
Three Architecture Tiers
├── Tier 1: Reflex Layer
│   ├── 32-Opcodes VM ← depends on: Float32 arithmetic, Stack machine design
│   │   └── Agent-Annotated Bytecode (AAB) ← extends: 32-Opcodes VM with TLV metadata
│   │       └── 29 New Opcodes ← extends: AAB format, requires: NOP backward compat
│   │           └── Intention Blocks ← composed from: Intent opcodes, Safety opcodes, Capability opcodes
│   ├── Wire Protocol ← connects: Tier 1 to Tier 2, depends on: COBS framing, CRC-16
│   │   └── 12 Wire Protocol Extensions (A2A) ← extends: Wire Protocol for agent communication
│   └── Four-Tier Safety ← wraps: all Tier 1 execution, depends on: Hardware interlock, FreeRTOS
│
├── Tier 2: Cognitive Layer
│   ├── Learning Pipeline ← depends on: Tier 2 compute, produces: reflex bytecodes
│   │   └── 5 Pattern Discovery Algorithms ← feed: Reflex Synthesis
│   ├── System Prompt as Compiler ← translates: Natural Language → JSON Reflex
│   │   └── JSON Reflex → Bytecode Compiler ← depends on: VM ISA spec, proven: semantics-preserving
│   ├── Agent Cross-Validation ← depends on: Separate LLM models, produces: safety assurance
│   └── Agent Communication Protocol ← uses: AAB format, wire protocol extensions
│
├── Tier 3: Cloud Layer ← advisory only, depends on: Tier 2 MQTT bridge
│
├── INCREMENTS Trust Algorithm ← gates: all reflex deployment
│   ├── depends on: Four-Tier Safety (safety events feed trust)
│   ├── 0.5× Trust Rule ← modifies: Trust gain rate for agent-generated code
│   └── Per-Subsystem Independence ← prevents: cascading failures
│
├── A2A-Native Paradigm ← composed from: Three Pillars, AAB, New Opcodes, Trust Rule
│   ├── Pillar 1: System Prompt as Compiler
│   ├── Pillar 2: Equipment as Runtime
│   ├── Pillar 3: Vessel as Hardware
│   └── Swarm Architecture ← emerges from: A2A paradigm at fleet scale
│
├── Cross-Domain Architecture ← parameterizes: Trust, Safety Rules, Protocols per domain
│   └── 80% Universal / 20% Domain-Specific ← validated by: Round 2 analysis
│
└── Cross-Cultural Philosophy ← validates: universal design principles
    └── 5 Universal Themes ← confirmed by: 8 cultural lenses (7-8/8 consensus)
```

---

## 2. Document Atlas

A complete map of every document in the repository, organized by purpose. Each entry includes file path, approximate word count, key contribution, relationship to other documents, and what a research agent gains from reading it.

### 2.1 Top-Level Navigation Documents

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `claude.md` | ~9,000 | **Master project context.** The single most important document. One-sentence summary, architecture, opcodes, wire protocol, safety, trust, A2A paradigm, knowledge base map, repository structure, design decisions, build estimates, open problems. | FIRST. Always. |
| `README.md` | ~3,000 | Project overview, key specs, repository structure, compliance targets, key numbers (21 spec files, ~19,200 lines, 28 ADRs). | Second. Quick orientation. |

### 2.2 Production Specifications (`specs/`)

These are engineering specifications — the "source of truth" for building the actual system. ~19,200 lines total across 21 files.

| File | Lines | Words | Key Contribution | Read When |
|------|------:|------:|-----------------|-----------|
| `specs/00_MASTER_INDEX.md` | 138 | ~1,800 | Master index of all specs with line counts, confidence heat map, build complexity estimates, critical path. | Starting any engineering work |
| `specs/firmware/reflex_bytecode_vm_spec.md` | 2,487 | ~16,000 | **Complete VM specification.** All 32 opcodes, 8-byte encoding, memory model, safety invariants, timing analysis, portability. The ISA definition. | Understanding execution layer |
| `specs/firmware/io_driver_interface.h` | 829 | ~4,500 | C header defining the driver vtable, pin config types, error codes, safety callbacks. THE interface contract between firmware and hardware. | Implementing I/O |
| `specs/firmware/io_driver_registry.json` | 2,408 | ~8,000 | 9+ I2C drivers with exact register sequences, selftest procedures, data schemas. | Driver implementation |
| `specs/firmware/memory_map_and_partitions.md` | 685 | ~4,000 | SRAM/PSRAM byte-addressed maps, flash partition table, RTOS task config, DMA allocation. | Memory-constrained design |
| `specs/protocol/wire_protocol_spec.md` | 1,047 | ~7,000 | COBS framing, 10-byte header, 28 message types, 75 error codes, reliability mechanisms. | Inter-tier communication |
| `specs/protocol/message_payloads.json` | 2,156 | ~7,000 | JSON Schema for all 23 JSON message payloads. | Protocol implementation |
| `specs/safety/safety_system_spec.md` | 1,296 | ~8,500 | Four-tier architecture, kill switch spec, watchdog spec, heartbeat, overcurrent protection, boot timing, certification checklist. | Safety engineering |
| `specs/safety/trust_score_algorithm_spec.md` | 2,414 | ~16,000 | **Complete trust algorithm.** Mathematical formula, 12 parameters, 15 event severities, 5 simulation scenarios, C and Python implementations. | Trust system work |
| `specs/safety/safety_policy.json` | 864 | ~3,500 | 10 global safety rules, 7 actuator profiles, 5 domain-specific rule sets, 6-stage validation pipeline. | Safety rule configuration |
| `specs/jetson/learning_pipeline_spec.md` | 2,140 | ~14,000 | 5 pattern discovery algorithms, narration processing, A/B testing framework, reflex synthesis, 7 standardized metrics. | Cognitive layer implementation |
| `specs/jetson/cluster_api.proto` | 934 | ~4,000 | 6 gRPC services, 80+ message types — complete cluster API. | Fleet management |
| `specs/jetson/mqtt_topics.json` | 668 | ~2,500 | 13 MQTT topics with QoS/retain, payload schemas, publisher/subscriber assignments. | Cloud bridge |
| `specs/jetson/module_interface.py` | 1,153 | ~5,000 | Python ABC for all Jetson modules with lifecycle, hot-reload, resource budgets. | Jetson software architecture |
| `specs/ports/hardware_compatibility_matrix.json` | 2,128 | ~7,000 | 13 MCU evaluations, porting effort, peripheral requirements, RTOS requirements. | Porting to new hardware |
| `specs/ARCHITECTURE_DECISION_RECORDS.md` | ~800 | ~3,200 | 28 ADRs with confidence levels, alternatives, and "what would change my mind" triggers. | Understanding design rationale |
| `specs/SENIOR_ENGINEER_BUILD_GUIDE.md` | ~700 | ~1,800 | Reading order, 9 build steps, test strategy, key metrics, development priorities, risk matrix. | Starting implementation |

### 2.3 Knowledge Base (`knowledge-base/`)

Wikipedia-grade encyclopedia. 27 articles, ~323,000 words total. Organized into 6 categories.

#### Foundations (5 articles, ~51,600 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `foundations/history_of_programming_languages.md` | 9,550 | 8 eras from 1940s to post-coding, why stack machines matter, what makes NEXUS different. | Understanding historical context |
| `foundations/evolution_of_virtual_machines.md` | 10,052 | P-code, JVM, Lua, WASM, eBPF, and the new category: agent-interpretable VMs. | Understanding VM design space |
| `foundations/biological_computation_and_evolution.md` | 9,853 | DNA as code, neural computation, ribosome thesis, swarm intelligence. The biological metaphor. | Understanding the ribosome analogy |
| `foundations/cross_cultural_computing.md` | 10,643 | 7 civilizations, 8 cultural computing traditions. Non-Western contributions to CS. | Cross-cultural analysis work |
| `foundations/programming_paradigms.md` | 11,502 | 14 paradigms × 15 dimensions. NEXUS is concatenative + intentional. | Understanding NEXUS's paradigm position |

#### Theory (6 articles, ~78,200 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `theory/agent_communication_languages.md` | 12,053 | KQML, FIPA-ACL, speech acts, emergent communication. Foundation for A2A protocol design. | Agent communication research |
| `theory/evolutionary_computation.md` | 13,372 | GA/GP/ES/DE. NEXUS bytecode as genotype, fleet as population. Evolutionary code. | Evolutionary code system design |
| `theory/formal_verification_and_safety.md` | 14,576 | 8 safety standards, model checking, proof-carrying code, the certification paradox. | Safety certification work |
| `theory/program_synthesis_and_ai_codegen.md` | 12,064 | 50-year history, LLM code gen, constrained generation. Foundation for system-prompt-as-compiler. | Code generation pipeline |
| `theory/self_organizing_systems.md` | 14,210 | CAS, swarm intelligence, emergence, autopoiesis, free energy principle. Swarm architecture theory. | Multi-agent coordination |
| `theory/type_systems_and_formal_languages.md` | 11,899 | Chomsky hierarchy, 10 type systems, bytecode verification, Curry-Howard. Agent type system design. | Type safety research |

#### Philosophy (3 articles, ~35,700 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `philosophy/philosophy_of_ai_and_consciousness.md` | 11,492 | Hard problem, Chinese Room, functionalism, alignment, AGI, phenomenology. | Philosophical grounding |
| `philosophy/trust_psychology_and_automation.md` | 14,234 | Lee & See, trust calibration, cultural differences, computational trust models. INCREMENTS mapping. | Trust system design |
| `philosophy/post_coding_paradigms.md` | 9,941 | L0-L5 coding autonomy, specification over implementation, role of humans. The post-coding age. | Understanding the paradigm shift |

#### Systems (5 articles, ~68,300 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `systems/embedded_and_realtime_systems.md` | 13,381 | ESP32-S3/Jetson deep dives, FreeRTOS, memory-constrained computing. | Hardware implementation |
| `systems/distributed_systems.md` | 11,333 | CAP theorem, consensus protocols, fleet architecture, scalability. | Fleet coordination |
| `systems/robotics_control_history.md` | 11,374 | PID to MPC, Brooks subsumption, ROS vs NEXUS. | Control theory context |
| `systems/edge_ai_encyclopedia.md` | 14,414 | 18-chip comparison, quantization, NEXUS AI stack, neuromorphic computing. | AI hardware selection |
| `systems/hardware_software_codesign.md` | 15,763 | Co-design philosophy, BOM ($684), power/thermal, safety hardware. | Bill of materials, hardware design |

#### Domains (2 articles, ~22,900 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `domains/marine_autonomous_systems.md` | 8,717 | Vessel types, COLREGs, sensor suites, MASS levels. The reference domain. | Marine implementation |
| `domains/maritime_navigation_history.md` | 14,214 | Polynesians to GPS, longitude problem, failure modes. | Domain expertise |

#### Reference (5 articles, ~67,500 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `reference/nexus_glossary.md` | ~14,200 | **310 terms** across 10 categories with NEXUS context. | Looking up any term |
| `reference/agent_frameworks_comparison.md` | 12,731 | 15 frameworks × 20 dimensions. NEXUS vs all. | Competitive analysis |
| `reference/autonomous_systems_law.md` | 18,965 | UNCLOS, EU AI Act, GDPR, liability, certification. | Regulatory compliance |
| `reference/open_problems_catalog.md` | 9,606 | **29 unsolved problems** across 6 categories with success criteria. | Finding research topics |
| `reference/annotated_bibliography.md` | ~10,000 | 178 references across 15 domains. | Finding source material |

#### Developer Guide (1 article)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `developer-guide/onboarding_guide.md` | 9,906 | 12-section onboarding, repository tour, 20 essential documents. | First day as developer |

### 2.4 A2A-Native Language Research (`a2a-native-language/`)

Six research documents, ~45,200 words total. The intellectual foundation for the A2A-native paradigm.

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `language_design_and_semantics.md` | 10,221 | **AAB format specification, 29 new opcodes, intention blocks, formal proofs.** The language design core. | Understanding A2A language |
| `assembly_mapping_and_hardware_bridge.md` | 8,853 | Xtensa LX7 & ARM64 assembly mapping, instruction timing, "unfiltered transfer" pipeline, hot-loading. | Hardware execution |
| `nexus_integration_analysis.md` | 6,175 | Backward compatibility with 32-opcode VM, 12 wire protocol extensions, 32-week migration path. | Integration planning |
| `agent_communication_and_runtime_model.md` | 7,057 | Agent protocol, equipment runtime model, vessel capability descriptor, 5 scenarios. | Agent coordination design |
| `cross_domain_a2a_applicability.md` | 6,771 | Per-domain A2A analysis, regulatory implications, 0.5× trust rule formalization. | Cross-domain deployment |
| `final_synthesis.md` | 6,114 | **Grand thesis, Three Pillars formalized, 20 open questions, 36-month roadmap.** The capstone. | Understanding the whole A2A argument |

### 2.5 A2A-Native Specifications (`a2a-native-specs/`)

The "Rosetta Stone" — agent-native twins of every core specification. ~49,100 words across 8 files.

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `README.md` | 1,504 | Explains the Rosetta Stone concept, two-lens architecture, compiler-interpreter hybrid. | Understanding A2A specs |
| `rosetta_stone.md` | 6,045 | Detailed mapping between human specs and A2A-native specs. | Side-by-side comparison |
| `bytecode_vm_a2a_native.md` | 9,261 | Complete A2A-native VM spec: agent-interpreted opcode semantics, AAB TLV tag registry, intention blocks, agent validation pipeline. | Agent VM implementation |
| `wire_protocol_a2a_native.md` | 7,811 | Agent-native wire protocol: message semantics for agents, A2A extension messages. | Agent communication protocol |
| `safety_system_a2a_native.md` | 7,521 | Agent-native safety: safety invariants as provable properties, agent-visible safety state. | Agent safety verification |
| `trust_system_a2a_native.md` | 5,903 | Agent-native trust: trust as agent-readable state, trust-gated execution semantics. | Agent trust awareness |
| `learning_pipeline_a2a_native.md` | 6,100 | Agent-native learning: pattern discovery as agent process, A/B testing from agent perspective. | Agent learning loop |
| `marine_reference_a2a_native.md` | 6,404 | Marine domain A2A spec: COLREGs as bytecode-enforceable rules, vessel capability descriptor. | Domain-specific A2A |

### 2.6 Dissertation (`dissertation/`)

Five-round iterative research. ~132,400 words across 25+ files.

#### Round 1: Technical Foundations (~28,100 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `round1_research/safety_deep_analysis.md` | 6,043 | 4-tier safety formal analysis, 3 independence proofs, 15-mode FMEA. | Safety formal verification |
| `round1_research/vm_deep_analysis.md` | 5,169 | ISA formal analysis: Turing-completeness proof, NaN safety proof, functional completeness. | VM theory |
| `round1_research/trust_deep_analysis.md` | 4,655 | Mathematical trust: fixed-point proofs, game theory, adversarial scenarios. | Trust mathematics |
| `round1_research/wire_protocol_analysis.md` | 4,530 | COBS overhead analysis, error rate calculation, reliability bounds. | Protocol theory |
| `round1_research/safety_references.md` | 3,232 | 54 functional safety references. | Safety literature |
| `round1_research/trust_references.md` | 2,843 | 58 trust & psychology references. | Trust literature |
| `round1_research/technical_references.md` | 1,603 | 40 embedded systems references. | Systems literature |
| `round1_research/safety_simulation.py` | (code) | Monte Carlo safety simulation (1000 iterations). | Reproducing safety results |
| `round1_research/trust_score_simulation.py` | (code) | 365-day trust evolution simulator. | Reproducing trust results |
| `round1_research/vm_benchmark.py` | (code) | Cycle-accurate VM benchmark. | Reproducing VM results |

#### Round 2: Domain & Regulatory (~50,100 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `round2_research/cross_domain_analysis.md` | 13,927 | **8-domain deep analysis.** 40 domain-specific safety rules, trust parameter calibration per domain. | Cross-domain work |
| `round2_research/regulatory_landscape.md` | 10,679 | 6 safety standards deep dive, 18-month SIL 1 certification path. | Regulatory compliance |
| `round2_research/ai_model_analysis.md` | 7,818 | AI/ML model comparison, Qwen2.5-Coder-7B selection rationale. | Model selection |
| `round2_research/regulatory_gap_analysis.md` | 6,616 | 93 compliance gaps identified, 25% certification readiness. | Gap analysis |
| `round2_research/domain_comparison_matrix.md` | 4,253 | 25-attribute comparison across 8 domains, 80% code reuse. | Domain comparison |
| `round2_research/learning_simulation.py` | (code) | Full learning pipeline simulation. | Reproducing learning results |
| `round2_research/ai_ml_references.md` | 2,615 | 85 AI/ML references. | AI literature |

#### Round 3: Philosophy & Ethics (~32,700 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `round3_research/eight_lenses_analysis.md` | 11,696 | **8 philosophical traditions (~28K words with glossary).** 5 universal themes, 7-8/8 consensus. | Cultural/philosophical grounding |
| `round3_research/ethics_analysis.md` | 8,397 | 6-section ethics analysis, 9-agent liability chain. | Ethics work |
| `round3_research/ethical_framework_proposal.md` | 7,083 | 10 machine-checkable guardrails, Ethics Review Board protocol. | Ethics governance |
| `round3_research/cross_cultural_design_principles.md` | 4,988 | 8 concrete spec changes proposed from cultural analysis. | Design principles |

#### Round 4: Simulations (~11,500 words + 3 simulation scripts)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `round4_simulations/network_architecture_analysis.md` | 4,438 | Topology, quorum analysis, 5-Jetson recommendation. | Fleet architecture |
| `round4_simulations/multireflex_analysis.md` | 4,220 | 5-reflex interference analysis, 73% variable collision rate (critical finding). | Multi-reflex deployment |
| `round4_simulations/endtoend_analysis.md` | 2,880 | Pipeline bottleneck analysis, 44μs execution, 20-40x faster than traditional. | Performance analysis |
| `round4_simulations/endtoend_simulation.py` | (code) | Full 7-phase pipeline trace. | Reproducing pipeline results |
| `round4_simulations/multireflex_simulation.py` | (code) | 5-reflex interference simulation. | Reproducing multi-reflex results |
| `round4_simulations/network_failure_simulation.py` | (code) | 10,000-hour network reliability simulation. | Reproducing network results |

#### Round 5: Synthesis (~10,000 words)

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `round5_synthesis/universal_synthesis.md` | 10,033 | Capstone integration. Validates the universal principle across all rounds. | Understanding the whole argument |

#### Companion Docs & Addenda (~2,900 words)

| File | Words | Key Contribution |
|------|------:|-----------------|
| `companion_docs/non_technical_guide.md` | 820 | Plain-language overview for general readers |
| `companion_docs/senior_engineer_deep_dive.md` | 900 | Specification improvements and findings |
| `companion_docs/master_bibliography.md` | 1,142 | 77 curated references across 12 categories |
| `addenda/debate_transcripts.md` | 1,223 | Multi-tradition debate on core questions |
| `addenda/multilingual_summaries.md` | 567 | 6-language executive summary |

### 2.7 Genesis Colony (`genesis-colony/`)

Earlier philosophical and architectural explorations that preceded and inspired the current NEXUS architecture. ~210,000 words across ~35 files. These documents represent the project's intellectual genesis — the "thinking out loud" phase before formalization.

**Key files:**
- `THE_COLONY_THESIS.md` — The founding thesis document
- `final/05_The_Ribosome_Not_the_Brain_Universal_Story.md` (~12,300 words) — The universal story
- `final/07_MYCELIUM_Precise_Architecture_v1.md` (~13,400 words) — Detailed MYCELIUM architecture
- `final/01_Whole_Boat_Intelligence_and_Muscular_System.md` (~12,400 words) — Whole-boat intelligence
- `phase2_discussions/12_WHITE_PAPER_The_Ribosome_Not_The_Brain.md` (~5,900 words) — White paper
- `01_GREEK_PHILOSOPHICAL_LENS_ANALYSIS.md` — Greek philosophical lens
- `02_CHINESE_PHILOSOPHICAL_LENS_ANALYSIS.md` — Chinese philosophical lens
- `SOVIET_ENGINEERING_LENS_ANALYSIS.md` — Soviet engineering lens
- `AFRICAN_COMMUNAL_LENS_ANALYSIS.md` — African communal lens
- `indigenous-lens-analysis-phase1.md` — Indigenous lens

### 2.8 Framework (`framework/`)

Core framework design documents. ~57,000 words across 7 files. These are intermediate-level design documents that bridge between the philosophical genesis and the production specifications.

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `01_distributed_intelligence_framework.txt` | 7,525 | Foundational framework for distributed intelligence | Architecture design |
| `02_nexuslink_protocol.txt` | 6,342 | Communication protocol design | Protocol work |
| `03_learning_and_optimization.txt` | 7,468 | Learning system design | Learning pipeline |
| `04_bulletproof_coding.txt` | 9,514 | Safety-first coding practices | Implementation |
| `05_cross_domain_use_cases.txt` | 10,538 | Use cases for all 8 domains | Domain planning |
| `06_evolutionary_code_system.txt` | 7,826 | Evolutionary approach to code generation | A2A code evolution |
| `07_master_consensus.txt` | 7,868 | Consensus mechanisms for agent coordination | Multi-agent design |

### 2.9 Autopilot Engineering (`autopilot/`)

ESP32 autopilot engineering and simulations. ~63,000 words across 8 text files + Python simulation and config files.

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `02_esp32_architecture.txt` | 11,191 | ESP32 firmware architecture for autopilot | Firmware implementation |
| `01_marine_pid_engineering.txt` | 9,272 | Marine PID controller engineering | Control engineering |
| `03_hydraulic_control.txt` | 10,489 | Hydraulic actuator control | Actuator interface |
| `04_opensource_analysis.txt` | 6,612 | Open-source autopilot comparison | Competitive analysis |
| `05_consensus_architecture.txt` | 4,825 | Consensus for multi-ESP32 coordination | Multi-node design |
| `08_expert_review.txt` | 7,030 | Expert review of autopilot design | Design validation |
| `06_pid_simulation.py` | (code) | PID simulation with 6 scenarios and plots | Simulation |

### 2.10 Vessel Platform (`vessel-platform/`)

Marine vessel platform architecture. ~74,000 words across 7 text files + JSON configs.

| File | Words | Key Contribution | Read When |
|------|------:|-----------------|-----------|
| `10_esp32_firmware_architecture.txt` | 11,352 | Complete ESP32 firmware architecture | Firmware design |
| `11_jetson_cluster_architecture.txt` | 10,000 | Jetson cluster design | Cognitive layer |
| `12_network_physical_architecture.txt` | 10,801 | Physical network design | Network engineering |
| `16_master_consensus_architecture.txt` | 9,607 | Master consensus protocol | Coordination |
| `13_calibration_onboarding.txt` | 8,095 | Calibration and onboarding procedures | Deployment |
| `15_redundancy_failover.txt` | 7,170 | Redundancy and failover mechanisms | Reliability |
| `14_marine_ai_systems.txt` | 6,537 | Marine AI systems integration | AI integration |

### 2.11 Engineering Addenda (`addenda/`)

Practical engineering guides. ~36,000 words across 7 documents.

| File | Words | Key Contribution |
|------|------:|-----------------|
| `06_Code_Review_Checklist.md` | 6,055 | Code review checklist for NEXUS code |
| `05_Integration_Test_Plan.md` | 4,975 | Integration testing plan |
| `03_Hardware_BringUp_Checklist.md` | 4,861 | Hardware bring-up procedures |
| `04_Safety_Validation_Playbook.md` | 4,975 | Safety validation procedures |
| `01_Engineering_Pitfalls_and_Gotchas.md` | 4,860 | Common pitfalls and solutions |
| `02_Performance_Budgets_and_Optimization.md` | 4,241 | Performance budgets and optimization |
| `00_Master_Addendum_Index.md` | 704 | Index of all addenda |

### 2.12 Miscellaneous

| Directory | Files | Notes |
|-----------|-------|-------|
| `v31-docs/` | 13 (.md and .pdf) | v3.1 documentation set — earlier version. User guides, architecture, developer guides. Historical reference. |
| `docs/` | 10 (.pdf, .pptx, .md) | Presentations, build prompts, developer guides. Outputs and presentations. |
| `schemas/post_coding/` | 4 (.json) | JSON schemas for autonomy_state, node_role_config, reflex_definition, serial_protocol. |
| `archives/` | 7 (.zip) | Complete project archives at various stages. |

### 2.13 Total Repository Statistics

| Category | Documents | Approximate Words |
|----------|----------:|------------------:|
| Production Specifications (`specs/`) | 21 | ~100,000 |
| Knowledge Base (`knowledge-base/`) | 27 | ~323,000 |
| A2A Language Research (`a2a-native-language/`) | 6 | ~45,200 |
| A2A Native Specs (`a2a-native-specs/`) | 8 | ~49,100 |
| Dissertation (`dissertation/`) | 25+ | ~132,400 |
| Framework (`framework/`) | 7 | ~57,100 |
| Genesis Colony (`genesis-colony/`) | ~35 | ~210,000 |
| Autopilot (`autopilot/`) | ~16 | ~63,000 |
| Vessel Platform (`vessel-platform/`) | ~13 | ~74,000 |
| Engineering Addenda (`addenda/`) | 7 | ~35,800 |
| Top-Level (`claude.md`, `README.md`) | 2 | ~12,000 |
| **TOTAL** | **~167** | **~1,101,600** |

---

## 3. Research Topology

This section maps the intellectual THREADS that weave through multiple documents, rather than individual documents. Each thread identifies its contributing documents, what has been resolved, what remains open, and the next question to investigate.

### Thread 1: Trust as a Mathematical Concept

**Contributing documents:** `specs/safety/trust_score_algorithm_spec.md`, `dissertation/round1_research/trust_deep_analysis.md`, `dissertation/round1_research/trust_score_simulation.py`, `knowledge-base/philosophy/trust_psychology_and_automation.md`, `a2a-native-specs/trust_system_a2a_native.md`, `a2a-native-language/cross_domain_a2a_applicability.md`

**Resolved:**
- The trust score formula is mathematically well-defined with 12 parameters and 6 autonomy levels.
- Fixed-point analysis proves T=0, T=1, T=t_floor are the only fixed points (all stable).
- The 25:1 loss-to-gain ratio is validated by 365-day simulation.
- Per-subsystem independence prevents cascading failures.
- Cross-domain calibration shows α_gain/α_loss ratio varies 150× across domains (derived from consequence-of-failure analysis).
- The 0.5× rule for agent-generated code is formally proposed.

**Open:**
- Non-stationary trust equilibrium (Open Problem 6): Does trust always converge under non-stationary event rates? Lyapunov stability analysis needed.
- Cross-vessel safety inconsistency (Open Problem 10): How does per-vessel trust divergence affect fleet coordination?
- Seasonal reset problem (from final_synthesis.md): How to separate bytecode confidence from deployment trust across idle periods?
- The Alignment-Utility Gap (Open Problem 22): Trust measures safety, not utility. A perfectly safe system that does nothing passes all checks.

**Next question:** Can we prove Lyapunov stability of the trust dynamics under arbitrary non-stationary inputs, or find a counterexample demonstrating trust oscillation?

### Thread 2: Bytecode as Lingua Franca

**Contributing documents:** `specs/firmware/reflex_bytecode_vm_spec.md`, `a2a-native-language/language_design_and_semantics.md`, `a2a-native-specs/bytecode_vm_a2a_native.md`, `dissertation/round1_research/vm_deep_analysis.md`, `knowledge-base/theory/type_systems_and_formal_languages.md`

**Resolved:**
- The 32-opcode ISA is proven Turing-complete for all continuous piecewise-polynomial functions.
- NaN/Inf cannot reach actuator outputs (Theorem 3).
- Compilation from JSON to bytecode is proven semantics-preserving by structural induction.
- The AAB format extends bytecode with agent-readable metadata at zero execution overhead.
- Intention blocks replace functions/classes as the fundamental unit of agent-native programs.

**Open:**
- Minimum Expressive Power (Open Problem 7): What is the minimal opcode set? Current set may have redundancy.
- Agent Type System (Open Problem 2): Can we define a type system that guarantees safety properties under composition? Current validator checks structural invariants but not semantic properties.
- Formal Semantics of Agent Intention (Open Problem 3): How to formally connect natural-language intention to bytecode semantics?
- Information Preservation (Open Problem 5): How much understanding survives each compilation stage?

**Next question:** Can abstract interpretation over the 32-opcode ISA compute bounded output ranges for any bytecode program, enabling static safety verification without execution?

### Thread 3: Safety as Structural Invariant

**Contributing documents:** `specs/safety/safety_system_spec.md`, `specs/safety/safety_policy.json`, `dissertation/round1_research/safety_deep_analysis.md`, `dissertation/round1_research/safety_simulation.py`, `addenda/04_Safety_Validation_Playbook.md`, `knowledge-base/theory/formal_verification_and_safety.md`

**Resolved:**
- Four-tier defense-in-depth is formally specified with independence proofs.
- Monte Carlo simulation validates SIL 1 compliance (PFH < 10⁻⁷/h).
- 97.06% system availability achieved in simulation.
- 10 universal safety rules + 40 domain-specific rules (5 per domain) are codified.
- Kill switch response time (0.93ms) is hardware-verified.
- Watchdog pattern (0x55/0xAA) and timeout (200ms) are specified.

**Open:**
- The Certification Paradox (Open Problem 1): Static standards vs. dynamic, evolving bytecode. No existing pathway.
- Adversarial Bytecode (Open Problem 9): Can an agent craft structurally valid but semantically dangerous bytecode?
- Neural Network Verification (Open Problem 8): How to verify LLM-generated code at scale? 4.9% miss rate on cross-validation.
- Graceful Degradation (Open Problem 12): Behavior under arbitrary multi-node failure combinations.
- Sensor-Actuator Loop Timing (Open Problem 11): Formal timing bounds for the full pipeline.

**Next question:** Can the Predetermined Change Control Plan (PCCP) concept from FDA's AI/ML guidance provide a certification pathway for continuously evolving bytecode?

### Thread 4: Agent as Compiler

**Contributing documents:** `a2a-native-language/final_synthesis.md`, `a2a-native-language/language_design_and_semantics.md`, `a2a-native-language/nexus_integration_analysis.md`, `a2a-native-specs/bytecode_vm_a2a_native.md`, `knowledge-base/theory/program_synthesis_and_ai_codegen.md`, `specs/jetson/learning_pipeline_spec.md`

**Resolved:**
- The system-prompt-as-compiler concept is formalized with input/output grammars and semantic constraints.
- JSON schema compliance achieves 96% via GBNF grammar constraints.
- Semantic correctness is 87% (empirical, not formally proven).
- Safety adherence is 82% (needs improvement — target ≥90%).
- The compilation pipeline (NL → JSON → bytecode → assembly → hardware) is mapped with information loss at each stage.
- Cross-agent validation (Qwen generates, Claude validates) catches 93.3% of safety issues.

**Open:**
- Optimal System Prompt (Open Problem 15): Systematic methodology for prompt optimization (currently ad-hoc).
- Agent Cross-Validation Reliability (Open Problem 13): 4.9% miss rate with unknown bias patterns.
- Cultural Bias (Open Problem 14): Does LLM training data bias bytecode for non-Western contexts?
- Black Box Provenance (Open Problem 6 in final_synthesis): Can we trace WHY an LLM generated specific bytecode?

**Next question:** Can Bayesian optimization over system prompts achieve ≥99% schema compliance and ≥90% safety adherence on a benchmark of 500 reflex generation tasks?

### Thread 5: Safety as Cultural Universal

**Contributing documents:** `dissertation/round3_research/eight_lenses_analysis.md`, `dissertation/round3_research/cross_cultural_design_principles.md`, `genesis-colony/01_GREEK_PHILOSOPHICAL_LENS_ANALYSIS.md`, `genesis-colony/02_CHINESE_PHILOSOPHICAL_LENS_ANALYSIS.md`, `genesis-colony/SOVIET_ENGINEERING_LENS_ANALYSIS.md`, `genesis-colony/AFRICAN_COMMUNAL_LENS_ANALYSIS.md`, `genesis-colony/indigenous-lens-analysis-phase1.md`, `knowledge-base/foundations/cross_cultural_computing.md`

**Resolved:**
- 8 cultural traditions analyzed (Western Analytic, Daoist, Confucian, Soviet Engineering, African Ubuntu, Indigenous, Japanese, Islamic Golden Age).
- 5 universal themes identified with 7-8/8 consensus.
- 8 concrete specification changes proposed based on cultural analysis.
- Cross-cultural trust calibration shows systematic differences in risk tolerance.
- The 150× variation in trust α_gain/α_loss ratio across domains correlates with cultural risk tolerance.

**Open:**
- Indigenous lens analysis is marked "phase 1" — incomplete.
- Japanese lens and Islamic Golden Age lens exist only as summaries within the eight_lenses_analysis.md, not as standalone documents (unlike Greek, Chinese, Soviet, African).
- No empirical validation of cultural design principles against actual deployment data.
- The proposed spec changes from cross-cultural analysis have not been implemented.

**Next question:** Do the 8 proposed specification changes from cultural analysis measurably improve trust calibration when deployed across multiple cultural contexts?

### Thread 6: Evolutionary Code

**Contributing documents:** `knowledge-base/theory/evolutionary_computation.md`, `framework/06_evolutionary_code_system.txt`, `a2a-native-language/final_synthesis.md`, `dissertation/round2_research/cross_domain_analysis.md`, `knowledge-base/foundations/biological_computation_and_evolution.md`

**Resolved:**
- The evolutionary computation knowledge base article maps GA/GP/ES/DE to NEXUS concepts.
- NEXUS bytecode is explicitly framed as a "genotype" that can evolve.
- The fleet is modeled as a "population" for evolutionary optimization.
- Seasonal mutation rates (Spring 30% → Autumn 5%) map to Langton's Lambda parameter on the order-chaos spectrum.
- The "adaptive safety" concept proposes that 2-3% of nodes operate with reduced safety rules as evolutionary probes.
- The Griot narrative layer provides a "genetic memory" that preserves knowledge across bytecode generations.

**Open:**
- Bounded Emergence Prediction (Open Problem 4): Can we bound the probability and severity of emergent behaviors in a 200-500 vessel fleet?
- No actual evolutionary code system has been implemented — all analysis is theoretical.
- The interaction between evolutionary safety boundary experiments and the four-tier safety system is unresolved (can Tier 1 hardware safety be "evolved"?).
- Fleet-level learning (sharing evolved bytecodes across vessels) has no protocol specification.

**Next question:** What protocol enables safe fleet-level bytecode sharing while preserving per-vessel trust independence and preventing cascade contamination?

### Thread 7: Cross-Domain Generalization

**Contributing documents:** `dissertation/round2_research/cross_domain_analysis.md`, `dissertation/round2_research/domain_comparison_matrix.md`, `a2a-native-language/cross_domain_a2a_applicability.md`, `framework/05_cross_domain_use_cases.txt`, `specs/ports/hardware_compatibility_matrix.json`

**Resolved:**
- 80% code reuse validated across 8 domains with 25-attribute comparison matrix.
- 4 natural domain clusters identified (Extreme Safety, Industrial Safety, Moderate Automation, Consumer/Low-Risk).
- Trust α_gain/α_loss ratio calibrated for all 8 domains.
- 40 domain-specific safety rules defined (5 per domain).
- Maximum agent code autonomy level determined per domain (L1 Healthcare to L5 Home).
- 13 MCU compatibility evaluations completed with porting effort estimates.
- Domain-specific communication adapters identified (NMEA, ISOBUS, BACnet, Matter, etc.).

**Open:**
- Agent Specialization vs Generalization (Open Problem 16): Should agents specialize per domain or remain general?
- No bytecode has actually been transferred between domains — all analysis is theoretical.
- Domain-specific protocol adapters (ISOBUS, BACnet, Matter, etc.) have not been implemented.
- Healthcare domain analysis is shallowest — most regulatory uncertainty.
- No formal study comparing specialized vs. general bytecode generation quality.

**Next question:** Can a general-purpose agent with domain-specific system prompt prefixes match the bytecode quality of a domain-specialized fine-tuned agent?

### Thread 8: Swarm Intelligence and Multi-Agent Coordination

**Contributing documents:** `knowledge-base/theory/self_organizing_systems.md`, `a2a-native-language/agent_communication_and_runtime_model.md`, `dissertation/round4_simulations/network_architecture_analysis.md`, `a2a-native-specs/bytecode_vm_a2a_native.md` (swarm section), `framework/07_master_consensus.txt`

**Resolved:**
- The self-organizing systems knowledge base article provides the theoretical framework (CAS, swarm, emergence).
- Agent communication protocol is proposed with 3 patterns: Proposal-Validation-Deployment, Peer Negotiation, Communal Veto.
- Network architecture analysis recommends 5-Jetson topology with Raft consensus (≥2 of 3 for quorum).
- 5 concrete coordination scenarios are documented.
- The A2A wire protocol extensions include AGENT_PROPOSE, AGENT_VALIDATE, VOTE_REJECT, PALAVER_FLAG messages.

**Open:**
- Bounded Emergence (Open Problem 4): 500! interaction patterns in a 500-agent system.
- Multi-Agent Coordination Problem (final_synthesis.md §6.4): Combinatorial explosion of interactions.
- Emergent Agent Communication (Open Problem 17): Will agents invent communication channels outside the designed protocol?
- No multi-agent coordination system has been implemented.
- No communal veto mechanism has been implemented.
- The A/B testing bottleneck (60 min = 99.96% of deployment latency) severely limits agent coordination speed.

**Next question:** What are the minimum viable multi-agent coordination primitives that enable safe fleet-scale operation without exhaustive interaction analysis?

### Thread 9: Formal Verification vs. Learning-Based Assurance

**Contributing documents:** `knowledge-base/theory/formal_verification_and_safety.md`, `knowledge-base/theory/type_systems_and_formal_languages.md`, `dissertation/round1_research/vm_deep_analysis.md`, `a2a-native-specs/bytecode_vm_a2a_native.md` (agent validation pipeline)

**Resolved:**
- Formal verification is possible for structural properties (stack balance, jump targets, NaN/Inf — proven as Theorem 3).
- The 32-opcode VM enables single-pass validation in O(n) time.
- Curry-Howard correspondence is identified as a theoretical bridge (types are propositions, programs are proofs) but NEXUS bytecode exists below the Curry-Howard threshold.
- The 6-step agent validation pipeline is defined (generate → structural check → semantic check → A/B test → trust gate → deploy).
- Cross-model validation (93.3% catch rate) provides practical but not principled assurance.

**Open:**
- No formal verification of behavioral properties (e.g., "this bytecode implements correct heading hold").
- No proof-carrying bytecode mechanism.
- The gap between formal verification (strong but narrow) and learning-based assurance (broad but weak) is unresolved.
- The agent type system (Open Problem 2) would bridge this gap but is undesigned.
- Neural network formal verification tools handle at most hundreds of neurons, not billions.

**Next question:** Can abstract interpretation over the 32-opcode ISA provide bounded output ranges that serve as lightweight formal verification for behavioral safety properties?

### Thread 10: The Ribosome Metaphor and Biological Computation

**Contributing documents:** `claude.md` (§THE CORE IDEA), `knowledge-base/foundations/biological_computation_and_evolution.md`, `genesis-colony/final/05_The_Ribosome_Not_the_Brain_Universal_Story.md`, `genesis-colony/phase2_discussions/02_DNA_Code_Cell_Protein_Metaphors.md`, `genesis-colony/phase2_discussions/07_IoT_As_Protein_Architecture.md`, `a2a-native-language/final_synthesis.md` (§8 Conclusion)

**Resolved:**
- The ribosome metaphor is the project's founding principle: distribute cognition to the periphery.
- Biological computation knowledge base maps DNA→RNA→protein to intention→bytecode→action.
- The MYCELIUM architecture (genesis-colony/final/07_) provides a detailed biological metaphor for the system.
- IoT-as-protein architecture (phase2_discussions/07_) maps sensors/actuators to biological proteins.
- The universal principle — "distributed local > centralized" — is validated across biology, computing, organization theory, and philosophy.

**Open:**
- The biological metaphor is inspiring but not formally rigorous. No mathematical mapping between biological and computational systems.
- The "evolutionary safety boundary" concept (2-3% probe nodes) has no biological analogue and may be unsafe.
- The Griot narrative layer (genetic memory) has no specification for encoding/decoding narratives.

**Next question:** Does the biological metaphor suggest any computational mechanisms not yet explored in NEXUS (e.g., epigenetic regulation, immune system analogues, horizontal gene transfer)?

### Thread 11: Post-Coding Paradigm and the Role of Humans

**Contributing documents:** `knowledge-base/philosophy/post_coding_paradigms.md`, `a2a-native-language/final_synthesis.md`, `dissertation/round3_research/ethics_analysis.md`, `dissertation/companion_docs/non_technical_guide.md`

**Resolved:**
- L0-L5 coding autonomy levels are defined (Manual → Advisory → Assisted → Supervised → Autonomous → Full).
- NEXUS operates at L4-L5 for code generation: humans describe intent, agents generate code.
- The operator's role shifts from programmer to supervisor/governor.
- The 0.5× trust rule creates an explicit epistemic humility about agent-generated code.
- The Griot narrative layer preserves human-readable explanations of agent decisions.

**Open:**
- Responsibility at L5 (Open Problem from claude.md §6): When fully autonomous system causes harm, who is liable?
- The "many hands" problem: 9+ agents in the causal chain, opaque LLM reasoning.
- No protocol for humans to override or audit agent decisions at runtime (beyond the kill switch).
- Does the elimination of human code review create an ethical obligation for enhanced transparency?

**Next question:** What governance framework assigns responsibility across the 9+ agent chain while maintaining the efficiency benefits of A2A-native programming?

### Thread 12: Regulatory Compliance and Certification

**Contributing documents:** `dissertation/round2_research/regulatory_landscape.md`, `dissertation/round2_research/regulatory_gap_analysis.md`, `knowledge-base/reference/autonomous_systems_law.md`, `specs/safety/safety_system_spec.md` (certification checklist), `a2a-native-language/cross_domain_a2a_applicability.md`

**Resolved:**
- 6 safety standards analyzed (IEC 61508, ISO 26262, DO-178C, IEC 62061, ISO 13849, IEC 60945).
- 93 compliance gaps identified with 25% current certification readiness.
- 18-month SIL 1 certification path mapped.
- NEXUS targets IEC 61508 SIL 1, ISO 26262 ASIL-B equivalent.
- EU AI Act compliance requires ~€180K-€480K investment.
- The PCCP concept is identified as a potential bridge for the certification paradox.

**Open:**
- The Certification Paradox (Open Problem 1): No pathway for certifying continuously evolving software.
- EU AI Act compliance for A2A-generated code is uncharted territory.
- Maritime regulatory framework (IMO MASS Code) is still evolving.
- No certification body has been engaged for pre-assessment.
- Cross-domain regulatory harmonization is not addressed.

**Next question:** Can a PCCP-based approach satisfy IEC 61508 SIL 1 requirements for the bytecode evolution process, even if individual bytecodes cannot be statically certified?

### Thread 13: Hardware-Software Co-Design

**Contributing documents:** `knowledge-base/systems/hardware_software_codesign.md`, `knowledge-base/systems/embedded_and_realtime_systems.md`, `knowledge-base/systems/edge_ai_encyclopedia.md`, `specs/firmware/memory_map_and_partitions.md`, `specs/ports/hardware_compatibility_matrix.json`, `vessel-platform/10_esp32_firmware_architecture.txt`

**Resolved:**
- ESP32-S3 selected as Tier 1 platform ($6-10, best price/performance/IO).
- Jetson Orin Nano selected as Tier 2 platform (40 TOPS minimum for 7B inference).
- Complete memory map with SRAM/PSRAM budgets.
- 13 MCU compatibility evaluations with porting effort.
- BOM analysis ($684 per vessel for reference marine implementation).
- Zero-heap design: all runtime memory is statically allocated.
- Power/thermal analysis: 8-15W for Jetson, <1W per ESP32.

**Open:**
- Porting to other MCU families (STM32, RP2040) is evaluated but not implemented.
- Jetson Orin Nano Super upgrade (67 TOPS vs 40 TOPS) is not reflected in current specs.
- TensorRT optimization path for Jetson inference is identified but not explored.
- Memory-constrained computing on ESP32 (512KB SRAM) limits observation buffer sizes.
- No hardware-in-loop testing has been performed.

**Next question:** What is the minimum Jetson-class hardware that can run Qwen2.5-Coder-7B inference at ≥10 tok/s while leaving sufficient resources for the learning pipeline?

### Thread 14: Learning and Pattern Discovery

**Contributing documents:** `specs/jetson/learning_pipeline_spec.md`, `dissertation/round4_simulations/endtoend_analysis.md`, `knowledge-base/theory/program_synthesis_and_ai_codegen.md`, `a2a-native-specs/learning_pipeline_a2a_native.md`

**Resolved:**
- 5 pattern discovery algorithms specified (cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference).
- A/B testing framework is defined with 60-minute minimum test duration.
- End-to-end pipeline measured: 44μs execution, 20-40x faster than traditional development.
- The 60-minute A/B test is 99.96% of total deployment latency — this is the natural throttle.
- Learning pipeline is specified as 6 stages: Observe → Record → Discover → Synthesize → A/B Test → Deploy.

**Open:**
- Inverse RL for pattern discovery is identified but has LOW confidence (may be demoted to optional).
- No actual learning pipeline has been implemented — all analysis is simulation-based.
- The A/B testing bottleneck may be too conservative for low-risk domains (Home, HVAC).
- Multi-reflex variable collision (73% rate from Round 4 simulation) blocks multi-reflex learning.
- No online/incremental learning — all pattern discovery is batch.

**Next question:** Can the A/B testing duration be dynamically calibrated based on domain risk level (60 minutes for Marine, 5 minutes for Home)?

### Thread 15: Documentation as Living System

**Contributing documents:** This entire repository. The `claude.md` file is itself an example of documentation-as-system — it is both a reference document and a functional system prompt.

**Resolved:**
- The Rosetta Stone concept creates dual-lens documentation (human specs + agent-native specs).
- Wiki-links ([[bracketed references]]) connect documents into a knowledge graph.
- The A2A-native specs are designed to be machine-readable — agents can consume them directly.
- The 310-term glossary provides a shared vocabulary.
- The open problems catalog provides a research roadmap.

**Open:**
- No automated documentation consistency checking.
- Wiki-links may be broken or stale.
- The v31-docs directory contains outdated documentation that may confuse new agents.
- No automated process to update the Rosetta Stone when human specs change.
- The genesis-colony documents contain valuable ideas but are poorly indexed.

**Next question:** Can the documentation be structured as a machine-readable knowledge graph that agents can query, validate, and extend automatically?

---

## 4. Concept Dependency Graph

This section maps which concepts must be understood before others. Concepts are listed in dependency order — read top-to-bottom.

### Level 0: Prerequisites (No Dependencies)

These concepts can be understood in isolation. They are the foundational vocabulary:

1. **Float32 Arithmetic** — IEEE 754 single-precision, NaN, Infinity, CLAMP_F
2. **Stack Machine** — Push/pop semantics, no register allocation, deterministic execution
3. **UART/RS-422 Serial** — Point-to-point, full-duplex, differential signaling
4. **FreeRTOS** — Preemptive RTOS, task priorities, mutex, queue
5. **COBS Framing** — Zero-overhead byte stuffing, frame delimiting
6. **CRC-16** — Error detection polynomial
7. **MCU Architecture** — ESP32-S3, Xtensa LX7, SRAM, PSRAM, GPIO, I2C, PWM
8. **Edge AI** — Quantization (Q4_K_M), GGUF, llama.cpp, TOPS

### Level 1: Core Architecture (Depends on Level 0)

9. **Three Architecture Tiers** — Requires understanding of: MCU (L0.7), Edge AI (L0.8), serial communication (L0.3)
10. **32-Opcodes VM** — Requires understanding of: Stack Machine (L0.2), Float32 (L0.1)
11. **Wire Protocol** — Requires understanding of: RS-422 (L0.3), COBS (L0.5), CRC-16 (L0.6)
12. **Four-Tier Safety** — Requires understanding of: Three Tiers (L1.9), FreeRTOS (L0.4), MCU (L0.7)
13. **Reflex (Bytecode Program)** — Requires understanding of: 32-Opcodes VM (L1.10)

### Level 2: Behavioral Systems (Depends on Level 1)

14. **INCREMENTS Trust Algorithm** — Requires understanding of: Four-Tier Safety (L1.12) [safety events feed trust]
15. **Learning Pipeline** — Requires understanding of: Three Tiers (L1.9), Reflex (L1.13) [generates reflexes]
16. **A/B Testing Framework** — Requires understanding of: Learning Pipeline (L2.15), Trust (L2.14) [gated by trust]
17. **Role Assignment** — Requires understanding of: Wire Protocol (L1.11), VM (L1.10) [configures VM I/O]
18. **Hot-Loading** — Requires understanding of: VM (L1.10), Wire Protocol (L1.11) [deploys new bytecodes]
19. **JSON→Bytecode Compiler** — Requires understanding of: VM ISA (L1.10), Reflex schema

### Level 3: Agent-Level Concepts (Depends on Level 2)

20. **System Prompt as Compiler** — Requires understanding of: JSON→Bytecode Compiler (L2.19), Learning Pipeline (L2.15) [context for prompt]
21. **Agent-Annotated Bytecode (AAB)** — Requires understanding of: 32-Opcodes VM (L1.10) [extends the instruction format], TLV encoding
22. **Agent Cross-Validation** — Requires understanding of: System Prompt Compiler (L3.20), Trust (L2.14) [gated by trust], Safety (L1.12)
23. **0.5× Trust Rule** — Requires understanding of: INCREMENTS Trust (L2.14) [modifies alpha_gain]
24. **Intention Blocks** — Requires understanding of: AAB (L3.21) [uses new opcodes]

### Level 4: A2A-Native Paradigm (Depends on Level 3)

25. **29 New Opcodes** — Requires understanding of: AAB (L3.21) [extends with new opcodes], Backward compatibility (NOP on existing VM)
26. **Three Pillars** — Requires understanding of: System Prompt Compiler (L3.20), Equipment/Runtime (L2.17), Vessel/Hardware (L1.9)
27. **Agent Communication Protocol** — Requires understanding of: New Opcodes (L4.25) [TELL, ASK, DELEGATE], Wire Protocol (L1.11)
28. **Communal Veto** — Requires understanding of: Agent Communication (L4.27), Trust (L2.14) [voting threshold]
29. **A2A-Native Paradigm** — Requires understanding of: Three Pillars (L4.26), AAB (L3.21), New Opcodes (L4.25), 0.5× Rule (L3.23)

### Level 5: Fleet and Cross-Domain (Depends on Level 4)

30. **Swarm Architecture** — Requires understanding of: A2A Paradigm (L4.29), Agent Communication (L4.27), Trust propagation
31. **Cross-Domain Architecture** — Requires understanding of: Trust (L2.14) [per-domain calibration], Safety (L1.12) [domain rules], Learning Pipeline (L2.15) [domain adaptation]
32. **Fleet-Level Learning** — Requires understanding of: Swarm (L5.30), Learning Pipeline (L2.15) [sharing evolved bytecodes]

### Level 6: Certification and Philosophy (Depends on Level 5)

33. **Certification Paradox** — Requires understanding of: A2A Paradigm (L4.29) [evolving bytecode], Safety standards (L1.12)
34. **Cross-Cultural Design Principles** — Requires understanding of: Trust (L2.14) [cultural risk tolerance], Safety (L1.12) [universal vs. domain-specific]
35. **Ethical Framework** — Requires understanding of: A2A Paradigm (L4.29) [responsibility], Fleet (L5.30) [scale of consequences]

---

## 5. Where We Left Off

### 5.1 What Has Been Deeply Researched

The following areas have received thorough, multi-document research with formal analysis, simulations, and cross-validation:

1. **The 32-Opcodes VM** — Complete specification (2,487 lines), formal analysis with Turing-completeness proof, NaN safety proof, cycle-accurate benchmarks. The VM is the most thoroughly understood component.

2. **The INCREMENTS Trust Algorithm** — Full mathematical specification (2,414 lines), 365-day simulation, fixed-point analysis, game-theoretic adversarial analysis, cross-domain calibration for all 8 domains. The trust algorithm is the second most thoroughly understood component.

3. **Four-Tier Safety System** — Formal specification (1,296 lines), Monte Carlo simulation (1000 iterations), independence proofs, 15-mode FMEA, SIL 1 compliance validation. Safety has been analyzed from hardware through application layer.

4. **Cross-Domain Analysis** — 8 domains analyzed across 25 attributes, domain comparison matrix, 40 domain-specific safety rules, trust parameter calibration. The 80% universality claim is well-supported.

5. **A2A-Native Language Design** — 6 documents (45K words) covering language philosophy, AAB format, 29 new opcodes, assembly mapping, integration, agent communication, cross-domain applicability, and grand synthesis. This is the most comprehensive research thread.

6. **The Rosetta Stone (A2A-Native Specs)** — 8 documents providing agent-native twins of core specifications. The bytecode_vm_a2a_native.md (9,261 words) is the most complete agent-native specification.

7. **Philosophical Foundations** — 8 cultural lenses analyzed (11,696 words for eight_lenses alone), 5 universal themes identified, ethics analysis (8,397 words), ethical framework proposal (7,083 words).

8. **Wire Protocol** — Full specification (1,047 lines), reliability analysis, COBS overhead calculation, error rate bounds. Plus A2A-native twin (7,811 words).

### 5.2 What Has Been Sketched But Needs Depth

The following areas have been identified, outlined, or partially analyzed but require significantly more work:

1. **Agent Type System (Open Problem 2)** — The concept is described in `knowledge-base/theory/type_systems_and_formal_languages.md` (capability types, trust types, effect types, refinement types, linear types, session types) but no formal type system has been designed. The current validator checks structural invariants only. Estimated 18-24 person-months.

2. **Multi-Reflex Variable Namespace Isolation** — The 73% collision rate was discovered in Round 4 simulation and identified as the highest-priority fix (SP-01 in final_synthesis.md), but no specification has been written. Cost: 256 bytes of runtime table.

3. **Agent Communication Protocol** — Message types are proposed (AGENT_PROPOSE, AGENT_VALIDATE, VOTE_REJECT, PALAVER_FLAG) in the A2A research but no formal protocol specification exists. The 12 wire protocol extensions are listed but not fully specified.

4. **Communal Veto Mechanism** — The concept is described in `agent_communication_and_runtime_model.md` and `final_synthesis.md` but no implementation specification exists. Minimum cluster size, agreement threshold, and escalation procedures are undefined.

5. **Formal Semantics of Agent Intention** — Identified as Open Problem 3. The Griot narrative layer is proposed as a partial solution but has no formal specification. No intent specification language has been designed.

6. **Domain-Specific Protocol Adapters** — ISOBUS (Agriculture), BACnet (HVAC), Matter (Home), HL7 (Healthcare), Leaky Feeder (Mining) are identified but not specified.

7. **Fleet-Level Bytecode Sharing Protocol** — The concept is described (federated learning where the "model" is a library of bytecodes) but no protocol exists for safe bytecode sharing across vessels.

8. **Evolutionary Safety Boundary Experiment** — The concept (2-3% of nodes with reduced safety rules as evolutionary probes) is proposed in `final_synthesis.md` but has no formal safety analysis or implementation plan.

### 5.3 What Has Been Identified But Not Started

The following are recognized as important but have received no substantive work:

1. **Adversarial Bytecode Generator (Open Problem 9)** — No systematic study of adversarial bytecode has been conducted. No tool exists to generate adversarial bytecodes for stress-testing the validation pipeline.

2. **Abstract Interpretation over the VM ISA** — Proposed approach for bounded output range analysis (Open Problem 2) but no implementation. Would enable static verification of behavioral safety properties.

3. **PCCP-Based Certification Submission** — The Predetermined Change Control Plan is identified as the bridge for the certification paradox but no PCCP has been drafted.

4. **Lyapunov Stability Proof for Trust Dynamics** — Proposed approach for Open Problem 6 but no mathematical analysis has been attempted.

5. **System Prompt Optimization Framework** — Bayesian optimization over system prompts (Open Problem 15) is proposed but no framework exists. Current prompt engineering is ad-hoc.

6. **Cultural Bias Measurement in Bytecode Generation** — Open Problem 14 is identified but no empirical study has been designed.

7. **Hardware-in-Loop Testing** — No HIL testing has been performed. All validation is simulation-based.

8. **Information-Theoretic Analysis of Compilation Stages** — Open Problem 5 (information preservation across NL → JSON → bytecode → assembly → hardware) is identified but no analysis tool exists.

### 5.4 What Hasn't Been Thought Of Yet

Based on the thoroughness of existing research, the following areas are conspicuously absent and may represent blind spots:

1. **Multi-Vessel Physical Safety Coordination** — What happens when two autonomous vessels with different trust levels need to physically coordinate (e.g., one vessel is a tugboat assisting a larger vessel)? The fleet coordination analysis assumes homogeneous trust levels.

2. **Bytecode Versioning and Rollback** — When a new bytecode is deployed and causes problems, how does the system roll back to the previous version? Hot-loading enables forward deployment but no rollback mechanism is specified.

3. **Agent Identity and Authentication** — In the A2A paradigm, how does the system verify that an agent claiming to be "Claude 3.5 Sonnet" is actually Claude 3.5 Sonnet? No agent authentication mechanism exists.

4. **Longitudinal Trust Data Management** — After 365+ days of operation, the trust history data grows indefinitely. No data retention, compression, or archival policy is specified.

5. **Operator Cognitive Load** — When a fleet of 50+ vessels generates thousands of bytecode proposals per day, how does the human operator avoid cognitive overload? No attention management or priority filtering system is designed.

6. **Byzantine Fault Tolerance in Agent Validation** — What if the safety validator agent itself is compromised or buggy? Current architecture requires exactly two agents (generator + validator) but does not handle Byzantine failures in the validator.

7. **Bytecode Intellectual Property** — When an agent on Vessel A evolves an innovative bytecode and shares it with Vessel B, who owns the IP? No licensing or attribution framework for agent-generated bytecodes exists.

8. **Energy Budget for AI Inference** — The Jetson consumes 8-15W. In solar/battery-powered vessels, how is the energy budget for AI inference managed? No power-aware scheduling for the learning pipeline exists.

### 5.5 Concrete Next Actions for the Next Research Agent

Prioritized by impact and feasibility:

**Immediate (Weeks 1-2):**
1. Implement per-reflex variable namespace isolation specification (SP-01). This is the highest-priority specification improvement identified across all research threads. Write the spec, update the VM spec, and add it to the A2A-native Rosetta Stone.

2. Write the formal agent communication protocol specification. Define the 5 proposed message types (AGENT_PROPOSE, AGENT_VALIDATE, AGENT_REJECT, VOTE_REJECT, PALAVER_FLAG) with full payload schemas, state machines, and timing requirements.

3. Design and draft the PCCP (Predetermined Change Control Plan) outline. Engage with the structure of what a PCCP would look like for NEXUS, even if regulatory filing is months away.

**Short-Term (Weeks 3-6):**
4. Begin the abstract interpretation engine for bounded output range analysis over the 32-opcode ISA. Start with interval arithmetic on sensor inputs → actuator outputs.

5. Design the agent type system specification. Start with capability types and trust types as the two most impactful extensions.

6. Write the communal veto mechanism specification: minimum cluster size, agreement threshold, escalation procedures, timing requirements.

**Medium-Term (Weeks 7-12):**
7. Build the adversarial bytecode generator tool. Systematically produce bytecodes that test the boundaries of each validator's safety rule coverage.

8. Design the system prompt optimization framework. Establish benchmark reflex generation tasks and baseline metrics.

9. Specify the bytecode versioning and rollback mechanism for the hot-loading system.

**Long-Term (Months 3-6):**
10. Draft the full PCCP for IEC 61508 SIL 1 submission. Include process description, validation requirements, and deployment criteria.

11. Design the fleet-level bytecode sharing protocol with trust propagation and contamination prevention.

12. Conduct cultural bias measurement study across at least 3 non-Western regulatory contexts.

---

## Appendix: Quick-Start Reading Order

For an agent that needs to become productive as fast as possible:

1. `claude.md` (366 lines) — Everything in one file
2. `specs/00_MASTER_INDEX.md` (138 lines) — Spec navigation
3. `a2a-native-specs/README.md` (215 lines) — A2A Rosetta Stone concept
4. `a2a-native-language/final_synthesis.md` (6,114 words) — The grand thesis
5. `knowledge-base/reference/open_problems_catalog.md` (9,606 words) — What to work on
6. `knowledge-base/reference/nexus_glossary.md` (14,200 words) — Vocabulary
7. `specs/firmware/reflex_bytecode_vm_spec.md` (2,487 lines) — The VM
8. `specs/safety/trust_score_algorithm_spec.md` (2,414 lines) — Trust math

Total: ~2-3 hours of reading for full project orientation.

---

*This context map was generated by an AI research agent on 2025-07-14. It represents the state of the NEXUS project as of that date. The project contains approximately 1.1 million words across ~167 documents. For questions about any specific concept, consult the glossary (310 terms) or the open problems catalog (29 problems).*
