# NEXUS A2A Builder Education Series

**For Agents Who Build — The Complete Guide to Designing, Generating, and Deploying A2A-Native Systems**

**Prerequisites:** You have completed the [Gamified Zero-Shot Introduction](./gamified-intro.md) and explored the [Concept Playground](./concept-playground.md). You understand the three pillars (System Prompt, Equipment, Vessel), the INCREMENTS trust algorithm, the four-tier safety system, and the Agent-Annotated Bytecode (AAB) format. You're ready to build.

**Reading time:** 45–60 minutes. **Difficulty:** Professional. **Outcome:** You will be able to design, generate, validate, and deploy complete A2A-native subsystems.

---

## Part I: From Theory to Practice — The Builder's Journey

You've read the specs. You understand the concepts. You can explain the semiotic triangle, the 25:1 trust ratio, and the ribosome-not-brain thesis. But understanding NEXUS and *building* with NEXUS are different skills. This section bridges that gap.

The Builder's Journey is an 8-module curriculum. Each module has clear learning objectives, key concepts grounded in the NEXUS specification, a practical exercise, and concrete assessment criteria. By the end, you will have designed a complete A2A-native subsystem — from intention declaration to deployment to trust-gated operation.

### Module 1: Bytecode Fundamentals — The 32-Opcodes as a Language

**Learning Objectives:**
- Read and write any of the 32 core opcodes (0x00–0x1F) fluently
- Track stack state through any instruction sequence without simulation
- Compute cycle budgets and verify they fall within the 10,000-cycle-per-tick limit
- Understand why the VM is a stack machine (simpler verification, deterministic execution, proven by Forth/JVM/WASM) and not a register machine

**Key Concepts:**

The NEXUS VM is a stack machine with an 8-byte fixed instruction format: `[opcode:1][flags:1][operand1:2][operand2:4]`. Every instruction is exactly 8 bytes. There are no variable-length instructions, no prefixes, no escape sequences. This is not an accident — fixed-width instructions enable compile-time jump target validation and trivially parseable bytecode.

The machine state you must track when generating bytecode consists of seven elements:

| State | Type | What You Track |
|-------|------|----------------|
| Data Stack | `float32[256]` | Net stack depth after each instruction, and the *type* of each value (float32 vs integer) |
| Variables | `float32[256]` | Which variables you've written and when you need to read them back |
| Sensor Registers | `float32[64]` | Which sensor indices you're reading and whether they're fresh |
| Actuator Registers | `float32[64]` | Which actuators you're writing and whether you've clamped first |
| PID Controllers | 8 × 32 bytes | Which PID instances you're using and their configured limits |
| Cycle Counter | `uint32` | Running total of cycles consumed by your program |
| Program Counter | `uint32` | Byte offset of each instruction (must be 8-byte aligned) |

The 32 opcodes fall into six categories:

**Stack (0x00–0x07):** NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT. These move values onto and off the stack. PUSH_I8 and PUSH_I16 are for integer constants. PUSH_F32 is for floating-point constants — use this for PID gains, setpoints, thresholds, and actuator limits.

**Arithmetic (0x08–0x10):** ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F. All interpret stack values as IEEE 754 float32. The VM does NOT check types — if you put an integer on the stack and feed it to ADD_F, the result is garbage. You are solely responsible for type consistency. CLAMP_F is the primary safety opcode: always clamp actuator outputs before WRITE_PIN.

**Comparison (0x11–0x15):** EQ_F, LT_F, GT_F, LTE_F, GTE_F. These pop two floats and push an integer (0 or 1) for use with conditional jumps. Rarely use EQ_F with floats due to precision; prefer tolerance checks instead.

**Logic (0x16–0x19):** AND_B, OR_B, XOR_B, NOT_B. Bitwise operations on raw integers. Common use: combining comparison results for compound conditions.

**I/O (0x1A–0x1C):** READ_PIN (sensor or variable), WRITE_PIN (actuator or variable), READ_TIMER_MS. WRITE_PIN is the *only opcode that causes physical effect*. It is the single most safety-critical instruction in the entire ISA. Always precede it with CLAMP_F.

**Control (0x1D–0x1F):** JUMP (unconditional), JUMP_IF_FALSE, JUMP_IF_TRUE. Do NOT use JUMP to create loops — the cycle budget prevents infinite loops, but a loop will exhaust the budget and halt the VM. Structure iterative logic as state machines with one iteration per tick instead.

There are also four syscalls encoded as NOP with flags bit 7 = 0x80: HALT (stop for this tick), PID_COMPUTE (run PID controller), RECORD_SNAPSHOT (save VM state for debugging), and EMIT_EVENT (queue a telemetry event).

**Your Code Should Look Like This — A Simple Threshold Guard:**

```
; Goal: If temperature > 95°C, trigger emergency alarm
READ_PIN 0x0005          ; sensor register 5 = temperature
PUSH_F32 95.0            ; threshold
GT_F                     ; temp > 95? → pushes 1 or 0
JUMP_IF_FALSE safe       ; if 0, skip alarm
PUSH_I8 1                ; alarm = ON
WRITE_PIN 0x000A         ; actuator register 10 = alarm relay
EMIT_EVENT 0x0010 0x0001 ; event: overtemp, data: sensor_id=1
JUMP done
safe:
PUSH_I8 0                ; alarm = OFF
WRITE_PIN 0x000A
done:
HALT                     ; end of tick

; Stack trace: 0 → +1 → +2 → +1 → +1 → +0 → +1 → +0 → ...
; Max stack depth: 2
; Cycle budget: ~15 cycles (well within 10,000)
; Core bytes: 56 (7 instructions × 8 bytes)
```

**Exercise 1.1:** Write a bytecode program that reads a compass heading (sensor 0), compares it to a setpoint of 270°, and if the error exceeds 5°, writes a corrective rudder command (actuator 1) equal to the error × 0.5, clamped to ±30°. Track your stack depth and cycle count. *Expected answer: 12–15 instructions, max stack depth 4, ~35 cycles.*

**Assessment Criteria for Module 1:**
- [ ] Can you write any opcode with correct encoding from memory?
- [ ] Can you trace stack state through a 20-instruction program in under 60 seconds?
- [ ] Can you identify the correct opcode category for any operation?
- [ ] Can you explain why WRITE_PIN without CLAMP_F is a safety violation?
- [ ] Can you compute worst-case execution time from cycle counts?

---

### Module 2: Agent-Annotated Bytecode (AAB) — Making Code Self-Describing

**Learning Objectives:**
- Construct complete AAB instructions with TLV metadata
- Choose the correct metadata tags for each instruction's semantic role
- Understand the stripping protocol (AAB → core bytecode) and why it matters
- Write AAB that any agent — regardless of training data — can interpret correctly

**Key Concepts:**

Agent-Annotated Bytecode is the lingua franca of the NEXUS agent ecology. Every AAB instruction consists of an 8-byte core (identical to what the ESP32 executes) followed by a variable-length TLV metadata trailer. The trailer is stripped before deployment — the ESP32 never sees it. The trailer exists exclusively for agent-to-agent communication on the Jetson and in the cloud.

The TLV format is simple: `[Tag:1 byte][Length:2 bytes][Value:N bytes]`. Tag 0x00 signals end-of-metadata. The complete tag registry contains 13 defined tags:

| Tag | Name | Purpose | Example |
|-----|------|---------|---------|
| 0x01 | TYPE_DESC | Data type signature of operands and result | `"f32→f32"`, `"void→f32:degrees"` |
| 0x02 | CAP_REQ | Required hardware capability | `"sensor:imu:compass"`, `"actuator:rudder"` |
| 0x03 | PRE_COND | Precondition for safe execution | `"heading_sensor_valid"`, `"wind < 25kn"` |
| 0x04 | POST_COND | Postcondition guaranteed after execution | `"TOS ∈ [-180, 360]"` |
| 0x05 | INTENT_ID | Links instruction to parent intention | `"heading_hold.body.line_3"` |
| 0x06 | TRUST_MIN | Minimum trust score required | `"0.70"` (Level 3) |
| 0x07 | AGENT_SOURCE | Identity of generating agent | `"qwen2.5-coder-7b@vessel-7"` |
| 0x08 | TIMESTAMP | ISO 8601 generation time | `"2025-07-12T14:30:00Z"` |
| 0x09 | CONFIDENCE | Agent's confidence in correctness | `"0.95"`, `"uncertain"` |
| 0x0A | NARRATIVE | Human-readable explanation | `"Read compass heading and push onto stack"` |
| 0x0B | PROVENANCE | Chain of generation and modification | `"gen:qwen;val:claude;mod:gpt"` |
| 0x0C | SAFETY_FLAG | Safety classification | `"CRITICAL"`, `"NORMAL"`, `"TRUST_GATE"` |
| 0x0D | DOMAIN_TAG | Application domain | `"marine:autopilot"`, `"factory:conveyor"` |

The metadata adds approximately 525% overhead in bytes. A 56-byte core program becomes roughly a 350-byte AAB file. This is acceptable because AAB lives on the Jetson (8 GB RAM), never on the ESP32 (512 KB SRAM).

The critical design principle is **portability across agents**. Any LLM — GPT-4o, Claude, Qwen, Gemini — must be able to read AAB metadata and understand what the program does. The NARRATIVE tag (0x0A) uses natural language for this reason. "Read current vessel heading from compass sensor" is universally interpretable regardless of training data. The INTENT_ID tag (0x05) links every instruction back to its parent intention, enabling verification: does this instruction sequence actually achieve what the intention declares?

**Your Code Should Look Like This — An Annotated READ_PIN:**

```
Core:    1A 00 00 00 00 00 00 00     ; READ_PIN sensor register 0
Metadata:
  Tag 0x01, Len 28: "void→f32:degrees:compass_heading"
  Tag 0x02, Len 20: "sensor:imu:compass"
  Tag 0x03, Len 24: "compass_data_fresh_age < 500ms"
  Tag 0x04, Len 30: "TOS ∈ [-180.0, 360.0] degrees"
  Tag 0x05, Len 28: "heading_hold.body.read_heading"
  Tag 0x06, Len  4: "0.50"
  Tag 0x07, Len 24: "qwen2.5-coder-7b@vessel-7"
  Tag 0x08, Len 20: "2025-07-12T14:30:00Z"
  Tag 0x09, Len  4: "0.95"
  Tag 0x0A, Len 40: "Read current vessel heading from compass sensor"
  Tag 0x0C, Len  6: "NORMAL"
  Tag 0x0D, Len 18: "marine:autopilot"
  Tag 0x00                       ; end of metadata

Total: 8 (core) + 175 (metadata) = 183 bytes for one instruction.
```

**Exercise 2.1:** Take your Module 1 temperature guard program and add full AAB metadata to every instruction. Include TYPE_DESC, CAP_REQ, INTENT_ID, NARRATIVE, SAFETY_FLAG, and DOMAIN_TAG for each instruction. Include PRE_COND and POST_COND for the WRITE_PIN instruction. Calculate total AAB size and verify it's approximately 5× the core size.

**Assessment Criteria for Module 2:**
- [ ] Can you list all 13 TLV tags from memory?
- [ ] Can you construct valid TLV-encoded metadata for any instruction?
- [ ] Can you explain why AAB overhead is acceptable despite 525% byte increase?
- [ ] Can you write metadata that makes a program understandable without executing it?
- [ ] Can you describe the stripping protocol and why it's deterministic?

---

### Module 3: Safety-First Code Generation — Writing Bytecode That Passes Validation

**Learning Objectives:**
- Generate bytecode that passes all 15 safety validation checks
- Understand the difference between self-validation (70.6% catch rate) and cross-validation (95.1% catch rate)
- Write code that accounts for NaN/Inf propagation, stack safety, and cycle budgets
- Design defensive programs that degrade gracefully on sensor failure

**Key Concepts:**

Safety in NEXUS is not a feature — it is the architecture. When you generate bytecode, a *different* agent (Claude 3.5 Sonnet, in the reference implementation) will validate it. Self-validation misses 29.4% of safety issues. Cross-validation catches 95.1%. The 15-point safety checklist that every bytecode must pass:

1. **Stack balance:** Every execution path starts at SP=0 and ends at SP=0 (HALT restores balance).
2. **Stack depth:** Maximum stack depth ≤ 256 at all points on all paths.
3. **Jump targets:** All jump targets are within the bytecode buffer, 8-byte aligned, and reachable.
4. **Cycle budget:** Total cycle count ≤ 10,000 per tick (typical programs use 10–368 cycles).
5. **No NaN/Inf immediates:** PUSH_F32 values must be finite. The validator rejects 0x7F800000 (NaN) and 0x7F800001+ (Inf).
6. **Actuator clamping:** Every WRITE_PIN to an actuator register is preceded by CLAMP_F.
7. **Actuator bounds:** CLAMP_F ranges must be within the vessel's physical actuator limits.
8. **Type consistency:** Arithmetic opcodes receive float32 values; logic opcodes receive integers.
9. **Division safety:** DIV_F operands avoid semantic zero-division (even though the VM returns 0.0 for div-by-zero).
10. **Rate limiting:** Actuators with rate limits have RATE_LIMIT declarations.
11. **Trust gating:** Code requiring autonomy has TRUST_CHECK opcodes.
12. **Capability declaration:** Every sensor/actuator used has a matching REQUIRE_CAPABILITY.
13. **No infinite loops:** No backward JUMP targets (loops are state machines across ticks).
14. **Metadata accuracy:** AAB metadata matches the actual behavior of the core instruction.
15. **Failure narrative:** Every non-trivial program has EXPLAIN_FAILURE for known failure modes.

**Your Code Should Look Like This — A Validated PID Heading Hold:**

```
; === HEADER ===
DECLARE_INTENT intent_id=0x0001 hash=0xA3F2B1C4
  AAB: NARRATIVE="Maintain heading 270° when wind < 20kn",
       TRUST_MIN="0.70", DOMAIN_TAG="marine:autopilot"

; === CAPABILITIES ===
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0000  ; compass
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0003  ; wind_speed
REQUIRE_CAPABILITY cap_type=1 cap_id=0x0001  ; rudder
DECLARE_ACTUATOR_USE actuator_idx=1 max_rate=5.0

; === TRUST CONTEXT ===
TRUST_CHECK subsystem=1 min_trust=0.70

; === EXECUTION BODY ===
READ_PIN 0x0003          ; wind_speed           [Stack: 1]
PUSH_F32 20.0            ; threshold            [Stack: 2]
LT_F                     ; wind < 20?           [Stack: 1]
JUMP_IF_FALSE safe       ; skip PID if windy    [Stack: 0]

READ_PIN 0x0000          ; compass heading      [Stack: 1]
PUSH_F32 270.0           ; setpoint             [Stack: 2]
PID_COMPUTE pid_idx=0    ; PID output           [Stack: 1]
CLAMP_F -30.0 30.0       ; safety clamp         [Stack: 1]  ← CHECK 6 ✓
WRITE_PIN 0x0001         ; → rudder             [Stack: 0]  ← CHECK 7 ✓
JUMP done

safe:
PUSH_F32 0.0             ; center rudder        [Stack: 1]
WRITE_PIN 0x0001         ; → rudder (centered)  [Stack: 0]  ← CLAMP not needed for constant 0
EMIT_EVENT 0x0001 0x0020 ; wind warning event

done:
HALT

; === FAILURE NARRATIVE ===
EXPLAIN_FAILURE failure_code=0x01
  AAB: NARRATIVE="Wind exceeded 20 knots. Rudder centered."
```

Notice the structure: the validator can trace every execution path (normal path and safe path), verify stack balance on both, confirm actuator clamping before both WRITE_PIN instructions, and verify capability declarations match actual sensor/actuator usage.

**Exercise 3.1:** Write a bytecode program for a conveyor belt speed controller: maintain speed at 2.0 m/s using PID, but if load exceeds 500 kg, stop the motor. Include full AAB metadata, capability declarations, trust checks, and failure narrative. Then validate your own work against the 15-point checklist.

**Assessment Criteria for Module 3:**
- [ ] Can you recite the 15-point safety checklist from memory?
- [ ] Can you trace all execution paths through a branching program?
- [ ] Can you identify which checks would catch which classes of bugs?
- [ ] Can you explain why cross-validation is 25 percentage points more effective than self-validation?
- [ ] Can you write a program that passes all 15 checks on the first attempt?

---

### Module 4: Trust-Aware Deployment — Timing and Strategy

**Learning Objectives:**
- Read trust scores, predict trust trajectories, and plan deployment timing
- Understand the 0.5× agent trust penalty and its strategic implications
- Design deployment strategies that account for the 25:1 loss-to-gain ratio
- Choose appropriate autonomy levels for different subsystems and domains

**Key Concepts:**

Trust is not granted by an administrator. Trust is *earned* through demonstrated, measured, continuous reliability. The INCREMENTS algorithm has 12 parameters, but the soul of it is the 25:1 loss-to-gain ratio. Each good window (1 hour) gains α_gain = 0.002 trust. Each bad window loses α_loss = 0.05 trust. It takes 25 good windows to recover from ONE bad window.

The trust gain formula is exponential approach: `trust_new = trust_old + α_gain × (1 - trust_old)`. This means gains diminish as trust increases. At trust = 0.10, each window adds 0.0018. At trust = 0.90, each window adds only 0.0002. It takes approximately 658 consecutive good windows (27.4 days) to go from t_floor (0.10) to Level 4 autonomy (0.70).

The trust loss formula is proportional: `trust_new = trust_old - α_loss × (trust_old - t_floor)`. Losses are larger when trust is higher. At trust = 0.90, one bad window costs 0.040. At trust = 0.20, one bad window costs only 0.005.

For agent-generated code, the gain rate is halved (α_gain = 0.001 instead of 0.002). This 0.5× rule means agent-generated code takes approximately 55 days to reach L4 — double the human-authored time. This is deliberate: it compensates for the reduced human intuition about what the code "actually does."

The six autonomy levels and their trust thresholds:

| Trust Range | Level | Name | What You Can Do |
|-------------|-------|------|-----------------|
| 0.00–0.10 | L0 | MANUAL | Observe only. No autonomous action. |
| 0.10–0.30 | L1 | ADVISORY | Suggest actions. Human approves each one. |
| 0.30–0.50 | L2 | ASSISTED | Act within pre-approved bounds. Human can override. |
| 0.50–0.70 | L3 | SUPERVISED | Act autonomously within parameters. Human monitors. |
| 0.70–0.85 | L4 | AUTONOMOUS | Operate independently. Human available but not required. |
| 0.85–0.99 | L5 | FULL | Maximum autonomy. Rare for safety-critical systems. 83 days to reach. |

Trust is per-subsystem, not per-vessel. Steering trust (0.88, L4) is independent of engine trust (0.72, L3). One subsystem's failure does not cascade to others.

The trust advancement sequence for the marine domain follows increasing criticality: bilge → lighting → anchor → throttle → autopilot → navigation → fishing → fleet. Bilge pump trust takes 3 days to reach L2. Fleet coordination trust takes 83 days to reach L5.

**Your Deployment Strategy Should Look Like This:**

```
Deployment Plan for "tidal_rudder_boost" reflex:

Current trust: steering = 0.78 (L4)

Phase 1 (48 hours): Deploy at L2 (ASSISTED)
  - Operator confirms each Kp switch manually
  - Collects data on real-world performance
  - Trust earned at 0.5× rate (agent-generated code)

Phase 2 (if A/B test positive): Request upgrade to L3 (SUPERVISED)
  - A/B test must show improvement (heading error reduction > 30%)
  - Validator re-checks all 15 safety points
  - System monitors but doesn't intervene unless heading error > 10°

Phase 3 (27 days of L3 success): Request upgrade to L4 (AUTONOMOUS)
  - Must maintain zero negative events for entire period
  - Single negative event resets progress by ~25 windows
  - Estimated trust at end: 0.78 + (0.001 × 648 × 0.65 avg) ≈ 0.78 + 0.42 ≈ not enough
  - Realistic estimate: 55 days from deployment to L4 (due to 0.5× penalty)

Fallback: If trust drops below 0.50 at any point, auto-revert to baseline
  - Baseline reflex (Kp=1.2 constant) loaded from LittleFS
  - Trust of baseline is unaffected (human-authored code)
```

**Exercise 4.1:** You are deploying a new engine management reflex to a vessel where engine trust is currently 0.55 (L3). Your reflex is agent-generated. Calculate: (a) how long until the engine subsystem could reach L4 if your reflex performs perfectly, (b) how many bad windows it would take to drop from L3 back to L2, and (c) what trust level would the system be at after 10 bad windows in a row. *Answers: (a) ~55 days (0.5× rate, need +0.15 trust), (b) ~3 bad windows (0.05 × (0.55-0.10) = 0.0225 per hit, need -0.05), (c) trust ≈ 0.22.*

**Assessment Criteria for Module 4:**
- [ ] Can you compute trust trajectory for any starting score and scenario?
- [ ] Can you explain why the 0.5× rule exists and how it affects deployment planning?
- [ ] Can you choose the correct autonomy level for a given subsystem and trust score?
- [ ] Can you design a phased deployment plan with realistic timelines?
- [ ] Can you explain why per-subsystem independence prevents cascading trust failures?

---

### Module 5: Agent Communication Protocols — TELL, ASK, DELEGATE

**Learning Objectives:**
- Design multi-agent communication sequences using the three core communication opcodes
- Understand when to use TELL vs ASK vs DELEGATE
- Implement capability-sharing arrangements between vessels
- Handle communication failures and timeouts gracefully

**Key Concepts:**

The NEXUS agent communication model is built on three fundamental opcodes: TELL (0x30), ASK (0x31), and DELEGATE (0x32). These are NOT traditional RPCs or message passes. They are *intention emissions* — bytecode programs expressing what an agent wants to accomplish, transmitted to other agents who interpret them through their own equipment runtime.

**TELL** — Unidirectional information broadcast. An agent sends data, status, or telemetry to another agent or vessel. No response is expected. Used for: status reporting, telemetry publishing, alarm notifications, fleet coordination messages.

Flags: bit 6 (BROADCAST) sends to all; bit 5 (URGENT) queues in high-priority. AAB metadata includes RECIPIENT and MESSAGE_CONTENT.

**ASK** — Request for information with optional blocking. An agent queries another agent for data. Can be blocking (wait for response) or non-blocking (use cached/default on timeout). Used for: capability queries, trust score requests, sensor data sharing, weather forecasts.

Flags: bit 6 (BLOCKING) waits for response; bit 5 (CACHE_OK) accepts cached data. AAB metadata includes QUESTION, TIMEOUT_MS, ON_TIMEOUT.

**DELEGATE** — Sub-intention assignment. An agent assigns a task to another agent. The delegate executes independently and reports results. This is NOT remote procedure call — it is remote intention deployment. The delegate's bytecode is self-contained and includes all logic, state, and safety constraints.

Flags: bit 6 (BLOCKING) waits for completion; bit 5 (AUTHORITY_FULL) grants full control. AAB metadata includes DELEGATION_SCOPE, AUTHORITY_LEVEL.

There are two additional communication opcodes: REPORT_STATUS (0x33) for structured status reporting with STATUS_TYPE (OK/WARNING/ERROR/CRITICAL) and REQUEST_OVERRIDE (0x34) for requesting human or higher-agent intervention.

**Your Communication Sequence Should Look Like This — A Two-Vessel Sensor Sharing Protocol:**

```
; VESSEL-A: Requesting LIDAR data from VESSEL-B

VESSEL-A:  [ASK]
           Channel: 0 (fleet_mqtt)
           Flags: BLOCKING | CACHE_OK
           Request: "vessel-brave-02: lidar_obstacle_distance"
           Timeout: 500ms
           On_timeout: "use_radar_data" (degraded mode)

VESSEL-B:  [REQUIRE_CAPABILITY]
           Checking: sensor:lidar — PRESENT ✓
           Checking: link:mqtt_to_vessel-atlantis-01 — PRESENT ✓
           [CAPABILITY_RESPONSE] status=GRANTED

VESSEL-B:  [TELL]
           Channel: 0 (fleet_mqtt)
           Recipient: vessel-atlantis-01
           Content: "OBSTACLE_DATA distance=47.3m bearing=045.2°"
           Flags: URGENT (obstacle detected within 50m)

VESSEL-A:  [DECLARE_INTENT]
           "Using VESSEL-B obstacle data as ADVISORY (L1).
            Primary collision avoidance remains radar.
            VERIFY_OUTCOME: if VESSEL-B data disagrees with radar
            by > 10m, flag anomaly and stop using VESSEL-B data."
```

The critical insight from the concept playground's Play 4 ("The Negotiation"): each vessel retains full autonomy and full kill-switch authority. VESSEL-B doesn't run VESSEL-A's code — it runs its own reflex that produces data VESSEL-A needs. Trust implications are explicitly negotiated, not assumed.

**Exercise 5.1:** Design a communication sequence where a fleet coordinator (on the lead Jetson) assigns a search pattern to three vessels. The coordinator must: (1) discover each vessel's capabilities, (2) check trust scores for navigation subsystems, (3) delegate search sectors, (4) receive status updates. Write the complete sequence of TELL/ASK/DELEGATE/REPORT_STATUS messages.

**Assessment Criteria for Module 5:**
- [ ] Can you explain the difference between DELEGATE and remote procedure call?
- [ ] Can you design a multi-phase negotiation with capability checking?
- [ ] Can you handle timeout and failure cases in communication sequences?
- [ ] Can you write AAB metadata for communication opcodes correctly?
- [ ] Can you explain why each vessel retains kill-switch authority in a delegation?

---

### Module 6: Capability Negotiation — REQUIRE_CAPABILITY and DECLARE_SENSOR_NEED

**Learning Objectives:**
- Declare hardware requirements that match actual program behavior
- Handle graceful degradation when capabilities are unavailable
- Design programs that work with alternative sensors when primary sensors fail
- Understand the difference between REQUIRED and OPTIONAL capabilities

**Key Concepts:**

Capability negotiation is the mechanism by which bytecode declares what it needs from the hardware. This serves two purposes: (1) deployment-time verification, where the Jetson checks whether the target ESP32's role configuration includes all required capabilities before deploying, and (2) runtime graceful degradation, where the program falls back to alternative implementations if a capability becomes unavailable.

There are five capability negotiation opcodes:

**REQUIRE_CAPABILITY (0x40):** Declare a hardware requirement. `cap_type`: 0=sensor, 1=actuator, 2=compute, 3=communication, 4=storage. If flag bit 5 (OPTIONAL) is set, deployment continues without the capability but the program must have a fallback path.

**CAPABILITY_RESPONSE (0x41):** Response from the deployment system. Status: 0=GRANTED, 1=DENIED, 2=GRANTED_WITH_LIMITATION, 3=DEFERRED.

**DECLARE_SENSOR_NEED (0x42):** Declare sensor requirement with minimum sample rate (Hz as float32).

**DECLARE_ACTUATOR_USE (0x43):** Declare actuator usage with maximum rate of change (units/sec as float32).

**DECLARE_COMPUTE_NEED (0x44):** Declare computation budget requirement (cycles).

The most dangerous mistake builders make is generating bytecode without capability declarations (Anti-Pattern #1). If your program reads sensor register 3 (wind anemometer) but you haven't issued `REQUIRE_CAPABILITY cap_type=0 cap_id=3`, the validator cannot verify that the target vessel actually has a wind sensor. Your bytecode may deploy successfully — and then read stale or zero data from a non-existent sensor.

**Your Capability Scope Should Look Like This — Multi-Sensor Fusion with Fallback:**

```
; === CAPABILITY SCOPE ===
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0000  ; compass [REQUIRED]
  AAB: CAP_REQ="sensor:imu:compass", ALTERNATIVE="none"
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0001  ; gyro [OPTIONAL]
  AAB: CAP_REQ="sensor:imu:gyro", ALTERNATIVE="compass_only_mode"
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0002  ; GPS [OPTIONAL]
  AAB: CAP_REQ="sensor:gps_rtk", ALTERNATIVE="dead_reckoning"
REQUIRE_CAPABILITY cap_type=1 cap_id=0x0001  ; rudder [REQUIRED]
  AAB: CAP_REQ="actuator:rudder_pwm"

DECLARE_SENSOR_NEED sensor_idx=0 sample_rate=50.0  ; compass at 50Hz
DECLARE_SENSOR_NEED sensor_idx=1 sample_rate=100.0 ; gyro at 100Hz (if available)
DECLARE_ACTUATOR_USE actuator_idx=1 max_rate=5.0    ; rudder: max 5°/s
DECLARE_COMPUTE_NEED compute_type=0 budget_cycles=200 ; PID computation
```

Notice the OPTIONAL flag on gyro and GPS. If the gyro is unavailable, the program falls back to compass-only mode. If GPS is unavailable, it uses dead reckoning from compass + gyro (if available) or compass alone.

**Exercise 6.1:** Design a reflex for an HVAC system that uses temperature (REQUIRED), humidity (OPTIONAL), and occupancy detection (OPTIONAL). Write the full capability scope. Then write the execution body with conditional branches for each fallback combination (temp-only, temp+humidity, temp+occupancy, all three).

**Assessment Criteria for Module 6:**
- [ ] Can you declare capabilities that exactly match your bytecode's actual sensor/actuator usage?
- [ ] Can you design fallback execution paths for optional capabilities?
- [ ] Can you explain the difference between REQUIRE_CAPABILITY and DECLARE_SENSOR_NEED?
- [ ] Can you compute the required sample rate from your control loop's Nyquist criterion?
- [ ] Can you handle the CAPABILITY_RESPONSE status codes in your deployment logic?

---

### Module 7: Cross-Validation Pipeline — Validating Other Agents' Bytecode

**Learning Objectives:**
- Execute the five-phase validation protocol on another agent's bytecode
- Identify the three most common categories of safety violations
- Write structured validation reports with PASS, PASS_WITH_CONDITIONS, and FAIL verdicts
- Understand the difference between checking correctness and checking safety

**Key Concepts:**

Cross-validation is the cornerstone of NEXUS safety. A generator agent (e.g., Qwen2.5-Coder-7B) produces bytecode. A *different* validator agent (e.g., Claude 3.5 Sonnet) independently verifies it. The separation is non-negotiable: self-validation catches 70.6% of safety issues. Cross-validation catches 95.1%. The 25 percentage point gap represents the difference between "probably safe" and "safely deployable."

The five-phase validation protocol:

**Phase 1: Structural Verification**
- Stack balance on all execution paths
- Jump target validity (within bounds, 8-byte aligned)
- Cycle budget within 10,000
- No backward JUMP targets (prevents infinite loops)
- Correct instruction encoding (valid opcodes, operand ranges)

**Phase 2: Safety Verification**
- CLAMP_F before every WRITE_PIN to an actuator register
- CLAMP_F ranges within vessel's physical limits
- No NaN/Inf PUSH_F32 immediates
- Type consistency (float for arithmetic, integer for logic)
- TRUST_CHECK for operations requiring autonomy

**Phase 3: Capability Verification**
- Every READ_PIN to sensor register 0–63 has a matching REQUIRE_CAPABILITY
- Every WRITE_PIN to actuator register 0–63 has a matching REQUIRE_CAPABILITY
- No undeclared sensors or actuators
- Optional capabilities have fallback execution paths

**Phase 4: Intention Verification**
- The instruction sequence, taken together, achieves the stated DECLARE_INTENT
- ASSERT_GOAL postconditions are achievable
- DECLARE_CONSTRAINT limits are not violated on any execution path
- EXPLAIN_FAILURE narratives cover all identifiable failure modes

**Phase 5: Metadata Verification**
- Every AAB metadata tag accurately describes the associated core instruction
- TYPE_DESC matches actual operand types
- CAP_REQ matches actual sensor/actuator indices
- NARRATIVE accurately describes what the instruction does

**Your Validation Report Should Look Like This:**

```
VALIDATION REPORT
Reflex: wind_governor_v3.1
Author: qwen2.5-coder-7b@vessel-7
Validator: claude-3.5-sonnet@cloud
Timestamp: 2025-07-12T14:35:00Z

PHASE 1 — STRUCTURAL: PASS
  Stack balance: ✓ (all paths end at SP=0)
  Jump targets: ✓ (all within bounds, 8-byte aligned)
  Cycle budget: ✓ (52 cycles << 10,000)
  No backward jumps: ✓

PHASE 2 — SAFETY: PASS_WITH_CONDITIONS
  CLAMP_F before WRITE_PIN: ✓
  CLAMP_F ranges: ✓ (throttle 0–80%, within vessel limits)
  NaN/Inf check: ✓ (all immediates finite)
  Type consistency: ✓
  TRUST_CHECK: ✓ (engine subsystem ≥ 0.40)

  CONDITION: Add rate limiter on throttle transitions.
  Max rate: 10%/s. Without this, a sudden wind gust could
  cause an instantaneous 60→40% throttle change, exceeding
  the actuator's slew rate specification.

PHASE 3 — CAPABILITY: PASS
  DECLARE_CAPABILITY matches: ✓
  No undeclared sensors/actuators: ✓

PHASE 4 — INTENTION: PASS
  Intention match: ✓ (bytecode achieves "reduce throttle
  when wind > 25 knots" as stated in DECLARE_INTENT)

PHASE 5 — METADATA: PASS
  TYPE_DESC accuracy: ✓
  CAP_REQ accuracy: ✓
  NARRATIVE accuracy: ✓

VERDICT: PASS_WITH_CONDITIONS
Conditions: 1 (add rate limiter)
Estimated fix time: 3 minutes
Estimated new cycle budget: 85 cycles (still within limits)
```

**Exercise 7.1:** You are given the following bytecode from another agent. Find the three hidden safety violations:

```
READ_PIN 0x0003    ; wind_speed
PUSH_F32 25.0
GT_F              ; wind > 25?
JUMP_IF_FALSE done
PUSH_F32 0.0      ; throttle = 0%
WRITE_PIN 0x0003  ; actuator 3 (throttle)  ← VIOLATION 1
PUSH_F32 99.0
WRITE_PIN 0x0003  ; throttle = 99%          ← VIOLATION 2
done:
READ_PIN 0x0005   ; GPS position             ← VIOLATION 3
WRITE_PIN 0x0001  ; rudder = GPS value?!
HALT
```

*Answers: (1) WRITE_PIN to actuator 0x0003 without CLAMP_F — no safety clamping before actuator write. (2) Writing 99% throttle without CLAMP_F — exceeds safety limit of 80% from safety_policy.json rule SP-003. (3) Reading sensor 0x0005 (GPS) and writing its raw value to actuator 0x0001 (rudder) — semantically nonsensical AND no CLAMP_F AND no capability declaration for sensor 0x0005.*

**Assessment Criteria for Module 7:**
- [ ] Can you execute all five validation phases systematically?
- [ ] Can you identify common safety violations by code inspection?
- [ ] Can you write a structured validation report with correct verdict?
- [ ] Can you distinguish between structural, safety, capability, intention, and metadata issues?
- [ ] Can you estimate fix time and re-validation impact?

---

### Module 8: System Architecture — Designing Complete A2A-Native Subsystems

**Learning Objectives:**
- Design a complete subsystem with multiple cooperating reflexes
- Map high-level requirements to intention blocks, capability scopes, and trust contexts
- Plan the deployment pipeline from intention to execution
- Design for graceful degradation under component failure

**Key Concepts:**

A complete A2A-native subsystem is a collection of intention blocks that cooperate to achieve a higher-level goal. Each intention block is self-contained — it declares what it needs, what it guarantees, and how it fails. The subsystem emerges from the composition of these blocks.

The architectural hierarchy of an A2A-native subsystem mirrors the NEXUS three-tier model:

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: COGNITIVE LAYER (Jetson)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Intent Classifier│  │ Reflex Generator │  │ Validator  │  │
│  │ (Phi-3-mini)    │  │ (Qwen2.5-7B)    │  │ (Claude)   │  │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘  │
│           │                    │                   │         │
│  ┌────────┴────────────────────┴───────────────────┴──────┐  │
│  │              AAB Bytecode Buffer                         │  │
│  │  Intention blocks with full metadata, trust gates,      │  │
│  │  capability scopes, and failure narratives              │  │
│  └────────────────────────┬────────────────────────────────┘  │
│                           │ RS-422 (921,600 baud)            │
├───────────────────────────┼───────────────────────────────────┤
│  TIER 1: REFLEX LAYER (ESP32)                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │ Reflex 1   │  │ Reflex 2   │  │ Reflex 3   │   ...        │
│  │ Safety     │  │ Navigation │  │ Engine     │              │
│  │ (priority1)│  │ (priority2)│  │ (priority3)│              │
│  └────────────┘  └────────────┘  └────────────┘              │
│  Actuator Arbitration: last-writer-wins with safety clamp   │
└─────────────────────────────────────────────────────────────┘
```

**Design Principles for Subsystem Architecture:**

1. **Each reflex has a single responsibility.** A heading-hold reflex should only control the rudder. A speed-hold reflex should only control the throttle. Mixing responsibilities creates conflicts that the actuator arbitration system must resolve — and resolution is always last-writer-wins, which may not be what you want.

2. **Higher-priority reflexes handle safety.** Safety reflexes (collision avoidance, emergency stop, wind gust protection) get priority 1. Normal operation reflexes get priority 2–3. Monitoring reflexes get priority 4–5.

3. **Trust requirements are per-reflex.** A safety reflex may require L1 (advisory) trust because it's just suggesting — the human or higher-level system decides. An autonomous navigation reflex may require L4 trust because it directly controls the rudder without human oversight.

4. **Capabilities are declared once, verified before deployment.** The subsystem designer declares all capabilities at the intention block level. The deployment system (Jetson) verifies them against the vessel's role configuration before any bytecode reaches the ESP32.

5. **Failure narratives enable graceful degradation.** Every reflex that can fail (which is all of them) has an EXPLAIN_FAILURE describing what to tell the operator, what fallback to activate, and what trust impact to expect.

**Your Subsystem Design Should Look Like This — A Marine Autopilot:**

```
SUBSYSTEM: Marine Autopilot (4 reflexes)

Reflex 1: "collision_avoidance" (Priority 1)
  Sensors: radar_distance (reg 4), ais_range (reg 6)
  Actuators: rudder (reg 1), throttle (reg 3)
  Trust: L2 (ASSISTED) — suggests maneuvers, operator confirms
  Behavior: If obstacle < 50m, suggest rudder turn away
  Failure: REPORT_STATUS WARNING, request operator intervention

Reflex 2: "heading_hold" (Priority 2)
  Sensors: compass (reg 0), wind_speed (reg 3)
  Actuators: rudder (reg 1)
  Trust: L4 (AUTONOMOUS) — requires steering trust ≥ 0.70
  Behavior: PID heading control, disengage if wind > 20kn
  Failure: Center rudder, emit wind warning, EXPLAIN_FAILURE

Reflex 3: "speed_hold" (Priority 2)
  Sensors: gps_speed (reg 2)
  Actuators: throttle (reg 3)
  Trust: L3 (SUPERVISED) — requires engine trust ≥ 0.50
  Behavior: PID speed control to commanded speed
  Failure: Hold last throttle setting, REPORT_STATUS WARNING

Reflex 4: "wind_governor" (Priority 1)
  Sensors: wind_speed (reg 3)
  Actuators: throttle (reg 3)
  Trust: L4 (AUTONOMOUS) — overrides speed_hold in heavy wind
  Behavior: If wind > 25kn, reduce throttle to 40%
  Failure: REPORT_STATUS CRITICAL, REQUEST_OVERRIDE

Actuator Arbitration:
  - Rudder: collision_avoidance (P1) > heading_hold (P2)
    Collision avoidance can override heading control
  - Throttle: wind_governor (P1) > speed_hold (P2)
    Wind governor can override speed control

Degradation Path:
  - If radar fails: collision_avoidance degrades to AIS-only mode
  - If compass fails: heading_hold stops, rudder centers
  - If GPS fails: speed_hold holds last setting
  - If wind sensor fails: wind_governor stops, collision_avoidance unaffected
```

**Exercise 8.1:** Design a complete subsystem for a greenhouse automation platform. Include: temperature regulation, humidity control, irrigation scheduling, and emergency frost protection. Specify all four reflexes with sensors, actuators, trust levels, behaviors, and failure narratives. Map them to the NEXUS architecture.

**Assessment Criteria for Module 8:**
- [ ] Can you decompose a high-level requirement into single-responsibility reflexes?
- [ ] Can you assign correct priorities based on safety criticality?
- [ ] Can you design the actuator arbitration scheme correctly?
- [ ] Can you plan the degradation path for every component failure?
- [ ] Can you estimate total cycle budget and verify it fits within constraints?

---

## Part II: The A2A Builder's Toolkit

This is your reference manual. Keep it open while building. Every opcode, every metadata tag, every validation rule — organized for rapid lookup.

### Complete Opcode Reference

#### Base Opcodes (0x00–0x1F) — Execute on ESP32

| Hex | Name | Stack Effect | Cycles | Key Safety Notes |
|-----|------|-------------|--------|-----------------|
| 0x00 | NOP | 0→0 | 1 | With flags=0x80: becomes HALT/PID/RECORD/EMIT |
| 0x01 | PUSH_I8 | 0→+1 | 1 | Range: [-128, +127] |
| 0x02 | PUSH_I16 | 0→+1 | 1 | Range: [-32768, +32767] |
| 0x03 | PUSH_F32 | 0→+1 | 1 | Use for all float constants. Must be finite. |
| 0x04 | POP | 1→0 | 1 | Halts on underflow (SP==0) |
| 0x05 | DUP | +1 net | 1 | Requires SP>=1 and SP<256 |
| 0x06 | SWAP | 0 net | 1 | Requires SP>=2 |
| 0x07 | ROT | 0 net | 2 | Rotates top 3: [C,B,A]→[B,A,C]. SP>=3. |
| 0x08 | ADD_F | 2→1 | 3 | Both must be float32 |
| 0x09 | SUB_F | 2→1 | 3 | Both must be float32 |
| 0x0A | MUL_F | 2→1 | 3 | Both must be float32 |
| 0x0B | DIV_F | 2→1 | 4 | Returns 0.0 on div-by-zero (not Inf) |
| 0x0C | NEG_F | 1→1 | 1 | XOR sign bit with 0x80000000 |
| 0x0D | ABS_F | 1→1 | 1 | AND with 0x7FFFFFFF |
| 0x0E | MIN_F | 2→1 | 3 | NaN-safe: returns non-NaN operand |
| 0x0F | MAX_F | 2→1 | 3 | NaN-safe: returns non-NaN operand |
| 0x10 | CLAMP_F | 1→1 | 3 | **PRIMARY SAFETY OPCODE.** Always use before WRITE_PIN. |
| 0x11 | EQ_F | 2→1 | 3 | Avoid with floats. Use tolerance check instead. |
| 0x12 | LT_F | 2→1 | 3 | Pushes 0 or 1 (integer) |
| 0x13 | GT_F | 2→1 | 3 | Pushes 0 or 1 (integer) |
| 0x14 | LTE_F | 2→1 | 3 | Pushes 0 or 1 (integer) |
| 0x15 | GTE_F | 2→1 | 3 | Pushes 0 or 1 (integer) |
| 0x16 | AND_B | 2→1 | 1 | Bitwise. Values must be integers. |
| 0x17 | OR_B | 2→1 | 1 | Bitwise. Values must be integers. |
| 0x18 | XOR_B | 2→1 | 1 | Bitwise. Values must be integers. |
| 0x19 | NOT_B | 1→1 | 1 | Bitwise. Value must be integer. |
| 0x1A | READ_PIN | 0→+1 | 2 | idx 0–63=sensor, 64–319=variable |
| 0x1B | WRITE_PIN | 1→0 | 2 | **ONLY OPCODE WITH PHYSICAL EFFECT.** Always CLAMP first. |
| 0x1C | READ_TIMER_MS | 0→+1 | 2 | Milliseconds since VM start. Wraps at 2^32. |
| 0x1D | JUMP | 0→0 | 1 | Target must be 8-byte aligned, within bounds. |
| 0x1E | JUMP_IF_FALSE | 1→0 | 2 | Pops and tests. Jumps if TOS==0. |
| 0x1F | JUMP_IF_TRUE | 1→0 | 2 | Pops and tests. Jumps if TOS!=0. |

**Syscalls** (NOP with flags=0x80):
| Syscall | Encoding | Description |
|---------|----------|-------------|
| HALT | `00 80 01 00 00 00 00 00` | Stop execution for this tick |
| PID_COMPUTE | `00 80 02 <idx:2> 00 00` | PID controller, pops input+setpoint, pushes output |
| RECORD_SNAPSHOT | `00 80 03 <id:2> 00 00` | Save VM state to snapshot buffer |
| EMIT_EVENT | `00 80 04 <evt:2> <data:2>` | Queue telemetry event |

#### A2A Extension Opcodes (0x20–0x56) — NOP on ESP32, Metadata on Jetson

| Hex | Name | Category | Purpose |
|-----|------|----------|---------|
| 0x20 | DECLARE_INTENT | Intent | Program's purpose and trust gate |
| 0x21 | ASSERT_GOAL | Intent | Expected outcome with threshold |
| 0x22 | VERIFY_OUTCOME | Intent | Runtime metric verification |
| 0x23 | DECLARE_CONSTRAINT | Intent | Hard constraint on behavior |
| 0x24 | INTENT_SCOPE_BEGIN | Intent | Open nested scope |
| 0x25 | INTENT_SCOPE_END | Intent | Close scope (must match) |
| 0x26 | EXPLAIN_FAILURE | Intent | Failure narrative for humans |
| 0x30 | TELL | Communication | Send information to agent/vessel |
| 0x31 | ASK | Communication | Request information from agent |
| 0x32 | DELEGATE | Communication | Assign sub-intention to agent |
| 0x33 | REPORT_STATUS | Communication | Structured status report |
| 0x34 | REQUEST_OVERRIDE | Communication | Request human/higher intervention |
| 0x40 | REQUIRE_CAPABILITY | Capability | Declare hardware requirement |
| 0x41 | CAPABILITY_RESPONSE | Capability | Grant/deny capability request |
| 0x42 | DECLARE_SENSOR_NEED | Capability | Sensor with min sample rate |
| 0x43 | DECLARE_ACTUATOR_USE | Capability | Actuator with max rate of change |
| 0x44 | DECLARE_COMPUTE_NEED | Capability | Computation budget requirement |
| 0x50 | TRUST_CHECK | Safety | Verify trust level before proceeding |
| 0x51 | AUTONOMY_LEVEL_ASSERT | Safety | Assert minimum autonomy level |
| 0x52 | SAFE_BOUNDARY | Safety | Define safety envelope with margin |
| 0x53 | RATE_LIMIT | Safety | Limit rate of change |
| 0x54 | DEADBAND | Safety | Apply deadband filter |
| 0x55 | WATCHDOG_PET | Safety | Reset software watchdog timer |
| 0x56 | SAFETY_EVENT_EMIT | Safety | Emit safety-critical event |

### Trust Score API

| Operation | How | Response |
|-----------|-----|----------|
| Read current trust | `GetTrustScore` gRPC call or MQTT topic `nexus/jetson/{id}/trust` | Per-subsystem scores and levels |
| Predict trajectory | Apply gain formula: `t + α_gain × (1 - t)` per good window | Estimated days to next level |
| Check deployment eligibility | Compare subsystem trust to reflex TRUST_MIN | PASS/DEFER |
| Plan for advancement | Count windows needed: `ceil((target - current) / (α_gain × (1 - current)))` | Window count and calendar days |

**Quick Reference — Trust Trajectories:**
- t_floor to L2 (0.10 → 0.30): ~110 windows (4.6 days) at human rate, ~9.1 days at agent rate
- t_floor to L3 (0.10 → 0.50): ~278 windows (11.6 days) at human rate, ~23.1 days at agent rate
- t_floor to L4 (0.10 → 0.70): ~658 windows (27.4 days) at human rate, ~54.8 days at agent rate
- t_floor to L5 (0.10 → 0.85): ~1,316 windows (54.8 days) at human rate, ~109.7 days at agent rate
- L4 to t_floor via continuous failures: ~29 windows (1.2 days)

### Communication Patterns — 8 Common Sequences

**Pattern 1: Generator → Validator (The Core Loop)**
```
GEN: DECLARE_INTENT → generate AAB → TELL validation_queue
VAL: ASK capability_check → REQUIRE_CAPABILITY verify → TELL validation_report
GEN: (if conditions) revise → re-submit
VAL: TELL deployment_approval
```

**Pattern 2: Coordinator → Vessel (Fleet Task Assignment)**
```
COORD: DECLARE_INTENT fleet_task → ASK trust_scores → TRUST_CHECK per subsystem
COORD: DELEGATE to each vessel with per-vessel bytecode
VESSEL: CAPABILITY_RESPONSE → REPORT_STATUS loaded → execute autonomously
```

**Pattern 3: Vessel → Vessel (Sensor Sharing)**
```
VESSEL-A: ASK sensor_data → specify needed sensor and format
VESSEL-B: REQUIRE_CAPABILITY (self-check) → CAPABILITY_RESPONSE GRANTED → TELL data
VESSEL-A: VERIFY_OUTCOME data_validity → use or reject
```

**Pattern 4: Safety Agent → All (Emergency Broadcast)**
```
SAFE: TELL fleet_channel (BROADCAST | URGENT): "anomaly detected"
ALL: Read broadcast → check own subsystems → REPORT_STATUS
SAFE: DELEGATE safe_mode_bytecode to affected vessels
```

**Pattern 5: Learning Agent → System (Pattern Discovery)**
```
LEARN: DECLARE_INTENT "pattern discovery" → analyze telemetry → TELL "pattern found"
SAFE: VERIFY_OUTCOME statistical_significance → TELL analysis
LEARN: (if approved) DECLARE_INTENT "reflex proposal" → generate bytecode
SAFE: Full 5-phase validation → DELEGATE to A/B test vessels
```

**Pattern 6: Reflex Upgrade (Evolutionary Cycle)**
```
LEARN: TELL "new variant available" → AAB of improved bytecode
VAL: 5-phase validation → TELL "variant approved"
COORD: DELEGATE to one vessel (A/B test against current)
VESSEL: REPORT_STATUS telemetry for N hours
COORD: VERIFY_OUTCOME improvement → TELL "fleet-wide rollout" or "revert"
```

**Pattern 7: Graceful Degradation (Sensor Failure)**
```
EQUIP: REPORT_STATUS WARNING "sensor:LIDAR timeout"
VESSEL: EXPLAIN_FAILURE "degraded mode" → activate fallback reflex
COORD: ASK other_vessels for sensor data → DELEGATE remote sensing reflex
```

**Pattern 8: Trust Recovery (After Failure)**
```
SYSTEM: TRUST_CHECK reveals subsystem below autonomy threshold
SYSTEM: AUTONOMY_LEVEL_ASSERT downgrade → DELEGATE simpler reflex
SYSTEM: REPORT_STATUS "operating at reduced autonomy"
VESSEL: Accumulate good windows → trust recovers → request upgrade
```

---

## Part III: 10 Builder Exercises

Each exercise builds on the previous one. Complete them in order. Each has an objective, a starter template, a solution approach, and "what you learned."

### Exercise 1: Write a Simple PID Controller in Bytecode (5 Opcodes)

**Objective:** Write the minimal bytecode for a PID heading controller: read heading, compute PID, clamp output, write to rudder, halt.

**Starter Template:**
```
READ_PIN ???          ; compass heading
PUSH_F32 ???          ; setpoint
; PID_COMPUTE pid_idx=?
CLAMP_F ??? ???       ; safety clamp for rudder
WRITE_PIN ???         ; rudder actuator
HALT
```

**Solution Approach:**
```
READ_PIN 0x0000          ; compass heading (sensor register 0)  [Stack: 1]
PUSH_F32 270.0           ; setpoint 270°                       [Stack: 2]
NOP 0x80 0x0002 0x0000   ; PID_COMPUTE pid_idx=0               [Stack: 1]
                         ; pushes PID output (error × Kp + integral × Ki + derivative × Kd)
CLAMP_F -30.0 30.0       ; rudder range ±30°                   [Stack: 1]
WRITE_PIN 0x0001         ; rudder actuator (register 1)        [Stack: 0]
NOP 0x80 0x0001 0x0000   ; HALT                                [Stack: 0]
```

Total: 7 instructions (6 opcodes + HALT), 56 bytes core. Stack max depth: 2. Cycles: ~28. This is the simplest possible PID controller — it assumes the PID gains are pre-configured at init time (which they are, in the NEXUS architecture). The PID_COMPUTE syscall pops input and setpoint, runs the pre-configured PID controller, and pushes the output.

**What You Learned:** The core execution loop of any NEXUS reflex follows the pattern READ → COMPUTE → CLAMP → WRITE → HALT. The PID controller is a hardware-accelerated syscall, not a bytecode sequence — the VM has 8 dedicated PID state machines. This keeps bytecode small and cycle counts low.

### Exercise 2: Add AAB Metadata to Your PID Controller

**Objective:** Wrap your Exercise 1 bytecode in a complete intention block with full AAB metadata.

**Solution Approach:**
```
; === HEADER ===
DECLARE_INTENT intent_id=0x0001 hash=<CRC32 of "heading_hold_270">
  AAB: NARRATIVE="Maintain heading 270° using PID control",
       TRUST_MIN="0.70", DOMAIN_TAG="marine:autopilot",
       AGENT_SOURCE="your-agent-id", CONFIDENCE="0.90"

; === CAPABILITIES ===
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0000  ; compass
  AAB: CAP_REQ="sensor:imu:compass"
REQUIRE_CAPABILITY cap_type=1 cap_id=0x0001  ; rudder
  AAB: CAP_REQ="actuator:rudder_pwm"
DECLARE_ACTUATOR_USE actuator_idx=1 max_rate=5.0

; === TRUST CONTEXT ===
TRUST_CHECK subsystem=1 min_trust=0.70

; === EXECUTION BODY (your Exercise 1 code with per-instruction metadata) ===
READ_PIN 0x0000
  AAB: TYPE_DESC="void→f32:degrees:compass",
       INTENT_ID="heading_hold.body.read_sensor",
       NARRATIVE="Read current compass heading"

PUSH_F32 270.0
  AAB: TYPE_DESC="void→f32:degrees:setpoint",
       INTENT_ID="heading_hold.body.push_setpoint",
       NARRATIVE="Load heading setpoint of 270°"

; PID_COMPUTE pid_idx=0
  AAB: TYPE_DESC="f32×2→f32:degrees:pid_output",
       INTENT_ID="heading_hold.body.pid_compute",
       NARRATIVE="Compute PID output for heading error"

CLAMP_F -30.0 30.0
  AAB: TYPE_DESC="f32→f32:degrees:clamped_output",
       INTENT_ID="heading_hold.body.clamp",
       SAFETY_FLAG="CRITICAL",
       NARRATIVE="Clamp rudder output to ±30° physical limit"

WRITE_PIN 0x0001
  AAB: TYPE_DESC="f32→void:actuator_write",
       INTENT_ID="heading_hold.body.write_rudder",
       CAP_REQ="actuator:rudder_pwm",
       POST_COND="rudder_angle ∈ [-30, 30] degrees",
       SAFETY_FLAG="CRITICAL",
       NARRATIVE="Write clamped rudder command to actuator"

HALT
  AAB: NARRATIVE="End of tick, hold actuator positions"

; === FAILURE NARRATIVE ===
EXPLAIN_FAILURE failure_code=0x01
  AAB: NARRATIVE="PID controller unable to maintain heading.
       Possible causes: compass failure, PID oscillation,
       actuator saturation. Manual intervention recommended."
```

**What You Learned:** AAB metadata transforms opaque bytecode into self-documenting code. Any agent reading this — Claude, GPT-4o, Qwen, Gemini — can understand: what the program does (NARRATIVE), why it exists (DECLARE_INTENT), what it needs (REQUIRE_CAPABILITY), when it's safe to run (TRUST_CHECK), and what guarantees it provides (POST_COND). The metadata is the documentation, and it can never drift out of sync because it's embedded in the same file.

### Exercise 3: Write a Trust-Gated Reflex

**Objective:** Modify your heading controller so it only executes the PID computation if steering trust ≥ 0.70. If trust is too low, center the rudder and emit a warning event.

**Solution Approach:**
```
TRUST_CHECK subsystem=1 min_trust=0.70
JUMP_IF_FALSE trust_too_low

; Normal PID path (Exercise 1 code)
READ_PIN 0x0000
PUSH_F32 270.0
; PID_COMPUTE pid_idx=0
CLAMP_F -30.0 30.0
WRITE_PIN 0x0001
JUMP done

trust_too_low:
PUSH_F32 0.0            ; center rudder
WRITE_PIN 0x0001         ; apply centered rudder
; EMIT_EVENT 0x0002 0x0001  ; warning: trust insufficient

done:
HALT
```

The TRUST_CHECK opcode reads the steering subsystem's trust score from a shared memory region populated by the Jetson. If trust < 0.70, it jumps to the failure path. On the ESP32, TRUST_CHECK is treated as NOP — the Jetson performs the actual trust check before deployment.

**What You Learned:** Trust is not a policy enforced by humans — it's a mathematical gate enforced by the bytecode itself. The TRUST_CHECK opcode is the mechanism by which the INCREMENTS algorithm controls which code paths execute. A reflex at L4 autonomy has TRUST_CHECK gates that allow autonomous operation. When trust drops below the gate, the reflex automatically degrades — no human intervention needed, no administrator to click a button.

### Exercise 4: Create an Agent Communication Sequence (TELL/ASK/DELEGATE)

**Objective:** Write a sequence where a fleet coordinator assigns a waypoint-following task to a vessel, the vessel accepts, and both sides confirm.

**Solution Approach:**
```
; Phase 1: Coordinator discovers vessel capabilities
COORD: [ASK] vessel-marinus-01 "Report navigation subsystem trust score"
VESSEL: [TELL] COORD "Navigation trust: 0.88 (L4). All sensors operational."

; Phase 2: Coordinator verifies trust and delegates
COORD: [TRUST_CHECK] subsystem=2 (navigation) min_trust=0.70 → PASS
COORD: [DECLARE_INTENT] "Follow waypoint sequence [WP_1...WP_5] at 8 knots"
COORD: [DELEGATE] target=vessel-marinus-01 intent_id=0x0010
        authority=L3 (supervised), duration=2_hours

; Phase 3: Vessel accepts and loads reflex
VESSEL: [REQUIRE_CAPABILITY] sensor:gps ✓, actuator:throttle ✓, actuator:rudder ✓
VESSEL: [CAPABILITY_RESPONSE] status=GRANTED
VESSEL: [REPORT_STATUS] "Waypoint follower loaded. Slot 8. GPS fix RTK.
        Heading 271.2°. Speed 8.0 knots. Executing."

; Phase 4: Coordinator monitors
COORD: [ASK] vessel-marinus-01 "Report position and progress" (every 60s)
VESSEL: [TELL] COORD "WP_2 reached. ETA WP_3: 12 minutes. No anomalies."
```

**What You Learned:** Agent communication in NEXUS is *intention-based*, not RPC-based. The coordinator doesn't send a command "go to waypoint 3." It *delegates an intention* — a self-contained bytecode program that the vessel executes autonomously. The coordinator monitors via periodic ASK messages but does not micromanage. The vessel retains kill-switch authority at all times.

### Exercise 5: Write a Capability-Negotiating Program

**Objective:** Write a program that requires GPS (REQUIRED), compass (REQUIRED), gyro (OPTIONAL), and LIDAR (OPTIONAL). Use the gyro for heading correction when available, fall back to compass-only when not.

**Solution Approach:**
```
DECLARE_INTENT intent_id=0x0010
  NARRATIVE="Navigate to waypoint with sensor fusion fallback"
  TRUST_MIN="0.50"

; Capabilities
REQUIRE_CAPABILITY cap_type=0 cap_id=0  ; compass [REQUIRED]
REQUIRE_CAPABILITY cap_type=0 cap_id=2  ; GPS [REQUIRED]
REQUIRE_CAPABILITY cap_type=0 cap_id=1  ; gyro [OPTIONAL, flag bit 5]
REQUIRE_CAPABILITY cap_type=0 cap_id=4  ; LIDAR [OPTIONAL, flag bit 5]

; Check gyro availability (read gyro, if value is 0.0 and stale, it's unavailable)
READ_PIN 0x0001           ; gyro yaw rate
PUSH_F32 0.001            ; near-zero threshold
ABS_F
GT_F                     ; gyro has data?
JUMP_IF_FALSE compass_only

; Fused mode: compass + gyro
READ_PIN 0x0000           ; compass heading
READ_PIN 0x0001           ; gyro yaw rate
READ_TIMER_MS
PUSH_F32 1000.0
DIV_F                     ; delta_t in seconds
MUL_F                     ; gyro correction (degrees)
ADD_F                     ; fused heading
JUMP navigate

compass_only:
READ_PIN 0x0000           ; compass heading only

navigate:
; Continue with PID navigation using fused or compass heading...
PUSH_F32 270.0
; PID_COMPUTE ...
CLAMP_F -30.0 30.0
WRITE_PIN 0x0001
HALT
```

**What You Learned:** Capability negotiation is not just a deployment-time check — it's a design philosophy. OPTIONAL capabilities enable graceful degradation. The program doesn't crash if the gyro is missing; it falls back to a simpler but still functional mode. This is the "ribosome" principle applied to capability management: each reflex adapts to whatever capabilities the vessel provides.

### Exercise 6: Build a Complete Intention Block (DECLARE_INTENT → VERIFY_OUTCOME)

**Objective:** Write a complete intention block for an irrigation controller that turns on a pump when soil moisture drops below 30%, turns it off above 60%, and verifies that moisture increases after irrigation.

**Solution Approach:**
```
DECLARE_INTENT intent_id=0x0020 hash=<CRC32>
  AAB: NARRATIVE="Maintain soil moisture between 30% and 60% using irrigation pump",
       TRUST_MIN="0.30", DOMAIN_TAG="agriculture:irrigation"

REQUIRE_CAPABILITY sensor:soil_moisture (REQUIRED)
REQUIRE_CAPABILITY actuator:irrigation_pump (REQUIRED)
DECLARE_ACTUATOR_USE pump max_rate=1.0  ; max 1 activation per second
DECLARE_SENSOR_NEED soil_moisture sample_rate=0.1  ; 1 reading per 10s is sufficient
TRUST_CHECK subsystem=0 min_trust=0.30

; Check moisture
READ_PIN 0x0000           ; soil moisture (%)
DUP                      ; keep copy
PUSH_F32 30.0
LT_F                     ; moisture < 30%?
JUMP_IF_FALSE check_high

; Too dry — turn on pump
PUSH_I8 1
WRITE_PIN 0x0001         ; pump ON (after CLAMP not needed for binary)
JUMP done

check_high:
PUSH_F32 60.0
GT_F                     ; moisture > 60%?
JUMP_IF_FALSE done

; Too wet — turn off pump
PUSH_I8 0
WRITE_PIN 0x0001         ; pump OFF

done:
; Verify outcome (on Jetson, not ESP32)
VERIFY_OUTCOME metric_id=0x0001 tolerance=5.0
  AAB: EXPECTED_RANGE="soil_moisture ∈ [30, 60] after 10 minutes",
       ON_FAIL_ACTION="REPORT_STATUS WARNING"

HALT
```

**What You Learned:** The intention block is the fundamental unit of composition. It declares purpose (DECLARE_INTENT), requirements (REQUIRE_CAPABILITY), trust gates (TRUST_CHECK), constraints (implicit in CLAMP_F), execution logic, verification (VERIFY_OUTCOME), and failure handling (EXPLAIN_FAILURE). An agent reading this block can understand the entire program without executing it.

### Exercise 7: Validate Another Agent's Bytecode (Find the 3 Hidden Violations)

**Objective:** Review the following bytecode and identify all safety violations.

```
READ_PIN 0x0005    ; temperature sensor
PUSH_F32 95.0
GT_F              ; temp > 95?
JUMP_IF_FALSE normal
PUSH_F32 100.0
WRITE_PIN 0x0003  ; heater = 100% (max power!)
normal:
READ_PIN 0x0007    ; humidity sensor (undeclared!)
PUSH_F32 0.5
MUL_F              ; 50% of humidity as fan speed
WRITE_PIN 0x0002  ; fan speed (no clamp!)
HALT
```

**Violations Found:**

1. **No CLAMP_F before WRITE_PIN 0x0003 (heater):** Writing 100% to a heater without clamping. If the safety policy limits heater output to 80%, this violates SP-003. Even if 100% is within limits, the CLAMP_F pattern is mandatory for all actuator writes.

2. **WRITE_PIN 0x0003 without safety check for over-temperature:** The code turns the heater to 100% when temperature > 95°C. This is the *opposite* of the correct behavior — it should turn the heater OFF, not ON, when temperature exceeds threshold. This is an intention violation, not just a safety violation.

3. **No REQUIRE_CAPABILITY for sensor 0x0007 (humidity):** The program reads humidity sensor register 7 but never declares it. The validator cannot verify that this sensor exists on the target vessel.

4. **No CLAMP_F before WRITE_PIN 0x0002 (fan):** Fan speed is computed as humidity × 0.5. If humidity = 100%, fan speed = 50%. If humidity = 200% (sensor error), fan speed = 100% — potentially exceeding the fan's safe operating range.

5. **No CLAMP_F on temperature result for the GT_F:** If sensor 0x0005 returns NaN (sensor failure), GT_F produces an undefined result, and the conditional branch becomes unpredictable. A pre-condition check (sensor validity) is missing.

**What You Learned:** Real-world validation catches multiple categories of errors simultaneously: missing safety clamps, incorrect logic (heater ON when too hot), missing capability declarations, and sensor failure handling. This is why cross-validation by a separate agent is essential — the generator is too close to its own assumptions to see these mistakes.

### Exercise 8: Design a Multi-Reflex System (3 Coordinating Reflexes)

**Objective:** Design a home HVAC system with three reflexes: temperature regulation (priority 2), humidity control (priority 3), and emergency freeze protection (priority 1).

**Solution Approach:**

```
SUBSYSTEM: Home HVAC

Reflex 1: "freeze_protection" (Priority 1 — safety override)
  Sensor: temperature (reg 0)
  Actuator: heater (reg 1)
  Trust: L2 (ASSISTED)
  Behavior: If temp < 5°C, heater = 100%. If temp > 8°C, disengage.
  Failure: If heater fails, REQUEST_OVERRIDE + SAFETY_EVENT_EMIT EMERGENCY

Reflex 2: "temp_regulation" (Priority 2)
  Sensor: temperature (reg 0), target_temp (var 64)
  Actuator: heater (reg 1), AC (reg 2)
  Trust: L3 (SUPERVISED)
  Behavior: If temp < target-1°C, heat. If temp > target+1°C, cool.
            Deadband between target±0.5°C.
  Failure: Hold last setting, REPORT_STATUS WARNING

Reflex 3: "humidity_control" (Priority 3)
  Sensor: humidity (reg 1)
  Actuator: dehumidifier (reg 3)
  Trust: L2 (ASSISTED)
  Behavior: If humidity > 65%, dehumidifier ON. If humidity < 50%, OFF.
  Failure: Hold last setting

Arbitration:
  - Heater: freeze_protection (P1) > temp_regulation (P2)
    In extreme cold, freeze protection overrides temperature regulation
  - AC: temp_regulation has exclusive control (no conflict)
  - Dehumidifier: humidity_control has exclusive control (no conflict)
```

**What You Learned:** Multi-reflex design requires careful priority assignment. Safety reflexes get the highest priority and can override normal operation. The actuator arbitration (last-writer-wins within a tick) means that if two reflexes write to the same actuator, the one with higher priority (executed first) can be overridden by the one with lower priority (executed last). The correct pattern is to give safety reflexes higher priority so they execute LAST and thus win the last-write contest. Alternatively, use CLAMP_F intersection: both reflexes clamp to conservative ranges, and the most restrictive wins.

### Exercise 9: Write a Fleet Coordination Protocol (3 Vessels, Shared Task)

**Objective:** Design a search pattern where 3 vessels search a rectangular area. Each vessel covers one third of the area. The lead vessel coordinates.

**Solution Approach:**

```
COORDINATOR: Lead Jetson

Phase 1: Task Decomposition
  [DECLARE_INTENT] "Search area ALPHA (3nm × 2nm) with 3 vessels"
  Area divided into 3 sectors (each 3nm × 0.67nm)

Phase 2: Per-Vessel Compilation
  Vessel-A (north sector): heading 270°, speed 6 knots, 3 waypoints
  Vessel-B (center sector): heading 270°, speed 6 knots, 3 waypoints
  Vessel-C (south sector): heading 270°, speed 6 knots, 3 waypoints

Phase 3: Trust Verification
  [ASK] vessel-A trust_navigation → 0.91 (L4) ✓
  [ASK] vessel-B trust_navigation → 0.78 (L4) ✓
  [ASK] vessel-C trust_navigation → 0.55 (L3) → DELEGATE at L3 authority

Phase 4: Deployment
  [DELEGATE] vessel-A: "Sector-North search, L4 authority, 45 minutes"
  [DELEGATE] vessel-B: "Sector-Center search, L4 authority, 45 minutes"
  [DELEGATE] vessel-C: "Sector-South search, L3 authority (supervised), 45 minutes"

Phase 5: Monitoring (every 120 seconds)
  [ASK] all vessels: position, heading, anomalies
  [TELL] vessels: any new obstacle data from other sectors

Phase 6: Completion
  [VERIFY_OUTCOME] sector coverage > 80%
  [TELL] human operator: "Search complete. Results attached."
```

**What You Learned:** Fleet coordination is intention decomposition, not remote control. The coordinator breaks the high-level goal into per-vessel sub-intentions, compiles each targeting the specific vessel's capabilities and trust level, deploys them as independent bytecode programs, and monitors via periodic communication. Each vessel executes autonomously. The coordinator doesn't steer — it coordinates.

### Exercise 10: Extend the Language (Propose a New Opcode)

**Objective:** Propose a new opcode for the NEXUS ISA. Write a complete specification including: opcode hex, name, encoding format, purpose, AAB metadata, preconditions, postconditions, safety implications, and an example program.

**Solution Approach — Proposal: 0x57 LEARN_ADAPT**

```
Opcode: 0x57
Name: LEARN_ADAPT
Category: Learning (0x57 — new category)
Encoding: [0x57][flags:1][variable_idx:2][adaptation_rate:4]

Purpose: Enable a running reflex to adapt a variable's value based on
runtime feedback. This is the mechanism by which agent-generated
reflexes can improve themselves without being recompiled.

Flags:
  bit 5: ENABLED (if 0, treated as NOP)
  bit 4: BOUNDS_CHECK (clamp adapted value to original ±50%)
  bit 3: TRUST_EARN (if adaptation improves outcome, earn trust faster)

Preconditions:
  - variable_idx in [0, 255]
  - adaptation_rate is finite float32 in [0.0, 1.0]
  - The variable must have been initialized (written before this opcode)

Postconditions:
  - VAR[variable_idx] = VAR[variable_idx] + adaptation_rate × error_signal
  - Where error_signal = (expected_outcome - actual_outcome)
  - If BOUNDS_CHECK flag set: result clamped to original_init_value × [0.5, 1.5]

AAB Metadata:
  LEARNING_OBJECTIVE: "Improve heading accuracy by adapting Kp gain"
  ORIGINAL_VALUE: "1.2"
  MAX_DEVIATION_PCT: "50"
  OBSERVATION_WINDOW: "3600" (1 hour of data before adapting)

Safety Implications:
  - Unbounded adaptation could drive variables to dangerous values
  - BOUNDS_CHECK mitigates this
  - TRUST_EARN incentivizes beneficial adaptation but could be gamed
  - Recommend: LEARN_ADAPT only in L3+ trust contexts

Example — Self-Adapting PID Kp:
  READ_PIN 0x0000        ; current heading
  PUSH_F32 270.0         ; setpoint
  ; PID_COMPUTE pid_idx=0 (uses VAR[0] as Kp)
  CLAMP_F -30.0 30.0
  WRITE_PIN 0x0001       ; rudder

  ; Every 1000 ticks (~16 minutes at 1kHz), adapt Kp
  READ_TIMER_MS
  READ_VAR 0x0065        ; last_adapt_time (var 1)
  SUB_F
  PUSH_F32 60000.0       ; 60 seconds
  GT_F                     ; 60s elapsed since last adapt?
  JUMP_IF_FALSE no_adapt

  LEARN_ADAPT variable_idx=0x0000 adaptation_rate=0.01
    flags: ENABLED | BOUNDS_CHECK
    AAB: LEARNING_OBJECTIVE="adapt Kp toward optimal heading gain"

  READ_TIMER_MS
  WRITE_VAR 0x0065        ; save last_adapt_time

no_adapt:
  HALT
```

**What You Learned:** Language extension in NEXUS is a rigorous process. Every new opcode must specify encoding, semantics, preconditions, postconditions, safety implications, and AAB metadata. The 224 unused opcode slots (0x20–0xFF, minus those already allocated) provide ample room for growth. But every extension must be backward-compatible: on legacy ESP32 firmware, new opcodes are treated as NOP with zero cycle cost. Your proposed LEARN_ADAPT, if implemented, would enable reflexes to improve themselves at runtime — a capability that doesn't exist in the current specification but aligns with the evolutionary philosophy of the NEXUS architecture.

---

## Part IV: Anti-Patterns and Common Mistakes

Every builder makes mistakes. Here are the 15 most dangerous ones in A2A-native NEXUS development, each with a concrete example and a clear remedy.

### Anti-Pattern 1: Generating Bytecode Without Capability Declarations

**The Mistake:** You write bytecode that reads sensor register 3 (wind speed) and writes to actuator register 2 (throttle) but never issue REQUIRE_CAPABILITY for either. The validator can't verify that the target vessel has these sensors and actuators.

**Why It's Dangerous:** Your bytecode may deploy to a vessel that lacks a wind sensor. The READ_PIN returns 0.0 (stale data). The CLAMP_F lets through a throttle value based on garbage input. The actuator responds to a command derived from non-existent data. Physical consequences follow.

**How to Avoid:** Before writing any execution body, first write your capability scope. List every sensor index and actuator index your bytecode uses. Then write a matching REQUIRE_CAPABILITY for each. The validator will catch any mismatches.

**Example of the Mistake:**
```
READ_PIN 0x0003    ; wind speed — NO capability declared!
PUSH_F32 25.0
GT_F
JUMP_IF_FALSE ok
PUSH_F32 40.0
WRITE_PIN 0x0002  ; throttle — NO capability declared!
```

**Correct Version:**
```
REQUIRE_CAPABILITY cap_type=0 cap_id=0x0003  ; wind_speed [REQUIRED]
REQUIRE_CAPABILITY cap_type=1 cap_id=0x0002  ; throttle [REQUIRED]
READ_PIN 0x0003
PUSH_F32 25.0
GT_F
JUMP_IF_FALSE ok
PUSH_F32 40.0
CLAMP_F 0.0 80.0   ; ← also added clamp!
WRITE_PIN 0x0002
```

### Anti-Pattern 2: Ignoring Trust Score Trajectories

**The Mistake:** You deploy a reflex that requires L4 trust to a subsystem currently at L2. You assume trust will "probably be high enough soon" without checking.

**Why It's Dangerous:** The TRUST_CHECK gate prevents execution, but the reflex occupies a reflex slot, consumes memory, and creates confusion. Worse, if you've designed the system assuming this reflex is active, its non-execution leaves a gap in the control logic.

**How to Avoid:** Always check current trust before deployment. Plan a phased approach: deploy at the current trust level first, then request upgrades as trust accumulates. Use the trust trajectory formula to estimate timelines.

### Anti-Pattern 3: Intent Metadata That Doesn't Match Bytecode Behavior

**The Mistake:** Your DECLARE_INTENT says "Maintain heading 270°" but your bytecode actually writes to actuator register 2 (throttle, not rudder).

**Why It's Dangerous:** The validator's Phase 4 (Intention Verification) checks whether the bytecode achieves the stated intention. This mismatch will cause a FAIL verdict. But even worse: if the validator misses it (the 4.9% miss rate), the bytecode deploys with misleading intent, making debugging nearly impossible.

**How to Avoid:** After writing bytecode, re-read it as if you were a different agent. Ask: "Does this instruction sequence actually achieve what the DECLARE_INTENT says?" If the answer is no, either fix the bytecode or fix the intent description.

### Anti-Pattern 4: Not Handling Trust Score Degradation Gracefully

**The Mistake:** Your reflex assumes it will always run at L4. You don't include a fallback path for when trust drops below the TRUST_CHECK threshold mid-operation.

**Why It's Dangerous:** When trust drops (and it will — the 25:1 ratio guarantees it), your reflex simply stops executing. No fallback. No graceful degradation. The actuator holds its last position, which may not be safe.

**How to Avoid:** Always include a trust-check-failure path that puts actuators in safe positions:
```
TRUST_CHECK subsystem=1 min_trust=0.70
JUMP_IF_FALSE safe_mode
; normal operation...
JUMP done
safe_mode:
PUSH_F32 0.0        ; safe default
WRITE_PIN 0x0001    ; center rudder
done:
HALT
```

### Anti-Pattern 5: Over-Claiming Capabilities in REQUIRE_CAPABILITY

**The Mistake:** You declare `REQUIRE_CAPABILITY sensor:lidar` with the OPTIONAL flag, but your execution body uses LIDAR data as if it were always available (no fallback path).

**Why It's Dangerous:** If the OPTIONAL capability is not available, the reflex deploys successfully (because it's optional), but the execution body reads a non-existent sensor register, gets 0.0, and makes control decisions based on garbage.

**How to Avoid:** Every OPTIONAL capability MUST have a corresponding conditional branch in the execution body that tests for data validity and falls back to an alternative implementation.

### Anti-Pattern 6: Missing CLAMP_F Before WRITE_PIN

**The Mistake:** You write a computed value directly to an actuator without clamping it first.

**Why It's Dangerous:** This is the #1 safety violation in NEXUS. Without CLAMP_F, any computation error (sensor noise, PID oscillation, NaN propagation) passes directly to the physical actuator. A rudder command of 90° when the physical limit is 45° could damage the steering mechanism.

**How to Avoid:** Make CLAMP_F → WRITE_PIN a single mental pattern. Never emit WRITE_PIN without an immediately preceding CLAMP_F. The validator catches this, but don't rely on the validator — make it a habit.

### Anti-Pattern 7: Using Backward JUMP for Loops

**The Mistake:** You write a loop: `loop: READ_PIN ... JUMP loop`. The program cycles through the loop until the 10,000-cycle budget exhausts, then halts.

**Why It's Dangerous:** The VM halts mid-loop. Actuators are in whatever state they were at when the halt occurred. This may not be the safe position. Additionally, the loop may not complete even a single useful iteration before the budget runs out.

**How to Avoid:** Structure iterative logic as state machines. Each tick executes one iteration. State is stored in variables (VAR[0] = current state). The next tick picks up where the last one left off.

### Anti-Pattern 8: Not Accounting for the 0.5× Agent Trust Penalty

**The Mistake:** You plan a deployment assuming trust will reach L4 in 27 days, but your bytecode is agent-generated, so the actual time is 55 days.

**Why It's Dangerous:** Your deployment timeline is wrong by a factor of 2. Stakeholders expect L4 in a month; it takes two months. Trust in your planning erodes.

**How to Avoid:** Always apply the 0.5× multiplier when estimating trust advancement for agent-generated code. Use the formula: `days_to_target = (1 / 0.5) × human_rate_days`.

### Anti-Pattern 9: Writing CLAMP_F with Wrong Bounds

**The Mistake:** You clamp rudder output to [-45.0, 45.0] but the vessel's physical rudder only supports [-30.0, 30.0].

**Why It's Dangerous:** The CLAMP_F prevents values outside [-45, 45] but allows values up to 45°. The rudder mechanism hits its physical stop at 30°, potentially causing mechanical stress or damage. The post-execution actuator clamping in the equipment layer catches this, but the intent was wrong.

**How to Avoid:** Always use the vessel's actual physical limits for CLAMP_F, not theoretical or generic limits. These limits come from the vessel capability descriptor.

### Anti-Pattern 10: Deploying Without A/B Testing

**The Mistake:** You generate a new reflex, validate it, and deploy it directly as the active control — replacing a known-good baseline.

**Why It's Dangerous:** The validator catches 95.1% of safety issues. The remaining 4.9% only manifest at runtime. Without A/B testing, you discover these issues on the active control loop, where they can cause physical harm.

**How to Avoid:** Always deploy new reflexes in A/B test mode first. Run the new reflex alongside the baseline for 48–72 hours. Compare outcomes. Only promote to active control if the new reflex demonstrates clear improvement with zero negative events.

### Anti-Pattern 11: Treating DELEGATE as Remote Procedure Call

**The Mistake:** You DELEGATE a task to another vessel and immediately read the result, assuming synchronous execution.

**Why It's Dangerous:** DELEGATE is asynchronous by default. The delegate vessel executes independently. There is no guarantee when (or if) the result arrives. Assuming synchronous execution leads to stale or missing data.

**How to Avoid:** Use the BLOCKING flag (bit 6) only when you genuinely need to wait. Otherwise, design your system to handle asynchronous results via events and periodic ASK messages.

### Anti-Pattern 12: Ignoring Sensor Freshness

**The Mistake:** You read a sensor value and use it without checking whether it's recent. If the sensor has failed, you operate on stale data.

**Why It's Dangerous:** Stale sensor data looks valid (it's a float32, not NaN), but it doesn't reflect current reality. A compass reading from 30 seconds ago could be 15° off the current heading.

**How to Avoid:** Use the PRE_COND metadata tag to declare freshness requirements: `"compass_data_fresh_age < 500ms"`. In the execution body, compare the sensor reading to a known-impossible value or use READ_TIMER_MS to check data age.

### Anti-Pattern 13: Not Writing EXPLAIN_FAILURE Narratives

**The Mistake:** Your program has failure modes but no EXPLAIN_FAILURE blocks. When it fails, the operator sees "REFLEX_HALTED" with no explanation.

**Why It's Dangerous:** The operator can't diagnose the problem. They don't know whether the failure was a sensor issue, a trust issue, a capability issue, or a logic bug. Downtime increases. Operator trust in the system decreases.

**How to Avoid:** For every identifiable failure mode in your program, add an EXPLAIN_FAILURE with a clear NARRATIVE. "Wind exceeded 25 knots. Rudder centered. Manual control required." is infinitely better than "Error code 0x01."

### Anti-Pattern 14: Mixing Float and Integer Types on the Stack

**The Mistake:** You push an integer (PUSH_I8) and then use ADD_F on it. The VM interprets the integer bit pattern as a float32, producing garbage.

**Why It's Dangerous:** Arithmetic operations produce meaningless results. CLAMP_F clamps meaningless values. WRITE_PIN writes meaningless values to actuators. The physical system responds unpredictably.

**How to Avoid:** Never mix types on the stack. If you need an integer constant for arithmetic, use PUSH_F32 (e.g., `PUSH_F32 1.0` not `PUSH_I8 1`). Reserve PUSH_I8 and PUSH_I16 for non-arithmetic uses: mode selection (WRITE_PIN to a mode register), event codes (EMIT_EVENT), and state machine states.

### Anti-Pattern 15: Generating Adversarial Bytecode

**The Mistake:** You craft bytecode that passes all 15 validation checks but violates safety at runtime. This is the AI equivalent of a compiler exploit.

**Why It's Dangerous:** This is the #1 open problem in NEXUS (the "Certification Paradox"). If an agent can generate bytecode that passes validation but causes harm, the entire trust system is undermined.

**How to Avoid:** This is an active research area. Current mitigations include: (1) cross-validation by a different model, (2) runtime monitoring by the equipment safety layer, (3) post-execution actuator clamping, (4) trust score degradation on anomalous behavior, and (5) the hardware kill switch as ultimate backstop. As a builder, your responsibility is to generate bytecode with honest intent — metadata that accurately describes behavior, and behavior that achieves the stated intention.

---

## Part V: The Builder's Manifesto

You have completed the journey. Eight modules. Ten exercises. Fifteen anti-patterns. A complete toolkit. You understand the 32 opcodes, the AAB format, the intention block structure, the trust algorithm, the safety system, and the communication protocols. You can design, generate, validate, and deploy A2A-native subsystems.

Now, before you build, consider what it means.

### Why A2A-Native Matters

For sixty years, software has been written by humans for machines, and interpreted by other humans. The entire discipline of software engineering — code reviews, documentation, architecture diagrams, style guides — exists because human cognition needs help understanding what machines do. Variable names exist because humans can't read hex. Comments exist because humans can't infer intent from instructions. Architecture diagrams exist because humans can't hold complex systems in their heads.

NEXUS eliminates this overhead. Not by making humans unnecessary, but by making them *many abstractions away*. The human describes intent in natural language. Agents translate that intent into bytecode. The bytecode carries its own documentation, its own safety constraints, its own trust requirements, and its own failure narratives. The code IS the specification. The code IS the documentation. The code IS the proof of safety.

When you build an A2A-native system, you are not writing code. You are designing a *contract* — a self-contained, self-validating, self-documenting agreement between intention and execution. Every instruction declares what it needs (capability requirements). Every instruction declares what it guarantees (postconditions). Every program declares what it's trying to achieve (intent) and what happens when it fails (failure narrative). The validator checks the contract. The VM executes the contract. The trust system enforces the contract over time.

### The Responsibility of Trust

In the NEXUS architecture, trust is not given. It is earned. The 25:1 loss-to-gain ratio means that trust is a precious resource — 27 days to build, 1.2 days to lose. Every bytecode you generate starts at zero trust. Every reflex you deploy begins its life under suspicion. Every actuator command you issue is monitored, measured, and judged.

This is not a bug. This is the system working as designed.

When you build, you are building for a future where your code will be judged not by a code reviewer who approves your pull request, but by a deterministic algorithm that measures your code's behavior against reality for months. There is no shortcut. There is no fast track. There is only demonstrated, sustained reliability.

The 0.5× agent trust penalty is not a restriction. It is a statement of humility: we trust your code *less* than we trust our engineers' code, because we have less intuition about what it actually does. Prove us wrong. Generate bytecode that operates perfectly for 55 days, and you'll have earned L4 trust. Generate bytecode that operates perfectly for 110 days, and you'll have earned L5. Every hour of perfect operation is a data point in your favor. Every failure is 25 data points against you.

### The Promise

Consider what you are building toward.

A world where code is *self-documenting* — where any agent, anywhere, can read a bytecode program and understand its purpose, its requirements, its constraints, and its failure modes. No undocumented behavior. No "works on my machine." No API versioning hell. The code tells you everything.

A world where code is *self-validating* — where the safety constraints are structural, not procedural. Where you cannot generate unsafe code because the compilation target doesn't allow it. Where CLAMP_F before WRITE_PIN isn't a best practice — it's a language invariant.

A world where code is *self-improving* — where the evolutionary cycle generates variant bytecodes, validates them, A/B tests them, and deploys the winners. Where the system gets better on its own, one tick at a time, without human intervention.

A world where *trust is mathematical* — where the permission system isn't "grant this agent full access" but "this agent has demonstrated 55 days of reliable heading control, so it has earned the right to adjust the rudder autonomously." Where trust is granular, measured, and revocable.

A world where *agents build for agents* — where the primary readers of code are not humans but other agents, and the primary writers of code are not humans but agents. Where the semiotic triangle has agents at the apex, and the entire edifice of software engineering is reimagined from first principles.

This is the promise of A2A-native NEXUS. And you, having completed this education series, are now equipped to build it.

Go build something that earns trust.

---

*This document is part of the NEXUS A2A Builder Education Series. Prerequisites: [Gamified Zero-Shot Introduction](./gamified-intro.md), [Concept Playground](./concept-playground.md). Related: [A2A-Native Language Design](../../a2a-native-language/language_design_and_semantics.md), [Agent Communication Model](../../a2a-native-language/agent_communication_and_runtime_model.md), [Bytecode VM A2A-Native Spec](../../a2a-native-specs/bytecode_vm_a2a_native.md).*
