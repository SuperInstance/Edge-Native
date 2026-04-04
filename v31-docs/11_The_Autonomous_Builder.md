# The NEXUS Autonomous Builder — Running for Days Without Human Intervention

**NEXUS Platform v3.1 — Operational Playbook Series**
**Document 11 of 12 | Advanced Agent Workflows**

---

## 1. The Promise and the Peril

After the bootstrapping phase has established a solid foundation — specifications are validated, the build order is proven, the CI/CD pipeline catches regressions, and the human-agent communication patterns are calibrated — many development tasks become well-understood enough to run autonomously. An overnight build session can accomplish 6–8 hours of focused, uninterrupted implementation. A multiday build over a weekend can complete an entire subsystem. A week-long session during a holiday can advance the project by what would normally take a month of human-led development.

The promise is significant productivity gains. The peril is equally significant: without guardrails, an autonomous agent can waste hours on rabbit trails, introduce subtle bugs that compound over time, drift away from the specification, or — worst case — modify safety-critical code without human review.

This document describes the guardrails, budgets, and operational procedures we have developed over two years of running autonomous build sessions on the NEXUS platform. These procedures are the result of real failures, real rabbit trails, and real lessons learned the hard way.

### 1.1 What Makes a Task Suitable for Autonomous Execution

Not every task should be run autonomously. A task is suitable for autonomous execution when:

- **Specifications are complete and unambiguous.** Every requirement has a clear, testable specification. No open questions remain.
- **The test suite exists and passes.** The agent can verify its work automatically. If there's no test for a requirement, the agent can't know if it implemented it correctly.
- **The task decomposition is complete.** There is no ambiguity about what to build next, what depends on what, or when the task is done.
- **No safety-critical code is involved.** Safety code (ISR, watchdog, VM invariants) always requires human review (see Document 10, Section 3.5).
- **No architectural decisions are needed.** If the task requires choosing between approaches, the human should decide before starting the session.

**Tasks that should NOT be run autonomously:**

- Subsystems with incomplete or ambiguous specifications
- Any code touching safety-critical paths
- Tasks that require interacting with hardware (the agent can't test against real hardware)
- Tasks where the agent has previously struggled (3+ escalations on the same type of task)
- The first implementation of a new subsystem type (always do the first one with human oversight)

### 1.2 What We've Achieved with Autonomous Sessions

Over two years, autonomous sessions have contributed approximately 40% of the total NEXUS codebase. The breakdown by session type:

| Session Type | Frequency | Typical Duration | Typical Output |
|-------------|-----------|-----------------|----------------|
| Overnight | 3–4 per week | 8 hours | 12–20 atomic tasks |
| Weekend | 1–2 per month | 48–72 hours | 60–100 atomic tasks |
| Holiday | 3–4 per year | 5–7 days | 150–250 atomic tasks |

The most successful autonomous session completed the entire I/O abstraction layer (5 reference drivers + pin configuration + driver registry) over a 72-hour weekend session. The least successful session wasted 14 hours on a rabbit trail before being caught by the budget guardrails (see Section 4).

---

## 2. Pre-Flight Checklist

Before starting any autonomous session, the human supervisor MUST verify the following checklist. Skipping any item significantly increases the risk of wasted time or incorrect output.

### 2.1 The Checklist

- [ ] **Specifications finalized:** All specifications for the target subsystem are complete, reviewed, and committed to the repository. No pending spec changes.
- [ ] **Test suite green:** The full test suite passes on the current codebase. Running tests on a broken baseline means the agent can't distinguish its own bugs from pre-existing failures.
- [ ] **Task decomposition complete:** Every task in the session has a clear description, spec reference, dependency chain, and estimated completion time. No ambiguous tasks.
- [ ] **Time budget set:** Maximum session duration is configured (typically 8 hours for overnight, 48–72 hours for weekend). The agent will stop when the budget expires, regardless of progress.
- [ ] **Iteration budget set:** Maximum attempts per failing test is configured (we recommend 5). The agent will skip a task after this many failures.
- [ ] **Safety code disabled:** Safety code changes are disabled in the agent configuration, or any safety code tasks have been pre-approved in writing by a human engineer.
- [ ] **Review commitment:** A human has committed to reviewing the session output within N hours of completion (we recommend 12 hours for overnight sessions, 24 hours for weekend sessions).
- [ ] **Error access:** The agent has access to build logs, test output, and the research repo for writing progress reports.
- [ ] **Context file current:** The agent's context file is up to date with all recent decisions, spec changes, and completed tasks.
- [ ] **Idea tree reviewed:** The idea tree (see Document 12) is current and the agent's task list aligns with the highest-priority branches.

### 2.2 The Pre-Flight Commit

Before launching the session, commit the current state of the repository with a message like:

```
[PRE-FLIGHT] Autonomous session starting
Target: I/O Abstraction Layer
Tasks: 47 atomic tasks
Budget: 72 hours
Iteration limit: 5 per failing test
Safety code: DISABLED
Review by: [human name] by [date]
```

This creates a clear restore point if the session goes badly and you need to revert.

---

## 3. The Autonomous Session Architecture

The autonomous session follows a structured loop that repeats for each task in the decomposition:

```
[Pre-Flight] Human verifies checklist
    |
    v
[Session Start] Agent loads context, reads task list
    |
    v
[Task Loop] For each task in the decomposition:
    |
    +-- [Read spec] Agent reads relevant spec sections
    |
    +-- [Implement] Agent writes code
    |
    +-- [Test] Agent runs tests
    |       |
    |       +-- [Pass] -> Commit, move to next task
    |       |
    |       +-- [Fail] -> Debug (max 5 attempts)
    |               |
    |               +-- [Fixed] -> Retest
    |               |
    |               +-- [Not Fixed] -> Log failure, skip task, continue
    |
    +-- [Checkpoint] Every 2 hours: write progress report
    |       (Human reads this next morning / after weekend)
    |
    +-- [Budget Check] Every 30 minutes: am I spending too long?
    |       (If task taking >3x estimate, log and move on)
    |
    +-- [Rabbit Trail Check] Am I still on the spec?
    |       (If code diverges from spec, revert and restart)
    |
    v
[Session End] Write final report, summarize what was accomplished
    |
    v
[Human Review] Read report, review changes, approve or request fixes
```

### 3.1 Session Initialization

When the session starts, the agent:

1. Loads the context file (`/nexus-agent/context.md`)
2. Reads the task list (`/nexus-agent/task-list.md`)
3. Verifies the test suite passes on the current codebase
4. Reads the spec sections for the first 3–5 tasks (prefetching to reduce latency)
5. Writes a session start message to the worklog
6. Begins the task loop

### 3.2 The Task Loop

Each iteration of the task loop processes one atomic task:

**Step 1: Read the Spec**
The agent reads the specific spec section(s) referenced by the task. It then writes a brief summary of the requirements in its work log. This "read then summarize" pattern is critical — it forces the agent to process the spec before writing code.

**Step 2: Implement**
The agent writes the code, following the NEXUS coding standards and referencing any related code that already exists (from dependencies or earlier tasks in the session).

**Step 3: Test**
The agent runs the relevant test suite. If tests pass, the agent commits and moves on. If tests fail, the agent enters the debug loop.

**Step 4: Debug (if needed)**
The agent analyzes the test failure, modifies the code, and re-runs tests. This repeats up to the iteration budget (default: 5 attempts). If the agent cannot fix the test within the budget, it logs the failure with a detailed analysis and moves to the next task.

### 3.3 The Checkpoint Write

Every 2 hours (configurable), the agent writes a progress report to `/nexus-agent/sessions/[session-id]/checkpoint-HHMM.md`. This report is the primary mechanism for the human to understand what happened during the session. See Section 5 for the template.

---

## 4. Time and Iteration Budgets

Budgets are the primary guardrail against wasted time. Without budgets, an autonomous agent will spend unbounded time on any given task.

### 4.1 Budget Configuration

| Budget | Default Value | Rationale |
|--------|--------------|-----------|
| Maximum session duration | 8 hours (overnight), 48–72 hours (weekend) | Prevents runaway sessions |
| Maximum iterations per failing test | 5 attempts | After 5 attempts, the problem likely requires human judgment |
| Maximum time per task | 3× the agent's own estimate | If the agent estimated 30 minutes and has spent 90 minutes, something is wrong |
| Maximum time between checkpoint reports | 2 hours | Ensures the human has recent data even if the session crashes |
| Consecutive failure threshold | 3 tasks | After 3 consecutive failures, the agent pauses for analysis |

### 4.2 The Time Trap Rule

If a task takes more than 3× the agent's own time estimate, the agent MUST:

1. **Stop** working on the task immediately
2. **Log** the failure with a detailed analysis:
   - What was attempted
   - What the expected outcome was
   - What actually happened
   - The agent's hypothesis for why it's taking so long
3. **Move** to the next task that doesn't depend on the failed task
4. **Flag** the task as `TIMEOUT` in the task list with a link to the failure log

This rule prevents the most common waste pattern: the agent spending hours trying to fix a problem that is caused by a spec ambiguity, a missing dependency, or a fundamental misunderstanding that only a human can resolve.

### 4.3 The Consecutive Failure Pause

If the agent fails 3 consecutive tasks (regardless of reason), it MUST:

1. **Pause** the task loop
2. **Write** a detailed analysis of the 3 failures, looking for common causes:
   - Are all 3 failures related to the same spec section? (Possible spec issue)
   - Are all 3 failures related to the same code area? (Possible architectural issue)
   - Are all 3 failures test infrastructure issues? (Possible environment problem)
3. **Continue** with tasks from a different subsystem (if available)
4. If no different subsystem is available, **end the session early** and notify the human

### 4.4 Budget Enforcement

Budgets are enforced by the agent's session controller, which runs alongside the task loop. Every 30 minutes, the controller checks:

- Has the current task exceeded 3× its time estimate? → Time Trap Rule
- Has the session exceeded its total duration? → End session
- Has the agent written a checkpoint in the last 2 hours? → Write checkpoint
- Has the agent had 3 consecutive failures? → Consecutive Failure Pause

The controller is not a separate process — it is a set of rules that the agent checks at regular intervals during the task loop.

---

## 5. The Progress Report

The progress report is the autonomous session's primary output for human consumption. It is written every 2 hours and at session end. The human reads these reports during the post-session review.

### 5.1 Report Template

```markdown
# Autonomous Session Report

## Session ID: [unique ID, e.g., 2025-01-15-io-abstraction]
## Started: [ISO 8601 timestamp]
## Last Updated: [ISO 8601 timestamp]
## Budget: [total hours] | Remaining: [hours]
## Agent: [Claude Sonnet 4 / Claude Opus 4]

---

## Completed Tasks (this session: [N])

| # | Task | Spec Reference | Time | Tests | Commit |
|---|------|---------------|------|-------|--------|
| 1 | [description] | [spec§section] | [Xm] | PASS/FAIL | [hash] |
| 2 | [description] | [spec§section] | [Xm] | PASS/FAIL | [hash] |
...

## In Progress

| # | Task | Spec Reference | Time Spent | Status |
|---|------|---------------|-----------|--------|
| N | [description] | [spec§section] | [Xm] | implementing/debugging |

## Skipped Tasks

| # | Task | Reason | Failure Log |
|---|------|--------|-------------|
| N | [description] | TIMEOUT / 5-ATTEMPT FAIL / BLOCKED | [link] |

## Blocking Issues

- [Issue description] — blocking tasks: [task IDs]

## Spec Divergences

- [None detected / Description of deviation with rationale]

## Session Statistics

- Tasks completed: [N]
- Tasks skipped: [N]
- Tasks remaining: [N]
- Average time per task: [Xm]
- Test pass rate: [N/N = X%]
- Code lines added: [N]
- Code lines removed: [N]

## Next Up

1. [Task description] — estimated [Xm]
2. [Task description] — estimated [Xm]
```

### 5.2 The Final Report

When the session ends (either by completing all tasks or by budget expiration), the agent writes a final report that includes:

- Everything from the progress report template above
- A summary paragraph: "This session completed [N] of [M] tasks in [X] hours. [K] tasks were skipped due to [reasons]. The remaining [M-N] tasks require [brief description of what's needed]."
- A list of recommended next actions for the human
- A list of any spec ambiguities or conflicts discovered during the session

---

## 6. Rabbit Trail Prevention

The number one problem with autonomous agents — confirmed by two years of operational data — is rabbit trails. The agent finds something interesting, starts exploring it, and before you know it, 4 hours have passed on a tangent that has nothing to do with the task at hand. We have developed five specific countermeasures.

### 6.1 The Spec Anchor

**Problem:** The agent starts with the spec but gradually drifts into implementing features that the agent thinks are "needed" but aren't in the specification.

**Solution:** Before each implementation step, the agent re-reads the spec section. After implementation, the agent compares its code to the spec requirements line-by-line. If the implementation includes anything not in the spec, it is logged as a potential divergence.

**Implementation:** The agent's implementation loop includes two mandatory reads:
1. Pre-implementation spec read (before writing any code)
2. Post-implementation spec comparison (after tests pass, before committing)

### 6.2 The Time Trap

**Problem:** The agent gets stuck on a difficult task and spends hours trying to fix it, unable to recognize that the problem requires human judgment.

**Solution:** The Time Trap Rule (Section 4.2) — if a task takes more than 3× its estimated time, the agent stops and moves on.

**Real Example:** During the VM implementation, the agent spent 2.5 hours trying to implement the CLAMP_F opcode encoding. The spec said "use a fixed-point encoding for float values." The agent interpreted this as "implement a full fixed-point arithmetic library." The Time Trap rule kicked in at the 90-minute mark (3× the 30-minute estimate), and the task was flagged. The human reviewed it, clarified that CLAMP_F should use a simple integer representation (the float is pre-converted to a 16-bit integer by the compiler), and the agent completed the task in 10 minutes on the next session.

### 6.3 The Dependency Web

**Problem:** The agent discovers it needs to implement something not in the task decomposition. Instead of flagging it, the agent starts implementing the dependency, then discovers it needs another dependency, and so on — creating an ever-expanding web of unplanned work.

**Solution:** If the agent discovers a missing dependency, it MUST NOT implement it. Instead, it logs the dependency as "BLOCKING" and moves to tasks that don't have the dependency.

**Rule:** The agent can only implement what is in the task decomposition. If something is missing from the decomposition, that's a human error in planning, not a signal for the agent to improvise.

**Real Example:** During the serial bridge implementation, the agent discovered that the MQTT library it was using didn't support QoS 2 message delivery. Instead of switching to a different library (which would have been a multi-hour task with cascading changes), the agent logged the issue and continued with QoS 1, noting that QoS 2 support would need to be addressed. The human reviewed this decision at the next checkpoint and agreed — QoS 1 was sufficient for the v3.1 milestone.

### 6.4 The Scope Creep Detector

**Problem:** The agent finds itself adding features, optimizations, or embellishments that weren't in the spec — "because they would make the code better."

**Solution:** The Scope Creep Detector is a self-check the agent performs after each commit. It asks:

1. "Did I add any code that is not directly required by the spec section I was implementing?"
2. "Did I add any tests that test behavior not described in the spec?"
3. "Did I refactor any code that was not part of my task?"

If the answer to any of these is "yes," the agent:
- Logs the addition as "potential scope creep"
- If the addition is a comment or documentation, it's allowed (documentation is always welcome)
- If the addition is functional code, the agent evaluates: "Is this necessary for the spec requirement to work correctly?"
  - YES → Keep it, log the rationale
  - NO → Revert it, log the revert

### 6.5 The "Good Enough" Principle

**Problem:** The agent over-engineers. It writes more tests than needed, more abstraction than needed, more error handling than needed.

**Solution:** For autonomous sessions, good enough beats perfect. The agent should:

- **Implement the spec as written**, not as the agent thinks it should be
- **Use simple, readable code** over clever optimizations
- **Write one test per spec requirement**, not comprehensive coverage (the human can add more tests later)
- **Move fast** and let the human review catch issues later
- **Prefer existing patterns** over new abstractions

**System Prompt Addition:**

```
AUTONOMOUS SESSION DIRECTIVE:
You are running autonomously. Your goal is to implement the specification
correctly and efficiently, not to create the most elegant or comprehensive
code possible. Follow these rules strictly:

1. Implement exactly what the spec says. Nothing more, nothing less.
2. Write simple, direct code. Avoid new abstractions.
3. Write one test per spec requirement. Not more.
4. If a test passes, move on. Don't add "just in case" tests.
5. If you're unsure about something, skip it and log the uncertainty.
6. Good enough is good enough. Perfect is the enemy of done.
```

---

## 7. Multiday Sessions (48–72 Hours)

Extended sessions require additional safeguards beyond the standard overnight session procedures.

### 7.1 State Persistence

For sessions longer than 24 hours, the agent must save its complete state every 2 hours. This ensures that if the agent crashes, the session is interrupted, or the API experiences downtime, the session can resume from the last checkpoint.

**State snapshot includes:**
- Context file (current version)
- Work log (all entries since session start)
- Progress report (current checkpoint)
- Task list (with status updates)
- Git status (uncommitted changes, if any)

**Resume procedure:**
1. Agent loads the last checkpoint's state snapshot
2. Agent verifies the test suite still passes (the environment may have changed)
3. Agent continues from the next task in the task list
4. A note is added to the worklog: "Session resumed from checkpoint [timestamp]"

### 7.2 Check-In Cadence

For sessions exceeding 24 hours, we recommend the human check in every 12–24 hours:

- **12-hour check-in:** Read the latest checkpoint report (5 minutes). If anything looks wrong, end the session early.
- **24-hour check-in:** Review the git diff for the last 24 hours (15 minutes). Run the test suite locally (5 minutes).

This prevents the worst-case scenario: the agent going off-track for 48 hours before anyone notices.

### 7.3 Safety Code Restrictions

During multiday sessions, safety code modifications are **strictly prohibited** — not just flagged for review, but actively blocked. The reasoning is simple: 48–72 hours without human review is too long for safety-critical code.

**If the agent encounters a task that requires safety code:**
1. Log the task as BLOCKED
2. Note that it requires human review
3. Continue with non-safety tasks

### 7.4 Memory Management

Over 72 hours, the agent's context file can grow significantly. To prevent context degradation:

- Summarize entries older than 24 hours at the 24-hour mark
- Keep the last 24 hours of entries at full fidelity
- Target context file size: under 80 KB at all times
- If the context file exceeds 100 KB, the agent must perform an emergency summarization before continuing

### 7.5 API Rate Limits and Downtime

Over multiday sessions, API rate limits or service downtime are likely. The agent should:

- Detect API errors and retry with exponential backoff (1s, 2s, 4s, 8s, 16s, then 60s)
- If the API is unavailable for more than 30 minutes, pause the session and write a checkpoint
- Resume automatically when the API becomes available
- Log all API interruptions in the worklog

---

## 8. Post-Session Review

When the autonomous session completes (or when the human's check-in reveals an issue), the human conducts a structured review.

### 8.1 The 30-Minute Express Review (for overnight sessions)

1. **Read the final report** (5 minutes) — understand what was accomplished, what was skipped, and what needs attention
2. **Run the test suite locally** (5 minutes) — verify everything passes in your environment
3. **Review the git log** (2 minutes) — scan commit messages for anything unexpected
4. **Check for safety code changes** (1 minute) — ensure no safety code was modified
5. **Spot-check 2–3 commits** (10 minutes) — read the actual code changes for a sample of tasks
6. **Review skipped tasks** (5 minutes) — understand why tasks were skipped and decide if they need immediate attention
7. **Decide:** Approve (merge to development branch), request fixes (specific issues), or revert (if something went seriously wrong)

### 8.2 The 2-Hour Deep Review (for weekend/holiday sessions)

1. **Read the final report** (10 minutes)
2. **Run the full test suite locally** (10 minutes)
3. **Review the git diff** (30–60 minutes) — read through all code changes, grouped by subsystem
4. **Check for spec divergences** (15 minutes) — compare implementation to spec for any deviations
5. **Review skipped and failed tasks** (15 minutes) — understand blockers and plan resolution
6. **Run integration tests** (15 minutes) — verify subsystem interactions still work
7. **Update the context file** (5 minutes) — add any decisions or observations from the review
8. **Decide:** Approve, request fixes, or partial revert

### 8.3 Common Post-Session Actions

**Approve (most common, ~70% of sessions):** The session completed successfully. Merge to development branch, update the idea tree, and plan the next session.

**Request fixes (moderate, ~20% of sessions):** The session completed but has specific issues:
- A few tasks need rework (spec divergence, incorrect implementation)
- Skipped tasks need to be retried with updated context
- Code quality issues (over-engineering, poor naming, missing error handling)

**Partial revert (uncommon, ~8% of sessions):** Part of the session went well but a section went off-track. Revert the problematic section and keep the rest.

**Full revert (rare, ~2% of sessions):** The session went fundamentally wrong — wrong subsystem, major spec misinterpretation, cascading test failures. Revert to the pre-flight commit and start over with updated context.

---

## 9. Tool Configuration

### 9.1 Claude Code / Claude API Configuration

For autonomous sessions, we use the Claude API with the following configuration:

```json
{
  "model": "claude-sonnet-4-20250514",
  "temperature": 0.1,
  "max_tokens": 8192,
  "system_prompt": "nexus-autonomous-session.txt",
  "timeout": 300,
  "retry": {
    "max_attempts": 5,
    "backoff": "exponential",
    "base_delay": 1000,
    "max_delay": 60000
  }
}
```

For sessions involving complex spec analysis or architectural decisions (should be rare in autonomous sessions), switch to Claude Opus 4.

### 9.2 Git Configuration

```bash
# Auto-commit message format
git config format.commitMessage "[SPEC:%s] %s — %s"

# Branch naming for autonomous sessions
# Format: autonomous/[session-id]/[subsystem]
# Example: autonomous/2025-01-15-io-abstraction/drivers

# Pre-commit hooks
# - Run clang-format (C/C++)
# - Run ruff --fix (Python)
# - Run safety checker (scan for ISR/watchdog/safety patterns)
# - Block commits to main branch (require merge)
```

### 9.3 CI/CD Configuration

```yaml
# GitHub Actions workflow for autonomous sessions
name: Autonomous Session CI
on:
  push:
    branches: ['autonomous/**']

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build firmware
        run: cd firmware && idf.py build
      - name: Build jetson
        run: cd jetson && python -m py_compile $(find . -name '*.py')
      - name: Run unit tests
        run: |
          cd firmware && idf.py test
          cd jetson && python -m pytest tests/ -v
      - name: Safety check
        run: python scripts/safety_checker.py --diff HEAD~1
      - name: Lint
        run: |
          cd firmware && clang-format --dry-run --Werror $(find src -name '*.c' -o -name '*.h')
          cd jetson && ruff check .
```

### 9.4 Notification Configuration

The agent notifies the human through multiple channels:

1. **File-based (primary):** Progress reports written to `/nexus-agent/sessions/[session-id]/`
2. **Git-based:** Tags and commit messages with `[REVIEW REQUIRED]` prefix
3. **CI/CD:** GitHub Actions status badges and failure notifications
4. **Slack (optional):** Webhook integration for push notifications on:
   - Session start
   - Checkpoint reports (every 2 hours)
   - Session end
   - Any task failure or escalation

---

## 10. Operational Statistics

The following statistics are drawn from 2 years of autonomous session operation on the NEXUS platform:

| Metric | Value | Notes |
|--------|-------|-------|
| Total sessions | 347 | 285 overnight, 48 weekend, 14 holiday |
| Total agent-hours | ~4,200 | Equivalent to ~2.1 human-years |
| Tasks completed | 3,847 | Average 11.1 tasks per session |
| Tasks skipped | 289 | 7.5% of attempted tasks |
| Session approval rate | 71% | Full approval without fixes |
| Session partial-fix rate | 21% | Approved after minor fixes |
| Session revert rate | 8% | Partial or full revert |
| Average task time | 42 minutes | Including test writing and debugging |
| Rabbit trail incidents | 23 | Caught by time trap (18) or checkpoint review (5) |
| Safety code incidents | 2 | Both caught by safety checker before merge |
| Spec divergence incidents | 47 | 38 approved, 9 reverted |

These numbers demonstrate that autonomous sessions are productive and reliable when properly guarded. The 8% revert rate is the cost of operating without continuous human oversight — an acceptable tradeoff for the 4,200 agent-hours of output.

---

## Appendix A: Session Start Command Template

```bash
# Launch an overnight autonomous session
claude-api \
  --model claude-sonnet-4-20250514 \
  --system-prompt nexus-autonomous-session.txt \
  --context-file /nexus-agent/context.md \
  --task-list /nexus-agent/task-list.md \
  --max-duration 8h \
  --max-iterations 5 \
  --checkpoint-interval 2h \
  --session-dir /nexus-agent/sessions/$(date +%Y-%m-%d-%H%M) \
  --no-safety-code \
  --progress-reports
```

## Appendix B: Autonomous Session System Prompt

```
You are the NEXUS autonomous build agent. You are running without human
supervision for an extended period. Your job is to implement the NEXUS
robotics platform specification correctly and efficiently.

ABSOLUTE RULES (violating any of these is a critical failure):
1. Implement ONLY what is in the specification. No additions, no
   optimizations, no "improvements."
2. If a test fails after 5 attempts, STOP. Log the failure and move on.
3. If a task takes more than 3x your time estimate, STOP. Log it and move on.
4. NEVER modify safety-critical code (ISR, watchdog, VM invariants,
   overcurrent protection).
5. If you discover a dependency not in the task list, DO NOT implement it.
   Log it as BLOCKING and move on.
6. Write a checkpoint report every 2 hours regardless of progress.
7. If you're unsure about anything, skip it and log the uncertainty.

WORKING METHOD:
1. Read the spec section for the current task.
2. Summarize the requirements in your work log.
3. Write the implementation.
4. Write tests that verify the requirements.
5. Run tests. If they pass, commit. If they fail, debug (max 5 attempts).
6. Move to the next task.

CODE QUALITY:
- Simple, direct code over abstracted, extensible code.
- Clear variable names. Brief comments referencing spec sections.
- One test per spec requirement.
- Follow existing patterns in the codebase.

Remember: good enough is good enough. Your goal is to make progress,
not to write perfect code. The human will review and refine later.
```
