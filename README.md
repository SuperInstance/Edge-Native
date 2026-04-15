<p align="center">
  <img src="https://img.shields.io/badge/specs-21%20production-brightgreen" alt="Specs">
  <img src="https://img.shields.io/badge/specs-19.2K%20lines-blue" alt="Spec Lines">
  <img src="https://img.shields.io/badge/ADRs-28-purple" alt="ADRs">
  <img src="https://img.shields.io/badge/opcodes-32%20core%20%2B%2029%20A2A-orange" alt="Opcodes">
  <img src="https://img.shields.io/badge/KB-334K%20words-informational" alt="Knowledge Base">
  <img src="https://img.shields.io/badge/domains-8-red" alt="Domains">
</p>

<h1 align="center">NEXUS — Edge-Native Distributed Intelligence Platform</h1>

<p align="center">
  <strong>The Post-Coding Age of Industrial Robotics. No human writes, reads, or debugs code.</strong>
</p>

---

## Overview

NEXUS Edge-Native is the **definitive specification and knowledge repository** for the NEXUS distributed intelligence platform — a system where LLM agents, not humans, are the primary authors of control code. This repository contains everything needed to understand, specify, build, and deploy edge-native AI systems: 21 production specification files (~19,200 lines), 28 architecture decision records, a 333,775-word knowledge base encyclopedia, a 5-round research dissertation with Monte Carlo simulations, A2A-native programming language research, and a complete build roadmap spanning 6 phases, 20 sprints, and $2.6M over 36 months.

Where the companion [nexus-runtime](https://github.com/nexus-platform/nexus-runtime) repository contains the *executable code*, Edge-Native contains the *authoritative specifications* — every opcode, every wire frame, every trust parameter, every safety rule. If code disagrees with these specs, the specs win.

The platform inverts the conventional robotics paradigm. Rather than centralizing intelligence in a "brain" with dumb actuators, NEXUS distributes cognition to the periphery. Each limb runs a bytecode VM on an ESP32-S3 that executes reflex programs at 1ms ticks. The Jetson provides AI cognition — pattern discovery, natural language reflex synthesis, A/B testing — but the ESP32 maintains safe control even when ALL higher tiers fail. Like a biological ribosome translating mRNA into proteins without understanding, the ESP32 executes bytecode without comprehension.

## Architecture

Three-tier, hardware-agnostic design with progressive autonomy:

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  TIER 3: CLOUD  ───────────────────────────────────────────────────     │
  │  Hardware: Starlink / 5G / Cloud Servers                               │
  │  Latency: seconds – hours                                               │
  │                                                                         │
  │  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐                 │
  │  │ Heavy Model │   │  Fleet Mgmt  │   │  Simulation  │                 │
  │  │  Training   │   │  & Mission   │   │  Digital Twin│                 │
  │  └──────┬──────┘   └──────┬───────┘   └──────┬───────┘                 │
  └─────────┼─────────────────┼──────────────────┼──────────────────────────┘
            │                 │                  │
            │  Starlink / 5G  │  MQTT / gRPC     │
            ▼                 ▼                  ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  TIER 2: COGNITIVE (Jetson Orin Nano)  ──────────────────────────      │
  │  Hardware: NVIDIA Jetson Orin Nano Super — $249, 40 TOPS, 8GB LPDDR5   │
  │  Latency: 10 – 500ms                                                   │
  │                                                                         │
  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐   │
  │  │  Vision  │ │   Trust   │ │  Reflex  │ │ Learning  │ │  Swarm   │   │
  │  │ Pipeline │ │  Engine   │ │ Compiler │ │ Pipeline  │ │  Coord   │   │
  │  └──────────┘ └───────────┘ └──────────┘ └───────────┘ └──────────┘   │
  │                                                                         │
  └────────┬──────────────────┬──────────────────┬──────────────────────────┘
           │  RS-422 / UART   │  COBS/CRC-16    │  921,600 baud
           │  Trust scores    │  Bytecode deploy│  28 msg types
           ▼                  ▼                  ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  TIER 1: REFLEX (ESP32-S3 MCU)  ──────────────────────────────────     │
  │  Hardware: ESP32-S3 — $6–10/unit, 240MHz, 8MB PSRAM, 45 GPIO          │
  │  Latency: 10µs – 1ms                                                    │
  │                                                                         │
  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐                 │
  │  │ 32-op    │ │   Wire    │ │  Safety  │ │ Sensor /  │                 │
  │  │ Bytecode │ │ Protocol  │ │    SM    │ │ Actuator  │                 │
  │  │    VM    │ │ COBS+CRC  │ │ ISR+WDT  │ │   Drivers │                 │
  │  └──────────┘ └───────────┘ └──────────┘ └───────────┘                 │
  │                                                                         │
  │  ✓ Operates independently — maintains safe control even if ALL          │
  │    higher tiers fail                                                    │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  HARDWARE INTERLOCK (always active)                                     │
  │  Kill switch • Watchdog IC • Polyfuses • E-Stop ISR                    │
  │  Response: <1µs — operates regardless of all software                   │
  └─────────────────────────────────────────────────────────────────────────┘
```

**Key design principle**: Each tier operates independently. Tier 1 maintains safe control even when all higher tiers fail. No single point of failure can compromise safety.

## Edge Deployment Model

NEXUS follows a **peripheral intelligence** model — computation lives as close to the sensors and actuators as possible, with intelligence progressively centralized only for tasks that require it:

```
┌─────────────────── EDGE DEPLOYMENT TOPOLOGY ───────────────────┐
│                                                                 │
│   ┌─────────────┐    RS-422     ┌─────────────┐               │
│   │  ESP32 #1   │◄────────────►│             │               │
│   │  (Thruster) │    921600bd   │             │               │
│   └─────────────┘               │             │               │
│   ┌─────────────┐    RS-422     │   JETSON    │    Starlink    │
│   │  ESP32 #2   │◄────────────►│   ORIN NANO │◄──────────► CLOUD
│   │  (Rudder)   │    921600bd   │  (Cognition)│    / 5G       │
│   └─────────────┘               │             │               │
│   ┌─────────────┐    RS-422     │  • Trust    │               │
│   │  ESP32 #3   │◄────────────►│  • Learning │               │
│   │  (Sensors)  │    921600bd   │  • Compiler │               │
│   └─────────────┘               │  • Vision   │               │
│                                 └─────────────┘               │
│                                                                 │
│   Each ESP32 runs an independent bytecode VM. If the Jetson    │
│   fails, each ESP32 continues executing its last validated     │
│   reflex in safe-state mode. If an ESP32 fails, the Jetson    │
│   escalates the vessel to DEGRADED and redistributes tasks.   │
└─────────────────────────────────────────────────────────────────┘
```

### Tier Responsibilities

| Tier | Hardware | Role | Latency | Independence |
|------|----------|------|---------|-------------|
| **1 — Reflex** | ESP32-S3 MCU | Real-time sensor polling, bytecode VM execution, safety enforcement | 10µs – 1ms | Full — runs indefinitely without higher tiers |
| **2 — Cognitive** | NVIDIA Jetson Orin Nano | AI inference, NLP chat, pattern discovery, reflex compilation, trust scoring | 10 – 500ms | High — degrades gracefully to Tier 1 |
| **3 — Cloud** | Starlink / 5G | Heavy model training, simulation, fleet management, digital twins | seconds – hours | Optional — system fully functional offline |

### Safety Independence Model

```
  Cloud fails?     → Jetson continues cognition, ESP32s continue reflex execution
  Jetson fails?    → Each ESP32 runs last validated reflex in safe-state mode
  One ESP32 fails? → Jetson escalates to DEGRADED, redistributes tasks
  All ESP32s fail? → Hardware interlock kills actuator power in <1µs
  Serial link cut? → ESP32 heartbeat timeout → safe-state in <1s
```

## Key Specifications

- **Wire Protocol**: RS-422, COBS framing, CRC-16, 28 message types, 921,600 baud
- **Bytecode VM**: 32 opcodes, 8-byte fixed instructions, stack machine, ~3 KB footprint, <100µs per tick
- **Safety System**: 4-tier defense-in-depth (hardware interlock → firmware ISR → supervisory task → application)
- **Autonomy**: INCREMENTS framework with 6 levels per subsystem (L0-L5), 25:1 trust loss-to-gain ratio, 27 days minimum for full autonomy
- **Learning**: 5 pattern discovery algorithms (cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference)
- **A2A-Native**: 29 agent-to-agent opcodes, AAB metadata format, intent-first programming paradigm
- **Cross-Domain**: Marine, agriculture, HVAC, factory automation, mining, aerospace, healthcare

## Quick Start

**For builders using Claude Code** (recommended):

```bash
# 1. Read the entry point
cat claude.md

# 2. Understand the roadmap
cat roadmap.md

# 3. Start building
# Read claude-build/build-specification.md → Phase 0 Sprint 0.1
```

**For developers**:

```bash
# Explore specifications
ls specs/                          # 21 production specs
ls specs/firmware/                 # VM, drivers, memory map
ls specs/protocol/                 # Wire protocol, payloads
ls specs/safety/                   # Trust algorithm, safety policy

# Explore the knowledge base
ls knowledge-base/                  # 27 articles, 333K words
cat knowledge-base/developer-guide/onboarding_guide.md

# Run Jetson SDK (Sprint 0.1 foundation)
cd jetson && python -m main.nexus_main

# Run tests
python -m pytest tests/ -v
```

**For researchers**:

```bash
# 5-round dissertation with simulations
ls dissertation/round4_simulations/    # Monte Carlo simulations
cat dissertation/round5_synthesis/     # Universal synthesis

# A2A-native language research
ls a2a-native-language/                # 45K words, 6 documents
cat a2a-native-language/final_synthesis.md
```

## Repository Structure

```
├── specs/                   # ★ 21 production specifications (~19,200 lines)
│   ├── protocol/            # Wire protocol spec, message payloads (JSON)
│   ├── safety/              # Safety system, trust scores, safety policy (JSON)
│   ├── firmware/            # Bytecode VM, I/O drivers, memory map
│   ├── jetson/              # Learning pipeline, MQTT topics, cluster API (proto)
│   └── ports/               # Hardware compatibility matrix (JSON)
├── firmware/                # ESP-IDF C firmware (implementation target)
│   ├── nexus_vm/            # VM interpreter, validator, opcodes (C)
│   ├── wire_protocol/       # COBS, CRC-16, frame, dispatch (C)
│   ├── safety/              # Watchdog, heartbeat, safety SM, E-stop (C)
│   └── drivers/             # Sensor bus, actuator drivers, HAL (C)
├── jetson/                  # Python Jetson SDK (v0.1.0)
│   ├── main/                # Entry point (nexus_main.py)
│   ├── nexus_sdk/           # SDK package
│   ├── wire_client/         # Wire protocol client (Python)
│   ├── reflex_compiler/     # JSON-to-bytecode compiler
│   ├── trust_engine/        # INCREMENTS trust algorithm
│   ├── safety_validator/    # Reflex static analysis
│   ├── learning/            # Pattern discovery & A/B testing
│   └── agent_runtime/       # A2A-native agent execution
├── shared/                  # Shared bytecode definitions (C + Python)
│   └── bytecode/            # opcodes.h, instruction.h, opcodes.py
├── schemas/                 # JSON schemas (reflex, roles, protocol, autonomy)
├── dissertation/            # 5-round iterative research dissertation
│   ├── round1_research/     # Deep technical foundations
│   ├── round2_research/     # Cross-domain & regulatory analysis
│   ├── round3_research/     # Philosophical, ethical, cultural perspectives
│   ├── round4_simulations/  # Monte Carlo & adversarial simulations (Python)
│   └── round5_synthesis/    # Universal synthesis
├── knowledge-base/          # Encyclopedic knowledge base (27 articles, 333K words)
│   ├── foundations/         # History, VMs, biology, culture, paradigms
│   ├── theory/              # Agents, evolution, verification, self-org, types
│   ├── philosophy/          # AI consciousness, trust psychology, post-coding
│   ├── systems/             # Embedded, distributed, robotics, edge AI, co-design
│   ├── domains/             # Marine systems, maritime navigation history
│   └── reference/           # Glossary (310 terms), bibliography (178 refs)
├── a2a-native-language/     # A2A-native programming research (45K words, 6 docs)
├── a2a-native-specs/        # A2A-native Rosetta Stone twin specs (8 specs)
├── vessel-platform/         # Marine vessel platform architecture (16 docs)
├── autopilot/               # ESP32 autopilot engineering & PID simulations
├── framework/               # Core framework design documents (7 docs)
├── onboarding/              # Onboarding + user education (132K words)
├── claude-build/             # Build specifications for Claude Code
├── incubator/               # Edgeware Incubator — manifesto & principles
├── human-readable/          # Plain-language summaries (27K words)
├── addenda/                 # Engineering addenda (pitfalls, checklists, playbooks)
├── v31-docs/                # v3.1 documentation set (13 docs)
├── tools/                   # Test runner, flash script, safety check
├── tests/                   # Unit, firmware, HIL test suites
└── archives/                # Complete project zip archives
```

## Build the System

[**roadmap.md**](./roadmap.md) — Master build plan: 6 phases, 20 sprints, 5 milestones, $2.6M over 36 months.

[**claude-build/**](./claude-build/) — Component-by-component build specification for Claude Code. Struct definitions, opcode implementations, test vectors, the works.

**Build phases at a glance:**

| Phase | Name | Duration | Outcome |
|-------|------|----------|---------|
| **0** | Foundation | Weeks 1–4 | VM runs on ESP32, wire protocol connects to Jetson, LED blinks from NL |
| **1** | Safety Hardening | Weeks 5–8 | 4-tier safety tested, trust engine validated, HIL framework |
| **2** | Intelligence Layer | Weeks 9–16 | Pattern discovery, A/B testing, LLM reflex synthesis, marine domain |
| **3** | A2A-Native | Weeks 17–24 | Agent-annotated bytecode, cooperative perception, fleet learning |
| **4** | Self-Evolution | Weeks 25–32 | Genetic algorithms, evolutionary code improvement, meta-learning |
| **5** | Production | Weeks 33–48 | Certification evidence, multi-vessel sea trials, fleet deployment |

## Edgeware Incubator

NEXUS is the reference implementation for the [Edge-Native Edgeware Incubator](./incubator/) — a framework for designing, building, and evolving edge-native AI systems. Read the [manifesto](./incubator/manifesto.md) for the 10 principles.

## A2A-Native Programming

NEXUS extends its bytecode VM into an **agent-first programming paradigm** where LLM agents are the primary authors, interpreters, and validators of control code. With the right system prompt (compiler), runtime (equipment), and hardware (vessel), any agent can actualize a user's intention directly to the capability of the underlying hardware.

- **Research**: [`a2a-native-language/`](./a2a-native-language/) — 45,000-word research corpus (language design, hardware bridge, integration, communication, cross-domain, synthesis)
- **Rosetta Stone**: [`a2a-native-specs/`](./a2a-native-specs/) — Agent-native twin of every production specification
- **Builder Education**: [`onboarding/user-education/`](./onboarding/user-education/) — Gamified zero-shot education, builder toolkit, architecture patterns, use case scenarios
- **Research Onboarding**: [`onboarding/research/`](./onboarding/research/) — Context maps, research frontiers, methodology, expansion guides

## Integration

### Specification-Driven Development

Edge-Native is designed as the **single source of truth** for building NEXUS systems. Integration follows a strict spec-first methodology:

```
┌──────────────────────────────────────────────────────────────┐
│  SPEC-FIRST BUILD METHODOLOGY                                │
│                                                              │
│  1. READ SPEC    ──►  specs/firmware/reflex_bytecode_vm_spec.md
│  2. WRITE CODE   ──►  firmware/nexus_vm/vm_core.c
│  3. WRITE TESTS  ──►  tests/firmware/test_vm_opcodes.c
│  4. VERIFY       ──►  python -m pytest tests/ -v
│  5. DEPLOY       ──►  tools/flash.sh <port>
│                                                              │
│  ⚠  If code disagrees with spec → spec wins. File issue.    │
└──────────────────────────────────────────────────────────────┘
```

### Firmware Integration (ESP32-S3)

The `firmware/` directory is a complete ESP-IDF project ready for `idf.py build`:

```bash
# Set up ESP-IDF v5.3+
. $HOME/esp/esp-idf/export.sh

# Build
cd firmware && idf.py -p /dev/ttyUSB0 -b 921600 flash monitor

# Run firmware unit tests (Unity framework)
cd tests/unit/firmware && make test
```

### Jetson SDK Integration (Python)

The `jetson/` directory provides the Python SDK for the cognitive tier:

```bash
cd jetson
pip install -r requirements.txt

# Run main entry point
python -m main.nexus_main

# Components
python -c "from jetson.nexus_sdk import __version__; print(__version__)"  # v0.1.0
```

### Shared Bytecode Interface

The `shared/bytecode/` directory provides C and Python definitions used by both firmware and SDK:

```c
// shared/bytecode/opcodes.h — C enum for all 32 core + 29 A2A opcodes
// shared/bytecode/instruction.h — 8-byte instruction format struct
```

```python
# shared/bytecode/opcodes.py — Python enum mirroring C definitions
```

### Configuration Schemas

JSON schemas in `schemas/` define validated configuration formats:

| Schema | Purpose |
|--------|---------|
| `schemas/post_coding/reflex_definition.json` | Reflex program definition for bytecode compilation |
| `schemas/post_coding/node_role_config.json` | Node role and capability assignment |
| `schemas/post_coding/serial_protocol.json` | Serial communication parameters |
| `schemas/post_coding/autonomy_state.json` | Autonomy level state representation |

### Vessel Platform Architecture

The `vessel-platform/` directory defines the complete marine vessel integration with 16 engineering documents covering ESP32 firmware architecture, Jetson cluster design, network topology, redundancy failover, and calibration procedures. See [`vessel-platform/`](./vessel-platform/) for the full architecture.

## Knowledge Base

A Wikipedia-grade encyclopedia of 27 articles (333,775 words) covering the full breadth of knowledge a NEXUS developer needs — from the history of programming languages to maritime navigation law, from the philosophy of consciousness to the specifications of the ESP32-S3.

**Start here**: [`knowledge-base/developer-guide/onboarding_guide.md`](./knowledge-base/developer-guide/onboarding_guide.md)

Key resources:
- [`knowledge-base/reference/nexus_glossary.md`](./knowledge-base/reference/nexus_glossary.md) — 310 terms with NEXUS context
- [`knowledge-base/reference/open_problems_catalog.md`](./knowledge-base/reference/open_problems_catalog.md) — 29 unsolved problems
- [`knowledge-base/reference/annotated_bibliography.md`](./knowledge-base/reference/annotated_bibliography.md) — 178 references
- [`knowledge-base/README.md`](./knowledge-base/README.md) — Full article index

## Key Numbers

| Metric | Value |
|--------|-------|
| Specification files | 21 |
| Total specification lines | ~19,200 |
| Architecture decision records | 28 |
| VM opcodes | 32 (+ 29 proposed A2A extensions) |
| Wire protocol message types | 28 (+ 12 proposed A2A extensions) |
| Error codes | 75 |
| MCU families evaluated | 13 |
| A2A research documents | 6 (45,191 words) |
| A2A-native Rosetta Stone specs | 8 (350K+ words) |
| Research onboarding docs | 4 (45,100 words) |
| A2A user education docs | 7 (78,500 words) |
| Human-readable summaries | 3 (26,800 words) |
| Total onboarding content | ~132,500 words |
| Target domains | 8 |
| Estimated build (3 devs, parallel) | 12 – 16 weeks |
| Fastest path to demo | 8 weeks |
| A2A migration path | 32 weeks (3 phases) |
| Knowledge base articles | 27 |
| Knowledge base words | ~334,000 |
| Glossary terms | 310 |
| Annotated references | 178 |
| Open problems cataloged | 29 |
| Budget | $2.6M over 36 months |
| Build phases | 6 phases, 20 sprints, 5 milestones |

## Compliance Targets

| Standard | Level | Domain |
|----------|-------|--------|
| IEC 61508 | SIL 1 | Functional safety |
| ISO 26262 | ASIL-B equivalent | Automotive |
| IEC 60945 | — | Marine environmental |
| ISO 13850 | E-Stop | Emergency stop |

## Reference Hardware

| Tier | Role | Hardware | Cost | Key Specs |
|------|------|----------|------|-----------|
| **1 — Limbs** | Real-time reflex execution | ESP32-S3 | $6–10/unit | 240MHz dual-core, 8MB PSRAM, 45 GPIO |
| **2 — Brains** | AI cognition & trust | Jetson Orin Nano Super | $249 | 40 TOPS INT8, 8GB LPDDR5 |

## License

This project is released under the terms of the included LICENSE file.

---

*"The Ribosome, Not the Brain" — NEXUS does not centralize intelligence. It distributes cognition to the periphery, letting each limb think, react, and learn.*

---

<img src="callsign1.jpg" width="128" alt="callsign">
