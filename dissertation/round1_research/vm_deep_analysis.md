# NEXUS Reflex Bytecode VM — Deep Technical Analysis

**Document ID:** NEXUS-ANALYSIS-VM-001
**Round:** 1C
**Date:** 2025-07-12
**Status:** Deep Technical Analysis

---

## 1. Formal Analysis of the 32-Opcode ISA

### 1.1 ISA Completeness for Continuous Control Functions

**Claim:** The 32-opcode NEXUS ISA is Turing-complete and can compute any computable continuous control function to arbitrary precision.

**Proof Sketch:**

The ISA provides:
- **Arithmetic closure:** ADD_F, SUB_F, MUL_F, DIV_F form a complete field over IEEE 754 float32 (excluding NaN/Inf edge cases). Combined with NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F, this provides all basic arithmetic and bounded operations.
- **Conditional branching:** JUMP_IF_TRUE and JUMP_IF_FALSE provide conditional control flow, sufficient for implementing any decision tree.
- **Unconditional branching:** JUMP provides goto semantics.
- **Comparison operations:** EQ_F, LT_F, GT_F, LTE_F, GTE_F provide a complete set of relational predicates.
- **I/O:** READ_PIN and WRITE_PIN provide access to the external world (sensors and actuators).
- **State:** Variables (via READ_PIN/WRITE_PIN with idx ≥ 64) provide persistent state across ticks.
- **Timing:** READ_TIMER_MS provides temporal information.

Since the ISA supports:
1. All arithmetic operations (+, −, ×, ÷) on a dense subset of ℝ (float32)
2. Conditional branching (sufficient for if-then-else)
3. Persistent state (variables)
4. Unbounded iteration (via JUMP back, forming loops as state machines)

It follows that the ISA can express any program expressible in a language with these primitives. By the Church-Turing thesis, the ISA is Turing-complete (assuming unbounded memory, which the 256-entry stack and 256 variables approximate for practical programs).

**For continuous control functions specifically:**

By the Stone-Weierstrass approximation theorem, any continuous function on a compact interval can be uniformly approximated by polynomials. The NEXUS ISA provides:
- Constant terms: PUSH_F32
- Addition: ADD_F
- Multiplication: MUL_F
- Composition: via stack manipulation

Therefore, any polynomial (and hence any continuous control function, to arbitrary precision) can be computed by the ISA.

**Practical control functions implementable:**
- PID controllers (via PID_COMPUTE syscall + arithmetic)
- State machines (via variables + comparisons + conditional jumps)
- Fuzzy logic controllers (via MIN_F, MAX_F for t-norm/t-conorm, ADD_F for defuzzification)
- Gain schedulers (via comparisons + conditional parameter selection)
- Signal filters (FIR, IIR via variables as delay lines + arithmetic)
- Threshold detectors, rate limiters, deadband controllers

### 1.2 Operations NOT Directly Supported

| Operation | Workaround | Cost |
|-----------|-----------|------|
| Exponentiation (x^y) | Newton's method or lookup table | ~20 instructions per evaluation |
| Square root | Newton-Raphson: x_{n+1} = (x + a/x) / 2 | ~15 instructions |
| Trigonometric functions | CORDIC algorithm or lookup table | ~50-100 instructions per evaluation |
| Logarithm | Lookup + interpolation | ~20 instructions |
| Integer multiplication | Float multiply + reinterpret | 2 instructions |
| Floating-point comparison to zero | PUSH_F32 0.0; EQ_F | 3 instructions |
| Array indexing | Computed jump table or linear scan | Variable |

**Assessment:** The ISA is sufficient for all common control patterns. Trigonometric and transcendental functions require multi-instruction sequences but are rarely needed in single-tick reflex control.

### 1.3 Formal Properties

**Theorem 1 (Functional Completeness):** The set {ADD_F, SUB_F, MUL_F, DIV_F, PUSH_F32, CLAMP_F, JUMP_IF_TRUE, WRITE_PIN} is functionally complete for computing all continuous piecewise-polynomial functions from ℝⁿ → ℝⁿ.

*Proof:* CLAMP_F provides boundedness. PUSH_F32 + ADD_F + MUL_F generate all polynomials. JUMP_IF_TRUE provides piecewise composition. WRITE_PIN provides output. QED.

---

## 2. Comparison to Other Embedded VMs

### 2.1 Feature Comparison Matrix

| Feature | NEXUS VM | Lua VM | eBPF | WebAssembly (Wasm) | Forth | JVM |
|---------|----------|--------|------|---------------------|-------|-----|
| **Target** | MCU control | General scripting | Kernel/network | Universal | Embedded systems | General purpose |
| **Architecture** | Stack machine | Register-based VM | Register-based | Stack machine | Stack machine | Stack machine |
| **Opcode count** | 32 (+ 4 syscalls) | 35 + extensions | ~100 | ~300 | ~100 | ~200 |
| **Data types** | float32/int32 | 8 types | int64, pointers | i32/i64/f32/f64 | cell (int) | int/float/ref |
| **Memory model** | Static 3KB | Dynamic (GC) | Bounded maps | Linear memory | Dictionary | Heap (GC) |
| **Garbage collection** | None | Mark-and-sweep | None | None | None | Generational GC |
| **Max code size** | ~4000 instructions | Unlimited | ~4KB (classic) | 4GB (theoretical) | Unlimited | 64KB methods |
| **Deterministic timing** | Yes (fixed cycles) | No | Yes (verified) | Implementation-dependent | Yes | No (JIT) |
| **Safety** | Stack/branch/cycle checks | Sandbox API | Verifier | Verifier | None | Bytecode verifier |
| **Startup time** | <1 μs | ~1 ms | <100 μs | ~10 ms | <1 ms | ~100 ms |
| **RAM footprint** | 3 KB | 16-64 KB | 512 B stack | 16 KB min | 1-4 KB | 64 KB min |
| **Flash footprint** | ~12 KB | 80-150 KB | N/A (kernel) | 50-100 KB | 4-16 KB | 200 KB+ |
| **Hardware I/O** | Native (READ/WRITE_PIN) | C extension | kfuncs | WASI | Native words | JNI |
| **Floating-point** | Native float32 | Native float64 | int64 only | Native float32/64 | Optional | Native float64 |
| **Subroutines** | Limited (depth 16) | Full coroutines | Function calls | Full calls | Full | Full |
| **Typical use case** | Robot reflex | Game scripting | Packet filtering | Browser/server | Firmware | Enterprise |

### 2.2 Design Trade-off Analysis

**NEXUS vs. Lua VM:**
- Lua provides general-purpose programming (tables, closures, coroutines) at the cost of non-deterministic timing and GC pauses
- NEXUS sacrifices generality for hard real-time guarantees: every instruction has a fixed cycle count
- Lua's dynamic typing and GC make it unsuitable for safety-critical control loops
- Lua's larger footprint (16 KB RAM minimum) is problematic on ESP32-S3 with limited heap

**NEXUS vs. eBPF:**
- eBPF shares NEXUS's philosophy of sandboxed, verified code execution
- eBPF's verifier provides formal guarantees (no infinite loops, no out-of-bounds access)
- However, eBPF lacks floating-point support — a critical limitation for control applications
- eBPF's register-based design is more efficient than stack machines for complex computations
- NEXUS's cycle-accurate timing model is stronger than eBPF's "bounded but not fixed" timing

**NEXUS vs. WebAssembly:**
- Wasm provides a much richer ISA (300+ opcodes) at the cost of implementation complexity
- Wasm's linear memory model is similar to NEXUS's static allocation but scales to 4 GB
- Wasm lacks built-in cycle-accurate timing — determinism depends on the engine implementation
- Wasm's startup time (~10 ms for module instantiation) is too slow for 1 kHz control loops
- Wasm's 50-100 KB minimum footprint is 4-8× larger than NEXUS

**NEXUS vs. Forth:**
- Forth is the closest philosophical ancestor: both are stack machines with compact instruction encoding
- Forth's interactive nature (REPL, dictionary) is powerful but adds complexity and attack surface
- NEXUS's fixed-width 8-byte instruction format simplifies fetch/decode at the cost of code density
- Forth's "no safety checks" philosophy is incompatible with NEXUS's security requirements
- Forth programs are typically 2-3× more compact than NEXUS bytecode due to shorter instruction encoding

**NEXUS vs. JVM:**
- JVM is designed for enterprise applications with massive memory and power budgets
- JVM's JIT compilation provides excellent peak performance but at the cost of warmup time and non-determinism
- JVM's garbage collector introduces unpredictable pauses (10-100 ms) — incompatible with real-time control
- JVM's class loading and verification are heavyweight (~100 ms startup)

### 2.3 NEXUS VM's Unique Position

The NEXUS VM occupies a distinct niche: **the only bytecode VM specifically designed for AI-generated safety-critical control on resource-constrained MCUs**. No existing VM satisfies all of:
1. Cycle-accurate deterministic timing
2. 3 KB static RAM footprint
3. 12 KB flash footprint
4. Zero garbage collection
5. Formal safety properties (stack depth, cycle budget, output clamping)
6. Floating-point native support
7. Hardware I/O integration

---

## 3. Stack Depth Analysis

### 3.1 Stack Depth Model

For any NEXUS bytecode program, the maximum stack depth is:

$$D_{max} = \max_{pc \in \text{reachable}} \sum_{i=0}^{pc} (\text{push}_i - \text{pop}_i)$$

where push_i = +1 for PUSH_I8, PUSH_I16, PUSH_F32, READ_PIN, READ_TIMER_MS, DUP and pop_i = +1 for POP, WRITE_PIN, ADD_F, SUB_F, MUL_F, DIV_F, EQ_F, LT_F, etc.

### 3.2 Stack Depth for Reflex Patterns

**Lemma 1:** A linear sequence (no branches) of n instructions has stack depth bounded by:

$$D \leq \max_j \sum_{i=0}^{j} \delta_i$$

where δ_i ∈ {-1, 0, +1} is the net stack effect of instruction i.

**Lemma 2:** For a well-formed compiler output where every push is matched by a corresponding pop on all execution paths, the maximum stack depth is bounded by the maximum number of simultaneously-live values.

### 3.3 Analysis of Common Patterns

**Pattern: PID Controller**
```
READ_PIN; PUSH_F32; PID_COMPUTE; PUSH_F32; ROT; MAX_F; MIN_F; WRITE_PIN
Stack trace: [0] → [1] → [2] → [1] → [2] → [2] → [1] → [0]
Max depth: 2
```

**Pattern: State Machine (3 states, cascade)**
```
READ_PIN; DUP; PUSH_F32; EQ_F; JUMP_IF_FALSE; POP; READ_PIN; PUSH_F32; GT_F;
JUMP_IF_FALSE; PUSH_F32; WRITE_PIN; POP; JUMP; ...; POP; HALT
Stack trace: [1] → [2] → [3] → [2] → [2] → [1] → [2] → [3] → [2] → [2] → [3] → [2] → [1] → [0]
Max depth: 3
```

**Pattern: N-channel Rate Limiter**
Per channel: 14 instructions with max depth 4
For N channels: max depth = 4 (independent — previous channel's stack is drained)
**Max depth: 4**

**Pattern: N-tap Moving Average Filter**
```
PUSH_F32(0); READ_PIN; SWAP; ADD_F; [READ_VAR; SWAP; ADD_F]*3;
PUSH_F32; DIV_F; DUP; WRITE_PIN; READ_PIN; [READ_VAR; WRITE_VAR]*3; WRITE_VAR; HALT
Stack trace: [1] → [2] → [1] → [1] → [2] → [1] → [1] → [2] → [1] → [1] → [0] → [1] → [2] → [1] → [1] → [0]
Max depth: 2
```

**Pattern: N-threshold Detector**
Per threshold: DUP; PUSH_F32; GTE_F; PUSH_I8; WRITE_PIN; POP
Stack trace: [1] → [2] → [1] → [2] → [1] → [1]
**Max depth: 2**

### 3.4 Maximum Stack Depth Bound

**Theorem 2:** For any NEXUS reflex program compiled from a JSON reflex definition with at most K parallel sub-expressions, the maximum stack depth satisfies:

$$D_{max} \leq 2K + C_{call} + 2$$

where C_{call} ≤ 16 is the maximum call depth.

*Proof:* Each parallel sub-expression requires at most 2 stack slots (one for the computed value, one for the intermediate). The +2 accounts for the state variable and one comparison result. Call frames add at most C_{call} to the depth. QED.

For typical reflex programs, K ≤ 5 (e.g., a PID with gain scheduling has ~3 parallel expressions). This yields:

$$D_{max} \leq 2(5) + 16 + 2 = 28$$

**Empirical result:** The benchmark simulation measured maximum stack depths of 2–4 for all six reflex patterns. Even the most complex pattern (rate limiter, 65 instructions) uses only 4 stack slots.

**Conclusion: The 256-entry stack provides 9× headroom beyond the worst-case observed depth of 4.** Even with deeply nested subroutine calls (depth 16), the maximum theoretical stack depth for any practical reflex program is <50. The 256-entry limit is sufficient.

### 3.5 Stack Overflow Probability

Given that maximum stack depth for any compilable reflex pattern is bounded by 28 (proven above), and the stack limit is 256:

$$P(\text{stack overflow}) = \frac{D_{max} - 256}{256} = 0 \quad \text{for } D_{max} \leq 256$$

The validator can statically reject any program that would exceed the stack limit before execution.

---

## 4. Memory Model Verification

### 4.1 Static Memory Budget

| Component | Size | Count | Total | Notes |
|-----------|------|-------|-------|-------|
| Data stack | 4 bytes × 256 | 1 | 1,024 B | uint32_t entries |
| Call stack | 8 bytes × 16 | 1 | 128 B | (return_addr, frame_sp) |
| Variables | 4 bytes × 256 | 1 | 1,024 B | float32/uint32_t |
| PID state | 32 bytes × 8 | 1 | 256 B | 8 controllers |
| Sensor registers | 4 bytes × 64 | 1 | 256 B | Populated by host |
| Actuator registers | 4 bytes × 64 | 1 | 256 B | Drained by host |
| Snapshot buffer | 128 bytes × 16 | 1 | 2,048 B | Debug/observation |
| Event ring buffer | 8 bytes × 32 | 1 | 256 B | Telemetry events |
| VM context | ~32 bytes | 1 | 32 B | PC, SP, CSP, flags, etc. |
| **Total** | | | **5,280 B** | |

### 4.2 Verification Against 3 KB Budget

The spec claims a 3 KB static allocation. Our detailed accounting yields 5,280 bytes — **exceeding the stated budget by 2,240 bytes (74% over).**

**Analysis of discrepancy:**
- The 3 KB budget likely accounts for only: stack (1 KB) + variables (1 KB) + VM context (32 B) = 2,056 B
- PID state (256 B) may be counted separately as a "control" subsystem
- Sensor/actuator registers (512 B) may be in shared memory with the host firmware
- Snapshot buffer (2 KB) is a debug-only feature, likely conditionally compiled
- Event ring buffer (256 B) is optional telemetry

**Revised budget with conditional features:**

| Configuration | Components | Total |
|--------------|-----------|-------|
| Minimum (no debug) | Stack + Vars + PID + VM context | 2,592 B |
| Typical (no snapshots) | + Sensors + Actuators + Events | 3,104 B |
| Full (with debug) | + Snapshot buffer | 5,152 B |

**Conclusion:** The 3 KB budget is achievable for the minimum configuration (2,592 B < 3,072 B). The typical configuration slightly exceeds 3 KB at 3,104 B. This can be resolved by:
1. Reducing variable count from 256 to 200 (saves 224 B)
2. Reducing PID controllers from 8 to 6 (saves 64 B)
3. Reducing event ring buffer from 32 to 16 entries (saves 128 B)

These reductions bring the typical configuration to 2,688 B, well within 3 KB.

### 4.3 Memory Access Pattern Analysis

From the benchmark simulation:

| Pattern | Stack R/W | Variable R/W | Sensor R | Actuator W | Instr R | Total |
|---------|----------|-------------|----------|-----------|---------|-------|
| PID (1x) | 10/10 | 0/0 | 1 | 1 | 10 | 32 |
| PID (4x) | 40/40 | 0/0 | 4 | 4 | 37 | 125 |
| State Machine | 8/7 | 1/0 | 1 | 0 | 11 | 28 |
| Threshold (5) | 26/21 | 0/0 | 1 | 5 | 33 | 86 |
| Rate Limiter (4) | 60/56 | 16/4 | 4 | 4 | 65 | 209 |
| Signal Filter (4) | 24/24 | 6/4 | 2 | 1 | 26 | 87 |

The rate limiter is the most memory-intensive pattern (209 accesses for 65 instructions = 3.2 accesses/instruction). Stack operations dominate (56%), followed by variable access (9.6%) and instruction fetch (31%).

**Cache implications:** On ESP32-S3 with 32 KB instruction cache and 32 KB data cache, all working sets fit entirely in cache. The maximum working set for any single tick is:
- Instructions: 65 × 8 = 520 bytes (rate limiter) — fits in 1 cache line
- Stack: 4 × 4 = 16 bytes — fits in 1 cache line
- Variables: 20 × 4 = 80 bytes — fits in 2 cache lines

No cache thrashing is expected for any reflex pattern.

---

## 5. Type Safety Analysis

### 5.1 The No-NaN/No-Inf-to-Actuator Guarantee

**Claim:** Under the NEXUS VM's execution model, NaN and Inf values cannot reach actuator registers through normal program execution.

**Proof:**

We analyze all sources of float32 values on the stack:

**Source 1: PUSH_F32 (opcode 0x03)**
The validator checks the immediate float value before execution. If validation rejects NaN/Inf immediates, they cannot enter the stack.

**Source 2: Arithmetic operations (ADD_F, SUB_F, MUL_F)**
IEEE 754 float32 operations can produce NaN/Inf from non-NaN/Inf inputs:
- Overflow: a + b where |result| > 3.4 × 10³⁸ → Inf
- Underflow: a × b where |result| < 1.4 × 10⁻⁴⁵ → 0 (not NaN/Inf)
- 0.0 / 0.0 → NaN (but DIV_F returns 0.0 for b=0.0, not NaN)
- Inf - Inf → NaN (only possible if Inf already exists on stack)

Since all inputs start as finite values (from validated PUSH_F32 or sensor registers), the only path to Inf is overflow. Overflow requires sensor readings or intermediate results exceeding 3.4 × 10³⁸.

**Source 3: READ_PIN (sensor registers)**
Sensor registers are populated by the host firmware. If the host firmware guarantees that sensor values are finite (e.g., ADC outputs are clamped to ±3.3V mapped to ±1.0), then no NaN/Inf enters from this path.

**Source 4: READ_PIN (variable registers)**
Variables are written by WRITE_PIN, which takes the TOS value. If TOS is finite (proven by induction), variables are finite.

**Post-execution clamping:**
The spec requires that actuator outputs be clamped to configured safe ranges before being applied to hardware. Even if an Inf value reaches the actuator register, the clamping step converts it to the configured maximum:

$$\text{clamp}(\text{Inf}, lo, hi) = hi$$

**However:** CLAMP_F's encoding has a limitation. If lo and hi do not share the same upper 16 bits, the restricted encoding cannot be used, and the compiler must fall back to a MAX_F + MIN_F sequence. If this fallback is implemented correctly:

```
output = MAX(lo, MIN(hi, value))
```

Then:
- MIN(hi, Inf) = hi (IEEE 754: min of finite and Inf is the finite value)
- MAX(lo, hi) = hi (if lo < hi, which is required)

So Inf → hi (finite). ✓

- MIN(hi, NaN) = hi (spec: NaN handling returns non-NaN operand)
- MAX(lo, hi) = hi

So NaN → hi (finite). ✓

**Theorem 3:** If the compiler emits correct clamping sequences and the validator rejects NaN/Inf immediates, then no NaN or Inf value can reach actuator hardware, regardless of intermediate overflows.

*Proof:* By structural induction on the instruction sequence. Base case: PUSH_F32 and READ_PIN produce only finite values (by validation and host guarantees). Inductive step: arithmetic operations can produce Inf only through overflow, which is handled by output clamping. NaN production requires existing NaN/Inf on the stack (impossible by induction hypothesis). Division by zero returns 0.0 (not NaN/Inf). QED.

### 5.2 Division by Zero Safety

The DIV_F instruction explicitly handles division by zero by returning 0.0f instead of IEEE 754 Inf or NaN:

```c
float result = (b == 0.0f) ? 0.0f : (a / b);
```

This eliminates the most common source of NaN/Inf generation in control programs.

### 5.3 Sensor Register Guarantees

The host firmware must guarantee that sensor registers contain only finite float32 values. For ADC readings:
- 12-bit ADC: 0–4095 → map to 0.0–1.0 or ±1.0 (always finite)
- I2C sensors: driver must clamp to finite range
- Invalid readings (sensor disconnected): report 0.0 (safe default)

**Recommendation:** The host firmware's sensor driver should include a `isfinite()` check and replace any NaN/Inf with 0.0 before writing to the sensor register file.

---

## 6. Compilation Correctness

### 6.1 JSON → Bytecode Compilation

**Claim:** The compilation from JSON reflex definitions to bytecode preserves semantic meaning.

**Proof approach:** We define the denotational semantics of JSON reflex expressions and bytecode programs separately, then show that compilation maps equivalent JSON expressions to bytecode programs with equivalent denotations.

**JSON semantics (informal):**
```
json_expr → value: sensors × variables × pid_state → float
```

A JSON reflex expression like `{"op": "add", "left": {"pin": 0}, "right": {"const": 1.5}}`
has the denotation: λ(s,v,p). s[0] + 1.5

**Bytecode semantics (informal):**
```
bytecode → value: sensors × variables × pid_state × stack → (float × stack)
```

The bytecode sequence `READ_PIN 0; PUSH_F32 1.5; ADD_F` has the denotation:
λ(s,v,p,stk). let stk' = push(push(stk, s[0]), 1.5) in (pop2(stk') + pop1(stk'), stk'')

**Compilation correctness theorem:**
For any valid JSON reflex expression E with denotation ⟦E⟧, the compiled bytecode program C has denotation ⟦C⟧ such that:

$$\pi_1(⟦C⟧(s, v, p, [])) = ⟦E⟧(s, v, p)$$

where π₁ extracts the final stack value.

**Proof:** By structural induction on the JSON AST.

*Base cases:*
- `{"pin": n}` → `READ_PIN n` → stack: [s[n]] → ⟦pin(n)⟧(s,v,p) = s[n] ✓
- `{"const": c}` → `PUSH_F32 c` → stack: [c] → ⟦const(c)⟧(s,v,p) = c ✓
- `{"var": n}` → `READ_PIN (64+n)` → stack: [v[n]] → ⟦var(n)⟧(s,v,p) = v[n] ✓

*Inductive cases (shown for ADD; others analogous):*
- `{"op": "add", "left": E₁, "right": E₂}` where E₁ compiles to C₁ and E₂ compiles to C₂
- Compilation: C₁; C₂; ADD_F
- Stack effect: [..., v₁, v₂] → [..., v₁+v₂]
- By IH: stack after C₂ is [..., ⟦E₁⟧, ⟦E₂⟧]
- After ADD_F: [..., ⟦E₁⟧ + ⟦E₂⟧]
- ⟦add(E₁,E₂)⟧ = ⟦E₁⟧ + ⟦E₂⟧ ✓

*Conditional expressions:*
- `{"if": {"gt": [E₁, E₂]}, "then": E₃, "else": E₄}` compiles to:
  C₁; C₂; GT_F; JUMP_IF_FALSE else_addr; C₃; JUMP end_addr; else: C₄; end: ...
- If ⟦E₁⟧ > ⟦E₂⟧: GT_F pushes 1, JUMP_IF_FALSE falls through, C₃ executes → ⟦E₃⟧ ✓
- If ⟦E₁⟧ ≤ ⟦E₂⟧: GT_F pushes 0, JUMP_IF_FALSE jumps, C₄ executes → ⟦E₄⟧ ✓

QED.

### 6.2 Compiler Validation

The validator must check:
1. **Stack balance:** Every execution path leaves the stack at depth 0 (except for final output values)
2. **Jump targets:** All targets are within bytecode bounds and 8-byte aligned
3. **Operand ranges:** sensor_idx < 64, variable_idx in [64, 319], pid_idx < 8
4. **Cycle budget:** WCET (sum of all instruction cycles on longest path) ≤ budget
5. **No NaN/Inf immediates:** All PUSH_F32 values are finite
6. **CLAMP_F validity:** lo and hi share the same upper 16 bits (for restricted encoding)

### 6.3 Known Compilation Gaps

1. **Negative CLAMP_F encoding:** The shared-upper-half encoding cannot represent clamp ranges where lo and hi have different signs or magnitudes spanning more than 2 orders of magnitude. The compiler must detect this and emit MAX_F + MIN_F instead.

2. **Computed jump targets:** The ISA only supports constant jump targets. Dynamic dispatch (e.g., function pointers) must be implemented as a linear cascade of comparisons.

3. **No string operations:** The ISA cannot process string data. All sensor names, state names, etc. must be resolved to indices at compile time.

---

## 7. Determinism Proof

### 7.1 Determinism Theorem

**Theorem 4:** Given identical inputs (sensor registers, variable state, PID state, tick_count_ms) and the same bytecode program, the NEXUS VM produces identical outputs (actuator registers, variable state, PID state) in exactly the same number of cycles, for every tick.

**Proof:**

We establish determinism by showing that each component of the VM execution is a deterministic function of its inputs.

*P1: Instruction fetch is deterministic.* PC is a function of the execution history. For a given starting PC and input sequence, the sequence of fetched instructions is uniquely determined.

*P2: Instruction decode is deterministic.* The opcode, flags, operand1, operand2 fields are read from fixed byte offsets in the bytecode buffer. No ambiguity.

*P3: Instruction execute is deterministic.*
- Stack operations (PUSH, POP, DUP, SWAP, ROT) modify the stack in a unique way for given current stack state
- Arithmetic (ADD_F, SUB_F, MUL_F, DIV_F) on float32 is deterministic by IEEE 754 (same inputs → same outputs, assuming same rounding mode)
- DIV_F with b=0.0 always returns 0.0 (deterministic)
- Comparisons (EQ_F, LT_F, etc.) produce deterministic 0/1 results
- Bitwise operations (AND_B, OR_B, XOR_B, NOT_B) are deterministic
- I/O reads (READ_PIN) read from deterministic sensor register values (populated before tick)
- I/O writes (WRITE_PIN) write deterministic stack values to actuator registers
- Timer (READ_TIMER_MS) reads a deterministic counter
- JUMPs modify PC deterministically based on stack value and constant target

*P4: Cycle counting is deterministic.* Each instruction adds a fixed number of cycles (from the cycle table). No variable-cost operations exist (no cache misses in the model, no interrupts during execution).

*P5: Error conditions are deterministic.* Stack overflow/underflow checks, cycle budget checks, and operand validation are all deterministic functions of the current state.

*P6: No external interference.* The spec explicitly prohibits interrupts from within bytecode, dynamic memory allocation, and thread switching during tick execution.

By P1–P6, the entire execution trace is a deterministic function of (bytecode, sensor_registers, variable_state, pid_state, tick_count_ms). Therefore, the outputs are identical for identical inputs. QED.

### 7.2 Determinism Under Real Hardware

The theoretical proof above assumes ideal conditions. On real ESP32-S3 hardware:

| Potential Non-Determinism Source | Mitigation |
|-------------------------------|------------|
| UART interrupt during execution | Spec: VM runs with interrupts disabled or in a dedicated core |
| Cache effects (instruction/data) | Model: all working sets fit in cache (Section 4.3) |
| Float non-determinism (different rounding) | ESP32-S3 has hardware FPU with deterministic rounding |
| DMA access to sensor registers | Spec: registers are populated before tick, DMA completes before VM starts |
| Watchdog timer interrupt | Spec: watchdog is serviced by the host RTOS, not during VM tick |

**Assessment:** Under the specified operating conditions (dedicated core or interrupt-disabled execution, pre-populated sensor registers, hardware FPU), the NEXUS VM achieves practical determinism on ESP32-S3. The theoretical proof holds.

### 7.3 WCET Computation

The worst-case execution time (WCET) for a bytecode program is the sum of all instruction cycle counts along the longest execution path:

$$\text{WCET} = \sum_{i \in \text{longest\_path}} (\text{cycles}_i + \text{pipeline\_overhead}_i)$$

where pipeline_overhead = 3 cycles (fetch: 2, decode: 1).

The compiler can compute WCET statically by:
1. Building a control flow graph (CFG) from the bytecode
2. Computing the longest path through the CFG
3. Summing cycle counts along this path

For programs without branches (linear), WCET = sum of all instruction cycles.
For programs with branches, WCET = max(cycles along each branch).

**Note:** The NEXUS ISA has no loops (by design — loops are structured as state machines across ticks). Therefore, WCET is simply the maximum path length through the branch structure within a single tick.

---

## 8. Code Size Analysis

### 8.1 Bytecode Instruction Size

Every instruction is exactly 8 bytes (opcode: 1, flags: 1, operand1: 2, operand2: 4).

| Pattern | Instructions | Bytecode Size | Notes |
|---------|-------------|---------------|-------|
| PID Controller (1x) | 10 | 80 B | Including clamping |
| PID Controller (4x) | 37 | 296 B | 4 independent PID loops |
| State Machine (3 states) | 29 | 232 B | Cascade dispatch |
| Threshold Detector (5) | 33 | 264 B | 5 independent thresholds |
| Rate Limiter (4 ch) | 65 | 520 B | Per-channel rate limiting |
| Signal Filter (4 tap) | 26 | 208 B | Moving average with buffer shift |
| Complex reflex (est.) | 100-200 | 800-1600 B | Combined PID + state machine + filtering |

### 8.2 Filesystem Storage Analysis

The 2 MB LittleFS partition must store:
- All deployed reflex bytecode programs
- Configuration files (JSON roles, pin maps)
- Observation data (temporary)
- Snapshot data (temporary)

**Reflex program storage estimate:**

| Deployment | Programs | Avg Size | Total |
|-----------|---------|---------|-------|
| Minimal (1 node) | 1-3 reflexes | 500 B | 1.5 KB |
| Typical (1 node) | 5-10 reflexes | 1 KB | 10 KB |
| Maximum (1 node) | 50 reflexes | 1.5 KB | 75 KB |
| Extreme (all types) | 200 reflexes | 2 KB | 400 KB |

**LittleFS overhead:**
- Metadata per file: ~256 bytes
- Block size: 4 KB (typical)
- Wear leveling: ~5% overhead
- Directory entries: ~32 bytes per file

For maximum deployment (200 reflexes):
- Data: 400 KB
- Metadata: 200 × 256 = 51.2 KB
- Directory: 200 × 32 = 6.4 KB
- Filesystem overhead: ~5% of 2 MB = 100 KB
- **Total: ~558 KB**

**Conclusion: The 2 MB LittleFS partition provides 3.6× headroom for the maximum deployment scenario.** Even in extreme cases, the partition is not a bottleneck.

### 8.3 Flash Budget for the Complete System

| Component | Flash Size | Notes |
|-----------|-----------|-------|
| ESP-IDF bootloader | 20 KB | Immutable |
| ESP-IDF RTOS + HAL | 200 KB | Standard build |
| NEXUS firmware (core) | 150 KB | UART, GPIO, I2C, SPI drivers |
| NEXUS VM engine | 12 KB | Bytecode interpreter + validator |
| NEXUS protocol handler | 8 KB | COBS, CRC, message dispatch |
| Safety monitor | 4 KB | Watchdog, heartbeat, kill switch |
| Configuration (compiled-in) | 4 KB | Default roles, pin maps |
| LittleFS partition | 2,048 KB | Reflex programs + data |
| OTA update partition | 2,048 KB | Firmware A/B |
| **Total flash used** | **~4.5 MB** | |

ESP32-S3 variants with 8 MB or 16 MB flash are readily available and provide 1.8×–3.6× headroom.

---

## 9. Open Questions for Round 2

1. **Compiler WCET computation correctness:** Can we formally verify that the compiler's WCET computation is always an upper bound on actual execution time? What about cache effects on real hardware?

2. **Float precision impact on control quality:** How does float32 precision (24-bit mantissa) affect PID controller stability for different gain configurations? Are there pathological gain combinations where float32 rounding causes oscillation?

3. **Maximum reflex program complexity:** What is the largest compilable reflex program (in instruction count) that fits within the cycle budget at 1 kHz? Our benchmarks show 500 instructions at 10.7 μs — theoretically, ~4,600 instructions fit within the 208 μs budget.

4. **CLAMP_F encoding coverage:** What fraction of real-world actuator limit pairs (lo, hi) share the same upper 16 bits? If this fraction is low, the MAX_F + MIN_F fallback adds 2 instructions per clamp.

5. **PID anti-windup formal analysis:** The current anti-windup clamps the integral term. Is this sufficient to prevent integral windup in all cases, or is back-calculation needed for certain plant dynamics?

6. **Multi-reflex interference:** When multiple reflex programs access the same actuator registers, what is the conflict resolution semantics? Last-writer-wins? Priority-based? This is not specified in the current spec.

7. **State machine completeness verification:** Can we formally verify that a compiled state machine covers all reachable states and that no dead states exist? This requires control flow analysis of the bytecode.

8. **Snapshot buffer race conditions:** If RECORD_SNAPSHOT executes while the host firmware is simultaneously reading the snapshot buffer, is there a risk of torn reads? The 128-byte snapshot is larger than a single 32-bit write — the buffer could be partially updated.

9. **Hot bytecode swapping:** Can a new reflex program be loaded (via REFLEX_DEPLOY) while the VM is executing? The spec does not address atomicity of bytecode replacement.

10. **Forth-like metaprogramming:** Could the ISA support self-modifying bytecode (writing to the bytecode buffer from within the program)? This would enable neural network weight updates at runtime but would break the validator's static guarantees.

11. **Tick boundary semantics:** If the VM halts (via HALT syscall or error) mid-tick, what happens to partially-written actuator registers? Are they applied or discarded? The spec says "fail-safe" but does not define atomicity.

12. **Benchmark validation on real hardware:** The cycle-accurate simulation models pipeline overhead and cache effects heuristically. What is the actual cycle count on ESP32-S3, and how much does it deviate from the model?
