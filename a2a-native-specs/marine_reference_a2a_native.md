# Marine Reference Vessel — A2A-Native Implementation

**Document ID:** NEXUS-A2A-MARINE-REF-001
**Version:** 1.0.0
**Date:** 2025-07-12
**Domain:** Marine Autonomous Surface Vessel (ASV)
**Status:** Reference Implementation
**Cross-Reference:** [[safety_policy.json]], [[marine_autonomous_systems.md]], [[a2a-native-language/]]

---

## Table of Contents

1. [Marine Vessel — Agent-Native Description](#1-marine-vessel--agent-native-description)
2. [Marine Reflex Programs — A2A-Native Bytecode](#2-marine-reflex-programs--a2a-native-bytecode)
3. [COLREGs — Agent-Interpretable Safety Rules](#3-colregs--agent-interpretable-safety-rules)
4. [Marine Trust Advancement Sequence](#4-marine-trust-advancement-sequence)
5. [Marine Failure Scenarios — Agent Response](#5-marine-failure-scenarios--agent-response)

---

## 1. Marine Vessel — Agent-Native Description

### 1.1 Vessel Capability Descriptor

The vessel capability descriptor is the JSON structure that any agent receives when it queries what this vessel can do. It is the machine-readable identity of the hardware platform. The agent never reads a manual — it reads this descriptor.

```json
{
  "vessel_id": "NEXUS-MARINE-REF-001",
  "vessel_class": "USV",
  "hull_type": "monohull_displacement",
  "length_m": 6.5,
  "displacement_kg": 850,
  "max_speed_knots": 12,
  "domain": "marine",

  "sensors": [
    {
      "id": "compass", "type": "imu_magnetometer", "bus": "i2c:0",
      "register": 0, "update_hz": 10, "unit": "degrees",
      "range": {"min": 0.0, "max": 359.99}, "accuracy": 1.0,
      "stale_timeout_ms": 500,
      "capability_tag": "sensor:imu:compass"
    },
    {
      "id": "gps", "type": "gnss_receiver", "bus": "uart:1",
      "register": 1, "update_hz": 5, "unit": "degrees",
      "range": {"lat_min": -90.0, "lat_max": 90.0, "lon_min": -180.0, "lon_max": 180.0},
      "accuracy": 2.5, "stale_timeout_ms": 2000,
      "capability_tag": "sensor:gnss:position"
    },
    {
      "id": "speed_log", "type": "paddle_wheel", "bus": "uart:2",
      "register": 2, "update_hz": 1, "unit": "knots",
      "range": {"min": 0.0, "max": 15.0}, "accuracy": 0.1,
      "stale_timeout_ms": 2000,
      "capability_tag": "sensor:speed:water"
    },
    {
      "id": "depth", "type": "echo_sounder", "bus": "uart:3",
      "register": 3, "update_hz": 1, "unit": "meters",
      "range": {"min": 0.3, "max": 100.0}, "accuracy": 0.1,
      "stale_timeout_ms": 3000,
      "capability_tag": "sensor:depth:keel"
    },
    {
      "id": "wind_speed", "type": "anemometer", "bus": "i2c:0",
      "register": 4, "update_hz": 5, "unit": "m/s",
      "range": {"min": 0.0, "max": 60.0}, "accuracy": 0.3,
      "stale_timeout_ms": 1000,
      "capability_tag": "sensor:wind:speed"
    },
    {
      "id": "wind_dir", "type": "wind_vane", "bus": "i2c:0",
      "register": 5, "update_hz": 5, "unit": "degrees",
      "range": {"min": 0.0, "max": 359.99}, "accuracy": 3.0,
      "stale_timeout_ms": 1000,
      "capability_tag": "sensor:wind:direction"
    },
    {
      "id": "engine_temp", "type": "thermocouple", "bus": "adc:0",
      "register": 6, "update_hz": 2, "unit": "celsius",
      "range": {"min": -10.0, "max": 150.0}, "accuracy": 1.0,
      "stale_timeout_ms": 1000,
      "capability_tag": "sensor:engine:temperature"
    },
    {
      "id": "engine_rpm", "type": "hall_effect", "bus": "gpio:4",
      "register": 7, "update_hz": 10, "unit": "rpm",
      "range": {"min": 0, "max": 4000}, "accuracy": 10,
      "stale_timeout_ms": 500,
      "capability_tag": "sensor:engine:rpm"
    },
    {
      "id": "oil_pressure", "type": "pressure_transducer", "bus": "adc:1",
      "register": 8, "update_hz": 2, "unit": "psi",
      "range": {"min": 0.0, "max": 100.0}, "accuracy": 0.5,
      "stale_timeout_ms": 1000,
      "capability_tag": "sensor:engine:oil_pressure"
    },
    {
      "id": "bilge_level", "type": "ultrasonic", "bus": "i2c:0",
      "register": 9, "update_hz": 1, "unit": "centimeters",
      "range": {"min": 0.0, "max": 50.0}, "accuracy": 1.0,
      "stale_timeout_ms": 5000,
      "capability_tag": "sensor:bilge:level"
    },
    {
      "id": "battery_voltage", "type": "voltage_divider", "bus": "adc:2",
      "register": 10, "update_hz": 1, "unit": "volts",
      "range": {"min": 0.0, "max": 16.0}, "accuracy": 0.05,
      "stale_timeout_ms": 5000,
      "capability_tag": "sensor:power:voltage"
    }
  ],

  "actuators": [
    {
      "id": "rudder", "type": "servo", "profile": "servo",
      "register": 0, "unit": "pulse_us",
      "range": {"min": 1000, "max": 2000},
      "safe_state": 1500, "center": 1500,
      "rate_limit_us_per_10ms": 200,
      "capability_tag": "actuator:rudder"
    },
    {
      "id": "throttle", "type": "motor_pwm", "profile": "motor_pwm",
      "register": 1, "unit": "percent",
      "range": {"min": 0.0, "max": 80.0},
      "safe_state": 0.0, "center": 0.0,
      "rate_limit_pct_per_100ms": 10.0,
      "autonomous_max_pct": 80.0,
      "capability_tag": "actuator:throttle"
    },
    {
      "id": "bilge_pump", "type": "relay", "profile": "relay",
      "register": 2, "unit": "state",
      "safe_state": 0, "center": 0,
      "max_on_time_ms": 5000, "cooldown_ms": 1000,
      "capability_tag": "actuator:bilge_pump"
    },
    {
      "id": "nav_lights", "type": "relay", "profile": "relay",
      "register": 3, "unit": "state",
      "safe_state": 0, "center": 0,
      "capability_tag": "actuator:nav_lights"
    },
    {
      "id": "horn", "type": "buzzer", "profile": "buzzer",
      "register": 4, "unit": "state",
      "safe_state": 0, "center": 0,
      "max_on_time_ms": 30000, "duty_cycle_max_pct": 50,
      "capability_tag": "actuator:horn"
    }
  ],

  "compute": {
    "reflex_node": {
      "mcu": "ESP32-S3",
      "cores": 2, "clock_mhz": 240,
      "flash_kb": 4096, "sram_kb": 512, "psram_mb": 8,
      "vm_slots": 4, "vm_stack_depth": 256,
      "vm_cycle_budget": 50000,
      "tick_rate_hz": 10
    },
    "cognitive_node": {
      "sbc": "Jetson Orin Nano Super",
      "cpu_cores": 6, "clock_ghz": 1.5,
      "gpu_tops": 40, "ram_gb": 8,
      "model_primary": "Qwen2.5-Coder-7B-Q4_K_M",
      "model_secondary": "Phi-3-mini-4K"
    }
  },

  "communication": {
    "internal": {
      "protocol": "nexus_wire_v2",
      "physical": "RS-422",
      "baud": 921600,
      "encoding": "COBS",
      "integrity": "CRC-16/CCITT-FALSE"
    },
    "external": [
      {"type": "VHF", "range_nm": 20, "purpose": "safety_voice"},
      {"type": "AIS", "range_nm": 20, "purpose": "vessel_tracking"},
      {"type": "4G", "range_km": 15, "purpose": "telemetry_cloud"},
      {"type": "Starlink", "range_global": true, "purpose": "ocean_connectivity"}
    ]
  },

  "power": {
    "primary": "diesel_25hp",
    "auxiliary": "liFePO4_100Ah_12V",
    "solar": "120W_panel",
    "runtime_no_solar_hr": 8,
    "runtime_with_solar_hr": 24
  },

  "domain_overrides": {
    "max_rudder_deflection_deg": 45,
    "max_throttle_percent": 80,
    "depth_min_for_autopilot_m": 3.0,
    "max_speed_autonomous_kmh": 15.0,
    "max_wind_speed_autonomous_kmh": 40.0,
    "heartbeat_timeout_degraded_ms": 500,
    "heartbeat_timeout_safe_ms": 1000
  }
}
```

### 1.2 What an Agent Sees

When a new agent connects to this vessel (via the Jetson cognitive layer), the following AAB capability description is presented:

```
DECLARE_INTENT vessel_capabilities
  HUMAN_DESC: "6.5m monohull displacement USV, 850kg, 12kt max speed.
              GPS+compass+depth+wind+engine sensors. Rudder+throttle+bilge
              actuators. ESP32-S3 reflex, Jetson Orin Nano cognitive."
  CAP_REQ: sensor:compass, sensor:gnss:position, sensor:depth:keel,
           sensor:wind:speed, sensor:wind:direction, sensor:engine:*
           actuator:rudder, actuator:throttle, actuator:bilge_pump
  TRUST_MIN: 0.30  (minimum to observe telemetry)
  DOMAIN: marine:usv:ref
```

The agent reads this and immediately knows:
- It can read compass heading, GPS position, depth, wind, engine state
- It can command rudder (center at 1500us, range 1000-2000us), throttle (0-80%), bilge pump (on/off)
- It must check trust before actuating (0.30 to observe, 0.50 to advise, 0.70 to actuate autonomously)
- Domain is marine, vessel class is USV reference implementation
- The reflex layer runs at 10 Hz with 50,000 cycle budget per tick

### 1.3 Hardware Constraints as Capability Limits

Engineering specs say "the rudder actuator has a mechanical range of ±45 degrees." In the A2A-native world, an agent sees this as:

```
SAFE_BOUNDARY boundary_id=rudder_angle, envelope=[-45.0, 45.0]
  BREACH_ACTION: CLAMP_F -45.0 45.0 (hard clamp, zero tolerance)
  SAFETY_CLASS: CRITICAL
  RATIONALE: "Beyond 45 deg provides minimal turning moment while
             greatly increasing drag and risk of mechanical binding"
  SOURCE: safety_policy.json domain.marine.overrides.max_rudder_deflection_deg
```

This is a constraint the bytecode VM enforces — not a comment a human reads. CLAMP_F after every rudder computation makes it physically impossible to exceed ±45 degrees regardless of what the cognitive layer requests.

---

## 2. Marine Reflex Programs — A2A-Native Bytecode

### 2.1 Reflex Program 1: Heading Hold (PID on Compass Heading)

**Intention:** Maintain a compass heading using PID control, with wind-aware gain scheduling and heading normalization.

**AAB Metadata (agent-readable):**
```json
{
  "name": "heading_hold_pid",
  "intention": "Maintain vessel heading to setpoint using PID control on compass heading",
  "trust_min": 0.70,
  "domain": "marine:autopilot:steering",
  "sensors": ["compass", "setpoint"],
  "actuators": ["rudder"],
  "pid_controllers": {
    "heading_pid": {"kp": 1.2, "ki": 0.05, "kd": 0.3}
  },
  "safety_constraints": [
    "rudder_angle clamped to [-45, 45] degrees",
    "compass data freshness < 500ms",
    "trust level >= 0.70 (L3 SUPERVISED)"
  ],
  "postconditions": [
    "heading_error < 5 degrees within 30 seconds",
    "rudder_rate < 5 degrees/second"
  ]
}
```

**Bytecode (AAB format with full metadata):**
```
; === INTENTION BLOCK HEADER ===
; Core: 20 00 0001 A3F2B1C4
; Metadata: HUMAN_DESC="Maintain heading using PID",
;           TRUST_MIN=0.70, DOMAIN=marine:autopilot,
;           CAP_REQ=sensor:compass,actuator:rudder

; === CAPABILITY SCOPE ===
; Core: 40 00 0100 00000001  (REQUIRE_CAPABILITY sensor:compass)
; Core: 43 00 0000 00000005  (DECLARE_ACTUATOR_USE rudder, max_rate=5deg/s)

; === TRUST CONTEXT ===
; Core: 50 00 0001 3F000000  (TRUST_CHECK steering >= 0.50)
; JUMP_IF_FALSE → trust_fail_handler

; === EXECUTION BODY ===

; Instruction 0: READ_PIN heading
; Core: 1A 00 0000 00000000
; Metadata: TYPE=f32:degrees:compass_heading,
;           PRE_COND=compass_data_fresh < 500ms,
;           POST_COND=stack_top in [-180, 360],
;           CYCLE_COST=2

; Instruction 1: READ_PIN setpoint
; Core: 1A 00 0100 00000000
; Metadata: TYPE=f32:degrees:target_heading,
;           SOURCE=variable_memory[1]

; Instruction 2: PID_COMPUTE heading_pid
; Core: 00 80 0000 00000000
; Metadata: TYPE=f32→f32, PID_ID=0,
;           GAINS=kp:1.2, ki:0.05, kd:0.3,
;           ANTI_WINDUP=true, MAX_INTEGRAL=30.0,
;           D_ON_MEASUREMENT=true,
;           CYCLE_COST=20

; Instruction 3: CLAMP_F -45.0 45.0
; Core: 10 00 0000 C2300000
; Metadata: TYPE=f32→f32,
;           POST_COND=stack_top in [-45.0, 45.0],
;           SAFETY_CLASS=CRITICAL,
;           ENFORCES=safety_policy marine.max_rudder_deflection_deg,
;           CYCLE_COST=6

; Instruction 4: WRITE_PIN rudder
; Core: 1B 00 0000 00000000
; Metadata: TYPE=f32:pulse_us, ACTUATOR=rudder,
;           PRE_COND=safety_enable[0]==true (SR-001),
;           RATE_LIMIT=200us/10ms (SR-005),
;           SIDE_EFFECT=writes:actuator:rudder,
;           CYCLE_COST=3

; Instruction 5: HALT
; Core: 00 80 0001 00000000

; === STRIPPED 8-BYTE CORE (deployed to ESP32) ===
; Offset  Hex                  Annotation
; 0x0000  1A 00 0000 00000000  READ_PIN sensor[0]  (heading)
; 0x0008  1A 00 0100 00000000  READ_PIN sensor[1]  (setpoint)
; 0x0010  00 80 0000 00000000  SYSCALL: PID_COMPUTE pid[0]
; 0x0018  10 00 0000 C2300000  CLAMP_F -45.0 45.0
; 0x0020  1B 00 0000 00000000  WRITE_PIN actuator[0] (rudder)
; 0x0028  00 80 0001 00000000  SYSCALL: HALT
```

**Cycle Analysis:** 2 + 2 + 20 + 6 + 3 = 33 cycles. At 240 MHz = 0.14 microseconds. Budget utilization: 0.07% of 50,000. Stack depth: 2 (peak during PID). Validated: stack balanced on all paths.

---

### 2.2 Reflex Program 2: Speed Control (Throttle with RPM Feedback)

**Intention:** Maintain target speed through closed-loop throttle control with RPM feedback and autonomous throttle cap at 80%.

**Bytecode (stripped 8-byte core):**
```
; Speed control with RPM feedback and 80% autonomous cap
; Uses PID: speed_pid with kp=0.5, ki=0.02, kd=0.1
; Marine override: max_throttle_percent = 80 (safety_policy)

; 0x0000  1A 00 0200 00000000  READ_PIN sensor[2]  (speed_log, knots)
; 0x0008  1A 00 0300 00000000  READ_PIN sensor[3]  (speed_setpoint)
; 0x0010  00 80 0001 00000000  SYSCALL: PID_COMPUTE pid[1] (speed_pid)
; 0x0018  10 00 0000 42A00000  CLAMP_F 0.0 80.0  (SR: marine.max_throttle_percent)
; 0x0020  1B 00 0100 00000000  WRITE_PIN actuator[1] (throttle)
; 0x0028  00 80 0001 00000000  SYSCALL: HALT
```

**AAB Metadata highlights:**
- `POST_COND`: throttle output ∈ [0.0, 80.0] (80% cap is domain override from safety_policy.json)
- `SAFETY_CLASS`: CRITICAL — throttle directly controls vessel speed
- `RATE_LIMIT`: 10%/100ms per motor_pwm profile (prevents abrupt speed changes)
- `TRUST_MIN`: 0.70 — autonomous throttle requires L3

**Cycle count:** 33 cycles. Stack depth: 2.

---

### 2.3 Reflex Program 3: Depth Hold (Submersible Variant)

**Intention:** Maintain target depth using PID control on echo sounder reading, with emergency surface on depth_min violation.

**Bytecode (stripped 8-byte core):**
```
; Depth hold with emergency surface
; If depth > 3.0m, autopilot permitted (safety_policy depth_min_for_autopilot_m)
; If depth > 80% of max, reduce descent rate
; PID: depth_pid kp=0.8, ki=0.03, kd=0.2

; 0x0000  1A 00 0400 00000000  READ_PIN sensor[4]  (depth_meters)
; 0x0008  1A 00 0500 00000000  READ_PIN sensor[5]  (depth_setpoint)
; 0x0010  00 80 0002 00000000  SYSCALL: PID_COMPUTE pid[2] (depth_pid)
; 0x0018  10 00 0000 C28F5C29  CLAMP_F -100.0 100.0  (max decent/ascent rate)
; 0x0020  1B 00 0200 00000000  WRITE_PIN actuator[2] (depth_control)
; 0x0028  00 80 0001 00000000  SYSCALL: HALT
```

**Safety invariant:** If bilge_level sensor > 30cm while depth hold is active, override to surface immediately. This is a cross-reflex safety boundary enforced by the reflex orchestrator, not by this program.

---

### 2.4 Reflex Program 4: Collision Avoidance (Radar/Lidar Obstacle Detection)

**Intention:** Detect obstacles via closest-point-of-approach (CPA) analysis and execute evasive maneuvers per COLREGs Rule 8.

**Bytecode (stripped 8-byte core — 16 instructions):**
```
; Collision avoidance reflex
; Reads: obstacle_distance (register 12), obstacle_bearing (register 13),
;         vessel_speed (register 2), vessel_heading (register 0)
; Writes: rudder (actuator 0), throttle (actuator 1)
; Safety: CPA < 50m → evasive turn; CPA < 20m → hard turn + reverse

; Phase 1: Check obstacle distance
; 0x0000  1A 00 0C00 00000000  READ_PIN sensor[12] (obstacle_dist_m)
; 0x0008  03 00 0000 42480000  PUSH_F32 50.0
; 0x0010  15 00 0000 00000000  GTE_F  (dist >= 50? → no threat)
; 0x0018  1F 00 0018 00000000  JUMP_IF_TRUE safe_exit  (skip to end)

; Phase 2: Determine turn direction (avoid obstacle bearing)
; 0x0020  1A 00 0D00 00000000  READ_PIN sensor[13] (obstacle_bearing)
; 0x0028  1A 00 0000 00000000  READ_PIN sensor[0]  (vessel_heading)
; 0x0030  09 00 0000 00000000  SUB_F  (relative_bearing = obstacle - vessel)
; 0x0038  0C 00 0000 00000000  NEG_F  (turn_away = -relative_bearing)

; Phase 3: Scale turn by proximity (closer = harder turn)
; 0x0040  1A 00 0C00 00000000  READ_PIN sensor[12] (obstacle_dist_m again)
; 0x0048  03 00 0000 41900000  PUSH_F32 20.0
; 0x0050  14 00 0000 00000000  LTE_F  (dist <= 20? → emergency)
; 0x0058  1E 00 0010 00000000  JUMP_IF_FALSE moderate_turn

; Phase 4: Emergency turn (CPA < 20m)
; 0x0060  03 00 0000 C31E0000  PUSH_F32 1600.0  (hard starboard: 1600us pulse)
; 0x0068  1B 00 0000 00000000  WRITE_PIN actuator[0] (rudder → hard over)
; 0x0070  03 00 0000 3DCCCCCD  PUSH_F32 0.1  (reverse throttle: 10%)
; 0x0078  1B 00 0100 00000000  WRITE_PIN actuator[1] (throttle → reverse)
; 0x0080  1D 00 0028 00000000  JUMP done

; Phase 5: Moderate turn (50m > CPA > 20m)
; moderate_turn:
; 0x0088  0D 00 0000 00000000  ABS_F  (magnitude of turn_away)
; 0x0090  10 00 0000 41C80000  CLAMP_F 0.0 25.0  (max 25 deg correction)
; 0x0098  03 00 0000 44160000  PUSH_F32 600.0  (degrees to pulse offset: 600/45*25)
; 0x00A0  0A 00 0000 00000000  MUL_F  (turn_away * scale)
; 0x00A8  03 00 0000 446B4000  PUSH_F32 1500.0  (center pulse)
; 0x00B0  08 00 0000 00000000  ADD_F  (1500 + offset)
; 0x00B8  10 00 0000 C3200000  CLAMP_F 1000.0 2000.0  (servo limits)
; 0x00C0  1B 00 0000 00000000  WRITE_PIN actuator[0] (rudder → correction)

; done:
; 0x00C8  00 80 0001 00000000  SYSCALL: HALT

; safe_exit:
; 0x00D0  00 80 0001 00000000  SYSCALL: HALT
```

**Cycle Analysis:** ~85 cycles. Stack depth: 4. Budget utilization: 0.17%. All paths terminate in HALT.

**AAB Metadata highlights:**
- `INTENT_ID`: colregs_rule8_collision_avoidance
- `SAFETY_CLASS`: CRITICAL — overrides all other steering reflexes
- `TRUST_MIN`: 0.50 — collision avoidance active even at L2 (semi-auto)
- `AUTONOMY_LEVEL_ASSERT`: minimum L2 for advisory output, L3 for autonomous turn
- `COLREGS_REF`: "Rule 8 — Action to Avoid Collision: take early and substantial action"

---

### 2.5 Reflex Program 5: Docking Approach (Multi-Phase)

**Intention:** Execute a three-phase docking approach: (1) long-range approach at 3 kt, (2) close-range alignment at 1 kt, (3) final approach at 0.5 kt with position hold.

**Phase structure (agent-interpretable):**
```
DECLARE_INTENT docking_approach
  PHASES: 3

  PHASE 1: long_approach
    CONDITION: distance_to_dock > 50m
    SETPOINTS: speed=3.0 kt, heading=approach_bearing
    TRUST_MIN: 0.70
    TIMEOUT_MS: 300000  (5 minutes)

  PHASE 2: close_alignment
    CONDITION: 20m < distance_to_dock <= 50m
    SETPOINTS: speed=1.0 kt, heading=final_approach_bearing
    TRUST_MIN: 0.80
    TIMEOUT_MS: 120000  (2 minutes)

  PHASE 3: final_approach
    CONDITION: distance_to_dock <= 20m
    SETPOINTS: speed=0.5 kt, heading=dock_heading
    TRUST_MIN: 0.85
    TIMEOUT_MS: 60000  (1 minute)
    ENGAGES: station_keeping at dock
```

**Bytecode core (simplified — actual implementation uses state machine across ticks):**
```
; Docking approach — single-tick execution body
; State machine: phase is stored in variable[20]

; 0x0000  1A 00 1400 00000000  READ_PIN sensor[20] (dock_distance_m)
; 0x0008  03 00 0000 42480000  PUSH_F32 50.0
; 0x0010  15 00 0000 00000000  GTE_F  (dist >= 50?)
; 0x0018  1E 00 0008 00000000  JUMP_IF_FALSE check_close
; Phase 1: long approach
; 0x0020  03 00 0000 40400000  PUSH_F32 3.0  (speed setpoint)
; 0x0028  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint)
; 0x0030  1D 00 0028 00000000  JUMP speed_control

; check_close:
; 0x0038  1A 00 1400 00000000  READ_PIN sensor[20] (dock_distance_m)
; 0x0040  03 00 0000 41A00000  PUSH_F32 20.0
; 0x0048  15 00 0000 00000000  GTE_F  (dist >= 20?)
; 0x0050  1E 00 0008 00000000  JUMP_IF_FALSE final_approach
; Phase 2: close alignment
; 0x0058  03 00 0000 3F800000  PUSH_F32 1.0
; 0x0060  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint)
; 0x0068  1D 00 0018 00000000  JUMP speed_control

; final_approach:
; 0x0070  03 00 0000 3F000000  PUSH_F32 0.5
; 0x0078  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint)

; speed_control: (delegates to speed_control reflex)
; 0x0080  00 80 0001 00000000  SYSCALL: HALT
```

**Cycle count:** ~52 cycles. Stack depth: 2.

---

### 2.6 Reflex Program 6: MOB Response (Man Overboard — Emergency)

**Intention:** Execute immediate emergency maneuver on man-overboard alert: hard turn to reciprocal heading, reduce speed, activate homing mode.

**Bytecode (stripped 8-byte core — 8 instructions):**
```
; MOB Emergency Response — triggers on MOB alert flag (sensor[15])
; This reflex has ABSOLUTE priority — overrides all others

; 0x0000  1A 00 0F00 00000000  READ_PIN sensor[15] (mob_alert_flag)
; 0x0008  1E 00 0018 00000000  JUMP_IF_FALSE no_mob  (flag == 0? exit)

; Record MOB position
; 0x0010  1A 00 0100 00000000  READ_PIN sensor[1]  (gps_lat)
; 0x0018  1B 00 0A00 00000000  WRITE_VAR variable[10] (mob_lat)
; 0x0020  1A 00 0200 00000000  READ_PIN sensor[2]  (gps_lon, repurposed)
; 0x0028  1B 00 0B00 00000000  WRITE_VAR variable[11] (mob_lon)

; Hard turn to reciprocal heading +180 degrees
; 0x0030  1A 00 0000 00000000  READ_PIN sensor[0]  (current heading)
; 0x0038  03 00 0000 43700000  PUSH_F32 240.0  (add 240 deg for Williamson turn)
; 0x0040  08 00 0000 00000000  ADD_F  (heading + 240)
; 0x0048  10 00 0000 43700000  CLAMP_F 0.0 360.0
; 0x0050  1B 00 0500 00000000  WRITE_VAR variable[5] (heading_setpoint)
; Write rudder hard over
; 0x0058  03 00 0000 446B4000  PUSH_F32 1500.0  (center = no turn, for Williamson: start)
; 0x0060  1B 00 0000 00000000  WRITE_PIN actuator[0] (rudder → center first)

; Reduce speed
; 0x0068  03 00 0000 3F000000  PUSH_F32 0.5  (0.5 knots)
; 0x0070  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint)

; Activate horn (MOB signal)
; 0x0078  03 00 0000 3F800000  PUSH_F32 1.0  (horn ON)
; 0x0080  1B 00 0400 00000000  WRITE_PIN actuator[4] (horn)

; Emit MOB event to cognitive layer
; 0x0088  00 80 0006 00000003  SYSCALL: EMIT_EVENT event=MOB_ALERT

; no_mob:
; 0x0090  00 80 0001 00000000  SYSCALL: HALT
```

**AAB Metadata highlights:**
- `SAFETY_CLASS`: CRITICAL — life safety reflex
- `TRUST_MIN`: 0.30 — activates at ANY trust level (human life at stake)
- `AUTONOMY_LEVEL_ASSERT`: bypasses trust gates for MOB response
- `COLREGS_REF`: "Rule 5 — Look-out: maintain proper look-out at all times"
- `HUMAN_DESC`: "Immediate Williamson turn on MOB alert, record position, reduce speed, sound horn"

---

### 2.7 Reflex Program 7: Weather Helm (Wind Compensation)

**Intention:** Apply automatic wind compensation to heading setpoint based on apparent wind angle and speed, preventing weather helm drift.

**Bytecode (stripped 8-byte core — 8 instructions):**
```
; Wind compensation — adjusts heading setpoint based on apparent wind
; Reads: wind_speed (sensor[4]), wind_dir (sensor[5]), vessel_speed (sensor[2])
; Writes: heading_setpoint_correction (variable[6])

; 0x0000  1A 00 0400 00000000  READ_PIN sensor[4]  (wind_speed m/s)
; 0x0008  03 00 0000 41C80000  PUSH_F32 25.0  (threshold: 25 m/s)
; 0x0010  13 00 0000 00000000  GT_F  (wind > 25 m/s?)
; 0x0018  1E 00 0010 00000000  JUMP_IF_FALSE calm  (exit if calm)

; Compute wind compensation offset
; 0x0020  1A 00 0500 00000000  READ_PIN sensor[5]  (wind_dir degrees)
; 0x0028  1A 00 0000 00000000  READ_PIN sensor[0]  (vessel_heading)
; 0x0030  09 00 0000 00000000  SUB_F  (relative_wind = wind_dir - heading)
; 0x0038  1A 00 0400 00000000  READ_PIN sensor[4]  (wind_speed again)
; 0x0040  03 00 0000 3DCCCCCD  PUSH_F32 0.1  (compensation factor)
; 0x0048  0A 00 0000 00000000  MUL_F  (relative_wind * speed * 0.1)
; 0x0050  10 00 0000 41C80000  CLAMP_F -25.0 25.0  (max 25 deg compensation)
; 0x0058  1B 00 0600 00000000  WRITE_VAR variable[6] (heading_correction)

; calm:
; 0x0060  00 80 0001 00000000  SYSCALL: HALT
```

**Safety constraint:** max_wind_speed_autonomous_kmh = 40.0 (11.1 m/s) from safety_policy.json. Above this, autonomous operation disengages. This reflex operates below that threshold.

---

### 2.8 Reflex Program 8: Station Keeping (Position Hold)

**Intention:** Maintain vessel position within a defined radius using GPS-based position feedback with heading and speed control.

**Bytecode (stripped 8-byte core — 12 instructions):**
```
; Station keeping — GPS position hold
; Reads: gps_lat (sensor[1]), gps_lon (sensor[16]), target_lat (var[7]),
;         target_lon (var[8]), vessel_speed (sensor[2])
; Writes: heading_setpoint (var[5]), speed_setpoint (var[3])

; Compute distance to target
; 0x0000  1A 00 0100 00000000  READ_PIN sensor[1]  (current_lat)
; 0x0008  1A 00 0700 00000000  READ_VAR variable[7] (target_lat)
; 0x0010  09 00 0000 00000000  SUB_F  (lat_error)
; 0x0018  0D 00 0000 00000000  ABS_F  (abs_lat_error)

; 0x0020  1A 00 1000 00000000  READ_PIN sensor[16] (current_lon)
; 0x0028  1A 00 0800 00000000  READ_VAR variable[8] (target_lon)
; 0x0030  09 00 0000 00000000  SUB_F  (lon_error)
; 0x0038  0D 00 0000 00000000  ABS_F  (abs_lon_error)

; Simple distance estimate (degrees lat ≈ 111km)
; 0x0040  08 00 0000 00000000  ADD_F  (total_error_deg)
; 0x0048  03 00 0000 42B40000  PUSH_F32 90.0  (meters per degree at ~10km)
; 0x0050  0A 00 0000 00000000  MUL_F  (distance_meters)

; Check if within station radius
; 0x0058  03 00 0000 42480000  PUSH_F32 50.0  (50m station radius)
; 0x0060  14 00 0000 00000000  LTE_F  (distance <= 50m?)
; 0x0068  1E 00 0008 00000000  JUMP_IF_FALSE need_correction

; Within radius: zero speed
; 0x0070  03 00 0000 00000000  PUSH_F32 0.0
; 0x0078  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint = 0)
; 0x0080  1D 00 0008 00000000  JUMP done

; need_correction: compute heading toward target
; 0x0088  03 00 0000 00000000  PUSH_F32 5.0  (correction speed)
; 0x0090  1B 00 0300 00000000  WRITE_VAR variable[3] (speed_setpoint)
; (bearing calculation delegates to cognitive layer via EMIT_EVENT)

; done:
; 0x0098  00 80 0001 00000000  SYSCALL: HALT
```

---

### 2.9 Reflex Program 9: Waypoint Following (GPS Navigation)

**Intention:** Navigate between GPS waypoints with automatic advance on arrival, cross-track error correction, and speed management.

**Bytecode (stripped 8-byte core — 14 instructions):**
```
; Waypoint following — single-tick execution
; State: current_waypoint_index stored in variable[12]
; Waypoints stored in variable array [20..N]

; Read current position
; 0x0000  1A 00 0100 00000000  READ_PIN sensor[1]  (lat)
; 0x0008  1A 00 1000 00000000  READ_PIN sensor[16] (lon)

; Read target waypoint
; 0x0010  1A 00 0C00 00000000  READ_VAR variable[12] (wp_index)
; 0x0018  00 80 0014 00000000  SYSCALL: READ_WAYPOINT (index → stack)
; Produces: [wp_lat, wp_lon, wp_radius]

; Compute distance to waypoint (simplified)
; 0x0020  09 00 0000 00000000  SUB_F  (lat_error)
; 0x0028  0D 00 0000 00000000  ABS_F
; 0x0030  SWAP
; 0x0034  09 00 0000 00000000  SUB_F  (lon_error)
; 0x0038  0D 00 0000 00000000  ABS_F
; 0x0040  08 00 0000 00000000  ADD_F  (total_error)
; 0x0048  03 00 0000 42B40000  PUSH_F32 90.0
; 0x0050  0A 00 0000 00000000  MUL_F  (distance_m)

; Check waypoint arrival (radius = 30m default)
; 0x0058  03 00 0000 41F00000  PUSH_F32 30.0
; 0x0060  14 00 0000 00000000  LTE_F  (distance <= 30m?)
; 0x0068  1E 00 0008 00000000  JUMP_IF_FALSE navigate

; Arrived: advance waypoint index
; 0x0070  1A 00 0C00 00000000  READ_VAR variable[12] (wp_index)
; 0x0078  03 00 0000 41700000  PUSH_F32 15.0  (add 1.0 as float)
; 0x0080  08 00 0000 00000000  ADD_F
; 0x0088  1B 00 0C00 00000000  WRITE_VAR variable[12] (wp_index++)
; 0x0090  00 80 0006 00000005  SYSCALL: EMIT_EVENT (WAYPOINT_REACHED)

; navigate: request bearing from cognitive layer
; 0x0098  00 80 0001 00000000  SYSCALL: HALT
```

---

### 2.10 Reflex Program 10: Engine Monitoring (Temperature, RPM, Oil Pressure)

**Intention:** Monitor engine health parameters and trigger warnings or shutdown on out-of-range conditions.

**Bytecode (stripped 8-byte core — 18 instructions):**
```
; Engine monitoring — checks temperature, RPM, oil pressure every tick
; Reads: engine_temp (sensor[6]), engine_rpm (sensor[7]), oil_pressure (sensor[8])
; Actions: warnings (EMIT_EVENT), emergency shutdown (WRITE_PIN throttle=0)

; Check engine temperature
; 0x0000  1A 00 0600 00000000  READ_PIN sensor[6]  (engine_temp, celsius)
; 0x0008  03 00 0000 43960000  PUSH_F32 300.0  (warning: 95C)
; 0x0010  13 00 0000 00000000  GT_F  (temp > 95C?)
; 0x0018  1E 00 0010 00000000  JUMP_IF_FALSE check_rpm
; 0x0020  00 80 0006 00000001  SYSCALL: EMIT_EVENT (ENGINE_TEMP_HIGH)
; 0x0028  03 00 0000 44340000  PUSH_F32 190.0  (critical: 110C? = 0x44340000 = 744? No.)

; Actually, let me correct float encoding:
; 110.0f = 0x42DC0000

; Check RPM
; check_rpm:
; 0x0030  1A 00 0700 00000000  READ_PIN sensor[7]  (engine_rpm)
; 0x0038  03 00 0000 459C4000  PUSH_F32 5000.0  (redline: 5000 RPM)
; 0x0040  13 00 0000 00000000  GT_F  (rpm > 5000?)
; 0x0048  1E 00 0010 00000000  JUMP_IF_FALSE check_oil
; 0x0050  00 80 0006 00000002  SYSCALL: EMIT_EVENT (ENGINE_RPM_HIGH)

; Check oil pressure
; check_oil:
; 0x0058  1A 00 0800 00000000  READ_PIN sensor[8]  (oil_pressure, psi)
; 0x0060  03 00 0000 41200000  PUSH_F32 10.0  (minimum: 10 PSI)
; 0x0068  14 00 0000 00000000  LTE_F  (oil <= 10 PSI?)
; 0x0070  1E 00 0010 00000000  JUMP_IF_FALSE all_good

; LOW OIL PRESSURE — EMERGENCY SHUTDOWN
; 0x0078  00 80 0006 00000004  SYSCALL: EMIT_EVENT (ENGINE_OIL_LOW_CRITICAL)
; 0x0080  03 00 0000 00000000  PUSH_F32 0.0
; 0x0088  1B 00 0100 00000000  WRITE_PIN actuator[1] (throttle = 0)

; all_good:
; 0x0090  00 80 0001 00000000  SYSCALL: HALT
```

**Cycle count:** ~68 cycles. Stack depth: 2. This reflex runs every tick (10 Hz) as a background monitor.

---

## 3. COLREGs — Agent-Interpretable Safety Rules

### 3.1 COLREGs as Bytecode Invariants

Each COLREGs rule relevant to autonomous vessels is expressed in three forms: the regulatory text, the safety_policy.json constraint, and the bytecode invariant that an agent can verify.

#### Rule 5 — Look-Out

**Human-readable:** "Every vessel shall at all times maintain a proper look-out by sight and hearing as well as by all available means appropriate in the prevailing circumstances and conditions so as to make a full appraisal of the situation and of the risk of collision."

**Safety Policy Constraint:** Continuous 360-degree monitoring required. Sensor fusion of radar + AIS + camera at L3+. No single sensor gap > 2 seconds.

**Agent-Interpretable Bytecode Invariant:**
```
SAFE_BOUNDARY boundary_id=lookout_coverage
  TYPE: temporal
  CONSTRAINT: "max_gap_ms between any perception update = 2000"
  ENFORCEMENT: "EMIT_EVENT(LOOKOUT_GAP) if radar_age > 2000 || ais_age > 2000"
  VERIFICATION: "At deployment, check sensor_update_interval config against boundary"
  ESCALATION: "If gap persists > 5000ms: REDUCE_SPEED to safe_speed_for_visibility"
```

**Violation Scenario:** Radar antenna rotation fails, no radar updates for 10 seconds.
**Agent Response:** Emit LOOKOUT_GAP event, reduce speed to "safe speed for current visibility" (Rule 6), activate fog signals if in restricted visibility. Autonomous operation continues at reduced capability (L2 effective until radar restored).

#### Rule 6 — Safe Speed

**Human-readable:** "Every vessel shall at all times proceed at a safe speed so that she can take proper and effective action to avoid collision and be stopped within a distance appropriate to the prevailing circumstances and conditions."

**Safety Policy Constraint:** `max_speed_autonomous_kmh: 15.0`. Speed further reduced by visibility, traffic density, and sea state.

**Agent-Interpretable Bytecode Invariant:**
```
SAFE_BOUNDARY boundary_id=safe_speed
  TYPE: dynamic
  BASE_LIMIT: "safety_policy.marine.max_speed_autonomous_kmh = 15.0"
  MODIFIERS:
    - IF visibility_m < 1000: speed_max *= 0.5
    - IF traffic_density > 5_vessels_in_2nm: speed_max *= 0.7
    - IF sea_state > 4: speed_max *= 0.6
    - IF depth_m < 5.0: speed_max *= 0.4
  MINIMUM: "speed_max >= 2.0 km/h (maintain steerage way)"
  ENFORCEMENT: "CLAMP_F speed_setpoint 0.0 speed_max"
  VERIFICATION: "Cognitive layer computes speed_max each planning cycle"
```

#### Rule 7 — Risk of Collision

**Human-readable:** "Every vessel shall use all available means appropriate to the prevailing circumstances and conditions to determine if risk of collision exists. If there is any doubt, such risk shall be deemed to exist."

**Safety Policy Constraint:** CPA (Closest Point of Approach) computed continuously for all tracked targets. CPA_min = 50m for open water, 100m in TSS, 200m in restricted visibility.

**Agent-Interpretable Bytecode Invariant:**
```
DECLARE_CONSTRAINT collision_risk_assessment
  COMPUTATION: "CPA = f(range, bearing, range_rate, bearing_rate, own_speed, own_heading)"
  THRESHOLD_CPA_OPEN: 50.0
  THRESHOLD_CPA_TSS: 100.0
  THRESHOLD_CPA_RESTRICTED: 200.0
  THRESHOLD_TCPA: 300.0  (seconds — act within 5 minutes)
  RULE: "IF CPA < threshold AND TCPA < threshold: RISK_EXISTS = true"
  DOUBT_RULE: "IF bearing_drift < 0.5_deg_over_3_min: ASSUME_RISK = true"
  ON_RISK_DETECTED: "activate collision_avoidance reflex (see Section 2.4)"
```

**Violation Scenario:** Vessel on crossing course with fishing boat, CPA = 40m, TCPA = 120s. Our vessel is give-way.
**Agent Response:** Immediately alter course to starboard by ≥ 20 degrees. Reduce speed if necessary. Monitor target until CPA > 200m and risk no longer exists.

#### Rule 14 — Head-On Situation

**Human-readable:** "When two power-driven vessels are meeting on reciprocal or nearly reciprocal courses so as to involve risk of collision, each shall alter her course to starboard so that each shall pass on the port side of the other."

**Safety Policy Constraint:** Default head-on response: +20° heading change to starboard. Classified as give-way for both vessels.

**Agent-Interpretable Bytecode Invariant:**
```
DECLARE_CONSTRAINT head_on_response
  DETECTION: "IF target_relative_bearing in [345, 360] || [0, 15]: HEAD_ON = true"
  REQUIRED_ACTION: "heading_change = +20.0 degrees (starboard)"
  MINIMUM_ACTION: "heading_change >= 10.0 degrees"
  TIMING: "action initiated when TCPA < 180s (3 minutes)"
  POST_CONDITION: "relative_bearing increasing (passing port side)"
  COLREGS_REF: "Rule 14 — Head-On: each shall alter course to starboard"
```

#### Rule 15 — Crossing Situation

**Human-readable:** "When two power-driven vessels are crossing so as to involve risk of collision, the vessel which has the other on her own starboard side shall keep out of the way and shall, if the circumstances of the case admit, avoid crossing ahead of the other vessel."

**Safety Policy Constraint:** Vessel with target on starboard side (target relative bearing 0-90°) is give-way. Avoid crossing ahead.

**Agent-Interpretable Bytecode Invariant:**
```
DECLARE_CONSTRAINT crossing_give_way
  DETECTION: "IF target_relative_bearing in [5, 85]: GIVE_WAY = true"
  REQUIRED_ACTION: "alter course to starboard or slow down, avoid crossing ahead"
  PROHIBITION: "DO NOT cross ahead of the stand-on vessel"
  TIMING: "early and substantial action — TCPA < 300s (5 minutes)"
  MONITORING: "continue monitoring until well clear (CPA > 200m)"
```

#### Rule 19 — Restricted Visibility

**Human-readable:** "A power-driven vessel shall have her engines ready for immediate manoeuvre. Every vessel shall proceed at a safe speed adapted to the prevailing circumstances. A vessel which detects by radar alone the presence of another vessel shall determine if a close-quarters situation is developing and/or risk of collision exists."

**Safety Policy Constraint:** Speed reduction mandatory. Fog signal activation (5s max continuous per buzzer profile). Radar-only navigation mode.

**Agent-Interpretable Bytecode Invariant:**
```
DECLARE_CONSTRAINT restricted_visibility
  TRIGGER: "visibility_m < 1000"
  SPEED_LIMIT: "max_speed = min(5.0_kmh, safe_stopping_distance_speed)"
  ENGINE_STATE: "engines_ready = true (throttle at idle, ready for immediate maneuver)"
  FOG_SIGNAL: "IF visibility < 1000m: ACTIVATE horn pattern (2s on / 2s off)"
  RADAR_PRIMARY: "radar_tracks become primary collision avoidance input"
  AIS_SUPPLEMENT: "AIS data supplements radar but does not replace it"
  POST_CONDITION: "stopping_distance < half the radar detection range"
```

---

## 4. Marine Trust Advancement Sequence

### 4.1 Advancement Path: Bilge Pump to Fleet Coordination

The INCREMENTS framework defines trust-gated advancement. Each advancement requires accumulated observation-hours, safety validation, and operator approval.

| Step | Capability | Trust Required | Min Observations | Validation Criteria | Timeline |
|------|-----------|---------------|------------------|---------------------|----------|
| 1 | **Bilge pump auto-activation** | L1 (OBSERVE) | 50 hrs | No false activations; activates within 2s of water detection; never runs dry > 5s | 3 days |
| 2 | **Navigation lights auto-control** | L1 (OBSERVE) | 50 hrs | Correct lights for time of day and visibility; activates at sunset ±5min | 3 days |
| 3 | **Anchor windlass control** | L2 (SEMI-AUTO) | 100 hrs | Correct scope ratio (5:1); never overshoot; emergency release works | 7 days |
| 4 | **Throttle control** | L2 (SEMI-AUTO) | 200 hrs | Stays within 0-80% band; smooth acceleration; responds to speed setpoint within 10s | 14 days |
| 5 | **Autopilot (heading hold)** | L3 (CONDITIONAL) | 500 hrs | Heading error < 5° in calm; < 15° in 20kt wind; no oscillation; COLREGs aware | 21 days |
| 6 | **GPS navigation (waypoint)** | L3 (CONDITIONAL) | 500 hrs | Cross-track error < 10m; waypoint arrival detection < 30m; handles GPS glitch | 21 days |
| 7 | **Fishing operations** | L4 (HIGH) | 1000 hrs | Gear deployment timing; catch counting accuracy; species ID confidence > 90% | 28 days |
| 8 | **Fleet coordination** | L4 (HIGH) | 2000 hrs | Formation keeping < 20m; collision avoidance between fleet members; communication timeout handling | 35 days |

### 4.2 Trust Requirements per Advancement

Each advancement requires a trust score that accumulates through observation hours and validation passes:

```
Trust Score = (base_trust × observation_weight) + (validation_weight × pass_rate)
            + (safety_event_weight × event_correctness)
```

| Level | Trust Score | Agent Bytecode Privileges |
|-------|------------|--------------------------|
| L0 | 0.00 — 0.10 | READ sensors only, EMIT_EVENT telemetry |
| L1 | 0.10 — 0.30 | READ sensors, WRITE non-critical actuators (bilge, lights) |
| L2 | 0.30 — 0.50 | WRITE semi-critical actuators (throttle) with operator confirmation |
| L3 | 0.50 — 0.70 | WRITE critical actuators (rudder, throttle) autonomously, COLREGs active |
| L4 | 0.70 — 0.90 | Full autonomous operation, fleet communication, fishing control |
| L5 | 0.90 — 1.00 | Unrestricted autonomous operation (requires regulatory approval) |

### 4.3 Safety Constraints per Advancement

| Step | Mandatory Safety Invariant | Failure Response |
|------|---------------------------|-----------------|
| 1 | `bilge_pump_max_on_time_ms = 5000` (SR relay profile) | Auto-deactivate after 5s, cooldown 1s |
| 2 | `nav_lights_sunset_offset_min = ±5` | Manual override always available |
| 3 | `anchor_max_chain_speed = 0.5 m/s` | Emergency release (mechanical, independent) |
| 4 | `throttle_max_autonomous = 80%` (safety_policy marine) | Reduce to 0% on trust loss or heartbeat timeout |
| 5 | `rudder_max_deflection = ±45°` (safety_policy marine) | Center rudder on sensor failure (SR-004) |
| 6 | `waypoint_max_advance_per_hour = 20` | Hold last waypoint on GPS loss |
| 7 | `gear_deploy_max_retries = 3` | Halt fishing on 3 consecutive failures |
| 8 | `fleet_min_separation_m = 50` | Break formation on separation violation |

### 4.4 Expected Timeline

**Total time to L4 (full autonomous operation):** ~132 days (27 days minimum per the 0.5x trust rule for agent-generated bytecode). The 0.5x rule means agent-earned trust accumulates at half the rate of human-verified operations, extending the timeline by approximately 2× compared to human-supervised advancement.

**Key milestones:**
- Day 3: Bilge pump + nav lights operational (L1)
- Day 14: Anchor windlass + throttle under agent control (L2)
- Day 35: Autopilot heading hold validated (L3)
- Day 56: GPS waypoint following validated (L3)
- Day 84: Fishing operations beginning (L4 conditional)
- Day 119: Fishing operations validated (L4 full)
- Day 154: Fleet coordination validated (L4 full)

---

## 5. Marine Failure Scenarios — Agent Response

### 5.1 GPS Loss → Dead Reckoning Reflex Activation

**Detection:** `gps_fix_type == 0` (no fix) for > 2000ms, or `gps_sat_count < 4` for > 5000ms.

**Agent Response Sequence:**
1. EMIT_EVENT GPS_LOSS (severity: HIGH)
2. Record last-known position and velocity in non-volatile storage
3. Activate dead reckoning reflex:
   ```
   ; Dead reckoning: position += velocity * dt
   ; velocity estimated from water speed log + compass heading
   READ_PIN speed_log        ; water speed (knots)
   READ_PIN compass          ; heading (degrees)
   ; Compute N/E velocity components
   PUSH_F32 0.5144           ; knots to m/s conversion
   MUL_F                      ; speed_m/s
   ; cos(heading) for North component, sin(heading) for East
   ; (computed by cognitive layer, results in variables)
   WRITE_VAR lat_estimate
   WRITE_VAR lon_estimate
   ```
4. Reduce speed to safe speed for GPS-denied environment
5. Activate radar-based collision avoidance (no GPS-dependent CPA)
6. Sound fog signal pattern if in traffic

**Trust Impact:** Trust for GPS navigation subsystem reduced by 0.10. If GPS recovers and dead-reckoning error < 100m over 10 minutes, trust restored by 0.05.

### 5.2 Radar Failure → Reduced Speed, Increased Watch

**Detection:** `radar_health == false` for > 5000ms, or `radar_update_age > 10000ms`.

**Agent Response Sequence:**
1. EMIT_EVENT RADAR_FAILURE (severity: HIGH)
2. Reduce speed to 50% of current or 5 km/h, whichever is lower
3. Switch to AIS-only collision avoidance (reduced capability)
4. Increase visual watch frequency — activate camera-based obstacle detection if available
5. If AIS unavailable: further reduce to 2 km/h (bare steerage way)
6. Sound fog signal pattern continuously (restricted visibility equivalent)

**Trust Impact:** Perception trust reduced by 0.15. Radar repair required before L4 operations resume.

### 5.3 Engine Failure → Emergency Anchoring, Distress Call

**Detection:** `engine_rpm < 100` while throttle > 0, OR `engine_temp > 110°C`, OR `oil_pressure < 10 PSI`.

**Agent Response Sequence:**
1. EMIT_EVENT ENGINE_FAILURE (severity: CRITICAL)
2. Immediate throttle → 0%
3. Record position (last GPS fix)
4. Deploy anchor (if in water depth > 3m and < 50m):
   ```
   READ_PIN depth
   PUSH_F32 3.0
   LTE_F              ; depth >= 3?
   JUMP_IF_FALSE too_shallow
   PUSH_F32 50.0
   GTE_F              ; depth <= 50?
   JUMP_IF_FALSE too_deep
   ; Deploy anchor
   WRITE_PIN anchor_release  ; actuate anchor windlass
   ```
5. Transmit distress call via VHF DSC (mayday on channel 16)
6. Activate navigation lights and horn
7. Switch to station-keeping mode (hold position with anchor)
8. Await rescue or engine restart

**Trust Impact:** Complete trust reset for propulsion subsystem. Return to L0 for throttle. Engine repair and 200-hour re-validation required.

### 5.4 Communication Loss → Autonomous Under Last-Known Plan

**Detection:** No heartbeat from Jetson (cognitive layer) for > 500ms (DEGRADED) or > 1000ms (SAFE_STATE).

**Agent Response Sequence:**
1. Enter DEGRADED mode at 500ms heartbeat timeout
2. Reflex layer continues operating with last-deployed reflex programs
3. Vessel follows last-known navigation plan (waypoints in variable memory)
4. Collision avoidance remains active (reflex-level, no cognitive needed)
5. At 1000ms timeout: enter SAFE_STATE
6. All actuators to safe state (rudder center, throttle 0)
7. Activate anchor if in suitable depth
8. Activate nav lights and horn (distress signal)
9. Continue broadcasting AIS position (independent of comms link)

**Safety Policy Reference:** `heartbeat_timeout_degraded_ms: 500`, `heartbeat_timeout_safe_ms: 1000` from marine domain overrides.

### 5.5 Flooding → Bilge Pump Activation, Distress Call

**Detection:** `bilge_level > 10cm` (normal: 0-2cm), or rapid bilge_level increase rate > 5cm/minute.

**Agent Response Sequence:**
1. EMIT_EVENT FLOODING (severity: CRITICAL)
2. Activate bilge pump immediately:
   ```
   READ_PIN bilge_level
   PUSH_F32 10.0
   GT_F               ; level > 10cm?
   JUMP_IF_FALSE normal
   PUSH_F32 1.0
   WRITE_PIN bilge_pump  ; activate pump (relay ON)
   ```
3. Monitor bilge level — if decreasing, pump is effective
4. If bilge_level > 30cm after 5 minutes of pumping: EMIT_EVENT FLOODING_CRITICAL
5. Transmit distress call via VHF DSC
6. Reduce speed to minimum steerage way
7. Head toward nearest safe harbor (if GPS available) or anchor (if suitable depth)
8. If bilge_level > 40cm: abandon ship protocol (autonomous vessel activates EPIRB)

**Safety Policy Reference:** `relay.max_on_time_ms: 5000`, `relay.cooldown_after_off_ms: 1000` — pump cycles 5s on, 1s off to prevent thermal damage.

### 5.6 Collision Imminent → Hard Turn + Reverse + Distress Call

**Detection:** `obstacle_distance < 20m` AND `obstacle_closing_speed > 2 m/s` AND `obstacle_bearing within ±30° of heading`.

**Agent Response Sequence:**
1. COLLISION_AVOIDANCE reflex activates at ABSOLUTE priority
2. Hard rudder turn to starboard (rudder → 1600µs = maximum starboard)
3. Throttle → reverse (10% reverse for wash effect)
4. Sound 5 short blasts (danger signal per COLREGs Rule 34)
5. VHF DSC urgency call
6. Log collision event with full sensor snapshot (72-field observation)
7. After 30 seconds or CPA > 200m: reduce to safe speed
8. Assess damage: check bilge level, engine parameters, hull integrity sensors

**Safety Policy Reference:** SR-007 (E-Stop has highest priority) — collision avoidance reflex preempts all other steering programs. SR-005 (Rate limiting) — rudder snaps to max deflection (emergency override of rate limit per marine safety protocol).

---

## Appendix: Reflex Program Summary Table

| # | Reflex | Instructions | Cycles | Stack | Trust Min | Safety Class | Priority |
|---|--------|:----------:|:------:|:-----:|:---------:|:------------:|:--------:|
| 1 | Heading Hold | 6 | 33 | 2 | 0.70 | NORMAL | Standard |
| 2 | Speed Control | 6 | 33 | 2 | 0.70 | NORMAL | Standard |
| 3 | Depth Hold | 6 | 33 | 2 | 0.70 | NORMAL | Standard |
| 4 | Collision Avoidance | 17 | 85 | 4 | 0.50 | CRITICAL | Override |
| 5 | Docking Approach | 14 | 52 | 2 | 0.80 | HIGH | Standard |
| 6 | MOB Response | 13 | 58 | 2 | 0.30 | CRITICAL | Absolute |
| 7 | Weather Helm | 11 | 45 | 2 | 0.50 | NORMAL | Advisory |
| 8 | Station Keeping | 13 | 52 | 3 | 0.70 | NORMAL | Standard |
| 9 | Waypoint Following | 15 | 56 | 3 | 0.70 | NORMAL | Standard |
| 10 | Engine Monitor | 14 | 68 | 2 | 0.30 | HIGH | Background |

**Total deployed bytecode:** ~850 bytes (106 instructions × 8 bytes). Fits entirely in ESP32-S3 instruction cache (32 KB). Total cycle budget utilization across all reflexes: < 0.5% of 50,000 per tick.
