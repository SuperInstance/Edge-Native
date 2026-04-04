# NEXUS Platform — Production Specification Master Index

## Version: 1.0 | Date: 2026-03-29 | Status: Production-Ready Draft

---

## File Manifest

### Protocol Layer
| File | Lines | Description |
|------|-------|-------------|
| `protocol/wire_protocol_spec.md` | 1,047 | COBS framing, 10-byte header, 28 message types, 75 error codes, binary payload formats, reliability mechanisms |
| `protocol/message_payloads.json` | 2,156 | JSON Schema for all 23 JSON message payloads with 13 reusable definitions |

### Firmware Layer (ESP32 / MCU Runtime)
| File | Lines | Description |
|------|-------|-------------|
| `firmware/reflex_bytecode_vm_spec.md` | 2,487 | Complete 32-opcode ISA, 8-byte instruction encoding, memory model, safety invariants, timing analysis, portability requirements |
| `firmware/io_driver_interface.h` | 829 | C header with driver vtable, pin config types, error codes, safety callbacks, NVS keys — THE interface contract |
| `firmware/io_driver_registry.json` | 2,408 | 9+ I2C drivers with exact register sequences, selftest procedures, data schemas, known limitations |
| `firmware/memory_map_and_partitions.md` | 685 | SRAM/PSRAM byte-addressed maps, flash partition table (CSV), RTOS task config, DMA allocation, memory budget |

### Jetson Layer (Cognitive Cluster)
| File | Lines | Description |
|------|-------|-------------|
| `jetson/cluster_api.proto` | 934 | 6 gRPC services, 80+ message types — complete cluster API for node management, reflex orchestration, learning, autonomy, chat |
| `jetson/mqtt_topics.json` | 668 | 13 MQTT topics with QoS/retain, payload schemas, publisher/subscriber assignments, message rates |
| `jetson/module_interface.py` | 1,153 | Python ABC for all Jetson modules with lifecycle, hot-reload, resource budgets, concrete ThrottleMonitor example |
| `jetson/learning_pipeline_spec.md` | 2,140 | 5 pattern discovery algorithms, narration processing, A/B testing framework, reflex synthesis pipeline, 7 standardized metrics |

### Safety Layer
| File | Lines | Description |
|------|-------|-------------|
| `safety/safety_policy.json` | 864 | 10 global safety rules, 7 actuator profiles, 5 domain-specific rule sets, 6-stage validation pipeline |
| `safety/safety_system_spec.md` | 1,296 | Four-tier architecture, kill switch spec, watchdog spec, heartbeat protocol, overcurrent protection, boot sequence timing, certification checklist |
| `safety/trust_score_algorithm_spec.md` | 2,414 | Mathematical trust formula, 12 parameters, 15 event severities, 5 simulation scenarios, C and Python implementations |

### Portability Layer
| File | Lines | Description |
|------|-------|-------------|
| `ports/hardware_compatibility_matrix.json` | 2,128 | 3 specification tiers, 13 MCUs evaluated with porting effort, peripheral requirements, RTOS requirements, compiler flags |

### Architecture (Cross-Cutting)
| File | Lines | Description |
|------|-------|-------------|
| `ARCHITECTURE_DECISION_RECORDS.md` | ~800 | 28 ADRs with confidence levels, alternatives, and "what would change my mind" triggers |
| `SENIOR_ENGINEER_BUILD_GUIDE.md` | ~700 | Reading order, 9 build steps, test strategy, key metrics, development priorities, risk matrix, dependency graph |

### Developer Guide (Previous Phase)
| File | Location | Description |
|------|----------|-------------|
| `Post_Coding_Platform_Developer_Guide.pdf` | `post_coding_platform/` | Annotated developer guide with philosophical rationale |

---

## Specification Statistics
- **Total specification files:** 21
- **Total lines:** ~19,200
- **Estimated total size:** ~650KB
- **JSON schemas defined:** 5 (node_role_config, reflex_definition, message_payloads, mqtt_topics, hardware_compatibility, safety_policy, autonomy_state)
- **Message types defined:** 28
- **Error codes defined:** 75
- **VM opcodes defined:** 32
- **I2C drivers specified:** 9
- **MCU compatibility evaluations:** 13
- **Architecture decisions recorded:** 28

---

## Confidence Heat Map

Where "confidence" means: how confident are we that this is the RIGHT architecture choice, on a scale of LOW/MEDIUM/HIGH/VERY HIGH.

| Decision | Confidence | Risk If Wrong | Mitigation |
|----------|------------|--------------|------------|
| RS-422 serial for ESP32 link | VERY HIGH | Low | No change needed |
| Hardware kill switch + relay | VERY HIGH | Critical | Not applicable |
| External MAX6818 watchdog | VERY HIGH | Low | No change needed |
| Serial OTA (not WiFi) | VERY HIGH | Low | WiFi can be added later |
| Factory partition never OTA'd | VERY HIGH | Critical | Not applicable |
| 8-byte fixed instruction size | VERY HIGH | Low | VM redesign needed |
| CRC-16 (not CRC-32) | HIGH | Low | Change polynomial constant |
| jsmn + cJSON parser split | HIGH | Low | Use cJSON everywhere |
| PSRAM ring buffer (not SRAM) | HIGH | Low | Buffer shrinks, not fatal |
| Universal single firmware | HIGH | Medium | Add modular build system |
| Separate LLM for safety validation | VERY HIGH | Medium | Use same LLM with different prompt |
| Qwen2.5-Coder-7B local model | MEDIUM | Low | Swap to newer model when available |
| JSON state machines (not behavior trees) | MEDIUM | Medium | Add behavior tree support |
| LittleFS (not SPIFFS) | MEDIUM | Low | Swap to FAT32 with journal |
| gRPC + MQTT (not REST) | MEDIUM | Low | Add REST adapter |
| Asymmetric trust (25:1 ratio) | HIGH | Medium | Increase gain rate for low-risk |
| HDBSCAN for clustering | MEDIUM | Low | Swap to K-means |
| Inverse RL for pattern discovery | LOW | Low | Demote to optional analysis tool |
| 32 fixed opcodes (not extensible) | HIGH | Low | Reserve 4 extended opcodes |

---

## Build Complexity Estimate

| Component | Estimated Effort | Developer Skill Required |
|-----------|------------------|------------------------|
| Wire protocol (COBS + framing + dispatch) | 2-3 weeks | Senior embedded C |
| I/O abstraction layer + 5 drivers | 3-4 weeks | Senior embedded C + hardware |
| Reflex bytecode VM | 3-4 weeks | Senior embedded C + VM/compiler |
| Safety monitor (kill switch, watchdog, heartbeat) | 1-2 weeks | Embedded C + hardware debugging |
| ESP32 main integration | 1-2 weeks | Embedded C (ESP-IDF experience) |
| Jetson serial bridge + node manager | 2-3 weeks | Python + embedded protocols |
| Reflex orchestrator + gRPC services | 2-3 weeks | Python + gRPC + embedded protocols |
| Trust score + autonomy state | 1-2 weeks | Python + math/statistics |
| Learning pipeline | 4-6 weeks | Python + ML (scikit-learn, Whisper, LLM APIs) |
| Chat interface + LLM integration | 2-3 weeks | Python + NLP + LLM API |
| MQTT bridge | 1 week | Python + MQTT |
| A/B testing framework | 2-3 weeks | Python + statistics |
| Cloud code generation pipeline | 3-4 weeks | Python + LLM API + embedded knowledge |
| Testing (unit + integration + hardware-in-loop) | 4-6 weeks | All of the above |
| **TOTAL (single developer)** | **~30-40 weeks** | **Senior full-stack + embedded** |
| **TOTAL (3 developers, parallel work)** | **~12-16 weeks** | **As above** |

---

## Critical Path

```
Week 1-2:  Wire protocol COBS/FRAMING
Week 2-3:  Kill switch ISR + watchdog + heartbeat
Week 3-4:  VM safety invariants + execution engine
Week 4-5:  JSON-to-bytecode compiler
Week 5-6:  I/O abstraction + 5 drivers
Week 6-7:  Boot sequence + role assignment + selftest
Week 7-8:  Observation buffer + serial bridge
Week 8-9:  Node manager + reflex orchestrator
Week 9-10: Trust score + autonomy manager
Week 10-12: Learning pipeline (narration + pattern discovery)
Week 12-14: Chat interface + cloud code generation
Week 14-16: A/B testing + integration testing + hardware-in-loop
```

The fastest path to a working demo (LED blinker reflex controlled by chat) is weeks 1-8. The fastest path to a full marine autopilot demo (with learning) is weeks 1-16.
