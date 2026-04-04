# The Simplest NEXUS System You Could Build Tomorrow

**A Practical, 7-Day Build Guide for a Minimum Viable NEXUS**

> This is NOT the full NEXUS. The full system has 32 opcodes, RS-422 serial at 921,600 baud, COBS framing, CRC-16 verification, 28 message types, a 12-parameter trust algorithm with 6 autonomy levels, and a Jetson Orin Nano running Qwen2.5-Coder-7B at Q4_K_M quantization. This guide strips all of that down to the absolute minimum that still embodies the NEXUS architecture — and shows you how to build it in a week with $60 of hardware and free software.

---

## Table of Contents

1. [The Minimum Viable NEXUS](#1-the-minimum-viable-nexus)
2. [The Glue Architecture](#2-the-glue-architecture)
3. [Step-by-Step Build Guide (7 Days)](#3-step-by-step-build-guide-7-days)
4. [What You Learn From This](#4-what-you-learn-from-this)
5. [From Minimum Viable to Production NEXUS](#5-from-minimum-viable-to-production-nexus)
6. [The "A2A Tomorrow" Variant](#6-the-a2a-tomorrow-variant)

---

## 1. The Minimum Viable NEXUS

### What NEXUS Actually Is (In One Paragraph)

NEXUS is a distributed intelligence platform for physical machines where control logic is compiled into bytecode and executed on a virtual machine running on embedded hardware. The VM is supervised by a trust algorithm that measures observed reliability and gates the permitted autonomy level. A higher-tier AI agent observes the system's behavior, discovers patterns, and synthesizes new control programs. The key insight: intelligence is distributed to the periphery (like a ribosome translating mRNA), not centralized in a single brain. When the higher tiers fail, the periphery maintains safe control independently.

### Stripping It Down

The full NEXUS spec has 32 opcodes, 8-byte fixed instructions, Float32-only arithmetic, a 256-entry stack, RS-422 at 921,600 baud, COBS framing, CRC-16/CCITT-FALSE, 28 message types, a 12-parameter trust algorithm with 6 autonomy levels (L0–L5), a 4-tier safety system (hardware kill switch, firmware watchdog, supervisory state machine, application-level trust gating), a Jetson Orin Nano running a 7B LLM, and a full learning pipeline with 5 pattern discovery algorithms. That's months of work.

Here's what you can strip away and still call it NEXUS:

**What You MUST Keep:**

1. **A bytecode VM on embedded hardware.** This is non-negotiable. The VM is the security boundary. AI-generated code executes inside the VM, not as raw firmware. Without it, you're just running scripts on a microcontroller. But you don't need 32 opcodes — you need 5: `PUSH`, `ADD`, `SUB`, `LOAD`, `STORE`. That's enough to implement a proportional controller, read a sensor, and write an actuator. You don't need 8-byte fixed instructions — use a simple byte array with variable-length encoding. You don't need Float32-only — use Python floats. You don't need a 256-entry stack — use a Python list.

2. **Trust-gated autonomy.** The system must not execute arbitrary code just because an agent generated it. There must be a trust score that starts low, increases with observed good behavior, and decreases on anomalies. The ratio must be asymmetric — harder to earn trust than to lose it. But you don't need all 12 INCREMENTS parameters — you need 3: `alpha_gain`, `alpha_loss`, and `t_floor`. You don't need 6 autonomy levels — you need 2: "advisory" (suggest only) and "supervised" (execute with heartbeat monitoring).

3. **A learning/agent component.** Something that can observe the system's behavior and generate new control programs. In the MVP, this is an LLM API call (OpenAI, Claude, or a local model). The agent receives sensor data and the current VM program, and produces a new VM program or parameters. You don't need 5 pattern discovery algorithms — you need one prompt that says "here's the temperature history, suggest a better control program."

4. **Safety monitoring.** Something that can detect when the system is misbehaving and halt it. In the MVP, this is a watchdog timer on the microcontroller and a current limiter on the actuator power supply. You don't need 4 tiers of safety — you need the firmware watchdog and a hardware cutoff.

**What You Can Strip:**

- RS-422 and COBS/CRC framing → use UART with JSON (yes, JSON on serial — it's fine for learning)
- 32 opcodes → 5 opcodes
- 8-byte fixed instructions → variable-length byte arrays
- Jetson Orin Nano with local LLM → laptop with OpenAI API
- 12 trust parameters → 3 trust parameters
- 6 autonomy levels → 2 autonomy levels
- 4-tier safety system → watchdog + current limit
- 28 message types → 4 JSON message types
- Multi-reflex deployment → single reflex
- COLREGs compliance → none (not marine)
- 1ms tick rate → 1-second tick rate

**What the MVP Can Do:**

- Read a temperature sensor via the VM's LOAD opcode
- Compute a proportional control output via PUSH/ADD/SUB
- Write an output to a heater/fan via the STORE opcode
- Send sensor data to a laptop via JSON over serial
- Receive new VM programs from the laptop
- Reject new programs if trust score is too low
- Halt if the watchdog timer expires or current exceeds a limit
- Have an LLM agent observe temperature data and suggest control improvements

**What the MVP CANNOT Do (Be Honest):**

- This system is NOT safety-certified and should NOT control anything dangerous
- No CRC protection means corrupted serial data could deploy bad bytecode
- JSON on serial is too slow for real-time control (<100 Hz)
- Python on ESP32 has nondeterministic timing (no hard real-time guarantees)
- No multi-reflex coordination or variable namespace isolation
- No A/B testing framework
- No observation recording or pattern discovery
- The LLM-generated code has not been formally validated
- Trust score dynamics are simplified and may not reflect real-world behavior

### The Minimum Viable Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│  LAPTOP (Tier 2 cognitive — simplified)              │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Trust Score │  │  LLM Agent   │  │   Serial   │  │
│  │ (Python)    │←→│  (OpenAI)    │  │  Monitor   │  │
│  │ 3 params    │  │ reflex gen   │  │  (pyserial)│  │
│  └──────┬──────┘  └──────────────┘  └─────┬──────┘  │
│         │                                   │         │
│    USB-TTL / UART (115200 baud, JSON)       │         │
└─────────┼───────────────────────────────────┼─────────┘
          │                                   │
┌─────────┼───────────────────────────────────┼─────────┐
│  ESP32-S3 (Tier 1 reflex — simplified)     │         │
│         │                                   │         │
│  ┌──────┴──────┐  ┌──────────────┐  ┌─────┴──────┐  │
│  │  Bytecode   │  │   Safety     │  │   Serial   │  │
│  │  VM (5 ops) │  │   Monitor    │  │  Link      │  │
│  │ MicroPython │  │  Watchdog    │  │ (UART JSON)│  │
│  └──────┬──────┘  └──────────────┘  └────────────┘  │
│         │                                           │
│  ┌──────┴──────┐                                    │
│  │  Hardware   │  GPIO4: DS18B20 temp sensor        │
│  │  I/O        │  GPIO2: LED (actuator indicator)   │
│  │             │  GPIO15: MOSFET (heater control)    │
│  └─────────────┘                                    │
└──────────────────────────────────────────────────────┘
```

This architecture embodies every NEXUS principle in its simplest possible form: a bytecode VM on the edge, trust-gated code deployment, an AI agent that generates control programs, and safety monitoring that can halt the system independently.

---

## 2. The Glue Architecture

This section lists every library, every wire, every component, and every line of glue code you need. No abstractions. No "choose your own adventure." Here is the exact stack.

### Bill of Materials (Hardware)

| # | Component | Part / Spec | Qty | Est. Cost | Link (Generic) |
|---|-----------|-------------|-----|-----------|----------------|
| 1 | Microcontroller | ESP32-S3-DevKitC-1 (N8R8, 8MB flash, 8MB PSRAM) | 1 | $8 | espressif.com, Adafruit, M5Stack |
| 2 | Temperature sensor | DS18B20 waterproof probe (1-Wire) | 1 | $3 | Adafruit 381, Maxim Integrated |
| 3 | Resistor | 4.7kΩ (for DS18B20 pull-up) | 1 | $0.05 | Any electronics supplier |
| 4 | LED | 5mm red, with 220Ω current-limiting resistor | 1 | $0.10 | Any |
| 5 | N-channel MOSFET | IRLZ44N (logic-level, 47A, TO-220) | 1 | $1.50 | Digi-Key, Mouser |
| 6 | Power resistor | 10Ω 10W (as dummy heater load) | 1 | $1 | Any |
| 7 | Current sensor | ACS712-5A (Hall effect, analog output) | 1 | $2 | AliExpress, SparkFun |
| 8 | Breadboard | Half-size solderless breadboard | 1 | $3 | Any |
| 9 | Jumper wires | M-M, M-F, F-F assortment (40-pack) | 1 | $3 | Any |
| 10 | USB-C cable | For ESP32 programming and power | 1 | $3 | Any |
| 11 | USB-TTL adapter | CP2102 or CH340 (if ESP32 dev board lacks USB) | 1 | $4 | AliExpress |
| 12 | Power supply | 5V 3A USB-C wall adapter (for ESP32 + load) | 1 | $8 | Any |
| 13 | Optional: Laptop | Any computer running Python 3.10+ | 1 | (existing) | — |
| | | | | **Total: ~$37** | |

If you want to skip the heater hardware entirely and just use the LED as the "actuator" (which is perfectly valid for learning), drop items 5, 6, 7 and reduce cost to ~$21. The LED blinking at different rates IS a valid control output — it represents duty cycle control.

### Wiring Diagram (Explicit Pin Mapping)

```
ESP32-S3 DevKitC-1 Pin Connections:
─────────────────────────────────────

DS18B20 Temperature Sensor:
    VCC  (Red)    → 3.3V pin on ESP32
    GND  (Black)  → GND pin on ESP32
    DATA (Yellow) → GPIO4 (input, pulled up with 4.7kΩ to 3.3V)

LED (Actuator Indicator):
    Anode  (+)    → 220Ω resistor → GPIO2 (output)
    Cathode (-)   → GND

IRLZ44N MOSFET (Heater Control):
    Gate   (pin 1) → GPIO15 (output, PWM capable)
    Drain  (pin 2) → One terminal of 10Ω power resistor
    Source (pin 3) → GND
    Other terminal of power resistor → 5V (via external 5V supply recommended)
    NOTE: For safety, add a 100mA fuse in series with the 5V heater supply.

ACS712-5A Current Sensor:
    VCC    → 5V
    GND    → GND
    OUT    → GPIO34 (ADC1_CH6, analog input, 12-bit, 0-3.3V range)
    IP+    → (in series with heater positive supply)
    IP-    → (heater positive terminal)

Serial Connection to Laptop:
    ESP32 TX (GPIO43) → USB-TTL RX
    ESP32 RX (GPIO44) → USB-TTL TX
    ESP32 GND         → USB-TTL GND
    (If using dev board's built-in USB-C, no external wiring needed)
```

### Software Stack (Specific Versions)

**ESP32-S3 Firmware (MicroPython):**

| Library | Version | Purpose |
|---------|---------|---------|
| MicroPython | v1.24.1 (ESP32-S3 variant) | Runtime on ESP32 |
| `machine` (builtin) | — | Pin, ADC, Timer, UART, WDT |
| `onewire` | MicroPython builtin (since 1.17) | DS18B20 1-Wire protocol |
| `ds18x20` | MicroPython builtin (since 1.17) | DS18B20 temperature conversion |
| `ujson` | MicroPython builtin | JSON encode/decode on serial |
| `uctypes` | MicroPython builtin | (Optional) Byte array as struct for bytecode |
| `time` | MicroPython builtin | `ticks_ms()` for timing |

Flashing MicroPython onto ESP32-S3: Download `ESP32_GENERIC_S3-20240622-v1.24.1.bin` from micropython.org, flash with `esptool.py`:
```bash
pip install esptool==4.8.0
esptool.py --chip esp32s3 -p /dev/ttyUSB0 -b 460800 \
    write_flash -z 0x0 ESP32_GENERIC_S3-20240622-v1.24.1.bin
```

**Laptop Software (Python 3.10+):**

| Library | Version | Install | Purpose |
|---------|---------|---------|---------|
| Python | 3.10+ | system | Runtime on laptop |
| `pyserial` | 3.5 | `pip install pyserial==3.5` | Serial communication with ESP32 |
| `openai` | 1.50+ | `pip install openai` | LLM API for reflex generation |
| `matplotlib` | 3.9+ | `pip install matplotlib` | Trust score visualization |
| `rich` | 13.8+ | `pip install rich` | Pretty console output |

Alternative: Use `anthropic` library instead of `openai` for Claude API. The agent prompt is the same structure either way.

### Communication Protocol: JSON over UART

The full NEXUS uses RS-422 at 921,600 baud with COBS framing and CRC-16. We're using UART at 115,200 baud with JSON and newline delimiters. Here's the explicit wire format:

```
Each message is a single line of JSON terminated by '\n' (0x0A).
Maximum message length: 512 bytes (well under UART buffer limits).
No CRC. No COBS. No escape characters. Just JSON.

Message format:
{"type": "<msg_type>", "ts": <timestamp_ms>, "data": {...}}

Where msg_type is one of:
  "heartbeat"   — ESP32 → Laptop, every 1000ms, no data payload
  "telemetry"   — ESP32 → Laptop, sensor readings
  "deploy"      — Laptop → ESP32, new bytecode program
  "command"     — Laptop → ESP32, direct actuator command (safety override)
  "ack"         — Either direction, acknowledges previous message
  "safety"      — ESP32 → Laptop, safety event notification
  "trust"       — Laptop → ESP32, current trust level and autonomy level
```

Concrete message examples:

```json
// ESP32 sends telemetry every 1 second
{"type": "telemetry", "ts": 17234, "data": {"temperature_c": 23.4, "output_pct": 45.2, "current_ma": 312}}

// Laptop deploys new bytecode program
{"type": "deploy", "ts": 17301, "data": {"program": [1, 2300, 1, 2500, 2, 4, 5, 2, 6], "trust_required": 0.3, "name": "temp_control_v2"}}

// ESP32 acknowledges deployment
{"type": "ack", "ts": 17302, "data": {"original_ts": 17301, "status": "accepted", "reason": "trust_sufficient"}}

// ESP32 reports safety event
{"type": "safety", "ts": 18001, "data": {"event": "overcurrent", "current_ma": 5200, "threshold_ma": 5000}}

// Laptop sends trust level update
{"type": "trust", "ts": 18500, "data": {"trust_score": 0.42, "autonomy_level": "supervised", "subsystem": "heater"}}
```

### The Simplified Trust Algorithm

The full INCREMENTS algorithm has 12 parameters, 15 event types, 6 autonomy levels, streak bonuses, subsystem multipliers, reset logic, and grace periods. Here's the stripped-down version — 3 parameters, 3 event types, 2 autonomy levels:

```python
class SimpleTrust:
    """Minimum viable trust score. 3 parameters. 2 levels."""

    def __init__(self, alpha_gain=0.01, alpha_loss=0.1, t_floor=0.1):
        self.trust = t_floor        # Start at floor
        self.alpha_gain = alpha_gain
        self.alpha_loss = alpha_loss
        self.t_floor = t_floor
        self.window_events = []     # Events in current 1-hour window
        self.autonomy_level = "advisory"  # "advisory" or "supervised"

    def record_event(self, event_type: str):
        """Record an event. Types: 'good', 'bad', 'neutral'."""
        self.window_events.append(event_type)

    def evaluate_window(self) -> dict:
        """Evaluate current window and update trust. Call every hour."""
        n_good = self.window_events.count("good")
        n_bad = self.window_events.count("bad")

        if n_bad > 0:
            # Penalty: trust decreases proportional to current trust
            delta = -self.alpha_loss * self.trust
        elif n_good > 0:
            # Gain: trust approaches 1.0 asymptotically
            delta = self.alpha_gain * (1.0 - self.trust)
        else:
            # Decay: trust drifts toward floor
            delta = -0.001 * (self.trust - self.t_floor)

        self.trust = max(self.t_floor, min(1.0, self.trust + delta))
        self.window_events = []

        # Update autonomy level
        if self.trust >= 0.3:
            self.autonomy_level = "supervised"
        else:
            self.autonomy_level = "advisory"

        return {
            "trust_score": round(self.trust, 4),
            "autonomy_level": self.autonomy_level,
            "delta": round(delta, 6),
            "n_good": n_good,
            "n_bad": n_bad
        }
```

Key difference from full INCREMENTS: the simplified version uses a 10:1 loss-to-gain ratio instead of 25:1, which means trust builds faster for the learning phase. This is intentional — you're building the MVP to learn, not to certify. When you upgrade to production, you'll tighten the ratio.

---

## 3. Step-by-Step Build Guide (7 Days)

### Day 1: ESP32 Setup + Basic I/O

**Objective:** Flash MicroPython onto the ESP32-S3, read a DS18B20 temperature sensor, blink an LED. No VM yet, no serial protocol yet. Just prove you can talk to hardware.

**Specific Steps:**

1. Install `esptool` on your laptop: `pip install esptool==4.8.0`
2. Download the MicroPython firmware binary from micropython.org (ESP32-S3 variant, latest stable)
3. Hold the BOOT button on the ESP32 dev board, press EN, release BOOT. The ESP32 enters download mode.
4. Flash the firmware:
   ```bash
   esptool.py --chip esp32s3 -p /dev/ttyUSB0 -b 460800 \
       write_flash -z 0x0 ESP32_GENERIC_S3-20240622-v1.24.1.bin
   ```
5. Open Thonny IDE (thonny.org), connect to the ESP32 via serial, verify the REPL works. Type `import machine; machine.freq()` — should return `240000000`.
6. Wire the DS18B20 to GPIO4 with 4.7kΩ pull-up. Wire the LED to GPIO2 with 220Ω resistor.
7. Create `main.py` on the ESP32:

```python
# main.py — Day 1: Read temperature, blink LED
import machine
import onewire
import ds18x20
import time

# --- Hardware Setup ---
# DS18B20 on GPIO4
ow = onewire.OneWire(machine.Pin(4))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()
print(f"Found {len(sensors)} temperature sensor(s)")

# LED on GPIO2
led = machine.Pin(2, machine.Pin.OUT)

# --- Main Loop ---
while True:
    ds.convert_temp()          # Start conversion (takes ~750ms)
    time.sleep_ms(750)         # Wait for conversion
    for s in sensors:
        temp_c = ds.read_temp(s)
        print(f"Temperature: {temp_c:.2f} °C")

        # Blink LED faster when hotter (proportional to temperature)
        blink_rate = max(50, int(500 - temp_c * 15))  # ms between blinks
        led.on()
        time.sleep_ms(blink_rate // 2)
        led.off()
        time.sleep_ms(blink_rate // 2)

    time.sleep_ms(250)
```

**Expected Output:**
```
Found 1 temperature sensor(s)
Temperature: 22.45 °C
Temperature: 22.47 °C
Temperature: 22.50 °C
```
The LED should blink — faster when you warm the sensor (pinch it with your fingers), slower when it's cool.

**How to Test It:**
- Verify temperature readings are reasonable (15–30°C at room temperature)
- Pinch the DS18B20 probe with your fingers for 10 seconds — temperature should rise 2–5°C
- Verify LED blink rate changes visibly with temperature
- Unplug the sensor — the script should handle the error gracefully (or crash with a clear error, which is fine for Day 1)

---

### Day 2: Simple Bytecode Interpreter (5 Opcodes)

**Objective:** Build a minimal stack-based bytecode VM in MicroPython that can execute a simple proportional control program. 5 opcodes: PUSH, ADD, SUB, LOAD, STORE. The VM reads a temperature sensor (LOAD) and writes a heater output (STORE).

**Specific Steps:**

1. Understand the opcode encoding. Each instruction is 4 bytes:
   ```
   Byte 0: Opcode (0=PUSH, 1=ADD, 2=SUB, 3=LOAD, 4=STORE)
   Byte 1-3: Operand (uint32 big-endian, only used by PUSH, LOAD, STORE)
   ```
2. Create `vm.py` on the ESP32:

```python
# vm.py — Day 2: Minimal bytecode VM (5 opcodes)
#
# Instruction format: 4 bytes
#   [opcode: u8] [operand: u24 (big-endian)]
#
# Opcodes:
#   0x00 = PUSH <value>    Push a float32 onto the stack
#   0x01 = ADD             Pop two, push sum
#   0x02 = SUB             Pop two, push second - first
#   0x03 = LOAD <addr>     Read sensor/input register, push value
#   0x04 = STORE <addr>    Pop value, write to actuator/output register

import struct

# Opcode constants
OP_PUSH  = 0x00
OP_ADD   = 0x01
OP_SUB   = 0x02
OP_LOAD  = 0x03
OP_STORE = 0x04

class NexusVM:
    """Minimal NEXUS bytecode VM. 5 opcodes. Stack machine."""

    def __init__(self, max_stack=64, max_program=256):
        self.stack = []
        self.max_stack = max_stack
        self.registers = [0.0] * 16  # 16 registers (I/O mapped)
        self.pc = 0                   # Program counter (instruction index)
        self.program = bytearray()
        self.max_program = max_program
        self.halted = False
        self.cycle_count = 0
        self.max_cycles = 1000        # Safety: abort after 1000 instructions

    def load_program(self, bytecode: bytes):
        """Load a bytecode program. Validates length."""
        if len(bytecode) > self.max_program:
            raise ValueError(f"Program too large: {len(bytecode)} > {self.max_program}")
        if len(bytecode) % 4 != 0:
            raise ValueError(f"Program not 4-byte aligned: {len(bytecode)} bytes")
        self.program = bytearray(bytecode)
        self.pc = 0
        self.halted = False
        self.stack = []
        self.cycle_count = 0

    def execute_tick(self):
        """Execute one tick of the VM (runs until HALT or cycle limit)."""
        self.halted = False
        self.cycle_count = 0

        while self.pc < len(self.program) and not self.halted:
            # Fetch
            opcode = self.program[self.pc]
            # Decode operand (3 bytes big-endian)
            operand = (self.program[self.pc + 1] << 16) | \
                      (self.program[self.pc + 2] << 8)  | \
                       self.program[self.pc + 3]

            # Execute
            if opcode == OP_PUSH:
                value = struct.unpack('>f', struct.pack('>I', operand))[0]
                self._push(value)

            elif opcode == OP_ADD:
                b = self._pop()
                a = self._pop()
                self._push(a + b)

            elif opcode == OP_SUB:
                b = self._pop()
                a = self._pop()
                self._push(a - b)

            elif opcode == OP_LOAD:
                if operand >= 16:
                    self._halt("LOAD: register out of range")
                    return
                self._push(self.registers[operand])

            elif opcode == OP_STORE:
                if operand >= 16:
                    self._halt("STORE: register out of range")
                    return
                self.registers[operand] = self._pop()

            else:
                self._halt(f"Unknown opcode: {opcode:#04x}")
                return

            self.pc += 4
            self.cycle_count += 1

            if self.cycle_count >= self.max_cycles:
                self._halt("Cycle limit exceeded")
                return

    def _push(self, value):
        if len(self.stack) >= self.max_stack:
            self._halt("Stack overflow")
            return
        self.stack.append(value)

    def _pop(self):
        if len(self.stack) == 0:
            self._halt("Stack underflow")
            return 0.0
        return self.stack.pop()

    def _halt(self, reason):
        self.halted = True
        self.halt_reason = reason


def make_push(value: float) -> bytes:
    """Helper: encode a PUSH instruction."""
    int_val = struct.unpack('>I', struct.pack('>f', value))[0]
    return bytes([OP_PUSH, (int_val >> 16) & 0xFF, (int_val >> 8) & 0xFF, int_val & 0xFF])

def make_load(addr: int) -> bytes:
    return bytes([OP_LOAD, 0, 0, addr])

def make_store(addr: int) -> bytes:
    return bytes([OP_STORE, 0, 0, addr])

def make_add() -> bytes:
    return bytes([OP_ADD, 0, 0, 0])

def make_sub() -> bytes:
    return bytes([OP_SUB, 0, 0, 0])
```

3. Create `main.py` that uses the VM to do proportional temperature control:

```python
# main.py — Day 2: VM-based proportional temperature control
from vm import NexusVM, make_push, make_load, make_store, make_sub
import onewire, ds18x20, machine, time, struct

# Hardware
ow = onewire.OneWire(machine.Pin(4))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()
led = machine.Pin(2, machine.Pin.OUT)

# Create VM
vm = NexusVM()

# Register mapping:
#   Reg 0 = temperature reading (C)
#   Reg 1 = heater output (0.0 - 100.0)
#   Reg 2 = setpoint (C)

# Build program: proportional control
#   LOAD 0         ; push temperature
#   PUSH 25.0      ; push setpoint
#   SUB            ; error = setpoint - temperature
#   PUSH 10.0      ; proportional gain
#   ADD            ; (placeholder: multiply would be needed)
#   STORE 1        ; write output
#
# Note: We don't have MUL, so this is just error + 10.
# That's fine — it's enough to see the VM working.
# The program exercises all 5 opcodes.

program = bytes([
    # LOAD 0 (read temperature)
    0x03, 0x00, 0x00, 0x00,
    # PUSH 25.0 (setpoint, float32 = 0x41C80000)
    0x00, 0x41, 0xC8, 0x00,
    # SUB (error = setpoint - temp)
    0x02, 0x00, 0x00, 0x00,
    # PUSH 10.0 (gain offset, float32 = 0x41200000)
    0x00, 0x41, 0x20, 0x00,
    # ADD (output = error + gain)
    0x01, 0x00, 0x00, 0x00,
    # STORE 1 (write output register)
    0x04, 0x00, 0x00, 0x01,
])

vm.load_program(program)

# Control loop
while True:
    # Read sensor into register 0
    ds.convert_temp()
    time.sleep_ms(750)
    temp = ds.read_temp(sensors[0])
    vm.registers[0] = temp

    # Execute VM tick
    vm.execute_tick()

    if vm.halted:
        print(f"VM HALTED: {vm.halt_reason}")
        break

    # Read output from register 1
    output = vm.registers[1]
    output_clamped = max(0.0, min(100.0, output))
    print(f"Temp: {temp:.2f}C  Output: {output_clamped:.1f}%  Cycles: {vm.cycle_count}")

    # Blink LED proportional to output
    led.value(1)
    time.sleep_ms(int(output_clamped * 10))
    led.value(0)
    time.sleep_ms(int((100 - output_clamped) * 10))

    time.sleep_ms(500)
```

**Expected Output:**
```
Temp: 22.45C  Output: 12.6%  Cycles: 6
Temp: 22.47C  Output: 12.5%  Cycles: 6
```
The VM executes 6 instructions per tick, always produces a valid output (may be negative, but gets clamped), and never crashes (the safety checks work).

**How to Test It:**
- Change the setpoint from 25.0 to 30.0 (replace `0x41, 0xC8, 0x00` with `0x41, 0xF0, 0x00`) — output should increase
- Disconnect the sensor — the VM should still execute (register 0 stays at last value)
- Create a program with a stack underflow (two SUBs in a row) — verify the VM halts gracefully with "Stack underflow"
- Create a program with 250 instructions — verify the cycle limit catches it

---

### Day 3: Serial Communication (ESP32 ↔ Laptop)

**Objective:** Establish bidirectional JSON communication between the ESP32 and your laptop over UART. The ESP32 sends telemetry (temperature + output) every second. The laptop displays it and can send commands.

**Specific Steps:**

1. Wire UART: ESP32 TX (GPIO43) to USB-TTL RX, ESP32 RX (GPIO44) to USB-TTL TX, GND to GND. Or use the dev board's built-in USB-C.
2. Create `serial_link.py` on the ESP32:

```python
# serial_link.py — Day 3: JSON serial communication
import machine, ujson, time
from vm import NexusVM

class SerialLink:
    """JSON-over-UART communication for NEXUS MVP."""

    def __init__(self, uart_id=0, baud=115200, tx_pin=43, rx_pin=44):
        self.uart = machine.UART(uart_id, baudrate=baud, tx=tx_pin, rx=rx_pin,
                                  timeout_char=100)
        self.msg_buffer = ""
        self.seq = 0

    def send(self, msg_type: str, data: dict = None):
        """Send a JSON message."""
        self.seq += 1
        msg = {
            "type": msg_type,
            "ts": time.ticks_ms() & 0xFFFF,
            "seq": self.seq,
            "data": data or {}
        }
        line = ujson.dumps(msg) + "\n"
        self.uart.write(line.encode())

    def receive(self) -> dict or None:
        """Non-blocking receive. Returns parsed message or None."""
        while self.uart.any():
            ch = self.uart.read(1).decode()
            if ch == "\n":
                if self.msg_buffer.strip():
                    try:
                        return ujson.loads(self.msg_buffer)
                    except ValueError:
                        self.send("safety", {"event": "parse_error"})
                self.msg_buffer = ""
            else:
                self.msg_buffer += ch
        return None
```

3. Update `main.py` to use the serial link:

```python
# main.py — Day 3: Full system with serial link
from serial_link import SerialLink
from vm import NexusVM
import onewire, ds18x20, machine, time

# Hardware
ow = onewire.OneWire(machine.Pin(4))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()
led = machine.Pin(2, machine.Pin.OUT)

# Serial link
link = SerialLink()
link.send("heartbeat", {"msg": "NEXUS MVP online"})

# VM with default program
vm = NexusVM()
# (same program as Day 2 — proportional control)
default_program = bytes([0x03,0,0,0, 0x00,0x41,0xC8,0, 0x02,0,0,0, 0x00,0x41,0x20,0, 0x01,0,0,0, 0x04,0,0,1])
vm.load_program(default_program)

# Trust state (received from laptop)
trust_level = "advisory"
trust_required = 0.3

last_heartbeat = time.ticks_ms()

while True:
    # Send telemetry every 1 second
    if time.ticks_diff(time.ticks_ms(), last_heartbeat) >= 1000:
        ds.convert_temp()
        time.sleep_ms(750)
        temp = ds.read_temp(sensors[0])
        vm.registers[0] = temp
        vm.execute_tick()
        output = max(0.0, min(100.0, vm.registers[1]))
        link.send("telemetry", {"temperature_c": round(temp, 2),
                                  "output_pct": round(output, 1),
                                  "vm_cycles": vm.cycle_count})
        last_heartbeat = time.ticks_ms()

    # Process incoming messages
    msg = link.receive()
    if msg:
        if msg["type"] == "deploy":
            # Laptop wants to deploy new bytecode
            program_bytes = bytes(msg["data"]["program"])
            req_trust = msg["data"].get("trust_required", 0.3)
            if trust_level == "supervised":
                vm.load_program(program_bytes)
                link.send("ack", {"original_ts": msg["ts"],
                                   "status": "accepted",
                                   "reason": "trust_sufficient"})
                link.send("safety", {"event": "program_deployed",
                                      "name": msg["data"].get("name", "unnamed"),
                                      "size": len(program_bytes)})
            else:
                link.send("ack", {"original_ts": msg["ts"],
                                   "status": "rejected",
                                   "reason": "trust_insufficient"})
                link.send("safety", {"event": "deploy_blocked",
                                      "trust_level": trust_level,
                                      "required": req_trust})

        elif msg["type"] == "trust":
            trust_level = msg["data"].get("autonomy_level", trust_level)
            link.send("ack", {"original_ts": msg["ts"], "status": "ok"})

        elif msg["type"] == "command":
            # Direct actuator control (safety override)
            output = msg["data"].get("output_pct", 0)
            led.value(1 if output > 50 else 0)
            link.send("ack", {"original_ts": msg["ts"], "status": "executed"})

    # VM halted?
    if vm.halted:
        link.send("safety", {"event": "vm_halted", "reason": vm.halt_reason})
        # Reload default program as failsafe
        vm.load_program(default_program)
```

4. Create `laptop_monitor.py` on your laptop:

```python
#!/usr/bin/env python3
"""laptop_monitor.py — Day 3: Laptop-side serial monitor"""
import serial
import json
import time
import sys

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)

def send(msg_type, data=None):
    msg = {"type": msg_type, "ts": int(time.time() * 1000) % 0xFFFF, "data": data or {}}
    ser.write((json.dumps(msg) + "\n").encode())

# Send trust level
send("trust", {"trust_score": 0.35, "autonomy_level": "supervised"})

print("NEXUS MVP Monitor — Press Ctrl+C to exit")
print("=" * 60)

try:
    while True:
        line = ser.readline().decode().strip()
        if line:
            try:
                msg = json.loads(line)
                mtype = msg.get("type", "?")
                data = msg.get("data", {})

                if mtype == "telemetry":
                    print(f"[TELEM] {data['temperature_c']:6.2f}°C  "
                          f"Output: {data['output_pct']:5.1f}%  "
                          f"VM cycles: {data['vm_cycles']}")
                elif mtype == "heartbeat":
                    print(f"[HB]    {data}")
                elif mtype == "safety":
                    print(f"[SAFETY] *** {data} ***")
                elif mtype == "ack":
                    print(f"[ACK]   {data}")
                else:
                    print(f"[{mtype.upper():7s}] {data}")
            except json.JSONDecodeError:
                print(f"[RAW]   {line[:80]}")
except KeyboardInterrupt:
    print("\nExiting.")
    ser.close()
```

**Expected Output (Laptop):**
```
NEXUS MVP Monitor — Press Ctrl+C to exit
============================================================
[HB]    {'msg': 'NEXUS MVP online'}
[TELEM]  22.45°C  Output:  12.5%  VM cycles: 6
[TELEM]  22.47°C  Output:  12.5%  VM cycles: 6
```

**How to Test It:**
- Verify telemetry arrives every ~1 second
- Warm the sensor — temperature changes should appear on the laptop
- Send a deploy command from the laptop REPL: `send("deploy", {"program": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "name": "test"})` — verify the ESP32 accepts it
- Set trust to "advisory" — verify the ESP32 rejects deploy commands
- Unplug the serial cable — verify the ESP32 keeps running (the VM is independent)

---

### Day 4: Trust Score Implementation

**Objective:** Implement the simplified INCREMENTS trust algorithm on the laptop. The trust score updates based on telemetry from the ESP32. Deployments are gated by trust level.

**Specific Steps:**

1. Create `trust_engine.py` on the laptop:

```python
# trust_engine.py — Day 4: Simplified INCREMENTS trust algorithm
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TrustEvent:
    timestamp: datetime
    event_type: str  # "good", "bad", "neutral"
    description: str = ""

@dataclass
class TrustState:
    trust_score: float = 0.1
    autonomy_level: str = "advisory"
    hours_observed: float = 0.0
    consecutive_good_windows: int = 0
    total_good: int = 0
    total_bad: int = 0
    history: list = field(default_factory=list)

class TrustEngine:
    """
    Simplified INCREMENTS trust algorithm.

    Differences from full spec:
    - 3 parameters instead of 12 (alpha_gain, alpha_loss, t_floor)
    - 2 autonomy levels instead of 6 (advisory, supervised)
    - No streak bonus, no subsystem multiplier, no reset logic
    - 10:1 loss-to-gain ratio (full spec is 25:1)
    - 1-hour evaluation windows (same as full spec)
    """

    def __init__(self, alpha_gain=0.01, alpha_loss=0.10, t_floor=0.10):
        self.alpha_gain = alpha_gain
        self.alpha_loss = alpha_loss
        self.t_floor = t_floor
        self.state = TrustState()
        self.window_events: list[TrustEvent] = []

    def record_good(self, description=""):
        self.window_events.append(
            TrustEvent(datetime.now(), "good", description))

    def record_bad(self, description=""):
        self.window_events.append(
            TrustEvent(datetime.now(), "bad", description))

    def record_neutral(self, description=""):
        self.window_events.append(
            TrustEvent(datetime.now(), "neutral", description))

    def evaluate_window(self) -> dict:
        """Evaluate the current window and update trust. Call hourly."""
        n_good = sum(1 for e in self.window_events if e.event_type == "good")
        n_bad = sum(1 for e in self.window_events if e.event_type == "bad")
        T = self.state.trust_score

        if n_bad > 0:
            # Branch 2: Penalty
            delta = -self.alpha_loss * T
            self.state.consecutive_good_windows = 0
            self.state.total_bad += n_bad
        elif n_good > 0:
            # Branch 1: Net positive (gain approaches 1.0 asymptotically)
            delta = self.alpha_gain * (1.0 - T)
            self.state.consecutive_good_windows += 1
            self.state.total_good += n_good
        else:
            # Branch 3: Decay toward floor
            delta = -0.001 * (T - self.t_floor)
            self.state.consecutive_good_windows = 0

        T_new = max(self.t_floor, min(1.0, T + delta))

        result = {
            "trust_before": round(T, 4),
            "trust_after": round(T_new, 4),
            "delta": round(delta, 6),
            "n_good": n_good,
            "n_bad": n_bad,
            "autonomy_level": self._compute_level(T_new)
        }

        self.state.trust_score = T_new
        self.state.autonomy_level = result["autonomy_level"]
        self.state.hours_observed += 1.0
        self.state.history.append(result)
        self.window_events = []

        return result

    def _compute_level(self, trust: float) -> str:
        """Map trust score to autonomy level."""
        if trust >= 0.3:
            return "supervised"
        else:
            return "advisory"

    def should_allow_deploy(self, required_trust: float = 0.3) -> tuple:
        """Check if deployment is allowed at current trust level."""
        allowed = self.state.trust_score >= required_trust
        reason = "trust_sufficient" if allowed else "trust_insufficient"
        return allowed, reason
```

2. Integrate trust into `laptop_monitor.py`:

```python
# In laptop_monitor.py, add trust evaluation logic:
from trust_engine import TrustEngine

trust = TrustEngine()

# In the telemetry handler:
if mtype == "telemetry":
    temp = data["temperature_c"]
    output = data["output_pct"]
    # Good event: output is reasonable (not extreme)
    if 0 <= output <= 100 and 10 < temp < 40:
        trust.record_good(f"normal_operation t={temp}")
    # Bad event: output is at limits (possible control issue)
    elif output >= 99.0 or output <= 1.0:
        trust.record_bad(f"output_saturated output={output}")

# Add hourly evaluation (or evaluate every 60 telemetry messages for testing):
if telemetry_count % 60 == 0:
    result = trust.evaluate_window()
    print(f"[TRUST] {result['trust_before']:.3f} -> {result['trust_after']:.3f}  "
          f"Level: {result['autonomy_level']}  "
          f"(+{result['n_good']} good, -{result['n_bad']} bad)")

    # Send trust update to ESP32
    send("trust", {"trust_score": trust.state.trust_score,
                   "autonomy_level": trust.state.autonomy_level})
```

**Expected Output:**
```
[TELEM]  22.45°C  Output:  12.5%  VM cycles: 6
...
[TRUST] 0.1000 -> 0.1089  Level: advisory  (+58 good, -2 bad)
[TRUST] 0.1089 -> 0.1172  Level: advisory  (+60 good, -0 bad)
[TRUST] 0.1172 -> 0.1248  Level: advisory  (+59 good, -1 bad)
...
[TRUST] 0.2890 -> 0.2953  Level: advisory  (+60 good, -0 bad)
[TRUST] 0.2953 -> 0.3010  Level: supervised  (+60 good, -0 bad)
```

**How to Test It:**
- Run for 60+ telemetry messages — trust should increase from 0.1 toward 0.3
- Verify autonomy level transitions from "advisory" to "supervised"
- After reaching "supervised," send a deploy command — verify it's accepted
- Disconnect the sensor to trigger a "bad" event — verify trust decreases
- Note: at 10:1 ratio, one bad event wipes ~10 good events. This is intentional.

---

### Day 5: LLM Integration (Agent Generates Bytecode)

**Objective:** Connect an LLM (OpenAI GPT-4o-mini or Claude Haiku) to the system. The agent receives telemetry history and generates new VM bytecode programs. The generated code is validated by the trust system before deployment.

**Specific Steps:**

1. Create `reflex_agent.py` on the laptop:

```python
# reflex_agent.py — Day 5: LLM agent generates bytecode from natural language
from openai import OpenAI
import json

client = OpenAI()  # Uses OPENAI_API_KEY environment variable

SYSTEM_PROMPT = """You are a NEXUS reflex synthesis agent. You generate bytecode
programs for a minimal stack-based VM controlling a temperature system.

VM Architecture:
- Stack machine with 5 opcodes, 4-byte instructions
- Register mapping:
  Reg 0 = temperature reading (float, Celsius)
  Reg 1 = heater output (float, 0.0 to 100.0, percent)
  Reg 2 = setpoint (float, Celsius, stored by LOAD/STORE)

Opcode encoding (4 bytes each):
  PUSH <value>  = [0x00] [3 bytes float32 big-endian]
  ADD           = [0x01, 0x00, 0x00, 0x00]
  SUB           = [0x02, 0x00, 0x00, 0x00]
  LOAD <reg>    = [0x03, 0x00, 0x00, reg]
  STORE <reg>   = [0x04, 0x00, 0x00, reg]

Rules:
1. Every program must end by storing output to Reg 1
2. Output must be in range 0.0 to 100.0 (the VM clamps, but try)
3. Read temperature from Reg 0
4. You do NOT have MUL — use repeated ADD or SUB for scaling
5. Return ONLY a JSON object with "bytecode" (list of ints 0-255),
   "name" (string), and "description" (string)
6. Keep programs under 20 instructions (80 bytes) for safety

Response format:
{"bytecode": [0, 0, 0, 0, ...], "name": "program_name", "description": "what it does"}
"""

def generate_reflex(telemetry_history: list, user_request: str) -> dict:
    """Ask the LLM to generate a bytecode program."""

    # Build context from recent telemetry
    recent = telemetry_history[-10:]  # Last 10 readings
    context = "\n".join(
        f"  t={d['temperature_c']:.1f}C out={d['output_pct']:.1f}%"
        for d in recent
    )

    user_msg = f"""Current telemetry (last 10 readings):
{context}

Human request: {user_request}

Generate a bytecode program that addresses this request."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.3,  # Low temperature for deterministic code generation
        max_tokens=500
    )

    content = response.choices[0].message.content.strip()
    # Extract JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    result = json.loads(content)
    return result


def validate_bytecode(bytecode: list) -> tuple:
    """Basic validation of generated bytecode before deployment."""
    issues = []

    if len(bytecode) == 0:
        return False, ["empty program"]
    if len(bytecode) % 4 != 0:
        issues.append(f"not 4-byte aligned: {len(bytecode)} bytes")
    if len(bytecode) > 80:
        issues.append(f"too large: {len(bytecode)} bytes (max 80)")

    # Scan opcodes
    has_load = False
    has_store = False
    for i in range(0, len(bytecode) - 3, 4):
        opcode = bytecode[i]
        if opcode not in (0x00, 0x01, 0x02, 0x03, 0x04):
            issues.append(f"unknown opcode {opcode:#04x} at offset {i}")
        if opcode == 0x03:
            has_load = True
        if opcode == 0x04:
            has_store = True

    if not has_load:
        issues.append("no LOAD instruction (doesn't read sensors)")
    if not has_store:
        issues.append("no STORE instruction (doesn't write actuators)")

    return len(issues) == 0, issues
```

2. Integrate into the monitor — add a command to trigger reflex generation:

```python
# In laptop_monitor.py, add:
from reflex_agent import generate_reflex, validate_bytecode

telemetry_history = []

# In telemetry handler, accumulate history:
telemetry_history.append(data)

# Interactive command loop (in a separate thread or after Ctrl+C):
print("\nCommands: 'gen <request>', 'trust', 'deploy <name>', 'quit'")
while True:
    cmd = input("nexus> ").strip()
    if cmd.startswith("gen "):
        request = cmd[4:]
        print(f"Generating reflex for: {request}...")
        try:
            result = generate_reflex(telemetry_history, request)
            valid, issues = validate_bytecode(result["bytecode"])
            print(f"  Name: {result['name']}")
            print(f"  Description: {result['description']}")
            print(f"  Size: {len(result['bytecode'])} bytes")
            print(f"  Valid: {valid}")
            if issues:
                print(f"  Issues: {issues}")
            if valid:
                send("deploy", {"program": result["bytecode"],
                                "name": result["name"],
                                "trust_required": 0.3})
                trust.record_good(f"reflex_generated:{result['name']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            trust.record_bad(f"reflex_generation_failed:{e}")
    elif cmd == "trust":
        print(f"  Trust: {trust.state.trust_score:.4f}")
        print(f"  Level: {trust.state.autonomy_level}")
        print(f"  Hours: {trust.state.hours_observed}")
        print(f"  Good/Bad: {trust.state.total_good}/{trust.state.total_bad}")
```

**Expected Interaction:**
```
nexus> gen Make the heater proportional to how cold it is below 25 degrees
  Generating reflex for Make the heater proportional to how cold it is below 25 degrees...
  Name: proportional_below_setpoint
  Description: Reads temperature, subtracts from 25, if positive (below setpoint) uses as heater output
  Size: 24 bytes
  Valid: True
[ACK]   {'original_ts': 173, 'status': 'accepted', 'reason': 'trust_sufficient'}
```

**How to Test It:**
- Generate several different reflexes with natural language requests
- Verify the LLM produces valid JSON with correct opcode values
- Verify the ESP32 accepts and executes generated bytecode
- Check that the VM doesn't halt on generated code (it shouldn't, if validation passes)
- Try a deliberately vague request ("do something interesting") — see what the LLM generates
- Note how often the LLM produces incorrect opcodes (this is the "29.4% safety issue" from the full spec — self-validation is imperfect)

---

### Day 6: Safety Monitor (Watchdog, Current Limit, Heartbeat)

**Objective:** Add safety monitoring that operates independently of the VM and the serial link. If the VM goes haywire or the serial link dies, the ESP32 enters a safe state.

**Specific Steps:**

1. Add hardware watchdog to the ESP32:

```python
# safety.py — Day 6: Safety monitor for NEXUS MVP
import machine, time

class SafetyMonitor:
    """
    Minimal safety monitor. Two independent safety mechanisms:

    1. Hardware watchdog (WDT): Must be "kicked" every 5 seconds.
       If the main loop hangs, the ESP32 reboots.

    2. Current limit: Reads ACS712 sensor, trips if over threshold.
       Drives all outputs LOW on trip.

    3. Serial heartbeat: If no message from laptop for 10 seconds,
       revert to failsafe program.
    """

    def __init__(self, timeout_ms=5000, current_threshold_ma=3000,
                 heartbeat_timeout_ms=10000):
        # Hardware watchdog
        self.wdt = machine.WDT(timeout=timeout_ms)
        self.timeout_ms = timeout_ms

        # Current sensor (ACS712 on GPIO34, ADC)
        self.current_adc = machine.ADC(machine.Pin(34))
        self.current_adc.atten(machine.ADC.ATTN_11V)  # 0-3.3V range
        self.current_threshold_ma = current_threshold_ma
        self.current_reading_ma = 0.0

        # Heartbeat timeout
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.last_laptop_msg_ms = time.ticks_ms()

        # Safety state
        self.tripped = False
        self.trip_reason = None
        self.trips_count = 0

        # Safe state outputs
        self.led = machine.Pin(2, machine.Pin.OUT)
        self.heater = machine.Pin(15, machine.Pin.OUT)

    def kick(self):
        """Kick the watchdog. Call from main loop."""
        self.wdt.feed()

    def record_laptop_message(self):
        """Call when any message received from laptop."""
        self.last_laptop_msg_ms = time.ticks_ms()

    def check(self) -> dict:
        """
        Run all safety checks. Call every loop iteration.
        Returns dict with status and any trip events.
        """
        events = []

        # Check current
        raw = self.current_adc.read()  # 0-4095
        voltage = raw * 3.3 / 4095.0   # Convert to voltage
        # ACS712-5A: 0A = 2.5V, sensitivity = 185mV/A
        self.current_reading_ma = (voltage - 2.5) / 0.185 * 1000.0
        if abs(self.current_reading_ma) > self.current_threshold_ma:
            self._trip(f"overcurrent {self.current_reading_ma:.0f}mA")
            events.append("overcurrent")

        # Check heartbeat timeout
        if time.ticks_diff(time.ticks_ms(), self.last_laptop_msg_ms) > \
                self.heartbeat_timeout_ms:
            events.append("heartbeat_timeout")

        # Check if tripped
        if self.tripped:
            self.enter_safe_state()

        return {
            "current_ma": round(self.current_reading_ma, 0),
            "tripped": self.tripped,
            "trip_reason": self.trip_reason,
            "trips_count": self.trips_count,
            "events": events
        }

    def _trip(self, reason: str):
        """Trip the safety system."""
        if not self.tripped:
            self.tripped = True
            self.trip_reason = reason
            self.trips_count += 1

    def enter_safe_state(self):
        """Drive all outputs to safe state."""
        self.led.value(0)
        self.heater.value(0)

    def reset(self):
        """Reset safety state (after manual intervention)."""
        self.tripped = False
        self.trip_reason = None
```

2. Integrate safety into the main loop. The key change: `safety.check()` is called every iteration, and `safety.kick()` is called every iteration. If the main loop hangs for >5 seconds, the hardware watchdog reboots the ESP32. This is a real hardware safety mechanism — it cannot be overridden by software.

3. Wire the ACS712 current sensor in series with the heater power supply.

**Expected Output (during normal operation):**
```
[SAFETY] current=312mA, tripped=False, events=[]
```

**Expected Output (during overcurrent):**
```
[SAFETY] *** {"event": "overcurrent", "current_ma": 5200, "threshold_ma": 3000} ***
[SAFETY] current=5200mA, tripped=True, trip_reason="overcurrent 5200mA"
```

**How to Test It:**
- Short the heater output briefly — verify the current sensor detects the spike and trips
- Disconnect the serial cable — verify heartbeat timeout is detected (but note: the ESP32 should continue running with the default program, not halt)
- Introduce an infinite loop in the VM (a JUMP to itself — oh wait, we don't have JUMP). Instead, make the main loop `time.sleep(10)` instead of `time.sleep(0.01)` — the watchdog should reboot the ESP32 after 5 seconds.

---

### Day 7: First Autonomous Behavior (Temperature Control with Trust Gating)

**Objective:** Put it all together. The system reads temperature, runs the VM, sends telemetry to the laptop, the laptop evaluates trust, and the LLM agent suggests control improvements. The full loop: observe → evaluate → generate → validate → deploy → execute → observe.

**Specific Steps:**

1. Create the full integration script `nexus_mvp.py` on the laptop that combines all components:
   - Serial link (Day 3)
   - Trust engine (Day 4)
   - Reflex agent (Day 5)
   - Telemetry logging and plotting

2. Add automatic reflex improvement: every 100 telemetry messages, if trust is above "supervised," ask the agent to analyze the data and suggest an improvement.

3. Add a simple dashboard using matplotlib that plots:
   - Temperature over time
   - Output (heater) over time
   - Trust score over time
   - All on a single figure, updating in real-time

4. The end-to-end flow:

```
1. ESP32 reads DS18B20 → register 0
2. VM executes bytecode → computes output → register 1
3. ESP32 sends telemetry over serial
4. Laptop receives telemetry
5. Trust engine records event (good if normal, bad if anomalous)
6. Every 60 events, trust engine evaluates window → updates trust score
7. Laptop sends trust level to ESP32
8. ESP32 accepts/rejects deploy commands based on trust level
9. Every 100 events, agent analyzes telemetry and generates new bytecode
10. Generated bytecode is validated, then deployed if trust sufficient
11. ESP32 executes new bytecode
12. Go to step 1
```

**Expected Behavior:**

- First 2–3 hours: trust builds from 0.1 to 0.3. System is in "advisory" mode. No autonomous deployment.
- Hour 3+: trust crosses 0.3 threshold. System enters "supervised" mode. Agent can deploy bytecode.
- Agent generates first control program. ESP32 executes it.
- If the program works well (reasonable outputs, no current trips), trust continues to build.
- If the program causes issues (output saturation, current trips), trust drops. Agent's deployment privilege is revoked.
- Over time, the agent discovers better control strategies through experimentation.

**How to Test It (The Final Exam):**

1. Start the system and let it run for 3 hours. Verify trust reaches 0.3.
2. Ask the agent to generate a program. Verify it deploys successfully.
3. Create a disturbance: hold the temperature sensor (warm it up). Does the system respond correctly?
4. Kill the laptop process. Does the ESP32 continue running? (It should — the VM is independent.)
5. Restart the laptop. Does the system reconnect? (It should — the ESP32 keeps sending telemetry.)
6. Deliberately generate bad bytecode (manually send a deploy with random bytes). Does the VM halt gracefully?
7. After the VM halts, verify the ESP32 reloads the default program.

---

## 4. What You Learn From This

Each simplified component maps directly to a component in the full NEXUS spec. Here's what each day teaches you, and what the production version adds.

### Bytecode Design (Day 2)

**What you learned:** A stack machine is simple to implement. PUSH/ADD/SUB/LOAD/STORE is enough for basic control. The safety checks (stack overflow, unknown opcodes, cycle limits) are essential — without them, a bad program crashes the microcontroller, not just the VM. 4-byte fixed instructions make parsing trivial.

**What the full spec adds:**
- 32 opcodes instead of 5 (including MUL, DIV, CLAMP, comparisons, jumps, PID computation)
- 8-byte fixed instructions with flags byte, operand1 (uint16), operand2 (uint32) — richer encoding
- Float32-only arithmetic (no type tagging, the compiler is responsible for type correctness)
- 256-entry stack limit (production has bounded memory, no dynamic allocation)
- PID computation as a syscall (pseudo-instruction synthesized from JUMP + internal function call)
- CLAMP_F opcode that clamps outputs to safe ranges — your Python `max(0, min(100, x))` is the manual equivalent
- Variable access through register indirection (LOAD register 64+ = read variable)

The key insight from Day 2: **the VM IS the security boundary.** Once you see a bad program get caught by the stack underflow check instead of crashing the ESP32, you understand why NEXUS uses bytecode instead of interpreted JSON or direct firmware.

### Serial Protocols (Day 3)

**What you learned:** JSON-over-UART works for prototyping but has obvious limitations. No CRC means corrupted data gets parsed as valid JSON (or fails to parse and is silently dropped). No sequence numbers means you can't detect lost messages. No COBS framing means you can't embed binary data. Newline delimiters mean messages can't contain newlines.

**What the full spec adds:**
- RS-422 instead of TTL UART (differential signaling, 100m cable length, EMI resistant)
- 921,600 baud instead of 115,200 (8x throughput for sensor telemetry)
- COBS framing instead of newline delimiters (zero-byte delimiters, handles any payload)
- CRC-16/CCITT-FALSE instead of no integrity check (catches corruption)
- 28 message types instead of 4 (complete lifecycle: boot, role assignment, observation, OTA)
- 10-byte binary header instead of JSON envelope (smaller, faster to parse)
- Sequence numbers and acknowledgement/retry (reliable delivery)
- Baud rate negotiation (start at 115200, upgrade to 921600 after handshake)
- Priority queuing (safety messages preempt telemetry)

The key insight from Day 3: **reliable communication is a solved problem with known engineering patterns.** The COBS+CRC pattern is used in OBD-II automotive diagnostics, MAVLink drones, and CAN bus. It's not glamorous but it's what makes the system work at sea.

### Trust Dynamics (Day 4)

**What you learned:** The asymmetric gain/loss ratio creates a system that's "hard to trust, easy to distrust." With a 10:1 ratio, 10 good events barely compensate for 1 bad event. The trust score approaches 1.0 asymptotically — it never quite gets there, which is the point. The floor (t_floor) prevents trust from decaying all the way to zero via inactivity alone. Trust gating means the system starts conservative and earns its way to autonomy.

**What the full spec adds:**
- 25:1 loss-to-gain ratio (10:1 in MVP is already quite conservative)
- 12 parameters instead of 3 (quality cap, streak bonus, severity exponent, decay rate)
- 15 event types instead of 3 (with severity and quality values for fine-grained scoring)
- 6 autonomy levels instead of 2 (Disabled → Advisory → Supervised → Semi-Auto → High Auto → Full Auto)
- Minimum observation hours, consecutive days, and clean windows per level
- Promoted/demoted rules with cooldowns
- Reset logic (firmware update multiplies by 0.7, safety incident zeros to 0.0)
- Per-subsystem independence (steering trust independent of engine trust)
- The 0.5× trust rule for agent-generated code

The key insight from Day 4: **trust is not a boolean. It's a continuous function that reflects observed behavior over time.** The INCREMENTS algorithm is mathematically designed so that the time constant for gaining trust (658 windows ≈ 27 days) is 22× longer than losing it (29 windows ≈ 1.2 days). This prevents the "automation surprise" — the sudden, catastrophic failure of an overtrusted system, as happened with Boeing 737 MAX MCAS.

### Agent Code Generation (Day 5)

**What you learned:** LLMs can generate bytecode, but they're not perfect. They sometimes produce wrong opcodes, forget to include a STORE instruction, or generate programs that are syntactically valid but semantically wrong. The validation step catches some of these issues but not all. The 29.4% miss rate from the full spec (self-validation misses) is real — you'll see the LLM generate something that looks correct but produces unexpected results when executed.

**What the full spec adds:**
- Separate validation agent (Claude 3.5 Sonnet) that catches 95.1% of safety issues vs 70.6% for self-validation
- Formal bytecode verification (static analysis: stack depth analysis, jump target validation, register range checking)
- A/B testing framework (deploy new reflex alongside old, compare performance, keep winner)
- 5 pattern discovery algorithms for autonomous observation
- The full reflex synthesis pipeline: Observe → Record → Discover Patterns → Synthesize → A/B Test → Deploy
- Agent-Annotated Bytecode (AAB) with intent, capability requirements, and safety constraints as metadata
- The 0.5× trust rule: agent-generated code earns trust at half the rate

The key insight from Day 5: **agents can write control code, but they need supervision.** The two-agent validation pattern (generator + validator) catches most issues but not all. The trust system is the backstop — even if a bad program gets deployed, the trust score will drop when bad behavior is observed, revoking the agent's deployment privilege. Three layers of defense: validation, trust gating, and safety monitoring.

### Safety Engineering (Day 6)

**What you learned:** The hardware watchdog is the most important safety mechanism because it operates independently of all software. If the main loop hangs, the watchdog reboots the ESP32 — there's nothing any VM program, serial message, or LLM output can do about it. The current sensor provides ground truth about actuator behavior — you can command 50% output, but if the current is 5A, something is wrong.

**What the full spec adds:**
- Mechanical kill switch (MOSFET with 0.93ms response, physically cuts power)
- ISR guard (interrupt-level safety check that can preempt the VM)
- Hardware watchdog (MAX6818 external chip with 0x55/0xAA pattern feeding)
- Software watchdog (FreeRTOS task monitoring)
- Safety state machine (NORMAL → DEGRADED → SAFE_STATE → FAULT) with defined transitions
- Pull-down resistors on all actuators (fail to zero when unpowered)
- Per-actuator current sensing with INA219 (I2C, more accurate than ACS712)
- The safety_event wire message (criticality level 2, retried with escalation)

The key insight from Day 6: **safety must be layered and independent.** The watchdog catches software hangs. The current sensor catches hardware failures. The kill switch catches everything else. No single mechanism is sufficient — they're complementary. The full spec has 4 tiers for exactly this reason.

---

## 5. From Minimum Viable to Production NEXUS

You've built the MVP in 7 days. Now here's the concrete roadmap to the full NEXUS, with specific technical changes at each stage and the reasoning behind them.

### Weeks 2–3: Expand VM and Protocol

**What changes:**
- Add 27 more opcodes (MUL, DIV, CLAMP_F, comparisons, jumps, PID syscall). The VM goes from 5 to 32 opcodes.
- Change instruction encoding from 4 bytes to 8 bytes (opcode, flags, operand1 uint16, operand2 uint32).
- Add a bytecode validator that does static analysis before first execution (stack depth, jump targets, register ranges).
- Replace JSON framing with COBS encoding and add CRC-16/CCITT-FALSE. This is ~200 lines of C on the ESP32.
- Add sequence numbers and acknowledgement/retry logic.

**Why:** The 5-opcode VM can't do multiplication or branching — it can't implement PID control or conditional logic. COBS+CRC is needed for reliable communication on longer cables and in electrically noisy environments. The validator catches bad programs before they execute, which is essential when the program comes from an LLM.

**Estimated effort:** 2 weeks, 1 developer. The VM expansion is the bulk of the work — each new opcode needs careful implementation and testing.

### Weeks 4–5: Jetson Orin Nano and Local LLM

**What changes:**
- Replace the laptop with an NVIDIA Jetson Orin Nano (8GB, 40 TOPS, $249).
- Install Qwen2.5-Coder-7B at Q4_K_M quantization (4.2GB VRAM, 17.2 tok/s inference speed).
- Run the trust engine, reflex agent, and telemetry monitor as native Python services on the Jetson.
- Replace USB-UART with RS-422 transceiver (TI THVD1500, $2.50, 3.3V, differential pair).
- Add a second ESP32-S3 to demonstrate multi-node communication.

**Why:** The Jetson provides local AI inference without network dependency. On a boat at sea, you can't call OpenAI. The 40 TOPS is just enough for 7B model inference at usable speed. RS-422 gives you 100m cable range with EMI resistance, which you need when the ESP32 is in the engine room and the Jetson is on the bridge.

**Estimated effort:** 2 weeks, 1 developer. Mostly integration work — the software is already Python. The main challenge is setting up the Jetson environment (JetPack SDK, llama.cpp or vLLM for inference, UART pin muxing).

### Weeks 6–8: Full Trust, Safety, and COLREGs

**What changes:**
- Implement all 12 INCREMENTS parameters, 15 event types, and 6 autonomy levels.
- Add the full four-tier safety system (hardware kill switch, ISR guard, FreeRTOS watchdog, application trust gating).
- Implement the safety state machine (NORMAL → DEGRADED → SAFE_STATE → FAULT).
- Encode COLREGs rules (72 rules from safety_policy.json) as safety constraints on VM programs.
- Add INA219 current sensors (I2C, more accurate than ACS712) on all actuator channels.
- Implement per-subsystem trust independence (steering, throttle, bilge, lighting, anchor).

**Why:** The simplified 3-parameter trust works for a single temperature control loop. For a marine vessel with 5+ subsystems, you need the full algorithm with per-subsystem independence, observation hour requirements, and promotion/demotion rules. The four-tier safety system is non-negotiable for any system that can cause physical harm. COLREGs compliance is legally required for autonomous vessels in international waters.

**Estimated effort:** 3 weeks, 2 developers. Safety engineering is slow by design — every state transition, every timer, every threshold needs careful specification and testing.

### Months 3–4: Multi-Reflex Deployment, A/B Testing, Learning Pipeline

**What changes:**
- Implement multi-reflex deployment (multiple VM programs running concurrently, each with its own trust score).
- Add variable namespace isolation (each reflex gets its own variable space — no collisions).
- Implement the A/B testing framework (deploy new reflex alongside old, compare performance metrics, automatically promote winner).
- Build the observation recording system (store sensor data to Parquet files on NVMe SSD).
- Implement 2 pattern discovery algorithms (cross-correlation scanner and Bayesian change-point detection).
- Build the reflex synthesis pipeline: Observe → Record → Discover → Synthesize → A/B Test → Deploy.

**Why:** Multi-reflex deployment is what makes NEXUS useful — a real vessel needs separate control loops for navigation, engine management, bilge monitoring, lighting, and anchoring. A/B testing is the scientific method applied to control software: you don't deploy a new program because it "looks good," you deploy it alongside the old one and measure which performs better. The learning pipeline is what turns the system from a manually-operated tool into a self-improving organism.

**Estimated effort:** 6–8 weeks, 2–3 developers. This is the most complex phase — it requires concurrent software design, statistical analysis, and careful integration of the pattern discovery algorithms.

### Months 5–6: A2A-Native Extensions, Agent Validation Pipeline

**What changes:**
- Implement Agent-Annotated Bytecode (AAB): 8-byte core instruction + variable-length TLV metadata trailer.
- Build the two-agent validation pipeline (generator agent + separate validator agent).
- Implement the 0.5× trust rule for agent-generated code.
- Add the 29 proposed A2A opcodes (DECLARE_INTENT, VERIFY_OUTCOME, TELL, ASK, TRUST_CHECK, etc.) — all NOP on existing ESP32 firmware for backward compatibility.
- Build the agent communication protocol (agents negotiate bytecode, validate each other's output, resolve conflicts).
- Implement the formal bytecode verification pass (abstract interpretation to prove stack depth bounds, execution time bounds, and output range bounds).

**Why:** This is the frontier — the transition from "human-built MVP" to "agent-built system." AAB format lets agents read, understand, and validate each other's code. The two-agent validation pattern catches 95.1% of safety issues (vs 70.6% for self-validation). The 0.5× trust rule compensates for the reduced human intuition about what agent-generated code "actually does."

**Estimated effort:** 6–8 weeks, 2–3 developers. This phase is research-heavy — many of the design patterns are novel (there's no existing open-source codebase for agent-annotated bytecode or multi-agent bytecode validation).

---

## 6. The "A2A Tomorrow" Variant

### What Changes When Agents Build the System

The MVP you built in 7 days has humans at every critical point: a human chose the pin mapping, a human wrote the VM, a human designed the trust parameters, a human tested the safety monitor, and a human approved the LLM-generated bytecode. The A2A variant removes humans from the code path entirely.

Here's what changes — specifically and concretely.

**Step 1: Agent Writes the VM**

Instead of a human writing `vm.py`, an LLM agent receives the NEXUS VM specification (the 2,487-line document) and generates the complete MicroPython VM implementation. The agent's system prompt IS the compiler frontend — it translates the spec into code. A second agent validates the generated VM by running test programs and comparing outputs against a reference implementation.

What this looks like in practice:

```
Agent 1 (Generator):
  System prompt: NEXUS VM spec (32 opcodes, 8-byte encoding, safety invariants)
  User prompt: "Implement the complete VM in MicroPython for ESP32-S3."
  Output: vm_generated.py (estimated ~500 lines)

Agent 2 (Validator):
  System prompt: NEXUS VM spec + test suite (100 test programs)
  User prompt: "Validate this VM implementation against the test suite."
  Process: Execute each test program, compare stack state, check safety invariants
  Output: Validation report (pass/fail per test, identified issues)
```

**Step 2: Agent Validates Generated Bytecode**

In the MVP (Day 5), you had a simple `validate_bytecode()` function that checked for 4-byte alignment, instruction count, and presence of LOAD/STORE. In the A2A variant, a dedicated validation agent performs deep analysis:

- Static analysis: simulate execution, prove stack depth never exceeds 256, prove all jump targets are valid
- Semantic analysis: check that the program's intent (from AAB metadata) matches its behavior
- Safety analysis: prove that output values are always within actuator limits
- Cross-validation: a second agent independently validates the first agent's analysis

**Step 3: Agent Deploys Bytecode Through Trust**

The agent doesn't just generate bytecode — it participates in the trust system. The deployment flow becomes:

```
1. Generator agent produces bytecode with AAB metadata (intent, safety constraints)
2. Validator agent checks bytecode against NEXUS spec and safety policy
3. Trust engine checks current trust level and autonomy level
4. If trust sufficient, bytecode is deployed to ESP32
5. ESP32 executes bytecode, sends telemetry
6. Observation engine records telemetry
7. Pattern discovery engine identifies improvement opportunities
8. Generator agent synthesizes improved bytecode based on patterns
9. A/B testing framework compares old and new bytecode
10. If new bytecode is better, it's promoted; trust increases
11. If new bytecode causes issues, it's rolled back; trust decreases
12. Cycle repeats — the system improves itself without human intervention
```

**Step 4: Agent Monitors and Responds to Safety Events**

In the MVP, the laptop monitor displays safety events and a human decides what to do. In the A2A variant, an agent monitors the safety event stream and responds automatically:

- Overcurrent detected → agent reduces actuator output limits and generates a diagnostic bytecode program
- Watchdog timeout → agent reboots the ESP32 and re-deploys the last-known-good program
- Trust score dropped → agent reverts to a simpler, more conservative control program
- Serial communication loss → agent switches to local-only mode (the ESP32 runs independently, the agent waits for reconnection)

### The Bridge: From Human-Built to Agent-Built

The transition from the 7-day MVP to the A2A variant happens in 4 stages:

**Stage 1 (Week 1–2, your MVP):** Humans build everything. Agents assist with code generation but humans review and approve all changes. Trust system is simplified. Safety monitoring is basic.

**Stage 2 (Week 3–4):** Agents generate VM programs from natural language. Humans validate the generated programs before deployment. Trust system is expanded to 6 levels. Safety monitoring includes current sensing and heartbeat timeout.

**Stage 3 (Week 5–8):** Agents validate each other's generated programs. The two-agent pattern (generator + validator) replaces human review for routine deployments. Humans review only for trust level promotions (advisory → supervised → semi-autonomous). Full safety system deployed.

**Stage 4 (Month 3+):** Agents handle the entire lifecycle: observe, discover patterns, synthesize bytecode, validate, deploy, monitor, and improve. Humans set high-level goals ("maintain temperature at 25°C ± 0.5°C") and the system figures out how. Humans intervene only for safety incidents and trust level promotions above L3.

### Honest Assessment of the A2A Variant

**What works well:**
- Agents are excellent at generating syntactically correct bytecode from natural language descriptions
- The two-agent validation pattern catches most safety issues
- The trust system provides a mathematical backstop — even if a bad program is deployed, trust decreases and deployment privileges are revoked
- The system can improve faster than human-authored code because it can iterate continuously (24/7)

**What doesn't work well (yet):**
- Agent cross-validation misses ~5% of safety issues. For a marine vessel, 5% is unacceptable.
- The "black box provenance problem" (Open Problem #6): when an agent generates a specific bytecode sequence, you can't trace WHY it chose those specific instructions. For certification (IEC 61508), you need provenance.
- The "adversarial bytecode" problem (Open Problem #4): can an agent craft bytecode that passes validation but violates safety? This is an open research question.
- The "responsibility at L5" problem (Open Problem #5): when a fully autonomous system causes harm, who is responsible? There is no legal precedent.

**The honest conclusion:** The A2A variant is buildable with today's tools. The 7-day MVP proves the architecture. But the A2A variant should be deployed at L1–L2 (advisory/supervised) only. Full autonomy (L4–L5) requires advances in formal verification of agent-generated code, legal frameworks for agent responsibility, and regulatory acceptance of self-modifying safety-critical software. These are research problems, not engineering problems. They may take 5–10 years to resolve.

The NEXUS trust system is designed for exactly this reality: it lets you deploy agent-generated code at low autonomy levels today, and gradually increase autonomy as the technology matures. The trust score doesn't care whether the code was written by a human or an agent — it only cares whether the code behaves safely. That's the right abstraction for an uncertain future.

---

## Appendix: Quick Reference

### Hardware Summary

| Component | ESP32-S3 Pin | Function |
|-----------|-------------|----------|
| DS18B20 | GPIO4 | Temperature sensor (1-Wire) |
| LED | GPIO2 | Actuator indicator |
| MOSFET (heater) | GPIO15 | Power control (PWM capable) |
| ACS712 | GPIO34 | Current sensor (ADC) |
| UART TX | GPIO43 | Serial to laptop |
| UART RX | GPIO44 | Serial from laptop |

### Software Summary

| Component | Platform | File |
|-----------|----------|------|
| VM (5 opcodes) | ESP32 (MicroPython) | `vm.py` |
| Serial link | ESP32 (MicroPython) | `serial_link.py` |
| Safety monitor | ESP32 (MicroPython) | `safety.py` |
| Main loop | ESP32 (MicroPython) | `main.py` |
| Trust engine | Laptop (Python) | `trust_engine.py` |
| Reflex agent | Laptop (Python) | `reflex_agent.py` |
| Monitor | Laptop (Python) | `laptop_monitor.py` |

### Key Numbers (MVP vs Production)

| Metric | MVP | Production NEXUS |
|--------|-----|-----------------|
| Opcodes | 5 | 32 (+ 29 A2A, NOP on existing) |
| Instruction size | 4 bytes | 8 bytes |
| Stack depth | 64 | 256 |
| Serial | UART 115200, JSON | RS-422 921600, COBS+CRC |
| Message types | 4 | 28 |
| Trust parameters | 3 | 12 |
| Autonomy levels | 2 | 6 |
| Safety tiers | 1 (watchdog) | 4 (hardware, firmware, supervisory, application) |
| AI model | OpenAI GPT-4o-mini (cloud) | Qwen2.5-Coder-7B Q4_K_M (local) |
| Loss:gain ratio | 10:1 | 25:1 |
| Time to L4 | ~hours (testing) | 45 days ideal |
| Total cost | ~$37 | ~$684 |
| Build time | 7 days | 12–16 weeks |

---

*This document was generated as part of the NEXUS project. For the full specification suite, see `specs/00_MASTER_INDEX.md`. For the philosophical foundation, see `knowledge-base/philosophy/`. For the A2A-native language research, see `a2a-native-language/final_synthesis.md`.*
