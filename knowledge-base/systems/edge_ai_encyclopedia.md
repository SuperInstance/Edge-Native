# Edge AI and On-Device Machine Learning — Complete Encyclopedia

**Knowledge Base Article — NEXUS Platform Systems**

---

## Table of Contents

1. [What is Edge AI?](#1-what-is-edge-ai)
   - 1.1 [Definition and Core Concepts](#11-definition-and-core-concepts)
   - 1.2 [Motivation: The Four Pillars](#12-motivation-the-four-pillars)
   - 1.3 [The Edge–Cloud Continuum](#13-the-edgecloud-continuum)
2. [Edge Hardware Landscape](#2-edge-hardware-landscape)
   - 2.1 [Microcontroller-Class Devices](#21-microcontroller-class-devices)
   - 2.2 [Single-Board Computers](#22-single-board-computers)
   - 2.3 [Dedicated AI Accelerators](#23-dedicated-ai-accelerators)
   - 2.4 [Comprehensive Chip Comparison Table](#24-comprehensive-chip-comparison-table)
3. [Model Optimization for Edge](#3-model-optimization-for-edge)
   - 3.1 [Quantization](#31-quantization)
   - 3.2 [Pruning](#32-pruning)
   - 3.3 [Knowledge Distillation](#33-knowledge-distillation)
   - 3.4 [Efficient Architecture Design](#34-efficient-architecture-design)
   - 3.5 [Neural Architecture Search (NAS)](#35-neural-architecture-search-nas)
4. [Edge AI Frameworks](#4-edge-ai-frameworks)
   - 4.1 [TensorFlow Lite (TFLite)](#41-tensorflow-lite-tflite)
   - 4.2 [ONNX Runtime Mobile](#42-onnx-runtime-mobile)
   - 4.3 [TensorRT](#43-tensorrt)
   - 4.4 [llama.cpp](#44-llamacpp)
   - 4.5 [Edge Impulse](#45-edge-impulse)
   - 4.6 [TVM and Apache TVM](#46-tvm-and-apache-tvm)
   - 4.7 [Framework Comparison Table](#47-framework-comparison-table)
5. [Edge AI Applications](#5-edge-ai-applications)
   - 5.1 [Computer Vision](#51-computer-vision)
   - 5.2 [Speech and Audio](#52-speech-and-audio)
   - 5.3 [Time-Series and Predictive Maintenance](#53-time-series-and-predictive-maintenance)
   - 5.4 [Robotics and Autonomous Navigation](#54-robotics-and-autonomous-navigation)
   - 5.5 [Natural Language Processing on Edge](#55-natural-language-processing-on-edge)
6. [NEXUS Edge AI Stack Analysis](#6-nexus-edge-ai-stack-analysis)
   - 6.1 [Jetson Orin Nano as Edge AI Platform](#61-jetson-orin-nano-as-edge-ai-platform)
   - 6.2 [Qwen2.5-Coder-7B Quantization Analysis](#62-qwen25-coder-7b-quantization-analysis)
   - 6.3 [Phi-3-mini as Secondary Model](#63-phi-3-mini-as-secondary-model)
   - 6.4 [Memory Budget Analysis](#64-memory-budget-analysis)
   - 6.5 [Whisper for Voice: On-Demand Loading](#65-whisper-for-voice-on-demand-loading)
   - 6.6 [Why NOT TinyML on ESP32?](#66-why-not-tinyml-on-esp32)
7. [Performance Benchmarking](#7-performance-benchmarking)
   - 7.1 [Inference Latency vs. Model Size Tradeoff](#71-inference-latency-vs-model-size-tradeoff)
   - 7.2 [Power Consumption Analysis](#72-power-consumption-analysis)
   - 7.3 [Thermal Management at Sustained Inference](#73-thermal-management-at-sustained-inference)
   - 7.4 [Batch Size Considerations for Edge](#74-batch-size-considerations-for-edge)
8. [The Future of Edge AI](#8-the-future-of-edge-ai)
   - 8.1 [Scaling Laws for Edge Models](#81-scaling-laws-for-edge-models)
   - 8.2 [Mixture of Experts (MoE) for Edge](#82-mixture-of-experts-moe-for-edge)
   - 8.3 [Neuromorphic Computing](#83-neuromorphic-computing)
   - 8.4 [Analog and In-Memory Computing](#84-analog-and-in-memory-computing)
   - 8.5 [Photonic Computing](#85-photonic-computing)
9. [Edge AI Safety](#9-edge-ai-safety)
   - 9.1 [Adversarial Robustness on Edge](#91-adversarial-robustness-on-edge)
   - 9.2 [Model Integrity Verification](#92-model-integrity-verification)
   - 9.3 [OTA Model Update Safety](#93-ota-model-update-safety)
   - 9.4 [Certification of AI on Edge](#94-certification-of-ai-on-edge)
10. [Edge AI in Autonomous Systems](#10-edge-ai-in-autonomous-systems)
    - 10.1 [Latency Requirements for Control](#101-latency-requirements-for-control)
    - 10.2 [Sensor Fusion at Edge](#102-sensor-fusion-at-edge)
    - 10.3 [Real-Time Inference Scheduling](#103-real-time-inference-scheduling)
    - 10.4 [Failover: When Edge AI Fails](#104-failover-when-edge-ai-fails)
11. [References and Further Reading](#11-references-and-further-reading)

---

## 1. What is Edge AI?

### 1.1 Definition and Core Concepts

**Edge AI** (also called **on-device AI**, **edge machine learning**, or **embedded AI**) refers to the deployment of machine learning models and AI inference workloads directly on devices at the network edge — that is, on or near the data source — rather than routing data to centralized cloud infrastructure for processing. The "edge" in edge computing denotes the physical or logical location where data is generated and consumed: sensors, cameras, microphones, industrial controllers, autonomous vehicles, smartphones, robots, and IoT devices.

Formally, edge AI is characterized by three properties:

1. **Proximity of computation to data generation.** The model executes on the same device (or a device within one network hop) that captures the input data. No round-trip to a remote data center is required for inference.

2. **Resource-constrained execution.** Edge AI models operate under strict constraints in at least two of the following dimensions: compute (TOPS or GFLOPS), memory (SRAM, DRAM, or flash measured in KB to GB), power (milliwatts to tens of watts), and thermal envelope (passive cooling or small heatsinks).

3. **Functional independence from the cloud.** While edge AI systems may periodically synchronize with cloud services for model updates, training data aggregation, or fallback processing, they must perform their core inference task without a live network connection.

The distinction between edge AI and cloud AI is not merely about deployment location — it represents a fundamentally different engineering philosophy. Cloud AI optimizes for maximum model accuracy with essentially unlimited compute resources (GPU clusters with hundreds of gigabytes of HBM memory). Edge AI optimizes for the Pareto frontier of accuracy, latency, power consumption, and cost — a multi-objective optimization problem where the constraints are hardware-defined and immutable.

Edge AI intersects with several related fields:

- **TinyML**: A subfield of edge AI focused on machine learning on microcontrollers (MCUs) with less than 1 MB of SRAM and typically less than 256 KB of flash for model storage. TinyML targets applications like wake word detection, anomaly detection, and gesture recognition.

- **Embedded AI**: Machine learning integrated into embedded systems, ranging from MCU-class devices to application processors. This is the broadest term and encompasses both TinyML and higher-performance edge AI.

- **On-device AI**: A term popularized by the mobile industry (particularly Apple and Qualcomm) to describe AI inference running locally on smartphones, tablets, and wearables.

The NEXUS platform, as described in [[embedded_and_realtime_systems]], occupies a specific position on the edge AI spectrum: its ESP32-S3 nodes operate as real-time sensor controllers and actuator drivers (TinyML-adjacent but not running ML inference), while its Jetson Orin Nano nodes serve as the primary edge AI compute platform, running large language models (LLMs) and computer vision models with GPU-accelerated inference.

### 1.2 Motivation: The Four Pillars

The migration of AI workloads from cloud to edge is driven by four technical imperatives, each of which is critical for autonomous systems like NEXUS:

#### Latency

Cloud inference introduces network latency that is unacceptable for real-time control systems. Even under ideal conditions (5G with <10 ms one-way latency, geographically proximate data center), the round-trip time for a single inference request can range from 20–100 ms. Under realistic maritime conditions (satellite connectivity with 600–1200 ms round-trip, intermittent cellular, or no connectivity at all), cloud-based AI is simply inoperable.

For autonomous systems, the latency requirements span multiple tiers:

| Tier | Application | Maximum Latency | Cloud Viability |
|------|-------------|-----------------|-----------------|
| Reflex | Collision avoidance, kill switch | < 1 ms | Impossible |
| Control | PID loop, heading correction | 1–10 ms | Marginal (wired) |
| Cognitive | Path planning, reflex synthesis | 100–500 ms | Possible (5G) |
| Analytical | Trend analysis, reporting | 1–60 seconds | Suitable |

The NEXUS platform's [[reflex bytecode VM|specs/firmware/reflex_bytecode_vm_spec.md]] operates at Tier 1 (sub-millisecond) and Tier 2 (1–10 ms), making cloud AI fundamentally unsuitable for its core control loops. Edge AI is not a preference — it is a requirement.

#### Bandwidth

AI workloads generate enormous data volumes. A single 1080p camera at 30 fps produces ~1.5 Gbps of raw video data. A NEXUS vessel with multiple cameras, LIDAR, radar, sonar, IMU, GPS, and environmental sensors can generate 5–20 Gbps of sensor data. Transmitting all of this to the cloud for processing is prohibitively expensive in terms of both bandwidth and cellular data costs.

Edge AI enables **pre-processing and feature extraction at the source**: instead of transmitting raw video frames, the edge device transmits detected objects, semantic labels, or compressed feature vectors. A YOLOv8-nano model running on a Jetson Orin Nano can process 1080p video at 100+ fps, reducing the output to a JSON payload of detected objects — a bandwidth reduction of approximately 100,000:1.

#### Privacy

Edge AI provides inherent data privacy by keeping sensitive data on-device. In maritime applications, onboard camera footage of crew members, passengers, or nearby vessels may contain personal data subject to GDPR. Processing this data on-device and transmitting only anonymized results (object detections, pose estimates without biometric data) significantly reduces the regulatory burden.

For the NEXUS platform, the [[regulatory landscape analysis]] identified that camera and LIDAR data constitute personal data under GDPR. Edge AI enables real-time face masking and person anonymization before any data leaves the vessel, simplifying compliance with the EU AI Act's data governance requirements.

#### Cost

Cloud AI inference at scale is expensive. Running GPT-4 class models costs approximately $0.03–0.06 per 1,000 tokens (input) and $0.06–0.12 per 1,000 tokens (output). A NEXUS vessel that generates 500 reflex synthesis requests per day, each consuming 2,000 tokens, would incur approximately $90–180/month in cloud inference costs alone — before accounting for computer vision, sensor fusion, or NLP workloads.

By deploying Qwen2.5-Coder-7B on-device via [[llama.cpp]], the NEXUS platform pays the hardware cost once (approximately $249 per Jetson Orin Nano module) and executes unlimited inference with no per-query cost. The amortized cost over a 5-year vessel lifetime is less than $1/month per node.

### 1.3 The Edge–Cloud Continuum

Modern edge AI systems do not exist in isolation from the cloud; they operate on a **continuum** that spans from the sensor to the data center, with intelligence distributed across multiple tiers. The NEXUS platform implements a three-tier architecture that maps naturally onto this continuum:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLOUD TIER (Optional)                          │
│  GPT-4o / Claude 3.5 for reflex validation, fleet analytics,      │
│  model training, OTA model distribution                            │
│  Latency: 100–5000 ms | Connectivity: Intermittent                 │
├─────────────────────────────────────────────────────────────────────┤
│                     EDGE TIER (Primary AI)                          │
│  Jetson Orin Nano: Qwen2.5-Coder-7B (Q4_K_M), Phi-3-mini,        │
│  Whisper (on-demand), YOLOv8, sensor fusion                       │
│  Latency: 10–100 ms | Connectivity: Local LAN                     │
├─────────────────────────────────────────────────────────────────────┤
│                     DEVICE TIER (Real-Time)                         │
│  ESP32-S3: Reflex VM, sensor acquisition, actuator control,       │
│  safety supervision, heartbeat protocol                            │
│  Latency: 0.01–1 ms | Connectivity: RS-422, ESP-NOW              │
└─────────────────────────────────────────────────────────────────────┘
```

This tiered architecture ensures graceful degradation: if the cloud is unavailable, the edge continues operating. If the edge fails, the device tier maintains safety-critical control. This is a **defense-in-depth** approach to AI availability, directly analogous to the NEXUS platform's [[four-tier safety architecture|specs/safety/safety_system_spec.md]].

The edge–cloud continuum also enables **federated learning**: each vessel trains or fine-tunes its local model based on its specific operational data, then shares only model weight updates (not raw data) with the fleet. This enables fleet-wide model improvement without compromising individual vessel data privacy — a pattern documented in the [[distributed systems]] knowledge base article.

---

## 2. Edge Hardware Landscape

### 2.1 Microcontroller-Class Devices

Microcontroller-class edge AI devices are characterized by limited memory (typically 256 KB–2 MB SRAM), limited compute (typically 50–600 MHz single or dual-core CPUs without hardware floating point), and ultra-low power consumption (50–500 mW). They are suitable for TinyML workloads: small models (< 1 MB) with low-dimensional inputs and outputs.

#### ESP32-S3

The **Espressif ESP32-S3**, used throughout the NEXUS platform for sensor control and actuator driving, features a dual-core Xtensa LX7 @ 240 MHz with 512 KB SRAM and 8 MB external PSRAM. Its 256-bit vector instructions provide limited AI acceleration for 8-bit integer operations. However, as detailed in [[Section 6.6|#66-why-not-tinyml-on-esp32]], the ESP32-S3 is fundamentally unsuitable for running models larger than approximately 1–2 MB in parameters, which excludes all modern LLMs.

**ESP32-S3 AI capabilities:**

| Feature | Specification |
|---------|---------------|
| Vector instructions | 256-bit SIMD for INT8 operations |
| Peak throughput | ~0.6 TOPS (INT8, estimated) |
| Usable memory for models | ~2 MB (PSRAM, non-DMA) |
| Suitable model size | < 500 KB (SRAM), < 2 MB (PSRAM) |
| Practical applications | Wake word, keyword spotting, anomaly detection |
| Framework support | TensorFlow Lite for Microcontrollers, ESP-DL |

#### STM32H7 Series

The **STMicroelectronics STM32H7** family (H743, H753, H750, H7A3, H7B3) is based on the ARM Cortex-M7 core running at up to 550 MHz with 1 MB SRAM (TCM) and hardware double-precision FPU. The STM32H747 is a dual-core variant with Cortex-M7 + Cortex-M4. These devices are widely used in industrial control, medical devices, and automotive applications.

| Feature | STM32H743 |
|---------|-----------|
| Core | ARM Cortex-M7 @ 550 MHz |
| SRAM | 1 MB (TCM: 512 KB ITCM + 512 KB DTCM) |
| Flash | 2 MB |
| FPU | Double-precision hardware FPU |
| DSP instructions | ARM Cortex-M7 DSP extension |
| AI acceleration | None (software only via CMSIS-NN) |
| Peak throughput | ~2.2 GFLOPS (FP32), ~4.4 GOPS (INT8 via CMSIS-NN) |
| Power | ~350 mW (active) |

#### GreenWaves GAP9

The **GreenWaves Technologies GAP9** is a purpose-built ultra-low-power AI processor for IoT and wearable applications. It features a RISC-V cluster of 9 cores (1 control core + 8 parallel processing cores) running at up to 370 MHz, with 1.2 MB of shared L2 SRAM and hardware support for INT8/INT16 vector operations.

| Feature | GAP9 |
|---------|------|
| Architecture | RISC-V (1 fabric controller + 8 SIMD cores) |
| Clock | Up to 370 MHz |
| SRAM | 1.2 MB L2 + 64 KB L1 per core |
| Flash | External (up to 64 MB) |
| Peak throughput | ~50 GOPS (INT8) |
| Power | 5–50 mW (typical) |
| Standby power | ~1 µW |
| Applications | Keyword spotting, human activity recognition, ECG analysis |

#### Google Coral (Edge TPU)

The **Google Coral** line of products integrates the **Edge TPU** (Tensor Processing Unit) — an ASIC designed by Google specifically for running TensorFlow Lite models with INT8 quantization. The Edge TPU is available in multiple form factors: a USB accelerator dongle, a PCIe M.2 module, a system-on-module (SoM), and a development board.

| Feature | Coral USB Accelerator | Coral Dev Board |
|---------|----------------------|-----------------|
| Edge TPU cores | 1 | 1 |
| Peak throughput | 4 TOPS (INT8) | 4 TOPS (INT8) |
| Power | 2.0 W | 2.0 W (SoC) + 2.5 W (SoM) |
| Interface | USB 3.0 | Direct SoC access |
| Memory | Host-dependent | 1 GB LPDDR4 |
| Connectivity | USB | Wi-Fi, Bluetooth, Ethernet |
| Price | ~$60 | ~$150 |

### 2.2 Single-Board Computers

Single-board computers (SBCs) provide significantly more compute and memory than microcontrollers, typically running full Linux operating systems and supporting GPU-accelerated inference.

#### NVIDIA Jetson Family

The NVIDIA Jetson family, described extensively in [[embedded_and_realtime_systems#26-the-nvidia-jetson-lineage-ai-at-the-edge-2014present]], is the dominant platform for edge AI in robotics and autonomous systems. The current Orin generation provides from 40 to 275 TOPS of INT8 compute:

| Module | GPU | CUDA Cores | Tensor Cores | TOPS (INT8) | Memory | Power | Price |
|--------|-----|------------|--------------|-------------|--------|-------|-------|
| Jetson Orin Nano | Ampere | 1024 | 32 | 40 | 8 GB LPDDR5 | 7–15 W | $249 |
| Jetson Orin Nano Super | Ampere | 1024 | 32 | 67 | 8 GB LPDDR5 | 7–25 W | $249 |
| Jetson Orin NX 16GB | Ampere | 1024 | 32 | 100 | 16 GB LPDDR5 | 10–25 W | $599 |
| Jetson AGX Orin 64GB | Ampere | 2048 | 64 | 275 | 64 GB LPDDR5 | 15–60 W | $1,999 |

The NEXUS platform uses the **Jetson Orin Nano Super** (67 TOPS, 8 GB LPDDR5), which provides sufficient GPU memory to run Qwen2.5-Coder-7B at Q4_K_M quantization (4.2 GB VRAM) alongside the operating system and secondary models.

#### Raspberry Pi 5

The **Raspberry Pi 5** (2023) represents a significant leap in SBC performance with its Broadcom BCM2712 SoC featuring a quad-core ARM Cortex-A76 @ 2.4 GHz and a VideoCore VII GPU. While it lacks dedicated AI acceleration hardware (no Tensor cores, no NPU), its competitive price ($60–$80) and mature ecosystem make it a popular platform for lightweight edge AI workloads.

| Feature | Raspberry Pi 5 | Jetson Orin Nano |
|---------|---------------|------------------|
| CPU | 4× Cortex-A76 @ 2.4 GHz | 6× Cortex-A78AE @ 1.5 GHz |
| GPU | VideoCore VII (no Tensor cores) | Ampere (1024 CUDA + 32 Tensor cores) |
| AI Acceleration | None (software via NCNN/TFLite) | 40–67 TOPS (INT8) |
| Memory | 4 GB / 8 GB LPDDR4X | 8 GB LPDDR5 |
| Power | 3–12 W (typical) | 7–25 W |
| Price | $60–$80 | $249 |
| AI inference (ResNet-50) | ~200 ms (CPU) | ~1.5 ms (GPU) |
| LLM (Phi-2 2.7B Q4) | ~0.8 tok/s (CPU) | ~25 tok/s (GPU) |

#### Coral Dev Board

The **Google Coral Dev Board** integrates an NXP i.MX 8M SoC (4× Cortex-A53 @ 1.5 GHz) with the Edge TPU coprocessor, providing an all-in-one platform for TensorFlow Lite inference with hardware acceleration. It is well-suited for vision workloads (classification, detection, segmentation) but cannot run LLMs due to limited memory (1 GB LPDDR4).

### 2.3 Dedicated AI Accelerators

Dedicated AI accelerators are chips or modules designed exclusively for neural network inference, typically connecting to a host processor via PCIe, USB, or M.2 interfaces.

#### Intel Movidius (Myriad X VPU)

The **Intel Movidius Myriad X** Vision Processing Unit (VPU) was designed for computer vision workloads at ultra-low power. It features a dedicated neural compute engine, 16 programmable SHAVE cores, and hardware support for 16-bit floating-point inference. Originally developed by Movidius (acquired by Intel in 2016), the Myriad X powers the Intel Neural Compute Stick 2.

| Feature | Intel Neural Compute Stick 2 |
|---------|------------------------------|
| Processor | Myriad X VPU |
| Neural compute engine | 1 TOPS (FP16) |
| SHAVE cores | 16 |
| Memory | 512 MB LPDDR4 |
| Power | 1.5 W |
| Interface | USB 3.0 |
| Framework support | OpenVINO |
| Price | ~$70 (discontinued, replaced by Intel Arc NUC) |

#### Hailo-8

The **Hailo-8** is an AI accelerator from Israeli startup Hailo Technologies, delivering 26 TOPS of INT8 compute at just 2.5 W — an exceptional performance-per-watt ratio. The Hailo-8 uses a proprietary network-on-chip architecture with 256 MAC (multiply-accumulate) units organized for efficient sparse model execution.

| Feature | Hailo-8 | Hailo-8L |
|---------|---------|----------|
| Peak throughput | 26 TOPS (INT8) | 13 TOPS (INT8) |
| Power | 2.5 W | 1.5 W |
| Efficiency | 10.4 TOPS/W | 8.7 TOPS/W |
| Memory | Host-dependent | Host-dependent |
| Interface | PCIe 2.1 / M.2 | PCIe 2.1 / M.2 |
| Framework support | Hailo Dataflow Compiler, TFLite, ONNX |
| Price | ~$100 (module) | ~$70 (module) |

#### Qualcomm QCS Series

Qualcomm's **QCS** (Qualified Compute Stack) family, particularly the **QCS6490** and **QCS8550**, brings smartphone-grade AI acceleration to edge devices. The QCS8550 features the Qualcomm Hexagon DSP with the HVX (Hexagon Vector eXtensions) architecture and a dedicated Tensor accelerator, delivering up to 48 TOPS of INT4 performance.

| Feature | QCS6490 | QCS8550 |
|---------|---------|---------|
| CPU | 4× Cortex-A78 + 4× Cortex-A55 | 1× Cortex-X4 + 3× Cortex-A720 + 4× Cortex-A520 |
| AI accelerator | Hexagon DSP + Tensor | Hexagon DSP + Tensor |
| Peak AI throughput | 12 TOPS (INT8) | 48 TOPS (INT4) |
| Memory | 8 GB LPDDR5 | Up to 24 GB LPDDR5X |
| Power | 5–15 W | 10–30 W |
| Interface | PCIe, USB, Ethernet | PCIe Gen 4, USB 3.2, Ethernet |

### 2.4 Comprehensive Chip Comparison Table

The following table compares 18 edge AI chips and platforms across key dimensions relevant to deployment decisions:

| Device | Compute (TOPS) | Memory | Power (W) | Efficiency (TOPS/W) | Price (USD) | Best For |
|--------|---------------|--------|-----------|---------------------|-------------|----------|
| ESP32-S3 | ~0.001 (vector) | 512K SR + 8M PSRAM | 0.3–1.0 | ~0.001 | $6 | TinyML, keyword spotting |
| STM32H743 | ~0.004 (CMSIS-NN) | 1 MB SRAM | 0.35 | ~0.011 | $15 | Industrial ML, motor control |
| GAP9 | 0.05 (INT8) | 1.2 MB SRAM | 0.005–0.05 | 1.0–10.0 | $20 | Wearable AI, ECG/EMG |
| Google Coral USB | 4 (INT8) | Host-dependent | 2.0 | 2.0 | $60 | Vision classification, detection |
| Hailo-8 | 26 (INT8) | Host-dependent | 2.5 | 10.4 | $100 | Vision, multi-camera systems |
| Raspberry Pi 5 | ~0.01 (CPU) | 8 GB LPDDR4X | 3–12 | ~0.001 | $80 | Light ML, prototyping |
| Coral Dev Board | 4 (INT8) | 1 GB LPDDR4 | 5.0 | 0.8 | $150 | Vision with Edge TPU |
| Jetson Nano (old) | 0.47 (FP16) | 4 GB LPDDR4 | 5–10 | 0.05–0.09 | $99 (old) | Entry-level edge AI |
| Jetson Orin Nano | 40 (INT8) | 8 GB LPDDR5 | 7–15 | 2.7–5.7 | $249 | Robotics, LLMs (small) |
| Jetson Orin Nano Super | 67 (INT8) | 8 GB LPDDR5 | 7–25 | 2.7–9.6 | $249 | **NEXUS platform** |
| Jetson Orin NX 16GB | 100 (INT8) | 16 GB LPDDR5 | 10–25 | 4.0–10.0 | $599 | Multi-model edge AI |
| Jetson AGX Orin 64GB | 275 (INT8) | 64 GB LPDDR5 | 15–60 | 4.6–18.3 | $1,999 | Heavy edge AI, multi-camera SLAM |
| Intel Movidius Stick 2 | 1 (FP16) | 512 MB LPDDR4 | 1.5 | 0.67 | $70 | Vision (legacy) |
| Qualcomm QCS6490 | 12 (INT8) | 8 GB LPDDR5 | 5–15 | 0.8–2.4 | $200 | Mobile edge, vision |
| Qualcomm QCS8550 | 48 (INT4) | 24 GB LPDDR5X | 10–30 | 1.6–4.8 | $350 | Multi-model edge |
| Rockchip RK3588 | 6 (INT8) | 8–32 GB LPDDR4/5 | 5–20 | 0.3–1.2 | $100 | Budget edge AI, NAS |
| AMD Xilinx Kria K26 | 4 (INT8) | 4 GB DDR4 | 15 | 0.27 | $350 | FPGA-based reconfigurable AI |
| Huawei Ascend 310 | 22 (INT8) | Host-dependent | 8 | 2.75 | $200 | Vision, NLP |

**Key insight:** The Jetson Orin Nano Super (67 TOPS, $249) offers the best price-performance ratio for platforms like NEXUS that need to run LLMs alongside vision models. Its 8 GB LPDDR5 with 68 GB/s bandwidth is sufficient for a 7B-parameter model at Q4 quantization (4.2 GB) plus the OS and secondary models, as detailed in [[Section 6.4|#64-memory-budget-analysis]].

---

## 3. Model Optimization for Edge

Deploying neural network models on edge hardware requires aggressive optimization to fit within memory, compute, and power constraints while maintaining acceptable accuracy. This section covers the five principal techniques: quantization, pruning, knowledge distillation, efficient architecture design, and neural architecture search.

### 3.1 Quantization

Quantization is the process of reducing the numerical precision of a neural network's weights and activations. A model trained with 32-bit floating-point (FP32) arithmetic can be converted to lower-precision formats that use less memory and require fewer compute cycles per operation.

#### Precision Spectrum

The following table shows the precision formats commonly used in edge AI, from highest to lowest precision:

| Format | Bits per Weight | Memory Reduction vs FP32 | Compute Speedup | Typical Accuracy Loss |
|--------|----------------|-------------------------|-----------------|----------------------|
| FP32 (baseline) | 32 | 1.0× (baseline) | 1.0× (baseline) | 0% (baseline) |
| FP16 | 16 | 2.0× | 1.5–2.0× (GPU) | < 0.1% |
| BF16 | 16 | 2.0× | 1.5–2.0× (GPU) | < 0.5% |
| INT8 | 8 | 4.0× | 2.0–4.0× (INT8 HW) | 0.5–2.0% |
| INT4 | 4 | 8.0× | 4.0–8.0× | 1.0–5.0% |
| 2-bit | 2 | 16.0× | 8.0–16.0× | 5.0–15.0% |
| 1-bit (binary) | 1 | 32.0× | 32.0× (XNOR) | 15.0–40.0% |

#### Post-Training Quantization (PTQ)

PTQ converts a pre-trained FP32 model to lower precision without retraining. It is fast (minutes to hours) but may produce larger accuracy degradation, especially for models that are sensitive to quantization noise.

The most common PTQ methods include:

- **Min-max symmetric quantization**: Maps FP32 values to INT8 using the absolute maximum value as the scale factor. Simple but suboptimal for non-uniform weight distributions.
- **Percentile-based quantization**: Uses a percentile (e.g., 99.9th) of the absolute values to avoid outlier-dominated scaling.
- **Entropy-based quantization** (TensorRT): Chooses quantization parameters that minimize the KL divergence between the FP32 and INT8 activation distributions.

For the NEXUS platform, PTQ is the primary quantization approach for vision models (YOLOv8, classification networks) where INT8 quantization via TensorRT yields < 1% accuracy loss with 2–4× speedup on Jetson's Tensor cores.

#### Quantization-Aware Training (QAT)

QAT inserts simulated quantization operations (fake quantization nodes) into the training graph, allowing the model to learn weights that are robust to quantization noise. QAT typically recovers 0.5–1.0% accuracy compared to PTQ at the same precision, at the cost of a full training or fine-tuning cycle.

QAT is recommended when:
- PTQ produces > 2% accuracy degradation
- The model has asymmetric activation distributions
- The model uses sensitive operations (attention layers, softmax)

#### LLM-Specific Quantization Formats

The quantization of large language models for edge deployment has become a specialized subfield. The following table compares the dominant GGUF quantization formats used by [[llama.cpp|#44-llamacpp]]:

| Format | Bits per Weight | Group Size | KV Cache | VRAM for 7B Model | Speed (relative) | Quality (PPL increase) |
|--------|----------------|------------|----------|--------------------|--------------------|------------------------|
| Q8_0 | 8 | 32 | FP16 | ~7.5 GB | 0.85× | +0.1% |
| Q6_K | 6.5 | 256 | FP16 | ~6.0 GB | 0.95× | +0.3% |
| Q5_K_M | 5.5 | 256 | FP16 | ~5.1 GB | 1.00× (reference) | +1.2% |
| **Q4_K_M** | **4.5** | **256** | **FP16** | **~4.2 GB** | **1.15×** | **+4.2%** |
| Q4_0 | 4 | 32 | FP16 | ~3.9 GB | 1.20× | +6.8% |
| Q3_K_M | 3.5 | 256 | FP16 | ~3.3 GB | 1.30× | +12.1% |
| Q2_K | 2.5 | 256 | FP16 | ~2.6 GB | 1.50× | +25.4% |
| IQ4_XS | 4 | 256 | Q8 | ~3.6 GB | 1.25× | +5.5% |

**NEXUS quantization choice:** Q4_K_M is the optimal format for the NEXUS platform's Qwen2.5-Coder-7B deployment. It achieves a 7.6× memory reduction (4.2 GB vs. ~28 GB FP32) with only 4.2% perplexity increase, while running at 17.2 tokens/second on the Jetson Orin Nano Super's GPU. This is detailed in [[Section 6.2|#62-qwen25-coder-7b-quantization-analysis]].

#### Other LLM Quantization Methods

- **GPTQ** (Frantar et al., 2022): A one-shot post-training quantization method that uses approximate second-order information (Hessian) to minimize the layer-wise reconstruction error. GPTQ typically produces better INT4 models than simple PTQ but requires GPU-based calibration with representative data. Popular in the Hugging Face ecosystem.
- **AWQ** (Lin et al., 2023): Activation-Aware Weight Quantization protects salient weight channels (those with large activation magnitudes) from aggressive quantization. AWQ consistently outperforms GPTQ at INT4 for generative models.
- **bitsandbytes** (Dettmers et al., 2022): Provides NF4 (4-bit NormalFloat) and Double Quantization for memory-efficient LLM loading in the Hugging Face Transformers ecosystem. Primarily used for cloud inference, not edge deployment.

### 3.2 Pruning

Pruning removes unnecessary parameters from a neural network, reducing model size and inference latency without significantly degrading accuracy.

#### Structured vs. Unstructured Pruning

| Type | Method | Hardware Benefit | Accuracy Impact | Implementation Complexity |
|------|--------|-----------------|-----------------|--------------------------|
| **Unstructured** | Zero out individual weights with smallest magnitude | Memory reduction (sparse storage) | Low (< 1% at 50% sparsity) | Low (weight masking) |
| **Structured** | Remove entire filters, channels, attention heads, or layers | Actual compute reduction (smaller matrix dimensions) | Medium (2–5% at 50% sparsity) | High (architecture modification) |
| **Semi-structured** | Remove weights in 2:4 patterns (NVIDIA Ampere sparse tensor cores) | 2× compute speedup on Ampere+ GPUs | Low (< 1%) | Medium (requires hardware support) |

For edge deployment, **structured pruning** is generally preferred because it produces actual latency reductions — a 50% sparsity model with unstructured pruning still requires the same number of MAC operations unless the hardware supports sparse matrix multiplication. The NEXUS Jetson Orin Nano supports NVIDIA's **2:4 structured sparsity** on its Ampere Tensor cores, providing a 2× speedup for pruned models that conform to the 2:4 pattern (two out of every four consecutive weights are zero).

#### The Lottery Ticket Hypothesis

The **Lottery Ticket Hypothesis** (Frankle & Carlin, 2019) conjectures that within any large, over-parameterized network, there exists a small subnetwork ("winning ticket") that, when trained in isolation from the same initialization, can achieve comparable accuracy to the full network. This hypothesis has motivated research into **pruning at initialization** — identifying and keeping only the most important connections before training begins.

Practical implications for edge AI:
- Iterative Magnitude Pruning (IMP) can find 50–80% sparse subnetworks with < 1% accuracy loss for vision models
- The "winning ticket" property is more pronounced for convolutional networks than for transformers
- For LLMs, structured pruning of attention heads and FFN layers has been shown to remove 20–30% of parameters with minimal quality degradation (e.g., ShortGPT, SliceG)

### 3.3 Knowledge Distillation

Knowledge distillation transfers the learned representations of a large, accurate model (the **teacher**) to a smaller, faster model (the **student**) by training the student to match the teacher's output distribution (soft labels) rather than just the ground-truth labels.

#### Standard Distillation Pipeline

```
Teacher Model (e.g., LLaMA-70B)
        │
        │ Soft labels (logits with temperature T)
        ▼
Student Model (e.g., Qwen2.5-Coder-7B) ←── Hard labels (ground truth)
        │
        ▼
  Loss = α × CE(student, hard_labels) + (1-α) × KL(student_logits/T, teacher_logits/T)
```

The temperature parameter T controls the "softness" of the teacher's output distribution: higher T produces smoother distributions that reveal more information about the teacher's inter-class relationships. Typical values are T = 2–5.

#### Self-Distillation

In self-distillation (also called **self-training** or **bootstrapping**), the student model is a copy or slightly modified version of the teacher. The model is trained in multiple stages, where each stage's output becomes the teacher for the next stage. This technique requires no external teacher model and has been shown to improve generalization even without reducing model size.

#### Distillation for Edge AI

Knowledge distillation is critical for edge AI because it enables the creation of models that are specifically optimized for edge constraints while retaining the knowledge of much larger models:

| Teacher | Student | Task | Compression Ratio | Accuracy Retention |
|---------|---------|------|-------------------|-------------------|
| GPT-4 | Qwen2.5-Coder-7B | Code generation | ~20:1 | ~75% |
| BERT-Large | DistilBERT | NLP classification | 7:1 | 97% |
| ResNet-152 | MobileNetV3 | Image classification | 9:1 | 72% |
| Whisper-Large | Whisper-Tiny | Speech-to-text | 32:1 | ~60% |
| YOLOv8-XL | YOLOv8-Nano | Object detection | 30:1 | ~50% |

### 3.4 Efficient Architecture Design

Efficient architecture design creates neural network architectures that are inherently small and fast, rather than compressing a larger model after the fact.

#### MobileNet Family

The **MobileNet** family, developed by Google, pioneered depthwise separable convolutions as a drop-in replacement for standard convolutions. A standard convolution with kernel size K applied to C_in input channels and producing C_out output channels requires K² × C_in × C_out multiplications. A depthwise separable convolution decomposes this into a depthwise convolution (K² × C_in) followed by a pointwise 1×1 convolution (C_in × C_out), reducing computation by a factor of approximately K².

| Model | Parameters | FLOPs (224×224) | Top-1 ImageNet | Latency (Pixel 4, ms) |
|-------|-----------|-----------------|----------------|----------------------|
| MobileNetV1 | 4.2 M | 569 M | 70.6% | 6.0 |
| MobileNetV2 | 3.4 M | 300 M | 72.0% | 5.5 |
| MobileNetV3-Large | 5.4 M | 219 M | 75.2% | 4.5 |
| MobileNetV3-Small | 2.9 M | 56 M | 67.4% | 3.0 |
| MobileNetV4 | 3.1 M | 175 M | 76.4% | 3.8 |

#### EfficientNet Family

**EfficientNet** (Tan & Le, 2019) introduced compound scaling — simultaneously scaling network width, depth, and resolution using a principled coefficient. The EfficientNet-B0 to B7 family achieves better ImageNet accuracy per parameter than any previous architecture.

#### Efficient Transformer Architectures

For NLP and LLM tasks, the dominant efficient architectures include:

| Model | Parameters | Context | Task | Edge Viability |
|-------|-----------|---------|------|---------------|
| **DistilBERT** | 66 M | 512 tokens | Classification, QA | MCU-class (with INT8) |
| **TinyBERT** | 14.5 M | 512 tokens | Classification | MCU-class (INT8) |
| **ALBERT-Base** | 12 M (shared) | 512 tokens | Classification | MCU-class |
| **Phi-3-mini** | 3.8 B | 128K tokens | General LLM | SBC-class (Q4: ~2 GB) |
| **Qwen2.5-Coder-7B** | 7.6 B | 128K tokens | Code generation | SBC-class (Q4: ~4.2 GB) |
| **Gemma-2B** | 2.0 B | 8K tokens | General LLM | SBC-class (Q4: ~1.2 GB) |
| **TinyLlama-1.1B** | 1.1 B | 2K tokens | General LLM | SBC-class (Q4: ~0.7 GB) |

### 3.5 Neural Architecture Search (NAS)

Neural Architecture Search automates the design of neural network architectures by searching over a defined space of possible architectures and evaluating their performance on a target task and hardware platform. NAS has produced several state-of-the-art efficient architectures:

- **EfficientNet** was discovered via NAS using the compound scaling method
- **MobileNetV3** used hardware-aware NAS to optimize for actual latency on mobile phones, not just FLOP count
- **TinyTL** combines NAS with weight-only quantization, searching for architectures where only the biases need to be stored in high precision

NAS for edge AI differs from general NAS in two key ways: (1) the search objective includes hardware-specific metrics (latency, energy, memory) alongside accuracy, and (2) the search space is constrained to hardware-supported operations (e.g., depthwise convolutions for mobile GPUs, INT8 MAC operations for NPUs).

For the NEXUS platform, NAS is not directly used (the architecture relies on pre-trained models from the open-source community), but the principles of hardware-aware architecture selection guide model choice: Qwen2.5-Coder-7B was selected over alternatives because its Grouped Query Attention (GQA) architecture reduces KV cache memory by 8× compared to standard multi-head attention, making it more suitable for edge deployment with limited VRAM.

---

## 4. Edge AI Frameworks

### 4.1 TensorFlow Lite (TFLite)

**TensorFlow Lite** is Google's lightweight inference framework for mobile and embedded devices. It converts trained TensorFlow models into a FlatBuffer-based `.tflite` format optimized for on-device execution.

**Architecture:**

| Component | Description |
|-----------|-------------|
| **TFLite Converter** | Converts TF SavedModel / Keras model to `.tflite` format with quantization |
| **TFLite Interpreter** | On-device runtime that loads and executes `.tflite` models |
| **Delegates** | Hardware-specific execution backends (GPU, NNAPI, Edge TPU, Hexagon DSP, Core ML) |
| **Task Library** | High-level APIs for common tasks (ImageClassifier, ObjectDetector, NLClassifier) |
| **Micro** | Ultra-lightweight interpreter for microcontrollers (< 16 KB RAM) |

**Delegates** extend TFLite to leverage hardware accelerators:
- **GPU Delegate** (OpenGL ES / Vulkan): 2–5× speedup for conv operations
- **NNAPI Delegate** (Android): Routes to Qualcomm Hexagon, Mali GPU, or Edge TPU
- **Edge TPU Delegate**: Runs on Google Coral hardware with INT8 quantization
- **XNNPACK Delegate**: Optimized CPU backend using SIMD (ARM NEON, x86 AVX)

**TFLite for Microcontrollers** targets the TinyML space:
- Minimum footprint: ~16 KB RAM, ~200 KB flash
- Supports INT8 and INT16 quantization
- No dynamic memory allocation (fully static)
- Runs bare-metal on ARM Cortex-M, ESP32, RISC-V

### 4.2 ONNX Runtime Mobile

**ONNX Runtime Mobile** (from Microsoft) provides cross-platform inference for models in the Open Neural Network Exchange (ONNX) format. It supports quantization (INT8, UINT8) and hardware acceleration via EPs (Execution Providers).

| Feature | TFLite | ONNX Runtime Mobile |
|---------|--------|---------------------|
| Source format | TensorFlow / Keras | ONNX (PyTorch, TF, etc.) |
| Model quantization | Built-in converter | ONNX Quantization tools |
| Hardware delegates | GPU, NNAPI, Edge TPU, Hexagon | NNAPI, CoreML, DirectML, QNN |
| Micro support | TFLite Micro | Not available |
| Model zoo | TF Hub (mostly vision) | Hugging Face ONNX Hub |
| Dynamic shapes | Limited | Full support |
| Edge LLM support | No | No (use llama.cpp) |

ONNX Runtime Mobile is the preferred choice when the training pipeline uses PyTorch (as is common in research and NLP), since the ONNX format provides a direct conversion path without going through TensorFlow.

### 4.3 TensorRT

**NVIDIA TensorRT** is a high-performance deep learning inference optimizer and runtime specifically designed for NVIDIA GPUs. It is the **primary inference framework for the NEXUS platform's Jetson Orin Nano**.

**Key capabilities:**

| Feature | Description |
|---------|-------------|
| **Layer fusion** | Combines multiple layers (conv + bias + ReLU) into single GPU kernels |
| **Kernel auto-tuning** | Selects optimal CUDA kernels for the target GPU (Ampere SM 8.7) |
| **INT8 calibration** | Calibrates quantization using representative dataset with KL-divergence minimization |
| **Dynamic shapes** | Supports variable input dimensions (e.g., variable-length text sequences) |
| **Memory optimization** | Reduces VRAM usage through tensor lifecycle analysis and in-place operations |
| **Tensor cores** | Exploits mixed-precision (FP16/INT8) Tensor Core operations on Ampere |
| **DLA support** | Can offload compatible layers to the Deep Learning Accelerator on Jetson |

**TensorRT workflow on NEXUS:**

```
ONNX Model (from PyTorch/HuggingFace)
        │
        ▼  trtexec --onnx=model.onnx --fp16 --int8 --calib=data/calibration.cache
TensorRT Engine (.engine / .plan)
        │
        ▼  TensorRT Runtime API (C++ / Python)
GPU Execution (FP16/INT8 Tensor Cores)
```

For vision models (YOLOv8, ResNet, classification networks), TensorRT provides 2–4× speedup over native PyTorch on the same Jetson hardware by leveraging layer fusion, kernel auto-tuning, and INT8 Tensor Core operations. For LLMs, TensorRT-LLM provides optimized kernels for transformer inference, though the NEXUS platform currently uses [[llama.cpp|#44-llamacpp]] for LLM inference due to its broader quantization format support.

### 4.4 llama.cpp

**llama.cpp** is an open-source C/C++ implementation of LLM inference designed for CPU and GPU execution on consumer hardware. Originally created by Georgi Gerganov for running LLaMA models on MacBook CPUs, it has become the de facto standard for running quantized LLMs on edge devices.

**Key features relevant to NEXUS:**

| Feature | Implementation |
|---------|---------------|
| **GGUF format** | Single-file model format supporting mixed-precision quantization per-layer |
| **Quantization formats** | Q2_K through Q8_0, plus IQ (importance-weighted quantization) variants |
| **GPU acceleration** | CUDA, Metal, Vulkan, SYCL, ROCm backends |
| **KV cache management** | Offloading to GPU, CPU-GPU split, quantized KV cache |
| **Prompt processing** | Batched prompt evaluation for efficient context filling |
| **GGML tensor library** | Low-level tensor operations with SIMD optimization (AVX2, NEON) |
| **Server mode** | OpenAI-compatible HTTP API for integration with other services |

**Why NEXUS uses llama.cpp for LLMs:**

1. **Quantization flexibility.** TensorRT-LLM supports FP16 and INT8 but does not support the Q4_K_M format that is optimal for NEXUS's memory constraints. llama.cpp's GGUF format enables fine-grained per-layer quantization that balances accuracy and memory.

2. **Mixed CPU-GPU execution.** When the KV cache exceeds GPU memory, llama.cpp can offload layers to CPU. On the Jetson Orin Nano's 8 GB VRAM, the Q4_K_M Qwen2.5-Coder-7B model (4.2 GB weights) fits entirely in GPU memory, leaving ~3.8 GB for KV cache — sufficient for ~16K tokens of context at Q4_K_M quantization.

3. **Portability.** llama.cpp is a single C/C++ codebase with no external dependencies beyond the CUDA runtime. It compiles on ARM64 Linux (Jetson), x86-64 Linux (desktop), macOS, and even Raspberry Pi.

4. **Active community.** llama.cpp is one of the most active open-source AI projects, with frequent support for new model architectures and quantization methods.

**NEXUS llama.cpp build configuration:**

```bash
# Jetson Orin Nano (ARM64 + CUDA)
cmake -B build \
  -DGGML_CUDA=ON \
  -DGGML_CUDA_F16=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_ARCHITECTURES=87  # Ampere SM 8.7

# Recommended runtime flags
./llama-server \
  -m qwen2.5-coder-7b-q4_k_m.gguf \
  -ngl 99 \          # All layers on GPU
  -ctx 8192 \        # Context window
  -batch-size 512 \  # Batch size for prompt eval
  -ubatch-size 64    # Micro-batch for generation
```

### 4.5 Edge Impulse

**Edge Impulse** is an end-to-end TinyML platform that provides data collection, signal processing, model training, and deployment for microcontroller-class devices. It abstracts away the complexity of embedded ML, making it accessible to domain experts without deep ML expertise.

| Capability | Description |
|------------|-------------|
| **Data acquisition** | Web-based data collection from sensors (accelerometer, microphone, camera) |
| **Signal processing** | DSP blocks: FFT, filtering, feature extraction, spectral analysis |
| **Model training** | AutoML: automatically selects and trains optimal model architecture |
| **Quantization** | Automatic INT8 quantization with accuracy impact assessment |
| **Deployment** | Generates C++ library for Arduino, ESP32, STM32, nRF52, Ambiq |
| **Testing** | On-device performance benchmarking (latency, memory, accuracy) |
| **EON Tuner** ("EON" = Embedded, Optimized Neural) | Hardware-aware NAS that selects architecture for target MCU |

Edge Impulse is the recommended starting point for teams new to TinyML. However, for the NEXUS platform's Jetson Orin Nano workloads (LLMs, computer vision), Edge Impulse is not suitable — its model sizes are limited to < 1 MB, and it does not support transformer architectures.

### 4.6 TVM and Apache TVM

**Apache TVM** (Tensor Virtual Machine) is a compiler stack for deep learning that takes models from multiple frameworks (TensorFlow, PyTorch, MXNet, ONNX) and compiles them into optimized machine code for diverse hardware targets (CPUs, GPUs, FPGAs, ASICs).

**TVM compilation pipeline:**

```
Frontend (TF/PyTorch/ONNX)
        │
        ▼  Relay IR (high-level tensor operations)
Relay Optimizer (fusion, layout transformation, constant folding)
        │
        ▼  TE (Tensor Expression) / TIR (Tensor IR)
AutoTVM / AutoScheduler (hardware-specific kernel tuning)
        │
        ▼  Target-specific code generation
Runtime Library (compiled .so / .dll)
```

**Key capabilities:**
- **AutoTVM**: Automatic kernel tuning that explores operator implementations and finds the fastest configuration for the target hardware. This is critical for edge AI because optimal kernels vary dramatically across hardware (ARM NEON vs. CUDA vs. custom NPU).
- **BYOC (Bring Your Own Codegen)**: Integrates external code generators (TensorRT, TensorRT-LLM, Intel OpenVINO, Ethos-N NPU) into the TVM compilation pipeline.
- **Relay**: A high-level intermediate representation that supports standard ML operations and enables cross-framework model optimization.

TVM is primarily used in production environments where a single model must be deployed across heterogeneous hardware (e.g., a model that runs on both x86 servers and ARM edge devices). For the NEXUS platform, TVM is not currently used (llama.cpp and TensorRT provide sufficient optimization for the homogeneous Jetson hardware), but TVM would be valuable if NEXUS were ported to additional hardware targets.

### 4.7 Framework Comparison Table

| Framework | Supported Models | Quantization | Hardware Acceleration | MCU Support | LLM Support | License |
|-----------|-----------------|--------------|----------------------|-------------|-------------|---------|
| **TensorFlow Lite** | TF/Keras models | INT8, INT16, FP16 | GPU, NNAPI, Edge TPU, Hexagon | Yes (TFLite Micro) | Limited (TFLite Tasks) | Apache 2.0 |
| **ONNX Runtime Mobile** | ONNX models | INT8, UINT8 | NNAPI, CoreML, QNN, DirectML | No | No | MIT |
| **TensorRT** | ONNX, UFF | FP16, INT8 | CUDA, Tensor Cores, DLA | No | TensorRT-LLM (separate) | NVIDIA EULA |
| **llama.cpp** | GGUF (LLaMA-family) | Q2_K–Q8_0, IQ, FP16 | CUDA, Metal, Vulkan, SYCL | No | Primary use case | MIT |
| **Edge Impulse** | AutoML + imported | INT8, INT16 | MCU DSP, various MCUs | Yes (primary target) | No | Commercial (free tier) |
| **Apache TVM** | TF, PyTorch, ONNX, MXNet | INT8, INT16, FP16 | AutoTVM (any target), BYOC | Experimental | Experimental | Apache 2.0 |
| **OpenVINO** | ONNX, TF, PyTorch | FP16, INT8 | Intel CPU/GPU/VPU/NPU | No | OpenVINO-LLM | Apache 2.0 |
| **NCNN** | Caffe, ONNX | INT8 | ARM NEON, Vulkan, Metal | Experimental | No | BSD 3-Clause |

---

## 5. Edge AI Applications

### 5.1 Computer Vision

Computer vision is the most mature application domain for edge AI, driven by the availability of efficient model architectures and dedicated vision accelerators.

#### Object Detection

Real-time object detection is essential for autonomous navigation, surveillance, and industrial quality control. On edge hardware, the **YOLO family** (You Only Look Once) dominates due to its single-stage, real-time detection architecture:

| Model | Input Size | mAP (COCO) | Parameters | Jetson Orin Nano FPS (FP16) | Jetson Orin Nano FPS (INT8) |
|-------|-----------|------------|------------|---------------------------|---------------------------|
| YOLOv8-Nano | 640×640 | 37.3% | 3.2 M | 180+ | 280+ |
| YOLOv8-Small | 640×640 | 44.9% | 11.2 M | 120+ | 200+ |
| YOLOv8-Medium | 640×640 | 50.2% | 25.9 M | 70+ | 120+ |
| YOLOv8-Large | 640×640 | 52.9% | 43.7 M | 40+ | 70+ |
| YOLOv10-Nano | 640×640 | 38.5% | 2.3 M | 200+ | 300+ |
| YOLOv11-Nano | 640×640 | 39.7% | 2.6 M | 190+ | 290+ |

**NEXUS application:** YOLOv8-Nano at 640×640 runs at >180 fps on the Jetson Orin Nano Super, enabling real-time detection of vessels, buoys, navigational markers, and obstacles for maritime autonomous navigation. The NEXUS platform's [[Marine AI Systems brief|vessel-platform/14_marine_ai_systems.txt]] specifies a 30 Hz detection rate with < 30 ms latency — well within the capability of even the YOLOv8-Medium model.

#### Semantic Segmentation

Semantic segmentation assigns a class label to every pixel in an image, providing dense scene understanding. Edge-efficient segmentation models include:

| Model | Parameters | mIoU (Cityscapes) | Jetson Latency (ms) |
|-------|-----------|-------------------|---------------------|
| DeepLabV3-Mobile | 5.8 M | 75.0% | ~25 |
| Fast-SCNN | 1.1 M | 68.0% | ~8 |
| LR-ASPP | 0.7 M | 62.0% | ~5 |
| BiSeNetV2 | 1.5 M | 72.0% | ~10 |

#### Pose Estimation

Human pose estimation on edge devices uses lightweight architectures like **MediaPipe Pose** (Google), **MoveNet** (TensorFlow), and **YOLOv8-Pose**:

| Model | Parameters | Keypoints | Jetson Latency (ms) |
|-------|-----------|-----------|---------------------|
| MoveNet-Lightning | 3.9 M | 17 | ~5 |
| MoveNet-Thunder | 9.0 M | 17 | ~12 |
| MediaPipe Pose | 3.0 M | 33 | ~8 |
| YOLOv8-Pose-Nano | 3.2 M | 17 | ~6 |

### 5.2 Speech and Audio

#### Wake Word Detection

Wake word (keyword spotting) detection is the canonical TinyML application. Models are typically < 500 KB and run on microcontrollers at < 1 mW:

| Model | Parameters | Memory | Latency | Accuracy | Platform |
|-------|-----------|--------|---------|----------|----------|
| DS-CNN | 22 K | 8 KB SRAM | 30 ms | 95% (single word) | ARM Cortex-M4 |
| CRNN | 50 K | 15 KB SRAM | 50 ms | 96% | ARM Cortex-M4 |
| Attention-based | 75 K | 22 KB SRAM | 80 ms | 97% | ARM Cortex-M4F |
| AudioMNV2 | 335 K | 100 KB SRAM | 100 ms | 98% | ESP32-S3, ARM Cortex-M7 |
| MCUNetV2 | 417 K | 256 KB SRAM | 150 ms | 97.5% | STM32H7 |

#### Speech-to-Text

Edge speech-to-text has been revolutionized by **OpenAI's Whisper** model family. While the full Whisper-Large model requires cloud infrastructure, the Whisper-Tiny model is viable on edge hardware:

| Model | Parameters | VRAM (FP16) | VRAM (INT8) | WER (LibriSpeech) | Jetson Speed |
|-------|-----------|-------------|-------------|--------------------|--------------|
| Whisper-Tiny | 39 M | ~75 MB | ~40 MB | ~7% | ~15× real-time |
| Whisper-Base | 74 M | ~140 MB | ~75 MB | ~5% | ~8× real-time |
| Whisper-Small | 244 M | ~460 MB | ~240 MB | ~3% | ~3× real-time |
| Whisper-Medium | 769 M | ~1.5 GB | ~770 MB | ~2.5% | ~1× real-time |
| Whisper-Large-v3 | 1.55 B | ~3.0 GB | ~1.5 GB | ~1.5% | ~0.3× real-time |

**NEXUS application:** Whisper-Small (INT8, ~240 MB VRAM) provides a good balance for the NEXUS platform, processing audio at 3× real-time speed on the Jetson Orin Nano. However, because Whisper shares GPU VRAM with Qwen2.5-Coder-7B, it is loaded **on-demand** and swapped out when not in use, as detailed in [[Section 6.5|#65-whisper-for-voice-on-demand-loading]].

### 5.3 Time-Series and Predictive Maintenance

Time-series analysis on edge devices encompasses anomaly detection, predictive maintenance, and condition monitoring. These applications are well-suited for microcontroller-class devices due to low-dimensional inputs (typically 1–20 sensor channels) and relatively simple model architectures.

| Application | Model Architecture | Typical Size | MCU Viability | Accuracy |
|-------------|-------------------|-------------|---------------|----------|
| Vibration anomaly detection | 1D-CNN + Autoencoder | 10–50 KB | Yes (Cortex-M4) | 92–98% |
| Bearing fault classification | 1D-CNN + SVM | 20–80 KB | Yes (Cortex-M4F) | 90–96% |
| Power consumption anomaly | LSTM (small) | 50–200 KB | Marginal (Cortex-M7) | 88–95% |
| Motor current signature | FFT + 1D-CNN | 10–30 KB | Yes (Cortex-M4) | 91–97% |
| Temperature prediction | Linear regression / SVR | < 1 KB | Yes (any MCU) | 85–95% |

**NEXUS application:** The NEXUS ESP32-S3's [[pattern discovery engine]] (cross-correlation, BOCPD change-point detection) implements edge-side time-series analysis for vessel operational patterns. While this is statistical rather than ML-based, the same data pipeline could feed TinyML anomaly detection models on the ESP32-S3 in future iterations.

### 5.4 Robotics and Autonomous Navigation

Edge AI is foundational to autonomous robotics, where real-time perception, planning, and control must execute onboard with minimal latency. Key applications include:

| Task | Model / Algorithm | Latency Requirement | Edge Platform | NEXUS Relevance |
|------|-------------------|-------------------|---------------|-----------------|
| Visual SLAM | ORB-SLAM3 + DNN loop closure | 30–100 ms | Jetson Orin | Future capability |
| Obstacle avoidance | YOLOv8-Nano + depth estimation | < 50 ms | Jetson Orin | Primary (maritime) |
| Path planning | RRT* / A* / D* Lite | 100–500 ms | Jetson Orin | Cognitive layer |
| Terrain classification | Semantic segmentation | < 100 ms | Jetson Orin | N/A (marine) |
| Object manipulation | GraspNet + force feedback | 10–50 ms | Jetson Orin | N/A (marine) |
| Vessel detection | YOLOv8-Nano (marine-trained) | < 50 ms | Jetson Orin | **Active deployment** |
| Navigation (COLREGs) | Rule-based + LLM reasoning | 100–1000 ms | Jetson Orin | **Active deployment** |

### 5.5 Natural Language Processing on Edge

Edge NLP has been historically challenging due to the parameter count of language models, but the combination of efficient architectures and aggressive quantization has made it viable on single-board computers.

| Application | Model (Quantized) | VRAM | Latency | Quality |
|-------------|-------------------|------|---------|---------|
| Sentiment analysis | DistilBERT (INT8) | ~65 MB | < 10 ms | 91% accuracy |
| Intent classification | TinyBERT (INT8) | ~15 MB | < 5 ms | 89% accuracy |
| Text summarization | BART-Base (INT8) | ~440 MB | ~500 ms | ROUGE ~18 |
| Named entity recognition | BERT-Tiny (INT8) | ~30 MB | < 10 ms | F1 ~82 |
| Code generation | Qwen2.5-Coder-7B (Q4_K_M) | ~4.2 GB | ~58 ms/tok | HumanEval 89.6% |
| Conversational AI | Phi-3-mini (Q4_K_M) | ~2.0 GB | ~35 ms/tok | MMLU 68% |
| Speech-to-text | Whisper-Small (INT8) | ~240 MB | 3× real-time | WER ~3% |

**NEXUS application:** The NEXUS platform uses Qwen2.5-Coder-7B at Q4_K_M for reflex synthesis (converting natural language observations and operator instructions into executable Reflex JSON bytecode), and Phi-3-mini for conversational interaction and non-code reasoning tasks. This dual-model architecture is detailed in [[Section 6|#6-nexus-edge-ai-stack-analysis]].

---

## 6. NEXUS Edge AI Stack Analysis

This section provides a detailed analysis of the NEXUS platform's edge AI deployment, including hardware selection rationale, model quantization decisions, memory budgeting, and the architectural decision to run AI on Jetson rather than ESP32.

### 6.1 Jetson Orin Nano as Edge AI Platform

The NEXUS platform selected the **NVIDIA Jetson Orin Nano Super** (developer kit, $249) as its primary edge AI compute platform. This decision is driven by the following requirements and constraints:

| Requirement | NEXUS Need | Jetson Orin Nano Super Spec |
|-------------|-----------|----------------------------|
| LLM inference | 7B model at > 15 tok/s | 67 TOPS INT8, CUDA + Tensor Cores |
| VRAM for 7B Q4 model | > 4.5 GB | 8 GB LPDDR5 (68 GB/s bandwidth) |
| Vision inference | 30 fps object detection | 67 TOPS sufficient for YOLOv8-Nano @ 180 fps |
| Power budget | < 30 W total | 7–25 W configurable |
| Thermal | Passive or small fan | Active cooling with included fan |
| Linux support | CUDA, Docker, standard ML stack | JetPack 6.x (Ubuntu 22.04 + CUDA 12) |
| Form factor | < 10×10 cm | 100×100 mm SoM |
| Cost | < $300 per node | $249 |

The Jetson Orin Nano Super delivers 67 TOPS of INT8 compute (up from 40 TOPS in the standard Orin Nano), achieved by unlocking higher GPU clock frequencies within the same thermal envelope. This makes it the most cost-effective AI edge platform for running 7B-parameter LLMs, as documented in the NEXUS [[Architecture Decision Records|specs/ARCHITECTURE_DECISION_RECORDS.md]].

**Three-Jetson cluster architecture:** The NEXUS platform deploys three Jetson Orin Nano units in a distributed cluster connected via Gigabit Ethernet, with each node responsible for a dedicated AI function (code generation, vision, sensor fusion) to eliminate runtime model swapping. This architecture is specified in the [[Jetson Cluster Architecture|vessel-platform/11_jetson_cluster_architecture.txt]].

### 6.2 Qwen2.5-Coder-7B Quantization Analysis

The **Qwen2.5-Coder-7B** model is the NEXUS platform's primary LLM, responsible for reflex synthesis (generating executable Reflex JSON bytecode from natural language prompts and sensor observations).

**Model architecture:**

| Parameter | Value |
|-----------|-------|
| Parameter count | 7.6 B (7,613,317,632) |
| Layers | 28 transformer blocks |
| Hidden dimension | 4096 |
| Attention heads | 32 (4 KV heads via GQA) |
| Context length | 128,000 tokens |
| Activation | SwiGLU |
| Position encoding | RoPE (Rotary Position Embedding) |
| Training data | 5.5 T tokens (code + natural language) |

**Quantization comparison for NEXUS deployment:**

| Format | VRAM Usage | Tokens/sec (CUDA) | PPL (WikiText-2) | Reflex Quality (RJQS) | **Recommendation** |
|--------|-----------|-------------------|------------------|----------------------|-------------------|
| FP16 | 14.5 GB | ❌ exceeds 8 GB | 5.12 | 0.96 | **Infeasible** |
| Q8_0 | 7.5 GB | ~12 tok/s | 5.14 (+0.4%) | 0.95 | Marginal (tight memory) |
| Q6_K | 6.0 GB | ~14 tok/s | 5.18 (+1.2%) | 0.94 | Viable |
| Q5_K_M | 5.1 GB | ~15.5 tok/s | 5.26 (+2.8%) | 0.92 | Good |
| **Q4_K_M** | **4.2 GB** | **~17.2 tok/s** | **5.33 (+4.2%)** | **0.90** | **Optimal** |
| Q4_0 | 3.9 GB | ~18 tok/s | 5.47 (+6.8%) | 0.85 | Quality concern |
| Q3_K_M | 3.3 GB | ~19.5 tok/s | 5.75 (+12.1%) | 0.72 | Unacceptable |

**Q4_K_M is optimal for NEXUS** because it provides the best balance of:
1. **Memory fit**: 4.2 GB leaves 3.8 GB for KV cache, OS, and secondary models
2. **Inference speed**: 17.2 tok/s generates a 500-token reflex in ~29 seconds (within the NEXUS cognitive latency budget of 30–120 seconds)
3. **Quality retention**: Only 4.2% perplexity increase over FP16, corresponding to ~6% decrease in Reflex JSON Quality Score (RJQS)
4. **KV cache efficiency**: At Q4_K_M, the 16K token KV cache requires approximately 1.2 GB, leaving 2.6 GB for OS and secondary models

The Q4_K_M format uses **block-wise quantization with k-quants**: the 4096-dimensional weight matrices are divided into blocks of 256 elements, and each block has its own scale factors. This per-block adaptation captures the non-uniform weight distributions of transformer layers, providing better accuracy than simpler uniform quantization (Q4_0) at a modest cost in decode overhead.

### 6.3 Phi-3-mini as Secondary Model

The **Microsoft Phi-3-mini** (3.8B parameters) serves as the NEXUS platform's secondary model for conversational interaction, intent classification, and non-code reasoning tasks.

| Parameter | Value |
|-----------|-------|
| Parameter count | 3.8 B |
| Quantization | Q4_K_M |
| VRAM usage | ~2.0 GB |
| Inference speed | ~25 tok/s (CUDA, Jetson Orin Nano) |
| Context length | 128K tokens |
| MMLU score (Q4_K_M) | ~68% (vs. 69% FP16) |

Phi-3-mini is deployed alongside Qwen2.5-Coder-7B on a dedicated Jetson node (or swapped in on single-node deployments) because:
1. It requires only 2.0 GB VRAM, fitting easily alongside other models
2. Its 25 tok/s speed is sufficient for conversational latency requirements
3. Its training data includes high-quality educational content and reasoning tasks, making it strong for general Q&A and intent classification
4. Its small size enables faster loading and unloading for model swap scenarios

### 6.4 Memory Budget Analysis

The NEXUS Jetson Orin Nano Super has 8 GB of unified LPDDR5 memory shared between the GPU and CPU. The memory budget for the AI stack is:

| Component | Memory Usage | Purpose |
|-----------|-------------|---------|
| Qwen2.5-Coder-7B (Q4_K_M) | 4.2 GB | Primary LLM for reflex synthesis |
| Phi-3-mini (Q4_K_M) | 2.0 GB | Secondary LLM for conversation/reasoning |
| KV cache (Qwen, 8K tokens) | 0.8 GB | Active inference context |
| Ubuntu 22.04 + JetPack | 0.4 GB | Operating system, drivers |
| ROS 2 + middleware | 0.1 GB | Robot Operating System |
| Camera buffers + pipelines | 0.15 GB | Vision processing DMA buffers |
| Python runtime + libraries | 0.15 GB | llama.cpp, TFLite, numpy |
| **Total committed** | **7.8 GB** | |
| **Free headroom** | **0.2 GB** | Safety margin for fragmentation |
| **Grand total** | **8.0 GB** | |

**Critical constraint:** This budget leaves zero room for Whisper (speech-to-text) to be loaded simultaneously. Whisper-Small at INT8 requires ~240 MB, which exceeds the 200 MB headroom. Therefore, **Whisper is loaded on-demand** and Qwen or Phi must be swapped out, as detailed in the next section.

**Three-node cluster solution:** With three Jetson Orin Nano units, the memory budget is distributed:

| Node | Primary Model | Memory Usage | Available for Other |
|------|---------------|-------------|---------------------|
| Node 1: "Cognitive" | Qwen2.5-Coder-7B (Q4_K_M) | 4.2 GB | 3.8 GB free |
| Node 2: "Vision" | YOLOv8-Medium + segmentation | 1.5 GB | 6.5 GB free |
| Node 3: "Interaction" | Phi-3-mini + Whisper-Small (swapped) | 2.5 GB | 5.5 GB free |

This architecture eliminates runtime model swapping and provides generous headroom on each node, as documented in the [[Jetson Cluster Architecture|vessel-platform/11_jetson_cluster_architecture.txt]].

### 6.5 Whisper for Voice: On-Demand Loading

Voice interaction on the NEXUS platform uses OpenAI's **Whisper-Small** model (INT8 quantized, ~240 MB VRAM) for speech-to-text, followed by Phi-3-mini for intent classification and response generation.

**On-demand model loading workflow:**

```
[Voice input detected]
        │
        ▼
1. Check VRAM availability
   - If Phi-3-mini loaded: unload Phi-3-mini (saves 2.0 GB)
   - If Qwen loaded: defer voice processing (priority: safety > control > interaction)
        │
        ▼
2. Load Whisper-Small (INT8) from NVMe → VRAM (~2 seconds)
        │
        ▼
3. Process audio buffer through Whisper-Small (3× real-time)
   Output: text transcript
        │
        ▼
4. Unload Whisper-Small from VRAM
        │
        ▼
5. Load Phi-3-mini (if not already in VRAM)
        │
        ▼
6. Feed transcript to Phi-3-mini for intent classification
   Output: structured intent JSON → action dispatch
```

**Timing analysis:**

| Step | Duration | Cumulative |
|------|----------|------------|
| Model unload (Phi-3-mini → disk) | ~1.5 s | 1.5 s |
| Model load (Whisper-Small from NVMe) | ~2.0 s | 3.5 s |
| Audio transcription (10 s of audio @ 3× RT) | ~3.3 s | 6.8 s |
| Model unload (Whisper) + load (Phi-3-mini) | ~3.5 s | 10.3 s |
| Intent classification (Phi-3-mini, ~200 tokens) | ~8.0 s | 18.3 s |
| **Total voice-to-intent latency** | | **~18 seconds** |

This latency is acceptable for NEXUS's voice interaction use case (operator commands and natural language queries), which operates at the **cognitive tier** (100–500 ms is the ideal target, but 18 seconds is acceptable for voice-driven reflex synthesis requests).

### 6.6 Why NOT TinyML on ESP32?

The NEXUS platform's ESP32-S3 nodes are remarkably capable microcontrollers (dual-core 240 MHz, 512 KB SRAM, 8 MB PSRAM), but they are fundamentally unsuitable for running modern AI models for the following reasons:

| Constraint | NEXUS Requirement | ESP32-S3 Capability | Gap |
|------------|-------------------|---------------------|-----|
| Model size (LLM) | 7B parameters (~4.2 GB Q4) | 8 MB PSRAM maximum | **525,000×** |
| Memory bandwidth | ~68 GB/s (Jetson LPDDR5) | ~40 MB/s (Octal SPI PSRAM) | **1,700×** |
| Compute throughput | 67 TOPS (Jetson INT8) | ~0.6 TOPS (vector INT8) | **112×** |
| Matrix operations | Tensor cores (16×16×16 INT8 MAC/cycle) | Software INT8 SIMD (256-bit) | ~**40×** |
| Floating point | Hardware FP16/FP32 | Software emulation (20–50 cycles/op) | **20–50×** |
| Model load time | < 1 second (NVMe → VRAM) | Minutes (flash → PSRAM) | **60×** |

**In concrete terms:** The smallest viable code generation model (TinyLlama-1.1B at Q4_K_M) requires ~700 MB of memory — 87.5× more than the ESP32-S3's total 8 MB PSRAM. Running this model would require streaming weights from external flash on every inference pass, resulting in inference times measured in hours (not milliseconds). Even a keyword spotting model (50 KB) is feasible only for its intended purpose, not for the general intelligence tasks that the NEXUS cognitive layer requires.

**The NEXUS architectural principle:** ESP32-S3 handles what it excels at — real-time sensor acquisition, actuator control, safety supervision, and the [[reflex bytecode VM|specs/firmware/reflex_bytecode_vm_spec.md]] — while the Jetson Orin Nano handles what it excels at — neural network inference, LLM processing, and computer vision. This is a **heterogeneous computing architecture** that places each workload on the hardware best suited to execute it.

This division of labor is analogous to the biological nervous system: the spinal cord (ESP32) handles reflexes without involving the brain, while the cerebral cortex (Jetson) handles higher-order reasoning, planning, and language. The NEXUS platform's [[three-tier architecture]] maps directly to this biological model.

---

## 7. Performance Benchmarking

### 7.1 Inference Latency vs. Model Size Tradeoff

The fundamental tradeoff in edge AI is between model accuracy (which generally increases with model size) and inference latency (which also increases with model size, but is bounded by hardware compute). The following table illustrates this tradeoff on the Jetson Orin Nano Super:

| Model | Parameters | Quantization | VRAM | Latency (ms/tok) | Speed (tok/s) | Quality |
|-------|-----------|--------------|------|-------------------|---------------|---------|
| TinyLlama-1.1B | 1.1 B | Q4_K_M | 0.7 GB | 11 | 90 | Perplexity 8.2 |
| Phi-2-2.7B | 2.7 B | Q4_K_M | 1.6 GB | 20 | 50 | Perplexity 6.1 |
| Phi-3-mini-3.8B | 3.8 B | Q4_K_M | 2.0 GB | 28 | 36 | Perplexity 5.8 |
| Gemma-2B | 2.0 B | Q4_K_M | 1.2 GB | 15 | 67 | Perplexity 6.5 |
| Qwen2.5-Coder-7B | 7.6 B | Q4_K_M | 4.2 GB | 58 | 17.2 | Perplexity 5.33 |
| Mistral-7B | 7.2 B | Q4_K_M | 4.0 GB | 55 | 18 | Perplexity 5.5 |
| CodeLlama-7B | 6.7 B | Q4_K_M | 3.8 GB | 52 | 19 | Perplexity 5.7 |
| Qwen2.5-Coder-7B | 7.6 B | Q5_K_M | 5.1 GB | 64 | 15.5 | Perplexity 5.26 |
| Qwen2.5-Coder-7B | 7.6 B | FP16 | 14.5 GB | N/A | N/A | Perplexity 5.12 |

**The Pareto frontier** for the NEXUS platform (latency vs. quality, constrained to 8 GB VRAM) includes:
- **Phi-3-mini (Q4_K_M)**: Best speed-to-quality ratio for conversational tasks
- **Qwen2.5-Coder-7B (Q4_K_M)**: Best quality for code generation within 8 GB VRAM
- **Qwen2.5-Coder-7B (Q5_K_M)**: Best quality achievable if memory is freed by model swapping

### 7.2 Power Consumption Analysis

Edge AI power consumption is critical for autonomous systems where energy is limited (battery-powered or solar-powered vessels). The following measurements are for the Jetson Orin Nano Super:

| Operating Mode | Power Draw | Activity |
|----------------|-----------|----------|
| Idle (Linux booted) | 3.5 W | CPU idle, GPU powered down |
| Sensor acquisition | 4.2 W | Camera capture, I2C polling |
| LLM inference (Qwen2.5-Coder-7B Q4_K_M, batch decode) | 12–15 W | GPU at ~80% utilization |
| LLM inference (sustained, 30 min) | 13 W (avg) | Thermal equilibrium reached |
| Vision inference (YOLOv8-Nano, 30 fps) | 8–10 W | GPU at ~30% utilization |
| Combined LLM + Vision | 18–22 W | GPU near saturation |
| Peak (all cores maxed) | 25 W | DVFS at maximum |

**Power budget for NEXUS vessel:**
- Solar panel output: ~60 W (typical marine solar installation)
- Total vessel power budget: ~45 W for electronics
- Three Jetson Orin Nanos at ~13 W each: 39 W
- ESP32-S3 nodes (×6): ~6 W total
- **Total AI stack: ~45 W** — matches available power

The NEXUS platform's [[power and thermal management strategy|addenda/02_Performance_Budgets_and_Optimization.md]] uses DVFS (Dynamic Voltage and Frequency Scaling) to modulate Jetson power consumption based on AI workload demand, reducing average power draw to ~10 W during low-activity periods.

### 7.3 Thermal Management at Sustained Inference

Sustained AI inference on the Jetson Orin Nano generates significant heat. The Ampere GPU at full utilization produces approximately 10–15 W of thermal energy that must be dissipated to maintain junction temperatures below the 100°C thermal throttle point.

**Thermal profile during sustained LLM inference (Qwen2.5-Coder-7B Q4_K_M):**

| Time | GPU Temperature | SoC Temperature | Fan Speed | Power Draw | Notes |
|------|----------------|-----------------|-----------|------------|-------|
| 0:00 | 42°C | 38°C | 30% | 12 W | Cold start |
| 0:30 | 55°C | 48°C | 40% | 13 W | Warming |
| 1:00 | 63°C | 55°C | 50% | 14 W | Approaching equilibrium |
| 5:00 | 69°C | 60°C | 55% | 14.5 W | Thermal equilibrium |
| 15:00 | 69°C | 60°C | 55% | 14.5 W | Stable |
| 30:00 | 69°C | 60°C | 55% | 14.5 W | No degradation |

The Jetson Orin Nano's active cooling system (included heatsink + fan) maintains a stable 69°C GPU temperature during sustained LLM inference, which is well below the 100°C throttle threshold. This provides approximately 30°C of thermal headroom for ambient temperature increases (e.g., direct sunlight on a marine vessel deck, where ambient temperatures can reach 40–50°C).

**NEXUS thermal design considerations:**
- Jetson units are housed in IP67-rated enclosures with passive ventilation
- Ambient temperature sensor triggers DVFS downscaling above 55°C ambient
- The [[safety system|specs/safety/safety_system_spec.md]] monitors Jetson temperature and triggers graceful degradation if SoC temperature exceeds 85°C

### 7.4 Batch Size Considerations for Edge

Batch size selection on edge devices involves a different tradeoff than in cloud training. For edge inference:

| Batch Size | Latency (single inference) | Throughput (inferences/sec) | Memory (activations) | Use Case |
|-----------|---------------------------|---------------------------|---------------------|----------|
| 1 | Minimum | Lowest | Minimum | Interactive / real-time |
| 2–4 | 1.2–1.5× latency | 1.5–2.0× throughput | 2–4× activations | Multi-stream processing |
| 8–16 | 1.5–2.0× latency | 3–5× throughput | 8–16× activations | Batch analytics |
| 32+ | 2.0–3.0× latency | 5–8× throughput | 32×+ activations | Max throughput (cloud) |

**NEXUS batch size decisions:**

| Workload | Batch Size | Rationale |
|----------|-----------|-----------|
| LLM generation (tok-by-tok) | 1 | Autoregressive generation is inherently sequential |
| LLM prompt processing (prefill) | 512 (ubatch 64) | Batch process prompt tokens for efficiency; ubatch limits memory |
| YOLOv8 detection | 1 | Single camera stream; batch size > 1 increases latency without benefit |
| Whisper audio processing | 1 (30s segments) | Sequential audio segments; 30s chunks balance quality and latency |

---

## 8. The Future of Edge AI

### 8.1 Scaling Laws for Edge Models

Empirical scaling laws suggest that model quality scales predictably with parameter count, training data, and compute. For edge AI, the relevant question is: **when will smaller models match today's larger models?**

**Historical trajectory and projections:**

| Year | Best 1B Model ≈ Today's | Best 3B Model ≈ Today's | Best 7B Model ≈ Today's |
|------|------------------------|------------------------|------------------------|
| 2023 | GPT-2 (2019) | GPT-3-small (2020) | GPT-3 (2020) |
| 2024 | Mistral-7B (2023) | LLaMA-2-13B (2023) | LLaMA-2-70B (2023) |
| 2025 | Qwen2.5-3B ≈ LLaMA-2-7B | Qwen2.5-7B ≈ LLaMA-2-13B | Qwen2.5-32B ≈ GPT-3.5 |
| 2026 (projected) | Qwen3-1B ≈ Qwen2.5-7B | Qwen3-3B ≈ current Qwen2.5-Coder-7B | Qwen3-7B ≈ current 30B |
| 2028 (projected) | Model-1B ≈ current 3B | Model-3B ≈ current 7B | Model-7B ≈ current 30B |

**Implication for NEXUS:** By 2026, a 3B-parameter model should match Qwen2.5-Coder-7B's current quality (89.6% HumanEval, 0.96 RJQS). At Q4_K_M, a 3B model requires only ~1.6 GB VRAM, enabling it to run alongside Phi-3-mini, Whisper, and YOLOv8 on a single 8 GB Jetson — eliminating the need for model swapping entirely. This would halve the NEXUS hardware cost from three Jetson units ($750) to one ($249) plus a smaller dedicated vision unit.

### 8.2 Mixture of Experts (MoE) for Edge

Mixture of Experts architectures (e.g., Mixtral 8×7B, Qwen1.5-MoE-A2.7B) use sparse activation to achieve quality comparable to dense models of much larger size while requiring only a fraction of the compute per token. In MoE models, only a subset of expert layers are activated for each input token (typically 2 of 8 experts), reducing FLOPs proportionally.

| Model | Total Params | Active Params (per token) | Quality | VRAM (Q4) | Edge Viability |
|-------|-------------|--------------------------|---------|-----------|---------------|
| Mixtral 8×7B | 46.7 B | 12.9 B (2/8 experts) | ≈ LLaMA-2-70B | ~24 GB | ❌ Too large |
| Qwen1.5-MoE-A2.7B | 14.3 B | 3.4 B (2/8 experts) | ≈ LLaMA-2-13B | ~7.5 GB | Marginal (Q4) |
| Phi-3.5-MoE (future) | ~8 B (projected) | ~2 B (projected) | ≈ Qwen2.5-7B | ~4.5 GB (Q4) | **Viable (2026)** |
| Custom 4-expert MoE | ~6 B | ~1.5 B | TBD | ~3.5 GB (Q4) | **NEXUS target** |

**NEXUS MoE opportunity:** A custom 4-expert MoE model with ~6B total parameters and ~1.5B active parameters per token could match Qwen2.5-Coder-7B's quality while fitting in 3.5 GB VRAM at Q4_K_M — and running at ~30 tok/s (2× faster than the current dense model). This is a medium-term research direction for the NEXUS platform.

### 8.3 Neuromorphic Computing

Neuromorphic computing implements neural network computations using hardware that mimics biological neurons and synapses, rather than traditional von Neumann architecture (separate CPU, memory, and I/O).

**Intel Loihi 2** (2022):
| Feature | Specification |
|---------|---------------|
| Neuron cores | 128 |
| Neurons per chip | ~1 million |
| Synapses per chip | ~128 million |
| Power | < 1 W (typical) |
| Process | Intel 4 (7 nm) |
| Learning | On-chip (spike-timing-dependent plasticity) |

**IBM TrueNorth** (2014):
| Feature | Specification |
|---------|---------------|
| Neuron cores | 4,096 |
| Neurons per chip | 1 million |
| Synapses per chip | 256 million |
| Power | 70 mW (typical) |
| Process | Samsung 28 nm |

Neuromorphic chips excel at event-driven processing (e.g., event cameras, spike-based sensors) where traditional frame-based processing wastes computation on redundant data. However, neuromorphic computing is currently unsuitable for LLM inference because transformer attention mechanisms do not map efficiently to spike-based computation. Research is ongoing on "neuromorphic transformers" that could bridge this gap.

### 8.4 Analog and In-Memory Computing

Analog computing performs neural network multiplications directly in the memory array using analog circuits (e.g., resistive RAM crossbars), eliminating the von Neumann bottleneck of separate memory and compute units.

| Technology | Company | Key Advantage | Maturity |
|------------|---------|--------------|----------|
| Analog-in-memory (ReRAM) | Mythic, Tetramem | 10–50 TOPS/W | Early production |
| Digital-in-memory (SRAM compute) | Syntiant, Gyrfalcon | Low latency, high efficiency | Production |
| Flash-based compute | Mythic M1076 | 25 TOPS at 3 W | Production |
| Phase-change memory | IBM, Samsung | Non-volatile, radiation-hard | Research |

The key advantage of in-memory computing is energy efficiency: by performing multiply-accumulate operations where the weights are stored, the energy cost of fetching weights from external memory is eliminated. This can improve energy efficiency by 10–100× compared to traditional digital architectures.

For the NEXUS platform, analog computing could enable future ESP32-class devices to run significantly larger models (10–100× more parameters) at the same power budget — potentially enabling TinyML models with millions of parameters on microcontrollers. However, the technology is not yet mature enough for production deployment.

### 8.5 Photonic Computing

Photonic computing uses light (photons) instead of electrons to perform neural network computations. Photonic processors can perform matrix multiplication at the speed of light, offering the potential for ultra-low-latency inference.

| Company | Technology | Performance Claim | Status |
|---------|-----------|------------------|--------|
| Lightmatter | Photonic interconnect + compute | 100× speedup for attention | Research |
| Luminous Computing | Photonic AI accelerator | 10,000 TOPS/W (claimed) | Bankrupt (2024) |
| Salience Labs | Photonic-electronic hybrid | 100 TOPS at < 1 W | Early prototype |
| Intel | Silicon photonics research | Photonic interconnect | Research |

Photonic computing remains firmly in the research stage for AI inference. The challenges of integrating photonic components with electronic control logic, managing thermal effects, and achieving sufficient precision for neural network weights have proven more difficult than initial projections suggested. Photonic computing is not expected to impact edge AI deployment within the NEXUS platform's 3–5 year development horizon.

---

## 9. Edge AI Safety

### 9.1 Adversarial Robustness on Edge

Adversarial attacks — carefully crafted inputs designed to cause model misclassification — are a significant concern for edge AI systems deployed in safety-critical environments. Edge AI systems face unique adversarial challenges:

| Attack Vector | Description | Edge AI Impact | Mitigation |
|--------------|-------------|---------------|------------|
| Physical adversarial patches | Printed patterns applied to objects | Vision misclassification (stop sign → speed limit) | adversarial training, input validation |
| Sensor spoofing | Injected signals into sensor inputs | GPS spoofing, IMU manipulation | sensor redundancy, plausibility checks |
| Digital adversarial examples | Crafted input perturbations | Classification/decision errors | adversarial training, certified defenses |
| Model extraction | Query-based theft of model parameters | IP theft, targeted attacks | rate limiting, query obfuscation |
| Backdoor attacks | Poisoned training data or models | Hidden triggers for malicious behavior | model verification, anomaly detection |

For the NEXUS platform, the primary adversarial concern is **physical adversarial attacks on the vision system** (e.g., adversarial patches on navigation buoys or other vessels) and **sensor spoofing** (GPS spoofing to cause navigation errors). The NEXUS safety architecture mitigates these through:

1. **Multi-sensor fusion**: Vision alone does not drive navigation decisions; radar, sonar, GPS, and IMU inputs are cross-validated
2. **Plausibility checks**: The [[safety system|specs/safety/safety_system_spec.md]] validates AI outputs against physical constraints (e.g., a vessel cannot teleport, objects cannot pass through each other)
3. **Confidence thresholds**: Low-confidence AI predictions trigger fallback to conservative behavior (reduced speed, increased safety margin)

### 9.2 Model Integrity Verification

Ensuring that the model running on an edge device is the intended model (and has not been tampered with) is critical for safety. Model integrity verification addresses:

| Threat | Description | Verification Method |
|--------|-------------|-------------------|
| Model replacement | Attacker replaces the model file with a malicious one | SHA-256 hash of model file, verified at load |
| Weight tampering | Individual weight values modified | Merkle tree of weight blocks |
| Architecture tampering | Model structure modified (layer removal/addition) | Architecture hash stored in secure enclave |
| Supply chain attack | Compromised model distributed via OTA | Digital signature verification (RSA-3072) |

The NEXUS platform uses **RSA-3072 digital signatures** for all OTA model updates, matching the ESP32-S3's Secure Boot v2 capability. Model files are signed by the NEXUS fleet authority and verified by the Jetson's secure boot chain before loading. This is described in the [[OTA provisioning configuration|vessel-platform/config/ota_provisioning_config.json]].

### 9.3 OTA Model Update Safety

Over-the-air (OTA) model updates are essential for edge AI systems (models must be improved and deployed without physical access), but they introduce risks if the update is corrupted, interrupted, or malicious.

**NEXUS OTA model update safety protocol:**

| Step | Action | Safety Mechanism |
|------|--------|-----------------|
| 1 | Download new model to staging area | A/B partition; old model remains active |
| 2 | Verify digital signature | RSA-3072 against fleet authority certificate |
| 3 | Verify file integrity | SHA-256 hash comparison |
| 4 | Run model smoke test | Execute 10 reference inputs, verify outputs |
| 5 | Run regression test | Verify accuracy on held-back test set |
| 6 | A/B swap | Atomic switch to new model |
| 7 | Health monitoring | Monitor for 30 minutes post-deployment |
| 8 | Automatic rollback | If accuracy drops > 5% or errors > 1%, revert to old model |

This protocol extends the NEXUS platform's [[A/B partition scheme for OTA updates|embedded_and_realtime_systems#91-ab-partition-scheme]] to include model-specific verification steps.

### 9.4 Certification of AI on Edge (EU AI Act Requirements)

The **EU AI Act** (Regulation 2024/1689, fully applicable August 2026) classifies AI systems into four risk categories: Unacceptable, High-Risk, Limited-Risk, and Minimal-Risk. Autonomous marine vessels using AI for navigation and control are classified as **High-Risk AI systems**, requiring compliance with Article 9–49 obligations.

**Key requirements for edge AI systems under the EU AI Act:**

| Requirement | Article | NEXUS Compliance Status |
|-------------|---------|------------------------|
| Risk management system | Art. 9 | Partial — NEXUS has safety system but no formal AI risk management |
| Data governance | Art. 10 | Gap — no formal data quality assurance for training data |
| Technical documentation | Art. 11 | Partial — model cards exist but not to EU AI Act specification |
| Record-keeping (logs) | Art. 12 | Compliant — NEXUS observation pipeline logs all decisions |
| Transparency | Art. 13 | Compliant — NEXUS uses structured JSON for explainability |
| Human oversight | Art. 14 | Compliant — INCREMENTS L0-L5 with trust score |
| Accuracy, robustness, cybersecurity | Art. 15 | Partial — accuracy measured, robustness testing incomplete |

The NEXUS platform's [[regulatory gap analysis]] identified 93 total gaps, 9 of which are CRITICAL, for full EU AI Act compliance. Closing these gaps is estimated to require ~1,158 person-days of work at a cost of $630K–$1.05M. However, the NEXUS platform's [[trust score system|specs/safety/trust_score_algorithm_spec.md]] and [[INCREMENTS autonomy framework|incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]] provide a unique competitive advantage: they partially satisfy the human oversight requirements by design, as trust scores automatically limit autonomy levels based on demonstrated system reliability.

---

## 10. Edge AI in Autonomous Systems

### 10.1 Latency Requirements for Control

Autonomous systems have strict latency requirements that vary by control tier, from sub-millisecond reflexes to multi-second cognitive processing:

| Tier | Latency Budget | Example Task | AI Requirement | NEXUS Implementation |
|------|---------------|--------------|----------------|---------------------|
| **Reflex** (Tier 1) | < 1 ms | Kill switch, collision emergency | None (deterministic logic) | ESP32-S3 reflex VM |
| **Control** (Tier 2) | 1–10 ms | PID loop, servo control | None (deterministic math) | ESP32-S3 PID scheduler |
| **Perception** (Tier 3) | 10–100 ms | Object detection, SLAM, sensor fusion | Vision models (YOLOv8) | Jetson Orin Nano |
| **Cognitive** (Tier 4) | 100–500 ms | Path planning, COLREGs reasoning | LLM (Qwen2.5-Coder-7B) | Jetson Orin Nano |
| **Deliberative** (Tier 5) | 1–60 seconds | Reflex synthesis, fleet coordination | LLM (Qwen2.5-Coder-7B) | Jetson Orin Nano + Cloud |

The NEXUS platform's **latency budget allocation** is:

```
Total sensor-to-actuator budget: 100 ms (maximum for safe marine navigation)

├── ESP32-S3 sensor acquisition: 1 ms
├── ESP32-S3 → Jetson UART transport: 2 ms
├── Jetson AI inference (perception): 15 ms (YOLOv8-Nano, 640×640)
├── Jetson AI inference (cognitive): 50 ms (context-dependent, single-token LLM)
├── Jetson → ESP32-S3 command transport: 2 ms
├── ESP32-S3 actuator response: 1 ms
└── Safety margin: 29 ms (29% headroom)
```

For the **reflex layer** (0.01–1 ms), AI is deliberately excluded. The NEXUS Reflex VM executes deterministic bytecode programs with cycle-accurate timing guarantees, as specified in [[embedded_and_realtime_systems#71-stack-vs-heap-the-fundamental-dichotomy]]. This design choice — AI for perception and cognition, deterministic logic for reflex and control — is the standard approach in safety-critical autonomous systems.

### 10.2 Sensor Fusion at Edge

Sensor fusion combines data from multiple sensors to produce more accurate and robust state estimates than any single sensor could provide. Edge AI enables real-time sensor fusion without cloud dependency.

**NEXUS sensor fusion architecture:**

| Sensor | Modality | Update Rate | Processing Location | AI Component |
|--------|----------|-------------|-------------------|-------------|
| IMU (BNO085) | Orientation, acceleration, angular velocity | 100 Hz | ESP32-S3 | None (raw data) |
| GPS/RTK | Position, velocity | 10 Hz | ESP32-S3 | None (raw data) |
| Compass (HMC5883L) | Heading | 10 Hz | ESP32-S3 | None (raw data) |
| Anemometer | Wind speed, direction | 1 Hz | ESP32-S3 | None (raw data) |
| Camera (1080p) | Visual | 30 fps | Jetson Orin Nano | YOLOv8-Nano (detection) |
| LIDAR (optional) | Range, point cloud | 10 Hz | Jetson Orin Nano | PointNet (segmentation) |
| Radar (optional) | Range, velocity | 10 Hz | Jetson Orin Nano | CFAR (detection) |
| Sonar | Depth, obstacle range | 5 Hz | Jetson Orin Nano | Threshold + clustering |

**Fusion pipeline:**

```
ESP32-S3 Layer (0.01–10 ms):
  IMU → Kalman filter (9-DOF orientation)
  GPS → Position/velocity estimation
  Compass → Heading correction
  All sensor data → UnifiedObservation (72 fields) → Jetson via RS-422

Jetson Layer (10–100 ms):
  Vision → Object detection (YOLOv8-Nano)
  LIDAR → Point cloud segmentation (PointNet)
  Radar → Target detection (CFAR algorithm)
  All → Extended Kalman Filter (EKF) → Global state estimate
  State estimate → Path planning + COLREGs compliance → Control commands

ESP32-S3 Layer:
  Control commands → Reflex VM execution → Actuator outputs
```

The [[UnifiedObservation data model|specs/jetson/learning_pipeline_spec.md]] aggregates 72 fields from all sensors into a single JSON object that is transmitted from ESP32-S3 to Jetson via the NEXUS Wire Protocol. This design decouples sensor acquisition (ESP32) from AI processing (Jetson), allowing each tier to operate independently.

### 10.3 Real-Time Inference Scheduling

Running multiple AI models concurrently on a single edge device requires careful scheduling to meet latency constraints. The Jetson Orin Nano's GPU is a shared resource, and concurrent model execution must be managed to prevent priority inversion (where a low-priority model blocks a high-priority one).

**NEXUS inference priority scheduling:**

| Priority | Model | Latency Budget | GPU Allocation | Preemption |
|----------|-------|---------------|---------------|------------|
| P0 (safety) | YOLOv8-Nano (collision detection) | < 33 ms (30 fps) | Guaranteed 50% GPU | Preemptable only by P1 |
| P1 (critical) | Object tracking | < 100 ms | Guaranteed 30% GPU | Preemptable by P0 |
| P2 (navigation) | Path planning (LLM) | < 500 ms | Shared 15% GPU | Preemptable by P0, P1 |
| P3 (interaction) | Voice recognition (Whisper) | < 5 s | Shared 5% GPU | Background |

This priority scheme ensures that safety-critical vision inference always meets its latency budget, even when the LLM is generating a long response or Whisper is processing audio. The Jetson's CUDA streams and hardware priority scheduling are used to implement this policy.

### 10.4 Failover: When Edge AI Fails

Edge AI systems must define clear failure modes and fallback behaviors. The NEXUS platform's safety architecture, documented in [[embedded_and_realtime_systems#the-nexus-four-tier-safety-architecture]] and the [[safety system specification|specs/safety/safety_system_spec.md]], defines a cascading failover strategy:

| Failure Mode | Detection | Response | Time to Safe State |
|-------------|-----------|----------|-------------------|
| **Jetson unresponsive** | ESP32 heartbeat timeout (3 missed beats, 300 ms) | Enter SAFE_STATE; ESP32 controls actuators directly | < 500 ms |
| **Vision model error** | Confidence < 50% for > 3 consecutive frames | Reduce speed; rely on radar/sonar only | < 1 s |
| **LLM hallucination** | Output fails GBNF grammar validation | Reject response; retry with more constrained prompt | < 5 s |
| **LLM timeout** | No response within 120 seconds | Fall back to pre-programmed reflex patterns | 120 s |
| **Model file corruption** | SHA-256 hash mismatch at load | Use last known good model; alert operator | < 2 s |
| **Thermal throttle** | SoC temperature > 85°C | Reduce AI workload (disable LLM, keep vision) | < 5 s |
| **Network partition** | MQTT heartbeat loss (5 seconds) | Continue edge-only operation; queue data for sync | Immediate |

**The zero-AI fallback:** If all AI components fail simultaneously (extremely unlikely given the NEXUS architecture's defense-in-depth), the ESP32-S3 nodes continue operating using pre-programmed reflex bytecode patterns. The NEXUS Reflex VM can execute up to 200 reflex patterns with deterministic timing guarantees, providing basic autonomous operation (station-keeping, collision avoidance, return-to-home) without any AI involvement. This is the ultimate safety net: the system degrades gracefully from AI-assisted autonomy to rule-based autonomy to human control.

This cascading failover strategy maps to the NEXUS platform's [[graceful degradation levels|specs/safety/safety_system_spec.md]]:

```
Level 5: Full AI autonomy (Qwen + Phi + Vision + Voice)
    │ failover
Level 4: Reduced AI (Vision only; LLM disabled)
    │ failover
Level 3: Minimal AI (basic object detection; no reasoning)
    │ failover
Level 2: Rule-based autonomy (reflex patterns only, no AI)
    │ failover
Level 1: Manual control (operator takes direct actuator control)
    │ failover
Level 0: Safe state (all actuators disabled, emergency anchoring)
```

---

## 11. References and Further Reading

1. Shi, W., Cao, J., Zhang, Q., Li, Y., & Xu, L. (2016). "Edge Computing: Vision and Challenges." *IEEE Internet of Things Journal*, 3(5), 637–646.

2. Lin, J., Chen, W., Lin, Y., Cohn, J., Gan, C., & Han, S. (2020). "MCUNet: Tiny Deep Learning on IoT Devices." *NeurIPS 2020*.

3. Han, S., Mao, H., & Dally, W. J. (2016). "Deep Compression: Compressing Deep Neural Networks with Pruning, Trained Quantization and Huffman Coding." *ICLR 2016*.

4. Hinton, G., Vinyals, O., & Dean, J. (2015). "Distilling the Knowledge in a Neural Network." *NeurIPS 2015 Workshop*.

5. Frankle, J., & Carlin, M. (2019). "The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks." *ICLR 2019*.

6. Tan, M., & Le, Q. V. (2019). "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks." *ICML 2019*.

7. Gerganov, G. (2023). "llama.cpp: LLM Inference in C/C++." GitHub repository. https://github.com/ggerganov/llama.cpp

8. Frantar, E., Ashkboos, S., Hoefler, T., & Alistarh, D. (2022). "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers." *arXiv:2210.17323*.

9. Lin, J., Tang, J., Tang, H., Yang, S., Dang, X., Gan, C., & Han, S. (2023). "AWQ: Activation-Aware Weight Quantization for LLM Compression and Acceleration." *arXiv:2306.00978*.

10. Dettmers, T., Lewis, M., Belkada, Y., & Zettlemoyer, L. (2022). "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale." *NeurIPS 2022*.

11. NVIDIA Corporation (2023). "NVIDIA Jetson Orin Technical Reference Manual."

12. Espressif Systems (2023). "ESP32-S3 Technical Reference Manual."

13. Abadi, M. et al. (2016). "TensorFlow: A System for Large-Scale Machine Learning." *OSDI 2016*.

14. Zhang, A., Li, J., & Ding, Y. (2024). "Qwen2.5-Coder Technical Report." *arXiv:2409.12186*.

15. Radford, A. et al. (2023). "Robust Speech Recognition via Large-Scale Weak Supervision." *arXiv:2212.04356* (Whisper).

16. European Parliament (2024). "Regulation (EU) 2024/1689 — Artificial Intelligence Act."

17. IEC 61508 (2010). "Functional Safety of Electrical/Electronic/Programmable Electronic Safety-Related Systems."

18. Warden, P. & Situnayake, D. (2019). *TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers.* O'Reilly Media.

19. Jacob, B. et al. (2018). "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *arXiv:1712.05877* (TFLite quantization).

20. Moreau, T., et al. (2019). "TVM: An Automated End-to-End Optimizing Compiler for Deep Learning." *OSDI 2019*.

---

**Related articles:** [[embedded_and_realtime_systems]], [[distributed_systems]], [[marine_autonomous_systems]], [[robotics_control_history]], [[evolutionary_computation]], [[formal_verification_and_safety]]

**Cross-references to NEXUS specifications:**
- [[Reflex Bytecode VM Specification|specs/firmware/reflex_bytecode_vm_spec.md]]
- [[Safety System Specification|specs/safety/safety_system_spec.md]]
- [[Trust Score Algorithm Specification|specs/safety/trust_score_algorithm_spec.md]]
- [[Jetson Cluster Architecture|vessel-platform/11_jetson_cluster_architecture.txt]]
- [[Memory Map and Partition Specification|specs/firmware/memory_map_and_partitions.md]]
- [[Learning Pipeline Specification|specs/jetson/learning_pipeline_spec.md]]
- [[OTA Provisioning Configuration|vessel-platform/config/ota_provisioning_config.json]]
- [[Architecture Decision Records|specs/ARCHITECTURE_DECISION_RECORDS.md]]
- [[Performance Budgets and Optimization|addenda/02_Performance_Budgets_and_Optimization.md]]
- [[INCREMENTS Autonomy Framework|incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]]
