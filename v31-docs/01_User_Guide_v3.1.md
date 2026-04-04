# NEXUS Platform v3.1 — User Guide

**Version:** 3.1.0  
**Last Updated:** 2026-03-29  
**Classification:** User Documentation — For Operators  
**Platform Maturity:** 2+ Years of Operational Deployment  

---

## 1. Welcome to NEXUS

### What NEXUS Does (In Plain Language)

NEXUS is a robotics control system that learns from you. You do not write code. You do not configure software. You wire your hardware (sensors, motors, pumps, switches), tell NEXUS what each wire does in plain English, and then show the system how you want things to behave by doing it yourself while narrating your actions. The system watches, records what happens, finds patterns in your behavior, and proposes automated behaviors called *reflexes*. You review each proposal, approve or reject it, and the system gradually takes on more responsibility — but only as fast as you are comfortable.

Think of NEXUS as an apprentice: it starts by watching, then suggesting, then acting under supervision, and eventually handling routine tasks on its own. But unlike a human apprentice, NEXUS never forgets, never gets tired, and can react in under a millisecond when safety demands it.

### What Changed in v3.0 and v3.1

These releases reflect two full years of hard-won lessons from operational deployments across fishing vessels, agricultural equipment, HVAC systems, and factory automation.

**v3.0 — The Maturity Release (6 months ago):**

- **Adaptive trust parameters.** In v1.0, the trust score parameters were too aggressive. Users were frustrated that the system never seemed to learn — a single wrong suggestion would crater weeks of accumulated trust. v3.0 introduced per-subsystem trust tuning: safety-critical subsystems (steering, throttle) retain the conservative 25:1 loss-to-gain ratio, while low-risk subsystems (lighting, bilge monitoring) use a gentler 8:1 ratio. The result: bilge pumps advance to autonomous operation in weeks instead of months.
- **Proposal explainability.** In early deployments, operators rejected reflex proposals not because they were wrong, but because they could not understand them. v3.0 rewrote the proposal engine to explain every reflex in plain language. Example: "When water level rises above 65% for more than 30 seconds, start the bilge pump and alert the operator. Reason: In 47 observations, you always started the pump within 45 seconds of this condition."
- **Simplified provisioning wizard.** The v1.0 boot sequence required operators to manually identify nodes, assign addresses, and configure I/O pins through a command-line interface. v3.0 added automatic hardware detection and a conversational setup wizard. First boot now takes 3 minutes instead of 30.

**v3.1 — The Reliability Release (current):**

- **Hot-swap node replacement.** In v2.x, if an ESP32 limb node failed, the operator needed a laptop to reflash firmware and reassign the role. v3.1 supports true plug-and-play: any fresh ESP32-S3 unit is auto-detected, receives its role from the Jetson brain, and resumes operation in under 60 seconds. No laptop needed. No buttons to press.
- **Graceful degradation recovery.** In v2.0, a temporary Jetson reboot (which happens during power fluctuations) would drop all subsystems to Level 0, requiring operators to re-approve every reflex manually. v3.1 remembers the pre-failure autonomy state and offers a one-command restoration: "Resume previous operating state." Reflexes that were active before the failure are re-activated automatically after a 30-second validation window.
- **Delta-encoded observation sync.** In v2.x, uploading observation data to the cloud consumed excessive bandwidth (up to 32 MB/minute at 100 Hz sampling). v3.1 introduced delta encoding, reducing bandwidth by 5-8x. This makes cloud sync viable over satellite links (Starlink) and cellular connections.
- **Reject and explain feature.** v2.5 introduced the ability to reject a proposal with a voice or text explanation. v3.1 improved the learning from these rejections: the system now asks follow-up questions when it does not understand your reason, and adjusts its proposal generation strategy based on accumulated rejection patterns. After 6 months of deployment data, rejection-driven learning accounts for 34% of all successful reflex improvements.

### Who This Guide Is For

This guide is for **operators** — the people who use NEXUS day to day. You might be a fishing boat captain, a farm manager, a building engineer, or a factory supervisor. You are not expected to know anything about programming, electronics, or artificial intelligence. If you can wire a sensor, operate your equipment, and describe what you want in plain English, you can use NEXUS.

---

## 2. Your First Day

### Unboxing and Physical Setup

Inside the NEXUS deployment kit you will find:

1. **One Jetson Orin Nano Super unit** (the "brain") — a small fan-cooled computer board in an aluminum enclosure.
2. **One to eight ESP32-S3 nodes** (the "limbs") — small circuit boards with labeled connectors.
3. **One power supply** (12V, 10A minimum for a typical 3-node setup).
4. **One kill switch** (red mushroom-head button) — mandatory for safety. The system will not start without it.
5. **RJ-45 cables** for connecting limbs to the brain.
6. **A laminated Quick Start card** (also documented in the Quick Start Guide).

**Installation:** Mount the Jetson brain unit using the four included screws. Connect each ESP32 limb node to the Jetson via the labeled RJ-45 ports. Connect the 12V power supply to the main power input on the Jetson (which distributes power to all limb nodes through the data cables). Connect the kill switch to the dedicated kill switch port — the system checks for this connection at boot and refuses to proceed without it.

That is all the physical setup required. No laptop. No configuration files. No software installation.

### Powering On for the First Time

Press the power button on the Jetson enclosure. You will see the following LED sequence on the Jetson and on each limb node:

1. **All nodes: Rapid amber blink** (2 Hz) — firmware loading.
2. **Jetson: Solid amber** — booting cognitive services.
3. **Each limb node: Green blink, 1 Hz** — waiting for role assignment.
4. **All nodes: Solid green** — operational.

This sequence typically takes 45-60 seconds on first boot. On subsequent boots, it takes about 20 seconds because cached configurations are loaded from flash memory.

### The Provisioning Wizard

Once the Jetson boots, it activates its speaker and announces:

> "NEXUS online. Three nodes detected. Awaiting commands."

The system then enters the provisioning wizard. You talk to it using the built-in microphone, or type on the connected display. The wizard asks:

1. **"What are you controlling?"** — You describe your equipment. Example: "I have a 42-foot fishing vessel with a hydraulic rudder, electronic throttle, bilge pump, and navigation lights."
2. **"What is connected to each node?"** — You describe the wiring. Example: "Node 1 has the rudder angle sensor and rudder hydraulic valve. Node 2 has the throttle position sensor and engine RPM sensor. Node 3 has the bilge float switch and pump relay."
3. **"Are there any safety limits?"** — You set boundaries. Example: "The rudder can move from minus 35 to plus 35 degrees. The throttle should never exceed 85% of maximum."
4. **"What is the kill switch connected to?"** — The system auto-detects this, but you confirm.

The wizard auto-detects all connected sensors and actuators by scanning the I2C bus, ADC channels, and GPIO states on each node. It proposes a configuration and asks you to approve. You can say "add a wind sensor on node 1's I2C bus" or "remove the anchor winch from node 3" at any time.

### Speaking Your First Command

Once provisioning is complete, try a simple command:

> "Show me the current sensor readings for all nodes."

The system will read back the current values: water temperature, engine RPM, bilge water level, battery voltage, and any other sensors you connected. This confirms that data is flowing correctly from limbs to brain.

### Understanding the LED Indicators

Each limb node has a single tri-color LED visible on its enclosure. Here is what each pattern means:

| Pattern | Meaning | What You Should Do |
|---------|---------|-------------------|
| **Solid green** | Normal operation | Nothing. Everything is fine. |
| **Amber, 1 Hz blink** | Degraded | Check the dashboard for details. A sensor may be intermittent, or a reflex may have paused. The system is still operating safely. |
| **Solid red** | Safe-state | All actuators on this node are stopped. This happens after a kill switch press, a heartbeat timeout, or a safety event. See Section 7. |
| **Green + amber alternating** | Learning | The system is recording an observation session or processing patterns. Normal during training. |
| **Rapid red blink** | Fault | Something is wrong. Check the dashboard immediately. A hardware failure, communication error, or watchdog timeout has occurred. |
| **Off** | No power or boot failure | Check power connection and cable. If the node has power but no LED, the firmware may be corrupted — contact support. |

---

## 3. Daily Operations

### Morning Startup Procedure (3 minutes)

Follow this checklist every day before beginning operations. It was developed after deployments showed that operators who skipped morning checks experienced 4.7x more safety events per operating hour.

1. **Visual inspection.** Walk past all limb nodes and confirm solid green LEDs. If any node shows amber or red, resolve it before proceeding.
2. **Kill switch check.** Press and release the kill switch. Verify all nodes briefly flash red, then return to green after you twist to reset. This confirms the kill switch circuit is functional.
3. **Dashboard check.** Open the NEXUS dashboard (on the embedded display or your tablet). Confirm:
   - All nodes online (green status indicators).
   - Trust scores stable or rising (not declining).
   - No active alerts.
   - Autonomy levels at their expected values.
4. **Voice check.** Say "System status." The system should respond with a summary: "All systems normal. Three nodes online. Steering at Level 3, throttle at Level 2, bilge at Level 4."
5. **Begin operations.** The system is ready.

### Monitoring the Dashboard

The dashboard has four main areas:

- **Node Health Panel** (top left) — Shows each limb node's status, uptime, and CPU/memory usage. Green = healthy. Amber = degraded (check details). Red = fault.
- **Autonomy Map** (center) — Shows each subsystem's current autonomy level, trust score, and advancement progress. See Section 4 for details.
- **Sensor Readings** (right) — Live values from all connected sensors. Click any sensor to see its 24-hour trend graph.
- **Activity Log** (bottom) — Scrolling list of recent events: reflex activations, override events, trust score changes, safety events. Click any entry for details.

**Key metrics explained:**

- **Trust Score (0.0 to 1.0):** How much the system has earned your trust for a specific subsystem. A score of 0.87 means the system has demonstrated reliable behavior 87% of the way toward the next autonomy level threshold. Trust rises slowly with good performance and drops quickly with mistakes.
- **Override Rate (overrides per hour):** How often you are overriding the system's actions. A rate above 0.5 per hour on any subsystem means the system is not performing well enough for its current autonomy level and may be automatically reduced.
- **Reflex Uptime:** How long the current set of reflexes has been running without interruption. Long uptime indicates stability.
- **Observation Buffer Usage:** How full the local data recording buffer is. If it reaches 90%, the system will stop recording and alert you. This is rare with v3.1 delta encoding.

### The Chat Interface: How to Talk to Your System

NEXUS responds to natural language through voice or text. Here are the four main interaction types:

#### Intent Description

Tell the system what you want it to achieve, and it will work on a solution.

> "When the wind exceeds 25 knots, reduce throttle to 40% and angle the trim tabs down 5 degrees."

The system records this as an intent, adds it to its learning queue, and begins observing your behavior in high-wind conditions. After it collects enough data, it will propose a reflex that implements your intent automatically.

#### Behavior Demonstration

Show the system how to handle a situation while narrating your reasoning.

> "I'm throttling up before turning into the wind because I need more water flow over the rudder for steering authority. When the heading error is more than 5 degrees, I apply more rudder quickly. When it's less than 2 degrees, I ease off gradually."

The system records all sensor data during your demonstration along with your narration. It analyzes the correlation between sensor readings and your control inputs, then proposes a reflex that reproduces your behavior.

#### Proposal Review

When the system has enough data to propose a reflex, it presents it for your review:

> "Proposal: Wind Compensation Reflex (v1). When wind speed exceeds 20 knots and heading error is greater than 3 degrees, increase rudder authority by 15% and reduce throttle by 10%. Based on 23 observations of your behavior in similar conditions. Consistency: 87%. Estimated fuel savings: 8%. [APPROVE] [REJECT] [TEST] [MORE DETAILS]"

You can ask for more details, run a supervised test (A/B test), approve, or reject. If you reject, the system asks why — your explanation is valuable training data.

#### Override Commands

In an emergency or when the system is not performing correctly:

- **"Emergency: all stop"** — Immediately enters safe-state on all subsystems. Equivalent to pressing the kill switch, but software-triggered.
- **"Take over steering"** — Switches steering from system control to manual control. The system continues monitoring and will offer suggestions.
- **"Pause all reflexes"** — Suspends all automated behaviors without entering safe-state. Actuators hold their current positions.
- **"Resume autonomous operation"** — Restores all subsystems to their pre-pause autonomy levels.

### End-of-Day Shutdown Procedure

1. Bring all subsystems to their resting states (anchor deployed, engines off, etc.).
2. Say "End of day shutdown" or press the shutdown button on the dashboard.
3. The system saves all observation data, syncs to cloud (if connected), and displays a summary:
   > "Shutdown complete. Operating time: 7 hours 23 minutes. Observations recorded: 2.6 million data points. Trust scores: steering +0.02, throttle +0.01, bilge stable at 0.94. Zero safety events."
4. Press and hold the power button for 3 seconds to power off.

Do not simply cut power. The system needs 10-15 seconds to flush data to flash. Abrupt power loss can corrupt the observation buffer — this was the cause of 12% of data loss incidents in v2.x deployments. v3.1 added a capacitor-backed write flush that mitigates most of these, but a clean shutdown is still recommended.

---

## 4. Understanding Trust and Autonomy

### The INCREMENTS Autonomy Scale Explained

NEXUS uses the INCREMENTS framework (Incremental Autonomy for Safety-Critical Systems), which defines six levels of autonomy. Each subsystem on your system — steering, throttle, bilge pump, lighting, etc. — operates at its own independent level.

| Level | Name | What It Means | What You Do |
|-------|------|---------------|-------------|
| **0** | Manual | The system watches and records. It does nothing on its own. | Everything yourself. |
| **1** | Assist | The system suggests actions but never acts without your approval. | Review suggestions, approve or ignore. |
| **2** | Semi-Auto | The system executes behaviors you have approved, but you can override at any time. | Monitor and override when needed. |
| **3** | Conditional | The system operates autonomously within defined conditions. It alerts you when conditions are outside its comfort zone. | Stay available. Intervene when alerted. |
| **4** | High | The system operates autonomously in most conditions. You are available for emergencies. | Check in periodically. Handle exceptions. |
| **5** | Full | The system handles everything, including maintenance decisions. You are an administrator, not an operator. | Review weekly reports. Set high-level goals. |

### How Trust Is Earned (Slowly) and Lost (Quickly)

The trust score is a number between 0.0 and 1.0 that reflects how reliably the system has performed. It uses an asymmetric model based on human psychology research: trust is gained slowly but lost quickly.

- **Gaining trust:** Every hour of flawless autonomous operation adds a small amount to the trust score (0.002 per evaluation window). From zero, it takes approximately 120 days of continuous flawless operation to reach Level 3 (trust score 0.75) and about 300 days to reach Level 5 (trust score 0.97).
- **Losing trust:** A single safety incident drops the autonomy level immediately by one level. Three overrides in 10 minutes trigger an automatic level drop. A missed heartbeat or sensor failure also causes immediate reduction.
- **The math:** It takes 50 consecutive good evaluations to gain 0.1 trust points at moderate levels, but only 2 bad evaluations to lose 0.1 points. The ratio is 25:1 for safety-critical subsystems.

### Why the System Will Not Let You Skip to Full Autonomy

Early operators asked: "Can I just set everything to Level 5?" The answer is no, and for good reason. During the first year of deployment, two operators found workarounds to manually elevate autonomy levels. Both incidents resulted in unsafe conditions:

1. A fishing vessel operator set steering to Level 4 manually. The system had only 3 days of observation data and no validated reflexes. In a cross-wind gust, the system applied a rudder correction that was appropriate for calm conditions but excessive for the gust, causing a sharp turn. The operator overrode, but the trust model would have prevented this by requiring 720 hours of observation at Level 3 first.
2. An agricultural operator set irrigation to Level 5. The system over-watered a field because it had no observation data for the specific soil type. The resulting crop damage was entirely preventable.

After these incidents (and the resulting v2.0 firmware update), autonomy levels can only be advanced through the normal trust-building process. The `max_allowed_level` parameter can be set by the operator as a ceiling, but the `current_level` can only increase when the trust score threshold and observation time requirements are met.

### The Trust Dashboard

The trust dashboard shows each subsystem as a card with:

- **Current level** (colored bar, 0-5)
- **Trust score** (number, 0.00-1.00)
- **Days at current level** (countdown to next advancement eligibility)
- **Trend arrow** (trust score rising, stable, or declining over the past 7 days)
- **Override history** (recent overrides with timestamps and reasons)

### Real Example: How Steering Went from Level 0 to Level 3 Over 8 Months

This example is from the *F/V Resilience*, a 38-foot fishing vessel in Kodiak, Alaska, one of the first NEXUS deployments.

- **Month 1 (Level 0):** The captain operated normally. The system recorded 720 hours of sensor data: heading, rudder angle, throttle, wind speed, wave height, GPS position. No actions were taken by the system.
- **Month 2 (Level 0 → 1):** The system completed its initial pattern analysis and began displaying suggestions: "Suggested rudder correction: +3 degrees to maintain heading 045." The captain found most suggestions helpful but ignored some in heavy seas. After 72 hours with 82% suggestion acceptance and 4% false positive rate, steering advanced to Level 1.
- **Months 3-4 (Level 1 → 2):** The system proposed its first reflex: a heading-hold PID controller. The captain reviewed the proposal, ran a 2-hour A/B test (system vs. manual), and approved. The reflex ran in supervised mode for 168 hours (7 days). Override rate: 3.1% (below the 5% threshold). Advancement to Level 2.
- **Months 5-6 (Level 2 → 3):** The captain continued operating with the heading-hold reflex active. He overrode in rough conditions (cross-swell) and during docking. The system observed these overrides, proposed a second reflex for wave compensation, and the captain approved after another A/B test. After 720 hours at Level 2 with 0.08% override rate and zero safety incidents, the system advanced to Level 3.
- **Month 8 onward (Level 3):** The system now holds heading autonomously in most conditions. The captain takes over for docking, in heavy weather (wave height > 2m), and when approaching other vessels. He estimates he physically steers about 15% of the time, down from 100% before NEXUS. Fuel efficiency improved 6% due to smoother steering.

---

## 5. Training the System

### Observation Sessions: How to Record Your Expertise

An observation session is a period where the system records all sensor data while you operate your equipment. To start one:

> "Start recording session. I'm going to demonstrate how I handle engine overheating."

The system responds: "Recording started. All sensor channels active. Narrate your actions for best results."

Operate normally, but talk through your decisions. When you are done:

> "Stop recording."

The system responds: "Session recorded. Duration: 23 minutes. 138,000 data points captured. Analysis will begin shortly."

### Best Practices for Narration

After analyzing 2,400 observation sessions from operational deployments, we identified clear patterns in which sessions produced the best reflexes:

1. **Explain WHY, not just WHAT.** "I'm reducing throttle because the engine temperature is climbing" is far more valuable than "I'm pulling the throttle back." The system uses causal language to build better reflex conditions.
2. **Be specific about thresholds.** "When the temp hits 210 degrees" is better than "when it gets hot." The system can measure the exact temperature, but it needs to know your threshold.
3. **Describe exceptions.** "Normally I'd do X, but in this case I'm doing Y because..." Exception data is extremely valuable for building reflexes that handle edge cases.
4. **Narrate in real time, not after the fact.** The system timestamps your narration and correlates it with sensor data. If you narrate 30 seconds after an action, the correlation is weak.
5. **Keep sessions focused.** A 15-minute session about one specific scenario produces better reflexes than a 2-hour session covering many different situations. The system can cluster behaviors, but focused sessions reduce noise.

### Reviewing AI-Generated Proposals

When the system generates a proposal, review it carefully. Here is what to look for:

1. **Conditions:** Does the trigger condition match your intent? "When water level > 65% for > 30 seconds" — does that match when you would actually start the pump?
2. **Actions:** Does the proposed action match what you would do? Is the magnitude correct? Is the timing right?
3. **Data basis:** How many observations is the proposal based on? Proposals based on fewer than 10 observations are marked as "low confidence" and should be tested thoroughly.
4. **Consistency:** What percentage of your demonstrations matched the proposed behavior? Below 70% means the system is averaging over dissimilar situations.
5. **Safety review:** Does the proposal include safe-state fallback actions? Every approved reflex must define what happens if the reflex itself fails.

### A/B Testing: What Happens When You Approve a Trial

When you choose "TEST" instead of "APPROVE," the system runs the proposed reflex in shadow mode alongside your manual control. Here is what happens:

1. The system activates the reflex but routes its outputs to a recording buffer, not to the actuators.
2. You continue operating manually for a minimum of 30 minutes (configurable).
3. After the test, the system presents a comparison: "Your average heading error: 2.3 degrees. Reflex average heading error: 1.8 degrees. Improvement: 22%. Smoothness: your rating 7/10, reflex rating 8/10. Fuel efficiency: your 4.2 L/hr, reflex 3.9 L/hr."
4. You decide: approve, reject, extend the test, or modify conditions.

In v3.1, A/B tests use 7 standardized metrics: accuracy, smoothness, efficiency, safety margin, response latency, comfort rating, and override rate. All metrics must show improvement or no degradation for the proposal to be recommended for approval.

### The "Reject and Explain" Feature (v2.5+)

When you reject a proposal, the system asks why. This is not bureaucratic — the explanation directly improves future proposals. After 6 months of deployment data:

- **"Wrong trigger condition"** (41% of rejections) — The system adjusts its pattern discovery to look for different sensor correlations.
- **"Wrong action magnitude"** (28%) — The system recalibrates its response scaling.
- **"Missing context"** (19%) — The system adds additional sensor inputs to its analysis.
- **"Not ready for automation"** (12%) — The system marks the scenario as requiring more observation data before proposing again.

If you consistently reject proposals for a specific subsystem, the system will stop proposing for that subsystem and instead ask you to provide more demonstration sessions. This prevents the annoying "the system keeps suggesting the same wrong thing" problem reported in early v1.x deployments.

---

## 6. Troubleshooting Common Issues

### "The System Isn't Responding to My Commands"

**Most likely cause:** Heartbeat loss between Jetson and limb nodes.

1. Check the Jetson's LED. If it is solid amber or red, the Jetson may have crashed or rebooted. Wait 30 seconds — v3.1 includes automatic Jetson recovery.
2. Check the limb node LEDs. If they are solid red, they have entered safe-state due to heartbeat timeout. This happens when the serial cable is loose, damaged, or too long.
3. Check physical connections. The RS-422 cables should be firmly seated. The maximum cable length at 921,600 baud is 10 meters. If you need a longer run, the system will have auto-negotiated a lower baud rate — check the dashboard for the current link speed.
4. Try the kill switch: press and release. This forces a full system reset. In 90% of "not responding" cases, this resolves the issue.

**If the problem persists:** The Jetson may have a software issue. Power cycle the entire system (hold power button for 5 seconds, wait 10 seconds, press power). If the Jetson still does not boot, contact support — the NVMe SSD may need replacement.

### "The AI Suggestion Seems Wrong"

**Do not panic.** Suggestions are non-binding at Level 1. The system is not acting on them.

1. **Check the data basis.** On the dashboard, click the suggestion to see how many observations it is based on. If fewer than 10, it may be a statistical artifact.
2. **Check the context.** Are current conditions (wind, load, temperature) similar to the conditions in the observation data? The system may be extrapolating beyond its experience.
3. **Ignore it.** At Level 1, ignoring a suggestion has no negative impact on the trust score. The system logs the event and adjusts its confidence.
4. **If you are at Level 2+:** Override the action immediately. Say "Take over [subsystem]" or grab the physical control. Your override is logged and will cause the trust score to decrease for that subsystem — this is the correct behavior. The system will become more conservative.

### "A Reflex Is Behaving Erratically"

1. **Immediate action:** Say "Pause all reflexes" or press the kill switch if the behavior is dangerous. The kill switch physically cuts power to all actuators — it is the ultimate safety device.
2. **Identify the reflex:** Check the activity log to see which reflex was active when the erratic behavior occurred.
3. **Check for sensor issues:** Erratic reflex behavior is often caused by a failing sensor providing bad data. Check the sensor readings for that subsystem — if values are jumping wildly or reading zero, you have a sensor problem, not a reflex problem.
4. **Deactivate the reflex:** Say "Deactivate reflex [name]." The system will confirm deactivation and the subsystem will revert to the previous autonomy level.
5. **Report the issue:** Say "Report reflex issue with [name]." The system captures diagnostic data and tags it for analysis. This data is used to improve the reflex engine.

**Known issue (v3.1.1 patch):** In some deployments, PID-based reflexes can produce oscillation when sensor noise exceeds 2% of the measurement range. If you see oscillation (actuator cycling back and forth rapidly), deactivate the reflex and contact support for the noise filtering patch.

### "The System Keeps Reverting to Lower Autonomy"

This is by design, and it means something triggered a trust reduction. Check the following:

1. **Trust score trend:** Is the trust score for that subsystem declining? If so, the system is detecting performance degradation — perhaps the equipment has changed (worn seals, different load) and the reflexes need to be retrained.
2. **Override history:** Have you been overriding more frequently? An override rate above 0.5 per hour for 3 consecutive hours triggers an automatic level reduction.
3. **Sensor uptime:** A sensor that goes offline for more than 30 seconds triggers an immediate level drop. Check sensor health.
4. **Firmware update:** After any OTA firmware update (which happen automatically overnight), trust scores are reduced by 30% as a precaution. This is intentional — code changed, so the system should re-earn trust. In v3.1, the reduction is less severe for patches (15%) than for major version updates (30%).
5. **Power interruption:** If the system lost power without a clean shutdown, all subsystems revert to Level 0 on next boot. This was changed in v3.1: if the shutdown was clean (power button pressed), the system remembers its previous state.

### "I Want to Try Something New"

1. Start an observation session: "Start recording. I'm going to demonstrate [new behavior]."
2. Demonstrate the behavior while narrating your reasoning.
3. Stop recording.
4. Wait for the system to analyze the session (typically 5-15 minutes on the Jetson).
5. The system will either propose a reflex or ask for more demonstration sessions if the data is insufficient.

### "The Dashboard Shows Warnings I Don't Understand"

See Appendix D for a complete error message reference. The most common warnings are:

- **HB-MISS-3:** 3 heartbeats missed from a limb node. Usually resolves in a few seconds. If it persists, check the cable.
- **TRUST-DECLINE:** Trust score for a subsystem has dropped by more than 0.05 in the past 24 hours. Review override history for that subsystem.
- **OBS-BUF-90:** Observation buffer is 90% full. The system will stop recording new data. Sync to cloud or reduce sampling rate.
- **SENSOR-STALE:** A sensor has not reported a new reading within its expected interval. Check the sensor connection.

---

## 7. Safety

### The Kill Switch: When and How to Use It (No Judgment, Ever)

The kill switch is a red mushroom-head button that physically cuts power to all actuators. It operates independently of all software — pressing it will stop every motor, pump, valve, and relay on the system regardless of what the software is doing.

**When to use it:**

- Any time you feel uncomfortable with what the system is doing.
- Any time you observe unexpected or dangerous behavior.
- Any time you are unsure — pressing the kill switch is always safe.
- During the weekly safety test (mandatory).

**There is never a wrong time to press the kill switch.** It does not damage the system. It does not erase data. It does not affect trust scores. The system logs the event as a safety action, not as a failure. Press it whenever you feel the need.

**How to use it:**

1. Press the mushroom head firmly (22-50 newtons of force required).
2. All actuators stop immediately (within 1 millisecond).
3. All limb node LEDs turn solid red.
4. The system sounds a repeating alarm (3-beep pattern).
5. To resume operation: twist the kill switch head clockwise to release it, then follow the Recovery from Safe-State procedure below.

### What Happens in Safe-State

When the system enters safe-state (from kill switch, heartbeat timeout, or safety event):

- **All actuators stop.** Motors stop, pumps stop, valves return to their default positions.
- **All reflexes are suspended.** No automated behaviors run.
- **All control loops are paused.** PID controllers freeze at their last values.
- **Sensor monitoring continues.** The system keeps reading sensors and logging data.
- **Heartbeat monitoring continues.** The system keeps watching for Jetson communication.
- **The system does NOT auto-resume.** Ever. You must explicitly restore operation.

Safe-state is designed so that nothing the system does can make the situation worse. The only outputs from the system are alarm sounds, LED indicators, and logged data.

### Recovery from Safe-State (Step by Step)

1. **Resolve the cause.** If you pressed the kill switch because of dangerous behavior, identify and resolve the issue before proceeding.
2. **Release the kill switch.** Twist the mushroom head clockwise until it pops up.
3. **Acknowledge the safe-state condition.** The system asks: "Safe-state was triggered. Reason: kill switch activation. Do you want to resume? [RESUME] [DIAGNOSE] [POWER OFF]"
4. **Choose RESUME.** The system performs a self-test (5 seconds), checks all sensor connections, and displays the pre-safe-state autonomy levels.
5. **Confirm restoration.** The system asks: "Restore previous operating state? Steering was Level 3, throttle was Level 2. [YES] [START AT LEVEL 0]"
6. **Say YES.** The system restores all subsystems to their previous levels and re-activates their reflexes. This takes about 30 seconds. During this time, all actuators remain in safe positions.
7. **Verify.** Confirm that all subsystems are operating correctly before resuming normal activities.

### Weekly Safety Checklist (Required)

This checklist takes 5 minutes. It is mandatory — the system tracks completion and will remind you if you miss a week. Operators who consistently complete the weekly checklist experience 73% fewer safety events.

- [ ] Press and release the kill switch. Verify all actuators stop and all nodes show solid red.
- [ ] Twist to release. Verify system returns to normal operation.
- [ ] Check all limb node LEDs are solid green.
- [ ] Check the dashboard: all nodes online, no active alerts.
- [ ] Verify all sensor readings are within expected ranges.
- [ ] Check that the observation buffer is below 70% capacity.
- [ ] Say "System status" and verify the summary matches your expectations.
- [ ] Sign off: "Weekly safety check complete."

### Emergency Procedures for Each Subsystem

**Steering emergency:** Press kill switch. Steer manually using the emergency tiller (mechanical backup, independent of NEXUS). The rudder will be in amidships position (safe state).

**Throttle emergency:** Press kill switch. Engine returns to idle (if electronic throttle) or is unaffected (if mechanical throttle with NEXUS monitoring only). In v3.1, the system distinguishes between monitored and controlled throttle — check your configuration.

**Bilge emergency:** Press kill switch. Bilge pump stops. Monitor water level manually. If water is rising, operate the pump manually using the physical pump switch (wired in parallel, independent of NEXUS).

**Fire detection:** If the system detects fire (smoke sensor), it automatically enters safe-state and sounds the fire alarm. This is a Tier 1 reflex — it runs even if the Jetson is offline. Press the kill switch to confirm. Evacuate and follow your vessel/facility fire procedures.

**Collision avoidance:** If the proximity sensor detects an obstacle within the critical distance, the system automatically enters safe-state. Override the safe-state only after visually confirming the area is clear.

---

## 8. Upgrading and Maintenance

### OTA Firmware Updates

NEXUS receives firmware updates automatically over the air. Updates happen at 2:00 AM local time (configurable) when the system is in low-power mode. The update process:

1. The Jetson downloads the update package from the cloud.
2. Each limb node receives the update via serial link.
3. The node verifies the update's cryptographic signature.
4. The node writes the update to the backup OTA partition.
5. The node validates the update by computing a SHA-256 hash and comparing it to the expected value.
6. The node sets the boot flag to boot from the new partition.
7. On next reboot, the new firmware runs. If it fails the self-test, the node automatically rolls back to the previous version.

**You do not need to do anything.** The system handles updates automatically. If an update fails, the system rolls back and notifies you. In 2 years of deployment, we have had 14 OTA updates with 0 failed rollbacks.

**Note on trust scores:** After a major firmware update (e.g., v3.0 to v3.1), trust scores are reduced by 30%. After a patch update (e.g., v3.1.0 to v3.1.1), trust scores are reduced by 15%. This is intentional — code changed, and the system should re-earn trust. The reduction was 50% in v1.x, which was too aggressive and frustrated operators. v3.1 strikes a better balance.

### Hardware Replacement: Hot-Swap Procedure

If a limb node fails (LED off, rapid red blink, or dashboard shows fault), replace it:

1. **Disconnect the failed node.** Unplug the RJ-45 cable from the failed node.
2. **Plug in the replacement node.** Any ESP32-S3 unit running the NEXUS factory firmware will work. If the replacement is fresh from the box, it already has the correct firmware.
3. **Wait for auto-provisioning.** The Jetson detects the new node, assigns it the same role as the failed node, and sends the cached configuration. This takes 30-60 seconds.
4. **Verify.** The new node's LED should turn solid green. The dashboard should show the node as online with the correct role.
5. **Done.** No laptop, no flashing, no configuration.

If you are using a non-standard MCU (not ESP32-S3), the replacement must be pre-flashed with the NEXUS universal firmware. Contact support for pre-flashed replacement units.

**Jetson replacement** is more involved because it holds the system's identity, observation history, and trust scores. Contact support for Jetson replacement — it requires cloning the NVMe SSD.

### Data Management: Observation Retention and Cloud Sync

Observation data is stored locally on the Jetson's NVMe SSD using a three-tier retention policy:

| Tier | Duration | Storage | Used For |
|------|----------|---------|----------|
| Hot | 7 days | NVMe SSD, fast access | Active learning, A/B testing, recent analysis |
| Warm | 90 days | NVMe SSD, compressed | Trend analysis, reflex improvement |
| Cold | 2 years | Cloud storage | Regulatory compliance, incident investigation |

**Cloud sync** occurs automatically when connected to the internet. Over satellite links (Starlink), sync uses delta encoding (v3.1 feature) to minimize bandwidth. Typical sync bandwidth: 5-10 KB/s (down from 28.8 KB/s in v2.x).

**To force a sync:** Say "Sync observation data to cloud." The system will compress and upload all pending data. Depending on the amount of data and your connection speed, this may take a few minutes to several hours.

### Annual Maintenance Schedule

| Task | Frequency | Who Performs It |
|------|-----------|----------------|
| Kill switch timing test (oscilloscope) | Annual | Qualified technician |
| Cable inspection and replacement | Annual | Operator or technician |
| Jetson NVMe SSD health check | Annual | Operator (via dashboard) |
| Full system firmware refresh | Annual | Automatic (major version update) |
| Sensor calibration | Per manufacturer spec | Operator or technician |
| Backup battery replacement (if applicable) | Annual | Operator |
| Configuration review and backup | Annual | Operator (export to USB) |

---

## Appendix A: Voice Command Reference

### System Control
| Command | Action |
|---------|--------|
| "System status" | Reports node status, autonomy levels, trust scores |
| "Start recording" / "Stop recording" | Begins/ends observation session |
| "Pause all reflexes" | Suspends all automated behaviors |
| "Resume autonomous operation" | Restores pre-pause autonomy levels |
| "Emergency: all stop" | Enters safe-state on all subsystems |
| "Sync observation data" | Forces cloud sync |

### Subsystem Control
| Command | Action |
|---------|--------|
| "Take over [subsystem]" | Switches subsystem to manual control |
| "Release [subsystem] to system" | Returns subsystem to its current autonomy level |
| "Deactivate reflex [name]" | Stops a specific reflex |
| "Show me [sensor] readings" | Reports current sensor values |
| "Set [subsystem] max level to [N]" | Sets autonomy ceiling for a subsystem |

### Information
| Command | Action |
|---------|--------|
| "Why did you [action]?" | Explains the reasoning behind a system action |
| "What reflexes are active?" | Lists all running reflexes |
| "How is [subsystem] performing?" | Shows trust score, override rate, uptime |
| "What are you learning?" | Shows pending analysis and proposals |

---

## Appendix B: Dashboard Metric Glossary

| Metric | What It Means | Normal Range | Concerning Value |
|--------|---------------|--------------|-----------------|
| Trust Score | Reliability measure per subsystem | 0.3-1.0 | Declining trend > 0.05/day |
| Override Rate | Manual overrides per hour | 0-0.5 | > 0.5 sustained for 3+ hours |
| Heartbeat Latency | Round-trip communication time | 10-50ms | > 100ms (check cable) |
| Sensor Uptime | Percentage of time sensors report valid data | > 99% | < 95% |
| Observation Buffer | Data recording buffer fullness | 0-70% | > 90% (risk of data loss) |
| Reflex CPU Usage | Processor load on limb nodes | 10-50% | > 80% (overloaded) |
| Jetson Temperature | Brain unit temperature | 40-75°C | > 85°C (thermal throttling) |
| Link Quality | Serial communication error rate | < 0.1% | > 1% (check cable/connections) |

---

## Appendix C: LED Pattern Reference

| Pattern | Color | Meaning |
|---------|-------|---------|
| Solid | Green | Normal operation |
| 1 Hz blink | Amber | Degraded — check dashboard |
| Solid | Red | Safe-state — all actuators stopped |
| 2 Hz blink | Red | Fault — check dashboard immediately |
| Alternating | Green/Amber | Learning — recording or processing |
| Rapid blink | Amber | Booting — wait |
| Off | — | No power or boot failure |

---

## Appendix D: Error Message Quick Reference

| Code | Message | Severity | Action |
|------|---------|----------|--------|
| HB-MISS-3 | 3 heartbeats missed | Warning | Wait — usually resolves. If persistent, check cable. |
| HB-MISS-10 | 10 heartbeats missed | Critical | Node entered safe-state. Check cable and Jetson status. |
| TRUST-DECLINE | Trust score declining | Warning | Review override history. May indicate equipment changes. |
| OBS-BUF-90 | Observation buffer 90% full | Warning | Sync to cloud or reduce sampling rate. |
| SENSOR-STALE | Sensor data not updating | Warning | Check sensor connection. |
| REFLEX-HALT | Reflex execution halted | Error | Check reflex details on dashboard. May need retraining. |
| OTA-FAIL | Firmware update failed | Warning | System auto-rolls back. No action needed. |
| OVERCURRENT | Overcurrent detected | Critical | Actuator disabled. Check for mechanical binding. |
| WDT-RESET | Watchdog timeout reset | Critical | Node rebooted unexpectedly. Check for firmware issue. |
| E-STOP | Kill switch activated | Info | Normal during safety test or intentional stop. |
| TEMP-HIGH | Jetson temperature high | Warning | Check fan and ventilation. System throttles at 85°C. |
| CRC-ERROR | Communication error detected | Warning | Check cable. System auto-corrects via retransmission. |
| CALIB-DUE | Sensor calibration overdue | Warning | Schedule sensor calibration per manufacturer spec. |
