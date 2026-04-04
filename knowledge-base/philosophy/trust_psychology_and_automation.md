# Human-Machine Trust Psychology and Automation Trust Models

**Knowledge Base Article** | NEXUS Robotics Platform
**Revision:** 1.0 | **Date:** 2026-03-29
**Classification:** Theoretical Foundations for the INCREMENTS Trust Framework
**Cross-References:** [[philosophy_of_ai_and_consciousness]], [[agent_communication_languages]], [[Trust Score Algorithm Specification]], [[eight_lenses_analysis]], [[cross_cultural_design_principles]]

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Trust Theory Foundations](#2-trust-theory-foundations)
3. [Human-Automation Trust: The Core Literature](#3-human-automation-trust-the-core-literature)
4. [Trust Calibration](#4-trust-calibration)
5. [Trust Development Over Time](#5-trust-development-over-time)
6. [Trust in Autonomous Vehicles](#6-trust-in-autonomous-vehicles)
7. [Trust Measurement](#7-trust-measurement)
8. [Cultural Differences in Trust](#8-cultural-differences-in-trust)
9. [Trust in AI Systems](#9-trust-in-ai-systems)
10. [Computational Trust Models](#10-computational-trust-models)
11. [Trust and Ethics](#11-trust-and-ethics)
12. [Open Questions](#12-open-questions)
13. [Synthesis: NEXUS's INCREMENTS Framework](#13-synthesis-nexuss-increments-framework)
14. [References](#14-references)

---

## 1. Introduction

Trust is the invisible substrate upon which every human-machine relationship is built. From the earliest industrial machines to the most advanced large language models, the question of when and how humans place confidence in automated systems has remained one of the central problems in engineering, psychology, and philosophy. A surgeon trusts an autopilot to maintain altitude during a critical procedure; a factory operator trusts a robotic arm not to crush a colleague; a homeowner trusts a smart thermostat not to freeze the pipes while they sleep. In each case, trust is not binary — it exists on a continuum, calibrated by experience, shaped by expectations, and vulnerable to disruption.

The NEXUS robotics platform's INCREMENTS framework represents a distinctive approach to this ancient problem. Rather than treating trust as a static certification (as in aviation's DO-178C) or as an implicit byproduct of interface design (as in most consumer automation), NEXUS formalizes trust as a continuously computed, event-driven quantity that dynamically governs the autonomy level of each subsystem. A vessel's steering system does not achieve Level 4 autonomy because an engineer declared it so — it achieves Level 4 because it has demonstrated, over 45 days of sustained reliable operation with no safety-critical violations, that it has earned that trust. And it can lose it in 1.2 days.

This article provides a comprehensive, Wikipedia-grade survey of the scientific literature on human trust psychology and automation trust models, organized to show how each theoretical contribution informs NEXUS's design. The field spans six decades, multiple academic disciplines (psychology, engineering, computer science, economics, philosophy, anthropology), and a growing body of empirical evidence about how humans actually behave when they delegate control to machines. Understanding this literature is essential for anyone who works on, deploys, or regulates autonomous systems — and it is foundational to understanding why NEXUS's trust architecture looks the way it does.

---

## 2. Trust Theory Foundations

### 2.1 Defining Trust: Interpersonal, Organizational, and Institutional

Trust has been studied across multiple levels of human social organization, and each level provides insights relevant to human-machine trust.

**Interpersonal trust** was first systematically studied by Rotter (1967), who defined it as "a generalized expectancy held by an individual that the word, promise, oral or written statement of another individual or group can be relied upon." Rotter's Interpersonal Trust Scale demonstrated that trust is a relatively stable personality trait — some individuals are dispositionally more trusting than others, and this disposition affects their behavior across a wide range of social situations. Rotter's work established two critical insights: first, that trust involves an *expectancy* about future behavior (not just a perception of past behavior); second, that trust involves *vulnerability* — the trusting person accepts risk based on the expectation that the trusted party will act favorably.

Rotter's conceptualization has been refined by decades of subsequent research. The most influential refinement is the definition proposed by Rousseau, Sitkin, Burt, and Camerer (1998), who defined trust as "a psychological state comprising the intention to accept vulnerability based upon positive expectations of the intentions or behavior of another." This definition highlights three components that have become canonical: (1) trust is a *psychological state*, not a behavior; (2) trust involves *acceptance of vulnerability*; and (3) trust is based on *positive expectations*. This tripartite structure — state, vulnerability, expectation — is the foundation upon which all subsequent trust theory in human-automation interaction has been built.

**Organizational trust** extends the interpersonal concept to the level of firms, teams, and institutions. Mayer, Davis, and Schoorman (1995) proposed the most influential model of organizational trust, identifying three antecedent conditions that determine whether one party will trust another: *ability*, *benevolence*, and *integrity*. Their model has been validated across hundreds of empirical studies and remains the gold standard for understanding trust in professional and organizational settings.

**Institutional trust** — trust in systems, processes, and institutions rather than in specific individuals — is particularly relevant to automation. When a person boards a commercial aircraft, they are not trusting a specific pilot; they are trusting the institutional system of pilot training, FAA regulation, aircraft maintenance protocols, and air traffic control. Luhmann (1979) distinguished between *interpersonal trust* (trust in persons) and *system trust* (trust in systems), arguing that system trust is a necessary substitute for interpersonal trust in complex, modern societies where individuals cannot personally verify the competence of every expert they depend upon. This distinction maps directly to human-automation trust: users of autonomous systems are engaging in *system trust*, not interpersonal trust, even though the psychological mechanisms may be similar.

### 2.2 The Mayer-Davis-Schoorman Model (1995): Ability, Benevolence, Integrity

The Mayer, Davis, and Schoorman (1995) model, published in the Academy of Management Review, is the most widely cited framework for understanding trust antecedents. It proposes that trust is determined by three characteristics of the trustee (the party being trusted):

**Ability** refers to the trustee's competence to perform the task for which trust is being placed. In the context of automation, ability maps to the system's functional capability — can the autopilot actually maintain heading? Can the diagnostic AI actually detect the fault? Ability is domain-specific: a system may be highly trusted for one task (navigation) but distrusted for another (collision avoidance).

**Benevolence** refers to the trustee's intention to do good for the trustor, beyond any profit motive or obligation. In automation, benevolence maps to the perceived alignment of the system's goals with the user's welfare. A medical AI that recommends treatments optimized for patient outcomes (rather than hospital revenue) is perceived as benevolent. An algorithmic trading system that maximizes returns at any cost is not.

**Integrity** refers to the trustee's adherence to a set of principles that the trustor finds acceptable. In automation, integrity maps to the system's adherence to safety standards, transparency about its limitations, and consistency with user expectations. A self-driving car that silently disengages its autonomy without informing the driver violates integrity, regardless of whether the disengagement was technically correct.

Mayer, Davis, and Schoorman also identified two moderating factors: the *propensity to trust* (the trustor's general disposition toward trusting others, building on Rotter's work) and the *perceived risk* (the magnitude of potential negative outcomes if trust is misplaced). These moderating factors are critical for understanding why different users trust the same system to different degrees.

### 2.3 Trust as a Psychological State: The Willingness to Be Vulnerable

The defining feature of trust across all theoretical frameworks is the acceptance of vulnerability. Deutsch (1958) was among the first to formalize this, defining trust as occurring when an individual "can rely on the other, or is willing to act on the basis of the other's conduct." This willingness to act — to expose oneself to potential harm based on the expectation that the trusted party will not exploit that exposure — is what distinguishes trust from mere prediction. One can predict that a system will behave in a certain way without trusting it; trust requires that one *acts on* that prediction, accepting the risk of being wrong.

Luhmann (1979) further developed this idea by distinguishing between *familiarity* and *trust*. Familiarity is the result of repeated experience — you know what to expect because you have seen the pattern before. Trust goes beyond familiarity by involving a decision to *reduce complexity* by acting as if the expected outcome will occur, even though you cannot be certain. In the context of automation, familiarity corresponds to understanding how the system works; trust corresponds to relying on it despite incomplete understanding.

This distinction has profound implications for system design. A user who understands an autopilot's algorithm perfectly (high familiarity) may still not trust it if they believe it has a hidden failure mode. Conversely, a user who understands nothing about how a system works may place full trust in it based on brand reputation or aesthetic design cues. The relationship between familiarity and trust is complex and often non-monotonic — the Dunning-Kruger effect applies to automation trust as well, with users who know just enough to be dangerous often exhibiting the worst trust calibration.

### 2.4 Relevance to NEXUS: The INCREMENTS Trust Score as Computational Trust Psychology

The NEXUS INCREMENTS framework operationalizes trust as a continuous score T ∈ [0, 1.0], updated every evaluation window based on observed events. This is a direct computational implementation of the psychological state described by Rousseau et al. (1998): the trust score represents the "intention to accept vulnerability" as a function of the accumulated evidence of the system's ability, benevolence, and integrity.

The three event categories in the NEXUS trust model — GOOD, BAD, and NEUTRAL — map to the three trust antecedents:

- **Ability events** (e.g., `successful_action`, `successful_action_with_reserve`) reflect the system's demonstrated competence.
- **Benevolence events** (e.g., `human_override_approved` — the system correctly recognized the need for human intervention) reflect the system's alignment with user welfare.
- **Integrity events** (e.g., `safety_rule_violation`, `manual_revocation`) reflect violations of the principles the system is supposed to uphold.

The asymmetry in the trust score — gain rate α_gain = 0.002 versus loss rate α_loss = 0.05, a 25:1 ratio — directly encodes the psychological principle that trust is harder to build than to destroy (Slovic, 1993; Baumeister et al., 2001). The six autonomy levels (L0 through L5) represent graduated degrees of vulnerability acceptance, from "no autonomous actions" to "full autonomy with asynchronous notification." See [[Trust Score Algorithm Specification]] for the complete mathematical formalization.

---

## 3. Human-Automation Trust: The Core Literature

### 3.1 Lee & See (2004): The Foundational Paper

John D. Lee and Katrina A. See's 2004 paper "Trust in Automation: Designing for Appropriate Reliance," published in *Human Factors*, is universally recognized as the single most important work on trust in automation. It has been cited over 4,000 times and has shaped virtually every subsequent study in the field. Its central thesis is deceptively simple yet profoundly important: **the goal of trust design is not to maximize trust or minimize trust, but to calibrate trust to the actual capabilities and limitations of the automation.**

Lee and See argue that the "trust-automation paradox" — the observation that users sometimes over-rely on unreliable automation and under-rely on reliable automation — arises from a fundamental mismatch between how humans form trust and how automation actually works. Humans evolved to trust other humans, using social cues (eye contact, tone of voice, body language, reputation) that have no analog in machine behavior. When a human interacts with an automated system, they instinctively apply human trust heuristics to a non-human entity, producing systematic miscalibration.

**Three Bases of Trust.** Lee and See identify three distinct bases upon which trust in automation can be established:

1. **Performance trust** is based on the system's observed reliability and competence — does it do what it is supposed to do, accurately and consistently? This is the most intuitive basis of trust and the one most easily measured through failure rates, error rates, and task completion statistics. Performance trust is what most engineers think of when they design "reliable" systems.

2. **Process trust** is based on the user's understanding of *how* the system achieves its results — is its reasoning process transparent, understandable, and consistent with the user's mental model? A medical AI that says "the patient has a 73% probability of sepsis" but cannot explain *why* may achieve high performance but low process trust. Process trust is closely related to the concept of *explainability* in modern AI research.

3. **Purpose trust** is based on the user's belief that the system's *goals* are aligned with their own — does the system act in the user's best interest, or does it serve some other agenda? An algorithmic recommender system that optimizes for engagement (rather than accuracy or user welfare) may achieve high performance but low purpose trust, as users sense that the system's goals are not aligned with theirs.

Lee and See argue that all three bases must be addressed for trust to be appropriately calibrated. A system that performs well but has opaque reasoning and misaligned goals will generate either overtrust (if users assume good intent) or distrust (if users suspect hidden agendas). They recommend that designers explicitly consider all three bases when designing automated systems, and that trust be continuously monitored and adjusted rather than assumed at design time.

**Design Implications for NEXUS.** The INCREMENTS framework primarily models performance trust through event-driven scoring. Process trust is partially addressed through the transparency of the trust score itself — operators can see exactly why the system is at a particular trust level and which events contributed to it. Purpose trust is addressed through the safety_policy.json framework, which makes the system's goals (safety constraints) explicit and auditable. The framework's limitation is that it does not model the *operator's perception* of these bases — it models objective system behavior, not subjective human judgment. This gap is discussed in [[#7-trust-measurement|Section 7]] on trust measurement.

### 3.2 Muir (1987, 1994): Trust in Supervisory Control

Brenda Muir's pioneering work on trust in automated systems, published across two seminal papers in *Ergonomics* (1987) and (1994, with Moray), established the conceptual framework for understanding trust in supervisory control situations — scenarios in which a human operator oversees an automated system rather than directly performing tasks.

Muir proposed that trust in automation comprises three components, arranged hierarchically:

1. **Predictability** — Can the operator predict what the system will do in a given situation? This is the lowest level of trust and is based purely on the system's behavioral consistency. A system that always responds the same way to the same input is predictable, regardless of whether its responses are correct.

2. **Dependability** — Can the operator rely on the system to perform correctly when needed? This goes beyond predictability by incorporating the system's reliability over time and across different conditions. A system that is predictable but unreliable (e.g., it always fails in the same predictable way) has low dependability.

3. **Faith** — Does the operator believe the system will act in their best interest even in novel, unexpected situations? This is the highest and most abstract level of trust, incorporating beliefs about the system's underlying design philosophy, safety margins, and "graceful degradation" behavior.

Muir's experimental work (with Moray, 1996) demonstrated several critical findings:

- **Trust formation follows a sigmoid curve.** Initially, operators are skeptical and trust grows slowly. After a period of consistent good performance, trust accelerates rapidly. Finally, trust plateaus at a high level, with further good performance having diminishing effects. This sigmoid pattern is precisely what the NEXUS logistic gain branch T(t) = 1 - (1 - T₀)·exp(-λt) produces mathematically.

- **Trust violations cause disproportionate trust reduction.** A single failure after a long period of reliable performance causes a larger trust drop than a failure after a short period. This "violated expectations" effect is captured in the NEXUS model by the penalty branch, where trust loss is proportional to current trust T_prev — a failure at T=0.95 causes a larger absolute drop than the same failure at T=0.40.

- **Trust is task-specific.** Operators develop trust independently for different tasks, even when performed by the same system. A process control operator might trust the temperature regulation system while distrusting the pressure regulation system, even though both are controlled by the same software. This finding directly motivated NEXUS's per-subsystem trust independence (see [[Trust Score Algorithm Specification]], Section 8).

### 3.3 Parasuraman & Riley (1997): Use, Misuse, Disuse, and Abuse

Raja Parasuraman and V. Riley's 1997 paper "Humans and Automation: Use, Misuse, Disuse, Abuse" in *Human Factors* is the definitive review of how humans interact with automated systems and the ways in which these interactions go wrong. They identified four fundamental failure modes of human-automation interaction:

1. **Disuse (under-reliance):** The human fails to use automation that would improve performance, either because they do not trust it or because they are unaware of its capabilities. This represents a failure of trust *formation* — the automation may be excellent, but the human never gives it a chance. Disuse is particularly common when automation is introduced gradually and operators develop workarounds that become habitual.

2. **Misuse (over-reliance):** The human relies on automation beyond its demonstrated capabilities, either because they trust it too much or because they fail to monitor it adequately. This represents a failure of trust *calibration* — the human's trust exceeds the automation's actual competence. Misuse is the most dangerous failure mode because it combines inappropriate delegation with reduced vigilance.

3. **Abuse (inappropriate dependence):** The human uses automation in ways that the designers did not intend, often because the automation's actual behavior diverges from its specification. This can occur when operators discover "creative" uses of automated systems that exploit edge cases or design flaws.

4. **Failure to monitor:** The human fails to detect automation failures because their monitoring has degraded, either due to complacency (the system has been reliable for so long that monitoring seems unnecessary) or due to excessive workload (the human is too busy with other tasks to monitor effectively).

Parasuraman and Riley's framework is crucial because it shows that both too little trust and too much trust are dangerous. The ideal state — "appropriate reliance" — exists at the intersection of adequate trust (preventing disuse) and adequate skepticism (preventing misuse). This dual-failure perspective directly informed NEXUS's design philosophy: the 25:1 asymmetry prevents overtrust by making trust hard to earn, while the graduated autonomy levels (L0 through L5) ensure that even low-trust systems provide some value (preventing disuse).

### 3.4 Jian, Bisantz, & Drury (2000): Foundations of Human-Automation Trust Measurement

Jian Y. Jian, Ann M. Bisantz, and Colin G. Drury's 2000 paper "Foundations for an Empirically Determined Scale of Trust in Automated Systems," published in the *International Journal of Cognitive Ergonomics*, made three essential contributions to the field:

1. **Trust is distinct from usability.** Through factor analysis of trust-related questionnaire items, they demonstrated that trust in automation is a separate construct from perceived usability, perceived utility, and perceived reliability. A system can be easy to use (high usability) without being trusted, and a system can be trusted without being easy to use.

2. **Trust is multidimensional.** They identified 12 distinct dimensions of trust in automation, including reliability, accuracy, robustness, understandability, predictability, dependability, familiarity, utility, intention, faith, expediency, and diligence. No single metric captures the full complexity of trust.

3. **Trust is situation-specific.** Trust developed in one context does not automatically transfer to another. An operator who trusts a system in simulation may not trust it in the field; an operator who trusts a system for routine operations may not trust it for emergency procedures.

Their 12-item trust scale became the standard instrument for measuring trust in automation research and has been adapted for use in domains ranging from healthcare to aviation to autonomous driving. See [[#7-trust-measurement|Section 7]] for a detailed discussion of trust measurement methods.

### 3.5 Hoffman, Lee, Woods, & Zarnekow (2013): Trust in Automation Measurement

Gina M. Hoffman, John D. Lee, David D. Woods, and Rostislav Zarnekow's chapter "Trust in Automation: Lessons from Measurement" synthesized two decades of trust measurement research and proposed a comprehensive framework for evaluating trust. Their key insight was that trust measurement must account for the *dynamic* nature of trust — trust is not a static attitude but a continuously evolving assessment that changes in response to new information. They recommended measuring trust at multiple time points during system interaction rather than as a single pre- or post-exposure measurement.

Hoffman et al. also emphasized the distinction between *trust* (the psychological state) and *reliance* (the behavioral manifestation). A person may trust an automated system but still choose not to rely on it (e.g., due to regulatory requirements), or may rely on a system they do not trust (e.g., due to social pressure or time constraints). Measuring trust through behavior alone (reliance) is therefore insufficient — self-report measures, physiological measures, and behavioral measures each capture different aspects of the trust construct.

### 3.6 Kaber (2018): 30+ Years of Trust Research

David B. Kaber's 2018 review paper, "Issues in Human-Automation Interaction Modeling: The 30+ Year Journey from 1985 to 2015," published in *Ergonomics*, provides the most comprehensive survey of the trust in automation literature. Kaber identified several trends in the evolution of the field:

- **From static to dynamic models.** Early trust models (1980s–1990s) treated trust as a relatively stable attitude; later models (2000s–2010s) treat trust as a dynamic state that updates continuously.
- **From single-system to multi-system trust.** As automated systems have become more complex, trust research has shifted from studying trust in a single system to studying trust in systems-of-systems and human-automation teams.
- **From laboratory to field studies.** Early trust research relied heavily on controlled laboratory experiments; recent research increasingly uses field studies, simulation studies, and naturalistic observation.
- **From descriptive to prescriptive models.** While most trust research has been descriptive (understanding how trust works), there is a growing body of prescriptive work (designing systems that produce appropriately calibrated trust).

Kaber's review concludes with a call for interdisciplinary collaboration between psychologists, engineers, and computer scientists to develop trust models that are both theoretically grounded and practically implementable. NEXUS's INCREMENTS framework is a direct response to this call.

---

## 4. Trust Calibration

### 4.1 What Is Trust Calibration?

Trust calibration refers to the alignment between a person's trust in an automated system and the system's actual reliability and capabilities. A perfectly calibrated operator trusts the system exactly to the degree that trust is warranted — no more and no less. Trust calibration is the central normative concept in human-automation trust research: it is the standard against which all trust-related failures are judged.

The concept of calibration comes from the meteorological literature on probability judgment (Lichtenstein, Fischhoff, & Phillips, 1982), where a forecaster is "well-calibrated" if, over many predictions, it rains on 70% of the days for which the forecaster predicted a 70% chance of rain. Applied to automation, a well-calibrated operator delegates control to the automation exactly when the automation is likely to perform correctly and intervenes exactly when it is likely to fail.

### 4.2 Overtrust: The Most Dangerous Failure Mode

Overtrust — also called automation bias, complacency, or excessive reliance — occurs when an operator's trust exceeds the automation's actual capabilities. Overtrust is widely regarded as the most dangerous failure mode in human-automation interaction because it combines inappropriate delegation with reduced vigilance. The operator both gives the automation more control than it deserves and fails to monitor for the failures that this excessive delegation makes likely.

**Automation bias** (Mosier et al., 1996; Goddard, Roudsari, & Wyatt, 2012) is a specific form of overtrust in which operators disproportionately favor automated recommendations over their own judgment, even when the automation is demonstrably wrong. Goddard et al.'s systematic review found that automation bias occurs in 37–55% of clinical decision support system interactions, making it a significant patient safety concern. Automation bias is exacerbated by time pressure, high workload, and high-stakes environments — precisely the conditions under which automation is most valuable and most dangerous.

**Complacency** (Parasuraman & Manzey, 2010) is the reduced vigilance that accompanies overtrust. When an operator has relied on automation for a long period without observing failures, their monitoring behavior degrades. They check the automation less frequently, process automated outputs less critically, and take longer to detect failures when they occur. Bahner, Hüper, and Manzey (2008) demonstrated that complacency actually *increases* with experience — contrary to the intuitive assumption that training reduces misuse, experienced operators are often *more* susceptible to automation bias than novices because their initial skepticism has been eroded by familiarity.

**NEXUS's Approach to Overtrust Prevention.** The INCREMENTS framework prevents overtrust by design through three mechanisms:

1. **Slow trust gain** (27.4 days to reach the gain time constant). Trust cannot be rushed — no matter how many successful actions occur, the logistic gain branch ensures that trust approaches high levels only asymptotically. A system must demonstrate sustained reliability over weeks, not hours, to reach high autonomy levels.

2. **Fast trust loss** (1.2 days loss time constant). The 25:1 asymmetry means that even at high trust levels, a single bad event causes significant trust reduction. At T = 0.80 (Level 4), a single `safety_rule_violation` (severity 0.7) drops trust by approximately 3.5% in a single evaluation window — and trust continues to erode if bad events persist.

3. **Equilibrium ceiling under adverse conditions.** Under a 5% bad event rate, the trust score reaches equilibrium at approximately T ≈ 0.44 (Level 2). Under a 10% bad event rate, equilibrium drops to T ≈ 0.29 (Level 1). This means the system mathematically cannot reach high autonomy levels unless it is genuinely reliable — overtrust is structurally impossible.

### 4.3 Distrust: Underutilization and Mode Rejection

Distrust — also called undertrust, disuse, or rejection — occurs when an operator's trust is lower than the automation's actual capabilities warrant. While less immediately dangerous than overtrust, distrust imposes significant costs: automation that operators refuse to use provides no value, and operators who constantly override automation create additional workload for both themselves and the system.

Distrust can arise from several sources:

- **Negative past experience:** A single failure can disproportionately reduce trust, even if the failure was atypical (Slovic, 1993). This "negativity bias" is well-documented in human judgment and is one of the strongest arguments for designing automation that degrades gracefully rather than catastrophically.

- **Lack of transparency:** Operators who cannot understand *how* the automation works are less likely to trust it, even if its observed performance is good. This is the process trust dimension from Lee & See's framework.

- **Mismatched mental models:** If the operator's understanding of what the automation does differs from what it actually does, trust will be miscalibrated. For example, if an operator believes an autopilot handles crosswind corrections when it actually does not, they may distrust the autopilot's behavior during crosswinds even though it is performing exactly as designed.

- **Cultural and individual factors:** Dispositional trust (Rotter, 1967) varies across individuals and cultures. Some people are simply less trusting of technology, and some cultural contexts discourage delegation of control to machines.

**NEXUS's Approach to Distrust Prevention.** The INCREMENTS framework addresses distrust through:

1. **Low autonomy entry barriers.** Level 1 (Advisory) requires only T ≥ 0.20, achievable after approximately 7 days of reliable operation. This allows the system to provide value even at low trust levels — it can give recommendations even if it cannot act autonomously.

2. **Visible trust trajectory.** The trust score is continuously displayed to operators, showing them the system's track record and expected progression. This transparency helps operators develop accurate mental models of the system's capabilities.

3. **Per-subsystem independence.** A failure in one subsystem does not reduce trust in others. An operator who has lost trust in the steering system can still benefit from autonomous navigation or engine management.

### 4.4 Factors Affecting Trust Calibration

Research has identified several factors that influence whether trust is well-calibrated:

| Factor | Effect on Calibration | Direction | Mechanism |
|--------|----------------------|-----------|-----------|
| **System reliability** | Strongest single predictor (d = 0.73; Kraus et al., 2021) | Higher reliability → higher trust | Direct performance evidence |
| **Transparency** | Moderate effect (d ≈ 0.4) | Higher transparency → better calibration | Improved process trust |
| **Predictability** | Moderate effect | Higher predictability → higher trust | Reduced uncertainty |
| **Understandability** | Moderate effect | Higher understandability → better calibration | Improved mental models |
| **Training** | Variable effect | Depends on training content | Improved knowledge, but may increase overtrust |
| **Individual differences** | Moderate effect | Dispositional trust, cognitive style | Baseline propensity to trust/distrust |
| **Time pressure** | Negative effect | Reduces monitoring → overtrust | Resource depletion |
| **Workload** | Negative effect (curvilinear) | Both high and very low workload impair calibration | Attention allocation |
| **Cultural context** | Moderate effect | Varies by cultural dimensions | Social norms, technology attitudes |

### 4.5 NEXUS's Calibration Architecture: 27 Days to Earn, 1.2 Days to Lose

The INCREMENTS framework's trust dynamics are specifically designed to maintain calibration through asymmetric update rates:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Trust gain time constant (τ_g) | 658 windows ≈ 27.4 days | Time for trust to reach ~63% of its asymptotic value under ideal conditions |
| Trust loss time constant (τ_l) | 29 windows ≈ 1.2 days | Time for trust to fall to ~37% of its current value under sustained failures |
| Gain-to-loss ratio | 25:1 | Trust is 25× harder to build than to destroy |
| Decay time constant (τ_d) | 10,000 windows ≈ 417 days | Time for trust to decay to floor through inactivity alone |
| Days to L4 (ideal) | 45 | Minimum time to reach High Autonomy under perfect conditions |
| Days to L5 (ideal) | 83 | Minimum time to reach Full Autonomy under perfect conditions |
| Equilibrium trust (5% bad events) | T ≈ 0.44 (L2) | Maximum trust achievable under moderate unreliability |
| Equilibrium trust (10% bad events) | T ≈ 0.29 (L1) | Maximum trust achievable under high unreliability |

These numbers encode a profound design principle: **trust must be earned through sustained demonstration, not granted through declaration.** The system cannot talk its way into high autonomy — it can only perform its way there.

---

## 5. Trust Development Over Time

### 5.1 Initial Trust Formation

When a human first encounters an automated system, their initial trust is influenced by factors that precede any actual experience with the system. Lee and See (2004) identified several "antecedents of initial trust" that operate before the system is used:

- **Reputation and brand:** Users carry expectations from the manufacturer's reputation, similar products, and social recommendations. A Tesla owner's initial trust in Autopilot is influenced by media coverage, peer discussions, and the Tesla brand.
- **Appearance and anthropomorphism:** Systems that look "capable" or "human-like" tend to receive higher initial trust. This is the basis of the "computer as social actor" paradigm (Reeves & Nass, 1996).
- **Dispositional trust:** Individual differences in general propensity to trust (Rotter, 1967) affect initial trust. High-dispositional-trust individuals will start with higher trust; low-dispositional-trust individuals will start with skepticism.
- **First impressions:** The first few interactions with a system disproportionately shape subsequent trust development, due to primacy effects and anchoring bias (Asch, 1946).

### 5.2 Trust Building Through Experience

After initial contact, trust develops through accumulated experience. Muir and Moray (1996) identified a three-phase trust development process:

1. **Exploratory phase:** The operator tests the system cautiously, comparing its outputs to their own expectations. Trust grows slowly because each interaction is carefully evaluated. This corresponds to the initial (nearly linear) portion of the sigmoid curve.

2. **Exploitation phase:** After sufficient positive experience, the operator begins to rely on the system more heavily. Trust grows rapidly during this phase because the operator has accepted the system as generally competent and focuses on positive rather than negative evidence. This corresponds to the steep middle portion of the sigmoid curve.

3. **Stabilization phase:** Trust reaches a plateau as the system's behavior becomes predictable and routine. Further experience has diminishing effects because the operator has already formed a stable assessment. This corresponds to the asymptotic upper portion of the sigmoid curve.

**NEXUS Mapping:** The INCREMENTS framework's logistic gain branch T(t) = 1 - (1 - T₀)·exp(-λt) precisely models this three-phase development. The initial slow growth (exploratory), rapid middle growth (exploitation), and asymptotic plateau (stabilization) are emergent properties of the logistic equation with constant gain rate.

### 5.3 Trust Repair After Failures

Trust repair — the process of restoring trust after a violation — is one of the most practically important and theoretically complex topics in trust research. The effectiveness of repair depends critically on the *type* of violation:

**Competence violations** occur when the system fails to perform as expected (e.g., a collision avoidance system fails to detect an obstacle). Kraus and Schlick (2022) found that the most effective repair strategy for competence violations is *demonstrating improved performance* — the system must show, through action, that the failure was atypical and that corrective measures have been taken.

**Integrity violations** occur when the system is perceived to have violated its stated principles or hidden information (e.g., a self-driving car's autonomy level is misrepresented). For integrity violations, *apologies and explanations* are more effective than performance demonstrations, because the issue is not capability but perceived deception.

**Process violations** occur when the system's reasoning process is revealed to be flawed (e.g., an AI diagnostic system produces the right answer for the wrong reasons). Process violations are the hardest to repair because they undermine the operator's entire mental model of the system.

**NEXUS Mapping:** The INCREMENTS framework implements trust repair through the gain branch — the system naturally rebuilds trust by accumulating good events after a failure. However, the 25:1 asymmetry means that repair is slow: after a severe failure that drops trust from T = 0.80 to T = 0.40, it takes approximately 30 days of perfect performance to return to T = 0.80. This slow repair is intentional — it ensures that trust is only restored after sustained evidence of improvement, not after a brief period of good behavior.

### 5.4 Trust Erosion: Single vs. Cumulative Failures

Trust erosion is not a simple linear function of the number of failures. Research has identified several patterns:

- **Negativity bias:** A single failure has a larger impact on trust than a single success (Baumeister et al., 2001). In behavioral economics terms, humans are "loss averse" with respect to trust — they weight failures approximately 2–3× more heavily than equivalent successes.
- **Recency effect:** More recent failures have a larger impact than distant ones (Hogarth & Einhorn, 1992). A failure that occurred yesterday reduces trust more than an identical failure that occurred a month ago.
- **Violated expectations effect:** Failures after a long period of reliable performance cause disproportionate trust reduction because they violate the operator's stabilized expectations (Muir & Moray, 1996).
- **Cumulative erosion:** Multiple small failures can erode trust below a critical threshold even when no single failure is catastrophic. This is the "death by a thousand cuts" pattern.

### 5.5 NEXUS Mapping: L0→L5 as Trust Development Timeline

The INCREMENTS framework maps the trust development process onto six explicit autonomy levels:

| Level | Trust Threshold | Minimum Observation | Interpretation |
|-------|----------------|--------------------:|----------------|
| **L0** (Disabled) | — | — | No trust — the system must prove itself |
| **L1** (Advisory) | T ≥ 0.20 | 8 hours | Initial exploratory trust — system can suggest but not act |
| **L2** (Supervised) | T ≥ 0.40 | 48 hours | Growing confidence — system can act with monitoring |
| **L3** (Semi-Autonomous) | T ≥ 0.60 | 168 hours (7 days) | Established trust — system acts, human reachable within 30s |
| **L4** (High Autonomy) | T ≥ 0.80 | 336 hours (14 days) | Deep trust — system acts independently, periodic monitoring |
| **L5** (Full Autonomy) | T ≥ 0.95 | 720 hours (30 days) | Complete trust — asynchronous notification only |

The 25:1 asymmetry serves as erosion protection: trust can be destroyed 22× faster than it is built, ensuring that the system never reaches a high autonomy level without having truly demonstrated sustained reliability. This is the mathematical formalization of the intuitive principle that "trust takes years to build, seconds to break, and forever to repair."

---

## 6. Trust in Autonomous Vehicles

### 6.1 Self-Driving Car Trust Research

The development of SAE Level 0–5 autonomous driving has generated the largest single body of empirical research on trust in automation. Key findings include:

- **Takeover trust.** Eriksson and Stanton (2017) found that trust in automation significantly affects takeover time and quality in SAE Level 3 vehicles. Overtrusting drivers take longer to assume manual control because they assume the system will handle the situation. Undertrusting drivers may take over prematurely, negating the benefits of automation.

- **Trust dynamics during transitions.** Lu, Hengster, and Roetting (2021) demonstrated that both overtrust and undertrust degrade takeover performance, identifying an "optimal trust zone" — a Goldilocks region where trust is calibrated appropriately and takeover performance is maximized.

- **Mode confusion.** Endsley (2017) identified mode confusion — the operator's inability to determine what the automation is currently doing or about to do — as a primary safety concern in semi-autonomous vehicles. Mode confusion is a direct consequence of poor process trust (Lee & See, 2004): the operator does not understand *how* the system works and therefore cannot predict its behavior.

- **Operational Design Domain (ODD) trust.** Research has shown that trust is highly sensitive to the perceived boundaries of the ODD. Drivers who believe the system can handle only highway driving trust it in that domain but distrust it in urban environments, even if the system's actual capability extends to both.

**NEXUS Mapping:** The NEXUS L0–L5 autonomy levels closely parallel the SAE J3016 levels but add dynamic trust-based adjustment. In SAE, autonomy level is a static design-time property (the car is Level 3 because the engineer designed it to be Level 3). In NEXUS, autonomy level is a runtime property that changes based on observed performance (the system is at Level 3 *because it has demonstrated Level 3 reliability*). This makes NEXUS more conservative than SAE — a NEXUS Level 4 system has *earned* its autonomy through weeks of demonstrated reliability, not merely through design-time specification.

### 6.2 Aviation Autopilot Trust

Aviation has the longest history of human-automation trust research, dating back to the introduction of autopilots in the 1930s and accelerating with the glass cockpit revolution of the 1980s. Key findings include:

- **Automation surprise.** Sarter, Woods, and Billings (1997) documented numerous cases of "automation surprise" — situations in which the autopilot did something the pilot did not expect, often with serious consequences. The Airbus A320 accident at Mulhouse-Habsheim (1988) and the Air France Flight 447 crash (2009) both involved pilots who were confused about what the automation was doing.

- **Mode awareness degradation.** As automation complexity increases, pilots' ability to maintain awareness of the current automation mode degrades. This has led to regulatory requirements for mode annunciation and the development of "ecological interface design" principles that make automation modes visually salient.

- **Skill atrophy.** Extended use of automation leads to degradation of manual flying skills, creating a paradox: the more reliable the automation, the less capable the pilot becomes at handling automation failures. This has been demonstrated in both simulator studies and accident analyses.

**NEXUS Relevance:** Aviation's experience provides a cautionary tale for NEXUS. As the system progresses toward higher autonomy levels, operator skill at manual operation may degrade. The INCREMENTS framework mitigates this by requiring operators to remain engaged (at least at the notification level) even at L5, and by making demotion to lower levels a routine occurrence (not just during emergencies).

### 6.3 Maritime Autonomous Vessel Trust

Trust in autonomous maritime vessels is a relatively new but rapidly growing research area, driven by the International Maritime Organization's (IMO) regulatory scoping exercise for Maritime Autonomous Surface Ships (MASS) and the development of autonomous ferry and cargo vessel prototypes in Scandinavia and Asia.

Porathe et al. (2023) identified trust as a "critical factor for autonomous vessel adoption" and proposed a supervisory control framework where remote operators manage multiple autonomous vessels from a shore-based control center. Their findings highlight unique maritime trust challenges:

- **Communication latency.** Unlike aviation, where pilots are physically co-located with the automation, autonomous vessels may be controlled remotely with communication latencies of seconds to minutes. This latency fundamentally changes the trust dynamic because the operator cannot intervene quickly in emergencies.

- **Environmental variability.** Maritime environments are highly variable (weather, traffic, sea state), and the conditions under which the automation is reliable may change rapidly. Trust must be continuously recalibrated to the current environmental conditions.

- **Regulatory uncertainty.** The legal framework for autonomous vessels is still evolving, creating uncertainty about liability, responsibility, and operational standards. This regulatory uncertainty reduces operator trust because it removes the institutional safety net that aviation operators rely on.

Wróbel et al. (2021) conducted a comprehensive review of autonomous vessel challenges and concluded that trust, liability, and dynamic risk assessment are the three most significant barriers to autonomous vessel deployment — all three of which NEXUS's INCREMENTS framework directly addresses.

### 6.4 Trust Transfer: From One Domain to Another

Trust transfer refers to the phenomenon whereby trust developed in one context influences trust in a different but related context. Madhavan and Wiegmann (2007) found that operators transfer trust from familiar to unfamiliar systems based on perceived similarity — a pilot who trusts one autopilot will transfer some trust to a different autopilot from the same manufacturer, even without direct experience.

Trust transfer has both positive and negative implications for NEXUS:

- **Positive:** An operator who trusts the NEXUS platform on one vessel will transfer some trust to NEXUS on other vessels, reducing the time required for initial trust formation in fleet deployments.

- **Negative:** An operator who experiences a trust violation on one vessel may transfer distrust to the entire fleet, even if the failure was vessel-specific. This is why NEXUS's per-subsystem independence is critical — it prevents "guilt by association" from propagating across the fleet.

**NEXUS's Cross-Domain Trust Parameters:** NEXUS supports configurable trust parameters per domain, allowing the same core framework to be deployed across marine, agriculture, factory automation, mining, HVAC, home automation, healthcare, and autonomous vehicles with domain-appropriate calibration. See the cross-domain analysis for specific parameter recommendations.

---

## 7. Trust Measurement

### 7.1 Self-Report Scales

The most common method of measuring trust in automation is through self-report questionnaires. The gold standard is the scale developed by Jian, Bisantz, and Drury (2000), which uses a 12-item Likert scale measuring perceived reliability, predictability, dependability, familiarity, and other trust-related dimensions. The scale has been validated across multiple domains and shows acceptable reliability (Cronbach's α typically > 0.80).

Other notable self-report instruments include:

- **The Trust Perception Scale – Human-Robot Interaction (TiP-HRI)** developed by Ullman and Malle (2019), which measures trust across five dimensions: competence, experience, reliability, emotional connection, and cultural similarity.
- **The Automation Trust Scale** used in military contexts, which emphasizes mission-critical aspects of trust.
- **The Multidimensional Measure of Trust** by Schaefer (2013), which distinguishes between cognitive trust (based on evidence) and affective trust (based on feelings).

Self-report scales have the advantage of being easy to administer and directly measuring the psychological construct of interest. Their limitations include social desirability bias (operators may report higher trust than they actually feel to appear competent), retrospective distortion (memory biases affecting recall of past trust states), and the fundamental problem that self-reported trust may not predict actual reliance behavior.

### 7.2 Behavioral Measures

Behavioral measures infer trust from observable actions rather than self-reports. The two primary behavioral indicators are:

- **Compliance:** Does the operator follow the automation's recommendations? Compliance reflects the degree to which the operator accepts the automation's outputs as correct.

- **Reliance:** Does the operator allow the automation to act autonomously, and for how long? Reliance reflects the degree to which the operator delegates control to the automation.

Behavioral measures are more objective than self-reports but capture only the behavioral manifestation of trust, not the underlying psychological state. An operator may comply with an automation's recommendation while internally disagreeing with it (outward compliance, inward distrust), or may fail to comply despite trusting the system (e.g., due to regulatory requirements).

**NEXUS's Computational Trust as Behavioral Proxy.** The INCREMENTS framework's trust score can be interpreted as a behavioral measure of the *system's trustworthiness* (as opposed to the operator's trust). The trust score reflects the accumulated behavioral evidence — actions taken, actions failed, safety violations detected — rather than subjective feelings. This makes it an inherently objective measure that is not subject to the biases of self-report scales.

### 7.3 Physiological Measures

Physiological measures attempt to capture the autonomic nervous system's response to trust-related situations. These measures include:

- **Eye tracking:** Pupil dilation, fixation patterns, and saccade velocity can indicate cognitive load, uncertainty, and attention allocation during human-automation interaction. Operators who trust an automation tend to fixate on it less frequently (reduced monitoring), while operators who distrust it show increased scanning behavior.

- **Electroencephalography (EEG):** Event-related potentials (ERPs) such as the P300 and error-related negativity (ERN) can indicate surprise, error detection, and conflict resolution during automation monitoring. EEG studies have shown that automation failures elicit larger ERN responses than human errors, suggesting that the brain processes automation errors differently.

- **Galvanic skin response (GSR):** Changes in skin conductance can indicate arousal and emotional response to trust violations. GSR spikes are often observed immediately after automation failures, particularly when the failure is unexpected.

- **Heart rate variability (HRV):** Reduced HRV is associated with increased cognitive load and stress during difficult trust decisions.

Physiological measures have the advantage of being continuous and involuntary, providing real-time data about the operator's trust state. Their limitations include high individual variability, sensitivity to non-trust-related factors (fatigue, temperature, caffeine), and the need for specialized equipment.

### 7.4 Computational Trust Models

Computational trust models formalize trust as a mathematical quantity that can be computed, stored, and transmitted. These models range from simple numerical scores to complex probabilistic frameworks. NEXUS's INCREMENTS framework is a computational trust model — it produces a numerical trust score that is updated algorithmically based on observed events.

Computational trust models have a critical advantage over psychological measures: they are *objective and reproducible*. The same event stream always produces the same trust score, regardless of the operator's mood, fatigue, or cultural background. This makes them suitable for safety-critical applications where consistency and predictability are essential.

The limitation of computational trust models is that they measure *trustworthiness* (the system's demonstrated reliability) rather than *trust* (the human's psychological state). A system may be highly trustworthy (high trust score) while the operator still distrusts it (low subjective trust), or vice versa. The gap between computational trustworthiness and psychological trust is the fundamental challenge of human-automation trust calibration. See [[#10-computational-trust-models|Section 10]] for a detailed comparison of computational trust models.

### 7.5 NEXUS's 12-Parameter Algorithm as Trust Measurement

The NEXUS trust score algorithm uses 12 tunable parameters to compute a trust score from observed events. The 12 parameters are:

| # | Parameter | Symbol | Default | Role in Trust Measurement |
|---|-----------|--------|---------|---------------------------|
| 1 | Gain rate | α_gain | 0.002 | Sensitivity of trust increase to good events |
| 2 | Loss rate | α_loss | 0.05 | Sensitivity of trust decrease to bad events |
| 3 | Decay rate | α_decay | 0.0001 | Rate of trust erosion during inactivity |
| 4 | Trust floor | t_floor | 0.20 | Minimum baseline trust maintained during inactivity |
| 5 | Quality cap | quality_cap | 10 | Maximum event count contributing to gain per window |
| 6 | Evaluation window | evaluation_window_hours | 1.0 | Temporal resolution of trust updates |
| 7 | Severity exponent | severity_exponent | 1.0 | Nonlinearity of severity weighting |
| 8 | Streak bonus rate | streak_bonus | 0.00005 | Reward for consecutive clean windows |
| 9 | Minimum events for gain | min_events_for_gain | 1 | Evidence threshold for trust increase |
| 10 | Reset grace period | reset_grace_hours | 24.0 | Cooldown between trust resets |
| 11 | Promotion cooldown | promotion_cooldown_hours | 72.0 | Minimum time between autonomy promotions |
| 12 | Count penalty slope | n_penalty_slope | 0.1 | Sensitivity to multiple simultaneous failures |

This 12-parameter model can be understood as a computational operationalization of the human trust psychology literature: the gain/loss asymmetry (parameters 1–2) captures negativity bias; the quality cap (parameter 5) prevents event flooding from inflating trust; the streak bonus (parameter 8) captures the psychological reward of sustained good performance; and the decay rate (parameter 3) captures the slow erosion of trust through inactivity.

---

## 8. Cultural Differences in Trust

### 8.1 Cross-Cultural Trust Research

Trust is not a universal psychological phenomenon — it varies significantly across cultures, and these variations have important implications for the design and deployment of automated systems.

The most influential framework for understanding cultural differences in trust is Hofstede's (2001) cultural dimensions theory, which identifies several dimensions that directly affect trust attitudes:

- **Power Distance** affects trust in authority and automation. High power distance cultures (e.g., China, Malaysia, Mexico) tend to place more trust in systems endorsed by authoritative institutions, while low power distance cultures (e.g., Denmark, Israel, Austria) are more skeptical of top-down automation mandates.

- **Uncertainty Avoidance** affects trust in novel systems. High uncertainty avoidance cultures (e.g., Japan, Greece, Portugal) are initially more distrustful of new technology and require more evidence before trusting it, while low uncertainty avoidance cultures (e.g., Singapore, Jamaica, Denmark) are more willing to experiment with new systems.

- **Individualism vs. Collectivism** affects the basis of trust formation. Individualist cultures (e.g., USA, UK, Australia) tend to base trust on direct personal experience, while collectivist cultures (e.g., China, Korea, Japan) place greater weight on social proof — the opinions and experiences of others in their reference group.

- **Long-Term Orientation** affects trust repair. Cultures with long-term orientation (e.g., China, Japan, South Korea) may be more willing to invest in rebuilding trust after failures, while cultures with short-term orientation (e.g., USA, UK, Nigeria) may abandon systems more quickly after trust violations.

### 8.2 High-Trust vs. Low-Trust Societies

Fukuyama (1995) proposed the distinction between "high-trust" and "low-trust" societies, arguing that cultures with high generalized social trust (trust in strangers and institutions) are more economically productive because they reduce the transaction costs of cooperation. This framework has direct implications for automation adoption:

- **High-trust societies** (Scandinavian countries, the Netherlands, Canada) tend to adopt automation more readily because they start with a higher baseline trust in institutions and technology. Automation designers in these markets can assume a higher initial trust level and focus on maintaining calibration.

- **Low-trust societies** (Mediterranean countries, parts of Latin America and Africa) tend to be more skeptical of automation and require stronger evidence of reliability before adoption. Automation designers in these markets must invest more in initial trust building and transparency.

### 8.3 Trust in Technology Across Cultures

Zhang et al. (2022) conducted a survey study across five countries (Japan, China, USA, Germany, and India) and found significant cultural differences in trust in autonomous vehicles:

- **Japanese and Chinese participants** showed higher initial trust in autonomous vehicles compared to American and German participants, but lower trust repair after failures. This pattern is consistent with the collectivist emphasis on social proof (high initial trust based on positive social signals) combined with the face-saving culture that makes failure recovery more difficult.

- **American and German participants** showed lower initial trust but higher trust repair, consistent with the individualist emphasis on direct experience (requiring personal evidence before trusting) and the cultural tolerance for failure as a learning opportunity.

- **Indian participants** showed the highest variance in trust, reflecting the country's cultural diversity and the wide range of prior experience with automation.

### 8.4 NEXUS's Cultural Deployment Profiles

NEXUS addresses cultural differences through configurable deployment profiles, as developed in the [[eight_lenses_analysis|Eight Lenses Analysis]] and [[cross_cultural_design_principles|Cross-Cultural Design Principles]]. Seven regional deployment profiles have been defined, each specifying:

- **Trust calibration parameters:** Different α_gain/α_loss ratios for different cultural contexts. For example, high-uncertainty-avoidance cultures use more conservative ratios (slower gain, same or faster loss).
- **Human oversight model:** Different levels and styles of human involvement in the autonomy loop. Hierarchical cultures prefer clear operator authority; egalitarian cultures prefer collaborative oversight.
- **Communication style:** Different framing of trust-related information. Collectivist cultures prefer community-based trust summaries; individualist cultures prefer per-operator trust dashboards.

| Region | Trust Calibration | Days to L4 | Human Oversight Model |
|--------|------------------|-----------|----------------------|
| East Asia (Japan, Korea, China) | Moderate gain (30–45 days); high penalty for protocol violations | 30–45 | Hierarchical: operator as elder |
| Sub-Saharan Africa | Community-calibrated: collective evaluation, not individual performance | Variable | Communal: operator as elder voice in palaver |
| Northern Europe | High initial trust; rapid evidence-based calibration | 15–25 | Egalitarian: operator as colleague |
| Mediterranean / Middle East | Moderate initial trust; relationship-based calibration | 25–40 | Relational: operator as family elder |
| North America | Low initial trust; rapid evidence-based calibration | 20–35 | Pragmatic: operator as manager |
| South / Southeast Asia | Variable; mixed collectivist and individualist | 20–40 | Hierarchical with community input |
| Latin America | Relationship-based; high importance of social proof | 25–40 | Relational: operator as padrino/madrina |

---

## 9. Trust in AI Systems

### 9.1 Trust in Large Language Models: Transparency, Consistency, Reliability

The emergence of large language models (LLMs) as practical tools for code generation, decision support, and knowledge work has created a new frontier for trust research. LLMs present unique trust challenges because they combine high capability (can produce convincing, seemingly expert outputs) with fundamental limitations (can hallucinate confidently, produce inconsistent outputs for similar inputs, and lack true understanding of the content they generate).

Three dimensions of LLM trust have emerged as critical:

- **Transparency:** Can the user understand why the LLM produced a particular output? Current LLMs are largely opaque — even with chain-of-thought prompting, the reasoning process is not fully interpretable. This opacity makes process trust (Lee & See, 2004) difficult to establish.

- **Consistency:** Does the LLM produce similar outputs for similar inputs? LLMs are stochastic — the same prompt can produce different outputs on different runs, and the distribution of outputs can shift across model versions. Inconsistency undermines predictability, which Muir (1994) identified as the foundation of trust.

- **Reliability:** Does the LLM produce correct outputs? For code generation, reliability can be measured through test suite pass rates and human evaluation. NEXUS's AI model analysis found that Qwen2.5-Coder-7B achieves 89.6% on HumanEval but has a 29.4% missed safety issue rate when self-validating. This means the LLM is reliable for most tasks but unreliable for safety-critical tasks — precisely the situation where trust calibration is most important.

### 9.2 Trust in AI-Generated Code

NEXUS's architecture involves AI agents generating bytecode programs that are deployed to embedded hardware. This creates a unique trust challenge: can humans trust code that they did not write and may not fully understand?

Research on trust in AI-generated code has identified several factors:

- **Verifiability:** Can the generated code be formally verified? NEXUS's bytecode VM is small enough (32 opcodes) that generated programs can be exhaustively tested, bounded-time verified, and statically analyzed before deployment.

- **Explainability:** Can the AI explain *why* it generated a particular code sequence? NEXUS's reflex synthesis pipeline includes a narration step that generates natural-language explanations of generated reflexes.

- **Sandboxing:** Can the generated code be run in a safe environment before deployment? NEXUS's VM enforces cycle budgets, stack depth limits, and safety invariants that prevent generated code from causing physical damage even if it contains bugs.

- **Validation by independent agent:** NEXUS uses a separate cloud-based validator (Claude 3.5 Sonnet achieves 95.1% safety catch rate) to independently verify generated reflexes before deployment. This two-agent architecture prevents the "self-validation bias" where an agent rates its own output favorably.

### 9.3 Explainability as Trust Enabler

Explainable AI (XAI) has emerged as a key approach to building trust in AI systems. The basic argument is that if an AI system can explain its reasoning, users will be better able to calibrate their trust — they can evaluate the quality of the reasoning, not just the output.

However, research has shown that explainability is a double-edged sword:

- **Positive effects:** Explanations can improve trust calibration by providing process trust (Lee & See, 2004). Users who understand *why* a system made a decision can better judge whether that decision was appropriate.

- **Negative effects:** Explanations can *increase* overtrust by creating an illusion of understanding. Users may feel that they understand a system because they have seen an explanation, even if the explanation is simplified or misleading. This "explanation effect" has been demonstrated in multiple studies (Glikson & Woolley, 2020).

- **Harmful explanations:** Poorly designed explanations can be worse than no explanation. An explanation that is technically accurate but misleading can cause users to trust a system in situations where it is unreliable.

### 9.4 The "Black Box" Trust Problem

The fundamental challenge of trust in AI systems is the "black box" problem: the systems are too complex for humans to fully understand, yet humans must decide whether to rely on them. This challenge is particularly acute for deep neural networks, where the mapping from inputs to outputs is distributed across millions of parameters with no human-interpretable structure.

The NEXUS platform takes a distinctive approach to the black box problem: rather than trying to make the AI understandable, it makes the AI's *outputs* verifiable. The generated bytecode is small, deterministic, and bounded — it can be tested exhaustively before deployment. The trust score provides an objective measure of the system's historical reliability. The per-subsystem independence limits the blast radius of any single AI-generated program failure.

This approach can be summarized as: **don't trust the AI; trust the verification pipeline.** The AI generates candidates; the verification pipeline (VM bounds, static analysis, independent validation, trust score) ensures that only safe, reliable programs are deployed. Trust is placed in the safety architecture, not in the AI itself.

---

## 10. Computational Trust Models

### 10.1 Beta Distribution Models

Beta distribution models represent trust as a probability distribution over the range [0, 1], parameterized by two shape parameters α (successes) and β (failures). The mean of the distribution α/(α + β) represents the point estimate of trust, while the variance αβ/((α+β)²(α+β+1)) represents uncertainty.

The advantage of beta distribution models is their mathematical elegance: they are the conjugate prior for the Bernoulli/binomial likelihood, meaning that Bayesian updating with new evidence (success or failure) requires only incrementing α or β — no complex computation is needed. This makes them computationally efficient and well-suited for embedded systems.

Teacy, Patel, Jennings, and Luck (2006) applied beta distribution models to trust in multi-agent systems, showing that they can effectively capture the uncertainty in trust estimates when evidence is limited. However, beta distribution models have a significant limitation: they assume that all evidence is equally informative, with no recency weighting or event severity differentiation. A minor anomaly detected five months ago is weighted equally with a major safety violation detected yesterday.

### 10.2 Bayesian Trust Models (Jøsang)

Audun Jøsang's subjective logic framework (Jøsang & Pope, 2005) extends the beta distribution model by adding an explicit uncertainty dimension. In subjective logic, trust is represented as a triplet (b, d, u) — belief, disbelief, and uncertainty — where b + d + u = 1. This representation allows the model to distinguish between "I don't trust this system" (high disbelief) and "I don't have enough information to trust this system" (high uncertainty).

Jøsang's framework also provides operators for trust *composition* (combining trust from multiple sources), *transitivity* (deriving trust in a third party from trust in a recommender), and *aggregation* (combining multiple trust assessments). These operators enable multi-agent trust reasoning that goes beyond simple point estimates.

### 10.3 Fuzzy Trust Models

Fuzzy trust models represent trust using fuzzy logic, where trust is not a crisp number but a fuzzy set with membership functions for categories like "low trust," "medium trust," and "high trust." These models can capture the imprecision and gradation inherent in human trust judgments, which are often expressed in qualitative rather than quantitative terms ("I somewhat trust this system" rather than "I trust this system 0.73").

Fuzzy trust models have been applied in peer-to-peer networks, e-commerce, and multi-agent systems. Their advantage is the ability to handle linguistic uncertainty and qualitative inputs. Their disadvantage is the difficulty of defining appropriate membership functions and inference rules, which often require domain expertise and may not transfer well across domains.

### 10.4 Reputation Systems

Reputation systems aggregate trust information from multiple sources to compute a collective trust assessment. The most well-known reputation systems include:

- **EigenTrust** (Kamvar, Schlosser, & Garcia-Molina, 2003): Uses the PageRank algorithm to compute a global trust score for each peer in a peer-to-peer network. Each peer rates its interactions with other peers, and the ratings are aggregated using the principal eigenvector of the rating matrix. EigenTrust has the property that reputation propagates transitively — a peer trusted by trusted peers inherits some of that trust.

- **PageRank** (Page, Brin, Motwani, & Winograd, 1999): Originally developed for web search, PageRank assigns importance scores to nodes in a graph based on the importance of the nodes linking to them. Applied to trust, PageRank can compute the "trust authority" of each agent in a network.

- **eBay-style feedback systems:** Simple summation or averaging of positive and negative ratings. These systems are widely used but have known vulnerabilities to strategic manipulation (fake positive reviews, retaliatory negative reviews).

### 10.5 Multi-Agent Trust: Regret, FIRE, and Related Systems

Multi-agent trust systems address the challenge of computing and maintaining trust in environments with many interacting agents, where agents may have conflicting interests and may behave strategically.

- **REGRET** (Sabater & Sierra, 2002): Combines three dimensions of reputation — individual (direct experience), social (witnessed interactions), and ontological (role-based). REGRET computes a composite reputation score that accounts for the source and reliability of each piece of evidence.

- **FIRE** (Huynh, Jennings, & Shadbolt, 2006): Combines four trust models — interaction trust (direct experience), role-based trust (based on agent roles), witness reputation (based on third-party reports), and certified reputation (based on institutional endorsements). Each model contributes to a composite trust score using a weighted combination.

### 10.6 Comprehensive Comparison: Computational Trust Models vs. NEXUS INCREMENTS

| Feature | Beta Distribution | Jøsang Subjective Logic | Fuzzy Trust | EigenTrust | REGRET/FIRE | **NEXUS INCREMENTS** |
|---------|------------------|------------------------|-------------|------------|-------------|---------------------|
| **Trust representation** | Probability distribution | Triplet (b, d, u) | Fuzzy set | Scalar (0–1) | Composite scalar | Scalar (0–1) |
| **Uncertainty quantification** | Variance of distribution | Explicit uncertainty component | Fuzzy membership | No | Partial (via composite) | No explicit uncertainty |
| **Event severity** | Binary (success/fail) | Binary | Fuzzy severity | Binary | Variable | Continuous [0, 1] severity scale |
| **Event quality** | No | No | No | No | Partial | Continuous [0, 1] quality scale |
| **Asymmetry (gain vs. loss)** | Symmetric (β/α ratio) | Symmetric | Configurable | Symmetric | Configurable | **25:1 enforced** |
| **Recency weighting** | No | No | No | PageRank damping | Partial | No (all windows equal weight) |
| **Multi-agent composition** | No | Yes (operators) | No | Yes (eigenvector) | Yes | Per-subsystem independence |
| **Safety guarantees** | None | None | None | None | None | **Provable: equilibrium below L3 under 5% failures** |
| **Real-time capable** | Yes (simple update) | Moderate | Moderate | No (global computation) | No (requires communication) | **Yes (12 parameters, O(1) per window)** |
| **Domain** | E-commerce, P2P | Security, multi-agent | General | P2P, web | Multi-agent systems | **Safety-critical robotics** |
| **Parameters** | 2 (α, β) | 3+ per relationship | Multiple MFs | 1 (damping) | Multiple | **12 parameters** |
| **Autonomy levels** | No | No | No | No | No | **6 levels (L0–L5)** |
| **Formal proofs** | Yes (conjugate prior) | Yes (logic axioms) | No | Yes (eigenvector theory) | No | **Yes (fixed points, stability, independence)** |
| **Field deployment** | Limited | Limited | Academic | Limited | Academic | **NEXUS fleet deployment** |

**Key differentiators of NEXUS INCREMENTS:**

1. **Asymmetry enforcement.** The 25:1 gain-to-loss ratio is not merely a parameter — it is a structural property enforced by the parameter validation rules (α_loss > α_gain × quality_cap). This prevents the system from reaching high trust levels through statistical noise.

2. **Safety guarantees.** The INCREMENTS framework provides formal mathematical guarantees that no other model offers: provable equilibrium ceilings under adverse conditions, provable independence between subsystems, and provable bounds on adversarial trust inflation.

3. **Real-time operation on embedded hardware.** The algorithm requires O(1) computation per evaluation window and fits within the resource constraints of an ESP32-S3 microcontroller. No other model in this comparison has been designed for real-time execution on resource-constrained embedded hardware.

4. **Event richness.** The 15-event taxonomy with continuous severity and quality scales provides far richer evidence than the binary success/fail models used by most computational trust frameworks.

5. **Graduated autonomy.** The six autonomy levels provide actionable behavioral outcomes linked to trust scores, transforming the abstract concept of trust into concrete operational permissions.

---

## 11. Trust and Ethics

### 11.1 Responsibility and Trustworthy AI

The concept of "trustworthy AI" has become a central theme in AI ethics and policy. The European Commission's High-Level Expert Group on AI (2019) identified seven requirements for trustworthy AI: human agency and oversight, technical robustness and safety, privacy and data governance, transparency, diversity and fairness, societal and environmental well-being, and accountability.

These requirements are interrelated through trust: technical robustness and safety are necessary for trustworthiness, transparency enables trust calibration, and accountability provides recourse when trust is violated. The ethical imperative is not merely to build AI that *can* be trusted, but to build AI that *deserves* to be trusted.

### 11.2 EU AI Act: Trustworthiness Requirements

The EU AI Act (Regulation 2024/1689), which entered into force in August 2024, establishes legally binding requirements for AI systems classified as "high-risk." Six of NEXUS's eight target domains (Marine, Agriculture, Factory, Mining, Healthcare, Ground AV) are classified as high-risk under the Act, requiring compliance with:

- **Risk management systems** (Article 9): Continuous identification and mitigation of risks throughout the AI system lifecycle.
- **Data governance** (Article 10): Ensuring training, validation, and testing datasets are relevant and representative.
- **Technical documentation** (Article 11): Comprehensive documentation of the AI system's design, capabilities, and limitations.
- **Record-keeping and logging** (Article 12): Automatic logging of the AI system's operations for traceability.
- **Transparency** (Article 13): Providing users with sufficient information to understand the system's capabilities and limitations.
- **Human oversight** (Article 14): Ensuring effective human oversight mechanisms are in place.
- **Accuracy, robustness, and cybersecurity** (Article 15): Ensuring the system achieves appropriate levels of accuracy, robustness, and security.

The INCREMENTS framework partially satisfies the human oversight requirement (Article 14) by providing a quantitative, evidence-based mechanism for adjusting autonomy levels based on observed system performance. This is a distinctive compliance advantage — most AI systems have no equivalent mechanism for dynamically adjusting their autonomy based on demonstrated trustworthiness.

### 11.3 The Duty of Trustworthiness

Ryan (2020) argues that trustworthiness is not merely a desirable property but a *moral duty* for those who design and deploy AI systems. When users place trust in an AI system, they make themselves vulnerable based on the expectation that the system will act in their interest. If the system fails to meet this expectation — whether through bugs, design flaws, or misaligned objectives — the user bears the cost of that vulnerability. The designer who creates a system that invites trust without deserving it is, in effect, exploiting the user's willingness to be vulnerable.

This moral argument has direct implications for NEXUS: the platform's trust architecture is not merely an engineering feature but an ethical commitment. By ensuring that high autonomy must be earned through demonstrated reliability and can be revoked rapidly on evidence of failure, NEXUS respects the operator's vulnerability. The system does not ask for trust it has not earned, and it does not maintain trust it does not deserve.

### 11.4 NEXUS's Position: Trust Must Be Earned, Not Granted

NEXUS's foundational trust principle is: **trust must be earned through sustained demonstrated reliability, not granted through declaration, certification, or assumption.** This principle manifests in every aspect of the INCREMENTS framework:

- A new subsystem starts at T = 0.0 (Level 0: Disabled), not at some assumed baseline.
- Trust can only increase through observed good events — there is no mechanism for declaring trust.
- Trust is lost immediately on evidence of failure — there is no grace period for bad events.
- Autonomy promotion requires sustained performance over days, not minutes — a brief period of good behavior is insufficient.
- Autonomy demotion is immediate — a single severe event can drop the system multiple levels.
- The mathematical structure (25:1 asymmetry, logistic gain, exponential penalty) ensures that these principles hold under all conditions.

This "earn it, don't declare it" philosophy contrasts with most existing automation frameworks, where autonomy levels are assigned at design time based on engineering analysis and remain fixed unless manually changed. The NEXUS approach recognizes that a system's trustworthiness can change over time as components age, software is updated, and environmental conditions shift. A system that was trustworthy yesterday may not be trustworthy today, and the trust score reflects this reality.

---

## 12. Open Questions

### 12.1 Can Computational Trust Ever Match Human Trust?

Human trust is a complex, multidimensional, context-sensitive psychological state influenced by emotions, social cues, cultural norms, dispositional factors, and cognitive biases. Computational trust, as implemented in NEXUS and other frameworks, is a deterministic function of observed events. The question of whether computational trust can ever match human trust is therefore really two questions: *Should it?* and *Can it?*

**Should it?** Probably not. Human trust is subject to systematic biases (negativity bias, confirmation bias, availability heuristic) that produce miscalibration. A computational model that faithfully reproduced these biases would be no better than human judgment — and potentially worse, because it would lack the intuitive flexibility that humans use to compensate for their biases.

**Can it?** Not fully, because computational models lack access to the full range of information that humans use to form trust: facial expressions, tone of voice, social context, cultural norms, and emotional states. However, computational models have access to information that humans cannot easily process: exact failure rates, precise temporal patterns, multi-dimensional event classification, and statistical trends. The goal is not to replicate human trust but to provide a *better* trust assessment by combining computational precision with human judgment through appropriate interface design.

### 12.2 How Does Trust Propagate Across a Fleet?

NEXUS's per-subsystem independence prevents trust transfer between subsystems on the same vessel. But what about trust transfer between vessels in a fleet? If Vessel A's steering system demonstrates high reliability, should Vessel B's steering system inherit some of that trust?

The current NEXUS design says no — each vessel's trust scores are computed independently. This is conservative and prevents cascading failures, but it also means that the fleet cannot benefit from collective experience. A potential future extension is a *reputation layer* where fleet-level statistics inform initial trust for new vessels, while per-vessel experience remains the primary trust driver. This would be analogous to Jøsang's trust transitivity operators, applied at the fleet level.

The challenge is designing such a reputation layer without creating new vulnerabilities: if fleet reputation can be manipulated (e.g., by compromising one vessel's event reporting), the entire fleet's trust assessment could be corrupted. NEXUS's current architecture avoids this risk by making trust purely local.

### 12.3 What Happens When Trust and Safety Conflict?

Consider a scenario: a vessel's steering system has been at Level 4 for three months, and a sudden sensor failure drops its trust to Level 2. The operator needs to navigate through a narrow channel and believes that the system is still capable of autonomous steering despite the sensor failure. Should the operator be able to override the trust-based autonomy restriction?

This scenario illustrates a fundamental tension: the trust score reflects statistical evidence about the system's reliability, but the operator may have situation-specific knowledge that the trust score does not capture. The operator might know that the sensor failure is in a non-critical channel and that the system can still navigate safely using redundant sensors. The trust score, based on event data alone, cannot incorporate this contextual knowledge.

NEXUS resolves this tension through the `manual_revocation` event type (severity 1.0, the maximum) and the `operator_disagreement` reset (trust multiplier 0.3). The operator can explicitly increase trust (by continuing to use the system and generating good events) or accept the trust score's assessment and operate at the restricted level. The system does not prevent the operator from using the system at lower autonomy levels — it only restricts the *degree* of autonomy available.

The deeper philosophical question is: who has the final authority over trust — the algorithm or the human? NEXUS's design philosophy is that the *algorithm* sets the ceiling on autonomy (preventing overtrust), while the *human* sets the floor (preventing disuse by choosing to use the system at whatever level is available). This division of authority respects both the mathematical rigor of the trust score and the operator's situational judgment.

### 12.4 Additional Open Questions

1. **Recency weighting:** Should the INCREMENTS framework incorporate exponential decay weighting so that recent events count more than distant ones? Current analysis suggests this would better match human psychology but could introduce oscillation instabilities.

2. **Trust in the trust algorithm:** If operators disagree with the trust score, their trust in the trust system itself may degrade. How should the system handle meta-trust — trust in the trust computation?

3. **Fleet-level trust dynamics:** In a fleet of 100+ vessels, what emergent trust dynamics arise from individual trust score evolution? Can trust "waves" propagate through the fleet?

4. **Adversarial environments:** How should the trust model adapt when bad events may be caused by deliberate attacks rather than system failures?

5. **Long-term trust drift:** Over years of operation, does the trust score remain calibrated, or does it accumulate historical bias that no longer reflects current system reliability?

---

## 13. Synthesis: NEXUS's INCREMENTS Framework

The INCREMENTS trust framework represents a synthesis of six decades of trust research, implemented as a practical, deployable, safety-critical system. Its key contributions to the field are:

1. **Computational formalization of human trust psychology.** The 12-parameter algorithm captures the essential dynamics of human trust — slow gain, fast loss, negativity bias, streak effects, task-specificity — as deterministic mathematical operations suitable for embedded execution.

2. **Structural prevention of overtrust.** The 25:1 asymmetry and equilibrium ceiling guarantees make overtrust mathematically impossible under realistic failure conditions. No amount of event flooding or parameter manipulation can inflate trust above the equilibrium dictated by the actual bad event rate.

3. **Graduated vulnerability acceptance.** The six autonomy levels (L0–L5) provide a precise, actionable mapping from trust score to operational permission, ensuring that the degree of vulnerability acceptance is always proportional to the evidence of trustworthiness.

4. **Per-subsystem independence with fleet coherence.** Each subsystem's trust score is computed independently, preventing cascading failures, while the framework provides mechanisms for fleet-level coordination through shared parameters and cultural deployment profiles.

5. **Formal safety properties.** The INCREMENTS framework provides proofs of fixed-point stability, subsystem independence, adversarial robustness, and equilibrium guarantees — properties that no other computational trust model in the literature offers.

6. **Cultural adaptability.** The framework's configurable parameters enable deployment across diverse cultural contexts while maintaining the same core safety properties.

The INCREMENTS framework is not merely a trust *measurement* tool — it is a trust *governance* system. It does not passively observe trust; it actively regulates autonomy based on demonstrated trustworthiness. In doing so, it operationalizes the central insight of six decades of trust research: **appropriate reliance, not maximum reliance, is the goal.**

This article's treatment of trust psychology — from Rotter's dispositional trust to Lee & See's three bases, from Muir's sigmoid development to Parasuraman's use/misuse framework, from cultural differences to computational models — provides the theoretical foundation for understanding why INCREMENTS looks the way it does. Every parameter, every event type, every autonomy threshold has a basis in the scientific literature reviewed above.

The connection between trust psychology and the philosophy of artificial intelligence is explored further in [[philosophy_of_ai_and_consciousness]]. The relationship between trust and multi-agent communication protocols — how agents that trust each other communicate differently than agents that do not — is examined in [[agent_communication_languages]].

---

## 14. References

1. Asch, S. E. (1946). Forming impressions of personality. *Journal of Abnormal and Social Psychology*, 41(3), 258–290.
2. Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.
3. Bahner, J. E., Hüper, M. D., & Manzey, D. (2008). Misuse of automated decision aids. *International Journal of Human-Computer Studies*, 66(9), 688–699.
4. Baumeister, R. F., Bratslavsky, E., Finkenauer, C., & Vohs, K. D. (2001). Bad is stronger than good. *Review of General Psychology*, 5(4), 323–370.
5. Cabitza, F., Campagner, A., & Balsano, C. (2017). Bridging the 'last mile' gap between AI implementation and operation. *Annals of Translational Medicine*, 5(27).
6. Chen, J., & Terrence, P. I. (2009). Effects of imperfect automation and individual differences on trust and compliance. *Proceedings of the HFES Annual Meeting*, 53, 367–371.
7. Coleman, J. S. (1990). *Foundations of Social Theory*. Harvard University Press.
8. Dasgupta, P. (1988). Trust as a commodity. In *Trust: Making and Breaking Cooperative Relations* (pp. 49–72). Blackwell.
9. Deutsch, M. (1958). Trust and suspicion. *Conflict Resolution*, 2(4), 265–279.
10. Endsley, M. R. (1995). Toward a theory of situation awareness. *Human Factors*, 37(1), 32–64.
11. Endsley, M. R. (2017). Autonomous driving systems: A preliminary naturalistic study. *Proceedings of the HFES Annual Meeting*, 61(1), 1863–1867.
12. Eriksson, A., & Stanton, N. A. (2017). Takeover time in highly automated vehicles. *Human Factors*, 59(4), 689–705.
13. European Commission (2019). *Ethics Guidelines for Trustworthy AI*.
14. Ezer, N., Fisk, A. D., & Rogers, W. A. (2008). More than a trust issue: Age and trust in an intelligent system. *Proceedings of the HFES Annual Meeting*, 52(26), 2035–2039.
15. Fukuyama, F. (1995). *Trust: Social Virtues and the Creation of Prosperity*. Free Press.
16. Gambetta, D. (1988). Can we trust trust? In *Trust: Making and Breaking Cooperative Relations* (pp. 213–237). Blackwell.
17. Goddard, K., Roudsari, A., & Wyatt, J. C. (2012). Automation bias: A systematic review. *JAMIA*, 19(1), 121–127.
18. Glikson, E., & Woolley, A. W. (2020). Human trust in artificial intelligence. *Journal of Behavioral Decision Making*, 33(3), 263–278.
19. Hoff, K. A., & Bashir, M. (2015). Trust in automation: Integrating empirical evidence. *Human Factors*, 57(3), 407–434.
20. Hoffman, G. M., Lee, J. D., Woods, D. D., & Zarnekow, R. (2013). Trust in automation: Lessons from measurement. In *Automation and Human Performance* (pp. 257–274). CRC Press.
21. Hofstede, G. (2001). *Culture's Consequences* (2nd ed.). Sage.
22. Hollnagel, E. (2004). *Barriers and Accident Prevention*. Ashgate.
23. Huang, J., & Nicolau, M. A. (2023). A Bayesian approach to trust modeling in autonomous systems. *IEEE Transactions on Intelligent Transportation Systems*, 24(8), 8231–8244.
24. Huynh, T. D., Jennings, N. R., & Shadbolt, N. R. (2006). An integrated trust and reputation model for open multi-agent systems. *Autonomous Agents and Multi-Agent Systems*, 13(2), 119–154.
25. IMO (2021). MSC 103/23 — Regulatory Scoping Exercise for MASS.
26. Jian, J. Y., Bisantz, A. M., & Drury, C. G. (2000). Foundations for an empirically determined scale of trust in automated systems. *International Journal of Cognitive Ergonomics*, 4(1), 53–71.
27. Jøsang, A., & Pope, S. (2005). Semantic constraints for trust transitivity. *Proceedings of APCCM*, 59–68.
28. Kaber, D. B. (2018). Issues in human-automation interaction modeling. *Ergonomics*, 61(12), 1581–1595.
29. Kamvar, S. D., Schlosser, M. T., & Garcia-Molina, H. (2003). The EigenTrust algorithm for reputation management in P2P networks. *Proceedings of WWW*, 640–651.
30. Kim, J., et al. (2024). Adaptive trust calibration using reinforcement learning. *IEEE Transactions on Robotics*, 40, 1234–1249.
31. Klein, M., et al. (2023). A game-theoretic framework for trust-based decision making. *Autonomous Agents and Multi-Agent Systems*, 37(1), 1–32.
32. Kraus, J., et al. (2021). Trust in autonomous systems: A meta-analysis. *Human Factors*, 63(5), 835–860.
33. Kraus, J., & Schlick, C. (2021). Trust in automation: A review and meta-analysis. *Ergonomics*, 64(12), 1611–1630.
34. Kraus, J., & Schlick, C. (2022). Repairing trust in automation: A meta-analysis. *Human Factors*, 64(2), 301–330.
35. Kumar, N., & Benbasat, I. (2006). The influence of recommendations and consumer reviews. *Information Systems Research*, 17(4), 425–439.
36. Lau, N., et al. (2024). Trust calibration in AI across cultures: A systematic review. *International Journal of Human-Computer Interaction*, 40(2), 1–20.
37. Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50–80.
38. Leveson, N. (2011). *Engineering a Safer World*. MIT Press.
39. Lichtenstein, S., Fischhoff, B., & Phillips, L. D. (1982). Calibration of probabilities. *Judgment Under Uncertainty: Heuristics and Biases*, 306–334.
40. Lu, Z., Hengster, M., & Roetting, M. (2021). Does trust in automated vehicles affect takeover performance? *Transportation Research Part F*, 80, 265–275.
41. Luhmann, N. (1979). *Trust and Power*. Wiley.
42. Lyons, J. B., et al. (2021). Trust in automation and artificial intelligence: An issues paper. *DTIC Document*.
43. Madhavan, P., & Wiegmann, D. A. (2007). Similarities and differences between human–human and human–automation trust. *Proceedings of the HFES Annual Meeting*, 51(4), 284–288.
44. Mayer, R. C., Davis, J. H., & Schoorman, F. D. (1995). An integrative model of organizational trust. *Academy of Management Review*, 20(3), 709–734.
45. Merritt, S. M., & Ilgen, D. R. (2008). Not all trust is created equal. *Proceedings of the HFES Annual Meeting*, 52(21), 1636–1640.
46. Mosier, K. L., et al. (1996). The role of bias in automated decision aids. *Proceedings of the HFES Annual Meeting*, 40, 386–390.
47. Muir, B. M. (1987). Trust in automation: Part I. *Ergonomics*, 37(11), 1905–1922.
48. Muir, B. M. (1994). Trust in automation: Part I. Theoretical issues. *Ergonomics*, 37(11), 1905–1922.
49. Muir, B. M., & Moray, N. (1996). Trust in automation: Part II. Experimental studies. *Ergonomics*, 39(3), 429–460.
50. Oishi, S., et al. (2019). Culture, social expectations, and trust in AI. *Computers in Human Behavior*, 100, 354–361.
51. Ozturk, P., & Lewis, M. (2024). Economic analysis of trust calibration. *JAIR*, 79, 1–38.
52. Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking. *Stanford InfoLab Technical Report*.
53. Pang, J., et al. (2023). Deep learning for trust computation: A survey. *Knowledge-Based Systems*, 260, 110222.
54. Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation. *Human Factors*, 52(3), 381–410.
55. Parasuraman, R., & Riley, V. (1997). Humans and automation: Use, misuse, disuse, abuse. *Human Factors*, 39(2), 230–253.
56. Parasuraman, R., Sheridan, T. B., & Wickens, C. D. (2000). A model for types and levels of human interaction with automation. *IEEE Transactions on SMC*, 30(3), 286–297.
57. Porathe, T., et al. (2023). Human–machine collaboration for autonomous ships. *Proceedings of the IMechE Part M*, 237(1), 3–15.
58. Regan, K., Poupart, P., & Cohen, R. (2006). Bayesian reputation modeling in e-marketplaces. *Proceedings of AAAI*, 1206–1212.
59. Reeves, B., & Nass, C. (1996). *The Media Equation*. Cambridge University Press.
60. Rotter, J. B. (1967). A new scale for the measurement of interpersonal trust. *Journal of Personality*, 35(4), 651–665.
61. Rousseau, D. M., Sitkin, S. B., Burt, R. S., & Camerer, C. (1998). Not so different after all. *Academy of Management Review*, 23(3), 393–404.
62. Ryan, M. (2020). The duty of trustworthiness. *Ethics and Information Technology*, 22(4), 307–317.
63. Sabater, J., & Sierra, C. (2002). Reputation and social network analysis in multi-agent systems. *Proceedings of AAMAS*, 475–482.
64. Sarter, N. B., Woods, D. D., & Billings, C. E. (1997). Automation surprise. In *Handbook of Human Factors and Ergonomics* (pp. 1926–1943). Wiley.
65. Schaefer, K. E. (2013). *The Perception and Measurement of Human-Robot Trust*. PhD Thesis, University of Central Florida.
66. Sheridan, T. B., & Hennessy, R. T. (1984). *Monitoring and Supervisory Control*. Springer.
67. Slovic, P. (1993). Perceived risk, trust, and democracy. *Risk Analysis*, 13(6), 675–682.
68. Sullivan, J. B., & Decker, P. J. (2019). Trust and distrust in human-automation teaming. *Proceedings of the HFES Annual Meeting*, 63(1), 2013–2017.
69. Teacy, W. T. L., Patel, J., Jennings, N. R., & Luck, M. (2006). Travos: Trust and reputation in the context of inaccurate information sources. *Autonomous Agents and Multi-Agent Systems*, 12(2), 183–198.
70. Ullman, D., & Malle, B. F. (2019). Measuring multi-dimensional trust in human-robot interaction. *Proceedings of HRI*, 22–31.
71. Urkowitz, A., Pratt, S., & Parasuraman, R. (2022). A quantitative model of human trust in multiple autonomous agents. *Human Factors*, 64(6), 1112–1128.
72. Wang, Y., & Singh, M. P. (2007). Formal trust model for multiagent systems. *Proceedings of IJCAI*, 1551–1556.
73. Wróbel, K., et al. (2021). Towards autonomous ships: A review of key challenges. *Ocean Engineering*, 231, 109073.
74. Xu, H., et al. (2023). A dynamic trust model for autonomous systems based on Hidden Markov Models. *Reliability Engineering & System Safety*, 238, 109497.
75. Yu, H., & Singh, M. P. (2002). Distributed reputation management for electronic commerce. *Computational Intelligence*, 18(4), 535–549.
76. Zhang, T., et al. (2022). Cross-cultural differences in trust in autonomous vehicles. *Transportation Research Part F*, 86, 1–15.

---

*This article is part of the NEXUS Robotics Platform Knowledge Base. For related articles, see [[philosophy_of_ai_and_consciousness]] for the philosophical foundations of machine consciousness and [[agent_communication_languages]] for trust in multi-agent communication systems.*
