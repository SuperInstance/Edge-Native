# NEXUS Platform — Senior Engineer Build Guide

## For: Production Implementation of the Post-Coding Distributed Intelligence Platform

---

## 1. Reading Order

Read these files in this order. Each builds on the previous. Estimated total reading time: 8-10 hours.

### Phase 1: Architecture Foundation (2 hours)
1. **`ARCHITECTURE_DECISION_RECORDS.md`** — Read FIRST. Every decision has a confidence level. Focus on MEDIUM and LOW confidence decisions first — these are the ones most likely to need your input.
2. **`safety/safety_system_spec.md`** — Read SECOND. Safety is non-negotiable. Understand the four-tier architecture, kill switch wiring, watchdog behavior, and boot sequence timing before writing any code.

### Phase 2: Wire Protocol and Firmware Core (3 hours)
3. **`protocol/wire_protocol_spec.md`** — The complete wire protocol. Pay attention to the COBS encoding algorithm (Appendix A) and binary payload formats. Implement the encoder/decoder first — everything depends on it.
4. **`protocol/message_payloads.json`** — JSON Schema for every message type. Use this to generate Python validation code on the Jetson side.
5. **`firmware/reflex_bytecode_vm_spec.md`** — The bytecode VM specification. This is the heart of the system. Read every opcode definition, the memory model, and the timing analysis. You will implement this in C.

### Phase 3: Hardware and I/O (2 hours)
6. **`firmware/memory_map_and_partitions.md`** — Memory layout and flash partition table. Copy the partition_table.csv to your ESP-IDF project directly.
7. **`firmware/io_driver_interface.h`** — The C interface contract. Your firmware code must conform to every type and function signature defined here.
8. **`firmware/io_driver_registry.json`** — Driver catalog with exact register sequences. Use this to implement each driver.

### Phase 4: Jetson Cognitive Layer (2 hours)
9. **`jetson/cluster_api.proto`** — gRPC service definitions. Generate Python stubs from this. All inter-Jetson communication goes through these services.
10. **`jetson/module_interface.py`** — Jetson module ABC. All Jetson modules (learning, chat, vision, monitoring) must subclass this.
11. **`jetson/mqtt_topics.json`** — MQTT topic hierarchy and QoS settings. Configure your broker exactly as specified.

### Phase 5: Safety and Autonomy (1.5 hours)
12. **`safety/safety_policy.json`** — Machine-readable safety rules. Your validation pipeline must programmatically check generated code against these rules.
13. **`safety/trust_score_algorithm_spec.md`** — The trust score formula, parameters, and simulation results. Implement this as a Python module with the exact parameters specified.

### Phase 6: Portability (0.5 hours)
14. **`ports/hardware_compatibility_matrix.json`** — MCU compatibility matrix. Reference this if you need to port to a different MCU family.

---

## 2. Build Steps

### Step 1: Create ESP-IDF Project

```bash
# Requires ESP-IDF v5.2+
idf.py create-project nexus_limb
cd nexus_limb
idf.py set-target esp32s3
```

Copy the partition table from `memory_map_and_partitions.md` into `partitions.csv`.

Required `sdkconfig` overrides:
```
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
```

### Step 2: Implement Wire Protocol Layer

Files to create:
- `main/components/nexus_protocol/cobs.c/h` — COBS encode/decode (reference pseudocode in wire_protocol_spec.md Appendix A)
- `main/components/nexus_protocol/crc16.c/h` — CRC-16/CCITT-FALSE
- `main/components/nexus_protocol/framing.c/h` — Frame TX/RX with ring buffers
- `main/components/nexus_protocol/msg_handler.c/h` — Message dispatch table (28 message types)

Build this first and test with a loopback test (TX connected to RX) verifying every message type encodes and decodes correctly.

### Step 3: Implement I/O Abstraction Layer

Files to create:
- `main/components/nexus_io/io_abstraction.c/h` — Pin configuration parser and validator
- `main/components/nexus_io/pin_config.c/h` — Pin capability database and allocation
- `main/drivers/` — One file per driver (hmc5883l.c, mpu6050.c, bme280.c, etc.)

Follow the driver vtable interface in `io_driver_interface.h` exactly. Every driver must implement all 7 functions in the vtable struct.

### Step 4: Implement Reflex Bytecode VM

Files to create:
- `main/components/nexus_vm/vm.c/h` — VM execution engine (fetch-decode-execute loop)
- `main/components/nexus_vm/opcodes.c/h` — Opcode implementations (32 opcodes)
- `main/components/nexus_vm/compiler.c/h` — JSON-to-bytecode compiler
- `main/components/nexus_vm/safety.c/h` — VM safety invariants (stack bounds, cycle budget, actuator clamping)

This is the most complex component. Implement the safety checks FIRST, then the execution engine. Test by creating a simple counter reflex (increment variable every tick) and verifying cycle timing with a GPIO toggle.

### Step 5: Implement Safety Monitor

Files to create:
- `main/components/nexus_safety/kill_switch.c/h` — GPIO ISR for NC kill switch
- `main/components/nexus_safety/watchdog.c/h` — Software watchdog (feeds external MAX6818)
- `main/components/nexus_safety/heartbeat.c/h` — Jetson heartbeat monitoring
- `main/components/nexus_safety/overcurrent.c/h` — INA219-based current monitoring

Wire a physical NC button to the kill-switch GPIO and verify:
1. Pressing button sets all outputs to safe state within 100us (measure with oscilloscope)
2. Holding button for 1s triggers full system reset
3. Releasing button allows normal operation after selftest

### Step 6: Integrate into Main Application

File: `main/main.c`
- Init sequence exactly as specified in safety_system_spec.md Section 7
- All outputs LOW at T+0ms
- Watchdog start at T+5ms
- Serial init at T+10ms
- Identity send at T+20ms
- Role config at T+50ms (or load cached from NVS)
- Selftest at T+300ms
- Normal operation at T+500ms

### Step 7: Create Jetson Python Package

```bash
mkdir -p nexus_cognitive && cd nexus_cognitive
# Generate gRPC stubs
python -m grpc_tools.protoc -I. --python_out=. ../nexus_specs/jetson/cluster_api.proto
```

Create package structure:
```
nexus_cognitive/
├── __init__.py
├── nexus_module.py          # Copy from module_interface.py
├── node_manager.py          # Implements NodeDiscovery + NodeManager gRPC services
├── reflex_orchestrator.py  # Implements ReflexOrchestrator gRPC service
├── learning_pipeline.py     # Pattern discovery, narration processing
├── safety_manager.py        # Safety event handling, trust score
├── chat_interface.py        # Chat bot with LLM integration
├── mqtt_bridge.py           # MQTT pub/sub
├── serial_bridge.py         # Serial port management for all ESP32 connections
└── tests/
    ├── test_wire_protocol.py
    ├── test_vm_execution.py
    └── test_trust_score.py
```

### Step 8: Configure MQTT Broker

Install EMQX or Mosquitto. Configure topics per `mqtt_topics.json`. Set the override topic (`autonomy/*/override`) to QoS 2 with retained messages.

### Step 9: End-to-End Integration Test

1. Flash ESP32 with universal firmware
2. Connect ESP32 to Jetson via USB-RS422 adapter
3. Verify device identity exchange
4. Assign a simple role (LED blinker) via chat interface
5. Verify auto-detection and selftest
6. Deploy a reflex (LED blinking pattern)
7. Test observation recording and dump
8. Test heartbeat timeout and failsafe behavior
9. Test kill switch
10. Test OTA firmware update

---

## 3. Test Strategy

### Unit Tests (run on every commit)
- Wire protocol: encode/decode round-trip for every message type, CRC validation, COBS edge cases
- VM: every opcode execution, stack overflow/underflow detection, cycle budget enforcement, division-by-zero
- I/O: pin conflict detection, capability validation, driver initialization
- Trust score: simulation against all 5 reference scenarios, parameter boundary values
- JSON schemas: validate all example payloads against schemas

### Integration Tests (run nightly)
- ESP32 ↔ Jetson serial communication (loopback with USB-RS422 adapter)
- Node discovery and role assignment flow
- Reflex deployment → execution → observation → dump → analysis pipeline
- Heartbeat timeout → degraded → safe-state escalation
- OTA firmware update with rollback on self-test failure

### Hardware-in-Loop Tests (run before each release)
- Kill switch response time (oscilloscope measurement, must be <100ms)
- Watchdog reset timing (must reset within 1.1s of feed failure)
- Observation buffer dump integrity (CRC-32 verification)
- Full boot sequence timing (oscilloscope on serial TX line)
- Solenoid timeout enforcement (measure actual off-time with current probe)
- Relay flyback diode protection verification (test with inductive load)

### Safety Tests (run before ANY production deployment)
- All actuators at safe state on boot
- Kill switch overrides ALL software states
- Watchdog resets within 1.1s of feed failure
- Heartbeat loss triggers safe-state within 1.0s
- No single sensor failure causes uncontrolled actuation
- Rate limiting enforced on all actuators
- OTA rollback works when self-test fails
- Full boot sequence completes within 500ms

---

## 4. Key Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Boot to operational | < 500ms | Oscilloscope on serial TX |
| Kill switch response | < 100ms | Oscilloscope on actuator output |
| Watchdog reset | < 1.1s | Timer between last feed and RST assertion |
| Reflex cycle time (typical PID) | < 100us | GPIO toggle + timer measurement |
| Reflex cycle time (worst case) | < 500us | Cycle counter in VM |
| Serial throughput | > 70 KB/s | Time to dump 1MB observation data |
| Observation buffer capacity | 31 minutes at 100Hz | Frame counter at buffer full |
| COBS decode overhead | < 5% CPU at 921600 baud | CPU utilization monitor |
| Trust score computation | < 10ms per evaluation | Python profiler |
| MQTT message latency (override) | < 200ms | End-to-end timestamp comparison |

---

## 5. Development Priorities

### Critical Path (build these first)
1. Wire protocol COBS encoder/decoder
2. Kill switch ISR and hardware relay control
3. VM safety invariants
4. Boot sequence (all outputs safe until selftest passes)
5. Heartbeat monitoring and failsafe

### High Priority (core functionality)
6. Reflex VM execution engine (all 32 opcodes)
7. JSON-to-bytecode compiler
8. I/O abstraction with at least 5 drivers (digital, PWM, ADC, I2C compass, UART)
9. Observation buffer recording and dump
10. Role assignment protocol

### Medium Priority (intelligence features)
11. Jetson serial bridge and node manager
12. Chat interface with LLM integration
13. MQTT telemetry bridge
14. Trust score computation and autonomy state management

### Lower Priority (advanced features)
15. Pattern discovery engine
16. A/B testing framework
17. Cloud code generation pipeline
18. Cross-domain equipment templates
19. Local LLM code generation
20. Multi-Jetson clustering

---

## 6. Known Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VM bytecode has a bug that causes incorrect actuator output | Medium | Critical | Extensive unit tests for every opcode, formal cycle-count verification, actuator clamping as final safety net |
| COBS implementation has edge case with 256 consecutive zero bytes | Low | Medium | Test with fuzzing (random binary payloads), reference C implementation in spec appendix |
| Observation buffer corrupts during power loss | Low | Medium | LittleFS journaling protects reflex files; observation buffer in PSRAM is volatile-by-design (acceptable loss) |
| Cloud LLM generates unsafe code that passes validation | Medium | Critical | Separate LLM for validation, MISRA-C rules, simulation against recorded data, human approval gate |
| Trust score parameters poorly tuned for real operations | Medium | Medium | Configurable per-subsystem; start conservative (alpha_gain=0.001) and increase based on field data |
| Jetson thermal throttling under load | Medium | Medium | Monitor Jetson temperature, reduce LLM concurrency, shed non-critical services at 85C |
| Starlink latency causes timeout on cloud code generation | Medium | Low | 60-second timeout with automatic retry, queue-and-forward, local model handles 70% of requests |

---

## 7. File Dependency Graph

```
io_driver_interface.h          (no dependencies - implement first)
  ↓
io_driver_registry.json        (references io_driver_interface.h types)
  ↓
wire_protocol_spec.md           (references io_driver_registry.json driver names)
message_payloads.json          (references wire_protocol_spec.md message types)
  ↓
reflex_bytecode_vm_spec.md     (references wire protocol for deployment commands)
  ↓
memory_map_and_partitions.md   (hardware-specific, no code dependencies)
  ↓
cluster_api.proto              (references all message payload schemas)
module_interface.py            (independent Python ABC)
  ↓
safety_policy.json              (references all message types for safety events)
trust_score_algorithm_spec.md (independent math specification)
safety_system_spec.md          (references memory map for timing)
mqtt_topics.json               (references all telemetry formats)
hardware_compatibility_matrix.json (references minimum specs from all specs)
  ↓
ARCHITECTURE_DECISION_RECORDS.md (references all of the above)
```

The dependency graph shows that `io_driver_interface.h` is the foundation. Implement it first and verify the interface compiles on your target MCU. Then build upward from there.
