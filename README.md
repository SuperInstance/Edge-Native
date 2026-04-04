# NEXUS — Edge-Native Distributed Intelligence Platform

> The Post-Coding Age of Industrial Robotics. No human writes, reads, or debugs code.

![NEXUS](docs/NEXUS_Platform_Presentation.pptx)

## Overview

NEXUS is a production-ready specification for a **distributed intelligence system** designed for general-purpose industrial robotics. Instead of humans writing code, operators wire hardware, describe intent in natural language, demonstrate desired behaviors, and approve or reject AI-generated proposals. The system learns from observation, synthesizes reflexes, validates them through A/B testing, and progressively earns trust to operate with increasing autonomy.

## Architecture

Three-tier, hardware-agnostic design:

| Tier | Hardware | Role | Latency |
|------|----------|------|---------|
| **1 — Reflex** | ESP32-S3 MCU | Real-time sensor polling, bytecode VM execution, safety enforcement | 10µs – 1ms |
| **2 — Cognitive** | NVIDIA Jetson Orin Nano | AI inference, NLP chat, pattern discovery, reflex compilation | 10 – 500ms |
| **3 — Cloud** | Starlink / 5G | Heavy training, simulation, fleet management | seconds – hours |

Each tier operates independently. Tier 1 maintains control even when all higher tiers fail.

## Key Specifications

- **Wire Protocol**: RS-422, COBS framing, CRC-16, 28 message types, 921,600 baud
- **Bytecode VM**: 32 opcodes, 8-byte instructions, ~3 KB footprint, <100µs per tick
- **Safety System**: 4-tier defense-in-depth (hardware interlock → firmware ISR → supervisory task → application)
- **Autonomy**: INCREMENTS framework with 6 levels per subsystem, 25:1 trust loss-to-gain ratio
- **Learning**: 5 pattern discovery algorithms (cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference)
- **Cross-Domain**: Marine, agriculture, HVAC, factory automation, mining, aerospace, healthcare

## Repository Structure

```
├── docs/                    # Reports, presentations, overviews
├── specs/                   # Phase 1 production specifications
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
│   ├── round5_synthesis/    # Universal synthesis
│   ├── companion_docs/      # Non-technical guide + senior engineer deep dive
│   ├── addenda/             # Debate transcripts, multilingual summaries
│   └── figures/             # Simulation data & charts
├── framework/               # Core framework design documents
├── vessel-platform/         # Marine vessel platform architecture
├── autopilot/               # ESP32 autopilot engineering & simulations
├── genesis-colony/          # Earlier philosophical/architectural explorations
│   ├── round1-4/            # Iterative research rounds
│   ├── final/               # Final synthesis documents
│   └── phase2_discussions/  # Deep-dive discussions
├── knowledge-base/          # Encyclopedic knowledge base (333K words)
│   ├── foundations/         # History, VMs, biology, culture, paradigms
│   ├── theory/              # Agents, evolution, verification, synthesis, self-org, types
│   ├── philosophy/          # AI consciousness, trust psychology, post-coding
│   ├── systems/             # Embedded, distributed, robotics, edge AI, HW/SW co-design
│   ├── domains/             # Marine systems, maritime navigation history
│   ├── reference/           # Glossary (310 terms), frameworks, law, bibliography (178 refs)
│   └── developer-guide/     # Onboarding guide for new developers
├── a2a-native-language/     # A2A-native programming research (45K words)
├── a2a-native-specs/        # A2A-native Rosetta Stone twin specs
├── onboarding/              # Onboarding for research agents + A2A user education
│   ├── research/            # Deep context maps, frontiers, methodology (45K words)
│   └── user-education/      # Gamified intros, builder education, patterns (79K words)
├── human-readable/          # Plain-language summaries for non-technical readers (27K words)
├── worksheets-logs/         # Iteration worksheets, agent worklogs, session logs
├── claude-build/             # Build specifications for Claude Code (Claude Code starts here)
├── incubator/               # Edgeware Incubator — philosophy, manifesto, contribution guide
├── a2a-native-language/     # A2A-native programming research (45K words)
│   ├── language_design_and_semantics.md    # Language philosophy, 29 new opcodes, AAB format
│   ├── assembly_mapping_and_hardware_bridge.md  # Xtensa/ARM64 mapping, unfiltered transfer
│   ├── nexus_integration_analysis.md      # Backward compatibility, 12 wire protocol extensions
│   ├── agent_communication_and_runtime_model.md  # Agent protocol, equipment runtime, vessel model
│   ├── cross_domain_a2a_applicability.md  # 8-domain analysis, regulatory, trust calibration
│   └── final_synthesis.md                 # Grand thesis, Three Pillars, 36-month roadmap
├── v31-docs/                # v3.1 documentation set
├── addenda/                 # Engineering addenda (pitfalls, checklists, playbooks)
├── schemas/                 # JSON schemas for configuration
└── archives/                # Complete project zip archives
```

## Build the System

[**roadmap.md**](./roadmap.md) — Master build plan: 6 phases, 20 sprints, 5 milestones, $2.6M over 36 months.

[**claude-build/**](./claude-build/) — Component-by-component build specification for Claude Code. Struct definitions, opcode implementations, test vectors, the works.

**Quick start for Claude Code:** Read `claude.md` → `roadmap.md` → `claude-build/build-specification.md` → start with Phase 0 Sprint 0.1.

## Edgeware Incubator

NEXUS is the reference implementation for the [Edge-Native Edgeware Incubator](./incubator/) — a framework for designing, building, and evolving edge-native AI systems. Read the [manifesto](./incubator/manifesto.md) for the 10 principles.

---

## A2A-Native Programming

NEXUS extends its bytecode VM into an **agent-first programming paradigm** where LLM agents are the primary authors, interpreters, and validators of control code. With the right system prompt (compiler), runtime (equipment), and hardware (vessel), any agent can actualize a user's intention directly to the capability of the underlying hardware.

- **Research**: [`a2a-native-language/`](./a2a-native-language/) — 45,000-word research corpus (language design, hardware bridge, integration, communication, cross-domain, synthesis)
- **Rosetta Stone**: [`a2a-native-specs/`](./a2a-native-specs/) — Agent-native twin of every production specification
- **Builder Education**: [`onboarding/user-education/`](./onboarding/user-education/) — Gamified zero-shot education, builder toolkit, architecture patterns, use case scenarios
- **Research Onboarding**: [`onboarding/research/`](./onboarding/research/) — Context maps, research frontiers, methodology, expansion guides

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

## Compliance Targets

| Standard | Level | Domain |
|----------|-------|--------|
| IEC 61508 | SIL 1 | Functional safety |
| ISO 26262 | ASIL-B equivalent | Automotive |
| IEC 60945 | — | Marine environmental |
| ISO 13850 | E-Stop | Emergency stop |

## Reference Hardware

- **Tier 1 (Limbs)**: ESP32-S3 — $6–10/unit, 240MHz dual-core, 8MB PSRAM, 45 GPIO
- **Tier 2 (Brains)**: NVIDIA Jetson Orin Nano Super — $249, 40 TOPS INT8, 8GB LPDDR5

## License

This project is released under the terms of the included LICENSE file.

---

*"The Ribosome, Not the Brain" — NEXUS does not centralize intelligence. It distributes cognition to the periphery, letting each limb think, react, and learn.*
