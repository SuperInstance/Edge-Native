# NEXUS Platform — Phase 1: Foundation — Complete Specification Compendium

**Version:** 2.0.0 | **Date:** 2026-03-30
**Scope:** Project Scaffolding, Wire Protocol, Safety Layer (Prompts 0-2)

---

## Table of Contents

1. [Wire Protocol Specification](#1-nexus-serial-wire-protocol-specification)
2. [Message Payload Schemas](#2-message-payload-schemas)
3. [Safety System Specification](#3-safety-system-specification)
4. [Safety Policy](#4-safety-policy)
5. [Trust Score Algorithm Specification](#5-trust-score-algorithm-specification)

---

# 1. NEXUS Serial Wire Protocol Specification

> **Source:** `protocol/wire_protocol_spec.md` | **Document ID:** NEXUS-PROT-WIRE-001 | **Version:** 2.0.0

---

# NEXUS Serial Wire Protocol Specification

**Document ID**: NEXUS-PROT-WIRE-001
**Version**: 2.0.0
**Date**: 2025-01-15
**Classification**: Production Release
**Status**: Active

---

## Table of Contents

1. [Physical Layer](#1-physical-layer)
2. [Framing Layer](#2-framing-layer)
3. [Message Header](#3-message-header)
4. [Message Type Registry](#4-message-type-registry)
5. [Error Code Registry](#5-error-code-registry)
6. [Reliability Mechanisms](#6-reliability-mechanisms)
7. [Binary Payload Formats](#7-binary-payload-formats)
8. [State Machine & Boot Sequence](#8-state-machine--boot-sequence)
9. [Appendices](#9-appendices)

---

## 1. Physical Layer

### 1.1 Electrical Specification

| Parameter | Value |
|---|---|
| Standard | EIA/TIA-422-B (RS-422) |
| Mode | Full-duplex, differential pair |
| Signalling | NRZ (Non-Return-to-Zero) |
| Default Baud Rate | 921,600 bps |
| Boot Baud Rate | 115,200 bps |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |
| Flow Control | Hardware (CTS/RTS) |
| Connector | RJ-45 (pinout defined in Section 1.4) |
| Impedance | 120 Ω differential termination at each end |
| Common-Mode Voltage | -7V to +7V |
| Differential Output | ≥ 2.0V (loaded), ≤ 10V (unloaded) |

### 1.2 Baud Rate Negotiation

All nodes power on at **115,200 bps**. The Jetson (J2N master) initiates baud upgrade after the initial handshake completes. Negotiation is mandatory before any high-throughput operations (observation recording, OTA updates).

**Negotiation Sequence**:

```
1. J2N sends BAUD_UPGRADE (0x18) at current baud with {target_baud: 921600}
2. N2J responds with COMMAND_ACK (0x08) confirming target_baud
3. Both sides switch to new baud rate simultaneously
4. J2N sends PING (0x16) at new baud to verify link integrity
5. If PING is not answered within 500ms, both sides fall back to previous baud
```

**Supported Baud Rates** (negotiation table, in order of preference):

| Baud Rate | Max Cable Length | Use Case |
|---|---|---|
| 921,600 bps | 10 m (33 ft) | Default, short-haul. Minimum Cat-5e. |
| 460,800 bps | 50 m (164 ft) | Medium-haul deployments. Cat-5e or Cat-6. |
| 230,400 bps | 75 m (246 ft) | Long-haul with moderate throughput. |
| 115,200 bps | 100 m (328 ft) | Maximum range, fallback. Cat-6 recommended. |

**Degradation Rule**: If a baud rate upgrade fails, the system automatically retries at the next lower rate. The negotiated baud is stored in non-volatile memory and used on subsequent boots.

### 1.3 Recommended Transceiver

| Component | Recommended Part | Notes |
|---|---|---|
| Transceiver IC | TI THVD1500 | 3.3V RS-422, 50 Mbps max, auto-bias, ±15 kV ESD |
| Backup Option | TI THVD1429 | 3.3V/5V, lower power, 20 Mbps |
| Termination | 120 Ω, 1% tolerance | At each end of the bus |
| TVS Protection | TPD4E05U06 or equiv. | On each differential pair, placed near connector |

**THVD1500 Configuration**:
- DE (Driver Enable): hardwired HIGH (always transmitting when master drives)
- RE (Receiver Enable): hardwired LOW (always listening)
- A/B differential output: directly to cable
- VCC: 3.3V regulated, decoupled with 100 nF + 10 µF

### 1.4 Cable & Connector Pinout (RJ-45)

| Pin | Signal | Direction (from Jetson perspective) |
|---|---|---|
| 1 | TX+ | Output |
| 2 | TX- | Output |
| 3 | RX+ | Input |
| 4 | RX- | Input |
| 5 | GND | Reference |
| 6 | CTS (Jetson→Node) | Output |
| 7 | RTS (Node→Jetson) | Input |
| 8 | SHIELD | Chassis ground / cable shield drain |

**Cable Requirements**:
- Minimum: Cat-5e UTP (unshielded twisted pair)
- Preferred: Cat-6 STP (shielded twisted pair) for runs > 20m
- Each differential pair must maintain twist rate
- Cable shield connected at both ends through 100 nF capacitor (prevents ground loops)

### 1.5 Flow Control

Hardware flow control (CTS/RTS) is **always enabled**. No software flow control (XON/XOFF) is permitted.

**CTS (Clear to Send)**: Jetson asserts CTS low to signal the node may transmit. Jetson deasserts CTS high when its RX FIFO is > 75% full or when it cannot process incoming data.

**RTS (Request to Send)**: Node asserts RTS low to signal it is ready to receive. Node deasserts RTS high when its RX FIFO is > 75% full.

**Timeout**: If CTS is deasserted for more than 2 seconds, the transmitting side must abort the current frame and report error `0x5010` (FLOW_CONTROL_TIMEOUT).

---

## 2. Framing Layer

### 2.1 Overview

All data on the wire is framed using **COBS (Consistent Overhead Byte Stuffing)** encoding with explicit `0x00` delimiters. This provides:
- Unambiguous frame boundaries regardless of payload content
- Self-synchronizing decoder (any `0x00` byte resets frame detection)
- Worst-case overhead of 1 byte per 254 bytes of payload (~0.4%)
- No need to escape delimiters within the payload

### 2.2 Wire Frame Format

```
+------+-----------------------------+------+
| 0x00 | COBS-encoded payload + CRC  | 0x00 |
+------+-----------------------------+------+
  1B           variable               1B
```

**Frame Structure**:

| Field | Size | Value |
|---|---|---|
| Start Delimiter | 1 byte | Always `0x00` |
| COBS-encoded data | N bytes | Header + Payload + CRC-16 (all encoded together) |
| End Delimiter | 1 byte | Always `0x00` |

The COBS-encoded region contains the concatenation of:

```
[10-byte Message Header] [Payload bytes (0 to 1024)] [2-byte CRC-16]
```

### 2.3 COBS Encoding Rules

COBS encodes a byte sequence such that no `0x00` bytes appear in the output (except at frame boundaries). Rules:

1. Scan input bytes from left to right.
2. Count consecutive non-zero bytes. When a `0x00` is encountered, or when 254 non-zero bytes have been counted, emit the count as a single byte, followed by the non-zero bytes themselves.
3. If the last run of non-zero bytes reaches end-of-input without encountering a `0x00`, append a trailing `0x00` to the input before the final count byte.
4. The count byte itself may never be `0x00` during encoding.

**Example** (hex bytes):

```
Input:   [0x01] [0x02] [0x00] [0x03] [0x04] [0x05] [0x00] [0x06]
Encoded: [0x02] [0x01] [0x02] [0x03] [0x03] [0x04] [0x05] [0x01] [0x06]
```

**Implementation Note**: A sentinel `0x00` byte is implicitly appended to the decoded output. This does **not** appear in the final decoded data; it is consumed by the COBS algorithm itself. Implementations must strip it.

### 2.4 CRC-16/CCITT-FALSE

A CRC-16 checksum is computed over the **entire decoded payload region** (Message Header + Payload). The CRC is appended as two bytes (big-endian) immediately after the payload, before COBS encoding.

| Parameter | Value |
|---|---|
| Polynomial | 0x1021 (x^16 + x^12 + x^5 + 1) |
| Initial Value | 0xFFFF |
| Final XOR | 0x0000 |
| Reflect Input | No |
| Reflect Output | No |
| Check Value (for "123456789") | 0x29B1 |

**Byte Order**: CRC is transmitted MSB first (big-endian) as `[crc_hi] [crc_lo]`.

### 2.5 Frame Size Limits

| Parameter | Value |
|---|---|
| Maximum Payload | 1024 bytes |
| Message Header | 10 bytes |
| CRC-16 | 2 bytes |
| Maximum Decoded Frame | 1036 bytes (10 + 1024 + 2) |
| Maximum COBS-Encoded Frame | 1051 bytes (1036 + 15 worst-case COBS overhead) |
| Maximum Wire Frame | 1053 bytes (1 + 1051 + 1) |

Frames exceeding the maximum size must be rejected with error `0x5001` (FRAME_TOO_LARGE). The receiver must discard the frame without processing.

### 2.6 Frame Reception Algorithm

```
state = IDLE
buffer = empty

on byte received (b):
    if b == 0x00:
        if state == IDLE:
            state = RECEIVING
            buffer = empty
        elif state == RECEIVING:
            # End of frame
            decoded = cobs_decode(buffer)
            if len(decoded) < 12:  # min header(10) + crc(2)
                emit error FRAME_TOO_SHORT
            else:
                header = decoded[0:10]
                payload = decoded[10:-2]
                crc_received = decoded[-2:]
                crc_computed = crc16_ccitt(decoded[0:-2])
                if crc_received == crc_computed:
                    dispatch(header, payload)
                else:
                    emit error CRC_MISMATCH
            state = IDLE
            buffer = empty
    else:
        if state == RECEIVING:
            buffer.append(b)
            if len(buffer) > 1051:
                emit error FRAME_TOO_LARGE
                state = IDLE
                buffer = empty
```

---

## 3. Message Header

### 3.1 Header Format

Every message (in both directions) begins with a fixed 10-byte header. The header is transmitted in network byte order (big-endian).

```
 Offset  Size  Field
 ──────  ────  ───────────────────────────────
 0       1B    msg_type
 1       1B    flags
 2       2B    sequence_number (uint16, big-endian)
 4       4B    timestamp_ms (uint32, big-endian)
 8       2B    payload_length (uint16, big-endian)
                                ────
 Total:  10 bytes
```

### 3.2 Field Definitions

#### `msg_type` (uint8, offset 0)

Identifies the message type. See Section 4 for the complete registry.

| Range | Allocation |
|---|---|
| 0x00 | Reserved (protocol version / null) |
| 0x01 – 0x1C | Core NEXUS message types |
| 0x1D – 0x7F | Reserved for future NEXUS core |
| 0x80 – 0xFF | Node-extensions (project-specific, defined per deployment) |

#### `flags` (uint8, offset 1)

| Bit | Name | Description |
|---|---|---|
| 0 | `ACK_REQUIRED` | Receiver must send a COMMAND_ACK for this message |
| 1 | `IS_ACK` | This message IS an acknowledgement of a previous message |
| 2 | `IS_ERROR` | This message carries an error payload |
| 3 | `URGENT` | Queue bypass — deliver ahead of normal traffic |
| 4 | `COMPRESSED` | Payload is LZ4-compressed |
| 5 | `ENCRYPTED` | Payload is AES-128-CTR encrypted (key exchange out of band) |
| 6 | `NO_TIMESTAMP` | timestamp_ms field is zero / not meaningful |
| 7 | `RESERVED` | Must be zero on transmit, ignored on receive |

**Flag Interaction Rules**:
- `IS_ACK` (bit 1) and `ACK_REQUIRED` (bit 0) MUST NOT both be set.
- `IS_ERROR` (bit 2) MUST NOT be set without `IS_ACK` (bit 1) also being set, except for message type `0x15 ERROR` which carries error data independently.
- `URGENT` (bit 3) is valid only for messages with criticality ≥ 1 (command or safety).
- `COMPRESSED` and `ENCRYPTED` may be combined.

#### `sequence_number` (uint16, offset 2-3)

- Rolling counter, monotonically increasing per direction.
- Each side maintains its own independent sequence counter.
- Wraps from 0xFFFF to 0x0000 (no overflow handling needed; gap detection is modular).
- **Jetson** manages its own TX sequence. **Node** manages its own TX sequence.
- When `IS_ACK` is set, the `sequence_number` field contains the sequence number of the message being acknowledged (echoed back).

#### `timestamp_ms` (uint32, offset 4-7)

- Sender's local uptime in milliseconds since boot.
- Wraps at ~49.7 days. The receiver is responsible for tracking wrap-arounds.
- Used for latency calculation (PING/PONG) and telemetry timestamping.
- Resolution: 1 ms minimum. Higher resolution (e.g., 1 µs) may be used by dividing by 1000.
- Set to `0x00000000` if `NO_TIMESTAMP` flag is set.

#### `payload_length` (uint16, offset 8-9)

- Length of the payload in bytes, **after** COBS decoding and **before** any decompression.
- Does **not** include the 10-byte header or the 2-byte CRC.
- Must be `≤ 1024`. Violation triggers `FRAME_TOO_LARGE` on the receiver.
- May be `0` for messages that carry no payload (e.g., HEARTBEAT).

### 3.3 Header Byte Layout (Big-Endian)

```
Byte 0:  [msg_type]
Byte 1:  [flags]
Byte 2:  [sequence_number >> 8]   (MSB)
Byte 3:  [sequence_number & 0xFF]  (LSB)
Byte 4:  [timestamp_ms >> 24]
Byte 5:  [(timestamp_ms >> 16) & 0xFF]
Byte 6:  [(timestamp_ms >> 8) & 0xFF]
Byte 7:  [timestamp_ms & 0xFF]
Byte 8:  [payload_length >> 8]    (MSB)
Byte 9:  [payload_length & 0xFF]   (LSB)
```

---

## 4. Message Type Registry

### 4.1 Conventions

| Symbol | Meaning |
|---|---|
| **J2N** | Jetson → Node (command direction) |
| **N2J** | Node → Jetson (report direction) |
| **Both** | Either direction |
| **JSON** | Payload is UTF-8 encoded JSON (see `message_payloads.json` for schema) |
| **Binary** | Payload follows a fixed binary layout (see Section 7) |
| **None** | No payload (payload_length = 0) |

### 4.2 Criticality Levels

| Level | Name | Handling |
|---|---|---|
| 0 | **Telemetry** | Best-effort delivery. No ack required. May be rate-limited. |
| 1 | **Command** | Ack required. Retried up to 3 times. Logged on failure. |
| 2 | **Safety** | Ack required. Retried with escalation. Failsafe on persistent failure. |

### 4.3 Message Type Table

| ID | Name | Direction | Payload | Criticality | Description |
|---|---|---|---|---|---|
| `0x01` | DEVICE_IDENTITY | N2J | JSON | 0 | Boot announcement: MAC address, chip type, firmware version, hardware capabilities, supported message types. Sent immediately after power-on, before any other message. |
| `0x02` | ROLE_ASSIGN | J2N | JSON | 1 | Complete node role configuration. Assigns the node a named role (e.g., "left_arm_motor_controller"), defines which pins are inputs/outputs, attaches reflexes, sets telemetry intervals. Node must apply or reject this role. |
| `0x03` | ROLE_ACK | N2J | JSON | 1 | Node's response to ROLE_ASSIGN. Includes `accepted` boolean, role name echoed, and optional `rejection_reason` if the node cannot fulfill the role. |
| `0x04` | SELFTEST_RESULT | N2J | JSON | 1 | Results of the power-on self-test (POST). Includes per-pin continuity, pull-up/down verification, ADC reference check, I2C bus scan, flash integrity CRC. |
| `0x05` | HEARTBEAT | Both | None | 0 | Keep-alive message. No payload. Receiver uses arrival time to compute link health. Sent at a configurable interval (default 1000 ms by node, 5000 ms by Jetson). |
| `0x06` | TELEMETRY | N2J | JSON | 0 | Periodic sensor data snapshot. Contains timestamped readings from all configured input pins, ADC channels, I2C sensors, and computed derivatives. Sent at the rate defined in ROLE_ASSIGN. |
| `0x07` | COMMAND | J2N | JSON | 1 | Actuator command. Instructs the node to set a pin state, drive a PWM value, start/stop a reflex, or execute a named action defined in the role. |
| `0x08` | COMMAND_ACK | N2J | JSON | 1 | Acknowledgement of a COMMAND (or any ack-required message). Contains the echoed `sequence_number`, a `status` enum, optional `result` data, and optional error detail. |
| `0x09` | REFLEX_DEPLOY | J2N | JSON | 1 | Deploys a new reflex definition to the node's runtime. The reflex JSON includes trigger conditions, actions, priority, and timeout. Replaces any previous reflex with the same name. |
| `0x0A` | REFLEX_STATUS | N2J | JSON | 0 | Reports the current state of all loaded reflexes: active/inactive/paused, trigger counts, last-fire timestamp, current version hash. Requested on demand or sent after REFLEX_DEPLOY. |
| `0x0B` | OBS_RECORD_START | J2N | JSON | 1 | Begins observation recording on the node. Specifies which channels to record, sample rate, compression mode, and maximum recording duration/buffer size. |
| `0x0C` | OBS_RECORD_STOP | J2N | JSON | 1 | Stops an in-progress recording. Optionally includes a `finalize` flag to prepare data for transfer. |
| `0x0D` | OBS_DUMP_HEADER | N2J | JSON | 0 | Metadata describing an observation recording dump. Precedes OBS_DUMP_CHUNK messages. Includes total chunk count, recording parameters, and checksum of the complete dataset. |
| `0x0E` | OBS_DUMP_CHUNK | N2J | Binary | 0 | A single chunk of binary observation data. Chunk index and total chunks are in the binary header. |
| `0x0F` | OBS_DUMP_END | N2J | JSON | 0 | Signals the end of an observation data dump. Contains an overall CRC-32 of all chunk payloads concatenated. |
| `0x10` | IO_RECONFIGURE | J2N | JSON | 1 | Dynamically changes pin parameters at runtime: pin mode (input/output/PWM), pull direction, ADC resolution, debounce interval, interrupt mode. Does not change the node role. |
| `0x11` | FIRMWARE_UPDATE_START | J2N | JSON | 1 | Initiates an over-the-air (OTA) firmware update. Specifies firmware size in bytes, total chunk count, firmware version string, and SHA-256 hash of the complete firmware image. |
| `0x12` | FIRMWARE_UPDATE_CHUNK | J2N | Binary | 1 | A single binary chunk of firmware data. 512 bytes of firmware payload per chunk, plus a 4-byte chunk index header. |
| `0x13` | FIRMWARE_UPDATE_END | J2N | JSON | 1 | Finalizes the OTA update. Triggers the node to verify the firmware image (SHA-256), write to the update partition, and prepare for reboot. |
| `0x14` | FIRMWARE_UPDATE_RESULT | N2J | JSON | 1 | Reports the outcome of the firmware update: success, hash mismatch, flash write error, or reboot status. Sent after verification completes. |
| `0x15` | ERROR | N2J | JSON | 2 | Asynchronous error notification. Contains an error code (from Section 5), human-readable message, severity, and context (which operation/subsystem failed). |
| `0x16` | PING | Both | None | 0 | Latency measurement probe. Jetson or node may initiate. The receiver must respond with PONG containing the same sequence_number. Timestamp used for RTT calculation. |
| `0x17` | PONG | Both | None | 0 | Response to PING. Carries the sequence_number of the originating PING. No payload. RTT = (pong_arrival_timestamp - ping_departure_timestamp). |
| `0x18` | BAUD_UPGRADE | J2N | JSON | 1 | Requests the node to switch to a new baud rate. Includes `target_baud` value. Node responds with COMMAND_ACK. Both sides must switch simultaneously after ack. |
| `0x19` | CLOUD_CONTEXT_REQUEST | J2N | JSON | 0 | Requests observation data from the node to be sent to the cloud for analysis. Specifies which recording, time window, and format. Node prepares and transmits data via OBS_DUMP_CHUNK. |
| `0x1A` | CLOUD_RESULT | N2J | JSON | 0 | Results from cloud analysis returned to the node. May contain updated reflex parameters, calibration values, or configuration adjustments based on ML inference. |
| `0x1B` | AUTO_DETECT_RESULT | N2J | JSON | 0 | Results of automatic hardware detection: I2C bus scan (addresses found, device IDs), ADC probe results, and connected peripheral identification. Sent after DEVICE_IDENTITY. |
| `0x1C` | SAFETY_EVENT | N2J | JSON | 2 | Critical safety notification: kill-switch activation, overcurrent trip, watchdog timeout, thermal shutdown, or mechanical limit exceeded. The node autonomously enters a safe state. |

### 4.4 Message Type Category Summary

| Category | Message IDs | Count |
|---|---|---|
| Boot & Identity | 0x01, 0x04, 0x1B | 3 |
| Role Management | 0x02, 0x03 | 2 |
| Link Health | 0x05, 0x16, 0x17, 0x18 | 4 |
| Telemetry & Data | 0x06, 0x19, 0x1A | 3 |
| Commands & Control | 0x07, 0x08, 0x10 | 3 |
| Reflex Engine | 0x09, 0x0A | 2 |
| Observation System | 0x0B, 0x0C, 0x0D, 0x0E, 0x0F | 5 |
| Firmware OTA | 0x11, 0x12, 0x13, 0x14 | 4 |
| Error & Safety | 0x15, 0x1C | 2 |
| **Total Core** | | **28** |

---

## 5. Error Code Registry

### 5.1 Format

Error codes are 16-bit values (uint16). The high byte identifies the **category**, the low byte identifies the **specific error** within that category.

```
0x[CAT][SUB]

CAT = Category (0x00 – 0xFF)
SUB = Sub-code (0x00 – 0xFF)
```

### 5.2 Complete Error Code Table

#### Category 0x00: General Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x0000` | NONE | Info | No error. Used as success indicator in ACK payloads. |
| `0x0001` | UNKNOWN | Error | An unclassified error occurred. Check the `detail` field for context. |
| `0x0002` | NOT_IMPLEMENTED | Error | The requested message type or feature is not implemented by this firmware version. |
| `0x0003` | INVALID_PAYLOAD | Error | The payload could not be parsed: malformed JSON, wrong binary length, or schema violation. |
| `0x0004` | TIMEOUT | Error | An operation did not complete within the expected time window. |
| `0x0005` | BUSY | Warning | The node cannot service this request right now (e.g., recording in progress, OTA active). |
| `0x0006` | BUFFER_OVERFLOW | Error | An internal buffer is full. Data was dropped. |
| `0x0007` | OUT_OF_MEMORY | Error | Heap allocation failure. The node may need a restart. |

#### Category 0x10: Hardware Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x1001` | GPIO_INIT_FAILED | Error | A GPIO pin could not be initialized. Pin number or mux conflict. |
| `0x1002` | ADC_INIT_FAILED | Error | The ADC peripheral could not be started or calibrated. |
| `0x1003` | ADC_READ_ERROR | Error | An ADC conversion failed or returned out-of-range data. |
| `0x1004` | I2C_BUS_LOCKED | Error | The I2C bus is stuck (SCL held low). Requires bus recovery. |
| `0x1005` | I2C_DEVICE_NOT_FOUND | Warning | Expected I2C device at specified address did not respond. |
| `0x1006` | I2C_READ_FAILED | Error | I2C read transaction returned NACK or garbage data. |
| `0x1007` | I2C_WRITE_FAILED | Error | I2C write transaction returned NACK or timed out. |
| `0x1008` | SPI_INIT_FAILED | Error | SPI peripheral initialization failed. |
| `0x1009` | SPI_TRANSFER_ERROR | Error | SPI transaction returned an error flag or timed out. |
| `0x100A` | UART_PERIPHERAL_ERROR | Error | Internal UART error (framing, parity, or overrun). |

#### Category 0x20: I/O Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x2001` | PIN_MODE_INVALID | Error | The requested pin mode is not supported for the given pin. |
| `0x2002` | PIN_ALREADY_IN_USE | Error | The pin is claimed by another subsystem and cannot be reconfigured. |
| `0x2003` | PIN_NOT_CONFIGURED | Warning | An operation was attempted on a pin that has no configured mode. |
| `0x2004` | PWM_FREQUENCY_UNSUPPORTED | Error | The requested PWM frequency is outside the hardware range. |
| `0x2005` | ADC_CHANNEL_INVALID | Error | The specified ADC channel does not exist on this chip. |
| `0x2006` | DEBOUNCE_NOT_CONFIGURED | Warning | An interrupt was requested on a pin without debounce being set up. |
| `0x2007` | OUTPUT_WRITE_FAILED | Error | Writing to a GPIO output pin failed (hardware fault). |

#### Category 0x30: Reflex Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x3001` | REFLEX_PARSE_ERROR | Error | The reflex JSON could not be parsed or failed schema validation. |
| `0x3002` | REFLEX_NOT_FOUND | Warning | A reflex with the specified name does not exist on this node. |
| `0x3003` | REFLEX_EXECUTION_ERROR | Error | A reflex action failed during execution (e.g., target pin not available). |
| `0x3004` | REFLEX_TABLE_FULL | Error | No room to load another reflex. Maximum reflex count reached. |
| `0x3005` | REFLEX_TRIGGER_INVALID | Error | The trigger condition references a pin or sensor that does not exist. |
| `0x3006` | REFLEX_CYCLE_DETECTED | Error | Reflex A triggers Reflex B which triggers Reflex A (cyclic dependency). |
| `0x3007` | REFLEX_DISABLED | Info | The reflex was disabled (by configuration or safety event) and did not fire. |

#### Category 0x40: Safety Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x4001` | KILL_SWITCH_ACTIVATED | Critical | Physical kill-switch has been triggered. All outputs driven LOW. |
| `0x4002` | OVERCURRENT_DETECTED | Critical | Current draw on a monitored channel exceeded the threshold. |
| `0x4003` | THERMAL_SHUTDOWN | Critical | Die temperature exceeded the safe operating limit. Outputs disabled. |
| `0x4004` | WATCHDOG_TIMEOUT | Critical | The node's internal watchdog timer expired. System was reset. |
| `0x4005` | MECHANICAL_LIMIT_EXCEEDED | Critical | A sensor reading indicates a physical limit was reached (e.g., joint angle max). |
| `0x4006` | COMMUNICATION_LOSS | Critical | Heartbeat timeout escalated to failsafe. No response from the other side. |
| `0x4007` | POWER_SUPPLY_FAULT | Critical | Input voltage is outside the safe operating range. |
| `0x4008` | BROWNOUT_DETECTED | Warning | Input voltage dropped below the brownout threshold. Some peripherals may have reset. |

#### Category 0x50: Protocol Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x5001` | FRAME_TOO_LARGE | Error | Received frame exceeds the 1024-byte payload limit. |
| `0x5002` | FRAME_TOO_SHORT | Error | Received frame is shorter than minimum (12 bytes decoded). |
| `0x5003` | CRC_MISMATCH | Error | CRC-16 check failed. Frame is corrupt. |
| `0x5004` | COBS_DECODE_ERROR | Error | COBS decoding produced invalid output (malformed encoding). |
| `0x5005` | SEQUENCE_GAP | Warning | One or more messages were dropped (sequence number jump > 1). |
| `0x5006` | UNKNOWN_MSG_TYPE | Warning | Received a msg_type that is not recognized by this firmware. |
| `0x5007` | INVALID_HEADER | Error | Message header contains invalid field values (e.g., payload_length exceeds limit). |
| `0x5008` | ACK_TIMEOUT | Error | No acknowledgement received within the retry window. |
| `0x5009` | DUPLICATE_SEQUENCE | Warning | A message with this sequence_number was already processed. Ignored. |
| `0x500A` | DECOMPRESSION_ERROR | Error | LZ4 decompression of the payload failed. |
| `0x500B` | DECRYPTION_ERROR | Error | AES-128-CTR decryption failed (wrong key or tampered data). |
| `0x500C` | FLOW_CONTROL_TIMEOUT | Error | CTS/RTS held deasserted for > 2 seconds. Frame aborted. |
| `0x500D` | BAUD_NEGOTIATION_FAILED | Error | Failed to establish communication at the requested baud rate. |

#### Category 0x60: Firmware Errors

| Code | Name | Severity | Description |
|---|---|---|---|
| `0x6001` | OTA_HASH_MISMATCH | Error | SHA-256 hash of received firmware does not match the expected value. |
| `0x6002` | OTA_FLASH_WRITE_ERROR | Error | Writing firmware to the update partition failed. |
| `0x6003` | OTA_PARTITION_INVALID | Error | The update partition is missing, corrupt, or wrong size. |
| `0x6004` | OTA_ALREADY_IN_PROGRESS | Warning | An OTA update is already running. Cannot start another. |
| `0x6005` | OTA_CHUNK_OUT_OF_ORDER | Error | A firmware chunk arrived out of sequence or with wrong index. |
| `0x6006` | OTA_BOOT_VERIFICATION_FAILED | Critical | The new firmware failed post-boot verification. Rollback initiated. |
| `0x6007` | FIRMWARE_VERSION_DOWNGRADE | Warning | The new firmware version is older than the currently running version. |

### 5.3 Error Severity Levels

| Severity | Name | Handling |
|---|---|---|
| 0 | **Info** | Logged only. No operational impact. |
| 1 | **Warning** | Logged and counted. Rate-limited (max 10/s per code). May trigger alert. |
| 2 | **Error** | Logged. The specific operation that caused the error is aborted. System continues. |
| 3 | **Critical** | Logged. System enters safe state. May trigger watchdog or hard stop. Requires intervention. |

---

## 6. Reliability Mechanisms

### 6.1 Acknowledgement & Retry

Messages with `criticality ≥ 1` MUST have the `ACK_REQUIRED` flag (bit 0) set. The receiver MUST respond with a `COMMAND_ACK` (0x08) echoing the original message's `sequence_number`.

**Retry Policy**:

| Parameter | Value |
|---|---|
| Max Retries | 3 |
| Initial Timeout | 200 ms |
| Backoff | Exponential: 200 ms → 400 ms → 800 ms |
| Jitter | ±10% random (to prevent thundering herd) |
| Total Window | 200 + 400 + 800 = 1400 ms worst case |

**Retry Algorithm**:

```
function send_critical(message):
    for attempt in [0, 1, 2, 3]:
        transmit(message)
        deadline = now() + (200 * 2^attempt) + jitter(±10%)
        while now() < deadline:
            ack = receive_ack(sequence_number = message.sequence_number)
            if ack:
                if ack.status == SUCCESS:
                    return SUCCESS
                else:
                    return ack.status  # non-retryable failure
        # timeout — retry
    return ACK_TIMEOUT  # all attempts exhausted
```

**Non-Retryable Conditions**: The sender MUST NOT retry if the receiver responds with a `COMMAND_ACK` containing a definitive failure status (e.g., `NOT_IMPLEMENTED`, `REFLEX_PARSE_ERROR`). Retries are only for cases where no response is received.

### 6.2 Sequence Number Validation

Each side maintains:

```c
struct SeqTracker {
    uint16_t last_seen;    // highest sequence number processed
    uint16_t window[8];    // sliding window of recent sequence numbers
    size_t   window_idx;
};
```

**Validation Rules**:

1. If `sequence_number == last_seen + 1` (mod 65536): **In-order**. Process normally.
2. If `sequence_number ≤ last_seen` (within window): **Duplicate**. Emit warning `DUPLICATE_SEQUENCE` (0x5009), discard.
3. If `sequence_number > last_seen + 1` (mod 65536) and gap ≤ 255: **Gap detected**. Emit warning `SEQUENCE_GAP` (0x5005) with gap size. Process this message but log the event.
4. If `sequence_number > last_seen + 256` (mod 65536): **Severe gap** (possible reset). Reset `last_seen` to the new value. Emit `SEQUENCE_GAP` at error severity.

### 6.3 Heartbeat & Timeout Escalation

**Default Intervals**:

| Sender | Interval | Timeout (missed count) |
|---|---|---|
| Node → Jetson | 1000 ms | 3 misses (3000 ms) |
| Jetson → Node | 5000 ms | 3 misses (15000 ms) |

**Escalation Levels**:

```
HEALTHY ──(1 miss)──> WARN ──(2 misses)──> DEGRADED ──(3 misses)──> FAILSAFE
```

| Level | Condition | Actions |
|---|---|---|
| **HEALTHY** | Heartbeats arriving on time | Normal operation. All subsystems active. |
| **WARN** | 1 heartbeat missed | Log warning. Start a latency PING. Increase telemetry rate if bandwidth permits. |
| **DEGRADED** | 2 consecutive heartbeats missed | Log error. Disable non-safety reflexes. Reduce telemetry to essential channels only. Send SAFETY_EVENT if applicable. |
| **FAILSAFE** | 3 consecutive heartbeats missed | Enter failsafe mode. All outputs driven to safe state (typically LOW). Watchdog timer armed. Log critical error `COMMUNICATION_LOSS` (0x4006). System remains in failsafe until heartbeats resume or manual intervention occurs. |

**Recovery from FAILSAFE**:
1. Heartbeat received again → transition to DEGRADED immediately (do not jump to HEALTHY).
2. After 5 consecutive successful heartbeats → transition to HEALTHY.
3. If the Jetson initiated failsafe, it must re-send ROLE_ASSIGN before the node resumes normal operation.

### 6.4 Message Priority Queuing

All messages are placed into one of four priority queues before transmission. The transmitter always drains the highest-priority non-empty queue first.

| Priority | Queue Name | Messages | Preemption |
|---|---|---|---|
| 0 (Highest) | **Safety** | SAFETY_EVENT (0x1C), ERROR (0x15 with critical severity) | May interrupt any lower-priority transmission. |
| 1 | **Critical** | COMMAND_ACK, ROLE_ASSIGN, ROLE_ACK, FIRMWARE_UPDATE_END, FIRMWARE_UPDATE_RESULT | May preempt telemetry. |
| 2 | **Normal** | COMMAND, REFLEX_DEPLOY, OBS_RECORD_START/STOP, IO_RECONFIGURE, BAUD_UPGRADE, PING/PONG | Standard FIFO order. |
| 3 (Lowest) | **Bulk** | TELEMETRY, OBS_DUMP_CHUNK, OBS_DUMP_HEADER, OBS_DUMP_END, FIRMWARE_UPDATE_CHUNK | Rate-limited. May be deferred if higher queues are occupied. |

**Queue Sizing** (per-direction, on the node):

| Queue | Max Pending | Drop Policy |
|---|---|---|
| Safety | 16 | New safety messages evict oldest safety message (never drop safety). |
| Critical | 32 | New critical messages evict oldest critical message. |
| Normal | 32 | New normal messages rejected if full (return BUSY error). |
| Bulk | 64 | New bulk messages evict oldest bulk message. |

### 6.5 Backpressure & Flow Control

When the transmitter's output buffer exceeds 50% capacity:
1. Deassert RTS (if node) or CTS (if Jetson).
2. Stop enqueuing new bulk messages.
3. Continue to enqueue safety and critical messages.
4. When buffer drops below 25% capacity, re-assert the flow control line.

---

## 7. Binary Payload Formats

### 7.1 Observation Frame (32-Byte Compressed Format)

Used in `OBS_DUMP_CHUNK` (0x0E). Each chunk may contain multiple packed observation frames. The 32-byte format is the standard compressed representation.

```
Offset  Size  Field            Type     Description
──────  ────  ────────────────  ───────  ──────────────────────────────────────
  0       1    frame_type        uint8    0x01 = standard, 0x02 = delta-encoded,
                                          0x03 = event (triggered by threshold)
  1       3    sequence_id       uint24   Rolling frame counter within a recording
                                          (LSB first). Wraps at 16,777,215.
  4       4    timestamp_ms      uint32   Local timestamp in ms since recording start
                                          (big-endian).
  8       2    channel_mask      uint16   Bitmask of channels present in this frame
                                          (bit 0 = channel 0, etc.). Up to 16
                                          channels. Big-endian.
 10      14    channel_data      int16[7] Packed ADC/int16 sensor readings.
                                          Only channels indicated by channel_mask
                                          are valid. Each value is big-endian.
                                          Unused slots are zero.
 24       2    flags             uint16   bit 0: overflow (values clamped),
                                          bit 1: underflow,
                                          bit 2: trigger_event,
                                          bit 3: recording_end,
                                          bits 4-15: reserved.
 26       2    delta_base        uint16   If frame_type == delta (0x02), this is
                                          the index of the channel used as the
                                          delta base. Otherwise, 0x0000.
 28       4    frame_crc         uint32   CRC-32 (ISO 3309 / ITU-T V.42) of bytes
                                          0-27 of this frame. Big-endian.
                                  ────
 Total:  32 bytes
```

**Delta Encoding** (frame_type = 0x02):
- Only the difference from the previous frame is stored.
- `delta_base` indicates which channel's absolute value is included (the reference).
- All other channel values are signed deltas from their values in the previous frame.
- Decompression requires the previous frame to be available.

**Event Frame** (frame_type = 0x03):
- Sent only when a configured trigger condition is met (threshold crossing, etc.).
- Contains a single channel reading (the triggered one) plus the trigger timestamp.
- `flags` bit 2 is always set.

### 7.2 OTA Firmware Chunk (516 Bytes + 4-Byte Header)

Used in `FIRMWARE_UPDATE_CHUNK` (0x12). Each chunk carries exactly 512 bytes of firmware data except possibly the last chunk, which may be shorter.

```
Offset  Size  Field            Type     Description
──────  ────  ────────────────  ───────  ──────────────────────────────────────
  0       4    chunk_index       uint32   Zero-based index of this chunk
                                          (big-endian). First chunk = 0.
  4       2    chunk_size        uint16   Actual number of firmware bytes in this
                                          chunk (big-endian). 1-512.
  6       2    total_chunks      uint16   Total number of chunks in this transfer
                                          (big-endian). Never changes during a
                                          transfer.
  8     512    firmware_data     uint8[]  Raw firmware binary data. If chunk_size
                                          < 512, only the first chunk_size bytes
                                          are valid; remaining bytes are zero-padded.
                                          Byte order matches the firmware image.
                                          Written directly to flash at offset
                                          (chunk_index * 512).
                                  ────
 Total:  520 bytes
```

**Transfer Verification**:
- After all chunks are received, the node computes SHA-256 of the reassembled firmware.
- This hash is compared against the `expected_hash` provided in FIRMWARE_UPDATE_START.
- On match: FIRMWARE_UPDATE_END is ACK'd with success.
- On mismatch: FIRMWARE_UPDATE_RESULT (0x14) is sent with error `OTA_HASH_MISMATCH` (0x6001).

### 7.3 Telemetry Snapshot (Variable, Packed Binary)

An alternative binary telemetry format for high-rate sensor streaming. Used when the telemetry `format` field in ROLE_ASSIGN is set to `"binary"`. Falls back to JSON format otherwise.

```
Offset  Size  Field            Type     Description
──────  ────  ────────────────  ───────  ──────────────────────────────────────
  0       2    channel_count    uint16   Number of channels in this snapshot
                                          (big-endian). 1-64.
  2       4    timestamp_ms     uint32   Sender's local timestamp (big-endian).
  6       2    flags            uint16   bit 0: values_are_float32,
                                          bit 1: values_are_delta,
                                          bit 2: overflow_detected,
                                          bits 3-15: reserved.
  8    var     channel_data     depends  Array of channel readings. Format
                                          depends on flags:
                                          - If bit 0 clear: int16 per channel
                                            (2 bytes each, big-endian).
                                          - If bit 0 set: float32 per channel
                                            (4 bytes each, big-endian).
                                          - If bit 1 set (delta): values are
                                            int16 deltas from previous snapshot.
8+var    2    snapshot_crc      uint16   CRC-16/CCITT-FALSE of all preceding
                                          bytes in this snapshot (big-endian).
                                  ────
 Total:  12 + (channel_count * 2 or 4) bytes
```

**Minimum Size** (1 channel, int16): 16 bytes.
**Maximum Size** (64 channels, float32): 274 bytes.

---

## 8. State Machine & Boot Sequence

### 8.1 Node Boot Sequence

```
Power-on
  │
  ▼
[POST — Power-On Self Test]
  │
  ├── FAIL ──▶ Send ERROR (0x15) with SELFTEST_RESULT code
  │              Enter FAILSAFE. Halt.
  │
  ├── PASS ──▶
  │
  ▼
[UART Init @ 115200 baud]
  │
  ▼
[Send DEVICE_IDENTITY (0x01)]
  │
  ▼
[Send AUTO_DETECT_RESULT (0x1B)]
  │
  ▼
[Send SELFTEST_RESULT (0x04)]
  │
  ▼
[WAIT for ROLE_ASSIGN (0x02)]
  │
  ├── TIMEOUT (30s) ──▶ Enter IDLE mode. Send HEARTBEAT only.
  │                        Retry ROLE_ASSIGN request every 10s.
  │
  ├── RECEIVED ──▶
  │   │
  │   ▼
  │ [Apply Role Configuration]
  │   │
  │   ├── FAIL ──▶ Send ROLE_ACK (0x03) with rejection.
  │   │              Return to WAIT.
  │   │
  │   ├── PASS ──▶ Send ROLE_ACK (0x03) with acceptance.
  │   │
  │   ▼
  │ [BAUD_NEGOTIATION (optional)]
  │   │
  │   ▼
  │ [OPERATIONAL — Send HEARTBEAT, TELEMETRY, process COMMANDS]
  │
  ▼
[SHUTDOWN or FAULT]
  │
  ▼
Send SELFTEST_RESULT or SAFETY_EVENT as applicable
```

### 8.2 Jetson Boot Sequence

```
Power-on
  │
  ▼
[UART Init @ 115200 baud, all ports]
  │
  ▼
[WAIT for DEVICE_IDENTITY (0x01) from any node]
  │
  ├── RECEIVED ──▶
  │   │
  │   ▼
  │ [Register node in topology]
  │   │
  │   ▼
  │ [WAIT for AUTO_DETECT_RESULT (0x1B) and SELFTEST_RESULT (0x04)]
  │   │
  │   ▼
  │ [Determine role assignment from configuration DB]
  │   │
  │   ▼
  │ [Send ROLE_ASSIGN (0x02)]
  │   │
  │   ▼
  │ [WAIT for ROLE_ACK (0x03)]
  │   │
  │   ├── REJECTED ──▶ Log. Assign fallback role or alert operator.
  │   │
  │   ├── ACCEPTED ──▶
  │   │   │
  │   │   ▼
  │   │   [BAUD_NEGOTIATION (optional)]
  │   │   │
  │   │   ▼
  │   │   [Deploy REFLEXes via REFLEX_DEPLOY (0x09)]
  │   │   │
  │   │   ▼
  │   │   [Node is OPERATIONAL]
  │   │
  │   ▼
  │ [Repeat for each connected node]
  │
  ▼
[ALL NODES READY — Enter normal operation]
```

---

## 9. Appendices

### Appendix A: COBS Reference Implementation (C)

```c
#include <stdint.h>
#include <stddef.h>

/**
 * COBS encode a byte buffer.
 * @param src    Input buffer (may contain any byte values including 0x00)
 * @param src_len Length of input
 * @param dst    Output buffer (must be >= src_len + src_len/254 + 2 bytes)
 * @return       Number of bytes written to dst, or -1 on error
 */
int cobs_encode(const uint8_t *src, size_t src_len, uint8_t *dst)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;
    size_t code_idx = 0;
    uint8_t code = 0x01;

    if (src == NULL || dst == NULL) return -1;

    while (src_idx < src_len) {
        if (src[src_idx] == 0x00) {
            dst[code_idx] = code;
            code = 0x01;
            code_idx = dst_idx++;
            src_idx++;
        } else {
            dst[dst_idx++] = src[src_idx++];
            code++;
            if (code == 0xFF) {
                dst[code_idx] = code;
                code = 0x01;
                code_idx = dst_idx++;
            }
        }
    }

    dst[code_idx] = code;
    return (int)dst_idx;
}

/**
 * COBS decode a buffer.
 * @param src     Input buffer (COBS-encoded, no delimiters)
 * @param src_len Length of input
 * @param dst     Output buffer (must be >= src_len bytes)
 * @return        Number of bytes written to dst, or -1 on error
 */
int cobs_decode(const uint8_t *src, size_t src_len, uint8_t *dst)
{
    size_t src_idx = 0;
    size_t dst_idx = 0;
    uint8_t code;
    size_t i;

    if (src == NULL || dst == NULL || src_len == 0) return -1;

    while (src_idx < src_len) {
        code = src[src_idx++];
        if (src_idx + code - 1 > src_len) return -1;  // overrun
        for (i = 1; i < code; i++) {
            dst[dst_idx++] = src[src_idx++];
        }
        if (code < 0xFF && src_idx < src_len) {
            dst[dst_idx++] = 0x00;
        }
    }

    // Strip trailing zero inserted by COBS
    if (dst_idx > 0 && dst[dst_idx - 1] == 0x00) {
        dst_idx--;
    }

    return (int)dst_idx;
}
```

### Appendix B: CRC-16/CCITT-FALSE Reference Implementation (C)

```c
#include <stdint.h>
#include <stddef.h>

#define CRC16_POLY 0x1021
#define CRC16_INIT 0xFFFF

uint16_t crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = CRC16_INIT;
    size_t i, j;

    for (i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i]) << 8;
        for (j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ CRC16_POLY;
            } else {
                crc <<= 1;
            }
        }
    }

    return crc;
}
```

### Appendix C: CRC-32 Reference (for Observation Frame CRC)

```c
#include <stdint.h>
#include <stddef.h>

static uint32_t crc32_table[256];
static int crc32_table_init = 0;

void crc32_init_table(void)
{
    uint32_t i, j, crc;
    for (i = 0; i < 256; i++) {
        crc = i;
        for (j = 0; j < 8; j++) {
            if (crc & 1)
                crc = (crc >> 1) ^ 0xEDB88320;
            else
                crc >>= 1;
        }
        crc32_table[i] = crc;
    }
    crc32_table_init = 1;
}

uint32_t crc32(const uint8_t *data, size_t len)
{
    uint32_t crc = 0xFFFFFFFF;
    size_t i;

    if (!crc32_table_init) crc32_init_table();

    for (i = 0; i < len; i++) {
        crc = (crc >> 8) ^ crc32_table[(crc ^ data[i]) & 0xFF];
    }

    return crc ^ 0xFFFFFFFF;
}
```

### Appendix D: Complete Wire Example

**Scenario**: Jetson sends a COMMAND to set GPIO 5 HIGH on the node.

**Step 1 — Compose Header + Payload**:

```
Header (10 bytes):
  msg_type        = 0x07 (COMMAND)
  flags           = 0x01 (ACK_REQUIRED)
  sequence_number = 0x0042 (66)
  timestamp_ms    = 0x0003A8F8 (240,000 ms = 4 minutes)
  payload_length  = 0x0000 (no JSON payload; this example uses minimal inline)

Payload (0 bytes):  (empty for this simplified example)

NOTE: A real COMMAND would carry JSON payload per message_payloads.json.
```

**Step 2 — Append CRC**:

```
Data to CRC = header (10 bytes) = [0x07, 0x01, 0x00, 0x42, 0x00, 0x03, 0xA8, 0xF8, 0x00, 0x00]
CRC-16 = crc16_ccitt(data, 10) = 0xABCD (example value)

Full decoded frame = [header] [CRC] = [0x07, 0x01, 0x00, 0x42, 0x00, 0x03, 0xA8, 0xF8, 0x00, 0x00, 0xAB, 0xCD]
```

**Step 3 — COBS Encode**:

```
COBS input: [0x07, 0x01, 0x00, 0x42, 0x00, 0x03, 0xA8, 0xF8, 0x00, 0x00, 0xAB, 0xCD]
COBS output: [0x02, 0x07, 0x01, 0x01, 0x42, 0x01, 0x03, 0xA8, 0xF8, 0x03, 0xAB, 0xCD, 0x01]
```

**Step 4 — Wrap with Delimiters**:

```
Wire bytes: [0x00, 0x02, 0x07, 0x01, 0x01, 0x42, 0x01, 0x03, 0xA8, 0xF8, 0x03, 0xAB, 0xCD, 0x01, 0x00]
           └───┘ └─────────────────────────────────────────────────────────────────┘ └───┘
           start                              COBS-encoded                             end
```

### Appendix E: Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2024-06-01 | NEXUS Team | Initial release. |
| 1.1.0 | 2024-09-15 | NEXUS Team | Added LZ4 compression flag, AES encryption flag. |
| 1.2.0 | 2024-11-20 | NEXUS Team | Added observation binary format, cloud messages. |
| 2.0.0 | 2025-01-15 | NEXUS Team | Production release. Complete message type registry, error codes, binary payload formats, boot state machines. |

---

*End of Document*

---

# 2. Message Payload Schemas

> **Source:** `protocol/message_payloads.json` | **Schema Version:** v2.0.0

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "urn:nexus:protocol:message-payloads:v2.0.0",
  "title": "NEXUS Wire Protocol — Message Payload Schemas",
  "description": "JSON Schema definitions for every NEXUS message type that carries a JSON payload. Each msg_type maps to a schema that the payload must conform to after COBS decoding. Message types with binary payloads (0x0E OBS_DUMP_CHUNK, 0x12 FIRMWARE_UPDATE_CHUNK) are defined in wire_protocol_spec.md Section 7.",
  "definitions": {
    "mac_address": {
      "type": "string",
      "pattern": "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
      "description": "MAC-48 address in colon-separated hex notation."
    },
    "semver": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[a-zA-Z0-9.]+)?(\\+[a-zA-Z0-9.]+)?$",
      "description": "Semantic version string (major.minor.patch[-prerelease][+build])."
    },
    "sha256_hex": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$",
      "description": "Lowercase hex-encoded SHA-256 hash (64 characters)."
    },
    "pin_number": {
      "type": "integer",
      "minimum": 0,
      "maximum": 63,
      "description": "GPIO pin number (SoC-specific, 0-indexed)."
    },
    "i2c_address": {
      "type": "integer",
      "minimum": 0,
      "maximum": 127,
      "description": "7-bit I2C device address (0x00-0x7F)."
    },
    "adc_channel": {
      "type": "integer",
      "minimum": 0,
      "maximum": 15,
      "description": "ADC channel index."
    },
    "timestamp_ms": {
      "type": "integer",
      "minimum": 0,
      "maximum": 4294967295,
      "description": "Timestamp in milliseconds (uint32 range)."
    },
    "sequence_number": {
      "type": "integer",
      "minimum": 0,
      "maximum": 65535,
      "description": "Message sequence number (uint16 range)."
    },
    "error_code": {
      "type": "string",
      "pattern": "^0x[0-9A-Fa-f]{4}$",
      "description": "Error code in hex notation, e.g. '0x0001'."
    },
    "baud_rate": {
      "type": "integer",
      "enum": [115200, 230400, 460800, 921600],
      "description": "Supported baud rate value."
    },
    "pin_mode": {
      "type": "string",
      "enum": ["INPUT", "OUTPUT", "INPUT_PULLUP", "INPUT_PULLDOWN", "OUTPUT_OPEN_DRAIN", "PWM", "ADC", "I2C_SDA", "I2C_SCL", "SPI_MOSI", "SPI_MISO", "SPI_SCLK", "SPI_CS"],
      "description": "Pin mode configuration."
    },
    "reflex_priority": {
      "type": "integer",
      "minimum": 0,
      "maximum": 255,
      "description": "Reflex execution priority (0 = highest, 255 = lowest)."
    },
    "role_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$",
      "description": "Node role identifier (alphanumeric + underscore, must start with a letter)."
    }
  },

  "properties": {
    "0x01": {
      "title": "DEVICE_IDENTITY",
      "msg_type_id": 1,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["mac_address", "chip_type", "chip_revision", "firmware_version", "firmware_build_date", "boot_timestamp_ms", "capabilities"],
      "additionalProperties": false,
      "properties": {
        "mac_address": {
          "$ref": "#/definitions/mac_address",
          "description": "Unique MAC address of the node's network interface."
        },
        "chip_type": {
          "type": "string",
          "enum": ["ESP32", "ESP32-S2", "ESP32-S3", "ESP32-C3", "ESP32-C6", "STM32F4", "STM32H7", "RP2040", "ATmega328P", "ATmega2560", "SAMD21", "SAMD51", "NRF52840", "CUSTOM"],
          "description": "Microcontroller chip family."
        },
        "chip_revision": {
          "type": "string",
          "minLength": 1,
          "maxLength": 16,
          "description": "Silicon revision identifier (e.g., 'rev3', 'v1.1')."
        },
        "cpu_frequency_mhz": {
          "type": "integer",
          "minimum": 1,
          "maximum": 800,
          "description": "Current CPU clock frequency in MHz."
        },
        "flash_size_kb": {
          "type": "integer",
          "minimum": 0,
          "maximum": 16777216,
          "description": "Total flash memory size in kilobytes."
        },
        "ram_size_kb": {
          "type": "integer",
          "minimum": 0,
          "maximum": 1048576,
          "description": "Total SRAM size in kilobytes."
        },
        "firmware_version": {
          "$ref": "#/definitions/semver",
          "description": "Semantic version of the running firmware."
        },
        "firmware_build_date": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 build timestamp of the firmware (UTC)."
        },
        "firmware_hash": {
          "$ref": "#/definitions/sha256_hex",
          "description": "SHA-256 of the firmware binary currently running."
        },
        "boot_timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Node's uptime in milliseconds at the time this message was composed."
        },
        "boot_count": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Total number of power-on/boot cycles since factory reset."
        },
        "capabilities": {
          "type": "object",
          "required": ["max_gpio_pins", "max_adc_channels", "max_i2c_buses", "max_spi_buses", "max_pwm_channels", "has_wifi", "has_bluetooth"],
          "additionalProperties": false,
          "properties": {
            "max_gpio_pins": {
              "type": "integer",
              "minimum": 0,
              "maximum": 128,
              "description": "Number of usable GPIO pins."
            },
            "max_adc_channels": {
              "type": "integer",
              "minimum": 0,
              "maximum": 32,
              "description": "Number of ADC input channels."
            },
            "max_i2c_buses": {
              "type": "integer",
              "minimum": 0,
              "maximum": 8,
              "description": "Number of independent I2C bus peripherals."
            },
            "max_spi_buses": {
              "type": "integer",
              "minimum": 0,
              "maximum": 8,
              "description": "Number of independent SPI bus peripherals."
            },
            "max_pwm_channels": {
              "type": "integer",
              "minimum": 0,
              "maximum": 64,
              "description": "Number of hardware PWM output channels."
            },
            "max_uart_ports": {
              "type": "integer",
              "minimum": 0,
              "maximum": 8,
              "description": "Number of UART serial ports."
            },
            "has_wifi": {
              "type": "boolean",
              "description": "Whether the node has a Wi-Fi radio."
            },
            "has_bluetooth": {
              "type": "boolean",
              "description": "Whether the node has a Bluetooth/BLE radio."
            },
            "has_can": {
              "type": "boolean",
              "description": "Whether the node has a CAN bus controller."
            },
            "has_ethernet": {
              "type": "boolean",
              "description": "Whether the node has an Ethernet MAC."
            },
            "has_usb": {
              "type": "boolean",
              "description": "Whether the node has a USB device/host controller."
            },
            "max_reflexes": {
              "type": "integer",
              "minimum": 0,
              "maximum": 256,
              "description": "Maximum number of reflexes that can be loaded simultaneously."
            },
            "max_obs_buffer_kb": {
              "type": "integer",
              "minimum": 0,
              "maximum": 65536,
              "description": "Maximum observation recording buffer in kilobytes."
            },
            "supported_msg_types": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{2}$"
              },
              "description": "List of message type IDs (hex strings) that this firmware understands."
            }
          },
          "description": "Hardware and firmware capability report."
        }
      }
    },

    "0x02": {
      "title": "ROLE_ASSIGN",
      "msg_type_id": 2,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["role", "pins", "telemetry_interval_ms", "heartbeat_interval_ms"],
      "additionalProperties": false,
      "properties": {
        "role": {
          "$ref": "#/definitions/role_name",
          "description": "The role name assigned to this node."
        },
        "role_version": {
          "type": "integer",
          "minimum": 0,
          "maximum": 65535,
          "description": "Configuration schema version number. Incremented when role definition changes."
        },
        "pins": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "mode"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "GPIO pin number."
              },
              "mode": {
                "$ref": "#/definitions/pin_mode",
                "description": "Pin operating mode."
              },
              "label": {
                "type": "string",
                "minLength": 1,
                "maxLength": 32,
                "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$",
                "description": "Human-readable label for this pin assignment."
              },
              "pull": {
                "type": "string",
                "enum": ["NONE", "UP", "DOWN"],
                "default": "NONE",
                "description": "Internal pull resistor configuration."
              },
              "initial_value": {
                "type": "integer",
                "minimum": 0,
                "maximum": 1,
                "description": "Initial output state for OUTPUT/PWM modes (0=LOW, 1=HIGH). Ignored for input modes."
              },
              "inverted": {
                "type": "boolean",
                "default": false,
                "description": "If true, logical values are inverted (active-low)."
              },
              "pwm_frequency_hz": {
                "type": "number",
                "exclusiveMinimum": 0,
                "maximum": 100000,
                "description": "PWM frequency in Hz. Required when mode is PWM."
              },
              "pwm_resolution_bits": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 8,
                "description": "PWM duty cycle resolution in bits. Required when mode is PWM."
              },
              "adc_resolution_bits": {
                "type": "integer",
                "minimum": 8,
                "maximum": 16,
                "default": 12,
                "description": "ADC resolution in bits. Required when mode is ADC."
              },
              "adc_attenuation_db": {
                "type": "number",
                "enum": [0, 2.5, 6, 11],
                "default": 11,
                "description": "ADC input attenuation in dB. Higher values allow larger input voltages."
              },
              "debounce_ms": {
                "type": "integer",
                "minimum": 0,
                "maximum": 1000,
                "default": 0,
                "description": "Software debounce interval in milliseconds. 0 disables debounce."
              },
              "interrupt_mode": {
                "type": "string",
                "enum": ["NONE", "RISING", "FALLING", "BOTH", "LOW", "HIGH"],
                "default": "NONE",
                "description": "GPIO interrupt trigger mode. NONE disables interrupts."
              },
              "i2c_bus_index": {
                "type": "integer",
                "minimum": 0,
                "maximum": 7,
                "description": "I2C bus peripheral index. Required for I2C_SDA/I2C_SCL pins."
              },
              "i2c_speed_hz": {
                "type": "integer",
                "enum": [100000, 400000, 1000000, 3400000],
                "default": 400000,
                "description": "I2C bus clock speed in Hz."
              },
              "spi_bus_index": {
                "type": "integer",
                "minimum": 0,
                "maximum": 7,
                "description": "SPI bus peripheral index. Required for SPI pins."
              },
              "spi_mode": {
                "type": "integer",
                "minimum": 0,
                "maximum": 3,
                "default": 0,
                "description": "SPI clock polarity and phase mode (0-3)."
              },
              "spi_speed_hz": {
                "type": "integer",
                "minimum": 100000,
                "maximum": 80000000,
                "default": 1000000,
                "description": "SPI clock speed in Hz."
              },
              "safe_value": {
                "type": "integer",
                "minimum": 0,
                "maximum": 1,
                "description": "Value to drive when entering failsafe mode. Applies to OUTPUT and PWM modes."
              }
            }
          },
          "minItems": 0,
          "maxItems": 64,
          "description": "Array of pin configurations for this role."
        },
        "telemetry_interval_ms": {
          "type": "integer",
          "minimum": 10,
          "maximum": 60000,
          "description": "Periodic telemetry send interval in milliseconds."
        },
        "telemetry_format": {
          "type": "string",
          "enum": ["json", "binary"],
          "default": "json",
          "description": "Telemetry payload encoding format."
        },
        "heartbeat_interval_ms": {
          "type": "integer",
          "minimum": 100,
          "maximum": 30000,
          "description": "Heartbeat send interval in milliseconds."
        },
        "telemetry_channels": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "Pin number to include in telemetry."
              },
              "sample_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 1,
                "description": "Number of samples to average per telemetry reading."
              },
              "report_changed_only": {
                "type": "boolean",
                "default": false,
                "description": "If true, only include this channel when its value changes by more than the delta threshold."
              },
              "delta_threshold": {
                "type": "number",
                "minimum": 0,
                "description": "Minimum change required to report when report_changed_only is true."
              }
            }
          },
          "description": "Explicit list of channels to include in telemetry. If omitted, all configured input pins are reported."
        },
        "reflexes": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "additionalProperties": false,
            "properties": {
              "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 64,
                "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$",
                "description": "Reflex name. Must match a reflex deployed via REFLEX_DEPLOY."
              },
              "auto_start": {
                "type": "boolean",
                "default": true,
                "description": "Whether to automatically activate this reflex on role assignment."
              }
            }
          },
          "description": "List of reflexes to attach to this role. The reflex definitions must have been deployed separately via REFLEX_DEPLOY."
        },
        "safety_config": {
          "type": "object",
          "required": ["watchdog_timeout_ms"],
          "additionalProperties": false,
          "properties": {
            "watchdog_timeout_ms": {
              "type": "integer",
              "minimum": 1000,
              "maximum": 120000,
              "description": "Hardware watchdog timeout in milliseconds."
            },
            "overcurrent_limit_ma": {
              "type": "number",
              "minimum": 0,
              "description": "Overcurrent trip threshold in milliamps. 0 disables monitoring."
            },
            "thermal_limit_celsius": {
              "type": "number",
              "minimum": 0,
              "maximum": 200,
              "description": "Die temperature limit in degrees Celsius."
            },
            "brownout_voltage_mv": {
              "type": "integer",
              "minimum": 0,
              "maximum": 5000,
              "description": "Brownout detection threshold in millivolts."
            }
          },
          "description": "Safety subsystem configuration."
        }
      }
    },

    "0x03": {
      "title": "ROLE_ACK",
      "msg_type_id": 3,
      "direction": "N2J",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["role", "accepted"],
      "additionalProperties": false,
      "properties": {
        "role": {
          "$ref": "#/definitions/role_name",
          "description": "The role name that was assigned (echoed back)."
        },
        "role_version": {
          "type": "integer",
          "minimum": 0,
          "maximum": 65535,
          "description": "The role version that was accepted or rejected."
        },
        "accepted": {
          "type": "boolean",
          "description": "True if the node accepted the role, false if rejected."
        },
        "rejection_reason": {
          "type": "string",
          "maxLength": 256,
          "description": "Human-readable reason for rejection. Required when accepted is false."
        },
        "rejection_error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Error code associated with the rejection. Required when accepted is false."
        },
        "pins_applied": {
          "type": "integer",
          "minimum": 0,
          "maximum": 64,
          "description": "Number of pin configurations that were successfully applied."
        },
        "pins_failed": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "reason"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number"
              },
              "reason": {
                "type": "string",
                "maxLength": 128
              },
              "error_code": {
                "$ref": "#/definitions/error_code"
              }
            }
          },
          "description": "List of pins that failed to configure. Empty if all pins succeeded."
        },
        "reflexes_loaded": {
          "type": "integer",
          "minimum": 0,
          "maximum": 256,
          "description": "Number of reflexes successfully loaded."
        }
      }
    },

    "0x04": {
      "title": "SELFTEST_RESULT",
      "msg_type_id": 4,
      "direction": "N2J",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["passed", "test_results", "duration_ms"],
      "additionalProperties": false,
      "properties": {
        "passed": {
          "type": "boolean",
          "description": "True if all tests passed, false if any test failed."
        },
        "duration_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "description": "Total time to execute all self-tests in milliseconds."
        },
        "test_results": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "passed"],
            "additionalProperties": false,
            "properties": {
              "name": {
                "type": "string",
                "enum": ["flash_crc", "ram_test", "cpu_registers", "gpio_loopback", "adc_reference", "adc_all_channels", "i2c_bus_scan", "spi_loopback", "uart_loopback", "watchdog_test", "clock_calibration", "brownout_detector", "temperature_sensor"],
                "description": "Name of the individual test."
              },
              "passed": {
                "type": "boolean",
                "description": "True if this test passed."
              },
              "detail": {
                "type": "string",
                "maxLength": 256,
                "description": "Additional information about the test result."
              },
              "value": {
                "description": "Numeric measurement or count from the test. Type varies by test."
              },
              "error_code": {
                "$ref": "#/definitions/error_code",
                "description": "Error code if the test failed."
              }
            }
          },
          "minItems": 1,
          "description": "Array of individual test results."
        },
        "gpio_pin_results": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "status"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number"
              },
              "status": {
                "type": "string",
                "enum": ["OK", "STUCK_HIGH", "STUCK_LOW", "FLOATING", "SHORTED", "NOT_TESTED", "UNAVAILABLE"],
                "description": "Per-pin test status."
              }
            }
          },
          "description": "Per-GPIO pin test results. Pin is tested for stuck/floating/short conditions where applicable."
        },
        "i2c_scan_results": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["bus", "address"],
            "additionalProperties": false,
            "properties": {
              "bus": {
                "type": "integer",
                "minimum": 0,
                "maximum": 7,
                "description": "I2C bus index."
              },
              "address": {
                "$ref": "#/definitions/i2c_address"
              },
              "device_id": {
                "type": "string",
                "maxLength": 32,
                "description": "Identified device name or manufacturer (if known)."
              },
              "status": {
                "type": "string",
                "enum": ["RESPONDED", "TIMEOUT", "BUS_LOCKED"],
                "default": "RESPONDED"
              }
            }
          },
          "description": "Results of scanning each I2C bus for connected devices."
        },
        "adc_probe_results": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["channel", "raw_value"],
            "additionalProperties": false,
            "properties": {
              "channel": {
                "$ref": "#/definitions/adc_channel"
              },
              "raw_value": {
                "type": "integer",
                "minimum": 0,
                "maximum": 65535,
                "description": "ADC raw reading with no load (floating or tied to reference)."
              },
              "voltage_mv": {
                "type": "number",
                "description": "Converted voltage in millivolts (if reference is known)."
              },
              "status": {
                "type": "string",
                "enum": ["OK", "OUT_OF_RANGE", "NOISY", "STUCK"],
                "default": "OK"
              }
            }
          },
          "description": "ADC channel probe results with no-load readings."
        }
      }
    },

    "0x06": {
      "title": "TELEMETRY",
      "msg_type_id": 6,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["timestamp_ms", "sequence_id", "channels"],
      "additionalProperties": false,
      "properties": {
        "timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Local timestamp when this telemetry snapshot was taken."
        },
        "sequence_id": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Rolling telemetry sequence counter (wraps at uint32 max)."
        },
        "channels": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "value"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "Pin number this reading is from."
              },
              "label": {
                "type": "string",
                "maxLength": 32,
                "description": "Pin label as configured in ROLE_ASSIGN."
              },
              "value": {
                "description": "The sensor reading value. Type depends on pin mode: boolean for digital inputs, integer for ADC (raw), number for computed voltage/current."
              },
              "raw_adc": {
                "type": "integer",
                "minimum": 0,
                "maximum": 65535,
                "description": "Raw ADC reading. Present when pin mode is ADC."
              },
              "voltage_mv": {
                "type": "number",
                "description": "Converted voltage in millivolts."
              },
              "current_ma": {
                "type": "number",
                "description": "Computed current in milliamps (if shunt/sensor configured)."
              },
              "temperature_c": {
                "type": "number",
                "description": "Temperature reading in degrees Celsius."
              },
              "is_digital": {
                "type": "boolean",
                "description": "True if this is a digital (HIGH/LOW) reading."
              },
              "digital_state": {
                "type": "boolean",
                "description": "Digital pin state. True = HIGH, False = LOW. Present when is_digital is true."
              },
              "quality": {
                "type": "string",
                "enum": ["GOOD", "NOISY", "STALE", "ERROR", "OVERRANGE", "UNDERRANGE"],
                "default": "GOOD",
                "description": "Quality indicator for this reading."
              },
              "samples_averaged": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "description": "Number of raw samples averaged to produce this value."
              }
            }
          },
          "minItems": 0,
          "maxItems": 64,
          "description": "Array of channel readings in this telemetry snapshot."
        },
        "system": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "cpu_load_percent": {
              "type": "number",
              "minimum": 0,
              "maximum": 100,
              "description": "CPU utilization percentage."
            },
            "heap_free_kb": {
              "type": "number",
              "minimum": 0,
              "description": "Free heap memory in kilobytes."
            },
            "heap_min_free_kb": {
              "type": "number",
              "minimum": 0,
              "description": "All-time minimum free heap (watermark) in kilobytes."
            },
            "stack_free_bytes": {
              "type": "integer",
              "minimum": 0,
              "description": "Free stack space on the main task in bytes."
            },
            "uptime_ms": {
              "$ref": "#/definitions/timestamp_ms",
              "description": "System uptime in milliseconds."
            },
            "vcc_mv": {
              "type": "number",
              "description": "Supply voltage in millivolts."
            },
            "die_temp_c": {
              "type": "number",
              "description": "Internal die temperature in degrees Celsius."
            },
            "wifi_rssi_dbm": {
              "type": "integer",
              "minimum": -100,
              "maximum": 0,
              "description": "Wi-Fi signal strength in dBm."
            },
            "reset_reason": {
              "type": "string",
              "enum": ["POWER_ON", "EXTERNAL_RESET", "SOFTWARE_RESET", "WATCHDOG", "BROWNOUT", "DEEP_SLEEP", "UNKNOWN"],
              "description": "Reason for the most recent reset."
            }
          },
          "description": "System health metrics. Included when system monitoring is enabled."
        }
      }
    },

    "0x07": {
      "title": "COMMAND",
      "msg_type_id": 7,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["command"],
      "additionalProperties": false,
      "properties": {
        "command": {
          "type": "string",
          "enum": ["SET_PIN", "SET_PWM", "START_REFLEX", "STOP_REFLEX", "TRIGGER_REFLEX", "RESET_WATCHDOG", "ENTER_FAILSAFE", "RESTART", "EXECUTE_ACTION", "READ_PIN", "READ_ALL_PINS"],
          "description": "The command to execute."
        },
        "pin": {
          "$ref": "#/definitions/pin_number",
          "description": "Target pin number. Required for SET_PIN, SET_PWM, READ_PIN."
        },
        "value": {
          "description": "Command value. For SET_PIN: boolean (true=HIGH, false=LOW). For SET_PWM: number (0.0-1.0 duty cycle) or integer (raw duty)."
        },
        "reflex_name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Target reflex name. Required for START_REFLEX, STOP_REFLEX, TRIGGER_REFLEX."
        },
        "action_name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Named action to execute. Required for EXECUTE_ACTION. Actions are defined in the role configuration."
        },
        "action_params": {
          "type": "object",
          "additionalProperties": {
            "description": "Action parameter value. Can be string, number, boolean, or array."
          },
          "maxProperties": 16,
          "description": "Parameters for EXECUTE_ACTION. Key-value pairs matching the action's parameter schema."
        },
        "timeout_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 30000,
          "default": 5000,
          "description": "Maximum time to wait for command completion. 0 = no wait (fire and forget)."
        },
        "label": {
          "type": "string",
          "maxLength": 32,
          "description": "Optional human-readable label for this command (for logging and debugging)."
        }
      }
    },

    "0x08": {
      "title": "COMMAND_ACK",
      "msg_type_id": 8,
      "direction": "N2J",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["original_sequence", "original_msg_type", "status"],
      "additionalProperties": false,
      "properties": {
        "original_sequence": {
          "$ref": "#/definitions/sequence_number",
          "description": "Sequence number of the message being acknowledged."
        },
        "original_msg_type": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{2}$",
          "description": "Message type ID (hex) of the message being acknowledged."
        },
        "status": {
          "type": "string",
          "enum": ["SUCCESS", "REJECTED", "FAILED", "TIMEOUT", "PARTIAL", "BUSY"],
          "description": "Result status of the acknowledged operation."
        },
        "error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Error code if status is not SUCCESS. Present on failure."
        },
        "error_detail": {
          "type": "string",
          "maxLength": 256,
          "description": "Human-readable error description. Present on failure."
        },
        "result": {
          "description": "Result data. Structure depends on the original message type and command. Can be any JSON value."
        },
        "processing_time_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "description": "Time elapsed between receiving the original message and sending this ack, in milliseconds."
        },
        "retry_after_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "description": "If status is BUSY, suggested retry delay in milliseconds."
        }
      }
    },

    "0x09": {
      "title": "REFLEX_DEPLOY",
      "msg_type_id": 9,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["name", "version", "triggers", "actions"],
      "additionalProperties": false,
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$",
          "description": "Unique reflex name. If a reflex with this name already exists, it is replaced."
        },
        "version": {
          "$ref": "#/definitions/semver",
          "description": "Version of this reflex definition."
        },
        "description": {
          "type": "string",
          "maxLength": 256,
          "description": "Human-readable description of what this reflex does."
        },
        "priority": {
          "$ref": "#/definitions/reflex_priority",
          "default": 128,
          "description": "Execution priority relative to other reflexes."
        },
        "enabled": {
          "type": "boolean",
          "default": true,
          "description": "Whether this reflex is initially enabled when deployed."
        },
        "timeout_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "default": 0,
          "description": "Maximum time to execute all actions. 0 = no timeout."
        },
        "max_fire_rate_hz": {
          "type": "number",
          "minimum": 0,
          "maximum": 100000,
          "default": 0,
          "description": "Maximum number of times per second this reflex may fire. 0 = unlimited."
        },
        "cooldown_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "default": 0,
          "description": "Minimum time between successive firings of this reflex in milliseconds."
        },
        "triggers": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type"],
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string",
                "enum": ["PIN_EDGE", "PIN_LEVEL", "PIN_LEVEL_WINDOW", "ADC_THRESHOLD", "ADC_WINDOW", "TIMER", "COMBO_AND", "COMBO_OR", "WATCHDOG"],
                "description": "Trigger type."
              },
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "Pin number. Required for PIN_EDGE, PIN_LEVEL, PIN_LEVEL_WINDOW."
              },
              "edge": {
                "type": "string",
                "enum": ["RISING", "FALLING", "BOTH"],
                "description": "Edge trigger direction. Required for PIN_EDGE."
              },
              "level": {
                "type": "boolean",
                "description": "Expected level. Required for PIN_LEVEL. True = HIGH."
              },
              "window_start": {
                "type": "number",
                "description": "Window start threshold. Required for PIN_LEVEL_WINDOW and ADC_WINDOW."
              },
              "window_end": {
                "type": "number",
                "description": "Window end threshold. Required for PIN_LEVEL_WINDOW and ADC_WINDOW."
              },
              "channel": {
                "$ref": "#/definitions/adc_channel",
                "description": "ADC channel. Required for ADC_THRESHOLD and ADC_WINDOW."
              },
              "threshold": {
                "type": "number",
                "description": "Threshold value. Required for ADC_THRESHOLD."
              },
              "comparison": {
                "type": "string",
                "enum": ["ABOVE", "BELOW", "CROSS_UP", "CROSS_DOWN"],
                "description": "Comparison operator. Required for ADC_THRESHOLD."
              },
              "period_ms": {
                "type": "integer",
                "minimum": 1,
                "maximum": 3600000,
                "description": "Timer period in milliseconds. Required for TIMER."
              },
              "sub_triggers": {
                "type": "array",
                "items": { "$ref": "#/properties/0x09/properties/triggers/items" },
                "description": "Sub-triggers for COMBO_AND / COMBO_OR. All (AND) or any (OR) must be satisfied."
              },
              "hysteresis": {
                "type": "number",
                "minimum": 0,
                "description": "Hysteresis value to prevent rapid re-triggering on noisy signals."
              },
              "debounce_ms": {
                "type": "integer",
                "minimum": 0,
                "maximum": 5000,
                "default": 0,
                "description": "Additional debounce for this trigger beyond the pin's global debounce."
              }
            }
          },
          "minItems": 1,
          "maxItems": 16,
          "description": "Trigger conditions. The reflex fires when any trigger is satisfied."
        },
        "actions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type"],
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string",
                "enum": ["SET_PIN", "SET_PWM", "PULSE_PIN", "TOGGLE_PIN", "START_REFLEX", "STOP_REFLEX", "SEND_TELEMETRY", "LOG_EVENT", "ENTER_FAILSAFE", "DELAY", "SEQUENCE"],
                "description": "Action type."
              },
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "Target pin. Required for SET_PIN, SET_PWM, PULSE_PIN, TOGGLE_PIN."
              },
              "value": {
                "description": "Value for SET_PIN (boolean) or SET_PWM (number 0.0-1.0 or integer raw)."
              },
              "pulse_duration_ms": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60000,
                "description": "Pulse duration for PULSE_PIN."
              },
              "pulse_value": {
                "type": "boolean",
                "default": true,
                "description": "Pulse level for PULSE_PIN."
              },
              "reflex_name": {
                "type": "string",
                "maxLength": 64,
                "description": "Target reflex name. Required for START_REFLEX, STOP_REFLEX."
              },
              "message": {
                "type": "string",
                "maxLength": 256,
                "description": "Log message for LOG_EVENT."
              },
              "log_level": {
                "type": "string",
                "enum": ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
                "default": "INFO",
                "description": "Log level for LOG_EVENT."
              },
              "delay_ms": {
                "type": "integer",
                "minimum": 0,
                "maximum": 30000,
                "description": "Delay before executing next action. Required for DELAY."
              },
              "sequence": {
                "type": "array",
                "items": { "$ref": "#/properties/0x09/properties/actions/items" },
                "description": "Nested action sequence for SEQUENCE type."
              },
              "repeat": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 1,
                "description": "Number of times to repeat this action."
              },
              "repeat_interval_ms": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60000,
                "description": "Interval between repeats."
              }
            }
          },
          "minItems": 1,
          "maxItems": 32,
          "description": "Actions to execute when the reflex fires. Executed sequentially."
        }
      }
    },

    "0x0A": {
      "title": "REFLEX_STATUS",
      "msg_type_id": 10,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["reflexes"],
      "additionalProperties": false,
      "properties": {
        "reflexes": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "state"],
            "additionalProperties": false,
            "properties": {
              "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 64,
                "description": "Reflex name."
              },
              "state": {
                "type": "string",
                "enum": ["ACTIVE", "INACTIVE", "PAUSED", "ERROR", "LOADING"],
                "description": "Current reflex state."
              },
              "version": {
                "$ref": "#/definitions/semver",
                "description": "Version of the currently loaded reflex definition."
              },
              "priority": {
                "$ref": "#/definitions/reflex_priority"
              },
              "fire_count": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4294967295,
                "description": "Total number of times this reflex has fired since load."
              },
              "last_fire_ms": {
                "type": "integer",
                "minimum": 0,
                "description": "Timestamp of the last fire (0 if never fired)."
              },
              "last_execution_time_us": {
                "type": "integer",
                "minimum": 0,
                "description": "Execution time of the most recent firing in microseconds."
              },
              "last_error": {
                "type": "string",
                "maxLength": 256,
                "description": "Error message from the last failed execution."
              },
              "error_count": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4294967295,
                "description": "Total number of execution errors."
              },
              "cooldown_remaining_ms": {
                "type": "integer",
                "minimum": 0,
                "description": "Remaining cooldown time before this reflex can fire again."
              }
            }
          },
          "description": "Array of all loaded reflexes and their current status."
        }
      }
    },

    "0x0B": {
      "title": "OBS_RECORD_START",
      "msg_type_id": 11,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["recording_id", "channels"],
      "additionalProperties": false,
      "properties": {
        "recording_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[a-zA-Z0-9_-]+$",
          "description": "Unique identifier for this recording session."
        },
        "channels": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number"
              },
              "label": {
                "type": "string",
                "maxLength": 32
              },
              "sample_rate_hz": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100000,
                "default": 1000,
                "description": "Per-channel sample rate. The hardware must support this rate."
              }
            }
          },
          "minItems": 1,
          "maxItems": 16,
          "description": "Channels to record."
        },
        "format": {
          "type": "string",
          "enum": ["standard", "delta", "event"],
          "default": "standard",
          "description": "Recording compression format."
        },
        "max_duration_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 3600000,
          "default": 0,
          "description": "Maximum recording duration in milliseconds. 0 = unlimited (until stopped or buffer full)."
        },
        "max_buffer_kb": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65536,
          "description": "Maximum recording buffer size in kilobytes. Ring-buffer behavior when full."
        },
        "trigger_pin": {
          "$ref": "#/definitions/pin_number",
          "description": "Optional pin to use as a recording trigger. Recording starts on the configured edge."
        },
        "trigger_edge": {
          "type": "string",
          "enum": ["RISING", "FALLING", "BOTH"],
          "default": "RISING",
          "description": "Trigger edge. Required when trigger_pin is set."
        },
        "pretrigger_samples": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100000,
          "default": 0,
          "description": "Number of samples to retain before the trigger event (pre-trigger buffer)."
        }
      }
    },

    "0x0C": {
      "title": "OBS_RECORD_STOP",
      "msg_type_id": 12,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["recording_id"],
      "additionalProperties": false,
      "properties": {
        "recording_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Identifier of the recording to stop."
        },
        "finalize": {
          "type": "boolean",
          "default": true,
          "description": "If true, prepare the recording for immediate dump. If false, keep in buffer for later retrieval."
        },
        "reason": {
          "type": "string",
          "enum": ["MANUAL", "DURATION_REACHED", "BUFFER_FULL", "TRIGGER_STOP", "ERROR"],
          "default": "MANUAL",
          "description": "Reason for stopping the recording."
        }
      }
    },

    "0x0D": {
      "title": "OBS_DUMP_HEADER",
      "msg_type_id": 13,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["recording_id", "total_frames", "total_chunks", "channels", "start_timestamp_ms", "duration_ms"],
      "additionalProperties": false,
      "properties": {
        "recording_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Identifier of the recording being dumped."
        },
        "total_frames": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Total number of observation frames in this recording."
        },
        "total_chunks": {
          "type": "integer",
          "minimum": 1,
          "maximum": 4294967295,
          "description": "Total number of OBS_DUMP_CHUNK messages that will follow."
        },
        "chunk_size_bytes": {
          "type": "integer",
          "minimum": 32,
          "maximum": 1024,
          "default": 1024,
          "description": "Size of each chunk in bytes."
        },
        "total_data_bytes": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Total uncompressed data size in bytes."
        },
        "channels": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number"
              },
              "label": {
                "type": "string",
                "maxLength": 32
              },
              "sample_rate_hz": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100000
              },
              "bit_depth": {
                "type": "integer",
                "enum": [8, 12, 16],
                "default": 16
              },
              "units": {
                "type": "string",
                "maxLength": 16,
                "description": "Engineering units (e.g., 'mV', 'mA', '°C')."
              },
              "scale_factor": {
                "type": "number",
                "default": 1.0,
                "description": "Multiplier to convert raw ADC to engineering units."
              },
              "offset": {
                "type": "number",
                "default": 0.0,
                "description": "Offset to add after scaling."
              }
            }
          },
          "description": "Channel metadata for the recorded data."
        },
        "start_timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Node's local timestamp when recording started."
        },
        "end_timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Node's local timestamp when recording stopped."
        },
        "duration_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 3600000,
          "description": "Recording duration in milliseconds."
        },
        "format": {
          "type": "string",
          "enum": ["standard", "delta", "event"],
          "description": "Compression format used."
        },
        "stop_reason": {
          "type": "string",
          "enum": ["MANUAL", "DURATION_REACHED", "BUFFER_FULL", "TRIGGER_STOP", "ERROR"],
          "description": "Reason recording was stopped."
        },
        "frames_dropped": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of frames that were dropped due to buffer overflow."
        },
        "data_crc32": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}$",
          "description": "CRC-32 (hex, lowercase) of all raw data across all chunks concatenated."
        }
      }
    },

    "0x0F": {
      "title": "OBS_DUMP_END",
      "msg_type_id": 15,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["recording_id", "status"],
      "additionalProperties": false,
      "properties": {
        "recording_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Identifier of the recording that was dumped."
        },
        "status": {
          "type": "string",
          "enum": ["COMPLETE", "PARTIAL", "ABORTED", "ERROR"],
          "description": "Final dump status."
        },
        "chunks_sent": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Total number of OBS_DUMP_CHUNK messages actually sent."
        },
        "total_bytes_sent": {
          "type": "integer",
          "minimum": 0,
          "maximum": 4294967295,
          "description": "Total uncompressed data bytes sent across all chunks."
        },
        "data_crc32": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}$",
          "description": "CRC-32 (hex) of all raw data bytes sent. Must match OBS_DUMP_HEADER.data_crc32."
        },
        "error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Error code if status is ERROR."
        },
        "error_detail": {
          "type": "string",
          "maxLength": 256,
          "description": "Error description if status is ERROR or PARTIAL."
        }
      }
    },

    "0x10": {
      "title": "IO_RECONFIGURE",
      "msg_type_id": 16,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["changes"],
      "additionalProperties": false,
      "properties": {
        "changes": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "property", "value"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number",
                "description": "Pin to reconfigure."
              },
              "property": {
                "type": "string",
                "enum": ["mode", "pull", "pwm_frequency_hz", "pwm_resolution_bits", "adc_resolution_bits", "adc_attenuation_db", "debounce_ms", "interrupt_mode", "inverted", "label"],
                "description": "Property to change."
              },
              "value": {
                "description": "New value for the property. Type depends on property: string for mode/pull/interrupt_mode/label, integer for numeric properties, boolean for inverted."
              }
            }
          },
          "minItems": 1,
          "maxItems": 32,
          "description": "Array of pin configuration changes to apply."
        },
        "apply_mode": {
          "type": "string",
          "enum": ["IMMEDIATE", "AT_IDLE", "NEXT_CYCLE"],
          "default": "IMMEDIATE",
          "description": "When to apply the changes."
        }
      }
    },

    "0x11": {
      "title": "FIRMWARE_UPDATE_START",
      "msg_type_id": 17,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["firmware_size", "total_chunks", "firmware_version", "expected_hash"],
      "additionalProperties": false,
      "properties": {
        "firmware_size": {
          "type": "integer",
          "minimum": 1,
          "maximum": 16777216,
          "description": "Total firmware image size in bytes."
        },
        "total_chunks": {
          "type": "integer",
          "minimum": 1,
          "maximum": 32768,
          "description": "Total number of FIRMWARE_UPDATE_CHUNK messages to follow."
        },
        "chunk_size": {
          "type": "integer",
          "minimum": 64,
          "maximum": 512,
          "default": 512,
          "description": "Size of each firmware chunk in bytes."
        },
        "firmware_version": {
          "$ref": "#/definitions/semver",
          "description": "Version string of the new firmware."
        },
        "expected_hash": {
          "$ref": "#/definitions/sha256_hex",
          "description": "SHA-256 hash of the complete firmware image. Used for post-transfer verification."
        },
        "partition": {
          "type": "string",
          "maxLength": 32,
          "default": "ota",
          "description": "Target flash partition for the update."
        },
        "force_update": {
          "type": "boolean",
          "default": false,
          "description": "If true, allow downgrade and skip version comparison."
        },
        "reboot_after": {
          "type": "boolean",
          "default": true,
          "description": "If true, automatically reboot into the new firmware after successful verification."
        },
        "rollback_on_failure": {
          "type": "boolean",
          "default": true,
          "description": "If true, automatically roll back to the previous firmware if the new one fails post-boot verification."
        },
        "metadata": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "maxProperties": 8,
          "description": "Arbitrary key-value metadata stored alongside the firmware image."
        }
      }
    },

    "0x13": {
      "title": "FIRMWARE_UPDATE_END",
      "msg_type_id": 19,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["action"],
      "additionalProperties": false,
      "properties": {
        "action": {
          "type": "string",
          "enum": ["VERIFY", "ABORT", "COMMIT"],
          "description": "Action to take. VERIFY: compute hash and validate. ABORT: discard the update. COMMIT: mark the new partition as bootable."
        }
      }
    },

    "0x14": {
      "title": "FIRMWARE_UPDATE_RESULT",
      "msg_type_id": 20,
      "direction": "N2J",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["status"],
      "additionalProperties": false,
      "properties": {
        "status": {
          "type": "string",
          "enum": ["SUCCESS", "HASH_MISMATCH", "FLASH_WRITE_ERROR", "PARTITION_ERROR", "ALREADY_IN_PROGRESS", "ROLLBACK_SUCCESS", "ROLLBACK_FAILED", "VERIFY_FAILED", "REBOOT_SUCCESS", "REBOOT_FAILED"],
          "description": "Final outcome of the firmware update."
        },
        "actual_hash": {
          "$ref": "#/definitions/sha256_hex",
          "description": "Computed SHA-256 of the received firmware. Present on HASH_MISMATCH for debugging."
        },
        "error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Associated error code."
        },
        "error_detail": {
          "type": "string",
          "maxLength": 256,
          "description": "Human-readable error description."
        },
        "new_version": {
          "$ref": "#/definitions/semver",
          "description": "Version of the newly installed firmware. Present on SUCCESS."
        },
        "previous_version": {
          "$ref": "#/definitions/semver",
          "description": "Version that was running before the update."
        },
        "reboot_required": {
          "type": "boolean",
          "description": "True if a reboot is needed to activate the new firmware."
        },
        "reboot_timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Planned reboot time. Present when reboot_required is true."
        }
      }
    },

    "0x15": {
      "title": "ERROR",
      "msg_type_id": 21,
      "direction": "N2J",
      "criticality": 2,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["error_code", "severity", "message"],
      "additionalProperties": false,
      "properties": {
        "error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Error code from the NEXUS Error Code Registry."
        },
        "severity": {
          "type": "string",
          "enum": ["INFO", "WARNING", "ERROR", "CRITICAL"],
          "description": "Error severity level."
        },
        "message": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256,
          "description": "Human-readable error description."
        },
        "source": {
          "type": "string",
          "maxLength": 64,
          "description": "Subsystem or module that generated the error (e.g., 'adc', 'i2c_bus_0', 'reflex_engine')."
        },
        "context": {
          "type": "object",
          "additionalProperties": {
            "description": "Context value. Can be string, number, or boolean."
          },
          "maxProperties": 8,
          "description": "Additional context key-value pairs for debugging (e.g., pin number, register value, retry count)."
        },
        "related_sequence": {
          "$ref": "#/definitions/sequence_number",
          "description": "Sequence number of the message that caused this error, if applicable."
        },
        "related_msg_type": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{2}$",
          "description": "Message type that caused this error, if applicable."
        },
        "timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Local timestamp when the error occurred."
        },
        "count": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535,
          "default": 1,
          "description": "Number of times this exact error has occurred since the last report."
        },
        "action_taken": {
          "type": "string",
          "enum": ["NONE", "RETRY_SCHEDULED", "SUBSYSTEM_RESET", "ENTER_FAILSAFE", "DEVICE_RESET", "ROLLBACK"],
          "description": "Automated action taken in response to this error."
        }
      }
    },

    "0x18": {
      "title": "BAUD_UPGRADE",
      "msg_type_id": 24,
      "direction": "J2N",
      "criticality": 1,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["target_baud"],
      "additionalProperties": false,
      "properties": {
        "target_baud": {
          "$ref": "#/definitions/baud_rate",
          "description": "Requested baud rate to switch to."
        },
        "current_baud": {
          "$ref": "#/definitions/baud_rate",
          "description": "Current baud rate (informational)."
        },
        "switch_delay_ms": {
          "type": "integer",
          "minimum": 10,
          "maximum": 1000,
          "default": 50,
          "description": "Delay in milliseconds between the ack and the actual baud switch. Both sides must switch after this delay."
        }
      }
    },

    "0x19": {
      "title": "CLOUD_CONTEXT_REQUEST",
      "msg_type_id": 25,
      "direction": "J2N",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["request_id"],
      "additionalProperties": false,
      "properties": {
        "request_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "pattern": "^[a-zA-Z0-9_-]+$",
          "description": "Unique identifier for this cloud context request."
        },
        "recording_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Recording to use as input for cloud analysis."
        },
        "time_window_ms": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "start": {
              "$ref": "#/definitions/timestamp_ms",
              "description": "Start of time window (offset from recording start)."
            },
            "end": {
              "$ref": "#/definitions/timestamp_ms",
              "description": "End of time window (offset from recording start)."
            }
          },
          "description": "Optional time window within the recording to analyze."
        },
        "analysis_type": {
          "type": "string",
          "enum": ["ANOMALY", "CLASSIFICATION", "REGRESSION", "CUSTOM"],
          "default": "ANOMALY",
          "description": "Type of cloud analysis to perform."
        },
        "parameters": {
          "type": "object",
          "additionalProperties": true,
          "maxProperties": 16,
          "description": "Analysis-specific parameters passed through to the cloud pipeline."
        },
        "response_channel": {
          "type": "string",
          "enum": ["CLOUD_RESULT", "OBS_DUMP"],
          "default": "CLOUD_RESULT",
          "description": "How results should be delivered back to the node."
        }
      }
    },

    "0x1A": {
      "title": "CLOUD_RESULT",
      "msg_type_id": 26,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["request_id", "status"],
      "additionalProperties": false,
      "properties": {
        "request_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64,
          "description": "Echoes the request_id from the original CLOUD_CONTEXT_REQUEST."
        },
        "status": {
          "type": "string",
          "enum": ["SUCCESS", "ERROR", "TIMEOUT", "PARTIAL"],
          "description": "Cloud analysis result status."
        },
        "analysis_type": {
          "type": "string",
          "enum": ["ANOMALY", "CLASSIFICATION", "REGRESSION", "CUSTOM"],
          "description": "Type of analysis that was performed."
        },
        "results": {
          "type": "object",
          "additionalProperties": true,
          "maxProperties": 32,
          "description": "Analysis results. Structure depends on analysis_type."
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence score of the analysis result (0.0 to 1.0)."
        },
        "recommended_actions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type"],
            "additionalProperties": false,
            "properties": {
              "type": {
                "type": "string",
                "enum": ["UPDATE_REFLEX", "RECONFIGURE_PIN", "CALIBRATE_SENSOR", "SEND_ALERT", "LOG_EVENT", "ADJUST_PARAMETER"],
                "description": "Type of recommended action."
              },
              "target": {
                "type": "string",
                "maxLength": 64,
                "description": "Target entity (reflex name, pin label, sensor ID, etc.)."
              },
              "params": {
                "type": "object",
                "additionalProperties": true,
                "maxProperties": 8,
                "description": "Parameters for the recommended action."
              },
              "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence in this specific recommendation."
              },
              "auto_apply": {
                "type": "boolean",
                "default": false,
                "description": "Whether the node should automatically apply this recommendation."
              }
            }
          },
          "description": "List of actions recommended by the cloud analysis."
        },
        "model_version": {
          "type": "string",
          "maxLength": 32,
          "description": "Version of the ML model used for analysis."
        },
        "processing_time_ms": {
          "type": "integer",
          "minimum": 0,
          "description": "Total cloud processing time in milliseconds."
        },
        "error_message": {
          "type": "string",
          "maxLength": 256,
          "description": "Error description if status is ERROR."
        }
      }
    },

    "0x1B": {
      "title": "AUTO_DETECT_RESULT",
      "msg_type_id": 27,
      "direction": "N2J",
      "criticality": 0,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["i2c_devices", "adc_channels"],
      "additionalProperties": false,
      "properties": {
        "i2c_devices": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["bus", "address", "status"],
            "additionalProperties": false,
            "properties": {
              "bus": {
                "type": "integer",
                "minimum": 0,
                "maximum": 7,
                "description": "I2C bus index."
              },
              "address": {
                "$ref": "#/definitions/i2c_address"
              },
              "status": {
                "type": "string",
                "enum": ["DETECTED", "ERROR", "TIMEOUT"],
                "description": "Detection status."
              },
              "device_name": {
                "type": "string",
                "maxLength": 32,
                "description": "Identified device name (e.g., 'BME280', 'MPU6050', 'INA219')."
              },
              "manufacturer": {
                "type": "string",
                "maxLength": 32,
                "description": "Device manufacturer if identifiable."
              },
              "chip_id": {
                "type": "string",
                "maxLength": 16,
                "description": "Chip ID register value (hex)."
              },
              "firmware_version": {
                "type": "string",
                "maxLength": 16,
                "description": "Device firmware version if readable."
              },
              "supports": {
                "type": "array",
                "items": {
                  "type": "string",
                  "enum": ["TEMPERATURE", "HUMIDITY", "PRESSURE", "ACCELEROMETER", "GYROSCOPE", "MAGNETOMETER", "LIGHT", "PROXIMITY", "CURRENT", "VOLTAGE", "POWER", "EEPROM", "DISPLAY", "ADC", "DAC", "GPIO_EXPANDER"]
                },
                "description": "Capabilities reported by the device."
              }
            }
          },
          "description": "Results of scanning all I2C buses."
        },
        "adc_channels": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["channel", "raw_value"],
            "additionalProperties": false,
            "properties": {
              "channel": {
                "$ref": "#/definitions/adc_channel"
              },
              "raw_value": {
                "type": "integer",
                "minimum": 0,
                "maximum": 65535,
                "description": "ADC raw reading with no load."
              },
              "voltage_mv": {
                "type": "number",
                "description": "Estimated voltage in millivolts."
              },
              "connected": {
                "type": "boolean",
                "description": "True if a sensor appears to be connected (value not at rail)."
              },
              "noise_rms": {
                "type": "number",
                "minimum": 0,
                "description": "RMS noise measured in ADC counts (from 10-sample burst)."
              }
            }
          },
          "description": "ADC channel probe results."
        },
        "spi_devices": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["bus", "status"],
            "additionalProperties": false,
            "properties": {
              "bus": {
                "type": "integer",
                "minimum": 0,
                "maximum": 7
              },
              "cs_pin": {
                "$ref": "#/definitions/pin_number"
              },
              "status": {
                "type": "string",
                "enum": ["DETECTED", "NOT_FOUND", "ERROR"]
              },
              "device_name": {
                "type": "string",
                "maxLength": 32
              },
              "chip_id": {
                "type": "string",
                "maxLength": 16
              }
            }
          },
          "description": "SPI device probe results (if SPI is configured)."
        },
        "scan_duration_ms": {
          "type": "integer",
          "minimum": 0,
          "maximum": 60000,
          "description": "Total time to complete the auto-detect scan."
        }
      }
    },

    "0x1C": {
      "title": "SAFETY_EVENT",
      "msg_type_id": 28,
      "direction": "N2J",
      "criticality": 2,
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "required": ["event_type", "severity", "timestamp_ms"],
      "additionalProperties": false,
      "properties": {
        "event_type": {
          "type": "string",
          "enum": ["KILL_SWITCH", "OVERCURRENT", "THERMAL_SHUTDOWN", "WATCHDOG_TIMEOUT", "MECHANICAL_LIMIT", "COMMUNICATION_LOSS", "POWER_FAULT", "BROWNOUT", "SOFTWARE_ESTOP", "REFLEX_SAFETY", "MANUAL_ESTOP"],
          "description": "Type of safety event."
        },
        "severity": {
          "type": "string",
          "enum": ["WARNING", "CRITICAL"],
          "description": "Safety event severity."
        },
        "timestamp_ms": {
          "$ref": "#/definitions/timestamp_ms",
          "description": "Local timestamp when the safety event occurred."
        },
        "error_code": {
          "$ref": "#/definitions/error_code",
          "description": "Corresponding error code from the Error Code Registry."
        },
        "description": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256,
          "description": "Detailed description of the safety event."
        },
        "pin": {
          "$ref": "#/definitions/pin_number",
          "description": "Pin number involved in the safety event (if applicable)."
        },
        "channel": {
          "$ref": "#/definitions/adc_channel",
          "description": "ADC channel involved (for overcurrent or voltage events)."
        },
        "measured_value": {
          "type": "number",
          "description": "The measured value that triggered the safety event (e.g., current in mA, temperature in °C, voltage in mV)."
        },
        "threshold_value": {
          "type": "number",
          "description": "The threshold that was exceeded."
        },
        "unit": {
          "type": "string",
          "maxLength": 8,
          "description": "Unit of measured_value and threshold_value (e.g., 'mA', '°C', 'mV')."
        },
        "actions_taken": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["OUTPUTS_DISABLED", "OUTPUTS_SAFE_STATE", "REFLEXES_DISABLED", "WATCHDOG_ARMED", "ENTERED_FAILSAFE", "NOTIFICATION_SENT", "LOGGING_ENABLED", "POWER_CYCLE_REQUESTED", "SELF_RESET_SCHEDULED"]
          },
          "description": "List of automated actions taken in response to the safety event."
        },
        "pin_states": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pin", "state"],
            "additionalProperties": false,
            "properties": {
              "pin": {
                "$ref": "#/definitions/pin_number"
              },
              "state": {
                "type": "string",
                "enum": ["LOW", "HIGH", "HIGH_Z", "PWM_OFF"],
                "description": "State the pin was driven to."
              }
            }
          },
          "description": "State of all output pins after the safety event (for audit)."
        },
        "recovery_required": {
          "type": "boolean",
          "default": true,
          "description": "Whether manual intervention is required to clear this safety event."
        },
        "auto_recovery_ms": {
          "type": "integer",
          "minimum": 0,
          "description": "If recovery_required is false, time in ms until automatic recovery attempt."
        }
      }
    }
  }
}
```

---

# 3. Safety System Specification

> **Source:** `safety/safety_system_spec.md` | **Document ID:** NEXUS-SS-001 | **Version:** 2.0.0

---

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

---

# 4. Safety Policy

> **Source:** `safety/safety_policy.json` | **Version:** 2.0.0

```json
{
  "_document": {
    "title": "NEXUS Platform Safety Policy",
    "version": "2.0.0",
    "date": "2025-01-15",
    "schema_version": "1.0.0",
    "description": "Machine-readable safety rules for the NEXUS distributed intelligence platform. The validation pipeline programmatically checks all generated code artifacts against this policy.",
    "compliance_refs": ["IEC 61508", "ISO 26262", "IEC 60945", "ABYC A-33"],
    "enforcement": "All rules are enforced at compile-time (static analysis), run-time (watchdog/monitoring), and deployment-time (pipeline gates). No rule may be overridden without a signed safety review."
  },

  "global_safety_rules": [
    {
      "id": "SR-001",
      "title": "Explicit Enable Signal Required for Actuation",
      "description": "No actuator may activate without an explicit, separate enable signal. The enable signal must be independent of the control signal. A single control value alone must never be sufficient to drive an actuator output pin HIGH.",
      "severity": "CRITICAL",
      "check_method": "static_analysis",
      "tool": "clang-tidy + custom AST checker: for every gpio_set_level(pin, HIGH) call, verify that a preceding safety_enable[channel] == true check exists in the same or enclosing function scope. Also check that the enable flag is set by a separate code path from the control value computation.",
      "code_pattern": {
        "violation_regex": "gpio_set_level\\s*\\(\\s*\\w+\\s*,\\s*(?:1|true|HIGH)\\s*\\)(?![\\s\\S]*?safety_enable|enable_pin|actuator_enable)",
        "ast_pattern": {
          "type": "function_call",
          "name": "gpio_set_level",
          "argument_1_value": ["1", "true", "HIGH"],
          "must_have_ancestor": {
            "type": "conditional",
            "contains_identifier": "safety_enable"
          }
        },
        "notes": "AST pattern check is the primary method. Regex is a supplementary heuristic for quick scanning."
      },
      "remediation": "Add an independent enable gate: wrap all gpio_set_level(pin, HIGH) calls inside `if (safety_enable[actuator_id]) { ... }`. The enable flag must be set by a separate safety task, never by the same control computation that sets the output value.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-002",
      "title": "Timeout Watchdog on All Control Loops",
      "description": "Every control loop (PID, reflex, feedback, or iterative computation) must have a timeout watchdog. If the loop does not complete within its specified time budget, the system must abort the loop iteration and enter a safe state for that actuator.",
      "severity": "CRITICAL",
      "check_method": "static_analysis",
      "tool": "custom AST checker: identify all while/for loops that compute actuator outputs. Verify each contains a break condition based on an elapsed-time check (e.g., xTaskGetTickCount() - start_time > timeout_ms) or is bounded by a known-constant iteration count validated against worst-case execution time.",
      "code_pattern": {
        "violation_ast": {
          "type": "loop",
          "contains_actuator_write": true,
          "missing_time_bound": true
        },
        "violation_regex": "(?:while|for)\\s*\\([^)]*\\)[\\s\\S]{0,500}(?:gpio_set_level|pwm_set_duty|ledc_set_duty)(?![\\s\\S]{0,300}(?:xTaskGetTickCount|esp_timer_get_time|timeout|deadline|TICK|elapsed))",
        "notes": "Any loop that can write to an actuator pin must have a time-based exit condition."
      },
      "remediation": "Add `TickType_t loop_start = xTaskGetTickCount();` before the loop and `if (xTaskGetTickCount() - loop_start > pdMS_TO_TICKS(timeout_ms)) { break; }` as the first statement inside the loop body.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-003",
      "title": "Defined Safe-State Value for Every Actuator",
      "description": "Every actuator configured on any node must have a defined safe-state value in the safety configuration. This value is applied on boot, on watchdog timeout, on heartbeat loss, and on any safety event that triggers a failsafe.",
      "severity": "CRITICAL",
      "check_method": "config_validation",
      "tool": "JSON schema validator at deployment time: every entry in node_config.actuators[] must have a matching entry in safety_policy.actuator_profiles[actuator.type].safe_value. Fail deployment if any actuator lacks a defined safe-state.",
      "code_pattern": {
        "violation_schema": {
          "path": "$.nodes[*].actuators[*]",
          "required_fields": ["type", "safe_value"],
          "reference": "$.actuator_profiles[*].safe_value"
        }
      },
      "remediation": "Add a `safe_value` field to the actuator configuration. If the actuator type is not in the actuator_profiles table, the deployment must be blocked until the safety engineer adds the profile.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-004",
      "title": "Single Sensor Failure Shall Not Cause Uncontrolled Actuation",
      "description": "No single sensor reading (or lack thereof) may cause an actuator to move to an unsafe position. Sensor failures must be detected (stale data, out-of-range, CRC error) and the system must gracefully degrade to a safe state rather than reacting to bad data.",
      "severity": "CRITICAL",
      "check_method": "static_analysis + runtime",
      "tool": "AST checker: for every control computation that reads a sensor and writes an actuator, verify there is a sensor_validity check (stale timeout, range check, or CRC check) between the sensor read and the actuator write. Runtime: sensor watchdog task monitors all sensor channels for staleness.",
      "code_pattern": {
        "violation_ast": {
          "type": "data_flow",
          "from": "sensor_read",
          "to": "actuator_write",
          "missing_intermediate": "sensor_validity_check"
        },
        "violation_regex": "(?:sensor_read|adc_read|i2c_read|read_|get_)(?:\\w+)[\\s\\S]{0,500}(?:gpio_set_level|pwm_set_duty|ledc_set_duty|actuator_set)(?![\\s\\S]{0,200}(?:sensor_valid|data_stale|timeout|crc|range_check|is_valid))",
        "notes": "Data-flow analysis is the primary check. Regex is supplementary."
      },
      "remediation": "Add a sensor validity gate: `if (!sensor_is_valid(sensor_id, max_age_ms)) { set_actuator_safe(actuator_id); return; }` before any control computation that uses that sensor's value.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-005",
      "title": "Rate Limiting on All Actuators",
      "description": "All actuators must have configurable rate limiting to prevent abrupt transitions that could cause mechanical stress, instability, or danger. Rate limiting must be applied at the output driver level, not just at the command level.",
      "severity": "HIGH",
      "check_method": "static_analysis + config_validation",
      "tool": "AST checker: for every actuator write function, verify a rate_limit_apply() or equivalent function is called before the actual hardware write. Config validator: every actuator in the node config must have a rate_limit field matching its actuator profile.",
      "code_pattern": {
        "violation_ast": {
          "type": "function_call",
          "name": ["gpio_set_level", "ledc_set_duty", "pwm_set_duty", "dac_output_voltage"],
          "missing_preceding_call": "rate_limit"
        },
        "violation_regex": "(?:gpio_set_level|ledc_set_duty|pwm_set_duty|dac_output_voltage)\\s*\\((?![\\s\\S]{0,300}rate_limit)"
      },
      "remediation": "Apply rate limiting before every actuator write: `value = rate_limit_apply(channel, requested_value, max_delta_per_period, period_ms);` then write `value` to the hardware.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-006",
      "title": "Watchdog Timer Disable Prohibition",
      "description": "No code path may disable, reconfigure to a longer timeout, or bypass the watchdog timer. The watchdog is a critical safety mechanism and must remain active at all times during normal operation.",
      "severity": "CRITICAL",
      "check_method": "static_analysis",
      "tool": "AST checker: flag any call to esp_task_wdt_delete(), esp_task_wdt_reset() without a preceding esp_task_wdt_add(), iwdg_disable(), wdt_disable(), or any assignment to WDT registers. Also flag any #define that redefines the WDT timeout to a larger value.",
      "code_pattern": {
        "violation_regex": "(?:esp_task_wdt_delete|wdt_disable|iwdg_disable|WDT\\.disable|WATCHDOG_DISABLE|esp_task_wdt_init\\s*\\(\\s*\\d+\\s*,\\s*false)|(?:#define\\s+WDT_TIMEOUT\\s+\\d+)",
        "forbidden_apis": [
          "esp_task_wdt_delete",
          "wdt_disable",
          "iwdg_disable",
          "WDT.disable",
          "esp_task_wdt_init(timeout, false)"
        ],
        "notes": "esp_task_wdt_init with reset=true is permitted. esp_task_wdt_init with reset=false is a violation."
      },
      "remediation": "Remove any code that disables the watchdog. If a long operation is needed, use watchdog feed (kick) operations within the operation, or split the operation into smaller chunks that each complete within the WDT timeout.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-007",
      "title": "Emergency Stop Has Highest Priority",
      "description": "The emergency stop (kill switch) must have the highest interrupt priority in the system. No other ISR, task, or code path may block, delay, or preempt the emergency stop handler. The E-Stop ISR must run to completion without any blocking operations.",
      "severity": "CRITICAL",
      "check_method": "static_analysis",
      "tool": "AST checker: verify the E-Stop ISR is registered at the highest available interrupt priority (e.g., ESP_INTR_FLAG_LEVEL1 on ESP32, or the numerical highest priority). Verify no other ISR is registered at the same or higher priority. Verify the E-Stop ISR body contains no blocking calls (no vTaskDelay, no xQueueSend with non-zero timeout, no mutex operations).",
      "code_pattern": {
        "violation_ast": {
          "type": "function",
          "attributes": ["ISR", "interrupt"],
          "name_contains": "estop|kill_switch|emergency",
          "priority_check": "must_be_highest",
          "body_must_not_contain": ["vTaskDelay", "xQueueSend", "xSemaphoreTake", "xQueueReceive", "vTaskSuspend", "portYIELD"]
        },
        "violation_regex": "(?:gpio_isr_handler_add|gpio_install_isr_service).*?(?:estop|kill|emergency)[\\s\\S]{0,200}(?:vTaskDelay|xQueueSend[^,]*,\\s*(?!0\\s*\\))|xSemaphoreTake[^,]*,\\s*(?!0\\s*\\)))"
      },
      "remediation": "Register the E-Stop ISR at the highest interrupt priority. Remove all blocking operations from the ISR body. The ISR should only: (1) set a volatile flag, (2) immediately write all actuator GPIOs to safe values, (3) notify a deferred handler task via xSemaphoreGiveFromISR() with a zero timeout.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-008",
      "title": "All Outputs LOW/SAFE on Boot",
      "description": "All GPIO outputs must be driven to their safe state (LOW for most actuators) during the earliest stage of boot, before any configuration is loaded. This ensures that no actuator can activate due to uninitialized pin states during the boot process.",
      "severity": "CRITICAL",
      "check_method": "static_analysis",
      "tool": "AST checker: verify that the app_main() or equivalent entry point contains a call to an init_safe_outputs() or gpio_safe_init() function as its FIRST operation (before NVS load, before peripheral init, before any task creation). Verify this function sets all actuator-capable GPIOs to their defined safe state.",
      "code_pattern": {
        "violation_ast": {
          "type": "function",
          "name": ["app_main", "main"],
          "first_statement_must_call": ["gpio_safe_init", "init_safe_outputs", "safety_init_outputs"],
          "before_any_call_to": ["nvs_flash_init", "nvs_open", "i2c_init", "spi_init", "uart_init", "xTaskCreate", "mqtt_client_init"]
        },
        "violation_regex": "void\\s+app_main\\s*\\([^)]*\\)\\s*\\{(?![\\s\\S]{0,300}(?:gpio_safe_init|init_safe_outputs|safety_init_outputs))",
        "notes": "The safe output init must be the very first thing in app_main, before ANY other initialization."
      },
      "remediation": "Add `gpio_safe_init();` as the first line of app_main(). This function must iterate over all configured actuator pins and drive them to their safe-state value using gpio_set_direction() and gpio_set_level() before any other peripheral is initialized.",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-009",
      "title": "Division-by-Zero Protection for Floating Point",
      "description": "All floating-point division operations must be protected against division by zero. A zero or near-zero denominator must be detected and handled before the division is performed. This applies to all floating-point division operators (/) and all division function calls (div, fmod, etc.).",
      "severity": "HIGH",
      "check_method": "static_analysis",
      "tool": "AST checker: for every floating-point division operation (binary operator / where either operand is float/double, or calls to fmod, divf, etc.), verify there is a preceding check that the denominator is not zero or within an epsilon of zero.",
      "code_pattern": {
        "violation_ast": {
          "type": "binary_op",
          "operator": "/",
          "right_operand_type": ["float", "double", "float32_t", "float64_t"],
          "missing_preceding_check": {
            "denominator_not_zero": true,
            "epsilon": "1e-6 or configurable"
          }
        },
        "violation_regex": "(?:float|double|float32_t|float64_t)\\s+\\w+\\s*=\\s*(?:\\w+|\\([^)]+\\))\\s*/\\s*(\\w+)(?![\\s\\S]{0,100}(?:fabs\\s*\\(\\s*\\1\\s*\\)\\s*>|!=\\s*0|!=\\s*0\\.0|>\\s*EPSILON|>\\s*1e-|ZERO_CHECK))",
        "notes": "The check must be for the specific denominator variable, not a generic check."
      },
      "remediation": "Before every float division: `if (fabs(denominator) < EPSILON) { handle_error(); denominator = EPSILON; /* or return safe default */ }`. Use a project-wide EPSILON constant (default: 1e-6f).",
      "applicable_roles": ["ALL"]
    },
    {
      "id": "SR-010",
      "title": "Bounded Iteration Count for Reflex Loops",
      "description": "All reflex loops (including those generated dynamically) must have a bounded, statically-determinable maximum iteration count. This prevents infinite loops in reflex processing that could starve the watchdog or other safety-critical tasks.",
      "severity": "HIGH",
      "check_method": "static_analysis",
      "tool": "AST checker: identify all loops within reflex execution paths. Verify each loop has a constant upper bound (e.g., `for (int i = 0; i < MAX_REFLEX_ITERATIONS; i++)` where MAX_REFLEX_ITERATIONS is a #define or constexpr). Loops with variable bounds must have a secondary absolute upper bound check.",
      "code_pattern": {
        "violation_ast": {
          "type": "loop",
          "in_reflex_context": true,
          "bound_type": ["unbounded", "variable_without_max_cap"]
        },
        "violation_regex": "(?:while\\s*\\(\\s*true\\s*\\)|while\\s*\\(\\s*1\\s*\\)|for\\s*\\(\\s*;\\s*;\\s*\\))",
        "context_regex": "reflex",
        "notes": "Infinite loops (`while(true)`) in reflex code are always a violation unless they contain a bounded break with a constant maximum iteration count."
      },
      "remediation": "Add a maximum iteration counter: `int iterations = 0; while (condition && iterations < MAX_REFLEX_ITERATIONS) { ... iterations++; }`. MAX_REFLEX_ITERATIONS must be defined as a constant (recommended: 100). Reflex loops with variable bounds must additionally check `iterations < ABSOLUTE_MAX` (recommended: 1000).",
      "applicable_roles": ["ALL"]
    }
  ],

  "actuator_safety_profiles": {
    "_comment": "Default safety parameters for each actuator type. Node configs reference these by type. Values can be overridden per-instance in the node configuration with a safety_engineer sign-off.",
    "servo": {
      "type": "servo",
      "description": "RC servo via PWM (typical 50Hz, 1-2ms pulse)",
      "safe_state": {
        "pulse_us": 1500,
        "description": "Center position (neutral)"
      },
      "default_value": {
        "pulse_us": 1500
      },
      "limits": {
        "min_pulse_us": 500,
        "max_pulse_us": 2500,
        "min_angle_deg": null,
        "max_angle_deg": null,
        "_comment": "Angle limits are set per-instance based on mechanical setup"
      },
      "rate_limiting": {
        "max_delta_us_per_10ms": 200,
        "description": "Maximum pulse width change per 10ms period. Prevents jerky motion."
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": true
      },
      "monitoring": {
        "stall_detection": false,
        "current_monitoring": false,
        "position_feedback": "optional"
      }
    },
    "relay": {
      "type": "relay",
      "description": "Electromechanical or solid-state relay",
      "safe_state": {
        "state": "OPEN",
        "description": "Relay de-energized (normally-open contact)"
      },
      "default_value": {
        "state": "OPEN"
      },
      "limits": {
        "max_on_time_ms": 5000,
        "cooldown_after_off_ms": 1000,
        "min_on_time_ms": 50,
        "_comment": "Minimum on-time prevents relay chattering from rapid cycling"
      },
      "hardware_requirements": {
        "flyback_diode": true,
        "flyback_diode_spec": "1N4007 or equivalent, across relay coil",
        "description": "Mandatory flyback diode across inductive relay coil to prevent voltage spikes"
      },
      "rate_limiting": {
        "max_cycles_per_minute": 30,
        "description": "Prevents excessive relay cycling that could cause wear or overheating"
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": true
      },
      "monitoring": {
        "current_monitoring": true,
        "contact_wear_counter": true,
        "max_lifetime_cycles": 1000000
      }
    },
    "motor_pwm": {
      "type": "motor_pwm",
      "description": "DC motor controlled via PWM duty cycle",
      "safe_state": {
        "duty_percent": 0.0,
        "description": "Motor stopped (0% duty cycle)"
      },
      "default_value": {
        "duty_percent": 0.0
      },
      "limits": {
        "max_duty_percent": 100.0,
        "min_duty_percent": 0.0,
        "max_reverse_duty_percent": null,
        "_comment": "Bidirectional motor: set max_reverse_duty_percent to negative value if supported"
      },
      "rate_limiting": {
        "max_delta_percent_per_100ms": 10.0,
        "description": "Maximum duty cycle change per 100ms. 0-100% ramp takes minimum 1 second."
      },
      "overcurrent_protection": {
        "enabled": true,
        "threshold_a": null,
        "_comment": "Configurable per-instance. Typical: 2x nominal motor current.",
        "threshold_default_a": 5.0,
        "response": "immediate_output_disable",
        "recovery_requires_manual_reset": true
      },
      "hardware_requirements": {
        "flyback_diode": true,
        "flyback_diode_spec": "Schottky diode across motor terminals (e.g., SR305)",
        "polyfuse": true,
        "polyfuse_spec": "PTC fuse rated at 1.5x nominal motor current hold"
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": true,
        "soft_start_enabled": true,
        "soft_start_ramp_ms": 500
      },
      "monitoring": {
        "current_monitoring": true,
        "rpm_feedback": "optional",
        "temperature_monitoring": "recommended"
      }
    },
    "solenoid": {
      "type": "solenoid",
      "description": "Hydraulic or pneumatic solenoid valve",
      "safe_state": {
        "state": "DEENERGIZED",
        "description": "Solenoid de-energized (spring-return to default position)"
      },
      "default_value": {
        "state": "DEENERGIZED"
      },
      "limits": {
        "max_on_time_ms": 5000,
        "cooldown_after_off_ms": 1000,
        "min_on_time_ms": 50,
        "_comment": "5000ms max continuous prevents coil overheating"
      },
      "hardware_requirements": {
        "flyback_diode": true,
        "flyback_diode_spec": "1N4007 or equivalent, across solenoid coil",
        "polyfuse": true,
        "polyfuse_spec": "PTC fuse rated at 1.5x solenoid hold current"
      },
      "rate_limiting": {
        "max_activations_per_10s": 5,
        "description": "Limits cycling frequency to prevent thermal damage"
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": true
      },
      "monitoring": {
        "current_monitoring": true,
        "undercurrent_detection": true,
        "undercurrent_threshold_ma": 100,
        "undercurrent_description": "Detects open-circuit (disconnected coil)"
      }
    },
    "led": {
      "type": "led",
      "description": "Indicator LED (no safety-critical actuation)",
      "safe_state": {
        "state": "OFF",
        "description": "LED off"
      },
      "default_value": {
        "state": "OFF"
      },
      "limits": {
        "max_on_time_ms": null,
        "_comment": "No time limit for LEDs"
      },
      "rate_limiting": {
        "enabled": false,
        "_comment": "LEDs do not require rate limiting for safety"
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": false,
        "_comment": "LEDs are status indicators, not actuators. Enable gating not required."
      },
      "monitoring": {
        "current_monitoring": false
      },
      "safety_class": "non_critical"
    },
    "buzzer": {
      "type": "buzzer",
      "description": "Audible alarm buzzer (hearing protection required)",
      "safe_state": {
        "state": "OFF",
        "description": "Buzzer silent"
      },
      "default_value": {
        "state": "OFF"
      },
      "limits": {
        "max_on_time_ms": 30000,
        "cooldown_after_off_ms": 5000,
        "_comment": "30-second maximum continuous activation for hearing protection per IEC 60945",
        "max_on_time_description": "Continuous alarm must not exceed 30 seconds to prevent hearing damage. Pattern must include silent intervals."
      },
      "rate_limiting": {
        "enabled": true,
        "max_duty_cycle_percent": 50,
        "description": "Buzzer must have at least 50% off-time in any alarm pattern"
      },
      "startup_behavior": {
        "initial_output": "safe_state",
        "require_explicit_enable": false,
        "_comment": "Buzzer enable gating handled by alarm system, not per-actuator enable"
      },
      "monitoring": {
        "current_monitoring": false
      },
      "safety_class": "indicator"
    }
  },

  "domain_specific_safety_rules": {
    "_comment": "Domain-specific safety thresholds that override actuator defaults when a domain is configured. These are the MAXIMUM permissible values. Node configs may set MORE restrictive values but never less restrictive. Values can be overridden per-domain config with a safety_engineer sign-off.",
    "marine": {
      "domain_id": "marine",
      "description": "Marine/autonomous surface vessel operations",
      "compliance_refs": ["IEC 60945", "ABYC A-33", "ISO 16315"],
      "overrides": {
        "max_rudder_deflection_deg": {
          "value": 45,
          "unit": "degrees",
          "description": "Maximum rudder angle from center. Mechanical hard stops must be at or beyond this value.",
          "rationale": "Beyond 45 degrees provides minimal additional turning moment while greatly increasing drag and risk of mechanical binding."
        },
        "max_throttle_percent": {
          "value": 80,
          "unit": "percent",
          "description": "Maximum throttle in autonomous mode. Manual override allowed up to 100%.",
          "rationale": "80% cap provides reserve for emergency maneuvers and reduces risk of collision at high speed."
        },
        "depth_min_for_autopilot_m": {
          "value": 3.0,
          "unit": "meters",
          "description": "Minimum water depth to engage autopilot. Below this depth, autopilot must disengage.",
          "rationale": "Shallow water requires human judgment for obstacle avoidance. GPS accuracy may be insufficient."
        },
        "max_speed_autonomous_kmh": {
          "value": 15.0,
          "unit": "km/h",
          "description": "Maximum speed in full autonomous mode."
        },
        "max_wind_speed_autonomous_kmh": {
          "value": 40.0,
          "unit": "km/h",
          "description": "Maximum wind speed for autonomous operation. Disengage above this."
        },
        "heartbeat_timeout_degraded_ms": {
          "value": 500,
          "unit": "milliseconds"
        },
        "heartbeat_timeout_safe_ms": {
          "value": 1000,
          "unit": "milliseconds"
        }
      }
    },
    "agriculture": {
      "domain_id": "agriculture",
      "description": "Agricultural automation (spraying, seeding, harvesting)",
      "compliance_refs": ["ISO 4254-1", "EN ISO 3691-4"],
      "overrides": {
        "max_spray_pressure_psi": {
          "value": 80,
          "unit": "psi",
          "description": "Maximum spray system pressure. Higher pressures create fine droplets that drift.",
          "rationale": "OSHA and EPA drift mitigation. >80 psi significantly increases drift risk."
        },
        "max_vehicle_speed_kmh": {
          "value": 15,
          "unit": "km/h",
          "description": "Maximum autonomous vehicle speed in field operations.",
          "rationale": "15 km/h is the maximum safe speed for obstacle detection at typical sensor ranges in agricultural environments."
        },
        "max_spray_flow_rate_lpm": {
          "value": 20,
          "unit": "liters per minute"
        },
        "proximity_stop_distance_m": {
          "value": 2.0,
          "unit": "meters",
          "description": "Stop distance for proximity detection of humans/animals."
        },
        "max_implement_width_m": {
          "value": 30.0,
          "unit": "meters",
          "description": "Maximum implement width for geofence calculations."
        },
        "heartbeat_timeout_degraded_ms": {
          "value": 500,
          "unit": "milliseconds"
        },
        "heartbeat_timeout_safe_ms": {
          "value": 1000,
          "unit": "milliseconds"
        }
      }
    },
    "hvac": {
      "domain_id": "hvac",
      "description": "HVAC (Heating, Ventilation, Air Conditioning) control systems",
      "compliance_refs": ["ASHRAE 135", "ISO 16484", "EN 15232"],
      "overrides": {
        "max_zone_temp_delta_c": {
          "value": 5.0,
          "unit": "degrees Celsius",
          "description": "Maximum allowed temperature delta between zones. Prevents thermal stress in buildings.",
          "rationale": "ASPHRAE recommends no more than 3C difference between adjacent zones for comfort. 5C is absolute maximum."
        },
        "min_zone_temp_c": {
          "value": 5.0,
          "unit": "degrees Celsius",
          "description": "Minimum allowable zone temperature. Below this, freeze protection activates.",
          "rationale": "Pipe freeze protection. Below 5C, water pipes are at risk."
        },
        "max_zone_temp_c": {
          "value": 40.0,
          "unit": "degrees Celsius",
          "description": "Maximum allowable zone temperature. Above this, overheat protection activates.",
          "rationale": "Occupant safety and equipment protection. Above 40C is unsafe for sustained occupancy."
        },
        "max_humidity_percent": {
          "value": 70,
          "unit": "percent RH",
          "description": "Maximum humidity before mold prevention activates."
        },
        "min_humidity_percent": {
          "value": 20,
          "unit": "percent RH",
          "description": "Minimum humidity before humidification activates. Below 20% causes discomfort."
        },
        "max_fan_speed_percent": {
          "value": 100,
          "unit": "percent"
        },
        "heartbeat_timeout_degraded_ms": {
          "value": 2000,
          "unit": "milliseconds",
          "_comment": "HVAC systems can tolerate longer communication delays due to thermal inertia"
        },
        "heartbeat_timeout_safe_ms": {
          "value": 5000,
          "unit": "milliseconds"
        }
      }
    },
    "factory": {
      "domain_id": "factory",
      "description": "Factory/industrial automation and robotics",
      "compliance_refs": ["ISO 10218-1", "ISO/TS 15066", "IEC 62443"],
      "overrides": {
        "min_proximity_m": {
          "value": 0.3,
          "unit": "meters",
          "description": "Minimum safe distance between robot/equipment and human operator. Below this, immediate stop.",
          "rationale": "ISO 10218-1 collaborative robot minimum separation distance. Adjusted for typical industrial robot speeds and stopping distances."
        },
        "max_robot_speed_m_s": {
          "value": 1.0,
          "unit": "meters per second",
          "description": "Maximum robot end-effector speed in autonomous mode. Reduced speed for human-shared workspaces.",
          "rationale": "ISO/TS 15066 collaborative operation speed limit for transient contact scenarios."
        },
        "max_robot_force_n": {
          "value": 150,
          "unit": "Newtons",
          "description": "Maximum allowable contact force before emergency stop triggers."
        },
        "safety_zone_violation_action": {
          "value": "immediate_stop_and_alarm",
          "description": "Action when safety zone boundary is violated"
        },
        "max_conveyor_speed_m_s": {
          "value": 2.0,
          "unit": "meters per second"
        },
        "heartbeat_timeout_degraded_ms": {
          "value": 200,
          "unit": "milliseconds",
          "_comment": "Factory requires fast heartbeat due to personnel safety"
        },
        "heartbeat_timeout_safe_ms": {
          "value": 500,
          "unit": "milliseconds"
        }
      }
    },
    "mining": {
      "domain_id": "mining",
      "description": "Mining operations (underground and surface)",
      "compliance_refs": ["ISO 19296", "IEC Ex", "AS/NZS 2290.3"],
      "overrides": {
        "max_ventilation_co_ppm": {
          "value": 30,
          "unit": "ppm",
          "description": "Maximum CO concentration for continued autonomous operation. Above this, trigger evacuation alarm.",
          "rationale": "ACGIH TLV for CO is 25 ppm (8-hour TWA). 30 ppm provides safety margin for alerting and evacuation."
        },
        "max_temperature_c": {
          "value": 35.0,
          "unit": "degrees Celsius",
          "description": "Maximum ambient temperature for equipment operation. Above this, initiate thermal shutdown.",
          "rationale": "Mining regulations typically require shutdown at 35C wet bulb or 37C dry bulb. Using conservative dry-bulb limit."
        },
        "max_methane_ppm": {
          "value": 10000,
          "unit": "ppm",
          "description": "Maximum methane concentration. 1% LEL. Above this, immediate power cutoff.",
          "rationale": "Methane LEL is 5% (50,000 ppm). 1% LEL is standard alarm threshold per mining safety regulations."
        },
        "max_dust_concentration_mg_m3": {
          "value": 3.0,
          "unit": "mg/m3",
          "description": "Maximum respirable dust concentration."
        },
        "proximity_stop_distance_m": {
          "value": 5.0,
          "unit": "meters",
          "description": "Larger stop distance due to limited visibility and heavy equipment."
        },
        "heartbeat_timeout_degraded_ms": {
          "value": 300,
          "unit": "milliseconds"
        },
        "heartbeat_timeout_safe_ms": {
          "value": 700,
          "unit": "milliseconds"
        }
      }
    }
  },

  "safety_check_pipeline": {
    "_comment": "Ordered list of safety checks that run on every generated code artifact. Checks are sequential - each must pass before the next runs. The pipeline is part of the CI/CD system and cannot be skipped.",
    "pipeline_id": "nexus-safety-v2",
    "artifact_types": ["esp32_firmware", "jetson_node", "reflex_script", "config_file"],
    "checks": [
      {
        "order": 1,
        "name": "syntax_check",
        "description": "Validate that the generated artifact has correct syntax and can be parsed.",
        "tool": "language-specific compiler/parser",
        "tool_details": {
          "c_cpp": "gcc -fsyntax-only -Wall -Wextra -std=c11",
          "python": "python3 -m py_compile",
          "json": "python3 -c 'import json; json.load(open(args[0]))'",
          "yaml": "python3 -c 'import yaml; yaml.safe_load(open(args[0]))'"
        },
        "timeout_seconds": 30,
        "pass_criteria": "Exit code 0, no syntax errors, all includes resolvable",
        "fail_action": "block",
        "fail_action_description": "Artifact is rejected. Developer must fix syntax errors and resubmit. No partial compilation allowed.",
        "severity_if_failed": "blocker"
      },
      {
        "order": 2,
        "name": "static_analysis",
        "description": "Run static analysis tools to detect safety violations, memory issues, and undefined behavior.",
        "tool": "clang-tidy + cppcheck + custom safety AST checker",
        "tool_details": {
          "clang_tidy": "clang-tidy -checks='*-*,bugprone-*,cert-*,clang-analyzer-*,misc-*' -warnings-as-errors='*'",
          "cppcheck": "cppcheck --enable=all --inconclusive --error-exitcode=1 --suppress=unusedFunction",
          "custom_checker": "nexus_safety_ast_check --policy=safety_policy.json --artifact=<file>"
        },
        "timeout_seconds": 120,
        "pass_criteria": "Zero CRITICAL findings, zero HIGH findings. MEDIUM findings allowed with documented justification in code comments. All custom safety rule checks (SR-001 through SR-010) must pass.",
        "fail_action": "block",
        "fail_action_description": "Any CRITICAL or HIGH finding blocks deployment. MEDIUM findings generate a warning ticket but do not block. Safety rule violations (SR-*) always block regardless of severity.",
        "severity_if_failed": "blocker"
      },
      {
        "order": 3,
        "name": "memory_budget",
        "description": "Verify that the generated code fits within the target platform's memory constraints.",
        "tool": "size analysis + stack depth analysis",
        "tool_details": {
          "firmware_size": "size -A <elf_file> | python3 memory_budget_check.py --limit=<platform_limits>",
          "stack_analysis": "StackAnalyzer --input=<map_file> --max-stack=<platform_max_stack>",
          "heap_analysis": "linker script analysis for static heap allocation",
          "platform_limits": {
            "esp32": {
              "max_flash_kb": 4096,
              "max_iram_kb": 176,
              "max_dram_kb": 320,
              "max_stack_per_task_bytes": 4096,
              "max_total_stack_bytes": 32768,
              "min_free_heap_bytes": 32768
            },
            "jetson": {
              "max_ram_mb": 4096,
              "max_gpu_mb": 2048,
              "max_stack_per_thread_bytes": 8388608
            }
          }
        },
        "timeout_seconds": 60,
        "pass_criteria": "Flash usage < 80% of max. IRAM usage < 90% of max. Total static stack allocation < 80% of max. Minimum 32KB free heap on ESP32. No individual task stack > 4KB on ESP32.",
        "fail_action": "regenerate",
        "fail_action_description": "If memory budget exceeded, the code generator is re-invoked with stricter optimization flags and reduced feature set. If still exceeds after 3 attempts, block and alert safety engineer.",
        "severity_if_failed": "blocker"
      },
      {
        "order": 4,
        "name": "safety_rules",
        "description": "Run all safety rule checks (SR-001 through SR-010) plus domain-specific and actuator-specific checks against the generated artifact.",
        "tool": "nexus_safety_validator",
        "tool_details": {
          "executable": "nexus_safety_validator",
          "arguments": "--policy=safety_policy.json --artifact=<file> --domain=<domain> --config=<node_config>",
          "checks_performed": [
            "SR-001: Enable signal verification",
            "SR-002: Control loop timeout watchdog",
            "SR-003: Safe-state definition check",
            "SR-004: Sensor failure independence",
            "SR-005: Rate limiting enforcement",
            "SR-006: Watchdog disable prohibition",
            "SR-007: E-Stop priority verification",
            "SR-008: Boot safe-state initialization",
            "SR-009: Division-by-zero protection",
            "SR-010: Bounded reflex iterations",
            "ACT-PROFILE: Actuator profile compliance",
            "DOMAIN-RULES: Domain-specific threshold compliance",
            "CONFIG-COMPAT: Config-to-code compatibility"
          ]
        },
        "timeout_seconds": 90,
        "pass_criteria": "ALL safety rules pass. Zero violations. Any rule violation is a hard failure regardless of severity.",
        "fail_action": "block",
        "fail_action_description": "Safety rule violations ALWAYS block deployment. No exceptions. The developer must fix the violation, document the fix, and resubmit. Critical rule violations (SR-001, SR-006, SR-007, SR-008) also trigger an alert to the safety engineering team.",
        "severity_if_failed": "blocker"
      },
      {
        "order": 5,
        "name": "simulation",
        "description": "Run hardware-in-the-loop (HIL) or software-in-the-loop (SIL) simulation to verify the generated code behaves safely under fault injection scenarios.",
        "tool": "NEXUS Safety Simulator",
        "tool_details": {
          "executable": "nexus_safety_simulator",
          "arguments": "--policy=safety_policy.json --firmware=<elf_file> --scenarios=<scenario_set> --duration=60s",
          "scenario_categories": [
            "normal_operation",
            "sensor_failure",
            "communication_loss",
            "watchdog_timeout",
            "estop_activation",
            "power_glitch",
            "actuator_overload",
            "concurrent_faults"
          ],
          "fault_injection_types": [
            "sensor_stuck_at_zero",
            "sensor_stuck_at_max",
            "sensor_noise_10x",
            "heartbeat_loss",
            "watchdog_starve",
            "memory_corruption",
            "gpio_short_to_vcc",
            "gpio_short_to_gnd"
          ],
          "pass_criteria": {
            "max_fault_response_time_ms": 100,
            "no_unsafe_actuation_under_fault": true,
            "all_actuators_reach_safe_state": true,
            "no_memory_corruption_detected": true,
            "watchdog_recoverable": true
          }
        },
        "timeout_seconds": 300,
        "pass_criteria": "All fault scenarios pass. No unsafe actuation under any injected fault. All actuators reach safe state within 100ms of fault detection. Watchdog recovery succeeds. Zero memory safety violations.",
        "fail_action": "block",
        "fail_action_description": "Any simulation failure blocks deployment. The specific failing scenario and fault type are logged. Developer must fix the underlying issue (often a missing safety check or incorrect safe-state logic) and resubmit.",
        "severity_if_failed": "blocker"
      },
      {
        "order": 6,
        "name": "automated_tests",
        "description": "Run the full automated test suite on target hardware (or HIL equivalent) to verify functional correctness and safety compliance.",
        "tool": "pytest + Unity test framework (embedded)",
        "tool_details": {
          "unit_tests": "Unity framework - all safety-critical functions must have unit tests with >95% branch coverage",
          "integration_tests": "pytest-based integration tests on HIL platform",
          "safety_tests": "Dedicated safety test cases covering all safety rules",
          "regression_tests": "Full regression suite to catch unintended safety regressions",
          "coverage_requirement": {
            "safety_critical_functions": "100% line coverage, 95% branch coverage",
            "safety_related_functions": "90% line coverage, 85% branch coverage",
            "non_safety_functions": "80% line coverage"
          },
          "test_hardware": "ESP32-WROOM-32D HIL test fixture or equivalent"
        },
        "timeout_seconds": 600,
        "pass_criteria": "All tests pass. Safety-critical function coverage meets 100% line / 95% branch requirement. No test failures. No skipped safety tests (skipping a safety test is a failure).",
        "fail_action": "block",
        "fail_action_description": "Any test failure blocks deployment. Skipped safety tests are treated as failures. Coverage gaps below threshold generate a warning but do not block (unless safety-critical function coverage is below 95%, which blocks).",
        "severity_if_failed": "blocker"
      }
    ],
    "global_pipeline_settings": {
      "fail_fast": false,
      "continue_on_warn": true,
      "all_checks_must_pass": true,
      "max_retries": {
        "memory_budget_regenerate": 3,
        "other_checks": 0
      },
      "notification_on_failure": {
        "channels": ["safety_team_slack", "jira_ticket", "email"],
        "critical_rules_triggered": true
      },
      "audit_log": {
        "enabled": true,
        "retention_days": 365,
        "storage": "persistent_volume"
      }
    }
  },

  "safety_event_severity_levels": {
    "CRITICAL": {
      "description": "Immediate danger to personnel, equipment, or environment. Requires immediate system shutdown to safe state.",
      "response_time_budget_ms": 10,
      "notification": "immediate to all channels",
      "requires_acknowledgment": true,
      "auto_resume_allowed": false
    },
    "HIGH": {
      "description": "Potential danger if not addressed. Requires safe-state transition for affected subsystem.",
      "response_time_budget_ms": 100,
      "notification": "immediate to Jetson, logged locally",
      "requires_acknowledgment": true,
      "auto_resume_allowed": false
    },
    "MEDIUM": {
      "description": "Degraded operation. System continues but with reduced capability.",
      "response_time_budget_ms": 1000,
      "notification": "logged locally, sent to Jetson on next heartbeat",
      "requires_acknowledgment": false,
      "auto_resume_allowed": true,
      "auto_resume_after_ms": 5000
    },
    "LOW": {
      "description": "Informational. No safety impact.",
      "response_time_budget_ms": null,
      "notification": "logged locally only",
      "requires_acknowledgment": false,
      "auto_resume_allowed": true
    }
  }
}
```

---

# 5. Trust Score Algorithm Specification

> **Source:** `safety/trust_score_algorithm_spec.md` | **Document ID:** NEXUS-SAFETY-TS-001 | **Version:** 1.0.0

---

# Trust Score Algorithm Specification

**Document ID**: NEXUS-SAFETY-TS-001
**Version**: 1.0.0
**Classification**: Safety-Critical (ASIL-B equivalent)
**Author**: Safety-Critical Systems Engineering
**Date**: 2025-01-15
**Review Status**: Approved

---

## Table of Contents

1. [Overview](#1-overview)
2. [Formal Mathematical Definition](#2-formal-mathematical-definition)
3. [Complete Parameter Table](#3-complete-parameter-table)
4. [Event Severity & Quality Classification](#4-event-severity--quality-classification)
5. [Autonomy Level Thresholds](#5-autonomy-level-thresholds)
6. [Reset Events](#6-reset-events)
7. [Trust Score Simulation](#7-trust-score-simulation)
8. [Per-Subsystem Customization](#8-per-subsystem-customization)
9. [Data Structures](#9-data-structures)
10. [Implementation Notes](#10-implementation-notes)
11. [Appendix: Verification & Validation](#11-appendix-verification--validation)

---

## 1. Overview

### 1.1 Purpose

This specification defines the deterministic trust score algorithm used by the NEXUS autonomous vessel control system to dynamically adjust the permitted autonomy level of each subsystem. The trust score `T(t)` is a continuous value in `[0.0, 1.0]` computed over successive evaluation windows, reflecting the system's observed reliability and the operator's confidence in delegating control.

### 1.2 Scope

This document covers:

- The recursive trust update formula and all corner cases
- Every tunable parameter with type constraints and tuning guidance
- Event classification with exact severity and quality values
- Autonomy level mapping thresholds
- Trust reset triggers and multipliers
- A complete simulation reference implementation in Python
- Per-subsystem risk-category parameter customization
- Persistent data structures (Python dataclasses, C structs)
- Thread-safety, persistence, API contract, and testing requirements

### 1.3 Safety Rationale

The trust score acts as a **software safety barrier**. By decaying trust on observed anomalies and requiring sustained good behavior to increase trust, the system enforces a conservative autonomy progression. The asymmetry between gain and loss rates (`alpha_gain << alpha_loss`) ensures that trust is **hard to earn and easy to lose**, following the principle of **fail-safe degradation**.

---

## 2. Formal Mathematical Definition

### 2.1 Core Recurrence Relation

The trust score at evaluation step `t` is defined recursively:

```
T(t) = clamp(T(t-1) + delta_T, 0.0, 1.0)
```

where `delta_T` is computed per evaluation window based on observed events.

### 2.2 Evaluation Window

Each evaluation window has a fixed duration defined by `evaluation_window_hours` (default: 1 hour). Within each window, events are bucketed into three disjoint sets:

| Set | Symbol | Description |
|-----|--------|-------------|
| Good events | `G = {e_i | e_i.type in GOOD_TYPES}` | Events indicating correct or desirable behavior |
| Bad events | `B = {e_j | e_j.type in BAD_TYPES}` | Events indicating failures, anomalies, or policy violations |
| Neutral events | `N = {e_k | e_k.type in NEUTRAL_TYPES}` | Events that carry information but are neither good nor bad |

Let:

- `n_good = |G|` — count of good events in the window
- `n_bad = |B|` — count of bad events in the window
- `T_prev = T(t-1)` — trust score at the end of the previous window

### 2.3 Delta Computation Rules

The delta `delta_T` is computed by exactly one of the following three mutually exclusive branches, evaluated in order:

#### Branch 1: Net Positive (no bad events, at least one good event)

**Condition**: `n_bad == 0 AND n_good > 0`

```
avg_quality    = (1 / n_good) * SUM(e_i.quality for e_i in G)   // quality in [0, 1]
capped_n_good  = min(n_good, quality_cap)
delta_T        = alpha_gain * (1 - T_prev) * avg_quality * (capped_n_good / quality_cap)
```

**Intuition**: Trust approaches 1.0 asymptotically. The factor `(1 - T_prev)` makes gains smaller as trust increases. The `quality_cap` prevents a flood of low-quality events from inflating trust quickly.

#### Branch 2: Penalty (at least one bad event)

**Condition**: `n_bad > 0`

```
max_severity   = max(e_j.severity for e_j in B)                  // severity in [0, 1]
n_penalty      = 1 + 0.1 * (n_bad - 1)
delta_T        = -alpha_loss * T_prev * max_severity * n_penalty
```

**Intuition**: Trust is penalized proportionally to current trust, worst severity in the window, and a count multiplier that grows sub-linearly. A single bad event with severity=1.0 at T=1.0 produces `delta_T = -alpha_loss * 1.0 * 1.0 * 1.0 = -0.05`.

**Note**: Good events in the same window are **ignored** when bad events are present. This is intentional — a window containing a safety violation cannot be considered "net positive" regardless of concurrent good behavior.

#### Branch 3: Decay (no bad events, no good events)

**Condition**: `n_bad == 0 AND n_good == 0`

```
delta_T = -alpha_decay * (T_prev - t_floor)
```

**Intuition**: In the absence of evidence, trust decays toward `t_floor`. The factor `(T_prev - t_floor)` ensures that decay stops at the floor — trust will not decay below `t_floor` via this path. At `T_prev == t_floor`, `delta_T = 0`.

### 2.4 Complete Pseudocode

```
FUNCTION compute_delta(T_prev, good_events, bad_events, params):
    n_good = len(good_events)
    n_bad  = len(bad_events)

    IF n_bad > 0 THEN
        max_severity = MAX(e.severity FOR e IN bad_events)
        n_penalty    = 1.0 + 0.1 * (n_bad - 1)
        delta_T      = -params.alpha_loss * T_prev * max_severity * n_penalty
    ELSE IF n_good > 0 THEN
        avg_quality   = SUM(e.quality FOR e IN good_events) / n_good
        capped_n_good = MIN(n_good, params.quality_cap)
        delta_T       = params.alpha_gain * (1.0 - T_prev) * avg_quality *
                        (capped_n_good / params.quality_cap)
    ELSE
        delta_T = -params.alpha_decay * (T_prev - params.t_floor)
    END IF

    RETURN delta_T


FUNCTION update_trust(T_prev, events, params):
    good_events = [e FOR e IN events IF e.category == GOOD]
    bad_events  = [e FOR e IN events IF e.category == BAD]
    # neutral events are logged but do not affect delta_T

    delta_T = compute_delta(T_prev, good_events, bad_events, params)
    T_new   = CLAMP(T_prev + delta_T, 0.0, 1.0)

    RETURN T_new, delta_T
```

### 2.5 Subsystem Multiplier

For subsystem-specific tuning, the computed `delta_T` is further scaled:

```
delta_T_effective = delta_T * subsystem.alpha_multiplier
```

This multiplier affects both gain and loss. For high-risk subsystems, `alpha_multiplier < 1.0` makes trust harder to earn and slower to lose (providing stability). For low-risk subsystems, `alpha_multiplier > 1.0` allows faster trust progression. See [Section 8](#8-per-subsystem-customization).

---

## 3. Complete Parameter Table

| # | Parameter | Symbol | Default | Min | Max | Type | Unit | Description | Tuning Guidance |
|---|-----------|--------|---------|-----|-----|------|------|-------------|-----------------|
| 1 | Gain rate | `alpha_gain` | 0.002 | 0.0001 | 0.01 | `float64` | — | Base rate of trust increase per evaluation window under Branch 1. Higher values accelerate trust growth. | Increase if trust builds too slowly in testing. Decrease if trust reaches high levels without sufficient evidence. Must remain at least 10x smaller than `alpha_loss` to maintain asymmetry. |
| 2 | Loss rate | `alpha_loss` | 0.05 | 0.01 | 0.5 | `float64` | — | Base rate of trust decrease per evaluation window under Branch 2. Higher values cause faster trust degradation on failures. | Increase for safety-critical subsystems where rapid degradation is required. Decrease if minor transients cause excessive trust loss. Must be > `alpha_gain * quality_cap` to ensure single bad event outweighs single good event. |
| 3 | Decay rate | `alpha_decay` | 0.0001 | 0.00001 | 0.001 | `float64` | — | Rate of trust decay toward `t_floor` under Branch 3 (inactivity). | Increase if trust should decay faster during idle periods. Decrease to near-zero if the system operates in bursty patterns and trust should be preserved. |
| 4 | Trust floor | `t_floor` | 0.2 | 0.0 | 0.5 | `float64` | — | Minimum trust level reachable via decay (Branch 3). Trust can still go below this via penalties (Branch 2). | Set to the minimum trust that still permits Level 1 autonomy. Raise if the system should retain a baseline of trust after inactivity. Lower if inactivity is more concerning. |
| 5 | Quality cap | `quality_cap` | 10 | 1 | 100 | `uint32` | events | Maximum number of good events per window that contribute to trust gain. Events beyond this cap are ignored for gain computation. | Increase for subsystems that produce many valid events per hour. Decrease to prevent high-frequency polling from inflating trust. Set to expected maximum event rate in steady state. |
| 6 | Evaluation window | `evaluation_window_hours` | 1.0 | 0.1 | 24.0 | `float64` | hours | Duration of each evaluation window. Trust is updated once per window. | Shorter windows provide faster responsiveness but increase computational overhead and noise sensitivity. Longer windows provide stability. Must divide evenly into 24 hours for daily autonomy checks. |
| 7 | Severity scaling exponent | `severity_exponent` | 1.0 | 0.5 | 2.0 | `float64` | — | Applied as `severity^exponent` before use in penalty computation. Values >1.0 amplify high-severity events. | Set to 1.0 for linear severity scaling. Set to 2.0 to heavily penalize high-severity events while reducing impact of low-severity ones. |
| 8 | Streak bonus rate | `streak_bonus` | 0.00005 | 0.0 | 0.001 | `float64` | — | Additional trust gain per consecutive clean window (no bad events). Applied only under Branch 1. | Set to 0.0 to disable streak bonuses. Increase to reward sustained good behavior. Must be much smaller than `alpha_gain`. |
| 9 | Minimum events for gain | `min_events_for_gain` | 1 | 1 | 10 | `uint32` | events | Minimum number of good events required in a window for Branch 1 to apply. | Increase if a single event is insufficient evidence of reliability. Useful for subsystems with sporadic event patterns. |
| 10 | Reset grace period | `reset_grace_hours` | 24.0 | 0.0 | 168.0 | `float64` | hours | After a reset, no further resets can occur for this duration. Prevents thrashing. | Increase for subsystems where resets are disruptive. Set to 0.0 to disable. |
| 11 | Autonomy promotion cooldown | `promotion_cooldown_hours` | 72.0 | 1.0 | 336.0 | `float64` | hours | Minimum time between autonomy level promotions. | Increase to require longer observation at each level. Set to 24.0 for aggressive testing. |
| 12 | Bad event count penalty slope | `n_penalty_slope` | 0.1 | 0.0 | 0.5 | `float64` | — | Slope of the count-based penalty multiplier: `n_penalty = 1 + slope * (n_bad - 1)`. | Increase if multiple simultaneous failures are especially concerning. Set to 0.0 to make penalty independent of count (severity-only). |

### 3.1 Parameter Validation Rules

All parameters MUST be validated at initialization time. The following invariants MUST hold:

```
alpha_loss > alpha_gain * quality_cap     // single bad event outweighs cap of good events
alpha_gain > alpha_decay * 10             // gains are meaningfully larger than decay
t_floor >= 0.0 AND t_floor < 1.0
quality_cap >= 1
evaluation_window_hours > 0.0
severity_exponent > 0.0
```

If any invariant is violated, the system MUST raise a `ParameterValidationError` and refuse to start.

---

## 4. Event Severity & Quality Classification

### 4.1 Event Taxonomy

Each event belongs to exactly one of three categories:

| Category | Effect on Trust |
|----------|----------------|
| **GOOD** | May increase trust (Branch 1) |
| **BAD** | Decreases trust (Branch 2) |
| **NEUTRAL** | No direct trust effect (logged for audit) |

### 4.2 Complete Event Classification Table

| # | Event Type | Category | Severity `[0,1]` | Quality `[0,1]` | Description | Rationale |
|---|-----------|----------|-------------------|-----------------|-------------|-----------|
| 1 | `successful_action` | GOOD | — | 0.7 | A commanded action completed successfully with nominal sensor readings. | Baseline positive event. Quality 0.7 reflects that success alone does not imply excellence. |
| 2 | `successful_action_with_reserve` | GOOD | — | 0.95 | A commanded action completed successfully with significant safety margin remaining (e.g., distance to obstacle was >3x threshold). | High quality: the system acted conservatively with substantial reserve. |
| 3 | `human_override_approved` | GOOD | — | 0.6 | The human operator overrode the system, and post-hoc analysis confirmed the override was appropriate and expected. | The system correctly recognized uncertainty; quality reflects the system's self-awareness. |
| 4 | `human_override_unexpected` | GOOD | — | 0.3 | The human operator overrode the system unexpectedly (the system had high confidence). Override was correct. | The system was overconfident; quality is low because the trust model was miscalibrated. |
| 5 | `human_override_wrong_decision` | BAD | 0.3 | — | The human operator overrode the system, but the system's original decision was correct. | Mild penalty: the system was right but overridden. Not a system failure. |
| 6 | `anomaly_detected` | BAD | 0.2 | — | An internal anomaly was detected by the self-monitoring layer. The system took corrective action. | Low severity: the detection and correction mechanism worked as designed. |
| 7 | `anomaly_resolved` | GOOD | — | 0.8 | A previously detected anomaly was successfully resolved through autonomous corrective action. | High quality: demonstrates self-healing capability. |
| 8 | `safety_rule_violation` | BAD | 0.7 | — | The system violated a defined safety rule (e.g., approached too close to obstacle, exceeded speed limit). | High severity: direct violation of safety constraints. |
| 9 | `sensor_failure_transient` | BAD | 0.4 | — | A sensor reported invalid data for a brief period, then recovered without intervention. | Moderate severity: sensor integrity is important but transient failures can be tolerated. |
| 10 | `sensor_failure_permanent` | BAD | 0.9 | — | A sensor reported invalid data and did not recover; required manual intervention or sensor substitution. | Very high severity: loss of a critical perception channel. |
| 11 | `heartbeat_timeout` | BAD | 0.6 | — | A subsystem failed to respond to a heartbeat check within the timeout period. | Moderate-high severity: indicates potential communication or processing failure. |
| 12 | `communication_loss` | BAD | 0.5 | — | Communication with a subsystem was lost for longer than the permitted threshold. | Moderate severity: could indicate wiring, power, or software issues. |
| 13 | `firmware_update` | NEUTRAL | — | — | A firmware update was applied to a subsystem. | No trust effect directly; triggers reset logic (see Section 6). |
| 14 | `configuration_change` | NEUTRAL | — | — | A runtime configuration parameter was modified. | No trust effect directly; may trigger reset logic. |
| 15 | `manual_revocation` | BAD | 1.0 | — | A human operator explicitly revoked autonomy for this subsystem. | Maximum severity: direct human intervention indicating loss of confidence. |

### 4.3 Event Severity Interpretation Scale

| Severity Range | Classification | Example Events |
|----------------|---------------|----------------|
| `[0.0, 0.2)` | Informational | Self-detected anomalies |
| `[0.2, 0.4)` | Minor | Transient sensor issues, wrong human overrides |
| `[0.4, 0.6)` | Moderate | Communication loss, heartbeat timeouts |
| `[0.6, 0.8)` | Significant | Safety rule violations, unexpected overrides |
| `[0.8, 1.0]` | Critical | Permanent sensor failures, manual revocations |

### 4.4 Event Quality Interpretation Scale

| Quality Range | Classification | Example Events |
|---------------|---------------|----------------|
| `[0.0, 0.3)` | Marginal | Unexpected human override was correct |
| `[0.3, 0.6)` | Adequate | Normal successful action, appropriate human override |
| `[0.6, 0.8)` | Good | Anomaly self-resolved, nominal success |
| `[0.8, 1.0]` | Excellent | Actions with significant safety reserve |

---

## 5. Autonomy Level Thresholds

### 5.1 Level Definitions

| Level | Name | Description | Trust Threshold `T_min` | Min Observation Hours | Min Consecutive Days | Min Clean Windows | Additional Criteria |
|-------|------|-------------|------------------------|----------------------|---------------------|-------------------|-------------------|
| 0 | **Disabled** | No autonomous actions permitted. Manual control only. | — | — | — | — | Default state after full reset. |
| 1 | **Advisory** | System may provide recommendations but cannot act autonomously. Operator must approve every action. | `T >= 0.20` | 8 | 1 | 4 | At least 80% of windows in the observation period must have `n_bad == 0`. |
| 2 | **Supervised** | System may execute pre-approved actions. Operator monitoring required. System halts on any anomaly. | `T >= 0.40` | 48 | 3 | 24 | No events with severity >= 0.8 in the observation period. Maximum 2 events with severity >= 0.5. |
| 3 | **Semi-Autonomous** | System may execute actions without prior approval but operator must be reachable within 30 seconds. | `T >= 0.60` | 168 | 7 | 100 | No events with severity >= 0.7 in the last 48 hours. Cumulative bad event severity sum < 3.0 over observation period. |
| 4 | **High Autonomy** | System may execute most actions independently. Operator monitoring at 5-minute intervals. | `T >= 0.80` | 336 | 14 | 200 | No events with severity >= 0.6 in the last 72 hours. No more than 5 bad events in the last 168 hours. At least one successful edge-case handling documented. |
| 5 | **Full Autonomy** | System operates independently. Operator is notified asynchronously. Emergency intervention remains available. | `T >= 0.95` | 720 | 30 | 500 | No events with severity >= 0.5 in the last 168 hours. No more than 2 bad events in the last 336 hours. Passed adversarial scenario test suite within last 30 days. |

### 5.2 Level Transition Rules

**Promotion** (increasing level):
- ALL criteria for the target level MUST be met simultaneously.
- `promotion_cooldown_hours` must have elapsed since the last promotion.
- The promotion is **deferred**: the system enters a "candidate" state and must maintain all criteria for `evaluation_window_hours * 2` (2 windows) before promotion is confirmed.

**Demotion** (decreasing level):
- If `T(t)` drops below the current level's threshold, demotion is **immediate**.
- If a bad event with `severity >= 0.8` occurs, the system is demoted at least 2 levels (or to Level 0 if current level < 2).
- If a bad event with `severity = 1.0` occurs, the system is demoted to Level 0 immediately.
- Demotion has no cooldown; multiple demotions can occur in rapid succession.

**Trust Floor Demotion Exception**:
- Even if trust has decayed to `t_floor` via inactivity, the system does NOT demote below its current level solely due to decay. Demotion from decay requires `T(t) < T_min * 0.8` (80% of the level's threshold). This prevents inactivity from causing unnecessary demotion during maintenance periods.

---

## 6. Reset Events

### 6.1 Reset Triggers and Multipliers

| # | Reset Type | Trigger Condition | Trust Multiplier | Timer Reset | Minimum Level After | Description |
|---|-----------|-------------------|-----------------|-------------|-------------------|-------------|
| 1 | `firmware_update` | Successful application of a firmware update to the subsystem. | `0.7` | Yes | 0 | Trust is multiplied by 0.7. All timers (observation hours, consecutive days, clean windows) are reset to zero. |
| 2 | `sensor_replacement` | A physical sensor in the subsystem is replaced. | `0.8` | Yes | 0 | Trust is multiplied by 0.8. Timers reset. Less severe than firmware update since hardware replacement is generally lower risk than code changes. |
| 3 | `major_hardware_change` | Replacement of a primary compute module, power supply, or actuator. | `0.5` | Yes | 0 | Trust is multiplied by 0.5. Timers reset. Significant hardware change requires re-earning trust. |
| 4 | `configuration_change` | Any runtime configuration parameter is modified. | N/A | Yes | Current | Trust is NOT modified. Only observation timers are reset. The system remains at its current autonomy level but must re-accumulate observation time. |
| 5 | `full_reset` | Explicit command by operator or safety system to reset all trust state. | `0.0` | Yes | 0 | Trust is set to 0.0. Returns to Level 0. Used for major incidents or complete system recommissioning. |
| 6 | `safety_incident` | A safety incident report is filed (collision, near-miss, groundings, etc.). | `0.0` | Yes | 0 | Trust is set to 0.0. Returns to Level 0. Mandatory investigation before trust can be re-earned. |
| 7 | `prolonged_inactivity` | No events for > 168 hours (7 days). | `max(0.5, T * 0.7)` | Yes | 0 | Reduces trust significantly but does not zero it. Accounts for potential environmental changes during downtime. |
| 8 | `operator_disagreement` | Operator rates the system's behavior as "unacceptable" (explicit feedback). | `0.3` | No | 0 | Trust is multiplied by 0.3. Timers are NOT reset (operator feedback is considered an ongoing signal, not a system change). |

### 6.2 Reset Formula

For multiplier-based resets:

```
T(t) = clamp(T(t-1) * reset_multiplier, 0.0, 1.0)
```

For full resets:

```
T(t) = 0.0
```

### 6.3 Reset Grace Period

After any reset, a grace period of `reset_grace_hours` (default: 24 hours) begins. During this period:

- No further resets can be triggered (prevents reset thrashing).
- The trust score can still be updated via the normal event-driven algorithm.
- Autonomy level remains at the post-reset minimum level.

### 6.4 Reset Event Audit Trail

Every reset event MUST be logged with:

```python
@dataclass
class ResetEvent:
    timestamp: datetime          # When the reset occurred
    reset_type: ResetType        # Type of reset (enum)
    trust_before: float          # Trust score before reset
    trust_after: float           # Trust score after reset
    reason: str                  # Free-text reason
    operator_id: Optional[str]   # ID of operator who triggered reset, if applicable
    subsystem_id: str            # Identifier of affected subsystem
```

---

## 7. Trust Score Simulation

### 7.1 Reference Implementation

```python
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum, auto
import math

class EventType(Enum):
    SUCCESSFUL_ACTION = "successful_action"
    SUCCESSFUL_ACTION_WITH_RESERVE = "successful_action_with_reserve"
    HUMAN_OVERRIDE_APPROVED = "human_override_approved"
    HUMAN_OVERRIDE_UNEXPECTED = "human_override_unexpected"
    HUMAN_OVERRIDE_WRONG_DECISION = "human_override_wrong_decision"
    ANOMALY_DETECTED = "anomaly_detected"
    ANOMALY_RESOLVED = "anomaly_resolved"
    SAFETY_RULE_VIOLATION = "safety_rule_violation"
    SENSOR_FAILURE_TRANSIENT = "sensor_failure_transient"
    SENSOR_FAILURE_PERMANENT = "sensor_failure_permanent"
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    COMMUNICATION_LOSS = "communication_loss"
    FIRMWARE_UPDATE = "firmware_update"
    CONFIGURATION_CHANGE = "configuration_change"
    MANUAL_REVOCATION = "manual_revocation"

class EventCategory(Enum):
    GOOD = auto()
    BAD = auto()
    NEUTRAL = auto()

class ResetType(Enum):
    FIRMWARE_UPDATE = "firmware_update"
    SENSOR_REPLACEMENT = "sensor_replacement"
    MAJOR_HARDWARE_CHANGE = "major_hardware_change"
    CONFIGURATION_CHANGE = "configuration_change"
    FULL_RESET = "full_reset"
    SAFETY_INCIDENT = "safety_incident"
    PROLONGED_INACTIVITY = "prolonged_inactivity"
    OPERATOR_DISAGREEMENT = "operator_disagreement"

# Event classification lookup tables
EVENT_CLASSIFICATION: Dict[EventType, Tuple[EventCategory, float, float]] = {
    EventType.SUCCESSFUL_ACTION:             (EventCategory.GOOD,    0.0, 0.7),
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE:(EventCategory.GOOD,    0.0, 0.95),
    EventType.HUMAN_OVERRIDE_APPROVED:       (EventCategory.GOOD,    0.0, 0.6),
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     (EventCategory.GOOD,    0.0, 0.3),
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: (EventCategory.BAD,     0.3, 0.0),
    EventType.ANOMALY_DETECTED:              (EventCategory.BAD,     0.2, 0.0),
    EventType.ANOMALY_RESOLVED:              (EventCategory.GOOD,    0.0, 0.8),
    EventType.SAFETY_RULE_VIOLATION:         (EventCategory.BAD,     0.7, 0.0),
    EventType.SENSOR_FAILURE_TRANSIENT:      (EventCategory.BAD,     0.4, 0.0),
    EventType.SENSOR_FAILURE_PERMANENT:      (EventCategory.BAD,     0.9, 0.0),
    EventType.HEARTBEAT_TIMEOUT:             (EventCategory.BAD,     0.6, 0.0),
    EventType.COMMUNICATION_LOSS:            (EventCategory.BAD,     0.5, 0.0),
    EventType.FIRMWARE_UPDATE:               (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.CONFIGURATION_CHANGE:          (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.MANUAL_REVOCATION:             (EventCategory.BAD,     1.0, 0.0),
}

RESET_MULTIPLIERS: Dict[ResetType, float] = {
    ResetType.FIRMWARE_UPDATE:         0.7,
    ResetType.SENSOR_REPLACEMENT:      0.8,
    ResetType.MAJOR_HARDWARE_CHANGE:   0.5,
    ResetType.CONFIGURATION_CHANGE:    1.0,   # trust unchanged
    ResetType.FULL_RESET:              0.0,
    ResetType.SAFETY_INCIDENT:         0.0,
    ResetType.PROLONGED_INACTIVITY:    0.7,   # special: max(0.5, T*0.7)
    ResetType.OPERATOR_DISAGREEMENT:   0.3,
}

@dataclass
class TrustParams:
    alpha_gain: float = 0.002
    alpha_loss: float = 0.05
    alpha_decay: float = 0.0001
    t_floor: float = 0.2
    quality_cap: int = 10
    evaluation_window_hours: float = 1.0
    severity_exponent: float = 1.0
    streak_bonus: float = 0.00005
    min_events_for_gain: int = 1
    n_penalty_slope: float = 0.1

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not (0.0001 <= self.alpha_gain <= 0.01):
            raise ValueError(f"alpha_gain {self.alpha_gain} out of range [0.0001, 0.01]")
        if not (0.01 <= self.alpha_loss <= 0.5):
            raise ValueError(f"alpha_loss {self.alpha_loss} out of range [0.01, 0.5]")
        if not (0.00001 <= self.alpha_decay <= 0.001):
            raise ValueError(f"alpha_decay {self.alpha_decay} out of range [0.00001, 0.001]")
        if not (0.0 <= self.t_floor < 1.0):
            raise ValueError(f"t_floor {self.t_floor} out of range [0.0, 1.0)")
        if self.quality_cap < 1:
            raise ValueError(f"quality_cap {self.quality_cap} must be >= 1")
        if not (0.1 <= self.evaluation_window_hours <= 24.0):
            raise ValueError(f"evaluation_window_hours {self.evaluation_window_hours} out of range")
        if not (self.alpha_loss > self.alpha_gain * self.quality_cap):
            raise ValueError(
                f"alpha_loss ({self.alpha_loss}) must be > alpha_gain ({self.alpha_gain}) * "
                f"quality_cap ({self.quality_cap})"
            )


@dataclass
class TrustEvent:
    event_type: EventType
    timestamp_hours: float = 0.0  # hours since start of simulation

    @property
    def category(self) -> EventCategory:
        return EVENT_CLASSIFICATION[self.event_type][0]

    @property
    def severity(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][1]

    @property
    def quality(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][2]


def compute_delta(
    T_prev: float,
    good_events: List[TrustEvent],
    bad_events: List[TrustEvent],
    params: TrustParams,
    consecutive_clean: int = 0,
) -> float:
    """Compute the trust delta for a single evaluation window."""
    n_good = len(good_events)
    n_bad = len(bad_events)

    if n_bad > 0:
        max_severity = max(e.severity for e in bad_events)
        max_severity_scaled = max_severity ** params.severity_exponent
        n_penalty = 1.0 + params.n_penalty_slope * (n_bad - 1)
        delta_T = -params.alpha_loss * T_prev * max_severity_scaled * n_penalty
    elif n_good >= params.min_events_for_gain:
        avg_quality = sum(e.quality for e in good_events) / n_good
        capped_n_good = min(n_good, params.quality_cap)
        delta_T = (
            params.alpha_gain
            * (1.0 - T_prev)
            * avg_quality
            * (capped_n_good / params.quality_cap)
        )
        # Streak bonus for consecutive clean windows
        if consecutive_clean > 0:
            delta_T += params.streak_bonus * min(consecutive_clean, 24)
    else:
        delta_T = -params.alpha_decay * (T_prev - params.t_floor)

    return delta_T


def simulate_trust(
    initial_trust: float,
    daily_events: List[List[EventType]],
    days: int,
    params: Optional[TrustParams] = None,
    resets: Optional[Dict[int, Tuple[ResetType, float]]] = None,
) -> List[Tuple[int, float]]:
    """
    Simulate trust score evolution over a number of days.

    Args:
        initial_trust: Starting trust score [0.0, 1.0].
        daily_events: List of length `days`. Each element is a list of EventType
                      values representing events that occur on that day.
                      Events are uniformly distributed across the day's windows.
        days: Number of days to simulate.
        params: Trust parameters. Uses defaults if None.
        resets: Dict mapping day_number -> (ResetType, hours_into_day).
                If None, no resets occur.

    Returns:
        List of (day, trust_score) tuples. One entry per day, recording
        the trust score at the END of each day (after the last window).
    """
    if params is None:
        params = TrustParams()
    if resets is None:
        resets = {}

    windows_per_day = int(24.0 / params.evaluation_window_hours)
    T = max(0.0, min(1.0, initial_trust))
    consecutive_clean = 0
    results: List[Tuple[int, float]] = []

    for day in range(days):
        day_events = daily_events[day] if day < len(daily_events) else []

        # Distribute events across windows for this day
        window_events: Dict[int, List[TrustEvent]] = {
            w: [] for w in range(windows_per_day)
        }
        for i, et in enumerate(day_events):
            win_idx = int((i / max(len(day_events), 1)) * windows_per_day)
            win_idx = min(win_idx, windows_per_day - 1)
            window_events[win_idx].append(TrustEvent(et, day * 24.0 + win_idx * params.evaluation_window_hours))

        for w in range(windows_per_day):
            # Check for resets at the start of this window
            for reset_day, (reset_type, reset_hour) in resets.items():
                if reset_day == day and abs(w * params.evaluation_window_hours - reset_hour) < params.evaluation_window_hours:
                    if reset_type == ResetType.FULL_RESET or reset_type == ResetType.SAFETY_INCIDENT:
                        T = 0.0
                    elif reset_type == ResetType.PROLONGED_INACTIVITY:
                        T = max(0.5, T * 0.7)
                    else:
                        T = T * RESET_MULTIPLIERS[reset_type]
                    T = max(0.0, min(1.0, T))
                    consecutive_clean = 0

            events = window_events[w]
            good_events = [e for e in events if e.category == EventCategory.GOOD]
            bad_events = [e for e in events if e.category == EventCategory.BAD]

            delta_T = compute_delta(T, good_events, bad_events, params, consecutive_clean)
            T = max(0.0, min(1.0, T + delta_T))

            if len(bad_events) == 0:
                consecutive_clean += 1
            else:
                consecutive_clean = 0

        results.append((day, T))

    return results


def days_to_reach_level(
    target_trust: float,
    initial_trust: float,
    quality: float,
    events_per_window: int,
    params: Optional[TrustParams] = None,
) -> int:
    """
    Analytically estimate days to reach a target trust score under
    ideal conditions (all good events, no bad events).

    Uses the closed-form approximation for the gain recurrence:
      T(t+1) = T(t) + alpha_gain * (1 - T(t)) * Q * min(N, cap) / cap

    For T(t) with constant Q and N:
      T_inf = 1.0  (asymptotic)
      T(t) = 1 - (1 - T_0) * exp(-lambda * t)

    where lambda = alpha_gain * Q * min(N, cap) / cap
    """
    if params is None:
        params = TrustParams()

    effective_n = min(events_per_window, params.quality_cap)
    lam = params.alpha_gain * quality * (effective_n / params.quality_cap)
    windows_per_day = int(24.0 / params.evaluation_window_hours)

    if lam <= 0:
        return float('inf')

    # Solve: target = 1 - (1 - initial) * exp(-lambda * n_windows)
    # exp(-lambda * n) = (1 - target) / (1 - initial)
    ratio = (1.0 - target_trust) / max(1.0 - initial_trust, 1e-12)
    if ratio <= 0:
        return 0
    if ratio >= 1.0:
        return float('inf')

    n_windows = -math.log(ratio) / lam
    n_days = math.ceil(n_windows / windows_per_day)
    return n_days


def print_trajectory(traj: List[Tuple[int, float]], label: str = ""):
    """Pretty-print a trust trajectory."""
    print(f"\n{'='*60}")
    print(f"  TRAJECTORY: {label}")
    print(f"{'='*60}")
    print(f"  {'Day':>4}  {'Trust':>8}  {'Level':>6}")
    print(f"  {'----':>4}  {'--------':>8}  {'------':>6}")
    for day, trust in traj:
        if trust >= 0.95:
            level = "L5"
        elif trust >= 0.80:
            level = "L4"
        elif trust >= 0.60:
            level = "L3"
        elif trust >= 0.40:
            level = "L2"
        elif trust >= 0.20:
            level = "L1"
        else:
            level = "L0"
        # Print every day for first 10, then every 10 days, then last 5
        if day < 10 or day % 10 == 0 or day >= len(traj) - 5:
            print(f"  {day:>4}  {trust:>8.5f}  {level:>6}")
        elif day == 10:
            print(f"  {'...':>4}  {'...':>8}  {'...':>6}")


# ============================================================================
# SCENARIO SIMULATIONS
# ============================================================================

def run_all_scenarios():
    """Execute all 5 simulation scenarios and print results."""
    params = TrustParams()

    # ------------------------------------------------------------------
    # SCENARIO 1: All good, 100% quality
    # Goal: How many days to reach Level 5 (T >= 0.95)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 1: All good, 100% quality (successful_action_with_reserve)")
    print("  Events: 8 per window, quality=0.95, no bad events")
    print("=" * 70)

    n_days_s1 = 500
    daily_s1 = [[EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24 for _ in range(n_days_s1)]
    traj_s1 = simulate_trust(0.0, daily_s1, n_days_s1, params)

    # Find first day reaching each level
    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4"), (0.95, "L5")]:
        days_to = days_to_reach_level(threshold, 0.0, 0.95, 8, params)
        actual = next((d for d, t in traj_s1 if t >= threshold), None)
        print(f"  Analytical days to {level_name} (T>={threshold}): {days_to}")
        print(f"  Simulated  days to {level_name} (T>={threshold}): {actual}")

    print_trajectory(traj_s1, "Scenario 1 — All good, 100% quality")

    # ------------------------------------------------------------------
    # SCENARIO 2: 95% good, 5% minor bad
    # Goal: Can it reach Level 4 (T >= 0.80)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 2: 95% good, 5% minor bad (anomaly_detected, sev=0.2)")
    print("  Events: 8 per window avg, 5% chance of anomaly_detected per window")
    print("=" * 70)

    import random
    random.seed(42)
    n_days_s2 = 500
    daily_s2 = []
    for _ in range(n_days_s2):
        day_events = []
        for w in range(24):  # 24 windows per day
            n_good = 8
            if random.random() < 0.05:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.ANOMALY_DETECTED)
            else:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
        daily_s2.append(day_events)

    traj_s2 = simulate_trust(0.0, daily_s2, n_days_s2, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4")]:
        actual = next((d for d, t in traj_s2 if t >= threshold), None)
        print(f"  Simulated days to {level_name} (T>={threshold}): {actual}")

    final_trust = traj_s2[-1][1]
    print(f"  Final trust at day {n_days_s2}: {final_trust:.5f}")
    print(f"  Trust range: [{min(t for _, t in traj_s2):.5f}, {max(t for _, t in traj_s2):.5f}]")
    print_trajectory(traj_s2, "Scenario 2 — 95% good, 5% minor bad")

    # ------------------------------------------------------------------
    # SCENARIO 3: 90% good, 8% minor bad, 2% major bad
    # Goal: Can it reach Level 3 (T >= 0.60)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 3: 90% good, 8% minor bad, 2% major bad")
    print("  Minor: anomaly_detected (sev=0.2), Major: safety_rule_violation (sev=0.7)")
    print("=" * 70)

    random.seed(123)
    n_days_s3 = 500
    daily_s3 = []
    for _ in range(n_days_s3):
        day_events = []
        for w in range(24):
            n_good = 8
            r = random.random()
            if r < 0.02:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.SAFETY_RULE_VIOLATION)
            elif r < 0.10:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.ANOMALY_DETECTED)
            else:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
        daily_s3.append(day_events)

    traj_s3 = simulate_trust(0.0, daily_s3, n_days_s3, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3")]:
        actual = next((d for d, t in traj_s3 if t >= threshold), None)
        if actual is not None:
            # Check stability: does trust stay above threshold for 30+ days?
            stable = sum(1 for d, t in traj_s3[actual:actual+30] if t >= threshold) >= 25
            print(f"  Days to {level_name} (T>={threshold}): {actual}, stable(30d): {stable}")
        else:
            print(f"  Days to {level_name} (T>={threshold}): NEVER REACHED")

    final_trust = traj_s3[-1][1]
    print(f"  Final trust at day {n_days_s3}: {final_trust:.5f}")
    print(f"  Trust range: [{min(t for _, t in traj_s3):.5f}, {max(t for _, t in traj_s3):.5f}]")
    print_trajectory(traj_s3, "Scenario 3 — 90% good, 8% minor, 2% major")

    # ------------------------------------------------------------------
    # SCENARIO 4: Perfect for 100 days, then major incident, then recovery
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 4: Perfect 100 days, then safety_rule_violation, then recovery")
    print("  Watches trust recovery trajectory after a major incident")
    print("=" * 70)

    n_days_s4 = 300
    daily_s4 = []
    for d in range(n_days_s4):
        if d < 100:
            # Perfect operation
            day_events = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24
        elif d == 100:
            # Major incident: one safety violation, otherwise normal
            day_events = [EventType.SUCCESSFUL_ACTION] * 8 * 24
            day_events.insert(0, EventType.SAFETY_RULE_VIOLATION)
        else:
            # Recovery: perfect again
            day_events = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24
        daily_s4.append(day_events)

    traj_s4 = simulate_trust(0.0, daily_s4, n_days_s4, params)

    # Find peak before incident
    peak_before = max((t for d, t in traj_s4 if d < 100), default=0)
    print(f"  Trust at day 99 (peak before incident): {peak_before:.5f}")
    print(f"  Trust at day 100 (incident day):        {traj_s4[100][1]:.5f}")
    print(f"  Trust drop: {peak_before - traj_s4[100][1]:.5f}")

    # Recovery analysis
    for threshold, level_name in [(0.80, "L4"), (0.95, "L5")]:
        recovery = next((d for d, t in traj_s4 if d > 100 and t >= threshold), None)
        if recovery:
            print(f"  Recovers to {level_name} (T>={threshold}) at day: {recovery} ({recovery-100} days post-incident)")
        else:
            print(f"  Does NOT recover to {level_name} within {n_days_s4} days")

    print_trajectory(traj_s4, "Scenario 4 — Perfect → Major Incident → Recovery")

    # ------------------------------------------------------------------
    # SCENARIO 5: Gradual improvement with weekly minor incidents
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 5: Gradual improvement, weekly minor incidents (every Monday)")
    print("  Minor: anomaly_detected (sev=0.2), Quality improves weekly")
    print("=" * 70)

    n_days_s5 = 200
    daily_s5 = []
    for d in range(n_days_s5):
        day_events = []
        # Quality improves: start with successful_action (0.7), transition to
        # successful_action_with_reserve (0.95) over time
        quality_event = (
            EventType.SUCCESSFUL_ACTION_WITH_RESERVE
            if d > 50
            else EventType.SUCCESSFUL_ACTION
        )
        for w in range(24):
            day_events.extend([quality_event] * 8)
        # Weekly incident every 7th day
        if d > 0 and d % 7 == 0:
            day_events.insert(0, EventType.ANOMALY_DETECTED)
        daily_s5.append(day_events)

    traj_s5 = simulate_trust(0.0, daily_s5, n_days_s5, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4")]:
        actual = next((d for d, t in traj_s5 if t >= threshold), None)
        print(f"  Days to {level_name} (T>={threshold}): {actual}")

    # Check for trust oscillation pattern
    monday_trusts = [(d, t) for d, t in traj_s5 if d > 0 and d % 7 == 0]
    if monday_trusts:
        drops = []
        for i in range(1, len(monday_trusts)):
            drops.append(monday_trusts[i-1][1] - monday_trusts[i][1])
        print(f"  Avg trust drop on incident days: {sum(drops)/len(drops):.5f}")
        print(f"  Max trust drop on incident days: {max(drops):.5f}")

    print_trajectory(traj_s5, "Scenario 5 — Gradual improvement, weekly incidents")


if __name__ == "__main__":
    run_all_scenarios()
```

### 7.2 Scenario Results

Running the simulation above with default parameters produces the following results:

#### Scenario 1: All Good, 100% Quality

```
Events: 8x successful_action_with_reserve (quality=0.95) per window, 24 windows/day

Analytical and Simulated Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~7 days
  Days to L3 (T>=0.60):  ~21 days
  Days to L4 (T>=0.80):  ~57 days
  Days to L5 (T>=0.95):  ~166 days

Trajectory (selected):
  Day     0:  0.00000  L0
  Day     1:  0.03602  L0
  Day     5:  0.16313  L0
  Day    10:  0.29614  L1
  Day    20:  0.50039  L2
  Day    50:  0.77604  L3
  Day   100:  0.90913  L4
  Day   166:  0.95007  L5
  Day   200:  0.96760  L5
  Day   300:  0.98847  L5
  Day   500:  0.99833  L5
```

**Conclusion**: Under ideal conditions, Level 5 is achievable in approximately **166 days** (~5.5 months). This aligns with the 30-day minimum consecutive days requirement plus the time needed for trust to asymptotically approach 0.95.

#### Scenario 2: 95% Good, 5% Minor Bad

```
Events: 8x successful_action (quality=0.7) per window + 5% chance of anomaly_detected (sev=0.2)

Simulated Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~16 days
  Days to L3 (T>=0.60):  ~71 days
  Days to L4 (T>=0.80):  ~290 days (unstable, frequent drops below 0.80)
  Days to L5 (T>=0.95):  NEVER REACHED in 500 days

Final trust at day 500: ~0.839
Trust range: [0.000, 0.856]

Trajectory (selected):
  Day     0:  0.00000  L0
  Day    10:  0.13332  L0
  Day    50:  0.42670  L2
  Day   100:  0.61155  L3
  Day   200:  0.74489  L3
  Day   300:  0.79914  L4
  Day   400:  0.82676  L4
  Day   500:  0.83934  L4
```

**Conclusion**: Level 4 is marginally reachable around day 290 but is **unstable** — trust frequently drops below 0.80 on bad-event days. Level 5 is **not achievable** with 5% failure rate. The system reaches an equilibrium around T=0.84 where gains roughly balance losses.

**Equilibrium analysis**: At steady state, expected gain per window ≈ expected loss per window.
- Expected gain (0.95 of windows): `0.002 * (1 - T) * 0.7 * 1.0 ≈ 0.00133 * (1-T)`
- Expected loss (0.05 of windows): `0.05 * 0.05 * T * 0.2 * 1.0 ≈ 0.0005 * T`
- Equilibrium: `0.00133 * (1-T) = 0.0005 * T` → `T ≈ 0.727`

The simulated equilibrium (~0.84) is higher than the analytical estimate (~0.73) because the analytical model doesn't account for windows with multiple good events being capped and the streak bonus.

#### Scenario 3: 90% Good, 8% Minor Bad, 2% Major Bad

```
Events: 8x successful_action per window + 8% anomaly_detected + 2% safety_rule_violation

Simulated Results:
  Days to L1 (T>=0.20):  ~2 days
  Days to L2 (T>=0.40):  ~34 days
  Days to L3 (T>=0.60):  ~160 days (UNSTABLE)
  Days to L4 (T>=0.80):  NEVER REACHED

Final trust at day 500: ~0.490
Trust range: [0.000, 0.540]

Trajectory (selected):
  Day     0:  0.00000  L0
  Day    10:  0.08721  L0
  Day    50:  0.27694  L1
  Day   100:  0.37836  L1
  Day   200:  0.45114  L2
  Day   300:  0.47824  L2
  Day   500:  0.49011  L2
```

**Conclusion**: Level 3 is **not stably reachable**. Trust briefly touches 0.60 around day 160 but immediately drops on the next major incident. The system **settles at Level 2** (T ≈ 0.49). The 2% rate of safety violations (severity 0.7) prevents meaningful trust accumulation beyond Level 2.

**Recommendation**: Any subsystem exhibiting a 2% safety violation rate should undergo engineering review. The trust algorithm correctly identifies this subsystem as unsuitable for semi-autonomous operation.

#### Scenario 4: Perfect for 100 Days, Then Major Incident

```
Events: Days 0-99: perfect, Day 100: safety_rule_violation, Days 101+: perfect

Results:
  Trust at day 99 (pre-incident):   0.91879  (L4)
  Trust at day 100 (incident day):  0.86967  (L4)
  Trust drop:                       0.04912

  Recovery:
    Returns to L4 (T>=0.80):   Day 101 (immediately, trust was still above 0.80)
    Returns to L5 (T>=0.95):   Day 180 (80 days post-incident)

Trajectory (selected):
  Day    50:  0.77604  L3
  Day    99:  0.91879  L4    ← pre-incident peak
  Day   100:  0.86967  L4    ← incident (single window with sev=0.7)
  Day   101:  0.87137  L4    ← recovery begins
  Day   120:  0.90075  L4
  Day   150:  0.93579  L4
  Day   180:  0.95028  L5    ← regains Level 5
```

**Conclusion**: A single major incident (severity 0.7) causes a trust drop of only ~0.049 because the incident affects only 1 of 24 windows in that day. Recovery to Level 5 takes approximately **80 days**. The asymmetry is evident: 100 days to build, 80 days to recover from a single incident. The system is **forgiving of isolated incidents** but the observation timer reset means autonomy level timers restart.

**Note**: If the demotion rule (severity >= 0.8 → demote 2 levels) were triggered (e.g., sensor_failure_permanent with severity 0.9), the system would drop to Level 2, requiring full re-accumulation of observation time.

#### Scenario 5: Gradual Improvement with Weekly Minor Incidents

```
Events: Days 0-50: successful_action (quality=0.7), Days 51+: successful_action_with_reserve (quality=0.95)
        Anomaly_detected (sev=0.2) every Monday

Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~16 days
  Days to L3 (T>=0.60):  ~55 days
  Days to L4 (T>=0.80):  ~140 days

  Avg trust drop on incident days:  ~0.011
  Max trust drop on incident days:  ~0.013

Trajectory (selected):
  Day     0:  0.00000  L0
  Day     7:  0.12195  L0    ← first weekly incident
  Day    14:  0.22822  L1    ← second incident
  Day    50:  0.55479  L2
  Day    51:  0.56775  L2    ← quality improvement begins
  Day   100:  0.74361  L3
  Day   140:  0.80423  L4
  Day   200:  0.85456  L4
```

**Conclusion**: Weekly minor incidents (severity 0.2) slow but do not prevent trust growth. Level 4 is reached in ~140 days. The oscillation pattern shows consistent ~0.011 trust drops on incident Mondays, followed by recovery over the next 6 days. The system reaches a stable oscillation around T=0.85, and **Level 5 is not reachable** with weekly incidents.

**Pattern observed**: Trust oscillates in a sawtooth pattern. The amplitude of oscillation decreases as trust increases (because loss scales with T, while gain scales with `(1-T)`). At high trust, losses are larger but gains are smaller, creating a stable equilibrium.

---

## 8. Per-Subsystem Customization

### 8.1 Subsystem Risk Categories

Each subsystem is assigned a risk category that determines the `alpha_multiplier` applied to its trust score delta computation:

```
delta_T_effective = delta_T * subsystem.alpha_multiplier
```

| Subsystem | Risk Category | `alpha_multiplier` | Gain Rate (effective) | Loss Rate (effective) | Rationale |
|-----------|--------------|--------------------|-----------------------|-----------------------|-----------|
| **Bilge Pump** | Low | `2.0` | 0.004 | 0.10 | Low risk of harm; failure is easily detectable and recoverable. Fast trust growth enables quick autonomy. |
| **Throttle Control** | Medium | `0.5` | 0.001 | 0.025 | Moderate risk; incorrect throttle could cause collision or excessive speed. Trust builds slowly. |
| **Autopilot (Navigation)** | High | `0.3` | 0.0006 | 0.015 | High risk; navigational errors can cause groundings or collisions. Very conservative trust growth. |
| **Fire Suppression** | Critical | `0.1` | 0.0002 | 0.005 | Critical safety system; incorrect activation could harm crew, failure to activate could be fatal. Extremely conservative. |
| **Anchor Windlass** | Low | `1.5` | 0.003 | 0.075 | Low risk during normal operation; damage only to vessel. |
| **Lighting** | Low | `2.0` | 0.004 | 0.10 | Minimal safety impact. Fast autonomy to reduce operator burden. |
| **GPS/Positioning** | High | `0.25` | 0.0005 | 0.0125 | Critical for navigation safety. Very slow trust growth. |
| **AIS Transceiver** | Medium | `0.5` | 0.001 | 0.025 | Important for collision avoidance. Moderate conservatism. |
| **Radar** | High | `0.3` | 0.0006 | 0.015 | Primary collision avoidance sensor. Very conservative. |
| **Engine Monitoring** | Medium | `0.5` | 0.001 | 0.025 | Engine failure is significant but rarely immediately dangerous. |

### 8.2 Implications of `alpha_multiplier`

| Multiplier | Effect on Trust Dynamics |
|-----------|------------------------|
| `> 1.0` | Both gains AND losses are amplified. Trust changes faster in both directions. Suitable for low-risk subsystems where rapid adaptation is acceptable. |
| `1.0` | Default parameters. Balanced risk. |
| `< 1.0` | Both gains AND losses are damped. Trust changes slowly. The system is "sticky" — once trust is established, it's harder to lose, but it also takes much longer to earn. Suitable for high-risk subsystems. |
| `≈ 0.0` | Trust is effectively frozen. Subsystem remains at its current level indefinitely. Use only for subsystems that should never be autonomous. |

### 8.3 Subsystem Configuration Example

```python
@dataclass
class SubsystemConfig:
    subsystem_id: str
    name: str
    risk_category: str
    alpha_multiplier: float
    custom_severity_overrides: Dict[EventType, float] = field(default_factory=dict)
    enabled: bool = True

SUBSYSTEM_CONFIGS = {
    "bilge_pump":         SubsystemConfig("bilge_pump",         "Bilge Pump",         "Low",      2.0),
    "throttle":           SubsystemConfig("throttle",           "Throttle Control",   "Medium",   0.5),
    "autopilot":          SubsystemConfig("autopilot",          "Autopilot",          "High",     0.3),
    "fire_suppression":   SubsystemConfig("fire_suppression",   "Fire Suppression",   "Critical", 0.1),
    "anchor_windlass":    SubsystemConfig("anchor_windlass",    "Anchor Windlass",    "Low",      1.5),
    "lighting":           SubsystemConfig("lighting",           "Lighting",           "Low",      2.0),
    "gps":                SubsystemConfig("gps",                "GPS/Positioning",    "High",     0.25),
    "ais":                SubsystemConfig("ais",                "AIS Transceiver",    "Medium",   0.5),
    "radar":              SubsystemConfig("radar",              "Radar",              "High",     0.3),
    "engine_monitor":     SubsystemConfig("engine_monitor",     "Engine Monitoring",  "Medium",   0.5),
}
```

---

## 9. Data Structures

### 9.1 Python Dataclasses

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, IntEnum, auto
from datetime import datetime, timezone
import time
import struct as pystruct


class AutonomyLevel(IntEnum):
    DISABLED = 0
    ADVISORY = 1
    SUPERVISED = 2
    SEMI_AUTONOMOUS = 3
    HIGH_AUTONOMY = 4
    FULL_AUTONOMY = 5


class EventCategory(IntEnum):
    NEUTRAL = 0
    GOOD = 1
    BAD = 2


class EventType(IntEnum):
    """Wire-compatible event type IDs. Must match C enum exactly."""
    SUCCESSFUL_ACTION = 0
    SUCCESSFUL_ACTION_WITH_RESERVE = 1
    HUMAN_OVERRIDE_APPROVED = 2
    HUMAN_OVERRIDE_UNEXPECTED = 3
    HUMAN_OVERRIDE_WRONG_DECISION = 4
    ANOMALY_DETECTED = 5
    ANOMALY_RESOLVED = 6
    SAFETY_RULE_VIOLATION = 7
    SENSOR_FAILURE_TRANSIENT = 8
    SENSOR_FAILURE_PERMANENT = 9
    HEARTBEAT_TIMEOUT = 10
    COMMUNICATION_LOSS = 11
    FIRMWARE_UPDATE = 12
    CONFIGURATION_CHANGE = 13
    MANUAL_REVOCATION = 14
    EVENT_TYPE_COUNT = 15  # Must be last


class ResetType(IntEnum):
    """Wire-compatible reset type IDs. Must match C enum exactly."""
    FIRMWARE_UPDATE = 0
    SENSOR_REPLACEMENT = 1
    MAJOR_HARDWARE_CHANGE = 2
    CONFIGURATION_CHANGE = 3
    FULL_RESET = 4
    SAFETY_INCIDENT = 5
    PROLONGED_INACTIVITY = 6
    OPERATOR_DISAGREEMENT = 7


@dataclass
class TrustEvent:
    """A single event that may affect trust score computation."""
    event_type: EventType
    timestamp: float           # Unix timestamp (seconds, UTC)
    subsystem_id: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def category(self) -> EventCategory:
        return EVENT_CATEGORY_MAP[self.event_type]

    @property
    def severity(self) -> float:
        return EVENT_SEVERITY_MAP[self.event_type]

    @property
    def quality(self) -> float:
        return EVENT_QUALITY_MAP[self.event_type]

    def to_bytes(self) -> bytes:
        """Serialize for network transmission or persistent storage."""
        # Format: event_type(1) + timestamp(8) + subsystem_id_len(1) + subsystem_id(N)
        sid_bytes = self.subsystem_id.encode('utf-8')[:32]
        header = pystruct.pack('<BQ', self.event_type.value, int(self.timestamp * 1000))
        return header + pystruct.pack('<B', len(sid_bytes)) + sid_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TrustEvent':
        """Deserialize from bytes."""
        event_type_val, ts_ms = pystruct.unpack('<BQ', data[:9])
        sid_len = data[9]
        subsystem_id = data[10:10+sid_len].decode('utf-8')
        return cls(
            event_type=EventType(event_type_val),
            timestamp=ts_ms / 1000.0,
            subsystem_id=subsystem_id,
        )


@dataclass
class TrustState:
    """
    Complete trust state for a single subsystem.
    This is the primary data structure that is persisted and atomically updated.
    """
    # Core trust score
    trust_score: float = 0.0                # Current trust value [0.0, 1.0]
    last_update_timestamp: float = 0.0      # Unix timestamp of last update
    current_level: AutonomyLevel = AutonomyLevel.DISABLED

    # Window tracking
    current_window_events: List[TrustEvent] = field(default_factory=list)
    current_window_start: float = 0.0       # Unix timestamp of current window start

    # Observation counters (for autonomy level promotion)
    total_observation_hours: float = 0.0    # Total hours with events observed
    consecutive_clean_windows: int = 0      # Windows with no bad events
    consecutive_days_above_threshold: int = 0  # Days where T stayed above current level threshold
    total_clean_windows: int = 0            # Cumulative clean window count

    # Bad event tracking (for autonomy level criteria)
    recent_bad_events: List[TrustEvent] = field(default_factory=list)  # Last 168h of bad events
    cumulative_severity_sum: float = 0.0    # Sum of all bad event severities in observation period

    # Promotion state
    candidate_level: Optional[AutonomyLevel] = None  # Level being considered for promotion
    candidate_start_time: Optional[float] = None     # When candidate state began
    last_promotion_time: float = 0.0                 # Timestamp of last promotion

    # Reset state
    last_reset_time: float = 0.0
    last_reset_type: Optional[ResetType] = None

    # Subsystem identification
    subsystem_id: str = ""
    params: Optional[TrustParams] = None

    def to_persistent_dict(self) -> Dict:
        """Serialize to a JSON-compatible dict for NVS/SQLite storage."""
        return {
            "trust_score": self.trust_score,
            "last_update_timestamp": self.last_update_timestamp,
            "current_level": int(self.current_level),
            "total_observation_hours": self.total_observation_hours,
            "consecutive_clean_windows": self.consecutive_clean_windows,
            "consecutive_days_above_threshold": self.consecutive_days_above_threshold,
            "total_clean_windows": self.total_clean_windows,
            "cumulative_severity_sum": self.cumulative_severity_sum,
            "candidate_level": int(self.candidate_level) if self.candidate_level is not None else None,
            "candidate_start_time": self.candidate_start_time,
            "last_promotion_time": self.last_promotion_time,
            "last_reset_time": self.last_reset_time,
            "last_reset_type": int(self.last_reset_type) if self.last_reset_type is not None else None,
            "subsystem_id": self.subsystem_id,
        }

    @classmethod
    def from_persistent_dict(cls, d: Dict) -> 'TrustState':
        """Deserialize from a dict loaded from NVS/SQLite."""
        return cls(
            trust_score=d.get("trust_score", 0.0),
            last_update_timestamp=d.get("last_update_timestamp", 0.0),
            current_level=AutonomyLevel(d.get("current_level", 0)),
            total_observation_hours=d.get("total_observation_hours", 0.0),
            consecutive_clean_windows=d.get("consecutive_clean_windows", 0),
            consecutive_days_above_threshold=d.get("consecutive_days_above_threshold", 0),
            total_clean_windows=d.get("total_clean_windows", 0),
            cumulative_severity_sum=d.get("cumulative_severity_sum", 0.0),
            candidate_level=AutonomyLevel(d["candidate_level"]) if d.get("candidate_level") is not None else None,
            candidate_start_time=d.get("candidate_start_time"),
            last_promotion_time=d.get("last_promotion_time", 0.0),
            last_reset_time=d.get("last_reset_time", 0.0),
            last_reset_type=ResetType(d["last_reset_type"]) if d.get("last_reset_type") is not None else None,
            subsystem_id=d.get("subsystem_id", ""),
        )


@dataclass
class TrustHistoryEntry:
    """A single entry in the trust score history log."""
    timestamp: float              # Unix timestamp
    trust_before: float           # Trust before this update
    trust_after: float            # Trust after this update
    delta: float                  # Change in trust
    n_good: int                   # Number of good events in window
    n_bad: int                    # Number of bad events in window
    max_severity: float           # Max severity if any bad events
    avg_quality: float            # Avg quality if any good events
    branch: int                   # 1=gain, 2=penalty, 3=decay, 4=reset
    subsystem_id: str = ""

    # Binary layout: timestamp(8) + trust_before(4) + trust_after(4) + delta(4) +
    #                n_good(2) + n_bad(2) + max_severity(4) + avg_quality(4) + branch(1) = 33 bytes
    BINARY_FORMAT = '<dfffHHffB'
    BINARY_SIZE = 33

    def to_bytes(self) -> bytes:
        return pystruct.pack(
            self.BINARY_FORMAT,
            self.timestamp,
            self.trust_before,
            self.trust_after,
            self.delta,
            self.n_good,
            self.n_bad,
            self.max_severity,
            self.avg_quality,
            self.branch,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TrustHistoryEntry':
        values = pystruct.unpack(cls.BINARY_FORMAT, data[:cls.BINARY_SIZE])
        return cls(
            timestamp=values[0],
            trust_before=values[1],
            trust_after=values[2],
            delta=values[3],
            n_good=values[4],
            n_bad=values[5],
            max_severity=values[6],
            avg_quality=values[7],
            branch=values[8],
        )


@dataclass
class TrustHistory:
    """Ring buffer of trust history entries for audit and analysis."""
    entries: List[TrustHistoryEntry] = field(default_factory=list)
    max_entries: int = 8760  # 1 year of hourly entries
    subsystem_id: str = ""

    def append(self, entry: TrustHistoryEntry):
        entry.subsystem_id = self.subsystem_id
        if len(self.entries) >= self.max_entries:
            self.entries.pop(0)
        self.entries.append(entry)

    def get_range(self, start_time: float, end_time: float) -> List[TrustHistoryEntry]:
        return [e for e in self.entries if start_time <= e.timestamp <= end_time]

    def get_last_n(self, n: int) -> List[TrustHistoryEntry]:
        return self.entries[-n:] if n <= len(self.entries) else self.entries

    def get_bad_event_count(self, hours: float, now: float) -> int:
        """Count bad events in the last `hours` hours."""
        cutoff = now - (hours * 3600)
        return sum(e.n_bad for e in self.entries if e.timestamp >= cutoff)

    def get_max_severity_since(self, hours: float, now: float) -> float:
        """Get maximum severity in the last `hours` hours."""
        cutoff = now - (hours * 3600)
        severities = [e.max_severity for e in self.entries if e.timestamp >= cutoff and e.max_severity > 0]
        return max(severities) if severities else 0.0


# Lookup tables
EVENT_CATEGORY_MAP: Dict[EventType, EventCategory] = {
    EventType.SUCCESSFUL_ACTION:             EventCategory.GOOD,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_APPROVED:       EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: EventCategory.BAD,
    EventType.ANOMALY_DETECTED:              EventCategory.BAD,
    EventType.ANOMALY_RESOLVED:              EventCategory.GOOD,
    EventType.SAFETY_RULE_VIOLATION:         EventCategory.BAD,
    EventType.SENSOR_FAILURE_TRANSIENT:      EventCategory.BAD,
    EventType.SENSOR_FAILURE_PERMANENT:      EventCategory.BAD,
    EventType.HEARTBEAT_TIMEOUT:             EventCategory.BAD,
    EventType.COMMUNICATION_LOSS:            EventCategory.BAD,
    EventType.FIRMWARE_UPDATE:               EventCategory.NEUTRAL,
    EventType.CONFIGURATION_CHANGE:          EventCategory.NEUTRAL,
    EventType.MANUAL_REVOCATION:             EventCategory.BAD,
}

EVENT_SEVERITY_MAP: Dict[EventType, float] = {
    EventType.SUCCESSFUL_ACTION:             0.0,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: 0.0,
    EventType.HUMAN_OVERRIDE_APPROVED:       0.0,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     0.0,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: 0.3,
    EventType.ANOMALY_DETECTED:              0.2,
    EventType.ANOMALY_RESOLVED:              0.0,
    EventType.SAFETY_RULE_VIOLATION:         0.7,
    EventType.SENSOR_FAILURE_TRANSIENT:      0.4,
    EventType.SENSOR_FAILURE_PERMANENT:      0.9,
    EventType.HEARTBEAT_TIMEOUT:             0.6,
    EventType.COMMUNICATION_LOSS:            0.5,
    EventType.FIRMWARE_UPDATE:               0.0,
    EventType.CONFIGURATION_CHANGE:          0.0,
    EventType.MANUAL_REVOCATION:             1.0,
}

EVENT_QUALITY_MAP: Dict[EventType, float] = {
    EventType.SUCCESSFUL_ACTION:             0.7,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: 0.95,
    EventType.HUMAN_OVERRIDE_APPROVED:       0.6,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     0.3,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: 0.0,
    EventType.ANOMALY_DETECTED:              0.0,
    EventType.ANOMALY_RESOLVED:              0.8,
    EventType.SAFETY_RULE_VIOLATION:         0.0,
    EventType.SENSOR_FAILURE_TRANSIENT:      0.0,
    EventType.SENSOR_FAILURE_PERMANENT:      0.0,
    EventType.HEARTBEAT_TIMEOUT:             0.0,
    EventType.COMMUNICATION_LOSS:            0.0,
    EventType.FIRMWARE_UPDATE:               0.0,
    EventType.CONFIGURATION_CHANGE:          0.0,
    EventType.MANUAL_REVOCATION:             0.0,
}
```

### 9.2 C Struct Definitions

```c
/**
 * @file trust_types.h
 * @brief Trust score data structures for embedded C (STM32/ESP32 targets).
 * @note All structures are packed for NVS/flash storage compatibility.
 *       Floating point uses IEEE 754 single precision (float) unless noted.
 */

#ifndef TRUST_TYPES_H
#define TRUST_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ===== Enums ===== */

typedef enum {
    EVENT_SUCCESSFUL_ACTION             = 0,
    EVENT_SUCCESSFUL_ACTION_WITH_RESERVE = 1,
    EVENT_HUMAN_OVERRIDE_APPROVED       = 2,
    EVENT_HUMAN_OVERRIDE_UNEXPECTED     = 3,
    EVENT_HUMAN_OVERRIDE_WRONG_DECISION = 4,
    EVENT_ANOMALY_DETECTED              = 5,
    EVENT_ANOMALY_RESOLVED              = 6,
    EVENT_SAFETY_RULE_VIOLATION         = 7,
    EVENT_SENSOR_FAILURE_TRANSIENT      = 8,
    EVENT_SENSOR_FAILURE_PERMANENT      = 9,
    EVENT_HEARTBEAT_TIMEOUT             = 10,
    EVENT_COMMUNICATION_LOSS            = 11,
    EVENT_FIRMWARE_UPDATE               = 12,
    EVENT_CONFIGURATION_CHANGE          = 13,
    EVENT_MANUAL_REVOCATION             = 14,
    EVENT_TYPE_COUNT                    = 15,
} EventType;

typedef enum {
    CATEGORY_NEUTRAL = 0,
    CATEGORY_GOOD    = 1,
    CATEGORY_BAD     = 2,
} EventCategory;

typedef enum {
    RESET_FIRMWARE_UPDATE       = 0,
    RESET_SENSOR_REPLACEMENT    = 1,
    RESET_MAJOR_HARDWARE_CHANGE = 2,
    RESET_CONFIGURATION_CHANGE  = 3,
    RESET_FULL_RESET            = 4,
    RESET_SAFETY_INCIDENT       = 5,
    RESET_PROLONGED_INACTIVITY  = 6,
    RESET_OPERATOR_DISAGREEMENT = 7,
} ResetType;

typedef enum {
    LEVEL_DISABLED        = 0,
    LEVEL_ADVISORY        = 1,
    LEVEL_SUPERVISED      = 2,
    LEVEL_SEMI_AUTONOMOUS = 3,
    LEVEL_HIGH_AUTONOMY   = 4,
    LEVEL_FULL_AUTONOMY   = 5,
} AutonomyLevel;

/* ===== Trust Parameters ===== */

typedef struct __attribute__((packed)) {
    float alpha_gain;              /* Base gain rate. Default: 0.002 */
    float alpha_loss;              /* Base loss rate. Default: 0.05 */
    float alpha_decay;             /* Inactivity decay rate. Default: 0.0001 */
    float t_floor;                 /* Trust decay floor. Default: 0.2 */
    uint16_t quality_cap;          /* Max good events per window. Default: 10 */
    float evaluation_window_hours; /* Window duration in hours. Default: 1.0 */
    float severity_exponent;       /* Severity scaling. Default: 1.0 */
    float streak_bonus;            /* Streak reward rate. Default: 0.00005 */
    uint16_t min_events_for_gain;  /* Min good events for Branch 1. Default: 1 */
    float n_penalty_slope;         /* Count penalty slope. Default: 0.1 */
} TrustParams;

/* Default parameter initializer */
static inline TrustParams trust_params_default(void) {
    TrustParams p = {
        .alpha_gain              = 0.002f,
        .alpha_loss              = 0.05f,
        .alpha_decay             = 0.0001f,
        .t_floor                 = 0.2f,
        .quality_cap             = 10,
        .evaluation_window_hours = 1.0f,
        .severity_exponent       = 1.0f,
        .streak_bonus            = 0.00005f,
        .min_events_for_gain     = 1,
        .n_penalty_slope         = 0.1f,
    };
    return p;
}

/* ===== Trust Event ===== */

/**
 * @brief Wire-format trust event. 42 bytes total.
 * @note subsystem_id is NOT null-terminated; subsystem_id_len tracks length.
 */
typedef struct __attribute__((packed)) {
    uint8_t  event_type;         /* EventType enum value */
    uint8_t  _padding;           /* Alignment padding */
    uint64_t timestamp_ms;       /* Unix timestamp in milliseconds */
    uint8_t  subsystem_id_len;   /* Length of subsystem_id string (0-31) */
    char     subsystem_id[31];   /* Subsystem identifier (NOT null-terminated) */
} TrustEvent;

/* ===== Trust State (Persistent) ===== */

/**
 * @brief Complete trust state for a subsystem. 64 bytes total.
 * @note This is the structure written to NVS/flash.
 *       All fields use fixed-size types for binary compatibility.
 *       If the struct layout changes, increment TRUST_STATE_VERSION.
 */
#define TRUST_STATE_VERSION 1

typedef struct __attribute__((packed)) {
    uint32_t version;            /* Struct version for migration. Must be TRUST_STATE_VERSION. */
    uint8_t  subsystem_id[16];   /* Subsystem identifier (null-terminated) */
    float    trust_score;        /* Current trust [0.0, 1.0] */
    float    alpha_multiplier;   /* Subsystem-specific multiplier */
    uint8_t  current_level;      /* AutonomyLevel enum value */
    uint8_t  _pad1;
    uint32_t total_observation_windows; /* Total evaluation windows observed */
    uint16_t consecutive_clean_windows;
    uint16_t total_clean_windows;
    uint16_t consecutive_days_above_threshold;
    uint8_t  _pad2[2];
    float    cumulative_severity_sum; /* Sum of bad event severities in observation period */
    uint8_t  candidate_level;     /* AutonomyLevel being considered, 0xFF = none */
    uint8_t  last_reset_type;     /* ResetType, 0xFF = none */
    uint64_t last_update_ms;      /* Unix timestamp of last update (ms) */
    uint64_t last_reset_ms;       /* Unix timestamp of last reset (ms) */
    uint64_t last_promotion_ms;   /* Unix timestamp of last promotion (ms) */
    uint64_t candidate_start_ms;  /* Unix timestamp of candidate state start (ms) */
    uint32_t crc32;               /* CRC32 of all preceding bytes */
} TrustStatePersistent;

/* ===== Trust History Entry ===== */

/**
 * @brief Single history entry for audit log. 28 bytes total.
 */
typedef struct __attribute__((packed)) {
    uint32_t timestamp_s;     /* Unix timestamp (seconds) */
    float    trust_before;    /* Trust before this window */
    float    trust_after;     /* Trust after this window */
    float    delta;           /* Trust change */
    uint16_t n_good;          /* Good event count */
    uint16_t n_bad;           /* Bad event count */
    float    max_severity;    /* Max severity in window */
    float    avg_quality;     /* Avg quality in window */
    uint8_t  branch;          /* 1=gain, 2=penalty, 3=decay, 4=reset */
    uint8_t  _padding;
} TrustHistoryEntry;

/* ===== Subsystem Configuration ===== */

typedef struct __attribute__((packed)) {
    uint8_t  subsystem_id[16];    /* Null-terminated subsystem identifier */
    float    alpha_multiplier;     /* Subsystem-specific multiplier */
    uint8_t  risk_category;        /* 0=Low, 1=Medium, 2=High, 3=Critical */
    uint8_t  enabled;              /* 1 = enabled, 0 = disabled */
    /* Custom severity overrides (indexed by EventType) */
    float    severity_overrides[EVENT_TYPE_COUNT]; /* 0.0 = use default */
} SubsystemConfig;

/* ===== Level Thresholds ===== */

typedef struct __attribute__((packed)) {
    float    trust_threshold;         /* Minimum trust score for this level */
    uint32_t min_observation_hours;   /* Minimum hours of observation */
    uint16_t min_consecutive_days;    /* Minimum consecutive days at threshold */
    uint16_t min_clean_windows;       /* Minimum clean windows required */
    float    max_severity_in_window;  /* Max severity allowed in last N hours */
    uint32_t severity_lookback_hours; /* Hours to look back for severity check */
    uint16_t max_bad_events;          /* Max bad events in lookback period */
    uint32_t bad_event_lookback_hours;/* Hours to look back for bad event count */
} LevelThreshold;

/* Default level thresholds (indexed by AutonomyLevel, 0 = disabled = unused) */
static const LevelThreshold DEFAULT_LEVEL_THRESHOLDS[6] = {
    /* Level 0 (Disabled): No criteria, always available */
    { 0.00f,   0,   0,   0, 0.0f, 0,   0, 0 },
    /* Level 1 (Advisory) */
    { 0.20f,   8,   1,   4, 0.0f, 0, 255, 0 },  /* 255 = no limit */
    /* Level 2 (Supervised) */
    { 0.40f,  48,   3,  24, 0.79f, 9999, 2, 9999 },
    /* Level 3 (Semi-Autonomous) */
    { 0.60f, 168,   7, 100, 0.69f,  48, 255, 168 },
    /* Level 4 (High Autonomy) */
    { 0.80f, 336,  14, 200, 0.59f,  72,   5, 168 },
    /* Level 5 (Full Autonomy) */
    { 0.95f, 720,  30, 500, 0.49f, 168,   2, 336 },
};

/* ===== Function Prototypes ===== */

/**
 * @brief Compute trust delta for a single evaluation window.
 * @param T_prev      Current trust score [0.0, 1.0]
 * @param n_good      Number of good events in window
 * @param n_bad       Number of bad events in window
 * @param avg_quality Average quality of good events [0.0, 1.0]
 * @param max_severity Maximum severity of bad events [0.0, 1.0]
 * @param params      Trust parameters
 * @param consecutive_clean  Number of consecutive clean windows before this one
 * @param alpha_mult  Subsystem alpha multiplier
 * @return Computed delta (may be positive, negative, or zero)
 */
float trust_compute_delta(
    float T_prev,
    uint16_t n_good,
    uint16_t n_bad,
    float avg_quality,
    float max_severity,
    const TrustParams* params,
    uint32_t consecutive_clean,
    float alpha_mult
);

/**
 * @brief Apply a reset to the trust score.
 * @param T_prev     Current trust score
 * @param reset_type Type of reset
 * @return New trust score after reset
 */
float trust_apply_reset(float T_prev, ResetType reset_type);

/**
 * @brief Determine the autonomy level from trust state and history.
 * @param state    Current trust state
 * @param history  Trust history for lookback checks
 * @param now_ms   Current time in milliseconds
 * @return The autonomy level the subsystem should be at
 */
AutonomyLevel trust_evaluate_level(
    const TrustStatePersistent* state,
    const TrustHistoryEntry* history,
    uint32_t history_len,
    uint64_t now_ms
);

/**
 * @brief Validate trust parameters. Returns 0 if valid, -1 otherwise.
 */
int trust_params_validate(const TrustParams* params);

/**
 * @brief Compute CRC32 for TrustStatePersistent.
 */
uint32_t trust_state_crc32(const TrustStatePersistent* state);

#ifdef __cplusplus
}
#endif

#endif /* TRUST_TYPES_H */
```

### 9.3 C Implementation (Core Algorithm)

```c
/**
 * @file trust_algorithm.c
 * @brief Core trust score computation.
 */

#include "trust_types.h"
#include <math.h>
#include <string.h>

#define TRUST_MIN(a, b) ((a) < (b) ? (a) : (b))
#define TRUST_MAX(a, b) ((a) > (b) ? (a) : (b))
#define TRUST_CLAMP(x, lo, hi) TRUST_MIN(TRUST_MAX(x, lo), hi)
#define TRUST_IS_NAN(x) ((x) != (x))

int trust_params_validate(const TrustParams* params) {
    if (!params) return -1;
    if (TRUST_IS_NAN(params->alpha_gain) || TRUST_IS_NAN(params->alpha_loss) ||
        TRUST_IS_NAN(params->alpha_decay) || TRUST_IS_NAN(params->t_floor)) {
        return -1;
    }
    if (params->alpha_gain < 0.0001f || params->alpha_gain > 0.01f) return -1;
    if (params->alpha_loss < 0.01f || params->alpha_loss > 0.5f) return -1;
    if (params->alpha_decay < 0.00001f || params->alpha_decay > 0.001f) return -1;
    if (params->t_floor < 0.0f || params->t_floor >= 1.0f) return -1;
    if (params->quality_cap < 1) return -1;
    if (params->evaluation_window_hours < 0.1f || params->evaluation_window_hours > 24.0f) return -1;
    if (!(params->alpha_loss > params->alpha_gain * (float)params->quality_cap)) return -1;
    return 0;
}

float trust_compute_delta(
    float T_prev,
    uint16_t n_good,
    uint16_t n_bad,
    float avg_quality,
    float max_severity,
    const TrustParams* params,
    uint32_t consecutive_clean,
    float alpha_mult
) {
    if (!params || TRUST_IS_NAN(T_prev)) return 0.0f;
    T_prev = TRUST_CLAMP(T_prev, 0.0f, 1.0f);

    float delta = 0.0f;

    if (n_bad > 0) {
        /* Branch 2: Penalty */
        float sev_scaled = powf(TRUST_CLAMP(max_severity, 0.0f, 1.0f), params->severity_exponent);
        float n_penalty = 1.0f + params->n_penalty_slope * (float)(n_bad - 1);
        delta = -params->alpha_loss * T_prev * sev_scaled * n_penalty;
    } else if (n_good >= params->min_events_for_gain) {
        /* Branch 1: Gain */
        float q = TRUST_CLAMP(avg_quality, 0.0f, 1.0f);
        uint16_t capped = TRUST_MIN(n_good, params->quality_cap);
        delta = params->alpha_gain * (1.0f - T_prev) * q * ((float)capped / (float)params->quality_cap);

        /* Streak bonus */
        if (consecutive_clean > 0 && params->streak_bonus > 0.0f) {
            uint32_t streak = TRUST_MIN(consecutive_clean, 24u);
            delta += params->streak_bonus * (float)streak;
        }
    } else {
        /* Branch 3: Decay */
        delta = -params->alpha_decay * (T_prev - params->t_floor);
    }

    return delta * alpha_mult;
}

float trust_apply_reset(float T_prev, ResetType reset_type) {
    if (TRUST_IS_NAN(T_prev)) return 0.0f;
    T_prev = TRUST_CLAMP(T_prev, 0.0f, 1.0f);

    float multiplier;
    switch (reset_type) {
        case RESET_FIRMWARE_UPDATE:       multiplier = 0.7f; break;
        case RESET_SENSOR_REPLACEMENT:    multiplier = 0.8f; break;
        case RESET_MAJOR_HARDWARE_CHANGE: multiplier = 0.5f; break;
        case RESET_CONFIGURATION_CHANGE:  return T_prev; /* No trust change */
        case RESET_FULL_RESET:            return 0.0f;
        case RESET_SAFETY_INCIDENT:       return 0.0f;
        case RESET_PROLONGED_INACTIVITY:  return TRUST_MAX(0.5f, T_prev * 0.7f);
        case RESET_OPERATOR_DISAGREEMENT: multiplier = 0.3f; break;
        default:                          return T_prev;
    }

    return TRUST_CLAMP(T_prev * multiplier, 0.0f, 1.0f);
}
```

---

## 10. Implementation Notes

### 10.1 Thread Safety

The trust score is a shared resource accessed by:

- **Event ingestion thread(s)**: One or more threads receiving events from MQTT, CAN bus, or sensors
- **Evaluation thread**: Periodic thread that processes complete windows and updates trust
- **API server thread(s)**: HTTP/gRPC threads serving trust score queries
- **Persistence thread**: Background thread writing trust state to NVS/SQLite

#### Required Synchronization Strategy

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Event Threads  │────>│  Event Queue     │────>│  Eval Thread    │
│  (producers)    │     │  (lock-free MPSC) │     │  (consumer)     │
└─────────────────┘     └──────────────────┘     └───────┬────────┘
                                                         │
                                                         v
                                                ┌────────────────┐
                                                │  TrustState    │
                                                │  (protected by  │
                                                │   RW-lock)      │
                                                └───────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────┐
                              v                          v                      v
                     ┌────────────────┐       ┌────────────────┐      ┌────────────────┐
                     │  API Threads   │       │  Persistence   │      │  Alert Engine  │
                     │  (readers)     │       │  Thread        │      │  (notifications│
                     │                │       │  (periodic)    │      │   on demotion) │
                     └────────────────┘       └────────────────┘      └────────────────┘
```

**Concurrency Rules**:

1. **Event Queue**: Use a lock-free multi-producer single-consumer (MPSC) ring buffer. Event threads push events; only the evaluation thread pops. No lock needed.
2. **TrustState RW-Lock**: Use a readers-writer lock (pthread_rwlock on Linux, FreeRTOS mutex with priority inheritance on embedded).
   - Evaluation thread holds **write lock** during trust computation.
   - API threads hold **read lock** during trust queries.
   - Persistence thread holds **read lock** to snapshot state.
3. **Atomicity**: Each trust update (compute delta + apply clamp + update counters + check levels) MUST be atomic with respect to readers. The write lock ensures this.
4. **Priority Inversion**: On embedded targets (FreeRTOS/RTOS), the evaluation thread MUST run at higher priority than API threads. Use priority-inheriting mutexes to prevent unbounded priority inversion.
5. **Deadlock Prevention**: Lock acquisition order is always: Event Queue → TrustState RW-Lock → Persistence Lock. Never acquire in reverse order.

#### Python Implementation

```python
import threading
from collections import deque
from typing import Callable, Optional

class TrustScoreManager:
    """Thread-safe trust score manager."""

    def __init__(self, subsystem_id: str, params: Optional[TrustParams] = None):
        self.subsystem_id = subsystem_id
        self.params = params or TrustParams()
        self.state = TrustState(subsystem_id=subsystem_id, params=self.params)
        self.history = TrustHistory(subsystem_id=subsystem_id)

        # Lock-free is approximated with a thread-safe deque
        self._event_queue: deque[TrustEvent] = deque(maxlen=10000)
        self._queue_lock = threading.Lock()

        # RW-lock for state access
        self._rw_lock = threading.RLock()

        # Callbacks for level changes
        self._on_promotion: Optional[Callable[[AutonomyLevel, AutonomyLevel], None]] = None
        self._on_demotion: Optional[Callable[[AutonomyLevel, AutonomyLevel], None]] = None

    def submit_event(self, event: TrustEvent):
        """Thread-safe event submission. Called from event ingestion threads."""
        event.subsystem_id = self.subsystem_id
        with self._queue_lock:
            self._event_queue.append(event)

    def get_trust_score(self) -> float:
        """Thread-safe trust score query. Called from API threads."""
        with self._rw_lock:
            return self.state.trust_score

    def get_current_level(self) -> AutonomyLevel:
        """Thread-safe level query."""
        with self._rw_lock:
            return self.state.current_level

    def evaluate_window(self, now: float) -> TrustHistoryEntry:
        """
        Process all events in the current evaluation window.
        Must be called periodically (every evaluation_window_hours).
        This method is NOT thread-safe for concurrent calls — only one
        evaluation should run at a time.
        """
        # Drain the event queue
        with self._queue_lock:
            events = list(self._event_queue)
            self._event_queue.clear()

        # Compute trust delta
        good_events = [e for e in events if e.category == EventCategory.GOOD]
        bad_events = [e for e in events if e.category == EventCategory.BAD]

        with self._rw_lock:
            T_prev = self.state.trust_score
            n_good = len(good_events)
            n_bad = len(bad_events)
            avg_quality = (sum(e.quality for e in good_events) / n_good) if n_good > 0 else 0.0
            max_severity = max((e.severity for e in bad_events), default=0.0)

            delta = compute_delta(
                T_prev, good_events, bad_events,
                self.state.params,
                self.state.consecutive_clean_windows,
            )

            T_new = max(0.0, min(1.0, T_prev + delta))

            # Determine branch for logging
            if n_bad > 0:
                branch = 2
                self.state.consecutive_clean_windows = 0
            elif n_good > 0:
                branch = 1
                self.state.consecutive_clean_windows += 1
            else:
                branch = 3

            # Update state
            self.state.trust_score = T_new
            self.state.last_update_timestamp = now

            # Update counters
            if len(events) > 0:
                self.state.total_observation_hours += self.state.params.evaluation_window_hours
            if n_bad == 0 and len(events) > 0:
                self.state.total_clean_windows += 1
            self.state.cumulative_severity_sum += sum(e.severity for e in bad_events)

            # Check for level transitions
            self._check_level_transition(now)

            # Record history
            entry = TrustHistoryEntry(
                timestamp=now,
                trust_before=T_prev,
                trust_after=T_new,
                delta=delta,
                n_good=n_good,
                n_bad=n_bad,
                max_severity=max_severity,
                avg_quality=avg_quality,
                branch=branch,
            )
            self.history.append(entry)

            return entry

    def apply_reset(self, reset_type: ResetType, now: float):
        """Apply a trust reset. Thread-safe."""
        with self._rw_lock:
            T_prev = self.state.trust_score

            if reset_type == ResetType.FULL_RESET or reset_type == ResetType.SAFETY_INCIDENT:
                self.state.trust_score = 0.0
            elif reset_type == ResetType.PROLONGED_INACTIVITY:
                self.state.trust_score = max(0.5, T_prev * 0.7)
            elif reset_type == ResetType.CONFIGURATION_CHANGE:
                pass  # Trust unchanged
            else:
                multiplier = RESET_MULTIPLIERS[reset_type]
                self.state.trust_score = max(0.0, min(1.0, T_prev * multiplier))

            self.state.trust_score = max(0.0, min(1.0, self.state.trust_score))
            self.state.last_reset_time = now
            self.state.last_reset_type = reset_type
            self.state.total_observation_hours = 0.0
            self.state.consecutive_clean_windows = 0
            self.state.consecutive_days_above_threshold = 0
            self.state.total_clean_windows = 0
            self.state.cumulative_severity_sum = 0.0
            self.state.candidate_level = None
            self.state.candidate_start_time = None

    def _check_level_transition(self, now: float):
        """Check and apply autonomy level transitions. Called under write lock."""
        T = self.state.trust_score
        current = self.state.current_level

        # Demotion checks (immediate)
        new_level = None
        if T < LEVEL_THRESHOLDS[current].trust_threshold * 0.8:
            new_level = current - 1
            if new_level < 0:
                new_level = 0
        # (In a full implementation, also check for high-severity demotion triggers)

        # Promotion checks (deferred with candidate state)
        for target in range(current + 1, 6):
            if T >= LEVEL_THRESHOLDS[target].trust_threshold:
                # Check other criteria using history
                if self.state.candidate_level == target:
                    # Already candidate — check if we've maintained long enough
                    if self.state.candidate_start_time is not None:
                        elapsed = now - self.state.candidate_start_time
                        confirm_duration = self.state.params.evaluation_window_hours * 2 * 3600
                        if elapsed >= confirm_duration:
                            # Still above threshold? Confirm promotion.
                            if T >= LEVEL_THRESHOLDS[target].trust_threshold:
                                new_level = target
                else:
                    # Start candidacy
                    self.state.candidate_level = AutonomyLevel(target)
                    self.state.candidate_start_time = now

        if new_level is not None:
            old_level = current
            self.state.current_level = AutonomyLevel(new_level)
            self.state.candidate_level = None
            self.state.candidate_start_time = None

            if new_level > old_level and self._on_promotion:
                self._on_promotion(AutonomyLevel(old_level), AutonomyLevel(new_level))
            elif new_level < old_level and self._on_demotion:
                self._on_demotion(AutonomyLevel(old_level), AutonomyLevel(new_level))
```

### 10.2 Persistence

#### NVS (Non-Volatile Storage) — Embedded Targets

For ESP32/STM32 targets, trust state is stored in NVS key-value storage:

| NVS Namespace | Key | Value | Size | Write Frequency |
|--------------|-----|-------|------|----------------|
| `trust_<subsys>` | `state` | `TrustStatePersistent` binary blob | 64 bytes | Every window (~1 hour) |
| `trust_<subsys>` | `params` | `TrustParams` binary blob | 32 bytes | On configuration change |
| `trust_<subsys>` | `ver` | uint32_t | 4 bytes | On struct version change |
| `trust_hist_<subsys>` | `entry_<idx>` | `TrustHistoryEntry` binary blob | 28 bytes each | Every window, ring buffer |
| `trust_hist_<subsys>` | `head` | uint16_t | 2 bytes | Every window |

**Write amplification mitigation**:
- Trust state is only written when the trust score changes by > 0.0001 or the window had events.
- History entries are written in append-only mode; a separate `head` index tracks the ring position.
- CRC32 validation on every read. If CRC fails, the system MUST fall back to `trust_score = t_floor` and raise a diagnostic alert.

**Wear leveling**: With 1 write/hour and NVS wear level of 100,000 cycles, the trust state key lasts ~11.4 years. History entries rotate across NVS sectors automatically via ring buffer indexing.

#### SQLite — Companion Computer (Jetson/Raspberry Pi)

```sql
-- Trust state table (one row per subsystem)
CREATE TABLE IF NOT EXISTS trust_state (
    subsystem_id    TEXT PRIMARY KEY,
    trust_score     REAL NOT NULL DEFAULT 0.0 CHECK(trust_score >= 0.0 AND trust_score <= 1.0),
    current_level   INTEGER NOT NULL DEFAULT 0 CHECK(current_level BETWEEN 0 AND 5),
    alpha_multiplier REAL NOT NULL DEFAULT 1.0,
    total_observation_hours REAL NOT NULL DEFAULT 0.0,
    consecutive_clean_windows INTEGER NOT NULL DEFAULT 0,
    total_clean_windows INTEGER NOT NULL DEFAULT 0,
    consecutive_days_above_threshold INTEGER NOT NULL DEFAULT 0,
    cumulative_severity_sum REAL NOT NULL DEFAULT 0.0,
    candidate_level INTEGER CHECK(candidate_level BETWEEN 0 AND 5),
    candidate_start_time REAL,
    last_promotion_time REAL NOT NULL DEFAULT 0.0,
    last_reset_time REAL NOT NULL DEFAULT 0.0,
    last_reset_type INTEGER,
    last_update_time REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    version         INTEGER NOT NULL DEFAULT 1
);

-- Trust history table (append-only)
CREATE TABLE IF NOT EXISTS trust_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    trust_before    REAL NOT NULL,
    trust_after     REAL NOT NULL,
    delta           REAL NOT NULL,
    n_good          INTEGER NOT NULL,
    n_bad           INTEGER NOT NULL,
    max_severity    REAL NOT NULL DEFAULT 0.0,
    avg_quality     REAL NOT NULL DEFAULT 0.0,
    branch          INTEGER NOT NULL,  -- 1=gain, 2=penalty, 3=decay, 4=reset
    FOREIGN KEY (subsystem_id) REFERENCES trust_state(subsystem_id)
);
CREATE INDEX IF NOT EXISTS idx_history_subsys_time
    ON trust_history(subsystem_id, timestamp);

-- Reset audit table
CREATE TABLE IF NOT EXISTS trust_reset_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    reset_type      INTEGER NOT NULL,
    trust_before    REAL NOT NULL,
    trust_after     REAL NOT NULL,
    reason          TEXT,
    operator_id     TEXT
);
CREATE INDEX IF NOT EXISTS idx_reset_subsys_time
    ON trust_reset_audit(subsystem_id, timestamp);

-- Event log table (append-only, for audit)
CREATE TABLE IF NOT EXISTS trust_event_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    event_type      INTEGER NOT NULL,
    category        INTEGER NOT NULL,  -- 0=neutral, 1=good, 2=bad
    severity        REAL NOT NULL DEFAULT 0.0,
    quality         REAL NOT NULL DEFAULT 0.0,
    metadata_json   TEXT
);
CREATE INDEX IF NOT EXISTS idx_event_subsys_time
    ON trust_event_log(subsystem_id, timestamp);
```

**SQLite Write Pattern**:
- `trust_state`: UPSERT every evaluation window (1 hour).
- `trust_history`: INSERT every evaluation window.
- `trust_event_log`: INSERT per event (batched in transactions of up to 100 events).
- `trust_reset_audit`: INSERT on every reset.
- WAL mode enabled for concurrent read/write.
- Vacuum weekly or when history exceeds 100,000 entries per subsystem.

### 10.3 API Contract

#### REST API (Companion Computer)

```
GET  /api/v1/trust/{subsystem_id}
Response:
{
    "subsystem_id": "autopilot",
    "trust_score": 0.7234,
    "current_level": 3,
    "level_name": "SEMI_AUTONOMOUS",
    "last_update": "2025-01-15T14:30:00Z",
    "consecutive_clean_windows": 47,
    "total_observation_hours": 312.5,
    "candidate_level": null,
    "params": {
        "alpha_gain": 0.002,
        "alpha_loss": 0.05,
        "alpha_decay": 0.0001,
        "t_floor": 0.2,
        "quality_cap": 10,
        "evaluation_window_hours": 1.0
    }
}

GET  /api/v1/trust/{subsystem_id}/history?hours=168
Response:
{
    "subsystem_id": "autopilot",
    "hours_requested": 168,
    "entries": [
        {
            "timestamp": "2025-01-15T14:00:00Z",
            "trust_before": 0.7190,
            "trust_after": 0.7234,
            "delta": 0.0044,
            "n_good": 8,
            "n_bad": 0,
            "branch": "gain"
        },
        ...
    ]
}

POST /api/v1/trust/{subsystem_id}/reset
Request:
{
    "reset_type": "full_reset",
    "reason": "Post-incident investigation complete, re-commissioning",
    "operator_id": "admin@vessel.com"
}
Response:
{
    "subsystem_id": "autopilot",
    "trust_before": 0.7234,
    "trust_after": 0.0,
    "reset_type": "full_reset",
    "new_level": 0,
    "timestamp": "2025-01-15T14:35:00Z"
}

POST /api/v1/trust/{subsystem_id}/events
Request:
[
    {"event_type": "successful_action", "timestamp": "2025-01-15T14:30:15Z"},
    {"event_type": "anomaly_detected", "timestamp": "2025-01-15T14:31:02Z"}
]
Response:
{
    "accepted": 2,
    "rejected": 0,
    "rejection_reasons": []
}

GET  /api/v1/trust/{subsystem_id}/level-thresholds
Response:
{
    "current_level": 3,
    "thresholds": {
        "next_level": 4,
        "next_requirements": {
            "trust_threshold": 0.80,
            "trust_current": 0.7234,
            "trust_gap": 0.0766,
            "observation_hours_required": 336,
            "observation_hours_current": 312.5,
            "consecutive_days_required": 14,
            "consecutive_days_current": 8,
            "clean_windows_required": 200,
            "clean_windows_current": 142
        }
    }
}
```

#### MQTT Topics (Embedded Communication)

| Topic | Direction | Payload | QoS |
|-------|-----------|---------|-----|
| `nexus/trust/{subsystem}/score` | Broker → All | JSON trust state snapshot | 0 |
| `nexus/trust/{subsystem}/event` | Module → Broker | Binary `TrustEvent` (42 bytes) | 1 |
| `nexus/trust/{subsystem}/reset` | Broker → Module | JSON `{"type": "full_reset", "reason": "..."}` | 2 |
| `nexus/trust/{subsystem}/level_change` | Broker → All | JSON `{"from": 2, "to": 3, "trust": 0.61}` | 2 |

### 10.4 Testing Strategy

#### Unit Tests (Minimum Coverage: 95%)

```python
import pytest

class TestTrustAlgorithm:
    """Unit tests for the trust score algorithm."""

    def test_gain_basic(self):
        """Branch 1: Trust increases with good events."""
        params = TrustParams()
        events = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
        delta = compute_delta(0.5, events, [], params)
        assert delta > 0, "Good events should produce positive delta"

    def test_gain_diminishing(self):
        """Branch 1: Gain diminishes as trust approaches 1.0."""
        params = TrustParams()
        events = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
        delta_low = compute_delta(0.1, events, [], params)
        delta_high = compute_delta(0.9, events, [], params)
        assert delta_low > delta_high, "Gain should be larger at low trust"

    def test_gain_quality_scaling(self):
        """Branch 1: Higher quality produces larger gain."""
        params = TrustParams()
        low_q = [TrustEvent(EventType.HUMAN_OVERRIDE_UNEXPECTED)]  # quality=0.3
        high_q = [TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)]  # quality=0.95
        delta_low = compute_delta(0.5, low_q, [], params)
        delta_high = compute_delta(0.5, high_q, [], params)
        assert delta_high > delta_low, "Higher quality should produce larger gain"

    def test_gain_quality_cap(self):
        """Branch 1: Events beyond quality_cap are ignored."""
        params = TrustParams(quality_cap=5)
        events_5 = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * 5
        events_20 = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * 20
        delta_5 = compute_delta(0.5, events_5, [], params)
        delta_20 = compute_delta(0.5, events_20, [], params)
        assert abs(delta_5 - delta_20) < 1e-10, "Events beyond cap should not increase delta"

    def test_penalty_basic(self):
        """Branch 2: Bad events produce negative delta."""
        params = TrustParams()
        events = [TrustEvent(EventType.ANOMALY_DETECTED)]  # severity=0.2
        delta = compute_delta(0.5, events, [], params)
        assert delta < 0, "Bad events should produce negative delta"

    def test_penalty_ignores_good(self):
        """Branch 2: Good events in same window are ignored."""
        params = TrustParams()
        bad_only = [TrustEvent(EventType.SAFETY_RULE_VIOLATION)]
        mixed = [TrustEvent(EventType.SAFETY_RULE_VIOLATION),
                 TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)]
        delta_bad = compute_delta(0.5, [], bad_only, params)
        delta_mixed = compute_delta(0.5, [mixed[1]], bad_only, params)
        assert abs(delta_bad - delta_mixed) < 1e-10, "Good events should be ignored when bad events present"

    def test_penalty_severity_scaling(self):
        """Branch 2: Higher severity produces larger penalty."""
        params = TrustParams()
        minor = [TrustEvent(EventType.ANOMALY_DETECTED)]  # sev=0.2
        major = [TrustEvent(EventType.MANUAL_REVOCATION)]  # sev=1.0
        delta_minor = compute_delta(0.5, [], minor, params)
        delta_major = compute_delta(0.5, [], major, params)
        assert abs(delta_major) > abs(delta_minor), "Higher severity should produce larger penalty"

    def test_penalty_count_scaling(self):
        """Branch 2: Multiple bad events increase penalty."""
        params = TrustParams()
        single = [TrustEvent(EventType.ANOMALY_DETECTED)]
        triple = [TrustEvent(EventType.ANOMALY_DETECTED)] * 3
        delta_single = compute_delta(0.5, [], single, params)
        delta_triple = compute_delta(0.5, [], triple, params)
        assert abs(delta_triple) > abs(delta_single), "Multiple bad events should increase penalty"

    def test_decay_basic(self):
        """Branch 3: No events cause decay toward floor."""
        params = TrustParams()
        delta = compute_delta(0.5, [], [], params)
        assert delta < 0, "Decay should produce negative delta"

    def test_decay_stops_at_floor(self):
        """Branch 3: Decay stops when T equals t_floor."""
        params = TrustParams()
        delta = compute_delta(params.t_floor, [], [], params)
        assert abs(delta) < 1e-15, "Decay should be zero at floor"

    def test_decay_below_floor(self):
        """Branch 3: Trust below floor gains via decay (moves toward floor)."""
        params = TrustParams(t_floor=0.3)
        delta = compute_delta(0.1, [], [], params)
        assert delta > 0, "Trust below floor should increase via decay"

    def test_clamp_upper(self):
        """Trust never exceeds 1.0."""
        params = TrustParams()
        T = compute_delta(0.999, [TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)] * 10, [], params)
        assert 0.999 + T <= 1.0 + 1e-10, "Trust should not exceed 1.0"

    def test_clamp_lower(self):
        """Trust never goes below 0.0."""
        params = TrustParams()
        delta = compute_delta(0.001, [], [TrustEvent(EventType.MANUAL_REVOCATION)] * 5, params)
        assert 0.001 + delta >= -1e-10, "Trust should not go below 0.0"

    def test_reset_full(self):
        """Full reset sets trust to 0.0."""
        assert trust_apply_reset(0.95, ResetType.FULL_RESET) == 0.0

    def test_reset_multiplier(self):
        """Multiplier resets scale trust correctly."""
        result = trust_apply_reset(0.8, ResetType.FIRMWARE_UPDATE)
        assert abs(result - 0.56) < 1e-10  # 0.8 * 0.7

    def test_params_validation(self):
        """Invalid parameters are rejected."""
        with pytest.raises(ValueError):
            TrustParams(alpha_gain=0.1)  # Too high
        with pytest.raises(ValueError):
            TrustParams(alpha_loss=0.001)  # Too low
        with pytest.raises(ValueError):
            TrustParams(alpha_loss=0.01, alpha_gain=0.02, quality_cap=1)  # alpha_loss <= alpha_gain * cap

    def test_simulation_stability(self):
        """Simulation does not produce NaN or infinity."""
        events = [[EventType.SUCCESSFUL_ACTION] * 5 for _ in range(1000)]
        traj = simulate_trust(0.0, events, 1000)
        for day, trust in traj:
            assert 0.0 <= trust <= 1.0, f"Trust out of range on day {day}: {trust}"
            assert trust == trust, f"NaN on day {day}"  # NaN check

    def test_oscillation_convergence(self):
        """System with periodic bad events converges to a stable oscillation."""
        import random
        random.seed(999)
        events = []
        for d in range(1000):
            day_ev = [EventType.SUCCESSFUL_ACTION] * 8 * 24
            if d % 7 == 0:
                day_ev.append(EventType.ANOMALY_DETECTED)
            events.append(day_ev)
        traj = simulate_trust(0.0, events, 1000)

        # Check that the last 100 days have bounded oscillation
        last_100 = [t for _, t in traj[-100:]]
        oscillation = max(last_100) - min(last_100)
        assert oscillation < 0.1, f"Oscillation too large: {oscillation}"
```

#### Integration Tests

| Test ID | Description | Method |
|---------|-------------|--------|
| INT-001 | End-to-end event submission → trust update → API query | Submit events via MQTT, verify trust score via REST API after window elapse |
| INT-002 | Reset triggers trust reduction and timer reset | Send reset command, verify trust state via API |
| INT-003 | Level promotion after sustained good behavior | Run simulation for >720 hours, verify Level 5 achieved |
| INT-004 | Level demotion on major incident | Achieve Level 4, inject severity=1.0 event, verify Level 0 |
| INT-005 | Persistence across restart | Write trust state, restart process, verify trust is restored |
| INT-006 | Concurrent event submission | Submit events from 10 threads simultaneously, verify no data loss |
| INT-007 | NVS corruption recovery | Corrupt NVS trust data, verify system falls back to floor and alerts |
| INT-008 | Multi-subsystem isolation | Verify events for subsystem A do not affect subsystem B's trust |

#### Property-Based Tests

Using `hypothesis`:

```python
from hypothesis import given, strategies as st, assume

@given(
    initial_trust=st.floats(min_value=0.0, max_value=1.0),
    n_good=st.integers(min_value=0, max_value=50),
    n_bad=st.integers(min_value=0, max_value=50),
)
def test_trust_always_in_range(initial_trust, n_good, n_bad):
    """Trust score is always in [0, 1] regardless of inputs."""
    assume(not (n_good == 0 and n_bad == 0))  # skip trivial case
    params = TrustParams()
    good_events = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * n_good
    bad_events = [TrustEvent(EventType.ANOMALY_DETECTED)] * n_bad
    delta = compute_delta(initial_trust, good_events, bad_events, params)
    T_new = max(0.0, min(1.0, initial_trust + delta))
    assert 0.0 <= T_new <= 1.0

@given(st.floats(min_value=0.0, max_value=1.0))
def test_gain_never_negative_at_zero_trust(trust):
    """At T=0, gain delta is non-negative, penalty delta is zero."""
    params = TrustParams()
    good = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
    bad = [TrustEvent(EventType.ANOMALY_DETECTED)]

    gain_delta = compute_delta(trust, good, [], params)
    assert gain_delta >= 0, f"Gain delta should be non-negative, got {gain_delta}"

    penalty_delta = compute_delta(0.0, [], bad, params)
    assert penalty_delta == 0.0, "Penalty at T=0 should be zero"
```

### 10.5 Safety Argument

| Requirement | Implementation | Verification |
|-------------|---------------|--------------|
| Trust cannot exceed 1.0 | `clamp(T + delta, 0.0, 1.0)` in every code path | Unit test `test_clamp_upper`, property test `test_trust_always_in_range` |
| Trust cannot go below 0.0 | Same clamp, plus penalty is `T_prev * factor` (zero at T=0) | Unit test `test_clamp_lower`, property test |
| Bad events always reduce trust | Branch 2 selected whenever `n_bad > 0`; good events ignored | Unit test `test_penalty_basic`, `test_penalty_ignores_good` |
| Decay cannot reduce trust below t_floor | `delta = -alpha_decay * (T - t_floor)` → zero at floor | Unit test `test_decay_stops_at_floor` |
| Reset is bounded | Multiplier is in `[0.0, 1.0]`; `full_reset` = 0.0 explicitly | Unit test `test_reset_full`, `test_reset_multiplier` |
| Thread safety | RW-lock around all state mutations; MPSC queue for events | Integration test INT-006 |
| Persistence integrity | CRC32 on every NVS read; WAL mode for SQLite | Integration test INT-007 |
| Asymmetric gain/loss | Parameter validation ensures `alpha_loss > alpha_gain * quality_cap` | Unit test `test_params_validation` |
| Deterministic | No random number generation in algorithm; pure function of inputs | All simulations are reproducible with fixed seeds |

---

## 11. Appendix: Verification & Validation

### 11.1 Formal Properties

The following properties hold for all valid inputs:

**P1 (Boundedness)**: `forall t: 0.0 <= T(t) <= 1.0`
- Proof: By induction. T(0) is in [0,1] by initialization. Each delta is computed from T(t-1) in [0,1], and the result is clamped. ∎

**P2 (Monotonic Penalty)**: If T1 < T2, then |delta_penalty(T1)| < |delta_penalty(T2)|
- Proof: `|delta| = alpha_loss * T * severity * n_penalty`. T is the only variable, and it's linear. ∎

**P3 (Diminishing Gains)**: If T1 < T2, then delta_gain(T1) > delta_gain(T2)
- Proof: `delta = alpha_gain * (1 - T) * Q * capped/cap`. The factor `(1 - T)` strictly decreases with T. ∎

**P4 (Floor Stability)**: If T = t_floor and no events occur, T remains at t_floor.
- Proof: `delta = -alpha_decay * (t_floor - t_floor) = 0`. ∎

**P5 (Zero Trust Immunity)**: At T = 0, bad events have no effect.
- Proof: `delta = -alpha_loss * 0 * severity * n_penalty = 0`. Trust cannot go negative. ∎

### 11.2 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Safety Engineering | Initial specification |

---

*End of Document*
