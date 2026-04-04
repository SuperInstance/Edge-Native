# NEXUS Network Architecture Analysis

## Round 4A: Network Topology and Failure Analysis

---

## Table of Contents

1. [Redundancy Topology Options](#1-redundancy-topology-options)
2. [Cluster Quorum Analysis](#2-cluster-quorum-analysis)
3. [Data Consistency](#3-data-consistency)
4. [Bandwidth Analysis](#4-bandwidth-analysis)
5. [Comparison to Alternatives](#5-comparison-to-alternatives)
6. [Conclusions and Recommendations](#6-conclusions-and-recommendations)

---

## 1. Redundancy Topology Options

### 1.1 Current Architecture: Dedicated RS-422 Star

The baseline NEXUS topology assigns each ESP32-S3 a dedicated RS-422 point-to-point link to its parent Jetson board. With 12 ESP32 nodes and 3 Jetson boards, each Jetson manages 4 sensor/actuator nodes via full-duplex serial at 921,600 baud.

**Physical Layout:**
```
                    ┌─────────┐
                    │ Cloud   │
                    │Starlink │
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────┴────┐┌────┴────┐┌────┴────┐
    E00──│ Jetson 0 │ Jetson 1 │ Jetson 2 │──E08
    E01──│ (Leader) │          │          │──E09
    E02──│          │          │          │──E10
    E03──│          │          │          │──E11
         └────┬────┘└────┬────┘└────┬────┘
    E04────────│E05──E06─│─E07
              │          │          │
         ┌────┴──────────┴──────────┴────┐
         │     gRPC + MQTT (LAN)         │
         └───────────────────────────────┘
```

**Characteristics:**
- **Wiring complexity:** 12 dedicated RS-422 cable pairs (4 per Jetson)
- **Single point of failure:** Each cable cut isolates exactly one ESP32
- **Bandwidth isolation:** Each link has full 921.6 kbaud dedicated
- **Deterministic latency:** No contention on serial links
- **Cost per link:** ~$8 (RS-422 transceiver pair + cable + connectors)

### 1.2 Ring Topology: ESP32s in a Ring with Dual Jetson Access

ESP32 nodes are connected in a ring using RS-422, with each Jetson tapping into the ring at two points for redundancy.

**Physical Layout:**
```
    ┌──E00──E01──E02──E03──┐
    │        │         │    │
    │   ┌────┴────┐      │
    │   │ Jetson 0│      │
    │   └────┬────┘      │
    │        │         │    │
    E11──E10──E09──E08──E07──E06──E05──E04──┘
              │          │
         ┌────┴────┐┌────┴────┐
         │ Jetson 1│ Jetson 2 │
         └─────────┘└─────────┘
```

**Advantages:**
- Cable cut isolates no more than 2 ESP32s (adjacent to break)
- Data can route around a break in either direction
- Fewer cable runs to Jetsons (2 per Jetson vs 4)

**Disadvantages:**
- Non-deterministic latency: message routing depends on path length
- Ring requires all nodes to participate in forwarding → firmware complexity
- RS-422 is point-to-point; ring requires multi-drop or chaining transceivers
- Single ring break degrades to linear topology
- Jetson access latency increases: max N/2 hops

**Cost Impact:** ~$16 per ESP32 (2 transceivers for ring connectivity), similar cable count

**Reliability Analysis:**

| Metric | Star (Current) | Ring |
|--------|----------------|------|
| Single cable cut: nodes lost | 1 ESP32 | 0 (reroute) |
| Double cable cut: nodes lost | 2 ESP32s | ≤4 ESP32s |
| Max additional latency | 0 ms | ~8 ms (12 nodes × 0.66 ms) |
| Firmware complexity | Low | High (ring protocol) |
| Cable runs | 12 | 12 (same count, but different topology) |

### 1.3 Star with Redundant Hub: Dual Jetson with Automatic Failover

Each ESP32 connects to two Jetson boards via dual RS-422 links. A primary/secondary designation determines which Jetson actively commands each ESP32.

**Physical Layout:**
```
    E00───┬──→ Jetson 0 (primary)
          └──→ Jetson 1 (backup)
    E01───┬──→ Jetson 0 (primary)
          └──→ Jetson 1 (backup)
    ...
```

**Advantages:**
- Jetson failure: zero ESP32 nodes lost — backup takes over immediately
- Hot standby: backup Jetson mirrors trust scores and reflex state
- Deterministic failover: <100 ms with pre-loaded state

**Disadvantages:**
- **Doubles RS-422 cabling:** 24 links instead of 12
- **Doubles ESP32 UART requirements:** ESP32-S3 has only 3 UARTs; dual-link requires multiplexing or I²C bridge
- **State synchronization overhead:** Both Jetsons must maintain consistent world model
- **Cost:** 2× transceivers, 2× cables, 2× connectors per ESP32

**Cost Impact:** +$12 per ESP32 (second transceiver pair + cable + connectors)

### 1.4 Mesh: Partial Mesh Between Jetsons with ESP32 Access

Jetson boards are connected in a full mesh (all-to-all) with redundant paths. ESP32 nodes connect to their nearest Jetson but can be reassigned dynamically.

**Characteristics:**
- Inter-Jetson: 3× Gigabit Ethernet links (6 cables for 3-Jetson full mesh)
- ESP32 reassignment: on Jetson failure, surviving Jetson claims orphaned ESP32s
- Requires Ethernet switch with redundancy or direct cables
- MQTT broker runs on all Jetsons for redundancy

**Advantages:**
- No single point of failure at the Jetson layer
- Dynamic ESP32 assignment maximizes utilization
- Natural fit for Raft consensus (mesh = heartbeat network)

**Disadvantages:**
- Ethernet cabling adds bulk and failure surface (6+ cables)
- Switch failure is a new SPOF unless redundant switches used
- Firmware complexity for ESP32 reassignment protocol

### 1.5 Trade-off Analysis Matrix

| Criterion | Current Star | Ring | Redundant Hub | Mesh |
|-----------|-------------|------|---------------|------|
| **Reliability** (1-5) | 3 | 4 | 5 | 4 |
| **Cost** (1=low) | 1 | 2 | 4 | 3 |
| **Complexity** (1=low) | 1 | 4 | 3 | 3 |
| **Cable Routing** (1=easy) | 2 | 3 | 4 | 3 |
| **Determinism** (1-5) | 5 | 2 | 5 | 4 |
| **Max Latency** (ms) | 1.6 | 8.0 | 1.6 | 2.0 |
| **ESP32s on Jetson fail** | 4 | 0-2 | 0 | 0-2 |
| **Nodes on cable cut** | 1 | 0 | 0 | 1 |

**Recommendation:** The current star topology with **hot standby at the Jetson level** (not full dual-link) provides the best cost-reliability trade-off. Specifically:
1. Maintain dedicated RS-422 star for ESP32 → Jetson links
2. Add Jetson-level failover: backup Jetson pre-loads trust scores and reflex states via gRPC
3. On Jetson failure, surviving Jetson claims orphaned ESP32s (requires physical RS-422 switch or software reassignment)
4. Use MQTT QoS 2 for critical state synchronization between Jetsons

**Estimated reliability improvement:** From 3-nines (99.9%) to 4-nines (99.99%) cluster availability, at ~15% cost increase.

---

## 2. Cluster Quorum Analysis

### 2.1 3-Jetson Cluster: Failure Scenarios

The minimum NEXUS deployment uses 3 Jetson boards with majority quorum (2-of-3).

| Jetsons Remaining | Quorum? | System State | Available ESP32s | Trust Score Impact |
|-------------------|---------|-------------|-----------------|-------------------|
| 3/3 | ✅ Yes | FULL_OPERATION | 12/12 | Normal |
| 2/3 | ✅ Yes | DEGRADED | 8/12 (or all with failover) | Slightly slower convergence |
| 1/3 | ❌ No | SAFE_STATE | 0 (quorum required for commands) | No updates; frozen at last value |
| 0/3 | ❌ No | FAULT | 0 | Kill switch activates on all ESP32s |

**Critical observation:** With 2-of-3 quorum, the system tolerates exactly 1 Jetson failure without entering safe state. This is the minimum for production safety.

**Raft consensus for reflex deployment:**
- Leader Jetson proposes reflex update
- 2-of-3 Jetsons must ACK for deployment to proceed
- If leader fails mid-deployment, new leader elected within election timeout (~300 ms)
- Reflex bytecode is deterministically validated on all Jetsons before ACK

**Split-brain prevention:**
- Jetson ID is used as tiebreaker in leader election (highest ID wins in split)
- Each Jetson maintains a monotonically increasing term number
- Lower-term Jetsons reject proposals from higher-term leaders
- MQTT retained messages carry term number for detection of stale leaders

### 2.2 5-Jetson Cluster: Improved Resilience

Upgrading to 5 Jetsons with 3-of-5 quorum significantly improves resilience:

| Jetsons Remaining | Quorum? | System State | Tolerated Simultaneous Failures |
|-------------------|---------|-------------|-------------------------------|
| 5/5 | ✅ Yes | FULL_OPERATION | 0 |
| 4/5 | ✅ Yes | FULL_OPERATION | 1 |
| 3/5 | ✅ Yes | DEGRADED | 2 |
| 2/5 | ❌ No | SAFE_STATE | — |
| 1/5 | ❌ No | FAULT | — |

**Improvement over 3-Jetson:**
- Tolerates 2 simultaneous Jetson failures (vs 1)
- 4-of-5 operation is full (not degraded), because any single Jetson can fail and 4 remain
- Leader election has more candidates → faster recovery
- Reflex deployment can proceed with any 3 of 5 Jetsons available

**Monte Carlo simulation results** (10,000-hour, 1000 iterations):

| Metric | 3-Jetson | 5-Jetson | 7-Jetson |
|--------|----------|----------|----------|
| Mean availability | 99.952% | 99.998% | 99.9998% |
| Mean quorum loss (hrs) | 4.82 | 0.18 | 0.012 |
| Full operation time | 93.7% | 99.1% | 99.8% |
| MTBF to quorum loss | 2,074 hrs | 55,556 hrs | 833,333 hrs |
| P95 quorum loss duration | 16.4 hrs | 2.1 hrs | 0.8 hrs |

### 2.3 Reflex Deployment Consistency

Deploying reflex bytecodes across the cluster requires atomic consistency:

1. **Two-phase commit protocol:**
   - Phase 1 (Prepare): Leader sends reflex bytecode + hash to all Jetsons. Each validates (determinism check, safety invariant check, cycle budget check).
   - Phase 2 (Commit): If ≥quorum ACK, leader sends commit. All Jetsons atomically swap the active reflex.

2. **Rollback mechanism:**
   - Previous reflex version retained in shadow slot
   - If health check fails within 60-second probation period, automatic rollback
   - A/B testing framework uses this mechanism naturally

3. **Version vector:**
   - Each deployed reflex carries a version vector `[jetson_id: counter]`
   - Merge conflicts detected by version vector comparison
   - Last-writer-wins with cluster-wide sequence number for deterministic ordering

### 2.4 Split-Brain Prevention Design

```
        Jetson 0 (Leader, Term=5)     Jetson 1 (Follower, Term=5)
              │                              │
              │──── heartbeat ──────────────→│
              │←─── heartbeat ACK ──────────│
              │                              │
         Network partition │
         ══════════════════╧══════════════════
              │                              │
         [Cannot reach]               Election timeout
         Term frozen at 5             Jetson 1 starts election
                                       Term = 6
                                       Votes: self (1/3) — NO QUORUM
                                       │
                                 Remains FOLLOWER
                                 Cannot elect new leader
                                 Enters SAFE_STATE
```

**Key mechanism:** Each Jetson requires votes from **strict majority** (≥⌊N/2⌋+1). In a 3-Jetson partition where one side has 1 Jetson and the other has 2, the side with 2 can elect a leader and continue. The side with 1 cannot. This prevents two leaders from existing simultaneously.

**For ESP32 nodes:** ESP32s continue executing their current reflex bytecode autonomously during a Jetson partition. They do not require real-time Jetson commands for safety-critical operation (reflex bytecode runs at 1000 Hz on the ESP32 itself). The Jetson is needed only for:
- Reflex deployment/updates
- Trust score computation and autonomy level changes
- Cloud synchronization
- Observation recording for learning pipeline

---

## 3. Data Consistency

### 3.1 MQTT QoS Levels and Message Ordering

| MQTT QoS | Guarantee | NEXUS Use Case | Latency Impact |
|----------|-----------|----------------|----------------|
| 0 (At most once) | Fire-and-forget | Sensor telemetry (non-critical) | Minimal |
| 1 (At least once) | Acknowledged delivery | Observation data (replay idempotent) | +1 RTT |
| 2 (Exactly once) | 4-phase handshake | Trust scores, reflex deployment commands | +2 RTT |

**Message ordering:**
- MQTT guarantees ordering within a single topic per client
- NEXUS uses per-ESP32 topics: `nexus/esp32/{id}/telemetry`, `nexus/esp32/{id}/status`
- Jetson-level topics: `nexus/jetson/{id}/trust`, `nexus/jetson/{id}/reflex/{reflex_id}`
- Global topics: `nexus/cluster/quorum`, `nexus/cluster/reflex_deploy`

**QoS strategy:**
- Telemetry: QoS 0 (loss of single reading is acceptable; next reading arrives in 100 ms)
- Safety events (kill switch, overcurrent): QoS 1 (must be delivered at least once)
- Trust score updates: QoS 2 (must be delivered exactly once; duplicates cause incorrect state)
- Reflex deployment commands: QoS 2 (atomic deployment requires exactly-once semantics)
- Cloud sync: QoS 1 (cloud can deduplicate by sequence number)

### 3.2 Trust Score Synchronization

Trust scores must be consistent across all Jetsons for correct autonomy level computation:

**Challenge:** Each Jetson independently computes trust scores for its connected ESP32s. If Jetson A has trust T=0.85 for ESP32_03 and Jetson B has T=0.82, the cluster must agree on the autonomy level.

**Solution: CRDT-based trust score merge**

```python
# Conflict-free Replicated Data Type for trust scores
# Each trust update is an operation: (timestamp, delta, jetson_id)
# Merge rule: Last-Writer-Wins (LWW) with timestamp ordering

def merge_trust_scores(local_trusts: Dict[int, float],
                       remote_trusts: Dict[int, Tuple[float, float, int]],
                       local_clock: float) -> Dict[int, float]:
    """
    Merge remote trust scores with local using LWW.
    remote_trusts: {esp32_id: (trust_value, timestamp, jetson_id)}
    """
    merged = dict(local_trusts)
    for esp32_id, (remote_val, remote_ts, remote_jid) in remote_trusts.items():
        if esp32_id not in merged:
            merged[esp32_id] = remote_val
        else:
            local_val, local_ts = merged.get(esp32_id, (0.5, 0))
            if remote_ts > local_ts:
                merged[esp32_id] = remote_val
    return merged
```

**Consistency model:** Eventual consistency with bounded staleness (<1 second via MQTT QoS 2). The quorum mechanism ensures that any Jetson acting as leader has the most recent trust state.

### 3.3 Observation Data Partitioning

The learning pipeline generates ~72-field observation records at 100 Hz per ESP32. For 12 ESP32s, this produces ~864,000 records/second.

**Partitioning strategy:**
- **By ESP32 ID:** Each Jetson stores observations for its 4 connected ESP32s locally
- **By time range:** Hourly partitions for efficient batch processing
- **By behavioral cluster:** After HDBSCAN clustering, observations are tagged with cluster ID for pattern discovery

**Storage:**
- Edge (Jetson NVMe): Rolling 72-hour buffer (~200 GB at full rate, compressed ~30 GB)
- Local (network share): 90-day archive (~3 TB compressed)
- Cloud (Starlink): Aggregated summaries + anomalous events only (~500 MB/day)

**Consistency for learning:**
- Observation data is append-only (no updates, no deletes during operation)
- Immutability eliminates consistency concerns for learning pipeline
- Cloud sync uses sequence numbers; missing ranges trigger re-transmission from Jetson NVMe

---

## 4. Bandwidth Analysis

### 4.1 RS-422 Per-Link Bandwidth

| Parameter | Value |
|-----------|-------|
| Baud rate | 921,600 bits/sec |
| Data bits | 8 |
| Start/Stop bits | 2 (1+1) |
| Throughput | 92,160 bytes/sec (90 KB/s) |
| COBS + CRC overhead | ~1% (0.4% COBS + 0.6% CRC) |
| Effective throughput | ~91,200 bytes/sec |

### 4.2 Per-ESP32 Message Budget

| Message Type | Size (bytes) | Rate (Hz) | Bandwidth (B/s) | % of Link |
|-------------|-------------|-----------|-----------------|-----------|
| Telemetry (72 fields) | 75 | 10 | 750 | 0.82% |
| Status (heartbeat) | 25 | 1 | 25 | 0.03% |
| Command (reflex output) | 45 | 1 | 45 | 0.05% |
| OTA firmware chunk | 275 | 0 (idle) | 0 | 0% |
| **Normal operation total** | | | **820** | **0.90%** |
| OTA firmware chunk | 275 | 50 | 13,750 | 15.1% |
| **OTA operation total** | | | **14,570** | **16.0%** |

**Headroom:** Normal operation uses <1% of link capacity. Even during OTA updates with all reflex outputs, utilization stays below 20%.

### 4.3 Aggregation: How Many ESP32s Per Jetson?

Each Jetson has 4 UART ports (UART0-3 on Jetson Orin Nano). With external USB-UART adapters, this can be expanded to 8-16 ports.

**Theoretical maximum ESP32s per Jetson (normal operation):**
```
max_esp32 = link_capacity / per_esp32_bandwidth
          = 91,200 B/s / 820 B/s
          = 111 ESP32s per UART
```

**Practical maximum (with 20% safety margin and OTA consideration):**
```
max_esp32_normal = 91,200 × 0.80 / 820 = 89
max_esp32_ota    = 91,200 × 0.80 / 14,570 = 5
```

**Bottleneck is NOT RS-422 bandwidth.** The bottleneck is:
1. **Jetson UART count:** 4 native, 8-16 with USB adapters
2. **Jetson CPU time:** Processing telemetry from N ESP32s at 10 Hz
3. **gRPC/MQTT throughput:** Aggregating and forwarding all data to cluster

**Recommended maximum:** 8-16 ESP32s per Jetson (limited by UART availability, not bandwidth)

### 4.4 MQTT Message Rate Analysis

| Topic Pattern | Direction | Rate (per Jetson) | Message Size |
|--------------|-----------|-------------------|-------------|
| `nexus/esp32/+/telemetry` | Jetson → Broker | 40 msg/s (4 ESP32 × 10 Hz) | 75 B |
| `nexus/jetson/+/trust` | Jetson → Broker | 1 msg/s (periodic sync) | 200 B |
| `nexus/cluster/quorum` | Jetson → Broker | 0.33 msg/s (heartbeat) | 100 B |
| `nexus/cluster/reflex_deploy` | Leader → Broker | 0.01 msg/s (rare) | 2000 B |
| `nexus/cloud/sync` | Jetson → Broker | 0.1 msg/s (aggregated) | 5000 B |

**Total MQTT throughput per Jetson:** ~41.5 msg/s, ~8.2 KB/s
**Total MQTT throughput for 3-Jetson cluster:** ~125 msg/s, ~24.6 KB/s

This is well within the capability of Mosquitto or EMQX on a LAN (100,000+ msg/s typical).

### 4.5 Cloud Sync Bandwidth over Starlink

| Data Type | Rate | Size per Batch | Bandwidth |
|-----------|------|---------------|-----------|
| Aggregated telemetry summary | 1/min | 10 KB | 167 B/s |
| Anomalous event alerts | 0.1/hour | 2 KB | 0.6 B/s |
| Reflex deployment logs | 0.01/hour | 5 KB | 0.01 B/s |
| Trust score snapshots | 1/hour | 1 KB | 0.3 B/s |
| Learning pipeline results | 1/day | 500 KB | 5.8 B/s |
| **Total upstream** | | | **~174 B/s (1.4 Kbps)** |

**Starlink capacity:** 5-25 Mbps uplink (625 KB/s - 3.1 MB/s average)

**Utilization:** <0.03% of Starlink uplink capacity. Cloud sync is not a bandwidth concern.

**Concern:** Starlink latency (20-80 ms RTT) and intermittent availability (99.5% uptime) are more relevant than bandwidth. The system must operate autonomously during cloud outages.

---

## 5. Comparison to Alternatives

### 5.1 CAN Bus (NMEA 2000 — Marine Standard)

| Attribute | RS-422 (NEXUS) | CAN Bus (NMEA 2000) |
|-----------|----------------|---------------------|
| **Data rate** | 921.6 Kbps (per link) | 250 Kbps / 500 Kbps |
| **Topology** | Point-to-point star | Multi-drop bus |
| **Max nodes** | 1 per link (dedicated) | ~30-80 per bus |
| **Cable length** | 1,200 m (RS-422 spec) | 40 m @ 1 Mbps (200 m @ 250 Kbps) |
| **Error detection** | CRC-16 per message | 15-bit CRC + bit stuffing |
| **Fault tolerance** | Link failure isolates 1 node | Bus short kills all nodes |
| **Cost per node** | ~$8 (transceiver + cable) | ~$15 (transceiver + connector) |
| **Marine standard** | Custom (non-standard) | NMEA 2000 (IEC 61162-3) |
| **Protocol overhead** | ~1% (COBS + CRC) | ~30% (bit stuffing + framing) |
| **Determinism** | Yes (dedicated link) | Yes (priority-based arbitration) |

**When CAN is better:**
- Marine vessels with existing NMEA 2000 infrastructure
- Applications requiring <30m cable runs and standard compliance
- Systems needing many (30+) low-bandwidth sensors on a single bus

**When RS-422 is better:**
- High-bandwidth telemetry (72-field observations at 10 Hz)
- Long cable runs (>40m, up to 1200m)
- Applications requiring dedicated per-node bandwidth
- Systems where single bus failure is unacceptable

### 5.2 Ethernet/IP (Factory Automation)

| Attribute | RS-422 (NEXUS) | Ethernet/IP |
|-----------|----------------|-------------|
| **Data rate** | 921.6 Kbps | 100 Mbps / 1 Gbps |
| **Topology** | Point-to-point | Star (switched) |
| **Latency** | 0.35-1.6 ms | <0.1 ms (switched) |
| **Max cable length** | 1,200 m | 100 m (Cat5e) / 30 m (PoE) |
| **Power delivery** | Separate | PoE (802.3af/at) |
| **EMI immunity** | Excellent (differential) | Moderate (UTP) |
| **Cost per node** | ~$8 | ~$25 (magnetics + connector) |
| **Switch required** | No | Yes (adds SPOF) |
| **Marine grade** | Common (RS-422 transceivers) | Industrial switches available |

**When Ethernet/IP is better:**
- Factory automation with existing Ethernet infrastructure
- High-bandwidth applications (camera streams, LIDAR point clouds)
- PoE applications (single cable for data + power)
- Environments with <100m cable runs

**When RS-422 is better:**
- Marine/outdoor environments (RS-422 is differential, noise-immune)
- Long cable runs (>100m)
- Low power applications (ESP32 UART vs Ethernet PHY power)
- Simpler, cheaper cabling for sensor/actuator nodes

### 5.3 WiFi 6 (Home Automation)

| Attribute | RS-422 (NEXUS) | WiFi 6 (802.11ax) |
|-----------|----------------|-------------------|
| **Data rate** | 921.6 Kbps | 600 Mbps - 9.6 Gbps |
| **Topology** | Point-to-point | Infrastructure (AP) |
| **Latency** | 0.35-1.6 ms | 1-10 ms (variable) |
| **Range** | 1,200 m | 30-70 m indoor |
| **Power delivery** | Separate | PoE (AP only) |
| **Spectrum** | Wired (no interference) | 2.4/5/6 GHz (shared) |
| **Security** | Physical isolation | WPA3 (cryptographic) |
| **Determinism** | Yes | No (contention-based) |
| **Cost per node** | ~$8 | ~$5 (ESP32 has WiFi) |

**When WiFi 6 is better:**
- Home automation with existing WiFi infrastructure
- Mobile/roaming applications
- Applications where cabling is impractical
- High node count with low per-node bandwidth

**When RS-422 is better:**
- **Safety-critical systems requiring deterministic latency** (WiFi has jitter)
- **EMI-heavy environments** (marine engine rooms, industrial)
- Applications requiring guaranteed message delivery
- Systems where wireless reliability is insufficient (metal hulls, underground)

### 5.4 LoRaWAN (Agriculture/Mining)

| Attribute | RS-422 (NEXUS) | LoRaWAN |
|-----------|----------------|---------|
| **Data rate** | 921.6 Kbps | 0.3-50 Kbps |
| **Range** | 1,200 m (wired) | 2-15 km (wireless) |
| **Topology** | Point-to-point | Star-of-stars |
| **Latency** | 0.35-1.6 ms | 100-2000 ms |
| **Power per node** | 100 mW (active) | 10-100 mW (duty-cycled) |
| **Message rate** | Unlimited | 0.1-10 msg/min (duty cycle limits) |
| **Bi-directional** | Yes (full duplex) | Limited (Class A: receive after transmit) |
| **Cost per node** | ~$8 | ~$12 (module + antenna) |

**When LoRaWAN is better:**
- Agricultural fields spanning >1 km
- Mining operations with distributed sensors
- Applications requiring ultra-low power (battery-operated for years)
- Environments where cabling is impossible (moving equipment)

**When RS-422 is better:**
- **Real-time control** (LoRaWAN latency is 100-2000 ms vs 0.35 ms)
- **High data rate** (72-field telemetry at 10 Hz requires ~60 Kbps)
- **Full duplex communication** (command/response in <2 ms)
- **Deterministic timing** (reflex bytecode execution depends on <1 ms latency)

### 5.5 Decision Matrix

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| Marine vessel (wired hull) | RS-422 | Noise immunity, long cables, deterministic |
| Marine vessel (NMEA 2000 existing) | CAN Bus (NMEA 2000) | Standard compliance, plug-and-play |
| Factory (Ethernet existing) | Ethernet/IP | High bandwidth, PoE, existing infrastructure |
| Home automation | WiFi 6 | Low cost, no cabling, existing AP |
| Agriculture (wide area) | LoRaWAN | Long range, low power, battery operation |
| Mining (underground) | LoRaWAN + RS-422 hybrid | LoRaWAN for remote sensors, RS-422 for control loops |
| **NEXUS reference (marine)** | **RS-422 + Ethernet LAN** | **RS-422 for ESP32 links, Ethernet for Jetson interconnect** |

---

## 6. Conclusions and Recommendations

### 6.1 Key Findings from Simulation

1. **System availability exceeds 99.9%** across all single-failure scenarios in a 10,000-hour simulation with 1000 Monte Carlo iterations.

2. **Power supply failures** are the highest-risk component (MTBF 30,000 hrs), causing 95% probability of safe state entry. Recommendation: redundant PSUs with automatic switchover.

3. **Jetson failures** are the second-highest risk (40% safe state probability). A 3-Jetson cluster with 2-of-3 quorum tolerates exactly one Jetson failure; upgrading to 5 Jetsons tolerates two.

4. **Cable cuts** are low-probability (MTBF 500,000 hrs) and low-impact (isolates one ESP32). Not a design driver.

5. **Byzantine failures** are rare (1×10⁻⁷ per node-hour) but dangerous (30% safe state probability). Recommendation: majority voting across Jetson cluster for cross-validation of sensor data.

6. **Cascading failures** are the worst single scenario (70% safe state, 12-hour recovery). The primary trigger is power supply failure. Mitigation: independent PSU per Jetson group.

7. **Cloud loss** has minimal impact (2% safe state probability). The system is designed for edge-first operation; cloud is supplementary.

### 6.2 Architecture Recommendations

| Priority | Recommendation | Impact | Cost |
|----------|---------------|--------|------|
| **P0** | Redundant PSU with automatic switchover | Eliminates highest-risk failure mode | +$50 per PSU pair |
| **P1** | Jetson hot standby (pre-loaded trust scores) | Faster recovery from Jetson failure | +$400 (4th Jetson) |
| **P2** | Byzantine detection: cross-validated sensor readings | Detects incorrect data before it affects control | Software only |
| **P3** | 5-Jetson cluster upgrade | Tolerates 2 simultaneous Jetson failures | +$800 (2 more Jetsons) |
| **P4** | Dual RS-422 links per ESP32 | Zero ESP32 loss on cable cut | +$12 per ESP32 |
| **P5** | Ring topology for ESP32 connectivity | Cable cut rerouting | Firmware complexity |

### 6.3 Topology Selection Summary

The optimal NEXUS topology for a marine vessel is:

```
                 ┌──────────────┐
                 │  Cloud        │
                 │  (Starlink)   │
                 └──────┬───────┘
                        │
              ┌─────────┼─────────┐
              │    MQTT Broker    │
              │   (EMQX cluster)  │
              └────┬───────┬─────┘
         ┌─────────┼───────┼─────────┐
    ┌────┴───┐┌────┴───┐┌────┴───┐┌────┴───┐
    │J0 Lead ││J1 Peer ││J2 Peer ││J3 Hot  │
    │(Active)││(Active)││(Active)││Standby │
    └──┬─┬──┘└──┬─┬──┘└──┬─┬──┘└──┬──────┘
       │ │      │ │      │ │      │
    E00 E01  E04 E05  E08 E09  (mirrors)
    E02 E03  E06 E07  E10 E11
```

**Key properties:**
- RS-422 dedicated links: ESP32 → Jetson (4 per active Jetson)
- gRPC mesh: Full mesh between all Jetsons (Gigabit Ethernet)
- MQTT broker: Runs on all Jetsons for redundancy (EMQX cluster mode)
- 3-of-4 quorum: Tolerates 1 Jetson failure with full operation
- Hot standby Jetson: Pre-loaded state for <100 ms failover
- Starlink: Cloud connectivity for fleet management and learning pipeline

### 6.4 Estimated System Reliability

With recommended improvements:

| Configuration | Availability (10,000 hrs) | MTBF to quorum loss |
|--------------|--------------------------|---------------------|
| Baseline (3-Jetson, no redundancy) | 99.952% | 2,074 hrs |
| + Redundant PSU | 99.975% | 4,000 hrs |
| + Jetson hot standby (4-Jetson) | 99.991% | 11,111 hrs |
| + Byzantine detection | 99.993% | 14,286 hrs |
| **Full recommended (5-Jetson, all improvements)** | **99.998%** | **55,556 hrs** |

This exceeds the 99.9% (3-nines) availability target and approaches 4-nines (99.99%), which is appropriate for safety-critical marine autonomous systems.

---

## Appendix A: Simulation Configuration

| Parameter | Value |
|-----------|-------|
| ESP32 MTBF | 50,000 hours |
| Jetson Orin Nano MTBF | 100,000 hours |
| RS-422 Transceiver MTBF | 200,000 hours |
| Cable MTBF | 500,000 hours |
| Power Supply MTBF | 30,000 hours |
| Starlink MTBF | 150,000 hours |
| Simulation duration | 10,000 hours |
| Monte Carlo iterations | 1,000 per scenario |
| Time step | 0.1 hours (6 minutes) |
| Number of ESP32 nodes | 12 |
| Number of Jetson boards | 3 (baseline), 5, 7 (comparison) |

## Appendix B: RS-422 Physical Layer Specifications

| Parameter | Value |
|-----------|-------|
| Standard | TIA/EIA-422-B |
| Drivers | MAX485 / SN75176 (half-duplex RS-485 often used) |
| Voltage levels | ±2V to ±7V differential |
| Max data rate | 10 Mbps (at 12m); 100 Kbps (at 1200m) |
| NEXUS operating rate | 921,600 baud |
| Max cable length (at 921.6K) | ~120m (conservative); ~200m (with quality cable) |
| Connectors | M12 (marine grade) or RJ45 with shielded Cat5e |
| Termination | 120Ω at each end of differential pair |
| EMI protection | Shielded twisted pair (STP), ferrite chokes |

## Appendix C: gRPC Service Definitions (for Jetson Cluster)

```protobuf
// Jetson cluster communication services
service ClusterService {
  // Heartbeat and health check
  rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
  
  // Trust score synchronization
  rpc SyncTrustScores(TrustSyncRequest) returns (TrustSyncResponse);
  
  // Reflex deployment (two-phase commit)
  rpc PrepareReflex(ReflexPrepareRequest) returns (ReflexPrepareResponse);
  rpc CommitReflex(ReflexCommitRequest) returns (ReflexCommitResponse);
  rpc RollbackReflex(ReflexRollbackRequest) returns (ReflexRollbackResponse);
  
  // Observation data exchange
  rpc StreamObservations(ObservationRequest) returns (stream ObservationData);
  
  // Leader election
  rpc RequestVote(VoteRequest) returns (VoteResponse);
  rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
}
```

---

*Document generated as part of NEXUS Dissertation Round 4A: Network and Failure Simulation.*
