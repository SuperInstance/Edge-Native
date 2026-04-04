# NEXUS Quick Start — From Box to Operation in 30 Minutes

**Version:** 3.1.0  
**Last Updated:** 2026-03-29  
**Prerequisite:** None — this guide assumes no prior technical knowledge  

---

## 1. What You Need

### Contents of the NEXUS Deployment Kit

Before you begin, verify your kit contains the following:

| Item | Quantity | Description |
|------|----------|-------------|
| Jetson Orin Nano unit (aluminum enclosure) | 1 | The "brain" — a small fan-cooled computer, approximately 10 cm x 10 cm x 5 cm. Has labeled RJ-45 ports (1-8) for limb connections, a 12V power input barrel jack, a kill switch port, a USB-C port, and a power button. |
| ESP32-S3 limb nodes | 1-8 (typical: 3) | The "limbs" — small circuit boards (5 cm x 3 cm) with an RJ-45 port, an LED indicator, and a label showing the node's pre-assigned hardware address (N1, N2, N3, etc.). |
| 12V power supply | 1 | 12V DC, 10A minimum (120W). Includes a barrel jack connector for the Jetson and a terminal block for optional direct wiring. |
| Kill switch | 1 | Red mushroom-head button (22mm panel-mount), pre-wired with a 3-meter cable and RJ-45 plug. This is mandatory — the system will not start without it connected. |
| RJ-45 Cat-5e cables | 1 per limb node | Standard Ethernet cables. Use the ones provided — they are shielded and rated for the RS-422 signal used by NEXUS. Ordinary patch cables will work at short distances but may cause errors at lengths over 3 meters. |
| Quick Start card (laminated) | 1 | Wallet-sized reference card with the essential commands and LED patterns. Keep it with you during operation. |

### Tools Required

**None.** You do not need a laptop, a screwdriver, a multimeter, or any software. The NEXUS system provisions itself. You just plug things together and talk.

### Optional but Helpful

- A tablet or smartphone running the NEXUS companion app (for a larger dashboard view).
- Cable ties or velcro straps for securing cables (not required but recommended on vessels and in industrial settings).
- A pen and paper for writing down your equipment configuration before starting the provisioning wizard (helps if you have many sensors and actuators).

---

## 2. Physical Setup (10 minutes)

### Step 1: Mount the Jetson Brain Unit (2 minutes)

Place or mount the Jetson unit in a dry, ventilated location near where you will operate. It needs:

- **Power access** — within reach of the 12V power supply.
- **Ventilation** — the fan needs unrestricted airflow. Do not enclose the unit in a sealed box.
- **Cable access** — within cable reach of all limb node locations.

If your kit includes mounting hardware, use the four included screws to secure the unit. Otherwise, place it on a flat, stable surface.

### Step 2: Connect ESP32 Limb Nodes (3 minutes)

For each limb node:

1. Place the limb node near the sensor(s) and actuator(s) it will control.
2. Run an RJ-45 cable from the limb node to the corresponding port on the Jetson. Port 1 on the Jetson corresponds to Node 1, Port 2 to Node 2, etc. The cables are labeled.
3. Connect your sensors and actuators to the limb node's screw terminals. Each terminal is labeled with its function (GPIO pin number, I2C bus, ADC channel, etc.). Refer to the wiring diagram included in your kit for your specific equipment configuration.

**Important:** The RJ-45 cables carry both data and power to the limb nodes. You do not need separate power connections for the nodes.

### Step 3: Connect Power (1 minute)

1. Plug the 12V power supply into a mains outlet.
2. Connect the barrel jack to the Jetson's power input.
3. The Jetson's power LED (small white LED near the power button) should light up, indicating standby power.

Do not press the power button yet.

### Step 4: Connect the Kill Switch (2 minutes)

1. Locate the kill switch cable (red, with an RJ-45 plug).
2. Plug it into the kill switch port on the Jetson (labeled with a red "E-STOP" label, separate from the data ports).
3. Mount the kill switch itself within arm's reach of your normal operating position. It should be accessible without looking — you may need to press it in an emergency.
4. If your kit includes panel-mount hardware for the kill switch, install it now. The standard 22mm hole size fits most instrument panels.

**The system checks for the kill switch connection at boot and will not proceed without it.** This is a safety requirement, not a suggestion.

### Step 5: Press Power (immediate)

Press the power button on the Jetson. The fan will spin up, and the system will begin booting.

---

## 3. First Boot (5 minutes)

### Watch the LED Sequence

After pressing power, observe the LEDs on each limb node and the Jetson:

| Time | What You See | What It Means |
|------|-------------|---------------|
| 0-5 seconds | All limb nodes: rapid amber blink (2 Hz) | Firmware loading from flash |
| 5-15 seconds | Jetson: solid amber | Linux booting, cognitive services starting |
| 15-30 seconds | Each limb node: green blink, 1 Hz (one at a time) | Node detected, waiting for role assignment |
| 30-45 seconds | All nodes: brief amber flash | Configuration being sent from Jetson |
| 45-60 seconds | All nodes: solid green | **Operational** |

If any node does not reach solid green within 90 seconds, check its RJ-45 cable connection and try reseating it. If the problem persists, that node may have a hardware issue — the system will continue operating with the remaining nodes.

### Wait for the Announcement

When all nodes are solid green, the Jetson's speaker activates:

> "NEXUS online. [N] nodes detected. Awaiting commands."

Where [N] is the number of limb nodes found. A typical 3-node system responds: "NEXUS online. Three nodes detected. Awaiting commands."

The system is now ready for configuration.

---

## 4. Configure Your System (5 minutes)

### Tell the System What You Want to Control

The provisioning wizard will guide you through configuration using voice or text (depending on your kit's display option). Here is a typical conversation for a marine vessel setup:

**System:** "Please describe what you want to control. Be as specific as you can about the equipment and how it is wired."

**You:** "I have a 42-foot fishing vessel. The rudder hydraulic valve and rudder angle sensor are on node 1. The electronic throttle and engine RPM sensor are on node 2. The bilge float switch and bilge pump relay are on node 3."

**System:** "I've detected the following on your nodes: Node 1 has an I2C device at address 0x1E (likely a compass) and a PWM output on GPIO 4. Node 2 has a frequency input on GPIO 16 (RPM sensor) and an ADC input on GPIO 32. Node 3 has a digital input on GPIO 4 (float switch) and a relay output on GPIO 5. Is this correct?"

**You:** "Yes. Also, there is a wind speed sensor on node 1's I2C bus at address 0x40."

**System:** "Added wind speed sensor on node 1, I2C address 0x40. I propose the following configuration: [displays configuration summary]. Approve?"

**You:** "Approve."

**System:** "Configuration saved. Running self-test on all nodes... All nodes pass. System is ready. Please describe any safety limits."

**You:** "The rudder can move from minus 35 to plus 35 degrees. The throttle should never exceed 85 percent. The bilge pump should not run for more than 5 minutes continuously."

**System:** "Safety limits configured. Rudder range: minus 35 to plus 35 degrees. Throttle maximum: 85 percent. Bilge pump timeout: 5 minutes. Provisioning complete."

This entire conversation typically takes 3-5 minutes. The system remembers your configuration in non-volatile storage — you only need to do this once.

---

## 5. Demonstrate Your First Behavior (10 minutes)

Now you will teach the system its first automated behavior. This is the core of how NEXUS learns.

### Step 1: Start Recording

**You:** "Start recording session. I'm going to demonstrate how I steer the vessel."

**System:** "Recording started. All sensor channels active at 10 Hz. Narrate your actions for best results."

### Step 2: Demonstrate and Narrate

Operate your equipment as you normally would. Talk through your decisions in real time. Here is an example for a steering demonstration:

> "I'm turning the wheel to the right. The rudder is moving to plus 15 degrees. I can see the heading is drifting — I need more rudder authority. I'm applying plus 25 degrees. The heading is now correcting. I'm easing the rudder back to plus 10 degrees as the heading error decreases. When the heading error is more than 5 degrees, I apply more rudder quickly. When it's less than 2 degrees, I ease off gradually."

Continue demonstrating for 5-10 minutes. Try to cover a range of conditions: gentle corrections, sharp turns, steady-state holding. The more variety in your demonstration, the better the reflex will be.

### Step 3: Stop Recording

**You:** "Stop recording."

**System:** "Session recorded. Duration: 8 minutes 23 seconds. 503,000 data points captured across 6 sensor channels. Analysis will begin. This typically takes 5 to 15 minutes."

### Step 4: Review the Proposal

After the analysis completes (5-15 minutes), the system presents a proposal:

**System:** "I have a proposal for you. Steering Reflex, version 1. Based on your demonstration: When heading error exceeds 3 degrees, apply rudder correction proportional to the error. When heading error drops below 2 degrees, reduce rudder smoothly. This matches your behavior in 84% of the 47 steering events I identified. Shall I activate this reflex in supervised mode? You can override at any time."

**You:** "Tell me more."

**System:** "The reflex uses a PID controller with proportional gain 1.2, integral gain 0.05, and derivative gain 0.3. These values were derived from your demonstration data. The reflex will maintain your current heading automatically. Rudder corrections will be limited to minus 35 to plus 35 degrees per your safety configuration. If the heading error exceeds 15 degrees, the reflex will alert you and recommend manual takeover."

**You:** "Activate in supervised mode."

**System:** "Steering reflex activated. Current autonomy level for steering: Level 2, Semi-Auto. The reflex is now controlling the rudder. You can override at any time by saying 'Take over steering' or by physically turning the wheel. Override rate and performance will be monitored."

### Step 5: Approve for Production

After the reflex runs in supervised mode for a while and you are satisfied:

**You:** "Approve steering reflex for production."

**System:** "Steering reflex approved. It will remain active across reboots. Trust score tracking has begun. Current trust score for steering: 0.30. Advancement to Level 3 requires trust score of 0.75 and 720 hours of observation. Estimated timeline: approximately 4 months at current performance."

---

## 6. You're Operational

**Congratulations.** Your NEXUS system is now running with its first automated reflex. Here is what to expect:

### Immediate Next Steps

- **Monitor the reflex.** Watch how it performs over the next few hours. Override it whenever you disagree with its actions. Overrides are normal and expected during the learning period.
- **Record more demonstrations.** The more data the system has, the better its reflexes will be. Record sessions for different conditions: calm weather, rough weather, docking, maneuvering in tight spaces.
- **Describe your intents.** Tell the system about other behaviors you want automated. "When the wind exceeds 20 knots, I want the system to alert me and suggest reducing speed." The system will observe your behavior in those conditions and eventually propose a reflex.
- **Complete the weekly safety check.** See the User Guide, Section 7. This is mandatory and takes 5 minutes.

### What Happens Over Time

The system will progressively earn your trust and advance through autonomy levels. Here is a realistic timeline for a typical marine vessel:

| Timeframe | Expected Progress |
|-----------|------------------|
| Week 1 | Level 0 → Level 1 (assist). System begins displaying suggestions. |
| Month 1-2 | Level 1 → Level 2 (semi-auto). First reflex approved and running. |
| Month 3-5 | Level 2 → Level 3 (conditional). Reflex handles most routine steering. |
| Month 6+ | Level 3 → Level 4 (high). System operates autonomously in most conditions. |
| Year 1+ | Level 4 → Level 5 (full). For low-risk subsystems like bilge and lighting. |

Safety-critical subsystems (steering, throttle) take longer to advance because the trust thresholds are higher. Low-risk subsystems (lighting, bilge, ventilation) advance faster.

### Getting Help

- **Say "Help"** at any time for a list of available commands.
- **Say "Explain [topic]"** for plain-language explanations of any NEXUS concept.
- **Consult the User Guide** for detailed procedures and troubleshooting.
- **Contact support** if you encounter a hardware failure or a problem not covered in this guide.

---

## Quick Reference Card (Laminated Wallet Card Content)

### Essential Voice Commands
- **"System status"** — Full status report
- **"Emergency: all stop"** — Safe-state, all subsystems
- **"Take over [subsystem]"** — Manual control
- **"Release [subsystem]"** — Back to system control
- **"Start recording" / "Stop recording"** — Observation sessions
- **"Pause all reflexes"** — Suspend automation
- **"Resume autonomous operation"** — Restore previous state
- **"Help"** — Command list

### LED Patterns
| Pattern | Meaning |
|---------|---------|
| 🟢 Solid green | Normal — all good |
| 🟡 Amber blink | Degraded — check dashboard |
| 🔴 Solid red | Safe-state — actuators stopped |
| 🟢🟡 Alternating | Learning — recording active |
| 🔴 Rapid blink | Fault — check immediately |

### Daily Checklist
- [ ] All nodes show solid green
- [ ] Kill switch test: press and release
- [ ] Dashboard: no alerts
- [ ] Say "System status" — verify
- [ ] Begin operations

### Emergency
- **Kill switch** = all stop. No judgment. Press anytime.
- **"Emergency: all stop"** = same effect, software-triggered.
- After kill switch: twist to release → say "Resume" → verify → operate.

### Troubleshooting
| Problem | Try This |
|---------|----------|
| System not responding | Check cables, press kill switch, power cycle |
| Erratic behavior | "Pause all reflexes," check sensors |
| Wrong suggestion | Ignore it (Level 1), or override (Level 2+) |
| Trust declining | Review override history, check equipment |
