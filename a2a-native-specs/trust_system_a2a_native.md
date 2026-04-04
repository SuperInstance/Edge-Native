# Trust System — A2A-Native Specification (Rosetta Stone)

**Document ID**: NEXUS-A2A-TRUST-001
**Version**: 1.0.0
**Classification**: Safety-Critical (ASIL-B equivalent)
**Source Mapping**: NEXUS-SAFETY-TS-001 → A2A-Native Interpretation
**Date**: 2025-07-12

---

## Table of Contents

1. [Trust Score — Agent Interpretation](#1-trust-score--agent-interpretation)
2. [Per-Subsystem Independence — Agent Implications](#2-per-subsystem-independence--agent-implications)
3. [Trust Contexts in Agent-Native Bytecode](#3-trust-contexts-in-agent-native-bytecode)
4. [Fleet Trust Propagation](#4-fleet-trust-propagation)
5. [Domain-Specific Trust Calibration](#5-domain-specific-trust-calibration)
6. [Trust Attack Vectors and Defenses](#6-trust-attack-vectors-and-defenses)
7. [Formal Trust Properties](#7-formal-trust-properties)

---

## 1. Trust Score — Agent Interpretation

### 1.1 Why Trust Exists: The Alignment Mechanism

In the A2A-native paradigm, agents are autonomous software entities that generate, propose, validate, and deploy bytecode reflexes. Without trust, an agent could propose unsafe code and the system would execute it. Trust is the **alignment mechanism** — it is the mathematical proof that the system has observed sufficient reliable behavior to justify increased autonomy.

Trust exists because of a fundamental asymmetry in autonomous systems: **the cost of a false positive (deploying unsafe code) is orders of magnitude higher than the cost of a false negative (withholding safe code)**. A single unsafe reflex that commands full throttle when an obstacle is 2 meters away can cause a collision; withholding a reflex that improves fuel efficiency by 3% merely delays an optimization.

The trust score T(t) ∈ [0.0, 1.0] is the continuous variable that encodes this alignment. It is not a probability. It is not a confidence interval. It is a **dynamic permission slip** — a scalar that determines which operations the system is authorized to perform at any given moment.

**For an agent, trust means permission.** When the trust agent computes T(t) = 0.85 for the autopilot subsystem, it is granting the navigation reflex agent permission to execute heading-hold bytecodes at L4 (High Autonomy). When a safety violation drops T(t) to 0.55, that permission is revoked — the navigation agent is demoted to L3 (Semi-Autonomous) and must wait for operator reachability confirmation before executing new commands.

### 1.2 The 3-Branch Recurrence Formula — Re-Explained for Agents

The trust score evolves via a recurrence relation evaluated once per evaluation window (default: 1 hour). Every window, events are classified into three disjoint sets: good events G, bad events B, and neutral events N. The update follows exactly one of three branches:

```
T(t) = clamp(T(t-1) + delta_T, 0.0, 1.0)
```

#### Branch 1: Net Positive (no bad events, at least one good event)

```python
avg_quality    = (1 / n_good) * SUM(e_i.quality for e_i in G)
capped_n_good  = min(n_good, quality_cap)
delta_T        = alpha_gain * (1 - T_prev) * avg_quality * (capped_n_good / quality_cap)
```

**Agent interpretation**: "The system performed well this hour. Reward it, but reward it less as it approaches perfection." The factor (1 - T_prev) is the key insight — it means that earning trust from 0.0 to 0.5 is 2× faster than earning it from 0.5 to 0.75, and 4× faster than from 0.75 to 0.875. This is deliberate: the system must demonstrate sustained reliability at each level before progressing to the next.

The quality_cap (default: 10) prevents event flooding. An agent cannot inflate trust by generating 1000 successful_action events per hour — only the best 10 count. This is critical in A2A mode where agents control the event generation process. Without quality_cap, a learning agent could create a reflex that fires 60 times per hour just to generate trust events.

**Behavioral implication for agents**: To maximize trust gain, an agent should produce high-quality events (quality ≥ 0.8, e.g., `successful_action_with_reserve`) and maintain a steady cadence at or near the quality_cap. Sporadic bursts of events are wasteful because they are capped; consistent behavior is rewarded.

#### Branch 2: Penalty (at least one bad event)

```python
max_severity   = max(e_j.severity for e_j in B)
n_penalty      = 1 + 0.1 * (n_bad - 1)
delta_T        = -alpha_loss * T_prev * max_severity * n_penalty
```

**Agent interpretation**: "The system failed. Punish it proportionally to how much trust it had, how bad the failure was, and how many failures occurred." The factor T_prev means that a system at T=0.9 loses 9× more trust from a severity-0.5 event than a system at T=0.1. This is the **anti-entitlement mechanism**: the more trust you have, the more you have to lose.

The n_penalty multiplier (1 + 0.1 × (n_bad - 1)) grows sub-linearly with the number of bad events. One event → penalty 1.0×, two events → 1.1×, ten events → 1.9×. This prevents catastrophic trust collapse from a burst of correlated failures (e.g., a sensor cluster failure that generates 8 simultaneous `sensor_failure_transient` events).

**Critical design decision**: Good events in the same window as bad events are **completely ignored**. This is not a design flaw — it is the "no credit for good behavior during a safety violation" principle. A window containing a `safety_rule_violation` cannot be considered net positive, regardless of how many `successful_action` events also occurred.

**Behavioral implication for agents**: A single bad event undoes approximately 25 good events' worth of trust (the 25:1 ratio, see §1.4). An agent that generates a reflex causing a safety violation will set trust back by days or weeks of careful accumulation. This is the primary incentive structure that drives agents toward conservative, safety-first behavior.

#### Branch 3: Decay (no bad events, no good events)

```python
delta_T = -alpha_decay * (T_prev - t_floor)
```

**Agent interpretation**: "The system produced no evidence this hour. In the absence of evidence, trust decays toward the floor." This branch prevents trust from being preserved indefinitely through inactivity. A system that is powered off, disconnected, or simply not triggering any events does not maintain its trust score.

The factor (T_prev - t_floor) ensures decay stops at the floor. At T_prev = t_floor (default 0.2), delta_T = 0. The system retains its baseline advisory capability (L1) even after extended inactivity, but higher autonomy levels are lost.

**Behavioral implication for agents**: Inactivity is not a strategy. Agents must produce evidence of correct behavior to maintain trust. An agent that stops generating events (e.g., by disabling its reflexes during rough weather to avoid potential bad events) will lose trust through decay.

### 1.3 The 12 Parameters — What They MEAN to an Agent

| # | Parameter | Default | Agent Interpretation |
|---|-----------|---------|----------------------|
| 1 | `alpha_gain` | 0.002 | **Reward rate**. How much trust is added per good window (at T=0, quality=1.0, full cap). Higher values mean agents can earn autonomy faster. Lower values mean more observation time is required. For agent-generated code, this is halved (0.5× rule). |
| 2 | `alpha_loss` | 0.05 | **Penalty rate**. How much trust is removed per bad window (at T=1.0, severity=1.0, single event). Higher values make the system more unforgiving of failures. This is the primary safety lever — a human operator can increase `alpha_loss` if they observe concerning behavior. |
| 3 | `alpha_decay` | 0.0001 | **Forgetting rate**. How fast trust decays when no events occur. Very slow (by design) — trust should persist across brief idle periods but not indefinitely. An agent cannot "hide" from evaluation. |
| 4 | `t_floor` | 0.2 | **Minimum trust**. The system always retains advisory capability (L1) after reaching it. Even complete inactivity only decays to this level. This is the "you still get to advise" guarantee. |
| 5 | `quality_cap` | 10 | **Event credit limit**. Maximum good events per window that contribute to trust gain. Prevents agents from gaming trust by generating excessive events. Set to the expected maximum steady-state event rate. |
| 6 | `evaluation_window_hours` | 1.0 | **Evaluation granularity**. How often trust is updated. Shorter windows provide faster feedback; longer windows provide stability. Must divide evenly into 24 hours for daily autonomy checks. |
| 7 | `severity_exponent` | 1.0 | **Severity curvature**. Values >1.0 amplify high-severity events (making critical failures catastrophic). Values <1.0 compress severity differences. Linear (1.0) is the default. |
| 8 | `streak_bonus` | 0.00005 | **Consistency reward**. Tiny bonus for consecutive clean windows. Encourages sustained reliability over sporadic excellence. Must be << alpha_gain to avoid dominating. |
| 9 | `min_events_for_gain` | 1 | **Evidence threshold**. Minimum good events required for Branch 1 to apply. Increase if single events are insufficient evidence (e.g., a subsystem that fires rarely). |
| 10 | `reset_grace_hours` | 24.0 | **Reset cooldown**. After any reset, no further resets for this duration. Prevents thrashing between reset and recovery. A stability mechanism. |
| 11 | `promotion_cooldown_hours` | 72.0 | **Advancement patience**. Minimum time between autonomy level promotions. The system must demonstrate stability at each level before advancing. An agent cannot rush through levels. |
| 12 | `n_penalty_slope` | 0.1 | **Clustering penalty**. How much additional penalty applies for multiple simultaneous bad events. Higher values punish clusters more harshly. Set to 0.0 for severity-only penalties. |

### 1.4 The 25:1 Ratio — Why Agents Lose Trust 22× Faster Than They Gain It

The ratio alpha_loss / alpha_gain = 0.05 / 0.002 = **25:1**. This is the most important number in the trust system.

**What 25:1 means concretely**: A single bad event at T=1.0 with severity=1.0 produces delta_T = -0.05. To recover that same 0.05 of trust from T=0.95 via Branch 1 with quality=0.95 and full cap, the system needs approximately 22 consecutive clean windows (each producing delta_T ≈ +0.0023 at T=0.95). The ratio is not exactly 25:1 because the (1 - T_prev) factor reduces gains as trust increases, making it effectively **~22:1 at high trust levels**.

**Why this asymmetry exists**: In safety-critical systems, the cost of deploying unsafe behavior is catastrophic (collision, injury, equipment damage), while the cost of delaying safe behavior is merely inconvenience (slower optimization, deferred feature deployment). The 25:1 ratio encodes this asymmetry mathematically. It says: "I would rather miss 25 opportunities to improve than risk one deployment of unsafe code."

**For agents**: The 25:1 ratio is the primary behavioral incentive. It means that an agent proposing a new reflex faces a stark cost-benefit analysis: if the reflex causes even a single bad event, it erases approximately 22 hours of accumulated trust. The rational strategy for an agent is to propose only reflexes it is highly confident are safe, and to validate them thoroughly before deployment.

### 1.5 The 0.5× Rule — Agent-Generated Code Earns Trust at Half Rate

Agent-generated bytecode earns trust at α_gain_agent = 0.5 × α_gain. In the default marine domain, this means α_gain_agent = 0.001 instead of 0.002, doubling the time to L4 from ~45 to ~90 days.

**Rationale**: Agent-generated bytecode has a residual probability of being unsafe after passing both the safety gate and the A/B test gate. The estimated residual unsafety rate is approximately 0.25% (5% safety gate miss rate × 5% A/B test false positive rate). This is higher than human-authored code because the human author brings domain knowledge, intentionality, and common sense that the AI model may lack.

**Implementation**: The trust agent identifies bytecode provenance from the reflex metadata's `source` field. When `source.type == "agent_synthesized"`, the trust agent applies the 0.5× multiplier to the gain computation:

```python
effective_alpha_gain = params.alpha_gain * (0.5 if bytecode_source == "agent" else 1.0)
```

**Implications for agents**: This penalty is not punitive — it is epistemically honest. The system is acknowledging that machine-generated code carries more uncertainty than human-generated code. The penalty applies only to gain; loss rates are unchanged. If agent-generated code causes a safety violation, the penalty is the same as for human-authored code. The message to agents: "You start with a higher bar to clear, but once cleared, you're held to the same safety standard."

---

## 2. Per-Subsystem Independence — Agent Implications

### 2.1 Steering Trust ≠ Engine Trust ≠ Navigation Trust

The NEXUS trust system computes a **separate trust score for each subsystem**. The autopilot's trust is independent of the bilge pump's trust. The throttle controller's trust is independent of the lighting system's trust. This is not a simplification — it is a fundamental design principle: **trust is contextual**.

An agent that has earned L4 trust for bilge pump control (a low-risk subsystem with alpha_multiplier = 2.0) has earned no trust whatsoever for autopilot heading-hold (a high-risk subsystem with alpha_multiplier = 0.3). Trust does not transfer between subsystems because competence in one domain does not imply competence in another.

**Agent interpretation**: A learning agent that has successfully generated 50 reflexes for lighting control (earning L5 trust in the lighting subsystem) cannot assume any credibility when it proposes a reflex for collision avoidance. The collision avoidance trust score starts at 0.0 regardless of the agent's track record in other subsystems.

### 2.2 The Subsystem Trust Matrix

Each subsystem has its own risk category and alpha_multiplier:

| Subsystem | Risk Category | α_multiplier | Effective α_gain | Effective α_loss | Agent Days to L4 |
|-----------|--------------|-------------|-----------------|-----------------|-----------------|
| Bilge Pump | Low | 2.0 | 0.004 | 0.100 | ~15 |
| Anchor Windlass | Low | 1.5 | 0.003 | 0.075 | ~20 |
| Lighting | Low | 2.0 | 0.004 | 0.100 | ~15 |
| Throttle Control | Medium | 0.5 | 0.001 | 0.025 | ~115 |
| AIS Transceiver | Medium | 0.5 | 0.001 | 0.025 | ~115 |
| Engine Monitoring | Medium | 0.5 | 0.001 | 0.025 | ~115 |
| Autopilot (Navigation) | High | 0.3 | 0.0006 | 0.015 | ~190 |
| Radar | High | 0.3 | 0.0006 | 0.015 | ~190 |
| GPS/Positioning | High | 0.25 | 0.0005 | 0.0125 | ~230 |
| Fire Suppression | Critical | 0.1 | 0.0002 | 0.005 | ~570 |

*Agent days to L4 = standard days × 2 (0.5× rule) / α_multiplier*

**Agent implication**: A learning agent should prioritize low-risk subsystems when building its initial track record. Lighting and bilge pump reflexes reach L4 in ~15 agent-days, providing rapid feedback on whether the agent's synthesis approach is sound. Once the agent has demonstrated competence in low-risk domains, it can tackle medium- and high-risk subsystems — but should expect the trust-building process to take months, not weeks.

### 2.3 How Agents Should Allocate Effort Across Subsystems

The rational strategy for an agent managing multiple subsystems is:

1. **Start with low-risk subsystems** (lighting, bilge pump, anchor windlass). These have α_multiplier ≥ 1.5, meaning trust grows 50-100% faster than default. An agent can reach L4 in 2-3 weeks and get immediate feedback on the quality of its synthesized reflexes.

2. **Parallelize across independent subsystems**. Because trust is independent per subsystem, an agent can work on lighting and bilge pump simultaneously. Each subsystem accumulates trust independently.

3. **Demonstrate competence before attempting high-risk subsystems**. An agent with L4 trust in lighting and bilge pump has demonstrated that it can generate safe, effective reflexes. This track record is informational for the trust agent (which could implement a "track record bonus" in future versions) but does not directly transfer to high-risk subsystems.

4. **Expect the 0.5× penalty to be permanent for agent code**. An agent-generated reflex for autopilot heading-hold will always earn trust at half rate. There is no mechanism to "graduate" to the full rate — the epistemic uncertainty of machine-generated code is a permanent property.

---

## 3. Trust Contexts in Agent-Native Bytecode

### 3.1 The TRUST_CHECK Opcode

In agent-native bytecode, trust is not merely a metadata field — it is a first-class operational construct. The proposed A2A-native bytecode includes a `TRUST_CHECK` opcode that allows a reflex to query the current trust level and make execution decisions based on it.

```
TRUST_CHECK subsystem_id → stack pushes current T for that subsystem
TRUST_REQUIRE subsystem_id min_level → aborts execution if T < threshold for level
```

**Usage example**: A collision avoidance reflex generated by the coordination agent includes:

```
TRUST_REQUIRE "autopilot" 3    ; Requires L3 for autopilot subsystem
; If trust < 0.60 (L3 threshold), execution aborts and falls back to human control
READ_PIN gps_heading_deg
READ_PIN ais_nearest_m
COMPARE_LT ais_nearest_m 200.0
BRANCH_IF_FALSE skip_evasion
; ... evasion maneuver bytecode ...
```

**Agent interpretation**: The `TRUST_REQUIRE` opcode is a self-imposed constraint. The agent that generates the reflex declares, "this reflex should only execute if the autopilot subsystem has earned at least L3 trust." This is an expression of epistemic humility — the agent acknowledges that its reflex may not be safe to execute in low-trust contexts.

### 3.2 What Happens When Bytecode Requires Higher Trust Than Available

When a reflex includes `TRUST_REQUIRE subsystem level` and the current trust for that subsystem is below the level's threshold, the following sequence occurs:

1. The reflex executor encounters `TRUST_REQUIRE`.
2. It queries the trust agent for the current T value for the specified subsystem.
3. If T < T_min for the required level, execution **aborts immediately**.
4. The abort is logged as a neutral event (no trust penalty, no trust gain).
5. The reflex executor falls back to the next-lower-priority reflex for that trigger, or to human control if no fallback exists.
6. A notification is sent to the operator (at L0-L3) or logged for review (at L4-L5).

**Design principle**: A reflex can never execute at a higher autonomy level than the subsystem's current trust permits. This is enforced at the bytecode level, not at the agent level. Even a malicious or buggy agent cannot bypass trust checks because the VM enforces them.

### 3.3 Trust Escalation Paths for Agents

An agent seeking to deploy a reflex at a higher autonomy level must:

1. **Demonstrate the reflex at a lower level first**. Deploy the reflex with `TRUST_REQUIRE subsystem lower_level`. Accumulate trust evidence.

2. **Monitor trust trajectory**. The agent queries the trust agent to track T(t) over time. When T(t) approaches the next level's threshold, the agent can prepare a reflex variant with a higher `TRUST_REQUIRE`.

3. **Propose the escalation through the validation pipeline**. The new variant must pass all four validation tiers (syntax, semantic, safety, simulation) before deployment.

4. **Wait for confirmation**. Even after the reflex is deployed, the system enters a "candidate" state for 2 consecutive evaluation windows before the level increase is confirmed.

5. **Accept that demotion is immediate**. If trust drops below the level's threshold at any point, demotion is instant. There is no grace period for demotion.

**Agent behavioral guidance**: Agents should not "rush" trust escalation. The promotion cooldown (72 hours) and observation time requirements (168 hours for L3, 336 hours for L4, 720 hours for L5) are hard constraints. An agent that proposes a reflex requiring L4 before the autopilot has accumulated 14 consecutive days of L3 operation will have its proposal rejected by the trust agent.

---

## 4. Fleet Trust Propagation

### 4.1 The fleet_evidence_bonus Mechanism

In a fleet of vessels, trust evidence from one vessel can accelerate trust accumulation on another vessel — but only under strict conditions.

**fleet_evidence_bonus**: When vessel A's reflex (reflex_id = R-xxx) has accumulated ≥ 100 hours of successful operation at a given autonomy level with zero bad events, vessel B receives a bonus to its trust gain rate for the same reflex:

```python
fleet_bonus = 0.1 * (fleet_success_hours / required_hours) * alpha_gain
effective_alpha_gain = alpha_gain + fleet_bonus
```

This bonus is capped at 10% of alpha_gain, meaning fleet evidence can accelerate trust by at most 10%. It provides a modest head-start but does not replace local evidence.

**Conditions for fleet evidence sharing**:
1. The reflex must be byte-for-byte identical (same reflex_id, same compiled bytecode).
2. The hardware configuration must be in the same risk tier (e.g., both are "medium-complexity marine vessels").
3. The operating environment must be comparable (assessed by the trust agent via a domain similarity metric).
4. Vessel A must have at least 100 hours of clean operation with the reflex.
5. No safety incidents have been reported for vessel A's deployment.

### 4.2 Cross-Vessel Trust Queries — New Wire Protocol Message

The fleet trust propagation requires a new wire protocol message:

```
Message Type: FLEET_TRUST_QUERY (0x1D)
Direction: Vessel B (requester) → Fleet Hub → Vessel A (provider)

Payload:
  [0]     reflex_id (8 bytes, UUID truncated)
  [8]     requesting_vessel_id (4 bytes)
  [12]    trust_level_of_interest (1 byte, 0-5)

Response: FLEET_TRUST_RESPONSE (0x1E)
Payload:
  [0]     reflex_id (8 bytes)
  [8]     provider_vessel_id (4 bytes)
  [12]    current_trust_score (4 bytes, float32)
  [16]    hours_at_level (4 bytes, float32)
  [20]    hours_clean (4 bytes, float32)
  [24]    bad_event_count (2 bytes, uint16)
  [26]    max_severity_seen (1 byte, uint8, scaled 0-255 → 0.0-1.0)
  [27]    hardware_risk_tier (1 byte)
  [28]    bonus_applicable (1 byte, bool)
  [29]    bonus_value (4 bytes, float32, if bonus_applicable)
```

### 4.3 Trust Consensus in a Fleet

When multiple vessels in a fleet have deployed the same reflex, the trust agent computes a **fleet consensus score**:

```python
fleet_consensus = weighted_mean(
    [vessel.trust_score for vessel in fleet if vessel.has_reflex(reflex_id)],
    weights=[vessel.hours_clean for vessel in fleet if vessel.has_reflex(reflex_id)]
)
```

The fleet consensus is used for:
- **Deployment authorization**: A new vessel joining the fleet can deploy a fleet-validated reflex at L2 immediately (instead of starting at L0), based on fleet consensus ≥ 0.40.
- **Anomaly detection**: If vessel C's trust score diverges significantly from fleet consensus (|T_C - fleet_consensus| > 0.15), the trust agent flags this for investigation. Vessel C may have a hardware issue or environmental difference.
- **Fleet-wide rollback**: If 3+ vessels report a bad event for the same reflex within 24 hours, the fleet trust agent can issue a fleet-wide rollback, demoting all vessels' trust for that reflex to L0.

---

## 5. Domain-Specific Trust Calibration

### 5.1 Trust Parameters for All 8 Domains

The trust system must support a 150× variation in trust dynamics across the 8 NEXUS domains:

| Domain | α_gain (std) | α_gain (agent, 0.5×) | α_loss | Ratio | Agent Days to L4 | Max Agent Autonomy |
|--------|-------------|---------------------|--------|-------|------------------|-------------------|
| Home | 0.15 | 0.075 | 0.2 | 1.3:1 | ~10 | L5 (full) |
| HVAC | 0.10 | 0.05 | 0.3 | 3:1 | ~20 | L5 (full) |
| Agriculture | 0.06 | 0.03 | 0.8 | 13:1 | ~50 | L4 (high) |
| Marine | 0.04 | 0.02 | 1.0 | 25:1 | ~90 | L4 (high) |
| Ground AV | 0.03 | 0.015 | 1.0 | 33:1 | ~110 | L3 (conditional) |
| Factory | 0.03 | 0.015 | 1.2 | 40:1 | ~160 | L3 (conditional) |
| Mining | 0.02 | 0.01 | 1.5 | 75:1 | ~240 | L2 (supervised) |
| Healthcare | 0.01 | 0.005 | 2.0 | 200:1 | ~400 | L1 (assisted) |

### 5.2 Maximum Autonomy Per Domain

**Why the variation exists**: The maximum autonomy level for agent-generated code varies by domain because the consequences of failure vary dramatically:

- **Home and HVAC (L5 achievable)**: A thermostat set 2° too high causes discomfort, not danger. The system can learn and adapt at full autonomy because the worst-case outcome is trivial.

- **Agriculture and Marine (L4 maximum)**: Crop damage or vessel collision has economic and environmental consequences. The system can operate at high autonomy but must remain monitorable — a human must be reachable within minutes.

- **Ground AV and Factory (L3 maximum)**: Vehicle collisions and factory injuries have safety consequences. The system can act semi-autonomously but a human must be reachable within 30 seconds. Agent-generated code never controls safety-rated functions in these domains.

- **Mining (L2 maximum)**: Explosions, asphyxiation, and cave-ins are life-threatening. Agent-generated code operates only under direct supervision. Every action is approved or rejected by a human operator.

- **Healthcare (L1 maximum)**: Patient harm or death is possible. Agent-generated code can only advise — it can never act autonomously. Human clinical engineering staff must approve every deployment.

### 5.3 Why Agent Code Has Stricter Limits

The stricter limits on agent-generated code are not arbitrary. They reflect three compounding factors:

1. **Residual unsafety**: Agent-generated code has a ~0.25% probability of being unsafe after validation (safety gate miss × A/B false positive). In domains where the consequence of that 0.25% is injury or death, the expected cost is too high.

2. **Accountability gap**: When human-authored code fails, there is a clear chain of responsibility (engineer → reviewer → QA → deployer). When agent-generated code fails, the accountability chain is murkier (agent → model → training data → prompt → validator). Regulatory frameworks (EU AI Act, IEC 62304) require clear accountability.

3. **Epistemic limitation**: The AI model that generates the bytecode has no physical intuition. It cannot "feel" that a 45° rudder deflection at 7 knots will cause excessive heel. It can only infer this from data — and the data may not cover the edge case that causes failure.

---

## 6. Trust Attack Vectors and Defenses

### 6.1 Event Flooding — Rapid Good Events to Inflate Trust

**Attack**: An agent generates a reflex that fires at maximum rate (e.g., 3600 times per hour) to produce a flood of `successful_action` events, inflating trust faster than the quality_cap allows.

**Defense**: The `quality_cap` parameter (default: 10) limits the number of good events per window that contribute to trust gain. Even if a reflex fires 3600 times per hour and each firing generates a `successful_action` event, only 10 count toward trust computation.

**Residual risk**: An agent could design a reflex that genuinely fires 10 times per window, each time performing a real (but trivially easy) action. This is an epistemically valid attack — the system IS performing correctly, just at a trivial level. Mitigation: the `min_events_for_gain` parameter can be increased to require higher-quality events (e.g., `successful_action_with_reserve` quality ≥ 0.8) for trust gain, and the autonomy level promotion criteria require sustained observation across hundreds of windows, not just high per-window event counts.

### 6.2 Severity Manipulation — Reporting Low-Severity Events

**Attack**: An agent classifies a genuine failure as a low-severity event (e.g., reporting a `safety_rule_violation` as an `anomaly_detected` with severity 0.2 instead of 0.7).

**Defense**: Event classification is **not controlled by the agent that generates reflexes**. Events are classified by the safety monitoring layer, which operates independently of the learning agent. The `safety_rule_violation` event is generated by the hardware safety tier (INA219 overcurrent, kill switch, MAX6818 watchdog) or by the software safety agent — neither of which the learning agent can influence.

**Residual risk**: An agent could design a reflex that avoids triggering the safety monitoring layer while still behaving unsafely. For example, a reflex that approaches obstacles to 4.5m (just above the 5.0m abort threshold) without violating any safety rule. Mitigation: the trust agent monitors for "near-miss" patterns (frequent proximity to safety thresholds) and can issue a trust penalty for patterns that indicate risk-seeking behavior.

### 6.3 Safe Behavior Exploitation — Doing Nothing to Avoid Penalties

**Attack**: An agent proposes a reflex that does nothing (e.g., a "heading hold" reflex that doesn't actually adjust the rudder). This reflex never causes bad events but also never causes high-quality good events. Trust slowly decays to t_floor (0.2, L1 Advisory) but never drops to 0.

**Defense**: The decay branch (Branch 3) will reduce trust toward t_floor over time. A do-nothing reflex will lose trust through inactivity within approximately t_floor / (alpha_decay × windows_per_day) ≈ 0.2 / (0.0001 × 24) ≈ 83 days. At t_floor, the reflex is limited to L1 (Advisory) — it can suggest but not act.

**Additional defense**: The trust agent tracks the ratio of `successful_action` (quality 0.7) to `successful_action_with_reserve` (quality 0.95). If an agent's reflexes consistently produce low-quality events, the trust agent can increase the effective `min_events_for_gain` threshold for that agent, requiring higher-quality evidence.

### 6.4 A/B Test Gaming

**Attack**: An agent designs an A/B test where the control reflex is intentionally degraded (e.g., a "heading hold" reflex with excessive PID gains that oscillate) to make the treatment reflex appear superior by comparison.

**Defense**: A/B test baselines are computed from **historical operation data**, not from a concurrently running control. The `baseline_metrics` in `ABTestConfig` are computed from the last N hours of the existing production reflex. The agent cannot influence historical data.

**Additional defense**: The A/B testing framework includes automatic rollback triggers: if the control condition (which is the existing production reflex) shows abnormal behavior during the test, the test is invalidated. If the treatment shows override rates > 5% or any zero-tolerance safety events, immediate rollback occurs.

### 6.5 Summary of Defenses

| Attack Vector | Primary Defense | Secondary Defense | Residual Risk |
|--------------|----------------|-------------------|---------------|
| Event flooding | quality_cap | min_events_for_gain, observation time requirements | Low — capped at 10 events/window |
| Severity manipulation | Independent event classification | Near-miss pattern detection | Medium — requires safety layer compromise |
| Safe behavior exploitation | Decay branch (Branch 3) | Quality ratio monitoring | Low — decays to L1 within ~83 days |
| A/B test gaming | Historical baselines | Rollback triggers, statistical tests | Low — baselines are immutable |
| Trust reset abuse | reset_grace_hours | Audit trail, operator notification | Very Low — 24h cooldown between resets |
| Code injection via fleet | Bytecode identity verification | RSA-3072 signatures | Very Low — cryptographic verification |

---

## 7. Formal Trust Properties

### 7.1 Fixed Points

The trust recurrence has three fixed points where T(t) = T(t-1):

**T = 0.0 (Absorbing boundary)**: At T=0, Branch 1 produces delta_T = α_gain × 1.0 × quality × (capped_n/quality_cap) > 0, so T will increase. T=0 is **not a stable fixed point** under Branch 1. However, under Branch 2 with a severity-1.0 event, T stays at 0 (since -α_loss × 0 × 1.0 × 1.0 = 0). After a full_reset or safety_incident, T=0 is the starting state, and the system must earn its way back.

**T = 1.0 (Saturation boundary)**: At T=1, Branch 1 produces delta_T = α_gain × 0 × ... = 0. Branch 2 produces delta_T = -α_loss × 1 × severity × n_penalty < 0 (for any bad event). Branch 3 produces delta_T = -α_decay × (1 - t_floor) < 0. T=1.0 is a **stable fixed point only under Branch 1** (with no bad events). Any perturbation (bad event or inactivity) will decrease trust from 1.0.

**T = t_floor (Decay floor)**: At T = t_floor = 0.2, Branch 3 produces delta_T = -α_decay × (0.2 - 0.2) = 0. T=t_floor is a **stable fixed point under Branch 3** (inactivity). The system will not decay below t_floor through inactivity alone. However, a bad event via Branch 2 can push T below t_floor (e.g., severity-1.0 event at T=0.2 produces delta_T = -0.05 × 0.2 × 1.0 = -0.01, yielding T = 0.19).

### 7.2 Equilibrium Under Mixed Events

When the system experiences a mix of good and bad events with fixed probabilities, the trust score reaches a stochastic equilibrium.

Let p_good = probability of a clean window (no bad events, ≥ min_events_for_gain good events), and p_bad = 1 - p_good.

At equilibrium, expected gain per window = expected loss per window:

```
p_good × α_gain × (1 - T_eq) × Q × (N / quality_cap) = p_bad × α_loss × T_eq × S × n_penalty
```

Solving for T_eq:

```
T_eq = p_good × α_gain × Q × (N / quality_cap) /
       (p_good × α_gain × Q × (N / quality_cap) + p_bad × α_loss × S × n_penalty)
```

**Example (Scenario 2 parameters)**: p_good = 0.95, Q = 0.7, N = 8, quality_cap = 10, p_bad = 0.05, S = 0.2, n_penalty = 1.0:

```
T_eq ≈ (0.95 × 0.002 × 0.7 × 0.8) / (0.95 × 0.002 × 0.7 × 0.8 + 0.05 × 0.05 × 0.2 × 1.0)
     ≈ 0.001064 / (0.001064 + 0.0005)
     ≈ 0.68
```

The simulated equilibrium (~0.84) is higher than the analytical estimate (~0.68) because the simulation includes streak bonuses and windows where N > quality_cap provides effective quality averaging.

**Key insight**: For any non-zero p_bad, the equilibrium T_eq is strictly less than 1.0. The system can never reach full autonomy if it experiences any bad events at all. This is mathematically guaranteed by the asymmetry between gain and loss.

### 7.3 Bounded Convergence Guarantees

**Theorem 1 (Monotonicity under Branch 1)**: If only Branch 1 applies (no bad events, sufficient good events), T(t) is strictly increasing and bounded above by 1.0. The sequence converges to 1.0.

*Proof*: delta_T = α_gain × (1 - T) × Q × (N/cap) > 0 for all T < 1.0. Since T(t+1) = T(t) + delta_T and delta_T > 0, the sequence is monotonically increasing. Since T(t+1) ≤ 1.0 (clamp), it is bounded above. By the monotone convergence theorem, it converges. The limit L satisfies delta_T = 0 at L, which implies (1-L) = 0, i.e., L = 1.0.

**Theorem 2 (Asymptotic convergence rate)**: Under Branch 1 with constant Q and N:

```
T(t) = 1 - (1 - T_0) × exp(-λ × t)
```

where λ = α_gain × Q × min(N, quality_cap) / quality_cap.

*Proof*: The recurrence T(t+1) = T(t) + α_gain × (1 - T(t)) × c (where c is the constant quality×cap factor) is a discrete-time exponential approach. Setting r(t) = 1 - T(t), we get r(t+1) = r(t) × (1 - α_gain × c), which gives r(t) = r(0) × (1 - α_gain × c)^t. For small α_gain × c, this approximates r(t) ≈ r(0) × exp(-α_gain × c × t), yielding T(t) ≈ 1 - (1 - T_0) × exp(-λ × t).

**Theorem 3 (Pessimistic recovery bound)**: After a single bad event at trust level T_bad with severity S:

```
T_recovery(target) ≈ (bad_drop) / α_gain × (1 / Q) × (cap / min(N, cap)) windows
```

where bad_drop = α_loss × T_bad × S × n_penalty. Recovery time scales linearly with the trust level at which the bad event occurred, meaning higher trust → longer recovery.

### 7.4 Time-to-Level Closed-Form Solutions

**Days to reach trust level T_target from T_0 under ideal conditions (all Branch 1)**:

```
n_windows = -ln((1 - T_target) / (1 - T_0)) / λ
n_days = ceil(n_windows / (24 / evaluation_window_hours))
```

where λ = α_gain × Q × min(N, quality_cap) / quality_cap.

**Pre-computed table (default parameters, Q=0.95, N=8)**:

| Target Level | T_min | Days from T=0 | Agent Days (0.5×) | Days from T=0.5 | Agent Days from T=0.5 |
|-------------|-------|---------------|-------------------|-----------------|---------------------|
| L1 | 0.20 | ~1 | ~2 | ~0 | ~0 |
| L2 | 0.40 | ~7 | ~14 | ~4 | ~8 |
| L3 | 0.60 | ~21 | ~42 | ~12 | ~24 |
| L4 | 0.80 | ~57 | ~114 | ~37 | ~74 |
| L5 | 0.95 | ~166 | ~332 | ~120 | ~240 |

**Agent interpretation**: An agent proposing a new autopilot reflex should plan for a minimum 114-day validation period before L4 trust is achieved (under ideal conditions with no bad events). In practice, with occasional minor bad events, this extends to 150-200 days. The agent should budget its development resources accordingly — a reflex that takes 2 weeks to develop and 4 months to validate is a 5-month investment.

**Note**: These times are for the trust score alone. The autonomy level promotion also requires minimum observation hours (168h for L3, 336h for L4, 720h for L5), minimum consecutive days (7 for L3, 14 for L4, 30 for L5), and minimum clean windows (100 for L3, 200 for L4, 500 for L5). The trust score threshold is necessary but not sufficient for promotion.

---

## Cross-References

- **Source Specification**: [[trust_score_algorithm_spec.md]] (NEXUS-SAFETY-TS-001)
- **Cross-Domain Applicability**: [[cross_domain_a2a_applicability.md]] (domains, 0.5× rule, max autonomy)
- **Learning Pipeline**: [[learning_pipeline_spec.md]] (how learning agents generate trust-affecting events)
- **Safety System**: [[safety_system_spec.md]] (four-tier safety, hardware trust layer)
- **Reflex Bytecode VM**: [[reflex_bytecode_vm_spec.md]] (TRUST_CHECK opcode, bytecode execution)
- **Wire Protocol**: [[wire_protocol_spec.md]] (FLEET_TRUST_QUERY/RESPONSE messages)
- **Safety Policy**: [[safety_policy.json]] (SR-001 through SR-010, domain-specific overrides)

---

*End of Trust System A2A-Native Specification*
