# Integration Test Plan — Component and System-Level Verification

**Document ID:** NEXUS-ITP-001
**Version:** 1.0
**Date:** 2025-07-12
**Status:** Draft
**Classification:** Internal — Engineering Team

---

## Test Strategy Overview

The NEXUS platform verification strategy employs three progressive levels of testing, each increasing in scope and decreasing in execution frequency:

| Level | Scope | Responsible Party | Execution Frequency |
|---|---|---|---|
| **Unit Tests** | Individual functions, classes, modules | Component owner (each engineer) | Every commit (CI gate) |
| **Integration Tests** | Cross-component interactions, protocol boundaries | Integration engineer + component owners | Nightly (automated CI/CD) |
| **System Tests** | End-to-end scenarios on real hardware | QA / systems engineer | Weekly + release gate |

**This document covers Integration Tests (Sections 1–6) and System Tests (Section 7).** Unit tests remain the responsibility of each component team and are not enumerated here, though pass/fail results from unit test suites feed into the integration test entrance criteria. All integration tests assume unit tests pass on both the Jetson and ESP32 sides before execution begins.

**Entrance Criteria for Integration Testing:**
- All unit tests pass on both ESP32 firmware and Jetson software (green CI).
- Wire protocol implementation compiles and passes unit-level COBS/CRC/frame tests.
- Bytecode VM passes unit-level opcode execution tests.
- Jetson serial bridge can establish a single connection to one ESP32 node.

**Exit Criteria for Release:**
- 100% of integration tests pass (no conditional waivers without sign-off).
- 24-hour soak test completes with zero safety events.
- All fault injection scenarios produce correct safe-state responses.
- Performance benchmarks meet or exceed thresholds defined in each test below.

---

## 1. Wire Protocol Integration Tests

These tests verify the serial communication layer between the Jetson and ESP32, encompassing COBS framing, CRC integrity, baud-rate negotiation, and hardware flow control. All tests run on physical hardware (not simulated UARTs) unless otherwise noted.

### 1.1 COBS Round-Trip Test

**Purpose:** Confirm that Consistent Overhead Byte Stuffing encoding and decoding produce byte-transparent, lossless transport over the full payload size range.

**Procedure:**
1. On the Jetson test harness, generate 10,000 random binary payloads with uniformly distributed lengths between 1 and 1,024 bytes. Each payload may contain any byte value including 0x00, 0xFF, and sequences that produce worst-case COBS expansion.
2. COBS-encode each payload and wrap it in a wire-protocol frame (header, payload, CRC-16).
3. Transmit each frame over the physical UART link at the currently negotiated baud rate.
4. On the ESP32 side, receive the raw bytes, COBS-decode, and extract the payload.
5. Echo the payload back to the Jetson (or return it in a TELEMETRY_ACK message).
6. Compare the received payload byte-for-byte against the original.
7. Track and log: mismatches, frame drops (detected via sequence number gaps), and timeouts.

**Metrics:**
| Metric | Threshold |
|---|---|
| Payload mismatches | 0 |
| Frame drops (sequence gaps) | 0 |
| Receive timeouts | 0 |
| Max COBS-encoded frame size | ≤ payload + ⌈payload/254⌉ + 3 (header/CRC) |

**Test Duration:** Approximately 5–15 minutes at 921,600 baud (depending on average payload size).

### 1.2 CRC-16 Coverage Test

**Purpose:** Verify that the CRC-16/CCITT-FALSE checksum detects every single-bit corruption in all frame regions (header, payload, and CRC field itself).

**Procedure:**
1. Construct a valid wire-protocol frame of 256 bytes (typical mid-range payload).
2. For each bit position in the frame (header bytes 0–3, payload bytes 4–259, CRC bytes 260–261), flip that single bit to create a corrupted variant.
3. Send each corrupted frame to the receiver.
4. Verify that the receiver rejects the frame and reports a CRC mismatch error.
5. Additionally, send the original uncorrupted frame interspersed every 50 corrupted frames to confirm the receiver does not false-reject valid frames.
6. Repeat with a 1,024-byte payload to verify coverage at maximum size.

**Metrics:**
| Metric | Threshold |
|---|---|
| Corrupted frames rejected | 100% (all 2,064 single-bit flips per size) |
| Valid frames accepted (false rejects) | 0 |
| Correct error code reported | CRC_MISMATCH (0x0003) |

### 1.3 Baud Rate Stress Test

**Purpose:** Validate link reliability at the maximum negotiated baud rate (921,600) under sustained full-throughput conditions for an extended duration.

**Procedure:**
1. Negotiate 921,600 baud during the handshake phase (BAUD_NEGOTIATE message sequence).
2. Start a continuous transmit loop on the Jetson: generate frames back-to-back with maximum-size payloads (1,024 bytes) at the highest rate the UART driver allows.
3. Run for exactly 1 hour of wall-clock time.
4. On the ESP32 side, receive and validate every frame: check CRC, check sequence number continuity, log any gaps.
5. Monitor UART hardware registers for overrun errors, framing errors, and parity errors (if applicable).
6. Log CPU utilization on both sides to confirm neither is saturated.

**Metrics:**
| Metric | Threshold |
|---|---|
| CRC errors | 0 |
| Sequence number gaps | 0 |
| Frame drops (detected or inferred) | 0 |
| UART overrun/framing errors | 0 |
| Jetson CPU utilization during test | < 70% |
| ESP32 CPU utilization during test | < 80% |
| Effective throughput | ≥ 80% of theoretical 921,600 baud |

**Test Duration:** 1 hour.

### 1.4 Flow Control Test

**Purpose:** Verify that hardware flow control (CTS/RTS) prevents data loss when the Jetson receive buffer approaches capacity.

**Procedure:**
1. Configure the serial port with RTS/CTS hardware flow control enabled.
2. On the Jetson side, artificially delay reading from the UART receive buffer (e.g., by pausing the read loop in the test harness).
3. Allow the ESP32 to transmit at maximum rate until the Jetson RX buffer reaches 75% capacity (monitor via OS-level serial buffer statistics).
4. Verify that CTS is deasserted by the Jetson at this threshold, causing the ESP32 to stop transmitting.
5. Confirm that no UART overrun errors occur during the backpressure period (data is held in the ESP32 TX buffer, not dropped).
6. Resume reading from the Jetson buffer, draining it below 25% capacity.
7. Verify CTS is reasserted, ESP32 resumes transmission, and all data is received intact.
8. Perform sequence-number audit: every frame sent must be accounted for in order.

**Metrics:**
| Metric | Threshold |
|---|---|
| Bytes lost during backpressure | 0 |
| UART overrun errors | 0 |
| Time from buffer full to CTS deassert | < 100 ms |
| Time from buffer drain to CTS reassert | < 100 ms |
| All frames received in order | Yes |

---

## 2. VM Integration Tests

These tests verify the Reflex Bytecode VM's integration with the compiler, deployment pipeline, telemetry feedback, and safety subsystem. They exercise the full path from JSON reflex definition to executing bytecode on the ESP32 and reading back results.

### 2.1 Reflex Deploy-Execute-Verify Cycle

**Purpose:** Validate the complete lifecycle of a reflex: definition → compilation → bytecode validation → deployment → execution → telemetry verification, using a real PID control algorithm as the reference payload.

**Procedure:**
1. **Generate reflex JSON** on the Jetson. The test uses a heading-hold PID controller with the following parameters: setpoint = 45.0°, Kp = 1.0, Ki = 0.05, Kd = 0.3, input = IMU yaw reading, output = rudder servo PWM. The JSON must conform to the reflex_definition.json schema.
2. **Compile JSON to bytecode** using the Jetson-side compiler. The compiler translates high-level operations (ADD, SUB, MUL for PID math) into the 32-opcode bytecode format, emitting 8-byte packed instructions.
3. **Validate bytecode** against all safety invariants defined in the VM specification: maximum instruction count per reflex (enforced by compiler), no forbidden opcodes (e.g., no HALT outside designated slots), memory access bounds checked, cycle budget field set correctly.
4. **Deploy via REFLEX_DEPLOY message** over the serial link. The Jetson sends the compiled bytecode to the ESP32, which loads it into the VM's reflex slot.
5. **Execute 1,000 VM ticks** on the ESP32 at 1 kHz (1 second of simulated runtime). Feed synthetic IMU yaw data that ramps from 0° to 90° to exercise the full PID response curve.
6. **Read back actuator outputs** via the TELEMETRY message stream. Each tick's rudder servo PWM value is captured.
7. **Compare to reference simulation.** Run an identical PID calculation in Python on the Jetson using the same input sequence and identical floating-point parameters (float32 precision).
8. **Compute per-tick error:** |ESP32_output − Python_output|. Verify that all errors are within float32 epsilon (≤ 1.0e-6 relative, or ≤ 1 ULP for the float32 representation).

**Metrics:**
| Metric | Threshold |
|---|---|
| Bytecode compiles without errors | Yes |
| All safety invariants pass | Yes |
| Reflex deployed successfully (ACK received) | Yes |
| VM completes 1,000 ticks without HALT | Yes |
| Max output deviation from Python reference | ≤ float32 epsilon |
| Tick-to-tick telemetry sequence continuity | No gaps |

### 2.2 Multi-Reflex Priority Test

**Purpose:** Verify that the reflex scheduler correctly arbitrates between multiple active reflexes based on assigned priority levels.

**Procedure:**
1. Deploy three reflexes to the ESP32:
   - Reflex "rudder_pid" at priority 10 (highest)
   - Reflex "throttle_limit" at priority 5 (medium)
   - Reflex "bilge_check" at priority 1 (lowest)
2. Configure input conditions so that all three reflexes trigger simultaneously on the same VM tick (e.g., rudder needs correction, throttle exceeds limit, bilge sensor active).
3. Run 500 ticks and collect the actuator output log.
4. Verify that when multiple reflexes write to the same output channel, the highest-priority reflex's value is applied.
5. Verify that reflexes writing to different output channels all execute (no starvation of lower-priority reflexes on non-conflicting outputs).
6. Swap priorities mid-test (reassign "bilge_check" to priority 15) and verify the scheduler immediately reflects the new ordering.

**Metrics:**
| Metric | Threshold |
|---|---|
| Correct priority arbitration (conflicting outputs) | 100% of ticks |
| Non-conflicting outputs all executed | Yes |
| Priority swap takes effect within | 1 tick |

### 2.3 Reflex Hot-Swap Test

**Purpose:** Verify that a reflex can be replaced at runtime without interrupting the VM tick cycle or losing actuator state.

**Procedure:**
1. Deploy reflex A (e.g., a simple proportional controller) and execute 100 ticks.
2. Without pausing the VM, deploy reflex B with the same name but different behavior (e.g., replace proportional with PID).
3. The deployment sequence: Jetson sends REFLEX_DEPLOY → ESP32 ACKs → ESP32 atomically swaps the reflex slot → VM continues on the next tick with reflex B loaded.
4. Execute 100 more ticks.
5. Verify that ticks 101–200 produce outputs consistent with reflex B's algorithm, not reflex A's.
6. Verify that no ticks were dropped or skipped during the swap (tick counter is continuous from 1 to 200).
7. Verify that actuator outputs did not glitch to zero or safe-state during the swap (seamless transition).

**Metrics:**
| Metric | Threshold |
|---|---|
| Tick counter continuous (no gaps) | Yes |
| Post-swap outputs match reflex B algorithm | Yes |
| No actuator glitch during swap | Yes |
| Swap latency (ticks affected) | ≤ 1 tick |

### 2.4 VM Safety Halt Recovery Test

**Purpose:** Verify that the VM's safety mechanisms correctly halt execution when a reflex exceeds its cycle budget, place actuators in safe-state, and allow clean recovery after deploying a fixed reflex.

**Procedure:**
1. Deploy a reflex that includes a deliberate infinite-loop pattern (e.g., a conditional jump that never terminates) designed to exceed the per-tick cycle budget of 50,000 instructions after approximately 5,000 ticks of gradual accumulation.
2. Execute the VM. At the point of budget exhaustion, the VM must assert the SAFETY_HALT condition.
3. Verify upon HALT:
   - All actuator outputs are driven to their configured safe-state values (servos to center, motors to neutral, solenoids off).
   - A SAFETY_HALT event message is transmitted to the Jetson.
   - The VM enters an idle loop and refuses to execute any reflex until explicitly cleared.
4. On the Jetson side, deploy a corrected reflex (same name, bounded loop).
5. Send a VM_RESET or CLEAR_HALT command.
6. Verify the VM resumes execution with the new reflex.
7. Execute 100 ticks of the corrected reflex and verify normal outputs.

**Metrics:**
| Metric | Threshold |
|---|---|
| Halt triggered at budget exhaustion | Yes |
| All actuators at safe-state post-halt | Yes |
| SAFETY_HALT message received by Jetson | Within 10 ms |
| VM refuses execution until cleared | Yes |
| Clean resume after reset | Yes |
| Corrected reflex produces valid output | Yes |

---

## 3. Boot Sequence Integration Tests

These tests validate the power-on and restart procedures for both the ESP32 and Jetson, including identity exchange, role assignment, reflex loading, and timing guarantees.

### 3.1 Cold Boot Timing Test

**Purpose:** Measure and verify the end-to-end cold boot time from simultaneous power-on to the system entering operational state (first TELEMETRY message received).

**Procedure:**
1. Power cycle both the ESP32 and Jetson simultaneously using a controlled power switch (or relay).
2. Start a high-resolution timer on power-on.
3. On the ESP32 side, the firmware executes its boot sequence: hardware init → UART init → send DEVICE_IDENTITY message.
4. On the Jetson side, the OS boots → NEXUS services start → serial bridge opens → receives DEVICE_IDENTITY → sends ROLE_ASSIGN → waits for REFLEX_DEPLOY_ACK.
5. Record the timestamp when the first TELEMETRY message arrives from the ESP32 after role assignment and reflex loading are complete.
6. Repeat 5 times and compute mean, min, and max boot times.

**Metrics:**
| Metric | Threshold |
|---|---|
| Mean cold boot time | < 5 seconds |
| Max cold boot time (5 runs) | < 8 seconds |
| DEVICE_IDENTITY sent within (ESP32 side) | < 500 ms |
| ROLE_ASSIGN received within | < 2 seconds |

### 3.2 Warm Boot Test (ESP32 Restart Only)

**Purpose:** Verify that an ESP32 node can restart and reconnect to an already-running Jetson without requiring a full Jetson restart.

**Procedure:**
1. Start the system normally (both powered on, operational).
2. Trigger an ESP32 software restart via the watchdog or a dedicated RESTART command from the Jetson.
3. The Jetson must detect the serial line reset (UART break condition) and enter the reconnection state machine.
4. The ESP32 reboots, reinitializes hardware, and sends DEVICE_IDENTITY.
5. The Jetson receives DEVICE_IDENTITY, matches it to the known node (by serial number), and re-sends ROLE_ASSIGN within 1 second.
6. The ESP32 loads cached reflexes from LittleFS (the last successfully deployed bytecode) and begins executing.
7. Verify that TELEMETRY resumes within 2 seconds of the restart trigger.

**Metrics:**
| Metric | Threshold |
|---|---|
| DEVICE_IDENTITY received after restart | < 1 second |
| ROLE_ASSIGN sent after DEVICE_IDENTITY | < 1 second |
| Cached reflexes loaded from LittleFS | Yes |
| TELEMETRY resumes within | < 2 seconds total |
| No actuator glitch during restart | Yes (hold last output) |

### 3.3 Role Reassignment Test

**Purpose:** Verify that a node's role can be changed at runtime, causing old reflexes to be unloaded and new role-appropriate reflexes to be deployed.

**Procedure:**
1. Assign role "autopilot" to the node. Deploy the associated reflex set (rudder_pid, throttle_pid, waypoint_nav).
2. Execute 100 ticks to confirm normal operation.
3. From the Jetson, send a ROLE_ASSIGN message with new role "bilge_monitor".
4. Verify the ESP32:
   - Unloads all "autopilot" reflexes (VM slots cleared).
   - Loads "bilge_monitor" reflexes (bilge_pump_ctrl, water_level_check).
   - Actuator outputs transition to the new role's safe defaults (no rudder output, pump off).
5. Execute 100 ticks in the new role and verify correct behavior.
6. Verify no stuck actuators: rudder servo returns to center, no orphaned PWM outputs.

**Metrics:**
| Metric | Threshold |
|---|---|
| Old reflexes unloaded on role change | Yes |
| New reflexes deployed and loaded | Yes |
| Role transition completes within | < 500 ms |
| No stuck actuators after transition | Yes |
| New role produces correct outputs | Yes |

---

## 4. Observation Pipeline Integration Tests

These tests verify the high-frequency data recording subsystem that captures sensor readings into the ESP32's PSRAM buffer for later retrieval and analysis.

### 4.1 Record-Transfer-Verify Cycle

**Purpose:** Validate the complete observation lifecycle: start recording, capture samples at high frequency, stop recording, transfer data to the Jetson, and verify integrity.

**Procedure:**
1. Send OBS_RECORD_START to the ESP32 with configuration: 100 Hz sample rate, sensor channels = IMU (accel + gyro), duration target = 60 seconds.
2. The ESP32 begins capturing sensor data into the PSRAM ring buffer at 100 Hz (expect 6,000 samples).
3. After 60 seconds, send OBS_RECORD_STOP. The ESP32 finalizes the recording.
4. Request data transfer via OBS_DUMP_CHUNK messages. The Jetson requests sequential chunks (e.g., 1,024 bytes each) until all data is received.
5. Reconstruct the complete dataset on the Jetson and compute a CRC-32 over the entire byte stream.
6. Compare the Jetson-computed CRC-32 against the CRC-32 reported by the ESP32 in the recording metadata.
7. If an independent sensor log is available (e.g., from a separate data logger on the same bus), cross-validate a statistical sample of readings.
8. Verify the sample count matches the expected 6,000 (±1 for timing jitter).

**Metrics:**
| Metric | Threshold |
|---|---|
| CRC-32 match (Jetson vs ESP32) | Exact match |
| Sample count | 5,998–6,002 (allowing ±0.03% jitter) |
| Transfer completes without errors | Yes |
| No corrupted chunks | 0 |
| Cross-validation with independent log (if available) | Within sensor noise tolerance |

### 4.2 Observation Buffer Overflow Test

**Purpose:** Verify graceful handling when the PSRAM observation buffer fills to capacity.

**Procedure:**
1. Start observation at 100 Hz with maximum sensor channel width (all sensors active, ~350 bytes/sample).
2. Run continuously until the 8 MB PSRAM buffer fills (approximately 4.6 minutes at this data rate).
3. Verify the ESP32's behavior:
   - Recording auto-stops when buffer is full (no wrap-around corruption).
   - An OBS_RECORD_STOP event message is sent to the Jetson indicating "buffer full" as the reason.
   - All data captured up to the buffer-full point is preserved and retrievable.
4. Dump the full buffer and verify CRC-32 integrity of the complete dataset.

**Metrics:**
| Metric | Threshold |
|---|---|
| Auto-stop triggered at buffer full | Yes |
| OBS_RECORD_STOP sent with reason = "buffer_full" | Yes |
| No data corruption in filled buffer | CRC-32 match |
| Time to fill (approximate) | ~4.6 minutes |

### 4.3 Observation During Reflex Execution

**Purpose:** Verify that high-frequency observation recording does not interfere with reflex VM execution timing.

**Procedure:**
1. Deploy a reflex that runs at 1 kHz with a tight cycle budget (near the 1 ms tick boundary).
2. Start observation at 100 Hz simultaneously.
3. Run for 10 seconds (10,000 reflex ticks, 1,000 observation samples).
4. Monitor:
   - Reflex tick timing: measure the interval between consecutive ticks using a hardware timer or GPIO toggle + oscilloscope.
   - Observation sample timestamps: verify 100 Hz ±2% jitter.
   - VM cycle count per tick: verify no reflex exceeds the 50,000-instruction budget.
5. Verify that observation data is valid (non-zero, monotonically increasing timestamps, plausible sensor values).

**Metrics:**
| Metric | Threshold |
|---|---|
| Reflex tick interval deviation | < 5% from 1 ms nominal |
| Reflex budget overruns | 0 |
| Observation sample rate | 98–102 Hz |
| Observation data validity | 100% of samples plausible |
| VM halt events | 0 |

---

## 5. Jetson Cluster Integration Tests

These tests verify the inter-Jetson communication layer (MQTT pub/sub, gRPC service discovery) and module health monitoring.

### 5.1 MQTT Topic Routing Test

**Purpose:** Verify that all 13 defined MQTT topics route messages correctly to the appropriate subscribers with the specified Quality of Service levels.

**Procedure:**
1. Start the MQTT broker on the primary Jetson.
2. Subscribe test clients to all 13 topics (nexus/telemetry/+, nexus/command/+, nexus/status/+, nexus/reflex/+, nexus/safety/+, nexus/observation/+, nexus/heartbeat/+, nexus/role/+, nexus/ota/+, nexus/health/+, nexus/abtest/+, nexus/learn/+, nexus/cloud/+).
3. Publish a test message to each topic individually.
4. Verify the correct subscriber receives each message.
5. For topics requiring QoS 1 (at-least-once) or QoS 2 (exactly-once), verify the broker delivers the correct QoS guarantee:
   - QoS 1: send message, disconnect subscriber before ACK, reconnect, verify redelivery.
   - QoS 2: send message, verify four-part handshake (PUBLISH → PUBREC → PUBREL → PUBCOMP).
6. For topics using QoS 0 (at-most-once, e.g., high-frequency telemetry), verify that messages are delivered at least once under normal conditions and that dropped messages under load do not stall the system.

**Metrics:**
| Metric | Threshold |
|---|---|
| Correct topic-to-subscriber routing | 13/13 topics |
| QoS 0 delivery under normal load | ≥ 99.5% |
| QoS 1 redelivery after disconnect | Yes |
| QoS 2 exactly-once guarantee | Yes (no duplicates, no losses in 100 messages) |
| Message latency (pub to sub) | < 50 ms |

### 5.2 gRPC Service Discovery Test

**Purpose:** Verify the gRPC-based NodeDiscovery and NodeManager services allow end-to-end node listing and role assignment across the cluster.

**Procedure:**
1. Start all Jetson nodes in the cluster (3 Jetsons minimum for test).
2. Connect at least 2 ESP32 nodes to each Jetson (6 total).
3. Call `NodeDiscovery.ListNodes` on each Jetson. Verify:
   - All ESP32 nodes connected to that Jetson are listed with correct serial numbers, firmware versions, and current roles.
4. Call `NodeManager.AssignRole` on Jetson A to change the role of one of its connected ESP32 nodes.
5. Verify:
   - gRPC call returns success.
   - The role change is propagated over the serial link (ESP32 confirms with ROLE_ASSIGN_ACK).
   - Subsequent `ListNodes` calls reflect the new role.
   - MQTT topic `nexus/role/<node_id>` publishes the role change event.
   - Other Jetsons receive the event via MQTT subscription.

**Metrics:**
| Metric | Threshold |
|---|---|
| ListNodes returns all connected nodes | 100% |
| AssignRole propagates to ESP32 | Within 500 ms |
| MQTT event published on role change | Yes |
| Other Jetsons receive role change event | Within 1 second |
| No stale data after role change | Yes |

### 5.3 Module Health Check Test

**Purpose:** Verify the Jetson module health monitoring system correctly detects healthy and unhealthy module states, and that module failures are isolated without cascading.

**Procedure:**
1. Start all Jetson modules: serial_bridge, node_manager, mqtt_broker, learning_pipeline, trust_score, autonomy_manager, code_generator, ota_manager.
2. Call `health_check()` on each module. All must return `HEALTHY` status.
3. Simulate a failure: kill the `learning_pipeline` process (SIGKILL).
4. Within the health check interval (≤ 5 seconds), verify:
   - `health_check()` for `learning_pipeline` returns `UNHEALTHY`.
   - An MQTT alert is published to `nexus/health/learning_pipeline` with status `UNHEALTHY`.
   - All other modules continue to report `HEALTHY` (no cascade failure).
   - The serial bridge continues forwarding telemetry (ESP32 nodes unaffected).
5. Restart the `learning_pipeline` process. Verify it rejoins the cluster and reports `HEALTHY`.

**Metrics:**
| Metric | Threshold |
|---|---|
| All modules initially HEALTHY | 8/8 |
| Failed module detected as UNHEALTHY | Within 5 seconds |
| Other modules remain HEALTHY | 7/7 |
| Serial bridge unaffected by module failure | Yes (telemetry continues) |
| Failed module recovers after restart | Yes, HEALTHY within 10 seconds |

---

## 6. AI Pipeline Integration Tests

These tests verify the cloud code generation and A/B testing pipelines, which are the key differentiators of the NEXUS platform.

### 6.1 Code Generation Round-Trip

**Purpose:** Validate the end-to-end flow from natural language intent to a deployed, executing reflex on the ESP32, including LLM-based validation to prevent self-validation bias.

**Procedure:**
1. **Input prompt:** "Create a PID reflex that holds heading at 45 degrees with Kp=1.0, Ki=0.05, Kd=0.3. Input: imu_yaw. Output: rudder_pwm (center=1500, range ±500)."
2. **LLM code generation:** The code_generator module sends this prompt to the code-generation LLM and receives a reflex JSON definition.
3. **Schema validation:** Pass the generated JSON through the JSON Schema validator (reflex_definition.json). Verify it passes without errors.
4. **Separate LLM validation:** Send the generated JSON (not the original prompt) to a *different* LLM instance configured as a code reviewer. The reviewer must verify: correct PID structure, safe parameter ranges, no forbidden opcodes, memory access within bounds, cycle budget reasonable. This eliminates self-validation bias.
5. **Bytecode compilation:** Compile the validated JSON to bytecode using the Jetson-side compiler. Verify no compilation errors.
6. **Deployment:** Deploy the bytecode to the ESP32 via REFLEX_DEPLOY. Verify ACK.
7. **Execution and verification:** Feed synthetic IMU yaw data (ramp 0° → 90°) and capture rudder PWM outputs. Compare against a Python PID reference simulation. Verify outputs match within float32 epsilon.

**Metrics:**
| Metric | Threshold |
|---|---|
| LLM generates valid JSON | Yes |
| JSON passes schema validation | Yes |
| Separate LLM validation passes | Yes (no safety concerns) |
| Bytecode compiles without errors | Yes |
| Reflex deploys successfully | Yes |
| Output matches Python PID reference | Within float32 epsilon |
| End-to-end latency (prompt to executing reflex) | < 30 seconds |

### 6.2 A/B Test Execution

**Purpose:** Verify the A/B testing framework correctly executes comparative tests, computes statistical significance, and recommends the optimal configuration.

**Procedure:**
1. Define a synthetic A/B test: compare two heading-hold PID configurations.
   - Variant A: Kp=0.8, Ki=0.03, Kd=0.2 (known sub-optimal)
   - Variant B: Kp=1.2, Ki=0.06, Kd=0.4 (known optimal for the test data)
2. Generate synthetic trial data: 50 trials per variant with Gaussian noise (σ=2° heading error), where Variant B has a true mean error 1.5° lower than Variant A.
3. Feed the trial results into the A/B testing module.
4. Verify:
   - Statistical significance is correctly detected (p < 0.05 using paired t-test with Bonferroni correction for multiple metrics).
   - The recommendation is Variant B (the known optimal).
   - The 7 standardized metrics (heading_error_rms, heading_error_max, overshoot_deg, settling_time_s, control_effort_rms, energy_cost_mj, stability_margin_db) are all computed correctly.
5. Verify that the result is published to `nexus/abtest/<test_id>/result` via MQTT.

**Metrics:**
| Metric | Threshold |
|---|---|
| Correct significance detection | p < 0.05 for heading_error_rms |
| Correct recommendation | Variant B |
| All 7 metrics computed | Yes |
| Bonferroni correction applied | Yes |
| Result published to MQTT | Yes |
| No false positives on noise-only data | Verified with 100 randomized synthetic runs |

---

## 7. System-Level Tests

These are end-to-end tests that exercise the complete NEXUS platform on real hardware with the full software stack running. They are the most expensive to execute and run less frequently.

### 7.1 24-Hour Soak Test

**Purpose:** Verify long-term system stability under continuous operation with all subsystems active.

**Procedure:**
1. Deploy the full system: 3 Jetson nodes, 5+ ESP32 nodes (rudder, throttle, bilge, navigation lights, sensor_hub).
2. Configure all subsystems in NORMAL operational mode:
   - Reflexes deployed and executing on all ESP32 nodes.
   - Telemetry streaming at 10 Hz per node.
   - Observation recording running on 2 sensor nodes at 50 Hz.
   - MQTT broker active, all topics subscribed.
   - Health checks running at 5-second intervals.
   - Watchdog timers active on all ESP32 nodes.
3. Run for 24 continuous hours.
4. Monitor and log the following metrics every minute:
   - CRC error count (cumulative, per serial link).
   - Sequence number gaps (per serial link).
   - Heartbeat miss count (per node).
   - Jetson memory usage (RSS, heap).
   - Jetson CPU utilization (per module).
   - ESP32 free heap memory (reported in telemetry).
   - CPU temperature (Jetson and ESP32 if available).
   - MQTT message queue depth.
5. At the end of 24 hours, analyze the log for anomalies.

**Metrics:**
| Metric | Threshold |
|---|---|
| Safety events (HALT, kill switch, watchdog) | 0 |
| Cumulative CRC errors | < 0.1% of total frames |
| Sequence number gaps | 0 |
| Heartbeat misses | 0 |
| Jetson memory growth (leak detection) | < 5% increase over 24 hours |
| ESP32 free heap stability | < 10% variation |
| MQTT queue depth (max) | < 100 messages |
| Module restarts | 0 |
| System uptime | 24 hours continuous |

### 7.2 Fault Injection Test

**Purpose:** Verify that the system responds correctly to a comprehensive set of hardware and software faults, entering safe-state and recovering gracefully where applicable.

**Procedure:**
Execute each fault scenario below in sequence. After each fault, verify the expected response, then restore normal conditions before proceeding to the next fault.

| # | Fault Scenario | Expected Response | Verification |
|---|---|---|---|
| F1 | **Jetson process crash:** Kill the serial_bridge process (SIGKILL) while ESP32 is executing reflexes. | ESP32 detects heartbeat timeout within 2 seconds → enters SAFE_STATE → all actuators to safe defaults → sends SAFETY_HEARTBEAT_TIMEOUT message. | Actuators at safe-state; no uncontrolled motion; Jetson restart of serial_bridge restores communication. |
| F2 | **Serial cable disconnect:** Physically unplug the UART cable between Jetson and ESP32 mid-operation. | ESP32 detects heartbeat timeout (no ACK received) → safe-state after timeout period. Jetson detects UART break condition → logs disconnection event → attempts reconnection. | Reconnect cable → system re-establishes communication → reflexes resume (from cached bytecode). |
| F3 | **I2C bus short:** Short SDA to GND on the ESP32's I2C bus during sensor reading. | ESP32 I2C driver detects bus lock → initiates bus recovery (clock up to 9 cycles) → reports I2C_BUS_ERROR. Reflex continues with last-known-good sensor value (fallback). | Bus recovers within 100 ms; no reflex halt; stale-data flag set in telemetry. |
| F4 | **Actuator overcurrent:** Apply excessive load to an actuator channel to trigger overcurrent detection. | ESP32 hardware overcurrent comparator trips → ISR fires → PWM output disabled on that channel → OVERCURRENT event sent to Jetson. Other channels unaffected. | Channel remains disabled until manually cleared; no hardware damage; event logged. |
| F5 | **Kill switch during OTA:** Press the physical kill switch while an OTA firmware update is in progress. | Kill switch ISR fires immediately (highest priority) → all outputs to safe-state → OTA process aborted (ESP32 does not apply partial firmware) → system remains on previous firmware version. | System boots on previous firmware after kill switch release; no bricked device; OTA rollback successful. |

**Metrics:**
| Metric | Threshold |
|---|---|
| Correct safe-state response for each fault | 5/5 scenarios |
| No uncontrolled actuator motion | Verified (oscilloscope/log) |
| Recovery after fault cleared | All recoverable scenarios restore normal operation |
| No data corruption after recovery | CRC checks pass post-recovery |
| Kill switch response time | < 10 ms (hardware ISR) |

### 7.3 Multi-Node Scalability Test

**Purpose:** Verify that a single Jetson can reliably manage 10 ESP32 nodes simultaneously at full operational rate.

**Procedure:**
1. Connect 10 ESP32 nodes to a single Jetson via a USB hub (or multi-port UART adapter).
2. Deploy reflexes to all 10 nodes (varied roles: 3x autopilot, 3x sensor, 2x bilge, 2x lights).
3. Run all nodes at 100 Hz telemetry simultaneously for 30 minutes.
4. Monitor:
   - Message loss rate (sequence number audit on every serial link).
   - Tick timing accuracy (verify 100 Hz ±5% on all nodes).
   - Jetson serial bridge CPU and memory utilization.
   - Serial link utilization (bytes/second vs theoretical maximum).
5. Verify that no node experiences degraded performance due to contention on the Jetson side.

**Metrics:**
| Metric | Threshold |
|---|---|
| Message loss rate (aggregate) | 0% |
| Tick timing accuracy (all 10 nodes) | 95–105 Hz |
| Jetson CPU utilization | < 80% |
| Serial link utilization (per link) | < 80% of link capacity |
| Memory stable (no leak over 30 min) | < 5% growth |
| All nodes operational at end of test | 10/10 |

---

## Test Automation

### Tooling Recommendations

| Component | Tool | Rationale |
|---|---|---|
| Jetson-side test framework | **pytest** (Python 3.10+) | Native Python; integrates with gRPC and MQTT client libraries; fixtures for serial port management; rich assertion reporting. |
| ESP32-side test framework | **Unity + CMock** (C) | Industry-standard for embedded C; minimal footprint; supports mocking of HAL layer; integrates with ESP-IDF build system. |
| CI/CD orchestration | **GitHub Actions** or **GitLab CI** | Matrix builds for ESP32 (xtensa) and Jetson (aarch64); artifact storage for test reports; nightly schedule triggers. |
| Test result reporting | **Allure** or **JUnit XML** | Generates HTML test reports with history tracking; integrates with pytest and Unity output adapters. |
| Hardware-in-the-loop fixture | **Custom Python test harness** | Manages power cycling (relay control), serial port enumeration, MQTT topic monitoring, and result collection. |

### CI/CD Pipeline Stages

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌────────────┐
│  Every       │───▶│  Nightly          │───▶│  Weekly        │───▶│  Release    │
│  Commit      │    │  Integration      │    │  System       │    │  Gate       │
│              │    │                   │    │               │    │             │
│ • Unit tests │    │ • Integration     │    │ • 24h soak    │    │ • All tests │
│   (ESP32 +   │    │   tests 1–6       │    │ • Fault       │    │   pass      │
│    Jetson)   │    │ • Multi-node      │    │   injection   │    │ • Performance│
│ • Lint /     │    │   (10 nodes)      │    │ • Cold/warm   │    │   baselines │
│   static     │    │ • A/B test        │    │   boot        │    │   met       │
│   analysis   │    │   framework       │    │ • Scale test  │    │ • Sign-off   │
└─────────────┘    └──────────────────┘    └───────────────┘    └────────────┘
```

### Test Environment Requirements

- **Bench setup:** Dedicated test bench with controllable power supply (relay-switched), oscilloscope or logic analyzer, and USB hub for multi-node serial connections.
- **Thermal chamber (optional):** For extended soak testing at elevated temperatures (40°C ambient) to catch thermal-related failures.
- **Network isolation:** Test MQTT broker on an isolated VLAN to prevent test traffic from interfering with production systems.

---

## Pass/Fail Summary Matrix

| Test ID | Test Name | Level | Pass Criteria | Priority |
|---|---|---|---|---|
| **1.1** | COBS Round-Trip | Integration | 0 mismatches, 0 frame drops in 10,000 payloads | Critical |
| **1.2** | CRC-16 Coverage | Integration | 100% single-bit corruption rejection | Critical |
| **1.3** | Baud Rate Stress | Integration | 0 errors in 1-hour continuous 921600 baud | Critical |
| **1.4** | Flow Control | Integration | 0 bytes lost during backpressure | Critical |
| **2.1** | Reflex Deploy-Execute-Verify | Integration | Bytecode output matches Python reference within float32 epsilon | Critical |
| **2.2** | Multi-Reflex Priority | Integration | Correct priority arbitration 100% of ticks | High |
| **2.3** | Reflex Hot-Swap | Integration | Seamless swap, 0 tick gaps, no actuator glitch | High |
| **2.4** | VM Safety Halt Recovery | Integration | Clean halt, safe-state, clean resume | Critical |
| **3.1** | Cold Boot Timing | Integration | < 5 seconds to first TELEMETRY | High |
| **3.2** | Warm Boot (ESP32) | Integration | Full reconnection < 2 seconds | High |
| **3.3** | Role Reassignment | Integration | Clean transition, no stuck actuators | High |
| **4.1** | Record-Transfer-Verify | Integration | CRC-32 match, correct sample count | High |
| **4.2** | Observation Buffer Overflow | Integration | Auto-stop, no data corruption | Medium |
| **4.3** | Observation During Reflex | Integration | No timing interference, valid data | High |
| **5.1** | MQTT Topic Routing | Integration | 13/13 topics correct, QoS guarantees met | High |
| **5.2** | gRPC Service Discovery | Integration | End-to-end role assignment via gRPC | High |
| **5.3** | Module Health Check | Integration | Failure detection, isolation, recovery | High |
| **6.1** | Code Generation Round-Trip | Integration | NL → JSON → bytecode → executing reflex, < 30s | High |
| **6.2** | A/B Test Execution | Integration | Correct significance detection and recommendation | Medium |
| **7.1** | 24-Hour Soak Test | System | 0 safety events, < 0.1% CRC error rate, stable memory | Critical |
| **7.2** | Fault Injection | System | Correct safe-state response to all 5 fault scenarios | Critical |
| **7.3** | Multi-Node Scalability | System | 10 nodes, 0 message loss, < 80% utilization | Critical |

**Total Tests:** 22 (18 Integration, 4 System)
**Critical Tests:** 10 (must pass for release)
**High Priority Tests:** 10
**Medium Priority Tests:** 2

---

*Document maintained by the NEXUS integration engineering team. Update this plan as the platform evolves and new subsystems are added.*
