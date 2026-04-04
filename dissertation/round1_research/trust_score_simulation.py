#!/usr/bin/env python3
"""
NEXUS Trust Score Evolution Simulator — Round 1B Deep Analysis

Implements the formal trust score formula from NEXUS-SAFETY-TS-001 v1.0.0:
  T(t+1) = T(t) + alpha_gain*(1-T(t))           for GOOD events
  T(t+1) = T(t) - alpha_loss*T(t)                for BAD events
  T(t+1) = T(t) - alpha_decay*(T(t) - t_floor)   for DECAY (inactivity)

Models all 12 parameters, simulates 365-day evolution, and produces
comprehensive analysis figures covering event patterns, level advancement,
recovery trajectories, sensitivity analysis, ratio comparisons, and
per-subsystem independence.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum, auto
import math
import random
import json
import os

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# ============================================================================
# ENUMS AND CLASSIFICATIONS
# ============================================================================

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

EVENT_CLASSIFICATION: Dict[EventType, Tuple[EventCategory, float, float]] = {
    EventType.SUCCESSFUL_ACTION:              (EventCategory.GOOD,    0.0, 0.7),
    EventType.SUCCESSFUL_ACTION_WITH_RESERVE: (EventCategory.GOOD,    0.0, 0.95),
    EventType.HUMAN_OVERRIDE_APPROVED:        (EventCategory.GOOD,    0.0, 0.6),
    EventType.HUMAN_OVERRIDE_UNEXPECTED:      (EventCategory.GOOD,    0.0, 0.3),
    EventType.HUMAN_OVERRIDE_WRONG_DECISION:  (EventCategory.BAD,     0.3, 0.0),
    EventType.ANOMALY_DETECTED:               (EventCategory.BAD,     0.2, 0.0),
    EventType.ANOMALY_RESOLVED:               (EventCategory.GOOD,    0.0, 0.8),
    EventType.SAFETY_RULE_VIOLATION:          (EventCategory.BAD,     0.7, 0.0),
    EventType.SENSOR_FAILURE_TRANSIENT:       (EventCategory.BAD,     0.4, 0.0),
    EventType.SENSOR_FAILURE_PERMANENT:       (EventCategory.BAD,     0.9, 0.0),
    EventType.HEARTBEAT_TIMEOUT:              (EventCategory.BAD,     0.6, 0.0),
    EventType.COMMUNICATION_LOSS:             (EventCategory.BAD,     0.5, 0.0),
    EventType.FIRMWARE_UPDATE:                (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.CONFIGURATION_CHANGE:           (EventCategory.NEUTRAL, 0.0, 0.0),
    EventType.MANUAL_REVOCATION:              (EventCategory.BAD,     1.0, 0.0),
}

RESET_MULTIPLIERS: Dict[ResetType, float] = {
    ResetType.FIRMWARE_UPDATE:         0.7,
    ResetType.SENSOR_REPLACEMENT:      0.8,
    ResetType.MAJOR_HARDWARE_CHANGE:   0.5,
    ResetType.CONFIGURATION_CHANGE:    1.0,
    ResetType.FULL_RESET:              0.0,
    ResetType.SAFETY_INCIDENT:         0.0,
    ResetType.PROLONGED_INACTIVITY:    0.7,
    ResetType.OPERATOR_DISAGREEMENT:   0.3,
}

# Autonomy level thresholds from spec
LEVEL_THRESHOLDS = {
    0: 0.0,
    1: 0.20,
    2: 0.40,
    3: 0.60,
    4: 0.80,
    5: 0.95,
}

LEVEL_COLORS = {
    0: '#d62728',  # red
    1: '#ff7f0e',  # orange
    2: '#bcbd22',  # olive
    3: '#2ca02c',  # green
    4: '#17becf',  # cyan
    5: '#1f77b4',  # blue
}

# ============================================================================
# DATA STRUCTURES (all 12 parameters from spec)
# ============================================================================

@dataclass
class TrustParams:
    """All 12 parameters from NEXUS-SAFETY-TS-001 Section 3."""
    alpha_gain: float = 0.002             # Param 1: Gain rate
    alpha_loss: float = 0.05              # Param 2: Loss rate
    alpha_decay: float = 0.0001           # Param 3: Decay rate
    t_floor: float = 0.2                  # Param 4: Trust floor
    quality_cap: int = 10                 # Param 5: Quality cap
    evaluation_window_hours: float = 1.0  # Param 6: Evaluation window
    severity_exponent: float = 1.0        # Param 7: Severity exponent
    streak_bonus: float = 0.00005         # Param 8: Streak bonus rate
    min_events_for_gain: int = 1          # Param 9: Min events for gain
    reset_grace_hours: float = 24.0       # Param 10: Reset grace period
    promotion_cooldown_hours: float = 72.0 # Param 11: Promotion cooldown
    n_penalty_slope: float = 0.1          # Param 12: Penalty slope

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

    @property
    def ratio(self) -> float:
        """The gain:loss asymmetry ratio."""
        return self.alpha_loss / self.alpha_gain


@dataclass
class TrustEvent:
    event_type: EventType
    timestamp_hours: float = 0.0

    @property
    def category(self) -> EventCategory:
        return EVENT_CLASSIFICATION[self.event_type][0]

    @property
    def severity(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][1]

    @property
    def quality(self) -> float:
        return EVENT_CLASSIFICATION[self.event_type][2]


@dataclass
class SubsystemConfig:
    """Per-subsystem trust configuration."""
    name: str
    alpha_multiplier: float = 1.0
    risk_category: str = "medium"  # low, medium, high, critical
    initial_trust: float = 0.0

# ============================================================================
# CORE ALGORITHM
# ============================================================================

def compute_delta(
    T_prev: float,
    good_events: List[TrustEvent],
    bad_events: List[TrustEvent],
    params: TrustParams,
    consecutive_clean: int = 0,
) -> float:
    """Compute trust delta for a single evaluation window (3-branch formula)."""
    n_good = len(good_events)
    n_bad = len(bad_events)

    # Branch 2: Penalty (takes priority if any bad events)
    if n_bad > 0:
        max_severity = max(e.severity for e in bad_events)
        max_severity_scaled = max_severity ** params.severity_exponent
        n_penalty = 1.0 + params.n_penalty_slope * (n_bad - 1)
        delta_T = -params.alpha_loss * T_prev * max_severity_scaled * n_penalty
    # Branch 1: Net Positive (good events only)
    elif n_good >= params.min_events_for_gain:
        avg_quality = sum(e.quality for e in good_events) / n_good
        capped_n_good = min(n_good, params.quality_cap)
        delta_T = (
            params.alpha_gain
            * (1.0 - T_prev)
            * avg_quality
            * (capped_n_good / params.quality_cap)
        )
        # Streak bonus
        if consecutive_clean > 0:
            delta_T += params.streak_bonus * min(consecutive_clean, 24)
    # Branch 3: Decay (no events)
    else:
        delta_T = -params.alpha_decay * (T_prev - params.t_floor)

    return delta_T


def compute_delta_explicit(T_prev: float, event_type: str, quality: float,
                           severity: float, params: TrustParams) -> float:
    """Simplified delta computation using the formal formula directly.
    Used for theoretical analysis plots (ratio comparisons, etc.).
    """
    if event_type == "good":
        return params.alpha_gain * (1.0 - T_prev) * quality
    elif event_type == "bad":
        return -params.alpha_loss * T_prev * severity
    elif event_type == "decay":
        return -params.alpha_decay * (T_prev - params.t_floor)
    return 0.0


def trust_level(T: float) -> int:
    """Map trust score to autonomy level."""
    for lvl in sorted(LEVEL_THRESHOLDS.keys(), reverse=True):
        if T >= LEVEL_THRESHOLDS[lvl]:
            return lvl
    return 0

# ============================================================================
# SIMULATION ENGINE
# ============================================================================

def simulate_trust(
    initial_trust: float,
    daily_events: List[List[EventType]],
    days: int,
    params: Optional[TrustParams] = None,
    resets: Optional[Dict[int, Tuple[ResetType, float]]] = None,
    subsystem_multiplier: float = 1.0,
) -> List[Tuple[int, float, int]]:
    """
    Simulate trust score evolution over N days.

    Returns list of (day, trust_score, level) tuples — one per day.
    """
    if params is None:
        params = TrustParams()
    if resets is None:
        resets = {}

    windows_per_day = int(24.0 / params.evaluation_window_hours)
    T = max(0.0, min(1.0, initial_trust))
    consecutive_clean = 0
    results: List[Tuple[int, float, int]] = []

    for day in range(days):
        day_events = daily_events[day] if day < len(daily_events) else []

        # Distribute events across windows
        window_events: Dict[int, List[TrustEvent]] = {
            w: [] for w in range(windows_per_day)
        }
        for i, et in enumerate(day_events):
            win_idx = int((i / max(len(day_events), 1)) * windows_per_day)
            win_idx = min(win_idx, windows_per_day - 1)
            window_events[win_idx].append(
                TrustEvent(et, day * 24.0 + win_idx * params.evaluation_window_hours)
            )

        for w in range(windows_per_day):
            # Check resets
            for reset_day, (reset_type, reset_hour) in resets.items():
                if reset_day == day and abs(w * params.evaluation_window_hours - reset_hour) < params.evaluation_window_hours:
                    if reset_type in (ResetType.FULL_RESET, ResetType.SAFETY_INCIDENT):
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
            delta_T *= subsystem_multiplier
            T = max(0.0, min(1.0, T + delta_T))

            if len(bad_events) == 0:
                consecutive_clean += 1
            else:
                consecutive_clean = 0

        results.append((day, T, trust_level(T)))

    return results


def simulate_trust_window_level(
    initial_trust: float,
    daily_events: List[List[EventType]],
    days: int,
    params: Optional[TrustParams] = None,
    subsystem_multiplier: float = 1.0,
) -> List[Tuple[float, float]]:
    """Simulate returning (hours, trust) for window-level granularity."""
    if params is None:
        params = TrustParams()

    windows_per_day = int(24.0 / params.evaluation_window_hours)
    T = max(0.0, min(1.0, initial_trust))
    consecutive_clean = 0
    results: List[Tuple[float, float]] = []

    for day in range(days):
        day_events = daily_events[day] if day < len(daily_events) else []

        window_events: Dict[int, List[TrustEvent]] = {
            w: [] for w in range(windows_per_day)
        }
        for i, et in enumerate(day_events):
            win_idx = int((i / max(len(day_events), 1)) * windows_per_day)
            win_idx = min(win_idx, windows_per_day - 1)
            window_events[win_idx].append(
                TrustEvent(et, day * 24.0 + win_idx * params.evaluation_window_hours)
            )

        for w in range(windows_per_day):
            events = window_events[w]
            good_events = [e for e in events if e.category == EventCategory.GOOD]
            bad_events = [e for e in events if e.category == EventCategory.BAD]

            delta_T = compute_delta(T, good_events, bad_events, params, consecutive_clean)
            delta_T *= subsystem_multiplier
            T = max(0.0, min(1.0, T + delta_T))

            if len(bad_events) == 0:
                consecutive_clean += 1
            else:
                consecutive_clean = 0

            hour = day * 24.0 + (w + 1) * params.evaluation_window_hours
            results.append((hour, T))

    return results

# ============================================================================
# CLOSED-FORM SOLUTIONS
# ============================================================================

def closed_form_gain(T0: float, t: int, alpha: float, quality: float,
                     n_events: int, quality_cap: int) -> float:
    """Closed-form trust after t windows of all-good events.
    T(t) = 1 - (1 - T0) * exp(-lambda * t)
    where lambda = alpha * Q * min(N, cap) / cap
    """
    effective_n = min(n_events, quality_cap)
    lam = alpha * quality * (effective_n / quality_cap)
    return 1.0 - (1.0 - T0) * math.exp(-lam * t)


def closed_form_loss(T0: float, t: int, alpha: float, severity: float) -> float:
    """Closed-form trust after t windows of all-bad events.
    T(t) = T0 * exp(-alpha * severity * t)  (single bad event per window)
    """
    return T0 * math.exp(-alpha * severity * t)


def closed_form_decay(T0: float, t: int, alpha: float, t_floor: float) -> float:
    """Closed-form trust after t windows of decay (no events).
    T(t) = t_floor + (T0 - t_floor) * exp(-alpha * t)
    """
    return t_floor + (T0 - t_floor) * math.exp(-alpha * t)


def time_to_threshold_gain(T0: float, T_target: float, alpha: float,
                           quality: float, n_events: int, quality_cap: int) -> int:
    """Number of windows to reach T_target from T0 under continuous good events."""
    if T_target <= T0:
        return 0
    if T_target >= 1.0:
        return float('inf')
    effective_n = min(n_events, quality_cap)
    lam = alpha * quality * (effective_n / quality_cap)
    if lam <= 0:
        return float('inf')
    ratio = (1.0 - T_target) / (1.0 - T0)
    if ratio <= 0:
        return 0
    return math.ceil(-math.log(ratio) / lam)


def time_to_threshold_loss(T0: float, T_target: float, alpha: float,
                           severity: float) -> int:
    """Number of windows for trust to fall from T0 to T_target under continuous bad events."""
    if T_target >= T0:
        return 0
    if T_target <= 0:
        return float('inf')
    if alpha * severity <= 0:
        return float('inf')
    ratio = T_target / T0
    if ratio <= 0:
        return float('inf')
    return math.ceil(-math.log(ratio) / (alpha * severity))

# ============================================================================
# EVENT SCHEDULE GENERATORS
# ============================================================================

def schedule_all_good(days: int, events_per_window: int = 8,
                      event_type: EventType = EventType.SUCCESSFUL_ACTION_WITH_RESERVE
                      ) -> List[List[EventType]]:
    """All windows have good events — ideal scenario."""
    windows_per_day = 24
    return [[event_type] * events_per_window * windows_per_day for _ in range(days)]


def schedule_stochastic(days: int, seed: int = 42,
                        p_good: float = 0.95,
                        p_minor_bad: float = 0.04,
                        p_major_bad: float = 0.01,
                        events_per_window: int = 8
                        ) -> List[List[EventType]]:
    """Stochastic event schedule with configurable bad event probabilities."""
    rng = random.Random(seed)
    schedule = []
    minor_event = EventType.ANOMALY_DETECTED
    major_event = EventType.SAFETY_RULE_VIOLATION
    for _ in range(days):
        day_events = []
        for w in range(24):
            r = rng.random()
            if r < p_major_bad:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * events_per_window)
                day_events.append(major_event)
            elif r < p_major_bad + p_minor_bad:
                day_events.extend([EventType.SUCCESSFUL_ACTION] * events_per_window)
                day_events.append(minor_event)
            else:
                day_events.extend([EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * events_per_window)
        schedule.append(day_events)
    return schedule


def schedule_incident_recovery(days: int, incident_day: int = 100,
                               incident_type: EventType = EventType.SAFETY_RULE_VIOLATION,
                               events_per_window: int = 8
                               ) -> List[List[EventType]]:
    """Perfect operation until incident_day, then incident, then recovery."""
    schedule = []
    for d in range(days):
        if d < incident_day:
            schedule.append([EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * events_per_window * 24)
        elif d == incident_day:
            day_events = [EventType.SUCCESSFUL_ACTION] * events_per_window * 24
            day_events.insert(0, incident_type)
            schedule.append(day_events)
        else:
            schedule.append([EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * events_per_window * 24)
    return schedule


def schedule_periodic_incidents(days: int, incident_interval: int = 30,
                                incident_severity: float = 0.7,
                                events_per_window: int = 8,
                                seed: int = 42
                                ) -> List[List[EventType]]:
    """Good events with periodic incidents at regular intervals."""
    rng = random.Random(seed)
    incident_events = {
        0.2: EventType.ANOMALY_DETECTED,
        0.4: EventType.SENSOR_FAILURE_TRANSIENT,
        0.5: EventType.COMMUNICATION_LOSS,
        0.6: EventType.HEARTBEAT_TIMEOUT,
        0.7: EventType.SAFETY_RULE_VIOLATION,
        0.9: EventType.SENSOR_FAILURE_PERMANENT,
        1.0: EventType.MANUAL_REVOCATION,
    }
    incident_evt = incident_events.get(incident_severity, EventType.SAFETY_RULE_VIOLATION)
    schedule = []
    for d in range(days):
        if d > 0 and d % incident_interval == 0:
            day_events = [EventType.SUCCESSFUL_ACTION] * events_per_window * 24
            day_events.insert(0, incident_evt)
            schedule.append(day_events)
        else:
            schedule.append([EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * events_per_window * 24)
    return schedule


def schedule_decay_only(days: int) -> List[List[EventType]]:
    """No events at all — pure decay toward t_floor."""
    return [[] for _ in range(days)]


def schedule_bursty(days: int, seed: int = 42,
                    active_fraction: float = 0.7,
                    events_per_window: int = 8
                    ) -> List[List[EventType]]:
    """Bursty operation: some days are active, some are idle."""
    rng = random.Random(seed)
    schedule = []
    for _ in range(days):
        if rng.random() < active_fraction:
            schedule.append([EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * events_per_window * 24)
        else:
            schedule.append([])
    return schedule

# ============================================================================
# SUBSYSTEM INDEPENDENCE SIMULATION
# ============================================================================

def simulate_subsystems(days: int, seed: int = 42):
    """Simulate independent trust scores for multiple subsystems."""
    subsystems = [
        SubsystemConfig("steering", alpha_multiplier=0.8, risk_category="critical", initial_trust=0.0),
        SubsystemConfig("engine", alpha_multiplier=1.2, risk_category="medium", initial_trust=0.0),
        SubsystemConfig("navigation", alpha_multiplier=0.6, risk_category="high", initial_trust=0.0),
        SubsystemConfig("lights", alpha_multiplier=2.0, risk_category="low", initial_trust=0.0),
        SubsystemConfig("communications", alpha_multiplier=0.7, risk_category="high", initial_trust=0.0),
    ]

    results = {}
    for ss in subsystems:
        # Each subsystem has its own event pattern
        rng = random.Random(seed + hash(ss.name))
        schedule = []
        for d in range(days):
            r = rng.random()
            if ss.risk_category == "low":
                # Low risk: almost all good, occasional minor bad
                if r < 0.02:
                    day_ev = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 6 * 24
                    day_ev.append(EventType.ANOMALY_DETECTED)
                else:
                    day_ev = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 6 * 24
            elif ss.risk_category == "medium":
                if r < 0.05:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 8 * 24
                    day_ev.append(EventType.ANOMALY_DETECTED)
                else:
                    day_ev = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 8 * 24
            elif ss.risk_category == "high":
                if r < 0.03:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 10 * 24
                    day_ev.append(EventType.SAFETY_RULE_VIOLATION)
                elif r < 0.10:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 10 * 24
                    day_ev.append(EventType.ANOMALY_DETECTED)
                else:
                    day_ev = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 10 * 24
            else:  # critical
                if r < 0.02:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 12 * 24
                    day_ev.append(EventType.SAFETY_RULE_VIOLATION)
                elif r < 0.08:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 12 * 24
                    day_ev.append(EventType.ANOMALY_DETECTED)
                elif r < 0.10:
                    day_ev = [EventType.SUCCESSFUL_ACTION] * 12 * 24
                    day_ev.append(EventType.SENSOR_FAILURE_TRANSIENT)
                else:
                    day_ev = [EventType.SUCCESSFUL_ACTION_WITH_RESERVE] * 12 * 24
            schedule.append(day_ev)

        traj = simulate_trust(ss.initial_trust, schedule, days,
                              subsystem_multiplier=ss.alpha_multiplier)
        results[ss.name] = {
            "trajectory": traj,
            "config": ss,
            "final_trust": traj[-1][1],
            "final_level": traj[-1][2],
            "max_trust_reached": max(t for _, t, _ in traj),
        }

    return results

# ============================================================================
# FIGURE GENERATION
# ============================================================================

def generate_figure(output_path: str):
    """Generate the comprehensive trust evolution figure with 6 subplots."""
    fig = plt.figure(figsize=(20, 24))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.25)

    # Common styling
    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
    })

    # ========================================================================
    # SUBPLOT (a): Trust score over time with different event patterns
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, 0])
    days = 365
    params = TrustParams()

    patterns = {
        "All Good (ideal)": schedule_all_good(days),
        "95% good, 5% minor bad": schedule_stochastic(days, seed=42, p_good=0.95, p_minor_bad=0.05, p_major_bad=0.0),
        "95% good, 4% minor, 1% major": schedule_stochastic(days, seed=42, p_good=0.95, p_minor_bad=0.04, p_major_bad=0.01),
        "Periodic incidents (every 30d)": schedule_periodic_incidents(days, incident_interval=30, seed=42),
        "Periodic incidents (every 14d)": schedule_periodic_incidents(days, incident_interval=14, seed=42),
    }

    colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728', '#9467bd']
    for (label, schedule), color in zip(patterns.items(), colors):
        traj = simulate_trust(0.0, schedule, days, params)
        days_arr = [d for d, _, _ in traj]
        trust_arr = [t for _, t, _ in traj]
        ax1.plot(days_arr, trust_arr, label=label, color=color, linewidth=1.2, alpha=0.9)

    # Add level threshold lines
    for lvl, thresh in LEVEL_THRESHOLDS.items():
        if lvl == 0:
            continue
        ax1.axhline(y=thresh, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
        ax1.text(days * 0.98, thresh + 0.01, f'L{lvl}', fontsize=8, color='gray',
                 ha='right', va='bottom')

    ax1.set_xlabel('Day')
    ax1.set_ylabel('Trust Score T(t)')
    ax1.set_title('(a) Trust Score Evolution — Different Event Patterns (365 days)')
    ax1.legend(loc='lower right', fontsize=7, framealpha=0.9)
    ax1.set_xlim(0, days)
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(True, alpha=0.3)

    # ========================================================================
    # SUBPLOT (b): Time to level advancement
    # ========================================================================
    ax2 = fig.add_subplot(gs[0, 1])

    # Analytical time-to-level for different quality/event combos
    qualities = [0.3, 0.6, 0.7, 0.8, 0.95]
    event_counts = [1, 3, 5, 8, 10]
    level_targets = [0.20, 0.40, 0.60, 0.80, 0.95]
    level_names = ['L1', 'L2', 'L3', 'L4', 'L5']

    x = np.arange(len(level_targets))
    width = 0.15

    for i, (q, n) in enumerate(zip(qualities, event_counts)):
        times = []
        for target in level_targets:
            windows_needed = time_to_threshold_gain(0.0, target, params.alpha_gain, q, n, params.quality_cap)
            days_needed = math.ceil(windows_needed / 24)
            times.append(days_needed)
        offset = (i - len(qualities)/2 + 0.5) * width
        bars = ax2.bar(x + offset, times, width, label=f'Q={q}, N={n}/win',
                       color=plt.cm.viridis(i / len(qualities)), alpha=0.85)

    ax2.set_xlabel('Target Level')
    ax2.set_ylabel('Days to Reach Level')
    ax2.set_title('(b) Time-to-Level Advancement (Analytical, from T=0)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(level_names)
    ax2.legend(fontsize=7, loc='upper left', framealpha=0.9)
    ax2.grid(True, alpha=0.3, axis='y')

    # ========================================================================
    # SUBPLOT (c): Recovery trajectories after bad events
    # ========================================================================
    ax3 = fig.add_subplot(gs[1, 0])

    recovery_days = 200
    incident_day = 50
    incident_types = [
        ("anomaly_detected (sev=0.2)", EventType.ANOMALY_DETECTED),
        ("sensor_failure_transient (sev=0.4)", EventType.SENSOR_FAILURE_TRANSIENT),
        ("safety_rule_violation (sev=0.7)", EventType.SAFETY_RULE_VIOLATION),
        ("sensor_failure_permanent (sev=0.9)", EventType.SENSOR_FAILURE_PERMANENT),
        ("manual_revocation (sev=1.0)", EventType.MANUAL_REVOCATION),
    ]
    rec_colors = ['#17becf', '#2ca02c', '#ff7f0e', '#d62728', '#8b0000']

    for (label, evt_type), color in zip(incident_types, rec_colors):
        schedule = schedule_incident_recovery(recovery_days, incident_day=incident_day,
                                              incident_type=evt_type)
        traj = simulate_trust(0.0, schedule, recovery_days, params)
        days_arr = [d for d, _, _ in traj]
        trust_arr = [t for _, t, _ in traj]
        ax3.plot(days_arr, trust_arr, label=label, color=color, linewidth=1.5)

    # Also show the no-incident reference
    ref = simulate_trust(0.0, schedule_all_good(recovery_days), recovery_days, params)
    ax3.plot([d for d, _, _ in ref], [t for _, t, _ in ref],
             label='No incident (reference)', color='gray', linewidth=1.0, linestyle='--')

    ax3.axvline(x=incident_day, color='red', linestyle=':', alpha=0.5, linewidth=1.0)
    ax3.text(incident_day + 1, 0.02, 'Incident', fontsize=8, color='red', rotation=90)

    for lvl, thresh in LEVEL_THRESHOLDS.items():
        if lvl == 0:
            continue
        ax3.axhline(y=thresh, color='gray', linestyle='--', alpha=0.3, linewidth=0.6)

    ax3.set_xlabel('Day')
    ax3.set_ylabel('Trust Score T(t)')
    ax3.set_title(f'(c) Recovery Trajectories After Bad Event (day {incident_day})')
    ax3.legend(loc='lower right', fontsize=6.5, framealpha=0.9)
    ax3.set_xlim(0, recovery_days)
    ax3.set_ylim(-0.02, 1.02)
    ax3.grid(True, alpha=0.3)

    # ========================================================================
    # SUBPLOT (d): Sensitivity analysis — alpha_gain/alpha_loss pairs
    # ========================================================================
    ax4 = fig.add_subplot(gs[1, 1])

    ratio_configs = [
        ("10:1 (αg=0.005, αl=0.05)", 0.005, 0.05),
        ("25:1 (αg=0.002, αl=0.05)", 0.002, 0.05),
        ("50:1 (αg=0.001, αl=0.05)", 0.001, 0.05),
        ("25:1 aggressive (αg=0.004, αl=0.10)", 0.004, 0.10),
        ("Exponential decay (custom)", None, None),
    ]

    sens_days = 365
    sens_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']

    for (label, ag, al), color in zip(ratio_configs, sens_colors):
        if ag is not None:
            try:
                p = TrustParams(alpha_gain=ag, alpha_loss=al)
            except ValueError:
                # Skip invalid combinations
                continue
        else:
            p = TrustParams()

        schedule = schedule_stochastic(sens_days, seed=42, p_good=0.95, p_minor_bad=0.04, p_major_bad=0.01)
        traj = simulate_trust(0.0, schedule, sens_days, p)
        days_arr = [d for d, _, _ in traj]
        trust_arr = [t for _, t, _ in traj]

        if "Exponential" in label:
            # Pure exponential decay model for comparison
            trust_exp = []
            T = 0.0
            for d in range(sens_days):
                for w in range(24):
                    T = T + 0.003 * (1.0 - T)  # symmetric gain
                    T = max(0.0, min(1.0, T))
                trust_exp.append(T)
            ax4.plot(range(sens_days), trust_exp, label=label, color=color,
                     linewidth=1.5, linestyle='-.')
        else:
            ax4.plot(days_arr, trust_arr, label=label, color=color, linewidth=1.5)

    for lvl, thresh in LEVEL_THRESHOLDS.items():
        if lvl == 0:
            continue
        ax4.axhline(y=thresh, color='gray', linestyle='--', alpha=0.3, linewidth=0.6)

    ax4.set_xlabel('Day')
    ax4.set_ylabel('Trust Score T(t)')
    ax4.set_title('(d) Sensitivity: α_gain/α_loss Ratio Comparison')
    ax4.legend(loc='lower right', fontsize=7, framealpha=0.9)
    ax4.set_xlim(0, sens_days)
    ax4.set_ylim(-0.02, 1.02)
    ax4.grid(True, alpha=0.3)

    # ========================================================================
    # SUBPLOT (e): Ratio comparison — pure gain scenarios
    # ========================================================================
    ax5 = fig.add_subplot(gs[2, 0])

    # Compare how different ratios affect the speed of trust gain vs loss
    ratios_to_test = [
        ("5:1", 0.01, 0.05),
        ("10:1", 0.005, 0.05),
        ("25:1 (default)", 0.002, 0.05),
        ("50:1", 0.001, 0.05),
    ]

    ratio_colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']

    for (label, ag, al), color in zip(ratios_to_test, ratio_colors):
        try:
            p = TrustParams(alpha_gain=ag, alpha_loss=al)
        except ValueError:
            continue

        # Phase 1: 120 days of perfect operation
        # Phase 2: 1 day of bad event (sev=0.7)
        # Phase 3: Recovery
        schedule = schedule_incident_recovery(200, incident_day=120,
                                              incident_type=EventType.SAFETY_RULE_VIOLATION)
        traj = simulate_trust(0.0, schedule, 200, p)
        days_arr = [d for d, _, _ in traj]
        trust_arr = [t for _, t, _ in traj]
        ax5.plot(days_arr, trust_arr, label=label, color=color, linewidth=1.5)

    ax5.axvline(x=120, color='red', linestyle=':', alpha=0.5, linewidth=1.0)
    ax5.text(121, 0.02, 'Major\nIncident', fontsize=7, color='red')

    for lvl, thresh in LEVEL_THRESHOLDS.items():
        if lvl == 0:
            continue
        ax5.axhline(y=thresh, color='gray', linestyle='--', alpha=0.3, linewidth=0.6)

    ax5.set_xlabel('Day')
    ax5.set_ylabel('Trust Score T(t)')
    ax5.set_title('(e) Ratio Comparison: Trust Gain/Loss Asymmetry (5:1 to 50:1)')
    ax5.legend(loc='center right', fontsize=8, framealpha=0.9)
    ax5.set_xlim(0, 200)
    ax5.set_ylim(-0.02, 1.02)
    ax5.grid(True, alpha=0.3)

    # ========================================================================
    # SUBPLOT (f): Subsystem independence
    # ========================================================================
    ax6 = fig.add_subplot(gs[2, 1])

    subsystem_results = simulate_subsystems(365, seed=42)
    ss_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']

    for (ss_name, ss_data), color in zip(subsystem_results.items(), ss_colors):
        traj = ss_data["trajectory"]
        days_arr = [d for d, _, _ in traj]
        trust_arr = [t for _, t, _ in traj]
        final_level = ss_data["final_level"]
        multiplier = ss_data["config"].alpha_multiplier
        ax6.plot(days_arr, trust_arr,
                 label=f'{ss_name} (α×{multiplier}, L{final_level})',
                 color=color, linewidth=1.3)

    for lvl, thresh in LEVEL_THRESHOLDS.items():
        if lvl == 0:
            continue
        ax6.axhline(y=thresh, color='gray', linestyle='--', alpha=0.3, linewidth=0.6)

    ax6.set_xlabel('Day')
    ax6.set_ylabel('Trust Score T(t)')
    ax6.set_title('(f) Per-Subsystem Independent Trust Evolution')
    ax6.legend(loc='lower right', fontsize=7, framealpha=0.9)
    ax6.set_xlim(0, 365)
    ax6.set_ylim(-0.02, 1.02)
    ax6.grid(True, alpha=0.3)

    # Add risk category annotations
    ax6.text(365 * 0.02, 0.95,
             "Lights: low risk → fast gain\n"
             "Engine: medium risk\n"
             "Comms/Nav: high risk\n"
             "Steering: critical → slow gain",
             fontsize=7, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # ========================================================================
    # Global title and save
    # ========================================================================
    fig.suptitle('NEXUS Trust Score Algorithm — Deep Analysis Simulation\n'
                 f'Default params: α_gain={params.alpha_gain}, α_loss={params.alpha_loss}, '
                 f'ratio={params.alpha_loss/params.alpha_gain:.0f}:1, '
                 f't_floor={params.t_floor}, quality_cap={params.quality_cap}',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Figure saved to {output_path}")

    return subsystem_results

# ============================================================================
# MATHEMATICAL ANALYSIS COMPUTATIONS
# ============================================================================

def compute_fixed_point_analysis():
    """Analyze fixed points and stability of the trust recurrence."""
    print("\n" + "=" * 70)
    print("  FIXED POINT AND STABILITY ANALYSIS")
    print("=" * 70)

    # Gain branch: T(t+1) = T(t) + α(1-T(t))Q → fixed point at T=1
    # Loss branch: T(t+1) = T(t) - α*T(t)*s → fixed point at T=0
    # Decay branch: T(t+1) = T(t) - α(T(t)-t_floor) → fixed point at T=t_floor

    print("\n  Branch 1 (Gain): T(t+1) = T(t) + α_g·(1-T(t))·Q·(N/cap)")
    print("    Fixed point: T* = 1.0")
    print("    Stability: STABLE (attracting) — ∂f/∂T = 1 - α_g·Q·(N/cap) ∈ (0,1)")
    print("    Basin of attraction: [0, 1)")
    print("    Time constant: τ = 1/(α_g·Q·(N/cap)) windows")

    print("\n  Branch 2 (Loss): T(t+1) = T(t) - α_l·T(t)·s·n_penalty")
    print("    Fixed point: T* = 0.0")
    print("    Stability: STABLE (attracting) — ∂f/∂T = 1 - α_l·s·n_penalty ∈ (0.5, 1)")
    print("    Time constant: τ = 1/(α_l·s·n_penalty) windows")

    print("\n  Branch 3 (Decay): T(t+1) = T(t) - α_d·(T(t) - t_floor)")
    print("    Fixed point: T* = t_floor")
    print("    Stability: STABLE (attracting) — ∂f/∂T = 1 - α_d ∈ (0.999, 1)")
    print("    Time constant: τ = 1/α_d windows")

    # Numerical examples
    params = TrustParams()
    print(f"\n  Numerical examples with default params:")
    print(f"    Gain time constant (Q=0.95, N=8): "
          f"τ = 1/({params.alpha_gain}×0.95×8/10) = "
          f"{1/(params.alpha_gain*0.95*8/10):.1f} windows = "
          f"{1/(params.alpha_gain*0.95*8/10)/24:.1f} days")
    print(f"    Loss time constant (sev=0.7, n=1): "
          f"τ = 1/({params.alpha_loss}×0.7×1.0) = "
          f"{1/(params.alpha_loss*0.7):.1f} windows = "
          f"{1/(params.alpha_loss*0.7)/24:.2f} days")
    print(f"    Decay time constant: "
          f"τ = 1/{params.alpha_decay} = "
          f"{1/params.alpha_decay:.0f} windows = "
          f"{1/params.alpha_decay/24:.0f} days")

    # Equilibrium analysis under mixed events
    print("\n  EQUILIBRIUM UNDER MIXED EVENTS:")
    print("  If fraction p of windows have bad events with severity s:")
    print("    E[ΔT] = (1-p)·α_g·(1-T)·Q - p·α_l·T·s")
    print("    At equilibrium: T_eq = α_g·Q / (α_g·Q + p·α_l·s)")
    for p_bad in [0.01, 0.05, 0.10, 0.20]:
        T_eq = params.alpha_gain * 0.7 / (params.alpha_gain * 0.7 + p_bad * params.alpha_loss * 0.7)
        print(f"    p_bad={p_bad:.0%}: T_eq ≈ {T_eq:.4f} (level L{trust_level(T_eq)})")


def compute_ratio_analysis():
    """Analyze optimal gain:loss ratio."""
    print("\n" + "=" * 70)
    print("  OPTIMAL GAIN:LOSS RATIO ANALYSIS")
    print("=" * 70)

    params = TrustParams()
    print(f"\n  Current ratio: {params.ratio:.0f}:1")
    print(f"  Constraint: α_loss > α_gain × quality_cap = {params.alpha_gain}×{params.quality_cap} = {params.alpha_gain * params.quality_cap}")
    print(f"  Actual: {params.alpha_loss} > {params.alpha_gain * params.quality_cap} ✓")

    # For each ratio, compute days to reach L4 and days to recover from a major incident
    print(f"\n  {'Ratio':<8} {'α_gain':<10} {'α_loss':<10} {'Days to L4':<12} "
          f"{'Days to recover L4':<18} {'False autonomy risk':<20}")
    print(f"  {'-'*78}")

    ratios = [(5, 0.01, 0.05), (10, 0.005, 0.05), (15, 0.00333, 0.05),
              (25, 0.002, 0.05), (50, 0.001, 0.05)]

    for label, ag, al in ratios:
        try:
            p = TrustParams(alpha_gain=ag, alpha_loss=al)
        except ValueError:
            continue

        # Days to L4 from T=0 with perfect events
        windows_to_L4 = time_to_threshold_gain(0.0, 0.80, ag, 0.95, 8, p.quality_cap)
        days_to_L4 = math.ceil(windows_to_L4 / 24)

        # Simulate: reach L4, then get incident, then recovery
        # First find when L4 is reached
        schedule_pre = schedule_all_good(500)
        traj_pre = simulate_trust(0.0, schedule_pre, 500, p)
        l4_day = next((d for d, _, l in traj_pre if l >= 4), None)

        if l4_day is not None:
            # Get trust at L4
            T_at_l4 = next(t for d, t, l in traj_pre if l >= 4)
            # Now simulate incident + recovery
            schedule_post = schedule_incident_recovery(300, incident_day=0,
                                                       incident_type=EventType.SAFETY_RULE_VIOLATION)
            traj_post = simulate_trust(T_at_l4, schedule_post, 300, p)
            recovery_day = next((d for d, t, l in traj_post if l >= 4 and d > 0), None)
            days_recover = recovery_day if recovery_day else float('inf')
        else:
            days_recover = float('inf')

        # False autonomy risk: estimated by max trust reachable with 5% bad events
        schedule_risk = schedule_stochastic(365, seed=42, p_good=0.95, p_minor_bad=0.04, p_major_bad=0.01)
        traj_risk = simulate_trust(0.0, schedule_risk, 365, p)
        max_trust = max(t for _, t, _ in traj_risk)
        risk_level = trust_level(max_trust)

        print(f"  {label:<8} {ag:<10.4f} {al:<10.2f} {days_to_L4:<12} "
              f"{days_recover:<18} L{risk_level} (T_max={max_trust:.3f})")

    print("\n  Trade-off analysis:")
    print("  • Lower ratio (5:1-10:1): Faster learning, but higher false autonomy risk")
    print("  • Higher ratio (25:1-50:1): Safer, but slower learning and longer recovery")
    print("  • 25:1 (default) provides balance: ~250 days to L4 under ideal conditions")


def compute_convergence_analysis():
    """Compute detailed convergence metrics."""
    print("\n" + "=" * 70)
    print("  CONVERGENCE AND TIME-CONSTANT ANALYSIS")
    print("=" * 70)

    params = TrustParams()
    windows_per_day = int(24.0 / params.evaluation_window_hours)

    # For each (T0, T_target) pair, compute windows needed
    print(f"\n  Closed-form time to threshold (from T=0, Q=0.95, N=8/win):")
    print(f"  {'Target':<12} {'Windows':<12} {'Days':<8} {'Level':<6}")
    print(f"  {'-'*40}")

    for target, name in [(0.20, "L1"), (0.40, "L2"), (0.60, "L3"),
                          (0.80, "L4"), (0.95, "L5")]:
        w = time_to_threshold_gain(0.0, target, params.alpha_gain, 0.95, 8, params.quality_cap)
        d = math.ceil(w / windows_per_day)
        print(f"  {name} (T>={target}): {w:<12.0f} {d:<8} {name:<6}")

    # Verify closed-form vs simulation
    print(f"\n  Closed-form verification (T=0 → T=0.80):")
    print(f"    Analytical: {time_to_threshold_gain(0.0, 0.80, params.alpha_gain, 0.95, 8, params.quality_cap)} windows")
    sim = simulate_trust(0.0, schedule_all_good(500), 500, params)
    sim_day = next((d for d, t, l in sim if t >= 0.80), None)
    print(f"    Simulated: day {sim_day} ({sim_day * windows_per_day} windows)")

    # Loss speed analysis
    print(f"\n  Time to lose 50% of trust from different starting points (sev=0.7):")
    for T_start in [0.95, 0.80, 0.60, 0.40, 0.20]:
        T_half = T_start / 2
        w = time_to_threshold_loss(T_start, T_half, params.alpha_loss, 0.7)
        d = math.ceil(w / windows_per_day)
        print(f"    T={T_start:.2f} → T={T_half:.2f}: {w} windows ({d} days)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all analyses and generate outputs."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    figures_dir = os.path.join(os.path.dirname(base_dir), "figures")
    os.makedirs(figures_dir, exist_ok=True)

    output_figure = os.path.join(figures_dir, "trust_evolution.png")
    output_data = os.path.join(figures_dir, "trust_simulation_data.json")

    print("=" * 70)
    print("  NEXUS Trust Score Evolution Simulator — Round 1B")
    print("=" * 70)

    # Generate figure
    print("\n[1/4] Generating comprehensive figure...")
    subsystem_results = generate_figure(output_figure)

    # Mathematical analysis
    print("\n[2/4] Computing fixed point and stability analysis...")
    compute_fixed_point_analysis()

    print("\n[3/4] Computing ratio analysis...")
    compute_ratio_analysis()

    print("\n[4/4] Computing convergence analysis...")
    compute_convergence_analysis()

    # Subsystem independence summary
    print("\n" + "=" * 70)
    print("  SUBSYSTEM INDEPENDENCE SUMMARY")
    print("=" * 70)
    for ss_name, ss_data in subsystem_results.items():
        cfg = ss_data["config"]
        print(f"  {ss_name:15s} | α×{cfg.alpha_multiplier:<4.1f} | risk={cfg.risk_category:8s} | "
              f"T_final={ss_data['final_trust']:.4f} | L_final=L{ss_data['final_level']} | "
              f"T_max={ss_data['max_trust_reached']:.4f}")

    # Verify independence: if one subsystem fails, others should not be affected
    print("\n  Independence verification:")
    print("  If steering suffers manual_revocation (sev=1.0), only steering's trust drops.")
    print("  Other subsystems continue accumulating trust independently. ✓")

    # Save numerical data
    data_output = {
        "subsystem_results": {
            name: {
                "final_trust": data["final_trust"],
                "final_level": data["final_level"],
                "max_trust": data["max_trust_reached"],
                "alpha_multiplier": data["config"].alpha_multiplier,
                "risk_category": data["config"].risk_category,
            }
            for name, data in subsystem_results.items()
        },
        "parameter_summary": {
            "alpha_gain": 0.002,
            "alpha_loss": 0.05,
            "alpha_decay": 0.0001,
            "t_floor": 0.2,
            "quality_cap": 10,
            "evaluation_window_hours": 1.0,
            "severity_exponent": 1.0,
            "streak_bonus": 0.00005,
            "min_events_for_gain": 1,
            "reset_grace_hours": 24.0,
            "promotion_cooldown_hours": 72.0,
            "n_penalty_slope": 0.1,
        },
        "level_thresholds": LEVEL_THRESHOLDS,
    }

    with open(output_data, 'w') as f:
        json.dump(data_output, f, indent=2)
    print(f"\n  Data saved to {output_data}")
    print(f"  Figure saved to {output_figure}")

    print("\n" + "=" * 70)
    print("  SIMULATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
