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
├── v31-docs/                # v3.1 documentation set
├── addenda/                 # Engineering addenda (pitfalls, checklists, playbooks)
├── schemas/                 # JSON schemas for configuration
└── archives/                # Complete project zip archives
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Specification files | 21 |
| Total specification lines | ~19,200 |
| Architecture decision records | 28 |
| VM opcodes | 32 |
| Wire protocol message types | 28 |
| Error codes | 75 |
| MCU families evaluated | 13 |
| Estimated build (3 devs, parallel) | 12 – 16 weeks |
| Fastest path to demo | 8 weeks |

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
