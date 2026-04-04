# NEXUS Platform — Modification Tips and Tricks

**Version:** 3.1.0  
**Date:** 2028-06-15  
**Classification:** Engineering Reference  
**Audience:** Engineers modifying, extending, and adapting the NEXUS platform  
**Philosophy:** Every tip in this document was learned the hard way. We share them so you don't have to.

---

## 1. Adding a New I2C Sensor Driver

This is the most common modification — every new domain (greenhouse, factory, mining) needs at least one new sensor. We'll walk through the BME280 environmental sensor driver as a real example.

### 1.1 Implement the io_driver_interface.h Vtable

The vtable has 7 mandatory functions. Here's the complete implementation for BME280:

```c
// firmware/components/io_drivers/bme280_driver.c

#include "io_driver_interface.h"
#include "driver/i2c.h"
#include <math.h>

#define BME280_ADDR           0x76  // or 0x77 (SDO pin)
#define BME280_CHIP_ID        0x60
#define BME280_REG_CHIPID     0xD0
#define BME280_REG_CTRL_HUM   0xF2
#define BME280_REG_CTRL_MEAS  0xF4
#define BME280_REG_CONFIG     0xF5
#define BME280_REG_DATA       0xF7

typedef struct {
    uint8_t i2c_bus;
    uint8_t addr;
    // Calibration coefficients (read at init, used for conversion)
    uint16_t dig_T1; int16_t dig_T2, dig_T3;
    uint16_t dig_P1; int16_t dig_P2, dig_P3, dig_P4, dig_P5, dig_P6, dig_P7, dig_P8, dig_P9;
    uint8_t  dig_H1, dig_H2, dig_H3; int16_t dig_H4, dig_H5, dig_H6;
    // Compensated values
    int32_t t_fine;
    float temperature_c;
    float pressure_hpa;
    float humidity_pct;
    bool data_valid;
} bme280_ctx_t;

// --- vtable function 1: init ---
static int bme280_init(void *ctx, const io_pin_config_t *config) {
    bme280_ctx_t *c = (bme280_ctx_t *)ctx;
    c->i2c_bus = config->bus;
    c->addr = config->addr;

    // Read chip ID to verify communication
    uint8_t chip_id = 0;
    i2c_master_read_from_device(c->i2c_bus, c->addr, BME280_REG_CHIPID,
                                &chip_id, 1, 100 / portTICK_PERIOD_MS);
    if (chip_id != BME280_CHIP_ID) {
        return IO_ERR_DEVICE_NOT_FOUND;
    }

    // Read calibration data (18 bytes from registers 0x88-0x9F and 0xA1, 0xE1-0xE7)
    // ... (standard BME280 calibration read — ~40 lines of register reads)

    // Configure: oversampling x1, forced mode
    uint8_t ctrl_hum = 0x01;  // Humidity oversampling x1
    uint8_t ctrl_meas = 0x27; // Temp oversampling x1, pressure x1, forced mode
    uint8_t config = 0x00;    // Standby 0.5ms, filter off
    i2c_master_write_to_device(c->i2c_bus, c->addr, BME280_REG_CTRL_HUM,
                               &ctrl_hum, 1, 100 / portTICK_PERIOD_MS);
    i2c_master_write_to_device(c->i2c_bus, c->addr, BME280_REG_CONFIG,
                               &config, 1, 100 / portTICK_PERIOD_MS);
    i2c_master_write_to_device(c->i2c_bus, c->addr, BME280_REG_CTRL_MEAS,
                               &ctrl_meas, 1, 100 / portTICK_PERIOD_MS);
    c->data_valid = false;
    return IO_OK;
}

// --- vtable function 2: read ---
static int bme280_read(void *ctx, io_reading_t *reading) {
    bme280_ctx_t *c = (bme280_ctx_t *)ctx;

    // Trigger forced measurement
    uint8_t ctrl = 0x27;
    i2c_master_write_to_device(c->i2c_bus, c->addr, BME280_REG_CTRL_MEAS,
                               &ctrl, 1, 50 / portTICK_PERIOD_MS);

    // Wait for measurement complete (~8ms for x1 oversampling)
    vTaskDelay(pdMS_TO_TICKS(10));

    // Read 8 bytes from 0xF7 (pressure MSB..LSB, temp MSB..LSB, humidity MSB..LSB)
    uint8_t buf[8];
    i2c_master_read_from_device(c->i2c_bus, c->addr, BME280_REG_DATA,
                                buf, 8, 50 / portTICK_PERIOD_MS);

    // Convert raw values using calibration coefficients
    int32_t adc_P = ((uint32_t)buf[0] << 12) | ((uint32_t)buf[1] << 4) | ((buf[2] >> 4) & 0x0F);
    int32_t adc_T = ((uint32_t)buf[3] << 12) | ((uint32_t)buf[4] << 4) | ((buf[5] >> 4) & 0x0F);
    int32_t adc_H = ((uint32_t)buf[6] << 8) | buf[7];

    // Temperature compensation (BME280 formula)
    // ... (standard BME280 compensation code — ~30 lines)
    c->temperature_c = compensate_temperature(c, adc_T);
    c->pressure_hpa = compensate_pressure(c, adc_P) / 100.0f;
    c->humidity_pct = compensate_humidity(c, adc_H);

    reading->values[0] = c->temperature_c;
    reading->values[1] = c->pressure_hpa;
    reading->values[2] = c->humidity_pct;
    reading->num_values = 3;
    c->data_valid = true;
    return IO_OK;
}

// --- vtable function 3: write (not applicable for sensor) ---
static int bme280_write(void *ctx, const io_write_cmd_t *cmd) {
    return IO_ERR_NOT_SUPPORTED;  // BME280 is read-only
}

// --- vtable function 4: configure ---
static int bme280_configure(void *ctx, const char *key, const char *value) {
    bme280_ctx_t *c = (bme280_ctx_t *)ctx;
    if (strcmp(key, "oversampling") == 0) {
        int os = atoi(value);
        if (os < 1 || os > 16) return IO_ERR_INVALID_PARAM;
        // Set oversampling register...
        return IO_OK;
    }
    return IO_ERR_UNKNOWN_KEY;
}

// --- vtable function 5: selftest ---
static int bme280_selftest(void *ctx) {
    bme280_ctx_t *c = (bme280_ctx_t *)ctx;
    uint8_t chip_id = 0;
    i2c_master_read_from_device(c->i2c_bus, c->addr, BME280_REG_CHIPID,
                                &chip_id, 1, 100 / portTICK_PERIOD_MS);
    if (chip_id != BME280_CHIP_ID) return IO_ERR_SELFTEST_FAIL;

    // Read data and check for plausible values
    io_reading_t reading;
    bme280_read(ctx, &reading);
    if (reading.num_values != 3) return IO_ERR_SELFTEST_FAIL;
    if (reading.values[0] < -40.0f || reading.values[0] > 85.0f) return IO_ERR_SELFTEST_FAIL;
    if (reading.values[1] < 300.0f || reading.values[1] > 1100.0f) return IO_ERR_SELFTEST_FAIL;
    if (reading.values[2] < 0.0f || reading.values[2] > 100.0f) return IO_ERR_SELFTEST_FAIL;
    return IO_OK;
}

// --- vtable function 6: deinit ---
static int bme280_deinit(void *ctx) {
    bme280_ctx_t *c = (bme280_ctx_t *)ctx;
    c->data_valid = false;
    return IO_OK;
}

// --- vtable function 7: get_info ---
static int bme280_get_info(void *ctx, io_driver_info_t *info) {
    strcpy(info->name, "bme280");
    strcpy(info->type, "i2c_sensor");
    strcpy(info->description, "Bosch BME280 environmental sensor");
    info->num_readings = 3;
    strcpy(info->reading_names[0], "temperature_c");
    strcpy(info->reading_names[1], "pressure_hpa");
    strcpy(info->reading_names[2], "humidity_pct");
    info->reading_units[0] = IO_UNIT_CELSIUS;
    info->reading_units[1] = IO_UNIT_HECTOPASCAL;
    info->reading_units[2] = IO_UNIT_PERCENT;
    return IO_OK;
}

// Vtable
const io_driver_vtable_t bme280_vtable = {
    .init = bme280_init,
    .read = bme280_read,
    .write = bme280_write,
    .configure = bme280_configure,
    .selftest = bme280_selftest,
    .deinit = bme280_deinit,
    .get_info = bme280_get_info,
};
```

### 1.2 Register in io_driver_registry.json

```json
{
  "bme280": {
    "vtable_symbol": "bme280_vtable",
    "context_size": 256,
    "i2c_addrs": ["0x76", "0x77"],
    "auto_detect": {
      "addr": "0x76",
      "chip_id_reg": "0xD0",
      "chip_id_val": "0x60"
    },
    "readings": {
      "temperature_c": {"unit": "celsius", "range": [-40, 85], "precision": 0.01},
      "pressure_hpa": {"unit": "hectopascal", "range": [300, 1100], "precision": 0.01},
      "humidity_pct": {"unit": "percent", "range": [0, 100], "precision": 0.01}
    },
    "selftest": {
      "description": "Read chip ID and verify plausible sensor values",
      "timeout_ms": 500
    },
    "timing": {
      "init_ms": 50,
      "read_ms": 12,
      "selftest_ms": 500
    },
    "known_limitations": [
      "Maximum I2C speed: 400kHz (not 1MHz)",
      "Forced mode: each read triggers a new 8ms conversion",
      "Chip ID 0x60 is shared with BMP280 — use register 0xD0-0xD1 for disambiguation"
    ]
  }
}
```

### 1.3 Add to AUTO_DETECT scanning

The I2C bus scan at boot probes addresses listed in the registry's `auto_detect` section. When a chip ID match is found, the driver is auto-registered and its readings appear in the telemetry stream without any configuration.

### 1.4 Test on Real Hardware

**Before committing:**
1. Flash the firmware to a dev ESP32-S3 with the BME280 connected
2. Verify init succeeds (check serial output for "BME280 initialized at 0x76")
3. Verify readings are plausible (temp ~20°C, pressure ~1013 hPa, humidity ~50%)
4. Run selftest (should pass)
5. Disconnect the sensor, reconnect, verify auto-detection works
6. Run the VM with a reflex that reads BME280 values and writes them to an actuator — verify the reflex compiles and executes

---

## 2. Adding a New VM Opcode

### 2.1 The 6 Files You Must Change

Adding a new opcode is a cross-cutting change that touches firmware, the compiler, tests, and documentation. Here are the 6 files:

**File 1: `vm_opcodes.h`**
```c
// Add to the opcode enum (if replacing an unused slot) or document
// that the new opcode uses a SYSCALL encoding via NOP
// Example: Adding ABS_I32 as a new arithmetic opcode
// Note: We are NOT adding new opcodes to the ISA. The 32-opcode
// ISA is frozen. New functionality uses the SYSCALL mechanism.
```

**Important:** The v3.1 ISA has 32 fixed opcodes (0x00-0x1F) and is frozen. You cannot add new opcodes. Instead, use the SYSCALL mechanism (NOP with flags bit 7 set) for new functionality. The SYSCALL operand1 field has room for 255 syscall IDs; we've used 4 so far (HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT).

**File 2: `vm_dispatch.c`** — Add the SYSCALL handler:
```c
case 0x05:  // New syscall: CUSTOM_OPERATION
    custom_operation(vm, operand2 & 0xFFFF);
    break;
```

**File 3: `vm_validator.c`** — Add validation rules:
```c
case 0x05:  // CUSTOM_OPERATION
    // Verify stack has required operands
    if (simulated_sp < 2) return ERR_VALIDATE_STACK_UNDERFLOW;
    // Verify operand2 is in valid range
    if ((operand2 & 0xFFFF) >= MAX_CUSTOM_PARAMS) return ERR_VALIDATE_OPERAND;
    break;
```

**File 4: `compiler.py`** (Jetson) — Add the compilation rule:
```python
def compile_custom_operation(self, node):
    """Compile a CUSTOM_OPERATION from the reflex JSON."""
    param = node.args[0]
    self.emit_syscall(0x05, param)
```

**File 5: `test_vm_opcodes.c`** — Add comprehensive unit tests:
```c
TEST_CASE("SYSCALL 0x05: basic operation", "[vm]") {
    vm_t vm;
    vm_init(&vm);
    // Set up stack with test operands
    PUSH_F32(&vm, 3.14f);
    PUSH_F32(&vm, 2.71f);
    // Emit the syscall instruction
    emit_syscall(&vm, 0x05, 0x0001);
    emit_halt(&vm);
    // Execute
    vm_execute(&vm);
    // Verify result
    float result = f32_from_u32(vm.stack[--vm.sp]);
    TEST_ASSERT_FLOAT_WITHIN(0.01, expected, result);
}
```

**File 6: `synthesis.md`** (or the reflex schema) — Document the new operation's semantics, stack effect, cycle count, and safety constraints.

### 2.2 Why We Added CLAMP_F but Would Never Do It Again

CLAMP_F seemed elegant — one instruction instead of two (MAX_F+MIN_F). But the encoding constraint (shared upper 16 bits) was a trap:

1. The compiler had to verify the constraint at compile time
2. The validator had to verify it again
3. The decoder had to reconstruct the upper half at runtime
4. Edge case: what if lower == upper? (degenerate range) — we didn't handle this initially
5. Edge case: what if lower > upper? (inverted range) — we didn't handle this either
6. The NOP-follows-CLAMP trick for general clamps was a maintenance nightmare

**Two simple instructions (MAX_F + MIN_F) are always better than one clever instruction.** If you find yourself designing a complex encoding to save one instruction, stop. Use two simple ones.

---

## 3. Customizing the Trust Score Parameters

### 3.1 Per-Subsystem Configuration

The trust score parameters are configurable per subsystem in the autonomy configuration:

```json
{
  "subsystem_trust_params": {
    "steering": {
      "alpha_gain": 0.002,
      "alpha_loss": 0.05,
      "level_3_threshold": 0.70,
      "level_5_threshold": 0.95,
      "evaluation_interval_ms": 100
    },
    "lighting": {
      "alpha_gain": 0.010,
      "alpha_loss": 0.05,
      "level_3_threshold": 0.60,
      "level_5_threshold": 0.85,
      "evaluation_interval_ms": 1000
    }
  }
}
```

Steering has conservative parameters (low alpha_gain, high threshold) because incorrect steering can cause collisions. Lighting has relaxed parameters (high alpha_gain, low threshold) because incorrect lighting is merely annoying, not dangerous.

### 3.2 The v2.0 Adaptive Trust Feature

Since v2.0, parameters auto-tune based on operator behavior:

```python
def adaptive_tune(subsystem: str, approval_history: list) -> dict:
    """Auto-tune trust parameters based on recent approval rate."""
    recent = approval_history[-100:]  # Last 100 evaluations
    approval_rate = sum(1 for e in recent if e.approved) / len(recent)

    if approval_rate > 0.95:
        # Operator almost always approves → speed up trust gain
        alpha_gain = min(0.005, base_gain * 2.0)
    elif approval_rate < 0.50:
        # Operator rejects frequently → slow down trust gain
        alpha_gain = max(0.001, base_gain * 0.5)
    else:
        alpha_gain = base_gain

    return {"alpha_gain": alpha_gain}
```

The adaptation is slow (updates every 100 evaluations) and bounded (alpha_gain ∈ [0.001, 0.005]) to prevent oscillation.

### 3.3 How to Reset Trust to Zero

After hardware replacement (e.g., new steering actuator), reset the trust for that subsystem:

```bash
# Via the chat interface:
> "Reset trust for steering subsystem"

# Via the gRPC API:
stub.SetAutonomyLevel(autonomy_pb2.LevelRequest(
    subsystem="steering",
    level=0,  # Reset to MANUAL
    reset_trust=True
))
```

The trust score is stored in a local SQLite database on the Jetson. Resetting it sets the score to 0.0 and clears the approval history.

### 3.4 How to Fast-Track Trust for Demo Mode

**⚠️ NEVER DO THIS IN PRODUCTION.**

```python
# Demo mode only — set alpha_gain to 10× normal
config = {
    "subsystem_trust_params": {
        "steering": {
            "alpha_gain": 0.020,  # 10× normal
            "alpha_loss": 0.005,  # 10× more forgiving
            "level_3_threshold": 0.40,  # Very low
            "level_5_threshold": 0.60   # Very low
        }
    }
}
```

With these settings, Level 3 autonomy is reached after ~15 flawless evaluations instead of ~150. Level 5 after ~50 instead of ~300.

**Why you should NEVER ship this:** The trust score exists to prevent premature autonomy. Fast-tracking bypasses the entire safety rationale. A demo with fast-tracked trust will show the system operating autonomously, creating the impression that it's safe for production. It's not — it just hasn't had enough exposure to edge cases to fail. We've seen customers demand "demo mode trust" in production after seeing a demo. Refuse.

---

## 4. Creating Custom Reflex Templates

### 4.1 The Reflex JSON Schema

Every reflex is defined as a JSON document that conforms to the schema in `jetson/compiler/reflex_schema.json`:

```json
{
  "$schema": "reflex_schema.json",
  "name": "heading_hold_pid",
  "version": "1.2.0",
  "priority": 10,
  "tick_rate_hz": 10,
  "variables": {
    "integral": {"type": "float32", "initial": 0.0},
    "prev_error": {"type": "float32", "initial": 0.0}
  },
  "sensors": {
    "heading": {"pin": 0, "type": "float32", "unit": "deg"},
    "setpoint": {"pin": 1, "type": "float32", "unit": "deg"}
  },
  "actuators": {
    "rudder": {"pin": 0, "min": -45.0, "max": 45.0, "safe": 0.0}
  },
  "pid_controllers": {
    "heading_pid": {
      "kp": 1.2, "ki": 0.05, "kd": 0.3,
      "integral_limit": 1500.0,
      "output_min": -45.0, "output_max": 45.0
    }
  },
  "code": "READ_PIN heading; READ_PIN setpoint; PID_COMPUTE heading_pid; MAX_F -45.0; MIN_F 45.0; WRITE_PIN rudder"
}
```

### 4.2 Best Practices for Reflex Design

1. **Keep it simple.** The average production reflex has 8 instructions. If your reflex exceeds 50 instructions, it's too complex. Break it into multiple reflexes with different priorities.

2. **Use state machines, not loops.** The VM has no loop construct. State machines are implemented as JUMP instructions at the end of the bytecode. The VM naturally re-enters at instruction 0 on the next tick.

3. **Avoid deep nesting.** The stack depth limit is 256 entries. Each PUSH adds one entry. A reflex that pushes 10 values, calls 5 subroutines, and has 3 levels of conditional logic can easily hit the limit. Use stack depth analysis in the compiler.

4. **Always clamp actuator outputs.** Every WRITE_PIN should be preceded by MAX_F and MIN_F. The safety guard also clamps, but clamping in the reflex provides defense-in-depth and avoids the safety guard's rate-limiting penalty.

5. **Use variables for persistence.** Variables persist across ticks. If you need a running sum, a previous value, or a state flag, use a variable.

6. **Test edge cases.** What happens when the sensor reads NaN? (The VM treats NaN as 0.0.) What happens when setpoint equals measurement? (PID output is 0.) What happens at power-on before sensors are valid? (All sensor registers are initialized to 0.0.)

### 4.3 The PID Template — Most Common Starting Point

85% of deployed reflexes are PID controllers. Here's the template:

```json
{
  "name": "pid_template",
  "version": "1.0.0",
  "priority": 10,
  "tick_rate_hz": 10,
  "sensors": {
    "process_variable": {"pin": 0, "type": "float32"},
    "setpoint": {"pin": 1, "type": "float32"}
  },
  "actuators": {
    "output": {"pin": 0, "min": -100.0, "max": 100.0, "safe": 0.0}
  },
  "pid_controllers": {
    "main_pid": {
      "kp": 1.0, "ki": 0.1, "kd": 0.01,
      "integral_limit": 500.0,
      "output_min": -100.0, "output_max": 100.0
    }
  },
  "code": "READ_PIN setpoint; READ_PIN process_variable; PID_COMPUTE main_pid; MAX_F -100.0; MIN_F 100.0; WRITE_PIN output"
}
```

Customize: change sensor/actuator pin mappings, adjust Kp/Ki/Kd, set appropriate min/max/output limits.

### 4.4 The Threshold Monitor Template

Second most common: triggers an actuator when a sensor crosses a threshold.

```json
{
  "name": "threshold_template",
  "version": "1.0.0",
  "priority": 5,
  "tick_rate_hz": 1,
  "sensors": {
    "input": {"pin": 0, "type": "float32"}
  },
  "actuators": {
    "alarm": {"pin": 0, "min": 0.0, "max": 1.0, "safe": 0.0}
  },
  "variables": {
    "threshold": {"type": "float32", "initial": 80.0}
  },
  "code": "READ_PIN input; READ_PIN 64;  // variable 0 = threshold\nGT_F; WRITE_PIN alarm"
}
```

### 4.5 The Sequencer Template

For multi-step behaviors (e.g., startup sequence, emergency shutdown):

```json
{
  "name": "sequencer_template",
  "version": "1.0.0",
  "priority": 20,
  "tick_rate_hz": 1,
  "variables": {
    "state": {"type": "float32", "initial": 0.0},
    "timer": {"type": "float32", "initial": 0.0}
  },
  "actuators": {
    "valve_a": {"pin": 0, "min": 0.0, "max": 1.0, "safe": 0.0},
    "valve_b": {"pin": 1, "min": 0.0, "max": 1.0, "safe": 0.0}
  },
  "code": "READ_PIN 64;  // state\nPUSH_I8 0; EQ_F; JUMP_IF_FALSE state_1\nPUSH_F32 1.0; WRITE_PIN valve_a; PUSH_F32 1.0; WRITE_PIN 65;  // timer=1\nREAD_PIN 64; PUSH_I8 1; EQ_F; JUMP_IF_FALSE state_1\nPUSH_F32 1.0; WRITE_PIN valve_b;  // state 1: open B too\nstate_1: ..."
}
```

### 4.6 How to Test a Reflex Before Deploying

Use the simulation harness:

```python
# jetson/tests/test_reflex_simulation.py

from compiler.compiler import compile_reflex
from simulator.vm_simulator import VMSimulator

# Compile the reflex
reflex_json = load_json("my_reflex.json")
bytecode = compile_reflex(reflex_json)

# Create a simulated environment
sim = VMSimulator()
sim.set_sensor(0, 10.0)   # heading = 10°
sim.set_sensor(1, 10.0)   # setpoint = 10° (on target)

# Run 100 ticks
for tick in range(100):
    outputs = sim.tick(bytecode)

# Verify: with heading == setpoint, rudder output should be ~0
assert abs(outputs[0]) < 0.1  # rudder near center

# Now perturb: heading drifts to 15°
sim.set_sensor(0, 15.0)
for tick in range(100):
    outputs = sim.tick(bytecode)

# Verify: rudder should be nonzero, correcting toward setpoint
assert outputs[0] != 0.0  # rudder deflecting
```

The simulation harness also checks:
- Cycle budget compliance (no reflex should use > 10,000 cycles)
- Stack depth compliance (no reflex should use > 128 stack entries)
- Actuator bounds compliance (all outputs within configured min/max)
- No NaN/Inf in outputs

---

## 5. Extending the Serial Protocol

### 5.1 Adding a New Message Type

Message types 0x00-0x7F are reserved for the core protocol. Types 0x80-0xFF are the extension range for domain-specific messages.

To add a new message type:

1. Define the message type constant in `shared/protocol_types.h` and `shared/protocol_types.py`
2. Add a handler function in `firmware/components/protocol/message_dispatch.c`
3. Register the handler in the dispatch table
4. Add the corresponding handler on the Jetson side in `serial_bridge/bridge.py`
5. Add unit tests for the new message type

**The wire compatibility promise:** "Any v1.0 firmware works with any v3.1 Jetson software." This means:
- New message types must be gracefully ignored by older firmware (unknown type → discard + log)
- Existing message types must never change their wire format
- New fields can be added to existing messages only at the end of the payload (older firmware ignores trailing bytes)

### 5.2 Adding a New Telemetry Format

Binary telemetry was the single biggest optimization we made (12.5× bandwidth savings over JSON). To add a new telemetry format:

1. Define the binary layout in a shared header file
2. Add serialization on the ESP32 side (pack sensor values into fixed-offset binary buffer)
3. Add deserialization on the Jetson side (unpack binary buffer into Python dict)
4. Update the telemetry schema in `mqtt_topics.json`

Binary layout example:
```c
// Shared binary telemetry format for marine domain
typedef struct __attribute__((packed)) {
    uint32_t timestamp_ms;
    float heading_deg;
    float speed_knots;
    float latitude;
    float longitude;
    float wind_speed_ms;
    float wind_direction_deg;
    float rudder_angle_deg;
    float throttle_percent;
    uint8_t flags;         // Bitfield: GPS_valid, compass_valid, etc.
    uint16_t battery_mv;
} marine_telemetry_t;  // 42 bytes
```

### 5.3 Adding a New Command Type

Commands (MSG_COMMAND, type 0x0A) have a flexible payload format. To add a new command:

1. Define the command ID in `shared/protocol_types.h`
2. Add a handler in `firmware/components/protocol/command_handler.c`
3. Add validation in the command dispatch table
4. Add the corresponding Jetson-side API call in `node_manager/manager.py`

---

## 6. Configuring for a New Domain

NEXUS was designed for marine but works for anything. Here's how to adapt it for a new domain, using greenhouse climate control as a real customer example.

### 6.1 Step 1: Define Equipment Template

Create `configs/greenhouse/equipment_template.json`:

```json
{
  "domain": "greenhouse",
  "nodes": [
    {
      "role": "climate_controller",
      "sensors": [
        {"name": "air_temp", "driver": "bme280", "reading": "temperature_c", "pin": 0},
        {"name": "humidity", "driver": "bme280", "reading": "humidity_pct", "pin": 1},
        {"name": "co2_ppm", "driver": "scd30", "reading": "co2_ppm", "pin": 2},
        {"name": "soil_moisture", "driver": "capacitive_soil", "reading": "moisture_pct", "pin": 3},
        {"name": "light_lux", "driver": "max44009", "reading": "light_lux", "pin": 4}
      ],
      "actuators": [
        {"name": "vent_opener", "gpio": 4, "mode": "pwm", "freq_hz": 50, "safe": 0},
        {"name": "heater", "gpio": 5, "mode": "relay", "safe": 0},
        {"name": "co2_injector", "gpio": 6, "mode": "relay", "safe": 0},
        {"name": "irrigation_pump", "gpio": 7, "mode": "relay", "safe": 0}
      ]
    }
  ]
}
```

### 6.2 Step 2: Create Domain-Specific Safety Policy

Create `configs/greenhouse/safety_policy.json`:

```json
{
  "global_rules": [
    {"id": "max_greenhouse_temp", "trigger": {"sensor": "air_temp", "threshold": 45.0, "operator": ">"}, "response": {"type": "safe_state"}, "severity": "CRITICAL"},
    {"id": "min_soil_moisture", "trigger": {"sensor": "soil_moisture", "threshold": 10.0, "operator": "<"}, "response": {"type": "safe_state"}, "severity": "HIGH"}
  ],
  "actuator_profiles": {
    "vent_opener": {"max_rate": 10.0, "min_on_ms": 100, "max_on_time_s": 3600},
    "heater": {"max_on_time_s": 1800, "cooldown_s": 60},
    "irrigation_pump": {"max_on_time_s": 600, "cooldown_s": 300}
  },
  "degradation_profile": {
    "at_high_temp": "disable_heater",
    "at_low_co2": "disable_co2_injector"
  }
}
```

### 6.3 Step 3: Write Domain-Specific Reflex Templates

Create `configs/greenhouse/reflex_templates/`:

```json
{
  "name": "temp_pid",
  "version": "1.0.0",
  "description": "Maintain target temperature using heater and vent",
  "sensors": {"air_temp": {"pin": 0}, "target_temp": {"pin": 5}},
  "actuators": {"heater": {"pin": 0, "min": 0, "max": 1, "safe": 0}, "vent_opener": {"pin": 1, "min": 0, "max": 1, "safe": 0}},
  "pid_controllers": {"temp_pid": {"kp": 0.5, "ki": 0.02, "kd": 0.1, "output_min": -1.0, "output_max": 1.0}},
  "code": "READ_PIN target_temp; READ_PIN air_temp; PID_COMPUTE temp_pid; DUP; MAX_F 0.0; MIN_F 1.0; WRITE_PIN vent_opener; NEG_F; MAX_F 0.0; MIN_F 1.0; WRITE_PIN heater"
}
```

### 6.4 Step 4: Calibrate Trust Parameters

Greenhouse climate control is lower-risk than marine steering. Use relaxed trust parameters:

```json
{
  "subsystem_trust_params": {
    "climate": {"alpha_gain": 0.005, "alpha_loss": 0.05, "level_3_threshold": 0.50, "level_5_threshold": 0.80},
    "irrigation": {"alpha_gain": 0.003, "alpha_loss": 0.05, "level_3_threshold": 0.60, "level_5_threshold": 0.85}
  }
}
```

### 6.5 Real Example: Greenhouse Climate Control

A customer adapted NEXUS for a 2000m² commercial greenhouse in the Netherlands. Setup took 3 days (1 day hardware wiring, 1 day sensor calibration, 1 day reflex tuning). The system has been running for 8 months with these results:

- Temperature control accuracy: ±0.5°C (was ±2°C with the previous timer-based system)
- Energy savings: 23% (PID control vs. bang-bang)
- Crop yield improvement: 8% (more consistent climate)
- Zero safety incidents
- The learning pipeline discovered that CO2 injection effectiveness varies with light intensity — a pattern the operator hadn't noticed in 15 years of farming.

---

## 7. Performance Optimization Tips

### 7.1 Binary Telemetry: 12.5× Bandwidth Savings

The single biggest optimization we made. JSON telemetry for a marine node with 10 sensor values averaged ~500 bytes per message at 10Hz = 5 KB/s. Binary telemetry (fixed-offset packed struct) averages ~40 bytes per message = 400 bytes/s.

**Implementation:** Define a packed struct with fixed offsets. No field names, no delimiters, no JSON overhead. The receiver knows the layout from the message type.

### 7.2 I2C Read Caching

Before v2.0, every subsystem that needed a sensor reading performed its own I2C read. With 3 subsystems reading the compass at 10Hz, we had 30 I2C transactions per second for the same data.

**Fix:** The I/O poll task reads all sensors once per tick and caches the values. The VM reads from the sensor register file (in SRAM), not from the I2C bus. This reduced I2C traffic by 3× and freed ~200µs per tick.

### 7.3 DMA for UART

Before v3.0, UART RX used interrupt-driven reads. Each received byte triggered an ISR that copied it to a buffer. At 921600 baud, that's ~92,160 interrupts per second — each consuming 2-5µs of CPU time.

**Fix:** UART DMA transfers the entire received byte stream to a buffer in hardware. The CPU is only interrupted when a complete COBS frame is received (via DMA half/full buffer interrupts). This freed ~200µs per tick of CPU time, enabling support for 10+ nodes per Jetson.

### 7.4 PSRAM Only for Observation Buffer

Everything safety-critical goes in SRAM. PSRAM is used ONLY for the observation buffer (and the flight recorder). Why:

- PSRAM has no power-loss protection — data is volatile
- PSRAM access is slower than SRAM (~3× latency for random access)
- PSRAM access can be disrupted by concurrent flash operations

If you need to add another PSRAM consumer, file an ADR. The current PSRAM usage is:
- Observation buffer: 6 MB (configurable)
- Flight recorder: 256 KB
- Total: ~6.3 MB of 8 MB

### 7.5 The "Fast Reflex" Pattern

Pin critical reflexes to Core 0 (the safety core) and everything else to Core 1:

```c
// In vm_tick_task creation:
xTaskCreatePinnedToCore(vm_tick_task, "vm_tick", 8192, NULL, 18, NULL, 0);
// ^^^ Core 0 — same core as safety supervisor, no cross-core cache misses

// I/O poll and telemetry on Core 1:
xTaskCreatePinnedToCore(io_poll_task, "io_poll", 4096, NULL, 17, NULL, 1);
xTaskCreatePinnedToCore(telemetry_task, "telemetry", 4096, NULL, 16, NULL, 1);
```

This ensures the VM tick has consistent timing because it doesn't compete with I/O bus transactions for cache lines. Measured improvement: 15% reduction in VM tick jitter.

---

## 8. Debugging War Stories (and What We Learned)

### 8.1 "The Case of the Missing Kill Switch Interrupt"

**Symptom:** Kill switch press had no effect during OTA updates.

**Root cause:** The E-Stop ISR was not marked `IRAM_ATTR`. During OTA, the SPI flash is busy for ~100ms. The CPU tried to fetch ISR instructions from flash, got a cache miss fault, and the ISR never executed.

**Fix:** Added `IRAM_ATTR` to the ISR function. Verified with the HIL test bench.

**Lesson:** EVERY safety ISR must be in IRAM. No exceptions. The CI pipeline now checks this with a custom lint rule.

### 8.2 "The 3AM CRC Mismatch"

**Symptom:** CRC-16 failures at ~3:00 AM on vessels in the Pacific timezone. Not reproducible in the lab.

**Root cause:** The message header uses big-endian byte order for the sequence number field. The Jetson (x86, little-endian) was writing the sequence number in native byte order, not network byte order. The mismatch only manifested when the sequence number crossed 256 (0x0100 in big-endian vs 0x0001 in little-endian). This happened roughly every 256 messages, which at 10Hz telemetry was every 25.6 seconds — but the error only caused CRC failure when combined with a specific payload pattern that made the two byte orders produce the same CRC for all but 1 in 256 cases.

**Fix:** Added `htons()`/`ntohs()` to all multi-byte header fields on both sides.

**Lesson:** Always use explicit byte-order conversion. Never assume the platform matches the wire format.

### 8.3 "The Phantom Heartbeat"

**Symptom:** Safety supervisor reporting heartbeat loss every few minutes, causing spurious DEGRADED mode transitions.

**Root cause:** Two specification files contradicted each other. The wire protocol spec said 1000ms interval; the safety spec said 100ms. We implemented the 1000ms interval, but the safety monitor expected 100ms.

**Fix:** Implemented the 100ms interval (safety spec wins). Added a `SAFETY_MODE` compile flag.

**Lesson:** When specs contradict, the safety spec wins. Document the resolution in an ADR.

### 8.4 "The Reflex That Wouldn't Deploy"

**Symptom:** Operator describes a reflex in chat, the LLM generates it, but deployment fails with `ERR_VALIDATE_STACK_OVERFLOW`.

**Root cause:** The JSON schema validation was too strict. The reflex JSON had an extra field ("description") that wasn't in the schema. The parser rejected it before compilation.

**Fix:** Made the JSON parser lenient — ignore unknown fields with a warning instead of rejecting. Added the "description" field to the schema.

**Lesson:** Be lenient in what you accept, strict in what you produce. A reflex with an extra field should deploy with a warning, not fail.

### 8.5 "The Observation Buffer That Ate Memory"

**Symptom:** After 30-minute observation sessions, the ESP32 started behaving erratically — sensors reading zero, VM crashing.

**Root cause:** The observation buffer (PSRAM ring buffer) filled up silently. The buffer write pointer wrapped around and started overwriting data. But the write pointer and the drain pointer are both uint32_t — at exactly 2^32 bytes of total writes (which takes ~5 days at 28.8 KB/s), the pointers alias and the drain task reads stale data. The stale data had wrong sequence numbers, causing the Jetson to reject all observation chunks and retry endlessly.

**Fix:** Added buffer full detection (80% warning, 95% stop recording). Added a maximum recording duration (5 minutes default, configurable). Added backpressure to the serial drain task.

**Lesson:** Silent data loss is the worst kind of failure. Always detect and report buffer fullness.

---

## 9. Common Mistakes and Anti-Patterns

Here are 12 things we've seen new developers do wrong, with fixes:

### 1. Putting ISR code in flash, not IRAM
**Fix:** Mark every ISR function and every function called from an ISR with `IRAM_ATTR`. The CI pipeline checks this automatically.

### 2. Using `printf()` in an ISR
**Fix:** Write to a ring buffer in DRAM instead. Have a normal-priority task drain the buffer.

### 3. Forgetting to strip the COBS trailing sentinel
**Fix:** After COBS decode, output length = `encoded_length - 2` (one overhead byte, one sentinel).

### 4. Allocating safety-critical data in PSRAM
**Fix:** Only the observation buffer goes in PSRAM. Everything else in SRAM.

### 5. Using internal pull-ups for kill switch sense wire
**Fix:** Use external 10KΩ pull-up at the connector. Internal pull-up is too weak (30-50KΩ).

### 6. Implementing CLAMP_F with only one bound
**Fix:** Always decompose to MAX_F + MIN_F. Never use the standalone CLAMP_F encoding.

### 7. Swapping PID_COMPUTE arguments (setpoint vs input)
**Fix:** Setpoint is pushed first (TOS-1), input second (TOS). Verify with a known test case.

### 8. Not handling the 50ms baud settling delay
**Fix:** Always wait 50ms after baud switch before sending PING. Both sides independently.

### 9. Using QoS 2 for everything in MQTT
**Fix:** Use QoS 0 for telemetry, QoS 1 for commands, QoS 2 only for safety events and overrides.

### 10. Setting alpha_gain > 0.01 in production trust configuration
**Fix:** Maximum alpha_gain in production is 0.005. Higher values bypass the safety rationale of slow trust accumulation.

### 11. Putting raw bytecode in wire protocol payloads without byte-swapping
**Fix:** Always use explicit serialization with byte-order conversion. VM operands are little-endian; protocol headers are big-endian.

### 12. Creating a reflex that writes to pin N instead of variable N
**Fix:** Pin indices are 0-63. Variable indices are 64-319 (operand1 = variable_index + 64). The validator enforces this, but always double-check your pin mappings.

---

*Document version: 3.1.0 | Last updated: 2028-06-15 | Every tip earned the hard way*
