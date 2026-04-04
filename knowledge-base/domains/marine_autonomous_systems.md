# Marine Autonomous Systems — Complete Technical Encyclopedia

**Classification:** Domain Knowledge Base — Marine Autonomous Vessels  
**Version:** 1.0.0  
**Date:** 2025-01-15  
**Maintainer:** NEXUS Platform Knowledge Engineering  
**Cross-Reference ID:** NEXUS-KB-MARINE-001  
**Target Audience:** Robotics engineers, marine autonomy developers, safety engineers, regulatory compliance teams  

---

## Table of Contents

1. [History of Marine Autonomy](#1-history-of-marine-autonomy)
2. [Marine Vessel Types](#2-marine-vessel-types)
3. [Navigation Systems](#3-navigation-systems)
4. [Propulsion and Control](#4-propulsion-and-control)
5. [Environmental Sensing](#5-environmental-sensing)
6. [Maritime Communication](#6-maritime-communication)
7. [Maritime Regulations](#7-maritime-regulations)
8. [Weather and Route Planning](#8-weather-and-route-planning)
9. [Existing Marine Autonomy Systems](#9-existing-marine-autonomy-systems)
10. [Marine-Specific Safety Challenges](#10-marine-specific-safety-challenges)
11. [Autonomy Levels for Marine](#11-autonomy-levels-for-marine)
12. [NEXUS Platform Marine Integration](#12-nexus-platform-marine-integration)

---

## 1. History of Marine Autonomy

### 1.1 The Pre-Autonomous Era (1900–1970)

The history of marine automation begins not with electronics but with mechanical ingenuity. The first significant step toward vessel autonomy was the **gyroscopic autopilot**, invented by Elmer Sperry in 1912. Sperry's device used a gyroscope to detect deviation from a set heading and mechanically actuated the rudder to correct course. Initially demonstrated on the USS *Delaware* in 1915, the Sperry autopilot could maintain a heading within ±2 degrees — a capability that revolutionized naval warfare during World War I by freeing helmsmen for other duties.

The interwar period saw incremental refinements. The **Minneapolis-Honeywell Regulator Company** (later Honeywell) developed pneumatic and then electronic heading controllers for commercial vessels. These early systems were purely proportional — they corrected proportionally to heading error but could not eliminate steady-state offsets caused by wind or current. The integral term, now considered essential for marine PID control (as detailed in [[Marine PID Engineering Reference|../autopilot/01_marine_pid_engineering.txt]]), would not appear until the 1960s.

World War II accelerated marine automation development. The **LORAN** (Long Range Navigation) system, operational from 1942, provided the first electronic navigation fix for vessels beyond visual range of shore. While not autonomous, LORAN established the principle that electronic systems could replace human celestial navigation — a necessary precursor for any autonomous vessel.

### 1.2 The Electronic Navigation Revolution (1970–1990)

The **Transit** (NAVSAT) satellite navigation system, developed by the U.S. Navy and operational from 1964, was the first satellite-based navigation system available to vessels. However, Transit provided only periodic position fixes (every 30–90 minutes) and was unsuitable for real-time course-keeping. The system's limitation catalyzed research into continuous satellite navigation.

**GPS (Global Positioning System)** achieved Initial Operational Capability in 1978 and Full Operational Capability in 1995, transforming marine navigation forever. For the first time, vessels could obtain continuous, accurate position fixes (±10–15 meters with Selective Availability, ±2–5 meters after SA was disabled in 2000). This capability made waypoint-following autopilots practical — the autopilot could now compute cross-track error and steer to correct it, not merely hold a heading.

Simultaneously, the **microprocessor revolution** reached marine electronics. Companies like **Raytheon** (Raymarine), **Robertson** (now Simrad), and **Furuno** introduced microprocessor-based autopilots that implemented full PID heading control with gain scheduling, multiple steering modes, and NMEA 0183 integration. The **NMEA 0183 standard**, published in 1980, created a common language for marine instruments — compasses, GPS receivers, wind sensors, and autopilots could all communicate over a simple RS-422 serial link at 4,800 baud. This standardization was foundational for any integrated autonomy system.

### 1.3 The Autonomous Surface Vessel Era (1990–2015)

The 1990s and 2000s saw the emergence of the first true **Autonomous Surface Vehicles (ASVs)** — vessels capable of navigating without human intervention. Key milestones include:

| Year | Milestone | Significance |
|------|-----------|--------------|
| 1993 | MIT SCOUT autonomous sailboat | First autonomous sailboat to cross the Atlantic (attempted); proved wind-vane self-steering could be automated |
| 1998 | USV Demo I (US Navy) | Military demonstrated autonomous patrol capability using remote control with rudimentary waypoint following |
| 2001 | USV Demo II | Added collision avoidance using radar and AIS; tested obstacle detection algorithms |
| 2006 | AutoNaut (ASV Global) | First commercially available wave-powered USV for ocean data collection |
| 2010 | SailBuoy (Offshore Sensing) | Wind-and-solar-powered autonomous surface vehicle capable of multi-month deployments |
| 2012 | *Mayflower Autonomous Research Ship* concept announced | Rolls-Royce and MSubs propose fully autonomous Atlantic crossing |
| 2014 | DARPA Anti-Submarine Warfare Continuous Trail Unmanned Vessel (ACTUV) | 132-foot autonomous trimaran for submarine tracking; demonstrated 100+ days autonomous operation |
| 2015 | *Viking Lady* (Kongsberg/Wärtsilä) | First cargo ship equipped with autonomous navigation bridge concept; remote control from shore |

### 1.4 The MASS Revolution (2015–Present)

The International Maritime Organization (IMO) began formal discussions on **Maritime Autonomous Surface Ships (MASS)** in 2016, releasing a scoping study in 2018 that defined four degrees of autonomy (see [[Section 11: Autonomy Levels for Marine|#11-autonomy-levels-for-marine]]). This regulatory attention catalyzed industry investment:

| Year | Milestone | Organization |
|------|-----------|--------------|
| 2017 | YARA Birkeland autonomous container vessel announced | YARA / Kongsberg |
| 2018 | 100% autonomous ferry crossing (Suomenlinna, Finland) | Finferries / Rolls-Royce |
| 2019 | *Mayflower Autonomous Ship* (MAS400) launched | IBM / Promare / ProMare |
| 2020 | 100% autonomous cargo ship trial (Tianjin, China) | Zhenhua Heavy Industries |
| 2021 | NEXUS platform architecture published | NEXUS Project (see [[NEXUS Wire Protocol Specification|../specs/protocol/wire_protocol_spec.md]]) |
| 2022 | IMO MASS Code draft circulated for comment | IMO MSC 106 |
| 2023 | Sea Machines SM300 installed on commercial workboats | Sea Machines Robotics |
| 2024 | First autonomous vessel traffic service trial | Norwegian Maritime Authority |
| 2025 | IMO MASS Code expected adoption | IMO |

The transition from "autopilot" (heading hold) to "autonomous navigation" (route planning, obstacle avoidance, regulatory compliance) represents a paradigm shift equivalent to the transition from human celestial navigation to GPS. The key enabling technologies — AI perception, edge computing, satellite communication (Starlink), and regulatory frameworks — have all matured in parallel.

---

## 2. Marine Vessel Types

Marine autonomous systems span an enormous range of vessel types, from 2-meter USVs to 400-meter container ships. The [[NEXUS Safety System Specification|../specs/safety/safety_system_spec.md]] defines marine domain overrides in `safety_policy.json` that adapt platform safety rules for each vessel class.

### 2.1 Comprehensive Vessel Type Comparison

| Vessel Type | Length Range | Displacement | Speed Range | Endurance | Primary Sensors | Typical Autonomy Level | Key Challenges |
|-------------|:-----------:|:------------:|:-----------:|:---------:|-----------------|:---------------------:|----------------|
| **Unmanned Surface Vehicle (USV)** | 2–8 m | 50–2,000 kg | 3–15 kts | 8–72 hrs | GPS, AIS, radar, stereo camera | L4–L5 | Power budget, weight, survivability |
| **Autonomous In-Water Survey** | 4–12 m | 500–10,000 kg | 3–8 kts | 12–96 hrs | MBES, SBP, USBL, CTD | L4–L5 | Sonar data quality, survey line accuracy |
| **Patrol / Security Vessel** | 8–20 m | 5–50 tons | 15–40 kts | 12–48 hrs | Radar, EO/IR, AIS, acoustic | L3–L4 | High-speed collision avoidance, pursuit logic |
| **Workboat / Tug** | 12–30 m | 50–500 tons | 5–15 kts | 8–24 hrs | Radar, AIS, DP sensors, wind | L2–L3 | Precise station-keeping, line handling |
| **Ferry / Passenger** | 30–200 m | 200–20,000 tons | 10–25 kts | 4–12 hrs | Radar, AIS, ECDIS, CCTV, passenger count | L1–L3 | Passenger safety, dense traffic, docking |
| **Fishing Vessel** | 10–60 m | 50–3,000 tons | 8–15 kts | 3–14 days | Radar, AIS, sonar, net sensors, catch monitoring | L2–L4 | Gear handling, catch identification (see [[Marine AI Systems Brief|../vessel-platform/14_marine_ai_systems.txt]]) |
| **Cargo / Container Ship** | 100–400 m | 10,000–200,000 DWT | 12–25 kts | 14–60 days | Radar, AIS, ECDIS, weather routing, engine monitoring | L2–L4 | Port approach, traffic separation, cargo shift |
| **Research Vessel** | 20–100 m | 500–10,000 tons | 8–15 kts | 14–60 days | Scientific sonar, CTD, ADCP, weather, winch control | L2–L3 | Station-keeping in weather, winch coordination |
| **Offshore Support Vessel** | 50–100 m | 3,000–10,000 tons | 8–14 kts | 21–60 days | DP, radar, AIS, motion reference, wind | L2–L3 | Dynamic positioning, wave compensation |

### 2.2 Sensor Suite Requirements by Autonomy Level

The sensor suite complexity scales dramatically with autonomy level, as defined by the [[INCREMENTS Framework|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]]:

| Autonomy Level | Minimum Navigation | Perception | Environmental | Communication | Total Sensor Cost |
|:--------------:|-------------------|-----------|--------------|---------------|:-----------------:|
| L0 — Manual | GPS, compass | None | None | VHF | $2,000 |
| L1 — Advisory | GPS, compass, depth | None | Wind speed/dir | VHF, cellular | $5,000 |
| L2 — Assisted | GPS, compass, AIS, depth | Forward camera | Wind, temp | VHF, cellular | $15,000 |
| L3 — Supervised | Dual GPS, IMU, AIS, radar, depth | Stereo cameras, lidar | Wind, waves, current | VHF, 4G, satellite | $50,000 |
| L4 — Autonomous | GNSS/INS, radar, AIS, ECDIS, depth | Multi-camera, lidar, sonar | Full weather suite | All channels redundant | $150,000+ |
| L5 — Fully Autonomous | Triple-redundant nav, multi-radar | Full perception suite | Full + predictive models | All + inter-vessel | $300,000+ |

### 2.3 Fishing Vessel Specialization

Fishing vessels represent a particularly challenging autonomy target due to the complexity of fishing operations. The [[Marine AI Systems Technical Brief|../vessel-platform/14_marine_ai_systems.txt]] details the NEXUS approach to fishing vessel autonomy, including:

- **Species identification** using YOLOv8-nano edge inference on [[Jetson-Bravo]] vision nodes
- **Catch rate tracking** with scale and measuring board integration
- **Depth sounder integration** for bottom classification and fish school detection
- **Reinforcement learning** framework for continuous model improvement
- **Night operations** using IR illumination and thermal imaging

The fishing vessel sensor suite is distinct from other vessel types in its emphasis on biological perception (fish identification, catch counting) rather than purely navigational sensing.

---

## 3. Navigation Systems

Navigation is the most safety-critical subsystem of any autonomous marine vehicle. The NEXUS platform's [[72-field UnifiedObservation model|../specs/jetson/learning_pipeline_spec.md]] captures the full navigation state, while the [[safety_policy.json|../specs/safety/safety_policy.json]] enforces depth thresholds and speed limits specific to the marine domain.

### 3.1 Primary Navigation Sensors

#### 3.1.1 GPS/GNSS

| Parameter | GPS (L1 C/A) | DGPS | RTK | Multi-constellation (GPS+GLONASS+Galileo+BeiDou) |
|-----------|:-----------:|:----:|:---:|:------------------------------------------------:|
| **Horizontal accuracy** | 2–5 m | 0.5–1.5 m | 1–2 cm | 1–3 m (standalone), 0.5 m (SBAS) |
| **Update rate** | 1–10 Hz | 1–5 Hz | 1–20 Hz | 1–20 Hz |
| **Acquisition time** | 30–60 s (cold) | 30–60 s + correction link | 10–30 s + base link | 20–40 s (cold) |
| **Cost (receiver)** | $50–500 | $500–2,000 | $5,000–20,000 | $200–2,000 |
| **Marine suitability** | Basic | Good | Excellent (port ops) | Good (open ocean) |
| **Failure modes** | Multipath (harbors), jamming, spoofing | Correction link loss | Base link distance limit, link loss | Ionospheric scintillation |

**NEXUS Implications:** The [[NEXUS Wire Protocol|../specs/protocol/wire_protocol_spec.md]] transports GPS data via TELEMETRY messages (0x06) at up to 100 Hz update rates over RS-422. GPS spoofing detection requires redundant position sources — NEXUS addresses this at L3+ through cross-referencing GPS with AIS and radar tracks.

#### 3.1.2 Inertial Navigation System (INS)

| Parameter | MEMS IMU | FOG IMU | Ring Laser Gyro | Marine INS (Navigation Grade) |
|-----------|:-------:|:------:|:--------------:|:----------------------------:|
| **Heading drift** | 1–10 °/hr | 0.01–0.1 °/hr | 0.001–0.01 °/hr | <0.001 °/hr |
| **Position drift** | 1 km/hr | 1 km/day | 100 m/day | 10 m/day |
| **Update rate** | 100–1000 Hz | 50–200 Hz | 50–100 Hz | 50–100 Hz |
| **Cost** | $10–500 | $5,000–50,000 | $50,000–500,000 | $100,000–1,000,000 |
| **Size/weight** | <100 g | 1–10 kg | 5–50 kg | 10–100 kg |
| **MTBF** | 50,000 hrs | 100,000 hrs | 200,000 hrs | 300,000 hrs |

INS is essential for maintaining heading and position during GPS outages. The **NEXUS autopilot PID** (see [[Marine PID Engineering|../autopilot/01_marine_pid_engineering.txt]]) uses heading data at 10 Hz with derivative-on-measurement filtering to avoid noise amplification.

#### 3.1.3 Marine Radar

| Parameter | Solid-State (X-band) | Magnetron (X-band) | S-band | Broadband |
|-----------|:--------------------:|:------------------:|:------:|:---------:|
| **Frequency** | 9.4 GHz | 9.4 GHz | 3.0 GHz | 5.5–6.5 GHz |
| **Range** | 24–72 NM | 48–96 NM | 48–96 NM | 24–48 NM |
| **Range resolution** | 10–20 m | 10–20 m | 30–50 m | 5–10 m |
| **Update rate** | 24–40 RPM | 24–30 RPM | 12–24 RPM | 30–60 RPM |
| **Target detection** | Good (small boats) | Good (all targets) | Good (weather, large targets) | Excellent (close-range) |
| **Emissions** | Low (no magnetron) | High | Medium | Very low |
| **MTBF** | 50,000 hrs | 10,000 hrs | 15,000 hrs | 60,000 hrs |
| **Cost** | $3,000–15,000 | $2,000–10,000 | $8,000–25,000 | $4,000–12,000 |

Radar is the primary collision avoidance sensor for marine autonomy. [[COLREGs compliance]] (see [[Section 7: Maritime Regulations|#7-maritime-regulations]]) requires radar-based target detection and tracking for autonomous vessel operation.

### 3.2 Navigation Accuracy Requirements by Autonomy Level

| Navigation Function | L0 Manual | L1 Advisory | L2 Assisted | L3 Supervised | L4 Autonomous | L5 Fully Autonomous |
|--------------------|:---------:|:-----------:|:-----------:|:------------:|:------------:|:-------------------:|
| **Position accuracy** | ±50 m | ±25 m | ±10 m | ±5 m | ±3 m | ±1 m |
| **Heading accuracy** | ±5° | ±3° | ±2° | ±1° | ±0.5° | ±0.3° |
| **Speed accuracy** | ±1 kt | ±0.5 kt | ±0.3 kt | ±0.2 kt | ±0.1 kt | ±0.1 kt |
| **Depth accuracy** | ±5 m | ±3 m | ±2 m | ±1 m | ±0.5 m | ±0.3 m |
| **Redundancy** | None | None | Single backup | Dual | Triple | Triple + diverse |

### 3.3 NMEA Integration

Marine navigation relies heavily on **NMEA 0183** and **NMEA 2000** protocols. The NEXUS ESP32 autopilot firmware processes NMEA sentences at 4800–38,400 baud (see [[NMEA Sentence Map|../autopilot/config/nmea_sentence_map.json]]). Key sentences include:

| Sentence | Function | Update Rate | Criticality |
|----------|----------|:-----------:|:-----------:|
| `$HDM` | Magnetic heading | 5–10 Hz | Safety-critical |
| `$HDT` | True heading | 5–10 Hz | Safety-critical |
| `$GGA` / `$GNS` | GPS position fix | 1–5 Hz | Safety-critical |
| `$VHW` | Water speed | 1 Hz | Important (gain scheduling) |
| `$MWV` | Wind speed/direction | 1–5 Hz | Important (disturbance) |
| `$DBT` | Depth below transducer | 1 Hz | Safety-critical |
| `$APB` | Autopilot command | 1–2 Hz | Command |
| `$AIVDM` | AIS vessel data | Event-driven | Safety-critical |

---

## 4. Propulsion and Control

### 4.1 Propulsion Types

| Propulsion Type | Speed Range | Efficiency | Complexity | Typical Vessel | Autonomous Suitability |
|----------------|:-----------:|:----------:|:----------:|:--------------:|:---------------------:|
| **Diesel Direct** | 8–25 kts | High | Medium | Cargo, workboat | High (proven reliability) |
| **Diesel-Electric** | 6–20 kts | Very High | High | Ferry, research, OSV | Very High (precise control) |
| **Hybrid (Diesel+Battery)** | 4–18 kts | High | Very High | Ferry, patrol | High (silent running mode) |
| **Full Electric** | 4–12 kts | Medium | Medium | Harbor craft, USV | Excellent (clean integration) |
| **Gas Turbine** | 25–40 kts | Low | Very High | Naval patrol | Low (poor throttle response) |
| **Sail** | 3–15 kts | Excellent | Medium | Sailboat, survey USV | Medium (wind dependency) |
| **Waterjet** | 15–50 kts | Low | High | Patrol, passenger | Low (poor low-speed control) |

### 4.2 Steering Actuator Types

| Actuator Type | Response Time | Authority | Failure Mode | Marine Use | NEXUS Wire Protocol Mapping |
|--------------|:------------:|:---------:|--------------|:-----------:|:---------------------------:|
| **Hydraulic Cylinder** | 100–300 ms | Very High (10,000+ lbf) | Seal failure, pump failure | 30–200 ft vessels | `motor_pwm` (solenoid valve control via [[safety_policy.json actuator profiles|../specs/safety/safety_policy.json]]) |
| **Electromechanical Actuator** | 50–200 ms | Medium (500–5,000 lbf) | Motor stall, gear failure | 15–60 ft vessels | `servo` (direct PWM drive) |
| **Solenoid Valve** | 50–150 ms | High (via hydraulic pump) | Coil burnout, contamination | Common autopilot interface | `solenoid` (with 5s max on-time per safety policy) |
| **Azimuth Thruster** | 200–500 ms | Very High (360° steering) | Hydraulic failure, calibration drift | Workboats, tugs, ferries | `motor_pwm` + `servo` (combined speed+direction) |
| **Rudder + Skeg** | 100–300 ms | High | Rudder stock failure | Sailboats, displacement hulls | `servo` or `solenoid` |
| **Bow Thruster** | 100–200 ms | Medium | Propeller fouling, motor failure | Docking, station-keeping | `motor_pwm` |

### 4.3 NEXUS Actuator Safety Mapping

The [[NEXUS safety policy|../specs/safety/safety_policy.json]] defines strict actuator safety profiles for marine use:

| NEXUS Actuator Profile | Marine Equivalent | Safe State | Rate Limit | Domain Override (Marine) |
|----------------------|------------------|------------|------------|:------------------------:|
| `servo` | Rudder actuator | Center (1500 µs) | 200 µs/10ms | Max ±45° deflection |
| `solenoid` | Hydraulic valve | De-energized | 5 activations/10s | 5s max on-time, 1s cooldown |
| `motor_pwm` | Thruster/azimuth | 0% duty | 10%/100ms | Max 80% throttle autonomous |
| `relay` | Bilge pump, lights | Open | 30 cycles/min | Bilge pump auto-permit at L4+ |

### 4.4 Control Loop Architecture

The NEXUS marine control system implements a **cascaded control architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│  COGNITIVE LAYER (Jetson)                                       │
│  Route planning, weather routing, COLREGs reasoning             │
│  → Generates waypoint commands, speed orders                    │
│  → Update rate: 0.01–0.1 Hz                                    │
├─────────────────────────────────────────────────────────────────┤
│  GUIDANCE LAYER (Jetson)                                        │
│  Waypoint following, cross-track error minimization             │
│  → Generates heading commands to autopilot                      │
│  → Update rate: 0.5–2 Hz                                       │
│  → NMEA: $APB sentence output                                  │
├─────────────────────────────────────────────────────────────────┤
│  CONTROL LAYER (ESP32)                                          │
│  PID heading control with gain scheduling (see                 │
│  [[Marine PID Engineering|../autopilot/01_marine_pid_engineering.txt]])     │
│  → Generates rudder/thruster commands                           │
│  → Update rate: 10 Hz (NEXUS standard)                          │
│  → NMEA: $APHDG input, sensor processing                       │
├─────────────────────────────────────────────────────────────────┤
│  REFLEX LAYER (ESP32, bytecode VM — see                       │
│  [[Reflex Bytecode VM Spec|../specs/firmware/reflex_bytecode_vm_spec.md]])          │
│  Collision avoidance, depth alarm, wind gust response            │
│  → Direct actuator override, no cognitive involvement            │
│  → Response: <10 ms (hardware interrupt)                        │
│  → 32-opcode stack machine, 50,000 cycle budget                │
├─────────────────────────────────────────────────────────────────┤
│  HARDWARE INTERLOCK (Tier 1 — see                              │
│  [[Safety System Spec|../specs/safety/safety_system_spec.md]])                        │
│  Kill switch, polyfuses, hardware watchdog, pull-downs           │
│  → Response: <1 ms                                             │
│  → Authority: ABSOLUTE                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Environmental Sensing

The marine environment is among the most hostile and dynamic environments for autonomous systems. The NEXUS platform's [[72-field UnifiedObservation model|../specs/jetson/learning_pipeline_spec.md]] captures the complete environmental state.

### 5.1 Environmental Parameter Matrix

| Parameter | Sensor Type | Measurement Range | Accuracy | Update Rate | Mounting | Signal Processing |
|-----------|------------|-------------------|:--------:|:-----------:|----------|-------------------|
| **Wind speed** | Cup anemometer | 0–60 m/s | ±0.3 m/s | 1–10 Hz | Masthead (10–20m) | Moving average (5s), gust detection |
| **Wind direction** | Vane / ultrasonic | 0–360° | ±3° | 1–10 Hz | Masthead | True/apparent conversion, heel correction |
| **Wave height** | Accelerometer (MRU) | 0–30 m | ±0.5 m | 1–10 Hz | Bilge/midships | Spectral analysis, Hs, Tp, direction |
| **Wave period** | Accelerometer (MRU) | 1–25 s | ±0.5 s | 1–10 Hz | Bilge/midships | FFT, peak detection |
| **Wave direction** | Wave radar / MRU | 0–360° | ±10° | 0.01 Hz | Masthead / hull | 2D FFT, directional spectrum |
| **Current speed** | ADCP / doppler log | 0–5 m/s | ±0.05 m/s | 0.1–1 Hz | Hull bottom | Profile averaging, tidal correction |
| **Current direction** | ADCP / doppler log | 0–360° | ±5° | 0.1–1 Hz | Hull bottom | Profile averaging |
| **Water temperature** | Thermistor / CTD | -2–40 °C | ±0.01 °C | 0.1–1 Hz | Hull (intake) | Calibration, offset correction |
| **Salinity** | CTD | 0–42 PSU | ±0.01 PSU | 0.1–1 Hz | Hull (intake) | Calibration, pressure compensation |
| **Air temperature** | Shielded thermistor | -40–60 °C | ±0.3 °C | 0.1–1 Hz | Masthead | Radiation shield, aspiration |
| **Barometric pressure** | Barometer | 880–1080 hPa | ±0.5 hPa | 0.01 Hz | Wheelhouse | Height correction, trend analysis |
| **Visibility** | Forward scatter | 10 m–50 km | ±10% | 1 Hz | Masthead | Logarithmic scaling, fog detection |
| **Sea surface temperature** | IR radiometer | -2–40 °C | ±0.1 °C | 0.1–1 Hz | Masthead | Sky reflection correction |

### 5.2 NEXUS 72-Field Observation Model

The NEXUS [[learning pipeline|../specs/jetson/learning_pipeline_spec.md]] defines a UnifiedObservation structure with 72 fields covering the complete vessel state. For marine deployments, the key environmental fields are:

| Field Category | Field Count | Example Fields | Marine Relevance |
|---------------|:-----------:|---------------|-----------------|
| Navigation | 8 | lat, lon, heading, sog, cog, altitude | Primary position/velocity |
| Attitude | 6 | roll, pitch, yaw, roll_rate, pitch_rate, yaw_rate | Wave-induced motion |
| Propulsion | 6 | throttle_port, throttle_stbd, rudder_angle, rpm, fuel_flow, boost_pressure | Engine/thruster state |
| Environmental | 16 | wind_speed, wind_dir, wave_height, wave_period, wave_dir, current_speed, current_dir, water_temp, air_temp, baro_pressure, salinity, humidity, visibility, sea_state, swell_height, swell_dir | Full environmental picture |
| Sensor Health | 12 | gps_fix_type, gps_sat_count, gps_hdop, imu_health, radar_health, ais_health, depth_sensor_health, compass_health, wind_sensor_health, comms_signal_strength, battery_voltage, cpu_temperature | Sensor validity for [[SR-004|../specs/safety/safety_policy.json]] compliance |
| Safety | 10 | heartbeat_count, override_active, safety_mode, trust_score, proximity_nearest, depth_below_keel, colregs_situation, man_overboard_alert, fire_alarm, flooding_alarm | Safety state for [[Four-Tier Safety|../specs/safety/safety_system_spec.md]] |
| Derived | 14 | cross_track_error, heading_error, speed_over_ground_delta, fuel_remaining, time_on_station, catch_count, gear_tension, winch_speed, anchor_scope, bilge_level, engine_hours, drift_angle, leeway, set | Computed values for decision-making |
| **Total** | **72** | | |

### 5.3 Environmental Signal Processing Challenges

Marine environmental sensors face unique signal processing challenges:

- **Wave motion contamination:** Accelerometer-based sensors (wave height, heading) are contaminated by vessel motion. **MRU (Motion Reference Unit)** data must be filtered using complementary filters or Kalman filters to separate wave-frequency motion from actual heading changes.
- **Salt spray and biofouling:** Optical and acoustic sensors degrade rapidly in marine environments. Anemometer cups accumulate salt crystals; depth sounders grow barnacles; cameras develop salt film. Regular maintenance schedules and self-diagnostic algorithms (correlation checks between redundant sensors) are essential.
- **Thermal gradients:** Air and water temperature sensors near the hull are affected by engine cooling water discharge. Sensor placement must account for thermal plumes.
- **EMI from propulsion systems:** Electric and hybrid propulsion systems generate significant electromagnetic interference that can corrupt low-level sensor signals (depth sounder returns, compass headings). Shielded cabling and differential signaling (RS-422, as used in the [[NEXUS Wire Protocol|../specs/protocol/wire_protocol_spec.md]]) are mandatory.

---

## 6. Maritime Communication

### 6.1 Communication System Comparison

| System | Frequency | Range | Bandwidth | Latency | Cost (monthly) | Use Case | NEXUS Integration |
|--------|-----------|:-----:|:---------:|:-------:|:--------------:|----------|:-----------------:|
| **VHF Voice** | 156 MHz | 20–60 NM | 3 kHz (voice) | Low (human) | $0 | Safety, bridge-to-bridge | External (speaker/audio) |
| **VHF DSC** | 156 MHz | 20–60 NM | 0.3 kbps | <1 s | $0 | Distress, positional reports | AIS via NMEA decoder |
| **AIS (Class A/B)** | 156 MHz | 20–60 NM (VHF) | 9.6 kbps | <1 s | $0 (receiver) | Vessel tracking, collision avoidance | NMEA $AIVDM → ESP32 parsing |
| **Cellular (4G/5G)** | 700–3900 MHz | Coast (2–30 km) | 10–100 Mbps | 20–100 ms | $50–200 | Coastal ops, telemetry, cloud | Jetson Wi-Fi → cellular bridge |
| **Satellite (Starlink Maritime)** | Ku/Ka band | Global | 100–350 Mbps down / 20–40 Mbps up | 20–50 ms | $2,500–5,000 | Ocean-going, real-time cloud | Jetson Ethernet → Starlink dish |
| **Satellite (Iridium Certus)** | L-band | Global | 0.7–176 kbps | 1–5 s | $200–2,000 | Low-bandwidth telemetry, distress | Serial → Iridium transceiver |
| **Satellite (Inmarsat VSAT)** | Ku/Ka band | Global | 0.5–10 Mbps | 600 ms+ | $1,000–10,000 | Legacy ocean connectivity | Jetson Ethernet → VSAT |
| **Underwater Acoustic** | 8–100 kHz | 1–50 km | 100 bps–10 kbps | 0.5–5 s | N/A | AUV/USV communication, subsea | Not directly supported |
| **Wi-Fi (802.11)** | 2.4/5 GHz | 100–500 m | 50–1000 Mbps | 1–10 ms | $0 | Vessel LAN, camera network | Jetson → ESP32 → cameras |

### 6.2 RS-422 for Inter-Vessel Communication

The NEXUS [[Wire Protocol Specification|../specs/protocol/wire_protocol_spec.md]] uses **EIA/TIA-422-B (RS-422)** as its physical layer for inter-node communication within the vessel. RS-422 is also widely used in marine equipment:

| RS-422 Parameter | NEXUS Specification | Marine Equipment Standard |
|-----------------|:------------------:|:-------------------------:|
| **Baud rate** | 115,200–921,600 bps | 4,800 bps (NMEA 0183) |
| **Mode** | Full-duplex, differential | Single-duplex (listen/talk) |
| **Max cable length** | 10–100 m | 100 m+ |
| **Connector** | RJ-45 | Terminal block, DB-9 |
| **Impedance** | 120 Ω differential termination | 120 Ω |
| **Transceiver** | TI THVD1500 | Various (Maxim, TI) |

**Why RS-422 for NEXUS?**
1. **Noise immunity:** Differential signaling rejects common-mode noise, critical in marine environments with EMI from engines, VHF radios, and lightning.
2. **Deterministic latency:** Unlike Ethernet (CSMA/CD or CSMA/CA), RS-422 has no contention — message latency is predictable and bounded.
3. **Point-to-point simplicity:** No switch infrastructure required; direct wire between Jetson and ESP32 nodes.
4. **Marine heritage:** Every marine instrument shop stocks RS-422 cabling and connectors.
5. **Galvanic isolation:** Easy to add opto-isolation for ground loop prevention between hull zones.

### 6.3 Communication Reliability Comparison

| Failure Mode | VHF | AIS | Cellular | Starlink | Underwater Acoustic | NEXUS RS-422 |
|-------------|:---:|:---:|:--------:|:--------:|:------------------:|:------------:|
| Weather degradation | High | Medium | Low | Low | Very High | None |
| Interference | Medium | Low | Medium | Low | Very High | Very Low |
| Physical damage (antenna) | Medium | Medium | Medium | Medium | N/A | Low (short cable) |
| Power failure | Possible | Possible | Possible | Possible | Possible | With UPS |
| Encryption | None | None | TLS | VPN | Optional | AES-128-CTR flag |
| Authentication | None | MMSI | SIM | Auth | None | Sequence numbers |
| Jamming vulnerability | High | High | Medium | Low | High | Very Low (short range) |

---

## 7. Maritime Regulations

### 7.1 COLREGs — Convention on the International Regulations for Preventing Collisions at Sea

COLREGs (1972, in force since 1977, amended 1981, 1987, 1989, 1993, 2001, 2007) comprises 72 rules organized into 10 parts. Every rule must be encodable in the NEXUS [[safety_policy.json|../specs/safety/safety_policy.json]] for autonomous compliance.

#### 7.1.1 COLREGs Structure and NEXUS Encoding

| COLREGs Part | Rules | Content | NEXUS Encoding Priority |
|-------------|:-----:|---------|:-----------------------:|
| Part A — General | 1–3 | Application, responsibility, definitions | Foundation |
| Part B — Steering and Sailing | 4–10 | Look-out, safe speed, risk of collision, action by stand-on/give-way, narrow channels, TSS | **CRITICAL** — must encode all action rules |
| Part C — Lights and Shapes | 11–18 | Navigation lights, day shapes | Important — perception integration |
| Part D — Sound and Light Signals | 19–20 | Sound signals in restricted visibility | Important — VHF integration |
| Part E — Exemptions | 21 | Exemptions for warships | N/A |
| Part F — Verification | 22 | Compliance verification | Testing |
| Part G — Distress | 23–30 | Distress signals | **CRITICAL** — reflex layer |
| Annexes | I–IV | Technical details, additional signals | Reference |

#### 7.1.2 Key COLREGs Rules for Autonomous Encoding

| Rule | Description | NEXUS Encoding |
|------|-------------|----------------|
| **Rule 5** — Look-out | Maintain proper look-out by all available means | Radar + AIS + camera perception fusion; continuous 360° monitoring |
| **Rule 6** — Safe Speed | Proceed at safe speed for conditions | `max_speed_autonomous_kmh: 15.0` in safety_policy.json |
| **Rule 7** — Risk of Collision | Use all available means to determine risk | Bearing drift analysis, CPA/TCPA calculation |
| **Rule 8** — Action to Avoid Collision | Take early and substantial action | Reflex layer: collision avoidance maneuvers |
| **Rule 13** — Overtaking | Overtaking vessel keeps clear | Target classification (overtaking/head-on/crossing) |
| **Rule 14** — Head-on | Both alter course to starboard | Default action: +20° heading change |
| **Rule 15** — Crossing | Give-way vessel keeps clear, stand-on holds course | Target bearing analysis, give-way classification |
| **Rule 16** — Action by Give-way | Take early and substantial action | Autonomous course change with 5-min CPA margin |
| **Rule 17** — Action by Stand-on | Hold course, but act if collision imminent | Collision avoidance override reflex |
| **Rule 19** — Restricted Visibility | Navigate at safe speed, sound signals | Reduced speed, fog signal activation, radar-only navigation |
| **Rule 35** — Sound Signals | Fog signals for power-driven vessel | Auto horn activation (5s max per safety_policy buzzer profile) |

#### 7.1.3 COLREGs Compliance State Machine

```
                    ┌──────────────────┐
                    │  MONITORING     │
                    │  (Rule 5 Look-out)│
                    └────────┬─────────┘
                             │ Target detected
                             ▼
                    ┌──────────────────┐
                    │  CLASSIFICATION │
                    │  Rule 13/14/15  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ OVERTAKING│  │ HEAD-ON  │  │ CROSSING │
        │ (Rule 13)│  │ (Rule 14)│  │ (Rule 15)│
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             ▼             ▼             ▼
        ┌──────────────────────────────────────────┐
        │  RISK ASSESSMENT (Rule 7)                 │
        │  CPA < CPA_min?  TCPA < TCPA_min?         │
        └──────────────────┬───────────────────────┘
                           │ Risk detected
                           ▼
        ┌──────────────────────────────────────────┐
        │  ACTION SELECTION (Rules 8, 16, 17)       │
        │  Give-way → early, substantial action     │
        │  Stand-on → hold course + monitor         │
        └──────────────────┬───────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │  EXECUTION (REFLEX → GUIDANCE)            │
        │  Reflex: immediate rudder/throttle command│
        │  Guidance: planned course change          │
        └──────────────────────────────────────────┘
```

### 7.2 SOLAS — Safety of Life at Sea

SOLAS Chapter V (Safety of Navigation) is directly applicable to autonomous vessels:

| SOLAS Requirement | Applicability to MASS | NEXUS Compliance |
|-------------------|:---------------------:|-----------------|
| V/19 — Carriage of nautical charts | ECDIS required | Electronic chart database |
| V/20 — Navigational equipment | GPS, compass, depth sounder | Sensor suite at L3+ |
| V/21 — Gyro compass | Required >500 GT | IMU/MRU at L3+ |
| V/22 — Radar | Required >300 GT | Marine radar at L3+ |
| V/23 — AIS | Required >300 GT | AIS receiver/transponder at L2+ |
| V/24 — Speed log | Required >300 GT | Water speed sensor at L3+ |
| V/31 — Danger messages | VHF/MF DSC distress alerts | NEXUS SAFETY_EVENT (0x1C) |
| V/34 — Safe navigation | Master's responsibility | INCREMENTS human responsibility per level |

### 7.3 MARPOL — Marine Pollution

| MARPOL Annex | Content | NEXUS Domain Rules |
|-------------|---------|-------------------|
| I — Oil | Oil discharge limits | Fuel tank monitoring, bilge pump control |
| III — Noxious Liquid Substances | Chemical cargo handling | Cargo sensor integration |
| IV — Sewage | Sewage discharge rules | Holding tank monitoring |
| V — Garbage | Garbage discharge rules | Waste logging |
| VI — Air Pollution | SOx, NOx, CO2 emissions | Emissions monitoring, speed optimization |

### 7.4 IMO MASS Code

The IMO MASS Code (draft, expected 2025) defines requirements for Maritime Autonomous Surface Ships:

| MASS Code Requirement | Description | NEXUS Compliance Approach |
|---------------------|-------------|---------------------------|
| Safe manning equivalency | Autonomous system must provide safety equivalent to crew | [[Four-Tier Safety Architecture|../specs/safety/safety_system_spec.md]] provides defense-in-depth |
| Remote control center | Shore-based monitoring and intervention | Starlink communication + Jetson telemetry |
| Situational awareness | 360° perception at least equivalent to human look-out | Radar + AIS + camera fusion |
| Collision avoidance | COLREGs compliance | Encoded in safety policy rules |
| Contingency planning | Response to system failures | Reflex layer + safe state definitions |
| Data logging | Voyage data recorder equivalent | 72-field observation recording (see [[learning pipeline spec|../specs/jetson/learning_pipeline_spec.md]]) |

---

## 8. Weather and Route Planning

### 8.1 Weather Routing Algorithms

Weather routing optimizes vessel routes considering weather forecasts, sea state predictions, fuel consumption, and schedule constraints. The NEXUS cognitive layer (Jetson) implements route planning, while the reflex layer handles immediate threats.

#### 8.1.1 Algorithm Comparison

| Algorithm | Method | Complexity | Optimality | NEXUS Layer |
|-----------|--------|:----------:|:----------:|:----------:|
| **Isochrone method** | Forward propagation of reachable positions | O(N² × T) | Near-optimal | Cognitive |
| **Dijkstra with weather weights** | Graph search with edge costs = f(weather) | O((V+E) log V) | Good | Cognitive |
| **A* with heuristic** | Directed graph search with weather-admissible heuristic | O(b^d) | Very good | Cognitive |
| **Dijkstra with deterministic weather** | Modified Dijkstra with time-dependent edge costs | O(V × E × T) | Optimal (deterministic) | Cognitive |
| **Monte Carlo tree search** | Random sampling with UCB1 selection | O(n_samples × path_length) | Good (stochastic) | Cognitive |
| **DODW (Dijkstra on deterministic weather)** | Time-expanded graph | O(V² × T) | Optimal | Cognitive |

#### 8.1.2 Weather Data Sources

| Source | Resolution | Update Frequency | Coverage | Format | NEXUS Integration |
|--------|:----------:|:----------------:|:--------:|--------|:-----------------:|
| **GFS (Global Forecast System)** | 0.25° × 0.25° | Every 6 hours | Global | GRIB2 | Jetson downloads via Starlink |
| **ECMWF** | 0.1° × 0.1° | Every 6 hours | Global | GRIB2 | Jetson downloads via Starlink |
| **NOAA Wavewatch III** | 0.5° × 0.5° | Every 6 hours | Global | GRIB2 | Wave height, period, direction |
| **AMap (Area Meteorological)** | 1–5 km | Every hour | Regional | Custom | High-resolution coastal weather |
| **Ship observations (VOS)** | Point | Real-time | Global | FM 13 SHIP | Crowdsourced verification |

### 8.2 NEXUS Reflex vs. Cognitive Layer for Weather

| Threat Type | Detection | NEXUS Reflex Layer (<10 ms) | NEXUS Cognitive Layer (<5 s) |
|-------------|-----------|:--------------------------:|:---------------------------:|
| **Sudden wind gust** | Anemometer rate > 10 m/s/s | Reduce throttle, feather sails | Update weather model, adjust course |
| ** Rogue wave detection** | MRU vertical acceleration > 0.5 g | Head into waves, reduce speed | Log event, update sea state estimate |
| **Approaching squall** | Radar + barometer trend | Reef sails, secure deck cargo | Plan course diversion, estimate passage time |
| **Fog detection** | Visibility sensor + ambient humidity | Reduce speed (Rule 6), activate fog signals | Update route to avoid navigation hazards |
| **Debris detection** | Radar + camera | Emergency course change, all-stop | Update local chart, log hazard |
| **Vessel crossing (COLREGs)** | AIS + radar | Give-way action (Rule 16) | Full COLREGs reasoning, log encounter |

### 8.3 Sea State Prediction

| Sea State | Beaufort | Wave Height (Hs) | Period (Tp) | NEXUS Autonomous Speed Limit | NEXUS Operating Restriction |
|:---------:|:--------:|:----------------:|:-----------:|:---------------------------:|:--------------------------:|
| 0–1 | 0–1 | 0–0.3 m | — | Full speed | No restriction |
| 2 | 2 | 0.3–0.6 m | 1–4 s | Full speed | No restriction |
| 3 | 3 | 0.6–1.2 m | 3–6 s | 80% | No restriction |
| 4 | 4 | 1.2–2.5 m | 4–8 s | 70% | Caution — increased sensor noise |
| 5 | 5 | 2.5–4.0 m | 6–10 s | 60% | Caution — heading accuracy degraded |
| 6 | 6 | 4.0–6.0 m | 8–12 s | 40% | **Max wind speed threshold** (40 km/h) |
| 7+ | 7+ | >6.0 m | >10 s | 0% (safe state) | **Autonomous operation prohibited** |

---

## 9. Existing Marine Autonomy Systems

### 9.1 Commercial System Comparison

| Feature | Sea Machines SM300 | Kongsberg K-Pos | Rolls-Royce MAS | ASV Global | Mayflower (MAS400) | NEXUS Platform |
|---------|:------------------:|:--------------:|:--------------:|:----------:|:-----------------:|:--------------:|
| **Autonomy Level** | L2–L3 | L2 | L3 (concept) | L3–L4 | L4 | L0–L5 ([[INCREMENTS|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]]) |
| **COLREGs Compliance** | Partial (Rules 14, 15, 19) | Full (commercial) | Full (planned) | Full | Full | Encodable (all 72 rules) |
| **Sensor Fusion** | Radar + AIS + camera | Radar + AIS + DP | Radar + AIS + LiDAR | Radar + AIS + camera | Radar + AIS + LiDAR + camera | Configurable per deployment |
| **Compute Platform** | Proprietary | Kongsberg K-Chief | Proprietary | Proprietary | NVIDIA Jetson + IBM cloud | NVIDIA Jetson + ESP32 (open) |
| **Communication** | 4G + satellite | Proprietary | Satellite + cellular | 4G + satellite | Starlink + cellular | Starlink + VHF + RS-422 (open protocol) |
| **Safety Architecture** | Single-tier | Dual redundant | Triple redundant | Dual redundant | Dual + cloud monitoring | [[Four-Tier Safety|../specs/safety/safety_system_spec.md]] (hardware, firmware, supervisory, application) |
| **Vessel Size Range** | 20–60 ft | 30–300 ft | 100–400 ft | 10–30 ft (USV) | 50 ft (sail) | Configurable (any) |
| **Open Source** | No | No | No | No | Partial (software) | **Yes** (full stack) |
| **Reflex System** | Limited | No | No | Limited | No | 32-opcode [[Bytecode VM|../specs/firmware/reflex_bytecode_vm_spec.md]], <10 ms response |
| **Learning Capability** | No | No | Limited | Limited | ML-based | [[Pattern discovery|../specs/jetson/learning_pipeline_spec.md]] + edge training |
| **Trust Score Model** | No | No | No | No | No | [[Quantitative trust|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]] (asymmetric gain/loss, 25:1 ratio) |
| **Incremental Autonomy** | No (fixed level) | No | No | No | No | [[L0–L5 per-subsystem|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]] advancement |
| **Estimated Cost** | $50–150K | $200K–1M | $500K–5M | $80–300K | $5M+ (research) | $5–30K (hardware) |

### 9.2 What NEXUS Does Differently

1. **Incremental Autonomy (INCREMENTS Framework):** Unlike commercial systems that operate at a fixed autonomy level, NEXUS allows each subsystem (bilge, throttle, autopilot, navigation) to operate at its own autonomy level independently. A fishing vessel can run bilge pumps at L4 while the throttle remains at L2.

2. **Quantitative Trust Model:** NEXUS implements a mathematically rigorous trust score (T ∈ [0, 1]) with asymmetric gain/loss rates (α_gain = 0.002, α_loss = 0.05 — 25:1 ratio). Trust must be *earned* through demonstrated performance over hours of operation.

3. **Open Architecture:** NEXUS is fully open-source, from the [[ESP32 firmware|../autopilot/02_esp32_architecture.txt]] to the [[Jetson cognitive layer|../specs/jetson/learning_pipeline_spec.md]]. No vendor lock-in.

4. **Bytecode Reflex VM:** Safety-critical reflex behaviors execute on a provably deterministic [[32-opcode stack machine|../specs/firmware/reflex_bytecode_vm_spec.md]] with a 50,000-cycle budget, providing guaranteed <10 ms response times independently of the cognitive layer.

5. **Four-Tier Safety:** The [[safety architecture|../specs/safety/safety_system_spec.md]] provides four independent safety barriers (hardware interlock, firmware guard, supervisory task, application control), exceeding the single-tier safety found in most commercial systems.

6. **Edge Learning:** NEXUS can [[learn new reflex behaviors on-device|../specs/jetson/learning_pipeline_spec.md]] using observation data, A/B testing, and the Qwen2.5-Coder-7B model running on Jetson — no cloud dependency for self-improvement.

7. **Machine-Readable Safety Policy:** The [[safety_policy.json|../specs/safety/safety_policy.json]] defines all safety rules in a structured format that can be programmatically checked by the CI/CD pipeline, static analysis tools, and the runtime safety validator.

---

## 10. Marine-Specific Safety Challenges

The marine environment presents unique safety challenges that distinguish it from terrestrial autonomy domains. The NEXUS [[four-tier safety architecture|../specs/safety/safety_system_spec.md]] addresses each through layered defense.

### 10.1 Hazard Analysis and NEXUS Response

| Hazard | Severity | Probability | Detection Method | NEXUS Tier 1 (Hardware) | NEXUS Tier 2 (Firmware) | NEXUS Tier 3 (Supervisory) | NEXUS Tier 4 (Application) |
|--------|:--------:|:-----------:|-----------------|:-----------------------:|:-----------------------:|:-------------------------:|:-------------------------:|
| **Rogue wave** | Critical | Low | MRU vertical acceleration > 0.5 g | Kill switch cuts power | ISR drives rudder to head-sea | Safe state: engines idle, rudder amidships | Course change to avoid wave trains |
| **GPS spoofing** | Critical | Medium | GPS position jumps, inconsistent with INS/AIS | N/A (sensor-level) | INS dead-reckoning fallback | Multi-sensor position cross-check | Reduce autonomy level, alert operator |
| **GPS jamming** | High | Medium | GPS C/N0 drops below threshold | N/A | INS dead-reckoning, depth-based nav | Transition to DEGRADED mode | Alert operator, navigate by radar/AIS |
| **Communication loss** | High | Medium | Heartbeat timeout (500ms/1000ms) | Hardware WDT (1.0s timeout) | Safe state outputs | DEGRADED → SAFE_STATE transition | Queue commands for reconnect |
| **Man overboard** | Critical | Low | Camera detection, MOB button, AIS SART | Kill switch (human activated) | Alert ISR: alarm + position logging | Log event, activate search pattern | Autonomous search pattern (L4+ only) |
| **Fire** | Critical | Low | Smoke/heat detectors | Kill switch cuts power + fuel | Fire isolation reflex | Alert + fire suppression activation | Emergency navigation to nearest port |
| **Flooding** | Critical | Medium | Bilge level sensors, draft sensors | N/A | Bilge pump reflex (auto-activate) | Monitor pump capacity vs ingress rate | Grounding protocol if losing battle |
| **Engine failure** | High | Medium | RPM sensor, oil pressure, temperature | N/A | Sail trim adjustment (if sail) | Drift analysis, anchor deployment | Distress signal (L3+), navigation under sail |
| **Steering gear failure** | Critical | Low | Rudder angle sensor disagreement | N/A | Alternative steering (azimuth thrusters, sails) | Emergency steering mode | Alert, navigate to safe anchorage |
| **Collision** | Critical | Medium | Radar + AIS + camera fusion | Kill switch (pre-impact) | Collision avoidance reflex | COLREGs compliance engine | Post-collision damage assessment |
| **Lightning strike** | High | Low | EM field sensor, power surge | Polyfuses, TVS diodes | System reset + safe state restart | Self-test after reset | Full system re-initialization |

### 10.2 Man Overboard Response Protocol

The man overboard (MOB) scenario is a uniquely marine safety challenge with no terrestrial equivalent:

1. **Detection (Tier 4, Application):** Camera-based person detection + optional MOB button/Wearable AIS beacon
2. **Reflex (Tier 2, Firmware):** Immediate alarm, GPS position logging, engine cut (if safe), course change toward MOB
3. **Supervisory (Tier 3):** Activate search pattern, log event, notify remote operator
4. **Cognitive (Tier 4, Application — L4 only):** Execute Williamson turn or Anderson turn, compute drift, deploy rescue equipment

The NEXUS reflex layer can execute the immediate MOB response in <10 ms — faster than any human reaction. However, the cognitive-level search pattern requires L4 autonomy (no human required for routine operations), per the [[INCREMENTS framework|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]].

### 10.3 GPS Spoofing Countermeasures

GPS spoofing is an increasing threat in congested waterways and conflict zones. NEXUS addresses this through:

1. **Multi-constellation GNSS:** GPS + GLONASS + Galileo + BeiDou makes spoofing more difficult (attacker must spoof all constellations)
2. **INS cross-check:** The IMU/INS provides independent position estimation; divergence from GPS indicates possible spoofing
3. **AIS correlation:** GPS-reported vessel positions should be consistent with AIS-reported positions of nearby vessels
4. **Radar ground truth:** Coastal radar returns should be consistent with GPS-derived position
5. **Signal quality monitoring:** GPS C/N0 (carrier-to-noise density), AGC levels, and satellite geometry (HDOP) provide spoofing indicators
6. **NEXUS [[SR-004|../specs/safety/safety_policy.json]]** ensures no single sensor failure (including GPS spoofing) can cause unsafe actuation

---

## 11. Autonomy Levels for Marine

### 11.1 Three-Standard Comparison

Marine autonomy levels are defined by three independent standards. The NEXUS [[INCREMENTS Framework|../../../incremental-autonomy-framework/INCREMENTS-autonomy-framework.md]] provides the most detailed, with quantitative advancement criteria.

#### 11.1.1 Complete Level Mapping Table

| Feature | Lloyd's Register (ALV 1–5) | IMO MASS Code (Degree 1–4) | NEXUS INCREMENTS (L0–L5) |
|---------|:-------------------------:|:--------------------------:|:------------------------:|
| **L0 / Degree 1** | — | Crew on board, systems available | Manual — system records sensor data only |
| **L1** | ALV 1: Computer aids decision-making | Degree 1: Crew on board, some systems automated | Advisory — system suggests, human acts |
| **L2** | ALV 2: Remote control from another ship | Degree 2: Remotely controlled (no crew) | Assisted — system proposes actions, human approves |
| **L3** | ALV 3: Remote control with autonomous decision support | Degree 3: Remotely controlled with minimal crew | Supervised — system acts, human can override |
| **L4** | ALV 4: Fully autonomous | Degree 4: Fully autonomous (no crew) | Autonomous — system acts, human notified |
| **L5** | — | — | Fully Autonomous — system manages itself incl. maintenance |
| **Human on board?** | Varies | Degree 1–2: Yes; 3–4: No | L0–L3: Yes; L4–L5: Optional |
| **Communication required** | Varies | Continuous (1–3) | L0–L2: Periodic; L3: Available; L4: Reachable; L5: Admin only |
| **COLREGs compliance** | Human responsibility | Machine + human oversight | L0–L2: Human; L3: Human + AI; L4–L5: AI (with logging) |

#### 11.1.2 Detailed INCREMENTS Level Specifications for Marine

| Dimension | L0 Manual | L1 Advisory | L2 Assisted | L3 Supervised | L4 Autonomous | L5 Fully Autonomous |
|-----------|:---------:|:-----------:|:-----------:|:------------:|:------------:|:-------------------:|
| **Minimum sensor uptime** | 0% (no requirement) | >95% | >99% | >99.5% | >99.9% | >99.95% |
| **Minimum observation time** | 0 hrs | 72 hrs | 168 hrs (7d) | 720 hrs (30d) | 2160 hrs (90d) | 4320 hrs (180d) |
| **Trust score threshold** | 0.00 | 0.30 | 0.55 | 0.75 | 0.90 | 0.97 |
| **Override rate allowed** | N/A | N/A | N/A | <5% | <0.5% | <0.05% |
| **Safety incidents allowed** | N/A | 0 | 0 | 0 | 0 | 0 |
| **Marine advancement order** | — | Bilge → lighting | Anchor → throttle | Autopilot | Navigation → fishing | Fleet coordination |
| **COLREGs encoding** | None | Alert only | Full rules in advisory mode | Full rules enforced by AI | Full rules enforced autonomously | Full rules + self-audit |

#### 11.1.3 Marine-Specific Advancement Sequence

The INCREMENTS framework defines a specific advancement order for marine vessels that reflects increasing risk and complexity:

```
Bilge Pump (L0→L1→L2→L3→L4→L5)
    ↓ [Sensor uptime >99% for 72h]
Lighting & Domestic (L0→L1→L2→L3→L4)
    ↓ [Safe anchor release/lock for 168h]
Anchor Winch (L0→L1→L2→L3)
    ↓ [Engine safety interlocks certified]
Throttle & Engine (L0→L1→L2→L3)
    ↓ [COLREGs compliance validated in simulator + sea trials]
Autopilot / Heading Hold (L0→L1→L2→L3)
    ↓ [Route planning validated with 720h supervised operation]
Navigation & Route Planning (L0→L1→L2→L3→L4)
    ↓ [Fishing pattern AI validated with human comparison]
Fishing Operations (L0→L1→L2→L3→L4)
    ↓ [Vessel-to-vessel communication certified]
Fleet Coordination (L0→L1→L2→L3→L4→L5)
```

---

## 12. NEXUS Platform Marine Integration

### 12.1 Hardware Architecture for Marine Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│  JETSON ORIN NX (Cognitive Layer)                               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │Navigation │ │COLREGs    │ │Weather    │ │Learning   │       │
│  │Planner    │ │Engine     │ │Router     │ │Pipeline   │       │
│  │(10.0.0.1) │ │(10.0.0.2) │ │(10.0.0.3) │ │(10.0.0.4) │       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘       │
│        └──────────────┴──────────────┴──────────────┘          │
│                         │ RS-422 (921,600 bps)                  │
│                    ┌────┴────┐                                   │
│                    │ MQTT/   │                                   │
│                    │ shared  │                                   │
│                    └────┬────┘                                   │
└─────────────────────────┼───────────────────────────────────────┘
                          │ RS-422 Bus
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────┴──┐   ┌───────┴───────┐   ┌───┴──────────┐
│ ESP32 #1   │   │  ESP32 #2     │   │  ESP32 #3    │
│ (Steering) │   │  (Engine)     │   │  (Sensors)   │
│ servo:     │   │  motor_pwm:   │   │  telemetry:  │
│ rudder     │   │  throttle     │   │  wind,depth, │
│ azimuth    │   │  start/stop   │   │  temp,ais    │
│            │   │  bilge pump   │   │              │
└────────────┘   └───────────────┘   └──────────────┘
    UART 1           UART 2               UART 3
```

### 12.2 Key Cross-References

| NEXUS Component | Path | Marine Relevance |
|----------------|------|-----------------|
| Wire Protocol Specification | [[specs/protocol/wire_protocol_spec.md]] | RS-422 physical layer, COBS framing, 28 message types |
| Safety System Specification | [[specs/safety/safety_system_spec.md]] | Four-tier safety, kill switch, watchdog, heartbeat |
| Safety Policy (JSON) | [[specs/safety/safety_policy.json]] | Marine domain overrides, actuator profiles, SR-001 to SR-010 |
| Reflex Bytecode VM | [[specs/firmware/reflex_bytecode_vm_spec.md]] | 32-opcode ISA for collision avoidance reflexes |
| Learning Pipeline | [[specs/jetson/learning_pipeline_spec.md]] | 72-field observation model, pattern discovery, reflex synthesis |
| Marine PID Engineering | [[autopilot/01_marine_pid_engineering.txt]] | Vessel dynamics model, PID tuning, gain scheduling |
| Hydraulic Control | [[autopilot/03_hydraulic_control.txt]] | Solenoid valve drivers, pump control, rudder actuation |
| ESP32 Architecture | [[autopilot/02_esp32_architecture.txt]] | Firmware architecture, task scheduling, peripheral drivers |
| INCREMENTS Framework | [[INCREMENTS-autonomy-framework.md]] | L0–L5 autonomy levels, trust scores, advancement criteria |
| Marine AI Systems Brief | [[vessel-platform/14_marine_ai_systems.txt]] | Fish identification, catch tracking, edge training |
| Trust Score Algorithm | [[specs/safety/trust_score_algorithm_spec.md]] | Quantitative trust model, α_gain/α_loss ratios |

### 12.3 Safety Compliance Summary

| Standard | NEXUS Compliance Level | Key Mechanism |
|----------|:---------------------:|-------------|
| [[IEC 61508]] SIL 1 | SIL 2 equivalent (exceeds target) | Four-tier safety, ~93% SFF |
| [[IEC 60945]] Marine environmental | Partial (testing gap identified) | Marine domain safety rules in safety_policy.json |
| [[ISO 26262]] ASIL-B | ASIL-C equivalent | Defense-in-depth, fault injection testing |
| [[IMO MASS Code]] draft | Encodable (COLREGs + contingency) | JSON-encodable rules, reflex COLREGs compliance |
| [[COLREGs]] 1972 | All 72 rules encodable | Safety policy rules + reflex bytecode |
| [[MARPOL]] | Monitor-level compliance | Sensor integration, emissions logging |
| [[SOLAS]] Ch. V | Sensor suite at L3+ | Navigation equipment requirements |
| [[ABYC A-33]] (American Boat & Yacht Council) | Compliant | Marine domain overrides, kill switch specification |

---

## Glossary

| Term | Definition |
|------|-----------|
| **ASV** | Autonomous Surface Vehicle — unmanned vessel operating on the water surface |
| **AIS** | Automatic Identification System — VHF-based vessel tracking system |
| **COLREGs** | Convention on the International Regulations for Preventing Collisions at Sea |
| **CPA** | Closest Point of Approach — minimum predicted distance between two vessels |
| **CTD** | Conductivity, Temperature, Depth sensor — measures salinity, temperature, pressure |
| **DP** | Dynamic Positioning — computer-controlled system to maintain vessel position |
| **ECDIS** | Electronic Chart Display and Information System — digital navigation charts |
| **GNSS** | Global Navigation Satellite System — generic term for GPS, GLONASS, Galileo, BeiDou |
| **INS** | Inertial Navigation System — self-contained navigation using accelerometers and gyros |
| **MASS** | Maritime Autonomous Surface Ship — IMO regulatory framework for autonomous vessels |
| **MRU** | Motion Reference Unit — measures vessel roll, pitch, heave for dynamic positioning |
| **NMEA** | National Marine Electronics Association — serial communication standard for marine instruments |
| **RS-422** | EIA/TIA-422-B — differential serial communication standard, used by NMEA 0183 and NEXUS |
| **SOLAS** | Safety of Life at Sea — IMO convention on maritime safety |
| **TCPA** | Time to Closest Point of Approach — time until CPA is reached |
| **USBL** | Ultra-Short Baseline — acoustic positioning system for underwater tracking |
| **XTE** | Cross-Track Error — perpendicular distance from planned route |

---

## References

1. International Maritime Organization (IMO). *Scoping Exercise for the Development of a Code for Maritime Autonomous Surface Ships (MASS)*. MSC 100/WP.13, 2018.
2. International Maritime Organization (IMO). *Draft Code for Maritime Autonomous Surface Ships (MASS)*. MSC 106/INF.12, 2022.
3. Lloyd's Register. *Autonomous Ships: A Code of Practice*. LR Technology, 2021.
4. International Association of Marine Aids to Navigation and Lighthouse Authorities (IALA). *IALA Guideline No. 1178 on the Use of Autonomous Marine Vehicles (AMVs) within the Maritime Aids to Navigation Infrastructure*. 2020.
5. International Electrotechnical Commission. *IEC 61508: Functional Safety of Electrical/Electronic/Programmable Electronic Safety-related Systems*. 2010.
6. International Maritime Organization. *Convention on the International Regulations for Preventing Collisions at Sea (COLREGs), 1972, as amended*.
7. International Maritime Organization. *International Convention for the Safety of Life at Sea (SOLAS), 1974, as amended*. Chapter V — Safety of Navigation.
8. SAE International. *J3016: Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles*. 2021.
9. Parasuraman, R., Sheridan, T.B., & Wickens, C.D. "A model for types and levels of human interaction with automation." *IEEE Transactions on Systems, Man, and Cybernetics*, 30(3), 286–297, 2000.
10. Lee, J.D. & See, K.A. "Trust in automation: Designing for appropriate reliance." *Human Factors*, 46(1), 50–80, 2004.

---

*This document is part of the NEXUS Knowledge Base. It is maintained as a living reference and updated as marine autonomy technology and regulations evolve. For the latest version, see the NEXUS repository at `Edge-Native/knowledge-base/domains/marine_autonomous_systems.md`.*
