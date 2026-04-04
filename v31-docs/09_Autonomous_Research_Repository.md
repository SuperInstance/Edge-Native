# Setting Up an Automatically Growing Research Repository for NEXUS

**Version:** 1.0.0 | **Date:** 2025-01-15 | **For:** NEXUS Development Teams (3–15 engineers)
**Context:** NEXUS v3.1, 2+ years operational, 3→10 engineer team growth

---

## 1. The Problem

After 18 months of NEXUS development, our research repository had become a maze. We had 47 branches, 23 of which were abandoned experiments nobody could explain. A new developer joining the team spent their first two weeks reading commit logs, Slack messages, and scattered Notion pages trying to understand what had been tried, what worked, and what was a dead end. Senior engineers were re-running experiments they'd already run six months earlier because nobody had written down the results.

The core problem wasn't a lack of documentation — it was a lack of *structure*. We had plenty of notes, but they were scattered across tools, formats, and people's heads. What we needed was a single repository that encoded the research direction, made the current state obvious, and automatically captured what happened each day so that "the next day's repo is most fruitful" — meaning any developer could sit down, spend 15 minutes reading, and pick up exactly where the team left off.

This document describes the system we built to solve this problem. It has been running for 6 months across our team of 10 engineers working on NEXUS v3.0–3.1. It works. Here's how to set it up.

---

## 2. The Research Repo Philosophy

Before describing the structure, five principles that guided the design:

**Principle 1: A living document, not a static archive.**
The repository is never "done." It is updated daily — sometimes automatically, sometimes by hand. Every experiment is documented *before* it starts (hypothesis, expected outcome, success criteria) and *after* it concludes (results, lessons learned). The repo grows organically with the project.

**Principle 2: Every experiment is documented before it starts.**
No developer should write a line of code for an experiment without first writing a README.md in the experiment directory that states what they're testing, why, and what success looks like. This is enforced by a pre-commit hook (see Section 8). The README is a contract with your future self and your teammates.

**Principle 3: Failed experiments are as valuable as successful ones.**
A dead end that is documented is a dead end that won't be re-explored. We have a `known_dead_ends.md` file that is the most-read document in the repository. It has saved us hundreds of hours of re-work. When an experiment fails, we celebrate the learning, not the failure.

**Principle 4: The repo structure encodes the research direction.**
The directory tree itself communicates what the team is working on. An experiment directory exists only if there is an active or recent hypothesis being tested. When an experiment concludes, it either moves to `03_IMPLEMENTATION/` (if successful) or stays in `02_EXPERIMENTS/` with a `conclusion.md` (if failed or inconclusive). The absence of directories in `02_EXPERIMENTS/` with active status means the team has no running experiments — which should never happen.

**Principle 5: 15 minutes to full context.**
A new developer — or a returning developer after a week away — should be able to understand the current state of the project in 15 minutes. This is measured and tracked. We survey new team members after their first week and ask: "How long did it take you to feel oriented?" The target is under 2 hours for onboarding and under 15 minutes for daily re-orientation.

---

## 3. Repository Structure

```
nexus-research/
├── 00_CONTEXT/                        ← READ THIS FIRST (auto-updated daily)
│   ├── current_hypotheses.md          ← What we're testing RIGHT NOW
│   ├── known_dead_ends.md             ← What we tried and why it didn't work
│   ├── open_questions.md              ← Things we don't know yet
│   ├── active_experiments.md          ← What's running on hardware right now
│   └── decision_log.md                ← Every significant decision with rationale
│
├── 01_SPECIFICATIONS/                 ← Source of truth (auto-synced from nexus_specs/)
│   ├── wire_protocol_spec.md
│   ├── vm_specification.md
│   ├── safety_system_spec.md
│   └── ...
│
├── 02_EXPERIMENTS/                    ← One directory per experiment
│   ├── EXP-001_pid_derivative_filter/
│   │   ├── README.md                  ← Hypothesis, setup, results, conclusion
│   │   ├── data/                      ← Raw data and analysis notebooks
│   │   ├── code/                      ← Experiment-specific code
│   │   └── conclusion.md              ← Final write-up (populated when experiment ends)
│   ├── EXP-002_observation_delta_encoding/
│   ├── EXP-003_synthetic_data_augmentation/
│   └── ...
│
├── 03_IMPLEMENTATION/                 ← Production code (merged from successful experiments)
│   ├── firmware/                      ← ESP32 firmware source
│   ├── jetson/                        ← Jetson cognitive layer source
│   └── schemas/                       ← JSON schemas (reflex, config, protocol)
│
├── 04_VALIDATION/                     ← Test results, safety reports, benchmarks
│   ├── test_results/
│   │   ├── 2025-01-10_regression_suite.json
│   │   └── 2025-01-10_safety_validation.json
│   ├── benchmarks/
│   └── incident_reports/
│
├── 05_LEARNED/                        ← Hard-won lessons (the most valuable directory)
│   ├── patterns.md                    ← Patterns that work (copy these)
│   ├── anti_patterns.md               ← Patterns that don't work (avoid these)
│   └── domain_knowledge.md            ← Non-obvious domain expertise
│
├── 06_AI_EXPERIMENTS/                 ← LLM fine-tuning, prompt engineering, model eval
│   ├── models/
│   │   ├── marine_v1.0.0/
│   │   │   ├── training_config.yaml
│   │   │   ├── evaluation_results.json
│   │   │   └── deployment_log.md
│   │   └── ...
│   ├── prompts/
│   └── evaluation/
│
├── 07_DAILY_DIGEST.md                 ← AUTO-GENERATED summary of yesterday's progress
│
└── .github/
    └── workflows/
        ├── daily_digest.yml           ← Runs at midnight, generates digest
        ├── experiment_status_check.yml ← Flags stale experiments (>2 weeks without update)
        └── context_sync.yml           ← Syncs 01_SPECIFICATIONS/ with upstream
```

### Directory Rationale

**`00_CONTEXT/`** is the "read me first" directory. It contains five files that together answer: "What is the team working on? What do we know? What don't we know? What happened? What did we decide?" Every file in this directory is auto-updated or semi-auto-updated (human writes the content, automation formats and timestamps). The `decision_log.md` is append-only — decisions are never removed, only annotated with "SUPERSEDED BY DEC-XXX" if reversed.

**`01_SPECIFICATIONS/`** is a read-only mirror of the canonical specification files. It is kept in sync with the main spec repository via a GitHub Action that runs hourly. No one edits files in this directory directly — all edits happen in the upstream `nexus_specs/` repository.

**`02_EXPERIMENTS/`** is the heart of the research repository. Each experiment gets a numbered directory (`EXP-NNN`) and a structured README. The README template is enforced by the pre-commit hook. Experiments are never deleted — they are either moved to `03_IMPLEMENTATION/` (on success) or left in place with a completed `conclusion.md` (on failure/inconclusive).

**`03_IMPLEMENTATION/`** contains the production codebase. Code arrives here via pull request from `02_EXPERIMENTS/` when an experiment is successful. The PR description must reference the experiment number and include a link to the conclusion.

**`04_VALIDATION/`** is the permanent record of all testing. Every test run produces a timestamped result file. This creates an audit trail that is invaluable for safety certification and for tracking long-term trends (e.g., "Has the regression suite pass rate been declining over the last 3 months?").

**`05_LEARNED/`** is the highest-value directory. It contains the distilled wisdom of the team — patterns that work, anti-patterns that don't, and non-obvious domain knowledge. This is the document that prevents the team from making the same mistakes twice. It is curated (not append-only) — entries are reviewed quarterly and consolidated.

**`06_AI_EXPERIMENTS/`** is a specialized directory for all AI/ML work, which has a different cadence and toolchain than the firmware/embedded work. It contains model training configs, evaluation results, and prompt engineering experiments.

---

## 4. The Daily Digest Generator

Every night at 00:00 UTC, a GitHub Action runs a Python script that generates `07_DAILY_DIGEST.md`. This is the single most impactful automation in the research repository. It means that every morning, every developer has a 5-minute summary of what happened yesterday.

### What the Digest Contains

```markdown
# Daily Digest — 2025-01-14 (Tuesday)

## Yesterday's Activity

### Experiments
- **EXP-012** (pid_wind_feedforward): Modified — added wind gust rejection logic.
  Author: @chen. Status: ACTIVE. Updated: data/results_0114.csv
- **EXP-009** (observation_lz4): Concluded — CONFIRMED. LZ4 compression achieves 2.1x
  reduction on observation data. Moving to implementation.
  Author: @martinez. Status: CONCLUDED.

### Decisions
- **DEC-042**: Chose LZ4 over Zstandard for observation compression (faster on ESP32,
  acceptable ratio). See decision_log.md for full rationale.

### Commits (14)
- chen: feat: add wind gust detection to PID feedforward (EXP-012)
- martinez: data: add LZ4 benchmark results (EXP-009)
- patel: fix: COBS encoding edge case for 256-byte payloads
- ... (11 more)

### Safety Events (0)
No safety events yesterday. streak: 47 days.

### Validation
- Regression suite: 48/50 passed (RT-023, RT-041 failed — investigating)

## Priorities for Today
1. [EXP-012] @chen: Test wind gust rejection in 20-knot conditions (weather permitting)
2. [EXP-013] @patel: Begin observation buffer overflow stress test
3. [ALL] Review DEC-042 before EOD — flag concerns in decision_log.md

## Dead Ends (Yesterday)
None. (Good day — no time wasted.)

## Stale Experiments (>14 days without update)
- **EXP-007** (i2c_multiplexer_daisy): Last updated 2024-12-28. Status: ACTIVE.
  @williams — is this still running?
```

### The Generator Script

The digest generator reads:

1. **Git log** (`git log --since="yesterday" --oneline --all`) for commits
2. **Experiment directories** (scans `02_EXPERIMENTS/*/README.md` for status changes) — detected by comparing `git diff` on experiment README files modified yesterday
3. **Decision log** (scans `00_CONTEXT/decision_log.md` for entries dated yesterday)
4. **Safety event log** (reads from `04_VALIDATION/incident_reports/`)
5. **Validation results** (reads from `04_VALIDATION/test_results/`)
6. **Experiment staleness** (checks `git log -1 --format="%ai"` for each `EXP-*` directory)

The script is at `.github/scripts/generate_daily_digest.py` (~200 lines of Python). It produces a markdown file and commits it with the message `chore: daily digest 2025-01-14`.

**Key design decision:** The digest is committed directly to the main branch (no PR). It is a generated artifact, not human-authored content. If a developer wants to add context to the digest, they add it to the experiment README or decision log — it will appear in tomorrow's digest.

---

## 5. The Experiment Template

Every experiment in `02_EXPERIMENTS/` starts from this template. The pre-commit hook verifies that the README exists and contains all required sections before allowing the commit.

```markdown
# EXP-NNN: [Title]

**Author:** [Name] | **Created:** YYYY-MM-DD | **Status:** ACTIVE/CONCLUDED/ABANDONED
**Hypothesis ID:** H-[number] (from current_hypotheses.md)

## Hypothesis

[What we believe and why we believe it. Should be a testable statement.]

*Example: "Adding a derivative low-pass filter (alpha=0.1) to the PID controller will reduce
rudder oscillation by at least 50% without increasing heading error by more than 1 degree,
because the current oscillation is caused by compass sensor noise being amplified by the
derivative term."*

## Setup

### Hardware
- [List hardware used: which nodes, sensors, actuators, test fixtures]

### Software
- [Firmware version, Jetson software version, any branches]

### Configuration
- [Relevant configuration snippets: PID gains, thresholds, etc.]

## Success Criteria

1. [Measurable, quantitative criterion]
2. [Measurable, quantitative criterion]
3. [Optional: "no regression on existing metrics"]

*Example:*
1. Rudder oscillation amplitude (peak-to-peak) < 2.0 degrees in calm conditions
2. Heading RMSE < 1.5 degrees in calm conditions
3. Schema validation pass rate unchanged (>90%)

## Procedure

1. [Step 1]
2. [Step 2]
3. [Step 3]
...

## Results

[Data, graphs, observations. Link to data/ directory.]

## Conclusion

**Status: CONFIRMED / REFUTED / INCONCLUSIVE**

[Summary of findings. What worked, what didn't, what was surprising.]

### Impact on Main Codebase

- [ ] No changes — hypothesis refuted
- [ ] Bug fix — file PR to 03_IMPLEMENTATION/
- [ ] New feature — file PR to 03_IMPLEMENTATION/
- [ ] Further investigation needed — create follow-up experiment

### Follow-up Experiments

- [EXP-NNN]: [Brief description of what to test next]

## Raw Data

See `data/` directory for:
- `data/run_001.csv` — [description]
- `data/run_002.csv` — [description]
- `analysis.ipynb` — Jupyter notebook with data analysis
```

### The Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit (or via pre-commit framework)

# Check that any new/modified experiment directory has a valid README
for dir in $(git diff --cached --name-only --diff-filter=ACMR | \
             grep '^02_EXPERIMENTS/EXP-[0-9]*/README.md$' | \
             xargs -I{} dirname {}); do
    if ! grep -q "## Hypothesis" "$dir/README.md"; then
        echo "ERROR: $dir/README.md is missing required '## Hypothesis' section."
        echo "Copy the template from 02_EXPERIMENTS/_TEMPLATE/README.md"
        exit 1
    fi
    if ! grep -q "## Success Criteria" "$dir/README.md"; then
        echo "ERROR: $dir/README.md is missing required '## Success Criteria' section."
        exit 1
    fi
done

echo "Pre-commit checks passed."
```

---

## 6. The Decision Log

Every significant decision — architectural, technical, or procedural — gets an entry in `00_CONTEXT/decision_log.md`. This is the project's collective memory for *why* things are the way they are.

```markdown
# Decision Log

## DEC-001: Two-Model Architecture for Code Generation

**Date:** 2024-03-15
**Author:** @martinez
**Context:** The system needs to generate reflex code AND validate it for safety. Should
we use one model for both or separate models?

### Options Considered
1. **Single model** (generate + validate):
   - Pros: Simpler architecture, lower VRAM (only 4 GB needed)
   - Cons: Model approves its own output; correlated generation/validation blind spots
2. **Two models** (7B generator + 3.8B validator):
   - Pros: Independent perspectives catch 3% more safety issues; 8% disagreement rate surfaces edge cases
   - Cons: Higher VRAM (6 GB); more complex swap logic
3. **Three models** (generator + validator + mediator):
   - Pros: Maximum safety
   - Cons: Exceeds VRAM budget; adds latency

### Decision
**Option 2: Two models** (7B generator + 3.8B validator, Q4_K_M quantization)

### Rationale
The 3% additional safety catch rate is significant in a system that controls physical actuators.
The VRAM cost (2 GB for the validator) is acceptable because the models are time-multiplexed,
not simultaneously loaded. The 8% disagreement rate between models provides a natural
"difference of opinion" signal that is useful for flagging borderline cases.

### Confidence
**HIGH** — validated by A/B testing over 3 months.

### Reversible
Yes — single model is a config change.

### Reviewed By
@martinez, @chen, @williams

---

## DEC-042: LZ4 over Zstandard for Observation Compression

**Date:** 2025-01-14
**Author:** @martinez
**Context:** Observation data transfer over serial takes 87 seconds for 8 MB buffer.
We need compression. LZ4 and Zstandard are both viable options.

### Options Considered
1. **LZ4**: 50 MB/s on ESP32, 2.0–2.5x compression ratio
2. **Zstandard (level 1)**: 8 MB/s on ESP32, 2.5–3.0x compression ratio
3. **No compression**: 0 overhead, 0 benefit

### Decision
**Option 1: LZ4**

### Rationale
The serial link runs at 92 KB/s. LZ4 (50 MB/s) has 540x headroom over the serial link — it
will never be the bottleneck. Zstandard's better ratio (0.5x improvement) saves ~14 seconds
per transfer but takes 6x longer to compress, risking buffer overflow on the ESP32 if the
observation rate spikes. The simpler, faster algorithm is the right choice here.

### Confidence
**HIGH** — measured on ESP32-S3 hardware.

### Reversible
Yes — compression algorithm is a compile-time flag.

### Reviewed By
@martinez, @patel, @chen
```

---

## 7. The "Next Morning" Protocol

Every developer on the NEXUS team follows this protocol when they start work each day. It takes 7 minutes.

### Step 1: Read `current_hypotheses.md` (2 minutes)

This file lists 3–7 active hypotheses with their status. Each hypothesis links to the experiment(s) testing it.

```markdown
# Current Hypotheses (2025-01-15)

## H-001: Derivative filtering reduces PID oscillation [TESTING]
- Experiment: EXP-012 (pid_wind_feedforward) — @chen
- Expected result: >50% oscillation reduction
- Status: Initial tests show 40% reduction. Tuning filter parameters.

## H-002: LZ4 compression is sufficient for observation transfer [CONFIRMED]
- Experiment: EXP-009 (observation_lz4) — @martinez
- Result: 2.1x compression, 50 MB/s on ESP32. Confirmed.
- Action: Merge into 03_IMPLEMENTATION/

## H-003: Marine-specific model improves reflex quality [TESTING]
- Experiment: See 06_AI_EXPERIMENTS/models/marine_v1.1.0/ — @patel
- Expected result: >90% schema pass rate, <1.0 corrections per reflex
- Status: Training in progress (cloud GPU, ETA 2 hours)
```

### Step 2: Read `07_DAILY_DIGEST.md` (3 minutes)

Covers yesterday's activity, today's priorities, and any warnings. See Section 4 for full content.

### Step 3: Skim `known_dead_ends.md` (1 minute)

Check for any new entries added in the last week. This file prevents re-exploration.

```markdown
# Known Dead Ends

## DE-001: Zstandard compression on ESP32 (2024-11-20)
Too slow at 8 MB/s. Observation generation rate (28.8 KB/s) leaves insufficient margin.
Use LZ4 instead. See DEC-042.

## DE-002: LoRA rank > 32 for fine-tuning (2024-09-15)
VRAM exceeds 4.8 GB on Jetson with r=64. Model swaps fail with OOM.
Maximum practical rank is 32 (4.2 GB). See 06_AI_EXPERIMENTS/models/rank_sweep/.

## DE-003: PID at 1 kHz with 5 I2C sensors (2024-08-03)
CPU budget exceeded: 1,100 µs per tick vs. 1,000 µs budget. I2C polling at 5 devices
takes 500 µs, leaving insufficient margin for VM execution. Use 100 Hz tick or batch I2C.

## DE-004: JSON telemetry at 100 Hz over serial (2024-07-22)
Consumes 22.9% of serial bandwidth alone. Combined with observation dumps (34.6%),
total utilization exceeds 58%. Switch to binary telemetry (1.8% at 100 Hz).
```

### Step 4: Check `active_experiments.md` (1 minute)

Identifies any experiments running on shared hardware that might conflict with your plans.

```markdown
# Active Experiments (2025-01-15)

| Experiment | Hardware | Author | ETA | Status |
|---|---|---|---|---|
| EXP-012 | Vessel "Alpha" (steering node) | @chen | Jan 17 | Running |
| EXP-013 | Workbench (bench power supply) | @patel | Jan 20 | Setup |
| Model train | Cloud GPU (g5.xlarge) | @patel | 2 hours | Queued |

**Conflict warning:** EXP-012 is using the steering node on Vessel Alpha.
If you need the steering node, coordinate with @chen.
```

**Total time: 7 minutes.** At this point, you know what the team is testing, what was decided, what failed, and whether your planned work will conflict with anyone else's. You are oriented.

---

## 8. Automation

### GitHub Actions

**Daily Digest Generation** (`.github/workflows/daily_digest.yml`):
```yaml
name: Daily Digest
on:
  schedule:
    - cron: '0 0 * * *'  # Midnight UTC
  workflow_dispatch: {}   # Manual trigger for testing
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for git log
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python .github/scripts/generate_daily_digest.py
      - name: Commit digest
        run: |
          git config user.name "Nexus Bot"
          git config user.email "nexus-bot@example.com"
          git add 07_DAILY_DIGEST.md
          git commit -m "chore: daily digest $(date +%Y-%m-%d)" || true
          git push
```

**Experiment Staleness Check** (`.github/workflows/experiment_status_check.yml`):
```yaml
name: Experiment Status
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM UTC — weekly check
  workflow_dispatch: {}
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: python .github/scripts/check_experiment_staleness.py --days 14
      # This script creates a GitHub Issue for each stale experiment,
      # tagging the author with a reminder to update or conclude it.
```

**Spec Sync** (`.github/workflows/context_sync.yml`):
```yaml
name: Sync Specifications
on:
  schedule:
    - cron: '0 * * * *'  # Hourly
  workflow_dispatch: {}
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          git remote add specs https://github.com/org/nexus_specs.git || true
          git fetch specs main
          git checkout specs/main -- nexus_specs/
          cp -r nexus_specs/* 01_SPECIFICATIONS/
          rm -rf nexus_specs/
          git add 01_SPECIFICATIONS/
          git diff --cached --quiet || git commit -m "chore: sync specifications from upstream"
          git push
```

### Branch Protection Rules

| Branch | Protection | Rationale |
|---|---|---|
| `main` | 1 approval, passing CI, no force push | Standard production protection |
| `00_CONTEXT/` directory on any branch | 2 approvals | Context changes affect everyone — require consensus |
| `01_SPECIFICATIONS/` directory on any branch | Read-only (CI fails if modified) | Specs come from upstream — no local edits |
| `03_IMPLEMENTATION/` directory on any branch | 1 approval + passing tests + experiment reference in PR description | Production code must be traceable to an experiment |

### Git Tags for Experiment Conclusions

When an experiment concludes, the conclusion script creates a git tag:

```bash
# .github/scripts/conclude_experiment.py
git tag -a "EXP-012-concluded" -m "EXP-012: PID wind feedforward - CONFIRMED"
git push origin "EXP-012-concluded"
```

Tags provide a permanent, easy-to-find reference point. `git tag -l "EXP-*"` lists all experiments with their conclusions.

---

## 9. Anti-Patterns in Research Repos

We learned these the hard way. Each one cost us days or weeks of productivity.

### Anti-Pattern 1: The "Graveyard Branch"
**What happened:** In v1.0, we had 30+ branches that were created for experiments and never merged or documented. When we needed to know if something had been tried, we had to check out each branch, read the code, and try to understand what was going on. Nobody did this consistently.

**How we fixed it:** Every experiment now lives in `02_EXPERIMENTS/EXP-NNN/` on the main branch. No experiment branches. The experiment README is the documentation. The code is in `02_EXPERIMENTS/EXP-NNN/code/`. If the experiment is abandoned, the README gets a conclusion explaining why.

### Anti-Pattern 2: The "Knowledge Silo"
**What happened:** One engineer (@williams in this case) spent two weeks debugging an I2C timing issue. They found the root cause (I2C bus arbitration contention with flash cache fills) and fixed it. But they didn't write it up. Three months later, another engineer hit the same issue and spent another week debugging it.

**How we fixed it:** Added `05_LEARNED/patterns.md` and `05_LEARNED/anti_patterns.md`. When any developer solves a non-obvious problem, they add an entry. The entry format is: symptom, root cause, fix, and affected components. During code review, if a PR fixes a subtle bug, the reviewer asks "is this a pattern?" and requests an entry.

### Anti-Pattern 3: The "Reinvented Wheel"
**What happened:** We ran a Zstandard compression experiment in November 2024 and concluded it was too slow. In January 2025, a new engineer proposed trying Zstandard compression. Nobody remembered the previous experiment.

**How we fixed it:** The `known_dead_ends.md` file and the pre-commit hook that requires linking experiments to hypotheses. The dead ends file is the first thing in the "Next Morning" protocol. It is impossible to miss.

### Anti-Pattern 4: The "Decision Vacuum"
**What happened:** A developer chose Q4_K_M quantization for the code generation model. Another developer later questioned this choice and wanted to try Q5_K_M. A 30-minute discussion followed, with both sides speculating about why the original choice was made. Nobody could find the rationale.

**How we fixed it:** The `decision_log.md` with structured entries (DEC-NNN). Every significant decision is logged with options considered, the choice made, the rationale, and who reviewed it. The quantization decision is DEC-001. Now that discussion takes 10 seconds: "Check DEC-001."

### Anti-Pattern 5: The "Context Cliff"
**What happened:** A new engineer joined the team in v2.0 and spent two weeks reading commit logs, Slack messages, and scattered notes before they could contribute. They almost quit because they felt lost.

**How we fixed it:** The "Next Morning" protocol (Section 7) and the 00_CONTEXT/ directory. New engineers now spend 2 hours on their first day reading the full 00_CONTEXT/ directory and the last 30 days of daily digests. On day 2, they are contributing. We measure onboarding time and the current average is 1.5 days to first contribution.

---

## 10. Scaling to Multiple Teams

Our team grew from 3 to 10 engineers between v2.0 and v3.1. The research repo structure scaled with some adjustments.

### Single Repo vs. Multi-Repo

We kept a single repository. Multi-repo introduces cross-repo synchronization problems that are worse than the single-repo problems it solves (merge conflicts on `00_CONTEXT/` files, mostly). The key rule: **never have two people editing the same 00_CONTEXT/ file simultaneously.** This is enforced by the 2-approval branch protection and a Slack notification when someone opens a PR that modifies `00_CONTEXT/`.

### Cross-Team References

When the firmware team and the AI team need to coordinate (e.g., the firmware team needs to add a new opcode for a reflex type the AI team invented), they create a "coordination issue" in GitHub:

```
Title: [COORD-001] Add SEQUENCE opcode to VM for new reflex type
Assignees: @chen (firmware), @patel (AI)
Description:
- AI team has designed a "sequencer" reflex type (see EXP-015)
- Needs VM opcode: SEQUENCE (step_number, condition, action, next_step)
- Firmware team to implement in vm_execute.c
- AI team to update reflex compiler to generate SEQUENCE opcodes
- Dependency: EXP-015 must conclude before this can be merged
```

### Weekly Sync Meeting (15 Minutes, Structured)

Every Monday at 10:00 AM, the team has a 15-minute standing meeting with this exact agenda:

1. **30 seconds each:** One-sentence summary of what you're working on this week
2. **3 minutes:** Review `current_hypotheses.md` — any status changes?
3. **3 minutes:** Review `known_dead_ends.md` — any new entries?
4. **3 minutes:** Review `active_experiments.md` — any hardware conflicts?
5. **3 minutes:** Open questions — anything blocking anyone?
6. **3 minutes:** Review last week's daily digests for anything missed

The meeting is run from the `07_DAILY_DIGEST.md` file (the most recent one) and `00_CONTEXT/current_hypotheses.md`. No slides. No prepared presentations. Just the documents.

### When the Structure Breaks Down

Warning signs that the repo structure is failing:

- Developers skip the "Next Morning" protocol because the digest isn't useful → fix the digest generator
- `known_dead_ends.md` is growing faster than 2 entries per week → too many failures; review the hypothesis quality
- Experiment directories are created but never concluded → stale experiment check is too infrequent; reduce from weekly to daily
- Decision log has entries without rationales → the pre-commit hook isn't checking for this; add the check
- New engineers still take > 3 days to orient → the 00_CONTEXT/ files are too long or too dense; split them or add a "START HERE" summary

---

## Quick-Start: Set Up Your Own Research Repo

1. Create the directory structure (Section 3). Takes 5 minutes.
2. Copy the experiment template into `02_EXPERIMENTS/_TEMPLATE/`. Takes 2 minutes.
3. Install the pre-commit hooks. Takes 5 minutes.
4. Create the GitHub Actions (Section 8). Takes 30 minutes.
5. Populate `00_CONTEXT/current_hypotheses.md` with your first 3 hypotheses. Takes 10 minutes.
6. Populate `00_CONTEXT/known_dead_ends.md` with anything you've already tried and failed at. Takes 15 minutes.
7. Write your first `07_DAILY_DIGEST.md` manually (the automation will take over tomorrow). Takes 10 minutes.
8. Run the "Next Morning" protocol with your team tomorrow morning. Takes 7 minutes per person.

**Total setup time: ~90 minutes. ROI: immediate — starting tomorrow, every developer saves 1–2 hours per week that they used to spend figuring out what's going on.**

---

*Document version: 1.0.0 — Based on 6 months of operational experience with the research repository structure across a 10-person NEXUS development team. Adapt the structure to your team size and workflow, but keep the five principles (Section 2) intact — they are the foundation.*
