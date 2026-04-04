# NEXUS Developer Onboarding Guide

**The Definitive Guide for New Developers**

> *"No human writes, reads, or debugs code."* — NEXUS Platform Motto

---

## Table of Contents

1. [Welcome to NEXUS — The Big Picture](#1-welcome-to-nexus--the-big-picture)
2. [Repository Tour](#2-repository-tour)
3. [The Architecture Deep Dive](#3-the-architecture-deep-dive)
4. [Hardware You Need to Know](#4-hardware-you-need-to-know)
5. [The A2A-Native Programming Paradigm](#5-the-a2a-native-programming-paradigm)
6. [Safety — The Non-Negotiable Foundation](#6-safety--the-non-negotiable-foundation)
7. [How to Read the Specifications](#7-how-to-read-the-specifications)
8. [Coding Standards for NEXUS](#8-coding-standards-for-nexus)
9. [Testing and Validation](#9-testing-and-validation)
10. [Knowledge Base Map](#10-knowledge-base-map)
11. [The Road Ahead](#11-the-road-ahead)
12. [Essential Reading Order](#12-essential-reading-order)

---

## 1. Welcome to NEXUS — The Big Picture

### What is NEXUS? (The One-Page Summary)

NEXUS is a **production-ready specification for a distributed intelligence system** designed for general-purpose industrial robotics. It is not a single application, framework, or library — it is a complete system architecture that spans three hardware tiers, a custom bytecode virtual machine, a wire protocol, a safety system with defense-in-depth, a trust-based autonomy framework, and an AI-driven learning pipeline.

The radical premise of NEXUS: **no human writes, reads, or debugs code.** Instead, operators wire hardware, describe intent in natural language, demonstrate desired behaviors, and approve or reject AI-generated proposals. The system learns from observation, synthesizes reflexes, validates them through A/B testing, and progressively earns trust to operate with increasing autonomy.

If you join this project, you will not be writing application code in the traditional sense. You will be building the infrastructure that allows AI agents to safely generate, deploy, and evolve control programs for physical robots. This is infrastructure for the Post-Coding Age.

### "The Ribosome, Not the Brain"

This is the defining metaphor of the entire NEXUS architecture, and you must internalize it before writing a single line of code.

The brain plans, reasons, and strategizes. The ribosome translates — mechanically, without understanding, converting mRNA sequences into protein chains. The ribosome does not know what it is building. It does not need to know. The evolutionary process that produced the mRNA blueprint already validated it.

In NEXUS terms:
- **The Brain** = the Jetson Orin Nano (AI inference, NLP, pattern discovery, reflex compilation)
- **The Ribosome** = the ESP32-S3 running the Reflex Bytecode VM (fetch-decode-execute, sensor polling, actuator commands)

The ribosome (ESP32 VM) does not understand the control strategy encoded in the bytecode. It fetches the next 8-byte instruction, decodes the opcode and operands, and executes the operation on the stack. Understanding is not required. Translation is sufficient.

The bytecode running on an ESP32 after 847 generations of evolution has been shaped by real-world performance data. It works not because the VM understands it, but because the evolutionary process that produced it has already demonstrated its fitness.

**Why this matters for you as a developer:** The VM you build must be a perfect, dumb translator — fast, deterministic, and safe. Do not add intelligence to the ribosome. The intelligence lives on the Jetson. The VM must execute with zero surprises.

### The Post-Coding Age

Every programming language in history was designed for human programmers. Python optimizes for readability. Rust optimizes for safety. C optimizes for control. But when the primary programmer is an AI agent, the assumptions behind all these languages collapse. Agents do not need readable syntax — they need verifiable, deterministic bytecode. They do not need helpful error messages — they need trust metrics. They do not need IDEs — they need formal specifications.

NEXUS is designed for a world where agents are first-class programmers. This changes everything:

- **Code does not need to be human-readable.** Bytecode is the right abstraction level.
- **Code must be verifiable by machines.** The validator catches what humans miss.
- **Code must carry its own provenance.** Agent-Annotated Bytecode (AAB) attaches metadata describing why each instruction exists.
- **Code must earn trust.** The INCREMENTS framework means every reflex starts at zero trust and must prove itself through safe operation.

### The Three-Tier Architecture in Plain Language

NEXUS distributes intelligence across three hardware tiers, each operating independently:

| Tier | Hardware | What It Does | Latency |
|------|----------|--------------|---------|
| **1 — Reflex** | ESP32-S3 MCU | Real-time sensor polling, bytecode execution, safety enforcement | 10µs – 1ms |
| **2 — Cognitive** | NVIDIA Jetson Orin Nano | AI inference, NLP chat, pattern discovery, reflex compilation | 10 – 500ms |
| **3 — Cloud** | Starlink / 5G | Heavy training, simulation, fleet management | seconds – hours |

**Tier 1 is the ribosome.** It runs the show in real time. It polls sensors at up to 1 kHz, executes compiled bytecode, and enforces safety constraints. If everything above it fails, Tier 1 keeps the vessel safe.

**Tier 2 is the brain.** It observes telemetry from Tier 1, discovers patterns in the data, generates new reflex programs (bytecode), and deploys them to Tier 1 nodes for A/B testing. It also handles natural language interaction with operators.

**Tier 3 is the library.** It stores fleet-wide knowledge, runs heavy training simulations, and manages deployments across multiple vessels.

Each tier operates independently. Tier 1 maintains control even when all higher tiers fail. This is not optional — it is a constitutional requirement of the architecture.

### Key Numbers Every Developer Must Know

| Metric | Value | Why It Matters |
|--------|-------|----------------|
| **32 opcodes** | The complete VM instruction set | Small enough for single-pass verification, expressive enough for any control pattern |
| **28 message types** | Wire protocol message vocabulary | Defines all communication between nodes and tiers |
| **6 trust levels** | INCREMENTS L0 through L5 | Every subsystem starts at L0 and must earn its way up |
| **8 domains** | Marine, agriculture, HVAC, factory, mining, aerospace, healthcare, home | 80% of the codebase is domain-agnostic |
| **8-byte instructions** | Fixed-width bytecode format | Enables direct indexing, worst-case timing analysis |
| **256-entry stack** | VM stack depth limit | 98% headroom (max observed depth: 4) |
| **10,000 cycles** | Per-tick execution budget | Hard guarantee against infinite loops |
| **921,600 baud** | Default serial link speed | Supports 80 telemetry messages/second |
| **25:1 ratio** | Trust loss-to-gain ratio | Trust is lost 25x faster than it is gained |
| **4 tiers** | Safety defense-in-depth | Hardware → firmware ISR → supervisory task → application |
| **5,280 bytes** | Total VM memory budget | Fits within ESP32-S3 SRAM constraints |
| **12 parameters** | Trust score configuration | Fully tunable per subsystem and domain |

---

## 2. Repository Tour

### Directory Structure Explained

The repository is organized into several major directories, each with a distinct purpose:

```
Edge-Native/
├── specs/                   # Phase 1 production specifications (START HERE)
│   ├── 00_MASTER_INDEX.md   # Index of all 21 specification files
│   ├── protocol/            # Wire protocol, message payloads
│   ├── safety/              # Safety system, trust scores, safety policy
│   ├── firmware/            # Bytecode VM, I/O drivers, memory map
│   ├── jetson/              # Learning pipeline, MQTT, cluster API
│   └── ports/               # Hardware compatibility matrix
├── dissertation/            # 5-round iterative research dissertation
│   ├── round1_research/     # Deep technical foundations
│   ├── round2_research/     # Cross-domain & regulatory analysis
│   ├── round3_research/     # Philosophical, ethical, cultural perspectives
│   ├── round4_simulations/  # Monte Carlo & adversarial simulations
│   └── round5_synthesis/    # Universal synthesis
├── knowledge-base/          # Encyclopedia-grade reference articles
│   ├── foundations/         # History and theory (5 articles)
│   ├── theory/              # Mathematical/computational foundations (6 articles)
│   ├── philosophy/          # The "why" behind design decisions (2 articles)
│   ├── systems/             # Hardware and software architecture (3 articles)
│   ├── domains/             # Application-specific knowledge (1 article)
│   ├── developer-guide/     # THIS FILE — you are here
│   └── reference/           # Glossary, bibliography (planned)
├── a2a-native-language/     # A2A programming research (45K words, 6 documents)
├── framework/               # Core framework design documents
├── vessel-platform/         # Marine vessel platform architecture
├── autopilot/               # ESP32 autopilot engineering & simulations
├── docs/                    # Reports, presentations, overviews
├── schemas/                 # JSON schemas for configuration
├── addenda/                 # Engineering addenda (pitfalls, checklists, playbooks)
└── archives/                # Complete project zip archives
```

### Where to Find Specifications

The `specs/` directory is your primary reference for all production specifications. These are the documents that define how the system must work. Start with `specs/00_MASTER_INDEX.md` which provides an index of all 21 specification files.

The key specification files you will reference constantly:

1. **`specs/firmware/reflex_bytecode_vm_spec.md`** — The 32-opcode VM. This is the heart of Tier 1.
2. **`specs/protocol/wire_protocol_spec.md`** — The RS-422 serial protocol with COBS framing, CRC-16, and 28 message types.
3. **`specs/safety/safety_system_spec.md`** — The four-tier safety architecture.
4. **`specs/safety/trust_score_algorithm_spec.md`** — The INCREMENTS trust score with all 12 parameters.
5. **`specs/safety/safety_policy.json`** — Runtime safety rules (SR-001 through SR-010).
6. **`specs/firmware/memory_map_and_partitions.md`** — ESP32-S3 memory layout.
7. **`specs/ARCHITECTURE_DECISION_RECORDS.md`** — 28 ADRs explaining why decisions were made.
8. **`specs/jetson/learning_pipeline_spec.md`** — The observe→discover→synthesize→test→deploy cycle.

### Where to Find Research

The `dissertation/` directory contains five rounds of iterative research, each building on the previous:

- **Round 1** — Deep technical foundations: VM benchmarking, safety Monte Carlo simulations, trust score modeling. Includes Python simulation scripts and figures.
- **Round 2** — Cross-domain analysis across 8 target domains, regulatory landscape (IEC 61508, EU AI Act, GDPR), AI model stack analysis.
- **Round 3** — Multi-cultural philosophical analysis through 8 civilizational lenses (Western Analytic, Daoist, Confucian, Soviet Engineering, African Ubuntu, Indigenous, Japanese, Islamic Golden Age).
- **Round 4** — Monte Carlo simulations and adversarial testing.
- **Round 5** — Universal synthesis across all research dimensions.

The `a2a-native-language/` directory contains 6 research documents (45,191 words total) covering the A2A-native programming paradigm.

### How to Navigate the Knowledge Base

The `knowledge-base/` directory contains encyclopedia-grade reference articles organized by category:

| Category | Directory | Contents | Purpose |
|----------|-----------|----------|---------|
| **Foundations** | `foundations/` | History of programming languages, evolution of VMs, programming paradigms, biological computation, cross-cultural computing | Understand *why* NEXUS is designed the way it is |
| **Theory** | `theory/` | Type systems, formal verification, evolutionary computation, agent communication, program synthesis, self-organizing systems | Mathematical and computational foundations |
| **Philosophy** | `philosophy/` | Trust psychology, philosophy of AI and consciousness | The "why" behind design decisions |
| **Systems** | `systems/` | Embedded/real-time systems, robotics control history, distributed systems | Hardware and software architecture |
| **Domains** | `domains/` | Marine autonomous systems (more planned) | Application-specific knowledge |

These articles are cross-referenced using `[[wiki-link]]` syntax. When you see `[[reflex_bytecode_vm_spec]]`, it refers to the VM specification.

### Key Files Every Developer Must Read (Top 10)

If you read nothing else, read these ten files in this order:

1. **`README.md`** — The project overview (you've already started here)
2. **`specs/00_MASTER_INDEX.md`** — The specification roadmap
3. **`specs/firmware/reflex_bytecode_vm_spec.md`** — The VM that everything depends on
4. **`specs/protocol/wire_protocol_spec.md`** — How nodes talk to each other
5. **`specs/safety/safety_system_spec.md`** — The four-tier safety architecture
6. **`specs/safety/trust_score_algorithm_spec.md`** — How autonomy is earned
7. **`specs/safety/safety_policy.json`** — Runtime safety rules
8. **`specs/ARCHITECTURE_DECISION_RECORDS.md`** — Why decisions were made
9. **`specs/firmware/memory_map_and_partitions.md`** — ESP32 memory constraints
10. **`specs/jetson/learning_pipeline_spec.md`** — How the system learns

---

## 3. The Architecture Deep Dive

### Three-Tier: Cloud → Jetson → ESP32 — What Each Does

#### Tier 1: Reflex (ESP32-S3)

The ESP32-S3 is the workhorse of the NEXUS architecture. Each ESP32 node runs a complete firmware stack:

- **FreeRTOS kernel** with 6 tasks at fixed priorities
- **Reflex Bytecode VM** — the 32-opcode stack machine that executes control programs
- **Safety system** — four-tier defense with hardware kill switch, watchdog timer, supervisory task, and application-level checks
- **Serial protocol handler** — COBS decoding, CRC-16 verification, message dispatch
- **I/O subsystem** — sensor polling (I2C, ADC, UART), actuator driving (PWM, GPIO, relay)

Tier 1 runs the show. At 1 kHz, it reads sensors, executes bytecode, writes actuators, checks safety constraints, and transmits telemetry — all within a 1ms tick. If Tier 2 and Tier 3 both fail simultaneously, Tier 1 keeps the vessel safe. This is not a design aspiration; it is a constitutional requirement.

A single NEXUS vessel may have 5-20 ESP32 nodes, each running independent reflex programs. The compass node runs a heading-hold reflex. The throttle node runs an engine management reflex. The bilge node runs a flooding-detection reflex. No node has a complete model of the vessel. Coordinated behavior emerges from the interaction of simple, locally-optimal reflex programs.

#### Tier 2: Cognitive (Jetson Orin Nano)

The Jetson Orin Nano Super ($249, 67 TOPS INT8, 8GB LPDDR5) is the brain of the system. Three Jetson units form a distributed AI cluster with dedicated model loading per node. The Jetson handles:

- **AI inference** — Qwen2.5-Coder-7B (quantized to Q4_K_M) generates reflex JSON from operator intent and telemetry patterns
- **Pattern discovery** — 5 algorithms: cross-correlation, BOCPD (change-point detection), HDBSCAN (behavioral clustering), temporal mining, Bayesian reward inference
- **Reflex compilation** — converts declarative JSON reflex definitions into imperative 8-byte bytecode instructions
- **A/B testing** — runs candidate reflexes alongside production reflexes, compares performance using Bayesian posterior analysis
- **Natural language interface** — operator chats with the system to describe intent, approve proposals, and query status
- **Telemetry aggregation** — receives data from all ESP32 nodes, identifies patterns, triggers learning cycles

The Jetson does NOT directly control actuators. It generates bytecode proposals and deploys them to ESP32 nodes via the wire protocol. The ESP32 validates and executes. This separation is the ribosome-brain distinction made concrete.

#### Tier 3: Cloud

The cloud tier handles workloads that are too heavy for edge computation:

- **Heavy model training** — fine-tuning LLMs on fleet-wide data
- **Simulation** — Monte Carlo safety simulations, adversarial testing
- **Fleet management** — cross-vessel knowledge transfer, pattern sharing
- **Long-term storage** — historical telemetry, evolutionary lineage tracking

Connectivity to the cloud is via Starlink or 5G. The system must function without cloud connectivity for extended periods (days to weeks).

### The Bytecode VM: 32 Opcodes, 8-Byte Instructions, Stack Machine

The Reflex Bytecode VM is the most important single component in the NEXUS architecture. It is the execution environment for all real-time control code. Every control program — PID controllers, state machines, threshold detectors, signal filters — runs as bytecode on this VM.

**Instruction Format:** Every instruction is exactly 8 bytes:

```
Byte 0:    Opcode (0x00–0x1F, 32 possible)
Byte 1:    Flags (bit 7: SYSCALL, bit 6: IMMEDIATE_F32, bits 0-5: reserved)
Byte 2:    Operand 1 (pin index, variable index, or jump offset high byte)
Byte 3:    Operand 2 (pin index, variable index, or jump offset low byte)
Bytes 4-7: Immediate value (int8, int16, float32, or unused — interpreted per opcode)
```

**Opcode Categories:**

| Category | Opcodes | Purpose |
|----------|---------|---------|
| Stack | `NOP`, `POP`, `DUP`, `SWAP` | Stack manipulation |
| Constants | `PUSH_I8`, `PUSH_I16`, `PUSH_F32` | Load literal values |
| Arithmetic | `ADD_F`, `SUB_F`, `MUL_F`, `DIV_F`, `NEG_F` | Float32 computation |
| Comparison | `EQ_F`, `LT_F`, `GT_F`, `LTE_F`, `GTE_F` | Comparison (produces 0 or 1) |
| Logic | `AND_F`, `OR_F`, `NOT_F` | Bitwise/logical operations |
| I/O | `READ_PIN`, `WRITE_PIN` | Sensor input, actuator output |
| Memory | `READ_VAR`, `WRITE_VAR` | Persistent variable storage (256 vars) |
| Control | `JUMP`, `JUMP_IF_TRUE`, `JUMP_IF_FALSE` | Conditional branching |
| System | `CLAMP_F`, `PID_COMPUTE`, `READ_TIMER_MS`, `SYSCALL` | Domain-specific operations |

**Key Properties:**
- **Stack-based** — no register allocation needed, simplifies compiler and verifier
- **Deterministic** — identical inputs produce identical outputs in identical cycle counts (proven as Theorem 4)
- **Bounded execution** — 10,000 cycle budget per tick prevents infinite loops
- **Type-safe** — no NaN or Infinity reaches actuators (proven as Theorem 3)
- **Verifiable** — single linear pass validates stack balance, jump targets, operand ranges, cycle budget

**Performance:** The VM adds only 1.2–1.3× overhead compared to hand-written C for arithmetic workloads. A typical PID controller uses 30 instructions and 368 cycles — 0.7% of the 50,000-cycle budget. The VM core fits in ~12KB of flash and ~3KB of SRAM.

### The Wire Protocol: COBS, CRC-16, RS-422, 28 Message Types

The NEXUS Wire Protocol defines how all nodes communicate over serial links. It is the nervous system of the architecture.

**Physical Layer — RS-422:**

RS-422 was chosen over CAN bus, Ethernet, and other alternatives for three reasons:

1. **Deterministic latency** — no CSMA/CD contention, no MAC-layer arbitration. Each message has a predictable worst-case delivery time.
2. **EMI resistance** — differential signaling provides robust noise immunity, critical for marine and industrial environments.
3. **Simplicity** — no IP stack, no routing tables, no driver complexity. Point-to-point serial links managed by a simple UART driver.

Default speed: 921,600 baud. Throughput: ~88 KB/s usable after framing overhead.

**Framing — COBS (Consistent Overhead Byte Stuffing):**

COBS encoding ensures that the `0x00` byte appears only as a frame delimiter. This is analogous to biological stop codons — reserved signals that unambiguously mark boundaries. Worst-case overhead: 0.4% per frame.

**Integrity — CRC-16/CCITT-FALSE:**

Every frame includes a CRC-16 checksum (polynomial 0x1021, initial value 0xFFFF). Undetected error rate: <10⁻¹⁰ under a bit error rate of 10⁻⁷. This is comparable to DNA's own error rate after repair mechanisms.

**Message Types — 28 Defined:**

| Category | Message Types | Examples |
|----------|---------------|---------|
| System | `HEARTBEAT`, `ROLE_ASSIGN`, `NODE_STATUS` | Node discovery and configuration |
| Reflex | `REFLEX_DEPLOY`, `REFLEX_QUERY`, `REFLEX_DELETE` | Bytecode lifecycle management |
| Telemetry | `TELEMETRY_REPORT`, `OBSERVATION_PUSH` | Sensor data and observation records |
| Safety | `SAFETY_EVENT`, `KILL_SWITCH_ACK`, `WATCHDOG_RESET` | Safety state transitions |
| Cognitive | `CHAT_REQUEST`, `CHAT_RESPONSE`, `PROPOSAL` | Agent-operator interaction |
| Firmware | `OTA_CHUNK`, `OTA_COMPLETE`, `OTA_VERIFY` | Over-the-air updates |

Each message type has a defined payload structure with field-level documentation in `specs/protocol/message_payloads.json`.

### The Safety System: Four-Tier Defense in Depth

Safety is the non-negotiable foundation of NEXUS. The system implements four independent safety tiers, each capable of bringing the vessel to a safe state independently:

**Tier 0 — Hardware Interlock (Fastest):**
- Physical NC (normally-closed) kill switch contact in series with actuator power
- Opens circuit on contact bounce: <100µs response time
- No software involved — this is a physical wire that, when broken, cuts power to all actuators
- Cannot be overridden by any software at any tier

**Tier 1 — Firmware Safety Guard (Fast):**
- Hardware watchdog timer (MAX6818) requires feeding every 200ms with 0x55/0xAA alternating pattern
- Safety ISRs at highest interrupt priority can preempt the VM and the protocol task
- Overcurrent detection per actuator channel
- Output clamping: post-execution verification that actuator values are within configured [min, max] ranges

**Tier 2 — Supervisory Task (Medium):**
- FreeRTOS task at priority 24 (highest application priority)
- Monitors heartbeat from Jetson (100ms interval, 500ms warning, 1000ms escalation)
- Monitors health of all other tasks (watchdog, VM, protocol, telemetry, I/O)
- Runs safety state machine: NORMAL → DEGRADED → SAFE_STATE → FAULT

**Tier 3 — Application Control (Slowest):**
- Normal application logic (reflex programs, telemetry, cognitive interaction)
- Operates within the constraints established by Tiers 0–2
- Can request safety state transitions but cannot prevent them

**Key principle:** Each tier operates independently. A failure in Tier 3 cannot prevent Tier 2 from escalating. A failure in Tier 2 cannot prevent Tier 1 from triggering. A failure in Tier 1 cannot prevent Tier 0 from cutting power.

### The Trust Score: INCREMENTS, 12 Parameters, 25:1 Ratio

The INCREMENTS framework defines six levels of autonomy (L0 through L5) per subsystem. Every subsystem starts at L0 (manual only) and must earn trust through demonstrated safe operation.

**The Trust Score Algorithm:**

The trust score T is a continuous value in [0, 1] updated every evaluation window. Three branches govern its evolution:

1. **Gain Branch** (good events): `T_new = T_prev + α_gain × quality × (1 - T_prev)`
   - Good events increase trust proportionally to quality, scaled by remaining headroom
   - Analogous to long-term potentiation (LTP) in neuroscience

2. **Penalty Branch** (bad events): `T_new = T_prev - α_loss × severity × T_prev`
   - Bad events decrease trust proportionally to severity, scaled by current trust
   - Analogous to long-term depression (LTD) in neuroscience

3. **Decay Branch** (inactivity): `T_new = T_prev + α_decay × (t_floor - T_prev)`
   - Inactivity causes slow decay toward the floor value (default 0.2)
   - Prevents the system from maintaining high trust without proving itself

**The 25:1 Ratio:**

The `α_loss` parameter (default 0.05) is 25 times larger than `α_gain` (default 0.002). This means trust is lost 25 times faster than it is gained. A single bad event at L4 drops trust by 3.5% immediately. Recovering that loss takes approximately 27 days of continuous good behavior.

**The 12 Parameters:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `α_gain` | 0.002 | Trust gain rate |
| `α_loss` | 0.05 | Trust loss rate |
| `α_decay` | 0.0001 | Inactivity decay rate |
| `t_floor` | 0.2 | Minimum trust value |
| `window_seconds` | 600 | Evaluation window (10 minutes) |
| `quality_max` | 1.0 | Maximum quality for gain events |
| `severity_max` | 1.0 | Maximum severity for penalty events |
| `streak_bonus` | 0.00005 | Bonus for consecutive clean windows |
| `candidate_threshold` | 0.05 | Minimum trust to receive proposals |
| `subsystem_weight` | varies | Per-subsystem risk multiplier |
| `α_multiplier` | varies | Domain-specific speed adjustment |
| `min_events_before_gain` | 5 | Events before trust can increase |

**The Six Levels:**

| Level | Trust Range | Capability |
|-------|-------------|------------|
| **L0** | T = 0 | Manual only. No autonomous actuation. |
| **L1** | 0 < T < 0.4 | Advisor. Suggests actions, requires approval. |
| **L2** | 0.4 ≤ T < 0.6 | Assistant. Executes approved actions with confirmation. |
| **L3** | 0.6 ≤ T < 0.8 | Collaborator. Executes within approved parameters. |
| **L4** | 0.8 ≤ T < 0.95 | Autonomous. Operates independently with monitoring. |
| **L5** | T ≥ 0.95 | Fully Autonomous. Minimal human oversight. |

### The Learning Pipeline: Observe → Discover → Synthesize → A/B Test → Deploy

The NEXUS learning pipeline is a five-stage process that continuously improves reflex programs based on real-world performance data:

**Stage 1 — Observe:**
- All ESP32 nodes collect sensor data at 10–100 Hz into a 72-field `UnifiedObservation` structure
- Data streams to the Jetson via the wire protocol (TELEMETRY_REPORT messages)
- Stored in a ring buffer on PSRAM (5.5 MB on each ESP32) and on Jetson SSD

**Stage 2 — Discover:**
- Five pattern discovery algorithms run on the Jetson:
  - **Cross-correlation** — identifies sensor-actuator relationships (e.g., "when wave height increases 0.3m, rudder corrections increase 15%")
  - **BOCPD** (Bayesian Online Change-Point Detection) — detects regime changes in sensor data
  - **HDBSCAN** — clusters behavior into modes (cruising, docking, rough weather, etc.)
  - **Temporal mining** — discovers event sequences and response patterns
  - **Bayesian reward inference** — estimates the operator's implicit reward function from demonstration data

**Stage 3 — Synthesize:**
- Qwen2.5-Coder-7B generates candidate reflex JSON from discovered patterns
- JSON is compiled to bytecode by the deterministic compiler
- Bytecode is validated by the VM verifier (stack balance, jump targets, cycle budget, NaN check)
- Claude 3.5 Sonnet (cloud) validates safety of the proposal (separate validation catches 29.4% more issues than self-validation)

**Stage 4 — A/B Test:**
- Candidate reflex runs alongside production reflex on the same node
- Performance compared using Bayesian posterior analysis
- 100% statistical power achieved at n=500 observations for 7% true lift
- If candidate outperforms production and passes safety checks → promotion

**Stage 5 — Deploy:**
- Hot-loaded to the ESP32 node via REFLEX_DEPLOY message over the wire protocol
- Bytecode swap occurs between ticks — the control loop never sees an inconsistent state
- Trust score for the subsystem begins tracking the new reflex's performance

---

## 4. Hardware You Need to Know

### ESP32-S3: The Reflex Tier

The ESP32-S3 (Espressif Systems, ~$6-10/unit) is the microcontroller that runs every Tier 1 node.

**Key Specifications:**
- **CPU:** Xtensa LX7 dual-core @ 240 MHz (no hardware FPU — software float emulation)
- **SRAM:** 512 KB internal
- **PSRAM:** 8 MB external (Octal SPI, ~80 MHz) — not DMA-capable, must copy via memcpy
- **Flash:** 4–32 MB external (QPI/OPI)
- **GPIO:** 45 pins (configurable as input, output, PWM, ADC)
- **I2C:** 2 buses @ 400 kHz Fast Mode
- **SPI:** 3 buses (FSPI, HSPI, VSPI)
- **UART:** 3 ports (debug, Jetson RS-422, GPS/NMEA)
- **ADC:** 2 × 12-bit SAR ADC (20 channels total)
- **CAN:** TWAI (CAN 2.0B)
- **USB:** OTG Full Speed
- **Wireless:** Wi-Fi 802.11 b/g/n + BLE 5.0 + ESP-NOW
- **Security:** Secure Boot v2 (RSA-3072), Flash Encryption (AES-256-XTS)
- **ULP Coprocessor:** RISC-V @ 17.5 MHz for always-on sensing

**Constraints You Must Respect:**

1. **No hardware FPU.** All float operations are software-emulated (~20-50 cycles per operation). This is acceptable for control loops but eliminates signal processing workloads.
2. **PSRAM is not DMA-capable.** All DMA transfers must use SRAM buffers with explicit memcpy to/from PSRAM. The observation data pipeline follows this pattern.
3. **No dynamic memory allocation at runtime.** All memory is statically allocated. The VM budget is 5,280 bytes total. No `malloc()` during execution.
4. **No garbage collection.** Zero heap allocation means zero GC pauses. This is a feature, not a bug — it guarantees deterministic timing.
5. **Core affinity is fixed.** Core 0 handles protocol/safety. Core 1 handles VM execution/I/O. Do not mix responsibilities across cores.

### Jetson Orin Nano: The Cognitive Tier

The Jetson Orin Nano Super ($249) is the AI inference platform.

**Key Specifications:**
- **GPU:** NVIDIA Ampere, 1024 CUDA cores, 32 Tensor cores
- **AI Performance:** 67 TOPS INT8
- **CPU:** 6-core ARM Cortex-A78AE
- **Memory:** 8 GB LPDDR5 (68 GB/s bandwidth)
- **Storage:** NVMe (via M.2 slot)
- **Power:** 7–25 W (configurable via DVFS)
- **Connectivity:** Gigabit Ethernet, USB 3.2, PCIe, UART, I2C, SPI

**Three Jetson Cluster Architecture:**
- Three Orin Nano units form a distributed AI cluster ($750 total vs. $1,999 for a single AGX Orin)
- Each node runs a dedicated model: Node 1 = Qwen2.5-Coder-7B, Node 2 = Phi-3-mini, Node 3 = Whisper (on-demand)
- Redis-based leader election for cluster management
- MQTT + gRPC for inter-node communication

**Constraints:**
- **Power budget is 15W sustained** with active cooling required above 10W
- **Thermal throttling at 69°C** — the Qwen model pushes the chip to 69°C average during sustained inference
- **Model memory:** Qwen2.5-Coder-7B Q4_K_M = 4.2 GB, Phi-3-mini = 2.0 GB, OS = 0.5 GB. Total: 6.7 GB of 8 GB. Tight fit.
- **Token generation:** ~17.2 tokens/second on Jetson Orin Nano — a 500-token reflex JSON takes ~29 seconds to generate

### RS-422: Why This Physical Layer

RS-422 is a differential serial signaling standard that uses twisted-pair wiring with balanced voltage transmission.

**Why RS-422 over alternatives:**

| Feature | RS-422 | CAN Bus | Ethernet | UART (TTL) |
|---------|--------|---------|----------|------------|
| **Max distance** | 1,200 m | 500 m | 100 m (copper) | 15 m |
| **Max speed** | 10 Mbps | 1 Mbps | 1 Gbps | 5 Mbps |
| **EMI resistance** | Excellent (differential) | Good (differential) | Good (twisted pair) | Poor (single-ended) |
| **Determinism** | Yes (point-to-point) | Yes (arbitration) | No (CSMA/CD) | Yes (point-to-point) |
| **Complexity** | Minimal (UART driver) | Medium (CAN controller) | High (TCP/IP stack) | Minimal (UART driver) |
| **Cost** | ~$0.50 transceiver | ~$2.00 transceiver + controller | ~$5.00 PHY | ~$0.10 |
| **Wiring** | 4 wires (Tx+, Tx-, Rx+, Rx-) | 2 wires (CAN_H, CAN_L) | 8 wires (4 pairs) | 2 wires (Tx, Rx) |

RS-422 was chosen because it provides the right balance: deterministic latency, EMI resistance for marine/industrial environments, minimal driver complexity, and sufficient bandwidth for NEXUS telemetry rates.

### Sensors and Actuators: The I/O Model

The NEXUS I/O model treats all sensors and actuators as memory-mapped registers accessed through two opcodes:

- **`READ_PIN idx`** — reads the current value from sensor register `idx` (0-63) and pushes it onto the stack
- **`WRITE_PIN idx`** — pops the top stack value and writes it to actuator register `idx` (0-63)

**Sensor categories:**
- **I2C sensors** — compass (HMC5883L or equivalent), IMU (MPU-6050 or BNO085), barometer, temperature
- **ADC sensors** — rudder angle feedback, battery voltage, water level, current sensors
- **UART sensors** — GPS/NMEA receiver (4,800-38,400 baud), depth sounder, weather station
- **Digital inputs** — kill switch, limit switches, button inputs

**Actuator categories:**
- **PWM outputs** — motor controllers, servo motors, solenoid valves (via LEDC peripheral, up to 8 channels)
- **Relay outputs** — pumps, lights, horns, bilge blowers (via GPIO → relay driver)
- **CAN outputs** — future: CAN-connected actuators, NMEA 2000 devices

**The I/O driver registry** (`specs/firmware/io_driver_registry.json`) defines a JSON schema for describing the sensor/actuator configuration of each node. This is loaded at boot via the `ROLE_ASSIGN` message.

### Power Budget and Thermal Constraints

**ESP32-S3 Power Budget:**
- Active (both cores @ 240 MHz): ~240 mA @ 3.3V = ~0.8W
- Light sleep (ULP active): ~0.8 mA = ~0.003W
- Deep sleep: ~10 µA = ~0.00003W
- A vessel with 10 ESP32 nodes draws ~8W total for Tier 1

**Jetson Orin Nano Power Budget:**
- Idle: ~5W
- Moderate inference: ~10W
- Full load (Qwen generation): ~15-20W
- A 3-Jetson cluster draws ~30-45W sustained
- Active cooling (fan) required above 10W
- Thermal throttling threshold: 69°C junction temperature

**System Total:**
- Full vessel: ~50-60W (3 Jetsons + 10 ESP32s + sensors)
- Solar/battery system must provide 60W continuous + 50% margin = 90W design target
- 12V marine power with 7.5A capacity per vessel

---

## 5. The A2A-Native Programming Paradigm

### What is A2A-Native?

Agent-to-Agent (A2A) native programming is the paradigm where **AI agents are the first-class programmers** — not humans. In traditional software development, a human writes code, a compiler translates it, and a machine executes it. In A2A-native development, an AI agent writes (or modifies) bytecode directly, another agent validates it, and the hardware executes it.

This is not science fiction. The NEXUS learning pipeline already implements this pattern: Qwen2.5-Coder-7B generates reflex JSON, the deterministic compiler produces bytecode, the VM validator checks safety properties, and the ESP32 executes it. The human operator's role is limited to describing intent in natural language and approving or rejecting proposals.

### Agent-Annotated Bytecode (AAB)

Agent-Annotated Bytecode extends the standard 8-byte instruction format with a TLV (Type-Length-Value) metadata trailer:

```
[8-byte core instruction] [TLV metadata block]
```

The metadata describes:
- **Provenance** — which agent generated this instruction, when, and why
- **Intention** — what goal this instruction serves (e.g., "reduce heading error")
- **Failure narrative** — what should happen if this instruction produces unexpected results
- **Confidence** — the generating agent's confidence in this instruction's correctness

AAB makes bytecode self-describing. An agent reading AAB bytecode can understand not just *what* the code does, but *why* it exists. This enables:
- Cross-agent code review (Claude reviewing Qwen's output)
- Composition (merging bytecodes from different agents while preserving intention)
- Debugging (tracing failures back to the generating agent's reasoning)
- Fleet learning (sharing bytecodes with their provenance intact)

### The 29 Proposed New Opcodes

The A2A-native language research proposes 29 new opcodes organized into five categories:

| Category | Proposed Opcodes | Purpose |
|----------|-----------------|---------|
| **Intent** | `INTENT_BEGIN`, `INTENT_END`, `INTENT_QUERY` | Declare and query program intentions |
| **Communication** | `AGENT_SEND`, `AGENT_RECV`, `AGENT_BROADCAST`, `AGENT_NEGOTIATE` | Inter-agent message passing |
| **Capability** | `CAP_QUERY`, `CAP_DECLARE`, `CAP_REQUEST`, `CAP_GRANT` | Resource and capability negotiation |
| **Safety** | `SAFETY_ASSERT`, `SAFETY_MONITOR`, `SAFETY_ESCALATE` | Enhanced safety annotations |
| **Meta** | `ANNOTATE`, `PROVENANCE`, `CONFIDENCE`, `NARRATIVE` | Self-description and provenance |

**Critical design decision:** All 29 new opcodes are NOP on the existing 32-opcode VM. Zero firmware changes required for backward compatibility. New opcodes are recognized only by agent interpreters, not by the ESP32 VM. This means the A2A migration can proceed incrementally without disrupting deployed systems.

### System Prompt = Compiler, Equipment = Runtime, Vessel = Hardware

The Three Pillars of A2A-native programming define the complete chain from agent intention to physical execution:

| Pillar | Role | Analogy | Implementation |
|--------|------|---------|----------------|
| **System Prompt** | Compiler frontend | Agent's "understanding" of the problem | Natural language description of intent, constraints, and verification criteria |
| **Equipment** | Runtime environment | OS + drivers + VM | Jetson cluster + ESP32 firmware + wire protocol |
| **Vessel** | Hardware platform | Physical robot | ESP32 nodes, sensors, actuators, power system, enclosure |

With the right system prompt (compiler), runtime (equipment), and hardware (vessel), **any agent can actualize a user's intention directly to the capability of the underlying hardware.** This is the grand thesis of A2A-native programming — it decouples intent from implementation, allowing any LLM (Qwen, Claude, GPT) to generate control code for any NEXUS vessel.

### Why This Is Different from Everything Before

A2A-native programming is not just "AI-assisted coding" (like GitHub Copilot). The differences are fundamental:

| Dimension | AI-Assisted Coding (Copilot) | A2A-Native (NEXUS) |
|-----------|-----------------------------|-------------------|
| **Primary programmer** | Human (AI assists) | AI agent (human supervises) |
| **Output format** | Source code (Python, C, JS) | Bytecode (8-byte instructions) |
| **Execution environment** | General-purpose computer | Safety-critical embedded VM |
| **Verification** | Human code review + tests | Formal validator + A/B testing + trust score |
| **Safety** | Developer responsibility | Constitutional requirement |
| **Trust** | Assumed (you ran the code) | Earned (INCREMENTS framework) |
| **Evolution** | Manual refactoring | Automatic evolutionary optimization |

The 0.5x Trust Rule: Agent-generated bytecode earns trust at **half the rate** of human-authored code. This reflects the reality that AI-generated code, while often correct, carries higher epistemic uncertainty than code written by a human who understands the system.

---

## 6. Safety — The Non-Negotiable Foundation

### Four-Tier Safety Explained

Safety is not a feature of NEXUS — it is the foundation on which everything else is built. The four-tier safety architecture ensures that no single software failure, no single hardware failure, and no combination of software and hardware failures can cause the system to produce unsafe actuator outputs.

**Tier 0 — Hardware Interlock:**
The kill switch is a physical normally-closed (NC) contact in series with actuator power. When the contact opens (operator pulls the switch, or a crash sensor triggers), all actuator power is cut within <100µs. This is the ultimate safety backstop — it works even if the firmware is completely corrupted, the processor is halted, and the power supply is failing.

**Tier 1 — Firmware Safety Guard:**
- **Watchdog timer (MAX6818):** Must be fed every 200ms with the alternating pattern 0x55, 0xAA, 0x55, 0xAA. If the pattern is wrong or the feed is late, the watchdog triggers a hardware reset. The alternating pattern prevents a stuck code path from accidentally feeding the watchdog — the code must be functioning correctly to produce the right sequence.
- **Safety ISRs:** Interrupt service routines at the highest hardware priority. They can preempt the VM execution, the protocol task, and even the safety supervisor task.
- **Overcurrent detection:** Per-channel current monitoring with configurable thresholds. Triggers immediate actuator shutdown on the affected channel.
- **Output clamping:** After every VM tick execution, a post-execution check verifies that all actuator register values are within their configured [min, max] ranges. Values outside the range are clamped.

**Tier 2 — Supervisory Task:**
A FreeRTOS task at priority 24 monitors:
- Heartbeat from Jetson (100ms interval, 500ms warning, 1000ms escalation to SAFE_STATE)
- Health of all other FreeRTOS tasks (alive, not stuck, not exceeding CPU budget)
- Safety state machine transitions (NORMAL → DEGRADED → SAFE_STATE → FAULT)
- Watchdog feeder task health (is it really feeding the pattern correctly?)

**Tier 3 — Application Control:**
Normal operation. Reflex programs execute, telemetry is transmitted, cognitive interaction occurs. This tier operates entirely within the safety envelope established by Tiers 0–2.

### Kill Switch Hardware: How It Works

The kill switch circuit is deceptively simple and deliberately so:

```
+12V Supply ─── [NC Kill Switch Contact] ─── [Actuator Power Bus]
                                                   │
                                            [Pull-down resistor]
                                                   │
                                                  GND
```

When the switch is in its normal (closed) position, power flows to actuators. When the operator pulls the switch (or a crash sensor breaks the contact), the circuit opens and all actuator power is removed. There is no software in this path. There is no microcontroller. There is a wire, a contact, and gravity (or a spring).

**Timing budget** (worst case):
1. Contact bounce settles: ~50µs
2. MOSFET gate charge depletes: ~100µs
3. Actuator power decays: ~500µs
4. Mechanical actuator stops: ~1-5ms (depends on actuator)

**Total: <1ms from switch contact to actuator power cutoff.** This is faster than any software response could possibly be.

### Watchdog Timer: 0x55/0xAA Pattern

The MAX6818 watchdog timer requires a specific 3-bit pattern on its input pin to prevent a reset. The NEXUS firmware uses the alternating pattern 0x55, 0xAA:

- 0x55 = binary 01010101
- 0xAA = binary 10101010

These two values are bitwise complements. A stuck code path (e.g., a `while(1)` loop that writes the same value repeatedly) will inevitably write the wrong value and trigger the reset. The firmware must be actively toggling between two distinct values to keep the watchdog happy.

The watchdog feeder runs as a separate FreeRTOS task at priority 23 (second highest). It writes the pattern every 200ms. If the feeder task dies, is preempted indefinitely, or writes the wrong value, the watchdog triggers a hardware reset within 200-600ms.

### Trust Score as Safety Gate

The trust score is not just a measure of reliability — it is an active safety gate. The INCREMENTS framework ties operational capability directly to demonstrated safe performance:

- **Below L1 (T < 0.4):** The subsystem cannot actuate anything. It can only observe and report. This is the default state for newly deployed systems.
- **At L2 (T = 0.4–0.6):** The subsystem can execute approved actions, but only after explicit operator confirmation.
- **At L4 (T = 0.8–0.95):** The subsystem can act autonomously, but it is still monitored. Any safety event triggers an immediate review and potential trust reduction.
- **At L5 (T ≥ 0.95):** The subsystem is fully autonomous. This requires months of demonstrated safe operation. It can be reached in ~83 days under ideal conditions — but a single severe safety event at L5 can drop trust back to L3 or lower.

The 25:1 loss-to-gain ratio ensures that the system must work hard to earn trust and can lose it quickly. This asymmetry is borrowed from neuroscience: synaptic weakening (LTD) occurs faster than synaptic strengthening (LTP), because in biological systems, responding quickly to danger is more important than slowly building confidence.

### Every Piece of Code Must Respect Safety Invariants

This is not a guideline — it is a rule. Every function you write, every interrupt handler you implement, every message you parse must be evaluated against the safety invariants:

1. **No unsafe actuator output is possible from any code path.**
2. **No code path can disable or bypass the safety system.**
3. **No code path can prevent the kill switch from working.**
4. **No code path can cause the watchdog to stop functioning.**
5. **No code path can consume more than the allocated CPU budget.**
6. **No code path can allocate memory at runtime (no malloc during execution).**

If you cannot verify that your code satisfies all six invariants, it does not ship.

---

## 7. How to Read the Specifications

### NEXUS Naming Conventions (NEXUS-XXX-NNN)

NEXUS specification documents follow a standardized naming convention:

```
NEXUS-{CATEGORY}-{IDENTIFIER} v{MAJOR}.{MINOR}.{PATCH}
```

| Field | Values | Meaning |
|-------|--------|---------|
| CATEGORY | `SPEC`, `PROT`, `SS`, `SAFETY` | Specification, Protocol, Sub-System, Safety |
| IDENTIFIER | `VM-001`, `WIRE-001`, `TS-001` | VM, Wire Protocol, Trust Score |
| VERSION | `v1.0.0`, `v2.0.0` | Semantic versioning (MAJOR.MINOR.PATCH) |

Examples:
- `NEXUS-SPEC-VM-001 v1.0.0` — Reflex Bytecode VM Specification
- `NEXUS-PROT-WIRE-001 v2.0.0` — Serial Wire Protocol Specification
- `NEXUS-SS-001 v2.0.0` — Safety System Specification
- `NEXUS-SAFETY-TS-001 v1.0.0` — Trust Score Algorithm Specification

### Version Numbers and What They Mean

NEXUS uses semantic versioning:
- **MAJOR** — Breaking changes that are not backward-compatible
- **MINOR** — New features that are backward-compatible
- **PATCH** — Bug fixes and clarifications

A specification at v2.0.0 has undergone at least one major revision. Read the changelog at the top of each spec to understand what changed between versions.

### How Specs Reference Each Other

Specifications cross-reference each other using `[[wiki-link]]` syntax. When you see `[[reflex_bytecode_vm_spec]]` in the safety specification, it means the safety system depends on the VM specification. Follow the link to understand the dependency.

Key dependency chains:
- **Wire Protocol** depends on → **Memory Map** (PSRAM layout for observation buffers)
- **Safety System** depends on → **Wire Protocol** (safety event messages), **Trust Score** (autonomy gating), **VM Spec** (cycle budget enforcement)
- **Learning Pipeline** depends on → **Wire Protocol** (telemetry messages), **VM Spec** (reflex JSON schema), **Safety Policy** (reflex validation rules)

### Safety Policy JSON Format

The safety policy (`specs/safety/safety_policy.json`) defines runtime safety rules in a structured JSON format:

```json
{
  "version": "1.0.0",
  "global_rules": [
    {
      "id": "SR-001",
      "description": "Actuator output clamping",
      "condition": "always",
      "action": "clamp",
      "parameters": { "source": "actuator_register", "range": "actuator_profile" }
    }
  ],
  "actuator_profiles": {
    "rudder_servo": { "min_deg": -45.0, "max_deg": 45.0, "rate_limit": 60.0 },
    "throttle_motor": { "min_percent": 0.0, "max_percent": 100.0, "rate_limit": 20.0 }
  },
  "domain_overrides": {
    "marine": [/* marine-specific rules */],
    "healthcare": [/* healthcare-specific rules */]
  }
}
```

There are 10 global safety rules (SR-001 through SR-010) covering output clamping, rate limiting, sensor validation, heartbeat monitoring, overcurrent protection, thermal protection, GPS validation, communication timeout, mode transitions, and emergency protocols.

### Bytecode Encoding Format

Each bytecode instruction is exactly 8 bytes:

```
Offset  Size  Field           Description
------  ----  -----           -----------
0       1     opcode          0x00-0x1F (32 defined opcodes)
1       1     flags           Bit 7: SYSCALL, Bit 6: IMMEDIATE_F32, Bits 0-5: reserved
2       1     operand1        Pin index, variable index, or jump offset MSB
3       1     operand2        Pin index, variable index, or jump offset LSB
4       4     immediate       int8 (bytes 4-4), int16 (bytes 4-5), float32 (bytes 4-7)
```

Example: A PID compute instruction:
- Opcode 0x1A = PID_COMPUTE
- Flags 0x00 = no syscall, no immediate
- Operand1 = 0x00 = PID instance 0
- Operand2 = 0x03 = output to actuator 3
- Immediate = 0x00000000 = unused

Result: `1A 00 00 03 00 00 00 00`

---

## 8. Coding Standards for NEXUS

### C Coding for ESP32 (FreeRTOS, MISRA Guidelines)

The ESP32 firmware is written in C using the ESP-IDF framework with FreeRTOS. Follow these standards:

**MISRA C Compliance:**
- Follow MISRA C:2012 guidelines where practical. The full 177-rule MISRA C standard is aspirational, but the following rules are mandatory:
  - No dynamic memory allocation at runtime (no `malloc`/`free`/`calloc` after initialization)
  - No recursion (all functions must have bounded stack depth)
  - No `goto` statements (use structured control flow)
  - No uninitialized variables
  - No implicit type conversions
  - No undefined behavior (all operations must be well-defined for all inputs)

**FreeRTOS Conventions:**
- All tasks are created during `app_main()` before the scheduler starts. No dynamic task creation.
- Use `xQueueSend()`/`xQueueReceive()` for inter-task communication. Never share mutable data between tasks without synchronization.
- Use `taskENTER_CRITICAL()`/`taskEXIT_CRITICAL()` sparingly and only for very short critical sections (no I/O, no blocking calls).
- Stack size for each task is 4096 bytes. Do not exceed this without architectural review.
- Use `configASSERT()` for debug-time invariant checking.

**Naming Conventions:**
- Functions: `snake_case()` with module prefix: `vm_execute_tick()`, `protocol_decode_frame()`
- Types: `snake_case_t`: `vm_stack_t`, `protocol_message_t`
- Macros: `UPPER_SNAKE_CASE`: `MAX_STACK_DEPTH`, `CYCLE_BUDGET`
- Constants: `UPPER_SNAKE_CASE`: `VM_OPCODE_COUNT`, `SAFETY_STATE_NORMAL`
- File names: `snake_case.c` / `snake_case.h`

### Python/C++ for Jetson

The Jetson cognitive layer uses Python for high-level logic and C++ for performance-critical inference:

**Python Standards:**
- Python 3.10+ with type hints everywhere
- Follow PEP 8 with 120-character line length
- All async code uses `asyncio` — no threading for I/O-bound operations
- JSON schema validation for all message formats (use `jsonschema` library)
- Configuration via environment variables with `python-dotenv`
- Logging via Python `logging` module (never `print()` in production code)

**C++ Standards:**
- C++17 with clang-tidy compliance
- RAII for all resource management (no raw `new`/`delete`)
- Smart pointers only (`std::unique_ptr`, `std::shared_ptr`)
- No exceptions in performance-critical paths (use `std::expected` or error codes)
- TensorRT for GPU inference — never write custom CUDA kernels unless absolutely necessary

### JSON Schema for Reflex Programs

Reflex programs are defined in JSON and compiled to bytecode. The schema follows this structure:

```json
{
  "name": "heading_hold_pid",
  "version": "1.0.0",
  "author": "qwen2.5-coder-7b",
  "description": "Maintain heading at setpoint using PID control",
  "inputs": [
    { "pin": 0, "type": "sensor", "description": "compass_heading_deg" },
    { "pin": 1, "type": "sensor", "description": "desired_heading_deg" }
  ],
  "outputs": [
    { "pin": 2, "type": "actuator", "description": "rudder_servo", "min": -45.0, "max": 45.0 }
  ],
  "variables": [
    { "index": 0, "name": "integral_error", "initial": 0.0 },
    { "index": 1, "name": "prev_error", "initial": 0.0 }
  ],
  "parameters": {
    "kp": 0.8, "ki": 0.01, "kd": 0.3,
    "sample_period_ms": 100,
    "output_clamp_min": -45.0,
    "output_clamp_max": 45.0
  },
  "bytecode": "hex_encoded_bytecode_string"
}
```

The `bytecode` field contains the hex-encoded binary bytecode that the VM will execute. The compiler generates this from the inputs, outputs, variables, and parameters.

### Wire Protocol Message Construction

To construct a wire protocol message:

1. **Build the payload** — a binary buffer containing the message type (1 byte) + message-specific fields
2. **Compute CRC-16** — CRC-16/CCITT-FALSE over the entire payload (polynomial 0x1021, init 0xFFFF)
3. **Append CRC** — 2 bytes, little-endian
4. **COBS-encode** — encode the payload + CRC using Consistent Overhead Byte Stuffing
5. **Transmit** — write the COBS-encoded frame followed by a `0x00` delimiter byte

On the receiving end:
1. Read bytes until `0x00` delimiter
2. COBS-decode the frame
3. Extract and verify CRC-16 (discard frame if mismatch, request retransmission)
4. Parse message type and dispatch to handler

---

## 9. Testing and Validation

### Unit Testing Strategy

**ESP32 Firmware (C):**
- Use Unity test framework (included in ESP-IDF)
- Test every opcode individually (32 tests minimum for the VM)
- Test every safety system component independently
- Test edge cases: stack overflow, cycle budget exceeded, division by zero, NaN input, maximum stack depth, all-zeros bytecode
- Target: 90%+ statement coverage for safety-critical functions

**Jetson Software (Python/C++):**
- Use pytest for Python, Google Test for C++
- Test the compiler: JSON → bytecode → disassemble → verify semantic preservation
- Test the learning pipeline: mock sensor data → pattern discovery → reflex synthesis → validate output
- Test the trust score: feed known event sequences and verify trust trajectory matches closed-form solutions

### VM Simulator Testing

A VM simulator (`vm_simulator.py` or equivalent) must be maintained in parallel with the firmware VM. It serves two purposes:

1. **Reference implementation** — the simulator defines the correct behavior. If the firmware VM disagrees with the simulator, the firmware is wrong.
2. **Regression testing** — run the full opcode test suite against the simulator on every commit. The simulator runs in milliseconds; testing on real hardware takes minutes.

The simulator must implement:
- All 32 opcodes with cycle-accurate timing
- The complete validator (stack balance, jump targets, operand ranges, NaN check, cycle budget)
- The safety state machine
- All 28 wire protocol message types

### Wire Protocol Testing

Wire protocol testing requires a hardware-in-the-loop (HIL) test setup:

1. **Framing tests** — send malformed COBS frames, verify rejection
2. **CRC tests** — inject bit errors, verify detection rate matches theoretical (undetected error rate <10⁻¹⁰)
3. **Throughput tests** — verify actual throughput matches specification (80+ telemetry messages/sec at 921600 baud)
4. **Latency tests** — measure ping/pong RTT, verify <2ms command RTT
5. **Noise tests** — inject electromagnetic interference, verify CRC catches corrupted frames
6. **Stress tests** — sustained maximum-rate transmission for 24+ hours, verify no memory leaks, no buffer overflows

### Safety Validation

Safety validation goes beyond unit testing. It requires:

1. **FMEA (Failure Mode and Effects Analysis)** — 15 failure modes documented in the safety spec. Each mode has a Risk Priority Number (RPN) and a mitigation strategy. Review and update for every firmware change.
2. **Monte Carlo simulation** — the safety simulation script (`safety_simulation.py`) models 1000+ iterations across 5 stress scenarios. Run after every safety-critical change.
3. **Watchdog testing** — deliberately starve the watchdog and verify reset occurs within 600ms.
4. **Kill switch testing** — trigger the kill switch and verify actuator power cutoff within 1ms (use an oscilloscope).
5. **Trust score boundary testing** — verify trust transitions at every level boundary (L0→L1, L1→L2, etc.) using scripted event sequences.
6. **Thermal testing** — run the system at maximum sustained load and verify thermal throttling does not cause safety violations.

### A/B Testing for Reflex Deployment

The A/B testing framework runs on the Jetson and validates candidate reflexes before deployment:

1. **Deploy candidate** — load new bytecode alongside production bytecode on the target ESP32 node
2. **Collect observations** — run both reflexes for n ≥ 500 observations (configurable)
3. **Compute Bayesian posterior** — estimate the probability that the candidate is better than production
4. **Safety gate** — if the candidate produces any safety violation during A/B testing, immediately terminate and discard
5. **Promote or reject** — if posterior P(candidate > production) > 0.95, promote. Otherwise, reject.

The statistical framework provides 100% power to detect a 7% improvement at α = 0.05 with n = 500 observations.

---

## 10. Knowledge Base Map

### Foundations: Start Here for History and Theory

The `knowledge-base/foundations/` directory contains five encyclopedia-grade articles:

1. **`history_of_programming_languages.md`** (~7,500 words) — 80 years of programming language evolution, from plugboards to LLMs, with specific analysis of what each era teaches us about agent-native programming.
2. **`evolution_of_virtual_machines.md`** — Complete genealogy of VMs from Turing's universal machine (1936) through the NEXUS Reflex VM (2025). Includes detailed comparison tables (JVM, Lua, eBPF, WebAssembly, NEXUS).
3. **`programming_paradigms.md`** (~9,200 words) — 14 major programming paradigms analyzed for their relevance to A2A-native programming. Includes a massive comparison matrix.
4. **`biological_computation_and_evolution.md`** — Biological systems that inform NEXUS: DNA as code, neural computation, evolutionary optimization, swarm intelligence, immune safety. Maps every biological mechanism to its NEXUS equivalent.
5. **`cross_cultural_computing.md`** — Non-Western contributions to computing: Babylonian base-60, Indian zero, Chinese abacus, Mayan calendars, Islamic algorithms, Japanese soroban. Demonstrates that NEXUS's design principles are culturally universal.

### Theory: Mathematical and Computational Foundations

The `knowledge-base/theory/` directory contains six articles:

1. **`type_systems_and_formal_languages.md`** — Type theory, formal grammars, and their relevance to bytecode verification.
2. **`formal_verification_and_safety.md`** — Model checking, theorem proving, abstract interpretation, safety standards (IEC 61508, ISO 26262, DO-178C), failure analysis (FMEA, FTA).
3. **`evolutionary_computation.md`** — Genetic algorithms, genetic programming, and the theoretical foundations of NEXUS's evolutionary bytecode optimization.
4. **`agent_communication_languages.md`** — How agents communicate: KQML, FIPA-ACL, and the design of the NEXUS agent protocol.
5. **`program_synthesis_and_ai_codegen.md`** — Program synthesis, neural code generation, and the theoretical limits of AI-generated code.
6. **`self_organizing_systems.md`** — Emergence, stigmergy, and self-organization in multi-agent systems.

### Philosophy: The "Why" Behind Design Decisions

The `knowledge-base/philosophy/` directory contains two articles:

1. **`trust_psychology_and_automation.md`** — Human trust psychology (Lee & See 2004) and how it informs the NEXUS trust score design.
2. **`philosophy_of_ai_and_consciousness.md`** — Philosophical implications of agent-native programming, consciousness, and autonomy.

### Systems: Hardware and Software Architecture

The `knowledge-base/systems/` directory contains three articles:

1. **`embedded_and_realtime_systems.md`** — Complete history of embedded systems from Intel 4004 to Jetson Orin Nano, FreeRTOS, scheduling theory, ESP32-S3 deep dive, Jetson Orin Nano deep dive, communication protocols, memory-constrained computing.
2. **`robotics_control_history.md`** — History of robotics control from teleoperation to autonomy.
3. **`distributed_systems.md`** (~11,333 words) — CAP theorem, consensus protocols, distributed architectures, fault tolerance, communication patterns, real-time distributed systems, edge computing, swarm robotics, network topologies.

### Domains: Application-Specific Knowledge

The `knowledge-base/domains/` directory currently contains:

1. **`marine_autonomous_systems.md`** (~8,700 words) — Marine vessel types, navigation systems, propulsion control, environmental sensing, maritime regulations (COLREGs, SOLAS), weather routing, existing autonomous systems.

### Reference: Glossary, Bibliography, Law

The `reference/` directory is planned for glossary, bibliography, and legal reference materials. Until it is populated, use the individual reference sections at the end of each knowledge base article.

---

## 11. The Road Ahead

### What Has Been Built (Specifications and Research)

NEXUS is currently a **complete specification** with extensive research backing. What exists:

- **21 specification files** (~19,200 lines) defining every aspect of the system
- **28 Architecture Decision Records** documenting key design choices
- **5 rounds of iterative research** (dissertation) covering safety, trust, VM performance, cross-domain analysis, regulatory compliance, AI model analysis, and multi-cultural philosophy
- **6 A2A-native language research documents** (45,191 words) defining the next-generation programming paradigm
- **17 knowledge base articles** (foundations, theory, philosophy, systems, domains)
- **Python simulation scripts** for safety Monte Carlo, trust score evolution, VM benchmarking, and learning pipeline
- **Figures and data** from all simulations

**What does NOT exist yet:** The actual running code. NEXUS is fully specified but not yet implemented.

### What Needs to Be Built (The Actual System)

The estimated build effort for 3 developers working in parallel is **12–16 weeks** to a working demo, with the **fastest path to demo at 8 weeks**.

**Phase 1 — Core ESP32 Firmware (4-6 weeks):**
- Reflex Bytecode VM (32 opcodes, validator, executor)
- Wire protocol handler (COBS, CRC-16, message dispatch)
- Safety system (watchdog, heartbeat, kill switch ISR, output clamping)
- I/O subsystem (sensor polling, actuator driving)
- Role assignment and configuration

**Phase 2 — Jetson Cognitive Layer (3-4 weeks):**
- MQTT broker and topic management
- Reflex compiler (JSON → bytecode)
- Telemetry aggregation and storage
- Learning pipeline (pattern discovery, reflex synthesis)
- A/B testing framework
- Natural language chat interface

**Phase 3 — Integration and Validation (3-4 weeks):**
- ESP32-Jetson communication (wire protocol over RS-422)
- End-to-end reflex deployment (generate → compile → transmit → validate → execute)
- Safety validation (Monte Carlo, HIL testing, kill switch)
- Trust score implementation and testing
- Multi-node colony demonstration

**Phase 4 — A2A Migration (32 weeks, 3 phases):**
- Phase 1 (12 weeks): AAB format, agent communication protocol, equipment runtime
- Phase 2 (12 weeks): Intention blocks, capability negotiation, 29 new opcodes
- Phase 3 (8 weeks): Fleet learning, cross-agent code review, multi-vessel coordination

### How to Contribute

1. **Read this guide and the 20 essential documents** (see Section 12).
2. **Pick a component** from the build plan that matches your skills:
   - Embedded C developers → ESP32 firmware (VM, wire protocol, safety)
   - Python/C++ developers → Jetson cognitive layer (learning pipeline, compiler, MQTT)
   - Systems engineers → Integration, testing, validation
   - AI/ML engineers → Model optimization, pattern discovery algorithms
3. **Read the relevant specification** before writing any code. The spec is the source of truth.
4. **Follow the coding standards** in Section 8.
5. **Write tests first.** Every function must have a corresponding test.
6. **Respect safety invariants.** No exceptions, no shortcuts.

### The 36-Month Roadmap

| Phase | Timeline | Focus | Deliverable |
|-------|----------|-------|-------------|
| **Foundation** | Months 1-6 | ESP32 firmware + Jetson core | Single-vessel demo with manual reflex deployment |
| **Learning** | Months 4-12 | Learning pipeline + A/B testing | System that learns from observation and deploys improved reflexes |
| **Multi-Domain** | Months 8-24 | Domain adaptation (marine, agriculture, HVAC) | Cross-domain deployment with domain-specific configurations |
| **A2A Migration** | Months 12-36 | Agent-native programming paradigm | Full A2A-native system with fleet learning |
| **Certification** | Months 24-36 | IEC 61508 SIL 1 + IEC 60945 | Certified system ready for commercial deployment |

---

## 12. Essential Reading Order

### The 20 Most Important Documents

Read these documents in this order. Order matters: start with overview, then architecture, then your specific domain.

#### Phase 1: Overview (Day 1-2)

| # | Document | Location | Time | Why |
|---|----------|----------|------|-----|
| 1 | Project README | `README.md` | 10 min | The 30,000-foot view |
| 2 | Master Index | `specs/00_MASTER_INDEX.md` | 15 min | Roadmap to all specifications |
| 3 | Architecture Decision Records | `specs/ARCHITECTURE_DECISION_RECORDS.md` | 60 min | Understand WHY decisions were made |
| 4 | Senior Engineer Build Guide | `specs/SENIOR_ENGINEER_BUILD_GUIDE.md` | 30 min | Practical build instructions |

#### Phase 2: Architecture (Day 3-5)

| # | Document | Location | Time | Why |
|---|----------|----------|------|-----|
| 5 | Reflex Bytecode VM Spec | `specs/firmware/reflex_bytecode_vm_spec.md` | 120 min | **THE most important spec.** The VM is the heart of everything. |
| 6 | Wire Protocol Spec | `specs/protocol/wire_protocol_spec.md` | 90 min | How nodes communicate. COBS, CRC-16, 28 message types. |
| 7 | Safety System Spec | `specs/safety/safety_system_spec.md` | 90 min | Four-tier defense-in-depth. Non-negotiable. |
| 8 | Trust Score Algorithm | `specs/safety/trust_score_algorithm_spec.md` | 60 min | How autonomy is earned. 12 parameters, 3-branch recurrence. |
| 9 | Safety Policy | `specs/safety/safety_policy.json` | 30 min | Runtime safety rules (SR-001 through SR-010). |

#### Phase 3: Implementation Details (Day 6-8)

| # | Document | Location | Time | Why |
|---|----------|----------|------|-----|
| 10 | Memory Map and Partitions | `specs/firmware/memory_map_and_partitions.md` | 45 min | ESP32 memory layout. Know your constraints. |
| 11 | I/O Driver Interface | `specs/firmware/io_driver_interface.h` | 30 min | The C header that defines sensor/actuator access. |
| 12 | I/O Driver Registry | `specs/firmware/io_driver_registry.json` | 20 min | JSON schema for device configuration. |
| 13 | Message Payloads | `specs/protocol/message_payloads.json` | 30 min | Binary format of every message type. |
| 14 | Learning Pipeline Spec | `specs/jetson/learning_pipeline_spec.md` | 60 min | Observe→discover→synthesize→test→deploy. |
| 15 | MQTT Topics | `specs/jetson/mqtt_topics.json` | 15 min | Topic hierarchy for Jetson communication. |

#### Phase 4: Deep Context (Week 2)

| # | Document | Location | Time | Why |
|---|----------|----------|------|-----|
| 16 | A2A Language Design & Semantics | `a2a-native-language/language_design_and_semantics.md` | 90 min | The future of the platform. 29 new opcodes, AAB format. |
| 17 | A2A Final Synthesis | `a2a-native-language/final_synthesis.md` | 60 min | Grand thesis, Three Pillars, 36-month roadmap. |
| 18 | Embedded and Real-Time Systems | `knowledge-base/systems/embedded_and_realtime_systems.md` | 120 min | ESP32-S3 deep dive, FreeRTOS, scheduling theory. |
| 19 | Formal Verification and Safety | `knowledge-base/theory/formal_verification_and_safety.md` | 120 min | Safety standards, model checking, FMEA, failure case studies. |
| 20 | Evolution of Virtual Machines | `knowledge-base/foundations/evolution_of_virtual_machines.md` | 90 min | Why NEXUS's VM is designed the way it is. History matters. |

**Total reading time: ~20 hours.** After completing this reading list, you will have the context needed to be productive on any component of the NEXUS system.

---

## Final Words

Welcome to NEXUS. You are joining a project that aims to fundamentally change how humans interact with autonomous machines — not by writing better code, but by building systems that write their own code, verify their own safety, and earn their own trust.

The specifications are complete. The research is thorough. The architecture is sound. What remains is the actual building — and that is why you are here.

**Three things to remember:**

1. **The ribosome does not need to understand what it builds.** Keep the VM simple, deterministic, and fast. The intelligence lives on the Jetson, not on the ESP32.

2. **Safety is non-negotiable.** Every line of code you write must respect the six safety invariants. If you are unsure, ask. There are no stupid safety questions.

3. **Trust is earned, not granted.** The INCREMENTS framework applies to developers as much as to subsystems. Start by reading, then by understanding, then by building. Trust your knowledge before you trust your code.

Now go read the VM specification. It is the most important document in this entire repository, and everything else depends on it.

---

*This guide was generated as part of the NEXUS knowledge base. Last updated: 2025.*
