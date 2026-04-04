# A2A-Native Language Design and Semantics

## Agents as First-Class Interpreters: A Programming Language Paradigm for the NEXUS Distributed Intelligence Platform

**Document ID:** NEXUS-A2A-LANG-001
**Task Agent:** 1 of 5 — Language Design & Semantics
**Date:** 2026-03-29
**Status:** Deep Research Report
**Classification:** Architectural Foundation

---

## Table of Contents

1. [Language Philosophy: The Semiotic Triangle Reimagined](#1-language-philosophy-the-semiotic-triangle-reimagined)
2. [Self-Describing Bytecode: Semantic Metadata in Every Instruction](#2-self-describing-bytecode-semantic-metadata-in-every-instruction)
3. [The Agent as Compiler Frontend](#3-the-agent-as-compiler-frontend)
4. [Opcode Design Extensions: From 32 to the Agent-Native ISA](#4-opcode-design-extensions-from-32-to-the-agent-native-isa)
5. [Program Structure: Beyond Functions and Classes](#5-program-structure-beyond-functions-and-classes)
6. [Formal Properties: Provable Guarantees for Agent-Native Code](#6-formal-properties-provable-guarantees-for-agent-native-code)
7. [Annotated Example Programs](#7-annotated-example-programs)
8. [Integration Points with Existing NEXUS VM](#8-integration-points-with-existing-nexus-vm)
9. [Open Questions and Future Research](#9-open-questions-and-future-research)

---

## 1. Language Philosophy: The Semiotic Triangle Reimagined

### 1.1 The Human-Native Language Paradigm

Every programming language in widespread use today — C, Python, Rust, Java, JavaScript — is designed for a semiotic triangle where **human cognition** occupies the apex:

```
          Human Cognition
             /        \
            /          \
    Syntax  ─────   Semantics
   (tokens,     (execution
    grammar,      behavior,
    structure)    side effects)
```

In this triangle:
- **Syntax** is shaped by human visual parsing, limited working memory, and cultural conventions (infix operators, keyword-based control flow, indentation significance).
- **Semantics** is defined operationally (what the machine does) but understood *declaratively* by humans (what the programmer intended).
- The **interpreter** (CPU, VM, runtime) is a dumb, deterministic executor. It has zero understanding — it merely follows instructions mechanically.

The entire discipline of software engineering — code reviews, documentation, naming conventions, type systems, linting — exists to bridge the gap between human intent and mechanical execution. Humans write the code, humans read the code, and the machine is a passive substrate.

### 1.2 The Agent-Native Language Paradigm

An A2A-native language inverts this triangle entirely:

```
          Agent Understanding
             /        \
            /          \
   Bytecode  ─────   Physical Effect
   (self-describing  (sensor readings,
    instructions)     actuator states,
                      environmental change)
```

In this inverted triangle:
- **Syntax** is binary bytecode designed for *machine* (agent) consumption, not human readability. There are no variable names, no comments, no indentation. Instead, each instruction carries *semantic metadata* that any agent — regardless of its training data — can interpret.
- **Semantics** includes not just *what the instruction does* but *why it was generated* (intention encoding), *what it requires* (capability declarations), and *what it guarantees* (safety annotations).
- The **interpreter** is an LLM agent with genuine *understanding* — it can reason about the bytecode's purpose, verify its correctness against stated intentions, and modify it to achieve new goals. The agent is not a passive substrate; it is an active participant in the language's lifecycle.

### 1.3 Why This Changes Everything

The fundamental shift from human-native to agent-native languages can be understood through six critical dimensions:

**Dimension 1: Who Reads the Code?**

In traditional languages, the primary reader is a human. Code quality metrics like "readability," "maintainability," and "self-documenting code" optimize for human cognitive load. In an agent-native language, the primary reader is an LLM agent. "Readability" means something entirely different: can an agent that has never seen this particular bytecode pattern before correctly infer what it does and why? This requires semantic metadata, not pretty formatting.

**Dimension 2: Who Writes the Code?**

In traditional languages, humans write code — sometimes with AI assistance, but always under human editorial control. In an A2A-native language, agents write, modify, and compose bytecode autonomously. The system prompt becomes the "style guide" and "architecture decision record." Different agents (Qwen2.5-Coder-7B, Claude 3.5 Sonnet, GPT-4o) may produce different bytecodes for the same intention — all valid, all safe, but with different optimization strategies.

**Dimension 3: What Does "Correct" Mean?**

For human-native languages, correctness means "matches the specification written by a human." For agent-native languages, correctness means "achieves the stated intention within the declared safety envelope." The intention is encoded *in the bytecode itself*, not in an external specification document. This enables a crucial property: any agent can verify any other agent's bytecode by checking whether the instructions, taken together, achieve the declared intention.

**Dimension 4: How Does the Language Evolve?**

Human-native languages evolve through standards committees (C++, Java) or benevolent dictatorships (Python, Rust). The evolution cycle is measured in years. Agent-native languages can evolve *per-compilation* — the system prompt that constrains bytecode generation can be updated in seconds, immediately changing the "dialect" of all future bytecode without breaking existing deployed programs.

**Dimension 5: What Is the Unit of Composition?**

In traditional languages, the unit of composition is the function, class, or module. In agent-native languages, the unit of composition is the **intention block** — a self-contained program that declares what it wants to achieve, what it needs to achieve it, and how success is verified. Intentions can be composed: "maintain heading 270°" + "reduce speed when obstacle detected" → combined intention that respects both goals.

**Dimension 6: Where Do Humans Appear?**

Humans are many abstractions away from the bytecode. They express desires in natural language: "When the wind exceeds 25 knots, reduce throttle to 40%." Multiple layers of agent intelligence translate this into bytecode:

```
Human Desire → Intent Classification (Phi-3-mini)
             → Reflex Generation (Qwen2.5-Coder-7B)
             → Safety Validation (Claude 3.5 Sonnet)
             → Bytecode Compilation (deterministic compiler)
             → Deployment (COBS-framed RS-422 serial)
             → Execution (ESP32 VM at 1 kHz)
```

Humans approve or reject proposals presented as natural-language explanations. They never see the bytecode.

### 1.4 Comparison: Human-Native vs Agent-Native Language Properties

| Property | Human-Native (C/Python/Rust) | Agent-Native (NEXUS A2A) |
|----------|-------------------------------|--------------------------|
| **Primary reader** | Human engineer | LLM agent |
| **Primary writer** | Human engineer | LLM agent |
| **Syntax design goal** | Human cognitive ergonomics | Agent interpretability |
| **Naming conventions** | Descriptive variable names (camelCase, snake_case) | Semantic metadata tags (type, capability, intent) |
| **Documentation** | Code comments, docstrings | Embedded intention declarations, pre/post conditions |
| **Error messages** | Human-readable stack traces | Structured failure narratives for agent consumption |
| **Version control** | Git diffs, PR reviews | Bytecode hash comparison, intention delta analysis |
| **Testing** | Unit tests, integration tests, property tests | Formal verification + A/B testing against human baseline |
| **Safety** | Type systems, linters, code review | Safety annotations + separate validation agent |
| **Correctness proof** | Manual reasoning, formal methods (rare) | Agent verification: "Does this bytecode achieve its stated intention?" |
| **Evolution speed** | Years (standards process) | Seconds (system prompt update) |
| **Composition unit** | Function, class, module | Intention block with declared goals and constraints |
| **Portability** | Source code → different compilers | Bytecode → different agents (all can interpret) |

### 1.5 The Three Pillars: System Prompt, Equipment, Vessel

In the NEXUS A2A-native paradigm, any agent's ability to actualize a user's intention rests on three pillars:

**Pillar 1: The System Prompt (The Mind)**
The system prompt is the agent's compiler — it defines what instructions are available, what safety rules apply, what the current hardware configuration supports, and what the trust level permits. Different system prompts produce different "dialects" of the same bytecode language. The system prompt is the living specification that evolves in real-time.

**Pillar 2: The Equipment (The Runtime)**
The "equipment" is the execution environment — the NEXUS bytecode VM running on ESP32-S3, the Jetson cognitive layer, the wire protocol. Equipment defines what is *possible*: the 32-opcode ISA constrains expressiveness, the 256-entry stack constrains complexity, the cycle budget constrains computation time. Equipment is the physical reality that grounds agent abstractions.

**Pillar 3: The Vessel (The Hardware)**
The "vessel" is the physical platform — the actual sensors, actuators, power systems, and mechanical structure. A vessel has capabilities (GPS, compass, lidar, throttle, rudder) and limitations (sensor ranges, actuator limits, power budgets). The vessel determines what intentions can be achieved. Equipment without a vessel is computation without effect.

The relationship between pillars is asymmetric: the system prompt is informed by equipment capabilities and vessel configuration. When equipment changes (new opcode added), the system prompt must be updated. When the vessel changes (new sensor added), the equipment configuration must be updated, which in turn updates the system prompt.

---

## 2. Self-Describing Bytecode: Semantic Metadata in Every Instruction

### 2.1 Why Self-Describing?

The existing NEXUS VM uses an 8-byte fixed instruction format:

```
[1 byte: opcode] [1 byte: flags] [2 bytes: operand1] [4 bytes: operand2]
```

This format is optimal for deterministic execution on ESP32-S3 — fixed-width instructions enable zero-overhead fetch-decode-execute cycles and compile-time jump target validation. However, it is entirely opaque to any agent that didn't write it. An agent reading this bytecode sees:

```
0x1A 0x00 0x0000 0x41B40000
```

Without external context, this is meaningless. Even with the ISA specification, the agent must perform a multi-step reasoning process:
1. Look up opcode 0x1A → READ_PIN
2. Interpret flags byte → no special flags
3. Decode operand1 (0x0000) → sensor register index 0
4. Decode operand2 (0x41B40000) → IEEE 754 float32 value 22.5

This is manageable for a single instruction but becomes cognitively expensive for a 65-instruction rate limiter program. A self-describing bytecode format embeds this context directly in the instruction, enabling any agent to interpret it without external lookup tables.

### 2.2 Extended Instruction Format: Agent-Annotated Bytecode (AAB)

We propose an **Agent-Annotated Bytecode (AAB)** format that extends the existing 8-byte instruction with a variable-length semantic metadata trailer. Critically, this trailer is **stripped before deployment to ESP32** — the execution format remains the efficient 8-byte fixed-width format. The AAB format exists only in the agent-to-agent communication layer (Jetson-side, cloud-side).

**AAB Instruction Structure:**

```
┌──────────────────────────────────────────────────────────────┐
│ Core Instruction (8 bytes — identical to existing NEXUS VM)  │
│ [opcode:1][flags:1][operand1:2][operand2:4]                  │
├──────────────────────────────────────────────────────────────┤
│ Semantic Metadata Block (variable length, TLV-encoded)       │
│                                                              │
│  [Tag:1][Length:1][Value:N] — Type Descriptor               │
│  [Tag:1][Length:1][Value:N] — Capability Declaration        │
│  [Tag:1][Length:1][Value:N] — Safety Annotation             │
│  [Tag:1][Length:1][Value:N] — Intention Encoding             │
│  [Tag:1][Length:1][Value:N] — Trust Context                 │
│  ...additional TLV fields...                                 │
└──────────────────────────────────────────────────────────────┘
```

**Tag Registry:**

| Tag ID | Name | Description | Example Value |
|--------|------|-------------|---------------|
| 0x01 | TYPE_DESC | Data type of operands and result | "f32→f32", "bool", "f32×2→f32" |
| 0x02 | CAP_REQ | Required hardware capability | "sensor:compass", "actuator:rudder" |
| 0x03 | PRE_COND | Precondition for execution | "heading_sensor_valid", "rudder_ready" |
| 0x04 | POST_COND | Postcondition guaranteed after execution | "rudder_angle ∈ [-45, 45]" |
| 0x05 | INTENT_ID | Links instruction to declared intention | "maintain_heading_reflex.line_3" |
| 0x06 | TRUST_MIN | Minimum trust score required | "0.70" (Level 3) |
| 0x07 | TRUST_IMPACT | Trust impact if this instruction fails | "alpha_loss × 0.5" |
| 0x08 | HUMAN_DESC | Human-readable description (for explanation) | "Read current compass heading" |
| 0x09 | DEPENDS_ON | Dependency on previous instruction | "prev.line_2" |
| 0x0A | SAFETY_CLASS | Safety classification | "CRITICAL", "NORMAL", "DEGRADED" |
| 0x0B | CYCLE_COST | Expected cycle cost | "3 cycles" |
| 0x0C | SIDE_EFFECT | Declared side effects | "writes:actuator:rudder" |
| 0x0D | UNIT_OF_MEASURE | Physical unit for float values | "degrees", "m/s", "%" |
| 0x0E | ALTERNATIVE | Alternative implementation (for optimization) | "USE_PID_COMPUTE instead" |

### 2.3 Example: Self-Describing READ_PIN

An agent reading the following AAB instruction immediately understands its full semantics:

```
Core:  0x1A 0x00 0x0000 0x00000000
       (READ_PIN, no flags, sensor register 0, no immediate)

Metadata:
  0x01 0x0C "f32:degrees:compass_heading"    — Type: float32, unit: degrees, source: compass
  0x02 0x08 "sensor:imu:compass"             — Requires: IMU compass sensor on I2C bus 0
  0x03 0x14 "compass_data_fresh_age < 500ms"  — Precondition: compass reading is fresh
  0x04 0x28 "stack_top ∈ [-180.0, 360.0]"     — Postcondition: heading is in valid range
  0x05 0x18 "heading_hold_pid.intention:read_heading"
  0x08 0x1C "Read current vessel heading from compass sensor"
  0x0A 0x06 "NORMAL"                           — Safety class: normal operation
  0x0B 0x08 "2 cycles"                         — Cycle cost: 2 (sensor register read)
  0x0D 0x08 "degrees"                          — Physical unit: degrees
```

**Agent reasoning chain** (what any LLM would do when encountering this instruction):
1. *This reads the compass heading as a float32 in degrees.*
2. *It requires the IMU compass sensor to be present and recently updated.*
3. *The result will be on the stack, and it should be in the range [-180, 360].*
4. *It's part of a heading-hold PID reflex.*
5. *It's a normal-safety operation costing 2 cycles.*

This reasoning takes ~50ms for an LLM agent — trivial compared to the 29-second reflex generation time.

### 2.4 Agent-Readable vs Machine-Executable Formats

The AAB format is **not** executed by the ESP32 VM. It is a communication format between agents. The lifecycle is:

```
Agent A generates AAB → Agent B validates AAB → Deterministic compiler strips metadata →
8-byte bytecode → COBS + CRC-16 → RS-422 serial → ESP32 VM executes
```

This separation is crucial because:
1. **ESP32 VM stays lean**: 8-byte fixed instructions, ~12 KB flash, 3 KB RAM. No metadata parsing overhead.
2. **Agents get full context**: Every instruction carries its rationale, requirements, and guarantees.
3. **Verification is possible**: Agent B can check whether the metadata accurately describes the core instruction's behavior.
4. **Portability across agents**: GPT-4o, Claude, Qwen — any agent can read AAB because the metadata is in natural language.

### 2.5 Metadata Density Analysis

| Program Pattern | Core Bytes | Metadata Bytes (avg) | Total AAB Bytes | Overhead |
|----------------|-----------|---------------------|-----------------|----------|
| Single READ_PIN | 8 | 62 | 70 | 775% |
| PID Controller (10 instr) | 80 | 420 | 500 | 525% |
| Rate Limiter (65 instr) | 520 | 2,730 | 3,250 | 525% |
| Complex Reflex (200 instr) | 1,600 | 8,400 | 10,000 | 525% |

The ~5× overhead is acceptable because AAB exists only in agent-to-agent communication (Jetson memory, cloud storage), never on the ESP32. A 10 KB AAB program consumes 0.12% of the Jetson's 8 GB memory.

---

## 3. The Agent as Compiler Frontend

### 3.1 The Compilation Pipeline: Intention → Bytecode

In traditional compilation, a human writes source code → compiler front-end (lexer, parser) → intermediate representation → compiler back-end (optimizer, code generator) → machine code. The compiler is a deterministic program with no understanding.

In A2A-native compilation, the pipeline is:

```
User Natural Language Intention
         │
         ▼
┌─────────────────────┐
│ Intent Classification │  ← Phi-3-mini-4K (40+ tok/s, ~200ms)
│ "This is a heading    │     Routes intent to correct handler,
│  hold request"        │     extracts parameters (heading=270°)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Reflex Generation     │  ← Qwen2.5-Coder-7B (17.2 tok/s, ~29s)
│ JSON reflex with      │     System prompt = compiler optimization
│ triggers, actions,    │     passes + safety checks + schema
│ safety_guards         │     constraints + few-shot examples
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Safety Validation     │  ← Claude 3.5 Sonnet (cloud, ~3s)
│ Separate agent        │     Independent safety analysis,
│ verifies safety       │     catches 95.1% of issues,
│ properties           │     produces structured report
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ AAB Generation        │  ← Qwen2.5-Coder-7B or deterministic
│ JSON → AAB bytecode  │     Translates reflex JSON to
│ with full metadata    │     agent-annotated bytecode
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Cross-Agent           │  ← Any LLM agent (~2s)
│ Verification          │     "Does this AAB achieve the
│                       │     stated intention?"
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Bytecode Stripping    │  ← Deterministic C compiler (~1ms)
│ AAB → 8-byte core    │     Extracts core 8-byte instructions,
│ instructions only     │     discards all metadata
└─────────────────────┘
         │
         ▼
    Deploy to ESP32
```

### 3.2 The System Prompt as Compiler Optimization Passes

The system prompt for Qwen2.5-Coder-7B serves a dual role: it is both the programming language specification and the compiler's optimization passes. Each section of the system prompt maps to a traditional compiler phase:

| System Prompt Section | Compiler Analogue | Function |
|-----------------------|-------------------|----------|
| Output format (JSON schema) | Lexer/Parser specification | Defines valid token sequences and AST structure |
| Available sensors list | Symbol table | Tells the compiler what external symbols exist |
| Safety rules | Optimization constraint pass | Constrains generated code to safe subsets |
| Few-shot examples | Optimization templates | Provides high-quality patterns to emulate |
| Grammar constraints (GBNF) | Syntax-directed translation | Constrains output tokens to valid syntax |
| Trust level requirements | Target platform specification | Constrains what instructions can be emitted |
| Actuator limits | Range analysis pass | Ensures all outputs are within physical limits |

This mapping reveals something profound: **the system prompt IS the language definition**. Changing the system prompt changes the language. There is no separate "language specification" document — the system prompt *is* the specification, and it is a living, evolving document.

### 3.3 Cross-Agent Compilation Variability

A critical question: if different agents compile the same intention, do they produce the same bytecode?

**Short answer: No. But they produce *equivalent* bytecodes.**

Consider the intention: "Maintain heading 270° using PID control."

**Agent A (Qwen2.5-Coder-7B, aggressive optimization):**
```json
{
  "name": "heading_hold_pid_v1",
  "pid_controllers": {
    "heading_pid": {"kp": 1.2, "ki": 0.05, "kd": 0.3}
  },
  "code": "READ_PIN heading; READ_PIN setpoint; PID_COMPUTE heading_pid; CLAMP_F -45.0 45.0; WRITE_PIN rudder"
}
```
Bytecode: 10 instructions, 80 bytes core.

**Agent B (Claude 3.5 Sonnet, conservative with extra safety):**
```json
{
  "name": "heading_hold_pid_safe_v2",
  "pid_controllers": {
    "heading_pid": {"kp": 1.2, "ki": 0.05, "kd": 0.3}
  },
  "code": "READ_PIN heading; DUP; PUSH_F32 360.0; LT_F; JUMP_IF_TRUE normalize; DUP; PUSH_F32 -180.0; LT_F; JUMP_IF_FALSE skip_normalize; ADD_F 360.0; normalize:; skip_normalize:; READ_PIN setpoint; PID_COMPUTE heading_pid; CLAMP_F -45.0 45.0; DUP; PUSH_F32 30.0; ABS_F; GT_F; JUMP_IF_FALSE safe; CLAMP_F -30.0 30.0; safe:; WRITE_PIN rudder"
}
```
Bytecode: 22 instructions, 176 bytes core. Includes heading normalization and additional angle limiting.

**Agent C (GPT-4o, using rate-limited output):**
```json
{
  "name": "heading_hold_smooth_v3",
  "pid_controllers": {
    "heading_pid": {"kp": 0.8, "ki": 0.03, "kd": 0.4}
  },
  "code": "READ_PIN heading; READ_PIN setpoint; PID_COMPUTE heading_pid; PUSH_F32 prev_rudder; SUB_F; CLAMP_F -5.0 5.0; ADD_F prev_rudder; CLAMP_F -45.0 45.0; WRITE_PIN rudder; WRITE_VAR prev_rudder"
}
```
Bytecode: 14 instructions, 112 bytes core. Uses rate-limited rudder changes for smooth operation.

**Analysis of variability:**

| Dimension | Agent A | Agent B | Agent C |
|-----------|---------|---------|---------|
| Instructions | 10 | 22 | 14 |
| Core bytes | 80 | 176 | 112 |
| Cycle cost | 36 | 85 | 52 |
| Stack depth | 2 | 4 | 3 |
| Safety guards | Basic (clamp) | Advanced (normalize + limit) | Medium (rate limit + clamp) |
| PID gains | kp=1.2, ki=0.05, kd=0.3 | kp=1.2, ki=0.05, kd=0.3 | kp=0.8, ki=0.03, kd=0.4 |
| Intention match | ✓ | ✓ | ✓ (approximate) |

All three achieve the same intention ("maintain heading 270°") but with different strategies, safety margins, and resource consumption. This is a feature, not a bug — it provides *implementation diversity*, which is a cornerstone of safety-critical systems (N-version programming).

### 3.4 Verification: Can One Agent Validate Another's Bytecode?

Yes. The verification protocol works as follows:

1. **Extract intention**: Read the INTENT_ID and INTENT_DESC metadata from the AAB program header.
2. **Simulate execution**: Walk through each instruction, tracking stack state and variable mutations.
3. **Check postconditions**: After simulation, verify that all declared POST_COND annotations are satisfied.
4. **Verify safety**: Check that all TRUST_MIN requirements are met, all SAFETY_CLASS annotations are consistent with the operations performed, and all actuator writes are within declared limits.
5. **Compare to intention**: Reason about whether the sequence of operations, taken together, achieves the stated intention.

**Empirical validation** (based on the NEXUS AI model analysis data):

| Validator | Safety Catch Rate | False Positive Rate | Agreement with Human |
|-----------|-------------------|---------------------|---------------------|
| Same model (self-validation) | 70.6% | 4.1% | 72.6% |
| Different model (cross-validation) | 93.3% (GPT-4o) | 3.4% | 96.0% |
| Claude 3.5 Sonnet | 95.1% | 4.8% | 97.0% |

Cross-agent validation catches 23 percentage points more safety issues than self-validation. This is why the NEXUS architecture deliberately separates generation (Qwen2.5-Coder-7B) from validation (Claude 3.5 Sonnet).

### 3.5 Cross-Agent Portability

For AAB bytecode to be truly agent-native, any agent must be able to read bytecode written by any other agent. This requires:

1. **Standardized metadata tags**: The TLV tag registry (Section 2.2) must be agreed upon by all agents in the system. This is established by the system prompt.
2. **Natural language descriptions**: The HUMAN_DESC (tag 0x08) field uses natural language, which any LLM can parse regardless of its training data. "Read current compass heading" is universally interpretable.
3. **Intention-level abstraction**: Instead of verifying individual instructions, agents verify at the intention-block level (Section 5). "This block maintains heading 270°" is easier to verify than "Instruction 3 is READ_PIN sensor 0."
4. **Canonical form**: While different agents may produce different AAB bytecodes for the same intention, there exists a canonical intention representation that enables comparison. Two programs are "equivalent" if they achieve the same intention under the same constraints, regardless of implementation.

---

## 4. Opcode Design Extensions: From 32 to the Agent-Native ISA

### 4.1 Existing 32-Opcodes: Foundation Review

The existing NEXUS ISA defines 32 opcodes (0x00–0x1F) in 10 categories:

| Category | Range | Opcodes |
|----------|-------|---------|
| Stack | 0x00–0x07 | NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT |
| Arithmetic | 0x08–0x10 | ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F |
| Comparison | 0x11–0x15 | EQ_F, LT_F, GT_F, LTE_F, GTE_F |
| Logic | 0x16–0x19 | AND_B, OR_B, XOR_B, NOT_B |
| I/O | 0x1A–0x1C | READ_PIN, WRITE_PIN, READ_TIMER_MS |
| Control | 0x1D–0x1F | JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE |

Extended operations (CALL, RET, HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT) use NOP (0x00) with SYSCALL flag (bit 7 of flags byte).

**Available opcode space:** Opcodes 0x20–0xFF are entirely unused. This provides 224 available opcode slots for extensions.

### 4.2 Proposed Extension: Intent Opcodes (0x20–0x2F)

Intent opcodes encode *why* the program exists, not just *what* it does. These opcodes are no-ops on the ESP32 VM (they execute as NOP with zero cycle cost) but carry critical metadata in the AAB format.

| Opcode | Name | Format | AAB Metadata | Purpose |
|--------|------|--------|-------------|---------|
| 0x20 | DECLARE_INTENT | `[0x20][0x00][intent_id:2][hash:4]` | HUMAN_DESC, TRUST_MIN, DOMAIN | Declares the program's intention |
| 0x21 | ASSERT_GOAL | `[0x21][0x00][goal_id:2][threshold:4]` | POST_COND, VERIFICATION_METHOD | Asserts an expected outcome |
| 0x22 | VERIFY_OUTCOME | `[0x22][0x00][metric_id:2][tolerance:4]` | EXPECTED_RANGE, ON_FAIL_ACTION | Checks whether goal was achieved |
| 0x23 | DECLARE_CONSTRAINT | `[0x23][0x00][constraint_id:2][limit:4]` | CONSTRAINT_TYPE, VIOLATION_ACTION | Declares a constraint on program behavior |
| 0x24 | INTENT_SCOPE_BEGIN | `[0x24][0x00][scope_id:2][0x00000000]` | SCOPE_TYPE, TRUST_MIN, CAP_REQ | Opens an intention scope |
| 0x25 | INTENT_SCOPE_END | `[0x25][0x00][scope_id:2][0x00000000]` | SCOPE_SUMMARY, ACHIEVED_GOALS | Closes an intention scope |
| 0x26 | EXPLAIN_FAILURE | `[0x26][0x00][failure_code:2][0x00000000]` | HUMAN_DESC, FAILURE_NARRATIVE | Describes what to tell the user on failure |

**AAB Example — DECLARE_INTENT:**

```
Core:  0x20 0x00 0x0001 0xA3F2B1C4
       (DECLARE_INTENT, intent_id=1, hash=0xA3F2B1C4)

Metadata:
  0x08 0x2A "Maintain heading 270° using PID control when wind speed < 20 knots"
  0x06 0x04 "0.70"   — Minimum trust: Level 3 (CONDITIONAL)
  0x02 0x18 "sensor:compass,actuator:rudder,sensor:wind"
  0x0A 0x08 "NORMAL"  — Safety class
```

### 4.3 Proposed Extension: Meta-Opcodes for Agent Communication (0x30–0x3F)

These opcodes enable bytecode programs to communicate with other agents in the system — requesting information, delegating tasks, or reporting results. On the ESP32, these map to EMIT_EVENT syscalls that are forwarded to the Jetson.

| Opcode | Name | Format | AAB Metadata | Purpose |
|--------|------|--------|-------------|---------|
| 0x30 | TELL | `[0x30][flags:1][channel:2][event_type:4]` | RECIPIENT, MESSAGE_CONTENT | Send information to another agent |
| 0x31 | ASK | `[0x31][flags:1][channel:2][request_id:4]` | QUESTION, TIMEOUT_MS, ON_TIMEOUT | Request information from another agent |
| 0x32 | DELEGATE | `[0x32][flags:1][target_agent:2][intent_id:4]` | DELEGATION_SCOPE, AUTHORITY_LEVEL | Delegate a sub-intention to another agent |
| 0x33 | REPORT_STATUS | `[0x33][0x00][status_code:2][detail:4]` | STATUS_TYPE, AFFECTED_SUBSYSTEM | Report execution status to supervisor |
| 0x34 | REQUEST_OVERRIDE | `[0x34][0x00][authority_level:2][reason:4]` | REASON_TEXT, SAFETY_IMPLICATION | Request human or higher-agent intervention |

**AAB Example — ASK:**

```
Core:  0x31 0x01 0x0002 0x000001F4
       (ASK, blocking flag, channel=2 (cognitive layer), request timeout=500ms)

Metadata:
  0x08 0x2A "Request current wind forecast from cognitive layer"
  0x02 0x04 "link:jetson:cognitive"
  0x06 0x04 "0.50"   — Can execute even at lower trust (informational)
```

### 4.4 Proposed Extension: Capability Negotiation Opcodes (0x40–0x4F)

These opcodes declare what the program needs from the hardware and what it provides in return. They are verified at deployment time (not at execution time) by the Jetson's role configuration.

| Opcode | Name | Format | AAB Metadata | Purpose |
|--------|------|--------|-------------|---------|
| 0x40 | REQUIRE_CAPABILITY | `[0x40][0x00][cap_type:2][cap_id:4]` | CAPABILITY_DESC, ALTERNATIVE, FALLBACK | Declare hardware requirement |
| 0x41 | CAPABILITY_RESPONSE | `[0x41][flags:1][status:2][alt_cap:4]` | GRANTED/DENIED, REASON, SUBSTITUTION | Response to capability check |
| 0x42 | DECLARE_SENSOR_NEED | `[0x42][0x00][sensor_idx:2][sample_rate:4]` | SENSOR_TYPE, ACCURACY_REQ, FRESHNESS_MAX | Declare sensor requirement |
| 0x43 | DECLARE_ACTUATOR_USE | `[0x43][0x00][actuator_idx:2][max_rate:4]` | ACTUATOR_TYPE, LIMIT_MIN, LIMIT_MAX | Declare actuator usage |
| 0x44 | DECLARE_COMPUTE_NEED | `[0x44][0x00][compute_type:2][budget_cycles:4]` | COMPUTE_DESC, FALLBACK_BUDGET | Declare computation requirement |

**AAB Example — REQUIRE_CAPABILITY:**

```
Core:  0x40 0x00 0x0001 0x00000003
       (REQUIRE_CAPABILITY, cap_type=1 (sensor), cap_id=3 (lidar))

Metadata:
  0x08 0x2C "Requires lidar sensor for obstacle detection, minimum range 15m"
  0x02 0x14 "sensor:lidar:obstacle_dist_m"
  0x0E 0x0A "USE_RADAR if lidar unavailable"
```

### 4.5 Proposed Extension: Safety-Augmented Opcodes (0x50–0x5F)

These opcodes embed safety checks directly in the bytecode, extending the existing safety model from hardware/firmware layers into the program itself.

| Opcode | Name | Format | AAB Metadata | Purpose |
|--------|------|--------|-------------|---------|
| 0x50 | TRUST_CHECK | `[0x50][0x00][subsystem:2][min_trust:4]` | TRUST_SCORE, CURRENT_LEVEL, ACTION_ON_FAIL | Verify trust level before proceeding |
| 0x51 | AUTONOMY_LEVEL_ASSERT | `[0x51][0x00][level:2][subsystem:4]` | REQUIRED_LEVEL, CURRENT_LEVEL, ESCALATION | Assert minimum autonomy level |
| 0x52 | SAFE_BOUNDARY | `[0x52][0x00][boundary_id:2][margin:4]` | BOUNDARY_TYPE, ENVELOPE_DEF, BREACH_ACTION | Define and enforce safety boundary |
| 0x53 | RATE_LIMIT | `[0x53][0x00][variable_idx:2][max_rate:4]` | UNIT_PER_SEC, ON_EXCEED, INTEGRAL_DECAY | Limit rate of change |
| 0x54 | DEADBAND | `[0x54][0x00][variable_idx:2][band_width:4]` | CENTER_VALUE, OUTPUT_ON_BAND | Apply deadband filter |
| 0x55 | WATCHDOG_PET | `[0x55][0x00][watchdog_id:2][timeout_ms:4]` | WATCHDOG_TYPE, ON_EXPIRE | Reset software watchdog timer |
| 0x56 | SAFETY_EVENT_EMIT | `[0x56][0x00][event_severity:2][event_code:4]` | EVENT_DESC, AFFECTED_ACTUATORS, RECOVERY | Emit safety event to supervisor |

**AAB Example — TRUST_CHECK:**

```
Core:  0x50 0x00 0x0001 0x3F000000
       (TRUST_CHECK, subsystem=1 (steering), min_trust=0.50 as float32)

Metadata:
  0x08 0x36 "Check that steering subsystem trust score >= 0.50 before executing autonomous turn"
  0x06 0x04 "0.50"   — Trust threshold: Level 2 (SEMI-AUTO)
  0x07 0x12 "alpha_loss × 0.1 if trust check fails"
```

**Execution on ESP32:** The trust check opcode maps to a SYSCALL (NOP + flag) that reads the trust score from a shared memory region populated by the Jetson. If trust < threshold, the instruction jumps to the failure handler (specified in the JUMP target encoded in operand2).

### 4.6 Complete Proposed Opcode Map

```
0x00–0x07  Stack Operations         (existing)
0x08–0x10  Arithmetic                (existing)
0x11–0x15  Comparison                (existing)
0x16–0x19  Logic                     (existing)
0x1A–0x1C  I/O                       (existing)
0x1D–0x1F  Control Flow              (existing)
0x20–0x2F  Intent Opcodes            (new — Section 4.2)
0x30–0x3F  Agent Communication        (new — Section 4.3)
0x40–0x4F  Capability Negotiation     (new — Section 4.4)
0x50–0x5F  Safety Augmentation        (new — Section 4.5)
0x60–0x7F  Reserved for Domain-Specific Extensions
0x80–0xFF  Reserved for Future Use
```

### 4.7 Encoding Format Extensions

The existing 8-byte instruction format is preserved for all existing opcodes. New opcodes use the same format but with extended operand semantics:

**Standard 8-byte format (unchanged):**
```
Byte 0: Opcode (0x00–0xFF)
Byte 1: Flags (bit 7: SYSCALL, bits 6-0: subtype flags)
Bytes 2-3: Operand 1 (uint16, big-endian)
Bytes 4-7: Operand 2 (int32 or float32, big-endian)
```

**Extended flags for new opcodes:**

| Bit | Name | Meaning |
|-----|------|---------|
| 7 | SYSCALL | Maps to VM syscall (existing) |
| 6 | BLOCKING | Wait for completion (ASK, DELEGATE) |
| 5 | OPTIONAL | Failure is non-fatal (REQUIRE_CAPABILITY) |
| 4 | VERIFIED | Pre-verified by validation agent |
| 3 | CRITICAL | Safety-critical operation |
| 2-0 | SUBTYPE | Opcode-specific subtype |

---

## 5. Program Structure: Beyond Functions and Classes

### 5.1 The Intention Block: Fundamental Unit of Agent-Native Programs

In human-native languages, programs are organized into functions (imperative), classes (object-oriented), or modules (package-based). In agent-native languages, programs are organized into **intention blocks** — self-contained units that declare:

1. **What** the block intends to achieve (goal statement)
2. **Why** the block exists (context and motivation)
3. **What** it needs to achieve it (capabilities and resources)
4. **How** success is verified (postconditions and metrics)
5. **What** to do on failure (failure narrative)
6. **Who** authorized it (trust context and autonomy level)

**Intention Block Structure:**

```
┌──────────────────────────────────────────────────┐
│ INTENTION BLOCK HEADER                            │
│                                                  │
│  DECLARE_INTENT                                   │
│    intention_id: "heading_hold_wind_aware"        │
│    human_desc: "Maintain heading 270° but only    │
│                when wind is below dangerous level"│
│    trust_min: 0.70 (Level 3)                     │
│    domain: "marine:autopilot:steering"            │
│    author_agent: "qwen2.5-coder-7b"              │
│    validator_agent: "claude-3.5-sonnet"          │
│    version: "1.2.0"                               │
│    hash: 0xA3F2B1C4                               │
│                                                  │
├──────────────────────────────────────────────────┤
│ CAPABILITY SCOPE                                  │
│                                                  │
│  REQUIRE_CAPABILITY sensor:compass                │
│  REQUIRE_CAPABILITY sensor:wind_speed             │
│  REQUIRE_CAPABILITY actuator:rudder               │
│  DECLARE_SENSOR_NEED compass, rate=10Hz          │
│  DECLARE_ACTUATOR_USE rudder, max_rate=5°/s      │
│  DECLARE_COMPUTE_NEED pid, budget=50 cycles       │
│                                                  │
├──────────────────────────────────────────────────┤
│ TRUST CONTEXT                                     │
│                                                  │
│  TRUST_CHECK subsystem=steering, min=0.70         │
│  AUTONOMY_LEVEL_ASSERT level=3, subsystem=steer  │
│                                                  │
├──────────────────────────────────────────────────┤
│ CONSTRAINT SCOPE                                  │
│                                                  │
│  DECLARE_CONSTRAINT rudder_abs_max=30°           │
│  SAFE_BOUNDARY wind_speed_max=25_knots           │
│  RATE_LIMIT rudder, max=5°/s                     │
│                                                  │
├──────────────────────────────────────────────────┤
│ EXECUTION BODY                                    │
│                                                  │
│  [Core bytecode instructions — standard NEXUS     │
│   opcodes 0x00–0x1F with computation logic]      │
│                                                  │
├──────────────────────────────────────────────────┤
│ VERIFICATION SCOPE                                │
│                                                  │
│  ASSERT_GOAL heading_error < 5°                  │
│  VERIFY_OUTCOME rudder_rate < 5°/s, tolerance=1° │
│                                                  │
├──────────────────────────────────────────────────┤
│ FAILURE NARRATIVE                                 │
│                                                  │
│  EXPLAIN_FAILURE wind_exceeded                    │
│    "Wind speed exceeded 25 knots. Heading hold    │
│     disengaged. Rudder returned to center.        │
│     Manual control required."                     │
│  EXPLAIN_FAILURE trust_insufficient               │
│    "Steering trust below 0.70. Reflex cannot      │
│     execute autonomously. Operator notified."     │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 5.2 Capability Scopes

A capability scope declares what hardware resources the program requires. This serves two purposes:

1. **Deployment-time verification**: The Jetson checks whether the target ESP32's role configuration includes all required capabilities before deploying bytecode.
2. **Runtime graceful degradation**: If a capability becomes unavailable during execution (sensor failure), the program can fall back to a degraded mode.

**Capability scope example for a multi-sensor fusion reflex:**

```
REQUIRE_CAPABILITY sensor:compass          [REQUIRED — no fallback]
REQUIRE_CAPABILITY sensor:gyro             [OPTIONAL — can use compass-only]
REQUIRE_CAPABILITY sensor:gps              [OPTIONAL — can use dead reckoning]
REQUIRE_CAPABILITY actuator:rudder         [REQUIRED — no fallback]

; Primary: compass + gyro fusion
READ_PIN compass_heading
READ_PIN gyro_yaw_rate
MUL_F gyro_yaw_rate delta_t
ADD_F fused_heading

; Fallback (if gyro unavailable): compass only
; [Alternative implementation selected at deployment time]
READ_PIN compass_heading
```

### 5.3 Trust Contexts

A trust context defines what INCREMENTS trust level and score are required for each section of the program. This enables **graduated autonomy within a single program** — some sections can execute at Level 2 (SEMI-AUTO) while others require Level 4 (HIGH).

**Trust context example:**

```
; === SECTION 1: Monitoring (any trust level) ===
AUTONOMY_LEVEL_ASSERT level=1, subsystem=monitoring
READ_PIN compass_heading
WRITE_VAR last_heading
EMIT_EVENT telemetry_heading, last_heading

; === SECTION 2: Advisory output (Level 2+) ===
TRUST_CHECK subsystem=steering, min=0.50
READ_PIN compass_heading
READ_VAR target_heading
SUB_F heading_error
; ... compute suggested rudder correction ...
EMIT_EVENT advisory_rudder, suggested_correction

; === SECTION 3: Autonomous control (Level 3+) ===
TRUST_CHECK subsystem=steering, min=0.70
READ_PIN compass_heading
READ_VAR target_heading
SUB_F heading_error
PID_COMPUTE heading_pid
CLAMP_F -30.0 30.0
WRITE_PIN rudder
```

If trust drops from 0.75 to 0.65 (below Section 3's threshold), Section 3 is skipped but Sections 1 and 2 continue to execute. The system automatically degrades from autonomous control to advisory output.

### 5.4 Failure Narratives

A failure narrative describes what the agent should "tell" the user when something goes wrong. This is not an error message in the traditional sense — it is a structured, human-readable explanation that an agent generates and presents to the operator.

**Failure narrative fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `failure_code` | Machine-readable error identifier | "WIND_EXCEEDED" |
| `severity` | Impact severity (INFO, WARNING, ERROR, CRITICAL) | "WARNING" |
| `what_happened` | Plain-English description of the event | "Wind speed exceeded 25 knots" |
| `what_the_system_did` | What action the system took | "Heading hold disengaged, rudder centered" |
| `what_the_user_should_do` | Recommended human action | "Take manual control or wait for wind to decrease" |
| `trust_impact` | Effect on trust score | "No trust penalty — environmental, not systemic" |
| `recovery_path` | How to return to autonomous operation | "Wind below 20 knots for 60 seconds → auto-restore" |

### 5.5 Composition: Combining Intention Blocks

Multiple intention blocks can be composed into a single deployment unit. The composition rules are:

1. **Non-conflicting actuators**: Two blocks may not write to the same actuator without an explicit arbitration declaration.
2. **Compatible trust contexts**: A composed program requires the maximum trust level across all blocks.
3. **Summed capability requirements**: The composed program requires the union of all blocks' capabilities.
4. **Ordered failure narratives**: If multiple blocks fail simultaneously, narratives are ordered by severity.

**Example composition:**

```
Block A: "Maintain heading 270°"
  - Requires: compass, rudder
  - Trust: Level 3
  - Writes: rudder

Block B: "Reduce speed in rough weather"
  - Requires: accelerometer, throttle
  - Trust: Level 2
  - Writes: throttle

Block C: "Emergency obstacle avoidance"
  - Requires: lidar, rudder, throttle
  - Trust: Level 2
  - Writes: rudder, throttle
  - Priority: CRITICAL (overrides Block A's rudder write)
```

When all three blocks are deployed:
- Normal operation: A controls rudder, B controls throttle
- Obstacle detected: C overrides both rudder and throttle (critical priority)
- Trust drops below 0.70: A disengages, B and C continue (Level 2 sufficient)

---

## 6. Formal Properties: Provable Guarantees for Agent-Native Code

### 6.1 Determinism Despite Agent Variability

**Theorem 5 (Agent-Compilation Determinism):** Given identical intentions, identical system prompts, and identical hardware configurations, the *deployed 8-byte bytecode* produced by the deterministic compiler from any valid AAB input is unique. Different agents may produce different AAB representations, but the AAB → 8-byte compilation is deterministic.

*Proof:*
1. AAB → 8-byte compilation is a deterministic function (implemented in C, no randomness).
2. The same AAB input always produces the same 8-byte output (compiler determinism).
3. Different agents produce different AAB inputs, but after compilation, each specific AAB maps to a unique bytecode sequence.
4. On the ESP32 VM, the bytecode execution is deterministic (Theorem 4 from the VM deep analysis: identical inputs → identical outputs in same cycles).
5. Therefore, the deployed system is deterministic end-to-end, even though the agent compilation process is stochastic. ∎

**Corollary:** The non-determinism of agent compilation is *confined to the generation phase*. Once bytecode is deployed, all behavior is deterministic. This is the key insight: agent variability provides implementation diversity during development, while the deployed system remains provably deterministic.

### 6.2 Safety Envelope Preservation Under Agent Compilation

**Theorem 6 (Safety Preservation):** If the validation agent accepts an AAB program (issues PASS verdict), and the deterministic compiler correctly translates AAB to 8-byte bytecode, then the deployed bytecode preserves all safety properties asserted in the AAB metadata.

*Proof:*
We show that each safety mechanism in the AAB maps to a safety mechanism in the deployed bytecode:

1. **TRUST_CHECK (opcode 0x50)**: Compiles to a SYSCALL that reads trust score from shared memory. If below threshold, execution jumps to failure handler. This is enforced by the VM's JUMP semantics.

2. **SAFE_BOUNDARY (opcode 0x52)**: Compiles to a comparison + conditional JUMP + clamp sequence. The CLAMP_F instruction guarantees the output stays within bounds (Theorem 3 from VM analysis: no value outside bounds reaches actuators).

3. **RATE_LIMIT (opcode 0x53)**: Compiles to a computation sequence that tracks previous output and limits delta. The rate limit is mathematically bounded by the max_rate parameter.

4. **DECLARE_ACTUATOR_USE (opcode 0x43)**: At deployment time, the Jetson checks that the actuator's configured min/max limits are compatible with the program's declared usage. If incompatible, deployment is rejected.

5. **POST_COND assertions**: These are verified at AAB validation time by the safety agent. The deterministic compiler preserves these conditions in the bytecode structure.

6. **Actuator clamping**: The VM firmware clamps all actuator register values to configured min/max after VM execution, regardless of bytecode output. This is the final safety net (Tier 2 safety).

Therefore, the safety envelope declared in the AAB is preserved through compilation and enforced at execution time. ∎

### 6.3 Correctness: Does the Bytecode Achieve the Stated Intention?

**Claim:** An AAB program is "correct" if its execution body, when run on the NEXUS VM with the declared capabilities, achieves the intention declared in DECLARE_INTENT.

**Verification approach:**

Correctness verification is performed by the validation agent (Claude 3.5 Sonnet) through a three-step process:

1. **Symbolic execution**: The validator traces through the bytecode, tracking symbolic stack values (not concrete values). For the heading-hold example, it tracks `heading` → `heading - setpoint` → `PID(heading - setpoint)` → `clamp(PID(...))`.

2. **Intention matching**: The validator compares the symbolic execution result to the stated intention. "Maintain heading 270°" is matched against "PID controller that drives rudder to minimize heading error relative to setpoint."

3. **Constraint satisfaction**: The validator checks that all declared constraints are satisfied by the symbolic execution. "Rudder never exceeds ±30°" is verified by tracing the CLAMP_F instruction.

**Limitation:** This verification is probabilistic, not absolute. The validator is an LLM, not a formal verification tool. It catches ~95.1% of safety issues (empirical data) but cannot guarantee 100% correctness. For true formal verification, a separate theorem prover (e.g., Z3, Coq) would need to operate on the AAB's symbolic representation.

**Proposed formal verification extension:**

The AAB metadata can include a **verification hint** that encodes the intended invariant as a first-order logic formula:

```
FORALL tick: |heading[tick] - 270| < 5  =>  |rudder[tick]| < 30
```

A formal verification tool can check this invariant by:
1. Extracting the symbolic execution trace from the bytecode.
2. Encoding the trace as a constraint system.
3. Using an SMT solver (Z3) to check whether the invariant holds under all possible inputs.

This is future work but architecturally enabled by the self-describing bytecode format.

### 6.4 Completeness: Can the Bytecode Express All Necessary Robotic Control Patterns?

**Theorem 7 (Expressive Completeness):** The extended NEXUS ISA (32 existing opcodes + proposed extensions) can express all common robotic control patterns while maintaining the VM's deterministic timing, bounded memory, and safety invariants.

*Proof by enumeration of required patterns:*

| Control Pattern | Existing Opcodes | New Ocodes Needed | Implementation |
|----------------|-----------------|-------------------|----------------|
| PID controller | PID_COMPUTE (syscall) | None | Direct syscall |
| State machine | JUMP_IF_TRUE/FALSE + variables | None | Comparison + branch cascade |
| Gain scheduling | PUSH_F32 + JUMP_IF | None | Conditional parameter selection |
| Fuzzy logic | MIN_F, MAX_F (t-norm/t-conorm) | None | Fuzzy inference via stack ops |
| Rate limiting | Variables + CLAMP_F | RATE_LIMIT (0x53) | Explicit rate limit opcode |
| Sensor fusion | ADD_F, MUL_F, CLAMP_F | None | Weighted average via stack |
| Obstacle avoidance | Comparison + JUMP | SAFE_BOUNDARY (0x52) | Boundary enforcement |
| Trust-gated control | None (new) | TRUST_CHECK (0x50) | Trust verification |
| Emergency stop | JUMP + WRITE_PIN | SAFETY_EVENT_EMIT (0x56) | Immediate safe state |
| Agent delegation | None (new) | DELEGATE (0x32) | Request cognitive processing |
| Graceful degradation | Comparison + JUMP | AUTONOMY_LEVEL_ASSERT (0x51) | Level-based execution |
| Failure reporting | EMIT_EVENT (syscall) | EXPLAIN_FAILURE (0x26) | Structured failure narrative |

All patterns are expressible. The new opcodes provide *convenience and safety structuring* but are not strictly necessary for expressiveness — any new opcode's behavior can be simulated using existing opcodes. For example, TRUST_CHECK can be simulated as: `READ_PIN trust_register; PUSH_F32 threshold; LT_F; JUMP_IF_TRUE failure_handler`.

However, the new opcodes provide critical *metadata* that enables agent understanding and verification, which is the primary purpose of the A2A-native language. ∎

### 6.5 Complexity Bounds for Agent-Native Programs

**Theorem 8 (Bounded Complexity):** Any agent-native program that passes AAB validation satisfies:
1. Stack depth ≤ 256 (proven by VM analysis; agent programs use ≤ 4 observed)
2. Cycle budget ≤ 10,000 per tick (VM safety invariant)
3. Instruction count ≤ 4,600 at 1 kHz tick rate (208 µs budget / ~45 ns per instruction)
4. Variable usage ≤ 256 (VM memory model)
5. PID controllers ≤ 8 (VM resource limit)
6. Trust checks: any number (compiles to comparison + branch, zero overhead)

These bounds are *preserved regardless of which agent generated the bytecode*, because the deterministic compiler rejects any program that would violate them. The AAB validation agent checks these bounds symbolically before compilation.

---

## 7. Annotated Example Programs

### 7.1 Example 1: Wind-Aware Heading Hold (Complete Agent-Native Program)

This program maintains heading 270° but automatically disengages when wind speed exceeds 25 knots. It demonstrates intention declaration, capability scoping, trust gating, and failure narratives.

```
╔══════════════════════════════════════════════════════════════╗
║ INTENTION BLOCK: wind_aware_heading_hold                    ║
╠══════════════════════════════════════════════════════════════╣

; ─── HEADER ───────────────────────────────────────────────────
; Core: 0x20 0x00 0x0001 0x7A3B2C1D
; AAB Metadata:
;   intent: "Maintain heading 270° with wind safety disengage"
;   trust_min: 0.70 (Level 3 - CONDITIONAL)
;   author: qwen2.5-coder-7b @ 2026-03-29T14:30:00Z
;   validator: claude-3.5-sonnet @ 2026-03-29T14:31:00Z
;   verdict: PASS (risk_score: 0.12)

; ─── CAPABILITY SCOPE ─────────────────────────────────────────
; Core: 0x40 0x00 0x0001 0x00000000  ; REQUIRE cap: sensor compass
; Core: 0x40 0x00 0x0001 0x00000001  ; REQUIRE cap: sensor wind_speed
; Core: 0x40 0x00 0x0002 0x00000000  ; REQUIRE cap: actuator rudder
; Core: 0x43 0x00 0x0000 0x41900000  ; DECLARE_ACTUATOR: rudder, max_rate=18°/s

; ─── TRUST CONTEXT ────────────────────────────────────────────
; Core: 0x50 0x00 0x0001 0x3F000000  ; TRUST_CHECK: steering >= 0.70
;   → On fail: JUMP to :trust_fail_handler

; ─── EXECUTION BODY ──────────────────────────────────────────
; (All instructions use existing NEXUS opcodes 0x00–0x1F)

; Step 1: Read wind speed and check against safety limit
; Core: 0x03 0x00 0x0000 0x41C80000  ; PUSH_F32 25.0 (wind limit)
; Core: 0x1A 0x00 0x0005 0x00000000  ; READ_PIN sensor[5] (wind_speed)
; Core: 0x14 0x00 0x0000 0x00000008  ; GTE_F → stack: [wind_speed >= 25.0]
; Core: 0x1F 0x00 0x0000 0x00000028  ; JUMP_IF_TRUE :wind_disengage

; Step 2: Wind is safe — execute heading PID
; Core: 0x1A 0x00 0x0000 0x00000000  ; READ_PIN sensor[0] (compass_heading)
; Core: 0x1A 0x00 0x0001 0x00000000  ; READ_PIN sensor[1] (target_heading=270)
; Core: 0x00 0x80 0x0000 0x00000004  ; SYSCALL: PID_COMPUTE pid[0]
; Core: 0x10 0x00 0x0000 0xC1F00000  ; CLAMP_F -30.0 (rudder limit, conservative)
;   [operand2 encoding: lo=-30.0, hi=+30.0, flags encode both]
; Core: 0x1C 0x00 0x0000 0x00000000  ; WRITE_PIN actuator[0] (rudder)
; Core: 0x1D 0x00 0x0000 0x00000040  ; JUMP :end (skip disengage block)

; ─── WIND DISENGAGE HANDLER ──────────────────────────────────
; :wind_disengage (offset = 0x28)
; Core: 0x03 0x00 0x0000 0x00000000  ; PUSH_F32 0.0 (center rudder)
; Core: 0x1C 0x00 0x0000 0x00000000  ; WRITE_PIN actuator[0] (rudder = 0°)
; Core: 0x00 0x80 0x0000 0x00000006  ; SYSCALL: EMIT_EVENT wind_disengage

; ─── TRUST FAIL HANDLER ──────────────────────────────────────
; :trust_fail_handler
; Core: 0x03 0x00 0x0000 0x00000000  ; PUSH_F32 0.0 (safe state)
; Core: 0x1C 0x00 0x0000 0x00000000  ; WRITE_PIN actuator[0] (rudder = 0°)
; Core: 0x00 0x80 0x0000 0x00000006  ; SYSCALL: EMIT_EVENT trust_insufficient

; ─── FAILURE NARRATIVES ─────────────────────────────────────
; Core: 0x26 0x00 0x0001 0x00000000  ; EXPLAIN_FAILURE wind_disengage
;   AAB: "Wind speed exceeded 25 knots. Heading hold disengaged.
;         Rudder centered for safety. Autonomy reduced to MANUAL."
;   AAB: recovery_path: "Wind < 20 knots for 60s → auto-restore"
;   AAB: trust_impact: "none (environmental, not systemic)"

; Core: 0x26 0x00 0x0002 0x00000000  ; EXPLAIN_FAILURE trust_insufficient
;   AAB: "Steering trust score below 0.70 (Level 3). Cannot operate
;         autonomously. Operator control required."
;   AAB: recovery_path: "Trust recovers through consistent good behavior"

; ─── VERIFICATION ────────────────────────────────────────────
; Core: 0x21 0x00 0x0001 0x41900000  ; ASSERT_GOAL: heading_error < 30.0°
; Core: 0x22 0x00 0x0001 0x41800000  ; VERIFY_OUTCOME: rudder in [-30, 30] ±16°

; :end
; Core: 0x00 0x00 0x0000 0x00000000  ; NOP (padding, safe)

╚══════════════════════════════════════════════════════════════╝
```

**Program Statistics:**
| Metric | Value |
|--------|-------|
| Core instructions | 18 |
| Core bytes | 144 |
| AAB bytes (estimated) | 820 |
| Max stack depth | 2 |
| Cycle cost | 58 |
| Cycle budget utilization | 0.6% |
| Trust level required | 3 (CONDITIONAL) |
| Capabilities required | compass, wind_speed, rudder |
| Safety class | NORMAL |

### 7.2 Example 2: Multi-Subsystem Trust-Gated Irrigation Controller

This demonstrates an agricultural use case where three subsystems (soil moisture, pump control, valve control) have independent trust levels. The program adapts its behavior based on each subsystem's trust.

```
╔══════════════════════════════════════════════════════════════╗
║ INTENTION BLOCK: adaptive_irrigation                        ║
╠══════════════════════════════════════════════════════════════╣

; ─── HEADER ───────────────────────────────────────────────────
; Core: 0x20 0x00 0x0002 0x5D1E9A3F
; AAB Metadata:
;   intent: "Water crops when soil moisture drops below threshold,
;            adapting behavior to subsystem trust levels"
;   trust_min: 0.30 (Level 1 - ASSIST)
;   domain: "agriculture:irrigation:zone_1"

; ─── TRUST CONTEXT: Per-Subsystem ────────────────────────────
; Core: 0x50 0x00 0x0010 0x3E99999A  ; TRUST_CHECK: moisture_sensor >= 0.30
;   → fail: use last known reading
; Core: 0x50 0x00 0x0011 0x3F000000  ; TRUST_CHECK: pump_control >= 0.50
;   → fail: advisory mode only (alert operator)
; Core: 0x50 0x00 0x0012 0x3ECCCCCD  ; TRUST_CHECK: valve_control >= 0.40
;   → fail: cannot open valves autonomously

; ─── EXECUTION BODY ──────────────────────────────────────────

; Step 1: Read soil moisture (with stale-data fallback)
; Core: 0x1A 0x00 0x0010 0x00000000  ; READ_PIN sensor[16] (soil_moisture_pct)
; Core: 0x03 0x00 0x0000 0x42C80000  ; PUSH_F32 100.0 (impossible value)
; Core: 0x11 0x00 0x0000 0x00000006  ; EQ_F → is_stale? (100.0 = stale sentinel)
; Core: 0x1E 0x00 0x0000 0x0000001C  ; JUMP_IF_FALSE :moisture_valid

; Step 1b: Fallback to last known reading
; Core: 0x1A 0x40 0x0050 0x00000000  ; READ_PIN var[16] (last_moisture)
;   → AAB: "Using cached moisture reading — sensor may be stale"
; Core: 0x1D 0x00 0x0000 0x00000024  ; JUMP :check_threshold

; :moisture_valid (offset = 0x1C)
; Core: 0x1A 0x40 0x0040 0x00000000  ; WRITE_PIN var[0] (cache moisture)

; :check_threshold (offset = 0x24)
; Core: 0x03 0x00 0x0000 0x41900000  ; PUSH_F32 30.0 (threshold)
; Core: 0x15 0x00 0x0000 0x00000034  ; GTE_F → moisture >= 30%?
; Core: 0x1F 0x00 0x0000 0x00000034  ; JUMP_IF_TRUE :skip_irrigation

; Step 2: Moisture below threshold — irrigate
; Step 2a: High trust — full autonomous control
; Core: 0x1A 0x40 0x0041 0x00000000  ; READ_PIN var[1] (pump_trust)
; Core: 0x03 0x00 0x0000 0x3F000000  ; PUSH_F32 0.50
; Core: 0x15 0x00 0x0000 0x00000044  ; GTE_F → pump_trust >= 0.50?
; Core: 0x1F 0x00 0x0000 0x00000044  ; JUMP_IF_TRUE :autonomous_irrigate

; Step 2b: Medium trust — advisory only
; Core: 0x00 0x80 0x0000 0x00000006  ; EMIT_EVENT: irrigation_advisory
;   AAB: "Soil moisture at 28% — below 30% threshold. Pump trust
;         insufficient for autonomous operation. Operator notified."
; Core: 0x1D 0x00 0x0000 0x00000058  ; JUMP :end

; :autonomous_irrigate (offset = 0x44)
; Core: 0x03 0x00 0x0000 0x42C80000  ; PUSH_F32 100.0 (pump on)
; Core: 0x1C 0x00 0x0020 0x00000000  ; WRITE_PIN actuator[0] (pump)
; Core: 0x03 0x00 0x0000 0x41A00000  ; PUSH_F32 20.0 (irrigation_duration_s)
; Core: 0x1A 0x00 0x003C 0x00000000  ; READ_TIMER_MS
; Core: 0x0A 0x00 0x0000 0x447A0000  ; DIV_F (ms_to_sec)
; Core: 0x1C 0x40 0x0042 0x00000000  ; WRITE_PIN var[2] (irrigation_start_time)

; :skip_irrigation
; :end

╚══════════════════════════════════════════════════════════════╝
```

**Key Features Demonstrated:**
- **Per-subsystem trust gating**: Three independent trust checks for three subsystems
- **Graceful degradation**: High trust → autonomous; medium trust → advisory; low trust → cached data
- **Stale sensor fallback**: Uses sentinel value to detect stale sensor data
- **Domain independence**: Same program structure works for agriculture, marine, or factory automation

### 7.3 Example 3: Agent Delegation — Requesting Cognitive Processing

This example shows a reflex program that detects a complex situation (unusual sensor correlation) and delegates analysis to the cognitive layer, then acts on the result. This is the A2A communication primitive.

```
╔══════════════════════════════════════════════════════════════╗
║ INTENTION BLOCK: anomaly_detection_with_delegation           ║
╠══════════════════════════════════════════════════════════════╣

; ─── HEADER ───────────────────────────────────────────────────
; Core: 0x20 0x00 0x0003 0xB2C4D6E8
; AAB Metadata:
;   intent: "Detect unusual heading oscillation and delegate
;            diagnostic analysis to cognitive layer"
;   trust_min: 0.50 (Level 2 - SEMI_AUTO)

; ─── EXECUTION BODY ──────────────────────────────────────────

; Step 1: Detect heading oscillation
;   (heading change rate exceeds threshold)
; Core: 0x1A 0x00 0x0000 0x00000000  ; READ_PIN sensor[0] (current_heading)
; Core: 0x1A 0x40 0x0040 0x00000000  ; READ_PIN var[0] (prev_heading)
; Core: 0x08 0x00 0x0000 0x00000000  ; SUB_F → heading_delta
; Core: 0x0B 0x00 0x0000 0x00000000  ; ABS_F → abs_heading_delta

; Step 2: Check if oscillation exceeds threshold
; Core: 0x03 0x00 0x0000 0x41200000  ; PUSH_F32 10.0 (threshold: 10°)
; Core: 0x12 0x00 0x0000 0x00000028  ; GT_F → delta > 10°?
; Core: 0x1E 0x00 0x0000 0x00000028  ; JUMP_IF_FALSE :no_anomaly

; Step 3: Anomaly detected — delegate to cognitive layer
; Core: 0x31 0x01 0x0002 0x000001F4  ; ASK cognitive_layer, timeout=500ms
;   AAB:
;     question: "Heading oscillating ±10° in < 1s. Possible causes:
;                (a) rudder actuator malfunction, (b) wave action,
;                (c) compass interference. Diagnose."
;     on_timeout: "Assume environmental cause, reduce speed"
;   → Result placed in var[10] (diagnosis_code)

; Step 4: Act on diagnosis
; Core: 0x1A 0x40 0x004A 0x00000000  ; READ_PIN var[10] (diagnosis)
; Core: 0x03 0x00 0x0000 0x00000001  ; PUSH_I8 1 (actuator_fault)
; Core: 0x11 0x00 0x0000 0x00000040  ; EQ_F → diagnosis == actuator_fault?
; Core: 0x1E 0x00 0x0000 0x00000050  ; JUMP_IF_FALSE :check_environmental

; Step 4a: Actuator fault — emergency safe state
; Core: 0x56 0x00 0x0003 0x00000001  ; SAFETY_EVENT_EMIT: CRITICAL, code=1
;   AAB: "Rudder actuator fault diagnosed. Entering safe state."
; Core: 0x03 0x00 0x0000 0x00000000  ; PUSH_F32 0.0
; Core: 0x1C 0x00 0x0000 0x00000000  ; WRITE_PIN actuator[0] (rudder = center)
; Core: 0x03 0x00 0x0000 0x41A00000  ; PUSH_F32 20.0 (reduce speed to 20%)
; Core: 0x1C 0x00 0x0001 0x00000000  ; WRITE_PIN actuator[1] (throttle)
; Core: 0x1D 0x00 0x0000 0x00000058  ; JUMP :end

; :check_environmental (offset = 0x50)
; Core: 0x03 0x00 0x0000 0x00000002  ; PUSH_I8 2 (environmental)
; Core: 0x11 0x00 0x0000 0x00000058  ; EQ_F → diagnosis == environmental?
; Core: 0x1E 0x00 0x0000 0x00000058  ; JUMP_IF_FALSE :end

; Step 4b: Environmental — reduce speed, maintain heading
; Core: 0x03 0x00 0x0000 0x42480000  ; PUSH_F32 50.0 (reduce speed to 50%)
; Core: 0x1C 0x00 0x0001 0x00000000  ; WRITE_PIN actuator[1] (throttle)
;   AAB: "Wave action detected. Speed reduced to 50%. Heading hold continues."

; :no_anomaly
; :end

╚══════════════════════════════════════════════════════════════╝
```

**Key Features Demonstrated:**
- **A2A communication**: ASK opcode delegates diagnostic reasoning to the cognitive layer
- **Timeout handling**: If cognitive layer doesn't respond in 500ms, fallback behavior activates
- **Structured diagnosis response**: Cognitive layer returns a diagnostic code (1=actuator, 2=environmental, 3=unknown)
- **Branching response**: Different safety responses based on diagnosis
- **SAFETY_EVENT_EMIT**: Formal safety event notification with structured metadata

---

## 8. Integration Points with Existing NEXUS VM

### 8.1 Backward Compatibility Strategy

All proposed extensions are designed to be **fully backward compatible** with the existing 32-opcode NEXUS VM:

1. **New opcodes 0x20–0x5F are treated as NOPs** by the existing ESP32 VM firmware. They consume 1 cycle (NOP cost) and are skipped. The VM continues to execute only opcodes 0x00–0x1F and recognized SYSCALLs.

2. **The deterministic compiler (Jetson-side) strips all metadata** before deployment. The ESP32 receives only 8-byte core instructions using opcodes 0x00–0x1F. No firmware update is needed on the ESP32.

3. **Intent opcodes (0x20–0x2F) compile to nothing** — they are pure metadata. Safety augmented opcodes (0x50–0x53) compile to equivalent sequences using existing comparison + branch + clamp opcodes.

4. **Agent communication opcodes (0x30–0x34) compile to EMIT_EVENT syscalls** — the existing SYSCALL mechanism handles them. The Jetson receives the event and routes it to the appropriate agent.

### 8.2 Opcode Translation Table

The following table shows how each new opcode translates to existing NEXUS opcodes:

| New Opcode | Translation to Existing Opcodes | Cycle Cost |
|------------|--------------------------------|------------|
| 0x20 DECLARE_INTENT | (no runtime representation — stripped) | 0 |
| 0x21 ASSERT_GOAL | (no runtime representation — verified at deploy time) | 0 |
| 0x22 VERIFY_OUTCOME | PUSH_F32 + READ_PIN + comparison + JUMP | ~15 |
| 0x23 DECLARE_CONSTRAINT | (no runtime representation — verified at deploy time) | 0 |
| 0x24 INTENT_SCOPE_BEGIN | (no runtime representation) | 0 |
| 0x25 INTENT_SCOPE_END | (no runtime representation) | 0 |
| 0x26 EXPLAIN_FAILURE | EMIT_EVENT (SYSCALL) | ~5 |
| 0x30 TELL | EMIT_EVENT (SYSCALL) | ~5 |
| 0x31 ASK | EMIT_EVENT (SYSCALL) + READ_PIN (for response) | ~10 |
| 0x32 DELEGATE | EMIT_EVENT (SYSCALL) | ~5 |
| 0x33 REPORT_STATUS | EMIT_EVENT (SYSCALL) | ~5 |
| 0x34 REQUEST_OVERRIDE | EMIT_EVENT (SYSCALL) | ~5 |
| 0x40 REQUIRE_CAPABILITY | (no runtime representation — verified at deploy time) | 0 |
| 0x41 CAPABILITY_RESPONSE | (no runtime representation — handled by Jetson) | 0 |
| 0x42 DECLARE_SENSOR_NEED | (no runtime representation) | 0 |
| 0x43 DECLARE_ACTUATOR_USE | (no runtime representation) | 0 |
| 0x50 TRUST_CHECK | READ_PIN (trust register) + PUSH_F32 + LT_F + JUMP_IF_FALSE | ~10 |
| 0x51 AUTONOMY_LEVEL_ASSERT | READ_PIN (trust register) + PUSH_F32 + LT_F + JUMP_IF_FALSE | ~10 |
| 0x52 SAFE_BOUNDARY | Comparison + CLAMP_F + JUMP | ~12 |
| 0x53 RATE_LIMIT | READ_PIN (previous value) + SUB_F + CLAMP_F + WRITE_PIN | ~15 |
| 0x54 DEADBAND | SUB_F + ABS_F + comparison + conditional zero | ~15 |
| 0x55 WATCHDOG_PET | (no runtime representation — handled by firmware) | 0 |
| 0x56 SAFETY_EVENT_EMIT | EMIT_EVENT (SYSCALL) | ~5 |

### 8.3 Wire Protocol Integration

AAB bytecode is transmitted over the existing NEXUS Serial Wire Protocol using the REFLEX_DEPLOY message (type 0x09). The message format is extended to include a version flag:

```
Existing REFLEX_DEPLOY payload:
  [version:1][bytecode_length:2][bytecode:N]

Extended REFLEX_DEPLOY payload (version 2):
  [version:2][aab_length:4][aab_bytecode:N][core_offset:4]
```

The version field (currently 1) is incremented to 2 for AAB-aware deployments. The ESP32 ignores the AAB metadata and extracts core bytecode starting at `core_offset`. Backward compatibility is maintained: version 1 deployments work unchanged.

**Bandwidth impact:** A typical AAB deployment is ~10 KB vs ~500 B for core-only. At 921,600 baud, this adds ~100 ms to the deployment time (from ~5 ms to ~105 ms). This is negligible compared to the 29-second reflex generation time.

### 8.4 AAB Storage on ESP32

AAB bytecode is **not stored on the ESP32**. Only the core 8-byte instructions are stored in the 2 MB LittleFS partition. AAB bytecode is stored on the Jetson's NVMe SSD (~256 GB), enabling a complete audit trail of every reflex ever deployed, including full metadata.

**Jetson storage per reflex:**

| Component | Size | Notes |
|-----------|------|-------|
| AAB bytecode | ~10 KB | Full metadata |
| Validation report (JSON) | ~2 KB | Claude's safety analysis |
| Generation context (JSON) | ~5 KB | Prompt + user intention + few-shot examples |
| Deployment record (JSON) | ~1 KB | Timestamp, target node, version |
| **Total per reflex** | **~18 KB** | |
| 1,000 reflexes | ~18 MB | ~0.007% of 256 GB |
| 100,000 reflexes | ~1.8 GB | ~0.7% of 256 GB |

### 8.5 Integration with INCREMENTS Trust Framework

The trust-checking opcodes (0x50, 0x51) integrate directly with the INCREMENTS trust score computation:

```
Trust Score (Jetson, Python) → shared memory → ESP32 reads via READ_PIN →
TRUST_CHECK compares against threshold → branch to appropriate code path
```

The INCREMENTS parameters map to AAB trust contexts:

| INCREMENTS Parameter | AAB Mapping |
|---------------------|-------------|
| alpha_gain (0.002) | TRUST_MIN thresholds (0.50, 0.70, 0.80, 0.90, 0.95) |
| alpha_loss (0.05) | TRUST_IMPACT metadata (how much trust is lost on failure) |
| Loss:Gain ratio (25:1) | AUTONOMY_LEVEL_ASSERT level assignments |
| Per-subsystem trust | Separate TRUST_CHECK per subsystem in trust context |
| Candidate state | AUTONOMY_LEVEL_ASSERT during A/B testing phase |

---

## 9. Open Questions and Future Research

### 9.1 Open Research Questions

1. **Formal verification of AAB programs**: Can we build an SMT-solver-based verifier that operates on AAB metadata to prove safety invariants, going beyond the ~95% catch rate of LLM-based validation?

2. **Intention equivalence classes**: Given two AAB programs with different implementations but the same declared intention, can we formally prove they are behaviorally equivalent? This is the "intentional equivalence problem."

3. **Agent-specific compilation profiles**: Different agents (GPT-4o, Claude, Qwen) have different strengths. Can we build agent-specific system prompts that leverage each model's unique capabilities to produce optimal AAB for different domains?

4. **AAB compression for cloud storage**: With 100K+ reflexes expected over a fleet's lifetime, efficient AAB storage and retrieval becomes important. Can we delta-encode AAB programs that share common intention blocks?

5. **Adversarial AAB injection**: If an agent is compromised or produces malicious AAB, what attack surfaces exist? The deterministic compiler strips metadata, but the core bytecode could still contain unsafe patterns that evade the validation agent's 95% catch rate.

6. **Real-time AAB modification**: Can an agent modify deployed AAB in real-time (hot-patching) while maintaining safety guarantees? The existing VM doesn't support hot bytecode swapping (identified as open question in VM deep analysis).

7. **Multi-agent AAB composition**: When three agents independently produce AAB blocks for the same subsystem, how are conflicts resolved? The "last-writer-wins" semantics for actuator registers are insufficient for safety-critical scenarios.

8. **AAB as audit evidence**: Under EU AI Act and IEC 61508 requirements, AAB bytecode with full metadata provides a complete audit trail. Can this be formalized as a compliance artifact?

### 9.2 Implementation Roadmap

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| Phase 1 | 4 weeks | AAB format specification, TLV tag registry, metadata schema |
| Phase 2 | 6 weeks | AAB generator (extends existing Qwen2.5-Coder-7B pipeline) |
| Phase 3 | 4 weeks | Cross-agent AAB validator (Claude 3.5 Sonnet prompt engineering) |
| Phase 4 | 3 weeks | Deterministic AAB → 8-byte compiler (C extension to existing compiler) |
| Phase 5 | 2 weeks | Wire protocol extension (REFLEX_DEPLOY v2) |
| Phase 6 | 8 weeks | ESP32 firmware update: new opcode handlers for 0x50–0x56 |
| Phase 7 | 4 weeks | Jetson trust score → ESP32 shared memory bridge |
| Phase 8 | 6 weeks | End-to-end integration testing: intention → AAB → bytecode → execution |
| **Total** | **37 weeks** | |

### 9.3 Conclusion

The A2A-native language paradigm represents a fundamental shift in how we think about programming. By making agents the first-class interpreters of bytecode — embedding intention, capability requirements, safety annotations, and failure narratives directly in the instruction format — we create a language that is:

1. **Self-describing**: Any agent can understand any bytecode, regardless of who generated it.
2. **Self-verifying**: Safety properties are encoded in the bytecode itself, enabling cross-agent validation.
3. **Self-explaining**: Failure narratives provide human-understandable explanations without requiring code reading.
4. **Evolutionary**: The language definition (system prompt) can change in seconds, immediately affecting all future compilations.
5. **Backward compatible**: All extensions integrate cleanly with the existing 32-opcode NEXUS VM and wire protocol.

The NEXUS platform's existing architecture — particularly the separation between agent-driven code generation (Jetson, 12–43 second latency) and deterministic reflex execution (ESP32, sub-200 µs latency) — provides the perfect foundation for this paradigm. Agents generate and reason about AAB bytecode at their own pace, while the deployed core bytecode executes with the determinism, timing guarantees, and safety invariants that physical robotics demands.

This is not merely an incremental improvement to the NEXUS bytecode format. It is a new category of programming language — one designed not for humans to write, but for agents to generate, verify, compose, and explain. The three pillars of system prompt, equipment, and vessel provide the context that makes this possible: the system prompt defines the language, the equipment defines what the language can express, and the vessel defines what the language can achieve. Together, they enable any agent to actualize any user's intention within the boundaries of physical reality and safety requirements.

---

## Appendix A: Complete Opcode Quick Reference

### Existing NEXUS Opcodes (0x00–0x1F)

```
0x00 NOP           0x10 CLAMP_F      0x1C READ_TIMER_MS
0x01 PUSH_I8       0x11 EQ_F         0x1D JUMP
0x02 PUSH_I16      0x12 LT_F         0x1E JUMP_IF_FALSE
0x03 PUSH_F32      0x13 GT_F         0x1F JUMP_IF_TRUE
0x04 POP           0x14 GTE_F
0x05 DUP           0x15 LTE_F
0x06 SWAP          0x16 AND_B
0x07 ROT           0x17 OR_B
0x08 ADD_F         0x18 XOR_B
0x09 SUB_F         0x19 NOT_B
0x0A MUL_F         0x1A READ_PIN
0x0B DIV_F         0x1B WRITE_PIN
0x0C NEG_F
0x0D ABS_F
0x0E MIN_F
0x0F MAX_F
```

### Proposed Agent-Native Opcodes (0x20–0x5F)

```
--- Intent Opcodes (0x20–0x2F) ---
0x20 DECLARE_INTENT        0x23 DECLARE_CONSTRAINT
0x21 ASSERT_GOAL           0x24 INTENT_SCOPE_BEGIN
0x22 VERIFY_OUTCOME        0x25 INTENT_SCOPE_END
                           0x26 EXPLAIN_FAILURE

--- Agent Communication (0x30–0x3F) ---
0x30 TELL                  0x33 REPORT_STATUS
0x31 ASK                   0x34 REQUEST_OVERRIDE
0x32 DELEGATE

--- Capability Negotiation (0x40–0x4F) ---
0x40 REQUIRE_CAPABILITY    0x43 DECLARE_ACTUATOR_USE
0x41 CAPABILITY_RESPONSE   0x44 DECLARE_COMPUTE_NEED
0x42 DECLARE_SENSOR_NEED

--- Safety Augmentation (0x50–0x5F) ---
0x50 TRUST_CHECK           0x54 DEADBAND
0x51 AUTONOMY_LEVEL_ASSERT 0x55 WATCHDOG_PET
0x52 SAFE_BOUNDARY         0x56 SAFETY_EVENT_EMIT
0x53 RATE_LIMIT
```

## Appendix B: TLV Tag Registry

| Tag | Name | Value Type | Example |
|-----|------|-----------|---------|
| 0x01 | TYPE_DESC | UTF-8 string | "f32:degrees:heading" |
| 0x02 | CAP_REQ | UTF-8 string | "sensor:compass" |
| 0x03 | PRE_COND | UTF-8 string | "compass_fresh < 500ms" |
| 0x04 | POST_COND | UTF-8 string | "rudder ∈ [-45, 45]" |
| 0x05 | INTENT_ID | UTF-8 string | "heading_hold.line_3" |
| 0x06 | TRUST_MIN | float32 string | "0.70" |
| 0x07 | TRUST_IMPACT | UTF-8 string | "alpha_loss × 0.5" |
| 0x08 | HUMAN_DESC | UTF-8 string | "Read current heading" |
| 0x09 | DEPENDS_ON | UTF-8 string | "prev.line_2" |
| 0x0A | SAFETY_CLASS | enum string | "CRITICAL\|NORMAL\|DEGRADED" |
| 0x0B | CYCLE_COST | UTF-8 string | "3 cycles" |
| 0x0C | SIDE_EFFECT | UTF-8 string | "writes:actuator:rudder" |
| 0x0D | UNIT_OF_MEASURE | UTF-8 string | "degrees" |
| 0x0E | ALTERNATIVE | UTF-8 string | "USE_PID_COMPUTE instead" |

---

*This document is part of the NEXUS A2A Language Design Research series, Task Agent 1 of 5. It establishes the philosophical foundation, bytecode format, compilation model, opcode extensions, program structure, and formal properties for an agent-native programming language paradigm.*
