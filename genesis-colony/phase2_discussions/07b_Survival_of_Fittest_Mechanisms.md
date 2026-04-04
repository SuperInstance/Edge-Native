# Survival of the Fittest: Selection Mechanisms in the NEXUS Colony

## Phase 2 Discussion 07b — The Evolutionary Engine

**Document ID:** NEXUS-GENESIS-P2-007b
**Agent:** Agent-2D (Safety-Critical Systems Engineer & Evolutionary Computation Specialist)
**Phase:** 2 — Mechanism Specification
**Status:** Technical Specification — Ready for Review
**Date:** 2026-03-30

---

## Epigraph

> *"The tree which does not bear fruit is not useless. It was the one that survived the blight that killed all the fruit-bearing trees, and its genes are the reason this forest exists."*
> — After Zhuangzi, "The Useless Tree"

---

## Preamble

This document defines the precise mechanisms by which bytecode variants in the NEXUS colony compete, succeed, fail, and are retired. Survival of the fittest is the colony's core evolutionary driver, but "fittest" is not synonymous with "best performer." Fitness in the NEXUS colony is a multi-dimensional, temporally stratified, colony-aware quantity that encodes safety as a non-negotiable prerequisite, long-term adaptability as a necessity, and short-term performance as merely one component. This specification draws on the Colony Thesis's fitness function, the Stress Test's safety-as-multiplier mandate, and the phase-level evolutionary cycle.

---

## I. Fitness Function Design

The master fitness function governs all selection decisions:

```
colony_fitness(v) = α·F_immediate(v) + β·F_heritability(v) + γ·F_adaptability(v) + δ·F_reversible(v) - ε·Debt(v)
```

With the critical safety gate:

```
if safety_regression(v, baseline) > threshold:
    colony_fitness(v) = 0   # Zero regardless of all other components
```

This safety multiplier (drawn from the Stress Test's requirement that "fitness function must encode safety as MULTIPLIER") means no variant can buy performance by eroding safety margins. A single safety regression — an obstacle avoidance margin shrunk below threshold, an actuator rate limit exceeded in any observed condition, a Lyapunov certificate that fails to verify — renders the entire fitness score zero. The variant does not compete; it is rejected before the arena.

### 1.1 F_immediate: Task Performance

F_immediate measures how well the variant performs its designated task right now. It is a weighted composite of domain-specific metrics:

**For safety-critical subsystems** (autopilot, engine safety, bilge management):
- **Accuracy:** Error magnitude vs. target setpoint, measured as RMSE over a rolling 24-hour window. Weight: 0.4
- **Latency:** Time between stimulus detection and actuator response, measured as p99 response time. Weight: 0.3
- **Efficiency:** Resource consumption per unit of task completion (fuel flow per nautical mile for autopilot, pump cycling frequency for bilge). Weight: 0.2
- **Comfort:** Variance in acceleration/jerk for human-occupied vessels, measured as integral of squared jerk over time. Weight: 0.1

**For non-critical subsystems** (greenhouse climate, lighting, dashboard display):
- Accuracy: 0.5, Efficiency: 0.3, Latency: 0.1, Comfort: 0.1

The weights are not static — they shift based on the current season and environmental conditions. During Autumn consolidation, accuracy weight increases by 20% relative to efficiency. During Spring exploration, efficiency weight decreases to favor novel approaches that may initially be wasteful.

**Measurement:** All F_immediate metrics are captured through continuous A/B testing. The incumbent variant and the challenger run in separate VM instances on the same node, with the safety supervisor using the incumbent's output unless the challenger's is within the statistical confidence envelope. Telemetry is captured at 10Hz, aggregated into 1-minute bins, and analyzed using the formula from the Stress Test:

```
required_N = (Z_alpha + Z_beta)^2 * sigma^2 / delta^2
```

For a 5% improvement detection at 95% confidence (Z_alpha=1.96, Z_beta=0.84, sigma estimated from rolling 7-day variance), a variant must accumulate a minimum of 200 data points per condition category before its F_immediate score is considered stable.

### 1.2 F_heritability: Innovation Reuse Potential

F_heritability measures how transferable a variant's innovation is to other nodes, vessels, or domains. A variant that discovers a generalizable pattern (e.g., a new I2C timing calibration that works across all nodes with the same sensor family) is more valuable than a variant that only improves performance for one specific node's unique configuration.

**Measurement by three sub-metrics:**

1. **Cross-node adoption rate:** After a variant proves itself on its home node, it is offered to peer nodes running the same niche function. The fraction of peer nodes where the variant achieves ≥90% of its home-node fitness constitutes the adoption score. A variant adopted by 6 of 8 peers scores 0.75.

2. **Pattern generality score:** The Jetson's pattern analysis engine decomposes each variant into structural primitives (gain adjustments, threshold shifts, conditional restructurings, algorithmic substitutions). Each primitive is tagged with its applicable scope (sensor-family-specific, node-architecture-specific, vessel-condition-specific, universally applicable). The generality score is the fraction of primitives that are applicable to 3+ nodes.

3. **Compositional compatibility:** Can this variant's innovations be combined with innovations from other variants? The Jetson performs pairwise compatibility tests: if variant A's thermal compensation curve and variant B's flow-rate sensitivity curve can be combined without Lyapunov violation, both receive a compatibility bonus. Variants that create "incompatible" mutations (e.g., hardcoding node-specific constants that cannot be generalized) receive a penalty.

F_heritability is computed as: `0.4·adoption_rate + 0.3·generality + 0.3·compatibility`

### 1.3 F_adaptability: Novel Condition Performance

F_adaptability measures how well a variant handles conditions it was not specifically optimized for. This is the most expensive metric to compute, because it requires testing against rare or synthetic conditions.

**Measurement:** The colony maintains a library of 50+ stress test scenarios spanning the expected operational envelope and beyond: extreme temperatures, sensor failure modes, unusual sea states, power fluctuations, communication dropout, high-latency conditions. Each variant is subjected to a subset of these scenarios during the competition arena phase (see Section II).

The adaptability score is the performance variance across conditions, inverted:

```
F_adaptability = 1 / (1 + CV(performance across conditions))
```

where CV is the coefficient of variation (standard deviation / mean). A variant that maintains consistent 95% accuracy across all conditions scores near 1.0. A variant that achieves 99% accuracy in normal conditions but drops to 60% in rough-weather scenarios scores much lower — its high variance penalizes it.

**The stress test scenario library is itself evolving:** When a variant encounters a condition where it performs poorly *and that condition subsequently occurs in real operation*, that condition is added to the stress test library with higher priority. The colony learns what it doesn't know and actively tests against those gaps.

### 1.4 F_reversible: Safe Rollback Capability

F_reversible measures how safely and quickly a variant can be rolled back to its predecessor. This encodes the Colony Thesis's principle of "purposeful without being purpose-driven" — every evolutionary step must be reversible, because the colony may need to retreat from an adaptation that proves harmful in unanticipated ways.

**Measurement by three sub-metrics:**

1. **Lyapunov certificate presence:** Variants with verified Lyapunov certificates (Level 1-2 changes) score 1.0 on this sub-metric. Level 3 changes without Lyapunov certificates but with empirical stability evidence score 0.6. Level 3 changes without either score 0.0.

2. **Stateless design score:** Variants that can be cleanly unloaded from the VM without leaving persistent state (no modified NVS entries, no changed GPIO configurations, no altered peripheral register states beyond what the HAL reinitializes) score 1.0. Variants that modify NVS during operation score 0.5. Variants that change hardware configurations that persist across bytecode reload score 0.0.

3. **Deterministic rollback score:** Can the variant be rolled back in under 60 seconds (RS-422 transfer of an 8KB bytecode takes ~0.09 seconds plus flash write time)? Does the rollback require a node reboot? Can the previous variant resume exactly where it left off? Full-state rollback (resume without reboot) scores 1.0. Reboot-required rollback scores 0.5. Rollback requiring Jetson intervention scores 0.3.

F_reversible = `0.4·lyapunov + 0.3·stateless + 0.3·rollback_speed`

### 1.5 Debt: Future Optionality Consumed

Debt is the negative component of the fitness function — it penalizes variants that achieve short-term gains by consuming resources that future variants will need. The Generational Debt Ledger tracks five categories:

| Debt Category | Measurement Unit | Ceiling |
|---|---|---|
| Storage debt | Fraction of bytecode partition used | 0.85 |
| Memory debt | Peak SRAM/PSRAM utilization fraction | 0.75 |
| Dependency debt | Count of external dependencies introduced | 3 new per variant |
| Diversity debt | Active lineages reduced | Never below 5 |
| Complexity debt | Bytecode size relative to ancestor | 1.5x ancestor size |

A variant that pushes any single debt category above its ceiling is rejected regardless of its fitness score. A variant at 80% storage debt with 2.0x bytecode complexity receives `Debt = 0.80 + 0.30 = 1.10`, which with ε=0.5 subtracts 0.55 from colony_fitness. Debt creates evolutionary friction — it does not prevent deployment, but it makes the variant less attractive than a simpler alternative.

---

## II. The Competition Arena

### 2.1 Tournament Format

The colony uses a **hybrid league-and-knockout format** that balances thoroughness with resource constraints:

**Phase 1 — League Table (All variants compete):** Every active variant in a niche runs concurrently in time-shared rotation on the node. The VM scheduler allocates execution slots in round-robin fashion: incumbent gets 60% of execution time, each challenger gets `40% / N_challengers`. This ensures the incumbent's stability is never compromised while challengers get meaningful real-world exposure. Duration: one full day-night cycle (24 hours minimum).

**Phase 2 — Statistical Evaluation:** After league play, variants are ranked by their composite fitness scores. Variants whose 95% confidence intervals overlap are statistically indistinguishable and proceed to Phase 3.

**Phase 3 — Knockout (Statistically tied variants):** Tied variants enter a focused head-to-head lasting 72 hours. During this phase, traffic splitting is 50/50 between the two candidates. The safety supervisor monitors both outputs and intervenes only if either variant exceeds safety bounds. The variant with the higher cumulative fitness at the end wins; the loser enters retirement evaluation.

**Phase 4 — Palaver Council:** The winner from Phase 3 is presented to the variant council (per the Colony Thesis's Palaver tradition). The council includes the five voices: sensor testimony, actuator testimony, environmental testimony, ancestor testimony, and future testimony. The council produces a narrative assessment — not a numerical score — that either endorses the variant for promotion or requests further evaluation.

### 2.2 The Scout Variant

From the Chinese philosophical tradition (Sun Tzu's reconnaissance principle), the colony periodically generates **scout variants** — bytecodes deliberately designed with known weaknesses that are intended to reveal information about the environment through controlled failure.

A scout variant might deliberately test the boundaries of safe operation: "What happens if I reduce the obstacle avoidance margin from 50m to 30m?" The scout does NOT carry traffic — it runs in shadow mode only, producing outputs that are logged but never sent to actuators. The safety supervisor monitors the scout's outputs. If the scout's decisions would have been safe in 95% of cases but dangerous in 5%, the colony learns something about the distribution of conditions it faces.

Scout variants are sacrificial by design. They are not competing for fitness; they are competing for *information yield*. A scout that reveals a previously unknown failure mode is considered successful even though its own fitness score would be zero. The Griot layer records the scout's findings as narrative: "Scout variant S-47 discovered that at sea state 5 with following swell, the 30m obstacle margin produces 12% more efficient routing with no safety incidents. Marginal conditions are safe for reduction."

### 2.3 Statistical Rigor

All competition results must meet these thresholds before being accepted:

- **Minimum N:** 200 data points per condition category (from the Stress Test's power analysis formula)
- **Confidence interval:** 95% (α=0.05)
- **Effect size:** Cohen's d ≥ 0.3 (small-to-medium effect). Smaller effects are real but not worth the evolutionary disruption of switching variants.
- **Duration:** Minimum 24 hours in normal conditions; minimum 72 hours for safety-critical subsystems.
- **Environmental coverage:** The variant must have been observed in at least 3 distinct condition categories (e.g., calm, moderate, rough) before its fitness score is considered representative.

---

## III. Retirement and Death

### 3.1 Retirement Triggers

A variant is retired when any of these conditions is met:

1. **Clear defeat:** A replacement variant achieves ≥5% higher colony_fitness with 95% statistical confidence.
2. **Fitness below floor:** colony_fitness drops below the minimum viability threshold (0.3 on a 0-1 scale) for 7 consecutive days.
3. **Generation limit:** The variant has been active for more than 10 seasonal cycles (approximately 2.5 years) without meaningful improvement. The colony mandates periodic refresh through the Soviet principle of "mandatory simplification every 10th generation."
4. **Safety regression:** Any safety metric falls below the constitutional safety floor. The variant is retired immediately — no grace period.
5. **Apoptosis:** The variant voluntarily retires (see Section 3.3).

### 3.2 The Garden of the Dead

Retired variants are stored in the version archive on the Jetson, not deleted. The archive uses aggressive downsampling per the Stress Test's storage analysis:
- **Last 90 days:** Full bytecode + full metadata + raw telemetry (per-variant)
- **90 days to 2 years:** Compressed bytecode + summary metadata (fitness trajectory, retirement reason, cross-node adoption record)
- **Beyond 2 years:** Aggregated statistics only (behavioral fingerprint hash, peak fitness, lineage position, notable innovations)

The "Garden of the Dead" serves three purposes: (1) it enables resurrection when environmental conditions favor old adaptations, (2) it provides the lineage history that informs the Griot's narrative knowledge, and (3) it serves as the genetic material for crossover operations when the colony needs to combine successful traits from different lineages.

### 3.3 Apoptosis: Voluntary Self-Retirement

A bytecode variant can detect its own inadequacy and voluntarily retire. This implements a mechanism identified as a design gap in Phase 1B — the colony needs cellular apoptosis, not just external culling.

**Self-assessment triggers:**

1. **Performance drift:** The variant's rolling 7-day F_immediate has degraded by ≥15% relative to its historical peak, AND the degradation correlates with an environmental shift detected by the Jetson's terrain profiling system. The variant recognizes: "Conditions have changed, and I am no longer adapted."

2. **Environmental mismatch score:** The Jetson maintains a terrain profile (from the Chinese lens) that classifies the current operating regime. Each variant carries the terrain profile under which it was evolved. When the distance between the current terrain profile and the variant's native terrain profile exceeds a threshold (Euclidean distance > 0.7 in normalized terrain-feature space), the variant flags itself for replacement.

3. **Resource competition detected:** When the variant detects that other variants on the same node are performing better on the same condition categories (measured by shared telemetry), it reduces its own execution time allocation. If it falls below 10% execution allocation for 5 consecutive days, it triggers self-retirement.

Apoptosis is always a recommendation, never an autonomous action. The variant signals: "I believe I should be retired. Reason: [drift/mismatch/competition]. Evidence: [attached metrics]." The actual retirement decision is made by the colony council, which may override the self-assessment if the variant's weaknesses are actually environmental (e.g., all variants are degrading due to a systemic issue like sensor degradation, not variant inadequacy).

---

## IV. Diversity Maintenance

### 4.1 Minimum Lineage Mandate

The Colony Thesis mandates 5-7 active lineages at all times. This is enforced as a constitutional constraint:

```
if active_lineage_count < 5:
    trigger_emergency_spring()   # Force exploration regardless of season
    freeze_all_retirements()     # No variants may be retired until count >= 5
```

A "lineage" is defined as a family of variants sharing ≥70% structural similarity (measured by normalized edit distance of bytecode instruction sequences) AND serving the same functional niche. Two variants that differ only in PID gains are the same lineage. Two variants with different control algorithms (PID vs. fuzzy logic vs. model predictive) are different lineages.

### 4.2 The Useless Tree

The Daoist principle of the useless tree requires maintaining at least one lineage that performs below current fitness thresholds. This "useless" variant serves as ecological insurance: it may carry adaptations for conditions that the dominant variants do not handle well.

**Enforcement:** The colony maintains a "reserve pool" of 1-2 lineages whose fitness scores are allowed to drop to 0.3 (the minimum viability threshold) without triggering retirement. These reserve lineages receive reduced execution time (10% of total) but are never retired unless they fail the safety regression check. The reserve pool is refreshed each Spring: old reserves may be retired and new candidates selected from the Garden of the Dead if environmental patterns suggest their adaptations may become relevant.

### 4.3 The Apeiron Index

The Apeiron Index measures generational diversity as a colony health metric, combining three sub-indices:

1. **Behavioral entropy (Shannon H):** Computed over the behavioral fingerprints of all active variants. Each variant's behavioral fingerprint is a 20-dimensional feature vector (10 sensor-response features + 10 actuator-command features, normalized to [0,1] and quantized to 10 bins). The Shannon entropy of the distribution across these bins measures how behaviorally diverse the colony is.

2. **Lineage count:** Simple count of distinct active lineages. Must be ≥ 5.

3. **Exploration coverage:** Fraction of the known terrain-feature space that has at least one variant whose native terrain profile covers it. If the terrain space is discretized into 50 cells, and the colony's variants collectively cover 40 cells, exploration coverage = 0.8.

```
Apeiron_Index = 0.4·H_norm + 0.3·lineage_norm + 0.3·exploration_norm
```

where `_norm` indicates normalization to [0,1]. The Apeiron Index is computed weekly and displayed on the colony dashboard. When it drops below 0.6, the colony enters "diversity recovery mode" — Spring exploration is triggered regardless of season, and the minimum lineage mandate is enforced.

### 4.4 Speciation and the Founder Effect

**Speciation** occurs when two variants from the same lineage diverge beyond the 70% structural similarity threshold AND occupy distinct environmental niches (measured by terrain profile distance > 0.5). When speciation is detected, the colony registers the new lineage and assigns it a separate lineage identifier.

**The founder effect** — a single successful variant dominating and eliminating all competition — is prevented by three mechanisms:

1. **Anti-dominance rule:** No single variant may occupy more than 60% of a niche's execution time. If a variant's dominance exceeds this threshold, the colony artificially boosts the execution time of the next-best variant(s) to restore balance.

2. **Diversity penalty on fitness:** A variant's fitness is reduced by 5% for each lineage it eliminates. If variant A causes the retirement of variants B, C, and D, variant A's effective fitness is reduced by 15%. This creates evolutionary pressure against monopolistic behavior.

3. **Mandatory Spring diversity injection:** At the start of every Spring phase, the colony generates at least 3 new lineages from the Garden of the Dead (resurrecting old lineages with relevant terrain profiles) and 2 entirely new lineages through epsilon-random exploration (10% of variant generation budget is allocated to random mutations outside the AI's latent space).

---

## V. Colony-Level Selection vs. Individual Selection

### 5.1 The Ubuntu Coefficient

The Colony Thesis's Ubuntu principle requires that individual fitness is necessary but not sufficient. The **Ubuntu coefficient** (U) modifies each variant's effective fitness based on its contribution to other nodes:

```
effective_fitness(v) = colony_fitness(v) × (1 + U(v))
```

where:

```
U(v) = 0.3·cross_node_adoption_rate(v) + 0.3·pattern_generality(v) + 0.4·colony_resource_savings(v)
```

The colony_resource_savings metric measures how much this variant's innovations reduce resource consumption across the colony. If variant A's timing optimization reduces I2C bus utilization by 5%, and 6 of 8 nodes adopt it, the colony saves 5% × 6 = 30% bus time. This savings is attributed back to variant A as a positive contribution.

### 5.2 The Tragedy of the Commons

A variant that maximizes its own fitness but harms the colony is identified and penalized. Examples:

- A variant that achieves 10% better fuel efficiency by increasing actuator wear rate (measured by pump cycling frequency) by 30%.
- A variant that monopolizes I2C bus bandwidth, degrading the performance of other nodes.
- A variant that creates a dependency on a shared sensor, reducing flexibility for other nodes.

Detection: The colony's relational monitoring layer (per Agent-1A's "emergent behavior" requirement) tracks inter-node resource usage correlations. When variant A's deployment on Node 1 correlates with a >5% performance degradation on Node 2, a "commons violation" flag is raised.

Resolution: The violating variant's Ubuntu coefficient is set to a negative value, reducing its effective fitness below its individual colony_fitness. The variant is flagged for council review. The council may: (a) impose a resource usage cap on the variant, (b) require the variant to be modified to eliminate the negative externality, or (c) retire the variant.

### 5.3 Selection Resolution

The final selection decision integrates all three evaluation layers:

1. **GOST compliance** (binary floor): Does the variant meet minimum reliability thresholds? No → reject.
2. **Individual fitness** (necessary): Does the variant perform well on its own node? No → deprioritize.
3. **Colony contribution** (sufficient modifier): Does the variant help or harm the colony? Harm → penalize or reject. Help → promote.

A variant can have high individual fitness but low colony contribution (e.g., a hyper-optimized variant that works only on one node and cannot transfer). Such a variant is deployed on its home node but is not propagated. A variant with moderate individual fitness but high colony contribution may be promoted above a higher-performing but less-transferable variant. The colony optimizes for collective capability, not individual excellence.

---

## VI. Environmental Selection Pressure

### 6.1 Conditional Genetics

The colony's conditional genetics system (from Phase 1D) selects bytecodes based on environmental conditions. The VM scheduler maintains a dispatch table mapping terrain-profile cells to bytecode variants:

```
dispatch[terrain_cell_id] = variant_id
```

When the terrain profiler classifies the current environment into a cell, the VM loads the corresponding variant. Transitions between variants are seamless: the outgoing variant's state is snapshot to SRAM, the incoming variant's state is restored, and execution continues within one VM tick (<340 microseconds for the optimized v3.1 VM).

### 6.2 Seasonal Pressure

Each season applies distinct selection pressure:

| Season | Duration | Selection Emphasis | Action |
|---|---|---|---|
| **Spring** | 4 weeks | Exploration & diversity | Generate 3-5 new lineages per niche; epsilon-random mutations at 10%; resurrect candidates from Garden of the Dead |
| **Summer** | 8 weeks | Exploitation & optimization | League and knockout tournaments; fitness scores drive promotion; scout variants probe boundaries |
| **Autumn** | 4 weeks | Consolidation & debt reduction | Retire underperformers; compress bytecode; repay generational debt; mandatory simplification |
| **Winter** | 4 weeks | Rest & analysis | No evolutionary changes; all variants frozen; deep analysis of seasonal data; Winter Report generated |

The seasonal rhythm is constitutionally mandated and cannot be overridden. A human operator cannot "disable Winter" any more than they can disable the hardware watchdog — attempting to do so triggers the same safety override mechanism.

### 6.3 Aporia Mode: Forced Exploration Under Novelty

When the colony encounters conditions where ALL active variants perform below the minimum viability threshold simultaneously (Aporia — from the Greek philosophical tradition's "state of puzzlement"), the colony enters Aporia Mode:

1. **All variant execution is paused** except the incumbent safety baseline (the last known-good variant with a Lyapunov certificate).
2. **Maximum diversity injection:** The AI generates 10-15 new candidate variants using maximum epsilon (50% random exploration instead of the normal 10%). These are deliberately diverse — different control strategies, different parameter ranges, different algorithmic approaches.
3. **Rapid league play:** Candidates compete in 6-hour rounds (instead of the normal 24 hours) with relaxed statistical thresholds (80% confidence instead of 95%).
4. **Early exit:** As soon as any candidate achieves fitness > 0.5 (the "good enough to survive" threshold), it is promoted to active duty. The remaining candidates continue in background competition.
5. **Narrative recording:** The Griot layer produces a detailed record: "Aporia event at [timestamp]. Duration: [X hours]. Conditions: [terrain profile]. Resolved by: [variant lineage]. New adaptations discovered: [list]."

Aporia Mode is costly — it consumes significant Jetson compute, generates many failed variants, and temporarily reduces performance. But it is the colony's mechanism for escaping local optima when the environment changes beyond the current gene pool's capacity. Without it, the colony would be permanently trapped by whatever adaptations it evolved during its initial deployment.

---

## VII. The Generational Debt Ledger

### 7.1 Definition and Tracking

The Generational Debt Ledger is a per-variant, per-resource accounting system that tracks the cumulative cost of each evolutionary decision. It implements the Colony Thesis's Principle 6 (Generational Responsibility) and the Native American Seven Generations principle: every variant's fitness is reduced by the future optionality it consumes.

The ledger is maintained on the Jetson and synchronized to the colony's knowledge base. Each variant has a debt profile:

```
debt(v) = {
    storage: 0.45,      # Fraction of bytecode partition consumed
    memory: 0.32,       # Peak SRAM+PSRAM utilization
    dependencies: 2,    # New external dependencies introduced
    diversity_impact: -1,  # Lineages displaced (-1 means this variant contributed to retiring 1 lineage)
    complexity: 1.2,    # Size relative to ancestor (1.0 = same size)
    total: 0.97         # Weighted sum
}
```

### 7.2 Debt Ceilings

Each debt category has a ceiling. A variant that exceeds ANY ceiling is rejected regardless of fitness:

| Category | Ceiling | Rationale |
|---|---|---|
| Storage | 0.85 of partition | Must reserve 15% for new variant generation during Spring |
| Memory | 0.75 of available | Must reserve headroom for safety supervisor and telemetry tasks |
| Dependencies | 3 new per variant | Prevents dependency proliferation |
| Diversity impact | Cannot reduce below 5 lineages | Constitutional minimum diversity mandate |
| Complexity | 1.5x ancestor | Prevents bytecode bloat (Kolmogorov fitness penalty) |

### 7.3 Debt Repayment

The Autumn consolidation phase specifically addresses generational debt:

1. **Bytecode compression:** The Jetson's AI analyzes each active variant and identifies removable instructions (dead code, redundant branches, over-specified parameters). Compressed variants are generated and tested. If the compressed variant maintains ≥95% fitness, it replaces the original, reducing storage and complexity debt.

2. **Dependency pruning:** Variants that introduced dependencies during Spring/Summer are examined: can those dependencies be eliminated while maintaining ≥90% fitness? If so, the dependency is pruned.

3. **Diversity restoration:** Retired lineages from the current seasonal cycle are evaluated for resurrection. If the reserve pool has fewer than 2 lineages, candidates from the Garden of the Dead are resurrected with terrain profiles matching anticipated future conditions.

4. **Debt audit:** The Winter Report includes a full debt audit with trend analysis: "Storage debt increased 12% this cycle, primarily due to rudder control variants. At current trajectory, the storage ceiling will be reached in 3 cycles. Recommend mandatory bytecode compression during next Autumn."

---

## VIII. Concrete Examples

### 8.1 Marine Autopilot in Changing Sea States

**Setting:** A vessel with 4 active rudder-control bytecodes competing across seasons.

- **Variant R-Alpha:** Optimized for calm conditions (sea state 1-2). Tight heading control (±0.5°), fuel-efficient, but produces aggressive corrections in rough water that increase passenger discomfort. Fitness in calm: 0.92. Fitness in rough: 0.41.
- **Variant R-Beta:** Optimized for moderate conditions (sea state 3-4). Relaxed heading control (±2.0°), smoother actuator commands, good fuel efficiency. Fitness in calm: 0.78. Fitness in moderate: 0.88. Fitness in rough: 0.62.
- **Variant R-Gamma:** A scout variant designed to test aggressive obstacle avoidance reduction. Runs in shadow mode only. Reveals that at sea state 3, obstacle margins can be safely reduced from 50m to 35m, saving 8% fuel. This finding triggers a new variant (R-Delta).
- **Variant R-Delta:** Inherits R-Beta's moderate-weather control with R-Gamma's reduced margins. Autumn consolidation compresses it from 14KB to 9KB by removing redundant storm-response branches that were never triggered. Final fitness: 0.85 across all conditions.

**Outcome:** R-Delta becomes the dominant variant. R-Alpha is retired to the Garden of the Dead but kept in the reserve pool (it's the "useless tree" — if the vessel operates in protected waters where aggressive control is safe, R-Alpha may be resurrected). R-Beta remains as the second lineage. R-Gamma is archived with high information-yield marks. Diversity is maintained at 3 active + 1 reserve = 4 (below minimum; Spring triggers 2 new exploratory variants).

### 8.2 Greenhouse Climate Control

**Setting:** Temperature bytecodes evolve for different crop stages, humidity variants adapt to seasonal changes.

- **Spring (environmental):** The AI generates 4 new temperature variants targeting different growth stages. Variant T-Seedling maintains tight 24±1°C control (seedling germination). T-Vegetative allows wider 22±3°C (vegetative growth). T-Flowering targets 20±2°C (flowering induction). T-Fruiting optimizes for 18±3°C (fruit development).
- **Summer (environmental):** All four compete simultaneously. The conditional genetics dispatch table maps growth-stage sensor data (from soil moisture, leaf temperature, photoperiod sensors) to variant selection. As plants mature, the dispatch automatically shifts from T-Seedling → T-Vegetative → T-Flowering → T-Fruiting.
- **Autumn (environmental):** The Jetson analyzes the season's data and discovers that T-Vegetative and T-Fruiting share 85% structural similarity — they differ only in setpoint and deadband. They are merged into a single parametric variant T-Growth(stage, setpoint, deadband), reducing storage debt by 40% for this niche.
- **Winter (environmental):** No changes. The Winter Report notes: "Temperature variants achieved 12% energy savings compared to the previous season's single-variant approach. Humidity variants failed to converge — 3 lineages remain statistically tied. Recommend more epsilon-random exploration for humidity next Spring."

### 8.3 Factory Conveyor Control

**Setting:** Speed optimization variants compete with hard safety constraints preventing dangerous speed increases.

- **Variant C-Fast:** Increases conveyor speed by 15% by reducing the inter-product gap from 200mm to 170mm. Achieves higher throughput (F_immediate = 0.93) but the safety supervisor flags 3 near-miss events where products were within 30mm of each other — above the 50mm safety margin encoded in Gye Nyame. Safety regression detected → colony_fitness = 0. Rejected.
- **Variant C-Smart:** Maintains speed but introduces predictive gap control — it uses upstream sensor data to anticipate product arrival and adjust speed dynamically. No safety regression. F_immediate = 0.89 (slightly lower throughput than C-Fast, but still higher than the baseline's 0.82). F_reversible = 0.95 (stateless, Lyapunov certified). Colony fitness = 0.89 × α + 0.8 × β + 0.7 × γ + 0.95 × δ - 0.1 × ε = 0.83. Promoted.
- **Variant C-Gentle:** Reduces conveyor speed by 10% but introduces shock-absorbing acceleration profiles that reduce product damage by 35%. F_immediate for throughput = 0.72, but F_immediate for product quality = 0.95. The colony weights shift during Autumn: with an increased emphasis on quality (0.4 from 0.2), C-Gentle's composite F_immediate rises to 0.86. It becomes the new incumbent for delicate product lines, while C-Smart remains incumbent for durable product lines.

**Outcome:** The colony evolves conditional dispatch for conveyor control: C-Gentle for fragile products, C-Smart for durable products. Both are Lyapunov-certified (Level 1 changes). The safety supervisor's Gye Nyame enforcement prevented C-Fast from deploying, demonstrating that constitutional safety operates as intended — it is a boundary the colony cannot cross, not a parameter it can negotiate.

---

## IX. Summary of Key Design Decisions

| Decision | Rationale | Source |
|---|---|---|
| Safety as multiplier, not additive term | Prevents reward hacking; a single regression zeroes fitness | Stress Test §3.2 |
| League + knockout tournament format | Balances thoroughness with resource constraints | Engineering judgment |
| Scout variants in shadow mode only | Gains environmental information without risking safety | Chinese philosophical lens |
| Minimum 5-7 active lineages | Constitutional diversity mandate | Colony Thesis §1.4 |
| Useless tree reserve pool | Insurance against unknown future conditions | Daoist philosophy |
| Aporia Mode with 50% epsilon | Escapes local optima when all variants fail simultaneously | Greek philosophical lens |
| Debt ceilings per category | Prevents any single resource from being exhausted | Seven Generations principle |
| Autumn debt repayment cycle | Systematic reduction of accumulated evolutionary debt | Seasonal rhythm mandate |
| Ubuntu coefficient as fitness modifier | Individual performance necessary but not sufficient | Colony Thesis §1.2 |
| Garden of the Dead with downsampling | Preserves genetic material within storage constraints | Stress Test §1.4 |

---

*Agent-2D signing off. The survival-of-fittest mechanism is not cruelty — it is the colony's immune system. It identifies what is strong, preserves what is useful, maintains what is insurance, and retires what is exhausted. Without it, the colony is a museum of equally valued artifacts. With it, the colony is a living system that becomes precisely what its environment demands.*
