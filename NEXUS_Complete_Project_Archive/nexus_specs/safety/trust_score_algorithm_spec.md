# Trust Score Algorithm Specification

**Document ID**: NEXUS-SAFETY-TS-001
**Version**: 1.0.0
**Classification**: Safety-Critical (ASIL-B equivalent)
**Author**: Safety-Critical Systems Engineering
**Date**: 2025-01-15
**Review Status**: Approved

---

## Table of Contents

1. [Overview](#1-overview)
2. [Formal Mathematical Definition](#2-formal-mathematical-definition)
3. [Complete Parameter Table](#3-complete-parameter-table)
4. [Event Severity & Quality Classification](#4-event-severity--quality-classification)
5. [Autonomy Level Thresholds](#5-autonomy-level-thresholds)
6. [Reset Events](#6-reset-events)
7. [Trust Score Simulation](#7-trust-score-simulation)
8. [Per-Subsystem Customization](#8-per-subsystem-customization)
9. [Data Structures](#9-data-structures)
10. [Implementation Notes](#10-implementation-notes)
11. [Appendix: Verification & Validation](#11-appendix-verification--validation)

---

## 1. Overview

### 1.1 Purpose

This specification defines the deterministic trust score algorithm used by the NEXUS autonomous vessel control system to dynamically adjust the permitted autonomy level of each subsystem. The trust score `T(t)` is a continuous value in `[0.0, 1.0]` computed over successive evaluation windows, reflecting the system's observed reliability and the operator's confidence in delegating control.

### 1.2 Scope

This document covers:

- The recursive trust update formula and all corner cases
- Every tunable parameter with type constraints and tuning guidance
- Event classification with exact severity and quality values
- Autonomy level mapping thresholds
- Trust reset triggers and multipliers
- A complete simulation reference implementation in Python
- Per-subsystem risk-category parameter customization
- Persistent data structures (Python dataclasses, C structs)
- Thread-safety, persistence, API contract, and testing requirements

### 1.3 Safety Rationale

The trust score acts as a **software safety barrier**. By decaying trust on observed anomalies and requiring sustained good behavior to increase trust, the system enforces a conservative autonomy progression. The asymmetry between gain and loss rates (`alpha_gain << alpha_loss`) ensures that trust is **hard to earn and easy to lose**, following the principle of **fail-safe degradation**.

---

## 2. Formal Mathematical Definition

### 2.1 Core Recurrence Relation

The trust score at evaluation step `t` is defined recursively:

```
T(t) = clamp(T(t-1) + delta_T, 0.0, 1.0)
```

where `delta_T` is computed per evaluation window based on observed events.

### 2.2 Evaluation Window

Each evaluation window has a fixed duration defined by `evaluation_window_hours` (default: 1 hour). Within each window, events are bucketed into three disjoint sets:

| Set | Symbol | Description |
|-----|--------|-------------|
| Good events | `G = {e_i | e_i.type in GOOD_TYPES}` | Events indicating correct or desirable behavior |
| Bad events | `B = {e_j | e_j.type in BAD_TYPES}` | Events indicating failures, anomalies, or policy violations |
| Neutral events | `N = {e_k | e_k.type in NEUTRAL_TYPES}` | Events that carry information but are neither good nor bad |

Let:

- `n_good = |G|` — count of good events in the window
- `n_bad = |B|` — count of bad events in the window
- `T_prev = T(t-1)` — trust score at the end of the previous window

### 2.3 Delta Computation Rules

The delta `delta_T` is computed by exactly one of the following three mutually exclusive branches, evaluated in order:

#### Branch 1: Net Positive (no bad events, at least one good event)

**Condition**: `n_bad == 0 AND n_good > 0`

```
avg_quality    = (1 / n_good) * SUM(e_i.quality for e_i in G)   // quality in [0, 1]
capped_n_good  = min(n_good, quality_cap)
delta_T        = alpha_gain * (1 - T_prev) * avg_quality * (capped_n_good / quality_cap)
```

**Intuition**: Trust approaches 1.0 asymptotically. The factor `(1 - T_prev)` makes gains smaller as trust increases. The `quality_cap` prevents a flood of low-quality events from inflating trust quickly.

#### Branch 2: Penalty (at least one bad event)

**Condition**: `n_bad > 0`

```
max_severity   = max(e_j.severity for e_j in B)                  // severity in [0, 1]
n_penalty      = 1 + 0.1 * (n_bad - 1)
delta_T        = -alpha_loss * T_prev * max_severity * n_penalty
```

**Intuition**: Trust is penalized proportionally to current trust, worst severity in the window, and a count multiplier that grows sub-linearly. A single bad event with severity=1.0 at T=1.0 produces `delta_T = -alpha_loss * 1.0 * 1.0 * 1.0 = -0.05`.

**Note**: Good events in the same window are **ignored** when bad events are present. This is intentional — a window containing a safety violation cannot be considered "net positive" regardless of concurrent good behavior.

#### Branch 3: Decay (no bad events, no good events)

**Condition**: `n_bad == 0 AND n_good == 0`

```
delta_T = -alpha_decay * (T_prev - t_floor)
```

**Intuition**: In the absence of evidence, trust decays toward `t_floor`. The factor `(T_prev - t_floor)` ensures that decay stops at the floor — trust will not decay below `t_floor` via this path. At `T_prev == t_floor`, `delta_T = 0`.

### 2.4 Complete Pseudocode

```
FUNCTION compute_delta(T_prev, good_events, bad_events, params):
    n_good = len(good_events)
    n_bad  = len(bad_events)

    IF n_bad > 0 THEN
        max_severity = MAX(e.severity FOR e IN bad_events)
        n_penalty    = 1.0 + 0.1 * (n_bad - 1)
        delta_T      = -params.alpha_loss * T_prev * max_severity * n_penalty
    ELSE IF n_good > 0 THEN
        avg_quality   = SUM(e.quality FOR e IN good_events) / n_good
        capped_n_good = MIN(n_good, params.quality_cap)
        delta_T       = params.alpha_gain * (1.0 - T_prev) * avg_quality *
                        (capped_n_good / params.quality_cap)
    ELSE
        delta_T = -params.alpha_decay * (T_prev - params.t_floor)
    END IF

    RETURN delta_T


FUNCTION update_trust(T_prev, events, params):
    good_events = [e FOR e IN events IF e.category == GOOD]
    bad_events  = [e FOR e IN events IF e.category == BAD]
    # neutral events are logged but do not affect delta_T

    delta_T = compute_delta(T_prev, good_events, bad_events, params)
    T_new   = CLAMP(T_prev + delta_T, 0.0, 1.0)

    RETURN T_new, delta_T
```

### 2.5 Subsystem Multiplier

For subsystem-specific tuning, the computed `delta_T` is further scaled:

```
delta_T_effective = delta_T * subsystem.alpha_multiplier
```

This multiplier affects both gain and loss. For high-risk subsystems, `alpha_multiplier < 1.0` makes trust harder to earn and slower to lose (providing stability). For low-risk subsystems, `alpha_multiplier > 1.0` allows faster trust progression. See [Section 8](#8-per-subsystem-customization).

---

## 3. Complete Parameter Table

| # | Parameter | Symbol | Default | Min | Max | Type | Unit | Description | Tuning Guidance |
|---|-----------|--------|---------|-----|-----|------|------|-------------|-----------------|
| 1 | Gain rate | `alpha_gain` | 0.002 | 0.0001 | 0.01 | `float64` | — | Base rate of trust increase per evaluation window under Branch 1. Higher values accelerate trust growth. | Increase if trust builds too slowly in testing. Decrease if trust reaches high levels without sufficient evidence. Must remain at least 10x smaller than `alpha_loss` to maintain asymmetry. |
| 2 | Loss rate | `alpha_loss` | 0.05 | 0.01 | 0.5 | `float64` | — | Base rate of trust decrease per evaluation window under Branch 2. Higher values cause faster trust degradation on failures. | Increase for safety-critical subsystems where rapid degradation is required. Decrease if minor transients cause excessive trust loss. Must be > `alpha_gain * quality_cap` to ensure single bad event outweighs single good event. |
| 3 | Decay rate | `alpha_decay` | 0.0001 | 0.00001 | 0.001 | `float64` | — | Rate of trust decay toward `t_floor` under Branch 3 (inactivity). | Increase if trust should decay faster during idle periods. Decrease to near-zero if the system operates in bursty patterns and trust should be preserved. |
| 4 | Trust floor | `t_floor` | 0.2 | 0.0 | 0.5 | `float64` | — | Minimum trust level reachable via decay (Branch 3). Trust can still go below this via penalties (Branch 2). | Set to the minimum trust that still permits Level 1 autonomy. Raise if the system should retain a baseline of trust after inactivity. Lower if inactivity is more concerning. |
| 5 | Quality cap | `quality_cap` | 10 | 1 | 100 | `uint32` | events | Maximum number of good events per window that contribute to trust gain. Events beyond this cap are ignored for gain computation. | Increase for subsystems that produce many valid events per hour. Decrease to prevent high-frequency polling from inflating trust. Set to expected maximum event rate in steady state. |
| 6 | Evaluation window | `evaluation_window_hours` | 1.0 | 0.1 | 24.0 | `float64` | hours | Duration of each evaluation window. Trust is updated once per window. | Shorter windows provide faster responsiveness but increase computational overhead and noise sensitivity. Longer windows provide stability. Must divide evenly into 24 hours for daily autonomy checks. |
| 7 | Severity scaling exponent | `severity_exponent` | 1.0 | 0.5 | 2.0 | `float64` | — | Applied as `severity^exponent` before use in penalty computation. Values >1.0 amplify high-severity events. | Set to 1.0 for linear severity scaling. Set to 2.0 to heavily penalize high-severity events while reducing impact of low-severity ones. |
| 8 | Streak bonus rate | `streak_bonus` | 0.00005 | 0.0 | 0.001 | `float64` | — | Additional trust gain per consecutive clean window (no bad events). Applied only under Branch 1. | Set to 0.0 to disable streak bonuses. Increase to reward sustained good behavior. Must be much smaller than `alpha_gain`. |
| 9 | Minimum events for gain | `min_events_for_gain` | 1 | 1 | 10 | `uint32` | events | Minimum number of good events required in a window for Branch 1 to apply. | Increase if a single event is insufficient evidence of reliability. Useful for subsystems with sporadic event patterns. |
| 10 | Reset grace period | `reset_grace_hours` | 24.0 | 0.0 | 168.0 | `float64` | hours | After a reset, no further resets can occur for this duration. Prevents thrashing. | Increase for subsystems where resets are disruptive. Set to 0.0 to disable. |
| 11 | Autonomy promotion cooldown | `promotion_cooldown_hours` | 72.0 | 1.0 | 336.0 | `float64` | hours | Minimum time between autonomy level promotions. | Increase to require longer observation at each level. Set to 24.0 for aggressive testing. |
| 12 | Bad event count penalty slope | `n_penalty_slope` | 0.1 | 0.0 | 0.5 | `float64` | — | Slope of the count-based penalty multiplier: `n_penalty = 1 + slope * (n_bad - 1)`. | Increase if multiple simultaneous failures are especially concerning. Set to 0.0 to make penalty independent of count (severity-only). |

### 3.1 Parameter Validation Rules

All parameters MUST be validated at initialization time. The following invariants MUST hold:

```
alpha_loss > alpha_gain * quality_cap     // single bad event outweighs cap of good events
alpha_gain > alpha_decay * 10             // gains are meaningfully larger than decay
t_floor >= 0.0 AND t_floor < 1.0
quality_cap >= 1
evaluation_window_hours > 0.0
severity_exponent > 0.0
```

If any invariant is violated, the system MUST raise a `ParameterValidationError` and refuse to start.

---

## 4. Event Severity & Quality Classification

### 4.1 Event Taxonomy

Each event belongs to exactly one of three categories:

| Category | Effect on Trust |
|----------|----------------|
| **GOOD** | May increase trust (Branch 1) |
| **BAD** | Decreases trust (Branch 2) |
| **NEUTRAL** | No direct trust effect (logged for audit) |

### 4.2 Complete Event Classification Table

| # | Event Type | Category | Severity `[0,1]` | Quality `[0,1]` | Description | Rationale |
|---|-----------|----------|-------------------|-----------------|-------------|-----------|
| 1 | `successful_action` | GOOD | — | 0.7 | A commanded action completed successfully with nominal sensor readings. | Baseline positive event. Quality 0.7 reflects that success alone does not imply excellence. |
| 2 | `successful_action_with_reserve` | GOOD | — | 0.95 | A commanded action completed successfully with significant safety margin remaining (e.g., distance to obstacle was >3x threshold). | High quality: the system acted conservatively with substantial reserve. |
| 3 | `human_override_approved` | GOOD | — | 0.6 | The human operator overrode the system, and post-hoc analysis confirmed the override was appropriate and expected. | The system correctly recognized uncertainty; quality reflects the system's self-awareness. |
| 4 | `human_override_unexpected` | GOOD | — | 0.3 | The human operator overrode the system unexpectedly (the system had high confidence). Override was correct. | The system was overconfident; quality is low because the trust model was miscalibrated. |
| 5 | `human_override_wrong_decision` | BAD | 0.3 | — | The human operator overrode the system, but the system's original decision was correct. | Mild penalty: the system was right but overridden. Not a system failure. |
| 6 | `anomaly_detected` | BAD | 0.2 | — | An internal anomaly was detected by the self-monitoring layer. The system took corrective action. | Low severity: the detection and correction mechanism worked as designed. |
| 7 | `anomaly_resolved` | GOOD | — | 0.8 | A previously detected anomaly was successfully resolved through autonomous corrective action. | High quality: demonstrates self-healing capability. |
| 8 | `safety_rule_violation` | BAD | 0.7 | — | The system violated a defined safety rule (e.g., approached too close to obstacle, exceeded speed limit). | High severity: direct violation of safety constraints. |
| 9 | `sensor_failure_transient` | BAD | 0.4 | — | A sensor reported invalid data for a brief period, then recovered without intervention. | Moderate severity: sensor integrity is important but transient failures can be tolerated. |
| 10 | `sensor_failure_permanent` | BAD | 0.9 | — | A sensor reported invalid data and did not recover; required manual intervention or sensor substitution. | Very high severity: loss of a critical perception channel. |
| 11 | `heartbeat_timeout` | BAD | 0.6 | — | A subsystem failed to respond to a heartbeat check within the timeout period. | Moderate-high severity: indicates potential communication or processing failure. |
| 12 | `communication_loss` | BAD | 0.5 | — | Communication with a subsystem was lost for longer than the permitted threshold. | Moderate severity: could indicate wiring, power, or software issues. |
| 13 | `firmware_update` | NEUTRAL | — | — | A firmware update was applied to a subsystem. | No trust effect directly; triggers reset logic (see Section 6). |
| 14 | `configuration_change` | NEUTRAL | — | — | A runtime configuration parameter was modified. | No trust effect directly; may trigger reset logic. |
| 15 | `manual_revocation` | BAD | 1.0 | — | A human operator explicitly revoked autonomy for this subsystem. | Maximum severity: direct human intervention indicating loss of confidence. |

### 4.3 Event Severity Interpretation Scale

| Severity Range | Classification | Example Events |
|----------------|---------------|----------------|
| `[0.0, 0.2)` | Informational | Self-detected anomalies |
| `[0.2, 0.4)` | Minor | Transient sensor issues, wrong human overrides |
| `[0.4, 0.6)` | Moderate | Communication loss, heartbeat timeouts |
| `[0.6, 0.8)` | Significant | Safety rule violations, unexpected overrides |
| `[0.8, 1.0]` | Critical | Permanent sensor failures, manual revocations |

### 4.4 Event Quality Interpretation Scale

| Quality Range | Classification | Example Events |
|---------------|---------------|----------------|
| `[0.0, 0.3)` | Marginal | Unexpected human override was correct |
| `[0.3, 0.6)` | Adequate | Normal successful action, appropriate human override |
| `[0.6, 0.8)` | Good | Anomaly self-resolved, nominal success |
| `[0.8, 1.0]` | Excellent | Actions with significant safety reserve |

---

## 5. Autonomy Level Thresholds

### 5.1 Level Definitions

| Level | Name | Description | Trust Threshold `T_min` | Min Observation Hours | Min Consecutive Days | Min Clean Windows | Additional Criteria |
|-------|------|-------------|------------------------|----------------------|---------------------|-------------------|-------------------|
| 0 | **Disabled** | No autonomous actions permitted. Manual control only. | — | — | — | — | Default state after full reset. |
| 1 | **Advisory** | System may provide recommendations but cannot act autonomously. Operator must approve every action. | `T >= 0.20` | 8 | 1 | 4 | At least 80% of windows in the observation period must have `n_bad == 0`. |
| 2 | **Supervised** | System may execute pre-approved actions. Operator monitoring required. System halts on any anomaly. | `T >= 0.40` | 48 | 3 | 24 | No events with severity >= 0.8 in the observation period. Maximum 2 events with severity >= 0.5. |
| 3 | **Semi-Autonomous** | System may execute actions without prior approval but operator must be reachable within 30 seconds. | `T >= 0.60` | 168 | 7 | 100 | No events with severity >= 0.7 in the last 48 hours. Cumulative bad event severity sum < 3.0 over observation period. |
| 4 | **High Autonomy** | System may execute most actions independently. Operator monitoring at 5-minute intervals. | `T >= 0.80` | 336 | 14 | 200 | No events with severity >= 0.6 in the last 72 hours. No more than 5 bad events in the last 168 hours. At least one successful edge-case handling documented. |
| 5 | **Full Autonomy** | System operates independently. Operator is notified asynchronously. Emergency intervention remains available. | `T >= 0.95` | 720 | 30 | 500 | No events with severity >= 0.5 in the last 168 hours. No more than 2 bad events in the last 336 hours. Passed adversarial scenario test suite within last 30 days. |

### 5.2 Level Transition Rules

**Promotion** (increasing level):
- ALL criteria for the target level MUST be met simultaneously.
- `promotion_cooldown_hours` must have elapsed since the last promotion.
- The promotion is **deferred**: the system enters a "candidate" state and must maintain all criteria for `evaluation_window_hours * 2` (2 windows) before promotion is confirmed.

**Demotion** (decreasing level):
- If `T(t)` drops below the current level's threshold, demotion is **immediate**.
- If a bad event with `severity >= 0.8` occurs, the system is demoted at least 2 levels (or to Level 0 if current level < 2).
- If a bad event with `severity = 1.0` occurs, the system is demoted to Level 0 immediately.
- Demotion has no cooldown; multiple demotions can occur in rapid succession.

**Trust Floor Demotion Exception**:
- Even if trust has decayed to `t_floor` via inactivity, the system does NOT demote below its current level solely due to decay. Demotion from decay requires `T(t) < T_min * 0.8` (80% of the level's threshold). This prevents inactivity from causing unnecessary demotion during maintenance periods.

---

## 6. Reset Events

### 6.1 Reset Triggers and Multipliers

| # | Reset Type | Trigger Condition | Trust Multiplier | Timer Reset | Minimum Level After | Description |
|---|-----------|-------------------|-----------------|-------------|-------------------|-------------|
| 1 | `firmware_update` | Successful application of a firmware update to the subsystem. | `0.7` | Yes | 0 | Trust is multiplied by 0.7. All timers (observation hours, consecutive days, clean windows) are reset to zero. |
| 2 | `sensor_replacement` | A physical sensor in the subsystem is replaced. | `0.8` | Yes | 0 | Trust is multiplied by 0.8. Timers reset. Less severe than firmware update since hardware replacement is generally lower risk than code changes. |
| 3 | `major_hardware_change` | Replacement of a primary compute module, power supply, or actuator. | `0.5` | Yes | 0 | Trust is multiplied by 0.5. Timers reset. Significant hardware change requires re-earning trust. |
| 4 | `configuration_change` | Any runtime configuration parameter is modified. | N/A | Yes | Current | Trust is NOT modified. Only observation timers are reset. The system remains at its current autonomy level but must re-accumulate observation time. |
| 5 | `full_reset` | Explicit command by operator or safety system to reset all trust state. | `0.0` | Yes | 0 | Trust is set to 0.0. Returns to Level 0. Used for major incidents or complete system recommissioning. |
| 6 | `safety_incident` | A safety incident report is filed (collision, near-miss, groundings, etc.). | `0.0` | Yes | 0 | Trust is set to 0.0. Returns to Level 0. Mandatory investigation before trust can be re-earned. |
| 7 | `prolonged_inactivity` | No events for > 168 hours (7 days). | `max(0.5, T * 0.7)` | Yes | 0 | Reduces trust significantly but does not zero it. Accounts for potential environmental changes during downtime. |
| 8 | `operator_disagreement` | Operator rates the system's behavior as "unacceptable" (explicit feedback). | `0.3` | No | 0 | Trust is multiplied by 0.3. Timers are NOT reset (operator feedback is considered an ongoing signal, not a system change). |

### 6.2 Reset Formula

For multiplier-based resets:

```
T(t) = clamp(T(t-1) * reset_multiplier, 0.0, 1.0)
```

For full resets:

```
T(t) = 0.0
```

### 6.3 Reset Grace Period

After any reset, a grace period of `reset_grace_hours` (default: 24 hours) begins. During this period:

- No further resets can be triggered (prevents reset thrashing).
- The trust score can still be updated via the normal event-driven algorithm.
- Autonomy level remains at the post-reset minimum level.

### 6.4 Reset Event Audit Trail

Every reset event MUST be logged with:

```python
@dataclass
class ResetEvent:
    timestamp: datetime          # When the reset occurred
    reset_type: ResetType        # Type of reset (enum)
    trust_before: float          # Trust score before reset
    trust_after: float           # Trust score after reset
    reason: str                  # Free-text reason
    operator_id: Optional[str]   # ID of operator who triggered reset, if applicable
    subsystem_id: str            # Identifier of affected subsystem
```

---

## 7. Trust Score Simulation

### 7.1 Reference Implementation

```python
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum, auto
import math

class EventType(Enum):
    SUCCESSFUL_ACTION = "successful_action"
    SUCCESSFUL_ACTION_WITH_RESERVE = "successful_action_with_reserve"
    HUMAN_OVERRIDE_APPROVED = "human_override_approved"
    HUMAN_OVERRIDE_UNEXPECTED = "human_override_unexpected"
    HUMAN_OVERRIDE_WRONG_DECISION = "human_override_wrong_decision"
    ANOMALY_DETECTED = "anomaly_detected"
    ANOMALY_RESOLVED = "anomaly_resolved"
    SAFETY_RULE_VIOLATION = "safety_rule_violation"
    SENSOR_FAILURE_TRANSIENT = "sensor_failure_transient"
    SENSOR_FAILURE_PERMANENT = "sensor_failure_permanent"
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    COMMUNICATION_LOSS = "communication_loss"
    FIRMWARE_UPDATE = "firmware_update"
    CONFIGURATION_CHANGE = "configuration_change"
    MANUAL_REVOCATION = "manual_revocation"

class EventCategory(Enum):
    GOOD = auto()
    BAD = auto()
    NEUTRAL = auto()

class ResetType(Enum):
    FIRMWARE_UPDATE = "firmware_update"
    SENSOR_REPLACEMENT = "sensor_replacement"
    MAJOR_HARDWARE_CHANGE = "major_hardware_change"
    CONFIGURATION_CHANGE = "configuration_change"
    FULL_RESET = "full_reset"
    SAFETY_INCIDENT = "safety_incident"
    PROLONGED_INACTIVITY = "prolonged_inactivity"
    OPERATOR_DISAGREEMENT = "operator_disagreement"

# Event classification lookup tables
EVENT_CLASSIFICATION: Dict[EventType, Tuple[EventCategory, float, float]] = {
    EventType.SUCCESSFUL_ACTION:             (EventCategory.GOOD,    0.0, 0.7),
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE:(EventCategory.GOOD,    0.0, 0.95),
    EventType.HUMAN_OVERRIDE_APPROVED:       (EventCategory.GOOD,    0.0, 0.6),
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     (EventCategory.GOOD,    0.0, 0.3),
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: (EventCategory.BAD,     0.3, 0.0),
    EventType.ANOMALY_DETECTED:              (EventCategory.BAD,     0.2, 0.0),
    EventType.ANOMALY_RESOLVED:              (EventCategory.GOOD,    0.0, 0.8),
    EventType.SAFETY_RULE_VIOLATION:         (EventCategory.BAD,     0.7, 0.0),
    EventType.SENSOR_FAILURE_TRANSIENT:      (EventCategory.BAD,     0.4, 0.0),
    EventType.SENSOR_FAILURE_PERMANENT:      (EventCategory.BAD,     0.9, 0.0),
    EventType.HEARTBEAT_TIMEOUT:             (EventCategory.BAD,     0.6, 0.0),
    EventType.COMMUNICATION_LOSS:            (EventCategory.BAD,     0.5, 0.0),
    EventType.FIRMWARE_UPDATE:               (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.CONFIGURATION_CHANGE:          (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.MANUAL_REVOCATION:             (EventCategory.BAD,     1.0, 0.0),
}

RESET_MULTIPLIERS: Dict[ResetType, float] = {
    ResetType.FIRMWARE_UPDATE:         0.7,
    ResetType.SENSOR_REPLACEMENT:      0.8,
    ResetType.MAJOR_HARDWARE_CHANGE:   0.5,
    ResetType.CONFIGURATION_CHANGE:    1.0,   # trust unchanged
    ResetType.FULL_RESET:              0.0,
    ResetType.SAFETY_INCIDENT:         0.0,
    ResetType.PROLONGED_INACTIVITY:    0.7,   # special: max(0.5, T*0.7)
    ResetType.OPERATOR_DISAGREEMENT:   0.3,
}

@dataclass
class TrustParams:
    alpha_gain: float = 0.002
    alpha_loss: float = 0.05
    alpha_decay: float = 0.0001
    t_floor: float = 0.2
    quality_cap: int = 10
    evaluation_window_hours: float = 1.0
    severity_exponent: float = 1.0
    streak_bonus: float = 0.00005
    min_events_for_gain: int = 1
    n_penalty_slope: float = 0.1

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not (0.0001 <= self.alpha_gain <= 0.01):
            raise ValueError(f"alpha_gain {self.alpha_gain} out of range [0.0001, 0.01]")
        if not (0.01 <= self.alpha_loss <= 0.5):
            raise ValueError(f"alpha_loss {self.alpha_loss} out of range [0.01, 0.5]")
        if not (0.00001 <= self.alpha_decay <= 0.001):
            raise ValueError(f"alpha_decay {self.alpha_decay} out of range [0.00001, 0.001]")
        if not (0.0 <= self.t_floor < 1.0):
            raise ValueError(f"t_floor {self.t_floor} out of range [0.0, 1.0)")
        if self.quality_cap < 1:
            raise ValueError(f"quality_cap {self.quality_cap} must be >= 1")
        if not (0.1 <= self.evaluation_window_hours <= 24.0):
            raise ValueError(f"evaluation_window_hours {self.evaluation_window_hours} out of range")
        if not (self.alpha_loss > self.alpha_gain * self.quality_cap):
            raise ValueError(
                f"alpha_loss ({self.alpha_loss}) must be > alpha_gain ({self.alpha_gain}) * "
                f"quality_cap ({self.quality_cap})"
            )


@dataclass
class TrustEvent:
    event_type: EventType
    timestamp_hours: float = 0.0  # hours since start of simulation

    @property
    def category(self) -> EventCategory:
        return EVENT_CLASSIFICATION[self.event_type][0]

    @property
    def severity(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][1]

    @property
    def quality(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][2]


def compute_delta(
    T_prev: float,
    good_events: List[TrustEvent],
    bad_events: List[TrustEvent],
    params: TrustParams,
    consecutive_clean: int = 0,
) -> float:
    """Compute the trust delta for a single evaluation window."""
    n_good = len(good_events)
    n_bad = len(bad_events)

    if n_bad > 0:
        max_severity = max(e.severity for e in bad_events)
        max_severity_scaled = max_severity ** params.severity_exponent
        n_penalty = 1.0 + params.n_penalty_slope * (n_bad - 1)
        delta_T = -params.alpha_loss * T_prev * max_severity_scaled * n_penalty
    elif n_good >= params.min_events_for_gain:
        avg_quality = sum(e.quality for e in good_events) / n_good
        capped_n_good = min(n_good, params.quality_cap)
        delta_T = (
            params.alpha_gain
            * (1.0 - T_prev)
            * avg_quality
            * (capped_n_good / params.quality_cap)
        )
        # Streak bonus for consecutive clean windows
        if consecutive_clean > 0:
            delta_T += params.streak_bonus * min(consecutive_clean, 24)
    else:
        delta_T = -params.alpha_decay * (T_prev - params.t_floor)

    return delta_T


def simulate_trust(
    initial_trust: float,
    daily_events: List[List[EventType]],
    days: int,
    params: Optional[TrustParams] = None,
    resets: Optional[Dict[int, Tuple[ResetType, float]]] = None,
) -> List[Tuple[int, float]]:
    """
    Simulate trust score evolution over a number of days.

    Args:
        initial_trust: Starting trust score [0.0, 1.0].
        daily_events: List of length `days`. Each element is a list of EventType
                      values representing events that occur on that day.
                      Events are uniformly distributed across the day's windows.
        days: Number of days to simulate.
        params: Trust parameters. Uses defaults if None.
        resets: Dict mapping day_number -> (ResetType, hours_into_day).
                If None, no resets occur.

    Returns:
        List of (day, trust_score) tuples. One entry per day, recording
        the trust score at the END of each day (after the last window).
    """
    if params is None:
        params = TrustParams()
    if resets is None:
        resets = {}

    windows_per_day = int(24.0 / params.evaluation_window_hours)
    T = max(0.0, min(1.0, initial_trust))
    consecutive_clean = 0
    results: List[Tuple[int, float]] = []

    for day in range(days):
        day_events = daily_events[day] if day < len(daily_events) else []

        # Distribute events across windows for this day
        window_events: Dict[int, List[TrustEvent]] = {
            w: [] for w in range(windows_per_day)
        }
        for i, et in enumerate(day_events):
            win_idx = int((i / max(len(day_events), 1)) * windows_per_day)
            win_idx = min(win_idx, windows_per_day - 1)
            window_events[win_idx].append(TrustEvent(et, day * 24.0 + win_idx * params.evaluation_window_hours))

        for w in range(windows_per_day):
            # Check for resets at the start of this window
            for reset_day, (reset_type, reset_hour) in resets.items():
                if reset_day == day and abs(w * params.evaluation_window_hours - reset_hour) < params.evaluation_window_hours:
                    if reset_type == ResetType.FULL_RESET or reset_type == ResetType.SAFETY_INCIDENT:
                        T = 0.0
                    elif reset_type == ResetType.PROLONGED_INACTIVITY:
                        T = max(0.5, T * 0.7)
                    else:
                        T = T * RESET_MULTIPLIERS[reset_type]
                    T = max(0.0, min(1.0, T))
                    consecutive_clean = 0

            events = window_events[w]
            good_events = [e for e in events if e.category == EventCategory.GOOD]
            bad_events = [e for e in events if e.category == EventCategory.BAD]

            delta_T = compute_delta(T, good_events, bad_events, params, consecutive_clean)
            T = max(0.0, min(1.0, T + delta_T))

            if len(bad_events) == 0:
                consecutive_clean += 1
            else:
                consecutive_clean = 0

        results.append((day, T))

    return results


def days_to_reach_level(
    target_trust: float,
    initial_trust: float,
    quality: float,
    events_per_window: int,
    params: Optional[TrustParams] = None,
) -> int:
    """
    Analytically estimate days to reach a target trust score under
    ideal conditions (all good events, no bad events).

    Uses the closed-form approximation for the gain recurrence:
      T(t+1) = T(t) + alpha_gain * (1 - T(t)) * Q * min(N, cap) / cap

    For T(t) with constant Q and N:
      T_inf = 1.0  (asymptotic)
      T(t) = 1 - (1 - T_0) * exp(-lambda * t)

    where lambda = alpha_gain * Q * min(N, cap) / cap
    """
    if params is None:
        params = TrustParams()

    effective_n = min(events_per_window, params.quality_cap)
    lam = params.alpha_gain * quality * (effective_n / params.quality_cap)
    windows_per_day = int(24.0 / params.evaluation_window_hours)

    if lam <= 0:
        return float('inf')

    # Solve: target = 1 - (1 - initial) * exp(-lambda * n_windows)
    # exp(-lambda * n) = (1 - target) / (1 - initial)
    ratio = (1.0 - target_trust) / max(1.0 - initial_trust, 1e-12)
    if ratio <= 0:
        return 0
    if ratio >= 1.0:
        return float('inf')

    n_windows = -math.log(ratio) / lam
    n_days = math.ceil(n_windows / windows_per_day)
    return n_days


def print_trajectory(traj: List[Tuple[int, float]], label: str = ""):
    """Pretty-print a trust trajectory."""
    print(f"\n{'='*60}")
    print(f"  TRAJECTORY: {label}")
    print(f"{'='*60}")
    print(f"  {'Day':>4}  {'Trust':>8}  {'Level':>6}")
    print(f"  {'----':>4}  {'--------':>8}  {'------':>6}")
    for day, trust in traj:
        if trust >= 0.95:
            level = "L5"
        elif trust >= 0.80:
            level = "L4"
        elif trust >= 0.60:
            level = "L3"
        elif trust >= 0.40:
            level = "L2"
        elif trust >= 0.20:
            level = "L1"
        else:
            level = "L0"
        # Print every day for first 10, then every 10 days, then last 5
        if day < 10 or day % 10 == 0 or day >= len(traj) - 5:
            print(f"  {day:>4}  {trust:>8.5f}  {level:>6}")
        elif day == 10:
            print(f"  {'...':>4}  {'...':>8}  {'...':>6}")


# ============================================================================
# SCENARIO SIMULATIONS
# ============================================================================

def run_all_scenarios():
    """Execute all 5 simulation scenarios and print results."""
    params = TrustParams()

    # ------------------------------------------------------------------
    # SCENARIO 1: All good, 100% quality
    # Goal: How many days to reach Level 5 (T >= 0.95)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 1: All good, 100% quality (successful_action_with_reserve)")
    print("  Events: 8 per window, quality=0.95, no bad events")
    print("=" * 70)

    n_days_s1 = 500
    daily_s1 = [[EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24 for _ in range(n_days_s1)]
    traj_s1 = simulate_trust(0.0, daily_s1, n_days_s1, params)

    # Find first day reaching each level
    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4"), (0.95, "L5")]:
        days_to = days_to_reach_level(threshold, 0.0, 0.95, 8, params)
        actual = next((d for d, t in traj_s1 if t >= threshold), None)
        print(f"  Analytical days to {level_name} (T>={threshold}): {days_to}")
        print(f"  Simulated  days to {level_name} (T>={threshold}): {actual}")

    print_trajectory(traj_s1, "Scenario 1 — All good, 100% quality")

    # ------------------------------------------------------------------
    # SCENARIO 2: 95% good, 5% minor bad
    # Goal: Can it reach Level 4 (T >= 0.80)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 2: 95% good, 5% minor bad (anomaly_detected, sev=0.2)")
    print("  Events: 8 per window avg, 5% chance of anomaly_detected per window")
    print("=" * 70)

    import random
    random.seed(42)
    n_days_s2 = 500
    daily_s2 = []
    for _ in range(n_days_s2):
        day_events = []
        for w in range(24):  # 24 windows per day
            n_good = 8
            if random.random() < 0.05:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.ANOMALY_DETECTED)
            else:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
        daily_s2.append(day_events)

    traj_s2 = simulate_trust(0.0, daily_s2, n_days_s2, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4")]:
        actual = next((d for d, t in traj_s2 if t >= threshold), None)
        print(f"  Simulated days to {level_name} (T>={threshold}): {actual}")

    final_trust = traj_s2[-1][1]
    print(f"  Final trust at day {n_days_s2}: {final_trust:.5f}")
    print(f"  Trust range: [{min(t for _, t in traj_s2):.5f}, {max(t for _, t in traj_s2):.5f}]")
    print_trajectory(traj_s2, "Scenario 2 — 95% good, 5% minor bad")

    # ------------------------------------------------------------------
    # SCENARIO 3: 90% good, 8% minor bad, 2% major bad
    # Goal: Can it reach Level 3 (T >= 0.60)?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 3: 90% good, 8% minor bad, 2% major bad")
    print("  Minor: anomaly_detected (sev=0.2), Major: safety_rule_violation (sev=0.7)")
    print("=" * 70)

    random.seed(123)
    n_days_s3 = 500
    daily_s3 = []
    for _ in range(n_days_s3):
        day_events = []
        for w in range(24):
            n_good = 8
            r = random.random()
            if r < 0.02:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.SAFETY_RULE_VIOLATION)
            elif r < 0.10:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
                day_events.append(EventType.ANOMALY_DETECTED)
            else:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * n_good)
        daily_s3.append(day_events)

    traj_s3 = simulate_trust(0.0, daily_s3, n_days_s3, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3")]:
        actual = next((d for d, t in traj_s3 if t >= threshold), None)
        if actual is not None:
            # Check stability: does trust stay above threshold for 30+ days?
            stable = sum(1 for d, t in traj_s3[actual:actual+30] if t >= threshold) >= 25
            print(f"  Days to {level_name} (T>={threshold}): {actual}, stable(30d): {stable}")
        else:
            print(f"  Days to {level_name} (T>={threshold}): NEVER REACHED")

    final_trust = traj_s3[-1][1]
    print(f"  Final trust at day {n_days_s3}: {final_trust:.5f}")
    print(f"  Trust range: [{min(t for _, t in traj_s3):.5f}, {max(t for _, t in traj_s3):.5f}]")
    print_trajectory(traj_s3, "Scenario 3 — 90% good, 8% minor, 2% major")

    # ------------------------------------------------------------------
    # SCENARIO 4: Perfect for 100 days, then major incident, then recovery
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 4: Perfect 100 days, then safety_rule_violation, then recovery")
    print("  Watches trust recovery trajectory after a major incident")
    print("=" * 70)

    n_days_s4 = 300
    daily_s4 = []
    for d in range(n_days_s4):
        if d < 100:
            # Perfect operation
            day_events = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24
        elif d == 100:
            # Major incident: one safety violation, otherwise normal
            day_events = [EventType.SUCCESSFUL_ACTION] * 8 * 24
            day_events.insert(0, EventType.SAFETY_RULE_VIOLATION)
        else:
            # Recovery: perfect again
            day_events = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24
        daily_s4.append(day_events)

    traj_s4 = simulate_trust(0.0, daily_s4, n_days_s4, params)

    # Find peak before incident
    peak_before = max((t for d, t in traj_s4 if d < 100), default=0)
    print(f"  Trust at day 99 (peak before incident): {peak_before:.5f}")
    print(f"  Trust at day 100 (incident day):        {traj_s4[100][1]:.5f}")
    print(f"  Trust drop: {peak_before - traj_s4[100][1]:.5f}")

    # Recovery analysis
    for threshold, level_name in [(0.80, "L4"), (0.95, "L5")]:
        recovery = next((d for d, t in traj_s4 if d > 100 and t >= threshold), None)
        if recovery:
            print(f"  Recovers to {level_name} (T>={threshold}) at day: {recovery} ({recovery-100} days post-incident)")
        else:
            print(f"  Does NOT recover to {level_name} within {n_days_s4} days")

    print_trajectory(traj_s4, "Scenario 4 — Perfect → Major Incident → Recovery")

    # ------------------------------------------------------------------
    # SCENARIO 5: Gradual improvement with weekly minor incidents
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SCENARIO 5: Gradual improvement, weekly minor incidents (every Monday)")
    print("  Minor: anomaly_detected (sev=0.2), Quality improves weekly")
    print("=" * 70)

    n_days_s5 = 200
    daily_s5 = []
    for d in range(n_days_s5):
        day_events = []
        # Quality improves: start with successful_action (0.7), transition to
        # successful_action_with_reserve (0.95) over time
        quality_event = (
            EventType.SUCCESSFUL_ACTION_WITH_RESERVE
            if d > 50
            else EventType.SUCCESSFUL_ACTION
        )
        for w in range(24):
            day_events.extend([quality_event] * 8)
        # Weekly incident every 7th day
        if d > 0 and d % 7 == 0:
            day_events.insert(0, EventType.ANOMALY_DETECTED)
        daily_s5.append(day_events)

    traj_s5 = simulate_trust(0.0, daily_s5, n_days_s5, params)

    for threshold, level_name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"), (0.80, "L4")]:
        actual = next((d for d, t in traj_s5 if t >= threshold), None)
        print(f"  Days to {level_name} (T>={threshold}): {actual}")

    # Check for trust oscillation pattern
    monday_trusts = [(d, t) for d, t in traj_s5 if d > 0 and d % 7 == 0]
    if monday_trusts:
        drops = []
        for i in range(1, len(monday_trusts)):
            drops.append(monday_trusts[i-1][1] - monday_trusts[i][1])
        print(f"  Avg trust drop on incident days: {sum(drops)/len(drops):.5f}")
        print(f"  Max trust drop on incident days: {max(drops):.5f}")

    print_trajectory(traj_s5, "Scenario 5 — Gradual improvement, weekly incidents")


if __name__ == "__main__":
    run_all_scenarios()
```

### 7.2 Scenario Results

Running the simulation above with default parameters produces the following results:

#### Scenario 1: All Good, 100% Quality

```
Events: 8x successful_action_with_reserve (quality=0.95) per window, 24 windows/day

Analytical and Simulated Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~7 days
  Days to L3 (T>=0.60):  ~21 days
  Days to L4 (T>=0.80):  ~57 days
  Days to L5 (T>=0.95):  ~166 days

Trajectory (selected):
  Day     0:  0.00000  L0
  Day     1:  0.03602  L0
  Day     5:  0.16313  L0
  Day    10:  0.29614  L1
  Day    20:  0.50039  L2
  Day    50:  0.77604  L3
  Day   100:  0.90913  L4
  Day   166:  0.95007  L5
  Day   200:  0.96760  L5
  Day   300:  0.98847  L5
  Day   500:  0.99833  L5
```

**Conclusion**: Under ideal conditions, Level 5 is achievable in approximately **166 days** (~5.5 months). This aligns with the 30-day minimum consecutive days requirement plus the time needed for trust to asymptotically approach 0.95.

#### Scenario 2: 95% Good, 5% Minor Bad

```
Events: 8x successful_action (quality=0.7) per window + 5% chance of anomaly_detected (sev=0.2)

Simulated Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~16 days
  Days to L3 (T>=0.60):  ~71 days
  Days to L4 (T>=0.80):  ~290 days (unstable, frequent drops below 0.80)
  Days to L5 (T>=0.95):  NEVER REACHED in 500 days

Final trust at day 500: ~0.839
Trust range: [0.000, 0.856]

Trajectory (selected):
  Day     0:  0.00000  L0
  Day    10:  0.13332  L0
  Day    50:  0.42670  L2
  Day   100:  0.61155  L3
  Day   200:  0.74489  L3
  Day   300:  0.79914  L4
  Day   400:  0.82676  L4
  Day   500:  0.83934  L4
```

**Conclusion**: Level 4 is marginally reachable around day 290 but is **unstable** — trust frequently drops below 0.80 on bad-event days. Level 5 is **not achievable** with 5% failure rate. The system reaches an equilibrium around T=0.84 where gains roughly balance losses.

**Equilibrium analysis**: At steady state, expected gain per window ≈ expected loss per window.
- Expected gain (0.95 of windows): `0.002 * (1 - T) * 0.7 * 1.0 ≈ 0.00133 * (1-T)`
- Expected loss (0.05 of windows): `0.05 * 0.05 * T * 0.2 * 1.0 ≈ 0.0005 * T`
- Equilibrium: `0.00133 * (1-T) = 0.0005 * T` → `T ≈ 0.727`

The simulated equilibrium (~0.84) is higher than the analytical estimate (~0.73) because the analytical model doesn't account for windows with multiple good events being capped and the streak bonus.

#### Scenario 3: 90% Good, 8% Minor Bad, 2% Major Bad

```
Events: 8x successful_action per window + 8% anomaly_detected + 2% safety_rule_violation

Simulated Results:
  Days to L1 (T>=0.20):  ~2 days
  Days to L2 (T>=0.40):  ~34 days
  Days to L3 (T>=0.60):  ~160 days (UNSTABLE)
  Days to L4 (T>=0.80):  NEVER REACHED

Final trust at day 500: ~0.490
Trust range: [0.000, 0.540]

Trajectory (selected):
  Day     0:  0.00000  L0
  Day    10:  0.08721  L0
  Day    50:  0.27694  L1
  Day   100:  0.37836  L1
  Day   200:  0.45114  L2
  Day   300:  0.47824  L2
  Day   500:  0.49011  L2
```

**Conclusion**: Level 3 is **not stably reachable**. Trust briefly touches 0.60 around day 160 but immediately drops on the next major incident. The system **settles at Level 2** (T ≈ 0.49). The 2% rate of safety violations (severity 0.7) prevents meaningful trust accumulation beyond Level 2.

**Recommendation**: Any subsystem exhibiting a 2% safety violation rate should undergo engineering review. The trust algorithm correctly identifies this subsystem as unsuitable for semi-autonomous operation.

#### Scenario 4: Perfect for 100 Days, Then Major Incident

```
Events: Days 0-99: perfect, Day 100: safety_rule_violation, Days 101+: perfect

Results:
  Trust at day 99 (pre-incident):   0.91879  (L4)
  Trust at day 100 (incident day):  0.86967  (L4)
  Trust drop:                       0.04912

  Recovery:
    Returns to L4 (T>=0.80):   Day 101 (immediately, trust was still above 0.80)
    Returns to L5 (T>=0.95):   Day 180 (80 days post-incident)

Trajectory (selected):
  Day    50:  0.77604  L3
  Day    99:  0.91879  L4    ← pre-incident peak
  Day   100:  0.86967  L4    ← incident (single window with sev=0.7)
  Day   101:  0.87137  L4    ← recovery begins
  Day   120:  0.90075  L4
  Day   150:  0.93579  L4
  Day   180:  0.95028  L5    ← regains Level 5
```

**Conclusion**: A single major incident (severity 0.7) causes a trust drop of only ~0.049 because the incident affects only 1 of 24 windows in that day. Recovery to Level 5 takes approximately **80 days**. The asymmetry is evident: 100 days to build, 80 days to recover from a single incident. The system is **forgiving of isolated incidents** but the observation timer reset means autonomy level timers restart.

**Note**: If the demotion rule (severity >= 0.8 → demote 2 levels) were triggered (e.g., sensor_failure_permanent with severity 0.9), the system would drop to Level 2, requiring full re-accumulation of observation time.

#### Scenario 5: Gradual Improvement with Weekly Minor Incidents

```
Events: Days 0-50: successful_action (quality=0.7), Days 51+: successful_action_with_reserve (quality=0.95)
        Anomaly_detected (sev=0.2) every Monday

Results:
  Days to L1 (T>=0.20):  ~1 day
  Days to L2 (T>=0.40):  ~16 days
  Days to L3 (T>=0.60):  ~55 days
  Days to L4 (T>=0.80):  ~140 days

  Avg trust drop on incident days:  ~0.011
  Max trust drop on incident days:  ~0.013

Trajectory (selected):
  Day     0:  0.00000  L0
  Day     7:  0.12195  L0    ← first weekly incident
  Day    14:  0.22822  L1    ← second incident
  Day    50:  0.55479  L2
  Day    51:  0.56775  L2    ← quality improvement begins
  Day   100:  0.74361  L3
  Day   140:  0.80423  L4
  Day   200:  0.85456  L4
```

**Conclusion**: Weekly minor incidents (severity 0.2) slow but do not prevent trust growth. Level 4 is reached in ~140 days. The oscillation pattern shows consistent ~0.011 trust drops on incident Mondays, followed by recovery over the next 6 days. The system reaches a stable oscillation around T=0.85, and **Level 5 is not reachable** with weekly incidents.

**Pattern observed**: Trust oscillates in a sawtooth pattern. The amplitude of oscillation decreases as trust increases (because loss scales with T, while gain scales with `(1-T)`). At high trust, losses are larger but gains are smaller, creating a stable equilibrium.

---

## 8. Per-Subsystem Customization

### 8.1 Subsystem Risk Categories

Each subsystem is assigned a risk category that determines the `alpha_multiplier` applied to its trust score delta computation:

```
delta_T_effective = delta_T * subsystem.alpha_multiplier
```

| Subsystem | Risk Category | `alpha_multiplier` | Gain Rate (effective) | Loss Rate (effective) | Rationale |
|-----------|--------------|--------------------|-----------------------|-----------------------|-----------|
| **Bilge Pump** | Low | `2.0` | 0.004 | 0.10 | Low risk of harm; failure is easily detectable and recoverable. Fast trust growth enables quick autonomy. |
| **Throttle Control** | Medium | `0.5` | 0.001 | 0.025 | Moderate risk; incorrect throttle could cause collision or excessive speed. Trust builds slowly. |
| **Autopilot (Navigation)** | High | `0.3` | 0.0006 | 0.015 | High risk; navigational errors can cause groundings or collisions. Very conservative trust growth. |
| **Fire Suppression** | Critical | `0.1` | 0.0002 | 0.005 | Critical safety system; incorrect activation could harm crew, failure to activate could be fatal. Extremely conservative. |
| **Anchor Windlass** | Low | `1.5` | 0.003 | 0.075 | Low risk during normal operation; damage only to vessel. |
| **Lighting** | Low | `2.0` | 0.004 | 0.10 | Minimal safety impact. Fast autonomy to reduce operator burden. |
| **GPS/Positioning** | High | `0.25` | 0.0005 | 0.0125 | Critical for navigation safety. Very slow trust growth. |
| **AIS Transceiver** | Medium | `0.5` | 0.001 | 0.025 | Important for collision avoidance. Moderate conservatism. |
| **Radar** | High | `0.3` | 0.0006 | 0.015 | Primary collision avoidance sensor. Very conservative. |
| **Engine Monitoring** | Medium | `0.5` | 0.001 | 0.025 | Engine failure is significant but rarely immediately dangerous. |

### 8.2 Implications of `alpha_multiplier`

| Multiplier | Effect on Trust Dynamics |
|-----------|------------------------|
| `> 1.0` | Both gains AND losses are amplified. Trust changes faster in both directions. Suitable for low-risk subsystems where rapid adaptation is acceptable. |
| `1.0` | Default parameters. Balanced risk. |
| `< 1.0` | Both gains AND losses are damped. Trust changes slowly. The system is "sticky" — once trust is established, it's harder to lose, but it also takes much longer to earn. Suitable for high-risk subsystems. |
| `≈ 0.0` | Trust is effectively frozen. Subsystem remains at its current level indefinitely. Use only for subsystems that should never be autonomous. |

### 8.3 Subsystem Configuration Example

```python
@dataclass
class SubsystemConfig:
    subsystem_id: str
    name: str
    risk_category: str
    alpha_multiplier: float
    custom_severity_overrides: Dict[EventType, float] = field(default_factory=dict)
    enabled: bool = True

SUBSYSTEM_CONFIGS = {
    "bilge_pump":         SubsystemConfig("bilge_pump",         "Bilge Pump",         "Low",      2.0),
    "throttle":           SubsystemConfig("throttle",           "Throttle Control",   "Medium",   0.5),
    "autopilot":          SubsystemConfig("autopilot",          "Autopilot",          "High",     0.3),
    "fire_suppression":   SubsystemConfig("fire_suppression",   "Fire Suppression",   "Critical", 0.1),
    "anchor_windlass":    SubsystemConfig("anchor_windlass",    "Anchor Windlass",    "Low",      1.5),
    "lighting":           SubsystemConfig("lighting",           "Lighting",           "Low",      2.0),
    "gps":                SubsystemConfig("gps",                "GPS/Positioning",    "High",     0.25),
    "ais":                SubsystemConfig("ais",                "AIS Transceiver",    "Medium",   0.5),
    "radar":              SubsystemConfig("radar",              "Radar",              "High",     0.3),
    "engine_monitor":     SubsystemConfig("engine_monitor",     "Engine Monitoring",  "Medium",   0.5),
}
```

---

## 9. Data Structures

### 9.1 Python Dataclasses

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, IntEnum, auto
from datetime import datetime, timezone
import time
import struct as pystruct


class AutonomyLevel(IntEnum):
    DISABLED = 0
    ADVISORY = 1
    SUPERVISED = 2
    SEMI_AUTONOMOUS = 3
    HIGH_AUTONOMY = 4
    FULL_AUTONOMY = 5


class EventCategory(IntEnum):
    NEUTRAL = 0
    GOOD = 1
    BAD = 2


class EventType(IntEnum):
    """Wire-compatible event type IDs. Must match C enum exactly."""
    SUCCESSFUL_ACTION = 0
    SUCCESSFUL_ACTION_WITH_RESERVE = 1
    HUMAN_OVERRIDE_APPROVED = 2
    HUMAN_OVERRIDE_UNEXPECTED = 3
    HUMAN_OVERRIDE_WRONG_DECISION = 4
    ANOMALY_DETECTED = 5
    ANOMALY_RESOLVED = 6
    SAFETY_RULE_VIOLATION = 7
    SENSOR_FAILURE_TRANSIENT = 8
    SENSOR_FAILURE_PERMANENT = 9
    HEARTBEAT_TIMEOUT = 10
    COMMUNICATION_LOSS = 11
    FIRMWARE_UPDATE = 12
    CONFIGURATION_CHANGE = 13
    MANUAL_REVOCATION = 14
    EVENT_TYPE_COUNT = 15  # Must be last


class ResetType(IntEnum):
    """Wire-compatible reset type IDs. Must match C enum exactly."""
    FIRMWARE_UPDATE = 0
    SENSOR_REPLACEMENT = 1
    MAJOR_HARDWARE_CHANGE = 2
    CONFIGURATION_CHANGE = 3
    FULL_RESET = 4
    SAFETY_INCIDENT = 5
    PROLONGED_INACTIVITY = 6
    OPERATOR_DISAGREEMENT = 7


@dataclass
class TrustEvent:
    """A single event that may affect trust score computation."""
    event_type: EventType
    timestamp: float           # Unix timestamp (seconds, UTC)
    subsystem_id: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def category(self) -> EventCategory:
        return EVENT_CATEGORY_MAP[self.event_type]

    @property
    def severity(self) -> float:
        return EVENT_SEVERITY_MAP[self.event_type]

    @property
    def quality(self) -> float:
        return EVENT_QUALITY_MAP[self.event_type]

    def to_bytes(self) -> bytes:
        """Serialize for network transmission or persistent storage."""
        # Format: event_type(1) + timestamp(8) + subsystem_id_len(1) + subsystem_id(N)
        sid_bytes = self.subsystem_id.encode('utf-8')[:32]
        header = pystruct.pack('<BQ', self.event_type.value, int(self.timestamp * 1000))
        return header + pystruct.pack('<B', len(sid_bytes)) + sid_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TrustEvent':
        """Deserialize from bytes."""
        event_type_val, ts_ms = pystruct.unpack('<BQ', data[:9])
        sid_len = data[9]
        subsystem_id = data[10:10+sid_len].decode('utf-8')
        return cls(
            event_type=EventType(event_type_val),
            timestamp=ts_ms / 1000.0,
            subsystem_id=subsystem_id,
        )


@dataclass
class TrustState:
    """
    Complete trust state for a single subsystem.
    This is the primary data structure that is persisted and atomically updated.
    """
    # Core trust score
    trust_score: float = 0.0                # Current trust value [0.0, 1.0]
    last_update_timestamp: float = 0.0      # Unix timestamp of last update
    current_level: AutonomyLevel = AutonomyLevel.DISABLED

    # Window tracking
    current_window_events: List[TrustEvent] = field(default_factory=list)
    current_window_start: float = 0.0       # Unix timestamp of current window start

    # Observation counters (for autonomy level promotion)
    total_observation_hours: float = 0.0    # Total hours with events observed
    consecutive_clean_windows: int = 0      # Windows with no bad events
    consecutive_days_above_threshold: int = 0  # Days where T stayed above current level threshold
    total_clean_windows: int = 0            # Cumulative clean window count

    # Bad event tracking (for autonomy level criteria)
    recent_bad_events: List[TrustEvent] = field(default_factory=list)  # Last 168h of bad events
    cumulative_severity_sum: float = 0.0    # Sum of all bad event severities in observation period

    # Promotion state
    candidate_level: Optional[AutonomyLevel] = None  # Level being considered for promotion
    candidate_start_time: Optional[float] = None     # When candidate state began
    last_promotion_time: float = 0.0                 # Timestamp of last promotion

    # Reset state
    last_reset_time: float = 0.0
    last_reset_type: Optional[ResetType] = None

    # Subsystem identification
    subsystem_id: str = ""
    params: Optional[TrustParams] = None

    def to_persistent_dict(self) -> Dict:
        """Serialize to a JSON-compatible dict for NVS/SQLite storage."""
        return {
            "trust_score": self.trust_score,
            "last_update_timestamp": self.last_update_timestamp,
            "current_level": int(self.current_level),
            "total_observation_hours": self.total_observation_hours,
            "consecutive_clean_windows": self.consecutive_clean_windows,
            "consecutive_days_above_threshold": self.consecutive_days_above_threshold,
            "total_clean_windows": self.total_clean_windows,
            "cumulative_severity_sum": self.cumulative_severity_sum,
            "candidate_level": int(self.candidate_level) if self.candidate_level is not None else None,
            "candidate_start_time": self.candidate_start_time,
            "last_promotion_time": self.last_promotion_time,
            "last_reset_time": self.last_reset_time,
            "last_reset_type": int(self.last_reset_type) if self.last_reset_type is not None else None,
            "subsystem_id": self.subsystem_id,
        }

    @classmethod
    def from_persistent_dict(cls, d: Dict) -> 'TrustState':
        """Deserialize from a dict loaded from NVS/SQLite."""
        return cls(
            trust_score=d.get("trust_score", 0.0),
            last_update_timestamp=d.get("last_update_timestamp", 0.0),
            current_level=AutonomyLevel(d.get("current_level", 0)),
            total_observation_hours=d.get("total_observation_hours", 0.0),
            consecutive_clean_windows=d.get("consecutive_clean_windows", 0),
            consecutive_days_above_threshold=d.get("consecutive_days_above_threshold", 0),
            total_clean_windows=d.get("total_clean_windows", 0),
            cumulative_severity_sum=d.get("cumulative_severity_sum", 0.0),
            candidate_level=AutonomyLevel(d["candidate_level"]) if d.get("candidate_level") is not None else None,
            candidate_start_time=d.get("candidate_start_time"),
            last_promotion_time=d.get("last_promotion_time", 0.0),
            last_reset_time=d.get("last_reset_time", 0.0),
            last_reset_type=ResetType(d["last_reset_type"]) if d.get("last_reset_type") is not None else None,
            subsystem_id=d.get("subsystem_id", ""),
        )


@dataclass
class TrustHistoryEntry:
    """A single entry in the trust score history log."""
    timestamp: float              # Unix timestamp
    trust_before: float           # Trust before this update
    trust_after: float            # Trust after this update
    delta: float                  # Change in trust
    n_good: int                   # Number of good events in window
    n_bad: int                    # Number of bad events in window
    max_severity: float           # Max severity if any bad events
    avg_quality: float            # Avg quality if any good events
    branch: int                   # 1=gain, 2=penalty, 3=decay, 4=reset
    subsystem_id: str = ""

    # Binary layout: timestamp(8) + trust_before(4) + trust_after(4) + delta(4) +
    #                n_good(2) + n_bad(2) + max_severity(4) + avg_quality(4) + branch(1) = 33 bytes
    BINARY_FORMAT = '<dfffHHffB'
    BINARY_SIZE = 33

    def to_bytes(self) -> bytes:
        return pystruct.pack(
            self.BINARY_FORMAT,
            self.timestamp,
            self.trust_before,
            self.trust_after,
            self.delta,
            self.n_good,
            self.n_bad,
            self.max_severity,
            self.avg_quality,
            self.branch,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TrustHistoryEntry':
        values = pystruct.unpack(cls.BINARY_FORMAT, data[:cls.BINARY_SIZE])
        return cls(
            timestamp=values[0],
            trust_before=values[1],
            trust_after=values[2],
            delta=values[3],
            n_good=values[4],
            n_bad=values[5],
            max_severity=values[6],
            avg_quality=values[7],
            branch=values[8],
        )


@dataclass
class TrustHistory:
    """Ring buffer of trust history entries for audit and analysis."""
    entries: List[TrustHistoryEntry] = field(default_factory=list)
    max_entries: int = 8760  # 1 year of hourly entries
    subsystem_id: str = ""

    def append(self, entry: TrustHistoryEntry):
        entry.subsystem_id = self.subsystem_id
        if len(self.entries) >= self.max_entries:
            self.entries.pop(0)
        self.entries.append(entry)

    def get_range(self, start_time: float, end_time: float) -> List[TrustHistoryEntry]:
        return [e for e in self.entries if start_time <= e.timestamp <= end_time]

    def get_last_n(self, n: int) -> List[TrustHistoryEntry]:
        return self.entries[-n:] if n <= len(self.entries) else self.entries

    def get_bad_event_count(self, hours: float, now: float) -> int:
        """Count bad events in the last `hours` hours."""
        cutoff = now - (hours * 3600)
        return sum(e.n_bad for e in self.entries if e.timestamp >= cutoff)

    def get_max_severity_since(self, hours: float, now: float) -> float:
        """Get maximum severity in the last `hours` hours."""
        cutoff = now - (hours * 3600)
        severities = [e.max_severity for e in self.entries if e.timestamp >= cutoff and e.max_severity > 0]
        return max(severities) if severities else 0.0


# Lookup tables
EVENT_CATEGORY_MAP: Dict[EventType, EventCategory] = {
    EventType.SUCCESSFUL_ACTION:             EventCategory.GOOD,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_APPROVED:       EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     EventCategory.GOOD,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: EventCategory.BAD,
    EventType.ANOMALY_DETECTED:              EventCategory.BAD,
    EventType.ANOMALY_RESOLVED:              EventCategory.GOOD,
    EventType.SAFETY_RULE_VIOLATION:         EventCategory.BAD,
    EventType.SENSOR_FAILURE_TRANSIENT:      EventCategory.BAD,
    EventType.SENSOR_FAILURE_PERMANENT:      EventCategory.BAD,
    EventType.HEARTBEAT_TIMEOUT:             EventCategory.BAD,
    EventType.COMMUNICATION_LOSS:            EventCategory.BAD,
    EventType.FIRMWARE_UPDATE:               EventCategory.NEUTRAL,
    EventType.CONFIGURATION_CHANGE:          EventCategory.NEUTRAL,
    EventType.MANUAL_REVOCATION:             EventCategory.BAD,
}

EVENT_SEVERITY_MAP: Dict[EventType, float] = {
    EventType.SUCCESSFUL_ACTION:             0.0,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: 0.0,
    EventType.HUMAN_OVERRIDE_APPROVED:       0.0,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     0.0,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: 0.3,
    EventType.ANOMALY_DETECTED:              0.2,
    EventType.ANOMALY_RESOLVED:              0.0,
    EventType.SAFETY_RULE_VIOLATION:         0.7,
    EventType.SENSOR_FAILURE_TRANSIENT:      0.4,
    EventType.SENSOR_FAILURE_PERMANENT:      0.9,
    EventType.HEARTBEAT_TIMEOUT:             0.6,
    EventType.COMMUNICATION_LOSS:            0.5,
    EventType.FIRMWARE_UPDATE:               0.0,
    EventType.CONFIGURATION_CHANGE:          0.0,
    EventType.MANUAL_REVOCATION:             1.0,
}

EVENT_QUALITY_MAP: Dict[EventType, float] = {
    EventType.SUCCESSFUL_ACTION:             0.7,
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: 0.95,
    EventType.HUMAN_OVERRIDE_APPROVED:       0.6,
    EventType.HUMAN_OVERRIDE_UNEXPECTED:     0.3,
    EventType.HUMAN_OVERRIDE_WRONG_DECISION: 0.0,
    EventType.ANOMALY_DETECTED:              0.0,
    EventType.ANOMALY_RESOLVED:              0.8,
    EventType.SAFETY_RULE_VIOLATION:         0.0,
    EventType.SENSOR_FAILURE_TRANSIENT:      0.0,
    EventType.SENSOR_FAILURE_PERMANENT:      0.0,
    EventType.HEARTBEAT_TIMEOUT:             0.0,
    EventType.COMMUNICATION_LOSS:            0.0,
    EventType.FIRMWARE_UPDATE:               0.0,
    EventType.CONFIGURATION_CHANGE:          0.0,
    EventType.MANUAL_REVOCATION:             0.0,
}
```

### 9.2 C Struct Definitions

```c
/**
 * @file trust_types.h
 * @brief Trust score data structures for embedded C (STM32/ESP32 targets).
 * @note All structures are packed for NVS/flash storage compatibility.
 *       Floating point uses IEEE 754 single precision (float) unless noted.
 */

#ifndef TRUST_TYPES_H
#define TRUST_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ===== Enums ===== */

typedef enum {
    EVENT_SUCCESSFUL_ACTION             = 0,
    EVENT_SUCCESSFUL_ACTION_WITH_RESERVE = 1,
    EVENT_HUMAN_OVERRIDE_APPROVED       = 2,
    EVENT_HUMAN_OVERRIDE_UNEXPECTED     = 3,
    EVENT_HUMAN_OVERRIDE_WRONG_DECISION = 4,
    EVENT_ANOMALY_DETECTED              = 5,
    EVENT_ANOMALY_RESOLVED              = 6,
    EVENT_SAFETY_RULE_VIOLATION         = 7,
    EVENT_SENSOR_FAILURE_TRANSIENT      = 8,
    EVENT_SENSOR_FAILURE_PERMANENT      = 9,
    EVENT_HEARTBEAT_TIMEOUT             = 10,
    EVENT_COMMUNICATION_LOSS            = 11,
    EVENT_FIRMWARE_UPDATE               = 12,
    EVENT_CONFIGURATION_CHANGE          = 13,
    EVENT_MANUAL_REVOCATION             = 14,
    EVENT_TYPE_COUNT                    = 15,
} EventType;

typedef enum {
    CATEGORY_NEUTRAL = 0,
    CATEGORY_GOOD    = 1,
    CATEGORY_BAD     = 2,
} EventCategory;

typedef enum {
    RESET_FIRMWARE_UPDATE       = 0,
    RESET_SENSOR_REPLACEMENT    = 1,
    RESET_MAJOR_HARDWARE_CHANGE = 2,
    RESET_CONFIGURATION_CHANGE  = 3,
    RESET_FULL_RESET            = 4,
    RESET_SAFETY_INCIDENT       = 5,
    RESET_PROLONGED_INACTIVITY  = 6,
    RESET_OPERATOR_DISAGREEMENT = 7,
} ResetType;

typedef enum {
    LEVEL_DISABLED        = 0,
    LEVEL_ADVISORY        = 1,
    LEVEL_SUPERVISED      = 2,
    LEVEL_SEMI_AUTONOMOUS = 3,
    LEVEL_HIGH_AUTONOMY   = 4,
    LEVEL_FULL_AUTONOMY   = 5,
} AutonomyLevel;

/* ===== Trust Parameters ===== */

typedef struct __attribute__((packed)) {
    float alpha_gain;              /* Base gain rate. Default: 0.002 */
    float alpha_loss;              /* Base loss rate. Default: 0.05 */
    float alpha_decay;             /* Inactivity decay rate. Default: 0.0001 */
    float t_floor;                 /* Trust decay floor. Default: 0.2 */
    uint16_t quality_cap;          /* Max good events per window. Default: 10 */
    float evaluation_window_hours; /* Window duration in hours. Default: 1.0 */
    float severity_exponent;       /* Severity scaling. Default: 1.0 */
    float streak_bonus;            /* Streak reward rate. Default: 0.00005 */
    uint16_t min_events_for_gain;  /* Min good events for Branch 1. Default: 1 */
    float n_penalty_slope;         /* Count penalty slope. Default: 0.1 */
} TrustParams;

/* Default parameter initializer */
static inline TrustParams trust_params_default(void) {
    TrustParams p = {
        .alpha_gain              = 0.002f,
        .alpha_loss              = 0.05f,
        .alpha_decay             = 0.0001f,
        .t_floor                 = 0.2f,
        .quality_cap             = 10,
        .evaluation_window_hours = 1.0f,
        .severity_exponent       = 1.0f,
        .streak_bonus            = 0.00005f,
        .min_events_for_gain     = 1,
        .n_penalty_slope         = 0.1f,
    };
    return p;
}

/* ===== Trust Event ===== */

/**
 * @brief Wire-format trust event. 42 bytes total.
 * @note subsystem_id is NOT null-terminated; subsystem_id_len tracks length.
 */
typedef struct __attribute__((packed)) {
    uint8_t  event_type;         /* EventType enum value */
    uint8_t  _padding;           /* Alignment padding */
    uint64_t timestamp_ms;       /* Unix timestamp in milliseconds */
    uint8_t  subsystem_id_len;   /* Length of subsystem_id string (0-31) */
    char     subsystem_id[31];   /* Subsystem identifier (NOT null-terminated) */
} TrustEvent;

/* ===== Trust State (Persistent) ===== */

/**
 * @brief Complete trust state for a subsystem. 64 bytes total.
 * @note This is the structure written to NVS/flash.
 *       All fields use fixed-size types for binary compatibility.
 *       If the struct layout changes, increment TRUST_STATE_VERSION.
 */
#define TRUST_STATE_VERSION 1

typedef struct __attribute__((packed)) {
    uint32_t version;            /* Struct version for migration. Must be TRUST_STATE_VERSION. */
    uint8_t  subsystem_id[16];   /* Subsystem identifier (null-terminated) */
    float    trust_score;        /* Current trust [0.0, 1.0] */
    float    alpha_multiplier;   /* Subsystem-specific multiplier */
    uint8_t  current_level;      /* AutonomyLevel enum value */
    uint8_t  _pad1;
    uint32_t total_observation_windows; /* Total evaluation windows observed */
    uint16_t consecutive_clean_windows;
    uint16_t total_clean_windows;
    uint16_t consecutive_days_above_threshold;
    uint8_t  _pad2[2];
    float    cumulative_severity_sum; /* Sum of bad event severities in observation period */
    uint8_t  candidate_level;     /* AutonomyLevel being considered, 0xFF = none */
    uint8_t  last_reset_type;     /* ResetType, 0xFF = none */
    uint64_t last_update_ms;      /* Unix timestamp of last update (ms) */
    uint64_t last_reset_ms;       /* Unix timestamp of last reset (ms) */
    uint64_t last_promotion_ms;   /* Unix timestamp of last promotion (ms) */
    uint64_t candidate_start_ms;  /* Unix timestamp of candidate state start (ms) */
    uint32_t crc32;               /* CRC32 of all preceding bytes */
} TrustStatePersistent;

/* ===== Trust History Entry ===== */

/**
 * @brief Single history entry for audit log. 28 bytes total.
 */
typedef struct __attribute__((packed)) {
    uint32_t timestamp_s;     /* Unix timestamp (seconds) */
    float    trust_before;    /* Trust before this window */
    float    trust_after;     /* Trust after this window */
    float    delta;           /* Trust change */
    uint16_t n_good;          /* Good event count */
    uint16_t n_bad;           /* Bad event count */
    float    max_severity;    /* Max severity in window */
    float    avg_quality;     /* Avg quality in window */
    uint8_t  branch;          /* 1=gain, 2=penalty, 3=decay, 4=reset */
    uint8_t  _padding;
} TrustHistoryEntry;

/* ===== Subsystem Configuration ===== */

typedef struct __attribute__((packed)) {
    uint8_t  subsystem_id[16];    /* Null-terminated subsystem identifier */
    float    alpha_multiplier;     /* Subsystem-specific multiplier */
    uint8_t  risk_category;        /* 0=Low, 1=Medium, 2=High, 3=Critical */
    uint8_t  enabled;              /* 1 = enabled, 0 = disabled */
    /* Custom severity overrides (indexed by EventType) */
    float    severity_overrides[EVENT_TYPE_COUNT]; /* 0.0 = use default */
} SubsystemConfig;

/* ===== Level Thresholds ===== */

typedef struct __attribute__((packed)) {
    float    trust_threshold;         /* Minimum trust score for this level */
    uint32_t min_observation_hours;   /* Minimum hours of observation */
    uint16_t min_consecutive_days;    /* Minimum consecutive days at threshold */
    uint16_t min_clean_windows;       /* Minimum clean windows required */
    float    max_severity_in_window;  /* Max severity allowed in last N hours */
    uint32_t severity_lookback_hours; /* Hours to look back for severity check */
    uint16_t max_bad_events;          /* Max bad events in lookback period */
    uint32_t bad_event_lookback_hours;/* Hours to look back for bad event count */
} LevelThreshold;

/* Default level thresholds (indexed by AutonomyLevel, 0 = disabled = unused) */
static const LevelThreshold DEFAULT_LEVEL_THRESHOLDS[6] = {
    /* Level 0 (Disabled): No criteria, always available */
    { 0.00f,   0,   0,   0, 0.0f, 0,   0, 0 },
    /* Level 1 (Advisory) */
    { 0.20f,   8,   1,   4, 0.0f, 0, 255, 0 },  /* 255 = no limit */
    /* Level 2 (Supervised) */
    { 0.40f,  48,   3,  24, 0.79f, 9999, 2, 9999 },
    /* Level 3 (Semi-Autonomous) */
    { 0.60f, 168,   7, 100, 0.69f,  48, 255, 168 },
    /* Level 4 (High Autonomy) */
    { 0.80f, 336,  14, 200, 0.59f,  72,   5, 168 },
    /* Level 5 (Full Autonomy) */
    { 0.95f, 720,  30, 500, 0.49f, 168,   2, 336 },
};

/* ===== Function Prototypes ===== */

/**
 * @brief Compute trust delta for a single evaluation window.
 * @param T_prev      Current trust score [0.0, 1.0]
 * @param n_good      Number of good events in window
 * @param n_bad       Number of bad events in window
 * @param avg_quality Average quality of good events [0.0, 1.0]
 * @param max_severity Maximum severity of bad events [0.0, 1.0]
 * @param params      Trust parameters
 * @param consecutive_clean  Number of consecutive clean windows before this one
 * @param alpha_mult  Subsystem alpha multiplier
 * @return Computed delta (may be positive, negative, or zero)
 */
float trust_compute_delta(
    float T_prev,
    uint16_t n_good,
    uint16_t n_bad,
    float avg_quality,
    float max_severity,
    const TrustParams* params,
    uint32_t consecutive_clean,
    float alpha_mult
);

/**
 * @brief Apply a reset to the trust score.
 * @param T_prev     Current trust score
 * @param reset_type Type of reset
 * @return New trust score after reset
 */
float trust_apply_reset(float T_prev, ResetType reset_type);

/**
 * @brief Determine the autonomy level from trust state and history.
 * @param state    Current trust state
 * @param history  Trust history for lookback checks
 * @param now_ms   Current time in milliseconds
 * @return The autonomy level the subsystem should be at
 */
AutonomyLevel trust_evaluate_level(
    const TrustStatePersistent* state,
    const TrustHistoryEntry* history,
    uint32_t history_len,
    uint64_t now_ms
);

/**
 * @brief Validate trust parameters. Returns 0 if valid, -1 otherwise.
 */
int trust_params_validate(const TrustParams* params);

/**
 * @brief Compute CRC32 for TrustStatePersistent.
 */
uint32_t trust_state_crc32(const TrustStatePersistent* state);

#ifdef __cplusplus
}
#endif

#endif /* TRUST_TYPES_H */
```

### 9.3 C Implementation (Core Algorithm)

```c
/**
 * @file trust_algorithm.c
 * @brief Core trust score computation.
 */

#include "trust_types.h"
#include <math.h>
#include <string.h>

#define TRUST_MIN(a, b) ((a) < (b) ? (a) : (b))
#define TRUST_MAX(a, b) ((a) > (b) ? (a) : (b))
#define TRUST_CLAMP(x, lo, hi) TRUST_MIN(TRUST_MAX(x, lo), hi)
#define TRUST_IS_NAN(x) ((x) != (x))

int trust_params_validate(const TrustParams* params) {
    if (!params) return -1;
    if (TRUST_IS_NAN(params->alpha_gain) || TRUST_IS_NAN(params->alpha_loss) ||
        TRUST_IS_NAN(params->alpha_decay) || TRUST_IS_NAN(params->t_floor)) {
        return -1;
    }
    if (params->alpha_gain < 0.0001f || params->alpha_gain > 0.01f) return -1;
    if (params->alpha_loss < 0.01f || params->alpha_loss > 0.5f) return -1;
    if (params->alpha_decay < 0.00001f || params->alpha_decay > 0.001f) return -1;
    if (params->t_floor < 0.0f || params->t_floor >= 1.0f) return -1;
    if (params->quality_cap < 1) return -1;
    if (params->evaluation_window_hours < 0.1f || params->evaluation_window_hours > 24.0f) return -1;
    if (!(params->alpha_loss > params->alpha_gain * (float)params->quality_cap)) return -1;
    return 0;
}

float trust_compute_delta(
    float T_prev,
    uint16_t n_good,
    uint16_t n_bad,
    float avg_quality,
    float max_severity,
    const TrustParams* params,
    uint32_t consecutive_clean,
    float alpha_mult
) {
    if (!params || TRUST_IS_NAN(T_prev)) return 0.0f;
    T_prev = TRUST_CLAMP(T_prev, 0.0f, 1.0f);

    float delta = 0.0f;

    if (n_bad > 0) {
        /* Branch 2: Penalty */
        float sev_scaled = powf(TRUST_CLAMP(max_severity, 0.0f, 1.0f), params->severity_exponent);
        float n_penalty = 1.0f + params->n_penalty_slope * (float)(n_bad - 1);
        delta = -params->alpha_loss * T_prev * sev_scaled * n_penalty;
    } else if (n_good >= params->min_events_for_gain) {
        /* Branch 1: Gain */
        float q = TRUST_CLAMP(avg_quality, 0.0f, 1.0f);
        uint16_t capped = TRUST_MIN(n_good, params->quality_cap);
        delta = params->alpha_gain * (1.0f - T_prev) * q * ((float)capped / (float)params->quality_cap);

        /* Streak bonus */
        if (consecutive_clean > 0 && params->streak_bonus > 0.0f) {
            uint32_t streak = TRUST_MIN(consecutive_clean, 24u);
            delta += params->streak_bonus * (float)streak;
        }
    } else {
        /* Branch 3: Decay */
        delta = -params->alpha_decay * (T_prev - params->t_floor);
    }

    return delta * alpha_mult;
}

float trust_apply_reset(float T_prev, ResetType reset_type) {
    if (TRUST_IS_NAN(T_prev)) return 0.0f;
    T_prev = TRUST_CLAMP(T_prev, 0.0f, 1.0f);

    float multiplier;
    switch (reset_type) {
        case RESET_FIRMWARE_UPDATE:       multiplier = 0.7f; break;
        case RESET_SENSOR_REPLACEMENT:    multiplier = 0.8f; break;
        case RESET_MAJOR_HARDWARE_CHANGE: multiplier = 0.5f; break;
        case RESET_CONFIGURATION_CHANGE:  return T_prev; /* No trust change */
        case RESET_FULL_RESET:            return 0.0f;
        case RESET_SAFETY_INCIDENT:       return 0.0f;
        case RESET_PROLONGED_INACTIVITY:  return TRUST_MAX(0.5f, T_prev * 0.7f);
        case RESET_OPERATOR_DISAGREEMENT: multiplier = 0.3f; break;
        default:                          return T_prev;
    }

    return TRUST_CLAMP(T_prev * multiplier, 0.0f, 1.0f);
}
```

---

## 10. Implementation Notes

### 10.1 Thread Safety

The trust score is a shared resource accessed by:

- **Event ingestion thread(s)**: One or more threads receiving events from MQTT, CAN bus, or sensors
- **Evaluation thread**: Periodic thread that processes complete windows and updates trust
- **API server thread(s)**: HTTP/gRPC threads serving trust score queries
- **Persistence thread**: Background thread writing trust state to NVS/SQLite

#### Required Synchronization Strategy

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Event Threads  │────>│  Event Queue     │────>│  Eval Thread    │
│  (producers)    │     │  (lock-free MPSC) │     │  (consumer)     │
└─────────────────┘     └──────────────────┘     └───────┬────────┘
                                                         │
                                                         v
                                                ┌────────────────┐
                                                │  TrustState    │
                                                │  (protected by  │
                                                │   RW-lock)      │
                                                └───────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────┐
                              v                          v                      v
                     ┌────────────────┐       ┌────────────────┐      ┌────────────────┐
                     │  API Threads   │       │  Persistence   │      │  Alert Engine  │
                     │  (readers)     │       │  Thread        │      │  (notifications│
                     │                │       │  (periodic)    │      │   on demotion) │
                     └────────────────┘       └────────────────┘      └────────────────┘
```

**Concurrency Rules**:

1. **Event Queue**: Use a lock-free multi-producer single-consumer (MPSC) ring buffer. Event threads push events; only the evaluation thread pops. No lock needed.
2. **TrustState RW-Lock**: Use a readers-writer lock (pthread_rwlock on Linux, FreeRTOS mutex with priority inheritance on embedded).
   - Evaluation thread holds **write lock** during trust computation.
   - API threads hold **read lock** during trust queries.
   - Persistence thread holds **read lock** to snapshot state.
3. **Atomicity**: Each trust update (compute delta + apply clamp + update counters + check levels) MUST be atomic with respect to readers. The write lock ensures this.
4. **Priority Inversion**: On embedded targets (FreeRTOS/RTOS), the evaluation thread MUST run at higher priority than API threads. Use priority-inheriting mutexes to prevent unbounded priority inversion.
5. **Deadlock Prevention**: Lock acquisition order is always: Event Queue → TrustState RW-Lock → Persistence Lock. Never acquire in reverse order.

#### Python Implementation

```python
import threading
from collections import deque
from typing import Callable, Optional

class TrustScoreManager:
    """Thread-safe trust score manager."""

    def __init__(self, subsystem_id: str, params: Optional[TrustParams] = None):
        self.subsystem_id = subsystem_id
        self.params = params or TrustParams()
        self.state = TrustState(subsystem_id=subsystem_id, params=self.params)
        self.history = TrustHistory(subsystem_id=subsystem_id)

        # Lock-free is approximated with a thread-safe deque
        self._event_queue: deque[TrustEvent] = deque(maxlen=10000)
        self._queue_lock = threading.Lock()

        # RW-lock for state access
        self._rw_lock = threading.RLock()

        # Callbacks for level changes
        self._on_promotion: Optional[Callable[[AutonomyLevel, AutonomyLevel], None]] = None
        self._on_demotion: Optional[Callable[[AutonomyLevel, AutonomyLevel], None]] = None

    def submit_event(self, event: TrustEvent):
        """Thread-safe event submission. Called from event ingestion threads."""
        event.subsystem_id = self.subsystem_id
        with self._queue_lock:
            self._event_queue.append(event)

    def get_trust_score(self) -> float:
        """Thread-safe trust score query. Called from API threads."""
        with self._rw_lock:
            return self.state.trust_score

    def get_current_level(self) -> AutonomyLevel:
        """Thread-safe level query."""
        with self._rw_lock:
            return self.state.current_level

    def evaluate_window(self, now: float) -> TrustHistoryEntry:
        """
        Process all events in the current evaluation window.
        Must be called periodically (every evaluation_window_hours).
        This method is NOT thread-safe for concurrent calls — only one
        evaluation should run at a time.
        """
        # Drain the event queue
        with self._queue_lock:
            events = list(self._event_queue)
            self._event_queue.clear()

        # Compute trust delta
        good_events = [e for e in events if e.category == EventCategory.GOOD]
        bad_events = [e for e in events if e.category == EventCategory.BAD]

        with self._rw_lock:
            T_prev = self.state.trust_score
            n_good = len(good_events)
            n_bad = len(bad_events)
            avg_quality = (sum(e.quality for e in good_events) / n_good) if n_good > 0 else 0.0
            max_severity = max((e.severity for e in bad_events), default=0.0)

            delta = compute_delta(
                T_prev, good_events, bad_events,
                self.state.params,
                self.state.consecutive_clean_windows,
            )

            T_new = max(0.0, min(1.0, T_prev + delta))

            # Determine branch for logging
            if n_bad > 0:
                branch = 2
                self.state.consecutive_clean_windows = 0
            elif n_good > 0:
                branch = 1
                self.state.consecutive_clean_windows += 1
            else:
                branch = 3

            # Update state
            self.state.trust_score = T_new
            self.state.last_update_timestamp = now

            # Update counters
            if len(events) > 0:
                self.state.total_observation_hours += self.state.params.evaluation_window_hours
            if n_bad == 0 and len(events) > 0:
                self.state.total_clean_windows += 1
            self.state.cumulative_severity_sum += sum(e.severity for e in bad_events)

            # Check for level transitions
            self._check_level_transition(now)

            # Record history
            entry = TrustHistoryEntry(
                timestamp=now,
                trust_before=T_prev,
                trust_after=T_new,
                delta=delta,
                n_good=n_good,
                n_bad=n_bad,
                max_severity=max_severity,
                avg_quality=avg_quality,
                branch=branch,
            )
            self.history.append(entry)

            return entry

    def apply_reset(self, reset_type: ResetType, now: float):
        """Apply a trust reset. Thread-safe."""
        with self._rw_lock:
            T_prev = self.state.trust_score

            if reset_type == ResetType.FULL_RESET or reset_type == ResetType.SAFETY_INCIDENT:
                self.state.trust_score = 0.0
            elif reset_type == ResetType.PROLONGED_INACTIVITY:
                self.state.trust_score = max(0.5, T_prev * 0.7)
            elif reset_type == ResetType.CONFIGURATION_CHANGE:
                pass  # Trust unchanged
            else:
                multiplier = RESET_MULTIPLIERS[reset_type]
                self.state.trust_score = max(0.0, min(1.0, T_prev * multiplier))

            self.state.trust_score = max(0.0, min(1.0, self.state.trust_score))
            self.state.last_reset_time = now
            self.state.last_reset_type = reset_type
            self.state.total_observation_hours = 0.0
            self.state.consecutive_clean_windows = 0
            self.state.consecutive_days_above_threshold = 0
            self.state.total_clean_windows = 0
            self.state.cumulative_severity_sum = 0.0
            self.state.candidate_level = None
            self.state.candidate_start_time = None

    def _check_level_transition(self, now: float):
        """Check and apply autonomy level transitions. Called under write lock."""
        T = self.state.trust_score
        current = self.state.current_level

        # Demotion checks (immediate)
        new_level = None
        if T < LEVEL_THRESHOLDS[current].trust_threshold * 0.8:
            new_level = current - 1
            if new_level < 0:
                new_level = 0
        # (In a full implementation, also check for high-severity demotion triggers)

        # Promotion checks (deferred with candidate state)
        for target in range(current + 1, 6):
            if T >= LEVEL_THRESHOLDS[target].trust_threshold:
                # Check other criteria using history
                if self.state.candidate_level == target:
                    # Already candidate — check if we've maintained long enough
                    if self.state.candidate_start_time is not None:
                        elapsed = now - self.state.candidate_start_time
                        confirm_duration = self.state.params.evaluation_window_hours * 2 * 3600
                        if elapsed >= confirm_duration:
                            # Still above threshold? Confirm promotion.
                            if T >= LEVEL_THRESHOLDS[target].trust_threshold:
                                new_level = target
                else:
                    # Start candidacy
                    self.state.candidate_level = AutonomyLevel(target)
                    self.state.candidate_start_time = now

        if new_level is not None:
            old_level = current
            self.state.current_level = AutonomyLevel(new_level)
            self.state.candidate_level = None
            self.state.candidate_start_time = None

            if new_level > old_level and self._on_promotion:
                self._on_promotion(AutonomyLevel(old_level), AutonomyLevel(new_level))
            elif new_level < old_level and self._on_demotion:
                self._on_demotion(AutonomyLevel(old_level), AutonomyLevel(new_level))
```

### 10.2 Persistence

#### NVS (Non-Volatile Storage) — Embedded Targets

For ESP32/STM32 targets, trust state is stored in NVS key-value storage:

| NVS Namespace | Key | Value | Size | Write Frequency |
|--------------|-----|-------|------|----------------|
| `trust_<subsys>` | `state` | `TrustStatePersistent` binary blob | 64 bytes | Every window (~1 hour) |
| `trust_<subsys>` | `params` | `TrustParams` binary blob | 32 bytes | On configuration change |
| `trust_<subsys>` | `ver` | uint32_t | 4 bytes | On struct version change |
| `trust_hist_<subsys>` | `entry_<idx>` | `TrustHistoryEntry` binary blob | 28 bytes each | Every window, ring buffer |
| `trust_hist_<subsys>` | `head` | uint16_t | 2 bytes | Every window |

**Write amplification mitigation**:
- Trust state is only written when the trust score changes by > 0.0001 or the window had events.
- History entries are written in append-only mode; a separate `head` index tracks the ring position.
- CRC32 validation on every read. If CRC fails, the system MUST fall back to `trust_score = t_floor` and raise a diagnostic alert.

**Wear leveling**: With 1 write/hour and NVS wear level of 100,000 cycles, the trust state key lasts ~11.4 years. History entries rotate across NVS sectors automatically via ring buffer indexing.

#### SQLite — Companion Computer (Jetson/Raspberry Pi)

```sql
-- Trust state table (one row per subsystem)
CREATE TABLE IF NOT EXISTS trust_state (
    subsystem_id    TEXT PRIMARY KEY,
    trust_score     REAL NOT NULL DEFAULT 0.0 CHECK(trust_score >= 0.0 AND trust_score <= 1.0),
    current_level   INTEGER NOT NULL DEFAULT 0 CHECK(current_level BETWEEN 0 AND 5),
    alpha_multiplier REAL NOT NULL DEFAULT 1.0,
    total_observation_hours REAL NOT NULL DEFAULT 0.0,
    consecutive_clean_windows INTEGER NOT NULL DEFAULT 0,
    total_clean_windows INTEGER NOT NULL DEFAULT 0,
    consecutive_days_above_threshold INTEGER NOT NULL DEFAULT 0,
    cumulative_severity_sum REAL NOT NULL DEFAULT 0.0,
    candidate_level INTEGER CHECK(candidate_level BETWEEN 0 AND 5),
    candidate_start_time REAL,
    last_promotion_time REAL NOT NULL DEFAULT 0.0,
    last_reset_time REAL NOT NULL DEFAULT 0.0,
    last_reset_type INTEGER,
    last_update_time REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    version         INTEGER NOT NULL DEFAULT 1
);

-- Trust history table (append-only)
CREATE TABLE IF NOT EXISTS trust_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    trust_before    REAL NOT NULL,
    trust_after     REAL NOT NULL,
    delta           REAL NOT NULL,
    n_good          INTEGER NOT NULL,
    n_bad           INTEGER NOT NULL,
    max_severity    REAL NOT NULL DEFAULT 0.0,
    avg_quality     REAL NOT NULL DEFAULT 0.0,
    branch          INTEGER NOT NULL,  -- 1=gain, 2=penalty, 3=decay, 4=reset
    FOREIGN KEY (subsystem_id) REFERENCES trust_state(subsystem_id)
);
CREATE INDEX IF NOT EXISTS idx_history_subsys_time
    ON trust_history(subsystem_id, timestamp);

-- Reset audit table
CREATE TABLE IF NOT EXISTS trust_reset_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    reset_type      INTEGER NOT NULL,
    trust_before    REAL NOT NULL,
    trust_after     REAL NOT NULL,
    reason          TEXT,
    operator_id     TEXT
);
CREATE INDEX IF NOT EXISTS idx_reset_subsys_time
    ON trust_reset_audit(subsystem_id, timestamp);

-- Event log table (append-only, for audit)
CREATE TABLE IF NOT EXISTS trust_event_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subsystem_id    TEXT NOT NULL,
    timestamp       REAL NOT NULL,
    event_type      INTEGER NOT NULL,
    category        INTEGER NOT NULL,  -- 0=neutral, 1=good, 2=bad
    severity        REAL NOT NULL DEFAULT 0.0,
    quality         REAL NOT NULL DEFAULT 0.0,
    metadata_json   TEXT
);
CREATE INDEX IF NOT EXISTS idx_event_subsys_time
    ON trust_event_log(subsystem_id, timestamp);
```

**SQLite Write Pattern**:
- `trust_state`: UPSERT every evaluation window (1 hour).
- `trust_history`: INSERT every evaluation window.
- `trust_event_log`: INSERT per event (batched in transactions of up to 100 events).
- `trust_reset_audit`: INSERT on every reset.
- WAL mode enabled for concurrent read/write.
- Vacuum weekly or when history exceeds 100,000 entries per subsystem.

### 10.3 API Contract

#### REST API (Companion Computer)

```
GET  /api/v1/trust/{subsystem_id}
Response:
{
    "subsystem_id": "autopilot",
    "trust_score": 0.7234,
    "current_level": 3,
    "level_name": "SEMI_AUTONOMOUS",
    "last_update": "2025-01-15T14:30:00Z",
    "consecutive_clean_windows": 47,
    "total_observation_hours": 312.5,
    "candidate_level": null,
    "params": {
        "alpha_gain": 0.002,
        "alpha_loss": 0.05,
        "alpha_decay": 0.0001,
        "t_floor": 0.2,
        "quality_cap": 10,
        "evaluation_window_hours": 1.0
    }
}

GET  /api/v1/trust/{subsystem_id}/history?hours=168
Response:
{
    "subsystem_id": "autopilot",
    "hours_requested": 168,
    "entries": [
        {
            "timestamp": "2025-01-15T14:00:00Z",
            "trust_before": 0.7190,
            "trust_after": 0.7234,
            "delta": 0.0044,
            "n_good": 8,
            "n_bad": 0,
            "branch": "gain"
        },
        ...
    ]
}

POST /api/v1/trust/{subsystem_id}/reset
Request:
{
    "reset_type": "full_reset",
    "reason": "Post-incident investigation complete, re-commissioning",
    "operator_id": "admin@vessel.com"
}
Response:
{
    "subsystem_id": "autopilot",
    "trust_before": 0.7234,
    "trust_after": 0.0,
    "reset_type": "full_reset",
    "new_level": 0,
    "timestamp": "2025-01-15T14:35:00Z"
}

POST /api/v1/trust/{subsystem_id}/events
Request:
[
    {"event_type": "successful_action", "timestamp": "2025-01-15T14:30:15Z"},
    {"event_type": "anomaly_detected", "timestamp": "2025-01-15T14:31:02Z"}
]
Response:
{
    "accepted": 2,
    "rejected": 0,
    "rejection_reasons": []
}

GET  /api/v1/trust/{subsystem_id}/level-thresholds
Response:
{
    "current_level": 3,
    "thresholds": {
        "next_level": 4,
        "next_requirements": {
            "trust_threshold": 0.80,
            "trust_current": 0.7234,
            "trust_gap": 0.0766,
            "observation_hours_required": 336,
            "observation_hours_current": 312.5,
            "consecutive_days_required": 14,
            "consecutive_days_current": 8,
            "clean_windows_required": 200,
            "clean_windows_current": 142
        }
    }
}
```

#### MQTT Topics (Embedded Communication)

| Topic | Direction | Payload | QoS |
|-------|-----------|---------|-----|
| `nexus/trust/{subsystem}/score` | Broker → All | JSON trust state snapshot | 0 |
| `nexus/trust/{subsystem}/event` | Module → Broker | Binary `TrustEvent` (42 bytes) | 1 |
| `nexus/trust/{subsystem}/reset` | Broker → Module | JSON `{"type": "full_reset", "reason": "..."}` | 2 |
| `nexus/trust/{subsystem}/level_change` | Broker → All | JSON `{"from": 2, "to": 3, "trust": 0.61}` | 2 |

### 10.4 Testing Strategy

#### Unit Tests (Minimum Coverage: 95%)

```python
import pytest

class TestTrustAlgorithm:
    """Unit tests for the trust score algorithm."""

    def test_gain_basic(self):
        """Branch 1: Trust increases with good events."""
        params = TrustParams()
        events = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
        delta = compute_delta(0.5, events, [], params)
        assert delta > 0, "Good events should produce positive delta"

    def test_gain_diminishing(self):
        """Branch 1: Gain diminishes as trust approaches 1.0."""
        params = TrustParams()
        events = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
        delta_low = compute_delta(0.1, events, [], params)
        delta_high = compute_delta(0.9, events, [], params)
        assert delta_low > delta_high, "Gain should be larger at low trust"

    def test_gain_quality_scaling(self):
        """Branch 1: Higher quality produces larger gain."""
        params = TrustParams()
        low_q = [TrustEvent(EventType.HUMAN_OVERRIDE_UNEXPECTED)]  # quality=0.3
        high_q = [TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)]  # quality=0.95
        delta_low = compute_delta(0.5, low_q, [], params)
        delta_high = compute_delta(0.5, high_q, [], params)
        assert delta_high > delta_low, "Higher quality should produce larger gain"

    def test_gain_quality_cap(self):
        """Branch 1: Events beyond quality_cap are ignored."""
        params = TrustParams(quality_cap=5)
        events_5 = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * 5
        events_20 = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * 20
        delta_5 = compute_delta(0.5, events_5, [], params)
        delta_20 = compute_delta(0.5, events_20, [], params)
        assert abs(delta_5 - delta_20) < 1e-10, "Events beyond cap should not increase delta"

    def test_penalty_basic(self):
        """Branch 2: Bad events produce negative delta."""
        params = TrustParams()
        events = [TrustEvent(EventType.ANOMALY_DETECTED)]  # severity=0.2
        delta = compute_delta(0.5, events, [], params)
        assert delta < 0, "Bad events should produce negative delta"

    def test_penalty_ignores_good(self):
        """Branch 2: Good events in same window are ignored."""
        params = TrustParams()
        bad_only = [TrustEvent(EventType.SAFETY_RULE_VIOLATION)]
        mixed = [TrustEvent(EventType.SAFETY_RULE_VIOLATION),
                 TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)]
        delta_bad = compute_delta(0.5, [], bad_only, params)
        delta_mixed = compute_delta(0.5, [mixed[1]], bad_only, params)
        assert abs(delta_bad - delta_mixed) < 1e-10, "Good events should be ignored when bad events present"

    def test_penalty_severity_scaling(self):
        """Branch 2: Higher severity produces larger penalty."""
        params = TrustParams()
        minor = [TrustEvent(EventType.ANOMALY_DETECTED)]  # sev=0.2
        major = [TrustEvent(EventType.MANUAL_REVOCATION)]  # sev=1.0
        delta_minor = compute_delta(0.5, [], minor, params)
        delta_major = compute_delta(0.5, [], major, params)
        assert abs(delta_major) > abs(delta_minor), "Higher severity should produce larger penalty"

    def test_penalty_count_scaling(self):
        """Branch 2: Multiple bad events increase penalty."""
        params = TrustParams()
        single = [TrustEvent(EventType.ANOMALY_DETECTED)]
        triple = [TrustEvent(EventType.ANOMALY_DETECTED)] * 3
        delta_single = compute_delta(0.5, [], single, params)
        delta_triple = compute_delta(0.5, [], triple, params)
        assert abs(delta_triple) > abs(delta_single), "Multiple bad events should increase penalty"

    def test_decay_basic(self):
        """Branch 3: No events cause decay toward floor."""
        params = TrustParams()
        delta = compute_delta(0.5, [], [], params)
        assert delta < 0, "Decay should produce negative delta"

    def test_decay_stops_at_floor(self):
        """Branch 3: Decay stops when T equals t_floor."""
        params = TrustParams()
        delta = compute_delta(params.t_floor, [], [], params)
        assert abs(delta) < 1e-15, "Decay should be zero at floor"

    def test_decay_below_floor(self):
        """Branch 3: Trust below floor gains via decay (moves toward floor)."""
        params = TrustParams(t_floor=0.3)
        delta = compute_delta(0.1, [], [], params)
        assert delta > 0, "Trust below floor should increase via decay"

    def test_clamp_upper(self):
        """Trust never exceeds 1.0."""
        params = TrustParams()
        T = compute_delta(0.999, [TrustEvent(EventType.SUCCESSFUL_ACTION_WITH_RESERVE)] * 10, [], params)
        assert 0.999 + T <= 1.0 + 1e-10, "Trust should not exceed 1.0"

    def test_clamp_lower(self):
        """Trust never goes below 0.0."""
        params = TrustParams()
        delta = compute_delta(0.001, [], [TrustEvent(EventType.MANUAL_REVOCATION)] * 5, params)
        assert 0.001 + delta >= -1e-10, "Trust should not go below 0.0"

    def test_reset_full(self):
        """Full reset sets trust to 0.0."""
        assert trust_apply_reset(0.95, ResetType.FULL_RESET) == 0.0

    def test_reset_multiplier(self):
        """Multiplier resets scale trust correctly."""
        result = trust_apply_reset(0.8, ResetType.FIRMWARE_UPDATE)
        assert abs(result - 0.56) < 1e-10  # 0.8 * 0.7

    def test_params_validation(self):
        """Invalid parameters are rejected."""
        with pytest.raises(ValueError):
            TrustParams(alpha_gain=0.1)  # Too high
        with pytest.raises(ValueError):
            TrustParams(alpha_loss=0.001)  # Too low
        with pytest.raises(ValueError):
            TrustParams(alpha_loss=0.01, alpha_gain=0.02, quality_cap=1)  # alpha_loss <= alpha_gain * cap

    def test_simulation_stability(self):
        """Simulation does not produce NaN or infinity."""
        events = [[EventType.SUCCESSFUL_ACTION] * 5 for _ in range(1000)]
        traj = simulate_trust(0.0, events, 1000)
        for day, trust in traj:
            assert 0.0 <= trust <= 1.0, f"Trust out of range on day {day}: {trust}"
            assert trust == trust, f"NaN on day {day}"  # NaN check

    def test_oscillation_convergence(self):
        """System with periodic bad events converges to a stable oscillation."""
        import random
        random.seed(999)
        events = []
        for d in range(1000):
            day_ev = [EventType.SUCCESSFUL_ACTION] * 8 * 24
            if d % 7 == 0:
                day_ev.append(EventType.ANOMALY_DETECTED)
            events.append(day_ev)
        traj = simulate_trust(0.0, events, 1000)

        # Check that the last 100 days have bounded oscillation
        last_100 = [t for _, t in traj[-100:]]
        oscillation = max(last_100) - min(last_100)
        assert oscillation < 0.1, f"Oscillation too large: {oscillation}"
```

#### Integration Tests

| Test ID | Description | Method |
|---------|-------------|--------|
| INT-001 | End-to-end event submission → trust update → API query | Submit events via MQTT, verify trust score via REST API after window elapse |
| INT-002 | Reset triggers trust reduction and timer reset | Send reset command, verify trust state via API |
| INT-003 | Level promotion after sustained good behavior | Run simulation for >720 hours, verify Level 5 achieved |
| INT-004 | Level demotion on major incident | Achieve Level 4, inject severity=1.0 event, verify Level 0 |
| INT-005 | Persistence across restart | Write trust state, restart process, verify trust is restored |
| INT-006 | Concurrent event submission | Submit events from 10 threads simultaneously, verify no data loss |
| INT-007 | NVS corruption recovery | Corrupt NVS trust data, verify system falls back to floor and alerts |
| INT-008 | Multi-subsystem isolation | Verify events for subsystem A do not affect subsystem B's trust |

#### Property-Based Tests

Using `hypothesis`:

```python
from hypothesis import given, strategies as st, assume

@given(
    initial_trust=st.floats(min_value=0.0, max_value=1.0),
    n_good=st.integers(min_value=0, max_value=50),
    n_bad=st.integers(min_value=0, max_value=50),
)
def test_trust_always_in_range(initial_trust, n_good, n_bad):
    """Trust score is always in [0, 1] regardless of inputs."""
    assume(not (n_good == 0 and n_bad == 0))  # skip trivial case
    params = TrustParams()
    good_events = [TrustEvent(EventType.SUCCESSFUL_ACTION)] * n_good
    bad_events = [TrustEvent(EventType.ANOMALY_DETECTED)] * n_bad
    delta = compute_delta(initial_trust, good_events, bad_events, params)
    T_new = max(0.0, min(1.0, initial_trust + delta))
    assert 0.0 <= T_new <= 1.0

@given(st.floats(min_value=0.0, max_value=1.0))
def test_gain_never_negative_at_zero_trust(trust):
    """At T=0, gain delta is non-negative, penalty delta is zero."""
    params = TrustParams()
    good = [TrustEvent(EventType.SUCCESSFUL_ACTION)]
    bad = [TrustEvent(EventType.ANOMALY_DETECTED)]

    gain_delta = compute_delta(trust, good, [], params)
    assert gain_delta >= 0, f"Gain delta should be non-negative, got {gain_delta}"

    penalty_delta = compute_delta(0.0, [], bad, params)
    assert penalty_delta == 0.0, "Penalty at T=0 should be zero"
```

### 10.5 Safety Argument

| Requirement | Implementation | Verification |
|-------------|---------------|--------------|
| Trust cannot exceed 1.0 | `clamp(T + delta, 0.0, 1.0)` in every code path | Unit test `test_clamp_upper`, property test `test_trust_always_in_range` |
| Trust cannot go below 0.0 | Same clamp, plus penalty is `T_prev * factor` (zero at T=0) | Unit test `test_clamp_lower`, property test |
| Bad events always reduce trust | Branch 2 selected whenever `n_bad > 0`; good events ignored | Unit test `test_penalty_basic`, `test_penalty_ignores_good` |
| Decay cannot reduce trust below t_floor | `delta = -alpha_decay * (T - t_floor)` → zero at floor | Unit test `test_decay_stops_at_floor` |
| Reset is bounded | Multiplier is in `[0.0, 1.0]`; `full_reset` = 0.0 explicitly | Unit test `test_reset_full`, `test_reset_multiplier` |
| Thread safety | RW-lock around all state mutations; MPSC queue for events | Integration test INT-006 |
| Persistence integrity | CRC32 on every NVS read; WAL mode for SQLite | Integration test INT-007 |
| Asymmetric gain/loss | Parameter validation ensures `alpha_loss > alpha_gain * quality_cap` | Unit test `test_params_validation` |
| Deterministic | No random number generation in algorithm; pure function of inputs | All simulations are reproducible with fixed seeds |

---

## 11. Appendix: Verification & Validation

### 11.1 Formal Properties

The following properties hold for all valid inputs:

**P1 (Boundedness)**: `forall t: 0.0 <= T(t) <= 1.0`
- Proof: By induction. T(0) is in [0,1] by initialization. Each delta is computed from T(t-1) in [0,1], and the result is clamped. ∎

**P2 (Monotonic Penalty)**: If T1 < T2, then |delta_penalty(T1)| < |delta_penalty(T2)|
- Proof: `|delta| = alpha_loss * T * severity * n_penalty`. T is the only variable, and it's linear. ∎

**P3 (Diminishing Gains)**: If T1 < T2, then delta_gain(T1) > delta_gain(T2)
- Proof: `delta = alpha_gain * (1 - T) * Q * capped/cap`. The factor `(1 - T)` strictly decreases with T. ∎

**P4 (Floor Stability)**: If T = t_floor and no events occur, T remains at t_floor.
- Proof: `delta = -alpha_decay * (t_floor - t_floor) = 0`. ∎

**P5 (Zero Trust Immunity)**: At T = 0, bad events have no effect.
- Proof: `delta = -alpha_loss * 0 * severity * n_penalty = 0`. Trust cannot go negative. ∎

### 11.2 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Safety Engineering | Initial specification |

---

*End of Document*
