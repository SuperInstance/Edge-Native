# CLAUDE.md — NEXUS Project Context for Claude Code

> **Read this file first.** This document gives you complete context to reason about the NEXUS project at the highest level. Every subsequent document you read should be understood through the lens of what's described here.

---

## ONE-SENTENCE SUMMARY

NEXUS is a distributed intelligence platform for industrial robotics where LLM agents — not humans — are the primary authors, interpreters, and validators of control code, executing on a bytecode VM that runs on embedded hardware (ESP32-S3) with AI cognition on edge GPUs (Jetson Orin Nano), governed by a mathematical trust algorithm that requires 27 days of safe operation before any subsystem earns full autonomy.

---

## THE CORE IDEA (THE RIBOSOME, NOT THE BRAIN)

Most robotics platforms put intelligence in the center (the "brain") and the limbs are dumb actuators. NEXUS inverts this: intelligence is distributed to the periphery. Each limb runs a bytecode virtual machine on an ESP32-S3 microcontroller that executes reflex programs at 1ms ticks. The Jetson Orin Nano provides AI cognition (pattern discovery, natural language, reflex synthesis) but the ESP32 maintains control even when ALL higher tiers fail. Like a biological ribosome, which translates mRNA into proteins WITHOUT understanding — the ESP32 executes bytecode without any comprehension. Like the brain, which plans and learns — the Jetson synthesizes new reflexes and improves existing ones.

**The A2A-native extension**: Agents (LLMs) are the "first-class interpreters" of this system. They generate the bytecode, validate each other's bytecode, and communicate through bytecode deployed to hardware. Humans are many abstractions away — they describe intentions in natural language, and agents translate those intentions into hardware-executable code. The system prompt IS the compiler frontend. The runtime equipment IS the execution context. The hardware vessel IS the capability boundary.

---

## ARCHITECTURE — THREE TIERS

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: CLOUD — Heavy training, simulation, fleet mgmt     │
│  Hardware: Starlink / 5G  │  Latency: seconds to hours      │
│  Role: Qwen2.5-Coder-7B full training, fleet optimization   │
├─────────────────────────────────────────────────────────────┤
│  TIER 2: COGNITIVE — AI inference, NLP, pattern discovery   │
│  Hardware: Jetson Orin Nano (40 TOPS, 8GB LPDDR5, 8-15W)    │
│  Role: LLM inference (Qwen2.5-Coder-7B Q4_K_M), reflex     │
│  synthesis, A/B testing, MQTT to cloud, wire to ESP32s      │
├─────────────────────────────────────────────────────────────┤
│  TIER 1: REFLEX — Real-time control, bytecode execution     │
│  Hardware: ESP32-S3 (Xtensa LX7, 240MHz, 512KB SRAM)        │
│  Role: 32-opcode stack VM, 1ms ticks, sensor I/O, actuator  │
│  control, safety enforcement. Operates independently.        │
└─────────────────────────────────────────────────────────────┘
```

**Critical design principle**: Each tier operates independently. Tier 1 maintains safe control even when tiers 2 and 3 are completely unreachable.

---

## THE 32 OPCODES (EXISTING VM)

Stack machine. 8-byte fixed instructions. 256-entry stack. Float32-only arithmetic.

| Category | Opcodes |
|----------|---------|
| Stack | NOP (0x00), PUSH (0x01), POP (0x02), DUP (0x03), SWAP (0x04), ROT (0x05) |
| Arithmetic | ADD (0x06), SUB (0x07), MUL (0x08), DIV (0x09), CLAMP_F (0x0A) |
| Comparison | LT (0x0B), LTE (0x0C), EQ (0x0D), GT (0x0E), GTE (0x0F) |
| Control | JUMP (0x10), JUMP_IF_LT (0x11), JUMP_IF_GTE (0x12), CALL (0x13), RETURN (0x14), HALT (0x15) |
| I/O | LOAD_VAR (0x16), STORE_VAR (0x17), LOAD_SENSOR (0x18), STORE_ACTUATOR (0x19) |
| System | SYSCALL (0x1A), READ_PIN (0x1B), WRITE_PIN (0x1C) |

**Spec**: `specs/firmware/reflex_bytecode_vm_spec.md` (2,487 lines)

---

## WIRE PROTOCOL (JETSON ↔ ESP32)

RS-422, 921,600 baud, COBS framing, CRC-16/CCITT-FALSE, 28 message types.

Key messages: HEARTBEAT (0x01), REFLEX_DEPLOY (0x05), SENSOR_TELEMETRY (0x08), COMMAND_SET_MODE (0x0C), ACTUATOR_FEEDBACK (0x0E), FIRMWARE_CHUNK (0x42).

**Spec**: `specs/protocol/wire_protocol_spec.md` (1,047 lines)

---

## FOUR-TIER SAFETY (NON-NEGOTIABLE)

1. **Hardware**: Kill switch (mechanical MOSFET, 0.93ms response), pull-down resistors on all actuators, current sensing (INA219)
2. **Firmware**: ISR guard (interrupt-level safety check), hardware watchdog (MAX6818, 0x55/0xAA pattern), software watchdog (FreeRTOS)
3. **Supervisory**: FreeRTOS task monitoring heartbeat, safety state machine (NORMAL→DEGRADED→SAFE_STATE→FAULT)
4. **Application**: Trust-score-gated autonomy (L0-L5), per-reflex safety validation, kill-switch availability check

**Spec**: `specs/safety/safety_system_spec.md` (1,296 lines)

---

## INCREMENTS TRUST ALGORITHM

12 parameters. 6 autonomy levels. 25:1 loss-to-gain ratio.

**Key parameters**: `alpha_gain` (0.002 per good window), `alpha_loss` (0.05 per bad window), `t_floor` (0.10), `t_max` (0.99), `window_seconds` (3600)

**Trust dynamics**: Gain time constant τ_g ≈ 658 windows (27.4 days). Loss time constant τ_l ≈ 29 windows (1.2 days). 22× faster to lose trust than gain it. This is intentional — it prevents overtrust.

**Autonomy levels**: L0 (Manual) → L1 (Advisory) → L2 (Assisted) → L3 (Supervised) → L4 (Autonomous) → L5 (Full). Takes 45 days ideal to reach L4. Takes 83 days ideal to reach L5.

**Per-subsystem independence**: Steering trust is independent of engine trust. One subsystem failure doesn't cascade. 5 independent trust scores per vessel.

**Spec**: `specs/safety/trust_score_algorithm_spec.md` (2,414 lines)

---

## LEARNING PIPELINE

Observe → Record → Discover Patterns → Synthesize Reflex → A/B Test → Deploy

5 pattern discovery algorithms: cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference.

**AI model**: Qwen2.5-Coder-7B at Q4_K_M (4.2GB VRAM, 17.2 tok/s on Jetson). 89.6% HumanEval, 96% schema compliance, 82% semantic correctness.

**Validation**: Self-validation misses 29.4% of safety issues. Separate Claude 3.5 Sonnet validation catches 95.1%.

**Spec**: `specs/jetson/learning_pipeline_spec.md` (2,140 lines)

---

## A2A-NATIVE PROGRAMMING PARADIGM

This is the frontier. The existing system has humans in the loop at multiple points. The A2A-native paradigm removes humans from the code path entirely:

### The Three Pillars
1. **System Prompt = Compiler**: An LLM's system prompt becomes the compilation pipeline. It translates intentions to bytecode, enforces safety constraints, optimizes for the target hardware.
2. **Equipment = Runtime**: The execution environment between bytecode and metal. The VM, the OS, the drivers, the sensor I/O system.
3. **Vessel = Hardware**: The physical platform. Its capabilities define what bytecode can accomplish. The vessel capability descriptor tells agents what they have to work with.

### Agent-Annotated Bytecode (AAB)
Extended bytecode format: 8-byte core instruction + variable-length TLV metadata trailer. Agents read the metadata (intent, capability requirements, safety constraints, trust implications). ESP32 receives only the stripped 8-byte core. Zero execution overhead.

### 29 Proposed New Opcodes
- **Intent** (0x20-0x26): DECLARE_INTENT, ASSERT_GOAL, VERIFY_OUTCOME, EXPLAIN_FAILURE
- **Agent Communication** (0x30-0x34): TELL, ASK, DELEGATE, REPORT_STATUS, REQUEST_OVERRIDE
- **Capability Negotiation** (0x40-0x44): REQUIRE_CAPABILITY, DECLARE_SENSOR_NEED, DECLARE_ACTUATOR_USE
- **Safety Augmentation** (0x50-0x56): TRUST_CHECK, AUTONOMY_LEVEL_ASSERT, SAFE_BOUNDARY, RATE_LIMIT

All new opcodes are NOP on existing ESP32 VM. Zero firmware changes required for backward compatibility.

### The 0.5× Trust Rule
Agent-generated bytecode earns trust at HALF the rate of human-authored code. This compensates for the reduced human intuition about what the code "actually does."

### Research: `a2a-native-language/` (6 documents, 45,191 words)

---

## MARINE REFERENCE DOMAIN

NEXUS's reference implementation is a marine autonomous vessel. Everything is designed to this domain first, then generalized.

**Regulations**: COLREGs (72 rules encoded in safety_policy.json), SOLAS, IMO MASS Code
**Navigation**: GPS/GNSS, INS, radar, AIS, ECDIS, depth sounder
**Environmental sensing**: Wind (speed, direction, gusts), waves, current, temperature
**Communication**: VHF, AIS, cellular, Starlink satellite, RS-422 (inter-board)
**Trust advancement sequence**: bilge → lighting → anchor → throttle → autopilot → navigation → fishing → fleet

---

## EIGHT TARGET DOMAINS

Marine (reference), Agriculture, Factory Automation, Mining, HVAC, Home Automation, Healthcare Robotics, Autonomous Ground Vehicles.

~80% of the architecture is domain-agnostic. ~20% is domain-specific (sensors, actuators, regulations, trust parameters). Trust α_gain/α_loss ratio varies 150× across domains (1.3:1 for home to 200:1 for healthcare).

**Research**: `knowledge-base/domains/marine_autonomous_systems.md`, `dissertation/round2_research/cross_domain_analysis.md`

---

## CROSS-CULTURAL PHILOSOPHICAL FOUNDATION

NEXUS's design was analyzed through 8 cultural lenses:
- **Western Analytic**: Four causes → NEXUS component mapping
- **Daoist**: Wu wei → reflex execution without deliberation
- **Confucian**: Hierarchy → three-tier architecture, ritual → wire protocol
- **Soviet Engineering**: Dialectical materialism → evolutionary optimization, Korolev triple redundancy
- **African Ubuntu**: "I am because we are" → relational ontology, communal veto
- **Indigenous**: Seven generations thinking → long-term system design
- **Japanese**: Kaizen → continuous improvement, wabi-sabi → embracing imperfection (trust score)
- **Islamic Golden Age**: Tawhid → unified knowledge base, ijtihad → pattern discovery

Five universal themes emerged with 7-8/8 consensus:
1. Intelligence is relational, not atomic
2. Purpose must be earned, not declared
3. Constraints enable rather than restrict
4. Knowledge must include narrative context
5. Balance requires oscillillation, not static equilibrium

**Research**: `dissertation/round3_research/eight_lenses_analysis.md`, `knowledge-base/philosophy/`

---

## KNOWLEDGE BASE MAP

27 Wikipedia-grade articles (333,775 words) in `knowledge-base/`:

### If you need to understand HISTORY:
- `foundations/history_of_programming_languages.md` — 8 eras, why stack machines, what makes NEXUS different
- `foundations/evolution_of_virtual_machines.md` — P-code, JVM, Lua, WASM, eBPF, agent-interpretable VMs
- `foundations/cross_cultural_computing.md` — 7 civilizations, non-Western contributions
- `domains/maritime_navigation_history.md` — Polynesians to GPS

### If you need to understand MATH and THEORY:
- `theory/type_systems_and_formal_languages.md` — Chomsky hierarchy, type systems, bytecode verification
- `theory/formal_verification_and_safety.md` — All 8 safety standards, model checking, proof-carrying code
- `theory/evolutionary_computation.md` — GA/GP/ES/DE, bytecode as genotype
- `theory/program_synthesis_and_ai_codegen.md` — How LLMs generate code, constrained generation

### If you need to understand PEOPLE and PHILOSOPHY:
- `philosophy/philosophy_of_ai_and_consciousness.md` — Hard problem, alignment, AGI, phenomenology
- `philosophy/trust_psychology_and_automation.md` — Lee & See, trust calibration, INCREMENTS mapping
- `philosophy/post_coding_paradigms.md` — The post-coding age, L0-L5 coding autonomy

### If you need to understand HARDWARE and SYSTEMS:
- `systems/embedded_and_realtime_systems.md` — ESP32-S3 and Jetson deep dives
- `systems/edge_ai_encyclopedia.md` — 18-chip comparison, quantization, NEXUS AI stack
- `systems/hardware_software_codesign.md` — Co-design, BOM ($684), power/thermal
- `systems/distributed_systems.md` — CAP theorem, consensus, fleet architecture
- `systems/robotics_control_history.md` — PID to MPC, ROS vs NEXUS

### If you need to LOOK SOMETHING UP:
- `reference/nexus_glossary.md` — 310 terms
- `reference/annotated_bibliography.md` — 178 references
- `reference/open_problems_catalog.md` — 29 unsolved problems
- `reference/agent_frameworks_comparison.md` — 15 frameworks × 20 dimensions
- `reference/autonomous_systems_law.md` — UNCLOS, EU AI Act, GDPR, liability

### If you are a NEW DEVELOPER:
- `developer-guide/onboarding_guide.md` — 12-section onboarding, 20 essential documents

### If you are a RESEARCH AGENT (start here):
- `onboarding/research/context-map.md` — Complete project genome, document atlas, research topology
- `onboarding/research/research-frontiers.md` — 29 expanded problems + 10 frontier directions
- `onboarding/research/methodology.md` — How to do research on this project
- `onboarding/research/expansion-guide.md` — 15 thread deep-dives, 10-agent assignment plan

### If you are an A2A BUILDER AGENT (start here):
- `onboarding/user-education/gamified-intro.md` — "What if code wasn't written for you?"
- `onboarding/user-education/concept-playground.md` — Bytecode Kitchen, Trust River, Agent Theater
- `onboarding/user-education/builder-education.md` — 8 modules, toolkit, 10 exercises
- `onboarding/user-education/architecture-patterns.md` — 25 composable patterns
- `onboarding/user-education/use-case-scenarios.md` — 10 A2A use cases

### If you are a HUMAN who needs context:
- `human-readable/project-overview.md` — Plain-language overview
- `human-readable/simplest-system-tomorrow.md` — 7-day MVP build guide
- `human-readable/progression-path.md` — Phase 0→5 roadmap with budgets

---

## DISSERTATION RESEARCH (5 ROUNDS)

In `dissertation/`:
- **Round 1** (Technical Foundations): Safety Monte Carlo simulation, trust score evolution simulation, VM benchmarking, wire protocol analysis
- **Round 2** (Domain & Regulatory): Cross-domain analysis (8 domains), regulatory landscape (IEC 61508, EU AI Act, GDPR), AI model analysis
- **Round 3** (Philosophy & Ethics): Eight cultural lenses, ethical framework, cross-cultural design principles
- **Round 4** (Simulations): End-to-end system analysis, multi-reflex deployment, network architecture
- **Round 5** (Synthesis): Universal synthesis across all rounds

---

## REPOSITORY STRUCTURE

```
Edge-Native/
├── claude.md                          ← YOU ARE HERE
├── README.md                          ← Project overview
├── specs/                             ← PRODUCTION SPECIFICATIONS (read these for engineering)
│   ├── 00_MASTER_INDEX.md             ← Start here for specs
│   ├── firmware/reflex_bytecode_vm_spec.md      ← 32-opcode VM (2,487 lines)
│   ├── protocol/wire_protocol_spec.md           ← RS-422, COBS, 28 msgs (1,047 lines)
│   ├── safety/safety_system_spec.md             ← 4-tier safety (1,296 lines)
│   ├── safety/trust_score_algorithm_spec.md     ← INCREMENTS (2,414 lines)
│   ├── safety/safety_policy.json                ← 10 global + domain rules (864 lines)
│   ├── jetson/learning_pipeline_spec.md         ← Observe→Deploy (2,140 lines)
│   ├── jetson/cluster_api.proto                 ← gRPC fleet API
│   ├── jetson/mqtt_topics.json                  ← MQTT topic hierarchy
│   └── firmware/memory_map_and_partitions.md    ← ESP32 memory layout
├── knowledge-base/                     ← ENCYCLOPEDIA (27 articles, 333K words)
│   ├── README.md                        ← Knowledge base index
│   ├── foundations/                     ← History, VMs, biology, culture, paradigms
│   ├── theory/                          ← Agents, evolution, verification, types, synthesis
│   ├── philosophy/                      ← AI consciousness, trust psychology, post-coding
│   ├── systems/                         ← Embedded, distributed, robotics, edge AI, HW/SW
│   ├── domains/                         ← Marine systems, maritime navigation
│   ├── reference/                       ← Glossary (310), bibliography (178), law, problems
│   └── developer-guide/                 ← Onboarding guide
├── a2a-native-language/                ← A2A RESEARCH (6 docs, 45K words)
│   ├── language_design_and_semantics.md          ← AAB format, 29 opcodes, formal proofs
│   ├── assembly_mapping_and_hardware_bridge.md   ← Xtensa/ARM64 mapping
│   ├── nexus_integration_analysis.md             ← Backward compat, 12 wire extensions
│   ├── agent_communication_and_runtime_model.md  ← Equipment, vessel, 5 scenarios
│   ├── cross_domain_a2a_applicability.md        ← 8-domain A2A analysis
│   └── final_synthesis.md                       ← Grand thesis, 36-month roadmap
├── a2a-native-specs/                  ← A2A-NATIVE TWIN DOCS (Rosetta stone)
│   └── [see README.md in this directory]
├── onboarding/                        ← ONBOARDING (research + user education)
│   ├── research/                      ← Agent research context (~45K words)
│   │   ├── context-map.md             ← Project genome, document atlas, research topology
│   │   ├── research-frontiers.md      ← 29 problems + 10 frontier directions
│   │   ├── methodology.md             ← How to do research on this project
│   │   └── expansion-guide.md         ← 15 thread deep-dives, 10-agent assignment plan
│   └── user-education/                ← A2A builder education (~79K words)
│       ├── gamified-intro.md          ← "What if code wasn't written for you?"
│       ├── concept-playground.md      ← Bytecode Kitchen, Trust River, Agent Theater
│       ├── builder-education.md       ← 8 modules, toolkit, 10 exercises, 15 anti-patterns
│       ├── architecture-patterns.md   ← 25 patterns across 5 categories
│       └── use-case-scenarios.md      ← 10 A2A use cases across diverse domains
├── human-readable/                    ← PLAIN-LANGUAGE SUMMARIES (~27K words)
│   ├── project-overview.md            ← Accessible overview for non-technical readers
│   ├── simplest-system-tomorrow.md    ← 7-day MVP build guide with BOM
│   └── progression-path.md            ← Phase 0→5 roadmap, risk, philosophical arc
├── worksheets-logs/                   ← ITERATION WORKSHEETS AND AGENT WORKLOGS
├── dissertation/                      ← 5-ROUND RESEARCH DISSERTATION
├── framework/                         ← Core framework design documents
├── autopilot/                         ← ESP32 autopilot engineering
├── genesis-colony/                    ← Philosophical/architectural explorations
├── vessel-platform/                   ← Marine vessel platform
├── addenda/                           ← Engineering addenda (pitfalls, checklists)
├── schemas/                           ← JSON schemas
└── v31-docs/                          ← v3.1 documentation
```

---

## KEY DESIGN DECISIONS (AND WHY)

| Decision | Why |
|----------|-----|
| Stack machine (not register) | Simpler verification, deterministic execution, smaller instructions, proven by Forth/JVM/WASM |
| Float32-only arithmetic | Avoids integer overflow bugs, NaN/Inf protection via CLAMP_F, sufficient precision for sensor/actuator |
| 8-byte fixed instructions | Cache-line aligned on Xtensa, trivially parseable, no variable-length complexity |
| RS-422 (not CAN/WiFi) | Deterministic latency, point-to-point reliability, EMI resistance for marine, simpler than CAN |
| COBS framing | Zero-overhead delimiting, 0.4% worst-case overhead, no escape characters |
| 25:1 loss-to-gain ratio | Prevents overtrust: takes 27 days to build, 1.2 days to lose. Humans overtrust automation — this is the fix. |
| ESP32-S3 (not STM32/RP2040) | Best price/performance/IO for reflex layer. WiFi/BLE for future, dual-core, 8MB PSRAM |
| Jetson Orin Nano (not Jetson Nano) | 40 TOPS is minimum for 7B model inference. 8GB LPDDR5 for Q4_K_M quantized model. |
| Qwen2.5-Coder-7B (not GPT-4/other) | Best edge code generation: 89.6% HumanEval, fits in 4.2GB at Q4_K_M, open weights |
| Agent-generated code at 0.5× trust | Compensates for reduced human intuition. Safety first. |

---

## WHAT'S BUILT vs WHAT NEEDS BUILDING

### Built (Specifications + Research):
- ✅ Complete specification suite (10,386 lines of production specs)
- ✅ A2A-native Rosetta Stone specs (7 twin specifications + rosetta stone)
- ✅ 5-round dissertation research (30+ research documents)
- ✅ 27-article knowledge base encyclopedia (333,775 words)
- ✅ A2A-native language research (45,191 words)
- ✅ Research onboarding suite (4 docs, ~45,100 words)
- ✅ A2A builder education suite (5 docs, ~78,500 words)
- ✅ Human-readable summaries (3 docs, ~26,800 words)
- ✅ Monte Carlo safety simulations
- ✅ Trust score evolution simulations
- ✅ VM performance benchmarks

### Needs Building (The Actual System):
- 🔲 ESP32 firmware: VM interpreter, wire protocol, I/O drivers, safety monitors
- 🔲 Jetson software: LLM inference pipeline, reflex compiler (JSON→bytecode), MQTT bridge, learning pipeline
- 🔲 Cloud services: Fleet management, heavy training, simulation
- 🔲 A2A-native language implementation: The hybrid compiler/interpreter
- 🔲 Safety validation: HIL testing, certification evidence collection
- 🔲 Hardware: Reference vessel PCB design, wiring, integration

### Estimated Build: 12-16 weeks (3 developers, parallel), 8 weeks to first demo

---

## THE OPEN PROBLEMS (WHAT TO THINK DEEPLY ABOUT)

The 6 CRITICAL unsolved problems (from `knowledge-base/reference/open_problems_catalog.md`):

1. **The Certification Paradox**: How do you certify software that rewrites itself? Static standards (IEC 61508) vs dynamic, evolving bytecode.

2. **Agent Cross-Validation Reliability**: Agent A validates Agent B's bytecode. How reliable is this? Self-validation misses 29.4% of safety issues.

3. **The Alignment-Utility Gap**: The trust score measures SAFETY (no bad events). It does not measure UTILITY (does the system do useful things?). A perfectly safe system that does nothing passes all trust checks.

4. **Adversarial Bytecode**: Can an agent craft bytecode that passes validation but violates safety? This is the AI equivalent of a compiler exploit.

5. **Responsibility at L5**: When a fully autonomous vessel causes harm, who is responsible? The fleet operator? The NEXUS developers? The AI agent? There is no legal precedent.

6. **The Black Box Provenance Problem**: Can you trace WHY an LLM agent generated a specific bytecode sequence? The reasoning is opaque. For certification, you need provenance.

---

## THE A2A-NATIVE ROSETTA STONE

The `a2a-native-specs/` directory contains the A2A-native "twin" of every core specification. This is the bridge between human-readable engineering specs and agent-interpretable language design.

The eventual implementation sits between a **compiler** and an **interpreter**:
- **Compiler-like**: Takes high-level intentions and produces optimized bytecode for a specific target (vessel)
- **Interpreter-like**: The bytecode carries semantic metadata that any agent can interpret, understand, and validate
- **Swarm-native**: Ground truth connects directly to application function. The system is a child of a larger swarm of nodes. Bytecode is the lingua franca.

The key insight: when you have a rock-solid marine all-in-one system with rock-solid engineering, and you can express that same system in an A2A-native language where agents can read, understand, modify, and improve it directly — you get a system that evolves at the speed of agent cognition, not the speed of human engineering cycles.

---

## CODING CONVENTIONS FOR THIS PROJECT

1. **Safety is non-negotiable**. Every code change must preserve four-tier safety invariants.
2. **The VM is the interface**. All control logic flows through the bytecode VM. No direct hardware access from higher tiers.
3. **Float32 everywhere** on the ESP32. No integer arithmetic for control values.
4. **Trust score gates everything**. Code doesn't deploy without sufficient trust. Period.
5. **Specs are the source of truth**. If code disagrees with specs, the specs win. File an issue and update the code.
6. **A2A-native extensions are backward compatible**. New opcodes (0x20+) are NOP on existing firmware.
7. **Zero-heap on ESP32**. All memory is statically allocated. No malloc/free in production firmware.
8. **Determinism is required**. Same inputs → same outputs in same number of cycles. Always.
9. **Cross-reference everything**. Use `[[wiki-links]]` in documentation. Keep the knowledge graph connected.
10. **Write for the next generation**. Every document should be self-contained enough that a developer who has never seen this project can understand it.
