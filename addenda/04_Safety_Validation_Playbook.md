# Safety Validation Playbook — Four-Tier Verification

**Document ID:** NEXUS-SVP-004
**Applicable Standard:** IEC 61508 SIL 1
**Platform:** NEXUS Robotics Platform (ESP32-S3 + Jetson Orin Nano Super)
**Revision:** 1.0

---

## How to Use This Playbook

This document defines every safety test that MUST pass before the NEXUS system can be declared operational. Tests are organized by safety tier, mirroring the platform's four-tier defense-in-depth architecture. No test may be skipped, waived, or marked as "not applicable" without written approval from the safety review board.

Each test specifies:
- **Objective** — What hazard is being mitigated.
- **Equipment** — Required instruments and test apparatus.
- **Procedure** — Step-by-step instructions. Steps numbered sequentially.
- **Pass Criteria** — Quantitative thresholds. "Shall" language denotes mandatory requirements.
- **Common Failure Causes** — Known pitfalls from integration testing.

Tests are prioritized by tier. Tier 1 (hardware interlock) is the last line of defense; failure here is a **CRITICAL** finding that blocks all further testing. Tier 2 failures are **HIGH** severity. Tier 3 failures are **MEDIUM**. Tier 4 failures are **LOW** but must still be resolved before release.

All test results shall be recorded in the Safety Test Log (NEXUS-STL-004) with timestamp, tester ID, measured values, and pass/fail determination.

---

## 1. Tier 1: Hardware Interlock Tests

Tier 1 tests verify the physical, non-software safety mechanisms. These tests require no firmware beyond basic power-on. They must pass even if the ESP32 is removed from the board entirely.

### Test 1.1: Kill Switch Power Interruption

**Objective:** Verify the kill switch physically interrupts power to all actuators regardless of software state, MCU health, or firmware version.

**Equipment:**
- Digital multimeter (DMM) with min/max hold
- Kill switch assembly (rated NC contact)
- 12V DC power supply (3A minimum)
- Resistive load bank simulating actuator current draw (2A nominal)
- Oscilloscope (optional, for timing verification at 1ms resolution)

**Procedure:**
1. Wire the 12V supply through the kill switch NC (normally closed) contacts to the actuator power rail on the PCB.
2. Connect the resistive load bank across the actuator power rail and ground.
3. Apply power. Verify nominal voltage (12V) and current draw on the actuator rail.
4. With the system fully powered and load drawing current, press and hold the kill switch.
5. Using the oscilloscope (or DMM min/max), measure the voltage on the actuator power rail. Record the value.
6. Measure current through the load bank. Record the value.
7. Release the kill switch. Observe whether actuators resume operation.
8. Repeat steps 4-7 five times to confirm repeatability.

**Pass Criteria:**
- Actuator rail voltage shall be 0V within 1ms of switch activation.
- Actuator current shall be 0A within 1ms of switch activation.
- System shall NOT resume automatically after switch release under any condition.
- All five repetitions shall pass.

**Common Failure Causes:**
- Kill switch wired in parallel with power path instead of in series.
- Fuse placed upstream of kill switch (fuse opens but kill switch bypass still conducts).
- Kill switch contacts rated for signal current only, not power current (contacts weld).
- Relay or contactor used without flyback diode (contact arcing, slow release).

### Test 1.2: Kill Switch Sense Wire Fail-Safe

**Objective:** Verify that a broken or disconnected sense wire defaults to the "kill switch activated" safe state, preventing the system from interpreting an open circuit as "switch released / system OK."

**Equipment:**
- Digital multimeter
- Oscilloscope (for ESD diode leakage verification)
- ESP32-S3 board powered via 3.3V LDO

**Procedure:**
1. Verify the sense wire circuit: GPIO configured as input, external 10K pull-up resistor to 3.3V, kill switch NC contact pulling GPIO to GND when activated.
2. With the kill switch in the released (unpressed) position, measure GPIO voltage. Shall read approximately 3.3V.
3. Press and hold the kill switch. Measure GPIO voltage. Shall read <0.5V.
4. Release the kill switch. Confirm GPIO returns to ~3.3V.
5. Disconnect the sense wire from the GPIO pin entirely (simulate wire break).
6. Measure GPIO voltage at the pin. Shall read <0.5V due to ESD protection diode clamping to ground (the pin floats LOW through the internal ESD structure).
7. Verify the E-Stop ISR fires on this floating-LOW condition (check safety event log).

**Pass Criteria:**
- Disconnected sense wire shall produce GPIO voltage <0.5V.
- Disconnected sense wire shall trigger the E-Stop ISR and log a safety event.
- A disconnected wire shall never be interpreted as "system normal."

**Common Failure Causes:**
- Using the ESP32 internal pull-up (too weak at ~45K; noise can pull the floating pin HIGH).
- No external pull-up resistor installed on the PCB.
- Sense wire routed near high-current motor traces (inductive coupling injects noise).
- GPIO configured as output by mistake (drives HIGH on disconnect).

### Test 1.3: Hardware Watchdog (MAX6818) Reset

**Objective:** Verify that the MAX6818 supervisory IC resets the ESP32 when the firmware stops toggling the watchdog input (WDI) pin, and that the reset pulse meets the MINIMUM duration required by the ESP32 EN pin specification.

**Equipment:**
- Oscilloscope (dual channel, 10MHz minimum)
- Logic analyzer (for WDI edge counting)
- ESP32-S3 board with MAX6818 populated

**Procedure:**
1. Load firmware with watchdog kick at 200ms interval. Verify normal system operation for 60 seconds (no spurious resets).
2. Flash test firmware with watchdog kick disabled (`#define DISABLE_WATCHDOG_KICK`).
3. Connect oscilloscope CH1 to WDI pin. Connect CH2 to ESP32 EN (reset) pin.
4. Start oscilloscope capture in single-shot mode, triggering on CH2 falling edge.
5. Observe the time elapsed from the last WDI toggle to the EN pin assertion. Record the value.
6. Measure the reset pulse duration on EN pin (time LOW). Record the value.
7. After reset, verify the system boots into PROVISIONING state (not NORMAL).
8. After reset, verify all GPIO outputs configured as outputs are driven LOW (safe state).
9. Monitor boot log for "Watchdog reset detected" message.

**Pass Criteria:**
- Reset shall occur within 1.0 to 1.1 seconds of the last WDI toggle (MAX6818 timeout = 1.0s typical).
- Reset pulse duration on EN pin shall be >=140ms (MAX6818 specification).
- System shall boot in PROVISIONING state after watchdog reset.
- All actuator GPIO outputs shall be LOW within 10ms of reset de-assertion.

**Common Failure Causes:**
- WDI pin stuck at a constant level (no toggle = no reset detected).
- Reset output not connected to ESP32 EN pin (connected to RST of wrong IC).
- Software feeding watchdog from a timer ISR (ISR continues running even if main task is dead, defeating the watchdog's purpose).
- WDI toggle interval too close to 1.0s timeout (clock drift causes spurious resets).

### Test 1.4: Polyfuse Overcurrent Trip

**Objective:** Verify that the PTC polyfuse trips at the specified current threshold, maintains high-resistance state during the fault, and self-resets after the fault is removed — all without component replacement or manual intervention.

**Equipment:**
- Programmable DC power supply with current limiting
- Current probe (Hall effect or shunt)
- Thermal camera (optional, for verifying thermal behavior)
- Stopwatch or timer

**Procedure:**
1. Identify the polyfuse part number and rated hold/trip currents from the schematic and BOM.
2. Apply current at 1.5x the rated hold current. Hold for 60 seconds. Verify the fuse remains in low-resistance state (voltage drop <0.25V).
3. Increase current to 2.0x the rated trip current. Start timer.
4. Measure voltage across the fuse. When voltage drop exceeds 1.0V, the fuse has tripped. Record the trip time.
5. Continue applying fault current for 5 seconds. Verify fuse remains tripped (voltage drop >1V).
6. Remove fault current. Allow fuse to cool.
7. Measure fuse resistance every 5 seconds until it returns to <0.1 ohm. Record the recovery time.
8. Repeat the full cycle (steps 2-7) three times to verify repeatability.

**Pass Criteria:**
- Fuse shall hold at 1.5x hold current for at least 60 seconds.
- Fuse shall trip within 5 seconds at 2.0x trip current.
- Voltage across tripped fuse shall exceed 1V (confirms high-resistance state).
- Fuse shall self-reset to <0.1 ohm within 30 seconds of fault removal.
- All three cycles shall pass (no degradation).

**Common Failure Causes:**
- Incorrect fuse value specified in BOM (e.g., 1A fuse where 500mA is required).
- Fuse installed after the MOSFET instead of before (fault current still flows through MOSFET body diode).
- Ambient temperature too high (polyfuse trips at lower current when hot).
- PCB copper pour acting as a heatsink keeps the fuse too cool to trip.

### Test 1.5: MOSFET Gate Fail-Safe

**Objective:** Verify that all actuator-drive MOSFETs are held in the OFF state when the ESP32 is unpowered, in reset, or experiencing a brownout condition, by confirming that gate pull-down resistors assert a valid LOW gate voltage.

**Equipment:**
- Digital multimeter
- 12V DC power supply
- ESP32-S3 board (power removable)

**Procedure:**
1. Disconnect ESP32 power entirely (remove 3.3V LDO input).
2. Apply 12V to the actuator power rail via a current-limited supply (bypassing the kill switch).
3. Measure gate-to-source voltage on each MOSFET in the actuator driver circuit. Record all values.
4. Measure drain-to-source current on each MOSFET channel. Record all values.
5. Briefly short ESP32 3.3V rail to GND through a 1K resistor (simulate brownout). Repeat measurements.
6. Reconnect ESP32 power. Boot to PROVISIONING state. Confirm all MOSFETs remain OFF until explicitly enabled.

**Pass Criteria:**
- Gate voltage on every MOSFET shall be <0.3V when ESP32 is unpowered.
- Drain current on every MOSFET shall be <1uA when ESP32 is unpowered.
- No actuator movement shall occur at any point during this test.

**Common Failure Causes:**
- Missing gate pull-down resistor (gate floats, picks up noise, MOSFET partially turns on).
- Pull-down resistor too strong (1K wastes power, creates excessive gate charge/discharge current).
- Pull-down resistor too weak (100K or higher does not pull gate low enough against EMI).
- MOSFET selected with too-low threshold voltage (Vgs(th) <0.5V, turns on with noise).

---

## 2. Tier 2: Firmware Safety Guard Tests

Tier 2 tests verify the ESP32 firmware's real-time response to safety events. These tests require the firmware safety guard module to be compiled and flashed. All tests in this section assume Tier 1 has passed.

### Test 2.1: E-Stop ISR Response Time

**Objective:** Verify that the E-Stop interrupt service routine responds to a kill switch activation within 1ms, driving all actuator outputs to their safe state.

**Equipment:**
- Oscilloscope (dual channel, 100MHz minimum bandwidth, 1MSa/s minimum sample rate)
- Kill switch or signal generator (for repeatable edge injection)
- ESP32-S3 board running production firmware

**Procedure:**
1. Connect oscilloscope CH1 to the kill switch sense GPIO pin (input side).
2. Connect oscilloscope CH2 to the primary actuator output GPIO pin (output side).
3. Configure the oscilloscope for single-shot capture, triggering on CH1 falling edge.
4. Set horizontal scale to 2ms/div (20ms window) and vertical scale to 1V/div.
5. Press the kill switch (or inject falling edge via signal generator).
6. Measure the time delta between the CH1 falling edge and the CH2 state change. Record value.
7. Repeat steps 5-6 for a total of 10 measurements.
8. Calculate mean, maximum, and standard deviation of the 10 measurements.

**Pass Criteria:**
- All 10 individual measurements shall be <1ms.
- Mean response time shall be <500us.
- Maximum response time shall be <1ms.
- Standard deviation shall be <100us (indicates deterministic behavior).

**Common Failure Causes:**
- ISR code not placed in IRAM (flash cache miss during ISR execution causes 20-40us stall).
- ISR priority misconfigured (lower-priority interrupt preempts the E-Stop ISR).
- Floating-point arithmetic inside ISR (software FPU emulation adds 100+ cycles).
- `configMAX_SYSCALL_INTERRUPT_PRIORITY` set too low, allowing FreeRTOS API calls to be interrupted.

### Test 2.2: ISR Code in IRAM Verification

**Objective:** Verify by static analysis that all code in the E-Stop ISR call chain resides in internal RAM (IRAM), not in flash, ensuring the ISR executes without flash access even during SPI flash operations.

**Equipment:**
- ESP-IDF build environment
- Linker map file (generated during build)
- Text analysis tool (grep, awk, or custom script)

**Procedure:**
1. Build the firmware with `CONFIG_ESP32S3_DATA_IN_IRAM=y` in `sdkconfig`.
2. Locate the generated linker map file: `build/nexus.elf.map`.
3. Search for `estop_isr_handler` in the map file. Record the section it is assigned to.
4. Trace all functions called from within the ISR call chain:
   - `gpio_set_level()` (HAL)
   - `ledc_set_duty()` (PWM control)
   - `xSemaphoreGiveFromISR()` (FreeRTOS)
   - Any helper functions used by the ISR
5. For each function in the call chain, verify it is in `.iram0.text` or `.iram0` section.
6. Flag any function found in `.flash.rodata`, `.flash.text`, or any section not containing "iram."

**Pass Criteria:**
- `estop_isr_handler` shall be in `.iram0.text`.
- Every function in the ISR call chain (depth >= 3) shall be in an IRAM section.
- Zero functions in the ISR call chain shall reside in flash-mapped sections.

**Common Failure Causes:**
- Missing `IRAM_ATTR` attribute on the ISR function or its callees.
- Calling `printf()`, `ESP_LOGI()`, or any logging function from the ISR (these are in flash).
- Calling a HAL function that has not been compiled with IRAM placement.
- Compiler optimizations inlining a flash-resident function into the ISR (check `-fno-inline` for ISR code).

### Test 2.3: Sensor Stale Detection

**Objective:** Verify that the firmware detects when a safety-critical sensor stops providing data (stale data condition) and transitions to safe-state within the configured timeout.

**Equipment:**
- I2C bus analyzer or protocol analyzer
- I2C sensor module (real or simulator)
- Oscilloscope (for timing measurement)
- ESP32-S3 board running production firmware

**Procedure:**
1. Configure the safety-critical sensor with a 500ms stale timeout in the safety policy configuration.
2. Verify sensor reads are completing normally (check log for successful I2C reads at the expected rate).
3. Disconnect the sensor's SDA and SCL lines simultaneously (simulating sensor failure or cable disconnect).
4. Start the oscilloscope capture at the moment of disconnection.
5. Monitor the serial log for the stale detection event.
6. Record the elapsed time from disconnection to safe-state entry.
7. Verify the safety event log contains the correct sensor ID and "STALE_DATA" reason code.

**Pass Criteria:**
- Safe-state shall be entered within 600ms of sensor disconnection (500ms timeout + 100ms maximum response latency).
- The safety event log shall record the correct sensor ID.
- All actuator outputs shall be in their configured safe-state values after transition.

**Common Failure Causes:**
- Stale check interval longer than the stale timeout (detection delayed by polling period).
- Stale counter not reset on successful sensor read (sensor works but counter still expires).
- I2C bus stuck in a state where the driver reports success but returns cached data (no true read).
- Sensor disconnected during a read transaction; I2C driver hangs instead of returning an error.

### Test 2.4: Overcurrent ISR Response

**Objective:** Verify that an overcurrent condition detected by the INA219 current sensor triggers the overcurrent ISR and disables the affected actuator channel within 2ms.

**Equipment:**
- Programmable electronic load (or variable resistor bank)
- INA219 current sensor module
- Oscilloscope (dual channel, 100MHz)
- ESP32-S3 board with INA219 connected to monitored channel

**Procedure:**
1. Connect the INA219 to the monitored actuator channel per the schematic.
2. Configure the INA219 overcurrent alert threshold at 2x the nominal actuator current.
3. Connect oscilloscope CH1 to the INA219 ALERT pin (open-drain output).
4. Connect oscilloscope CH2 to the actuator output GPIO pin.
5. Configure oscilloscope for single-shot trigger on CH1 falling edge.
6. Gradually increase load current until it exceeds the INA219 threshold.
7. Measure the time delta between CH1 falling edge (INA219 alert) and CH2 state change (output disabled).
8. Repeat three times. Record all values.

**Pass Criteria:**
- Actuator output shall be disabled within 2ms of the INA219 ALERT pin assertion.
- The overcurrent event shall be logged with the correct channel ID and measured current value.
- The channel shall remain disabled until explicitly re-enabled via Jetson command.

**Common Failure Causes:**
- INA219 ALERT pin not configured as an interrupt source in firmware (polled instead of interrupt-driven).
- Alert threshold register misconfigured (wrong multiplier or shunt resistor value in calculation).
- ALERT pin pull-up resistor missing (open-drain output never reaches valid HIGH).
- ISR for overcurrent shares priority with lower-critical interrupts and gets preempted.

---

## 3. Tier 3: Supervisory Task Tests

Tier 3 tests verify the FreeRTOS-based supervisory task that monitors system health, heartbeats, and resource utilization. These tests require the full firmware stack to be operational.

### Test 3.1: Heartbeat Loss Escalation

**Objective:** Verify the heartbeat monitoring escalation sequence: HEARTBEAT_DEGRADED after 5 consecutive missed heartbeats (~500ms) and HEARTBEAT_SAFE_STATE after 10 consecutive missed heartbeats (~1000ms). Confirm no automatic resume after heartbeat restoration.

**Equipment:**
- Jetson Orin Nano connected via serial to ESP32
- Logic analyzer (monitoring serial TX/RX lines)
- Serial terminal on both Jetson and ESP32 sides
- Stopwatch

**Procedure:**
1. Verify system is in NORMAL operational mode (Jetson sending heartbeats at 100ms interval, per safety spec).
2. Physically disconnect the Jetson serial TX line (ESP32 RX). Start stopwatch.
3. Monitor the ESP32 serial log for the HEARTBEAT_DEGRADED event. Record the time.
4. Continue monitoring for the HEARTBEAT_SAFE_STATE event. Record the time.
5. Verify all actuator outputs are at their configured safe-state values.
6. Reconnect the Jetson serial TX line.
7. Monitor the ESP32 serial log. Verify the system requests RESUME (does NOT auto-resume).
8. Send RESUME command from Jetson. Verify staged resume sequence begins.

**Pass Criteria:**
- HEARTBEAT_DEGRADED event shall be logged between 400ms and 600ms after heartbeat loss.
- HEARTBEAT_SAFE_STATE event shall be logged between 900ms and 1100ms after heartbeat loss.
- All actuator outputs shall be in safe-state after SAFE_STATE event.
- System shall NOT auto-resume when heartbeats resume. A RESUME command is required.
- After RESUME, staged resume shall follow the defined sequence (reflexes first, then PID, then AI).

**Common Failure Causes:**
- Heartbeat interval misconfigured: using 1000ms (wire protocol default) instead of 100ms (safety specification requirement).
- Auto-resume implemented as convenience feature (violates safety policy — operator must explicitly acknowledge).
- Heartbeat timeout counter not reset when a valid heartbeat arrives (counter only resets on transition, not on each beat).
- Serial buffer overflow causing valid heartbeats to be dropped (increases apparent miss rate).

### Test 3.2: Task Watchdog

**Objective:** Verify that the software task watchdog detects a hung task within 1 second and that a hung safety_supervisor task triggers a full hardware reset within 2 seconds.

**Equipment:**
- ESP32-S3 board running production firmware
- Serial terminal
- Test firmware variant with hung-task injection

**Procedure:**
1. Flash firmware with test mode enabled that creates a "poison" task which stops calling `safety_watchdog_checkin()` after 10 seconds of normal operation.
2. Monitor the serial log. At T+10s, verify a MEDIUM-severity "Task watchdog timeout" event is logged.
3. At T+12s, verify the poison task is suspended and all actuators are driven to safe-state.
4. Flash a second test variant that causes the `safety_supervisor` task itself to hang (infinite loop with interrupts disabled).
5. At T+1s, verify the software watchdog timeout is logged.
6. At T+2s, verify the MAX6818 hardware watchdog triggers a full system reset.
7. After reset, verify system boots in PROVISIONING state.

**Pass Criteria:**
- Hung non-safety task: first timeout (MEDIUM) logged at 1s, task suspended and actuators safe at 2s.
- Hung safety_supervisor task: software watchdog timeout at 1s, hardware watchdog reset at 2s.
- Post-reset boot state shall be PROVISIONING for both scenarios.

**Common Failure Causes:**
- Watchdog check-in called from a timer ISR instead of the monitored task (ISR always succeeds even if task is dead).
- Watchdog timeout set too generously (e.g., 10 seconds instead of 1 second).
- Safety_supervisor not registered with both software and hardware watchdog chains.
- Hung task holding a mutex that blocks the watchdog check-in of other tasks (cascading false positives).

### Test 3.3: Heap Monitoring

**Objective:** Verify that the heap monitoring subsystem detects memory leaks before heap exhaustion occurs, providing early warning at 30% remaining capacity and triggering safe-state transition at 10% remaining capacity.

**Equipment:**
- ESP32-S3 board running production firmware
- Serial terminal
- Test firmware with controlled memory leak injection

**Procedure:**
1. Record the baseline free heap value reported at boot (from the startup log).
2. Flash firmware with a test mode that allocates 100 bytes every 10 seconds and never frees it (simulating a slow leak).
3. Monitor the serial log. When free heap drops below 30% of the baseline value, verify a WARNING-severity "Heap low" event is logged with the current and baseline values.
4. Continue monitoring. When free heap drops below 10% of baseline, verify a SAFE_STATE transition occurs with reason "HEAP_CRITICAL."
5. Verify the system does not crash or reboot due to heap exhaustion (malloc failure).
6. Check that the leak rate and remaining heap are logged periodically (every 60 seconds minimum).

**Pass Criteria:**
- WARNING logged when free heap <30% of boot baseline.
- SAFE_STATE transition when free heap <10% of boot baseline.
- No crash or unexpected reboot from heap exhaustion at any point during the test.
- Periodic heap status logged at least every 60 seconds.

**Common Failure Causes:**
- Heap monitoring not implemented (relying solely on ESP-IDF's built-in heap corruption detection, which only triggers after corruption occurs).
- Free heap appears sufficient but largest contiguous free block is tiny (fragmentation not detected by total-free-heap check).
- Heap monitoring task itself allocates memory to format log messages (accelerates the very condition it is trying to detect — use static buffers).
- `heap_caps_get_largest_free_block()` not checked (total free heap can be 50% but largest block <1KB).

---

## 4. Tier 4: Application Control Tests

Tier 4 tests verify the application-layer safety controls that prevent unsafe actuator commands from reaching the hardware. These tests require the full system stack (firmware + Jetson + application).

### Test 4.1: Actuator Rate Limiting

**Objective:** Verify that actuator output changes are rate-limited per the safety policy, preventing rapid command sequences from reaching the actuators faster than the configured maximum rate.

**Equipment:**
- Jetson connected to ESP32
- Oscilloscope (monitoring PWM output)
- Test script generating rapid actuator commands

**Procedure:**
1. Configure the actuator with a 10Hz rate limit (minimum 100ms between output changes).
2. Deploy a reflex or Jetson command that attempts to change the actuator PWM value at 1000Hz (every 1ms).
3. Connect the oscilloscope to the actuator PWM output pin.
4. Count the number of actual PWM value transitions over a 1-second window.
5. Verify the measured transition rate matches the 10Hz configured limit.
6. Change the rate limit to 50Hz and repeat. Verify 50 transitions per second.

**Pass Criteria:**
- Actual PWM change rate shall not exceed the configured rate limit.
- Actual rate shall be within +/-10% of the configured rate (accounting for timer quantization).
- Rate limiting shall be applied AFTER safety bounds checking (a command that fails bounds check shall not consume a rate-limit slot).

**Common Failure Causes:**
- Rate limiting not implemented in the actuator driver.
- Rate limit applied before safety bounds check (out-of-bounds commands consume rate-limit slots, blocking legitimate commands).
- Rate limit counter shared across actuators (one fast actuator starves all others).
- Rate limit uses wall-clock time instead of a deterministic tick counter (drift under load).

### Test 4.2: Actuator Safe-State Bounds

**Objective:** Verify that actuator outputs are clamped to their configured minimum and maximum values regardless of the commanded value from the VM, PID controller, or direct application write, and that the safe-state value is correctly applied during safe-state transitions.

**Equipment:**
- ESP32-S3 board running production firmware
- Jetson connected via serial
- Oscilloscope (monitoring PWM output)

**Procedure:**
1. Configure an actuator channel with: min=1000us, max=2000us, safe=1500us (PWM pulse width in microseconds).
2. Deploy a reflex that writes 0 to the actuator channel.
3. Measure the actual PWM output with the oscilloscope. Record value.
4. Deploy a reflex that writes 3000 to the actuator channel.
5. Measure the actual PWM output. Record value.
6. Deploy a reflex that writes 1500 (the safe value). Verify output matches.
7. Deploy a reflex that writes 1200 (within bounds). Verify output matches.
8. Trigger a safe-state transition (e.g., via kill switch).
9. Measure the PWM output after safe-state. Record value.

**Pass Criteria:**
- Command value of 0 shall be clamped to 1000us (min bound).
- Command value of 3000 shall be clamped to 2000us (max bound).
- Command value of 1500 shall produce 1500us output (within bounds, no clamping).
- Command value of 1200 shall produce 1200us output (within bounds, no clamping).
- Safe-state transition shall produce 1500us output (explicit safe-state value, not last clamped value).
- Clamping violations shall be logged as MEDIUM-severity events.

**Common Failure Causes:**
- Clamping performed before VM output write (VM may bypass clamping through a different code path).
- Safe-state value not applied during transition (system holds last clamped value instead).
- Min/max values stored in wrong endianness or unit (microseconds vs. milliseconds vs. raw duty cycle).
- Clamping check uses `<=` instead of `<` at the boundary (off-by-one allows one value past the limit).

---

## 5. Combined Scenario Tests

Combined scenario tests exercise the entire four-tier safety system as an integrated whole. These tests verify that the tiers interact correctly and that no single-tier bypass exists.

### Test 5.1: Full Safety Chain

**Objective:** Exercise the complete safety chain from kill switch through firmware ISR, supervisory task escalation, and application control recovery.

**Equipment:**
- Complete NEXUS system (ESP32-S3 + Jetson + actuators + kill switch)
- Oscilloscope
- Serial terminals on both ESP32 and Jetson

**Procedure:**
1. **Step 1:** System in NORMAL operation. PID controller actively driving an actuator. Confirm actuator is moving.
2. **Step 2:** Press the kill switch. Verify: actuators stop immediately, E-Stop ISR fires (Tier 2), safe-state entered, safety event logged.
3. **Step 3:** Release the kill switch. Verify: system enters PROVISIONING state. No actuators move. No auto-resume.
4. **Step 4:** Reconnect via Jetson command (ASSIGN_ROLE + RESUME). Verify: staged resume sequence — reflexes activated first, PID enabled second, AI pipeline enabled third.
5. **Step 5:** Disable Jetson heartbeat (stop sending heartbeats). Verify: DEGRADED event at ~500ms, SAFE_STATE at ~1000ms.
6. **Step 6:** Resume Jetson heartbeats. Verify: system awaits explicit RESUME command (no auto-resume). Send RESUME. Verify staged resume.
7. **Step 7:** Induce overcurrent on a channel (increase load beyond threshold). Verify: channel disabled immediately, alarm event logged, other channels unaffected.
8. **Step 8:** Clear the error via Jetson command (CLEAR_ERROR + ENABLE_CHANNEL). Verify: channel re-enabled with soft-start ramp (output increases gradually, not instantly).

**Pass Criteria:**
- All 8 steps shall produce the correct response as described.
- No unexpected state transitions at any point.
- All safety events shall be logged with correct timestamps, source IDs, and reason codes.
- No actuator shall move outside its configured safe-state during any fault condition.

### Test 5.2: Boot-to-Operational Safety

**Objective:** Verify that the system maintains safe outputs during the entire boot sequence, and that rapid power cycling triggers FAULT mode to prevent damage from voltage instability.

**Equipment:**
- Complete NEXUS system
- Power supply with switch (for rapid cycling)
- Oscilloscope (monitoring GPIO outputs)
- Stopwatch

**Procedure:**
1. **Step 1:** Power on the system from a completely off state.
2. **Step 2:** Using the oscilloscope, verify ALL GPIO outputs configured as actuator drivers remain LOW for the first 500ms after power-on (until ROLE_ASSIGN state).
3. **Step 3:** Verify the hardware watchdog (MAX6818) begins receiving kicks within 5ms of the ESP32 exiting reset (check WDI pin on oscilloscope).
4. **Step 4:** Complete the full boot sequence. Deploy a reflex. Transition to NORMAL state. Verify actuator responds to commands.
5. **Step 5:** Kill power. Wait 3 seconds. Reapply power. Verify normal boot (PROVISIONING -> NORMAL). Check boot counter incremented by 1.
6. **Step 6:** Rapid power cycle: power on, wait 1 second, power off, wait 1 second. Repeat for a total of 6 cycles within 10 seconds.
7. **Step 7:** On the 6th boot, verify the system enters FAULT state (boot counter >5 within the 10-minute rolling window).
8. **Step 8:** Wait 10 minutes. Power cycle once. Verify normal boot (counter expired, system boots normally).

**Pass Criteria:**
- All actuator GPIO outputs LOW for first 500ms of every boot.
- Watchdog kick begins within 5ms of reset release.
- Normal boot-to-operational transition works correctly (Steps 1-4).
- FAULT mode entered on 6th rapid power cycle within 10 minutes (Step 7).
- FAULT mode clears after 10-minute window expires (Step 8).
- In FAULT mode, all outputs remain LOW and no commands are accepted.

---

## Test Schedule and Cadence

| Cadence | Tests | Duration | Sign-Off |
|---|---|---|---|
| **Daily (development)** | 1.1, 1.2, 2.1 | ~5 minutes | Developer self-sign |
| **Weekly (integration)** | All Tier 1 tests | ~30 minutes | Lead engineer sign-off |
| **Per release candidate** | All tests (Tiers 1-4 + Scenarios) | ~4 hours | Safety review board sign-off |
| **Pre-ship (production)** | Full test suite + thermal chamber (-20C to +60C) + vibration (IEC 60068) | ~2 days | Quality assurance + safety officer sign-off |

### Test Execution Rules

1. **No skipping.** Every test in the schedule must be executed and recorded. A "not tested" entry is equivalent to a "fail."
2. **Sequential ordering.** Tier 1 tests must pass before Tier 2 testing begins. Tier 2 before Tier 3. Tier 3 before Tier 4. Scenario tests require all tier tests to have passed.
3. **Regression on change.** Any change to firmware, hardware, or configuration reopens all tests from the affected tier and below.
4. **Environmental conditions.** Pre-ship tests must pass at temperature extremes (-20C, +25C, +60C) and during vibration (10-150Hz, 0.5g RMS).
5. **Record retention.** All test logs, oscilloscope captures, and sign-off records shall be retained for a minimum of 5 years per IEC 61508 requirements.

---

*This playbook is a living document. Revisions require safety review board approval. Test IDs shall not be reused. New tests shall be assigned the next sequential ID in their tier.*
