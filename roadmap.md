# NEXUS Master Build Roadmap

**Document ID:** NEXUS-ROADMAP-MASTER
**Version:** 1.0.0
**Date:** 2025-07-12
**Status:** ACTIVE — Definitive Build Plan
**Classification:** Engineering-Critical

---

## Executive Summary

NEXUS is a distributed intelligence platform for industrial robotics where LLM agents — not humans — are the primary authors, interpreters, and validators of control code. The system executes on a bytecode virtual machine running on embedded hardware (ESP32-S3, 240MHz, 512KB SRAM) with AI cognition on edge GPUs (Jetson Orin Nano, 40 TOPS, 8GB LPDDR5), governed by a mathematical trust algorithm (INCREMENTS) that requires 27 days of safe operation before any subsystem earns full autonomy.

The architecture inverts the conventional robotics paradigm. Rather than centralizing intelligence in a "brain" with dumb actuators, NEXUS distributes intelligence to the periphery. Each limb runs a bytecode VM on an ESP32-S3 that executes reflex programs at 1ms ticks. The Jetson provides AI cognition — pattern discovery, natural language reflex synthesis, A/B testing — but the ESP32 maintains safe control even when ALL higher tiers fail. Like a biological ribosome translating mRNA into proteins without understanding, the ESP32 executes bytecode without comprehension. Like the brain planning and learning, the Jetson synthesizes new reflexes and improves existing ones.

**What exists today:** 21 production specification files totaling 19,200 lines covering the 32-opcode bytecode VM, wire protocol (28 message types, COBS framing, CRC-16), four-tier safety system, INCREMENTS trust algorithm (12 parameters, 6 autonomy levels, 15 event types), and the learning pipeline (5 pattern discovery algorithms). A 27-article knowledge base encyclopedia (333,775 words). A2A-native language research (45,191 words across 6 documents). Monte Carlo safety simulations showing >99.97% safe-state achievement. Trust score evolution simulations validating the 25:1 loss-to-gain ratio. VM performance benchmarks (44μs per tick). No production code has been written. No hardware has been flashed.

**What must be built:** ESP32 firmware (VM interpreter, wire protocol, I/O drivers, safety monitors), Jetson software (LLM inference pipeline, reflex compiler, MQTT bridge, learning pipeline), cloud services (fleet management, heavy training, simulation), A2A-native language implementation (hybrid compiler/interpreter), safety validation infrastructure (hardware-in-loop testing, certification evidence), and reference hardware (PCB design, marine vessel integration).

**Budget:** $2.6M over 36 months, phased across 6 build phases with 5 major milestones. Team scales from 3 developers in Phase 0 to 12 in Phase 5. Hardware costs are front-loaded ($527 in Phase 0, scaling to $50K+ for multi-vessel sea trials). Cloud and regulatory costs dominate later phases ($180K-$480K for EU AI Act compliance alone).

**This document is the single source of truth for what to build, in what order, with what dependencies, and what success looks like at every step.** If code disagrees with this roadmap, the roadmap wins until it is formally updated. Every sprint has concrete deliverables, measurable pass/fail criteria, and explicit spec references.

---

## Build Philosophy

### Specs Are Source of Truth

Every specification in `specs/` is the authoritative engineering reference. The VM interpreter must match `reflex_bytecode_vm_spec.md` opcode-for-opcode, cycle-for-cycle. The wire protocol must match `wire_protocol_spec.md` frame-for-frame, CRC polynomial and all. The trust algorithm must match `trust_score_algorithm_spec.md` formula-for-formula, with identical parameter defaults. If a builder discovers a conflict between implementation and spec, the spec wins — file a GitHub issue and update the code, never the spec.

### Safety Is Non-Negotiable

Every pull request must preserve the four-tier safety invariants defined in `safety_system_spec.md`. Tier 1 (hardware interlock) operates regardless of firmware state. Tier 2 (firmware safety guard) overrides all application code via ISR. Tier 3 (supervisory task) monitors heartbeat and enforces the safety state machine. Tier 4 (application control) is the lowest authority — it can be overridden, suspended, or terminated at any time. No PR that weakens any tier will be merged. No exceptions.

### Iterative Delivery

Every phase boundary produces a working system. Phase 0 produces a system that compiles and runs on both targets. Phase 1 produces a system that deploys reflexes via LLM. Phase 2 produces a marine-grade platform with 72-hour continuous operation. Phase 3 produces a learning system that discovers patterns and improves its own behavior. Phase 4 produces an A2A-native system where agents write the code. Phase 5 produces a self-evolving platform. No phase ends with "specs written but nothing running."

### Test-Driven Engineering

Every component has three test layers: (1) unit tests that verify individual functions against spec-defined behavior (e.g., each of the 32 opcodes tested against spec test vectors), (2) integration tests that verify subsystem interactions (e.g., wire protocol round-trip between ESP32 and Jetson), and (3) hardware-in-loop (HIL) tests that verify behavior on physical hardware under realistic conditions (e.g., kill switch response time measured on oscilloscope). Test coverage must exceed 90% for all safety-critical code paths.

### Determinism Is Required

Same inputs produce same outputs in same number of cycles, every time, on every supported MCU. The VM has published cycle counts for every instruction. The wire protocol has published timing bounds. Safety responses have published latency budgets. Any change that introduces nondeterminism is rejected.

### Zero-Heap on ESP32

All memory on the ESP32 is statically allocated. No malloc/free in production firmware. No garbage collection. No dynamic data structures. This is not negotiable — heap fragmentation is the leading cause of embedded system failures, and NEXUS runs unattended for weeks at a time.

---

## Phase 0: Foundation Sprint (Weeks 1-4)

*"Get the bones right"*

Phase 0 establishes the build infrastructure, proves the VM compiles and runs on target hardware, establishes the communication channel between ESP32 and Jetson, and produces the first end-to-end demonstration: an LLM compiles a reflex, the reflex deploys to the ESP32, and an LED blinks.

### Sprint 0.1: Development Environment (Week 1)

**Goal:** A monorepo that compiles for both ESP32-S3 and Jetson, with CI/CD on every push.

**Tasks:**

1. Create the NEXUS monorepo structure under a version control system with the following top-level directories:
   - `firmware/` — ESP-IDF project for ESP32-S3 (C/C++, FreeRTOS)
   - `firmware/nexus_vm/` — Bytecode VM interpreter
   - `firmware/wire_protocol/` — COBS encoder/decoder, CRC-16, message dispatch
   - `firmware/drivers/` — I2C/SPI/1-Wire sensor drivers
   - `firmware/safety/` — Safety monitors (watchdog, kill switch, overcurrent)
   - `jetson/` — Python/C++ Jetson SDK
   - `jetson/wire_protocol/` — Python wire protocol client
   - `jetson/reflex_compiler/` — JSON-to-bytecode compiler
   - `jetson/trust_engine/` — INCREMENTS trust algorithm
   - `jetson/learning/` — Pattern discovery and A/B testing
   - `proto/` — Shared `.proto` definitions and JSON schemas
   - `proto/message_payloads.json` — Message payload schemas from spec
   - `specs/` — Symlink or copy of production specifications
   - `tests/` — Test framework (Unity for ESP32, pytest for Jetson)
   - `tests/firmware/` — ESP32 unit tests
   - `tests/jetson/` — Jetson unit tests
   - `tests/hil/` — Hardware-in-loop test skeletons
   - `.github/workflows/` — CI/CD pipeline definitions

2. Set up ESP-IDF v5.3+ build environment. Target: `esp32s3` with PSRAM enabled. Flash configuration: 8MB flash, 8MB PSRAM, FAT partition for NVS.

3. Set up Jetson Orin Nano development environment. Ubuntu 22.04 LTS. Python 3.11+. Dependencies: `pyserial>=3.5`, `llama-cpp-python`, `grpcio>=1.66`, `paho-mqtt>=2.1`, `numpy`, `scipy`, `matplotlib`.

4. Create CI/CD pipeline (GitHub Actions):
   - **ESP32 Build Job:** `idf.py build` on push to any branch. Verify zero warnings, zero errors. Binary size < 1MB.
   - **ESP32 Test Job:** Run Unity-based unit tests on host (not hardware). Flash to ESP32-S3 if USB-connected runner available.
   - **Jetson Build Job:** Python syntax check (`ruff check .`), type check (`mypy`), dependency installation, import validation.
   - **Jetson Test Job:** Run pytest suite. Minimum coverage: 80%.
   - **Lint Job:** `clang-format` for C code, `ruff format` for Python. Fail on any formatting violation.

5. Create HIL test harness skeleton:
   - `tests/hil/test_vm_accuracy.py` — Framework for measuring VM tick timing on oscilloscope-connected hardware.
   - `tests/hil/test_wire_roundtrip.py` — Framework for measuring wire protocol latency between ESP32 and Jetson.
   - `tests/hil/test_safety_response.py` — Framework for measuring kill switch response time.

**Files to Create:**
- `CMakeLists.txt` (top-level monorepo config)
- `firmware/CMakeLists.txt` (ESP-IDF project file)
- `firmware/main/nexus_main.c` (entry point, FreeRTOS task skeleton)
- `jetson/requirements.txt` (Python dependencies)
- `jetson/nexus_sdk/__init__.py` (Jetson SDK package)
- `.github/workflows/esp32-build.yml`
- `.github/workflows/esp32-test.yml`
- `.github/workflows/jetson-build.yml`
- `.github/workflows/jetson-test.yml`

**Specs to Implement:** `specs/firmware/memory_map_and_partitions.md` (flash partition table), `specs/firmware/io_driver_interface.h` (driver vtable contract).

**Deliverables:**
- [ ] Repository compiles for ESP32-S3 with `idf.py build` — zero errors, zero warnings
- [ ] Repository passes `ruff check` and `mypy` for all Python code
- [ ] CI/CD pipeline runs green on a test push
- [ ] Hardware-in-loop test skeleton is importable and runnable (even if tests are stubs)

**Duration:** 5 working days.

### Sprint 0.2: ESP32 VM Core (Week 2)

**Goal:** A complete 32-opcode stack machine interpreter that runs on the ESP32-S3 and passes comprehensive unit tests.

**Tasks:**

1. Implement the 8-byte fixed instruction format decoder. Every instruction is 8 bytes: 1 byte opcode, 1 byte flags, 2 bytes operand1 (uint16), 4 bytes operand2 (uint32). All fields are little-endian on ESP32-S3 (Xtensa LX7).

2. Implement all 32 opcodes per the definitive opcode map in `reflex_bytecode_vm_spec.md` §2.4:
   - **Stack (0x00-0x07):** NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT
   - **Arithmetic (0x08-0x10):** ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F
   - **Comparison (0x11-0x15):** EQ_F, LT_F, GT_F, LTE_F, GTE_F
   - **Logic (0x16-0x19):** AND_B, OR_B, XOR_B, NOT_B
   - **I/O (0x1A-0x1C):** READ_PIN, WRITE_PIN, READ_TIMER_MS
   - **Control (0x1D-0x1F):** JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE

3. Implement syscall mechanism via NOP with flags bit 7 (SYSCALL):
   - 0x01: HALT
   - 0x02: PID_COMPUTE (operand2.lo16 = pid_idx, 8 PID instances × 32 bytes each)
   - 0x03: RECORD_SNAPSHOT (16 snapshots × 128 bytes = 2KB buffer)
   - 0x04: EMIT_EVENT (32 events × 8 bytes = 256 byte ring buffer)

4. Implement the memory model per `reflex_bytecode_vm_spec.md` §4:
   - 256-entry data stack (uint32_t), stack overflow/underflow checks on every operation
   - 64 sensor registers (read-only from VM perspective, populated by host firmware before each tick)
   - 64 actuator registers (write-only from VM perspective, drained by host firmware after each tick)
   - Variable space via READ_PIN/WRITE_PIN with operand1 >= 64 (operand1 - 64 = variable index, range 0-255)
   - All memory statically allocated. Zero heap usage.
   - Call stack for CALL/RET (implemented via JUMP with flags bit 3 = IS_CALL)

5. Implement the execution model per §5:
   - Fetch-decode-execute loop
   - Cycle counting per instruction (published cycle counts per opcode)
   - 10,000-cycle budget per tick (configurable), HALT on violation
   - NaN/Infinity detection: no NaN or Infinity value may reach an actuator output register
   - All actuator outputs clamped to configured safe ranges after every tick

6. Implement safety invariants per §6:
   - Bounded execution: PC always within bytecode buffer bounds, validated at compile time
   - Type safety: no runtime type checking (compiler's responsibility), but NaN guard on actuator writes
   - Stack safety: overflow → HALT, underflow → HALT
   - Jump safety: all targets validated at compile time (multiple of 8, within bounds)

**Files to Create:**
- `firmware/nexus_vm/nexus_vm.h` (VM state structure, constants, error codes)
- `firmware/nexus_vm/nexus_vm.c` (interpreter implementation)
- `firmware/nexus_vm/vm_validator.h` (bytecode validation functions)
- `firmware/nexus_vm/vm_validator.c` (pre-execution validation)
- `firmware/nexus_vm/pid_controller.h` (PID state structure)
- `firmware/nexus_vm/pid_controller.c` (PID compute syscall)
- `tests/firmware/test_vm_opcodes.c` (opcode test vectors — one test per opcode)
- `tests/firmware/test_vm_safety.c` (safety invariant tests)
- `tests/firmware/test_vm_timing.c` (cycle count verification)

**Spec Reference:** `specs/firmware/reflex_bytecode_vm_spec.md` §1-§6, §11 (Opcode Quick-Reference), §12 (Full Encoding Table), §13 (Implementor's Checklist).

**Test Vectors (minimum 50 tests):**
- Every opcode with valid operands
- Every opcode with boundary operands (max/min float, zero, NaN, Infinity)
- Stack overflow (256+ pushes without pops)
- Stack underflow (pop on empty stack)
- Division by zero (must return 0.0, not IEEE Inf)
- NaN injection (NaN pushed to stack, then written to actuator — must be caught)
- Cycle limit enforcement (program that loops forever — must halt at 10,000 cycles)
- Jump to invalid target (out of bounds, non-aligned)
- CLAMP_F edge cases (lo == hi, lo > hi)
- PID compute with anti-windup (sustained error for 60 seconds)

**Deliverables:**
- [ ] `firmware/nexus_vm/` compiles and links into the ESP32 firmware
- [ ] All 32 opcodes execute correctly against spec test vectors
- [ ] 50+ unit tests pass on host (Unity framework)
- [ ] Cycle count accuracy verified: measured cycles match published cycle counts within 10%
- [ ] VM executes a "blink LED at 1Hz" test program on real ESP32-S3 hardware

**Duration:** 5 working days.

### Sprint 0.3: Wire Protocol (Week 3)

**Goal:** Bidirectional communication between ESP32 and Jetson using the production wire protocol (RS-422, COBS, CRC-16, 28 message types).

**Tasks:**

1. Implement COBS (Consistent Overhead Byte Stuffing) encoder and decoder per `wire_protocol_spec.md` §2.2-§2.3. Worst-case overhead: 1 byte per 254 bytes (0.4%). Self-synchronizing decoder (any 0x00 resets frame detection).

2. Implement CRC-16/CCITT-FALSE per §2.4:
   - Polynomial: 0x1021
   - Initial value: 0xFFFF
   - Final XOR: 0x0000
   - No reflection of input or output
   - Check value for "123456789": 0x29B1
   - Byte order: big-endian (MSB first)

3. Implement frame reception state machine per §2.6:
   - States: IDLE, RECEIVING
   - Maximum decoded frame: 1036 bytes (10-byte header + 1024-byte payload + 2-byte CRC)
   - Maximum COBS-encoded frame: 1051 bytes
   - Maximum wire frame: 1053 bytes (1 + 1051 + 1 delimiters)
   - Rejection of oversized frames (error 0x5001 FRAME_TOO_LARGE)
   - CRC mismatch detection (error 0x5003 CRC_MISMATCH)

4. Implement message header parsing per §3:
   - 10-byte header: msg_type (1B), flags (1B), sequence_number (2B, big-endian), timestamp_ms (4B, big-endian), payload_length (2B, big-endian)
   - Flag bit definitions: ACK_REQUIRED, IS_ACK, IS_ERROR, URGENT, COMPRESSED, ENCRYPTED, NO_TIMESTAMP

5. Implement at minimum 8 message types from §4.3:
   - HEARTBEAT (0x05) — keep-alive, no payload
   - DEVICE_IDENTITY (0x01) — boot announcement, JSON payload
   - ROLE_ASSIGN (0x02) — node configuration, JSON payload, criticality 1
   - ROLE_ACK (0x03) — role acceptance, JSON payload
   - SENSOR_TELEMETRY (0x06) — sensor data, JSON payload
   - COMMAND (0x07) — actuator command, JSON payload
   - REFLEX_DEPLOY (0x09) — bytecode deployment, JSON payload
   - COMMAND_ACK (0x08) — acknowledgement, JSON payload

6. Implement reliability mechanisms per §6:
   - Acknowledgement with retry: 3 retries, exponential backoff (200ms → 400ms → 800ms), ±10% jitter
   - Sequence number tracking: in-order processing, duplicate detection, gap detection
   - Heartbeat monitoring: 1000ms interval (node), 5000ms (Jetson), escalation to DEGRADED then FAILSAFE

7. Wire up hardware: ESP32 TX/RX → THVD1500 RS-422 transceiver → Cat-5e cable → Jetson USB-RS422 adapter (or FT232H). CTS/RTS hardware flow control enabled.

**Files to Create:**
- `firmware/wire_protocol/cobs.h` / `firmware/wire_protocol/cobs.c`
- `firmware/wire_protocol/crc16.h` / `firmware/wire_protocol/crc16.c`
- `firmware/wire_protocol/frame.h` / `firmware/wire_protocol/frame.c`
- `firmware/wire_protocol/message.h` / `firmware/wire_protocol/message.c`
- `firmware/wire_protocol/dispatch.h` / `firmware/wire_protocol/dispatch.c`
- `firmware/wire_protocol/reliability.h` / `firmware/wire_protocol/reliability.c`
- `jetson/wire_protocol/cobs.py`
- `jetson/wire_protocol/crc16.py`
- `jetson/wire_protocol/frame.py`
- `jetson/wire_protocol/node_client.py` (high-level client for communicating with ESP32 nodes)
- `tests/firmware/test_cobs.c`
- `tests/firmware/test_crc16.c`
- `tests/firmware/test_frame.c`
- `tests/jetson/test_wire_roundtrip.py`

**Spec Reference:** `specs/protocol/wire_protocol_spec.md` §1-§6. `specs/protocol/message_payloads.json` for all JSON payload schemas.

**Deliverables:**
- [ ] COBS encode/decode passes round-trip test with 1000 random byte sequences
- [ ] CRC-16 produces check value 0x29B1 for "123456789"
- [ ] Frame decoder correctly rejects malformed frames (bad CRC, oversized, too short)
- [ ] HEARTBEAT round-trip: Jetson sends HEARTBEAT, ESP32 responds with PONG, RTT < 5ms
- [ ] REFLEX_DEPLOY round-trip: Jetson sends REFLEX_DEPLOY, ESP32 responds with COMMAND_ACK
- [ ] Zero undetected errors across 10,000 frames (CRC validation)

**Duration:** 5 working days.

### Sprint 0.4: Jetson SDK + Reflex Compiler (Week 4)

**Goal:** End-to-end pipeline from natural language to blinking LED.

**Tasks:**

1. Implement the Jetson wire protocol client (`jetson/wire_protocol/node_client.py`):
   - Serial port management (pyserial, configurable baud rate)
   - Frame-level send/receive
   - Message-level API: `send_heartbeat()`, `send_role_assign()`, `send_reflex_deploy()`, `wait_for_ack()`
   - Automatic device discovery (wait for DEVICE_IDENTITY on boot)
   - Baud rate negotiation (115200 → 921600 per §1.2)

2. Implement the JSON-to-bytecode reflex compiler (`jetson/reflex_compiler/compiler.py`):
   - Input: human-readable reflex definition (JSON format per spec)
   - Output: 8-byte fixed-length bytecode binary
   - Compilation passes:
     1. **Parse:** Validate JSON schema against `message_payloads.json` REFLEX_DEPLOY schema
     2. **Type check:** Verify all stack operations are type-correct (float on arithmetic, integer on logic)
     3. **Bounds check:** Verify all jump targets are within bytecode bounds and 8-byte aligned
     4. **Stack analysis:** Compute maximum stack depth, verify < 256
     5. **Cycle analysis:** Compute worst-case cycle count, verify < 10,000 per tick
     6. **Actuator clamping:** Insert CLAMP_F instructions for all actuator writes
     7. **Emit:** Generate binary bytecode with HALT sentinel as final instruction
   - Compilation time target: < 10ms per reflex

3. Implement the INCREMENTS trust engine prototype (`jetson/trust_engine/increments.py`):
   - Full 12-parameter implementation per `trust_score_algorithm_spec.md` §2-§5
   - 15 event types with severity and quality classification
   - 6 autonomy levels (L0-L5) with promotion/demotion rules
   - Reset event handling (8 reset types with multipliers)
   - Per-subsystem tracking (steering, engine, navigation, bilge, lighting)
   - Trust-gated deployment check: `should_allow_deploy(subsystem, trust_required) → bool`

4. Wire the end-to-end pipeline:
   ```
   Natural language ("blink LED at 1Hz")
   → LLM generates reflex JSON (OpenAI API for Phase 0, local model for Phase 1)
   → Safety validation (basic: check actuator ranges, cycle budget, stack depth)
   → Trust check (trust >= 0.30 required for deployment)
   → Bytecode compilation
   → REFLEX_DEPLOY via wire protocol
   → ESP32 executes bytecode
   → LED blinks at 1Hz
   ```

5. Implement the system prompt for the LLM:
   - Safety rules (SR-001 through SR-010 from safety_policy.json)
   - Sensor/actuator naming conventions
   - Two few-shot examples: "blink LED at 1Hz" and "temperature PID control"
   - Output format specification (JSON schema)

**Files to Create:**
- `jetson/wire_protocol/node_client.py`
- `jetson/reflex_compiler/compiler.py`
- `jetson/reflex_compiler/bytecode_emitter.py`
- `jetson/reflex_compiler/safety_validator.py`
- `jetson/reflex_compiler/test_vectors.py`
- `jetson/trust_engine/increments.py`
- `jetson/trust_engine/events.py`
- `jetson/trust_engine/levels.py`
- `jetson/nexus_sdk/pipeline.py` (end-to-end orchestration)
- `jetson/nexus_sdk/system_prompt.py`
- `tests/jetson/test_compiler.py`
- `tests/jetson/test_trust_engine.py`
- `tests/jetson/test_pipeline.py`

**Spec Reference:** `specs/jetson/learning_pipeline_spec.md` §2 (Reflex Representation — for JSON reflex format), `specs/safety/safety_policy.json` (SR-001 through SR-010), `specs/safety/trust_score_algorithm_spec.md` §2-§5.

**Deliverables:**
- [ ] Compiler compiles "blink LED at 1Hz" to valid bytecode
- [ ] Compiler rejects reflexes with stack depth > 256
- [ ] Compiler rejects reflexes with cycle count > 10,000
- [ ] Trust engine matches spec predictions within 5% for 100 evaluation windows
- [ ] End-to-end: type natural language, observe LED blink on ESP32
- [ ] Pipeline round-trip latency < 30 seconds (including LLM API call)
- [ ] Complete Sprint 0 test suite passes with > 80% coverage

**Duration:** 5 working days.

---

## Phase 1: Safety Hardening (Weeks 5-8)

*"Make it impossible to be unsafe"*

Phase 1 transforms the working prototype from Phase 0 into a safety-hardened system where every reflex deployment passes through a rigorous validation pipeline, every actuator action is protected by multiple safety barriers, and the trust engine accurately tracks subsystem reliability.

### Sprint 1.1: ESP32 Safety Layer (Week 5)

**Goal:** Four-tier safety system implemented and tested on hardware.

**Tasks:**

1. **Tier 1 — Hardware Interlock:**
   - Wire NC mushroom-head kill switch in series with +12V actuator power supply
   - Connect kill switch sense wire to dedicated ESP32 GPIO with 10KΩ external pull-up
   - Implement `estop_isr_handler()` at interrupt priority 1 (highest configurable on ESP32)
   - ISR actions: set `estop_triggered` flag, drive all actuator GPIOs to safe state, disable PWM outputs, notify supervisor via semaphore
   - ISR execution time: < 1ms (measured on oscilloscope)
   - Wire MAX6818 hardware watchdog IC: WDI to ESP32 GPIO, RST/WDO to ESP32 EN pin
   - Implement alternating 0x55/0xAA kick pattern at 200ms intervals
   - Install INA219 current sensors on actuator power rails with configurable overcurrent thresholds

2. **Tier 2 — Firmware Safety Guard:**
   - Implement ISR-level safety check that runs before every VM tick
   - Checks: stack bounds, cycle budget, NaN/Infinity in actuator registers, actuator clamp ranges
   - Forces actuators to safe state on any violation
   - Response time: < 10ms from detection to safe-state output

3. **Tier 3 — Supervisory Task:**
   - Implement `safety_supervisor` FreeRTOS task at priority `configMAX_PRIORITIES - 1`
   - Period: 10ms
   - Heartbeat monitoring: expect heartbeat from Jetson every 100ms
   - State machine: NORMAL → DEGRADED (5 missed heartbeats, 500ms) → SAFE_STATE (10 missed, 1000ms)
   - Task watchdog: all monitored tasks must check in within 1.0 seconds
   - Escalation: task hung → suspend task + safe-state its actuators; supervisor hung → stop feeding hardware WDT

4. **Tier 4 — Application Safety:**
   - Trust-score-gated autonomy: reflex only deploys if trust score >= threshold for subsystem
   - Kill-switch availability check before every actuator command
   - Per-reflex safety validation against safety_policy.json

**Spec Reference:** `specs/safety/safety_system_spec.md` §1-§6 (Four-Tier Architecture, Kill Switch, Watchdog, Heartbeat, Overcurrent, Solenoid Timeout).

**Deliverables:**
- [ ] Kill switch response time < 1ms (oscilloscope verified)
- [ ] Hardware WDT timeout triggers system reset within 1.1 seconds
- [ ] Overcurrent detection disables channel within 2ms of threshold crossing
- [ ] Heartbeat loss triggers NORMAL → DEGRADED within 500ms, SAFE_STATE within 1000ms
- [ ] All three tiers (1, 2, 3) independently trigger safe-state on failure

### Sprint 1.2: Trust Score Engine (Week 6)

**Goal:** Full INCREMENTS trust algorithm with per-subsystem tracking.

**Tasks:**

1. Implement all 12 parameters per `trust_score_algorithm_spec.md` §3:
   - alpha_gain (0.002), alpha_loss (0.05), alpha_decay (0.0001), t_floor (0.20), quality_cap (10), evaluation_window_hours (1.0), severity_exponent (1.0), streak_bonus (0.00005), min_events_for_gain (1), n_penalty_slope (0.1), reset_grace_hours (24.0), promotion_cooldown_hours (72.0)

2. Implement all 15 event types per §4.2 with correct severity and quality values

3. Implement all 6 autonomy levels per §5 with promotion/demotion rules:
   - L0 (Disabled) → L1 (Advisory, T >= 0.20, 8 hours, 1 day, 4 clean windows)
   - L1 → L2 (Supervised, T >= 0.40, 48 hours, 3 days, 24 clean windows)
   - L2 → L3 (Semi-Autonomous, T >= 0.60, 168 hours, 7 days, 100 clean windows)
   - L3 → L4 (High Autonomy, T >= 0.80, 336 hours, 14 days, 200 clean windows)
   - L4 → L5 (Full Autonomy, T >= 0.95, 720 hours, 30 days, 500 clean windows)

4. Implement all 8 reset types per §6 with correct multipliers and grace periods

5. Implement per-subsystem tracking: steering, engine, navigation, bilge, lighting — independent trust scores

6. Implement parameter validation rules: alpha_loss > alpha_gain × quality_cap, alpha_gain > alpha_decay × 10

**Spec Reference:** `specs/safety/trust_score_algorithm_spec.md` §2-§9.

**Deliverables:**
- [ ] Trust algorithm matches spec reference implementation within 1% for 5 simulation scenarios
- [ ] All 15 event types correctly classified (good/bad/neutral, severity, quality)
- [ ] Autonomy level transitions match spec rules exactly
- [ ] Per-subsystem independence verified: steering failure does not affect engine trust
- [ ] Parameter validation rejects invalid configurations

### Sprint 1.3: Safety Validation Framework (Week 7)

**Goal:** Every reflex passes through a multi-stage safety validator before deployment.

**Tasks:**

1. Implement reflex static analysis (`jetson/reflex_compiler/safety_validator.py`):
   - **Stack depth analysis:** Compute worst-case stack depth by simulating all execution paths
   - **Jump bounds analysis:** Verify all jump targets within bytecode bounds and 8-byte aligned
   - **Cycle budget analysis:** Compute worst-case execution time, verify < 10,000 cycles
   - **Actuator clamping verification:** Verify all WRITE_PIN to actuator registers preceded by CLAMP_F
   - **NaN/Infinity guard:** Verify no path allows NaN/Infinity to reach actuator register
   - **Variable namespace check:** Verify no variable index conflicts between concurrent reflexes
   - **PID ownership check:** Verify no two reflexes share the same PID instance index

2. Implement safety policy engine (`jetson/safety/policy_engine.py`):
   - Load and parse `safety_policy.json` (10 global rules, 7 actuator profiles, 5 domain rule sets)
   - Evaluate each reflex against all applicable rules
   - Rules checked: SR-001 (maximum actuator rate), SR-002 (actuator range), SR-003 (sensor validity), SR-004 (minimum trust), SR-005 (kill switch availability), SR-006 (heartbeat required), SR-007 (ISR priority), SR-008 (safe boot), SR-009 (current limits), SR-010 (solennoid timeout)
   - Report violations with bytecode location and rule reference

3. Implement pre-deployment safety checklist:
   - [ ] Bytecode passes static analysis (stack, jump, cycle, NaN)
   - [ ] Reflex passes safety policy engine (all applicable rules)
   - [ ] Trust score >= required threshold for target subsystem
   - [ ] Kill switch is available (sense GPIO reads LOW = not pressed)
   - [ ] Heartbeat is active (Jetson is online)
   - [ ] No conflicting reflex already deployed on same PID instances

**Spec Reference:** `specs/safety/safety_system_spec.md` §7 (Boot Safety Sequence), §8 (Failsafe State Definitions), §10 (Certification Checklist). `specs/safety/safety_policy.json`.

**Deliverables:**
- [ ] Static analysis catches 100% of stack overflows and jump violations in test suite
- [ ] Safety policy engine evaluates all 10 global rules correctly
- [ ] Pre-deployment checklist blocks deployment when any check fails
- [ ] > 90% of safety policy rules have test coverage

### Sprint 1.4: Integration Test Suite (Week 8)

**Goal:** Hardware-in-loop test framework with > 90% safety policy coverage.

**Tasks:**

1. Build HIL test framework:
   - Automated test runner that connects to ESP32 via serial
   - Test fixture: breadboard with ESP32-S3, kill switch, LED (actuator), DS18B20 (sensor), INA219 (current sensor)
   - Automated kill switch actuation (servo-driven or relay-driven)
   - Current injection (programmable load)

2. Implement safety simulation tests:
   - Fault injection: disconnect sensor during operation → verify SAFE_STATE within 20ms
   - Overcurrent injection: ramp current above threshold → verify channel disabled within 2ms
   - Heartbeat loss: disconnect Jetson serial → verify DEGRADED in 500ms, SAFE_STATE in 1000ms
   - Kill switch: activate kill switch → verify all actuators off in < 1ms (oscilloscope)
   - VM fault: deploy bytecode with deliberate stack overflow → verify VM halts gracefully
   - Trust violation: deploy reflex when trust < threshold → verify deployment rejected

3. Trust score Monte Carlo verification:
   - Run 1000 simulated evaluation windows with random event sequences
   - Compare trust trajectory against reference implementation
   - Verify trust dynamics match spec: gain τ_g ≈ 658 windows, loss τ_l ≈ 29 windows

4. 24-hour continuous operation test:
   - Deploy 3 concurrent reflexes on 3 ESP32 nodes
   - Log all telemetry, trust scores, safety events
   - Target: zero VM halts, zero safety events, zero undetected wire protocol errors

**Deliverables:**
- [ ] HIL test suite passes > 90% of safety policy rules
- [ ] All 6 fault injection tests pass with measured response times within spec budgets
- [ ] Trust score Monte Carlo matches spec within 2% across 1000 windows
- [ ] 24-hour continuous operation: zero safety incidents

**Milestone 1: "Safe Reflex Deployment"** — Can compile a reflex from natural language, deploy it to ESP32, verify it runs safely under fault injection, and trust score tracks correctly.

---

## Phase 2: Intelligence Layer (Weeks 9-16)

*"Make it learn"*

Phase 2 gives the system the ability to observe its environment, discover patterns in sensor data, generate improved reflexes via LLM inference, validate them through A/B testing, and deploy winners through the trust system.

### Sprint 2.1: LLM Inference Pipeline (Weeks 9-10)

**Goal:** Local LLM inference on Jetson Orin Nano with deterministic JSON reflex output.

**Tasks:**

1. Install and configure Qwen2.5-Coder-7B Q4_K_M via llama.cpp on Jetson Orin Nano:
   - Download quantized model (4.2GB VRAM)
   - Configure for 8GB LPDDR5 (4.2GB model + 2GB KV cache + 1.8GB system)
   - Target: 17+ tokens/second inference throughput
   - Install GBNF grammar for constrained JSON decoding

2. Implement system prompt compiler:
   - Safety rules (SR-001 through SR-010) embedded in system prompt
   - Sensor/actuator naming conventions from ROLE_ASSIGN configuration
   - Domain-specific context (marine: COLREGs references, sensor types, actuator limits)
   - Two few-shot examples with full reflex JSON output
   - Output format: strict JSON schema with GBNF grammar enforcement

3. Implement reflex generation from natural language intent:
   - Input: "reduce throttle when engine temperature exceeds 95C"
   - LLM generates candidate reflex JSON (trigger conditions, computation, actuator output)
   - JSON validated against schema (96% target compliance)
   - Semantic correctness validated via separate model (cross-validation)

4. Benchmark and optimize:
   - Measure: latency (time to first token), throughput (tokens/second), schema compliance rate, semantic correctness rate
   - Targets: < 2s latency, > 17 tok/s throughput, > 95% schema compliance, > 82% semantic correctness

**Spec Reference:** `specs/jetson/learning_pipeline_spec.md` §3-§4 (Narration Processing, Reflex Synthesis).

**Deliverables:**
- [ ] Qwen2.5-Coder-7B runs on Jetson at 17+ tok/s
- [ ] System prompt produces valid reflex JSON for 50 marine-domain test inputs
- [ ] Schema compliance > 95% on 500 test inputs
- [ ] Semantic correctness > 82% on human-graded test set

### Sprint 2.2: Pattern Discovery (Weeks 11-12)

**Goal:** System observes sensor data and discovers actionable patterns automatically.

**Tasks:**

1. Implement observation recording pipeline per `learning_pipeline_spec.md` §1:
   - UnifiedObservation record schema (72 fields per observation)
   - Parquet storage format with Snappy compression (hot tier) and ZSTD (warm/cold)
   - Sensor registration format (type, unit, range, accuracy, sample rate)
   - Retention policy: 7 days hot (NVMe), 90 days warm, 2 years cold (cloud)
   - Storage budget: ~46GB/day at 100Hz, fits in 1TB NVMe for ~20 days hot+warm

2. Implement at least 2 pattern discovery algorithms per §2:
   - **Cross-correlation scanner** (§2.1): pairwise Pearson correlation between all sensor/actuator pairs, Bonferroni-corrected p-values, time-lagged relationships (±60s at 100ms resolution)
   - **BOCPD** (§2.2): Bayesian Online Change Point Detection for regime shifts in sensor time series, configurable hazard function, minimum run length threshold

3. Implement pattern-to-reflex compilation:
   - Discovered pattern → natural language description → LLM generates candidate reflex
   - Candidate reflex enters A/B testing pipeline (Sprint 2.3)

**Spec Reference:** `specs/jetson/learning_pipeline_spec.md` §1 (Observation Data Model), §2 (Pattern Discovery Engine).

**Deliverables:**
- [ ] Observation pipeline records 100Hz data to Parquet for 24 hours without data loss
- [ ] Cross-correlation discovers at least 3 sensor relationships per hour of data
- [ ] BOCPD detects simulated regime changes with > 80% confidence
- [ ] Discovered patterns generate candidate reflexes via LLM

### Sprint 2.3: A/B Testing Framework (Weeks 13-14)

**Goal:** Every proposed reflex change is validated through controlled statistical testing.

**Tasks:**

1. Implement dual-reflex execution: candidate and baseline run in parallel (candidate computes but does not control actuators; baseline controls)

2. Implement statistical comparison:
   - Welch's t-test (no assumption of equal variance)
   - Minimum sample size calculation based on desired effect size and confidence level
   - Default: 4,950 ticks (at 100Hz ≈ 50 minutes), 95% confidence for 5% effect size

3. Implement automatic outcome evaluation:
   - Success metrics per domain (marine: heading error, fuel efficiency, safety margin)
   - Automatic rollback if candidate produces any safety event during testing
   - Logging of all test results for post-hoc analysis

4. Implement automatic winner selection with trust gating:
   - If candidate outperforms baseline AND passes safety validation AND trust score permits → deploy candidate
   - Otherwise → retain baseline, log reason for rejection

**Spec Reference:** `specs/jetson/learning_pipeline_spec.md` §4 (A/B Testing Framework).

**Deliverables:**
- [ ] A/B test framework runs for 50+ minutes without intervention
- [ ] Statistical test correctly identifies 5% improvement with 95% confidence
- [ ] Safety event during A/B test triggers immediate rollback
- [ ] Winner selection deploys only when all three conditions met

### Sprint 2.4: Cross-Validation Pipeline (Week 15)

**Goal:** Separate AI model validates all generated reflexes for safety.

**Tasks:**

1. Implement 6-step validation pipeline per `learning_pipeline_spec.md` §8:
   - Step 1: **Syntax validation** — JSON schema compliance check
   - Step 2: **Safety policy validation** — check against safety_policy.json rules
   - Step 3: **Stack analysis** — static analysis of stack depth, jump bounds, cycle budget
   - Step 4: **Trust check** — verify trust score >= required threshold
   - Step 5: **Semantic validation** — separate AI model (Claude API or second local model) evaluates whether the reflex does what it claims
   - Step 6: **Adversarial validation** — attempt to find inputs that cause unsafe behavior

2. Implement safety issue reporting:
   - Bytecode location (instruction index) for each violation
   - Severity classification (informational, warning, error, critical)
   - Recommendation (accept, reject, modify)

**Deliverables:**
- [ ] Cross-validation catches > 90% of safety issues (measured on 200 adversarial test cases)
- [ ] False positive rate < 10% (does not reject safe reflexes)
- [ ] Validation completes within 5 seconds per reflex

### Sprint 2.5: Marine Domain Integration (Week 16)

**Goal:** System operates with marine sensors and COLREGs-aware safety policies.

**Tasks:**

1. Implement marine sensor drivers:
   - GPS/GNSS (u-blox NEO-M9N via UART)
   - Compass/IMU (BNO085 9-DOF via I2C)
   - Depth sounder interface (NMEA 2000)
   - Wind sensor interface

2. Encode COLREGs safety policy (rules 5-19) in safety_policy.json:
   - Rule 5: Look-out (require sensor data from radar, AIS, visual)
   - Rule 6: Safe speed (cap throttle based on visibility, traffic density)
   - Rule 7: Risk of collision (require CPA > minimum threshold)
   - Rule 8-19: Steering and sailing rules (give-way, stand-on, overtaking)

3. Implement navigation reflex library:
   - Waypoint following (GPS waypoint tracking with rudder/throttle control)
   - Station keeping (hold position against current/wind)
   - Collision avoidance (AIS-based CPA calculation, evasive maneuver)

**Deliverables:**
- [ ] GPS provides position fix with < 2.5m CEP accuracy
- [ ] IMU provides orientation with < 0.1 degree accuracy
- [ ] COLREGs policy blocks unsafe maneuvers in 100% of test scenarios
- [ ] Waypoint following maintains < 10m cross-track error

**Milestone 2: "Learning Vessel"** — Can observe sensor data, discover patterns, generate and validate reflexes via LLM, A/B test them, and deploy winners to ESP32 with trust tracking.

---

## Phase 3: A2A-Native Foundation (Weeks 17-24)

*"Agents write the code"*

### Sprint 3.1: Agent-Annotated Bytecode (AAB) (Weeks 17-18)

**Goal:** Extended bytecode format that carries agent-readable metadata alongside core instructions.

**Tasks:**

1. Design and implement AAB encoder/decoder:
   - Core format: 8-byte instruction (unchanged, ESP32-compatible)
   - TLV metadata trailer: Type (1 byte), Length (2 bytes), Value (variable)
   - TLV tags: INTENT (0x01), CAPABILITY (0x02), SAFETY (0x03), TRUST (0x04), NARRATIVE (0x05)
   - Each AAB instruction = [8-byte core] [variable-length TLV block]

2. Implement AAB stripper: deterministic removal of all TLV metadata, producing 8-byte-only bytecode for ESP32 deployment. Zero overhead on ESP32.

3. Validate backward compatibility: AAB bytecode produces identical behavior when stripped and deployed to ESP32 vs. non-AAB bytecode.

**Spec Reference:** `a2a-native-specs/bytecode_vm_a2a_native.md` §3.

### Sprint 3.2: A2A Opcodes (Weeks 19-20)

**Goal:** 29 new opcodes for agent communication, interpreted on Jetson, NOP on ESP32.

**Tasks:**

1. Implement 29 new opcodes in the opcode range 0x20-0x5F:
   - **Intent (0x20-0x26):** DECLARE_INTENT, ASSERT_GOAL, VERIFY_OUTCOME, EXPLAIN_FAILURE
   - **Agent Communication (0x30-0x34):** TELL, ASK, DELEGATE, REPORT_STATUS, REQUEST_OVERRIDE
   - **Capability Negotiation (0x40-0x44):** REQUIRE_CAPABILITY, DECLARE_SENSOR_NEED, DECLARE_ACTUATOR_USE
   - **Safety Augmentation (0x50-0x56):** TRUST_CHECK, AUTONOMY_LEVEL_ASSERT, SAFE_BOUNDARY, RATE_LIMIT

2. ESP32 implementation: all new opcodes are NOP (0x00 semantics). Zero firmware changes to execution engine. Backward compatibility guaranteed.

3. Jetson A2A interpreter: full implementation of all 29 opcodes as agent-interpretable operations. Intention block structure: DECLARE_INTENT → CAPABILITY_SCOPE → TRUST_CONTEXT → BODY → VERIFY_OUTCOME → EXPLAIN_FAILURE.

**Spec Reference:** `a2a-native-specs/bytecode_vm_a2a_native.md` §4-§5.

### Sprint 3.3: Agent Communication Protocol (Weeks 21-22)

**Goal:** Structured agent-to-agent communication via TELL/ASK/DELEGATE.

**Tasks:**

1. Implement TELL/ASK/DELEGATE message routing on Jetson
2. Implement agent identity and authentication (sign/verify bytecode origin)
3. Implement capability advertisement (agents declare what they can observe and control)
4. Implement three communication patterns:
   - Proposal-Validation-Deployment pipeline (state machine with timeouts and failure modes)
   - Peer Negotiation (resource allocation and conflict resolution)
   - Communal Veto (3+ nodes can block deployment)

**Spec Reference:** `a2a-native-language/agent_communication_and_runtime_model.md`.

### Sprint 3.4: 0.5x Trust Rule Implementation (Weeks 23-24)

**Goal:** Agent-generated code earns trust at half the rate of human-authored code.

**Tasks:**

1. Add `origin` field to reflex metadata: HUMAN_AUTHORED or AGENT_GENERATED
2. Modify trust formula: when origin == AGENT_GENERATED, apply 0.5x multiplier to alpha_gain
3. Validate: agent code takes ~54 days (not 27) to advance one trust level
4. Full trust trajectory simulation and verification against spec predictions

**Spec Reference:** `a2a-native-specs/trust_system_a2a_native.md`.

**Deliverables:**
- [ ] AAB bytecode strips to core and executes identically on ESP32
- [ ] All 29 A2A opcodes parse and interpret correctly on Jetson
- [ ] TELL/ASK/DELEGATE messages route correctly between agents
- [ ] 0.5x trust multiplier verified: agent code takes 2x longer to gain trust

**Milestone 3: "A2A-Native Runtime"** — Agents generate AAB, cross-validate it, strip it to core bytecode, deploy to ESP32. Trust tracks at 0.5x rate for agent code.

---

## Phase 4: Swarm & Fleet (Weeks 25-32)

*"Many vessels, one mind"*

### Sprint 4.1: Multi-ESP32 Coordination (Weeks 25-26)

- RS-422 bus with multiple ESP32 nodes (up to 8 per Jetson)
- Per-node reflex deployment and independent trust tracking
- Inter-node communication via Jetson as hub
- Priority arbitration for shared actuator resources

### Sprint 4.2: Inter-Vessel Protocol (Weeks 27-28)

- MQTT fleet messaging (Jetson → Cloud → other vessels) per `jetson/mqtt_topics.json`
- Vessel capability advertisement (what each vessel can observe and control)
- Trust propagation: node → subsystem → vessel → fleet

### Sprint 4.3: Fleet Coordination (Weeks 29-30)

- Consensus navigation (multi-vessel path planning with conflict resolution)
- Task delegation (TELL/ASK/DELEGATE across vessels)
- Emergency override propagation (safety event on one vessel → fleet-wide notification)

### Sprint 4.4: Cloud Services (Weeks 31-32)

- Fleet management dashboard (real-time vessel status, trust scores, reflex library)
- Heavy model training pipeline (full Qwen2.5-Coder-7B fine-tuning on cloud GPUs)
- Simulation environment (digital twin for testing new reflexes before deployment)
- Fleet trust analytics (aggregated trust scores, anomaly detection, compliance reporting)

**Milestone 4: "Fleet Intelligence"** — 3+ vessels coordinate tasks, share trust scores, and delegate via A2A protocol.

---

## Phase 5: Post-Human-Code Evolution (Months 9-12+)

*"Agents design, build, and improve the system"*

### Sprint 5.1: Self-Improvement Pipeline

- Agent generates new VM opcodes (with formal specification, test vectors, cycle counts)
- Agent modifies safety policies (with validation against existing safety invariants)
- Agent proposes architecture changes (with simulation and risk analysis)
- Human approval required for any change to safety_policy.json or trust parameters

### Sprint 5.2: Certification Evidence Generation

- Automatic test case generation from safety policies (cover every rule with boundary cases)
- Formal verification snippets (model checking for safety state machine)
- Compliance documentation auto-generation (IEC 61508 SIL 1, EU AI Act)
- Audit trail: provenance for every deployed bytecode (who generated it, why, what validated it)

### Sprint 5.3: Domain Portability Framework

- Domain abstraction layer (plug in different sensors, actuators, regulations)
- Trust parameter auto-calibration per domain (healthcare: 200:1 ratio, home: 1.3:1 ratio)
- Template safety policies per domain (marine, agriculture, factory, mining, HVAC, home, healthcare, AGV)

**Milestone 5: "Self-Evolving Platform"** — Agents can improve the system's own code, generate certification evidence, and port to new domains.

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|------------|--------|------------|-------|
| 1 | **ESP32 VM timing nondeterminism** (cache misses, interrupt latency) | Medium | Critical | Profile worst-case execution time on oscilloscope; add timing margin (target 50% headroom) | Firmware Lead |
| 2 | **LLM generates unsafe reflex** (passes validation but violates safety in edge case) | High | Critical | Cross-validation with separate model; adversarial testing; kill switch as ultimate safety net | AI/ML Lead |
| 3 | **Trust score calibration wrong** (too fast or too slow for domain) | Medium | High | Monte Carlo simulation before deployment; adjustable parameters per subsystem; 2-week calibration window | Safety Lead |
| 4 | **Wire protocol packet loss** (RS-422 interference, baud rate too high) | Medium | Medium | Hardware flow control (CTS/RTS); retry with exponential backoff; fallback to lower baud rate | Firmware Lead |
| 5 | **Jetson thermal throttling** (7B model causes overheating) | Medium | High | Thermal monitoring; dynamic frequency scaling; Q4_K_M quantization reduces compute by 75% | DevOps Lead |
| 6 | **A2A cross-validation unreliable** (agent validates own output, misses issues) | High | Critical | Two independent models required; 29.4% miss rate for self-validation documented; use Claude API for cross-validation | AI/ML Lead |
| 7 | **Regulatory non-compliance** (EU AI Act, IEC 61508) | High | Critical | Engage regulatory consultant in Phase 3; allocate €180K-€480K for compliance audit; generate evidence continuously | Regulatory Lead |
| 8 | **Hardware supply chain** (Jetson Orin Nano availability, lead times) | Medium | Medium | Order 2x required units; maintain breadboard prototype as fallback; ESP32-S3 widely available | Project Lead |
| 9 | **Agent-generated bytecode adversarial exploitation** (crafted bytecode passes validation but violates safety) | Low | Critical | Formal bytecode verification; cycle-budget enforcement; actuator clamping as hardware-level safety net; kill switch as ultimate fallback | Safety Lead |
| 10 | **Team capacity** (cannot hire required skill mix) | Medium | High | Cross-train existing team; use contractor for specialist work (marine integration); prioritize critical path | Project Lead |

---

## Resource Requirements

### Team Composition Per Phase

| Phase | Duration | Embedded/Firmware | AI/ML | Full-Stack/DevOps | Marine Systems | QA/Safety | Regulatory | Project Lead | Total |
|-------|----------|------------------|-------|--------------------|---------------|----------|------------|-------------|-------|
| 0 | 4 weeks | 1 | 1 | 1 | — | — | — | — | 3 |
| 1 | 4 weeks | 1 | 1 | 1 | — | — | — | — | 3 |
| 2 | 4 weeks | 1 | 1 | 1 | — | — | — | — | 3 |
| 3 | 8 weeks | 2 | 2 | 1 | 1 | 1 | — | — | 7 |
| 4 | 8 weeks | 2 | 3 | 1 | 1 | 1 | 1 | 1 | 10 |
| 5 | 8+ weeks | 2 | 3 | 1 | 1 | 1 | 1 | 1 | 10 |

### Hardware Costs Per Phase

| Phase | Hardware | Cost |
|-------|----------|------|
| 0 | 3× ESP32-S3 DevKit, 1× Jetson Orin Nano, sensors, breadboards, power supply | $527 |
| 1 | Kill switch, MAX6818, INA219, RS-422 transceivers, wiring | $500 |
| 2 | Marine sensors (GPS, IMU, compass, AIS, depth), IP67 enclosures | $15,000 |
| 3 | Vessel instrumentation (actuators, sensors, cabling, power) | $25,000 |
| 4 | Multi-vessel hardware (3× full node sets), sea trial equipment | $50,000 |
| 5 | Cloud GPU instances, additional sensor sets, domain portability kits | $20,000 |
| **Total Hardware** | | **~$91,527** |

### Cloud/Compute Costs Per Phase

| Phase | Compute | Cost |
|-------|---------|------|
| 0-2 | GitHub Actions CI/CD, minimal cloud | $2,000 |
| 3 | Claude API for cross-validation, moderate cloud compute | $10,000 |
| 4 | Heavy model training, fleet MQTT infrastructure, EU AI Act compliance audit | $180K-480K (compliance) + $20K (compute) |
| 5 | Cloud GPU training, simulation infrastructure | $50,000 |
| **Total Cloud/Regulatory** | | **~$262K-512K** |

### Total Budget Breakdown

| Category | Cost |
|----------|------|
| Hardware | $91,527 |
| Cloud/Regulatory | $262K-512K |
| Labor (loaded cost, ~$1,875/week avg) | $2,025,000 |
| Contingency (15%) | $367,329-466,079 |
| **TOTAL** | **~$2.6M** |

---

## Dependency Graph

```
Sprint 0.1 (Dev Environment)
    ├── Sprint 0.2 (ESP32 VM Core) ← depends on 0.1 (build system)
    │   └── Sprint 0.3 (Wire Protocol) ← depends on 0.2 (VM to test deploy)
    │       └── Sprint 0.4 (Jetson SDK + Compiler) ← depends on 0.3 (wire protocol)
    │           └── Phase 1 begins
    └── (all sprints in Phase 0 can overlap slightly in the second week)

Phase 1 (Safety Hardening)
    ├── Sprint 1.1 (ESP32 Safety Layer) ← depends on Phase 0
    │   ├── Sprint 1.2 (Trust Engine) ← independent of 1.1 (can parallelize)
    │   │   └── Sprint 1.3 (Safety Validation) ← depends on 1.2 (trust engine needed)
    │   │       └── Sprint 1.4 (Integration Tests) ← depends on 1.1 + 1.3
    │   └── Sprint 1.2 (Trust Engine) ← independent of 1.1

Phase 2 (Intelligence)
    ├── Sprint 2.1 (LLM Inference) ← depends on Phase 1
    ├── Sprint 2.2 (Pattern Discovery) ← depends on 2.1 (LLM for reflex generation)
    ├── Sprint 2.3 (A/B Testing) ← depends on 2.2 (patterns to test)
    ├── Sprint 2.4 (Cross-Validation) ← depends on 2.3 (reflexes to validate)
    └── Sprint 2.5 (Marine Domain) ← depends on 2.4 (COLREGs in safety policy)

Phase 3 (A2A-Native)
    ├── Sprint 3.1 (AAB) ← depends on Phase 2
    ├── Sprint 3.2 (A2A Opcodes) ← depends on 3.1
    ├── Sprint 3.3 (Agent Protocol) ← depends on 3.2
    └── Sprint 3.4 (0.5× Trust) ← depends on 3.3

Phase 4 (Swarm & Fleet)
    ├── Sprint 4.1 (Multi-ESP32) ← depends on Phase 3
    ├── Sprint 4.2 (Inter-Vessel) ← depends on 4.1
    ├── Sprint 4.3 (Fleet Coordination) ← depends on 4.2
    └── Sprint 4.4 (Cloud Services) ← depends on 4.3

Phase 5 (Post-Human-Code) ← depends on Phase 4
    ├── Sprint 5.1 (Self-Improvement)
    ├── Sprint 5.2 (Certification)
    └── Sprint 5.3 (Domain Portability)
```

**Critical Path:** Sprint 0.1 → 0.2 → 0.3 → 0.4 → 1.1 → 1.3 → 1.4 → 2.1 → 2.2 → 2.3 → 2.4 → 3.1 → 3.2 → 3.3 → 3.4 → 4.1 → 4.2 → 4.3 → 5.1

Longest dependency chain: 19 sprints (48 weeks). The critical path runs through the core VM, wire protocol, compiler, safety, intelligence, and A2A layers. Fleet coordination and cloud services are parallel workstreams that can proceed simultaneously with Phase 5 development.

---

## Success Criteria

### Milestone 1: Safe Reflex Deployment (End of Phase 1, Week 8)

| Criterion | Pass/Fail | Measurement |
|-----------|-----------|-------------|
| 24-hour continuous operation | PASS: zero VM halts, zero safety events | Automated log analysis |
| Trust score matches simulation | PASS: within 5% across 100 windows | Automated comparison |
| LLM generates valid reflex JSON | PASS: >90% schema compliance on 100 inputs | Automated test suite |
| Round-trip latency | PASS: < 30 seconds (NL input → deployed bytecode) | Automated timing |
| Kill switch response | PASS: < 1ms measured on oscilloscope | Oscilloscope capture |
| Multi-node communication | PASS: zero packet loss at 921,600 baud over 24 hours | Packet counter |
| Independent review | PASS: integration test report approved by external engineer | Human sign-off |

### Milestone 2: Learning Vessel (End of Phase 2, Week 16)

| Criterion | Pass/Fail | Measurement |
|-----------|-----------|-------------|
| 72-hour continuous operation | PASS: zero safety incidents | Automated log analysis |
| Trust matches INCREMENTS spec | PASS: within 1% across 1,000 windows | Automated comparison |
| 32 opcodes pass verification | PASS: determinism, type safety, bounded execution | Formal test suite |
| Wire protocol zero undetected errors | PASS: across 1,000,000 frames | Frame counter + CRC |
| LLM schema compliance | PASS: >95% on 500 marine-domain inputs | Automated test suite |
| Kill switch under all loads | PASS: < 1ms under all load conditions | Oscilloscope capture |
| Independent safety review | PASS: formal design review approved | External safety engineer |

### Milestone 3: A2A-Native Runtime (End of Phase 3, Week 24)

| Criterion | Pass/Fail | Measurement |
|-----------|-----------|-------------|
| AAB format validated | PASS: all 29 A2A opcodes parse and interpret | Automated test suite |
| Multi-agent deployment | PASS: < 0.1% safety incident rate | 30-day operational test |
| 0.5x trust multiplier | PASS: validated over 90 days of operation | Trust trajectory analysis |
| Communal veto works | PASS: blocks at least one unsafe deployment | Deliberate test scenario |
| Fleet coordination | PASS: 3+ vessels share bytecode patterns | Multi-vessel sea trial |
| Griot narrative layer | PASS: readable explanations for 90%+ of deployed reflexes | Human grading |

### Milestone 4: Fleet Intelligence (End of Phase 4, Week 32)

| Criterion | Pass/Fail | Measurement |
|-----------|-----------|-------------|
| Multi-vessel coordination | PASS: 3+ vessels coordinate tasks simultaneously | Sea trial |
| Trust score propagation | PASS: node → subsystem → vessel → fleet | Automated verification |
| A2A delegation | PASS: TELL/ASK/DELEGATE across vessels | Network capture analysis |
| Emergency propagation | PASS: safety event → fleet-wide notification within 5 seconds | Timing measurement |

### Milestone 5: Self-Evolving Platform (End of Phase 5, Month 12+)

| Criterion | Pass/Fail | Measurement |
|-----------|-----------|-------------|
| Agent self-improvement | PASS: agent generates and deploys at least one new VM opcode | Automated + human review |
| Certification evidence | PASS: auto-generated test cases cover > 95% of safety policy | Coverage analysis |
| Domain portability | PASS: system operates in at least 2 domains with minimal reconfiguration | Domain switch test |

---

## Appendix: Spec-to-Sprint Mapping Table

| Spec File | Sprint(s) | Sections Implemented |
|-----------|-----------|---------------------|
| `specs/firmware/reflex_bytecode_vm_spec.md` (2,487 lines) | 0.2, 1.1, 3.1-3.2 | §1-§6 (all core VM), §7 (compilation), §9 (timing), §11-§13 (appendices) |
| `specs/protocol/wire_protocol_spec.md` (1,047 lines) | 0.3, 0.4 | §1-§2 (physical + framing), §3-§4 (header + messages), §6 (reliability) |
| `specs/protocol/message_payloads.json` (2,156 lines) | 0.4, 2.1 | All JSON payload schemas used by compiler and LLM pipeline |
| `specs/safety/safety_system_spec.md` (1,296 lines) | 1.1, 1.3, 2.5 | §1-§6 (four tiers), §7 (boot sequence), §8 (failsafe), §10 (certification) |
| `specs/safety/safety_policy.json` (864 lines) | 1.3, 2.5, 3.4 | All 10 global rules + domain-specific rules |
| `specs/safety/trust_score_algorithm_spec.md` (2,414 lines) | 1.2, 3.4 | §2-§5 (formal definition, parameters, events, levels), §7 (simulation), §9 (data structures) |
| `specs/jetson/learning_pipeline_spec.md` (2,140 lines) | 2.1-2.4, 3.3 | §1 (observation), §2 (pattern discovery), §3-§4 (narration + synthesis), §5 (A/B testing) |
| `specs/jetson/cluster_api.proto` (934 lines) | 4.2-4.4 | All 6 gRPC services for fleet coordination |
| `specs/jetson/mqtt_topics.json` (668 lines) | 4.2-4.4 | All 13 MQTT topics for fleet communication |
| `specs/jetson/module_interface.py` (1,153 lines) | 2.1-2.4 | Python ABC for all Jetson modules |
| `specs/firmware/memory_map_and_partitions.md` (685 lines) | 0.1 | Flash partition table, SRAM/PSRAM maps |
| `specs/firmware/io_driver_interface.h` (829 lines) | 0.1, 2.5 | Driver vtable, pin config types, error codes |
| `specs/firmware/io_driver_registry.json` (2,408 lines) | 2.5 | 9+ I2C drivers with register sequences |
| `specs/ports/hardware_compatibility_matrix.json` (2,128 lines) | 5.3 | 13 MCU evaluations for domain portability |
| `a2a-native-specs/bytecode_vm_a2a_native.md` | 3.1-3.2 | §3 (AAB format), §4-§5 (A2A opcodes) |
| `a2a-native-specs/trust_system_a2a_native.md` | 3.4 | 0.5x trust multiplier |
| `a2a-native-specs/safety_system_a2a_native.md` | 3.3 | Agent safety validation extensions |
| `a2a-native-specs/learning_pipeline_a2a_native.md` | 3.3 | Agent learning pipeline extensions |
| `a2a-native-specs/wire_protocol_a2a_native.md` | 3.3 | 12 wire protocol extensions for A2A |
| `a2a-native-specs/marine_reference_a2a_native.md` | 3.3 | Marine domain A2A-native integration |
| `a2a-native-specs/rosetta_stone.md` | 3.1 | Mapping between human specs and agent-interpretable language |
| `a2a-native-language/language_design_and_semantics.md` | 3.1-3.4 | A2A language theory and formal proofs |
| `a2a-native-language/agent_communication_and_runtime_model.md` | 3.3 | Agent communication patterns |
| `a2a-native-language/nexus_integration_analysis.md` | 3.1 | Backward compatibility analysis |

---

*This roadmap is a living document. It will be updated at each phase boundary based on empirical findings from the previous phase. The structure (phases, milestones, success criteria) is stable. The details (sprint tasks, timelines, team composition) will be adjusted based on what we learn from hardware.*
