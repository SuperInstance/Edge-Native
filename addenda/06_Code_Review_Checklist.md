# Code Review Checklist — What to Look For in Every Pull Request

## How to Use This Checklist

Every PR must pass **ALL** applicable checks before merge. The reviewer checks off each item by verifying the code satisfies the requirement. Any unchecked item **blocks merge**. Items marked "safety-critical" carry a mandatory second reviewer.

If a check does not apply to the changed files, mark it **N/A** with a one-line justification. Do not leave items blank.

---

## 1. ESP32 Firmware — General

### Memory Safety

- [ ] **No `malloc`/`calloc` in ISR context or reflex execution path.** Search for `malloc`, `calloc`, `realloc`, `strdup`, `json_malloc` inside any function called from an ISR or from the reflex dispatch loop. Static allocation or pool allocators are the only acceptable alternatives.
- [ ] **No dynamic allocation in safety-critical code paths (Tier 2/3).** Every allocation in `safety_supervisor`, `safety_watchdog`, `reflex_engine`, and `kill_switch` modules must be provably static. Run `nm` on the ELF and confirm no `malloc` symbols in those compilation units.
- [ ] **All stack-allocated buffers have bounded size with explicit limits.** No `char buf[]` sized from a runtime variable without a `MIN(limit, value)` guard. Prefer fixed-size arrays with `#define` or `enum` constants.
- [ ] **No unbounded loops.** Every `while` or `for` loop must have a maximum iteration count, a timeout, or a provably finite bound (e.g., iterating over a fixed-length array). Search for `while(1)` and `for(;;)` outside of FreeRTOS task bodies and reject unless wrapped with a break-on-condition or watchdog kick.
- [ ] **No recursive functions in safety-critical paths.** Grep for functions that call themselves (directly or indirectly via call-graph analysis) inside `firmware/safety/` and `firmware/reflex/`. Recursion risks stack overflow which is unrecoverable on ESP32.
- [ ] **`sprintf`/`snprintf` used instead of `strcpy`/`strcat`.** All string operations must use bounded-length calls. `sprintf` is acceptable only when the output buffer is provably large enough; prefer `snprintf` with the buffer size argument.
- [ ] **All array accesses bounds-checked or provably within bounds.** Index variables derived from external input (serial payload, sensor readings, JSON config) must be validated before use as an array subscript. For loop indices over fixed arrays, the bound must be a compile-time constant.

### ISR Safety

- [ ] **ALL ISR functions marked with `IRAM_ATTR`.** Verify every function registered with `gpio_isr_handler_add`, `gpio_install_isr_service`, or `xtensa_set_interrupt_handler` has `IRAM_ATTR` in its declaration. Missing this causes a cache miss exception if flash is being accessed during the ISR.
- [ ] **ISR contains NO: `printf`, `ESP_LOGx`, `cJSON`, floating-point operations, mutex operations.** Search for these patterns inside every ISR function body. Even indirect calls through helper functions are forbidden — trace the call graph.
- [ ] **ISR only calls: `gpio_set_level`, `ledc_set_duty`, `xSemaphoreGiveFromISR`, `ets_delay_us`.** Any other function call in an ISR must be justified in a code comment explaining why it is safe (IRAM-resident, no blocking, no malloc).
- [ ] **ISR execution time < 1 ms.** Estimate instruction count: ESP32-S3 at 240 MHz executes ~240 instructions/µs. A 1 ms budget allows ~240,000 instructions. For ISRs containing more than ~50 lines of C, add a cycle-counter measurement and assert it stays under budget.
- [ ] **No ISR calls any function not in IRAM.** Build with `CONFIG_ESP32S3_DATA_IN_IRAM=y` and check the linker map (`.map` file) for ISR functions. All functions called from ISRs must appear in the `.iram.text` section.

### FreeRTOS Usage

- [ ] **Task priorities: `safety_supervisor` > `safety_watchdog` > application tasks.** Verify `xTaskCreatePinnedToCore` priority arguments. Safety tasks must be pinned to the same core (Core 0) and have strictly higher priority than any application or communication task.
- [ ] **No `vTaskDelay` in safety-critical tasks.** Safety tasks must use FreeRTOS timers, event groups (`xEventGroupWaitBits`), or task notifications (`ulTaskNotifyTake`). `vTaskDelay` makes the task unresponsive during the delay period.
- [ ] **No `vTaskDelete` in normal operation.** Use `vTaskSuspend`/`vTaskResume` instead. Dynamic task creation and deletion fragments the FreeRTOS heap and makes it impossible to guarantee worst-case timing.
- [ ] **All FreeRTOS API calls from ISR use `FromISR` variants.** Search for `xSemaphoreGive`, `xQueueSend`, `xEventGroupSetBits` without the `FromISR` suffix inside ISR functions. Replace with `xSemaphoreGiveFromISR`, `xQueueSendFromISR`, `xEventGroupSetBitsFromISR`.
- [ ] **Mutex never held across a context switch.** If a mutex is taken and then the task blocks (on a queue, semaphore, or delay), the mutex priority is implicitly boosted to that of the highest waiter. Use `portYIELD_WITHIN_API` carefully, or restructure to hold the mutex for the minimum possible duration.
- [ ] **Queue sends from ISR have `timeout=0`.** `xQueueSendFromISR` must never block. Verify all call sites pass `pdFALSE` as the `pxHigherPriorityTaskWoken` argument is used correctly.

### Power Management

- [ ] **WiFi/BLE disabled if not used by this firmware role.** Check `app_main` and `board_config.h`: if the role is a pure reflex controller (no telemetry), confirm `esp_wifi_stop()` or `esp_bt_controller_disable()` is called during init. Leaving the radio active wastes ~100 mA.
- [ ] **Light sleep not used during normal operation.** `esp_light_sleep_start()` adds 200–500 µs wakeup latency and is inappropriate when the system must respond to safety events in < 1 ms. Only acceptable during a deliberate PROVISIONING or SHIPPING state.
- [ ] **CPU frequency set appropriately.** Active operation at 240 MHz; confirm `esp_pm_configure()` or `CONFIG_ESP32S3_DEFAULT_CPU_FREQ_MHZ` is set to 240. Running at 160 MHz wastes latency for zero power savings on ESP32-S3.

---

## 2. Wire Protocol Layer (COBS + Message Dispatch)

### COBS Implementation

- [ ] **Encode/decode handles 254-byte run correctly (emits `0xFF`, not `0x00`).** In a payload segment of 254 non-zero bytes followed by a zero byte, the encoder must emit a `0xFF` overhead byte (meaning "254 non-zero bytes follow"), not `0x00` (which signals end-of-frame). Write a unit test: encode `[1]*254 + [0]` and verify the first byte is `0xFF`.
- [ ] **Encode/decode handles empty payload correctly.** An empty payload should encode to the single byte `0x01` (zero non-zero bytes, then implicit zero). Decoding `0x01` must yield an empty buffer.
- [ ] **Encode/decode handles all-zeros payload correctly.** A payload of `[0, 0, 0]` must encode to `0x01 0x01 0x01 0x01` (four overhead bytes, each meaning "one zero follows"), and round-trip decode must return `[0, 0, 0]`.
- [ ] **Frame reception rejects frames > 1051 bytes.** The COBS overhead for a 1024-byte payload plus 11-byte header plus 2-byte CRC is 1051 bytes. If the UART receive buffer exceeds 1051 before seeing a `0x00` delimiter, the frame must be discarded with error `FRAME_TOO_LONG (0x5004)`.
- [ ] **CRC-16 computed over header + payload ONLY (not including CRC bytes).** The CRC covers bytes 0 through (header_size + payload_size - 1). The two CRC bytes themselves are excluded from the CRC input. Verify by computing CRC of a known test vector.
- [ ] **CRC-16/CCITT-FALSE: polynomial `0x1021`, init `0xFFFF`, final XOR `0x0000`.** Confirm the implementation matches this exact parameter set. Test with the reference vector: CRC of `"123456789"` = `0x29B1`.

### Message Dispatch

- [ ] **Unknown message types rejected gracefully (error `0x5006`).** When the dispatch table has no handler for a received message type, the firmware must send an ERROR response with code `UNSUPPORTED_MESSAGE (0x5006)`. It must NOT crash, hang, or silently ignore the frame.
- [ ] **Frame too short (< 12 bytes decoded) rejected (error `0x5002`).** The minimum valid message is 12 bytes: 11-byte header + 1 byte minimum payload (for messages with a body). A decoded frame shorter than 12 bytes must trigger `FRAME_TOO_SHORT (0x5002)`.
- [ ] **Flag validation: `IS_ACK` and `ACK_REQUIRED` not both set.** A single message must never have both `IS_ACK` (bit 6) and `ACK_REQUIRED` (bit 7) set. If both are set, reject with `INVALID_FLAGS (0x5003)`.
- [ ] **`IS_ERROR` not set without `IS_ACK` (except message `0x15`).** Error responses are ACKs of previously sent messages. The only exception is message type `0x15` (HEARTBEAT_ERROR), which can set `IS_ERROR` independently.
- [ ] **Sequence numbers validated (in-order, duplicate, gap detection).** The receiver must track the expected next sequence number. Out-of-order frames trigger `SEQ_GAP_DETECTED`; duplicates are silently ACKed but not re-processed.
- [ ] **Critical messages (`ACK_REQUIRED`) have retry logic with exponential backoff.** Messages flagged `ACK_REQUIRED` must be retried with backoff: 50 ms, 100 ms, 200 ms, 400 ms, then fail. Maximum 5 attempts before reporting `SEND_TIMEOUT`.
- [ ] **Non-retryable errors not retried.** If the receiver replies with `REFLEX_PARSE_ERROR (0x5010)`, `REFLEX_TOO_LARGE (0x5011)`, or `REFLEX_COMPILE_ERROR (0x5012)`, the sender must NOT retry — the same payload will fail again.

### Endianness

- [ ] **Message header fields read/written in big-endian (network byte order).** Every `uint16_t` and `uint32_t` field in the wire protocol header must be serialized with `htons()`/`htonl()` (or equivalent manual byte swapping) before transmission and deserialized with `ntohs()`/`ntohl()` on receipt.
- [ ] **No native byte-order assumptions for serial protocol.** The ESP32-S3 is little-endian; the Jetson Orin is also little-endian, but the protocol must work correctly even if one side is big-endian. Verify no `memcpy` of header structs directly from the serial buffer.
- [ ] **All `uint16`/`uint32` fields use `htons`/`htonl` or manual byte swapping.** Audit every `read_u16`, `read_u32`, `write_u16`, `write_u32` helper function. Manual swap must do `(val >> 8) | (val << 8)` for 16-bit; for 32-bit, swap bytes 0↔3 and 1↔2.

---

## 3. Bytecode VM

### Safety Invariants

- [ ] **Stack push checks `SP < 256` before increment.** The `PUSH_F`, `PUSH_I`, and `DUP` opcodes must verify `vm->sp < 256` before writing to `vm->stack[vm->sp++]`. If the check fails, set `vm->status = VM_STACK_OVERFLOW` and execute `HALT`.
- [ ] **Stack pop checks `SP > 0` before decrement.** The `POP`, `ADD_F`, `SUB_F`, `MUL_F`, `DIV_F`, `MAX_F`, `MIN_F`, `CMP_*`, and all binary opcodes must verify `vm->sp >= expected_args` before reading from the stack. Underflow sets `VM_STACK_UNDERFLOW` and halts.
- [ ] **Cycle counter incremented per instruction, `HALT` at > 10,000.** Every instruction in the fetch-decode-execute loop increments `vm->cycle_count`. If `vm->cycle_count > 10000`, the VM halts with status `VM_CYCLE_LIMIT_EXCEEDED`. This prevents infinite reflex loops.
- [ ] **Actuator values clamped to min/max AFTER VM execution (not inside).** The reflex engine reads the actuator array after the VM halts and clamps each value to its configured `[min, max]` range before writing to hardware. The VM itself must not clamp — that would mask programming errors.
- [ ] **Division by zero returns `0.0f` (not NaN/Inf).** IEEE 754 float division by zero produces ±Inf, and 0.0f/0.0f produces NaN. Both would propagate through subsequent arithmetic and corrupt actuator outputs. Check the divisor explicitly before every `DIV_F` and return `0.0f` if zero.
- [ ] **Jump targets validated at compile time (within bounds, 8-byte aligned).** The JSON-to-bytecode compiler must verify that every `JMP`, `JZ`, `JNZ`, `CALL`, and `RET` target is: (a) within the bytecode array bounds, (b) 8-byte aligned (instruction size), and (c) not pointing to the middle of another instruction.

### Opcode Implementation

- [ ] **`DIV_F` checks for zero divisor explicitly.** Do not rely on IEEE 754 behavior. The check must be: `if (divisor == 0.0f) { push(0.0f); continue; }`.
- [ ] **`NEG_F` uses XOR `0x80000000` (bit flip, not float negate).** Correct implementation: `uint32_t bits = as_uint32(pop()); push(as_float(bits ^ 0x80000000))`. Using `-val` or `fneg` is acceptable if the compiler generates identical assembly, but the bit-flip is preferred for clarity and determinism.
- [ ] **`ABS_F` uses AND `0x7FFFFFFF` (bit clear, not `fabsf`).** Correct implementation: `uint32_t bits = as_uint32(pop()); push(as_float(bits & 0x7FFFFFFF))`. Same rationale as `NEG_F`.
- [ ] **`CLAMP_F` implements the shared-upper-half encoding correctly (or uses `MAX_F` + `MIN_F` decomposition).** The CLAMP opcode encodes three floats in two instruction slots using a shared upper 16 bits for the min and max values. Verify the decode logic reconstructs all three operands correctly. If decomposed into `MAX_F` followed by `MIN_F`, confirm the compiler emits the correct sequence.
- [ ] **`PID_COMPUTE`: integral anti-windup clamped, derivative computed correctly.** The integral accumulator must be clamped to `[-integral_limit, +integral_limit]`. Derivative must use the previous error (not previous measurement) for setpoint changes. Confirm the D term is not computed on the first cycle (no previous error).
- [ ] **`READ_PIN` with `operand1 >= 64` reads variables, `0–63` reads sensors.** The operand encodes the source: indices 0–63 map to the sensor array; indices 64–319 map to the variable array at offset `operand1 - 64`. Out-of-range operands (> 319) must trigger `VM_INVALID_OPERAND`.
- [ ] **`WRITE_PIN` with `operand1 >= 64` writes variables, `0–63` writes actuators.** Same encoding as `READ_PIN` but targeting the actuator and variable arrays. The clamping step happens after the VM exits, not during `WRITE_PIN`.
- [ ] **`SYSCALL` flag (bit 7 of flags) checked for `NOP` opcode.** Opcode `0x00` is `NOP` unless bit 7 of the flags byte is set, in which case it becomes `SYSCALL`. The decoder must check this bit before dispatching.

### Memory Layout

- [ ] **VM state struct fits in ~3 KB SRAM.** Total VM memory: data stack (1 KB) + variables (1 KB) + PID state (256 B) + PC + SP + cycle_count + status + flags = ~2.1 KB. The struct should be verified with `sizeof(vm_state_t)` in a test build.
- [ ] **Data stack: 256 entries × 4 bytes = 1 KB.** Defined as `float stack[256]` or `uint32_t stack[256]`. Must be statically allocated within the `vm_state_t` struct or as a global, never on the heap.
- [ ] **Variables: 256 × 4 bytes = 1 KB.** Defined as `float variables[256]`. Variables persist across VM invocations within the same reflex cycle but are reset on reflex reload.
- [ ] **PID state: 8 × 32 bytes = 256 bytes.** Eight PID slots, each containing: `integral`, `prev_error`, `setpoint`, `kp`, `ki`, `kd`, `integral_limit`, `output` (8 × float = 32 bytes).
- [ ] **All VM memory statically allocated.** No `malloc`, no `pvPortMalloc`, no heap allocation anywhere in the VM module. The entire VM state lives in a single static struct or is passed by pointer from a statically allocated parent.

---

## 4. Safety System

### Kill Switch

- [ ] **GPIO configured INPUT with external pull-up, falling edge interrupt.** The kill switch pin must use `gpio_set_direction(KILL_PIN, GPIO_MODE_INPUT)` with `gpio_pulldown_dis(KILL_PIN)` and `gpio_pullup_en(KILL_PIN)` (or rely on an external physical pull-up). The interrupt triggers on falling edge (`GPIO_INTR_NEGEDGE`).
- [ ] **ISR priority = `ESP_INTR_FLAG_LEVEL1` (highest).** Register with `gpio_isr_handler_add(KILL_PIN, kill_isr, NULL)` and set the interrupt to level 1 (or NMI if available). No other ISR may preempt the kill switch handler.
- [ ] **ISR only: set flag, drive outputs safe, disable PWM, give semaphore.** The ISR body must be limited to: (1) `kill_flag = true`, (2) iterate actuator pins and `gpio_set_level(pin, SAFE_LEVEL)`, (3) `ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, 0)`, (4) `xSemaphoreGiveFromISR(kill_sem, &woken)`. No logging, no serialization, no WiFi.
- [ ] **Deferred handler: log event, set state, notify Jetson.** A high-priority FreeRTOS task waits on `kill_sem`. Upon wake, it: (1) writes a safety event to NVS, (2) sets `safety_state = SAFE_STATE`, (3) sends a KILL_ALERT message to the Jetson via serial.
- [ ] **NO auto-resume after kill switch.** After a kill event, the system enters `PROVISIONING` state. It must NOT automatically resume normal operation when the kill switch is released. A full re-initialization sequence (including heartbeat re-establishment and explicit RESUME command from the Jetson) is required.

### Watchdog

- [ ] **Hardware watchdog (MAX6818) kick at 200 ms intervals.** A dedicated FreeRTOS timer or high-priority task must toggle the watchdog input at least every 200 ms. Missing a kick triggers a hard hardware reset — this is the last line of defense.
- [ ] **Alternating `0x55`/`0xAA` kick pattern.** The MAX6818 requires an alternating bit pattern; sending the same value twice does not reset the timer. Verify the kick function toggles between `0x55` and `0xAA` on successive calls.
- [ ] **Software watchdog monitors ALL application tasks.** Each application task must check in with the software watchdog at a known interval (e.g., every 100 ms). The watchdog task tracks a per-task "last seen" timestamp and flags any task that misses its deadline.
- [ ] **Safety supervisor hung → stop feeding HWD → system reset.** The hardware watchdog kick is gated behind a health check of the safety supervisor task. If the supervisor stops responding, the HWD starves and triggers a hard reset within 200–400 ms.
- [ ] **Boot counter in NVS, > 5 in 10 min → FAULT mode.** Each boot increments a counter with a timestamp in NVS. On boot, the firmware reads the counter; if more than 5 resets occurred within a rolling 10-minute window, the system enters FAULT mode and refuses to start application tasks.

### Heartbeat

- [ ] **Interval: 100 ms (safety spec).** The heartbeat timer fires every 100 ms. The Jetson must send a HEARTBEAT message every 100 ms. The ESP32 firmware must send a HEARTBEAT response every 100 ms. The 1000 ms wire-protocol-level heartbeat is a separate keepalive and does not replace the safety heartbeat.
- [ ] **DEGRADED at 5 misses (500 ms).** After 5 consecutive missed heartbeats (500 ms with no valid heartbeat received), the safety supervisor transitions to `DEGRADED` state: actuators hold their last position, but new reflex outputs are still applied.
- [ ] **SAFE_STATE at 10 misses (1000 ms).** After 10 consecutive missed heartbeats, the system transitions to `SAFE_STATE`: all actuators driven to their configured safe positions, PWM disabled, Jetson notified.
- [ ] **Resume requires 3 good heartbeats + explicit RESUME command.** After a heartbeat loss event, the system does not automatically resume. It must receive 3 consecutive valid heartbeats AND a RESUME command from the Jetson before transitioning back to ACTIVE.
- [ ] **NO auto-resume.** This rule is absolute. Even if heartbeats resume on their own, the system stays in SAFE_STATE until a human-initiated or Jetson-initiated RESUME command is received.

### Overcurrent

- [ ] **INA219 alert pin configured as GPIO interrupt.** The INA219 shunt monitor has an alert output that fires when the current exceeds a programmable threshold. This pin must be connected to an ESP32 GPIO and configured as a falling-edge interrupt.
- [ ] **100 ms detection window (sustained overcurrent, not inrush).** The ISR increments a counter; the deferred handler checks if the counter exceeds a threshold over a 100 ms window. This filters out motor startup inrush currents (typically 20–50 ms).
- [ ] **200 ms inrush allowance after initial activation.** When an actuator channel is first enabled, the overcurrent detection is suppressed for 200 ms to allow the motor to reach steady-state current.
- [ ] **Channel disabled on overcurrent, requires manual re-enable.** When overcurrent is confirmed, the affected channel is immediately disabled (PWM = 0, output set to safe level). It must NOT auto-re-enable. Re-enabling requires an explicit ENABLE_CHANNEL command from the Jetson.

---

## 5. Jetson Python Code

### Serial Bridge

- [ ] **Async I/O (`asyncio`) for all serial ports.** All serial communication must use `pyserial-asyncio` or `aiofiles`. No blocking `serial.Serial.read()` or `serial.Serial.write()` calls in the main event loop. Each serial port gets its own `asyncio.StreamReader`/`StreamWriter` pair.
- [ ] **COBS encode/decode matches ESP32 implementation exactly.** The Python COBS codec must produce identical byte sequences as the ESP32 C implementation for all test vectors. Run the shared test suite against both implementations.
- [ ] **Sequence numbers tracked per-direction.** The Jetson maintains separate sequence counters for outgoing (Jetson→ESP32) and incoming (ESP32→Jetson) messages. Each direction increments independently.
- [ ] **Heartbeat sent at 100 ms intervals.** An `asyncio` task sends a HEARTBEAT message every 100 ms to every connected ESP32 node. Use `asyncio.sleep(0.1)` in the loop, not `time.sleep(0.1)`.
- [ ] **Timeout handling for all serial operations.** Every `await reader.read()` and `await writer.write()` must have an `asyncio.wait_for(..., timeout=N)` wrapper. Default timeout: 1 second for normal messages, 200 ms for heartbeat responses.

### MQTT

- [ ] **QoS 2 for override topics (exactly-once).** Topics under `nexus/override/` use QoS 2 to guarantee delivery. The broker must support QoS 2 (e.g., Mosquitto, EMQX).
- [ ] **QoS 1 for status topics (at-least-once with retain).** Topics under `nexus/status/` use QoS 1 with `retain=True` so that new subscribers immediately receive the last known state.
- [ ] **QoS 0 for telemetry topics (fire-and-forget).** Topics under `nexus/telemetry/` use QoS 0 to minimize bandwidth. Occasional message loss is acceptable for telemetry streams.
- [ ] **Clean disconnect on shutdown (LWT message published).** On graceful shutdown, the MQTT client must: (1) publish an OFFLINE status to `nexus/status/{node_id}`, (2) call `client.disconnect()`. The LWT (Last Will and Testament) must be configured at connection time to publish OFFLINE if the client disconnects ungracefully.

### LLM Integration

- [ ] **Code generation and validation use SEPARATE model instances.** The generation LLM and the validation LLM must be independent API calls (or separate model instances) to prevent the generator from influencing the validator. The validator must not see the generation prompt.
- [ ] **Generated reflex JSON validated against schema before compilation.** Every reflex produced by the LLM must be validated against the `reflex_definition.json` JSON Schema before being sent to the ESP32 for compilation. Invalid JSON must be rejected with a descriptive error.
- [ ] **Timeout on all LLM API calls (60 seconds).** Every `openai.ChatCompletion.create()` or equivalent call must have `timeout=60` set. If the LLM does not respond within 60 seconds, the system falls back to a pre-defined simple reflex.
- [ ] **Fallback to simpler reflex if LLM unavailable.** If the LLM API is unreachable, rate-limited, or times out, the system must fall back to a hard-coded safe reflex (e.g., hold current position, disable affected outputs).
- [ ] **No raw LLM output sent directly to ESP32.** All LLM output must be parsed, validated, and compiled before transmission. The ESP32 must never receive raw text from an LLM.

### Module Interface

- [ ] **All modules implement `NexusModule` ABC.** Every Python module under `jetson/modules/` must inherit from `NexusModule` and implement: `async start()`, `async stop()`, `async health_check() -> HealthReport`, and `resource_budget() -> ResourceBudget`.
- [ ] **Resource budgets reported honestly.** `resource_budget()` must return accurate estimates of CPU%, GPU%, RAM, and VRAM usage. Over-reporting is acceptable; under-reporting is a bug that can lead to resource exhaustion.
- [ ] **Hot-reload tested and working.** Modules must support `stop()` → reload code → `start()` without crashing the parent process. The module manager must handle `ImportError`, `SyntaxError`, and runtime exceptions during reload gracefully.
- [ ] **Module failure does not crash other modules.** If any module raises an unhandled exception, the module manager must catch it, log the error, stop the failed module, and continue running all other modules. A single module failure must never cascade.

---

## 6. Configuration and Build

### Partition Table

- [ ] **Factory partition is NOT OTA-modifiable.** The `factory` partition in `partitions.csv` must be marked as `type=app, subtype=factory`. It is flashed once during manufacturing and never updated via OTA. OTA updates only write to `ota_0` and `ota_1`.
- [ ] **OTA_0 and OTA_1 are 1.5 MB each.** Each OTA slot must be at least 1.5 MB to accommodate the current ~320 KB firmware plus significant headroom for future growth. Verify in `partitions.csv`: `ota_0, app, ota_0, 0x12000, 1.5M` and equivalent for `ota_1`.
- [ ] **Reflexes partition uses LittleFS (not SPIFFS).** The reflex storage partition must use `type=data, subtype=spiffs, filesystem_type=littlefs` (or equivalent for ESP-IDF v5.2+). LittleFS supports wear leveling and directory operations that SPIFFS does not.
- [ ] **NVS partition is 24 KB.** The NVS partition stores: boot count + timestamp (2 entries), safety events ring buffer (max 32 events × 64 bytes), cached role configuration. 24 KB provides sufficient space with headroom for future keys.

### Build Configuration

- [ ] **ESP-IDF v5.2+.** Verify `IDF_VERSION` in the project's `CMakeLists.txt` or `idf.py --version` output. ESP-IDF v5.2 introduced significant improvements to the LittleFS driver and RISC-V toolchain for ESP32-S3.
- [ ] **`CONFIG_ESP32S3_DATA_IN_IRAM=y`.** This Kconfig option places all read-only data in IRAM, preventing cache-miss exceptions during ISR execution. Enable in `sdkconfig.defaults` or via `idf.py menuconfig`.
- [ ] **Optimizer: `-O2` (not `-O0` debug, not `-O3` risky).** `-O0` produces code that is too large and slow for safety-critical timing constraints. `-O3` may introduce aggressive optimizations that make debugging difficult and can reorder memory operations in ways that break ISR safety. Use `-O2` for release builds and `-Og` for debug builds.
- [ ] **LTO: disabled for safety-critical code.** Link-Time Optimization can make it impossible to map crash addresses to source lines, complicating post-mortem analysis. Disable with `CONFIG_COMPILER_OPTIMIZATION_LTO=n` for firmware targets that include safety modules.
- [ ] **Stack canary enabled.** Verify `CONFIG_COMPILER_STACK_CHECK_ALL=y` or at minimum `CONFIG_COMPILER_STACK_CHECK` is enabled. Stack canaries detect buffer overflow before the return address is corrupted.
- [ ] **Heap poisoning enabled in debug builds.** `CONFIG_HEAP_POISONING_COMPREHENSIVE=y` fills freed memory with `0xFE` and new allocations with `0xCE`, making use-after-free detectable. Enable in debug builds only (adds ~10% overhead).

---

## Anti-Patterns — IMMEDIATE REJECT

The following patterns are **automatic rejection reasons**. Do not approve a PR containing any of these:

| # | Pattern | Why It's Rejected |
|---|---------|-------------------|
| 1 | `while(1)` or `for(;;)` without a break condition in safety-critical code | Unbounded loop can hang the safety system permanently |
| 2 | `malloc` in ISR or safety task | Heap fragmentation; malloc can block; ISR cannot block |
| 3 | `printf` in ISR | printf is not IRAM-safe and can take milliseconds |
| 4 | `delay()` in ISR | Blocks the ISR, preventing other interrupts from being serviced |
| 5 | Any sleep/wait in ISR | Same as above; ISR must return in < 1 ms |
| 6 | Global mutable state without `volatile` (when accessed from ISR) | Compiler may cache the value in a register; ISR writes become invisible |
| 7 | Float operations in ISR | ESP32 float library is not in IRAM by default; cache miss → crash |
| 8 | cJSON or any JSON library in ISR | JSON parsing involves malloc, string operations, and is slow |
| 9 | Direct hardware access bypassing safety guard API | Safety invariants (current limits, solenoid timeouts) are bypassed |
| 10 | Hardcoded safety thresholds instead of configuration | Safety limits must be configurable; hardcoded values cannot be updated in the field |
| 11 | Ignoring return values for safety-critical calls (`gpio_set_level`, etc.) | A failed GPIO write can leave an actuator in an unsafe state |
| 12 | Timeouts exceeding spec maximum (heartbeat > 100 ms, ISR > 1 ms) | Violates the safety timing budget; a missed safety event may not be caught in time |

---

*This checklist is a living document. Update it when new safety requirements are added or when a near-miss is discovered during code review or testing.*
