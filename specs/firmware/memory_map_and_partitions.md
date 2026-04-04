# NEXUS Firmware — Memory Map & Partition Specification

**Document ID:** NEXUS-SPEC-MEM-001
**Revision:** 1.0.0
**Date:** 2025-07-12
**Status:** FINAL — Implementation Reference
**Classification:** Control-Critical Memory Layout
**Target MCU:** ESP32-S3 (single-core, QFN56, 240 MHz, Octal PSRAM)

---

## Table of Contents

1. [SRAM Memory Map](#1-sram-memory-map)
2. [PSRAM Memory Map](#2-psram-memory-map)
3. [Flash Partition Table](#3-flash-partition-table)
4. [Memory Budget Summary](#4-memory-budget-summary)
5. [RTOS Task Configuration](#5-rtos-task-configuration)
6. [DMA Allocation & Cache Coherency](#6-dma-allocation--cache-coherency)

---

## 1. SRAM Memory Map

### 1.1 Overview

The ESP32-S3 provides 512 KB of on-chip SRAM, mapped starting at `0x3FC88000`. This
memory is split into two contiguous banks with different capabilities:

| Bank | Address Range | Size | Executable | DMA-Capable | Malloc Zone |
|------|--------------|------|------------|-------------|-------------|
| **SRAM0 (DRAM)** | `0x3FC88000`–`0x3FCE0000` | 360 KB | Yes (IRAM) | Yes | `heap_caps_malloc(MALLOC_CAP_DMA \| MALLOC_CAP_EXEC)` |
| **SRAM1** | `0x3FCE0000`–`0x3FCF0000` | 64 KB | No (data-only) | Yes | `heap_caps_malloc(MALLOC_CAP_DMA)` |

> **NOTE:** The total on-chip SRAM from `0x3FC88000` to `0x3FCF0000` is 424 KB.
> The remaining 88 KB of the 512 KB budget resides in ROM-data overlay and
> RTC fast/slow memory (see §1.4). Address ranges above are authoritative;
> stated sizes are derived from the range boundaries.

### 1.2 FreeRTOS Heap Regions

ESP-IDF's `heap_caps` allocator manages the on-chip SRAM as follows:

```
+======================== SRAM0 (DRAM) ========================+
| 0x3FC88000                                            0x3FCE0000 |
|                                                           |        |
|  heap_caps_region[0]:  SYSTEM (default malloc)              |
|  ┌───────────────────────────────────────────────────────┐  |
|  │  Size: ~280 KB (after IRAM placement below)          │  |
|  │  Caps: MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL        │  |
|  │  Used by: FreeRTOS kernel, task stacks, general      │  |
|  │           heap allocations, ESP-IDF components       │  |
|  └───────────────────────────────────────────────────────┘  |
|                                                           |        |
|  NO_MALLOC zone (IRAM placed here by linker):               |
|  ┌───────────────────────────────────────────────────────┐  |
|  │  Safety ISR handlers (estop_isr, oc_isr)             │  |
|  │  FreeRTOS portASM & context switch routines          │  |
|  │  Critical interrupt dispatch tables                  │  |
|  │  Size: ~32 KB (linked, not malloc'd)                │  |
|  └───────────────────────────────────────────────────────┘  |
|                                                           |        |
+=============================================================+

+======================== SRAM1 ============================+
| 0x3FCE0000                                            0x3FCF0000 |
|                                                           |        |
|  heap_caps_region[1]:  DMA (32-bit aligned)                |
|  ┌───────────────────────────────────────────────────────┐  |
|  │  Size: 64 KB                                         │  |
|  │  Caps: MALLOC_CAP_DMA | MALLOC_CAP_32BIT             │  |
|  │  Used by: SPI DMA buffers, I2C DMA buffers,          │  |
|  │           UART FIFO DMA, ADC DMA                      │  |
|  │  Note: NOT in the default malloc pool.                │  |
|  │        Must use heap_caps_malloc() explicitly.       │  |
|  └───────────────────────────────────────────────────────┘  |
|                                                           |        |
+=============================================================+
```

### 1.3 NO_MALLOC Zones

The following regions are **excluded** from the FreeRTOS heap and must NOT be
accessed via `malloc()` / `heap_caps_malloc()`. They are statically placed by
the linker script.

| Region | Address Range | Size | Contents |
|--------|--------------|------|----------|
| IRAM (ISR code) | `0x3FC88000` – `0x3FC90000` | 32 KB | Safety ISRs, FreeRTOS port, interrupt vector table |
| Linker BSS/text | Embedded within heap regions | ~4 KB | `noinit` section for watchdog-recovery state |
| RTC FAST memory | `0x3FC88000` aliased | 8 KB | Deep-sleep stub, ULP wakeup code |
| RTC SLOW memory | `0x3FCA0000` aliased | 8 KB | Calibration data retained across resets |

**Enforcement:** The linker script (`sections.ld`) places `NOINIT` and
`.iram` sections first. The `heap_caps` init code scans for occupied regions
and trims the heap boundaries accordingly.

### 1.4 Per-Subsystem SRAM Allocation

All allocations below are placed within the DRAM/SRAM0 heap region
(`heap_caps_region[0]`) unless explicitly noted.

#### Detailed Allocation Table

| Subsystem | Size | Placement | Allocation Method | Notes |
|-----------|------|-----------|-------------------|-------|
| FreeRTOS kernel objects | 32 KB | DRAM heap | `xTaskCreate` / `xQueueCreate` | TCBs (6 × 320 B), queues (8 × 256 B), semaphores (12 × 80 B), timers (4 × 48 B), event groups (2 × 48 B) |
| Task stacks (6 tasks) | 24 KB | DRAM heap | `xTaskCreateStatic` preferred | 4 KB each; placed on 32-byte alignment |
| I/O abstraction driver state | 16 KB | DRAM heap | `malloc` at init | `nx_driver_vtable_t` ctx structs (up to 8 drivers × ~2 KB each) + pin registry + bus state |
| Reflex VM state | 6 KB | DRAM heap | `malloc` (never freed) | VM struct (1.2 KB), data stack 256 × 4 B (1 KB), call stack 16 × 32 B (512 B), 8 × PID state (256 B), 16 × snapshot (2 KB), event ring (256 B), variables (256 × 4 B = 1 KB), sensor/actuator regs (128 × 4 B = 512 B) |
| Serial protocol buffers | 8 KB | DRAM heap | `malloc` at init | RX COBS decode buffer (1053 B × 2 = 2.1 KB), TX COBS encode buffer (1053 B × 2 = 2.1 KB), 4 priority TX queues (32 × 24 B each = 3 KB), frame assembly scratch (512 B) |
| JSON parser workspace | 4 KB | DRAM heap | `malloc` on-demand | cJSON/token pool: max 4 concurrent JSON docs. Pooled; released after parse/serialize |
| Safety monitor | 4 KB | DRAM heap | `malloc` (never freed) | Safety state machine (256 B), solenoid timeout array (256 B), heartbeat tracker (128 B), event log ring (2 KB), watchdog state (256 B), misc flags (1 KB) |
| NVS cache | 2 KB | DRAM heap | ESP-IDF managed | NVS page cache for frequently read keys (driver config, safety params). ESP-IDF default is 32 KB but we override to 2 KB via `CONFIG_NVS_DEFAULT_PAGE_SIZE` |
| Observation metadata | 2 KB | DRAM heap | `malloc` | Recording config (128 B), channel descriptor table (512 B), timestamp bookkeeping (128 B), frame index/wrapping counter (128 B), trigger condition state (512 B), DMA descriptor linking (512 B) |
| DMA buffers | 8 KB | SRAM1 heap | `heap_caps_malloc(MALLOC_CAP_DMA)` | See §6 for detailed DMA breakdown |
| Misc / linker overhead | ~22 KB | Embedded | Static | `.data` (8 KB), `.bss` (10 KB), heap bookkeeping (4 KB). Not user-allocatable. |

#### Address Map Table

The following table shows the approximate virtual addresses within the DRAM
heap after initialization. Values are illustrative (actual layout depends on
linker and allocation order) but represent the definitive intended placement.

| Start Address | End Address | Size | Owner | Description |
|--------------|-------------|------|-------|-------------|
| `0x3FC88000` | `0x3FC90000` | 32 KB | **LINKER (NO_MALLOC)** | ISR code, FreeRTOS port, interrupt vectors |
| `0x3FC90000` | `0x3FC98000` | 32 KB | FreeRTOS kernel | Kernel objects, TCBs, queues, semaphores, timers |
| `0x3FC98000` | `0x3FC9E000` | 24 KB | FreeRTOS scheduler | Task stacks (6 × 4096 B, statically allocated) |
| `0x3FC9E000` | `0x3FCA2000` | 16 KB | I/O driver layer | Driver context structs, pin registry, bus mutexes |
| `0x3FCA2000` | `0x3FCA3800` | 6 KB | Reflex VM | VM instance, stacks, PID state, snapshots, event ring |
| `0x3FCA3800` | `0x3FCA5800` | 8 KB | Serial protocol | COBS encode/decode buffers, TX priority queues |
| `0x3FCA5800` | `0x3FCA6800` | 4 KB | JSON parser | Parsed token workspace (cJSON pool) |
| `0x3FCA6800` | `0x3FCA7800` | 4 KB | Safety monitor | State machine, heartbeat tracker, event log |
| `0x3FCA7800` | `0x3FCA8000` | 2 KB | NVS cache | Key-value cache for hot NVS keys |
| `0x3FCA8000` | `0x3FCA8800` | 2 KB | Observation subsystem | Recording metadata, channel descriptors |
| `0x3FCA8800` | `0x3FCAA880` | 8 KB | **Reserved / misc** | `.data`, `.bss`, heap bookkeeping, alignment padding |
| `0x3FCAA880` | `0x3FCE0000` | ~216 KB | **Free heap** | Uncommitted DRAM heap available for dynamic allocation |

> **Watermark guard:** At runtime, the idle task monitors
> `heap_caps_get_free_size(MALLOC_CAP_8BIT)`. If free DRAM drops below 32 KB,
> a `HEAP_LOW` warning is logged and the safety supervisor is notified. Below
> 16 KB, the system enters DEGRADED mode. Below 8 KB, SAFE_STATE is triggered.

---

## 2. PSRAM Memory Map

### 2.1 Overview

The ESP32-S3 is configured with 8 MB of Octal SPI PSRAM (e.g., ESP-PSRAM64H),
accessed through the cache-mapped address window. PSRAM is **not** DMA-capable
on ESP32-S3; all accesses go through the instruction/data cache (32 KB cache,
configurable mapping).

| Property | Value |
|----------|-------|
| Physical PSRAM size | 8 MB (64 Mbit) |
| Virtual base address | `0x3C000000` (default via `CONFIG_SPIRAM`) |
| Cache mapping | Auto via ESP-IDF MMU (32 KB cache lines) |
| Access method | Standard pointer dereference (cache-backed) |
| DMA support | **No** — must use memcpy to/from SRAM for DMA transfers |
| Speed | ~80 MHz QPI / OPI (cache-mapped, ~40 MB/s sustained) |
| Retention | Volatile (lost on power cycle) |

### 2.2 Region Layout

All offsets below are relative to the PSRAM virtual base address
(`0x3C000000`). The total mapped size is 8 MB (`0x00800000`).

```
+===================== 8 MB PSRAM =====================+
| Offset        | Size      | Region                   |
|===============|===========|==========================|
| 0x00000000    |           |                          |
|               | 5.5 MB    | Observation Buffer       |
|               | (5,767,168)| (ring buffer)           |
| 0x00580000    |           |                          |
|---------------|-----------|--------------------------|
|               | 1 MB      | Reflex Bytecode Storage  |
|               | (1,048,576)| (LittleFS)              |
| 0x00680000    |           |                          |
|---------------|-----------|--------------------------|
|               | 512 KB    | Telemetry Streaming      |
|               | (524,288) | Buffer                   |
| 0x00700000    |           |                          |
|---------------|-----------|--------------------------|
|               | 1 MB      | Free Headroom            |
|               | (1,048,576)| (reserved)              |
| 0x00800000    |           |                          |
+=====================================================+
```

### 2.3 Region Descriptions

#### 2.3.1 Observation Buffer (0x00000000 – 0x00580000)

| Property | Value |
|----------|-------|
| Virtual address | `0x3C000000` – `0x3C57FFFF` |
| Size | 5,767,168 bytes (5.5 MB) |
| Frame size | 32 bytes (see wire protocol §7.1) |
| Frame capacity | 180,224 frames |
| Organization | Contiguous ring buffer |
| Write pointer | 32-bit atomic counter, wraps at 180,224 |
| Access pattern | DMA burst-fill from sensor ADC, serialized read via UART |
| Alignment | 4-byte aligned (required for efficient cache line fills) |

**Ring buffer protocol:**
```
+-------------------------------------------------------------+
|  Frame 0  | Frame 1  | ... | Frame N-1  | Frame 0 (wrap)   |
|  32 bytes | 32 bytes |     | 32 bytes   | 32 bytes         |
+-------------------------------------------------------------+
^                                    ^
|                                    |
write_ptr (incremented per frame)    read_ptr (drained by UART)
```

The observation buffer is filled by the ADC DMA ISR at the configured sample
rate (up to 1 kHz). Frames are drained asynchronously by the telemetry task
and transmitted via `OBS_DUMP_CHUNK` messages over the RS-422 link at
921,600 baud (~92 KB/s theoretical; ~45 KB/s practical with COBS overhead).

At 1 kHz with 32 bytes/frame: 32 KB/s ingest. Buffer holds ~180 seconds of
data — sufficient for a 3-minute recording window at maximum rate.

#### 2.3.2 Reflex Bytecode Storage (0x00580000 – 0x00680000)

| Property | Value |
|----------|-------|
| Virtual address | `0x3C580000` – `0x3C67FFFF` |
| Size | 1,048,576 bytes (1 MB) |
| Filesystem | LittleFS (via `esp_littlefs`) |
| Mount point | `/psram/reflex` |
| Block size | 4 KB |
| Max files | ~32 bytecode files |
| Max file size | ~100 KB (typical reflex script: 2–20 KB) |

**Contents:**
- Compiled `.rbc` (Reflex Bytecode) files — validated bytecode ready for VM execution
- Backup copies of the last-known-good bytecode
- Bytecode manifests with CRC-32 integrity hashes

**Access pattern:** Read-heavy. Bytecode is loaded into DRAM (Reflex VM state, §1.4)
at deployment time. LittleFS wear leveling ensures PSRAM endurance. Writes occur
only during `REFLEX_DEPLOY` and OTA operations.

#### 2.3.3 Telemetry Streaming Buffer (0x00680000 – 0x00700000)

| Property | Value |
|----------|-------|
| Virtual address | `0x3C680000` – `0x3C6FFFFF` |
| Size | 524,288 bytes (512 KB) |
| Organization | Dual-buffer (ping-pong) |
| Buffer A | 0x3C680000 – 0x3C73FFFF (256 KB) |
| Buffer B | 0x3C740000 – 0x3C7FFFFF (256 KB) |
| Purpose | Aggregation of telemetry JSON before UART transmission |

**Operation:** The telemetry task writes JSON payloads into Buffer A. When
Buffer A reaches 80% capacity (or a flush timeout of 100 ms expires), the
buffers swap: Buffer A begins DMA-to-UART transmission while Buffer B accepts
new telemetry writes. This eliminates copy overhead and ensures deterministic
transmission timing.

Typical telemetry JSON size: 200–600 bytes per message at 10 Hz = 2–6 KB/s.
At 512 KB, the streaming buffer holds 85–256 seconds of telemetry — far more
than needed for the 200 ms worst-case UART drain time at 115,200 baud fallback.

#### 2.3.4 Free Headroom (0x00700000 – 0x00800000)

| Property | Value |
|----------|-------|
| Virtual address | `0x3C700000` – `0x3C7FFFFF` |
| Size | 1,048,576 bytes (1 MB) |
| Purpose | Reserved for future use, fragmentation headroom, emergency overflow |

This region is intentionally left uncommitted. It serves as:
1. **Fragmentation headroom:** LittleFS and malloc fragmentation over time will consume space; this prevents allocation failures.
2. **Future expansion:** Additional PSRAM-consuming features (larger observation windows, audio buffers, ML model caching) can be allocated here without repartitioning.
3. **Emergency overflow:** If the observation buffer wraps before UART can drain, an overflow spill region can be dynamically allocated here.

**Policy:** No code shall `malloc` from this region during normal operation.
It is released to the general PSRAM heap pool but monitored via a watermark:
if allocations consume > 256 KB of this region, a `PSRAM_LOW_HEADROOM` warning
is logged.

---

## 3. Flash Partition Table

### 3.1 Physical Flash Configuration

| Property | Value |
|----------|-------|
| Flash type | Quad SPI NOR Flash |
| Flash size | 16 MB (128 Mbit) |
| Flash chip | e.g., W25Q128JV, IS25LP128, GD25Q128 |
| Sector size | 4 KB |
| Block size | 64 KB |
| Page size | 256 bytes |
| Speed | 80 MHz (QPI) |

### 3.2 Partition Table (CSV)

The following CSV content must be placed at
`partitions.csv` in the project root and referenced via
`CONFIG_PARTITION_TABLE_CUSTOM_CSV_PATH="partitions.csv"`.

```csv
# NEXUS Partition Table — ESP32-S3 16MB Flash
# Name,        Type,   SubType,  Offset,   Size,        Flags
nvs,           data,   nvs,      0x9000,   0x4000,
otadata,       data,   ota,      0xD000,   0x2000,
phy_init,      data,   phy,      0xF000,   0x1000,
factory,       app,    factory,  0x10000,  0x200000,     secure_boot_v2
ota_0,         app,    ota_0,    0x210000, 0x200000,     secure_boot_v2
ota_1,         app,    ota_1,    0x410000, 0x200000,     secure_boot_v2
coredump,      data,   coredump, 0x610000, 0x40000,
nexus_cfg,     data,   spiffs,   0x650000, 0x10000,
reflex_bc,     data,   spiffs,   0x660000, 0x100000,
telem_log,     data,   fat,      0x760000, 0x80000,
sensor_cal,    data,   spiffs,   0x7E0000, 0x20000,
safety_log,    data,   spiffs,   0x800000, 0x100000,
reserved,      data,   fat,      0x900000,  0x700000,
```

### 3.3 Partition Detail

| # | Name | Type | SubType | Offset | Size | Description |
|---|------|------|---------|--------|------|-------------|
| 1 | `nvs` | `data` | `nvs` | `0x9000` | 16 KB | Non-volatile key-value storage. Boot flags, safety params, WiFi credentials, calibration data. See `io_driver_interface.h` §8 for full key registry. |
| 2 | `otadata` | `data` | `ota` | `0xD000` | 8 KB | OTA partition selection state. Single entry: which OTA slot is active. |
| 3 | `phy_init` | `data` | `phy` | `0xF000` | 4 KB | RF calibration data (auto-generated at first boot by ESP-IDF). |
| 4 | `factory` | `app` | `factory` | `0x10000` | 2 MB | Factory firmware image. Used for initial programming and fallback if both OTA slots are corrupt. |
| 5 | `ota_0` | `app` | `ota_0` | `0x210000` | 2 MB | OTA slot A — active firmware image (A/B scheme). |
| 6 | `ota_1` | `app` | `ota_1` | `0x410000` | 2 MB | OTA slot B — staged/backup firmware image. |
| 7 | `coredump` | `data` | `coredump` | `0x610000` | 256 KB | Crash dump storage. GDB-readable ELF core file written on panic. Overwritten on each crash. |
| 8 | `nexus_cfg` | `data` | `spiffs` | `0x650000` | 64 KB | NEXUS configuration files: role definitions, driver pin maps, telemetry channel configs, reflex trigger tables. |
| 9 | `reflex_bc` | `data` | `spiffs` | `0x660000` | 1 MB | Reflex bytecode files (`.rbc`). Mirror of PSRAM bytecode store for persistence across power cycles. Loaded to PSRAM at boot. |
| 10 | `telem_log` | `data` | `fat` | `0x760000` | 512 KB | Circular telemetry log. Stores recent telemetry JSON for post-mortem analysis. Wear-leveled via FAT filesystem. |
| 11 | `sensor_cal` | `data` | `spiffs` | `0x7E0000` | 128 KB | Per-sensor calibration data: IMU offsets, magnetometer soft-iron matrix, ADC reference values, ToF offset calibration. |
| 12 | `safety_log` | `data` | `spiffs` | `0x800000` | 1 MB | Safety event log. Persistent record of all safety events (E-Stop, overcurrent, watchdog, heartbeat loss) with timestamps. Ring-buffer: oldest entries overwritten. |
| 13 | `reserved` | `data` | `fat` | `0x900000` | 7 MB | Reserved for future use. Potential: larger OTA images, additional data partitions, or rollback journal. Currently unused. |

**Flash usage verification:**

| Category | Size | Running Total |
|----------|------|---------------|
| Bootloader + partition table | 36 KB (`0x0000` – `0x9000`) | 36 KB |
| NVS | 16 KB (`0x9000`) | 52 KB |
| OTA data | 8 KB (`0xD000`) | 60 KB |
| PHY init | 4 KB (`0xF000`) | 64 KB |
| Factory app | 2 MB (`0x10000`) | 2.063 MB |
| OTA_0 | 2 MB (`0x210000`) | 4.063 MB |
| OTA_1 | 2 MB (`0x410000`) | 6.063 MB |
| Coredump | 256 KB (`0x610000`) | 6.313 MB |
| NEXUS config | 64 KB (`0x650000`) | 6.375 MB |
| Reflex bytecode | 1 MB (`0x660000`) | 7.375 MB |
| Telemetry log | 512 KB (`0x760000`) | 7.875 MB |
| Sensor calibration | 128 KB (`0x7E0000`) | 8.000 MB |
| Safety event log | 1 MB (`0x800000`) | 9.000 MB |
| Reserved | 7 MB (`0x900000`) | **16.000 MB** |

All offsets verified contiguous: `0x900000 + 0x700000 = 0x1000000` (exact 16 MB boundary).

### 3.4 Secure Boot & Flash Encryption

Both OTA app partitions carry the `secure_boot_v2` flag, requiring RSA-3072
signature verification before execution. The factory partition is signed at
manufacturing time with the production key.

Flash encryption (AES-XTS-256) is enabled via `CONFIG_SECURE_FLASH_ENC_ENABLED`.
All partitions except `phy_init` are encrypted at rest.

---

## 4. Memory Budget Summary

### 4.1 SRAM Budget (On-Chip)

| Region | Total | Allocated | Free | Utilization |
|--------|-------|-----------|------|-------------|
| DRAM (SRAM0) — total range | 360 KB | 144 KB | 216 KB | 40% |
| FreeRTOS kernel objects | — | 32 KB | — | — |
| Task stacks (6 tasks) | — | 24 KB | — | — |
| I/O driver state | — | 16 KB | — | — |
| Reflex VM state | — | 6 KB | — | — |
| Serial protocol buffers | — | 8 KB | — | — |
| JSON parser workspace | — | 4 KB | — | — |
| Safety monitor | — | 4 KB | — | — |
| NVS cache | — | 2 KB | — | — |
| Observation metadata | — | 2 KB | — | — |
| **SRAM1** — total range | 64 KB | 8 KB | 56 KB | 12.5% |
| DMA buffers | — | 8 KB | — | — |
| **IRAM (NO_MALLOC)** | 32 KB | 32 KB | 0 KB | 100% |
| **SRAM Grand Total** | **456 KB** | **184 KB** | **272 KB** | **40.4%** |

> **Design margin:** 272 KB free SRAM (60% headroom) provides substantial
> buffer for: (a) future task additions, (b) ESP-IDF library allocations (WiFi/
> Bluetooth stacks if enabled, ~80 KB), (c) transient peak allocations during
> JSON parsing or OTA chunk assembly, (d) fragmentation tolerance over multi-day
> runtimes.

### 4.2 PSRAM Budget

| Region | Total | Allocated | Free (headroom) | Utilization |
|--------|-------|-----------|-----------------|-------------|
| Observation buffer | 5.5 MB | 5.5 MB | 0 KB | 100% |
| Reflex bytecode (LittleFS) | 1 MB | ~100 KB (typical) | ~900 KB | ~10% |
| Telemetry streaming buffer | 512 KB | 512 KB | 0 KB | 100% |
| Free headroom | 1 MB | 0 KB | 1 MB | 0% |
| **PSRAM Grand Total** | **8 MB** | **~6.1 MB** | **~1.9 MB** | **~76%** |

> **NOTE:** The Reflex bytecode allocation is typical, not worst-case. The
> LittleFS partition can hold up to 1 MB of bytecode files, but runtime active
> bytecodes loaded into DRAM typically total < 100 KB.

### 4.3 Combined Memory Summary

| Memory Type | Total | Available (budget) | Peak Used | Free at Idle |
|-------------|-------|--------------------|-----------|--------------|
| On-chip SRAM | 456 KB | 424 KB (excl. IRAM) | ~140 KB | ~280 KB |
| PSRAM | 8 MB | 8 MB | ~5.7 MB | ~2.3 MB |
| Flash (data partitions) | ~2.2 MB | 2.2 MB | — | — |
| Flash (app partitions) | 6 MB | 6 MB | ~1.5 MB (typical fw) | — |

---

## 5. RTOS Task Configuration

### 5.1 Task Table

All tasks are created during `app_main()` initialization. No tasks are created
dynamically at runtime (violates determinism requirement).

| # | Task Name | Function Entry | Priority | Stack Size | Frequency / Trigger | Description |
|---|-----------|---------------|----------|------------|-------------------|-------------|
| 1 | `safety_supervisor` | `safety_supervisor_task()` | 24 (`configMAX_PRIORITIES - 1`) | 4096 B | 10 ms (timer) | Monitors heartbeat, task health, solenoid timeouts, safety state machine. See NEXUS-SS-001 §1.4. |
| 2 | `safety_watchdog` | `safety_watchdog_task()` | 23 (`configMAX_PRIORITIES - 2`) | 4096 B | 200 ms (periodic) | Feeds hardware watchdog (MAX6818). Monitors task check-ins. See NEXUS-SS-001 §3.2. |
| 3 | `serial_protocol` | `serial_protocol_task()` | 20 | 4096 B | Event-driven (UART RX ISR wake) | COBS decode, CRC verify, message dispatch. Handles all NEXUS wire protocol message types. Enqueues to command handler queue. |
| 4 | `reflex_vm` | `reflex_vm_task()` | 15 | 4096 B | 1–1000 Hz (configurable per reflex) | Executes Reflex bytecode VM tick loop. Reads sensor registers, runs bytecode, writes actuator registers. One VM instance per task. |
| 5 | `telemetry` | `telemetry_task()` | 10 | 4096 B | 10–100 Hz (configurable, default 10 Hz) | Reads sensor values, formats JSON telemetry, writes to PSRAM streaming buffer, drains via UART TX. |
| 6 | `io_poll` | `io_poll_task()` | 8 | 4096 B | 100 Hz (10 ms period) | Polled I/O acquisition: reads I2C sensors, ADC channels, digital inputs. Populates sensor register file for Reflex VM. Drives DMA-initiated sensor reads. |

### 5.2 Task Stack Details

| Task | Stack Used (typical) | Stack Used (worst) | Stack Free (watermark) | Canary |
|------|---------------------|--------------------|-----------------------|--------|
| `safety_supervisor` | 1.2 KB | 2.1 KB | 1.9 KB | Yes |
| `safety_watchdog` | 512 B | 1024 B | 3.0 KB | Yes |
| `serial_protocol` | 1.8 KB | 3.2 KB | 896 B | Yes |
| `reflex_vm` | 2.4 KB | 3.5 KB | 576 B | Yes |
| `telemetry` | 2.8 KB | 3.8 KB | 256 B | Yes |
| `io_poll` | 2.0 KB | 3.0 KB | 1.0 KB | Yes |

> **Stack canary:** All tasks use `xTaskCreateStatic()` with a 4-byte canary
> pattern (`0xDEADBEEF`) written at the stack limit. The `idle` task checks
> canaries every 1 second. A corrupted canary triggers `NX_SAFETY_STACK_CANARY`
> (see `io_driver_interface.h` §6).

### 5.3 Priority Architecture

```
Priority 25:  (reserved — unused, buffer above safety)
Priority 24:  safety_supervisor          ← Highest application task
Priority 23:  safety_watchdog
Priority 22-21: (reserved for future safety expansion)
Priority 20:  serial_protocol             ← Command interface
Priority 19-16: (reserved for future high-priority tasks)
Priority 15:  reflex_vm                   ← Control loop
Priority 14-11: (reserved)
Priority 10:  telemetry                   ← Non-critical reporting
Priority  9:  (reserved)
Priority  8:  io_poll                     ← Sensor acquisition
Priority  7-2:  (reserved for ESP-IDF system tasks — timer, event loop)
Priority  1:  idle                        ← FreeRTOS idle task
Priority  0:  (never used)
```

`configMAX_PRIORITIES` is set to **25** in `sdkconfig.defaults`.

### 5.4 Inter-Task Communication

| Mechanism | Producer | Consumer | Size | Notes |
|-----------|----------|----------|------|-------|
| `safety_event_queue` | Any task / ISR | `safety_supervisor` | 16 × `nx_safety_event_t` (16 B each) = 256 B | Used for deferred safety event processing |
| `command_queue` | `serial_protocol` | `reflex_vm` / `telemetry` / `io_poll` | 32 × `uint8_t[32]` = 1 KB | Dispatches parsed wire protocol commands |
| `telemetry_queue` | `io_poll` | `telemetry` | 8 × `sensor_snapshot_t` (256 B each) = 2 KB | Delivers sensor data snapshots |
| `reflex_output_queue` | `reflex_vm` | `io_poll` | 8 × `actuator_command_t` (32 B each) = 256 B | Actuator commands from VM to poll task |
| `uart_tx_queue` | `telemetry` / `serial_protocol` | UART ISR (DMA) | 4 × 2048 B = 8 KB | Priority-ordered TX buffers |
| `watchdog_sem` | ISR | `safety_watchdog` | Binary semaphore | Wakes watchdog on HWD pattern requirement |
| `estop_sem` | E-Stop ISR | `safety_supervisor` | Binary semaphore | Deferred E-Stop handler wake |

---

## 6. DMA Allocation & Cache Coherency

### 6.1 DMA Capable Peripherals (ESP32-S3)

The ESP32-S3 provides a General DMA (GDMA) controller with 4 TX channels and
4 RX channels, multiplexable across peripherals:

| Peripheral | GDMA Channel | Direction | Buffer Location | Cache Notes |
|-----------|-------------|-----------|----------------|-------------|
| SPI2 (FSPI) | GDMA_TX_CH0, GDMA_RX_CH0 | Both | SRAM1 (DMA-capable) | No cache on SRAM1 — inherently coherent |
| SPI3 (HSPI) | GDMA_TX_CH1, GDMA_RX_CH1 | Both | SRAM1 | Same as above |
| I2C0 | GDMA_TX_CH2, GDMA_RX_CH2 | Both | SRAM1 | I2C DMA requires 32-bit aligned buffers |
| I2C1 | GDMA_TX_CH3, GDMA_RX_CH3 | Both | SRAM1 | Same as I2C0 |
| UART0 | GDMA_TX_CH0 (shared) | TX only | SRAM1 or DRAM | TX: flush cache before DMA start |
| UART1 | GDMA_TX_CH1 (shared) | TX only | SRAM1 or DRAM | Same as UART0 |
| UART2 | GDMA_TX_CH2 (shared) | TX only | SRAM1 or DRAM | Same as UART0 |
| ADC | Dedicated ADC DMA | RX only | SRAM1 | ADC DMA writes bypass cache; reads from CPU require cache flush |
| LCD/Camera (unused) | GDMA_TX_CH3, GDMA_RX_CH3 | Both | — | Reserved for future use |

### 6.2 DMA Buffer Allocation Table

All DMA buffers are allocated from SRAM1 (`0x3FCE0000` – `0x3FCF0000`) using
`heap_caps_malloc(MALLOC_CAP_DMA | MALLOC_CAP_32BIT)`.

| Buffer | Size | Alignment | Peripheral | Direction | Notes |
|--------|------|-----------|-----------|-----------|-------|
| SPI2 RX buffer (sensor bus) | 1024 B | 32 B | SPI2 (FSPI) | RX | Primary sensor SPI bus. Used for high-speed sensors (e.g., ADC modules, SPI IMUs). Double-buffered: 2 × 1024 B = 2048 B total. |
| SPI2 TX buffer | 512 B | 32 B | SPI2 (FSPI) | TX | SPI command/data transmit. |
| I2C0 RX buffer | 256 B | 32 B | I2C0 | RX | Primary I2C sensor bus. Max single-read: 24 bytes (BME280), buffer sized for batched reads. |
| I2C0 TX buffer | 128 B | 32 B | I2C0 | TX | I2C register address + data for multi-register writes. |
| I2C1 RX buffer | 128 B | 32 B | I2C1 | RX | Secondary I2C bus (if populated). |
| I2C1 TX buffer | 64 B | 32 B | I2C1 | TX | Secondary I2C transmit. |
| UART0 TX DMA buffer | 2048 B | 32 B | UART0 | TX | Debug console output (if enabled). |
| UART1 TX DMA buffer | 2048 B | 32 B | UART1 | TX | Primary NEXUS RS-422 link (Jetson communication). Double-buffered: 2 × 2048 B = 4096 B total. |
| ADC DMA buffer | 1024 B | 32 B | ADC | RX | Observation buffer fill. Written by ADC DMA, copied to PSRAM observation ring by ISR. |

**Total DMA allocation:** 1024×2 + 512 + 256 + 128 + 128 + 64 + 2048×2 + 1024 = **7,584 bytes (~7.4 KB)** of the 64 KB SRAM1 region.

### 6.3 Cache Coherency Protocol

The ESP32-S3 has separate instruction and data caches (32 KB each). SRAM0
(DRAM) is cached; SRAM1 is **uncached** (bypasses cache, which is why it is
used for DMA). PSRAM is always cache-backed.

| Memory | Cached? | DMA Coherent? | Required Action |
|--------|---------|---------------|-----------------|
| SRAM0 (DRAM) | Yes | No | `Cache_WriteBack_Addr()` before DMA TX; `Cache_Invalidate_Addr()` after DMA RX |
| SRAM1 | No (bypass) | Yes | None — inherently coherent |
| PSRAM | Yes | No | `esp_cache_msync()` before/after DMA; OR copy to SRAM1 first |
| Flash | Via MMU | No | ESP-IDF SPI flash driver handles cache ops internally |

**Policy for observation buffer (PSRAM):**
1. ADC DMA writes into SRAM1 ADC buffer (cache-coherent).
2. ADC ISR copies completed samples to PSRAM observation ring using `memcpy()`.
3. Since the PSRAM write is cache-backed, the cache will eventually write back.
4. When draining the observation buffer for UART transmission, the telemetry
   task reads from PSRAM — reads are cache-coherent by default (read-miss
   triggers cache fill).
5. No explicit cache management is needed for the PSRAM observation buffer
   because: (a) the producer (ADC ISR) uses a different cache line than the
   consumer (telemetry task), and (b) the cache line size (32 bytes) matches
   the frame size, ensuring no partial-line writes are observed.

**Policy for UART TX (DMA from DRAM):**
1. The serial protocol task builds outgoing frames in DRAM (COBS-encoded).
2. Before initiating UART TX DMA, the task calls:
   ```c
   esp_cache_msync(tx_buffer, tx_len, ESP_CACHE_MSYNC_FLAG_DIR_C2M);
   ```
3. This ensures the cache write-back completes before DMA reads the buffer.
4. The `serial_protocol` task uses a dedicated 2 KB TX buffer in DRAM, aligned
   to 32 bytes, to avoid cache-line sharing with other allocations.

**Policy for I2C DMA (SRAM1, inherently coherent):**
- No cache management needed.
- All I2C driver buffers are allocated from SRAM1 at driver init time.
- I2C DMA buffers are **never** freed (they persist for the driver lifetime).
- This prevents fragmentation of the limited SRAM1 pool.

### 6.4 DMA Channel Arbitration

GDMA channels are a shared resource. The following arbitration rules apply:

| Priority (high→low) | Peripheral | Justification |
|---------------------|-----------|---------------|
| 1 | ADC (observation) | Safety-critical data acquisition. Must never be starved. |
| 2 | UART1 (Jetson link) | Safety events and heartbeat traffic. |
| 3 | I2C0 (primary sensor bus) | Sensor data for control loops. |
| 4 | I2C1 (secondary sensor bus) | Lower-priority sensors. |
| 5 | SPI2 (sensor SPI) | Used only for SPI-based sensors (not always populated). |
| 6 | UART0 (debug console) | Lowest priority. Can be dropped under contention. |

**Implementation:** GDMA channels are registered at init time via
`gdma_connect()`. If a higher-priority peripheral needs to transfer, it
preempts by calling `gdma_start()` which aborts any in-progress lower-priority
transfer (the lower-priority peripheral's driver handles the restart).

---

## Appendix A: ESP-IDF sdkconfig Overrides

The following `sdkconfig.defaults` entries are required to implement this
memory map:

```
# PSRAM Configuration
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_SPIRAM_USE_MALLOC=y
CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=16384

# Heap Configuration
CONFIG_HEAP_POISONING_COMPREHENSIVE=y
CONFIG_HEAP_TRACING=y

# PSRAM as heap (not mapped)
CONFIG_SPIRAM_IGNORE_NOTFOUND=n

# Task Watchdog
CONFIG_ESP_TASK_WDT=y
CONFIG_ESP_TASK_WDT_TIMEOUT_S=5

# Flash Encryption & Secure Boot
CONFIG_SECURE_FLASH_ENC_ENABLED=y
CONFIG_SECURE_BOOT_V2_ENABLED=y
CONFIG_SECURE_BOOT_SIGNING_KEY="path/to/signing_key.pem"

# NVS
CONFIG_NVS_DEFAULT_PAGE_SIZE=4096
CONFIG_NVS_MAX_ITEM_SIZE=512

# LittleFS for PSRAM
CONFIG_LITTLEFS_SDMMC_SUPPORT=n
CONFIG_LITTLEFS_PAGE_SIZE=256

# FreeRTOS
CONFIG_FREERTOS_HZ=1000
CONFIG_FREERTOS_CHECK_STACKOVERFLOW_CANARY=y
CONFIG_FREERTOS_CHECK_STACKOVERFLOW_NONE=n
CONFIG_FREERTOS_IDLE_TASK_STACKSIZE=1536
CONFIG_FREERTOS_MAX_PRIORITIES=25
CONFIG_FREERTOS_TASK_FUNCTION_WRAPPER=y
CONFIG_FREERTOS_TIMER_TASK_PRIORITY=22
CONFIG_FREERTOS_TIMER_STACK_DEPTH=2048
```

## Appendix B: Runtime Memory Monitoring

The `idle` task (priority 1) executes the following checks every 1 second:

```c
void memory_monitor_tick(void) {
    // SRAM watermarks
    size_t free_dram = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
    size_t free_sram1 = heap_caps_get_free_size(MALLOC_CAP_DMA);
    size_t free_psram = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);

    // Minimum free thresholds (from safety policy)
    const size_t DRAM_MIN_FREE  = 32 * 1024;  // 32 KB
    const size_t SRAM1_MIN_FREE = 8  * 1024;  // 8 KB
    const size_t PSRAM_MIN_FREE = 256 * 1024; // 256 KB

    if (free_dram < DRAM_MIN_FREE) {
        safety_event_t ev = { .code = NX_SAFETY_HEAP_CORRUPT, .severity = HIGH };
        safety_event_queue_send(&ev);
    }
    if (free_psram < PSRAM_MIN_FREE) {
        nx_rt_log(1, "PSRAM headroom low: %u KB", (unsigned)(free_psram / 1024));
    }

    // Stack canary check (all 6 tasks)
    check_stack_canaries();

    // Heap integrity check (lightweight, 1% CPU budget)
    heap_caps_check_integrity_all(0);
}
```

---

**END OF DOCUMENT**

*Document generated from NEXUS-SPEC-MEM-001. Cross-references: NEXUS-SPEC-VM-001 (Reflex VM), NEXUS-SPEC-SS-001 (Safety), NEXUS-PROT-WIRE-001 (Wire Protocol), NEXUS-IO-INTF-002 (Driver Interface).*
