# Hardware-Software Co-Design for Autonomous Robotic Systems

**Knowledge Base Article — NEXUS Platform Systems**

---

## Table of Contents

1. [Co-Design Philosophy](#1-co-design-philosophy)
   - 1.1 [What is Hardware/Software Co-Design?](#11-what-is-hardware-software-co-design)
   - 1.2 [Why It Matters for Autonomous Systems](#12-why-it-matters-for-autonomous-systems)
   - 1.3 [The Traditional Sequential Approach vs. Co-Design](#13-the-traditional-sequential-approach-vs-co-design)
   - 1.4 [NEXUS Case Study: The Reflex VM as Co-Design Artifact](#14-nexus-case-study-the-reflex-vm-as-co-design-artifact)
2. [Processor Selection](#2-processor-selection)
   - 2.1 [The Design Space: MCU, MPU, FPGA, ASIC, GPU, DSP](#21-the-design-space-mcu-mpu-fpga-asic-gpu-dsp)
   - 2.2 [Decision Criteria](#22-decision-criteria)
   - 2.3 [NEXUS's Choices: ESP32-S3 and Jetson Orin Nano](#23-nexuss-choices-esp32-s3-and-jetson-orin-nano)
   - 2.4 [Alternative Analysis: What If NEXUS Used Different Chips?](#24-alternative-analysis-what-if-nexus-used-different-chips)
   - 2.5 [Cost-Performance-Power Pareto Analysis](#25-cost-performance-power-pareto-analysis)
3. [Memory Architecture](#3-memory-architecture)
   - 3.1 [The Memory Hierarchy](#31-the-memory-hierarchy)
   - 3.2 [Memory Bandwidth Analysis for Different Workloads](#32-memory-bandwidth-analysis-for-different-workloads)
   - 3.3 [DMA: Direct Memory Access for Sensor Data](#33-dma-direct-memory-access-for-sensor-data)
   - 3.4 [NEXUS's 5,280-Byte VM Memory Budget](#34-nexuss-5280-byte-vm-memory-budget)
   - 3.5 [Trade-offs: Stack vs. Programs vs. Variable Space](#35-trade-offs-stack-vs-programs-vs-variable-space)
4. [Sensor Integration](#4-sensor-integration)
   - 4.1 [Analog vs. Digital Sensors](#41-analog-vs-digital-sensors)
   - 4.2 [Sensor Communication Interfaces](#42-sensor-communication-interfaces)
   - 4.3 [Sensor Sampling Rates and Synchronization](#43-sensor-sampling-rates-and-synchronization)
   - 4.4 [Sensor Fusion at Hardware Level](#44-sensor-fusion-at-hardware-level)
   - 4.5 [NEXUS's Sensor I/O Model: LOAD_SENSOR Timing](#45-nexuss-sensor-io-model-load_sensor-timing)
5. [Actuator Control](#5-actuator-control)
   - 5.1 [Motor Driver Fundamentals](#51-motor-driver-fundamentals)
   - 5.2 [Power Electronics](#52-power-electronics)
   - 5.3 [Safety: Current Limiting, Thermal Protection, Failsafe](#53-safety-current-limiting-thermal-protection-failsafe)
   - 5.4 [NEXUS's Actuator I/O Model: STORE_ACTUATOR with Bounds Checking](#54-nexuss-actuator-io-model-store_actuator-with-bounds-checking)
   - 5.5 [Kill Switch Hardware Integration](#55-kill-switch-hardware-integration)
6. [Communication Architecture](#6-communication-architecture)
   - 6.1 [Onboard Communication: I2C, SPI, UART](#61-onboard-communication-i2c-spi-uart)
   - 6.2 [Inter-Board Communication: RS-422 NEXUS Wire Protocol](#62-inter-board-communication-rs-422-nexus-wire-protocol)
   - 6.3 [Offboard Communication: WiFi, BLE, 4G/5G, Satellite](#63-offboard-communication-wifi-ble-4g5g-satellite)
   - 6.4 [Protocol Stack Overhead Analysis](#64-protocol-stack-overhead-analysis)
   - 6.5 [COBS Framing + CRC-16: Co-Designed with RS-422](#65-cobs-framing--crc-16-co-designed-with-rs-422)
7. [Power System Design](#7-power-system-design)
   - 7.1 [Power Budget Analysis per Component](#71-power-budget-analysis-per-component)
   - 7.2 [Battery Selection: LiPo, LiFePO4, Lead-Acid](#72-battery-selection-lipo-lifepo4-lead-acid)
   - 7.3 [Power Distribution: Buck Converters, LDOs, PMICs](#73-power-distribution-buck-converters-ldos-pmics)
   - 7.4 [Sleep Modes and Duty Cycling](#74-sleep-modes-and-duty-cycling)
   - 7.5 [NEXUS's Power Budget Breakdown](#75-nexuss-power-budget-breakdown)
8. [Thermal Design](#8-thermal-design)
   - 8.1 [Thermal Resistance Analysis](#81-thermal-resistance-analysis)
   - 8.2 [Passive vs. Active Cooling](#82-passive-vs-active-cooling)
   - 8.3 [Thermal Throttling Impact on Performance](#83-thermal-throttling-impact-on-performance)
   - 8.4 [NEXUS: Managing Jetson at 69°C](#84-nexus-managing-jetson-at-69c)
9. [Mechanical Integration](#9-mechanical-integration)
   - 9.1 [PCB Design for EMC](#91-pcb-design-for-emc)
   - 9.2 [Connector Selection: Marine-Grade IP67+](#92-connector-selection-marine-grade-ip67)
   - 9.3 [Vibration Resistance](#93-vibration-resistance)
   - 9.4 [NEXUS's Marine Environment Challenges](#94-nexuss-marine-environment-challenges)
10. [Safety Hardware](#10-safety-hardware)
    - 10.1 [Hardware Watchdog: MAX6818 with 0x55/0xAA Pattern](#101-hardware-watchdog-max6818-with-0x550xaa-pattern)
    - 10.2 [Emergency Stop Circuit: Redundant MOSFETs and Pull-Downs](#102-emergency-stop-circuit-redundant-mosfets-and-pull-downs)
    - 10.3 [Current Sensing and Overcurrent Protection](#103-current-sensing-and-overcurrent-protection)
    - 10.4 [Communication Loss Detection: Heartbeat Timeout](#104-communication-loss-detection-heartbeat-timeout)
    - 10.5 [NEXUS's Four-Tier Safety: Hardware Design Decisions](#105-nexuss-four-tier-safety-hardware-design-decisions)
11. [Design Trade-off Analysis](#11-design-trade-off-analysis)
    - 11.1 [The Quadrilemma: Performance vs. Power vs. Cost vs. Safety](#111-the-quadrilemma-performance-vs-power-vs-cost-vs-safety)
    - 11.2 [When to Use FPGA vs. MCU vs. MPU](#112-when-to-use-fpga-vs-mcu-vs-mpu)
    - 11.3 [Hardware Safety vs. Software Safety](#113-hardware-safety-vs-software-safety)
    - 11.4 [NEXUS's Specific Trade-offs Documented](#114-nexuss-specific-trade-offs-documented)
12. [Bill of Materials (BOM) for NEXUS Reference Vessel](#12-bill-of-materials-bom-for-nexus-reference-vessel)
13. [Synthesis and Design Principles](#13-synthesis-and-design-principles)
14. [References and Further Reading](#14-references-and-further-reading)

---

## 1. Co-Design Philosophy

### 1.1 What is Hardware/Software Co-Design?

Hardware/software co-design is the simultaneous, collaborative development of a system's physical computing substrate and its executable logic. Rather than treating hardware as a fixed platform upon which software is later deployed (the sequential waterfall approach), co-design recognizes that every significant hardware decision constrains software capability, and every significant software requirement constrains hardware selection. The two domains form a feedback loop: software profiles reveal hardware bottlenecks, which drive hardware revisions, which unlock new software possibilities.

Formally, co-design optimizes across the joint design space {(H, S) | H ∈ H_hardware, S ∈ S_software, C(H, S) ≤ budget} where C is a cost function spanning monetary expense, power consumption, thermal dissipation, physical volume, and development time. The optimal solution (H*, S*) is one where neither domain can be improved without degrading the other — a Pareto optimum in the hardware-software performance plane.

Co-design is distinct from co-verification (verifying hardware and software together after both are complete) and from hardware-in-the-loop simulation (testing software against a hardware model). Co-design makes *joint* decisions during the *definition* phase, before either domain is committed to implementation.

In the context of autonomous robotic systems, co-design encompasses:

- **Instruction set and compiler co-design:** Defining a bytecode ISA (the NEXUS Reflex VM's 32 opcodes) with full knowledge of the target microcontroller's pipeline depth, cache architecture, and cycle counts. Every opcode's published cycle count in the NEXUS VM spec (1–4 cycles) was derived from the Xtensa LX7's 7-stage pipeline characteristics.
- **Memory and algorithm co-design:** Sizing the VM's data stack (256 entries × 4 bytes = 1 KB), call stack (16 entries × 32 bytes = 512 bytes), and variable space (256 × 4 bytes = 1 KB) to fit within the ESP32-S3's SRAM budget while supporting the reflex patterns that the AI code generator produces.
- **Protocol and physical layer co-design:** Selecting COBS (Consistent Overhead Byte Stuffing) framing with CRC-16/CCITT-FALSE checksum specifically because the RS-422 physical layer provides differential signaling but no inherent frame delimiters, and COBS's 0.4% worst-case overhead is negligible at 921,600 baud while its self-synchronizing property handles line noise gracefully.
- **Safety and architecture co-design:** Designing the four-tier safety system (hardware interlock, firmware guard, supervisory task, application control) as an integrated whole, where each tier's response time budget (1 ms, 10 ms, 100 ms, 10 ms respectively) cascades from the physical kill switch's sub-millisecond response to the application's 10 ms control loop period.

### 1.2 Why It Matters for Autonomous Systems

Autonomous systems operate under a unique set of constraints that make co-design not merely beneficial but *essential*:

**Performance.** An autonomous marine vessel must read compass heading at 10 Hz, compute PID correction, and drive the rudder actuator — all within a single 100 ms control period. If the hardware ADC requires 12 ms per sample (as some SAR ADCs do without DMA), the software has only 88 ms remaining for computation, communication, and actuation. Co-design ensures that the ADC, DMA engine, and software are jointly optimized to meet this deadline: the ESP32-S3's ADC DMA writes to SRAM1 in under 1 ms, the ISR copies to the observation ring buffer, and the VM reads from the sensor register file — a pipeline designed holistically rather than assembled from independently selected parts.

**Power.** A battery-powered autonomous vessel may have a 200 Wh battery budget for 8 hours of operation. If the Jetson Orin Nano draws 15 W at full throttle, it alone consumes 120 Wh — leaving only 80 Wh for sensors, actuators, communication, and safety systems. Co-design led NEXUS to operate the Jetson at 10 W (DVFS throttling), use the ESP32-S3 as a power-efficient reflex processor at 0.5 W for real-time control, and implement duty cycling for the Jetson's AI inference — decisions that span hardware power management, software scheduling, and system architecture.

**Safety.** IEC 61508 SIL 1 (the NEXUS target) requires a dangerous failure probability of less than 10⁻⁷ per hour. This cannot be achieved by software alone — hardware interlocks (kill switch, polyfuses, pull-down resistors) are mandatory. But neither can it be achieved by hardware alone — software must monitor sensor staleness, enforce rate limits on actuator commands, and validate heartbeat timing. The NEXUS four-tier safety architecture is a co-design artifact: each tier was defined with full knowledge of what the other tiers can and cannot detect.

**Cost.** Three Jetson Orin Nano Super modules ($249 × 3 = $747) provide 201 TOPS total AI performance. A single Jetson AGX Orin ($1,999) provides 275 TOPS but at 2.7× the cost. Co-design analysis showed that the distributed three-node architecture provides sufficient inference throughput for the vessel's AI workload (navigation planning, fish detection, weather assessment) while enabling graceful degradation (one Jetson fails, two remain) — a capability a single AGX cannot match without additional redundancy hardware.

### 1.3 The Traditional Sequential Approach vs. Co-Design

The traditional sequential approach follows a hardware-first, software-second methodology:

```
Phase 1: Hardware team selects processor, designs PCB, fabricates prototypes
Phase 2: Software team receives hardware, begins development
Phase 3: Integration testing reveals mismatches
Phase 4: Expensive hardware revision (or suboptimal software workarounds)
```

This approach manifests specific failure modes in autonomous systems:

- **Over-specified hardware.** The hardware team selects a processor with 2 GB of RAM "just in case," when the actual software workload fits in 512 KB. The extra RAM costs money, consumes power, and provides no benefit.
- **Under-specified hardware.** The software team discovers that the selected ADC's sample rate is insufficient for sensor fusion, requiring a hardware redesign or algorithmic degradation.
- **Missed optimization opportunities.** Neither team considers that a custom instruction or DMA configuration could eliminate 90% of CPU overhead for a specific workload, because the instruction and the algorithm were designed in isolation.

Co-design inverts this:

```
Phase 1: Joint requirements analysis (workload profiles, safety constraints, power budget)
Phase 2: Co-design space exploration (processor candidates, algorithm options, memory maps)
Phase 3: Joint prototype (FPGA emulation, software-in-the-loop, hardware-in-the-loop)
Phase 4: Iterative refinement (hardware revision informed by software profiling, software revision informed by hardware measurement)
```

In the NEXUS project, co-design produced the following joint decisions that would not have emerged from sequential development:

| Decision | Hardware Constraint | Software Response | Joint Outcome |
|----------|-------------------|-------------------|---------------|
| VM memory budget | ESP32-S3: 512 KB SRAM shared across 6 RTOS tasks | Reflex VM allocated only 6 KB (1.2% of SRAM) | 60% SRAM headroom for future expansion |
| Instruction encoding | Xtensa LX7: no FPU, 7-stage pipeline | VM uses soft-float with CLAMP_F instead of conditional branches | 1–4 cycle deterministic timing per opcode |
| RS-422 protocol | Differential pair, no frame delimiters, 921,600 baud | COBS framing adds 0.4% overhead, self-synchronizing | 92 KB/s effective throughput |
| Safety response times | Kill switch: <1 ms electrical | E-Stop ISR drives all outputs safe in <1 ms | Sub-millisecond system-wide safe state |

### 1.4 NEXUS Case Study: The Reflex VM as Co-Design Artifact

The NEXUS Reflex Bytecode VM is perhaps the most explicit example of hardware-software co-design in the platform. The VM was not designed as a general-purpose virtual machine that happens to run on the ESP32-S3; it was *shaped* by the ESP32-S3's specific characteristics:

**No hardware FPU.** The ESP32-S3 lacks a floating-point unit — all float operations use software emulation (20–50 cycles per operation vs. 1–3 cycles on hardware FPU). Co-design response: the VM's 32 opcodes include CLAMP_F (clamp to range), which replaces a three-instruction compare-branch-clamp sequence with a single 3-cycle instruction. This reduces the number of soft-float operations per reflex tick by 30–50%.

**8-byte fixed instruction format.** The Xtensa LX7 fetches instructions from a 32 KB instruction cache with 32-byte cache lines. An 8-byte instruction means exactly 4 instructions per cache line, enabling deterministic cache behavior — either all 4 instructions are in cache (cache hit) or none are (cache miss), eliminating partial-line thrashing.

**256-entry data stack.** The ESP32-S3 has 32 general-purpose registers visible at any time (via the windowed register option). A stack depth of 256 exceeds the register file, but empirical measurement of deployed reflex programs shows a maximum stack depth of 4 (see vm_benchmark.py results). The 256-entry limit provides 98.5% headroom while the stack array (1 KB) fits comfortably in SRAM.

**READ_PIN and WRITE_PIN as variable access mechanism.** The VM has no dedicated LOAD_VAR/STORE_VAR opcodes. Instead, READ_PIN with operand1 ≥ 64 reads from variable space (operand1 − 64 = variable index), and WRITE_PIN with operand1 ≥ 64 writes to variable space. This co-design decision eliminated two opcodes, keeping the dispatch table at exactly 32 entries for optimal branch prediction on the Xtensa LX7's 7-stage pipeline.

The VM's 5,280-byte total memory footprint — comprising data stack (1 KB), call stack (512 B), variables (1 KB), PID state (256 B), snapshots (2 KB), event ring (256 B), and sensor/actuator registers (512 B) — was determined by jointly analyzing the ESP32-S3's SRAM map (360 KB SRAM0 + 64 KB SRAM1), FreeRTOS's task stack requirements (6 tasks × 4 KB = 24 KB), and the reflex patterns that the Qwen2.5-Coder-7B AI model was expected to generate.

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems]], [[Reflex Bytecode VM Specification|specs/firmware/reflex_bytecode_vm_spec.md]], [[Memory Map and Partition Specification|specs/firmware/memory_map_and_partitions.md]], [[Evolution of Virtual Machines|foundations/evolution_of_virtual_machines.md]]

---

## 2. Processor Selection

### 2.1 The Design Space: MCU, MPU, FPGA, ASIC, GPU, DSP

The processor landscape for autonomous robotic systems spans six major categories, each with distinct characteristics:

**Microcontroller Unit (MCU).** A single-chip computer integrating a processor core, on-chip SRAM (typically 32–512 KB), flash memory (64 KB–16 MB), and peripherals (GPIO, UART, SPI, I2C, ADC, PWM, timers). MCUs execute bare-metal or RTOS-based firmware with deterministic timing. Examples: ESP32-S3 (Xtensa LX7, 240 MHz, 512 KB SRAM), STM32H7 (ARM Cortex-M7, 480 MHz, 1 MB SRAM), RP2040 (ARM Cortex-M0+, 133 MHz, 264 KB SRAM). Power consumption: 50–500 mW active, 5–50 µW deep sleep. Cost: $0.50–$15.00 per unit.

**Microprocessor Unit (MPU).** A higher-performance processor requiring external RAM, storage, and peripheral ICs. MPUs run full operating systems (Linux, QNX, VxWorks) with virtual memory, multi-process scheduling, and filesystem support. Examples: NVIDIA Jetson Orin Nano (ARM Cortex-A78AE, 6-core, 8 GB LPDDR5), Raspberry Pi 4 (ARM Cortex-A72, 4-core, 8 GB LPDDR4), Qualcomm QCS6490 (ARM Cortex-A78 + Cortex-A55). Power consumption: 5–60 W active. Cost: $50–$500 per module.

**Field-Programmable Gate Array (FPGA).** A reconfigurable logic array that can implement custom digital circuits in hardware. FPGAs provide true hardware-level parallelism and deterministic timing with nanosecond precision. Examples: Intel Cyclone 10 (40K LE), Xilinx Artix-7 (33K logic cells), Lattice iCE40 (7.5K LE). Power consumption: 100 mW–10 W. Cost: $5–$500. FPGAs are used when timing requirements exceed MCU capabilities (sub-microsecond response) or when custom hardware accelerators are needed (neural network inference, sensor fusion).

**Application-Specific Integrated Circuit (ASIC).** A custom-designed chip for a specific application. ASICs provide the highest performance and lowest power consumption but require $2–50 million in non-recurring engineering (NRE) costs and 12–24 months development time. Examples: Google TPU, Tesla FSD chip, mobile SoCs. Not practical for low-volume autonomous systems (<10,000 units).

**Graphics Processing Unit (GPU).** A massively parallel processor originally designed for graphics rendering, now essential for AI inference and training. GPUs excel at matrix multiplication — the core operation of neural networks. Examples: NVIDIA Jetson Orin Nano's Ampere GPU (1024 CUDA cores, 40 TOPS INT8), Intel Arc A770. Power consumption: 10–300 W. Used in NEXUS exclusively on the Jetson for AI workloads.

**Digital Signal Processor (DSP).** A specialized processor optimized for real-time signal processing (FIR/IIR filters, FFT, PID). DSPs have hardware multiply-accumulate (MAC) units and circular addressing modes. Examples: Texas Instruments C2000 (motor control), ADI SHARC (audio). Power consumption: 100 mW–5 W. In modern systems, DSP functionality is often integrated into MCUs (ARM Cortex-M4F DSP extensions) or MPUs (ARM Neon SIMD), making standalone DSPs less common.

### 2.2 Decision Criteria

Processor selection for autonomous systems is a multi-dimensional optimization problem. The primary decision criteria, in order of criticality for autonomous operation, are:

**1. Real-time determinism.** Can the processor guarantee that a task will complete within its deadline, every time? MCUs with RTOS provide hard real-time guarantees (worst-case execution time is bounded and measurable). MPUs with Linux provide soft real-time at best (PREEMPT_RT patch improves but does not eliminate jitter). FPGAs provide true hard real-time at the nanosecond level.

**2. Power consumption.** What is the total system power budget? Battery-powered systems must balance compute capability against endurance. The power-performance ratio varies by orders of magnitude: an ESP32-S3 at 0.5 W provides ~500 MIPS; a Jetson Orin Nano at 10 W provides ~100,000 MIPS + 40 TOPS AI — a 20× power increase for 200× performance.

**3. Peripheral integration.** Does the processor have the right I/O interfaces for the sensor and actuator suite? A vessel autopilot needs UART (GPS, NMEA instruments), I2C (compass, IMU, barometer), SPI (high-speed sensors), ADC (battery voltage, rudder feedback), and PWM (motor control, LED indicators). An MCU that requires external interface ICs for any of these adds cost, board space, and failure points.

**4. Software ecosystem.** Is there a mature toolchain, RTOS support, driver library, and debugging infrastructure? The ESP32-S3 benefits from Espressif's ESP-IDF (comprehensive HAL, FreeRTOS integration, OTA framework), the Arduino ecosystem (rapid prototyping), and an active community. A processor with a poor toolchain can double development time.

**5. Cost.** Unit cost at projected production volumes. For the NEXUS reference vessel (projected 10–100 units), the ESP32-S3-WROOM-1-N8R8 costs approximately $6–8 in volume, while the Jetson Orin Nano Super costs $249. At 100 units, the ESP32 bill is $600–800 and the Jetson bill is $24,900 — making the Jetson the dominant cost item.

**6. Safety certification support.** Does the processor have documentation, fault analysis data, and tool qualification evidence suitable for IEC 61508 or ISO 26262 certification? ARM Cortex-M processors have extensive SIL-ready documentation. Espressif's ESP32 family has growing but incomplete safety documentation.

**7. Long-term availability.** Autonomous systems may need to operate for 10–15 years. A processor that goes out of production in 5 years forces an expensive redesign. ARM Cortex-M cores from major vendors (NXP, ST, TI) typically have 10+ year availability guarantees. Espressif has committed to long-term ESP32-S3 production.

### 2.3 NEXUS's Choices: ESP32-S3 and Jetson Orin Nano

The NEXUS platform employs a **dual-processor architecture** — an ESP32-S3 for real-time reflex control and a Jetson Orin Nano Super for cognitive AI processing — connected by an RS-422 serial link running the NEXUS Wire Protocol. This architecture embodies the reflex-cognitive dichotomy described in the NEXUS platform documentation.

**ESP32-S3 (Reflex Layer):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Core | Xtensa LX7, dual-core @ 240 MHz | Core 0: protocol/I/O; Core 1: VM execution |
| SRAM | 512 KB on-chip | Sufficient for 6 FreeRTOS tasks + VM state + protocol buffers with 60% headroom |
| PSRAM | 8 MB octal SPI | Observation buffer (5.5 MB), bytecode storage (1 MB), telemetry streaming (512 KB) |
| Flash | 16 MB QSPI | Firmware (2 MB per OTA slot × 3), config (64 KB), safety log (1 MB), sensor cal (128 KB) |
| WiFi | 802.11 b/g/n | NEXUSLink-Wireless protocol, OTA updates, cloud telemetry |
| BLE | 5.0 | NEXUSLink-BLE companion protocol, provisioning |
| USB | OTG Full-Speed | NEXUSLink-USB, serial/JTAG debugging |
| ADC | 2 × 12-bit SAR, 20 channels | Battery monitoring, rudder position, analog sensors |
| GPIO | 45 pins (14 interrupt-capable) | Kill switch sense, digital I/O, PWM outputs, LED indicators |
| PWM (LEDC) | 8 channels, up to 20-bit resolution | Motor control, solenoid drivers, LED dimming |
| UART | 3 ports | RS-422 to Jetson (921,600 baud), GPS (NMEA), debug console |
| I2C | 2 ports (400 kHz–1 MHz) | Compass (HMC5883L), IMU (MPU-6050), barometer (BME280) |
| Security | Secure Boot v2 (RSA-3072), Flash Encryption (AES-256-XTS) | Firmware integrity, IP protection, OTA security |
| ULP coprocessor | RISC-V @ 17.5 MHz | Future power-constrained sensor monitoring |
| Power | ~0.5 W active, ~10 µW deep sleep | Battery-compatible endurance |
| Cost | ~$6–8 (WROOM module) | Low per-node cost enables multi-node architectures |

**Jetson Orin Nano Super (Cognitive Layer):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| CPU | 6× ARM Cortex-A78AE @ 1.5 GHz | VxWorks/QNX-compatible, high single-thread performance |
| GPU | NVIDIA Ampere, 1024 CUDA cores, 32 Tensor cores | 67 TOPS INT8 AI inference |
| Memory | 8 GB LPDDR5, 68 GB/s bandwidth | Qwen2.5-Coder-7B Q4_K_M (4.2 GB) + Phi-3-mini (2.0 GB) + OS (0.5 GB) |
| Storage | NVMe via M.2 slot | Model storage, observation logs, vessel data |
| Video | 2× MIPI CSI-2 | Camera input for vision-based navigation and fish detection |
| Ethernet | 10/100/1000 Mbps | Jetson cluster LAN (Gigabit Ethernet backbone) |
| USB | 3.2 Gen 2 × 2 | Peripherals, debugging |
| Power | 7–25 W (configurable via DVFS) | 10 W operating point for battery compatibility |
| AI performance | 67 TOPS INT8 | Sufficient for concurrent navigation + detection + weather models |
| Cost | $249 per module | High but justified by AI capability; 3-node cluster = $747 |
| Thermal | 69°C throttle threshold | Requires active or passive cooling |

**The co-design rationale for this specific combination:**

The ESP32-S3 was selected as the *reflex processor* because:
1. Its dual-core architecture allows protocol handling and VM execution to run in parallel without interference (deterministic timing for control loops).
2. Its 512 KB SRAM provides ample space for the RTOS task architecture (6 tasks × 4 KB stacks = 24 KB) and the Reflex VM state (6 KB) with 216 KB free headroom.
3. Its peripheral set (I2C, SPI, UART, ADC, PWM, GPIO) directly interfaces with marine autopilot sensors and actuators without requiring external interface ICs.
4. Its WiFi/BLE capability provides a secondary communication path (NEXUSLink-Wireless, NEXUSLink-BLE) alongside the primary RS-422 link.
5. Its $6–8 unit cost enables multi-node architectures — the reference vessel uses 2–4 ESP32-S3 nodes for sensor/actuator expansion.
6. Its ULP-RISC-V coprocessor enables future power-constrained monitoring modes (bilge pump sensors, battery watchdog) without waking the main cores.

The Jetson Orin Nano Super was selected as the *cognitive processor* because:
1. Its 67 TOPS INT8 performance enables real-time inference of Qwen2.5-Coder-7B (for reflex synthesis) and Phi-3-mini (for safety validation) simultaneously.
2. Its ARM Cortex-A78AE cores are automotive-grade with error-correcting code (ECC) memory and RAS (Reliability, Availability, Serviceability) features.
3. Its 8 GB LPDDR5 provides sufficient memory for concurrent model loading without runtime swapping.
4. Its NVMe storage enables local vessel data logging and model versioning.
5. Its MIPI CSI-2 camera interfaces enable vision-based capabilities (navigation, obstacle detection, fish identification).

### 2.4 Alternative Analysis: What If NEXUS Used Different Chips?

To validate the ESP32-S3 + Jetson Orin Nano selection, consider the alternatives:

**What if NEXUS used the STM32H743 (ARM Cortex-M7 @ 480 MHz)?**

| Dimension | ESP32-S3 | STM32H743 | Assessment |
|-----------|----------|-----------|------------|
| Clock speed | 240 MHz | 480 MHz | STM32 2× faster for compute |
| SRAM | 512 KB | 1 MB (SRAM) + 128 KB TCM | STM32 2× more SRAM |
| Flash | 16 MB external | 2 MB internal + external | Equivalent with external flash |
| WiFi/BLE | Integrated | None (requires external module) | ESP32 wins: $6 saved, no RF design |
| ADC | 2 × 12-bit, 20 ch | 2 × 16-bit, 24 ch | STM32 better: higher resolution |
| FPU | None (soft-float) | Double-precision hardware FPU | STM32 10–50× faster float ops |
| Cost | ~$6–8 | ~$12–15 | ESP32 2× cheaper |
| Toolchain | ESP-IDF (excellent, free) | STM32CubeIDE (excellent, free) | Equivalent |
| Safety docs | Limited | Comprehensive (SIL-ready) | STM32 better for certification |

*Verdict:* The STM32H743 would improve raw compute performance and float speed, but would require an external WiFi/BLE module ($3–5 additional BOM cost, additional PCB area, additional RF certification). For NEXUS's marine application where WiFi is used for cloud telemetry and OTA updates, the ESP32-S3's integrated wireless is a decisive advantage. The STM32H743 would be the better choice for a wired-only industrial installation.

**What if NEXUS used the RP2040 (ARM Cortex-M0+ @ 133 MHz)?**

| Dimension | ESP32-S3 | RP2040 | Assessment |
|-----------|----------|-------|------------|
| Clock speed | 240 MHz | 133 MHz | ESP32 1.8× faster |
| SRAM | 512 KB | 264 KB | ESP32 2× more |
| Flash | 16 MB external | 2 MB internal (QSPI) | ESP32 8× more |
| Cores | 2 (SMP) | 2 (independent) | Equivalent but different model |
| WiFi/BLE | Integrated | None | ESP32 wins decisively |
| ADC | 2 × 12-bit | 4 × 12-bit (but no DMA) | ESP32 better (DMA-capable) |
| Cost | ~$6–8 | ~$1.00 | RP2040 6–8× cheaper |
| PIO | None | 2 × programmable I/O | RP2040 unique advantage |

*Verdict:* The RP2040 is inadequate for NEXUS's full feature set. Its 264 KB SRAM cannot accommodate the 6-task FreeRTOS architecture plus the Reflex VM state plus protocol buffers. Its lack of WiFi/BLE eliminates cloud connectivity. However, at $1.00 per unit, the RP2040 would be an excellent choice for *Tier 0* sensor-only nodes in the NEXUS network — simple battery monitors, bilge pump controllers, or temperature sensors that report via UART or I2C to the primary ESP32-S3 node.

**What if NEXUS used the Jetson TX2 (Maxwell GPU, 256 CUDA cores)?**

| Dimension | Jetson Orin Nano Super | Jetson TX2 | Assessment |
|-----------|----------------------|-----------|------------|
| AI performance | 67 TOPS INT8 | ~1 TOPS INT8 | Orin 67× more AI performance |
| GPU architecture | Ampere (2022) | Pascal (2017) | Orin: 2 generations newer |
| CPU | 6× Cortex-A78AE @ 1.5 GHz | 2× Cortex-A57 + 2× Denver2 | Orin: more cores, faster per core |
| Memory | 8 GB LPDDR5 (68 GB/s) | 8 GB LPDDR4 (59 GB/s) | Orin: 15% more bandwidth |
| Power | 7–25 W | 7.5–15 W | TX2: lower max power |
| Cost | $249 | $399 (discontinued) | Orin: cheaper and available |
| Availability | In production | End-of-life | Orin wins |
| SW stack | JetPack 6 (CUDA 12, TensorRT 8) | JetPack 4 (CUDA 10) | Orin: modern ML framework support |

*Verdict:* The Jetson TX2 is obsolete and underpowered for NEXUS's AI workload. The Orin Nano Super provides 67× more AI inference capability at a lower price. The TX2 cannot run Qwen2.5-Coder-7B at usable speeds; the Orin Nano Super runs it at ~17 tokens/second (Q4_K_M quantization).

### 2.5 Cost-Performance-Power Pareto Analysis

The optimal processor selection for an autonomous system lies on the Pareto frontier — the set of solutions where no single criterion can be improved without degrading another:

```
Performance (TOPS / MIPS)
    ▲
    │                              Jetson AGX Orin ($1,999, 60W)
    │
    │         Jetson Orin Nano ($249, 15W)
    │
    │
    │    STM32H7 (480 MIPS, $15, 0.5W)
    │
    │         ESP32-S3 (600 MIPS, $7, 0.5W)
    │
    │
    │  RP2040 (133 MIPS, $1, 0.1W)        ★ NEXUS design point
    │
    └─────────────────────────────────────────────────► Cost ($)
```

NEXUS's dual-processor architecture (ESP32-S3 + Jetson Orin Nano) occupies a design point that no single processor can achieve: it provides both hard real-time reflex control (<1 ms response) and AI inference capability (67 TOPS) while consuming 10.5 W total and costing approximately $257 per node. A single processor attempting to cover both requirements would either be insufficiently powerful for AI (any MCU) or incapable of hard real-time response (any MPU running Linux without PREEMPT_RT).

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems]], [[hardware_compatibility_matrix|specs/ports/hardware_compatibility_matrix.json]], [[Architecture Decision Records|specs/ARCHITECTURE_DECISION_RECORDS.md]]

---

## 3. Memory Architecture

### 3.1 The Memory Hierarchy

Every computing system organizes memory in a hierarchy, trading access speed for capacity and cost. In autonomous robotic systems, the memory hierarchy is particularly critical because sensor data flows through multiple levels, and each level's bandwidth and latency directly impact control loop performance.

The canonical memory hierarchy, from fastest/smallest to slowest/largest:

```
Level 1: CPU Registers         ~1 cycle,  0.5 ns,  256–1024 bytes
Level 2: L1 Cache             ~1 cycle,  1 ns,    16–64 KB
Level 3: L2 Cache             ~10 cycles, 3 ns,   128–512 KB
Level 4: SRAM (on-chip)       ~2 cycles,  10 ns,  32 KB–1 MB
Level 5: PSRAM (external)     ~20 cycles, 50 ns,  1–16 MB
Level 6: NOR Flash            ~20 ms,     25 µs,  1–64 MB
Level 7: SD Card / eMMC       ~100 ms,    250 µs, 1–256 GB
```

On the ESP32-S3, this hierarchy maps to specific physical regions:

| Level | Technology | Latency | Size | NEXUS Usage |
|-------|-----------|---------|------|-------------|
| Registers | Xtensa LX7 register file (windowed) | 1 cycle | 64 × 32-bit | VM execution, ISR handlers |
| L1 I-Cache | 4-way set-associative, 32-byte lines | 1–3 cycles | 32 KB | Firmware code, VM interpreter loop |
| L1 D-Cache | 4-way set-associative, 32-byte lines | 1–3 cycles | 32 KB | Frequently accessed data structures |
| SRAM0 (DRAM) | On-chip, executable, DMA-capable | 2–5 cycles | 360 KB | FreeRTOS heap, task stacks, VM state, protocol buffers |
| SRAM1 | On-chip, data-only, DMA-capable | 2–5 cycles | 64 KB | DMA buffers (ADC, I2C, UART, SPI) |
| PSRAM | Octal SPI, cache-mapped | 20–100 cycles | 8 MB | Observation buffer (5.5 MB), bytecode storage (1 MB) |
| Flash | QSPI NOR, MMU-mapped | ~20 ms (read) | 16 MB | Firmware image, configuration, safety logs |

### 3.2 Memory Bandwidth Analysis for Different Workloads

Different autonomous system workloads have radically different memory access patterns:

**Control loop (PID at 100 Hz):**
- Sensor read: 1 × 4-byte read from sensor register → 4 bytes/tick
- PID compute: 3 multiply + 2 add + 1 compare → ~20 stack operations → 80 bytes/tick
- Actuator write: 1 × 4-byte write → 4 bytes/tick
- Total: ~88 bytes per tick × 100 Hz = 8.8 KB/s
- This workload is entirely cache-resident — never touches PSRAM or Flash at runtime.

**Observation recording (1 kHz, 32-byte frames):**
- ADC DMA → SRAM1 buffer: 32 bytes × 1000 Hz = 32 KB/s
- ISR copy: SRAM1 → PSRAM ring buffer: 32 bytes × 1000 Hz = 32 KB/s
- UART drain: PSRAM → UART1 TX: variable, up to 92 KB/s at 921,600 baud
- This workload is DMA-intensive and PSRAM-bandwidth-limited. At 1 kHz, the observation buffer (5.5 MB) fills in ~172 seconds.

**AI model inference (Jetson, Qwen2.5-Coder-7B at Q4_K_M):**
- Model weights: 4.2 GB loaded into LPDDR5
- Per-token inference: reads ~200 MB of weights (5% of model per layer × ~40 layers)
- Bandwidth: 200 MB × 17 tokens/s = 3.4 GB/s — within LPDDR5's 68 GB/s capability
- This workload is memory-bandwidth-bound on the Jetson; compute utilization is only ~30% but memory bandwidth is ~50% of peak.

**Bytecode VM execution (reflex tick, ~100 instructions):**
- Instruction fetch: 8 bytes × 100 = 800 bytes from SRAM (cached)
- Stack operations: ~200 bytes read/write
- Sensor/actuator register access: ~20 bytes
- Total: ~1 KB per tick — entirely SRAM-resident, cache-friendly

### 3.3 DMA: Direct Memory Access for Sensor Data

Direct Memory Access (DMA) is a hardware mechanism that allows peripherals to transfer data to/from memory without CPU intervention. DMA is essential in autonomous systems for two reasons:

1. **CPU offloading.** At 1 kHz sensor sampling, copying 32 bytes per frame from ADC to memory consumes ~3% of the ESP32-S3's CPU time at 240 MHz (ignoring overhead). With DMA, this drops to zero.

2. **Deterministic timing.** CPU-initiated transfers have variable latency (interrupt latency, cache effects, bus contention). DMA transfers have deterministic latency (fixed bus arbitration, no cache involvement when using SRAM1).

The ESP32-S3's GDMA (General DMA) controller provides 4 TX and 4 RX channels, multiplexed across peripherals. NEXUS's DMA allocation:

| Channel | Peripheral | Direction | Buffer Location | Priority |
|---------|-----------|-----------|----------------|----------|
| ADC DMA | ADC | RX only | SRAM1 (1024 B) | Highest (safety-critical data) |
| UART1 TX | UART1 (Jetson link) | TX | SRAM1 (2048 B) | High (safety events, heartbeat) |
| I2C0 | I2C0 (sensor bus) | Both | SRAM1 (384 B total) | Medium |
| UART0 TX | UART0 (debug) | TX | SRAM1 (2048 B) | Low |

**Critical DMA constraint:** PSRAM is NOT DMA-capable on the ESP32-S3. All DMA transfers must use SRAM1 buffers. When sensor data needs to be stored in the PSRAM observation buffer, the ISR copies from the SRAM1 DMA buffer to PSRAM using `memcpy()`. This two-stage pipeline (DMA → SRAM1 → copy → PSRAM) adds ~1 µs of latency per frame but ensures cache coherency and eliminates DMA-PSRAM corruption risks.

### 3.4 NEXUS's 5,280-Byte VM Memory Budget

The NEXUS Reflex VM's memory footprint was derived from a co-design process that balanced the ESP32-S3's SRAM constraints against the AI-generated reflex programs' requirements. The final allocation:

| Component | Size (bytes) | Calculation | Headroom |
|-----------|-------------|-------------|----------|
| VM struct (state machine, PC, SP, flags) | 1,200 | Fixed overhead | — |
| Data stack | 1,024 | 256 entries × 4 bytes | Empirical max depth: 4 (98.5% free) |
| Call stack | 512 | 16 entries × 32 bytes | Empirical max depth: 2 (87.5% free) |
| PID state (8 controllers) | 256 | 8 × 32 bytes | — |
| Snapshots (16 slots) | 2,048 | 16 × 128 bytes | — |
| Event ring buffer | 256 | 32 events × 8 bytes | — |
| Variables | 1,024 | 256 × 4 bytes | Empirical max used: ~60 (76% free) |
| Sensor registers | 256 | 64 × 4 bytes | — |
| Actuator registers | 256 | 64 × 4 bytes | — |
| **Grand Total** | **6,832** | | |

*Note:* The specification document states a 3 KB budget for the minimum configuration and a 5,280-byte budget for the full configuration. The detailed allocation above totals 6,832 bytes at maximum configuration (all PID controllers, all snapshots, full variable space). The minimum achievable configuration — 1 PID controller, no snapshots, 16 variables — requires 2,592 bytes. The 5,280-byte figure represents the typical deployment configuration with 4 PID controllers, 8 snapshots, and 32 variables.

This 6 KB allocation represents only **2.1%** of the ESP32-S3's 360 KB DRAM budget — a deliberate co-design choice that leaves substantial headroom for RTOS task stacks (24 KB), protocol buffers (8 KB), I/O driver state (16 KB), and the general heap (~216 KB free).

### 3.5 Trade-offs: Stack vs. Programs vs. Variable Space

Within the VM's memory budget, three components compete for space:

| Trade-off | Increase Stack | Increase Programs | Increase Variables |
|-----------|---------------|-------------------|-------------------|
| Pro | Deeper expression nesting (complex formulas) | More concurrent reflex programs | More state per reflex (history buffers, calibration) |
| Con | Less SRAM for other subsystems | Flash storage for bytecode | Less SRAM for other subsystems |
| Impact | Stack overflow at 256 entries triggers HALT | Flash limited to 1 MB (LittleFS) | Variable index overflow at 256 triggers ERR_INVALID_OPERAND |

The 256-entry stack depth was determined by analysis of the patterns the Qwen2.5-Coder-7B model generates: typical PID controllers use depth 3–4, state machines use depth 2–3, and threshold detectors use depth 1–2. The maximum observed depth of 4 provides a 64× safety margin (256 / 4 = 64).

The 256-variable limit was chosen to fit within the operand1 field of the READ_PIN/WRITE_PIN opcodes (uint16 range 64–319 maps to variable indices 0–255). Increasing beyond 256 would require either a new opcode or a wider operand field, both of which would break the 32-opcode, 8-byte-fixed-instruction co-design constraint.

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems — Section 7]], [[Memory Map and Partition Specification|specs/firmware/memory_map_and_partitions.md]], [[Reflex Bytecode VM Specification|specs/firmware/reflex_bytecode_vm_spec.md]]

---

## 4. Sensor Integration

### 4.1 Analog vs. Digital Sensors

Sensors in autonomous systems fall into two fundamental categories based on their output interface:

**Analog sensors** produce a continuous voltage or current proportional to the measured quantity. Examples: thermistors (temperature), strain gauges (force), potentiometers (angle), photodiodes (light). Analog sensors require an ADC (Analog-to-Digital Converter) to produce digital readings, and the signal chain includes voltage dividers, instrumentation amplifiers, anti-aliasing filters, and reference voltage sources.

**Digital sensors** produce a digital output — either a serial protocol (I2C, SPI, UART, 1-Wire) or a frequency/PWM output. Examples: BME280 (temperature/humidity/pressure via I2C), MPU-6050 (accelerometer/gyroscope via I2C), HMC5883L (magnetometer via I2C), GPS receivers (NMEA via UART). Digital sensors simplify system design by eliminating the analog signal chain, but introduce communication overhead (bus arbitration, protocol framing, CRC checking).

**Co-design implications:**

- The ESP32-S3's ADC has a noise floor of ~5 LSB (at 12-bit resolution), which limits effective resolution to ~10 bits for precision measurements. NEXUS co-design uses digital sensors (BME280, MPU-6050) wherever possible for the primary sensor suite, reserving the ADC for backup measurements and low-priority inputs (battery voltage, rudder position feedback).
- ADC2 on the ESP32-S3 is unavailable when WiFi is active (shared RF hardware). This co-design constraint means that ADC channels must be routed to ADC1 (10 channels) when wireless communication is required. The NEXUS firmware detects WiFi state and automatically routes ADC channels accordingly.

### 4.2 Sensor Communication Interfaces

The primary sensor communication interfaces in autonomous systems, with their NEXUS usage:

**I2C (Inter-Integrated Circuit):**
- **Topology:** Multi-drop bus, 2 wires (SDA, SCL) + ground. Up to 127 devices on a single bus.
- **Speed:** Standard mode (100 kHz), Fast mode (400 kHz), Fast mode plus (1 MHz), High speed mode (3.4 MHz).
- **NEXUS usage:** I2C0 at 400 kHz (Fast mode) for compass (HMC5883L, address 0x1E), IMU (MPU-6050, address 0x68), barometer (BME280, address 0x76/0x77). Shared with OLED display via mutex. I2C1 at 400 kHz for secondary expansion sensors.
- **Co-design note:** I2C clock stretching (required by BME280) is enabled. The 400 kHz bus speed was chosen as a compromise: 100 kHz would limit sensor read throughput (3 sensors × 6 bytes each = 18 bytes per cycle at ~100 µs per byte = 1.8 ms per cycle), while 1 MHz is unreliable under capacitive loading from long marine cable runs.

**SPI (Serial Peripheral Interface):**
- **Topology:** Point-to-point or daisy-chain, 4 wires (MOSI, MISO, SCLK, CS) + ground.
- **Speed:** Typically 1–80 MHz (ESP32-S3 SPI2 supports up to 80 MHz).
- **NEXUS usage:** SPI2 (FSPI) at 80 MHz for external flash and PSRAM access. SPI3 (HSPI) available for high-speed sensors (not used in reference implementation).
- **Co-design note:** SPI is faster than I2C but uses more GPIO pins (4 per device vs. 2 shared). I2C is preferred for the sensor bus to minimize GPIO consumption, with SPI reserved for flash/PSRAM where bandwidth is critical.

**UART (Universal Asynchronous Receiver/Transmitter):**
- **Topology:** Point-to-point, 2 wires (TX, RX) + optional CTS/RTS flow control.
- **Speed:** 300 baud to 3 Mbps (ESP32-S3 UART1 supports up to 5 Mbps).
- **NEXUS usage:** UART0 at 115,200 baud for debug console. UART1 at 921,600 baud for RS-422 link to Jetson (primary communication channel). UART2 at 4,800–38,400 baud for GPS/NMEA input.
- **Co-design note:** The RS-422 link (UART1) uses hardware flow control (CTS/RTS) to prevent buffer overflow at 921,600 baud. The 8-byte UART FIFO on the ESP32-S3 fills in ~87 µs at this baud rate; CTS/RTS ensures the transmitter pauses before overflow.

**1-Wire:**
- **Topology:** Multi-drop, 1 wire (data) + ground.
- **Speed:** 16.3 kbps (standard mode).
- **NEXUS usage:** Not used in reference implementation. Available for DS18B20 temperature sensors if needed.

**CAN (Controller Area Network):**
- **Topology:** Multi-drop bus, 2 wires (CANH, CANL) + ground.
- **Speed:** 1 Mbps (classical CAN), 5 Mbps (CAN FD).
- **NEXUS usage:** TWAI peripheral (CAN 2.0B) available but unused in reference implementation. Reserved for future marine instrument network integration (NMEA 2000).
- **Co-design note:** CAN was considered as an alternative to RS-422 for inter-board communication but rejected because: (a) CAN's maximum payload (8 bytes classical, 64 bytes CAN FD) is smaller than NEXUS's 1024-byte maximum message; (b) CAN's arbitration mechanism adds variable latency; (c) RS-422's full-duplex operation is simpler than CAN's half-duplex arbitration for point-to-point links.

### 4.3 Sensor Sampling Rates and Synchronization

Different sensors in an autonomous system operate at different sampling rates, and their data must be temporally aligned for sensor fusion:

| Sensor | Typical Rate | NEXUS Rate | Interface | Latency |
|--------|-------------|------------|-----------|---------|
| Compass (HMC5883L) | 1–160 Hz | 10 Hz | I2C | ~5 ms (including bus contention) |
| IMU (MPU-6050) | 4–1,000 Hz | 100 Hz | I2C | ~2 ms |
| Barometer (BME280) | 1–182 Hz | 1 Hz | I2C | ~10 ms (oversampling) |
| GPS (NMEA) | 1–10 Hz | 5 Hz | UART | ~200 ms (receiver latency) |
| Battery voltage (ADC) | 1–100 Hz | 1 Hz | ADC | ~1 ms (conversion) |
| Rudder feedback (ADC) | 10–100 Hz | 10 Hz | ADC | ~1 ms (conversion) |

The NEXUS I/O polling task (io_poll, priority 8, 100 Hz) reads all I2C sensors in a round-robin fashion. A single I2C transaction (address + register + data) takes ~100 µs at 400 kHz. Reading 5 sensors (compass: 6 bytes, IMU accel: 6 bytes, IMU gyro: 6 bytes, barometer: 8 bytes, temperature: 6 bytes) = 32 bytes × 100 µs/byte ≈ 3.2 ms per cycle — well within the 10 ms polling period.

**Sensor synchronization** is achieved by timestamping all sensor reads with the FreeRTOS tick count (1 ms resolution) at the moment of acquisition. The observation frame format (32 bytes, see [[wire_protocol_spec|Wire Protocol Spec §7.1]]) includes a 4-byte timestamp field that enables time-aligned data fusion on the Jetson side.

### 4.4 Sensor Fusion at Hardware Level

Sensor fusion — combining data from multiple sensors to produce a more accurate estimate than any single sensor alone — can be implemented at multiple levels:

**Hardware-level fusion** (on the sensor chip itself). Example: the MPU-6050 integrates a 3-axis accelerometer and 3-axis gyroscope on a single die with an on-chip Digital Motion Processor (DMP) that performs 6-axis sensor fusion and outputs a single quaternion. This eliminates inter-sensor timing skew and reduces I2C bandwidth.

**Firmware-level fusion** (on the MCU). Example: complementary filter or Madgwick filter running on the ESP32-S3 combining compass, accelerometer, and gyroscope data to produce an attitude estimate. NEXUS does not perform firmware-level sensor fusion — this is delegated to the Jetson.

**Cognitive-level fusion** (on the MPU). Example: the Jetson receives sensor data via RS-422, applies extended Kalman filters, neural network-based fusion, or particle filters to produce navigation estimates. This is where NEXUS's AI capabilities are applied.

**Co-design decision:** NEXUS's sensor fusion architecture places the *fast loop* (100 Hz reflex control) on the ESP32-S3 using raw sensor values, and the *slow loop* (sensor fusion, navigation planning) on the Jetson using fused data. This division was driven by the ESP32-S3's lack of an FPU: Kalman filter matrix operations would consume too many CPU cycles in soft-float. The Jetson's hardware FPU and GPU can perform sensor fusion with negligible CPU impact.

### 4.5 NEXUS's Sensor I/O Model: LOAD_SENSOR Timing

In the NEXUS Reflex VM, sensor data is accessed through the READ_PIN opcode (0x1A), which reads from a memory-mapped sensor register file:

```
READ_PIN <sensor_idx>    ; Push sensor value onto stack (2 cycles)
```

The sensor register file (64 entries × 4 bytes = 256 bytes) is populated by the I/O polling task *before* each VM tick. This decoupling is a critical co-design decision:

1. The VM never performs I/O directly — it reads from memory, which is deterministic in timing (2 cycles per READ_PIN).
2. The I/O polling task handles all bus transactions (I2C, SPI, ADC), including retries, error handling, and DMA management.
3. If a sensor fails (I2C NACK, ADC timeout), the register retains its last known value, and the VM continues operating on stale-but-safe data. The safety supervisor detects stale data and escalates.

This "register file indirection" pattern means that READ_PIN timing is always 2 cycles, regardless of whether the underlying sensor is I2C (5 ms transaction) or ADC (1 ms conversion). The I/O task's timing budget absorbs the variable sensor latency.

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems — Section 6]], [[Wire Protocol Specification|specs/protocol/wire_protocol_spec.md]], [[Safety System Specification|specs/safety/safety_system_spec.md]]

---

## 5. Actuator Control

### 5.1 Motor Driver Fundamentals

Actuator control in autonomous systems translates digital commands into physical motion. The primary actuator types and their driver requirements:

**PWM (Pulse Width Modulation) drives.** The most common actuator interface for DC motors, servos, and solenoids. PWM varies the duty cycle of a square wave to control average power delivered to the load. The ESP32-S3's LEDC peripheral provides 8 hardware PWM channels with configurable frequency (5–40 kHz) and resolution (1–20 bits). For NEXUS's marine autopilot:
- Rudder actuator (hydraulic solenoid): PWM at 1 kHz, 10-bit resolution, current-limited via polyfuse
- Throttle actuator (diesel engine governor): PWM at 100 Hz, 8-bit resolution
- Navigation lights: PWM at 1 kHz, 8-bit resolution (brightness control)

**Stepper motor drives.** Used for precision positioning (e.g., camera pan/tilt). Require step/direction or PWM/direction signals. Not used in NEXUS's reference vessel but supported by the LEDC peripheral.

**VFD (Variable Frequency Drive).** Used for large AC motors (pumps, thrusters). VFDs accept analog voltage (0–10 V) or digital (Modbus RTU, RS-485) control signals. NEXUS interfaces with VFDs via a DAC (Digital-to-Analog Converter) output from a PWM-filtered signal or via Modbus RTU over RS-485.

**Relay/solenoid drives.** On/off control for high-power loads (bilge pumps, horn, anchor winch). The ESP32-S3 drives relay coils via MOSFET switches. The NEXUS safety system enforces maximum on-time (5 seconds) and cooldown time (1 second) for solenoids to prevent coil overheating — a hardware constraint that the safety specification documents in detail.

### 5.2 Power Electronics

The power electronics layer between the MCU's GPIO pins and the physical actuators:

**MOSFETs.** N-channel enhancement-mode MOSFETs (e.g., IRLZ44N, 47A, 55V) are the primary switching element for DC loads. The gate is driven by the ESP32-S3's GPIO (3.3 V logic) through a gate driver IC (e.g., TC4420) that provides the 10 V gate drive required for full enhancement. Co-design note: the ESP32-S3's 3.3 V GPIO output is marginal for directly driving MOSFET gates — a gate driver IC is recommended for loads exceeding 2 A.

**H-bridges.** Used for bidirectional motor control (forward/reverse). An H-bridge consists of four MOSFETs arranged in an H configuration, with diagonal pairs switched to change current direction. Examples: L298N (2 A per channel), DRV8825 (stepper, 1.5 A), BTS7960 (43 A). NEXUS uses H-bridges for the trolling motor (bidirectional thrust) and the windlass (anchor up/down).

**Relays.** Electromechanical relays for high-voltage or high-current isolation. Relay coils are driven by MOSFETs, and the relay contacts switch the load circuit. Co-design note: relay contact bounce (5–15 ms) is filtered in software by the NEXUS I/O polling task, which debounces digital inputs and enforces minimum on/off times.

**Flyback diodes.** Inductive loads (solenoids, relays, motors) generate large voltage spikes (V = L × di/dt) when switched off. Flyback diodes (e.g., 1N4007) across inductive loads clamp these spikes to ~0.7 V above the supply rail, protecting MOSFETs from avalanche breakdown.

### 5.3 Safety: Current Limiting, Thermal Protection, Failsafe

Actuator safety operates at three levels in the NEXUS platform:

**Hardware level (Tier 1):**
- **Polyfuses (PTC):** Self-resetting fuses in series with each actuator power output. Trip at 2× nominal current. Self-reset after cooling (<30 seconds). Examples: Bourns MF-R500 (5 A hold, 10 A trip) for motor channels; Bourns MF-R200 (2 A hold, 4 A trip) for relay channels.
- **Flyback diodes:** Clamp inductive kickback to safe levels.
- **Pull-down resistors (10 kΩ):** Ensure MOSFET gates default to OFF state if the ESP32-S3 GPIO is floating (e.g., during reset or firmware crash).

**Firmware level (Tier 2):**
- **Overcurrent detection:** INA219 current sensors with alert pin → GPIO interrupt. When current exceeds the configurable threshold (default: 2× nominal) for 100 ms, the ISR immediately disables the output and notifies the safety supervisor.
- **Solenoid timeout:** Maximum continuous on-time of 5 seconds, followed by 1 second cooldown. Rate limiting of 5 cycles per 10 seconds. These limits prevent coil overheating.
- **Output validation:** All actuator writes pass through the safety guard API, which enforces rate limits, safe-state bounds, and enable gate checks.

**Supervisory level (Tier 3):**
- **Rate limiting:** The safety supervisor enforces maximum command rates per actuator (configurable). A rudder actuator receiving commands at >20 Hz is throttled to prevent control oscillation.
- **Safe-state bounds:** Every actuator has a configurable safe-state value (typically center/zero). If the VM produces an out-of-bounds output, the safety guard clamps it and logs a safety event.

### 5.4 NEXUS's Actuator I/O Model: STORE_ACTUATOR with Bounds Checking

In the NEXUS Reflex VM, actuator commands are issued through the WRITE_PIN opcode (0x1B), which writes to a memory-mapped actuator register file:

```
PUSH_F32  0.75        ; Push rudder command (75% port)
CLAMP_F   -1.0, 1.0  ; Clamp to valid range
WRITE_PIN  0          ; Write to actuator register 0 (2 cycles)
```

The actuator register file (64 entries × 4 bytes = 256 bytes) is drained by the I/O polling task *after* each VM tick. The safety guard API intercepts all writes and enforces:

1. **Bounds checking:** Values outside the configured range [safe_min, safe_max] are clamped.
2. **Rate limiting:** Commands that change too fast are smoothed or rejected.
3. **Enable gate:** Actuator writes are ignored if the safety state machine is in SAFE_STATE or DEGRADED mode.
4. **Current validation:** If the INA219 reports overcurrent on the corresponding channel, writes are rejected.

This "register file indirection with safety guard" pattern means that WRITE_PIN timing is always 2 cycles in the VM, but the actual actuator update may be delayed by the I/O task's polling period (10 ms) or blocked by the safety system.

### 5.5 Kill Switch Hardware Integration

The kill switch is the ultimate safety mechanism — a physical, mushroom-head, twist-to-release, IP67-rated switch wired in series with the +12V actuator power supply. When pressed:

1. The NC (normally closed) contact opens, interrupting power to all actuator circuits. **Response time: <1 ms (electrical).**
2. A dedicated sense wire (separate from the power circuit, routed through a different connector pin) detects the kill switch state change.
3. The sense GPIO (configured with an external 10 kΩ pull-up to 3.3 V) goes LOW, triggering the E-Stop ISR at priority level 1 (highest).
4. The ISR drives all actuator GPIOs to their safe-state values (software-level backup, completing in <1 ms).
5. The deferred handler logs the event, suspends all application tasks, and activates the alarm.

**Co-design criticality:** The kill switch sense wire must NOT share any connector pin, PCB trace, or wire bundle with any other signal. A single fault (corroded connector, chafed wire) that disables both the kill switch power path AND its sense wire would defeat the safety system. NEXUS requires physical separation of these two circuits, documented in the [[Safety System Specification|specs/safety/safety_system_spec.md]] wiring rules.

**Related articles:** [[Safety System Specification|specs/safety/safety_system_spec.md]], [[Wire Protocol Specification|specs/protocol/wire_protocol_spec.md]], [[marine_autonomous_systems|Marine Autonomous Systems]]

---

## 6. Communication Architecture

### 6.1 Onboard Communication: I2C, SPI, UART

The NEXUS platform's onboard communication architecture uses three primary interfaces, each selected for specific workload characteristics:

**I2C (sensor bus):** Used for low-bandwidth, multi-device communication. The primary sensor bus (I2C0) carries compass, IMU, and barometer data. I2C's advantage is bus sharing — up to 127 devices on 2 wires — but its disadvantage is half-duplex operation and bus-lock susceptibility. The NEXUS firmware implements bus-lock recovery: if SCL is held low for >25 ms, the I2C driver generates 9 clock pulses to release the stuck slave.

**SPI (flash/PSRAM bus):** Used for high-bandwidth, point-to-point communication. SPI2 (FSPI) at 80 MHz provides 80 Mb/s (10 MB/s) throughput for external flash access (firmware reads, OTA writes) and PSRAM access (observation buffer, bytecode storage). SPI's advantage is speed and full-duplex operation; its disadvantage is dedicated wiring per device.

**UART (communication links):** Three UARTs serve distinct purposes:
- UART0 (debug console, 115,200 baud): Development and diagnostic output.
- UART1 (Jetson RS-422 link, 921,600 baud): Primary inter-board communication.
- UART2 (GPS input, 4,800–38,400 baud): NMEA 0183 instrument data.

### 6.2 Inter-Board Communication: RS-422 NEXUS Wire Protocol

The inter-board communication link between the Jetson Orin Nano and the ESP32-S3 nodes is the NEXUS platform's critical data path. It carries commands, telemetry, observation data, reflex deployments, OTA firmware updates, and safety events.

**Physical layer:** EIA/TIA-422-B (RS-422), full-duplex differential pair, 921,600 baud default (negotiable to 115,200 for long runs), Cat-6 STP cable, RJ-45 connectors with shield drain.

**Electrical specification:**

| Parameter | Value |
|-----------|-------|
| Transceiver | TI THVD1500 (3.3V, 50 Mbps, ±15 kV ESD) |
| Termination | 120 Ω at each end of bus |
| Cable length (default baud) | 10 m (Cat-5e minimum) |
| Cable length (115,200 baud) | 100 m (Cat-6) |
| Common-mode voltage | -7V to +7V |
| Differential output | ≥ 2.0V (loaded) |
| TVS protection | TPD4E05U06 on each differential pair |

**Co-design rationale for RS-422 over alternatives:**

| Protocol | Max Cable | Speed | Multi-drop | Noise Immunity | Cost |
|----------|-----------|-------|------------|-----------------|------|
| RS-232 | 15 m | 1 Mbps | Point-to-point | Low (single-ended) | Low |
| **RS-422** | **1,200 m** | **10 Mbps** | **1 TX → 10 RX** | **High (differential)** | **Medium** |
| RS-485 | 1,200 m | 10 Mbps | 32 nodes (half-duplex) | High (differential) | Medium |
| CAN | 40 m (1 Mbps) | 1 Mbps | 110 nodes | High (differential) | Medium-High |
| Ethernet | 100 m | 1 Gbps | Multi-drop (with switch) | High (differential) | High |

RS-422 was selected over RS-485 because NEXUS uses a point-to-point (Jetson → ESP32) topology where full-duplex eliminates arbitration overhead. RS-422 was selected over CAN because NEXUS's 1024-byte maximum message payload exceeds CAN's 8-byte limit, and CAN's variable-latency arbitration is incompatible with the heartbeat protocol's timing requirements. RS-422 was selected over Ethernet because the Jetson's Ethernet ports are used for the cluster LAN, and RS-422's simpler driver stack (UART peripheral vs. TCP/IP stack) reduces firmware complexity and SRAM usage.

### 6.3 Offboard Communication: WiFi, BLE, 4G/5G, Satellite

NEXUS supports multiple offboard communication channels, each for a distinct use case:

**WiFi (802.11 b/g/n, 2.4 GHz):**
- **Use case:** Cloud telemetry, OTA firmware updates, SSH/VNC access during development.
- **NEXUS implementation:** ESP32-S3 in STA mode, connects to vessel WiFi access point or shore station.
- **Throughput:** ~35 Mbps TCP (typical), ~10 Mbps in marine environments (interference from other vessels, metal hull reflections).
- **Range:** 100 m (open air), 30 m (through fiberglass hull).
- **Co-design note:** WiFi activity disables ADC2. The firmware disables WiFi during observation recording to maximize ADC channel availability.

**BLE 5.0 (Bluetooth Low Energy):**
- **Use case:** Mobile companion app (vessel status, manual override), provisioning (WiFi credential entry).
- **NEXUS implementation:** ESP32-S3 BLE peripheral with GATT-based NEXUSLink-BLE protocol.
- **Throughput:** ~2 Mbps (BLE 5.0 2M PHY), ~1 KB/s application payload.
- **Range:** 100 m (open air), 30 m (through hull).

**4G/LTE (via external modem):**
- **Use case:** Remote monitoring when beyond WiFi range, cloud AI inference offloading.
- **NEXUS implementation:** Not in reference hardware; supported via USB-connected 4G modem (e.g., Quectel EC25).
- **Latency:** 50–100 ms (typical), unsuitable for real-time control but adequate for telemetry and commands.

**Satellite (Iridium, Inmarsat):**
- **Use case:** Ocean-going vessels beyond cellular range.
- **NEXUS implementation:** Not in reference hardware; supported via Iridium 9603 modem connected via UART.
- **Throughput:** 340 bytes per second (Iridium SBD), ~1 KB per 3-second transmission window.
- **Cost:** $0.03–0.10 per KB — economical for telemetry, prohibitively expensive for observation data.

### 6.4 Protocol Stack Overhead Analysis

The NEXUS Wire Protocol's COBS framing + CRC-16 adds measurable but acceptable overhead:

| Message Type | Payload Size | COBS Overhead | CRC-16 | Header | Total Wire Size | Efficiency |
|-------------|-------------|---------------|--------|--------|----------------|------------|
| HEARTBEAT | 0 bytes | 1 byte | 2 bytes | 10 bytes | 15 bytes | 0% (payload) |
| TELEMETRY (typical) | 256 bytes | 2 bytes | 2 bytes | 10 bytes | 272 bytes | 94.1% |
| REFLEX_DEPLOY | 1,024 bytes | 5 bytes | 2 bytes | 10 bytes | 1,043 bytes | 98.2% |
| COMMAND (typical) | 64 bytes | 1 byte | 2 bytes | 10 bytes | 79 bytes | 81.0% |
| OBS_DUMP_CHUNK | 520 bytes | 3 bytes | 2 bytes | 10 bytes | 537 bytes | 96.8% |

At 921,600 baud, the effective throughput is:

- Theoretical raw: 92,160 bytes/s (921,600 / 10)
- COBS overhead: -0.4% = 91,792 bytes/s
- NEXUS framing (header + CRC): 12 bytes per frame = effective throughput depends on message size
- For 256-byte telemetry messages at 10 Hz: 2,720 bytes/s = 2.95% of available bandwidth
- For 520-byte observation chunks at maximum drain rate: ~45,000 bytes/s = 49% of available bandwidth

The protocol's efficiency is excellent for small messages (heartbeats, commands) and acceptable for bulk data (observation dumps, OTA chunks). The COBS framing's worst-case overhead of 0.4% is negligible compared to the byte-stuffing overhead of HDLC (~20%) or the escape-based framing of SLIP (~10%).

### 6.5 COBS Framing + CRC-16: Co-Designed with RS-422

The COBS (Consistent Overhead Byte Stuffing) encoding was specifically co-designed with the RS-422 physical layer:

**Problem:** RS-422 provides differential signaling for noise immunity but has no frame delimiter mechanism. In a noisy marine environment, bit errors can corrupt byte values, and without delimiters, the receiver cannot identify frame boundaries.

**COBS solution:** COBS encodes the payload such that the 0x00 byte never appears in the encoded data. Frame boundaries are signaled by 0x00 delimiters. If a noise-induced 0x00 appears within a frame, the decoder will detect a CRC mismatch and discard the frame — a single-bit error cannot cause frame boundary confusion.

**CRC-16 solution:** The CCITT-FALSE polynomial (0x1021) provides error detection with a birthday-bound 50% collision probability at 303 messages and an undetected error rate of <10⁻¹⁰ under a bit error rate of 10⁻⁷. This is sufficient for marine environments where RS-422's differential signaling provides an inherent raw BER of <10⁻¹².

**Co-design synergy:** COBS + CRC-16 + RS-422 together provide:
1. Unambiguous frame boundaries (COBS 0x00 delimiters)
2. Burst error detection up to 16 bits (CRC-16 Hamming distance = 4)
3. Noise immunity to ±7V common-mode interference (RS-422 differential)
4. Self-synchronizing decoder (any 0x00 resets frame detection — recovers from any length of corruption)

**Related articles:** [[Wire Protocol Specification|specs/protocol/wire_protocol_spec.md]], [[embedded_and_realtime_systems|Embedded and Real-Time Systems — Section 6]], [[distributed_systems|Distributed Systems]]

---

## 7. Power System Design

### 7.1 Power Budget Analysis per Component

A comprehensive power budget is essential for battery-powered autonomous systems. The NEXUS reference vessel's power consumption by subsystem:

| Subsystem | Component | Active Power | Sleep Power | Duty Cycle | Average Power |
|-----------|-----------|-------------|------------|------------|---------------|
| Cognitive layer | Jetson Orin Nano Super | 10–15 W | 0.5 W | 80% active, 20% idle | 10.0 W |
| Reflex layer (×2) | ESP32-S3 nodes | 0.5 W each | 0.01 W | 95% active | 0.95 W |
| GPS receiver | u-blox NEO-M8N | 0.15 W | — | 100% | 0.15 W |
| Compass | HMC5883L | 0.01 W | — | 100% | 0.01 W |
| IMU | MPU-6050 | 0.02 W | — | 100% | 0.02 W |
| Barometer | BME280 | 0.003 W | — | 100% | 0.003 W |
| Display | OLED 128×64 | 0.1 W | 0 W | 20% on | 0.02 W |
| Navigation lights | LED array | 5 W | — | Night: 100%, Day: 0% | 2.5 W (avg) |
| Rudder actuator | Hydraulic solenoid | 12 W (active) | 0 W | 5% duty | 0.6 W |
| Horn | Piezo buzzer | 2 W | 0 W | <1% | 0.02 W |
| RS-422 transceivers | 2× THVD1500 | 0.06 W | — | 100% | 0.06 W |
| Buck converters | 3× TPS563200 | 0.3 W (loss) | — | 100% | 0.3 W |
| **Total** | | | | | **~14.6 W** |

**Battery sizing calculation:** For 8 hours of operation at 14.6 W average:
- Energy required: 14.6 W × 8 h = 116.8 Wh
- With 80% depth-of-discharge (LiFePO4): 116.8 / 0.80 = 146 Wh
- LiFePO4 cell voltage: 3.2 V nominal (12.8 V for 4S pack)
- Battery capacity: 146 Wh / 12.8 V = 11.4 Ah → **12 Ah, 12.8V LiFePO4 battery pack**

### 7.2 Battery Selection: LiPo, LiFePO4, Lead-Acid

| Chemistry | Energy Density | Cycle Life | Voltage/cell | Safety | Cost | NEXUS Suitability |
|-----------|---------------|------------|--------------|--------|------|------------------|
| LiPo | 150–200 Wh/kg | 300–500 cycles | 3.7 V | Moderate (thermal runaway risk) | $/Wh | High energy but safety concern |
| **LiFePO4** | **90–120 Wh/kg** | **2,000–5,000 cycles** | **3.2 V** | **High (no thermal runaway)** | **$/Wh** | **Best for marine: safe, long-lived** |
| Lead-acid | 30–50 Wh/kg | 200–300 cycles | 2.0 V | High (mature chemistry) | Low | Heavy, short-lived but cheap |
| NiMH | 60–120 Wh/kg | 300–500 cycles | 1.2 V | Moderate | Moderate | Acceptable but heavy |

**NEXUS recommendation:** LiFePO4 (Lithium Iron Phosphate) for marine deployment. Advantages:
- Inherent thermal stability: does not ignite or explode under overcharge, overdischarge, or mechanical damage
- 3,000+ cycle life: amortized cost is lower than lead-acid over vessel lifetime
- Flat discharge curve: 3.2 V nominal, 3.4 V charged, 2.8 V depleted — voltage indicates state-of-charge accurately
- Wide operating temperature: -20°C to +60°C — suitable for marine environments
- High discharge rate: 1C continuous, 3C burst — handles actuator current spikes

### 7.3 Power Distribution: Buck Converters, LDOs, PMICs

The NEXUS power distribution architecture:

```
12.8V LiFePO4 Battery (12 Ah)
    │
    ├── [Polyfuse 20A] ── Kill Switch (NC) ── 12V Actuator Bus
    │       ├── Rudder solenoid driver
    │       ├── Navigation lights
    │       └── Horn
    │
    ├── [Buck: 12V→5V, 3A] ── TPS563200 ── 5V Bus
    │       ├── Jetson Orin Nano (5V input, USB-C PD negotiation)
    │       └── RS-422 transceivers (3.3V via internal LDO)
    │
    └── [Buck: 12V→3.3V, 1A] ── TPS563200 ── 3.3V Bus
            ├── ESP32-S3 nodes (×2)
            ├── I2C sensors (3.3V pull-ups)
            ├── GPS receiver
            └── MOSFET gate drivers
```

**Co-design notes:**

- The Jetson Orin Nano requires USB-C Power Delivery negotiation for 5V/3A input. The TPS563200 buck converter provides 5V output, but a USB PD controller (e.g., FUSB302) is needed to negotiate the correct power profile. Alternatively, the Jetson can be powered directly from a 12V battery via its barrel jack with an internal regulator.

- The 3.3V bus for ESP32-S3 nodes must be low-noise: the ESP32-S3's ADC is sensitive to supply noise (±5 LSB at 12-bit resolution). A dedicated LDO (e.g., AMS1117-3.3) with decoupling capacitors (100 nF + 10 µF at each ESP32-S3) is recommended in addition to the main buck converter.

- Polyfuses provide hardware overcurrent protection without software dependency. The 20A main polyfuse protects the battery from short circuits, while per-channel polyfuses (5 A, 2 A) protect individual actuator circuits.

### 7.4 Sleep Modes and Duty Cycling

The ESP32-S3 supports multiple sleep modes, enabling power optimization for battery-constrained scenarios:

| Mode | Power | Wake-up Time | RAM Retained | Use Case |
|------|-------|-------------|-------------|----------|
| Active (240 MHz) | 240 mA | — | All | Normal operation |
| Modem Sleep | 20 mA | 1–3 ms | All | WiFi sleep between beacons |
| Light Sleep | 0.8 mA | 10–50 µs | All (SRAM + registers) | Inter-tick idle |
| Deep Sleep | 10 µA | 200–500 ms | RTC only (8 KB) | Extended standby |

**NEXUS duty cycling strategy:**

- **Reflex layer (ESP32-S3):** Does NOT use sleep modes during normal operation. The 6 FreeRTOS tasks run continuously at their configured rates (10–1000 Hz). Sleep would introduce unacceptable latency in the control loop. However, the ESP32-S3's DVFS (Dynamic Voltage and Frequency Scaling) is not used — it runs at a fixed 240 MHz for deterministic timing.

- **Cognitive layer (Jetson):** Uses NVIDIA's NV Power Mode framework to dynamically adjust clock frequencies and GPU power:
  - MAXN mode: 15 W, full performance (used during AI inference)
  - 15W mode: 15 W, full clocks (used during active navigation)
  - 10W mode: 10 W, reduced GPU clocks (used during cruising)
  - 7W mode: 7 W, minimum performance (used during idle)
  - The NEXUS firmware automatically selects power mode based on workload: MAXN for reflex synthesis, 10W for normal operation, 7W for standby.

### 7.5 NEXUS's Power Budget Breakdown

Summarizing NEXUS's power architecture as a pie chart:

```
Jetson Orin Nano:  68.5%  (10.0 W / 14.6 W total)
ESP32-S3 nodes:     6.5%  (0.95 W)
Navigation lights:  17.1% (2.5 W)
Actuators:          4.2%  (0.62 W)
Sensors:            0.1%  (0.18 W)
Power conversion:   2.1%  (0.30 W)
Communication:      0.4%  (0.06 W)
Other:              1.1%  (0.16 W)
```

The Jetson Orin Nano dominates the power budget at 68.5%. This is why the Jetson's DVFS capability is so critical — reducing the Jetson from 15 W to 7 W saves 8 W, which extends battery life from 8 hours to 13.2 hours. The ESP32-S3 nodes at 0.95 W total are negligible.

**Optimization opportunity:** If the Jetson is not required for a particular mission (e.g., short-range operation with pre-programmed reflexes only), removing it reduces total power to 4.6 W — more than tripling battery life to 25 hours. This is the NEXUS architecture's graceful degradation capability: the ESP32-S3 nodes can operate autonomously using local reflex programs when the Jetson is unavailable.

---

## 8. Thermal Design

### 8.1 Thermal Resistance Analysis

Thermal management is a critical co-design concern for the Jetson Orin Nano, which dissipates 10–15 W in a small form factor (70 mm × 45 mm module).

**Thermal resistance model:**

```
T_junction = T_ambient + (P_dissipated × θ_ja)

Where:
  T_junction = Junction temperature (must be < 100°C for reliability)
  T_ambient = Ambient temperature (marine: -10°C to +55°C)
  P_dissipated = Power dissipation (10 W typical)
  θ_ja = Junction-to-ambient thermal resistance (°C/W)
```

For the Jetson Orin Nano in a passive cooling configuration (heatsink only, no fan):
- θ_ja (heatsink) ≈ 8°C/W (typical aluminum heatsink, 50 mm × 50 mm × 20 mm fins)
- T_junction = 55°C + (10 W × 8°C/W) = 55°C + 80°C = 135°C → EXCEEDS LIMIT

For the Jetson Orin Nano with active cooling (heatsink + fan):
- θ_ja (heatsink + forced air) ≈ 3°C/W
- T_junction = 55°C + (10 W × 3°C/W) = 55°C + 30°C = 85°C → WITHIN LIMIT

### 8.2 Passive vs. Active Cooling

| Approach | θ_ja | T_junction (at 10W, 40°C ambient) | Pros | Cons |
|----------|------|------------------------------------|------|------|
| No heatsink | 30°C/W | 340°C — FAIL | Cheap, simple | Fatal — junction destruction |
| Passive heatsink | 8°C/W | 120°C — MARGINAL | Silent, no moving parts | Close to limit, degrades in high ambient |
| **Heatsink + fan** | **3°C/W** | **70°C — PASS** | **Reliable temperature margin** | **Fan noise, power consumption (+0.5W), maintenance** |
| Heatsink + blower | 1.5°C/W | 55°C — IDEAL | Large margin | Loud, complex, expensive |

**NEXUS design decision:** Active cooling with a heatsink + 40 mm fan, providing θ_ja ≈ 3°C/W. The fan speed is controlled by the Jetson's internal thermal management, which activates the fan at 50°C and increases speed linearly until the 69°C throttle threshold.

### 8.3 Thermal Throttling Impact on Performance

The Jetson Orin Nano's thermal management system applies throttling in stages:

| Temperature | Action | Performance Impact |
|-------------|--------|-------------------|
| <50°C | Fan off | 100% performance |
| 50°C | Fan on (low speed) | 100% performance |
| 55°C | Fan on (medium speed) | 100% performance |
| 60°C | Fan on (high speed) | 100% performance |
| 69°C | CPU/GPU clock reduction begins | 90% → 70% → 50% performance |
| 85°C | Critical throttle | 30% performance |
| 100°C | Thermal shutdown | 0% performance (system halt) |

**Co-design impact:** When the Jetson throttles at 69°C, AI inference latency increases. The Qwen2.5-Coder-7B model, which generates ~17 tokens/second at full speed, may drop to ~12 tokens/second at 90% performance and ~8 tokens/second at 50% performance. For reflex synthesis (which takes ~29 seconds at full speed), throttling adds ~6–15 seconds. This is acceptable because reflex synthesis is not a real-time operation — it occurs in the background while the ESP32-S3 continues executing current reflex programs.

However, if throttling occurs during **navigation AI inference** (which must complete within 100–500 ms), the latency increase could be safety-critical. The NEXUS firmware monitors the Jetson's temperature via the heartbeat protocol and switches to reflex-only mode (ESP32-S3 autonomous control) when the Jetson's temperature exceeds 65°C — providing a 4°C safety margin before throttling begins.

### 8.4 NEXUS: Managing Jetson at 69°C

NEXUS's thermal management strategy:

1. **Prevention.** The Jetson is mounted in a ventilated enclosure with a 40 mm fan. The heatsink is sized for 10 W dissipation at 40°C ambient with 29°C margin (T_junction = 69°C at 40°C ambient).

2. **Detection.** The Jetson reports its temperature in the heartbeat message. The ESP32-S3 safety supervisor monitors this field and transitions to DEGRADED mode if temperature exceeds 65°C for >10 seconds.

3. **Mitigation.** In DEGRADED mode, the Jetson reduces its workload: disables non-essential AI models, reduces camera frame rate, and limits inference frequency. This reduces power dissipation from 10 W to ~7 W, allowing the temperature to decrease.

4. **Fallback.** If temperature exceeds 85°C, the ESP32-S3 enters SAFE_STATE and operates on reflex programs only. The Jetson continues running but its AI outputs are ignored until temperature returns to normal.

5. **Hardware protection.** The Jetson's internal thermal sensor triggers hardware shutdown at 100°C. This is a last-resort protection that the software layers should never allow to activate.

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems — Section 8]], [[Safety System Specification|specs/safety/safety_system_spec.md]]

---

## 9. Mechanical Integration

### 9.1 PCB Design for EMC

Electromagnetic compatibility (EMC) is a critical concern for marine autonomous systems, where the vessel's metal hull, engine alternator, and VHF radio create a hostile electromagnetic environment.

**NEXUS PCB design EMC guidelines:**

- **Ground plane:** Solid copper ground plane on Layer 2 of a 4-layer PCB. All signal returns route to this plane. The ground plane provides low-impedance return paths for high-frequency currents, reducing radiated emissions.

- **Power plane:** Solid copper power plane (3.3V or 5V) on Layer 3. Decoupling capacitors (100 nF ceramic) placed within 2 mm of every IC power pin.

- **Signal routing:** High-speed signals (UART at 921,600 baud, SPI at 80 MHz) routed as differential pairs with controlled impedance (100 Ω for RS-422, 50 Ω for SPI). Minimum trace spacing of 3× trace width from unrelated signals.

- **I2C bus protection:** TVS diodes (e.g., TPD4E05U06) on SDA and SCL lines near the connector. Series resistors (100 Ω) on SDA/SCL to limit fault current. Pull-up resistors on the ESP32-S3 side of the bus.

- **Connector shielding:** RJ-45 connectors with shield drain connection to chassis ground through 100 nF capacitor (prevents ground loops while providing EMI shielding).

- **Crystal placement:** 40 MHz crystal for ESP32-S3 placed within 2 mm of the XTAL pins, with ground plane cutout underneath. Load capacitors (12 pF) placed adjacent to the crystal pads.

### 9.2 Connector Selection: Marine-Grade IP67+

Marine environments demand connectors that are waterproof, corrosion-resistant, and vibration-tolerant. NEXUS's connector specification:

| Connector | Application | Rating | Part Example |
|-----------|-------------|--------|-------------|
| RJ-45 (IP67) | RS-422 link, Ethernet | IP67, 1000 mating cycles | Amphenol RJHSE-5080 |
| M12 (5-pin) | I2C sensor bus | IP67, IP68, 100 mating cycles | Molex 105317-0010 |
| M12 (8-pin) | Power input/output | IP67, 100 A max | TE Connectivity |
| USB-C (IP67) | Jetson programming | IP67 | Amphenol S5B-PB |
| DB-9 (marine) | NMEA 0183 instruments | IP67 | Bulgin PX0430 |
| Terminal block | Power distribution | IP20 (inside enclosure) | Wago 221 series |
| Kill switch | Emergency stop | IP67, EN ISO 13850 | Schneider Electric XB4 |

**Co-design note:** All external connectors use **circular (M12) or panel-mount (RJ-45 with IP67 shell)** designs, not board-mount headers. This is because the PCB must be enclosed in a sealed enclosure, and the connectors must penetrate the enclosure wall while maintaining the IP67 seal.

### 9.3 Vibration Resistance

Marine vessels experience vibration from the engine, propeller, and wave impact. Vibration can cause:
- **Solder joint fatigue** (especially on heavy components like inductors, electrolytic capacitors)
- **Connector contact degradation** (intermittent connections)
- **Crystal oscillator frequency shifts** (causing UART baud rate errors)
- **PCB delamination** (in multi-layer boards)

**NEXUS vibration mitigation:**
- **Conformal coating:** The PCB is coated with HumiSeal 1B31 (acrylic conformal coating) to protect against moisture and corrosion.
- **Component selection:** SMD components (0805 or larger) instead of through-hole where possible. Heavy components (inductors, capacitors >470 µF) secured with silicone adhesive.
- **Connector locking:** All M12 connectors have threaded locking rings. RJ-45 connectors use latching tabs.
- **PCB mounting:** Four-corner standoffs with silicone vibration isolators between the PCB and the enclosure.
- **Wire routing:** External wires secured with cable ties and adhesive-lined heat shrink at every strain point. No wires longer than 300 mm without a strain relief.

### 9.4 NEXUS's Marine Environment Challenges

The marine environment presents five primary challenges for electronic systems:

**1. Salt spray corrosion.** Salt water and salt-laden air corrode exposed metal surfaces. Mitigation: IP67-sealed enclosures, conformal coating on PCBs, stainless steel or tin-plated connectors, sacrificial zinc anodes on the vessel hull.

**2. Humidity and condensation.** Temperature changes cause condensation inside enclosures, leading to water droplets on the PCB. Mitigation: desiccant packs inside enclosures, drain holes at the lowest point, conformal coating (prevents corrosion even if condensation occurs), heated enclosures (maintain temperature above dew point — power-intensive, used only for critical electronics).

**3. Vibration.** Engine and propeller vibration causes mechanical fatigue. Mitigation: vibration isolators, silicone-secured heavy components, strain-relieved wiring.

**4. UV exposure.** Sunlight degrades plastics and cable insulation. Mitigation: UV-resistant enclosures (polycarbonate or marine-grade fiberglass), UV-stabilized cable jackets (PUR or TPE, not PVC).

**5. Electromagnetic interference.** Engine alternators, VHF radios, and lightning produce strong EMI. Mitigation: shielded enclosures (aluminum or galvanized steel), filtered power inputs, differential signaling for all communication links, EMC-compliant PCB layout.

**Related articles:** [[marine_autonomous_systems|Marine Autonomous Systems]], [[Safety System Specification|specs/safety/safety_system_spec.md]]

---

## 10. Safety Hardware

### 10.1 Hardware Watchdog: MAX6818 with 0x55/0xAA Pattern

The MAX6818 is an external supervisor IC that provides a software-independent reset mechanism. It is the cornerstone of NEXUS's Tier 1 safety — the only safety mechanism that operates regardless of firmware state.

**How it works:**

1. The MAX6818's WDI (Watchdog Input) pin must be toggled (LOW→HIGH or HIGH→LOW) at least once every 1.0 seconds.
2. If the WDI pin is not toggled within 1.0 seconds, the MAX6818 asserts its RST/WDO (Reset/Watchdog Output) pin LOW for 140 ms minimum.
3. The RST pin is hardwired to the ESP32-S3's EN (reset) pin, causing a full processor reset.

**The 0x55/0xAA alternating pattern:**

NEXUS uses a sophisticated kick pattern rather than a simple periodic toggle:

```
Odd kicks:  GPIO → LOW → HIGH  (0x55 pattern: 01010101)
Even kicks: GPIO → HIGH → LOW  (0xAA pattern: 10101010)
```

This pattern detects two failure modes that a simple toggle misses:
- **Stuck-at-0 fault:** The GPIO is held LOW by a firmware bug or hardware latch-up. The MAX6818 sees no edge (LOW→HIGH) and times out.
- **Stuck-at-1 fault:** The GPIO is held HIGH. The MAX6818 sees no edge (HIGH→LOW) and times out.

A simple periodic toggle (LOW→HIGH→LOW→HIGH...) would not detect a stuck-at fault where the GPIO alternates but the firmware is otherwise non-functional (e.g., stuck in a loop that happens to toggle the GPIO as a side effect).

**Kick interval:** 200 ms (5× per second), providing a 5× safety margin below the 1.0 s timeout. The safety_watchdog task (FreeRTOS priority 23) performs the kick. If this task misses a kick, the MAX6818 will reset the system within 1.0 s.

### 10.2 Emergency Stop Circuit: Redundant MOSFETs and Pull-Downs

The E-Stop circuit is a pure hardware design that physically interrupts power to all actuators:

```
+12V Battery ──[Polyfuse 20A]── Kill Switch (NC) ── +12V Actuator Bus
                                            │
                                    ┌───────────────┤ Sense Wire (separate routing)
                                    │  10kΩ pull-up │
                                    │  to 3.3V       │
                                    └───────┬───────┘
                                            │
                                      ESP32-S3 GPIO
                                    (INPUT, FALLING_EDGE ISR)
```

**Redundancy in the MOSFET gate drive:**
Each actuator output uses a gate pull-down resistor (10 kΩ) to ensure the MOSFET is OFF by default. If the ESP32-S3 resets (MAX6818 timeout, brownout, firmware crash), all GPIO pins go high-impedance (input mode), and the pull-down resistors hold all MOSFETs OFF. This is a hardware guarantee, not a software one — the pull-down resistors are always present regardless of firmware state.

**Dual-path redundancy:**
1. Primary: Kill switch opens → power physically interrupted → actuators de-energized
2. Backup: Kill switch opens → sense GPIO detects → E-Stop ISR → software drives outputs safe → MOSFETs OFF

If the primary path fails (kill switch contact welds), the backup path still works (provided the sense wire is intact). If the sense wire fails, the primary path still works (provided the kill switch is intact. If both fail simultaneously, the MAX6818 watchdog will eventually reset the ESP32-S3, and the pull-down resistors will drive all outputs OFF — a third independent safety path.

### 10.3 Current Sensing and Overcurrent Protection

NEXUS implements overcurrent protection at two levels, as documented in the [[Safety System Specification|specs/safety/safety_system_spec.md]]:

**Hardware level (Tier 1):** Polyfuses (PTC) in series with each actuator channel. Passive, non-resettable within the fault window, self-resetting after cooling (<30 s). Trip at 2× nominal current. Provide last-resort protection if the active monitoring system fails.

**Firmware level (Tier 2/3):** INA219 current sensors on monitored channels. The INA219's ALERT pin is connected to an ESP32-S3 GPIO (interrupt). When current exceeds the configurable threshold for 100 ms (accounting for inrush current), the ISR immediately disables the output and logs a CRITICAL safety event.

**Detection parameters:**

| Channel Type | Threshold | Detection Window | Inrush Allowance |
|-------------|-----------|-----------------|-----------------|
| Solenoid (hydraulic) | 4,000 mA | 100 ms sustained | 200 ms, 2× threshold |
| Motor (PWM) | 5,000 mA | 100 ms sustained | 200 ms, 2× threshold |
| Relay | 2,000 mA | 100 ms sustained | 200 ms, 2× threshold |
| General purpose | 500 mA | 100 ms sustained | 200 ms, 2× threshold |

### 10.4 Communication Loss Detection: Heartbeat Timeout

The heartbeat protocol provides a software-level mechanism to detect Jetson failure:

| Parameter | Value |
|-----------|-------|
| Transmission interval | 100 ms (10 Hz) |
| Degraded threshold | 5 missed (500 ms) |
| Safe-state threshold | 10 missed (1,000 ms) |
| Resume requirement | 3 consecutive good heartbeats |

**Escalation sequence:**
```
HEALTHY → (5 missed, 500ms) → DEGRADED → (5 more missed, 1000ms total) → SAFE_STATE
```

In **DEGRADED mode**, the ESP32-S3 continues operating local reflex programs but disables Jetson-dependent features (AI inference, cloud connectivity, new commands). In **SAFE_STATE**, all actuators are driven to their safe positions and the system waits for Jetson reconnection or manual intervention.

**Co-design note:** The heartbeat timeout values (500 ms degraded, 1000 ms safe-state) were chosen to balance responsiveness against false-positive tolerance. The Jetson's heartbeat is generated by a dedicated process with real-time priority, ensuring it fires within ±10 ms of the 100 ms interval. The ESP32-S3's UART ISR timestamps each heartbeat arrival, and the safety supervisor compares inter-arrival times against the expected 80–120 ms window.

### 10.5 NEXUS's Four-Tier Safety: Hardware Design Decisions

The four-tier safety architecture is documented in full in the [[Safety System Specification|specs/safety/safety_system_spec.md]] and summarized here with emphasis on the hardware decisions:

| Tier | Mechanism | Response Time | Authority | Hardware Dependencies |
|------|-----------|--------------|-----------|---------------------|
| 1: Hardware Interlock | Kill switch, polyfuses, pull-down resistors, flyback diodes, MAX6818 WDT | <1 ms | ABSOLUTE | Kill switch (NC contact), polyfuses (PTC), 10 kΩ pull-downs, MAX6818 supervisor IC, 1N4007 flyback diodes |
| 2: Firmware Safety Guard | E-Stop ISR, overcurrent ISR, output safe-state driver | <10 ms | Overrides all software | INA219 current sensors, GPIO interrupt configuration, ISR code in IRAM |
| 3: Supervisory Task | Safety state machine, heartbeat monitor, task watchdog, solenoid timeout | <100 ms | Can override application | FreeRTOS timer, heartbeat UART, task check-in API |
| 4: Application Control | PID loops, reflexes, AI inference | <10 ms | Lowest | VM bytecode, PID state, Jetson AI pipeline |

**Key hardware design decision: Tier independence.** Each tier operates independently of the others. Tier 1 does not depend on any software. Tier 2 does not depend on the application (it uses ISRs, not FreeRTOS tasks). Tier 3 does not depend on the application's correctness (it monitors task health, not task output). This independence is achieved by:
- Physical separation of the kill switch power path from the sense wire
- Dedicated GPIO pins for safety functions (not shared with application I/O)
- ISR code placed in IRAM (not in flash, which could be corrupted)
- Separate FreeRTOS tasks for safety (not mixing safety and application code)

**Related articles:** [[Safety System Specification|specs/safety/safety_system_spec.md]], [[Safety Policy|specs/safety/safety_policy.json]], [[embedded_and_realtime_systems|Embedded and Real-Time Systems — Section 10]]

---

## 11. Design Trade-off Analysis

### 11.1 The Quadrilemma: Performance vs. Power vs. Cost vs. Safety

Autonomous system design is governed by a four-way trade-off that cannot be simultaneously optimized:

```
          Performance
              ▲
             /|\
            / | \
           /  |  \
          /   |   \     Safety (reliability, certification)
         /    |    \
        /     |     \
       /      |      \
      ────────┼───────► Cost
              |
           Power
```

**NEXUS's quadrilemma resolution:**

| Criterion | NEXUS Priority | Decision | Trade-off Accepted |
|-----------|---------------|----------|-------------------|
| Performance | Medium-High | Jetson Orin Nano Super (67 TOPS), ESP32-S3 (240 MHz) | Power: 14.6 W total. Not the most powerful possible (AGX Orin: 275 TOPS) but sufficient for vessel AI workload. |
| Power | Medium | LiFePO4 battery (12 Ah, 146 Wh), DVFS on Jetson | Performance: 10 W operating point limits AI throughput. Not the lowest power possible (single ESP32: 0.5 W) but enables cognitive capabilities. |
| Cost | Medium | $257 per node (Jetson $249 + ESP32-S3 × 2 at $8), ~$500 total vessel electronics | Performance: 3× Jetson cluster ($747) is cheaper than 1× AGX Orin ($1,999) for equivalent AI capability with redundancy. |
| Safety | **Highest** | Four-tier safety, MAX6818 WDT, kill switch, polyfuses, INA219 | Cost: Safety hardware adds ~$20 per node. Performance: Safety checks add ~1% CPU overhead. Power: INA219 sensors add 10 mW per channel. |

### 11.2 When to Use FPGA vs. MCU vs. MPU

The processor selection decision depends on the workload's timing requirements, computational complexity, and development constraints:

| Scenario | Optimal Processor | Rationale |
|----------|------------------|-----------|
| Sensor polling at 1 kHz, simple control logic | MCU (ESP32-S3) | Deterministic timing, low power, integrated peripherals |
| PID control at 100 Hz with float math | MCU with FPU (STM32H7) or MPU (Jetson with RTOS) | Hardware FPU reduces soft-float overhead from 50× to 1× |
| AI inference (7B parameter model) | MPU with GPU (Jetson Orin Nano) | GPU provides 67 TOPS — impossible on MCU |
| Sensor fusion at 10 kHz with sub-µs latency | FPGA | Parallel hardware logic provides deterministic sub-microsecond response |
| Computer vision (camera processing at 30 FPS) | MPU with GPU (Jetson Orin Nano) | GPU-accelerated image processing; MCU would be 100× too slow |
| Neural network inference on sensor data (TinyML) | MCU with vector extensions (ESP32-S3 INT8 MAC) or FPGA | ESP32-S3's 256-bit vector instructions can run small neural networks |
| Protocol bridging (CAN ↔ UART ↔ Ethernet) | FPGA or MCU with DMA | Both can handle; FPGA provides deterministic latency, MCU provides simpler development |
| Safety PLC (SIL 2+) | FPGA with certified IP cores or MCU with certified RTOS | Both are used in industrial safety applications |

**NEXUS's positioning:** NEXUS uses MCUs for the reflex layer (deterministic real-time control) and MPUs for the cognitive layer (AI inference, planning). FPGAs are not used because NEXUS's timing requirements (100 µs–10 ms) are well within MCU capabilities, and FPGA development cost (tools: $2,000–50,000, expertise: specialized) is disproportionate for a 100-unit production run.

### 11.3 Hardware Safety vs. Software Safety

A fundamental co-design question: when should a safety function be implemented in hardware vs. software?

**Hardware safety advantages:**
- Operates regardless of firmware state (including crashes)
- Faster response (sub-microsecond vs. milliseconds)
- Cannot be disabled by software bugs or malicious code
- Independent verification (hardware can be tested with oscilloscope, not debugger)

**Software safety advantages:**
- More flexible (configurable thresholds, adaptive behavior)
- Cheaper to modify (firmware update vs. PCB redesign)
- Can implement complex logic (state machines, temporal patterns)
- Easier to document and verify (code review vs. schematic review)

**NEXUS's decision framework:**

| Safety Function | Implementation | Rationale |
|----------------|---------------|-----------|
| Kill switch | **Hardware** (physical power interrupt) | Must operate if all software fails |
| Watchdog timeout | **Hardware** (MAX6818 external IC) | Must operate if firmware hangs |
| Overcurrent protection | **Both** (polyfuse + INA219/ISR) | Hardware provides last-resort backup; software provides fast, configurable response |
| Heartbeat monitoring | **Software** (FreeRTOS task) | Complex logic (timing windows, state machine) requires software |
| Actuator rate limiting | **Software** (safety guard API) | Configurable per-actuator thresholds require software |
| Output safe-state | **Both** (pull-down resistors + ISR) | Hardware ensures OFF during reset; software provides controlled transition |
| Sensor stale detection | **Software** (safety supervisor task) | Requires comparison with expected timing, configurable per-sensor |

**Principle:** Every safety-critical function has a hardware backup. If the software implementation fails, the hardware backup provides a (possibly degraded) safety response. No single point of failure can compromise safety.

### 11.4 NEXUS's Specific Trade-offs Documented

| Trade-off | Options Considered | Decision | Rationale |
|-----------|-------------------|----------|-----------|
| ESP32-S3 vs STM32H7 | Better compute (STM32), better wireless (ESP32) | **ESP32-S3** | Integrated WiFi/BLE saves $3–5 per node and eliminates RF design complexity |
| RS-422 vs CAN for inter-board | Simpler (RS-422), standardized (CAN) | **RS-422** | Full-duplex, no arbitration latency, 1024-byte payloads (CAN: 8 bytes) |
| COBS vs HDLC framing | Simpler (COBS), more robust (HDLC) | **COBS** | 0.4% overhead (HDLC: ~20%), self-synchronizing, simpler implementation |
| CRC-16 vs CRC-32 | Better detection (CRC-32), lower overhead (CRC-16) | **CRC-16** | 2-byte overhead (CRC-32: 4 bytes), sufficient for RS-422 BER <10⁻¹² |
| LiFePO4 vs LiPo | Higher energy (LiPo), safer (LiFePO4) | **LiFePO4** | Marine safety: no thermal runaway, 3000+ cycle life, flat discharge curve |
| Active vs passive cooling | Silent (passive), reliable (active) | **Active** | Jetson at 10 W cannot be passively cooled within 100°C junction limit |
| 3× Jetson Nano vs 1× Jetson AGX | Cheaper (3× Nano), more powerful (1× AGX) | **3× Jetson Orin Nano Super** | $747 vs $1,999, 201 TOPS vs 275 TOPS, AND provides redundancy |
| Kill switch sense via GPIO vs ADC | More precise (ADC), simpler (GPIO) | **GPIO** | Digital input with pull-up provides fail-safe default (LOW = kill active) |

---

## 12. Bill of Materials (BOM) for NEXUS Reference Vessel

| Category | Component | Part Number | Quantity | Unit Cost | Total Cost |
|----------|-----------|------------|----------|-----------|------------|
| **Compute** | Jetson Orin Nano Super | 945-13766-0004-100 | 1 | $249.00 | $249.00 |
| | ESP32-S3-WROOM-1-N8R8 | ESP32-S3-WROOM-1-N8R8 | 2 | $7.00 | $14.00 |
| **Memory** | MicroSD card (64 GB, A2) | Samsung EVO Plus | 1 | $12.00 | $12.00 |
| **Sensors** | Compass (HMC5883L) | HMC5883L | 1 | $4.50 | $4.50 |
| | IMU (MPU-6050) | MPU-6050 | 1 | $3.00 | $3.00 |
| | Barometer (BME280) | BME280 | 1 | $5.00 | $5.00 |
| | GPS (u-blox NEO-M8N) | NEO-M8N-0-000 | 1 | $35.00 | $35.00 |
| | Current sensor (INA219) | INA219BIDCNT-R | 2 | $3.50 | $7.00 |
| **Actuators** | Hydraulic solenoid (12V) | Parker 70180 | 1 | $85.00 | $85.00 |
| | MOSFET driver (TC4420) | TC4420EOA | 4 | $3.00 | $12.00 |
| | MOSFET (IRLZ44N) | IRLZ44N | 4 | $1.50 | $6.00 |
| **Communication** | RS-422 transceiver (THVD1500) | THVD1500DGGR | 2 | $2.50 | $5.00 |
| | RJ-45 connector (IP67) | RJHSE-5080 | 2 | $5.00 | $10.00 |
| | RS-422 cable (Cat-6 STP, 5 m) | Belden 2413 | 1 | $8.00 | $8.00 |
| **Power** | LiFePO4 battery (12.8V, 12 Ah) | Bioenno Power BLF-12100A | 1 | $95.00 | $95.00 |
| | Buck converter (12V→5V, 3A) | TPS563200DDA | 1 | $3.50 | $3.50 |
| | Buck converter (12V→3.3V, 1A) | TPS563200DDA | 1 | $3.50 | $3.50 |
| | Polyfuse 5A (MF-R500) | MF-R500 | 4 | $0.50 | $2.00 |
| | Polyfuse 2A (MF-R200) | MF-R200 | 4 | $0.40 | $1.60 |
| | Polyfuse 20A | MF-R2000 | 1 | $2.00 | $2.00 |
| **Safety** | Kill switch (IP67, EN ISO 13850) | XB4BS542 | 1 | $25.00 | $25.00 |
| | Watchdog IC (MAX6818) | MAX6818EUT+T | 1 | $2.50 | $2.50 |
| | TVS diode array (TPD4E05U06) | TPD4E05U06DQAR | 2 | $1.50 | $3.00 |
| | Flyback diodes (1N4007) | 1N4007 | 4 | $0.10 | $0.40 |
| **PCB** | Main controller PCB (4-layer) | Custom | 1 | $15.00 | $15.00 |
| | Sensor expansion PCB (2-layer) | Custom | 1 | $8.00 | $8.00 |
| | Enclosure (IP67, polycarbonate) | Custom | 1 | $30.00 | $30.00 |
| **Cooling** | Heatsink (Jetson, 50×50×20 mm) | Custom | 1 | $5.00 | $5.00 |
| | Fan (40 mm, 12V) | Sunon MF40100VX | 1 | $3.00 | $3.00 |
| **Connectors** | M12 5-pin (sensor bus) | 105317-0010 | 2 | $4.00 | $8.00 |
| | M12 8-pin (power) | — | 2 | $5.00 | $10.00 |
| | Terminal blocks (Wago 221) | 221-412 | 10 | $0.80 | $8.00 |
| **Miscellaneous** | OLED display (128×64, I2C) | SSD1306 | 1 | $4.00 | $4.00 |
| | LEDs, resistors, capacitors | Various | Kit | $5.00 | $5.00 |
| | Cables, wire, heat shrink | Various | Kit | $10.00 | $10.00 |
| **TOTAL** | | | | | **$684.00** |

**Cost breakdown by category:**

| Category | Cost | Percentage |
|-----------|------|-----------|
| Compute (Jetson + ESP32) | $263.00 | 38.5% |
| Power (battery + converters + fuses) | $107.60 | 15.7% |
| Safety (kill switch + watchdog + diodes) | $30.90 | 4.5% |
| Sensors | $54.50 | 8.0% |
| Actuators + drivers | $103.00 | 15.1% |
| Communication | $23.00 | 3.4% |
| PCB + enclosure | $53.00 | 7.7% |
| Cooling | $8.00 | 1.2% |
| Connectors + misc | $41.00 | 6.0% |

The Jetson Orin Nano Super alone accounts for **38.5%** of the total BOM — confirming the earlier analysis that the cognitive layer dominates the cost structure. At a 100-unit production run, the custom PCB cost drops to ~$5 per board (from $15) and the enclosure cost drops to ~$15 (from $30), reducing total BOM to approximately **$630 per vessel**.

---

## 13. Synthesis and Design Principles

The NEXUS platform's hardware-software co-design yields twelve key design principles applicable to any autonomous robotic system:

1. **Design the software for the hardware, not the hardware for the software.** The Reflex VM's 32-opcode ISA was shaped by the Xtensa LX7's pipeline characteristics, not by abstract software engineering considerations.

2. **Every safety function has a hardware backup.** Software monitoring (heartbeat, task watchdog) is complemented by hardware interlocks (kill switch, MAX6818, polyfuses). No single software bug can compromise safety.

3. **Memory is allocated before code is written.** The SRAM budget (6 KB VM, 24 KB stacks, 8 KB DMA, 216 KB free) was determined first; the firmware architecture was designed to fit within it.

4. **Protocol and physical layer are co-selected.** COBS framing was chosen because RS-422 has no frame delimiters. CRC-16 was chosen because its 2-byte overhead is acceptable at 921,600 baud while providing sufficient error detection.

5. **Power determines performance ceiling.** The Jetson's 10 W operating point constrains AI inference speed. DVFS enables graceful adaptation but cannot eliminate the constraint.

6. **Thermal design is a first-class requirement, not an afterthought.** The Jetson's 69°C throttle threshold was factored into the safety state machine (DEGRADED mode at 65°C), not discovered during testing.

7. **Redundancy is cheaper than perfection.** Three $249 Jetson Orin Nano units ($747) provide both 201 TOPS of AI performance AND single-fault tolerance — something a single $1,999 AGX Orin cannot match.

8. **Marine environment dictates every mechanical decision.** IP67 connectors, conformal coating, LiFePO4 batteries, stainless steel fasteners, and UV-stabilized cables are not optional upgrades — they are baseline requirements.

9. **The reflex layer must operate independently.** If the Jetson fails, the ESP32-S3 must continue controlling the vessel using local reflex programs. This independence is achieved by the register file indirection pattern and the heartbeat-triggered graceful degradation.

10. **Determinism is more valuable than performance.** The VM's fixed-cycle-count opcodes, the I/O polling task's register file updates, and the safety state machine's fixed-period checks all prioritize deterministic timing over maximum throughput.

11. **BOM cost is dominated by the cognitive layer.** At $263 out of $684 (38.5%), the compute subsystem is the primary cost driver. Sensor and actuator costs are relatively modest. Cost optimization should focus on the Jetson tier (usage, power management, duty cycling).

12. **Test the kill switch weekly.** The most safety-critical component ($25 kill switch) requires the simplest test (press it and verify actuators stop). The principle: safety mechanisms that are never tested are safety mechanisms that don't work.

**Related articles:** [[embedded_and_realtime_systems|Embedded and Real-Time Systems]], [[marine_autonomous_systems|Marine Autonomous Systems]], [[distributed_systems|Distributed Systems]], [[Safety System Specification|specs/safety/safety_system_spec.md]], [[Wire Protocol Specification|specs/protocol/wire_protocol_spec.md]]

---

## 14. References and Further Reading

1. Henzinger, T. A., & Kirsch, C. M. (2002). "The Embedded and Real-Time Systems Landscape." *ACM Computing Surveys*, 34(3), 333–358.
2. Wolf, W. (2017). *High-Performance Embedded Computing: Applications in Cyber-Physical Systems, Mobile Computing, and IoT.* Morgan Kaufmann.
3. Edwards, S., & Green, T. (2022). "Hardware-Software Co-Design for Autonomous Marine Systems." *IEEE Transactions on Industrial Electronics*, 69(8), 8234–8248.
4. IEC 61508:2010. *Functional Safety of Electrical/Electronic/Programmable Electronic Safety-Related Systems.* International Electrotechnical Commission.
5. ISO 13849-1:2023. *Safety of Machinery — Safety-Related Parts of Control Systems.* International Organization for Standardization.
6. Espressif Systems (2024). *ESP32-S3 Technical Reference Manual.* Version 1.5.
7. NVIDIA (2023). *Jetson Orin Nano Super Product Design Guide.* DG-10948-001.
8. Cheshire, S., & Oppenheimer, P. (1997). "Consistent Overhead Byte Stuffing." *IEEE/ACM Transactions on Networking*, 5(2), 251–258.
9. Liu, C. L., & Layland, J. W. (1973). "Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment." *Journal of the ACM*, 20(1), 46–61.
10. Kopetz, H. (2011). *Real-Time Systems: Design Principles for Distributed Embedded Applications.* Springer.
11. NEXUS Safety Engineering Team (2025). [[Safety System Specification|specs/safety/safety_system_spec.md]]. NEXUS-SS-001 v2.0.0.
12. NEXUS Protocol Team (2025). [[Wire Protocol Specification|specs/protocol/wire_protocol_spec.md]]. NEXUS-PROT-WIRE-001 v2.0.0.
13. NEXUS Firmware Team (2025). [[Reflex Bytecode VM Specification|specs/firmware/reflex_bytecode_vm_spec.md]]. NEXUS-SPEC-VM-001 v1.0.0.
14. NEXUS Memory Architecture Team (2025). [[Memory Map and Partition Specification|specs/firmware/memory_map_and_partitions.md]]. NEXUS-SPEC-MEM-001 v1.0.0.
15. Maxim Integrated (2023). *MAX6818 Ultra-Low-Power Microprocessor Supervisory Circuit Data Sheet.* 19-5683.
16. Texas Instruments (2023). *INA219 Bi-Directional Current/Power Monitor With I2C Interface.* SBOS547D.
17. Espressif Systems (2024). *ESP-IDF Programming Guide.* Version 5.1.
18. FreeRTOS (2023). *FreeRTOS Real Time Kernel — Developer Documentation.* Version 10.5.1.
19. Barr, M. (2003). *Mastering the FreeRTOS Real Time Kernel.* Amazon Web Services.
20. IMO (2023). *Guidelines for the Design and Construction of MASS (Marine Autonomous Surface Ships).* MSC.1/Circ.169.

---

*Document generated for the NEXUS Platform Knowledge Base. This article cross-references [[embedded_and_realtime_systems]] and all NEXUS specification documents. Last updated: 2025.*
