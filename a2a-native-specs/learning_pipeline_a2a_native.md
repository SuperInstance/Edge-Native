# Learning Pipeline — A2A-Native Specification (Rosetta Stone)

**Document ID**: NEXUS-A2A-LEARN-001
**Version**: 1.0.0
**Classification**: Implementation-Ready (Jetson Orin NX)
**Source Mapping**: NEXUS-JETSON-LP-001 → A2A-Native Interpretation
**Date**: 2025-07-12

---

## Table of Contents

1. [Learning Pipeline — Agent-Native Flow](#1-learning-pipeline--agent-native-flow)
2. [Pattern Discovery — Agent Interpretation](#2-pattern-discovery--agent-interpretation)
3. [Reflex Synthesis — Agent as Compiler](#3-reflex-synthesis--agent-as-compiler)
4. [A/B Testing — Agent-Managed](#4-ab-testing--agent-managed)
5. [Fleet Learning — Cross-Vessel Knowledge Transfer](#5-fleet-learning--cross-vessel-knowledge-transfer)
6. [The Seasonal Evolution Cycle — Agent-Native](#6-the-seasonal-evolution-cycle--agent-native)
7. [Example: Complete Learning Loop](#7-example-complete-learning-loop)

---

## 1. Learning Pipeline — Agent-Native Flow

### 1.1 The 6 Stages Re-Described for Agent Interpretation

The NEXUS learning pipeline transforms raw sensor observations into deployed, trusted reflex bytecodes. In the original H2M (Human-to-Machine) pipeline, humans initiate and supervise each stage. In the A2A-native pipeline, agents own the process end-to-end, with humans remaining as constitutional authorities.

The six stages, re-interpreted for agents:

| # | Original Stage | A2A-Native Stage | Agent Role | Human Role |
|---|---------------|-----------------|------------|------------|
| 1 | **Observe** | **Agent Observe** | Agent manages ObservationSession lifecycle, tags data, triggers session close | None (autonomous) |
| 2 | **Discover** | **Agent Discover** | Agent runs 5 pattern discovery algorithms, filters results, ranks candidates | None (autonomous) |
| 3 | **Synthesize** | **Agent Synthesize** | Agent generates reflex JSON from discovered patterns via LLM | Review at L0-L3, approve at L4-L5 |
| 4 | **Validate** | **Agent Validate** | Agent runs 4-tier validation pipeline (syntax, semantic, safety, simulation) | Review Tier 4 failures at L0-L3 |
| 5 | **A/B Test** | **Agent A/B Test** | Agent designs, executes, and evaluates A/B tests | Approve promotion at L0-L3 |
| 6 | **Deploy** | **Agent Deploy** | Agent deploys bytecode, monitors post-deployment metrics | Override capability at all levels |

### 1.2 How Agents Participate in Each Stage

**Stage 1 — Agent Observe**: The observation agent manages `ObservationSession` objects on the Jetson. It records `UnifiedObservation` records (72 fields per row) at 100 Hz into Parquet files on NVMe SSD. The agent automatically opens sessions when the vessel is under way, tags sessions with contextual metadata (weather, traffic density, operating mode), and closes sessions after a minimum duration or when a significant event occurs. The agent also manages the storage tier lifecycle (HOT → WARM → COLD → ARCHIVE) via cron jobs.

**Stage 2 — Agent Discover**: The learning agent triggers pattern discovery after each session close. It runs the 5 algorithms (cross-correlation, BOCPD, HDBSCAN, temporal mining, Bayesian reward inference) in parallel on the Jetson's 4-thread pool. The agent then filters results: only correlations with |r| ≥ 0.6 and p_corrected < 0.05 are kept; only change points with confidence > 0.5 are kept; only temporal rules with consistency > 0.6 and ≥ 5 occurrences are kept.

**Stage 3 — Agent Synthesize**: The learning agent formulates a system prompt incorporating the discovered patterns, current context (sensor readings, reward weights, vessel configuration), and safety constraints. It invokes the on-device LLM (Qwen2.5-Coder-7B, quantized to Q4_K_M) to generate a reflex JSON candidate. If on-device generation fails (timeout, quality issues), the agent falls back to the cloud LLM (GPT-4 class).

**Stage 4 — Agent Validate**: The safety agent independently validates the reflex JSON through 4 tiers:
- Tier 1 (Syntax): JSON schema compliance, field validation — 100ms timeout
- Tier 2 (Semantic): Logical consistency, dependency ordering — 500ms timeout
- Tier 3 (Safety): Obstacle guards, actuator limits, duration constraints — 1000ms timeout
- Tier 4 (Simulation): 100 perturbed replay scenarios on GPU — 60s timeout

**Stage 5 — Agent A/B Test**: The A/B testing agent designs the test configuration (randomization method, stopping criteria, safety limits), arms the test (loads both control and treatment reflexes), monitors execution (checks rollback conditions every trigger), and evaluates results (paired t-test, Cohen's d, 95% CI).

**Stage 6 — Agent Deploy**: The deployment agent pushes the validated bytecode to the ESP32 via the wire protocol (ROLE_ASSIGN + LOAD_PROGRAM messages), monitors post-deployment metrics (fuel efficiency, heading accuracy, override frequency), and manages rollback if post-deployment performance degrades.

### 1.3 Human-in-the-Loop Requirements by Autonomy Level

| Autonomy Level | Observation | Discovery | Synthesis | Validation | A/B Test | Deploy |
|---------------|-------------|-----------|-----------|------------|----------|--------|
| L0 (Disabled) | Human | Human | Human | Human | Human | Human |
| L1 (Advisory) | Agent | Agent | Agent proposes, human reviews | Agent, human reviews failures | Agent proposes, human approves | Human only |
| L2 (Supervised) | Agent | Agent | Agent proposes, human reviews | Agent, human reviews failures | Agent proposes, human approves | Human only |
| L3 (Semi-Auto) | Agent | Agent | Agent proposes, human reviews | Agent | Agent proposes, human approves | Agent, human reachable |
| L4 (High Auto) | Agent | Agent | Agent | Agent | Agent | Agent, human monitoring |
| L5 (Full Auto) | Agent | Agent | Agent | Agent | Agent | Agent, async notification |

**Key transitions**:
- **L1→L2**: Human moves from reviewing all proposals to reviewing only failures and approvals.
- **L2→L3**: Human no longer reviews proposals at all; agent generates and validates independently. Human still approves A/B test results and must be reachable within 30 seconds.
- **L3→L4**: Agent manages the full pipeline including A/B tests. Human monitors at 5-minute intervals.
- **L4→L5**: Agent operates independently. Human is notified asynchronously. Emergency intervention remains available.

### 1.4 The Agent-Native Variant: End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    A2A-NATIVE LEARNING PIPELINE                         │
│                                                                         │
│  Agent ──► Observe ──► Discover ──► Synthesize ──► Validate ──► Deploy  │
│    │         (100Hz)     (5 algos)     (LLM)      (4 tiers)   (Wire)  │
│    │                                                          │        │
│    │                                              ┌───────────┘        │
│    │                                              ▼                    │
│    │                                       A/B Test (Agent)           │
│    │                                      ┌──────────────┐           │
│    │                                      │  Control vs   │           │
│    │                                      │  Treatment    │           │
│    │                                      │  Paired t-test│           │
│    │                                      │  Auto-rollback│           │
│    │                                      └──────┬───────┘           │
│    │                                             │                    │
│    │            ┌────────────────────────────────┘                    │
│    │            ▼                                                      │
│    │     Trust Agent (continuous)                                      │
│    │     ┌──────────────────────┐                                      │
│    │     │  Compute T(t) per    │                                      │
│    │     │  subsystem, apply    │                                      │
│    │     │  0.5× for agent code │                                      │
│    │     └──────────────────────┘                                      │
│    │                                                                  │
│    └──── Human (constitutional authority, L0-L3: review/approve)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pattern Discovery — Agent Interpretation

### 2.1 Cross-Correlation Scanner — "What Moves Together?"

**What it discovers**: Time-lagged relationships between sensor variables and actuator commands. Given 72 observation fields, the scanner evaluates all C(72,2) = 2,556 variable pairs at lags from -60s to +60s in 100ms steps.

**Agent interpretation**: The cross-correlation scanner tells the agent: "When variable A changes, variable B changes N seconds later with correlation coefficient r." For example, it might discover that `wind_speed_m_s` leads `rudder_angle_deg` by 3.2 seconds with r = 0.72, meaning the pilot (or autopilot) adjusts the rudder approximately 3 seconds after a wind gust.

**How an agent uses the discoveries**:
1. **Reflex generation**: If wind leads rudder with r > 0.6, the agent can synthesize a wind-compensation reflex: "When wind speed changes by > 2 m/s, preemptively adjust rudder by (wind_delta × gain) with a 3-second lead."
2. **Anomaly detection**: If a previously strong correlation weakens (e.g., wind→rudder drops from r=0.72 to r=0.35), the agent flags this as a potential actuator fault (rudder not responding to wind changes).
3. **Performance optimization**: If the agent discovers that throttle_pct leads fuel_flow_L_h with r=0.95 and zero lag, this confirms the fuel flow sensor is accurately tracking throttle commands — a basic sanity check.

**Output format**: A list of `CorrelationRecord` objects sorted by |correlation| descending, each containing variable names, lag in seconds, Pearson r, Bonferroni-corrected p-value, and effect direction.

**Performance**: ~8 seconds per 1-hour session on Jetson Orin NX. Typical output: < 50 significant correlations per session.

### 2.2 BOCPD — "When Did Something Change?"

**What it discovers**: Abrupt shifts in the statistical properties (mean, variance) of sensor time series using Bayesian Online Change Point Detection (Adams & MacKay, 2007).

**Agent interpretation**: BOCPD tells the agent: "At timestamp T, the statistical properties of sensor X changed. Before T, the mean was μ₁ with std σ₁; after T, the mean is μ₂ with std σ₂." For example, it might detect that `engine_temp_c` shifted from 78°C ± 2°C to 85°C ± 3°C at a specific timestamp, indicating a potential cooling system degradation.

**How an agent uses the discoveries**:
1. **Threshold adaptation**: If BOCPD detects a change in `water_temp_c` from 15°C to 19°C (seasonal warming), the agent can propose adjusting cooling system thresholds accordingly.
2. **Predictive maintenance**: A change in `fuel_flow_L_h` mean from 12 L/h to 15 L/h at constant speed suggests engine degradation. The agent generates a maintenance recommendation reflex.
3. **Reflex triggering**: Change points can serve as reflex triggers. "If engine_temp_c mean shifts upward by > 5°C within 1 hour, activate pre-emptive cooling protocol."

**Parameters**: hazard_lambda = 0.01 (expects ~100 observations between changes), run_length_threshold = 100 (minimum 100 observations between reported changes, preventing spurious reports). Applied to all continuous sensor columns in parallel (4-thread pool on Jetson).

### 2.3 HDBSCAN Behavioral Clustering — "What Kinds of Behavior Exist?"

**What it discovers**: Groups similar segments of vessel behavior into distinct clusters (e.g., "cruising," "docking," "rough-weather maneuvering," "station-keeping"). Uses HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise) on PCA-reduced feature vectors.

**Agent interpretation**: HDBSCAN tells the agent: "The vessel exhibits N distinct behavioral modes. Mode 1 (cruising) is characterized by speed 5-7 m/s, low roll, minimal rudder activity. Mode 2 (docking) is characterized by speed 0-2 m/s, high bow thruster activity, frequent rudder changes."

**Feature extraction**: For each 10-second non-overlapping window, 8 sensor columns × 5 statistical features (mean, std, min, max, spectral centroid) = 40 dimensions → PCA to 5 components → HDBSCAN clustering.

**How an agent uses the discoveries**:
1. **Context-aware reflex selection**: The agent can load different reflex sets based on the current behavioral cluster. In "rough-weather maneuvering" mode, load conservative reflexes with wider safety margins; in "cruising" mode, load efficiency-optimized reflexes.
2. **Anomaly detection**: If the current behavior doesn't match any known cluster (HDBSCAN label = -1, "noise"), the agent flags this as anomalous behavior requiring investigation.
3. **Reflex scope**: A reflex discovered during "cruising" mode may not be appropriate for "docking" mode. The agent tags reflexes with their discovery context cluster.

### 2.4 Temporal Pattern Mining — "What Typically Happens After X?"

**What it discovers**: Recurrent event-response patterns: "When X happens, the pilot (or autopilot) typically does Y within N seconds." Uses Dynamic Time Warping (DTW) to cluster response sequences and identifies consistent response patterns.

**Agent interpretation**: Temporal mining tells the agent: "In 85% of the 23 observed occurrences where wind_speed_m_s exceeded 12 m/s, the pilot reduced throttle_pct by 15-25% within 1.5 seconds and adjusted rudder_angle_deg by -8 to -15°." This is a directly actionable pattern — the agent can propose a reflex that automates this response.

**Event definition language**:
```
event := condition ('AND' condition)*
condition := variable comparator threshold
comparator := '>' | '>=' | '<' | '<=' | '==' | '!=' | 'CHANGES_BY' | 'CROSSES'
```

**How an agent uses the discoveries**:
1. **Direct reflex synthesis**: A temporal rule with consistency > 0.6 and ≥ 5 occurrences is a strong candidate for automation. The agent formulates the pattern as a reflex trigger → action sequence.
2. **Consistency assessment**: If the consistency is low (e.g., 0.4), the response is not predictable enough for automation. The agent flags this as "requires human judgment."
3. **Exception handling**: Temporal mining identifies contexts where the response deviated from the typical pattern. The agent includes these as conditional guards in the synthesized reflex.

### 2.5 Bayesian Reward Inference — "What Does the Pilot Actually Value?"

**What it discovers**: A scalar reward function R(t) = w · features(t) that explains observed pilot behavior. Six features are computed: speed_comfort, heading_accuracy, fuel_efficiency, smoothness, safety_margin, wind_compensation. The weights are inferred via Maximum A Posteriori (MAP) estimation with Beta-distributed priors.

**Agent interpretation**: Reward inference tells the agent: "This pilot's behavior is best explained by prioritizing safety_margin (w=0.35) above all else, followed by fuel_efficiency (w=0.22) and heading_accuracy (w=0.20). Speed_comfort (w=0.08) and smoothness (w=0.10) are secondary considerations." This is a "preference fingerprint" that the agent uses to tune synthesized reflexes.

**How an agent uses the discoveries**:
1. **Reflex tuning**: When synthesizing a heading-hold reflex, the agent sets PID gains that prioritize heading_accuracy and safety_margin over speed_comfort, matching the pilot's preference profile.
2. **Conflict resolution**: When two reflexes have conflicting objectives (e.g., one optimizes fuel efficiency, another optimizes speed), the agent resolves the conflict using the reward weights as a priority ordering.
3. **Narration seeding**: The agent can incorporate reward weights as "narration_seeds" in the reflex synthesis prompt, biasing the LLM toward generating reflexes that align with the pilot's values.

### 2.6 How Agent-Discovered Patterns Become Bytecode

The complete transformation chain from pattern discovery to bytecode:

```
Cross-correlation → CorrelationRecord (A leads B, r=0.72, lag=3.2s)
                         │
                         ▼
Temporal Mining → TemporalRule (event: "wind_speed_m_s > 12", 
                                response: throttle -20%, rudder -12°,
                                consistency: 0.85, occurrences: 23)
                         │
                         ▼
Agent Synthesize → Reflex JSON
  {
    "trigger": {"conditions": [{"sensor": "wind_speed_m_s", 
                                "operator": ">", "value": 12.0}]},
    "action_sequence": [
      {"actuator": "throttle_pct", "command": {"type": "relative", 
       "value": -20.0, "unit": "pct"}, "delay_ms": 0},
      {"actuator": "rudder_angle_deg", "command": {"type": "relative", 
       "value": -12.0, "unit": "deg"}, "delay_ms": 500}
    ],
    "safety_constraints": [
      {"sensor": "lidar_obstacle_dist_m", "operator": "<", 
       "value": 5.0, "on_violation": "abort"}
    ]
  }
                         │
                         ▼
Agent Validate → Passes Tiers 1-4
                         │
                         ▼
Agent A/B Test → Treatment wins (heading accuracy -15%, p=0.003)
                         │
                         ▼
Compile to Bytecode → ESP32 VM instructions
```

---

## 3. Reflex Synthesis — Agent as Compiler

### 3.1 How an Agent Generates Reflex Bytecode from Discovered Patterns

The reflex synthesis process is a 4-step pipeline that transforms pattern discovery outputs into validated reflex JSON:

**Step 1: Pattern Selection**: The learning agent ranks discovered patterns by actionability score:

```python
actionability = (correlation_strength × temporal_consistency × occurrence_count × 
                 reward_alignment × (1 - ambiguity_score))
```

Patterns with actionability > 0.5 are candidates for synthesis. The agent selects the top-N candidates (default: 3 per session).

**Step 2: Context Assembly**: The agent assembles the synthesis context:
- Discovered pattern (correlation, temporal rule, or change point)
- Current sensor snapshot (all 72 UnifiedObservation fields)
- Reward weights (6-dimensional preference profile)
- Active reflex registry (to avoid conflicts)
- Vessel configuration (max speed, length, type)
- Current autonomy level (determines safety constraint strictness)

**Step 3: LLM Invocation**: The agent formulates the system prompt (see §3.2) and invokes the on-device LLM. Expected latency: 3-8 seconds on Jetson Orin NX with Q4_K_M quantization. If on-device generation fails, the agent retries once on-device, then falls back to cloud LLM (expected latency: 5-15 seconds).

**Step 4: Post-Processing**: The agent validates the LLM output:
- JSON parsing (reject if malformed)
- Schema compliance (all required fields present)
- Safety constraint presence (≥ 1 required, ≥ 3 for L3+)
- Value range compliance (actuator commands within physical limits)
- Deduplication check (no duplicate reflex_id with existing registry)

### 3.2 System Prompt Structure for Optimal Reflex Generation

The system prompt is structured in 5 sections:

```
SECTION 1: ROLE DEFINITION
  "You are the NEXUS Reflex Synthesis Engine. Convert structured pattern 
   data into safe, executable JSON reflex policies."

SECTION 2: CRITICAL SAFETY RULES (8 rules, always included)
  1. Every reflex MUST include a hard safety constraint
  2. Obstacle proximity guard required (< 5m abort)
  3. Actuator limits: rudder [-45,+45], throttle [0,100]
  4. Minimum cooldown: 3 seconds
  5. Speed clamping to vessel_max_speed
  6. Termination condition required
  7. Navigation reflexes: max duration 300s
  8. Never disable safety systems

SECTION 3: INPUT SCHEMA
  {intent, entities, context, reward_weights, ambiguity_score}

SECTION 4: OUTPUT SCHEMA (strict JSON)
  {reflex_id, name, description, source, trigger, action_sequence,
   termination, safety_constraints, priority, autonomy_level_required,
   evaluation_metrics, tags}

SECTION 5: QUALITY REQUIREMENTS
  - Trigger specificity (avoid false positives but fire when intended)
  - Physical realism (action sequence must be feasible)
  - Safety coverage (specific action + general hazards)
  - Self-containment (no dependency on other reflexes)
  - Ambiguity handling (set needs_clarification if ambiguity >= 0.5)
```

### 3.3 GBNF Grammar Constraints for Safe Reflex JSON

The LLM output is constrained by a GBNF (Grammar-Based Neural Format) grammar that enforces structural correctness:

```gbnf
reflex ::= "{"
  " \"reflex_id\": \"" reflex_id "\","
  " \"name\": \"" string_100 "\","
  " \"trigger\": {" trigger_body "},"
  " \"action_sequence\": [" action_list "],"
  " \"safety_constraints\": [" safety_list "],"
  " \"priority\": " int_0_100 ","
  " \"autonomy_level_required\": " int_0_5
"}"

trigger_body ::= 
  " \"conditions\": [" condition_list "],"
  " \"logic\": \"AND\","
  " \"cooldown_seconds\": " int_min_3

condition_list ::= condition ("," condition)*
condition ::= 
  " {\"sensor\": \"" sensor_name "\","
  " \"operator\": \"" operator "\","
  " \"value\": " float "}"

safety_constraint ::= 
  " {\"sensor\": \"" sensor_name "\","
  " \"operator\": \"" comparison_op "\","
  " \"value\": " float ","
  " \"on_violation\": \"" violation_action "\"}"
```

This grammar prevents the LLM from generating structurally invalid JSON, missing required fields, or using undefined sensor/actuator names. The grammar is loaded at LLM initialization time and applied during generation.

### 3.4 Quality Metrics for Agent-Generated Reflexes

Each synthesized reflex is scored on 4 quality dimensions:

| Dimension | Metric | Target | Weight |
|-----------|--------|--------|--------|
| Schema compliance | % of required fields present | 100% | 0.30 |
| Semantic correctness | Logical consistency of trigger→action | Pass/Fail | 0.30 |
| Safety adherence | Number of safety constraints, obstacle guard present | ≥ 3 for L3+ | 0.25 |
| Actionability score | Pattern strength × consistency × reward alignment | > 0.5 | 0.15 |

A reflex must score ≥ 0.7 overall to proceed to validation. Reflexes scoring 0.5-0.7 are flagged for human review at L0-L3 or automatically rejected at L4-L5. Reflexes scoring < 0.5 are always rejected.

---

## 4. A/B Testing — Agent-Managed

### 4.1 How Agents Design A/B Tests

The A/B testing agent designs tests based on the following protocol:

**Test configuration generation**:
1. **Control reflex**: The current production reflex (identified by reflex_id).
2. **Treatment reflex**: The newly synthesized reflex (proposed by the learning agent).
3. **Randomization method**: Default is "alternating" (ABABAB...), which provides deterministic, easily interpretable results. For complex scenarios, "stratified" randomization balances context variables (weather, traffic density).
4. **Stopping criteria**: Minimum 4 hours duration AND minimum 30 triggers per condition. Maximum 48 hours.
5. **Safety limits**: Override rate > 5% → immediate rollback. Any zero-tolerance event (safety_rule_violation, sensor_failure, heartbeat_timeout) → immediate rollback.

**Baseline computation**: Baseline metrics are computed from the last 24 hours of control-only operation. The 7 standard metrics are: fuel_efficiency, speed_consistency, heading_accuracy, ride_comfort, override_frequency, response_latency_ms, actuator_wear.

### 4.2 Statistical Power Analysis for Agent-Designed Tests

The agent performs power analysis to determine if the test can detect a meaningful effect:

```python
def compute_power(n_per_condition, effect_size_cohen_d, alpha=0.05):
    """
    Compute statistical power for paired t-test.
    
    For n=30 per condition, alpha=0.05, Cohen's d=0.5 (medium effect):
    Power ≈ 0.47 (47% chance of detecting the effect)
    
    For n=30, alpha=0.05, Cohen's d=0.8 (large effect):
    Power ≈ 0.86 (86% chance of detecting the effect)
    
    Minimum n for 80% power at d=0.5, alpha=0.05:
    n ≈ 64 per condition
    """
    from scipy.stats import nct, t
    nc = effect_size_cohen_d * sqrt(n_per_condition)
    t_crit = t.ppf(1 - alpha/2, df=n_per_condition - 1)
    power = 1 - nct.cdf(t_crit, df=n_per_condition-1, nc=nc)
    return power
```

**Agent decision rule**: If power < 0.80 for the expected effect size, the agent extends the test duration or requests more trigger events before evaluating.

### 4.3 Decision Rules: When to Promote, Revert, or Extend

After the stopping criteria are met, the agent evaluates the test results:

```
IF any zero-tolerance event occurred during treatment:
    REVERT → log reason, generate incident report

ELSE IF override_rate > 5% during treatment:
    REVERT → log reason (pilot rejection)

ELSE IF primary metric shows significant improvement (p < 0.05, Cohen's d ≥ 0.2):
    AND no other metric shows significant regression:
    PROMOTE → deploy treatment as new default, update trust agent

ELSE IF primary metric shows significant regression:
    REVERT → log reason, analyze what went wrong

ELSE IF results are inconclusive (p ≥ 0.05 OR |Cohen's d| < 0.2):
    IF test_duration < max_duration_hours:
        EXTEND → continue test for up to max_duration_hours
    ELSE:
        REVERT → log "inconclusive", retain control, archive for future analysis
```

### 4.4 Fleet-Wide A/B Testing

In a fleet of N vessels, the agent can design fleet-wide A/B tests:

**Design**: Vessels are randomly assigned to control or treatment groups using stratified randomization (balanced by vessel type, operating environment, and traffic density). Each vessel runs the test independently.

**Aggregation**: Fleet-level results are computed by meta-analyzing individual vessel results:

```python
def fleet_meta_analysis(vessel_results: list[dict]) -> dict:
    """
    Combine p-values across vessels using Fisher's method.
    Combine effect sizes using inverse-variance weighting.
    """
    from scipy.stats import combine_pvalues
    
    p_values = [v['p_value'] for v in vessel_results]
    effect_sizes = [v['cohens_d'] for v in vessel_results]
    weights = [1.0 / (v['ci_width'] ** 2) for v in vessel_results]
    
    fleet_p = combine_pvalues(p_values, method='fisher')[1]
    fleet_d = sum(w * d for w, d in zip(weights, effect_sizes)) / sum(weights)
    
    return {
        'fleet_p_value': fleet_p,
        'fleet_effect_size': fleet_d,
        'n_vessels': len(vessel_results),
        'vessel_agreement': sum(1 for v in vessel_results if v['significant']) / len(vessel_results)
    }
```

**Rollback policy**: If 3+ vessels in the treatment group trigger rollback conditions, the fleet agent issues a fleet-wide rollback, reverting all treatment vessels to control.

---

## 5. Fleet Learning — Cross-Vessel Knowledge Transfer

### 5.1 How Agents Share Learned Reflexes Across the Fleet

The fleet learning protocol enables vessels to share validated reflex bytecodes:

**Step 1: Reflex Export**: After a vessel's reflex passes all validation tiers and A/B testing on the originating vessel, the learning agent packages it for fleet distribution:

```json
{
  "reflex_id": "R-wind-compensation-a3f2b1c1",
  "origin_vessel": "VESSEL-001",
  "origin_timestamp": "2025-07-12T14:30:00Z",
  "bytecode_hash": "sha256:abc123...",
  "validation_results": {
    "tier1": {"passed": true, "score": 1.0},
    "tier2": {"passed": true, "score": 0.95},
    "tier3": {"passed": true, "score": 0.92},
    "tier4": {"passed": true, "score": 0.88, "scenarios": "97/100"}
  },
  "ab_test_results": {
    "primary_metric": "heading_accuracy",
    "relative_improvement_pct": -15.0,
    "p_value": 0.003,
    "cohens_d": 0.65,
    "conclusion": "treatment_wins"
  },
  "trust_context": {
    "subsystem": "autopilot",
    "trust_at_deploy": 0.72,
    "hours_since_deploy": 48,
    "bad_events": 0
  },
  "hardware_requirements": {
    "sensors": ["wind_speed_m_s", "wind_direction_deg", "rudder_angle_deg"],
    "actuators": ["rudder_angle_deg"],
    "min_sample_rates": {"wind_speed_m_s": 5.0}
  }
}
```

**Step 2: Fleet Distribution**: The reflex package is uploaded to the fleet bytecode repository (a versioned store accessible by all vessels). The fleet learning agent on each vessel queries the repository periodically (default: every 6 hours) for new reflexes compatible with its hardware configuration.

**Step 3: Local Adaptation**: When a vessel receives a fleet reflex, the local learning agent performs hardware compatibility checks:
- Does this vessel have all required sensors? (sensor registration check)
- Are sample rates sufficient? (compare required vs actual)
- Is the actuator mapping compatible? (ROLE_ASSIGN configuration)

If compatible, the vessel deploys the reflex at **L2 (Supervised)** regardless of the origin vessel's autonomy level. The receiving vessel must earn its own trust for the reflex — fleet evidence provides only a 10% bonus (see §4.1 of the Trust System A2A-Native spec).

### 5.2 Trust Transfer: How Fleet-Validated Bytecode Gets Accelerated Trust

When vessel B deploys a fleet-validated reflex (originally validated on vessel A), vessel B's trust agent applies a fleet evidence bonus:

```python
# Vessel A's fleet evidence
fleet_hours = vessel_a.trust_context.hours_since_deploy  # e.g., 200 hours
fleet_bad_events = vessel_a.trust_context.bad_events     # e.g., 0
required_hours = 100  # minimum for fleet evidence bonus

if fleet_hours >= required_hours and fleet_bad_events == 0:
    fleet_bonus = 0.1 * min(fleet_hours / required_hours, 2.0) * alpha_gain
    # Capped at 20% bonus (2.0 × 0.1 = 0.2)
    effective_alpha_gain = alpha_gain + fleet_bonus
    # Plus the 0.5× rule for agent code still applies
    effective_alpha_gain *= 0.5
```

**Result**: Fleet-validated reflexes earn trust at α_gain × 0.5 × 1.1 = α_gain × 0.55 (vs α_gain × 0.5 for non-fleet-validated reflexes). This is a modest 10% acceleration — sufficient to provide a head-start but not enough to bypass local evidence requirements.

### 5.3 Domain Transfer: Marine Reflex Adapted for Agriculture

The fleet learning protocol supports cross-domain adaptation. A reflex discovered for marine vessels can be adapted for agricultural robotics:

**Example**: A marine wind-compensation reflex (adjusting rudder based on wind speed) can be adapted to an agricultural spray-drift reflex (adjusting spray nozzle angle based on wind speed):

```
Original (Marine):
  trigger: wind_speed_m_s > 12
  action: rudder_angle_deg += wind_delta × 0.8
  
Adapted (Agriculture):
  trigger: wind_speed_m_s > 8
  action: spray_nozzle_angle_deg += wind_delta × 0.5
  safety_constraint: wind_speed_m_s > 20 → abort (stop spraying)
```

**Adaptation process**:
1. The learning agent identifies structural similarity between domains (both have wind_speed as input, both have an angular actuator as output).
2. The agent maps domain-specific parameters (thresholds, gains, safety limits) using the target domain's trust calibration and safety policy.
3. The adapted reflex is treated as a **new** reflex — it must pass all validation tiers and A/B testing on the target vessel. Fleet evidence from the source domain does not transfer.
4. The adapted reflex starts at trust T=0.0 in the target subsystem, with no fleet bonus (cross-domain transfer provides no trust acceleration).

### 5.4 The Fleet Bytecode Repository Concept

The fleet bytecode repository is a versioned, signed store of validated reflex bytecodes:

```
/fleet/bytecode_repo/
├── index.json                    # Registry of all fleet bytecodes
├── marine/
│   ├── wind_compensation/
│   │   ├── v1.0.0/
│   │   │   ├── reflex.json       # Reflex definition
│   │   │   ├── bytecode.bin      # Compiled VM instructions
│   │   │   ├── validation.json   # 4-tier validation results
│   │   │   ├── ab_test.json      # A/B test results
│   │   │   ├── fleet_results.json# Meta-analysis across vessels
│   │   │   └── signature.sig     # RSA-3072 signature from generating agent
│   │   └── v1.1.0/               # Updated version
│   └── collision_avoidance/
│       └── ...
├── agriculture/
│   ├── spray_drift_compensation/
│   └── irrigation_optimization/
├── factory/
│   └── ...
└── metadata/
    ├── compatibility_matrix.json # Which reflexes work on which hardware
    └── trust_scores.json         # Fleet-wide trust consensus per reflex
```

**Integrity guarantees**:
- Every bytecode is RSA-3072 signed by the generating agent.
- The fleet trust agent verifies signatures before allowing any vessel to load the bytecode.
- The repository is append-only — reflexes can be superseded by new versions but never modified or deleted.
- A fleet-wide rollback mechanism allows the fleet trust agent to revoke any reflex across all vessels.

---

## 6. The Seasonal Evolution Cycle — Agent-Native

### 6.1 The Four Seasons

The NEXUS learning pipeline operates on a seasonal cycle that governs when reflexes are discovered, tested, deployed, and integrated:

| Season | Duration | Focus | Agent Activity Level |
|--------|----------|-------|---------------------|
| **Spring** (Production) | 3 months | Deploy validated reflexes, monitor performance | Low — observation and monitoring |
| **Summer** (Evolution) | 3 months | Discover new patterns, synthesize new reflexes | High — active learning and synthesis |
| **Autumn** (Evaluation) | 1 month | A/B test new reflexes, evaluate performance | Medium — testing and evaluation |
| **Winter** (Integration) | 2 months | Promote winning reflexes, retire losers, update fleet repo | Medium — deployment and cleanup |

### 6.2 How Agents Manage Each Phase

**Spring (Production)**: The deployment agent manages the production fleet. It monitors 7 standard metrics per reflex, watches for trust decay, and manages rollback if performance degrades. The observation agent records high-quality operational data that will fuel the Summer discovery phase. Key agent activities:
- Continuous metric monitoring (every 5 minutes at L4, every 30 minutes at L5)
- Post-deployment trust tracking (T(t) per subsystem per reflex)
- Anomaly detection (metric deviation > 3σ from baseline)
- Automated rollback if override rate > 5% or any safety event

**Summer (Evolution)**: The learning agent enters its most active phase. It runs all 5 pattern discovery algorithms on the Spring observation data, synthesizes candidate reflexes, and queues them for Autumn testing. Key agent activities:
- Pattern discovery on 3 months of accumulated data
- Cross-correlation scan across all 2,556 variable pairs
- BOCPD change point detection on all continuous sensors
- HDBSCAN behavioral clustering for context-aware reflex scoping
- Temporal pattern mining for event-response automation
- Bayesian reward inference for preference-aligned synthesis
- LLM invocation for reflex JSON generation (expected: 10-50 candidates per season)

**Autumn (Evaluation)**: The A/B testing agent evaluates Summer's candidates. Each candidate is tested for 4-48 hours with statistical rigor. Key agent activities:
- Test configuration design (randomization, stopping criteria, safety limits)
- Parallel test execution (up to 3 concurrent A/B tests)
- Statistical evaluation (paired t-test, Cohen's d, 95% CI)
- Fleet-wide meta-analysis for fleet-validated reflexes
- Promotion/revert/extend decisions
- Fleet-wide rollback if needed

**Winter (Integration)**: The deployment agent and fleet agent work together to update the fleet bytecode repository. Key agent activities:
- Promote A/B test winners to production
- Retire losing reflexes (archive with results)
- Update fleet bytecode repository with new versions
- Generate cross-domain adaptations for applicable reflexes
- Compute trust calibration updates for the next Spring
- Produce seasonal report (metrics, trust trajectories, reflex churn rate)

### 6.3 Automated Seasonal Transitions

Seasonal transitions are triggered by fleet performance metrics:

```
Spring → Summer trigger:
  - All production reflexes have T(t) ≥ their deployment level threshold
  - No active A/B tests remaining
  - Minimum 60 days since last Summer (prevents premature transitions)

Summer → Autumn trigger:
  - Pattern discovery complete (all sessions processed)
  - Reflex candidate queue non-empty OR 60 days elapsed
  - All Summer-generated candidates have passed Tier 1-3 validation

Autumn → Winter trigger:
  - All A/B tests complete (promoted, reverted, or inconclusive)
  - No outstanding rollback conditions
  - Minimum 14 days since last Summer candidate was generated

Winter → Spring trigger:
  - Fleet bytecode repository updated with all promoted reflexes
  - All vessels have received and deployed the latest fleet bytecodes
  - Trust scores have stabilized (no > 0.05 changes in last 7 days)
```

Human override: At any time, the operator can manually trigger a seasonal transition or pause the cycle. During L0-L3 operation, seasonal transitions require operator confirmation. At L4-L5, transitions are automatic with asynchronous notification.

---

## 7. Example: Complete Learning Loop

### 7.1 Scenario: Wind Compensation Reflex Discovery and Deployment

**Context**: Vessel NEXUS-007 has been operating for 3 months (Spring season) with a basic heading-hold reflex. The learning agent has accumulated 2,160 hours of observation data. It is now Summer.

**Step 1: Observation (Ongoing, Spring)**

The observation agent has been recording UnifiedObservation records at 100 Hz. During a particularly windy week (wind_speed_m_s averaging 10-15 m/s), the pilot made frequent manual rudder corrections. The observation agent tags these sessions: `weather=gusty, traffic=light, pilot_active=true`.

**Step 2: Pattern Discovery (Summer, Day 1-3)**

The learning agent triggers pattern discovery on the accumulated data:

*Cross-correlation scan* (8 seconds on Jetson):
```
CorrelationRecord:
  variable_a: "wind_speed_m_s"
  variable_b: "rudder_angle_deg"
  lag_s: 3.2
  correlation: 0.72
  p_value: 0.001 (Bonferroni-corrected)
  effect_direction: "A_leads_B"
```
Interpretation: Wind speed changes lead rudder adjustments by ~3 seconds.

*Temporal pattern mining* (45 seconds on Jetson):
```
TemporalRule:
  event_definition: "wind_speed_m_s CHANGES_BY 3.0"
  typical_response: [
    {"actuator": "throttle_pct", "delta": -15.0, "delay_s": 0.5},
    {"actuator": "rudder_angle_deg", "delta": -10.0, "delay_s": 1.2}
  ]
  consistency: 0.82
  exceptions: ["low_speed_manoeuvring"]
  sample_count: 34
  avg_response_latency_s: 1.1
```
Interpretation: When wind gusts > 3 m/s, the pilot typically reduces throttle by 15% and applies -10° rudder within 1.1 seconds. This pattern occurs 34 times with 82% consistency.

*Bayesian reward inference* (3 seconds on Jetson):
```
RewardWeights:
  w_safety_margin: 0.35 (high priority)
  w_fuel_efficiency: 0.22 (high priority)
  w_heading_accuracy: 0.20 (high priority)
  w_smoothness: 0.10 (low priority)
  w_speed_comfort: 0.08 (minimal consideration)
  w_wind_compensation: 0.05 (minimal)
```
Interpretation: This pilot prioritizes safety and fuel efficiency. The reflex should conserve fuel while maintaining safe distances.

**Step 3: Reflex Synthesis (Summer, Day 4)**

The learning agent formulates the synthesis prompt and invokes the on-device LLM (Qwen2.5-Coder-7B):

```json
{
  "reflex_id": "R-navigational_command-windgust-a3f2b1c1",
  "name": "Wind Gust Compensation",
  "description": "Automatically reduce throttle and adjust rudder when wind gusts exceed 3 m/s change, compensating for crosswind drift",
  "source": {
    "narration": "auto-discovered: temporal pattern #3",
    "intent": "navigational_command",
    "confidence": 0.82,
    "created_at": "2025-07-15T10:30:00Z"
  },
  "trigger": {
    "conditions": [
      {"sensor": "wind_speed_m_s", "operator": "changes_by", "value": 3.0}
    ],
    "logic": "AND",
    "cooldown_seconds": 5,
    "max_activations_per_hour": 60
  },
  "action_sequence": [
    {
      "step": 0,
      "actuator": "throttle_pct",
      "command": {"type": "relative", "value": -15.0, "unit": "pct"},
      "delay_ms": 500,
      "duration_ms": 3000,
      "condition": "gps_speed_m_s > 2.0"
    },
    {
      "step": 1,
      "actuator": "rudder_angle_deg",
      "command": {"type": "relative", "value": -10.0, "unit": "deg"},
      "delay_ms": 1200,
      "duration_ms": 5000,
      "condition": "lidar_obstacle_dist_m > 10.0"
    }
  ],
  "termination": {
    "type": "timeout",
    "timeout_ms": 8000
  },
  "safety_constraints": [
    {
      "id": "sc_obstacle_guard",
      "description": "Abort if obstacle within 5m",
      "sensor": "lidar_obstacle_dist_m",
      "operator": "<",
      "value": 5.0,
      "on_violation": "abort"
    },
    {
      "id": "sc_speed_floor",
      "description": "Don't reduce throttle below idle",
      "sensor": "throttle_pct",
      "operator": "<",
      "value": 10.0,
      "on_violation": "clamp_to_range"
    },
    {
      "id": "sc_rudder_limit",
      "description": "Clamp rudder to physical range",
      "sensor": "rudder_angle_deg",
      "operator": "!=",
      "value": "clamped",
      "on_violation": "clamp_to_range"
    }
  ],
  "priority": 45,
  "autonomy_level_required": 3,
  "evaluation_metrics": [
    {"name": "heading_accuracy", "expected_direction": "lower_is_better",
     "expected_magnitude": "-15%"},
    {"name": "fuel_efficiency", "expected_direction": "higher_is_better",
     "expected_magnitude": "+5%"}
  ],
  "tags": ["synthesized", "navigational_command", "wind_compensation"]
}
```

**Step 4: Validation (Summer, Day 4 — 6 seconds)**

Tier 1 (Syntax): PASS — 100ms. All required fields present. Sensor/actuator names valid. Cooldown 5s ≥ 3s minimum.

Tier 2 (Semantic): PASS — 300ms. Actions in correct dependency order (throttle before rudder). Termination reachable within 8s. No circular references.

Tier 3 (Safety): PASS — 700ms. Obstacle guard present (< 5m). Actuator limits clamped. Duration < 300s. 3 safety constraints for L3 requirement met. Priority 45 < 90 (reserved for critical).

Tier 4 (Simulation): PASS — 45 seconds. 97/100 scenarios passed. 3 failures were edge cases where wind gusts coincided with obstacle proximity — already handled by safety constraint.

**Step 5: A/B Testing (Autumn, Day 1-2)**

The A/B testing agent configures the test:

```python
ABTestConfig(
    test_id="ab-windgust-001",
    name="Wind Gust Compensation vs Manual",
    description="Test auto-discovered wind gust reflex against pilot manual response",
    reflex_id_control="R-existing-heading-hold",
    reflex_id_treatment="R-navigational_command-windgust-a3f2b1c1",
    trigger_condition="wind_speed_m_s CHANGES_BY 3.0",
    randomization_method="alternating",
    min_duration_hours=8.0,
    min_triggers_per_condition=20,
    max_duration_hours=24.0,
    alpha=0.05,
    max_override_rate=0.05
)
```

Results after 18 hours (42 trigger events per condition):

```
heading_accuracy:
  control_mean: 4.2 degrees
  treatment_mean: 3.5 degrees
  absolute_change: -0.7 degrees (-16.7%)
  p_value: 0.008
  cohens_d: 0.42 (small-to-medium)
  significant: YES

fuel_efficiency:
  control_mean: 3.2 km/L
  treatment_mean: 3.4 km/L
  absolute_change: +0.2 km/L (+6.3%)
  p_value: 0.021
  cohens_d: 0.35 (small)
  significant: YES

override_frequency:
  control: 2.1/hour
  treatment: 0.8/hour
  (No override rate trigger — well below 5%)

Zero-tolerance events: NONE
```

**Decision**: PROMOTE. Both primary metrics show significant improvement with no safety regression.

**Step 6: Deployment (Winter, Day 1)**

The deployment agent pushes the bytecode to the ESP32:

Wire protocol sequence:
```
1. ROLE_ASSIGN reflex_id="R-navigational_command-windgust-a3f2b1c1"
2. LOAD_PROGRAM bytecode=<compiled VM instructions>
3. TRUST_REQUIRE subsystem="autopilot" level=3
```

Compiled bytecode (VM instructions):
```
; Wind Gust Compensation Reflex
; Trigger: wind_speed_m_s changes by 3.0+ within 5 seconds

00  LOAD_VAR   wind_speed_m_s        ; Read current wind speed
01  LOAD_VAR   _wind_prev             ; Read previous wind speed
02  SUB_F                           ; Compute delta
03  ABS_F                           ; Absolute value
04  LOAD_CONST  3.0                  ; Threshold
05  COMPARE_LT                       ; delta < 3.0?
06  BRANCH_IF_TRUE  end              ; If not gust, skip
07  STORE_VAR  _wind_prev wind_speed_m_s  ; Update previous
08  LOAD_VAR   gps_speed_m_s         ; Guard: speed > 2.0?
09  LOAD_CONST  2.0
10  COMPARE_LT
11  BRANCH_IF_FALSE skip_throttle
12  LOAD_VAR   throttle_pct          ; Reduce throttle by 15%
13  LOAD_CONST  15.0
14  SUB_F
15  CLAMP_F    10.0 100.0            ; Clamp to [10, 100]
16  STORE_ACTUATOR throttle_pct
17  WAIT_MS    700                   ; 700ms delay
18  LABEL      skip_throttle
19  LOAD_VAR   lidar_obstacle_dist_m  ; Safety: obstacle > 10m?
20  LOAD_CONST  10.0
21  COMPARE_LT
22  BRANCH_IF_FALSE skip_rudder
23  LOAD_VAR   rudder_angle_deg      ; Adjust rudder by -10°
24  LOAD_CONST  10.0
25  SUB_F
26  CLAMP_F    -45.0 45.0           ; Clamp to [-45, +45]
27  STORE_ACTUATOR rudder_angle_deg
28  LABEL      skip_rudder
29  WAIT_MS    8000                  ; 8s total duration
30  LABEL      end
31  HALT
```

**Post-deployment monitoring** (first 72 hours):

```
Hour 1-6:  T(autopilot) = 0.62 → 0.64 → 0.65 → 0.65 → 0.66 → 0.67
            Trust increasing. No bad events. heading_accuracy improving.

Hour 12:   T(autopilot) = 0.71. 6 consecutive clean windows.
            heading_accuracy: 3.3° (treatment better than A/B test average)

Hour 24:   T(autopilot) = 0.74. First streak_bonus applied.
            fuel_efficiency: 3.5 km/L (confirming A/B test results)

Hour 48:   T(autopilot) = 0.78. Agent proposes fleet distribution.
            48 hours clean operation. Zero bad events.

Hour 72:   T(autopilot) = 0.80. L4 threshold reached.
            Observation timer: 168h accumulated. Ready for promotion.
            Fleet trust agent approves fleet distribution with 10% bonus.
```

**Fleet distribution** (Winter, Day 3): The reflex is uploaded to the fleet bytecode repository with full provenance (discovery patterns, validation results, A/B test data, 72-hour deployment metrics). Vessels VESSEL-003 and VESSEL-012 download and deploy the reflex at L2 (Supervised). VESSEL-003 begins earning trust with the 0.5× agent rate + 10% fleet bonus = 0.55× effective rate. VESSEL-012's hardware lacks a wind direction sensor, so the reflex is marked incompatible and not deployed.

**End-to-end timeline**: 
- Discovery: 3 days (Summer)
- Synthesis + Validation: 1 day
- A/B Testing: 2 days (Autumn)
- Deployment monitoring: 3 days (Winter)
- Fleet distribution: 1 day
- **Total: 10 days from pattern discovery to fleet deployment**

---

## Cross-References

- **Source Specification**: [[learning_pipeline_spec.md]] (NEXUS-JETSON-LP-001)
- **Trust System A2A**: [[trust_system_a2a_native.md]] (trust score, 0.5× rule, fleet evidence)
- **Cross-Domain Applicability**: [[cross_domain_a2a_applicability.md]] (domain trust calibration, agent ecology)
- **Safety System**: [[safety_system_spec.md]] (four-tier safety, validation requirements)
- **Reflex Bytecode VM**: [[reflex_bytecode_vm_spec.md]] (VM instruction set, CLAMP_F, STORE_ACTUATOR)
- **Wire Protocol**: [[wire_protocol_spec.md]] (ROLE_ASSIGN, LOAD_PROGRAM, FLEET_TRUST messages)
- **AI Model Analysis**: [[ai_model_analysis.md]] (Qwen2.5-Coder-7B, quantization, latency)

---

*End of Learning Pipeline A2A-Native Specification*
