---
name: run-orchestration
description: "Execute a prepared orchestration plan from .orchestration/config.yaml. Reads the YAML config, validates it, then executes slice-by-slice: creates branches, dispatches specialized worker agents, enforces quality gates, creates Linear issues, and delivers one PR per slice. Use when the user says 'run-orchestration', 'execute orchestration', or has a prepared .orchestration/config.yaml ready to run."
version: 1.0.0
---

# Run Orchestration

Read `.orchestration/config.yaml`, validate it, and execute slice-by-slice. Each slice produces one branch, one set of Linear issues, and one PR.

**Core principle: work flows down, state flows up, chaos is contained.**

```
.orchestration/config.yaml (user-reviewed)
        │
        ▼
┌───────────────────────┐
│  run-orchestration     │
│                        │
│  For each slice:       │
│  1. Create branch      │
│  2. Create Linear issues│
│  3. Dispatch workers   │
│  4. Quality gates      │
│  5. Build + test       │
│  6. Create PR          │
│  7. Update state       │
└───────────┬───────────┘
            ▼
    Per-slice PRs delivered
```

## Agent Roles

| Agent | Role | Implemented By |
|-------|------|----------------|
| **Orchestrator** | User-facing executive. Loads config, delivers PRs | Main agent (you) |
| **Manager** | Dispatches workers per slice, tracks state | Main agent (you) |
| **Tech Lead** | Reviews architecture and code quality. Veto power | `code-reviewer` subagent |
| **QA Lead** | Monitors patterns, drift, systemic quality | `qa-engineer` subagent |
| **Workers** | Ephemeral execution units. One task, report, die | Typed subagents (see config) |
| **Merge/Ship** | Validates build, creates PR per slice | Main agent |

For full agent definitions and output contracts, see [references/agents.md](references/agents.md).

## Prerequisites

Before executing, validate quickly (these were checked in depth by `orchestration-setup`):

| Check | Command | What to verify |
|-------|---------|----------------|
| **Config exists** | Read `.orchestration/config.yaml` | File exists and is valid YAML |
| **Git clean** | `git status --porcelain` | Working directory is clean (warn if dirty) |
| **Platform CLI** | `gh auth status` or `az devops project show --detect` | Still authenticated |
| **Linear CLI** | `linctl --version` | If `platform.linear` is configured |

**If config is missing:** Tell the user to run `/orchestration-setup` first. Do not proceed.

## Config Validation

On load, validate the YAML against the schema. Report errors with field paths and descriptions:

1. `version` must be `"1.0"`
2. `source.type` must be one of: `linear`, `notion`, `file`, `inline`
3. `mandate.objective` must be non-empty
4. `mandate.acceptance_criteria` must have at least one entry
5. `slices` must have at least one slice
6. Each slice must have at least one issue with at least one task
7. Task IDs unique within each slice
8. `depends_on` references resolve within the same issue
9. `size` is `"small"` or `"medium"`
10. `worker_persona` maps to a known persona
11. `iteration_budget` is a positive integer

On validation failure, report the specific errors and stop. Example:
```
Config validation failed:
  - slices[1].issues[0].tasks[2].depends_on: "T099" does not exist in this issue
  - slices[2].issues[0].tasks[0].size: "large" is not valid (use "small" or "medium")
Fix .orchestration/config.yaml and re-run.
```

## Skill Resolution

The `skills:` section in the config maps roles to editable skills. On load, resolve each skill reference:

1. **Read `config.skills`** — apply defaults for any missing keys:
   - `task_execution` → `"task-execution"`
   - `tech_lead_review` → `"code-review-gate"`
   - `qa_lead_review` → `"qa-review-gate"`
   - `ticket_creation` → `null`

2. **Resolve skill paths** for each non-null value:
   - Plain name (e.g., `"task-execution"`): search `~/.cursor/skills/{name}/SKILL.md`, then `.cursor/skills/{name}/SKILL.md`
   - `adlc:` prefix (e.g., `"adlc:executing-tasks"`): resolve from `~/.claude/plugins/cache/AgenticEngineeringAcademy/adlc/*/skills/{name}/SKILL.md`

3. **Read each resolved skill** — cache the content for use in dispatch prompts. If a skill can't be found, warn the user but don't block (fall back to the role's built-in behavior from [references/agents.md](references/agents.md)).

4. **Include resolved skills in execution plan output** (see below).

## Execution Protocol

### Phase 1: Load and Validate

1. **Read `.orchestration/config.yaml`**
2. **Validate** against schema (see above)
3. **Resolve skills** (see Skill Resolution above)
4. **Load state** — if `.orchestration/state.yaml` exists, check for resume (see Resumption below)
5. **Quick prerequisite check** — verify CLI tools still authenticated
6. **Print execution plan** — summary of what will be executed:

```
## Execution Plan

Config: .orchestration/config.yaml
Source: CAL-123 — Add batch cancellation support
Slices to execute: 3
Skills:
  Task execution: task-execution
  Tech Lead review: code-review-gate
  QA Lead review: qa-review-gate

  Slice 1: Foundation — batch state infrastructure (6 iterations, 3 tasks)
  Slice 2: Cancel endpoint and events (10 iterations, 4 tasks)
  Slice 3: Integration tests (6 iterations, 1 task)

Proceeding with Slice 1...
```

### Phase 2: Slice Execution Loop

For each slice in order:

#### 2a. Branch Setup

6. **Determine branch name:**
   - From Linear ticket: `feature/<TICKET-ID>-<branch_suffix>` (e.g., `feature/CAL-123-batch-state-infrastructure`)
   - From other sources: `feature/orchestrate-<branch_suffix>`

7. **Create branch:**
   - Default: branch from `platform.default_branch`
   - Stacked option: if previous slice's PR is not yet merged, branch from previous slice's branch
   - Run `git checkout -b <branch-name>` from the appropriate base

#### 2b. Linear Issue Creation

8. **Create Linear issues** for this slice (if `platform.linear` is configured):
   - For each issue in `slices[N].issues`:
     - Create via `linctl issue create --title "..." --team <team> --parent <parent_issue>` (preferred)
     - Or via Linear MCP `save_issue` (fallback)
     - Apply labels from `issues[].labels`
     - Store created issue IDs in runtime state
   - If `platform.linear` is null, skip all Linear operations

#### 2c. Task Dispatch Loop

9. **Initialize task graph** from slice's issues and tasks:
   - Write all tasks to `TodoWrite` with initial states
   - Respect `depends_on` ordering within each issue
   - Issues are processed in order (issue 1's tasks before issue 2's where dependencies exist)

10. **Dispatch workers** respecting:
    - Dependency order (`depends_on` tasks must be `completed`)
    - Burn rate (max `workers.max_concurrent` concurrent, default 4)
    - Iteration budget for this slice

11. **For each dispatch batch:**
    - **Read the resolved `skills.task_execution` skill** and include its instructions in the worker prompt
    - Spawn worker subagents with full context (task description, AC, relevant code paths, completed work outputs, skill instructions)
    - Workers NEVER get vague instructions — include everything they need, including the skill's process and output format
    - Mark dispatched tasks as `in_progress` in TodoWrite
    - Use `run_in_background: true` for parallel workers

12. **Process worker reports:**
    - On success: mark `completed`, unlock dependent tasks, queue next dispatch
    - On failure: evaluate — re-queue with more context, break into sub-tasks, or escalate
    - **N failures on same task (N = `circuit_breakers.max_task_retries`) = mandatory Tech Lead review**

13. **Commit completed work** after each approved batch:
    - Stage changes with `git add`
    - Commit with descriptive message: `feat(<scope>/T001): <description>`
    - If from Linear: include ticket ID: `feat(CAL-123/T001): <description>`
    - Keep commits logically grouped

14. **Quality gates** (using resolved skills from config):
    - After each batch: dispatch `code-reviewer` subagent using the resolved `skills.tech_lead_review` skill's process and output format (if `quality_gates.tech_lead_review` is true)
    - Every N batches (N = `quality_gates.qa_lead_review_interval`): dispatch `qa-engineer` subagent using the resolved `skills.qa_lead_review` skill's process and output format
    - Adjust based on Tech Lead/QA Lead feedback

15. **Evaluate circuit breakers** at each iteration boundary:
    - Check stall, failure cascade, drift, infinite loop thresholds
    - If tripped: pause, report to user, write state, wait for instructions

16. **Loop** steps 10-15 until:
    - All tasks in slice complete, OR
    - Iteration budget exhausted, OR
    - Circuit breaker trips

For full iteration control details, see [references/iteration-control.md](references/iteration-control.md).

#### 2d. Slice Assembly and PR

17. **Run integration validation** for this slice:
    - `quality_gates.build_command` (if set)
    - `quality_gates.test_command` (if set)
    - `quality_gates.lint_command` (if set)
    - Fix any integration issues between parallel work streams

18. **Final Tech Lead review** on the assembled slice (using resolved `skills.tech_lead_review` skill)

19. **Push branch:** `git push -u origin HEAD`

20. **Create PR** using platform CLI:
    - **GitHub:** `gh pr create --title "<slice name>" --body "<PR body>"`
    - **Azure DevOps:** `az repos pr create --title "<slice name>" --description "<PR body>" --source-branch "<branch>" --detect`

    **PR body format:**
    ```markdown
    ## Summary
    <1-3 sentence description of what this slice delivers>

    **Source:** <Linear ticket link | plan file | description>
    **Slice:** <N of M> — <slice name>

    ## Changes
    <Bulleted list of what was built/changed>

    ## Task Completion
    | Task | Status | Description |
    |------|--------|-------------|
    | T001 | Done | <title> |
    | T002 | Done | <title> |

    ## Linear Issues
    | Issue | Status |
    |-------|--------|
    | CAL-124 | Done |
    | CAL-125 | Done |

    ## Validation
    - Build: PASS/FAIL
    - Tests: X/Y passed
    - Lint: PASS/FAIL

    ## Notes
    <Caveats, known issues, follow-up items>
    ```

21. **Update Linear issues** for this slice:
    - Move issues to "Done" or "In Review"
    - Add comment with PR URL to each issue
    - Add comment with PR URL to parent issue

22. **Update state file** — mark slice as complete

23. **Report slice completion** to user:
    ```
    ## Slice 1 Complete: Foundation — batch state infrastructure

    PR: https://github.com/org/repo/pull/42
    Tasks: 3/3 complete
    Linear issues: CAL-124, CAL-125 (updated)
    Build: PASS | Tests: 12/12 | Lint: PASS

    Proceeding to Slice 2...
    ```

#### 2e. Next Slice

24. **Return to step 6** for the next slice
25. **Branch strategy for next slice:**
    - If previous slice's PR is merged: branch from `default_branch` (pull latest)
    - If previous slice's PR is open: option to stack (branch from previous slice's branch) or branch from `default_branch`
    - Ask user if unclear

### Phase 3: Completion

26. **Final report** after all slices:

```
## Orchestration Complete

**Source:** CAL-123 — Add batch cancellation support
**Slices delivered:** 3/3

| Slice | PR | Status |
|-------|----|--------|
| Foundation — batch state infrastructure | #42 | Ready for review |
| Cancel endpoint and events | #43 | Ready for review |
| Integration tests | #44 | Ready for review |

**Total tasks:** 8/8 complete
**Linear parent issue:** CAL-123 (updated with all PR links)
```

## State Management

### `.orchestration/state.yaml`

Written after each slice completes. Enables resume if interrupted.

```yaml
version: "1.0"
config_hash: "<sha256 of config.yaml>"  # Detect if config changed
started_at: "2025-01-15T10:30:00Z"
last_updated: "2025-01-15T11:45:00Z"

slices:
  - name: "Foundation — batch state infrastructure"
    status: "completed"
    branch: "feature/CAL-123-batch-state-infrastructure"
    pr_url: "https://github.com/org/repo/pull/42"
    pr_number: 42
    linear_issues:
      - id: "CAL-124"
        title: "Batch State Enum and Transitions"
        status: "done"
    iterations_used: 4
    tasks_completed: 3
    tasks_total: 3

  - name: "Cancel endpoint and events"
    status: "in_progress"
    branch: "feature/CAL-123-cancel-endpoint"
    pr_url: null
    linear_issues:
      - id: "CAL-125"
        title: "Cancel API Endpoint"
        status: "in_progress"
    iterations_used: 6
    current_iteration: 7
    tasks_completed: 2
    tasks_total: 4
    task_states:
      T001: "completed"
      T002: "completed"
      T003: "in_progress"
      T004: "queued"

  - name: "Integration tests"
    status: "pending"
```

### Resumption

When invoked with `--resume` or when `state.yaml` exists:

1. **Load state.yaml** and config.yaml
2. **Check config hash** — if config changed since last run, warn user and ask whether to continue with new config or abort
3. **Find first non-completed slice** — resume from there
4. **Within that slice:** restore task states, skip completed tasks, re-dispatch in-progress tasks
5. **Continue normal execution** from that point

**Invocation:**
```
run-orchestration              # Normal run (or resume if state exists)
run-orchestration --resume     # Explicit resume
run-orchestration --restart    # Ignore state, start fresh
```

## Concurrency Rules

- **Maximum `workers.max_concurrent` parallel Task subagents** per dispatch batch (default: 4)
- Use `run_in_background: true` for parallel workers
- Poll background agents by reading their output files
- Use `TodoWrite` as the task graph state store

### Task State → Todo State

| Task Graph State | TodoWrite Status |
|------------------|------------------|
| `queued` | `pending` |
| `in_progress` | `in_progress` |
| `done` | `completed` |
| `blocked` | `pending` (with blocker noted in content) |
| `failed` / `dead` | `cancelled` (with failure details in content) |

## Guardrails Summary

Circuit breakers that auto-pause execution (thresholds from config):

| Breaker | Default Trigger | Action |
|---------|----------------|--------|
| Stall | 3 iterations with 0 completions | Pause + escalate to user |
| Failure Cascade | >50% failure rate for 2 iterations | Pause + Tech Lead review |
| Drift | QA reports off-track for 2 iterations | Pause + escalate to user |
| Infinite Loop | Same task fails 3+ times | Mark dead, continue or escalate |

## Invocation

```
run-orchestration                              # Full execution (or resume if state exists)
run-orchestration --resume                     # Explicit resume from state
run-orchestration --restart                    # Ignore state, start fresh
run-orchestration --slice 2                    # Execute only slice 2
run-orchestration --slice 1 --budget 4         # Slice 1 with custom iteration budget (overrides config)
run-orchestration --slice 1 --dry-run          # Validate config + show what would execute, don't run
```

### Flags

| Flag | Effect |
|------|--------|
| `--slice N` | Execute only slice N (1-indexed). Useful for testing one slice before full run |
| `--budget N` | Override the slice's `iteration_budget` from config. Controls how many dispatch-execute-review cycles run |
| `--resume` | Explicitly resume from `.orchestration/state.yaml` |
| `--restart` | Ignore saved state, start fresh |
| `--dry-run` | Validate config, resolve skills, print execution plan, but don't execute |

### Progression from `dev`

The `dev` skill uses the same sub-skills in a single pass. Once `dev` produces good results, scale up:

```
dev plan "feature description"                 # Test planning skill
dev "feature description" --tdd               # Full single-pass with TDD
run-orchestration --slice 1 --budget 4         # One slice, limited iterations
run-orchestration --slice 1                    # One slice, full budget
run-orchestration                              # All slices
```

For detailed execution examples, see [references/examples.md](references/examples.md).

## Reference Files

- [references/agents.md](references/agents.md) — Agent role definitions and dispatch rules (skills define the HOW)
- [references/iteration-control.md](references/iteration-control.md) — Iteration modes, lifecycle, circuit breakers, resumption protocol
- [references/examples.md](references/examples.md) — Execution examples showing YAML → PRs

## Default Sub-Skills

These skills define HOW each role works. Edit them independently or swap via `config.skills`:

| Role | Default Skill | What It Defines |
|------|--------------|-----------------|
| Worker task execution | `task-execution` | How workers implement and verify tasks |
| Tech Lead review | `code-review-gate` | Review criteria, output format, severity definitions |
| QA Lead assessment | `qa-review-gate` | Health report format, pattern detection, drift assessment |
