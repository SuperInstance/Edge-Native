# A2A-Native Specifications — The Rosetta Stone

## What Is This Directory?

This directory contains the **agent-native twin** of every specification in the `specs/` tree. Where the human specs describe the NEXUS platform for engineers who read English and write C, these A2A-native specs describe the *same platform* for LLM agents that read binary metadata and write bytecode.

Think of this as the **Rosetta Stone**: the same VM, the same wire protocol, the same safety system — expressed in the language that agents actually speak. An agent reading `bytecode_vm_a2a_native.md` can generate correct, safe, deployable bytecode without ever seeing a human-readable specification.

---

## The Two-Lens Architecture

```
┌─────────────────────────────────────┐
│          HUMAN SPEC LENS            │
│       (specs/ directory)            │
│                                     │
│  • Written in Markdown prose        │
│  • Read by human engineers          │
│  • Explains "what the machine does" │
│  • Opcode definitions in tables     │
│  • Safety analysis in English       │
│  • Compiler targets: GCC, clang     │
│  • Audience: C/Rust developers      │
└────────────────┬────────────────────┘
                 │
                 │  Describes the same
                 │  physical machine
                 │
┌────────────────┴────────────────────┐
│        A2A-NATIVE SPEC LENS         │
│    (a2a-native-specs/ directory)    │
│                                     │
│  • Written in structured metadata   │
│  • Read by LLM agents               │
│  • Explains "what it means"         │
│  • Opcode semantics with intent     │
│  • Safety as provable invariants    │
│  • Compiler targets: agents         │
│  • Audience: Qwen, Claude, GPT      │
└─────────────────────────────────────┘
```

### Key Differences in Perspective

| Dimension | Human Spec (`specs/`) | A2A-Native Spec (`a2a-native-specs/`) |
|---|---|---|
| **Opcode meaning** | "Pops two floats, pushes sum" | "Safe to generate when both TOS values are known IEEE 754 floats. Trust-neutral. No capability requirement. No side effects." |
| **Safety errors** | "Trigger ERR_STACK_UNDERFLOW and HALT" | "Agent must verify SP >= 2 before emitting. If violated, VM halts all actuators to safe positions. Trust impact: irreversible failure." |
| **Program structure** | "Sequential bytecode with jump targets" | "Intention block: DECLARE_INTENT → CAPABILITY_SCOPE → TRUST_CONTEXT → BODY → VERIFICATION → FAILURE_NARRATIVE" |
| **Correctness** | "Matches human-written specification" | "Achieves declared intention within declared safety envelope" |
| **Validation** | "Compile-time validator pass" | "6-step agent validation pipeline with cross-model verification" |

---

## How to Read Both Versions Side by Side

For the bytecode VM:

| Section | Human Spec Location | A2A-Native Spec Location |
|---|---|---|
| Philosophy & Design Goals | `specs/firmware/reflex_bytecode_vm_spec.md` §1 | `bytecode_vm_a2a_native.md` §1 (Design Rationale for Agents) |
| All 32 Opcodes (mechanical) | Human spec §2.3 | A2A spec §2 (same opcodes, agent-interpreted semantics) |
| Instruction Encoding | Human spec §3 | A2A spec §3 (includes AAB TLV metadata trailer) |
| Memory & Execution Model | Human spec §4–§5 | A2A spec §4 (agent-visible state) |
| Safety Invariants | Human spec §6 | A2A spec §6 (validated as provable properties) |
| Syscalls (HALT, PID, etc.) | Human spec §2.5 | A2A spec §2 (syscall semantics for agents) |
| AAB Format | Not in human spec | A2A spec §3 (complete TLV tag registry) |
| 29 New Agent-Native Opcodes | Not in human spec | A2A spec §4 (intent, communication, capability, safety) |
| Intention Block Structure | Not in human spec | A2A spec §5 (agent-native program organization) |
| Example Programs | Not in human spec | A2A spec §7 (5 complete AAB examples with hex dumps) |
| Agent Validation Pipeline | Not in human spec | A2A spec §8 (6-step cross-agent verification) |

---

## The Compiler-Interpreter Hybrid

The NEXUS A2A-native system is neither purely compiled nor purely interpreted — it is a **compiler-interpreter hybrid** that operates across four distinct layers:

### Layer 1: Agent as Compiler Frontend

An LLM agent (Qwen2.5-Coder-7B, Claude 3.5 Sonnet, GPT-4o) receives a natural-language intention and compiles it into Agent-Annotated Bytecode (AAB). The agent's system prompt acts as the compiler's optimization passes:

| System Prompt Section | Compiler Analogue |
|---|---|
| JSON output schema | Lexer/parser specification |
| Available sensors list | Symbol table |
| Safety rules | Constraint optimization pass |
| Few-shot examples | Template-based code generation |
| Trust level requirements | Target platform constraints |

### Layer 2: Cross-Agent Validation

A *different* agent model independently verifies the generated AAB. This separation (generation by one model, validation by another) catches 93.3% of safety issues — versus 70.6% when the same model self-validates.

### Layer 3: Deterministic Compilation

A deterministic C compiler strips the AAB metadata trailer, producing the 8-byte fixed-width core bytecode that the ESP32 VM executes. This step takes ~1ms and is fully deterministic.

### Layer 4: Hardware Interpreter

The ESP32 VM interprets the stripped bytecode at 1 kHz. Every instruction has a fixed cycle count. The VM enforces stack depth, jump bounds, cycle budgets, and actuator clamping as hardware-level safety guarantees.

```
Human Intent
    ↓
[Agent Compiler] → AAB (agent-readable, with metadata)
    ↓
[Cross-Agent Validator] → Verified AAB
    ↓
[Deterministic Stripper] → 8-byte core bytecode
    ↓
[COBS + CRC-16 + RS-422] → ESP32 VM executes
```

---

## Ground Truth: Connecting Directly to Application Function

The A2A-native specs establish **ground truth** — a direct, unambiguous mapping from intention to physical effect:

1. **Intention** (`DECLARE_INTENT`): "Maintain heading 270° when wind < 20 knots"
2. **Capability requirements** (`REQUIRE_CAPABILITY`): compass sensor, rudder actuator, wind speed sensor
3. **Trust context** (`TRUST_CHECK`): steering subsystem trust ≥ 0.70
4. **Execution body**: READ_PIN compass → READ_PIN setpoint → PID_COMPUTE → CLAMP_F → WRITE_PIN rudder
5. **Verification** (`ASSERT_GOAL`): heading error < 5°
6. **Failure narrative** (`EXPLAIN_FAILURE`): "Wind exceeded 20 knots. Heading hold disengaged."

Every link in this chain is encoded in the bytecode itself — not in external documentation. An agent receiving this bytecode from another agent (possibly a different model, possibly on a different vessel) can verify the entire chain without any external context.

This is the fundamental property that makes the A2A-native specs **the definitive reference for agent-generated code**: the spec and the code are the same artifact.

---

## Swarm-of-Nodes Architecture

The NEXUS platform operates as a **swarm of intelligent nodes**, and the A2A-native specs are designed for this architecture:

### Vessel-Internal Swarm

```
┌─────────────────────────────────────────────────┐
│                Jetson Orin Nano                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Agent A  │ │ Agent B  │ │ Agent C  │        │
│  │ Qwen     │ │ Claude   │ │ GPT      │        │
│  │ Generator│ │ Validator│ │ Planner  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │  AAB shared via │  Redis/gRPC          │
│       └────────────────┘                        │
│                    ↓                             │
│         Strip → Deploy → Verify                  │
│                    ↓                             │
│              RS-422 Bus                          │
├─────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ ESP32 #1 │ │ ESP32 #2 │ │ ESP32 #3 │        │
│  │ Nav Ctrl │ │ Engine   │ │ Payload  │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
```

Each ESP32 node receives bytecode compiled by agents running on the Jetson. Different agents may compile bytecode for different nodes. The AAB format ensures that any agent can read, verify, and modify bytecode targeted at any node.

### Fleet-Wide Swarm

Across vessels, agents communicate via the **TELL**, **ASK**, and **DELEGATE** opcodes (0x30–0x32):

- **TELL**: Broadcast information (e.g., "vessel 7 is at heading 180°")
- **ASK**: Request information (e.g., "what is the wind forecast at position X?")
- **DELEGATE**: Assign sub-tasks (e.g., "vessel 3: take station-keeping position at waypoint B")

These inter-vessel communications are encoded as AAB bytecode and validated by each receiving agent before execution.

### Trust Propagation

Trust scores propagate through the swarm:
- Individual node performance → node trust score
- Node trust scores → subsystem trust scores
- Subsystem trust scores → vessel-level trust
- Vessel trust → fleet trust

The A2A-native specs define how trust scores gate bytecode execution: an intention requiring trust level 3 (CONDITIONAL) will not execute on a subsystem with trust < 0.70.

---

## File Index

| File | Counterpart Human Spec | Description |
|---|---|---|
| `README.md` | — | This file — explains the Rosetta Stone concept |
| `bytecode_vm_a2a_native.md` | `specs/firmware/reflex_bytecode_vm_spec.md` | Complete A2A-native VM specification |

Future specs to be added:
- `wire_protocol_a2a_native.md` ← `specs/protocol/wire_protocol_spec.md`
- `safety_system_a2a_native.md` ← `specs/safety/safety_system_spec.md`
- `trust_score_a2a_native.md` ← `specs/safety/trust_score_algorithm_spec.md`

---

## Document Conventions

- **Core instruction**: The 8-byte fixed-width format that the ESP32 VM executes
- **AAB instruction**: Core instruction + variable-length TLV metadata trailer
- **Stripping**: The deterministic removal of metadata from AAB to produce core-only bytecode
- **Intention block**: The fundamental unit of agent-native programs (replaces functions/classes)
- **Trust gate**: A runtime check that prevents execution if trust score is below threshold
- **Safety class**: CRITICAL, NORMAL, or DEGRADED — classifies the safety impact of an operation
- **Generation agent**: The agent that compiles intent into AAB
- **Validation agent**: A *different* agent model that independently verifies the AAB

---

*These specifications are the living language definition for all NEXUS agents. When this document changes, the behavior of all agents changes. Treat every edit with the gravity of a compiler patch.*
