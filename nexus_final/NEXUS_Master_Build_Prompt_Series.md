# NEXUS Platform — Master Build Prompt Series for Coding Agents

**Version:** 2.0.0 | **Date:** 2026-03-30 | **Classification:** Production Build Instructions
**Purpose:** Complete prompt series for an AI coding agent to build the NEXUS Post-Coding Distributed Intelligence Platform from a blank repository to production release.
**Target Agents:** Claude Code, Cursor, glm-5-turbo full-stack, GitHub Copilot Workspace, or any capable AI coding assistant.

---

## How to Use This Document

1. **Start with Prompt M** (Master Coordinator) — load this as system context before any other prompt.
2. **Execute prompts in order** within each phase. Phases can overlap across developers.
3. **Each prompt is self-contained** — includes exact file paths, data structures, protocol bytes, and timing requirements. No external reference needed.
4. **After each prompt**, verify the stated "success criteria" before proceeding.

## Quick-Start Guide

| Goal | Prompts | Calendar Time | Parallelism |
|------|---------|--------------|-------------|
| **Minimum viable demo** (LED blinker via chat) | M, 0, 1, 2, 3, 4, 5, 6, 7 (partial) | ~8 weeks | 2 developers |
| **Core autopilot with reflex deploy** | M, 0–5, 6, 7, 8 | ~10 weeks | 2 developers |
| **Full system with learning** | M, 0–12 | ~14 weeks | 3 developers |
| **Production release** | M, 0–17 | ~18 weeks | 3 developers |
| **Jetson-only** (no firmware) | M, 0, 6, 7, 8, 9, 10, 11, 12, 13, 14 | ~12 weeks | 2 developers |
| **Firmware-only** (no Jetson) | M, 0, 1, 2, 3, 4, 5, 13, 15 | ~10 weeks | 1 developer |

---

## Prompt M: Master Coordinator (System Context)

**Load this as system context before executing any other prompt.** This gives the coding agent the full architectural vision.

```
You are building the NEXUS Platform, a post-coding distributed intelligence system for industrial robotics. Here is the complete architectural context you need.

WHAT NEXUS IS:
NEXUS eliminates the need for humans to write code. Operators wire hardware, describe intent in natural language, demonstrate desired behaviors, and approve or reject AI-generated proposals. The system learns from observation, synthesizes reflexes, validates them through A/B testing, and progressively earns trust to operate with increasing autonomy.

ARCHITECTURE — THREE TIERS:
  Tier 1 (MCU Reflex Layer): ESP32-S3 microcontrollers (~$6-10 each) serve as "limbs." They run a single universal firmware binary (~320KB) that executes compiled bytecode reflexes at up to 1kHz. They read sensors, compute control outputs, and drive actuators. They operate independently and can maintain basic reflex-based control even when all higher tiers fail.

  Tier 2 (Jetson Cognitive Layer): NVIDIA Jetson Orin Nano Super boards (~$249 each) serve as "brains." They handle AI inference, natural language understanding, pattern discovery from observation data, reflex compilation and deployment, MQTT telemetry bridging, and the chat interface. Three or more Jetson units form a cognitive cluster with role specialization.

  Tier 3 (Cloud — Optional): Heavy computational tasks exceeding Jetson capacity. Connected via Starlink satellite with queue-and-forward semantics. Used for training, large-scale simulation, fleet management, and generating complex reflex proposals. Authority: can suggest but cannot command actuators directly.

HARDWARE INTERCONNECTION:
  RS-422 full-duplex serial at 921600 baud (upgradeable from 115200 at boot). Cat-5e cable with RJ-45 connectors. TI THVD1500 transceivers. 120-ohm termination. Hardware CTS/RTS flow control. Max cable: 10m at 921600, 100m at 115200.

KEY SPECIFICATIONS:
  - Wire Protocol: COBS framing, CRC-16/CCITT-FALSE, 28 message types, 75 error codes
  - Bytecode VM: 32 opcodes (0x00-0x1F), 8-byte instructions, 3KB static footprint, 10,000 cycle budget per tick
  - Safety: 4-tier defense in depth (hardware interlock <1ms, firmware ISR <10ms, supervisory task <100ms, application layer)
  - Autonomy: 6-level INCREMENTS scale per subsystem (0=MANUAL to 5=FULL), asymmetric trust with 25:1 loss:gain ratio
  - Learning: 5 pattern discovery algorithms, 7 A/B test metrics, reflex synthesis from observation
  - AI Models: Qwen2.5-Coder-7B (local codegen), Phi-3-mini (intent classification), GPT-4o/Claude (cloud safety validation)
  - Data: 72-field UnifiedObservation schema at 100Hz, Parquet storage with 3-tier retention

FIRMWARE CONSTRAINTS:
  - Language: C (ESP-IDF v5.2+), MISRA-C compliant in safety-critical paths
  - All ISR code must be in IRAM (not flash) — no blocking, no floating point, no logging in ISR
  - Kill switch ISR: <1ms from contact break to all outputs at safe state
  - Boot sequence must complete in <500ms
  - Flash: factory partition (512KB, never OTA-modified), ota_0 (1.5MB), ota_1 (1.5MB), reflexes (2MB LittleFS)
  - Observation buffer: 5MB PSRAM ring buffer (volatile — acceptable to lose on power loss)

JETSON CONSTRAINTS:
  - Language: Python 3.11, async everywhere (asyncio)
  - Framework: gRPC for synchronous, MQTT for asynchronous
  - Local LLM: llama-cpp-python with Q4_K_M quantization
  - All AI-generated code must be validated by a DIFFERENT LLM call (prevent self-validation bias)
  - Resource budgets: every module reports CPU%, GPU%, RAM, VRAM; thermal throttle shedding at 85°C

QUALITY STANDARDS:
  - All code must compile/build with zero warnings
  - Unit test coverage >80% for safety-critical paths, >60% for everything else
  - Every commit must pass CI before merge
  - Safety-critical code (firmware ISR, kill switch, watchdog) requires code review + hardware-in-loop test
  - All JSON schemas must validate before deployment
  - All reflex bytecode must pass the compiler's safety validator before REFLEX_DEPLOY

CROSS-DOMAIN APPLICABILITY:
The same system controls marine vessels, agricultural equipment, HVAC, factory automation, mining, and home automation. Each domain is defined by configuration (JSON equipment templates), not custom code.

Build this system with extreme attention to safety. Every actuator write must pass through the safety guard. Every generated reflex must be validated. Every trust score change must be logged. Safety is non-negotiable.
```

**REASONING:** The Master Coordinator prompt establishes the "big picture" that prevents the coding agent from making locally optimal but globally destructive decisions. Without this context, an agent might optimize one component (e.g., making the VM faster) while violating a critical constraint (e.g., breaking deterministic timing guarantees that the safety system depends on). Loading this as system context ensures every subsequent prompt is interpreted within the correct architectural framework.

---

## Phase 1: Foundation

### Prompt 0: Project Scaffolding

**Dependencies:** None
**Estimated effort:** 1 day
**Goal:** Initialize monorepo with firmware (ESP-IDF C), jetson (Python), shared (proto, schemas), and CI pipeline.

```
Initialize a monorepo for the NEXUS Platform. Create this exact directory structure:

/nexus-platform/
├── firmware/                    # ESP-IDF v5.2+ C project
│   ├── CMakeLists.txt           # ESP-IDF project root
│   ├── partitions.csv           # Flash partition table
│   ├── sdkconfig.defaults       # SDK configuration overrides
│   ├── main/
│   │   ├── CMakeLists.txt
│   │   └── main.c               # Boot sequence entry point
│   ├── components/
│   │   ├── nexus_protocol/      # COBS, CRC, message dispatch
│   │   ├── nexus_io/            # I/O abstraction, pin config, drivers
│   │   ├── nexus_vm/            # Bytecode VM (32 opcodes)
│   │   ├── nexus_safety/        # Kill switch, watchdog, heartbeat
│   │   └── nexus_ota/           # OTA update management
│   └── config/                  # Default pin/safety JSON configs
├── jetson/                      # Python cognitive services
│   ├── pyproject.toml           # Python 3.11 package
│   ├── nexus_cognitive/
│   │   ├── __init__.py
│   │   ├── nexus_module.py      # Module ABC
│   │   ├── serial_bridge.py
│   │   ├── node_manager.py
│   │   ├── reflex_orchestrator.py
│   │   ├── learning_pipeline.py
│   │   ├── ab_testing.py
│   │   ├── code_generation.py
│   │   ├── autonomy_manager.py
│   │   ├── chat_interface.py
│   │   ├── mqtt_bridge.py
│   │   └── cloud_sync.py
│   ├── proto/
│   │   └── cluster_api.proto    # 6 gRPC services
│   ├── tests/
│   └── config/
├── shared/                      # Cross-cutting specs
│   ├── schemas/                 # JSON schemas
│   └── proto/                   # Shared .proto files
├── dashboard/                   # Next.js monitoring UI
├── tests/
│   ├── firmware/                # Unity test framework
│   └── jetson/                  # pytest
├── docs/
├── .github/workflows/
│   ├── ci-firmware.yml
│   └── ci-jetson.yml
├── .gitignore
└── README.md

REQUIRED FILES WITH EXACT CONTENT:

1. firmware/CMakeLists.txt:
   cmake_minimum_required(VERSION 3.16)
   include($ENV{IDF_PATH}/tools/cmake/project.cmake)
   project(nexus_limb)
   set(EXTRA_COMPONENT_DIRS "components")

2. firmware/partitions.csv:
   # Name,    Type, SubType,  Offset,  Size
   nvs,       data, nvs,      0x9000,  0x6000      # 24KB
   otadata,   data, ota,      0xf000,  0x2000      # 8KB
   phy_init,  data, phy,      0x11000, 0x1000      # 4KB
   factory,   app,  factory,  0x20000, 0x80000     # 512KB — NEVER OTA modified
   ota_0,     app,  ota_0,    0x100000,0x180000    # 1.5MB
   ota_1,     app,  ota_1,    0x280000,0x180000    # 1.5MB
   reflexes,  data, spiffs,   0x400000,0x200000    # 2MB LittleFS
   coredump,  data, coredump, 0x600000,0x10000     # 64KB

3. firmware/sdkconfig.defaults:
   CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
   CONFIG_PARTITION_TABLE_SINGLE_APP=n
   CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"
   CONFIG_SPIRAM=y
   CONFIG_SPIRAM_MODE_OCT=y
   CONFIG_SPIRAM_SPEED_80M=y
   CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y
   CONFIG_SPIRAM_RODATA=y
   CONFIG_ESP_CONSOLE_UART_NUM=0
   CONFIG_FREERTOS_HZ=1000
   CONFIG_ESP_DEFAULT_CPU_FREQ_240=y
   CONFIG_ESP_TASK_WDT=y
   CONFIG_ESP_TASK_WDT_TIMEOUT_S=1
   CONFIG_COMPILER_OPTIMIZATION_SIZE=y
   CONFIG_ESP_SYSTEM_PANIC_REBOOT_DELAY_SECONDS=0

4. jetson/pyproject.toml:
   [project]
   name = "nexus-cognitive"
   version = "0.1.0"
   requires-python = ">=3.11"
   dependencies = [
       "grpcio>=1.60", "grpcio-tools>=1.60",
       "paho-mqtt>=2.0", "pyserial>=3.5", "pyserial-asyncio>=0.6",
       "numpy>=1.26", "scipy>=1.12", "scikit-learn>=1.4",
       "hdbscan>=0.8", "pyarrow>=15.0", "pandas>=2.2",
       "llama-cpp-python>=0.2", "aiohttp>=3.9",
       "structlog>=24.1"
   ]

5. jetson/proto/cluster_api.proto — Define 6 gRPC services:
   service NodeDiscovery { rpc ListNodes(Empty) returns (NodeList); rpc GetNodeInfo(NodeId) returns (NodeInfo); }
   service NodeManager { rpc AssignRole(RoleAssignReq) returns (RoleAssignResp); rpc ReassignRole(RoleAssignReq) returns (RoleAssignResp); }
   service ReflexOrchestrator { rpc DeployReflex(ReflexDef) returns (DeployResp); rpc ListReflexes(NodeId) returns (ReflexList); rpc RemoveReflex(RemoveReq) returns (RemoveResp); }
   service LearningService { rpc StartSession(SessionConfig) returns (SessionInfo); rpc StopSession(SessionId) returns (SessionResult); rpc GetPatterns(SessionId) returns (PatternList); }
   service AutonomyManager { rpc GetTrustScore(SubsystemId) returns (TrustInfo); rpc SetAutonomyLevel(LevelSet) returns (LevelResp); }
   service ChatService { rpc SendMessage(ChatMsg) returns (ChatResp); rpc GetHistory(SessionId) returns (ChatHistory); }

6. README.md — Project overview with the three-tier architecture diagram, quick-start instructions, and links to docs/.

Create PLACEHOLDER implementations that compile/build but return 0/null. The firmware must pass `idf.py build`. The jetson package must pass `pip install -e .`. Do NOT write actual logic yet.
```

**REASONING:** Scaffolding first because every subsequent prompt depends on the directory structure, build system, and dependency declarations being correct. The partition table is specified here because it affects flash memory layout (and therefore the safety system — the factory partition must exist before the OTA system can be built). sdkconfig.defaults enables PSRAM at boot because the observation buffer depends on it. The proto file is a stub here but its service definitions constrain the Jetson API surface, preventing later design drift.

---

### Prompt 1: Wire Protocol Implementation

**Dependencies:** Prompt 0
**Estimated effort:** 2-3 weeks
**Goal:** Complete COBS framing, CRC-16, message header parsing, and 28-type dispatch table.

```
Implement the NEXUS serial wire protocol in /firmware/components/nexus_protocol/.

FILES: cobs.h/cobs.c, crc16.h/crc16.c, framing.h/framing.c, msg_handler.h/msg_handler.c

COBS ENCODING (Consistent Overhead Byte Stuffing):
- Scan input bytes left to right.
- Count consecutive non-zero bytes (max 254).
- When 0x00 encountered OR count reaches 254: emit the count byte, then emit the non-zero bytes.
- After all input consumed: emit final count byte followed by 0x00 sentinel.
- DECODE: read count byte N, copy next (N-1) bytes to output, append 0x00. If N==0xFF and no 0x00 within 254 bytes, this is a "stuff" byte — advance past it.
- CRITICAL: the decoded output NEVER contains 0x00. The wire frame uses 0x00 as unambiguous frame delimiter.
- Overhead: worst case +1 byte per 254 input bytes (0.4% typical).

CRC-16/CCITT-FALSE:
- Polynomial: 0x1021
- Initial value: 0xFFFF
- Final XOR: 0x0000
- No reflection of input or output
- Computed over: Header (10 bytes) + Payload (0-1024 bytes). NOT over the CRC itself.
- Transmitted MSB first (big-endian) as 2 bytes appended after payload.
- Test vector: CRC of "123456789" = 0x29B1.

WIRE FRAME FORMAT:
  [0x00 delimiter] [COBS-encoded data] [0x00 delimiter]
  COBS-encoded data = COBS(Header[10] + Payload[0-1024] + CRC16[2])
  Max decoded: 1036 bytes. Max COBS encoded: ~1038 bytes. Max wire frame: ~1040 bytes.
  Both sender and receiver MUST strip the 0x00 delimiters before COBS decode.

10-BYTE MESSAGE HEADER (all fields big-endian):
  Offset  Size  Field
  0       1     msg_type (uint8)
  1       1     flags (uint8):
                  bit 0 = ACK_REQUIRED
                  bit 1 = IS_ACK
                  bit 2 = IS_ERROR
                  bit 3 = URGENT (preempt lower-priority TX)
                  bit 7 = NO_TIMESTAMP
  2-3     2     sequence_number (uint16, rolling counter 0-65535)
  4-7     4     timestamp_ms (uint32, uptime since boot in ms)
  8-9     2     payload_length (uint16, 0-1024)

28 MESSAGE TYPES (hex values):
  Boot/Identity:
    0x01 DEVICE_IDENTITY   — Node→Jetson. JSON payload: {mac, chip_id, firmware_ver, capabilities}
    0x04 SELFTEST_RESULT   — Node→Jetson. JSON: {per_pin_results, flash_crc, boot_count}
    0x1B AUTO_DETECT_RESULT — Node→Jetson. JSON: {i2c_devices:[{bus,addr,type}], adc_channels}

  Role Management:
    0x02 ROLE_ASSIGN       — Jetson→Node. JSON: {role, pins:{...}, telemetry_interval_ms, reflexes:[...]}
    0x03 ROLE_ACK          — Node→Jetson. JSON: {accepted:bool, rejection_reason:string}

  Link Health:
    0x05 HEARTBEAT         — Both directions. No JSON payload (empty). Flags carry health state.
    0x06 TELEMETRY         — Node→Jetson. JSON: {timestamp, sensors:{name:value,...}}
    0x16 PING              — Either direction. No payload.
    0x17 PONG              — Either direction. Payload: {latency_ms, rx_seq}
    0x18 BAUD_UPGRADE      — Jetson→Node. JSON: {target_baud:uint32}

  Commands:
    0x07 COMMAND           — Jetson→Node. JSON: {target_subsystem, command, params}
    0x08 COMMAND_ACK       — Node→Jetson. JSON: {command_id, status, result}
    0x10 IO_RECONFIGURE    — Jetson→Node. JSON: {pins:{...}} (runtime reconfiguration)

  Reflex Engine:
    0x09 REFLEX_DEPLOY     — Jetson→Node. JSON: {name, version, bytecode_base64}
    0x0A REFLEX_STATUS     — Node→Jetson. JSON: {name, status, cycle_count, last_error}

  Observation:
    0x0B OBS_RECORD_START  — Jetson→Node. JSON: {session_id, sample_rate_hz, channels}
    0x0C OBS_RECORD_STOP   — Jetson→Node. Empty payload.
    0x0D OBS_DUMP_HEADER   — Node→Jetson. JSON: {session_id, total_frames, total_bytes, start_time}
    0x0E OBS_DUMP_CHUNK    — Node→Jetson. BINARY payload (raw observation data).
    0x0F OBS_DUMP_END      — Node→Jetson. JSON: {frames_sent, crc32}

  OTA:
    0x11 FIRMWARE_UPDATE_START — Jetson→Node. JSON: {size, chunk_count, version, sha256}
    0x12 FIRMWARE_UPDATE_CHUNK — Jetson→Node. BINARY payload (512 bytes).
    0x13 FIRMWARE_UPDATE_END   — Jetson→Node. Empty payload.
    0x14 FIRMWARE_UPDATE_RESULT — Node→Jetson. JSON: {success, boot_partition, sha256_actual}

  Cloud:
    0x19 CLOUD_CONTEXT_REQUEST — Jetson→Node. JSON: {request_id, context_data}
    0x1A CLOUD_RESULT           — Node→Jetson. JSON: {request_id, result_data}

  Error/Safety:
    0x15 ERROR              — Node→Jetson. JSON: {error_code:uint16, severity, message}
    0x1C SAFETY_EVENT       — Node→Jetson. JSON: {event_type, details}

RELIABILITY MECHANISMS:
- ACK_REQUIRED flag (bit 0): if set, sender expects 0x03/0x08/0x14 with IS_ACK flag within 500ms.
- Retry: up to 3 retries with exponential backoff (200ms, 400ms, 800ms). Log each retry.
- Sequence numbers: 16-bit rolling counter. Receiver detects gaps and duplicates via sliding window (8 entries).
- Priority queue: 4 levels — Safety(0), Critical(1), Normal(2), Bulk(3). Safety preempts everything.

75 ERROR CODES (categories):
  General (0x00-0x06): UNKNOWN, TIMEOUT, BUFFER_OVERFLOW, INVALID_MESSAGE, NOT_READY, ALREADY_IN_PROGRESS, CANCELLED
  Hardware (0x10-0x19): GPIO_INIT_FAILED, I2C_INIT_FAILED, I2C_BUS_LOCKED, ADC_INIT_FAILED, SPI_INIT_FAILED, UART_INIT_FAILED, FLASH_READ_ERROR, FLASH_WRITE_ERROR, DMA_ERROR, CLOCK_CONFIG_ERROR
  I/O (0x20-0x26): PIN_MODE_INVALID, PIN_ALREADY_IN_USE, PIN_NOT_CONFIGURED, PIN_OUT_OF_RANGE, DRIVER_NOT_FOUND, DRIVER_INIT_FAILED, IO_CONFIG_PARSE_ERROR
  Reflex (0x30-0x36): REFLEX_PARSE_ERROR, REFLEX_COMPILE_ERROR, REFLEX_DEPLOY_FAILED, REFLEX_NOT_FOUND, REFLEX_CYCLE_DETECTED, REFLEX_TOO_LARGE, REFLEX_VALIDATION_FAILED
  Safety (0x40-0x47): KILL_SWITCH_ACTIVATED, OVERCURRENT_DETECTED, THERMAL_SHUTDOWN, WATCHDOG_TIMEOUT, HEARTBEAT_LOST, SOLENOID_TIMEOUT, SENSOR_STALE, SAFE_STATE_ENTERED
  Protocol (0x50-0x5C): FRAME_TOO_LARGE, CRC_MISMATCH, COBS_DECODE_ERROR, SEQUENCE_GAP, UNKNOWN_MESSAGE_TYPE, INVALID_PAYLOAD, TIMEOUT_NO_ACK, BAUD_NEGOTIATION_FAILED
  Firmware (0x60-0x66): OTA_HASH_MISMATCH, OTA_BOOT_VERIFICATION_FAILED, OTA_INSUFFICIENT_SPACE, OTA_PARTITION_CORRUPT, FACTORY_BOOT_TRIGGERED, BOOT_COUNT_EXCEEDED

UART CONFIGURATION:
- Default: 115200 baud at boot.
- 8N1, hardware CTS/RTS flow control ALWAYS enabled.
- RX buffer: 2048 bytes. TX buffer: 1024 bytes.
- Use ESP-IDF uart_driver with UART_PIN_NO_CHANGE for unused pins.

UNIT TESTS:
- COBS: round-trip for payload sizes 0, 1, 2, 3, 253, 254, 255, 256, 1024 bytes.
- COBS edge case: 256 consecutive zero bytes, all 0xFF bytes, alternating 0x00/0xFF.
- CRC-16: verify against "123456789" → 0x29B1.
- Header encode/decode: verify all fields are big-endian.
- Frame assembly: encode message → COBS → frame, then decode frame → COBS → message. Verify round-trip for every message type.
- Sequence number wraparound: test at 65534→65535→0→1.
- Priority queue: send 4 messages at different priorities, verify Safety sent first.
```

**REASONING:** The wire protocol is the foundation of ALL communication. It must be implemented first because every other component (safety heartbeat, role assignment, reflex deploy, observation dump, OTA) depends on reliable message passing. COBS was chosen over newline-delimited JSON because observation buffer dumps are 5.5MB of binary data — JSON encoding would add 33% base64 overhead vs COBS's 0.4%. CRC-16 (not CRC-32) provides sufficient integrity for serial frames while being faster to compute on the MCU. The 28 message types are carefully partitioned to prevent scope creep — each type has a single responsibility.

---

### Prompt 2: Safety Layer

**Dependencies:** Prompts 0, 1
**Estimated effort:** 1-2 weeks
**Goal:** Implement kill switch ISR, hardware watchdog, heartbeat monitor, overcurrent detection, and boot-time safe-state enforcement.

```
Implement the four-tier safety system in /firmware/components/nexus_safety/. This is the MOST safety-critical component.

FILES: kill_switch.h/kill_switch.c, watchdog.h/watchdog.c, heartbeat.h/heartbeat.c, overcurrent.h/overcurrent.c, safety_supervisor.h/safety_supervisor.c

TIER 1 — HARDWARE INTERLOCK (Response: <1ms, Authority: ABSOLUTE):
Physical components (not code, but code must support them):
- NC mushroom-head kill switch (IP67, 22-50N actuation) wired in SERIES with +12V actuator power, BEFORE any fuse.
- MAX6818 external supervisor IC: WDI input from ESP32 GPIO, RST output to ESP32 EN pin. Timeout: 1.0s (NOT software-configurable).
- PTC polyfuse per channel: hold at 1.5x rated, trip at 2.0x rated, self-resetting.
- 10K-ohm pull-down on all MOSFET gates (fail-safe to LOW if MCU crashes).
- Flyback diodes on all inductive loads.
- TVS diodes on RS-422 lines for ESD protection.

TIER 2 — FIRMWARE SAFETY GUARD (Response: <10ms, Authority: overrides all software):

KILL SWITCH ISR:
- GPIO configured INPUT with external 10K pull-up. Falling edge = kill activated. Broken wire = floating high = safe (pull-up keeps it high, which is NOT the kill state... actually: NC switch means CLOSED=circuit made, OPEN=kill. Sense wire: connect one side to 3.3V through 10K pull-up, other side to GPIO. When switch is CLOSED (normal): GPIO sees 3.3V. When switch OPENS (kill): GPIO pulled to GND through switch. So: FALLING edge = kill.)
- ISR priority: ESP_INTR_FLAG_LEVEL1 (highest configurable).
- ALL ISR code MUST be in IRAM (IRAM_ATTR). NO blocking. NO floating point. NO logging. NO malloc.
- ISR actions (total <100us):
  1. Set volatile bool estop_triggered = true
  2. gpio_set_level() for ALL actuator pins to safe_value
  3. ledc_set_duty(0) for ALL PWM channels
  4. xSemaphoreGiveFromISR(safety_sem, &xHigherPriorityTaskWoken)
  5. Return immediately
- Test: oscilloscope CH1=kill switch GPIO, CH2=actuator output. Target: <1ms contact-break to output-safe.

HARDWARE WATCHDOG FEEDING:
- GPIO toggling at 200ms interval: alternate 0x55 (01010101) and 0xAA (10101010).
- This pattern prevents both stuck-at-0 and stuck-at-1 faults.
- If software crashes: GPIO freezes → MAX6818 times out in 1.0s → ESP32 hard resets.
- On reboot: check NVS boot_count. If >5 resets in 10 minutes: enter FAULT mode (identity + heartbeat only, no actuators).

OVERCURRENT DETECTION ISR:
- INA219 current sensor on I2C, alert pin to GPIO interrupt.
- Per-channel thresholds (configurable): solenoid=4A, motor=5A, relay=2A, servo=1A, general=500mA.
- 200ms inrush allowance after actuator activation.
- Detection: if current exceeds threshold for >100ms sustained → ISR fires.
- ISR: disable output immediately, set overcurrent flag, give semaphore.
- Deferred handler: log event, notify Jetson via SAFETY_EVENT (0x1C), enter DEGRADED if multiple channels.

TIER 3 — SUPERVISORY TASK (Response: <100ms, Authority: overrides control tasks):
- FreeRTOS task at priority configMAX_PRIORITIES - 1.
- Runs every 10ms via xTaskNotify / event group.
- Heartbeat monitoring: Jetson must send HEARTBEAT every 100ms via serial. States:
    NORMAL → DEGRADED (5 consecutive misses = 500ms): reflexes continue, PID holds last setpoint, AI disabled
    DEGRADED → SAFE_STATE (10 misses = 1000ms): ALL actuators to safe, all control suspended
    Recovery: 3 consecutive good heartbeats → DEGRADED → NORMAL (after Jetson sends explicit RESUME)
- Software task watchdog: every task calls safety_checkin(task_id) every 1.0s.
  1st miss = log+warn. 2nd miss = suspend task + safe its actuators. 3rd miss = system reset.
- Heap monitoring: if free heap < 10KB → log warning. If < 5KB → SAFE_STATE.

TIER 4 — APPLICATION CONTROL:
- All actuator writes MUST go through: safety_write_actuator(pin, value, caller_id)
- This function checks: safety_mode == NORMAL, actuator enabled, value within min/max, rate limit OK, solenoid timeout OK.
- Returns ESP_OK or ESP_ERR_INVALID_STATE. Caller MUST check return value.
- Application code (PID loops, VM) CANNOT bypass this function.

SOLENOID TIMEOUT:
- max_on_time_ms: 5000 (configurable per-output). After 5s continuous ON → auto-OFF.
- min_on_time_ms: 50. Cooldown: 1000ms after auto-OFF.
- Rate limit: 5 ON cycles per 10-second window.
- After timeout: set flag, require manual clear before re-activation.

SAFETY STATE MACHINE:
typedef enum {
    SAFETY_NORMAL,       // All systems operational
    SAFETY_DEGRADED,     // Non-critical fault, reduced operation
    SAFETY_SAFE_STATE,   // All actuators off, control suspended
    SAFETY_FAULT         // Critical unrecoverable fault, factory boot
} nexus_safety_mode_t;

Transitions:
  NORMAL → DEGRADED: heartbeat loss (5 misses), overcurrent (non-critical), heap low
  DEGRADED → NORMAL: 3 good heartbeats + RESUME command
  DEGRADED → SAFE_STATE: heartbeat loss (10 misses), multiple overcurrent
  ANY → SAFE_STATE: kill switch activated, thermal shutdown
  ANY → FAULT: boot count exceeded (>5 in 10min)
  SAFE_STATE → NORMAL: kill switch reset + 3 good heartbeats + RESUME (human must manually reset kill switch)
  FAULT → NORMAL: requires factory firmware reflash + manual intervention

UNIT TESTS:
- Kill switch: simulate GPIO falling edge, verify ISR fires, verify safe outputs within 10ms (measure with esp_timer).
- Watchdog: verify kick pattern alternates 0x55/0xAA, verify interval <= 200ms.
- Heartbeat: inject 5 missed heartbeats → verify DEGRADED. 10 misses → verify SAFE_STATE. 3 good → verify recovery.
- Overcurrent: mock INA219 alert, verify ISR disables output, verify deferred handler logs event.
- Solenoid: activate output, wait 5.1s, verify auto-deactivation. Verify cooldown prevents re-activation for 1s.
- State machine: verify all transition paths. Verify no transition from FAULT to NORMAL without manual intervention.
```

**REASONING:** Safety is built before application logic because the safety system is the IMMUTABLE foundation that all other code runs on top of. If we built the VM first, we'd need to retrofit safety checks into actuator writes — but if safety is built first, the safety_write_actuator() API forces all future code to go through the guard. The kill switch ISR must be in IRAM because during OTA flash writes, the flash is inaccessible — if the kill switch fires during an OTA update, the ISR must still execute. The watchdog uses an alternating pattern (not just a toggle) to detect stuck-at faults that a simple toggle wouldn't catch.

---

## Phase 2: Core Engine

### Prompt 3: I/O Abstraction Layer

**Dependencies:** Prompts 0, 1
**Estimated effort:** 3-4 weeks
**Goal:** Pin configuration from JSON, driver vtable interface, and 5 reference hardware drivers.

```
Implement the I/O abstraction layer in /firmware/components/nexus_io/.

DESIGN PRINCIPLE: Pin configurations are defined by JSON from Jetson at boot, NOT compiled into firmware. This enables the universal binary — one firmware image runs on every ESP32, with role determined entirely by configuration.

FILES: io_abstraction.h/io_abstraction.c, pin_config.h/pin_config.c, drivers/digital_output.c, drivers/pwm_output.c, drivers/adc_input.c, drivers/i2c_compass.c, drivers/uart_sensor.c

DRIVER VTABLE (every driver implements this):
typedef struct {
    esp_err_t (*init)(const io_pin_config_t* config);
    esp_err_t (*read)(void* buffer, size_t len);
    esp_err_t (*write)(const void* data, size_t len);
    esp_err_t (*configure)(const char* key, const char* value);
    esp_err_t (*selftest)(io_selftest_result_t* result);
    esp_err_t (*deinit)(void);
    const io_driver_info_t* (*get_info)(void);
} io_driver_vtable_t;

PIN CONFIG JSON FORMAT (received via ROLE_ASSIGN message 0x02):
{
  "role": "autopilot_controller",
  "pins": {
    "rudder_pwm":      {"gpio": 4,  "mode": "pwm",   "freq_hz": 50,   "safe_value": 1500},
    "throttle_relay":  {"gpio": 5,  "mode": "output","safe_value": 0},
    "compass_sda":     {"gpio": 21, "mode": "i2c",   "bus": 0, "addr": "0x1E", "scl_gpio": 22},
    "kill_switch":     {"gpio": 23, "mode": "input", "pull": "up", "interrupt": "falling"},
    "wind_speed":      {"gpio": 6,  "mode": "adc",   "channel": 3, "atten_db": 11}
  },
  "telemetry_interval_ms": 100,
  "reflexes": ["heading_hold_pid"]
}

PIN MODES AND CONSTRAINTS:
- input: pull(up|down|none), interrupt(rising|falling|both|none), debounce_ms(0-255)
- output: initial_value must equal safe_value at boot
- pwm: freq_hz(1-40000), duty_resolution_bits(1-20), safe_duty
- adc: channel(0-7), attenuation_db(0|3|6|11), samples_per_read(1-4)
- i2c: bus(0-1), addr(hex string), clock_khz(100-400), sda_gpio, scl_gpio
- uart: baud_rate(9600-921600), tx_gpio, rx_gpio

PIN CONFLICT RULES:
- No GPIO claimed by two functions. Reject with error 0x21 (PIN_ALREADY_IN_USE).
- Strapping pins (0, 2, 5, 12, 15) have constraints — reject if mode conflicts with strapping function.
- I2C SDA/SCL validated as pair — both must be on valid I2C-capable GPIOs.
- Input-only pins cannot be configured as output.
- GPIO >= 34 are input-only on ESP32-S3 (no output, no PWM).

5 REFERENCE DRIVERS:

1. DIGITAL OUTPUT (drivers/digital_output.c):
   - gpio_set_direction(GPIO_MODE_OUTPUT)
   - gpio_set_level(pin, value)
   - Self-test: set HIGH, read back (gpio_get_level), verify match. Set LOW, verify.
   - Safe state: GPIO LOW (0).

2. PWM OUTPUT (drivers/pwm_output.c):
   - Use ESP-IDF LEDC peripheral (LEDC_MODE, LEDC_CHANNEL auto-assignment).
   - ledc_timer_config: freq_hz from pin config, duty_resolution = 10 bits (0-1023).
   - ledc_channel_config: gpio, speed_mode, channel, timer, duty=0 initially.
   - Safe state: duty = 0 (output LOW).
   - Self-test: set duty 512 (50%), measure frequency with esp_timer (verify within 5% of requested).

3. ADC INPUT (drivers/adc_input.c):
   - ESP32 SAR ADC, 12-bit (0-4095), configurable attenuation.
   - adc1_channel_t from GPIO number mapping.
   - Multi-sample averaging: read N times (samples_per_read), return mean.
   - Return value: float32 representing actual voltage (V = raw * atten_scale / 4095.0).
   - Attenuation scales: 0dB=1.1V, 3dB=1.5V, 6dB=2.2V, 11dB=3.3V.
   - Self-test: with no input connected, reading should be near 0V. With 3.3V applied, verify near 3.3V.

4. I2C COMPASS — HMC5883L (drivers/i2c_compass.c):
   - Address: 0x1E. Default clock: 100kHz.
   - Register map:
     0x00 Config A: 8-average, 15Hz, normal measurement
     0x01 Config B: gain=1.3Ga (default)
     0x02 Mode: continuous measurement (0x00)
     0x03-0x05 Data X, Z, Y (16-bit big-endian, 2's complement)
     0x09 Status: bit 7 = data ready
   - Read sequence: check Status bit 7, read 6 bytes (0x03-0x08), convert.
   - Heading: heading_rad = atan2(Y_raw, X_raw), heading_deg = fmod(heading_rad * 180/PI + 360, 360).
   - Self-test: write 0x71 to Config B (positive bias), read X/Y/Z, verify X is within 100-500 and Y is within -500 to -100. Restore Config B.

5. UART SENSOR (drivers/uart_sensor.c):
   - Configurable baud rate via pin config JSON.
   - DMA-based RX (uart_driver_install with RX buffer 1024 bytes).
   - Line protocol: detect frame delimiters (configurable, default "\n").
   - Ring buffer for incomplete frames.
   - Self-test: verify UART initialized, send test pattern if TX configured, verify loopback if connected.

SENSOR REGISTER MODEL (how drivers feed the VM):
- Before each VM tick, firmware populates sensor_reg[0..63] with float32 values from all configured sensor drivers.
- Mapping: sensor names → register indices, allocated at role-assignment time.
- After each VM tick, firmware drains actuator_reg[0..63] and writes to actuator drivers.
- This is the bridge between I/O abstraction and the bytecode VM.

SELF-TEST FUNCTION:
- Iterates all configured pins.
- For outputs: set to safe value, read back, verify within tolerance.
- For inputs: read value, check within expected range.
- For I2C: scan bus, verify device at configured address responds.
- For ADC: read with known reference, check within tolerance.
- Returns: per-pin pass/fail array + overall status + detailed error messages.

UNIT TESTS:
- Pin conflict: configure GPIO 4 as output, then try GPIO 4 as PWM → reject with PIN_ALREADY_IN_USE.
- Digital output: set HIGH, read back, verify.
- PWM: set duty, measure with timer, verify frequency within tolerance.
- ADC: mock ADC readings, verify voltage conversion.
- I2C compass: mock I2C bus, inject known X/Y/Z readings, verify heading calculation including ±180° wraparound.
- Self-test: mock all drivers, inject pass/fail conditions, verify overall result.
```

**REASONING:** I/O abstraction is parallel with the VM (both depend on the wire protocol for receiving ROLE_ASSIGN, but neither depends on each other). However, I/O is listed first because the VM needs the sensor/actuator register model to be defined before it can execute REFLEX_DEPLOY. The driver vtable pattern enables hot-pluggable hardware — new sensors can be added by implementing 7 functions, without modifying any other code. The 5 reference drivers cover the most common hardware categories (digital, PWM, ADC, I2C, UART) and serve as templates for future drivers.

---

### Prompt 4: Reflex Bytecode Virtual Machine

**Dependencies:** Prompts 0, 1
**Estimated effort:** 3-4 weeks
**Goal:** 32-opcode stack machine that executes AI-generated control logic at 1kHz with deterministic timing.

```
Implement the bytecode VM in /firmware/components/nexus_vm/.

FILES: vm.h/vm.c, opcodes.h/opcodes.c, compiler.h/compiler.c, vm_safety.h/vm_safety.c

INSTRUCTION FORMAT — every instruction is exactly 8 bytes:
  Byte 0: opcode (0x00-0x1F)
  Byte 1: flags bitfield:
    bit 0 = HAS_IMMEDIATE
    bit 1 = IS_FLOAT (immediate is float32, not int32)
    bit 2 = EXTENDED_CLAMP (CLAMP_F uses operand1,2 as explicit bounds)
    bit 3 = IS_CALL (JUMP pushes return address)
    bit 4-6 = RESERVED (must be 0)
    bit 7 = SYSCALL (opcode is NOP, real operation in operand1)
  Bytes 2-3: operand1 (uint16, big-endian)
  Bytes 4-7: operand2 (uint32, big-endian)

32 OPCODES:
  STACK (0x00-0x07):
    0x00 NOP       — No operation. If flags bit 7: SYSCALL dispatch.
    0x01 PUSH_I8   — Push signed 8-bit immediate (operand1 low byte) onto stack.
    0x02 PUSH_I16  — Push signed 16-bit immediate (operand1) onto stack.
    0x03 PUSH_F32  — Push float32 immediate (operand2, reinterpreted via memcpy) onto stack.
    0x04 POP       — Discard top of stack.
    0x05 DUP       — Duplicate top of stack.
    0x06 SWAP      — Swap top two stack elements.
    0x07 ROT       — Rotate top 3 elements: [C,B,A] → [A,C,B]

  ARITHMETIC (0x08-0x10):
    0x08 ADD_F  — Pop a,b. Push b+a (float32 via memcpy).
    0x09 SUB_F  — Pop a,b. Push b-a.
    0x0A MUL_F  — Pop a,b. Push b*a.
    0x0B DIV_F  — Pop a,b. Push (a==0.0 ? 0.0 : b/a). Division by zero returns 0.0.
    0x0C NEG_F  — Pop a. Push -a (flip sign bit: XOR with 0x80000000).
    0x0D ABS_F  — Pop a. Push fabs(a) (clear sign bit: AND with 0x7FFFFFFF).
    0x0E MIN_F  — Pop a,b. Push min(a,b).
    0x0F MAX_F  — Pop a,b. Push max(a,b).
    0x10 CLAMP_F — Pop a. Push clamp(a, lo, hi). Default lo=-1.0, hi=1.0 (operand1,2 if EXTENDED_CLAMP flag).

  COMPARISON (0x11-0x15) — all push 0 (false) or 1 (true):
    0x11 EQ_F   — Pop a,b. Push (a==b ? 1 : 0).
    0x12 LT_F   — Pop a,b. Push (b<a ? 1 : 0).
    0x13 GT_F   — Pop a,b. Push (b>a ? 1 : 0).
    0x14 LTE_F  — Pop a,b. Push (b<=a ? 1 : 0).
    0x15 GTE_F  — Pop a,b. Push (b>=a ? 1 : 0).

  LOGIC (0x16-0x19) — bitwise on uint32:
    0x16 AND_B  — Pop a,b. Push a&b.
    0x17 OR_B   — Pop a,b. Push a|b.
    0x18 XOR_B  — Pop a,b. Push a^b.
    0x19 NOT_B  — Pop a. Push ~a.

  I/O (0x1A-0x1C):
    0x1A READ_PIN  — If operand1 < 64: push sensor_reg[operand1]. If >= 64: push variable[operand1-64].
    0x1B WRITE_PIN — If operand1 < 64: pop value, write to actuator_reg[operand1]. If >= 64: pop value, write to variable[operand1-64].
    0x1C READ_TIMER_MS — Push current uptime in milliseconds (uint32 cast to float32 via memcpy).

  CONTROL (0x1D-0x1F):
    0x1D JUMP          — Set PC = operand1 * 8 (byte address = operand index * 8). If IS_CALL flag: push return address to call stack first.
    0x1E JUMP_IF_FALSE — Pop value. If 0: jump as above.
    0x1F JUMP_IF_TRUE  — Pop value. If != 0: jump as above.

SYSCALL DISPATCH (opcode=0x00, flags bit 7=1):
  operand1 values:
    0x01 HALT              — Stop execution for this tick. Set vm->halted = true.
    0x02 PID_COMPUTE       — operand2.lo16 = PID index (0-7). Pop setpoint, pop input. Push output.
    0x03 RECORD_SNAPSHOT   — operand2.lo16 = snapshot_id (0-15). Copy current state to snapshot buffer.
    0x04 EMIT_EVENT        — operand2.lo16 = event_code. Push to event ring buffer.

CALL/RET MECHANISM:
  - JUMP with IS_CALL flag (bit 3): push (current_PC + 8) to call stack, then jump.
  - JUMP to operand1 = 0xFFFF (65535): this is RET — pop call stack, restore PC.
  - Call stack depth: max 16 entries. Overflow → HALT + safe outputs. Underflow → HALT.

PID CONTROLLER (8 instances):
  struct pid_state_t {
    float kp, ki, kd;
    float integral, prev_error;
    float integral_limit, output_min, output_max;
  }; // 32 bytes each, total 256 bytes
  Algorithm: error = setpoint - input; integral += error * dt; integral = clamp(integral, -limit, +limit); derivative = (error - prev_error) / dt; output = kp*error + ki*integral + kd*derivative; output = clamp(output, min, max); prev_error = error. dt = 1.0/tick_rate_hz.

MEMORY MODEL (total ~3KB, ALL static allocation, ZERO heap):
  uint32_t data_stack[256];        // 1 KB — computation stack, max depth 256
  struct { uint32_t ret_addr; } call_stack[16]; // 256 B — return addresses
  float variables[256];             // 1 KB — persistent across ticks
  float sensor_regs[64];           // 256 B — populated by firmware BEFORE each tick
  float actuator_regs[64];         // 256 B — drained by firmware AFTER each tick
  struct pid_state_t pid[8];      // 256 B — PID controller state
  uint8_t snapshot_buf[16][128];   // 2 KB — debug snapshots
  struct { uint32_t code, data; } event_ring[32]; // 256 B — event queue

VM EXECUTION LOOP:
void vm_tick(vm_t* vm) {
    vm->cycle_count = 0;
    vm->halted = false;
    // Pre-tick: firmware has already populated sensor_regs
    while (!vm->halted && vm->cycle_count < 10000) {
        uint8_t* pc = &vm->bytecode[vm->pc];
        uint8_t opcode = pc[0];
        uint8_t flags = pc[1];
        uint16_t op1 = (pc[2] << 8) | pc[3];
        uint32_t op2 = (pc[4] << 24) | (pc[5] << 16) | (pc[6] << 8) | pc[7];
        if (opcode == 0x00 && (flags & 0x80)) { handle_syscall(vm, op1, op2); vm->pc += 8; continue; }
        switch (opcode) { /* dispatch table */ }
        vm->pc += 8;
        vm->cycle_count++;
    }
    // Post-tick: firmware drains actuator_regs
    if (vm->halted || vm->cycle_count >= 10000) { clamp_all_actuators(vm); }
}

5 SAFETY INVARIANTS (checked EVERY tick):
  1. STACK BOUNDS: Every PUSH checks data_stack SP < 256. Every POP checks SP > 0. Violation → HALT + clamp actuators.
  2. CYCLE BUDGET: If cycle_count >= 10000 → HALT + clamp actuators. Prevents infinite loops.
  3. ACTUATOR CLAMPING: After VM execution, clamp ALL actuator_regs to configured min/max. This is the FINAL safety net — even if bytecode writes garbage, outputs are bounded.
  4. JUMP TARGETS: All jump targets validated at COMPILE time (within bytecode bounds, 8-byte aligned). Runtime cannot jump to invalid address.
  5. DIVISION SAFETY: DIV_F with zero divisor returns 0.0 (not NaN or Inf). IEEE 754 NaN/Inf must never appear in actuator registers.

JSON REFLEX FORMAT (human-readable source of truth):
{
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
    "heading_pid": {"kp": 1.2, "ki": 0.05, "kd": 0.3, "integral_limit": 1500.0, "output_min": -45.0, "output_max": 45.0}
  },
  "code": "READ_PIN heading; READ_PIN setpoint; PID_COMPUTE heading_pid; CLAMP_F -45.0 45.0; WRITE_PIN rudder"
}

COMPILER (JSON → bytecode, runs on Jetson in Python, ALSO on ESP32 in C for validation):
- Parse JSON, validate schema.
- Allocate variable indices: first variable → var[0], second → var[1], etc.
- Map sensor/actuator names to register indices from pin config.
- Parse "code" string: tokenize by ";", trim whitespace, match tokens to opcodes.
- For each token: resolve named references to indices, generate 8-byte instruction.
- Append HALT syscall as last instruction.
- Validate: all jump targets in bounds, stack depth analysis (max nesting), no unresolved references.
- Output: raw bytecode buffer.

UNIT TESTS:
- Every opcode: push known values, execute, verify stack state.
- Stack overflow: 257 pushes → HALT at 256th.
- Stack underflow: POP on empty → HALT.
- Cycle budget: 10001 NOPs → HALT at 10000.
- Division by zero: push 0, push 5, DIV_F → verify 0.0 on stack.
- PID: set kp=1,ki=0,kd=0, setpoint=10, input=8 → output=2.0.
- CLAMP: push 50, CLAMP_F 0 10 → verify 10.0.
- CALL/RET: call subroutine 3 levels deep, verify correct return.
- Compilation: compile heading_hold_pid JSON, verify bytecode, load into VM, execute tick, verify rudder output.
- Actuator clamping: bytecode writes rudder=999.0 but max=45.0 → verify clamped to 45.0 after tick.
```

**REASONING:** The VM is the heart of NEXUS — it executes AI-generated control logic without requiring humans to write or debug C code. Bytecode (not JSON interpretation) was chosen because JSON parsing at 1kHz would consume 500-2000μs of the 1000μs budget, leaving no time for computation. The bytecode VM completes a tick in <100μs — a 10x improvement. The 8-byte fixed instruction size enables direct PC indexing (PC = instruction_index * 8) with no variable-length decoding. The 5 safety invariants ensure that even malicious or buggy bytecode cannot damage hardware — actuator clamping is the ultimate safety net.

---

### Prompt 5: Main Firmware Integration

**Dependencies:** Prompts 0, 1, 2, 3, 4
**Estimated effort:** 1-2 weeks
**Goal:** Wire boot sequence, role assignment, observation buffer, OTA updates, and reflex deployment.

```
Wire all components into the main ESP32 application at /firmware/main/main.c.

FILES: main.c, role_manager.h/role_manager.c, obs_buffer.h/obs_buffer.c, ota_manager.h/ota_manager.c

MAIN.C — BOOT SEQUENCE (every timestamp is a HARD requirement):
void app_main(void) {
    // T+0ms: FORCE ALL OUTPUTS LOW (safe state) — THIS IS THE VERY FIRST THING
    gpio_safe_state_all();

    // T+5ms: Hardware watchdog feeding begins
    watchdog_init(WDT_KICK_GPIO, 200);  // 200ms kick interval

    // T+10ms: UART initialization at 115200 baud
    uart_init(UART_NUM_0, 115200, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);

    // T+20ms: Send DEVICE_IDENTITY (0x01)
    nexus_protocol_send_identity();

    // T+30ms: Send AUTO_DETECT_RESULT (0x1B)
    nexus_protocol_send_auto_detect();

    // T+50ms: Send SELFTEST_RESULT (0x04)
    nexus_protocol_send_selftest();

    // T+50-300ms: Wait for ROLE_ASSIGN (0x02) from Jetson
    role_config_t* role = role_wait_for_assignment(30000);  // 30 second timeout
    if (!role) {
        // No Jetson: enter IDLE mode
        role_load_cached_from_nvs();  // Use last known config
        if (!cached_role) { enter_idle_mode(); return; }
    }

    // T+300ms: Apply role configuration
    io_apply_pin_config(role);
    reflex_load_all_from_littlefs(role);

    // T+500ms: ENTER OPERATIONAL STATE
    heartbeat_start(100);  // 100ms interval
    telemetry_start(role->telemetry_interval_ms);

    // Main event loop — NEVER returns
    while (1) {
        safety_supervisor_tick();    // 10ms period, highest priority task
        if (nexus_safety_mode == SAFETY_NORMAL) {
            vm_tick_all_reflexes();   // At configured tick rate per reflex
        }
        telemetry_tick();             // At configured interval
        vTaskDelay(1);                // Yield to RTOS
    }
}

ROLE ASSIGNMENT:
- Jetson sends ROLE_ASSIGN (0x02) with full pin config JSON.
- Parse JSON using jsmn (minimal parser, ~2KB code).
- Validate: all GPIOs valid, no conflicts, all sensors have drivers, all actuators within limits.
- If valid: store in NVS, apply pin config, load reflexes from LittleFS, send ROLE_ACK (accepted=true).
- If invalid: send ROLE_ACK (accepted=false, rejection_reason="GPIO 34 cannot be output").
- On reboot without Jetson: load cached role from NVS, skip role assignment wait.

OBSERVATION BUFFER (PSRAM ring buffer):
- Size: 5MB in PSRAM (heap_caps_malloc(5*1024*1024, MALLOC_CAP_SPIRAM)).
- Frame format: 32 bytes per frame:
    uint16_t frame_type;     // 0=normal, 1=event, 2=session_marker
    uint32_t sequence_id;    // Rolling counter
    uint32_t timestamp_ms;   // Uptime
    uint16_t channel_mask;   // Bitfield: which channels have data
    int16_t channels[14];    // Up to 14 channels of int16 data
    uint8_t flags;
    uint8_t reserved;
    uint32_t crc32;          // CRC of preceding 28 bytes
- At 100Hz with 16 channels: ~5.5 minutes of recording.
- Recording control: OBS_RECORD_START (0x0B) and OBS_RECORD_STOP (0x0C) messages.
- Dump: OBS_DUMP_HEADER (frame count, total bytes) → OBS_DUMP_CHUNK (512-byte binary chunks) → OBS_DUMP_END (CRC verification).
- Buffer is volatile (PSRAM): power loss = acceptable data loss.

OTA FIRMWARE UPDATE:
- FIRMWARE_UPDATE_START (0x11): receives {size, chunk_count, version, sha256}.
- FIRMWARE_UPDATE_CHUNK (0x12): 512 bytes per chunk, written to ota_1 partition via esp_ota_begin/esp_ota_write.
- FIRMWARE_UPDATE_END (0x13): verify SHA-256, set boot partition to ota_1 via esp_ota_set_boot_partition.
- Reboot: bootloader validates ota_1. If valid → boot ota_1. If invalid → rollback to ota_0.
- If BOTH ota_0 and ota_1 fail validation → boot FACTORY partition (never OTA-modified).
- FACTORY partition contains minimal safe-mode firmware: identity + heartbeat + ROLE_ASSIGN wait.
- Report result via FIRMWARE_UPDATE_RESULT (0x14): {success, boot_partition, sha256_actual}.

BAUD RATE NEGOTIATION:
- After successful role assignment, Jetson sends BAUD_UPGRADE (0x18) with {target_baud}.
- ESP32 reconfigures UART to target_baud.
- Jetson switches simultaneously and sends PING (0x16) at new baud.
- If PONG (0x17) received within 500ms: upgrade confirmed. If not: fall back to previous baud.
- Supported rates: 921600 (10m), 460800 (50m), 230400 (75m), 115200 (100m).

LITTLEFS REFLEX STORAGE:
- Mount LittleFS on "reflexes" partition (2MB) using esp_vfs_littlefs.
- Each reflex stored as: /reflexes/{reflex_name}.bin (compiled bytecode).
- Power-loss safe: LittleFS uses copy-on-write + journaling. Either old or new version survives.
- Deploy: receive REFLEX_DEPLOY (0x09) with {name, version, bytecode_base64} → decode base64 → validate bytecode → write to LittleFS → hot-load into VM.
- Load all reflexes at boot after role assignment.

UNIT TESTS:
- Boot sequence: mock all peripherals, verify execution order and timing (use esp_timer_get_time).
- Role assignment: send valid ROLE_ASSIGN via serial tool, verify ROLE_ACK accepted=true, verify pins configured.
- Role rejection: send invalid ROLE_ASSIGN (GPIO 34 as output), verify ROLE_ACK accepted=false with reason.
- OTA: send firmware_update_start + chunks + end with known SHA-256, verify written to ota_1.
- OTA rollback: corrupt ota_1 after write, verify rollback to ota_0 on reboot.
- Observation: record 1000 frames at 100Hz, dump, verify frame count and CRC-32 integrity.
- Reflex deploy: compile heading_hold_pid JSON → bytecode, deploy via REFLEX_DEPLOY, verify VM executes correctly.
- Hot-swap: reset ESP32 after role assignment, verify cached role loaded and operation resumes.
- Baud negotiation: upgrade to 921600, verify PONG received, verify communication continues at new baud.
```

**REASONING:** This is the integration prompt that ties everything together. It MUST come after all components are individually implemented because integration reveals interface mismatches. The boot sequence timing is critical — if GPIO safe-state isn't forced at T+0ms, actuators could be in an undefined state during the 5-10ms before the watchdog starts. The factory partition as trusted recovery image is essential: if OTA corrupts both slots, the system is still recoverable without a JTAG programmer. The observation buffer uses PSRAM (not SRAM) because 5MB of observation data would consume 100% of SRAM — PSRAM is volatile by design, which is acceptable since observation data is valuable but not safety-critical.

---

## Phase 3: Cognitive Brain

### Prompt 6: Jetson Serial Bridge + Node Manager

**Dependencies:** Prompts 0, 1
**Estimated effort:** 2-3 weeks
**Goal:** Python serial port management, COBS encode/decode matching firmware, node discovery, and role assignment.

```
Implement the Jetson serial bridge and node manager.

FILES: jetson/nexus_cognitive/serial_bridge.py, jetson/nexus_cognitive/node_manager.py

SERIAL_BRIDGE.PY:
- Manage multiple serial ports (one per ESP32 node) using pyserial + pyserial-asyncio.
- COBS encode/decode MUST match the firmware implementation EXACTLY:
    def cobs_encode(data: bytes) -> bytes: ...
    def cobs_decode(data: bytes) -> bytes: ...
  Test: encode→decode round-trip for bytes 0x00 through 0xFF, for empty payload, for 256 consecutive zeros.
- CRC-16/CCITT-FALSE: polynomial 0x1021, init 0xFFFF, final XOR 0x0000.
  Test: CRC of "123456789" must equal 0x29B1.
- Frame format: [0x00][COBS(header_10 + payload + crc_2)][0x00]
- Header encode/decode matching firmware spec (10 bytes, all big-endian).
- Async TX/RX using asyncio with pyserial-asyncio.
- TX priority queue: Safety(0) > Critical(1) > Normal(2) > Bulk(3). Safety messages preempt lower priority.
- ACK/retry for messages with ACK_REQUIRED flag: 3 retries, exponential backoff (200ms, 400ms, 800ms).
- Baud negotiation: start at 115200, upgrade to 921600 after role assignment confirmed.

NODE_MANAGER.PY:
- Node registry: dict mapping MAC address → NodeInfo (mac, chip_type, firmware_ver, serial_port, role, status, last_heartbeat).
- Discovery: when DEVICE_IDENTITY (0x01) received on any serial port → register node.
- Role assignment: send ROLE_ASSIGN (0x02) to nodes based on roles.json configuration.
- Handle ROLE_ACK (0x03): if accepted → mark node OPERATIONAL. If rejected → log reason, retry with corrected config.
- Health monitoring: track heartbeat timestamps per node. Escalation:
    <500ms since last HB: HEALTHY
    500ms-1000ms: WARN
    >1000ms: DEGRADED
    >3000ms: OFFLINE (attempt reconnect)
- Hot-swap: if node disappears and a new node appears on same port → assign same role. This enables field replacement without a laptop.
- Reflex deployment: receive compiled bytecode, send via REFLEX_DEPLOY (0x09), confirm via REFLEX_STATUS (0x0A).

CONFIGURATION (roles.json):
{
  "nodes": {
    "serial:/dev/ttyUSB0": {
      "mac_filter": null,
      "role": {
        "role_name": "autopilot_controller",
        "pins": { ... },
        "telemetry_interval_ms": 100,
        "reflexes": ["heading_hold_pid"]
      }
    }
  },
  "global": {
    "default_baud": 115200,
    "upgrade_baud": 921600,
    "heartbeat_timeout_ms": 1000,
    "role_assign_timeout_ms": 30000
  }
}

UNIT TESTS:
- COBS encode/decode: test with empty, 1-byte, 254-byte, 255-byte, 1024-byte payloads. Test 256 consecutive zeros.
- CRC-16: verify against "123456789" → 0x29B1.
- Mock serial: use asyncio's mock streams or pty pairs to simulate full protocol exchange.
- Node discovery: simulate DEVICE_IDENTITY message → verify node registered in registry.
- Role assignment: send ROLE_ASSIGN → simulate ROLE_ACK accepted → verify node marked OPERATIONAL.
- Heartbeat timeout: simulate 5 missed heartbeats → verify WARN state, 10 misses → verify DEGRADED.
- Baud negotiation: simulate BAUD_UPGRADE flow → verify port reconfigured.
```

**REASONING:** The serial bridge is the Jetson-side mirror of the firmware wire protocol. It's the first Jetson component because everything else on the Jetson (node management, reflex orchestration, learning, chat) depends on being able to communicate with ESP32 nodes. Building it in parallel with the firmware safety layer (Prompt 2) maximizes parallelism — both depend on Prompt 1's protocol spec but not on each other. The hot-swap feature is critical for the "no laptop in the field" requirement: a fisherman can swap a broken ESP32 and the system auto-provisions the replacement.

---

### Prompt 7: Jetson Cognitive Services

**Dependencies:** Prompts 0, 6
**Estimated effort:** 3-4 weeks
**Goal:** gRPC services, MQTT bridge, module lifecycle, LLM chat interface, reflex compiler.

```
Implement core Jetson cognitive services.

1. GENERATE GRPC STUBS:
   cd jetson/nexus_cognitive
   python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/cluster_api.proto

2. MODULE ABC (nexus_module.py):
   from abc import ABC, abstractmethod
   class NexusModule(ABC):
       @abstractmethod
       async def start(self) -> None: ...
       @abstractmethod
       async def stop(self) -> None: ...
       @abstractmethod
       async def health_check(self) -> ModuleHealth: ...
       @abstractmethod
       def resource_budget(self) -> ResourceBudget: ...  # {cpu_pct, gpu_pct, ram_mb, vram_mb}
       async def hot_reload(self, config: dict) -> None: ...  # Default: no-op

   class ThrottleMonitor(NexusModule):
       # Monitors CPU/GPU temperature via /sys/class/thermal/
       # At 80°C: log warning. At 85°C: shed non-essential services (STT, vision). At 90°C: emergency shutdown.

3. MQTT BRIDGE (mqtt_bridge.py):
   Broker: Mosquitto (localhost:1883).
   13 topics with exact QoS/retain settings (matching spec):
     nexus/telemetry/{node_id}    QoS 0, no retain  — sensor data
     nexus/status/{node_id}       QoS 1, retain=yes  — node status
     nexus/safety/{node_id}       QoS 2, no retain   — safety events (exactly-once!)
     nexus/autonomy/{sub}/level   QoS 1, retain=yes  — autonomy level changes
     nexus/autonomy/{sub}/override QoS 2, retain=yes — override commands (exactly-once!)
     nexus/learning/session/{id}/control QoS 1  — recording control
     nexus/reflex/{id}/deploy     QoS 1             — reflex deployment commands
   Bridge direction:
     Serial→MQTT: node sends TELEMETRY, SAFETY_EVENT, HEARTBEAT → publish to MQTT.
     MQTT→Serial: subscribe to autonomy/override, reflex/deploy → send COMMAND, REFLEX_DEPLOY to node.

4. REFLEX ORCHESTRATOR (reflex_orchestrator.py):
   - Python bytecode compiler that matches the C compiler EXACTLY.
   - Input: JSON reflex definition.
   - Output: raw bytecode bytes + metadata (size, instruction count, variable count).
   - Validation: stack depth analysis, jump target verification, cycle count estimation.
   - Deploy: send compiled bytecode via serial_bridge (REFLEX_DEPLOY message).
   - List: query all nodes for active reflexes (REFLEX_STATUS).
   - Remove: send remove command, verify acknowledgment.
   - Hot-reload: update reflex parameters (PID gains, thresholds) without full redeploy.

5. CHAT INTERFACE (chat_interface.py):
   - Connect to local LLM via llama-cpp-python:
       from llama_cpp import Llama
       llm = Llama(model_path="models/qwen2.5-coder-7b-instruct-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=99)
   - Fallback to cloud API for complex requests (OpenAI GPT-4o or Anthropic Claude).
   - Intent classification using system prompt (no separate model for v1):
       System prompt includes: "You are NEXUS, a robotics control system. Classify the user's intent:
       REFLEX_CREATE, CONFIG_CHANGE, STATUS_QUERY, SAFETY_OVERRIDE, EXPLAIN_BEHAVIOR, GENERAL_CHAT"
   - Route to handler based on intent:
       REFLEX_CREATE → code_generation.create_reflex()
       CONFIG_CHANGE → node_manager.send_command()
       STATUS_QUERY → query telemetry from MQTT or node_manager
       SAFETY_OVERRIDE → autonomy_manager.override()
   - Format reflex proposals as NATURAL LANGUAGE for human approval:
       "I observed that when wind exceeds 25 knots, you reduce throttle to ~40%.
        Shall I automate this? Proposed rule: IF wind_speed > 25 THEN throttle = 40%."
   - Conversation history: per-session, stored in SQLite.

6. LEARNING SERVICE STUB (learning_pipeline.py):
   - Observation session management: start, stop, pause, resume, close.
   - Store observations as Parquet files in /data/observations/ (Snappy compression).
   - Expose gRPC LearningService methods.
   - Pattern discovery algorithms: placeholder stubs returning empty results (implemented in Prompt 9).

7. SAFETY MANAGER STUB (safety_manager.py):
   - Trust score computation (full implementation in Prompt 8).
   - Subscribe to nexus/safety/{node_id} MQTT topic.
   - Log all safety events to SQLite.
   - Alert operators (via chat interface) for CRITICAL safety events.

UNIT TESTS:
- gRPC: instantiate server, call all 6 services, verify responses.
- MQTT: use test.mosquitto.org or local broker, publish/subscribe, verify QoS levels.
- Chat: mock LLM responses, verify intent classification, verify routing to correct handler.
- Reflex compiler: compile heading_hold_pid JSON, verify bytecode matches expected output.
- Module lifecycle: start/stop/health_check for each module, verify resource budgets reported.
```

**REASONING:** This prompt wires together the Jetson's service architecture. The gRPC services define the public API surface — everything else (learning, trust, cloud) plugs into these services. MQTT bridges the serial world (ESP32) and the IP world (dashboard, cloud, mobile). The chat interface is the primary human interaction point — it's where the "post-coding" philosophy manifests: users describe intent in natural language, never see code. The reflex compiler on the Python side MUST match the C compiler exactly — any mismatch would deploy bytecode that the VM can't execute.

---

### Prompt 8: Trust Score + Autonomy Manager

**Dependencies:** Prompts 0, 7
**Estimated effort:** 1-2 weeks
**Goal:** Mathematical trust scoring, per-subsystem autonomy levels, override handling, SQLite persistence.

```
Implement the INCREMENTS autonomy framework at jetson/nexus_cognitive/autonomy_manager.py.

TRUST SCORE FORMULA (per subsystem):
  T(t+1) = T(t) + alpha_gain * (1 - T(t))    if evaluation is GOOD
  T(t+1) = T(t) - alpha_loss * T(t)           if evaluation is BAD
  T(t+1) = T(t)                               if no evaluation this tick

  Default parameters:
    alpha_gain = 0.002   (configurable per subsystem)
    alpha_loss = 0.05    (configurable per subsystem)
    T range: [0.0, 1.0]
    Initial trust: 0.0 (system starts with zero trust)

  Key property: 25:1 loss:gain ratio.
    Gaining 0.1 trust from T=0.5 requires ~50 consecutive good evaluations.
    Losing 0.1 from T=0.9 requires only 2 bad evaluations.
    This matches human psychology: trust is built slowly, destroyed quickly.

AUTONOMY LEVELS (per subsystem, independent):
  0 MANUAL:      Human full control. System monitors/records only.
  1 ASSIST:      System suggests, human approves every action.
  2 SEMI-AUTO:   System executes approved reflexes. Human can override anytime.
  3 CONDITIONAL: System autonomous in defined conditions. Human monitors.
  4 HIGH:        System autonomous in most conditions. Human available.
  5 FULL:        System fully autonomous. Human optional.

LEVEL TRANSITION RULES:
  0→1: Manual activation by operator (not trust-based).
  1→2: T >= 0.5 AND no bad evaluations in last 100.
  2→3: T >= 0.7 AND >= 7 days since last override.
  3→4: T >= 0.8 AND >= 30 days since last override.
  4→5: T >= 0.95 AND >= 90 days since last override.
  Any bad evaluation: immediate drop one level (3→2, 4→3, etc.).
  Manual override: immediate drop to SEMI-AUTO for that subsystem.

EVALUATION SOURCES:
  - A/B test results: reflex beats human baseline on efficiency without degrading safety → GOOD.
  - A/B test failure: reflex worse on safety OR no improvement on efficiency → BAD.
  - Human explicit: APPROVE → GOOD, REJECT → BAD.
  - Safety events: overcurrent, heartbeat loss → BAD.
  - Manual override events: human took control → BAD (but NOT if current level <= 2).

SQLITE SCHEMA:
  CREATE TABLE subsystem_trust (
      subsystem TEXT PRIMARY KEY,
      trust_score REAL DEFAULT 0.0,
      autonomy_level INTEGER DEFAULT 0,
      alpha_gain REAL DEFAULT 0.002,
      alpha_loss REAL DEFAULT 0.05,
      total_good INTEGER DEFAULT 0,
      total_bad INTEGER DEFAULT 0,
      last_eval_at TIMESTAMP,
      last_override_at TIMESTAMP,
      last_level_change_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  CREATE TABLE evaluation_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      subsystem TEXT NOT NULL,
      eval_type TEXT NOT NULL,  -- 'ab_test','human_approval','safety_event','override'
      is_good INTEGER NOT NULL,
      trust_before REAL,
      trust_after REAL,
      details TEXT,
      ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

gRPC API (AutonomyManager service):
  GetTrustScore(subsystem) → {subsystem, trust_score, autonomy_level, eval_counts, last_events}
  SetAutonomyLevel(subsystem, level) → {success, reason}  (manual override by operator)
  GetOverrides() → list of all active overrides
  GetHistory(subsystem, start, end) → list of evaluation_log entries

UNIT TESTS (with exact expected values):
  - 50 good evals from T=0.0: T = 1-(1-0.002)^50 = 0.0953 (verify within 0.0001).
  - 2 bad evals from T=0.9: T = 0.9*(1-0.05)^2 = 0.9*0.9025 = 0.81225 (verify within 0.001).
  - Level progression: simulate 120 days at 10 evals/day, all good → verify level reaches 3 (T>=0.7 at ~day 85).
  - Override: at level 3, send override → verify drops to level 2, verify cooldown prevents re-promotion for 7 days.
  - Edge: T=0.0 + bad eval → T stays 0.0 (floor). T=1.0 + good eval → T stays 1.0 (ceiling).
  - Persistence: write to SQLite, read back, verify all fields match.
```

**REASONING:** Trust scoring is the mechanism that makes NEXUS safe for real-world deployment. The 25:1 loss:gain ratio is the most important parameter in the entire system — it determines how quickly the system earns autonomy and how quickly it loses it. Starting at alpha_gain=0.002 means reaching Level 3 (T>=0.7) requires approximately 650 consecutive good evaluations, which at 10 evaluations per day = 65 days. This is conservative but realistic — it matches how long a human operator would need to trust an autopilot with their vessel. The asymmetric trust model (per-subsystem) allows the system to be trusted for steering (Level 4) while remaining at Level 0 for engine management.

---

### Prompt 9: Learning Pipeline + A/B Testing

**Dependencies:** Prompts 0, 7
**Estimated effort:** 4-6 weeks
**Goal:** Five pattern discovery algorithms, A/B testing framework, and reflex synthesis from observation data.

```
Implement the learning pipeline at jetson/nexus_cognitive/learning_pipeline.py and jetson/nexus_cognitive/ab_testing.py.

OBSERVATION DATA MODEL (72 fields, stored as Parquet):
Key fields (schema):
  Navigation: gps_lat(double), gps_lon(double), gps_speed_kts(double), gps_heading_deg(double)
  Attitude: imu_roll_deg(float32), imu_pitch_deg(float32), imu_yaw_deg(float32)
  Environment: wind_speed_m_s(float32), wind_dir_deg(float32), air_temp_c(float32), water_temp_c(float32)
  Propulsion: throttle_pct(float32), rudder_angle_deg(float32), engine_rpm(float32)
  System: autonomy_level(int8), trust_score(float32), safety_mode(int8)
  Timestamp: timestamp_ns(int64)

ObservationSession class:
  - session_id: UUIDv4
  - record(observation_dict): append to in-memory PyArrow table, flush to Parquet every 10000 rows or 1 second
  - close(): finalize Parquet file, write metadata JSON, compute column statistics
  - Storage: /data/observations/{session_id}/{timestamp}.parquet

PATTERN DISCOVERY (run after session.close()):
Execute all 5 algorithms. Each returns a list of PatternResult objects.

1. CROSS-CORRELATION SCANNER:
   Scan C(72,2) = 2556 variable pairs.
   Lags: -60s to +60s at 100ms resolution (1201 lag values per pair).
   Method: scipy.signal.correlate with mode='same'.
   Significance: Pearson r with Bonferroni correction (p_threshold = 0.05/2556 = 0.0000196).
   Filter: |r| >= 0.6 AND p < threshold.
   Output: list of {var_a, var_b, lag_ms, correlation, p_value}.
   Runtime: ~8 seconds per 1-hour session on Jetson Orin.

2. BAYESIAN ONLINE CHANGE-POINT DETECTION (BOCPD):
   Algorithm: Adams & MacKay (2007).
   Prior: Normal-Inverse-Gamma conjugate prior.
   Hazard rate (lambda): 0.01 (expect ~100 observations between changes).
   Report change points with: posterior_probability > 0.5 AND run_length > 100.
   Process all continuous columns in parallel (ProcessPoolExecutor, max_workers=4).
   Output: list of {column, timestamp, run_length, probability, mean_before, mean_after}.

3. BEHAVIORAL CLUSTERING (HDBSCAN):
   Window: 10 seconds non-overlapping.
   Features: 8 key sensors x 5 statistics (mean, std, min, max, spectral centroid via scipy.signal.welch).
   Total: 40 features per window.
   Preprocessing: RobustScaler (median/IQR), PCA to 5 components (explain >90% variance).
   Clustering: HDBSCAN(metric='euclidean', min_cluster_size=10, min_samples=3).
   Output: list of {cluster_id, start_time, end_time, representative_features, size}.

4. TEMPORAL PATTERN MINING:
   Event grammar: "{column} {comparator} {threshold}" joined by AND.
   Comparators: >, >=, <, <=, ==, !=, CHANGES_BY, CROSSES.
   For each event occurrence: extract actuator response sequence over [-10s, +30s] window.
   Cluster response sequences using DTW (Dynamic Time Warping) with Sakoe-Chiba bandwidth=10.
   Report rules with: consistency > 0.6 across > 5 occurrences.
   Output: list of {event_definition, response_cluster, consistency, occurrence_count}.

5. BAYESIAN REWARD INFERENCE:
   Reward features (6): speed_comfort, heading_accuracy, fuel_efficiency, smoothness, safety_margin, wind_compensation.
   For each feature: compute normalized score [0, 1] over the session.
   Weight inference: MAP estimation with Normal-Inverse-Gamma prior.
   Prior: uniform (all features equal weight) unless seeded by human narration.
   If narration contains "comfort matters most": increase prior weight for speed_comfort.
   Output: {weights: {speed_comfort: 0.25, heading_accuracy: 0.20, ...}, confidence: float}.

A/B TESTING FRAMEWORK (ab_testing.py):
7 STANDARDIZED METRICS:
  1. heading_rmse: sqrt(mean((heading_actual - heading_setpoint)^2)) — LOWER is better
  2. comfort_score: 1 - rms_jerk / max_jerk — HIGHER is better
  3. fuel_efficiency: distance_nm / fuel_consumed_L — HIGHER is better
  4. safety_margin: min(obstacle_distance_m) over window — HIGHER is better, threshold 10m
  5. smoothness: 1 - rms(heave_acceleration) / max_accel — HIGHER is better
  6. override_frequency: count(overrides) / hours — LOWER is better, threshold 2/hr
  7. response_latency_ms: mean(event_time to corrective_action_time) — LOWER is better

TEST PROTOCOL:
  Phase A (baseline): Record human-operated data for >= 30 minutes.
  Phase B (treatment): Activate proposed reflex alongside human. Human can override.
  Duration: >= 30 minutes per phase (or until statistical significance reached).

STATISTICAL DECISION:
  - For each metric: paired t-test between Phase A and Phase B samples.
  - Bonferroni correction for 7 metrics: significance threshold p < 0.05/7 = 0.007.
  - ACCEPT if: treatment is NOT statistically worse on ANY safety metric (4, 6, 7) AND is significantly better on at least ONE efficiency metric (1, 2, 3, 5).
  - REJECT if: treatment is worse on any safety metric.
  - INCONCLUSIVE if: neither accepted nor rejected (need more data).

REFLEX SYNTHESIS (pattern → reflex):
  Given a discovered pattern (e.g., "when wind > 25kts, human reduces throttle to ~40%"):
  1. Generate JSON reflex definition:
     {
       "name": "wind_throttle_governor",
       "sensors": {"wind_speed": {"pin": 2}},
       "actuators": {"throttle": {"pin": 1, "min": 0, "max": 100, "safe": 0}},
       "code": "READ_PIN wind_speed; PUSH_F32 25.0; GT_F; JUMP_IF_FALSE skip; PUSH_F32 40.0; WRITE_PIN throttle; JUMP end; skip: POP; end: HALT"
     }
  2. Compile to bytecode via reflex_orchestrator.compiler.
  3. Submit to A/B testing framework.
  4. If ACCEPTED: deploy to production via REFLEX_DEPLOY.
  5. If REJECTED: log rejection reason, do not deploy.

UNIT TESTS:
- Cross-correlation: generate two sinusoids with known 2-second phase shift → verify lag detection within 200ms.
- BOCPD: generate step-function change at t=500 → verify change-point detected within 50 samples.
- HDBSCAN: create 3 behavior types (fast+sparse, slow+dense, medium+periodic) → verify 3 clusters.
- A/B testing: generate synthetic data where treatment is 10% better on heading_rmse and equal on safety → verify ACCEPT.
- A/B rejection: generate treatment that is 5% worse on safety_margin → verify REJECT.
- Reflex synthesis: feed pattern result → verify JSON reflex generated → verify compiles → verify deploys.
```

**REASONING:** The learning pipeline is where NEXUS becomes truly intelligent — it observes human behavior and proposes automations. The 5 algorithms provide complementary perspectives: cross-correlation finds direct relationships, BOCPD detects regime changes, HDBSCAN groups behaviors, temporal mining finds event-response patterns, and reward inference understands motivation. The A/B testing framework is the gatekeeper — no reflex reaches production without statistical validation against human performance. The paired t-test with Bonferroni correction prevents false positives from multiple comparisons.

---

## Phase 4: Intelligence

### Prompt 10: Cloud Code Generation Pipeline

**Dependencies:** Prompts 0, 7
**Estimated effort:** 3-4 weeks
**Goal:** 6-stage intent-to-code pipeline with separate LLM validation, MISRA-C checking, and simulation.

```
Implement the code generation pipeline at jetson/nexus_cognitive/code_generation.py.

6-STAGE PIPELINE:

Stage 1 — INTENT CAPTURE:
  Input: natural language from chat_interface ("When wind exceeds 25 knots, reduce throttle to 40%").
  Output: StructuredIntent {raw_text, domain, subsystem, priority, context}.
  Context: current sensor readings, active reflexes, trust scores, safety events.

Stage 2 — INTENT CLASSIFICATION:
  Route to handler: reflex_creation | config_change | status_query | safety_override | explain_behavior | general_chat.
  Method: system prompt to local LLM (Qwen2.5-Coder-7B) with classification instructions.
  If confidence < 0.7: ask human for clarification.
  If route = reflex_creation: proceed to Stage 3.
  If route = config_change: send COMMAND to node_manager.
  If route = status_query: query telemetry from MQTT/node_manager.

Stage 3 — CODE GENERATION:
  Primary model: Qwen2.5-Coder-7B-Instruct (local, Q4_K_M, ~4GB VRAM, ~12 tok/s).
  Fallback: cloud LLM (OpenAI GPT-4o or Anthropic Claude via API).
  System prompt for generation (includes):
    "You generate JSON reflex definitions for the NEXUS robotics platform.
     Available sensors: {list from node config}.
     Available actuators: {list from node config} with min/max/safe values.
     VM opcodes: READ_PIN, WRITE_PIN, PUSH_F32, ADD_F, SUB_F, MUL_F, DIV_F, CLAMP_F, EQ_F, LT_F, GT_F, JUMP, JUMP_IF_FALSE, PID_COMPUTE, HALT.
     SAFETY RULES:
     - All actuator outputs MUST be clamped to configured min/max.
     - Reflex MUST end with HALT.
     - No more than 500 VM cycles per tick.
     - Division by zero must be guarded.
     Output ONLY valid JSON matching the reflex schema."
  Temperature: 0.2 (deterministic).
  Max tokens: 2048.
  Output: JSON reflex definition (80%), C code (15%), Python utility (5%).

Stage 4 — SAFETY VALIDATION (CRITICAL — MUST use DIFFERENT LLM):
  Send generated code to a SEPARATE LLM call (different conversation context, no access to generation reasoning).
  Validation prompt:
    "You are a safety auditor for industrial robotics. Review this generated code:
     {generated_code}
     Available actuators and limits: {actuator_config}
     Score each criterion 0-10:
     1. Actuator clamping: all outputs bounded by min/max?
     2. Safe-state enforcement: HALT/syscall behavior correct?
     3. Rate limiting: no excessive actuator cycling?
     4. Deadlock potential: no infinite loops without cycle budget?
     5. Numerical safety: no division by zero, no NaN/Inf?
     6. Timing determinism: no sleep, random, or heap allocation in control path?
     REJECT if any score < 7. Provide specific rejection reason."
  If rejected: return to Stage 3 with rejection reason. Max 3 generation attempts.
  If all 3 attempts rejected: inform human, log failure, do NOT deploy.
  Cost: ~$0.01-0.03 per validation call. Negligible compared to deploying unsafe code.

Stage 5 — SIMULATION:
  Load recorded observation data from a relevant session (matching domain/subsystem).
  Replay sensor inputs through the compiled reflex bytecode (Python VM emulator).
  Check after every tick:
    - All actuator values within min/max.
    - No reflex cycle exceeds 5000 VM cycles (half of 10000 budget).
    - No NaN or Inf in outputs.
  Run simulation for duration matching recorded session.
  If simulation passes: proceed to Stage 6.
  If simulation fails: reject with diagnostic (which tick, which actuator, what value).

Stage 6 — HUMAN APPROVAL:
  Format reflex proposal as NATURAL LANGUAGE (NOT code):
    "I noticed when wind_speed > 25 knots, you tend to reduce throttle to ~40%.
     Shall I automate this?
     Proposed rule: IF wind_speed > 25 THEN throttle = 40%
     Expected fuel saving: ~15% in windy conditions.
     A/B test duration: ~2 hours."
  Options: APPROVE | REJECT | MODIFY | TEST_LONGER
  On APPROVE: compile → deploy via REFLEX_DEPLOY → start A/B test → trust score update.

MISRA-C RULES (applied during validation, reject violations):
  - No dynamic memory allocation in control paths (malloc/free in ISR or VM tick).
  - All loops must have bounded iteration count (enforced by VM cycle budget).
  - No recursion deeper than call stack depth (16, enforced by VM).
  - All outputs explicitly initialized to safe values at boot.
  - No floating-point equality comparisons (use tolerance: fabs(a-b) < 1e-6).
  - All switch/case must have default (enforced by compiler).

UNIT TESTS:
- Intent classification: "make LED blink" → reflex_creation. "what's heading?" → status_query.
- Generation: "when temp > 30, turn on fan" → verify valid JSON reflex with fan output clamped.
- Validation rejection: inject code with unclamped output → verify rejected with score < 7.
- Simulation: compile heading_hold_pid, replay 1-hour recorded data → verify all outputs within bounds.
- End-to-end: "when wind > 25 knots reduce throttle" → classify → generate → validate → simulate → present for approval.
```

**REASONING:** The code generation pipeline is where the "post-coding" philosophy becomes reality. The 6-stage pipeline ensures that AI-generated code is validated at every step before reaching hardware. The CRITICAL design decision is Stage 4: using a DIFFERENT LLM for validation prevents self-validation bias. When the same model generates and validates code, it tends to approve its own work because the validation context includes the reasoning that led to the design. This is a well-documented cognitive bias. The simulation stage catches issues that static analysis misses — it runs the compiled bytecode against real recorded data and checks that outputs remain within safe bounds at every tick.

---

### Prompt 11: AI Model Integration

**Dependencies:** Prompts 0, 7, 10
**Estimated effort:** 2-3 weeks
**Goal:** Local LLM setup, intent classification model, STT/TTS integration, model management.

```
Implement AI model integration at jetson/nexus_cognitive/ai_models.py, jetson/nexus_cognitive/stt_service.py, jetson/nexus_cognitive/tts_service.py.

LOCAL LLM SETUP (ai_models.py):
  Primary code generation: Qwen2.5-Coder-7B-Instruct
    Model file: qwen2.5-coder-7b-instruct-q4_k_m.gguf (~4GB)
    Load: llama_cpp.Llama(model_path=..., n_ctx=4096, n_gpu_layers=99, n_batch=512)
    Inference: ~12 tok/s on Jetson Orin Nano Super
    Temperature: 0.2 for code gen, 0.7 for chat
    Max tokens: 2048 for code gen, 1024 for chat

  Safety validation: Same model, DIFFERENT conversation context.
    Create new Llama instance for each validation call (prevents context leakage).
    System prompt: safety auditor role (see Prompt 10 Stage 4).

  Intent classification: Phi-3-mini-4K
    Model file: phi-3-mini-4k-instruct-q4.gguf (~2GB)
    Load: llama_cpp.Llama(model_path=..., n_ctx=4096, n_gpu_layers=99)
    Inference: ~40+ tok/s
    Context window: 4K tokens (limitation — keep classification prompts short)

  Model management:
    - Download models from HuggingFace on first run.
    - Verify SHA-256 of downloaded files.
    - Store in /data/models/ (NVMe SSD).
    - VRAM budget tracking: codegen=4GB, classifier=2GB, STT=1GB, TTS=0.5GB. Total=7.5GB of 8GB.
    - If VRAM exhausted: unload least-recently-used model.

SPEECH-TO-TEXT (stt_service.py):
  Model: Whisper-small.en (FP16, ~1GB VRAM)
  Load: faster_whisper.WhisperModel("small.en", device="cuda", compute_type="float16")
  Stream: real-time audio from USB microphone via sounddevice.
  Processing: 3-second sliding window with 1-second overlap.
  Output: transcribed text with confidence score.
  Integration: feed transcribed text into chat_interface as if typed.
  VRAM: ~1GB. Can be unloaded when not actively listening.

TEXT-TO-SPEECH (tts_service.py):
  Engine: Piper TTS (CPU-based, no VRAM)
  Voice: download English voice model (~50MB) from Piper GitHub.
  Use cases: status announcements ("Heading hold engaged", "Trust level increased to 3"), safety alerts ("Kill switch activated").
  Priority queue: safety alerts preempt status announcements.
  Output: PCM audio to USB speaker via sounddevice.

UNIT TESTS:
- LLM load: verify model loads without error, verify VRAM allocation.
- Code generation: known prompt → verify output is valid JSON reflex schema.
- Intent classification: test 20 labeled examples, verify >90% accuracy.
- STT: record known audio, verify transcription accuracy.
- TTS: generate speech from text, verify audio output not empty.
- VRAM tracking: load all models simultaneously, verify VRAM < 8GB. Unload one, verify VRAM freed.
```

**REASONING:** AI models are the cognitive engine of NEXUS. The model stack is designed for the Jetson's 8GB VRAM constraint: codegen (4GB) + classifier (2GB) + STT (1GB) + TTS (0.5GB on CPU) = 7.5GB, leaving 0.5GB headroom. Phi-3-mini was chosen for classification because it's fast (40+ tok/s) and the 4K context window is sufficient for classification prompts (which are short). Whisper-small.en provides real-time transcription at acceptable quality for voice commands. Piper TTS runs on CPU (no VRAM), which is essential given the tight VRAM budget. The model manager ensures that models can be loaded/unloaded dynamically to prevent VRAM exhaustion.

---

### Prompt 12: Cloud Connectivity

**Dependencies:** Prompts 0, 7
**Estimated effort:** 2-3 weeks
**Goal:** Starlink queue-and-forward, fleet management, cloud sync, and remote monitoring.

```
Implement cloud connectivity at jetson/nexus_cognitive/cloud_sync.py.

CONNECTIVITY MODEL:
  Primary: Starlink satellite link (latency 20-600ms, bandwidth 5-50 Mbps down, 2-10 Mbps up).
  Fallback: 4G/5G cellular.
  Offline: all local functionality continues. Queue-and-forward for cloud messages.

QUEUE-AND-FORWARD:
  - Cloud-bound messages stored in SQLite queue: /data/cloud_queue.db
  - Schema: CREATE TABLE outbound (id INTEGER PRIMARY KEY, priority INTEGER, payload TEXT, created_at TIMESTAMP, sent_at TIMESTAMP NULL)
  - Priority: Safety(0) > Command(1) > Telemetry(2) > Analytics(3).
  - Flush: attempt to send when connectivity detected (ping cloud endpoint every 30s).
  - Retry: 3 attempts with 60s timeout. If all fail: retain in queue, retry on next connectivity check.
  - Telemetry batching: aggregate telemetry into 5-minute batches before sending (reduce bandwidth).
  - Compression: zstandard (zstd) level 3 for all payloads > 1KB.

CLOUD API ENDPOINTS (REST):
  POST /api/v1/vessel/{vessel_id}/telemetry — Upload telemetry batch.
  POST /api/v1/vessel/{vessel_id}/safety_event — Upload safety event (URGENT priority).
  POST /api/v1/vessel/{vessel_id}/observation — Upload observation session.
  GET  /api/v1/vessel/{vessel_id}/commands — Poll for pending commands.
  POST /api/v1/vessel/{vessel_id}/reflex_request — Request cloud code generation.
  POST /api/v1/vessel/{vessel_id}/reflex_result — Upload reflex generation result.

FLEET MANAGEMENT:
  - Cloud dashboard shows all vessels: GPS position, heading, speed, trust scores per subsystem, active reflexes, safety status.
  - Alert routing: safety events from any vessel routed to operator via SMS/email.
  - Over-the-air reflex deployment: operator can deploy reflex to any vessel via cloud → Jetson → ESP32 chain.

CLOUD CODE GENERATION (offloaded from Jetson when local model insufficient):
  - Jetson detects when local LLM fails (low confidence, complex request, context > 4K tokens).
  - Send request to cloud: {intent, context, sensor_config, actuator_limits, active_reflexes}.
  - Cloud runs GPT-4o or Claude with full context.
  - Response: generated reflex JSON + safety validation report.
  - Jetson applies same simulation pipeline (Stage 5) before human approval.
  - Typical latency: 5-15 seconds (vs 40+ seconds for local model on complex requests).

UNIT TESTS:
- Queue-and-forward: disconnect network, queue messages, reconnect, verify all sent.
- Priority: queue safety + telemetry + analytics, verify safety sent first.
- Compression: compress 1MB payload, verify size reduction > 3:1.
- Cloud API: mock HTTP server, verify request/response format.
- Offline mode: verify all local functionality (reflex deploy, chat, trust) works without cloud.
```

**REASONING:** Cloud connectivity extends NEXUS beyond the vessel edge. The queue-and-forward design ensures that intermittent Starlink connectivity doesn't cause data loss — everything is persisted locally and synced when connectivity is available. Cloud code generation is used as a fallback for complex requests that exceed the local model's capacity (e.g., generating a complete multi-condition reflex with 10+ states). The local model handles ~70% of requests; cloud handles the remaining 30% that are more complex.

---

## Phase 5: Production

### Prompt 13: Testing & Integration

**Dependencies:** All previous prompts
**Estimated effort:** 4-6 weeks
**Goal:** Comprehensive automated test suite: unit, integration, fuzz, hardware-in-loop, CI.

```
Create comprehensive test suites for the NEXUS platform.

FIRMWARE TESTS (/firmware/tests/, framework: Unity + Ceedling):

  test_cobs.c:
    - Round-trip for sizes: 0, 1, 2, 3, 253, 254, 255, 256, 512, 1024 bytes.
    - Edge: 256 consecutive zeros, all 0xFF, alternating 0x00/0xFF, single 0x00.
    - Invalid: malformed COBS stream, verify graceful rejection.

  test_crc16.c:
    - Known vector: "123456789" → 0x29B1.
    - Empty input → known CRC.
    - Max-length input (1036 bytes) → verify no overflow.

  test_vm.c:
    - Every opcode: push values, execute, verify stack state.
    - Stack overflow (257 pushes): HALT + safe outputs.
    - Stack underflow (POP on empty): HALT.
    - Cycle budget: 10001 NOPs → HALT at 10000.
    - Division by zero → 0.0, no crash.
    - PID: known inputs/outputs → verify against numpy reference.
    - CLAMP: out-of-range → clamped.
    - CALL/RET: nested 16 deep → overflow HALT. 15 deep → success.
    - VM isolation: reflex A variables don't leak to reflex B.

  test_safety.c:
    - Kill switch: simulate GPIO falling edge → verify ISR fires → verify safe outputs.
    - Watchdog: verify kick pattern alternates 0x55/0xAA.
    - Heartbeat: 5 misses → DEGRADED, 10 → SAFE_STATE, 3 good → recovery.
    - Overcurrent: mock fault → verify output disabled.
    - State machine: verify all transitions.

  test_io.c:
    - Pin conflict: same GPIO twice → reject.
    - Digital: set HIGH, read back.
    - PWM: duty verification.
    - ADC: mock readings, verify voltage conversion.
    - I2C: mock bus, verify compass heading.

JETSON TESTS (/jetson/tests/, framework: pytest + pytest-asyncio):

  test_serial_bridge.py:
    - COBS match firmware.
    - Mock serial (pty pair): full protocol exchange.
    - Baud negotiation.

  test_node_manager.py:
    - Discovery simulation.
    - Role assignment flow.
    - Hot-swap detection.

  test_trust_score.py:
    - 50 good: T → 0.095.
    - 2 bad from 0.9: T → 0.812.
    - Level progression simulation.
    - Override → level drop + cooldown.

  test_learning.py:
    - Cross-correlation with synthetic sinusoids.
    - BOCPD with step function.
    - HDBSCAN with 3 behavior types.
    - A/B test accept/reject scenarios.

  test_code_generation.py:
    - Intent classification (20 labeled examples).
    - Safety validation rejection (inject unsafe code).
    - Simulation pass/fail.

FUZZ TESTING:
  - COBS: afl-fuzz or libfuzzer on COBS decode with random bytes.
  - VM: random bytecode generation, verify no crash (HALT expected, no hard fault).
  - JSON parsing: malformed ROLE_ASSIGN payloads, verify graceful rejection.

CI PIPELINE (.github/workflows/):
  ci-firmware.yml: idf.py build → Unity tests → binary size check (< 350KB).
  ci-jetson.yml: pip install → pytest → type check (mypy) → lint (ruff).

HARDWARE-IN-LOOP (manual checklist, with oscilloscope):
  1. Kill switch: CH1=switch, CH2=actuator. Target: < 10ms.
  2. Watchdog: disable kick → verify reset in 1.1s.
  3. Boot timing: serial TX line. Target: OPERATIONAL < 500ms.
  4. Observation: 60s at 100Hz, dump, CRC-32 verify.
  5. Solenoid: activate, measure deactivation at ~5000ms.
  6. COBS stress: 1 million random frames, zero CRC errors.
```

**REASONING:** Testing is placed as the penultimate prompt because it validates everything built so far. The test suite follows the testing pyramid: many unit tests (fast, isolated), fewer integration tests (slower, multi-component), and rare hardware-in-loop tests (slowest, require physical hardware). Fuzz testing on COBS and the VM is critical because both handle untrusted input — COBS from the serial line (which could have EMI corruption) and VM bytecode from AI generation (which could have bugs).

---

### Prompt 14: Web Dashboard

**Dependencies:** Prompts 0, 7, 8
**Estimated effort:** 2-3 weeks
**Goal:** Real-time monitoring dashboard showing node status, telemetry, trust scores, and reflex management.

```
Create a Next.js web dashboard at /dashboard/.

TECH STACK:
  - Next.js 14+ (App Router)
  - TypeScript
  - Tailwind CSS
  - WebSocket for real-time data (socket.io)
  - Recharts for telemetry graphs

PAGES:

1. / (Overview):
   - System status: operational/degraded/safe_state per node (green/yellow/red indicators).
   - Trust score gauges per subsystem (circular progress, color-coded: red < 0.3, yellow < 0.7, green).
   - Autonomy level badges per subsystem (0-5, color intensity increases with level).
   - Active reflexes list with status (running/stopped/error).
   - Recent safety events (last 24h, red badges).
   - Uptime: time since last SAFE_STATE entry.

2. /nodes (Node Management):
   - Table: node MAC, role, status, firmware version, last heartbeat, serial port.
   - Click node → detail view: pin configuration, active reflexes, telemetry history.
   - Actions: assign role, deploy reflex, trigger OTA update.

3. /telemetry (Real-Time Data):
   - Time-series charts: sensor readings over time (configurable time range: 5min, 1hr, 6hr, 24hr).
   - Multi-axis: overlay heading, wind speed, throttle on same chart.
   - Real-time streaming via WebSocket.

4. /reflexes (Reflex Management):
   - List all reflexes across all nodes: name, version, status, tick_rate, cycle_count.
   - Deploy new reflex: upload JSON, preview compiled bytecode, deploy.
   - A/B test status: show active tests with progress bars and statistical results.

5. /autonomy (Trust & Autonomy):
   - Trust score history chart per subsystem.
   - Autonomy level timeline.
   - Override history log.
   - Manual level adjustment controls (with confirmation dialog).

6. /learning (Learning Pipeline):
   - Observation session list with duration and status.
   - Pattern discovery results: correlation matrix heatmap, change-point timeline, behavior cluster visualization.
   - Proposed reflexes: pending approval list with natural-language descriptions and APPROVE/REJECT buttons.

7. /safety (Safety Events):
   - Event log: timestamp, node, event_type, severity, details.
   - Kill switch activation history with timeline.
   - System health metrics: CPU temp, heap usage, heartbeat quality.

BACKEND (Next.js API Routes):
  /api/nodes — GET: list nodes, POST: assign role
  /api/nodes/[id]/reflexes — GET: list reflexes, POST: deploy reflex
  /api/telemetry/[nodeId] — WebSocket: real-time sensor data stream
  /api/autonomy/[subsystem] — GET: trust score, POST: set level
  /api/safety/events — GET: event log
  /api/learning/sessions — GET: session list, POST: start session

Authentication: simple token-based auth for v1. Username/password stored in .env.

UNIT TESTS:
- API routes: verify request/response format.
- WebSocket: verify telemetry stream with mock data.
- Components: React Testing Library for UI components.
```

**REASONING:** The web dashboard is the operator's primary interface for monitoring and managing the NEXUS system. It's placed in Phase 5 because it depends on the Jetson cognitive services being functional. The dashboard does NOT control safety-critical functions — it's read-only for safety events and requires confirmation for any control action. WebSocket streaming provides real-time telemetry without the overhead of HTTP polling.

---

### Prompt 15: Security Hardening

**Dependencies:** Prompts 0, 1, 5, 13
**Estimated effort:** 2-3 weeks
**Goal:** Code signing, secure boot, OTA verification, certificate management.

```
Implement security hardening for production deployment.

FIRMWARE SECURITY:
1. SECURE BOOT (ESP32-S3):
   - Enable ESP32-S3 secure boot v2 (RSA-3072 or ECDSA-P256).
   - Flash encryption: enable AES-256-XTS flash encryption on first boot.
   - Process: burn efuse for secure boot → generate signing key → sign firmware → flash.
   - Key storage: signing private key on build machine ONLY, NEVER on device or in repo.
   - Public key burned into eFuse (irreversible).
   - Anti-rollback: enable flash encryption anti-rollback with version counter.

2. OTA SIGNING:
   - All OTA firmware updates must be signed with the same key as secure boot.
   - Verification: esp_secure_boot_verify_digest() before booting any OTA partition.
   - If verification fails: rollback to factory partition.
   - Key rotation: support 2 signing keys (primary + backup). Burn backup key eFuse as secondary.

3. CODE SIGNING (Jetson Python packages):
   - Sign reflex bytecode with Ed25519 before deployment.
   - ESP32 verifies signature before loading bytecode into VM.
   - Process: Jetson signs with private key → ESP32 verifies with public key (embedded in firmware).
   - Prevents man-in-the-middle reflex injection on serial bus.

NETWORK SECURITY:
4. MQTT TLS:
   - Mosquitto configured with TLS 1.3.
   - Client certificate authentication.
   - Override topics (QoS 2) require mutual TLS.

5. gRPC TLS:
   - All inter-Jetson gRPC calls use TLS with mutual authentication.
   - Certificate rotation every 90 days.

6. SERIAL BUS SECURITY:
   - COBS + CRC-16 provides integrity checking (detects corruption).
   - Code signing (above) provides authentication.
   - No encryption on serial (physical security of RS-422 cable assumed).

KEY MANAGEMENT:
- Root CA: generated once, stored in HSM or password-protected file.
- Device certificates: one per ESP32 and per Jetson, signed by root CA.
- Certificate expiry: 2 years. Auto-renewal via cloud at 90 days before expiry.
- Key ceremony: documented procedure for root CA key generation and backup.

UNIT TESTS:
- Secure boot: sign firmware with valid key → verify boots. Sign with invalid key → verify rejects.
- OTA signing: sign update → verify accepted. Corrupt signature → verify rollback.
- Reflex signing: sign bytecode → ESP32 verifies. Tamper bytecode → ESP32 rejects.
- MQTT TLS: verify connection with valid cert succeeds, invalid cert fails.
```

**REASONING:** Security hardening comes late because it builds on top of the existing OTA and deployment mechanisms. Secure boot and flash encryption are ESP32-S3 hardware features that must be enabled after the firmware is functionally complete (because secure boot locks down the boot process — you can't easily debug a securely booted device). Code signing for reflexes prevents the most dangerous attack vector: an attacker tapping the serial bus and injecting malicious bytecode. Ed25519 was chosen over RSA for reflex signing because it's faster to verify on the MCU (critical for real-time reflex deployment) and produces smaller signatures (64 bytes vs 256 bytes).

---

### Prompt 16: Cross-Domain Equipment Templates

**Dependencies:** Prompts 0, 3
**Estimated effort:** 1-2 weeks
**Goal:** JSON equipment templates for 6 domains, enabling zero-code deployment to new applications.

```
Create equipment templates at /shared/schemas/templates/.

EACH TEMPLATE is a JSON file with:
  {
    "domain": "marine",
    "description": "Marine vessel autopilot and equipment control",
    "version": "1.0",
    "subsystems": {
      "steering": { ... },
      "throttle": { ... },
      "navigation_lights": { ... }
    },
    "safety_rules": [ ... ],
    "default_reflexes": [ ... ]
  }

DOMAIN 1 — MARINE (templates/marine.json):
  Subsystems: steering (compass + rudder PWM), throttle (relay + RPM sensor), bilge (float switch + pump), navigation lights (3x LED), anchor winch (relay + load cell).
  Safety rules: kill switch disables rudder + throttle. Bilge pump cannot be disabled by AI. Anchor winch has 30-second timeout.
  Default reflexes: heading_hold_pid, bilge_auto_pump.

DOMAIN 2 — AGRICULTURE (templates/agriculture.json):
  Subsystems: irrigation (soil moisture + valve), fertigation (EC sensor + dosing pump), greenhouse climate (temp + humidity + vent + heater), harvest (conveyor + optical sorter).
  Safety rules: dosing pump has 5-minute max runtime. Heater auto-off at 40°C. Vent forced open at 45°C.
  Default reflexes: auto_irrigate, climate_control.

DOMAIN 3 — HVAC (templates/hvac.json):
  Subsystems: zone_thermostat (temp sensor + damper + blower), air_quality (CO2 + VOC + fresh_air_damper), predictive_maintenance (vibration + current).
  Safety rules: fresh air damper minimum 20% open. Heater interlock: no heat without airflow.
  Default reflexes: zone_control, air_quality_mgmt.

DOMAIN 4 — FACTORY (templates/factory.json):
  Subsystems: conveyor (motor + speed sensor + emergency_stop), quality_inspection (camera trigger + sorting_actuator), safety_interlocks (light curtain + guard_switch).
  Safety rules: light curtain breaks = immediate stop. Guard switch open = prevent conveyor start.
  Default reflexes: conveyor_speed_control, quality_sort.

DOMAIN 5 — MINING (templates/mining.json):
  Subsystems: ventilation (airflow sensor + fan), pump_control (level_sensor + pump), gas_monitoring (CH4 + CO sensors + alarm).
  Safety rules: CH4 > 1% = alarm. CH4 > 2% = evacuate + shut down equipment. Pump cannot run dry.
  Default reflexes: auto_ventilation, pump_level_control, gas_alarm.

DOMAIN 6 — HOME AUTOMATION (templates/home.json):
  Subsystems: lighting (occupancy + dimmer), security (door_contact + PIR + siren), climate (thermostat + HVAC), energy (CT sensor + battery + solar).
  Safety rules: siren has 10-minute max runtime. Battery charge < 10% = shed non-essential loads.
  Default reflexes: occupancy_lighting, security_armed.

TEMPLATE VALIDATION:
- Each template must validate against the shared JSON schemas (node_role_config, reflex_definition).
- Each template includes at least 2 default reflexes with compilable bytecode.
- Each template lists at least 3 safety rules with measurable thresholds.

UNIT TESTS:
- Schema validation: each template passes JSON schema validation.
- Role assignment: send each template's pin config via ROLE_ASSIGN → verify accepted.
- Default reflexes: compile each template's default reflexes → verify bytecode.
- Safety rules: verify each rule has measurable threshold and defined response.
```

**REASONING:** Equipment templates are the key to NEXUS's cross-domain applicability. Without templates, deploying NEXUS to a new domain requires custom configuration. With templates, an operator selects a domain template, connects the specified hardware, and the system provisions itself. The template format is intentionally JSON (not code) — operators can read and modify templates without programming knowledge. Each template includes default reflexes so the system is useful immediately after hardware connection, even before any learning has occurred.

---

### Prompt 17: Documentation & Release

**Dependencies:** All previous prompts
**Estimated effort:** 1-2 weeks
**Goal:** Final documentation, ADRs, build guide, getting started guide, and release artifacts.

```
Create comprehensive documentation at /docs/.

1. ARCHITECTURE_DECISION_RECORDS.md (28 ADRs):
   Format:
   # ADR-XXX: [Title]
   - Status: Accepted
   - Date: [date]
   - Confidence: VERY HIGH / HIGH / MEDIUM / LOW
   - Category: [Protocol | Safety | VM | AI | Hardware | Learning]
   - Decision: [one-paragraph summary]
   - Context: [why this decision was needed]
   - Options Considered: [table with pros/cons]
   - Rationale: [why chosen option is best]
   - Consequences: [what this means for the system]
   - What Would Change Our Mind: [trigger for reconsideration]

   Include all 28 ADRs from the synthesis report.
   Highlight the 7 MEDIUM/LOW confidence decisions with expanded runner-up analysis:
     ADR-009 (JSON State Machines vs Behavior Trees)
     ADR-012 (gRPC+MQTT vs REST)
     ADR-013 (Qwen2.5-Coder-7B model choice)
     ADR-017 (Inverse RL for pattern discovery)
     ADR-018 (6-level vs 5-level autonomy)
     ADR-023 (LittleFS vs SPIFFS)
     ADR-028 (HDBSCAN vs K-Means)

2. SENIOR_ENGINEER_BUILD_GUIDE.md:
   - Reading order: which spec files to read first, estimated 8-10 hours total.
   - 9 build steps matching prompt sequence 0-8 with exact commands.
   - Test strategy: unit → integration → HIL → CI.
   - Key metrics table: boot time, ISR latency, VM tick time, memory usage, flash usage.
   - Development priorities: critical path highlighted.
   - Debugging: JTAG setup, UART logging, logic analyzer tips.

3. GETTING_STARTED.md:
   - Prerequisites: hardware list (1x ESP32-S3, 1x USB cable, 1x LED), software (ESP-IDF, Python 3.11).
   - 15-minute quickstart:
     1. Clone repo, install dependencies.
     2. Flash firmware to ESP32: idf.py -p /dev/ttyUSB0 flash.
     3. Connect LED to GPIO 4 + GND.
     4. Run Jetson: python -m nexus_cognitive --serial /dev/ttyUSB0.
     5. Chat: "blink the LED every 500ms"
     6. Approve reflex proposal.
     7. LED blinks. System is operational.
   - Next steps: add sensors, deploy autopilot template, start learning.

4. CONTRIBUTING.md:
   - Code style: MISRA-C for firmware, PEP 8 + Ruff for Python.
   - PR process: CI must pass, code review required for safety paths.
   - Issue templates: bug report, feature request, safety incident.

5. RELEASE_CHECKLIST.md:
   - [ ] All unit tests pass (>80% coverage on safety paths).
   - [ ] All integration tests pass.
   - [ ] Hardware-in-loop tests pass (with oscilloscope verification).
   - [ ] Firmware binary size < 350KB (fits in ota partition with margin).
   - [ ] OTA update tested (valid + corrupt + rollback).
   - [ ] Secure boot verified (signed firmware boots, unsigned rejected).
   - [ ] All 6 domain templates validated.
   - [ ] Dashboard loads and shows real-time data.
   - [ ] Documentation reviewed.
   - [ ] Release notes written.
```

**REASONING:** Documentation is last because it captures the system AS BUILT, not as designed. Writing docs before implementation leads to documentation drift — the docs describe what was planned, not what actually exists. The ADRs are particularly important: they capture the reasoning behind every major decision, so future developers can understand WHY the system is built this way and can make informed decisions about changes. The "What Would Change Our Mind" field is the most valuable part — it tells future developers exactly what evidence would justify revisiting a decision, preventing both reckless changes and dogmatic adherence to outdated choices.

---

## Path Analysis: Why This Ordering

### Critical Path
```
Prompt 0 (scaffolding)
  ├─→ Prompt 1 (wire protocol) ──→ Prompt 2 (safety) ──→ Prompt 5 (firmware integration)
  │                                 ──→ Prompt 3 (I/O) ──────↗
  │                                 ──→ Prompt 4 (VM) ───────↗
  └─→ Prompt 6 (serial bridge) ──→ Prompt 7 (cognitive services)
                                     ├─→ Prompt 8 (trust) ──→ Prompt 9 (learning) ──→ Prompt 10 (code gen)
                                     └─→ Prompt 11 (AI models)
                                    Prompt 12 (cloud)
```

### Why NOT Start with the VM?
The VM (Prompt 4) is the most interesting component, but it can't be tested without: (1) the wire protocol to receive REFLEX_DEPLOY messages, (2) the I/O abstraction to populate sensor registers, and (3) the safety system to enforce actuator clamping. Building the VM first would produce beautiful, untestable code. Building the protocol and safety layers first produces the infrastructure that makes the VM immediately testable.

### Why NOT Start with the Chat Interface?
The chat interface (Prompt 7) is the user-facing feature, but it depends on the serial bridge (to communicate with nodes), the reflex orchestrator (to deploy generated reflexes), and the trust score system (to know which reflexes are allowed at which autonomy level). Building chat first would require mocking every other component.

### Why This Ordering Works
1. **Foundation first** (protocol, safety) — these are immutable once tested.
2. **Core engine** (I/O, VM, integration) — these depend on the foundation.
3. **Brain** (serial bridge, cognitive services) — these depend on the core engine.
4. **Intelligence** (learning, code gen, AI models) — these depend on the brain.
5. **Production** (testing, dashboard, security, templates, docs) — these wrap everything.

### Parallel Work Opportunities (3 Developers)

| Developer A (Firmware) | Developer B (Jetson Core) | Developer C (ML/Cloud) |
|---|---|---|
| Prompts 0-5 | Prompts 0, 6-7 | Prompts 0, 7 (partial), 11-12 |
| Serial protocol, safety, I/O, VM, integration | Serial bridge, gRPC, MQTT, node manager, chat | AI models, cloud sync |
| Weeks 1-5 | Weeks 1-4 | Weeks 3-6 |
| Prompts 13, 15 | Prompts 8, 9 | Prompt 10 |
| Testing, security hardening | Trust, learning, A/B testing | Code generation pipeline |
| Weeks 6-9 | Weeks 5-9 | Weeks 5-8 |
| Prompt 16 | Prompt 14 | Prompt 17 |
| Templates | Dashboard | Documentation |
| Week 10 | Weeks 7-9 | Weeks 9-10 |

**Estimated total with 3 developers: 10-12 weeks.**

### Risk Mitigation Through Ordering
- **Safety bugs caught early**: kill switch ISR (Prompt 2) is built and tested before any actuator code runs.
- **Protocol mismatches caught early**: both firmware and Jetson COBS implementations (Prompts 1 and 6) are tested against the same spec.
- **VM safety validated early**: cycle budget and actuator clamping (Prompt 4) are tested before any AI-generated reflexes are deployed.
- **Trust system prevents premature autonomy**: trust scores (Prompt 8) start at 0.0, ensuring the system cannot operate autonomously until sufficient evidence accumulated.

### Effort Summary

| Phase | Prompts | Calendar Time (serial) | Calendar Time (parallel) |
|-------|---------|----------------------|------------------------|
| Foundation | M, 0, 1, 2 | 3-4 weeks | 3-4 weeks |
| Core Engine | 3, 4, 5 | 5-6 weeks | 5-6 weeks |
| Cognitive Brain | 6, 7, 8, 9 | 8-10 weeks | 6-8 weeks |
| Intelligence | 10, 11, 12 | 6-8 weeks | 4-6 weeks |
| Production | 13, 14, 15, 16, 17 | 8-10 weeks | 6-8 weeks |
| **TOTAL** | **M, 0-17** | **30-38 weeks** | **10-12 weeks** |

---

*End of Master Build Prompt Series. Begin with Prompt M, execute in order, and build the future of post-coding robotics.*
