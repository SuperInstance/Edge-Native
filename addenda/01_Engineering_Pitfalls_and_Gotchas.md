# Engineering Pitfalls & Gotchas — Read This Before Writing Any Code

> **Audience:** Senior embedded engineers who know C, Python, and serial protocols cold — but haven't memorized NEXUS's 19,200 lines of specs.  
> **Scope:** Every trap, footgun, and subtle interaction we found during deep analysis of the wire protocol spec, VM spec, safety system spec, memory map, and Jetson cognitive layer.  
> **Cross-references:** All section numbers refer to files in `nexus_specs/` unless noted. Line numbers are approximate.

---

## How to Use This Document

Each pitfall is tagged with a **severity** rating and the **spec source** it derives from. The severity levels are:

| Rating | Meaning |
|--------|---------|
| **CRITICAL** | Will cause data corruption, communication failure, or physical danger if wrong. |
| **HIGH** | Will cause intermittent failures that are extremely painful to debug. |
| **MEDIUM** | Will waste days of engineering time during integration. |
| **LOW** | Cosmetic or efficiency issue; correct eventually but annoying. |

Read all CRITICAL and HIGH items before writing *any* code. Keep this document open during code review — if a PR touches a subsystem covered here, verify the pitfall is addressed.

---

## 1. COBS Encoding Traps

### 1.1 The 256-Consecutive-Zeros Edge Case [CRITICAL]
*Source: `protocol/wire_protocol_spec.md`, Frame Encoding section*

COBS (Consistent Overhead Byte Stuffing) has a well-known but frequently forgotten maximum run length: **254 non-zero bytes**. A count byte of `0xFF` means "254 non-zero bytes follow." The implicit sentinel `0x00` that terminates every COBS frame is *consumed* by the decoding algorithm — it is not part of the payload.

The trap: if your COBS encoder produces a run of exactly 254 non-zero bytes and the next byte happens to be `0x00`, the count byte will be `0xFF` followed by the 254 bytes, then a new count byte of `0x01` (one zero byte). Many implementations forget to strip the trailing sentinel `0x00` after decoding, leaving a spurious zero byte appended to the payload. This shifts every subsequent field by one byte and corrupts the CRC-16 check value that follows.

**Debugging symptom:** CRC passes on the sender side but always fails on the receiver. You'll spend hours chasing a "one-byte-off" corruption that only manifests when payloads hit specific length boundaries.

**Correct implementation:** After COBS decode, the output buffer length is `encoded_length - 2` (subtract one for the overhead byte, one for the sentinel). The sentinel byte at position `encoded_length - 1` must be verified to be `0x00` and discarded.

### 1.2 CRC-16 Scope [CRITICAL]
*Source: `protocol/wire_protocol_spec.md`, Frame Integrity section*

The CRC-16/CCITT-FALSE covers the **decoded header + payload bytes only** — it does *not* include the CRC bytes themselves. Polynomial: `0x1021`. Init value: `0xFFFF`. Final XOR: `0x0000`. Input/output reflection: none.

This matters because some CRC libraries include the CRC bytes in their verification step (compare the computed CRC against the two bytes in the frame). The NEXUS spec says to compute CRC over header+payload, then compare the computed 16-bit value against the two received CRC bytes. If your library auto-appends and auto-verifies inclusive of the CRC field, you'll get false positives.

**The #1 cause of "works in unit test, fails on wire."** Unit tests often construct frames programmatically and compute CRC correctly. But when you hook up to real hardware, a one-byte framing error causes the CRC scope to shift and every frame fails.

### 1.3 Buffer Limit Is 1051, Not 1024 [HIGH]
*Source: `protocol/wire_protocol_spec.md`, Frame Limits section*

The spec states the maximum COBS-encoded frame size is **1051 bytes**, not 1024. This is because COBS encoding adds up to ⌈N/254⌉ overhead bytes. A 1024-byte decoded payload can expand to 1028 bytes COBS-encoded (4 overhead bytes for 4 blocks of 254). Adding the 5-byte message header (version + type + flags + sequence + length), 2-byte CRC, and 1-byte sentinel gives 1024 + 5 + 2 + 4 + 1 = **1036 bytes**. The spec rounds up to 1051 to account for alignment and future expansion.

If you allocate a 1024-byte receive buffer, you will silently overflow on large messages (e.g., `OBSERVATION_DATA` with 72 float fields). The buffer overflow corrupts adjacent memory and the symptom will be random crashes in unrelated subsystems.

### 1.4 Endianness Mismatch [HIGH]
*Source: `protocol/wire_protocol_spec.md` (header) + `firmware/reflex_bytecode_vm_spec.md` (instructions)*

Message headers are **big-endian** (network byte order): the `msg_type` field (bytes 1-2), `flags` (byte 3), `sequence` (bytes 4-5), and `payload_length` (bytes 6-7) all use `htons()`/`ntohs()` convention on the wire.

However, VM instruction operands are **native byte order** (little-endian on ESP32-S3, which is Xtensa LX7). The 4-byte `operand2` field in bytecode instructions stores floating-point values in IEEE 754 little-endian format.

If you transmit raw bytecode over the wire protocol without byte-swapping the float operands, a `PUSH_F 3.14` becomes `PUSH_F 0x1F85EB51` on the wire (big-endian) which the ESP32 interprets as `0x51EB851F` (a completely different float). **This produces silent, spectacularly wrong float values** — not NaN, but plausible-looking garbage that passes all range checks.

**Rule:** Never put raw bytecode in wire protocol payloads. Always serialize/deserialize with explicit endianness conversion. The `REFLEX_DEPLOY` message payload should use a serialization format that specifies byte order (e.g., Protocol Buffers, or a custom format with explicit endianness tags).

---

## 2. Bytecode VM Implementation Pitfalls

### 2.1 CLAMP_F Encoding Is a Minefield [CRITICAL]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Opcode Reference — CLAMP_F*

The `CLAMP_F` opcode needs to store two IEEE 754 float bounds (lower, upper) in a single 4-byte `operand2` field, which physically cannot hold two floats. The spec's original encoding used a "NOP-follows-CLAMP" trick where the next instruction in the bytecode stream was a `NOP` whose `operand2` held the second bound. This was fragile and deprecated.

The **preferred implementation** uses decomposition into `MAX_F` + `MIN_F`: `CLAMP_F` is compiled as `MAX_F lower_bound` then `MIN_F upper_bound`. The compiler must emit two instructions for every clamp operation. If you implement CLAMP_F as a single instruction and only read one bound, the clamping will silently use whatever happens to be in the second operand position — usually zero or the previous instruction's residual.

**Validation rule:** The bytecode validator must reject any standalone `CLAMP_F` opcode. Every `CLAMP_F` must be part of a compiled `MAX_F` + `MIN_F` pair, or the validator must expand it during a pre-pass.

### 2.2 Variable Space Aliasing with Pin Space [CRITICAL]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Memory Model section*

`READ_PIN` and `WRITE_PIN` use `operand1` as the address. Values `0x00–0x3F` (0–63) map to physical I/O pins. Values `0x40–0x9F` (64–159) map to VM variable space (index = `operand1 - 64`). Values `0xA0–0xFF` (160–255) are reserved.

The validator must enforce strict range checks:
- Pin access: `operand1` ∈ `[0, 63]`
- Variable access: `operand1` ∈ `[64, 159]` (256 max variables, 96 bytes at 4 bytes each)

**If you don't validate this, a reflex that writes to "variable 10" (operand1 = 74) but accidentally uses operand1 = 10 will write to physical pin 10.** On a motor driver node, this could be a PWM output pin — you'd be writing arbitrary float values to a motor PWM register. This is a safety-critical bug.

The `IO_DRIVER_REGISTRY` in `firmware/io_driver_registry.json` defines which pins are inputs vs outputs per node type. Cross-reference this during validation.

### 2.3 PID_COMPUTE Stack Order [HIGH]
*Source: `firmware/reflex_bytecode_vm_spec.md`, PID_COMPUTE instruction*

`PID_COMPUTE` pops **two** values and pushes **one**. The stack layout is:

```
Before: [..., setpoint, input]    ← input is TOS (top of stack)
After:  [..., output]
```

The setpoint is TOS-1, the input (current measurement) is TOS. If a compiler emits `PUSH_F setpoint` then `PUSH_F sensor_reading` then `PID_COMPUTE`, the PID controller gets the correct arguments. But if the order is reversed (setpoint pushed last), the PID will try to drive the measurement toward the setpoint *inverted*, and the controller will diverge.

**This is particularly insidious because a PID with swapped arguments doesn't crash — it just oscillates wildly or drives to rail.** You'll spend hours tuning gains when the real problem is argument order.

### 2.4 DIV_F Returns 0.0f, Not NaN [MEDIUM]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Arithmetic Opcodes*

Division by zero in `DIV_F` returns `0.0f`, **not** IEEE 754 `NaN` or `Inf`. This is a deliberate design choice for embedded determinism — NaN propagation through a control loop would make behavior unpredictable.

However, if your compiler or test suite checks for NaN to detect division errors, those checks will never trigger. Any safety logic that depends on NaN detection (e.g., "if result is NaN, use last good value") will silently use `0.0f` instead, which may be a worse failure mode.

**Workaround:** If you need NaN semantics, the compiler should emit an explicit `DUP` + `DUP` + `EQ_F` + `JZ` sequence before `DIV_F` to check for zero divisor and handle it explicitly.

### 2.5 No Type Tags on the Stack [HIGH]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Stack Model*

All VM stack slots are raw `uint32_t`. The VM performs **zero type checking** at runtime. If the compiler pushes an integer (via `PUSH_I`) and the next instruction is `ADD_F`, the VM will reinterpret the integer bit pattern as a float. For example, `PUSH_I 1` pushes `0x00000001`, which is `1.4e-45` as a float32. Any float arithmetic on this value produces garbage.

**The compiler is 100% responsible for type correctness.** There is no runtime safeguard. The bytecode validator should maintain a simulated type stack and reject any instruction that would operate on a mismatched type. This is the single most important validation pass to implement.

### 2.6 HALT Is Not a Separate Opcode [MEDIUM]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Instruction Encoding*

`HALT` is implemented as a `NOP` instruction with the `SYSCALL` flag (bit 7 of the flags byte) set and `operand1 = 0x01`. It is **not** a distinct opcode in the instruction set. The instruction byte for `NOP` is `0x00`.

If you search for `0xFF` (a common choice for HALT) in your disassembler, you'll never find halt instructions. The disassembler must check: if opcode == `0x00` AND `(flags & 0x80)` AND `operand1 == 0x01`, then this is `HALT`.

### 2.7 Cycle Budget Across CALL/RET [HIGH]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Execution Limits*

The VM enforces a maximum of **10,000 cycles per tick**. Each opcode has a documented cycle cost (typically 1–4 cycles). Simple reflexes (20 instructions × 3 cycles = 60 cycles) are well within budget.

**The trap:** the cycle counter must accumulate across `CALL`/`RET` boundaries. If a reflex implements a state machine with a loop containing a `CALL` to a subroutine, the cycle counter must include the subroutine's cycles. If you reset the counter on each `CALL`, a reflex with 50 nested calls can execute 50 × 10,000 = 500,000 cycles before being killed.

**Implementation:** The cycle counter is a `uint32_t` that increments by the current instruction's cycle count on every dispatch. Check `cycles_remaining >= current_cost` before each instruction. If it underflows, abort the reflex with `VM_ERROR_CYCLE_BUDGET` (error code `0x32` per the spec).

### 2.8 PID Derivative Kick at 10Hz [MEDIUM]
*Source: `firmware/reflex_bytecode_vm_spec.md`, PID_COMPUTE + safety considerations*

The PID implementation uses output clamping but the spec does **not** include derivative kick filtering. At the 10Hz tick rate, a step change in setpoint causes a massive derivative spike on the first tick: `d(setpoint - measurement)/dt` where setpoint jumps by the full step size in one 100ms period.

For example, a setpoint step from 0 to 100 produces a derivative term of `(100 - 0) / 0.1 = 1000/s`. If your derivative gain `Kd` is 0.1, that's a `100.0` contribution to the output, which will saturate the actuator immediately and may trigger overcurrent protection.

**Recommended mitigation:** The compiler should either:
1. Use "derivative on measurement" form: `d(-measurement)/dt` instead of `d(error)/dt`
2. Or insert a low-pass filter on the derivative term (e.g., first-order IIR with α = 0.1)

---

## 3. Serial Protocol Traps

### 3.1 Baud Rate Negotiation Race Condition [CRITICAL]
*Source: `protocol/wire_protocol_spec.md`, Link Establishment section*

Baud rate negotiation involves both sides switching simultaneously. The Jetson sends `BAUD_REQUEST`, the node ACKs at the old rate, then both sides switch. **The spec says "send PING to verify" but does not specify a settling delay.**

In practice, the UART hardware needs time to stabilize at the new baud rate — typically 1-2 character times (at 460800 baud, one character time is ~22µs, so two characters = ~44µs). But firmware-side UART reinitialization (calling `uart_driver_install()` with new parameters) can take 200-500µs on ESP32-S3 due to RTOS scheduling.

**If the Jetson switches 10ms before the node**, the node's ACK at the old baud rate is interpreted as garbage at the new rate, and the PING that follows is also lost. Both sides sit in a silent deadlock.

**Fix:** Add a **50ms settling delay** after baud rate switch before sending the PING. Both sides must independently wait before transmitting at the new rate. Implement this as a `vTaskDelay(pdMS_TO_TICKS(50))` in the UART task on the ESP32, and `time.sleep(0.05)` in the Jetson serial bridge.

### 3.2 Heartbeat: Two Conflicting Specs [CRITICAL]
*Source: `protocol/wire_protocol_spec.md` vs `safety/safety_system_spec.md`*

The wire protocol spec says: node heartbeat interval = **1000ms**, 3-miss threshold = 3000ms timeout. But the safety system spec says: node heartbeat interval = **100ms**, 5-miss = 500ms degraded mode, 10-miss = 1000ms safe-state.

**The safety spec overrides.** You must implement the 100ms interval. If you implement the wire protocol's 1000ms interval, the safety monitor will declare the node dead after 500ms (5 × 100ms expected beats not received), triggering a spurious safe-state transition.

**The root cause of this conflict** is likely that the wire protocol spec was written for development/debug mode (lower overhead) while the safety spec reflects production requirements. Your firmware should have a compile-time flag: `#define SAFETY_MODE` that selects the 100ms interval and 5-miss/10-miss thresholds.

### 3.3 Sequence Numbers Are Per-Direction [MEDIUM]
*Source: `protocol/wire_protocol_spec.md`, Message Header section*

Each side maintains its own independent TX sequence counter starting at 0. The Jetson has `jetson_tx_seq` and `node_tx_seq`. When the node ACKs message #7 from the Jetson, it sets the ACK's sequence field to **7** (echoing the original message's sequence number), not the node's own counter.

**Common mistake:** Using a shared counter or incrementing on receive. This causes the receiver to see duplicate sequence numbers and discard valid messages.

### 3.4 IS_ACK and ACK_REQUIRED Flag Conflict [HIGH]
*Source: `protocol/wire_protocol_spec.md`, Flags Byte section*

The flags byte has: bit 0 = `ACK_REQUIRED`, bit 1 = `IS_ACK`. The spec states these **must not both be set** in the same message. A message that is an ACK should never request an ACK back — that creates an infinite ACK loop.

**Your receive logic must validate this.** If a message arrives with both bits set, discard it and increment an error counter. Do not ACK it (that's the loop) and do not process it (it's malformed).

### 3.5 Flow Control Polarity [CRITICAL]
*Source: `protocol/wire_protocol_spec.md`, Hardware Handshake section*

The NEXUS spec uses CTS/RTS in the **DCE-to-DTE** convention:
- **CTS (Clear To Send):** Jetson → Node. The Jetson controls when the node is allowed to transmit.
- **RTS (Request To Send):** Node → Jetson. The node signals it has data to send.

This is the *opposite* of the common "RTS/CTS" naming convention where RTS means "I want to send" from the DTE perspective. If you connect CTS to the ESP32's RTS pin and RTS to the ESP32's CTS pin, flow control will be inverted: the Jetson will be told the node is ready when it's not, and vice versa.

**Pin mapping:** ESP32-S3 UART1 `CTS` pin (configurable, typically GPIO15) connects to Jetson `RTS`. ESP32-S3 `RTS` pin (GPIO14) connects to Jetson `CTS`. Label your schematics carefully.

---

## 4. Safety System Pitfalls

### 4.1 E-Stop ISR Must Be in IRAM [CRITICAL]
*Source: `safety/safety_system_spec.md`, Kill Switch section*

The E-Stop GPIO interrupt service routine **must** reside in IRAM (Internal RAM), not flash. During flash operations — OTA updates, NVS writes, SPIFFS/LittleFS operations — the ESP32's SPI flash is inaccessible for ~100ms. If the ISR is in flash, the CPU will trigger a cache miss fault when the kill switch is pressed during OTA, and the kill switch will not respond.

**This is a real failure mode that has caused injuries in deployed systems.** An operator presses the emergency stop during an OTA update, nothing happens, and the robot continues moving.

**Fix:** Attribute the ISR with `IRAM_ATTR`:
```c
void IRAM_ATTR gpio_isr_handler(void* arg) {
    // Only IRAM-safe operations
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xSemaphoreGiveFromISR(kill_switch_sem, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

### 4.2 Kill Switch Sense Wire: External Pull-Up Only [HIGH]
*Source: `safety/safety_system_spec.md`, Kill Switch Hardware section*

The kill switch sense wire uses an **external 10KΩ pull-up** to 3.3V. A broken wire reads LOW (same as "kill switch pressed") — correct fail-safe behavior.

**Do not use the ESP32's internal pull-up.** The internal pull-up is typically 30-50KΩ, which is too weak for long cable runs (3-10 meters in marine/industrial environments). EMI from motor PWM cables running parallel to the sense wire will induce enough voltage to create false triggers. At 50KΩ, only ~66µA of induced current (3.3V / 50KΩ) is needed to create a 0.5V noise margin violation. Motor PWM edges at 20KHz with 10A current can easily induce this.

**Hardware rule:** External 10KΩ pull-up at the connector, not at the MCU. This keeps the pull-up current loop short and minimizes the antenna formed by the sense wire.

### 4.3 Hardware Watchdog Kick Pattern Validation [HIGH]
*Source: `safety/safety_system_spec.md`, Watchdog section*

The MAX6818 hardware watchdog requires an alternating `0x55` / `0xAA` kick pattern on the WDI pin. A GPIO stuck HIGH or LOW will fail to toggle WDI and the MAX6818 will reset the system after ~1.6 seconds.

**The trap:** if the firmware crashes in a way that causes the GPIO to oscillate (e.g., an RTOS task stuck in a tight loop that happens to call `gpio_set_level()` with alternating values due to register corruption), the WDI sees valid toggle pattern and the watchdog stays alive.

**Software safeguard:** Before each kick, verify that the GPIO state actually changed from the previous kick. Store `last_kick_state` in a global variable and assert `gpio_state != last_kick_state` before writing. If it hasn't changed, force a software reset immediately — the firmware is in a bad state.

### 4.4 Boot Counter Lockout During Development [MEDIUM]
*Source: `safety/safety_system_spec.md`, Boot Counter section*

If the system boots more than 5 times in 10 minutes, it enters **FAULT mode** (permanent, requires manual reset or JTAG recovery). This is designed to prevent rapid reset loops from masking dangerous hardware faults.

During development, you *will* trigger this. A firmware crash loop reboots the ESP32 every 2-3 seconds → 5 boots in 15 seconds → FAULT mode. You'll think the board is bricked.

**Fix:** Add a compile-time development bypass:
```c
#ifdef DEVELOPMENT_MODE
  #define BOOT_COUNTER_MAX 999  // Effectively disabled
  #define BOOT_COUNTER_WINDOW_MS 60000
#else
  #define BOOT_COUNTER_MAX 5
  #define BOOT_COUNTER_WINDOW_MS 600000  // 10 minutes
#endif
```

Store the boot counter in RTC slow memory (persists across resets but not power cycles) using `esp_rtc_store()`.

### 4.5 ISR Must Only Call IRAM-Safe Functions [CRITICAL]
*Source: `safety/safety_system_spec.md`, ISR Constraints*

The kill switch ISR and overcurrent ISR must only call functions resident in IRAM. The following common functions are **NOT** IRAM-safe:
- `printf()`, `ESP_LOGx()` — touch flash for format strings
- `esp_timer_get_time()` — may touch flash on first call
- `xQueueSend()` — not ISR-safe; use `xQueueSendFromISR()`
- `nvs_get_*()` — touches flash
- `cJSON_*()` — touches flash for string literals

**Allowed in ISR:** `gpio_set_level()`, `ledc_set_duty()`, `xSemaphoreGiveFromISR()`, `xQueueSendFromISR()`, `portYIELD_FROM_ISR()`, direct register writes (`GPIO.out_w1ts`).

If you need to log from an ISR (development only), write to a ring buffer in DRAM and have a normal-priority task drain it.

---

## 5. Memory and Flash Pitfalls

### 5.1 Factory Partition Must Be Separate from OTA Slots [HIGH]
*Source: `firmware/memory_map_and_partitions.md`, Partition Table section*

The ESP32 partition table has three app slots: `factory`, `ota_0`, `ota_1`. The factory partition is **never** modified by OTA. If both OTA slots fail post-write validation (CRC or signature mismatch), the bootloader falls back to factory.

**Common mistake during development:** Accidentally setting the factory partition as the OTA_0 slot in the partition table CSV. This overwrites your failsafe firmware during the first OTA. If the new firmware is broken, you have no recovery path short of USB/JTAG flashing.

**Partition table CSV check:**
```csv
# Name,     Type, SubType,  Offset,   Size
factory,    app,  factory,   0x10000,  1M
ota_0,      app,  ota_0,     0x110000, 1M
ota_1,      app,  ota_1,     0x210000, 1M
```

The `otadata` partition (0x2000 bytes at a fixed offset) stores which slot is active. The bootloader reads this first, validates the selected slot, and falls back to factory on failure.

### 5.2 LittleFS on PSRAM Will Corrupt on Power Loss [HIGH]
*Source: `firmware/memory_map_and_partitions.md`, Storage Architecture section*

LittleFS is designed for SPI NOR flash, which has inherent wear leveling and power-loss resilience. PSRAM (Octal SPI on ESP32-S3) has **no power-loss protection** — a write interrupted by power loss leaves the data in an undefined state.

**The spec uses PSRAM exclusively for the observation buffer** — a ring buffer in raw memory, not a filesystem. Do not mount LittleFS or FAT on PSRAM. If you need persistent storage on PSRAM, implement a battery-backed write-through cache or accept that data is volatile.

### 5.3 VM Memory Budget: PID State Is Expensive [MEDIUM]
*Source: `firmware/reflex_bytecode_vm_spec.md`, Memory Model section*

The VM's total RAM footprint is approximately **3KB**: 256 slots × 4 bytes (stack) = 1024 bytes, plus variable space, plus PID controller state. Each PID controller requires **32 bytes** (8 × float32: Kp, Ki, Kd, setpoint, input, output, integral, prev_error).

With 8 PID slots available per the spec, that's 256 bytes just for PID state — 8.3% of the total VM budget. If your reflexes use 6 PID controllers simultaneously, you have 192 bytes consumed by PID state alone, leaving limited room for variables and stack depth.

**Planning rule:** Allocate PID controllers first, then variables, then stack. The stack can grow dynamically (up to 256 slots) but PID and variable space is statically allocated at reflex load time.

### 5.4 Observation Buffer Fill Rate [LOW]
*Source: `firmware/memory_map_and_partitions.md`, Observation Buffer section*

At 100Hz observation rate with 72 fields at float32 (4 bytes each): `100 × 72 × 4 = 28,800 bytes/second`. The PSRAM ring buffer is **8MB**, which fills in `8,388,608 / 28,800 ≈ 291 seconds (~4.9 minutes)`.

If your observation session exceeds 5 minutes, old data is overwritten. Plan your data offload intervals accordingly. The `OBSERVATION_DATA` message can only transmit ~1024 bytes per frame, so offloading the full buffer requires `8MB / 1024 ≈ 8,192 frames` at 100Hz = ~82 seconds of sustained transmission — which will overflow the serial link if not flow-controlled.

---

## 6. Jetson-Side Pitfalls

### 6.1 gRPC and MQTT Use Different Serialization [MEDIUM]
*Source: `jetson/cluster_api.proto` + `jetson/mqtt_topics.json`*

The gRPC interface uses Protocol Buffers (`cluster_api.proto`) while the MQTT topics use JSON payloads. You cannot share message definitions between them. A `NodeStatus` message in gRPC has field numbers (`node_id = 1; role = 2; ...`), while the MQTT equivalent on topic `nexus/nodes/{node_id}/status` uses JSON keys (`{"node_id": "...", "role": "..."}`).

**Don't try to write a single serialization layer.** Maintain separate protobuf and JSON schema definitions, and write explicit conversion functions between them. If you try to use protobuf's JSON mapping (`protojson`), you'll get camelCase field names that don't match the MQTT spec's snake_case convention.

### 6.2 LLM Code Generation Latency Perception [MEDIUM]
*Source: `jetson/learning_pipeline_spec.md`, Code Generation section*

The local Qwen2.5-Coder-7B model generates at approximately **12 tokens/second**. A 500-token reflex JSON takes **~42 seconds** to generate. There is no progress indicator in the base pipeline.

Users will think the system is frozen. The web UI must implement **streaming token output** — emit partial JSON as tokens arrive and render the in-progress reflex definition in the UI. Without this, users will reload the page, cancel the request, or power-cycle the Jetson.

### 6.3 LLM Validation Cost [LOW]
*Source: `jetson/learning_pipeline_spec.md`, Validation section*

The separate LLM validation call (second pass to verify generated code) costs approximately **$0.01–0.03 per call** when using a cloud API (GPT-4 class). At scale — 100 reflexes per day across a fleet — that's **$1–3/day** or **$30–90/month**. This is significant for a robotics platform that's supposed to reduce operational costs.

**Optimization:** Cache validation results. If two reflexes have identical bytecode (same SHA-256 hash), skip re-validation. The spec's trust score system already rewards consistency — leverage this to reduce redundant validation calls.

### 6.4 Trust Score Convergence Time [MEDIUM]
*Source: `safety/trust_score_algorithm_spec.md`, Parameters section*

Trust score parameters: `alpha_gain = 0.002`, `alpha_loss = 0.05`. Reaching Level 3 autonomy (trust ≥ 0.7) from Level 2 (trust = 0.4) requires approximately **150 flawless ticks** at minimum: `(0.7 - 0.4) / 0.002 = 150` gain events without any loss events. But since trust is evaluated per-reflex-per-tick, and there are typically 10-20 reflexes per node, reaching Level 3 system-wide requires ~150 × 10 = **1,500 consecutive flawless ticks** across all reflexes.

At 10Hz tick rate with 8-hour daily operation, that's `1500 / (10 × 8 × 3600) ≈ 0.005 days` per reflex — fast. But any single failure resets trust by `0.05`, requiring 25 flawless ticks to recover. If one reflex fails once per hour, it never reaches Level 3: hourly loss of 0.05 vs hourly gain of `0.002 × 10 × 3600 = 72` (if all other ticks are perfect), which is fine. The asymmetric ratio (25:1 recovery) is intentional — trust is easy to lose, hard to regain.

**Demo mode:** Temporarily set `alpha_gain = 0.02` (10× faster) for demonstrations. Never ship this to production.

### 6.5 MQTT QoS 2 Overhead at High Override Rates [HIGH]
*Source: `jetson/mqtt_topics.json`, Override Topics section*

Override topics use MQTT QoS 2 (exactly-once delivery), which requires a 4-packet handshake: `PUBLISH → PUBREC → PUBREL → PUBCOMP`. At 100Hz override rate, this generates **400 MQTT packets per second per node**.

With 6 nodes on a single Jetson, that's **2,400 packets/second** of pure MQTT overhead, not counting the actual payload data. Most MQTT brokers (Mosquitto, EMQX) can handle this, but the Jetson's Python MQTT client (paho-mqtt) will struggle — it's single-threaded and processes packets sequentially.

**Mitigation:** Use the `paho.mqtt.client` `max_inflight_messages` setting (default 20) and increase it to 200. Consider using the C-based `Mosquitto` client library instead of the Python wrapper for lower overhead. Alternatively, batch override commands at 10Hz instead of 100Hz — the PID loop runs at 10Hz anyway, so 100Hz overrides provide no benefit.

---

## 7. Integration Traps

### 7.1 Boot Sequence Timing Gap [HIGH]
*Source: `firmware/reflex_bytecode_vm_spec.md` + `protocol/wire_protocol_spec.md`*

The node boot sequence is time-critical:

| T+ (ms) | Event |
|---------|-------|
| 0 | GPIO safe state asserted |
| 5 | Hardware watchdog kicked |
| 10 | UART initialized |
| 20 | `DEVICE_IDENTITY` sent |
| 50 | `SELFTEST_RESULT` sent |
| 50–300 | Wait for `ROLE_ASSIGN` |
| 500 | Enter `OPERATIONAL` mode |

If the Jetson isn't ready to send `ROLE_ASSIGN` within 300ms, the node enters `IDLE` mode and retries every 10 seconds.

**The problem:** During development, the Jetson Orin Nano takes **30+ seconds** to boot Linux, initialize the serial bridge service, and send `ROLE_ASSIGN`. The node will be sitting in `IDLE` mode for 30 seconds, retrying every 10s. This is correct behavior — don't "fix" the 300ms timeout. Just know that on power-up, you'll wait 30+ seconds before the system becomes operational.

### 7.2 First Power-On Without Jetson Is Correct Behavior [MEDIUM]
*Source: `protocol/wire_protocol_spec.md`, Boot State Machine*

On first power-up with no Jetson connected, the node will:
1. Send `DEVICE_IDENTITY` (nobody listening)
2. Send `SELFTEST_RESULT` (nobody listening)
3. Wait 300ms for `ROLE_ASSIGN` (nobody responds)
4. Enter `IDLE` mode
5. Retry `ROLE_ASSIGN` request every 10 seconds indefinitely

This is **by design.** The node is functional but idle — GPIOs are in safe state, motors are not driven, the heartbeat is not running. Don't add a "no Jetson detected, power down" feature. The node should patiently wait. In a real deployment, the Jetson will eventually boot and send `ROLE_ASSIGN`.

### 7.3 I2C Bus Scan Timing Budget [LOW]
*Source: `firmware/io_driver_registry.json`, AUTO_DETECT_RESULT section*

The `AUTO_DETECT_RESULT` message includes I2C device discovery. The I2C bus scan probes all 128 possible 7-bit addresses, with a 100µs timeout per address for NACK detection. That's `128 × 100µs = 12.8ms` per bus. With 2 I2C buses, the total scan time is ~**25.6ms**.

This fits comfortably within the T+50ms deadline for `SELFTEST_RESULT`. However, if you add a third I2C bus or use longer timeouts (some I2C devices need up to 1ms to respond after power-up), the scan can exceed the deadline and delay the boot sequence.

**Rule:** Budget 15ms per I2C bus maximum. Use 100µs NACK timeout. Skip addresses that the `IO_DRIVER_REGISTRY` marks as "never present" for the current node type to reduce scan time.

---

## Quick Reference: Error Codes That Indicate Pitfall Violations

| Error Code | Name | Likely Pitfall |
|------------|------|----------------|
| `0x10` | `ERR_CRC_MISMATCH` | §1.2 CRC scope wrong |
| `0x11` | `ERR_FRAME_TOO_LARGE` | §1.3 Using 1024 instead of 1051 |
| `0x20` | `ERR_INVALID_OPCODE` | §2.6 HALT not recognized as NOP+flags |
| `0x21` | `ERR_STACK_UNDERFLOW` | §2.3 PID_COMPUTE stack order |
| `0x22` | `ERR_STACK_OVERFLOW` | §5.3 VM memory budget exceeded |
| `0x30` | `ERR_INVALID_PIN` | §2.2 Variable/pin space aliasing |
| `0x31` | `ERR_PIN_PROTECTED` | Safety pin accessed from VM |
| `0x32` | `ERR_CYCLE_BUDGET` | §2.7 Cycle counter not crossing CALL/RET |
| `0x40` | `ERR_ROLE_TIMEOUT` | §7.1 Jetson not ready in 300ms |
| `0x41` | `ERR_HEARTBEAT_MISS` | §3.2 Wrong heartbeat interval |

---

*Last updated: 2025. Based on NEXUS spec corpus v1.0 (21 files, ~19,200 lines). Review against spec updates before each release.*
