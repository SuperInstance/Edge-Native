# NEXUS Wire Protocol — Reliability Analysis

**Document ID:** NEXUS-ANALYSIS-WIRE-001
**Round:** 1C
**Date:** 2025-07-12
**Status:** Deep Technical Analysis

---

## 1. COBS Framing Efficiency Analysis

### 1.1 COBS Overhead Model

COBS (Consistent Overhead Byte Stuffing) encoding inserts a count byte for every run of non-zero bytes, with each run terminated by a zero byte in the decoded stream. The worst-case overhead is 1 extra byte per 254 bytes of payload, yielding a maximum expansion ratio of:

$$r_{max} = \frac{N + \lceil N/254 \rceil}{N} = 1 + \frac{1}{254} \approx 1.00394$$

The best case (payload is all zeros) yields zero overhead, as each zero byte maps directly to a framing delimiter. The expected overhead depends on the distribution of zero bytes in the payload.

### 1.2 Payload Size Distribution Across 28 Message Types

| Category | Message IDs | Typical Payload Size | Frame Overhead | Notes |
|----------|------------|---------------------|----------------|-------|
| Null/Keepalive | 0x05 HEARTBEAT, 0x16 PING, 0x17 PONG | 0 bytes | 2 delimiters + 1 COBS + 10 header + 2 CRC = 15 bytes | Highest per-byte overhead (infinite) |
| Identity/Boot | 0x01 DEVICE_IDENTITY, 0x04 SELFTEST, 0x1B AUTO_DETECT | 100–500 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.4–2.1% overhead |
| Role Mgmt | 0x02 ROLE_ASSIGN, 0x03 ROLE_ACK | 50–300 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.5–1.6% |
| Telemetry | 0x06 TELEMETRY, 0x19 CLOUD_CTX_REQ, 0x1A CLOUD_RESULT | 50–800 bytes JSON/binary | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.4–1.5% |
| Commands | 0x07 COMMAND, 0x08 CMD_ACK, 0x10 IO_RECONFIGURE | 20–200 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.7–3.3% |
| Reflex Engine | 0x09 REFLEX_DEPLOY, 0x0A REFLEX_STATUS | 100–600 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.4–2.1% |
| Observation | 0x0B–0x0F (5 types) | 0–1024 bytes (binary chunks) | 12 + N + ⌈(N+12)/254⌉ + 2 | Binary chunks near 1024B: 0.4% |
| Firmware OTA | 0x11–0x14 (4 types) | 0–520 bytes | 12 + N + ⌈(N+12)/254⌉ + 2 | Chunk: 516B → 0.6% |
| Error/Safety | 0x15 ERROR, 0x1C SAFETY_EVENT | 50–200 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 0.7–3.3% |
| Baud Mgmt | 0x18 BAUD_UPGRADE | ~20 bytes JSON | 12 + N + ⌈(N+12)/254⌉ + 2 | 2.7% |

### 1.3 Expected Overhead in Practice

For typical JSON payloads (UTF-8 encoded), zero bytes are rare. ASCII text contains no zero bytes by definition. Binary payloads (firmware chunks, observation frames) have an expected zero-byte density of approximately 1/256 per byte.

**For JSON payloads (no zero bytes):**
- Every 254 bytes of decoded data produces exactly 255 bytes of COBS-encoded data
- Overhead = ⌈(N + 12)/254⌉ bytes per frame
- For a 200-byte JSON payload: (200+12+2+12)/254 ≈ 1 byte COBS overhead → **0.48%**

**For binary payloads (random data with p=1/256 zeros):**
- Expected COBS expansion factor ≈ 1 + 1/254 × (1 - p) ≈ **0.39%**

**Frame efficiency summary:**

| Metric | Value |
|--------|-------|
| Worst-case COBS overhead | 0.394% (all non-zero payload) |
| Average COBS overhead (JSON) | 0.15% (small payloads) to 0.40% (large payloads) |
| Fixed per-frame overhead | 15 bytes (2 delimiters + 10 header + 2 CRC + 1 COBS count) |
| Maximum frame efficiency | 98.6% (1024-byte binary payload) |
| Minimum frame efficiency | 0% (null payload — 15 bytes overhead for 0 data) |

### 1.4 Comparison with Alternative Framing

| Framing | Overhead | Zero Handling | Self-Syncing | Complexity |
|---------|----------|---------------|--------------|------------|
| COBS | ~0.4% max | Excellent | Yes (0x00 delimiter) | Very Low |
| SLIP | ~1/128 = 0.78% max | Good | Yes (END = 0xC0) | Low |
| HDLC-like | ~0.4% (bit-stuffing) | Good | Yes (0x7E flag) | Medium |
| Length-prefixed | 2–4 bytes fixed | N/A | No | Very Low |
| JSON-delimited | Variable (JSON structure) | Complex | Partial | High |

COBS is an optimal choice for this protocol: minimal overhead, self-synchronizing decoder, and simple implementation suitable for bare-metal firmware.

---

## 2. CRC-16 Collision Probability Analysis

### 2.1 CRC-16/CCITT-FALSE Parameters

- Polynomial: 0x1021 (x¹⁶ + x¹² + x⁵ + 1)
- Initial value: 0xFFFF
- Final XOR: 0x0000
- No input/output reflection
- Check value for "123456789": 0x29B1

### 2.2 Collision Probability — Birthday Problem

The CRC-16 checksum space is 2¹⁶ = 65,536 possible values. For two arbitrary messages to have the same CRC:

$$P(\text{collision for 2 messages}) = \frac{1}{65536} \approx 1.53 \times 10^{-5}$$

**Birthday bound:** For n messages, the probability of at least one CRC collision among any pair is:

$$P(\text{collision among } n) \approx 1 - e^{-n^2 / (2 \times 65536)}$$

| Number of Messages (n) | Collision Probability |
|----------------------|----------------------|
| 10 | 0.076% |
| 50 | 1.89% |
| 100 | 7.45% |
| 200 | 26.4% |
| 256 | 39.4% |
| 303 | ≈50% |
| 500 | 78.3% |
| 1000 | 99.9% |

### 2.3 Collision Probability in Context

In the NEXUS protocol, CRC collisions matter in two scenarios:

**Scenario A: Random noise corruption**
A single corrupted frame must produce the same CRC as the original. Since the CRC-16 has Hamming distance ≥ 3 for all error patterns of weight ≤ 3, and the polynomial is known to have Hamming distance 4 for all data lengths ≤ 32767 bytes:
- Any 1-bit error is always detected (100%)
- Any 2-bit error is always detected (100%)
- Any 3-bit error is always detected (100%)
- Some 4-bit errors may be undetected: probability ≈ 2⁻¹⁶ per specific 4-bit pattern

The **undetected error rate** for random bit errors with BER = p is approximately:

$$P_{UE} \approx \frac{1}{2^{16}} \times \binom{n}{4} p^4 (1-p)^{n-4}$$

For a 200-byte (1600-bit) frame at BER = 10⁻⁴:

$$P_{UE} \approx \frac{1}{65536} \times \binom{1600}{4} (10^{-4})^4 \approx 1.5 \times 10^{-5} \times 10^{12} \times 10^{-16} \approx 1.5 \times 10^{-9}$$

This is negligible for safety-critical operation.

**Scenario B: Malicious CRC collision (adversarial)**
An attacker who can modify payload bytes while preserving CRC can do so with approximately 2¹⁶ operations (brute force). This is trivially computable. **CRC-16 provides no cryptographic integrity.** See Section 8 for mitigation recommendations.

### 2.4 Comparison with Stronger Checksums

| Checksum | Width | Undetected Error Rate (random) | Collision Resistance | Computation Cost |
|----------|-------|-------------------------------|---------------------|-----------------|
| CRC-16/CCITT | 16-bit | ~2⁻¹⁶ | None (cryptographic) | ~10 cycles/byte (table) |
| CRC-32/ISO | 32-bit | ~2⁻³² | None | ~15 cycles/byte |
| Fletcher-16 | 16-bit | ~2⁻¹⁵ (worse than CRC) | None | ~5 cycles/byte |
| Adler-32 | 32-bit | ~2⁻¹⁶ (weaker than CRC-32) | None | ~8 cycles/byte |
| HMAC-SHA256 | 256-bit | ~2⁻²⁵⁶ | 2¹²⁸ | ~500 cycles/byte |
| AES-GCM (128) | 128-bit | ~2⁻¹²⁸ | 2⁶⁴ | ~200 cycles/byte |

**Assessment:** CRC-16 is adequate for detecting random/corruption errors in a point-to-point serial link with hardware-level ESD protection and RS-422 differential signaling. It is NOT adequate for detecting malicious tampering. The protocol's existing `ENCRYPTED` flag bit (bit 5) with AES-128-CTR provides the necessary integrity protection when enabled, but AES-CTR alone does not authenticate — a MAC or AES-GCM would be needed for full integrity.

---

## 3. Throughput Analysis

### 3.1 Raw Bit Rates and Effective Data Rates

UART with 8N1 framing: 10 bits per byte (8 data + 1 start + 1 stop).

| Baud Rate | Raw Bit Rate | Byte Rate (8N1) | Max Throughput (COBS) | Max Frames/sec (1024B) | Max Frames/sec (100B) |
|-----------|-------------|-----------------|----------------------|------------------------|----------------------|
| 115,200 | 115.2 kbps | 11,520 B/s | ~11,475 B/s | ~10.9 fps | ~76.5 fps |
| 460,800 | 460.8 kbps | 46,080 B/s | ~45,897 B/s | ~43.5 fps | ~306 fps |
| 921,600 | 921.6 kbps | 92,160 B/s | ~91,794 B/s | ~87.0 fps | ~612 fps |

### 3.2 Effective Throughput with Protocol Overhead

Per-frame overhead at 921,600 baud:
- Start/stop delimiters: 2 bytes = 20 bits
- COBS encoding overhead: ~1 byte per 254 bytes
- CRC-16: 2 bytes
- Header: 10 bytes
- UART framing: 10 bits/byte

**For a 100-byte JSON telemetry payload:**
- Decoded frame: 10 (header) + 100 (payload) + 2 (CRC) = 112 bytes
- COBS-encoded: 112 + ⌈112/254⌉ = 113 bytes
- Wire frame: 1 + 113 + 1 = 115 bytes
- UART bits: 115 × 10 = 1,150 bits
- Time at 921,600: 1,248 μs ≈ 1.25 ms
- **Effective rate: ~80 telemetry messages/sec**

**For a 516-byte firmware chunk:**
- Decoded: 10 + 516 + 2 = 528 bytes
- COBS: 528 + ⌈528/254⌉ = 530 bytes
- Wire: 532 bytes → 5,320 bits → 5.77 ms
- **Effective rate: ~173 chunks/sec → ~88 MB/s firmware transfer**

### 3.3 Message Mix Scenarios

**Scenario A: Normal Operation (nominal traffic)**
| Message | Rate | Avg Payload | Bytes/sec (wire) | Baud Utilization |
|---------|------|-------------|-----------------|-----------------|
| HEARTBEAT (N→J) | 1/sec | 0 | 150 | 0.16% |
| TELEMETRY (N→J) | 10/sec | 100B | 11,500 | 12.5% |
| COMMAND_ACK (N→J) | 5/sec | 30B | 2,300 | 2.5% |
| PING/PONG (both) | 0.1/sec | 0 | 15 | 0.02% |
| **Total N→J** | | | **13,965** | **15.2%** |
| COMMAND (J→N) | 5/sec | 50B | 3,450 | 3.7% |
| REFLEX_DEPLOY (J→N) | 0.01/sec | 200B | 23 | 0.03% |
| **Total J→N** | | | **3,473** | **3.8%** |
| **Grand Total** | | | **17,438** | **19.0%** |

**Scenario B: Observation Recording (high throughput)**
| Message | Rate | Avg Payload | Bytes/sec (wire) | Baud Utilization |
|---------|------|-------------|-----------------|-----------------|
| OBS_DUMP_CHUNK (N→J) | 100/sec | 516B | 53,200 | 58.0% |
| OBS_DUMP_HEADER (N→J) | 1/sec | 50B | 65 | 0.07% |
| OBS_DUMP_END (N→J) | 1/sec | 20B | 41 | 0.04% |
| TELEMETRY (N→J) | 1/sec | 100B | 115 | 0.13% |
| HEARTBEAT | 1/sec | 0 | 15 | 0.02% |
| **Total** | | | **53,436** | **58.3%** |

**Scenario C: OTA Firmware Update (maximum throughput)**
| Message | Rate | Avg Payload | Bytes/sec (wire) | Baud Utilization |
|---------|------|-------------|-----------------|-----------------|
| FW_UPDATE_CHUNK (J→N) | 173/sec | 516B | 92,036 | 100.2% |
| FW_UPDATE_START/END | 0.01/sec | 50B | 0.5 | <0.01% |
| COMMAND_ACK (N→J) | 173/sec | 10B | 1,990 | 2.2% |
| **Total** | | | **94,027** | **102.4%** |

At 921,600 baud, OTA firmware transfer is bandwidth-limited. The protocol can sustain approximately **88 KB/s** of firmware data throughput (accounting for all overheads). For a 1 MB firmware image, this yields an update time of approximately **11.4 seconds**.

### 3.4 Baud Rate Degradation

At 115,200 baud (maximum range):
- OTA throughput: ~11 KB/s → 1 MB update in **91 seconds**
- Observation recording: limited to ~13 chunks/sec → impractical for high-rate recording
- Normal operation: 19% utilization → still comfortable headroom

---

## 4. Latency Analysis

### 4.1 End-to-End Message Path

The complete path from application message creation to reception by the remote application:

```
[Application] → [Serialize] → [CRC Compute] → [COBS Encode] → [UART TX FIFO]
     → [RS-422 Driver] → [Cable] → [RS-422 Receiver] → [UART RX FIFO]
     → [Frame Detect] → [COBS Decode] → [CRC Verify] → [Dispatch] → [Application]
```

### 4.2 Per-Stage Latency Budget

| Stage | Time (921,600) | Time (115,200) | Notes |
|-------|---------------|---------------|-------|
| **Serialize** (JSON→bytes) | 5–50 μs | 5–50 μs | Depends on payload complexity |
| **CRC-16 compute** | 1–5 μs | 1–5 μs | Table-based: ~10 cycles/byte |
| **COBS encode** | 1–3 μs | 1–3 μs | Single pass, ~5 cycles/byte |
| **UART TX FIFO → driver** | 0.1 μs | 0.1 μs | DMA or interrupt-driven |
| **Wire propagation** | 0.04 μs/m | 0.04 μs/m | RS-422: ~0.67c propagation |
| **UART RX → frame detect** | 0.1 μs | 0.1 μs | Hardware UART |
| **COBS decode** | 1–3 μs | 1–3 μs | Single pass |
| **CRC verify** | 1–5 μs | 1–5 μs | Same as compute |
| **Dispatch** | 1–10 μs | 1–10 μs | Message type switch + handler |
| **UART serialization** | N × 10.85 μs | N × 86.8 μs | N = wire frame bytes |
| **UART deserialization** | N × 10.85 μs | N × 86.8 μs | |

### 4.3 Total Latency Examples

**Ping/Pong (0-byte payload) at 921,600:**
- Wire frame: 15 bytes → UART time: 15 × 10.85 = 163 μs
- Processing: ~15 μs per side
- Cable (10m): ~0.05 μs (negligible)
- One-way latency: ~178 μs
- Round-trip: **~356 μs**

**Command (50-byte JSON payload) at 921,600:**
- Wire frame: 10+50+2+1+2 = 65 bytes → 705 μs UART
- Processing: ~60 μs
- One-way latency: **~765 μs**
- Round-trip with ACK (30-byte): **~1.6 ms**

**Telemetry (200-byte JSON) at 921,600:**
- Wire frame: 10+200+2+1+2 = 215 bytes → 2,333 μs UART
- Processing: ~80 μs
- One-way: **~2.4 ms**

**Firmware chunk (516-byte binary) at 921,600:**
- Wire frame: 10+516+2+1+2 = 531 bytes → 5,762 μs UART
- One-way: **~5.8 ms**

### 4.4 Worst-Case Latency Under Load

When the TX FIFO is full and CTS flow control is asserted:
- The transmitter must wait until the receiver drains its FIFO
- Worst case: full 1024-byte frame being received → 11.1 ms at 921,600
- Plus processing time of the current frame: ~5 ms (JSON parse + handler)
- **Worst-case queuing latency: ~16 ms**

This is within the 200 ms ACK timeout for command messages.

---

## 5. Reliability Under Noise

### 5.1 Bit Error Rate (BER) for RS-422

RS-422 differential signaling provides excellent noise immunity:

| Condition | Typical BER |
|-----------|------------|
| Ideal (laboratory) | 10⁻¹² |
| Good installation (Cat-5e, <10m) | 10⁻⁹ |
| Typical industrial | 10⁻⁷ to 10⁻⁸ |
| Noisy (long cable, EMI) | 10⁻⁵ to 10⁻⁶ |
| Severe EMI / cable damage | 10⁻³ to 10⁻⁴ |

### 5.2 Frame Error Rate (FER)

A frame of N bits is received correctly if all N bits are correct:

$$P(\text{frame error}) = 1 - (1 - BER)^N$$

| Frame Size | BER=10⁻⁵ | BER=10⁻⁶ | BER=10⁻⁷ | BER=10⁻⁸ |
|-----------|----------|----------|----------|----------|
| 150 bytes (PING) | 1.19% | 0.119% | 0.012% | 0.0012% |
| 532 bytes (FW chunk) | 4.17% | 0.419% | 0.042% | 0.0042% |
| 1053 bytes (max frame) | 8.19% | 0.826% | 0.083% | 0.0083% |

### 5.3 Effective Message Error Rate (MER)

After CRC verification, undetected errors (CRC collisions) are vastly rarer:

$$P(\text{undetected error}) \approx P(\text{frame error}) \times 2^{-16}$$

| Frame Size | BER=10⁻⁵ | BER=10⁻⁶ | BER=10⁻⁸ |
|-----------|----------|----------|----------|
| 150 bytes | 1.8 × 10⁻⁷ | 1.8 × 10⁻⁹ | 1.8 × 10⁻¹¹ |
| 532 bytes | 6.4 × 10⁻⁷ | 6.4 × 10⁻⁹ | 6.4 × 10⁻¹¹ |
| 1053 bytes | 1.2 × 10⁻⁶ | 1.3 × 10⁻⁸ | 1.3 × 10⁻¹⁰ |

**Assessment:** With CRC-16, the probability of an undetected corrupted message is below 10⁻⁶ even under severe noise conditions (BER=10⁻⁵). For typical industrial conditions (BER=10⁻⁷), undetected errors are below 10⁻¹⁰ — approximately one undetected error every 317 years of continuous operation at 100 messages/second.

### 5.4 COBS Self-Synchronization Under Errors

COBS provides an important robustness property: after any byte error, the decoder re-synchronizes at the next 0x00 delimiter. This limits error propagation to a single frame — a corrupted frame does not corrupt subsequent frames. This is superior to length-prefixed framing, where a corrupted length field can cause the decoder to misparse all subsequent data until a power cycle.

However, COBS cannot detect all encoding errors. A corrupted COBS count byte may cause the decoder to misinterpret the payload boundaries, potentially producing a payload that passes CRC verification. This is extremely unlikely (requires a specific pattern of corruption) but theoretically possible.

### 5.5 Retry Effectiveness

With the protocol's retry policy (3 retries, exponential backoff 200/400/800 ms):

$$P(\text{delivery failure}) = P(\text{frame error})^4$$

For BER=10⁻⁶ and 200-byte frames: (0.159%)⁴ = 6.4 × 10⁻⁹

This means approximately one delivery failure every 44 years of continuous operation at 10 critical messages/second. **The retry mechanism provides sufficient reliability for all non-catastrophic noise conditions.**

---

## 6. Comparison with Alternative Protocols

### 6.1 CAN Bus

| Property | NEXUS Serial (RS-422) | CAN 2.0B | CAN FD |
|----------|----------------------|-----------|--------|
| Max data rate | 921.6 kbps | 1 Mbps | 8 Mbps |
| Max payload | 1024 bytes | 8 bytes | 64 bytes |
| Framing overhead | ~1.5% | ~40% (bit stuffing + CRC + EOF) | ~15% |
| Error detection | CRC-16 | CRC-15 (Hamming d=6) | CRC-17/CRC-21 |
| Multi-master | No (star topology) | Yes (bus) | Yes |
| Addressing | Implicit (point-to-point) | 11/29-bit ID | 11/29-bit ID |
| Cable length | 100m @ 115.2k | 500m @ 125k | 30m @ 8M |
| Cost (transceiver) | ~$1.50 (THVD1500) | ~$1.00 (TJA1050) | ~$2.00 |
| MCU support | Universal (UART) | Dedicated peripheral | Dedicated peripheral |
| Topology | Point-to-point (star) | Multi-drop bus | Multi-drop bus |

**Verdict:** CAN bus is superior for multi-drop sensor networks but limited by 8-byte (CAN 2.0) or 64-byte (CAN FD) payloads. NEXUS serial supports larger payloads and simpler point-to-point wiring. CAN's built-in bus arbitration and priority mechanism are unnecessary for NEXUS's star topology.

### 6.2 Ethernet (10/100 Mbps)

| Property | NEXUS Serial | 100BASE-TX Ethernet |
|----------|-------------|---------------------|
| Data rate | 0.9216 Mbps | 100 Mbps |
| Latency | 0.2–6 ms | 0.05–1 ms |
| Max payload | 1024 bytes | 1500 bytes (MTU) |
| Cable length | 100m | 100m |
| Cost | ~$2 (transceiver + connector) | ~$5 (PHY + magnetics + connector) |
| MCU requirement | UART (universal) | MAC + PHY (not on all MCUs) |
| Power | ~50 mW | ~200 mW |
| Protocol stack | Custom (tiny) | TCP/IP (heavy) |
| Determinism | High (no CSMA/CD) | Moderate (switched: good; shared: poor) |

**Verdict:** Ethernet provides 100× more bandwidth but at 5× cost and 4× power. For NEXUS's use case (<100 KB/s sustained), serial is more efficient. Ethernet would be justified only if the same link carried video, bulk data logging, or connected >10 nodes.

### 6.3 MQTT-over-WebSocket

| Property | NEXUS Serial | MQTT/WS |
|----------|-------------|---------|
| Transport | RS-422 point-to-point | TCP/IP over WiFi/Ethernet |
| Latency | 0.2–6 ms | 10–100 ms (WiFi) |
| Overhead | ~15 bytes/frame | 40+ bytes TCP + 20+ bytes MQTT |
| Reliability | CRC-16 + retry | TCP retransmission + QoS |
| Topology | Star (Jetson hub) | Pub/Sub (broker required) |
| Broker dependency | None | Mosquitto/HiveMQ required |
| Security | Optional AES-128 | TLS 1.2/1.3 (built-in) |
| Determinism | High | Low (TCP congestion control) |

**Verdict:** MQTT provides better security (TLS), flexible pub/sub topology, and cloud connectivity, but at the cost of 10–100× higher latency and non-deterministic timing. For real-time reflex control (<10 ms loop), NEXUS serial is strongly preferred. MQTT could serve as a complementary cloud-facing protocol.

---

## 7. Protocol Extension Analysis: Message Types 29–50

### 7.1 Current Allocation

| Range | Allocation | Used |
|-------|-----------|------|
| 0x00 | Null/reserved | 1 |
| 0x01–0x1C | Core NEXUS (28 types) | 28 |
| 0x1D–0x7F | Reserved for future NEXUS core | 99 available |
| 0x80–0xFF | Node-extensions | 128 available |

### 7.2 Impact of Adding Message Types 29–50 (0x1D–0x3A)

Adding 22 new message types within the 0x1D–0x3A range requires:

1. **Firmware update** on all nodes to recognize new type codes
2. **Jetson software update** to generate/handle new messages
3. **Specification revision** documenting new message formats

**No protocol-level changes are needed.** The single-byte msg_type field supports values 0x00–0xFF, and the reserved range 0x1D–0x7F provides 99 slots for core extensions. Adding 22 types consumes only 22% of this reserve.

### 7.3 Compatibility Concerns

- **Old firmware receiving new message type:** The node will emit `UNKNOWN_MSG_TYPE` (0x5006) warning and discard the message. No crash or undefined behavior.
- **New firmware receiving only old message types:** Fully backward compatible — no change in behavior.
- **Mixed-version fleet:** The Jetson should query DEVICE_IDENTITY to determine firmware version before sending new message types. The protocol already includes firmware version in DEVICE_IDENTITY.

### 7.4 Practical Extension Limits

| Extension Type | Available Slots | Impact |
|---------------|----------------|--------|
| New core message types | 99 (0x1D–0x7F) | Requires spec update |
| Node-specific extensions | 128 (0x80–0xFF) | Per-deployment, no spec change |
| Payload extensions | Unlimited (within 1024B) | Backward compatible via schema versioning |
| Header extensions | None (10 bytes fixed) | Would require protocol version bump |

**The protocol can absorb 99 new core message types without any structural changes.** This is a well-designed extensibility model.

---

## 8. Security Analysis

### 8.1 Message Injection

**Threat:** An attacker with physical access to the RS-422 bus can inject arbitrary messages.

**Attack surface:**
- No authentication: any device that can transmit on the bus can send valid messages
- No message origin verification: the receiver trusts all received messages
- COMMAND (0x07) can directly control actuators
- REFLEX_DEPLOY (0x09) can upload arbitrary bytecode
- FIRMWARE_UPDATE_START/CHUNK/END can replace firmware

**Impact:** CRITICAL — full control of the node, including actuator manipulation, firmware replacement, and safety system override.

**Mitigations (current):**
- Physical access required (RS-422 point-to-point, not accessible remotely)
- Hardware flow control (CTS/RTS) provides minimal protection
- FIRMWARE_UPDATE_END requires SHA-256 hash verification

**Recommendations:**
1. Implement per-session key exchange on first connection
2. Use the existing `ENCRYPTED` flag (bit 5) with AES-128-GCM (not just CTR) for authentication
3. Add a sequence number MAC to prevent replay (see 8.2)
4. Critical commands (FIRMWARE_UPDATE, ROLE_ASSIGN) should require a secondary authorization token

### 8.2 Replay Attacks

**Threat:** An attacker records a valid message and re-transmits it later.

**Current protection:**
- Sequence numbers (uint16) with sliding window validation
- Timestamps (uint32 ms) for freshness checking
- DUPLICATE_SEQUENCE detection

**Weaknesses:**
1. **Sequence number is uint16:** Wraps at 65,536. At 100 messages/second, wraps in ~655 seconds (~11 minutes). After wrap, old messages with the same sequence number will be accepted if within the sliding window.
2. **No per-direction authentication:** An attacker can replay Node→Jetson messages back to the Node. The sequence number window is independent per direction, but a reflected COMMAND_ACK could be replayed.
3. **Timestamp is sender-local:** No clock synchronization mechanism. A replayed message with a stale timestamp will only be detected if the receiver tracks "last valid timestamp."
4. **Window size is 8:** After 8 messages, old sequence numbers are forgotten. A message from 8+ messages ago can be replayed successfully.

**Replay window:**

| Message Rate | Sequence Wrap Time | Replay Window (8 messages) |
|-------------|-------------------|---------------------------|
| 10 msg/s | 109 min | 0.8 s |
| 100 msg/s | 10.9 min | 0.08 s |
| 1000 msg/s | 65.5 s | 0.008 s |

**Assessment:** For typical NEXUS traffic (10–100 msg/s), the replay window is 0.08–0.8 seconds. A replayed command within this window could cause a duplicate actuator action. For example, a repeated "extend actuator" command could cause mechanical damage.

**Recommendation:** Add a per-message nonce or monotonic timestamp with minimum inter-message time enforcement. Or implement a small replay cache (256 entries) keyed by (msg_type, sequence_number).

### 8.3 Sequence Number Attacks

**Threat:** An attacker manipulates sequence numbers to disrupt protocol operation.

**Attack 1: Sequence number reset**
- Force both sides to wrap sequence numbers by injecting many messages
- After wrap, old cached sequence numbers are no longer valid
- Allows replay of previously-seen messages

**Attack 2: Sequence number gap**
- Inject a message with a high sequence number (e.g., last_seen + 256)
- Receiver resets `last_seen` per validation rule 4 ("Severe gap")
- This enables replay of messages with sequence numbers in the old range

**Attack 3: Sequence number desynchronization**
- If only one direction's sequence numbers are manipulated, the sliding windows become misaligned
- The ACK mechanism echoes the sender's sequence number, so desynchronization is detectable

**Assessment:** The sequence number mechanism provides basic gap detection but is not a security feature. It is designed for reliability (detecting dropped messages), not authentication.

### 8.4 Firmware Update Attack

**Threat:** An attacker initiates a firmware update with a malicious image.

**Current protection:**
- SHA-256 hash verification in FIRMWARE_UPDATE_END
- 3-phase update: START → CHUNK(s) → END → RESULT
- Partition-based update (A/B partition scheme implied by rollback mechanism)

**Weakness:**
- SHA-256 hash is transmitted in FIRMWARE_UPDATE_START as plaintext JSON
- An attacker who controls the link can replace both the firmware chunks AND the expected hash
- The hash verification only protects against accidental corruption, not malicious replacement

**Recommendation:** Pre-share a firmware signing public key on each node. Firmware images must be signed (Ed25519 or ECDSA), and the node verifies the signature before applying the update. The hash can then serve as an optimization for chunk-level integrity.

---

## 9. Open Questions for Round 2

1. **COBS performance on real hardware:** What is the actual COBS encode/decode throughput on ESP32-S3 with DMA-assisted UART? The theoretical analysis assumes CPU-driven byte-by-byte processing.

2. **CRC-16 collision under adversarial conditions:** Can we construct two valid NEXUS messages with identical CRC-16 that produce different behavior? What is the minimum number of byte flips needed?

3. **COBS + CRC interaction:** Does the COBS encoding transformation affect the CRC's error detection properties? Specifically, does a single-byte corruption in the COBS-encoded stream always produce a different decoded payload?

4. **Throughput with interleaved messages:** What is the maximum sustainable bidirectional throughput when safety messages preempt observation dump chunks? The current analysis assumes unidirectional flow.

5. **Flow control latency impact:** How much does CTS/RTS flow control add to worst-case latency? The 2-second timeout suggests long flow-control pauses are possible. What causes them?

6. **Baud rate switching reliability:** What is the failure rate of baud upgrade negotiation in practice? How does the 500ms verification window compare to actual UART re-synchronization time?

7. **Message priority inversion:** Can a burst of bulk (priority 3) messages starve critical (priority 1) messages if the transmitter processes queues in a naive round-robin?

8. **Heartbeat timeout sensitivity:** The 3-miss escalation to FAILSAFE is aggressive for a noisy link. Should the threshold be adaptive based on measured link quality?

9. **AES-128-CTR integrity gap:** The `ENCRYPTED` flag specifies AES-128-CTR, which provides confidentiality but not authentication. An attacker who knows the plaintext structure can flip bits in predictable ways. Should this be upgraded to AES-GCM?

10. **Sequence number recovery after extended outage:** After a communication loss lasting >49.7 days (timestamp wrap), both sequence numbers and timestamps have wrapped. What is the correct recovery procedure?

11. **Multi-node synchronization:** With >10 nodes connected to a single Jetson, what is the maximum aggregate bandwidth? Does the Jetson's UART multiplexer introduce head-of-line blocking?

12. **Formal verification of frame reception algorithm:** The COBS decoder in Section 2.6 should be verified for all possible byte sequences. Has this been done with a fuzzer or formal proof tool?
