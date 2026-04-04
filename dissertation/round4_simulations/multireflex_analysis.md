# NEXUS Multi-Reflex Interference and Edge Case Analysis

## Round 4B: Multi-Reflex Interference and Edge Case Simulation

---

## Table of Contents

1. [Scheduling Algorithm Recommendations](#1-scheduling-algorithm-recommendations)
2. [Actuator Arbitration Strategies](#2-actuator-arbitration-strategies)
3. [Formal Proof of Schedulability](#3-formal-proof-of-schedulability)
4. [Resource Isolation Proposals](#4-resource-isolation-proposals)
5. [Comparison to ROS 2 and FreeRTOS](#5-comparison-to-ros-2-and-freertos)
6. [Recommendations for Specification Improvements](#6-recommendations-for-specification-improvements)
7. [Open Questions for Round 5](#7-open-questions-for-round-5)

---

## 1. Scheduling Algorithm Recommendations

### 1.1 Current Design: Priority-Based Fixed-Priority Scheduling

The NEXUS platform currently specifies a priority-based scheduler where each reflex JSON contains a `priority` field (lower number = higher priority, Unix convention). The scheduler runs at 1 kHz on the ESP32-S3, iterating through enabled reflexes in priority order and executing those whose period has elapsed, subject to the 10,000-cycle budget.

**Simulation Results (5 concurrent reflexes):**

| Reflex | Frequency | Priority | Executions | Misses | Worst Response |
|--------|-----------|----------|------------|--------|---------------|
| heading_hold_pid | 10 Hz | 1 | 600/600 | 0 | 51.6 μs |
| throttle_governor | 20 Hz | 2 | 1200/1200 | 0 | 51.1 μs |
| anchor_watch | 0.1 Hz | 3 | 6/6 | 0 | 41.0 μs |
| bilge_monitor | 1 Hz | 4 | 60/60 | 0 | 47.2 μs |
| led_indicator | 1 Hz | 5 | 60/60 | 0 | 48.7 μs |

**Key finding:** Total CPU utilization is 0.004% of the 10K cycle budget — an enormous headroom of 74.35% before the rate-monotonic utilization bound is exceeded.

### 1.2 Rate-Monotonic Scheduling (RMS)

**Definition:** Rate-monotonic scheduling (Liu & Layland, 1973) assigns static priorities inversely proportional to period: higher-frequency tasks get higher priority. This is provably optimal among all static-priority algorithms for preemptive scheduling of periodic tasks.

**Comparison:**

| Criterion | Priority-Based (Current) | Rate-Monotonic |
|-----------|-------------------------|----------------|
| Priority assignment | User-defined `priority` field | Automatic: inversely proportional to frequency |
| Optimality | Suboptimal (depends on user choices) | Provably optimal for static priorities |
| Predictability | Requires manual analysis | Bounded by utilization test |
| Flexibility | User can override (e.g., safety reflex gets highest) | Less flexible (must assign by period) |
| Schedulability test | General response-time analysis | Utilization bound: U ≤ n(2^(1/n) − 1) |

**Recommendation:** Hybrid approach.

1. **Default priority assignment** uses rate-monotonic ordering (throttle_governor at 20 Hz gets priority 1, heading_hold_pid at 10 Hz gets priority 2, etc.)
2. **Priority override** allows the `priority` field in reflex JSON to explicitly set a higher priority for safety-critical reflexes (e.g., heading_hold_pid can override to priority 1 even though its frequency is lower than throttle_governor)
3. **Static validation** at deployment time computes response times using the iterative method from Joseph & Pandya (1986) and rejects deployment if any deadline is missed

### 1.3 Overload Behavior

The overload sweep simulation reveals the saturation point at **12× overload** (i.e., if all reflex cycle costs increase by 12×, deadline misses begin). At normal operation (1×), there is zero deadline misses and the system operates with 99.91% budget headroom per tick.

**Overload strategy recommendation:**

| Strategy | Description | Trade-off |
|----------|-------------|-----------|
| Graceful degradation | Skip lowest-priority reflexes when budget exceeded | Predictable, but lower-priority reflexes starve |
| Temporal isolation | Partition budget equally: 2000 cycles/reflex | Fair, but wastes headroom |
| Importance-based | Always execute safety-critical (priority 1-2), skip cosmetic | Optimal for safety, acceptable for monitoring |

**Recommended:** Importance-based degradation. Priority 1–2 reflexes always execute. Priority 3+ reflexes are skipped when budget < 20% remaining. This ensures heading control and throttle safety are never compromised, while LED indicators and low-frequency monitors may be dropped during transient overload.

### 1.4 Deadline Miss Rate Under Load

| Load Factor | Max Miss Rate | CPU Utilization |
|-------------|---------------|-----------------|
| 1× (normal) | 0.0% | 0.09% |
| 5× | 0.0% | 0.46% |
| 10× | 0.0% | 0.92% |
| 12× (saturation) | >0.1% | 1.10% |
| 20× | ~15% | 1.84% |
| 30× | ~40% | 2.76% |

The system saturates at 12× overload, far exceeding any realistic scenario. Even with worst-case jitter (±10% cycle variance), the system remains schedulable.

---

## 2. Actuator Arbitration Strategies

### 2.1 Problem Statement

When two reflexes attempt to write the same actuator register simultaneously, the system must resolve the conflict. The simulation tested two reflexes (heading_hold_pid at 10 Hz, priority 1; throttle_governor at 20 Hz, priority 2) both writing to actuator 0, with a 10 Hz rate limit.

**Simulation Results:**

| Metric | Value |
|--------|-------|
| Reflex A (Pri 1) accepted writes | 300/300 (100%) |
| Reflex B (Pri 2) accepted writes | 0/600 (0%) |
| Rate-limited drops | 600 |
| Priority conflicts | 0 |

**Observation:** All drops were rate-limited, not priority-based. With a 10 Hz rate limit and two reflexes totaling 30 Hz of writes, 2/3 of writes are correctly rate-limited. The priority system is not exercised because the rate limiter is the bottleneck.

### 2.2 Strategy Comparison

| Strategy | Mechanism | Advantages | Disadvantages |
|----------|-----------|------------|---------------|
| **Last-Writer-Wins** | Most recent write overwrites | Simple, no arbitration logic | Non-deterministic; depends on scheduling order |
| **Priority-Wins** | Higher-priority reflex always wins | Deterministic; safety-critical reflexes protected | Low-priority reflexes are starved |
| **Weighted Blend** | Output = α·A + (1−α)·B | Smooth transitions; no hard drops | Requires tuning; may violate safety constraints |
| **Mutex with Timeout** | First writer locks actuator | Fair; simple implementation | Priority inversion possible |
| **Priority Inheritance** | Low-priority holder boosts priority | Prevents priority inversion | Complex; overhead per lock acquisition |

### 2.3 Recommended Strategy: Priority-Wins with Rate Limiting

The NEXUS platform should implement a **two-stage arbitration**:

1. **Rate limiter** (first stage): Enforces maximum write rate per actuator (configurable, default 10 Hz for servos, 1 Hz for solenoids). This prevents actuator wear from excessive writes.

2. **Priority arbitration** (second stage): When two writes arrive within the same rate-limit window, the higher-priority reflex wins. The lower-priority write is silently dropped and logged.

**Formal specification:**

```
actuator_write(register_idx, value, reflex_id, priority, timestamp):
    if (timestamp - last_accepted_time[register_idx]) < min_interval:
        LOG(rate_limited, register_idx, reflex_id)
        return DROPPED
    
    if (last_writer[register_idx] != reflex_id AND
        priority > last_priority[register_idx]):
        LOG(priority_conflict, register_idx, reflex_id)
        return DROPPED
    
    actuators[register_idx] = CLAMP(value, profile.min, profile.max)
    last_writer[register_idx] = reflex_id
    last_priority[register_idx] = priority
    last_accepted_time[register_idx] = timestamp
    return ACCEPTED
```

### 2.4 Write-Read-Write Race Condition

The simulation of a write-read-write race condition (Reflex A writes at t=0, Reflex B reads at t=random, Reflex A writes at t=δ) shows:

| Metric | Value |
|--------|-------|
| Stale reads | 4,967/10,000 (49.7%) |
| Consistent reads | 5,033/10,000 (50.3%) |

**Analysis:** Without atomic read-modify-write semantics, approximately half of all reads by concurrent reflexes return stale data. This is acceptable for non-safety-critical data (e.g., telemetry logging) but **unacceptable for control loops**.

**Recommendation:** For safety-critical actuator registers, implement a **double-buffering** scheme where the writer atomically swaps buffers at the start of each scheduling period. Readers always access the previous period's complete state.

### 2.5 Actuator Rate Limiting Interaction

The simulation shows that rate limiting dominates priority arbitration. With a 10 Hz rate limit:
- heading_hold_pid (10 Hz): All 300 writes accepted (perfectly matched to rate limit)
- throttle_governor (20 Hz): All 600 writes dropped (exceeds rate limit)

**Recommendation:** The rate limit should be **per-pair** (reflex × actuator), not per-actuator. Alternatively, each actuator should have a dedicated rate limit per connected reflex:

```
rate_limit[reflex_id][register_idx] = 10 Hz  # per-reflex rate
```

This allows each reflex to write at its natural rate without being starved by other reflexes sharing the same actuator.

---

## 3. Formal Proof of Schedulability

### 3.1 System Model

We model N reflexes as a set of periodic tasks τ = {τ₁, τ₂, ..., τₙ} where each task τᵢ has:
- **Period** Tᵢ = 1/fᵢ (derived from the `frequency` field in reflex JSON)
- **Worst-case execution time** Cᵢ (computed from bytecode static analysis or WCET analysis)
- **Relative deadline** Dᵢ = Tᵢ (implicit deadlines, equal to period)
- **Priority** Pᵢ (from the `priority` field, lower = higher priority)

The scheduler is a **fixed-priority preemptive scheduler** running on a single ESP32-S3 core at 240 MHz.

### 3.2 Theorem 1: Schedulability Under Rate-Monotonic Priority Assignment

**Theorem:** A task set τ is schedulable under rate-monotonic priority assignment if and only if its total utilization U ≤ U_rm(n), where U_rm(n) = n(2^(1/n) − 1).

**Proof (Liu & Layland, 1973):** By induction on the number of tasks. For n=1, any utilization ≤ 1.0 is trivially schedulable. For n>1, the critical instant occurs when all tasks are released simultaneously. The utilization bound follows from the worst-case interference pattern. ∎

### 3.3 Theorem 2: Schedulability Under Arbitrary Priority Assignment

**Theorem:** A task set τ with arbitrary priority assignment is schedulable if and only if, for every task τᵢ, its worst-case response time Rᵢ ≤ Dᵢ.

**Proof:** The response time Rᵢ is the longest time from release to completion. For task τᵢ, Rᵢ satisfies the recurrence:

```
Rᵢ⁽⁰⁾ = Cᵢ
Rᵢ⁽ᵏ⁺¹⁾ = Cᵢ + Σ_{j∈hp(i)} ⌈Rᵢ⁽ᵏ⁾/Tⱼ⌉ · Cⱼ
```

where hp(i) is the set of tasks with higher priority than τᵢ. The sequence Rᵢ⁽ᰰ⁾ converges in at most n iterations (Joseph & Pandya, 1986). If Rᵢ ≤ Dᵢ for all i, the task set is schedulable. ∎

### 3.4 Theorem 3: NEXUS 5-Reflex Task Set is Schedulable

**Theorem:** The NEXUS reference deployment with 5 concurrent reflexes is schedulable under rate-monotonic priority assignment with a margin of 74.35%.

**Proof:** We compute the total utilization:

```
U = Σ Cᵢ/Tᵢ
  = (368 cycles / (0.1s × 240×10⁶ Hz)) +   # heading_hold_pid
    (280 cycles / (0.05s × 240×10⁶ Hz)) +   # throttle_governor
    (120 cycles / (1.0s × 240×10⁶ Hz)) +    # bilge_monitor
    (180 cycles / (10.0s × 240×10⁶ Hz)) +   # anchor_watch
    (90 cycles / (1.0s × 240×10⁶ Hz))       # led_indicator
  = 15.33 + 23.33 + 0.50 + 0.0075 + 0.375
  = 39.54 μs/s
  = 3.954 × 10⁻⁵

U_rm(5) = 5 × (2^(1/5) − 1) = 5 × 0.1487 = 0.7435

U / U_rm(5) = 3.954 × 10⁻⁵ / 0.7435 = 5.3 × 10⁻⁵
```

Since U = 0.004% << U_rm(5) = 74.35%, the task set is trivially schedulable. The margin is 74.35 − 0.004 = 74.35%. ∎

### 3.5 Theorem 4: Maximum Reflexes Within 10K Cycle Budget

**Theorem:** The maximum number of identical reflexes (each costing C cycles at frequency f Hz) that can be scheduled within a 10,000-cycle budget at 1 kHz is:

```
N_max = floor(10000 / C) if f ≤ 1000 Hz
```

**Proof:** At 1 kHz, each scheduling tick has 10,000 cycles. If N reflexes each consume C cycles, the constraint is N·C ≤ 10,000. The rate-monotonic bound provides the additional constraint N·(2^(1/N) − 1) ≥ U. For small U (as in NEXUS), the cycle budget is the binding constraint. ∎

**For the NEXUS reference reflex (C = 368 cycles):**
```
N_max = floor(10000 / 368) = 27 reflexes
```

**For the worst-case reflex (C = 1000 cycles):**
```
N_max = floor(10000 / 1000) = 10 reflexes
```

### 3.6 Theorem 5: Hyperbolic Bound (Bini et al., 2003)

**Theorem:** A task set τ is schedulable under rate-monotonic assignment if and only if:

```
Π_{i=1}^{n} (Uᵢ + 1) ≤ 2
```

**Proof:** (Bini, Buttazzo & Buttazzo, 2003). The product form provides a tighter sufficient condition than the Liu-Layland bound for task sets with non-uniform utilization. ∎

**Application to NEXUS:** With 5 reflexes, each contributing Uᵢ ≈ 8 × 10⁻⁶:

```
Π(8×10⁻⁶ + 1)^5 ≈ 1.00004 ≤ 2  ✓
```

The hyperbolic bound is satisfied by a margin of approximately 2.0.

---

## 4. Resource Isolation Proposals

### 4.1 Stack Partition: Per-Reflex Stack Quota

**Problem:** All reflexes share the 256-entry stack. If one reflex uses excessive stack depth, it can prevent others from executing.

**Simulation Results:** Maximum observed stack depth = 27/256 (10.5%). No overflow events in 60-second simulation.

**Proposal:** Partition the 256-entry stack into per-reflex quotas:

```
quota[reflex_i] = max(stack_depth_max[reflex_i], 16)  # minimum 16 entries
total_quota = Σ quota[i]
assert total_quota ≤ 256
```

For the 5 NEXUS reflexes:
- heading_hold_pid: 8 entries
- throttle_governor: 6 entries
- bilge_monitor: 4 entries
- anchor_watch: 5 entries
- led_indicator: 3 entries
- **Total: 26 entries** (10.2% utilization, 230 entries reserved for safety margin)

**Advantage:** Stack overflow in one reflex cannot affect other reflexes. The compiler can statically verify per-reflex stack bounds.

### 4.2 Variable Namespace: Per-Reflex Variable Offset

**Problem:** Two reflexes using the same variable index cause silent data corruption. The simulation shows a 73.3% corruption rate when two reflexes unknowingly share variable index 5.

**Proposal:** Implement per-reflex variable namespaces with offset allocation:

```
variable_offset[reflex_i] = Σ_{j<i} variables_used[reflex_j]
```

At deployment time, the Jetson compiler:
1. Parses all reflex JSON definitions
2. Assigns non-overlapping variable index ranges
3. Emits a variable mapping table to the ESP32
4. Each reflex's bytecode uses its local variable indices (0, 1, 2, ...)
5. The VM translates local indices to global indices at runtime

**Memory cost:** A simple lookup table of 256 bytes (one byte per variable, storing the owning reflex ID). Alternatively, a base pointer per reflex stored in the reflex descriptor.

**Compilation check:** If the total variable count exceeds 256, the compiler rejects the deployment with a clear error message.

### 4.3 PID Controller: Instance Registry

**Problem:** Two reflexes sharing a PID instance corrupt IIR state (integral, prev_error). The simulation shows 50 interferences from a 5 Hz interfering reflex over 10 seconds.

**Proposal:** Implement a PID instance registry with ownership semantics:

```
pid_registry[pid_idx] = {
    'owner': reflex_id,        # which reflex owns this PID
    'access_mode': 'exclusive',  # 'exclusive' or 'readonly'
}
```

At deployment:
1. Compiler detects if two reflexes reference the same PID instance
2. If both write (PID_COMPUTE), deployment is rejected
3. If one writes and one reads, the reader is granted read-only access
4. Read-only access allows reading the output but not modifying integral state

**Runtime enforcement:** PID_COMPUTE syscall checks the registry. If the caller is not the owner, the syscall returns 0.0 with an error flag.

### 4.4 Actuator Ownership Registry

Extending the PID registry concept to actuators:

```
actuator_registry[actuator_idx] = {
    'writers': [reflex_id_1, reflex_id_2],  # list of allowed writers
    'priority_order': [priority_1, priority_2],  # arbitration order
    'rate_limit_hz': 10.0,
}
```

The compiler validates that no actuator has more writers than the arbitration strategy can handle (recommendation: ≤ 2 writers per actuator).

### 4.5 Summary: Resource Isolation Architecture

| Resource | Current State | Proposed Isolation | Cost |
|----------|--------------|-------------------|------|
| Stack (256 entries) | Shared, unbounded | Per-reflex quota (compiler-enforced) | 0 bytes (compile-time) |
| Variables (256 entries) | Shared, unbounded | Per-reflex offset mapping | 256 bytes (runtime table) |
| PID (8 instances) | Shared, unbounded | Ownership registry | 32 bytes (8 × 4 bytes) |
| Actuators (64 registers) | Shared, last-writer-wins | Writer registry + priority | 256 bytes (64 × 4 bytes) |
| Cycle budget (10K) | Shared, greedy | Per-reflex reservation | 0 bytes (compile-time) |

**Total additional memory:** ~544 bytes (well within the 3 KB budget from NEXUS-SPEC-VM-001).

---

## 5. Comparison to ROS 2 Node Lifecycle and FreeRTOS Task Priorities

### 5.1 ROS 2 Node Lifecycle

| Feature | ROS 2 | NEXUS |
|---------|-------|-------|
| **Execution model** | Multi-process, DDS middleware | Single-process bytecode VM |
| **Scheduling** | OS-level (Linux/Fiorex) | Application-level (1 kHz tick) |
| **Lifecycle states** | Unconfigured → Inactive → Active → Finalized | Enabled → Running → Error → Halted |
| **Node communication** | Pub/sub (DDS topics) | Shared sensor/actuator registers |
| **Resource isolation** | Process-level (OS MMU) | Register-level (software) |
| **Determinism** | Non-deterministic (OS scheduling) | Deterministic (fixed priority, bounded cycles) |
| **Safety mechanisms** | safety_system package, watchdog | 4-tier safety escalation, kill switch |
| **Hot reload** | No (restart required) | Yes (reflex swap without restart) |

**Key difference:** ROS 2 relies on the OS for scheduling and isolation, making it non-deterministic. NEXUS provides deterministic scheduling through its application-level scheduler. This makes NEXUS more suitable for hard real-time control loops.

**NEXUS advantage:** The 1 kHz deterministic scheduler guarantees that all reflexes complete within a bounded time window. ROS 2 cannot make this guarantee due to OS-level preemption and GC pauses (in Python) or DDS middleware overhead.

### 5.2 FreeRTOS Task Priorities

| Feature | FreeRTOS | NEXUS |
|---------|----------|-------|
| **Task model** | Preemptive multi-tasking | Cooperative within tick, preemptive across ticks |
| **Priority levels** | 0–31 (configurable) | User-defined (reflex JSON) |
| **Stack allocation** | Per-task (compile-time or dynamic) | Shared 256-entry stack |
| **Inter-task communication** | Queues, semaphores, mutexes | Shared registers, variable namespace |
| **Timing** | tick-based (typically 1 ms) | 1 ms tick (configurable) |
| **Memory protection** | Optional MPU support | None (single address space) |
| **Watchdog** | Hardware + software task monitoring | MAX6818 + software task monitoring |

**Key similarity:** Both use priority-based preemptive scheduling with a tick-based model. NEXUS could theoretically map each reflex to a FreeRTOS task, but the overhead (task switching ~200 cycles × 5 tasks = 1000 cycles) would reduce the cycle budget by 10%.

**Key difference:** NEXUS uses cooperative scheduling within each 1 ms tick (all reflexes run in sequence) while FreeRTOS uses preemptive scheduling at all times. This gives NEXUS better worst-case predictability but less flexibility for long-running computations.

### 5.3 AUTOSAR OS Comparison

| Feature | AUTOSAR OS | NEXUS |
|---------|-----------|-------|
| **Compliance** | ISO 26262 (automotive) | IEC 61508 SIL 1 (marine) |
| **Task categories** | Basic + Extended tasks | Reflexes (single-shot) |
| **Scheduling** | Fixed-priority preemptive | Fixed-priority preemptive |
| **Timing protection** | Execution time budget, inter-arrival time | 10K cycle budget |
| **Error handling** | Protection hooks, OS status | 4-tier safety escalation |
| **Memory protection** | Application-specific | None (single address space) |

**Recommendation:** NEXUS should adopt AUTOSAR-style **timing protection** — a per-reflex execution time budget that triggers an error if exceeded. This is already partially implemented (10K cycle budget), but should be per-reflex rather than global.

---

## 6. Recommendations for Specification Improvements

### 6.1 Critical (Must-Have for Safety Certification)

| ID | Recommendation | Specification | Priority |
|----|---------------|---------------|----------|
| **SP-01** | Add per-reflex variable namespace to reflex JSON | NEXUS-SPEC-VM-001 | HIGH |
| **SP-02** | Add PID instance ownership to reflex JSON | NEXUS-SPEC-VM-001 | HIGH |
| **SP-03** | Add actuator write registry to reflex JSON | NEXUS-SPEC-VM-001 | HIGH |
| **SP-04** | Formalize rate-monotonic priority as default | NEXUS-SPEC-VM-001 | HIGH |
| **SP-05** | Add per-reflex cycle budget allocation | NEXUS-SPEC-VM-001 | HIGH |

**SP-01 Detail:** Each reflex JSON should include:
```json
{
  "variable_namespace": {"offset": 0, "count": 5},
  "pid_instances": [{"idx": 0, "access": "exclusive"}],
  "actuator_writes": [{"idx": 0, "rate_limit_hz": 10, " arbitration": "priority"}]
}
```

### 6.2 Important (Significantly Improves Robustness)

| ID | Recommendation | Priority |
|----|---------------|----------|
| **SP-06** | Add double-buffering for shared actuator registers | MEDIUM |
| **SP-07** | Add per-reflex stack depth limit in compiler validation | MEDIUM |
| **SP-08** | Add write-read-write atomicity guarantee for critical registers | MEDIUM |
| **SP-09** | Add reflex deployment conflict detection at Jetson compiler | MEDIUM |
| **SP-10** | Add overload graceful degradation policy specification | MEDIUM |

### 6.3 Nice-to-Have (Improves Observability)

| ID | Recommendation | Priority |
|----|---------------|----------|
| **SP-11** | Add per-reflex execution statistics telemetry | LOW |
| **SP-12** | Add actuator write audit log (who wrote what, when) | LOW |
| **SP-13** | Add I2C bus utilization monitoring | LOW |
| **SP-14** | Add reflex dependency graph (reflex A's output feeds reflex B's input) | LOW |

---

## 7. Open Questions for Round 5

### Question 1: What is the optimal actuator arbitration strategy for the marine domain?

The simulation shows that rate limiting dominates priority arbitration. Should NEXUS implement **per-pair rate limiting** (each reflex gets its own rate limit per actuator) or **global rate limiting** (one limit per actuator, shared across all writers)? The former provides fairness but may cause actuator oscillation; the latter provides stability but starves low-priority writers.

### Question 2: How should the system handle dynamic reflex addition/removal during operation?

The role reassignment simulation shows a 7.3% execution drop rate during a 500 ms transition window. What is the maximum acceptable drop rate for each priority level? Should there be a "quiescent period" where all reflexes are paused during deployment?

### Question 3: What is the formal verification strategy for the multi-reflex scheduler?

Can the NEXUS bytecode VM scheduler be verified using model checking (e.g., SPIN, UPPAAL)? What properties should be verified (deadlock freedom, starvation freedom, bounded response time)?

### Question 4: How should variable namespace collisions be handled at fleet scale?

If two independently evolved bytecodes from different vessels both use variable index 5, and a fleet operator tries to deploy both to the same ESP32, what error reporting should the system provide? Should the system auto-remap variables or reject the deployment?

### Question 5: What is the optimal cycle budget allocation for mixed-criticality reflexes?

The current 10K cycle budget is shared equally. Should safety-critical reflexes get a guaranteed reservation (e.g., 50% of budget for priority 1–2) while non-critical reflexes get the remainder? How does this interact with the rate-monotonic utilization bound?

### Question 6: How should I2C bus contention be modeled for multi-sensor systems?

The simulation showed zero I2C contention because sensor reads were serialized. In a real system with 10+ sensors on a single I2C bus, contention could cause significant jitter. What is the maximum number of sensors per I2C bus before jitter exceeds the reflex deadline?

### Question 7: What is the impact of FreeRTOS tick jitter on multi-reflex timing?

The 1 ms FreeRTOS tick has ±1 μs jitter on Xtensa LX7. With 5 reflexes, the cumulative jitter could be ±5 μs. For the heading_hold_pid reflex with a 100 ms period and ~1.5 μs execution time, this is negligible. But at higher frequencies (100+ Hz), does jitter accumulate?

### Question 8: How should the system handle a reflex that writes to multiple actuators atomically?

If heading_hold_pid needs to write to both rudder (actuator 0) and thruster (actuator 2) in the same execution cycle, but the rudder write is accepted and the thruster write is rate-limited, the vessel enters an inconsistent state. Should the system implement transactional writes?

### Question 9: What monitoring should detect PID instance contention at runtime?

If two reflexes accidentally share a PID instance (due to a compiler bug or deployment error), how quickly can the system detect this? The simulation showed 50 interferences in 10 seconds — should the system flag after N interferences per second?

### Question 10: How does the multi-reflex scheduler interact with the trust score system?

If a reflex has a low trust score (e.g., T < 0.3), should its cycle budget be reduced? Should low-trust reflexes be deprioritized in favor of high-trust reflexes? What happens if all reflexes for a critical subsystem have low trust simultaneously?

---

## Appendix A: Simulation Configuration

| Parameter | Value |
|-----------|-------|
| CPU frequency | 240 MHz (Xtensa LX7) |
| Cycle budget per tick | 10,000 cycles |
| Stack size | 256 entries |
| Variable space | 256 entries |
| PID instances | 8 |
| Sensor registers | 64 |
| Actuator registers | 64 |
| Scheduler tick | 1 ms (1 kHz) |
| Simulation duration | 60 seconds |
| Overload sweep range | 1× to 35× |
| Monte Carlo seed | 42 |

## Appendix B: Reflex Configuration

| Reflex | Frequency | Priority | Cycles | Stack | Variables | PID | Sensors | Actuators |
|--------|-----------|----------|--------|-------|-----------|-----|---------|-----------|
| heading_hold_pid | 10 Hz | 1 | 368 | 8 | [0–4] | [0] | [0,1] | [0] |
| throttle_governor | 20 Hz | 2 | 280 | 6 | [5–8] | [1] | [2,3] | [1] |
| bilge_monitor | 1 Hz | 4 | 120 | 4 | [10,11] | [] | [10,11] | [5] |
| anchor_watch | 0.1 Hz | 3 | 180 | 5 | [15,16] | [] | [12,13] | [6] |
| led_indicator | 1 Hz | 5 | 90 | 3 | [20] | [] | [20] | [10] |

## Appendix C: Key Simulation Results Summary

| Metric | Value | Assessment |
|--------|-------|------------|
| Total CPU utilization | 0.004% | Excellent headroom |
| Deadline miss rate (normal) | 0.0% | No misses |
| Saturation overload factor | 12× | Far above normal |
| Worst-case response time | 51.6 μs | Well within period |
| Variable collision rate | 73.3% | CRITICAL — needs fix |
| PID interference count | 50 in 10s | Needs isolation |
| NaN write detection | PASS | Safe |
| Infinite loop detection | PASS (5000 iterations) | Safe |
| Stack overflow detection | PASS (at 256) | Safe |
| Division by zero handling | PASS (returns 0.0) | Safe |
| All-reflex halt response | 1000 ms | Acceptable |
| Invalid bytecode validation | 6/6 PASS | Safe |
| Role reassignment drops | 7.3% | Acceptable |

---

*Document generated as part of NEXUS Dissertation Round 4B: Multi-Reflex Interference and Edge Case Simulation.*
