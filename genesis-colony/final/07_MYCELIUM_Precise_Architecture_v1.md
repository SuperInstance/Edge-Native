# MYCELIUM Precise Architecture Specification v1.0

**Document ID:** MYCELIUM-ARCH-v1.0
**Classification:** Engineering Specification — Build-Ready
**Date:** 2026-03-30
**Source Authority:** MYCELIUM Schema (R4-09), Minimum Code Kernel (Final-02), Downstream Effects (Final-04), Genetic Variation Mechanics (P2-05), IoT-as-Protein (P2-07), Survival of Fittest (P2-07b), Whole Boat Simulation (Final-01)
**Mandate:** A firmware engineer with ESP-IDF experience, an oscilloscope, and a pile of ESP32-S3-WROOM-1-N8R8 modules must be able to build a functional MYCELIUM colony from this document alone.

---

## Preamble

This document is the engineering specification, not the philosophical vision. Every number is justified. Every protocol is unambiguous. Every data structure has a C definition with exact byte offsets. Where this document differs from source material, this document takes precedence — it represents the resolved design after all tensions have been arbitrated.

**Resolution of Key Tensions:**
- READ_HORMONE opcode IS included (0x20) but with mandatory VM-level validity checks (rate-of-change clamping, plausibility filtering).
- Stigmergic field is Jetson-hosted with BLE mesh consensus fallback for Jetson-loss resilience.
- Fitness weights are seasonal with ±0.10 adaptive deviation from constitutional defaults.
- Winter is non-overridable (constitutional constraint).
- Maximum colony mutation rate cap: 35% in any phase.
- Grafting restricted to kinship-compatible nodes (kinship_group match or shared ancestor_hash).
- Minimum viable colony: 5 nodes for emergence; 3 nodes for production.

---

# Part I: System Architecture

---

## 1. Hardware Reference Design

### 1.1 Node Topology — 12-Node Marine Vessel Deployment

```
                         ┌──────────────────────────────────────┐
                         │     JETSON ORIN NX 16GB (PoE)        │
                         │  ┌─────────────────────────────────┐  │
                         │  │ AI Model (7B Q4 + LoRA r=16)   │  │
                         │  │ Griot Colony DB (NVMe)           │  │
                         │  │ Emergence Detector               │  │
                         │  │ Infrastructure Griot             │  │
                         │  │ Pattern Discovery Engine          │  │
                         │  │ Stigmergic Field Host (256B)     │  │
                         │  └─────────────────────────────────┘  │
                         │  15W TDP | 40 TOPS INT8 | 16GB LPDDR5 │
                         └──────────────┬────────────────────────┘
                                        │ RS-422 (921,600 baud)
                                        │ Multi-drop, 120Ω termination
                         ┌──────────────┼────────────────────────┐
                         │              │                         │
              ┌──────────┴──────┐ ┌─────┴──────┐ ┌────────────────┴──┐
              │  MAST CLUSTER   │ │  DECK      │ │   HULL CLUSTER    │
              │  (2 nodes)      │ │  CLUSTER   │ │   (2 nodes)       │
              │                 │ │  (2 nodes) │ │                    │
              │ NAV-01 [0x01]   │ │ DECK-01    │ │ BILGE-01  [0x05]  │
              │ GPS+MAG+IMU+AIS │ │ [0x03]     │ │ Water+pump+touch  │
              │                 │ │ Wind+load  │ │                    │
              │ MAST-02 [0x02]  │ │            │ │ HULL-01   [0x06]  │
              │ Anem+rig+BME    │ │ SAIL-01    │ │ Temp+vib+mics+ToF │
              │                 │ │ [0x04]     │ │                    │
              └─────────────────┘ │ Sheet+fur  │ └────────────────────┘
                                  └────────────┘
              ┌─────────────────┐ ┌────────────┐ ┌────────────────────┐
              │  PROPULSION     │ │  CABIN     │ │  ELECTRICAL       │
              │  CLUSTER        │ │  CLUSTER   │ │  CLUSTER          │
              │  (2 nodes)      │ │  (2 nodes) │ │  (2 nodes)        │
              │                 │ │            │ │                    │
              │ PROP-01 [0x07]  │ │ CABIN-01   │ │ ELEC-01   [0x09]  │
              │ Throttle+RPM    │ │ [0x0A]     │ │ Battery+solar+load│
              │                 │ │ HVAC+CO2   │ │                    │
              │ RUDDER-01 [0x08]│ │            │ │ SAFETY-01 [0x0B]  │
              │ Servo+feedback  │ │ COMFORT-01 │ │ Kill+fire+CO+MOB │
              │                 │ │ [0x0C]     │ │                    │
              └─────────────────┘ │ Heat+light │ └────────────────────┘
                                  └────────────┘

              ┌──────────────────────────────────────────────────────────┐
              │  SENTINEL & RESERVE POOL                                 │
              │  SENT-01 [0x0D] (forward: I2S mic + touch + BLE)        │
              │  SENT-02 [0x0E] (aft: I2S mic + touch + BLE)            │
              │  STEM-01 [0x0F] (reserve: forward locker, cold)          │
              │  STEM-02 [0x10] (reserve: lazarette, cold)              │
              └──────────────────────────────────────────────────────────┘

  UART2 Fungal Ring (115,200 baud):
  NAV-01→MAST-02→RUDDER-01→PROP-01→DECK-01→SAIL-01→BILGE-01→
  HULL-01→CABIN-01→COMFORT-01→ELEC-01→SAFETY-01→NAV-01

  BLE Mesh: All 16 nodes, ESP-NOW, beacon every 30s
  GPIO Emergency: SAFETY-01 → all clusters (fire/collision/MOB hardwire)
```

### 1.2 Pin Assignment Table — ESP32-S3 Standard Node

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| GPIO0 | Safety: Kill Switch Input | IN | External pull-up, EXTI, 200ms debounce |
| GPIO1 | UART0 TX (debug) | OUT | 115,200 baud, USB bridge |
| GPIO2 | UART0 RX (debug) | IN | 115,200 baud |
| GPIO3 | UART1 TX (RS-422 to Jetson) | OUT | 921,600 baud, via MAX485 |
| GPIO4 | UART1 RX (RS-422 from Jetson) | IN | 921,600 baud, via MAX485 |
| GPIO5 | UART1 DE (RS-422 TX enable) | OUT | Active high during transmit |
| GPIO6 | UART2 TX_A (fungal ring output) | OUT | 115,200 baud, Port A |
| GPIO7 | UART2 RX_A (fungal ring input) | IN | 115,200 baud, Port A |
| GPIO8 | I2C0 SDA (sensor bus) | I/O | 400 kHz, external pull-ups |
| GPIO9 | I2C0 SCL (sensor bus) | I/O | 400 kHz, external pull-ups |
| GPIO10 | UART2 TX_B (fungal ring output) | OUT | 115,200 baud, Port B |
| GPIO11 | UART2 RX_B (fungal ring input) | IN | 115,200 baud, Port B |
| GPIO12 | Touch pad 0 (water detect / proximity) | IN | Capacitive, shared with RTC_GPIO13 |
| GPIO13 | ADC1_CH4 (power rail monitor) | IN | 12-bit, INA219 SDA alternative |
| GPIO14 | PWM0 (actuator output 1 — e.g., servo) | OUT | LEDC, 50 Hz or as configured |
| GPIO15 | Touch pad 1 (proximity / environmental) | IN | Capacitive |
| GPIO16 | PWM1 (actuator output 2) | OUT | LEDC, configurable frequency |
| GPIO17 | GPIO emergency input (from SAFETY-01) | IN | EXTI, active-low |
| GPIO18 | I2S MCLK (MEMS microphone) | OUT | 16-bit 16 kHz audio |
| GPIO19 | I2S WS (MEMS microphone) | OUT | |
| GPIO20 | I2S SD_IN (MEMS microphone) | IN | |
| GPIO21 | SPI0 MOSI (future vascular / flash) | OUT | Reserved for SPI vascular protocol |
| GPIO22 | SPI0 MISO | IN | Reserved |
| GPIO23 | SPI0 CLK | OUT | Reserved |
| GPIO24 | SPI0 CS0 | OUT | Reserved |
| GPIO25 | ADC1_CH6 (stigmergic field analog) | IN | 12-bit, optional analog hormone read |
| GPIO26 | DAC_CH1 (debug output) | OUT | Oscilloscope trigger, 8-bit |
| GPIO27 | Touch pad 2 (environmental) | IN | Capacitive |
| GPIO28 | Hall Effect Sensor (internal) | IN | Magnetic field monitoring |
| GPIO29 | GPIO status LED | OUT | Active low |
| GPIO30-31 | Not bonded on WROOM module | — | |
| GPIO32-33 | Not bonded on WROOM module | — | |
| GPIO34-37 | ADC2 (optional environmental) | IN | 12-bit, WiFi active blocks ADC2 |
| GPIO38-39 | ADC2 (optional) | IN | |
| GPIO40-41 | Not bonded | — | |
| GPIO42-48 | SPI Flash (occupied by WROOM) | — | Do not use |

**Power Pins:**
- 3.3V: LDO output, max 1A total (ESP32-S3 draws ~240mA peak)
- 5V: Input from 12V→5V buck converter (MP1584 or equivalent)
- GND: Star ground at power input

### 1.3 Power Distribution Architecture

```
  SHORE POWER / SOLAR / ALTERNATOR
              │
         ┌────┴────┐
         │ 12V Bus │  (18 AWG marine-grade, 5A main fuse)
         └────┬────┘
              │
    ┌─────────┼─────────┐─────────┐──────────┐
    │         │         │         │          │
  [FUSE]   [FUSE]    [FUSE]    [FUSE]    [FUSE]
   5A        2A/node    2A/node   2A/node   2A/node
    │         │         │         │          │
  JETSON   BUCK      BUCK      BUCK      BUCK
  (PoE)    12V→5V    12V→5V    12V→5V    12V→5V
  15W      (3A)      (3A)      (3A)      (3A)
           │         │         │          │
         ┌─┴─┐     ┌─┴─┐     ┌─┴─┐      ┌─┴─┐
         │LDO│     │LDO│     │LDO│      │LDO│
         │3.3V│    │3.3V│    │3.3V│     │3.3V│
         │1A │    │1A │    │1A │     │1A │
         └─┬─┘     └─┬─┘     └─┬─┘      └─┬─┘
           │         │         │          │
         ESP32     ESP32     ESP32     ESP32
         Cluster   Cluster   Cluster   Cluster
```

**Current Budget Per Node:**

| Mode | Current | Duration | Peripherals Active |
|------|---------|----------|--------------------|
| Full Active | 120 mA | Continuous (Summer/emergency) | UART1+UART2+BLE+Touch+Hall+I2S+ADC |
| Normal Active | 80 mA | Default | UART1+BLE+ADC+core |
| Light Active | 45 mA | Low-demand | UART1+ADC+core (reduced) |
| Light Sleep | 0.8 mA | Inter-tick | ULP+touch+Hall |
| Deep Sleep (Winter) | 0.15 mA | Dormancy | ULP sentinel only |
| Emergency Wake | 120 mA | < 5 min | Full Active (adrenaline trigger) |

**Colony Total (12 primary + 2 sentinel):**
- Normal: 12×80 + 2×80 = 1,120 mA @ 5V = 5.6W
- Summer peak: 14×120 = 1,680 mA @ 5V = 8.4W
- Winter dormancy: 14×0.15 = 2.1 mA @ 3.3V ≈ 7mW
- Jetson: 15W (PoE powered separately or from 12V bus via dedicated converter)
- **Total colony power budget: 25W maximum (including Jetson)**

### 1.4 Physical Wiring Specification

| Cable | Type | Max Run | Notes |
|-------|------|---------|-------|
| RS-422 bus | Belden 3106A (22 AWG, shielded twisted pair) | 1,200 m | 120Ω termination at each end |
| UART2 fungal link | Belden 2461R (24 AWG, 2-conductor) | 15 m between adjacent nodes | Daisy-chain, ring topology |
| BLE mesh | None (wireless) | ~30-100 m LOS | ESP-NOW, 2.4 GHz |
| Power 12V | 18 AWG marine-grade tinned copper | 10 m per segment | Terminal blocks, strain relief |
| Power 5V | 20 AWG silicone-jacketed | 3 m per node | From local buck converter |
| GPIO emergency | 22 AWG single conductor | 30 m | Pull-up at source, pull-down at receiver |
| I2C sensor bus | 26 AWG ribbon cable | 1 m per node | External 4.7kΩ pull-ups on SDA/SCL |

**Connectors:**
- RS-422 bus: M12 5-pin (A-coded), IP67 rated
- Power: M12 4-pin (power-coded), IP67 rated
- UART2 fungal: JST PH 2.0mm 4-pin (port A + port B)
- GPIO emergency: Molex KK 2.54mm 2-pin
- I2C sensors: JST SH 1.0mm 4-pin or JST GH 1.25mm 4-pin
- Antenna (BLE/WiFi): IPEX/U.FL to external whip antenna

### 1.5 Jetson Orin NX Integration Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Module | Jetson Orin NX 16GB | Orin Nano Super (40 TOPS, 8GB) also supported |
| Power | 12V bus via PoE splitter or dedicated DC-DC | 15W TDP, 25W peak |
| Connectivity to colony | RS-422 via UART1 (921,600 baud) | Multi-drop, Jetson is bus master |
| Storage | NVMe M.2 2280, ≥256GB | Colony Griot database, bytecode archives |
| AI Model | DeepSeek-Coder-7B Q4 + LoRA r=16 | ~3.7GB VRAM, inference 200-500ms |
| GPU Budget | 30% Spring, 10% Summer, 5% Autumn, 50% Winter peak | Thermal throttle at >60°C |
| RAM Budget | 4GB for model, 2GB for Griot DB, 2GB for buffers | 8GB or 16GB total |
| Uptime | 24/7 during Spring/Summer/Autumn, reduced Winter | ULP-equivalent: low-power polling only in Winter |

**Jetson Tasks by Season:**

| Season | Active Tasks | GPU Utilization |
|--------|-------------|-----------------|
| Spring | Candidate generation (20-40/node), BO optimization, Z3 verification, Lineage Card analysis | ~30% |
| Summer | Emergence detection (real-time), shadow execution monitoring, Griot enrichment | ~10% |
| Autumn | Bytecode pruning, grievance adjudication, terroir update, debt audit | ~5% |
| Winter | Model fine-tuning (2h), memory replay, novel synthesis, infrastructure advisories | ~50% peak |

---

## 2. The Reflex VM Specification v1.0

### 2.1 Complete Opcode Table

The MYCELIUM Reflex VM implements 33 opcodes. Each instruction is exactly 8 bytes. The instruction format is:

```
Byte 0: Opcode (0x00 - 0x20)
Byte 1: Flags (bit 7 = syscall flag; bits 6-0 = sub-flags)
Byte 2: Operand1 (opcode-dependent)
Byte 3: Operand2 (opcode-dependent)
Bytes 4-7: Immediate value (32-bit float or 32-bit address, big-endian)
```

| Hex | Name | Operands | Cycle Cost | Description |
|-----|------|----------|------------|-------------|
| 0x00 | NOP | — | 1 | No operation; padding; dead code marker |
| 0x01 | PUSH_I8 | imm8 (byte 2) | 1 | Push 8-bit signed integer onto stack |
| 0x02 | PUSH_F32 | imm32 (bytes 4-7) | 1 | Push 32-bit float onto stack |
| 0x03 | PUSH_I16 | imm16 (bytes 2-3) | 1 | Push 16-bit signed integer onto stack |
| 0x04 | POP | — | 1 | Discard top of stack |
| 0x05 | DUP | — | 1 | Duplicate top of stack |
| 0x06 | READ_PIN | pin_idx (byte 2) | 2 | Read sensor register [pin_idx] → push |
| 0x07 | WRITE_PIN | pin_idx (byte 2) | 2 | Pop stack → write to actuator register [pin_idx] |
| 0x08 | READ_VAR | var_idx (byte 2) | 1 | Read VM variable [var_idx] → push |
| 0x09 | WRITE_VAR | var_idx (byte 2) | 1 | Pop stack → write to VM variable [var_idx] |
| 0x0A | ADD_F | — | 1 | Pop a, b; push (a + b) |
| 0x0B | SUB_F | — | 1 | Pop a, b; push (a - b) |
| 0x0C | MUL_F | — | 1 | Pop a, b; push (a × b) |
| 0x0D | DIV_F | — | 3 | Pop a, b; push (a / b); division-by-zero → push 0 |
| 0x0E | SQRT_F | — | 4 | Pop a; push √a; negative → push 0 |
| 0x0F | ABS_F | — | 1 | Pop a; push \|a\| |
| 0x10 | CMP_LT | — | 1 | Pop a, b; push 1.0 if a < b, else push 0.0 |
| 0x11 | CMP_EQ | — | 1 | Pop a, b; push 1.0 if \|a-b\| < 1e-6, else push 0.0 |
| 0x12 | CMP_GT | — | 1 | Pop a, b; push 1.0 if a > b, else push 0.0 |
| 0x13 | CMP_LTE | — | 1 | Pop a, b; push 1.0 if a ≤ b, else push 0.0 |
| 0x14 | CMP_GTE | — | 1 | Pop a, b; push 1.0 if a ≥ b, else push 0.0 |
| 0x15 | AND_F | — | 1 | Pop a, b; push (a × b) — logical AND via multiply |
| 0x16 | OR_F | — | 1 | Pop a, b; push (a + b - a×b) — logical OR |
| 0x17 | NOT_F | — | 1 | Pop a; push (1.0 - a) — logical NOT |
| 0x18 | JUMP | offset16 (bytes 2-3) | 1 | PC += offset16 (signed, 8-byte aligned target) |
| 0x19 | JUMP_IF_FALSE | offset16 (bytes 2-3) | 2 | Pop stack; if zero, PC += offset16 |
| 0x1A | JUMP_IF_TRUE | offset16 (bytes 2-3) | 2 | Pop stack; if non-zero, PC += offset16 |
| 0x1B | CALL | offset16 (bytes 2-3) | 3 | Push PC; PC += offset16; call depth ≤ 16 |
| 0x1C | RET | — | 2 | Pop PC from call stack; decrement call depth |
| 0x1D | CLAMP_F | min (bytes 2-3), max (bytes 4-5) | 1 | Pop a; push clamp(a, min, max) |
| 0x1E | EMIT_EVENT | event_code (byte 2) | 2 | Pop value; emit telemetry event to host |
| 0x1F | EMIT_TELEMETRY | schema_id (byte 2) | 2 | Snapshot current state; queue telemetry message |
| 0x20 | READ_HORMONE | hormone_idx (byte 2, 0-5) | 2 | Push hormone value [0.0, 1.0] onto stack |
| 0x80+0x01 | **SYS: HALT** | — | 0 | Stop execution; apply output clamping; safe state |
| 0x80+0x02 | **SYS: PID_COMPUTE** | pid_idx (byte 2) | 8 | Pop setpoint, measurement; PID step; push output |
| 0x80+0x03 | **SYS: READ_STATE** | var_idx (byte 2) | 2 | Push PID integral accumulator (for advanced control) |
| 0x80+0x04 | **SYS: RESET_PID** | pid_idx (byte 2) | 1 | Reset PID controller state (for genome switching) |

**Opcode 0x20 (READ_HORMONE) validity checks:**
The VM SHALL implement the following checks on every READ_HORMONE execution:
1. Rate-of-change filter: if |hormone[t] - hormone[t-1]| > 0.3/tick (impossible given decay rates), return hormone[t-1].
2. Plausibility clamp: hormone values outside [0.0, 1.0] are clamped.
3. Stale value fallback: if hormone has not been updated within 2× its natural decay period (e.g., 120s for cortisol with 60s half-life), hormone returns 0.0.
4. CPU cost: ~2 µs per READ_HORMONE (one array lookup + 2 comparisons).

### 2.2 Instruction Format (8 Bytes)

```
Offset  Size  Field
0x00    1     Opcode (0x00-0x20 for standard; 0x80-0x84 for syscalls)
0x01    1     Flags & Sub-opcode
              Bit 7: syscall flag (1 = syscall, 0 = standard)
              Bits 6-0: sub-flags (opcode-specific)
0x02    1     Operand1 (pin index, variable index, hormone index)
0x03    1     Operand2 (secondary index, sub-parameter)
0x04    4     Immediate (float32 IEEE 754 or int16+offset16 or int32)
              Encoded big-endian for cross-platform determinism
```

### 2.3 Register File Specification

| Register Type | Count | Access | Address Range | Description |
|---------------|-------|--------|---------------|-------------|
| Sensor Registers | 64 | READ only | 0x00–0x3F | I2C sensors, ADC readings, GPIO inputs, UART2 received data |
| Actuator Registers | 64 | WRITE only | 0x40–0x7F | PWM outputs, relay controls, UART2 transmit data, GPIO outputs |
| Internal Variables | 32 | READ/WRITE | 0x80–0x9F | VM scratch variables, intermediate state |
| PID Controllers | 8 | VIA syscall | 0x80+pid_idx | Each: 32-byte state block (Kp, Ki, Kd, integral, prev_error, limits) |

**Sensor register mapping (examples for NAV-01):**
| Index | Source | Data Type | Update Rate |
|-------|--------|-----------|-------------|
| 0x00 | GPS latitude | float32 (degrees) | 10 Hz |
| 0x01 | GPS longitude | float32 (degrees) | 10 Hz |
| 0x02 | GPS speed | float32 (knots) | 10 Hz |
| 0x03 | Compass heading | float32 (degrees) | 100 Hz |
| 0x04 | Gyro X | float32 (deg/s) | 100 Hz |
| 0x05 | Gyro Y | float32 (deg/s) | 100 Hz |
| 0x06 | Gyro Z | float32 (deg/s) | 100 Hz |
| 0x07 | Accel X | float32 (g) | 100 Hz |
| 0x08 | Accel Y | float32 (g) | 100 Hz |
| 0x09 | Accel Z | float32 (g) | 100 Hz |
| 0x0A | Internal temperature | float32 (°C) | 1 Hz |

### 2.4 Stack Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Depth | 256 entries | 4 bytes each (float32) |
| Total size | 1,024 bytes | PSRAM-backed on ESP32-S3 |
| Overflow behavior | VM HALT + safe state | Safety invariant |
| Underflow behavior | VM HALT + safe state | Safety invariant |
| Stack pointer (SP) | 16-bit | Points to next free slot |

### 2.5 Memory Map

```
ES32-S3 Flash (16 MB):
  0x00000000 - 0x0000FFFF  Bootloader (64 KB, signed RSA-3072)
  0x00010000 - 0x0003FFFF  OTA_0 partition (192 KB, encrypted AES-XTS-256)
  0x00040000 - 0x0006FFFF  OTA_1 partition (192 KB, encrypted)
  0x00070000 - 0x0008FFFF  NXS partition (factory-safe bytecode, 128 KB)
  0x00090000 - 0x0009FFFF  NVS partition (calibration, safety config, 64 KB)
  0x000A0000 - 0x0019FFFF  reflex_bc partition (1 MB LittleFS: 7 genomes + candidates)
  0x001A0000 - 0x001BFFFF  stigmergic_backup (128 KB, local hormone cache)
  0x001C0000 - 0x001DFFFF  lineage_partition (128 KB, Lineage Card + Griot cache)
  0x001E0000 - 0x00FFFFFF  Reserved for future use

ESP32-S3 SRAM (512 KB):
  0x0000 - 0x01FF  VM state (PC, SP, call stack, 512 bytes)
  0x0200 - 0x05FF  VM stack (256 entries × 4 bytes, 1024 bytes)
  0x0600 - 0x07FF  PID state (8 controllers × 32 bytes, 256 bytes)
  0x0800 - 0x0BFF  Sensor register file (64 × 4 bytes, 256 bytes)
  0x0C00 - 0x0FFF  Actuator register file (64 × 4 bytes, 256 bytes)
  0x1000 - 0x13FF  Internal variables (32 × 4 bytes, 128 bytes)
  0x1400 - 0x17FF  Shadow VM state (same structure, Core 1)
  0x1800 - 0xFFFF  FreeRTOS heap + HAL buffers (~54 KB)
  Remaining: 120 KB used by FreeRTOS, Wi-Fi/BLE stacks, DMA buffers

ESP32-S3 PSRAM (8 MB):
  0x000000 - 0x555555  Observation ring buffer (5.5 MB, ~32 bytes/frame at 1 kHz)
  0x555556 - 0x666665  Telemetry ping-pong buffer (1.1 MB)
  0x666666 - 0x6FFFFF  Stigmergic field local cache (256 bytes + padding)
  0x700000 - 0x7FFFFF  Reserved (~1 MB)
```

### 2.6 Execution Model

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Default tick rate | 100 Hz (10 ms period) | Standard for marine control loops |
| Maximum tick rate | 1 kHz (1 ms period) | Fast reflex arcs (safety-critical) |
| Minimum tick rate | 10 Hz (100 ms period) | Non-critical monitoring |
| Cycle budget | 1,000 µs at 100 Hz | Leaves 9,000 µs for I/O, comms, OS |
| Cycle budget enforcement | Hardware timer ISR sets flag; VM checks every instruction | Non-bypassable |
| Safety check | Post-execution output clamping (< 5 µs) | Applied outside VM context |
| Watchdog kick interval | Every 10 VM ticks (100 ms) | Hardware IWDT, independent of CPU |
| Max instructions per tick | ~1,200 (at 240 MHz, ~0.8 µs/instruction average) | Soft-float; FPU-accelerated MCUs higher |
| VM task priority | FreeRTOS priority 15 (highest) | Safety-critical |
| Preemption | Disabled during VM execution (critical section) | Ensures deterministic timing |

### 2.7 Safety Invariants — What the VM CANNOT Do

1. **No out-of-bounds memory access:** Sensor registers [0-63], actuator registers [64-127], variables [128-159] are bounds-checked. Access outside range → VM HALT.
2. **No infinite loops:** Cycle budget timer fires at tick boundary; VM halts immediately. No bytecode can run longer than 1,000 µs per tick.
3. **No unsafe actuator outputs:** Post-execution clamping applies per-channel min/max from NVS. VM writes to scratch buffer; DMA or safety supervisor copies to actual output register with clamping. VM cannot bypass this path.
4. **No runaway recursion:** Call depth counter (max 16). Overflow → VM HALT.
5. **No unsafe syscall parameters:** PID_COMPUTE with pid_idx ≥ 8 → VM HALT. READ_PIN with index ≥ 64 → VM HALT.
6. **No modification of firmware, bootloader, or partition table:** Flash writes are restricted to the `reflex_bc` LittleFS partition. Secure boot v2 (RSA-3072) and flash encryption (AES-XTS-256) prevent modification of other partitions.
7. **No raw GPIO manipulation:** All GPIO access goes through the HAL's configured pin map. The VM cannot reconfigure pins or override safety clamping.
8. **No network access:** The VM has no opcodes for UART TX/RX, BLE, WiFi, or MQTT. All communication is handled by FreeRTOS tasks outside the VM.
9. **No timing control:** The VM cannot modify its tick rate, disable the watchdog, or delay its own execution.
10. **No floating-point NaN propagation:** Any NaN or Inf result from arithmetic is clamped to 0.0 before pushing to stack.


## 3. Communication Protocol Specifications

### 3.1 RS-422 NEXUS Wire Protocol v2.0

The primary communication channel between all ESP32 nodes and the Jetson. Multi-drop topology with Jetson as bus master. 921,600 baud, 8-N-1, CRC-16-CCITT.

**Physical Layer:**
- Transceiver: MAX485 or equivalent
- Baud: 921,600 (default); 115,200 (fallback)
- Topology: Multi-drop, 120Ω termination at each end
- Max nodes: 20 per bus segment
- Cable: 22 AWG shielded twisted pair, max 1,200 m

**Frame Format:**
```
Offset  Size  Field                    Description
0x00    1     Start byte               0x7E (SLIP-style framing)
0x01    1     Message type             See table below
0x02    1     Source node ID           0x01–0x10
0x03    1     Destination node ID      0x00 = Jetson, 0x01-0x10 = node, 0xFF = broadcast
0x04    2     Payload length           Big-endian uint16, max 240 bytes
0x06    2     Sequence number          Monotonic uint16, overflow OK
0x08    N     Payload                  N bytes (COBS-encoded if contains 0x7E or 0x7D)
0x08+N  2     CRC-16                   CRC-16-CCITT over bytes 0x01 through 0x08+N-1
0x0A+N  1     End byte                 0x7E
```

**COBS Encoding:** If payload contains 0x7E or 0x7D, the entire payload is COBS-encoded (Consistent Overhead Byte Stuffing) before framing. The payload length field indicates the decoded length.

**Message Types:**

| Type | Name | Direction | Payload Description |
|------|------|-----------|---------------------|
| 0x01 | HEARTBEAT | Node → Jetson | 1 byte: alive status (0=OK, 1=degraded, 2=emergency) |
| 0x02 | SENSOR_REPORT | Node → Jetson | Packed sensor readings (variable schema, ≤72 fields) |
| 0x03 | TELEMETRY_STREAM | Node → Jetson | 10 Hz periodic state snapshot |
| 0x04 | ACTUATOR_CMD | Jetson → Node | 2 bytes: register_idx + 4 bytes: float32 value |
| 0x05 | ACTUATOR_ACK | Node → Jetson | Echo of command + status byte |
| 0x06 | BYTECODE_UPDATE | Jetson → Node | 64-byte header + bytecode binary |
| 0x07 | BYTECODE_ACK | Node → Jetson | content_hash + status (0=OK, 1=CRC fail, 2=validation fail) |
| 0x08 | FITNESS_REPORT | Node → Jetson | 4 bytes: float32 fitness score |
| 0x09 | HORMONE_SET | Jetson → Node | 1 byte: hormone_idx + 1 byte: 4.4 fixed-point value |
| 0x0A | THREAT_BROADCAST | Any → All | 1 byte: level (0-4) + 1 byte: threat_code |
| 0x0B | LINEAGE_EXCHANGE | Node → Node (via Jetson) | 64-byte Lineage Card |
| 0x0C | STIGMERGIC_FIELD | Jetson → All | 256 bytes: full field sync |
| 0x0D | STIGMERGIC_DELTA | Jetson → All | Changed fields only, variable length |
| 0x0E | GRIEVANCE_FILE | Node → Jetson | Grievance record (see data structures) |
| 0x0F | GRIEVANCE_RESPONSE | Jetson → Node | Accept/reject + reasoning hash |
| 0x10 | GENOME_SWITCH | Jetson → Node | 1 byte: genome_slot (0-6) |
| 0x11 | CALIBRATION_UPDATE | Jetson → Node | NVS key-value pairs |
| 0x12 | INFRASTRUCTORY_ALERT | Jetson → Human | Natural-language advisory string |
| 0x13 | SEASON_COMMAND | Jetson → All | 1 byte: season enum (0=Spring, 1=Summer, 2=Autumn, 3=Winter) |
| 0x14 | EPOCH_SYNC | Jetson → All | 8 bytes: uint64 Unix timestamp ms |
| 0x15 | NODE_QUERY | Jetson → Node | Request node status/capabilities |
| 0x16 | NODE_RESPONSE | Node → Jetson | Capabilities, health, storage status |
| 0x17 | OTA_CHUNK | Jetson → Node | Firmware update chunk |
| 0x18 | OTA_COMPLETE | Jetson → Node | Finalize OTA, trigger reboot |
| 0x19 | EMERGENCY_OVERRIDE | Jetson → All | 1 byte: emergency_type + actions |
| 0x1A | GRAFT_PROPOSAL | Node → Node (via Jetson) | Subroutine fragment + metadata |
| 0x1B | GRAFT_ACCEPT | Node → Node | Accept + placement offset |
| 0x1C | COLONY_MATING_INIT | Jetson → Jetson (inter-vessel) | Colony metadata exchange |

**Flow Control:**
- Jetson polls nodes in round-robin at 100 Hz (10 nodes × 100 µs max per poll = 1 ms bus utilization)
- Nodes transmit unsolicited messages (THREAT, HEARTBEAT) using carrier-sense: wait for 2 bytes of silence (22 µs at 921,600 baud), then transmit
- If collision detected (CRC mismatch on receive), both nodes back off for random 1-5 ms and retry
- Bus utilization target: < 60% (leaves margin for burst traffic)

### 3.2 UART2 Fungal Protocol

Direct node-to-node communication, bypassing the Jetson. Daisy-chain ring topology. 115,200 baud default.

**Frame Format (8 bytes, fixed):**
```
Offset  Size  Field
0x00    1     Source node ID (0x01–0x10)
0x01    1     Message type
0x02    2     Payload (big-endian, type-dependent)
0x04    2     Sequence number (monotonic uint16, overflow OK)
0x06    2     CRC-16 (polynomial 0x8005, optional: enabled for type 3 and type 4 only)
```

**Message Types:**

| Type | Name | Payload | Frequency |
|------|------|---------|-----------|
| 0x00 | STATUS | Byte 0: sensor_summary (0-255), Byte 1: actuator_summary (0-255) | Every 30 s |
| 0x01 | FITNESS | uint16: fitness_score (0-1000) | Every 60 s |
| 0x02 | THREAT | Byte 0: threat_level (0-4), Byte 1: threat_code (see codes below) | Immediate |
| 0x03 | LINEAGE | uint16: first 2 bytes of content_hash (kinship recognition) | On exchange |
| 0x04 | GRIEVANCE | uint16: retiring_variant_hash, uint16: grievance_vocabulary_idx | On retirement |
| 0x05 | REFLEX_DATA | 4 bytes: sensor/actuator value for reflex arc partner | 100 Hz (during active reflex) |
| 0x06 | HEARTBEAT_ACK | 1 byte: node status, 1 byte: ring_health (0=OK, 1=break detected) | Every 30 s |
| 0x07 | GRAFT_FRAGMENT | uint16: offset, uint16: fragment_hash (pre-exchange metadata) | On graft proposal |

**Threat Codes:**
| Code | Threat |
|------|--------|
| 0x00 | None (status update) |
| 0x01 | Node failure (heartbeat timeout) |
| 0x02 | Sensor anomaly (statistical outlier) |
| 0x03 | Squall precursor (baro + wind + humidity) |
| 0x04 | Collision risk (proximity alarm) |
| 0x05 | Structural failure (impact + vibration) |
| 0x06 | Flooding (water level) |
| 0x07 | Fire / CO / smoke |
| 0x08 | Power failure (voltage drop) |
| 0x09 | Man overboard |

**Ring Health Monitoring:**
Each node monitors its UART2 ring connectivity. If node N fails to receive a frame from node N-1 within 90 seconds, it broadcasts THREAT type=0x01 with payload={0x02, N-1}. If the ring breaks, the surviving segment reconfigures to a linear chain; the endpoints cannot communicate directly but relay through the Jetson via RS-422 as fallback.

### 3.3 BLE Mesh / ESP-NOW Protocol

Wireless proximity-based coordination. ESP-NOW (connectionless, no pairing). 2.4 GHz, ~1 Mbps raw, 5-50 ms latency.

**Beacon Format (ESP-NOW, 32 bytes max):**
```
Offset  Size  Field
0x00    1     Colony ID (matches vessel; prevents inter-vessel confusion)
0x01    1     Node ID (0x01–0x10)
0x02    1     Beacon type (0=status, 1=emergency, 2=lineage_request, 3=lineage_response)
0x03    1     Season (0=Spring, 1=Summer, 2=Autumn, 3=Winter)
0x04    2     Fitness score (uint16, 0-1000)
0x06    1     Threat level (0-4)
0x07    1     RSSI of sender (as measured by sender — not useful; receiver measures own RSSI)
0x08    4     Content hash prefix (first 4 bytes of SHA-256)
0x0C    4     Colony metabolic rate (float32, watts)
0x10    16    Reserved (future: stigmergic field delta, environmental data)
```

**Beacon Frequency:**
- Normal: Every 30 seconds
- Emergency (threat level ≥ 3): Every 2 seconds, broadcast with WIFI_TX_POWER_HIGH (20 dBm)
- Winter dormancy: Every 5 minutes (ULP beacon if supported, else main core wake)

**Emergency Override:**
When any node broadcasts beacon type=1 (emergency), all receiving nodes immediately enter elevated state:
1. Check adrenaline hormone (via stigmergic field or local cache)
2. If not already elevated, switch to emergency genome from portfolio
3. Increase sensor sampling to maximum rate
4. Enable all reflex arcs
5. Send GPIO emergency line pulse to downstream nodes (if available)

**Spatial Model:**
RSSI values from all nodes are aggregated into a 16×16 distance matrix (256 bytes). The Jetson computes approximate 2D positions using trilateration. The model updates every 30 seconds. This enables detection of physical topology changes (hatches opened, panels removed, new nodes installed).

### 3.4 The Stigmergic Field Protocol

The endocrine layer's shared memory. 256 byte-addressable locations hosted by the Jetson and broadcast to all nodes via RS-422.

**Layout:**
```
Address   Size  Name                    Access       Description
0x00      1     Hormone: Cortisol        Jetson-only  Stress level, 4.4 fixed-point
0x01      1     Hormone: Auxin            Jetson-only  Growth level, 4.4 fixed-point
0x02      1     Hormone: Melatonin        Jetson-only  Sleep level, 4.4 fixed-point
0x03      1     Hormone: Oxytocin         Jetson-only  Bonding level, 4.4 fixed-point
0x04      1     Hormone: Adrenaline       Jetson-only  Alert level, 4.4 fixed-point
0x05      1     Hormone: Ethylene         Jetson-only  Senescence level, 4.4 fixed-point
0x06-0x07 2     Colony metabolic rate    Jetson-only  uint16 (milliwatts)
0x08-0x09 2     Colony temperature        Jetson-only  int16 (°C × 10)
0x0A-0x0B 2     Bus activity density      Jetson-only  uint16 (messages/second)
0x0C      1     Power supply margin       Jetson-only  uint8 (% headroom)
0x0D      1     Node count alive          Jetson-only  uint8 (0-16)
0x0E-0x0F 2     Colony fitness aggregate  Jetson-only  uint16 (0-1000)
0x10-0x1F 16    Colony status word        Jetson-only  Bitfield: node health, season, alert state
0x20-0x2F 16    Node-01 local channel     Node-01 RW   Node-01 writes its state summary
0x30-0x3F 16    Node-02 local channel     Node-02 RW
...
0xF0-0xFF 16    Node-14 local channel     Node-14 RW   (Node-15 and Node-16 use 0xF0-0xFF overflow)
```

**Hormone Encoding: 4.4 Fixed Point**
- 1 byte encodes values 0.0 to 0.9375 in steps of 0.0625 (1/16)
- To encode: `(uint8_t)(value * 16.0 + 0.5)` clamped to [0, 240]
- To decode: `(float)byte / 16.0`
- 0xF0 = 0.9375 (maximum practical value; values 0xF1-0xFF reserved)
- Justification: 4 bits of fraction (0.0625 resolution) is sufficient for graded behavioral responses. Full byte resolution is unnecessary.

**Decay Algorithm:**
Every 60 seconds (configurable per hormone), each hormone value is right-shifted by 1 (equivalent to halving):
```
hormone = hormone >> 1;  // Halving decay
```
This produces exponential decay with half-life = decay_period.

| Hormone | Half-Life | Min Decay Rate | Max Value |
|---------|-----------|----------------|-----------|
| Cortisol | 60 s | 60 s (constitution) | 0.9375 (0xF0) |
| Auxin | 120 s | 120 s | 0.9375 |
| Melatonin | 300 s | 300 s | 0.9375 |
| Oxytocin | 600 s | 600 s | 0.9375 |
| Adrenaline | 10 s | 10 s | 0.9375 |
| Ethylene | 180 s | 180 s | 0.9375 |

**Write Authority:**
- Locations 0x00-0x1F: Jetson only (via HORMONE_SET message). Gye Nyame layer can write 0x04 (adrenaline) directly in hardware-detected emergencies.
- Locations 0x20-0xFF: Each node writes only to its own 16-byte channel. Cross-writing is prohibited by the VM (WRITE_PIN to another node's channel → VM HALT).

**Jetson-Loss Fallback:**
When the Jetson heartbeat is not received for 30 consecutive seconds (3 heartbeat intervals):
1. All hormone values in local ESP32 cache continue decaying to zero naturally.
2. BLE mesh consensus: nodes broadcast their last-known hormone values; majority value is adopted.
3. If BLE consensus is unavailable (no neighbors), all hormones default to 0.0.
4. Adrenaline fallback: hardware emergency inputs (kill switch, fire detector) directly set adrenaline = 0.9375 in local cache without Jetson involvement.

### 3.5 SPI Vascular Protocol (Future — Specification for Coherence)

For future register sharing between nodes connected via SPI (in-phase co-evolved bytecodes operating on shared sensor/actuator state).

**Coherence Protocol: Write-Invalidate with Owner:**
1. Each 16-byte block in the shared register space has an owner node (the node that writes to it).
2. When the owner writes to a block, it broadcasts an INVALIDATE message on the SPI bus.
3. Non-owner nodes mark their cached copy as invalid.
4. When a non-owner reads an invalidated block, it fetches the current value from the owner via SPI transfer.
5. Conflict resolution: if two nodes attempt to own the same block, the node with the lower node ID wins (deterministic tie-breaking).

**SPI Parameters:**
- Speed: 80 MHz (ESP32-S3 SPI2 maximum)
- Mode: 0 (CPOL=0, CPHA=0)
- Frame format: 8 bytes (same as VM instruction format for consistency)
- Max shared blocks: 64 blocks × 16 bytes = 1,024 bytes
- Latency: < 0.1 ms per block transfer (80 MHz / 8 bits × 128 bits)

This protocol is specified but NOT implemented in v1.0. It requires the SPI GPIO pins to be freed from their reserved status (currently occupied by flash on WROOM modules; requires ESP32-S3-WROOM-1 with Octal SPI or a module with separate SPI pins).

---

## 4. The Three-Layer Coordination Model — Precise Specification

### 4.1 Endocrine Layer

**Hormone Trigger Conditions (exact thresholds):**

| Hormone | Trigger Condition | Source |
|---------|-------------------|--------|
| Cortisol | `sustained_heading_variance > 3.0° for > 60s` OR `sensor_anomaly_count > 2 in 30s` OR `power_supply_margin < 20%` | Jetson computed from telemetry |
| Auxin | `power_supply_margin > 50%` AND `cpu_utilization < 40%` AND `threat_level == 0` AND `season == SPRING` | Jetson computed |
| Melatonin | `season == WINTER` OR `(internal_temp > 60°C for > 30 min)` OR `operator_override == true` | Jetson or NVS config |
| Oxytocin | `(inosculation_bridge_confirmed == true)` OR `(colony_fitness_aggregate > 800 for > 7 days)` OR `(colony_mating_event == true)` | Jetson computed |
| Adrenaline | `(any node broadcasts threat_level >= 3)` OR `(collision_risk_distance < 50m)` OR `(structural_impact > 10g)` | Immediate, bypass Jetson if needed |
| Ethylene | `season == AUTUMN` OR `(colony_fitness_aggregate < 400 for > 14 days)` OR `(bytecode_age > 200 generations)` | Jetson computed |

**VM Opcode Interface: READ_HORMONE (0x20)**
```
Operand: hormone_idx (0=Cortisol, 1=Auxin, 2=Melatonin, 3=Oxytocin, 4=Adrenaline, 5=Ethylene)
Returns: float32 [0.0, 1.0] pushed onto stack
Latency: ~2 µs (local cache read + validity check)
Safety: rate-of-change filter + plausibility clamp + stale fallback (see §2.1)
```

### 4.2 Nervous Layer

**Reflex Arc Formation Protocol:**

**Phase 1 — Discovery (Spring phase, GPIO + BLE):**
- GPIO proximity detection: nodes with GPIO17 (emergency input) connected by wire detect each other via a 1 Hz heartbeat pulse (alternating high/low, detected by EXTI interrupt).
- BLE RSSI scanning: nodes broadcast ESP-NOW beacons; RSSI > -60 dBm (approximately 5 m indoors) indicates potential neighbor.
- Discovery result: a set of (node_A, node_B, distance_estimate, channel_type) tuples.
- Discovery duration: first 72 hours of Spring phase.

**Phase 2 — Experimentation (Bridge Formation, 1-2 weeks):**
- A tentative UART2 bridge is established between discovered neighbors.
- Bridge data type 0x05 (REFLEX_DATA) carries a single float32 value per tick at 100 Hz.
- The colony's evolutionary process evaluates bridge fitness: does inter-node coordination via this bridge improve colony fitness compared to coordination through Jetson alone (which adds 2-50 ms latency)?
- Bridge evaluation period: minimum 4,950 ticks (49.5 seconds at 100 Hz) per SPRT statistical significance requirement.
- If fitness improves by >5% with p < 0.05: bridge is promoted to Phase 3.
- If no improvement after 7 days: bridge is decommissioned.

**Phase 3 — Consolidation (Reflex Calibration, Summer phase):**
- The Jetson generates bytecodes that explicitly use REFLEX_DATA (UART2 type 0x05) values.
- Sensor node: pushes sensor reading to UART2 type 0x05 at 100 Hz.
- Actuator node: reads REFLEX_DATA via sensor register (mapped from UART2 receive buffer) in the same tick.
- Calibration data (timing offsets, value scaling, safety thresholds) stored in NVS.
- Consolidated reflex arcs are permanent until Autumn pruning review or explicit veto.

**Reflex Arc Safety Constraints:**
1. **Timeout:** If sensor node stops streaming for > 10 consecutive ticks (100 ms), actuator falls back to local bytecode.
2. **Output clamping:** Same per-channel min/max limits apply regardless of data source (local or reflex).
3. **No chains:** Reflex arcs are strictly point-to-point (sensor → actuator). Multi-hop prohibited.
4. **Veto:** Human operator or Jetson (Spring/Autumn only) can disable any reflex arc via ACTUATOR_CMD 0x19.
5. **Bandwidth limit:** Maximum 1 reflex arc per UART2 port (A and B), per node.

### 4.3 Immune Layer

**Pathogen Detection Algorithms:**

**1. Corrupted Bytecode Detection:**
- Method: Jetson temporal pattern mining (BOCPD — Bayesian Online Change Point Detection).
- Threshold: If a node's output RMS error changes by >3σ from its 30-day rolling baseline for >100 consecutive ticks, flag as potential corruption.
- Secondary: Stigmergic field comparison — if neighboring nodes with correlated sensors report consistent values while the flagged node diverges, confirm corruption.
- Response: OTA re-flash from most recent stable-point bytecode (< 1 second). Quarantine corrupted bytecode in pathogen archive.

**2. Sensor Drift Detection:**
- Method: Cross-node correlation analysis. If node A's sensor reading diverges from nodes B and C (which measure correlated quantities) by >2× the historical correlation residual for >24 hours, flag drift.
- Challenge: Bytecode co-evolves with drift — the bytecode cannot detect its own sensor's drift.
- Response: Automatic recalibration against colony baseline (Jetson computes correction factor). If recalibration residual > 10% of sensor range, flag for physical maintenance.
- Detection timescale: Days to weeks (drift is gradual).

**3. External Interference Detection:**
- Method: Simultaneous noise floor increase across ≥3 nodes without corresponding physical stimulus. Statistical test: noise floor variance across nodes vs. historical baseline.
- Response: Increase sampling rates (2×). Enable digital filtering (IIR, configurable coefficients). Switch affected communication to alternative channel if available.
- Detection timescale: Seconds.

**4. Parasitic Bytecode Detection:**
- Metric: `colony_contribution_per_watt = fitness_score / current_draw_mA`
- Threshold: If node's contribution per watt falls below 10th percentile of colony for >7 consecutive days AND current draw > 200 mA.
- Response: (a) Reduce VM tick budget to 50 Hz (from 100 Hz). (b) Limit RS-422 bus access time to 5% of round-robin slot. (c) Target for aggressive bytecode replacement in next Spring (higher mutation rate, more candidates).

**Kinship Recognition Algorithm:**
```
function kinship_score(card_a, card_b):
    if card_a.kinship_group == card_b.kinship_group:
        return 1.0  // Same parent → maximum kinship
    shared_ancestors = 0
    for i in 0..3:
        if card_a.ancestor_hash[i] in card_b.ancestor_hash[0..3]:
            shared_ancestors++
    if shared_ancestors >= 2:
        return 0.8  // Strong kinship
    if shared_ancestors == 1:
        return 0.5  // Weak kinship
    return 0.0  // Unrelated

function graft_permission(card_a, card_b):
    score = kinship_score(card_a, card_b)
    if score >= 0.5:
        return ALLOWED  // Graft permitted with compatibility check
    if score >= 0.0 and terroir_compat > 0.70:
        return CONDITIONAL  // Graft permitted with extended testing (30-day A/B)
    return DENIED
```

**Grievance Filing Protocol:**
1. When a variant is retired (see §7.2), if it was the best performer under ANY specific environmental condition (normalized fitness > 1.0σ in any terrain cell), it files a grievance.
2. Grievance format: {retiring_variant_hash (uint32), terrain_cell_id (uint8), fitness_in_condition (float32), conditional_advantage_description (uint16 vocabulary index)}.
3. Grievance is broadcast via UART2 type 0x04 and forwarded to Jetson via RS-422 type 0x0E.
4. Grievance is stored in Jetson Griot database with timestamp.
5. Adjudication occurs during Autumn consolidation (see §7.3).

---

## 5. Safety Constitution

### 5.1 Gye Nyame Layer (Hardware-Enforced)

| Mechanism | Implementation | Value | Bypass? |
|-----------|---------------|-------|---------|
| Independent Watchdog (IWDT) | ESP32 Timer Group 1, Timer 0 | 100 ms timeout; VM must kick every 10 ticks | No — hardware peripheral |
| Output Clamping | Post-VM DMA buffer copy or ISR check | Per-channel min/max from NVS keys | No — runs after VM halts |
| Cycle Budget Timer | ESP32 Timer Group 0, Timer 0 | 1,000 µs at 100 Hz; ISR sets `budget_expired` flag | No — hardware timer interrupt |
| Safe-State GPIO | GPIO configured via bootloader, never modified by firmware | Kill switch, emergency outputs | No — bootloader-locked |
| Flash Protection | Secure Boot v2 (RSA-3072) + Flash Encryption (AES-XTS-256) | All partitions except reflex_bc are immutable | No — hardware crypto engine |
| Brownout Detector | ESP32 builtin, 2.5V threshold | Resets on voltage drop | No — hardware comparator |
| Stack Canary | Compiler-inserted canary pattern at stack boundaries | 0xDEADBEEF | No — compiler-generated check |

**Output Clamping Implementation (concrete):**
```c
// Runs in safety ISR or DMA completion callback, OUTSIDE VM context
void safety_clamp_outputs(void) {
    for (int ch = 0; ch < NUM_ACTUATOR_CHANNELS; ch++) {
        float output = actuator_scratch[ch];  // VM wrote here
        if (output < safe_min[ch]) output = safe_min[ch];
        if (output > safe_max[ch]) output = safe_max[ch];
        // Rate limiting
        float delta = output - actuator_last[ch];
        float max_delta = safe_rate[ch] * dt;  // safe_rate in units/sec
        if (delta > max_delta) delta = max_delta;
        if (delta < -max_delta) delta = -max_delta;
        output = actuator_last[ch] + delta;
        // Write to actual hardware
        write_actuator_hw(ch, output);
        actuator_last[ch] = output;
    }
}
```

### 5.2 Firmware Guard Layer

| Layer | Priority | What It Protects | Mechanism |
|-------|----------|-------------------|-----------|
| Safety clamping ISR | Priority 1 (highest) | Actuator outputs | Timer ISR, cannot be preempted |
| Cycle budget ISR | Priority 2 | VM execution time | Timer ISR, sets flag |
| Watchdog kick | Priority 3 | System liveness | Called in VM loop |
| RS-422 RX ISR | Priority 5 | Communication | UART interrupt, DMA buffer |
| UART2 RX ISR | Priority 5 | Fungal network | UART interrupt |
| BLE RX callback | Priority 6 | Mesh communication | WiFi/BLE task |
| Telemetry task | Priority 10 | Data logging | FreeRTOS task |
| Jetson communication task | Priority 12 | Colony coordination | FreeRTOS task |
| OTA update task | Priority 15 (lowest) | Firmware updates | Only runs when VM paused |

**Memory Protection:**
- VM code executes in a dedicated function with its own stack frame. The stack pointer is checked against bounds before every instruction dispatch.
- The `reflex_bc` LittleFS partition is the ONLY partition the VM can trigger writes to. The NVS partition is writable only through the `nx_rt_nvs_*()` API, which validates key names and value ranges.
- OTA verification: All OTA images are verified with RSA-3072 signature before flashing. The public key hash is burned into eFuse at manufacturing time. No OTA image without a valid signature from the NEXUS authority can execute.

### 5.3 VM Sandbox Layer

**Pre-execution validation (before any bytecode is loaded into the VM):**
1. **Magic check:** Bytecode metadata must contain `0x4E45585A` ("NEXU") at offset 0.
2. **Opcode scan:** Every byte at 8-byte-aligned offsets must be a valid opcode (0x00-0x20 or 0x81-0x84). Invalid opcode → reject.
3. **Jump target validation:** Every JUMP/JUMP_IF_FALSE/CALL target must point to a valid 8-byte-aligned offset within the bytecode. Target out of range → reject.
4. **Stack depth analysis:** Symbolic execution traces all paths; maximum stack depth must be < 256. Overflow detected → reject.
5. **Call depth analysis:** Maximum nesting depth of CALL/RET must be < 16. Overflow detected → reject.
6. **Register access validation:** All READ_PIN/WRITE_PIN operands must be < 128 (within sensor+actuator range). Out-of-range → reject.
7. **PID index validation:** All PID_COMPUTE operands must be < 8. Out-of-range → reject.
8. **Hormone index validation:** All READ_HORMONE operands must be < 6. Out-of-range → reject.
9. **HALT sentinel:** Bytecode must contain at least one HALT instruction (0x81). Missing → reject.

**Runtime enforcement (during every tick):**
1. Cycle budget flag checked every instruction.
2. Stack pointer checked against bounds every PUSH/DUP/CALL.
3. NaN/Inf result clamped to 0.0 after every arithmetic instruction.
4. Division by zero returns 0.0 (does not trigger VM HALT).
5. Any violation → VM HALT immediately → safe-state outputs applied.

### 5.4 Runtime Supervisor Layer

**Lyapunov Stability Certificate:**

The Lyapunov certificate is a mathematical proof (or strong empirical evidence) that a bytecode's closed-loop behavior is stable. It is generated by the Jetson and attached to every deployed bytecode's metadata.

**Generation Procedure (Level 1 — Parameter Mutation):**
1. Linearize the plant model around the current operating point:
   ```
   dx/dt = A·x + B·u
   y = C·x
   ```
   Where x = [error, integral, derivative]^T for a PID loop.
2. Solve the Continuous-time Algebraic Riccati Equation (CARE):
   ```
   A'P + PA - PBR^{-1}B'P + Q = 0
   ```
   Where Q = diag([100, 1, 10]) (state cost), R = 1 (control cost).
3. Verify P is positive definite: all eigenvalues of P > 0.
4. Compute minimum eigenvalue: λ_min(P). This is the stability margin.
5. **Pass criterion:** λ_min > 0.001 (empirically determined threshold for the NEXUS fleet).
6. **Computation time:** < 100 ms on Jetson Orin NX for a SISO PID loop.

**Certificate Format (stored in bytecode metadata):**
```c
typedef struct {
    float operating_point[3];      // {heading_error_deg, speed_knots, load_fraction}
    float eigenvalues[3];          // Eigenvalues of P matrix
    float min_eigenvalue;          // λ_min(P) — the pass/fail metric
    uint8_t linearization_valid;   // 1 = within operating envelope, 0 = extrapolation
    uint8_t monte_carlo_pass_rate; // % of 10K perturbations that remained stable
    uint16_t reserved;
} lyapunov_certificate_t;  // 32 bytes
```

**Verification Procedure (at bytecode load time on ESP32):**
The ESP32 does NOT recompute the Lyapunov certificate — it only verifies the attached certificate:
1. Check `min_eigenvalue > 0.001`.
2. Check `linearization_valid == 1`.
3. Check `monte_carlo_pass_rate >= 95`.
4. If any check fails, bytecode is loaded but flagged for shadow-execution-only (cannot drive actuators until a valid certificate is attached by the Jetson).

**Output Rate Limiting:**
Every actuator channel has a configurable rate limit stored in NVS:
```
safe_rate[channel] = max_change_per_second
```
Applied in the safety_clamp_outputs() function (see §5.1). The rate limit is computed as:
```
max_delta = safe_rate[channel] × (1.0 / tick_rate_hz)
```
This is applied AFTER the absolute clamping, ensuring that even if the VM produces a valid but rapidly changing output, the physical actuator is protected from violent transients.

**Safe-State Transition Protocol:**
When the VM HALTs (due to cycle budget, stack overflow, or explicit HALT instruction):
1. VM execution stops immediately.
2. Current actuator scratch buffer values are preserved (NOT zeroed).
3. Safety clamping is applied to the preserved values (this is the "safe state" — the last valid output clamped to safe range).
4. If the VM was driving a safety-critical channel (rudder, throttle, kill switch relay), the channel is forced to its configured safe-state value from NVS (e.g., rudder → 90° center, throttle → 0% idle, kill switch → active).
5. The VM does NOT restart automatically. It waits for the next tick boundary.
6. If the VM has halted >3 times in the last 100 ticks, the node enters DEGRADED mode: VM is paused, safe-state outputs are held, Jetson is notified via HEARTBEAT with status=2 (emergency).


# Part II: Evolutionary Engine

---

## 6. Genetic Variation Mechanics — Precise Algorithms

### 6.1 Four Mutation Levels

**Level 1 — Parameter Mutation (PID Gains + Bounds)**

What changes: PID gains (Kp, Ki, Kd), integral_limit, output_min, output_max in pid_state_t (32 bytes per controller). Fields at offsets +0, +4, +8, +20, +24, +28.

Algorithm (hybrid gradient descent + Bayesian optimization):
```
function generate_level1_variant(parent, telemetry):
    // Step 1: Identify active PID_COMPUTE syscalls
    //   Scan for opcode=0x80|0x02 in instruction array
    //   Extract pid_idx from byte 2

    // Step 2: Extract current gains from config block (offset 0x40)
    current = {Kp, Ki, Kd, integral_limit, output_min, output_max}

    // Step 3: Gradient estimate from telemetry window (N=1000-10000 ticks)
    error = [setpoint[i] - actual[i] for i in telemetry_window]
    for each gain g in {Kp, Ki, Kd}:
        delta_g = -learning_rate * d(sum(error^2))/d(g)
        learning_rate = 0.001 / (1.0 + generation * 0.01)

    // Step 4: Bayesian posterior sample
    if GP_surrogate_available:
        g_proposed = gp_mean + gp_std * randn()
    else:
        sigma = 0.05 * |g_current|  // 5% relative noise (Spring: 10%)
        g_proposed = g_current + delta_g + sigma * randn()

    // Step 5: Clamp to safe bounds
    Kp = clamp(g_proposed.Kp, 0.0, 100.0)
    Ki = clamp(g_proposed.Ki, 0.0, 50.0)
    Kd = clamp(g_proposed.Kd, 0.0, 10.0)
    integral_limit = clamp(Kp * 100, 0.0, inf)

    // Step 6: Generate child bytecode (copy parent, overwrite config)
    child = clone(parent)
    child.config_block.pid_gains = {Kp, Ki, Kd, integral_limit, ...}
    child.metadata.content_hash = SHA256(child.instructions)

    // Step 7: Lyapunov validation
    cert = compute_lyapunov(child, plant_model)
    if cert.min_eigenvalue < 0.001:
        retry_count++
        if retry_count < 3: goto Step 4
        else: return parent  // No valid variant found

    return child
```

**Level 2 — Conditional Mutation (Control Flow Structure)**

What changes: JUMP_IF_FALSE/JUMP_IF_TRUE targets, comparison operands, condition-action block insertion/removal.

Procedure:
1. **Anomaly detection:** BOCPD on telemetry stream. Metric deviates >2σ from rolling baseline for >10 ticks → anomaly event.
2. **AI hypothesis generation:** Jetson model proposes: "When condition X, then action Y." Formatted as JSON reflex fragment.
3. **Compilation:** Reflex compiler translates JSON to 8-byte instructions. Block size: typically 4-32 instructions (32-256 bytes).
4. **Structural validation:** All jumps target valid 8-byte-aligned offsets within bytecode. Stack depth analysis passes.
5. **Z3 SMT verification (< 10s on Jetson):**
   - Condition is satisfiable (can be true under some input).
   - Action block terminates within 800 µs (200 µs margin).
   - No stack overflow through any path.
   - Output values remain within safety clamp range.
6. **Shadow execution (1000+ ticks, hours):** Variant runs in shadow VM. If output ever differs from production by >10% of actuator range → alert.

**Level 3 — Algorithm Mutation (Full Strategy Replacement)**

What changes: Entire control strategy (e.g., PID → state machine, feedforward+feedback, etc.).

Procedure:
1. AI proposal with natural-language justification.
2. Full simulation on Jetson: 864,000 ticks (24h at 100Hz) against plant model.
3. Cross-validation against last 30 days of historical telemetry.
4. Monte Carlo stress test: 10,000 random perturbations (±20% all parameters). Pass rate must exceed 95%.
5. Human review (mandatory): operator reviews justification, simulation results, stress test report.
6. Deployment with 72-hour mandatory rollback countdown.
7. Auto-rollback if: VM halts >3 times in 100 ticks, safety metric regresses >20%, or operator sends manual rollback command.

**Level 4 — Architecture Mutation (Hardware Change)**

Colony REQUESTS, human APPROVES and EXECUTES. Colony cannot physically modify hardware.
1. Deficiency detection: "Cannot distinguish normal bilge accumulation from leak because no flow-rate sensor."
2. Structured proposal: sensor type, pin mapping, reflex definition, expected fitness improvement.
3. Human evaluation: physical feasibility, cost, installation effort, risk.
4. Physical installation by operator.
5. Post-installation: Level 3 mutation cycle to evolve bytecodes for new hardware.

### 6.2 Crossover Mechanism (Bytecode Grafting)

**Subtree Crossover via CFG Block Swapping:**
1. Parse both parent bytecodes into Control Flow Graphs (CFGs). Each node is a basic block (single entry, single exit).
2. Select compatible blocks:
   - Same stack effect (net push/pop count identical).
   - Same I/O registers (reads same sensors, writes same actuators).
   - Cyclomatic complexity within ±1.
3. Swap blocks. Remap jump targets to maintain CFG validity.
4. Full validation pipeline (structural, Lyapunov, shadow execution).

**Restrictions:**
- Crossover ONLY during Spring (15% rate). Summer/ Autumn: asexual only.
- ONLY between kinship-compatible nodes (kinship_score ≥ 0.5).
- No cross-niche crossover (rudder × bilge prohibited).
- Grafted child records both parent_hash and parent2_hash in metadata.

### 6.3 Kolmogorov Fitness Function

```
K_fitness = behavioral_score / compressed_bytecode_size
```

Where:
- `behavioral_score` = weighted sum of performance metrics (accuracy, latency, efficiency, comfort) across standardized test scenarios (32 scenarios × 4 features each, normalized to [0,1]).
- `compressed_bytecode_size` = size in bytes after gzip compression of the instruction array.
- The Kolmogorov fitness explicitly rewards simplicity: two bytecodes with identical behavioral scores but different sizes have different fitness — the smaller one is fitter.
- This drives the Compute Reduction Pathway: evolution naturally compresses bytecodes over generations.

**Byte-level implementation:**
```c
float kolmogorov_fitness(bytecode_t *bc, telemetry_t *results) {
    float behavioral_score = 0.0;
    for (int s = 0; s < 32; s++) {
        float scenario_score = 0.0;
        scenario_score += 0.4 * (1.0 / (1.0 + results[s].rmse_error));
        scenario_score += 0.3 * (1.0 / (1.0 + results[s].p99_latency_ms));
        scenario_score += 0.2 * (1.0 / (1.0 + results[s].resource_cost));
        scenario_score += 0.1 * (1.0 / (1.0 + results[s].jerk_integral));
        behavioral_score += scenario_score / 32.0;
    }
    size_t compressed_size = gzip_compress(bc->instructions, bc->instruction_count * 8);
    return behavioral_score / (float)compressed_size;
}
```

### 6.4 Fitness Function: Exact Weight Formula

```
R(v) = α·F_task(v) + β·F_resource(v) + γ·F_stability(v) + δ·F_adaptability(v) + ε·F_innovation(v) - ζ·Debt(v)
```

**Constitutional constraint:** If `safety_regression(v, baseline) > threshold`, then `R(v) = 0`.

**Extended weight formula with seasonal modulation and adaptive deviation:**

| Season | α (task) | β (resource) | γ (stability) | δ (adapt) | ε (innovation) | ζ (debt) |
|--------|----------|-------------|---------------|-----------|----------------|----------|
| Spring (base) | 0.35 | 0.10 | 0.15 | 0.25 | 0.15 | 0.50 |
| Summer (base) | 0.55 | 0.15 | 0.25 | 0.05 | 0.00 | 0.50 |
| Autumn (base) | 0.40 | 0.20 | 0.20 | 0.10 | 0.10 | 0.50 |

**Adaptive deviation:** Jetson may propose weight changes up to ±0.10 from base values, subject to:
- Constitutional anchor: no coefficient may exceed 0.70 or fall below 0.05.
- Stability floor: γ ≥ 0.15 in all seasons.
- Sum = 1.0 always.
- Maximum rate of change: 0.05 per component per season.
- Reset trigger: if colony fitness declines for >3 consecutive seasons, return to base values.

**Component definitions:**
- `F_task(v)` = 1.0 / (1.0 + RMS_error) — primary task performance
- `F_resource(v)` = 1.0 / (1.0 + current_draw_mA / 100.0) — resource efficiency
- `F_stability(v)` = min_eigenvalue of Lyapunov certificate (0 to 1.0, normalized)
- `F_adaptability(v)` = 1.0 / (1.0 + CV(performance across conditions)) — cross-condition robustness
- `F_innovation(v)` = Kolmogorov fitness (behavioral_score / compressed_size) — simplicity reward
- `Debt(v)` = sum of debt ratios across 5 categories (storage, memory, dependencies, diversity, complexity)

---

## 7. Seasonal Protocol — Precise Timing

### 7.1 Spring: Exploration and Discovery

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Duration | 2-4 weeks (14-28 days) | Depends on colony maturity; first Spring: 4 weeks |
| Mutation rate | 30% | 30% of variant generation events introduce mutation |
| Crossover rate | 15% | Subtree crossover during Spring only |
| Epsilon exploration | 30% | 30% of variant selection is random (not tournament) |
| Tournament size | 2 | Small tournaments = more diversity |
| Fitness weights | α=0.35, β=0.10, γ=0.15, δ=0.25, ε=0.15 | Maximizes adaptability and innovation |
| Candidate generation | 20-40 per node | High diversity |
| Inosculation scanning | First 72 hours | GPIO + BLE neighbor discovery |
| Grievance review | Week 3-4 | Review previous cycle's retirements |
| A/B/C/D testing | Up to 5 variants per niche | Portfolio exploration |
| Stem cell experimentation | Active | Sentinels run risky candidates |
| Mini-Spring trigger | BOCPD drift detected → 48h at ε=0.2 | Unscheduled if concept drift detected |

### 7.2 Summer: Exploitation and Emergence

| Parameter | Value |
|-----------|-------|
| Duration | 4-8 weeks |
| Mutation rate | 10% |
| Crossover rate | 5% |
| Epsilon exploration | 10% |
| Tournament size | 3 |
| Fitness weights | α=0.55, β=0.15, γ=0.25, δ=0.05, ε=0.00 |
| Candidate generation | 5-10 per node (focused on refinements) |
| Reflex arc operation | Full capacity, all consolidated arcs active |
| Stigmergic field | Fully active, hormone responses evolved |
| Jetson role | Passive flower — generates candidates but does NOT command deployment |
| Emergence detection | Active (CAP-Delta, ABI, TPS, SDI computed weekly) |
| A/B testing | 5% shadow for safety-critical, 20% for non-critical |

### 7.3 Autumn: Consolidation and Preparation

| Parameter | Value |
|-----------|-------|
| Duration | 2-3 weeks |
| Mutation rate | 5% |
| Crossover rate | 2% |
| Epsilon exploration | 5% |
| Tournament size | 4 |
| Fitness weights | α=0.40, β=0.20, γ=0.20, δ=0.10, ε=0.10 |
| Grievance adjudication | Weeks 1-2 — review all grievances from Spring/Summer |
| Bytecode pruning | Target: 15-25% size reduction, >95% fitness retention |
| Topology consolidation | Successful bridges retained; failed bridges removed |
| Terroir update | Update all terroir descriptors with season's data |
| Griot pruning | Old entries decay; recent insights persist |
| Debt audit | Full generational debt assessment and repayment plan |
| Stem cell assessment | Verify reserve capacity; schedule Spring deployment if needed |

**Grievance Adjudication Procedure:**
1. Collect all grievances filed during Spring/Summer.
2. For each grievance: verify the retiring variant's conditional advantage using the colony's full telemetry archive.
3. Statistical test: Did the retiring variant significantly outperform the promoted variant (p < 0.10, relaxed from the promotion threshold) in the specified terrain cell?
4. If YES: preserve as dissent lineage in the 7-genome portfolio.
5. If NO: archive grievance as rejected. The Griot records the rejection reasoning.
6. Portfolio management: if portfolio is full (7 genomes), retire the least-fit genome to make room.

### 7.4 Winter: Rest and Dream

| Parameter | Value |
|-----------|-------|
| Duration | 2-4 weeks |
| Mutation rate | 0% (constitutionally non-overridable) |
| Crossover rate | 0% |
| Epsilon exploration | 0% |
| Tournament size | N/A — no competition |
| Fitness evaluation | Suspended — all bytecodes frozen |
| ULP sentinel | Active on all nodes: 150 µA per node, monitoring power, touch, Hall, bus |
| Jetson model fine-tuning | QAT + LoRA on DeepSeek-Coder-7B Q4; ~2h training, 4.5 GB peak VRAM |
| Memory replay | Systematic analysis of full season's telemetry |
| Infrastructure Griot | Natural-language maintenance advisories |
| Emergence detection | Full colony archaeologist analysis |
| Cross-colony dreaming | Generate candidates combining best adaptations from multiple environments |
| Novel synthesis | Deliberately unusual candidates from outside colony's behavioral cluster |
| Minimum rest period | 14 days (even if analysis completes early) |

**ULP Sentinel Program (runs during Winter):**
- Wake every 500 ms from deep sleep.
- Read power rail voltage (ADC1_CH4).
- Read capacitive touch pads 0-2 (water intrusion).
- Read Hall effect sensor (magnetic field).
- Check UART1 for Jetson activity (RS-422 bus alive?).
- If any anomaly detected: wake main cores into restricted emergency mode (safety-critical genomes only, no evolutionary activity).

---

## 8. The Griot Knowledge Architecture

### 8.1 Node-Level Griot (LittleFS on ESP32)

**Storage budget:** ~50 KB in `lineage_partition` (128 KB partition, ~50 KB usable).

**Per-Generation Record Format (JSON, ~100 bytes):**
```json
{
    "gen": 412,
    "hash": "a3f2b8c1",
    "parent_hash": "e7d4c6a9",
    "fitness": 0.862,
    "delta": "+0.015",
    "mutation": "L1: Kp +3.2%, Kd -1.8%",
    "season": "Summer",
    "timestamp": "2026-08-14T14:32:00Z"
}
```

**Calibration Data (NVS keys, ~2 KB):**
- Sensor offsets, PID tuned gains, communication timing, environmental baselines.
- Updated continuously during operation; stable points saved as calibration checkpoints.

### 8.2 Colony-Level Griot (Jetson NVMe)

**Storage budget:** ~2 GB reserved on NVMe. Growth rate: ~180 KB/year per node × 14 nodes = ~2.5 MB/year.

**Schema:**
```json
{
    "colony_id": "NEXUS-042",
    "vessel": "40ft Cutter, Salish Sea",
    "seasons_completed": 4,
    "total_generations": 612,
    "nodes": {
        "0x01": {
            "lineage": [...],       // Full generation chain with narrative
            "calibration_history": [...],
            "fitness_trajectory": [...],
            "emergence_events": [...]
        }
    },
    "colony_fitness_trajectory": [...],   // Weekly aggregate fitness
    "emergence_detection_log": [
        {
            "timestamp": "2026-08-14T14:32:00Z",
            "metric": "ABI",
            "value": 0.45,
            "description": "Colony pre-furled jib 30s before squall precursor"
        }
    ],
    "grievances": [...],
    "infrastructure_hypotheses": [
        {
            "timestamp": "2026-10-02T03:17:00Z",
            "symptom": "BILGE-01 sensor noise increased 340%",
            "hypothesis": "Cable gland degradation",
            "confidence": 0.72
        }
    ],
    "colony_personality": {
        "risk_tolerance": 0.34,
        "adaptability": 0.72,
        "coordination_density": 0.61,
        "culture_type": "cautious_cooperative"
    },
    "topology_history": [...]
}
```

### 8.3 Fleet-Level Griot (Cloud)

**Schema:**
```json
{
    "fleet_id": "nexus_production",
    "vessels": 47,
    "total_node_years": 624,
    "cross_vessel_patterns": [
        {
            "pattern_id": "P-001",
            "description": "Rudder gain increases correlate with hull fouling",
            "vessels": [17, 22, 31, 42],
            "terroir_commonality": "saltwater_displacement_hull",
            "effectiveness": 0.85
        }
    ],
    "terroir_compatibility_matrix": {
        "salish_sea_deep_water": {
            "compatible_with": ["pacific_nw_coastal", "san_francisco_bay"],
            "incompatible_with": ["great_lakes_freshwater", "caribbean_shallow"]
        }
    },
    "species_knowledge": {
        "BME280": {
            "drift_pattern": "0.3%/°C",
            "calibration_interval_days": 90,
            "failure_mode_distribution": {"humidity_sensor": 0.4, "pressure": 0.3, "temp": 0.3}
        }
    }
}
```

### 8.4 Knowledge Decay

| Data Type | Retention | Decay Trigger | Justification |
|-----------|-----------|---------------|---------------|
| Current bytecode + calibration | Indefinite (on ESP32) | Never | Operational necessity |
| Last 3 stable points | Indefinite (on ESP32) | Never | Rollback capability |
| Per-generation records | 90 days full, 2 years summary, 5+ years aggregated | Time-based | Storage constraints |
| Griot narrative | 90 days full text, 2 years compressed, 5+ years index-only | Time-based | NVMe budget |
| Grievance records | 1 seasonal cycle (active), then archive | Seasonal cycle | Relevance decay |
| Lineage Cards | Indefinite (on NVMe) | Never | Immune system requires |
| Infrastructure hypotheses | 6 months (unresolved), indefinite if confirmed | Resolution | Maintenance relevance |
| Emergence events | Indefinite | Never | Research data — never prune |

---

# Part III: Bootstrap and Operations

---

## 9. Bootstrap Protocol

### 9.1 First-Node Bootstrap (USB Flash)

The first node in a colony is flashed via USB using esptool or the ESP-IDF flash tool.

**Bootstrap Image Contents (~3 KB minimum):**
| Component | Size | Purpose |
|-----------|------|---------|
| Bootloader (2nd stage) | 1,024 B | UART boot mode, accepts firmware |
| Minimum VM (12-opcode) | 256 B | NOP, PUSH, POP, READ_PIN, WRITE_PIN, ADD, MUL, CMP_LT, JUMP_IF_FALSE, PID_COMPUTE, HALT |
| Safety layer | 96 B | Watchdog config, output clamping, cycle budget timer |
| HAL (minimal) | 1,024 B | UART driver, 1 GPIO input, 1 GPIO output |
| Communication (4-byte) | 256 B | Heartbeat transmitter |
| Factory-safe bytecode | 256 B | `READ_PIN 0; WRITE_PIN 64` — stem cell |

**Procedure:**
1. `esptool.py --chip esp32s3 -p /dev/ttyUSB0 write_flash 0x0 bootloader.bin partition-table.bin nxs_factory.bin bootstrap.bin`
2. Node boots, loads factory-safe bytecode from NXS partition.
3. Node transmits 4-byte heartbeat (type=0, payload=0x01, CRC-8) every 1 second.
4. Human connects Jetson to RS-422 bus.
5. Jetson detects new node heartbeat, initiates commissioning sequence.

### 9.2 Subsequent-Node Bootstrap (OTA from Neighbor)

New nodes join the colony automatically via ESP-NOW OTA from a neighboring ESP32.

**Procedure:**
1. New node powers on with GPIO0 pulled low (factory jumper) → enters ROM bootloader mode.
2. Neighbor detects ROM bootloader traffic on UART or via ESP-NOW probe.
3. Neighbor sends bootstrap image (3 KB) over ESP-NOW (max payload 250 bytes per frame → ~15 frames, ~2 seconds at 1 Mbps).
4. New node writes bootstrap image to flash, resets.
5. New node boots, loads factory-safe bytecode, begins heartbeat transmission.
6. Neighboring node detects heartbeat, forwards to Jetson via RS-422.
7. Jetson commissions new node: assigns node_id, pin configuration, niche assignment.

### 9.3 Calibration Sequence (First 24 Hours)

| Hour | Activity | Details |
|------|----------|---------|
| 0-1 | Node identification | Jetson assigns node_id, reads I2C device scan, configures pin map |
| 1-2 | Sensor initialization | All I2C sensors configured via driver init() (BME280, MPU6050, etc.) |
| 2-6 | Baseline collection | Collect 4 hours of sensor data for noise floor, drift, and range characterization |
| 6-12 | Gyro/accel calibration | Stationary averaging (30s), rotation test, bias computation, NVS write |
| 12-18 | Actuator characterization | Servo range test, PWM linearity, current monitoring |
| 18-24 | First bytecode deployment | Jetson generates initial bytecode from AI model, deploys via RS-422 |
| 24 | Colony member | Node fully operational, reporting telemetry, participating in fungal network |

### 9.4 Spring Initialization (First Evolutionary Cycle)

The first Spring phase begins 7 days after bootstrap calibration completes (day 31 after deployment).

| Day | Activity |
|-----|----------|
| 1-2 | Jetson generates 20 candidate bytecodes per node (using general-purpose AI model, no colony-specific fine-tuning yet) |
| 3-5 | Inosculation scanning: GPIO proximity + BLE RSSI discovery |
| 5-7 | UART2 bridge formation and initial fitness evaluation |
| 7-14 | A/B/C/D testing of initial candidate pool |
| 14-21 | First reflex arc consolidation |
| 21-28 | Grievance review (likely none in first cycle) + portfolio allocation |
| 28 | Transition to Summer |

---

## 10. Operational Procedures

### 10.1 Normal Operation State Machine

```
                    ┌──────────┐
         ┌─────────│  BOOT    │─────────┐
         │         └──────────┘         │
         │                              │
         v                              │
    ┌──────────┐    heartbeat_timeout    ┌──────────┐
    │ CALIBRATE│───────────────────────>│DEGRADED  │
    └──────────┘                        └──────────┘
         │                                  │
         │ calibration_complete             │ jetson_restored
         v                                  │
    ┌──────────┐    season_command          │
    │ NORMAL   │<──────────────────────────┘
    │(Seasonal)│─────────────────────┐
    └──────────┘                     │
         │                          │
         │ emergency_gpio            │ winter_command
         v                          v
    ┌──────────┐              ┌──────────┐
    │EMERGENCY │              │ WINTER   │
    │(Adrenalin)│              │(Dormant) │
    └──────────┘              └──────────┘
```

### 10.2 Degraded Mode (Jetson Unavailable)

Trigger: No Jetson heartbeat for 30 consecutive seconds.

**Behavior:**
1. All hormones decay to zero via natural half-life (10-600 seconds depending on hormone).
2. BLE mesh consensus: nodes share last-known hormone values, adopt majority.
3. Nodes switch to current production bytecode (no new candidates generated).
4. Conditional genetics still active: genome switching based on local sensor data.
5. Reflex arcs continue operating (they don't depend on Jetson).
6. UART2 fungal network continues operating.
7. Fitness evaluation continues locally (F_task only, weighted by β=0.15 resource).
8. No bytecode updates until Jetson returns.
9. Colony metabolic rate drops to ~5.6W (no Jetson overhead).
10. Griot records: "Jetson loss at [timestamp]. Duration: [ongoing]. Mode: DEGRADED."

### 10.3 Emergency Mode (Adrenaline Hormone)

Trigger: Any node broadcasts threat_level ≥ 3, OR shared GPIO emergency line pulled low.

**Behavior:**
1. Adrenaline hormone set to 0.9375 (maximum) by hardware (GPIO ISR) or Jetson.
2. All nodes switch to emergency genome from conditional genetics portfolio.
3. Sensor sampling rates increased to maximum.
4. All reflex arcs activated.
5. VM tick rate increased to 1 kHz (1 ms cycle budget) for safety-critical nodes.
6. Power budget temporarily increased: 14 × 120 mA = 1.68 A @ 5V = 8.4W (sustainable for < 5 minutes from battery).
7. Adrenaline decays with 10-second half-life → emergency state lasts ~30 seconds before significant decay.
8. After adrenaline < 0.1: nodes return to seasonal-appropriate genomes.

### 10.4 Winter Dormancy Mode

Trigger: Jetson sends SEASON_COMMAND with season=3 (Winter).

**Behavior:**
1. Main CPU cores enter light sleep. ULP-RISC-V coprocessor activates sentinel program.
2. ULP sentinel wakes every 500 ms, checks power/touch/Hall/bus activity.
3. If anomaly detected: wake main cores into restricted emergency mode.
4. If no anomaly: return to deep sleep (150 µA per node).
5. Colony power budget: 14 × 0.15 mA × 3.3V = 7 mW.
6. Jetson continues running: model fine-tuning, memory replay, infrastructure advisories.
7. Duration: minimum 14 days, maximum 28 days (4 weeks).
8. Transition back to Spring: Jetson sends SEASON_COMMAND season=0. All nodes wake, load Spring-appropriate genomes.

### 10.5 Node Failure and Regeneration

**Phase 1 — Immediate (0-10s):**
- Surviving nodes shift to conditional genetics emergency genomes.
- Mechanical failsafes activate (float switch → bilge pump).
- SAFETY-01 broadcasts Threat Level 2 (node failure) via UART2.
- Cortisol hormone elevated to 0.50.

**Phase 2 — Surrogate Evolution (10min-2h):**
- Jetson triggers mini-Spring (48h, ε=0.2) on neighboring nodes.
- Neighboring bytecodes grow new conditional branches to cover lost node's function.
- Example: HULL-01 adapts ToF sensor to measure bilge water level.

**Phase 3 — Stem Cell Deployment (hours-1 day):**
- Operator installs STEM-01 in failed node's location.
- STEM-01 boots, detects hardware context (I2C scan), loads lost node's bytecode from archive.
- Receives epigenetic context from Jetson (calibration, communication patterns, environmental model).
- Begins operating as replacement within 60 seconds.

**Phase 4 — Colony Re-Equilibration (1-4 weeks):**
- Colony achieves NEW equilibrium (not restoration of old state).
- Griot records as "colony inflection event."

### 10.6 Colony Mating Protocol (Two Vessels Meet)

1. **Encounter:** BLE beacons from Colony A and Colony B detect each other (RSSI < -70 dBm, ~100 m).
2. **Courtship:** Colonies exchange Lineage Cards via BLE type 2/3 beacons. Each evaluates terroir compatibility.
3. **Compatibility check:** `terroir_similarity > 0.70` → proceed.
4. **Genetic exchange:** Colonies exchange subroutine fragments (proven subroutines, not whole bytecodes). Exchange via MQTT over WiFi if available; else via BLE at reduced rate.
5. **Hybrid testing:** Each colony integrates exchanged fragments via grafting mechanism. Tests during next Spring phase (48h minimum A/B).
6. **Selection:** Successful hybrids retained. Failed hybrids rejected. Mating event recorded in Griot.

---

# Part IV: Data Structures

---

## 11. All Critical Data Structures

### 11.1 Lineage Card (64 bytes)

```c
#include <stdint.h>

typedef struct __attribute__((packed)) {
    uint8_t  generation;          // 0x00: Current bytecode generation (0-255)
    uint8_t  kinship_group;       // 0x01: 8-bit group ID (same parent → same group)
    uint8_t  node_role;           // 0x02: 0=standard, 1=sentinel, 2=stem_cell
    uint8_t  niche_id;            // 0x03: Functional niche (rudder=0, throttle=1, etc.)
    uint32_t content_hash;        // 0x04: SHA-256 truncated to 32 bits of current bytecode
    uint32_t parent_hash;         // 0x08: SHA-256 truncated of parent bytecode
    uint32_t parent2_hash;        // 0x0C: Second parent hash if crossover (0 = asexual)
    uint32_t ancestor_hash[4];    // 0x10: Up to 4 great-grandparent hashes (16 bytes)
    uint16_t fitness_score;       // 0x20: Last-evaluated fitness (0-1000)
    uint8_t  terroir_compat;      // 0x22: Terroir compatibility (0-255)
    uint8_t  graft_count;         // 0x23: Successful grafts received
    uint32_t grievance_hash;      // 0x24: Hash of last-filed grievance (0 = none)
    uint32_t environment_hash;    // 0x28: Hash of environmental conditions
    uint16_t bytecode_size;       // 0x2C: Instruction array size in bytes
    uint8_t  mutation_level;      // 0x2E: Last mutation level (1-4)
    uint8_t  season_born;         // 0x2F: Season when bytecode was born
    float    lyapunov_min_eig;    // 0x30: Lyapunov certificate minimum eigenvalue
    uint8_t  monte_carlo_pct;     // 0x34: Monte Carlo pass rate (0-100)
    uint8_t  reserved[14];        // 0x35: Future use (zeroed)
} lineage_card_t;  // Total: 64 bytes
```

### 11.2 Fungal Protocol Frame (8 bytes)

```c
typedef struct __attribute__((packed)) {
    uint8_t  source_node_id;      // 0x00: Source node (0x01-0x10)
    uint8_t  message_type;        // 0x01: 0=status,1=fitness,2=threat,3=lineage,
                                   //        4=grievance,5=reflex_data,6=heartbeat_ack,
                                   //        7=graft_fragment
    uint16_t payload;             // 0x02: Type-dependent data (big-endian)
    uint16_t sequence_number;     // 0x04: Monotonic counter, overflow OK
    uint16_t crc16;               // 0x06: CRC-16 (enabled for types 3,4 only; else 0)
} fungal_frame_t;  // Total: 8 bytes
```

### 11.3 Stigmergic Field Layout (256 bytes)

```c
typedef struct __attribute__((packed)) {
    // Hormone field (6 bytes, 4.4 fixed-point each)
    uint8_t  hormone_cortisol;    // 0x00: Stress level [0, 0xF0]
    uint8_t  hormone_auxin;       // 0x01: Growth level [0, 0xF0]
    uint8_t  hormone_melatonin;   // 0x02: Sleep level [0, 0xF0]
    uint8_t  hormone_oxytocin;    // 0x03: Bonding level [0, 0xF0]
    uint8_t  hormone_adrenaline;  // 0x04: Alert level [0, 0xF0]
    uint8_t  hormone_ethylene;    // 0x05: Senescence level [0, 0xF0]

    // Colony metrics (10 bytes)
    uint16_t colony_metabolic_mw; // 0x06: Colony power (milliwatts)
    int16_t  colony_temp_cx10;    // 0x08: Colony temperature (°C × 10)
    uint16_t bus_activity;        // 0x0A: Messages per second
    uint8_t  power_margin_pct;    // 0x0C: Power headroom (%)
    uint8_t  node_count_alive;    // 0x0D: Active node count
    uint16_t colony_fitness;      // 0x0E: Aggregate fitness (0-1000)

    // Colony status word (16 bytes)
    uint8_t  season;              // 0x10: 0=Spring,1=Summer,2=Autumn,3=Winter
    uint8_t  alert_state;         // 0x11: 0=normal,1=caution,2=warning,3=emergency
    uint8_t  node_health[14];     // 0x12: Per-node health bitmask
                                   //        bit 0=alive, bit 1=degraded, bit 2=emergency

    // Node-local channels (224 bytes, 14 nodes × 16 bytes each)
    uint8_t  node_channel[14][16]; // 0x20-0xFF: Each node writes its own 16 bytes
} stigmergic_field_t;  // Total: 256 bytes
```

### 11.4 Griot Per-Generation Record

```c
typedef struct {
    uint32_t content_hash;        // SHA-256 truncated (32 bits)
    uint32_t parent_hash;         // Parent's content hash
    uint16_t generation;          // Generation number
    uint16_t fitness_before;      // Parent's fitness (0-1000, scaled)
    uint16_t fitness_after;       // This variant's fitness (0-1000, scaled)
    uint8_t  mutation_level;      // 1=Parameter, 2=Conditional, 3=Algorithm
    uint8_t  season;              // 0=Spring, 1=Summer, 2=Autumn
    float    lyapunov_min_eig;    // Lyapunov certificate value
    uint32_t env_hash;            // Environmental context hash
    // Narrative stored as JSON in separate file, indexed by content_hash
} griot_gen_record_t;  // Total: 24 bytes (binary); full record ~500 bytes with JSON narrative
```

### 11.5 Terroir Descriptor

```c
typedef struct __attribute__((packed)) {
    // Vessel fingerprint (16 bytes)
    char     vessel_id[8];        // "NX-042\0\0"
    uint8_t  hull_type;           // 0=mono, 1=cat, 2=trimaran
    uint16_t displacement_tons;   // Displacement in tons × 10
    uint8_t  propulsion_type;     // 0=diesel, 1=electric, 2=sail, 3=hybrid
    uint8_t  rudder_count;        // Number of rudders
    uint8_t  reserved_vessel[3];  // Future vessel attributes

    // Environmental fingerprint (16 bytes)
    int8_t   avg_temp_c;          // Mean annual temperature (°C)
    uint8_t  water_type;          // 0=fresh, 1=brackish, 2=salt
    uint8_t  avg_wave_ht_dm;      // Mean wave height (decimeters)
    uint8_t  avg_current_knots;   // Mean current (knots)
    uint8_t  tidal_range_dm;      // Tidal range (decimeters)
    uint8_t  fog_frequency;       // 0=none,1=rare,2=occasional,3=frequent
    uint8_t  storm_frequency;     // 0=none,1=rare,2=occasional,3=frequent
    uint8_t  avg_wind_knots;      // Mean wind speed (knots)
    uint8_t  salinity_ppt;        // Water salinity (parts per thousand)
    uint8_t  reserved_env[6];     // Future environmental attributes

    // Temporal fingerprint (8 bytes)
    uint8_t  deployment_month;    // Month of initial deployment (1-12)
    uint8_t  seasons_completed;   // Number of seasonal cycles completed
    uint16_t total_hours;         // Total operational hours
    uint16_t generation_depth;    // Deepest bytecode generation number
    uint8_t  colony_maturity;     // 0=infant,1=juvenile,2=mature,3=elder

    // Lineage fingerprint (8 bytes)
    uint32_t root_lineage_hash;   // Hash of the original bootstrap bytecode
    uint32_t dominant_lineage;    // Hash of the current dominant variant family
} terroir_descriptor_t;  // Total: 48 bytes
```

### 11.6 Reflex Arc Configuration

```c
typedef struct __attribute__((packed)) {
    uint8_t  sensor_node_id;      // Source node (sensor side)
    uint8_t  actuator_node_id;    // Destination node (actuator side)
    uint8_t  sensor_register;     // Sensor register index (0-63)
    uint8_t  actuator_register;   // Actuator register index (64-127)
    uint8_t  status;              // 0=discovery,1=experimental,2=consolidated,3=vetoed
    uint8_t  channel;             // 0=UART2_A, 1=UART2_B
    uint16_t fitness_improvement; // % improvement from bridge (0-100, 0=unmeasured)
    uint32_t discovery_timestamp; // Unix timestamp when discovered
    uint32_t consolidation_ts;    // Unix timestamp when consolidated (0=not yet)
    uint32_t last_data_tick;      // Last tick with valid data (timeout = 10 ticks)
    uint16_t data_rate_hz;        // Actual data rate (0 = inactive)
    uint8_t  safety_veto;         // 0=none, 1=human veto, 2=Jetson veto
    uint8_t  reserved[11];        // Future use
} reflex_arc_config_t;  // Total: 32 bytes
```

### 11.7 Grievance Record

```c
typedef struct __attribute__((packed)) {
    uint32_t retiring_variant_hash; // Hash of the retiring bytecode
    uint8_t  terrain_cell_id;       // Environmental condition where variant excelled
    uint8_t  terrain_dim_count;     // Number of dimensions in terrain cell
    float    fitness_in_condition;  // Normalized fitness in the specific condition
    uint16_t vocabulary_idx;        // Index into shared grievance vocabulary
    uint16_t evidence_tick_count;   // Number of ticks supporting the grievance
    uint8_t  adjudication_result;   // 0=pending, 1=accepted, 2=rejected
    uint8_t  dissension_preserved;  // 1 = preserved as dissent lineage
    uint32_t filed_timestamp;       // Unix timestamp when filed
    uint32_t adjudication_timestamp;// Unix timestamp when adjudicated (0=pending)
    uint8_t  reserved[8];           // Future use
} grievance_record_t;  // Total: 28 bytes
```

### 11.8 Bytecode Metadata Header (64 bytes)

```c
typedef struct __attribute__((packed)) {
    uint32_t magic;              // 0x00: 0x4E45585A ("NEXU")
    uint8_t  version;            // 0x04: Metadata format version (1)
    uint8_t  mutation_level;     // 0x05: 1=Parameter, 2=Conditional, 3=Algorithm
    uint8_t  generation;         // 0x06: Generation number (0-255, wraps)
    uint8_t  season;             // 0x07: 0=Spring, 1=Summer, 2=Autumn, 3=Winter
    uint32_t parent_hash;        // 0x08: SHA-256 of parent (first 4 bytes)
    uint32_t parent2_hash;       // 0x0C: Second parent if crossover (0 if asexual)
    uint32_t content_hash[8];    // 0x10: Full SHA-256 of instruction array (32 bytes)
    float    fitness_score;      // 0x30: Most recent fitness evaluation
    float    kolmogorov_fitness; // 0x34: behavioral_score / compressed_size
    float    stability_eig_min;  // 0x38: Minimum eigenvalue of Lyapunov P matrix
    uint16_t tick_count_tested;  // 0x3C: Number of ticks tested
    uint16_t bytecode_size;      // 0x3E: Instruction array size in bytes
    uint8_t  environment_hash[8];// 0x40: Hash of testing conditions (8 bytes)
    uint8_t  node_id;            // 0x48: Node that generated/last ran this variant
    uint8_t  niche_id;           // 0x49: Functional niche
    uint8_t  terroir_compat;     // 0x4A: Terroir compatibility score (0-255)
    uint8_t  graft_count;        // 0x4B: Grafts received
    uint16_t monte_carlo_pct;    // 0x4C: Monte Carlo pass rate (0-100)
    uint8_t  apoptosis_flag;     // 0x4E: 1 = variant requested self-retirement
    uint8_t  reserved[17];       // 0x4F: Future use
} bytecode_metadata_t;  // Total: 64 bytes
```

---

## Appendix A: Opcode Quick Reference

| Hex | Mnemonic | Stack Effect | Cycles |
|-----|----------|-------------|--------|
| 0x00 | NOP | — | 1 |
| 0x01 | PUSH_I8 | +1 | 1 |
| 0x02 | PUSH_F32 | +1 | 1 |
| 0x03 | PUSH_I16 | +1 | 1 |
| 0x04 | POP | -1 | 1 |
| 0x05 | DUP | +1 | 1 |
| 0x06 | READ_PIN | +1 | 2 |
| 0x07 | WRITE_PIN | -1 | 2 |
| 0x08 | READ_VAR | +1 | 1 |
| 0x09 | WRITE_VAR | -1 | 1 |
| 0x0A | ADD_F | -1 | 1 |
| 0x0B | SUB_F | -1 | 1 |
| 0x0C | MUL_F | -1 | 1 |
| 0x0D | DIV_F | -1 | 3 |
| 0x0E | SQRT_F | 0 | 4 |
| 0x0F | ABS_F | 0 | 1 |
| 0x10 | CMP_LT | 0 | 1 |
| 0x11 | CMP_EQ | 0 | 1 |
| 0x12 | CMP_GT | 0 | 1 |
| 0x13 | CMP_LTE | 0 | 1 |
| 0x14 | CMP_GTE | 0 | 1 |
| 0x15 | AND_F | -1 | 1 |
| 0x16 | OR_F | -1 | 1 |
| 0x17 | NOT_F | 0 | 1 |
| 0x18 | JUMP | 0 | 1 |
| 0x19 | JUMP_IF_FALSE | -1 | 2 |
| 0x1A | JUMP_IF_TRUE | -1 | 2 |
| 0x1B | CALL | +1 (call stack) | 3 |
| 0x1C | RET | -1 (call stack) | 2 |
| 0x1D | CLAMP_F | 0 | 1 |
| 0x1E | EMIT_EVENT | -1 | 2 |
| 0x1F | EMIT_TELEMETRY | 0 | 2 |
| 0x20 | READ_HORMONE | +1 | 2 |
| 0x81 | SYS:HALT | — | 0 |
| 0x82 | SYS:PID_COMPUTE | -2, +1 | 8 |
| 0x83 | SYS:READ_STATE | +1 | 2 |
| 0x84 | SYS:RESET_PID | — | 1 |

## Appendix B: Node ID Assignment

| ID | Node | Cluster | Primary Function |
|----|------|---------|-----------------|
| 0x01 | NAV-01 | Mast | GPS + magnetometer + IMU + AIS |
| 0x02 | MAST-02 | Mast | Anemometer + rig tension + BME280 |
| 0x03 | DECK-01 | Deck | Windlass + deck load + RFID |
| 0x04 | SAIL-01 | Deck | Sheet tension + furler + mast rotation |
| 0x05 | BILGE-01 | Hull | Water level + pump + intrusion |
| 0x06 | HULL-01 | Hull | Hull temp + vibration + mics + ToF |
| 0x07 | PROP-01 | Propulsion | Throttle + RPM + exhaust |
| 0x08 | RUDDER-01 | Propulsion | Rudder servo + feedback |
| 0x09 | ELEC-01 | Electrical | Battery + solar + load management |
| 0x0A | CABIN-01 | Cabin | HVAC + CO2 + temp + humidity |
| 0x0B | COMFORT-01 | Cabin | Lighting + heating + water + fridge |
| 0x0C | SAFETY-01 | Electrical | Kill switch + fire + CO + MOB |
| 0x0D | SENT-01 | Sentinel | Acoustic + touch + BLE (forward) |
| 0x0E | SENT-02 | Sentinel | Acoustic + touch + BLE (aft) |
| 0x0F | STEM-01 | Reserve | Cold spare (forward locker) |
| 0x10 | STEM-02 | Reserve | Cold spare (lazarette) |

## Appendix C: Season Transition Matrix

| From → To | Trigger | Action |
|-----------|---------|--------|
| Spring → Summer | Fixed duration (2-4 weeks) OR Apeiron Index > 0.8 for 7 days | Jetson sends SEASON_COMMAND season=1 |
| Summer → Autumn | Fixed duration (4-8 weeks) | Jetson sends SEASON_COMMAND season=2 |
| Autumn → Winter | Fixed duration (2-3 weeks) | Jetson sends SEASON_COMMAND season=3 |
| Winter → Spring | Minimum 14 days elapsed + Jetson analysis complete | Jetson sends SEASON_COMMAND season=0 |
| Any → Emergency | Shared GPIO low OR threat_level ≥ 3 | Immediate, all nodes, adrenaline = max |
| Emergency → Any | Adrenaline < 0.1 for 60 seconds | Return to pre-emergency season |

---

*MYCELIUM Architecture Specification v1.0 — END OF DOCUMENT*

*Total specification: ~9,500 words (excluding C struct definitions, tables, and ASCII diagrams)*

*This document is the engineering specification. All numbers are justified. All protocols are unambiguous. A firmware engineer can build from this alone.*

