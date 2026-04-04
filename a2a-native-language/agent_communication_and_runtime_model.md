# Agent Communication & Runtime Model for A2A-Native Programming in NEXUS

**Document ID:** NEXUS-A2A-AGENT-001  
**Version:** 1.0  
**Date:** 2025-07-12  
**Status:** Deep Research — Agent Communication, Equipment Runtime, and Vessel Hardware Model  

---

## Table of Contents

1. [Introduction: The Three Pillars of Agent Actualization](#1-introduction-the-three-pillars-of-agent-actualization)
2. [Agent-to-Agent Communication Protocol](#2-agent-to-agent-communication-protocol)
3. [The Equipment Runtime Model](#3-the-equipment-runtime-model)
4. [The Vessel Hardware Model](#4-the-vessel-hardware-model)
5. [Multi-Agent Coordination](#5-multi-agent-coordination)
6. [The Equipment-Vessel Contract](#6-the-equipment-vessel-contract)
7. [Concrete Scenarios](#7-concrete-scenarios)
8. [Conclusions and Open Questions](#8-conclusions-and-open-questions)

---

## 1. Introduction: The Three Pillars of Agent Actualization

The NEXUS platform introduces a radical re-conception of how autonomous systems operate. In traditional robotics, a human programmer writes code that runs on hardware. In NEXUS, an **agent** — an autonomous software entity with a system prompt, a trust score, and a compiled bytecode program — translates intention into physical action through a layered architecture we call the **Three Pillars**:

| Pillar | Role | NEXUS Implementation |
|--------|------|---------------------|
| **System Prompt** | Compiler frontend: defines how an agent translates intention to bytecode | Qwen2.5-Coder-7B generating JSON reflex definitions, safety-validated by Claude 3.5 Sonnet |
| **Equipment** | Runtime environment: everything between bytecode and metal | The 32-opcode bytecode VM, wire protocol, safety system, trust framework, OS scheduler |
| **Vessel** | Hardware platform: physical capabilities and constraints | ESP32-S3 limbs, Jetson Orin Nano brains, RS-422 links, sensors, actuators |

The central thesis is: **with the right system prompt + the right equipment + the right vessel, any agent can actualize an intention to the full capability of the hardware.** This document explores the deep architecture that makes this possible, with particular focus on how agents communicate through bytecode, how the equipment runtime manages resources, and how the vessel hardware defines capability boundaries.

This architecture implements what the NEXUS literature calls the **"ribosome not brain"** thesis: ESP32 nodes are ribosomes — simple, local, reliable instruction followers — while the Jetson cognitive cluster is a nervous system — coordinating behavior without micromanaging individual cell operations. The ribosome architecture provides 99.97% availability across 10,000-hour simulations, because each ESP32 continues executing its current reflex bytecode autonomously during Jetson communication loss.

---

## 2. Agent-to-Agent Communication Protocol

### 2.1 Intention Emission, Not Message Passing

In NEXUS, agents do not communicate through traditional message-passing abstractions (RPCs, pub/sub topics, or request-response pairs). Instead, agents **emit intentions** — bytecode programs that express what they want to accomplish — and other agents **interpret** those intentions through their own equipment runtime.

This is a fundamental architectural distinction:

| Traditional Approach | NEXUS Approach |
|---------------------|----------------|
| Agent A sends command "set_throttle(40)" | Agent A compiles reflex bytecode expressing intention "reduce speed when wind gusts > 15 m/s" |
| Agent B receives and executes | Agent B's equipment runtime loads and validates the bytecode |
| Tight temporal coupling | Loose coupling through shared intention language |
| Requires shared API schema | Requires shared bytecode ISA (32 opcodes) |
| Central coordination | Distributed coordination through bytecode semantics |

The bytecode ISA serves as the **universal language of intention**. Any agent that can compile to the 32-opcode NEXUS ISA can express intentions to any other agent, regardless of their system prompt, their equipment configuration, or their vessel hardware. The ISA is provably Turing-complete and can compute all continuous piecewise-polynomial functions (proven via the Stone-Weierstrass approximation theorem), making it sufficient for expressing any control intention.

### 2.2 Agent Identity and Capability Advertisement

Every agent in the NEXUS ecosystem identifies itself through a structured identity protocol that occurs at boot time:

**Tier 1 (MCU Limb) Identity:**
The ESP32 firmware sends a `DEVICE_IDENTITY` message (type 0x01) containing:
- MAC address (unique hardware identifier)
- Chip type (ESP32-S3, ESP32-C6, STM32H7, etc.)
- Firmware version (semantic versioning)
- Capabilities vector: which sensor types are physically connected, which actuators are available, which reflex slots are populated

This is followed by an `AUTO_DETECT_RESULT` (type 0x1B) with I2C bus scan results identifying all connected sensors by their I2C addresses, and a `SELFTEST_RESULT` (type 0x04) confirming per-pin continuity and CRC verification.

**Tier 2 (Jetson Cognitive) Identity:**
Jetson nodes advertise their identity through the gRPC cluster API:
- `NodeDiscovery.ListNodes()` returns all connected MCU nodes
- `NodeDiscovery.GetNodeInfo()` returns detailed capabilities including loaded reflexes, trust scores, autonomy levels
- MQTT topics `nexus/jetson/{id}/trust` and `nexus/jetson/{id}/status` provide continuous capability updates

**Agent Capability Descriptor (Machine-Readable):**

```json
{
  "agent_id": "esp32-AABBCCDDEEFF",
  "vessel_id": "vessel-marinus-01",
  "equipment_class": "limb",
  "capabilities": {
    "sensors": ["compass_3axis", "gps_rtk", "imu_9dof", "wind_anemometer"],
    "actuators": ["rudder_pwm", "throttle_relay", "anchor_winch"],
    "reflex_slots": {"total": 50, "used": 7, "available": 43},
    "vm_features": ["pid_controller", "state_machine", "rate_limiter", "signal_filter"],
    "tick_rate_hz": [100, 500, 1000],
    "isa_version": "1.0",
    "firmware_hash_sha256": "a3f2b8..."
  },
  "trust_state": {
    "subsystems": {
      "steering": {"score": 0.85, "level": 4},
      "engine": {"score": 0.72, "level": 3}
    }
  },
  "constraints": {
    "max_cycle_budget": 10000,
    "max_stack_depth": 256,
    "max_bytecode_size": 4000,
    "safety_policy_version": "2.0.0"
  }
}
```

### 2.3 Intention Negotiation Protocol

When an agent on one vessel wants to coordinate with an agent on another vessel, they negotiate through a multi-phase intention protocol:

**Phase 1: Capability Discovery**
- Agent A queries Agent B's capability descriptor
- Agent A determines whether its intention can be expressed in Agent B's bytecode vocabulary
- If Agent B lacks a required sensor type, negotiation fails immediately (no point compiling bytecode for non-existent hardware)

**Phase 2: Intention Compilation**
- Agent A's system prompt (the "compiler frontend") generates a JSON reflex definition
- The reflex is validated by the safety system (separate AI validator, 95.1% catch rate)
- The reflex is compiled to bytecode targeting Agent B's specific equipment configuration (pin mappings, sensor indices, actuator limits)

**Phase 3: Intention Deployment**
- Bytecode is transmitted via REFLEX_DEPLOY (message 0x09) through the wire protocol
- Agent B's equipment runtime validates the bytecode (stack balance, jump targets, cycle budget, NaN/Inf immediates)
- Agent B loads the bytecode into a reflex slot and begins execution at the configured tick rate

**Phase 4: Trust-Gated Activation**
- The deployed reflex includes a `min_autonomy_level` precondition
- Agent B checks its current trust score for the relevant subsystem
- If trust exceeds the threshold, the reflex activates; otherwise, it waits in standby

**Phase 5: Continuous Monitoring**
- Agent B executes the reflex and reports results via TELEMETRY (message 0x06)
- Trust score is updated based on execution quality
- If trust drops below threshold, the reflex is automatically deactivated

This negotiation is fundamentally different from RPC-based communication because the intention is **self-contained** — the bytecode includes all logic, state, and safety constraints. The receiving agent does not need to call back to the sending agent for guidance; it executes autonomously.

### 2.4 Delegation: Sub-Intention Across Vessels

A key capability of the A2A model is **intention delegation** — an agent on one vessel delegating a sub-intention to an agent on a different vessel. This is not remote procedure call; it is remote intention deployment.

**Delegation Protocol:**

1. **Intention Decomposition:** The originating agent's system prompt decomposes a complex intention into sub-intentions, each targetable at a specific vessel's capabilities.

2. **Per-Vessel Compilation:** Each sub-intention is compiled independently, targeting the specific equipment and vessel of the delegate agent. Pin mappings, sensor indices, and actuator limits are resolved at compile time.

3. **Deployment via Wire Protocol:** Sub-intentions are transmitted through the network architecture (RS-422 serial for same-vessel, MQTT/gRPC for cross-vessel, Starlink/5G for cloud-mediated cross-site).

4. **Autonomous Execution:** The delegate agent executes the sub-intention independently, reporting results back through the telemetry hierarchy.

5. **Composition:** The originating agent composes results from multiple delegates into a higher-level outcome.

**Critical insight:** Because the bytecode VM is provably deterministic (Theorem 4: identical inputs produce identical outputs in identical cycles), the originating agent can **predict** the delegate's behavior with perfect accuracy, given knowledge of the delegate's sensor inputs. This eliminates the need for tight temporal coupling between delegator and delegate.

### 2.5 Conflict Resolution for Competing Intentions

When two agents' intentions conflict on shared hardware resources, the NEXUS architecture resolves conflicts through a priority-based system:

1. **Priority Assignment:** Each reflex has a priority field (1 = highest, 5 = lowest). Higher-priority reflexes preempt lower-priority ones.

2. **Actuator Arbitration:** When multiple reflexes write to the same actuator register, the safety system applies **last-writer-wins** semantics within a tick. Since reflexes execute sequentially (not concurrently), the execution order determines which reflex's output is applied.

3. **Safety Override:** Any reflex that produces an output violating the safety policy (e.g., rudder angle exceeding safe limits) is clamped by the post-execution actuator clamping step, regardless of priority.

4. **Trust-Veto:** If two reflexes have conflicting intentions and the lower-priority reflex has a higher trust score, the equipment runtime may suspend the higher-priority but less-trusted reflex. This is the "communal veto" mechanism inspired by the Ubuntu philosophical tradition.

5. **Kill Switch Absolute Authority:** The hardware kill switch (Tier 1 safety) overrides all software-level conflict resolution. When activated, all actuators enter safe state within 1ms, regardless of any agent's intention.

---

## 3. The Equipment Runtime Model

### 3.1 What Is Equipment?

Equipment is the **runtime environment** that sits between the agent's bytecode and the vessel's hardware. It is the "everything else" — the bytecode VM, the wire protocol stack, the safety system, the trust framework, the OS scheduler, the device drivers, and the resource allocator.

```
┌─────────────────────────────────────────────────────┐
│                  AGENT (System Prompt)               │
│  Qwen2.5-Coder-7B  →  JSON Reflex  →  Bytecode      │
└──────────────────────┬──────────────────────────────┘
                       │ Compiled Intention
                       ▼
┌─────────────────────────────────────────────────────┐
│                  EQUIPMENT (Runtime)                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ Bytecode  │ │  Safety   │ │  Trust    │          │
│  │    VM     │ │  System   │ │  Engine   │          │
│  │ 32 opcode │ │ 4-tier    │ │ INCREMENTS│          │
│  │ 3KB RAM   │ │ IEC 61508 │ │ 25:1 ratio│          │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘          │
│        │             │             │                  │
│  ┌─────┴─────────────┴─────────────┴─────┐          │
│  │         Resource Manager               │          │
│  │  Cycle budget │ Stack │ Memory │ I/O   │          │
│  └─────────────────┬──────────────────────┘          │
│                    │                                   │
│  ┌─────────────────┴──────────────────────┐          │
│  │       Wire Protocol Stack               │          │
│  │  COBS framing │ CRC-16 │ 28 msg types   │          │
│  └─────────────────┬──────────────────────┘          │
└────────────────────┼──────────────────────────────────┘
                       │ RS-422 / MQTT / gRPC
                       ▼
┌─────────────────────────────────────────────────────┐
│                  VESSEL (Hardware)                    │
│  ESP32-S3 │ Jetson Orin Nano │ Sensors │ Actuators  │
└─────────────────────────────────────────────────────┘
```

### 3.2 The Bytecode VM as Equipment Core

The 32-opcode bytecode VM is the heart of the equipment runtime. Its design properties directly enable A2A communication:

| Property | Value | A2A Significance |
|----------|-------|-------------------|
| ISA size | 32 opcodes + 4 syscalls | Small enough for any agent's compiler to target |
| Instruction width | 8 bytes (fixed) | Predictable transmission size over wire protocol |
| Memory footprint | ~3 KB static (5,280 B full) | Fits on any MCU meeting minimum specs |
| Execution time | 44 μs mean (PID controller) | 15,000× faster than human response |
| Determinism | Proven (Theorem 4) | Predictable behavior for remote agents |
| Type safety | Proven no NaN/Inf to actuators (Theorem 3) | Safe for untrusted remote intention |
| Cycle budget | 10,000 cycles/tick max | Bounded resource consumption |
| Code size | 80–520 B per reflex (typical) | Efficient transmission over serial links |

The VM's **determinism guarantee** is the cornerstone of A2A communication. When Agent A compiles an intention and deploys it to Agent B, Agent A can predict Agent B's exact behavior because the VM will produce identical outputs given identical sensor inputs, in exactly the same number of cycles, every single time. This transforms remote deployment from an uncertain RPC call into a precise mathematical operation.

### 3.3 Equipment as Capability Provider

The equipment runtime provides capabilities to agent bytecode through a structured abstraction:

**Sensor Access (Input Path):**
1. Physical sensor hardware produces raw signals (I2C, SPI, ADC, UART)
2. Equipment's I/O driver layer reads and normalizes signals
3. Equipment populates the VM's 64 sensor registers (float32 each) before each tick
4. Bytecode accesses sensors via `READ_PIN` opcode with sensor index

**Actuator Control (Output Path):**
1. Bytecode writes to the VM's 64 actuator registers via `WRITE_PIN` opcode
2. Post-execution clamping applies configured min/max bounds
3. Safety system validates output against safety policy
4. Equipment's I/O driver layer converts float32 values to hardware signals (PWM, relay, DAC)

**Compute Resources:**
- PID controllers: 8 hardware-accelerated PID state machines (via `PID_COMPUTE` syscall)
- Timing: `READ_TIMER_MS` provides tick-count for temporal logic
- State: 256 persistent float32 variables across ticks (via `READ_PIN`/`WRITE_PIN` with index ≥ 64)
- Events: 32-entry event ring buffer for asynchronous notifications (via `EMIT_EVENT`/`RECORD_SNAPSHOT` syscalls)

**Equipment Introspection API:**

An agent can query its equipment's capabilities at runtime through the bytecode event mechanism and the wire protocol:

| Query Method | Mechanism | Response |
|-------------|-----------|----------|
| What sensors are available? | `AUTO_DETECT_RESULT` at boot | List of detected I2C addresses, ADC channels |
| What actuators are connected? | `ROLE_ASSIGN` pin map | JSON mapping logical names to GPIO pins |
| How much cycle budget remains? | Cycle counter in VM context | Remaining cycles before budget exhaustion |
| What reflexes are loaded? | `REFLEX_STATUS` response | List of loaded reflexes with status |
| What is my trust score? | `GetTrustScore` gRPC call | Per-subsystem trust scores and autonomy levels |
| Am I still connected to my Jetson? | Heartbeat timeout detection | HEALTHY / WARN / DEGRADED / FAILSAFE state |

### 3.4 Resource Management in Equipment

The equipment runtime manages resources between competing agent programs through several mechanisms:

**Cycle Budget Enforcement:**
- Maximum 10,000 VM cycles per tick (configurable)
- If exceeded, VM halts and places actuators in safe position
- Typical reflex programs use 10–368 cycles (0.1–3.7% of budget)
- WCET is computable statically by the compiler

**Memory Allocation:**
- Zero heap allocation during VM execution
- Static allocation: 256 stack entries (1 KB), 256 variables (1 KB), 8 PID controllers (256 B)
- Reflex programs stored in 2 MB LittleFS partition (maximum 200 reflex programs at ~2 KB average)
- No garbage collection, no fragmentation risk

**I/O Bandwidth:**
- RS-422 link at 921,600 baud provides ~91,200 B/s effective throughput
- Normal operation uses <1% of link capacity per ESP32 node
- Priority queuing: Safety > Critical > Normal > Bulk
- CTS/RTS hardware flow control with backpressure at 50% buffer capacity

**Concurrent Reflex Scheduling:**
- Multiple reflex programs can be loaded simultaneously
- Reflexes execute sequentially within a tick (not preemptively)
- Priority determines execution order
- Each reflex can have independent tick rate (100, 500, or 1000 Hz)

**Real-Time Constraints:**

| Constraint | Value | Enforcement |
|-----------|-------|-------------|
| Max tick duration | 1 ms (at 1 kHz) | FreeRTOS timer callback |
| Max cycle budget | 10,000 cycles | VM cycle counter |
| Max stack depth | 256 entries | PUSH/POP bounds check |
| Sensor read latency | <100 μs (I2C) | Hardware I2C @ 400 kHz |
| Actuator write latency | <50 μs (PWM) | Hardware PWM peripheral |
| Watchdog timeout | 1.0 s (MAX6818) | Hardware watchdog, non-configurable |
| Kill switch response | <1 ms | ISR in IRAM, priority level 1 |

### 3.5 Equipment Constraints and Graceful Degradation

The equipment runtime is designed to degrade gracefully under stress:

**Thermal Throttling (Jetson):**
- SoC temperature monitoring triggers service shedding at 85°C
- Non-essential services (MQTT telemetry, cloud sync) are shed first
- Reflex execution and safety monitoring continue at all times
- Full performance available below 78°C; 25% degradation at 92°C

**Memory Pressure:**
- If reflex storage exceeds 75% of LittleFS partition, oldest reflexes by last-use time are archived
- If VM stack approaches limit (>200 entries), warning event emitted
- If observation buffer fills, oldest data is overwritten (ring buffer)

**Communication Degradation:**
- Heartbeat escalation: HEALTHY → WARN (2 misses) → DEGRADED (5 misses) → FAILSAFE (10 misses)
- In FAILSAFE state, ESP32 continues executing loaded reflexes autonomously
- On communication recovery, ESP32 re-synchronizes with Jetson

**Power Budget:**
- ESP32-S3 active power: ~240 mW (acceptable for battery-backed operation)
- Jetson Orin Nano: 15–25W (requires mains power or large battery)
- Equipment monitors power rail voltage and can shed services to reduce consumption

---

## 4. The Vessel Hardware Model

### 4.1 Vessel as Capability Boundary

A **vessel** is the physical hardware platform on which equipment runs. It defines the hard boundary of what an agent can and cannot do. The NEXUS architecture is vessel-agnostic by design: the same equipment runtime (same bytecode VM, same wire protocol, same safety system) runs on any vessel that meets the minimum specifications.

**Vessel Capability Hierarchy:**

```
Vessel (Physical Platform)
├── Compute Tier
│   ├── Tier 1: MCU Reflex Layer (ESP32-class)
│   │   └── 200 MHz dual-core, 512 KB SRAM, 8 MB PSRAM
│   ├── Tier 2: Cognitive Layer (Jetson-class)
│   │   └── 6-core ARM Cortex-A78AE, 8 GB LPDDR5, 40 TOPS
│   └── Tier 3: Cloud (Optional)
│       └── Heavy reasoning, fleet management
├── Sensor Tier
│   ├── Navigation (GPS, compass, IMU)
│   ├── Environment (wind, temperature, depth)
│   ├── Perception (LIDAR, radar, camera, AIS)
│   └── System (current, temperature, voltage)
├── Actuator Tier
│   ├── Propulsion (throttle, steering)
│   ├── Auxiliary (pumps, lights, horn)
│   └── Safety (kill switch, emergency systems)
└── Communication Tier
    ├── Intra-vessel: RS-422 serial (921,600 baud)
    ├── Inter-Jetson: gRPC + MQTT (Gigabit Ethernet)
    └── Extra-vessel: Starlink/5G (cloud)
```

### 4.2 Vessel Capability Descriptor Format

Every vessel publishes a machine-readable capability descriptor that enables agents to adapt their intentions to the hardware:

```json
{
  "vessel_id": "vessel-marinus-01",
  "vessel_class": "marine_autonomous",
  "hardware": {
    "mcu_nodes": [
      {
        "node_id": "esp32-AABBCCDDEEFF",
        "soc": "ESP32-S3",
        "clock_mhz": 240,
        "sram_kb": 512,
        "psram_mb": 8,
        "flash_mb": 16,
        "uart_count": 3,
        "i2c_count": 2,
        "adc_channels": 20
      }
    ],
    "cognitive_nodes": [
      {
        "node_id": "jetson-001",
        "soc": "Jetson Orin Nano Super",
        "gpu_tops": 40,
        "cpu_cores": 6,
        "ram_gb": 8,
        "storage": "256 GB NVMe",
        "roles": ["chat", "vision", "stt_tts"]
      }
    ]
  },
  "connectivity": {
    "intra_vessel": {
      "protocol": "RS-422",
      "baud_rate": 921600,
      "topology": "star",
      "max_cable_m": 10
    },
    "inter_vessel": {
      "protocol": "MQTT-over-WiFi",
      "broker": "EMQX cluster",
      "latency_ms": "10-100"
    },
    "cloud": {
      "protocol": "Starlink",
      "latency_ms": "20-80",
      "availability_pct": 99.5
    }
  },
  "sensors": {
    "gps": {"type": "rtk", "accuracy_m": 0.02, "update_hz": 10},
    "compass": {"type": "3axis_i2c", "accuracy_deg": 1.0, "update_hz": 50},
    "imu": {"type": "9dof", "accel_range_g": 16, "gyro_range_dps": 2000},
    "wind": {"type": "anemometer", "range_ms": [0, 60], "accuracy_ms": 0.3}
  },
  "actuators": {
    "rudder": {"type": "pwm_servo", "range_deg": [-45, 45], "safe_deg": 0},
    "throttle": {"type": "relay", "range_pct": [0, 100], "safe_pct": 0},
    "anchor_winch": {"type": "motor_pwm", "range_m": [0, 30], "safe_m": 0}
  },
  "power": {
    "main_supply_v": 12,
    "battery_capacity_wh": 500,
    "solar_w": 100,
    "max_draw_w": 150
  },
  "environmental": {
    "operating_temp_c": [-15, 55],
    "ingress_protection": "IP67",
    "vibration_tolerance": "IEC 60945 Category A"
  }
}
```

### 4.3 Heterogeneous Fleet Operation

A key feature of the NEXUS architecture is the ability to operate across vessels with vastly different capabilities:

| Vessel Type | Compute | Sensors | Actuators | Use Case |
|------------|---------|---------|-----------|----------|
| **Full Autonomous** | 3× Jetson + 12× ESP32 | GPS RTK, LIDAR, radar, AIS, camera | Steering, throttle, anchor, bilge | Open-ocean autonomous transit |
| **Cognitive Light** | 1× Jetson + 4× ESP32 | GPS, compass, IMU | Steering, throttle | Coastal navigation |
| **Reflex Only** | 0× Jetson + 2× ESP32 | Compass, depth sounder | Bilge pump, alarm | Moored monitoring buoy |
| **Minimal Sensor** | 1× ESP32 | Temperature, humidity | Relay, LED | Greenhouse node |

The same bytecode ISA runs on all four vessel types. The difference is in **which reflexes can be compiled** — a vessel without GPS cannot execute a GPS-waypoint-following reflex because the sensor register will contain no valid data.

**Cross-Vessel Bytecode Sharing:**
The universal synthesis analysis (Round 5) identifies that "the same evolutionary process, run under the same constraints, converges on the same solution regardless of who initiated it." This is the **Objective Correctness principle** — bytecodes evolved on one vessel can be shared across vessels because the underlying physics is universal. However, the bytecode must be recompiled with vessel-specific pin mappings and sensor indices.

### 4.4 Hardware Failure Modes and Agent Adaptation

The NEXUS architecture handles vessel degradation through a layered resilience model:

**ESP32 Node Failure:**
- Detected by heartbeat timeout (< 100 ms, 3 consecutive misses)
- Orphaned functions are reassigned to surviving ESP32s via `ROLE_ASSIGN`
- If no spare ESP32 exists, the function degrades (e.g., sensor data becomes stale)
- Trust scores for affected subsystems are frozen; autonomy levels may decrease

**Jetson Failure:**
- Detected by gRPC heartbeat timeout (300 ms)
- Surviving Jetsons claim orphaned ESP32s via Raft leader election
- Hot standby Jetson (if provisioned) takes over within 100 ms
- Reflex bytecode continues executing on ESP32s autonomously during Jetson recovery
- System enters DEGRADED mode: no new reflex deployments, no trust updates, no cloud sync

**Sensor Failure:**
- Detected by stale data check (> 500 ms without update) or out-of-range values
- Equipment runtime substitutes 0.0 (safe default) for the failed sensor
- Reflexes depending on the sensor continue executing with degraded inputs
- Safety policy may trigger automatic autonomy level reduction

**Communication Failure:**
- RS-422 link loss: ESP32 enters FAILSAFE after 10 consecutive missed heartbeats
- MQTT broker failure: inter-vessel coordination lost, local operation continues
- Starlink outage: cloud sync deferred, no impact on real-time operation
- The system is **edge-first**: cloud is supplementary, never required for safety

**Partial Vessel Degradation:**
When a vessel loses capabilities (e.g., GPS failure), the agent's system prompt can recompile reflexes to use alternative sensor fusion (e.g., dead reckoning from IMU + compass). This is not an automatic process — it requires the cognitive layer to be operational. If the cognitive layer is also degraded, the system relies on pre-degraded reflex variants stored in the ESP32's LittleFS partition.

### 4.5 Vessel Evolution and Bytecode Portability

NEXUS vessels are designed for incremental hardware evolution:

**Hardware Upgrade Path:**
1. New ESP32 node plugged in → automatically detected via `DEVICE_IDENTITY`
2. Jetson sends `ROLE_ASSIGN` with appropriate pin mapping
3. Existing reflexes are recompiled (if needed) for the new pin configuration
4. System transitions seamlessly; no downtime required

**Firmware Upgrade Path:**
- OTA firmware updates via FIRMWARE_UPDATE_START/CHUNK/END messages
- A/B partition scheme: ota_0 and ota_1 with rollback capability
- Factory partition (512 KB) is never modified — trusted recovery image
- SHA-256 hash verification prevents corrupted firmware from being applied
- Rollback occurs automatically if health check fails within 60-second probation period

**Bytecode Forward Compatibility:**
The 32-opcode ISA is fixed — no new opcodes are added. New capabilities are exposed through:
- New syscalls (using NOP opcode with SYSCALL flag, bit 7 of flags byte)
- New sensor/actuator types (new I2C drivers with same READ_PIN/WRITE_PIN interface)
- New reflex parameters (new JSON fields compiled to existing bytecode patterns)

This means bytecode compiled for one firmware version will continue to work on future firmware versions. The VM's determinism guarantee is preserved across firmware updates.

---

## 5. Multi-Agent Coordination

### 5.1 Colony Model: Multi-Agent, Multi-Vessel

The most advanced coordination mode in NEXUS is the **colony model** — multiple agents coordinating across multiple vessels to achieve fleet-level objectives. This extends the multicellular analogy: individual cells (ESP32 nodes) form tissues (vessels), which form organs (subsystems), which form the organism (fleet).

**Colony Coordination Hierarchy:**

```
┌──────────────────────────────────────────────────────┐
│                   FLEET INTELLIGENCE                   │
│  Cloud / Fleet Manager (optional)                     │
│  - Cross-vessel task allocation                        │
│  - Fleet-level trust aggregation                       │
│  - Long-term pattern discovery                         │
└──────────────────────┬───────────────────────────────┘
                       │ MQTT / Starlink
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  VESSEL A   │ │  VESSEL B   │ │  VESSEL C   │
│ Jetson Lead │ │ Jetson Peer │ │ Jetson Peer │
│ ┌──┬──┬──┐ │ │ ┌──┬──┬──┐ │ │ ┌──┬──┬──┐ │
│ │E0│E1│E2│ │ │ │E3│E4│E5│ │ │ │E6│E7│E8│ │
│ └──┴──┴──┘ │ │ └──┴──┴──┘ │ │ └──┴──┴──┘ │
└────────────┘ └────────────┘ └────────────┘
```

**Fleet-Level Consensus (Raft Protocol):**
The 3-Jetson cluster uses Raft consensus for fleet-level decisions:
- Leader Jetson proposes reflex deployments, trust updates, and task allocations
- 2-of-3 Jetsons must ACK for the proposal to commit
- Leader election within 300 ms of leader failure
- Split-brain prevention through strict majority requirement

**Trust Score Synchronization:**
Trust scores are synchronized across the fleet using CRDT (Conflict-free Replicated Data Type) with Last-Writer-Wins merge:
- Each trust update carries a timestamp and Jetson ID
- Merging resolves conflicts by accepting the most recent update
- Eventual consistency with bounded staleness (< 1 second via MQTT QoS 2)

### 5.2 Fleet Orchestration Scenarios

**Hierarchical Agent Structures:**
A single supervisory agent (on the lead Jetson) can coordinate many vessels by deploying intentions to each vessel's equipment runtime:

1. The supervisory agent decomposes a fleet-level objective (e.g., "search area X for target Y") into vessel-specific sub-objectives
2. Each sub-objective is compiled to bytecode targeting the specific vessel's equipment
3. Bytecodes are deployed via the appropriate communication channel
4. Each vessel executes autonomously, reporting results via telemetry
5. The supervisory agent composes results and adapts the plan

**Emergent Behavior:**
Can complex coordination emerge from simple agent-native bytecode? The NEXUS evidence suggests yes, within bounds:

- **Collective sensor fusion:** Multiple vessels each running a simple "report obstacle" reflex, combined at the fleet level, creates a distributed obstacle map far richer than any single vessel's sensors
- **Distributed search pattern:** Simple compass-heading-hold reflexes with offset angles deployed to different vessels create a expanding search pattern without central coordination
- **Load balancing:** The trust score's asymmetric loss function (25:1 ratio) naturally prevents over-reliance on any single vessel: if a vessel fails, its subsystems' trust freezes, and the fleet adapts

However, truly complex emergent behavior (e.g., formation flying, cooperative manipulation) requires more sophisticated inter-agent communication than the current architecture supports. The bytecode ISA's lack of direct inter-agent messaging (no "send to peer" opcode) limits emergence to cases where agents share a common environment but not explicit communication channels.

### 5.3 Consensus Protocols for Fleet Decisions

For decisions that require fleet-wide agreement (e.g., "should the fleet abort the mission?"), NEXUS provides three consensus mechanisms:

| Mechanism | Speed | Fault Tolerance | Use Case |
|-----------|-------|----------------|----------|
| Raft (Jetson cluster) | ~300 ms election | 1-of-3 Jetson failure | Reflex deployment, trust updates |
| CRDT (trust scores) | <1 s convergence | Any number of node failures | Trust score synchronization |
| Hardware kill switch | <1 ms | Software-independent | Emergency stop (physical override) |
| Trust-veto (Ubuntu mechanism) | 1 tick (1 ms) | Requires 3+ nodes in subsystem | Safety policy override |

---

## 6. The Equipment-Vessel Contract

### 6.1 The Interface Layer

The equipment-vessel contract is the formal interface between the runtime environment and the hardware platform. It is defined by the I/O driver interface (`io_driver_interface.h`) which specifies a driver vtable with 7 mandatory functions:

```c
typedef struct {
    int  (*init)(void *config);
    int  (*read)(void *buffer, size_t len);
    int  (*write)(const void *data, size_t len);
    int  (*configure)(const char *key, const char *value);
    int  (*selftest)(void);
    void (*deinit)(void);
    int  (*get_info)(char *buf, size_t len);
} io_driver_vtable_t;
```

This vtable is the **contract** between equipment and vessel. Every hardware driver (I2C sensor, PWM actuator, ADC channel, UART interface) must implement these 7 functions. The equipment runtime interacts with hardware exclusively through this vtable, never through direct register access.

### 6.2 Abstraction While Preserving Capability

The equipment layer abstracts vessel differences while preserving capability through three mechanisms:

1. **Logical Naming:** Pin mappings are resolved at deployment time, not compiled into bytecode. A reflex references "heading" not "I2C bus 0, address 0x1E, register 0x02." The equipment layer maps logical names to physical addresses based on the vessel's `ROLE_ASSIGN` configuration.

2. **Type Normalization:** All sensor values are normalized to float32 in the sensor register file. Whether a temperature sensor reports via I2C (digital), ADC (analog), or UART (NMEA sentence), the bytecode sees a float32 in degrees Celsius.

3. **Capability Advertisement:** The equipment runtime reports what it can and cannot do through the capability descriptor. Agents can query this descriptor and compile bytecodes that only use available capabilities.

### 6.3 Performance Guarantees

The equipment runtime provides the following performance guarantees to agent bytecode:

| Guarantee | Value | Condition |
|-----------|-------|-----------|
| Deterministic execution | Identical inputs → identical outputs | No interrupts during tick, pre-populated sensor registers |
| Bounded execution time | ≤ 10,000 cycles per tick | Cycle counter halts on overflow |
| Bounded memory | ≤ 3 KB static allocation | No heap allocation during execution |
| Actuator safety | Output always within [min, max] | Post-execution clamping |
| No NaN/Inf to actuators | Proven by Theorem 3 | Validator rejects non-finite immediates |
| Sensor validity | All values are finite float32 | Host firmware guarantees isfinite() check |
| Kill switch response | < 1 ms | Hardware interrupt, IRAM code |

### 6.4 Safety Guarantees: When Equipment Cannot Fulfill

When the equipment cannot fulfill a vessel request, the safety system provides layered guarantees:

| Failure Mode | Equipment Response | Vessel Impact |
|-------------|-------------------|---------------|
| Cycle budget exceeded | VM halts, actuators → safe position | Control output frozen at safe values |
| Stack overflow/underflow | VM halts immediately | No actuator update this tick |
| Sensor data stale | Substitute 0.0 (safe default) | Reflexes execute with degraded inputs |
| I2C bus locked | Timeout after 100 ms, report error | Missing sensor data |
| Heartbeat timeout (3 misses) | Enter WARN state, reduce non-essential services | Partial degradation |
| Heartbeat timeout (10 misses) | Enter FAILSAFE, continue loaded reflexes | Autonomous operation |
| Kill switch activated | ISR forces all outputs to safe state | Complete shutdown of actuation |
| Jetson communication loss | Continue executing loaded reflexes autonomously | No new deployments, no trust updates |
| Watchdog timeout (1 s) | Hardware reset to factory firmware | Full reboot, safe provisioning mode |

---

## 7. Concrete Scenarios

### Scenario 1: Agent on Jetson Delegates a Reflex to ESP32 on the Same Vessel

**Context:** The Jetson's AI model generates a new reflex — "When wind exceeds 25 knots, reduce throttle to 40%." This intention must be deployed to the ESP32 that controls the throttle actuator.

**Step-by-Step Execution:**

1. **Intention Generation (Jetson, ~29 seconds):**
   - Qwen2.5-Coder-7B at Q4_K_M generates JSON reflex definition (500 tokens at 17.2 tok/s)
   - Few-shot prompt with 2 examples + GBNF grammar constraints achieves 99.5% schema compliance

2. **Safety Validation (Cloud, ~2-3 seconds):**
   - Claude 3.5 Sonnet validates the reflex (95.1% safety catch rate)
   - Checks: throttle range [0, 80%] (safety rule: never > 80%), ramp rate ≤ 10%/s, min_autonomy_level ≥ 2
   - Result: PASS_WITH_CONDITIONS ("add max_duration: 30.0 safety guard")

3. **Compilation (Jetson, ~6.8 ms):**
   - JSON reflex compiled to 7 bytecode instructions (56 bytes)
   - Compiler validates: stack balance (max depth 2), jump targets, cycle budget (12 cycles), no NaN/Inf immediates
   - WCET verified: 12 cycles × 3 cycles/instruction + pipeline = 51 cycles (well within 10,000 budget)

4. **Deployment (RS-422, ~1.6 ms):**
   - REFLEX_DEPLOY message (type 0x09) sent via COBS-framed RS-422 at 921,600 baud
   - COBS encoding adds 1 byte overhead, CRC-16 computed (2 bytes), 10-byte header
   - Total wire frame: ~80 bytes → 0.87 ms UART time + 0.06 ms processing

5. **Validation (ESP32, <0.1 ms):**
   - ESP32's equipment runtime re-validates bytecode (determinism check, safety invariant check, cycle budget check)
   - Bytecode stored in LittleFS partition (56 bytes, negligible storage)

6. **Activation (ESP32, immediate):**
   - Reflex loaded into execution slot
   - Trust score for engine subsystem checked: T = 0.72, required ≥ 0.40 (L2 threshold)
   - Trust exceeds threshold → reflex activated at configured tick rate (10 Hz)

7. **Execution (ESP32, every 100 ms):**
   - Equipment populates sensor registers: wind_speed = 26.3 m/s
   - VM executes: READ_PIN(wind) → PUSH(25.0) → GT_F → JUMP_IF_FALSE → PUSH(40.0) → WRITE_PIN(throttle) → HALT
   - Actuator clamping: throttle output 40.0 is within [0, 100] → applied directly
   - Execution time: ~44 μs (measured mean)

**Total latency from intention to physical action:** ~32 seconds (29 s generation + 3 s validation + ~0.01 s compilation + deployment + execution)

**Key insight:** The slow part is intention generation and validation (human-speed timescale). The fast part — compilation, deployment, and execution — takes <10 ms (reflex-speed timescale). These two timescales never interfere.

### Scenario 2: Agent on Vessel A Requests Sensor Data from Vessel B

**Context:** Vessel A needs LIDAR data from Vessel B for collision avoidance, but Vessel A has no LIDAR sensor installed.

**Step-by-Step Execution:**

1. **Capability Discovery:**
   - Vessel A's Jetson queries Vessel B's capability descriptor via MQTT
   - Discovers Vessel B has LIDAR with 200m range, 10 Hz update rate

2. **Intention Compilation:**
   - Vessel A's system prompt generates a reflex for Vessel B: "When LIDAR detects obstacle < 30m, emit event with distance and bearing"
   - Bytecode compiled targeting Vessel B's sensor indices (LIDAR mapped to sensor register 12)

3. **Deployment:**
   - REFLEX_DEPLOY sent via MQTT QoS 2 (exactly-once delivery) from Vessel A to Vessel B
   - ~20-80 ms latency over WiFi LAN

4. **Execution on Vessel B:**
   - Reflex runs at 10 Hz on Vessel B's ESP32
   - When obstacle detected: EMIT_EVENT syscall writes to event ring buffer
   - Event is transmitted to Vessel A via MQTT topic `nexus/telemetry/{vessel_b_id}`

5. **Processing on Vessel A:**
   - Vessel A's Jetson subscribes to Vessel B's telemetry topic
   - Receives obstacle events with distance and bearing
   - Updates Vessel A's world model
   - May deploy an evasive maneuver reflex to Vessel A's own ESP32

**Limitation:** The ~20-80 ms MQTT latency is too slow for real-time collision avoidance (which requires <50 ms response). This scenario works for slow-moving vessels or long-range obstacle detection (>100m), but not for high-speed close-proximity operations. For those cases, direct RS-422 serial links between vessels would be needed.

### Scenario 3: Fleet of 10 Vessels — Agents Negotiate Task Allocation

**Context:** A fleet of 10 autonomous marine vessels must search a 10 km² area. Each vessel has different sensor capabilities and battery levels.

**Step-by-Step Execution:**

1. **Fleet Leader Election:**
   - 3 Jetson clusters (vessels 1, 5, 10) run Raft consensus
   - Vessel 1 elected leader (highest Jetson ID)
   - Leader has quorum (vessels 1 + 5 = 2 of 3)

2. **Capability Aggregation:**
   - Leader requests capability descriptors from all 10 vessels
   - Builds fleet capability map:
     - Vessels 1-3: Full sensor suite (GPS RTK, LIDAR, radar), 90% battery
     - Vessels 4-6: Basic sensors (GPS, compass), 75% battery
     - Vessels 7-8: Minimal sensors (GPS only), 50% battery
     - Vessels 9-10: Enhanced sensors (side-scan sonar), 95% battery

3. **Task Decomposition:**
   - Leader's system prompt decomposes search area into 10 sectors
   - Assigns sectors based on capability matching:
     - Vessels 9-10 (sonar): Near-shore shallow sectors
     - Vessels 1-3 (full sensors): Deep-water sectors with obstacle risk
     - Vessels 4-6 (basic): Open-water sectors with simple navigation
     - Vessels 7-8 (minimal): Perimeter patrol (simple patterns)

4. **Intention Deployment:**
   - Leader compiles sector-specific navigation reflexes for each vessel
   - Each reflex includes: GPS waypoints, search pattern (lawnmower/spiral), speed limits, battery-conservation thresholds
   - Deployed via MQTT QoS 2 to each vessel's Jetson

5. **Autonomous Execution:**
   - Each vessel executes its search pattern independently
   - Telemetry reported to fleet leader via MQTT QoS 0 (loss acceptable)
   - If a vessel encounters an obstacle, it deploys an avoidance reflex locally

6. **Dynamic Rebalancing:**
   - Fleet leader monitors battery levels and search progress
   - If vessel 8's battery drops below 30%, leader reassigns its sector to vessel 4
   - New reflex deployed to vessel 4 with updated waypoints

7. **Consensus on Mission Completion:**
   - When all sectors searched, each vessel reports completion
   - Leader aggregates results (using CRDT merge for consistency)
   - Leader proposes mission-end; 2-of-3 Jetson clusters ACK → fleet stands down

### Scenario 4: Vessel Loses GPS — Agents Reconfigure Bytecode to Use Dead Reckoning

**Context:** A marine vessel's GPS module fails (no satellite fix for > 30 seconds). The agent must reconfigure its navigation reflexes to use IMU dead reckoning.

**Step-by-Step Execution:**

1. **Failure Detection (Equipment, <500 ms):**
   - GPS sensor register becomes stale (> 500 ms without update)
   - Equipment runtime substitutes 0.0 for GPS position and heading
   - Stale data event written to event ring buffer
   - SAFETY_EVENT message sent to Jetson: "GPS_DATA_STALE"

2. **Trust Impact (Equipment, immediate):**
   - Navigation subsystem trust score frozen (no updates while sensor is degraded)
   - If trust was at L4 (conditional autonomy), navigation reflexes continue but at frozen trust level
   - If trust was at L2 (semi-auto), system may require human confirmation for continued operation

3. **Degraded Reflex Deployment (Jetson, ~29 seconds):**
   - Jetson receives GPS failure notification
   - System prompt generates a degraded navigation reflex:
     ```json
     {
       "name": "dead_reckoning_nav",
       "sensors": {
         "imu_accel_x": {"pin": 4, "type": "float32"},
         "imu_gyro_z": {"pin": 6, "type": "float32"},
         "compass_heading": {"pin": 0, "type": "float32"}
       },
       "actuators": {
         "rudder": {"pin": 0, "min": -30, "max": 30, "safe": 0},
         "throttle": {"pin": 1, "min": 0, "max": 50, "safe": 0}
       },
       "code": "... compass_heading_hold_with_drift_compensation ..."
     }
     ```
   - Note: throttle limited to 50% (reduced speed for dead reckoning accuracy)
   - Safety validator adds constraint: max_duration 300 seconds (dead reckoning drift limits)

4. **Deployment and Execution:**
   - Degraded reflex deployed to ESP32 via REFLEX_DEPLOY
   - Old GPS-dependent reflex remains loaded but its sensor inputs are stale (0.0)
   - Equipment runtime executes both reflexes; degraded reflex takes priority (higher priority number) for actuator writes
   - Dead reckoning provides position estimates with ~2% drift per minute

5. **Recovery:**
   - When GPS recovers, fresh data flows into sensor registers
   - Equipment runtime detects valid GPS data (non-zero position)
   - GPS-dependent reflex resumes normal operation
   - Navigation trust score resumes updating
   - Degraded reflex automatically deactivates (its max_duration safety guard expires)

### Scenario 5: New Vessel Joins Fleet — Agents Bootstrap Its Equipment and Deploy Initial Bytecode

**Context:** A new vessel (Vessel D) arrives at the fleet's operational area. It must be integrated into the fleet without human intervention.

**Step-by-Step Execution:**

1. **Physical Connection (Human, ~5 minutes):**
   - New vessel powered on
   - ESP32 nodes boot and send DEVICE_IDENTITY on RS-422
   - Jetson detects new nodes via serial port enumeration

2. **Auto-Detection (Equipment, <1 second):**
   - New vessel's ESP32s send AUTO_DETECT_RESULT: I2C scan reveals connected sensors
   - SELFTEST_RESULT confirms pin continuity and CRC verification
   - Jetson's NodeDiscovery.ListNodes() reports new vessel's nodes

3. **Role Assignment (Jetson, <500 ms):**
   - Fleet leader queries new vessel's capability descriptor
   - Determines vessel class (e.g., "cognitive light" with 4 ESP32s, 1 Jetson)
   - Sends ROLE_ASSIGN to each ESP32 with appropriate pin mappings
   - Roles assigned based on detected sensors: "navigation_controller", "engine_monitor", "environmental_sensor", "safety_monitor"

4. **Firmware Verification (Jetson, <5 seconds):**
   - Fleet leader compares new vessel's firmware hash against known-good hash
   - If firmware is outdated, OTA update initiated via FIRMWARE_UPDATE_START/CHUNK/END
   - Update size: ~1 MB, transfer time: ~11.4 seconds at 921,600 baud
   - SHA-256 hash verification on completion
   - Probation period: 60 seconds of health monitoring before acceptance

5. **Fleet Integration (Fleet Leader, ~30 seconds):**
   - Fleet leader generates initial reflexes for new vessel based on its capabilities:
     - Standard navigation hold reflex (heading + speed)
     - Safety monitoring reflex (heartbeat, overcurrent, kill switch)
     - Fleet communication reflex (obstacle reporting, position telemetry)
   - Each reflex compiled targeting new vessel's specific pin mappings
   - Safety validation performed by cloud validator (or local Phi-3-mini if cloud unavailable)

6. **Trust Bootstrap:**
   - New vessel starts with trust score T = 0.20 (L1 — Assisted) for all subsystems
   - This is the decay branch's stable fixed point — the floor below which trust cannot fall
   - Fleet leader deploys reflexes with min_autonomy_level = 1 (consistent with L1)
   - As the new vessel operates successfully, trust accumulates: ~7 days to L2, ~26 days to L3

7. **Operational Integration:**
   - New vessel begins reporting telemetry to fleet via MQTT
   - Fleet leader includes new vessel in task allocation
   - CRDT trust merge incorporates new vessel's trust scores into fleet-wide state
   - Full integration complete within ~1 minute of physical connection

---

## 8. Conclusions and Open Questions

### 8.1 Key Findings

1. **The bytecode ISA is the universal language of A2A communication.** Its 32 opcodes, fixed 8-byte instruction format, and provable determinism make it the ideal medium for expressing intentions that any agent on any vessel can execute.

2. **Equipment is the critical abstraction layer.** It sits between the agent's intention (bytecode) and the vessel's hardware (silicon), providing sensor normalization, actuator safety, resource management, and communication — all without requiring the agent to know the hardware details.

3. **The vessel capability descriptor enables compile-time adaptation.** Agents can query a vessel's capabilities before compiling bytecode, ensuring that deployed intentions only use available hardware resources.

4. **Trust-gated activation prevents premature autonomy.** A newly deployed reflex cannot activate until the relevant subsystem's trust score exceeds the reflex's minimum autonomy level. This ensures that untested intentions cannot cause harm.

5. **The ribosome architecture provides remarkable resilience.** ESP32 nodes continue executing their current reflex bytecode autonomously during Jetson communication loss. The system achieves 99.97% availability across 10,000-hour simulations.

6. **Cross-vessel delegation is possible but latency-constrained.** MQTT-based cross-vessel coordination introduces 20–80 ms latency, suitable for strategic coordination but not for real-time reflex control.

7. **Graceful degradation is built into every layer.** From sensor failure (substitute 0.0) to Jetson failure (autonomous reflex continuation) to complete communication loss (FAILSAFE with loaded reflexes), the system degrades without failing catastrophically.

### 8.2 Open Questions for Future Research

1. **Direct inter-agent bytecode messaging:** Should the ISA include a "SEND_TO_PEER" opcode for direct reflex-to-reflex communication? This would enable tighter coordination but could violate the VM's determinism guarantee.

2. **Emergent coordination from simple reflexes:** Can sophisticated fleet behaviors (formation flying, cooperative manipulation) emerge from simple individual reflexes without explicit inter-agent messaging? What is the theoretical limit?

3. **Cross-vessel safety policy synchronization:** When two vessels with different domain-specific safety policies (e.g., marine vs. mining) cooperate, how are policy conflicts resolved?

4. **Quantum-resistant firmware signing:** The current firmware update mechanism uses SHA-256. Should it be upgraded to post-quantum signatures for long-lived deployments?

5. **Formal verification of multi-agent interactions:** Can model checking verify the safety of fleet-level coordination protocols where individual agents are verified but their interactions are not?

6. **Adaptive equipment runtime:** Should the equipment runtime adapt its resource allocation (cycle budget, memory, I/O bandwidth) based on observed agent behavior, or should it be statically configured?

7. **Vessel-to-vessel bytecode portability metrics:** How can we measure the "portability distance" between two vessels — the minimum modification needed to run the same bytecode on both?

---

*This document synthesizes findings from seven major NEXUS research deliverables spanning five rounds of iterative design work. It represents the deep research of Task Agent 4, focused on the agent communication model and runtime environment for A2A-native programming in the NEXUS platform.*
