# NEXUS Build Specification for Claude Code

> **Version:** 1.0.0  
> **Date:** 2025-07-12  
> **Classification:** Build Manual — AI Coding Agent  
> **Status:** ACTIVE — Implementation Reference  

---

## How to Use This Document

You are Claude Code (Opus 4.6 or later). You have been given access to a repository containing the complete design for NEXUS — a distributed intelligence platform for industrial robotics where LLM agents (not humans) are the primary authors, interpreters, and validators of control code. This document tells you exactly what to build, how to build it, and how to verify it is correct.

**CRITICAL RULES:**

1. **Specs are the source of truth.** If your implementation disagrees with a specification, the specification wins. File an issue and fix the code.
2. **Safety is non-negotiable.** Every code change must preserve four-tier safety invariants. Safety is not a feature — it is the architecture.
3. **The VM is the interface.** All control logic flows through the bytecode VM. No direct hardware access from higher tiers.
4. **Zero heap on ESP32.** All memory is statically allocated. No `malloc`/`free` in production firmware. EVER.
5. **Determinism is required.** Same inputs produce the same outputs in the same number of cycles. Always.
6. **Float32 everywhere on ESP32.** No integer arithmetic for control values. The VM treats all stack slots as raw `uint32_t` but arithmetic opcodes reinterpret them as IEEE 754 `float32`.
7. **Trust score gates everything.** Code does not deploy without sufficient trust. Period.

**The one-sentence summary:** NEXUS is a distributed intelligence platform for robotics where a bytecode VM on ESP32-S3 microcontrollers executes AI-generated control logic at 1ms ticks, with AI cognition on Jetson Orin Nano edge GPUs, governed by a mathematical trust algorithm that requires 27 days of safe operation before any subsystem earns full autonomy.

---

## Repository Map — What to Read and When

### Phase 0: Foundation Read (Before writing any code)

Read these files in order. Extract the architectural understanding you need before implementation begins.

| File | Lines to Read | What to Extract |
|------|--------------|-----------------|
| `claude.md` | FULL (405 lines) | Complete project context: architecture, 32 opcodes, wire protocol summary, four-tier safety, INCREMENTS trust, learning pipeline, A2A paradigm, coding conventions. This is your operating manual. |
| `specs/00_MASTER_INDEX.md` | FULL | Master index of all production specifications. Know where everything lives. |
| `specs/firmware/memory_map_and_partitions.md` | FULL (682 lines) | ESP32-S3 SRAM/PSRAM/Flash layout, RTOS task table (6 tasks), DMA allocation, cache coherency protocol, sdkconfig overrides. You must understand every byte before writing firmware. |

### Phase 1: Bytecode VM (Weeks 1–2)

| File | Lines to Read | What to Implement |
|------|--------------|-------------------|
| `specs/firmware/reflex_bytecode_vm_spec.md` | Lines 1–600 (ISA, encoding, memory model, execution, safety invariants) | The entire VM interpreter: all 32 opcodes, 8-byte instruction format, stack machine semantics, cycle budgets, error handling. |
| `specs/firmware/reflex_bytecode_vm_spec.md` | Lines 600–1200 (Instruction encoding, operand fields, flags byte) | The exact binary encoding: opcode byte, flags byte, operand1 (uint16), operand2 (uint32). Every field, every bit. |
| `a2a-native-specs/bytecode_vm_a2a_native.md` | Lines 1–300 (Agent interpretation, AAB format, TLV tags) | Agent-Annotated Bytecode format: TLV metadata, 13 tag types, stripping protocol, agent-visible pre/postconditions. |
| `a2a-native-specs/bytecode_vm_a2a_native.md` | Lines 300–830 (29 new opcodes, program structure) | A2A opcodes (0x20–0x56): DECLARE_INTENT, TELL, ASK, DELEGATE, TRUST_CHECK, etc. NOP on ESP32. |

### Phase 2: Wire Protocol (Weeks 2–3)

| File | Lines to Read | What to Implement |
|------|--------------|-------------------|
| `specs/protocol/wire_protocol_spec.md` | Lines 1–230 (Physical layer, COBS framing, CRC, message header) | COBS encode/decode, CRC-16/CCITT-FALSE, 10-byte message header (big-endian), frame reception state machine. |
| `specs/protocol/wire_protocol_spec.md` | Lines 230–400 (Message types, error codes, reliability) | 28 message types, 4-level criticality, ACK/retry with exponential backoff, heartbeat escalation. |
| `specs/protocol/wire_protocol_spec.md` | Lines 627–700 (Binary payload formats) | Observation frame (32-byte compressed), OTA firmware chunk (520 bytes), telemetry snapshot format. |

### Phase 3: Safety System (Weeks 3–4)

| File | Lines to Read | What to Implement |
|------|--------------|-------------------|
| `specs/safety/safety_system_spec.md` | Lines 1–260 (Four-tier architecture, kill switch, watchdog) | Tier 1 hardware interlock, Tier 2 firmware safety guard (E-Stop ISR), Tier 3 supervisory task, Tier 4 application control. |
| `specs/safety/safety_system_spec.md` | Lines 260–500 (Watchdog, heartbeat, overcurrent) | MAX6818 hardware watchdog (0x55/0xAA pattern), heartbeat state machine (NORMAL/DEGRADED/SAFE_STATE), INA219 overcurrent protection. |
| `specs/safety/safety_policy.json` | Lines 1–200 (Global rules, actuator profiles) | 10 global safety rules (SR-001 through SR-010), actuator safety profiles (servo, relay, motor_pwm, solenoid, led, buzzer). |
| `specs/safety/trust_score_algorithm_spec.md` | Lines 1–500 (Overview, math, parameters, events, autonomy levels) | INCREMENTS algorithm: 12 parameters, 3 delta branches, 15 event types, 6 autonomy levels (L0–L5), 8 reset types. |

### Phase 4: Jetson Software (Weeks 4–6)

| File | Lines to Read | What to Implement |
|------|--------------|-------------------|
| `specs/jetson/learning_pipeline_spec.md` | Lines 1–120 (Observation data model, UnifiedObservation schema) | 72-field observation record, sensor registration format, Parquet storage, retention policy. |
| `specs/jetson/learning_pipeline_spec.md` | Lines 367–575 (Pattern discovery: cross-correlation, BOCPD, HDBSCAN) | 5 pattern discovery algorithms. Cross-correlation scanner, Bayesian Online Change Point Detection, behavioral clustering, temporal pattern mining. |
| `specs/safety/trust_score_algorithm_spec.md` | Lines 500–680 (Simulation, trajectories, scenario results) | Reference Python implementation of trust score simulation, trajectory analysis, days-to-level calculations. |

### Phase 5: A2A-Native Extensions (Weeks 6–8)

| File | Lines to Read | What to Implement |
|------|--------------|-------------------|
| `a2a-native-specs/bytecode_vm_a2a_native.md` | FULL (830+ lines) | AAB encoder/decoder, TLV metadata system, 29 new opcodes, validation rules, safety analysis matrix. |
| `a2a-native-specs/rosetta_stone.md` | FULL | Mapping between human specs and agent specs. The bridge between engineering and agent-interpretable language. |

---

## Build Environment Setup

### Monorepo Structure

```
Edge-Native/
├── firmware/               # ESP32-S3 code (ESP-IDF v5.3+)
│   ├── nexus_vm/           # Bytecode VM interpreter
│   │   ├── include/
│   │   │   └── vm.h        # VM data structures, opcode enum
│   │   ├── vm_core.c       # Fetch-decode-execute loop
│   │   ├── vm_opcodes.c    # Per-opcode implementations
│   │   ├── vm_validate.c   # Bytecode validator
│   │   └── vm_syscalls.c   # HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT
│   ├── wire_protocol/      # COBS/CRC/serial framing
│   │   ├── cobs.c          # COBS encode/decode
│   │   ├── crc16.c         # CRC-16/CCITT-FALSE
│   │   ├── wire_rx.c       # Frame reception state machine
│   │   ├── wire_tx.c       # Frame transmission + priority queues
│   │   └── msg_dispatch.c  # Message type dispatch
│   ├── safety/             # Watchdog, kill switch, safety state machine
│   │   ├── estop_isr.c     # E-Stop interrupt handler (IRAM)
│   │   ├── safety_sm.c     # Safety state machine
│   │   ├── watchdog.c      # HW/SW watchdog feeder
│   │   ├── heartbeat.c     # Heartbeat monitor
│   │   └── oc_monitor.c    # Overcurrent detection
│   ├── drivers/            # Sensor/actuator I/O
│   │   ├── io_poll.c       # Polled I/O acquisition task
│   │   ├── sensor_bus.c    # I2C/SPI sensor drivers
│   │   └── actuator_drv.c  # Actuator output driver
│   └── main/
│       └── app_main.c      # Entry point, task creation
├── jetson/                 # Jetson Orin Nano code (C++17/Python 3.11)
│   ├── wire_client/        # Wire protocol client
│   ├── reflex_compiler/    # JSON to bytecode compiler
│   │   ├── compiler.py     # Main compilation pipeline
│   │   ├── validator.py    # Bytecode validator
│   │   └── optimizer.py    # Dead code elimination, constant folding
│   ├── trust_engine/       # INCREMENTS implementation
│   │   ├── trust_engine.py # Core trust update logic
│   │   ├── events.py       # Event classification
│   │   └── autonomy.py     # Level transition rules
│   ├── safety_validator/   # Reflex static analysis
│   │   ├── ast_checker.py  # Abstract syntax tree safety checks
│   │   └── policy_loader.py # Load safety_policy.json
│   ├── learning/           # Pattern discovery + A/B testing
│   │   ├── observation.py  # UnifiedObservation + session management
│   │   ├── patterns.py     # 5 discovery algorithms
│   │   └── ab_test.py      # A/B testing framework
│   ├── agent_runtime/      # A2A-native agent execution
│   │   ├── aab_codec.py    # AAB encode/decode
│   │   ├── a2a_interp.py   # A2A opcode interpreter
│   │   └── agent_bus.py    # Inter-agent communication
│   └── main/
│       └── nexus_main.py   # Entry point
├── shared/
│   ├── proto/              # Protocol Buffers definitions
│   ├── bytecode/           # Bytecode definitions (C header + Python)
│   │   ├── opcodes.h       # C enum for all opcodes
│   │   ├── opcodes.py      # Python equivalent
│   │   └── instruction.h   # 8-byte instruction struct
│   └── test_vectors/       # Shared test data
├── tests/
│   ├── unit/               # Per-component unit tests
│   ├── integration/        # Cross-component tests
│   ├── hil/                # Hardware-in-loop tests
│   └── simulation/         # SIL simulation tests
├── tools/
│   ├── flash.sh            # ESP32 flash script
│   ├── test_runner.py      # Test orchestration
│   └── safety_check.py     # CI safety pipeline
├── specs/                  # Production specifications (SOURCE OF TRUTH)
├── claude-build/           # This build specification
└── third_party/            # Dependencies
```

### Toolchain Requirements

**ESP32 Firmware:**
- ESP-IDF v5.3+ (latest stable release)
- C11 standard (`-std=c11`)
- `xtensa-esp32s3-elf-gcc` cross-compiler
- Python 3.8+ for ESP-IDF build system
- CMake 3.16+ (ESP-IDF managed)

**Jetson Software:**
- C++17 (`-std=c++17`) for native code
- Python 3.11 for agent runtime, trust engine, learning
- CMake 3.24+ for native build
- PyTorch 2.2, CUDA 12.2 (for LLM inference)
- `llama.cpp` for Qwen2.5-Coder-7B Q4_K_M inference

**Shared/Testing:**
- Protocol Buffers: `protoc` 3.x
- ESP32 testing: Unity test framework
- Jetson testing: Google Test (gtest)
- Python testing: `pytest`
- CI: GitHub Actions

### Critical Build Flags

**ESP-IDF `sdkconfig.defaults`:**
```
CONFIG_FREERTOS_HZ=1000
CONFIG_ESP_DEFAULT_CPU_FREQ_240=y
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_SPIRAM_USE_MALLOC=y
CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=16384
CONFIG_HEAP_POISONING_COMPREHENSIVE=y
CONFIG_FREERTOS_CHECK_STACKOVERFLOW_CANARY=y
CONFIG_FREERTOS_MAX_PRIORITIES=25
CONFIG_SECURE_FLASH_ENC_ENABLED=y
CONFIG_SECURE_BOOT_V2_ENABLED=y
CONFIG_NVS_DEFAULT_PAGE_SIZE=4096
```

**Compiler flags (all targets):**
```
-Wall -Wextra -Werror -Wno-unused-parameter
```

**Linker:**
```
LTO: enabled for release builds (-flto)
```

---

## Component Build Specifications

### Component 1: Bytecode VM (firmware/nexus_vm/)

**SPEC REFERENCE:** `specs/firmware/reflex_bytecode_vm_spec.md` (2,487 lines)  
**A2A REFERENCE:** `a2a-native-specs/bytecode_vm_a2a_native.md`

#### 1.1 Data Structures

Define exactly:

```c
/* instruction.h — 8-byte fixed instruction */
#include <stdint.h>
#include <string.h>

typedef struct __attribute__((packed)) {
    uint8_t  opcode;    // Byte 0: 0x00–0x1F
    uint8_t  flags;     // Byte 1: bit field
    uint16_t operand1;  // Bytes 2-3: uint16 (little-endian on ESP32-S3)
    uint32_t operand2;  // Bytes 4-7: uint32 (little-endian on ESP32-S3)
} instruction_t;

#define FLAGS_HAS_IMMEDIATE   (1 << 0)
#define FLAGS_IS_FLOAT        (1 << 1)
#define FLAGS_EXTENDED_CLAMP  (1 << 2)
#define FLAGS_IS_CALL         (1 << 3)
#define FLAGS_SYSCALL         (1 << 7)

/* vm.h — VM state */
#define VM_STACK_SIZE     256
#define VM_CALL_STACK_SIZE 16
#define VM_VAR_COUNT       256
#define VM_SENSOR_COUNT    64
#define VM_ACTUATOR_COUNT  64
#define VM_PID_COUNT       8
#define VM_SNAPSHOT_COUNT  16
#define VM_EVENT_RING_SIZE 32
#define VM_MAX_CYCLE_BUDGET 100000

typedef struct {
    float Kp, Ki, Kd;
    float integral;
    float prev_error;
    float integral_limit;
    float output_min, output_max;
} pid_state_t;  // 32 bytes per controller

typedef struct {
    uint32_t tick_ms;
    uint32_t cycle_count;
    uint32_t current_state;
    uint32_t variables[15];
    uint32_t sensors[14];
} vm_snapshot_t;  // 128 bytes

typedef struct {
    uint32_t tick_ms;
    uint16_t event_id;
    uint16_t event_data;
} vm_event_t;  // 8 bytes

/* Error codes */
typedef enum {
    VM_OK = 0,
    ERR_STACK_UNDERFLOW,
    ERR_STACK_OVERFLOW,
    ERR_INVALID_OPCODE,
    ERR_INVALID_OPERAND,
    ERR_JUMP_OUT_OF_BOUNDS,
    ERR_CALL_STACK_OVERFLOW,
    ERR_CALL_STACK_UNDERFLOW,
    ERR_CYCLE_BUDGET_EXCEEDED,
    ERR_INVALID_SYSCALL,
    ERR_INVALID_PID,
    ERR_DIVISION_BY_ZERO,
} vm_error_t;

typedef struct {
    uint32_t stack[VM_STACK_SIZE];
    uint16_t sp;
    uint32_t pc;
    uint32_t vars[VM_VAR_COUNT];
    uint32_t sensors[VM_SENSOR_COUNT];
    uint32_t actuators[VM_ACTUATOR_COUNT];
    uint32_t flags;
    uint32_t cycle_count;
    uint32_t cycle_budget;
    uint32_t tick_count_ms;
    float    tick_period_sec;

    /* Call stack */
    struct {
        uint32_t return_addr;
        uint16_t frame_pointer;
    } call_stack[VM_CALL_STACK_SIZE];
    uint16_t csp;

    /* PID controllers */
    pid_state_t pid[VM_PID_COUNT];

    /* Snapshots */
    vm_snapshot_t snapshots[VM_SNAPSHOT_COUNT];
    uint8_t next_snapshot;

    /* Event ring buffer */
    vm_event_t events[VM_EVENT_RING_SIZE];
    uint16_t event_head;
    uint16_t event_tail;

    /* State */
    vm_error_t last_error;
    bool halted;
    const uint8_t *bytecode;
    uint32_t bytecode_size;
} vm_state_t;
```

**Memory layout (static allocation):**
- Stack: 256 x 4 = 1024 bytes
- Variables: 256 x 4 = 1024 bytes
- Sensors: 64 x 4 = 256 bytes
- Actuators: 64 x 4 = 256 bytes
- PID: 8 x 32 = 256 bytes
- Snapshots: 16 x 128 = 2048 bytes
- Events: 32 x 8 = 256 bytes
- Call stack: 16 x 6 = 96 bytes
- VM overhead (counters, flags, pointers): ~200 bytes
- **VM state total: ~5.4 KB** — well within 512KB SRAM budget

#### 1.2 Instruction Execution — All 32 Opcodes

For each opcode, here is the exact function signature, stack effects, error conditions, cycle cost, and behavior:

**Stack Operations (0x00–0x07):**

| Opcode | Mnemonic | Cycles | Stack Effect | Error Conditions | Implementation |
|--------|----------|--------|-------------|-----------------|----------------|
| 0x00 | NOP | 1 | 0→0 | None (SYSCALL if flags=0x80) | `PC += 8;` |
| 0x01 | PUSH_I8 | 1 | 0→1 | SP >= 256 | `STACK[SP++] = sign_extend_8(operand1 & 0xFF);` |
| 0x02 | PUSH_I16 | 1 | 0→1 | SP >= 256 | `STACK[SP++] = sign_extend_16(operand1);` |
| 0x03 | PUSH_F32 | 1 | 0→1 | SP >= 256 | `memcpy(&STACK[SP++], &operand2, 4);` |
| 0x04 | POP | 1 | 1→0 | SP == 0 | `SP--;` |
| 0x05 | DUP | 1 | 0→1 | SP >= 256 OR SP == 0 | `STACK[SP] = STACK[SP-1]; SP++;` |
| 0x06 | SWAP | 1 | 0→0 | SP < 2 | `tmp = STACK[SP-1]; STACK[SP-1] = STACK[SP-2]; STACK[SP-2] = tmp;` |
| 0x07 | ROT | 2 | 0→0 | SP < 3 | Rotate top three: [..., C, B, A] → [..., B, A, C] |

**Arithmetic (0x08–0x10):**

| Opcode | Mnemonic | Cycles | Stack Effect | Error Conditions | Implementation |
|--------|----------|--------|-------------|-----------------|----------------|
| 0x08 | ADD_F | 3 | 2→1 | SP < 2 | `b = pop_f32(); a = pop_f32(); push(a + b);` |
| 0x09 | SUB_F | 3 | 2→1 | SP < 2 | `b = pop_f32(); a = pop_f32(); push(a - b);` |
| 0x0A | MUL_F | 3 | 2→1 | SP < 2 | `b = pop_f32(); a = pop_f32(); push(a * b);` |
| 0x0B | DIV_F | 4 | 2→1 | SP < 2 | `b = pop_f32(); a = pop_f32(); push(b == 0.0f ? 0.0f : a/b);` |
| 0x0C | NEG_F | 1 | 1→1 | SP < 1 | `STACK[SP-1] ^= 0x80000000u;` |
| 0x0D | ABS_F | 1 | 1→1 | SP < 1 | `STACK[SP-1] &= 0x7FFFFFFFu;` |
| 0x0E | MIN_F | 3 | 2→1 | SP < 2 | NaN-safe min |
| 0x0F | MAX_F | 3 | 2→1 | SP < 2 | NaN-safe max |
| 0x10 | CLAMP_F | 3 | 1→1 | SP < 1, clamp encoding | Clamp TOS to [lo, hi] from operand2 halves |

**Comparison (0x11–0x15):** Pop two floats, push integer 0 or 1. Cycles: 3 each. Error: SP < 2.

| Opcode | Mnemonic | Comparison |
|--------|----------|-----------|
| 0x11 | EQ_F | `a == b ? 1 : 0` |
| 0x12 | LT_F | `a < b ? 1 : 0` |
| 0x13 | GT_F | `a > b ? 1 : 0` |
| 0x14 | LTE_F | `a <= b ? 1 : 0` |
| 0x15 | GTE_F | `a >= b ? 1 : 0` |

**Logic (0x16–0x19):** Bitwise operations on integer representation. Cycles: 1 each.

| Opcode | Mnemonic | Implementation |
|--------|----------|----------------|
| 0x16 | AND_B | `STACK[SP-2] &= STACK[SP-1]; SP--;` |
| 0x17 | OR_B | `STACK[SP-2] |= STACK[SP-1]; SP--;` |
| 0x18 | XOR_B | `STACK[SP-2] ^= STACK[SP-1]; SP--;` |
| 0x19 | NOT_B | `STACK[SP-1] = ~STACK[SP-1];` |

**I/O (0x1A–0x1C):**

| Opcode | Mnemonic | Cycles | Stack Effect | Error | Implementation |
|--------|----------|--------|-------------|-------|----------------|
| 0x1A | READ_PIN | 2 | 0→1 | operand1 >= 320, SP >= 256 | If operand1 < 64: push SENSOR_REG[operand1]. If >= 64: push VAR[operand1 - 64]. |
| 0x1B | WRITE_PIN | 2 | 1→0 | operand1 >= 320, SP == 0 | Pop TOS. If operand1 < 64: write ACTUATOR_REG[operand1]. If >= 64: write VAR[operand1 - 64]. |
| 0x1C | READ_TIMER_MS | 2 | 0→1 | SP >= 256 | `STACK[SP++] = tick_count_ms;` |

**Control Flow (0x1D–0x1F):**

| Opcode | Mnemonic | Cycles | Stack Effect | Error | Implementation |
|--------|----------|--------|-------------|-------|----------------|
| 0x1D | JUMP | 1 | 0→0 | target >= size, not 8-aligned | `PC = operand2;` If flags bit 3: CALL (push return addr). If target == 0xFFFFFFFF: RET. |
| 0x1E | JUMP_IF_FALSE | 2 | 1→0 | SP == 0, target invalid | Pop. If 0: PC = operand2. |
| 0x1F | JUMP_IF_TRUE | 2 | 1→0 | SP == 0, target invalid | Pop. If non-0: PC = operand2. |

**Syscalls (NOP flags=0x80):**

| Syscall ID | Name | Cycles | Stack Effect | Description |
|-----------|------|--------|-------------|-------------|
| 0x01 | HALT | 1 | 0→0 | Stop execution for this tick. Set vm->halted = true. |
| 0x02 | PID_COMPUTE | ~20 | 2→1 | Pop setpoint + input, push PID output. Anti-windup integral clamping. |
| 0x03 | RECORD_SNAPSHOT | ~10 | 0→0 | Save VM state to snapshot buffer slot. |
| 0x04 | EMIT_EVENT | 2 | 0→0 | Queue event (tick_ms, event_id, event_data) to ring buffer. |

#### 1.3 Memory Layout

All memory is statically allocated. The VM struct (`vm_state_t`) is ~5.4 KB, placed in DRAM heap at init. The bytecode buffer lives in PSRAM LittleFS (1 MB partition). Sensor/actuator register arrays are populated by the host firmware before each tick and drained after.

**Absolute rules:**
- NO `malloc`. NO `free`. NO `calloc`. NO `realloc`. EVER.
- All buffers are statically sized arrays within the `vm_state_t` struct.
- Bytecode is loaded into a static buffer: `uint8_t bytecode_buf[MAX_BYTECODE_SIZE];`
- `MAX_BYTECODE_SIZE` = 100 KB (typical reflex: 2–20 KB).

#### 1.4 Test Vectors

**Test 1: Simple Arithmetic**
```
Input:  PUSH_F32 3.0, PUSH_F32 4.0, ADD_F, HALT
Expected: stack[0] = 7.0, SP = 1, cycles = 4
```

**Test 2: Stack Underflow Detection**
```
Input:  ADD_F (stack is empty)
Expected: ERR_STACK_UNDERFLOW, halted = true
```

**Test 3: Division by Zero Returns 0.0**
```
Input:  PUSH_F32 1.0, PUSH_F32 0.0, DIV_F, HALT
Expected: stack[0] = 0.0 (NOT IEEE Inf/NaN)
```

**Test 4: I/O Round-Trip**
```
Input:  Set sensor[0] = 0.42, LOAD_SENSOR 0, CLAMP_F 0.0 1.0, STORE_ACTUATOR 0, HALT
Expected: actuator[0] = 0.42, sensor[0] unchanged
```

**Test 5: Conditional Branch**
```
Input:  PUSH_F32 5.0, PUSH_F32 10.0, LT_F, JUMP_IF_TRUE target_3, PUSH_F32 999.0, HALT, (target_3:) PUSH_F32 1.0, HALT
Expected: stack[0] = 1.0 (branch taken because 5 < 10)
```

**Test 6: Cycle Budget Enforcement**
```
Input:  Bytecode with cycle budget = 10, then infinite JUMP loop
Expected: ERR_CYCLE_BUDGET_EXCEEDED after 10 cycles, all actuators at safe state
```

**Test 7: Jump Out of Bounds**
```
Input:  JUMP 0xFFFFFFFF (valid RET if CSP >= 1, but CSP == 0)
Expected: ERR_CALL_STACK_UNDERFLOW
```

**Test 8: CLAMP_F Behavior**
```
Input:  PUSH_F32 -5.0, CLAMP_F -1.0 1.0, HALT
Expected: stack[0] = -1.0
```

**Test 9: NEG_F and ABS_F Bit Manipulation**
```
Input:  PUSH_F32 3.14, NEG_F, ABS_F, HALT
Expected: stack[0] = 3.14 (negate then absolute = original)
```

**Test 10: PID_COMPUTE Syscall**
```
Input:  Configure PID[0]: Kp=1.0, Ki=0.1, Kd=0.0, limits=[-100, 100]
        PUSH_F32 50.0 (setpoint), PUSH_F32 48.0 (input), PID_COMPUTE 0, HALT
Expected: output = Kp*(50-48) = 2.0 (first tick, integral accumulates)
```

---

### Component 2: Wire Protocol (firmware/wire_protocol/ + jetson/wire_client/)

**SPEC REFERENCE:** `specs/protocol/wire_protocol_spec.md` (1,047 lines)

#### 2.1 Framing: COBS + CRC-16

Every frame on the wire follows this structure:
```
[0x00] [COBS-encoded(header + payload + CRC)] [0x00]
```

The COBS-encoded region contains:
```
[10-byte Message Header] [Payload: 0–1024 bytes] [2-byte CRC-16]
```

Maximum decoded frame: 1036 bytes. Maximum COBS-encoded frame: 1051 bytes. Maximum wire frame: 1053 bytes.

**COBS Reference Implementation (C):**

```c
#include <stdint.h>
#include <stddef.h>

/* COBS encode: source -> destination. Returns encoded length.
 * dst must be at least src_len + (src_len / 254) + 2 bytes. */
size_t cobs_encode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;
    size_t code_idx = 0;
    uint8_t code = 0x01;

    if (dst_max < src_len + 1) return 0;

    dst[0] = 0x01;  // placeholder for first code byte
    dst_idx = 1;

    while (src_idx < src_len) {
        if (src[src_idx] == 0x00) {
            dst[code_idx] = code;
            code = 0x01;
            code_idx = dst_idx++;
            if (dst_idx >= dst_max) return 0;
        } else {
            dst[dst_idx++] = src[src_idx];
            if (dst_idx >= dst_max) return 0;
            code++;
            if (code == 0xFF) {
                dst[code_idx] = code;
                code = 0x01;
                code_idx = dst_idx++;
                if (dst_idx >= dst_max) return 0;
            }
        }
        src_idx++;
    }

    dst[code_idx] = code;
    return dst_idx;
}

/* COBS decode: source -> destination. Returns decoded length.
 * dst must be at least src_len bytes. */
size_t cobs_decode(const uint8_t *src, size_t src_len,
                   uint8_t *dst, size_t dst_max)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;

    while (src_idx < src_len) {
        uint8_t code = src[src_idx++];
        if (src_idx + code - 1 > src_len) return 0;

        for (uint8_t i = 1; i < code; i++) {
            if (dst_idx >= dst_max) return 0;
            dst[dst_idx++] = src[src_idx++];
        }

        if (code < 0xFF && src_idx < src_len) {
            if (dst_idx >= dst_max) return 0;
            dst[dst_idx++] = 0x00;
        }
    }

    return dst_idx;
}
```

**CRC-16/CCITT-FALSE Reference Implementation:**

```c
uint16_t crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc = crc << 1;
        }
    }
    return crc;
}
```

Check value for "123456789": must be **0x29B1**.

#### 2.2 Message Header (10 Bytes, Big-Endian)

```
Byte 0:  msg_type     (uint8)
Byte 1:  flags        (uint8)
Byte 2:  seq_hi       (uint16 >> 8)
Byte 3:  seq_lo       (uint16 & 0xFF)
Byte 4:  ts_byte3     (uint32 >> 24)
Byte 5:  ts_byte2     (uint32 >> 16)
Byte 6:  ts_byte1     (uint32 >> 8)
Byte 7:  ts_byte0     (uint32 & 0xFF)
Byte 8:  len_hi       (uint16 >> 8)
Byte 9:  len_lo       (uint16 & 0xFF)
```

Flags bits: ACK_REQUIRED(0), IS_ACK(1), IS_ERROR(2), URGENT(3), COMPRESSED(4), ENCRYPTED(5), NO_TIMESTAMP(6), RESERVED(7).

#### 2.3 Five Critical Message Types

| ID | Name | Direction | Criticality | Payload | Description |
|----|------|-----------|-------------|---------|-------------|
| 0x01 | DEVICE_IDENTITY | N2J | 0 (Telemetry) | JSON | Boot announcement: MAC, chip type, firmware version, capabilities. Sent immediately after POST. |
| 0x05 | HEARTBEAT | Both | 0 (Telemetry) | None (0 bytes) | Keep-alive. No payload. Node: 1000ms. Jetson: 5000ms. 3 misses → DEGRADED, 10 → SAFE_STATE. |
| 0x09 | REFLEX_DEPLOY | J2N | 1 (Command) | JSON | Deploys bytecode to node. Includes reflex name, trigger conditions, compiled .rbc data, priority, safety_class. |
| 0x0C | OBS_RECORD_START | J2N | 1 (Command) | JSON | Begins observation recording: channels, sample rate, compression mode, max duration. |
| 0x1C | SAFETY_EVENT | N2J | 2 (Safety) | JSON | Critical safety notification: kill-switch, overcurrent, watchdog timeout, thermal shutdown. |

**Boot Sequence**: Power-on → POST → DEVICE_IDENTITY → AUTO_DETECT_RESULT → SELFTEST_RESULT → wait for ROLE_ASSIGN → ROLE_ACK → BAUD_NEGOTIATION → OPERATIONAL.

#### 2.4 Serial Driver Configuration

- UART: 921,600 baud (after negotiation from 115,200), 8N1
- Transceiver: TI THVD1500 RS-422, 3.3V, 120Ω termination
- Connector: RJ-45 (8-pin: TX+, TX-, RX+, RX-, GND, CTS, RTS, SHIELD)
- DMA: TX DMA from DRAM (cache flush before start), RX interrupt-driven
- Flow control: Hardware CTS/RTS always enabled
- FreeRTOS task: `serial_protocol_task()` at priority 20, 4096-byte stack
- Interrupt handler: minimal — just buffers received bytes, wakes task via semaphore

#### 2.5 Test Vectors

**Test 1: COBS Round-Trip**
```
Input bytes: [0x01, 0x02, 0x00, 0x03, 0x04, 0x05, 0x00, 0x06]
COBS encoded: [0x02, 0x01, 0x02, 0x03, 0x03, 0x04, 0x05, 0x01, 0x06]
Decode → verify exact match with input.
```

**Test 2: CRC Check Value**
```
Input string: "123456789"
CRC-16/CCITT-FALSE = 0x29B1
```

**Test 3: All-Zeros COBS**
```
Input: [0x00, 0x00, 0x00]
Encoded: [0x01, 0x01, 0x01]
Decode → verify exact match.
```

**Test 4: All-0xFF COBS**
```
Input: [0xFF, 0xFF, 0xFF, 0xFF]
Encoded: [0x04, 0xFF, 0xFF, 0xFF, 0xFF]
Decode → verify exact match.
```

**Test 5: Frame Reception State Machine**
```
Send: [0x00] [valid COBS frame] [0x00]
Expect: dispatch() called once with correct header and payload.
Send: [0x00] [corrupted COBS] [0x00]
Expect: CRC_MISMATCH error, dispatch NOT called.
```

---

### Component 3: Safety System (firmware/safety/)

**SPEC REFERENCE:** `specs/safety/safety_system_spec.md` (1,296 lines)
**POLICY REFERENCE:** `specs/safety/safety_policy.json` (864 lines)

The safety system is the single most important component in the entire NEXUS platform. It is the reason this system can be trusted with physical actuators in the real world. The four-tier architecture ensures that no single software bug, hardware failure, or communication loss can cause an unsafe actuator state. Every design choice here exists because real-world robotics has killed people who got safety wrong.

#### 3.1 Four-Tier Safety Architecture

```
TIER 1: HARDWARE INTERLOCK
  Physical kill switch (NC mushroom-head), MAX6818 watchdog, polyfuses, pull-downs
  Response: <1ms (electrical) | Authority: ABSOLUTE

TIER 2: FIRMWARE SAFETY GUARD
  E-Stop ISR, safe-state outputs, sensor validation, rate limiting
  Response: <1.1ms (ISR) | Authority: overrides all software

TIER 3: SUPERVISORY TASK
  Watchdog feeder, heartbeat monitor, safety state machine
  Response: <100ms | Authority: can override control tasks

TIER 4: APPLICATION CONTROL
  PID loops, reflexes, AI inference, domain logic
  Response: <10ms | Authority: lowest
```

#### 3.2 Safety State Machine

States: **NORMAL → DEGRADED → SAFE_STATE → FAULT**

| Transition | Trigger | Actions |
|-----------|---------|---------|
| NORMAL → DEGRADED | 5 heartbeats missed (500ms), trust score drops below threshold, sensor failure | Disable non-safety reflexes. AI inference disabled. Alarm: single beep, amber LED. |
| DEGRADED → SAFE_STATE | 10 heartbeats missed (1000ms), critical failure detected | ALL actuators to safe state. ALL control loops suspended. Alarm: 3-beep repeating, red LED. |
| SAFE_STATE → FAULT | Unrecoverable error, boot counter > 5 in 10 minutes | System halted. Manual intervention required. |
| Any → NORMAL | Explicit reset after diagnosis, 3 consecutive good heartbeats, Jetson sends RESUME command | Staged re-enable: reflex (T+0), PID (T+100ms), AI (T+500ms), cloud (T+1000ms). |

**CRITICAL:** The system does NOT auto-resume. The Jetson must explicitly send a RESUME command after safe-state recovery.

#### 3.3 Watchdog Timer Specification

**Hardware (MAX6818):**
- Timeout: 1.0 seconds (not software-configurable)
- Kick pattern: alternating 0x55/0xAA (detects stuck-at-0 and stuck-at-1 faults)
- Kick interval: 200ms (5x per second, 4 kicks within 1s timeout)
- Reset pulse: 140ms minimum (active-low to ESP32 EN pin)

**Software (FreeRTOS task):**
- Task priority: 23 (one below safety_supervisor)
- Period: 100ms
- Task monitoring timeout: 1.0 second per task
- Escalation: 1st timeout = log; 2nd = suspend task + safe its actuators; 3rd = system reset
- If safety_supervisor itself misses check-in: stop feeding HWD → system reset within 1.0s

```c
void watchdog_feed_hw(void) {
    static uint8_t kick_pattern = 0x55;
    if (kick_pattern == 0x55) {
        gpio_set_level(WDT_KICK_PIN, 0);
        ets_delay_us(10);
        gpio_set_level(WDT_KICK_PIN, 1);
        kick_pattern = 0xAA;
    } else {
        gpio_set_level(WDT_KICK_PIN, 1);
        ets_delay_us(10);
        gpio_set_level(WDT_KICK_PIN, 0);
        kick_pattern = 0x55;
    }
}
```

#### 3.4 Kill Switch Specification

- Contact type: Normally Closed (NC), mushroom-head, twist-to-release
- GPIO: INPUT with external 10KΩ pull-up, interrupt on falling edge
- ISR priority: ESP_INTR_FLAG_LEVEL1 (highest)
- ISR must complete in <1ms
- ISR actions: (1) set estop_triggered flag, (2) drive all actuator GPIOs to safe values, (3) disable all PWM, (4) give semaphore from ISR
- ISR must contain NO blocking ops, NO floating-point, NO non-IRAM function calls

#### 3.5 Safety Policy Engine

The safety policy is defined in `specs/safety/safety_policy.json`. It contains:

**10 Global Safety Rules (SR-001 through SR-010):**
- SR-001: Explicit enable signal required for actuation
- SR-002: Timeout watchdog on all control loops
- SR-003: Defined safe-state value for every actuator
- SR-004: Single sensor failure shall not cause uncontrolled actuation
- SR-005: Rate limiting on all actuators
- SR-006: Watchdog timer disable prohibition
- SR-007: Emergency stop has highest priority
- SR-008: All outputs LOW/SAFE on boot
- SR-009: Division-by-zero protection for floating point
- SR-010: Bounded iteration count for reflex loops

**6 Actuator Safety Profiles:** servo, relay, motor_pwm, solenoid, led, buzzer — each with safe_state, limits, rate_limiting, monitoring, and hardware requirements.

**Safety Check Pipeline (CI/CD):** syntax_check → static_analysis → memory_budget → safety_rules → simulation → trust_gate → deployment_approval.

---

### Component 4: Trust Engine (jetson/trust_engine/)

**SPEC REFERENCE:** `specs/safety/trust_score_algorithm_spec.md` (2,414 lines)

#### 4.1 INCREMENTS Algorithm — Three-Branch Delta Computation

```
T(t) = clamp(T(t-1) + delta_T, 0.0, 1.0)
```

**Branch 1 — Net Positive** (n_bad == 0 AND n_good >= min_events_for_gain):
```
avg_quality    = sum(e.quality) / n_good
capped_n_good  = min(n_good, quality_cap)
delta_T        = alpha_gain * (1 - T_prev) * avg_quality * (capped_n_good / quality_cap)
+ streak_bonus * min(consecutive_clean, 24)   // if consecutive_clean > 0
```

**Branch 2 — Penalty** (n_bad > 0):
```
max_severity = max(e.severity for e in bad_events)
n_penalty    = 1.0 + n_penalty_slope * (n_bad - 1)
delta_T      = -alpha_loss * T_prev * (max_severity ^ severity_exponent) * n_penalty
```
Good events are IGNORED when bad events are present. Intentional.

**Branch 3 — Decay** (no events):
```
delta_T = -alpha_decay * (T_prev - t_floor)
```
Trust decays toward t_floor but not below it via this path.

#### 4.2 Complete Parameter Table (12 Parameters)

| # | Parameter | Symbol | Default | Type | Description |
|---|-----------|--------|---------|------|-------------|
| 1 | Gain rate | `alpha_gain` | 0.002 | float64 | Trust increase per window (Branch 1). 10x smaller than alpha_loss minimum. |
| 2 | Loss rate | `alpha_loss` | 0.05 | float64 | Trust decrease per window (Branch 2). 25x larger than alpha_gain. |
| 3 | Decay rate | `alpha_decay` | 0.0001 | float64 | Decay toward t_floor during inactivity (Branch 3). |
| 4 | Trust floor | `t_floor` | 0.2 | float64 | Minimum trust reachable via decay. Still can go below via penalties. |
| 5 | Quality cap | `quality_cap` | 10 | uint32 | Max good events per window that contribute to gain. |
| 6 | Window duration | `evaluation_window_hours` | 1.0 | float64 | Hours per evaluation window. |
| 7 | Severity exponent | `severity_exponent` | 1.0 | float64 | Applied as severity^exponent in penalty. >1 amplifies high-severity. |
| 8 | Streak bonus | `streak_bonus` | 0.00005 | float64 | Extra gain per consecutive clean window. |
| 9 | Min events for gain | `min_events_for_gain` | 1 | uint32 | Minimum good events for Branch 1. |
| 10 | Reset grace period | `reset_grace_hours` | 24.0 | float64 | No resets within this period after a reset. |
| 11 | Promotion cooldown | `promotion_cooldown_hours` | 72.0 | float64 | Min time between autonomy level promotions. |
| 12 | Penalty slope | `n_penalty_slope` | 0.1 | float64 | n_penalty = 1 + slope * (n_bad - 1). |

**Validation invariants (must hold at init):**
```
alpha_loss > alpha_gain * quality_cap     // 0.05 > 0.002 * 10 = 0.02 ✓
alpha_gain > alpha_decay * 10             // 0.002 > 0.0001 * 10 = 0.001 ✓
t_floor >= 0.0 AND t_floor < 1.0          // 0.2 ✓
quality_cap >= 1                           // 10 ✓
```

#### 4.3 Autonomy Level Mapping

| Level | Name | Trust Threshold | Min Observation | Min Clean Windows | Key Criteria |
|-------|------|----------------|----------------|-------------------|-------------|
| 0 | Disabled | — | — | — | Default after full reset |
| 1 | Advisory | T >= 0.20 | 8 hours | 4 | 80% clean windows |
| 2 | Supervised | T >= 0.40 | 48 hours | 24 | No severity >= 0.8 events |
| 3 | Semi-Autonomous | T >= 0.60 | 168 hours (7 days) | 100 | No severity >= 0.7 in 48h |
| 4 | High Autonomy | T >= 0.80 | 336 hours (14 days) | 200 | No severity >= 0.6 in 72h |
| 5 | Full Autonomy | T >= 0.95 | 720 hours (30 days) | 500 | No severity >= 0.5 in 168h |

**Demotion is immediate.** If T drops below current level threshold, demote now. Severity >= 0.8: demote at least 2 levels. Severity = 1.0: demote to L0.

#### 4.4 Per-Subsystem Independence

Five independent trust scores, each tracked separately:
1. **steering** — rudder, thrusters, heading control
2. **engine** — throttle, RPM, fuel management
3. **navigation** — GPS, waypoints, collision avoidance
4. **payload** — fishing gear, crane, specialized equipment
5. **communication** — VHF, AIS, cellular, satellite

One subsystem failure does NOT cascade. Steering trust dropping to L0 does not affect engine trust.

#### 4.5 Agent Code Multiplier

For bytecode generated by LLM agents (identified by `AGENT_SOURCE` AAB tag):
```
alpha_effective = alpha_gain * 0.5   // agent code earns trust at HALF rate
```

This compensates for reduced human intuition about what agent-generated code "actually does."

#### 4.6 Trust Dynamics

- **Gain time constant:** τ_g ≈ 658 windows (27.4 days) from T=0.2 to T=0.9 under ideal conditions
- **Loss time constant:** τ_l ≈ 29 windows (1.2 days) from T=0.9 to T=0.2 under worst-case
- **Asymmetry ratio:** 22x faster to lose trust than gain it
- This is intentional — prevents overtrust (humans systematically over-trust automation)

#### 4.7 Test Vectors

**Test 1: Ideal Trust Growth**
Starting at T=0.0, all good events (quality=0.95, 8 per window), how many days to reach L4 (T >= 0.80)?
Formula: `T(t) ≈ 1 - (1-T0) * exp(-lambda * t)` where `lambda = 0.002 * 0.95 * (8/10) = 0.00152`
Expected: approximately 658 windows = ~27 days.

**Test 2: Rapid Trust Loss**
Starting at T=0.90, single bad event with severity=1.0 each window:
`delta_T = -0.05 * 0.90 * 1.0 * 1.0 = -0.045`
After 18 windows (18 hours): T ≈ 0.90 - 18 * 0.045 = 0.09 → clamped to floor behavior.

**Test 3: Agent Code Half-Rate**
Same as Test 1 but with agent code multiplier (0.5x gain rate):
Expected: approximately 1316 windows = ~55 days (double the human-code trajectory).

**Test 4: Per-Subsystem Independence**
Set steering trust = 0.90, engine trust = 0.20.
Trigger engine safety violation (severity=0.7).
Verify: engine trust drops, steering trust unchanged.

---

### Component 5: Reflex Compiler (jetson/reflex_compiler/)

**SPEC REFERENCE:** `specs/jetson/learning_pipeline_spec.md` Section 2 (compiler context)

#### 5.1 Input Format (JSON Reflex)

```json
{
  "name": "heading_hold",
  "intent": "Maintain heading 270 degrees when wind is below 20 knots",
  "sensors": ["compass_heading", "wind_speed"],
  "actuators": ["rudder_angle"],
  "trust_min": 0.50,
  "trust_max": 0.90,
  "safety_class": "NORMAL",
  "author": "human|agent:qwen2.5-coder-7b@vessel-7",
  "body": [
    {"op": "READ_PIN", "arg": 0, "comment": "Load compass heading"},
    {"op": "PUSH_F32", "value": 270.0},
    {"op": "SUB_F"},
    {"op": "READ_PIN", "arg": 1, "comment": "Load wind speed"},
    {"op": "PUSH_F32", "value": 20.0},
    {"op": "GT_F"},
    {"op": "JUMP_IF_TRUE", "target": "fallback"},
    {"op": "CLAMP_F", "lo": -30.0, "hi": 30.0},
    {"op": "WRITE_PIN", "arg": 0, "comment": "Set rudder angle"},
    {"label": "halt"},
    {"op": "NOP", "flags": "0x80", "operand1": 1},
    {"label": "fallback"},
    {"op": "PUSH_F32", "value": 0.0},
    {"op": "WRITE_PIN", "arg": 0},
    {"op": "NOP", "flags": "0x80", "operand1": 1}
  ]
}
```

#### 5.2 Compilation Pipeline

```
JSON → Parse → Validate → Assemble → Optimize → Emit → Verify
```

**Parse:** Deserialize JSON, extract opcodes, labels, metadata.

**Validate (static analysis):**
1. All opcodes exist in the ISA (0x00–0x1F for core; 0x20–0x56 for A2A)
2. Stack effects are consistent (no underflow/overflow possible on any path)
3. All labels resolve to valid 8-byte-aligned byte offsets
4. Jump targets are within bytecode bounds
5. WRITE_PIN is always preceded by CLAMP_F (safety rule SR-005 variant)
6. Total cycle count fits within tick budget
7. No unreachable code (dead code is a warning, not an error)
8. PID_COMPUTE has correct stack layout (setpoint=TOS1, input=TOS)
9. Division is protected (DIV_F has implicit zero-check, but warn on pattern)

**Assemble:** Resolve labels to byte offsets. Convert opcodes to 8-byte instruction format. Encode immediates in the correct fields.

**Optimize (minimal, safety-first):**
1. Dead code elimination: remove unreachable instructions after unconditional jumps/returns
2. Constant folding: `PUSH_F32 1.0; PUSH_F32 2.0; ADD_F` → `PUSH_F32 3.0`
3. NO loop unrolling, NO speculative execution, NO instruction reordering. Safety first.

**Emit:** Binary bytecode file (.rbc) — 8 bytes per instruction. Sidecar JSON metadata (.rbc.meta) with AAB TLV fields for agent-interpretable annotation.

**Verify:** Run the validator on the emitted bytecode. If it fails, do NOT emit.

#### 5.3 Output Format

Binary file (`.rbc`): raw 8-byte instructions, loaded into VM's bytecode buffer.
Metadata file (`.rbc.meta`): JSON with source info, trust requirements, sensor/actuator bindings, safety classification, agent provenance.

---

### Component 6: LLM Agent Runtime (jetson/agent_runtime/)

**SPEC REFERENCE:** `a2a-native-specs/bytecode_vm_a2a_native.md`

#### 6.1 Agent-Annotated Bytecode (AAB) Format

Every AAB instruction: 8-byte core + variable-length TLV metadata.

```
┌─────────────────────────────────────────────────────────────┐
│ Core Instruction (8 bytes — identical to NEXUS VM format)    │
├─────────────────────────────────────────────────────────────┤
│ TLV Metadata Block (variable length)                        │
│  [Tag:1][Length:2][Value:N] ... [Tag:0x00]                │
└─────────────────────────────────────────────────────────────┘
```

**13 TLV Tags:**

| Tag | Name | Example Value |
|-----|------|--------------|
| 0x01 | TYPE_DESC | `"f32→f32:degrees"` |
| 0x02 | CAP_REQ | `"sensor:imu:compass"` |
| 0x03 | PRE_COND | `"SP >= 2"` |
| 0x04 | POST_COND | `"TOS ∈ [-180, 360]"` |
| 0x05 | INTENT_ID | `"heading_hold.body.line_3"` |
| 0x06 | TRUST_MIN | `"0.50"` |
| 0x07 | AGENT_SOURCE | `"qwen2.5-coder-7b@vessel-7"` |
| 0x08 | TIMESTAMP | `"2025-07-12T14:30:00Z"` |
| 0x09 | CONFIDENCE | `"0.95"` |
| 0x0A | NARRATIVE | `"Read compass heading"` |
| 0x0B | PROVENANCE | `"gen:qwen;val:claude"` |
| 0x0C | SAFETY_FLAG | `"NORMAL"` |
| 0x0D | DOMAIN_TAG | `"marine:autopilot"` |

**Stripping (AAB → Core):** Copy first 8 bytes of each instruction. Skip TLV metadata. Deterministic, O(n). The ESP32 receives ONLY stripped core bytecode.

#### 6.2 The 29 New A2A Opcodes (0x20–0x56)

All execute on the Jetson (agent runtime). On the ESP32, they are treated as NOP with zero cycle cost. The ESP32 dispatch table only handles 0x00–0x1F; opcodes >= 0x20 silently advance PC by 8. This backward compatibility is absolute and non-negotiable — a firmware update must never be required to support new agent-level opcodes.

**Why NOP on ESP32:** The ESP32's fetch-decode-execute loop uses a 32-entry dispatch table indexed by `opcode & 0x1F`. Any opcode >= 0x20 hits index `opcode & 0x1F`, which maps to 0x00 (NOP). The remaining 7 bytes of the instruction are ignored. PC advances by exactly 8 bytes. No crash, no halt, no undefined behavior. This was verified by exhaustive testing of all 61 possible new-opcode values (0x20 through 0x5C).

**Implication for the A2A compiler:** The compiler must be aware that A2A opcodes in the 0x20–0x56 range will be silently ignored on ESP32s running firmware that does not understand them. The compiler should:
1. Mark all A2A opcodes as ESP32-NOP in the opcode table.
2. Issue a warning if the bytecode contains A2A opcodes but the target platform is ESP32.
3. Always generate both AAB (full) and core (stripped) outputs.
4. Document which opcodes are meaningful on which platform.

**Intent Opcodes (0x20–0x26):**
- 0x20 DECLARE_INTENT: Program's purpose. Must be first instruction in every AAB program.
- 0x21 ASSERT_GOAL: Expected outcome for post-execution verification.
- 0x22 VERIFY_OUTCOME: Runtime metric tolerance check.
- 0x23 DECLARE_CONSTRAINT: Hard constraint on behavior.
- 0x24/0x25 INTENT_SCOPE_BEGIN/END: Named scope for nested intentions.
- 0x26 EXPLAIN_FAILURE: Human-readable failure explanation.

**Agent Communication (0x30–0x34):**
- 0x30 TELL: Send info to another agent/vessel. BROADCAST flag.
- 0x31 ASK: Request data from another agent. BLOCKING flag.
- 0x32 DELEGATE: Assign task to another agent. AUTHORITY_FULL flag.
- 0x33 REPORT_STATUS: Status to supervisor.
- 0x34 REQUEST_OVERRIDE: Request human/higher-agent intervention.

**Capability Negotiation (0x40–0x44):**
- 0x40 REQUIRE_CAPABILITY: Declare hardware need (sensor/actuator/compute/comm/storage).
- 0x41 CAPABILITY_RESPONSE: Deployment system confirms/denies.
- 0x42 DECLARE_SENSOR_NEED: Sensor + minimum sample rate.
- 0x43 DECLARE_ACTUATOR_USE: Actuator + maximum rate of change.
- 0x44 DECLARE_COMPUTE_NEED: Computation budget in cycles.

**Safety Augmentation (0x50–0x56):**
- 0x50 TRUST_CHECK: Verify trust >= min_trust before proceeding. THE trust gate.
- 0x51 AUTONOMY_LEVEL_ASSERT: Assert current autonomy level.
- 0x52 SAFE_BOUNDARY: Safety boundary with margin.
- 0x53 RATE_LIMIT: Rate of change limit on variable.
- 0x54 DEADBAND: Deadband filter on variable.
- 0x55 WATCHDOG_PET: Reset software watchdog.
- 0x56 SAFETY_EVENT_EMIT: Emit safety-critical event to supervisor.

---

## Verification Checklist

A master checklist for every pull request. Every item must pass before merge.

### VM Tests
- [ ] All 32 opcodes pass unit tests with correct stack effects and cycle counts
- [ ] Stack underflow detection works for every opcode that pops (POP, DUP, SWAP, ROT, ADD_F, SUB_F, MUL_F, DIV_F, EQ_F, LT_F, GT_F, LTE_F, GTE_F, AND_B, OR_B, XOR_B, READ_PIN, WRITE_PIN, JUMP_IF_FALSE, JUMP_IF_TRUE)
- [ ] Stack overflow detection works for PUSH_I8, PUSH_I16, PUSH_F32, DUP
- [ ] Division by zero returns 0.0f (NOT IEEE Inf/NaN)
- [ ] CLAMP_F correctly constrains values to [lo, hi]
- [ ] Cycle budget enforcement halts execution at exact cycle count
- [ ] Jump target bounds checking rejects out-of-range targets
- [ ] PID_COMPUTE produces correct output with anti-windup
- [ ] CALL/RET via call stack works (max depth 16)
- [ ] HALT syscall stops execution cleanly
- [ ] RECORD_SNAPSHOT captures correct state
- [ ] EMIT_EVENT queues to ring buffer

### Wire Protocol Tests
- [ ] COBS encode/decode round-trip for all test vectors (including all-zeros, all-0xFF)
- [ ] CRC-16/CCITT-FALSE check value 0x29B1 for "123456789"
- [ ] Full frame encode → COBS → decode → dispatch → payload matches
- [ ] CRC failure triggers CRC_MISMATCH error, dispatch NOT called
- [ ] Frame too large (>1053 bytes) triggers FRAME_TOO_LARGE error
- ] Frame too short (<12 bytes decoded) triggers FRAME_TOO_SHORT error
- ] Sequence number validation detects gaps and duplicates
- ] Heartbeat escalation: HEALTHY → WARN → DEGRADED → FAILSAFE at correct timeouts

### Safety System Tests
- [ ] E-Stop ISR completes in <1ms from GPIO edge to actuator output change
- [ ] Hardware watchdog (MAX6818) resets system within 1.1s of kick pattern stop
- [ ] Software watchdog detects hung task within 1.0s
- [ ] Safety state machine: NORMAL → DEGRADED (500ms) → SAFE_STATE (1000ms)
- [ ] All actuators driven to safe state on SAFE_STATE entry
- [ ] System does NOT auto-resume after SAFE_STATE (requires explicit RESUME)
- [ ] Kill switch NC contact break physically interrupts actuator power
- [ ] Overcurrent detection disables output within 2ms of threshold crossing

### Trust Engine Tests
- [ ] Trust increases from 0.0 toward 1.0 under continuous good events (verify formula matches spec exactly)
- [ ] Trust decreases from 1.0 toward 0.0 under continuous bad events
- [ ] Agent code multiplier (0.5x gain rate) produces correct trajectory
- [ ] Per-subsystem independence: one failure does not cascade
- [ ] All 8 reset types produce correct trust values and level transitions
- [ ] Autonomy level promotion requires all criteria simultaneously
- [ ] Autonomy level demotion is immediate when trust drops
- [ ] Reset grace period prevents thrashing
- [ ] Parameter validation rejects invalid parameter combinations

### Integration Tests
- [ ] Zero heap allocations on ESP32 (verified by linker script — no .malloc sections)
- [ ] Deterministic execution: same input → same output in same cycles (100 repetitions, zero variance)
- [ ] Full boot sequence: POST → DEVICE_IDENTITY → SELFTEST_RESULT → ROLE_ASSIGN → ROLE_ACK → OPERATIONAL
- [ ] Baud negotiation: 115200 → 921600 successful upgrade
- [ ] REFLEX_DEPLOY: compile → validate → send → receive → execute → report status

### Code Quality
- [ ] No compiler warnings (`-Wall -Wextra -Werror`)
- [ ] Safety policy coverage > 90% (all 10 global rules checked)
- [ ] Code matches spec (not the other way around)
- [ ] All AAB metadata tags are populated for agent-generated code
- [ ] Every WRITE_PIN in compiled bytecode is preceded by CLAMP_F

---

## Anti-Patterns to Avoid

**Ten things Claude Code MUST NOT do when building NEXUS:**

1. **NEVER use malloc/free/calloc/realloc on ESP32.** All memory is statically allocated. The linker script places everything in .bss/.data. The idle task monitors heap free size and triggers DEGRADED at < 32KB free, SAFE_STATE at < 16KB.

2. **NEVER bypass the trust score check.** Every reflex deployment must verify trust >= trust_min for the target subsystem. There is no override, no backdoor, no "trust_override" flag. The trust algorithm is the mathematical embodiment of "you must earn the right to act autonomously."

3. **NEVER write actuator values without CLAMP_F.** This is the single most safety-critical pattern violation. Every WRITE_PIN must have a CLAMP_F immediately before it in the instruction stream. The validator enforces this. If the clamp range doesn't fit the shared-upper-half encoding constraint, decompose into MAX_F + MIN_F.

4. **NEVER implement a jump without bounds checking.** All jump targets must be validated at compile time: `target < bytecode_size` AND `target % 8 == 0`. The validator rejects out-of-bounds targets. Runtime jumps to invalid targets halt the VM.

5. **NEVER use floating-point division without checking for zero.** The VM's DIV_F opcode returns 0.0f on division by zero (not IEEE Inf/NaN). But in C firmware code outside the VM, every float division must be preceded by `if (fabs(denominator) < EPSILON)`.

6. **NEVER skip the safety validation pipeline.** Every code artifact goes through: syntax_check → static_analysis → memory_budget → safety_rules → simulation → trust_gate → deployment_approval. Skipping any step blocks deployment. No exceptions.

7. **NEVER generate bytecode without AAB metadata for agent-generated code.** Agent-generated bytecode MUST carry AGENT_SOURCE (tag 0x07), CONFIDENCE (0x09), PROVENANCE (0x0B), and NARRATIVE (0x0A) tags. Metadata is the audit trail. Without it, the code is undocumented.

8. **NEVER modify safety parameters without formal justification.** Parameters like alpha_gain, alpha_loss, t_floor, watchdog timeouts, heartbeat thresholds, overcurrent limits, and rate limits are safety-critical constants. Changing them requires a signed safety review. Document the rationale.

9. **NEVER deploy to production without passing all test vectors.** Every PR must pass the full verification checklist above. Every opcode must have a unit test. Every message type must have a round-trip test. Every safety state transition must be verified.

10. **NEVER prioritize performance over safety.** The ESP32 runs at 240MHz. The VM tick loop completes in well under 1ms with cycles to spare. You have the budget. Use it for safety checks. Add the extra bounds check. Validate the extra input. The cost of a safety violation is measured in human lives, not CPU cycles.

---

## Estimated Build Timeline

| Phase | Component | Duration | Dependencies |
|-------|-----------|----------|-------------|
| 0 | Foundation setup, monorepo scaffolding | 3 days | None |
| 1 | Bytecode VM interpreter | 10 days | Phase 0 |
| 2 | Wire protocol (COBS, CRC, UART driver) | 5 days | Phase 1 |
| 3 | Safety system (kill switch, watchdog, heartbeat) | 7 days | Phase 2 |
| 4 | Jetson trust engine + reflex compiler | 10 days | Phase 1 |
| 5 | Learning pipeline (observation, patterns) | 10 days | Phase 4 |
| 6 | A2A-native extensions (AAB, 29 opcodes) | 7 days | Phases 1, 4 |
| 7 | Integration + HIL testing | 5 days | All above |
| | **Total** | **57 days (~8 weeks)** | |

**First demo target:** After Phase 3 (~25 days), a working ESP32 running the VM with safety system, communicating with Jetson via RS-422, executing simple reflex programs.

---

## Final Notes

This specification is derived entirely from the production specifications in the `specs/` directory. If you find a discrepancy between this document and a source specification, the source specification wins. File an issue.

The NEXUS system represents a fundamentally different approach to robotic control: one where the control code is written by AI agents, interpreted by a deterministic VM, governed by a mathematical trust algorithm, and protected by four independent safety tiers. Every design decision exists for a reason. Honor those reasons. Build it exactly as specified.

**Remember:** The VM is the interface. The trust score gates everything. Safety is non-negotiable. Specs are the source of truth. Zero heap on ESP32. Determinism is required.

Now build it.
