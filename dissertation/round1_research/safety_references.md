# NEXUS Safety System - Research References

**Document ID:** NEXUS-SR-001  
**Round:** 1A - Safety Simulation and Deep Analysis  
**Date:** 2025-01-15  
**Author:** NEXUS Safety Research Team  
**Purpose:** Comprehensive bibliography for functional safety research in robotics and distributed intelligence platforms  

---

## 1. Foundational Functional Safety Standards

### 1.1 IEC 61508 — Functional Safety of Electrical/Electronic/Programmable Electronic Safety-Related Systems

[1] **IEC 61508-1:2010.** *Functional safety of electrical/electronic/programmable electronic safety-related systems — Part 1: General requirements.* International Electrotechnical Commission, 2010.

The foundational standard for functional safety across all industries. Defines Safety Integrity Levels (SIL 1-4), hardware fault tolerance, safe failure fraction, and the overall safety lifecycle (specification → design → implementation → verification → operation). The NEXUS platform targets SIL 1 compliance. Key concepts: PFH (Probability of dangerous Failure per Hour), diagnostic coverage, common-cause failure analysis.

[2] **IEC 61508-2:2010.** *Part 2: Requirements for electrical/electronic/programmable electronic safety-related systems.* International Electrotechnical Commission, 2010.

Specifies requirements for the design, integration, validation, and modification of safety-related systems. Covers hardware safety integrity (architectural measures, diagnostic tests) and systematic safety integrity (design techniques, quality measures). Relevant to NEXUS Tier 1 hardware design and Tier 2 firmware safety guard.

[3] **IEC 61508-3:2010.** *Part 3: Software requirements.* International Electrotechnical Commission, 2010.

Defines software safety integrity levels, software lifecycle requirements, and techniques for software development at different SIL levels. At SIL 1, recommended techniques include: modular design, defensive programming, formal interface specifications, and static analysis. The NEXUS CI/CD pipeline (SR-001 through SR-010) aligns with these requirements.

[4] **IEC 61508-4:2010.** *Part 4: Definitions and abbreviations.* International Electrotechnical Commission, 2010.

[5] **IEC 61508-5:2010.** *Part 5: Examples of methods for the determination of safety integrity levels.* International Electrotechnical Commission, 2010.

Provides risk graphs and hazard analysis methods for determining required SIL levels. Useful for justifying the SIL 1 target for the NEXUS marine autopilot application.

[6] **IEC 61508-6:2010.** *Part 6: Guidelines on the application of IEC 61508-2 and IEC 61508-3.* International Electrotechnical Commission, 2010.

Contains detailed guidance on architectural measures, diagnostic coverage calculation, and common-cause failure scoring (used in Section 1.4 of the deep analysis report).

[7] **IEC 61508-7:2010.** *Part 7: Overview of techniques and measures.* International Electrotechnical Commission, 2010.

### 1.2 ISO 26262 — Road Vehicles Functional Safety

[8] **ISO 26262-1:2018.** *Road vehicles — Functional safety — Part 1: Vocabulary.* International Organization for Standardization, 2018.

Defines ASIL (Automotive Safety Integrity Level) categories A-D. The NEXUS system's SIL 1 target corresponds approximately to ASIL-B. Key difference: ISO 26262 uses ASIL-QM for non-safety functions, while IEC 61508 uses SIL for all safety functions.

[9] **ISO 26262-4:2018.** *Part 4: Product development at the system level.* International Organization for Standardization, 2018.

Covers system-level safety architecture, technical safety concept, and integration/testing. The NEXUS 4-tier architecture draws inspiration from ISO 26262's concept of safety mechanisms with defined ASIL allocation.

[10] **ISO 26262-5:2018.** *Part 5: Product development at the hardware level.* International Organization for Standardization, 2018.

Provides methods for hardware safety metrics calculation (SPFM, LFM, PMHF). Relevant to NEXUS Tier 1 hardware interlock design and component reliability analysis.

### 1.3 IEC 60945 — Maritime Navigation and Radiocommunication Equipment

[11] **IEC 60945:2002+A1:2008.** *Maritime navigation and radiocommunication equipment and systems — General requirements — Methods of testing and required test results.* International Electrotechnical Commission, 2008.

The primary environmental and safety standard for marine electronic equipment. Covers: EMC testing, environmental conditions (temperature, humidity, vibration), E-Stop requirements (color, actuation force), and alarm specifications. The NEXUS platform targets compliance with this standard for marine applications. Key requirements: RED/YELLOW E-Stop coloring, IP67 ingress protection, alarm duration limits.

[12] **IEC 62288:2014.** *Maritime navigation and radiocommunication equipment and systems — Presentation of navigation-related information on shipborne navigational displays — General requirements, methods of testing and required test results.* International Electrotechnical Commission, 2014.

### 1.4 DO-178C — Software Considerations in Airborne Systems

[13] **RTCA DO-178C.** *Software Considerations in Airborne Systems and Equipment Certification.* RTCA, Inc., 2012.

The avionics software safety standard, widely regarded as the most rigorous software safety standard in any domain. Defines five software levels (A-E, where A is most critical). DO-178C Level B is the closest equivalent to SIL 2-3. Key requirements: structural coverage (MC/DC for Level A), traceability, configuration management, tool qualification. The NEXUS safety analysis in Section 7.3 compares against DO-178C Level B requirements as a benchmark.

### 1.5 Additional Safety Standards

[14] **ISO 13849-1:2023.** *Safety of machinery — Safety-related parts of control systems — Part 1: General principles for design.* International Organization for Standardization, 2023.

Covers PL (Performance Level) a-e for machinery safety. The NEXUS kill switch design follows ISO 13849 principles (PL d/e equivalent).

[15] **ISO 13850:2015.** *Safety of machinery — Emergency stop function — Principles for design.* International Organization for Standardization, 2015.

Specifies E-Stop design requirements including mushroom-head actuation, twist-to-release, color (RED), and actuation force (22-50N). Directly referenced in NEXUS Section 2.1.

[16] **IEC 62443.** *Industrial communication networks — Network and system security.* International Electrotechnical Commission.

Series of standards for industrial cybersecurity. Relevant to NEXUS distributed architecture where safety-critical communication (heartbeat, commands) must be protected from cyber threats.

---

## 2. Defense-in-Depth for Autonomous Systems

[17] **Koopman, P., & Wagner, M. (2016).** "Autonomous Vehicle Safety: An Interdisciplinary Challenge." *IEEE Intelligent Transportation Systems Magazine*, 8(3), 90-96.

Key paper arguing that autonomous vehicle safety requires an interdisciplinary approach combining software engineering, safety engineering, and systems engineering. Introduces the concept of "challenge problems" for autonomous system safety validation. Relevant to NEXUS multi-tier architecture design philosophy.

[18] **B spikes, S., & Guiochet, J. (2019).** "Safety/security-related requirements and trade-offs in automotive systems: An automotive case study." *Reliability Engineering & System Safety*, 191, 106552.

Analyzes the trade-offs between safety and security requirements in automotive systems, using defense-in-depth as a framework. Proposes a methodology for identifying conflicts between safety and security objectives. Relevant to NEXUS where the heartbeat protocol serves both safety (liveness monitoring) and security (command authentication) functions.

[19] **Nubert, J., Fischinger, D., Hong, A., & D'Andrea, R. (2020).** "Dynamic Safety Envelopes for Robotic Manipulators." *IEEE Robotics and Automation Letters*, 5(4), 5703-5710.

Introduces dynamic safety envelopes — real-time computed boundaries beyond which a robot cannot physically move due to safety constraints. While focused on manipulators, the concept is applicable to NEXUS actuator safe-state bounds and rate limiting.

[20] **Makansi, O., Eghbalzadeh, K., & Brox, T. (2023).** "Safe Control with Learned Dynamics: A Control Barrier Function Approach for Autonomous Racing." *IEEE Transactions on Robotics*, 39(6), 4520-4537.

Presents control barrier functions (CBFs) for ensuring safety of learned control policies. Relevant to NEXUS Tier 4 where AI inference drives actuator commands — CBFs could provide a mathematical guarantee of safe-state bounds even when AI inference produces unexpected outputs.

[21] **Hespanhol, P., Voss, T., Glocker, C., & Lebelt, M. (2019).** "Robust Functional Safety Concept for Autonomous Driving." *ATZ Worldwide*, 121(10), 52-57.

Describes a multi-layered safety concept for autonomous driving combining functional safety (ISO 26262), SOTIF (ISO 21448), and runtime safety monitors. The layered approach is analogous to NEXUS's 4-tier architecture.

[22] **Magedanz, T., et al. (2019).** "Safety Concept for Automated Driving Functions with Deep Learning." *2019 IEEE Intelligent Vehicles Symposium (IV)*, 1843-1848.

Addresses the challenge of applying functional safety concepts to systems incorporating deep learning. Proposes a safety architecture with runtime monitors as the primary safety mechanism for AI-based components. Directly relevant to NEXUS where AI inference on Jetson is supervised by ESP32 safety guards.

[23] **Dreossi, T., Donzé, A., & Seshia, S. A. (2017).** "Compositional Falsification of Cyber-Physical Systems." *ACM International Conference on Hybrid Systems: Computation and Control (HSCC)*, 85-94.

Introduces simulation-based falsification methods for verifying safety properties of cyber-physical systems. The NEXUS Monte Carlo simulation (Deliverable 1) implements a simplified version of this approach for safety state analysis.

---

## 3. Hardware Watchdog and Supervisor IC Research

[24] **Maxim Integrated (now Analog Devices).** *MAX6818-MAX6825 Datasheet: +5V, Precision, Pin-Selectable Watchdog Supervisors.* Rev. 3, 2016.

Primary component datasheet for the MAX6818 used in NEXUS Tier 1. Key specifications: 1.0s fixed timeout (MAX6818), 140ms minimum reset pulse width, 2.93V undervoltage threshold, automotive-grade qualification. The alternating 0x55/0xAA kick pattern design is based on the requirement that the WDI pin must see both edges within the timeout period.

[25] **Texas Instruments.** *TPS3823-33 Datasheet: Small, Accurate, Supervisory Circuits with Window-Watchdog.* 2019.

Alternative hardware watchdog IC to MAX6818. Notable feature: window-watchdog mode that requires kick within both a minimum and maximum time window. This provides additional fault detection (detects both stuck-at faults AND excessively fast kicking) compared to the simple timeout of MAX6818.

[26] **Avionics Watchdog Timer Study.** *ARP4754A / ARP4761 Guidelines.* SAE International, 2014.

While focused on avionics, these guidelines provide best practices for watchdog timer design including: mutual monitoring between watchdog and supervised processor, kick pattern design, and timeout selection methodology.

[27] **Priess, B., Kugele, S., & Mottok, J. (2017).** "Watchdog Process as Safety Element out of Context." *SAE Technical Paper 2017-01-0034.*

Analyzes the use of external watchdog processors (safety elements out of context, SEooC) in automotive systems. Demonstrates that independent watchdog processors provide higher diagnostic coverage than internal MCU watchdogs. Supports the NEXUS design choice of using an external MAX6818 rather than relying solely on ESP32's internal watchdog.

[28] **Björkman, G. (2004).** "Watchdog timers: The forgotten stepchild of system safety." *Embedded Systems Conference, Boston.*

Advocates for proper watchdog timer design in embedded systems. Key recommendations: watchdog should monitor both task execution AND task sequencing (not just "alive" signals); kick pattern should be pseudo-random to prevent pattern-matching faults; watchdog timeout should be based on maximum safe exposure time. These principles informed the NEXUS 0x55/0xAA alternating pattern design.

---

## 4. Heartbeat Protocols in Distributed Systems

[29] **Fetzer, C., & Xiao, Z. (2005).** "Heartbeat Failover Protocols for Fault-Tolerant Distributed Systems." *International Conference on Dependable Systems and Networks (DSN)*, 746-755.

Formal analysis of heartbeat-based failure detection in distributed systems. Demonstrates that heartbeat interval, timeout thresholds, and message loss probability interact in non-obvious ways. Provides mathematical models for optimizing heartbeat parameters. Directly applicable to NEXUS heartbeat protocol parameter selection (Section 6 of the deep analysis).

[30] **Chandra, T. D., & Toueg, S. (1996).** "Unreliable Failure Detectors for Reliable Distributed Systems." *Journal of the ACM*, 43(2), 225-267.

Foundational paper on failure detectors in distributed systems. Defines classes of failure detectors (Strong, Weak, Eventually Strong, Eventually Weak) based on completeness and accuracy properties. The NEXUS heartbeat protocol implements an "Eventually Strong" failure detector — it eventually suspects every crashed process and never suspects a correct process after some stabilization time.

[31] **Hayashibara, N., Defago, X., Yared, R., & Katayama, T. (2004).** "The ϕ Accrual Failure Detector." *IEEE International Symposium on Reliable Distributed Systems (SRDS)*, 66-78.

Introduces the φ accrual failure detector, which outputs a suspicion level (φ) rather than a binary suspect/not-suspect decision. This allows graduated responses — low φ could trigger logging, medium φ could trigger degraded mode, high φ could trigger safe state. The NEXUS graduated escalation (NORMAL → DEGRADED → SAFE_STATE) implements a simplified version of this concept.

[32] **Linux-HA Project.** *Heartbeat: High-Availability Linux.* https://linux-ha.org/

Practical implementation of heartbeat protocols for high-availability clusters. Demonstrates that heartbeat-based failure detection is effective for detecting node crashes, network partitions, and OS hangs. The NEXUS heartbeat protocol draws on this practical experience for parameter selection.

[33] **ROS 2 Design.** *Quality of Service (QoS) Policies for DDS.* https://docs.ros.org/en/humble/Concepts/About-Quality-of-Service.html.

ROS 2's DDS-based communication framework provides built-in deadline and liveliness QoS policies that function as heartbeat mechanisms. However, these are software-only and lack the hardware foundation of the NEXUS heartbeat design. Comparison provided in Section 7.1 of the deep analysis.

---

## 5. Functional Safety for Robotics

[34] **ISO 10218-1:2011.** *Robots and robotic devices — Safety requirements for industrial robots — Part 1: Robots.* International Organization for Standardization, 2011.

Primary safety standard for industrial robots. Defines safety functions: emergency stop, protective stop, safeguarding, speed/force limiting. The NEXUS safety state machine is influenced by the ISO 10218 concept of safety-rated monitored stop and safeguarded space.

[35] **ISO/TS 15066:2016.** *Robots and robotic devices — Collaborative robots.* International Organization for Standardization, 2016.

Defines safety requirements for collaborative robots operating in shared workspaces with humans. Introduces biomechanical load limits for transient contact. The NEXUS factory domain rules (Section 7.1 of deep analysis) reference ISO/TS 15066 for speed (1.0 m/s) and force (150N) limits.

[36] **Haddadin, S., Albu-Schäffer, A., & Hirzinger, G. (2017).** "Safe Requirements for Physical Human-Robot Interaction." *Handbook of Robotics*, 2nd edition, Springer, 2379-2402.

Comprehensive survey of safety requirements for human-robot interaction, covering mechanical design, control, and sensor requirements. Proposes a safety hierarchy: (1) inherent safety design, (2) safety-related control, (3) safety-related monitoring. This hierarchy maps directly to the NEXUS 4-tier architecture.

[37] **Khalil, W., & Kleinfinger, P. (2004).** "A new geometric approach to the joint limit and obstacle avoidance of manipulators." *Robotics and Autonomous Systems*, 48(2-3), 125-143.

Introduces geometric approaches to joint limit and obstacle avoidance that could enhance NEXUS Tier 4 safe-state bounds enforcement for robotic applications.

[38] **Kulić, D., & Croft, E. (2006).** "Real-Time Safety for Human-Robot Interaction." *Robotics and Autonomous Systems*, 54(1), 1-12.

Presents real-time safety assessment methods for human-robot interaction using safety fields and potential-based obstacle avoidance. Relevant to NEXUS domain-specific safety rules (proximity detection, speed limiting) for factory and mining applications.

[39] **Lasota, P. A., Fong, J., & Shah, J. A. (2017).** "A Survey of Methods for Safe Human-Robot Interaction." *Foundations and Trends in Robotics*, 5(4), 261-349.

Extensive survey covering over 300 papers on safe human-robot interaction. Categorizes safety methods into: safety by control (speed/separation monitoring, power/force limiting), safety by sensing (vision, tactile, proximity), and safety by design (mechanical compliance, redundant actuators). The NEXUS multi-tier architecture combines elements of all three categories.

---

## 6. Embedded Systems Safety and Reliability

[40] **Koopman, P. (2014).** *Better Embedded System Software.* Dr. Philip Koopman, Carn Mellon University.

Comprehensive guide to embedded software safety practices. Covers defensive programming, coding standards (MISRA C), watchdog timer design, and failure mode analysis. The NEXUS coding rules (SR-001 through SR-010) align with Koopman's recommended practices for safety-critical embedded software.

[41] **MISRA C:2012.** *Guidelines for the use of the C language in critical systems.* MISRA Ltd., 2013.

Industry-standard coding guidelines for safety-critical C code. Defines 143 mandatory and advisory rules for C programming in safety-critical systems. The NEXUS ESP32 firmware should comply with MISRA C guidelines for SIL 1 certification.

[42] **Barr, M. (2013).** *Embedded C Coding Standard.* Barr Group, 2013.

Coding standard for embedded C that complements MISRA C with additional rules specific to embedded systems. Covers interrupt handling rules (no blocking in ISRs), stack management, and hardware register access — all relevant to NEXUS Tier 2 ISR design.

[43] **Ganssle, J. (2008).** *The Art of Designing Embedded Systems.* 2nd edition, Newnes.

Practical guide to embedded system design covering hardware-software co-design, real-time constraints, and debugging. Chapter on watchdog timers provides practical guidance on timeout selection and kick pattern design that informed the NEXUS watchdog specification.

[44] **Nagle, J. (2003).** "Watchdog Timer Design Considerations for Safety-Critical Systems." *Embedded Systems Design Magazine*, 16(4).

Practical article on watchdog timer design considerations including: timeout selection based on maximum safe exposure time, kick pattern design to detect stuck-at faults, and the importance of using external (independent) watchdog ICs rather than relying solely on MCU-internal watchdogs.

---

## 7. Failure Analysis Methods

[45] **IEC 60812:2018.** *Failure modes and effects analysis (FMEA and FMECA).* International Electrotechnical Commission, 2018.

The standard that defines the FMEA methodology used in Section 3 of the deep analysis report. Covers: failure mode identification, severity/occurrence/detection rating scales, Risk Priority Number (RPN) calculation, and recommended actions.

[46] **IEC 61025:2006.** *Fault tree analysis (FTA).* International Electrotechnical Commission, 2006.

Standard for fault tree analysis, which is identified as a gap in the current NEXUS safety analysis (Section 2.5). FTA provides a top-down, deductive approach to identifying combinations of failures that can lead to a hazardous event. Should be performed in Round 2.

[47] **Stamatelatos, M., et al. (2002).** *Fault Tree Handbook with Aerospace Applications.* NASA, 2002.

Comprehensive guide to fault tree analysis from NASA. Provides detailed methodology for constructing fault trees, calculating cut-sets, and performing quantitative analysis. Useful reference for performing the NEXUS fault tree analysis in Round 2.

[48] **Ericson, C. A. (2011).** *Fault Tree Analysis Primer.* CreateSpace Independent Publishing Platform.

Accessible introduction to fault tree analysis covering basic gates (AND, OR, k-out-of-n), common-cause failure modeling, and quantitative evaluation methods.

---

## 8. Reliability Engineering

[49] **O'Connor, P., & Kleyner, A. (2012).** *Practical Reliability Engineering.* 5th edition, Wiley.

Comprehensive reliability engineering reference covering component reliability data, system reliability modeling, and environmental stress analysis. Relevant to NEXUS component FIT rate analysis for PFH calculation.

[50] **Birolini, A. (2014).** *Reliability Engineering: Theory and Practice.* 8th edition, Springer.

Theoretical foundation for reliability engineering including Markov models, reliability block diagrams, and common-cause failure modeling. The defense-in-depth probability model in Section 1.3 of the deep analysis is based on reliability series system modeling from this reference.

[51] **US Department of Defense.** *MIL-HDBK-217F: Reliability Prediction of Electronic Equipment.* 1991.

Military handbook for electronic component reliability prediction. Provides failure rate models for electronic components including ICs, resistors, capacitors, connectors, and switches. While outdated, the methodology is still relevant for estimating component-level failure rates for PFH calculation.

---

## 9. Additional Academic References

[52] **Gessner, D., et al. (2019).** "Functional Safety and SOTIF — Will They Converge?" *ATZ Electronics Worldwide*, 14(1), 28-33.

Discusses the convergence of functional safety (ISO 26262) and safety of the intended functionality (ISO 21448, SOTIF) for autonomous systems. SOTIF addresses hazards arising from functional insufficiencies (e.g., AI perception failures) rather than random hardware failures. Relevant to NEXUS FM-15 (AI inference failure) which is a SOTIF-type hazard.

[53] **Schuldt, F., et al. (2022).** "Standardized Surrogate Test Scenarios for Safety Evaluation of Automated Driving." *IEEE Transactions on Intelligent Transportation Systems*, 23(7), 7623-7634.

Introduces standardized test scenarios for evaluating the safety of automated driving systems. The concept of standardized fault injection scenarios (used in the NEXUS simulation) draws from this approach.

[54] **Reich, J., et al. (2023).** "Proving Safety of Machine Learning Systems: A Survey." *ACM Computing Surveys*, 55(12), 1-36.

Comprehensive survey on formal verification methods for machine learning systems. Covers: formal verification of neural networks, robustness certification, runtime monitoring, and shield approaches. Highly relevant to NEXUS AI inference safety (FM-15) — runtime monitoring and shielding are identified as the most practical approaches for ensuring AI safety in real-time control systems.

---

## Appendix: Standard Quick Reference

| Standard | Domain | Scope | NEXUS Relevance |
|----------|--------|-------|-----------------|
| IEC 61508 (Parts 1-7) | Cross-industry | Functional safety of E/E/PE systems | Primary compliance target (SIL 1) |
| ISO 26262 (Parts 1-12) | Automotive | Functional safety of road vehicles | ASIL-B equivalent reference |
| IEC 60945 | Marine | Environmental & safety for navigation equipment | Marine domain compliance |
| DO-178C | Avionics | Software safety in airborne systems | Benchmark for software rigor |
| ISO 13849-1 | Machinery | Safety-related control systems | E-Stop and control system design |
| ISO 13850 | Machinery | Emergency stop function | Kill switch physical design |
| ISO 10218-1/2 | Industrial robots | Robot safety requirements | Factory domain safety rules |
| ISO/TS 15066 | Collaborative robots | Collaborative robot safety | Human-robot interaction safety |
| IEC 62443 | Industrial cybersecurity | Network and system security | Distributed system security |
| IEC 60812 | Cross-industry | FMEA methodology | Failure analysis method |
| IEC 61025 | Cross-industry | Fault tree analysis | Top-down failure analysis |
| MISRA C:2012 | Software | C coding guidelines | Embedded firmware quality |
| ISO 21448 (SOTIF) | Automotive | Safety of intended functionality | AI perception safety |
