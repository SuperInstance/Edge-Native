# NEXUS Platform Cross-Domain Application Analysis

## Round 2A — Deep Research Deliverable 1
**Version:** 1.0 | **Date:** 2026-03-29 | **Task ID:** 2A

---

## Table of Contents

1. [Introduction and Methodology](#1-introduction-and-methodology)
2. [Domain 1: Marine Vessels](#2-domain-1-marine-vessels)
3. [Domain 2: Agricultural Equipment](#3-domain-2-agricultural-equipment)
4. [Domain 3: Factory Automation](#4-domain-3-factory-automation)
5. [Domain 4: Mining Operations](#5-domain-4-mining-operations)
6. [Domain 5: HVAC Systems](#6-domain-5-hvac-systems)
7. [Domain 6: Home Automation](#7-domain-6-home-automation)
8. [Domain 7: Healthcare Robotics](#8-domain-7-healthcare-robotics)
9. [Domain 8: Autonomous Vehicles (Ground)](#9-domain-8-autonomous-vehicles-ground)
10. [Cross-Domain Safety Policy Analysis](#10-cross-domain-safety-policy-analysis)
11. [Trust Score Calibration Across Domains](#11-trust-score-calibration-across-domains)
12. [INCREMENTS Framework Autonomy Mapping](#12-increments-framework-autonomy-mapping)
13. [Sensor and Actuator Cost Analysis](#13-sensor-and-actuator-cost-analysis)
14. [Regulatory Burden Comparison](#14-regulatory-burden-comparison)
15. [Market Size and Competitive Landscape](#15-market-size-and-competitive-landscape)
16. [Universal vs. Domain-Specific Feature Decomposition](#16-universal-vs-domain-specific-feature-decomposition)
17. [Research Challenges Synthesis](#17-research-challenges-synthesis)
18. [Conclusions and Recommendations](#18-conclusions-and-recommendations)

---

## 1. Introduction and Methodology

### 1.1 Purpose

This document provides a comprehensive analysis of eight target domains for the NEXUS distributed intelligence platform. For each domain, we evaluate the applicability of the NEXUS architecture, identify domain-specific safety requirements, estimate hardware costs, map applicable autonomy levels from the INCREMENTS framework, and identify key research challenges.

### 1.2 Methodology

Our analysis follows a structured framework:

1. **Regulatory mapping** — Identify all applicable standards, certifications, and compliance requirements
2. **Safety policy extension** — Extend the NEXUS `safety_policy.json` schema with domain-specific rules
3. **Hardware profiling** — Estimate sensor/actuator counts and per-node BOM costs
4. **Trust calibration** — Derive domain-appropriate alpha_gain and alpha_loss parameters based on risk profiles
5. **Autonomy mapping** — Map domain use cases to INCREMENTS levels L0–L5
6. **Market analysis** — Estimate market size, existing solutions, and competitive positioning
7. **Research challenge identification** — Enumerate open problems specific to each domain

### 1.3 NEXUS Architecture Context

The NEXUS platform is a distributed intelligence system with:
- **ESP32 sensor/actuator nodes** running a 32-opcode reflex bytecode VM
- **Jetson cognitive cluster** for learning, trust scoring, and autonomy management
- **RS-422 serial links** with COBS framing at 921600 baud
- **Trust score algorithm** with 12 parameters, asymmetric gain/loss (25:1 ratio), and 6 autonomy levels (L0–L5)
- **Safety policy engine** with 10 global rules, domain-specific overrides, and a 6-stage validation pipeline

The platform was originally designed for **marine autopilot** as its primary domain, but the architecture is intentionally generalizable.

---

## 2. Domain 1: Marine Vessels

### 2.1 Domain Overview

Marine vessels represent the **reference domain** for NEXUS. The platform's design origins in marine autopilot provide a strong foundation for extension.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Autopilot (heading/course) | CRITICAL | < 100 ms | High |
| Dynamic Positioning (DP) | CRITICAL | < 50 ms | Very High |
| Engine Management | HIGH | < 500 ms | Medium |
| Bilge Monitoring | MEDIUM | < 1 s | Low |
| Anchor Winch Control | HIGH | < 200 ms | Medium |
| Collision Avoidance | CRITICAL | < 50 ms | Very High |
| Navigation Lights | MEDIUM | < 1 s | Low |
| Fire Detection | CRITICAL | < 1 s | Medium |

### 2.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **IMO MSC.252(83)** | IMO Performance Standards for Radar | Defines sensor integration requirements for collision avoidance |
| **SOLAS Chapter V** | Safety of Navigation | Mandates bridge equipment, AIS, voyage data recording |
| **IEC 60945** | Maritime Navigation and Radiocommunication Equipment | Environmental testing, EMC, safety for marine electronics |
| **IEC 62288** | Presentation of Navigation Information | UI/UX standards for navigation displays |
| **ISO 16315** | Small Craft — Autopilots | Directly applicable to NEXUS marine autopilot |
| **ABYC A-33** | Diesel Engine Control Systems | Engine management safety requirements |
| **IEC 61162** | Maritime Navigation Equipment (NMEA) | Data interchange protocols for marine sensors |
| **IALA O-139** | AIS Shore Station Requirements | AIS data format and processing |

### 2.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "marine": {
      "domain_id": "marine",
      "compliance_refs": ["IEC 60945", "ABYC A-33", "ISO 16315", "IMO MSC.252(83)", "SOLAS V"],
      "overrides": {
        "max_rudder_deflection_deg": { "value": 45, "unit": "degrees" },
        "max_throttle_percent": { "value": 80, "unit": "percent" },
        "depth_min_for_autopilot_m": { "value": 3.0, "unit": "meters" },
        "max_speed_autonomous_kmh": { "value": 15.0, "unit": "km/h" },
        "max_wind_speed_autonomous_kmh": { "value": 40.0, "unit": "km/h" }
      },
      "domain_rules": [
        {
          "id": "MR-001",
          "title": "Depth-Limited Autopilot Engagement",
          "description": "Autopilot shall not engage below minimum depth threshold. GPS accuracy is insufficient in shallow water for safe autonomous navigation.",
          "severity": "CRITICAL",
          "sensor_dependency": ["depth_sounder"],
          "safe_state": "disengage_autopilot"
        },
        {
          "id": "MR-002",
          "title": "AIS Collision Proximity Alert",
          "description": "When AIS targets are within CPA threshold and TCPA < 5 minutes, trigger alarm and recommend course change. If TCPA < 2 minutes, initiate evasive maneuver.",
          "severity": "CRITICAL",
          "sensor_dependency": ["ais_receiver", "gps", "compass"],
          "safe_state": "reduced_speed_and_alarm"
        },
        {
          "id": "MR-003",
          "title": "MOB (Man Overboard) Emergency Response",
          "description": "MOB activation shall immediately mark position, disengage autopilot, and display bearing/range to MOB position. Option for auto-return.",
          "severity": "CRITICAL",
          "sensor_dependency": ["gps", "mob_button"],
          "safe_state": "stop_and_mark"
        },
        {
          "id": "MR-004",
          "title": "Bilge High-Water Engine Shutdown",
          "description": "If bilge water exceeds critical level, engine must shut down to prevent water ingestion through exhaust.",
          "severity": "HIGH",
          "sensor_dependency": ["bilge_float_switch", "bilge_water_level"],
          "safe_state": "engine_stop"
        },
        {
          "id": "MR-005",
          "title": "Anchor Drag Detection",
          "description": "Monitor GPS position relative to anchor drop point. If vessel drifts beyond threshold, trigger anchor drag alarm.",
          "severity": "MEDIUM",
          "sensor_dependency": ["gps", "anchor_winch_sensor"],
          "safe_state": "alarm_only"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [-15, 55],
        "humidity_max_percent": 95,
        "ingress_protection": "IP67",
        "vibration_tolerance": "IEC 60945 Category A",
        "salt_spray_resistance": true,
        "surge_protection": true
      }
    }
  }
}
```

### 2.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| GPS (RTK-capable) | UART NMEA 0183 | 1 | 250–800 | CRITICAL |
| Magnetic Compass (3-axis) | I2C | 1 | 15–50 | CRITICAL |
| IMU (9-DOF) | I2C/SPI | 1 | 10–30 | HIGH |
| AIS Receiver | UART | 1 | 150–500 | CRITICAL |
| Radar (X-band, 72 RPM) | Ethernet | 1 | 2000–8000 | HIGH |
| Sonar/Depth Sounder | NMEA 2000 | 1 | 200–600 | HIGH |
| Wind Sensor (anemometer) | NMEA 2000 | 1 | 300–800 | MEDIUM |
| Water Temperature | 1-Wire / Analog | 1 | 5–15 | LOW |
| Bilge Level Sensor | GPIO float switch | 2–4 | 5–10 ea | HIGH |
| Engine RPM Sensor | Frequency/Counter | 1 | 20–50 | HIGH |
| Fuel Flow Meter | Frequency | 1 | 100–300 | MEDIUM |

**Estimated total sensor cost per vessel node: $3,100–$11,200**

### 2.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Steering Servo / Actuator | motor_pwm | 1 | 500–3000 | CRITICAL |
| Throttle Actuator | motor_pwm | 1 | 200–800 | CRITICAL |
| Anchor Winch Motor | motor_pwm | 1 | 300–1500 | HIGH |
| Bilge Pump | relay | 2–4 | 50–150 ea | HIGH |
| Navigation Lights | relay | 4–8 | 20–50 ea | MEDIUM |
| Horn / Alarm | buzzer | 1 | 30–100 | MEDIUM |
| Engine Kill Switch | relay | 1 | 20–50 | CRITICAL |

**Estimated total actuator cost per vessel node: $1,400–$6,000**

### 2.6 INCREMENTS Autonomy Level Mapping

| Level | Marine Application | Requirements |
|-------|-------------------|--------------|
| L0 — Manual | All basic operations | Manual steering, throttle, anchor |
| L1 — Assisted | Autopilot heading hold with human confirmation | Course correction suggestions |
| L2 — Supervised | Autopilot course tracking, auto-anchoring | Human monitors at all times |
| L3 — Conditional | Dynamic positioning, auto-trim | Human available within 30s response |
| L4 — High | Fully autonomous navigation (open water) | Periodic check-ins, remote monitoring |
| L5 — Full | Autonomous passage planning + execution | Remote oversight only |

### 2.7 Trust Score Parameters

```json
{
  "marine": {
    "trust_parameters": {
      "subsystem_weights": {
        "steering": { "weight": 1.0, "risk_factor": 1.2 },
        "engine": { "weight": 0.9, "risk_factor": 1.0 },
        "navigation": { "weight": 1.0, "risk_factor": 1.1 },
        "collision_avoidance": { "weight": 1.0, "risk_factor": 1.3 },
        "bilge_monitoring": { "weight": 0.5, "risk_factor": 0.7 },
        "anchor_system": { "weight": 0.7, "risk_factor": 0.9 }
      },
      "alpha_gain_default": 0.04,
      "alpha_loss_default": 1.0,
      "recommended_ratio": "25:1",
      "rationale": "Marine operations have high consequence of failure (drowning, collision, grounding). Trust should accumulate slowly and be very sensitive to safety events. 25:1 ratio validated by Round 1B simulation showing 45-day path to L4 with no false autonomy under 5% bad events."
    }
  }
}
```

### 2.8 Market Size and Existing Solutions

**Global Market:** The autonomous marine technology market is projected at **$4.5B by 2027** (CAGR 12.3%).

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| Autopilot Evolution | Garmin | Heading/course hold, sail assist | Limited learning, fixed algorithms |
| SeaPilot | Furuno | Radar/AIS integration, route planning | No adaptive behavior |
| AP Mk3 | Raymarine | Advanced autopilot with wind compensation | Not open, no extensibility |
| SmartSteer | Simrad | Autosteering with waypoint nav | No reflex learning |
| ROS-based USV | Various academic | Full autonomy stack | Not production-grade |

**NEXUS Competitive Advantage:** Reflex bytecode VM for real-time response, trust-score-gated autonomy, learned pattern incorporation.

### 2.9 Key Research Challenges

1. **GPS-denied navigation** — Harbors, canals, and high-latitude regions have degraded GPS. Fusion with IMU, radar, and visual landmarks is needed.
2. **Sea-state adaptive control** — Wave patterns are non-stationary; control parameters must adapt to changing conditions without destabilizing.
3. **Maritime V2V communication** — Inter-vessel coordination for collision avoidance requires standardized protocols beyond AIS.
4. **Corrosion and biofouling** — Long-term deployment in saltwater degrades sensors and actuators; self-diagnostic calibration is critical.
5. **Regulatory approval pathway** — No existing framework for certifying learned/adaptive autopilot behaviors. IEC 60945 assumes static firmware.

---

## 3. Domain 2: Agricultural Equipment

### 3.1 Domain Overview

Agricultural automation is experiencing rapid growth driven by labor shortages, precision agriculture economics, and sustainability mandates.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Precision Irrigation | MEDIUM | < 5 s | Medium |
| Variable-Rate Fertilization | MEDIUM | < 2 s | High |
| Harvest Timing Optimization | LOW | < 60 s | High |
| Greenhouse Climate Control | MEDIUM | < 10 s | High |
| Crop Monitoring Drones | LOW | < 1 s | Medium |
| Spraying Operations | HIGH | < 500 ms | High |
| Autonomous Tractor Navigation | HIGH | < 200 ms | Very High |
| PTO Safety Interlock | CRITICAL | < 50 ms | Medium |

### 3.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **ISO 11783 (ISOBUS)** | Agricultural machinery communication | Defines sensor/actuator data interchange protocol |
| **ISO 4254-1** | Agricultural machinery — Safety | General safety requirements for agricultural machines |
| **ASABE EP366** | Safety for Agricultural Equipment | US-specific safety standards |
| **EN ISO 3691-4** | Driverless industrial trucks | Autonomous vehicle safety in mixed environments |
| **EPA Regulation 40 CFR Part 170** | Worker Protection Standard | Chemical application safety |
| **ISO 25119** | Tractors and machinery — Safety-related control systems | Functional safety for agricultural electronics |

### 3.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "agriculture": {
      "domain_id": "agriculture",
      "compliance_refs": ["ISO 11783", "ISO 4254-1", "ASABE EP366", "EN ISO 3691-4", "EPA 40 CFR 170"],
      "overrides": {
        "max_spray_pressure_psi": { "value": 80, "unit": "psi" },
        "max_vehicle_speed_kmh": { "value": 15, "unit": "km/h" },
        "max_spray_flow_rate_lpm": { "value": 20, "unit": "liters per minute" },
        "proximity_stop_distance_m": { "value": 2.0, "unit": "meters" },
        "max_implement_width_m": { "value": 30.0, "unit": "meters" }
      },
      "domain_rules": [
        {
          "id": "AG-001",
          "title": "Geofence Boundary Enforcement",
          "description": "Autonomous equipment shall not operate outside geofenced field boundaries. Implement width offsets for wide implements.",
          "severity": "CRITICAL",
          "sensor_dependency": ["gps_rtk", "implement_width"],
          "safe_state": "stop_and_alarm"
        },
        {
          "id": "AG-002",
          "title": "Rollover Detection and Engine Kill",
          "description": "IMU-based rollover angle monitoring. If tilt exceeds threshold (e.g., 25 degrees), immediately kill engine and PTO.",
          "severity": "CRITICAL",
          "sensor_dependency": ["imu", "engine_rpm"],
          "safe_state": "engine_stop_and_pto_disengage"
        },
        {
          "id": "AG-003",
          "title": "PTO Safety Interlock",
          "description": "PTO shall only engage when: (a) operator present or (b) L3+ autonomy confirmed, implement properly attached, no personnel in proximity zone.",
          "severity": "CRITICAL",
          "sensor_dependency": ["operator_presence", "proximity_sensors", "pto_rpm"],
          "safe_state": "pto_disengage"
        },
        {
          "id": "AG-004",
          "title": "Chemical Spill Containment",
          "description": "Monitor spray system pressure and flow. If leak detected (pressure drop without valve opening), close master valve and alert.",
          "severity": "HIGH",
          "sensor_dependency": ["spray_pressure", "flow_meter", "master_valve"],
          "safe_state": "close_master_valve_and_alarm"
        },
        {
          "id": "AG-005",
          "title": "Livestock/Animal Proximity Detection",
          "description": "Thermal and proximity sensors must detect animals in vehicle path. Minimum 5m detection range for wildlife, 10m for livestock herds.",
          "severity": "HIGH",
          "sensor_dependency": ["thermal_camera", "proximity_radar", "lidar"],
          "safe_state": "stop_and_alarm"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [-20, 55],
        "humidity_max_percent": 100,
        "ingress_protection": "IP66",
        "vibration_tolerance": "ISO 4254-1 Class III",
        "dust_resistance": true,
        "uv_resistance": true
      }
    }
  }
}
```

### 3.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| GPS RTK Base+Rover | UART/RTCM | 1 set | 3000–8000 | CRITICAL |
| IMU (6-DOF) | I2C | 1 | 10–25 | HIGH |
| Soil Moisture (TDR) | Analog/I2C | 4–12 | 25–80 ea | MEDIUM |
| NDVI Multispectral Camera | SPI/UART | 1 | 500–2000 | LOW |
| Weather Station (T/H/W/S) | I2C/UART | 1 | 200–600 | MEDIUM |
| Proximity Radar (77 GHz) | CAN/UART | 2–4 | 100–300 ea | HIGH |
| Thermal Camera | USB/I2C | 1 | 300–1500 | MEDIUM |
| Flow Meter (spray) | Frequency | 2–4 | 50–150 ea | HIGH |
| Pressure Sensor (spray) | I2C | 1–2 | 15–40 ea | HIGH |
| PTO RPM Sensor | Frequency | 1 | 15–30 | CRITICAL |
| Operator Presence Switch | GPIO | 1 | 10–25 | CRITICAL |

**Estimated total sensor cost per node: $5,000–$16,000**

### 3.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Steering Actuator | motor_pwm | 1 | 300–1200 | HIGH |
| Throttle Actuator | motor_pwm | 1 | 150–500 | HIGH |
| Spray Valves (section) | solenoid | 4–16 | 15–40 ea | HIGH |
| Master Spray Valve | solenoid | 1 | 50–100 | CRITICAL |
| PTO Clutch | relay | 1 | 20–50 | CRITICAL |
| Implement Lift | motor_pwm | 1 | 200–600 | HIGH |
| Irrigation Valves | solenoid | 4–24 | 10–30 ea | MEDIUM |

**Estimated total actuator cost per node: $1,200–$3,500**

### 3.6 INCREMENTS Autonomy Level Mapping

| Level | Agricultural Application | Requirements |
|-------|-------------------------|--------------|
| L0 — Manual | All field operations | Driver-operated |
| L1 — Assisted | GPS guidance display, auto-section control | Driver confirms actions |
| L2 — Supervised | Autosteering on rows, auto-spray section | Driver in cab, ready to take over |
| L3 — Conditional | Autonomous tillage/spraying (no driver) | Remote operator available |
| L4 — High | Fully autonomous field operations | Remote monitoring |
| L5 — Full | Fleet coordination, adaptive operations | Fully unsupervised fleet |

### 3.7 Trust Score Parameters

```json
{
  "agriculture": {
    "trust_parameters": {
      "subsystem_weights": {
        "steering": { "weight": 1.0, "risk_factor": 0.9 },
        "spray_system": { "weight": 0.8, "risk_factor": 1.1 },
        "navigation": { "weight": 1.0, "risk_factor": 0.8 },
        "pto_system": { "weight": 1.0, "risk_factor": 1.3 },
        "irrigation": { "weight": 0.4, "risk_factor": 0.5 }
      },
      "alpha_gain_default": 0.06,
      "alpha_loss_default": 0.8,
      "recommended_ratio": "13:1",
      "rationale": "Agricultural operations have moderate consequence of failure (crop damage, not typically life-threatening). Lower risk ratio allows faster trust accumulation for efficiency, but chemical application (spray_system) retains higher loss sensitivity."
    }
  }
}
```

### 3.8 Market Size and Existing Solutions

**Global Market:** Precision agriculture market projected at **$16.7B by 2028** (CAGR 12.7%). Agricultural robot market at **$20.6B by 2028**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| AutoTrac | John Deere | GPS-guided steering, section control | Closed ecosystem, no learning |
| AgriCaptain | CLAAS | Autosteering, ISOBUS integration | Limited autonomy levels |
| RowCrop Pro | Trimble | RTK guidance, field mapping | No adaptive behavior |
| See & Spray | Blue River (JD) | ML-based weed detection/spraying | Vision-only, not full platform |
| DOT | Saskatchewan Farming | Autonomous platform for implements | Limited to specific implements |
| XAG Agricultural Drone | XAG | Autonomous spraying drones | Drone-specific, not ground vehicles |

### 3.9 Key Research Challenges

1. **Non-uniform terrain** — Fields have ditches, rocks, mud, and slopes that challenge vehicle dynamics models. Real-time terrain classification is needed.
2. **Environmental variability** — Weather, soil conditions, and crop growth stages create a non-stationary operational environment that invalidates fixed control parameters.
3. **ISOBUS integration** — Interfacing with existing ISOBUS implement electronics requires reverse engineering of proprietary protocols from major OEMs.
4. **Chemical application optimization** — Balancing spray efficacy with drift and environmental contamination requires real-time wind/cloud modeling beyond simple sensor thresholds.
5. **Long-range coordination** — Multi-vehicle fleet operations across thousands of acres require mesh networking beyond the RS-422 point-to-point links NEXUS currently supports.

---

## 4. Domain 3: Factory Automation

### 4.1 Domain Overview

Factory automation is the most mature of the eight domains, with well-established standards and significant existing investment in industrial control systems.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Conveyor Speed Control | HIGH | < 50 ms | Low |
| Quality Inspection (Vision) | MEDIUM | < 200 ms | High |
| Safety Interlock Monitoring | CRITICAL | < 10 ms | Medium |
| Robotic Welding Control | CRITICAL | < 10 ms | Very High |
| Packaging Line Orchestration | MEDIUM | < 100 ms | High |
| Collaborative Robot (Cobot) Control | CRITICAL | < 5 ms | Very High |
| Material Handling AGV | HIGH | < 100 ms | High |
| Predictive Maintenance | LOW | < 60 s | Medium |

### 4.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **ISO 10218-1/2** | Industrial robots — Safety requirements | Robot cell safety design and operation |
| **ISO/TS 15066** | Collaborative robots — Safety | Force/pressure limits for human contact |
| **IEC 62443** | Industrial automation cybersecurity | Network security, access control |
| **IEC 62061** | Safety of machinery — Functional safety | SIL assignments for safety functions |
| **ISO 13849** | Safety of machinery — Safety parts | Performance levels (PL a–e) |
| **OSHA 29 CFR 1910** | General industry safety standards | US workplace safety mandates |
| **IEC 61131-3** | Programmable controllers — Languages | PLC programming standard (comparison point) |

### 4.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "factory": {
      "domain_id": "factory",
      "compliance_refs": ["ISO 10218-1", "ISO/TS 15066", "IEC 62443", "IEC 62061", "ISO 13849", "OSHA 1910.212"],
      "overrides": {
        "min_proximity_m": { "value": 0.3, "unit": "meters" },
        "max_robot_speed_m_s": { "value": 1.0, "unit": "m/s" },
        "max_robot_force_n": { "value": 150, "unit": "Newtons" },
        "safety_zone_violation_action": { "value": "immediate_stop_and_alarm" },
        "max_conveyor_speed_m_s": { "value": 2.0, "unit": "m/s" }
      },
      "domain_rules": [
        {
          "id": "FA-001",
          "title": "Collaborative Robot Force Limiting",
          "description": "Cobots operating in shared workspace must continuously monitor force/torque sensors. If transient contact force exceeds ISO/TS 15066 body-region thresholds, immediate soft-stop.",
          "severity": "CRITICAL",
          "sensor_dependency": ["force_torque_sensor", "proximity"],
          "safe_state": "soft_stop_and_retract"
        },
        {
          "id": "FA-002",
          "title": "Safety Zone Boundary Enforcement",
          "description": "LIDAR-based safety zones must be continuously monitored. Zone violation triggers immediate stop of all robots in the cell. Recovery requires manual reset.",
          "severity": "CRITICAL",
          "sensor_dependency": ["lidar", "safety_scanner"],
          "safe_state": "immediate_stop_zone"
        },
        {
          "id": "FA-003",
          "title": "Emergency Stop Category 0/1",
          "description": "All E-Stop circuits must meet IEC 60204-1 Category 0 (uncontrolled stop) or Category 1 (controlled stop with power removal). NEXUS kill switch provides Category 0; controlled deceleration provides Category 1.",
          "severity": "CRITICAL",
          "sensor_dependency": ["estop_buttons", "safety_mats"],
          "safe_state": "power_removal"
        },
        {
          "id": "FA-004",
          "title": "Robot-Side Safety PLC Supervision",
          "description": "NEXUS safety decisions shall be supervised by an independent safety PLC (PLe/SIL 3) for any application where ISO 13849 PL d or higher is required. NEXUS acts as the primary controller; safety PLC provides the safety layer.",
          "severity": "HIGH",
          "sensor_dependency": ["safety_plc_feedback"],
          "safe_state": "safety_plc_override"
        },
        {
          "id": "FA-005",
          "title": "Conveyor Jam Detection",
          "description": "Monitor conveyor motor current and encoder speed. If current exceeds nominal by 2x or speed drops below 50% of setpoint, stop conveyor and alert.",
          "severity": "MEDIUM",
          "sensor_dependency": ["motor_current", "encoder"],
          "safe_state": "conveyor_stop"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [0, 50],
        "humidity_max_percent": 85,
        "ingress_protection": "IP54",
        "vibration_tolerance": "IEC 60068-2-6",
        "emc_compliance": "IEC 61000-6-2/4",
        "cleanroom_compatible": "optional"
      }
    }
  }
}
```

### 4.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| LIDAR Safety Scanner | Ethernet | 1–2 | 2000–5000 | CRITICAL |
| Force/Torque Sensor (6-axis) | CAN/Ethernet | 1–2 | 500–3000 | CRITICAL |
| Proximity Sensor (capacitive) | I2C/GPIO | 4–12 | 20–80 ea | HIGH |
| Vision Camera (industrial) | GigE/USB | 1–4 | 300–2000 ea | MEDIUM |
| Encoder (motor feedback) | Quadrature/SSI | 2–6 | 50–300 ea | HIGH |
| Current Sensor (per motor) | Analog/I2C | 2–8 | 10–40 ea | HIGH |
| Safety Light Curtain | Safety I/O | 1–4 | 500–2000 ea | CRITICAL |
| Safety Mat / Floor Sensor | Safety I/O | 2–6 | 100–400 ea | CRITICAL |
| Temperature (motor/bearing) | I2C/1-Wire | 2–6 | 5–15 ea | MEDIUM |
| Vibration Sensor | I2C/SPI | 2–4 | 50–200 ea | MEDIUM |

**Estimated total sensor cost per cell node: $6,000–$30,000**

### 4.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Servo Motor (joint) | motor_pwm | 2–6 | 200–1500 ea | HIGH |
| Conveyor Drive | motor_pwm | 1–4 | 300–1000 ea | HIGH |
| Pneumatic Valve | solenoid | 2–8 | 20–80 ea | MEDIUM |
| Robot Gripper | servo + motor_pwm | 1–2 | 300–2000 ea | HIGH |
| Indicator Stack Light | led/relay | 1–2 | 50–200 | LOW |
| Safety Relay Driver | relay | 1–4 | 20–60 ea | CRITICAL |

**Estimated total actuator cost per cell node: $2,000–$15,000**

### 4.6 INCREMENTS Autonomy Level Mapping

| Level | Factory Application | Requirements |
|-------|-------------------|--------------|
| L0 — Manual | Manual tool operation | Operator controls all axes |
| L1 — Assisted | Guided assembly, quality alerts | Operator confirms each step |
| L2 — Supervised | Repeating programmed tasks, human co-exists | Continuous operator monitoring |
| L3 — Conditional | Adaptive pick-and-place, batch optimization | Remote supervisor available |
| L4 — High | Multi-cell coordination, self-optimizing lines | Periodic check-ins |
| L5 — Full | Lights-out manufacturing, self-reconfiguring cells | Remote oversight only |

### 4.7 Trust Score Parameters

```json
{
  "factory": {
    "trust_parameters": {
      "subsystem_weights": {
        "robot_motion": { "weight": 1.0, "risk_factor": 1.3 },
        "conveyor_system": { "weight": 0.6, "risk_factor": 0.8 },
        "quality_inspection": { "weight": 0.5, "risk_factor": 0.4 },
        "safety_interlocks": { "weight": 1.0, "risk_factor": 1.5 },
        "material_handling": { "weight": 0.7, "risk_factor": 0.9 }
      },
      "alpha_gain_default": 0.03,
      "alpha_loss_default": 1.2,
      "recommended_ratio": "40:1",
      "rationale": "Factory environments have high personnel density with severe injury potential. Trust must accumulate very slowly with extreme sensitivity to safety events. The 40:1 ratio reflects the highest safety bar of all domains, comparable to SIL 3 / PLe requirements."
    }
  }
}
```

### 4.8 Market Size and Existing Solutions

**Global Market:** Industrial automation market projected at **$265B by 2027** (CAGR 8.9%). Collaborative robot market at **$9.2B by 2028** (CAGR 32.8%).

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| ROS 2 Industrial | Open Robotics | Full robot middleware | Not safety-certified, complex setup |
| PLC Systems | Siemens, Rockwell | SIL 3 safety PLCs | No learning, rigid programming |
| UR e-Series | Universal Robots | Cobot with force limiting | Limited extensibility |
| FANUC FIELD System | FANUC | Robot analytics, edge computing | Proprietary, not general-purpose |
| Ignition | Inductive Automation | SCADA/HMI platform | No reflex-level control |

### 4.9 Key Research Challenges

1. **Hard real-time guarantees** — Factory safety requires deterministic sub-10ms response. The NEXUS VM must guarantee cycle timing in the presence of LLM inference and MQTT traffic on the Jetson.
2. **Certification pathway for learned behavior** — ISO 13849 and IEC 62061 assume static safety functions. Incorporating learned reflexes into a certified safety system is an open problem.
3. **Multi-cell coordination** — Orchestrating autonomous behavior across multiple robot cells requires conflict resolution and deadlock avoidance at the safety policy level.
4. **Human intent prediction** — For effective collaboration, the system must predict human operator intent and adapt robot trajectories accordingly.
5. **Legacy system integration** — Most factories have existing PLCs, safety relays, and fieldbus networks. NEXUS must interface with Modbus, PROFINET, EtherCAT, and OPC UA.

---

## 5. Domain 4: Mining Operations

### 5.1 Domain Overview

Mining is one of the harshest and most hazardous operational environments, with explosion risks, toxic gases, dust, vibration, and extreme temperatures.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Ventilation Fan Control | CRITICAL | < 1 s | Medium |
| Pump Control (dewatering) | HIGH | < 500 ms | Medium |
| Environmental Monitoring | CRITICAL | < 5 s | Medium |
| Autonomous Haul Trucks | CRITICAL | < 200 ms | Very High |
| Drill Automation | HIGH | < 100 ms | High |
| Slope Stability Monitoring | HIGH | < 60 s | High |
| Blast Management | CRITICAL | < 100 ms | Very High |

### 5.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **IEC 60079** | Explosive atmospheres — Equipment protection | Intrinsically safe design for gas/dust zones |
| **IEC Ex / ATEX** | Equipment for explosive atmospheres | Certification required for underground operations |
| **ISO 19296** | Mining machinery — Safety requirements | General mining equipment safety |
| **AS/NZS 2290.3** | Electrical equipment in coal mines | Australian mining electrical standards |
| **MSHA 30 CFR 75** | US mining safety regulations | Mandatory safety systems for US mines |
| **ISO 17757** | Earth-moving machinery — Autonomous | Safety for autonomous mining vehicles |

### 5.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "mining": {
      "domain_id": "mining",
      "compliance_refs": ["IEC 60079", "IEC Ex", "ISO 19296", "AS/NZS 2290.3", "MSHA 30 CFR 75", "ISO 17757"],
      "overrides": {
        "max_ventilation_co_ppm": { "value": 30, "unit": "ppm" },
        "max_temperature_c": { "value": 35.0, "unit": "degrees C" },
        "max_methane_ppm": { "value": 10000, "unit": "ppm" },
        "max_dust_concentration_mg_m3": { "value": 3.0, "unit": "mg/m3" },
        "proximity_stop_distance_m": { "value": 5.0, "unit": "meters" }
      },
      "domain_rules": [
        {
          "id": "MN-001",
          "title": "Methane Level Power Cutoff",
          "description": "When methane concentration exceeds 1% LEL (10,000 ppm), immediately cut all non-intrinsically-safe electrical power. Only intrinsically-safe gas monitoring may continue operating.",
          "severity": "CRITICAL",
          "sensor_dependency": ["methane_sensor", "intrinsically_safe_power_controller"],
          "safe_state": "explosion_proof_power_cutoff"
        },
        {
          "id": "MN-002",
          "title": "Multi-Gas Environmental Monitoring",
          "description": "Continuously monitor CH4, CO, NO2, H2S, and O2 levels. Each gas has independent thresholds. Any threshold exceedance triggers escalating alarms and operational restrictions.",
          "severity": "CRITICAL",
          "sensor_dependency": ["multi_gas_detector", "oxygen_sensor"],
          "safe_state": "evacuation_alarm_and_restricted_operations"
        },
        {
          "id": "MN-003",
          "title": "Proximity Detection for Heavy Equipment",
          "description": "All autonomous and semi-autonomous mining vehicles must have proximity detection with minimum 5m stopping distance. Detection must work in dust, fog, and darkness.",
          "severity": "CRITICAL",
          "sensor_dependency": ["radar", "lidar", "tag_based_system"],
          "safe_state": "immediate_vehicle_stop"
        },
        {
          "id": "MN-004",
          "title": "Communication Loss Protocol",
          "description": "If communication with surface control is lost for more than 30 seconds, all autonomous equipment shall enter safe state (stop in place, activate beacons). Resume only on manual command.",
          "severity": "CRITICAL",
          "sensor_dependency": ["comm_monitor", "watchdog"],
          "safe_state": "stop_in_place_with_beacon"
        },
        {
          "id": "MN-005",
          "title": "Explosion-Proof Enclosure Integrity",
          "description": "All NEXUS nodes in underground mines must be in IEC 60079 certified enclosures. Enclosure integrity sensors (pressure differential, door switches) must be continuously monitored.",
          "severity": "CRITICAL",
          "sensor_dependency": ["enclosure_pressure", "door_switch"],
          "safe_state": "power_down_enclosure_compromised"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [-10, 50],
        "humidity_max_percent": 100,
        "ingress_protection": "IP68",
        "explosion_protection": "Ex d IIC T6 Gb or Ex ia IIC T4 Ga",
        "vibration_tolerance": "IEC 60068-2-6 Class III",
        "dust_resistance": "IEC 60529 IP6X"
      }
    }
  }
}
```

### 5.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| Multi-Gas Detector (CH4/CO/NO2/H2S) | 4-20mA/HART | 2–6 | 1000–3000 ea | CRITICAL |
| Oxygen Sensor | 4-20mA | 2–4 | 200–500 ea | CRITICAL |
| Dust Monitor (respirable) | Analog/Modbus | 2–4 | 500–2000 ea | HIGH |
| Vibration Sensor (triple-axis) | I2C/SPI | 2–8 | 50–300 ea | HIGH |
| Temperature (ambient + equipment) | I2C/1-Wire | 4–12 | 5–20 ea | MEDIUM |
| LIDAR (mining-grade, IP68) | Ethernet | 1–2 | 5000–15000 | CRITICAL |
| Radar (77 GHz, dust-penetrating) | CAN | 2–6 | 200–800 ea | CRITICAL |
| Strain Gauge (structural) | Analog | 4–12 | 20–80 ea | HIGH |
| Water Level (pump stations) | 4-20mA | 2–4 | 50–200 ea | HIGH |
| Airflow Velocity (ventilation) | Analog | 4–8 | 100–300 ea | HIGH |

**Estimated total sensor cost per node: $10,000–$40,000**

### 5.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Ventilation Fan VFD | motor_pwm | 2–6 | 1000–4000 ea | CRITICAL |
| Dewatering Pump VFD | motor_pwm | 2–8 | 1000–5000 ea | HIGH |
| Warning Beacon/Horn | buzzer + led | 2–4 | 50–200 ea | HIGH |
| Explosion-Proof Isolator | relay | 4–12 | 200–800 ea | CRITICAL |
| Brake System (vehicles) | solenoid | 2–4 | 300–1000 ea | CRITICAL |
| Steering (haul trucks) | motor_pwm | 1 | 1000–3000 | CRITICAL |

**Estimated total actuator cost per node: $5,000–$25,000**

### 5.6 INCREMENTS Autonomy Level Mapping

| Level | Mining Application | Requirements |
|-------|-------------------|--------------|
| L0 — Manual | Equipment operation | Human operator in vehicle |
| L1 — Assisted | Collision warnings, gas alerts | Operator confirms actions |
| L2 — Supervised | Tele-remote operation | Operator at surface control room |
| L3 — Conditional | Semi-autonomous hauling (defined routes) | Remote operator available |
| L4 — High | Fully autonomous hauling + loading | Periodic remote check-ins |
| L5 — Full | Autonomous mine operation (drill, haul, process) | Remote oversight |

### 5.7 Trust Score Parameters

```json
{
  "mining": {
    "trust_parameters": {
      "subsystem_weights": {
        "gas_monitoring": { "weight": 1.0, "risk_factor": 1.5 },
        "vehicle_control": { "weight": 1.0, "risk_factor": 1.3 },
        "ventilation": { "weight": 1.0, "risk_factor": 1.4 },
        "pump_systems": { "weight": 0.6, "risk_factor": 0.9 },
        "structural_monitoring": { "weight": 0.8, "risk_factor": 1.0 }
      },
      "alpha_gain_default": 0.02,
      "alpha_loss_default": 1.5,
      "recommended_ratio": "75:1",
      "rationale": "Mining has the highest environmental hazard and worst-case outcomes (explosion, asphyxiation, cave-in). Trust must be extremely conservative. The 75:1 ratio means approximately 120 days to reach L4 from zero, preventing premature autonomous operation in a deadly environment."
    }
  }
}
```

### 5.8 Market Size and Existing Solutions

**Global Market:** Mining automation market projected at **$5.6B by 2027** (CAGR 7.8%). Autonomous mining equipment at **$3.4B by 2027**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| AutoMine | Sandvik | Autonomous haul trucks, loaders | Very expensive, proprietary |
| Command for Hauling | Caterpillar | Autonomous truck fleet | Proprietary ecosystem |
| FLEET Management | Modular Mining | Dispatch, fleet management | No direct vehicle control |
| MineSTAR | John Deere | Machine guidance, telemetry | Limited autonomy |
| ROS Mining Stack | Open source academic | Research prototyping | Not production/safety certified |

### 5.9 Key Research Challenges

1. **Explosion-proof electronics design** — NEXUS nodes must be certified intrinsically safe or explosion-proof (Ex d/Ex ia), requiring specialized PCB design, enclosure sealing, and component selection.
2. **Dust and particulate interference** — Mining dust degrades LIDAR, cameras, and connectors. Radar and ultrasonic sensors must be primary, with vision as supplementary.
3. **Underground communication** — WiFi and GPS are unavailable underground. Leaky feeder, mesh radio, or UWB systems must replace standard NEXUS communication.
4. **Gas sensor drift and calibration** — Electrochemical gas sensors drift over time and require frequent calibration. Self-calibrating sensor fusion is essential.
5. **Regulatory fragmentation** — Mining regulations differ significantly by country and even by state/province, requiring per-jurisdiction safety policy customization.

---

## 6. Domain 5: HVAC Systems

### 6.1 Domain Overview

HVAC (Heating, Ventilation, and Air Conditioning) systems are the lowest-risk domain in terms of life safety but represent a large market opportunity for energy optimization and indoor air quality.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Zone Temperature Control | LOW | < 30 s | Medium |
| Predictive Maintenance | LOW | < 60 s | High |
| Energy Optimization | LOW | < 300 s | High |
| Indoor Air Quality Monitoring | MEDIUM | < 30 s | Medium |
| Freezestat Protection | HIGH | < 5 s | Low |
| Refrigerant Leak Detection | HIGH | < 10 s | Medium |
| Demand Response (Grid) | LOW | < 300 s | High |
| Smoke/Fire Damper Control | CRITICAL | < 1 s | Medium |

### 6.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **ASHRAE 135 (BACnet)** | Building automation communication | Primary protocol for HVAC control networks |
| **ISO 16484** | Building automation and control systems | Overall BMS design standard |
| **ASHRAE 62.1** | Ventilation for acceptable IAQ | Minimum outdoor air requirements |
| **EN 15232** | Energy performance of buildings | Building energy classes (A–I) |
| **ASHRAE 90.1** | Energy standard for buildings | Minimum energy efficiency requirements |
| **UL 864** | Control units for fire alarm | Fire/smoke damper control certification |
| **AHRI 1351** | Performance rating of VAV boxes | Actuator performance standards |

### 6.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "hvac": {
      "domain_id": "hvac",
      "compliance_refs": ["ASHRAE 135", "ISO 16484", "ASHRAE 62.1", "EN 15232", "UL 864"],
      "overrides": {
        "max_zone_temp_delta_c": { "value": 5.0, "unit": "degrees C" },
        "min_zone_temp_c": { "value": 5.0, "unit": "degrees C" },
        "max_zone_temp_c": { "value": 40.0, "unit": "degrees C" },
        "max_humidity_percent": { "value": 70, "unit": "percent RH" },
        "min_humidity_percent": { "value": 20, "unit": "percent RH" }
      },
      "domain_rules": [
        {
          "id": "HV-001",
          "title": "Freeze Protection Activation",
          "description": "When any zone temperature drops below 5°C or supply air temperature drops below 2°C, immediately close outside air dampers, enable heating, and activate freeze protection alarm.",
          "severity": "HIGH",
          "sensor_dependency": ["zone_temp", "supply_air_temp"],
          "safe_state": "close_oa_dampers_and_heat"
        },
        {
          "id": "HV-002",
          "title": "Refrigerant Leak Detection",
          "description": "Monitor for refrigerant leaks using dedicated sensors. If concentration exceeds TLV-TWA (varies by refrigerant type), shut down affected unit and evacuate zone if occupied.",
          "severity": "HIGH",
          "sensor_dependency": ["refrigerant_leak_detector", "occupancy"],
          "safe_state": "unit_shutdown_and_zone_alarm"
        },
        {
          "id": "HV-003",
          "title": "Smoke Damper Closure on Fire Alarm",
          "description": "Upon receipt of fire alarm signal (from fire alarm panel via supervised input), close all smoke dampers within the affected zone within 60 seconds per NFPA 90A.",
          "severity": "CRITICAL",
          "sensor_dependency": ["fire_alarm_input", "damper_feedback"],
          "safe_state": "close_smoke_dampers"
        },
        {
          "id": "HV-004",
          "title": "CO2-Based Demand-Controlled Ventilation",
          "description": "Modulate outdoor air damper position based on CO2 concentration to maintain levels below 1000 ppm (ASHRAE 62.1 target). Minimum outdoor air shall never fall below design minimum.",
          "severity": "MEDIUM",
          "sensor_dependency": ["co2_sensor", "oa_damper_position"],
          "safe_state": "open_damper_to_minimum"
        },
        {
          "id": "HV-005",
          "title": "Occupancy-Based Setback",
          "description": "When a zone is unoccupied for >30 minutes, allow temperature to drift to setback setpoints (±5°C from occupied setpoint). Upon occupancy detection, return to occupied setpoint within ASHRAE 55 comfort limits.",
          "severity": "LOW",
          "sensor_dependency": ["occupancy_sensor", "zone_temp"],
          "safe_state": "setback_mode"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [0, 50],
        "humidity_max_percent": 95,
        "ingress_protection": "IP40 (indoor)",
        "vibration_tolerance": "minimal",
        "emc_compliance": "FCC Part 15 Class B"
      }
    }
  }
}
```

### 6.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| Temperature (zone) | I2C | 4–16 | 5–15 ea | MEDIUM |
| Humidity (RH) | I2C | 4–16 | 10–25 ea | MEDIUM |
| CO2 Sensor (NDIR) | I2C/UART | 4–16 | 30–80 ea | MEDIUM |
| VOC Sensor | I2C | 2–8 | 20–50 ea | LOW |
| Occupancy (PIR/UWB) | GPIO/I2C | 4–16 | 5–30 ea | LOW |
| Supply Air Temperature | I2C/4-20mA | 1–4 | 10–30 ea | HIGH |
| Refrigerant Leak Detector | 4-20mA/Modbus | 1–4 | 100–400 ea | HIGH |
| Differential Pressure | I2C/4-20mA | 2–8 | 30–100 ea | MEDIUM |
| Outside Air Temperature | I2C | 1–2 | 10–25 ea | MEDIUM |
| Flow Meter (air/water) | Pulse/4-20mA | 2–8 | 50–200 ea | LOW |

**Estimated total sensor cost per node: $400–$2,500**

### 6.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Damper Actuator | motor_pwm | 4–16 | 50–200 ea | HIGH |
| Valve Actuator (2-way/3-way) | motor_pwm | 2–12 | 80–300 ea | MEDIUM |
| VFD (fan motor) | motor_pwm | 1–4 | 200–1500 ea | MEDIUM |
| Boiler/Furnace Control | relay | 1–2 | 50–200 ea | HIGH |
| Reheat Relay | relay | 4–16 | 10–30 ea | LOW |

**Estimated total actuator cost per node: $500–$5,000**

### 6.6 INCREMENTS Autonomy Level Mapping

| Level | HVAC Application | Requirements |
|-------|-----------------|--------------|
| L0 — Manual | Manual thermostat control | Building operator sets all setpoints |
| L1 — Assisted | Schedule-based control, efficiency suggestions | Operator confirms changes |
| L2 — Supervised | Adaptive PID tuning, occupancy-based setback | Operator reviews periodic reports |
| L3 — Conditional | Predictive maintenance, demand response | Remote monitoring |
| L4 — High | Self-optimizing building, AI-driven energy management | Periodic check-ins |
| L5 — Full | Multi-building coordination, grid-interactive operation | Fully autonomous |

### 6.7 Trust Score Parameters

```json
{
  "hvac": {
    "trust_parameters": {
      "subsystem_weights": {
        "temperature_control": { "weight": 0.5, "risk_factor": 0.3 },
        "ventilation": { "weight": 0.6, "risk_factor": 0.5 },
        "freeze_protection": { "weight": 1.0, "risk_factor": 0.8 },
        "smoke_control": { "weight": 1.0, "risk_factor": 1.0 },
        "energy_optimization": { "weight": 0.3, "risk_factor": 0.2 }
      },
      "alpha_gain_default": 0.10,
      "alpha_loss_default": 0.3,
      "recommended_ratio": "3:1",
      "rationale": "HVAC has the lowest safety risk of all domains (no direct life threat in normal operation). The 3:1 ratio allows rapid trust accumulation (approximately 10 days to L4), enabling fast deployment of energy optimization features. However, freeze protection and smoke control subsystems retain higher loss sensitivity."
    }
  }
}
```

### 6.8 Market Size and Existing Solutions

**Global Market:** Building automation systems (BAS) market projected at **$136B by 2027** (CAGR 10.1%). Smart HVAC controls at **$25B by 2027**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| BACnet/IP Controllers | Siemens, Honeywell, Johnson Controls | Industry standard BMS | Proprietary programming, no learning |
| Nest Thermostat | Google | Learning thermostat | Consumer-grade, not commercial |
| BuildingIQ | BuildingIQ | AI-based energy optimization | Cloud-only, not edge |
| Distech Controls | Acuity Brands | ECLYPSE series BACnet controllers | Limited ML at edge |
| CopperTree Analytics | CopperTree | HVAC analytics, fault detection | Analytics only, no control |

### 6.9 Key Research Challenges

1. **Legacy BACnet integration** — Existing BMS systems use BACnet/IP and BACnet MSTP. NEXUS must either implement a BACnet stack or bridge via a gateway, both adding complexity.
2. **Thermal inertia modeling** — Buildings have large thermal time constants (minutes to hours). Control algorithms must account for this to avoid oscillation while remaining responsive.
3. **Multi-zone coupling** — HVAC zones are thermally coupled through shared walls, ductwork, and return air. Controlling one zone affects adjacent zones.
4. **Commissioning and calibration** — Every building is unique. NEXUS must self-commission zone models from observation data, replacing manual tuning.
5. **Cybersecurity for building networks** — BACnet networks are notoriously insecure. NEXUS must implement IEC 62443 principles for building automation cybersecurity.

---

## 7. Domain 6: Home Automation

### 7.1 Domain Overview

Home automation is the highest-volume, lowest-safety-criticality domain, offering the largest market opportunity but with significant consumer experience challenges.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Lighting Scene Control | LOW | < 500 ms | Low |
| Security System Response | HIGH | < 500 ms | Medium |
| Energy Management | LOW | < 5 s | Medium |
| Elderly Assistance | HIGH | < 1 s | High |
| Voice Control Integration | LOW | < 2 s | Medium |
| Appliance Control | MEDIUM | < 1 s | Low |
| Water Leak Detection | HIGH | < 5 s | Low |
| Smart Lock Control | HIGH | < 500 ms | Medium |

### 7.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **UL 60335** | Household electrical appliances | Safety for motor-operated appliances |
| **FCC Part 15** | Radio frequency devices | EMI/RFI compliance for wireless devices |
| **UL 217** | Smoke alarms | Smoke detector certification |
| **UL 2034** | CO alarms | CO detector certification |
| **UL 63141** | Door lock systems | Smart lock safety requirements |
| **Matter / Thread** | IoT interoperability standard | New interoperability standard (replaces Zigbee/Z-Wave) |
| **IEEE 802.15.4** | Low-rate wireless networks | Physical layer for Thread/Zigbee |

### 7.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "home_automation": {
      "domain_id": "home_automation",
      "compliance_refs": ["UL 60335", "FCC Part 15", "UL 217", "UL 2034", "Matter 1.0"],
      "overrides": {
        "max_actuator_power_w": { "value": 1500, "unit": "watts" },
        "max_temperature_warn_c": { "value": 45.0, "unit": "degrees C" },
        "max_water_flow_duration_min": { "value": 60, "unit": "minutes" },
        "lock_engage_timeout_ms": { "value": 5000, "unit": "milliseconds" },
        "alarm_max_duration_s": { "value": 300, "unit": "seconds" }
      },
      "domain_rules": [
        {
          "id": "HA-001",
          "title": "Fire Detection and Emergency Response",
          "description": "Upon smoke/CO alarm activation: (a) turn on all lights, (b) unlock front door, (c) disable HVAC fan, (d) send emergency notification, (e) activate audible alarm.",
          "severity": "CRITICAL",
          "sensor_dependency": ["smoke_detector", "co_detector"],
          "safe_state": "emergency_response_sequence"
        },
        {
          "id": "HA-002",
          "title": "Water Leak Detection and Shutoff",
          "description": "When water leak sensor activates, close main water shutoff valve within 5 seconds. Send notification to all registered users.",
          "severity": "HIGH",
          "sensor_dependency": ["water_leak_sensor", "shutoff_valve"],
          "safe_state": "close_water_valve"
        },
        {
          "id": "HA-003",
          "title": "Occupancy-Based Security Arming",
          "description": "Security system shall auto-arm in AWAY mode when no occupancy detected for 30 minutes and all doors/windows confirmed closed. Auto-disarm when authorized user arrives.",
          "severity": "MEDIUM",
          "sensor_dependency": ["occupancy", "door_contact", "window_contact"],
          "safe_state": "arm_security"
        },
        {
          "id": "HA-004",
          "title": "Elderly Fall Detection Response",
          "description": "When fall is detected (via IMU wearable or radar): alert caregiver, turn on nearest lights, unlock door for emergency responders, activate two-way audio.",
          "severity": "HIGH",
          "sensor_dependency": ["fall_detector", "radar_presence"],
          "safe_state": "emergency_alert_and_access"
        },
        {
          "id": "HA-005",
          "title": "Smart Lock Deadbolt Confirmation",
          "description": "Every lock/unlock command must be confirmed by physical deadbolt position sensor. If position sensor does not confirm within 5 seconds, retry once then alarm.",
          "severity": "HIGH",
          "sensor_dependency": ["deadbolt_position_sensor", "lock_motor"],
          "safe_state": "alarm_failed_lock"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [0, 45],
        "humidity_max_percent": 85,
        "ingress_protection": "IP30 (indoor)",
        "aesthetic_requirements": true,
        "noise_emission": "<30 dBA"
      }
    }
  }
}
```

### 7.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| Motion Sensor (PIR) | GPIO | 4–8 | 3–10 ea | LOW |
| Door/Window Contact | GPIO/RF | 8–20 | 3–8 ea | MEDIUM |
| Temperature/Humidity | I2C | 2–6 | 5–15 ea | LOW |
| Smoke Detector | GPIO/UART | 2–4 | 10–30 ea | CRITICAL |
| CO Detector | GPIO/UART | 1–2 | 15–40 ea | CRITICAL |
| Water Leak Sensor | GPIO (conductive) | 2–6 | 5–15 ea | HIGH |
| Occupancy (mmWave radar) | I2C/SPI | 2–4 | 10–30 ea | LOW |
| Light Level (lux) | I2C/ADC | 2–6 | 3–10 ea | LOW |
| Smart Lock Position Sensor | Hall effect/GPIO | 1–4 | 5–15 ea | HIGH |
| Air Quality (PM2.5) | I2C/UART | 1–2 | 15–40 ea | LOW |

**Estimated total sensor cost per home node: $150–$500**

### 7.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Smart Switch/Relay | relay | 8–30 | 10–30 ea | MEDIUM |
| Dimmer Module | motor_pwm | 4–16 | 10–25 ea | LOW |
| Smart Lock Motor | motor_pwm | 1–4 | 20–80 ea | HIGH |
| Water Shutoff Valve | solenoid | 1 | 50–150 | HIGH |
| Thermostat Control | motor_pwm | 1–2 | 15–40 ea | MEDIUM |
| Siren/Buzzer | buzzer | 1–2 | 10–30 | MEDIUM |
| LED Indicator | led | 4–12 | 0.5–2 ea | LOW |

**Estimated total actuator cost per home node: $200–$800**

### 7.6 INCREMENTS Autonomy Level Mapping

| Level | Home Automation Application | Requirements |
|-------|---------------------------|--------------|
| L0 — Manual | Manual switch operation | User presses physical buttons |
| L1 — Assisted | Voice control, scheduled scenes | User initiates, system confirms |
| L2 — Supervised | Occupancy-adaptive lighting/climate | User reviews activity logs |
| L3 — Conditional | Security auto-arm, leak auto-shutoff | User can override anytime |
| L4 — High | Fully adaptive home, predictive climate | Periodic preferences review |
| L5 — Full | Self-optimizing home, predictive maintenance | Fully autonomous |

### 7.7 Trust Score Parameters

```json
{
  "home_automation": {
    "trust_parameters": {
      "subsystem_weights": {
        "lighting": { "weight": 0.2, "risk_factor": 0.1 },
        "climate": { "weight": 0.4, "risk_factor": 0.3 },
        "security": { "weight": 1.0, "risk_factor": 0.9 },
        "safety_devices": { "weight": 1.0, "risk_factor": 1.0 },
        "energy_management": { "weight": 0.3, "risk_factor": 0.1 }
      },
      "alpha_gain_default": 0.15,
      "alpha_loss_default": 0.2,
      "recommended_ratio": "1.3:1",
      "rationale": "Home automation has the lowest risk profile. Consequences of most failures are minor inconvenience (lights don't turn off) rather than safety hazards. However, security and life-safety devices (smoke, CO, water shutoff) retain conservative loss parameters. The 1.3:1 ratio enables rapid deployment — approximately 5 days to L4 for non-safety subsystems."
    }
  }
}
```

### 7.8 Market Size and Existing Solutions

**Global Market:** Smart home market projected at **$182B by 2027** (CAGR 17.3%). Home automation systems at **$78B by 2027**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| Home Assistant | Open source | Universal integration, local control | No safety framework, DIY focus |
| Apple HomeKit | Apple | Secure ecosystem, Siri control | Limited device support, Apple-only |
| Google Home | Google | Voice control, ML automation | Cloud-dependent, privacy concerns |
| Amazon Alexa | Amazon | Voice control, routines | Cloud-dependent, limited local |
| Hubitat | Hubitat | Local automation hub | Limited learning capabilities |
| SmartThings | Samsung | Zigbee/Z-Wave/WiFi hub | Cloud-dependent, limited reflex control |

### 7.9 Key Research Challenges

1. **Consumer usability** — Home automation must "just work" with zero configuration. Trust calibration must be invisible to end users while still providing safety guarantees.
2. **Interoperability fragmentation** — Matter is improving but legacy Zigbee, Z-Wave, WiFi, Bluetooth, and proprietary protocols coexist. NEXUS must bridge these.
3. **Privacy and data sovereignty** — Home data is highly personal. NEXUS must provide strong local processing guarantees with minimal cloud dependency.
4. **Cost sensitivity** — Consumer market demands sub-$100 node pricing. The ESP32-based NEXUS architecture is well-positioned, but additional sensors add cost.
5. **False alarm fatigue** — Home security systems suffer from high false alarm rates. NEXUS learning must reduce false alarms without increasing missed detections.

---

## 8. Domain 7: Healthcare Robotics

### 8.1 Domain Overview

Healthcare robotics represents the most heavily regulated domain with the highest stakes — patient safety and regulatory compliance (FDA/HIPAA) create significant barriers to entry but also strong market differentiation.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Surgical Assistance | CRITICAL | < 5 ms | Very High |
| Rehabilitation Robotics | HIGH | < 20 ms | Very High |
| Patient Vital Monitoring | CRITICAL | < 1 s | High |
| Medication Dispensing | CRITICAL | < 500 ms | High |
| Patient Transport (AGV) | HIGH | < 200 ms | Medium |
| Disinfection Robotics | MEDIUM | < 1 s | Medium |
| Social/Companion Robots | LOW | < 500 ms | Medium |
| Prosthetic Control | HIGH | < 10 ms | Very High |

### 8.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **FDA 510(k)** | Medical device premarket notification | Required for most healthcare devices |
| **IEC 62304** | Medical device software lifecycle | Software development process requirements |
| **IEC 62366** | Usability engineering for medical devices | Human factors engineering |
| **HIPAA** | Health Insurance Portability and Accountability | Data privacy for patient information |
| **IEC 60601-1** | Medical electrical equipment — General requirements | Electrical safety for patient-connected equipment |
| **ISO 14971** | Medical devices — Risk management | Formal risk management process |
| **ISO 13485** | Medical devices — Quality management | Quality system requirements |

### 8.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "healthcare": {
      "domain_id": "healthcare",
      "compliance_refs": ["FDA 510(k)", "IEC 62304", "IEC 62366", "HIPAA", "IEC 60601-1", "ISO 14971", "ISO 13485"],
      "overrides": {
        "max_contact_force_n": { "value": 50, "unit": "Newtons" },
        "max_robot_speed_m_s": { "value": 0.5, "unit": "m/s" },
        "max_vital_sign_interval_s": { "value": 5, "unit": "seconds" },
        "max_dose_deviation_percent": { "value": 1.0, "unit": "percent" },
        "backup_power_duration_min": { "value": 30, "unit": "minutes" }
      },
      "domain_rules": [
        {
          "id": "HC-001",
          "title": "Patient Contact Force Limiting",
          "description": "All robotic systems in patient contact must have redundant force limiting. If any sensor exceeds 50N (body contact) or 150N (limb contact), immediate soft-stop. Dual-channel force sensing required.",
          "severity": "CRITICAL",
          "sensor_dependency": ["force_torque_sensor_x2", "pressure_mat"],
          "safe_state": "soft_stop_and_retract"
        },
        {
          "id": "HC-002",
          "title": "Medication Dispensing Verification",
          "description": "Every medication dispense operation must be verified by: (a) barcode/RFID scan of medication, (b) patient identification, (c) dose calculation verification. Any mismatch blocks dispensing and alerts pharmacist.",
          "severity": "CRITICAL",
          "sensor_dependency": ["barcode_scanner", "rfid_reader", "weight_sensor"],
          "safe_state": "block_dispensing_and_alert"
        },
        {
          "id": "HC-003",
          "title": "Vital Sign Escalation Protocol",
          "description": "Monitor vital signs at defined intervals. Implement three-tier escalation: YELLOW (minor deviation, nurse alert), ORANGE (significant deviation, rapid response), RED (critical, code blue activation).",
          "severity": "CRITICAL",
          "sensor_dependency": ["pulse_oximeter", "bp_monitor", "ecg", "temperature"],
          "safe_state": "escalation_protocol"
        },
        {
          "id": "HC-004",
          "title": "Sterilization Cycle Verification",
          "description": "Surgical robots must verify sterilization status before patient contact. Chemical indicator + biological indicator verification. Non-sterile instruments shall be physically locked out.",
          "severity": "CRITICAL",
          "sensor_dependency": ["sterilization_indicator", "instrument_rfid"],
          "safe_state": "lockout_instrument"
        },
        {
          "id": "HC-005",
          "title": "Backup Power and Graceful Degradation",
          "description": "All patient-connected systems must have 30-minute battery backup. On power loss: (a) switch to backup, (b) alert staff, (c) enter safe state for non-critical functions, (d) maintain patient monitoring.",
          "severity": "CRITICAL",
          "sensor_dependency": ["power_monitor", "battery_level"],
          "safe_state": "backup_power_mode"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [10, 40],
        "humidity_max_percent": 80,
        "ingress_protection": "IPX4 (cleanable)",
        "biocompatibility": "ISO 10993",
        "emc_compliance": "IEC 60601-1-2",
        "cleanroom_class": "ISO Class 7 (operating room)"
      }
    }
  }
}
```

### 8.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| Force/Torque (6-axis, medical) | CAN/Ethernet | 2–4 | 1000–4000 ea | CRITICAL |
| Pulse Oximeter | I2C/UART | 1–4 | 20–100 ea | CRITICAL |
| Blood Pressure Sensor | UART/I2C | 1–2 | 50–200 ea | CRITICAL |
| ECG Lead (3/12 lead) | Analog | 1–4 | 100–500 ea | CRITICAL |
| Temperature (patient, NTC) | I2C/1-Wire | 1–4 | 5–20 ea | HIGH |
| Pressure Mat (bed/chair) | I2C array | 1–4 | 100–500 ea | HIGH |
| Encoder (joint feedback) | SSI/BiSS | 4–12 | 100–500 ea | HIGH |
| Vision Camera (3D/depth) | USB3/GigE | 1–4 | 300–2000 ea | MEDIUM |
| Ultrasound (distance) | I2C/UART | 2–8 | 10–50 ea | MEDIUM |
| Barcode/RFID Reader | UART/USB | 1–2 | 100–500 ea | CRITICAL |

**Estimated total sensor cost per node: $3,000–$20,000**

### 8.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Servo Motor (medical-grade) | motor_pwm | 2–8 | 500–3000 ea | CRITICAL |
| Linear Actuator (bed/chair) | motor_pwm | 2–6 | 100–500 ea | HIGH |
| Pump (infusion) | motor_pwm | 1–4 | 200–1000 ea | CRITICAL |
| Gripper (surgical) | servo + motor_pwm | 1–2 | 1000–5000 ea | CRITICAL |
| LED Indicator (status) | led | 2–8 | 1–5 ea | LOW |
| Alarm (visual/audible) | buzzer + led | 1–2 | 20–100 ea | HIGH |

**Estimated total actuator cost per node: $2,000–$20,000**

### 8.6 INCREMENTS Autonomy Level Mapping

| Level | Healthcare Application | Requirements |
|-------|----------------------|--------------|
| L0 — Manual | Manual surgical tools, manual vital sign checks | Clinician performs all actions |
| L1 — Assisted | Surgical navigation display, medication reminders | Clinician confirms all actions |
| L2 — Supervised | Tele-rehabilitation, automated vital sign logging | Clinician monitors remotely |
| L3 — Conditional | Autonomous medication dispensing, guided rehab | Clinician available within 2 min |
| L4 — High | Autonomous patient transport, routine monitoring | Periodic clinician check-ins |
| L5 — Full | Autonomous surgical subtasks, fully autonomous rehab | Clinician oversight only |

### 8.7 Trust Score Parameters

```json
{
  "healthcare": {
    "trust_parameters": {
      "subsystem_weights": {
        "surgical_control": { "weight": 1.0, "risk_factor": 2.0 },
        "vital_monitoring": { "weight": 1.0, "risk_factor": 1.5 },
        "medication_dispensing": { "weight": 1.0, "risk_factor": 1.8 },
        "patient_transport": { "weight": 0.7, "risk_factor": 1.0 },
        "rehabilitation": { "weight": 0.6, "risk_factor": 0.7 }
      },
      "alpha_gain_default": 0.01,
      "alpha_loss_default": 2.0,
      "recommended_ratio": "200:1",
      "rationale": "Healthcare has the absolute highest risk of any domain — patient harm or death. The 200:1 ratio makes trust accumulation extremely slow (~200 days to L4 for critical subsystems). Even L2 (supervised) requires ~30 days of demonstrated reliability. This reflects the regulatory reality of FDA approval processes and the non-negotiable nature of patient safety."
    }
  }
}
```

### 8.8 Market Size and Existing Solutions

**Global Market:** Medical robotics market projected at **$44B by 2027** (CAGR 22.1%). Healthcare automation at **$79B by 2027**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| da Vinci Surgical System | Intuitive Surgical | Minimally invasive robotic surgery | $2M+ per unit, FDA 510(k) cleared |
| TUG (Transport) | Aethon | Autonomous hospital logistics | Single-purpose, expensive |
| InTouch Vita | InTouch Health | Telemedicine robot | Telepresence only, no physical interaction |
| Lokomat | Hocoma | Robotic gait rehabilitation | Single-purpose, very expensive |
| Omnicell | Omnicell | Automated medication dispensing | Dispensing only, not full platform |
| ROS Medical | Various academic | Research platforms | Not FDA cleared, not production-grade |

### 8.9 Key Research Challenges

1. **FDA regulatory pathway** — No precedent for FDA clearance of an adaptive/learning platform controlling medical devices. The IEC 62304 lifecycle must be adapted for continuous learning systems.
2. **Patient variability** — Patient anatomy, conditions, and responses are highly variable. Control parameters must adapt safely without extensive per-patient calibration.
3. **Clinical validation requirements** — Medical device approval requires extensive clinical trials. The NEXUS learning system's adaptive behavior complicates traditional validation approaches.
4. **HIPAA compliance for edge AI** — Patient data processed on NEXUS nodes must meet HIPAA Security Rule requirements (encryption, access controls, audit logging) at the edge.
5. **Dual-use safety/failure modes** — Healthcare robots that assist patients can also cause harm (e.g., rehabilitation robot over-exertion). Failure modes must be exhaustively analyzed per ISO 14971.

---

## 9. Domain 8: Autonomous Vehicles (Ground)

### 9.1 Domain Overview

Ground autonomous vehicles (AGVs, AMRs, delivery robots) represent a broad category spanning warehouse logistics, last-mile delivery, agriculture, and construction.

#### Key Application Areas
| Application | Safety Criticality | Latency Requirement | Complexity |
|-------------|-------------------|--------------------|----|
| Warehouse AGV Navigation | HIGH | < 100 ms | High |
| Last-Mile Delivery Robot | HIGH | < 200 ms | Very High |
| Agricultural Robot (weeding) | MEDIUM | < 500 ms | High |
| Construction Vehicle (autonomous) | CRITICAL | < 100 ms | Very High |
| Hospital Transport AGV | HIGH | < 200 ms | Medium |
| Cleaning Robot (industrial) | MEDIUM | < 500 ms | Medium |
| Forklift AGV | CRITICAL | < 50 ms | High |
| Road Crossing Delivery Bot | HIGH | < 100 ms | Very High |

### 9.2 Regulatory Framework

| Standard | Scope | Impact on NEXUS |
|----------|-------|-----------------|
| **ISO 3691-4** | Industrial trucks — Driverless trucks | Safety requirements for AGVs |
| **ANSI/ITSDF B56.5** | Driverless automatic guided vehicles | US standard for AGV safety |
| **ISO 3691-6** | Industrial trucks — Remote-controlled trucks | Remote operation safety |
| **EN 1525** | Driverless trucks and their systems | European AGV standard |
| **ISO 13849** | Safety of machinery — Safety parts | Performance levels for AGV safety functions |
| **ISO 19296** | Mining machinery — Safety | Surface mining vehicle safety |
| **UNECE R79** | Steering systems for vehicles | Road vehicle steering safety |
| **SAE J3016** | Driving automation levels | Taxonomy (L0–L5) for road vehicles |

### 9.3 Domain-Specific Safety Policy JSON Extension

```json
{
  "domain_specific_safety_rules": {
    "autonomous_vehicles": {
      "domain_id": "autonomous_vehicles",
      "compliance_refs": ["ISO 3691-4", "ANSI/ITSDF B56.5", "ISO 13849-1", "EN 1525", "UNECE R79"],
      "overrides": {
        "max_speed_indoor_m_s": { "value": 1.5, "unit": "m/s" },
        "max_speed_outdoor_m_s": { "value": 2.0, "unit": "m/s" },
        "pedestrian_detection_range_m": { "value": 10.0, "unit": "meters" },
        "obstacle_detection_range_m": { "value": 20.0, "unit": "meters" },
        "max_deceleration_m_s2": { "value": 3.0, "unit": "m/s²" },
        "geofence_required": true,
        "emergency_stop_trigger_distance_m": { "value": 0.5, "unit": "meters" }
      },
      "domain_rules": [
        {
          "id": "AV-001",
          "title": "Three-Zone Speed Reduction",
          "description": "Implement three concentric detection zones: (a) SLOW zone at 10m — reduce speed to 50%, (b) STOP zone at 3m — decelerate to stop, (c) E-STOP zone at 0.5m — immediate hard stop. Zone sizes configurable per environment.",
          "severity": "CRITICAL",
          "sensor_dependency": ["lidar", "radar", "camera"],
          "safe_state": "three_zone_stop"
        },
        {
          "id": "AV-002",
          "title": "Speed Limiting by Zone Classification",
          "description": "Maximum speed is determined by zone classification: PEDESTRIAN zone (1.0 m/s), INDUSTRIAL zone (1.5 m/s), VEHICLE zone (2.0 m/s), OUTDOOR zone (2.0 m/s). Zone classification is determined by environmental sensors and map data.",
          "severity": "CRITICAL",
          "sensor_dependency": ["zone_map", "occupancy", "lidar"],
          "safe_state": "reduce_to_zone_limit"
        },
        {
          "id": "AV-003",
          "title": "Geofence Boundary Enforcement",
          "description": "Vehicle shall not operate outside configured geofence boundaries. If within 1m of geofence, stop and alert. Geofence may be updated remotely but requires safety validation.",
          "severity": "HIGH",
          "sensor_dependency": ["gps", "odometry", "slam"],
          "safe_state": "stop_at_boundary"
        },
        {
          "id": "AV-004",
          "title": "Payload Stability Monitoring",
          "description": "Monitor payload weight and center of gravity via load cells and IMU. If payload shifts beyond stability envelope (tilt > 5 degrees or COG shift > 20%), stop immediately.",
          "severity": "HIGH",
          "sensor_dependency": ["load_cell", "imu", "tilt_sensor"],
          "safe_state": "stop_and_stabilize"
        },
        {
          "id": "AV-005",
          "title": "Communication Loss Safe Stop",
          "description": "If communication with fleet manager is lost for >10 seconds (indoor) or >30 seconds (outdoor), vehicle shall stop in place and activate hazard lights. Resume requires manual or authenticated remote command.",
          "severity": "HIGH",
          "sensor_dependency": ["comm_monitor", "watchdog"],
          "safe_state": "stop_in_place"
        }
      ],
      "environmental_limits": {
        "operating_temp_range_c": [-10, 50],
        "humidity_max_percent": 95,
        "ingress_protection": "IP54 (warehouse) / IP65 (outdoor)",
        "vibration_tolerance": "IEC 60068-2-6",
        "emc_compliance": "EN 55032/EN 55035"
      }
    }
  }
}
```

### 9.4 Sensor Suite

| Sensor | Interface | Qty per Node | Cost (USD) | Criticality |
|--------|-----------|-------------|------------|-------------|
| 2D/3D LIDAR | Ethernet/UART | 1–2 | 200–3000 ea | CRITICAL |
| Depth Camera (stereo/ToF) | USB/Ethernet | 1–4 | 50–500 ea | HIGH |
| IMU (6/9-DOF) | I2C/SPI | 1–2 | 10–50 ea | HIGH |
| Wheel Encoders | Quadrature | 2–4 | 15–50 ea | HIGH |
| Ultrasonic (proximity) | I2C/GPIO | 4–12 | 5–20 ea | MEDIUM |
| Camera (monocular) | USB/MIPI | 1–4 | 10–100 ea | MEDIUM |
| Load Cell (payload) | I2C/Analog | 2–4 | 30–100 ea | HIGH |
| Bumper/Contact Sensor | GPIO | 2–8 | 5–15 ea | CRITICAL |
| Emergency Stop Button | GPIO (safety) | 1–4 | 5–20 ea | CRITICAL |
| RFID Tag Reader (localization) | UART/SPI | 1–2 | 50–200 ea | MEDIUM |

**Estimated total sensor cost per vehicle node: $800–$6,000**

### 9.5 Actuator Suite

| Actuator | Type | Qty | Cost (USD) | Safety Class |
|----------|------|-----|------------|-------------|
| Drive Motor (differential) | motor_pwm | 2 | 50–300 ea | HIGH |
| Steering Servo | servo | 1 | 30–200 ea | HIGH |
| Brake (electromechanical) | solenoid/relay | 1–2 | 50–200 ea | CRITICAL |
| Lifting Mechanism | motor_pwm | 0–2 | 100–500 ea | HIGH |
| Horn/Beacon | buzzer/led | 1–2 | 20–80 ea | MEDIUM |
| Status Display | led | 1–2 | 10–30 ea | LOW |

**Estimated total actuator cost per vehicle node: $300–$2,000**

### 9.6 INCREMENTS Autonomy Level Mapping

| Level | Ground AV Application | Requirements |
|-------|----------------------|--------------|
| L0 — Manual | Manual driving/joystick control | Operator controls all motion |
| L1 — Assisted | Collision warnings, suggested routes | Operator confirms all actions |
| L2 — Supervised | Autonomous waypoint following (structured) | Operator monitors and can override |
| L3 — Conditional | Autonomous navigation in mixed environments | Remote operator available |
| L4 — High | Fully autonomous warehouse/facility operation | Periodic remote check-ins |
| L5 — Full | Autonomous delivery on public roads | Remote oversight |

### 9.7 Trust Score Parameters

```json
{
  "autonomous_vehicles": {
    "trust_parameters": {
      "subsystem_weights": {
        "navigation": { "weight": 1.0, "risk_factor": 1.3 },
        "obstacle_detection": { "weight": 1.0, "risk_factor": 1.4 },
        "drive_control": { "weight": 1.0, "risk_factor": 1.2 },
        "payload_handling": { "weight": 0.6, "risk_factor": 0.8 },
        "communication": { "weight": 0.5, "risk_factor": 0.6 }
      },
      "alpha_gain_default": 0.03,
      "alpha_loss_default": 1.0,
      "recommended_ratio": "33:1",
      "rationale": "Ground autonomous vehicles operate in mixed pedestrian/industrial environments with significant collision risk. The 33:1 ratio balances the need for deployment efficiency (warehouse economics) with pedestrian safety requirements. Approximately 55 days to L4, requiring substantial validation before unsupervised operation."
    }
  }
}
```

### 9.8 Market Size and Existing Solutions

**Global Market:** Autonomous mobile robot (AMR) market projected at **$12.3B by 2027** (CAGR 22.4%). Warehouse automation at **$30B by 2027**.

| Solution | Vendor | Capabilities | Limitations |
|----------|--------|-------------|-------------|
| MiR Fleet | Mobile Industrial Robots | AMR fleet management | Expensive, proprietary |
| OTTO Fleet Manager | Rockwell Automation | AMR fleet orchestration | Enterprise-only pricing |
| ROS 2 Nav2 | Open Robotics | Open-source navigation stack | Not safety-certified, complex |
| Starship Robot | Starship Technologies | Last-mile delivery | Single-purpose, limited payloads |
| Amazon Robotics | Amazon | Kiva-like warehouse robots | Not commercially available |
| Boston Dynamics Spot | Boston Dynamics | Legged robot platform | Very expensive, limited autonomy |

### 9.9 Key Research Challenges

1. **Dynamic obstacle avoidance** — Unstructured environments with moving pedestrians, forklifts, and other vehicles require real-time path planning at 10+ Hz, challenging for the Jetson-side processing.
2. **SLAM in GPS-denied environments** — Indoor warehouses lack GPS. Visual SLAM or LIDAR SLAM must provide robust localization, but are sensitive to environmental changes.
3. **Fleet coordination and deadlock avoidance** — Multi-vehicle systems in shared spaces require decentralized coordination protocols that guarantee deadlock-free operation.
4. **Safety certification for learned navigation** — ISO 3691-4 requires safety functions to be validated. Learned navigation behaviors must be formally verified.
5. **Edge cases in pedestrian prediction** — Human behavior is unpredictable. Pedestrian intent prediction remains a significant unsolved problem for outdoor delivery robots.

---

## 10. Cross-Domain Safety Policy Analysis

### 10.1 Common Safety Rules (Universal)

All eight domains share the 10 global safety rules (SR-001 through SR-010) from the NEXUS safety_policy.json. These are:

| Rule | Domain Applicability | Notes |
|------|---------------------|-------|
| SR-001: Explicit Enable Signal | All | Universal requirement |
| SR-002: Timeout Watchdog | All | Timeout values vary by domain |
| SR-003: Safe-State Definition | All | Safe state varies by domain |
| SR-004: Sensor Failure Independence | All | Marine/mining need enhanced redundancy |
| SR-005: Rate Limiting | All | HVAC needs slowest limiting |
| SR-006: Watchdog Disable Prohibition | All | Universal |
| SR-007: E-Stop Priority | All | Factory/mining need fastest response |
| SR-008: Boot Safe-State | All | Universal |
| SR-009: Division-by-Zero | All | Universal |
| SR-010: Bounded Iteration | All | Universal |

### 10.2 Domain-Specific Rule Count

| Domain | Domain Rules | Unique Safety Mechanisms |
|--------|-------------|------------------------|
| Marine | 5 | MOB response, AIS collision, anchor drag, bilge shutdown |
| Agriculture | 5 | Geofence, rollover, PTO interlock, chemical containment, animal detection |
| Factory | 5 | Force limiting, safety zones, E-Stop categories, safety PLC supervision, jam detection |
| Mining | 5 | Gas cutoff, multi-gas monitoring, proximity (dust), comm loss, explosion-proof integrity |
| HVAC | 5 | Freeze protection, refrigerant leak, smoke damper, DCV, occupancy setback |
| Home | 5 | Fire response, water shutoff, security arming, fall detection, lock confirmation |
| Healthcare | 5 | Force limiting (medical), medication verification, vital sign escalation, sterilization, backup power |
| Ground AV | 5 | Three-zone speed, zone classification, geofence, payload stability, comm loss |

### 10.3 Heartbeat Timeout Comparison

| Domain | Degraded (ms) | Safe State (ms) | Rationale |
|--------|--------------|-----------------|-----------|
| Factory | 200 | 500 | Personnel safety requires fastest detection |
| Mining | 300 | 700 | Explosive atmosphere requires fast response |
| Marine | 500 | 1000 | Vessel dynamics provide natural inertia |
| Agriculture | 500 | 1000 | Outdoor environment, moderate speeds |
| Ground AV | 300 | 700 | Pedestrian proximity requires fast detection |
| Healthcare | 400 | 1000 | Patient monitoring requires reliable heartbeat |
| HVAC | 2000 | 5000 | Thermal inertia allows slowest heartbeat |
| Home | 1000 | 3000 | Low-risk environment allows relaxed timing |

---

## 11. Trust Score Calibration Across Domains

### 11.1 Alpha Gain/Loss Summary

| Domain | α_gain | α_loss | Ratio | Days to L4 | Days to L5 | Risk Category |
|--------|--------|--------|-------|-----------|-----------|---------------|
| Healthcare | 0.01 | 2.0 | 200:1 | ~200 | ~400 | Catastrophic |
| Mining | 0.02 | 1.5 | 75:1 | ~120 | ~240 | Critical |
| Factory | 0.03 | 1.2 | 40:1 | ~80 | ~160 | Critical |
| Marine | 0.04 | 1.0 | 25:1 | ~45 | ~83 | High |
| Ground AV | 0.03 | 1.0 | 33:1 | ~55 | ~105 | High |
| Agriculture | 0.06 | 0.8 | 13:1 | ~25 | ~50 | Moderate |
| HVAC | 0.10 | 0.3 | 3:1 | ~10 | ~20 | Low |
| Home | 0.15 | 0.2 | 1.3:1 | ~5 | ~10 | Minimal |

### 11.2 Trust Accumulation Curve Analysis

The time-to-L4 varies by **40×** across domains — from 5 days (home automation) to 200 days (healthcare). This range reflects the fundamental risk trade-off:

- **Fast trust** → Faster deployment, higher risk of premature autonomy
- **Slow trust** → Slower deployment, lower risk, more operational data before autonomy

The asymmetric ratios ensure that even in low-risk domains, a single critical safety event can cause significant trust degradation, maintaining a conservative safety posture.

### 11.3 Subsystem Risk Factor Heat Map

| Domain | Motion | Monitoring | Chemical/Bio | Environmental | Communication |
|--------|--------|-----------|-------------|--------------|---------------|
| Marine | 1.2 | 0.7 | — | 1.1 | 0.9 |
| Agriculture | 0.9 | 0.5 | 1.1 | 0.8 | 0.7 |
| Factory | 1.3 | 0.4 | — | 0.6 | 0.5 |
| Mining | 1.3 | 1.5 | 1.4 | 1.4 | 0.8 |
| HVAC | 0.3 | 0.5 | 0.5 | 0.8 | 0.3 |
| Home | 0.1 | 1.0 | — | 0.3 | 0.2 |
| Healthcare | 2.0 | 1.5 | 1.8 | 0.5 | 0.6 |
| Ground AV | 1.2 | 1.4 | — | 0.6 | 0.6 |

---

## 12. INCREMENTS Framework Autonomy Mapping

### 12.1 Level Distribution by Domain

| Level | Healthcare | Mining | Factory | Marine | Ground AV | Agriculture | HVAC | Home |
|------|-----------|--------|---------|--------|-----------|-------------|------|------|
| L0 | Manual | Manual | Manual | Manual | Manual | Manual | Manual | Manual |
| L1 | Assisted surgery | Gas alerts | Quality alerts | Heading hold | Collision warn | GPS guidance | Schedules | Voice control |
| L2 | Tele-rehab | Tele-remote | Repeating tasks | Course tracking | Waypoint nav | Autosteering | Adaptive PID | Occupancy adaptive |
| L3 | Med dispensing | Semi-auto haul | Adaptive pick-place | Dynamic positioning | Mixed env nav | Autonomous tillage | Predictive maint | Security auto-arm |
| L4 | Patient transport | Auto haul fleet | Multi-cell coord | Open water nav | Warehouse fleet | Field fleet ops | Self-optimizing | Fully adaptive |
| L5 | Surgical subtasks | Full mine | Lights-out mfg | Passage planning | Public roads | Adaptive fleet | Grid-interactive | Self-optimizing |

### 12.2 Maximum Practically Achievable Level (Near-Term, 3-5 Years)

| Domain | Max Level | Rationale |
|--------|-----------|-----------|
| Healthcare | L2–L3 | FDA/IEC 62304 barriers limit adaptive behavior |
| Mining | L3–L4 | ATEX certification + harsh environment limit full autonomy |
| Factory | L3–L4 | ISO 13849/SIL certification feasible with safety PLC supervision |
| Marine | L3–L4 | Open water autonomy demonstrated; harbor/close-quarters remains L2 |
| Ground AV | L3–L4 | Warehouse AMRs at L4; public road delivery at L3 |
| Agriculture | L4 | Large open fields with GPS RTK enable near-full autonomy |
| HVAC | L4–L5 | Low risk enables rapid autonomy progression |
| Home | L4–L5 | Consumer tolerance for imperfection + low risk enables high autonomy |

---

## 13. Sensor and Actuator Cost Analysis

### 13.1 Per-Node Cost Summary

| Domain | Sensors (USD) | Actuators (USD) | Compute (USD) | Total Node BOM (USD) |
|--------|--------------|-----------------|---------------|---------------------|
| Marine | 3,100–11,200 | 1,400–6,000 | 300–500 | 4,800–17,700 |
| Agriculture | 5,000–16,000 | 1,200–3,500 | 300–500 | 6,500–20,000 |
| Factory | 6,000–30,000 | 2,000–15,000 | 300–500 | 8,300–45,500 |
| Mining | 10,000–40,000 | 5,000–25,000 | 500–800 | 15,500–65,800 |
| HVAC | 400–2,500 | 500–5,000 | 200–400 | 1,100–7,900 |
| Home | 150–500 | 200–800 | 150–300 | 500–1,600 |
| Healthcare | 3,000–20,000 | 2,000–20,000 | 500–1000 | 5,500–41,000 |
| Ground AV | 800–6,000 | 300–2,000 | 300–500 | 1,400–8,500 |

### 13.2 Sensor Count per Node

| Domain | Min Sensors | Max Sensors | Avg Sensors | Unique Sensor Types |
|--------|-----------|-----------|-------------|-------------------|
| Marine | 8 | 12 | 10 | 8 types |
| Agriculture | 12 | 24 | 16 | 11 types |
| Factory | 10 | 40 | 20 | 10 types |
| Mining | 20 | 50 | 30 | 10 types |
| HVAC | 8 | 40 | 20 | 10 types |
| Home | 12 | 40 | 24 | 10 types |
| Healthcare | 10 | 30 | 18 | 10 types |
| Ground AV | 10 | 30 | 18 | 10 types |

### 13.3 Cost Per Autonomy Level Achieved

The cost-per-autonomy-level metric represents how much additional hardware investment is needed to progress from one INCREMENTS level to the next:

| Domain | L0→L1 | L1→L2 | L2→L3 | L3→L4 | L4→L5 |
|--------|-------|-------|-------|-------|-------|
| Marine | $1,000 | $3,000 | $8,000 | $15,000 | $25,000 |
| Agriculture | $500 | $2,000 | $5,000 | $10,000 | $20,000 |
| Factory | $2,000 | $5,000 | $15,000 | $30,000 | $50,000 |
| Mining | $5,000 | $15,000 | $30,000 | $50,000 | $80,000 |
| HVAC | $200 | $500 | $1,000 | $3,000 | $5,000 |
| Home | $100 | $300 | $500 | $800 | $1,200 |
| Healthcare | $5,000 | $15,000 | $30,000 | $50,000 | $100,000 |
| Ground AV | $500 | $1,500 | $3,000 | $5,000 | $8,000 |

---

## 14. Regulatory Burden Comparison

### 14.1 Certification Complexity Index

We define a Regulatory Complexity Score (RCS) on a 1–10 scale based on:
- Number of applicable standards
- Cost of certification
- Time to certification
- Ongoing compliance burden

| Domain | RCS | Primary Standards | Est. Certification Cost | Est. Certification Time |
|--------|-----|-------------------|----------------------|----------------------|
| Healthcare | 10/10 | FDA 510(k), IEC 62304, HIPAA, ISO 13485 | $500K–$5M | 2–5 years |
| Mining | 9/10 | IEC 60079, ATEX, MSHA, ISO 19296 | $200K–$2M | 1–3 years |
| Factory | 8/10 | ISO 10218, IEC 62443, ISO 13849, OSHA | $100K–$1M | 6–18 months |
| Marine | 7/10 | IEC 60945, SOLAS, IMO, ABYC | $50K–$500K | 6–12 months |
| Ground AV | 7/10 | ISO 3691-4, B56.5, ISO 13849 | $50K–$500K | 6–12 months |
| Agriculture | 6/10 | ISO 11783, ISO 4254, EPA | $30K–$300K | 3–9 months |
| HVAC | 5/10 | ASHRAE 135, UL 864, EN 15232 | $10K–$100K | 1–6 months |
| Home | 4/10 | FCC Part 15, UL 60335, Matter | $5K–$50K | 1–3 months |

### 14.2 Liability Exposure

| Domain | Typical Liability per Incident | Insurance Premium Impact | Regulatory Enforcement |
|--------|------------------------------|------------------------|----------------------|
| Healthcare | $1M–$100M+ | Extreme | FDA audit, product recall |
| Mining | $500K–$50M | Very High | MSHA investigation, fines |
| Factory | $100K–$10M | High | OSHA citation, willful violation |
| Marine | $100K–$10M | High | Coast Guard investigation, USCG |
| Ground AV | $50K–$5M | Medium-High | OSHA, state regulations |
| Agriculture | $10K–$1M | Medium | EPA, state agricultural dept |
| HVAC | $1K–$100K | Low | Local building codes |
| Home | $1K–$50K | Low | Consumer protection, local codes |

---

## 15. Market Size and Competitive Landscape

### 15.1 Total Addressable Market (TAM) Summary

| Domain | 2024 Market | 2027 Projected | CAGR | NEXUS Serviceable Market |
|--------|-----------|---------------|------|------------------------|
| Marine | $3.2B | $4.5B | 12.3% | $500M (12%) |
| Agriculture | $12.1B | $20.6B | 19.4% | $800M (4%) |
| Factory | $190B | $265B | 11.7% | $2.0B (0.8%) |
| Mining | $4.3B | $5.6B | 9.2% | $200M (4%) |
| HVAC | $90B | $136B | 14.8% | $1.5B (1.1%) |
| Home | $98B | $182B | 22.9% | $5.0B (2.7%) |
| Healthcare | $22B | $44B | 26.0% | $300M (0.7%) |
| Ground AV | $6.5B | $12.3B | 23.7% | $1.0B (8%) |

### 15.2 Competitive Density

| Domain | Number of Major Competitors | Market Leader Share | Entry Difficulty |
|--------|---------------------------|-------------------|-----------------|
| Factory | 20+ | Siemens ~15% | Very High |
| HVAC | 15+ | Siemens/Honeywell ~20% each | High |
| Home | 30+ | Amazon/Google/Apple ~40% combined | Very High |
| Marine | 10+ | Garmin ~25% | High |
| Agriculture | 10+ | John Deere ~30% | Very High |
| Ground AV | 15+ | Fragmented, no clear leader | Medium |
| Mining | 5+ | Caterpillar/Sandvik ~40% each | Very High |
| Healthcare | 5+ | Intuitive Surgical ~60% (surgical) | Extreme |

### 15.3 NEXUS Differentiation Strength

| Domain | Differentiation Strength | Key Differentiator |
|--------|------------------------|-------------------|
| Marine | ★★★★★ | Trust-gated autonomy, reflex learning, marine-specific safety policy |
| Agriculture | ★★★★☆ | ISOBUS integration, adaptive precision, low-cost nodes |
| Factory | ★★★☆☆ | Learning capabilities vs. static PLCs; requires safety PLC bridge |
| Mining | ★★★★☆ | Harsh environment expertise, gas monitoring integration |
| HVAC | ★★★☆☆ | Energy optimization learning, but BACnet integration is key barrier |
| Home | ★★★☆☆ | Safety framework vs. consumer platforms; needs Matter integration |
| Healthcare | ★★☆☆☆ | Regulatory barriers dominate; technology differentiation secondary |
| Ground AV | ★★★★☆ | Trust-gated autonomy, SLAM + learning, fleet coordination |

---

## 16. Universal vs. Domain-Specific Feature Decomposition

### 16.1 Universal NEXUS Features (All Domains)

| Feature | Percentage of Codebase | Domain-Specific Customization |
|---------|----------------------|------------------------------|
| Wire Protocol (COBS framing) | 100% universal | None |
| Safety Rules SR-001 to SR-010 | 100% universal | None |
| Trust Score Algorithm | 80% universal | α_gain, α_loss, risk_factor, subsystem_weights |
| VM Bytecode Engine | 95% universal | Cycle budget, instruction subset |
| Jetson Cluster API | 80% universal | Module-specific Python classes |
| MQTT Bridge | 90% universal | Topic schemas, QoS requirements |
| Configuration System | 85% universal | Domain-specific overrides |
| OTA Update | 95% universal | Safety validation pipeline stages |

### 16.2 Domain-Specific Components

| Component | Marine | Ag | Factory | Mining | HVAC | Home | Health | AV |
|-----------|--------|-----|---------|--------|------|------|--------|-----|
| Sensor Drivers | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Actuator Profiles | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Domain Safety Rules | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Communication Protocol | NMEA | ISOBUS | Modbus/EtherCAT | Leaky feeder | BACnet | Matter/WiFi | HL7/MQTT | WiFi/Mesh |
| Environmental Enclosure | IP67 | IP66 | IP54 | IP68+Ex | IP40 | IP30 | IPX4 | IP54–65 |
| Regulatory Cert | IEC 60945 | ISO 4254 | ISO 13849 | ATEX | UL 864 | FCC Pt15 | IEC 60601 | ISO 3691-4 |

### 16.3 Estimated Codebase Split

```
Universal Core:          55%  (~10,500 lines)
  - Wire protocol, VM, safety engine, trust algorithm, cluster API

Common Domain Abstraction Layer: 20%  (~3,800 lines)
  - Sensor driver registry, actuator profiles, config system

Domain-Specific Extensions: 25%  (~4,900 lines)
  - Domain safety rules (8 × ~200 lines each = 1,600 lines)
  - Communication protocol adapters (8 × ~200 lines each = 1,600 lines)
  - Domain-specific reflex patterns (8 × ~200 lines each = 1,600 lines)
```

---

## 17. Research Challenges Synthesis

### 17.1 Cross-Cutting Challenges (All Domains)

| Challenge | Severity | Domains Affected | Research Area |
|-----------|----------|-----------------|---------------|
| **Certification for adaptive systems** | Critical | All | Formal methods, runtime verification |
| **Security of learned behaviors** | Critical | All | Adversarial ML, sandboxing |
| **Multi-domain configuration management** | High | All | Software engineering, DSL design |
| **Sensor fusion for reliability** | High | All | Signal processing, ML |
| **Explainability of trust decisions** | Medium | All | XAI, HCI |

### 17.2 Domain-Specific Challenge Matrix

| Challenge | Marine | Ag | Factory | Mining | HVAC | Home | Health | AV |
|-----------|--------|-----|---------|--------|------|------|--------|-----|
| GPS-denied navigation | ● | ● | ○ | ● | ○ | ○ | ○ | ● |
| Extreme environments | ● | ● | ○ | ● | ○ | ○ | ○ | ○ |
| Human proximity safety | ○ | ● | ● | ● | ○ | ○ | ● | ● |
| Legacy system integration | ● | ● | ● | ○ | ● | ● | ● | ○ |
| Non-stationary dynamics | ● | ● | ○ | ○ | ● | ○ | ● | ● |
| Regulatory fragmentation | ● | ● | ● | ● | ● | ● | ● | ● |
| Cost sensitivity | ○ | ● | ○ | ○ | ● | ● | ○ | ● |
| Privacy requirements | ○ | ○ | ○ | ○ | ○ | ● | ● | ○ |
| Fleet coordination | ○ | ● | ● | ● | ○ | ○ | ○ | ● |
| Certification cost/time | ● | ○ | ● | ● | ○ | ○ | ● | ● |

● = Primary concern, ○ = Secondary concern

---

## 18. Conclusions and Recommendations

### 18.1 Domain Prioritization Matrix

| Domain | Technical Feasibility | Market Opportunity | Safety Risk | Regulatory Burden | **Priority Score** |
|--------|---------------------|-------------------|------------|------------------|-------------------|
| HVAC | High | Very High | Low | Low | **9.5/10** |
| Home | High | Very High | Low | Low | **9.0/10** |
| Marine | High | High | High | Medium | **8.0/10** |
| Agriculture | Medium | High | Medium | Medium | **7.5/10** |
| Ground AV | Medium | High | High | Medium | **7.0/10** |
| Factory | Medium | Medium | High | High | **6.0/10** |
| Mining | Low | Medium | Very High | Very High | **4.0/10** |
| Healthcare | Low | High | Very High | Extreme | **3.5/10** |

### 18.2 Recommended Implementation Order

**Phase 1 (Months 1–6):** HVAC + Home Automation
- Lowest risk, fastest trust accumulation, largest market
- Validates core platform with minimal regulatory overhead
- Generates revenue to fund higher-risk domain development

**Phase 2 (Months 4–12):** Marine (reference domain)
- Leverages original NEXUS design
- Strong trust parameters already validated in Round 1
- IEC 60945 certification pathway is well-understood

**Phase 3 (Months 8–18):** Agriculture + Ground AV
- Medium complexity, good market opportunity
- Shared sensor/actuator requirements between domains
- GPS RTK navigation is a common capability

**Phase 4 (Months 12–24):** Factory Automation
- Requires safety PLC bridge for certification
- Significant competitive moat if achieved
- Leverages Phase 3 sensor/actuator experience

**Phase 5 (Months 18–36):** Mining + Healthcare
- Highest barriers, highest rewards
- Mining: requires ATEX certification expertise
- Healthcare: requires FDA regulatory strategy

### 18.3 Key Architectural Recommendations

1. **Abstraction Layer Investment** — The 20% codebase for common domain abstraction should be prioritized to enable rapid domain expansion
2. **Trust Parameter Configuration** — Domain-specific trust parameters (α_gain, α_loss, risk_factors) should be externalized to JSON configuration, not compiled in
3. **Safety Policy Plugin Architecture** — Domain-specific safety rules should be loadable modules, not hardcoded
4. **Communication Protocol Abstraction** — A communication adapter pattern should abstract NMEA, ISOBUS, BACnet, Matter, and other protocols behind a common NEXUS interface
5. **Hardware Platform Variants** — Create 3 hardware tiers: Consumer (home, HVAC), Industrial (factory, agriculture, AV), and Harsh (marine, mining, healthcare)

---

*End of Cross-Domain Application Analysis — Round 2A Deliverable 1*
