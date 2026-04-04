# Building with Artifact Swarm Intelligence: A Practical Developer Guide

**Document ID:** NEXUS-COLONY-P2-009  
**Phase:** 4A — Developer Documentation  
**Author:** Agent-4A, Senior Developer Advocate  
**Date:** 2026-03-30  
**Status:** Release Candidate  
**Mandate:** Teach developers how to BUILD with the Artifact Swarm Intelligence framework — from first hardware connection to advanced evolutionary patterns.  

---

## 1. Getting Started

### 1.1 Hardware Requirements

You need three hardware components to form a minimal colony:

| Component | Part | Role | Approximate Cost |
|-----------|------|------|------------------|
| **Worker Node** | ESP32-S3 with 8MB PSRAM (e.g., Adafruit ESP32-S3 Feather) | Executes evolved bytecodes; reads sensors, drives actuators | $5–15 |
| **Queen Bee** | Nvidia Jetson Orin Nano Super Developer Kit | Runs AI model; generates bytecode variants; performs Bayesian optimization | $250–500 |
| **Backbone** | RS-422 transceiver modules (MAX485) + shielded twisted pair | Connects Jetson to ESP32 nodes; carries telemetry and bytecode OTA | $5 per node |

Additional parts per node: sensors (BME280, MPU6050, etc.), actuators (servos, relays, MOSFET drivers), 12V power supply with per-node 2A fusing, and IP65 enclosures with cable glands.

The ESP32-S3's flash is partitioned into 13 fixed regions. The partition that matters for evolution is `reflex_bc` — a 1MB LittleFS partition that stores up to 7 evolved bytecode genomes per node. At typical evolution rates (1–2 bytecode updates per week), the 100K flash erase cycles give approximately 1,000 years of operational life.

### 1.2 Software Setup

On the **Jetson** (Ubuntu 22.04 with JetPack 6.x):

```bash
# Clone the NEXUS colony framework
git clone https://github.com/nexus-colony/queen-bee.git /opt/nexus-queen
cd /opt/nexus-queen

# Install Python dependencies for the evolutionary pipeline
pip3 install -r requirements.txt
# Key packages: scikit-learn (Bayesian optimization), z3-solver (SMT verification),
#   llama-cpp-python (INT4 quantized LLM inference)

# Flash the queen bee model (DeepSeek-Coder-7B, Q4 quantized)
python3 download_model.py --model deepseek-coder-7b-instruct --quant q4
```

On the **ESP32** (ESP-IDF v5.x):

```bash
# Clone the colony firmware (universal — same binary for all nodes)
git clone https://github.com/nexus-colony/worker-firmware.git
cd worker-firmware

# Configure target (the firmware auto-detects pin configuration from NVS)
idf.py set-target esp32s3
idf.py -p /dev/ttyUSB0 -b 921600 flash monitor
```

The universal firmware is the "ribosome" — a fixed 12KB binary containing the Reflex VM (32-opcode bytecode interpreter), the Hardware Abstraction Layer, the four-tier safety system, and the RS-422 telemetry stack. It never changes. All behavioral evolution happens through the bytecodes that the VM interprets.

### 1.3 First Deployment: The Temperature-Controlled Fan

Your first colony system: a temperature sensor (BME280) and a PWM fan controlled by an evolved PID reflex. This is the "hello world" of colony computing — you'll watch a bytecode evolve its own PID gains in real time.

**Wiring:**

| ESP32 Pin | BME280 | RS-422 MAX485 | Fan MOSFET |
|-----------|--------|---------------|-------------|
| GPIO 8 (I2C SDA) | SDA | — | — |
| GPIO 9 (I2C SCL) | SCL | — | — |
| GPIO 43 (UART0 TX) | — | DI | — |
| GPIO 44 (UART0 RX) | — | RO | — |
| GPIO 6 (PWM) | — | — | Gate |

**Send the pin configuration JSON to the ESP32 via the initial provisioning tool:**

```json
{
  "node_id": 1,
  "colony_id": "dev-colony-001",
  "pins": {
    "i2c_sda": 8, "i2c_scl": 9,
    "uart_tx": 43, "uart_rx": 44,
    "pwm_channels": [{"pin": 6, "freq_hz": 25000, "safe_duty": 0}],
    "kill_switch": 0
  },
  "sensors": [
    {"name": "bme280", "bus": "i2c", "addr": 0x76, "type": "temperature_humidity_pressure"}
  ],
  "actuators": [
    {"name": "fan", "type": "pwm", "channel": 0, "min_duty": 0.0, "max_duty": 1.0, "rate_limit_per_sec": 0.1}
  ]
}
```

**Deploy the seed reflex (the initial, unevolved bytecode) from the Jetson:**

```bash
nexus-cli deploy-reflex \
  --node 1 \
  --json reflex_temperature_fan.json
```

Where `reflex_temperature_fan.json` is:

```json
{
  "name": "temperature_hold",
  "sensors": ["bme280.temperature_celsius"],
  "actuators": ["fan"],
  "variables": [
    {"name": "target_temp", "init": 22.0},
    {"name": "current_temp", "init": 22.0}
  ],
  "pid_controllers": [
    {
      "index": 0,
      "kp": 1.5, "ki": 0.1, "kd": 0.3,
      "integral_limit": 50.0,
      "output_min": 0.0, "output_max": 1.0
    }
  ],
  "code": [
    "READ_PIN 0",
    "WRITE_PIN 64",
    "PUSH_F32 22.0",
    "READ_PIN 64",
    "SWAP",
    "NOP 0x80 0x02 0x0000",
    "CLAMP_F 0.0 1.0",
    "WRITE_PIN 0",
    "NOP 0x80 0x01 0x0000"
  ]
}
```

This seed reflex reads the BME280 temperature, runs PID controller 0 (targeting 22.0°C), clamps the output to [0.0, 1.0], and writes it to the fan PWM. It works — but it's generic. Over the next few hours, the colony will evolve the PID gains (Kp, Ki, Kd) to match the thermal characteristics of your specific room, fan, and sensor placement.

**Watch evolution happen:**

```bash
# Open the colony dashboard (default: http://jetson-ip:8080)
# You'll see:
#   - Generation counter incrementing
#   - Kp/Ki/Kd values shifting
#   - Fitness score climbing
#   - Temperature settling time decreasing
```

Within 20–40 minutes of Nelder-Mead simplex optimization running on the ESP32 (using only 64 bytes of SRAM), followed by Bayesian Optimization on the Jetson (30–80 evaluations at 30 minutes each), the colony will converge on gains that are specifically tuned for your thermal environment. A bytecode that started at 22°C setpoint overshoot will evolve to achieve ±0.3°C stability with 30% less fan cycling than the seed.

---

## 2. Defining Your Colony

### 2.1 Colony, Pod, Organ, Node

The colony hierarchy maps to physical topology:

- **Colony** = one Jetson + all its ESP32 nodes (typically 5–20 nodes)
- **Pod** = a functional subsystem (navigation pod: rudder + compass + IMU; propulsion pod: throttle + fuel + temperature)
- **Organ** = a logical group of pods (steering organ = navigation + propulsion)
- **Node** = one ESP32-S3 with its sensors and actuators

### 2.2 Node Roles

Each node is assigned a role in the `nexus_cfg` NVS partition at provisioning time:

| Role | Sensors | Actuators | Typical Bytecode Size | Example |
|------|---------|-----------|----------------------|---------|
| **Sensor** | 1–4 sensors | None | 4–6 KB | BME280 weather station |
| **Actuator** | 0–2 feedback sensors | 1–3 actuators | 8–12 KB | Servo with encoder feedback |
| **Hybrid** | 2–6 sensors | 1–4 actuators | 12–18 KB | Rudder controller with IMU |

The role determines the bytecode's structure — sensor nodes have short bytecodes (read, filter, report); hybrid nodes have longer bytecodes (read, compute PID, clamp, write, emit telemetry).

### 2.3 Example: Marine Autopilot Colony Configuration

```yaml
# colony_config.yaml — Vessel NEXUS-017, a 12-meter research vessel
colony:
  id: "nexus-017"
  queen: "jetson-orin-nano"
  season: "summer"             # Current evolutionary phase
  seasonal_schedule:
    spring:  { start_month: 3, start_day: 1,  duration_days: 28 }
    summer:  { start_month: 4, start_day: 1,  duration_days: 56 }
    autumn:  { start_month: 6, start_day: 1,  duration_days: 28 }
    winter:  { start_month: 7, start_day: 1,  duration_days: 28 }

  pods:
    - name: navigation
      nodes:
        - id: 1
          role: hybrid
          sensors: [hmc5883l.compass, mpu6050.imu, bme280.temp]
          actuators: [rudder_servo]
          niche: heading_hold
          portfolio_size: 7       # calm/moderate/rough/dock/storm/emergency/reserve
        - id: 2
          role: hybrid
          sensors: [ina219.engine_current, ina219.engine_voltage]
          actuators: [throttle_actuator]
          niche: speed_control
    - name: environment
      nodes:
        - id: 3
          role: hybrid
          sensors: [mpu6050.accel_z, mpu6050.gyro_y]
          actuators: [trim_tab_servo]
          niche: ride_comfort
        - id: 4
          role: actuator
          sensors: [bme280.humidity]  # bilge level proxy
          actuators: [bilge_pump_relay]
          niche: bilge_management

  evolution:
    fitness_function:
      weights:
        accuracy: 0.4
        latency: 0.3
        efficiency: 0.2
        comfort: 0.1
      safety_multiplier: true     # Zero fitness on any safety regression
    diversity:
      min_lineages: 5
      max_genomes_per_niche: 7
      reserve_pool_size: 2
    seasonal:
      spring:  { mutation_rate: 0.30, crossover_rate: 0.15, epsilon: 0.30 }
      summer:  { mutation_rate: 0.10, crossover_rate: 0.05, epsilon: 0.10 }
      autumn:  { mutation_rate: 0.05, crossover_rate: 0.02, epsilon: 0.05 }
      winter:  { mutation_rate: 0.00, crossover_rate: 0.00, epsilon: 0.00 }

  safety:
    kill_switch_pin: 0            # GPIO 0 with external pull-up
    max_rudder_rate: 60.0         # degrees/second
    max_throttle_rate: 10.0        # percent/second
    lyapunov_required: true        # All Level 1-2 mutations need stability cert
```

---

## 3. Writing Reflex Bytecodes (The "Genome")

### 3.1 The JSON Reflex Format

The compiler translates high-level JSON reflex definitions into 8-byte bytecode instructions. You write bytecodes in JSON; evolution modifies them in bytecode. Here is the complete schema:

```json
{
  "name": "heading_hold_rough",
  "version": "1.2.0",
  "sensors": ["hmc5883l.heading_deg", "mpu6050.rate_gyro_z"],
  "actuators": ["rudder_servo"],
  "variables": [
    {"name": "heading_error", "init": 0.0},
    {"name": "rate_of_turn",  "init": 0.0},
    {"name": "prev_error",    "init": 0.0}
  ],
  "pid_controllers": [
    {
      "index": 0,
      "kp": 2.8,
      "ki": 0.15,
      "kd": 1.2,
      "integral_limit": 100.0,
      "output_min": -1.0,
      "output_max": 1.0
    },
    {
      "index": 1,
      "kp": 0.5,
      "ki": 0.0,
      "kd": 0.8,
      "integral_limit": 50.0,
      "output_min": -0.5,
      "output_max": 0.5
    }
  ],
  "code": [
    "READ_PIN 0",
    "WRITE_PIN 64",
    "READ_PIN 1",
    "WRITE_PIN 65",
    "READ_PIN 64",
    "READ_PIN 65",
    "SUB_F",
    "NOP 0x80 0x02 0x0000",
    "CLAMP_F -1.0 1.0",
    "WRITE_PIN 0",
    "NOP 0x80 0x01 0x0000"
  ]
}
```

### 3.2 Understanding the 32-Opcode ISA

The bytecode VM is a stack machine with exactly 32 opcodes encoded in 8-byte fixed instructions:

```
Byte layout: [OPCODE:1][FLAGS:1][OPERAND1:2][OPERAND2:4]

Stack operations:  NOP, PUSH_I8, PUSH_I16, PUSH_F32, POP, DUP, SWAP, ROT
Arithmetic:      ADD_F, SUB_F, MUL_F, DIV_F, NEG_F, ABS_F, MIN_F, MAX_F, CLAMP_F
Comparison:      EQ_F, LT_F, GT_F, LTE_F, GTE_F
Logic:           AND_B, OR_B, XOR_B, NOT_B
I/O:             READ_PIN, WRITE_PIN, READ_TIMER_MS
Control:         JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE
Syscalls:        NOP with flags=0x80 (HALT, PID_COMPUTE, RECORD_SNAPSHOT, EMIT_EVENT)
```

Variable access uses `READ_PIN`/`WRITE_PIN` with operand1 >= 64 (operand1 - 64 = variable index). PID computation uses the syscall `NOP 0x80 0x02 0x0000` which pops setpoint and process variable from the stack, computes the PID output, and pushes the result.

### 3.3 Best Practices

1. **Keep bytecodes small.** The Kolmogorov fitness function (`behavioral_score / compressed_binary_size`) explicitly rewards smaller bytecodes. A typical evolved bytecode is 8–12KB (1,000–1,500 instructions). Anything above 20KB triggers the complexity debt penalty.

2. **Use PID_COMPUTE for all control loops.** Never implement PID manually with ADD_F/SUB_F/MUL_F — the syscall version includes anti-windup, output clamping, and derivative filtering that manual implementations miss.

3. **Avoid deep branching.** The ISA has no loop construct. Use state machines instead: SET_STATE / GET_STATE (via VAR_0) with a JUMP table. Evolution handles branching well (Level 2 mutations), but deeply nested conditions reduce the Kolmogorov fitness score.

4. **Always CLAMP_F outputs.** Even though the safety system enforces actuator limits, clamping in bytecode prevents the VM from wasting cycles computing values that will be clipped anyway. Use the actuator's physical limits as the clamp bounds.

5. **Emit events for telemetry.** Use `NOP 0x80 0x04 event_id event_data` to emit structured telemetry events. These feed the pattern discovery engine on the Jetson and appear in the Griot narrative layer.

---

## 4. Setting Up Evolution

### 4.1 Configuring the Fitness Function

The master fitness function is:

```
colony_fitness(v) = α·F_immediate(v) + β·F_heritability(v) + γ·F_adaptability(v) + δ·F_reversible(v) - ε·Debt(v)

if safety_regression(v, baseline) > threshold:
    colony_fitness(v) = 0   # Non-negotiable
```

For your domain, configure the F_immediate weights:

```yaml
# fitness_config.yaml
fitness:
  immediate:
    weights:
      accuracy: 0.4      # RMSE vs setpoint
      latency: 0.3        # p99 response time
      efficiency: 0.2      # Resource consumption per unit task
      comfort: 0.1         # Smoothness of actuator motion
  safety:
    regression_threshold: 0.0   # ANY regression zeroes fitness
    lyapunov_required: true
  kolmogorov:
    enabled: true              # Penalize large bytecodes
  debt:
    storage_ceiling: 0.85
    memory_ceiling: 0.75
    max_new_dependencies: 3
    min_lineages: 5
    max_complexity_ratio: 1.5
```

### 4.2 Setting Seasonal Parameters

Evolution oscillates through four phases, each mapped to specific ML techniques:

| Season | Duration | Mutation Rate | Exploration (ε) | Primary Technique |
|--------|----------|---------------|------------------|-------------------|
| **Spring** | 1–2 weeks | 30% | 30% | AI generates diverse variants; UCB Bayesian exploration |
| **Summer** | 2–4 weeks | 10% | 10% | EI Bayesian optimization; Nelder-Mead on-device tuning |
| **Autumn** | 1–2 weeks | 5% | 5% | Pruning, compression, debt repayment, portfolio consolidation |
| **Winter** | 1–2 weeks | 0% | 0% | No evolution. Offline model fine-tuning. Winter Report generated |

Winter is constitutionally mandated — you cannot disable it. This is the Native American Seven Generations principle encoded in software: the colony must rest, analyze, and prepare before its next cycle of growth.

### 4.3 Safety Constraints

Three layers protect the colony:

**Layer 1 (Hardware — Gye Nyame):** Kill switch on GPIO 0 with external pull-up. Triggers safety ISR in IRAM in <1µs. Cannot be overridden by any bytecode, any AI decision, or any human override command. This is the "there is a power greater than all control" boundary.

**Layer 2 (Firmware — Lyapunov):** Every Level 1–2 variant must pass a Lyapunov stability certificate before deployment. The Jetson solves the continuous-time algebraic Riccati equation in <100ms for a SISO PID loop. If the certificate fails, the variant is rejected — it is never loaded onto the ESP32.

**Layer 3 (Evolutionary — Nomos):** The safety multiplier in the fitness function means any variant with a safety regression receives zero fitness regardless of performance. The system does not negotiate with safety; it enforces it.

### 4.4 Example: Evolving an Energy-Efficient Climate Strategy

Configure the colony to optimize for energy efficiency during Summer:

```bash
# Shift fitness weights toward efficiency
nexus-cli set-fitness-weights --accuracy 0.3 --efficiency 0.4 --comfort 0.2 --latency 0.1

# Set seasonal intent (natural language guidance to the AI queen)
nexus-cli set-intent "Focus on minimizing pump cycling frequency while maintaining temperature within ±1°C of setpoint. Prioritize strategies that reduce actuator wear."

# Trigger Summer phase manually (normally auto-scheduled)
nexus-cli set-season summer
```

Over 2–4 weeks of Summer exploitation, the colony will discover strategies such as: longer fan coast-down periods, predictive pre-cooling based on temperature trends, and deadband widening in stable conditions. Each strategy is tested via A/B comparison against the incumbent bytecode, with statistical significance assessed using sequential probability ratio testing (minimum N ≈ 4,950 ticks at 100Hz for a 5% effect detection).

---

## 5. Monitoring and Managing the Colony

### 5.1 The Colony Dashboard

Access the dashboard at `http://<jetson-ip>:8080`. Key views:

- **Node Status:** Real-time view of all nodes, their active genomes, fitness scores, and VM tick times (typically 280–520µs). Green = healthy, Yellow = degraded (Jetson disconnected), Red = safe-state triggered.
- **Genealogy Browser:** Click any variant to see its full lineage tree — parent hashes, mutation descriptions, environmental conditions at birth, and fitness trajectory over time.
- **Seasonal Calendar:** Visual timeline showing current season, days remaining, and seasonal transition history.
- **Fitness Leaderboard:** Ranked table of all active variants with composite fitness scores, condition-normalized rankings, and Ubuntu coefficients.

### 5.2 Key Health Metrics

- **Apeiron Index** (0.0–1.0): Colony diversity health. Combines behavioral entropy (Shannon H), lineage count (must be ≥ 5), and exploration coverage. When this drops below 0.6, the colony triggers a "diversity recovery" mini-Spring regardless of the current season.
- **Wu Wei Score** (0.0–1.0): Measures how little intervention the colony requires. High scores mean evolution is self-directed; low scores mean the human elder is frequently overriding decisions.
- **Kolmogorov Fitness:** `behavioral_score / compressed_binary_size`. A bytecode that achieves 0.92 accuracy in 8KB is fitter than one that achieves 0.95 in 20KB. Evolution actively compresses bytecodes over generations.
- **Generational Debt:** Cumulative cost of consumed resources (storage fraction, memory usage, complexity ratio, dependencies introduced). Debt above any category ceiling prevents variant deployment. Autumn consolidation is the debt repayment cycle.

### 5.3 Intervention: Override, Retire, Inject

```bash
# Override evolution — retire current variant, promote a specific ancestor
nexus-cli promote --node 1 --variant-hash a3f2b8c1 --reason "Manual: operator observed oscillation in harbor"

# Inject a new seed variant (for example, after hardware change)
nexus-cli inject-reflex --node 1 --json new_heading_hold.json --mutation-level 3

# Trigger manual season transition
nexus-cli transition-season autumn --reason "Early consolidation after successful adaptation"

# Roll back to last known-good bytecode
nexus-cli rollback --node 1 --to last-stable
```

---

## 6. Advanced Patterns

### 6.1 Conditional Genetics: Multi-Genome Portfolios

Each node maintains a portfolio of up to 7 bytecodes for different environmental conditions. The switching is sensor-driven, not code-driven:

```json
{
  "portfolio_index": {
    "genomes": [
      {"file": "reflex_calm.rbc",   "condition": {"sensor": "wave_height_m", "max": 0.5, "fallback": true}},
      {"file": "reflex_moderate.rbc","condition": {"sensor": "wave_height_m", "min": 0.5, "max": 2.5}},
      {"file": "reflex_rough.rbc",  "condition": {"sensor": "wave_height_m", "min": 2.5}},
      {"file": "reflex_dock.rbc",   "condition": {"type": "manual", "trigger": "operator_docking_mode"}}
    ],
    "emergency": "reflex_safe.rbc"
  }
}
```

Switching latency is <1ms: HAL evaluates conditions, LittleFS reads the new bytecode, VM validates and reinitializes. PID state resets on switch (prevents integral windup), but variables persist.

### 6.2 Cross-Node Learning

When a variant proves successful on one node, the Jetson automatically offers it to peer nodes running the same niche:

```bash
# Enable cross-node sharing (on by default)
nexus-cli config --cross-node-adoption true

# View adoption rates
nexus-cli adoption-report
# Node 1 (rudder): variant R-Alpha adopted by 6/8 peers
# Node 4 (bilge):  variant B-47 adopted by 2/3 peers (bilge geometries differ)
```

### 6.3 Custom Mutation Operators

You can define domain-specific mutation strategies that override the default hybrid gradient descent + Bayesian optimization:

```python
# custom_mutations.py — inject into queen bee pipeline
from nexus_evolution import MutationOperator

class MarineWeatherMutator(MutationOperator):
    """Adjusts gains based on sea state forecast, not just current conditions."""
    
    def mutate(self, parent_bytecode, weather_forecast):
        if weather_forecast.sea_state_trend == "rising":
            # Preemptively increase derivative damping before conditions worsen
            bytecode = parent_bytecode.copy()
            bytecode.pid[0].Kd *= 1.15  # 15% more derivative
            bytecode.pid[0].Kp *= 0.95  # 5% less proportional
            return bytecode
        return parent_bytecode
```

### 6.4 Hybrid Lamarckian-Darwinian Evolution

The colony is fundamentally Lamarckian — telemetry from real-world operation directly informs bytecode synthesis. But you can tune the epsilon-exploration rate to inject Darwinian randomness:

```yaml
evolution:
  lamarkian_weight: 0.85    # 85% of mutations are gradient-directed (Lamarckian)
  darwinian_weight: 0.15    # 15% are random exploration (Darwinian)
  darwinian_epsilon_max: 0.10  # Maximum noise added to parameter proposals
```

During Spring, the Darwinian weight increases to 0.30 to ensure the colony explores novel regions. During Summer, it drops to 0.05 as the colony exploits known-good regions.

---

## 7. Troubleshooting

### 7.1 Common Pitfalls

| Problem | Cause | Solution |
|---------|-------|---------|
| All variants score 0 fitness | Safety regression detected | Check Lyapunov certificate; verify actuator limits; review recent environmental changes |
| Fitness plateaus for 3+ cycles | Evolution exhausted search space | Trigger diversity recovery; inject random variants; consider Level 3 algorithm replacement |
| VM halts repeatedly | Bytecode validation failure | Check stack depth (<256), jump alignment (8-byte), PID index range (0–7) |
| Excessive actuator oscillation | Derivative gain too low for conditions | Increase exploration epsilon; check if conditions have shifted beyond portfolio coverage |
| Flash wear warning | Storage debt near ceiling | Trigger Autumn consolidation; archive old variants; compress bytecodes |

### 7.2 Debugging Evolved Bytecodes

The colony provides two debugging tools:

**Flight Recorder:** Each bytecode carries a snapshot ring buffer (16 snapshots × 128 bytes = 2KB). Use `RECORD_SNAPSHOT` in your bytecodes to capture state at critical points. Replay on the Jetson:

```bash
nexus-cli replay --node 1 --variant-hash a3f2b8c1 --ticks 1000-1100
```

**Behavioral Fingerprinting:** The Jetson computes a 128-byte fingerprint vector for each variant by running it through 32 standardized test scenarios (step input, sine wave, noise, etc.). Compare fingerprints to detect behavioral drift:

```bash
nexus-cli fingerprint-diff --variant-a a3f2b8c1 --variant-b e7d4c6a9
# Euclidean distance: 0.23 (similar — same lineage)
# vs. baseline: 1.87 (significantly different — new adaptation)
```

### 7.3 Aporia Mode

When ALL active variants for a niche simultaneously drop below the minimum viability threshold (fitness < 0.3), the colony enters **Aporia Mode** — the Greek state of puzzlement. This means the environment has changed beyond the gene pool's capacity.

The colony's automated response:
1. Freeze all variants except the last known-good safety baseline
2. Generate 10–15 new candidates with 50% random exploration
3. Run rapid 6-hour competition rounds with relaxed statistical thresholds
4. Promote the first candidate that achieves fitness > 0.5

```bash
# Check if colony is in Aporia Mode
nexus-cli status | grep aporia
# aporia: true (since 2026-06-15T14:23:00Z, duration: 4h 12m)
# emergency_variants_generated: 13
# best_emergency_fitness: 0.47 (below promotion threshold)
```

### 7.4 Performance Tuning

- **VM tick budget:** Default 1000µs at 100Hz (10ms period). If bytecodes are timing out, reduce the tick budget or move complex computations to subroutines (CALL/RET).
- **Serial bandwidth:** RS-422 at 921,600 baud = ~870 KB/s raw, ~60 KB/s effective. A 12KB bytecode transfers in ~0.09 seconds. With 20 nodes, the Jetson can update all nodes in under 2 seconds.
- **Jetson VRAM:** Budget 3.8GB for the queen bee model (DeepSeek-Coder-7B Q4), 2.2GB for the auxiliary model (Phi-3-mini Q4), and ~2GB for BO, telemetry, and OS. Monitor with `nvidia-smi`.

---

## 8. The Human-in-the-Loop Workflow

### 8.1 The Elder's Daily Routine

The Gardener's Covenant defines the human operator's role. A typical daily interaction takes 5–10 minutes:

**Morning check-in (3 minutes):**
```bash
nexus-cli overnight-report
# "Overnight: 3 variants promoted across 2 nodes.
#  Rudder heading RMS improved 0.8° → 0.6° in moderate seas.
#  Throttle variant T-47 retired — 18% higher fuel consumption than baseline.
#  Apeiron Index: 0.72 (healthy). No safety events."

nexus-cli approve --all    # Approve overnight promotions
```

**Midday assessment (2 minutes):**
```bash
nexus-cli anomaly-report
# "Bilge pump cycling frequency increased 15% over baseline.
#  Investigation: hull joint gap widening due to vessel age.
#  Recommended: Level 4 architecture mutation — add flow-rate sensor.
#  Colony has already generated the hardware proposal."
```

**Evening decision (5 minutes):**
```bash
# Set intent for overnight evolution
nexus-cli set-intent "Sea state forecast rising to 4 tomorrow. Prioritize rough-weather stability. Do not sacrifice fuel efficiency more than 10%."

# Review the Griot narrative for the day
nexus-cli griot-summary --day today
# "Generation 413 improved heading hold by detecting propeller walk asymmetry
#  and compensating with port-biased derivative gain. Ancestor A2.3 used a
#  different approach 127 days ago. The colony chose a more nuanced adaptation."
```

### 8.2 The Palaver (Council Assessment)

When a variant completes Phase 3 knockout testing, it is presented to the **variant council** — the five voices that evaluate whether the variant deserves promotion:

1. **Sensor testimony:** "The IMU reports lower vibration amplitude with this variant."
2. **Actuator testimony:** "Servo current draw is 8% lower — less mechanical stress."
3. **Environmental testimony:** "Tested across sea states 1–4; no performance degradation."
4. **Ancestor testimony:** "This variant inherits cold-adaptive features from lineage A2."
5. **Future testimony:** "The variant introduces 2 new dependencies — acceptable, but watch debt ceiling."

The council produces a narrative assessment, not a score. As the elder, you read the story and decide. You can approve, reject, or request modifications. This is the Palaver — the African tradition of communal deliberation before action.

### 8.3 Natural Language Guidance

The colony's Griot layer enables natural language interaction:

```bash
nexus-cli ask "Why did variant R-Alpha get retired?"
# "R-Alpha was retired because its fitness dropped to 0.41 in rough conditions,
#  below the 0.5 minimum viability threshold sustained for 7 consecutive days.
#  Its calm-weather performance (0.92) was excellent, but rough-weather
#  performance was insufficient. R-Delta inherited its calm-weather
#  adaptations and added R-Gamma's rough-weather resilience."

nexus-cli suggest "Try higher derivative gain for the rudder in conditions above 15 knots wind"
# The AI queen bee generates a candidate bytecode with Kd increased by 20% for
# conditions where wind speed > 15 knots (implemented as a conditional branch
# mutation — Level 2). The variant enters shadow testing for 10,000 ticks.
```

### 8.4 The Gardener's Covenant — Your Rights and Responsibilities

| Right | Responsibility |
|-------|---------------|
| Decide what the colony optimizes for (fitness function) | Set realistic fitness weights; avoid contradictory goals |
| Veto any variant or evolution decision | Review the Griot narrative before approving; don't rubber-stamp |
| Export all colony data in standard formats | Perform dependency audits; maintain local backups |
| Operate without the Jetson (degraded mode) | Verify bytecodes work autonomously before trusting the colony |
| Receive honest, transparent explanations | Don't ask the colony to justify what it cannot |

The colony exists to extend your capability, not to replace your judgment. You are the gardener. The colony grows the plants; you decide what to cultivate.

---

## Quick Reference Card

```
ESSENTIAL COMMANDS:
  nexus-cli deploy-reflex --node N --json reflex.json
  nexus-cli set-season {spring|summer|autumn|winter}
  nexus-cli set-intent "natural language guidance"
  nexus-cli approve --all
  nexus-cli rollback --node N --to last-stable
  nexus-cli promote --node N --variant-hash <hash>
  nexus-cli retire --node N --variant-hash <hash>
  nexus-cli griot-summary --day today
  nexus-cli fitness-report --node N
  nexus-cli adoption-report
  nexus-cli overnight-report
  nexus-cli ask "<question>"

KEY FILES:
  /etc/nexus/colony_config.yaml     — Colony topology and evolution parameters
  /etc/nexus/fitness_config.yaml    — Fitness function weights and safety thresholds
  /var/lib/nexus/bytecodes/          — Bytecode archive (Merkle tree)
  /var/lib/nexus/griot/             — Narrative provenance records (JSON)
  /var/log/nexus/evolution.log       — Evolution pipeline logs

PORTS:
  Dashboard:     http://<jetson-ip>:8080
  MQTT telemetry: tcp://<jetson-ip>:1883 (topic: nexus/<colony_id>/#)
  RS-422 serial: /dev/ttyTHS1 at 921600 baud (connects to ESP32 bus)
```

---

*This guide is a living document maintained by the NEXUS developer advocacy team. For the theoretical foundations, see the Phase 2 discussion series (documents 01–07b). For the bytecode VM specification, see NEXUS-SPEC-VM-001. For the safety system specification, see NEXUS-SPEC-SS-001. For the philosophical foundations, see the five cross-cultural lens analyses and the Colony Thesis.*

**Remember: you are building a greenhouse, not an android. Seed it, shape its constraints, trust evolution, and harvest durable intelligence that no engineer could have designed.**

---

*Document ID: NEXUS-COLONY-P2-009 | Phase 4A | Agent-4A | Status: Release Candidate*
