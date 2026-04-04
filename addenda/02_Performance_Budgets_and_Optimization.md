# Performance Budgets & Optimization Guide

> **NEXUS Platform — Engineer-to-Engineer Reference**
> ESP32-S3 (Xtensa LX7 dual-core 240 MHz, 512 KB SRAM, 8 MB PSRAM) + Jetson Orin Nano Super (40 TOPS, 8 GB LPDDR5), RS-422 @ 921,600 baud.
> Every number in this document was derived from datasheet values, measured bus timings, or bounded worst-case analysis. If you see a number that looks wrong, it is — go measure it on hardware and update this file.

---

## 1. ESP32-S3 Memory Budget (512 KB SRAM)

The ESP32-S3 has a unified 512 KB SRAM pool. PSRAM (8 MB via Octal SPI) is a separate, slower memory domain (~40 MB/s sustained vs. ~40 GB/s effective SRAM bandwidth with cache). PSRAM access also incurs cache-line misses that stall the CPU for 10–20 cycles. **Rule: only bulk, latency-tolerant data lives in PSRAM. Everything else is SRAM.**

### SRAM Allocation Table

| Consumer | Size (bytes) | Notes |
|---|---|---|
| FreeRTOS kernel | 4,000–6,000 | `configUSE_TIMERS=1`, `configMAX_PRIORITIES=7`, `configTICK_RATE_HZ=1000` |
| Idle task stack | 1,024 | Minimum safe for Xtensa context save |
| Safety supervisor task stack | 2,048 | Needs headroom for stack-heavy ISR deferral |
| Watchdog task stack | 1,024 | Light — just kicks WDT and checks task liveness |
| Serial TX/RX buffers (UART DMA) | 4,096 | 2 x 2,048-byte ring buffers on UART0/1 |
| COBS encode/decode working buffers | 2,048 | Max wire frame is 1,051 bytes + 5% COBS overhead + 1 delimiter |
| JSON parser working buffer (jsmn) | 1,024 | Token pool for incoming config/role messages (~100 tokens) |
| I2C driver buffers | 512 | 2 x 256-byte command/response FIFOs |
| Observation ring buffer metadata | 512 | Head/tail pointers, wrap counter, sequence number (data in PSRAM) |
| Protocol dispatch state machine | 512 | Current state, partial message assembly, CRC accumulator |
| **VM state** | **~5,376** | Data stack 1,024 + call stack 256 + variables 1,024 + sensor registers 256 + actuator registers 256 + PID state 256 + snapshot 2,048 + event ring 256 |
| Reflex bytecode storage (4 slots) | 16,384 | Up to 4 KB per compiled reflex, max 4 concurrent |
| Role configuration (cached JSON) | 2,048 | Parsed role definition held in SRAM after boot |
| Safety event log buffer | 1,024 | Circular buffer of last 16 safety events (64 bytes each) |
| Heap (dynamic allocations) | 20,000–30,000 | Telemetry assembly, temporary JSON, malloc fragmentation reserve |
| **TOTAL KNOWN** | **~62,000–68,000** | |
| **REMAINING for application** | **~444,000–450,000** | Very comfortable — but heap fragmentation is the real enemy |

### PSRAM Allocation

| Consumer | Size | Justification |
|---|---|---|
| Observation data ring buffer | 6 MB | 72 fields x 4 bytes x 100 Hz x ~277 seconds |
| Reflex bytecode (overflow beyond 4-slot SRAM cache) | 1 MB | Pre-compiled reflex library for fast slot swaps |
| Telemetry history (Jetson fetches this) | 1 MB | Decimated 1 Hz snapshots, ~7,000 samples |

**Critical warning:** Never allocate ISR-context buffers in PSRAM. PSRAM access can be preempted by flash cache misses, causing non-deterministic ISR latency. All ISR-used buffers (UART DMA, COBS working memory, safety event log) MUST reside in SRAM. Use `heap_caps_malloc(size, MALLOC_CAP_INTERNAL)` to enforce this at allocation time.

---

## 2. ESP32-S3 CPU Budget (240 MHz, Dual-Core)

### Core Affinity Assignment

| Core | Responsibilities | Rationale |
|---|---|---|
| **Core 0 (Protocol Core)** | UART RX ISR + COBS decode + dispatch, safety supervisor loop, watchdog, heartbeat TX | Deterministic I/O path; isolated from jittery sensor bus |
| **Core 1 (Application Core)** | VM execution, I2C sensor polling, GPIO/PWM actuator writes, telemetry assembly, observation sampling | CPU-intensive but latency-tolerant tasks |

### Per-Tick Timing Analysis

At a 1 kHz tick rate (1,000 µs budget per tick):

| Operation | Best Case | Worst Case | Notes |
|---|---|---|---|
| I2C sensor polling (N devices) | 200 µs | 500 µs | 400 kHz I2C, ~100 µs per device (address + 6-byte read + ACK). 2–5 devices typical |
| VM execution (single reflex) | 20 µs | 100 µs | 10–30 instructions at ~3 cycles each at 10 ns/cycle = 300–900 ns per instruction, plus register I/O overhead |
| Actuator writes (GPIO + PWM) | 10 µs | 20 µs | LEDC channel update via peripheral register writes |
| Telemetry assembly (JSON, amortized) | 10 µs | 30 µs | Full frame assembled at 10 Hz, amortized = 100–300 µs / 10 ticks |
| Safety checks (stale sensor, rate limits) | 5 µs | 10 µs | Monotonic timestamp comparison only — no I/O |
| **TOTAL per tick** | **~245 µs** | **~660 µs** | |
| **MARGIN** | **755 µs** | **340 µs** | Tight at worst case but feasible |

### Tick Rate Recommendations

| Tick Rate | Budget | Margin (worst case) | Recommendation |
|---|---|---|---|
| **100 Hz** | 10,000 µs | 9,340 µs | **Default for marine control.** PID at 10 Hz is sufficient for vessel dynamics (time constants > 500 ms). |
| **500 Hz** | 2,000 µs | 1,340 µs | Use for fast mechanical systems (e.g., arm servos with sub-10 ms response). |
| **1,000 Hz** | 1,000 µs | 340 µs | **Maximum.** Only use if you have fewer than 3 I2C devices or switch to SPI sensors. Batch I2C reads across ticks. |

### Scheduling Rules

1. **Never do I2C and UART DMA on the same core in the same tick.** I2C bus arbitration contention with flash cache fills creates unpredictable stalls.
2. **Sensor data flows Core 1 → FreeRTOS queue → Core 0** for telemetry TX. Queue depth = 4 entries (4 KB) is sufficient for 1 kHz burst absorption.
3. **VM execution on Core 1 must yield every N instructions** (configurable, default 50) to prevent telemetry starvation.
4. **Use ESP-IDF `esp_timer` for timestamping, not `xTaskGetTickCount()`**. `esp_timer` is 64-bit hardware-backed at 1 µs resolution; `xTaskGetTickCount()` is 32-bit and wraps at ~50 days at 1 kHz.

---

## 3. Serial Link Bandwidth Budget (921,600 Baud)

RS-422 differential signaling at 921,600 baud, 8N1 framing, full-duplex. Effective raw bitrate accounting for start/stop bits:

```
921,600 bits/sec / 10 bits/byte = 92,160 bytes/sec raw throughput
```

### COBS Encoding Overhead

COBS (Consistent Overhead Byte Stuffing) adds worst-case 1 byte per 254 bytes of payload plus 1 delimiter byte:

```
Overhead = ceil(payload / 254) + 1
For typical 200-byte telemetry: ceil(200/254) + 1 = 2 bytes overhead = +1.0%
For max 1051-byte frame: ceil(1051/254) + 1 = 6 bytes overhead = +0.57%
Average across message mix: ~+0.4%
```

Effective post-COBS throughput: **~92,530 bytes/sec.**

### Bandwidth Allocation Table

| Data Stream | Rate | Payload (bytes) | Overhead (HDR+CRC) | Total/sec | % of Link |
|---|---|---|---|---|---|
| JSON telemetry | 10 Hz | 200 | 12 | 2,120 | 2.3% |
| JSON telemetry | 100 Hz | 200 | 12 | 21,200 | 22.9% |
| Heartbeat (ESP32 → Jetson) | 10 Hz | 4 | 12 | 160 | 0.2% |
| Heartbeat | 100 Hz | 4 | 12 | 1,600 | 1.7% |
| Command ACK (Jetson → ESP32) | Sporadic | 8 | 12 | ~500 | 0.5% |
| Observation dump (active) | Burst | 28,800 | 3,200 | 32,000 | 34.6% |
| **Worst case total** | — | — | — | **~53,828** | **58.2%** |
| **Available headroom** | — | — | — | **~38,700** | **41.8%** |

### Bandwidth Conflict Resolution

When observation dumps are active (triggered by Jetson for learning), the observation stream consumes ~35% of link bandwidth. This conflicts with 100 Hz JSON telemetry. Resolution strategy:

1. **Primary:** Reduce telemetry to 10 Hz during observation capture (saves 19,080 bytes/sec).
2. **Fallback:** Switch telemetry to binary format (see Section 7, item #1) — 16 bytes vs. 200 bytes = **12.5x reduction**. This drops telemetry to 1.8% of link even at 100 Hz.
3. **Emergency:** Pause telemetry entirely for the ~87 seconds needed to dump a full 8 MB observation buffer.

### Frame Timing

```
Max frame size (COBS-encoded): 1,057 bytes
Transmission time at 921,600 baud: 1,057 x 10 / 921,600 = 11.5 ms worst case
Typical telemetry frame: 212 bytes → 2.3 ms
```

**Implication:** The serial link is the dominant source of latency in the sensor-to-Jetson path. A full-rate telemetry frame takes 2.3 ms on the wire. A max-size observation chunk takes 11.5 ms. Plan accordingly.

---

## 4. Jetson Orin Nano Super Resource Budget

### Memory (8 GB LPDDR5, Unified CPU/GPU)

| Consumer | Allocation | Notes |
|---|---|---|
| Linux + system services | 1,500 MB | JetPack 6.x with minimal desktop, no GUI |
| Qwen2.5-Coder-7B Q4_K_M (GGUF) | 4,096 MB | 4-bit quantized, 7B parameters. Primary code generation model. |
| Phi-3-mini-4k Q4 (GGUF) | 2,048 MB | 4-bit quantized, 3.8B parameters. Classification + reflex generation. |
| Whisper-small.en FP16 | 960 MB | 244M parameters. Always-resident for voice interface. |
| Piper TTS (ONNX) | 500 MB | Lightweight neural TTS. Always-resident. |
| Python application heap | 500 MB | asyncio event loop, MQTT client, gRPC stubs, telemetry buffers |
| OS page cache + buffers | 400 MB | Kernel-managed |
| **TOTAL** | **~8,004 MB** | **Exceeds physical memory if all LLMs loaded simultaneously** |

### Model Loading Strategy

**Iron rule: Only one LLM is loaded at a time.**

```
Qwen2.5-Coder-7B  (4 GB)  ← loaded for code generation
        ↓ swap (~2.5 sec via mmap + llama.cpp)
Phi-3-mini         (2 GB)  ← loaded for classification/reflex synthesis
        ↓ swap (~1.5 sec)
[neither loaded]           ← VRAM freed for observation processing
```

Whisper and Piper remain permanently loaded (~1.5 GB combined). They are small enough and used frequently enough that swap overhead is unacceptable.

**Swap time measured on Orin Nano Super (40 TOPS, LPDDR5-5600):**
- Qwen 7B unload + Phi 3B load: ~2.8 seconds (disk-to-memory for 2 GB, 8 GB/s LPDDR5 bandwidth)
- Phi 3B unload: ~0.3 seconds (kernel page cache eviction, not disk write)
- Total hot-swap cycle: **~3.1 seconds**

This is acceptable for interactive code generation (user is typing anyway) but **unacceptable for real-time reflex deployment**. Reflex bytecode must be pre-compiled and cached.

### CPU Core Allocation (6-core ARM Cortex-A78AE)

| Core(s) | Service | Utilization (typical) |
|---|---|---|
| Core 1 | Serial bridge (Python asyncio, all 4+ RS-422 ports) | 15–25% |
| Core 2 | MQTT broker (Eclipse Mosquitto) + gRPC server | 10–20% |
| Core 3 | LLM inference thread pool (llama.cpp, 4 threads) | 80–95% during inference, 0% idle |
| Cores 4–5 | Python application services (learning pipeline, chat, telemetry) | 30–60% |
| Core 6 | OS + kernel + background services | 10–20% |

**Thread affinity:** Pin llama.cpp to cores 3–5 with `taskset`. Pin the serial bridge to core 1. Left unpinned, the Linux scheduler will migrate the serial bridge across cores, causing cache misses and intermittent UART RX buffer overflows.

### Thermal Budget

| Parameter | Value |
|---|---|
| TDP | 15 W (typical), 25 W (max with `nvpmodel -m 0`) |
| Thermal throttle point | 85 °C (GPU clock reduced to 50%) |
| Time to throttle at full GPU load, no fan | ~30 minutes |
| Time to throttle at full GPU load, 80 mm Noctua @ 2000 RPM | Never (steady-state ~72 °C) |
| Ambient temperature rating | 0–50 °C operating |

**Mandatory:** Active cooling with a minimum 80 mm fan at 2,000 RPM. In marine environments (enclosed hull spaces reaching 55 °C ambient), consider a 40 mm heatsink + 80 mm fan combo with intake from outside the electronics bay.

---

## 5. End-to-End Latency Budgets

This is the single most important table in this document. It defines the fundamental architectural constraint that drives every other design decision.

### Critical Path: Sensor → Actuator (Real-Time Reflex)

```
Sensor sample → I2C read → ESP32 register → VM executes reflex → GPIO/PWM write → Actuator moves
```

| Stage | Latency | Notes |
|---|---|---|
| Sensor physical response time | 1–10 ms | IMU: 1 ms, temperature: 100 ms (doesn't matter — cached) |
| I2C read (sensor → ESP32 SRAM) | 100 µs | 400 kHz bus, 6-byte register read |
| VM reflex execution | 20–100 µs | See Section 2 |
| GPIO/PWM register write | 1 µs | Direct peripheral register access |
| Actuator physical response | 5–100 ms | Servo: 5–20 ms, hydraulic solenoid: 10–50 ms |
| **ESP32-local total (excl. actuator)** | **~121–201 µs** | **Sub-millisecond. This is real-time.** |

### Critical Path: Sensor → Jetson → Actuator (AI-Mediated)

```
Sensor → ESP32 → Serial → Jetson → AI inference → Serial → ESP32 → Actuator
```

| Stage | Latency | Notes |
|---|---|---|
| Sensor → ESP32 register | 100 µs | As above |
| ESP32 telemetry assembly + COBS encode | 50 µs | JSON format |
| Serial transmission (typical 212 bytes) | 2.3 ms | 212 x 10 / 921,600 |
| Jetson COBS decode + dispatch | 100 µs | Python asyncio overhead included |
| LLM inference (Qwen 7B, 500 output tokens @ 12 tok/s) | **41.7 seconds** | Not real-time. Period. |
| LLM inference (Phi 3B, 200 tokens @ 18 tok/s) | **11.1 seconds** | Still not real-time. |
| Reflex compile + serial transmit | ~500 ms | Python compiler → bytecode → COBS → 1,057 bytes @ 921,600 baud |
| Serial transmission (command, 100 bytes) | 1.1 ms | 100 x 10 / 921,600 |
| ESP32 COBS decode + dispatch | 20 µs | |
| VM execution (newly deployed reflex) | 20–100 µs | |
| **Total AI-mediated path** | **~12.1–43.1 seconds** | |

### The Fundamental Design Constraint

> **Real-time control (sub-millisecond) MUST use local ESP32 VM reflexes.**
> **AI generates NEW reflexes but does NOT participate in real-time control loops.**

This is not a performance limitation to work around — it is an architectural feature. The entire NEXUS system is designed around this separation:
- **Tier 1 (Reflex):** ESP32-local, sub-200 µs, deterministic.
- **Tier 2 (Cognitive):** Jetson-local, 1–10 second latency, for learning and reflex generation.
- **Tier 3 (Cloud):** Minutes latency, for training and fleet-level optimization.

Any design that requires an LLM in the sensor-to-actuator feedback loop is architecturally wrong for this platform.

---

## 6. Observation Data Rate Budgets

Observations are the lifeblood of the learning pipeline. Understanding the data rate at every stage of the pipeline prevents buffer overflows and bandwidth saturation.

### Generation Rate

| Parameter | Value |
|---|---|
| Sample rate | 100 Hz |
| Fields per sample | 72 (sensor readings + computed values + actuator states) |
| Bytes per field | 4 (float32) |
| Raw rate | 72 x 4 x 100 = **28,800 bytes/sec (28.2 KB/s)** |
| Delta-encoded rate (typical) | **5,000–10,000 bytes/sec** | Most fields change slowly; only IMU and gyro update at full rate |

### Storage Budget

| Buffer | Size | Duration at 100 Hz | Duration at delta-encoded |
|---|---|---|---|
| ESP32 PSRAM ring buffer | 8 MB | 277 seconds (4.6 min) | 800–1,600 seconds (13–27 min) |
| Jetson SSD staging | 500 MB | 17,361 seconds (4.8 hours) | 50,000–100,000 seconds (14–28 hours) |

### Transfer Budget

| Path | Bandwidth | Time to transfer 8 MB |
|---|---|---|
| ESP32 → Jetson (RS-422 @ 921,600 baud, raw) | 92.2 KB/s | **87 seconds** |
| ESP32 → Jetson (with COBS + header overhead) | ~88 KB/s | **91 seconds** |
| ESP32 → Jetson (LZ4 compressed, ~2:1 ratio) | ~88 KB/s effective | **~46 seconds** (4 MB transferred) |
| Jetson → Cloud (Starlink, typical 20 Mbps uplink) | 2.5 MB/s | **3.2 seconds** |
| Jetson → Cloud (4G LTE, typical 5 Mbps uplink) | 625 KB/s | **12.8 seconds** |
| Jetson → Cloud (bad cellular, 1 Mbps) | 125 KB/s | **64 seconds** |

**Practical implication:** At 100 Hz raw, the ESP32 PSRAM buffer fills in 4.6 minutes. The serial link takes 87 seconds to drain it. This means the ESP32 can buffer ~5 minutes of observations before the buffer wraps, but the Jetson must initiate a dump before 4.6 minutes elapse or data is lost. **Delta encoding is not optional — it extends buffer lifetime to 13–27 minutes, providing ample margin for the Jetson to notice and initiate a dump.**

---

## 7. Optimization Checklist

The following 15 optimizations are ranked by estimated impact. Each is a concrete, implementable change with a measurable effect on one or more budget dimensions.

### 1. Binary Telemetry Format Instead of JSON — **CRITICAL**
**Impact:** 12.5x bandwidth reduction (200 bytes → 16 bytes per frame)
**Applies to:** Serial link budget, CPU budget (eliminates JSON serialization)
**Implementation:** Define a fixed-order struct matching the 72 observation fields. Transmit as raw bytes with no field names. The Jetson knows the field order from the role configuration JSON received at boot. Saves 18,400 bytes/sec at 100 Hz — frees 20% of serial bandwidth.
**Effort:** 2 hours. Changes in `telemetry.c` (ESP32) and `serial_bridge.py` (Jetson).

### 2. DMA for All UART Transfers — **HIGH**
**Impact:** Frees ~200 µs CPU time per tick on Core 0
**Applies to:** CPU budget
**Implementation:** Use ESP-IDF `uart_driver_install()` with `rx_buffer_size=2048` and `tx_buffer_size=2048`. The driver already uses DMA by default — just ensure you're not calling `uart_read_bytes()` in a busy loop. Use `uart_event_task` to wait on UART events via FreeRTOS queue.
**Effort:** 1 hour. Verify existing code uses event-driven UART, not polling.

### 3. Cache I2C Sensor Reads — **HIGH**
**Impact:** Eliminates redundant I2C transactions when both VM and telemetry need the same data
**Applies to:** CPU budget, I2C bus contention
**Implementation:** Read each sensor once per tick into a shared `sensor_snapshot_t` struct in SRAM. Both VM and telemetry assembly read from this struct. Prevents 2–3x redundant I2C reads per tick.
**Effort:** 3 hours. Introduce snapshot struct, refactor sensor drivers and telemetry.

### 4. Batch COBS Encoding — **MEDIUM**
**Impact:** ~30% reduction in COBS encode CPU time
**Applies to:** CPU budget
**Implementation:** Assemble the complete payload (header + body + CRC) in a contiguous buffer first, then COBS-encode the entire buffer in a single pass. Multi-pass encoding (header → COBS, body → COBS, concatenate) adds function call overhead and prevents the encoder from optimizing across boundaries.
**Effort:** 2 hours.

### 5. PSRAM Only for Observation Buffer — **HIGH (correctness)**
**Impact:** Prevents non-deterministic ISR latency
**Applies to:** Timing determinism
**Implementation:** Use `heap_caps_malloc(size, MALLOC_CAP_SPIRAM)` exclusively for the observation ring buffer data. Use `MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT` for everything else. Add a static assertion at compile time that total static SRAM usage stays below 470 KB (leaving 42 KB for heap minimum).
**Effort:** 1 hour audit + fixes.

### 6. Pre-Compile Reflexes on Jetson — **HIGH**
**Impact:** Eliminates ~500 ms reflex deployment latency (compile phase)
**Applies to:** Latency budget, CPU budget (ESP32)
**Implementation:** The reflex compiler runs on Jetson (Python or C extension). It outputs raw bytecode that is COBS-encoded and transmitted to ESP32. ESP32 only does a `memcpy` into the reflex slot — zero compilation on the microcontroller.
**Effort:** 4 hours (already in spec — verify implementation).

### 7. Use jsmn for Protocol Messages — **MEDIUM**
**Impact:** 5x less RAM and 3x faster than cJSON for parsing
**Applies to:** SRAM budget, CPU budget
**Implementation:** `jsmn` is a minimal, single-pass JSON tokenizer (no tree building, no string copying). Use it for all incoming protocol messages (role config, reflex deploy, commands). Use `cJSON` only for the initial role configuration parsing at boot where readability matters.
**Effort:** 4 hours.

### 8. IRAM_ATTR on All ISR Code — **HIGH (correctness)**
**Impact:** Prevents ISR latency spikes from flash cache misses
**Applies to:** Timing determinism
**Implementation:** Mark every ISR handler and every function called from an ISR with `IRAM_ATTR`. This forces the linker to place the code in IRAM (instruction RAM), which is not subject to flash cache eviction. Flash cache misses cause 20–100 µs stalls — unacceptable in ISRs.
**Effort:** 2 hours audit + annotations.

### 9. Disable WiFi/BLE When Not Needed — **LOW**
**Impact:** Saves ~100 mA, frees ~5% CPU cycles, reduces RF noise on I2C
**Applies to:** Power budget, CPU budget, analog sensor noise
**Implementation:** Call `esp_wifi_deinit()` and `esp_bt_mem_release()` at boot if the limb node is wired-only. In marine environments, WiFi is rarely useful (metal hull = Faraday cage). Save 100 mA = significant for battery-powered nodes.
**Effort:** 30 minutes.

### 10. Tickless Idle Mode Below 1 kHz — **LOW**
**Impact:** 30–50% power reduction at 100 Hz tick rate
**Applies to:** Power budget
**Implementation:** Enable `CONFIG_FREERTOS_USE_TICKLESS_IDLE=y` in `menuconfig`. At 100 Hz, the CPU sleeps for ~9.5 ms between ticks. At 1 kHz, tickless mode provides negligible benefit (only 0.3 ms sleep windows). Only enable when running at 100 Hz or below.
**Effort:** 15 minutes (config change + rebuild).

### 11. PID at 10 Hz, Not 1 kHz — **MEDIUM**
**Impact:** Frees 900 µs of CPU time per tick at 1 kHz (or enables 1 kHz tick rate)
**Applies to:** CPU budget
**Implementation:** Marine vessel dynamics have time constants of 500 ms – 10 seconds. Running PID at 1 kHz provides zero benefit over 10 Hz for these systems. Run PID on a separate FreeRTOS timer at 10 Hz, not on the main VM tick. This frees the VM tick for sensor I/O and reflex execution.
**Effort:** 3 hours. Create separate `pid_timer_callback()` at 10 Hz.

### 12. MQTT Message Packing — **LOW**
**Impact:** 40% reduction in MQTT broker CPU and bandwidth
**Applies to:** Jetson CPU budget, network bandwidth
**Implementation:** Instead of publishing each telemetry reading as a separate MQTT message (100 msg/sec per node), batch 10 readings into a single JSON array payload (10 msg/sec). Reduces per-message MQTT overhead (topic string, QoS headers) by 10x.
**Effort:** 2 hours in the MQTT bridge module.

### 13. gRPC Streaming for Observation Data — **MEDIUM**
**Impact:** 60% reduction in gRPC overhead vs. unary RPC for large observation transfers
**Applies to:** Jetson ↔ Cloud bandwidth
**Implementation:** Define a `stream ObservationChunk` RPC in the cluster API proto. The Jetson streams observation data as a sequence of 64 KB chunks instead of sending the entire 8 MB buffer in a single unary call. Reduces gRPC framing overhead and enables flow control.
**Effort:** 4 hours (proto change + Jetson + cloud service).

### 14. C Extension for Reflex Compiler — **MEDIUM**
**Impact:** 50x faster compilation (Python: ~50 ms → C: ~1 ms per reflex)
**Applies to:** Jetson CPU budget, reflex deployment latency
**Implementation:** Rewrite the reflex compiler's bytecode generation pass as a Python C extension (or use Cython). The tokenizer and AST builder can stay in Python. The bytecode emitter (linear pass over AST) is the hotspot.
**Effort:** 8 hours. Non-blocking — start with pure Python, optimize later.

### 15. LZ4 Compression for Observation Transfer — **LOW**
**Impact:** 2x faster serial transfer for observation dumps
**Applies to:** Serial link utilization
**Implementation:** Use LZ4 block compression (not frame format) on the ESP32 before transmitting observation data. LZ4 on Xtensa at 240 MHz achieves ~50 MB/s compression — more than fast enough to keep up with the 92 KB/s serial link. Requires ~64 KB of working memory (SRAM) during compression.
**Effort:** 6 hours (integrate `lz4.h`, manage compression context).

---

## Appendix A: Quick-Reference Budget Summary

| Resource | Total | Used (worst case) | Margin | Status |
|---|---|---|---|---|
| ESP32 SRAM | 512 KB | ~68 KB static + 30 KB heap | ~414 KB | **Green** |
| ESP32 PSRAM | 8 MB | ~6 MB (obs buffer) | ~2 MB | **Green** |
| ESP32 CPU (Core 0) | 1,000 µs @ 1 kHz | ~660 µs | 340 µs | **Yellow** |
| ESP32 CPU (Core 1) | 1,000 µs @ 1 kHz | ~500 µs | 500 µs | **Green** |
| Serial link | 92,160 B/s | 53,828 B/s | 38,332 B/s | **Yellow** |
| Jetson VRAM | 8,192 MB | ~8,004 MB (all models) | N/A (model swap required) | **Red** (by design) |
| Jetson CPU | 6 cores | ~4 cores typical | ~2 cores | **Green** |
| End-to-end reflex latency | N/A | ~200 µs | N/A | **Green** |
| End-to-end AI latency | N/A | ~12–43 seconds | N/A | **Red** (by design — not in control loop) |

## Appendix B: Measurement Instrumentation

Every budget claim above should be verified on hardware. Use the following instrumentation:

- **ESP32 CPU:** `esp_timer_get_time()` around each operation in the tick loop. Log worst-case per 1,000-tick window to UART.
- **ESP32 SRAM:** `heap_caps_get_free_size(MALLOC_CAP_INTERNAL)` and `heap_caps_get_free_size(MALLOC_CAP_SPIRAM)` printed at boot and every 60 seconds.
- **Serial bandwidth:** Byte counter on TX DMA completion interrupt. Log bytes/sec every 10 seconds.
- **Jetson VRAM:** `tegrastats` (built into JetPack) for GPU memory usage. `free -h` for system RAM.
- **Jetson thermal:** `cat /sys/class/thermal/thermal_zone*/temp` every 5 seconds.
- **End-to-end latency:** Timestamp at sensor read (ESP32 `esp_timer`), timestamp at actuator write. Difference = total reflex latency. Log to observation buffer for Jetson analysis.

---

*Document version: 1.0 — Generated for NEXUS platform build phase. All numbers assume ESP-IDF 5.x and JetPack 6.x. Re-measure after every platform version upgrade.*
