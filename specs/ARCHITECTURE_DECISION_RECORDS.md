# NEXUS Platform — Architecture Decision Records (ADRs)

## Document Purpose
This document captures every significant architectural decision made during the design of the NEXUS Post-Coding Distributed Intelligence Platform. Each decision includes the chosen approach, rejected alternatives, confidence level, and rationale. This is a living document — decisions are never deleted, only superseded.

## Decision Index

| ADR | Title | Status | Confidence | Category |
|-----|-------|--------|------------|----------|
| 001 | Universal firmware vs per-role binaries | Accepted | HIGH | Firmware |
| 002 | Bytecode VM vs interpreted JSON reflexes | Accepted | HIGH | Firmware |
| 003 | COBS framing vs newline-delimited JSON | Accepted | HIGH | Protocol |
| 004 | RS-422 serial vs WiFi for Jetson-ESP32 link | Accepted | VERY HIGH | Protocol |
| 005 | Separate LLM for safety validation | Accepted | VERY HIGH | Cloud |
| 006 | Asymmetric trust model (25:1 loss:gain) | Accepted | HIGH | Autonomy |
| 007 | Hardware NC kill switch vs software-only | Accepted | VERY HIGH | Safety |
| 008 | Serial OTA vs WiFi OTA for firmware updates | Accepted | VERY HIGH | Deployment |
| 009 | JSON state machines vs behavior trees | Accepted | MEDIUM | Firmware |
| 010 | jsmn (runtime) + cJSON (config-only) parsers | Accepted | HIGH | Firmware |
| 011 | PSRAM ring buffer vs SRAM for observation data | Accepted | VERY HIGH | Firmware |
| 012 | gRPC + MQTT vs REST for Jetson cluster comms | Accepted | MEDIUM | Jetson |
| 013 | Qwen2.5-Coder-7B as local codegen model | Accepted | MEDIUM | Jetson |
| 014 | Factory partition never OTA-modified | Accepted | VERY HIGH | Safety |
| 015 | 80/15/5 JSON/C/Python code generation ratio | Accepted | HIGH | Cloud |
| 016 | Whisp-small.en for local STT | Accepted | HIGH | Jetson |
| 017 | Inverse RL for pattern discovery | Accepted | LOW | Learning |
| 018 | INCREMENTS 6-level vs SAE J3016 5-level | Accepted | MEDIUM | Autonomy |
| 019 | Per-subsystem autonomy vs system-wide | Accepted | HIGH | Autonomy |
| 020 | Hardcoded 32-opcode ISA vs extensible | Accepted | HIGH | Firmware |
| 021 | CRC-16 vs CRC-32 for wire protocol | Accepted | HIGH | Protocol |
| 022 | 8-byte fixed instruction size vs variable | Accepted | VERY HIGH | Firmware |
| 023 | LittleFS vs SPIFFS for reflex storage | Accepted | MEDIUM | Firmware |
| 024 | Phi-3-mini for intent classification | Accepted | MEDIUM | Jetson |
| 025 | PTC polyfuse as hardware current backup | Accepted | VERY HIGH | Safety |
| 026 | MAX6818 external watchdog vs internal only | Accepted | HIGH | Safety |
| 027 | QoS 2 for override MQTT messages | Accepted | HIGH | Protocol |
| 028 | HDBSCAN for behavioral clustering | Accepted | MEDIUM | Learning |

---

## ADR-001: Universal Firmware vs Per-Role Binaries

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** HIGH (but not VERY HIGH — there is a real performance trade-off)
**Category:** Firmware

### Decision
Ship a single identical firmware binary (~320KB) for every ESP32 in the system. Role is determined entirely by JSON configuration sent at boot.

### Context
Every ESP32 in the system needs to potentially become any type of controller: autopilot, throttle, lighting, bilge, sensor hub, etc. Two approaches exist:

### Options Considered
**Option A (Chosen): Universal firmware**
- One binary to test, sign, and flash
- Dynamic role assignment via JSON at boot
- Hot-swap: replace any ESP32 with a fresh unit, it gets its role automatically
- Slightly larger binary due to unused driver code (~320KB vs ~150KB minimal)

**Option B: Per-role firmware**
- Smaller per-role binaries (~150KB)
- Role is baked in at compile time
- Each binary needs individual testing and signing
- Replacing a failed unit requires knowing which firmware to flash

### Rationale
The operational simplicity of Option A far outweighs the 170KB flash overhead. ESP32-S3 with 4MB+ flash has ample room. The hot-swap advantage is decisive for field deployment: a fisherman can swap a waterlogged ESP32 without a laptop, just by plugging in a new unit. The factory partition (which is never OTA-modified) provides the trusted runtime foundation that all roles share.

### Consequences
- Firmware binary is ~320KB (acceptable on 4MB+ flash)
- Flash usage for unused drivers is wasted
- Adding a new peripheral driver requires firmware update to ALL nodes (not just the ones that need it)
- Mitigation: driver registry can be loaded from LittleFS as C extension modules for rare drivers

### What Would Change My Mind
If we discover a MCU target with only 256KB flash, we may need to switch to a modular firmware build system that links only the needed drivers. The I/O driver registry design anticipates this by using function pointers.

---

## ADR-002: Bytecode VM vs Interpreted JSON Reflexes

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** HIGH
**Category:** Firmware

### Decision
Compile JSON reflex definitions to bytecode at load time. Execute bytecode on a lightweight stack VM (32 opcodes, 8-byte fixed instructions).

### Context
Reflex behaviors need to execute at 100Hz-1kHz. Two execution models:

### Options Considered
**Option A (Chosen): Bytecode VM**
- JSON→bytecode compilation: ~10ms one-time cost
- Per-cycle execution: <100us for typical PID reflex
- Deterministic timing (bounded instruction count)
- Requires a VM implementation (~12KB code)
- Debugging requires decompilation or source-level tracing

**Option B: Interpreted JSON**
- Direct jsmn parse + evaluate each cycle
- Per-cycle parsing: 0.5-2ms (unacceptable at 1kHz)
- Human-readable execution trace (every step is a JSON operation)
- No VM overhead (~4KB code)
- Non-deterministic (JSON string handling has variable length)

### Rationale
At 1kHz tick rate, the per-cycle budget is 1000us. JSON parsing alone consumes 500-2000us, leaving insufficient time for actual computation. Bytecode execution takes <100us, leaving 900us for PID math, state machine evaluation, and sensor filtering. The 12KB VM code cost is modest and pays for itself in every reflex cycle.

### Consequences
- JSON reflexes serve as the human-readable source of truth
- Bytecode is a compiled artifact, always regenerable from JSON
- VM adds implementation complexity but provides the deterministic timing guarantee that safety-critical systems require
- A bug in the VM itself would affect ALL reflexes (mitigated by VM being small, static, and extensively tested)

### What Would Change My Mind
If reflex execution frequency requirements are lowered to <10Hz for all use cases, interpreted JSON becomes viable. But industrial robotics commonly needs 50-100Hz control loops, and marine autopilot needs 10Hz heading hold with <1ms response. Bytecode is the safe choice.

---

## ADR-003: COBS Framing vs Newline-Delimited JSON

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** HIGH
**Category:** Protocol

### Decision
Use Consistent Overhead Byte Stuffing (COBS) framing with 0x00 delimiters for all serial messages, with CRC-16/CCITT-FALSE validation.

### Options Considered
**Option A (Chosen): COBS framing**
- Supports both JSON and binary payloads (observation dumps, OTA chunks)
- Bounded overhead: exactly 1 extra byte per 254 payload bytes (0.4%)
- No escaping needed inside payload
- Well-tested open source implementations in C and Python

**Option B: Newline-delimited JSON**
- Simple to implement and debug
- Only supports JSON payloads (requires base64 encoding for binary data)
- Base64 encoding adds 33% overhead to binary payloads
- JSON must never contain raw newlines (common pitfall)

**Option C: SLIP (Serial Line IP)**
- Mature protocol (RFC 1055)
- Uses 0xC0 as delimiter (ambiguous if transmitter crashes mid-message)
- Overhead comparable to COBS

### Rationale
The observation buffer dump transfers 5.5MB of binary data. With newline-delimited JSON + base64, this would expand to 7.3MB. With COBS framing, it stays at 5.5MB + 0.4% framing overhead = 5.52MB. COBS also cleanly separates framing from payload semantics, making the protocol easier to reason about. The SLIP delimiter ambiguity (0xC0 appears in both start and end positions) was the decisive factor against it.

---

## ADR-004: RS-422 Serial vs WiFi for Jetson-ESP32 Link

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** VERY HIGH
**Category:** Protocol

### Decision
Use RS-422 full-duplex serial as the primary link between Jetson and ESP32 nodes. WiFi available as backup only.

### Rationale
Marine and industrial environments have unreliable RF: metal hulls attenuate WiFi, salt spray corrodes antennas, motors generate EMI. RS-422 is immune to all of these. A wired connection simply works. The performance is adequate: 921600 baud provides ~80KB/s effective throughput, enough for all telemetry, commands, and even full observation buffer dumps.

**What Would Change My Mind:** Nothing. This is one of the highest-confidence decisions. If RF reliability is not a concern (e.g., indoor factory with WiFi infrastructure), WiFi can be used as primary with RS-422 as backup. But the default should always be wired.

---

## ADR-005: Separate LLM for Safety Validation

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** VERY HIGH
**Category:** Cloud

### Decision
Safety validation of generated code must use a DIFFERENT LLM call (or at minimum, a different conversation context) than the code generation call.

### Rationale
When the same model generates and validates code, it tends to approve its own work because the validation context includes the reasoning that led to the design. This is a well-documented cognitive bias in LLMs called "self-validation bias." Using a different model forces fresh analysis. The $0.01-0.03 per validation call cost is negligible compared to deploying unsafe code.

---

## ADR-006: Asymmetric Trust Model (25:1 Loss:Gain)

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** HIGH (matches human psychology research, but specific ratio is tunable)
**Category:** Autonomy

### Decision
Trust is gained slowly (alpha_gain = 0.002) and lost quickly (alpha_loss = 0.05), creating a 25:1 loss-to-gain ratio.

### Rationale
Grounded in Lee and See (2004) human trust psychology: humans trust automation slowly but distrust it quickly. A single frightening event undermines weeks of reliable operation. The 25:1 ratio means gaining 0.1 trust from T=0.5 requires ~50 consecutive good evaluations, while losing 0.1 from T=0.9 requires only 2 bad evaluations. This produces realistic advancement timelines: Level 3 in ~120 days of flawless operation, Level 5 in ~300 days.

### What Would Change My Mind
If field testing shows advancement is too slow for practical use, alpha_gain can be increased to 0.005 (5:1 ratio) for low-risk subsystems like lighting. The ratio is configurable per-subsystem.

---

## ADR-007: Hardware NC Kill Switch vs Software-Only

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** VERY HIGH
**Category:** Safety

### Decision
Physical NC (normally-closed) mushroom-head kill switch wired to GPIO interrupt + hardware relay that cuts actuator power. Software kill (CLI command, MQTT message) available but NOT the primary mechanism.

### Rationale
Software crashes. Period. No software-only kill switch can be trusted because the software that is supposed to implement it may itself be crashed. The NC contact physically pulls the GPIO low regardless of software state. The relay cuts actuator power independently of the ESP32. This is defense in depth: even if the ESP32 firmware enters an infinite loop or the SRAM is corrupted, actuators de-energize within 100ms.

---

## ADR-009: JSON State Machines vs Behavior Trees

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** MEDIUM (this is the decision I'm least confident about)
**Category:** Firmware

### Decision
Use JSON state machines as the primary reflex representation.

### Options Considered
**Option A (Chosen): JSON state machines**
- Easy to visualize: "system is in CORRECTING state because heading error > 2 degrees"
- Straightforward to verify for deadlock and reachability
- Maps naturally to bytecode VM's execution model (labeled code blocks)
- Limited composability (can't easily combine two state machines)

**Option B: Behavior trees**
- More compositional: complex behaviors built from simple subtrees
- Industry standard in game AI and robotics (BehaviorTree.CPP)
- Harder to represent in JSON (tree structure with decorators)
- Harder to explain to a human operator
- Harder to verify formally

### Rationale
Explainability is paramount. A fisherman needs to understand why the system did something: "The autopilot turned left because the wind shifted." State machines make this explanation trivial. Behavior trees would require explaining decorator sequences. The composability limitation is real but manageable: complex behaviors are broken into multiple named reflexes with priority ordering rather than one giant tree.

### What Would Change My Mind
If we encounter use cases that require deeply nested conditional logic (more than 5 levels of decision making), behavior trees may become necessary. We could support both representations in the VM, with state machines as the default and behavior trees available for complex cases.

---

## ADR-013: Qwen2.5-Coder-7B as Local Codegen Model

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** MEDIUM (model landscape changes rapidly)
**Category:** Jetson

### Decision
Use Qwen2.5-Coder-7B-Instruct at Q4_K_M quantization (~4GB VRAM) as the local code generation model on Jetson Orin Nano 8GB.

### Options Considered
**Option A (Chosen): Qwen2.5-Coder-7B** — 12 tok/s, excellent code quality, understands embedded constraints
**Option B: CodeLlama-7B** — slightly faster (14 tok/s), lower code quality, worse at following system prompts
**Option C: DeepSeek-Coder-6.7B** — comparable quality, slightly faster, less tested on Jetson platform
**Option D: StarCoder2-7B** — good quality, poor at following embedded-specific system prompts
**Option E: Phi-3-mini-4K** — much faster (40+ tok/s), but 4K context window too small for complex reflexes

### Rationale
Qwen2.5-Coder-7B offers the best balance of code quality, instruction-following for embedded constraints, and inference speed on Jetson hardware. The 4GB VRAM footprint leaves 4GB for OS, Docker, Whisper, and other services. The 12 tok/s speed means generating a typical 500-token reflex JSON in ~40 seconds, which is acceptable for interactive use.

### What Would Change My Mind
New models are released monthly. If a 3B parameter model achieves comparable code quality at 30+ tok/s, we should switch. The model interface is abstracted behind a simple generate_code(prompt, max_tokens) API, making swaps straightforward.

---

## ADR-017: Inverse RL for Pattern Discovery

**Status:** Accepted (with caveats)
**Date:** 2026-03-29
**Confidence:** LOW (academic technique, industrial validation limited)
**Category:** Learning

### Decision
Use Bayesian reward inference (inspired by Inverse Reinforcement Learning) as one of the pattern discovery algorithms, alongside simpler cross-correlation and change-point detection.

### Rationale
IRL provides the theoretical framework for inferring "why" a human acts the way they do, not just "what" they do. The reward function (weighted features like comfort, efficiency, safety) is directly interpretable. However, IRL in practice requires substantial data (days of observation) and can be unstable. We mitigate this by:
1. Using IRL as one tool among several (not the sole pattern discovery method)
2. Seeding the prior with narration rules (the human says "comfort matters most" → weight comfort higher)
3. Running IRL offline (not real-time) so computational cost doesn't affect operation

### What Would Change My Mind
If IRL proves unstable or unreliable in field testing, it can be demoted to an optional analysis tool. Cross-correlation and change-point detection alone are sufficient for 80% of pattern discovery use cases. IRL is retained for the 20% where understanding human motivation matters (e.g., "why does the captain prefer a particular trolling pattern?").

---

## ADR-020: Hardcoded 32-Opcodes vs Extensible

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** HIGH
**Category:** Firmware

### Decision
Define exactly 32 opcodes (0x00-0x1F) in the bytecode VM. No mechanism for runtime extension.

### Rationale
A fixed instruction set ensures: (1) every bytecode can be statically analyzed before execution, (2) cycle-count timing analysis is exact (no unknown opcodes), (3) the VM implementation is small and testable (~12KB), and (4) the compiler is simple (32 cases in a switch statement). If we need new capabilities, we add opcodes to the VM firmware and update all nodes via OTA — this is infrequent enough that the operational overhead is acceptable.

### What Would Change My Mind
If we discover a domain that fundamentally needs capabilities not expressible in 32 opcodes, we could reserve opcodes 0x1C-0x1F as "extended" opcodes with domain-specific semantics loaded from C extension modules. This hybrid approach was considered but rejected as unnecessary for the initial release.

---

## ADR-022: 8-Byte Fixed Instruction Size vs Variable

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** VERY HIGH
**Category:** Firmware

### Decision
Every VM instruction is exactly 8 bytes: 1 byte opcode + 1 byte flags + 2 bytes operand1 + 4 bytes operand2.

### Rationale
Fixed-size instructions enable direct indexing (PC += 8 to go to next instruction) without any length decoding. This eliminates a class of bugs (wrong PC advancement) and makes the fetch cycle a single memory read. Variable-length instructions save average memory but add complexity and timing variability. For safety-critical systems, predictable timing beats memory efficiency.

---

## ADR-023: LittleFS vs SPIFFS for Reflex Storage

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** MEDIUM (both are viable, difference is marginal)
**Category**: Firmware

### Decision
Use LittleFS for the reflex storage partition.

### Options Considered
**Option A (Chosen): LittleFS** — Power-loss resilient (copy-on-write with journaling), wear leveling, dynamic wear leveling, supports directories
**Option B: SPIFFS** — Simpler implementation, widely used in ESP-IDF, but no journaling (corruption on power loss during write)

### Rationale
ESP32s in marine/industrial environments experience unpredictable power loss (battery disconnects, blown fuses, vibration-induced connector failures). LittleFS's journaling ensures that either the old or new version of a reflex file is intact after power loss — never a corrupted partial write. This is critical because a corrupted reflex file could prevent the ESP32 from loading any reflex behavior on reboot, forcing it into safe-state mode.

### What Would Change My Mind
If LittleFS proves unreliable on ESP32-S3 PSRAM (it was designed for SPI flash, and PSRAM has different wear characteristics), we could use FAT32 on the flash partition with a journal layer.

---

## ADR-028: HDBSCAN vs K-Means for Behavioral Clustering

**Status:** Accepted
**Date:** 2026-03-29
**Confidence:** MEDIUM
**Category**: Learning

### Decision
Use HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise) for clustering similar behavioral patterns.

### Rationale
HDBSCAN does not require specifying the number of clusters in advance (unlike K-means), naturally handles noise/outlier trips (a captain doing something unusual once doesn't create a new cluster), and produces stable clusters (same data always produces same result). For behavioral data, where the number of distinct driving styles is unknown a priori and outlier trips are common, these properties are essential. The computational cost is higher than K-means but runs offline on the Jetson where 30 minutes of analysis time is acceptable.

---

## Superseded Decisions

(None yet — all decisions are active.)

## Pending Decisions

| Topic | Status | Notes |
|-------|--------|-------|
| OTA signing: ECDSA-P256 vs Ed25519 | Under evaluation | Ed25519 is faster but ECDSA has wider hardware support |
| Local LLM quantization: Q4 vs Q5 vs Q8 | Under evaluation | Q4 is a good balance; Q8 may improve quality significantly |
| MQTT broker: Mosquitto vs EMQX | Under evaluation | EMQX has better clustering but Mosquitto is simpler |
| Database: SQLite vs PostgreSQL for observation storage | Under evaluation | SQLite sufficient for single-vessel; PostgreSQL for fleet |
| Container orchestration: Docker Compose vs Kubernetes | Under evaluation | Docker Compose for single-vessel; K8s for fleet-scale deployment |
| Formal verification: Frama-C vs CBMC | Under evaluation | CBMC for model checking; Frama-C for worst-case execution time analysis |
