# Claude Build Specification

## What Is This Directory?

This directory contains everything Claude Code (Opus 4.6+) needs to build the NEXUS system from specifications. If you are Claude Code and you've been pointed at this repo to start building — **start here, then read `build-specification.md`.**

## The Build Hierarchy

```
claude-build/
├── README.md                    ← YOU ARE HERE
└── build-specification.md       ← THE BUILD MANUAL (read this next)
```

## How to Use

1. **Read** `claude.md` in the repo root — full project context
2. **Read** `roadmap.md` in the repo root — master build plan with phases and sprints
3. **Read** `build-specification.md` — component-by-component build instructions
4. **Reference** `specs/` — production specifications are the SOURCE OF TRUTH
5. **Reference** `a2a-native-specs/` — A2A-native twin specs for agent-native components
6. **Consult** `knowledge-base/` — encyclopedic background when you need depth
7. **Consult** `onboarding/research/` — research context for advanced design decisions

## Non-Negotiable Rules

1. **Specs win over assumptions.** If code disagrees with specs, fix the code.
2. **Safety is never optional.** Every PR must preserve four-tier safety invariants.
3. **Zero heap on ESP32.** No malloc. No free. Ever. Static allocation only.
4. **Trust gates everything.** Code doesn't deploy without sufficient trust.
5. **Determinism is required.** Same inputs → same outputs in same cycles.
6. **All 32 opcodes must pass unit tests** before any feature work begins.
7. **The VM is the interface.** All control logic flows through bytecode. No direct hardware access from higher tiers.

## Build Order

The `build-specification.md` and `roadmap.md` both define the same build sequence:

| Phase | Sprint | What Gets Built | Success Criteria |
|-------|--------|-----------------|------------------|
| 0 | 0.1-0.4 | Dev env, VM core, wire protocol, reflex compiler | LED blinks from compiled bytecode |
| 1 | 1.1-1.4 | Safety layer, trust engine, validation framework | Fault injection → safe recovery |
| 2 | 2.1-2.5 | LLM pipeline, pattern discovery, A/B testing, marine domain | System learns from observation |
| 3 | 3.1-3.4 | AAB format, A2A opcodes, agent comms, 0.5× trust | Agents generate validated bytecode |
| 4 | 4.1-4.4 | Multi-node, inter-vessel, fleet coordination, cloud | 3 vessels coordinate tasks |
| 5 | 5.1-5.3 | Self-improvement, cert evidence, domain portability | System improves its own code |

## Key Files to Reference During Build

| When Building | Read This |
|---|---|
| The VM | `specs/firmware/reflex_bytecode_vm_spec.md` |
| Wire protocol | `specs/protocol/wire_protocol_spec.md` |
| Safety system | `specs/safety/safety_system_spec.md` |
| Trust algorithm | `specs/safety/trust_score_algorithm_spec.md` |
| Learning pipeline | `specs/jetson/learning_pipeline_spec.md` |
| A2A VM semantics | `a2a-native-specs/bytecode_vm_a2a_native.md` |
| A2A trust system | `a2a-native-specs/trust_system_a2a_native.md` |
| Memory layout | `specs/firmware/memory_map_and_partitions.md` |
| Safety policy rules | `specs/safety/safety_policy.json` |
| Agent comms model | `a2a-native-language/agent_communication_and_runtime_model.md` |

---

*This directory is the bridge between 400,000+ words of design and the first line of production code.*
