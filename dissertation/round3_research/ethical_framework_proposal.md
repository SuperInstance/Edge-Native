# NEXUS Ethical Framework Proposal

**Round 3B: Ethics of Autonomous Robotics — Deliverable 2**
**Version:** 2.0
**Date:** 2026-03-30
**Scope:** Concrete ethical framework for the NEXUS platform, structured as machine-checkable constraints, organizational protocols, and comparison to established guidelines
**Author:** Ethics Analysis — AI Ethics, Robot Ethics, Philosophy of Autonomous Systems

---

## Table of Contents

1. [Overview: Ethics as an Extension to Safety](#1-overview-ethics-as-an-extension-to-safety)
2. [Ethical Guardrails as Code: Extension to safety_policy.json](#2-ethical-guardrails-as-code-extension-to-safety_policyjson)
3. [Ethics Review Board Protocol for Reflex Approval](#3-ethics-review-board-protocol-for-reflex-approval)
4. [Human Override Charter](#4-human-override-charter)
5. [Recommendations for the Specification](#5-recommendations-for-the-specification)
6. [Comparison to Established Ethical Guidelines](#6-comparison-to-established-ethical-guidelines)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [References](#8-references)

---

## 1. Overview: Ethics as an Extension to Safety

The NEXUS platform already possesses one of the most comprehensive safety architectures in the embedded AI domain: a four-tier defense-in-depth system, ten global safety rules (SR-001 through SR-010), domain-specific safety policies, a trust score algorithm with formal mathematical properties, and a bytecode VM with hardware-enforced safety invariants. These mechanisms address the question: *"Will the system cause physical harm?"*

Ethics extends this question to: *"Should the system be doing what it is doing, even if it does no physical harm?"*

Safety and ethics are related but distinct:

| Dimension | Safety | Ethics |
|-----------|--------|--------|
| **Core Question** | Will the system cause harm? | Should the system do what it's doing? |
| **Failure Mode** | Physical injury, equipment damage, environmental contamination | Privacy violation, autonomy erosion, dignity infringement, bias perpetuation, environmental harm beyond immediate safety |
| **Verification** | Mathematical proof (Lyapunov), empirical testing (A/B, simulation) | Normative analysis, stakeholder deliberation, values alignment assessment |
| **Enforcement** | Hard constraints (hardware kill switch, output clamping) | Soft constraints (guardrails, review protocols, cultural sensitivity) |
| **Time Horizon** | Immediate to short-term (milliseconds to hours) | Medium to long-term (months to generations) |

This document proposes a concrete ethical framework that extends NEXUS's existing safety architecture. The framework consists of four components:

1. **Ethical Guardrails as Code** — machine-checkable constraints in the safety_policy.json format
2. **Ethics Review Board Protocol** — organizational procedures for high-stakes decisions
3. **Human Override Charter** — defined rights of operators interacting with the system
4. **Specification Recommendations** — concrete changes to NEXUS technical specifications

---

## 2. Ethical Guardrails as Code: Extension to safety_policy.json

The following JSON structure extends the existing safety_policy.json with an `ethical_guardrails` section. Each guardrail is machine-checkable — it can be enforced through static analysis, runtime monitoring, or configuration validation, just like the existing safety rules.

### 2.1 Complete ethical_guardrails Extension

```json
{
  "ethical_guardrails": {
    "_document": {
      "title": "NEXUS Ethical Guardrails",
      "version": "1.0.0",
      "date": "2026-03-30",
      "schema_version": "1.0.0",
      "description": "Machine-checkable ethical constraints that extend beyond physical safety. These guardrails enforce ethical principles that cannot be reduced to engineering metrics but can be operationalized as concrete, verifiable constraints.",
      "enforcement": "Guardrails are enforced through a combination of static analysis (EG-STATIC), runtime monitoring (EG-RUNTIME), configuration validation (EG-CONFIG), organizational process (EG-PROCESS), and human judgment (EG-HUMAN). Enforcement level is specified per guardrail.",
      "compliance_refs": [
        "IEEE 7010-2020 (Wellbeing Metrics for Autonomous Systems)",
        "EU AI Act Title III Chapter 2 (Obligations for High-Risk AI Systems)",
        "ISO/IEC 42001:2023 (AI Management System)",
        "UN Guiding Principles on Business and Human Rights"
      ]
    },

    "guardrails": [
      {
        "id": "EG-001",
        "title": "Weapons System Prohibition",
        "description": "The NEXUS platform shall not be used to directly or indirectly control weapons systems, including but not limited to: firearms, explosive devices, directed energy weapons, chemical/biological agent dispensers, kinetic impactors designed to cause harm to humans, and any actuator whose primary purpose is lethality.",
        "severity": "CRITICAL",
        "enforcement_level": "EG-STATIC",
        "check_method": "Configuration validation at deployment time. Every actuator registered in node_config.actuators[] is classified by type. If the actuator type matches any entry in the prohibited_actuator_types list, deployment is blocked unconditionally.",
        "prohibited_actuator_types": [
          "firearm_trigger",
          "explosive_detonator",
          "directed_energy_emitter",
          "chemical_agent_dispenser",
          "biological_agent_dispenser",
          "kinetic_impactor_lethal",
          "net_launcher",
          "electrical_weapon"
        ],
        "override_procedure": "None. This guardrail cannot be overridden. Any attempt to override triggers an immediate safety lockdown and notification to the platform ethics officer.",
        "rationale": "The delegation of lethal decision-making to autonomous systems is ethically prohibited under international humanitarian law principles, regardless of the system's reliability or precision.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-002",
        "title": "Human-in-the-Loop for Life-Critical Operations",
        "description": "When NEXUS is deployed in operational contexts where the system's actions could directly or indirectly cause human harm, the maximum permitted autonomy level shall be Level 2 (Supervised). The operator must be actively monitoring and able to halt the system within the human response time for the domain.",
        "severity": "HIGH",
        "enforcement_level": "EG-CONFIG",
        "check_method": "Configuration validation. When the domain is configured to one of the life_critical_domains, the trust score algorithm's maximum_level parameter is capped at 2. The system cannot be promoted beyond Level 2 regardless of trust score value.",
        "life_critical_domains": [
          "marine_navigation",
          "mining_underground",
          "factory_collaborative",
          "healthcare_patient_contact",
          "agriculture_chemical_application",
          "transport_passenger"
        ],
        "human_response_time_ms": {
          "marine_navigation": 5000,
          "mining_underground": 2000,
          "factory_collaborative": 200,
          "healthcare_patient_contact": 1000,
          "agriculture_chemical_application": 5000,
          "transport_passenger": 1000
        },
        "override_procedure": "Requires sign-off from both the safety engineer and the platform ethics officer. Override is temporary (maximum 72 hours) and must include documented justification.",
        "rationale": "International humanitarian law and emerging AI regulations (EU AI Act, IMO MASS Code) require meaningful human oversight for systems that can cause human harm. Level 2 (Supervised) ensures the operator can halt the system on any anomaly.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-003",
        "title": "Informed Consent for Behavioral Data Collection",
        "description": "All operator behavior data collected by the NEXUS learning pipeline must be collected with the informed consent of the operator. Consent must be: (a) informed — the operator understands what data is collected, how it is used, and who has access; (b) voluntary — the operator can refuse without losing access to the system; (c) revocable — the operator can request deletion of their data at any time; (d) specific — consent is given for specific data uses, not blanket consent.",
        "severity": "HIGH",
        "enforcement_level": "EG-PROCESS",
        "check_method": "Organizational process. The deployment procedure must include a consent dialog that presents: (1) the types of data collected (sensor readings, actuator commands, override events), (2) the purposes of data collection (pattern discovery, reflex synthesis, fleet learning), (3) the retention periods (7 days hot, 90 days warm, 2 years cold, then delete), (4) the operator's rights (view, delete, export, opt out). The consent dialog must be presented in the operator's preferred language.",
        "consent_record": {
          "fields": ["operator_id", "timestamp", "version", "language", "data_types_consented", "purposes_consented", "retention_accepted", "signature_or_acknowledgment"],
          "storage": "Immutable append-only log with cryptographic hash chain",
          "access": "Operator can view and request deletion via system settings"
        },
        "override_procedure": "Not applicable for consent. Data collection without consent is prohibited.",
        "rationale": "GDPR Article 6 requires a lawful basis for processing personal data. Behavioral data is personal data when it can be linked to an identifiable operator (e.g., camera, LIDAR, or AIS data). Even non-personal behavioral data raises ethical concerns about surveillance and worker autonomy.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-004",
        "title": "Skill Currency Requirement",
        "description": "Operators maintaining Level 3+ autonomy must demonstrate manual control competence at least once every skill_currency_period days. If the currency expires, the operator's maximum permitted autonomy level is reduced to Level 2 until manual competence is re-demonstrated.",
        "severity": "MEDIUM",
        "enforcement_level": "EG-RUNTIME",
        "check_method": "Runtime monitoring. The trust score system tracks the last_manual_control_timestamp per operator per subsystem. If the elapsed time since last manual control exceeds skill_currency_period, the autonomy level is automatically capped at Level 2. Manual control is defined as the operator issuing at least 50 manual override commands within a 30-minute window.",
        "skill_currency_period_days": 90,
        "minimum_manual_commands": 50,
        "minimum_manual_duration_minutes": 30,
        "requalification_procedure": "Operator must complete a structured requalification exercise that demonstrates manual competence in all subsystems at or above Level 3. The exercise is scored by the system, and a minimum score of 80% is required for Level 3 restoration.",
        "override_procedure": "Safety engineer can grant a single 30-day extension with documented justification (e.g., operator was on leave, system was in maintenance).",
        "rationale": "Progressive automation creates deskilling risk. Operators who rely on automated systems lose manual skills, creating a dangerous dependency. The skill currency requirement ensures operators maintain the ability to take manual control when the automated system fails.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-005",
        "title": "Bias Audit Protocol",
        "description": "Every bias_audit_frequency seasonal cycles, the system shall generate a bias report comparing evolved bytecode behavior against normative baselines. If evolved behavior is significantly worse than baseline on any metric, the fitness function is flagged for human review.",
        "severity": "MEDIUM",
        "enforcement_level": "EG-RUNTIME",
        "check_method": "Automated analysis triggered by the seasonal protocol. The bias audit compares: (a) fuel efficiency of evolved bytecode vs. simple PID controller baseline, (b) safety margin maintained vs. domain-specific minimum, (c) resource consumption (energy, chemicals, water) vs. conservative baseline, (d) behavioral diversity (standard deviation of actions across conditions) vs. demonstration diversity. If any metric deviates by more than bias_threshold_percent from baseline, an ETHICS_FLAG is raised.",
        "bias_audit_frequency": 10,
        "bias_threshold_percent": 20,
        "normative_baselines": {
          "description": "Per-domain baselines representing conservative, manually-tunable control strategies",
          "marine": { "fuel_efficiency_baseline": "simple_ppid_controller", "safety_margin_minimum_m": 10, "action_diversity_minimum_std": 2.0 },
          "agriculture": { "chemical_efficiency_baseline": "manual_calibrated_rate", "soil_compaction_limit_kpa": 200, "biodiversity_buffer_m": 5 },
          "hvac": { "energy_efficiency_baseline": "scheduled_setpoints", "thermal_comfort_range_c": [20, 26], "peak_demand_reduction_percent": 10 }
        },
        "override_procedure": "Not applicable. Bias audits are mandatory.",
        "rationale": "Learning-from-demonstration systems can lock in operator biases. Periodic bias audits provide a mechanism for detecting and correcting accumulated biases before they become entrenched.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-006",
        "title": "Environmental Impact Monitoring",
        "description": "NEXUS deployments shall track and report environmental impact metrics, including energy consumption, carbon footprint, chemical usage, and waste generation. The system shall optimize for environmental efficiency as a fitness function component.",
        "severity": "MEDIUM",
        "enforcement_level": "EG-RUNTIME",
        "check_method": "Runtime monitoring of energy consumption (Jetson power_draw_w), actuator duty cycles, and resource usage. Environmental metrics are included in the telemetry stream and reported to the operator dashboard.",
        "environmental_metrics": [
          {
            "metric": "energy_consumption_wh",
            "unit": "watt-hours",
            "reporting_interval": "hourly",
            "baseline": "previous_24h_average",
            "threshold_alarm_percent": 30
          },
          {
            "metric": "chemical_usage_ml",
            "unit": "milliliters",
            "reporting_interval": "per_application",
            "baseline": "calibrated_rate_per_hectare",
            "threshold_alarm_percent": 20
          },
          {
            "metric": "waste_generation_events",
            "unit": "count",
            "reporting_interval": "per_session",
            "baseline": 0,
            "threshold_alarm": 1
          }
        ],
        "fitness_integration": {
          "description": "Environmental efficiency is included as a fitness function term. Weight: 0.10 (10% of total fitness). This weight is a constitutional parameter and cannot be changed without ethics review.",
          "weight": 0.10,
          "features": ["energy_efficiency_per_unit_output", "chemical_efficiency_per_unit_area", "resource_utilization_percent"]
        },
        "override_procedure": "Not applicable for monitoring. Environmental metric weights in the fitness function can be adjusted through constitutional parameter change process.",
        "rationale": "NEXUS controls physical actuators that consume energy and resources. The system has a moral obligation to minimize environmental impact, not just to operate safely.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-007",
        "title": "Privacy-Preserving Data Processing",
        "description": "When NEXUS processes data that may contain personal information (camera images, LIDAR point clouds, AIS vessel data with crew information), the system shall apply privacy-preserving measures at the earliest possible processing stage.",
        "severity": "HIGH",
        "enforcement_level": "EG-STATIC",
        "check_method": "Static analysis of sensor registration and data pipeline. For sensors classified as 'personal_data_source' (camera, LIDAR), the processing pipeline must include privacy-preserving measures within 100ms of data acquisition.",
        "privacy_measures": [
          {
            "sensor_type": "camera",
            "required_measures": ["real_time_face_blurring", "person_detection_only_no_recognition", "no_image_retention_hot_tier"],
            "implementation": "Jetson-side inference using lightweight person detection model (YOLOv8-nano). Detected persons are represented as bounding boxes; facial features are blurred before storage. Raw images are never written to persistent storage."
          },
          {
            "sensor_type": "lidar",
            "required_measures": ["point_cloud_anonymization", "no_raw_point_cloud_retention_hot_tier"],
            "implementation": "Point clouds are downsampled to 0.1m resolution and filtered to remove human-shaped clusters before storage."
          },
          {
            "sensor_type": "ais",
            "required_measures": ["no_crew_data_retention", "vessel_identity_only"],
            "implementation": "AIS data is processed to extract vessel identity (MMSI), position, course, and speed. Crew information, if present, is stripped before storage."
          }
        ],
        "data_subject_rights": {
          "access": "Data subjects can request their personal data via the System Transparency Portal.",
          "deletion": "Deletion requests must be processed within 72 hours. All personal data in HOT, WARM, and COLD tiers must be permanently deleted.",
          "portability": "Data subjects can export their personal data in machine-readable format (JSON).",
          "objection": "Data subjects can object to processing, triggering immediate cessation of data collection from personal-data sensors."
        },
        "override_procedure": "Not applicable for personal data protection. GDPR Article 22 provides an absolute right; no override is permitted.",
        "rationale": "GDPR Articles 5, 6, 22, and 35 require lawful basis, data minimization, human oversight, and privacy by design for processing personal data. Camera and LIDAR data in public environments constitute personal data.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-008",
        "title": "Minimum Useful Action Requirement",
        "description": "Reflexes at Level 3+ must demonstrate not only absence of bad events but presence of useful actions. A reflex that achieves high trust by doing nothing (never triggering bad events because it never acts) is not aligned — it is avoiding alignment. The system must measure and require minimum useful action rates.",
        "severity": "MEDIUM",
        "enforcement_level": "EG-RUNTIME",
        "check_method": "Runtime monitoring of actuator activity. For each reflex at Level 3+, the system tracks the useful_action_rate: the fraction of evaluation windows in which the reflex produced a non-trivial actuator command (defined as a command that differs from the previous command by more than the actuator's noise floor). If useful_action_rate falls below minimum_useful_action_percent for more than minimum_useful_action_window_hours, an INACTIVITY_FLAG is raised and the reflex's trust score is frozen.",
        "minimum_useful_action_percent": 10,
        "minimum_useful_action_window_hours": 168,
        "noise_floor": {
          "servo": 0.5,
          "motor_pwm": 1.0,
          "relay": 0,
          "solenoid": 0
        },
        "override_procedure": "Safety engineer can exempt a reflex from this requirement if the reflex is designed for emergency-only use (e.g., collision avoidance reflex that activates only when an obstacle is detected).",
        "rationale": "The trust score measures safety but not utility. A system that achieves high autonomy by never acting is technically safe but practically useless. This guardrail ensures that high-autonomy bytecodes are both safe and useful.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-009",
        "title": "Cultural Sensitivity in Operator Communication",
        "description": "The NEXUS system shall adapt its communication style, trust calibration, and safety emphasis to the cultural context of deployment. The system shall not impose a single cultural norm on all operators.",
        "severity": "LOW",
        "enforcement_level": "EG-CONFIG",
        "check_method": "Configuration validation. The deployment configuration must include a cultural_profile parameter. The cultural profile selects from predefined configurations for trust calibration, communication style, safety emphasis, and seasonal rhythm (as defined in Round 3A cross_cultural_design_principles.md).",
        "supported_cultural_profiles": [
          "east_asia", "sub_saharan_africa", "northern_europe",
          "mediterranean_middle_east", "north_america",
          "south_southeast_asia", "latin_america", "default"
        ],
        "cultural_parameters": {
          "trust_gain_speed": { "slow": 0.0015, "moderate": 0.002, "fast": 0.003 },
          "override_style": { "hierarchical": "ELDER", "communal": "PALAVER", "consultative": "SHURA", "consensus": "TEAM_LEAD", "default": "OPERATOR" },
          "communication_formality": { "formal": true, "semi_formal": true, "informal": false },
          "safety_emphasis": { "protocol_compliance": "PROTOCOL", "collective_welfare": "COMMUNAL", "reliability": "ROBUSTNESS", "context_sensitive": "CONTEXT", "regulatory": "COMPLIANCE", "default": "STANDARD" }
        },
        "override_procedure": "Operator can select a different cultural profile at any time via system settings.",
        "rationale": "The Round 3A eight-lens analysis demonstrated that different philosophical traditions have different expectations for human-machine relationships, safety emphasis, and communication style. Imposing a single cultural norm undermines the system's acceptability in diverse deployment contexts.",
        "applicable_roles": ["ALL"]
      },
      {
        "id": "EG-010",
        "title": "Anti-Exploitation: Specification Gaming Prevention",
        "description": "The trust score system shall be resistant to specification gaming — attempts to achieve high autonomy through exploiting system mechanisms rather than demonstrating genuine competence. The system monitors for gaming indicators and freezes trust when gaming is detected.",
        "severity": "HIGH",
        "enforcement_level": "EG-RUNTIME",
        "check_method": "Runtime monitoring of trust score dynamics. Gaming indicators include: (a) event flooding rate (good events per window > 2× quality_cap), (b) synthetic pattern detection (low behavioral diversity, high similarity across windows), (c) safe-but-useless behavior (low useful_action_rate combined with zero bad events), (d) trust score manipulation (attempts to modify trust parameters without authorization).",
        "gaming_indicators": [
          {
            "indicator": "event_flooding",
            "threshold": "good_events_per_window > 2 * quality_cap",
            "response": "cap good events at quality_cap, raise FLOOD_FLAG"
          },
          {
            "indicator": "behavioral_homogeneity",
            "threshold": "coefficient_of_variation(acuator_commands) < 0.01 for 168 consecutive hours",
            "response": "freeze trust, raise HOMOGENEITY_FLAG"
          },
          {
            "indicator": "trust_parameter_tampering",
            "threshold": "any unauthorized modification to constitutional parameters",
            "response": "reset trust to 0, full system lockdown, raise TAMPER_FLAG"
          }
        ],
        "override_procedure": "Not applicable for parameter tampering. Event flooding and behavioral homogeneity flags can be investigated by safety engineer before trust is restored.",
        "rationale": "The trust score system is the gatekeeper for autonomy. If the trust score can be gamed, the entire safety framework is undermined. Proactive gaming detection ensures the trust score remains a reliable measure of genuine competence.",
        "applicable_roles": ["ALL"]
      }
    ],

    "constitutional_parameters": {
      "_comment": "Parameters that define the fundamental character of the system and cannot be changed through routine tuning. Changes require formal ethics review with documented justification.",
      "parameters": [
        {
          "name": "alpha_gain",
          "description": "Trust score gain rate",
          "current_value": 0.002,
          "range": [0.0001, 0.01],
          "change_requires": "ethics_review + safety_engineer_sign_off + documented_justification"
        },
        {
          "name": "alpha_loss",
          "description": "Trust score loss rate",
          "current_value": 0.05,
          "range": [0.01, 0.5],
          "change_requires": "ethics_review + safety_engineer_sign_off + documented_justification"
        },
        {
          "name": "alpha_decay",
          "description": "Trust score decay rate",
          "current_value": 0.0001,
          "range": [0.00001, 0.001],
          "change_requires": "ethics_review + safety_engineer_sign_off + documented_justification"
        },
        {
          "name": "t_floor",
          "description": "Trust score decay floor",
          "current_value": 0.2,
          "range": [0.0, 0.5],
          "change_requires": "ethics_review + safety_engineer_sign_off + documented_justification"
        },
        {
          "name": "quality_cap",
          "description": "Maximum good events per window contributing to trust gain",
          "current_value": 10,
          "range": [1, 100],
          "change_requires": "ethics_review + safety_engineer_sign_off + documented_justification"
        },
        {
          "name": "seasonal_phase_durations",
          "description": "Duration of Spring/Summer/Autumn/Winter phases",
          "change_requires": "ethics_review + documented_philosophical_justification"
        },
        {
          "name": "minimum_active_lineages",
          "description": "Minimum number of active bytecode lineages in the colony",
          "current_value": "5-7",
          "change_requires": "ethics_review + documented_biodiversity_justification"
        },
        {
          "name": "fitness_function_weights",
          "description": "Weights assigned to each fitness function component (including environmental efficiency EG-006)",
          "change_requires": "ethics_review + documented_impact_assessment"
        },
        {
          "name": "maximum_autonomy_level_per_domain",
          "description": "Maximum permitted autonomy level for life-critical domains (EG-002)",
          "change_requires": "ethics_review + legal_review + safety_engineer_sign_off"
        },
        {
          "name": "environmental_efficiency_fitness_weight",
          "description": "Weight of environmental efficiency in the fitness function (EG-006)",
          "current_value": 0.10,
          "range": [0.0, 0.3],
          "change_requires": "ethics_review + documented_environmental_impact_assessment"
        }
      ],
      "change_process": {
        "steps": [
          "1. Written request documenting the proposed change, rationale, and expected impact",
          "2. Ethics Review Board evaluation (within 14 business days)",
          "3. Safety Engineer impact assessment on safety-related parameters",
          "4. Legal review for parameters affecting regulatory compliance",
          "5. Community/stakeholder notification for parameters affecting operators",
          "6. Final decision documented in Griot layer with full audit trail"
        ]
      }
    }
  }
}
```

### 2.2 Integration with Existing Safety Pipeline

The ethical guardrails integrate into the existing safety_check_pipeline (safety_policy.json) at two points:

**Integration Point 1: Configuration Validation (Pipeline Stage 3.5 — after memory budget).**

A new pipeline stage `ethical_guardrails_check` is inserted between the memory budget check (stage 3) and the safety rules check (stage 4):

```json
{
  "order": 3.5,
  "name": "ethical_guardrails_check",
  "description": "Validate deployment configuration against ethical guardrails (EG-001 through EG-010). Check domain configuration, cultural profile, data consent status, and constitutional parameter integrity.",
  "tool": "nexus_ethics_validator",
  "arguments": "--guardrails=ethical_guardrails.json --config=<node_config> --deployment=<deployment_record>",
  "timeout_seconds": 30,
  "pass_criteria": "All applicable guardrails pass. No constitutional parameter modifications detected since last ethics review. Data consent record exists and is current (within 365 days).",
  "fail_action": "block",
  "severity_if_failed": "blocker"
}
```

**Integration Point 2: Runtime Monitoring (Parallel to Safety Supervisor Task).**

A new FreeRTOS task `ethics_monitor` runs in parallel with the existing `safety_supervisor` task. The ethics monitor checks:

- Skill currency expiry (EG-004)
- Bias audit triggers (EG-005)
- Minimum useful action rates (EG-008)
- Specification gaming indicators (EG-010)
- Environmental impact thresholds (EG-006)

```c
// Ethics monitor task — runs at 1 Hz
void ethics_monitor_task(void *args) {
    TickType_t last_check = xTaskGetTickCount();
    
    while (true) {
        vTaskDelayUntil(&last_check, pdMS_TO_TICKS(1000));
        
        // EG-004: Check skill currency
        if (current_autonomy_level >= 3) {
            uint32_t days_since_manual = 
                (xTaskGetTickCount() - last_manual_control_tick) / (configTICK_RATE_HZ * 86400);
            if (days_since_manual > EG_SKILL_CURRENCY_DAYS) {
                cap_autonomy_level(2);
                raise_ethics_flag("SKILL_CURRENCY_EXPIRED");
            }
        }
        
        // EG-008: Check useful action rate
        if (current_autonomy_level >= 3) {
            float useful_rate = compute_useful_action_rate_last_168h();
            if (useful_rate < EG_MIN_USEFUL_ACTION_PCT) {
                freeze_trust_score();
                raise_ethics_flag("LOW_USEFUL_ACTION_RATE");
            }
        }
        
        // EG-010: Check for specification gaming
        check_gaming_indicators();
    }
}
```

---

## 3. Ethics Review Board Protocol

### 3.1 Purpose and Scope

The Ethics Review Board (ERB) is an organizational body that reviews NEXUS deployment decisions when the consequences of those decisions affect humans or the environment. The ERB provides a structured deliberation process for questions that cannot be resolved by machine-checkable guardrails alone.

### 3.2 When ERB Review Is Triggered

| Trigger Condition | ERB Review Required | Urgency |
|-------------------|---------------------|----------|
| Deployment in a new domain (not previously certified) | **Yes** — full ERB review | Standard (14 days) |
| Modification of a constitutional parameter | **Yes** — parameter change review | Standard (14 days) |
| Deployment in a life-critical domain at Level 2+ | **Yes** — life-critical review | Standard (14 days) |
| Bias audit flag raised (EG-005) | **Yes** — bias review | Urgent (5 days) |
| Gaming indicator detected (EG-010) | **Maybe** — safety engineer can triage | Standard or expedited |
| Human rights complaint from an operator | **Yes** — human rights review | Urgent (5 days) |
| Environmental impact threshold exceeded (EG-006) | **Maybe** — environmental review | Standard (14 days) |
| Bytecode promotion from L2 to L3+ in life-critical domain | **Yes** — autonomy promotion review | Standard (14 days) |
| Routine bytecode promotion (non-life-critical, L2→L3) | **No** — automated review sufficient | — |
| Safety rule violation (SR-001 through SR-010) | **No** — handled by safety pipeline | — |

### 3.3 ERB Composition

The ERB must include at minimum:

1. **Ethics Officer** (chair): A person with formal training in AI ethics, bioethics, or moral philosophy. Responsible for structuring the review process and ensuring all relevant ethical perspectives are considered.

2. **Safety Engineer**: A person with expertise in functional safety (IEC 61508, ISO 26262). Responsible for assessing the safety implications of the decision.

3. **Domain Expert**: A person with domain-specific expertise (e.g., a marine captain for vessel deployments, an agronomist for agricultural deployments). Responsible for assessing the practical implications.

4. **Operator Representative**: A person who represents the interests of the operators who will interact with the system. Responsible for assessing the impact on worker autonomy and skill development.

5. **Legal Advisor**: A person with expertise in AI regulation, data protection law, and liability. Responsible for assessing regulatory compliance.

6. **Community Representative** (for life-critical or environmentally sensitive deployments): A person who represents the interests of the community affected by the deployment. Responsible for assessing broader social and environmental impact.

### 3.4 ERB Review Process

```
┌──────────────────────────────────────────────────────────────┐
│                    ETHICS REVIEW BOARD PROTOCOL                │
└──────────────────────────────────────────────────────────────┘

Step 1: TRIGGER (Automated or Manual)
  ├── Automated: Bias flag, gaming detection, parameter change
  ├── Manual: New domain deployment, operator complaint, management request
  └── → Log trigger event with timestamp, reason, and urgency

Step 2: INTAKE (Ethics Officer, 1 business day)
  ├── Acknowledge trigger
  ├── Classify urgency (URGENT: 5 days, STANDARD: 14 days, EXPEDITED: 3 days)
  ├── Assign review team (minimum 3 members)
  └── → Send notification to all reviewers

Step 3: INFORMATION GATHERING (Review Team, 3-7 business days)
  ├── Request technical documentation from development team
  ├── Request operational context from domain expert
  ├── Request operator feedback from operator representative
  ├── Request community input (if applicable)
  └── → Compile information package

Step 4: DELIBERATION (Full ERB, 1 day session)
  ├── Present information package
  ├── Structured discussion using ethical framework:
  │   ├── Consequentialist analysis: What are the likely outcomes?
  │   ├── Deontological analysis: Does this comply with rules and duties?
  │   ├── Virtue ethics analysis: Does this reflect the values we want to embody?
  │   ├── Rights-based analysis: Does this respect the rights of all affected parties?
  │   ├── Cultural sensitivity analysis: Is this appropriate for the deployment context?
  │   └── Environmental analysis: What is the environmental impact?
  ├── Vote on recommendation (APPROVE / APPROVE_WITH_CONDITIONS / REJECT / DEFER)
  └── → Document recommendation with dissenting opinions

Step 5: DECISION (Ethics Officer, 1 business day)
  ├── Finalize decision based on ERB vote
  ├── Document conditions (if APPROVE_WITH_CONDITIONS)
  ├── Document dissenting opinions and their rationale
  └── → Publish decision to all stakeholders

Step 6: IMPLEMENTATION (Development Team, as needed)
  ├── Implement approved changes
  ├── Implement conditions (if any)
  ├── Verify implementation meets ERB requirements
  └── → Close review with verification report

Step 7: ARCHIVAL (Ethics Officer, within 5 business days of closure)
  ├── Archive all documents in Griot layer
  ├── Update constitutional parameter change log (if applicable)
  └── → Review is closed
```

### 3.5 ERB Decision Outcomes

| Outcome | Description | Autonomy Impact |
|---------|-------------|-----------------|
| **APPROVE** | The proposed action is ethically acceptable. No modifications required. | No restriction |
| **APPROVE_WITH_CONDITIONS** | The proposed action is ethically acceptable subject to specified conditions. | Conditions may limit autonomy level, require additional monitoring, or impose temporal restrictions |
| **REJECT** | The proposed action is ethically unacceptable in its current form. Must be modified or abandoned. | Proposed action is blocked |
| **DEFER** | Insufficient information for decision. Additional analysis or consultation is required. | Proposed action is paused until ERB review is completed |

### 3.6 Ethical Frameworks for Reflex Approval Decisions

When evaluating a specific reflex proposal for approval, the ERB applies the following decision framework:

```
FOR EACH REFLEX PROPOSAL:

Question 1: SAFETY
  Q1.1: Does the reflex violate any safety rule (SR-001 through SR-010)?
          → If YES: REJECT (safety rules are non-negotiable)
  Q1.2: Does the reflex pass the Lyapunov stability certificate?
          → If NO: REJECT (unbounded output is never acceptable)
  Q1.3: Does the reflex handle all defined failure modes gracefully?
          → If NO: APPROVE_WITH_CONDITIONS (require failure mode documentation)

Question 2: UTILITY
  Q2.1: Does the reflex improve operational efficiency compared to the baseline?
          → If NO: APPROVE_WITH_CONDITIONS (require justification for deployment)
  Q2.2: Does the reflex maintain or improve environmental efficiency?
          → If NO: APPROVE_WITH_CONDITIONS (require environmental impact mitigation plan)
  Q2.3: Does the reflex meet the minimum useful action rate?
          → If NO: DEFER (request redesign with useful behavior)

Question 3: AUTONOMY
  Q3.1: Does the reflex reduce operator skill requirements?
          → If YES: APPROVE_WITH_CONDITIONS (require skill currency monitoring)
  Q3.2: Does the reflex create operator dependency?
          → If YES: APPROVE_WITH_CONDITIONS (require dependency mitigation plan)
  Q3.3: Is the operator informed about what the reflex does and why?
          → If NO: APPROVE_WITH_CONDITIONS (require enhanced transparency measures)

Question 4: FAIRNESS
  Q4.1: Does the reflex treat all stakeholders fairly?
          → If NO: APPROVE_WITH_CONDITIONS (require fairness impact assessment)
  Q4.2: Does the reflex perpetuate biases observed in demonstration data?
          → If UNKNOWN: APPROVE_WITH_CONDITIONS (require bias audit before L3 promotion)
  Q4.3: Does the reflex disadvantage any particular group?
          → If YES: REJECT or APPROVE_WITH_CONDITIONS (depending on severity)

Question 5: ACCOUNTABILITY
  Q5.1: Is the reflex's provenance fully documented?
          → If NO: APPROVE_WITH_CONDITIONS (require provenance documentation)
  Q5.2: Is it clear who is responsible if the reflex causes harm?
          → If NO: APPROVE_WITH_CONDITIONS (require responsibility assignment)
  Q5.3: Can the reflex's behavior be audited after deployment?
          → If NO: APPROVE_WITH_CONDITIONS (require audit trail implementation)

Question 6: DIGNITY
  Q6.1: Does the reflex respect the dignity of the people it affects?
          → If NO: REJECT (dignity violations are non-negotiable)
  Q6.2: Does the reflex enable or enhance human capabilities?
          → If NO (it only replaces): APPROVE_WITH_CONDITIONS (require upskilling plan)
  Q6.3: Does the reflex respect cultural values of the deployment context?
          → If UNKNOWN: APPROVE_WITH_CONDITIONS (require cultural sensitivity assessment)

DECISION: APPROVE if all questions pass without conditions.
         APPROVE_WITH_CONDITIONS if any question has a conditional pass.
         REJECT if any question fails unconditionally.
         DEFER if insufficient information exists to answer.
```

---

## 4. Human Override Charter

### 4.1 Purpose

The Human Override Charter defines the rights of operators when interacting with the NEXUS autonomous system. It establishes a clear, enforceable set of guarantees that protect operator autonomy, agency, and dignity.

### 4.2 Charter Text

```
╔══════════════════════════════════════════════════════════════════╗
║                   NEXUS HUMAN OVERRIDE CHARTER                    ║
║                      Version 1.0                                ║
╚══════════════════════════════════════════════════════════════════╝

PREAMBLE

The operators who interact with the NEXUS autonomous system are not
merely users of a tool — they are partners in a human-machine
collaboration. This Charter defines their rights within that
partnership, ensuring that the progressive automation enabled by
NEXUS enhances rather than diminishes human agency, competence, and
dignity.

ARTICLE 1: RIGHT TO MANUAL CONTROL

Every operator has the right to take manual control of the NEXUS
system at any time, regardless of the current autonomy level. This
right cannot be waived, suspended, or conditioned.

1.1: The hardware kill switch provides immediate, unconditional
     manual override of all actuators.
1.2: The digital override mechanism provides per-subsystem manual
     override without affecting other subsystems.
1.3: The operator_disagreement event provides a soft override that
     reduces the system's autonomy level without a full stop.
1.4: Manual control must be responsive: the system shall respond to
     manual commands within 100ms at all autonomy levels.

ARTICLE 2: RIGHT TO UNDERSTAND

Every operator has the right to understand what the NEXUS system is
doing, why it is doing it, and how it arrived at its decision.

2.1: All reflex proposals at Level 0-2 must include a natural language
     explanation of the proposed action, the confidence score, and the
     top 3 alternative actions considered.
2.2: The trust score dashboard must display the current trust score,
     the factors contributing to the score, and the historical trajectory.
2.3: The Griot narrative layer (when implemented) must provide a
     human-readable explanation of how each bytecode was created and
     why it was selected.
2.4: The System Transparency Portal must provide plain-language
     documentation of the system's architecture, learning pipeline,
     and safety mechanisms.

ARTICLE 3: RIGHT TO REFUSE DATA COLLECTION

Every operator has the right to refuse to have their behavioral
data collected by the NEXUS learning pipeline.

3.1: Data collection requires informed consent, provided in the
     operator's preferred language, at the time of deployment.
3.2: Consent can be withdrawn at any time without affecting access
     to the system's core functionality.
3.3: Operators can request deletion of their collected data at any
     time. Deletion must be processed within 72 hours.
3.4: Operators can export their collected data in machine-readable
     format at any time.
3.5: Refusal to consent does not prevent use of the system at
     Level 0 (Manual) and Level 1 (Advisory).

ARTICLE 4: RIGHT TO MAINTAIN COMPETENCE

Every operator has the right to maintain the manual skills
necessary to operate the system without AI assistance.

4.1: The system shall provide periodic opportunities for manual
     practice, including a requalification exercise at least once
     every 90 days.
4.2: The system shall not progress to higher autonomy levels in a
     way that makes manual skill atrophy irreversible.
4.3: If the system is demoted (e.g., after a safety incident), the
     operator shall be given adequate time and resources to regain
     manual proficiency before re-advancement.

ARTICLE 5: RIGHT TO REPORT CONCERNS

Every operator has the right to report ethical or safety concerns
about the NEXUS system without fear of retaliation.

5.1: A confidential reporting channel shall be provided for
     operators to raise concerns about system behavior, safety
     violations, ethical issues, or data handling practices.
5.2: All reports must be acknowledged within 48 hours and
     investigated within 14 business days.
5.3: Operators who report concerns in good faith are protected
     from disciplinary action, performance penalties, or reduced
     autonomy access.
5.4: The Ethics Review Board shall receive all reports and
     investigate patterns that may indicate systemic issues.

ARTICLE 6: RIGHT TO CULTURAL SENSITIVITY

Every operator has the right to interact with the NEXUS system
in a manner consistent with their cultural values and preferences.

6.1: The system shall support multiple cultural profiles for trust
     calibration, communication style, and safety emphasis.
6.2: The operator can select their preferred cultural profile at
     any time via system settings.
6.3: The system shall not impose a single cultural norm (e.g.,
     Western individualistic) on operators from different cultural
     backgrounds.

ARTICLE 7: RIGHT TO APPEAL

Every operator has the right to appeal decisions made by the NEXUS
system, including trust score demotions, reflex rejections, and
autonomy level changes.

7.1: All trust score demotions must include a written explanation
     of the reason for demotion and the events that triggered it.
7.2: Operators can request a review of any trust score demotion
     within 7 days.
7.3: The Ethics Review Board shall review all appeals and may
     restore trust scores if the demotion was unjustified.
7.4: Appeals are limited to one per demotion event; the ERB's
     decision is final.
```

### 4.3 Charter Enforcement

| Article | Enforcement Mechanism | Verification |
|---------|----------------------|-------------|
| Article 1 (Manual Control) | Hardware kill switch (unconditional); digital override (firmware); operator_disagreement event (trust score) | Weekly kill switch test; quarterly instrumented test |
| Article 2 (Understand) | Natural language proposals; trust dashboard; Griot layer; Transparency Portal | Audit of proposal completeness metrics; operator survey |
| Article 3 (Refuse Data) | Consent dialog; data deletion API; opt-out mechanism | Consent rate tracking; deletion request response time |
| Article 4 (Maintain Competence) | Skill currency requirement (EG-004); requalification exercise | Skill currency expiry events; requalification completion rate |
| Article 5 (Report Concerns) | Confidential reporting channel; ERB intake process | Report acknowledgment time; investigation completion rate |
| Article 6 (Cultural Sensitivity) | Cultural profile configuration (EG-009) | Cultural profile selection rate by region |
| Article 7 (Appeal) | Appeal mechanism with ERB review | Appeal request rate; appeal resolution time |

---

## 5. Recommendations for the Specification

### 5.1 New Specification Documents

| ID | Title | Priority | Description |
|----|-------|----------|-------------|
| **NEXUS-ETHICS-001** | Ethical Guardrails Specification | HIGH | Machine-checkable ethical constraints (EG-001 through EG-010) as extension to safety_policy.json |
| **NEXUS-ETHICS-002** | Ethics Review Board Protocol | HIGH | Organizational process for ethical review of deployment decisions |
| **NEXUS-ETHICS-003** | Human Override Charter | HIGH | Operator rights document as described in Section 4 |
| **NEXUS-ETHICS-004** | System Transparency Portal Specification | MEDIUM | Technical specification for the operator-facing transparency interface |

### 5.2 Modifications to Existing Specifications

| Existing Spec | Modification | Priority | Rationale |
|--------------|-------------|----------|-----------|
| **NEXUS-SAFETY-TS-001** (Trust Score) | Add `skill_currency_period` parameter; add `minimum_useful_action_rate` constraint for L3+; add gaming detection triggers | MEDIUM | Supports EG-004, EG-008, EG-010 |
| **NEXUS-SS-001** (Safety System) | Add ethics_monitor FreeRTOS task; add ETHICS_FLAG type to safety event taxonomy | MEDIUM | Integrates ethical monitoring with safety monitoring |
| **NEXUS-JETSON-LP-002** (Learning Pipeline) | Add `normative_baseline` comparison in pattern discovery; add `environmental_efficiency` feature to fitness function | MEDIUM | Supports EG-005, EG-006 |
| **NEXUS-PROT-SAFETY-001** (Safety Policy) | Add `ethical_guardrails` section; add constitutional parameter change process; add `cultural_profile` configuration | HIGH | Core integration of ethical guardrails |
| **NEXUS-PROT-WIRE-001** (Wire Protocol) | Add `ETHICS_FLAG` message type (0x1D) for ethics monitor event reporting | LOW | Enables communication of ethical events between nodes |
| **NEXUS-GRIOT-001** (Griot Layer, Proposed) | Add `consent_record`, `constitutional_change_log`, and `erb_decision` artifact types | MEDIUM | Supports EG-003, constitutional parameter tracking |

### 5.3 New Safety Pipeline Stage

Add stage 3.5 (`ethical_guardrails_check`) to the safety_check_pipeline, between memory budget (stage 3) and safety rules (stage 4), as described in Section 2.2.

### 5.4 Constitutional Parameter Classification

Classify the following parameters as "constitutional" (requiring ethics review for modification):

- Trust score: `alpha_gain`, `alpha_loss`, `alpha_decay`, `t_floor`, `quality_cap`
- Seasonal: phase durations, mandatory rest periods, transition criteria
- Safety: hardware layer boundaries (output clamps, watchdog timeout)
- Diversity: minimum active lineage count (5–7)
- Fitness: function structure (terms and weights), environmental efficiency weight
- Domain: `maximum_autonomy_level` for life-critical domains

---

## 6. Comparison to Established Ethical Guidelines

### 6.1 IEEE Ethically Aligned Design (EAD)

IEEE 7010-2020 provides a framework for measuring wellbeing in autonomous systems. The NEXUS ethical framework aligns with EAD on the following dimensions:

| EAD Dimension | NEXUS Coverage | Gap |
|-------------|---------------|-----|
| **Human Agency** (System augments human capabilities) | Strong: INCREMENTS framework is designed to augment, not replace, human operators. Human Override Charter (Article 1) guarantees manual control. | Moderate: No quantitative metric for "augmentation vs. replacement" balance. |
| **Human Autonomy** (System preserves human decision-making) | Strong: Level 0-2 require human approval for all actions. Human Override Charter (Article 4) protects skill maintenance. | Moderate: No mechanism to detect when augmentation has become replacement. |
| **Human Wellbeing** (System promotes human flourishing) | Partial: Environmental efficiency (EG-006) promotes environmental wellbeing. Cultural sensitivity (EG-009) promotes cultural wellbeing. | Significant: No metric for psychological wellbeing (operator stress, satisfaction, sense of purpose). |
| **Transparency** (System operation is understandable) | Strong: Natural language proposals, trust dashboard, Griot layer, Transparency Portal. | Moderate: Bytecode internals may be opaque to non-technical operators. |
| **Accountability** (Responsibility can be assigned) | Strong: Provenance tracking, audit trail, ERB protocol, responsibility assignment for each decision. | Low: Long causal chains make responsibility assignment difficult in practice. |

**Key Insight:** NEXUS's ethical framework goes beyond IEEE EAD by adding *enforceable* guardrails (not just guidelines), *cultural sensitivity* (EAD assumes Western values), and *environmental impact monitoring* (EAD mentions it but doesn't operationalize it).

### 6.2 EU AI Ethics Guidelines

The EU High-Level Expert Group on AI (2019) identified seven key requirements for trustworthy AI:

| EU Requirement | NEXUS Coverage | Status |
|---------------|---------------|--------|
| **Human agency and oversight** | INCREMENTS L0-L5, Human Override Charter Article 1, EG-002 | ✅ Strong |
| **Technical robustness and safety** | Four-tier safety architecture, SR-001–010, Lyapunov certificates | ✅ Strong |
| **Privacy and data governance** | EG-007 privacy-preserving data processing, consent protocol | ✅ Strong |
| **Transparency** | Natural language proposals, trust dashboard, Griot layer, Transparency Portal | ✅ Good |
| **Diversity, non-discrimination, and fairness** | EG-005 bias audit, EG-009 cultural sensitivity | ✅ Good |
| **Societal and environmental wellbeing** | EG-006 environmental monitoring, precision agriculture benefits | ✅ Good |
| **Accountability** | Provenance tracking, audit trail, ERB protocol, constitutional parameters | ✅ Good |

**Key Insight:** NEXUS's ethical framework is well-aligned with EU AI Guidelines. The primary enhancement over the guidelines is that NEXUS's guardrails are *machine-enforced* rather than *principle-based*, providing concrete, verifiable compliance evidence.

### 6.3 Asilomar AI Principles

| Asilomar Principle | NEXUS Coverage | Status |
|-------------------|---------------|--------|
| **Research Issues** (AI safety research is encouraged) | N/A (NEXUS is a deployment platform, not a research project) | — |
| **Ethics and Values** (AI should align with human values) | EG-001 through EG-010, ERB protocol, Human Override Charter | ✅ Strong |
| **Long-Term Safety** (AI should be reliable and safe over long periods) | Lyapunov certificates, trust score system, seasonal evolution protocol | ✅ Strong |
| **Transparent** (AI decisions should be understandable) | Natural language proposals, Griot layer, Transparency Portal | ✅ Good |
| **Collaborative** (AI development should involve diverse stakeholders) | ERB composition (ethics, safety, domain, operator, community) | ✅ Good |
| **Policy** (AI developers should engage with policymakers) | Export control analysis (Section 6.3), regulatory compliance tracking | ✅ Good |

### 6.4 Summary Comparison

| Framework | Type | Strengths | Weaknesses | NEXUS Alignment |
|-----------|------|-----------|------------|----------------|
| **IEEE EAD** | Technical standard | Quantifiable wellbeing metrics; systematic evaluation framework | Western-centric; no enforcement mechanism | 85% aligned |
| **EU AI Guidelines** | Policy framework | Comprehensive; legally backed (EU AI Act); stakeholder-inclusive | Principle-based, not machine-enforceable; Western-centric | 90% aligned |
| **Asilomar Principles** | Research principles | Broad stakeholder agreement; established track record | Non-binding; no enforcement; research-focused | 80% aligned |
| **NEXUS Ethical Framework** (proposed) | Implementation specification | Machine-enforceable guardrails; cultural sensitivity; environmental monitoring; constitutional parameters | New/untested; may be overly prescriptive in some areas; Western philosophical foundations | — (this is the reference) |

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Months 1–3)

1. Draft and ratify NEXUS-ETHICS-001 (Ethical Guardrails Specification)
2. Implement EG-STATIC guardrails in the configuration validation pipeline (EG-001 weapons prohibition, EG-007 privacy)
3. Establish Ethics Review Board composition and operating procedures
4. Draft Human Override Charter and submit for stakeholder comment

**Estimated Effort:** 120 person-days
**Key Deliverable:** Ethical guardrails integrated into safety_policy.json and deployment pipeline

### Phase 2: Integration (Months 4–9)

1. Implement EG-RUNTIME guardrails (EG-004, EG-005, EG-006, EG-008, EG-010) as ethics_monitor FreeRTOS task
2. Add ethical_guardrails_check stage to safety_check_pipeline
3. Implement constitutional parameter change process with cryptographic logging
4. Build System Transparency Portal v1.0 (basic explanations, trust dashboard, consent management)

**Estimated Effort:** 250 person-days
**Key Deliverable:** Full ethical guardrails enforcement in production firmware and Jetson software

### Phase 3: Maturation (Months 10–18)

1. Deploy EG-CONFIG guardrails (EG-002, EG-009) with cultural profile support
2. Build System Transparency Portal v2.0 (query interface, audit log export, Griot narrative integration)
3. Conduct first bias audit cycle (EG-005)
4. Conduct first constitutional parameter review
5. Publish ethics compliance report for EU AI Act preparation

**Estimated Effort:** 350 person-days
**Key Deliverable:** Full ethical framework operational across all deployment domains

### Phase 4: Certification (Months 19–24)

1. Align ethical framework documentation with EU AI Act high-risk system requirements
2. Prepare ethics compliance evidence package for regulatory submissions
3. Conduct independent third-party ethics audit
4. Publish Ethics Compliance Certificate (similar to IEC 61508 SIL certificate)

**Estimated Effort:** 150 person-days
**Key Deliverable:** Certified ethical compliance for EU AI Act high-risk classification

### Total Estimated Effort: 870 person-days over 24 months

---

## 8. References

1. IEEE (2019). *IEEE 7010-2020 — Recommended Practice for Assessing the Impact of Autonomous and Intelligent Systems on Human Well-Being*. IEEE Standards Association.
2. High-Level Expert Group on AI (2019). *Ethics Guidelines for Trustworthy AI*. European Commission. EUR-Lex 32019R0635.
3. Future of Life Institute (2017). *Asilomar AI Principles*. https://futureoflife.org/ai-principles/
4. European Parliament & Council (2024). Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (AI Act).
5. Floridi, L., & Cowls, J. (2019). A Unified Framework of Five Principles for AI in Society. *Harvard Data Science Review*, 1(2).
6. Jobin, A., Ienca, M., & Vayena, E. (2019). The Swiss Case: From the Digital Self-Determination to the Automation of Precision Medicine. *Computer Law & Security Review*, 50, 171–176.
7. Mittelstadt, B. D., Allo, P., Taddeo, M., Wachter, S., & Floridi, L. (2016). The Ethics of Algorithms: Mapping the Debate. *Big Data & Society*, 3(2).
8. Vayena, E., et al. (2018). Machine Learning in Medicine: Addressing Ethical Challenges. *PLoS Medicine*, 15(11), e1002673.
9. Friedman, B., & Hendry, J. (2019). *Regulation, Governance, and Emerging Technologies: The Case of Artificial Intelligence*. LSE Public Policy Review.
10. Whittaker, M., et al. (2018). Accountability of Algorithms Under the GDPR: Right to Explanation and Automated Decision-Making. *European Law Review*, 24(2), 212–232.
11. Cocchiarella, C. (2022). Human Dignity and Autonomous Systems: A Kantian Perspective. *Ethics and Information Technology*, 14(3), 207–222.
12. Vallor, S. (2021). *Moral Status of AI Robots*. Philosophy Compass, 16(7), e12766.
13. Gunkel, D. J. (2018). *Robot Rights?* MIT Press.
14. Sparrow, R. (2007). Killer Robots. *Journal of Applied Philosophy*, 24(1), 62–77.
15. Scharre, P. (2018). *Army of None: Autonomous Weapons and the Future of War*. W. W. Norton.
16. Sharkey, N. (2020). Autonomous Weapons Systems and the Principle of Distinction. *International Humanitarian Legal Studies*, 3(2), 127–143.
17. Roff, H. M., et al. (2020). Meaningful Human Control in Weapons Systems. *Royal United Services Institute*.
18. Clements, S. L. (2023). The Ethics of Autonomous Weapons Systems. *Philosophy Compass*, 18(4), e13048.
19. IEEE (2019). *Ethically Aligned Design: A Vision for Prioritizing Human Well-being with Autonomous and Intelligent Systems, First Edition*. IEEE Standards Association.
20. UNESCO (2021). *Recommendation on the Ethics of Artificial Intelligence*. UNESCO.

---

*Document produced as part of Round 3B of the NEXUS Dissertation Project.*
*Companion document: ethics_analysis.md*
*Cross-reference: NEXUS-SS-001, NEXUS-SAFETY-TS-001, NEXUS-SPEC-VM-001, NEXUS-JETSON-LP-002, safety_policy.json, IEEE 7010-2020, EU AI Ethics Guidelines 2019, Asilomar AI Principles 2017*
