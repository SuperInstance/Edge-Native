#!/usr/bin/env python3
"""
NEXUS Network Topology and Failure Analysis Simulation
=======================================================
Round 4A: Network and Failure Simulation for NEXUS Platform

Models:
  - N ESP32 nodes connected via RS-422 serial to M Jetson boards
  - Inter-Jetson gRPC (LAN) and MQTT communication
  - Jetson-to-Cloud (Starlink) connectivity
  - 8 failure scenarios with Monte Carlo analysis (1000 iterations)
  - 10,000-hour simulation per iteration

Component MTBF (hours):
  - ESP32:              50,000
  - Jetson Orin Nano:  100,000
  - RS-422 transceiver: 200,000
  - Cable:              500,000
  - Power supply:        30,000
  - Starlink link:     150,000

Author: NEXUS Dissertation Round 4A
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
import json
import os
import time as time_module
from collections import defaultdict

# ============================================================================
# Configuration Constants
# ============================================================================

SIMULATION_HOURS = 10_000
NUM_ITERATIONS = 500
SEED = 42

# Network topology
NUM_ESP32_NODES = 12
NUM_JETSON_BOARDS = 3
ESP32S_PER_JETSON = NUM_ESP32_NODES // NUM_JETSON_BOARDS  # 4 each

# Component MTBF (hours) - Weibull shape parameter k=1 (exponential/constant hazard)
MTBF = {
    'esp32':       50_000,
    'jetson':     100_000,
    'rs422_tx':   200_000,
    'cable':      500_000,
    'power_supply': 30_000,
    'starlink':   150_000,
}

# MTTR (hours) - mean time to recovery
MTTR = {
    'esp32':           2.0,    # firmware reload + verify
    'jetson':          8.0,    # full reboot + cluster rejoin
    'rs422_tx':        1.0,    # hardware swap
    'cable':           4.0,    # physical cable replacement
    'power_supply':    1.5,    # PSU swap
    'starlink':        0.5,    # automatic reconnection
    'cascade':        12.0,    # complex cascade recovery
    'byzantine':       6.0,    # detection + quarantine + restore
}

# Safety state entry probabilities per failure type
SAFETY_STATE_PROB = {
    'esp32_failure':        0.05,  # individual ESP32 fails -> low impact
    'jetson_failure':       0.40,  # Jetson loss -> significant
    'cable_cut':            0.15,  # serial link loss
    'grpc_loss':            0.20,  # inter-Jetson comm loss
    'power_failure':        0.95,  # full power loss -> almost certain
    'cascading':            0.70,  # cascading failures
    'byzantine':            0.30,  # incorrect data detection
    'cloud_loss':           0.02,  # cloud loss -> minimal local impact
}

# Degraded mode durations (hours) - lognormal parameters
DEGRADED_PARAMS = {
    'esp32_failure':   (1.0, 0.5),   # mean, std of log-duration
    'jetson_failure':  (2.0, 0.8),
    'cable_cut':       (1.5, 0.6),
    'grpc_loss':       (0.7, 0.3),
    'power_failure':   (2.5, 1.0),
    'cascading':       (2.8, 0.9),
    'byzantine':       (2.2, 0.7),
    'cloud_loss':      (0.3, 0.2),
}

# Byzantine failure injection probability (per hour, per node)
BYZANTINE_PROB = 1e-7

# Data loss rates (bytes/hour) during failures
DATA_LOSS_RATE = {
    'esp32_failure':    500,    # one node worth of telemetry
    'jetson_failure':  5000,   # accumulated sensor data from children
    'cable_cut':       500,    # one link worth
    'grpc_loss':      2000,    # inter-cluster sync data
    'power_failure': 10000,    # all data in flight
    'cascading':     15000,    # widespread data loss
    'byzantine':      1000,    # corrupted data + quarantine
    'cloud_loss':        50,   # cloud sync backlog
}


# ============================================================================
# Enums and Data Classes
# ============================================================================

class SystemState(Enum):
    FULL_OPERATION = auto()
    DEGRADED = auto()
    SAFE_STATE = auto()
    FAULT = auto()
    RECOVERING = auto()

class FailureType(Enum):
    ESP32_NODE = auto()
    JETSON_BOARD = auto()
    CABLE_CUT = auto()
    GRPC_LOSS = auto()
    POWER_FAILURE = auto()
    CASCADING = auto()
    BYZANTINE = auto()
    CLOUD_LOSS = auto()

class LinkType(Enum):
    RS422_SERIAL = auto()
    GRPC_LAN = auto()
    MQTT_LAN = auto()
    STARLINK = auto()


@dataclass
class Component:
    """A single hardware or software component in the network."""
    name: str
    comp_type: str           # key into MTBF dict
    mtbf: float
    operating: bool = True
    failure_time: Optional[float] = None
    recovery_time: Optional[float] = None
    failure_count: int = 0
    total_downtime: float = 0.0

@dataclass
class RS422Link:
    """Point-to-point RS-422 serial link between ESP32 and Jetson."""
    esp32_id: int
    jetson_id: int
    cable_length_m: float = 15.0     # default 15m cable
    active: bool = True
    transceiver: Optional[Component] = None
    cable: Optional[Component] = None

@dataclass
class JetsonBoard:
    """A Jetson Orin Nano cognitive processing board."""
    id: int
    component: Optional[Component] = None
    is_leader: bool = False
    connected_esp32s: List[int] = field(default_factory=list)
    grpc_links: List[int] = field(default_factory=list)  # peer Jetson IDs
    operating: bool = True

@dataclass
class ClusterState:
    """Current state of the cognitive cluster."""
    active_jetsons: int = 0
    total_jetsons: int = 0
    has_quorum: bool = True
    leader_id: int = 0
    system_state: SystemState = SystemState.FULL_OPERATION
    degraded_start: Optional[float] = None
    safe_state_entries: int = 0
    fault_entries: int = 0

@dataclass
class SimulationResult:
    """Results from a single simulation iteration."""
    iteration: int
    scenario: str
    availability: float = 0.0
    total_failures: int = 0
    total_safe_state_entries: int = 0
    total_fault_entries: int = 0
    total_downtime: float = 0.0
    mtbf_actual: float = 0.0
    mttr_actual: float = 0.0
    data_loss_bytes: float = 0.0
    degraded_durations: List[float] = field(default_factory=list)
    failure_events: List[Dict] = field(default_factory=list)
    quorum_loss_hours: float = 0.0
    cascading_count: int = 0
    byzantine_detected: int = 0


# ============================================================================
# Topology Builder
# ============================================================================

def build_topology(num_esp32: int, num_jetsons: int) -> Tuple[
    List[Component], List[JetsonBoard], List[RS422Link], List[Component]
]:
    """Build the NEXUS network topology.
    
    Returns:
        esp32s: List of ESP32 node components
        jetsons: List of Jetson boards
        links: List of RS-422 links
        cables: List of cable components
    """
    rng = np.random.RandomState(SEED + 7)
    
    # Create ESP32 nodes
    esp32s = []
    for i in range(num_esp32):
        esp = Component(
            name=f"ESP32_{i:02d}",
            comp_type='esp32',
            mtbf=MTBF['esp32'],
        )
        esp32s.append(esp)
    
    # Create Jetson boards
    jetsons = []
    for j in range(num_jetsons):
        jboard = JetsonBoard(
            id=j,
            is_leader=(j == 0),
            operating=True,
        )
        jboard.component = Component(
            name=f"Jetson_{j}",
            comp_type='jetson',
            mtbf=MTBF['jetson'],
        )
        jetsons.append(jboard)
    
    # Assign ESP32s to Jetsons (round-robin with cable length variation)
    links = []
    cables = []
    for i, esp in enumerate(esp32s):
        jetson_id = i % num_jetsons
        jboard = jetsons[jetson_id]
        jboard.connected_esp32s.append(i)
        
        # Variable cable lengths (5-30m depending on physical placement)
        cable_length = 5.0 + rng.uniform(0, 25.0)
        
        transceiver = Component(
            name=f"TX_ESP{i:02d}_J{jetson_id}",
            comp_type='rs422_tx',
            mtbf=MTBF['rs422_tx'],
        )
        cable = Component(
            name=f"Cable_ESP{i:02d}_J{jetson_id}",
            comp_type='cable',
            mtbf=MTBF['cable'],
        )
        cables.append(cable)
        
        link = RS422Link(
            esp32_id=i,
            jetson_id=jetson_id,
            cable_length_m=cable_length,
            transceiver=transceiver,
            cable=cable,
        )
        links.append(link)
    
    # Create gRPC mesh between Jetsons (all-to-all)
    for j in range(num_jetsons):
        for k in range(num_jetsons):
            if j != k:
                jetsons[j].grpc_links.append(k)
    
    return esp32s, jetsons, links, cables


# ============================================================================
# Failure Event Generator
# ============================================================================

def generate_failure_events(
    rng: np.random.RandomState,
    components: Dict[str, List[Component]],
    scenario: str,
    sim_hours: float,
) -> List[Dict]:
    """Generate failure events for a given scenario over the simulation period.
    
    Each event has: time, component, failure_type, recovery_time
    """
    events = []
    
    if scenario == 'esp32_failure':
        # Random ESP32 node failures with time-varying MTBF
        for comp in components['esp32']:
            # Time-varying MTBF: increases with age (bathtub curve - wearout)
            t = 0
            while t < sim_hours:
                # Age factor: MTBF decreases after 30,000 hours (wearout)
                age_factor = max(0.3, 1.0 - max(0, t - 30000) / 70000)
                effective_mtbf = comp.mtbf * age_factor
                failure_dt = rng.exponential(effective_mtbf)
                t += failure_dt
                if t < sim_hours:
                    mttr = rng.exponential(MTTR[comp.comp_type])
                    events.append({
                        'time': t,
                        'component': comp.name,
                        'comp_type': comp.comp_type,
                        'failure_type': FailureType.ESP32_NODE,
                        'recovery_time': mttr,
                        'recovery_end': t + mttr,
                    })
                    t += mttr

    elif scenario == 'jetson_failure':
        for comp in components['jetson']:
            t = 0
            while t < sim_hours:
                failure_dt = rng.exponential(comp.mtbf)
                t += failure_dt
                if t < sim_hours:
                    mttr = rng.exponential(MTTR[comp.comp_type])
                    events.append({
                        'time': t,
                        'component': comp.name,
                        'comp_type': comp.comp_type,
                        'failure_type': FailureType.JETSON_BOARD,
                        'recovery_time': mttr,
                        'recovery_end': t + mttr,
                    })
                    t += mttr

    elif scenario == 'cable_cut':
        for comp in components['cable']:
            t = 0
            while t < sim_hours:
                # Cable failures increase with length
                failure_dt = rng.exponential(comp.mtbf)
                t += failure_dt
                if t < sim_hours:
                    mttr = rng.exponential(MTTR[comp.comp_type])
                    events.append({
                        'time': t,
                        'component': comp.name,
                        'comp_type': comp.comp_type,
                        'failure_type': FailureType.CABLE_CUT,
                        'recovery_time': mttr,
                        'recovery_end': t + mttr,
                    })
                    t += mttr

    elif scenario == 'grpc_loss':
        # Inter-Jetson communication failures (switch/LAN issues)
        num_links = len(components['jetson']) * (len(components['jetson']) - 1)
        t = 0
        grpc_mtbf = 80_000  # gRPC link MTBF (depends on switch, NIC, cable)
        while t < sim_hours:
            failure_dt = rng.exponential(grpc_mtbf / num_links)
            t += failure_dt
            if t < sim_hours:
                mttr = rng.exponential(MTTR['rs422_tx'])  # similar recovery time
                events.append({
                    'time': t,
                    'component': f"gRPC_link_{rng.randint(0, num_links)}",
                    'comp_type': 'grpc',
                    'failure_type': FailureType.GRPC_LOSS,
                    'recovery_time': mttr,
                    'recovery_end': t + mttr,
                })
                t += mttr

    elif scenario == 'power_failure':
        # Power supply failures affecting multiple components
        num_psus = 3  # main + 2 redundant
        for psu_id in range(num_psus):
            t = 0
            while t < sim_hours:
                failure_dt = rng.exponential(MTBF['power_supply'])
                t += failure_dt
                if t < sim_hours:
                    # Power failure affects multiple components simultaneously
                    mttr = rng.exponential(MTTR['power_supply'])
                    events.append({
                        'time': t,
                        'component': f"PSU_{psu_id}",
                        'comp_type': 'power_supply',
                        'failure_type': FailureType.POWER_FAILURE,
                        'recovery_time': mttr,
                        'recovery_end': t + mttr,
                        'affected_components': ['all_on_psu'],
                    })
                    t += mttr

    elif scenario == 'cascading':
        # One failure can trigger others
        # Start with a primary failure, then cascade
        t = 0
        cascade_mtbf = 200_000  # base cascade trigger rate
        while t < sim_hours:
            failure_dt = rng.exponential(cascade_mtbf)
            t += failure_dt
            if t < sim_hours:
                # Primary failure: power supply or Jetson
                primary_type = rng.choice(['power_supply', 'jetson'])
                primary_mttr = rng.exponential(MTTR[primary_type])
                
                # Cascade: 30-70% chance of secondary failure within 1 hour
                num_secondary = rng.binomial(3, 0.4)
                secondary_events = []
                for _ in range(num_secondary):
                    sec_delay = rng.exponential(0.5)  # cascade delay
                    sec_mttr = rng.exponential(MTTR['cascade'])
                    secondary_events.append({
                        'time': t + sec_delay,
                        'component': f"cascade_secondary",
                        'comp_type': 'cascade',
                        'failure_type': FailureType.CASCADING,
                        'recovery_time': sec_mttr,
                        'recovery_end': t + sec_delay + sec_mttr,
                    })
                
                events.append({
                    'time': t,
                    'component': f"cascade_primary_{primary_type}",
                    'comp_type': primary_type,
                    'failure_type': FailureType.CASCADING,
                    'recovery_time': primary_mttr,
                    'recovery_end': t + primary_mttr,
                    'cascade_secondary': num_secondary,
                })
                events.extend(secondary_events)
                t += max(primary_mttr, max([e['recovery_end'] - t for e in secondary_events] or [0]))

    elif scenario == 'byzantine':
        # Byzantine failures: node sends incorrect data
        all_components = components['esp32'] + components['jetson']
        t = 0
        while t < sim_hours:
            failure_dt = rng.exponential(1.0 / (BYZANTINE_PROB * len(all_components)))
            t += failure_dt
            if t < sim_hours:
                # Byzantine failure: hard to detect, random duration
                comp = rng.choice(all_components)
                detect_time = rng.exponential(2.0)  # time to detect
                mttr = rng.exponential(MTTR['byzantine'])
                events.append({
                    'time': t,
                    'component': comp.name,
                    'comp_type': comp.comp_type,
                    'failure_type': FailureType.BYZANTINE,
                    'recovery_time': detect_time + mttr,
                    'recovery_end': t + detect_time + mttr,
                    'detection_delay': detect_time,
                })
                t += detect_time + mttr

    elif scenario == 'cloud_loss':
        # Starlink connectivity loss
        t = 0
        while t < sim_hours:
            failure_dt = rng.exponential(MTBF['starlink'])
            t += failure_dt
            if t < sim_hours:
                # Starlink outage during critical operation
                mttr = rng.exponential(MTTR['starlink'])
                # 20% chance of extended outage (>30 min)
                if rng.random() < 0.2:
                    mttr *= 5
                events.append({
                    'time': t,
                    'component': "Starlink_Terminal",
                    'comp_type': 'starlink',
                    'failure_type': FailureType.CLOUD_LOSS,
                    'recovery_time': mttr,
                    'recovery_end': t + mttr,
                })
                t += mttr
    
    return events


# ============================================================================
# Simulation Engine
# ============================================================================

def run_single_iteration(
    iteration: int,
    scenario: str,
    num_esp32: int = NUM_ESP32_NODES,
    num_jetsons: int = NUM_JETSON_BOARDS,
    sim_hours: float = SIMULATION_HOURS,
    seed: int = None,
) -> SimulationResult:
    """Run a single Monte Carlo iteration using event-driven simulation."""
    if seed is None:
        seed = SEED + iteration * 1000 + hash(scenario) % 10000
    
    rng = np.random.RandomState(seed)
    
    # Build topology
    esp32s, jetsons, links, cables = build_topology(num_esp32, num_jetsons)
    
    # Component collections
    all_components = {
        'esp32': esp32s,
        'jetson': [j.component for j in jetsons],
        'cable': cables,
        'rs422_tx': [l.transceiver for l in links],
    }
    
    # Generate failure events
    events = generate_failure_events(rng, all_components, scenario, sim_hours)
    events.sort(key=lambda e: e['time'])
    
    # Build timeline of all state changes
    # Each event has a start (failure) and end (recovery)
    timeline = []
    for idx, event in enumerate(events):
        timeline.append((event['time'], 'start', idx))
        timeline.append((event['recovery_end'], 'end', idx))
    timeline.sort(key=lambda x: (x[0], 0 if x[1] == 'end' else 1))
    
    # Simulate by processing timeline events
    result = SimulationResult(
        iteration=iteration,
        scenario=scenario,
    )
    
    active_failures = set()
    prev_time = 0.0
    system_uptime = 0.0
    total_data_loss = 0.0
    failure_count = 0
    recovery_times = []
    current_state = SystemState.FULL_OPERATION
    degraded_start = None
    first_failure_time = None
    
    quorum_threshold = (num_jetsons // 2) + 1
    
    def compute_cluster_state(active_set):
        """Compute number of active Jetsons given current failures."""
        n_active = num_jetsons
        has_grpc_loss = False
        for idx in active_set:
            ft = events[idx]['failure_type']
            if ft == FailureType.JETSON_BOARD:
                n_active -= 1
            elif ft == FailureType.GRPC_LOSS:
                has_grpc_loss = True
            elif ft == FailureType.POWER_FAILURE:
                n_active = max(0, n_active - 1)  # redundant PSU
            elif ft == FailureType.CASCADING:
                cascade_n = events[idx].get('cascade_secondary', 0)
                n_active = max(0, n_active - cascade_n // 2)
        return n_active, has_grpc_loss
    
    # Process timeline
    for t, action, idx in timeline:
        if t > sim_hours:
            break
        
        dt = t - prev_time
        
        # Accumulate metrics for the elapsed period
        if current_state == SystemState.FULL_OPERATION:
            system_uptime += dt
        elif current_state == SystemState.DEGRADED:
            system_uptime += dt * 0.5
        
        # Data loss accumulation
        if len(active_failures) > 0:
            for fidx in active_failures:
                ft = events[fidx]['failure_type']
                fkey = ft.name.lower()
                total_data_loss += DATA_LOSS_RATE.get(fkey, 100) * dt
        
        # Quorum loss accumulation
        n_active, has_grpc_loss = compute_cluster_state(active_failures)
        has_quorum = n_active >= quorum_threshold
        if not has_quorum:
            result.quorum_loss_hours += dt
        
        prev_time = t
        
        # Apply state change
        if action == 'start':
            active_failures.add(idx)
            failure_count += 1
            if first_failure_time is None:
                first_failure_time = t
            
            # Cascade secondary tracking
            if events[idx]['failure_type'] == FailureType.CASCADING:
                if 'cascade_secondary' in events[idx]:
                    result.cascading_count += events[idx]['cascade_secondary']
            
            # Byzantine detection tracking
            if events[idx]['failure_type'] == FailureType.BYZANTINE:
                result.byzantine_detected += 1
            
        else:  # action == 'end'
            if idx in active_failures:
                active_failures.discard(idx)
                recovery_times.append(events[idx]['recovery_time'])
        
        # Recompute cluster state
        n_active, has_grpc_loss = compute_cluster_state(active_failures)
        has_quorum = n_active >= quorum_threshold
        
        # Determine new system state
        if len(active_failures) == 0:
            if current_state != SystemState.FULL_OPERATION:
                if degraded_start is not None:
                    result.degraded_durations.append(t - degraded_start)
                    degraded_start = None
            current_state = SystemState.FULL_OPERATION
            
        elif has_quorum:
            if current_state == SystemState.FULL_OPERATION:
                degraded_start = t
            elif current_state in (SystemState.SAFE_STATE, SystemState.FAULT):
                # Recovering from safe/fault to degraded
                degraded_start = t
            current_state = SystemState.DEGRADED
            
        else:
            # No quorum
            if current_state not in (SystemState.SAFE_STATE, SystemState.FAULT):
                # Determine safe state vs fault
                if active_failures:
                    dominant_ft = events[min(active_failures)]['failure_type']
                    fkey = dominant_ft.name.lower()
                    safety_prob = SAFETY_STATE_PROB.get(fkey, 0.1)
                    if rng.random() < safety_prob:
                        current_state = SystemState.SAFE_STATE
                        result.total_safe_state_entries += 1
                    else:
                        current_state = SystemState.FAULT
                        result.total_fault_entries += 1
    
    # Final period accumulation
    dt = sim_hours - prev_time
    if current_state == SystemState.FULL_OPERATION:
        system_uptime += dt
    elif current_state == SystemState.DEGRADED:
        system_uptime += dt * 0.5
    if degraded_start is not None:
        result.degraded_durations.append(sim_hours - degraded_start)
    
    # Compute final metrics
    result.availability = system_uptime / sim_hours
    result.total_failures = failure_count
    result.total_downtime = sim_hours - system_uptime
    result.data_loss_bytes = total_data_loss
    
    if failure_count > 0:
        result.mtbf_actual = sim_hours / failure_count
        result.mttr_actual = sum(recovery_times) / len(recovery_times) if recovery_times else 0
    else:
        result.mtbf_actual = sim_hours
        result.mttr_actual = 0
    
    result.failure_events = events
    
    return result


def run_monte_carlo(
    scenario: str,
    num_iterations: int = NUM_ITERATIONS,
    sim_hours: float = SIMULATION_HOURS,
    num_esp32: int = NUM_ESP32_NODES,
    num_jetsons: int = NUM_JETSON_BOARDS,
) -> Dict:
    """Run Monte Carlo simulation for a scenario."""
    results = []
    for i in range(num_iterations):
        result = run_single_iteration(
            iteration=i,
            scenario=scenario,
            num_esp32=num_esp32,
            num_jetsons=num_jetsons,
            sim_hours=sim_hours,
        )
        results.append(result)
    
    # Aggregate results
    availabilities = [r.availability for r in results]
    failures = [r.total_failures for r in results]
    safe_entries = [r.total_safe_state_entries for r in results]
    fault_entries = [r.total_fault_entries for r in results]
    mttrs = [r.mttr_actual for r in results]
    mttbs = [r.mtbf_actual for r in results if r.total_failures > 0]
    data_losses = [r.data_loss_bytes for r in results]
    degraded_durs = [d for r in results for d in r.degraded_durations]
    quorum_losses = [r.quorum_loss_hours for r in results]
    
    return {
        'scenario': scenario,
        'num_iterations': num_iterations,
        'availability_mean': np.mean(availabilities),
        'availability_std': np.std(availabilities),
        'availability_p5': np.percentile(availabilities, 5),
        'availability_p95': np.percentile(availabilities, 95),
        'failures_mean': np.mean(failures),
        'failures_std': np.std(failures),
        'safe_state_mean': np.mean(safe_entries),
        'safe_state_std': np.std(safe_entries),
        'fault_entries_mean': np.mean(fault_entries),
        'fault_entries_std': np.std(fault_entries),
        'mttr_mean': np.mean(mttrs),
        'mttr_std': np.std(mttrs),
        'mtbf_mean': np.mean(mttbs) if mttbs else sim_hours,
        'mtbf_std': np.std(mttbs) if mttbs else 0,
        'data_loss_mean': np.mean(data_losses),
        'data_loss_std': np.std(data_losses),
        'data_loss_max': np.max(data_losses),
        'degraded_duration_mean': np.mean(degraded_durs) if degraded_durs else 0,
        'degraded_duration_std': np.std(degraded_durs) if degraded_durs else 0,
        'degraded_duration_median': np.median(degraded_durs) if degraded_durs else 0,
        'degraded_duration_p95': np.percentile(degraded_durs, 95) if degraded_durs else 0,
        'quorum_loss_mean': np.mean(quorum_losses),
        'quorum_loss_std': np.std(quorum_losses),
        'cascading_mean': np.mean([r.cascading_count for r in results]),
        'byzantine_detected_mean': np.mean([r.byzantine_detected for r in results]),
        'raw_results': results,
    }


# ============================================================================
# Quorum Analysis
# ============================================================================

def quorum_analysis(
    num_jetsons_list: List[int] = [3, 5, 7],
    jetson_mtbf: float = 100_000,
    jetson_mttr: float = 8.0,
    sim_hours: float = SIMULATION_HOURS,
    num_iterations: int = 300,
) -> Dict:
    """Analyze cluster quorum requirements using analytical + Monte Carlo approach."""
    results = {}
    
    for num_j in num_jetsons_list:
        rng = np.random.RandomState(SEED + num_j * 100)
        quorum_threshold = (num_j // 2) + 1
        
        quorum_loss_total = 0.0
        full_op_total = 0.0
        
        for _ in range(num_iterations):
            # Event-driven: generate failure/recovery events for each Jetson
            jetson_events = []  # (time, 'start'/'end', jetson_id)
            for j in range(num_j):
                t = 0.0
                while t < sim_hours:
                    failure_dt = rng.exponential(jetson_mtbf)
                    t += failure_dt
                    if t >= sim_hours:
                        break
                    recovery = rng.exponential(jetson_mttr)
                    jetson_events.append((t, 'start', j))
                    jetson_events.append((t + recovery, 'end', j))
                    t += recovery
            
            jetson_events.sort(key=lambda x: (x[0], 0 if x[1] == 'end' else 1))
            
            # Process events
            recovering = set()
            prev_t = 0.0
            quorum_loss = 0.0
            full_op_hours = 0.0
            
            for ev_t, ev_action, ev_jid in jetson_events:
                if ev_t > sim_hours:
                    break
                dt = ev_t - prev_t
                
                active = num_j - len(recovering)
                if active >= quorum_threshold:
                    if active == num_j:
                        full_op_hours += dt
                else:
                    quorum_loss += dt
                
                prev_t = ev_t
                if ev_action == 'start':
                    recovering.add(ev_jid)
                else:
                    recovering.discard(ev_jid)
            
            # Final period
            dt = sim_hours - prev_t
            active = num_j - len(recovering)
            if active >= quorum_threshold:
                if active == num_j:
                    full_op_hours += dt
            else:
                quorum_loss += dt
            
            quorum_loss_total += quorum_loss
            full_op_total += (full_op_hours / sim_hours) * 100
        
        results[f'jetson_{num_j}'] = {
            'cluster_size': num_j,
            'quorum_threshold': quorum_threshold,
            'mean_quorum_loss_hours': quorum_loss_total / num_iterations,
            'mean_availability': 1.0 - (quorum_loss_total / num_iterations / sim_hours),
            'full_operation_pct': full_op_total / num_iterations,
            'survives_n_minus_1': quorum_threshold <= num_j - 1,
            'survives_n_minus_2': quorum_threshold <= num_j - 2,
        }
    
    return results


# ============================================================================
# Bandwidth Analysis
# ============================================================================

def bandwidth_analysis() -> Dict:
    """Compute bandwidth utilization for the NEXUS network."""
    # RS-422 at 921600 baud
    baud_rate = 921600
    bits_per_byte = 10  # 8 data + 1 start + 1 stop (no parity for RS-422)
    raw_bytes_per_sec = baud_rate / bits_per_byte  # 92160 B/s
    
    # NEXUS wire protocol: COBS framing + CRC-16 + message header
    # Typical telemetry message: ~60 bytes payload + 15 bytes overhead = 75 bytes
    telemetry_msg_size = 75  # bytes
    telemetry_rate = 10  # Hz per ESP32 (10 messages per second)
    
    # Command message: ~30 bytes
    command_msg_size = 45  # bytes
    command_rate = 1  # Hz per ESP32 (1 command per second on average)
    
    # OTA firmware chunk: 256 bytes payload + overhead = 275 bytes
    ota_chunk_size = 275
    ota_rate = 50  # chunks/sec during update
    
    # Per-ESP32 bandwidth utilization
    esp32_bandwidth = {
        'baud_rate': baud_rate,
        'max_bytes_per_sec': raw_bytes_per_sec,
        'telemetry': {
            'msg_size': telemetry_msg_size,
            'rate_hz': telemetry_rate,
            'bytes_per_sec': telemetry_msg_size * telemetry_rate,
            'pct_of_max': (telemetry_msg_size * telemetry_rate / raw_bytes_per_sec) * 100,
        },
        'commands': {
            'msg_size': command_msg_size,
            'rate_hz': command_rate,
            'bytes_per_sec': command_msg_size * command_rate,
            'pct_of_max': (command_msg_size * command_rate / raw_bytes_per_sec) * 100,
        },
        'ota_update': {
            'msg_size': ota_chunk_size,
            'rate_hz': ota_rate,
            'bytes_per_sec': ota_chunk_size * ota_rate,
            'pct_of_max': (ota_chunk_size * ota_rate / raw_bytes_per_sec) * 100,
        },
    }
    
    # How many ESP32s per Jetson before saturation?
    normal_utilization = esp32_bandwidth['telemetry']['bytes_per_sec'] + esp32_bandwidth['commands']['bytes_per_sec']
    max_esp32s_normal = int(raw_bytes_per_sec / normal_utilization)
    max_esp32s_with_ota = int(raw_bytes_per_sec / (normal_utilization + esp32_bandwidth['ota_update']['bytes_per_sec']))
    
    # Jetson aggregation
    esp32_per_jetson = ESP32S_PER_JETSON
    total_serial_bandwidth = normal_utilization * esp32_per_jetson
    
    # gRPC between Jetsons
    grpc_msg_size = 1024  # bytes typical observation sync
    grpc_rate = 100  # Hz per Jetson pair
    grpc_bandwidth = grpc_msg_size * grpc_rate  # bytes/sec
    
    # MQTT
    mqtt_msg_size = 512  # bytes
    mqtt_rate = 50  # Hz
    mqtt_bandwidth = mqtt_msg_size * mqtt_rate
    
    # Starlink (cloud)
    starlink_avg_down = 50e6 / 8  # 50 Mbps average = 6.25 MB/s
    starlink_avg_up = 5e6 / 8  # 5 Mbps average = 625 KB/s
    cloud_sync_rate = 100  # KB/s typical
    cloud_sync_pct = (cloud_sync_rate * 1024 / starlink_avg_up) * 100
    
    return {
        'rs422_per_link': esp32_bandwidth,
        'aggregation': {
            'esp32s_per_jetson': esp32_per_jetson,
            'total_serial_bytes_per_sec': total_serial_bandwidth,
            'serial_utilization_pct': (total_serial_bandwidth / raw_bytes_per_sec) * 100,
            'max_esp32s_normal_ops': max_esp32s_normal,
            'max_esp32s_during_ota': max_esp32s_with_ota,
        },
        'jetson_communication': {
            'grpc_bytes_per_sec': grpc_bandwidth,
            'mqtt_bytes_per_sec': mqtt_bandwidth,
            'total_lan_bytes_per_sec': grpc_bandwidth + mqtt_bandwidth,
        },
        'cloud': {
            'starlink_avg_up_bytes_per_sec': starlink_avg_up,
            'starlink_avg_down_bytes_per_sec': starlink_avg_down,
            'cloud_sync_bytes_per_sec': cloud_sync_rate * 1024,
            'cloud_sync_utilization_pct': cloud_sync_pct,
        },
    }


# ============================================================================
# Visualization
# ============================================================================

def generate_6_panel_figure(
    all_scenario_results: Dict[str, Dict],
    quorum_results: Dict,
    bw_results: Dict,
    output_path: str,
):
    """Generate the 6-panel figure for the network failure analysis."""
    
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(
        'NEXUS Network Failure Simulation — Monte Carlo Analysis\n'
        f'{NUM_ESP32_NODES} ESP32 Nodes · {NUM_JETSON_BOARDS} Jetson Cluster · '
        f'{SIMULATION_HOURS:,}h Simulation · {NUM_ITERATIONS} Iterations',
        fontsize=14, fontweight='bold', y=0.98
    )
    
    gs = gridspec.GridSpec(2, 3, hspace=0.35, wspace=0.30,
                           left=0.06, right=0.97, top=0.90, bottom=0.06)
    
    scenarios = list(all_scenario_results.keys())
    scenario_labels = [
        'ESP32\nFailure',
        'Jetson\nFailure',
        'Cable\nCut',
        'gRPC\nLoss',
        'Power\nFailure',
        'Cascading\nFailure',
        'Byzantine\nFailure',
        'Cloud\nLoss',
    ]
    colors = plt.cm.Set2(np.linspace(0, 1, len(scenarios)))
    
    # Panel 1: System Availability by Scenario (bar chart)
    ax1 = fig.add_subplot(gs[0, 0])
    means = [all_scenario_results[s]['availability_mean'] * 100 for s in scenarios]
    stds = [all_scenario_results[s]['availability_std'] * 100 for s in scenarios]
    p5s = [all_scenario_results[s]['availability_p5'] * 100 for s in scenarios]
    p95s = [all_scenario_results[s]['availability_p95'] * 100 for s in scenarios]
    
    x = np.arange(len(scenarios))
    bars = ax1.bar(x, means, width=0.6, color=colors, edgecolor='black', linewidth=0.5)
    # Clamp error bars to non-negative
    yerr_lo = np.maximum(0, np.array(means) - np.array(p5s))
    yerr_hi = np.maximum(0, np.array(p95s) - np.array(means))
    if yerr_lo.max() > 0.001 or yerr_hi.max() > 0.001:
        ax1.errorbar(x, means, yerr=[yerr_lo, yerr_hi],
                     fmt='none', color='black', capsize=3, linewidth=1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenario_labels[:len(scenarios)], fontsize=7, ha='center')
    ax1.set_ylabel('Availability (%)')
    ax1.set_title('(a) System Availability by Scenario', fontsize=10, fontweight='bold')
    y_min = max(99.5, min(means) - max(yerr_lo) - 0.5)
    ax1.set_ylim(y_min, 100.05)
    ax1.axhline(y=99.9, color='red', linestyle='--', alpha=0.5, label='99.9% target')
    ax1.legend(fontsize=7, loc='lower left')
    ax1.grid(axis='y', alpha=0.3)
    
    # Panel 2: MTBF and MTTR comparison
    ax2 = fig.add_subplot(gs[0, 1])
    mtbf_vals = [all_scenario_results[s]['mtbf_mean'] for s in scenarios]
    mttr_vals = [all_scenario_results[s]['mttr_mean'] for s in scenarios]
    
    # Normalize for display (log scale)
    ax2_twin = ax2.twinx()
    
    width = 0.35
    ax2.bar(x - width/2, [np.log10(max(v, 1)) for v in mtbf_vals], width,
            color='#2196F3', alpha=0.8, label='MTBF (log₁₀ hrs)')
    ax2_twin.bar(x + width/2, mttr_vals, width,
                 color='#FF5722', alpha=0.8, label='MTTR (hrs)')
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenario_labels[:len(scenarios)], fontsize=7, ha='center')
    ax2.set_ylabel('MTBF (log₁₀ hours)', color='#2196F3')
    ax2_twin.set_ylabel('MTTR (hours)', color='#FF5722')
    ax2.set_title('(b) MTBF vs MTTR by Scenario', fontsize=10, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper right')
    
    # Panel 3: Safety State Entry & Data Loss
    ax3 = fig.add_subplot(gs[0, 2])
    safe_means = [all_scenario_results[s]['safe_state_mean'] for s in scenarios]
    fault_means = [all_scenario_results[s]['fault_entries_mean'] for s in scenarios]
    data_losses = [all_scenario_results[s]['data_loss_mean'] / 1024 for s in scenarios]  # KB
    
    ax3.bar(x - width/2, safe_means, width, color='#4CAF50', alpha=0.8, label='Safe State Entries')
    ax3.bar(x + width/2, fault_means, width, color='#F44336', alpha=0.8, label='Fault Entries')
    
    ax3_twin = ax3.twinx()
    ax3_twin.plot(x, data_losses, 'D-', color='#FF9800', markersize=6, linewidth=1.5,
                  label='Data Loss (KB)')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(scenario_labels[:len(scenarios)], fontsize=7, ha='center')
    ax3.set_ylabel('State Entries (count)')
    ax3_twin.set_ylabel('Data Loss (KB)', color='#FF9800')
    ax3.set_title('(c) Safety State Entries & Data Loss', fontsize=10, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='upper left')
    
    # Panel 4: Degraded Mode Duration Distribution (violin plot)
    ax4 = fig.add_subplot(gs[1, 0])
    all_degraded = []
    labels_violin = []
    for s in scenarios:
        durs = []
        for r in all_scenario_results[s]['raw_results']:
            durs.extend(r.degraded_durations)
        if durs:
            all_degraded.append(durs)
            labels_violin.append(s.replace('_', '\n'))
    
    if all_degraded:
        parts = ax4.violinplot(all_degraded, showmeans=True, showmedians=True, showextrema=False)
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i])
            pc.set_alpha(0.7)
        parts['cmeans'].set_color('red')
        parts['cmedians'].set_color('blue')
        
        ax4.set_xticks(range(1, len(labels_violin) + 1))
        ax4.set_xticklabels(labels_violin, fontsize=6, ha='center')
        ax4.set_ylabel('Duration (hours)')
        ax4.set_title('(d) Degraded Mode Duration Distribution', fontsize=10, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)
    
    # Panel 5: Quorum Analysis
    ax5 = fig.add_subplot(gs[1, 1])
    cluster_sizes = sorted(quorum_results.keys())
    avail_by_size = [quorum_results[k]['mean_availability'] * 100 for k in cluster_sizes]
    full_op = [quorum_results[k]['full_operation_pct'] for k in cluster_sizes]
    quorum_loss = [quorum_results[k]['mean_quorum_loss_hours'] for k in cluster_sizes]
    sizes = [quorum_results[k]['cluster_size'] for k in cluster_sizes]
    
    x_q = np.arange(len(sizes))
    ax5.bar(x_q - width/2, avail_by_size, width, color='#3F51B5', alpha=0.8, label='Quorum Availability')
    ax5.bar(x_q + width/2, full_op, width, color='#009688', alpha=0.8, label='Full Operation %')
    
    ax5.set_xticks(x_q)
    ax5.set_xticklabels([f'{s}-Jetson\nCluster' for s in sizes], fontsize=9)
    ax5.set_ylabel('Percentage (%)')
    ax5.set_title('(e) Cluster Quorum Analysis', fontsize=10, fontweight='bold')
    ax5.legend(fontsize=8)
    ax5.grid(axis='y', alpha=0.3)
    ax5.set_ylim(min(avail_by_size) - 0.5, max(max(avail_by_size), max(full_op)) + 1)
    
    # Add quorum threshold annotations
    for i, k in enumerate(cluster_sizes):
        qt = quorum_results[k]['quorum_threshold']
        ax5.annotate(f'Quorum: {qt}/{quorum_results[k]["cluster_size"]}',
                     xy=(i, avail_by_size[i]), xytext=(i, avail_by_size[i] - 0.3),
                     ha='center', fontsize=7, color='red',
                     arrowprops=dict(arrowstyle='->', color='red', lw=0.5))
    
    # Panel 6: Bandwidth Utilization
    ax6 = fig.add_subplot(gs[1, 2])
    
    bw_categories = ['Telemetry\n(10 Hz)', 'Commands\n(1 Hz)', 'OTA Update\n(50 Hz)', 
                     'gRPC Sync\n(100 Hz)', 'MQTT\n(50 Hz)', 'Cloud Sync']
    bw_values = [
        bw_results['rs422_per_link']['telemetry']['pct_of_max'],
        bw_results['rs422_per_link']['commands']['pct_of_max'],
        bw_results['rs422_per_link']['ota_update']['pct_of_max'],
        0, 0, 0  # placeholder for LAN and cloud
    ]
    bw_colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63', '#00BCD4']
    
    # Per-link bandwidth
    bars6 = ax6.barh(range(len(bw_categories)), bw_values, color=bw_colors, alpha=0.8,
                     edgecolor='black', linewidth=0.5)
    
    # Add aggregate info as text
    agg_text = (
        f"Per-Jetson Serial Load: {bw_results['aggregation']['serial_utilization_pct']:.1f}%\n"
        f"Max ESP32s (normal): {bw_results['aggregation']['max_esp32s_normal_ops']}\n"
        f"Max ESP32s (OTA): {bw_results['aggregation']['max_esp32s_during_ota']}\n"
        f"Cloud Sync: {bw_results['cloud']['cloud_sync_utilization_pct']:.1f}% of Starlink uplink"
    )
    ax6.text(0.98, 0.98, agg_text, transform=ax6.transAxes, fontsize=7,
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax6.set_yticks(range(len(bw_categories)))
    ax6.set_yticklabels(bw_categories, fontsize=8)
    ax6.set_xlabel('Bandwidth Utilization (% of RS-422 link)')
    ax6.set_title('(f) Bandwidth Analysis (per RS-422 link)', fontsize=10, fontweight='bold')
    ax6.grid(axis='x', alpha=0.3)
    ax6.axvline(x=80, color='red', linestyle='--', alpha=0.5, label='80% saturation')
    ax6.legend(fontsize=7, loc='lower right')
    
    # Add value labels on bars
    for bar, val in zip(bars6, bw_values):
        if val > 0:
            ax6.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                     f'{val:.1f}%', va='center', fontsize=7)
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Figure saved to {output_path}")


# ============================================================================
# Topology Diagram Generator
# ============================================================================

def generate_topology_diagram(output_path: str):
    """Generate a network topology diagram showing the physical layout."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('NEXUS Network Topology — Physical Architecture',
                 fontsize=14, fontweight='bold')
    
    # Draw Jetson boards (top row)
    jetson_positions = [(2, 7), (7, 7), (12, 7)]
    for i, (x, y) in enumerate(jetson_positions):
        rect = FancyBboxPatch((x-1.2, y-0.6), 2.4, 1.2,
                               boxstyle="round,pad=0.1",
                               facecolor='#1565C0', edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        label = f"Jetson {i}\n({'LEADER' if i == 0 else 'Peer'})"
        ax.text(x, y, label, ha='center', va='center', fontsize=9,
                color='white', fontweight='bold')
    
    # Draw ESP32 nodes (bottom rows)
    esp32_positions = []
    for j_idx in range(NUM_JETSON_BOARDS):
        base_x = jetson_positions[j_idx][0]
        for esp_idx in range(ESP32S_PER_JETSON):
            x = base_x - 1.5 + esp_idx * 1.0
            y = 3.0 + (esp_idx % 2) * 0.0
            esp32_positions.append((x, y, j_idx))
    
    for i, (x, y, j_idx) in enumerate(esp32_positions):
        rect = FancyBboxPatch((x-0.35, y-0.35), 0.7, 0.7,
                               boxstyle="round,pad=0.05",
                               facecolor='#2E7D32', edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(x, y, f'E{i:02d}', ha='center', va='center', fontsize=7,
                color='white', fontweight='bold')
        
        # Draw RS-422 link to Jetson
        jx, jy = jetson_positions[j_idx]
        ax.annotate('', xy=(jx, jy - 0.7), xytext=(x, y + 0.4),
                    arrowprops=dict(arrowstyle='<->', color='#FF6F00', lw=1.5,
                                   connectionstyle='arc3,rad=0.0'))
        # Label RS-422
        mid_x, mid_y = (x + jx) / 2, (y + jy) / 2 - 0.5
        if i % 2 == 0:
            ax.text(mid_x, mid_y, 'RS-422', fontsize=5, color='#FF6F00',
                    ha='center', rotation=90, alpha=0.7)
    
    # Draw gRPC links between Jetsons (mesh)
    for i in range(len(jetson_positions)):
        for j in range(i+1, len(jetson_positions)):
            x1, y1 = jetson_positions[i]
            x2, y2 = jetson_positions[j]
            ax.annotate('', xy=(x2-0.8, y2+0.7), xytext=(x1+0.8, y1+0.7),
                        arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=2,
                                       connectionstyle='arc3,rad=0.0'))
            mid_x = (x1 + x2) / 2
            ax.text(mid_x, y1 + 1.0, 'gRPC', fontsize=7, color='#9C27B0',
                    ha='center', fontweight='bold')
    
    # Draw MQTT broker
    mqtt_x, mqtt_y = 7, 5
    rect = FancyBboxPatch((mqtt_x-0.8, mqtt_y-0.4), 1.6, 0.8,
                           boxstyle="round,pad=0.1",
                           facecolor='#E91E63', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(mqtt_x, mqtt_y, 'MQTT\nBroker', ha='center', va='center',
            fontsize=8, color='white', fontweight='bold')
    
    # Connect Jetsons to MQTT
    for jx, jy in jetson_positions:
        ax.plot([jx, mqtt_x], [jy-0.7, mqtt_y+0.5], '--', color='#E91E63',
                linewidth=1, alpha=0.5)
    
    # Draw Cloud (Starlink)
    cloud_x, cloud_y = 7, 8.5
    ax.text(cloud_x, cloud_y, '☁ Cloud (Starlink)', ha='center', va='center',
            fontsize=10, color='#0288D1', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#0288D1'))
    ax.annotate('', xy=(cloud_x, cloud_y-0.5), xytext=(7, 7.7),
                arrowprops=dict(arrowstyle='->', color='#0288D1', lw=2))
    
    # Legend
    legend_items = [
        ('#1565C0', 'Jetson Orin Nano (cognitive)'),
        ('#2E7D32', 'ESP32-S3 (sensor/actuator)'),
        ('#FF6F00', 'RS-422 Serial (921600 baud)'),
        ('#9C27B0', 'gRPC (LAN inter-Jetson)'),
        ('#E91E63', 'MQTT (event bus)'),
        ('#0288D1', 'Starlink (cloud sync)'),
    ]
    for i, (color, label) in enumerate(legend_items):
        ax.add_patch(plt.Rectangle((0.2, 0.8 - i * 0.35), 0.4, 0.25,
                                    facecolor=color, edgecolor='black'))
        ax.text(0.8, 0.92 - i * 0.35, label, fontsize=7, va='center')
    
    # Specs text
    specs = (
        f"Topology: {NUM_ESP32_NODES} ESP32 → {NUM_JETSON_BOARDS} Jetson (star)\n"
        f"Serial: RS-422 point-to-point, 921600 baud\n"
        f"Inter-Jetson: gRPC + MQTT over Gigabit LAN\n"
        f"Cloud: Starlink LEO satellite terminal\n"
        f"Quorum: {NUM_JETSON_BOARDS//2 + 1}/{NUM_JETSON_BOARDS} Jetson majority"
    )
    ax.text(14.5, 1.5, specs, fontsize=7, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='gray', alpha=0.9),
            family='monospace')
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Topology diagram saved to {output_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run all simulations and generate outputs."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    figures_dir = os.path.join(os.path.dirname(base_dir), 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    print("=" * 70)
    print("NEXUS Network Failure Simulation — Round 4A")
    print("=" * 70)
    
    # Define scenarios
    scenarios = [
        'esp32_failure',
        'jetson_failure',
        'cable_cut',
        'grpc_loss',
        'power_failure',
        'cascading',
        'byzantine',
        'cloud_loss',
    ]
    
    # Run Monte Carlo for each scenario
    print(f"\nRunning {NUM_ITERATIONS} Monte Carlo iterations per scenario...")
    print(f"Simulation period: {SIMULATION_HOURS:,} hours")
    all_results = {}
    
    for scenario in scenarios:
        print(f"  Simulating: {scenario}...", end=' ', flush=True)
        t0 = time_module.time()
        result = run_monte_carlo(scenario, NUM_ITERATIONS, SIMULATION_HOURS)
        elapsed = time_module.time() - t0
        all_results[scenario] = result
        print(f"done ({elapsed:.1f}s) — Availability: {result['availability_mean']*100:.3f}%")
    
    # Quorum analysis
    print(f"\nRunning quorum analysis for 3, 5, 7-Jetson clusters...")
    quorum_results = quorum_analysis()
    for k, v in quorum_results.items():
        print(f"  {k}: availability={v['mean_availability']*100:.4f}%, "
              f"quorum_loss={v['mean_quorum_loss_hours']:.2f}h")
    
    # Bandwidth analysis
    print(f"\nRunning bandwidth analysis...")
    bw_results = bandwidth_analysis()
    print(f"  RS-422 max: {bw_results['rs422_per_link']['max_bytes_per_sec']:.0f} B/s")
    print(f"  Per-Jetson serial load: {bw_results['aggregation']['serial_utilization_pct']:.1f}%")
    print(f"  Max ESP32s (normal): {bw_results['aggregation']['max_esp32s_normal_ops']}")
    print(f"  Max ESP32s (OTA): {bw_results['aggregation']['max_esp32s_during_ota']}")
    print(f"  Cloud sync: {bw_results['cloud']['cloud_sync_utilization_pct']:.1f}% of uplink")
    
    # Generate figures
    print(f"\nGenerating figures...")
    fig_path = os.path.join(figures_dir, 'network_failure.png')
    generate_6_panel_figure(all_results, quorum_results, bw_results, fig_path)
    
    topo_path = os.path.join(figures_dir, 'network_topology.png')
    generate_topology_diagram(topo_path)
    
    # Save data
    data_path = os.path.join(figures_dir, 'network_simulation_data.json')
    save_data = {}
    for s, r in all_results.items():
        save_data[s] = {k: v for k, v in r.items() if k != 'raw_results'}
    save_data['quorum_analysis'] = quorum_results
    save_data['bandwidth_analysis'] = bw_results
    save_data['config'] = {
        'num_esp32': NUM_ESP32_NODES,
        'num_jetsons': NUM_JETSON_BOARDS,
        'simulation_hours': SIMULATION_HOURS,
        'num_iterations': NUM_ITERATIONS,
        'mtbf': MTBF,
        'mttr': MTTR,
    }
    
    with open(data_path, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"Data saved to {data_path}")
    
    # Print summary table
    print("\n" + "=" * 70)
    print("SIMULATION SUMMARY")
    print("=" * 70)
    print(f"{'Scenario':<20} {'Availability':>12} {'MTBF (hrs)':>12} {'MTTR (hrs)':>12} {'Safe State':>10}")
    print("-" * 70)
    for s in scenarios:
        r = all_results[s]
        print(f"{s:<20} {r['availability_mean']*100:>11.3f}% {r['mtbf_mean']:>12.1f} "
              f"{r['mttr_mean']:>12.3f} {r['safe_state_mean']:>10.2f}")
    
    print("\n" + "=" * 70)
    print("QUORUM ANALYSIS SUMMARY")
    print("=" * 70)
    for k, v in quorum_results.items():
        print(f"  {v['cluster_size']}-Jetson: Quorum={v['quorum_threshold']}/{v['cluster_size']}, "
              f"Availability={v['mean_availability']*100:.4f}%, "
              f"Full Op={v['full_operation_pct']:.2f}%")
    
    print("\n✓ All simulations complete.")
    return all_results


if __name__ == '__main__':
    main()
