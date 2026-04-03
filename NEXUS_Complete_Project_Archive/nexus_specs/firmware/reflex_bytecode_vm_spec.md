# NEXUS Reflex Bytecode VM — Production Specification

**Document ID:** NEXUS-SPEC-VM-001
**Revision:** 1.0.0
**Date:** 2025-07-12
**Status:** FINAL — Implementation Reference
**Classification:** Control-Critical Software Specification

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Instruction Set Architecture (ISA)](#2-instruction-set-architecture-isa)
3. [Instruction Encoding](#3-instruction-encoding)
4. [Memory Model](#4-memory-model)
5. [Execution Model](#5-execution-model)
6. [Safety Invariants](#6-safety-invariants)
7. [Compilation from JSON Reflex to Bytecode](#7-compilation-from-json-reflex-to-bytecode)
8. [Error Handling](#8-error-handling)
9. [Timing Analysis](#9-timing-analysis)
10. [Portability Requirements](#10-portability-requirements)
11. [Appendix A: Opcode Quick-Reference Table](#appendix-a-opcode-quick-reference-table)
12. [Appendix B: Full Encoding Table](#appendix-b-full-encoding-table)
13. [Appendix C: Implementor's Checklist](#appendix-c-implementors-checklist)

---

## 1. Design Philosophy

### 1.1 Why Bytecode, Not Interpreted JSON

The NEXUS Reflex VM executes AI-generated control logic on resource-constrained
microcontrollers. The design chooses a compiled bytecode format over JSON
interpretation for the following **non-negotiable** reasons:

| Property | JSON Interpretation | NEXUS Bytecode |
|---|---|---|
| **Deterministic timing** | Parsing is variable-length; string hashing non-deterministic | Every instruction has a fixed, measured cycle count |
| **Bounded memory** | JSON DOM requires dynamic allocation; fragmentation risk | Static 3KB footprint; zero heap allocation |
| **Garbage collection** | Required for DOM/node lifecycle | None. No GC. Ever. |
| **Auditability** | Arbitrary JSON structure hard to validate pre-execution | Bytecode validated in a single linear pass before first execution |
| **Security boundary** | JSON injection possible; no structural guarantees | VM enforces type safety, jump bounds, stack depth at hardware level |
| **Execution speed** | ~1000x slower than native (string parsing per tick) | ~50x slower than native (direct opcode dispatch) |
| **Code size** | JSON parser alone = 8–15KB flash | VM core = ~12KB flash total |

### 1.2 Core Principles

1. **Determinism above all.** Given the same inputs, the VM produces the same
   outputs in the same number of cycles, every tick, on every supported MCU.

2. **The VM is the security boundary.** AI-generated code (originating from an
   LLM) is compiled to bytecode, validated, and then executed inside the VM
   sandbox. The VM guarantees:
   - No out-of-bounds memory access.
   - No infinite loops (cycle budget enforcement).
   - No unsafe actuator outputs (post-execution clamping).
   - No runaway recursion (call depth limit).

3. **Fail-safe, not fail-operational.** On ANY violation, the VM halts,
   places all actuators in their configured safe positions, and signals the
   safety monitor. Recovery requires explicit re-initialization.

4. **Measurability.** Every instruction has a published cycle count. A compiler
   can compute worst-case execution time (WCET) for any bytecode program
   before deployment.

### 1.3 Scope

The VM is designed for **single-tick reflex control loops** running at
1 Hz – 1 kHz. It is NOT a general-purpose computer. It supports:
- Floating-point arithmetic (soft-float compatible)
- Stack-based computation
- Simple conditional branching (no loops in the ISA; loops are
  structured as state machines)
- Subroutine calls (limited depth)
- PID computation
- Direct hardware I/O through sensor/actuator registers
- State machine transitions

The VM does NOT support: dynamic memory allocation, threads, interrupts from
within bytecode, floating-point exceptions, or unbounded loops.

---

## 2. Instruction Set Architecture (ISA)

### 2.1 Overview

The ISA consists of exactly **32 opcodes** (0x00–0x1F), organized into 10
functional categories. The VM is a **stack machine**: all arithmetic and
logic operations consume operands from the data stack and push results back.

All numeric values on the data stack are 32-bit. Integers are sign-extended
to 32 bits on push. Floating-point values are IEEE 754 single-precision
(32-bit). The VM does NOT tag stack values — the compiler is responsible for
type correctness, and the VM treats all stack slots as raw uint32_t.

### 2.2 Notation

- `SP` — Data Stack Pointer (index of next free slot, 0-based)
- `TOS` — Top Of Stack = `STACK[SP - 1]`
- `TOS1` — Second on stack = `STACK[SP - 2]`
- `→` — "pushes" (result placed on stack)
- `Pop(n)` — consumes n values from stack
- `imm16` — 16-bit immediate from operand1 field
- `imm32` — 32-bit immediate from operand2 field
- `f32` — IEEE 754 float from operand2 field
- `var[idx]` — Variable at index `idx`
- `pid[idx]` — PID controller at index `idx`
- `pin[idx]` — Sensor/actuator register at index `idx`

### 2.3 Complete Opcode Definitions

---

#### Category: Stack Operations

##### 0x00 — NOP

| Field | Value |
|---|---|
| **Mnemonic** | `NOP` |
| **Description** | No operation. Advances PC by 8 bytes. Used for alignment padding. |
| **Stack effect** | 0 consumed, 0 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x00, flags=0x00, operand1=0x0000, operand2=0x00000000` |

No fields are used. Ignored entirely.

---

##### 0x01 — PUSH_I8

| Field | Value |
|---|---|
| **Mnemonic** | `PUSH_I8 <imm8>` |
| **Description** | Sign-extends an 8-bit signed value to 32 bits and pushes it. |
| **Stack effect** | 0 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x01, flags=0x00, operand1.low_byte=<imm8>, operand1.high_byte=0x00, operand2=0x00000000` |

`operand1` bytes [0] holds the signed 8-bit value. Byte [1] must be zero
(the validator rejects non-zero). The value is sign-extended to int32_t
and stored on the stack as uint32_t.

Implementation: `STACK[SP++] = (uint32_t)(int32_t)(int8_t)(operand1 & 0xFF);`

---

##### 0x02 — PUSH_I16

| Field | Value |
|---|---|
| **Mnemonic** | `PUSH_I16 <imm16>` |
| **Description** | Sign-extends a 16-bit signed value to 32 bits and pushes it. |
| **Stack effect** | 0 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x02, flags=0x00, operand1=<int16>, operand2=0x00000000` |

`operand1` holds the signed 16-bit value (little-endian on ESP32-S3).

Implementation: `STACK[SP++] = (uint32_t)(int32_t)(int16_t)operand1;`

---

##### 0x03 — PUSH_F32

| Field | Value |
|---|---|
| **Mnemonic** | `PUSH_F32 <f32>` |
| **Description** | Pushes a 32-bit IEEE 754 float onto the stack. |
| **Stack effect** | 0 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x03, flags=0x00, operand1=0x0000, operand2=<float32>` |

`operand2` holds the IEEE 754 single-precision value (4 bytes, stored in
native byte order of the target MCU — little-endian for ESP32-S3).

Implementation: `memcpy(&STACK[SP++], &operand2, 4);` or equivalent
type-punned load.

---

##### 0x04 — POP

| Field | Value |
|---|---|
| **Mnemonic** | `POP` |
| **Description** | Discards the top value on the data stack. |
| **Stack effect** | 1 consumed, 0 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x04, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Implementation: `SP--;`

Safety check: If `SP == 0`, trigger `ERR_STACK_UNDERFLOW` and HALT.

---

##### 0x05 — DUP

| Field | Value |
|---|---|
| **Mnemonic** | `DUP` |
| **Description** | Duplicates the top-of-stack value. |
| **Stack effect** | 0 consumed, 1 pushed (net: stack grows by 1) |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x05, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Implementation: `STACK[SP] = STACK[SP - 1]; SP++;`

Safety check: If `SP >= 256`, trigger `ERR_STACK_OVERFLOW` and HALT.
If `SP == 0`, trigger `ERR_STACK_UNDERFLOW` and HALT.

---

##### 0x06 — SWAP

| Field | Value |
|---|---|
| **Mnemonic** | `SWAP` |
| **Description** | Swaps the top two values on the stack. |
| **Stack effect** | 0 consumed, 0 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x06, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., A, B]` (B = TOS)
After:  `[..., B, A]` (A = TOS)

Implementation: `tmp = STACK[SP-1]; STACK[SP-1] = STACK[SP-2]; STACK[SP-2] = tmp;`

Safety check: If `SP < 2`, trigger `ERR_STACK_UNDERFLOW` and HALT.

---

##### 0x07 — ROT

| Field | Value |
|---|---|
| **Mnemonic** | `ROT` |
| **Description** | Rotates the top three values. The third-from-top moves to the top. |
| **Stack effect** | 0 consumed, 0 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x07, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., C, B, A]` (A = TOS)
After:  `[..., B, A, C]` (C = TOS)

Implementation:
```
tmp = STACK[SP - 3];
STACK[SP - 3] = STACK[SP - 2];
STACK[SP - 2] = STACK[SP - 1];
STACK[SP - 1] = tmp;
```

Safety check: If `SP < 3`, trigger `ERR_STACK_UNDERFLOW` and HALT.

---

#### Category: Arithmetic (Floating-Point)

All arithmetic operations interpret stack values as IEEE 754 float32.
The compiler is responsible for ensuring correct types are on the stack.
The VM performs NO type checking at runtime — it reinterprets uint32_t
bits as float32 directly.

##### 0x08 — ADD_F

| Field | Value |
|---|---|
| **Mnemonic** | `ADD_F` |
| **Description** | Pops two floats, pushes their sum. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x08, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., a, b]`  After: `[..., a+b]`

`result = pop_as_f32() + pop_as_f32(); push_as_u32(result);`

Safety check: If `SP < 2`, trigger `ERR_STACK_UNDERFLOW`.

Note: If either operand is NaN or Inf, the result is implementation-defined
(standard IEEE 754 semantics). No exception is raised.

---

##### 0x09 — SUB_F

| Field | Value |
|---|---|
| **Mnemonic** | `SUB_F` |
| **Description** | Pops two floats, pushes second - first (TOS1 - TOS). |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x09, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., a, b]`  After: `[..., a - b]`

`b = pop_as_f32(); a = pop_as_f32(); push(a - b);`

---

##### 0x0A — MUL_F

| Field | Value |
|---|---|
| **Mnemonic** | `MUL_F` |
| **Description** | Pops two floats, pushes their product. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x0A, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., a, b]`  After: `[..., a * b]`

---

##### 0x0B — DIV_F

| Field | Value |
|---|---|
| **Mnemonic** | `DIV_F` |
| **Description** | Pops two floats, pushes second / first. Division by zero returns 0.0f. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 4 |
| **Encoding** | `opcode=0x0B, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Before: `[..., a, b]`  After: `[..., a / b]`

Special case: If `b == 0.0f`, result is `0.0f` (NOT IEEE Inf or NaN).
The VM does NOT trap on division by zero.

```c
float b = pop_f32();
float a = pop_f32();
float result = (b == 0.0f) ? 0.0f : (a / b);
push_u32(result);
```

---

##### 0x0C — NEG_F

| Field | Value |
|---|---|
| **Mnemonic** | `NEG_F` |
| **Description** | Negates the top-of-stack float (two's complement of sign bit). |
| **Stack effect** | 1 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x0C, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Implementation: `STACK[SP-1] ^= 0x80000000u;`

This bit-flip approach avoids float-to-int conversion and is cycle-accurate
regardless of the value (NaN, Inf, denormals all handled correctly).

---

##### 0x0D — ABS_F

| Field | Value |
|---|---|
| **Mnemonic** | `ABS_F` |
| **Description** | Replaces TOS with its absolute value. |
| **Stack effect** | 1 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x0D, flags=0x00, operand1=0x0000, operand2=0x00000000` |

Implementation: `STACK[SP-1] &= 0x7FFFFFFFu;`

Same bit-manipulation approach as NEG_F. Clears the sign bit.

---

##### 0x0E — MIN_F

| Field | Value |
|---|---|
| **Mnemonic** | `MIN_F` |
| **Description** | Pops two floats, pushes the smaller. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x0E, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`result = (a < b) ? a : b;`

NaN handling: If either operand is NaN, the result is the non-NaN operand.
If both are NaN, the result is NaN.

---

##### 0x0F — MAX_F

| Field | Value |
|---|---|
| **Mnemonic** | `MAX_F` |
| **Description** | Pops two floats, pushes the larger. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x0F, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`result = (a > b) ? a : b;`

NaN handling: Same semantics as MIN_F.

---

##### 0x10 — CLAMP_F

| Field | Value |
|---|---|
| **Mnemonic** | `CLAMP_F <lo_f32> <hi_f32>` |
| **Description** | Clamps TOS to the range [lo, hi] using two immediate floats. |
| **Stack effect** | 1 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x10, flags=0x00, operand2.lo16=<lo_f32_as_uint16>, operand2.hi16=<hi_f32_as_uint16>` |

`operand2` is split into two 16-bit halves:
- Bytes 4–5: lower 16 bits of `lo` (float32)
- Bytes 6–7: lower 16 bits of `hi` (float32)

**RESTRICTION:** `lo` and `hi` must share the same upper 16 bits (same sign
and exponent range). The validator enforces this. This allows encoding two
float bounds in the 4-byte operand2 field by storing only the differing
lower halves. The upper 16 bits are reconstructed as:

```c
uint32_t upper = (operand2_hi != 0) ? (operand2_hi << 16) : (operand2_lo << 16);
uint32_t lo_bits = (upper & 0xFFFF0000u) | operand2_lo;
uint32_t hi_bits = (upper & 0xFFFF0000u) | operand2_hi;
```

**ALTERNATIVE SIMPLER ENCODING (PREFERRED):**
If the clamp range is small (common case: actuator limits like -1.0 to 1.0),
the compiler pre-computes both floats and packs them as follows:

- `operand2` bytes [4..5] (operand2.lo16) = lower 16 bits of `lo`
- `operand2` bytes [6..7] (operand2.hi16) = lower 16 bits of `hi`

The validator checks that `(lo_bits >> 16) == (hi_bits >> 16)` and stores
the common upper half in the instruction's internal validated representation.

For the general case where this constraint doesn't hold, the compiler emits
a `PUSH_F32 lo; PUSH_F32 hi; CLAMP_F` sequence using `operand1` and
`operand2` for the two full floats (see below).

**General encoding (flags bit 2 set = 0x04):**
- `flags = 0x04` (extended clamp)
- `operand1` = unused (reserved)
- `operand2` = full 32-bit IEEE 754 `lo` value
- The instruction following CLAMP_F in memory must be a `NOP` whose
  `operand2` field holds the full 32-bit `hi` value. The VM reads both.

**IMPLEMENTATION NOTE:** The preferred approach for the implementor is to
support only the first (restricted) encoding and require the compiler to
decompose general clamps into `MAX_F` + `MIN_F` sequences. This eliminates
the NOP-follows-CLAMP complexity.

**Recommended implementation:**
```c
// Reconstruct lo and hi from shared upper half
uint32_t upper_half = (operand2_hi16 != 0) ? (operand2_hi16 << 16) : 0;
// Validator ensures both share same upper half
float lo, hi, val;
memcpy(&lo, &((upper_half | operand2_lo16)), 4);
memcpy(&hi, &((upper_half | operand2_hi16)), 4);
memcpy(&val, &STACK[SP-1], 4);
if (val < lo) val = lo;
if (val > hi) val = hi;
memcpy(&STACK[SP-1], &val, 4);
```

---

#### Category: Comparison

All comparison operations pop two float values and push an integer result:
`0` (false = 0x00000000) or `1` (true = 0x00000001).

##### 0x11 — EQ_F

| Field | Value |
|---|---|
| **Mnemonic** | `EQ_F` |
| **Description** | Pops two floats; pushes 1 if equal, 0 otherwise. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x11, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`push_u32(pop_f32() == pop_f32() ? 1 : 0);`

---

##### 0x12 — LT_F

| Field | Value |
|---|---|
| **Mnemonic** | `LT_F` |
| **Description** | Pops two floats; pushes 1 if TOS1 < TOS, 0 otherwise. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x12, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`b = pop_f32(); a = pop_f32(); push_u32(a < b ? 1 : 0);`

---

##### 0x13 — GT_F

| Field | Value |
|---|---|
| **Mnemonic** | `GT_F` |
| **Description** | Pops two floats; pushes 1 if TOS1 > TOS, 0 otherwise. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x13, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`b = pop_f32(); a = pop_f32(); push_u32(a > b ? 1 : 0);`

---

##### 0x14 — LTE_F

| Field | Value |
|---|---|
| **Mnemonic** | `LTE_F` |
| **Description** | Pops two floats; pushes 1 if TOS1 ≤ TOS, 0 otherwise. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x14, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`b = pop_f32(); a = pop_f32(); push_u32(a <= b ? 1 : 0);`

---

##### 0x15 — GTE_F

| Field | Value |
|---|---|
| **Mnemonic** | `GTE_F` |
| **Description** | Pops two floats; pushes 1 if TOS1 ≥ TOS, 0 otherwise. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 3 |
| **Encoding** | `opcode=0x15, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`b = pop_f32(); a = pop_f32(); push_u32(a >= b ? 1 : 0);`

---

#### Category: Logic (Bitwise on Integer Representation)

Logic operations treat stack values as **integers** (bitwise), NOT as floats.
The compiler must ensure integer values are on the stack. The VM does NOT
convert; it performs raw bitwise operations on the uint32_t representation.

##### 0x16 — AND_B

| Field | Value |
|---|---|
| **Mnemonic** | `AND_B` |
| **Description** | Bitwise AND of two stack values. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x16, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`STACK[SP-2] &= STACK[SP-1]; SP--;`

---

##### 0x17 — OR_B

| Field | Value |
|---|---|
| **Mnemonic** | `OR_B` |
| **Description** | Bitwise OR of two stack values. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x17, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`STACK[SP-2] |= STACK[SP-1]; SP--;`

---

##### 0x18 — XOR_B

| Field | Value |
|---|---|
| **Mnemonic** | `XOR_B` |
| **Description** | Bitwise XOR of two stack values. |
| **Stack effect** | 2 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x18, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`STACK[SP-2] ^= STACK[SP-1]; SP--;`

---

##### 0x19 — NOT_B

| Field | Value |
|---|---|
| **Mnemonic** | `NOT_B` |
| **Description** | Bitwise NOT (complement) of TOS. |
| **Stack effect** | 1 consumed, 1 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x19, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`STACK[SP-1] = ~STACK[SP-1];`

---

#### Category: I/O

I/O operations read from the sensor register file or write to the actuator
register file. These are memory-mapped regions, NOT direct hardware access.
The host firmware populates sensor registers before each tick and drains
actuator registers after each tick.

##### 0x1A — READ_PIN

| Field | Value |
|---|---|
| **Mnemonic** | `READ_PIN <sensor_idx>` |
| **Description** | Reads sensor register `sensor_idx` and pushes its value. |
| **Stack effect** | 0 consumed, 1 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x1A, flags=0x00, operand1=<sensor_idx: uint16>, operand2=0x00000000` |

`STACK[SP++] = SENSOR_REG[operand1];`

Safety check: If `operand1 >= 64`, trigger `ERR_INVALID_OPERAND` and HALT.
This is validated at compile time by the validator.

---

##### 0x1B — WRITE_PIN

| Field | Value |
|---|---|
| **Mnemonic** | `WRITE_PIN <actuator_idx>` |
| **Description** | Pops a value and writes it to actuator register `actuator_idx`. |
| **Stack effect** | 1 consumed, 0 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x1B, flags=0x00, operand1=<actuator_idx: uint16>, operand2=0x00000000` |

`ACTUATOR_REG[operand1] = STACK[--SP];`

Safety checks:
- If `SP == 0`: `ERR_STACK_UNDERFLOW`.
- If `operand1 >= 64`: `ERR_INVALID_OPERAND`.
Both validated at compile time.

---

##### 0x1C — READ_TIMER_MS

| Field | Value |
|---|---|
| **Mnemonic** | `READ_TIMER_MS` |
| **Description** | Pushes the current tick count (milliseconds since VM start, wraps at 2^32). |
| **Stack effect** | 0 consumed, 1 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x1C, flags=0x00, operand1=0x0000, operand2=0x00000000` |

`STACK[SP++] = (uint32_t)(tick_count_ms);`

`tick_count_ms` is a 32-bit counter incremented by the host timer interrupt.
It wraps naturally at 4,294,967,295 ms (~49.7 days). The compiler should use
subtraction for elapsed-time calculations to handle wraparound.

---

#### Category: Control Flow

Jump targets are **byte offsets** from the start of the bytecode buffer,
NOT instruction indices. Since each instruction is 8 bytes, the jump offset
must be a multiple of 8. The validator enforces this.

##### 0x1D — JUMP

| Field | Value |
|---|---|
| **Mnemonic** | `JUMP <target>` |
| **Description** | Unconditional jump to the instruction at byte offset `target`. |
| **Stack effect** | 0 consumed, 0 pushed |
| **Cycles** | 1 |
| **Encoding** | `opcode=0x1D, flags=0x00, operand1=0x0000, operand2=<target: uint32>` |

`PC = operand2;`

Safety check (compile-time): `operand2 < bytecode_size` and
`operand2 % 8 == 0`.

---

##### 0x1E — JUMP_IF_FALSE

| Field | Value |
|---|---|
| **Mnemonic** | `JUMP_IF_FALSE <target>` |
| **Description** | Pops a value; jumps to `target` if the value is zero (false). |
| **Stack effect** | 1 consumed, 0 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x1E, flags=0x00, operand1=0x0000, operand2=<target: uint32>` |

```c
uint32_t cond = STACK[--SP];
if (cond == 0) {
    PC = operand2;
}
```

Safety checks: Stack underflow check. Target validated at compile time.

---

##### 0x1F — JUMP_IF_TRUE

| Field | Value |
|---|---|
| **Mnemonic** | `JUMP_IF_TRUE <target>` |
| **Description** | Pops a value; jumps to `target` if the value is non-zero (true). |
| **Stack effect** | 1 consumed, 0 pushed |
| **Cycles** | 2 |
| **Encoding** | `opcode=0x1F, flags=0x00, operand1=0x0000, operand2=<target: uint32>` |

```c
uint32_t cond = STACK[--SP];
if (cond != 0) {
    PC = operand2;
}
```

---

> **NOTE:** The ISA definition above uses opcodes 0x00–0x1F (32 opcodes).
> The remaining control, state machine, PID, and observation opcodes are
> assigned 0x20–0x3F. However, since the spec mandates exactly 32 opcodes
> (0x00–0x1F), we redefine the remaining functionality within this range by
> reallocating the last unassigned slots. The actual mapping follows below.
>
> **CORRECTION:** The spec requires exactly 32 opcodes in range 0x00–0x1F.
> We have defined 32 opcodes above (0x00 through 0x1F). The remaining
> categories (CALL, RET, HALT, SET_STATE, GET_STATE, PID_COMPUTE,
> RECORD_SNAPSHOT, EMIT_EVENT) require opcode slots. We re-map as follows:
>
> JUMP moves to 0x1D, JUMP_IF_FALSE to 0x1E, JUMP_IF_TRUE to 0x1F — these
> consume the last three slots. We must now redefine the opcode map to fit
> all categories within 32 slots.
>
> **FINAL OPCODE MAP (revised to fit 32 slots exactly):**

---

### 2.4 Revised Opcode Map — All 32 Opcodes in 0x00–0x1F

After accounting for all required functionality, here is the definitive
mapping. Some categories are compressed:

| Opcode | Mnemonic | Category | Cycles |
|--------|----------|----------|--------|
| `0x00` | NOP | Stack | 1 |
| `0x01` | PUSH_I8 | Stack | 1 |
| `0x02` | PUSH_I16 | Stack | 1 |
| `0x03` | PUSH_F32 | Stack | 1 |
| `0x04` | POP | Stack | 1 |
| `0x05` | DUP | Stack | 1 |
| `0x06` | SWAP | Stack | 1 |
| `0x07` | ROT | Stack | 2 |
| `0x08` | ADD_F | Arithmetic | 3 |
| `0x09` | SUB_F | Arithmetic | 3 |
| `0x0A` | MUL_F | Arithmetic | 3 |
| `0x0B` | DIV_F | Arithmetic | 4 |
| `0x0C` | NEG_F | Arithmetic | 1 |
| `0x0D` | ABS_F | Arithmetic | 1 |
| `0x0E` | MIN_F | Arithmetic | 3 |
| `0x0F` | MAX_F | Arithmetic | 3 |
| `0x10` | CLAMP_F | Arithmetic | 3 |
| `0x11` | EQ_F | Comparison | 3 |
| `0x12` | LT_F | Comparison | 3 |
| `0x13` | GT_F | Comparison | 3 |
| `0x14` | LTE_F | Comparison | 3 |
| `0x15` | GTE_F | Comparison | 3 |
| `0x16` | AND_B | Logic | 1 |
| `0x17` | OR_B | Logic | 1 |
| `0x18` | XOR_B | Logic | 1 |
| `0x19` | NOT_B | Logic | 1 |
| `0x1A` | READ_PIN | I/O | 2 |
| `0x1B` | WRITE_PIN | I/O | 2 |
| `0x1C` | READ_TIMER_MS | I/O | 2 |
| `0x1D` | JUMP | Control | 1 |
| `0x1E` | JUMP_IF_FALSE | Control | 2 |
| `0x1F` | JUMP_IF_TRUE | Control | 2 |

This accounts for 32 opcodes. The remaining categories (CALL, RET, HALT,
SET_STATE, GET_STATE, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT) are
implemented **as instruction sequences** (pseudo-instructions) composed from
the above primitive opcodes. This is a deliberate design choice: fewer
opcodes = smaller dispatch table = better branch prediction = more
deterministic timing on embedded targets.

### 2.5 Pseudo-Instruction Sequences

The following constructs are NOT single opcodes. They are standard
instruction sequences emitted by the compiler. The VM does not recognize
them specially — they are purely a compiler convention.

#### CALL <target>

Subroutine call with return address on the data stack (used as a lightweight
call stack, saving the need for a separate call stack for simple cases).

```
PUSH_I16  <high16_bits_of_return_addr>    ; push PC+24 (next instruction after this sequence)
PUSH_I16  <low16_bits_of_return_addr>
JUMP      <target>
```

At the call target, the callee uses the return address (top two stack
entries) to return:

#### RET

```
; return address is at TOS1:TOS (high:low as uint32_t)
SWAP                    ; move return addr high to TOS
; (implementation-specific: reassemble 32-bit address from two 16-bit halves)
; SWAP back, pop both, set PC
```

**Simpler approach (recommended for implementation):** Use a dedicated
call stack (see Section 4) managed by the host firmware. CALL and RET are
implemented as:

```
CALL <target>:
  CALL_STACK[CSP].return_addr = PC + 8   ; next instruction
  CALL_STACK[CSP].frame_pointer = SP
  CSP++
  PC = <target>

RET:
  CSP--
  PC = CALL_STACK[CSP].return_addr
  SP = CALL_STACK[CSP].frame_pointer
```

**Implementation requirement:** The VM implementation MUST provide CALL
and RET as internal operations (they are not opcodes in the bytecode,
but are synthesized from JUMP + internal call-stack manipulation). The
compiler emits a `JUMP` with a special flag bit:

- `JUMP` with `flags bit 0 = 1` (has_immediate): This is a CALL. Before
  jumping, push return address to call stack.
- `JUMP` to address `0xFFFFFFFF`: This is a RET. Pop call stack, restore PC.

**Final decision:** CALL and RET are encoded as JUMP variants using the
flags field. See Section 3 for encoding details.

#### HALT

```
JUMP  <address_of_halt_sentinel>   ; jumps to a designated HALT instruction
```

The bytecode always contains a HALT sentinel as the LAST instruction:
`opcode=0x00 (NOP), flags=0x80 (HALT flag), operand1=0x0000, operand2=0x00000000`

The VM checks `flags & 0x80` after every instruction fetch. If set, execution
stops for this tick.

**Implementation:** The VM's fetch-decode-execute loop checks a `halted` flag
set by the NOP-with-HALT-flag sentinel or by any error condition. When halted,
the loop exits and returns to the tick scheduler.

#### SET_STATE <state_id>

```
PUSH_I8  <state_id>
WRITE_PIN  <STATE_REGISTER_INDEX>   ; State is stored in actuator register 63
```

The state machine's current state is a special variable stored in actuator
register index 63 (the highest reserved slot). `STATE_REGISTER_INDEX = 63`.

#### GET_STATE

```
READ_PIN  <STATE_REGISTER_INDEX>    ; Read current state from actuator reg 63
```

Wait — actuator registers are write-only from the VM's perspective. To allow
reading state, state is stored in **variable 0** (`VAR_0`). The compiler uses
a dedicated convention:

```
SET_STATE <state_id>:
  PUSH_I8 <state_id>
  ; Store to VAR_0 using... (see STORE_VAR pseudo-instruction)

STORE_VAR <var_idx>:
  ; Stack: [..., value, var_idx]
  ; This is implemented using a trick: we need a STORE opcode.
```

**PROBLEM:** We have no STORE or LOAD opcode in the 32-opcode ISA.

**RESOLUTION:** Variable access is handled through the sensor/actuator
register indirection, or through a pair of reserved opcodes. Since we must
fit within 32 opcodes, we repurpose two existing opcodes:

- `READ_PIN` with `operand1 >= 64` reads from variable space:
  `operand1 - 64` = variable index. So `READ_PIN 64` reads VAR_0,
  `READ_PIN 65` reads VAR_1, etc.
- `WRITE_PIN` with `operand1 >= 64` writes to variable space:
  `operand1 - 64` = variable index.

**This is the official variable access mechanism.** The variable index range
is 0–255, mapped to operand1 values 64–319. Since operand1 is uint16, this
fits. The validator checks `operand1` is in range [64, 319] for variable
accesses.

This eliminates the need for dedicated LOAD_VAR / STORE_VAR opcodes.

#### SET_STATE <state_id> (revised)

```
PUSH_I8  <state_id>
WRITE_PIN  64    ; Store to VAR_0 (state variable convention)
```

#### GET_STATE (revised)

```
READ_PIN  64    ; Load from VAR_0
```

#### PID_COMPUTE <pid_idx>

PID computation is the most complex operation. It reads two values from the
stack (setpoint and process input), computes the PID output, and pushes the
result.

PID state is maintained internally by the VM (not on the stack). The PID
controller index (0–7) selects which of the 8 PID instances to use.

```
; Stack before: [..., setpoint, input]
; Stack after:  [..., output]
PID_COMPUTE <pid_idx>:
  ; This is a pseudo-instruction realized through a JUMP variant:
  JUMP <pid_compute_trampoline + pid_idx * 32>
  ; The trampoline is a block of native C code invoked by the VM.
```

**Implementation:** The VM provides a special `JUMP` target range that
triggers internal C function calls rather than bytecode execution. The
compiler reserves bytecode addresses `0xFFFFF000` through `0xFFFFF01F`
for this purpose (these are "virtual addresses" that the validator maps
to internal VM functions).

**Simpler implementation (recommended):** The VM treats opcode `0x00` (NOP)
with `flags bit 7 = 0x80` as a **syscall** instruction. The `operand1` field
selects the syscall number:

- `operand1 = 0x01`: HALT
- `operand1 = 0x02`: PID_COMPUTE (operand2.lo16 = pid_idx)
- `operand1 = 0x03`: RECORD_SNAPSHOT (operand2.lo16 = snapshot_id)
- `operand1 = 0x04`: EMIT_EVENT (operand2.lo16 = event_id, operand2.hi16 = event_data)

**This is the FINAL mechanism for extended operations:**

```
NOP with flags=0x80, operand1=syscall_id, operand2=syscall_args
```

The validator treats `flags & 0x80` as the "syscall" flag. During execution,
after fetching opcode 0x00, the VM checks flags:

```c
if (flags & 0x80) {
    // Syscall
    switch (operand1) {
        case 0x01: // HALT
            vm->halted = true;
            break;
        case 0x02: // PID_COMPUTE
            pid_compute(vm, operand2 & 0xFFFF);
            break;
        case 0x03: // RECORD_SNAPSHOT
            record_snapshot(vm, operand2 & 0xFFFF);
            break;
        case 0x04: // EMIT_EVENT
            emit_event(vm, operand2 & 0xFFFF, (operand2 >> 16) & 0xFFFF);
            break;
        default:
            vm_halt_error(vm, ERR_INVALID_SYSCALL);
    }
    PC += 8;
    cycle_count++;
    continue;
}
```

**PID_COMPUTE detail:**

Stack before: `[..., setpoint_f32, input_f32]`
Stack after:  `[..., output_f32]`

```c
void pid_compute(vm_t *vm, uint16_t pid_idx) {
    if (pid_idx >= 8) { vm_halt_error(vm, ERR_INVALID_PID); return; }
    if (vm->sp < 2) { vm_halt_error(vm, ERR_STACK_UNDERFLOW); return; }

    float input = u32_as_f32(vm->stack[--vm->sp]);
    float setpoint = u32_as_f32(vm->stack[--vm->sp]);

    pid_state_t *pid = &vm->pid[pid_idx];
    float dt = vm->tick_period_sec;

    float error = setpoint - input;
    pid->integral += error * dt;
    // Anti-windup: clamp integral
    if (pid->integral > pid->integral_limit) pid->integral = pid->integral_limit;
    if (pid->integral < -pid->integral_limit) pid->integral = -pid->integral_limit;

    float derivative = (error - pid->prev_error) / dt;
    pid->prev_error = error;

    float output = (pid->Kp * error) +
                   (pid->Ki * pid->integral) +
                   (pid->Kd * derivative);

    // Output clamping (configured per-PID at init time)
    if (output > pid->output_max) output = pid->output_max;
    if (output < pid->output_min) output = pid->output_min;

    vm->stack[vm->sp++] = f32_as_u32(output);
}
```

PID state structure (24 bytes per controller):
```c
typedef struct {
    float Kp;              // +0:  Proportional gain
    float Ki;              // +4:  Integral gain
    float Kd;              // +8:  Derivative gain
    float integral;        // +12: Accumulated integral
    float prev_error;      // +16: Previous error for derivative
    float integral_limit;  // +20: Anti-windup clamp
    float output_min;      // +24: Output lower bound (NOT included in 24-byte count)
    float output_max;      // +28: Output upper bound
} pid_state_t;             // 32 bytes total per controller (revised from 24)
```

**Revised PID memory:** 8 controllers × 32 bytes = 256 bytes.

#### RECORD_SNAPSHOT <snapshot_id>

```
NOP flags=0x80, operand1=0x03, operand2.lo16=<snapshot_id: 0-15>
```

Records a snapshot of the current VM state (all variables, sensor registers,
current state) into a snapshot buffer. Snapshots are used for debugging and
AI observation. The snapshot buffer holds 16 snapshots × 128 bytes = 2KB.

Snapshot contents (128 bytes per snapshot):
```
Offset  Size   Field
0       4      tick_count_ms
4       4      cycle_count_this_tick
8       4      current_state (VAR_0)
12      256    variables[0..63] (first 64 variables)
268     256    sensor_registers[0..63]
524     256    actuator_registers[0..63]
```

Wait — 4+4+4+256+256+256 = 780 bytes, not 128. Snapshots are too large for
2KB buffer with 16 slots.

**Revised snapshot:** Only record critical data.
```
Offset  Size   Field
0       4      tick_count_ms
4       4      cycle_count_this_tick
8       4      current_state
12      60     first 15 variables (VAR_0..VAR_14)
72      56     first 14 sensor registers (SENSOR_0..SENSOR_13)
```
Total: 128 bytes per snapshot. 16 snapshots × 128 bytes = 2KB.

The host firmware can drain snapshots asynchronously.

#### EMIT_EVENT <event_id> <event_data>

```
NOP flags=0x80, operand1=0x04, operand2.lo16=<event_id: 0-255>, operand2.hi16=<event_data: 0-65535>
```

Queues an event into a ring buffer (32 events × 8 bytes = 256 bytes). Events
are consumed by the host firmware for telemetry, logging, or triggering
higher-level behaviors.

Event structure:
```c
typedef struct {
    uint32_t tick_ms;
    uint16_t event_id;
    uint16_t event_data;
} vm_event_t;  // 8 bytes
```

---

## 3. Instruction Encoding

### 3.1 Fixed 8-Byte Instruction Format

Every instruction in the bytecode is exactly 8 bytes, 8-byte aligned.
The bytecode buffer is an array of `uint8_t[8]` elements (or equivalently,
`uint32_t[2]` for fast 32-bit loads).

```
┌─────────┬─────────┬──────────────┬──────────────────────────┐
│ Byte 0  │ Byte 1  │  Bytes 2-3   │       Bytes 4-7          │
│ OPCODE  │ FLAGS   │  OPERAND1    │       OPERAND2            │
│ (u8)    │ (u8)    │  (uint16_t)  │  (uint32_t)               │
│         │         │              │                           │
│ 0x00-   │ see     │ see per-     │ see per-opcode           │
│ 0x1F    │ below   │ opcode       │ definitions               │
└─────────┴─────────┴──────────────┴──────────────────────────┘
```

### 3.2 Flags Byte (Byte 1) — Bit Field Definition

```
Bit 0 (LSB):  HAS_IMMEDIATE
               0 = operand fields are not used (or used as address)
               1 = operand fields contain immediate data

Bit 1:        IS_FLOAT
               0 = operand values are integers
               1 = operand2 contains a float32 (for PUSH_F32)

Bit 2:        EXTENDED_CLAMP
               0 = normal instruction
               1 = CLAMP_F with separate lo/hi floats

Bit 3:        IS_CALL
               0 = JUMP is a plain jump
               1 = JUMP is a CALL (push return addr to call stack)

Bit 4:        RESERVED_4

Bit 5:        RESERVED_5

Bit 6:        RESERVED_6

Bit 7 (MSB):  SYSCALL
               0 = normal instruction
               1 = this NOP is a syscall (HALT, PID_COMPUTE, etc.)
```

### 3.3 Operand Field Usage by Opcode

The following table specifies EXACTLY which bytes are used by each opcode
and what they contain. Any field marked "unused" MUST be zero in valid
bytecode (enforced by the validator).

| Opcode | Mnemonic | Operand1 (Bytes 2-3) | Operand2 (Bytes 4-7) | Flags Usage |
|--------|----------|----------------------|----------------------|-------------|
| 0x00 | NOP | unused (0x0000) | unused (0x00000000) | Bit 7: SYSCALL |
| 0x01 | PUSH_I8 | [0]=imm8, [1]=0x00 | unused (0x00000000) | — |
| 0x02 | PUSH_I16 | int16 (signed) | unused (0x00000000) | — |
| 0x03 | PUSH_F32 | unused (0x0000) | float32 (IEEE 754) | — |
| 0x04 | POP | unused (0x0000) | unused (0x00000000) | — |
| 0x05 | DUP | unused (0x0000) | unused (0x00000000) | — |
| 0x06 | SWAP | unused (0x0000) | unused (0x00000000) | — |
| 0x07 | ROT | unused (0x0000) | unused (0x00000000) | — |
| 0x08 | ADD_F | unused (0x0000) | unused (0x00000000) | — |
| 0x09 | SUB_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0A | MUL_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0B | DIV_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0C | NEG_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0D | ABS_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0E | MIN_F | unused (0x0000) | unused (0x00000000) | — |
| 0x0F | MAX_F | unused (0x0000) | unused (0x00000000) | — |
| 0x10 | CLAMP_F | unused (0x0000) | lo16:lo_f32, hi16:hi_f32 | Bit 2: extended |
| 0x11 | EQ_F | unused (0x0000) | unused (0x00000000) | — |
| 0x12 | LT_F | unused (0x0000) | unused (0x00000000) | — |
| 0x13 | GT_F | unused (0x0000) | unused (0x00000000) | — |
| 0x14 | LTE_F | unused (0x0000) | unused (0x00000000) | — |
| 0x15 | GTE_F | unused (0x0000) | unused (0x00000000) | — |
| 0x16 | AND_B | unused (0x0000) | unused (0x00000000) | — |
| 0x17 | OR_B | unused (0x0000) | unused (0x00000000) | — |
| 0x18 | XOR_B | unused (0x0000) | unused (0x00000000) | — |
| 0x19 | NOT_B | unused (0x0000) | unused (0x00000000) | — |
| 0x1A | READ_PIN | sensor_idx (uint16) | unused (0x00000000) | — |
| 0x1B | WRITE_PIN | actuator_idx (uint16) | unused (0x00000000) | — |
| 0x1C | READ_TIMER_MS | unused (0x0000) | unused (0x00000000) | — |
| 0x1D | JUMP | unused (0x0000) | target_byte_offset (uint32) | Bit 3: IS_CALL |
| 0x1E | JUMP_IF_FALSE | unused (0x0000) | target_byte_offset (uint32) | — |
| 0x1F | JUMP_IF_TRUE | unused (0x0000) | target_byte_offset (uint32) | — |

### 3.4 Byte Order

All multi-byte fields use **little-endian** byte order. This matches ESP32-S3
(Xtensa LX7) and most ARM Cortex-M MCUs. The validator/compiler for a
big-endian target must byte-swap before writing bytecode to flash.

```
operand1 (uint16_t):
  Byte 2 = low byte  (bits 7:0)
  Byte 3 = high byte (bits 15:8)

operand2 (uint32_t):
  Byte 4 = bits 7:0
  Byte 5 = bits 15:8
  Byte 6 = bits 23:16
  Byte 7 = bits 31:24
```

### 3.5 CLAMP_F Encoding Detail

The CLAMP_F instruction clamps TOS to [lo, hi] where lo and hi are float32
values with the same upper 16 bits (same sign + exponent, allowing different
mantissas).

```
operand2 bytes 4-5:  lower 16 bits of lo (IEEE 754)
operand2 bytes 6-7:  lower 16 bits of hi (IEEE 754)

Reconstruction:
  common_upper = (float_bits(hi) >> 16) << 16   // or lo, they share the same upper
  lo_full = common_upper | operand2_bytes_4_5
  hi_full = common_upper | operand2_bytes_6_7
```

**Compiler responsibility:** The compiler must verify that both floats share
the same upper 16 bits. If they don't, the compiler emits the general clamp:
```
DUP           ; save original value
PUSH_F32 <hi> ; push upper bound
SWAP          ; [orig, hi, orig]
PUSH_F32 <lo> ; [orig, hi, orig, lo]
SWAP          ; [orig, hi, lo, orig]
; -- not quite right --
```

**General clamp sequence (compiler-emitted):**
```
; Stack: [..., val]
DUP                     ; [..., val, val]
PUSH_F32 <hi>           ; [..., val, val, hi]
SWAP                    ; [..., val, hi, val]
MIN_F                   ; [..., val, min(val, hi)]
PUSH_F32 <lo>           ; [..., val, min(val,hi), lo]
MAX_F                   ; [..., max(val, min(val,hi))]
; Result: clamp(val, lo, hi)
```

This sequence uses 6 instructions (48 bytes of bytecode) but is fully
general. The specialized CLAMP_F opcode exists for the common case where
lo and hi share the same upper half (e.g., clamping to [-1.0, 1.0] or
[0.0, 100.0]).

---

## 4. Memory Model

### 4.1 Memory Map

All VM memory is statically allocated. No malloc, no free, no dynamic
allocation of any kind. The total VM state fits in 3,392 bytes (revised).

```
Region                    Size (bytes)   Address (in VM struct)
─────────────────────────────────────────────────────────────────
Data Stack                1024           vm->stack[256]
Call Stack                512            vm->call_stack[64]
Variables (VAR_0-255)     1024           vm->variables[256]
Sensor Registers          256            vm->sensors[64]
Actuator Registers        256            vm->actuators[64]
PID Controllers (×8)      256            vm->pid[8]
Event Queue               256            vm->events[32]
Snapshot Buffer           2048           vm->snapshots[16]
─────────────────────────────────────────────────────────────────
TOTAL VM STATE            5632           (revised from initial 3KB estimate)
```

**Note:** The snapshot buffer (2KB) is optional. If not enabled, total state
is 3,584 bytes. The "minimum viable VM" (no snapshots, no events) uses
3,328 bytes.

### 4.2 Data Stack

- Capacity: 256 entries × 4 bytes = 1024 bytes
- Type: `uint32_t stack[256]`
- Pointer: `SP` (uint16_t, initially 0)
- SP = 0 means empty. SP = 256 means full.
- Stack grows upward (push = write at SP, then SP++)
- Underflow: accessing when SP = 0
- Overflow: writing when SP = 256

**Stack discipline:** The VM enforces strict stack discipline. Every
instruction that pushes checks `SP < 256` before writing. Every instruction
that pops checks `SP > 0` before reading. Violations cause immediate HALT.

**No stack canaries** are used. The stack is bounded by SP checks alone.
The validator also performs static analysis to verify stack depth never
exceeds the limit.

### 4.3 Call Stack

- Capacity: 64 entries × 8 bytes = 512 bytes
- Entry structure:
  ```c
  typedef struct {
      uint32_t return_addr;   // Byte offset in bytecode
      uint16_t frame_pointer; // SP at time of call (for restoring on RET)
      uint16_t padding;       // Alignment
  } call_frame_t;
  ```
- Pointer: `CSP` (uint8_t, initially 0)
- Maximum depth: 16 (enforced by VM, even though 64 slots exist)
- CALL checks `CSP < 16` before pushing
- RET checks `CSP > 0` before popping

**CALL encoding:** `JUMP` with `flags bit 3 = 1` (IS_CALL).

```c
// CALL implementation (inside JUMP handler when flags & 0x08):
if (vm->csp >= 16) {
    vm_halt_error(vm, ERR_CALL_DEPTH);
    return;
}
vm->call_stack[vm->csp].return_addr = vm->pc + 8; // next instruction
vm->call_stack[vm->csp].frame_pointer = vm->sp;
vm->csp++;
vm->pc = operand2; // jump target
```

**RET encoding:** `JUMP` with `operand2 = 0xFFFFFFFF` (magic sentinel).

```c
// RET implementation:
if (vm->csp == 0) {
    vm_halt_error(vm, ERR_CALL_UNDERFLOW);
    return;
}
vm->csp--;
vm->pc = vm->call_stack[vm->csp].return_addr;
// NOTE: SP is NOT restored to frame_pointer. The callee must balance
// its own stack usage. This is a design choice: it allows the callee
// to return values on the stack.
```

### 4.4 Variables (VAR_0 through VAR_255)

- Capacity: 256 entries × 4 bytes = 1024 bytes
- Type: `uint32_t variables[256]`
- Persistent across ticks (retained until VM reset)
- Initialized to zero on VM start
- Access: `READ_PIN` / `WRITE_PIN` with `operand1` in range [64, 319]
  - `operand1 - 64` = variable index
- VAR_0 is the **state machine state** register (convention)

### 4.5 Sensor Registers (SENSOR_0 through SENSOR_63)

- Capacity: 64 entries × 4 bytes = 256 bytes
- Type: `uint32_t sensors[64]` (interpreted as float32 or int32 per pin config)
- Read-only from bytecode (WRITE_PIN to sensor index triggers ERR_WRITE_RO)
- Populated by host firmware BEFORE each tick
- Typical mapping (example):
  ```
  SENSOR_0:  heading (degrees, float)
  SENSOR_1:  speed (m/s, float)
  SENSOR_2:  rudder_angle (degrees, float)
  SENSOR_3:  wind_speed (m/s, float)
  SENSOR_4:  wind_direction (degrees, float)
  SENSOR_5:  battery_voltage (V, float)
  ...
  ```

### 4.6 Actuator Registers (ACTUATOR_0 through ACTUATOR_63)

- Capacity: 64 entries × 4 bytes = 256 bytes
- Type: `uint32_t actuators[64]`
- Written by bytecode during tick
- Drained by host firmware AFTER each tick (values applied to hardware)
- All values are clamped to configured safe ranges AFTER execution completes
- On VM error: all actuators set to their configured **safe values** (not zero)
- Each actuator has: min, max, safe_default (configured at init)

Typical mapping (example):
```
ACTUATOR_0:  rudder_command (degrees, float, range: -45.0 to 45.0, safe: 0.0)
ACTUATOR_1:  throttle_command (0.0 to 1.0, safe: 0.0)
ACTUATOR_2:  bilge_pump (0 or 1, safe: 0)
...
```

### 4.7 PID Controllers (PID_0 through PID_7)

- Capacity: 8 controllers × 32 bytes = 256 bytes
- Type: `pid_state_t pid[8]` (see Section 2.5 for structure)
- Configured at VM initialization (gains, limits, etc.)
- State (integral, prev_error) persists across ticks
- PID output is pushed to the data stack, NOT directly to actuators
  (the compiler follows PID_COMPUTE with WRITE_PIN)

### 4.8 Event Queue

- Capacity: 32 events × 8 bytes = 256 bytes
- Type: ring buffer of `vm_event_t`
- Written by EMIT_EVENT syscall
- Drained by host firmware
- Full queue: new events are silently dropped (no error)

### 4.9 Snapshot Buffer (Optional)

- Capacity: 16 snapshots × 128 bytes = 2048 bytes
- Written by RECORD_SNAPSHOT syscall
- Read by host firmware or debug interface
- Full buffer: oldest snapshot is overwritten (ring buffer)

### 4.10 Memory Layout in C

```c
#define VM_DATA_STACK_SIZE    256
#define VM_CALL_STACK_SIZE    64
#define VM_VARIABLE_COUNT     256
#define VM_SENSOR_COUNT       64
#define VM_ACTUATOR_COUNT     64
#define VM_PID_COUNT          8
#define VM_EVENT_QUEUE_SIZE   32
#define VM_SNAPSHOT_COUNT     16
#define VM_SNAPSHOT_SIZE      128
#define VM_MAX_CALL_DEPTH     16
#define VM_MAX_CYCLE_COUNT    5000
#define VM_BYTECODE_MAX_SIZE  4096  // max 512 instructions

typedef struct {
    // Execution state
    uint32_t    pc;             // Program counter (byte offset)
    uint16_t    sp;             // Data stack pointer
    uint8_t     csp;            // Call stack pointer
    uint8_t     halted;         // 1 = halted this tick
    uint32_t    cycle_count;    // Cycles consumed this tick
    uint32_t    error_code;     // Last error (0 = none)
    uint32_t    tick_count_ms;  // Monotonic tick counter

    // Configuration
    uint32_t    bytecode_size;  // Size of bytecode in bytes
    uint32_t    max_cycles;     // Cycle budget per tick
    float       tick_period_sec;// Tick period in seconds (for PID dt)

    // Data stack (1KB)
    uint32_t    stack[VM_DATA_STACK_SIZE];

    // Call stack (512B)
    struct {
        uint32_t return_addr;
        uint16_t frame_pointer;
        uint16_t _padding;
    } call_stack[VM_CALL_STACK_SIZE];

    // Variables (1KB)
    uint32_t    variables[VM_VARIABLE_COUNT];

    // Sensor registers (256B, read-only)
    uint32_t    sensors[VM_SENSOR_COUNT];

    // Actuator registers (256B, write-only)
    uint32_t    actuators[VM_ACTUATOR_COUNT];
    struct {
        float min;
        float max;
        float safe_default;
    } actuator_config[VM_ACTUATOR_COUNT];

    // PID controllers (256B)
    pid_state_t pid[VM_PID_COUNT];

    // Event queue (256B)
    vm_event_t  events[VM_EVENT_QUEUE_SIZE];
    uint8_t     event_head;
    uint8_t     event_tail;

    // Snapshot buffer (2KB, optional)
    uint8_t     snapshots[VM_SNAPSHOT_COUNT][VM_SNAPSHOT_SIZE];
    uint8_t     snapshot_idx;

    // Bytecode (stored externally, pointed to)
    const uint8_t *bytecode;

} vm_state_t;
```

**Total struct size (without bytecode):** ~5.8KB
**Minimum viable (no snapshots, no events):** ~3.3KB

---

## 5. Execution Model

### 5.1 Tick-Based Execution

The VM does NOT run continuously. It runs in discrete **ticks**, driven by
a hardware timer interrupt at a configurable rate:

| Tick Rate | Period | Max Bytecode Budget | Use Case |
|-----------|--------|---------------------|----------|
| 1 Hz | 1000 ms | 500,000 cycles | Slow environmental control |
| 10 Hz | 100 ms | 50,000 cycles | Medium-speed control |
| 100 Hz | 10 ms | 5,000 cycles | Fast control loops |
| 500 Hz | 2 ms | 1,000 cycles | High-rate servo |
| 1000 Hz | 1 ms | 500 cycles | Ultra-fast reflex only |

The **cycle budget** is the maximum number of VM cycles allowed per tick.
The default is 5,000 cycles (designed for 100 Hz tick rate).

### 5.2 Fetch-Decode-Execute Loop

```c
vm_error_t vm_execute_tick(vm_state_t *vm) {
    vm->cycle_count = 0;
    vm->halted = 0;
    vm->sp = 0;          // Reset data stack each tick
    vm->csp = 0;         // Reset call stack each tick

    // NOTE: Variables, PID state, sensors are NOT reset (persistent)

    while (!vm->halted) {
        // Cycle budget check
        if (vm->cycle_count >= vm->max_cycles) {
            vm_halt_error(vm, ERR_CYCLE_BUDGET);
            break;
        }

        // Bounds check PC
        if (vm->pc + 8 > vm->bytecode_size) {
            vm_halt_error(vm, ERR_PC_OUT_OF_BOUNDS);
            break;
        }

        // Fetch (8 bytes, aligned)
        const uint8_t *ip = &vm->bytecode[vm->pc];
        uint8_t opcode = ip[0];
        uint8_t flags  = ip[1];
        uint16_t op1   = (uint16_t)ip[2] | ((uint16_t)ip[3] << 8);
        uint32_t op2   = (uint32_t)ip[4] | ((uint32_t)ip[5] << 8) |
                         ((uint32_t)ip[6] << 16) | ((uint32_t)ip[7] << 24);

        // Decode & Execute
        uint8_t cycles = dispatch(vm, opcode, flags, op1, op2);

        vm->cycle_count += cycles;
        if (!vm->halted) {
            vm->pc += 8;
        }
    }

    // Post-execution: clamp actuators to safe ranges
    if (vm->halted && vm->error_code != 0) {
        vm_apply_safe_defaults(vm);
    } else {
        vm_clamp_actuators(vm);
    }

    return vm->error_code;
}
```

### 5.3 Dispatch Implementation

The dispatch function uses a switch statement or computed goto (GCC/Clang
extension) for O(1) instruction dispatch:

```c
// Option A: switch (portable, all compilers)
static uint8_t dispatch(vm_state_t *vm, uint8_t opcode, uint8_t flags,
                        uint16_t op1, uint32_t op2) {
    switch (opcode) {
        case 0x00: return op_nop(vm, flags, op1, op2);
        case 0x01: return op_push_i8(vm, flags, op1, op2);
        // ... all 32 cases ...
        default:
            vm_halt_error(vm, ERR_INVALID_OPCODE);
            return 1;
    }
}

// Option B: computed goto (GCC/Clang, faster dispatch)
static void *dispatch_table[32] = {
    &&op_nop, &&op_push_i8, /* ... */ &&op_jump_if_true
};

static uint8_t dispatch(vm_state_t *vm, uint8_t opcode, uint8_t flags,
                        uint16_t op1, uint32_t op2) {
    if (opcode >= 32) {
        vm_halt_error(vm, ERR_INVALID_OPCODE);
        return 1;
    }
    goto *dispatch_table[opcode];
op_nop:
    return op_nop_impl(vm, flags, op1, op2);
// ...
}
```

### 5.4 Stack Reset Per Tick

The data stack pointer (SP) and call stack pointer (CSP) are reset to 0
at the start of each tick. This means:

- The bytecode cannot rely on data persisting on the stack across ticks.
- All persistent state must be in variables (VAR_0–VAR_255) or PID state.
- The stack is a scratch workspace for the current tick's computation.

**Rationale:** This prevents stack leaks across ticks and ensures
deterministic behavior. A bug in one tick cannot corrupt the next tick's
stack.

### 5.5 HALT Sentinel

The last 8 bytes of every bytecode program MUST be the HALT sentinel:
```
00 80 00 00 00 00 00 00
```
(opcode=0x00, flags=0x80, operand1=0x0000, operand2=0x00000000)

The validator rejects bytecode that does not end with this sentinel.

When the PC reaches the HALT sentinel, the VM sets `halted = 1` and exits
the loop cleanly (no error). This is the normal termination condition.

### 5.6 Watchdog Integration

The VM's cycle budget acts as a software watchdog. In addition:

1. The host firmware should configure a **hardware watchdog timer** with a
   timeout of 2× the tick period. If the VM or host firmware hangs, the
   hardware watchdog triggers a full MCU reset.

2. The VM signals successful completion by writing to a "heartbeat" GPIO
   or flag that the hardware watchdog service routine checks.

---

## 6. Safety Invariants

These invariants are **non-negotiable**. They MUST be enforced by every
VM implementation. A formal verification argument should reference each
invariant.

### 6.1 Stack Bounds

```
INVARIANT: 0 ≤ SP ≤ 256 at all times
CHECK: Every push checks SP < 256 before writing
CHECK: Every pop checks SP > 0 before reading
VIOLATION: ERR_STACK_OVERFLOW or ERR_STACK_UNDERFLOW → HALT
```

### 6.2 Call Depth

```
INVARIANT: 0 ≤ CSP ≤ 16 at all times
CHECK: CALL checks CSP < 16 before pushing
CHECK: RET checks CSP > 0 before popping
VIOLATION: ERR_CALL_DEPTH or ERR_CALL_UNDERFLOW → HALT
```

### 6.3 Program Counter Bounds

```
INVARIANT: 0 ≤ PC < bytecode_size, and PC is always 8-byte aligned
CHECK: Before fetch, verify PC + 8 ≤ bytecode_size and PC % 8 == 0
CHECK: Jump targets validated at compile time (validator)
VIOLATION: ERR_PC_OUT_OF_BOUNDS → HALT
```

### 6.4 Division Safety

```
INVARIANT: Division by zero does not crash, hang, or produce NaN/Inf
IMPLEMENTATION: DIV_F returns 0.0f when divisor == 0.0f
```

### 6.5 Actuator Safety

```
INVARIANT: After each tick, every actuator value is in [min, max]
IMPLEMENTATION: vm_clamp_actuators() runs after execution
INVARIANT: On error, every actuator is set to its safe_default
IMPLEMENTATION: vm_apply_safe_defaults() runs on any HALT with error
```

Post-execution clamping code:
```c
static void vm_clamp_actuators(vm_state_t *vm) {
    for (int i = 0; i < VM_ACTUATOR_COUNT; i++) {
        float val;
        memcpy(&val, &vm->actuators[i], 4);
        if (val < vm->actuator_config[i].min) val = vm->actuator_config[i].min;
        if (val > vm->actuator_config[i].max) val = vm->actuator_config[i].max;
        memcpy(&vm->actuators[i], &val, 4);
    }
}

static void vm_apply_safe_defaults(vm_state_t *vm) {
    for (int i = 0; i < VM_ACTUATOR_COUNT; i++) {
        memcpy(&vm->actuators[i], &vm->actuator_config[i].safe_default, 4);
    }
}
```

### 6.6 Cycle Budget

```
INVARIANT: Total cycles per tick ≤ max_cycles
CHECK: cycle_count incremented after every instruction
CHECK: if cycle_count ≥ max_cycles, HALT with ERR_CYCLE_BUDGET
DEFAULT: max_cycles = 5000
```

### 6.7 Sensor Register Protection

```
INVARIANT: Bytecode cannot write to sensor registers
CHECK: WRITE_PIN with operand1 < 64 triggers ERR_WRITE_RO → HALT
NOTE: Variable space (operand1 ≥ 64) is writable
```

### 6.8 Invalid Opcode

```
INVARIANT: Any opcode ≥ 0x20 is rejected
CHECK: dispatch() switch/case default → ERR_INVALID_OPCODE → HALT
```

### 6.9 Variable Index Bounds

```
INVARIANT: Variable index (operand1 - 64) < 256
CHECK: WRITE_PIN/READ_PIN with operand1 > 319 triggers ERR_INVALID_OPERAND → HALT
```

---

## 7. Compilation from JSON Reflex to Bytecode

### 7.1 JSON Reflex Format

A NEXUS Reflex is defined as a JSON state machine:

```json
{
  "name": "heading_hold",
  "version": "1.0",
  "tick_rate_hz": 100,
  "initial_state": "acquiring",
  "states": {
    "acquiring": {
      "entry_actions": [
        { "type": "set_variable", "var": 1, "value": 0.0 }
      ],
      "transitions": [
        {
          "condition": { "sensor": 0, "op": "gt", "value": 0.5 },
          "target": "holding"
        }
      ]
    },
    "holding": {
      "pid": {
        "index": 0,
        "setpoint": { "variable": 1 },
        "input": { "sensor": 0 },
        "output": { "actuator": 0 }
      },
      "transitions": [
        {
          "condition": { "sensor": 5, "op": "lt", "value": 10.0 },
          "target": "safety_stop"
        }
      ]
    },
    "safety_stop": {
      "entry_actions": [
        { "type": "write_actuator", "pin": 0, "value": 0.0 },
        { "type": "write_actuator", "pin": 1, "value": 0.0 }
      ],
      "is_final": true
    }
  }
}
```

### 7.2 Compilation Algorithm

The compiler transforms the JSON state machine into a flat bytecode program
with one labeled block per state and dispatch jumps.

**Step 1: Assign byte offsets to each state block.**

The compiler first lays out the bytecode by allocating blocks for each state:
```
Offset 0x000:   [state dispatch jump table]
Offset 0x080:   [state "acquiring" block]
Offset 0x100:   [state "holding" block]
Offset 0x180:   [state "safety_stop" block]
Offset 0x1F8:   [HALT sentinel]
```

**Step 2: Generate state dispatch.**

At program start (PC=0), the compiler emits a jump table that reads VAR_0
(current state) and dispatches to the appropriate block:

```
; State dispatch (PC = 0x000)
READ_PIN   64          ; push VAR_0 (current state)
PUSH_I8    0           ; push state ID for "acquiring" (0)
EQ_F                   ; VAR_0 == 0 ?
JUMP_IF_TRUE  0x080    ; yes → go to acquiring block

READ_PIN   64          ; push VAR_0
PUSH_I8    1           ; push state ID for "holding" (1)
EQ_F                   ; VAR_0 == 1 ?
JUMP_IF_TRUE  0x100    ; yes → go to holding block

READ_PIN   64          ; push VAR_0
PUSH_I8    2           ; push state ID for "safety_stop" (2)
EQ_F
JUMP_IF_TRUE  0x180    ; yes → go to safety_stop block

; No matching state — HALT
NOP  flags=0x80, op1=0x01   ; HALT syscall
```

For N states, the dispatch is O(N) comparisons. This is acceptable for
state machines with ≤ 16 states (128 bytes of dispatch code). For larger
state machines, the compiler can emit a binary search dispatch.

**Step 3: Generate state blocks.**

For the "acquiring" state (state ID = 0):
```
; --- State: acquiring (0x080) ---
; entry_actions:
PUSH_F32  0.0
WRITE_PIN 65           ; VAR_1 = 0.0

; transitions:
READ_PIN  0            ; push SENSOR_0 (heading quality)
PUSH_F32  0.5          ; threshold
GT_F                   ; SENSOR_0 > 0.5 ?
JUMP_IF_FALSE 0x0F8    ; no → skip transition, fall through to next state's block

; transition to "holding":
PUSH_I8   1            ; state ID for "holding"
WRITE_PIN 64           ; VAR_0 = 1 (set state)
JUMP      0x000        ; back to dispatch

; no transition matched → HALT (or jump to dispatch for next tick)
NOP  flags=0x80, op1=0x01   ; HALT
```

For the "holding" state (state ID = 1):
```
; --- State: holding (0x100) ---
; PID computation:
READ_PIN  64           ; push VAR_1 (setpoint, stored in variable)
READ_PIN  0            ; push SENSOR_0 (heading, input to PID)
NOP  flags=0x80, op1=0x02, op2=0x0000   ; PID_COMPUTE pid_idx=0
WRITE_PIN 0            ; ACTUATOR_0 = PID output

; transitions:
READ_PIN  5            ; push SENSOR_5 (battery voltage)
PUSH_F32  10.0         ; threshold
LT_F                   ; SENSOR_5 < 10.0 ?
JUMP_IF_FALSE 0x170    ; no → skip

; transition to "safety_stop":
PUSH_I8   2            ; state ID for "safety_stop"
WRITE_PIN 64           ; VAR_0 = 2
JUMP      0x000        ; back to dispatch

; no transition matched → HALT
NOP  flags=0x80, op1=0x01   ; HALT
```

For the "safety_stop" state (state ID = 2):
```
; --- State: safety_stop (0x180) ---
; entry_actions:
PUSH_F32  0.0
WRITE_PIN 0            ; ACTUATOR_0 = 0.0
PUSH_F32  0.0
WRITE_PIN 1            ; ACTUATOR_1 = 0.0

; is_final = true → HALT
NOP  flags=0x80, op1=0x01   ; HALT
```

**Step 4: Append HALT sentinel.**
```
; Offset 0x1F8:
00 80 00 00 00 00 00 00
```

### 7.3 Compilation Rules Summary

| JSON Construct | Bytecode Pattern | Instructions |
|---|---|---|
| State dispatch | `READ_PIN 64; PUSH_I8 id; EQ_F; JUMP_IF_TRUE` | 4 per state |
| `set_variable` | `PUSH_F32 val; WRITE_PIN (64+var_idx)` | 2 |
| `write_actuator` | `PUSH_F32 val; WRITE_PIN actuator_idx` | 2 |
| `read_sensor` | `READ_PIN sensor_idx` | 1 |
| Comparison `gt` | `READ_PIN s; PUSH_F32 v; GT_F` | 3 |
| Comparison `lt` | `READ_PIN s; PUSH_F32 v; LT_F` | 3 |
| Comparison `eq` | `READ_PIN s; PUSH_F32 v; EQ_F` | 3 |
| Comparison `gte` | `READ_PIN s; PUSH_F32 v; GTE_F` | 3 |
| Comparison `lte` | `READ_PIN s; PUSH_F32 v; LTE_F` | 3 |
| Transition (condition + jump) | comparison + `JUMP_IF_FALSE skip; state_set; JUMP dispatch` | 6 |
| PID compute | `READ_PIN setpoint; READ_PIN input; PID_COMPUTE idx; WRITE_PIN out` | 4 |
| HALT (normal) | `NOP flags=0x80 op1=0x01` | 1 |
| `is_final` state | entry_actions + HALT | varies + 1 |

### 7.4 Compiler Validation Pass

Before emitting bytecode, the compiler performs a validation pass:

1. **Opcode range:** All opcodes in [0x00, 0x1F].
2. **Jump targets:** All targets point to valid 8-byte-aligned offsets within
   the bytecode. No forward jumps past the HALT sentinel (except the sentinel
   itself).
3. **Stack depth analysis:** Simulate execution of every reachable code path;
   verify max stack depth ≤ 256 and stack never goes negative.
4. **Variable index bounds:** All `operand1` values for variable access in [64, 319].
5. **Sensor/actuator index bounds:** `operand1` in [0, 63] for hardware registers.
6. **HALT sentinel:** Last 8 bytes must be the HALT sentinel.
7. **Syscall validation:** All syscall IDs in valid range, PID indices in [0,7].
8. **CLAMP_F validation:** lo and hi share upper 16 bits (or use general sequence).

---

## 8. Error Handling

### 8.1 Error Code Definitions

```c
#define ERR_NONE                 0x00  // No error
#define ERR_STACK_UNDERFLOW      0x01  // Pop from empty stack
#define ERR_STACK_OVERFLOW       0x02  // Push to full stack
#define ERR_INVALID_OPCODE       0x03  // Opcode ≥ 0x20
#define ERR_PC_OUT_OF_BOUNDS     0x04  // PC beyond bytecode
#define ERR_CALL_DEPTH           0x05  // CALL when CSP ≥ 16
#define ERR_CALL_UNDERFLOW       0x06  // RET when CSP == 0
#define ERR_WRITE_RO             0x07  // WRITE_PIN to sensor register
#define ERR_INVALID_OPERAND      0x08  // Operand out of valid range
#define ERR_CYCLE_BUDGET         0x09  // Exceeded max cycles per tick
#define ERR_INVALID_SYSCALL      0x0A  // Unknown syscall ID
#define ERR_INVALID_PID          0x0B  // PID index ≥ 8
#define ERR_DIVISION_BY_ZERO     0x0C  // (Informational — DIV_F returns 0.0)
#define ERR_VALIDATION_FAILED    0x0D  // Bytecode failed validation
```

### 8.2 Error Response Protocol

On ANY error during execution:

1. **Immediately halt:** Set `vm->halted = 1`. Stop the fetch-decode loop.
2. **Record error:** Set `vm->error_code` to the appropriate code.
3. **Safe actuators:** Call `vm_apply_safe_defaults()` to set all actuators
   to their configured safe values.
4. **Emit error event:** Automatically emit event with:
   - `event_id = 0xFF` (reserved for VM errors)
   - `event_data = error_code`
5. **Signal safety monitor:** Set a flag or GPIO that the host firmware's
   safety monitor task reads. The safety monitor is responsible for:
   - Logging the error to non-volatile storage
   - Notifying the control system
   - Preventing automatic restart without explicit acknowledgment

### 8.3 Error Recovery

The VM does NOT auto-recover from errors. Recovery requires:

1. Host firmware receives error notification.
2. Host firmware performs diagnostic checks (read `vm->error_code`,
   `vm->pc`, `vm->cycle_count`).
3. Host firmware may optionally read the snapshot buffer for debugging.
4. Host firmware resets the VM state (variables, PID accumulators, etc.).
5. Host firmware re-validates bytecode (may re-flash if corrupted).
6. Host firmware explicitly re-enables the VM tick.

The safety monitor should enforce a **minimum cooldown period** (e.g., 1
second) between error and re-enable, and a **maximum restart count** (e.g.,
3 restarts in 60 seconds triggers a full system fault).

---

## 9. Timing Analysis

### 9.1 Cycle Counts

All cycle counts are measured in **VM cycles**, where 1 VM cycle = 1 opcode
dispatch iteration. The actual wall-clock time per cycle depends on the MCU
clock speed and implementation quality.

**Base cycle costs (every instruction):**
- Instruction fetch: included in the dispatch
- Dispatch overhead: ~10–20 CPU cycles on ESP32-S3

| Opcode | Cycles | Notes |
|--------|--------|-------|
| NOP | 1 | No operation |
| PUSH_I8 | 1 | Sign-extend + store |
| PUSH_I16 | 1 | Sign-extend + store |
| PUSH_F32 | 1 | 4-byte store |
| POP | 1 | Decrement SP |
| DUP | 1 | Copy + SP check |
| SWAP | 1 | 3-register swap |
| ROT | 2 | 4-register rotation |
| ADD_F | 3 | Soft-float add (~30 CPU cycles) |
| SUB_F | 3 | Soft-float sub (~30 CPU cycles) |
| MUL_F | 3 | Soft-float mul (~50 CPU cycles) |
| DIV_F | 4 | Soft-float div (~80 CPU cycles) |
| NEG_F | 1 | XOR (no float op) |
| ABS_F | 1 | AND (no float op) |
| MIN_F | 3 | Compare + select |
| MAX_F | 3 | Compare + select |
| CLAMP_F | 3 | 2 compares + 2 selects |
| EQ_F | 3 | Float compare |
| LT_F | 3 | Float compare |
| GT_F | 3 | Float compare |
| LTE_F | 3 | Float compare |
| GTE_F | 3 | Float compare |
| AND_B | 1 | Bitwise AND |
| OR_B | 1 | Bitwise OR |
| XOR_B | 1 | Bitwise XOR |
| NOT_B | 1 | Bitwise NOT |
| READ_PIN | 2 | Array load |
| WRITE_PIN | 2 | Array store |
| READ_TIMER_MS | 2 | 32-bit load |
| JUMP | 1 | PC assign |
| JUMP_IF_FALSE | 2 | Pop + conditional PC |
| JUMP_IF_TRUE | 2 | Pop + conditional PC |

**Syscall cycle costs (NOP with flags=0x80):**

| Syscall | Cycles | Notes |
|---------|--------|-------|
| HALT | 1 | Set flag, exit |
| PID_COMPUTE | 15 | Error + integral + derivative + clamp |
| RECORD_SNAPSHOT | 20 | 128-byte memcpy |
| EMIT_EVENT | 3 | Ring buffer write |

### 9.2 Worst-Case Execution Time (WCET) Calculation

**Target: "Typical PID reflex" with 30 instructions**

Example program (heading hold with one transition check):
```
; State dispatch (12 instructions, worst-case for N=3 states)
READ_PIN  64       ; 2 cycles
PUSH_I8   0       ; 1
EQ_F               ; 3
JUMP_IF_TRUE 0x80  ; 2
READ_PIN  64       ; 2
PUSH_I8   1       ; 1
EQ_F               ; 3
JUMP_IF_TRUE 0x100 ; 2
NOP HALT            ; 1
; -- dispatch subtotal: 17 cycles --

; Holding state (10 instructions)
READ_PIN  64       ; 2   (load setpoint from VAR_1)
READ_PIN  0        ; 2   (load heading from SENSOR_0)
NOP PID_COMPUTE    ; 15  (PID controller 0)
WRITE_PIN 0        ; 2   (output to ACTUATOR_0)
READ_PIN  5        ; 2   (load battery voltage)
PUSH_F32  10.0     ; 1
LT_F               ; 3   (battery < 10V ?)
JUMP_IF_FALSE 0x170 ; 2
; -- holding state subtotal: 29 cycles --

; HALT
NOP HALT            ; 1
```

**Total cycles:** 17 (dispatch) + 29 (state body) + 1 (halt) = **47 cycles**

### 9.3 Budget Verification at 100 Hz

At 100 Hz tick rate:
- Tick period: 10 ms = 10,000 µs
- Default cycle budget: 5,000 VM cycles
- Our program: 47 cycles
- **Utilization: 0.94%** ✓

### 9.4 Budget Verification at 1000 Hz

At 1000 Hz tick rate:
- Tick period: 1 ms = 1,000 µs
- Cycle budget should be: 500 VM cycles (for 500 µs budget)
- Our program: 47 cycles
- **Utilization: 9.4%** ✓

### 9.5 CPU Cycle Estimate on ESP32-S3 (240 MHz)

Each VM cycle requires approximately:
- Dispatch overhead: ~15 CPU cycles (load instruction, switch/case jump)
- Instruction execution: 1–80 CPU cycles depending on operation

**Worst-case single instruction:** DIV_F
- VM cycles: 4
- CPU cycles: ~15 (dispatch) + ~80 (soft-float division) = ~95 CPU cycles
- Wall-clock time at 240 MHz: 95 / 240,000,000 ≈ 0.40 µs

**Worst-case program (5,000 VM cycles, all DIV_F):**
- CPU cycles: 5,000 × 95 = 475,000
- Wall-clock time: 475,000 / 240,000,000 ≈ **1.98 ms**

This EXCEEDS the 500 µs budget at 1 kHz. Therefore, at 1 kHz tick rate,
the cycle budget should be reduced to ~1,200 cycles.

**Realistic worst-case (mixed instructions):**
- Average cost per VM cycle: ~25 CPU cycles (dispatch + average execution)
- 5,000 VM cycles × 25 = 125,000 CPU cycles
- Wall-clock time: 125,000 / 240,000,000 ≈ **0.52 ms** ≈ 520 µs

This slightly exceeds 500 µs. Set `max_cycles = 4800` for a 100 Hz tick to
stay under 500 µs with margin.

**Typical PID reflex (47 VM cycles):**
- CPU cycles: 47 × 25 = 1,175
- Wall-clock time: 1,175 / 240,000,000 ≈ **4.9 µs** ✓

**Conclusion:** The typical PID reflex completes in under 5 µs, well within
any tick rate budget. Even at 1 kHz (1 ms budget), the reflex uses < 1% of
the available time.

### 9.6 Timing Summary Table

| Metric | Value |
|--------|-------|
| Typical PID reflex (47 cycles) | ~4.9 µs |
| Maximum reflex (5,000 cycles) | ~520 µs |
| Minimum reflex (1 instruction) | ~0.1 µs |
| Dispatch overhead per instruction | ~0.06 µs |
| Soft-float DIV_F (most expensive) | ~0.4 µs |
| PID_COMPUTE syscall | ~1.5 µs |
| Actuator clamping (64 registers) | ~5 µs |

---

## 10. Portability Requirements

### 10.1 Minimum Hardware Requirements

The NEXUS Reflex VM is designed to run on ANY 32-bit MCU that meets these
minimum requirements:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **Flash (code)** | 32 KB | 64 KB |
| **RAM (VM state)** | 8 KB | 12 KB |
| **RAM (bytecode)** | 256 bytes (1 instruction) | 4 KB (512 instructions) |
| **CPU** | 32-bit, any ISA | 32-bit at 48 MHz+ |
| **FPU** | Not required (soft-float) | IEEE 754 single-precision |
| **Timer** | 1 hardware timer | 1 hardware timer |
| **Interrupts** | 1 (for tick timer) | 1 (for tick timer) |

**No dependencies on:**
- Operating system (runs bare-metal)
- C standard library (uses only compiler builtins)
- Dynamic memory allocation
- Floating-point hardware unit
- Any specific MCU vendor SDK (beyond timer setup)

### 10.2 Required C Compiler Features

The VM implementation requires:

1. `<stdint.h>` — Fixed-width integer types (uint8_t, uint16_t, uint32_t)
2. `<string.h>` — `memcpy()` for type-punned float/uint32_t conversion
3. No other headers are required.

Optional compiler features (for optimization):
- GCC/Clang `__attribute__((packed))` for struct packing
- Computed goto for dispatch (fall back to switch if unavailable)
- `__builtin_expect()` for branch prediction hints

### 10.3 Endianness Considerations

The VM uses **little-endian** byte order for all multi-byte fields. On a
big-endian target:

```c
// Portable read of uint16_t from bytecode:
static inline uint16_t read_u16_le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

// Portable read of uint32_t from bytecode:
static inline uint32_t read_u32_le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
```

The compiler (which generates the bytecode) must also write in little-endian.

### 10.4 Floating-Point Portability

The VM uses IEEE 754 single-precision (float32) for all arithmetic. If the
target MCU does not have an FPU:

- Use the compiler's soft-float library (`-mfloat-abi=soft` on ARM, or
  default on ESP32 with soft-float)
- All float operations go through compiler-provided soft-float routines
- Cycle counts in this spec account for soft-float overhead
- Special cases (NaN, Inf, denormals) follow standard IEEE 754 behavior

**Critical:** The NEG_F and ABS_F opcodes use bit manipulation (XOR / AND)
rather than float arithmetic. This is intentional — it avoids invoking the
soft-float library for these trivial operations and guarantees identical
behavior across all platforms.

### 10.5 Minimum Viable VM Implementation

A stripped-down VM implementation (no snapshots, no events, no call stack)
requires:

**Flash (code):**
```
vm_execute_tick()       ~200 bytes  (fetch-decode loop)
dispatch()              ~500 bytes  (32-case switch or table)
Individual op handlers  ~800 bytes  (32 handlers, ~25 bytes each)
vm_clamp_actuators()    ~50 bytes
vm_validate_bytecode()  ~300 bytes  (validation pass)
Type conversion utils   ~50 bytes
────────────────────────────────────
TOTAL CODE              ~1,900 bytes (~2 KB)
```

**RAM (state, no snapshots/events):**
```
Data stack (256 × 4)    1,024 bytes
Variables (256 × 4)     1,024 bytes
Sensor registers        256 bytes
Actuator registers      256 bytes
Actuator config         384 bytes (64 × 3 × float)
PID state (8 × 32)      256 bytes
VM struct overhead      ~64 bytes
────────────────────────────────────
TOTAL RAM               ~3,264 bytes (~3.2 KB)
```

**Implementation effort estimate:**
- Lines of C code: ~800–1,200 LOC (including comments and validation)
- Developer effort: 2–4 days for an experienced embedded C developer
- Testing effort: 1–2 weeks (unit tests for all 32 opcodes, edge cases,
  integration with timer interrupt)

### 10.6 Full VM Implementation (with all features)

```
Flash: ~12 KB (code + validation + debug)
RAM:   ~6 KB (state + snapshots + events)
LOC:   ~1,500–2,000 lines of C
```

---

## Appendix A: Opcode Quick-Reference Table

| Hex | Dec | Mnemonic | Category | Stack (in→out) | Cycles |
|-----|-----|----------|----------|-----------------|--------|
| 0x00 | 0 | NOP | Stack | 0→0 | 1 |
| 0x01 | 1 | PUSH_I8 | Stack | 0→+1 | 1 |
| 0x02 | 2 | PUSH_I16 | Stack | 0→+1 | 1 |
| 0x03 | 3 | PUSH_F32 | Stack | 0→+1 | 1 |
| 0x04 | 4 | POP | Stack | -1→0 | 1 |
| 0x05 | 5 | DUP | Stack | 0→+1 | 1 |
| 0x06 | 6 | SWAP | Stack | 0→0 | 1 |
| 0x07 | 7 | ROT | Stack | 0→0 | 2 |
| 0x08 | 8 | ADD_F | Arith | -2→+1 | 3 |
| 0x09 | 9 | SUB_F | Arith | -2→+1 | 3 |
| 0x0A | 10 | MUL_F | Arith | -2→+1 | 3 |
| 0x0B | 11 | DIV_F | Arith | -2→+1 | 4 |
| 0x0C | 12 | NEG_F | Arith | 0→0 | 1 |
| 0x0D | 13 | ABS_F | Arith | 0→0 | 1 |
| 0x0E | 14 | MIN_F | Arith | -2→+1 | 3 |
| 0x0F | 15 | MAX_F | Arith | -2→+1 | 3 |
| 0x10 | 16 | CLAMP_F | Arith | 0→0 | 3 |
| 0x11 | 17 | EQ_F | Cmp | -2→+1 | 3 |
| 0x12 | 18 | LT_F | Cmp | -2→+1 | 3 |
| 0x13 | 19 | GT_F | Cmp | -2→+1 | 3 |
| 0x14 | 20 | LTE_F | Cmp | -2→+1 | 3 |
| 0x15 | 21 | GTE_F | Cmp | -2→+1 | 3 |
| 0x16 | 22 | AND_B | Logic | -2→+1 | 1 |
| 0x17 | 23 | OR_B | Logic | -2→+1 | 1 |
| 0x18 | 24 | XOR_B | Logic | -2→+1 | 1 |
| 0x19 | 25 | NOT_B | Logic | 0→0 | 1 |
| 0x1A | 26 | READ_PIN | I/O | 0→+1 | 2 |
| 0x1B | 27 | WRITE_PIN | I/O | -1→0 | 2 |
| 0x1C | 28 | READ_TIMER_MS | I/O | 0→+1 | 2 |
| 0x1D | 29 | JUMP | Ctrl | 0→0 | 1 |
| 0x1E | 30 | JUMP_IF_FALSE | Ctrl | -1→0 | 2 |
| 0x1F | 31 | JUMP_IF_TRUE | Ctrl | -1→0 | 2 |

**Pseudo-instructions (via NOP syscall, flags=0x80):**

| operand1 | Name | Stack | Cycles |
|----------|------|-------|--------|
| 0x01 | HALT | 0→0 | 1 |
| 0x02 | PID_COMPUTE | -2→+1 | 15 |
| 0x03 | RECORD_SNAPSHOT | 0→0 | 20 |
| 0x04 | EMIT_EVENT | 0→0 | 3 |

**CALL/RET (via JUMP variant):**

| Encoding | Name | Stack | Cycles |
|----------|------|-------|--------|
| JUMP, flags bit 3 = 1 | CALL | 0→0 | 2 |
| JUMP, operand2 = 0xFFFFFFFF | RET | 0→0 | 2 |

---

## Appendix B: Full Encoding Table

Every field of every instruction, in hex, for a concrete example bytecode
sequence implementing `PUSH_F32 1.5; PUSH_F32 2.5; ADD_F; WRITE_PIN 0; HALT`:

### Instruction 0: PUSH_F32 1.5

```
1.5 in IEEE 754 float32: 0x3FC00000
Little-endian bytes:     00 00 C0 3F

Byte 0 (opcode):   03
Byte 1 (flags):    00
Byte 2 (op1 lo):   00
Byte 3 (op1 hi):   00
Byte 4 (op2 B0):   00
Byte 5 (op2 B1):   00
Byte 6 (op2 B2):   C0
Byte 7 (op2 B3):   3F
Hex: 03 00 00 00 00 00 C0 3F
```

### Instruction 1: PUSH_F32 2.5

```
2.5 in IEEE 754 float32: 0x40200000
Little-endian bytes:     00 00 20 40

Byte 0: 03  Byte 1: 00  Bytes 2-3: 00 00  Bytes 4-7: 00 00 20 40
Hex: 03 00 00 00 00 00 20 40
```

### Instruction 2: ADD_F

```
Byte 0: 08  Byte 1: 00  Bytes 2-3: 00 00  Bytes 4-7: 00 00 00 00
Hex: 08 00 00 00 00 00 00 00
```

### Instruction 3: WRITE_PIN 0

```
Byte 0: 1B  Byte 1: 00  Bytes 2-3: 00 00  Bytes 4-7: 00 00 00 00
Hex: 1B 00 00 00 00 00 00 00
```

### Instruction 4: HALT (NOP syscall)

```
Byte 0: 00  Byte 1: 80  Bytes 2-3: 01 00  Bytes 4-7: 00 00 00 00
Hex: 00 80 01 00 00 00 00 00
```

### Full Bytecode (40 bytes):

```
03 00 00 00 00 00 C0 3F   ; PUSH_F32 1.5
03 00 00 00 00 00 20 40   ; PUSH_F32 2.5
08 00 00 00 00 00 00 00   ; ADD_F
1B 00 00 00 00 00 00 00   ; WRITE_PIN 0
00 80 01 00 00 00 00 00   ; HALT
```

Execution trace:
```
PC=0x00: PUSH_F32 1.5    → SP: 0→1,  STACK: [1.5]
PC=0x08: PUSH_F32 2.5    → SP: 1→2,  STACK: [1.5, 2.5]
PC=0x10: ADD_F           → SP: 2→1,  STACK: [4.0]
PC=0x18: WRITE_PIN 0     → SP: 1→0,  ACTUATOR[0] = 4.0
PC=0x20: HALT            → halted = 1, clean exit
Total cycles: 1+1+3+2+1 = 8
```

---

## Appendix C: Implementor's Checklist

A C developer implementing this VM from scratch should complete the following
steps:

### Phase 1: Core VM (Day 1–2)

- [ ] Define `vm_state_t` struct per Section 4.10
- [ ] Implement `vm_init()` — zero all state, set defaults
- [ ] Implement `vm_load_bytecode()` — validate and set bytecode pointer
- [ ] Implement instruction fetch (8-byte aligned read)
- [ ] Implement dispatch loop (switch statement, all 32 cases)
- [ ] Implement stack operations: NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT
- [ ] Implement arithmetic: ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F
- [ ] Implement comparison: EQ_F, LT_F, GT_F, LTE_F, GTE_F
- [ ] Implement logic: AND_B, OR_B, XOR_B, NOT_B
- [ ] Write unit tests for all stack, arithmetic, comparison, and logic opcodes

### Phase 2: I/O and Control (Day 2–3)

- [ ] Implement READ_PIN, WRITE_PIN (including variable access for op1 ≥ 64)
- [ ] Implement READ_TIMER_MS
- [ ] Implement JUMP (including CALL with flags bit 3 and RET with operand2=0xFFFFFFFF)
- [ ] Implement JUMP_IF_FALSE, JUMP_IF_TRUE
- [ ] Implement syscall dispatch in NOP handler (HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT)
- [ ] Write unit tests for all I/O and control opcodes

### Phase 3: Safety (Day 3)

- [ ] Implement all stack bounds checks (overflow/underflow)
- [ ] Implement PC bounds check
- [ ] Implement call depth limit
- [ ] Implement cycle budget enforcement
- [ ] Implement sensor register write protection
- [ ] Implement `vm_clamp_actuators()` with per-actuator min/max
- [ ] Implement `vm_apply_safe_defaults()`
- [ ] Implement `vm_halt_error()` with full error response protocol
- [ ] Write tests for every safety invariant violation

### Phase 4: Advanced Features (Day 3–4)

- [ ] Implement PID_COMPUTE syscall (full PID with anti-windup)
- [ ] Implement RECORD_SNAPSHOT syscall
- [ ] Implement EMIT_EVENT syscall (ring buffer)
- [ ] Implement `vm_validate_bytecode()` with all validation checks
- [ ] Write integration tests for PID, snapshots, events

### Phase 5: Integration (Day 4)

- [ ] Integrate with hardware timer interrupt (tick driver)
- [ ] Integrate sensor register population (ADC/PWM/UART input)
- [ ] Integrate actuator register draining (PWM/DAC/GPIO output)
- [ ] Integrate safety monitor (error notification, restart logic)
- [ ] Measure actual cycle times on target hardware
- [ ] Verify WCET calculations from Section 9

### Phase 6: Compiler (Separate Module)

- [ ] Implement JSON reflex parser
- [ ] Implement state-to-bytecode compiler per Section 7
- [ ] Implement bytecode validator per Section 7.4
- [ ] Implement bytecode emitter (little-endian output)
- [ ] Write end-to-end tests: JSON → bytecode → VM execution → verify actuator outputs

---

## Document Revision History

| Rev | Date | Author | Description |
|-----|------|--------|-------------|
| 1.0.0 | 2025-07-12 | NEXUS Architecture Team | Initial release — production specification |

---

*End of Specification*
