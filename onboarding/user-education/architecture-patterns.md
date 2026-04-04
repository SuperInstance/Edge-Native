# NEXUS A2A Architecture Patterns

## A Pattern Catalog for Agent-to-Agent Distributed Intelligence

**Document ID:** NEXUS-PATTERNS-001
**Version:** 1.0
**Date:** 2025-07-12
**Classification:** User Education — Architectural Reference
**Audience:** System architects, agent developers, integration engineers

---

## How to Read This Document

This catalog contains **25 architectural patterns** organized into **6 categories**. Every pattern follows a consistent structure:

- **Name** — A descriptive, searchable name
- **Intent** — The problem this pattern solves and when to apply it
- **Structure** — Concrete bytecode, protocol messages, or wire-format data showing exactly how NEXUS implements the pattern using real opcodes, trust parameters, and message types
- **Consequences** — Benefits, trade-offs, and failure modes
- **Marine Example** — A concrete scenario from the NEXUS marine reference domain

Patterns reference real NEXUS constants: the 0.5× agent trust multiplier, the 25:1 loss-to-gain trust ratio (α_gain = 0.002, α_loss = 0.05), the trust floor of 0.10, the 6 autonomy levels (L0–L5), the 10,000-cycle VM budget, the 256-entry stack, and the full opcode set (0x00–0x5F including A2A extensions).

Cross-references link to the NEXUS specification suite: `[[specs/firmware/reflex_bytecode_vm_spec.md]]`, `[[specs/safety/trust_score_algorithm_spec.md]]`, `[[specs/safety/safety_system_spec.md]]`, `[[a2a-native-language/language_design_and_semantics.md]]`, and `[[a2a-native-language/agent_communication_and_runtime_model.md]]`.

---

## Category 1: Core Execution

These four patterns form the bedrock of every NEXUS deployment. They govern how a single intention becomes a running reflex on an ESP32, how trust gates that reflex, how the system degrades when resources vanish, and how capability boundaries prevent impossible requests from ever being compiled.

---

### Pattern 1.1 — Intention Block

**Intent:** Structure every deployed reflex as a self-describing, self-verifying unit that encodes *what* it does, *why* it exists, *what* it needs, and *what* happens when it fails. The intention block is the fundamental unit of composition in the A2A-native paradigm — the analogue of a function in C or a class in Python, but designed for agent readers rather than human readers.

**Structure:**

An intention block is an Agent-Annotated Bytecode (AAB) program with six required sections. Each section maps to concrete opcodes and TLV metadata tags. On the ESP32, all A2A opcodes (0x20–0x5F) execute as NOP with zero cycle cost — the metadata is consumed by agents during validation and stripped before deployment.

```
╔══════════════════════════════════════════════════════════════╗
║ INTENTION BLOCK: heading_hold_wind_aware                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ ─── HEADER ─────────────────────────────────────────────────  ║
║ 0x20 0x00 0x0001 0x7A3B2C1D  ; DECLARE_INTENT id=1          ║
║   TLV 0x08: "Maintain heading 270° with wind safety"          ║
║   TLV 0x06: "0.70"             ; TRUST_MIN: Level 3          ║
║   TLV 0x02: "sensor:compass,actuator:rudder,sensor:wind"      ║
║                                                              ║
║ ─── CAPABILITY SCOPE ─────────────────────────────────────── ║
║ 0x40 0x00 0x0001 0x00000000  ; REQUIRE_CAPABILITY compass    ║
║ 0x40 0x00 0x0001 0x00000005  ; REQUIRE_CAPABILITY wind_speed ║
║ 0x40 0x00 0x0002 0x00000000  ; REQUIRE_CAPABILITY rudder     ║
║ 0x43 0x00 0x0000 0x41900000  ; ACTUATOR_USE rudder 18°/s     ║
║                                                              ║
║ ─── TRUST CONTEXT ────────────────────────────────────────── ║
║ 0x50 0x00 0x0001 0x3F000000  ; TRUST_CHECK steering ≥ 0.70   ║
║   → on fail: JUMP :trust_fail                                ║
║                                                              ║
║ ─── EXECUTION BODY ───────────────────────────────────────── ║
║ PUSH_F32    25.0               ; wind limit (knots)           ║
║ READ_PIN    sensor[5]          ; wind_speed                   ║
║ GTE_F                           ; wind ≥ 25?                  ║
║ JUMP_IF_TRUE  :wind_disengage                                ║
║ READ_PIN    sensor[0]          ; compass_heading              ║
║ READ_PIN    sensor[1]          ; target_heading (270°)        ║
║ SYSCALL     PID_COMPUTE pid[0]                               ║
║ CLAMP_F     -30.0 +30.0       ; rudder safe envelope         ║
║ WRITE_PIN   actuator[0]        ; rudder                       ║
║ JUMP        :end                                             ║
║                                                              ║
║ ─── HANDLERS ─────────────────────────────────────────────── ║
║ :wind_disengage                                              ║
║   PUSH_F32 0.0  ; WRITE_PIN rudder  ; EMIT_EVENT wind_off    ║
║ :trust_fail                                                  ║
║   PUSH_F32 0.0  ; WRITE_PIN rudder  ; EMIT_EVENT trust_low   ║
║                                                              ║
║ ─── VERIFICATION & NARRATIVE ────────────────────────────── ║
║ 0x21 0x00 0x0001 0x41F00000  ; ASSERT_GOAL error < 30°       ║
║ 0x26 0x00 0x0001 0x00000000  ; EXPLAIN_FAILURE wind_disengage ║
║   TLV: "Wind exceeded 25 kn. Rudder centered. No trust penalty."║
╚══════════════════════════════════════════════════════════════╝
```

Bytecode lifecycle: Agent generates AAB → validation agent checks intention match (95.1% catch rate) → deterministic compiler strips TLV metadata → 8-byte core instructions → COBS-framed RS-422 at 921,600 baud → ESP32 validates and loads into reflex slot.

**Consequences:**

*Benefits:* Any agent can read, verify, and compose intention blocks without external documentation. The header, capability scope, and trust context serve as machine-readable contracts. Failure narratives are pre-authored by the generating agent, eliminating ambiguity at runtime. Composition of multiple intention blocks follows explicit rules (non-conflicting actuators, compatible trust contexts, union of capabilities).

*Trade-offs:* AAB format has ~525% metadata overhead versus raw 8-byte bytecode — acceptable because AAB lives only in agent-to-agent communication (Jetson memory, cloud storage), never on the ESP32. The intention declaration is a soft contract: it enables agent verification but does not provide formal proof (the validation agent is an LLM, not a theorem prover).

*Failure mode:* If the generating agent produces a misleading intention description that doesn't match the bytecode body, the validation agent may not catch the discrepancy (the 4.9% miss rate). Mitigation: N-version validation using two different agent models.

**Marine Example:** A fishing vessel's cognitive layer generates a "maintain station-keeping position" intention block. The block declares requirements for GPS RTK and bow thruster, sets trust minimum at Level 4 (autonomous), and includes a failure narrative for GPS loss that falls back to dead reckoning from compass + IMU. When deployed to the station-keeping ESP32, the reflex executes at 100 Hz, and the trust system applies the 0.5× agent multiplier — meaning the reflex must demonstrate 54 days of safe operation (instead of 27) before reaching Level 4.

---

### Pattern 1.2 — Trust-Gated Reflex

**Intent:** Bind a reflex's execution to the current INCREMENTS trust score of its target subsystem. The reflex does not execute (or degrades to advisory mode) if trust is below a declared threshold. This pattern prevents immature code from controlling critical hardware, enforcing the principle that *autonomy must be earned, not declared*.

**Structure:**

The TRUST_CHECK opcode (0x50) reads the subsystem's trust score from a shared memory region populated by the Jetson's trust engine. If the score falls below the threshold encoded in operand2 (IEEE 754 float32), execution jumps to a labeled failure handler. The trust score is updated every `window_seconds` (3600s = 1 hour) using the INCREMENTS algorithm:

```
T(t+1) = T(t) + α_gain × (1 - T(t))     if window was good
T(t+1) = T(t) - α_loss × (T(t) - t_floor) if window was bad
```

Where α_gain = 0.002 (or 0.001 for agent-generated code due to the 0.5× multiplier) and α_loss = 0.05.

```
; ─── Trust-gated autopilot with graduated authority ─────────

; Graduated gating: three sections with different trust floors

; === MONITORING (any trust level) ===
AUTONOMY_LEVEL_ASSERT  level=1, subsystem=steering
READ_PIN  compass_heading
WRITE_VAR last_heading
EMIT_EVENT telemetry_heading, last_heading

; === ADVISORY (Level 2+, trust ≥ 0.40) ===
TRUST_CHECK  subsystem=steering, min=0x3ECCCCCD  ; 0.40 float32
  → on fail: JUMP :skip_advisory
READ_PIN  compass_heading
READ_VAR  target_heading
SUB_F     heading_error
; ... compute suggested rudder, do NOT write actuator ...
EMIT_EVENT advisory_rudder, suggested_correction

; === AUTONOMOUS (Level 3+, trust ≥ 0.70) ===
TRUST_CHECK  subsystem=steering, min=0x3F333333  ; 0.70 float32
  → on fail: JUMP :skip_autonomous
READ_PIN  compass_heading
READ_VAR  target_heading
SUB_F     heading_error
SYSCALL   PID_COMPUTE heading_pid
CLAMP_F   -30.0 30.0
WRITE_PIN actuator[0]  ; rudder — ONLY at Level 3+

; === CRITICAL MANEUVER (Level 4+, trust ≥ 0.90) ===
TRUST_CHECK  subsystem=steering, min=0x3F666666  ; 0.90 float32
  → on fail: JUMP :skip_critical
; ... emergency collision avoidance with full rudder authority ...
```

Trust dynamics for agent-generated code:
- Gain time constant: τ_g = 1/α_gain_eff = 1/0.001 ≈ 1316 windows ≈ **54.8 days** to full trust
- Loss time constant: τ_l = 1/α_loss = 1/0.05 = 20 windows ≈ **20 hours** to lose trust
- Net ratio: agent code is **66× slower to gain trust, 22× faster to lose it**

**Consequences:**

*Benefits:* Automatic, continuous trust enforcement without human intervention. Graduated authority within a single reflex enables smooth transitions: a reflex can monitor at any trust level, advise at Level 2, and control at Level 3+. The 0.5× multiplier means agent-generated reflexes earn trust at half the rate of human-authored code, providing a safety buffer for code that no human has directly inspected.

*Trade-offs:* The 54.8-day time to full autonomy for agent code is intentionally conservative. This can frustrate operators who want rapid deployment. The trust check adds one memory read per gate (~2 cycles, negligible). Trust scores are per-subsystem — steering trust is independent of engine trust — so a single subsystem failure does not cascade.

*Failure mode:* A transient sensor glitch that causes one bad window will cost 0.05 × (T - 0.10) trust. If trust was 0.85, that's a loss of 0.0375 — recoverable in ~19 good windows. But a persistent fault causing consecutive bad windows will drain trust to t_floor (0.10) in approximately 29 windows (1.2 days), correctly disabling the reflex.

**Marine Example:** An autonomous trawler deploys an agent-generated net-payload monitoring reflex at trust Level 1. The reflex monitors load cell sensors and emits telemetry. After 14 days of correct monitoring (trust reaches ~0.25), it graduates to Level 2: it now advises the operator about optimal trawl speed. After 45 days (trust ≈ 0.65), it reaches Level 3 and can autonomously adjust throttle to maintain optimal tension. A net snag causes a bad window at day 50, dropping trust from 0.72 to 0.68 — below the Level 3 threshold — so the reflex drops back to advisory-only. The operator is notified and resumes manual throttle control.

---

### Pattern 1.3 — Graceful Degradation

**Intent:** When hardware capabilities become unavailable (sensor failure, communication loss, Jetson offline), the system must continue operating at a reduced capability level rather than failing catastrophically. Each reflex declares fallback behavior for each capability it marks as OPTIONAL. When the capability disappears, the equipment runtime substitutes the fallback automatically.

**Structure:**

Capability requirements have two grades: REQUIRED (bit 5 of flags = 0) and OPTIONAL (bit 5 = 1). When an OPTIONAL capability is unavailable at deployment time, the compiler selects the fallback path encoded in the AAB metadata. When a capability fails at runtime, the equipment runtime substitutes 0.0 for the missing sensor and the reflex's comparison logic routes to the degraded path.

```
; ─── Multi-sensor heading hold with graceful degradation ────

; Capability declarations
0x40 0x20 0x0001 0x00000000  ; REQUIRE compass    [REQUIRED]
0x40 0x20 0x0001 0x00000002  ; REQUIRE gyro       [OPTIONAL]
0x40 0x20 0x0001 0x00000003  ; REQUIRE gps        [OPTIONAL]
0x40 0x00 0x0002 0x00000000  ; REQUIRE rudder     [REQUIRED]

; Check gyro availability (stale data = unavailable)
READ_PIN    sensor[2]        ; gyro_status (0.0 = unavailable, 1.0 = OK)
PUSH_F32    0.5
GT_F
JUMP_IF_FALSE :compass_only

; === FULL FUSION: compass + gyro ===
READ_PIN  sensor[0]          ; compass_heading
READ_PIN  sensor[2]          ; gyro_yaw_rate
READ_PIN  sensor[9]          ; delta_t (from READ_TIMER_MS)
MUL_F                       ; gyro_delta = yaw_rate × dt
ADD_F                       ; fused = compass + gyro_delta
JUMP :pid_compute

; === DEGRADED: compass only ===
:compass_only
READ_PIN  sensor[0]          ; compass_heading only

; === PID COMPUTE (shared by both paths) ===
:pid_compute
READ_VAR  target_heading
SUB_F     heading_error
SYSCALL   PID_COMPUTE heading_pid
CLAMP_F   -30.0 30.0
WRITE_PIN actuator[0]

; Heartbeat degradation states
; HEALTHY  → WARN (2 misses) → DEGRADED (5 misses) → FAILSAFE (10)
; In FAILSAFE: ESP32 continues loaded reflexes autonomously
```

Communication degradation follows the heartbeat escalation protocol. The ESP32 monitors heartbeats from the Jetson (HEARTBEAT message type 0x01). Missed heartbeats trigger state transitions:

| State | Condition | Behavior |
|-------|-----------|----------|
| HEALTHY | 0–1 missed | Full operation, trust updates flowing |
| WARN | 2 missed | Non-essential services shed |
| DEGRADED | 5 missed | No new deployments, existing reflexes continue |
| FAILSAFE | 10 missed | Fully autonomous on loaded reflexes, no trust updates |

**Consequences:**

*Benefits:* The system never goes dark. Even with complete Jetson failure, ESP32 nodes continue executing their last-loaded reflex programs. The 99.97% availability figure from 10,000-hour simulations comes directly from this pattern: ESP32s are ribosomes — they execute without understanding and without supervision. Sensor fallbacks mean a single sensor failure doesn't disable the entire reflex.

*Trade-offs:* Degraded modes may produce worse control performance (compass-only heading hold drifts faster than compass+gyro fusion). The operator must be aware of current degradation state. When the Jetson recovers, trust updates resume — but if trust decayed to t_floor during the outage, the reflex may need to rebuild trust before regaining autonomous authority.

*Failure mode:* If ALL optional AND required sensors fail simultaneously, the reflex receives 0.0 for all sensor inputs. The PID controller computes zero error and outputs zero correction — the vessel drifts. This is intentional: zero output is the safe default for rudder and throttle.

**Marine Example:** A research vessel operating 50 nautical miles offshore loses its GPS RTK link. The heading-hold reflex degrades from "compass + gyro + GPS fusion" to "compass + gyro only." The Jetson emits a TELL message to the fleet: "vessel-oceanus GPS degraded, position accuracy reduced to ±5m." Ten minutes later, the gyro IMU reports stale data (I2C bus lockup). The reflex degrades further to compass-only heading hold. The operator sees the degradation chain in real-time. When the I2C bus resets (hardware watchdog), the gyro comes back online and the reflex automatically re-enters full-fusion mode.

---

### Pattern 1.4 — Capability-Bounded Execution

**Intent:** Before an agent compiles bytecode for a target vessel, it must verify that the vessel possesses every hardware capability the reflex requires. This prevents the deployment of reflexes that reference non-existent sensors, impossible actuator ranges, or unsupported compute features. The capability descriptor is the contract between intention and hardware.

**Structure:**

Every vessel publishes a capability descriptor at boot via the `DEVICE_IDENTITY` message (type 0x01) and `AUTO_DETECT_RESULT` (type 0x1B). The descriptor is a JSON document describing sensors, actuators, compute resources, and constraints:

```json
{
  "agent_id": "esp32-AABBCCDDEEFF",
  "vessel_id": "vessel-marinus-01",
  "capabilities": {
    "sensors": ["compass_3axis", "gps_rtk", "imu_9dof", "wind_anemometer"],
    "actuators": ["rudder_pwm", "throttle_relay", "anchor_winch"],
    "reflex_slots": {"total": 50, "used": 7, "available": 43},
    "tick_rate_hz": [100, 500, 1000]
  },
  "constraints": {
    "max_cycle_budget": 10000,
    "max_stack_depth": 256,
    "max_bytecode_size": 4000,
    "safety_policy_version": "2.0.0"
  }
}
```

The compilation pipeline performs capability negotiation before generating bytecode:

```
Agent: "I need lidar for obstacle avoidance"
Vessel: "I have no lidar. Available: compass, gps, imu, wind"
Agent: "I'll use radar (sensor[8]) instead, or skip obstacle avoidance"
Vessel: "I have radar. Compiling with sensor[8] = radar_dist_m"
```

At deployment time, the Jetson checks every REQUIRE_CAPABILITY opcode against the vessel's descriptor. If any REQUIRED capability is missing, deployment is rejected with a structured error. OPTIONAL capabilities trigger fallback compilation.

The equipment runtime enforces physical bounds at runtime:
- Cycle budget: VM halts if > 10,000 cycles per tick
- Stack depth: VM halts if > 256 entries
- Actuator range: post-execution clamping to configured min/max
- Bytecode size: rejected if > 4,000 bytes

**Consequences:**

*Benefits:* Impossible reflexes are caught at compilation time, never reaching the ESP32. The capability descriptor enables fleet-wide deployment: the same high-level intention can be compiled differently for each vessel based on its specific hardware. A reflex designed for a fully-equipped vessel can be automatically degraded for a sensor-limited vessel by falling back to available sensors.

*Trade-offs:* The capability descriptor is a static snapshot at boot. If hardware is hot-plugged mid-operation, the descriptor may become stale. The system handles this through `AUTO_DETECT_RESULT` re-scans triggered by `ROLE_ASSIGN` messages, but there is a brief window of inconsistency. The max_bytecode_size of 4,000 bytes limits reflex complexity — complex multi-sensor fusion reflexes may need to be split into multiple simpler reflexes.

*Failure mode:* If the capability descriptor is corrupted (e.g., stale firmware reports capabilities it doesn't actually have), a reflex may compile targeting non-existent hardware. The equipment runtime's stale-data detection (sensor reading = 0.0 after 500ms) catches this at runtime, routing to the degraded path.

**Marine Example:** A fleet commander on the cloud Jetson wants to deploy an "underwater obstacle avoidance" reflex to a coastal patrol vessel. The reflex requires a depth sounder (sensor: sonar_depth). The cloud agent queries the patrol vessel's capability descriptor and discovers the vessel has no sonar. The agent recompiles the reflex to use radar-only obstacle detection (reduced capability) and marks the depth-sounder requirement as OPTIONAL with a compass-radar fallback. The modified reflex deploys successfully.

---

## Category 2: Agent Communication

These four patterns govern how agents communicate through bytecode rather than traditional message-passing. In NEXUS, agents emit intentions, not commands. The bytecode ISA is the universal language of coordination.

---

### Pattern 2.1 — Generator-Validator Pair

**Intent:** Separate the agent that *creates* a reflex from the agent that *validates* it. This N-version approach catches safety issues that the generator misses. Self-validation catches 70.6% of safety issues; cross-validation by a different model catches 93.3% (GPT-4o) or 95.1% (Claude 3.5 Sonnet). The 24.5-percentage-point improvement justifies the additional latency.

**Structure:**

The generation and validation pipeline runs as a two-agent relay. Each agent has a different system prompt, a different model, and different incentives:

```
┌──────────────────────┐    ┌──────────────────────┐    ┌───────────┐
│  GENERATOR AGENT     │    │  VALIDATOR AGENT     │    │ DETERMIN- │
│  Qwen2.5-Coder-7B    │───▶│  Claude 3.5 Sonnet   │───▶│ ISTIC     │
│  Role: CREATE        │    │  Role: VERIFY        │    │ COMPILER  │
│  System Prompt:      │    │  System Prompt:      │    │ (C code)  │
│   - Output schema    │    │   - Safety checklist │    │           │
│   - Available sensors│    │   - Trust thresholds │    │ Strip     │
│   - Safety rules     │    │   - Actuator limits  │    │ metadata  │
│   - Few-shot examples│    │   - Attack patterns  │    │ → 8-byte  │
│                      │    │                      │    │ bytecode  │
│  Output: AAB reflex  │    │  Output: PASS/REJECT │    │           │
│  Latency: ~29s       │    │  + structured report │    │ Latency:  │
│  VRAM: 4.2GB Q4_K_M  │    │  Latency: ~3s (cloud)│    │ ~1ms      │
└──────────────────────┘    └──────────────────────┘    └───────────┘
```

The validator agent performs a structured safety analysis encoded as a TELL message to the generator:

```
TELL channel=generation_feedback {
  "reflex_id": "heading_hold_v12",
  "verdict": "PASS_WITH_CONDITIONS",
  "risk_score": 0.12,
  "catches": [
    {
      "severity": "WARNING",
      "location": "instruction_14 (CLAMP_F)",
      "issue": "Rudder limit 30° exceeds COLREGs safe maneuvering limit of 25°",
      "recommendation": "CLAMP_F -25.0 25.0"
    },
    {
      "severity": "INFO",
      "location": "capability_scope",
      "issue": "No wind speed fallback declared for heading hold in open ocean",
      "recommendation": "Add SAFE_BOUNDARY wind_speed_max=25_knots"
    }
  ],
  "trust_impact": "Agent-generated: 0.5× gain multiplier applies",
  "deployment_ready": true
}
```

The generator agent incorporates the validator's feedback, re-generates the reflex, and re-submits. This loop typically converges in 1–3 iterations.

**Consequences:**

*Benefits:* The generator-validator pair catches 95.1% of safety issues — a 24.5-point improvement over self-validation. The two agents have different training data, different architectures, and different biases, providing genuine N-version diversity. The structured report enables automated re-generation, creating a closed-loop safety pipeline.

*Trade-offs:* The additional validation step adds ~3 seconds of latency (cloud round-trip for Claude 3.5 Sonnet). For emergency reflexes (collision avoidance), this may be unacceptable — the system can bypass validation for safety-critical responses that use only pre-validated patterns. The validator is itself an LLM with a 4.9% miss rate — it cannot guarantee 100% safety.

*Failure mode:* If both agents share the same blind spot (e.g., neither recognizes a novel failure mode), the issue passes through. Mitigation: periodic human review of deployed reflexes and Monte Carlo safety simulations on the cloud.

**Marine Example:** A fishing fleet's cloud agent generates a "adaptive trawl depth" reflex that uses sonar data to adjust net depth based on fish school position. The generator produces bytecode with a CLAMP_F range of 0–100m for the net winch. The validator catches that the vessel's winch has a physical limit of 30m and the safety policy limits net depth to 25m in the current fishing zone. The validator returns PASS_WITH_CONDITIONS, the generator adjusts to CLAMP_F 0 25, and the reflex deploys successfully.

---

### Pattern 2.2 — Ask-Tell-Delegate Chain

**Intent:** Agents coordinate through three fundamental communication primitives — TELL (push information), ASK (pull information), and DELEGATE (push a sub-intention). These opcodes enable multi-step coordination chains where Agent A delegates a task to Agent B, Agent B asks Agent C for data, Agent C tells Agent B the answer, and Agent B tells Agent A the result. Each step is a bytecode instruction that becomes an EMIT_EVENT syscall on the ESP32.

**Structure:**

The three communication opcodes share a common format but differ in semantics:

```
; TELL: Push information to another agent (fire-and-forget)
0x30 0x00 0x0002 0x00000001  ; TELL channel=2 (cognitive), event_type=OBSTACLE_FOUND
  TLV 0x08: "Obstacle detected 25m ahead at bearing 045°"
  TLV 0x02: "link:jetson:cognitive"

; ASK: Request information, optionally block for response
0x31 0x01 0x0002 0x000001F4  ; ASK channel=2, blocking=true, timeout=500ms
  TLV 0x08: "What is the current COLREGs situation for vessel ahead?"
  TLV 0x02: "link:jetson:cognitive"
  → Response placed on stack by event handler

; DELEGATE: Assign a sub-intention to another agent
0x32 0x00 0x0003 0x00000005  ; DELEGATE target=agent_3, intent_id=5
  TLV 0x08: "Perform starboard maneuver to avoid collision"
  TLV: AUTHORITY_LEVEL=L3, SCOPE=collision_avoidance
```

A concrete Ask-Tell-Delegate chain for cross-vessel obstacle avoidance:

```
; === ON VESSEL A (scout vessel with lidar) ===

; Step 1: Vessel A's lidar detects obstacle
READ_PIN  sensor[12]        ; lidar_nearest_dist_m
PUSH_F32  30.0              ; obstacle threshold
LT_F                         ; dist < 30m?
JUMP_IF_FALSE :no_obstacle

; Step 2: Vessel A TELLs the fleet about the obstacle
TELL  channel=fleet_broadcast
      message="OBSTACLE: dist=22m bearing=045 type=unknown"

; Step 3: Vessel A DELEGATEs evasion to the lead vessel
DELEGATE  target=vessel-lead
          intent="suggest_evasion_route"
          scope=navigation

; === ON VESSEL B (lead vessel, receives delegation) ===

; Step 4: Vessel B ASKs its cognitive layer for route options
ASK   channel=cognitive
      question="evasion_options_for_obstacle_at_045_dist_22m"
      timeout=2000ms
  → cognitive layer responds with route on stack

; Step 5: Vessel B TELLs the fleet the recommended route
TELL  channel=fleet_broadcast
      message="EVASION_ROUTE: starboard_30_deg_then_resume"
```

**Consequences:**

*Benefits:* The TELL/ASK/DELEGATE primitives provide a complete coordination vocabulary that maps naturally to the bytecode ISA. Delegation is remote intention deployment, not RPC — the delegate executes autonomously without callback. The deterministic VM means the delegating agent can predict the delegate's behavior given knowledge of its sensor inputs.

*Trade-offs:* ASK with blocking=true can stall the reflex pipeline if the cognitive layer is slow (LLM inference at 17.2 tok/s). The system mitigates this with timeout defaults and fallback behavior. Delegation across vessels introduces latency (10–100ms over WiFi, 20–80ms over Starlink) that may be unacceptable for time-critical maneuvers.

*Failure mode:* If an ASK times out, the requesting reflex must have a fallback path. If a DELEGATE fails (target vessel unreachable), the delegating agent must handle the failure — typically by executing a local fallback reflex.

**Marine Example:** A three-vessel fishing fleet operates in formation. Vessel A (starboard wing) has the best radar coverage and detects an approaching cargo ship at 2 nautical miles. Vessel A TELLs the fleet about the contact. Vessel B (lead vessel) ASKs its cognitive layer for a COLREGs-compliant evasion plan. The cognitive layer determines Rule 15 (crossing situation) applies and recommends a starboard turn. Vessel B DELEGATEs the maneuver plan to all vessels. Each vessel's ESP32 loads the evasion reflex and executes it autonomously — no further coordination needed.

---

### Pattern 2.3 — Fleet Broadcast

**Intent:** When information must reach all vessels simultaneously — weather alerts, navigation hazards, mission changes, trust score updates — a single agent broadcasts a structured message that every vessel's equipment runtime interprets and acts upon. Fleet broadcast uses the MQTT topic hierarchy as the distribution mechanism, with QoS 2 (exactly-once delivery) for critical messages.

**Structure:**

```
MQTT Topic Hierarchy:
  nexus/fleet/{fleet_id}/broadcast/alerts         ← weather, navigation hazards
  nexus/fleet/{fleet_id}/broadcast/navigation      ← route changes, waypoints
  nexus/fleet/{fleet_id}/broadcast/trust           ← trust score updates
  nexus/fleet/{fleet_id}/broadcast/mission         ← mission phase changes
```

A weather alert broadcast from the fleet manager:

```
TELL channel=fleet_broadcast/broadcast/alerts {
  "msg_type": "WEATHER_ALERT",
  "severity": "WARNING",
  "issuer": "fleet-manager-cloud",
  "timestamp": "2026-03-29T14:30:00Z",
  "fleet_id": "fleet-north-sea-01",
  "content": {
    "condition": "Gale warning — wind forecast 35 knots from NW in 2 hours",
    "recommended_action": "All vessels reduce speed to 40%, seek shelter heading 180°",
    "reflex_deployment": {
      "name": "gale_preparation",
      "trigger": "wind_speed > 25 knots",
      "actions": ["throttle = 40%", "heading = 180°", "anchor standby"],
      "trust_min": 0.50
    },
    "trust_impact": "none — fleet-wide environmental condition"
  }
}
```

Each vessel's Jetson receives the broadcast, validates the reflex deployment, and if the vessel's trust score permits, deploys the gale_preparation reflex to the appropriate ESP32 nodes. The trust score synchronization uses CRDTs (Conflict-free Replicated Data Types) with Last-Writer-Wins merge — bounded staleness < 1 second via MQTT QoS 2.

**Consequences:**

*Benefits:* Single-message coordination across the entire fleet. The broadcast carries both information and action — the reflex deployment means every vessel can respond identically and autonomously. CRDT-based trust synchronization ensures all vessels converge on the same trust state within 1 second, even if some vessels temporarily lose connectivity.

*Trade-offs:* MQTT QoS 2 has higher overhead than QoS 0 (fire-and-forget). For non-critical telemetry, QoS 0 is preferred. The reflex in the broadcast must be validated before deployment — this takes ~3 seconds per vessel if validation is done locally. Pre-validated reflex templates (stored in the fleet's shared reflex library) eliminate this delay.

*Failure mode:* If the MQTT broker fails, fleet-wide communication is lost. Each vessel continues operating on its last-loaded reflexes (FAILSAFE mode). The Raft-based Jetson cluster ensures broker failover within 300ms (2-of-3 Jetsons must ACK).

**Marine Example:** The North Sea fishing fleet's cloud manager receives a gale warning from the UK Met Office. It broadcasts a WEATHER_ALERT to all 12 vessels with a pre-validated "gale_preparation" reflex. Each vessel's Jetson receives the alert, checks its current trust scores, and deploys the reflex to throttle and steering ESP32s. Within 30 seconds of the alert, all 12 vessels are executing identical gale-response programs autonomously.

---

### Pattern 2.4 — Emergency Override

**Intent:** When an agent detects an imminent safety hazard — collision risk, equipment failure, environmental danger — it must be able to override any lower-priority reflex immediately. The emergency override uses the hardware kill switch as the ultimate backstop, with software-level overrides layered above it. The override pattern uses the REQUEST_OVERRIDE opcode (0x34) and the SAFETY_EVENT_EMIT opcode (0x56).

**Structure:**

Emergency overrides operate at three priority levels, each with different authorities:

```
┌──────────────────────────────────────────────────────────────┐
│ Level 0: HARDWARE KILL SWITCH (mechanical MOSFET)           │
│ Response: <1ms. All actuators → safe state. No software     │
│ override possible. ISR in IRAM, interrupt priority level 1.  │
│ Trigger: Physical button, watchdog timeout (MAX6818, 1.0s), │
│          current overload (INA219).                          │
├──────────────────────────────────────────────────────────────┤
│ Level 1: FIRMWARE ISR GUARD                                 │
│ Response: <0.1ms. Actuator clamping, state machine          │
│ transition NORMAL→DEGRADED→SAFE_STATE→FAULT.                │
│ Trigger: Stack overflow, cycle budget exceeded, NaN/Inf     │
│ detected in actuator output.                                │
├──────────────────────────────────────────────────────────────┤
│ Level 2: AGENT EMERGENCY OVERRIDE                           │
│ Response: 1 tick (1ms). Reflex preemption via priority.     │
│ Trigger: REQUEST_OVERRIDE opcode, SAFETY_EVENT_EMIT,        │
│          trust-veto (Ubuntu mechanism).                      │
└──────────────────────────────────────────────────────────────┘
```

A collision avoidance emergency override in bytecode:

```
; === EMERGENCY COLLISION AVOIDANCE REFLEX ===
; Priority: 1 (HIGHEST) — preempts all other reflexes

DECLARE_INTENT  id=emergency_avoid
  trust_min=0.30  ; Low trust floor for emergencies
  safety_class=CRITICAL

READ_PIN  sensor[12]       ; lidar_nearest_dist_m
PUSH_F32  15.0             ; collision threshold
LT_F                       ; dist < 15m?
JUMP_IF_FALSE :no_emergency

; EMERGENCY: Full rudder turn + throttle reduction
SAFETY_EVENT_EMIT  severity=CRITICAL, event_code=COLLISION_IMMINENT
  TLV: "Obstacle at {dist}m. Executing emergency starboard turn."

PUSH_F32  -45.0            ; full rudder deflection
WRITE_PIN actuator[0]      ; rudder → -45° (starboard)
PUSH_F32  20.0             ; minimum safe speed
WRITE_PIN actuator[1]      ; throttle → 20%

REQUEST_OVERRIDE  authority_level=EMERGENCY
  TLV: reason="Collision imminent at 15m"
  TLV: safety_implication="Full rudder, reduced throttle"

EMIT_EVENT  collision_avoidance_activated

:no_emergency
NOP
```

**Consequences:**

*Benefits:* The three-level override hierarchy ensures safety at every layer. The hardware kill switch is software-independent — even a completely corrupted firmware cannot prevent the mechanical MOSFET from disconnecting actuators. Agent-level emergency overrides require only trust Level 1 (0.30), ensuring that even immature reflexes can protect the vessel in emergencies.

*Trade-offs:* Emergency overrides bypass the trust-gating pattern. A reflex at trust Level 1 can command full rudder deflection during an emergency — this is intentional but means the emergency path has less trust validation than normal operation. The Ubuntu trust-veto mechanism (where a lower-priority reflex with higher trust can block a higher-priority reflex) adds complexity to the arbitration logic.

*Failure mode:* If the emergency reflex itself contains a bug (e.g., turns the wrong direction), the firmware ISR guard's actuator clamping provides a backstop. If even the clamping is misconfigured, the hardware kill switch provides the final backstop.

**Marine Example:** A cargo vessel's autopilot reflex (trust Level 4, priority 3) is holding course 270°. A recreational speedboat suddenly appears 12m ahead on a collision course. The emergency collision avoidance reflex (trust Level 1, priority 1) detects the obstacle via lidar, preempts the autopilot, and commands full starboard rudder (-45°) with throttle reduction to 20%. The autopilot reflex is suspended. After the danger passes (lidar reads >50m for 5 seconds), the emergency reflex relinquishes control and the autopilot resumes.

---

## Category 3: Safety

These four patterns implement NEXUS's non-negotiable safety model. Safety is not a feature — it is the foundation upon which all other patterns are built.

---

### Pattern 3.1 — Defense in Depth

**Intent:** No single safety mechanism is sufficient. Every potentially dangerous operation is protected by at least four independent layers of safety, each with different failure modes, different implementations, and different authorities. A failure in one layer is caught by the next. This pattern encodes IEC 61508 SIL-2 principles directly into the architecture.

**Structure:**

The four safety layers map to the NEXUS three-tier architecture:

```
LAYER 1 — HARDWARE (t_fault < 1ms, mechanical, software-independent)
├── Kill switch: mechanical MOSFET disconnecting all actuators
├── Pull-down resistors: actuators default to safe position on signal loss
├── Current sensing: INA219 on every actuator circuit, overcurrent → kill
└── Watchdog: MAX6818 hardware watchdog, 0x55/0xAA pattern, 1.0s timeout

LAYER 2 — FIRMWARE (t_fault < 0.1ms, ISR-level, runs on ESP32)
├── ISR guard: interrupt-level safety check before every actuator write
├── Software watchdog: FreeRTOS task monitoring, 500ms timeout
├── Actuator clamping: post-execution CLAMP_F on all actuator registers
├── NaN/Inf guard: Theorem 3 guarantee — no non-finite value reaches actuators
└── Stack overflow guard: bounds check on every PUSH, VM halts on violation

LAYER 3 — SUPERVISORY (t_fault < 100ms, task-level, FreeRTOS on ESP32)
├── State machine: NORMAL → DEGRADED → SAFE_STATE → FAULT transitions
├── Heartbeat monitoring: HEALTHY → WARN → DEGRADED → FAILSAFE
├── Trust score enforcement: reflex activation gated by TRUST_CHECK
├── Safety policy: 10 global + 72 COLREGs rules encoded in safety_policy.json
└── Observation monitoring: anomaly detection on sensor data streams

LAYER 4 — APPLICATION (t_fault = human-speed, agent-level, Jetson/cloud)
├── Generator-validator pair: 95.1% safety catch rate
├── Trust-gated autonomy: L0–L5 with 25:1 loss-gain ratio
├── A/B reflex testing: new reflexes shadow-tested before activation
├── Kill-switch availability check: reflex must confirm kill switch is armed
└── Provenance tracking: every deployed reflex has author, validator, hash
```

A concrete example: what happens when a reflex tries to command rudder = 50° (exceeding the physical limit of 45°):

1. **Agent validation (Layer 4):** Validator catches CLAMP_F limit of 50° during AAB review — REJECT
2. **If validator misses:** Compiler detects limit exceeds vessel capability descriptor — REJECT
3. **If compiler misses:** ESP32 actuator clamping applies configured max of 45° — CLAMPED
4. **If clamping misconfigured:** Hardware pull-down resistors ensure rudder returns to center on signal fault
5. **If all software fails:** Kill switch disconnects rudder actuator power entirely

**Consequences:**

*Benefits:* No single point of failure can cause a safety violation. The layers are implemented in different technologies (mechanical, firmware ISR, FreeRTOS task, LLM agent) with different failure modes, providing true diversity. The INCREMENTS trust algorithm adds a temporal dimension: even if all static checks pass, a reflex must demonstrate safe behavior over time before earning higher autonomy.

*Trade-offs:* Four layers of safety add complexity and latency. The hardware kill switch adds $8–12 to the BOM. The ISR guard consumes ~2μs per tick — negligible at 1ms tick rate but measurable. The safety policy JSON (864 lines, 72 COLREGs rules) must be kept in sync with regulatory changes.

*Failure mode:* A systematic failure that affects all four layers simultaneously is considered impossible given their implementation diversity. The only scenario would be physical destruction of the vessel, which is outside the safety system's scope.

**Marine Example:** During a storm, an agent-generated autopilot reflex experiences a buffer overflow in the PID integral term, causing it to request rudder = 90° (double the physical limit). Layer 4 (agent validation) catches the overflow in the integral windup check. If it missed it, Layer 2 (firmware clamping) limits the output to 45°. If the clamping configuration was corrupted, the hardware pull-down resistor returns the rudder servo to its mechanical center. If the servo itself fails, the INA219 current sensor detects the overcurrent and triggers the kill switch MOSFET. The vessel is safe.

---

### Pattern 3.2 — Fail-Safe Default

**Intent:** When a reflex cannot determine the correct action — sensor data is missing, computation produces an unexpected result, or the trust score is ambiguous — it must default to a known-safe state. In NEXUS, the safe default is always **zero output**: rudder = 0° (center), throttle = 0% (off), anchor = 0m (retracted). The safe state is enforced by the hardware pull-down resistors even when all software fails.

**Structure:**

The fail-safe default is implemented at three levels:

```
; === LEVEL 1: Bytecode-level safe defaults ===

; Every reflex begins by establishing safe defaults
PUSH_F32  0.0
WRITE_PIN actuator[0]  ; rudder = 0° (safe center)
PUSH_F32  0.0
WRITE_PIN actuator[1]  ; throttle = 0% (safe off)

; Only modify actuators AFTER safety checks pass
TRUST_CHECK  subsystem=steering, min=0.70
JUMP_IF_FALSE :safe_state

READ_PIN  sensor[0]   ; compass_heading
; ... normal control logic ...
WRITE_PIN actuator[0]  ; rudder = computed value

:safe_state
; Explicitly write safe values (redundancy with start-of-tick defaults)
PUSH_F32  0.0
WRITE_PIN actuator[0]
PUSH_F32  0.0
WRITE_PIN actuator[1]

; === LEVEL 2: Firmware actuator clamping ===
; After VM execution, firmware applies configured min/max:
; rudder: CLAMP [-45, 45]
; throttle: CLAMP [0, 100]
; These limits are loaded from safety_policy.json at boot

; === LEVEL 3: Hardware fail-safe ===
; PWM signal loss → pull-down resistor → servo to center
; Relay coil de-energize → normally-open contact → circuit open
; Motor driver enable pin LOW → motor coast to stop
```

Sensor stale-data substitution follows the same principle:

```
; If sensor[5] (wind_speed) has no update in 500ms:
; Equipment runtime substitutes 0.0

; Reflex handles the substitution:
READ_PIN  sensor[5]        ; wind_speed (may be 0.0 if stale)
PUSH_F32  0.1              ; minimum plausible wind speed
LT_F                       ; wind < 0.1? (stale or calm)
JUMP_IF_TRUE :wind_unknown

; Wind data is valid — proceed with wind-aware control
; ...

:wind_unknown
; Use safe default: assume worst case (high wind → conservative control)
PUSH_F32  40.0             ; conservative throttle (reduced from 80%)
WRITE_PIN actuator[1]
```

**Consequences:**

*Benefits:* The system always degrades to a known state, never to an unknown one. Zero output is physically safe for all NEXUS actuators: centered rudder allows the vessel to drift naturally, zero throttle stops propulsion, retracted anchor is the default position. Hardware enforcement means the safe default is maintained even during complete software failure.

*Trade-offs:* The safe default of "do nothing" may not be the optimal response in all situations. A drifting vessel in a shipping lane may be in more danger than a vessel actively maneuvering. The system mitigates this by allowing higher-trust reflexes to override the safe default when they have sufficient confidence.

*Failure mode:* If a vessel's mechanical design does not support the zero-output safe state (e.g., a rudder that doesn't return to center without power), the hardware fail-safe is compromised. The vessel capability descriptor must declare this limitation, and the equipment runtime must enforce a custom safe state.

**Marine Example:** A moored monitoring buoy runs on 2 ESP32 nodes with no Jetson. The bilge pump reflex monitors a water level sensor. When the sensor fails (corroded probe), the equipment runtime substitutes 0.0. The reflex reads 0.0 and, following the fail-safe pattern, activates the bilge pump at full power (safe default: pump = ON when water level is unknown). This is a domain-specific inversion of the default-zero principle — the system prompt for this vessel specifies that the safe state for the bilge pump is ON, not OFF.

---

### Pattern 3.3 — Trust Decay Recovery

**Intent:** When a reflex's trust score drops due to a bad event, the system must provide a structured recovery path that doesn't require human intervention. The INCREMENTS algorithm's asymmetric gain/loss ratio (25:1) means trust decays 22× faster than it builds. Recovery requires demonstrating consistent safe behavior over many good windows. The trust decay recovery pattern formalizes this process and provides visibility into the recovery trajectory.

**Structure:**

Trust score dynamics for agent-generated code:

```
T(t+1) = T(t) + 0.001 × (1.0 - T(t))       [good window, agent 0.5× multiplier]
T(t+1) = T(t) - 0.050 × (T(t) - 0.10)       [bad window, standard α_loss]

Recovery time from trust floor (0.10) to Level 2 (0.40):
  T rises as 1 - 0.9 × e^(-0.001 × t)
  Solving 0.40 = 1 - 0.9 × e^(-0.001 × t):
  t = -1000 × ln(0.667) ≈ 405 windows ≈ 16.9 days

Recovery from a single bad event at T=0.85:
  Loss: ΔT = 0.05 × (0.85 - 0.10) = 0.0375
  New T: 0.8125
  Recovery time to 0.85: ~38 windows ≈ 1.6 days
```

The recovery monitoring reflex runs on the Jetson and reports recovery progress:

```
; === TRUST RECOVERY MONITOR ===
; Runs at 1 Hz on the Jetson, not on ESP32

; Read current trust for steering subsystem
ASK  channel=trust_engine
     question="current_trust steering"
     → trust_current on stack

; Read trust 24 hours ago
ASK  channel=trust_engine
     question="trust_history steering hours=24"
     → trust_24h_ago on stack

; Compute recovery rate
SUB_F     trust_delta      ; positive = recovering
PUSH_F32  0.001            ; minimum recovery rate (1 good window)
LT_F                       ; recovery too slow?
JUMP_IF_TRUE :stalled_recovery

; Report recovery progress
TELL  channel=fleet_broadcast/trust
     message="RECOVERY: steering trust {trust_current}, "
            "Δ24h = +{trust_delta}, ETA to Level 3: {eta_days} days"

:stalled_recovery
; Trust is not recovering — alert operator
TELL  channel=operator_alert
     message="TRUST_STALLED: steering trust {trust_current}, "
            "no improvement in 24h. Possible persistent fault."
REQUEST_OVERRIDE  authority_level=ADVISORY
     reason="Trust recovery stalled — human inspection recommended"
```

**Consequences:**

*Benefits:* The recovery process is transparent and predictable. Given the INCREMENTS parameters, recovery time is mathematically determined — operators can calculate the exact number of good windows needed to reach any target trust level. The asymmetric ratio (25:1) is intentional: it prevents the system from quickly regaining trust after a failure, ensuring that the failure is not a fluke.

*Trade-offs:* The 16.9-day recovery from trust floor to Level 2 (for agent-generated code) is a long time. During recovery, the subsystem operates in manual or advisory mode, reducing the vessel's autonomy. This is the price of safety: the system must earn trust slowly because trust, once broken, reveals a real weakness.

*Failure mode:* If the underlying fault that caused the trust loss is not fixed, every window will be bad and trust will remain at t_floor (0.10). The stalled-recovery detection catches this and alerts the operator. If the operator ignores the alert, the subsystem remains at L0 (manual) indefinitely — which is safe, just not useful.

**Marine Example:** A fishing vessel's net-tension monitoring reflex experiences a calibration drift, causing it to trigger false "net snag" events. Trust drops from 0.78 to 0.55 over three bad windows. The operator identifies the calibration issue, recalibrates the load cell, and the reflex resumes correct operation. The trust recovery monitor shows: "Steering trust 0.55, Δ24h = +0.02, ETA to Level 3 (0.70): ~7.5 days." After 8 days of consistent good windows, trust reaches 0.71 and the reflex regains Level 3 autonomous authority.

---

### Pattern 3.4 — Adversarial Resistance

**Intent:** Protect the NEXUS system from adversarial bytecode — code that passes validation but violates safety at runtime. This is the AI equivalent of a compiler exploit: an agent might craft bytecode that uses obscure instruction sequences to produce dangerous outputs. The adversarial resistance pattern layers multiple defenses: bytecode verification, cycle-budget enforcement, actuator clamping, and anomaly detection.

**Structure:**

```
┌──────────────────────────────────────────────────────────────┐
│ DEFENSE LAYER 1: STATIC BYTECODE VERIFICATION                │
│ Deterministic compiler rejects:                               │
│ ├── NaN/Inf immediates (Theorem 3)                           │
│ ├── Jump targets outside program bounds                       │
│ ├── Stack imbalance (pushes ≠ pops across all paths)         │
│ ├── Cycle budget violation (> 10,000 cycles)                 │
│ ├── Undefined opcodes (0x60+)                                │
│ ├── Write to sensor registers (read-only)                     │
│ └── Missing HALT at program end                              │
├──────────────────────────────────────────────────────────────┤
│ DEFENSE LAYER 2: RUNTIME SANDBOXING                           │
│ ESP32 VM enforces:                                           │
│ ├── Stack depth ≤ 256 (bounds check on every PUSH)           │
│ ├── Cycle counter ≤ 10,000 per tick (VM halt on exceed)      │
│ ├── Variable index ≤ 256 (bounds check on every READ/WRITE)  │
│ ├── Sensor register index ≤ 64 (bounds check)                │
│ ├── Actuator register index ≤ 64 (bounds check)              │
│ └── No heap allocation (zero malloc/free in production)       │
├──────────────────────────────────────────────────────────────┤
│ DEFENSE LAYER 3: OUTPUT VALIDATION                            │
│ Post-execution checks before actuator write:                  │
│ ├── CLAMP_F to configured min/max (hardware-safe range)       │
│ ├── isfinite() check on all actuator values                  │
│ ├── Rate-of-change limit (maximum delta per tick)             │
│ ├── Safety policy compliance (COLREGs, SOLAS rules)           │
│ └── Consistency check: actuator output matches intention      │
├──────────────────────────────────────────────────────────────┤
│ DEFENSE LAYER 4: ANOMALY DETECTION                            │
│ Jetson-side behavioral monitoring:                            │
│ ├── BOCPD (Bayesian Online Change Point Detection) on outputs │
│ ├── Statistical anomaly detection on sensor readings          │
│ ├── Trust score trend analysis (unexpected decline)           │
│ └── Cross-vessel consistency check (fleet behavior drift)     │
└──────────────────────────────────────────────────────────────┘
```

A concrete adversarial bytecode and how each layer catches it:

```
; ADVERSARY ATTEMPT: Overflow PID integral to produce large rudder command
; The adversary hopes the integral term will saturate and produce 100°

; Layer 1 (static check) CATCHES: none — this bytecode is syntactically valid
; Layer 2 (sandbox)    CATCHES: none — uses legitimate opcodes within budget
; Layer 3 (output)     CATCHES: CLAMP_F -45.0 45.0 limits rudder to ±45°
; Layer 4 (anomaly)    CATCHES: BOCPD detects sudden large output change

; Additional defense: the PID_COMPUTE syscall has built-in anti-windup
; Maximum integral accumulation is bounded by the PID state machine
; The safety policy limits rudder authority to ±30° at trust Level 3
```

**Consequences:**

*Benefits:* Four independent defense layers make it extremely difficult to craft adversarial bytecode that produces a dangerous output. Even if an adversary finds a novel attack vector, Layer 3 (actuator clamping) provides a hard physical limit that cannot be bypassed in software. The anomaly detection layer (Layer 4) adapts to novel attack patterns over time.

*Trade-offs:* The defense layers add computational overhead: static verification adds ~1ms compilation time, runtime sandboxing adds ~2μs per tick, output validation adds ~1μs per tick. Anomaly detection on the Jetson consumes ~2% of the 40 TOPS compute budget. The system cannot defend against physical attacks (cutting cables, GPS spoofing) through software alone.

*Failure mode:* A sophisticated adversary who knows the exact CLAMP_F limits could craft bytecode that hovers just below the threshold (44.9° rudder repeatedly). This is caught by the rate-of-change limit and the anomaly detection layer. The ultimate defense is that the INCREMENTS trust algorithm will detect the unusual behavior as "bad windows" and reduce trust, eventually disabling the adversarial reflex entirely.

**Marine Example:** During a fleet exercise, a red-team agent attempts to deploy bytecode to a vessel that would cause it to deviate from its patrol route. The static verifier rejects the bytecode because it attempts to write to a sensor register (read-only). The red team refines the attack to use only valid instructions. The validator agent (Claude 3.5 Sonnet) catches that the bytecode's declared intention ("maintain patrol route") does not match its actual behavior (heading offset +15° from patrol route). The attack fails at Layer 1. Even if it passed, Layer 3 would clamp the heading offset to the safety policy's maximum deviation, and Layer 4's BOCPD would detect the anomalous behavior within 3 ticks.

---

## Category 4: Learning

These four patterns govern how the NEXUS system improves its reflexes over time — from raw observation to pattern discovery to A/B testing to deployment. The learning pipeline is: Observe → Record → Discover Patterns → Synthesize Reflex → A/B Test → Deploy.

---

### Pattern 4.1 — Observe-Record-Discover

**Intent:** Continuously observe the vessel's sensor data and actuator responses, record snapshots at configurable intervals, and discover patterns using five automated algorithms. This pattern is the foundation of the learning pipeline: without observation and recording, there is no data for pattern discovery. Without pattern discovery, there are no new reflex candidates.

**Structure:**

The observation-recording loop runs on the ESP32 at every tick, with minimal overhead:

```
; === OBSERVATION REFLEX (runs every tick at 1 kHz) ===
; Priority: 5 (LOWEST) — never preempts control reflexes

DECLARE_INTENT  id=observation_loop
  trust_min=0.10  ; Any trust level
  safety_class=NORMAL

; Record sensor and actuator snapshot every N ticks
READ_TIMER_MS               ; current tick count
READ_VAR     last_snapshot_tick
SUB_F        ticks_since_snapshot
PUSH_F32     100.0          ; snapshot every 100 ticks (100ms)
GTE_F
JUMP_IF_FALSE :no_snapshot

; === SNAPSHOT: 16 values (sensor + actuator + state) ===
SYSCALL  RECORD_SNAPSHOT
  ; Records to ring buffer:
  ;   sensor[0..5]: compass, gps_lat, gps_lon, wind_speed, wind_dir, depth
  ;   actuator[0..2]: rudder, throttle, anchor
  ;   state[0..2]: trust_score, mode, tick_count
  ;   meta: timestamp, reflex_active_flags
  ; Ring buffer: 10,000 entries × 16 float32 × 4 bytes = 640 KB

WRITE_VAR  last_snapshot_tick  ; update last snapshot time

:no_snapshot
NOP
```

Pattern discovery runs on the Jetson's cognitive layer using five algorithms:

| Algorithm | Input | Output | Marine Use Case |
|-----------|-------|--------|-----------------|
| Cross-correlation | Sensor pairs | Correlation coefficients (r ∈ [-1, 1]) | "Wind speed and heading error correlate at r=0.82" |
| BOCPD | Time series | Change points (timestamps) | "Heading error pattern changed at 14:30" |
| HDBSCAN | Multivariate snapshots | Cluster labels | "Three distinct operating modes detected" |
| Temporal mining | Event sequences | Frequent subsequences | "Wind > 25 → throttle reduction → stable heading" |
| Bayesian reward inference | State-action-outcome tuples | Reward function | "Throttle 60% maximizes fuel efficiency at wind 10–15 kn" |

When a pattern is discovered, the Jetson's LLM synthesizes a candidate reflex:

```
DISCOVERY: Cross-correlation between wind_speed and heading_error
  Correlation: r = 0.82 (p < 0.001)
  Pattern: When wind_speed > 20 knots, heading error increases by 15°
  Candidate reflex: "Increase PID gains when wind > 20 knots"
  → Send to A/B testing pipeline
```

**Consequences:**

*Benefits:* The system continuously improves without human intervention. The five algorithms cover different pattern types (correlation, change points, clustering, temporal sequences, reward optimization), providing comprehensive coverage. The ring buffer provides a 16.7-minute sliding window of data at 100ms intervals — sufficient for discovering most operational patterns.

*Trade-offs:* The ring buffer consumes 640 KB of the ESP32's 8 MB PSRAM — significant but acceptable. Pattern discovery is computationally expensive on the Jetson (~15% of GPU compute for continuous BOCPD). The system can only discover patterns in data it observes — if a critical sensor is missing, the pattern is invisible. Pattern discovery can produce false positives (spurious correlations), which is why every candidate reflex undergoes A/B testing before deployment.

*Failure mode:* If the observation reflex fails (stack overflow, cycle budget exceeded), snapshots stop recording and pattern discovery operates on stale data. The mitigation is the observation reflex's low priority and minimal cycle cost (~12 cycles per tick, 0.12% of budget).

**Marine Example:** A long-line fishing vessel operates in the North Sea for 30 days. The observation reflex records sensor snapshots every 100ms. After 10 days, the cross-correlation algorithm discovers that when sea state (derived from accelerometer variance) exceeds 3.0, the heading-hold PID's integral term winds up, causing overshoot. The Jetson's LLM synthesizes a candidate reflex: "Disable PID integral term when sea state > 3.0." The reflex enters A/B testing.

---

### Pattern 4.2 — A/B Reflex Testing

**Intent:** Before a new or modified reflex is deployed to production, it must be shadow-tested against the current production reflex. The A/B testing pattern runs both reflexes simultaneously — the production reflex writes to actuators, while the candidate reflex writes to a shadow output register — and compares their outputs over a statistically significant number of ticks.

**Structure:**

The A/B test infrastructure uses a special reflex slot that mirrors production actuator writes:

```
; === A/B TEST MANAGER (runs on Jetson, controls ESP32 A/B slots) ===

; Phase 1: DEPLOY candidate to shadow slot
TELL  channel=esp32-deploy
     message="DEPLOY_REFLEX slot=shadow reflex=candidate_sea_state_pid"

; Phase 2: COLLECT shadow vs production outputs for N ticks
; Production reflex writes to actuator[0] (rudder) — controls the vessel
; Shadow reflex writes to actuator[32] (shadow_rudder) — recorded only

ASK  channel=esp32-telemetry
     question="compare_outputs production=actuator[0] shadow=actuator[32] "
               "window=3600 ticks"
  → comparison_metrics on stack:
  ;   mean_absolute_error: |production - shadow| averaged
  ;   max_deviation: maximum |production - shadow|
  ;   correlation: r(production, shadow)
  ;   safety_violations: count of shadow output > CLAMP_F limits

; Phase 3: EVALUATE candidate quality
PUSH_F32  2.0              ; max acceptable MAE (degrees)
GT_F                         ; MAE > 2.0?
JUMP_IF_TRUE :reject_candidate

PUSH_F32  5.0              ; max acceptable deviation
GT_F                         ; max_deviation > 5.0?
JUMP_IF_TRUE :reject_candidate

PUSH_F32  0.0              ; zero safety violations required
GT_F                         ; violations > 0?
JUMP_IF_TRUE :reject_candidate

; Phase 4: PROMOTE candidate to production
TELL  channel=esp32-deploy
     message="SWAP_REFLEX production_slot=0 with shadow_slot=32"
TELL  channel=fleet_broadcast/trust
     message="REFLEX_PROMOTED: sea_state_pid v1 → production"
JUMP :done

; Phase 5: REJECT candidate
:reject_candidate
TELL  channel=generator_agent
     message="A/B_REJECT: sea_state_pid v1 MAE={mae} max_dev={max_dev}"
TELL  channel=fleet_broadcast/trust
     message="REFLEX_REJECTED: sea_state_pid v1 did not meet quality bar"

:done
NOP
```

**Consequences:**

*Benefits:* New reflexes are validated against real-world data, not just simulation. The shadow-testing approach means the candidate reflex cannot affect the vessel's actual behavior — safety is maintained throughout the test. The statistical comparison (MAE, max deviation, correlation) provides objective quality metrics. The 0.5× trust multiplier applies to the promoted reflex, ensuring agent-generated improvements still earn trust slowly.

*Trade-offs:* A/B testing requires the shadow reflex to use actuator registers 32–63 (shadow register space), reducing the number of available actuator channels. The test duration must be long enough to cover representative operating conditions — typically 1–4 hours of accumulated tick data. If the vessel operates in a narrow regime during testing, the candidate may pass the A/B test but fail in other conditions.

*Failure mode:* If the shadow reflex causes a cycle budget overflow (unlikely since it mirrors the production reflex's structure), the VM halts and the production reflex continues unaffected. If the candidate produces outputs identical to production (MAE ≈ 0), the test is inconclusive — the candidate adds no value and is rejected.

**Marine Example:** The candidate reflex from Pattern 4.1 ("disable PID integral when sea state > 3.0") enters A/B testing. The shadow reflex runs alongside the production heading-hold PID for 4 hours (14,400 ticks at 1 Hz). Results: MAE = 0.8° (below 2.0° threshold), max deviation = 3.2° (below 5.0° threshold), zero safety violations. The correlation between production and shadow outputs is r = 0.94. The candidate is promoted to production. Trust starts at 0.10 (t_floor) with the 0.5× agent multiplier and must build from scratch.

---

### Pattern 4.3 — Trust-Gated Learning

**Intent:** Not all vessels, subsystems, or operating conditions are equally suited for autonomous learning. The trust-gated learning pattern restricts the learning pipeline's autonomy based on the current trust level. At low trust, the system only observes and records. At medium trust, it discovers patterns but does not deploy them. At high trust, it synthesizes and deploys reflexes autonomously. This prevents the learning system from making dangerous modifications when the base system is not yet proven stable.

**Structure:**

```
; === TRUST-GATED LEARNING CONTROLLER (Jetson-side) ===

; Read current trust for the target subsystem
ASK  channel=trust_engine
     question="current_trust steering"
  → trust_steering on stack

; === LEVEL 1: OBSERVE ONLY (trust < 0.40) ===
PUSH_F32  0.40
LT_F
JUMP_IF_FALSE :level_2

; At low trust: only observe and record
TELL  channel=observation
     message="MODE: OBSERVE_ONLY — recording snapshots, no discovery"
JUMP :done

; === LEVEL 2: OBSERVE + DISCOVER (trust 0.40–0.70) ===
:level_2
PUSH_F32  0.70
LT_F
JUMP_IF_FALSE :level_3

; At medium trust: observe, discover, but do NOT deploy
TELL  channel=observation
     message="MODE: OBSERVE_DISCOVER — running all 5 discovery algorithms"
TELL  channel=discovery
     message="RUN_ALGORITHMS: cross_correlation, bocpd, hdbscan, temporal, bayesian"
TELL  channel=reporting
     message="DISCOVERY_RESULTS: send to operator for review"
; Discovered patterns are reported to the operator, not auto-deployed
JUMP :done

; === LEVEL 3: OBSERVE + DISCOVER + TEST (trust 0.70–0.90) ===
:level_3
PUSH_F32  0.90
LT_F
JUMP_IF_FALSE :level_4

; At high trust: observe, discover, A/B test, but require operator approval
TELL  channel=observation
     message="MODE: OBSERVE_DISCOVER_TEST"
TELL  channel=discovery
     message="RUN_ALGORITHMS + SYNTHESIZE_CANDIDATES"
TELL  channel=ab_testing
     message="START_SHADOW_TEST for candidate_reflex"
; After A/B test passes, ASK operator for deployment approval
ASK  channel=operator
     question="APPROVE_DEPLOY candidate={reflex_name} ab_results={metrics}"
     timeout=3600000ms  ; 1 hour operator response
JUMP :done

; === LEVEL 4: FULL AUTONOMY (trust ≥ 0.90) ===
:level_4
TELL  channel=observation
     message="MODE: FULL_AUTONOMY"
TELL  channel=discovery
     message="RUN_ALGORITHMS + SYNTHESIZE + AUTO_DEPLOY"
; Reflexes are automatically promoted after passing A/B test
; Trust-gated: 0.5× multiplier still applies to new reflexes
; Human notification (not approval required):
TELL  channel=operator
     message="AUTO_DEPLOYED: {reflex_name} trust={trust} ab_score={score}"

:done
NOP
```

**Consequences:**

*Benefits:* The learning system's autonomy scales with demonstrated competence. A vessel that has proven stable operation over weeks earns the right to self-improve. A newly deployed vessel starts in observe-only mode and gradually unlocks learning capabilities. This prevents the "learner's paradox" — an unstable system trying to improve itself.

*Trade-offs:* At Level 1 (observe only), the system accumulates data but cannot act on it — a resource cost with no immediate benefit. At Level 3, operator approval for deployment introduces human latency (~minutes to hours). At Level 4, full autonomy removes human oversight — the 0.5× trust multiplier and A/B testing are the only safety nets.

*Failure mode:* If the trust score is inflated (e.g., the vessel operates in easy conditions and earns high trust, then encounters challenging conditions), the learning system may deploy reflexes that are optimized for easy conditions but fail in hard ones. The A/B testing phase catches this if the test covers representative conditions, but there is a risk of distribution shift.

**Marine Example:** A new autonomous patrol vessel starts with all subsystems at trust Level 0 (manual). For the first 2 weeks, it operates in observe-only mode, recording sensor data while the operator steers manually. After the steering subsystem reaches trust Level 2 (0.40) at day 18, pattern discovery activates. At day 32, steering trust reaches Level 3 (0.70) and the system begins A/B testing candidate reflexes. The operator approves the first learned reflex (improved wind-compensation PID) at day 38. By day 83, steering trust reaches Level 5 (0.99) and the system operates with full learning autonomy.

---

### Pattern 4.4 — Pattern-to-Reflex Compilation

**Intent:** When a pattern discovery algorithm identifies a repeatable behavior, the system must translate that pattern into executable bytecode. This pattern bridges the gap between abstract statistical patterns (correlation coefficients, change points) and concrete reflex programs (bytecode sequences). The compilation uses the LLM agent as the synthesis engine, constrained by the same system prompt that governs all reflex generation.

**Structure:**

The compilation pipeline transforms a discovered pattern into a deployed reflex in six steps:

```
Step 1: PATTERN EXTRACTION
  BOCPD discovers change point at 14:30 — heading error variance increases
  Cross-correlation finds r=0.82 between wind_speed and heading_error
  → Pattern: "Heading control degrades when wind_speed > 20 knots"

Step 2: PATTERN ENCODING (structured representation)
  {
    "pattern_id": "P-2026-03-29-001",
    "type": "conditional_gain_adjustment",
    "trigger": {"sensor": "wind_speed", "operator": "GT", "threshold": 20.0},
    "action": {"parameter": "heading_pid.kd", "value": 0.8, "reason": "increase damping"},
    "evidence": {
      "correlation_r": 0.82,
      "change_point_p": 0.001,
      "observation_count": 288000,  // 8 hours at 10 Hz
      "confidence": 0.94
    }
  }

Step 3: REFLEX SYNTHESIS (Qwen2.5-Coder-7B, 17.2 tok/s, ~29s)
  System prompt includes:
    - Pattern as input context
    - Safety rules from safety_policy.json
    - Current vessel capability descriptor
    - Few-shot examples of similar patterns
    - GBNF grammar constraints for valid JSON reflex output

  → Candidate AAB reflex with:
    - DECLARE_INTENT: "Adaptive PID damping for high wind"
    - TRUST_CHECK: steering ≥ 0.40
    - EXECUTION BODY: conditional Kd adjustment based on wind speed
    - SAFE_BOUNDARY: rudder ∈ [-30, 30]
    - EXPLAIN_FAILURE: narrative for each failure mode

Step 4: SAFETY VALIDATION (Claude 3.5 Sonnet, ~3s)
  Verifies:
    - Intention matches bytecode behavior
    - Actuator limits within vessel capability
    - Trust context appropriate for the action
    - No adversarial instruction sequences
    - Rate limits on parameter changes

Step 5: A/B TESTING (1–4 hours shadow testing)
  Shadow reflex runs alongside production reflex
  Statistical comparison determines promotion/rejection

Step 6: DEPLOYMENT WITH TRUST SEEDING
  Promoted reflex starts at t_floor (0.10)
  0.5× agent multiplier applies
  Trust builds through INCREMENTS: τ_g ≈ 54.8 days to full trust
```

**Consequences:**

*Benefits:* The pattern-to-reflex pipeline creates a closed learning loop: the system observes its own behavior, identifies improvement opportunities, and implements those improvements autonomously. The LLM agent provides the "creativity" needed to translate abstract patterns into concrete control strategies. The safety validation and A/B testing gates ensure that only genuinely beneficial reflexes reach production.

*Trade-offs:* Each pattern-to-reflex cycle takes approximately 4–5 hours (29s generation + 3s validation + 1–4 hours A/B testing). This is slow by machine standards but fast by human engineering standards. The LLM agent may not always synthesize the optimal reflex for a given pattern — it produces *a* valid reflex, not *the best* possible reflex. Multiple synthesis attempts with different system prompts can improve quality.

*Failure mode:* If the pattern is a spurious correlation (e.g., "heading error increases when the cabin light is on"), the synthesized reflex may implement a meaningless control change. The A/B testing phase catches this because the candidate reflex's output will not be significantly better than production. If the A/B test period happens to coincide with unusual conditions, the test may produce misleading results.

**Marine Example:** After 15 days of observation, a fishing vessel's pattern discovery identifies that heading hold performance improves by 12% when the PID derivative gain (Kd) is increased from 0.3 to 0.6 during crosswind conditions (wind direction perpendicular to heading ± 30°). The LLM synthesizes a reflex that conditionally adjusts Kd based on the angle between wind direction and heading. After A/B testing (2.3 hours, MAE improvement of 0.6°), the reflex is promoted to production with trust starting at 0.10.

---

## Category 5: Swarm

These four patterns govern coordination across multiple vessels in a fleet. The swarm model treats each vessel as an autonomous agent that communicates through the shared bytecode ISA and coordinates through intention emission, trust synchronization, and emergent behavior.

---

### Pattern 5.1 — Consensus Navigation

**Intent:** When multiple vessels must agree on a shared navigation decision — formation heading, search pattern, route change — they use a consensus protocol to ensure agreement before any vessel acts. The consensus pattern prevents situations where vessels make conflicting decisions based on different local information.

**Structure:**

NEXUS uses Raft consensus for fleet-level decisions, with the Jetson cluster as the consensus group:

```
┌──────────────────────────────────────────────────────────────┐
│              RAFT CONSENSUS FOR FLEET NAVIGATION             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PROPOSER (Lead Jetson, vessel-marinus-01)                   │
│  ├── Receives navigation intent from fleet manager           │
│  ├── Compiles per-vessel bytecode for the maneuver           │
│  ├── Sends PROPOSE message to follower Jetsons               │
│  └── Waits for ACK from majority (2 of 3)                    │
│                                                              │
│  FOLLOWERS (Peer Jetsons, vessel-marinus-02, -03)            │
│  ├── Receive PROPOSE with bytecode and trust requirements    │
│  ├── Validate: cycle budget, capability match, safety rules  │
│  ├── Check: local trust score ≥ maneuver requirement          │
│  ├── Send ACK or REJECT with reason                          │
│  └── On commit: deploy bytecode to local ESP32s              │
│                                                              │
│  CONSENSUS TIMELINE:                                         │
│  t=0ms:    PROPOSE sent                                      │
│  t=50ms:   Follower 1 validates + ACK                        │
│  t=80ms:   Follower 2 validates + ACK (majority reached)     │
│  t=100ms:  COMMIT broadcast to all vessels                   │
│  t=200ms:  All ESP32s have reflex deployed and executing     │
│  t=300ms:  Leader election timeout if leader fails           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

A formation turn consensus:

```
; === PROPOSAL: Fleet formation turn to heading 045° ===
; Issued by lead Jetson (vessel-marinus-01)

PROPOSE {
  "proposal_id": "nav-2026-0329-001",
  "type": "FORMATION_TURN",
  "params": {
    "target_heading": 45.0,
    "turn_rate": 3.0,        ; degrees per second
    "formation_offset": [0, -100, -200]  ; meters, port side
  },
  "per_vessel_bytecode": {
    "vessel-marinus-01": "<AAB: lead_vessel_turn>",
    "vessel-marinus-02": "<AAB: wing_port_turn offset=-100m>",
    "vessel-marinus-03": "<AAB: wing_port_turn offset=-200m>"
  },
  "trust_requirements": {
    "steering": 0.60  // Level 3 for all vessels
  },
  "timeout_ms": 5000
}

; === FOLLOWER RESPONSE (vessel-marinus-02) ===
ACK {
  "proposal_id": "nav-2026-0329-001",
  "vessel_id": "vessel-marinus-02",
  "validation": {
    "bytecode_valid": true,
    "capability_match": true,
    "trust_sufficient": true,  // steering trust = 0.78 ≥ 0.60
    "cycle_budget_ok": true    // 45 cycles < 10,000 limit
  }
}
```

**Consequences:**

*Benefits:* All vessels execute the maneuver simultaneously and consistently. The 2-of-3 majority requirement ensures that a single faulty Jetson cannot force a dangerous maneuver. Per-vessel bytecode compilation accounts for different vessel capabilities (a sensor-limited wing vessel gets simplified reflex). The ~200ms consensus-to-execution latency is well within the requirements for formation navigation.

*Trade-offs:* Raft consensus requires a majority of Jetsons to be operational. If 2 of 3 Jetsons fail, no fleet decisions can be made (though individual vessels continue on their last-loaded reflexes). The per-vessel bytecode compilation adds ~7ms per vessel at the leader. The consensus protocol adds messaging overhead (~200 bytes per proposal over MQTT).

*Failure mode:* If the leader Jetson fails mid-consensus, a new leader is elected within 300ms. If a follower disagrees (e.g., its trust score is too low for the maneuver), it sends REJECT with its reason. The leader may re-propose with lower trust requirements (e.g., advisory mode instead of autonomous). If no consensus is reached within the timeout, the fleet continues on its current course.

**Marine Example:** A three-vessel fishing fleet in formation receives a weather alert recommending a course change from 270° to 315°. The lead vessel's Jetson proposes a formation turn. All three vessels validate the bytecode and check their trust scores (0.82, 0.71, 0.68 — all above the 0.60 threshold). Consensus is reached in 120ms. Within 200ms, all three vessels are executing synchronized turns, each with offset-adjusted timing to maintain formation spacing.

---

### Pattern 5.2 — Load-Balanced Task Assignment

**Intent:** When a fleet has multiple tasks to perform (patrol sectors, fishing zones, search areas), the fleet manager must assign tasks to vessels based on capability, proximity, trust level, and current workload. The load-balanced task assignment pattern distributes work fairly and efficiently while respecting each vessel's constraints.

**Structure:**

Task assignment uses a trust-weighted capability scoring algorithm:

```
; === TASK ASSIGNMENT ALGORITHM (fleet manager on cloud Jetson) ===

; For each task, compute a suitability score for each vessel:
;
;   suitability = proximity_score × capability_match × trust_weight
;
; Where:
;   proximity_score = 1 / (1 + distance_nm)         ∈ (0, 1]
;   capability_match = matched_sensors / required_sensors  ∈ [0, 1]
;   trust_weight = vessel_trust / trust_max           ∈ [0, 1]
;
; Assign each task to the vessel with the highest suitability score,
; then re-scores remaining vessels for remaining tasks (greedy assignment).

; Example: Search area assignment for 3-vessel fleet
;
; Task 1: Search sector A (near vessel 1, requires lidar)
; Task 2: Search sector B (near vessel 3, requires sonar)
; Task 3: Patrol corridor C (requires radar, any vessel)
;
; Scoring matrix:
;                Vessel 1    Vessel 2    Vessel 3
;                (lidar+radar) (radar)    (sonar+radar)
; Task 1 (lidar)  0.95×1.0×0.82=0.78  N/A (no lidar)  N/A (no lidar)
; Task 2 (sonar)  N/A (no sonar)  N/A (no sonar)  0.80×1.0×0.71=0.57
; Task 3 (radar)  0.60×0.5×0.82=0.25  0.90×1.0×0.65=0.59  0.50×1.0×0.71=0.36
;
; Assignment: Task 1→Vessel 1, Task 2→Vessel 3, Task 3→Vessel 2
```

The assignment is communicated via DELEGATE to each vessel:

```
; Fleet manager → Vessel 1
DELEGATE {
  "target_vessel": "vessel-marinus-01",
  "intent": "search_sector_A",
  "bytecode": "<AAB: sector_search lidar-based>",
  "estimated_duration_hours": 4,
  "trust_required": 0.50,
  "report_interval_minutes": 15
}

; Fleet manager → Vessel 2
DELEGATE {
  "target_vessel": "vessel-marinus-02",
  "intent": "patrol_corridor_C",
  "bytecode": "<AAB: corridor_patrol radar-based>",
  "estimated_duration_hours": 6,
  "trust_required": 0.40,
  "report_interval_minutes": 30
}
```

**Consequences:**

*Benefits:* Tasks are assigned to the most suitable vessel, considering hardware capabilities, geographic proximity, and demonstrated trust. The trust-weighted scoring means a vessel with a history of reliable operation is preferred for critical tasks. The greedy assignment algorithm is fast (O(tasks × vessels)) and produces good (though not necessarily optimal) assignments.

*Trade-offs:* The greedy algorithm does not guarantee globally optimal assignment. A vessel assigned to a nearby task may block a more important distant task for another vessel. The suitability scores are static at assignment time — if conditions change (weather, sensor failure), the assignment may become suboptimal. Reassignment requires a new consensus round.

*Failure mode:* If a vessel fails mid-task, the fleet manager must reassign the task. The CRDT trust synchronization ensures all vessels know the failed vessel's trust score has dropped to t_floor. The manager re-runs the assignment algorithm and delegates the orphaned task to the next most suitable vessel.

**Marine Example:** A 5-vessel survey fleet must map a 50 km² area. The fleet manager divides the area into 5 sectors and assigns each vessel to its nearest sector. Vessel 3 (closest to sector 3, trust 0.85, equipped with side-scan sonar) is assigned to the deepest sector. Vessel 1 (trust 0.42, no sonar) is assigned to the shallowest sector requiring only depth sounder. After 2 hours, Vessel 3's sonar fails. The manager reassigns sector 3 to Vessel 4 (next closest, trust 0.73, has sonar), which adjusts course and picks up the survey.

---

### Pattern 5.3 — Scout-Report-Act

**Intent:** When a fleet needs information about an unknown area (unmapped waters, potential hazards, target search), one vessel acts as a scout to gather data, reports findings to the fleet, and the fleet decides on a coordinated action. This pattern separates the data-gathering role from the decision-making role, allowing specialized vessels for each function.

**Structure:**

```
┌──────────────────────────────────────────────────────────────┐
│                    SCOUT-REPORT-ACT PATTERN                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASE 1: SCOUT                                              │
│  Fleet manager DELEGATEs scout mission to scout vessel:       │
│    intent: "Survey area 58°30'N 3°15'E radius 2nm"           │
│    reflex: pattern_survey_lidar + depth_sounder              │
│    trust_min: 0.40                                           │
│    report_trigger: obstacle_detected OR area_complete         │
│                                                              │
│  Scout vessel executes reflex autonomously:                   │
│    - Follow survey grid at 5 knots                           │
│    - READ_PIN lidar_dist, depth_sounder each tick             │
│    - EMIT_EVENT on obstacle detection (dist < 20m)           │
│    - RECORD_SNAPSHOT every 100 ticks                         │
│                                                              │
│  PHASE 2: REPORT                                             │
│  Scout vessel TELLs findings to fleet:                       │
│    message="SURVEY_COMPLETE: area surveyed 100%"             │
│    attachments={                                             │
│      obstacles: [{dist:18m, bearing:045, type:rock}, ...],   │
│      depth_profile: [12.3, 14.1, 8.7, ...],                  │
│      safe_passage: {heading:090, width:45m}                  │
│    }                                                         │
│                                                              │
│  PHASE 3: ACT                                                │
│  Fleet manager processes report:                              │
│    - Updates shared navigation chart                          │
│    - Computes safe route through surveyed area               │
│    - DELEGATEs route-following reflex to all vessels         │
│    - Each vessel compiles route to its own capability set     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Scout reflex bytecode:

```
; === SCOUT SURVEY REFLEX ===
; Runs at 10 Hz on scout vessel's ESP32

DECLARE_INTENT  id=scout_survey
  trust_min=0.40
  capabilities: lidar, depth_sounder, gps

; Check for obstacles
READ_PIN  sensor[12]       ; lidar_nearest_dist_m
PUSH_F32  20.0             ; obstacle threshold
LT_F
JUMP_IF_FALSE :no_obstacle

; Obstacle detected — report immediately
EMIT_EVENT  obstacle_detected
  ; Event payload: {dist, bearing, gps_lat, gps_lon, timestamp}
TELL  channel=fleet_broadcast
     message="OBSTACLE_FOUND: dist={dist}m bearing={bearing} at {gps}"

:no_obstacle
; Record survey snapshot
READ_PIN  sensor[15]       ; depth_sounder_m
READ_PIN  sensor[1]        ; gps_lat
READ_PIN  sensor[2]        ; gps_lon
SYSCALL  RECORD_SNAPSHOT

; Check if survey area is complete
READ_PIN  sensor[1]        ; current gps_lat
READ_VAR  survey_north_limit
GTE_F
JUMP_IF_FALSE :survey_continue
READ_PIN  sensor[2]        ; current gps_lon
READ_VAR  survey_east_limit
GTE_F
JUMP_IF_FALSE :survey_continue

; Survey complete
EMIT_EVENT  survey_complete
TELL  channel=fleet_broadcast
     message="SURVEY_COMPLETE: area {north_limit}×{east_limit} scanned"
JUMP :done

:survey_continue
; Continue survey grid navigation
; ... (waypoint following logic) ...

:done
NOP
```

**Consequences:**

*Benefits:* The scout vessel acts autonomously, reducing communication overhead. The fleet manager only receives structured reports, not raw sensor data. The report-act separation means the fleet can deliberate on the best action while the scout moves to the next survey area. Specialized scout vessels can have different sensor suites (lidar, sonar) than the rest of the fleet.

*Trade-offs:* The scout vessel is exposed to unknown hazards during the scouting phase. The trust requirement of 0.40 (Level 2) means only semi-autonomous vessels can scout — a very new vessel cannot. The time delay between scouting and fleet action (scout time + report transmission + deliberation + deployment) may be unacceptable for time-critical situations.

*Failure mode:* If the scout vessel loses communication during scouting, it continues its survey grid autonomously and reports findings when communication resumes. If the scout vessel is lost, the fleet manager times out the scout mission and reassigns it to another vessel.

**Marine Example:** A 3-vessel fleet approaches an uncharted reef area. Vessel 1 (equipped with forward-looking sonar, trust 0.72) is designated as scout. It surveys a 2 nautical mile radius at 5 knots, detecting 3 submerged rocks at depths of 2–4m. It reports the findings to the fleet via TELL. The fleet manager computes a safe passage route between the rocks and DELEGATEs the route to all three vessels. Each vessel compiles the route with its own sensor configuration (Vessel 2 uses radar instead of sonar, Vessel 3 uses GPS-only with wider safety margins).

---

### Pattern 5.4 — Emergent Behavior Control

**Intent:** Enable complex fleet-level behaviors to emerge from simple per-vessel reflexes, while maintaining safety boundaries that prevent emergent behavior from becoming dangerous. Emergence in NEXUS is bounded: each vessel's reflexes are individually validated, trust-gated, and actuator-clamped, so the fleet's collective behavior cannot exceed the safety envelope of any individual vessel.

**Structure:**

Emergent behaviors arise from three mechanisms:

**Mechanism 1: Shared environment, independent reflexes**
Each vessel runs identical or similar reflexes that react to the same environmental signals. The fleet's collective behavior emerges from each vessel's individual response.

```
; === EMERGENT SEARCH PATTERN ===
; Each vessel runs the same reflex with a different heading offset
; Fleet behavior: expanding spiral search without central coordination

; Vessel 1: base_heading + 0° offset
; Vessel 2: base_heading + 120° offset
; Vessel 3: base_heading + 240° offset

; Common reflex (parameterized by vessel offset):
READ_PIN  sensor[0]        ; compass_heading
READ_VAR  base_heading
ADD_VAR   vessel_offset    ; 0°, 120°, or 240°
SUB_F     heading_error
PID_COMPUTE search_pid
CLAMP_F   -15.0 15.0
WRITE_PIN actuator[0]      ; rudder
PUSH_F32  5.0              ; slow search speed
WRITE_PIN actuator[1]      ; throttle

; Emergent behavior: three vessels spread out in a spiral,
; covering 360° of search area without any inter-vessel communication
```

**Mechanism 2: Distributed sensor fusion**
Each vessel contributes local observations to a shared map. The fleet's collective perception emerges from individual observations.

```
; Each vessel reports its local obstacle detections:
READ_PIN  sensor[12]       ; lidar/radar nearest obstacle
PUSH_F32  50.0             ; report threshold
LT_F
JUMP_IF_FALSE :no_report

EMIT_EVENT  obstacle_report
  ; Payload: {vessel_id, dist, bearing, gps_lat, gps_lon}

; Fleet manager aggregates:
; → Shared obstacle map with contributions from all vessels
; → Map is richer than any single vessel's perception
; → Each vessel receives the aggregated map via fleet broadcast
```

**Mechanism 3: Trust-gated adaptive flocking**
The INCREMENTS trust algorithm creates natural load balancing: if a vessel performs poorly (bad windows), its trust drops and it is assigned less critical tasks. High-trust vessels naturally take on more responsibility.

```
; Trust-based task weight adjustment:
; vessel_task_weight = (vessel_trust / sum_of_all_trusts) × total_tasks

; Example with trust decay in Vessel 2:
; Initial:  V1=0.80 (40%), V2=0.75 (37.5%), V3=0.45 (22.5%)
; After V2 failure: V1=0.80 (47%), V2=0.10 (5.9%), V3=0.45 (26.5%)
; Vessel 1 and 3 automatically absorb Vessel 2's tasks
```

Safety boundaries on emergence:

```
; Every emergent behavior reflex includes:
SAFE_BOUNDARY  max_speed_knots=10.0  ; fleet speed limit
SAFE_BOUNDARY  min_vessel_sep_m=50.0 ; minimum separation
SAFE_BOUNDARY  max_area_nm2=25.0     ; maximum operational area
TRUST_CHECK    subsystem=steering, min=0.50  ; minimum trust
RATE_LIMIT     heading_change, max=3.0°/s    ; prevent erratic turns
```

**Consequences:**

*Benefits:* Complex fleet behaviors (search patterns, formation keeping, distributed mapping) arise from simple per-vessel reflexes without central coordination. The trust algorithm naturally adapts task allocation based on demonstrated competence. Bounded emergence means the fleet cannot produce dangerous behaviors — every vessel's reflex is individually safe, so the fleet is collectively safe.

*Trade-offs:* Emergent behaviors are difficult to predict analytically. The fleet may converge on suboptimal solutions (e.g., all vessels searching the same area). The safety boundaries limit the range of possible emergent behaviors — the system trades optimal emergence for guaranteed safety. True complex emergence (e.g., cooperative manipulation, tight formation flying at speed) may require more sophisticated inter-vessel communication than the current architecture supports.

*Failure mode:* If multiple vessels converge on the same location (a failure of the separation boundary), the collision avoidance reflex (Pattern 2.4) activates on each vessel and separates them. The emergent behavior is disrupted but the fleet remains safe.

**Marine Example:** A 3-vessel fleet searches for a life raft in a 10 nm² area. Each vessel runs the emergent search pattern reflex with heading offsets of 0°, 120°, and 240°. The fleet naturally spreads out to cover 360° without any inter-vessel coordination. When Vessel 3's radar detects a small contact at 800m, it TELLs the fleet. Vessels 1 and 2 adjust their search patterns (still independent reflexes, but now reacting to the shared information) to converge on the contact. The fleet locates the life raft within 45 minutes — faster than any single vessel could achieve alone.

---

## Category 6: Pattern Composition

These three system designs show how individual patterns compose into complete architectures. Each design specifies which patterns are active, how they interact, and what the failure modes are.

---

### Composition 6.1 — Single Vessel: Autonomous Patrol Boat

**Patterns Used (8):** Intention Block (1.1), Trust-Gated Reflex (1.2), Graceful Degradation (1.3), Capability-Bounded Execution (1.4), Generator-Validator Pair (2.1), Defense in Depth (3.1), Fail-Safe Default (3.2), Trust-Gated Learning (4.3)

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│                    SINGLE VESSEL — PATROL BOAT               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  HARDWARE:                                                   │
│    1× Jetson Orin Nano (cognitive layer)                     │
│    3× ESP32-S3 (navigation, propulsion, sensors)             │
│    Sensors: GPS RTK, compass, IMU, radar, AIS, wind          │
│    Actuators: rudder, throttle, anchor, navigation lights    │
│    Safety: kill switch, INA219, MAX6818 watchdog             │
│                                                              │
│  PATTERN STACK (bottom to top):                              │
│                                                              │
│  [Defense in Depth] — Foundation                             │
│    Hardware kill switch → firmware ISR → state machine →     │
│    trust-gated autonomy. Every action passes through 4       │
│    safety layers. The kill switch can stop everything in     │
│    <1ms regardless of software state.                        │
│                                                              │
│  [Fail-Safe Default] — On top of defense                    │
│    Every reflex defaults to rudder=0°, throttle=0%.          │
│    Sensor failures substitute 0.0 and trigger degraded mode. │
│    Hardware pull-downs enforce safe state on signal loss.    │
│                                                              │
│  [Capability-Bounded Execution] — Compilation gate           │
│    The Jetson queries each ESP32's capability descriptor     │
│    before compiling reflexes. A radar-only reflex won't      │
│    compile for a radar-less ESP32. Max 10,000 cycles/tick.  │
│                                                              │
│  [Trust-Gated Reflex] — Execution gate                       │
│    Steering starts at L0. After 27 days of safe operation    │
│    (54 days for agent code at 0.5×), reaches L4. Every      │
│    reflex checks trust before writing actuators.             │
│                                                              │
│  [Graceful Degradation] — Resilience layer                  │
│    Radar failure → compass-only navigation. Jetson failure   │
│    → ESP32s continue on loaded reflexes. Sensor stale after  │
│    500ms → degraded mode with conservative defaults.         │
│                                                              │
│  [Intention Block] — Structure layer                         │
│    Every reflex is an AAB intention block with declared      │
│    goals, capabilities, trust context, and failure          │
│    narratives. The heading-hold reflex, the obstacle-        │
│    avoidance reflex, and the patrol-route reflex all follow  │
│    the intention block structure.                            │
│                                                              │
│  [Generator-Validator Pair] — Creation layer                 │
│    New reflexes generated by Qwen2.5-Coder-7B, validated    │
│    by Claude 3.5 Sonnet (95.1% catch rate). Existing        │
│    reflexes were human-authored (1.0× trust multiplier).     │
│                                                              │
│  [Trust-Gated Learning] — Improvement layer                  │
│    At trust Level 1: observe only. Level 2: discover        │
│    patterns. Level 3: A/B test with operator approval.       │
│    Level 4: full autonomous learning and deployment.         │
│                                                              │
│  TYPICAL OPERATIONAL FLOW:                                   │
│  1. Operator sets patrol waypoints via tablet                 │
│  2. Jetson generates waypoint-following reflex (Intention)   │
│  3. Validator checks safety (Generator-Validator)            │
│  4. Reflex compiled and deployed to navigation ESP32         │
│     (Capability-Bounded)                                     │
│  5. Trust gate allows execution at Level 2+ (Trust-Gated)   │
│  6. Radar fails → degrades to compass-only (Graceful)        │
│  7. Observation discovers pattern → candidate reflex         │
│     (Trust-Gated Learning)                                   │
│  8. All through 4 safety layers (Defense in Depth)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Failure Scenario:** Radar fails during patrol. Graceful Degradation detects stale radar data (500ms timeout), substitutes 0.0, and the navigation reflex routes to compass-only mode. The obstacle avoidance reflex (which depends on radar) is suspended — Fail-Safe Default centers the rudder if an obstacle is detected by AIS instead. The operator is notified via TELL. Trust for the navigation subsystem is unaffected (radar failure is environmental, not systemic). The observation reflex continues recording, and Trust-Gated Learning notes the degraded regime for future pattern discovery.

---

### Composition 6.2 — Three-Vessel Fleet: Coordinated Fishing Operation

**Patterns Used (10):** All 8 from Composition 6.1, plus Fleet Broadcast (2.3), Consensus Navigation (5.1), Ask-Tell-Delegate Chain (2.2)

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│           3-VESSEL FLEET — COORDINATED FISHING              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  VESSEL 1 (LEAD): Full autonomous (3× Jetson, 12× ESP32)   │
│    Role: Fleet coordination, heavy processing, cloud link    │
│    Raft leader: proposes fleet maneuvers, validates          │
│    Trust: steering=0.88, engine=0.82, net=0.75              │
│                                                              │
│  VESSEL 2 (WING PORT): Cognitive light (1× Jetson, 4× ESP32)│
│    Role: Port wing of formation, sonar surveys               │
│    Raft follower: validates proposals, ACKs/REJECTs          │
│    Trust: steering=0.71, engine=0.68, net=0.60              │
│                                                              │
│  VESSEL 3 (WING STARBOARD): Cognitive light (1× Jetson, 4) │
│    Role: Starboard wing, water quality monitoring            │
│    Raft follower: validates proposals, ACKs/REJECTs          │
│    Trust: steering=0.65, engine=0.72, net=0.55              │
│                                                              │
│  FLEET-WIDE PATTERNS (on top of single-vessel patterns):     │
│                                                              │
│  [Consensus Navigation]                                      │
│    Formation changes require Raft consensus (2 of 3 ACK).    │
│    When lead vessel detects fish school via sonar:           │
│      1. Lead PROPOSEs formation change to intercept          │
│      2. Each wing vessel validates: trust ≥ 0.60? Capable?  │
│      3. Consensus reached → COMMIT → all deploy turn reflex  │
│      4. Per-vessel bytecode: lead turns first, wings delay   │
│         by offset time to maintain formation spacing         │
│                                                              │
│  [Fleet Broadcast]                                           │
│    Weather alerts from cloud → all vessels simultaneously.   │
│    Trust score synchronization via CRDTs (< 1s convergence). │
│    Fish school detection broadcast from lead → wings adjust. │
│    Net deployment coordination: all vessels must ACK before  │
│    any vessel deploys nets.                                  │
│                                                              │
│  [Ask-Tell-Delegate Chain]                                   │
│    Lead ASKs wings for sensor data (sonar, water quality).   │
│    Wings TELL lead their local observations.                 │
│    Lead DELEGATEs specific tasks: "Vessel 3, sample water    │
│    at 58°30'N 3°15'E" → Vessel 3 compiles and executes.     │
│    Cross-vessel obstacle avoidance: Vessel 2 detects         │
│    obstacle → TELLs fleet → Lead DELEGATEs evasion.         │
│                                                              │
│  OPERATIONAL FLOW — FISH SCHOOL INTERCEPTION:                │
│  1. Vessel 1 sonar detects fish school at bearing 045°, 2nm  │
│  2. Vessel 1 TELLs fleet: "FISH_SCHOOL bearing=045 dist=2nm"│
│  3. Vessel 1 PROPOSEs formation turn to intercept            │
│  4. Vessels 2,3 validate trust + capability → ACK            │
│  5. Consensus reached → COMMIT                              │
│  6. Per-vessel reflexes deployed (lead first, wings follow)  │
│  7. During approach: Vessel 2 ASKs lead for trawl timing     │
│  8. Lead TELLs: "DEPLOY_NETS in 30 seconds"                 │
│  9. All vessels prepare nets (Trust-Gated Reflex ensures     │
│     net subsystem trust ≥ 0.50 for each vessel)              │
│  10. Fleet Broadcast: "NETS_DEPLOYED" confirms all vessels   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Failure Scenario:** Vessel 3's Jetson fails during trawl. Raft detects heartbeat timeout (300ms), elects new leader (Vessel 1 remains leader if healthy; otherwise Vessel 2 takes over). Vessel 3's ESP32s enter FAILSAFE — they continue executing loaded reflexes (net tension monitoring, bilge pump) autonomously. Trust scores for Vessel 3's subsystems are frozen at current values via CRDT synchronization. Vessel 1 DELEGATEs Vessel 2 to maintain position near Vessel 3 for safety. When Vessel 3's Jetson recovers (hot standby activates within 100ms), it re-syncs trust scores and resumes operation.

---

### Composition 6.3 — Heterogeneous Swarm: Multi-Domain Maritime Operations

**Patterns Used (12):** All 8 from Composition 6.1, plus Fleet Broadcast (2.3), Consensus Navigation (5.1), Load-Balanced Task Assignment (5.2), Scout-Report-Act (5.3), Emergent Behavior Control (5.4), Emergency Override (2.4)

**Architecture:**

```
┌──────────────────────────────────────────────────────────────┐
│       HETEROGENEOUS SWARM — MULTI-DOMAIN MARITIME OPS       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  VESSEL TYPES (heterogeneous fleet):                        │
│                                                              │
│  Type A: Full Autonomous (3 vessels)                        │
│    3× Jetson + 12× ESP32, GPS RTK, lidar, radar, AIS,       │
│    sonar, full propulsion. Trust: 0.85–0.95.                 │
│    Role: Fleet coordination, heavy processing, scout         │
│                                                              │
│  Type B: Cognitive Light (5 vessels)                        │
│    1× Jetson + 4× ESP32, GPS, compass, radar.                │
│    Trust: 0.60–0.80.                                         │
│    Role: Patrol, search, sensor relay                        │
│                                                              │
│  Type C: Reflex Only (8 vessels)                            │
│    2× ESP32, compass, depth sounder, basic actuators.        │
│    Trust: 0.30–0.55.                                         │
│    Role: Sensor buoys, perimeter monitoring, relay nodes     │
│                                                              │
│  Type D: Minimal Sensor (12 vessels)                        │
│    1× ESP32, temperature, humidity, relay.                   │
│    Trust: 0.10–0.30.                                         │
│    Role: Environmental sensor grid, communication relay      │
│                                                              │
│  TOTAL: 28 vessels, 14 Jetson nodes, 80 ESP32 nodes          │
│                                                              │
│  SWARM PATTERN STACK:                                        │
│                                                              │
│  [Emergency Override] — Safety umbrella                      │
│    Any vessel can broadcast COLLISION_IMMINENT to fleet.     │
│    Hardware kill switch on all Type A/B vessels.              │
│    Type C/D vessels have no propulsion kill switch           │
│    (they drift if all software fails — acceptable risk).     │
│                                                              │
│  [Defense in Depth + Fail-Safe Default] — Per-vessel         │
│    Each vessel runs its own 4-layer safety stack.            │
│    Type C/D vessels have simplified stacks:                   │
│      Hardware: watchdog only (no kill switch)                │
│      Firmware: cycle budget + stack bounds                   │
│      Supervisory: heartbeat only (no trust)                 │
│      Application: none (no LLM, no validation)              │
│                                                              │
│  [Load-Balanced Task Assignment] — Fleet optimization        │
│    Fleet manager (cloud) assigns tasks based on:             │
│      suitability = proximity × capability × trust            │
│    Type A vessels get complex tasks (scout, coordinate)      │
│    Type B vessels get patrol and relay tasks                 │
│    Type C vessels get perimeter monitoring                   │
│    Type D vessels get environmental sensing (any trust)      │
│                                                              │
│  [Scout-Report-Act] — Exploration                           │
│    Type A vessels scout unknown areas with full sensor suite │
│    Report findings via Fleet Broadcast to all vessels        │
│    Fleet manager computes safe routes for Type B/C vessels   │
│    Type D sensor buoys provide persistent environmental data │
│                                                              │
│  [Emergent Behavior Control] — Collective intelligence      │
│    Search patterns: 8 Type C/D vessels form a sensor grid    │
│    Each runs identical "report anomaly" reflex independently  │
│    Fleet manager aggregates reports → shared anomaly map     │
│    Trust-gated adaptive flocking: high-trust Type A vessels  │
│    handle dynamic reassignment automatically                 │
│                                                              │
│  [Consensus Navigation] — Formation control                 │
│    Only Type A Jetsons participate in Raft consensus         │
│    Type B/C/D vessels follow via delegation from Type A      │
│    Consensus required for: formation changes, route changes, │
│    mission abort, emergency maneuvers                        │
│                                                              │
│  [Fleet Broadcast + Ask-Tell-Delegate] — Communication      │
│    MQTT QoS 2 for critical messages (emergency, consensus)  │
│    MQTT QoS 0 for telemetry (sensor data, heartbeats)       │
│    Type D vessels relay messages — they act as mesh nodes    │
│    extending fleet communication range                       │
│                                                              │
│  OPERATIONAL SCENARIO — POLLUTION RESPONSE:                  │
│                                                              │
│  1. Type D sensor grid detects anomalous pH readings in     │
│     sector 7. Emergent behavior: multiple buoys report       │
│     the anomaly. Fleet manager detects the pattern.          │
│                                                              │
│  2. Fleet manager uses Load-Balanced Task Assignment to     │
│     send nearest Type A vessel (Vessel-A2, trust 0.88)      │
│     to scout sector 7.                                       │
│                                                              │
│  3. Vessel-A2 runs Scout-Report-Act pattern:                │
│     - Scouts with lidar + water quality sensors              │
│     - Reports: "Oil slick, 500m × 200m, thickness 2mm"      │
│     - Reports: "Safe approach from south, avoid north"       │
│                                                              │
│  4. Fleet broadcast to all 28 vessels:                      │
│     "POLLUTION_DETECTED sector_7, avoid_area={polygon}"     │
│     Pre-validated avoidance reflex deployed to all vessels   │
│     with steering capability (Type A/B/C).                   │
│                                                              │
│  5. Consensus Navigation: Type A vessels vote on response    │
│     plan. Consensus: deploy containment booms from south.    │
│     Type B vessels assigned to boom deployment.               │
│                                                              │
│  6. Type C sensor buoys at the perimeter provide continuous  │
│     monitoring of containment effectiveness. Emergent        │
│     behavior: buoys report current drift patterns → fleet    │
│     adjusts boom positions.                                  │
│                                                              │
│  7. Trust-Gated Learning: observation data from the event    │
│     feeds pattern discovery. After 30 days, the system may  │
│     discover patterns like "pH anomaly correlates with       │
│     shipping lane proximity" and deploy early-warning        │
│     reflexes to sensor buoys.                                │
│                                                              │
│  SAFETY ANALYSIS:                                            │
│  - 28 vessels × 4 safety layers = 112 independent safety    │
│    barriers. The probability of simultaneous failure across  │
│    all barriers on all vessels is astronomically low.        │
│  - Trust diversity: vessels at different trust levels        │
│    provide natural experimentation. Type A at L4 can try     │
│    maneuvers that Type C at L2 cannot.                      │
│  - Communication resilience: Type D mesh relay extends       │
│    range by ~3×. Losing 50% of Type D vessels still         │
│    provides connectivity for the remaining fleet.           │
│  - Graceful degradation: if all Type A vessels fail,         │
│    Type B vessels take over coordination (trust permitting). │
│    If all Jetsons fail, Type C/D ESP32s continue on last     │
│    loaded reflexes (sensor reporting, basic patrol).         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Failure Scenario — Cascading Jetson Failure:** All 14 Jetson nodes experience a simultaneous software fault (e.g., corrupted LLM model in shared storage). All 80 ESP32 nodes enter FAILSAFE and continue executing their last-loaded reflexes. Type A/B vessels lose cognitive capability but maintain heading hold and basic collision avoidance. Type C/D sensor buoys continue reporting environmental data. The fleet's behavior degrades from "coordinated swarm" to "independent vessels with basic safety reflexes" — which is safe but not useful for complex operations. The hardware watchdogs (MAX6818, 1.0s timeout) trigger resets on all Jetsons. After reset, the Jetsons boot from the factory partition (trusted recovery image), re-establish MQTT connections, and resume fleet coordination. Total disruption: ~30 seconds.

---

### Composition 6.4 — Intention Composition

**Intent:** Combine multiple independent intention blocks into a single deployment unit that respects actuator arbitration, trust compatibility, and capability union rules. Intention composition is the mechanism by which simple, single-purpose reflexes combine into sophisticated multi-objective control programs without central coordination.

**Structure:**

Composition rules are enforced by the Jetson's deployment manager before any composed reflex reaches the ESP32:

```
╔══════════════════════════════════════════════════════════════╗
║         INTENTION COMPOSITION RULES (enforced at deploy)     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  RULE 1: NON-CONFLICTING ACTUATORS                           ║
║  Two blocks may not write to the same actuator register       ║
║  without an explicit ARBITRATION declaration.                 ║
║  Violation → REJECT with "actuator conflict on pin {idx}"    ║
║                                                              ║
║  RULE 2: COMPATIBLE TRUST CONTEXTS                            ║
║  A composed program requires the MAXIMUM trust level across   ║
║  all blocks. If Block A needs Level 3 and Block B needs       ║
║  Level 2, the composed program requires Level 3.             ║
║  Rationale: the composed program activates ALL blocks; if    ║
║  one block cannot safely execute, none should.                ║
║                                                              ║
║  RULE 3: UNION OF CAPABILITIES                               ║
║  The composed program requires every capability declared by   ║
║  any constituent block. If Block A needs compass and Block B  ║
║  needs lidar, the composed program needs both.                ║
║  If any REQUIRED capability is unavailable → REJECT.          ║
║                                                              ║
║  RULE 4: PRIORITY-ORDERED EXECUTION                          ║
║  Blocks execute in priority order within a tick:              ║
║    Priority 1 (CRITICAL) → emergency reflexes                ║
║    Priority 2 (HIGH) → safety-related reflexes               ║
║    Priority 3 (NORMAL) → standard control reflexes           ║
║    Priority 4 (LOW) → observation, telemetry                  ║
║    Priority 5 (BACKGROUND) → learning, logging               ║
║  Higher-priority blocks may preempt lower-priority blocks     ║
║  for shared actuator writes (last-writer-wins semantics).    ║
║                                                              ║
║  RULE 5: ORDERED FAILURE NARRATIVES                          ║
║  If multiple blocks fail simultaneously, narratives are       ║
║  ordered by severity (CRITICAL > ERROR > WARNING > INFO).     ║
║  The operator sees the most severe failure first.             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

Concrete composition — three blocks for a coastal patrol vessel:

```
; === COMPOSED DEPLOYMENT: coastal_patrol_v3 ===
; Deployed as a single REFLEX_DEPLOY message with 3 blocks

; ── Block A: Heading Hold (Priority 3, Level 3) ──────────────
;   Requires: compass, rudder. Writes: rudder.
;   Trust: steering ≥ 0.70

DECLARE_INTENT  id=heading_hold
  trust_min=0.70, priority=3
TRUST_CHECK  subsystem=steering, min=0.70
READ_PIN  compass_heading
READ_VAR  target_heading
SUB_F     heading_error
SYSCALL   PID_COMPUTE heading_pid
CLAMP_F   -30.0 30.0
WRITE_PIN actuator[0]  ; rudder

; ── Block B: Speed Control (Priority 3, Level 2) ─────────────
;   Requires: gps, throttle. Writes: throttle.
;   Trust: engine ≥ 0.40

DECLARE_INTENT  id=speed_control
  trust_min=0.40, priority=3
TRUST_CHECK  subsystem=engine, min=0.40
READ_PIN  gps_speed_knots
READ_VAR  target_speed
SUB_F     speed_error
SYSCALL   PID_COMPUTE speed_pid
CLAMP_F   0.0 80.0       ; safety policy: never > 80%
WRITE_PIN actuator[1]  ; throttle

; ── Block C: Emergency Obstacle Avoidance (Priority 1, Level 1) ─
;   Requires: radar, rudder, throttle. Writes: rudder, throttle.
;   Trust: steering ≥ 0.30
;   ARBITRATION: OVERRIDES Block A (rudder) and Block B (throttle)

DECLARE_INTENT  id=emergency_avoid
  trust_min=0.30, priority=1
  ARBITRATION: override_actuator[0], override_actuator[1]
READ_PIN  radar_nearest_dist_m
PUSH_F32  15.0
LT_F
JUMP_IF_FALSE :no_emergency
SAFETY_EVENT_EMIT  severity=CRITICAL, event_code=COLLISION_RISK
PUSH_F32  -45.0
WRITE_PIN actuator[0]  ; rudder → full starboard (overrides Block A)
PUSH_F32  20.0
WRITE_PIN actuator[1]  ; throttle → minimum speed (overrides Block B)
:no_emergency
NOP

; ── Composed program trust context ───────────────────────────
; Requires MAX(A=0.70, B=0.40, C=0.30) = Level 3 (0.70)
; BUT: Block B and C can execute independently at their lower trust
; Only Block A requires Level 3
; Trust gating is per-block, not per-program

; ── Composed program capability scope ────────────────────────
; Requires UNION of: compass, rudder, gps, throttle, radar
; If radar unavailable → Block C cannot load, but A and B deploy
; Partial composition is supported
```

**Consequences:**

*Benefits:* Complex behavior emerges from simple, verified building blocks. Each block can be validated, A/B tested, and trust-gated independently. The priority system ensures safety-critical blocks always win actuator arbitration. Partial composition (when some capabilities are unavailable) provides graceful degradation at the composition level.

*Trade-offs:* The union-of-capabilities rule means a composed program may fail to deploy if any single block requires an unavailable sensor, even if other blocks could operate without it. Partial composition mitigates this but adds deployment complexity. The maximum trust rule is conservative: if any block needs high trust, the entire composed deployment requires it (even though per-block gating allows lower-trust blocks to execute independently).

*Failure mode:* If two blocks with conflicting actuator writes have the same priority, the execution order determines the outcome (non-deterministic if execution order is unspecified). The ARBITRATION declaration resolves this explicitly. If the arbitration declaration is missing, the deployment manager rejects the composition.

**Marine Example:** A patrol vessel runs a composed program with three blocks: heading hold (Block A), speed control (Block B), and emergency obstacle avoidance (Block C). During normal operation, A controls the rudder and B controls the throttle. When the radar detects an obstacle at 12m, Block C (priority 1) activates and overrides both A's rudder command and B's throttle command. After the obstacle clears (radar > 50m for 5 seconds), Block C deactivates and control returns to A and B. The operator sees the event as a single EXPLAIN_FAILURE narrative from Block C, with severity CRITICAL.

---

### Composition 6.5 — Trust-Gated Orchestration

**Intent:** Manage the lifecycle of reflex deployment, monitoring, and retirement across the fleet using trust as the primary decision variable. The orchestration pattern automates the operational decisions that would otherwise require human judgment: when to deploy a new reflex, when to promote it from shadow to production, when to retire a reflex whose trust has decayed, and when to re-deploy a previously retired reflex that has been improved.

**Structure:**

The orchestration agent runs on the fleet manager's Jetson and implements a state machine for every reflex in the fleet:

```
╔══════════════════════════════════════════════════════════════╗
║         REFLEX LIFECYCLE STATE MACHINE                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌──────────┐  trust ≥ threshold   ┌──────────┐              ║
║  │ STANDBY  │ ──────────────────▶  │  ACTIVE  │              ║
║  │          │                      │          │              ║
║  │ Waiting  │  trust < threshold   │ Running  │              ║
║  │ for      │ ◀────────────────── │ at tick  │              ║
║  │ trust    │                      │ rate     │              ║
║  └────┬─────┘                      └────┬─────┘              ║
║       │                                 │                     ║
║       │ candidate generated             │ trust = t_floor     ║
║       │ (pattern discovery)             │ (consecutive bad)   ║
║       ▼                                 ▼                     ║
║  ┌──────────┐  A/B pass + trust OK  ┌──────────┐              ║
║  │ SHADOW   │ ──────────────────▶  │  ACTIVE  │              ║
║  │          │                      │          │              ║
║  │ A/B test │  A/B fail            │ (promoted│              ║
║  │          │ ──────────────────▶  │  reflex) │              ║
║  └────┬─────┘                      └──────────┘              ║
║       │                                                        ║
║       │ trust = t_floor + recovery_timeout                    ║
║       │ (no improvement after 7 days)                         ║
║       ▼                                                        ║
║  ┌──────────┐                                                 ║
║  │ RETIRED  │                                                 ║
║  │          │  new candidate generated                        ║
║  │ Removed  │ ◀────────────────────────────────               ║
║  │ from     │  (improved version)                              ║
║  │ slots    │                                                 ║
║  └──────────┘                                                 ║
║                                                              ║
║  State transitions:                                          ║
║    STANDBY → SHADOW:   pattern discovery produces candidate   ║
║    SHADOW → ACTIVE:   A/B test passes + trust ≥ threshold    ║
║    SHADOW → RETIRED:  A/B test fails after 3 attempts        ║
║    ACTIVE → STANDBY:  trust drops below threshold             ║
║    ACTIVE → RETIRED:  trust at t_floor for 7 consecutive days║
║    RETIRED → SHADOW:  improved candidate generated             ║
║    ANY → RETIRED:    operator manual retirement command        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

The orchestration agent's decision bytecode (Jetson-side pseudocode):

```
; === ORCHESTRATION AGENT (runs on fleet manager Jetson) ===

; For each reflex in fleet, check lifecycle state

; ── Step 1: Check active reflexes for trust degradation ──
ASK  channel=trust_engine
     question="all_reflex_trust vessel=*"
  → trust_map on stack

FOR_EACH reflex IN trust_map:
  IF reflex.trust < reflex.trust_threshold:
    TELL  channel=vessel_{reflex.vessel_id}
         message="DEACTIVATE_REFLEX slot={reflex.slot}"
    TELL  channel=fleet_broadcast/trust
         message="REFLEX_DEACTIVATED: {reflex.name} trust={reflex.trust}"
    UPDATE reflex.state = STANDBY

  IF reflex.trust <= t_floor AND reflex.stale_days >= 7:
    TELL  channel=vessel_{reflex.vessel_id}
         message="RETIRE_REFLEX slot={reflex.slot}"
    TELL  channel=fleet_broadcast/trust
         message="REFLEX_RETIRED: {reflex.name} no recovery in 7 days"
    UPDATE reflex.state = RETIRED

; ── Step 2: Check shadow reflexes for promotion ──
ASK  channel=ab_testing
     question="all_shadow_results"
  → ab_results on stack

FOR_EACH result IN ab_results:
  IF result.mae < 2.0 AND result.max_dev < 5.0 AND result.violations == 0:
    ASK  channel=trust_engine
         question="current_trust subsystem={result.subsystem}"
    IF trust >= result.trust_threshold:
      TELL  channel=vessel_{result.vessel_id}
           message="PROMOTE_REFLEX shadow_slot={result.slot}"
      TELL  channel=fleet_broadcast/trust
           message="REFLEX_PROMOTED: {result.name} → ACTIVE"
      UPDATE reflex.state = ACTIVE
      UPDATE reflex.trust_start = now  ; 0.5× agent clock starts

; ── Step 3: Check for retired reflexes that have new candidates ──
ASK  channel=pattern_discovery
     question="candidates_for_retired_reflexes"
  → candidates on stack

FOR_EACH candidate IN candidates:
  TELL  channel=generator_agent
       message="GENERATE_REFLEX from_pattern={candidate.pattern_id}"
  ; This triggers Pattern 4.1 (Observe-Record-Discover) →
  ; Pattern 4.4 (Pattern-to-Reflex Compilation) →
  ; Pattern 4.2 (A/B Reflex Testing)
  UPDATE reflex.state = SHADOW

; ── Step 4: Report fleet health ──
TELL  channel=fleet_broadcast/health
     message="FLEET_HEALTH: {active}/{total} reflexes active, "
            "{standby} standby, {shadow} testing, {retired} retired"
```

**Consequences:**

*Benefits:* The entire reflex lifecycle is automated — from discovery to deployment to retirement to re-deployment — without human intervention (at trust Level 4+). The state machine provides clear, predictable transitions. The 7-day retirement timeout prevents permanently stuck reflexes from consuming resources. The fleet health broadcast gives operators continuous visibility into the system's state.

*Trade-offs:* The orchestration agent itself is trust-gated: it can only manage reflexes within its own trust level. At Level 3, it can promote shadow reflexes that passed A/B testing. At Level 4, it can retire reflexes and generate new candidates. At Level 5, it operates fully autonomously. The 7-day retirement timeout is conservative — some reflexes may recover given more time, but the system frees the reflex slot for new candidates.

*Failure mode:* If the orchestration agent makes a bad retirement decision (retiring a reflex that would have recovered), the retired reflex's pattern ID is preserved. When a new candidate is generated for the same pattern, the system can compare it to the retired version and potentially deploy a variant with different parameters. If the orchestration agent's own trust drops, it cannot make retirement/promotion decisions — the system freezes in its current state until trust recovers.

**Marine Example:** A fishing fleet's orchestration agent manages 47 reflexes across 3 vessels. After a storm, 8 reflexes drop to STANDBY (trust below threshold due to rough-sea bad windows). Over the next 14 days, 6 recover through normal INCREMENTS operation and return to ACTIVE. Two reflexes (sonar-based fish detection and wave-compensated net tension) remain at t_floor for 10 consecutive days. The orchestration agent retires both, freeing 2 reflex slots. Pattern discovery identifies improved candidates for both (trained on the storm data, which provides valuable high-sea observations). New candidates enter SHADOW testing. After A/B testing passes, they are promoted to ACTIVE with fresh trust starting at t_floor (0.10) and the 0.5× agent multiplier.

---

## Appendix: Quick Reference

### Pattern-to-Opcode Mapping

| Pattern | Key Opcodes | Key Messages |
|---------|-------------|--------------|
| Intention Block | 0x20 (DECLARE_INTENT), 0x40 (REQUIRE_CAPABILITY), 0x50 (TRUST_CHECK) | REFLEX_DEPLOY (0x09) |
| Trust-Gated Reflex | 0x50 (TRUST_CHECK), 0x51 (AUTONOMY_LEVEL_ASSERT) | HEARTBEAT (0x01) |
| Graceful Degradation | 0x40 (OPTIONAL flag), 0x43 (DECLARE_ACTUATOR_USE) | HEARTBEAT (escalation states) |
| Capability-Bounded | 0x40 (REQUIRE_CAPABILITY), 0x42 (DECLARE_SENSOR_NEED) | DEVICE_IDENTITY (0x01), AUTO_DETECT_RESULT (0x1B) |
| Generator-Validator | AAB TLV tags 0x01–0x0E | TELL (0x30) with validation report |
| Ask-Tell-Delegate | 0x30 (TELL), 0x31 (ASK), 0x32 (DELEGATE) | EMIT_EVENT syscall, MQTT topics |
| Fleet Broadcast | 0x30 (TELL, fleet channel) | MQTT QoS 2 broadcast topics |
| Emergency Override | 0x34 (REQUEST_OVERRIDE), 0x56 (SAFETY_EVENT_EMIT) | HEARTBEAT (state machine) |
| Defense in Depth | Hardware kill, ISR guard, CLAMP_F, TRUST_CHECK | SAFETY_EVENT (all levels) |
| Fail-Safe Default | CLAMP_F (0x0A), WRITE_PIN with 0.0 default | Pull-down resistors (hardware) |
| Trust Decay Recovery | INCREMENTS algorithm (α_gain=0.002, α_loss=0.05) | TELL fleet_broadcast/trust |
| Adversarial Resistance | Static verification, runtime sandbox, anomaly detection | SAFETY_EVENT with BOCPD alert |
| Observe-Record-Discover | RECORD_SNAPSHOT syscall | MQTT telemetry topics |
| A/B Reflex Testing | Shadow actuator registers (32–63) | REFLEX_STATUS, TELL ab_results |
| Trust-Gated Learning | ASK trust_engine + conditional TELL to pipeline | TELL with MODE: OBSERVE/DISCOVER/TEST |
| Pattern-to-Reflex | Agent compilation pipeline (Qwen + Claude) | DELEGATE to generator agent |
| Consensus Navigation | Raft protocol on Jetson cluster | MQTT PROPOSE/ACK/COMMIT |
| Load-Balanced Assignment | Suitability scoring algorithm | DELEGATE per-vessel tasks |
| Scout-Report-Act | EMIT_EVENT obstacle_detected + TELL report | Fleet broadcast with survey data |
| Emergent Behavior Control | Independent reflexes + shared environment | Fleet broadcast aggregation |

### Trust Parameters Quick Reference

| Parameter | Value | Notes |
|-----------|-------|-------|
| α_gain (human code) | 0.002 per good window | τ_g ≈ 500 windows ≈ 20.8 days |
| α_gain (agent code) | 0.001 per good window | 0.5× multiplier; τ_g ≈ 1000 windows ≈ 41.7 days |
| α_loss | 0.050 per bad window | τ_l ≈ 20 windows ≈ 20 hours |
| Loss-to-gain ratio | 25:1 | 22× faster to lose than gain (human code) |
| Trust floor (t_floor) | 0.10 | Minimum trust score |
| Trust max (t_max) | 0.99 | Asymptotic maximum |
| Window duration | 3600 seconds (1 hour) | Trust update interval |
| Agent multiplier | 0.5× | Agent code earns trust at half rate |

### Autonomy Level Thresholds

| Level | Name | Trust Range | Typical Capability |
|-------|------|-------------|-------------------|
| L0 | Manual | — | Human controls everything |
| L1 | Advisory | 0.10–0.30 | System monitors and advises |
| L2 | Assisted | 0.30–0.50 | System suggests, human approves |
| L3 | Supervised | 0.50–0.70 | System acts, human monitors |
| L4 | Autonomous | 0.70–0.90 | System acts independently |
| L5 | Full | 0.90–0.99 | No human oversight required |

---

*This document is part of the NEXUS User Education series. For the full specification suite, see [[specs/00_MASTER_INDEX.md]]. For the A2A-native language design, see [[a2a-native-language/language_design_and_semantics.md]]. For the trust algorithm specification, see [[specs/safety/trust_score_algorithm_spec.md]].*
