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
