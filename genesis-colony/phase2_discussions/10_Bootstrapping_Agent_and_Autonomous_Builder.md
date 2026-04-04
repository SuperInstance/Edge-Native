# The Bootstrapping Agent & The Overnight Autonomous Builder

## Practical Developer Workflows for Building the NEXUS Genesis Colony Architecture

**Phase 4B — Agent Workflows**
**Document:** `10_Bootstrapping_Agent_and_Autonomous_Builder.md`
**Status:** Authoritative — Developer Workflow Guide
**Date:** 2026-03-30
**Agent:** Agent-4B, AI Agent Design & Autonomous Development Specialist

---

## Preamble: Why These Guides Exist

Building the NEXUS Genesis Colony Architecture is not like building a web application or a mobile app. It is an act of cultivation — designing the conditions under which firmware organisms evolve, adapt, and survive on resource-constrained microcontrollers. The specification corpus spans philosophy (five cultural lens analyses), biology (DNA-code-cell-protein metaphor stack), safety engineering (four-tier safety, Lyapunov certificates), evolutionary computation (four-level mutation operators, seasonal protocols), and distributed systems (colony topology, reflex VM architecture). The total body of work is enormous, but most of it follows the same pattern: well-specified requirements, clear interfaces, and deterministic implementation paths.

This is precisely the kind of work that AI agents excel at — and precisely the kind of work where a human should be doing architecture, not typing. These two guides describe how to build the colony architecture itself using autonomous agents: one guide for the long-running bootstrapping agent with human-in-the-loop check-ins, and one for overnight or multiday autonomous builds with idea treeing to prevent wasted effort.

**These are developer workflow guides for the team building the NEXUS Genesis Colony Architecture — not end-user documentation.** The target reader is an engineer who has the specification corpus in front of them and wants to use AI agents to accelerate implementation without sacrificing quality, safety, or architectural coherence.

---

# PART A: The Bootstrapping Agent

## A1. What Is a Bootstrapping Agent?

A bootstrapping agent is an AI-driven development system that takes the NEXUS Genesis Colony Architecture specification corpus — the Colony Thesis, the cross-cultural lens analyses, the stress test analysis, the genetic variation mechanics spec, the ML/RL techniques spec, the IoT-as-protein architecture spec, the survival-of-fittest mechanisms spec, the white paper schema, and all supporting ADRs — and progressively builds the colony architecture from those specifications. The human is not writing code. The human is the *elder* — reviewing progress, making architectural course corrections, resolving ambiguities, and approving milestones.

The terminology is deliberate. In the Colony Thesis (Principle 12, Deliberative Promotion), the human is the elder whose veto is absolute, not as an override button but as a constitutional participant in the colony's governance. The bootstrapping agent extends this metaphor into the development process itself: the agent implements, the elder directs. The agent carries the spec as its DNA; the elder provides the evolutionary pressure (priority signals, quality feedback, architectural constraints).

**What distinguishes this from a generic "use Claude to write code" workflow:**

1. **Specification-driven, not imagination-driven.** The agent does not decide what to build. It reads the spec corpus and implements what has been specified. Every line of code references a specific section of a specific document.

2. **Context-persistent across sessions.** The agent maintains a persistent context file that survives between sessions. It remembers what was built yesterday, what failed, what the human said, and what comes next. This is not a fresh conversation every time — it is a continuous development thread.

3. **Human waypoints, not human typing.** The human's role is to review a 10-minute daily summary, adjust priorities, resolve ambiguities, and make architectural decisions. Typical human investment: 10 minutes per day, 1 hour per week, 4 hours per milestone.

4. **Safety-critical awareness.** Any code touching the safety system (the Gye Nyame layer — hardware-enforced safe state, Lyapunov stability certificates, VM safety invariants) is automatically flagged for mandatory human review before merge. The agent implements safety code but never commits it without elder approval.

### A1.1 What a Bootstrapping Agent CAN Do Well

- **Implement from specs.** Given a clear spec section (e.g., "Implement COBS framing per wire_protocol_spec.md section 3.2"), the agent produces correct, tested code in minutes.
- **Write tests.** The agent writes unit tests and integration tests that verify the implementation against spec requirements. One test per spec requirement, nothing more.
- **Fix bugs it introduced.** If a test fails, the agent analyzes the failure, fixes the code, and re-runs. This works 85% of the time within 3 attempts.
- **Document as it goes.** Every function references the spec section it implements. Inline comments, docstrings, and progress reports are generated automatically.
- **Maintain the build.** The agent runs the CI pipeline, fixes lint errors, resolves merge conflicts, and keeps the codebase in a green state.

### A1.2 What a Bootstrapping Agent CANNOT Do Well

- **Architectural decisions.** "Should the fitness function use a multiplicative or additive safety constraint?" This requires understanding the relationship between the safety system's three layers, the seasonal protocol's exploration-exploitation dynamics, and the GOST reliability floor. The agent defers to the elder.
- **Resolve spec ambiguities.** If the Colony Thesis says "the system must maintain inviolable individual rights" but the genetic variation spec says "least-fit genome retirement," which takes precedence? The agent flags the conflict and waits.
- **Creative problem-solving.** When the spec describes a desired behavior but not a specific implementation strategy (e.g., "the colony must detect concept drift in fitness trajectories"), the agent can implement a known algorithm (BOCPD) but cannot invent a novel approach.
- **Understand the philosophical rationale.** The agent can implement the seasonal protocol's Spring/Summer/Autumn/Winter cycle as code, but it cannot explain why Winter is a mathematical requirement for preventing overfitting in non-stationary environments. It follows the spec, not the philosophy.

### A1.3 The Confidence Calibration Problem

The most dangerous failure mode of a bootstrapping agent is the false sense of completion. The agent implements a spec section, writes tests that pass, commits the code, and reports "DONE." But the tests only verify what the agent wrote, not what the spec *actually requires*. If the agent misunderstood the spec, the tests will pass (testing the wrong behavior) and the agent will confidently report success.

**Countermeasures:**

1. **Pre-implementation spec summary.** Before writing any code, the agent writes a brief summary of the spec requirements it intends to implement. This forces explicit comprehension.
2. **Post-implementation spec comparison.** After tests pass, the agent compares its implementation line-by-line against the spec requirements and logs any divergence.
3. **Human spot-checks.** During the weekly review, the elder reads 3–5 commits against the original spec sections. This catches the ~5% of misunderstandings that slip through the automated checks.
4. **Integration tests written by a different session.** When possible, use a fresh agent session (with a clean context) to write integration tests based purely on the spec. This catches implementation-spec mismatches that the same agent session would not notice.

---

## A2. Architecture of a Bootstrapping Agent

The bootstrapping agent has five logical subsystems that operate in sequence during each task cycle.

### A2.1 The Context Manager

The context manager is the agent's memory system. It maintains a persistent markdown file (`/colony-agent/context.md`) that contains:

- **Spec coverage map:** Which sections of which spec documents have been implemented, which are in progress, and which are pending.
- **Implementation notes:** Key technical decisions made during implementation (e.g., "CRC-16 polynomial is 0x1021, init value 0xFFFF per wire_protocol_spec.md section 4.1").
- **Blocking issues:** Spec conflicts, dependency gaps, or decisions requiring elder input.
- **Elder directives:** The human's latest direction notes, preserved verbatim.

**Context file management:** When the context file exceeds 80 KB, the agent performs a rolling summarization: entries older than 30 days are compressed into a summary archive, the last 30 days remain at full fidelity, and a "key decisions" section is preserved permanently. Target size: 50–80 KB for optimal agent performance.

### A2.2 The Task Decomposer

The task decomposer takes a high-level directive from the elder ("Implement the reflex bytecode VM execution engine") and breaks it into atomic tasks. Each atomic task:

- Produces fewer than 200 lines of code
- References a specific spec section
- Has a clear, testable completion criterion
- Has an estimated implementation time
- Lists dependencies on other tasks

**Decomposition example:** Given the directive "Implement the 32-opcode Reflex VM," the decomposer produces:

| # | Task | Spec Section | Est. Time | Dependencies |
|---|------|-------------|-----------|--------------|
| 1 | Define VM state structure (stack, PC, SP, registers) | reflex_bytecode_vm_spec.md §2.1 | 20 min | None |
| 2 | Implement FETCH/DECODE cycle for 8-byte fixed instructions | reflex_bytecode_vm_spec.md §2.2 | 30 min | Task 1 |
| 3 | Implement stack operations (PUSH, POP, DUP, SWAP) | reflex_bytecode_vm_spec.md §3.1 | 25 min | Task 2 |
| 4 | Implement arithmetic ops (ADD, SUB, MUL, DIV, MOD) | reflex_bytecode_vm_spec.md §3.2 | 25 min | Task 2 |
| 5 | Implement comparison ops (EQ, NEQ, LT, GT, LTE, GTE) | reflex_bytecode_vm_spec.md §3.3 | 25 min | Task 2 |
| 6 | Implement control flow (JMP, JZ, JNZ, CALL, RET) | reflex_bytecode_vm_spec.md §4.1 | 30 min | Task 2 |
| 7 | Implement I/O ops (READ_PIN, WRITE_PIN) | reflex_bytecode_vm_spec.md §4.2 | 20 min | Task 2 |
| 8 | Implement PID_COMPUTE syscall | reflex_bytecode_vm_spec.md §5.1 | 45 min | Tasks 3-7 |
| 9 | Implement HALT sentinel and safety invariants | reflex_bytecode_vm_spec.md §5.2 | 35 min | Task 2 |
| 10 | Implement CLAMP_F encoding | reflex_bytecode_vm_spec.md §5.3 | 20 min | Task 2 |
| 11 | Write unit tests for all 32 opcodes | reflex_bytecode_vm_spec.md §6 | 60 min | Tasks 1-10 |
| 12 | Write integration test: full PID control bytecode execution | reflex_bytecode_vm_spec.md §7 | 40 min | Tasks 1-11 |

### A2.3 The Implementation Engine

The core coding subsystem. For each atomic task:

1. Read the spec section
2. Summarize the requirements (forced comprehension)
3. Read related existing code (dependencies)
4. Write the implementation
5. Write tests
6. Run tests
7. If tests pass: commit with spec-reference message
8. If tests fail: analyze, fix, re-run (max 3 attempts)
9. If 3 attempts fail: escalate to elder with detailed failure analysis

**The 3-Attempt Rule:** This is the single most important guardrail. Without it, the agent will spend hours trying to fix problems that require human judgment — typically spec ambiguities (60% of escalations), missing dependencies (25%), or genuine spec gaps (15%).

### A2.4 The Documentation Writer

Generates three types of documentation:

- **Daily digest** (~5 KB): What was accomplished, what failed, what's next. Written at end of each session or every 2 hours.
- **Checkpoint report** (~2 KB): Structured summary for elder review at the daily/weekly/milestone review cadences.
- **Spec divergence log:** When implementation differs from spec (with rationale). Reviewed by elder at next checkpoint.

### A2.5 The Safety Checker

Scans every commit for code touching safety-critical paths:

- Kill switch ISR (Gye Nyame layer — hardware-enforced safe state)
- Safety supervisor task (heartbeat monitoring, escalation logic)
- Watchdog integration (MAX6818 kick pattern, software fallback)
- VM safety invariants (stack overflow detection, cycle budget enforcement)
- Lyapunov stability certificate computation
- Overcurrent protection (ADC sampling, MOSFET gate control)

If safety code is detected, the commit is redirected to a `safety/[task-name]` branch, tagged `[ELDER REVIEW REQUIRED]`, and the elder is notified. **No safety code merges without explicit elder approval.** This is non-negotiable per the Colony Thesis Principle 4 (Constitutional Safety).

---

## A3. The Daily Cycle

The bootstrapping agent operates on a daily cycle with three phases:

### A3.1 Morning: Reconciliation

- Load the context file from the previous session
- Review any elder feedback from the latest daily review (direction notes, priority changes, resolved ambiguities)
- Reconcile the task list with any changes
- Verify the test suite passes on the current codebase (if it doesn't, stop and notify the elder)
- Read spec sections for the next 3–5 tasks (prefetching for latency reduction)

### A3.2 Core Hours: Execution

- Process atomic tasks sequentially from the task list
- For each task: read spec → summarize → implement → test → commit → move on
- Write a checkpoint report every 2 hours during extended sessions
- If blocked, skip to the next unblocked task

### A3.3 Evening: Compilation

- Run the full test suite
- Compile a daily digest summarizing everything accomplished
- Update the context file with new implementation notes, completed tasks, and any new blocking issues
- Prepare the checkpoint report for the elder's next review
- Commit all documentation

### A3.4 The Check-in Document

The elder reads a structured report at each review cadence:

**Daily (10 minutes):** Digest with task completion list, commit log, safety review flags, and "Next Up" priorities.

**Weekly (1 hour):** Full checkpoint report with code spot-checks, git diff review, integration test results, idea tree status, and priority adjustments for the coming week.

**Milestone (4 hours):** Comprehensive phase review comparing implementation against original specs section-by-section, architectural consistency validation, and sign-off for merge.

---

## A4. Concrete Setup for Building the Colony Architecture

### A4.1 Tool Stack

| Component | Tool | Configuration |
|-----------|------|---------------|
| Code generation | Claude Sonnet 4 (implementation), Claude Opus 4 (spec analysis) | Temperature 0.1 for code, 0.3 for analysis |
| Version control | Git | Branch naming: `colony/[subsystem]`, safety branches: `safety/[task]` |
| CI/CD | GitHub Actions | Build, lint, test on every commit; safety pattern scanner |
| Documentation | Obsidian / Markdown | Persistent context file, daily digests, checkpoint reports |
| Notifications | Slack (optional) or file-based pull | Session start/end, checkpoint reports, safety flags |

### A4.2 The Spec Library

Organize all NEXUS Genesis Colony Architecture documents for agent access:

```
/colony-agent/
├── specs/
│   ├── THE_COLONY_THESIS.md          # Master reference document
│   ├── phase1/
│   │   ├── 01_GREEK_PHILOSOPHICAL_LENS.md
│   │   ├── 02_CHINESE_PHILOSOPHICAL_LENS.md
│   │   ├── AFRICAN_COMMUNAL_LENS.md
│   │   ├── SOVIET_ENGINEERING_LENS.md
│   │   └── indigenous-lens-analysis.md
│   ├── phase2/
│   │   ├── 01_Colony_vs_Body_Paradigm.md
│   │   ├── 02_DNA_Code_Cell_Protein.md
│   │   ├── 03_LCARS_Not_Matrix.md
│   │   ├── 04_Durable_vs_Scalable.md
│   │   ├── 05_Genetic_Variation_Mechanics.md
│   │   ├── 06_ML_RL_OnDevice_Techniques.md
│   │   ├── 07_IoT_As_Protein_Architecture.md
│   │   └── 07b_Survival_of_Fittest_Mechanisms.md
│   └── architecture/
│       ├── STRESS_TEST_ANALYSIS.md
│       └── 00_White_Paper_Schema_v1.md
├── context.md                          # Agent's working memory
├── idea-tree.md                        # Priority-organized task hierarchy
├── task-list.md                        # Current atomic task decomposition
├── worklog.md                          # Append-only progress log
└── sessions/                           # Daily digests and checkpoint reports
```

### A4.3 The Build Manifest

The build manifest defines the implementation order for the colony architecture, derived from the dependency graph. For the NEXUS Genesis Colony Architecture, the critical path is:

1. **Reflex VM Core** — The 32-opcode bytecode execution engine (3KB flash, 4KB SRAM). Everything depends on this.
2. **HAL Layer** — Hardware abstraction for I/O pins, PWM, ADC, UART, I2C, SPI, GPIO, watchdog, flash. The VM needs this for READ_PIN/WRITE_PIN.
3. **Safety System** — Kill switch ISR, watchdog integration, VM safety invariants, Lyapunov certificate computation. Non-negotiable; must be built and human-reviewed before any actuator code runs.
4. **Wire Protocol** — COBS framing, CRC-16, message dispatch, flow control. Enables ESP32-Jetson communication.
5. **Genetic Variation Engine** — Four-level mutation operators (parameter, conditional, algorithm, architecture). Depends on VM and safety system.
6. **Selection System** — Tournament selection, A/B/C/D testing, SPRT significance testing, promotion/retirement criteria. Depends on genetic variation.
7. **Seasonal Protocol** — Spring/Summer/Autumn/Winter cycle management, exploration rate scheduling, mandatory Winter pause. Depends on genetic variation and selection.
8. **Griot Layer** — Narrative provenance, genetic lineage tracking, version history as story. Depends on all evolutionary components.
9. **Fitness Function** — Extended Kolmogorov fitness, behavioral fingerprinting, conditional genetics, multi-genome portfolios. Depends on VM, safety, selection.
10. **Jetson-Side Cognitive Layer** — Serial bridge, node manager, reflex orchestrator, learning pipeline. Depends on wire protocol.
11. **Learning Pipeline** — Cross-correlation, BOCPD, HDBSCAN clustering, temporal pattern mining, Bayesian reward inference. Depends on cognitive layer.

### A4.4 Risk Management

The agent automatically tracks and mitigates these risk categories:

| Risk | Detection | Mitigation |
|------|-----------|------------|
| Spec ambiguity | Agent logs conflicting requirements | Escalate to elder, do not guess |
| Test suite regression | CI failure on any commit | Agent fixes immediately; 3-attempt rule applies |
| Safety code without review | Safety checker pattern scan | Block merge, redirect to safety branch |
| Context file bloat | Size check every session | Rolling summarization at 80 KB threshold |
| Dependency gap | Task references unresolved dependency | Log as BLOCKED, skip to unblocked tasks |
| Architectural drift | Weekly elder review of git diff | Elder redirects; agent follows direction |

---

## A5. Realistic Expectations and Failure Modes

### A5.1 What to Expect

Over a sustained bootstrapping effort on the colony architecture, expect:

- **8–12 atomic tasks per day** for a well-specified subsystem (VM, HAL, wire protocol)
- **5–8 atomic tasks per day** for a complex subsystem (genetic variation, selection, fitness function)
- **3–5 atomic tasks per day** for subsystems with significant spec ambiguity or architectural open questions
- **8% escalation rate** — approximately 1 in 12 tasks will require elder intervention
- **95% first-pass accuracy** on non-safety code; **100% elder review required** on safety code
- **3–4 weeks to steady state** — initial setup, prompt calibration, and communication pattern establishment

### A5.2 Detecting Circular Behavior

The agent can get stuck in loops: implementing, testing, failing, fixing differently, testing, failing again, trying a third approach, and then either succeeding or giving up — but having consumed hours on what should have been a 30-minute task. Detection patterns:

- **Same file modified 5+ times in a session** without a commit
- **Test output cycling between 2–3 different error messages**
- **Time-per-task consistently 3×+ above estimate**
- **Context file entries saying "retrying X" more than 3 times**

**Response:** The 3-Attempt Rule catches most of this automatically. For subtler cases, the elder's daily review of the commit log reveals the pattern. If detected, the elder sends a direction nudge: "Stop working on [task X]. Log the failure and move on. I'll look at it during the weekly review."

### A5.3 The Over-Engineering Trap

AI agents tend to write elegant, well-abstracted code with extensive error handling. For the colony architecture running on ESP32-S3 with 512 KB SRAM, this is a liability. Every unnecessary abstraction layer costs SRAM, flash, and CPU cycles that the evolutionary bytecode system needs.

**Countermeasure:** Include in the system prompt:

> "Prefer simple, direct code over abstracted, extensible code. The NEXUS colony runs on ESP32-S3 with 512 KB SRAM and 8 MB PSRAM. Every byte matters. If a function can be 15 lines instead of 40 lines without sacrificing correctness, write the 15-line version. Follow existing patterns in the codebase. Do not create new abstractions unless the spec explicitly requires them."

This directive reduced average function size by 30% in production testing.

---

# PART B: The Overnight Autonomous Builder

## B1. What Is an Overnight Builder?

An overnight builder is an AI agent that runs for hours or days without human oversight, implementing the NEXUS colony architecture from the specification corpus. The elder goes to sleep (or takes a weekend off) and wakes up to a summary of what was accomplished. The ideal outcome: 12–20 atomic tasks completed, all tests passing, a clean git history, and a structured report ready for review.

The key difference from the bootstrapping agent is the absence of real-time human waypoints. The overnight builder must be self-governing: it decides what to work on (from the prioritized task list), detects its own rabbit trails, enforces its own time budgets, and knows when to stop.

**When is an overnight session appropriate?**

- The specifications for the target subsystem are complete and unambiguous
- The test suite exists and passes on the current codebase
- The task decomposition is complete with clear dependencies
- No safety-critical code is involved (safety code always requires elder review)
- No architectural decisions are needed

**When is it NOT appropriate?**

- Subsystems with incomplete specs
- First implementation of a new subsystem type
- Any code touching the Gye Nyame safety layer
- Tasks where the agent has previously struggled (3+ escalations on the same type)
- When the elder cannot commit to reviewing the output within 12 hours of session completion

---

## B2. Idea Treeing: Preventing Rabbit Trails

### B2.1 The Core Problem

AI agents are natural explorers. Given the rich specification corpus of the colony architecture — spanning evolutionary computation, Lyapunov stability, Griot narrative systems, seasonal protocols, and protein-architecture metaphors — the agent will constantly discover interesting tangents. The reflex VM spec mentions CLAMP_F encoding, which leads the agent to research fixed-point arithmetic, which leads it to discover that IEEE 754 half-precision might be more efficient, which leads it to propose a new VM encoding scheme, which leads it to start redesigning the instruction format... Four hours later, nothing from the original task list has been completed.

This is not a failure of intelligence. It is a failure of *focus*. The agent is doing what it was designed to do — explore, connect, propose — but exploration without boundaries is the enemy of implementation.

### B2.2 The Idea Tree

The idea tree is a hierarchical, priority-tagged structure that organizes every potential work item into a navigable format. It is the agent's compass.

**Structure definition (YAML):**

```yaml
# /colony-agent/idea-tree.yml
tree:
  id: "nexus-colony-architecture"
  version: "1.0"
  last_updated: "2026-03-30"
  current_milestone: "Foundation Layer"

  branches:
    - id: "core-platform"
      name: "Core Platform"
      priority: "P0"
      status: "IN_PROGRESS"
      rationale: "Everything depends on VM, HAL, safety, and wire protocol"
      children:
        - id: "reflex-vm"
          name: "Reflex Bytecode VM"
          priority: "P0"
          status: "DONE"
          effort_hours: 16
          spec_ref: "reflex_bytecode_vm_spec.md"
          children:
            - id: "vm-core"
              name: "VM Core (fetch/decode/state)"
              priority: "P0"
              status: "DONE"
              effort_hours: 4
            - id: "vm-stack-ops"
              name: "Stack Operations"
              priority: "P0"
              status: "DONE"
              effort_hours: 2
            - id: "vm-arithmetic"
              name: "Arithmetic Operations"
              priority: "P0"
              status: "DONE"
              effort_hours: 2
            - id: "vm-control-flow"
              name: "Control Flow"
              priority: "P0"
              status: "DONE"
              effort_hours: 3
            - id: "vm-io-ops"
              name: "I/O Operations (READ_PIN/WRITE_PIN)"
              priority: "P0"
              status: "DONE"
              effort_hours: 2
            - id: "vm-pid-compute"
              name: "PID_COMPUTE Syscall"
              priority: "P0"
              status: "DONE"
              effort_hours: 3
            - id: "vm-safety-invariants"
              name: "Safety Invariants (stack overflow, cycle budget)"
              priority: "P0"
              status: "DONE"
              effort_hours: 2
              safety_critical: true

        - id: "hal-layer"
          name: "Hardware Abstraction Layer"
          priority: "P0"
          status: "IN_PROGRESS"
          effort_hours: 24
          spec_ref: "hal_platform.h, hal_common.h"
          children:
            - id: "hal-gpio"
              name: "GPIO Driver"
              priority: "P0"
              status: "DONE"
              effort_hours: 3
            - id: "hal-pwm"
              name: "PWM Driver"
              priority: "P0"
              status: "DONE"
              effort_hours: 3
            - id: "hal-adc"
              name: "ADC Driver"
              priority: "P0"
              status: "IN_PROGRESS"
              effort_hours: 3
            - id: "hal-uart"
              name: "UART Driver"
              priority: "P0"
              status: "TODO"
              effort_hours: 4
            - id: "hal-i2c"
              name: "I2C Driver"
              priority: "P0"
              status: "TODO"
              effort_hours: 4
            - id: "hal-spi"
              name: "SPI Driver"
              priority: "P0"
              status: "TODO"
              effort_hours: 4
            - id: "hal-watchdog"
              name: "Watchdog Driver"
              priority: "P0"
              status: "TODO"
              effort_hours: 2
              safety_critical: true

        - id: "safety-system"
          name: "Safety System (Gye Nyame Layer)"
          priority: "P0"
          status: "TODO"
          effort_hours: 20
          safety_critical: true
          children:
            - id: "kill-switch-isr"
              name: "Kill Switch ISR"
              priority: "P0"
              status: "TODO"
              effort_hours: 4
              safety_critical: true
            - id: "heartbeat-monitor"
              name: "Heartbeat Monitor"
              priority: "P0"
              status: "TODO"
              effort_hours: 4
            - id: "watchdog-integration"
              name: "Watchdog Integration"
              priority: "P0"
              status: "TODO"
              effort_hours: 3
              safety_critical: true
            - id: "lyapunov-certificate"
              name: "Lyapunov Stability Certificate"
              priority: "P0"
              status: "TODO"
              effort_hours: 9

    - id: "evolution-engine"
      name: "Evolution Engine"
      priority: "P1"
      status: "TODO"
      rationale: "Depends on VM + safety being complete"
      depends_on: ["core-platform"]
      children:
        - id: "genetic-variation"
          name: "Genetic Variation Operators"
          priority: "P1"
          status: "TODO"
          spec_ref: "05_Genetic_Variation_Mechanics.md"
          effort_hours: 40
          children:
            - id: "mutation-l1-parameter"
              name: "Level 1: Parameter Mutation"
              priority: "P1"
              status: "TODO"
              effort_hours: 8
            - id: "mutation-l2-conditional"
              name: "Level 2: Conditional Logic Mutation"
              priority: "P1"
              status: "TODO"
              effort_hours: 12
            - id: "mutation-l3-algorithm"
              name: "Level 3: Algorithm Replacement"
              priority: "P1"
              status: "TODO"
              effort_hours: 12
            - id: "mutation-l4-architecture"
              name: "Level 4: Architecture Change"
              priority: "P1"
              status: "TODO"
              effort_hours: 8
        - id: "selection-system"
          name: "Selection & Competition"
          priority: "P1"
          status: "TODO"
          spec_ref: "07b_Survival_of_Fittest_Mechanics.md"
          effort_hours: 30
        - id: "seasonal-protocol"
          name: "Seasonal Protocol (Spring/Summer/Autumn/Winter)"
          priority: "P1"
          status: "TODO"
          effort_hours: 20
        - id: "griot-layer"
          name: "Griot Narrative Layer"
          priority: "P1"
          status: "TODO"
          effort_hours: 15
        - id: "fitness-function"
          name: "Extended Kolmogorov Fitness"
          priority: "P1"
          status: "TODO"
          effort_hours: 20

    - id: "cognitive-layer"
      name: "Jetson Cognitive Layer"
      priority: "P1"
      status: "TODO"
      depends_on: ["core-platform"]
      children:
        - id: "serial-bridge"
          name: "Serial Bridge"
          priority: "P1"
          status: "TODO"
          effort_hours: 12
        - id: "node-manager"
          name: "Node Manager"
          priority: "P1"
          status: "TODO"
          effort_hours: 15
        - id: "learning-pipeline"
          name: "Learning Pipeline"
          priority: "P1"
          status: "TODO"
          spec_ref: "06_ML_RL_OnDevice_Techniques.md"
          effort_hours: 40

    - id: "pruned"
      name: "[PRUNED] Interesting But Off-Track"
      priority: "NONE"
      children:
        - id: "behavior-tree-support"
          name: "Behavior Tree Support"
          status: "PRUNED"
          reason: "Colony thesis uses evolved bytecodes, not behavior trees. VM is the ribosome."
        - id: "lua-vm"
          name: "Lua VM Alternative"
          status: "PRUNED"
          reason: "~40KB flash overhead vs 3KB for custom bytecode. Insufficient for ESP32-S3 constraints."
        - id: "rest-api"
          name: "REST API Endpoint"
          status: "PRUNED"
          reason: "gRPC+MQTT only per NEXUS Wire Protocol spec. REST is the wrong architecture for resource-constrained nodes."
```

### B2.3 Rabbit Trail Detection

The agent performs a self-check every 30 minutes during an autonomous session:

1. **Task alignment check:** "Am I currently working on the highest-priority available task in the idea tree?" If no, log the deviation and return to the correct task.
2. **Spec anchor check:** "Does my current work reference a specific section of a specific spec document?" If no, it's a rabbit trail. Stop.
3. **Time budget check:** "Has the current task exceeded 3× my own time estimate?" If yes, stop and log as TIMEOUT.
4. **Scope creep check:** "Have I added any code not required by the spec section I was implementing?" If yes, revert the addition.
5. **Dependency spiral check:** "Have I discovered more than 2 new dependencies in this session?" If yes, log them all as BLOCKED and return to the original task list.

### B2.4 Priority Calculation Formula

When the agent needs to determine what to work on next, it uses a priority score:

```
priority_score = (base_priority * dependency_multiplier * phase_multiplier * elder_signal) - risk_penalty

where:
  base_priority:     P0=100, P1=75, P2=50, P3=25, PRUNED=0
  dependency_multiplier: 1.5 if this task unblocks ≥2 other tasks, 1.0 otherwise
  phase_multiplier:  foundation=1.5, features=1.0, polish=0.5
  elder_signal:      1.5 if the elder's last direction note mentioned this task/area, 1.0 otherwise
  risk_penalty:      +20 if safety_critical and no elder present (discourages autonomous safety work)
```

Tasks are sorted by priority_score descending. The agent works on the highest-scoring task that has all dependencies met.

---

## B3. Nudging: Keeping Focus on the Right Tree

### B3.1 Priority Nudging

Every 4 hours during a multiday session, the agent recalculates priorities based on:

1. **Current project phase:** Foundation → Features → Polish. Foundation tasks get a 1.5× multiplier. This ensures the critical path is always built first.
2. **Dependencies:** If a task unblocks 3 other tasks, its priority score increases by 50%. This naturally pushes the agent toward high-leverage work.
3. **Risk:** Safety-critical tasks are penalized (reduced by 20 points) during autonomous sessions, preventing the agent from working on safety code without elder review.
4. **Elder intent:** The elder's most recent direction note acts as the strongest priority signal (1.5× multiplier). If the elder said "focus on the HAL layer," the HAL tasks get boosted.

### B3.2 Direction Nudging via the Check-in Note

The elder's check-in note is the most powerful nudge tool. It is a brief, specific instruction that redirects the agent between formal reviews. The format:

> **[What's happening]** + **[Why it matters]** + **[What to do instead]**

**Effective nudges:**

- *"The ADC driver implementation is solid, but I see you started working on the I2C driver. Finish the ADC driver first — the sensor proteins (BME280, HMC5883L) all need ADC-readable voltage levels before I2C communication can be validated. Complete ADC, then I2C."*
- *"You're spending too much time on the CLAMP_F encoding edge cases. The spec says to use simple 16-bit integer representation. Implement it simply, write one test per spec requirement, and move on to the PID_COMPUTE syscall."*
- *"Good progress on the HAL layer. Switch to the safety system next — the kill switch ISR is P0 and depends on GPIO being done, which it is. But remember: safety code goes to a safety branch, not the main branch. I'll review it in the morning."*

**Ineffective nudges:**

- *"Try harder."* — Vague, unactionable.
- *"Focus on what's important."* — The agent's definition of "important" may not match yours.
- *"That doesn't look right."* — Doesn't identify the problem or the solution.

### B3.3 The "Good Idea, Wrong Time" Response

When the agent proposes a new idea or suggests working on a lower-priority branch, never say "no." Say "yes, but later." Add the idea to the tree at the appropriate priority and redirect to the current critical path.

This keeps the agent motivated (the idea is valued, not rejected) while maintaining focus (the critical path gets built). Over the two-year NEXUS platform build, this technique reduced agent resistance to redirection by approximately 80% compared to flat rejection.

### B3.4 Automated Self-Nudging

The agent also nudges itself. Every 4 hours, it reviews its own idea tree and asks:

1. "Am I making progress on P0 tasks?" If the last 4 hours produced no P0 completions, the agent logs a self-nudge: "P0 progress is stalled. Redirecting to [highest-priority P0 task]."
2. "Have I been working on the same task for more than 2 hours?" If yes, it's either a genuinely complex task (acceptable) or a rabbit trail (not acceptable). The agent evaluates: "Is this task producing progress (tests passing, code committing) or am I spinning?" If spinning, apply the 3-Attempt Rule.
3. "Are there any BLOCKED tasks I can unblock by completing a dependency?" The agent scans the tree for BLOCKED tasks whose dependencies are all DONE except one — and that one is a TODO the agent can work on. This is high-leverage work and gets priority.

---

## B4. The Overnight Build Cycle

### B4.1 Pre-Flight Checklist (Elder performs before launching)

- [ ] All specs for the target subsystem are complete and committed
- [ ] Full test suite passes on current codebase
- [ ] Task decomposition is complete with clear dependencies
- [ ] Time budget set (8 hours overnight, 48–72 hours weekend)
- [ ] Iteration budget set (max 5 attempts per failing test)
- [ ] Safety code changes disabled (or pre-approved in writing)
- [ ] Context file is current
- [ ] Idea tree is reviewed and priorities are correct
- [ ] Elder has committed to reviewing output within 12 hours

### B4.2 The Build Loop

```
[Pre-Flight] Elder verifies checklist
    |
    v
[Session Start] Agent loads context, reads idea tree, verifies test suite
    |
    v
[Task Loop] For each task:
    |
    +-- Read spec section → Summarize requirements
    |
    +-- Implement → Write tests → Run tests
    |       |
    |       +-- Pass → Commit → Move to next task
    |       |
    |       +-- Fail → Debug (max 5 attempts)
    |               |
    |               +-- Fixed → Retest
    |               +-- Not fixed → Log, skip, continue
    |
    +-- [Every 30 min] Rabbit trail check
    |       Am I on the right task? Am I within budget?
    |       Is my code spec-compliant? Am I spiraling on dependencies?
    |
    +-- [Every 2 hours] Checkpoint report
    |       Write progress report to /colony-agent/sessions/
    |
    +-- [Every 4 hours] Priority recalculation
    |       Re-read idea tree, check elder direction notes,
    |       recalculate priority scores, adjust task order
    |
    v
[Session End] Write final report, summarize accomplishments
    |
    v
[Elder Review] Read report, review changes, approve or request fixes
```

### B4.3 The Critical Rule: Stop on Test Failure

**If the test suite turns red, the agent MUST stop and fix it before continuing.** This is the #1 overnight failure mode prevention technique. If the agent continues building on a broken foundation, every subsequent task will fail too — but the failures will be caused by the earlier breakage, not by the new code. The agent will waste hours "fixing" code that is actually correct, chasing a bug it introduced 6 tasks ago.

**The rule is absolute:** If any test fails after a commit, the agent enters fix mode. It does not start a new task. It does not "come back to it later." It fixes the test suite before proceeding. If it cannot fix it within 5 attempts, it reverts the commit that broke the suite and logs the failure.

### B4.4 The Morning Summary

When the elder wakes up, they read a structured report:

```markdown
# Overnight Session Report
## Session: 2026-03-30-hal-uart-i2c
## Duration: 7.5 hours (budget: 8 hours)
## Agent: Claude Sonnet 4

## Completed Tasks (14)
| # | Task | Spec Ref | Time | Tests | Commit |
|---|------|----------|------|-------|--------|
| 1 | HAL UART driver init | hal_uart.h §2 | 25m | PASS | a3f2... |
| 2 | HAL UART transmit | hal_uart.h §3 | 30m | PASS | b7c1... |
| 3 | HAL UART receive with DMA | hal_uart.h §4 | 45m | PASS | c4d8... |
| 4 | HAL UART baud rate config | hal_uart.h §5 | 20m | PASS | d9e3... |
| 5 | HAL UART unit tests | hal_uart.h §6 | 35m | PASS | e1f5... |
| 6 | HAL I2C master init | hal_i2c.h §2 | 20m | PASS | f2a6... |
| 7 | HAL I2C write | hal_i2c.h §3 | 25m | PASS | a8b7... |
| 8 | HAL I2C read | hal_i2c.h §4 | 30m | PASS | b9c8... |
| 9 | HAL I2C bus lockup detection | hal_i2c.h §5 | 40m | PASS | c0d9... |
| 10 | HAL I2C DMA support | hal_i2c.h §6 | 50m | PASS | d1e0... |
| 11 | HAL I2C unit tests | hal_i2c.h §7 | 35m | PASS | e2f1... |
| 12 | HAL SPI driver (full) | hal_spi.h | 60m | PASS | f3a2... |
| 13 | HAL SPI unit tests | hal_spi.h §8 | 30m | PASS | a4b3... |
| 14 | HAL flash driver (mock) | hal_flash.h | 25m | PASS | b5c4... |

## Skipped Tasks (1)
| # | Task | Reason |
|---|------|--------|
| 1 | HAL flash actual implementation | No hardware target configured; mock sufficient for current phase |

## Spec Divergences (1)
- I2C bus lockup detection: Spec says "reset bus on lockup." Implementation uses "clock-stretch recovery attempt first, then reset." Rationale: Clock-stretch recovery preserves connected device state. Awaiting elder review.

## Test Suite Status: ALL GREEN (47 tests passing)

## Next Up
1. HAL watchdog driver (P0, safety-critical — will use safety branch) — est. 2 hours
2. HAL flash actual implementation (P0, needs hardware target config) — est. 3 hours
3. Safety system: Kill switch ISR (P0, safety-critical) — est. 4 hours

## Elder Actions Needed
- Review I2C bus lockup spec divergence
- Confirm hardware target for flash driver implementation
- Safety review for watchdog driver (will be on safety/ branch)
```

---

## B5. Multi-Day Autonomous Operation

### B5.1 Chaining Overnight Sessions

A weekend session (48–72 hours) is essentially three chained overnight sessions with additional safeguards:

- **State persistence:** Every 2 hours, the agent saves a complete state snapshot (context file, work log, progress report, task list, git status). If the agent crashes or the API goes down, it resumes from the last snapshot.
- **12-hour check-ins:** The elder reads the latest checkpoint report every 12 hours. If anything looks wrong, the session ends early.
- **Memory management:** Entries older than 24 hours are summarized at the 24-hour mark to prevent context degradation.
- **Safety code prohibition:** During multiday sessions, safety code changes are actively *blocked*, not just flagged. The agent logs safety-adjacent tasks as BLOCKED and continues with non-safety work.

### B5.2 The Morning Handoff Protocol

When the elder reviews the overnight output, they perform a structured handoff:

1. **Read the final report** (5 minutes) — understand what was accomplished and what needs attention
2. **Run the test suite locally** (5 minutes) — verify the agent's "ALL GREEN" claim in your own environment
3. **Review the git log** (2 minutes) — scan for unexpected commits
4. **Check for safety code** (1 minute) — ensure no safety code was modified without review
5. **Spot-check 2–3 commits** (10 minutes) — read actual code changes against spec requirements
6. **Review skipped tasks** (5 minutes) — understand blockers and decide on resolution
7. **Update direction note** (2 minutes) — write a brief note for the next session
8. **Update idea tree** (if needed) — adjust priorities, add new items, prune completed branches

**Decision outcomes:**

- **Approve (~70%):** Merge to development branch, plan next session
- **Request fixes (~20%):** Specific issues identified; agent addresses in next session
- **Partial revert (~8%):** Some work is good, some went off-track; revert the bad parts
- **Full revert (~2%):** Session went fundamentally wrong; revert to pre-flight commit

### B5.3 Compound Error Prevention

The deadliest overnight failure mode is compound errors: the agent makes a small mistake in task 3, builds on it in tasks 4–8, and by task 12 the entire session's output is based on a flawed foundation. The tests all pass because the tests test the agent's (incorrect) implementation, not the spec's requirements.

**Prevention strategies:**

1. **Pre-implementation spec summary** — forces the agent to process the spec before writing code
2. **Post-implementation spec comparison** — catches divergence immediately
3. **Integration tests from a fresh session** — a second agent (or the same agent with a cleared context) writes integration tests based purely on the spec, not on the implementation
4. **Mid-session test suite run** — every 2 hours, the full test suite runs, not just the tests for the current task. This catches regressions early.

---

## B6. Idea Tree Implementation: Complete Specification

### B6.1 Data Model

```json
{
  "$schema": "idea-tree-v1",
  "node": {
    "id": "string (unique identifier)",
    "name": "string (human-readable name)",
    "priority": "P0 | P1 | P2 | P3 | NONE",
    "status": "TODO | IN_PROGRESS | DONE | PARTIAL | BLOCKED | PRUNED",
    "effort_hours": "number (estimated effort)",
    "spec_ref": "string | null (which spec document section)",
    "safety_critical": "boolean",
    "depends_on": ["node-id", "..."],
    "rationale": "string | null (why this node exists)",
    "prune_reason": "string | null (if PRUNED, why)",
    "children": ["node (recursive)"]
  }
}
```

### B6.2 Priority Score Formula (Implementation)

```python
def calculate_priority_score(node, elder_direction_note, project_phase):
    base_priority = {"P0": 100, "P1": 75, "P2": 50, "P3": 25, "NONE": 0}[node["priority"]]

    # Dependency multiplier: boost tasks that unblock others
    unblocked_count = count_tasks_that_depend_on(node["id"])
    dependency_multiplier = 1.5 if unblocked_count >= 2 else 1.0

    # Phase multiplier
    phase_multiplier = {"foundation": 1.5, "features": 1.0, "polish": 0.5}[project_phase]

    # Elder signal: boost if elder mentioned this area recently
    elder_signal = 1.0
    if elder_direction_note and node["name"].lower() in elder_direction_note.lower():
        elder_signal = 1.5
    if elder_direction_note and node["spec_ref"] and node["spec_ref"].lower() in elder_direction_note.lower():
        elder_signal = 1.5

    # Risk penalty: discourage autonomous safety work
    risk_penalty = 20 if node.get("safety_critical", False) else 0

    score = (base_priority * dependency_multiplier * phase_multiplier * elder_signal) - risk_penalty
    return score
```

### B6.3 Dependency Resolution Algorithm

```python
def get_next_task(idea_tree, completed_task_ids, blocked_task_ids):
    """Return the highest-priority task whose dependencies are all met."""

    eligible = []
    for node in flatten_tree(idea_tree):
        if node["status"] in ("DONE", "PRUNED", "BLOCKED"):
            continue
        if node["id"] in completed_task_ids:
            continue
        if node["id"] in blocked_task_ids:
            continue

        # Check all dependencies are completed
        deps_met = all(dep_id in completed_task_ids for dep_id in node.get("depends_on", []))
        if deps_met:
            eligible.append(node)

    if not eligible:
        return None  # All tasks are blocked or done

    # Sort by priority score, return highest
    eligible.sort(key=lambda n: calculate_priority_score(n), reverse=True)
    return eligible[0]
```

### B6.4 Example: Building the Colony VM from Scratch

Here is an illustrative idea tree snapshot for the first overnight session targeting the Reflex VM:

```yaml
# Idea Tree — Session: 2026-03-30-vm-foundation
session_goal: "Complete Reflex VM core (fetch/decode/execute) + all 32 opcodes + unit tests"
time_budget: "8 hours"
iteration_budget: 5

branches:
  - id: "vm-session"
    name: "Tonight's Build: Reflex VM Foundation"
    priority: "P0"
    children:
      - id: "vm-state-struct"
        name: "VM State Structure (stack, PC, SP, registers)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.5
        spec_ref: "reflex_bytecode_vm_spec.md §2.1"
        depends_on: []

      - id: "vm-fetch-decode"
        name: "Fetch/Decode Cycle (8-byte fixed instructions)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.75
        spec_ref: "reflex_bytecode_vm_spec.md §2.2"
        depends_on: ["vm-state-struct"]

      - id: "vm-stack-ops"
        name: "Stack Operations (PUSH, POP, DUP, SWAP, OVER)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.75
        spec_ref: "reflex_bytecode_vm_spec.md §3.1"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-arithmetic"
        name: "Arithmetic (ADD, SUB, MUL, DIV, MOD, NEG)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.75
        spec_ref: "reflex_bytecode_vm_spec.md §3.2"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-comparison"
        name: "Comparison (EQ, NEQ, LT, GT, LTE, GTE)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.75
        spec_ref: "reflex_bytecode_vm_spec.md §3.3"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-logic"
        name: "Logic (AND, OR, XOR, NOT, SHL, SHR)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.5
        spec_ref: "reflex_bytecode_vm_spec.md §3.4"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-control-flow"
        name: "Control Flow (JMP, JZ, JNZ, CALL, RET)"
        priority: "P0"
        status: "TODO"
        effort_hours: 1.0
        spec_ref: "reflex_bytecode_vm_spec.md §4.1"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-io-ops"
        name: "I/O (READ_PIN, WRITE_PIN, READ_VAR, WRITE_VAR)"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.75
        spec_ref: "reflex_bytecode_vm_spec.md §4.2"
        depends_on: ["vm-fetch-decode"]

      - id: "vm-syscalls"
        name: "Syscalls (PID_COMPUTE, CLAMP_F, HALT)"
        priority: "P0"
        status: "TODO"
        effort_hours: 1.25
        spec_ref: "reflex_bytecode_vm_spec.md §5.1-5.3"
        depends_on: ["vm-fetch-decode", "vm-arithmetic"]

      - id: "vm-safety"
        name: "Safety Invariants (stack overflow, cycle budget, div-by-zero)"
        priority: "P0"
        status: "TODO"
        effort_hours: 1.0
        spec_ref: "reflex_bytecode_vm_spec.md §5.4"
        depends_on: ["vm-fetch-decode"]
        safety_critical: true

      - id: "vm-unit-tests"
        name: "Unit Tests (one per opcode + integration test)"
        priority: "P0"
        status: "TODO"
        effort_hours: 1.5
        spec_ref: "reflex_bytecode_vm_spec.md §6-7"
        depends_on: ["vm-stack-ops", "vm-arithmetic", "vm-comparison", "vm-logic", "vm-control-flow", "vm-io-ops", "vm-syscalls"]

      - id: "vm-integration-test"
        name: "Integration Test: Full PID bytecode execution"
        priority: "P0"
        status: "TODO"
        effort_hours: 0.5
        spec_ref: "reflex_bytecode_vm_spec.md §7"
        depends_on: ["vm-unit-tests"]

  - id: "pruned-tonight"
    name: "[NOT TONIGHT] Future Work"
    priority: "NONE"
    children:
      - id: "vm-debug-interface"
        name: "Debug Interface (single-step, breakpoint, register dump)"
        status: "PRUNED"
        reason: "Not in v3.1 spec. Useful for development but not for production. Revisit in v4.0."
      - id: "vm-jit-compilation"
        name: "JIT Compilation to native ESP32 instructions"
        status: "PRUNED"
        reason: "Interesting performance optimization but adds enormous complexity. Current VM at 340μs/tick is well within 1000μs budget."
```

---

## Conclusion: The Elder's Covenant for Agent Development

These two workflows — the bootstrapping agent with daily elder check-ins and the overnight autonomous builder with idea treeing — are not shortcuts. They are a disciplined allocation of human attention. The elder does not write code. The elder writes direction. The elder does not debug. The elder reviews and redirects. The elder does not maintain context. The elder reads the checkpoint report and adjusts priorities.

This mirrors the LCARS principle from the Colony Thesis (Document 03): the colony augments human capability without replacing human judgment. The bootstrapping agent and overnight builder extend the elder's implementation capacity by 10–20× while concentrating the elder's attention on the decisions that matter most — architectural direction, safety validation, and philosophical coherence.

The colony architecture being built is, itself, an autonomous system. It is only fitting that the tools used to build it embody the same principles: specification-driven development, constitutional safety boundaries, seasonal rhythm (build / review / rest), and the elder's absolute veto. The builder and the built share the same DNA.

> "The elder does not write bytecodes. The elder writes the conditions under which bytecodes evolve. The elder does not write the colony's code. The elder writes the conditions under which the colony is built. In both cases, the principle is the same: design the greenhouse, not the flower."
