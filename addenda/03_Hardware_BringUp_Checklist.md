# Hardware Bring-Up Checklist — First Power-On Procedures

**Document ID:** NEXUS-ADD-003
**Revision:** 1.0
**Applies to:** NEXUS robotics platform — ESP32-S3 limb nodes and Jetson Orin Nano Super brain nodes
**Audience:** Hardware and firmware engineers performing first assembly and power-on

> **CRITICAL SAFETY RULE:** At every gate, if ANY test fails, STOP. Do not proceed to the next gate until the failure is understood, resolved, and re-tested. The NEXUS safety architecture is only as strong as its hardware foundation.

---

## Prerequisites

### Equipment Required

| Equipment | Minimum Spec | Purpose |
|-----------|-------------|---------|
| Oscilloscope | 200 MHz, 4 channel | Timing verification, signal integrity |
| Digital multimeter | 0.1 mV resolution, 0.01 Ω continuity | Rail voltages, continuity checks |
| Logic analyzer | Saleae Logic Pro 16 or equivalent | Protocol decode (UART, I²C, COBS framing) |
| USB-TTL serial adapter | 3.3V I/O, CP2102 or CH340 | ESP32 console, Jetson serial debug |
| RS-422 test board | THVD1500 or equivalent transceiver | Physical layer validation |
| Bench power supply | Adjustable 0-15V, current limit | Controlled power during bring-up |
| Thermal camera | FLIR One or equivalent (optional) | Hot-spot detection on power rails |
| RJ-45 loopback plug | Pins 1-2 bridged to 3-4 | RS-422 local loopback test |
| Known-good I²C device | TMP117 temperature sensor or BMP280 | I²C bus validation |

### Software Required

| Software | Version | Purpose |
|----------|---------|---------|
| ESP-IDF | v5.2+ | ESP32-S3 firmware toolchain |
| VSCode + ESP-IDF extension | Latest | IDE and flash/debug |
| Python | 3.11+ | Jetson-side scripts, serial bridge |
| minicom or picocom | Any | Serial terminal for raw UART debug |
| pyserial | v3.5+ | Python serial communication |
| NVIDIA JetPack | 6.x | Jetson Orin Nano Super SDK |

### Reference Documents (Keep Open)

| Document | Location | Why |
|----------|----------|-----|
| Wire Protocol Spec | `wire_protocol_spec.md` | Frame format, COBS rules, message type IDs |
| Safety System Spec | `safety_system_spec.md` | E-Stop timing, watchdog behavior, state machine |
| Reflex Bytecode VM Spec | `reflex_bytecode_vm_spec.md` | Opcode table, safety invariants, memory layout |
| Build Prompts | `NEXUS_Claude_Code_Build_Prompts.md` | Pin assignments, boot sequence timing |

---

## Gate 0: Board Bring-Up (No NEXUS Firmware)

**Goal:** Verify raw hardware functions before loading ANY NEXUS code. This gate proves the silicon, power delivery, and basic peripherals work.

### 0.1 Power Supply Verification

**Objective:** Confirm all voltage rails are within specification before connecting any processors or peripherals.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 0.1.1 | Set bench supply to 12.0V, connect to board input terminals. Verify polarity (red = +, black = GND). | No smoke, no spark, bench supply current reads <50mA (board idle). | ☐ |
| 0.1.2 | Measure 3.3V rail with multimeter: probe between 3.3V test point and GND. | **3.28V – 3.32V** under no-load conditions. | ☐ |
| 0.1.3 | Load the 3.3V rail (connect a 100Ω resistor between 3.3V and GND = 33mA load). Re-measure. | Remains within **3.25V – 3.33V**. Voltage sag <0.05V. | ☐ |
| 0.1.4 | If a 5V rail exists (USB-powered boards), measure at the 5V test point. | **4.95V – 5.05V**. | ☐ |
| 0.1.5 | Measure the 12V actuator supply rail at the motor driver input pins. | **11.5V – 12.5V** with no actuators connected. | ☐ |
| 0.1.6 | **Power OFF.** Measure continuity across the polyfuse (F1) with multimeter in continuity mode. Touch probes across fuse terminals. | Continuity beep. Resistance <0.5Ω. | ☐ |
| 0.1.7 | Locate the kill switch NC contact terminals. With power OFF, measure continuity across them with the mushroom-head button **released**. | Continuity beep. NC contact closed. | ☐ |
| 0.1.8 | Press the kill switch. Continuity should **break** (no beep). | Open circuit when pressed. | ☐ |
| 0.1.9 | Release the kill switch. Continuity should **return**. | Continuity returns immediately. | ☐ |
| 0.1.10 | Power ON. Measure voltage at the kill switch sense GPIO (GPIO22 on standard build). Button released. | **~3.3V** (pulled HIGH by external 10K pull-up to 3.3V rail). | ☐ |
| 0.1.11 | Press the kill switch. Measure voltage at the sense GPIO. | **~0.0V** (pulled LOW through switch to GND). | ☐ |
| 0.1.12 | Cut the sense wire (simulate broken wire). Measure voltage at the sense GPIO. | **~3.3V** — this is the FAIL-SAFE state. Broken wire = switch released = safe. | ☐ |

> **PITFALL:** If step 0.1.12 reads LOW with a broken wire, you have a pull-DOWN instead of a pull-UP. This is a safety-critical error — a broken wire would trigger a false E-Stop, masking the real danger. Fix before proceeding.

### 0.2 ESP32-S3 Bare Metal Test

**Objective:** Confirm the ESP32-S3 boots, communicates, and basic peripherals work using only the factory ESP-IDF "hello_world" example.

**Setup:** Connect USB-TTL adapter: TX→RX (GPIO43), RX→TX (GPIO44), GND→GND. Do NOT connect CTS/RTS yet.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 0.2.1 | Open a terminal: `idf.py -p /dev/ttyUSB0 flash monitor -b 460800` from the `examples/get-started/hello_world` directory. | Flash succeeds. Monitor shows ESP32 boot messages at 74880 baud (ROM bootloader), then 115200 baud (app). | ☐ |
| 0.2.2 | Look for the string "Hello world!" in the serial output. | Printed every 1 second. Text is clean, no garbled characters. | ☐ |
| 0.2.3 | Read the ESP32's MAC address from boot log: line containing "rst:0x1". Note the 6-byte MAC for later DEVICE_IDENTITY verification. | MAC address recorded: `__`:__`:__`:__`:__`:`__ | ☐ |
| 0.2.4 | Place multimeter in series with 3.3V supply to ESP32 (measure current draw). | **40 – 80 mA** (no peripherals, WiFi/BT idle). | ☐ |
| 0.2.5 | Enable WiFi briefly (`esp_wifi_init()` + `esp_wifi_start()`). Measure peak current. | **120 – 200 mA** transient during calibration, settling to ~100mA. | ☐ |
| 0.2.6 | Write a minimal GPIO test: toggle GPIO2 (built-in LED on most ESP32-S3 dev boards) at 1Hz using `gpio_set_level()`. | LED blinks at 1Hz, visible to the eye. Measure with oscilloscope: period = 1000ms ± 1ms. | ☐ |
| 0.2.7 | Test ADC1_CH6 (GPIO7 on ESP32-S3). Apply a known voltage (e.g., 1.65V from a voltage divider between 3.3V and GND using two 10K resistors). Read the raw ADC value. | Raw value ≈ 2048 (12-bit ADC, mid-range). Converted voltage ≈ 1.65V ± 0.05V. | ☐ |
| 0.2.8 | Test I²C0 on GPIO21 (SDA) and GPIO22 (SCL). Run `i2c_scanner` example. | I²C scan completes without hang. Known I²C device (e.g., TMP117 at address 0x48) appears in scan results. | ☐ |

### 0.3 RS-422 Physical Layer Test

**Objective:** Verify the THVD1500 RS-422 transceiver works at full speed before connecting the Jetson.

**Wiring Diagram:**
```
ESP32-S3                    THVD1500                    Jetson Orin Nano
  GPIO4 (TX)  ────────────> DI (pin 3)          
  GPIO5 (RX)  <──────────── RO (pin 1)          
  GPIO6 (CTS) ────────────> (not used for DE)
  GPIO7 (RTS) ────────────> (not used for RE)
              VCC ────────── VCC (pin 5) → 3.3V
              GND ────────── GND (pin 2) → GND
              DE  ────────── DE (pin 4) → 3.3V (hardwired HIGH, always transmitting)
              RE̅  ────────── RE (pin 6) → GND (hardwired LOW, always receiving)
              A   ────────── A  (pin 7) → RJ-45 pin 1 (TX+) / pin 3 (RX+)
              B̅   ────────── B  (pin 8) → RJ-45 pin 2 (TX−) / pin 4 (RX−)
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 0.3.1 | Solder THVD1500 to breakout board. Apply 3.3V to VCC, GND to GND. Wire DE to 3.3V, RE to GND. | No overheating. Current draw <5mA (idle transceiver). | ☐ |
| 0.3.2 | Install 120Ω termination resistor across A-B at each end of the RS-422 cable (RJ-45 connector). | Resistance across A-B at any connector ≈ 60Ω (two 120Ω in parallel). | ☐ |
| 0.3.3 | Connect RJ-45 loopback plug: pin 1→pin 3, pin 2→pin 4. This connects TX output to RX input on the same transceiver. | Loopback path established. | ☐ |
| 0.3.4 | Configure UART1 on ESP32-S3: 115200 baud, 8N1, CTS/RTS disabled for this test. TX on GPIO4, RX on GPIO5. | UART initializes without error. | ☐ |
| 0.3.5 | Send 0xAA pattern (alternating bits, worst-case for signal integrity): transmit 1000 bytes of 0xAA via UART1. Read back from UART1 RX. | All 1000 bytes received correctly. Zero bit errors. | ☐ |
| 0.3.6 | Repeat at 460800 baud, then 921600 baud. | Zero bit errors at both baud rates. | ☐ |
| 0.3.7 | Measure differential voltage with oscilloscope: probe A (CH1) and B (CH2), Math = CH1 − CH2. | Differential voltage ≥ **2.0V** peak-to-peak under loaded conditions (with 120Ω termination). | ☐ |
| 0.3.8 | Check signal eye diagram at 921600 baud: trigger on rising edge, persistence mode. | Clean eye opening. Minimal overshoot (<10%), minimal ringing (<5% of amplitude settling within 10ns). | ☐ |

> **PITFALL:** If differential voltage < 1.5V, check: (1) 3.3V supply sag under load, (2) THVD1500 is genuine (counterfeits have weak drivers), (3) cable capacitance (use Cat5e or Cat6, max 100m for 921600 baud).

### 0.4 Jetson Orin Nano Super Boot

**Objective:** Verify the Jetson Orin Nano Super boots, all peripherals are detected, and storage is ready.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 0.4.1 | Follow NVIDIA's official JetPack 6.x flashing guide. Connect Jetson to host PC via USB-C (recovery mode pins shorted). Run `sudo ./nvidia-jetson-sdk-installer.sh`. | Flash completes in ~30 minutes. No errors. | ☐ |
| 0.4.2 | Connect keyboard, monitor (HDMI), and Ethernet to Jetson. Power on. Wait for Ubuntu desktop. | System boots to login prompt. Default credentials: `nvidia` / `nvidia`. | ☐ |
| 0.4.3 | Open terminal, run: `nvidia-smi`. | Output shows GPU: Orin (40 TOPS), driver version, CUDA version. Memory shows ~8GB total. | ☐ |
| 0.4.4 | Run: `free -h`. | Total RAM ≈ 7.5–7.8 GB available (some reserved by kernel/GPU). | ☐ |
| 0.4.5 | Install NVMe SSD (M.2 2280). Run: `lsblk`. | NVMe device appears (e.g., `/dev/nvme0n1`). Reported size ≈ 256 GB. | ☐ |
| 0.4.6 | Format and mount NVMe: `sudo mkfs.ext4 /dev/nvme0n1p1`, add to `/etc/fstab`. Reboot. Verify mount at `/data`. | SSD persists across reboot. Write speed > 500 MB/s (`dd if=/dev/zero of=/data/test bs=1M count=1000`). | ☐ |
| 0.4.7 | Configure static IP on GbE interface: edit `/etc/netplan/01-network-manager-all.yaml`. Assign `192.168.1.100/24`, gateway `192.168.1.1`. Apply with `sudo netplan apply`. | `ip addr show eth0` shows configured IP. `ping 192.168.1.1` succeeds. | ☐ |
| 0.4.8 | Connect USB-TTL adapter. Run: `ls /dev/ttyUSB*`. | `/dev/ttyUSB0` appears. | ☐ |
| 0.4.9 | Install Python 3.11 and dependencies: `sudo apt install python3.11 python3-pip && pip3 install pyserial paho-mqtt numpy`. | All packages install without error. `python3 -c "import serial; print(serial.__version__)"` works. | ☐ |
| 0.4.10 | Run: `python3 -c "import serial; s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1); s.write(b'AT\r\n'); print(s.read(100))"`. | No crash. Serial port opens and writes successfully. | ☐ |

---

## Gate 1: Serial Communication (ESP32 ↔ Jetson)

**Goal:** Establish reliable bidirectional serial communication using the NEXUS wire protocol. Both sides must encode/decode COBS frames, compute CRC-16, and exchange messages with zero errors.

### 1.1 ESP32 Side — Minimal Protocol Firmware

Flash a minimal firmware that implements only the COBS encoder/decoder, CRC-16 calculator, and message dispatch for four message types: DEVICE_IDENTITY (0x01), HEARTBEAT (0x05), PING (0x16), and PONG (0x17).

**Build and flash:**
```bash
cd /firmware
idf.py set-target esp32s3
idf.py -p /dev/ttyUSB0 -b 460800 flash monitor
```

**Expected boot output at 115200 baud:**
```
NEXUS Limb Node v0.1.0-pre
MAC: AA:BB:CC:DD:EE:FF
UART1 initialized at 115200 baud, 8N1, CTS/RTS on
[COBS TX] msg_type=0x01 DEVICE_IDENTITY len=64
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 1.1.1 | Flash the minimal protocol firmware. Monitor boot log on UART0 (USB console). | Boot messages appear. No panic, no Guru Meditation. | ☐ |
| 1.1.2 | Verify DEVICE_IDENTITY message is sent on UART1 (RS-422 side). Use logic analyzer on TX pair (A/B) to capture. | COBS frame starts with 0x00, ends with 0x00. Decoded header: msg_type=0x01. Payload contains JSON with `"mac"` field. | ☐ |
| 1.1.3 | Connect Jetson RS-422 RX to ESP32 TX pair. Run Jetson Python script to listen. | DEVICE_IDENTITY received and parsed. MAC matches value from step 0.2.3. | ☐ |

### 1.2 Jetson Side — Serial Bridge Test Script

Create `/jetson/tests/test_serial_basic.py`:

```python
import serial, struct, time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2.0)

# Wait for DEVICE_IDENTITY (msg_type 0x01)
while True:
    frame = ser.read_until(b'\x00')
    if len(frame) > 12:  # minimum: 0x00 + COBS(10 header + 2 CRC) + 0x00
        # Decode COBS (simplified — use full cobs library in production)
        msg_type = frame[1]  # After COBS decode, first byte is msg_type
        if msg_type == 0x01:
            print(f"DEVICE_IDENTITY received ({len(frame)} bytes)")
            break

# Send PING (0x16) with sequence number 1
header = struct.pack('>BBHIH', 0x16, 0x00, 1, int(time.time()*1000) % 0xFFFFFFFF, 0)
# Compute CRC-16/CCITT-FALSE over header
crc = crc16_ccitt(header)
wire = b'\x00' + cobs_encode(header + struct.pack('>H', crc)) + b'\x00'
ser.write(wire)

# Wait for PONG (0x17)
t_start = time.monotonic()
frame = ser.read_until(b'\x00')
t_rtt = (time.monotonic() - t_start) * 1000  # ms
print(f"PONG received. Round-trip: {t_rtt:.1f} ms")
assert t_rtt < 5.0, f"PING/PONG too slow: {t_rtt:.1f} ms"
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 1.2.1 | Run the test script. Verify DEVICE_IDENTITY is received within 500ms of ESP32 power-on. | `DEVICE_IDENTITY received (XX bytes)` printed. | ☐ |
| 1.2.2 | Verify PONG response arrives and round-trip latency is measured. | `PONG received. Round-trip: X.X ms`. Value < **5.0 ms** at 115200 baud. | ☐ |
| 1.2.3 | Send 1000 consecutive PING/PONG pairs. Count CRC errors. | Zero CRC errors. 1000/1000 PONGs received. | ☐ |
| 1.2.4 | Verify COBS framing: inspect raw bytes on logic analyzer. | Every frame bounded by 0x00. No 0x00 bytes within COBS-encoded payload. | ☐ |

### 1.3 Baud Rate Upgrade

**Objective:** Negotiate from 115200 to 921600 baud using the BAUD_UPGRADE (0x18) message.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 1.3.1 | Jetson sends BAUD_UPGRADE (0x18) with JSON payload `{"target_baud": 921600}`. | ESP32 acknowledges. Both sides switch baud rate simultaneously. | ☐ |
| 1.3.2 | Add **50ms settling delay** on BOTH sides after baud switch. Critical for transceiver re-lock. | No data loss during transition. | ☐ |
| 1.3.3 | Jetson sends PING at 921600 baud. Verify PONG received within 500ms. | PONG received. Round-trip < **2.0 ms** at 921600. | ☐ |
| 1.3.4 | Run 1000 PING/PONG pairs at 921600. Verify zero CRC errors. | 1000/1000 success. Zero errors. | ☐ |
| 1.3.5 | If step 1.3.3 fails: both sides fall back to 115200. Retry at 460800 baud. | At minimum, 460800 baud must work reliably. | ☐ |

### PASS Criteria — Gate 1

- [ ] DEVICE_IDENTITY received within **500ms** of ESP32 boot
- [ ] PING/PONG round-trip < **5ms** at 115200 baud, < **2ms** at 921600 baud
- [ ] Zero CRC errors in **1000 consecutive messages** at 921600 baud
- [ ] Baud upgrade from 115200 → 921600 succeeds on **first attempt**
- [ ] COBS framing verified on logic analyzer: no in-frame 0x00 bytes

**Sign-off:** _________________ **Date:** __________ **Engineer:** _________________

---

## Gate 2: Kill Switch and Safety Hardware

**Goal:** Verify the PRIMARY safety mechanism — the kill switch — works at hardware and firmware level. This is the most safety-critical gate.

> **REMINDER:** The kill switch is a normally-closed (NC) mushroom-head switch wired in **series** with the +12V actuator supply. Opening the switch removes power from ALL actuators. The sense wire provides software awareness of the switch state.

### 2.1 Kill Switch Wiring Verification

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.1.1 | **Power OFF.** Measure continuity across kill switch terminals. Button **released**. | Continuity beep. Resistance < 0.5Ω. | ☐ |
| 2.1.2 | Press the kill switch. | Continuity breaks. Open circuit. | ☐ |
| 2.1.3 | Release the kill switch. | Continuity returns immediately. No bounce visible on multimeter (mushroom-head switches are typically bounce-free). | ☐ |
| 2.1.4 | Measure the sense wire voltage at the GPIO (GPIO22): button released. | **3.3V** (pulled HIGH by external 10KΩ resistor). | ☐ |
| 2.1.5 | Press kill switch. Measure GPIO voltage. | **0.0V** (pulled LOW through switch to GND). | ☐ |
| 2.1.6 | Release kill switch. | Returns to **3.3V**. | ☐ |

### 2.2 E-Stop ISR Timing Test

**Objective:** Measure the time from kill-switch contact break to actuator output GPIO transitioning to safe state. The spec requires <1ms; the target is <100µs.

**Setup:**
- Oscilloscope CH1: probe kill switch contact (one side, other to GND).
- Oscilloscope CH2: probe actuator output GPIO (e.g., GPIO4 — rudder PWM output).
- Trigger: CH1 falling edge.

**Firmware:** Load minimal E-Stop test firmware:
```c
// ISR assigned to GPIO22 (kill switch sense), FALLING edge
void IRAM_ATTR estop_isr_handler(void* arg) {
    // IMMEDIATELY set all actuator GPIOs to safe state (LOW)
    gpio_set_level(ACTUATOR_GPIO_1, 0);
    gpio_set_level(ACTUATOR_GPIO_2, 0);
    gpio_set_level(ACTUATOR_GPIO_3, 0);
    // NO floating point. NO logging. NO blocking. Return immediately.
}
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.2.1 | Load E-Stop test firmware. Verify GPIO22 configured as INPUT with pull-up, interrupt on FALLING edge, priority ESP_INTR_FLAG_LEVEL1. | Firmware boots. ISR registered without error. | ☐ |
| 2.2.2 | Set actuator output GPIO to HIGH (simulating active actuator). Verify on oscilloscope CH2. | CH2 reads 3.3V (HIGH). | ☐ |
| 2.2.3 | Press kill switch. Capture single-shot on oscilloscope. Measure Δt between CH1 falling edge and CH2 falling edge. | Δt **< 1ms**. Target: **< 100µs**. | ☐ |
| 2.2.4 | Release kill switch. Re-arm actuator GPIO to HIGH. Repeat. | Consistent timing across presses. | ☐ |
| 2.2.5 | Repeat steps 2.2.2–2.2.4 for a total of **10 presses**. Record all 10 timing measurements. | All 10 measurements < **1ms**. Worst-case recorded: `____`µs. | ☐ |

**Timing Record:**
| Press | Δt (µs) | Pass |
|-------|---------|------|
| 1 | | ☐ |
| 2 | | ☐ |
| 3 | | ☐ |
| 4 | | ☐ |
| 5 | | ☐ |
| 6 | | ☐ |
| 7 | | ☐ |
| 8 | | ☐ |
| 9 | | ☐ |
| 10 | | ☐ |

### 2.3 Hardware Watchdog Test

**Objective:** Verify the MAX6818 (or TPS3823-33) external supervisor IC resets the ESP32 if the watchdog kick stops.

**Wiring:**
```
MAX6818:
  VCC  → 3.3V rail
  GND  → GND
  WDI  → ESP32 GPIO (e.g., GPIO8)
  RST̅/WDO → ESP32 EN (reset) pin
```

**Kick pattern:** Alternating 0x55/0xAA on the WDI GPIO every 200ms. This prevents both stuck-at-0 and stuck-at-1 faults.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 2.3.1 | Wire MAX6818 per diagram above. Verify WDI GPIO toggles on oscilloscope: 200ms period, alternating 0x55/0xAA pattern. | Square wave at ~2.5Hz (200ms period). Logic levels clean (0V / 3.3V). | ☐ |
| 2.3.2 | Run system continuously for **60 seconds** with watchdog kick active. System should not reset. | No reset. Serial output continuous for 60 seconds. | ☐ |
| 2.3.3 | Enter test mode: stop watchdog kick. Set GPIO to static HIGH or LOW. | System continues briefly. | ☐ |
| 2.3.4 | Measure time from watchdog kick stop to ESP32 reset. | Reset occurs within **1.1 seconds** (MAX6818 timeout = 1.0s + startup). | ☐ |
| 2.3.5 | After reset, verify boot counter increments in NVS. Read NVS key "boot_count". | boot_count = previous + 1. | ☐ |
| 2.3.6 | Trigger 6 rapid resets within 10 minutes (stop WDT, wait for reset, restart WDT, repeat). Verify FAULT mode entered. | FAULT mode detected. System refuses to enable actuators. Log shows "FAULT: >5 resets in 10min". | ☐ |

### PASS Criteria — Gate 2

- [ ] Kill switch breaks power to actuators (multimeter verifies 0V at actuator supply when pressed)
- [ ] Sense wire GPIO reads HIGH (3.3V) when released, LOW (0V) when pressed
- [ ] E-Stop ISR response < **1ms** on ALL 10 oscilloscope measurements (target < 100µs)
- [ ] Hardware watchdog resets ESP32 within **1.1s** when kick stopped
- [ ] FAULT mode entered after 5+ rapid resets in 10 minutes
- [ ] Broken sense wire results in SAFE state (GPIO reads HIGH = switch released = system continues in safe mode)

**Sign-off:** _________________ **Date:** __________ **Engineer:** _________________

---

## Gate 3: Boot Sequence and Role Assignment

**Goal:** Load the full NEXUS boot sequence firmware and verify the timed milestone protocol works end-to-end.

### 3.1 ESP32 Boot Timing

**Objective:** Measure actual boot milestones against the specification targets.

**Setup:** Logic analyzer on UART1 TX (A/B differential pair). Capture entire boot sequence from power-on to OPERATIONAL.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.1.1 | Flash full NEXUS firmware. Power-cycle ESP32 with Jetson connected. | Boot begins. No panic. | ☐ |
| 3.1.2 | Measure time from power-on (3.3V rail rising) to DEVICE_IDENTITY (0x01) on UART1. | **< 30ms** (spec target: T+20ms). Measured: `____`ms. | ☐ |
| 3.1.3 | Measure time from power-on to AUTO_DETECT_RESULT (0x1B) on UART1. | **< 50ms** (spec target: T+30ms). Measured: `____`ms. | ☐ |
| 3.1.4 | Measure time from power-on to SELFTEST_RESULT (0x04) on UART1. | **< 70ms** (spec target: T+50ms). Measured: `____`ms. | ☐ |
| 3.1.5 | Verify SELFTEST_RESULT contains per-pin pass/fail for all configured pins. | JSON payload includes `"tests": [{"pin": 4, "status": "pass"}, ...]`. All pins pass. | ☐ |
| 3.1.6 | Wait for ROLE_ASSIGN (0x02) from Jetson. Verify ESP32 sends ROLE_ACK (0x03) with `"accepted": true`. | ROLE_ACK received within **100ms** of ROLE_ASSIGN. | ☐ |
| 3.1.7 | Measure time from power-on to OPERATIONAL state (first HEARTBEAT (0x05) sent). | **< 500ms** (spec target). Measured: `____`ms. | ☐ |

### 3.2 Jetson Boot Manager

**Objective:** Run the Jetson-side node manager script that discovers the ESP32, assigns it a role, and deploys a test reflex.

```bash
cd /jetson
python3 -m nexus_cognitive.node_manager --config tests/roles_test.json --serial /dev/ttyUSB0
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 3.2.1 | Start node manager. Verify it receives DEVICE_IDENTITY, AUTO_DETECT_RESULT, SELFTEST_RESULT in order. | Console output: `Node discovered: AA:BB:CC:DD:EE:FF`, `Auto-detect: OK`, `Self-test: PASSED`. | ☐ |
| 3.2.2 | Verify node manager reads role configuration from local JSON file. | Role config parsed. Pin assignments loaded. | ☐ |
| 3.2.3 | Node manager sends ROLE_ASSIGN with test role: LED blink on GPIO2 at 1Hz. | ROLE_ASSIGN sent. Log shows payload includes GPIO2 config. | ☐ |
| 3.2.4 | ESP32 responds with ROLE_ACK `"accepted": true`. | ROLE_ACK received by Jetson. Console confirms acceptance. | ☐ |
| 3.2.5 | Verify GPIO2 LED begins blinking at 1Hz on the ESP32 dev board. | LED blinks at 1Hz ± 5%. | ☐ |
| 3.2.6 | Node manager sends REFLEX_DEPLOY (0x09) with LED blink reflex bytecode. | REFLEX_DEPLOY sent. ACK received. | ☐ |
| 3.2.7 | Verify LED blink rate changes to the reflex-specified rate (e.g., 2Hz). | LED now blinks at 2Hz. Reflex is executing on VM. | ☐ |

### PASS Criteria — Gate 3

- [ ] DEVICE_IDENTITY within **30ms** of power-on
- [ ] AUTO_DETECT_RESULT within **50ms** of power-on
- [ ] SELFTEST_RESULT within **70ms** of power-on
- [ ] Full boot sequence (power-on to OPERATIONAL) within **500ms**
- [ ] ROLE_ASSIGN accepted and applied (GPIO2 responds to new role config)
- [ ] Reflex deploys and executes (LED blink rate changes)

**Sign-off:** _________________ **Date:** __________ **Engineer:** _________________

---

## Gate 4: VM and Reflex Execution

**Goal:** Verify all 32 VM opcodes produce correct results, the PID controller works, and safety invariants are enforced.

### 4.1 Opcode Validation

**Test strategy:** Deploy test bytecode via REFLEX_DEPLOY for each opcode category. Use READ_PIN to inject known test values, WRITE_PIN to capture outputs, and verify against expected results.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| **Stack Operations** | | | |
| 4.1.1 | PUSH_I8 42 → POP: stack depth returns to 0. | Stack empty after POP. No leak. | ☐ |
| 4.1.2 | PUSH_I8 1, PUSH_I8 2, DUP → stack: [1, 2, 2, 2]. Top = 2. | Stack depth = 4. Top two elements both 2. | ☐ |
| 4.1.3 | PUSH_I8 1, PUSH_I8 2, SWAP → stack: [1, 2] becomes [2, 1]. | Top = 1, second = 2. | ☐ |
| 4.1.4 | PUSH_I8 1, PUSH_I8 2, PUSH_I8 3, ROT → top three rotated. | Stack: [3, 1, 2] (top moved to bottom of trio). | ☐ |
| 4.1.5 | PUSH 257 values without POP. | VM **HALTS**. Stack overflow detected. estop_triggered = true. | ☐ |
| **Arithmetic** | | | |
| 4.1.6 | PUSH_F32 3.0, PUSH_F32 2.0, ADD_F → 5.0. | Result = 5.0 ± 0.001. | ☐ |
| 4.1.7 | PUSH_F32 10.0, PUSH_F32 3.0, DIV_F → 3.333... | Result ≈ 3.333. | ☐ |
| 4.1.8 | PUSH_F32 1.0, PUSH_F32 0.0, DIV_F → **0.0** (not NaN, not Inf). | Result = 0.0. No crash. VM continues. | ☐ |
| 4.1.9 | PUSH_F32 2.0, NEG_F → -2.0. PUSH_F32 -5.0, ABS_F → 5.0. | Results correct. | ☐ |
| 4.1.10 | PUSH_F32 7.0, PUSH_F32 3.0, CLAMP_F 0.0 5.0 → 5.0 (clamped). | Result = 5.0. | ☐ |
| 4.1.11 | PUSH_F32 -1.0, CLAMP_F 0.0 5.0 → 0.0 (clamped from below). | Result = 0.0. | ☐ |
| 4.1.12 | PUSH_F32 3.0, CLAMP_F 0.0 5.0 → 3.0 (within range, unchanged). | Result = 3.0. | ☐ |
| **Comparison** | | | |
| 4.1.13 | PUSH_F32 3.0, PUSH_F32 5.0, LT_F → 1 (true). | Result = 1. | ☐ |
| 4.1.14 | PUSH_F32 5.0, PUSH_F32 3.0, GT_F → 1 (true). | Result = 1. | ☐ |
| 4.1.15 | PUSH_F32 3.0, PUSH_F32 3.0, EQ_F → 1 (true). | Result = 1. | ☐ |
| **Control Flow** | | | |
| 4.1.16 | JUMP forward 16 bytes, PUSH_F32 99.0, WRITE_PIN test_output. Verify only one value written. | Single WRITE_PIN observed. JUMP skipped intermediate instructions. | ☐ |
| 4.1.17 | PUSH_I8 1, JUMP_IF_TRUE forward → branch taken. PUSH_I8 0, JUMP_IF_TRUE forward → branch NOT taken. | Correct branching for both true and false conditions. | ☐ |

### 4.2 PID_COMPUTE Test

**Objective:** Deploy a PID reflex and verify closed-loop tracking behavior.

**Test reflex (heading-hold simplified):**
```
READ_PIN 0          ; setpoint (from test fixture or hardcoded variable)
READ_PIN 1          ; input (actual heading from sensor)
PID_COMPUTE 0       ; PID instance 0 (Kp=1.2, Ki=0.05, Kd=0.3)
CLAMP_F -45.0 45.0  ; rudder range
WRITE_PIN 0         ; rudder output
```

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.2.1 | Deploy PID reflex. Set setpoint = 100.0. Set initial input = 0.0. | Output ramps toward 45.0 (clamped max). | ☐ |
| 4.2.2 | Slowly increase input from 0.0 to 100.0. | Output decreases toward 0.0 as error decreases. | ☐ |
| 4.2.3 | Step setpoint from 100.0 to 200.0. Observe output step response. | Output steps positive. Overshoot < **5%** of final value. Settling time < 2 seconds. | ☐ |
| 4.2.4 | Anti-windup test: hold error at maximum (input = 0, setpoint = 1000.0) for **60 seconds**. Then restore input = 1000.0. | Integral clamps to integral_limit (1500.0). No runaway. Recovery within 2s of error reversal. | ☐ |

### 4.3 Safety Invariant Tests

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 4.3.1 | **Stack overflow:** Deploy reflex that pushes 257 values without popping. | VM **HALTS** immediately on 257th push. Actuator outputs forced to safe values. No crash. | ☐ |
| 4.3.2 | **Cycle budget:** Deploy reflex with infinite loop (`JUMP 0` → `JUMP 0` → ...). | VM **HALTS** at exactly **10,000 cycles**. Log shows "CYCLE_BUDGET_EXCEEDED". | ☐ |
| 4.3.3 | **Division by zero:** `PUSH_F32 1.0, PUSH_F32 0.0, DIV_F`. | Result = **0.0** (not NaN, not Infinity). VM continues normally. | ☐ |
| 4.3.4 | **Actuator clamping:** Deploy reflex with `PUSH_F32 999.0, WRITE_PIN 0` where pin 0 has max = 45.0. | Output clamped to **45.0** after VM execution completes. | ☐ |
| 4.3.5 | **All three safety violations** in sequence: cycle budget → stack overflow → div-by-zero. | Each HALT is independent. No corruption between tests. System recovers cleanly each time. | ☐ |

### PASS Criteria — Gate 4

- [ ] All **32 opcodes** produce correct results (verified per-category above)
- [ ] PID step response overshoot < **5%**
- [ ] PID anti-windup holds integral within limits over 60s sustained error
- [ ] VM HALTS on stack overflow (257th push)
- [ ] VM HALTS at exactly 10,000 cycles
- [ ] Division by zero returns 0.0, not NaN
- [ ] All actuator outputs clamped to configured min/max after VM execution

**Sign-off:** _________________ **Date:** __________ **Engineer:** _________________

---

## Gate 5: Full System Integration

**Goal:** Connect all subsystems — ESP32 limb nodes, Jetson brain, RS-422 bus — and run end-to-end tests including observation recording and (optionally) cloud connectivity.

### 5.1 Multi-Node Observation Recording

**Setup:** Connect 2+ ESP32 nodes to the Jetson via RS-422 bus. Each node has an assigned role with sensors configured.

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 5.1.1 | Power on Jetson. Start node manager. Verify all nodes discovered. | Console shows 2+ nodes with unique MAC addresses. All in OPERATIONAL state. | ☐ |
| 5.1.2 | Jetson sends OBS_RECORD_START (0x0B) to all nodes: 100Hz, 30 seconds. | All nodes ACK. Recording begins. | ☐ |
| 5.1.3 | Wait 30 seconds. Jetson sends OBS_RECORD_STOP (0x0C). | Recording stops. Nodes report `frames_recorded`. | ☐ |
| 5.1.4 | Jetson sends OBS_DUMP_HEADER (request via message type). Verify response. | Header received: contains `frame_count`, `start_time`, `end_time`, `crc32`. | ☐ |
| 5.1.5 | Jetson requests OBS_DUMP_CHUNK for all frames. Verify data integrity. | Each chunk CRC-32 matches. No corrupted frames. | ☐ |
| 5.1.6 | Verify sample count: 100Hz × 30s = **3000 samples** per node. | `frame_count` = 3000 ± 5 (allowing for timer drift). | ☐ |
| 5.1.7 | Verify data timestamps are monotonically increasing within each node. | No timestamp regressions. Maximum gap < 15ms (100Hz = 10ms period + jitter). | ☐ |
| 5.1.8 | Run for 5 minutes continuous recording. Verify no buffer overflow or frame drops. | Total frames ≈ 30,000. Zero drops reported in OBS_DUMP_HEADER. | ☐ |

### 5.2 Cloud Connectivity (If Available)

| Step | Action | Expected Result | Pass/Fail |
|------|--------|----------------|-----------|
| 5.2.1 | Configure MQTT broker endpoint in Jetson config. Start MQTT bridge. | `MQTT connected to broker.example.com:8883` logged. TLS handshake successful. | ☐ |
| 5.2.2 | Publish telemetry to `nexus/telemetry/{node_id}`. Verify on MQTT subscriber (separate machine). | Telemetry JSON received. All fields present and well-formed. | ☐ |
| 5.2.3 | Upload observation data to cloud endpoint (if configured). | Upload succeeds. Server responds HTTP 200. Round-trip latency < **60 seconds**. | ☐ |
| 5.2.4 | Verify cloud result download: trigger CLOUD_CONTEXT_REQUEST (0x19), wait for CLOUD_RESULT (0x1A). | CLOUD_RESULT received. Payload contains expected response data. | ☐ |

### PASS Criteria — Gate 5

- [ ] All nodes discovered and in OPERATIONAL state
- [ ] 30-second observation recording at 100Hz: **3000 samples ± 5**
- [ ] All OBS_DUMP_CHUNK CRC-32 checks pass (zero corrupted frames)
- [ ] 5-minute continuous recording: zero frame drops
- [ ] (Optional) MQTT telemetry publish verified on remote subscriber
- [ ] (Optional) Cloud round-trip < 60 seconds

**Sign-off:** _________________ **Date:** __________ **Engineer:** _________________

---

## Final Sign-Off Summary

| Gate | Description | Status | Sign-Off | Date |
|------|-------------|--------|----------|------|
| 0 | Board Bring-Up (No NEXUS Firmware) | ☐ PASS / ☐ FAIL | | |
| 1 | Serial Communication (ESP32 ↔ Jetson) | ☐ PASS / ☐ FAIL | | |
| 2 | Kill Switch and Safety Hardware | ☐ PASS / ☐ FAIL | | |
| 3 | Boot Sequence and Role Assignment | ☐ PASS / ☐ FAIL | | |
| 4 | VM and Reflex Execution | ☐ PASS / ☐ FAIL | | |
| 5 | Full System Integration | ☐ PASS / ☐ FAIL | | |

**Lead Engineer Final Approval:** _________________ **Date:** __________

**Notes:**
```
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
```

---

*This checklist is a living document. Update pin assignments and voltage thresholds if your hardware revision differs from the reference design. Every modification must be reviewed by the lead engineer.*
