# VM Consolidation Research — `Edge-Native` vs `nexus-edge-runtime`

**Branch:** `vm-consolidation-research-2026-07-10` (on `SuperInstance/Edge-Native`)
**Date:** 2026-07-10
**Scope:** Research/comparison only. No VM code was merged, deprecated, or modified.
**Trigger:** `SuperInstance/the-technician` `06-EDUCATIONAL-PLATFORM.md` (PR#1) flagged that both repos contain a "bytecode VM for ESP32/Jetson" and asked whether they should converge. This doc gathers the evidence a human roadmap owner needs to decide.

---

## TL;DR (conclusion up front)

**Not actually duplicative — but the ownership boundary is muddy and worth fixing.**
The two repos do **not** contain two different VM designs solving the same job. They contain the **same NEXUS bytecode ISA** (identical 32 opcodes 0x00–0x1F, identical 8-byte instruction encoding) implemented at **two different deployment tiers**:

- **`Edge-Native`** owns the **authoritative spec** (`specs/firmware/reflex_bytecode_vm_spec.md`, 2487 lines) and the **C firmware VM** that actually executes on an ESP32-S3 (`firmware/nexus_vm/`, ~1023 lines C + 238-line header). It also ships a **Python encoder/decoder** for host tooling (`shared/bytecode/opcodes.py`) but deliberately ships **no Python executor**.
- **`nexus-edge-runtime`** ships a **host-side Python VM executor** (`src/core/vm.py`, 426 lines) that reimplements that same ISA, bundled with ~9 unrelated agent modules (trust, wire, safety, reflex compiler, fleet, digital twin…). It has **no spec, no firmware, no tests, no CI** of its own.

So they are **complementary tiers, not competitors**. The thing to fix is not "delete a VM" — it is **naming, documentation, and single-source-of-truth for the opcode table** (each repo currently hand-maintains an identical copy that will drift).

---

## 1. Method

Cloned `nexus-edge-runtime` to `/tmp/opencode/nexus-edge-runtime`; `Edge-Native` was the working tree. Read every VM-related source file in both, ran both test suites, and diffed the opcode tables and instruction encodings directly. Every numeric claim below was produced this session; none are estimated.

## 2. Target platform — what each actually claims to run on

| | `Edge-Native` | `nexus-edge-runtime` |
|---|---|---|
| Claims ESP32-S3? | **Yes, as deployable firmware.** `firmware/sdkconfig.defaults` + `CMakeLists.txt` are an ESP-IDF build; `README.md:24` "Each limb runs a bytecode VM on an ESP32-S3 that executes reflex programs at 1ms ticks." | **Yes, in prose only.** `README.md:8` and `src/core/vm.py:5` say "ESP32-S3 deployment + Jetson supervision." |
| Claims Jetson? | **Yes, as the cognitive tier that compiles/supervises bytecode** (`README.md:47`, Tier 2 "Cognitive Jetson Orin Nano"). | **Yes, in prose** (`src/core/vm.py:5`). |
| Actually ships ESP32 firmware? | **Yes** — `firmware/{main,drivers,safety,wire_protocol,nexus_vm}/` with `sdkconfig.defaults`, `partitions.csv`, `CMakeLists.txt`. | **No.** Pure Python package under `src/`. No firmware, no ESP-IDF, no MicroPython/CircuitPython target. The "ESP32-S3 deployment" claim is aspirational. |
| Actually ships Jetson code? | Skeleton only — `jetson/reflex_compiler/`, `jetson/nexus_sdk/` are empty `__init__.py`; `jetson/agent_runtime/` likewise. Host-side Python is in `shared/`. | Its entire `src/` *is* the "edge runtime" and is Python. |

**Same nominal targets (ESP32-S3 + Jetson), but only one repo (`Edge-Native`) can actually produce an ESP32-S3 artifact.** `nexus-edge-runtime`'s "ESP32-S3/Jetson" wording describes intent, not a deployable target.

## 3. Opcode / instruction model — are they solving the same problem the same way?

**Yes — this is the single most important finding.** Both are **32-opcode, stack-based, 8-byte-instruction** VMs with **byte-for-byte identical opcode assignments**:

```
0x00-0x07  NOP PUSH_I8 PUSH_I16 PUSH_F32 POP DUP SWAP ROT
0x08-0x10  ADD_F SUB_F MUL_F DIV_F NEG_F ABS_F MIN_F MAX_F CLAMP_F
0x11-0x15  EQ_F LT_F GT_F LTE_F GTE_F
0x16-0x19  AND_B OR_B XOR_B NOT_B
0x1A-0x1C  READ_PIN WRITE_PIN READ_TIMER_MS
0x1D-0x1F  JUMP JUMP_IF_FALSE JUMP_IF_TRUE
```

Verified identical across three independent declarations:
- `Edge-Native` C enum `firmware/nexus_vm/include/vm.h:53-99`
- `Edge-Native` Python `IntEnum` `shared/bytecode/opcodes.py:17-62`
- `nexus-edge-runtime` Python `IntEnum` `src/core/vm.py:20-34`

### Instruction encoding (structurally identical)

| Repo | Layout (little-endian) | Notes |
|---|---|---|
| `Edge-Native` | `<BBHI` = opcode:u8, flags:u8, operand1:u16, operand2:u32 | `shared/bytecode/opcodes.py:92`; C `instruction_t` `vm.h:35-42` with `_Static_assert(sizeof==8)` |
| `nexus-edge-runtime` | `<BBHi` = opcode:u8, arg8:u8, arg16:u16, imm32:i32 | `src/core/vm.py:298` |

Same 8-byte layout. The only divergence is operand2 typed **unsigned** vs **signed** — irrelevant for the shared opcodes (both pack `PUSH_F32` as IEEE-754 bits). **The two VMs execute each other's bytecode for the core 0x00–0x1F range.**

### Where the implementations genuinely diverge (extensions, not competition)

`Edge-Native`'s C VM is the **superset** and the **only one with production-control features**:

- **Syscall layer** (`firmware/nexus_vm/vm_syscalls.c`, 130 lines): `SYSCALL_HALT`, `SYSCALL_PID_COMPUTE` (full PID with anti-windup), `SYSCALL_RECORD_SNAPSHOT`, `SYSCALL_EMIT_EVENT`. `nexus-edge-runtime` has **none** of these — its programs terminate by falling off the end of memory (I confirmed this live: a program without a trailing `JUMP` raises `VMError: PC out of bounds: 65536` at `vm.py:105`).
- **A2A extension opcodes 0x20–0x5F** (`shared/bytecode/opcodes.h:47-63`, 29 opcodes: DECLARE_INTENT, TELL/ASK/DELEGATE, TRUST_CHECK, etc.) — defined and spec'd in `Edge-Native`; absent from `nexus-edge-runtime`.
- **WCET cycle budgets**: `Edge-Native` publishes per-opcode cycle costs (`vm_core.c:13-46`) and enforces `VM_CYCLE_BUDGET_EXCEEDED`; `nexus-edge-runtime` only has a flat `max_cycles` counter.
- **CALL/RET** via `FLAGS_IS_CALL` (`vm.h:48`, `vm_opcodes.c:334-352`); `nexus-edge-runtime` has no subroutine mechanism.
- **NaN/Inf guards on actuator writes** → `ERR_NAN_DETECTED` (`vm_opcodes.c:308-311`); `nexus-edge-runtime` writes whatever float is on the stack.
- **Pre-execution bytecode validator** with jump-bounds + pin-range checks (`vm_validate.c`, 88 lines); `nexus-edge-runtime`'s `Validator` (`vm.py:337-363`) only checks size alignment and opcode range.
- **Static, zero-heap memory model** sized for MCU (`vm.h:21-31`: 256-entry stack, 100KB max bytecode, ~3KB footprint per the spec).

`nexus-edge-runtime`'s `vm.py` is **simpler and host-oriented**: it adds a one-pass **Assembler** (`vm.py:234-305`) and **Disassembler** (`vm.py:307-334`) that `Edge-Native` keeps out of its Python tooling (Edge-Native's `shared/bytecode/opcodes.py` is encoding-only, 125 lines, with no executor loop). This is the one concrete capability `nexus-edge-runtime`'s VM adds that `Edge-Native`'s Python side lacks: **a runnable Python interpreter for the ISA**.

**Bottom line of §3:** Same ISA, same problem. `Edge-Native`'s C VM is the feature-complete production implementation; `nexus-edge-runtime`'s Python VM is a lighter host-side reimplementation that trades the safety/syscall/timing machinery for an assembler+disassembler+interpreter convenient for prototyping and teaching.

## 4. Language / toolchain

| | `Edge-Native` VM | `nexus-edge-runtime` VM |
|---|---|---|
| Implementation language | **C99/C11** (firmware) + **Python** (host encoder) | **Python** only |
| Build system | ESP-IDF (`firmware/`) + CMake host-test harness (`CMakeLists.txt`) | none (import `src/core/vm.py`) |
| Runs on bare ESP32-S3? | **Yes** (designed for it; statically allocated, zero heap) | **No** — requires a Python interpreter |
| Runs on a Jetson / host? | Yes (host-test build) | Yes (this is its native tier) |

This is decisive for the "are they duplicative?" question: **a C firmware VM and a Python host VM are not the same artifact even when they share an ISA.** They occupy non-overlapping deployment slots.

## 5. Maturity / test coverage / deployability (real numbers, measured this session)

### `Edge-Native` VM

- **Spec:** 1 production spec, `specs/firmware/reflex_bytecode_vm_spec.md`, **2487 lines** (status: FINAL).
- **C firmware tests:** `tests/unit/firmware/test_vm_opcodes.c` — **601 lines**, **38 test functions** (`grep -c '^void test_'`), **62 `TEST_ASSERT_*` calls**, **38 `RUN_TEST` invocations**. Built and passed via `cmake -DNEXUS_HOST_TEST=ON` + `ctest`: **3/3 test binaries PASSED, 0.01s** (incl. `test_vm_opcodes`, `test_cobs`, `test_crc16`).
- **Python host tests:** `tests/unit/jetson/test_opcodes.py` — **14 tests passed in 0.05s** (`pytest -q`).
- **HIL tests:** `tests/hil/test_vm_accuracy.py` — 3 tests, all `@pytest.mark.skip` pending ESP32-S3 hardware (oscilloscope timing). Skeleton only.
- **CI:** **4 workflows** in `.github/workflows/` (`esp32-build.yml`, `esp32-test.yml`, `jetson-build.yml`, `jetson-test.yml`) with path filtering and an 80% coverage gate on the Jetson side.
- **VM provenance:** added in commit `a34d416` on **2026-04-04** ("feat: Sprint 0.1 — monorepo foundation with VM, wire protocol, CI/CD"). It is the **origin** of this ISA.

### `nexus-edge-runtime` VM

- **Spec:** **None.** No spec doc; its only documentation is `src/core/vm.py:1-12` (module docstring) and one README bullet (`README.md:7-8`).
- **Tests:** **None.** `find ... -name '*test*'` over the repo returns zero test files. No `tests/` directory.
- **CI:** **None.** No `.github/workflows/`; the repo is 16 commits ending `6f446f8` (2026-04-13).
- **Verification this session:** I ran the VM by hand (`PUSH_F32 3.0 / PUSH_F32 4.0 / ADD_F / WRITE_PIN 5 / JUMP 4`) and it produced the correct output (`cycles=20, outputs=[('WRITE_PIN',(5, 7.0))]`). It executes, but it has no automated correctness net and I also hit one real bug (no HALT → runs off the end of the 64KB memory array and raises `VMError`).
- **VM provenance:** added in commit `599c780` on **2026-04-09** — **5 days after** `Edge-Native`, and its commit message ("Core: 32-opcode bytecode VM with assembler, disassembler, validator") describes the same feature set as `Edge-Native`'s Sprint 0.1 VM.

> Note on "round-3 production-hardening": the task context states both were independently verified working in a round-3 pass. I could not locate that pass inside either repo (no matching string in `worklog.md`/`README.md`/`roadmap.md`), so I am not citing it. The directly-verifiable evidence above is what this doc relies on.

### Deployability summary

`Edge-Native` is the deployable, spec'd, CI-backed, firmware-capable VM. `nexus-edge-runtime`'s VM is runnable but untested, unspec'd, un-CI'd, and ships no firmware artifact — it is prototyping/teaching-grade today.

## 6. Actual overlap in scope — what does each repo *say* it is?

- **`Edge-Native` `README.md:20`:** *"the **definitive specification and knowledge repository** for the NEXUS distributed intelligence platform … If code disagrees with these specs, the specs win."* The C VM is the reference implementation of that spec; the ESP32-S3 is the named execution substrate (`README.md:24`).
- **`nexus-edge-runtime` `README.md:1-3`:** *"Edge runtime for autonomous agents in the Cocapn fleet — generalized beyond maritime robotics for IoT, industrial, aerial, and marine domains."* Its `README.md:47-54` positions it as a **generalization of yet another repo** (`SuperInstance/nexus-runtime`), not as a peer of `Edge-Native`. Its `vm.py` is listed as **1 of ~10 modules** alongside `trust/`, `wire/`, `safety/`, `reflex/compiler.py`, `fleet/`, `perception/`, `digital_twin/`.

So on its own terms `nexus-edge-runtime` is a **fleet agent runtime** that happens to include a Python bytecode VM; it does not present itself as the NEXUS VM's home. `Edge-Native` presents itself as the NEXUS VM's home. **Neither repo's README acknowledges the other's VM exists** — which is exactly why the question landed on the roadmap.

## 7. Verdict: not duplicative in design; duplicative in opcode-table ownership

1. **The designs are not competitors.** One C firmware VM (production, ESP32-S3) and one Python host VM (prototyping/teaching/simulation) sharing an ISA is the normal, healthy pattern for an embedded bytecode platform. The technician paper's choice of the Python VM for *teaching* and the C VM for *deployment* matches the artifacts' actual strengths.
2. **The real risk is divergence, not redundancy.** There are now **three hand-maintained copies** of the opcode table (`vm.h`, `opcodes.py` in Edge-Native; `vm.py` in nexus-edge-runtime) that the specs require to stay identical (`opcodes.py:7` literally says *"Must be kept in sync with opcodes.h"*). With no shared dependency and no test asserting cross-repo parity, the Python and C implementations **will drift**. (They have not yet — I confirmed all 32 values match — but the guard does not exist.)
3. **There is no spec'd or tested reason to delete either VM.** Deprecating the C VM would remove the only deployable firmware executor and all safety/syscall/WCET machinery. Deprecating the Python VM would remove the only runnable host-side reference interpreter and the assembler/disassembler the teaching track relies on.

### Recommendation (for the human roadmap owner — not a decision I'm making for you)

**Keep both VMs; fix ownership and naming.** Specifically:

1. **Designate `Edge-Native` as the canonical owner of the NEXUS VM ISA** (it already is in practice — it has the spec, the firmware, the CI, and is 5 days older). Make this explicit in both READMEs.
2. **Re-label `nexus-edge-runtime`'s `vm.py` as the *host-side reference/simulation implementation* of the Edge-Native NEXUS VM** — not "the bytecode VM" in its own right. Update `nexus-edge-runtime/README.md:7-8` and `src/core/vm.py:1-12` to say so and to link the spec.
3. **Single source of truth for opcodes.** Either (a) generate `vm.h` / `opcodes.h` / the Python `IntEnum` from one table in `Edge-Native`, or (b) add a cross-repo conformance test (a golden bytecode blob + expected stack result) that both `Edge-Native`'s `esp32-test.yml` and a new `nexus-edge-runtime` workflow run. Either closes the drift gap that makes "two VMs" feel risky.
4. **Give `nexus-edge-runtime`'s VM a test + a HALT.** It currently has zero tests and no clean termination path (it errors on PC-out-of-bounds). If it stays as the teaching VM (the technician paper's choice), it needs at least a minimal pytest suite and an explicit halt/terminate convention that matches the C VM's `SYSCALL_HALT`.
5. **If, later, deployment data shows nobody runs the Python VM except in teaching**, the consolidation move is to **absorb `nexus-edge-runtime`'s assembler/disassembler into `Edge-Native`'s `shared/bytecode/`** (where a Python executor is the one missing piece) and let `nexus-edge-runtime` *consume* the VM rather than *contain* it. That is an organizational cleanup, not a design deprecation — and it should wait until usage data exists.

### What would change this verdict

- Evidence that the Python VM is **actually deployed on Jetsons in the field** (not just prototyped with) would strengthen "keep it as a peer runtime."
- Evidence that **nobody uses `nexus-edge-runtime`'s VM outside the teaching curriculum** would tip toward option (5) above — fold its tooling into `Edge-Native` now.
- A discovery that the two ISA copies have **already silently diverged** in some branch would escalate urgency on (3) from "should" to "now."

I did not find any of these in-repo, so they fall to whoever has deployment/usage telemetry.

## 8. Evidence index (file:line)

**`Edge-Native` (this repo):**
- `firmware/nexus_vm/include/vm.h:21-31` — static MCU memory budget; `:35-42` 8-byte `instruction_t`; `:53-99` opcode enum; `:101-107` syscall IDs.
- `firmware/nexus_vm/vm_core.c:13-46` — per-opcode cycle costs; `:95-151` tick loop with cycle-budget + PC-bounds enforcement.
- `firmware/nexus_vm/vm_opcodes.c:143-151` DIV_F div-by-zero→0.0; `:153-167` NEG/ABS via bit ops; `:301-320` NaN-guarded actuator writes; `:330-360` CALL/RET.
- `firmware/nexus_vm/vm_syscalls.c:41-86` PID; `:88-109` snapshot; `:111-125` event ring.
- `firmware/nexus_vm/vm_validate.c:15-87` pre-execution validator.
- `shared/bytecode/opcodes.py:17-62` Python opcode IntEnum; `:7` "Must be kept in sync"; `:82-98` `Instruction` codec.
- `shared/bytecode/opcodes.h:47-63` A2A extension opcodes 0x20–0x5F.
- `specs/firmware/reflex_bytecode_vm_spec.md:1-82` (2487-line spec; design philosophy + scope).
- `tests/unit/firmware/test_vm_opcodes.c` — 601 lines, 38 tests, 62 assertions.
- `.github/workflows/{esp32-test,jetson-test}.yml` — CI.
- `README.md:20,24,47` — repo self-description.
- Commit `a34d416` (2026-04-04) — VM origin.

**`nexus-edge-runtime`:**
- `src/core/vm.py:1-12` module docstring (claims ESP32-S3/Jetson); `:20-34` opcode enum; `:103-111` instruction decode; `:113-224` step loop; `:234-305` Assembler; `:307-334` Disassembler; `:337-363` Validator.
- `README.md:1-3,7-8,47-54` — repo self-description + positioning vs `nexus-runtime`.
- No `tests/`, no `.github/workflows/`.
- Commit `599c780` (2026-04-09) — VM added 5 days after `Edge-Native`.
