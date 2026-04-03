# NEXUS Platform — Claude Code Build Prompts

**Purpose:** Sequential prompts to build the entire NEXUS Post-Coding Distributed Intelligence Platform from a blank repository. Each prompt is self-contained and references the production specification.

**How to use:** Create a fresh repository, run each prompt in order via Claude Code (or any AI coding assistant). Each prompt produces a working deliverable that the next prompt builds upon.

**Reading order:** Prompts within a phase must run sequentially. Phases can overlap across developers.

---

## Quick-Start Guide

| Goal | Prompts | Calendar Time |
|------|---------|--------------|
| **Minimum demo** (LED blinker via chat) | 0, 1, 2, 3, 4, 5, 6 | ~8 weeks |
| **Full autopilot with learning** | 0-12 | ~16 weeks |
| **Jetson side only** (no firmware) | 0, 6, 7, 8, 9, 10, 11 | ~10 weeks |
| **Firmware side only** (no Jetson) | 0, 1, 2, 3, 4, 5 | ~8 weeks |

---

## Prompt 0: Project Scaffolding

**Dependencies:** None
**Estimated effort:** 1 day
**Goal:** Initialize monorepo with /firmware (ESP-IDF C), /jetson (Python), /shared (proto, schemas), CI pipeline, and documentation structure.

### Prompt

```
Initialize a monorepo for the NEXUS Platform, a post-coding distributed intelligence system for industrial robotics. Create this structure:

/firmware/              — ESP-IDF v5.2+ C project (universal limb firmware)
  components/
    nexus_protocol/    — COBS framing, CRC, message dispatch
    nexus_io/           — I/O abstraction layer, pin config, drivers
    nexus_vm/           — Bytecode VM (32 opcodes, stack machine)
    nexus_safety/       — Kill switch ISR, watchdog, heartbeat
  main/main.c           — Boot sequence, integration
  partitions.csv         — Flash partition table
/firmware/config/       — Pin configs, safety configs (JSON)
/jetson/                — Python package (cognitive services)
  nexus_cognitive/
    __init__.py
    nexus_module.py     — Base class for all modules
    serial_bridge.py     — Serial port management
    node_manager.py      — Node discovery + role assignment
    reflex_orchestrator.py
    learning_pipeline.py
    safety_manager.py    — Trust score + autonomy
    chat_interface.py
    mqtt_bridge.py
  proto/                — Generated gRPC stubs
/shared/                — Cross-cutting specs
  schemas/              — JSON schemas (node_role, reflex_definition, etc.)
  specs/                — Markdown spec files (reference only)
/tests/                 — Test suites
  firmware/tests/        — Unity test framework for C
  jetson/tests/         — pytest
docs/                   — Architecture docs

Key files to create:
1. firmware/CMakeLists.txt — ESP-IDF project pointing to components/ and main/
2. firmware/partitions.csv — Factory (512KB), ota_0 (1.5MB), ota_1 (1.5MB), nvs (24KB), reflexes (2MB/LittleFS), phy_init (4KB)
3. jetson/pyproject.toml — Python 3.11, dependencies: grpcio, paho-mqtt, pyserial, numpy, scikit-learn, hdbscan, pyarrow, llama-cpp-python
4. jetson/nexus_cognitive/proto/cluster_api.proto — Stub 6 gRPC services: NodeDiscovery, NodeManager, ReflexOrchestrator, LearningService, AutonomyManager, ChatService
5. .github/workflows/ci.yml — Basic build pipeline
6. README.md with project overview

SDKCONFIG overrides for firmware (set in sdkconfig.defaults):
CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y
CONFIG_PARTITION_TABLE_SINGLE_APP=n
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_ESP_CONSOLE_UART_NUM=0
CONFIG_FREERTOS_HZ=1000
CONFIG_ESP_DEFAULT_CPU_FREQ_240=y
CONFIG_ESP_TASK_WDT=y
CONFIG_ESP_TASK_WDT_TIMEOUT_S=1
CONFIG_COMPILER_OPTIMIZATION_SIZE=y

The firmware must compile with idf.py build. The Jetson package must pip install -e . successfully. Create placeholder implementations that return 0/null so everything compiles. Do NOT write actual logic yet — that comes in subsequent prompts.
```

---

## Prompt 1: Wire Protocol Implementation

**Dependencies:** Prompt 0
**Estimated effort:** 2-3 weeks
**Goal:** Complete COBS framing, CRC-16, message header parsing, and 28-type dispatch table for serial communication between Jetson and ESP32.

### Prompt

```
Implement the NEXUS serial wire protocol in /firmware/components/nexus_protocol/. This is the communication layer between the Jetson brain and ESP32 limbs.

FILES TO CREATE:
  cobs.h / cobs.c     — COBS encode/decode
  crc16.h / crc16.c    — CRC-16/CCITT-FALSE (polynomial 0x1021, init 0xFFFF)
  framing.h / framing.c — Frame TX/RX with ring buffers, 0x00 delimiters
  msg_handler.h / msg_handler.c — Message dispatch table for 28 message types

COBS ENCODING RULES:
- Scan input left to right. Count consecutive non-zero bytes.
- When a 0x00 is encountered or 254 non-zero bytes counted, emit the count byte followed by the non-zero bytes.
- Final run: append trailing 0x00 to input before final count byte.
- Decode: reverse the process. The output never contains the sentinel 0x00.

WIRE FRAME FORMAT:
  [0x00] [COBS-encoded: Header(10) + Payload(0-1024) + CRC-16(2)] [0x00]
  Max decoded frame: 1036 bytes. Max COBS encoded: 1051 bytes. Max wire frame: 1053 bytes.

10-BYTE MESSAGE HEADER (big-endian):
  Byte 0: msg_type (uint8)
  Byte 1: flags (uint8, bit 0=ACK_REQUIRED, bit 1=IS_ACK, bit 2=IS_ERROR, bit 3=URGENT, bit 7=NO_TIMESTAMP)
  Bytes 2-3: sequence_number (uint16)
  Bytes 4-7: timestamp_ms (uint32, uptime since boot)
  Bytes 8-9: payload_length (uint16)

28 MESSAGE TYPES:
  0x01 DEVICE_IDENTITY (N2J, JSON, telemetry)
  0x02 ROLE_ASSIGN (J2N, JSON, command)
  0x03 ROLE_ACK (N2J, JSON, command)
  0x04 SELFTEST_RESULT (N2J, JSON, command)
  0x05 HEARTBEAT (Both, none, telemetry)
  0x06 TELEMETRY (N2J, JSON, telemetry)
  0x07 COMMAND (J2N, JSON, command)
  0x08 COMMAND_ACK (N2J, JSON, command)
  0x09 REFLEX_DEPLOY (J2N, JSON, command)
  0x0A REFLEX_STATUS (N2J, JSON, telemetry)
  0x0B OBS_RECORD_START (J2N, JSON, command)
  0x0C OBS_RECORD_STOP (J2N, JSON, command)
  0x0D OBS_DUMP_HEADER (N2J, JSON, telemetry)
  0x0E OBS_DUMP_CHUNK (N2J, binary, telemetry)
  0x0F OBS_DUMP_END (N2J, JSON, telemetry)
  0x10 IO_RECONFIGURE (J2N, JSON, command)
  0x11 FIRMWARE_UPDATE_START (J2N, JSON, command)
  0x12 FIRMWARE_UPDATE_CHUNK (J2N, binary, command)
  0x13 FIRMWARE_UPDATE_END (J2N, JSON, command)
  0x14 FIRMWARE_UPDATE_RESULT (N2J, JSON, command)
  0x15 ERROR (N2J, JSON, safety)
  0x16 PING (Both, none, telemetry)
  0x17 PONG (Both, none, telemetry)
  0x18 BAUD_UPGRADE (J2N, JSON, command)
  0x19 CLOUD_CONTEXT_REQUEST (J2N, JSON, telemetry)
  0x1A CLOUD_RESULT (N2J, JSON, telemetry)
 0x1B AUTO_DETECT_RESULT (N2J, JSON, telemetry)
  0x1C SAFETY_EVENT (N2J, JSON, safety)

CRC-16/CCITT-FALSE PARAMETERS:
  Polynomial: 0x1021, Init: 0xFFFF, Final XOR: 0x0000, No reflection
  Check value for "123456789": 0x29B1
  Computed over Header + Payload (NOT the CRC itself). Transmitted MSB first.

RELIABILITY:
- Messages with criticality >= 1 must have ACK_REQUIRED flag. Retry up to 3 times with exponential backoff (200ms, 400ms, 800ms).
- 4-level priority queue: Safety (0) > Critical (1) > Normal (2) > Bulk (3).
- Heartbeat: node sends every 1000ms, timeout escalation: 1 miss=WARN, 2=DEGRADED, 3=FAILSAFE.

For each message type, create a handler function stub (void nexus_handle_DEVICE_IDENTITY(const uint8_t* payload, uint16_t len)) that logs receipt. Implement full COBS encode/decode with a loopback test that TX/RX every message type and verifies CRC. Include unit tests for COBS edge cases (256 consecutive zeros, empty payload, max-size payload).

UART CONFIGURATION:
- Default: 115200 baud at boot, negotiable up to 921600
- 8N1, hardware CTS/RTS flow control always enabled
- Use ESP-IDF uart driver with ESP_UART_FLAG_USE_TXD2 and RTS/CTS GPIOs

TEST: Write a loopback test (TX connected to RX via null modem adapter) that sends each message type, verifies COBS encode/decode roundtrip, CRC match, and sequence number validation. This should pass on real hardware.
```

---

## Prompt 2: Safety Layer

**Dependencies:** Prompts 0, 1
**Estimated effort:** 1-2 weeks
**Goal:** Implement kill switch ISR, hardware watchdog, heartbeat monitor, overcurrent detection, and boot-time safe-state enforcement.

### Prompt

```
Implement the four-tier safety system in /firmware/components/nexus_safety/. This is the most safety-critical component — every line must be correct.

FILES TO CREATE:
  kill_switch.h / kill_switch.c
  watchdog.h / watchdog.c
  heartbeat.h / heartbeat.c
  overcurrent.h / overcurrent.c
  safety_supervisor.h / safety_supervisor.c

BOOT SEQUENCE (TIMED — ALL OUTPUTS LOW AT T+0ms):
  T+0ms:   Power on. ALL GPIO outputs forced LOW (safe state). This is the FIRST thing in main().
  T+5ms:   Hardware watchdog feeding begins (MAX6818 kick pin, 200ms interval).
  T+10ms:  UART init at 115200 baud.
  T+20ms:   Send DEVICE_IDENTITY.
  T+50ms:   Send AUTO_DETECT_RESULT + SELFTEST_RESULT.
  T+300ms:  Apply role config, load cached reflexes.
  T+500ms:  Enter OPERATIONAL. Begin heartbeat, telemetry, reflex execution.
  If no Jetson after 30s: Enter IDLE, heartbeat only, retry ROLE_ASSIGN every 10s.

KILL SWITCH (Tier 1 + Tier 2):
- Physical NC mushroom-head switch wired in SERIES with +12V actuator power.
- Sense wire to GPIO configured INPUT with external 10K pull-up. Broken wire = safe state.
- GPIO interrupt on FALLING edge, priority ESP_INTR_FLAG_LEVEL1 (highest).
- ISR (must be in IRAM, declared IRAM_ATTR):
  1. Set volatile flag estop_triggered = true
  2. Set ALL actuator GPIOs to safe state IMMEDIATELY
  3. Disable all PWM (ledc_set_duty(channel, 0))
  4. Give semaphore from ISR (xSemaphoreGiveFromISR)
  5. RETURN. NO blocking, NO floating point, NO logging in ISR. Total ISR < 1ms.
- Deferred handler (safety_supervisor task): log event, set SAFE_STATE, suspend all tasks, notify Jetson.
- Test requirement: oscilloscope measurement from kill-switch contact break to actuator output change < 10ms (target < 1ms).

HARDWARE WATCHDOG (Tier 1):
- MAX6818 or TPS3823-33 supervisor IC.
- WDI pin connected to ESP32 GPIO. RST/WDO connected to ESP32 EN (reset) pin.
- Timeout: 1.0 seconds (not software-configurable).
- Kick pattern: alternating 0x55/0xAA (prevents stuck-at-0 and stuck-at-1 faults).
- Kick interval: every 200ms (5x per second, 4 kicks before timeout).
- On timeout: ESP32 resets. On reboot: boot counter in NVS, >5 resets in 10min = FAULT mode.

HEARTBEAT MONITOR (Tier 3):
- Jetson sends heartbeat every 100ms on dedicated UART.
- Format: "HB:<seq>:<timestamp_ms>:<xor_checksum>\n"
- States: NORMAL → DEGRADED (5 misses / 500ms) → SAFE_STATE (10 misses / 1000ms).
- DEGRADED: reflexes continue, PID holds last setpoint, AI disabled.
- SAFE_STATE: ALL actuators to safe state, all control loops suspended.
- Recovery: 3 consecutive good heartbeats → DEGRADED → (after Jetson sends RESUME) → NORMAL.
- Heartbeat check runs every 100ms in safety_supervisor task (priority: configMAX_PRIORITIES - 1).

OVERCURRENT DETECTION (Tier 2):
- INA219 current sensor on I2C. Alert pin to GPIO interrupt.
- Per-channel thresholds (solenoid: 4A, motor: 5A, relay: 2A, servo: 1A, general: 500mA).
- Detection window: 100ms sustained (after 200ms inrush allowance).
- Response: ISR immediately disables output, deferred handler logs and notifies Jetson.
- PTC polyfuse as hardware backup (1.5x hold, 2.0x trip).

SOFTWARE WATCHDOG (Tier 2/3):
- Monitor all application tasks. Each must call safety_watchdog_checkin(task_id) every 1.0s.
- Task monitoring: 1st timeout = log + warn. 2nd = suspend task + safe its actuators. 3rd = system reset.
- Safety supervisor itself: if it misses check-in, stop feeding hardware WDT → full reset in 1.0s.

SOLENOID TIMEOUT:
- max_on_time_ms: 5000 (configurable per-output). min_on_time_ms: 50. Cooldown: 1000ms.
- Rate limit: 5 cycles per 10-second window.
- Auto-deactivation with flag to prevent re-trigger without manual clear.

SAFETY STATE MACHINE:
typedef enum { SAFETY_MODE_NORMAL, SAFETY_MODE_DEGRADED, SAFETY_MODE_SAFE_STATE, SAFETY_MODE_FAULT } safety_mode_t;

Include comprehensive unit tests:
- Kill switch ISR timing (verify with GPIO toggle + timer measurement)
- Watchdog kick pattern verification
- Heartbeat state transitions (NORMAL→DEGRADED→SAFE_STATE→recovery)
- Overcurrent threshold detection
- Solenoid timeout enforcement
- Boot sequence timing (verify each milestone with timestamps)
```

---

## Prompt 3: I/O Abstraction Layer

**Dependencies:** Prompts 0, 1
**Estimated effort:** 3-4 weeks
**Goal:** Implement pin configuration from JSON, driver vtable interface, and 5 reference hardware drivers.

### Prompt

```
Implement the I/O abstraction layer in /firmware/components/nexus_io/. This decouples pin configurations from compiled firmware — pins are defined by JSON sent from the Jetson at boot.

FILES TO CREATE:
  io_abstraction.h / io_abstraction.c
  pin_config.h / pin_config.c
  drivers/digital_output.c
  drivers/pwm_output.c
  drivers/adc_input.c
  drivers/i2c_compass.c    (HMC5883L)
  drivers/uart_sensor.c

DRIVER VTABLE INTERFACE (from io_driver_interface.h):
typedef struct {
  esp_err_t (*init)(const io_pin_config_t* config);
  esp_err_t (*read)(void* buffer, size_t len);
  esp_err_t (*write)(const void* data, size_t len);
  esp_err_t (*configure)(const char* key, const char* value);
  esp_err_t (*selftest)(io_selftest_result_t* result);
  esp_err_t (*deinit)(void);
  const io_driver_info_t* (*get_info)(void);
} io_driver_vtable_t;

PIN CONFIGURATION JSON FORMAT (received via ROLE_ASSIGN):
{
  "role": "autopilot_controller",
  "pins": {
    "rudder_pwm": {"gpio": 4, "mode": "pwm", "freq_hz": 50, "safe_value": 1500},
    "throttle_relay": {"gpio": 5, "mode": "output", "safe_value": 0},
    "compass_sda": {"gpio": 21, "mode": "i2c", "bus": 0, "addr": "0x1E"},
    "kill_switch": {"gpio": 22, "mode": "input", "pull": "up", "interrupt": "falling"},
    "wind_speed": {"gpio": 6, "mode": "adc", "channel": 3, "atten_db": 11}
  },
  "telemetry_interval_ms": 100
}

PIN MODES: input, output, pwm, adc, i2c, uart, spi
Each mode has specific constraints:
- INPUT: pull (up/down/none), interrupt (rising/falling/both/none), debounce_ms
- OUTPUT: initial_value (must equal safe_value at boot)
- PWM: freq_hz (1-40000), duty_resolution_bits (1-20), safe_duty
- ADC: channel (0-7), attenuation_db (0/3/6/11), samples_per_read (1-4)
- I2C: bus (0-1), address (hex string "0x1E"), clock_khz (100-400), sda_gpio, scl_gpio
- UART: baud_rate, tx_gpio, rx_gpio, data_bits, parity, stop_bits

PIN CONFLICT DETECTION:
- No GPIO can be claimed by two different functions simultaneously.
- Certain pins have hardware-mux constraints (e.g., strapping pins, USB pins).
- I2C SDA/SCL pairs are validated together.
- If conflict detected, reject pin config and return PIN_ALREADY_IN_USE error.

5 REFERENCE DRIVERS:

1. DIGITAL OUTPUT:
   - Simple GPIO on/off. Must track state. No special hardware.

2. PWM OUTPUT:
   - Use ESP-IDF LEDC peripheral. Support freq 1-40000Hz, duty 0-1023 (10-bit).
   - Safe duty = 0 (output LOW / off).

3. ADC INPUT:
   - ESP32 SAR ADC, 12-bit, configurable attenuation.
   - Multiple samples per read (hardware averaging).
   - Return float32 voltage (actual voltage, not raw counts).

4. I2C COMPASS (HMC5883L):
   - I2C address 0x1E. 100kHz default (400kHz available after validation).
   - Registers: Config A/B (0x00/0x01), Mode register (0x02), Data output X/Y/Z (0x03-0x05).
   - Self-test: write 0x71 to Config B, read Status A (0x09), check bit 7 (self-test failed if 0).
   - Read 6 bytes (X,Z,Y as 16-bit big-endian). Convert to heading: heading_rad = atan2(Y, X), heading_deg = heading_rad * 180/PI.
   - ±180° wraparound handling.

5. UART SENSOR:
   - Configurable baud rate (9600-921600). DMA-based RX.
   - Line protocol parsing (detect frame delimiters, extract payload).
   - Buffer with overflow handling (ring buffer).

Include a self-test function that:
- Iterates all configured pins
- For outputs: sets to safe value, reads back, verifies
- For inputs: reads value, checks within expected range
- For I2C: scans bus, verifies device responds at configured address
- For ADC: reads with known voltage divider, checks within tolerance
- Returns io_selftest_result_t with per-pin pass/fail and overall status
```

---

## Prompt 4: Reflex Bytecode Virtual Machine

**Dependencies:** Prompts 0, 1
**Estimated effort:** 3-4 weeks
**Goal:** Implement a 32-opcode stack machine bytecode VM that executes AI-generated control logic at 1kHz with deterministic timing.

### Prompt

```
Implement the reflex bytecode VM in /firmware/components/nexus_vm/. This is the heart of the NEXUS system — it executes AI-generated control logic on the ESP32.

FILES TO CREATE:
  vm.h / vm.c           — VM execution engine (fetch-decode-execute loop)
  opcodes.h / opcodes.c   — All 32 opcode implementations
  compiler.h / compiler.c — JSON-to-bytecode compiler
  safety.h / safety.c     — VM safety invariants

INSTRUCTION SET ARCHITECTURE (32 opcodes, 0x00-0x1F):
Stack machine. All values on stack are uint32_t. Float interpretation via memcpy.
Every instruction is exactly 8 bytes: [opcode:1][flags:1][operand1:2][operand2:4].

OPCODES:
  Stack:    0x00=NOP, 0x01=PUSH_I8, 0x02=PUSH_I16, 0x03=PUSH_F32, 0x04=POP, 0x05=DUP, 0x06=SWAP, 0x07=ROT
  Arithmetic: 0x08=ADD_F, 0x09=SUB_F, 0x0A=MUL_F, 0x0B=DIV_F(div by zero returns 0.0), 0x0C=NEG_F(bit flip sign), 0x0D=ABS_F(clear sign bit), 0x0E=MIN_F, 0x0F=MAX_F, 0x10=CLAMP_F
  Comparison: 0x11=EQ_F, 0x12=LT_F, 0x13=GT_F, 0x14=LTE_F, 0x15=GTE_F (all push 0 or 1)
  Logic:    0x16=AND_B, 0x17=OR_B, 0x18=XOR_B, 0x19=NOT_B (bitwise on uint32)
  I/O:      0x1A=READ_PIN, 0x1B=WRITE_PIN, 0x1C=READ_TIMER_MS
  Control:  0x1D=JUMP, 0x1E=JUMP_IF_FALSE, 0x1F=JUMP_IF_TRUE

VARIABLE ACCESS MECHANISM (no dedicated LOAD/STORE opcodes):
- READ_PIN with operand1 >= 64: reads variable at index (operand1 - 64). Range 0-255.
- WRITE_PIN with operand1 >= 64: writes variable at index (operand1 - 64).
- Sensor registers: operand1 0-63 (read-only, populated by firmware before each tick).
- Actuator registers: operand1 0-63 (write-only, drained by firmware after each tick).
- State variable convention: VAR_0 = variable at READ_PIN/WRITE_PIN 64.

SYSCALL MECHANISM (NOP with flags bit 7 set):
- opcode=0x00, flags=0x80:
  operand1=0x01: HALT (stop execution for this tick)
  operand1=0x02: PID_COMPUTE (operand2.lo16 = pid_idx 0-7). Stack before: [..., setpoint, input]. Stack after: [..., output].
  operand1=0x03: RECORD_SNAPSHOT (operand2.lo16 = snapshot_id 0-15)
  operand1=0x04: EMIT_EVENT (operand2.lo16 = event_id, operand2.hi16 = event_data)

CALL/RET mechanism:
- JUMP with flags bit 3 set (IS_CALL): push return address to call stack, then jump.
- JUMP to address 0xFFFFFFFF: pop call stack, restore PC (this is RET).
- Call stack: 16 entries max. CSP++ on call, CSP-- on ret. Halt if overflow/underflow.

FLAGS BYTE BIT FIELD:
  Bit 0: HAS_IMMEDIATE, Bit 1: IS_FLOAT, Bit 2: EXTENDED_CLAMP, Bit 3: IS_CALL, Bits 4-6: RESERVED, Bit 7: SYSCALL

PID CONTROLLER (8 instances, 32 bytes each):
  Fields: Kp(float32), Ki(float32), Kd(float32), integral(float32), prev_error(float32), integral_limit(float32), output_min(float32), output_max(float32)
  Total: 8 * 32 = 256 bytes.
  Anti-windup: clamp integral to ±integral_limit.
  Output clamp: clamp output to [output_min, output_max].

MEMORY MODEL (total ~3KB, static allocation in SRAM):
  Data stack:    256 x uint32 = 1 KB
  Call stack:    16 x {uint32_t return_addr, uint16_t frame_pointer} = 256 B
  Variables:     256 x float32 = 1 KB
  Sensor regs:   64 x float32 = 256 B
  Actuator regs: 64 x float32 = 256 B
  PID state:     8 x 32 bytes = 256 B
  Snapshot buf:  16 x 128 bytes = 2 KB
  Event ring:    32 x 8 bytes = 256 B

SAFETY INVARIANTS (enforced EVERY tick):
  1. Stack bounds: SP < 256 on push, SP > 0 on pop. Violation = HALT + safe outputs.
  2. Cycle budget: max 10,000 cycles per tick. Exceeded = HALT + safe outputs.
  3. Actuator clamping: after VM execution, clamp ALL actuator registers to configured min/max.
  4. Jump target: validated at compile time (within bytecode bounds, 8-byte aligned).
  5. Division: divide by zero returns 0.0 (not NaN/Inf).

VM EXECUTION LOOP:
```
void vm_tick(vm_t* vm) {
    vm->cycle_count = 0;
    vm->halted = false;
    while (!vm->halted && vm->cycle_count < MAX_CYCLES) {
        // Fetch: read 8 bytes at PC
        uint8_t opcode = vm->bytecode[vm->pc];
        uint8_t flags = vm->bytecode[vm->pc + 1];
        uint16_t op1 = *(uint16_t*)&vm->bytecode[vm->pc + 2];
        uint32_t op2 = *(uint32_t*)&vm->bytecode[vm->pc + 4];
        // Syscall check
        if (opcode == 0x00 && (flags & 0x80)) { handle_syscall(vm, flags, op1, op2); vm->pc += 8; continue; }
        // Decode + Execute (switch on opcode)
        vm->pc += 8;
        vm->cycle_count += opcode_cycles[opcode]; // lookup table
    }
    if (vm->halted) { clamp_all_actuators(vm); }
}
```

JSON REFLEX FORMAT (input to compiler):
{
  "name": "heading_hold_pid",
  "version": "1.0",
  "priority": 10,
  "tick_rate_hz": 10,
  "variables": {"integral": {"type": "float32", "initial": 0.0}},
  "sensors": {"heading": {"pin": 0, "type": "float32"}},
  "actuators": {"rudder": {"pin": 0, "min": -45.0, "max": 45.0, "safe": 0.0}},
  "pid_controllers": {"heading_pid": {"kp": 1.2, "ki": 0.05, "kd": 0.3, "integral_limit": 1500.0}},
  "code": "READ_PIN 0; READ_PIN 1; PID_COMPUTE 0; CLAMP_F -45.0 45.0; WRITE_PIN 0"
}

COMPILER (JSON to bytecode):
- Parse JSON reflex schema
- Allocate variable indices, validate sensor/actuator pin references
- Parse "code" string into tokens: READ_PIN, WRITE_PIN, PUSH_I8/I16/F32, ADD_F, etc.
- For each token: resolve operand, generate 8-byte instruction
- CALL: set flags bit 3 on JUMP instruction
- HALT: append NOP with flags=0x80 as last instruction
- Validate: all jump targets within bounds and 8-byte aligned, stack depth analysis
- Output: raw bytecode buffer ready for REFLEX_DEPLOY

TESTS:
- Every opcode: push values, verify stack state
- Stack overflow/underflow detection
- Cycle budget enforcement (inject infinite loop, verify HALT at 10000 cycles)
- PID computation: known inputs → verify outputs against Python numpy reference
- JSON compilation: compile heading_hold_pid, verify bytecode, load into VM, step through
- Actuator clamping: set output beyond limits, verify clamped after execution
- Division by zero: verify returns 0.0, no crash
```

---

## Prompt 5: Main Firmware Integration

**Dependencies:** Prompts 0, 1, 2, 3, 4
**Estimated effort:** 1-2 weeks
**Goal:** Wire boot sequence, role assignment, observation buffer, OTA updates, and reflex deployment into the main application.

### Prompt

```
Wire all components together into the main ESP32 firmware application at /firmware/main/main.c. This is the integration layer that makes the universal limb work end-to-end.

MAIN.C STRUCTURE:
void app_main() {
  // T+0ms: SAFE STATE (all outputs LOW — this is FIRST)
  gpio_set_level_safe_all();
  
  // T+5ms: Hardware watchdog
  watchdog_init(WDT_KICK_PIN, 200);
  
  // T+10ms: UART init
  uart_init(UART_NUM_0, 115200);
  
  // T+20ms: Announce identity
  nexus_send_DEVICE_IDENTITY();  // MAC, chip ID, firmware version, capabilities
  
  // T+30ms: Hardware auto-detect
  nexus_send_AUTO_DETECT_RESULT();  // I2C scan, ADC probe
  
  // T+50ms: Self-test results
  nexus_send_SELFTEST_RESULT();  // Per-pin continuity, flash CRC
  
  // T+50-300ms: Wait for ROLE_ASSIGN
  role_config_t* role = wait_for_role_assignment(30000);
  if (!role) { enter_idle_mode(); }
  
  // T+300ms: Apply role configuration
  io_apply_pin_config(role);
  
  // T+500ms: OPERATIONAL
  start_heartbeat_monitor();
  start_telemetry(role->telemetry_interval_ms);
  
  // Main loop
  while (1) {
    safety_supervisor_tick();  // 10ms period
    if (safety_mode == NORMAL) {
      vm_tick_all_loaded_reflexes();  // At configured tick rate
    }
    telemetry_tick();             // At configured interval
  }
}

ROLE ASSIGNMENT PROTOCOL:
- Jetson sends ROLE_ASSIGN (msg 0x02) as JSON with pins, telemetry interval, and reflex names.
- Parse JSON, validate all pin configs against hardware capabilities.
- Store role config in NVS (survives reboot).
- Respond with ROLE_ACK (msg 0x03): accepted=true/false with rejection reason.
- On reboot: load cached role from NVS if no Jetson within 30s.

OBSERVATION BUFFER (PSRAM ring buffer):
- Size: configurable, default 5MB in PSRAM.
- Format: 32-byte compressed frames (frame_type, sequence_id, timestamp, channel_mask, 14 channels of int16 data, flags, CRC-32).
- At 100Hz with 16 channels: 31 minutes of recording.
- Recording control via OBS_RECORD_START/STOP messages.
- Dump via OBS_DUMP_HEADER + OBS_DUMP_CHUNK + OBS_DUMP_END.
- Buffer is volatile (PSRAM): power loss = acceptable data loss.

OTA FIRMWARE UPDATE:
- FIRMWARE_UPDATE_START: receives size, chunk_count, version, SHA-256 hash.
- FIRMWARE_UPDATE_CHUNK: 512 bytes per chunk, written to ota_1 partition.
- FIRMWARE_UPDATE_END: verify SHA-26, write boot block pointing to ota_1.
- Reboot: bootloader validates ota_1 CRC. If valid → boot from ota_1. If invalid → rollback to ota_0.
- If both fail → boot from factory partition (never OTA-modified).
- Factory partition contains minimal safe-mode firmware (identity + heartbeat + ROLE_ASSIGN wait).

BAUD RATE NEGOTIATION:
- After role assignment, Jetson sends BAUD_UPGRADE (0x18) with target_baud.
- Both sides switch simultaneously. Jetson sends PING at new baud to verify.
- If no PONG within 500ms: fall back to previous baud.
- Supported rates: 921600 (10m cable), 460800 (50m), 230400 (75m), 115200 (100m).

LITTLEFS PARTITION (reflex storage):
- Mount LittleFS on the "reflexes" partition (2MB).
- Store compiled bytecode files (one per reflex name).
- Power-loss safe (journaling). Either old or new version survives.
- Load all reflexes at boot after role assignment.
- Deploy new reflex: receive via REFLEX_DEPLOY, compile JSON→bytecode, store to LittleFS, hot-load into VM.

TESTS:
- Full boot sequence with oscilloscope on serial TX line (verify timing milestones)
- Role assignment: send ROLE_ASSIGN via serial tool, verify ROLE_ACK, verify pins configured
- OTA update: send fake firmware via serial, verify SHA-256 check, verify boot from ota_1
- OTA rollback: send corrupt firmware, verify rollback to ota_0, then corrupt ota_0 → verify factory boot
- Observation: record for 10 seconds at 100Hz, dump, verify frame count and CRC integrity
- Reflex deploy: compile heading_hold_pid, deploy, verify execution on VM
- Hot-swap: reset ESP32, verify it reloads cached role and resumes operation
```

---

## Prompt 6: Jetson Serial Bridge + Node Manager

**Dependencies:** Prompts 0, 1
**Estimated effort:** 2-3 weeks
**Goal:** Python serial port management, COBS encoding/decode matching firmware, node discovery, and role assignment.

### Prompt

```
Implement the Jetson serial bridge and node manager at /jetson/nexus_cognitive/serial_bridge.py and /jetson/nexus_cognitive/node_manager.py.

SERIAL_BRIDGE.PY:
- Manage multiple serial ports (one per ESP32 node) using pyserial.
- COBS encode/decode matching the firmware implementation exactly:
  - Polynomial 0x1021, init 0xFFFF, final XOR 0x0000
  - Frame format: [0x00][COBS(payload)][0x00]
  - Max payload: 1024 bytes
- Message header encode/decode (10 bytes, big-endian, matching firmware spec):
  msg_type(1), flags(1), sequence_number(2), timestamp_ms(4), payload_length(2)
- Async TX/RX using asyncio + pyserial-asyncio.
- Priority queue: Safety > Critical > Normal > Bulk.
- Retry logic for ACK-required messages (3 retries, exponential backoff 200/400/800ms).
- Baud negotiation: start at 115200, upgrade to 921600 after role assignment.
- Node registration: when DEVICE_IDENTITY received, register node with MAC address, chip type, firmware version.

NODE_MANAGER.PY:
- Maintain node registry: {mac_address: NodeInfo} for all discovered nodes.
- Send ROLE_ASSIGN to nodes based on configuration database (JSON file or SQLite).
- Handle ROLE_ACK: log acceptance or rejection, retry on rejection.
- Deploy reflexes: compile JSON reflex definition to bytecode, send via REFLEX_DEPLOY.
- Monitor node health: track heartbeat timestamps, detect DEGRADED/SAFE_STATE transitions.
- Hot-swap detection: when a node disappears and reappears with different MAC, assign same role.

CONFIGURATION FORMAT (roles.json):
{
  "nodes": {
    "autopilot_esp32": {
      "serial_port": "/dev/ttyUSB0",
      "mac_filter": null,  // match any ESP32 on this port
      "role": {
        "role_name": "autopilot_controller",
        "pins": { ... },  // Full pin config
        "reflexes": ["heading_hold_pid", "throttle_governor"]
      }
    }
  }
}

Include unit tests:
- COBS encode/decode round-trip for all message types.
- Header encode/decode big-endian verification.
- Mock serial device test (TX/RX loopback using pty pair).
- Node discovery simulation.
- Role assignment flow simulation.
- Heartbeat timeout detection.
```

---

## Prompt 7: Jetson Cognitive Services

**Dependencies:** Prompts 0, 6
**Estimated effort:** 3-4 weeks
**Goal:** gRPC services, MQTT bridge, module lifecycle, LLM chat interface.

### Prompt

```
Implement the remaining Jetson cognitive services in /jetson/nexus_cognitive/. Generate gRPC stubs from the proto file and implement core modules.

1. GENERATE GRPC STUBS:
   cd /jetson/nexus_cognitive
   python -m grpc_tools.protoc -I./proto --python_out=./proto ./proto/cluster_api.proto

2. MQTT BRIDGE (/jetson/nexus_cognitive/mqtt_bridge.py):
   - Use paho-mqtt (paho.mqtt.client).
   - 13 topics with QoS and retain settings:
     nexus/telemetry/{node_id} (QoS 0, no retain)
     nexus/status/{node_id} (QoS 1, retain)
     nexus/safety/{node_id} (QoS 2, no retain)
     nexus/autonomy/{subsystem}/level (QoS 1, retain)
     nexus/autonomy/{subsystem}/override (QoS 2, retain)
     nexus/learning/session/{id}/control (QoS 1, no retain)
     nexus/reflex/{reflex_id}/deploy (QoS 1, no retain)
   - Bridge serial events to MQTT (node sends SAFETY_EVENT → publish to MQTT).
   - Bridge MQTT commands to serial (subscribe to autonomy override → send COMMAND to node).

3. MODULE ABC (/jetson/nexus_cognitive/nexus_module.py):
   - Abstract base class with: start(), stop(), health_check(), resource_budget(), hot_reload(config).
   - ThrottleMonitor concrete example: monitors CPU/GPU temp, sheds services at 85C.
   - Module registry: track all running modules, enforce resource budgets.

4. REFLEX ORCHESTRATOR (/jetson/nexus_cognitive/reflex_orchestrator.py):
   - Compile JSON reflex definitions to bytecode (Python bytecode compiler matching firmware compiler).
   - Deploy via serial_bridge: send REFLEX_DEPLOY messages.
   - List active reflexes across all nodes.
   - Hot-reload: update reflex parameters without restart.

5. CHAT INTERFACE (/jetson/nexus_cognitive/chat_interface.py):
   - Connect to local LLM via llama-cpp-python (Qwen2.5-Coder-7B-Instruct, Q4_K_M quantization).
   - Fallback to cloud LLM (OpenAI or Anthropic API) for complex requests.
   - Intent classification: parse user natural language, route to correct handler:
     "set rudder to 15 degrees" → COMMAND
     "create a reflex that..." → REFLEX_ORCHESTRATOR
     "what's the current heading?" → TELEMETRY_QUERY
     "show me the trust scores" → AUTONOMY_STATUS
   - Maintain conversation history per session.
   - Format reflex proposals as natural language (NOT code) for human approval.

6. LEARNING SERVICE (/jetson/nexus_cognitive/learning_pipeline.py):
   - Observation session management: start/stop/pause/resume.
   - Store observations as Parquet files with Snappy compression.
   - Expose gRPC LearningService methods.

7. SAFETY MANAGER (/jetson/nexus_cognitive/safety_manager.py):
   - Compute trust scores using the formula:
     T(t+1) = T(t) + alpha_gain * (1 - T(t))  [good evaluation]
     T(t+1) = T(t) - alpha_loss * T(t)        [bad evaluation]
     alpha_gain = 0.002, alpha_loss = 0.05
   - Manage per-subsystem autonomy levels (0-5 INCREMENTS scale).
   - Persist trust scores to SQLite database.
   - Trigger autonomy level transitions based on thresholds (L2 at T>=0.5, L3 at T>=0.7, L5 at T>=0.95).

Include integration tests:
- gRPC service instantiation and method calls.
- MQTT publish/subscribe with test broker.
- Chat interface with mocked LLM responses.
- Trust score computation over 100 simulated evaluations.
- Node manager with mock serial bridge.
```

---

## Prompt 8: Trust Score + Autonomy Manager

**Dependencies:** Prompts 0, 7
**Estimated effort:** 1-2 weeks
**Goal:** Mathematical trust scoring, per-subsystem autonomy levels, override handling, and persistent state management.

### Prompt

```
Implement the trust score algorithm and INCREMENTS autonomy framework at /jetson/nexus_cognitive/autonomy_manager.py.

TRUST SCORE FORMULA:
  T(t+1) = T(t) + alpha_gain * (1 - T(t))       if evaluation is GOOD
  T(t+1) = T(t) - alpha_loss * T(t)              if evaluation is BAD
  T(t+1) = T(t)                                  if no evaluation

  alpha_gain = 0.002 (configurable per-subsystem)
  alpha_loss = 0.05 (configurable per-subsystem)
  T range: [0.0, 1.0]
  Initial trust: 0.0

AUTONOMY LEVELS (INCREMENTS scale, per-subsystem):
  0: MANUAL     — Human has full control, system only monitors/records.
  1: ASSIST     — System suggests actions, human approves every action.
  2: SEMI-AUTO — System executes approved reflexes, human can override anytime.
  3: CONDITIONAL — System operates autonomously in defined conditions, human monitors.
  4: HIGH       — System operates autonomously in most conditions, human available.
  5: FULL       — System fully autonomous in all conditions, human optional.

LEVEL TRANSITION THRESHOLDS (configurable):
  0→1: Manual activation by operator (not trust-based).
  1→2: T >= 0.5 AND no bad evaluations in last 100 evaluations.
  2→3: T >= 0.7 AND minimum 7 days since last override.
  3→4: T >= 0.8 AND minimum 30 days since last override.
  4→5: T >= 0.95 AND minimum 90 days since last override.

Any bad evaluation immediately drops to next lower level (2→1, 3→2, etc.).

EVALUATION SOURCES:
- A/B test results (comparison metrics vs human baseline)
- Human explicit approval/rejection of proposed actions
- Safety system events (overcurrent, sensor stale, heartbeat loss)
- Manual override events (human took control back)

OVERRIDE HANDLING:
- When human sends override command (MQTT QoS 2): immediately drop to SEMI-AUTO for that subsystem.
- Log override event with timestamp, reason (if provided), current trust score, current level.
- Start override cooldown timer (7 days before re-promotion possible).

PERSISTENCE:
  SQLite schema:
  CREATE TABLE subsystem_trust (
    subsystem TEXT PRIMARY KEY,
    trust_score REAL NOT NULL DEFAULT 0.0,
    autonomy_level INTEGER NOT NULL DEFAULT 0,
    alpha_gain REAL NOT NULL DEFAULT 0.002,
    alpha_loss REAL NOT NULL DEFAULT 0.05,
    total_good_evaluations INTEGER NOT NULL DEFAULT 0,
    total_bad_evaluations INTEGER NOT NULL DEFAULT 0,
    last_evaluation_at TIMESTAMP,
    last_override_at TIMESTAMP,
    last_level_change_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
  CREATE TABLE evaluation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem TEXT NOT NULL,
    evaluation_type TEXT NOT NULL,  -- 'ab_test', 'human_approval', 'safety_event', 'override'
    is_good INTEGER NOT NULL,          -- 1=good, 0=bad
    trust_before REAL,
    trust_after REAL,
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subsystem) REFERENCES subsystem_trust(subsystem)
  );

Include unit tests:
- Trust score computation: 50 consecutive good evaluations from T=0.0 should reach T~0.095.
- 2 consecutive bad evaluations from T=0.9 should drop to T~0.776.
- Level transitions: simulate 120 days of good evaluations, verify level progression.
- Override handling: verify immediate level drop and cooldown enforcement.
- Persistence: write/read from SQLite, verify data integrity.
- Edge cases: evaluation at T=0.0 (bad), T=1.0 (good), very rapid evaluations.
```

---

## Prompt 9: Learning Pipeline

**Dependencies:** Prompts 0, 7
**Estimated effort:** 4-6 weeks
**Goal:** Five pattern discovery algorithms, A/B testing framework, and reflex synthesis from observation data.

### Prompt

```
Implement the learning pipeline at /jetson/nexus_cognitive/learning_pipeline.py. This is the system's ability to learn from observing human behavior.

OBSERVATION DATA MODEL (UnifiedObservation, 72 fields):
Store observations as Apache Parquet files with these key fields:
- Navigation: gps_latitude, gps_longitude, gps_speed_m_s, gps_heading_deg (double)
- Attitude: imu_roll_deg, imu_pitch_deg, imu_yaw_deg, imu_accel_x/y/z_m_s2 (float32)
- Environment: wind_speed_m_s, air_temp_c, water_temp_c, barometric_hpa (float32)
- Propulsion: throttle_pct, rudder_angle_deg, engine_rpm, fuel_flow_L_h (float32)
- Auxiliary: bow_thruster_pct, bilge_pump_active (bool)
- Perception: lidar_obstacle_dist_m, radar_contacts_count (int16)
- System: cpu_usage_pct, core_temp_c, autonomy_level, trust_score (float32)

OBSERVATIONSESSION:
  - session_id (UUIDv4), vessel_id, tags, status (recording/paused/closed)
  - record(observation): append to in-memory Arrow table, flush to Parquet every 1s or 10000 rows
  - close(): finalize Parquet, write metadata, compute column statistics, move to hot storage
  - export(format, start_time, end_time, columns): export subset as Parquet/CSV/JSONL

PATTERN DISCOVERY ALGORITHMS (run after session close):

1. CROSS-CORRELATION SCANNER:
   - Scan all C(72,2)=2556 pairs at lags -60s to +60s at 100ms resolution.
   - scipy.signal.correlate with mode='same'.
   - Pearson r with Bonferroni correction.
   - Filter: |r| >= 0.6 AND p_corrected < 0.05.
   - Runtime: ~8 seconds per 1-hour session on Jetson Orin.

2. BAYESIAN ONLINE CHANGE-POINT DETECTION (BOCPD, Adams & MacKay 2007):
   - Normal-Inverse-Gamma conjugate priors.
   - Hazard lambda = 0.01 (expected ~100 obs between changes).
   - Report changes with posterior probability > 0.5 and run length > 100.
   - Process all continuous sensor columns in parallel (4 workers).

3. BEHAVIORAL CLUSTERING (HDBSCAN):
   - 10-second non-overlapping windows.
   - Extract 40 features per window (8 sensors x 5 stats: mean, std, min, max, spectral centroid).
   - RobustScaler normalization, PCA to 5 components.
   - HDBSCAN(metric='euclidean', min_cluster_size=10, min_samples=3).
   - Classify temporal pattern via autocorrelation: < 0.3=transient, > 0.7=stationary, else=periodic.

4. TEMPORAL PATTERN MINING:
   - Event language grammar: "variable comparator threshold AND variable comparator threshold".
   - Supported comparators: >, >=, <, <=, ==, !=, CHANGES_BY, CROSSES.
   - For each event occurrence: extract actuator response sequence over [-10s, +30s].
   - Cluster response sequences using DTW (Dynamic Time Warping) with Sakoe-Chiba band.
   - Report rules with consistency > 0.6 across > 5 occurrences.

5. BAYESIAN REWARD INFERENCE:
   - 6 reward features: speed_comfort, heading_accuracy, fuel_efficiency, smoothness, safety_margin, wind_compensation.
   - Compute feature matrix T x 6 for each session.
   - MAP estimation with Normal-Inverse-Gamma priors.
   - Prior seeded by human narration ("comfort matters most" → weight comfort higher).

A/B TESTING FRAMEWORK:
  - test_id, subsystem, baseline_recording, treatment_recording
  - 7 metrics: heading RMSE, comfort score, fuel efficiency, safety margin, smoothness, override frequency, response latency.
  - Statistical significance: paired t-test with Bonferroni correction (7 metrics → p < 0.007).
  - Decision: accept if treatment is not statistically worse on any safety metric AND significantly better on at least one efficiency metric.

REFLEX SYNTHESIS:
  Given a discovered pattern (from temporal rules or cross-correlation):
  1. Generate JSON reflex definition (states, transitions, triggers, actions).
  2. Compile to bytecode.
  3. Send to A/B test framework.
  4. If accepted: deploy to production via REFLEX_DEPLOY.

Include unit tests with synthetic observation data:
- Cross-correlation: inject known sinusoidal signals with phase shift, verify detection.
- BOCPD: inject step-function changes, verify change-point detection.
- HDBSCAN: create 3 distinct behavior types, verify clustering.
- Temporal mining: create event-response pairs, verify rule discovery.
- A/B testing: create synthetic baseline and treatment data, verify statistical decision.
```

---

## Prompt 10: A/B Testing Framework

**Dependencies:** Prompts 0, 9
**Estimated effort:** 2-3 weeks
**Goal:** Production-grade A/B testing framework for validating proposed reflexes against human baselines.

(This is included in Prompt 9 above as part of the learning pipeline. If building standalone, extract it into /jetson/nexus_cognitive/ab_testing.py.)

---

## Prompt 11: Cloud Code Generation Pipeline

**Dependencies:** Prompts 0, 7
**Estimated effort:** 3-4 weeks
**Goal:** Intent-to-code pipeline with separate LLM validation, MISRA-C rule checking, and simulation.

### Prompt

```
Implement the cloud code generation pipeline at /jetson/nexus_cognitive/code_generation.py.

6-STAGE PIPELINE:

1. INTENT CAPTURE:
   - Input: natural language text from chat interface ("When wind exceeds 25 knots, reduce throttle to 40% and angle trim tabs down 5 degrees").
   - Output: structured intent record {raw_text, domain, subsystem, priority, context}.

2. INTENT CLASSIFICATION:
   - Route to correct handler: reflex_generation, config_change, status_query, safety_override.
   - Use Phi-3-mini-4K (local, 40+ tok/s) for fast classification.
   - If confidence < 0.7: escalate to human for clarification.

3. CODE GENERATION:
   - Primary: Qwen2.5-Coder-7B-Instruct (local, Q4_K_M, ~4GB VRAM, 12 tok/s).
   - Fallback: cloud LLM (GPT-4o or Claude, via API) for complex requests.
   - Output: JSON reflex definition (80%), C firmware code for performance-critical (15%), Python utility (5%).
   - Temperature: 0.2 for reflex generation (deterministic output).
   - Max tokens: 2048.
   - System prompt includes: safety rules summary, available pins/sensors, actuator limits, timing constraints.

4. SAFETY VALIDATION (CRITICAL — MUST use different LLM):
   - Send generated code to a DIFFERENT LLM call than the generation call.
   - Validation prompt: "You are a safety auditor for industrial robotics code. Review this code for:
     a) Actuator output clamping violations (values exceeding configured min/max)
     b) Missing kill-switch check or safe-state enforcement
     c) Rate limiting violations
     d) Deadlock potential in state machine
     e) Integer overflow or division by zero
     f) Non-deterministic timing (sleep, random, heap allocation in control path)
     Score each 0-10. Reject if any safety score < 7."
   - If rejected: send back to step 3 with rejection reason. Max 3 retries.
   - If accepted: proceed to simulation.

5. SIMULATION:
   - Load recorded observation data from a relevant session.
   - Run the proposed reflex against the recorded data (replay sensor inputs through the reflex, verify outputs are within safe bounds).
   - Check: no actuator exceeds min/max. No reflex cycle exceeds 10000 VM cycles.
   - If simulation passes: proceed to approval. If fails: reject with diagnostic info.

6. HUMAN APPROVAL:
   - Present the reflex proposal as NATURAL LANGUAGE (not code):
     "I noticed that when wind exceeds 25 knots, you tend to reduce throttle to ~42% and angle trim tabs to ~5 degrees down. 
      Shall I automate this behavior? The proposed rule would trigger when wind_speed > 25 and activate 
      throttle_target=40%, trim_angle_target=-5.0."
   - Options presented: APPROVE, REJECT, MODIFY, TEST_LONGER.
   - On APPROVE: deploy via REFLEX_DEPLOY.

MISRA-C RULES (applied during validation):
  - No dynamic memory allocation in control paths.
  - All loops must have bounded iteration count.
  - No recursion deeper than call stack depth.
  - All outputs must be explicitly initialized.
  - No floating-point equality comparisons (use tolerance).
  - All switch/case statements must have default.

Include tests:
- Generate reflex from known intent, verify JSON structure.
- Validation rejection: inject unsafe code (unclamped output), verify rejection.
- Simulation: replay recorded data through compiled reflex, verify outputs.
- End-to-end: intent text → classification → generation → validation → simulation → approval flow.
```

---

## Prompt 12: Testing & Integration

**Dependencies:** All previous prompts
**Estimated effort:** 4-6 weeks
**Goal:** Comprehensive test suite covering unit, integration, and hardware-in-loop testing.

### Prompt

```
Create comprehensive test suites for the NEXUS platform. Tests should be automated and runnable in CI.

FIRMWARE UNIT TESTS (/firmware/tests/):
Framework: Unity (CMock + Ceedling for ESP-IDF).

Test categories:
1. Wire Protocol:
   - COBS encode/decode round-trip for every payload size 0-1024 bytes.
   - CRC-16 computation against known test vectors.
   - Header encode/decode (big-endian verification).
   - Sequence number wraparound handling.
   - Frame reassembly after fragmentation.

2. VM:
   - Every opcode: push specific values, verify stack state after execution.
   - Stack overflow (256 push without pop) → HALT + safe outputs.
   - Stack underflow (pop on empty stack) → HALT + safe outputs.
   - Cycle budget: inject NOP loop of 10001 iterations → HALT at 10000.
   - Jump target validation: bytecode with invalid jump offset → reject at compile time.
   - Division by zero → returns 0.0, no crash.
   - PID computation: known Kp/Ki/Kd/setpoint/input → verify output against numpy reference.
   - CLAMP_F: value outside range → verify clamped.
   - CALL/RET: nested calls to depth 16 → HALT on overflow.
   - VM state isolation: variables from one reflex don't leak to another.

3. I/O Abstraction:
   - Pin conflict detection: assign same GPIO twice → PIN_ALREADY_IN_USE.
   - Digital output: set HIGH, read back, verify.
   - PWM: set duty 512, measure with logic analyzer or frequency counter.
   - ADC: apply known voltage, read ADC, verify within tolerance.
   - I2C compass: mock I2C reads, verify heading calculation.
   - Self-test: all configured pins pass selftest with known hardware.

4. Safety:
   - Kill switch ISR timing (measure GPIO edge to output change, must be < 10ms).
   - Watchdog kick pattern (verify 0x55/0xAA alternation).
   - Heartbeat state machine: simulate 5 misses → DEGRADED, 10 → SAFE_STATE, 3 good → recovery.
   - Overcurrent detection: inject fault current, verify disable.
   - Solenoid timeout: set output ON, wait > 5000ms, verify auto-deactivation.

JETSON UNIT TESTS (/jetson/tests/):
Framework: pytest with pytest-asyncio.

Test categories:
1. Serial bridge:
   - COBS encode/decode matching firmware.
   - Message header encoding/decoding.
   - Mock serial device (pty pair): full protocol exchange simulation.
   - Baud negotiation simulation.

2. Node manager:
   - Node discovery simulation with mock serial bridge.
   - Role assignment flow.
   - Reflex deployment flow.

3. Trust score:
   - 50 good evaluations: T rises from 0.0 to ~0.095.
   - 2 bad from 0.9: T drops to ~0.776.
   - Level transitions: 120 days good evals → L3, 300 days → L5.
   - Override: level drop, cooldown enforcement.

4. Learning pipeline:
   - Cross-correlation: two sinusoids with known phase shift, verify lag detection.
   - BOCPD: step function change, verify change-point detection.
   - A/B testing: paired t-test with known-meaningful data, verify significance.

5. Integration tests (require mock serial or actual ESP32):
   - Full boot sequence simulation.
   - Role assignment → reflex deploy → telemetry → observation dump pipeline.
   - Kill switch → SAFE_STATE → recovery.
   - OTA update simulation (valid + corrupt firmware + rollback).

HARDWARE-IN-LOOP TESTS (manual, with oscilloscope):
1. Kill switch response: oscilloscope CH1=kill switch, CH2=actuator output. Target: < 10ms (aspirational < 1ms).
2. Watchdog reset: disable software kick, verify reset within 1.1s.
3. Full boot timing: oscilloscope on serial TX line. Target: OPERATIONAL at < 500ms.
4. Observation dump integrity: record 60s at 100Hz, dump, CRC-32 verify.
5. Solenoid timeout: activate output, measure auto-deactivation at ~5000ms.
6. COBS decode stress test: send 1 million random binary frames, verify zero CRC errors.

Run tests:
  make test                # Firmware unit tests
  pytest jetson/tests/     # Jetson unit tests
  pytest jetson/tests/test_integration.py  # Integration tests (with mock serial)
```

---

## Prompt 13: Documentation and Cross-Domain Templates

**Dependencies:** All prompts
**Estimated effort:** 1-2 weeks
**Goal:** Architecture decision records, build guide, domain-specific equipment templates, and getting-started guide.

### Prompt

```
Create comprehensive documentation for the NEXUS platform.

1. ARCHITECTURE_DECISION_RECORDS.md (28 ADRs):
   Each ADR includes: title, status (Accepted), date, confidence (VERY HIGH/HIGH/MEDIUM/LOW), category, decision, options considered, rationale, consequences, "what would change my mind" trigger.
   Include the 7 MEDIUM/LOW confidence decisions with detailed runner-up alternatives:
   - ADR-009: JSON State Machines vs Behavior Trees (MEDIUM)
   - ADR-012: gRPC+MQTT vs REST (MEDIUM)
   - ADR-013: Qwen2.5-Coder-7B model choice (MEDIUM)
   - ADR-017: Inverse RL pattern discovery (LOW)
   - ADR-018: 6-level vs 5-level autonomy (MEDIUM)
   - ADR-023: LittleFS vs SPIFFS (MEDIUM)
   - ADR-028: HDBSCAN vs K-Means clustering (MEDIUM)

2. SENIOR_ENGINEER_BUILD_GUIDE.md:
   - Reading order for all spec files (8-10 hours estimated).
   - 9 build steps with exact commands and file paths.
   - Test strategy: unit, integration, HIL, safety.
   - Key performance metrics table with measurement methods.
   - Development priorities: critical path → high → medium → lower.
   - Risk matrix.
   - File dependency graph.

3. EQUIPMENT TEMPLATES (one JSON per domain):
   Marine: compass, rudder, throttle, bilge pump, anchor winch, navigation lights.
   Agriculture: soil moisture, irrigation valves, greenhouse climate, fertigation.
   HVAC: zone thermostats, dampers, blowers, air quality.
   Factory: conveyor motors, quality sensors, safety interlocks, status lights.
   Mining: ventilation fans, water pumps, gas sensors, environmental monitoring.

4. GETTING_STARTED.md:
   - Prerequisites (hardware list, software tools, accounts).
   - 15-minute quickstart: flash firmware, connect serial, assign LED role, send REFLEX_DEPLOY, see LED blink.
   - Next steps for autopilot demo.

Write all documentation as Markdown files in /docs/. Reference existing spec files in /shared/specs/ where needed.
```

---

## Summary: Dependency Graph

```
Prompt 0: Scaffolding (1 day)
  ↓
Prompt 1: Wire Protocol (2-3 weeks) ← can start in parallel with Prompt 2
Prompt 2: Safety Layer (1-2 weeks) ← depends on Prompt 1 for protocol messaging
  ↓
Prompt 3: I/O Abstraction (3-4 weeks) ← depends on Prompt 1 for protocol messaging
Prompt 4: Bytecode VM (3-4 weeks) ← depends on Prompt 1 for protocol messaging
  ↓
Prompt 5: Firmware Integration (1-2 weeks) ← depends on Prompts 1-4
  ↓
Prompt 6: Jetson Serial Bridge (2-3 weeks) ← can start in parallel with Prompt 2
  ↓
Prompt 7: Jetson Cognitive Services (3-4 weeks) ← depends on Prompt 6
  ↓
Prompt 8: Trust + Autonomy (1-2 weeks) ← depends on Prompt 7
  ↓
Prompt 9: Learning Pipeline (4-6 weeks) ← depends on Prompt 7
  ↓
Prompt 10: A/B Testing (included in Prompt 9)
  ↓
Prompt 11: Cloud Code Gen (3-4 weeks) ← depends on Prompt 7
  ↓
Prompt 12: Testing (4-6 weeks) ← depends on all above
  ↓
Prompt 13: Documentation (1-2 weeks) ← depends on all above
```

## Parallel Work Opportunities

With 3 developers, split work as follows:

| Developer A (Firmware) | Developer B (Jetson Core) | Developer C (ML/Cloud) |
|---------------------|------------------------|--------------------|
| Prompts 0-5 | Prompts 0, 6-7 | Prompts 0, 7, 9 |
| Serial protocol, safety, I/O, VM, integration | Serial bridge, gRPC, MQTT, node manager, chat | Learning pipeline, A/B testing, cloud code gen |

Estimated total with parallel work: **12-16 weeks**.
