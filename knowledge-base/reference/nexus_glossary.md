# NEXUS Comprehensive Glossary

**Document ID:** NEXUS-KB-REF-GLOSSARY  
**Version:** 1.0  
**Date:** 2025-07-14  
**Total Terms:** 310  
**Classification:** Reference Document

> The definitive glossary for the NEXUS Edge-Native Distributed Intelligence Platform. Every technical term used across the NEXUS project, organized by category with definitions, NEXUS context, and cross-references.

---

## Table of Contents

1. [NEXUS-Specific Terms](#1-nexus-specific-terms)
2. [Hardware Terms](#2-hardware-terms)
3. [Software Architecture](#3-software-architecture)
4. [AI/ML Terms](#4-aiml-terms)
5. [Safety Terms](#5-safety-terms)
6. [Trust Terms](#6-trust-terms)
7. [Distributed Systems](#7-distributed-systems)
8. [Philosophical Terms](#8-philosophical-terms)
9. [Domain Terms](#9-domain-terms)
10. [A2A-Native Terms](#10-a2a-native-terms)

---

## 1. NEXUS-Specific Terms

### 1.1 Core Platform Concepts

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 1 | **NEXUS** | — | A production-ready specification for a distributed intelligence system designed for general-purpose industrial robotics, where operators wire hardware, describe intent in natural language, and approve AI-generated proposals. | The overarching platform spanning reflex, cognitive, and cloud tiers. No human writes, reads, or debugs code. | Reflex Layer, Cognitive Layer, Cloud Layer |
| 2 | **INCREMENTS** | — | The graduated autonomy framework with 6 levels per subsystem (L0–L5), governing how trust is earned, maintained, and lost over time. Features a 25:1 trust loss-to-gain ratio. | Each subsystem (steering, navigation, engine) independently earns autonomy through demonstrated reliability. | Trust Score, Autonomy Levels, alpha_gain, alpha_loss |
| 3 | **Post-Coding Age** | — | The paradigm shift where code is not written, read, or debugged by humans. AI agents generate bytecode from natural-language intent, and operators approve or reject proposals. | NEXUS's founding design philosophy. Operators describe intent; agents produce executable bytecode. | AAB, Intention Block, Agent-Native |
| 4 | **Ribosome Thesis** | — | The philosophical principle that NEXUS distributes cognition to the periphery rather than centralizing it. Each limb thinks, reacts, and learns independently, like cellular ribosomes. | The platform motto: "The Ribosome, Not the Brain." Reflex VMs on ESP32 nodes act as local cognitive units. | Reflex Layer, Edge AI, Distributed Intelligence |

### 1.2 AAB (Agent-Annotated Bytecode)

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 5 | **Agent-Annotated Bytecode** | AAB | An 8-byte core instruction followed by a TLV (Type-Length-Value) metadata trailer that describes the instruction's provenance, intention, and failure semantics for agent interpretation. | Extends the base 32-opcode bytecode with agent-readable metadata. The bytecode tells the VM *what* to do; AAB metadata tells other agents *why*. | Reflex VM, TLV, A2A-Native |
| 6 | **TLV Metadata** | TLV | Type-Length-Value encoding appended to AAB instructions carrying agent-interpretable annotations such as intention ID, provenance, and failure narrative. | Each AAB instruction can carry a TLV trailer describing its purpose, trust context, and expected behavior for other agents. | AAB, Agent-Annotated Bytecode |

### 1.3 Bytecode VM Opcodes (All 32)

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 7 | **NOP** | `0x00` | No operation. Advances PC by 8 bytes. Also serves as syscall carrier when flags bit 7 is set. | Alignment padding and syscall dispatch (HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT). | Syscall, Flags |
| 8 | **PUSH_I8** | `0x01` | Sign-extends an 8-bit signed immediate value to 32 bits and pushes it onto the data stack. | Used for small integer constants, state IDs, and boolean values. 1 cycle. | Stack Machine |
| 9 | **PUSH_I16** | `0x02` | Sign-extends a 16-bit signed immediate to 32 bits and pushes onto the data stack. | Used for medium-range integer constants and address offsets. 1 cycle. | Stack Machine |
| 10 | **PUSH_F32** | `0x03` | Pushes a 32-bit IEEE 754 single-precision float onto the data stack. | Used for PID gains, sensor thresholds, and actuator setpoints. 1 cycle. | IEEE 754, Stack Machine |
| 11 | **POP** | `0x04` | Discards the top value on the data stack (1 consumed, 0 pushed). | Used to discard intermediate values. Triggers ERR_STACK_UNDERFLOW if SP==0. | Stack Machine |
| 12 | **DUP** | `0x05` | Duplicates the top-of-stack value (0 consumed, 1 pushed). | Used when a value is needed multiple times. Triggers ERR_STACK_OVERFLOW if SP>=256. | Stack Machine |
| 13 | **SWAP** | `0x06` | Swaps the top two values on the stack. | Reorders operands for operations requiring specific ordering. | Stack Machine |
| 14 | **ROT** | `0x07` | Rotates the top three values: third-from-top moves to top. | Used for ternary operations. 2 cycles. | Stack Machine |
| 15 | **ADD_F** | `0x08` | Pops two floats, pushes their sum. | Core arithmetic for PID error accumulation, signal addition. 3 cycles. | Arithmetic Opcodes |
| 16 | **SUB_F** | `0x09` | Pops two floats, pushes second minus first (TOS1 - TOS). | PID error computation: setpoint - input. 3 cycles. | PID, Arithmetic Opcodes |
| 17 | **MUL_F** | `0x0A` | Pops two floats, pushes their product. | PID proportional/derivative scaling. 3 cycles. | Arithmetic Opcodes |
| 18 | **DIV_F** | `0x0B` | Pops two floats, pushes second divided by first. Division by zero returns 0.0f. | PID integral gain application. 4 cycles. No NaN/Inf trap. | Arithmetic Opcodes |
| 19 | **NEG_F** | `0x0C` | Negates the top-of-stack float via sign-bit flip (`XOR 0x80000000`). | Signal inversion, direction reversal. 1 cycle, bit-level operation. | Arithmetic Opcodes |
| 20 | **ABS_F** | `0x0D` | Replaces TOS with its absolute value via sign-bit clear (`AND 0x7FFFFFFF`). | Error magnitude computation. 1 cycle. | Arithmetic Opcodes |
| 21 | **MIN_F** | `0x0E` | Pops two floats, pushes the smaller. NaN returns the non-NaN operand. | Safety clamping, limit enforcement. 3 cycles. | Arithmetic Opcodes |
| 22 | **MAX_F** | `0x0F` | Pops two floats, pushes the larger. NaN returns the non-NaN operand. | Safety clamping, threshold selection. 3 cycles. | Arithmetic Opcodes |
| 23 | **CLAMP_F** | `0x10` | Clamps TOS to a range [lo, hi] using two immediate floats packed in operand2. | Actuator output limiting (e.g., servo position [-1.0, 1.0]). 3 cycles. | Safety Invariant, Output Clamping |
| 24 | **EQ_F** | `0x11` | Pops two floats; pushes 1 if equal, 0 otherwise. | State comparison, threshold detection. 3 cycles. | Comparison Opcodes |
| 25 | **LT_F** | `0x12` | Pops two floats; pushes 1 if TOS1 < TOS, 0 otherwise. | Below-threshold detection. 3 cycles. | Comparison Opcodes |
| 26 | **GT_F** | `0x13` | Pops two floats; pushes 1 if TOS1 > TOS, 0 otherwise. | Above-threshold detection. 3 cycles. | Comparison Opcodes |
| 27 | **LTE_F** | `0x14` | Pops two floats; pushes 1 if TOS1 ≤ TOS, 0 otherwise. | Within-bound checking. 3 cycles. | Comparison Opcodes |
| 28 | **GTE_F** | `0x15` | Pops two floats; pushes 1 if TOS1 ≥ TOS, 0 otherwise. | Minimum-value enforcement. 3 cycles. | Comparison Opcodes |
| 29 | **AND_B** | `0x16` | Bitwise AND of two stack values treated as integers. | Flag masking, bit-field manipulation. 1 cycle. | Logic Opcodes |
| 30 | **OR_B** | `0x17` | Bitwise OR of two stack values treated as integers. | Flag setting, bit-field combination. 1 cycle. | Logic Opcodes |
| 31 | **XOR_B** | `0x18` | Bitwise XOR of two stack values treated as integers. | Toggle bits, parity computation. 1 cycle. | Logic Opcodes |
| 32 | **NOT_B** | `0x19` | Bitwise NOT (complement) of TOS treated as integer. | Flag inversion. 1 cycle. | Logic Opcodes |
| 33 | **READ_PIN** | `0x1A` | Reads sensor register at index and pushes its value. Indices ≥ 64 read from variable space (VAR_0..VAR_255). | The primary input mechanism. Firmware populates sensor registers before each tick. 2 cycles. | Sensor Register, Variable Space |
| 34 | **WRITE_PIN** | `0x1B` | Pops a value and writes it to actuator register at index. Indices ≥ 64 write to variable space. | The primary output mechanism. Firmware drains actuator registers after each tick. 2 cycles. | Actuator Register, Variable Space |
| 35 | **READ_TIMER_MS** | `0x1C` | Pushes the current tick count in milliseconds since VM start (wraps at 2^32). | Time-based logic, elapsed-time computation. 2 cycles. | Tick, Timing |
| 36 | **JUMP** | `0x1D` | Unconditional jump to byte offset in operand2. With flags bit 3 set, acts as CALL (pushes return address). | State machine transitions, loop constructs. 1 cycle (2 for CALL). | Control Flow, CALL |
| 37 | **JUMP_IF_FALSE** | `0x1E` | Pops a value; jumps to target if the value is zero (false). | Conditional branching for if/else logic. 2 cycles. | Control Flow |
| 38 | **JUMP_IF_TRUE** | `0x1F` | Pops a value; jumps to target if the value is non-zero (true). | Conditional branching for threshold triggers. 2 cycles. | Control Flow |

### 1.4 Pseudo-Instructions / Syscalls

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 39 | **CALL** | — | Subroutine call pseudo-instruction. Implemented as JUMP with IS_CALL flag (flags bit 3). Pushes return address to internal call stack. | Enables reusable code blocks within reflex programs. Max call depth enforced. | JUMP, Call Stack, RET |
| 40 | **RET** | — | Return from subroutine. Pops call stack, restores PC and frame pointer. | Paired with CALL for structured subroutine usage. | CALL, Call Stack |
| 41 | **HALT** | — | Stops execution for the current tick. Implemented as NOP with SYSCALL flag and operand1=0x01. | Normal end-of-program sentinel. Always placed as last instruction in bytecode. | NOP, Syscall |
| 42 | **PID_COMPUTE** | — | Syscall (NOP flags=0x80, operand1=0x02) that computes PID output from setpoint and input on stack. Selects one of 8 PID controllers. | Core control operation. Stack: [setpoint, input] → [output]. 24 bytes of state per controller. | PID, Syscall |
| 43 | **RECORD_SNAPSHOT** | — | Syscall (operand1=0x03) that records a 128-byte VM state snapshot into a 16-slot circular buffer (2KB total). | Used for debugging, AI observation, and post-incident analysis. | Observation System |
| 44 | **EMIT_EVENT** | — | Syscall (operand1=0x04) that queues a timestamped event (event_id, event_data) into a 32-event ring buffer (256 bytes). | Generates events consumed by telemetry, logging, or higher-level behaviors. | Event Ring Buffer, Telemetry |

### 1.5 Wire Protocol Message Types (All 28)

| # | Term | Code | Definition | NEXUS Context | Cross-refs |
|---|------|------|------------|---------------|------------|
| 45 | **DEVICE_IDENTITY** | `0x01` | Boot announcement containing MAC address, chip type, firmware version, hardware capabilities, and supported message types. Sent N2J immediately after power-on. | First message any node sends. Enables Jetson to auto-discover topology. | Boot Sequence |
| 46 | **ROLE_ASSIGN** | `0x02` | Complete node role configuration (J2N). Assigns named role, pin I/O modes, reflex attachments, and telemetry intervals. | Defines each node's function in the vessel (e.g., "rudder_controller"). | Role Management |
| 47 | **ROLE_ACK** | `0x03` | Node's response to ROLE_ASSIGN (N2J). Includes accepted boolean, echoed role name, and optional rejection reason. | Confirms or rejects role assignment. | ROLE_ASSIGN |
| 48 | **SELFTEST_RESULT** | `0x04` | Power-on self-test results (N2J) including per-pin continuity, ADC reference check, I2C bus scan, and flash CRC. | Validates hardware integrity before entering operational mode. | Boot Sequence, POST |
| 49 | **HEARTBEAT** | `0x05` | Keep-alive message with no payload. Both directions. Default: node sends every 1000ms, Jetson every 5000ms. | Link health monitoring. Three missed heartbeats trigger failsafe escalation. | Heartbeat Escalation |
| 50 | **TELEMETRY** | `0x06` | Periodic sensor data snapshot (N2J) with timestamped readings from all configured inputs. Sent at rate defined in ROLE_ASSIGN. | Primary data channel for observation and cloud analysis. | Observation System |
| 51 | **COMMAND** | `0x07` | Actuator command (J2N). Sets pin state, drives PWM, starts/stops reflexes, or executes named actions. | How the Jetson directs node behavior. | COMMAND_ACK |
| 52 | **COMMAND_ACK** | `0x08` | Acknowledgement of COMMAND or any ack-required message (N2J). Contains echoed sequence_number, status enum, and optional result/error. | Reliability mechanism for critical messages. Retry on timeout. | Retry Policy |
| 53 | **REFLEX_DEPLOY** | `0x09` | Deploys a new reflex definition to the node (J2N). Includes trigger conditions, actions, priority, and timeout. Replaces previous reflex with same name. | How AI-generated control programs are loaded onto ESP32 nodes. | Hot-Loading, Reflex VM |
| 54 | **REFLEX_STATUS** | `0x0A` | Reports current state of all loaded reflexes (N2J): active/inactive/paused, trigger counts, last-fire timestamp, version hash. | Runtime monitoring of deployed reflex programs. | REFLEX_DEPLOY |
| 55 | **OBS_RECORD_START** | `0x0B` | Begins observation recording on the node (J2N). Specifies channels, sample rate, compression, and duration/buffer size. | Triggers high-rate data capture for pattern discovery. | Observation System |
| 56 | **OBS_RECORD_STOP** | `0x0C` | Stops an in-progress recording (J2N). Optionally finalizes data for transfer. | Ends data capture and prepares for dump. | OBS_RECORD_START |
| 57 | **OBS_DUMP_HEADER** | `0x0D` | Metadata describing an observation recording dump (N2J). Precedes OBS_DUMP_CHUNK messages. | Provides recording parameters and dataset checksum. | Observation System |
| 58 | **OBS_DUMP_CHUNK** | `0x0E` | A single chunk of binary observation data (N2J). 32-byte compressed frames with delta encoding support. | Bulk data transfer of recorded sensor data. | Binary Payload |
| 59 | **OBS_DUMP_END** | `0x0F` | Signals end of observation data dump (N2J). Contains CRC-32 of all chunk payloads concatenated. | Confirms complete data transfer. | OBS_DUMP_CHUNK |
| 60 | **IO_RECONFIGURE** | `0x10` | Dynamically changes pin parameters at runtime (J2N): pin mode, pull direction, ADC resolution, debounce, interrupt mode. | Does not change node role; modifies I/O configuration. | ROLE_ASSIGN |
| 61 | **FIRMWARE_UPDATE_START** | `0x11` | Initiates OTA firmware update (J2N). Specifies firmware size, chunk count, version string, and SHA-256 hash. | First message in the 3-phase OTA update sequence. | OTA |
| 62 | **FIRMWARE_UPDATE_CHUNK** | `0x12` | A single 512-byte binary chunk of firmware data (J2N) with chunk index header. | Second phase: bulk data transfer. | FIRMWARE_UPDATE_START |
| 63 | **FIRMWARE_UPDATE_END** | `0x13` | Finalizes OTA update (J2N). Triggers SHA-256 verification, update partition write, and reboot preparation. | Third phase: verification and activation. | OTA |
| 64 | **FIRMWARE_UPDATE_RESULT** | `0x14` | Reports OTA update outcome (N2J): success, hash mismatch, flash error, or reboot status. | Confirms whether update succeeded or requires rollback. | OTA |
| 65 | **ERROR** | `0x15` | Asynchronous error notification (N2J) containing error code, human-readable message, severity, and context. | All error reporting flows through this message type. 75 error codes defined. | Error Codes |
| 66 | **PING** | `0x16` | Latency measurement probe. Either direction. No payload. Receiver must respond with PONG. | Used for round-trip-time measurement and link diagnostics. | PONG |
| 67 | **PONG** | `0x17` | Response to PING. Echoes originating sequence_number. No payload. RTT = pong_arrival - ping_departure. | Latency measurement response. | PING |
| 68 | **BAUD_UPGRADE** | `0x18` | Requests node to switch baud rate (J2N). Includes target_baud. Both sides switch simultaneously after ACK. | Negotiates higher throughput after initial handshake. | RS-422 |
| 69 | **CLOUD_CONTEXT_REQUEST** | `0x19` | Requests observation data from node for cloud analysis (J2N). Specifies recording, time window, and format. | Bridges edge observation to cloud ML pipeline. | Cloud Layer |
| 70 | **CLOUD_RESULT** | `0x1A` | Results from cloud analysis returned to node (N2J). May contain updated reflex parameters, calibration values, or configuration adjustments. | Feedback loop from cloud inference back to edge control. | Cloud Layer, ML Pipeline |
| 71 | **AUTO_DETECT_RESULT** | `0x1B` | Results of automatic hardware detection (N2J): I2C bus scan, ADC probe results, and peripheral identification. Sent after DEVICE_IDENTITY. | Enables zero-configuration hardware discovery. | DEVICE_IDENTITY |
| 72 | **SAFETY_EVENT** | `0x1C` | Critical safety notification (N2J): kill-switch activation, overcurrent trip, watchdog timeout, thermal shutdown, or mechanical limit exceeded. | Highest-priority message. Triggers autonomous safe-state entry. | Safety System, Failsafe |

### 1.6 Safety Tiers & Seasonal Evolution

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 73 | **Safety Tier 1** | — | Hardware interlock layer: physical kill switch, overcurrent protection, MAX6818 watchdog, hardware-defined safe states. | Fastest response (µs), cannot be overridden by software. Always active. | Defense-in-Depth |
| 74 | **Safety Tier 2** | — | Firmware safety guard: ISRs (interrupt service routines) for kill-switch, watchdog feeding, current monitoring, output clamping. | Responds within microseconds. Preempts all application tasks. | ISR, Watchdog |
| 75 | **Safety Tier 3** | — | Supervisory task: FreeRTOS task at priority 24 monitoring heartbeat, task health, safety state machine transitions. | Monitors Tier 2 and application layer. Can trigger Tier 1 if needed. | Safety Supervisor |
| 76 | **Safety Tier 4** | — | Application control layer: the reflex VM and command processing. Not safety-rated; operates under constraint of Tiers 1–3. | All user-facing control logic runs here. Bounded by safety envelope. | Reflex VM |
| 77 | **Seasonal Evolution** | — | NEXUS's phased deployment model where autonomy grows through seasonal milestones (discovery → optimization → expansion → maintenance). | Each season has distinct trust, safety, and operational characteristics. | INCREMENTS, Trust Score |

### 1.7 Vessel & Equipment

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 78 | **Vessel** | — | The physical robotic platform (e.g., a marine vessel) that hosts all NEXUS nodes, sensors, and actuators. Defines the capability boundaries and physical constraints. | In A2A-native terms, the vessel is the "hardware platform" pillar. | Three Pillars, Equipment |
| 79 | **Equipment** | — | The runtime environment bridging bytecode and hardware. Comprises the OS, drivers, VM, and capability provider layer. | In A2A-native terms, equipment is the "runtime" pillar between system prompt (compiler) and vessel (hardware). | Three Pillars, Vessel |

---

## 2. Hardware Terms

### 2.1 Microcontrollers & Processors

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 80 | **ESP32-S3** | — | Espressif's dual-core 240MHz MCU with Xtensa LX7 cores, 512KB SRAM, 8MB PSRAM, 45 GPIO, BLE 5.0, and Wi-Fi. The Tier 1 "limbs" platform at $6–10/unit. | Runs the Reflex VM, safety system, wire protocol, and I/O polling on FreeRTOS. | Reflex Layer, Xtensa LX7 |
| 81 | **Xtensa LX7** | — | Cadence-designed 32-bit RISC processor core with 7-stage pipeline, configurable ISA extensions, windowed registers, and 256-bit vector instructions. | Core of the ESP32-S3. No hardware FPU; floating-point uses software emulation (20–50 cycles/op). | ESP32-S3, Software FPU |
| 82 | **Jetson Orin Nano Super** | — | NVIDIA's edge AI module with ARM Cortex-A78AE cores, 1024 CUDA cores, 32 Tensor cores, 67 TOPS INT8, 8GB LPDDR5, at $249. The Tier 2 "brains" platform. | Runs AI inference (Qwen2.5-Coder-7B, Whisper, Piper), pattern discovery, NLP, and MQTT cluster coordination. | Cognitive Layer, Cortex-A78AE |
| 83 | **Cortex-A78AE** | — | ARM's Automotive Enhanced core with RAS (Reliability, Availability, Serviceability) features, designed for ASIL-B/D functional safety. | Core of the Jetson Orin Nano Super. Provides hardware-level error detection for safety-critical workloads. | Jetson Orin Nano, ASIL |

### 2.2 Communication & Interface ICs

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 84 | **RS-422** | — | EIA/TIA-422-B full-duplex differential serial standard using twisted pairs. Supports up to 921,600 baud over 10m with Cat-5e cable. | NEXUS's physical wire protocol layer between Jetson and ESP32 nodes. 120Ω termination at each end. | Wire Protocol, THVD1500 |
| 85 | **THVD1500** | — | Texas Instruments 3.3V RS-422 transceiver IC supporting 50Mbps, auto-bias, and ±15kV ESD protection. | Recommended transceiver for NEXUS RS-422 links. DE hardwired HIGH, RE hardwired LOW. | RS-422 |
| 86 | **MAX6818** | — | Maxim Integrated 8-channel switch debouncer with watchdog timer. Provides hardware-level input debouncing and supervisory reset capability. | External hardware watchdog that the safety_watchdog FreeRTOS task feeds every 200ms. | Watchdog, Safety Tier 1 |

### 2.3 Memory & Storage

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 87 | **PSRAM** | — | External pseudo-static RAM connected via Octal SPI. ESP32-S3 has 8MB PSRAM at ~80MHz. Not DMA-capable. | Stores 5.5MB observation ring buffer, 1MB LittleFS reflex bytecode storage, 512KB telemetry buffers. | Memory Map, LittleFS |
| 88 | **SRAM** | — | On-chip static RAM. ESP32-S3 has 512KB split into SRAM0 (360KB, executable, DMA-capable), SRAM1 (64KB, DMA-only), and RTC regions. | FreeRTOS heap lives in SRAM0. DMA buffers must use SRAM1. PSRAM is NOT DMA-capable. | Memory Map |
| 89 | **LittleFS** | — | Lightweight file system designed for embedded systems with power-loss resilience, wear leveling, and small RAM footprint. | Stores reflex bytecode on PSRAM (1MB partition). Enables persistent reflex storage across reboots. | PSRAM, Hot-Loading |

### 2.4 Communication Protocols

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 90 | **UART** | — | Universal Asynchronous Receiver-Transmitter. Serial communication protocol for point-to-point data transfer. | UART0: debug console (115200); UART1: Jetson RS-422 link (921600); UART2: GPS/NMEA (4800–38400). | Wire Protocol |
| 91 | **I2C** | — | Inter-Integrated Circuit. Two-wire (SDA/SCL) synchronous serial bus for short-range peripheral communication at up to 400kHz. | I2C0: primary sensor bus (compass, IMU, OLED display); I2C1: secondary expansion bus. Shared via mutex. | Sensor Bus |
| 92 | **SPI** | — | Serial Peripheral Interface. Four-wire synchronous serial bus (MOSI/MISO/SCK/CS) for high-speed peripheral communication. | SPI2 (FSPI): external flash and PSRAM access at 80MHz QPI. | PSRAM, Flash |
| 93 | **GPIO** | — | General-Purpose Input/Output. Configurable digital pins for reading switches, driving LEDs, relays, and other digital peripherals. | 45 GPIO on ESP32-S3. Kill switch input, button inputs, LED outputs, relay drivers configured per ROLE_ASSIGN. | Digital I/O |
| 94 | **PWM** | — | Pulse Width Modulation. Technique for generating analog-like output by rapidly switching a digital pin on/off with variable duty cycle. | LEDC peripheral provides up to 8 PWM channels for motor/solenoid/LED control. Configurable frequency and duty. | LEDC |
| 95 | **DMA** | — | Direct Memory Access. Hardware mechanism for transferring data between peripherals and memory without CPU intervention. | 4 TX + 4 RX GDMA channels on ESP32-S3. ADC DMA writes to SRAM1; UART TX/RX uses DMA. PSRAM is NOT DMA-capable. | GDMA |
| 96 | **CAN** | — | Controller Area Network. Robust multi-master serial bus standard used in automotive and industrial applications for differential signaling. | ESP32-S3 has TWAI (CAN 2.0B) peripheral, reserved for future expansion in NEXUS. | TWAI |
| 97 | **ESP-NOW** | — | Espressif's proprietary connectionless 2.4GHz wireless protocol enabling direct device-to-device communication without Wi-Fi association overhead. | Sub-1ms latency, 250-byte payload, CCMP-128 encryption. Reserved for future inter-node wireless links. | Wireless |

### 2.5 Data Integrity

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 98 | **COBS** | — | Consistent Overhead Byte Stuffing. Framing encoding that eliminates 0x00 bytes from payload, using 0x00 as unambiguous frame delimiter. | All wire protocol frames are COBS-encoded. Worst-case 0.4% overhead. Self-synchronizing decoder. | Wire Protocol |
| 99 | **CRC-16** | — | 16-bit Cyclic Redundancy Check using polynomial 0x1021 (CCITT-FALSE). Detects data corruption in transmitted frames. | Appended to every wire protocol message before COBS encoding. Computed over header + payload. | Wire Protocol |

---

## 3. Software Architecture

### 3.1 Three-Tier Architecture

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 100 | **Reflex Layer** | Tier 1 | The real-time sensor polling, bytecode VM execution, and safety enforcement layer running on ESP32-S3 MCUs. Latency: 10µs–1ms. | Maintains control even when all higher tiers fail. Runs 6 FreeRTOS tasks at fixed priorities. | ESP32-S3, FreeRTOS |
| 101 | **Cognitive Layer** | Tier 2 | The AI inference, NLP chat, pattern discovery, and reflex compilation layer running on Jetson Orin Nano. Latency: 10–500ms. | Generates reflex bytecode from natural language. Runs LLMs and pattern discovery algorithms. | Jetson Orin Nano, AI Inference |
| 102 | **Cloud Layer** | Tier 3 | The heavy training, simulation, and fleet management layer accessed via Starlink/5G. Latency: seconds–hours. | Long-term pattern analysis, model training, fleet-wide coordination, simulation. | Starlink, Fleet Management |

### 3.2 Virtual Machine & Execution

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 103 | **Reflex VM** | — | NEXUS's stack-based bytecode virtual machine with 32 opcodes, 8-byte fixed instructions, ~3KB footprint, and <100µs per tick execution. | The security boundary for AI-generated code. No heap allocation, no GC, deterministic timing. | Bytecode, Opcodes |
| 104 | **Stack Machine** | — | A VM architecture where operations consume operands from and push results to a data stack, eliminating the need for register allocation. | NEXUS's VM is stack-based by deliberate design. Enables single-pass validation and deterministic timing. | Reflex VM |
| 105 | **Reflex** | — | An AI-generated control program compiled from JSON to bytecode and deployed on an ESP32 node. Expresses a control behavior (e.g., PID, state machine, threshold detector). | The fundamental unit of AI-generated control logic. Deployed via REFLEX_DEPLOY message. | REFLEX_DEPLOY, JSON Reflex |
| 106 | **Bytecode** | — | Compiled binary instruction format executed by the Reflex VM. Each instruction is exactly 8 bytes with opcode, flags, and two operand fields. | The runtime representation of all AI-generated control programs. Validated in a single linear pass. | Reflex VM |

### 3.3 Operating System & Runtime

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 107 | **FreeRTOS** | — | Free Real-Time Operating System. Preemptive priority-based RTOS kernel. ~9KB flash, ~4KB RAM minimum. MIT license. | Runs on every ESP32-S3 node. 6 tasks: safety_supervisor (P24), safety_watchdog (P23), serial_protocol (P20), reflex_vm (P15), telemetry (P10), io_poll (P8). | RTOS, Task Architecture |
| 108 | **Hot-Loading** | — | The ability to replace running reflex bytecode without stopping the control loop. The VM swaps bytecode between ticks so execution never sees inconsistent state. | Inspired by Erlang's hot code loading. New reflexes transmitted via wire protocol, validated, and activated between ticks. | OTA, REFLEX_DEPLOY |
| 109 | **OTA** | — | Over-the-Air update mechanism for deploying firmware and reflex bytecode to ESP32 nodes without physical access. | Three-phase: FIRMWARE_UPDATE_START → CHUNK → END with SHA-256 verification. | FIRMWARE_UPDATE_START |

### 3.4 Memory & Data

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 110 | **Zero-Heap Design** | — | NEXUS's design philosophy of eliminating all dynamic memory allocation from the runtime path. All buffers are statically allocated. | Prevents heap fragmentation, memory leaks, and allocation failures. The VM uses zero heap allocation. | Static Allocation |
| 111 | **5,280-Byte VM Budget** | — | The total RAM allocation for the Reflex VM: 256-entry data stack (1KB), 256-byte call stack, 16-entry variable space, 8 PID controllers (256B), 16 snapshots (2KB), 32-event ring buffer (256B), plus overhead. | Fits within ESP32-S3's SRAM with significant margin. Every byte is accounted for. | Memory Budget |

---

## 4. AI/ML Terms

### 4.1 Models & Frameworks

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 112 | **Qwen2.5-Coder-7B** | — | Alibaba's 7-billion parameter code generation model. The primary LLM used in NEXUS for generating JSON reflex definitions from natural-language intent. | Generates reflex JSON that a deterministic compiler translates to bytecode. Runs quantized on Jetson Orin Nano via llama.cpp. | Constrained Generation, GGUF |
| 113 | **GBNF Grammar** | — | Grammars for BNF (GBNF) format used to constrain LLM output to valid JSON schemas, ensuring generated reflexes conform to the NEXUS reflex specification. | Applied during inference to guarantee syntactically correct reflex JSON output. | Constrained Generation, JSON Reflex |
| 114 | **Phi-3-mini** | — | Microsoft's compact language model. Considered for edge inference scenarios where the 7B model is too large. | Evaluated as a potential lightweight alternative for resource-constrained cognitive nodes. | LLM, Edge AI |
| 115 | **Claude 3.5 Sonnet** | — | Anthropic's frontier LLM used during the research and dissertation phases of NEXUS for analysis, synthesis, and document generation. | Not deployed at runtime; used in the development and research workflow. | LLM, Research |
| 116 | **Whisper** | — | OpenAI's automatic speech recognition model for converting audio input to text. Enables voice-based operator interaction with the NEXUS system. | Runs on Jetson Orin Nano for speech-to-text, allowing operators to describe intent verbally. | Speech Recognition |
| 117 | **Piper** | — | An offline text-to-speech engine that converts NEXUS system messages and AI responses to spoken audio. | Enables the system to communicate status, alerts, and recommendations verbally. | TTS, Operator Interface |

### 4.2 Inference & Optimization

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 118 | **Constrained Generation** | — | Technique of restricting LLM output to a formal grammar (GBNF) during decoding, ensuring all generated text conforms to a specified schema. | Ensures Qwen2.5-Coder-7B always produces valid NEXUS reflex JSON, eliminating syntax errors. | GBNF, JSON Reflex |
| 119 | **Quantization** | Q4_K_M | Model compression technique that reduces neural network weights from higher precision to lower precision (e.g., FP16 → 4-bit integers). | NEXUS uses Q4_K_M quantization for Qwen2.5-Coder-7B, reducing model size ~4x with minimal quality loss. | GGUF, LLM |
| 120 | **GGUF** | — | GPT-Generated Unified Format. A file format for storing quantized LLM weights optimized for CPU/GPU inference via llama.cpp. | The format used to store and load quantized models on the Jetson Orin Nano. | llama.cpp, Quantization |
| 121 | **llama.cpp** | — | Open-source C/C++ library for running LLM inference on CPUs and GPUs with quantization support. No GPU required for basic inference. | Primary inference runtime for Qwen2.5-Coder-7B on the Jetson Orin Nano. | GGUF, Qwen2.5-Coder-7B |
| 122 | **TensorRT** | — | NVIDIA's high-performance deep learning inference optimizer and runtime. Compiles trained models into optimized execution engines. | Potential future optimization path for Jetson inference pipeline. Not yet used in NEXUS MVP. | TOPS, GPU |
| 123 | **TOPS** | — | Tera Operations Per Second. Metric for AI accelerator performance, measuring integer (INT8) or floating-point operations. | Jetson Orin Nano Super delivers 67 TOPS INT8. Three Orin Nano units ($750 total) provide 201 TOPS cluster. | Jetson Orin Nano |

### 4.3 Learning & Pattern Discovery

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 124 | **A/B Testing** | — | Experimental method comparing two versions (candidate vs. production) to determine which performs better. In NEXUS, reflex candidates are tested against production reflexes. | New AI-generated reflexes run in shadow mode alongside production reflexes. Performance comparison determines promotion. | Reflex Candidate, Trust Escalation |
| 125 | **Few-Shot** | — | Machine learning technique providing a small number of example input-output pairs to guide model inference. | Used when generating reflexes for novel control scenarios where limited examples exist. | Zero-Shot, Prompt Engineering |
| 126 | **Zero-Shot** | — | Machine learning technique where the model generates output without any task-specific examples, relying only on its training and the system prompt. | Default mode for NEXUS reflex generation when no prior examples of the target behavior exist. | Few-Shot |
| 127 | **System Prompt** | — | The foundational instruction set provided to an LLM that defines its behavior, constraints, and output format. In A2A-native terms, the "compiler frontend." | The NEXUS system prompt translates operator intent into bytecode by instructing the LLM on reflex schema and safety constraints. | Three Pillars, Compiler |
| 128 | **Cross-Correlation** | — | Statistical measure of similarity between two signals as a function of the time-lag applied to one. A pattern discovery algorithm in NEXUS. | Used to discover causal relationships between sensor inputs and actuator outputs from observation data. | Pattern Discovery |
| 129 | **BOCPD** | — | Bayesian Online Change Point Detection. Algorithm that identifies points in a data stream where the statistical properties change. | Detects regime changes in sensor data (e.g., load shift, environmental change) to trigger reflex adaptation. | Pattern Discovery |
| 130 | **HDBSCAN** | — | Hierarchical Density-Based Spatial Clustering of Applications with Noise. Clustering algorithm that does not require specifying the number of clusters. | Groups similar operational states from observation data to identify distinct behavioral modes. | Pattern Discovery |
| 131 | **Temporal Mining** | — | Extraction of temporal patterns (frequent subsequences, periodicities) from time-series data. | Discovers recurring temporal patterns in sensor/actuator data for predictive reflex generation. | Pattern Discovery |
| 132 | **Bayesian Reward Inference** | — | Algorithm that infers the implicit reward function guiding operator behavior from observed demonstrations. | Learns what the operator values (comfort, efficiency, safety margin) from their manual control patterns. | Imitation Learning |

---

## 5. Safety Terms

### 5.1 Safety Standards

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 133 | **IEC 61508** | — | International standard for functional safety of electrical/electronic/programmable electronic safety-related systems. The foundational standard from which domain-specific standards derive. | NEXUS targets SIL 1 compliance. System SFF estimated at ~93%. | SIL, PFH |
| 134 | **SIL** | — | Safety Integrity Level. IEC 61508 defines four levels (SIL 1–4) specifying required reliability of safety functions based on PFH/PFD. | NEXUS targets SIL 1 (PFH ≥ 10⁻⁶ to < 10⁻⁵). Estimated Category 3 / PL d equivalent. | IEC 61508, SFF |
| 135 | **PFH** | — | Probability of Dangerous Failure per Hour. Quantitative metric for safety integrity. SIL 1 requires PFH ≥ 10⁻⁶/h. | NEXUS Monte Carlo simulations show all 5 scenarios pass SIL 1 (< 10⁻⁷/h). | SIL, SFF |
| 136 | **SFF** | — | Safe Failure Fraction. Proportion of failures that are either safe (detected and handled) or dangerous but detected. | NEXUS system SFF estimated at ~93%, exceeding SIL 1's 60% requirement. | SIL, Diagnostic Coverage |
| 137 | **ISO 26262** | — | Automotive functional safety standard. Defines ASIL (Automotive Safety Integrity Level) levels A–D. | NEXUS uses as ASIL-B equivalent reference. FMEDA estimates meet ASIL-B target (90% diagnostic coverage). | ASIL |
| 138 | **ASIL** | — | Automotive Safety Integrity Level. ISO 26262's risk classification: QM, A (cosmetic), B (moderate), C (serious), D (life-threatening). | NEXUS targets ASIL-B equivalent for future ground autonomous vehicle domain. | ISO 26262 |
| 139 | **DO-178C** | — | Aviation software safety standard defining five software levels (A–E) based on failure condition severity. Level A requires 100% MC/DC coverage. | Not directly targeted but relevant for future UAV applications. NEXUS AI model stack has gaps relative to Level C. | Aviation |
| 140 | **IEC 62061** | — | Machinery-specific functional safety standard defining Performance Levels (PL a–e). | NEXUS classified as Category 3 / PL d / SIL 2 equivalent, exceeding its SIL 1 target. | PL, Category |
| 141 | **ISO 13849** | — | Machinery safety standard using qualitative categories (B, 1–4) and performance levels for safety-related control system parts. | NEXUS 4-tier architecture maps to ISO 13849 Category 3. | Category, PL |
| 142 | **IEC 60945** | — | Maritime navigation equipment environmental and EMC testing standard. Covers dry heat, cold, damp heat, vibration, shock, EMI/EMC. | Compliance target for marine deployment. Gap-050: no salt spray test conducted. | Marine |
| 143 | **IEC 62443** | — | Industrial automation and control systems cybersecurity standard. Defines Security Levels (SL 1–4) and zones/conduits model. | NEXUS targets SL 1 baseline, SL 2 for fleet deployments. Gap: no authentication on serial protocol. | Cybersecurity |

### 5.2 Analysis Methodologies

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 144 | **FMEA** | — | Failure Mode and Effects Analysis. Systematic method for identifying potential failure modes, their causes, and their effects on the system. | NEXUS documents 15 failure modes in Safety Validation Playbook. Hardware FMEA complete; software FMEA needs expansion. | Safety Analysis |
| 145 | **FTA** | — | Fault Tree Analysis. Top-down, deductive failure analysis using Boolean logic to trace system failures to root causes. | Used to analyze how safety-critical failures can occur despite the 4-tier defense. | Safety Analysis |
| 146 | **HAZOP** | — | Hazard and Operability Study. Systematic examination of process deviations using guide words (no, more, less, etc.) to identify hazards. | Applied to NEXUS operational scenarios to identify deviation-based hazards. | Safety Analysis |
| 147 | **STPA** | — | Systems-Theoretic Process Analysis. Modern hazard analysis technique that models safety as a control problem, identifying unsafe control actions rather than component failures. | Particularly relevant to NEXUS where safety emerges from the interaction of independently evolved agents. | Safety Analysis |
| 148 | **FMEDA** | — | Failure Modes, Effects, and Diagnostic Analysis. Quantitative extension of FMEA that calculates diagnostic coverage and SFF. | Used to estimate NEXUS system SFF at ~93%. | SFF, Diagnostic Coverage |

### 5.3 Safety Mechanisms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 149 | **Kill Switch** | — | Physical hardware switch that immediately cuts power to actuators. Cannot be overridden by software. | Primary Tier 1 safety mechanism. GPIO pin monitored by ISR with interrupt priority. | Safety Tier 1 |
| 150 | **Watchdog** | WDT | Timer circuit that must be periodically reset ("fed") by software. If not fed within the timeout period, it triggers a system reset. | External MAX6818 watchdog fed by safety_watchdog task every 200ms. Internal ESP32 watchdog as secondary. | MAX6818, Safety Tier 1 |
| 151 | **Heartbeat** | — | Periodic message exchanged between nodes to verify liveness and communication integrity. | Node sends every 1000ms, Jetson every 5000ms. Three missed heartbeats → FAILSAFE escalation. | HEARTBEAT, Failsafe |
| 152 | **Dead Man's Switch** | — | Safety mechanism requiring continuous positive action (holding a button, maintaining presence) to keep the system operational. Release triggers safe state. | Maritime operating mode where the helmsman must maintain physical presence or the system reverts to safe state. | Kill Switch |
| 153 | **Graceful Degradation** | — | The ability of a system to continue operating (at reduced capability) when some components fail, rather than failing catastrophically. | NEXUS heartbeat escalation: HEALTHY → WARN → DEGRADED → FAILSAFE. Non-safety reflexes disabled first. | Safety State Machine |
| 154 | **Defense-in-Depth** | — | Security/safety architecture principle using multiple independent layers of protection so that no single failure causes complete loss of safety. | NEXUS's 4-tier safety architecture: hardware interlock → firmware ISR → supervisory task → application control. | Safety Tiers |
| 155 | **Failsafe** | — | System state entered when a safety-critical failure is detected. All actuators driven to predefined safe positions. | FAILSAFE state: all outputs LOW or to configured safe positions. Requires explicit re-initialization to exit. | Safety State Machine |

### 5.4 Safety State Machine

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 156 | **NORMAL** | — | Default operational state. All subsystems active, safety monitoring running, autonomy at earned level. | System operates in NORMAL when no safety events or heartbeat timeouts have occurred. | Safety State Machine |
| 157 | **DEGRADED** | — | Reduced capability state. Non-safety reflexes disabled, telemetry reduced to essential channels. | Entered after 2 consecutive missed heartbeats or minor anomaly detection. | Heartbeat Escalation |
| 158 | **SAFE_STATE** | — | All actuators in safe positions, control loops stopped. System monitors but does not act. | Entered after 3 missed heartbeats or critical safety event. | Failsafe |
| 159 | **FAULT** | — | Unrecoverable error state. Requires manual intervention or system reset to exit. | Entered after unrecoverable hardware failure or full reset command. | Full Reset |

---

## 6. Trust Terms

### 6.1 Trust Score Parameters (All 12)

| # | Term | Symbol | Definition | NEXUS Context | Cross-refs |
|---|------|--------|------------|---------------|------------|
| 160 | **alpha_gain** | α_gain | Base rate of trust increase per evaluation window under Branch 1 (net positive). Default: 0.002. Range: [0.0001, 0.01]. | Controls how fast trust builds. Must remain ≥10x smaller than α_loss to maintain asymmetry. | Trust Gain Branch |
| 161 | **alpha_loss** | α_loss | Base rate of trust decrease per evaluation window under Branch 2 (penalty). Default: 0.05. Range: [0.01, 0.5]. | Controls how fast trust erodes on failures. At default, a single severity=1.0 event at T=1.0 drops trust by 0.05. | Trust Penalty Branch |
| 162 | **alpha_decay** | α_decay | Rate of trust decay toward t_floor under Branch 3 (inactivity). Default: 0.0001. Range: [0.00001, 0.001]. | Slow decay prevents trust from persisting indefinitely without evidence. | Trust Decay Branch |
| 163 | **t_floor** | — | Minimum trust level reachable via inactivity decay. Default: 0.2. Range: [0.0, 0.5]. Trust can go below via penalties. | Set to Level 1 threshold so systems retain advisory capability after inactivity. | Decay, Autonomy Level 1 |
| 164 | **quality_cap** | — | Maximum number of good events per window contributing to trust gain. Default: 10. Range: [1, 100]. | Prevents high-frequency polling from inflating trust. Events beyond cap ignored for gain. | Trust Gain Branch |
| 165 | **evaluation_window_hours** | — | Duration of each evaluation window. Default: 1.0 hour. Range: [0.1, 24.0]. | Trust is updated once per window. Must divide evenly into 24 hours for daily checks. | Evaluation Window |
| 166 | **severity_exponent** | — | Applied as severity^exponent before penalty computation. Default: 1.0. Range: [0.5, 2.0]. | Set to 2.0 to heavily penalize high-severity events while reducing low-severity impact. | Penalty Branch |
| 167 | **streak_bonus** | — | Additional trust gain per consecutive clean window (no bad events). Default: 0.00005. Range: [0.0, 0.001]. | Rewards sustained reliability. Must be much smaller than α_gain. | Trust Gain Branch |
| 168 | **min_events_for_gain** | — | Minimum number of good events required in a window for Branch 1 to apply. Default: 1. Range: [1, 10]. | Prevents a single lucky event from inflating trust in sporadic systems. | Trust Gain Branch |
| 169 | **reset_grace_hours** | — | Duration after a reset during which no further resets can occur. Default: 24.0 hours. Range: [0.0, 168.0]. | Prevents reset thrashing during unstable periods. | Reset Events |
| 170 | **promotion_cooldown_hours** | — | Minimum time between autonomy level promotions. Default: 72.0 hours. Range: [1.0, 336.0]. | Requires sustained observation at each level before advancement. | Autonomy Levels |
| 171 | **n_penalty_slope** | — | Slope of count-based penalty multiplier: n_penalty = 1 + slope × (n_bad - 1). Default: 0.1. Range: [0.0, 0.5]. | Controls how multiple simultaneous failures compound trust loss. | Penalty Branch |

### 6.2 Trust Dynamics

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 172 | **Trust Score** | T(t) | Continuous value in [0.0, 1.0] computed over evaluation windows, reflecting system reliability and operator confidence. Updated via three branches: gain, penalty, or decay. | Dynamically governs autonomy level of each subsystem. Gains at 0.002/window, loses at 0.05/window (25:1 ratio). | INCREMENTS, Autonomy Levels |
| 173 | **Trust Gain Branch** | Branch 1 | Computes delta_T when n_bad == 0 AND n_good > 0: δT = α_gain × (1 - T_prev) × avg_quality × (capped_n_good / quality_cap). | Trust approaches 1.0 asymptotically. The (1 - T_prev) factor makes gains smaller at high trust. | alpha_gain |
| 174 | **Trust Penalty Branch** | Branch 2 | Computes delta_T when n_bad > 0: δT = -α_loss × T_prev × max_severity × n_penalty. Good events ignored when bad events present. | Single severity=1.0 event at T=1.0 produces δT = -0.05. Penalty proportional to current trust. | alpha_loss |
| 175 | **Trust Decay Branch** | Branch 3 | Computes delta_T when n_bad == 0 AND n_good == 0: δT = -α_decay × (T_prev - t_floor). Decay stops at floor. | In the absence of evidence, trust drifts toward the floor. At t_floor, δT = 0. | alpha_decay, t_floor |
| 176 | **Trust Escalation** | — | The process of a subsystem earning higher autonomy levels through sustained reliable operation. Requires meeting all criteria for the target level simultaneously. | Promotion requires meeting trust threshold, minimum observation hours, consecutive days, and clean windows. | Autonomy Levels, Candidate State |
| 177 | **Trust Erosion** | — | The reduction of trust score due to failures, anomalies, or inactivity. Follows negativity bias: failures weighted 2–3× more than equivalent successes. | The 25:1 asymmetry ensures erosion is rapid relative to building. At T=0.80, a severity=0.7 event drops ~3.5%. | alpha_loss, Negativity Bias |

### 6.3 Autonomy Levels

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 178 | **Level 0** | L0 | **Disabled**: No autonomous actions. Manual control only. Default state after full reset. | T < 0.20. No observation or clean window requirements. Starting point. | Full Reset |
| 179 | **Level 1** | L1 | **Advisory**: System provides recommendations but cannot act autonomously. Operator approves every action. | T ≥ 0.20, 8 hours observation, 1 day consecutive, 4 clean windows. | t_floor |
| 180 | **Level 2** | L2 | **Supervised**: System executes pre-approved actions with operator monitoring. Halts on any anomaly. | T ≥ 0.40, 48 hours, 3 days, 24 clean windows. No severity ≥ 0.8 events. | Supervised Autonomy |
| 181 | **Level 3** | L3 | **Semi-Autonomous**: System executes without prior approval. Operator reachable within 30 seconds. | T ≥ 0.60, 168 hours (7 days), 7 days, 100 clean windows. No severity ≥ 0.7 in last 48h. | Semi-Autonomous |
| 182 | **Level 4** | L4 | **High Autonomy**: System executes most actions independently. Operator monitoring at 5-minute intervals. | T ≥ 0.80, 336 hours (14 days), 14 days, 200 clean windows. Minimum 45 days ideal. | High Autonomy |
| 183 | **Level 5** | L5 | **Full Autonomy**: System operates independently. Operator notified asynchronously. Emergency intervention available. | T ≥ 0.95, 720 hours (30 days), 30 days, 500 clean windows. Must pass adversarial test suite. Minimum 83 days ideal. | Full Autonomy |

### 6.4 Trust States & Transitions

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 184 | **Candidate State** | — | A deferred promotion state where the system has met all criteria for a higher level but must maintain them for 2 additional evaluation windows before promotion is confirmed. | Prevents fleeting good performance from triggering premature autonomy escalation. | Autonomy Promotion |
| 185 | **Fleet Evidence** | — | Trust evidence aggregated from multiple vessels or deployments operating similar subsystems, used to accelerate trust building for new deployments. | Enables "transfer learning" of trust: a new vessel can bootstrap trust faster if fleet-wide evidence exists. | Colony, Fleet |
| 186 | **Overtrust** | — | Condition where operator trust exceeds the system's actual capabilities, leading to inappropriate reliance and reduced monitoring. | Prevented by design: the 25:1 asymmetry makes trust hard to earn. Equilibrium at T≈0.44 under 5% bad events. | Trust Calibration |
| 187 | **Undertrust** | — | Condition where operator trust is lower than the system's actual capabilities, leading to disuse and unnecessary manual intervention. | Addressed by low entry barriers (L1 at T≥0.20), visible trust trajectory, and per-subsystem independence. | Trust Calibration |

---

## 7. Distributed Systems

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 188 | **Consensus** | — | Agreement among distributed nodes on a single data value or state despite partial failures. Ensures consistency across the system. | NEXUS's 3-Jetson Raft consensus cluster ensures reliable coordination for fleet management and safety decisions. | Raft |
| 189 | **Raft** | — | A consensus algorithm for managing a replicated log. Provides strong consistency with leader election and log replication. | Used for the 3-Jetson cluster master consensus architecture. Leader handles all write operations. | Consensus, Jetson Cluster |
| 190 | **CRDT** | — | Conflict-Free Replicated Data Type. Data structure that can be replicated across multiple nodes with concurrent updates without coordination, merging automatically. | Candidate approach for trust score synchronization across vessels where network partitions are expected. | Consensus |
| 191 | **Paxos** | — | Family of consensus protocols for achieving agreement in distributed systems. Predecessor to Raft, harder to understand but equivalent in capability. | Referenced in NEXUS research as alternative consensus mechanism. Raft chosen for simplicity. | Consensus, Raft |
| 192 | **CAP Theorem** | — | States that a distributed system can simultaneously guarantee at most two of: Consistency, Availability, and Partition tolerance. | NEXUS prioritizes partition tolerance (marine environments have unreliable links) and consistency (safety requires it), sacrificing availability during partitions. | Consistency |
| 193 | **Fleet** | — | A collection of NEXUS vessels operating under coordinated management. Fleet-level trust evidence, configuration, and model updates propagate across the fleet. | Managed by the cloud layer. Fleet evidence accelerates trust building for new vessels. | Colony, Vessel |
| 194 | **Colony** | — | A group of NEXUS nodes (ESP32 + Jetson) that form a single vessel's distributed intelligence system. Nodes communicate via wire protocol and coordinate through consensus. | Each vessel is a colony of reflex-layer nodes and cognitive-layer nodes. | Vessel, Equipment |

---

## 8. Philosophical Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 195 | **Ribosome Thesis** | — | The principle that intelligence should be distributed to the periphery (like cellular ribosomes) rather than centralized in a single brain. Each autonomous unit is self-sufficient. | NEXUS's founding metaphor. Each ESP32 node thinks, reacts, and learns independently. The platform motto: "The Ribosome, Not the Brain." | Post-Coding Age, Distributed Intelligence |
| 196 | **Intentional Stance** | — | Daniel Dennett's philosophical position that the best way to predict a system's behavior is to treat it as a rational agent with beliefs, desires, and intentions. | In NEXUS, treating each node as having "intentions" (expressed via AAB metadata) enables agent-to-agent coordination. | AAB, Agent-Native |
| 197 | **Functionalism** | — | Philosophical theory of mind that mental states are defined by their functional roles rather than their physical implementation. | Supports NEXUS's hardware-agnostic design: the same trust/computation/safety functions can run on different hardware. | Hardware-Agnostic |
| 198 | **Embodied Cognition** | — | The theory that cognition is shaped by the body's interactions with the environment, not just the brain. | NEXUS embodies AI in physical robots. Reflex control is "embodied" in sensor-actuator loops running at 1kHz. | Reflex Layer |
| 199 | **Extended Mind** | — | Clark and Chalmers' thesis that cognitive processes extend beyond the brain into the environment, including tools and external systems. | The NEXUS colony is an "extended mind" where cognition spans ESP32 nodes, Jetson modules, and cloud resources. | Colony, Distributed Intelligence |
| 200 | **wu wei** | — | Daoist concept of "effortless action" or "non-forcing action." Achieving outcomes through natural alignment rather than coercive control. | The ideal NEXUS operator experience: describe intent, and the system acts in alignment without constant intervention. | Autonomy, Intent |
| 201 | **ubuntu** | — | Southern African philosophical concept: "I am because we are." Emphasizes interconnectedness, mutual care, and collective identity. | Models the NEXUS colony: nodes are not independent agents but interconnected parts of a collective intelligence. | Colony, Fleet |
| 202 | **Autopoiesis** | — | Maturana and Varela's concept of self-creation: a system that continuously reproduces and maintains itself. | NEXUS vessels that self-monitor, self-diagnose, and self-repair approach autopoietic behavior. | Self-Healing, Reflex |
| 203 | **Trust Calibration** | — | Alignment between a person's trust in an automated system and the system's actual reliability and capabilities. | NEXUS's central design challenge. The INCREMENTS framework computationally enforces calibration through asymmetric update rates. | Overtrust, Undertrust |
| 204 | **Negativity Bias** | — | Psychological principle that negative events (failures) have a disproportionate impact compared to positive events of equal magnitude. | Encoded in NEXUS's 25:1 trust loss-to-gain ratio. A single failure outweighs 25 equivalent successes. | alpha_loss, alpha_gain |

---

## 9. Domain Terms

### 9.1 Maritime

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 205 | **COLREGs** | — | International Regulations for Preventing Collisions at Sea. Defines right-of-way rules, navigation lights, sound signals, and steering/sailing rules. | Primary regulatory framework for NEXUS marine vessel operations. NEXUS reflexes must comply with COLREGs navigation rules. | MASS, Marine |
| 206 | **MASS** | — | Maritime Autonomous Surface Ship. IMO classification for vessels operating at varying degrees of autonomy without human crew on board. | NEXUS's primary target domain. MASS autonomy degrees map approximately to NEXUS L0–L5. | COLREGs |
| 207 | **SOLAS** | — | Safety of Life at Sea. International treaty on maritime safety covering ship construction, equipment, fire protection, and life-saving appliances. | Compliance target for NEXUS marine deployments. Safety systems must meet SOLAS requirements. | IEC 60945 |
| 208 | **ECDIS** | — | Electronic Chart Display and Information System. Computer-based navigation information system that replaces paper nautical charts. | Potential integration point for NEXUS navigation subsystem. | GNSS, Marine |
| 209 | **AIS** | — | Automatic Identification System. Tracking system used on ships for identification, location, and collision avoidance via VHF radio. | Sensor input for NEXUS vessel awareness and COLREGs compliance. | COLREGs |

### 9.2 Navigation & Positioning

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 210 | **GNSS** | — | Global Navigation Satellite System. Generic term for satellite-based positioning (GPS, Galileo, GLONASS, BeiDou). | Primary position source for NEXUS marine navigation. GPS/NMEA input via UART2. | GPS, NMEA |

### 9.3 Control Theory

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 211 | **PID Control** | PID | Proportional-Integral-Derivative control. The most widely used feedback control algorithm. Output = Kp×error + Ki×∫error + Kd×d(error)/dt. | Core control algorithm in NEXUS. Implemented as PID_COMPUTE syscall with 8 concurrent controllers per VM instance. | PID_COMPUTE |
| 212 | **MPC** | — | Model Predictive Control. Advanced control strategy that optimizes control actions over a future time horizon using a dynamic model of the system. | Future enhancement for NEXUS cognitive layer. Can handle constraints and multi-variable optimization. | Control Theory |
| 213 | **SLAM** | — | Simultaneous Localization and Mapping. Computational technique for building a map of an unknown environment while tracking the agent's position within it. | Relevant for NEXUS vessels operating in unknown or changing environments. Requires Jetson-level compute. | Cognitive Layer |

---

## 10. A2A-Native Terms

### 10.1 Core A2A Concepts

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 214 | **Agent-Native** | — | Programming paradigm where agents (LLMs) are the primary authors, interpreters, and validators of control code. Agents, not humans, are the first-class programmers. | NEXUS's A2A extension: the bytecode VM becomes an agent-first programming environment. | A2A, Post-Coding Age |
| 215 | **Intention Block** | — | The fundamental program unit in A2A-native programming, replacing functions/classes. Contains: goal, constraints, verification criteria, and failure narrative. | Describes *what* should be achieved and *how to verify* it, letting the interpreter figure out the execution. | AAB, Agent-Native |
| 216 | **Capability Scope** | — | A declarative description of what a node can physically do: available sensors, actuator ranges, timing constraints, and safety limits. | Agents query capability scope to understand what actions are possible before generating reflexes. | Vessel, Equipment |
| 217 | **Trust Context** | — | A metadata envelope carrying the trust score, autonomy level, and provenance information alongside an intention block or bytecode. | Enables agents to make informed decisions about whether to accept, modify, or reject code from other agents. | Trust Score, AAB |
| 218 | **Failure Narrative** | — | A structured description of what should happen when an intention block fails to achieve its goal: fallback behaviors, escalation procedures, and recovery steps. | Embedded in AAB metadata. Tells other agents *what went wrong* and *what to do about it*. | Intention Block, AAB |

### 10.2 Three Pillars

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 219 | **Three Pillars** | — | The A2A-native architectural model consisting of: (1) System Prompt as compiler, (2) Equipment as runtime, (3) Vessel as hardware. | The foundational abstraction for A2A-native programming. Any agent with these three pillars can actualize intent. | Agent-Native |
| 220 | **System Prompt (Compiler)** | — | The system prompt that acts as a compiler frontend, translating human intention into bytecode by instructing the LLM on schemas, constraints, and safety rules. | First pillar. The agent's "understanding" of the domain and the bridge between natural language and bytecode. | Three Pillars |
| 221 | **Equipment (Runtime)** | — | The runtime environment providing capability between bytecode and metal: OS, drivers, VM, sensor/actuator abstraction layer. | Second pillar. The "OS + drivers + VM" that makes the vessel's capabilities accessible to bytecode. | Three Pillars |
| 222 | **Vessel (Hardware)** | — | The physical hardware platform defining capability boundaries: available sensors, actuators, compute resources, power budgets, and physical constraints. | Third pillar. The physical robot that constrains what is possible. | Three Pillars |

### 10.3 A2A Language Features

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 223 | **29 New Opcodes** | — | Proposed A2A extension opcodes for intent expression, inter-agent communication, capability negotiation, and safety augmentation beyond the base 32. | Categories: Intent, Communication, Capability Negotiation, Safety Augmentation. All are NOP on existing ESP32 VM (backward compatible). | Opcodes, A2A |
| 224 | **0.5x Trust Rule** | — | Agent-generated bytecode earns trust at half the rate of human-authored code, reflecting the additional verification burden. | Ensures human oversight advantage. Agent code must demonstrate reliability for longer before earning autonomy. | Trust Score, alpha_gain |
| 225 | **Unfiltered Transfer** | — | The pipeline for directly mapping A2A bytecode to Xtensa LX7 or ARM64 assembly without intermediate abstraction layers. | Minimizes overhead from agent-generated code to hardware execution. One-to-one instruction mapping where possible. | Assembly Mapping |

---

## 11. Additional Technical Terms

### 11.1 Formal Verification & Logic

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 226 | **Model Checking** | — | Automated verification technique that exhaustively checks a finite-state system model against formal properties expressed in temporal logic. | Applicable to NEXUS safety state machine verification. Tools: SPIN (LTL), NuSMV (CTL), CBMC (C code). | Formal Verification |
| 227 | **Theorem Proving** | — | Verification technique using mathematical proof (interactive or automated) to establish that a system satisfies its specification. | NEXUS VM candidate for partial formal verification in Isabelle/HOL or ACL2. Four target theorems identified. | Isabelle, Coq |
| 228 | **Abstract Interpretation** | — | Theory of sound approximation of program semantics over abstract domains. Proves absence of error classes (overflow, buffer overflow). | Most immediately applicable verification technique for NEXUS ESP32 firmware. Tools: Polyspace, Astree. | Static Analysis |
| 229 | **LTL** | — | Linear Temporal Logic. Temporal logic for reasoning about properties over individual execution paths using operators: X (next), F (eventually), G (globally), U (until). | NEXUS safety invariant: `G(not(kill_switch_pressed ∧ actuators_active))`. | CTL, Model Checking |
| 230 | **CTL** | — | Computation Tree Logic. Temporal logic for reasoning about properties over trees of all possible executions using path quantifiers (A, E) + temporal operators. | NEXUS safety liveness: `AG(heartbeat_restored → AF(normal_mode))`. | LTL, Model Checking |
| 231 | **Proof-Carrying Code** | PCC | Architecture where code is accompanied by a formal proof of safety, verified by the receiver before execution. | NEXUS's bytecode validator is a practical form of PCC: single-pass validation rejects unsafe bytecode. | Bytecode Validator |

### 11.2 Embedded & RTOS Concepts

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 232 | **ISR** | — | Interrupt Service Routine. Hardware-triggered function that preempts normal execution to handle time-critical events. | NEXUS safety ISRs handle kill-switch, current monitoring, and output clamping at Tier 2 priority. | Safety Tier 2 |
| 233 | **Rate Monotonic Scheduling** | RMS | Fixed-priority scheduling algorithm that assigns higher priority to tasks with shorter periods. Optimal among all fixed-priority algorithms. | NEXUS uses RMS-like scheduling. With 6 tasks, the schedulability bound is 73.5%. Measured utilization: 25–50%. | FreeRTOS, EDF |
| 234 | **EDF** | — | Earliest Deadline First. Dynamic-priority scheduling that assigns priority based on absolute deadline. Can schedule any set with utilization ≤ 100%. | More theoretical than practical for NEXUS. RMS chosen for simplicity and predictability. | RMS |
| 235 | **Priority Inversion** | — | Pathological case where a low-priority task holds a resource needed by a high-priority task, and a medium-priority task prevents release. | Solved by FreeRTOS's priority inheritance protocol on all mutex-protected shared resources (I2C bus, NVS). | Mars Pathfinder |
| 236 | **DVFS** | — | Dynamic Voltage and Frequency Scaling. Technique for adjusting processor voltage and clock speed to balance performance and power consumption. | Jetson Orin Nano supports DVFS across 7–25W power range. ESP32-S3 has limited DVFS support. | Power Management |
| 237 | **POST** | — | Power-On Self Test. Automated hardware diagnostic executed on boot to verify basic functionality. | NEXUS nodes run POST before sending DEVICE_IDENTITY: pin continuity, ADC reference, I2C scan, flash CRC. | Boot Sequence |
| 238 | **MISRA C** | — | Motor Industry Software Reliability Association C coding standard. 177 rules for writing safe C code in safety-critical systems. | NEXUS VM sidesteps many MISRA issues by design: no dynamic allocation, no recursion, fixed-size buffers. | Safety Coding |
| 239 | **Tick** | — | One complete execution cycle of the Reflex VM. At a given frequency (1–1000 Hz), each tick reads sensors, executes bytecode, writes actuators. | The fundamental unit of real-time control. Typical cycle budget: 50,000 cycles per tick. | Reflex VM |
| 240 | **Cycle Budget** | — | Maximum number of CPU cycles allocated per VM tick. Default: 50,000 cycles. Exceeding it triggers ERR_CYCLE_BUDGET_EXCEEDED and HALT. | Ensures bounded execution and deterministic timing. Every instruction has a published cycle count. | Timing Analysis |
| 241 | **Observation Buffer** | — | 5.5MB ring buffer in PSRAM for high-rate sensor data recording. Used for pattern discovery and post-incident analysis. | Filled by DMA-copied ADC data, drained by observation dump commands. | PSRAM, OBS_RECORD_START |
| 242 | **JSON Reflex** | — | A declarative JSON specification of a control behavior (type, setpoint, input/output pins, parameters) that a compiler translates to bytecode. | The human/agent-readable format for specifying control programs. Example: `{"type": "pid_reflex", "setpoint_pin": 0}`. | REFLEX_DEPLOY |

### 11.3 Software Concepts

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 243 | **Determinism** | — | Property of a system producing identical outputs from identical inputs in identical cycles, every time. | Core VM principle (Theorem 1). Every instruction has a fixed, measured cycle count. | Reflex VM |
| 244 | **Type Safety** | — | Property of a system preventing type errors (e.g., treating a float as an integer) from reaching unsafe operations. | NEXUS enforces at compile time (validator). Theorem 2: no NaN/Inf reaches actuators. Division by zero returns 0.0f. | Bytecode Validator |
| 245 | **Sensor Register** | — | Memory-mapped array of 64 slots populated by firmware before each VM tick. Read by READ_PIN opcode. | The input mechanism for the VM. Firmware populates from ADC, I2C, and GPIO sources. | READ_PIN |
| 246 | **Actuator Register** | — | Memory-mapped array of 64 slots written by the VM during each tick. Drained by firmware after the tick. | The output mechanism for the VM. Values are clamped to safe ranges before hardware application. | WRITE_PIN |
| 247 | **Variable Space** | — | 256 variables (VAR_0 to VAR_255) accessed via READ_PIN/WRITE_PIN with indices 64–319. Persistent across ticks within a reflex execution. | VAR_0 conventionally stores the current state machine state. Other variables used for intermediate computation. | READ_PIN |
| 248 | **Data Stack** | — | 256-entry stack of uint32_t values used for all computation in the Reflex VM. Maximum empirical depth: 4 for typical reflex patterns. | The sole computational workspace. No registers. All arithmetic, comparison, and I/O flows through the stack. | Stack Machine |
| 249 | **Call Stack** | — | Internal stack for subroutine return addresses and frame pointers. Managed by the VM for CALL/RET pseudo-instructions. | Separate from the data stack. Depth limit enforced to prevent stack overflow. | CALL, RET |
| 250 | **State Machine** | — | Computational model with a finite set of states, transitions between states triggered by events or conditions. | Implemented via GET_STATE/SET_STATE pseudo-instructions using VAR_0 as the state variable. | SET_STATE |
| 251 | **Bytecode Validator** | — | Single-pass static analysis that verifies all safety invariants of a bytecode program before first execution. | Checks: stack depth bounds, jump target validity, operand ranges, non-finite float rejection, cycle budget. | Safety Invariant |

### 11.4 Safety Events & Error Categories

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 252 | **successful_action** | — | GOOD event: a commanded action completed successfully with nominal sensor readings. Quality: 0.7. | Baseline positive event. Does not imply excellence. | Event Taxonomy |
| 253 | **successful_action_with_reserve** | — | GOOD event: action completed with significant safety margin (e.g., distance > 3× threshold). Quality: 0.95. | Highest quality event. Demonstrates conservative operation. | Event Taxonomy |
| 254 | **human_override_approved** | — | GOOD event: operator overrode the system, and post-hoc analysis confirmed the override was appropriate. Quality: 0.6. | Demonstrates system self-awareness. | Event Taxonomy |
| 255 | **safety_rule_violation** | — | BAD event: the system violated a defined safety rule (e.g., approached too close, exceeded speed limit). Severity: 0.7. | High severity. Direct violation of safety constraints. | Event Taxonomy |
| 256 | **manual_revocation** | — | BAD event: operator explicitly revoked autonomy for the subsystem. Severity: 1.0 (maximum). | Maximum severity penalty. Direct human intervention indicating loss of confidence. | Event Taxonomy |
| 257 | **anomaly_detected** | — | BAD event: internal anomaly detected by self-monitoring. Self-corrective action taken. Severity: 0.2. | Low severity because detection and correction mechanism worked. | Event Taxonomy |
| 258 | **heartbeat_timeout** | — | BAD event: subsystem failed to respond to heartbeat check within timeout period. Severity: 0.6. | Indicates potential communication or processing failure. | Heartbeat, Failsafe |
| 259 | **communication_loss** | — | BAD event: communication lost for longer than permitted threshold. Severity: 0.5. | Triggers failsafe escalation. Could indicate wiring, power, or software issues. | Heartbeat Escalation |

### 11.5 Additional Domain & Research Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 260 | **TinyML** | — | Machine learning on microcontrollers. Techniques for running neural network inference on resource-constrained devices. | ESP32-S3's 256-bit vector extension is available for future TinyML acceleration. Currently, AI runs on Jetson, not ESP32. | Edge AI, ESP32-S3 |
| 261 | **TensorFlow Lite Micro** | — | Google's framework for running TensorFlow models on microcontrollers and DSPs. | Evaluated as potential embedded ML runtime. Not used in NEXUS MVP (Jetson handles all ML). | TinyML |
| 262 | **Edge Impulse** | — | Platform for democratizing embedded ML, providing tools for data collection, model training, and deployment on edge devices. | Referenced as a potential tool for future NEXUS embedded ML workflows. | TinyML |
| 263 | **NMEA** | — | National Marine Electronics Association. Standard for marine electronics data communication (GPS, AIS, wind sensors, autopilot commands). | GPS/NMEA input received on UART2 at 4800–38400 baud. | GNSS, UART |
| 264 | **Starlink** | — | SpaceX's satellite internet constellation providing broadband connectivity in maritime and remote environments. | Primary cloud connectivity for NEXUS marine deployments. Enables Tier 3 fleet management. | Cloud Layer |
| 265 | **MQTT** | — | Message Queuing Telemetry Transport. Lightweight publish/subscribe messaging protocol for IoT and distributed systems. | Jetson cluster uses MQTT for inter-node communication and cloud connectivity. Topics defined in mqtt_topics.json. | Cloud Layer, Jetson Cluster |
| 266 | **Shadow Mode** | — | Operating mode where a candidate reflex runs in parallel with the production reflex, comparing outputs without affecting actual control. | A/B testing mechanism: candidate reflex processes real inputs but its outputs are only logged, not applied to actuators. | A/B Testing |
| 267 | **Reflex Compilation** | — | The process of converting a JSON reflex specification to validated bytecode instructions via a deterministic compiler. | Compiler optimizes for determinism and safety (not speed). Produces fixed 8-byte instructions. | JSON Reflex, Bytecode |
| 268 | **Hot Code Loading** | — | The ability to replace running code without stopping the system, inherited from Erlang's design philosophy. | NEXUS swaps bytecode between VM ticks, ensuring the control loop never sees an inconsistent state. | Hot-Loading |
| 269 | **Sandbox** | — | An isolated execution environment that restricts what code can do, preventing unauthorized access to system resources. | The Reflex VM is the sandbox: no heap allocation, no threads, no I/O except through defined registers. | Reflex VM |
| 270 | **Hardware-Agnostic** | — | Design that is independent of specific hardware, allowing deployment across different platforms. | NEXUS's three-tier design is hardware-agnostic at the specification level. Ports matrix defined for different MCU families. | Architecture |
| 271 | **WCET** | — | Worst-Case Execution Time. The maximum time a computation can take for any valid input. Critical for real-time system scheduling. | Every Reflex VM instruction has a published cycle count, enabling WCET computation for any bytecode program. | Timing Analysis |
| 272 | **Homoiconicity** | — | Property of a language where code and data share the same representation. Originated in LISP. | NEXUS's AAB format achieves a form of homoiconicity: bytecode (code) carries metadata (data) about its own purpose. | AAB, LISP |

### 11.6 Historical & Reference Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 273 | **Forth** | — | Stack-based programming language (1970) designed for embedded control. ~50 core opcodes. | Historical precedent for NEXUS's stack-based VM. NEXUS's 32 opcodes follow Forth's minimalist tradition. | Stack Machine |
| 274 | **Occam** | — | Programming language (1983) implementing Tony Hoare's CSP formalism. Used concurrent processes communicating through typed channels. | Direct ancestor of NEXUS's wire protocol: typed, CRC-verified, COBS-framed serial messages as channel vocabulary. | Wire Protocol, CSP |
| 275 | **Erlang** | — | Functional programming language (1986) designed for telecom fault tolerance. Introduced "let it crash" philosophy and hot code loading. | NEXUS safety model maps directly to Erlang's design: reflex halt → degraded mode → safe state → fault. | Hot-Loading, Graceful Degradation |
| 276 | **CSP** | — | Communicating Sequential Processes. Formalism for concurrent computation using message passing between processes. | Occam's channels → NEXUS's wire protocol. Communication IS the programming language for multi-agent coordination. | Occam |
| 277 | **seL4** | — | The first general-purpose OS microkernel with a machine-checked proof of functional correctness (~8,700 lines of C verified in Isabelle/HOL). | Aspirational benchmark for NEXUS VM formal verification. | Theorem Proving |
| 278 | **CompCert** | — | The first C compiler with a machine-checked proof of correctness (verified in Coq). | Demonstrates that verified compilation is achievable. NEXUS's compiler could follow similar verification path. | Theorem Proving |

### 11.7 Pattern Discovery & Learning Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 279 | **Pattern Discovery** | — | The process of automatically identifying recurring patterns, correlations, and anomalies in observation data using ML algorithms. | NEXUS implements 5 algorithms: cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference. | Cognitive Layer |
| 280 | **Shadow Execution** | — | Running a new reflex candidate on real input data in parallel with production, comparing outputs without affecting actuators. | The A/B testing mechanism. Candidate outputs logged but not applied. Promoted only if superior. | A/B Testing |
| 281 | **Reflex Candidate** | — | A newly generated reflex undergoing evaluation. Runs in shadow mode, compared against the production reflex it would replace. | Must demonstrate superiority over sustained operation before promotion to production. | Shadow Mode, A/B Testing |
| 282 | **Imitation Learning** | — | ML technique where the system learns control policies by observing and imitating human demonstrations. | Bayesian Reward Inference learns implicit reward functions from operator demonstrations. | Bayesian Reward Inference |

### 11.8 Additional Safety & Reliability Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 283 | **MTTF** | — | Mean Time To Failure. Average time a system operates before experiencing a failure. | NEXUS safety classification: MTTF MEDIUM as part of PL d determination. | SFF, PL |
| 284 | **Diagnostic Coverage** | — | Percentage of dangerous failures detected by diagnostic mechanisms. SIL 1 requires ≥ 60%. | NEXUS estimated at ~93% system SFF, far exceeding SIL 1 requirement. | SFF, SIL |
| 285 | **Safety Envelope** | — | The set of all states and transitions that the system can enter while maintaining safe operation, bounded by safety invariants. | The Reflex VM operates within a safety envelope defined by output clamping, cycle budget, and safety policy rules. | Safety Invariant |
| 286 | **Runtime Assertion** | — | A condition checked during execution that, if violated, triggers a safety response. | NEXUS implements runtime assertions via the VM validator (pre-execution) and safety ISRs (during execution). | Safety Tier 2 |
| 287 | **Redundancy** | — | Duplication of critical components or functions so that a single failure does not cause complete system failure. | NEXUS achieves redundancy through its 4-tier architecture: multiple independent layers detect the same failures. | Defense-in-Depth |
| 288 | **Common Cause Failure** | CCF | Failure of multiple components due to the same root cause. A key concern in safety systems that rely on redundancy. | NEXUS mitigates CCF by using diverse technologies (hardware vs. firmware vs. software) across safety tiers. | Defense-in-Depth |
| 289 | **A/B Partition Scheme** | — | OTA update strategy using two firmware partitions, alternating between them to enable rollback if the new firmware fails. | NEXUS OTA uses A/B partitions. On boot failure, the system automatically rolls back to the previous partition. | OTA |

### 11.9 Power & Thermal Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 290 | **Brownout** | — | Condition where input voltage drops below the minimum required for reliable operation, causing unpredictable behavior. | ESP32-S3 detects brownout via BROWNOUT_DETECTED error. Some peripherals may reset. | POWER_SUPPLY_FAULT |
| 291 | **Thermal Shutdown** | — | Automatic shutdown triggered when die temperature exceeds the safe operating limit to prevent permanent damage. | Critical safety error (0x4003). All outputs disabled until temperature returns to safe range. | Safety Event |

### 11.10 Additional Networking Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 292 | **5G** | — | Fifth-generation mobile network technology providing high-bandwidth, low-latency wireless connectivity. | Alternative cloud connectivity for NEXUS deployments where Starlink is unavailable or impractical. | Cloud Layer |
| 293 | **RJ-45** | — | Registered Jack 45. Standard Ethernet connector used for NEXUS RS-422 serial links. | 8-pin connector: TX+/TX-, RX+/RX-, GND, CTS/RTS, SHIELD. Requires Cat-5e minimum. | RS-422, Wire Protocol |
| 294 | **LZ4** | — | Lossless compression algorithm optimized for speed. Used for wire protocol payload compression when COMPRESSED flag is set. | Payload compression option for large telemetry or observation data transfers. | Wire Protocol |

### 11.11 Project & Process Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 295 | **ADR** | — | Architecture Decision Record. A document capturing an important architectural decision, its context, rationale, and consequences. | NEXUS maintains 28 ADRs documenting key design decisions (e.g., ADR-013: 3× Orin Nano vs 1× Orin AGX). | Architecture |
| 296 | **MVP** | — | Minimum Viable Product. The smallest version of a product that can be deployed to validate core hypotheses. | NEXUS MVP targets SIL 1 with ESP32-S3 + Jetson Orin Nano, single vessel, marine domain. | Roadmap |
| 297 | **VM Footprint** | — | Total memory consumed by the Reflex VM in RAM. Approximately 3KB for the core VM plus 5,280 bytes total budget. | Fits within ESP32-S3's 512KB SRAM with 99% margin. ~12KB flash for VM code. | Memory Budget |
| 298 | **Espressif Systems** | — | Shanghai-based fabless semiconductor company that designs and manufactures the ESP32 family of microcontrollers. | Manufacturer of the ESP32-S3 used across all NEXUS Tier 1 nodes. | ESP32-S3 |
| 299 | **Cadence Design Systems** | — | Electronic design automation company that acquired Tensilica, creator of the Xtensa processor architecture. | Designer of the Xtensa LX7 core used in the ESP32-S3. | Xtensa LX7 |

### 11.12 Miscellaneous Technical Terms

| # | Term | Abbr. | Definition | NEXUS Context | Cross-refs |
|---|------|-------|------------|---------------|------------|
| 300 | **LPDDR5** | — | Low-Power Double Data Rate 5 SDRAM. High-bandwidth, energy-efficient memory technology. | Jetson Orin Nano Super has 8GB LPDDR5 providing the memory bandwidth needed for LLM inference. | Jetson Orin Nano |
| 301 | **Software FPU** | — | Floating-point arithmetic implemented in software (library calls) rather than dedicated hardware. | ESP32-S3 has no hardware FPU. All float operations use software emulation via libgcc (20–50 cycles/op). | Xtensa LX7 |
| 302 | **ULP-RISC-V** | — | Ultra-Low-Power RISC-V coprocessor in the ESP32-S3 that can execute code while main cores are in deep sleep (up to 17.5 MHz). | Reserved in NEXUS for future power-constrained sensor nodes (e.g., bilge pump monitors). | Deep Sleep |
| 303 | **Secure Boot v2** | — | ESP32-S3's hardware security feature using RSA-3072 signing to verify firmware authenticity before execution. | Prevents unauthorized firmware from running on NEXUS nodes. Part of the security architecture. | IEC 62443 |
| 304 | **DMA-Capable** | — | Memory regions that can be directly accessed by DMA controllers without CPU intervention. | SRAM1 is DMA-capable; PSRAM is NOT. ADC DMA writes to SRAM1, then ISR copies to PSRAM ring buffer. | DMA, PSRAM |
| 305 | **NVMe** | — | Non-Volatile Memory Express. High-performance storage interface protocol. | Jetson Orin Nano can use NVMe for local model and data storage. | Jetson Orin Nano |
| 306 | **IEEE 754** | — | Standard for floating-point arithmetic. Defines formats (float32, float64), operations, and special values (NaN, Infinity). | All Reflex VM float values use IEEE 754 single-precision (32-bit). Division by zero returns 0.0f (not NaN). | Float32, CLAMP_F |
| 307 | **GDMA** | — | General DMA. ESP32-S3's DMA controller with 4 TX and 4 RX channels, with priority-based arbitration. | Handles UART TX/RX, ADC sampling, and other peripheral-to-memory transfers. | DMA |
| 308 | **LEDC** | — | LED PWM Controller. ESP32-S3 peripheral providing up to 8 channels of configurable PWM output. | Used for motor/solenoid/LED control. Frequency and duty cycle set per channel. | PWM |
| 309 | **TWAI** | — | Two-Wire Automotive Interface. ESP32-S3's CAN 2.0B controller. Reserved for future expansion. | CAN bus capability available but not used in current NEXUS MVP. | CAN |
| 310 | **Zephyr** | — | Linux Foundation's RTOS for IoT devices. Richer networking than FreeRTOS but larger footprint. | Evaluated but rejected for NEXUS ESP32 nodes due to higher SRAM requirements. | FreeRTOS |

---

## Appendix: Quick Reference Tables

### A. Opcode Categories (32 Opcodes)

| Category | Opcodes | Count |
|----------|---------|-------|
| Stack Operations | NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT | 8 |
| Arithmetic (Float) | ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F | 9 |
| Comparison | EQ_F, LT_F, GT_F, LTE_F, GTE_F | 5 |
| Logic (Bitwise) | AND_B, OR_B, XOR_B, NOT_B | 4 |
| I/O | READ_PIN, WRITE_PIN, READ_TIMER_MS | 3 |
| Control Flow | JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE | 3 |

### B. Wire Protocol Message Categories (28 Messages)

| Category | Message IDs | Count |
|----------|-------------|-------|
| Boot & Identity | 0x01, 0x04, 0x1B | 3 |
| Role Management | 0x02, 0x03 | 2 |
| Link Health | 0x05, 0x16, 0x17, 0x18 | 4 |
| Telemetry & Data | 0x06, 0x19, 0x1A | 3 |
| Commands & Control | 0x07, 0x08, 0x10 | 3 |
| Reflex Engine | 0x09, 0x0A | 2 |
| Observation System | 0x0B, 0x0C, 0x0D, 0x0E, 0x0F | 5 |
| Firmware OTA | 0x11, 0x12, 0x13, 0x14 | 4 |
| Error & Safety | 0x15, 0x1C | 2 |

### C. Trust Score Parameters (12 Parameters)

| # | Parameter | Default | Range |
|---|-----------|---------|-------|
| 1 | alpha_gain | 0.002 | [0.0001, 0.01] |
| 2 | alpha_loss | 0.05 | [0.01, 0.5] |
| 3 | alpha_decay | 0.0001 | [0.00001, 0.001] |
| 4 | t_floor | 0.2 | [0.0, 0.5] |
| 5 | quality_cap | 10 | [1, 100] |
| 6 | evaluation_window_hours | 1.0 | [0.1, 24.0] |
| 7 | severity_exponent | 1.0 | [0.5, 2.0] |
| 8 | streak_bonus | 0.00005 | [0.0, 0.001] |
| 9 | min_events_for_gain | 1 | [1, 10] |
| 10 | reset_grace_hours | 24.0 | [0.0, 168.0] |
| 11 | promotion_cooldown_hours | 72.0 | [1.0, 336.0] |
| 12 | n_penalty_slope | 0.1 | [0.0, 0.5] |

### D. Autonomy Levels (L0–L5)

| Level | Name | Threshold | Min Days (Ideal) |
|-------|------|-----------|-------------------|
| L0 | Disabled | — | — |
| L1 | Advisory | T ≥ 0.20 | 7 |
| L2 | Supervised | T ≥ 0.40 | 20 |
| L3 | Semi-Autonomous | T ≥ 0.60 | 45 |
| L4 | High Autonomy | T ≥ 0.80 | 45 |
| L5 | Full Autonomy | T ≥ 0.95 | 83 |

---

*This glossary is a living document. Terms should be added as the NEXUS platform evolves and new concepts are introduced.*
