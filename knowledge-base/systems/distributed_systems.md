# Distributed Systems — Complete Encyclopedia

**Knowledge Base Article** | NEXUS Robotics Platform
**Revision:** 1.0 | **Date:** 2026-03-29
**Classification:** Systems Theory — Encyclopedic Reference
**Cross-References:** [[agent_communication_languages]], [[embedded_and_realtime_systems]], [[Master Consensus Architecture]], [[Trust Score Algorithm Specification]], [[Network and Physical Architecture]], [[Reflex Bytecode VM Specification]], [[Safety System Specification]], [[Redundancy and Failover]]

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [CAP Theorem and the NEXUS Design Position](#2-cap-theorem-and-the-nexus-design-position)
3. [Consensus Protocols](#3-consensus-protocols)
4. [Distributed Architectures](#4-distributed-architectures)
5. [Fault Tolerance](#5-fault-tolerance)
6. [Communication Patterns](#6-communication-patterns)
7. [Real-Time Distributed Systems](#7-real-time-distributed-systems)
8. [Edge Computing](#8-edge-computing)
9. [Distributed State Management](#9-distributed-state-management)
10. [Swarm Robotics as Distributed Systems](#10-swarm-robotics-as-distributed-systems)
11. [Network Topologies](#11-network-topologies)
12. [Scalability Analysis](#12-scalability-analysis)
13. [Synthesis: NEXUS as a Distributed System](#13-synthesis-nexus-as-a-distributed-system)
14. [References](#14-references)

---

## 1. Introduction

A **distributed system** is a collection of independent computing nodes that appear to their users as a single coherent system. These nodes communicate by passing messages over a network, coordinating their actions to achieve a common goal. The fundamental challenges of distributed computing — concurrency, partial failure, independent clocks, and uncertain message delivery — have occupied computer scientists since the 1970s and remain active research frontiers in 2026.

The NEXUS robotics platform is, at its core, a distributed system. A NEXUS fleet is a **colony of autonomous vessels**, each vessel is a **cluster of compute nodes** (Jetson Orin Nano Super boards), and each Jetson coordinates a **constellation of microcontrollers** (ESP32-S3 nodes). Messages flow across RS-422 serial links, Gigabit Ethernet, MQTT brokers, and satellite uplinks. Consensus is required for reflex deployment, trust score synchronization, and fleet-level coordination. Fault tolerance is a life-safety requirement: a node failure at sea cannot bring down the autopilot.

This encyclopedia article provides a comprehensive treatment of distributed systems theory, organized around eleven thematic pillars, with continuous mapping to NEXUS's architectural decisions. Each section covers foundational theory, practical engineering considerations, comparison tables, and specific NEXUS application analysis.

The study of distributed systems can be organized along three orthogonal axes:

- **Theory axis:** From CAP theorem to Byzantine fault tolerance to eventual consistency
- **Architecture axis:** From client-server to peer-to-peer to swarm intelligence
- **Application axis:** From cloud datacenters to edge robotics to autonomous marine vessels

NEXUS occupies a distinctive position at the intersection of all three: a real-time, safety-critical, physically distributed system that must operate reliably on the open ocean with intermittent cloud connectivity.

---

## 2. CAP Theorem and the NEXUS Design Position

### 2.1 Formal Statement of CAP

The **CAP theorem**, formulated by Eric Brewer in 2000 and proven by Gilbert and Lynch in 2002, states that a distributed data store can provide at most two of the following three guarantees simultaneously:

| Property | Formal Definition | What It Means |
|----------|------------------|---------------|
| **Consistency (C)** | Every read receives the most recent write or an error | All nodes see the same data at the same time |
| **Availability (A)** | Every request receives a non-error response, without guarantee of most recent write | The system is always ready to respond |
| **Partition Tolerance (P)** | The system continues to operate despite an arbitrary number of messages being dropped or delayed between nodes | Network failures do not bring down the system |

Brewer's key insight is that **in the presence of a network partition** (which is inevitable in real-world distributed systems), a system must choose between consistency and availability. It cannot guarantee both.

### 2.2 The Three Corners of CAP

**CP Systems** (Consistent + Partition Tolerant) sacrifice availability during partitions. Examples include: traditional relational databases with synchronous replication, ZooKeeper, HBase. When a partition occurs, these systems return errors rather than stale data.

**AP Systems** (Available + Partition Tolerant) sacrifice consistency during partitions. Examples include: DNS, Amazon DynamoDB (in eventual consistency mode), Cassandra, CouchDB. When a partition occurs, these systems continue serving requests, possibly with stale data.

**CA Systems** (Consistent + Available) assume no partitions — an assumption that fails in any real network. Single-node databases technically qualify, but they are not distributed systems. Modern distributed databases that claim CA are typically CP systems with optimistic partition handling.

### 2.3 PACELC: The Extended Model

Abadi's 2012 **PACELC** theorem extends CAP by addressing what happens when there is no partition:

- **PA/EL**: Prefer availability during partition; prefer low latency otherwise (e.g., Cassandra, DynamoDB)
- **PA/EC**: Prefer availability during partition; prefer consistency otherwise (e.g., PNUTS)
- **PC/EL**: Prefer consistency during partition; prefer low latency otherwise (e.g., MongoDB)
- **PC/EC**: Prefer consistency during partition; prefer consistency otherwise (e.g., ZooKeeper, HBase)

### 2.4 Where NEXUS Fits: AP with Safety Guardrails

NEXUS is unambiguously an **AP system** that prioritizes Availability and Partition tolerance over strict Consistency. This design choice is driven by the fundamental physics of the deployment environment:

**Partitions are guaranteed.** Vessels at sea communicate via satellite links (Starlink, 99.5% uptime) or VHF radio. Between vessels, partitions lasting minutes to hours are normal. Even within a single vessel, the RS-422 serial link between a Jetson and its ESP32 nodes can be interrupted by cable damage, connector corrosion, or electromagnetic interference.

**Availability is life-safety.** When a vessel loses communication with the fleet or with its cloud backend, it must continue operating its autopilot, engine monitoring, and safety systems. Returning an error because "consistency cannot be guaranteed" is not acceptable when the vessel is approaching a lee shore.

**Consistency is relaxed with bounded staleness.** Trust scores, configuration settings, and fleet-level state are eventually consistent. NEXUS uses CRDTs (Conflict-free Replicated Data Types) with Last-Writer-Wins (LWW) merging and version vectors to resolve conflicts when partitions heal. The bounded staleness window is typically less than one second for intra-vessel state and less than one hour for inter-vessel state.

| CAP Dimension | NEXUS Position | Rationale |
|---------------|---------------|-----------|
| **Consistency** | Eventual (bounded staleness <1s intra-vessel, <1h inter-vessel) | Real-time control requires local availability more than global consistency |
| **Availability** | High priority (ESP32 reflexes run autonomously; no cloud dependency for safety) | Life-safety: autopilot must operate during any communication failure |
| **Partition Tolerance** | Mandatory (satellite links, serial cables, WiFi all can fail) | Maritime physics guarantees partitions |

### 2.5 Safety Consistency Layer

NEXUS introduces a **safety consistency layer** on top of the AP foundation:

- **Reflex deployment** uses Two-Phase Commit (2PC) for atomic deployment across the Jetson cluster (see [[Consensus Protocols]] below). This is a CP operation: if a partition prevents quorum, the deployment is rejected rather than partially applied.
- **Trust score updates** use CRDT-based merging (AP). During partitions, each vessel computes trust scores independently; when connectivity is restored, scores are merged using LWW with timestamps.
- **Safety-critical commands** (kill switch, E-Stop) are hardware-level and bypass the distributed system entirely (Tier 1 safety).

This hybrid approach — AP for operational data, CP for safety-critical deployments, hardware for emergency stops — is the correct engineering balance for a safety-critical distributed system operating in an unreliable communication environment.

---

## 3. Consensus Protocols

### 3.1 Paxos — The Foundation

**Paxos**, developed by Leslie Lamport in 1989 (published in 1998), is the foundational consensus algorithm for achieving agreement in a distributed system. It guarantees that a set of nodes can agree on a single value even if some nodes fail.

**How Paxos works** (simplified):

1. **Prepare Phase:** A proposer sends a prepare(n) message to all acceptors with a proposal number n. Each acceptor promises to reject any future proposal with a number less than n, and returns the highest-numbered proposal it has previously accepted (if any).
2. **Accept Phase:** If the proposer receives promises from a majority of acceptors, it sends accept(n, value) where value is the highest-numbered previously accepted value (or its own if none). Each acceptor accepts the proposal if n is the highest it has seen.
3. **Learn Phase:** Once a majority of acceptors have accepted, the value is chosen. Learners are notified.

**Properties of Paxos:**
- **Safety:** No two nodes ever learn different values (agreement guaranteed)
- **Liveness:** If a majority of nodes are reachable and no new proposers interfere, a value will eventually be chosen
- **Fault tolerance:** Tolerates up to ⌊(N-1)/2⌋ simultaneous failures

**Why Paxos is hard:** Lamport's original paper was notoriously difficult to understand, leading to the famous "Paxos Made Simple" follow-up in 2001. The algorithm's difficulty stems from its generality — it handles arbitrary numbers of proposers, acceptors, and learners, including concurrent proposers with conflicting proposals.

**NEXUS mapping:** Paxos is not directly used in NEXUS because of its implementation complexity and the availability of simpler alternatives (Raft) for the specific use cases required. However, Paxos's theoretical properties underpin the entire field and inform NEXUS's approach to distributed agreement.

### 3.2 Raft — Understandable Consensus for Fleet Coordination

**Raft**, developed by Diego Ongaro and John Ousterhout in 2014, was explicitly designed to be an understandable alternative to Paxos. It decomposes the consensus problem into three independent subproblems:

| Subproblem | Description | NEXUS Application |
|-----------|-------------|-------------------|
| **Leader Election** | One node is elected leader and handles all client requests | Jetson cluster leader election via Redis (simplified Raft variant) |
| **Log Replication** | The leader replicates its log to followers; agreement requires majority ACK | Reflex bytecode deployment requires 2-of-3 Jetson ACK |
| **Safety** | If a log entry is committed, it will eventually be on all leaders | Deployed reflexes are deterministic; all Jetsons validate before ACK |

**Raft roles:**

- **Leader:** Handles all client requests, replicates log entries to followers, sends heartbeats. Only one leader at a time (per term).
- **Follower:** Responds to leader's AppendEntries RPCs and RequestVote RPCs. Passively receives replicated data.
- **Candidate:** A follower that has not received a heartbeat within the election timeout, and initiates a leader election.

**Raft terms and elections:**

Raft divides time into terms of arbitrary length, numbered with monotonically increasing integers. Each term begins with a leader election. If a leader is elected, it serves for the remainder of the term. If the election fails (no node receives majority votes), a new term begins with a new election.

1. A follower increments its current term and transitions to **candidate**.
2. It votes for itself and sends RequestVote RPCs to all other nodes.
3. If it receives votes from a majority, it becomes **leader**.
4. If another node establishes itself as leader (by receiving AppendEntries with a higher term), the candidate reverts to **follower**.
5. If the election timeout elapses without a winner, a new election begins.

**NEXUS Jetson cluster and Raft:**

The NEXUS 3-Jetson cluster uses a simplified Raft variant for leader election:

```
Jetson-Alpha (10.0.0.1) — Leader (normal operation)
Jetson-Bravo (10.0.0.2) — Follower (vision services)
Jetson-Charlie (10.0.0.3) — Follower (engine/NMEA services)
```

- **Leader election:** Uses Redis SET NX (set-if-not-exists) with a 5-second TTL. The leader must renew every 3 seconds. If the key expires, all Jetsons race to become leader; lowest IP wins ties.
- **Log replication:** Reflex deployments use a 2PC protocol inspired by Raft: leader proposes, followers validate and ACK, leader commits. This is a synchronous operation — the leader waits for majority ACK before confirming deployment.
- **Safety:** If the leader Jetson crashes mid-deployment, a new leader is elected within ~300ms. The deployment either completed (reflex is on ≥2 Jetsons) or did not (reflex is on 0 or 1). Partial deployments are detected by version number comparison and rolled back.

### 3.3 Byzantine Fault Tolerance (PBFT)

**Byzantine Fault Tolerance (BFT)** addresses a more severe failure model than Paxos or Raft. While Paxos/Raft assume nodes can crash (fail-stop), BFT assumes nodes can exhibit **arbitrary behavior** — including sending conflicting messages to different peers, which is the worst possible failure in a distributed system. This is named after the Byzantine Generals Problem described by Lamport, Shostak, and Pease in 1982.

**The Byzantine Generals Problem:** A group of generals must agree on a common plan of action (attack or retreat). They communicate via messengers. Some generals may be traitors who send false messages. The problem is to devise a protocol that ensures loyal generals agree on the same plan, regardless of what the traitors do.

**Practical Byzantine Fault Tolerance (PBFT),** developed by Castro and Liskov in 1999, was the first BFT protocol to demonstrate that BFT could be practical for real systems. It requires 3f+1 nodes to tolerate f Byzantine faults.

**PBFT phases:**
1. **Pre-prepare:** The primary (leader) assigns a sequence number to the client request and multicasts it to all backups.
2. **Prepare:** Each backup accepts the pre-prepare, sends a prepare message to all nodes (including itself). A node accepts when it has 2f+1 matching prepare messages.
3. **Commit:** Once a node has collected 2f+1 prepare messages, it multicasts a commit message. When 2f+1 commit messages are collected, the request is committed and executed.

**NEXUS application:**

NEXUS does not use full PBFT (which requires 4 nodes minimum for 1 Byzantine fault) but incorporates Byzantine-aware design principles:

| BFT Concept | NEXUS Implementation |
|------------|---------------------|
| Cross-validation | Dual-ESP32 autopilot pair: STANDBY monitors ACTIVE's sensor readings via cross-link UART. Divergence >10° triggers auto-disengage |
| Majority voting | 3-Jetson cluster quorum (2-of-3) prevents a single faulty Jetson from deploying malicious reflexes |
| Replicated state machines | All 3 Jetsons maintain independent trust score databases; LWW merge on reconciliation |
| Fingerprint verification | SHA-256 hash on all deployed bytecode; hash mismatch triggers automatic rollback |

**Why not full PBFT in NEXUS?** Full PBFT requires 4 nodes minimum (3f+1 for f=1) and adds significant message complexity (3 round trips per consensus). For a 3-Jetson vessel cluster, the cost of a fourth Jetson ($350 + power + cabling) is not justified by the extremely low probability of Byzantine faults in hardware (estimated at 1×10⁻⁷ per node-hour from Monte Carlo simulation). Instead, NEXUS relies on the 4-tier safety system (see [[Fault Tolerance]]) to catch incorrect behavior before it affects physical actuators.

### 3.4 CRDTs — Conflict-Free Replicated Data Types

**Conflict-free Replicated Data Types (CRDTs)**, formalized by Marc Shapiro and colleagues starting in 2011, are data structures designed to be replicated across multiple nodes where replicas are updated independently and concurrently, without coordination. CRDTs guarantee that all replicas converge to the same state, a property called **Strong Eventual Consistency (SEC)**.

**Two families of CRDTs:**

| Type | Mechanism | Example | Trade-off |
|------|-----------|---------|-----------|
| **State-based (CvRDT)** | Replicas exchange full state; merge function is commutative, associative, idempotent | G-Counter, OR-Set, LWW-Element-Set | Requires sending full state (bandwidth cost) |
| **Operation-based (CmRDT)** | Replicas exchange operations; operations are commutative | Increment-only counter, observed-remove set | Requires reliable broadcast (exactly-once delivery) |

**NEXUS trust score as a CRDT:**

The NEXUS trust score is implemented as a **Last-Writer-Wins (LWW) Register**, a state-based CRDT:

```python
# CRDT merge rule for trust scores
# Each update is tagged with (value, timestamp, jetson_id)
# Merge: take the update with the highest timestamp
def merge_trust(local: (float, float, int), remote: (float, float, int)) -> (float, float, int):
    local_val, local_ts, local_jid = local
    remote_val, remote_ts, remote_jid = remote
    if remote_ts > local_ts:
        return (remote_val, remote_ts, remote_jid)
    return local
```

This merge function is commutative, associative, and idempotent — the three requirements for a valid CRDT merge operation. When a partition heals and two vessels exchange trust scores, the LWW rule guarantees convergence regardless of the order in which updates arrive.

### 3.5 Two-Phase Commit and Three-Phase Commit

**Two-Phase Commit (2PC)** is a blocking atomic commitment protocol used when a distributed transaction must be either fully committed or fully aborted across all participants.

| Phase | Messages | Purpose |
|-------|----------|---------|
| **Prepare (Phase 1)** | Coordinator → Participants: "Can you commit?" | Each participant votes YES or NO and writes a durable log record |
| **Commit/Abort (Phase 2)** | Coordinator → Participants: "Commit" or "Abort" | Each participant executes the decision and writes a final log record |

**2PC failure scenarios:**
- If the coordinator crashes after sending prepare but before sending commit: participants are **blocked**, holding locks on resources indefinitely.
- If a participant crashes after voting YES but before receiving commit: the coordinator cannot proceed until the participant recovers.

**Three-Phase Commit (3PC)** was designed to solve 2PC's blocking problem by adding a **Pre-Commit phase**:

1. **CanCommit:** Coordinator asks participants if they can commit.
2. **PreCommit:** If all vote YES, coordinator sends PreCommit. Participants acknowledge.
3. **DoCommit:** Coordinator sends DoCommit. Participants commit.

3PC is **non-blocking** under the assumption that network partitions do not occur simultaneously with coordinator failures — an assumption that limits its practical applicability (it does not handle network partitions, violating the P in CAP).

**NEXUS application — Reflex deployment as 2PC:**

NEXUS uses a 2PC-inspired protocol for atomic reflex deployment across the Jetson cluster:

1. **Prepare Phase:** Leader Jetson sends reflex bytecode + SHA-256 hash + version to all Jetsons. Each Jetson validates: determinism check (same inputs → same outputs within cycle budget), safety invariant check (no actuator commands outside safe-state bounds), resource check (sufficient VM memory and cycle budget). Each Jetson votes YES or NO.
2. **Commit Phase:** If ≥quorum (2-of-3) votes YES, leader sends COMMIT. All Jetsons atomically swap the active reflex. If <quorum votes YES, leader sends ABORT and all Jetsons discard the candidate.

**Rollback mechanism:** Previous reflex version is retained in a shadow slot. If health check fails within a 60-second probation period after commit, automatic rollback occurs.

### 3.6 Vector Clocks and Lamport Timestamps

**Lamport timestamps**, invented by Leslie Lamport in 1978, provide a partial ordering of events in a distributed system. Each process maintains a counter that increments before each event and includes the counter value in every message. On receiving a message, a process updates its counter to max(local, received) + 1.

**Properties of Lamport timestamps:**
- If event A causally precedes event B, then L(A) < L(B).
- If L(A) < L(B), it does NOT mean A causally precedes B (clocks can be concurrent).
- Lamport timestamps provide **happened-before** ordering but not total ordering.

**Vector clocks** extend Lamport timestamps by maintaining a vector of N counters (one per process in the system). On each event, process i increments its own counter v[i]. On receiving a message, process i takes the element-wise maximum of its vector and the received vector, then increments its own counter.

**Vector clock comparison:**
- V(A) < V(B) if every element of V(A) is ≤ the corresponding element of V(B), and at least one element is strictly less.
- V(A) || V(B) (concurrent) if neither V(A) < V(B) nor V(B) < V(A).

**NEXUS application:**

NEXUS uses both Lamport timestamps and version vectors:

| Mechanism | Where Used | Purpose |
|-----------|-----------|---------|
| **Lamport timestamps** | MQTT QoS 2 message deduplication, trust score updates | Ordering of events from same source |
| **Version vectors** | Deployed reflexes carry `[jetson_id: counter]` per deployment | Detect merge conflicts across Jetsons |
| **Monotonic sequence numbers** | Heartbeat protocol (Jetson → ESP32), VesselLink message IDs | Detect duplicate or out-of-order messages |

### 3.7 Consensus Protocol Comparison Table

| Protocol | Fault Model | Nodes Required | Message Complexity | Latency (rounds) | Throughput | Understandability | NEXUS Use |
|----------|------------|---------------|-------------------|------------------|-----------|------------------|-----------|
| **Paxos** | Crash-stop | 2f+1 | O(N²) | 2 | High | Very Low | Indirect (theoretical foundation) |
| **Raft** | Crash-stop | 2f+1 | O(N) | 2 | High | High | Jetson cluster leader election |
| **PBFT** | Byzantine | 3f+1 | O(N²) | 3 | Low-Medium | Medium | Byzantine-aware design principles only |
| **2PC** | Crash-stop | N (no fault tolerance) | O(N) | 2 | Low (blocking) | High | Reflex bytecode deployment |
| **3PC** | Crash-stop (no partitions) | N | O(N) | 3 | Very Low | Medium | Not used |
| **CRDT (LWW)** | Any | N (any fault tolerance) | O(N) (merge) | 1 (local) | Very High | High | Trust score synchronization |
| **Gossip** | Crash-stop | N | O(log N) per rumor | O(log N) | High | Very High | Fleet-level state propagation |

---

## 4. Distributed Architectures

### 4.1 Overview of Architectural Styles

| Architecture | Description | Advantages | Disadvantages | Example |
|-------------|-------------|------------|---------------|---------|
| **Client-Server** | Centralized server provides services to clients | Simple, well-understood, easy to manage | Single point of failure, scalability bottleneck | Web applications, database servers |
| **Peer-to-Peer** | All nodes are equal; no central authority | No single point of failure, scalable | Complex coordination, inconsistent state | BitTorrent, blockchain |
| **Publish-Subscribe** | Producers publish to topics; consumers subscribe to topics | Decoupled producers and consumers, flexible routing | Message delivery guarantees are complex | MQTT (NEXUS), Kafka, RabbitMQ |
| **Actor Model** | Everything is an actor; communication via async messages | Encapsulated state, natural concurrency, location transparency | Message ordering, deadlock-free design required | Erlang/OTP, Akka |
| **Microservices** | Fine-grained, independently deployable services | Independent scaling, polyglot, team autonomy | Network overhead, distributed debugging, data consistency | Netflix, Amazon |
| **Event-Driven** | Components react to events (state changes) | Responsive, loosely coupled, real-time capable | Event ordering, replay complexity, debugging | CQRS, event sourcing |
| **Blackboard** | Shared structured memory; knowledge sources read/write | Loose coupling, easy to extend | Performance bottleneck at shared memory, contention | HEARSAY-II, NEXUS Jetson cognitive layer |

### 4.2 NEXUS's Architecture: Hierarchical Within Vessel, Peer-to-Peer Across Fleet

NEXUS employs a **hybrid architecture** that combines hierarchical control within a vessel with peer-to-peer coordination across the fleet.

**Within a vessel — Three-tier hierarchy:**

```
┌─────────────────────────────────────────────────────────┐
│  TIER 0: Jetson Cluster (Gigabit Ethernet, 10.0.0.0/24) │
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │ JETSON-α │    │ JETSON-β │    │ JETSON-γ │         │
│   │ LEADER   │    │ FOLLOWER │    │ FOLLOWER │         │
│   │ 10.0.0.1 │    │ 10.0.0.2 │    │ 10.0.0.3 │         │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│        │               │               │                │
│   ┌────┴───────────────┴───────────────┴────┐          │
│   │    gRPC (synchronous) + MQTT (async)     │          │
│   └──────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────┐
│  TIER 1: ESP32 Node Bus (RS-422, 115200 baud)         │
│                                                         │
│   Jetson-α: AP-PRIMARY, AP-BACKUP, EnvSensor           │
│   Jetson-β: Camera PTZ, Deck Equipment, Bilge Monitor   │
│   Jetson-γ: Engine PRIMARY, Engine BACKUP, Tank Level   │
└─────────────────────────────────────────────────────────┘
```

**Within the vessel, the architecture is hierarchical:**
- **Jetson layer (coordinator):** 3 Jetson Orin Nano Super boards form a Raft-based cluster. One is elected leader and manages ESP32 provisioning, reflex deployment, and fleet communication.
- **ESP32 layer (workers):** Each Jetson manages 4-8 ESP32-S3 microcontroller nodes via dedicated RS-422 serial links. ESP32s execute reflex bytecode autonomously and report telemetry to their parent Jetson.

**Across the fleet — Peer-to-Peer:**

```
┌──────────┐    Starlink    ┌──────────┐
│ VESSEL A │◄══════════════►│ VESSEL B │
│ 3 Jetsons│   MQTT over    │ 3 Jetsons│
│ 12 ESP32s│   TLS/VPN      │ 12 ESP32s│
└──────────┘                └──────────┘
      │                          │
      │      ┌──────────┐       │
      └─────►│  CLOUD   │◄──────┘
            │ FLEET MGR │
            └──────────┘
```

- Vessels are **peers**: no vessel is the fleet "master." The cloud performs aggregation and learning pipeline tasks but does not control vessel operations.
- **Cloud is optional**: A vessel operates fully autonomously without cloud connectivity. The cloud provides fleet-level analytics, model training, and OTA firmware distribution.
- **Inter-vessel communication**: MQTT broker with TLS encryption. Messages include trust score synchronization, observation data exchange, and fleet task allocation.

### 4.3 Actor Model Mapping

NEXUS's architecture is a strict interpretation of the Actor model applied to physical hardware. See [[agent_communication_languages]] for the complete mapping. The key insight is:

- Each ESP32 running a [[Reflex Bytecode VM Specification|bytecode VM]] is an **actor**: it receives messages (bytecode programs via the wire protocol), processes them one at a time, sends messages (telemetry via EMIT_EVENT syscalls), and modifies its own state.
- Each Jetson is a **supervisor actor**: it manages a group of ESP32 actors, deploys bytecode to them, monitors their health, and aggregates telemetry.
- The fleet is a **network of networks**: supervisors communicate with each other via MQTT.

The critical distinction from the classical Actor model is that in NEXUS, **the message carries executable code, not just data**. When Agent A deploys a reflex bytecode to Agent B's ESP32, it is sending a behavior, not information. This transforms the communication model from data exchange to intention deployment.

---

## 5. Fault Tolerance

### 5.1 Fault Models

A distributed system must handle multiple categories of faults:

| Fault Type | Description | Detection Method | Example in NEXUS |
|-----------|-------------|-----------------|-----------------|
| **Fail-stop** | Node halts and does not respond | Heartbeat timeout, missing message | ESP32 watchdog timeout → reset |
| **Crash** | Node crashes and may restart | Missing heartbeat, reboot detection | Jetson OS crash → leader re-election |
| **Omission** | Node drops some messages | Sequence number gaps, CRC mismatch | RS-422 frame loss → retry mechanism |
| **Timing** | Node responds too slowly | Deadline monitoring (task watchdog) | PID loop misses 10ms deadline |
| **Byzantine** | Node exhibits arbitrary behavior | Cross-validation, majority voting | Sensor divergence between dual ESP32s |
| **Cascading** | One fault triggers others | Fault isolation, circuit breakers | Power supply failure → Jetson crash → ESP32 safe-state |

### 5.2 Checkpointing and Recovery

**Checkpointing** is the process of saving a distributed system's state at a known-good point, enabling recovery to that point after a failure.

| Checkpointing Type | Description | Trade-off | NEXUS Application |
|-------------------|-------------|-----------|------------------|
| **Synchronous** | All nodes checkpoint simultaneously; blocks processing during checkpoint | Consistent but high latency overhead | Not used (latency unacceptable for real-time control) |
| **Asynchronous** | Each node checkpoints independently while processing continues | Low overhead but may capture inconsistent state | Jetson NVMe periodic state dumps (SQLite checkpoint) |
| **Coordinated** | Two-phase checkpointing; nodes agree on a consistent cut | Moderate overhead; consistent state | Trust score snapshots (periodic, LWW-merged) |
| **Application-level** | Application defines what constitutes a checkpointable state | Most flexible; application-specific correctness | Reflex bytecode version stored in NVS with SHA-256 integrity |

**NEXUS recovery mechanisms:**

1. **ESP32 firmware recovery:** Dual-slot flash (factory + OTA). If new firmware fails to boot within 60 seconds, anti-rollback reverts to factory partition.
2. **Jetson state recovery:** Redis persistence (RDB snapshots + AOF). On Jetson restart, state is loaded from last known-good snapshot.
3. **Autopilot failover:** Dual-ESP32 architecture with relay selector board. Failover in <100ms from heartbeat loss to corrective output.
4. **Cloud data recovery:** Append-only observation logs with sequence numbers. Missing ranges trigger re-transmission from Jetson NVMe.

### 5.3 Self-Healing Systems

A **self-healing system** automatically detects, diagnoses, and recovers from faults without human intervention. NEXUS implements multiple layers of self-healing:

| Layer | Self-Healing Mechanism | Detection | Recovery | Time |
|-------|----------------------|-----------|----------|------|
| ESP32 | External watchdog (MAX6818) resets frozen processor | 1.0s timeout (0x55/0xAA pattern) | Full reset, reload from flash | 1.01s |
| ESP32 | OTA rollback | 60s probation failure | Flash partition swap | ~2 min |
| ESP32 | Jetson heartbeat loss → DEGRADED → SAFE_STATE | 500ms / 1000ms heartbeat timeout | Reflex-only → all outputs safe | 0.5-1.0s |
| Jetson | Leader election (Redis SET NX) | 5s key TTL expiry | New leader elected | ~0.3s |
| Jetson | Redis Sentinel failover | Master unreachable for 10s | Sentinel promotes replica | ~10s |
| Vessel | Graceful degradation | Component health monitoring | Shed non-critical capabilities | Automatic |
| Fleet | CRDT merge on partition heal | Version vector comparison | LWW merge of trust scores | <1s post-reconnect |

### 5.4 NEXUS's Four-Tier Safety as Distributed Fault Tolerance

NEXUS's [[Safety System Specification]] implements a defense-in-depth architecture with four independent tiers. When viewed through the lens of distributed fault tolerance, each tier provides a different level of abstraction:

| Tier | Safety Barrier | Fault Tolerance Role | Response Time | Authority |
|------|---------------|---------------------|--------------|-----------|
| **Tier 1: Hardware Interlock** | Kill switch, polyfuses, hardware watchdog, MOSFET pull-downs | **Independent of all software.** Cannot be affected by any software fault, communication failure, or distributed consensus failure. | <1ms (electrical) | Absolute |
| **Tier 2: Firmware Safety Guard** | E-Stop ISR, safe-state outputs, sensor validation, overcurrent detection | **Faster than supervisory tasks.** Detects and responds to hardware-level faults (overcurrent, kill switch) that the software consensus layer cannot detect. | <10ms (ISR) | Overrides all software |
| **Tier 3: Supervisory Task** | Watchdog feeder, heartbeat monitor, safety state machine | **Bridges hardware and application.** Detects distributed system failures (Jetson heartbeat loss, task hang) and escalates to safe-state. | <100ms | Can override control tasks |
| **Tier 4: Application Control** | PID loops, reflexes, AI inference, domain logic | **Lowest authority, most intelligent.** Subject to all constraints of Tiers 1-3. Can be suspended or terminated at any time. | <10ms (control loop) | Lowest |

**Key insight:** The four tiers form a **distributed fault tolerance cascade**. A fault at Tier 4 (e.g., PID integral windup) is caught by Tier 3 (plausibility check). A fault at Tier 3 (supervisor task hang) is caught by Tier 2 (software watchdog escalates to Tier 1). A fault at Tier 2 (ISR corruption) is caught by Tier 1 (hardware watchdog resets the processor). And a fault at Tier 1 (kill switch failure) is caught by... the captain's weekly manual test. The system is safe only when all four tiers are operational, and the failure of any one tier does not compromise the effectiveness of the remaining tiers.

### 5.5 Graceful Degradation in Distributed Systems

**Graceful degradation** is the ability of a system to continue operating at reduced capability when some components fail, rather than failing catastrophically. NEXUS implements a comprehensive degradation hierarchy:

```
LEVEL 0 (FULL):
  All 3 Jetsons online, all 12 ESP32s healthy, vision + voice + GPS track + AI
  active. Full autonomous operation.

LEVEL 1 (DEGRADED — 1 Jetson lost):
  2 Jetsons remain (quorum maintained). Vision may be reduced (only 1 Jetson for
  DeepStream). Voice may be unavailable. Autopilot, engine monitor, safety
  continue at full capability.

LEVEL 2 (REDUCED — 2 Jetsons lost):
  1 Jetson remains (no quorum for fleet operations). Vessel continues standalone
  operation. Autopilot runs on local Jetson. No fleet coordination, no cloud sync.

LEVEL 3 (MINIMAL — All Jetsons lost):
  ESP32s continue autonomous operation using last-deployed reflex bytecode.
  Autopilot holds last heading (PID loop runs locally). Engine monitor continues
  independent safety monitoring. No AI, no fleet, no cloud.

LEVEL 4 (SAFE STATE — Kill switch activated):
  All actuators de-energized. Solenoids spring-center. Rudder holds via hydraulic
  lock. Captain steers manually via helm. This is the ultimate safe state.
```

---

## 6. Communication Patterns

### 6.1 Overview of Communication Patterns

| Pattern | Description | Latency | Reliability | Ordering | Use Case |
|---------|-------------|---------|-------------|----------|----------|
| **Request-Reply** | Client sends request, server sends reply | Low (1-2 RTT) | High (retries) | FIFO per connection | gRPC, HTTP, database queries |
| **Publish-Subscribe** | Producers publish to topics; consumers subscribe | Low (push) | Configurable (QoS 0/1/2) | Per-topic FIFO | MQTT (NEXUS), Kafka |
| **Gossip** | Nodes randomly share information with peers | O(log N) propagation | High (redundant paths) | Eventual | Cluster state propagation |
| **Scatter-Gather** | Request broadcast to multiple nodes; responses aggregated | High (parallel) | High (timeout + retry) | Not guaranteed | Parallel queries, map-reduce |
| **Pipeline** | Data flows through a chain of processing stages | Low (per stage) | Medium (backpressure) | FIFO | Stream processing |
| **Shared Memory** | Nodes read/write to common memory space | Very Low | Medium (consistency) | Depends on implementation | NEXUS MQTT topics (logical shared memory) |

### 6.2 NEXUS Communication Protocols

NEXUS uses four distinct communication protocols, each optimized for its specific role in the system:

**MQTT (publish-subscribe) for Jetson-to-Cloud:**

| Parameter | Value |
|-----------|-------|
| Broker | Mosquitto (vessel), EMQX (fleet) |
| Transport | TCP/IP over Gigabit Ethernet / Starlink |
| QoS Levels | 0 (telemetry), 1 (safety events), 2 (trust scores, reflex deployment) |
| Retained Messages | Trust scores, vessel status |
| Last Will and Testament | Jetson publishes OFFLINE status on disconnect |
| Topic Hierarchy | `nexus/vessel/{id}/...`, `nexus/cluster/...`, `nexus/cloud/...` |
| Latency | <1ms (LAN), 20-80ms (Starlink) |

MQTT's publish-subscribe model provides the loose coupling required for fleet communication: vessels publish telemetry without knowing which consumers exist, and consumers subscribe without knowing which producers exist. This decoupling is essential for a system where vessels may join or leave the fleet at any time.

**RS-422 (serial, request-reply) for Jetson-to-ESP32:**

| Parameter | Value |
|-----------|-------|
| Physical Layer | RS-422 differential serial (EIA-422) |
| Baud Rate | 115200 bps (8N1) |
| Frame Format | JSON text + newline delimiter |
| Topology | Star (dedicated point-to-point links) |
| Galvanic Isolation | ADuM1201 dual optoisolator (3kV) |
| Latency | 0.35-1.6ms (message round-trip) |
| Protocol | VesselLink JSON (see wire protocol spec) |

RS-422 is the workhorse of intra-vessel communication. Every ESP32 has a dedicated link to its parent Jetson, providing full bandwidth isolation and deterministic latency. The choice of RS-422 over CAN bus, Ethernet, or WiFi was driven by five factors: simplicity (debuggable with any terminal program), reliability (full-duplex, no collision), range (1200m at low speed), cost ($8 per link), and determinism (no contention).

**ESP-NOW (mesh) for ESP32-to-ESP32:**

| Parameter | Value |
|-----------|-------|
| Protocol | ESP-NOW (Espressif proprietary) |
| Transport | 2.4 GHz ISM band, encrypted (CCMP) |
| Topology | Mesh (many-to-many) |
| Range | ~200m line-of-sight (marine: ~100m) |
| Latency | <1ms |
| Payload | Up to 250 bytes per packet |
| Use Case | Dual-ESP32 autopilot cross-link (3-wire UART preferred for safety-critical) |

ESP-NOW is used for non-safety-critical ESP32-to-ESP32 communication (e.g., environmental sensor sharing between nodes managed by different Jetsons). For safety-critical dual-ESP32 links (autopilot pair), dedicated 3-wire UART provides higher reliability and lower latency.

**NMEA 0183 (instrument bus) for sensor integration:**

| Parameter | Value |
|-----------|-------|
| Protocol | NMEA 0183 (EIA-422 single-talker, multi-listener) |
| Baud Rate | 4800 baud (standard), 38400 (AIS high-speed) |
| Topology | Single talker per bus, listeners via tees |
| NEXUS Role | Passive listener only (never transmits on instrument bus) |

### 6.3 Communication Pattern Comparison Table for NEXUS

| Pattern | Protocol | Latency | Bandwidth | Topology | Fault Isolation | NEXUS Use |
|---------|----------|---------|-----------|----------|-----------------|-----------|
| **Request-Reply** | gRPC | <1ms (LAN) | 1 Gbps | Star (Ethernet) | Per-connection | Jetson-to-Jetson RPC |
| **Request-Reply** | VesselLink/RS-422 | 0.35-1.6ms | 93 KB/s | Star (serial) | Per-link | Jetson-to-ESP32 commands |
| **Publish-Subscribe** | MQTT | <1ms (LAN) | Variable | Star (broker) | Per-topic | Jetson-to-Cloud telemetry |
| **Request-Reply** | UART cross-link | <0.1ms | 11.5 KB/s | Point-to-point | Isolated | ESP32 dual-pair heartbeat |
| **Publish-Subscribe** | ESP-NOW | <1ms | ~250 B/packet | Mesh | Per-node | ESP32-to-ESP32 non-critical |
| **Listen-Only** | NMEA 0183 | N/A | 480 bytes/s | Bus (multi-drop) | Bus-wide | Instrument data ingestion |

---

## 7. Real-Time Distributed Systems

### 7.1 Time Synchronization

Accurate time synchronization is essential for any distributed system, and critical for real-time control systems where actuator commands must be issued at precise intervals.

| Protocol | Accuracy | Mechanism | Network Requirements | NEXUS Use |
|----------|----------|-----------|---------------------|-----------|
| **NTP (Network Time Protocol)** | 1-100ms (typical 10-50ms) | Hierarchical servers, Marzullo's algorithm | UDP port 123, Internet or LAN | Jetson OS time sync via NTP |
| **PTP (Precision Time Protocol, IEEE 1588)** | 100ns - 1μs | Hardware timestamps, Best Master Clock algorithm | Ethernet (layer 2), hardware support | Not used (not available on Jetson) |
| **GPS/GNSS** | 10-40ns | Satellite signals with atomic clocks | Antenna with sky view | Potential for fleet-wide time sync |
| **Lamport clocks** | Logical (not physical) | Software counters | None (local) | Event ordering in reflex deployment |
| **RS-422 heartbeat** | ~1ms (nominal) | Periodic pulse from Jetson to ESP32 | Dedicated serial link | ESP32 tick synchronization |

**NEXUS time synchronization strategy:**

1. **Jetson layer:** NTP synchronization via GPS-disciplined NTP server on Jetson-Alpha (when GPS fix is available). Typical accuracy: 1-5ms on LAN with GPS reference.
2. **ESP32 layer:** No NTP/PTP. ESP32s run a 1ms FreeRTOS tick (configTICK_RATE_HZ = 1000). Time is relative (milliseconds since boot). Jetson-to-ESP32 heartbeat provides approximate synchronization.
3. **Fleet layer:** GPS provides absolute time reference on each vessel. Clock skew between vessels is bounded by GPS accuracy (typically <100ns) plus NTP synchronization error (1-5ms on LAN).

### 7.2 Real-Time Scheduling in Distributed Systems

Real-time scheduling in a distributed system must account for communication delays, jitter, and the possibility of missed deadlines.

| Scheduling Strategy | Description | NEXUS Application |
|--------------------|-------------|-------------------|
| **Rate-monotonic** | Fixed-priority; shorter period = higher priority | ESP32 FreeRTOS task priorities (PID at priority 24, watchdog at 23) |
| **Deadline-monotonic** | Fixed-priority; shorter deadline = higher priority | Safety supervisor (deadline: 100ms check interval) |
| **Earliest Deadline First (EDF)** | Dynamic priority; task with nearest deadline runs first | Not used (EDF requires runtime priority changes, incompatible with FreeRTOS) |
| **Time-triggered** | All actions occur at predefined time slots | ESP32 reflex execution at 1ms ticks |
| **Hierarchical** | Different scheduling policies at different system levels | NEXUS: EDF-like scheduling on Jetson (Linux CFS), fixed-priority on ESP32 (FreeRTOS) |

**NEXUS scheduling hierarchy:**

```
Level 0 (Hardware):  ISR — <100μs response, absolute priority
Level 1 (Firmware):  FreeRTOS tasks — fixed priority, 1ms tick
  - task_pid_control:        Priority 24, Period 10ms
  - task_watchdog_heartbeat:  Priority 23, Period 100ms
  - task_serial_jetson_rx:    Priority 19, Event-driven
Level 2 (Application):  Linux processes — CFS scheduler
  - DeepStream (camera pipeline): ~30ms frame processing
  - Qwen2.5-7B (LLM inference): ~3s per response
  - MQTT broker:               continuous
```

### 7.3 CAN Bus as Real-Time Distributed Protocol

CAN bus (Controller Area Network, ISO 11898) is the dominant real-time communication protocol in automotive and industrial systems. Its relevance to NEXUS lies in the architectural decision to **not** use CAN for ESP32-to-Jetson communication.

| Attribute | CAN Bus | RS-422 (NEXUS choice) |
|-----------|---------|---------------------|
| **Data rate** | 1 Mbps (CAN), 5 Mbps (CAN FD) | 115200 bps |
| **Topology** | Multi-drop bus (up to 80 nodes) | Point-to-point star |
| **Arbitration** | Non-destructive bitwise (priority-based) | None (dedicated links) |
| **Determinism** | Yes (priority-based, bounded worst-case) | Yes (no contention) |
| **Fault confinement** | Automatic (error frames, bus-off) | Manual (link failure isolates one node) |
| **Physical layer** | Differential, 2-wire | Differential, 4-wire (full duplex) |
| **Max cable length** | 40m @ 1 Mbps, 500m @ 50 Kbps | 1200m @ low speed, ~300m @ 115200 |
| **Cost per node** | ~$15 (transceiver + connector) | ~$8 (transceiver + cable) |
| **Debuggability** | Requires CAN analyzer tools | Standard serial terminal |

**Why NEXUS chose RS-422 over CAN:**
1. RS-422 is simpler to implement on Jetson (no custom kernel modules, standard USB serial driver).
2. RS-422 supports longer cable runs (300m practical at 115200 vs 40m at 1Mbps CAN).
3. RS-422 is full-duplex (no collision risk, no arbitration delay).
4. RS-422 is debuggable with any terminal program (JSON payloads are human-readable).
5. RS-422 bandwidth is sufficient (93 KB/s vs <40 KB/s actual load per Jetson).

### 7.4 NEXUS's Timing Requirements: 1ms Reflex Ticks

NEXUS's ESP32 nodes execute reflex bytecode at a **1ms tick rate** (configTICK_RATE_HZ = 1000 on FreeRTOS). This means:

- Each tick, the Reflex VM scheduler checks for pending reflexes, selects the highest-priority runnable reflex, and executes it within the cycle budget (50,000 instructions maximum).
- The PID control loop runs at 10ms (every 10th tick), consuming typically 368 cycles of the 50,000-cycle budget (0.7% utilization).
- The heartbeat monitor checks for Jetson heartbeats every 100ms (every 100th tick).
- The external hardware watchdog is kicked every 200ms.

**Timing synchronization across nodes:**

Within a single vessel, ESP32 tick synchronization is maintained by the Jetson heartbeat (100ms intervals). Each ESP32 receives the heartbeat, uses it to calibrate its local clock, and adjusts its timestamp for telemetry messages. The accuracy of this synchronization is bounded by:

- Serial latency jitter: ±0.1ms (RS-422 at 115200 baud)
- Jetson heartbeat scheduling jitter: ±10ms (Linux CFS scheduler)
- ESP32 FreeRTOS tick accuracy: ±1μs (crystal oscillator)

The total synchronization error between ESP32 nodes on the same vessel is approximately ±10ms — sufficient for the 10ms PID control period but insufficient for microsecond-precision applications.

Across vessels, GPS provides a common time reference. When GPS fix is available on both vessels, clock skew is bounded by GPS accuracy (typically <100ns) plus the NTP synchronization chain (1-5ms on LAN). This enables fleet-level temporal ordering of events for learning pipeline data aggregation.

---

## 8. Edge Computing

### 8.1 The Cloud-Edge-Device Continuum

Modern computing architectures are increasingly organized along a continuum from cloud datacenters to edge devices:

| Tier | Location | Latency | Bandwidth | Compute | NEXUS Mapping |
|------|----------|---------|-----------|---------|---------------|
| **Cloud** | Remote datacenter | 20-80ms (Starlink) | 5-25 Mbps up | Virtually unlimited | Fleet management, model training, OTA distribution |
| **Edge** | Vessel (Jetson cluster) | <1ms (LAN) | 1 Gbps | 201 TOPS (3× Orin Nano) | AI inference, reflex synthesis, data aggregation |
| **Device** | ESP32 nodes | <0.1ms (serial) | 93 KB/s | 240 MHz Xtensa | Sensor acquisition, reflex execution, actuator control |

**Key insight:** NEXUS is fundamentally an **edge computing architecture**. The critical control loops (autopilot PID, engine monitoring, safety) execute entirely on the edge and device tiers. The cloud is a supplementary resource for fleet analytics and model training, not a dependency for operational safety.

### 8.2 Edge AI Processing

Edge AI refers to running machine learning inference on edge devices rather than in the cloud. NEXUS runs multiple AI models on the Jetson Orin Nano cluster:

| Model | Purpose | Location | Framework | Latency | Quantization |
|-------|---------|----------|-----------|---------|-------------|
| **Qwen2.5-Coder-7B** | Reflex synthesis from narrative | Jetson | llama.cpp (Q4_K_M) | ~29s for 500 tokens | 4-bit integer |
| **YOLOv8-nano** | Object detection (fish species, deck safety) | Jetson-Bravo | TensorRT (FP16/INT8) | ~30ms per frame | FP16 |
| **Whisper** | Speech-to-text (crew voice commands) | Jetson | faster-whisper (CTranslate2) | ~500ms per utterance | FP16 |
| **Piper TTS** | Text-to-speech (system announcements) | Jetson | Piper (CPU) | ~200ms per phrase | N/A (non-neural) |
| **Reflex VM bytecode** | Real-time control programs | ESP32 | Custom VM (see spec) | <1ms per tick | N/A (deterministic) |

**Edge AI advantages for NEXUS:**
1. **Latency:** Object detection at 30ms on-edge vs 80ms+ round-trip to cloud (Starlink). Critical for real-time safety monitoring.
2. **Availability:** AI inference continues during cloud outages (Starlink 99.5% uptime means ~44 hours of downtime per year).
3. **Bandwidth:** Camera frames processed locally (~45 Mbps) vs streaming to cloud (~45 Mbps uplink — exceeds Starlink capacity).
4. **Privacy:** Camera data never leaves the vessel. No GDPR concerns about transmitting video of crew members.
5. **Determinism:** Edge inference has bounded, predictable latency. Cloud inference has variable latency due to network conditions.

### 8.3 Federated Learning — Relevance to NEXUS Fleet Learning

**Federated Learning (FL)** is a machine learning approach where multiple edge devices collaboratively train a shared model without sharing raw data. Each device trains on its local data and sends only model updates (gradients) to a central server, which aggregates the updates.

**FL for NEXUS fleet learning:**

The NEXUS learning pipeline (see [[AI Model Stack]]) can be naturally extended to federated learning:

| FL Phase | Traditional ML | NEXUS Federated |
|---------|---------------|-----------------|
| **Data collection** | Centralized in cloud | Each vessel collects data locally |
| **Feature engineering** | Centralized | Each vessel computes features locally |
| **Model training** | Centralized GPU cluster | Each Jetson trains locally on its vessel's data |
| **Aggregation** | Single model | Federated averaging: weighted average of vessel model updates |
| **Deployment** | Push to all vessels | Each vessel validates and deploys its own model |

**Benefits of federated learning for NEXUS:**
1. **Data privacy:** Raw sensor data (camera, audio, GPS) never leaves the vessel.
2. **Bandwidth efficiency:** Only model gradients (~500 KB per vessel per update) are transmitted vs raw observation data (~30 GB per vessel per day).
3. **Heterogeneity:** Each vessel's model adapts to local conditions (sea state, species distribution, vessel load).
4. **Communication resilience:** Model updates can be batched and sent when bandwidth is available. No real-time connectivity required.

**Challenges:**
1. **Non-IID data:** Different vessels experience different conditions, leading to model divergence.
2. **Straggler vessels:** Slower Jetsons or vessels with less data slow down the federated averaging round.
3. **Security:** A compromised vessel could submit malicious model updates. Requires robust aggregation (e.g., Krum's algorithm, trimmed mean).

### 8.4 NEXUS's Three-Tier as Edge Computing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLOUD TIER (Starlink)                    │
│                                                             │
│  • Fleet management dashboard                               │
│  • Federated learning aggregation                            │
│  • OTA firmware distribution                                 │
│  • Historical data archival                                  │
│  • Model training (Qwen2.5 fine-tuning)                     │
│                                                             │
│  Uplink: ~174 B/s (1.4 Kbps) — telemetry + anomalies       │
│  Downlink: ~5 KB/s — OTA firmware + model updates           │
│  Availability: 99.5% (Starlink)                             │
│  Latency: 20-80ms RTT                                       │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────┐
│                    EDGE TIER (Vessel)                        │
│                                                             │
│  3× Jetson Orin Nano Super — 201 TOPS total                 │
│  • YOLOv8-nano object detection (30ms/frame)                │
│  • Whisper speech-to-text (500ms/utterance)                  │
│  • Reflex synthesis (Qwen2.5, 29s/500 tokens)               │
│  • Pattern discovery (HDBSCAN, BOCPD)                       │
│  • Trust score computation                                  │
│  • MQTT broker (Mosquitto)                                  │
│  • Redis (leader election, caching)                         │
│  • 512GB NVMe (72-hour rolling buffer)                      │
│                                                             │
│  Compute: 201 TOPS | Storage: 1.5 TB | Power: ~81W         │
│  Latency: <1ms (LAN) | Availability: 99.95%+               │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────┐
│                   DEVICE TIER (ESP32)                        │
│                                                             │
│  8-12× ESP32-S3 @ 240 MHz — 512KB SRAM each               │
│  • Reflex bytecode VM execution (1ms tick)                  │
│  • PID autopilot control (10ms loop)                        │
│  • Sensor acquisition (compass, rudder, temperature)        │
│  • Actuator control (solenoids, relays, motors)            │
│  • Heartbeat monitoring                                     │
│  • Safety state machine                                     │
│                                                             │
│  Compute: 240 MHz each | Storage: 8MB flash | Power: ~2W each│
│  Latency: <0.1ms (serial) | Availability: 99.99%+          │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Distributed State Management

### 9.1 Distributed Shared Memory

**Distributed Shared Memory (DSM)** provides the illusion of a shared memory space across multiple nodes, even though memory is physically distributed. DSM systems must handle:

| Challenge | Description | NEXUS Approach |
|-----------|-------------|---------------|
| **Consistency** | How quickly do writes propagate? | MQTT QoS 2 for critical state, QoS 0 for telemetry |
| **Coherence** | How are concurrent writes handled? | Last-Writer-Wins with timestamps (CRDT merge) |
| **Replication** | Where is data stored? | Jetson NVMe (local), cloud (optional) |
| **Fault tolerance** | What happens when a node fails? | Dual-ESP32 redundancy, Jetson hot standby |

NEXUS does not implement classical DSM. Instead, it uses **logical shared memory** through MQTT topics. Multiple Jetsons can read and write to topics like `nexus/cluster/trust_scores`, and the broker ensures message ordering within each topic. This provides the semantic equivalent of shared memory without the complexity of hardware-level memory coherence protocols.

### 9.2 State Machine Replication

**State Machine Replication (SMR)** is the principle that if multiple nodes start in the same initial state and execute the same sequence of commands in the same order, they will end in the same final state. This is the theoretical foundation of Raft, Paxos, and virtually all consensus protocols.

**NEXUS applies SMR at three levels:**

1. **Jetson cluster:** All three Jetsons maintain independent trust score databases. When the leader proposes a reflex deployment, all Jetsons validate and execute the deployment. The reflex bytecode is deterministic (proven by the VM specification), ensuring identical execution across all nodes.
2. **Dual-ESP32 autopilot pair:** Both ESP32s in the autopilot pair independently execute the PID control loop. The STANDBY compares its output with the ACTIVE's reported output, detecting discrepancies via sensor cross-checking.
3. **Fleet-level reflex deployment:** When the fleet leader proposes a reflex update, all vessels validate the bytecode and, if accepted, deploy it. Identical bytecode on identical VMs produces identical outputs.

### 9.3 Eventual Consistency Models

**Eventual consistency** guarantees that if no new updates are made, eventually all accesses will return the last updated value. The "eventually" qualifier is critical: there is no bound on how long convergence takes unless one is explicitly provided.

| Consistency Level | Guarantee | Example | NEXUS Use |
|------------------|-----------|---------|-----------|
| **Strong** | Reads always return most recent write | Traditional SQL databases | Not used (requires coordination unavailable at sea) |
| **Sequential** | Reads see all writes in some sequential order | Spanner, CockroachDB | Not used (requires distributed transactions) |
| **Causal** | Causally related operations are seen by all in order | DynamoDB (consistent reads) | Trust score updates (LWW with causal ordering) |
| **Read-your-writes** | A node always sees its own writes | Redis with write-through | Jetson local state (Redis + SQLite) |
| **Eventual** | All replicas converge given no new writes | Cassandra, CouchDB | Fleet telemetry (MQTT QoS 0) |
| **Bounded staleness** | Reads are at most T seconds stale | DynamoDB consistent reads | Intra-vessel trust scores (<1s staleness) |

### 9.4 NEXUS Trust Score as Distributed State

The NEXUS trust score is a **distributed state variable** that must be synchronized across all Jetsons within a vessel and, eventually, across the fleet.

**Trust score consistency requirements:**

| Scenario | Consistency Requirement | Mechanism |
|----------|------------------------|-----------|
| Jetson cluster (intra-vessel) | Bounded staleness <1s | MQTT QoS 2 with LWW merge |
| Fleet (inter-vessel) | Eventual, bounded staleness <1h | MQTT QoS 1 with periodic sync |
| During partition | Local-only computation continues | Each Jetson/vessel computes independently |
| Partition heal | Convergence to single value | CRDT merge (LWW with timestamp) |
| Reflex deployment decision | Must be consistent at decision time | 2PC with quorum (2-of-3) |

**Trust score synchronization protocol:**

1. **Local computation:** Each Jetson independently computes trust scores for its connected ESP32s based on locally observed events.
2. **Intra-vessel sync:** Jetsons publish trust scores to MQTT topic `nexus/jetson/{id}/trust` with QoS 2. Other Jetsons receive and merge using LWW CRDT.
3. **Fleet sync:** The leader Jetson publishes aggregated trust scores to `nexus/cluster/fleet_trust` with QoS 1. Other vessels receive and merge.
4. **Conflict resolution:** When two vessels report different trust scores for the same ESP32 (which should not happen, since ESP32s are vessel-local), the LWW rule selects the update with the latest timestamp.

**Why this works:** The trust score is a monotonically-evolving state variable that changes slowly (time constant: 27.4 days for gain, 1.2 days for loss). Rapid synchronization is not required — bounded staleness of seconds to hours is perfectly acceptable. The CRDT merge guarantees convergence regardless of partition duration or message ordering.

---

## 10. Swarm Robotics as Distributed Systems

### 10.1 Communication Models in Swarm Robotics

Swarm robotics applies principles from biological swarms (ant colonies, bee hives, fish schools) to groups of simple robots that collectively accomplish complex tasks. The fundamental challenge is achieving coherent global behavior from local interactions.

| Communication Model | Description | Scalability | Robustness | NEXUS Relevance |
|--------------------|-------------|-------------|------------|-----------------|
| **Direct** | Robots communicate via explicit messages | Low (O(N²) message overhead) | Medium | Vessel-to-vessel MQTT |
| **Stigmergic** | Robots communicate by modifying the shared environment | Very High | Very High | Not directly used, but conceptually similar to shared fleet state |
| **Implicit** | Robots observe each other's behavior without communication | High | High | Dual-ESP32 sensor cross-checking |
| **Hierarchical** | Communication through organized layers (leader → subordinates) | Medium | Medium | Jetson → ESP32 hierarchy |
| **Hybrid** | Combination of above | High | High | NEXUS's approach |

### 10.2 Decentralized Decision Making

In swarm robotics, **decentralized decision making** requires each robot to make locally optimal decisions that collectively produce globally optimal outcomes.

**Approaches to decentralized decision making:**

| Approach | Mechanism | Convergence Guarantee | NEXUS Application |
|----------|-----------|----------------------|-------------------|
| **Threshold-based** | Each robot uses local threshold to decide | Converges under bounded information discrepancy | ESP32 safety state machine (heartbeat threshold → mode change) |
| **Voting** | Robots vote on decisions | Converges with majority | Communal veto mechanism (3+ agents can veto a proposed action) |
| **Market-based** | Robots bid for tasks (Contract Net) | Converges with complete information | Fleet task allocation |
| **Chemotaxis-inspired** | Robots follow gradients in environment | Converges under smooth gradient | Not directly used |
| **Consensus** | Robots agree via consensus protocol | Converges with quorum | Raft-based reflex deployment |

**NEXUS's Ubuntu-inspired communal veto:**

NEXUS includes a distinctive consensus mechanism called the **communal veto**, inspired by the Southern African philosophical tradition of Ubuntu ("I am because we are"). If three or more agents in a subsystem detect that a proposed action would violate safety constraints, they can collectively veto the action. This is implemented through the trust score system: if the proposing agent's trust score drops below the autonomy threshold for the relevant subsystem, its reflexes are automatically suspended.

### 10.3 Emergent Collective Behavior

**Emergent behavior** in swarm robotics refers to complex global patterns that arise from simple local rules, without any centralized control. Examples include:

- **Flocking:** Each bird follows three simple rules (separation, alignment, cohesion) and the flock exhibits complex, coordinated motion.
- **Ant foraging:** Ants leave pheromone trails; shorter trails receive more traffic and stronger pheromone, converging on optimal paths.
- **Schooling:** Fish align with their nearest neighbors and maintain minimum distance, creating coordinated evasion maneuvers.

**NEXUS emergent behaviors:**

| Behavior | Local Rule | Emergent Result |
|----------|-----------|----------------|
| **Fleet formation** | Each vessel adjusts heading based on neighbors' positions | Coordinated search pattern |
| **Trust-based task allocation** | Vessels with higher trust scores get priority for critical tasks | Reliable vessels handle more critical operations |
| **Collective threat detection** | Multiple vessels report anomalies; fleet aggregates | False positive filtering (anomalous reading on one vessel, not corroborated by others) |
| **Distributed learning** | Each vessel trains on local data; fleet aggregates | Model that works across diverse conditions |

### 10.4 NEXUS Colony Model as Swarm Robotics

The NEXUS **colony model** (see [[The Colony Thesis]]) explicitly frames the fleet as a biological colony — a distributed system with emergent behavior:

| Biological Metaphor | NEXUS Implementation |
|--------------------|---------------------|
| **Organism** | Individual vessel (3 Jetsons + 12 ESP32s) |
| **Organ** | Jetson cluster (nervous system), ESP32 nodes (muscles + sensors) |
| **Cell** | ESP32 microcontroller node |
| **Reflex** (innate behavior) | Deployed bytecode on ESP32 VM |
| **Learning** (acquired behavior) | Pattern discovery → reflex synthesis → A/B test → deployment |
| **Evolution** (generational improvement) | Production → variant → A/B test → evolved bytecode |
| **Immune system** | Four-tier safety system (hardware interlock → firmware guard → supervisor → application) |
| **Nervous system** | Jetson cluster (cognitive layer) + RS-422 serial links (peripheral nerves) |
| **Colony coordination** | Fleet MQTT communication + CRDT-based state merging |
| **Colony resilience** | No single vessel failure compromises the colony |

---

## 11. Network Topologies

### 11.1 Overview of Network Topologies

| Topology | Description | Advantages | Disadvantages | NEXUS Use |
|----------|-------------|------------|---------------|-----------|
| **Star** | All nodes connect to a central hub | Simple, easy to manage, no routing | Hub is single point of failure | RS-422 star (ESP32 → Jetson), Ethernet switch (Jetson → Jetson) |
| **Ring** | Nodes connected in a circular chain | Equal access, no hub SPOF (dual ring) | Latency accumulates per hop | Not used |
| **Mesh** | Every node connects to every other | Maximum redundancy, multiple paths | Expensive, complex cabling | ESP-NOW for ESP32-to-ESP32 (partial mesh) |
| **Bus** | All nodes share a single communication channel | Simple wiring, low cost | Single point of failure, contention | NMEA 0183 instrument bus |
| **Tree** | Hierarchical star topology | Scalable, organized | Parent node failure isolates subtree | NEXUS three-tier hierarchy |
| **Hybrid** | Combination of above | Optimized for each level | Complex | NEXUS's overall topology |

### 11.2 Physical Topology in NEXUS

NEXUS uses **three distinct physical topologies**, each optimized for its communication tier:

```
TIER 0 — ETHERNET STAR (Jetson interconnect):
     JETSON-α ──┐
     JETSON-β ──┼── Gigabit Switch ── WiFi AP (monitoring only)
     JETSON-γ ──┘

TIER 1 — RS-422 STAR (Jetson-to-ESP32):
     JETSON-α → ESP32-AP-PRI, ESP32-AP-BAK, ESP32-ENV
     JETSON-β → ESP32-CAM, ESP32-DECK, ESP32-BILGE
     JETSON-γ → ESP32-ENG-PRI, ESP32-ENG-BAK, ESP32-TANK

TIER 2 — NMEA 0183 BUS (instrument bus):
     GPS ──┐
     Compass ──┼── Listener Tees ── JETSON-α (NMEA mux)
     Depth ──┘

ESP32-TO-ESP32 (safety-critical dual pair):
     AP-PRI ←── 3-wire UART ──→ AP-BAK
     ENG-PRI ←── 3-wire UART ──→ ENG-BAK

ESP32-TO-ESP32 (non-critical):
     Partial ESP-NOW mesh for inter-node sensor sharing
```

### 11.3 Logical Topology: NEXUS's Three-Tier Hierarchy

The logical topology of NEXUS is a **three-tier tree** with the cloud at the root:

```
CLOUD (Fleet Manager, Starlink)
│
├── VESSEL A (Peer)
│   ├── Jetson-α (Leader)
│   │   ├── ESP32-AP-PRI (Autopilot Primary)
│   │   ├── ESP32-AP-BAK (Autopilot Backup)
│   │   └── ESP32-ENV (Environmental Sensor)
│   ├── Jetson-β (Follower)
│   │   ├── ESP32-CAM (Camera PTZ)
│   │   ├── ESP32-DECK (Deck Equipment)
│   │   └── ESP32-BILGE (Bilge Monitor)
│   └── Jetson-γ (Follower)
│       ├── ESP32-ENG-PRI (Engine Primary)
│       ├── ESP32-ENG-BAK (Engine Backup)
│       └── ESP32-TANK (Tank Level)
│
├── VESSEL B (Peer)
│   └── [Same structure as Vessel A]
│
└── VESSEL N (Peer)
    └── [Same structure as Vessel A]
```

### 11.4 Fault Tolerance of Different Topologies

| Topology | Single Link Failure | Single Node Failure | N Nodes Lost | Recovery Time |
|----------|---------------------|---------------------|--------------|---------------|
| **Star (NEXUS RS-422)** | 1 ESP32 isolated | 1 ESP32 isolated | 1 | Hot-swap (<5 min) |
| **Dual Star (redundant hub)** | No ESP32 lost | Hub failure: all ESP32 lost (if not redundant) | 0 (with redundancy) | <100ms (failover) |
| **Ring** | 0-2 ESP32s isolated (depends on location) | 1 node breaks ring into linear chain | 0-2 | Manual repair |
| **Full Mesh** | No node isolated | 1 node lost | 0 | Automatic |
| **Bus (NMEA)** | All downstream nodes lost | Device failure: may not affect others | Potentially all | Depends on failure mode |
| **NEXUS hybrid** | At most 1 ESP32 per link | Jetson failure: 4 ESP32s lose coordinator (but continue standalone) | 0 ESP32s (safety-critical), 4 ESP32s lose AI capability | ESP32 hot-swap; Jetson failover ~300ms |

---

## 12. Scalability Analysis

### 12.1 How Many Vessels Can a NEXUS Fleet Support?

The scalability of a NEXUS fleet is constrained by multiple factors:

| Constraint | Limiting Factor | Estimated Maximum | Notes |
|-----------|----------------|-------------------|-------|
| **MQTT broker** | Messages per second | ~100 vessels (125 msg/s per vessel, ~100K msg/s broker limit) | Mosquitto single instance |
| **Trust score sync** | CRDT merge overhead | ~500 vessels (LWW merge is O(N) per vessel) | Quadratic merge cost |
| **Fleet task allocation** | Communication complexity | ~50 vessels (O(N²) pairwise communication) | Gossip protocol reduces to O(N log N) |
| **Cloud bandwidth** | Starlink uplink | ~100 vessels (each vessel sends ~174 B/s; fleet sends ~17 KB/s) | Well within 5-25 Mbps uplink |
| **OTA distribution** | Concurrent firmware transfers | ~20 vessels (each OTA transfer: ~14.6 KB/s per ESP32 link) | P2P distribution would improve this |
| **Human monitoring** | Captain attention | ~10 vessels (one captain per vessel) | Autonomous operation needed beyond |

**Practical fleet size recommendation:** 5-20 vessels with a single MQTT broker. Beyond 20 vessels, hierarchical MQTT clustering (EMQX) is recommended.

### 12.2 Communication Bandwidth Constraints

| Communication Link | Bandwidth | Utilization (per vessel) | Bottleneck? |
|-------------------|-----------|--------------------------|-------------|
| RS-422 (Jetson → ESP32) | 93 KB/s | 0.90% (820 B/s normal) | No (massive headroom) |
| RS-422 (Jetson → ESP32, OTA) | 93 KB/s | 16.0% (14.6 KB/s) | No |
| Gigabit Ethernet (Jetson interconnect) | 125 MB/s | ~2 MB/s (camera streams + telemetry) | No |
| MQTT (LAN) | Virtually unlimited (100K+ msg/s) | 125 msg/s per vessel | No (for <100 vessels) |
| Starlink uplink | 625 KB/s - 3.1 MB/s | 174 B/s (0.01%) | No |
| Starlink latency | 20-80ms RTT | N/A (critical for real-time, acceptable for sync) | Yes (limits real-time cloud interaction) |

### 12.3 Trust Score Synchronization Overhead

Trust score synchronization uses a CRDT merge with O(N) cost per merge operation, where N is the number of vessels:

| Fleet Size | Messages per Sync Cycle | Bandwidth per Sync | Sync Frequency | Total Overhead |
|-----------|------------------------|--------------------|----------------|----------------|
| 5 vessels | 5 × 200 B = 1 KB | 1 KB | 1/minute | ~17 B/s (negligible) |
| 20 vessels | 20 × 200 B = 4 KB | 4 KB | 1/minute | ~67 B/s (negligible) |
| 100 vessels | 100 × 200 B = 20 KB | 20 KB | 1/minute | ~333 B/s (negligible) |
| 500 vessels | 500 × 200 B = 100 KB | 100 KB | 1/minute | ~1.7 KB/s (manageable) |

The trust score synchronization overhead is negligible at all practical fleet sizes. The bottleneck is not bandwidth but **consistency**: with 500 vessels, each computing trust scores independently, the LWW merge may take significant time to propagate updates across the fleet.

### 12.4 Hot-Loading Bytecode Across Fleet

Deploying reflex bytecode across the fleet is a **scatter-gather** operation:

1. **Scatter (leader → all vessels):** Leader sends reflex bytecode (typically <2 KB) to all vessels via MQTT QoS 2.
2. **Validate (each vessel, in parallel):** Each vessel's Jetson cluster validates the bytecode (determinism check, safety invariant check).
3. **Deploy (each vessel, in parallel):** Each vessel's leader Jetson deploys to its ESP32s via RS-422.
4. **Gather (all vessels → leader):** Each vessel reports deployment status.

**Deployment timing:**

| Phase | Duration | Bottleneck |
|-------|----------|-----------|
| Scatter (leader → vessels) | 20-80ms (MQTT via Starlink) | Starlink latency |
| Validate (per vessel) | ~100ms (VM determinism check) | Jetson CPU |
| Deploy (per vessel) | ~2 min (RS-422 at 115200, ~1.5MB) | RS-422 bandwidth |
| Gather (vessels → leader) | 20-80ms (MQTT via Starlink) | Starlink latency |
| **Total (sequential)** | ~2.5 min per vessel, N vessels serial | |
| **Total (parallel, with phased rollout)** | ~2.5 min (all vessels in parallel) | |
| **Total (rolling deployment with A/B test)** | 60s probation + 24-48h A/B observation | Trust score convergence time |

---

## 13. Synthesis: NEXUS as a Distributed System

NEXUS is a **safety-critical, real-time, heterogeneous, hierarchical distributed system** that operates in a physically harsh, communication-constrained environment. Its distributed systems properties can be summarized as follows:

### 13.1 Design Principles Summary

| Principle | Implementation | Rationale |
|-----------|---------------|-----------|
| **Availability over Consistency** | AP system with CRDT merge; ESP32s run autonomously during partitions | Vessel safety cannot depend on communication |
| **Consistency where required** | 2PC for reflex deployment; quorum for safety-critical decisions | Bytecode must be deployed atomically or not at all |
| **Hierarchical within, peer across** | Jetson → ESP32 hierarchy within vessel; vessel-to-vessel peer equality | Matches physical reality and organizational structure |
| **Defense in depth** | Four-tier safety system independent of distributed consensus | Software consensus can fail; hardware cannot be compromised |
| **Graceful degradation** | Five degradation levels from FULL to SAFE_STATE | Every component failure reduces capability, never eliminates safety |
| **Local autonomy** | ESP32 reflex bytecode runs at 1ms without Jetson communication | Control loop must survive any communication failure |
| **Eventual convergence** | CRDTs for trust scores; LWW merge on partition heal | Fleet state converges when connectivity is restored |

### 13.2 Key Architectural Decisions

| Decision | Choice | Rejected Alternative | Reason |
|----------|--------|---------------------|--------|
| Intra-vessel bus | RS-422 serial | CAN bus | Simpler, debuggable, longer range, no Jetson HAT needed |
| Inter-Jetson protocol | gRPC + MQTT | ROS 2 DDS | gRPC for synchronous RPC, MQTT for async telemetry |
| Inter-vessel protocol | MQTT over TLS/VPN | Custom protocol | Standard, reliable, well-supported |
| Consensus for deployment | 2PC (Raft-inspired) | Full PBFT | 3-Jetson cluster insufficient for 4-node BFT |
| State synchronization | CRDT (LWW Register) | Strong consistency | Communication at sea is unreliable; eventual consistency is sufficient |
| Time sync | NTP + GPS | PTP (IEEE 1588) | PTP requires hardware support not available on Jetson |
| WiFi | Monitoring only | Control path | Non-deterministic latency, EMI interference, security |

### 13.3 Open Challenges

| Challenge | Current Status | Proposed Solution |
|-----------|----------------|-------------------|
| Byzantine fault tolerance | BFT-aware design only; no full PBFT | Add 4th Jetson for 3f+1 BFT if regulatory requirements demand it |
| Fleet-wide clock synchronization | GPS-based, ~1-5ms accuracy | PTP hardware on Jetson upgrade path for sub-microsecond sync |
| Scalability beyond 100 vessels | MQTT single-broker architecture | Hierarchical broker clustering (EMQX) with gossip-based state propagation |
| Federated learning deployment | Conceptual design only | Implement federated averaging with Krum's aggregator for Byzantine robustness |
| Dynamic topology (vessels joining/leaving) | Manual provisioning | Zero-config provisioning via MQTT service discovery + ESP-NOW beaconing |
| Formal verification of distributed protocols | Simulation-based testing only | Model checking (TLA+) for consensus and safety protocols |

---

## 14. References

1. Brewer, E. A. (2000). "Towards robust distributed systems." *PODC '00*.
2. Gilbert, S., & Lynch, N. (2002). "Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services." *ACM SIGACT News*, 33(2), 51-59.
3. Lamport, L. (1989). "The part-time parliament." Technical Report 49, Digital Equipment Corporation.
4. Lamport, L. (1998). "The part-time parliament." *ACM TOCS*, 16(2), 133-169.
5. Ongaro, D., & Ousterhout, J. (2014). "In search of an understandable consensus algorithm." *ATC '14*.
6. Castro, M., & Liskov, B. (1999). "Practical Byzantine fault tolerance." *OSDI '99*.
7. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011). "Conflict-free replicated data types." *SSS '11*.
8. Lamport, L. (1978). "Time, clocks, and the ordering of events in a distributed system." *Communications of the ACM*, 21(7), 558-565.
9. Abadi, D. (2012). "Consistency tradeoffs in modern distributed database system design: CAP is only part of the story." *IEEE Computer*, 45(2), 37-43.
10. Gray, J., & Lamport, L. (2006). "Consensus on transaction commit." *ACM TODS*, 31(1), 133-160.
11. Hewitt, C., Bishop, P., & Steiger, R. (1973). "A universal modular ACTOR formalism for artificial intelligence." *IJCAI '73*.
12. Davis, R., & Smith, R. G. (1983). "Negotiation as a metaphor for distributed problem solving." *Artificial Intelligence*, 20(1), 63-109.
13. Bonabeau, E., Dorigo, M., & Theraulaz, G. (1999). *Swarm Intelligence: From Natural to Artificial Systems*. Oxford University Press.
14. Dijkstra, E. W., & Scholten, C. S. (1980). "Termination detection for diffusing computations." *Information Processing Letters*, 11(1), 1-4.
15. Tanenbaum, A. S., & Van Steen, M. (2017). *Distributed Systems: Principles and Paradigms* (3rd ed.). Pearson.
16. Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
17. Lynch, N. A. (1996). *Distributed Algorithms*. Morgan Kaufmann.
18. NEXUS Platform. (2025). "NEXUS Safety System Specification" (NEXUS-SS-001 v2.0.0).
19. NEXUS Platform. (2025). "Trust Score Algorithm Specification" (NEXUS-SAFETY-TS-001 v1.0.0).
20. NEXUS Platform. (2025). "Master Consensus Architecture Document" (VRP-MCA-2025-016).

---

*This article is part of the NEXUS Robotics Platform Knowledge Base. For related topics, see [[agent_communication_languages]] for the theoretical foundations of inter-agent communication, and [[embedded_and_realtime_systems]] for the real-time computing constraints that shape NEXUS's distributed system design.*
