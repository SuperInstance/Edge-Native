# Idea Trees — Preventing Rabbit Trails and Nudging Direction

**NEXUS Platform v3.1 — Operational Playbook Series**
**Document 12 of 12 | Advanced Agent Workflows**

---

## 1. The Problem of Infinite Exploration

AI agents are natural explorers. They generate ideas faster than they can implement them, see connections between concepts that humans might miss, and constantly propose improvements, alternatives, and "what if" scenarios. In many contexts, this is a strength. In a specification-driven development project with a critical path and deadlines, it is the single greatest threat to progress.

Over two years of operating the NEXUS bootstrapping agent, we observed a consistent pattern: without explicit structure, the agent would pursue interesting tangents at the expense of the critical path. Not because the tangents were bad ideas — many of them were genuinely good — but because every hour spent on a tangent is an hour not spent on the critical path, and the critical path is what ships the product.

The problem manifests in several ways:

- **Feature creep:** The agent adds features not in the spec because "they would make the system better"
- **Architecture tourism:** The agent explores alternative architectures instead of implementing the specified one
- **Perfect implementation syndrome:** The agent keeps refining a completed feature instead of moving to the next task
- **Dependency discovery spiral:** The agent keeps finding new dependencies and going deeper instead of implementing at the current level
- **Analysis paralysis:** The agent keeps researching instead of implementing

This document describes the system we developed to manage the agent's exploratory tendency: the Idea Tree. It is a simple, git-backed, markdown-based structure that organizes every idea, feature, and task into a hierarchical tree with clear priorities, statuses, and pruning rules. It is the compass that keeps the agent — and the human — pointed at the most productive work.

---

## 2. The Idea Tree Structure

The Idea Tree is a single markdown file (`/nexus-agent/idea-tree.md`) that contains every idea, feature, and task in the NEXUS platform, organized hierarchically. It is the authoritative source of what exists, what's in progress, what's done, and what's been deliberately discarded.

### 2.1 Current Tree (as of v3.1, 2 years operational)

```
NEXUS Platform v3.1
├── Core Platform (MUST BUILD FIRST)
│   ├── Wire Protocol
│   │   ├── COBS Framing
│   │   │   ├── Reference implementation [DONE]
│   │   │   ├── Edge case handling [DONE]
│   │   │   └── Fuzz testing [DONE]
│   │   ├── Message Dispatch
│   │   │   ├── Routing table [DONE]
│   │   │   ├── Priority queuing [DONE]
│   │   │   └── Flow control [DONE]
│   │   └── Baud Negotiation
│   │       ├── State machine [DONE]
│   │       ├── Settling delay fix [DONE - v1.1]
│   │       └── Rate fallback [DONE]
│   ├── Safety System (MUST BUILD FIRST)
│   │   ├── Kill Switch
│   │   │   ├── Hardware wiring [DONE]
│   │   │   ├── ISR implementation [DONE]
│   │   │   └── Test procedures [DONE]
│   │   ├── Watchdog
│   │   │   ├── MAX6818 integration [DONE]
│   │   │   ├── Kick pattern [DONE]
│   │   │   └── Software fallback [DONE]
│   │   └── Heartbeat
│   │       ├── Protocol [DONE]
│   │       └── Escalation [DONE]
│   ├── Bytecode VM
│   │   ├── 32 Opcodes [DONE]
│   │   ├── CLAMP_F encoding [DONE - simplified]
│   │   ├── PID_COMPUTE [DONE]
│   │   ├── Safety invariants [DONE]
│   │   └── State machine support [DONE]
│   └── Boot Sequence [DONE]
│
├── Cognitive Layer (BUILD SECOND)
│   ├── Serial Bridge [DONE]
│   ├── Node Manager [DONE]
│   ├── Reflex Orchestrator [DONE]
│   ├── Learning Pipeline
│   │   ├── Cross-Correlation [DONE]
│   │   ├── Change-Point Detection [DONE]
│   │   ├── Behavioral Clustering [DONE]
│   │   ├── Temporal Pattern Mining [DONE]
│   │   ├── Bayesian Reward Inference [DONE]
│   │   └── IRL refinement [PARTIAL - unstable]
│   ├── Trust Score [DONE]
│   └── Chat Interface [DONE]
│
├── Cloud Layer (BUILD THIRD, OPTIONAL)
│   ├── Code Generation Pipeline [IN_PROGRESS]
│   ├── Fleet Management [TODO]
│   └── Training Pipeline [TODO]
│
├── Enhanced Features (BUILD AFTER CORE IS STABLE)
│   ├── Custom Model Training [TODO]
│   ├── Fleet Learning [TODO]
│   ├── Predictive Maintenance [TODO]
│   └── Multi-Vessel Coordination [TODO]
│
└── [PRUNED] Interesting But Off-Track Ideas
    ├── Behavior Tree Support [PRUNED - ADR-009 chose JSON state machines]
    ├── Native WiFi OTA [PRUNED - serial is more reliable, ADR-007]
    ├── REST API [PRUNED - gRPC+MQTT chosen, ADR-011]
    ├── K-Means Clustering [PRUNED - HDBSCAN better, kept as fallback ref]
    ├── Inverse RL Enhancement [PRUNED - unstable, kept as experimental]
    ├── Custom Allocator [PRUNED - PSRAM sufficient, premature optimization]
    ├── Lua VM [PRUNED - custom bytecode simpler for this use case]
    ├── BLE Peripheral Mode [PRUNED - not needed for v3.1]
    ├── CAN Bus Support [PRUNED - RS-422 sufficient, kept for v4.0]
    └── Real-Time Kernel [PRUNED - FreeRTOS adequate, unnecessary risk]
```

### 2.2 Node Anatomy

Each node in the tree has:

- **Name:** A short, descriptive label
- **Status:** One of `TODO`, `IN_PROGRESS`, `DONE`, `PARTIAL`, `BLOCKED`, `PRUNED`
- **Priority:** One of `P0` (critical path), `P1` (important), `P2` (nice-to-have), `P3` (future)
- **Annotation:** Optional context — rationale for pruning, note about instability, reference to ADR

### 2.3 Priority Definitions

| Priority | Meaning | Agent Behavior |
|----------|---------|---------------|
| **P0** | Critical path — must be done for the next milestone | Agent MUST work on this before any other priority |
| **P1** | Important — should be done for the next milestone | Agent works on P1 when no P0 tasks are available |
| **P2** | Nice-to-have — improves quality but not required | Agent only works on P2 when P0 and P1 are complete |
| **P3** | Future — interesting but not aligned with current goals | Agent never works on P3 unless explicitly directed |

---

## 3. Tree Maintenance Rules

The idea tree is only useful if it is maintained consistently. These rules ensure the tree remains accurate and actionable.

### Rule 1: Every idea goes into the tree before implementation

No code is written for a feature that doesn't have a corresponding node in the tree. This includes features the agent suggests and features the human suggests. The tree is the single source of truth for what exists.

**How to add an idea:** Open a pull request against the idea tree file. The PR must include:
- The new node with name, priority, and `TODO` status
- A brief rationale for why the idea is worth considering
- The proposed position in the tree hierarchy

**How to add an idea quickly (for human use):** Just add it directly. The human has the authority to add ideas without PRs. The agent does not.

### Rule 2: Every leaf node has a status

Every leaf node (a node with no children) must have exactly one status: `TODO`, `IN_PROGRESS`, `DONE`, `PARTIAL`, `BLOCKED`, or `PRUNED`. No status means no tracking, and no tracking means the idea will be forgotten.

| Status | Meaning | Can the agent work on it? |
|--------|---------|--------------------------|
| `TODO` | Not started, ready to work on | Yes |
| `IN_PROGRESS` | Currently being worked on | Yes (the current task) |
| `DONE` | Completed and verified | No |
| `PARTIAL` | Partially complete, known gaps | Yes (with caution — understand what's missing) |
| `BLOCKED` | Cannot proceed due to dependency | No (log the blocker) |
| `PRUNED` | Deliberately removed from scope | No |

### Rule 3: Parent completion requires child completion

A parent node can only be marked `DONE` when ALL of its children are `DONE`. This prevents prematurely closing a subsystem when critical pieces are still missing.

**Example:** The "Learning Pipeline" node cannot be `DONE` until all six of its children are `DONE`. Currently, "IRL refinement" is `PARTIAL`, so "Learning Pipeline" is `PARTIAL` regardless of the status of its other children.

### Rule 4: PRUNED nodes include the reason

When a node is pruned, it must include a brief annotation explaining why. This prevents the same idea from being re-explored every time someone (human or agent) looks at the tree.

**Example:** `Behavior Tree Support [PRUNED - ADR-009 chose JSON state machines]` — the reference to ADR-009 means anyone who questions the pruning can read the ADR and understand the decision.

### Rule 5: No branching in-progress work

New children can only be added to `DONE` or `PRUNED` parent nodes, not to `IN_PROGRESS` parents. This prevents scope creep on active work.

**Example:** If "Learning Pipeline" is `IN_PROGRESS`, the agent cannot add a "Neural Architecture Search" child to it. If the human wants to add it, they must wait until "Learning Pipeline" is `DONE` or `PRUNED`, or they must explicitly approve the addition with a note explaining why it's an exception.

### Rule 6: Weekly review by the human

The tree is reviewed every week by the human during the weekly 1-hour review (see Document 10, Section 4.2). The review covers:
- Status accuracy: Are all statuses correct?
- Priority accuracy: Are priorities still correct given current goals?
- New ideas: Any ideas the agent or human has proposed since the last review?
- Pruning: Any branches that should be pruned based on changing priorities?
- Blocking: Any BLOCKED nodes that can be unblocked?

---

## 4. Direction Nudging Techniques

Direction nudging is the primary mechanism for keeping the agent focused on productive work. It is a set of communication techniques that the human uses during reviews and checkpoints to redirect the agent without demoralizing it or triggering defensive behavior.

### 4.1 Priority Marking

The most fundamental nudge: ensure the tree's priorities are correct and the agent knows to follow them.

**System Prompt Addition:**

```
IDEA TREE DIRECTIVE:
You MUST always work on the highest-priority available branch in the
idea tree. If P0 tasks are available, work on P0. Only move to P1
when no P0 tasks remain. Never work on P2 or P3 unless explicitly
directed by the human.

Before starting each task, check the idea tree. Confirm the task
you're about to work on is the highest-priority available task.
If it's not, log the discrepancy and work on the highest-priority task instead.
```

### 4.2 The "Why Are You Working On This?" Check

When reviewing agent progress, if you find the agent working on a lower-priority branch while higher-priority branches are incomplete, ask directly:

**Example 1:** "I see you're implementing the fleet learning feature (P2). But the core learning pipeline (P0) still has IRL refinement marked as PARTIAL. Please focus on completing P0 branches first. We can't do fleet learning without a stable learning pipeline."

**Example 2:** "The predictive maintenance feature is interesting but it's P2. We need the basic cognitive layer done first (P0/P1). Redirect your effort to [specific P0/P1 task]."

**Example 3:** "You spent the last session working on the cloud code generation pipeline, which is P1. But the trust score (P0) still has edge cases marked as TODO. Please complete P0 items before moving to P1."

**Key principle:** Always reference the specific priority level and the specific incomplete task. Vague nudges ("focus on what's important") don't work because the agent's definition of "important" may differ from yours.

### 4.3 The "Good Idea, Wrong Time" Response

When the agent proposes a new idea or suggests working on a lower-priority branch, never say "no." Instead, say "yes, but later." This keeps the agent motivated while maintaining focus.

**Templates:**

- *"That's a great idea for v4.0. Let me add it to the tree as P3. For now, we're focused on getting v3.1 stable. Please continue with [current P0 task]."*
- *"I agree that CAN bus support would be valuable, and I've added it to the tree as P3 (v4.0 scope). RS-422 is sufficient for v3.1 per ADR-016. Please continue with the serial bridge implementation."*
- *"The neural architecture search concept is interesting. I've added it as P3 under 'Enhanced Features.' For now, the fixed learning pipeline (P0) is what we need. Continue with [current task]."*

**Why this works:** The agent's motivation system is tied to feeling productive and valued. A flat "no" can trigger the agent to argue for the idea or become less engaged. A "yes, but later" validates the idea while maintaining direction. The agent adds the idea to the tree (it's not lost) and returns to the critical path (focus is maintained).

### 4.4 The Completion Bonus

When the agent completes a significant milestone (a P0 branch), acknowledge the achievement and provide forward momentum:

**Example 1:** "Excellent work on the wire protocol. That was our biggest risk item — reliable communication between ESP32 and Jetson is the foundation of everything else. The remaining P0 items (safety system, VM) are more straightforward. You're making great progress."

**Example 2:** "The safety system is now complete and all tests pass. This is the most critical subsystem — getting it right is non-negotiable and you did. The VM (our last P0 item) should take about a week. Then we can start on the cognitive layer."

**Example 3:** "All P0 branches are now DONE. That's a major milestone. The cognitive layer (P1) is next. I've updated the task list with the P1 decomposition. The first task is the serial bridge — it's the Jetson-side counterpart to the wire protocol you just completed."

**Why this works:** Positive reinforcement for completed work correlates with higher-quality output on subsequent tasks (see Document 10, Section 8.7). The completion bonus serves two purposes: it acknowledges the achievement (motivation) and it clearly identifies the next objective (direction).

---

## 5. The Pruning Process

Not all ideas should be implemented. Pruning — deliberately removing an idea from the active scope — is a healthy and necessary part of the development process. An unpruned tree grows uncontrollably; a well-pruned tree focuses effort on the most impactful work.

### 5.1 When to Prune

**Scenario 1: Architectural Decision Conflict**
When an idea conflicts with a decided ADR, prune it immediately. Reference the ADR in the annotation.
```
Native WiFi OTA [PRUNED - ADR-007: serial flashing is more reliable
and has lower complexity. WiFi OTA reintroduces the provisioning
problem. See ADR-007 for full rationale.]
```

**Scenario 2: Exploration Showed It Wasn't Viable**
When an idea has been explored and found to be impractical, prune it with a summary of findings.
```
Lua VM [PRUNED - explored for 2 sessions. Lua adds ~40KB flash overhead,
requires a full runtime, and the introspection capabilities we need
aren't available in embedded Lua. Custom bytecode VM (32 opcodes) gives
us exactly what we need in ~8KB. See worklog entries 2024-03-15 through
2024-03-18.]
```

**Scenario 3: Priority Mismatch**
When an idea is good but doesn't align with current goals, prune it with a note about when it might become relevant.
```
CAN Bus Support [PRUNED - RS-422 is sufficient for the single-Jetson,
multi-ESP32 topology of v3.1. CAN bus becomes relevant in v4.0 when we
add multi-Jetson configurations. Keep as reference for v4.0 planning.]
```

**Scenario 4: Diminishing Returns**
When an idea keeps resurfacing but never reaches the priority threshold, prune it to stop the cycle.
```
Custom Memory Allocator [PRUNED - proposed 4 times. Each evaluation
concluded that ESP32's heap is adequate with PSRAM for large buffers.
The custom allocator would save ~2KB SRAM but adds significant complexity
and risk. Not worth it for v3.1. Revisit if SRAM becomes constrained.]
```

### 5.2 Pruning Rules

1. **Never delete pruned ideas.** They prevent re-exploration (the agent won't propose the same idea again if it sees the pruned node with a rationale) and may become relevant in future versions.
2. **Always include the reason.** A pruned node without a reason is indistinguishable from an ignored node. The reason prevents the "but why didn't we do this?" question from resurfacing.
3. **Prune aggressively.** A tree with 100 nodes of which 40 are pruned is healthier than a tree with 60 unpruned nodes that the agent has to evaluate every time it checks priorities.
4. **The human makes pruning decisions.** The agent can suggest pruning ("This idea conflicts with ADR-009; should I prune it?") but the human must confirm. This prevents the agent from pruning ideas that the human considers important.

### 5.3 The PRUNED Section

All pruned nodes live in a dedicated `[PRUNED]` section at the bottom of the tree. This section serves as a permanent record of explored-and-discarded ideas. It is invaluable for:

- **Preventing re-exploration:** When the agent (or a new team member) proposes an idea, check the pruned section first
- **Informing future decisions:** When priorities change in a future version, the pruned section contains ready-made research on ideas that were previously evaluated
- **Maintaining morale:** When the agent's idea is pruned, seeing it preserved with a clear rationale feels less like rejection and more like "filed for later"

---

## 6. Anti-Patterns

The following anti-patterns are behaviors we've observed in the agent (and, honestly, in ourselves) that the idea tree is designed to prevent.

### 6.1 The Shiny Object

**Symptom:** The agent keeps proposing new ideas instead of finishing current work. Every checkpoint report includes a "Suggested Improvements" section with 5–10 new ideas.

**Detection:** The idea tree's `[PRUNED]` section grows faster than the `[DONE]` section. The agent spends more time discussing ideas than implementing tasks.

**Fix:** 
- Add the proposed ideas to the tree as P3 (acknowledgment without action)
- Redirect: "Great ideas — I've added them all as P3. Let's get [current P0 task] done first."
- If the pattern persists, add to the system prompt: "Do not propose new ideas during implementation sessions. Focus on the current task."

### 6.2 The Perfect is the Enemy

**Symptom:** The agent keeps refining a completed feature instead of moving to the next task. A `DONE` node gets reopened for "improvements" that weren't in the original spec.

**Detection:** A node that was marked `DONE` keeps getting new children added (violating Rule 5). The agent's commit log shows repeated modifications to the same files after the feature was declared complete.

**Fix:**
- Close the node: "This feature is DONE. It meets the spec. Move on."
- If improvements are genuinely needed, add them as new nodes in the tree with appropriate priority
- Add to the system prompt: "When a feature is marked DONE, do not revisit it unless the human explicitly requests changes."

### 6.3 The Bottom-Up Spiral

**Symptom:** The agent keeps discovering dependencies and going deeper instead of implementing at the current level. Instead of implementing the VM, it discovers it needs a memory allocator, which requires a heap manager, which requires a linked list, which requires...

**Detection:** The task list grows faster than tasks are completed. The agent's worklog shows a pattern of "discovered dependency X, implementing X" entries. The tree develops very deep branches with many `IN_PROGRESS` nodes.

**Fix:**
- Enforce the dependency rule: "If you discover a dependency not in the task list, log it as BLOCKING and move to a task that doesn't have the dependency."
- During review, look for dependency spirals and flatten them: "Implement a stub/mock for the dependency and move on. We'll fill in the real implementation later."
- Add to the system prompt: "When you discover a missing dependency, DO NOT implement it. Log it and continue with tasks that don't need it."

### 6.4 Analysis Paralysis

**Symptom:** The agent keeps researching, reading, and analyzing instead of implementing. The checkpoint reports are full of "Research: [topic]" entries but few "Completed: [task]" entries.

**Detection:** The agent's context file grows rapidly (research notes) but the git commit log shows few new commits. The agent proposes more spec clarifications than code changes.

**Fix:**
- Set a research budget: "Spend at most 15 minutes researching before starting implementation. If you're still unsure after 15 minutes, log your uncertainty and implement your best interpretation."
- Redirect: "Stop researching and start implementing. If your implementation is wrong, the tests will tell you and we'll fix it in the next review."
- Add to the system prompt: "Prefer implementation over research. Write code, run tests, fix failures. Research is only productive if it leads to code changes."

### 6.5 The Monolith Builder

**Symptom:** The agent tries to implement an entire subsystem in one session instead of following the atomic task decomposition. Tasks are large (500+ lines of code), tests are comprehensive but slow, and failures are hard to debug.

**Detection:** Individual commits are large (500+ lines changed). Tasks in the task list have vague descriptions ("implement the learning pipeline" instead of "implement cross-correlation function"). The agent's time-per-task is consistently above estimate.

**Fix:**
- Enforce the atomic task rule: "Each task must produce fewer than 200 lines of code."
- During review, break large tasks into smaller ones before the next session.
- Add to the system prompt: "If a task would produce more than 200 lines of code, break it into smaller subtasks."

---

## 7. Implementing the Idea Tree

The idea tree is deliberately simple. It uses markdown, git, and nothing else. No database, no web interface, no special tooling. This simplicity is intentional — it ensures the tree is accessible to both the human and the agent, version-controlled, and easy to maintain.

### 7.1 File Structure

```
/nexus-agent/
├── idea-tree.md          # The tree itself
├── idea-tree-archive/    # Archived versions (one per month)
│   ├── idea-tree-2024-01.md
│   ├── idea-tree-2024-02.md
│   └── ...
├── context.md            # Agent's working memory
├── worklog.md            # Append-only progress log
├── task-list.md          # Current task decomposition
└── sessions/             # Autonomous session reports
```

### 7.2 Monthly Archival

At the end of each month, the current idea tree is archived and a fresh copy is started. The archive preserves the history of decisions and priorities, which is valuable for understanding how the project evolved.

**Archival procedure:**
1. Copy `idea-tree.md` to `idea-tree-archive/idea-tree-YYYY-MM.md`
2. Create a new `idea-tree.md` from the archived version, keeping all nodes but resetting statuses for the new month's work
3. Review the archived version: are any `PRUNED` ideas worth revisiting? Are any `P3` ideas worth promoting?
4. Commit both files with a message like: "Monthly idea tree archival — [month year]"

### 7.3 Integration with the Task List

The task list (`task-list.md`) is the agent's immediate work queue. It is derived from the idea tree but contains more detail:

- Each task has a specific spec reference
- Each task has a time estimate
- Each task has dependency links
- Tasks are ordered by priority and dependency

**Sync procedure (weekly):**
1. Review the idea tree for priority changes
2. Generate a new task list from the highest-priority `TODO` and `IN_PROGRESS` nodes
3. Break each node into atomic tasks (see Document 10, Section 3.2)
4. Estimate time for each task
5. Order by dependency and priority
6. Commit the new task list

### 7.4 Integration with the Checkpoint Report

The checkpoint report (see Document 10, Section 3.4) includes an "Idea Tree Updates" section where the agent logs any tree changes:

```markdown
## Idea Tree Updates
- Added: "Neural Architecture Search" under "Enhanced Features" [P3]
- Status: "IRL refinement" changed from TODO to PARTIAL [P0]
- Proposed prune: "Custom Allocator" — reason: PSRAM sufficient (awaiting human confirmation)
```

This keeps the human informed of tree changes without requiring them to read the full tree after every session.

---

## 8. When the Human Goes Off-Track

The idea tree isn't just for the agent — it's for the human too. One of the most valuable functions of the tree is keeping the human focused.

**Scenario:** You're reviewing the agent's work and you notice something that could be improved. You start writing a long review note with 8 improvement suggestions. Before you finish, you realize: 6 of those 8 suggestions are P2 or P3 ideas that have nothing to do with the current milestone.

**The tree's role:** Before writing the review note, check the idea tree. Are your improvement suggestions aligned with the current priorities? If not, add them to the tree at the appropriate priority level and focus your review on the current P0/P1 tasks.

**The principle:** The human has the same infinite-exploration problem as the agent, just in a different form. The idea tree provides the same discipline for the human that it provides for the agent: a structured, prioritized list of what matters right now versus what matters later.

---

## Appendix A: Idea Tree Template (for New Projects)

```markdown
# [Project Name] Idea Tree
## Last Updated: [Date]
## Current Milestone: [Name]

# [Project Name]
├── Phase 1: Foundation (P0)
│   ├── [Subsystem A] [TODO/P1]
│   │   ├── [Feature A1] [TODO]
│   │   └── [Feature A2] [TODO]
│   └── [Subsystem B] [TODO/P0]
│       └── [Feature B1] [TODO]
├── Phase 2: Core Features (P1)
│   └── [Subsystem C] [TODO]
├── Phase 3: Enhanced Features (P2)
│   └── [Subsystem D] [TODO]
└── [PRUNED]
    └── (pruned ideas will be collected here)

## Legend
- [TODO] Not started
- [IN_PROGRESS] Currently being worked on
- [DONE] Completed and verified
- [PARTIAL] Partially complete
- [BLOCKED] Cannot proceed (dependency)
- [PRUNED] Deliberately removed from scope

## Priority Legend
- P0: Critical path (must be done for current milestone)
- P1: Important (should be done for current milestone)
- P2: Nice-to-have (improves quality but not required)
- P3: Future (interesting but not aligned with current goals)
```

## Appendix B: Quick Reference — Nudging Commands

| Situation | Nudge |
|-----------|-------|
| Agent working on P2 while P0 is incomplete | "Focus on [specific P0 task]. [P2 task] is P2 and can wait." |
| Agent proposes new feature | "Great idea. Added as P3. Continue with [current task]." |
| Agent keeps refining a DONE feature | "This feature is DONE per spec. Move to the next task." |
| Agent is stuck on a dependency | "Log the dependency as BLOCKING. Continue with tasks that don't need it." |
| Agent is researching too much | "15 minutes max research. Implement your best interpretation. Tests will tell us if it's wrong." |
| Agent completed a P0 milestone | "Excellent work. [Milestone] is done. Next: [next P0 task]." |
| Agent going down a rabbit hole | "This isn't in the spec. Stop and return to [current task]." |
| Agent's implementation diverges from spec | "The spec says [X]. Your implementation does [Y]. Please follow the spec." |
