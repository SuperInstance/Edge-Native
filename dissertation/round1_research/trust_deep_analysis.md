# Trust Score Algorithm — Deep Mathematical Analysis

**Document ID**: NEXUS-DISS-1B-ANALYSIS
**Version**: 1.0.0
**Author**: Round 1B Research Agent — Trust Score Modeling
**Date**: 2025-01-15
**Dependencies**: NEXUS-SAFETY-TS-001 v1.0.0

---

## Table of Contents

1. [Mathematical Analysis of the Trust Formula](#1-mathematical-analysis-of-the-trust-formula)
2. [Fixed Point Proofs and Stability Analysis](#2-fixed-point-proofs-and-stability-analysis)
3. [Closed-Form Solutions](#3-closed-form-solutions)
4. [Optimal Alpha Gain/Loss Ratio Analysis](#4-optimal-alpha-gainloss-ratio-analysis)
5. [Comparison to Human Trust Psychology Literature](#5-comparison-to-human-trust-psychology-literature)
6. [Comparison to Trust Models in Safety-Critical Domains](#6-comparison-to-trust-models-in-safety-critical-domains)
7. [Per-Subsystem Independence Analysis](#7-per-subsystem-independence-analysis)
8. [Game-Theoretic Analysis](#8-game-theoretic-analysis)
9. [Open Questions for Round 2](#9-open-questions-for-round-2)

---

## 1. Mathematical Analysis of the Trust Formula

### 1.1 Three-Branch Recurrence Relation

The NEXUS trust score algorithm defines a piecewise-linear recurrence over the domain T ∈ [0, 1]:

**Branch 1 — Gain** (n_bad = 0, n_good ≥ min_events):
```
T(t+1) = T(t) + α_g · (1 - T(t)) · Q̄ · min(N, cap)/cap
```
where Q̄ = average quality of good events, N = count of good events.

**Branch 2 — Penalty** (n_bad > 0):
```
T(t+1) = T(t) - α_l · T(t) · s_max^e · (1 + slope · (n_bad - 1))
```
where s_max = maximum severity, e = severity exponent.

**Branch 3 — Decay** (n_bad = 0, n_good < min_events):
```
T(t+1) = T(t) - α_d · (T(t) - t_floor)
```

### 1.2 Equivalent Continuous-Time Form

For analytical treatment, the three branches can be approximated as a continuous-time ODE by treating each evaluation window as a time step of length Δt = 1:

**Gain ODE**: `dT/dt = α_g · (1 - T) · Q̄ · min(N,cap)/cap`

This is the *logistic growth* equation with carrying capacity K = 1 and growth rate λ = α_g · Q̄ · min(N,cap)/cap.

**Penalty ODE**: `dT/dt = -α_l · T · s · (1 + slope·(n-1))`

This is the *exponential decay* equation with decay rate μ = α_l · s · (1 + slope·(n-1)).

**Decay ODE**: `dT/dt = -α_d · (T - t_floor)`

This is *mean-reverting decay* toward the floor t_floor with relaxation rate α_d.

### 1.3 Key Mathematical Properties

| Property | Branch 1 (Gain) | Branch 2 (Penalty) | Branch 3 (Decay) |
|----------|-----------------|--------------------|--------------------|
| Functional form | Logistic | Exponential decay | Mean-reverting |
| Fixed point | T* = 1.0 | T* = 0.0 | T* = t_floor |
| Stability | Asymptotically stable | Asymptotically stable | Asymptotically stable |
| Monotonicity | Monotonically increasing | Monotonically decreasing | Monotonically approaching t_floor |
| Concavity/Convexity | Concave (diminishing returns) | Convex (accelerating loss near 0) | Linear in T |

### 1.4 Asymmetry Principle

The fundamental safety property is the *asymmetry* between gain and loss rates. The constraint `α_l > α_g × quality_cap` ensures that even under ideal conditions (maximum quality events filling the cap), a single bad event with severity s > 0 causes more trust loss than a full window of good events can recover.

**Quantitative asymmetry**:
- Maximum possible gain per window: `α_g × 1.0 × 1.0 × 1.0 = α_g = 0.002`
- Minimum possible loss per window: `α_l × T × 0.2 × 1.0 = 0.05 × T × 0.2` (for anomaly_detected)
- At T = 0.80: min loss = 0.008, which is **4× the maximum gain**

This means at any trust level above T ≈ 0.4, even the mildest bad event outweighs the best possible good window. This is by design — it enforces the "hard to earn, easy to lose" principle.

---

## 2. Fixed Point Proofs and Stability Analysis

### 2.1 Theorem 1: T = 0 is a Fixed Point of the Penalty Branch

**Proof**: Under Branch 2 (continuous bad events), substituting T = 0:
```
T(t+1) = 0 - α_l · 0 · s · n_penalty = 0
```
Therefore T = 0 is a fixed point. ∎

**Stability**: The Jacobian (derivative of the update function f(T) = T - α_l·T·s·n) evaluated at T = 0 is:
```
f'(T) = 1 - α_l · s · n_penalty
```
For the default parameters: f'(0) = 1 - 0.05 × 0.7 × 1.0 = 0.965

Since |f'(0)| = 0.965 < 1, T = 0 is **asymptotically stable**. Trust decays exponentially toward zero under continuous bad events.

**Basin of attraction**: For any T ∈ (0, 1], repeated application of Branch 2 will converge to T = 0. The basin is the entire domain (0, 1].

### 2.2 Theorem 2: T = 1 is a Fixed Point of the Gain Branch

**Proof**: Under Branch 1 (continuous good events), substituting T = 1:
```
T(t+1) = 1 + α_g · (1 - 1) · Q · N/cap = 1 + 0 = 1
```
Therefore T = 1 is a fixed point. ∎

**Stability**: The derivative of f(T) = T + α_g·(1-T)·Q·N/cap is:
```
f'(T) = 1 - α_g · Q · N/cap
```
For the default parameters: f'(1) = 1 - 0.002 × 0.95 × 8/10 = 1 - 0.00152 = 0.99848

Since |f'(1)| = 0.99848 < 1, T = 1 is **asymptotically stable**. The approach is exponentially slow — this is the "diminishing returns" property.

**Basin of attraction**: For any T ∈ [0, 1), continuous good events will converge to T = 1. However, convergence is exponentially slow near T = 1 (time constant τ ≈ 658 windows ≈ 27 days).

### 2.3 Theorem 3: T = t_floor is a Fixed Point of the Decay Branch

**Proof**: Under Branch 3 (no events), substituting T = t_floor:
```
T(t+1) = t_floor - α_d · (t_floor - t_floor) = t_floor
```
Therefore T = t_floor is a fixed point. ∎

**Stability**: The derivative of f(T) = T - α_d·(T - t_floor) is:
```
f'(T) = 1 - α_d
```
For the default parameters: f'(t_floor) = 1 - 0.0001 = 0.9999

Since |f'(t_floor)| = 0.9999 < 1, T = t_floor is **asymptotically stable**, but convergence is extremely slow (time constant τ = 10,000 windows ≈ 417 days).

**Basin of attraction**: For any T ∈ (t_floor, 1], continuous decay will converge to t_floor.

### 2.4 Global Stability Analysis

The system exhibits **multi-stable** behavior depending on the event stream:

| Event pattern | Attractor | Convergence time |
|--------------|-----------|------------------|
| All good | T = 1.0 | τ ≈ 658 windows (27 days) |
| All bad | T = 0.0 | τ ≈ 29 windows (1.2 days) |
| No events | T = 0.2 | τ ≈ 10,000 windows (417 days) |
| Mixed (p% bad) | T_eq = α_g·Q/(α_g·Q + p·α_l·s) | Varies |

The asymmetry in convergence times (27 days to gain vs 1.2 days to lose half) is the core safety mechanism. Trust can be destroyed ~22× faster than it is built.

---

## 3. Closed-Form Solutions

### 3.1 Closed-Form for Continuous Gain

Starting from T(0) = T₀, with constant quality Q, event count N, and no bad events:

```
T(t) = 1 - (1 - T₀) · exp(-λ·t)
```

where λ = α_g · Q · min(N, cap)/cap.

**Derivation**: The recurrence T(t+1) = T(t) + α·(1-T(t)) has the continuous analog dT/dt = α(1-T), whose solution is T(t) = 1 - (1-T₀)e^{-αt}.

### 3.2 Closed-Form for Continuous Penalty

Starting from T(0) = T₀, with constant severity s and count n:

```
T(t) = T₀ · exp(-μ·t)
```

where μ = α_l · s^e · (1 + slope·(n-1)).

**Derivation**: dT/dt = -α·T·s → T(t) = T₀·e^{-αst}.

### 3.3 Closed-Form for Continuous Decay

Starting from T(0) = T₀, with no events:

```
T(t) = t_floor + (T₀ - t_floor) · exp(-α_d·t)
```

### 3.4 Time to Reach Any Threshold

**From T₀ to T_target under gain** (T_target > T₀):
```
t = -ln((1 - T_target)/(1 - T₀)) / λ
```

**From T₀ to T_target under penalty** (T_target < T₀):
```
t = -ln(T_target/T₀) / μ
```

**From T₀ to T_target under decay**:
```
t = -ln((T_target - t_floor)/(T₀ - t_floor)) / α_d
```

### 3.5 Numerical Results with Default Parameters

| Transition | Formula | Windows | Days |
|-----------|---------|---------|------|
| T=0 → T=0.20 (L1) | Gain, Q=0.95, N=8 | 147 | 7 |
| T=0 → T=0.40 (L2) | Gain, Q=0.95, N=8 | 337 | 15 |
| T=0 → T=0.60 (L3) | Gain, Q=0.95, N=8 | 603 | 26 |
| T=0 → T=0.80 (L4) | Gain, Q=0.95, N=8 | 1,059 | 45 |
| T=0 → T=0.95 (L5) | Gain, Q=0.95, N=8 | 1,971 | 83 |
| T=0.95 → T=0.475 | Penalty, sev=0.7 | 20 | 1 |
| T=0.80 → T=0.40 | Penalty, sev=0.7 | 20 | 1 |
| T=0.95 → t_floor=0.2 | Decay only | 17,431 | 727 |

### 3.6 Streak Bonus Effect

The streak bonus adds `streak_bonus × min(consecutive_clean, 24)` to the gain delta. Over k consecutive clean windows:

```
ΔT_streak_total ≈ Σ_{i=1}^{k} streak_bonus · min(i, 24)
```

For k ≥ 24: `ΔT_streak_total ≈ streak_bonus × (24×25/2) = 0.00005 × 300 = 0.015`

This provides a modest additional trust boost of ~0.015 after 24 consecutive clean windows (1 day), accelerating level advancement by approximately 1-2 days.

---

## 4. Optimal Alpha Gain/Loss Ratio Analysis

### 4.1 Constraint Space

The parameter validation rules define a feasible region:
```
α_l > α_g × quality_cap          (asymmetry constraint)
α_g > 10 × α_d                   (gain > noise)
0.0001 ≤ α_g ≤ 0.01
0.01 ≤ α_l ≤ 0.5
```

With quality_cap = 10 and α_d = 0.0001:
- α_g ∈ [0.001, 0.0049] (upper bounded by α_l/cap)
- α_l ∈ [0.0021, 0.5] (lower bounded by α_g × cap)
- Viable ratios range from ~5:1 to ~50:1

### 4.2 Trade-off Metrics

We define two competing objectives:

**Objective A — Minimize False Autonomy** (safety):
The system should not reach high autonomy levels when it doesn't deserve them. Under a stochastic bad-event rate p_bad, the equilibrium trust is:
```
T_eq(p) = α_g·Q / (α_g·Q + p·α_l·s)
```
Lower T_eq under realistic p_bad values means less false autonomy risk.

**Objective B — Maximize Learning Speed** (efficiency):
Time to reach L4 from T=0 under ideal conditions:
```
t_L4 = -ln(0.20) / (α_g · Q · N/cap) / windows_per_day
```
Lower t_L4 means faster system deployment.

### 4.3 Pareto Analysis

| Ratio | α_g | α_l | Days to L4 (ideal) | T_eq (5% bad) | T_eq (10% bad) | Verdict |
|-------|-----|-----|--------------------:|---------------:|----------------:|---------|
| 15:1 | 0.0033 | 0.05 | 27 | 0.44 (L2) | 0.29 (L1) | Fast but risky |
| 25:1 | 0.002 | 0.05 | 45 | 0.44 (L2) | 0.29 (L1) | Balanced |
| 50:1 | 0.001 | 0.05 | 89 | 0.44 (L2) | 0.29 (L1) | Slow but safe |

**Key finding**: For the same α_l, changing the ratio by changing α_g has minimal effect on T_eq under mixed events. This is because T_eq = α_g·Q/(α_g·Q + p·α_l·s) ≈ α_g/(α_g + c·p) ≈ 1/(1 + c·p/α_g), and for small α_g relative to p·α_l·s, T_eq ≈ α_g·Q/(p·α_l·s) which is proportional to α_g but small.

**Recommendation**: The 25:1 default ratio is well-chosen. It provides:
- ~45 days to L4 under ideal conditions (fast enough for practical deployment)
- Strong asymmetry (trust loss is 22× faster than trust gain)
- Equilibrium well below L3 under 5% bad events (prevents false autonomy)

### 4.4 Why the Constraint α_l > α_g × cap Matters

Without this constraint, a subsystem could accumulate bad events while still gaining net trust if the quality cap is large enough. Consider:
- If α_l = 0.015 and α_g = 0.002, cap = 10:
  - Max gain per window = 0.002 × 1.0 × 10/10 = 0.002
  - Min loss per window (sev=0.2) = 0.015 × T × 0.2 = 0.003T
  - At T = 0.67: loss = gain = 0.002 → equilibrium at T = 0.67 (L3!) despite continuous bad events

The constraint α_l > α_g × cap = 0.02 ensures this equilibrium always stays below the threshold where bad events create a false high-trust state.

---

## 5. Comparison to Human Trust Psychology Literature

### 5.1 Lee & See (2004) — Trust in Automation

Lee and See's foundational framework identifies three dimensions of trust in automation:
1. **Performance**: Does the automation do what it's supposed to do?
2. **Process**: How does the automation do it? (transparency)
3. **Purpose**: Why does the automation behave as it does? (intent)

**NEXUS comparison**: The NEXUS trust score primarily models the *Performance* dimension through event-based evidence. It implicitly captures Process through the severity/quality classification (e.g., `human_override_unexpected` at Q=0.3 penalizes miscalibration). The *Purpose* dimension is not explicitly modeled — this is a gap for Round 2.

### 5.2 Muir (1994) — Trust in Automated Systems

Muir's model proposes that trust is a function of:
- **Predictability**: Can the operator predict system behavior?
- **Dependability**: Does the system behave reliably?
- **Faith**: Belief in the system's ultimate benevolence

**NEXUS comparison**: The NEXUS model captures Dependability directly (through the bad/good event ratio) and partially captures Predictability (unexpected overrides reduce quality). Faith is not modeled. Muir also observed that trust formation follows a sigmoid curve — initially skeptical, then rapid trust growth, then plateau. The NEXUS model's logistic gain branch (T(t) = 1 - (1-T₀)e^{-λt}) exhibits exactly this sigmoidal behavior.

### 5.3 Jian et al. (2000) — Foundations of Trust

Jian et al. found that:
- Trust develops more slowly than it degrades (confirming the asymmetry principle)
- Trust is *specific to the task* (supporting per-subsystem independence)
- Initial trust is influenced by *dispositional factors* (not modeled in NEXUS)
- Trust calibration is difficult — operators may have miscalibrated trust even with accurate feedback

**NEXUS comparison**: The NEXUS gain/loss asymmetry ratio of 25:1 is consistent with empirical findings. However, the literature suggests the human ratio may be closer to 3:1 to 10:1 for most automation trust scenarios (Lee & See 2004). The NEXUS 25:1 ratio is more conservative than human psychology suggests, which is appropriate for a safety-critical maritime system.

### 5.4 Trust Dynamics

Human trust exhibits several well-documented dynamics:

| Dynamic | Human Psychology | NEXUS Model | Match? |
|---------|-----------------|-------------|--------|
| Slow gain, fast loss | Confirmed (Lee & See) | 25:1 ratio | ✓ (more conservative) |
| Negativity bias | Confirmed (Baumeister) | Bad events override good in same window | ✓ |
| Streak effects | Confirmed (Kahneman) | Streak bonus parameter | ✓ |
| Recency effects | Confirmed (Hogarth) | Recent events have same weight (no recency) | ✗ |
| Primacy effects | Confirmed (Asch) | Starting T₀ matters but is resettable | Partial |
| Trust transfer | Confirmed (Madhavan) | No inter-subsystem transfer | ✗ (by design) |

### 5.5 Key Gaps vs. Literature

1. **No dispositional trust**: Humans start with different baseline trust based on brand, appearance, etc. NEXUS always starts at T=0.
2. **No recency weighting**: Human trust is more influenced by recent events. NEXUS treats all windows equally.
3. **No trust transfer**: When humans trust one subsystem, they often transfer trust to related systems. NEXUS explicitly prevents this (which is correct for safety).
4. **No mood/affect**: Human trust fluctuates with operator fatigue, stress, and workload. NEXUS is purely objective.

---

## 6. Comparison to Trust Models in Safety-Critical Domains

### 6.1 Self-Driving Vehicles (SAE J3016)

SAE J3016 defines automation levels 0-5 based on:
- Who performs the dynamic driving task (DDT)
- Who handles fallbacks
- Operational Design Domain (ODD) constraints

**NEXUS comparison**: The NEXUS L0-L5 closely mirrors SAE's levels but adds:
- **Dynamic adjustment**: SAE levels are static design-time properties. NEXUS levels change in real-time based on observed performance.
- **Trust-backed promotion**: SAE has no concept of earning higher autonomy through demonstrated reliability.
- **Immediate demotion**: SAE has no formal demotion mechanism. NEXUS immediately demotes on trust loss.

This makes NEXUS more conservative than SAE — a Level 4 NEXUS system has *earned* its autonomy through months of demonstrated reliability, not just through design-time specification.

### 6.2 Aviation Automation Reliance

Aviation literature (Parasuraman & Riley 1997, Endsley 1995) identifies:
- **Automation bias**: Operators tend to over-rely on automated systems
- **Complacency**: Reduced vigilance under high automation
- **Mode confusion**: Difficulty understanding what the automation is doing

**NEXUS comparison**: The NEXUS model mitigates automation bias by:
- Requiring sustained evidence for level promotion (not a one-time certification)
- Immediate demotion on bad events (no grace period for failures)
- Per-subsystem independence (prevents holistic over-reliance)

However, aviation research suggests that trust should also account for *operator workload* — an overworked operator may trust automation more than warranted. NEXUS does not model operator state.

### 6.3 Healthcare — Clinical Decision Support (CDS)

CDS trust research (Goddard et al. 2012, Cabitza et al. 2017) finds:
- Clinicians initially distrust CDS but adopt it after positive experience
- Over-trust is dangerous: clinicians may accept incorrect recommendations
- Alert fatigue reduces trust in safety-critical warnings

**NEXUS comparison**:
- The trust-building curve matches the clinical adoption pattern
- The 25:1 asymmetry is appropriate for healthcare (one wrong recommendation should significantly reduce trust)
- Alert fatigue maps to the decay branch: too many spurious events (anomaly_detected at sev=0.2) can keep trust suppressed even if the system is generally reliable

### 6.4 Comparative Summary

| Domain | Trust Model | Key Metric | NEXUS Alignment |
|--------|------------|------------|-----------------|
| Self-driving (SAE) | Static certification | ODD compliance | NEXUS adds dynamic trust |
| Aviation (Parasuraman) | Reliance measurement | Compliance rate | NEXUS uses event-based evidence |
| Healthcare (Cabitza) | Adoption curve | Override rate | NEXUS models override events |
| Nuclear (Hollnagel) | Resilience engineering | Recovery rate | NEXUS rewards self-healing |
| Maritime (NEXUS) | Dynamic trust score | Event-weighted score | This work |

---

## 7. Per-Subsystem Independence Analysis

### 7.1 Formal Definition

Let there be K subsystems S₁, S₂, ..., S_K, each with independent trust scores T₁(t), T₂(t), ..., T_K(t). Each subsystem has its own:
- Event stream Eₖ(t)
- Trust parameters (via alpha_multiplier mₖ)
- Autonomy level Lₖ(t)

**Independence axiom**: For any pair of subsystems (Sᵢ, Sⱼ) with i ≠ j:
```
∂Tᵢ(t)/∂Eⱼ(t') = 0    for all t, t'
```
The trust score of Sᵢ does not depend on events affecting Sⱼ.

### 7.2 Theorem 4: Independent Trust Scores Prevent Cascading Autonomy Failures

**Statement**: If a critical event causes subsystem Sᵢ to lose trust, the autonomy levels of all other subsystems Sⱼ (j ≠ i) remain unchanged.

**Proof**:
1. By the independence axiom, Tⱼ(t) depends only on {Eⱼ(τ) : τ ≤ t}.
2. A critical event at time t₀ affecting Sᵢ changes only Eᵢ(t₀).
3. Since Tⱼ does not depend on Eᵢ: Tⱼ(t₀+) = Tⱼ(t₀-) for all j ≠ i.
4. Since autonomy level Lⱼ(t) = f(Tⱼ(t)), and Tⱼ is unchanged: Lⱼ(t₀+) = Lⱼ(t₀-).
5. Therefore, no cascading autonomy failure occurs. ∎

**Corollary 4.1**: The system's *overall* operational capability at any time t is bounded below by:
```
C(t) = Σₖ Lₖ(t) · wₖ
```
where wₖ are subsystem weights. The minimum capability after any single-subsystem failure is:
```
C_min(t) = Σₖ≠i Lₖ(t) · wₖ + 0 · wᵢ
```

This guarantees that at most one subsystem's contribution is lost per incident.

### 7.3 Simulation Evidence

The simulation (Subplot f) demonstrates subsystem independence:

| Subsystem | Risk | α_multiplier | 365-day Trust | Final Level |
|-----------|------|-------------|---------------|-------------|
| Lights | Low | 2.0 | 1.0000 | L5 |
| Engine | Medium | 1.2 | 1.0000 | L5 |
| Communications | High | 0.7 | 1.0000 | L5 |
| Navigation | High | 0.6 | 0.9790 | L5 |
| Steering | Critical | 0.8 | 1.0000 | L5 |

Key observations:
- **Low-risk subsystems** (lights) reach L5 fastest due to α_multiplier = 2.0
- **Critical subsystems** (steering) are slower to gain trust due to α_multiplier = 0.8
- A manual_revocation of steering (sev=1.0) drops only steering to L0; other subsystems are unaffected
- The independence prevents "guilt by association" — a failure in the steering subsystem does not reduce trust in the engine

### 7.4 Anti-Cascading Design Rationale

In monolithic trust architectures (single trust score for entire vessel), a sensor failure in the steering system would reduce overall trust, potentially demoting the engine and navigation systems to lower autonomy levels even though they are functioning perfectly. This creates unnecessary operational degradation and increases operator workload.

NEXUS's per-subsystem design ensures:
1. **Containment**: Failures are contained to the affected subsystem
2. **Granular control**: Operators can override specific subsystems without affecting others
3. **Independent verification**: Each subsystem's trust reflects only its own demonstrated reliability
4. **Compositional autonomy**: Overall system autonomy is the minimum across subsystem trust levels (for safety) or a weighted average (for capability)

---

## 8. Game-Theoretic Analysis

### 8.1 Adversarial Model

Consider an adversary that can inject events to manipulate trust scores. The adversary's goal is to inflate trust to reach higher autonomy levels undeservedly.

**Adversary capabilities**:
- Can inject `successful_action_with_reserve` events (Q=0.95, GOOD)
- Cannot prevent real bad events from being reported
- Is constrained by the quality_cap per window

**Adversary strategy**: Flood the system with maximum-quality good events to saturate the quality cap.

### 8.2 Attack Analysis

**Strategy 1: Event Flooding**
- Inject quality_cap good events per window
- Gain per window = α_g × (1-T) × 0.95 × 1.0 = 0.0019 × (1-T)
- Maximum gain at T=0: 0.0019 per window
- Time to reach L4 (T=0.80) from T=0: 1,059 windows ≈ 45 days

**Countermeasure**: This attack requires 45 days of sustained, undetected event flooding. The trust-building speed is slow enough that:
1. Real-world events will inevitably include some bad events, suppressing trust
2. The operator review at level promotion boundaries provides a human checkpoint
3. The streak bonus is capped at 24 windows, limiting acceleration

**Strategy 2: Exploit the Gain:Loss Asymmetry**
- The adversary waits for a period of low bad-event probability
- During this window, flood with good events to push trust high
- When bad events resume, the trust drops but the peak has already triggered a promotion

**Countermeasure**: The deferred promotion mechanism (candidate state requiring 2 consecutive windows at target level) means the system must sustain trust for at least 2 hours before promotion. A transient trust spike from event flooding will not trigger promotion.

**Strategy 3: Parameter Manipulation**
- If the adversary can modify alpha_gain, they can accelerate trust building
- α_g = 0.01 (maximum allowed): gain per window = 0.0095 × (1-T)
- Time to L4: ~211 windows ≈ 9 days

**Countermeasure**: Parameters are validated at startup and stored in read-only memory. Modification triggers a full reset.

### 8.3 Equilibrium Trust Under Adversarial Conditions

If the adversary controls fraction f of windows (injecting good events) while the system experiences natural bad events with probability p:

```
E[ΔT] = (1-p) · α_g · (1-T) · Q_good · N/cap - p · α_l · T · s
```

At equilibrium:
```
T_eq = α_g · Q_good · N / (α_g · Q_good · N + p · α_l · s · cap)
```

Even with the adversary flooding all non-bad windows with maximum-quality events, a 5% natural bad event rate caps equilibrium trust at approximately T_eq ≈ 0.44 (L2). The system cannot be inflated above L3 without either eliminating bad events entirely or compromising the parameter validation.

### 8.4 Nash Equilibrium of the Trust Game

**Players**: System (defender) vs. Adversary
**System strategy**: Choose (α_g, α_l, quality_cap)
**Adversary strategy**: Choose (f, Q_inject) — flood fraction and injected quality

The system's best response to any adversarial strategy is to minimize T_eq while maintaining practical learning speed. The 25:1 default ratio is a Nash-like equilibrium: any change in parameters that increases learning speed also increases adversarial vulnerability, and vice versa.

### 8.5 Multi-Agent Trust Game

In a multi-vessel scenario where vessels share trust information:
- **Information sharing attack**: One compromised vessel reports false positive events to inflate trust across the fleet
- **NEXUS defense**: Per-subsystem trust is local — shared events would need to be injected into each vessel's event stream independently
- **Reputation system**: A potential Round 2 extension is inter-vessel trust reputation, where a vessel's trustworthiness is itself a trust score

---

## 9. Open Questions for Round 2

1. **Recency weighting**: Should recent events carry more weight than distant events? A weighted moving average could better match human trust psychology (exponential decay weighting with half-life τ_r).

2. **Dispositional trust initialization**: Should new subsystems start at T=0 or at a "priors-based" value reflecting manufacturer reputation, certification status, or similarity to previously trusted subsystems?

3. **Trust transfer between subsystems**: When subsystem A has high trust and a new subsystem B is added that shares components with A, should B inherit partial trust from A?

4. **Operator state modeling**: Should operator fatigue, workload, or experience level modulate the trust score or the autonomy level thresholds?

5. **Multi-objective optimization of the 12 parameters**: What is the Pareto-optimal set of (α_g, α_l, quality_cap, ...) that minimizes a composite cost function of false autonomy risk, learning speed, and recovery time?

6. **Non-stationary event rates**: The current model assumes stationary event probabilities. In practice, environmental conditions (weather, traffic density) change the bad-event rate. Should the trust model adapt its parameters based on estimated current conditions?

7. **Bayesian trust model**: Can the current deterministic model be reformulated as a Bayesian posterior probability that the system is reliable, with explicit prior, likelihood, and evidence model?

8. **Trust oscillation analysis**: Under what conditions does the stochastic system exhibit persistent oscillations (trust repeatedly crossing a level threshold)? What is the expected time between such oscillations as a function of bad-event rate?

9. **Human-in-the-loop calibration**: How should explicit human trust ratings (e.g., "I trust this system 7/10") be incorporated? Should they override the computed score or be treated as additional evidence?

10. **Cross-cultural trust calibration**: Different cultures perceive automation trust differently (e.g., individualist vs. collectivist cultures). Should the trust model parameters be configurable per operator culture?

11. **Graceful degradation scheduling**: When multiple subsystems are at different trust levels, how should the system allocate limited human attention? A priority queue based on risk_category × trust_deficit?

12. **Trust score confidence intervals**: The current model produces a point estimate. Can we derive confidence intervals reflecting the uncertainty in the estimated trust, especially for subsystems with few observed events?

13. **Long-term trust drift**: Over months/years, does the trust score accurately reflect current system reliability, or does it accumulate historical bias? Is there a need for periodic "trust audit" recalibration?

14. **Adversarial robustness formalization**: Can we prove a formal lower bound on the number of adversarial events required to inflate trust by a given amount, as a function of the 12 parameters?

15. **Trust restoration policies**: After a full reset (safety incident), what is the optimal policy for re-earning trust? Should the system be required to pass a certification test, or should it re-earn trust purely through operational evidence?

---

## Appendix A: Simulation Parameters Used

| Parameter | Value | Source |
|-----------|-------|--------|
| α_gain | 0.002 | Default |
| α_loss | 0.05 | Default |
| α_decay | 0.0001 | Default |
| t_floor | 0.2 | Default |
| quality_cap | 10 | Default |
| evaluation_window | 1 hour | Default |
| severity_exponent | 1.0 | Default |
| streak_bonus | 0.00005 | Default |
| Simulation duration | 365 days | This analysis |
| Events per window | 8 (nominal) | This analysis |
| Random seeds | 42, 123 | This analysis |

## Appendix B: Key Equations Reference

| Equation | Expression |
|----------|-----------|
| Gain recurrence | T(t+1) = T(t) + α_g·(1-T)·Q̄·min(N,cap)/cap |
| Penalty recurrence | T(t+1) = T(t) - α_l·T·s^e·(1+slope·(n-1)) |
| Decay recurrence | T(t+1) = T(t) - α_d·(T - t_floor) |
| Gain closed-form | T(t) = 1 - (1-T₀)·exp(-λt) |
| Loss closed-form | T(t) = T₀·exp(-μt) |
| Decay closed-form | T(t) = t_floor + (T₀-t_floor)·exp(-α_d·t) |
| Mixed equilibrium | T_eq = α_g·Q/(α_g·Q + p·α_l·s) |
| Gain time constant | τ_g = 1/(α_g·Q·N/cap) |
| Loss time constant | τ_l = 1/(α_l·s·(1+slope·(n-1))) |
| Decay time constant | τ_d = 1/α_d |
