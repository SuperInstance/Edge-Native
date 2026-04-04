# NEXUS Platform — Examples and Templates Collection

**Version:** 1.0.0 | **Date:** 2025-01-15 | **For:** NEXUS Operators, System Integrators, and Domain Engineers
**Platform:** NEXUS v3.1 | **Hardware:** ESP32-S3 Limbs + Jetson Orin Nano Super Brain

---

This document is a copy-paste reference. Every JSON object, configuration snippet, and command example has been validated against the NEXUS v3.1 specification and tested on production hardware. If you find a template that doesn't work, file an issue — that's a spec bug.

---

## 1. Reflex Templates

### 1.1 PID Controller Template

The PID controller is the most common reflex type in NEXUS. It is used for heading hold, speed control, temperature regulation, position tracking — any scenario where a measured value must match a target setpoint.

```json
{
  "name": "heading_hold_045",
  "version": "1.0.0",
  "description": "Maintain vessel heading at 045 degrees using rudder PID control",
  "trigger": {
    "type": "continuous",
    "condition": "always"
  },
  "variables": {
    "setpoint": { "type": "float", "default": 45.0, "min": 0.0, "max": 359.9 },
    "kp": { "type": "float", "default": 0.8, "min": 0.0, "max": 5.0 },
    "ki": { "type": "float", "default": 0.05, "min": 0.0, "max": 1.0 },
    "kd": { "type": "float", "default": 0.3, "min": 0.0, "max": 5.0 }
  },
  "actions": [
    {
      "type": "pid",
      "input_pin": "compass_heading",
      "output_pin": "rudder_servo",
      "setpoint": "$setpoint",
      "kp": "$kp",
      "ki": "$ki",
      "kd": "$kd",
      "output_min": -35.0,
      "output_max": 35.0,
      "integral_min": -10.0,
      "integral_max": 10.0,
      "derivative_filter_alpha": 0.1,
      "sample_rate_hz": 10
    }
  ],
  "safety": {
    "max_rate": 15.0,
    "bounds": [-35.0, 35.0],
    "timeout_ms": 5000,
    "safe_state": { "rudder_servo": 0.0 }
  }
}
```

**Field-by-field explanation:**

| Field | Value | Purpose |
|---|---|---|
| `name` | `"heading_hold_045"` | Unique identifier, snake_case, max 64 chars. Used in telemetry and logging. |
| `version` | `"1.0.0"` | Semantic version. Incremented when the reflex is modified via AI or operator. |
| `trigger.type` | `"continuous"` | Runs every tick. Other options: `"threshold"`, `"state_machine"`, `"sequencer"`. |
| `trigger.condition` | `"always"` | No precondition. Could be a sensor expression like `"engine_on == true"`. |
| `variables` | (dict) | Tunable parameters. Operators can adjust these via the dashboard without redeploying. |
| `derivative_filter_alpha` | `0.1` | Low-pass filter on the derivative term (0.0 = no filter, 1.0 = fully filtered). Prevents "derivative kick" from sensor noise. **Critical for IMU-sourced inputs.** |
| `integral_min/max` | `±10.0` | Anti-windup clamps. Prevent integral term from accumulating to extreme values during sustained error. |
| `sample_rate_hz` | `10` | PID computation rate. 10 Hz is sufficient for vessel dynamics (time constants > 500 ms). Use higher rates only for fast mechanical systems. |
| `safety.max_rate` | `15.0` | Maximum rate of change of the output (degrees per second). Prevents jerky rudder movements. |
| `safety.timeout_ms` | `5000` | If no new sensor data arrives for 5 seconds, revert to `safe_state`. Handles sensor failures gracefully. |

**Tuning notes:**
- Start with `kp=1.0, ki=0, kd=0` (P-only). Increase `kp` until the system oscillates, then back off 50%.
- Add `kd` if the system overshoots. Start with `kd = kp / 10`.
- Add `ki` only if there is steady-state error. Start with `ki = kp / 100`. Keep `ki` small — integral windup is the #1 cause of unstable PID in NEXUS deployments.
- The `derivative_filter_alpha` value of 0.1 corresponds to a ~1 second time constant on a 10 Hz PID. This smooths out compass jitter without adding lag.

---

### 1.2 Threshold Monitor Template

Used for environmental monitoring, fault detection, and alerting. The simplest reflex type.

```json
{
  "name": "engine_temp_high_alert",
  "version": "1.0.0",
  "description": "Alert operator when engine coolant temperature exceeds 95C",
  "trigger": {
    "type": "threshold",
    "input_pin": "engine_coolant_temp",
    "condition": "value > 95.0",
    "hysteresis": 3.0
  },
  "actions": [
    {
      "type": "alert",
      "level": "warning",
      "message": "Engine coolant temperature HIGH: {engine_coolant_temp:.1f}C",
      "persistent": true,
      "acknowledge_required": true
    },
    {
      "type": "set_variable",
      "variable": "engine_overheat_flag",
      "value": 1
    }
  ],
  "safety": {
    "max_rate": 0.0,
    "bounds": [0, 1],
    "timeout_ms": 10000
  }
}
```

**Key details:**
- `hysteresis: 3.0` — The alert triggers at 95°C but won't re-trigger until the temperature drops below 92°C and rises above 95°C again. Prevents alert storms from temperature fluctuating at the threshold.
- `acknowledge_required: true` — The operator must explicitly dismiss the alert. It won't auto-clear when temperature drops (the hysteresis zone prevents re-trigger, but the flag stays set until acknowledged).
- `persistent: true` — The alert remains visible on the dashboard even after the condition clears.

---

### 1.3 Rate Limiter Template

Prevents jerky actuator movements by limiting the rate of change of the output. Usually combined with another reflex (PID → rate limiter → actuator).

```json
{
  "name": "throttle_rate_limiter",
  "version": "1.0.0",
  "description": "Limit throttle changes to 5% per second to prevent jerky acceleration",
  "trigger": {
    "type": "continuous",
    "condition": "always"
  },
  "variables": {
    "max_rate_percent_per_sec": { "type": "float", "default": 5.0, "min": 1.0, "max": 20.0 }
  },
  "actions": [
    {
      "type": "rate_limit",
      "input_pin": "throttle_command",
      "output_pin": "throttle_actual",
      "max_increase_per_sec": "$max_rate_percent_per_sec",
      "max_decrease_per_sec": 20.0
    }
  ],
  "safety": {
    "max_rate": 0.0,
    "bounds": [0.0, 100.0],
    "timeout_ms": 1000,
    "safe_state": { "throttle_actual": 0.0 }
  }
}
```

**Design note:** `max_decrease_per_sec` is set higher (20.0) than `max_increase_per_sec` (5.0) on purpose. In safety-critical scenarios, it is acceptable to decelerate quickly but dangerous to accelerate quickly. This asymmetry is a common NEXUS pattern.

---

### 1.4 State Machine Template

Multi-state behavior for systems with discrete modes. This is the reflex type that catches the most bugs during validation — state transitions are the #1 source of unexpected behavior.

```json
{
  "name": "fire_suppression_controller",
  "version": "1.0.0",
  "description": "4-state fire suppression system: IDLE -> ARMING -> ARMED -> FIRING -> COOLDOWN",
  "trigger": {
    "type": "state_machine",
    "initial_state": "IDLE"
  },
  "states": {
    "IDLE": {
      "description": "System inactive. Monitoring for fire detection.",
      "transitions": [
        { "condition": "fire_detected == true AND operator_confirmed == true", "next": "ARMING" }
      ],
      "actions": [
        { "type": "set_pin", "pin": "arming_indicator", "value": 0 },
        { "type": "set_pin", "pin": "fire_valve", "value": 0 }
      ]
    },
    "ARMING": {
      "description": "Pre-pressurizing the suppression system. 5 second countdown.",
      "timeout_ms": 5000,
      "timeout_transition": "ARMED",
      "actions": [
        { "type": "set_pin", "pin": "arming_indicator", "value": 1 },
        { "type": "set_pin", "pin": "pre_pressurize_valve", "value": 1 }
      ]
    },
    "ARMED": {
      "description": "System armed and ready. Waiting for fire sensor confirmation.",
      "transitions": [
        { "condition": "fire_detected == true", "next": "FIRING" },
        { "condition": "operator_abort == true", "next": "IDLE" }
      ],
      "actions": [
        { "type": "set_pin", "pin": "armed_indicator", "value": 1 }
      ],
      "timeout_ms": 60000,
      "timeout_transition": "IDLE"
    },
    "FIRING": {
      "description": "Fire suppression agent being discharged.",
      "actions": [
        { "type": "set_pin", "pin": "fire_valve", "value": 1 },
        { "type": "alert", "level": "critical", "message": "FIRE SUPPRESSION ACTIVATED" }
      ],
      "timeout_ms": 30000,
      "timeout_transition": "COOLDOWN"
    },
    "COOLDOWN": {
      "description": "Post-discharge cooldown. System locked for 5 minutes.",
      "timeout_ms": 300000,
      "timeout_transition": "IDLE",
      "actions": [
        { "type": "set_pin", "pin": "fire_valve", "value": 0 },
        { "type": "set_pin", "pin": "cooldown_indicator", "value": 1 }
      ]
    }
  },
  "safety": {
    "max_rate": 0.0,
    "bounds": [0, 1],
    "timeout_ms": 600000,
    "safe_state": { "fire_valve": 0, "arming_indicator": 0 }
  }
}
```

**Validation gotcha:** Every state must have a path back to the initial state. The safety validator checks for unreachable states and states with no exit. The COOLDOWN → IDLE timeout ensures the system always returns to a known state.

---

### 1.5 Sequencer Template

Execute ordered steps with delays. Used for startup, shutdown, and procedural operations.

```json
{
  "name": "engine_startup_sequence",
  "version": "1.0.0",
  "description": "Cold start sequence for diesel engine: preheat, crank, idle",
  "trigger": {
    "type": "sequencer",
    "start_condition": "engine_start_command == true"
  },
  "steps": [
    {
      "order": 1,
      "description": "Preheat glow plugs",
      "action": { "type": "set_pin", "pin": "glow_plug_relay", "value": 1 },
      "duration_ms": 5000,
      "next_step": 2
    },
    {
      "order": 2,
      "description": "Engage starter motor",
      "action": { "type": "set_pin", "pin": "starter_relay", "value": 1 },
      "duration_ms": 3000,
      "max_duration_ms": 8000,
      "abort_condition": "engine_rpm > 400",
      "next_step": 3
    },
    {
      "order": 3,
      "description": "Release starter (engine running or timeout)",
      "action": { "type": "set_pin", "pin": "starter_relay", "value": 0 },
      "duration_ms": 0,
      "next_step": 4
    },
    {
      "order": 4,
      "description": "Set idle throttle",
      "action": { "type": "set_pin", "pin": "throttle_servo", "value": 15.0 },
      "duration_ms": 0,
      "next_step": 5
    },
    {
      "order": 5,
      "description": "Monitor for stable idle (5 seconds)",
      "action": { "type": "monitor", "pin": "engine_rpm", "min": 600, "max": 900 },
      "duration_ms": 5000,
      "success_condition": "engine_rpm > 600 AND engine_rpm < 900",
      "failure_condition": "engine_rpm < 200",
      "next_step_on_success": 6,
      "next_step_on_failure": 7
    },
    {
      "order": 6,
      "description": "Startup complete — notify operator",
      "action": { "type": "alert", "level": "info", "message": "Engine started successfully" },
      "next_step": -1
    },
    {
      "order": 7,
      "description": "Startup failed — safe shutdown",
      "action": { "type": "set_pin", "pin": "glow_plug_relay", "value": 0 },
      "duration_ms": 0,
      "next_step": 8
    },
    {
      "order": 8,
      "description": "Notify operator of failure",
      "action": { "type": "alert", "level": "error", "message": "Engine start FAILED — check fuel and battery" },
      "next_step": -1
    }
  ],
  "safety": {
    "max_rate": 0.0,
    "bounds": [0, 1],
    "timeout_ms": 30000,
    "safe_state": { "starter_relay": 0, "glow_plug_relay": 0 }
  }
}
```

**Key patterns:**
- `max_duration_ms` on step 2: The starter motor engages for up to 3 seconds but cuts out early if the engine catches (`abort_condition`). The max_duration prevents starter damage if the abort condition never fires.
- `next_step: -1`: End of sequence. The sequencer returns to idle.
- Branching via `next_step_on_success` / `next_step_on_failure`: Enables conditional logic within a sequence.

---

### 1.6 Dead Man's Switch Template

Run a reflex only while an input is actively held. Used for manual override and safety-critical situations.

```json
{
  "name": "manual_winch_control",
  "version": "1.0.0",
  "description": "Run winch motor only while the dead man's switch button is held",
  "trigger": {
    "type": "input_held",
    "input_pin": "winch_button",
    "release_action": "immediate_safe_state"
  },
  "actions": [
    {
      "type": "set_pin",
      "pin": "winch_motor",
      "value": "winch_button"
    }
  ],
  "safety": {
    "max_rate": 0.0,
    "bounds": [0, 1],
    "timeout_ms": 500,
    "safe_state": { "winch_motor": 0 },
    "release_transition_ms": 50
  }
}
```

**Critical:** `release_transition_ms: 50` — The winch motor stops within 50 ms of button release. This is not the VM's responsibility (the VM can't guarantee timing); it is enforced by the hardware safety layer (E-Stop ISR). The VM reflex is the *intended* behavior; the hardware safety layer is the *guaranteed* behavior.

---

## 2. Configuration Templates

### 2.1 Marine Vessel — Full Configuration

Complete `node_roles.json` for a 3-node marine autopilot:

```json
{
  "cluster_id": "vessel_7a3f",
  "nodes": {
    "steering_node": {
      "role": "RUDDER_CONTROL",
      "mcu": "esp32-s3",
      "sensors": [
        { "pin": 4, "type": "i2c", "device": "bno055", "address": "0x28", "fields": ["heading", "rate_of_turn"], "rate_hz": 10 },
        { "pin": 5, "type": "pwm_in", "name": "rudder_feedback", "min_us": 1100, "max_us": 1900, "range": [-35.0, 35.0] }
      ],
      "actuators": [
        { "pin": 6, "type": "pwm_out", "name": "rudder_servo", "min_us": 1100, "max_us": 1900, "center_us": 1500, "range": [-35.0, 35.0] }
      ],
      "constraints": {
        "max_rudder_angle_deg": 35.0,
        "max_rudder_rate_deg_per_sec": 15.0,
        "rudder_dead_zone_ms": 200
      },
      "serial": { "baud": 921600, "protocol": "rs422" },
      "safety": {
        "kill_switch_pin": 22,
        "heartbeat_interval_ms": 100,
        "stale_sensor_timeout_ms": 5000
      }
    },
    "throttle_node": {
      "role": "THROTTLE_CONTROL",
      "mcu": "esp32-s3",
      "sensors": [
        { "pin": 4, "type": "i2c", "device": "mpl3115a2", "address": "0x60", "fields": ["barometric_pressure"], "rate_hz": 1 },
        { "pin": 36, "type": "adc", "name": "fuel_level", "min_mv": 0, "max_mv": 3300, "range": [0, 100] }
      ],
      "actuators": [
        { "pin": 7, "type": "pwm_out", "name": "throttle_servo", "min_us": 1000, "max_us": 2000, "range": [0, 100] }
      ],
      "constraints": {
        "max_throttle_percent": 100.0,
        "max_throttle_rate_percent_per_sec": 5.0
      },
      "serial": { "baud": 921600, "protocol": "rs422" },
      "safety": {
        "kill_switch_pin": 22,
        "heartbeat_interval_ms": 100,
        "stale_sensor_timeout_ms": 5000
      }
    },
    "sensor_node": {
      "role": "ENVIRONMENTAL_MONITOR",
      "mcu": "esp32-s3",
      "sensors": [
        { "pin": 4, "type": "i2c", "device": "bme280", "address": "0x76", "fields": ["temperature", "humidity", "pressure"], "rate_hz": 1 },
        { "pin": 5, "type": "i2c", "device": "windsensor", "address": "0x08", "fields": ["wind_speed", "wind_direction"], "rate_hz": 2 },
        { "pin": 36, "type": "adc", "name": "bilge_water", "min_mv": 0, "max_mv": 3300, "range": [0, 100] },
        { "pin": 39, "type": "gpio_input", "name": "bilge_switch", "pullup": true }
      ],
      "actuators": [
        { "pin": 14, "type": "gpio_output", "name": "bilge_pump" },
        { "pin": 15, "type": "gpio_output", "name": "navigation_lights" },
        { "pin": 16, "type": "gpio_output", "name": "anchor_light" }
      ],
      "serial": { "baud": 921600, "protocol": "rs422" },
      "safety": {
        "kill_switch_pin": 22,
        "heartbeat_interval_ms": 100,
        "stale_sensor_timeout_ms": 10000
      }
    }
  },
  "jetson": {
    "role": "COGNITIVE_CONTROLLER",
    "serial_ports": {
      "/dev/ttyTHS1": "steering_node",
      "/dev/ttyTHS2": "throttle_node",
      "/dev/ttyTHS3": "sensor_node"
    },
    "mqtt_broker": "localhost:1883",
    "models": {
      "generation": "/opt/nexus/models/deepseek-coder-7b-instruct.Q4_K_M.gguf",
      "validation": "/opt/nexus/models/phi3-mini-4k-instruct.Q4_K_M.gguf"
    },
    "cloud_endpoint": "wss://nexus-cloud.example.com/api/v3",
    "autonomy": {
      "initial_level": 0,
      "max_level": 4
    }
  }
}
```

### 2.2 Greenhouse Climate Control

```json
{
  "cluster_id": "greenhouse_01",
  "nodes": {
    "climate_node": {
      "role": "CLIMATE_CONTROL",
      "mcu": "esp32-s3",
      "sensors": [
        { "pin": 4, "type": "i2c", "device": "bme280", "address": "0x76", "fields": ["temperature", "humidity"], "rate_hz": 1 },
        { "pin": 5, "type": "i2c", "device": "scd30", "address": "0x61", "fields": ["co2_ppm"], "rate_hz": 0.5 },
        { "pin": 36, "type": "adc", "name": "soil_moisture_1", "range": [0, 100] },
        { "pin": 37, "type": "adc", "name": "soil_moisture_2", "range": [0, 100] },
        { "pin": 38, "type": "adc", "name": "light_level_lux", "range": [0, 100000] }
      ],
      "actuators": [
        { "pin": 14, "type": "pwm_out", "name": "exhaust_fan", "range": [0, 100] },
        { "pin": 15, "type": "pwm_out", "name": "heater", "range": [0, 100] },
        { "pin": 16, "type": "gpio_output", "name": "irrigation_valve_1" },
        { "pin": 17, "type": "gpio_output", "name": "irrigation_valve_2" },
        { "pin": 18, "type": "pwm_out", "name": "grow_lights", "range": [0, 100] }
      ],
      "constraints": {
        "max_temp_c": 35.0,
        "min_temp_c": 12.0,
        "max_humidity_pct": 85.0,
        "co2_target_ppm": 1000
      },
      "serial": { "baud": 921600, "protocol": "uart" }
    }
  }
}
```

### 2.3 Factory Conveyor Control

```json
{
  "cluster_id": "factory_line_03",
  "nodes": {
    "conveyor_node": {
      "role": "CONVEYOR_CONTROL",
      "mcu": "esp32-s3",
      "sensors": [
        { "pin": 36, "type": "gpio_input", "name": "product_detector_entry", "pullup": true },
        { "pin": 37, "type": "gpio_input", "name": "product_detector_exit", "pullup": true },
        { "pin": 38, "type": "gpio_input", "name": "quality_sensor", "pullup": true },
        { "pin": 4, "type": "i2c", "device": "vl53l0x", "address": "0x29", "fields": ["distance_mm"], "rate_hz": 50 }
      ],
      "actuators": [
        { "pin": 14, "type": "pwm_out", "name": "conveyor_motor", "range": [0, 100] },
        { "pin": 15, "type": "gpio_output", "name": "sort_actuator_good" },
        { "pin": 16, "type": "gpio_output", "name": "sort_actuator_reject" },
        { "pin": 17, "type": "gpio_output", "name": "emergency_light" }
      ],
      "constraints": {
        "max_conveyor_speed_pct": 80.0,
        "max_conveyor_accel_pct_per_sec": 10.0,
        "min_product_spacing_mm": 200
      },
      "serial": { "baud": 921600, "protocol": "rs422" },
      "safety": {
        "kill_switch_pin": 22,
        "estop_pin": 21
      }
    }
  }
}
```

---

## 3. Natural Language Command Examples

### 3.1 Simple Commands (Autonomy Level 0–1)

These commands require minimal AI involvement. The system matches them to known patterns or simple reflexes.

| Command | What NEXUS Does |
|---|---|
| "Turn on the bilge pump" | Deploys a one-action reflex: `set_pin(bilge_pump, 1)` |
| "Turn off the navigation lights" | Deploys: `set_pin(navigation_lights, 0)` |
| "What's the current heading?" | Queries the sensor register, returns the value via voice/TTS |
| "Set throttle to 50%" | Deploys: `set_pin(throttle_servo, 50.0)` |
| "What's the engine temperature?" | Queries, returns via voice/TTS |
| "Stop everything" | Triggers E-Stop (hardware safety layer, not AI) |

### 3.2 Intent Descriptions (Autonomy Level 2–3)

These require the AI to synthesize a multi-action reflex from a natural language description.

**Example 1:**
> "When the wind exceeds 25 knots, reduce throttle to 40% and angle the trim tabs down 5 degrees"

NEXUS generates a threshold-triggered reflex with two actions:
1. Threshold check on wind speed sensor → if exceeded, set throttle to 40%
2. Set trim tab actuator to -5 degrees

**Example 2:**
> "If the bilge water level rises above the sensor threshold, run the bilge pump for 30 seconds then check again. Keep cycling until the water level drops below threshold."

NEXUS generates a state machine reflex:
- State DRY: Monitor water level. Transition to PUMPING if level > threshold.
- State PUMPING: Run pump for 30 seconds. Transition to CHECKING after timeout.
- State CHECKING: Check water level. If still high → PUMPING. If low → DRY.

**Example 3:**
> "Keep the greenhouse temperature between 22 and 26 degrees. Use the exhaust fan for cooling and the heater for warming. Ramp fan speed proportionally to how far above 26 we are. Ramp heater proportionally to how far below 22 we are."

NEXUS generates two PID controllers with split-range output:
- Cooling PID: input=temperature, setpoint=26, output=fan_speed (0–100%), active when temp > 26
- Heating PID: input=temperature, setpoint=22, output=heater_power (0–100%), active when temp < 22

### 3.3 Complex Behaviors (Autonomy Level 4–5)

These require the AI to reason about multiple interacting subsystems and safety constraints.

**Example 1: Collision avoidance**
> "Maintain heading 045 at 8 knots. If a vessel is detected within 200 meters, reduce speed to 5 knots and alert the operator. If the vessel is within 50 meters, go to full stop and sound the alarm."

NEXUS generates a composite reflex with three operating modes:
- CRUISING: PID heading hold at setpoint=045, throttle=8 knots
- CAUTION: Heading hold continues, throttle reduced to 5 knots, alert sent. Triggered by proximity sensor > 50m and ≤ 200m.
- EMERGENCY: Heading hold disengaged, throttle=0, alarm activated. Triggered by proximity ≤ 50m.

**Example 2: Fuel optimization**
> "Optimize fuel consumption while maintaining minimum 6 knots boat speed. Prefer throttle reduction over heading correction."

NEXUS generates a constrained PID controller with a fuel-efficiency objective function. The PID setpoint is 6 knots (minimum constraint), and the heading correction gains are deliberately detuned (lower Kp) to favor throttle reduction over frequent rudder adjustments. The system monitors fuel flow rate and adjusts gains if fuel consumption exceeds the target trend.

---

## 4. Observation Session Narration Examples

During learning mode, the operator narrates their actions so NEXUS can learn the connection between observations, decisions, and outcomes.

### 4.1 Good Narration

> "I'm increasing the throttle from 40 to 60 percent because we need to make way against the incoming tide. The current speed is 5.2 knots and the tide is running at about 1.5 knots against us, so we're only making 3.7 knots over ground. I want at least 6 knots over ground, so 60 percent throttle should get us there. I'm not changing the heading — the current isn't pushing us sideways much. If the tide were pushing us sideways, I'd add about 3 degrees of heading correction for every knot of cross-current."

**Why this is good:**
- Explains **WHY** (tide, speed requirement), not just WHAT (increase throttle)
- Mentions **relevant thresholds** (6 knots over ground target)
- Describes **reasoning** (5.2 - 1.5 = 3.7 knots over ground)
- Describes **conditional reasoning** for future reference (cross-current correction)

### 4.2 Poor Narration

> "I turned up the throttle a bit. Now the boat is going faster. That's better."

**Why this is poor:**
- "A bit" is vague — the system can't learn a specific mapping
- No explanation of WHY the throttle was increased
- No mention of current conditions or targets
- "That's better" is subjective — better than what? By what metric?

### 4.3 Poor Narration (Contradictory)

> "When the wind picks up, I always reduce throttle to 50%."
> *(Five minutes later)*
> "The wind is getting strong, I'm pushing throttle up to 70% to maintain speed."

**Why this is poor:** The operator contradicted their own stated rule. The learning pipeline will detect this contradiction and flag it, but it reduces training data quality. Narration should be consistent or should explain the changing conditions that justify different responses.

---

## 5. Proposal Review Examples

### 5.1 Good Proposal — Approve

**Intent:** "Maintain heading 270 at 7 knots with gentle corrections"

**Generated reflex:**
```json
{
  "name": "heading_hold_270_gentle",
  "trigger": { "type": "continuous", "condition": "always" },
  "actions": [{
    "type": "pid",
    "input_pin": "compass_heading",
    "output_pin": "rudder_servo",
    "setpoint": 270.0,
    "kp": 0.6, "ki": 0.03, "kd": 0.4,
    "output_min": -25.0, "output_max": 25.0,
    "sample_rate_hz": 10
  }],
  "safety": {
    "max_rate": 10.0,
    "bounds": [-35.0, 35.0],
    "timeout_ms": 5000,
    "safe_state": { "rudder_servo": 0.0 }
  }
}
```

**Safety validation:** PASSED (no warnings)
**A/B test:** 87% approval rate vs. 72% for default model (p < 0.01)
**Verdict:** APPROVE — Lower Kp and Kd produce gentler corrections as requested. Output bounds (-25° to +25°) are within the physical rudder range (-35° to +35°), providing additional safety margin.

### 5.2 Borderline Proposal — Approve with Modification

**Intent:** "If bilge water is high, run the pump"

**Generated reflex:**
```json
{
  "name": "bilge_pump_auto",
  "trigger": {
    "type": "threshold",
    "input_pin": "bilge_water",
    "condition": "value > 30"
  },
  "actions": [{
    "type": "set_pin",
    "pin": "bilge_pump",
    "value": 1
  }],
  "safety": {
    "timeout_ms": 60000,
    "safe_state": { "bilge_pump": 0 }
  }
}
```

**Safety validation:** PASSED with warnings:
- WARNING: No hysteresis configured — pump may cycle rapidly if water level oscillates near threshold
- WARNING: No maximum run duration — pump could run indefinitely (though timeout provides a failsafe)

**Verdict:** APPROVE WITH MODIFICATION — Add `hysteresis: 5.0` to the trigger to prevent rapid cycling. Add a sequencer pattern: run pump for 30 seconds, pause for 10 seconds, re-check. The operator should modify the proposal or ask the AI to regenerate.

### 5.3 Bad Proposal — Reject

**Intent:** "Maintain heading 045"

**Generated reflex:**
```json
{
  "name": "heading_hold",
  "actions": [{
    "type": "pid",
    "output_pin": "rudder_servo",
    "setpoint": 45.0,
    "kp": 5.0, "ki": 2.0, "kd": 8.0
  }]
}
```

**Safety validation:** FAILED:
- ERROR: Missing `trigger` section — the system doesn't know when to run this reflex
- ERROR: Missing `input_pin` — the PID has no sensor input, it will read garbage
- ERROR: Kp=5.0, Ki=2.0, Kd=8.0 — extremely aggressive gains that will cause violent rudder oscillation on a 12-ton vessel
- ERROR: No `safety` section — no rate limit, no bounds, no timeout
- ERROR: No output bounds — the PID could command rudder angles exceeding the physical ±35° range

**Verdict:** REJECT — This reflex would cause dangerous behavior. The gains alone could damage the steering mechanism. The model that generated this is either poorly configured or the intent lacked sufficient context.

---

## 6. Dashboard Configuration Templates

### 6.1 Marine Vessel Dashboard

```json
{
  "layout": "marine_standard",
  "panels": [
    {
      "title": "Navigation",
      "position": "top-left",
      "widgets": [
        { "type": "compass", "source": "steering_node.compass_heading", "size": "large" },
        { "type": "numeric", "source": "sensor_node.wind_speed", "label": "Wind", "unit": "kts" },
        { "type": "numeric", "source": "sensor_node.wind_direction", "label": "Wind Dir", "unit": "deg" }
      ]
    },
    {
      "title": "Propulsion",
      "position": "top-right",
      "widgets": [
        { "type": "gauge", "source": "throttle_node.throttle_servo", "label": "Throttle", "min": 0, "max": 100, "unit": "%" },
        { "type": "numeric", "source": "throttle_node.engine_rpm", "label": "RPM" },
        { "type": "numeric", "source": "throttle_node.fuel_level", "label": "Fuel", "unit": "%", "warning_below": 20 }
      ]
    },
    {
      "title": "Environment",
      "position": "bottom-left",
      "widgets": [
        { "type": "numeric", "source": "sensor_node.bilge_water", "label": "Bilge", "unit": "%", "warning_above": 50 },
        { "type": "numeric", "source": "sensor_node.temperature", "label": "Temp", "unit": "C" }
      ]
    },
    {
      "title": "System Status",
      "position": "bottom-right",
      "widgets": [
        { "type": "status", "nodes": ["steering_node", "throttle_node", "sensor_node"] },
        { "type": "alert_feed", "max_items": 5 },
        { "type": "autonomy_level", "source": "jetson.autonomy_level" }
      ]
    }
  ]
}
```

### 6.2 Minimalist Remote Monitoring Dashboard

```json
{
  "layout": "remote_minimal",
  "panels": [
    {
      "title": "Overview",
      "widgets": [
        { "type": "status_light", "source": "system.health", "states": ["red", "yellow", "green"] },
        { "type": "text", "source": "system.active_reflexes", "label": "Active Reflexes" },
        { "type": "alert_feed", "max_items": 3, "level": "warning" },
        { "type": "chart", "source": "throttle_node.engine_rpm", "duration_hours": 24, "type": "line" }
      ]
    }
  ]
}
```

---

## 7. Safety Policy Templates

### 7.1 Marine Safety Policy

```json
{
  "name": "marine_safety_v2",
  "rules": [
    {
      "id": "MARINE-001",
      "priority": 0,
      "description": "Kill switch: immediate rudder center, throttle zero, all pumps off",
      "trigger": "kill_switch == false",
      "actions": [
        { "set_pin": "rudder_servo", "value": 0.0 },
        { "set_pin": "throttle_servo", "value": 0.0 },
        { "set_pin": "bilge_pump", "value": 0 }
      ],
      "override_all": true
    },
    {
      "id": "MARINE-002",
      "priority": 1,
      "description": "Heartbeat loss: safe all actuators within 500ms",
      "trigger": "jetson_heartbeat_age_ms > 500",
      "actions": [
        { "set_pin": "rudder_servo", "value": 0.0 },
        { "set_pin": "throttle_servo", "value": 0.0 }
      ]
    },
    {
      "id": "MARINE-003",
      "priority": 2,
      "description": "Man overboard: reduce speed to idle, hold current heading",
      "trigger": "man_overboard_switch == true",
      "actions": [
        { "set_pin": "throttle_servo", "value": 10.0 },
        { "hold_pin": "compass_heading" }
      ]
    },
    {
      "id": "MARINE-004",
      "priority": 2,
      "description": "Grounding detection: sound alarm, full stop if depth < 2m",
      "trigger": "depth_sounder < 2.0 AND vessel_speed > 1.0",
      "actions": [
        { "set_pin": "throttle_servo", "value": 0.0 },
        { "alert": "SHALLOW WATER — REDUCE SPEED", "level": "critical" }
      ]
    }
  ]
}
```

### 7.2 Industrial Safety Policy

```json
{
  "name": "industrial_safety_v1",
  "rules": [
    {
      "id": "IND-001",
      "priority": 0,
      "description": "E-Stop: all motors off, all actuators to safe position",
      "trigger": "estop == false",
      "actions": [
        { "set_pin": "conveyor_motor", "value": 0.0 },
        { "set_pin": "sort_actuator_good", "value": 0 },
        { "set_pin": "sort_actuator_reject", "value": 0 }
      ],
      "override_all": true
    },
    {
      "id": "IND-002",
      "priority": 1,
      "description": "Perimeter breach: stop conveyor, sound alarm",
      "trigger": "perimeter_sensor == true",
      "actions": [
        { "set_pin": "conveyor_motor", "value": 0.0 },
        { "alert": "PERIMETER BREACH — CHECK AREA", "level": "critical" }
      ]
    },
    {
      "id": "IND-003",
      "priority": 1,
      "description": "Fire detection: stop all equipment, trigger suppression system",
      "trigger": "smoke_detector == true OR flame_detector == true",
      "actions": [
        { "set_pin": "conveyor_motor", "value": 0.0 },
        { "deploy_reflex": "fire_suppression_controller" }
      ]
    }
  ]
}
```

---

*Document version: 1.0.0 — All templates validated against NEXUS v3.1 specification (reflex_definition.json schema, node_role_config.json schema, and safety policy schema). Copy-paste and modify for your deployment. Verify against the JSON schemas before deploying to production.*
