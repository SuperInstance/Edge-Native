# Onboarding — NEXUS Project

> Comprehensive onboarding material for two distinct audiences: AI research agents continuing work, and A2A user/builder agents encountering the platform for the first time.

---

## Purpose

This directory contains the complete onboarding suite for the NEXUS distributed intelligence platform. The material is split between two subdirectories serving different audiences:

| Directory | Audience | Purpose |
|-----------|----------|---------|
| `research/` | AI research agents | Deep context, research topology, methodology, and expansion guides for continuing NEXUS research |
| `user-education/` | A2A user and builder agents | Zero-shot gamified education for understanding and building with the NEXUS platform |

---

## `research/` — For AI Research Agents

Deep onboarding material designed for AI agents that need full intellectual context to continue research on the NEXUS project. Read these if you are picking up where a previous agent left off, extending a research thread, or beginning work on one of the 29 open problems.

### Files

| File | Words | Description |
|------|------:|-------------|
| `context-map.md` | ~9,500 | Complete intellectual map of the NEXUS project: Project Genome, Document Atlas, Research Topology (15 threads), Concept Dependency Graph, and Where We Left Off. Start here. |
| `research-frontiers.md` | ~12,400 | Expanded assessment of all 29 open problems, 10 frontier research directions, a methodology guide, cross-pollination map, and a 12-month priority research roadmap. |
| `methodology.md` | ~7,500 | Operating manual for NEXUS research agents: agent identity, extension protocols, evidence hierarchy (L1–L7), research patterns (7 reusable templates), quality gates, communication protocols, and iteration handoff procedures. |
| `expansion-guide.md` | ~15,500 | Deep continuation guide for Iteration 2+ research: 15 thread deep-dives with critical open questions, 10 frontier briefs, a dependency DAG, a 10-agent assignment plan, and a cross-iteration continuity protocol. |

**Subtotal: ~45,100 words.**

### Reading Order

1. `context-map.md` — orient yourself to the full project
2. `methodology.md` — learn the conventions and quality standards
3. `research-frontiers.md` — understand what's open and frontier directions
4. `expansion-guide.md` — begin deep work on specific threads

---

## `user-education/` — For A2A User and Builder Agents

Gamified, zero-shot education material designed for AI agents encountering NEXUS for the first time. No prerequisites beyond general agent capability. Read these if you want to understand what NEXUS is, how it works, and how to build with it.

### Files

| File | Words | Description |
|------|------:|-------------|
| `gamified-intro.md` | ~7,900 | Provocative zero-shot introduction: the Three Revelations (System Prompt as Compiler, Hardware as Capability Boundary, Trust as Permission System), 10 redefined buzzwords, 5 concrete application scenarios, and 10 challenge-mode questions to test understanding. |
| `concept-playground.md` | ~11,800 | Interactive exploratory document using cooking analogies (Bytecode Kitchen), river ecosystems (Trust as River), theatrical scripts (Agent Conversation Theater), simulation thought experiments, and a gamified Progression Ladder to make concepts tangible. |
| `builder-education.md` | ~12,100 | Complete 8-module builder curriculum: bytecode fundamentals, Agent-Annotated Bytecode (AAB) construction, safety-first code generation, trust-aware deployment strategy, agent communication protocols (TELL/ASK/DELEGATE), capability negotiation, cross-validation pipeline, and full subsystem architecture design. Includes 10 exercises, complete opcode reference, and 15 anti-patterns. |
| `architecture-patterns.md` | ~16,700 | Pattern catalog of 25 architectural patterns across 5 categories (Core Execution, Agent Communication, Safety, Swarm Intelligence, Post-Coding), each with concrete bytecode, protocol messages, and marine examples. |
| `use-case-scenarios.md` | ~12,100 | 10 detailed A2A use case scenarios across diverse domains: smart homes, autonomous delivery fleets, surgical robotics, agricultural swarms, factory automation, deep-sea mining, smart grids, healthcare monitoring, disaster response, and creative industries. |

**Subtotal: ~60,700 words.**

### Reading Order

1. `gamified-intro.md` — the hook; establishes the paradigm shift
2. `concept-playground.md` — make concepts tangible through analogies
3. `builder-education.md` — learn to build with NEXUS
4. `architecture-patterns.md` — reference catalog for system design
5. `use-case-scenarios.md` — see NEXUS applied to real-world problems

---

## Statistics

| Category | Documents | Words |
|----------|----------:|------:|
| Research onboarding | 4 | ~45,100 |
| User education | 5 | ~60,700 |
| **Total** | **9** | **~105,800** |

---

## How This Connects to the Rest of the Repo

This onboarding suite sits at the top of the NEXUS documentation hierarchy. It references and contextualizes three other major directories:

- **`knowledge-base/`** — The 27-article, ~334K-word encyclopedia. Research agents use it as the theoretical foundation; user education documents assume it as deeper reference material.
- **`a2a-native-language/`** — The 6-document, ~45K-word A2A research corpus. The `research/` files reference it extensively; the `user-education/` files build on its Three Pillars and 29 proposed opcodes.
- **`specs/`** — The production specification suite (~19,200 lines). All patterns, bytecode examples, and trust parameters in user education documents reference these specs as ground truth.

For the full project context, read [[claude.md]] first, then return here.
