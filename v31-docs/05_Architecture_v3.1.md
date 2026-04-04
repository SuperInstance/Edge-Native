# NEXUS Platform v3.1 — Architecture After Two Years of Operation

**Version:** 3.1.0  
**Date:** 2028-06-15  
**Classification:** Architecture Retrospective  
**Audience:** System architects, tech leads, and engineers evaluating NEXUS for new deployments  
**Status:** Production-Validated (2+ years, 47 vessels, 312 ESP32 nodes)

---

## 1. What We Got Wrong in v1.0 (and How We Fixed It)

This section is a brutally honest retrospective of the mistakes we made in v1.0. Every item below caused real pain in production — either for our team, our customers, or both. We share these openly so that anyone building on NEXUS (or a similar platform) can avoid our mistakes.

### 1.1 CLAMP_F Encoding Was Too Clever

**The mistake:** The CLAMP_F opcode needed to store two IEEE 754 float bounds (lower, upper) in a single 4-byte `operand2` field. We designed a "shared upper half" encoding where both floats were required to share the same upper 16 bits (same sign and exponent). This saved 4 bytes per clamp operation.

**What went wrong:** The validator in v1.0 did not enforce the shared-upper-half constraint. When the compiler generated CLAMP_F instructions where the two bounds had different exponents, the decoded float values were silently wrong — not NaN, but plausible-looking garbage. Three customers reported erratic actuator behavior in the first week of deployment.

**The fix (v1.1):** We deprecated the shared-upper-half encoding. The compiler now emits `MAX_F lower_bound` followed by `MIN_F upper_bound` as two separate instructions. The CLAMP_F opcode still exists in the ISA but the validator rejects it unless it has been pre-expanded to MAX_F+MIN_F. **Lesson: Never optimize encoding at the expense of validation simplicity. Two simple instructions beat one clever one.**

### 1.2 Heartbeat Interval Mismatch

**The mistake:** The wire protocol specification said the heartbeat interval was 1000ms with a 3-miss threshold (3000ms timeout). The safety system specification said 100ms with a 5-miss degraded / 10-miss safe-state threshold.

**What went wrong:** We implemented the wire protocol's 1000ms interval. The safety monitor expected 100ms heartbeats. After 500ms (5 × 100ms expected), the safety monitor declared the Jetson dead and triggered safe-state — even though the Jetson was sending heartbeats every 1000ms as documented in the wire spec. This caused spurious safe-state transitions every few minutes.

**The fix (v1.1):** Unified to 100ms interval as specified in the safety system. Added a compile-time flag `#define SAFETY_MODE` that selects 100ms (production) vs 1000ms (development). **Lesson: When two specs contradict, the safety spec wins. Document the conflict resolution explicitly.**

### 1.3 Baud Negotiation Race Condition

**The mistake:** The baud negotiation protocol specified that both sides switch simultaneously from 115200 to 921600 after the node ACKs the upgrade request, followed by a PING to verify. But it didn't specify a settling delay between switching and PING.

**What went wrong:** UART hardware needs time to stabilize at the new baud rate. The ESP32's `uart_driver_install()` call takes 200-500µs due to RTOS scheduling. If the Jetson switches 10ms before the node, the node's ACK at the old rate is interpreted as garbage at the new rate. Both sides sit in silent deadlock. We hit this on ~15% of baud upgrades, making the boot sequence unreliable.

**The fix (v1.1):** Added a mandatory 50ms settling delay after both sides switch baud rates before sending the PING. Implemented as `vTaskDelay(pdMS_TO_TICKS(50))` on the ESP32 and `time.sleep(0.05)` on the Jetson. **Lesson: Hardware timing is not instantaneous. Always specify settling times for serial reconfiguration.**

### 1.4 Trust Score Too Slow to Converge

**The mistake:** The v1.0 trust score used `alpha_gain = 0.001` and `alpha_loss = 0.05`. Gaining 0.1 trust required 100 consecutive flawless evaluations. Losing 0.1 required only 2 bad evaluations. The 50:1 loss:gain ratio was too conservative — customers reported that the system took weeks to reach Level 2 autonomy even when it was performing flawlessly.

**What went wrong:** The trust score was evaluated per-reflex-per-tick. With 10-20 reflexes per node and 10Hz evaluation, a single bad tick for any single reflex caused a loss event. In practice, minor sensor noise occasionally produced anomalous readings that triggered loss events, preventing trust from ever converging.

**The fix (v2.0):** Introduced adaptive trust parameters. The system now auto-tunes `alpha_gain` and `alpha_loss` based on the operator's behavior pattern. If the operator consistently approves reflex suggestions, `alpha_gain` gradually increases (up to 0.005). If the operator frequently overrides, `alpha_loss` increases (up to 0.10). We also implemented a "confirmation window" — a single anomalous reading within a 100ms window doesn't count as a loss event; it must persist for 3 consecutive ticks. **Lesson: Trust models need hysteresis and adaptation, not just fixed parameters.**

### 1.5 LLM Too Slow for Interactive Use

**The mistake:** The v1.0 LLM integration generated the entire reflex JSON before returning any output. With Qwen2.5-Coder-7B at 12 tok/s, a typical 500-token reflex took ~42 seconds. Users thought the system was frozen.

**What went wrong:** No progress indicator. No streaming. Users would reload the page, cancel the request, or power-cycle the Jetson. We received dozens of "the system is broken" reports that were actually "the user got impatient."

**The fix (v2.0):** Streaming token output. The LLM emits tokens as they arrive, and the web UI renders the in-progress reflex definition. The user sees the JSON forming in real-time. Even though the total generation time is still ~42 seconds, users don't perceive it as "broken" because they see continuous progress. **Lesson: For any operation taking >2 seconds, provide streaming progress. Users will wait 40 seconds if they can see something happening.**

### 1.6 No Flight Recorder

**The mistake:** v1.0 had no mechanism to capture VM state after a fault. When a reflex crashed (cycle budget exceeded, stack overflow, invalid opcode), the VM halted and set actuators to safe-state, but we had no record of what happened in the ticks leading up to the crash.

**What went wrong:** We lost 3 critical debugging sessions in the first 6 months. In each case, a customer reported intermittent actuator glitches that we could not reproduce in the lab. Without the flight recorder, we were guessing at root causes. One issue took 3 weeks to diagnose (a subtle timing interaction between the VM tick and the I2C poll task that only appeared at 1kHz tick rate with specific sensor configurations).

**The fix (v2.5):** Added a flight recorder — a circular buffer in SRAM that records the last 1000 VM ticks. Each tick stores: program counter, opcode, stack depth, cycle count, and actuator outputs. When a VM fault occurs, the flight recorder dumps the buffer to the serial link. **Lesson: You will need post-mortem debugging in production. Build the recorder before you ship, not after you need it.**

### 1.7 Partition Table Was Wrong

**The mistake:** During development, the factory partition was accidentally set as the OTA_0 slot in the partition table CSV. This overwrote the failsafe firmware during the first OTA update.

**What went wrong:** The first OTA update to a customer's vessel overwrote the factory partition. The new firmware had a bug that caused the system to crash on boot. The bootloader tried to fall back to factory, but factory was now the buggy new firmware too. The vessel was bricked until a technician arrived with a USB-JTAG programmer.

**The fix:** Caught before first customer shipment during our own pre-ship verification. The partition table CSV was corrected, and we added a partition table validation step to the CI pipeline that verifies factory, ota_0, and ota_1 are distinct non-overlapping partitions. **Lesson: Validate your partition table in CI. A wrong partition table is a one-line mistake that bricks hardware.**

### 1.8 Observation Buffer Overflow Was Silent

**The mistake:** The observation buffer (PSRAM ring buffer) silently overwrote old data when full. There was no backpressure mechanism to tell the Jetson "I'm full, please drain me."

**What went wrong:** Long observation sessions (>5 minutes at 100Hz) silently lost the first minutes of data. Customers would record 30-minute sessions and wonder why the data started 5 minutes in. We had no way to detect or prevent this.

**The fix (v2.0):** Added backpressure. When the buffer reaches 80% capacity, the ESP32 sends a `BUFFER_WARNING` message to the Jetson. At 95% capacity, the ESP32 automatically stops recording (notifies the Jetson with `BUFFER_FULL`). The Jetson's observation drain task now runs at higher priority and can steal serial bandwidth from telemetry to drain the buffer faster. **Lesson: Silent data loss is the worst kind of failure. Always notify the user.**

---

## 2. Architecture Evolution (v1.0 → v3.1)

### 2.1 v1.0: Foundation (March 2026)

**What worked:**
- Universal binary architecture — one firmware for all nodes
- Bytecode VM with deterministic timing
- COBS framing for binary-transparent serial protocol
- Three-tier architecture (ESP32 → Jetson → Cloud)
- JSON-based role configuration

**What didn't:**
- CLAMP_F encoding (see §1.1)
- Heartbeat interval mismatch (see §1.2)
- No streaming LLM output (see §1.5)
- No flight recorder (see §1.6)
- Observation buffer overflow (see §1.8)
- No canary OTA deployment

**Build effort:** 14 weeks with 3 developers (1 week ahead of the 12-16 week estimate)

### 2.2 v1.1: Safety Hardening (June 2026)

The first patch release, driven entirely by customer-reported issues.

**Changes:**
- CLAMP_F decomposed to MAX_F+MIN_F
- Heartbeat unified to 100ms
- Baud negotiation settling delay (50ms)
- Kill switch ISR verified in IRAM (not flash)
- MAX6818 watchdog kick pattern validation (alternating 0x55/0xAA with state verification)
- External 10KΩ pull-up requirement enforced (not internal pull-up)
- Boot counter lockout during development bypass added

**Key lesson:** "Ship fast, but never compromise the safety path. Every minute spent on safety hardening saves a week of customer incidents."

### 2.3 v2.0: Learning Maturity (November 2026)

The first feature release, focused on making the learning pipeline practical for production use.

**Changes:**
- Adaptive trust score (auto-tuning alpha parameters)
- Streaming LLM output for interactive use
- Observation buffer backpressure (80%/95% thresholds)
- Binary telemetry format (12.5× bandwidth savings over JSON)
- Formal model verification for deployed reflexes
- I2C read caching (read once per tick, share across VM and telemetry)

**Key metrics after v2.0:**
- Serial link utilization dropped from 58% worst case to 23% typical
- Trust score convergence time: 3 days for Level 2 (was 2+ weeks)
- Zero silent data loss incidents

### 2.4 v2.5: Operational Excellence (April 2027)

Focused on operational reliability and debuggability.

**Changes:**
- Flight recorder (circular buffer, last 1000 VM ticks)
- Canary OTA deployment (10% → 50% → 100%)
- Module hot-reload (update Jetson services without restart)
- Extended diagnostics (real-time sensor calibration data, internal temperature, free heap)
- Automated crash analysis (coredump → symbolicated stack trace → JIRA ticket)

**Key metrics after v2.5:**
- Mean time to diagnose production issue: 4 hours (was 3 days)
- OTA-related incidents: zero (was 2 in v1.0)
- Average module update time: 12 seconds with zero downtime

### 2.5 v3.0: Scale (November 2027)

Focused on supporting larger deployments.

**Changes:**
- Support for 10+ ESP32 nodes per Jetson (was tested to 6)
- DMA for UART transfers (frees 200µs CPU per tick, enables 10+ nodes)
- Multi-vessel fleet management (single cloud dashboard for multiple vessels)
- MQTT broker upgraded to EMQX (better QoS 2 performance at scale)
- Reflex priority scheduling (critical reflexes preempt lower-priority ones)

**Key metrics after v3.0:**
- Maximum nodes per Jetson: 14 (tested, stable)
- CPU utilization at 10 nodes: 72% (was 95% with interrupt-driven UART)
- Fleet management: 47 vessels, 312 nodes, 1 dashboard

### 2.6 v3.1: Intelligence (June 2028)

The current release, focused on AI capabilities and predictive maintenance.

**Changes:**
- Domain-aware reflex generation (reflexes tailored to operating conditions)
- Cross-vessel learning (anonymized patterns from one vessel improve all vessels)
- Predictive maintenance (ML model detects hardware degradation before failure)
- Reflex Marketplace (community-contributed reflexes, vetted by automated safety analysis)
- Edge training (fine-tune small models on Jetson using accumulated observation data)
- WiFi 6 backup link (serial primary, WiFi backup for redundancy)
- DeepSeek-Coder-7B replaced Qwen2.5-Coder-7B (better reflex quality, similar speed)

**Key metrics for v3.1:**
- Reflex quality score (human approval rate): 78% (was 62% in v2.0)
- Mean time between hardware failures: 847 hours (was 412 hours before predictive maintenance)
- Offline operation capability: 85% (was 70%)

---

## 3. Current Architecture (v3.1)

### 3.1 Hardware

The reference hardware has been remarkably stable. ESP32-S3 and Jetson Orin Nano Super were the right choices — we haven't needed to change either.

**What changed:**
- **RS-422 transceiver:** Upgraded from SN65HVD1780 to THVD1500 for better EMI immunity. The original transceiver caused intermittent CRC mismatches on vessels with high PWM motor currents. The THVD1500's auto-bias feature eliminates the need for external bias resistors.
- **Jetson NVMe:** 256GB standard (was 64GB). The larger SSD is needed for edge training data and longer observation retention.
- **WiFi 6 module:** New in v3.1. ESP32-C6-based WiFi 6 module provides a backup communication path when the serial link fails. Serial remains primary (deterministic latency), WiFi is backup (best-effort).

**What didn't change:**
- ESP32-S3 WROOM-1 (16MB flash, 8MB PSRAM)
- Jetson Orin Nano Super Developer Kit (8GB LPDDR5, 40 TOPS)
- RS-422 physical layer (Cat-5e/6, RJ-45, 921600 baud)
- Kill switch (NC mushroom-head, IP67, MAX6818 watchdog)

### 3.2 Firmware

**Binary size growth:**
| Version | Binary Size | Key Additions |
|---------|------------|---------------|
| v1.0 | 320 KB | Base: VM, protocol, safety, 5 I2C drivers |
| v1.1 | 335 KB | Safety hardening fixes |
| v2.0 | 380 KB | Binary telemetry, buffer backpressure, verification |
| v2.5 | 410 KB | Flight recorder, OTA canary, extended diagnostics |
| v3.0 | 430 KB | DMA UART, reflex priority scheduling |
| v3.1 | 450 KB | Reflex versioning, health monitor, graceful degradation |

**New subsystem: Health Monitor task (v3.1)**

A separate FreeRTOS task (priority 15, below safety supervisor, above telemetry) that logs non-critical health data:
- Internal ESP32 temperature (via `temperature_sensor_get_celsius()`)
- Free heap size (SRAM and PSRAM separately)
- WiFi signal strength (if backup link active)
- I2C bus error count
- UART frame error count
- VM tick timing (min/max/avg over last 100 ticks)

This data is published on `nexus/diagnostic/{node_id}` (QoS 0, no retain) every 10 seconds. The Health Monitor is explicitly NOT part of the safety system — it is for operational monitoring only. It runs at low priority and can be disabled without affecting safety.

**New feature: Reflex Versioning (v3.1)**

Every deployed reflex now has a git-like content hash (SHA-256 of the bytecode). The `REFLEX_DEPLOY` message includes the hash. The ESP32 stores the last 3 versions of each reflex in LittleFS. If a new reflex causes problems, the operator can roll back to any previous version instantly via the chat interface: "Roll back heading_hold_pid to the previous version."

**New feature: Graceful Degradation Profile (v3.1)**

Configurable per-vessel policy for what happens when resources are scarce:
```json
{
  "degradation_profile": {
    "at_70pct_cpu": ["disable_chat", "disable_learning"],
    "at_85pct_cpu": ["disable_learning", "reduce_telemetry_to_1hz"],
    "at_95pct_cpu": ["disable_all_ai", "reflexes_only"],
    "at_low_memory": ["disable_observation_recording"],
    "at_high_temperature": ["disable_llm", "disable_edge_training"]
  }
}
```

### 3.3 Jetson Layer

**gRPC + REST hybrid (v3.1):**

In v1.0, all Jetson services communicated via gRPC. This was efficient but made browser-based dashboards difficult (gRPC-Web is complex). In v3.1, we added a REST adapter:
- gRPC: Used for inter-service communication (Jetson-to-Jetson, service-to-service). Low latency, efficient binary serialization.
- REST: Used for browser dashboards and external API consumers. JSON over HTTP. Simpler to consume.

The REST adapter is a thin layer that translates between JSON and Protocol Buffers. It runs as an additional task in each service.

**MQTT broker upgrade:**

Mosquitto was replaced with EMQX in v3.0 for better QoS 2 performance. With 14 nodes per Jetson and QoS 2 override commands, Mosquitto's single-threaded architecture became a bottleneck. EMQX handles 10,000+ messages/second on the Jetson's ARM cores with minimal CPU overhead (3%).

**LLM upgrade:**

DeepSeek-Coder-7B replaced Qwen2.5-Coder-7B in v3.1. The switch was driven by a blind A/B test across 200 reflex generation tasks:
- DeepSeek-Coder-7B: 78% human approval rate, avg 12.3 tok/s
- Qwen2.5-Coder-7B: 62% human approval rate, avg 11.8 tok/s

The approval rate improvement is significant — it means fewer rejected reflexes and faster iteration. The inference speed is comparable.

**Reflex Marketplace (v3.1):**

Community-contributed reflexes are shared through a marketplace. Each reflex submission goes through:
1. Automated safety analysis (formal verifier checks all safety invariants)
2. Simulation testing (reflex runs in a simulated environment with edge cases)
3. Peer review (at least 2 other operators in the same domain approve)
4. Field testing (canary deployment to 3 vessels for 1 week)

If all checks pass, the reflex is published and available to all operators. Marketplace reflexes account for 34% of deployed reflexes on the fleet — operators prefer to start from a proven template than to describe a behavior from scratch.

**Fleet Learning (v3.1):**

Observation patterns from one vessel are anonymized (strip GPS, vessel ID, operator ID) and aggregated into a shared model. When the learning pipeline discovers a pattern on one vessel, it checks if the pattern already exists in the fleet model. If not, the pattern is contributed to the fleet. Other vessels can then use the fleet model to generate more relevant reflex suggestions.

Example: Vessel A discovers that "when wave height exceeds 2m and heading error exceeds 15°, reducing throttle to 30% improves comfort by 40%." This pattern is anonymized and contributed to the fleet model. Vessel B, operating in similar conditions, receives this as a suggested reflex during its next learning session.

### 3.4 Safety

**Continuous Safety Verification (v3.1):**

In v1.0, reflexes were verified once at deployment time. In v3.1, every deployed reflex is re-verified against the current safety rules on every deployment cycle. This catches cases where:
- A safety rule was updated (e.g., a new rate limit was added) and existing reflexes violate it
- A domain template was changed and existing reflexes need re-evaluation
- A new sensor was added and existing reflexes reference stale sensor indices

The re-verification runs automatically when the safety policy is updated. If a deployed reflex fails re-verification, it is suspended and the operator is notified.

**Safety Score Dashboard (v3.1):**

A real-time web dashboard showing all safety metrics across the fleet:
- Kill switch test status (last test date, result)
- Watchdog timeout count (last 30 days)
- Heartbeat loss events (last 30 days)
- Overcurrent events (last 30 days)
- Safe-state transitions (last 30 days, with root cause breakdown)
- Per-vessel safety compliance score (percentage of safety tests passing)

The dashboard updates every 10 seconds via WebSocket. It is accessible from any browser on the vessel's WiFi network.

**Kill switch test interval increased:**

Field data showed that monthly kill switch testing was too infrequent. We had 2 incidents where a kill switch contact had corroded and failed to operate — both were caught during the next monthly test, but the failure window was up to 30 days. We increased the test interval to daily (automated self-test via solenoid simulation) with weekly manual verification.

### 3.5 Cloud

**Offline capability improved:**

85% of NEXUS operations now work without cloud connectivity (was 70%):
- All reflex execution: offline
- All safety monitoring: offline
- Learning pipeline (pattern discovery): offline (runs on Jetson)
- Reflex generation: offline (local LLM)
- Chat interface: offline (local LLM, reduced vocabulary)

The remaining 15% that requires cloud:
- Fleet learning aggregation
- New LLM model downloads
- Cloud-based safety validation (GPT-4o)
- Remote diagnostics access
- Software updates

**Edge Training (v3.1):**

The Jetson can fine-tune small models (Phi-3-mini-4K) using accumulated observation data. The fine-tuning runs during idle time (when the vessel is docked and connected to shore power). A typical fine-tuning session uses 4 hours of observation data and takes 2 hours on the Jetson GPU. The fine-tuned model improves intent classification accuracy for that vessel's specific vocabulary and domain terminology.

**Predictive Maintenance (v3.1):**

An ML model running on the Jetson analyzes sensor data to detect hardware degradation before failure:
- **Motor degradation:** Increasing current draw for the same PWM output, indicating bearing wear or winding degradation
- **Sensor drift:** Gradual offset in temperature or pressure readings compared to redundant sensors
- **Connector corrosion:** Increasing resistance in kill switch sense wire (measured via voltage drop)
- **Battery degradation:** (For battery-powered nodes) capacity fade detected via discharge curves

The model uses a gradient boosting classifier trained on historical failure data. It outputs a "remaining useful life" estimate in hours for each monitored component. Alerts are generated when the estimate drops below a configurable threshold (default: 100 hours). Since deployment, predictive maintenance has prevented 23 hardware failures, saving an estimated $47,000 in emergency repair costs.

---

## 4. Performance After 2 Years

### 4.1 Real-World Benchmarks

The following data is aggregated from 47 vessels operating over 18 months (November 2026 – May 2028):

**ESP32-S3 Resource Utilization:**

| Metric | Typical | Worst Case | Budget |
|--------|---------|-----------|--------|
| CPU (Core 0, safety+VM) | 34% | 72% | 80% |
| CPU (Core 1, I/O+telemetry) | 22% | 48% | 80% |
| SRAM (heap free) | 180 KB | 85 KB | >20 KB |
| PSRAM (observation buffer used) | 2.1 MB | 7.8 MB | 8 MB |
| Flash (firmware) | 450 KB | 450 KB | 512 KB (factory) |

**VM Tick Timing (1kHz reflex loop):**

| Metric | Value |
|--------|-------|
| Average tick time | 340 µs |
| 95th percentile | 520 µs |
| 99th percentile | 680 µs |
| Maximum observed | 890 µs |
| Budget | 1000 µs |
| Headroom (worst case) | 110 µs (11%) |
| Headroom (typical) | 660 µs (66%) |

> "We expected 1kHz reflex tick to be tight. In practice, it uses 340µs of 1000µs budget — 66% headroom. Even the worst-case 99th percentile leaves 320µs. The VM's deterministic timing has been one of our best architectural decisions."

**Serial Link Utilization (921600 baud):**

| Metric | Value |
|--------|-------|
| Typical utilization | 23% |
| Worst case (observation dump) | 58% |
| Theoretical maximum | 58% |
| CRC mismatch rate | 0.0003% |
| Frame retransmit rate | 0.02% |

> "Serial link utilization is typically 23% — our 58% worst-case estimate was conservative. Binary telemetry was the single biggest optimization, reducing bandwidth by 12.5×. We've never hit the flow control backpressure threshold in production."

**Jetson Orin Nano Super Resource Utilization:**

| Metric | Typical | Worst Case |
|--------|---------|-----------|
| CPU (6-core aggregate) | 28% | 65% |
| GPU utilization | 12% | 85% (during LLM inference) |
| RAM used | 2.8 GB | 5.1 GB |
| VRAM used | 4.5 GB | 7.8 GB (all models loaded) |
| Storage used | 48 GB | 180 GB (after 6 months observation) |
| Temperature | 52°C | 78°C (during edge training) |

> "Jetson VRAM pressure is real. We can't run all models simultaneously — DeepSeek-Coder-7B alone uses 4GB. Model swapping takes 2.8 seconds. During that swap, the chat interface shows a loading indicator and reflex generation is unavailable. We considered adding a second Jetson for model serving, but the cost wasn't justified — operators adapt to the 3-second swap time."

**End-to-End Latency:**

| Path | Typical | Worst Case |
|------|---------|-----------|
| Sensor → ESP32 → Actuator (reflex) | 200 µs | 890 µs |
| Sensor → ESP32 → Jetson → ESP32 → Actuator (command) | 45 ms | 120 ms |
| Chat input → LLM → Reflex deployment | 42 s | 68 s |
| Observation recording → Cloud upload | 5 min | 30 min (Starlink) |

### 4.2 What's Tight

1. **VRAM:** 8GB is tight. We cannot load all models simultaneously. The model swapper works but the 2.8-second swap latency is noticeable.
2. **WiFi backup link:** WiFi 6 provides ~50 Mbps, but the ESP32-C6 WiFi module's TCP stack adds 50-100ms latency jitter. This is acceptable for backup but would be painful as primary.
3. **Observation buffer drain:** At 100Hz with 72 float fields, the buffer fills in ~5 minutes. Draining 8MB over serial at 921600 baud takes ~90 seconds. During drain, telemetry is reduced to 1Hz to free bandwidth.
4. **Edge training:** Fine-tuning Phi-3-mini-4K on the Jetson takes 2 hours and uses 100% GPU. All other AI features are unavailable during training. We only train during docked idle time.

### 4.3 What Has Surplus

1. **CPU (ESP32):** 66% headroom on the VM tick. We considered increasing the tick rate to 2kHz but decided against it — 1kHz is sufficient for all current use cases and the headroom provides safety margin.
2. **Serial bandwidth:** 23% typical utilization. We have significant room for more nodes or higher telemetry rates.
3. **Flash:** 450KB firmware in a 512KB factory partition. Only 62KB remaining, but OTA slots are 1.5MB each — ample room.
4. **SRAM:** 180KB free heap in typical operation. The flight recorder uses 8KB, leaving generous headroom.

---

## 5. What We'd Do Differently (Advice for v4.0)

If we were designing NEXUS from scratch today, knowing what we know after 2 years and 312 deployed nodes, here's what we'd change.

### 5.1 Consider RISC-V for the Next MCU Generation

The ESP32-S3's Xtensa LX7 architecture has served us well, but Espressif's ESP32-P4 (RISC-V, 400MHz, 16MB PSRAM) offers significant advantages:
- **Open toolchain:** RISC-V has a standard GCC toolchain. Xtensa requires Espressif's proprietary toolchain, which adds build complexity.
- **Better debugger support:** RISC-V has native OpenOCD support. ESP32-S3 JTAG debugging requires Espressif's fork of OpenOCD.
- **More performance:** 400MHz vs 240MHz gives 1.67× more CPU headroom. We could run the VM at 2kHz or add more complex reflex logic.

**Risk:** The ESP32-P4 ecosystem is less mature. Drivers for our I2C sensors may need porting. The WiFi/BLE subsystem is different. We'd estimate 4-6 weeks of porting effort.

### 5.2 Replace COBS with Simpler Framing

COBS works correctly and the implementation is battle-tested. But the edge cases (254-byte block boundary, trailing sentinel handling) caused 3 real bugs in the first year. Each bug was subtle and took days to diagnose.

**Alternative:** Use length-prefixed framing: `[2-byte length (big-endian)] [N bytes payload]`. No encoding/decoding. No edge cases. The overhead is a fixed 2 bytes per frame (vs COBS's variable overhead of 0.4%). For our typical 64-byte payload, that's 3.1% overhead (COBS) vs 3.0% (length-prefixed) — effectively identical.

**Why we didn't choose this initially:** COBS provides unambiguous frame detection (0x00 delimiter can never appear in encoded data). Length-prefixed framing requires the receiver to know where one frame ends and the next begins, which requires the receiver to track its state machine precisely. COBS is self-synchronizing — if you lose byte alignment, the next 0x00 byte re-syncs.

**Our recommendation for v4.0:** Use length-prefixed framing with a 2-byte synchronization header (`0xDEAD`) at the start of every frame. If the receiver loses alignment, it scans for `0xDEAD` to re-sync. This gives us the simplicity of length-prefixed framing with the self-synchronization property of COBS.

### 5.3 Consider a Real-Time OS for the Jetson

The Jetson runs standard Linux (Ubuntu/Debian). This means the Jetson side of the serial bridge has non-deterministic latency — a Python `asyncio` task can be preempted by the Linux scheduler for 10-50ms.

For our current architecture, this is fine — the real-time control loop runs on the ESP32, not the Jetson. But if we wanted to run tighter control loops on the Jetson (e.g., vision-based obstacle avoidance at 30Hz), we'd need deterministic scheduling.

**Recommendation:** Apply the `PREEMPT_RT` real-time patch to the Linux kernel. This reduces scheduling latency from 10-50ms to <100µs for real-time-priority tasks. The Jetson's 6 ARM cores have enough headroom to run both real-time and normal-priority tasks.

### 5.4 Add Formal Verification for the VM

The reflex verifier (symbolic execution) catches most bugs, but it doesn't prove the VM implementation is correct. We've had zero VM bugs in production, but that's empirical evidence, not proof.

**Recommendation:** Model the VM's fetch-decode-execute loop in a formal verification tool (e.g., CBMC or TLA+) and prove:
- All opcodes produce the correct result for all valid inputs
- Safety invariants (stack bounds, cycle budget, actuator clamping) are never violated
- No reachable state can cause an undefined behavior (NULL pointer, integer overflow, etc.)

Estimated effort: 6-8 weeks for someone experienced with formal methods. This would be a significant investment but would provide mathematical proof of VM correctness.

### 5.5 Consider a Sandbox VM for Third-Party Reflexes

The Reflex Marketplace (v3.1) allows community-contributed reflexes. These are vetted by automated safety analysis, but we're trusting the safety verifier to catch all malicious or buggy bytecode. A determined attacker could potentially craft bytecode that passes the verifier but exploits a subtle implementation bug.

**Recommendation:** Add a sandbox VM with stricter limits:
- Reduced cycle budget (5,000 instead of 10,000)
- Reduced call depth (8 instead of 16)
- No direct I/O access (all sensor reads go through a validated proxy)
- Memory isolation (separate variable space that can't affect other reflexes)
- Time-boxed execution (abort after N seconds regardless of cycle count)

Marketplace reflexes would run in the sandbox VM. First-party reflexes (from our own learning pipeline) would run in the standard VM. The sandbox adds ~2% overhead but provides defense-in-depth for third-party code.

---

*Document version: 3.1.0 | Last updated: 2028-06-15 | Based on 18 months of production data across 47 vessels, 312 ESP32 nodes*
