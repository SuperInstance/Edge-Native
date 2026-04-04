# NEXUS Platform — Engineering Addenda Master Index

**Version:** 1.0.0 | **Date:** 2026-03-30 | **For:** NEXUS Platform Engineering Team

---

## Purpose

This document set supplements the NEXUS Platform Final Synthesis Report with practical, engineer-to-engineer guidance distilled from deep analysis of the full 19,200-line specification suite. These addenda address the "how" and "what to watch out for" that the architecture documents don't cover. Read the synthesis for WHAT to build; read these addenda for HOW to build it without shooting yourself in the foot.

## How to Use These Documents

**Before writing any code:** Read ALL addenda cover-to-cover. Total reading time: ~2 hours. This is the highest-ROI 2 hours you'll spend on this project.

**During development:** Consult specific addenda as you encounter each subsystem:

- Implementing COBS? → Addendum 01, Section 1
- Writing the VM? → Addendum 01, Section 2; Addendum 02, Section 2
- Wiring the kill switch? → Addendum 01, Section 4; Addendum 03, Gate 2; Addendum 04, Section 1
- Writing ISR code? → Addendum 04, Test 2.2; Addendum 06, Section 1 (ISR Safety)
- Reviewing a PR? → Addendum 06 (full checklist)
- Doing integration testing? → Addendum 05 (full test plan)

**Before every release:** Run the Safety Validation Playbook (Addendum 04) and Integration Test Plan (Addendum 05).

## Document Index

| # | Document | Focus | When to Read | Key Questions Answered |
|---|----------|-------|-------------|----------------------|
| 00 | Master Addendum Index (this document) | Navigation | First | Where is everything? What applies to my current task? |
| 01 | Engineering Pitfalls and Gotchas | Implementation traps | Before coding | What will bite me? What are the subtle bugs waiting to happen? |
| 02 | Performance Budgets and Optimization | Timing, memory, bandwidth | During design | Will it fit in SRAM? Can we make the 1ms tick deadline? |
| 03 | Hardware Bring-Up Checklist | First power-on procedures | Board assembly | How do I verify the hardware works before loading NEXUS firmware? |
| 04 | Safety Validation Playbook | Safety test procedures | Pre-ship | How do I prove the system is safe? What measurements do I need? |
| 05 | Integration Test Plan | Cross-component tests | During integration | How do I verify subsystems work together? |
| 06 | Code Review Checklist | PR review criteria | Every PR | What must I check before approving this code? |

## Relationship to Main Specification

```
NEXUS_Platform_Final_Synthesis.md  ←  WHAT to build (architecture, decisions, vision)
         |
         v
nexus_specs/ (21 files)            ←  DETAILED WHAT (message formats, opcodes, schemas)
         |
         v
addenda/ (this set)                ←  HOW to build it safely and correctly
```

The main synthesis tells you the system has a COBS-framed serial protocol. The wire_protocol_spec.md tells you the exact byte format. These addenda tell you that the #1 COBS bug is forgetting to strip the trailing sentinel byte, and that you need a 50ms settling delay after baud rate negotiation because the spec doesn't mention it.

## Key Numbers Quick Reference

| Constraint | Value | Source |
|-----------|-------|--------|
| ESP32 SRAM | 512 KB (PSRAM 8 MB) | Synthesis §4.1 |
| VM tick budget at 1kHz | 1 ms (340–960µs typical) | Addendum 02 §2 |
| E-Stop ISR response | <1 ms (<100µs target) | Safety Spec §2.4 |
| Kill switch to safe-state | <1 ms (hardware, not software) | Safety Spec §1.2 |
| Heartbeat interval | 100 ms (safety spec overrides wire spec) | Safety Spec §4.1 |
| Serial link utilization | <80% sustained | Addendum 02 §3 |
| PSRAM observation buffer | 8 MB ≈ ~4.6 min at 100Hz full rate | Addendum 02 §6 |
| Jetson VRAM (all models loaded) | ~7.5 GB of 8 GB (tight!) | Addendum 02 §4 |
| Trust Level 3 from zero | ~120 days flawless operation | Synthesis §11.3 |
| Full build (3 devs, parallel) | 12–16 weeks | Synthesis §17.2 |
| LED demo (fastest path) | 8 weeks | Synthesis §17.3 |

## Contact and Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-30 | Initial release covering all 6 subsystems |
