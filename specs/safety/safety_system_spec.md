# NEXUS Platform Safety System Specification

**Document ID:** NEXUS-SS-001  
**Version:** 2.0.0  
**Date:** 2025-01-15  
**Classification:** Safety-Critical  
**Compliance:** IEC 61508 (SIL 1 target), ISO 26262 (ASIL-B equivalent), IEC 60945 (Marine)  
**Author:** NEXUS Safety Engineering Team  
**Review Status:** Approved  

---

## Table of Contents

1. [Four-Tier Safety Architecture](#1-four-tier-safety-architecture)
2. [Kill Switch Specification](#2-kill-switch-specification)
3. [Watchdog Timer Specification](#3-watchdog-timer-specification)
4. [Heartbeat Protocol](#4-heartbeat-protocol)
5. [Overcurrent Protection](#5-overcurrent-protection)
6. [Solenoid/Relay Timeout](#6-solenoidrelay-timeout)
7. [Boot Safety Sequence](#7-boot-safety-sequence)
8. [Failsafe State Definitions](#8-failsafe-state-definitions)
9. [Safety Event Logging](#9-safety-event-logging)
10. [Safety Certification Checklist](#10-safety-certification-checklist)

---

## 1. Four-Tier Safety Architecture

The NEXUS platform implements a defense-in-depth safety architecture with four independent tiers. No single tier is sufficient on its own; the system is safe only when all four tiers are operational. Each tier provides an independent safety barrier, and the failure of any one tier must not compromise the effectiveness of the remaining tiers.

### 1.1 Architecture Overview

```
+------------------------------------------------------------------+
|                     TIER 1: HARDWARE INTERLOCK                    |
|  Physical kill switch, polyfuses, hardware watchdog, pull-downs   |
|  Response: <1ms (electrical) | Authority: ABSOLUTE                |
+------------------------------------------------------------------+
          |
+------------------------------------------------------------------+
|                     TIER 2: FIRMWARE SAFETY GUARD                 |
|  E-Stop ISR, safe-state outputs, sensor validation, rate limiting |
|  Response: <10ms (ISR) | Authority: overrides all software        |
+------------------------------------------------------------------+
          |
+------------------------------------------------------------------+
|                     TIER 3: SUPERVISORY TASK                      |
|  Watchdog feeder, heartbeat monitor, safety state machine         |
|  Response: <100ms | Authority: can override control tasks         |
+------------------------------------------------------------------+
          |
+------------------------------------------------------------------+
|                     TIER 4: APPLICATION CONTROL                   |
|  PID loops, reflexes, AI inference, domain logic                  |
|  Response: <10ms (control loop) | Authority: lowest               |
+------------------------------------------------------------------+
```

### 1.2 Tier 1: Hardware Interlock

**Purpose:** Provide an absolute, software-independent safety barrier that operates regardless of firmware state, processor health, or power supply quality.

**Hardware/Software Boundary:**
- Entirely hardware-implemented. No software dependency whatsoever.
- Components: physical kill switch (NC contact), external hardware watchdog IC (MAX6818), polyfuses (PTC), gate pull-down resistors (10KΩ), flyback diodes, TVS diodes.
- Software cannot disable, bypass, or reconfigure any Tier 1 component.
- The external WDT reset line is hardwired to the ESP32 EN (reset) pin with no software-controllable intermediate.

**Response Time Budget:**
| Event | Detection | Response | Total |
|-------|-----------|----------|-------|
| Kill switch press (mechanical) | 0ms (physical contact break) | 0ms (power path interrupted) | **<1ms** |
| External WDT timeout | 1.0s (timer expiry) | <1ms (reset pulse) | **<1.01s** |
| Polyfuse trip | 0ms (instantaneous at fault current) | <100ms (thermal trip) | **<100ms** |
| Flyback diode clamping | 0ms (instantaneous) | N/A (passive) | **<1µs** |

**Authority Scope:**
- ABSOLUTE. Tier 1 overrides everything else. No software, firmware, or user action can override a Tier 1 safety action.
- Kill switch physically interrupts power to all actuator circuits. No software recovery path exists while the kill switch is held open.
- External WDT physically resets the processor. No software can prevent this once the timer expires.

**Failure Mode Analysis (FMEA):**

| Failure Mode | Effect | Detection | Mitigation |
|-------------|--------|-----------|------------|
| Kill switch contact welds closed | E-Stop non-functional | Weekly manual test | Redundant: software watchdog triggers backup safe-state |
| Kill switch NC contact opens due to corrosion | Unintended safe-state | Visual inspection, alarm | Reconnect kill switch, investigate corrosion |
| MAX6818 WDT IC failure (stuck HIGH) | WDT reset lost | Software WDT (Tier 2) monitors HWD kick success | Software WDT triggers safe-state as backup |
| MAX6818 WDT IC failure (stuck LOW) | Continuous reset loop | Boot counter in NVS, >5 consecutive resets = alarm | Operator notification, manual intervention |
| Polyfuse fails open | Circuit permanently disabled | Output stuck in safe-state (acceptable) | Replace polyfuse |
| Polyfuse fails shorted | Overcurrent protection lost | Tier 2 overcurrent monitoring (INA219) detects fault | Software disables output + alarm |
| Pull-down resistor failure (open) | Floating gate on MOSFET | MOSFET may turn on due to noise | Tier 2 ensures all outputs LOW at boot + on WDT reset |

**Test Procedure:**
1. **Weekly Manual Kill Switch Test (Mandatory):**
   - With system in normal operation, press and hold kill switch.
   - Verify ALL actuators immediately deactivate (visual/audible confirmation).
   - Verify red LED illuminates (if powered via separate logic path).
   - Release kill switch.
   - Verify system enters provisioning state (does NOT auto-resume normal operation).
   - Record test result in maintenance log.

2. **Monthly Hardware WDT Test:**
   - Force WDT timeout by disabling the software kick task (test mode only).
   - Verify system resets within 1.1 seconds of WDT timeout.
   - Verify all outputs are in safe state after reset.
   - Record test result.

3. **Annual Full Tier 1 Validation:**
   - Perform kill switch timing measurement with oscilloscope (<1ms verification).
   - Verify polyfuse trip current with controlled overload.
   - Verify flyback diode clamping voltage with inductive load.
   - Replace any kill switch showing >10ms actuation time.

### 1.3 Tier 2: Firmware Safety Guard

**Purpose:** Provide a software-level safety barrier that can respond to detected faults faster than the supervisory task, and independently of the application control logic.

**Hardware/Software Boundary:**
- Implemented as ISRs (interrupt service routines) and the highest-priority FreeRTOS tasks.
- Runs on the same ESP32 processor as the application but at interrupt level.
- Has dedicated hardware resources: GPIO interrupt for kill switch, timer interrupt for output monitoring.
- Cannot be preempted by any application-level code.

**Response Time Budget:**
| Event | Detection | Response | Total |
|-------|-----------|----------|-------|
| E-Stop ISR trigger | <100µs (GPIO edge detection) | <1ms (all outputs safe) | **<1.1ms** |
| Overcurrent detection (ISR) | <1ms (INA219 alert pin) | <1ms (output disable) | **<2ms** |
| Sensor stale detection | <10ms (periodic check) | <10ms (safe-state transition) | **<20ms** |

**Authority Scope:**
- Can override any Tier 4 (application control) action.
- Can directly drive GPIO outputs to safe-state values without going through the application control path.
- Cannot override Tier 1 (by design - Tier 1 is absolute).

**Failure Mode Analysis (FMEA):**

| Failure Mode | Effect | Detection | Mitigation |
|-------------|--------|-----------|------------|
| ISR corrupted (flash bit flip) | Incorrect safety response | CRC on firmware partition | Boot from recovery partition |
| ISR stack overflow | System crash | FreeRTOS stack overflow hook | System reset via WDT |
| ISR priority misconfigured | ISR preempted by app code | Static analysis (SR-007) | Pipeline blocks deployment |
| GPIO interrupt missed | E-Stop not detected | Tier 3 periodic GPIO poll (backup) | Tier 3 triggers safe-state within 100ms |

**Test Procedure:**
1. **E-Stop Response Time Test:**
   - Connect oscilloscope to kill switch GPIO and one actuator output GPIO.
   - Trigger kill switch.
   - Measure time from GPIO edge to actuator output change.
   - PASS: <1.1ms. FAIL: investigate ISR priority, latency.
2. **Overcurrent Response Test:**
   - Connect programmable load to monitored output.
   - Ramp current above threshold.
   - Measure time from overcurrent threshold crossing to output disable.
   - PASS: <2ms.
3. **Sensor Stale Detection Test:**
   - Disconnect a safety-critical sensor.
   - Measure time from disconnection to safe-state transition.
   - PASS: <20ms (within sensor's configured stale timeout).

### 1.4 Tier 3: Supervisory Task

**Purpose:** Monitor the health of all system components, enforce timing constraints, and manage the overall safety state machine. This tier bridges the gap between the fast-but-simple hardware/tier-2 responses and the complex application logic.

**Hardware/Software Boundary:**
- Implemented as the highest-priority FreeRTOS task (safety_supervisor).
- Priority: configMAX_PRIORITIES - 1 (one below maximum to allow ISRs).
- Stack size: 2048 bytes (sufficient for state machine and logging).
- Runs at a fixed period of 10ms.

**Response Time Budget:**
| Event | Detection | Response | Total |
|-------|-----------|----------|-------|
| Heartbeat loss (degraded) | 500ms (5 missed) | <10ms (mode transition) | **<510ms** |
| Heartbeat loss (safe-state) | 1000ms (10 missed) | <10ms (all outputs safe) | **<1010ms** |
| Task watchdog timeout | 1.0s (configurable) | <10ms (safe-state transition) | **<1.01s** |
| Application task hung | 5.0s (extended timeout) | System reset via WDT | **<6.0s** |

**Authority Scope:**
- Can disable any application-level task (Tier 4) via FreeRTOS task suspend/delete.
- Can force any actuator to safe-state regardless of Tier 4 commands.
- Can force the system into degraded or safe-state mode.
- Can trigger a system reset by stopping the WDT feed (escalates to Tier 1).

**Failure Mode Analysis (FMEA):**

| Failure Mode | Effect | Detection | Mitigation |
|-------------|--------|-----------|------------|
| Supervisor task hung | All monitoring lost | Tier 1 HWD timeout after 1.0s | Full system reset |
| Supervisor task crashed | All monitoring lost | FreeRTOS detects, HWD timeout | Full system reset |
| State machine bug | Incorrect mode transitions | Formal verification of state machine | Unit tests + model checking |
| Misconfigured timeout | Too slow to detect faults | Static config validation | Pipeline blocks deployment |

**Test Procedure:**
1. **Heartbeat Loss Test:**
   - Disconnect Jetson heartbeat serial line.
   - Observe mode transitions: NORMAL → DEGRADED (at 500ms) → SAFE_STATE (at 1000ms).
   - Verify all actuators at safe-state in SAFE_STATE mode.
   - Reconnect heartbeat line.
   - Verify system returns to NORMAL after 3 consecutive good heartbeats.
2. **Task Watchdog Test:**
   - Inject a fault that causes an application task to hang (test mode).
   - Verify supervisor detects the hung task within 1.0s.
   - Verify system transitions to safe-state.

### 1.5 Tier 4: Application Control

**Purpose:** Implement the domain-specific control logic (PID loops, reflexes, AI inference, sequencing). This tier has the LOWEST safety authority and is subject to all constraints imposed by Tiers 1-3.

**Hardware/Software Boundary:**
- Implemented as one or more FreeRTOS tasks at priorities below the safety supervisor.
- No direct hardware access without going through safety-checked API functions.
- All actuator writes must pass through the safety guard API (which enforces rate limiting, enable checks, and safe-state limits).

**Response Time Budget:**
| Function | Target | Maximum |
|----------|--------|---------|
| PID control loop | 10ms | 50ms |
| Reflex execution | 5ms | 20ms |
| Sensor polling | 10ms | 100ms |
| AI inference (Jetson) | 100ms | 500ms |

**Authority Scope:**
- LOWEST. Can be overridden, suspended, or terminated by Tiers 1-3 at any time.
- Cannot directly access hardware without safety guard API.
- Must respect all safety constraints (rate limits, enable gates, timeouts).
- Has no authority to disable any safety mechanism.

**Failure Mode Analysis (FMEA):**

| Failure Mode | Effect | Detection | Mitigation |
|-------------|--------|-----------|------------|
| Control loop produces unsafe output | Actuator commanded to dangerous position | Tier 3 rate limiter + safe-state bounds | Output clamped to safe range |
| PID integral windup | Large overshoot or oscillation | Anti-windup in PID implementation | Output limited to safe range |
| AI inference produces bad result | Incorrect actuation | Tier 3 plausibility check | Reflex fallback or safe-state |
| Task CPU starvation | Control loop misses deadline | Tier 3 task watchdog | Degraded mode → safe-state |
| Memory leak | Heap exhaustion → crash | Tier 3 heap monitoring | Safe-state transition |

**Test Procedure:**
1. **Control Loop Timing Test:**
   - Enable all control loops at maximum complexity.
   - Measure each loop's actual period with logic analyzer.
   - PASS: all loops within their maximum period.
2. **PID Windup Test:**
   - Create a sustained error condition for 60 seconds.
   - Remove error (setpoint = measurement).
   - Verify no overshoot >5% of setpoint range.
3. **AI Inference Failure Test:**
   - Inject garbage data into AI input.
   - Verify system does not produce unsafe actuator commands.
   - Verify reflex fallback activates within 100ms.

---

## 2. Kill Switch Specification

### 2.1 Physical Requirements

| Parameter | Requirement | Notes |
|-----------|------------|-------|
| Contact type | Normally Closed (NC) | Circuit breaks on press |
| Actuation style | Mushroom-head, twist-to-release | Prevents accidental reset |
| Ingress protection | IP67 minimum | Marine/industrial environments |
| Color | RED head, YELLOW body | Per IEC 60945 / ISO 13850 |
| Min actuation force | 22N | Per ISO 13850 |
| Max actuation force | 50N | Must be operable with one hand |
| Electrical rating | 250VAC / 10A minimum | Must handle load current |
| Mechanical life | >100,000 operations | Minimum for marine/industrial use |
| Mounting | Panel mount, 22mm diameter | Standard industrial cutout |
| Illumination | Optional (LED ring, 24V) | Only for status indication, NOT required for function |
| Locking | Twist-to-release mechanism | Prevents accidental restart after E-Stop |

### 2.2 Wiring Specification

```
                    ┌──────────────────────┐
   +12V Supply ─────┤ Kill Switch (NC)     ├───── Actuator Power Rail
                    └──────────────────────┘
                          │
                          │ (dedicated wire, NOT shared)
                          │
                    ┌─────┴─────┐
                    │ ESP32 GPIO│  (GPIO_INPUT, PULLUP, interrupt on falling edge)
                    │ (E-Stop   │
                    │  Sense)   │
                    └───────────┘
```

**Critical Wiring Rules:**
1. The kill switch is wired in SERIES with the +12V actuator power supply, BEFORE any fuse. This is the primary safety path - breaking this circuit physically de-energizes all actuators regardless of software state.
2. A dedicated sense wire connects from the kill switch output (actuator side) to an ESP32 GPIO. This allows the firmware to detect the kill switch state and take software-level safety actions (logging, Jetson notification) in addition to the hardware-level power cutoff.
3. The sense wire must NOT share a connector pin, PCB trace segment, or wire bundle with any other signal. Physical separation is required to prevent a single fault from disabling both the kill switch and its sense wire.
4. The sense GPIO must be configured with an external pull-up resistor (10KΩ to 3.3V) so that a broken sense wire defaults to the "kill switch activated" (safe) state.
5. No other function, circuit, or signal path may share the kill switch or its wiring. It is a dedicated, single-purpose safety circuit.

### 2.3 GPIO Configuration

| Parameter | Value |
|-----------|-------|
| GPIO mode | INPUT |
| Pull mode | PULLUP (external 10KΩ also required) |
| Interrupt type | Falling edge (switch opens → GPIO goes LOW) |
| Interrupt priority | 1 (highest on ESP32) |
| Debounce | None (hardware-level, no software debounce) |
| ISR function | `estop_isr_handler()` |

### 2.4 ISR Specification

**Function:** `void IRAM_ATTR estop_isr_handler(void* arg)`

**Trigger:** Falling edge on E-Stop sense GPIO (kill switch pressed or sense wire broken).

**Timing Requirement:** ISR must begin execution within 100µs of the GPIO edge.

**Priority Level:** ESP_INTR_FLAG_LEVEL1 (highest configurable priority on ESP32).

**ISR Actions (in exact order):**

```
1. SET volatile flag: estop_triggered = true
2. SET all actuator GPIOs to SAFE state immediately:
   - For each configured actuator output pin:
     gpio_set_level(pin, SAFE_VALUE)
3. DISABLE all PWM outputs:
   - ledc_set_duty(channel, 0)
   - ledc_update_duty(channel)
4. WRITE to notification semaphore (from ISR):
   xSemaphoreGiveFromISR(estop_semaphore, &task_woken)
5. RETURN (no other actions in ISR)
```

**Critical ISR Rules:**
- NO blocking operations (no delays, no queue sends with timeout, no mutex operations).
- NO floating-point operations.
- NO function calls to non-IRAM functions (everything in ISR must be in IRAM).
- NO string formatting or logging in the ISR.
- Total ISR execution time must be <1ms.
- The ISR must be declared with `IRAM_ATTR` to ensure it resides in internal RAM.

**Deferred Handler (runs in safety_supervisor task):**
After the ISR completes, the deferred handler (triggered by the semaphore) performs:
1. Log safety event to NVS (event_type: ESTOP_TRIGGERED, severity: CRITICAL).
2. Set system safety state to SAFE_STATE.
3. Suspend all application tasks (Tier 4).
4. Notify Jetson via serial: `{"event":"estop","state":"safe","timestamp":<ms>}`.
5. Activate alarm buzzer pattern (3-beep repeating).
6. Activate red LED (solid).

### 2.5 Test Procedure

**Weekly Manual Test (Mandatory - Operator Responsible):**
1. With system in NORMAL operation mode.
2. Press kill switch (mushroom head).
3. **Verify:**
   - [ ] All actuators immediately deactivate (visual/audible confirmation).
   - [ ] System does NOT resume operation while kill switch is held.
   - [ ] Buzzer sounds alarm pattern.
   - [ ] Red LED illuminates.
4. Twist kill switch to release.
5. **Verify:**
   - [ ] System enters PROVISIONING state (does NOT auto-resume).
   - [ ] Manual re-engagement required to return to NORMAL.
6. Record in maintenance log: date, time, pass/fail, operator initials.

**Quarterly Instrumented Test (Technician Required):**
1. Connect oscilloscope CH1 to kill switch contact (monitor voltage break).
2. Connect oscilloscope CH2 to a primary actuator output GPIO.
3. Press kill switch.
4. **Measure and verify:**
   - [ ] Time from contact break to GPIO output change: **<100ms** (target: <10ms).
   - [ ] Actuator output transitions to safe-state value.
   - [ ] No actuator output remains in non-safe state.
5. Record oscilloscope capture for audit trail.

**Annual Comprehensive Test:**
1. Perform quarterly instrumented test (above).
2. Verify kill switch actuation force is within 22N-50N range (use force gauge).
3. Inspect kill switch contacts for wear, pitting, or discoloration.
4. Verify IP67 seal integrity (visual inspection).
5. Verify sense wire continuity and pull-up resistor value.
6. Replace kill switch if any parameter is out of specification or visual defect found.

### 2.6 Redundancy

The kill switch is the PRIMARY and PREFERRED safety mechanism. It is a physical, hardware-level power interrupt that operates independently of all software. However, the following redundancy exists:

| Primary Mechanism | Backup Mechanism | Detection | Response |
|-------------------|-----------------|-----------|----------|
| Kill switch (power interrupt) | Software watchdog → system reset | Kill switch sense GPIO stays HIGH while system runs | After 1.0s HWD timeout, full system reset. All outputs safe via pull-down resistors. |
| Kill switch (power interrupt) | E-Stop ISR (if power path separate) | GPIO interrupt on falling edge | ISR drives all outputs safe in <1ms. (Note: this is software-dependent and NOT the primary mechanism.) |

**IMPORTANT:** The software backup path is NOT a substitute for a functioning kill switch. If the kill switch is known to be faulty, the system must NOT be operated until the kill switch is repaired or replaced. The software backup exists only to mitigate the consequences of a kill switch failure that occurs DURING operation.

---

## 3. Watchdog Timer Specification

### 3.1 Hardware Watchdog (HWD)

**Purpose:** Provide an independent, software-independent reset mechanism. If the firmware becomes completely unresponsive (e.g., stuck in infinite loop with interrupts disabled, GPIO latch-up, flash corruption), the HWD will reset the processor.

**Component:** MAX6818 or equivalent supervisor IC.

| Parameter | Value | Notes |
|-----------|-------|-------|
| IC part number | MAX6818 (primary), TPS3823-33 (alternative) | Both are automotive-grade supervisors |
| Input voltage range | 2.5V - 5.5V | Powered from 3.3V rail |
| Timeout period | 1.0 seconds (fixed) | Not software-configurable |
| Watchdog input (WDI) | Connected to ESP32 GPIO (kick pin) | Must be toggled to prevent reset |
| Reset output (RST/WDO) | Connected to ESP32 EN (reset) pin | Active-low, open-drain |
| Reset pulse duration | 140ms minimum (MAX6818) | Ensures complete processor reset |
| Reset threshold (if used) | 2.93V | Below this, HWD also asserts reset (undervoltage protection) |

**Wiring:**
```
    ESP32 GPIO (kick) ────── MAX6818 WDI
    ESP32 EN (reset) ─────── MAX6818 RST/WDO (active-low)
    3.3V ────── MAX6818 VCC
    GND  ────── MAX6818 GND
```

**Kick Pattern Requirement:**
The WDI pin must be toggled (LOW → HIGH or HIGH → LOW) at least once every 1.0 seconds. The software watchdog task implements the following kick pattern:

```
Feed sequence: alternating 0x55 / 0xAA pattern
- Odd kicks: write GPIO LOW then HIGH (0x55 pattern)
- Even kicks: write GPIO HIGH then LOW (0xAA pattern)
```

**Rationale for alternating pattern:** If the firmware gets stuck with the GPIO pin held at a constant level (stuck-at-0 or stuck-at-1 fault), the WDI pin will stop toggling, and the HWD will timeout and reset the system. A simple periodic toggle would not detect this fault.

**Kick Interval:** 200ms (5x per second). This provides a comfortable margin below the 1.0s timeout while allowing the system to miss up to 4 consecutive kicks before a reset occurs.

### 3.2 Software Watchdog (SWD)

**Purpose:** Monitor the health of application tasks and the safety supervisor. If a task stops responding, the SWD escalates to the appropriate safety action (task restart, safe-state transition, or system reset via HWD timeout).

**Implementation:** FreeRTOS task (safety_watchdog_task).

| Parameter | Value | Notes |
|-----------|-------|-------|
| Task priority | configMAX_PRIORITIES - 2 (one below safety_supervisor) | High but not highest |
| Stack size | 1024 bytes | Minimal stack needed |
| Period | 100ms | Checks all monitored tasks every 100ms |
| HWD kick interval | 200ms | Feeds hardware WDT every 200ms |
| Task monitoring timeout | 1.0 seconds per task | If task doesn't check in within 1.0s, action taken |
| Escalation: task hung | Task suspended, safe-state for its actuators | Logged as HIGH severity |
| Escalation: supervisor hung | Stop feeding HWD → HWD resets system after 1.0s | Logged as CRITICAL severity |
| Escalation: 3+ tasks hung | Stop feeding HWD → system reset | Multiple task failures indicate systemic issue |

**Task Monitoring Mechanism:**
Each monitored task must call `safety_watchdog_checkin(task_id)` at least once every 1.0 seconds. If the SWD task detects that a task has not checked in within its timeout period:

1. First timeout: Log MEDIUM event, increment timeout counter for that task.
2. Second consecutive timeout: Log HIGH event, suspend the task, force its actuators to safe-state.
3. Third consecutive timeout (if task somehow resumes and hangs again): Escalate to system reset.
4. If safety_supervisor itself misses check-in: Immediately stop feeding HWD. HWD resets system within 1.0s.

**Feed Pattern Implementation:**
```c
// In safety_watchdog_task, called every 200ms:
static uint8_t kick_pattern = 0x55;

void watchdog_feed_hw(void) {
    // Alternate between 0x55 and 0xAA patterns to detect stuck-at faults
    if (kick_pattern == 0x55) {
        gpio_set_level(WDT_KICK_PIN, 0);
        ets_delay_us(10);
        gpio_set_level(WDT_KICK_PIN, 1);
        kick_pattern = 0xAA;
    } else {
        gpio_set_level(WDT_KICK_PIN, 1);
        ets_delay_us(10);
        gpio_set_level(WDT_KICK_PIN, 0);
        kick_pattern = 0x55;
    }
}
```

### 3.3 Recovery Procedure

**On Hardware WDT Reset (MAX6818 timeout):**
1. ESP32 resets (EN pin pulled low for ≥140ms).
2. Boot ROM executes, loads bootloader from flash.
3. Bootloader validates application partition (SHA-256 hash).
4. If valid: loads application. If invalid: loads recovery partition.
5. Application boots in PROVISIONING state (never auto-engages).
6. All GPIO outputs driven to safe-state as first action (SR-008).
7. NVS loaded (including last known safety events).
8. Safety event logged: `HWD_RESET` with timestamp.
9. Boot counter incremented in NVS.
10. If boot counter > 5 in last 10 minutes: enter FAULT mode, require manual reset.
11. System waits for Jetson connection and role assignment.
12. Normal operation only after explicit re-engagement command.

**On Software WDT Action (task suspension):**
1. Hung task is suspended via `vTaskSuspend()`.
2. All actuators owned by that task are driven to safe-state.
3. Safety event logged: `TASK_WATCHDOG_TIMEOUT` with task ID and timeout count.
4. Event sent to Jetson immediately.
5. System continues in DEGRADED mode (other tasks unaffected).
6. If the task can be safely restarted (determined by safety supervisor): restart after 5 seconds.
7. If task cannot be restarted: remain in DEGRADED mode until manual intervention or system reset.

---

## 4. Heartbeat Protocol

### 4.1 Protocol Specification

**Purpose:** Monitor the health of the Jetson companion computer. The Jetson is responsible for AI inference, high-level planning, and cloud connectivity. The ESP32 is responsible for real-time control and safety. The heartbeat ensures the ESP32 can detect Jetson failures and respond appropriately.

**Direction:** Jetson → ESP32 (Jetson sends, ESP32 monitors).

**Transport:** Dedicated UART serial link (UART1, 115200 baud, 8N1).

**Message Format:**
```
HB:<sequence_number>:<timestamp_ms>:<checksum>\n
```
- `HB` - Message type identifier (2 bytes)
- `:` - Separator (1 byte)
- `<sequence_number>` - Monotonically increasing 32-bit unsigned integer (1-10 digits)
- `:` - Separator (1 byte)
- `<timestamp_ms>` - Jetson uptime in milliseconds (13 digits)
- `:` - Separator (1 byte)
- `<checksum>` - XOR of all preceding bytes (2 hex digits)
- `\n` - Line terminator (1 byte)

**Example:** `HB:0000001234:0000012345678:A7\n`

**Timing:**
| Parameter | Value | Notes |
|-----------|-------|-------|
| Transmission interval | 100ms (10 Hz) | Jetson sends every 100ms ±10ms |
| Expected arrival window | 80-120ms between heartbeats | Allows for UART jitter |
| Degraded threshold | 5 consecutive missed (500ms) | Enter DEGRADED mode |
| Safe-state threshold | 10 consecutive missed (1000ms) | Enter SAFE_STATE mode |
| Resume requirement | 3 consecutive good heartbeats | Return to NORMAL mode |
| Sequence validation | Must be monotonically increasing | Detects duplicate/out-of-order |

### 4.2 State Machine

```
                    ┌──────────────┐
                    │   NORMAL     │
                    │  (Full ops)  │
                    └──────┬───────┘
                           │ 5 heartbeats missed (500ms)
                           ▼
                    ┌──────────────┐
              ┌────▶│  DEGRADED    │────┐
              │     │ (Reflex only)│    │ 5 more missed (1000ms total)
              │     └──────────────┘    ▼
              │                   ┌──────────────┐
              │                   │  SAFE_STATE  │
              │                   │ (All safe)   │
              │                   └──────┬───────┘
              │                          │ 3 consecutive good heartbeats
              │                          │ + Jetson sends RESUME command
              │                          ▼
              │                   ┌──────────────┐
              └───────────────────│  NORMAL      │
               (heartbeat resumes │  (Full ops)  │
                before safe-state)└──────────────┘
```

### 4.3 Mode Descriptions

**NORMAL Mode:**
- All system functions operational.
- Jetson sends commands, ESP32 executes.
- Reflexes, PID loops, AI inference all active.
- Cloud connectivity active (if configured).
- This is the standard operating mode.

**DEGRADED Mode (entered when 5 heartbeats missed):**
- Reflex loops continue operating (these are local to the ESP32 and don't depend on Jetson).
- PID loops continue with last known setpoint (or switch to safe hold if no setpoint available).
- AI inference disabled (Jetson is not responding).
- Cloud connectivity disabled (no Jetson = no MQTT).
- New commands from Jetson are rejected (connection is down).
- Alarm: single beep, amber LED solid.
- Log event: `HEARTBEAT_DEGRADED`, severity: HIGH.
- The system continues to function at a reduced capability level, ensuring basic safety.

**SAFE_STATE Mode (entered when 10 heartbeats missed):**
- ALL actuators driven to their defined safe-state values immediately.
- ALL control loops (PID, reflex) suspended.
- ALL outputs held at safe-state values.
- System waits indefinitely for Jetson reconnection.
- Alarm: 3-beep repeating, red LED solid.
- Log event: `HEARTBEAT_SAFE_STATE`, severity: CRITICAL.
- Event immediately sent to... nowhere (Jetson is down). Event logged to NVS.
- Manual intervention may be required if Jetson does not recover.

### 4.4 Reconnection Procedure

When the Jetson reconnects (3 consecutive good heartbeats received):

1. ESP32 logs event: `HEARTBEAT_RESTORED`, severity: MEDIUM.
2. ESP32 sends status to Jetson: `{"mode":"safe_state","reason":"heartbeat_loss","duration_ms":<elapsed>,"events_pending":<count>}`
3. Jetson sends `RESUME` command with optional mode override.
4. ESP32 validates RESUME command (checksum, sequence number).
5. ESP32 transitions from SAFE_STATE → DEGRADED (briefly) → NORMAL.
6. ESP32 re-enables control loops in a staged sequence:
   - T+0ms: Enable reflex loops.
   - T+100ms: Enable PID loops (ramp from safe-state to last setpoint over 1 second).
   - T+500ms: Enable AI inference (accept Jetson commands).
   - T+1000ms: Enable cloud connectivity.
7. ESP32 logs event: `OPERATION_RESUMED`, severity: MEDIUM.
8. Amber LED off, green LED on (if no other alarms active).

**IMPORTANT:** The system does NOT auto-resume to the previous operating state. The Jetson must explicitly send a RESUME command. If the Jetson reconnects but does not send RESUME within 10 seconds, the ESP32 logs a warning and remains in SAFE_STATE.

### 4.5 Heartbeat Implementation (ESP32 Side)

```c
#define HB_INTERVAL_MS          100     // Expected interval between heartbeats
#define HB_DEGRADED_THRESHOLD   5       // Missed heartbeats to enter DEGRADED
#define HB_SAFE_THRESHOLD       10      // Missed heartbeats to enter SAFE_STATE
#define HB_RESUME_THRESHOLD     3       // Good heartbeats to resume from SAFE_STATE

typedef enum {
    HEARTBEAT_MODE_NORMAL,
    HEARTBEAT_MODE_DEGRADED,
    HEARTBEAT_MODE_SAFE_STATE
} heartbeat_mode_t;

// Called every 100ms by heartbeat monitor task
void heartbeat_check(void) {
    static uint32_t last_good_hb_ms = 0;
    static uint8_t missed_count = 0;
    static uint8_t good_count = 0;
    static heartbeat_mode_t mode = HEARTBEAT_MODE_NORMAL;

    if (hb_received_this_period) {
        hb_received_this_period = false;
        missed_count = 0;
        good_count++;

        if (mode == HEARTBEAT_MODE_SAFE_STATE && good_count >= HB_RESUME_THRESHOLD) {
            // Request Jetson to send RESUME command
            send_to_jetson("{\"status\":\"heartbeat_restored\",\"awaiting_resume\":true}");
            // Do NOT auto-resume - wait for explicit RESUME command
        } else if (mode == HEARTBEAT_MODE_DEGRADED) {
            mode = HEARTBEAT_MODE_NORMAL;
            log_safety_event(SAFE_EVT_HB_RESTORED, MEDIUM);
            set_mode(MODE_NORMAL);
        }
        last_good_hb_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    } else {
        good_count = 0;
        missed_count++;

        if (mode == HEARTBEAT_MODE_NORMAL && missed_count >= HB_DEGRADED_THRESHOLD) {
            mode = HEARTBEAT_MODE_DEGRADED;
            log_safety_event(SAFE_EVT_HB_DEGRADED, HIGH);
            enter_degraded_mode();
        } else if (mode == HEARTBEAT_MODE_DEGRADED && missed_count >= HB_SAFE_THRESHOLD) {
            mode = HEARTBEAT_MODE_SAFE_STATE;
            log_safety_event(SAFE_EVT_HB_SAFE_STATE, CRITICAL);
            enter_safe_state();
        }
    }
}
```

---

## 5. Overcurrent Protection

### 5.1 Architecture

Overcurrent protection operates at two levels:

1. **Hardware Level (Tier 1):** Polyfuse (PTC) provides passive, non-resettable protection. Trips at a fixed current threshold. Self-resets after cooling.
2. **Software Level (Tier 2/3):** Active current monitoring via INA219 or ADC + shunt resistor. Provides fast, configurable, per-channel protection with event logging.

### 5.2 Current Monitoring Hardware

**Primary Method: INA219 Current Sensor**

| Parameter | Value | Notes |
|-----------|-------|-------|
| IC | INA219B (I2C, 26V, ±3.2A) | One per monitored channel or multiplexed |
| Shunt resistor | 0.1Ω, 1%, 2W | On-board or external |
| Resolution | 0.1mA (at ±3.2A range) | Sufficient for most actuator types |
| Sample rate | Up to 688 samples/second | Default: 100 SPS (10ms per reading) |
| I2C address | Configurable (0x40-0x4F) | Multiple devices on same bus |
| Alert pin | Connected to ESP32 GPIO (interrupt) | Triggers ISR on overcurrent |

**Alternative Method: ADC + Shunt Resistor**

| Parameter | Value | Notes |
|-----------|-------|-------|
| ADC | ESP32 internal ADC or ADS1115 (external, 16-bit) | ADS1115 recommended for accuracy |
| Shunt resistor | 0.01Ω, 1%, 5W (low-side) | Or 0.1Ω for higher gain |
| Differential measurement | Required | Measure voltage across shunt |
| Resolution | ~1mA (ADS1115) | Lower accuracy than INA219 but cheaper |

### 5.3 Overcurrent Detection Parameters

**Per-Channel Configuration:**

| Channel Type | Default Threshold | Response | Notes |
|-------------|-------------------|----------|-------|
| Solenoid (hydraulic) | 4000mA | Immediate disable | Based on existing marine config |
| Motor (PWM) | Configurable (default: 5A) | Immediate disable | 2x nominal motor current |
| Relay | 2A | Immediate disable | Based on relay coil rating |
| Servo | 1A | Immediate disable | RC servo stall current |
| General purpose | 500mA | Warning → disable at 2x | For LEDs, sensors, etc. |

**Detection Parameters:**
| Parameter | Value | Notes |
|-----------|-------|-------|
| Overcurrent threshold | Configurable per-pin (in safety config) | See actuator profiles |
| Detection window | 100ms | Sustained overcurrent for 100ms triggers action |
| Inrush current allowance | 200ms, 2x threshold | Allows motor/solenoid inrush current |
| Measurement averaging | 10 samples over 100ms | Prevents false triggers from noise |

### 5.4 Overcurrent Response Sequence

**When overcurrent is detected (sustained for 100ms beyond inrush period):**

1. **T+0ms:** ISR triggered (INA219 ALERT pin → GPIO interrupt).
2. **T+0ms:** ISR immediately sets the affected output GPIO to safe-state (LOW for most actuators).
3. **T+0ms:** ISR sets `oc_detected[channel] = true` volatile flag.
4. **T+1ms:** Deferred handler (from ISR semaphore):
   - Log safety event: `OVERCURRENT_DETECTED`, severity: CRITICAL.
   - Set error flag for the affected channel: `channel_error[channel] = ERR_OVERCURRENT`.
   - Disable the channel: `channel_enabled[channel] = false`.
   - Notify Jetson: `{"event":"overcurrent","channel":<id>,"current_ma":<value>,"action":"disabled"}`.
   - Activate alarm (if no other alarm active): buzzer 3-beep, red LED.
5. **T+100ms:** Verify current has dropped to safe level.
6. **Recovery:** Channel remains disabled until:
   - Operator manually clears the error via Jetson command or physical button.
   - System verifies current is below 50% of threshold.
   - A 1-second cooldown has elapsed since the event.
   - The channel is re-enabled with a soft-start ramp.

### 5.5 Hardware Backup: Polyfuse (PTC)

**Purpose:** Provide a passive, non-software-dependent overcurrent protection as a last resort if the active monitoring fails.

| Parameter | Specification |
|-----------|--------------|
| Type | PTC (Positive Temperature Coefficient) resettable fuse |
| Hold current | 1.5x nominal channel current |
| Trip current | 2.0x nominal channel current |
| Max voltage | ≥ 2x supply voltage |
| Trip time | <5s at 2x hold current |
| Reset time | <30s (after power removed and fault cleared) |
| Placement | In series with each actuator power output, before the MOSFET/driver |
| Part example (5A channel) | Bourns MF-R500 (hold 5A, trip 10A) |
| Part example (2A channel) | Bourns MF-R200 (hold 2A, trip 4A) |

---

## 6. Solenoid/Relay Timeout

### 6.1 Purpose

Solenoids and relays contain inductive coils that generate heat during continuous activation. Prolonged activation beyond the rated duty cycle can cause:
- Coil overheating and insulation breakdown.
- Permanent coil damage (short or open circuit).
- Fire hazard in extreme cases.

The timeout system automatically deactivates solenoids/relays after a maximum continuous activation period, regardless of the commanding software.

### 6.2 Parameters

| Parameter | Default Value | Configurable | Notes |
|-----------|---------------|--------------|-------|
| max_on_time_ms | 5000 | Yes, per-output | Maximum continuous activation time |
| cooldown_time_ms | 1000 | Yes, per-output | Minimum off-time after automatic deactivation |
| min_on_time_ms | 50 | Yes, per-output | Minimum on-time (prevents relay chattering) |
| min_off_time_ms | 200 | Yes, per-output | Minimum off-time between activations |
| rate_limit_cycles_per_10s | 5 | Yes, per-output | Maximum activation cycles in 10 seconds |

### 6.3 Timeout Implementation

```c
typedef struct {
    uint32_t on_start_ms;        // Timestamp when output was turned ON
    uint32_t last_off_ms;        // Timestamp when output was last turned OFF
    uint32_t cycle_count;        // Number of ON cycles in current window
    uint32_t cycle_window_ms;    // Start of current rate-limiting window
    bool auto_deactivated;       // True if last deactivation was automatic
} solenoid_timeout_t;

// Called every 10ms by safety supervisor task
void solenoid_timeout_check(uint8_t channel) {
    if (solenoid_state[channel] == ON) {
        uint32_t elapsed = xTaskGetTickCount() * portTICK_PERIOD_MS - solenoid_timeout[channel].on_start_ms;

        if (elapsed >= solenoid_config[channel].max_on_time_ms) {
            // AUTOMATIC DEACTIVATION
            set_output(channel, OFF);
            solenoid_timeout[channel].auto_deactivated = true;
            solenoid_timeout[channel].last_off_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
            log_safety_event(SAFE_EVT_SOLENOID_TIMEOUT, HIGH,
                           "channel=%d, on_duration_ms=%lu", channel, elapsed);
            notify_jetson("{\"event\":\"solenoid_timeout\",\"channel\":%d,\"duration_ms\":%lu}",
                         channel, elapsed);
        }
    }

    // Cooldown enforcement
    if (solenoid_timeout[channel].auto_deactivated) {
        uint32_t off_elapsed = xTaskGetTickCount() * portTICK_PERIOD_MS - solenoid_timeout[channel].last_off_ms;
        if (off_elapsed < solenoid_config[channel].cooldown_time_ms) {
            // Block any activation attempt
            if (pending_command[channel] == ON) {
                pending_command[channel] = BLOCKED;
            }
        } else {
            solenoid_timeout[channel].auto_deactivated = false;
        }
    }

    // Rate limiting
    uint32_t window_elapsed = xTaskGetTickCount() * portTICK_PERIOD_MS - solenoid_timeout[channel].cycle_window_ms;
    if (window_elapsed >= 10000) {
        solenoid_timeout[channel].cycle_count = 0;
        solenoid_timeout[channel].cycle_window_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    }
}
```

### 6.4 Override Protection

- The timeout system operates at Tier 2/3 level.
- Application code (Tier 4) CANNOT override, disable, or extend the timeout.
- Only the safety supervisor task may modify timeout parameters, and only during initialization (not during runtime).
- If the safety supervisor detects that an application task is attempting to repeatedly activate a solenoid that is in cooldown, it will:
  1. Log the attempt as a safety event (severity: MEDIUM).
  2. Ignore the activation command.
  3. If more than 10 blocked attempts in 1 second: suspend the offending task.

### 6.5 Per-Output Independence

Each solenoid/relay output has independent timeout tracking:
- Independent `on_start_ms` timestamps.
- Independent `cooldown` enforcement.
- Independent `cycle_count` and `cycle_window`.
- One output timing out does NOT affect other outputs.

---

## 7. Boot Safety Sequence

### 7.1 Exact Timing Specification

The boot sequence is a hard real-time sequence. Every step must complete within its allocated time budget. If any step fails, the system enters PROVISIONING state and waits for manual intervention.

```
Time    Action                                    Dependency         Failure Action
─────   ──────────────────────────────────────    ───────────────    ─────────────────
T+0ms   POWER-ON                                  N/A                N/A
        - ESP32 exits reset
        - Internal pull-ups/pull-downs active
        - ALL GPIO outputs driven LOW (safe state)
        - No peripheral initialization yet
        - No code execution yet (ROM bootloader)

T+1ms   NVS INIT                                  Power stable       FAULT: blink red LED 5x
        - nvs_flash_init()                                            Enter PROVISIONING
        - Load cached config from NVS key "config"
        - Validate config checksum (CRC-32)
        - Load safety policy from NVS key "safety"
        - Load last known safety events (for diagnostics)

T+5ms   WATCHDOG INIT                             NVS loaded         FAULT: blink red LED 4x
        - esp_task_wdt_init()                                         Enter PROVISIONING
        - MAX6818 hardware WDT acknowledged (GPIO init for kick pin)
        - Start safety_watchdog_task
        - First HWD kick within 200ms of this step

T+10ms  SERIAL PROTOCOL INIT                      WDT running        FAULT: blink red LED 3x
        - UART0 (debug): 115200 baud                                  Enter PROVISIONING
        - UART1 (Jetson heartbeat): 115200 baud
        - UART2 (NEXUSLink): 921600 baud
        - Serial protocol handlers registered

T+20ms  DEVICE IDENTITY BROADCAST                 Serial ready       N/A (best-effort)
        - Send device ID, firmware version, capabilities
        - Format: "NEXUS:<device_id>:<fw_version>:<capabilities>\n"
        - Sent on all serial ports simultaneously

T+50ms  WAIT FOR JETSON ROLE ASSIGNMENT           Identity sent      TIMEOUT: load cached
        - Wait up to 50ms for Jetson to assign role                  role from NVS
        - If role received: proceed with assigned role
        - If timeout: load last known role from NVS cache
        - Log which path was taken

T+100ms CONFIGURE I/O PER ROLE                    Role known         FAULT: blink red LED 2x
        - Set GPIO modes per role config                             Enter PROVISIONING
        - Configure PWM channels (LEDC)
        - Configure ADC channels
        - Configure I2C peripherals
        - Initialize INA219 current sensors
        - Verify all pin assignments are within role bounds

T+200ms LOAD REFLEXES                             I/O configured     FAULT: blink red LED 1x
        - Load reflex definitions from NVS/config                     Enter PROVISIONING
        - Validate reflex syntax and safety compliance
        - Register reflex triggers
        - Reflexes are loaded but NOT yet active

T+300ms RUN SELFTEST SEQUENCE                     Reflexes loaded    FAIL: Enter PROVISIONING
        - GPIO continuity test (output → input loopback)
        - Current sensor calibration verification
        - Kill switch circuit test (verify NC state)
        - Memory integrity check (stack canary, heap)
        - Watchdog test (briefly delay, verify WDT doesn't trigger)
        - Serial link test (echo test with Jetson)

T+500ms ENTER NORMAL OPERATION                    Selftest PASS      N/A
        - Set system state to NORMAL
        - Enable reflex execution
        - Enable control loops (if Jetson heartbeat present)
        - Activate green status LED
        - Log boot complete event to NVS
```

### 7.2 Output Safe-State Guarantee

**CRITICAL REQUIREMENT:** All actuator outputs MUST remain in their safe-state value from T+0ms until the selftest sequence passes at T+300ms. No actuator may be activated before T+500ms under ANY circumstances.

**Enforcement:**
1. At T+0ms: Hardware pull-down resistors (10KΩ) ensure all MOSFET gates are LOW. All PWM channels are disabled by default after reset.
2. At T+1ms: Firmware explicitly drives all actuator-capable GPIOs LOW as the first code action.
3. At T+100ms: I/O configuration sets all actuator outputs to their defined safe-state values from the safety policy.
4. At T+300ms: Selftest verifies all outputs are at safe-state values. If any output is not at safe-state, selftest FAILS.
5. At T+500ms: Only after explicit confirmation that selftest passed are control loops and reflex outputs enabled.

### 7.3 Boot Failure Handling

If ANY step fails before T+500ms:
1. System enters PROVISIONING state (not NORMAL, not DEGRADED).
2. All outputs held at safe-state.
3. Red LED blinks a pattern indicating the failed step (see table above).
4. Debug information printed to UART0.
5. System waits indefinitely for manual intervention (re-flash, config fix, etc.).
6. Watchdog remains active (system will reset if watchdog task hangs).

---

## 8. Failsafe State Definitions

### 8.1 Per-Actuator-Type Safe States

Every actuator type has a defined safe-state value. This is the value that the actuator is driven to during any failsafe condition (E-Stop, heartbeat loss, watchdog timeout, boot, etc.).

| Actuator Type | Safe-State Value | Physical Meaning | Safety Rationale |
|--------------|-----------------|------------------|------------------|
| **Servo** | 1500µs pulse (center) | Servo at center/neutral position | Center position minimizes risk of collision or uncontrolled motion |
| **Relay** | OPEN (de-energized) | Relay contact open, no current flow | Removes power from downstream device. Most loads are safe when de-energized. |
| **Motor/PWM** | 0% duty cycle | Motor stopped, no torque | Stopped motor cannot cause motion. This is always the safest state. |
| **Solenoid** | DE-ENERGIZED | Solenoid de-energized, spring return | Spring-return mechanism moves valve to default (safe) position. |
| **LED** | OFF | LED not illuminated | LEDs are indicators only; OFF is the neutral state. |
| **Buzzer** | OFF | Buzzer silent | Reduces noise stress. Hearing protection per IEC 60945. |

### 8.2 Per-Instance Override

Individual actuator instances may override the default safe-state value, but ONLY with a documented safety engineering justification:

```json
{
  "actuator_id": "rudder_servo",
  "type": "servo",
  "safe_state_override": {
    "pulse_us": 1500,
    "justification": "Center position. Mechanical stops at ±35°. Center is equidistant from both stops."
  },
  "override_approved_by": "safety_engineer",
  "override_date": "2025-01-15"
}
```

**Rules for safe-state overrides:**
1. The safe-state must be between the actuator's minimum and maximum limits.
2. The safe-state must not cause any downstream hazard (verified by safety analysis).
3. Override requires explicit safety engineer approval (digital signature in config).
4. Override is logged in the safety event log on every boot.
5. The system may NOT boot if the override is not approved.

### 8.3 Domain-Specific Safe States

Some domains may require different safe-state values based on operational context:

| Domain | Actuator | Override Safe-State | Reason |
|--------|----------|-------------------|--------|
| Marine | Rudder servo | 1500µs (center) | Center rudder = straight ahead = minimal turning force |
| Marine | Throttle motor | 0% duty | Zero throttle = no propulsion |
| Agriculture | Spray relay | OPEN | Stop spraying immediately on any fault |
| Agriculture | Drive motor | 0% duty | Stop vehicle immediately |
| HVAC | Heating relay | OPEN | Stop heating (overheat prevention) |
| HVAC | Cooling relay | OPEN | Stop cooling (freeze prevention) |
| Factory | Robot motor | 0% duty | Stop all robot motion immediately |
| Mining | Ventilation fan | MUST NOT STOP | Mining ventilation requires continuous operation. Override safe-state = ON (last speed). This is a CRITICAL exception requiring additional safety analysis. |

### 8.4 Safe-State Transition Timing

| Actuator Type | Max Time to Reach Safe-State | Method |
|--------------|------------------------------|--------|
| Relay/Solenoid | <5ms | Direct GPIO LOW (de-energize) |
| Servo | <50ms | PWM pulse to center position, servo servo-mechanism responds |
| Motor/PWM | <10ms | Duty cycle → 0%, motor coasts to stop (external braking may apply) |
| LED | <1ms | Direct GPIO LOW |
| Buzzer | <1ms | Direct GPIO LOW or PWM duty → 0% |

---

## 9. Safety Event Logging

### 9.1 Storage Architecture

**Primary Storage:** NVS (Non-Volatile Storage) on ESP32 internal flash.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Storage type | NVS namespace "safety_events" | Survives power loss and firmware updates |
| Buffer type | Circular buffer | Overwrites oldest events when full |
| Buffer capacity | 100 events | Each event ≈ 128 bytes, total ≈ 12.5KB |
| Key format | "evt_000" to "evt_099" | Fixed-length keys for fast access |
| Write endurance | NVS handles wear leveling | ESP-IDF NVS abstraction |
| Persistence | Survives power loss, firmware updates | Only factory reset clears events |

**Secondary Storage (Jetson):**
- Critical events (severity: CRITICAL, HIGH) are immediately sent to the Jetson.
- Jetson stores events in a local SQLite database.
- Jetson periodically syncs events to cloud storage (if connected).

### 9.2 Event Record Format

Each safety event is stored as a structured record with the following fields:

```c
typedef struct {
    uint32_t timestamp_ms;        // System uptime in milliseconds (32-bit, wraps at ~49 days)
    uint64_t timestamp_epoch_ms;  // Unix epoch in milliseconds (if RTC available, else 0)
    uint8_t  event_type;          // Event category (see table below)
    uint8_t  severity;            // CRITICAL=3, HIGH=2, MEDIUM=1, LOW=0
    uint16_t triggering_condition; // Specific condition that triggered the event
    uint8_t  current_mode;        // System mode at time of event (NORMAL/DEGRADED/SAFE/PROVISIONING)
    uint8_t  action_taken;        // What the safety system did in response
    int32_t  additional_data;     // Optional: sensor value, current reading, etc.
    char     description[48];     // Human-readable description (null-terminated)
} safety_event_t;                 // Total: ~72 bytes
```

**JSON representation (for Jetson transmission and human readability):**
```json
{
  "timestamp_ms": 1234567890,
  "timestamp_iso": "2025-01-15T10:30:45.123Z",
  "event_type": "OVERCURRENT_DETECTED",
  "severity": "CRITICAL",
  "triggering_condition": "channel_3_current_exceeded_4000mA",
  "current_mode": "NORMAL",
  "action_taken": "channel_disabled_output_safe",
  "additional_data": {"channel": 3, "current_ma": 4521},
  "description": "Overcurrent on channel 3: 4521mA > 4000mA threshold"
}
```

### 9.3 Event Types

| Event Type Code | Name | Default Severity | Description |
|----------------|------|-----------------|-------------|
| 0x01 | ESTOP_TRIGGERED | CRITICAL | Emergency kill switch activated |
| 0x02 | HWD_RESET | CRITICAL | Hardware watchdog triggered system reset |
| 0x03 | SWD_RESET | HIGH | Software watchdog triggered action |
| 0x04 | TASK_TIMEOUT | HIGH | Application task failed to check in |
| 0x05 | HEARTBEAT_DEGRADED | HIGH | Jetson heartbeat missed, entered degraded mode |
| 0x06 | HEARTBEAT_SAFE_STATE | CRITICAL | Jetson heartbeat lost, entered safe-state mode |
| 0x07 | HEARTBEAT_RESTORED | MEDIUM | Jetson heartbeat restored |
| 0x08 | OVERCURRENT_DETECTED | CRITICAL | Overcurrent detected on a monitored channel |
| 0x09 | UNDERCURRENT_DETECTED | HIGH | Current below expected (possible open circuit) |
| 0x0A | SOLENOID_TIMEOUT | HIGH | Solenoid/relay exceeded max on-time |
| 0x0B | SENSOR_STALE | MEDIUM | Sensor data exceeded staleness timeout |
| 0x0C | SENSOR_OUT_OF_RANGE | MEDIUM | Sensor reading outside valid range |
| 0x0D | SENSOR_CRC_ERROR | HIGH | Sensor communication CRC failure |
| 0x0E | VOLTAGE_UNDER | HIGH | Supply voltage below threshold |
| 0x0F | VOLTAGE_OVER | HIGH | Supply voltage above threshold |
| 0x10 | TEMPERATURE_HIGH | MEDIUM | Component temperature above warning |
| 0x11 | MEMORY_LOW | MEDIUM | Free heap memory below threshold |
| 0x12 | CONFIG_LOAD_FAILED | HIGH | Failed to load configuration from NVS |
| 0x13 | SELFTEST_FAILED | HIGH | Boot selftest failed |
| 0x14 | SELFTEST_PASSED | LOW | Boot selftest passed |
| 0x15 | BOOT_COMPLETE | LOW | System boot completed successfully |
| 0x16 | MODE_CHANGE | LOW | System operating mode changed |
| 0x17 | OPERATIONAL_RESUMED | MEDIUM | Operation resumed after safe-state |
| 0x18 | RATE_LIMIT_EXCEEDED | MEDIUM | Actuator command exceeded rate limit (clamped) |
| 0x19 | DIVISION_BY_ZERO | MEDIUM | Division by zero detected and prevented |
| 0x1A | WATCHDOG_DISABLE_ATTEMPT | CRITICAL | Code attempted to disable watchdog (SR-006 violation) |
| 0x1B | REFLEX_ITERATION_LIMIT | MEDIUM | Reflex loop hit iteration limit |
| 0x1C | ACTUATOR_ENABLE_VIOLATION | CRITICAL | Actuator activated without enable signal (SR-001 violation) |

### 9.4 Event Severity Summary

| Severity | Response | Logged to NVS | Sent to Jetson | Sent to Cloud | Requires ACK |
|----------|----------|---------------|----------------|---------------|-------------|
| CRITICAL | Immediate safe-state | Yes (immediately) | Yes (immediately) | Yes (when available) | Yes (operator) |
| HIGH | Subsystem safe-state | Yes (immediately) | Yes (immediately) | Yes (when available) | Yes (operator) |
| MEDIUM | Degraded operation | Yes | Yes (next heartbeat) | Yes (periodic sync) | No |
| LOW | Informational | Yes | No | No | No |

### 9.5 Event Retrieval

Events can be retrieved via:
1. **Serial command:** `EVENTS:GET:<count>:<offset>` → returns last `<count>` events starting from `<offset>`.
2. **Jetson API:** `safety_get_events(count, offset, severity_filter)` → returns JSON array.
3. **Direct NVS read:** `nvs_get_blob(safety_handle, "evt_099", &event, sizeof(event))` → raw binary.

---

## 10. Safety Certification Checklist

### 10.1 Safety Integrity Levels (SIL) Mapping

The NEXUS platform targets **IEC 61508 SIL 1** for the safety controller (ESP32-based safety functions) and **SIL 2** for the hardware safety interlock (kill switch, HWD). The following checklist maps each safety function to its target SIL and specifies the required test procedures.

### 10.2 SIL 2 Requirements (Hardware Interlocks)

These requirements apply to Tier 1 (Hardware Interlock) components.

| ID | Requirement | Test Method | Frequency | Acceptance Criteria |
|----|------------|-------------|-----------|-------------------|
| HW-01 | Kill switch interrupts actuator power within 1ms | Oscilloscope measurement | Quarterly | Time from contact break to voltage drop on actuator rail: <1ms |
| HW-02 | Kill switch contact resistance <100mΩ (new) | Micro-ohmmeter | Annual | <100mΩ for new switch, <500mΩ for in-service |
| HW-03 | Kill switch mechanical life >100,000 operations | Accelerated life test (type test) | Once (type approval) | No contact welding or intermittent behavior |
| HW-04 | Kill switch IP67 rating maintained | Visual inspection + spray test | Annual | No moisture ingress after spray test per IEC 60529 |
| HW-05 | HWD (MAX6818) triggers reset within 1.1s of timeout | Logic analyzer | Monthly | Reset pulse within 1.0s ±100ms of last kick |
| HW-06 | HWD reset pulse duration ≥140ms | Oscilloscope | Monthly | RST pin LOW for ≥140ms |
| HW-07 | Polyfuse trips at rated current ±20% | Controlled current source | Annual | Trip between 1.6x and 2.4x hold current |
| HW-08 | Flyback diode clamping voltage within spec | Oscilloscope with inductive load | Annual | Clamp voltage < rated diode voltage + 2V |
| HW-09 | Pull-down resistors functional (10KΩ ±10%) | Multimeter | Annual | 9.0KΩ - 11.0KΩ |
| HW-10 | Kill switch sense wire continuity | Continuity test | Monthly | <1Ω end-to-end |

### 10.3 SIL 1 Requirements (Firmware Safety Functions)

These requirements apply to Tier 2 (Firmware Safety Guard) and Tier 3 (Supervisory Task).

| ID | Requirement | Test Method | Frequency | Acceptance Criteria |
|----|------------|-------------|-----------|-------------------|
| FW-01 | E-Stop ISR responds within 1.1ms of GPIO edge | Oscilloscope: GPIO edge to actuator output change | Every firmware release | <1.1ms for all configured actuators |
| FW-02 | All outputs at safe-state within 10ms of E-Stop | Oscilloscope: all actuator outputs monitored | Every firmware release | Every output at safe-state within 10ms |
| FW-03 | Watchdog timeout triggers safe-state or reset | Inject fault (disable WDT feed in test mode) | Every firmware release | System enters safe-state or resets within 2.0s |
| FW-04 | Heartbeat loss triggers degraded mode within 510ms | Disconnect Jetson serial, observe mode transition | Every firmware release | DEGRADED mode entered within 510ms |
| FW-05 | Heartbeat loss triggers safe-state within 1010ms | Continue disconnect from FW-04 | Every firmware release | SAFE_STATE mode entered within 1010ms |
| FW-06 | Overcurrent detection and response within 5ms | Inject overcurrent via programmable load | Every firmware release | Output disabled within 5ms of threshold crossing |
| FW-07 | Solenoid timeout deactivates within 20ms of expiry | Timer measurement | Every firmware release | Output OFF within max_on_time_ms + 20ms |
| FW-08 | All outputs LOW on boot (before any config loaded) | Power cycle with oscilloscope monitoring | Every firmware release | All outputs LOW within 5ms of power-on |
| FW-09 | Rate limiting prevents instantaneous actuator transitions | Step command test | Every firmware release | Output transitions comply with configured rate limit |
| FW-10 | No single sensor failure causes unsafe actuation | Fault injection: disconnect each sensor in turn | Every firmware release | System enters degraded/safe-state, no unsafe actuation |
| FW-11 | Division-by-zero protection functional | Inject zero denominator inputs | Every firmware release | No crash, no NaN output, safe default used |
| FW-12 | Reflex loop bounded iteration | Reflex with stuck condition | Every firmware release | Loop exits within MAX_REFLEX_ITERATIONS |
| FW-13 | Safety event logging captures all events | Trigger each event type, verify NVS storage | Every firmware release | All events present in NVS, correct format |
| FW-14 | Boot selftest detects common faults | Inject faults (GPIO stuck, sensor disconnected) | Every firmware release | Selftest FAILS correctly for each injected fault |
| FW-15 | Watchdog cannot be disabled by application code | Static analysis (SR-006) + runtime attempt | Every firmware release | No code path disables WDT. Runtime attempt blocked. |

### 10.4 SIL 1 Requirements (Application Control)

These requirements apply to Tier 4 (Application Control) and verify that application-level safety constraints are correctly implemented.

| ID | Requirement | Test Method | Frequency | Acceptance Criteria |
|----|------------|-------------|-----------|-------------------|
| APP-01 | PID control loop completes within deadline | Logic analyzer: task period measurement | Every firmware release | Worst-case period < 50ms |
| APP-02 | Reflex execution completes within deadline | Logic analyzer: trigger to response | Every firmware release | Worst-case reflex time < 20ms |
| APP-03 | Anti-windup prevents integral term overflow | Sustained error test (60s) | Every firmware release | No overshoot >5% after error removal |
| APP-04 | Actuator enable gate enforced (SR-001) | Static analysis + runtime test | Every firmware release | No actuation without enable signal |
| APP-05 | Safe-state bounds enforced on all outputs | Command actuator beyond limits | Every firmware release | Output clamped to safe range |
| APP-06 | Configuration validation blocks invalid configs | Deploy invalid config (missing safe-state) | Every firmware release | Deployment blocked with clear error |
| APP-07 | Memory budget not exceeded | Build output analysis | Every firmware build | Flash <80%, heap >32KB free |
| APP-08 | Code coverage meets requirements | Coverage analysis with test suite | Every firmware release | Safety-critical: 100% line, 95% branch |

### 10.5 Environmental and EMC Tests

| ID | Requirement | Test Method | Frequency | Acceptance Criteria |
|----|------------|-------------|-----------|-------------------|
| ENV-01 | Operating temperature range: -20°C to +60°C | Environmental chamber | Type test | All safety functions operate within spec |
| ENV-02 | Storage temperature range: -40°C to +85°C | Environmental chamber | Type test | No permanent damage, full recovery |
| ENV-03 | Humidity: 95% RH non-condensing | Humidity chamber | Type test | No corrosion, no insulation breakdown |
| ENV-04 | Vibration: per IEC 60945 | Vibration table | Type test | No loose connections, no cracked solder joints |
| ENV-05 | ESD immunity: ±8kV contact, ±15kV air | ESD gun per IEC 61000-4-2 | Type test | No safety function disruption, self-recovery |
| ENV-06 | EMI susceptibility: per IEC 60945 | EMC chamber | Type test | No false safety triggers from EMI |
| ENV-07 | Power supply transient: per IEC 60945 | Power supply tester | Type test | Safe-state maintained during transients |
| ENV-08 | Salt spray (marine only): 48h per IEC 60068-2-11 | Salt spray chamber | Type test | Kill switch and connectors operational after test |

### 10.6 Documentation Requirements

For each safety level, the following documentation must be maintained and kept up-to-date:

**SIL 2 (Hardware Interlocks):**
- [ ] Hardware safety requirements specification (this document, Sections 1.2, 2, 3.1, 5.2, 5.5)
- [ ] Hardware design schematic with safety circuits highlighted
- [ ] Bill of materials with safety-critical components identified
- [ ] Hardware FMEA (Section 1.2)
- [ ] Hardware test reports (HW-01 through HW-10)
- [ ] Component certificates (MAX6818 datasheet, kill switch datasheet, polyfuse datasheet)
- [ ] PCB layout review (safety circuit isolation verified)
- [ ] Wiring diagrams (kill switch wiring per Section 2.2)

**SIL 1 (Firmware Safety Functions):**
- [ ] Software safety requirements specification (this document, Sections 1.3-1.5, 3.2, 4, 6, 7, 8, 9)
- [ ] Software architecture document with safety tasks identified
- [ ] Software FMEA (Sections 1.3-1.5)
- [ ] Source code with safety-critical sections annotated
- [ ] Static analysis reports (SR-001 through SR-010)
- [ ] Test reports (FW-01 through FW-15)
- [ ] Code coverage reports (APP-08)
- [ ] Safety policy validation report (safety_policy.json checks)
- [ ] Simulation test reports (fault injection scenarios)

**SIL 1 (Application Control):**
- [ ] Application requirements specification (per domain)
- [ ] Control algorithm documentation (PID tuning, reflex definitions)
- [ ] Test reports (APP-01 through APP-08)
- [ ] Configuration validation reports
- [ ] Memory budget reports

### 10.7 Certification Sign-Off

This safety specification requires sign-off from the following roles before the system may be deployed in a safety-critical application:

| Role | Responsibility | Sign-Off Required |
|------|---------------|-------------------|
| Safety Engineer (Author) | Specification correctness and completeness | Required |
| Safety Engineer (Reviewer) | Independent review of all safety requirements | Required |
| Hardware Engineer | Hardware implementation meets safety specifications | Required |
| Firmware Engineer | Firmware implementation meets safety specifications | Required |
| Test Engineer | All test procedures executed and passed | Required |
| Project Manager | Resource allocation and schedule for safety activities | Required |
| Domain Expert | Domain-specific safety rules are appropriate | Required (if domain-specific deployment) |
| Quality Manager | All documentation complete and auditable | Required (before production release) |

---

## Appendix A: Acronyms

| Acronym | Definition |
|---------|-----------|
| ADC | Analog-to-Digital Converter |
| ASIL | Automotive Safety Integrity Level |
| ESP32 | Espressif Systems ESP32 microcontroller |
| E-Stop | Emergency Stop |
| FMEA | Failure Mode and Effects Analysis |
| GPIO | General Purpose Input/Output |
| HWD | Hardware Watchdog |
| ISR | Interrupt Service Routine |
| IEC | International Electrotechnical Commission |
| INA219 | Texas Instruments current/voltage sensor IC |
| LED | Light Emitting Diode |
| MAX6818 | Maxim Integrated supervisor/watchdog IC |
| NC | Normally Closed (contact) |
| NVS | Non-Volatile Storage |
| PCB | Printed Circuit Board |
| PID | Proportional-Integral-Derivative (controller) |
| PTC | Positive Temperature Coefficient (fuse) |
| PWM | Pulse Width Modulation |
| SIL | Safety Integrity Level |
| SWD | Software Watchdog |
| TVS | Transient Voltage Suppressor |
| UART | Universal Asynchronous Receiver-Transmitter |
| WDT | Watchdog Timer |
| WDI | Watchdog Input |

## Appendix B: Referenced Standards

| Standard | Title | Relevance |
|----------|-------|-----------|
| IEC 61508 | Functional Safety of Electrical/Electronic Systems | Overall safety lifecycle and SIL definitions |
| ISO 26262 | Road Vehicles - Functional Safety | ASIL definitions (for factory/robotics domains) |
| IEC 60945 | Maritime Navigation and Radiocommunication Equipment | Marine environmental and safety requirements |
| ABYC A-33 | Diesel Engine Shutdown Systems | Marine kill switch and shutdown requirements |
| ISO 13850 | Safety of Machinery - Emergency Stop | Kill switch physical requirements |
| ISO 10218-1 | Robots and Robotic Devices - Safety | Factory/robotics safety requirements |
| ISO/TS 15066 | Collaborative Robot Safety | Human-robot collaboration safety |
| IEC 60529 | Degrees of Protection (IP Code) | Ingress protection for enclosures |
| IEC 61000-4-2 | EMC - Electrostatic Discharge | ESD immunity testing |
| ASHRAE 135 | BACnet Protocol | HVAC control system standard |
| IEC 60947-5-1 | Low-Voltage Switchgear - Control Devices | Relay and contactor requirements |

## Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-06-01 | NEXUS Safety Team | Initial release |
| 1.1.0 | 2024-09-15 | NEXUS Safety Team | Added heartbeat protocol, refined boot sequence |
| 2.0.0 | 2025-01-15 | NEXUS Safety Team | Major revision: added four-tier architecture, expanded certification checklist, added safety_policy.json companion document, added domain-specific rules, added overcurrent protection, comprehensive FMEA |
