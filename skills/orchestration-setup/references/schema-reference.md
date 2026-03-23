# YAML Config Schema Reference

Complete schema documentation for `.orchestration/config.yaml`. This is the shared config consumed by both `dev` (single-pass) and `run-orchestration` (multi-slice). One file, two workflows.

| Section | `dev` | `run-orchestration` |
|---------|-------|---------------------|
| `skills` | Reads for skill defaults | Reads for skill defaults |
| `quality_gates` | Reads for verification commands | Reads for verification commands |
| `dev_state` | Reads/writes phase state for cascading | Ignored |
| `slices` | Ignored | Required — defines work units |
| `circuit_breakers` | Ignored | Reads for guardrails |
| `workers` | Ignored | Reads for concurrency config |
| `source`, `mandate`, `platform` | Ignored | Required — defines context |

## Top-Level Structure

```yaml
version: "1.0"          # Schema version (required)
source: {}               # Where the work came from (run-orchestration)
mandate: {}              # What to build (run-orchestration)
platform: {}             # Git and PM tool configuration (run-orchestration)
slices: []               # Decomposed work units (run-orchestration only)
quality_gates: {}        # Build/test/lint commands (both)
circuit_breakers: {}     # Automatic pause thresholds (run-orchestration)
skills: {}               # Skill references for each role (both)
workers: {}              # Concurrency and persona config (run-orchestration)
dev_state: {}            # Phase state for dev cascading (dev only)
```

## `version`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | yes | Always `"1.0"` for this schema version |

## `source`

Where the work originated. Used for traceability in PRs and Linear comments.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | One of: `"linear"`, `"notion"`, `"file"`, `"inline"` |
| `ref` | string | yes | Source reference: ticket ID, URL, file path, or description |
| `raw_title` | string | yes | Original title from the source, unmodified |

```yaml
source:
  type: "linear"
  ref: "CAL-123"
  raw_title: "Add batch cancellation support to CalcEngine"
```

## `mandate`

The normalized objective derived from the source. Editable — the user can refine before execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objective` | string | yes | Clear, concise goal statement |
| `constraints` | list[string] | no | Technical, scope, or time constraints |
| `acceptance_criteria` | list[string] | yes | What "done" looks like for the entire effort |
| `context` | list[string] | no | Domain knowledge, codebase references, architectural decisions |
| `escalation_policy` | string | no | When to pause and ask the user. Default: `"Pause and ask user on any ambiguity"` |

```yaml
mandate:
  objective: "Add batch cancellation support allowing users to cancel running batches"
  constraints:
    - "Workers must finish current job before honoring cancellation"
    - "Cancellation must be idempotent"
  acceptance_criteria:
    - "PATCH /v1/api/batches/{id}/cancel returns 200 and transitions batch to Cancelling"
    - "Workers detect cancellation via health endpoint within 30s"
    - "All existing tests continue to pass"
  context:
    - "Batch states: Submitted, Running, Completed, Failed"
    - "Workers poll health endpoint every 30s"
  escalation_policy: "Pause and ask user on any ambiguity"
```

## `platform`

Git remote and project management tool configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `git_remote` | string | yes | One of: `"github"`, `"azure-devops"` |
| `cli_tool` | string | yes | CLI tool name: `"gh"` or `"az"` |
| `default_branch` | string | yes | Default branch name (auto-detected) |
| `linear` | object\|null | no | Linear integration config. Set to `null` to disable |

### `platform.linear`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `team` | string | yes | Linear team identifier (e.g., `"OLDALM"`) |
| `project` | string | no | Linear project name to associate issues with |
| `parent_issue` | string | no | Parent issue ID — new issues created as children |

```yaml
platform:
  git_remote: "github"
  cli_tool: "gh"
  default_branch: "main"
  linear:
    team: "OLDALM"
    project: "ALM Testing Framework Pyramid"
    parent_issue: "CAL-123"
```

## `slices`

**Required by `run-orchestration`. Ignored by `dev`.**

The core of the orchestration config. Each slice represents one independently shippable unit of work that produces one PR.

**Key design decisions:**
- 1 slice = 1 PR = 1 feature branch
- Slices are ordered by dependency — slice N may depend on slice N-1 being merged
- Each slice contains 1+ issues; each issue contains 1+ tasks

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable slice name |
| `branch_suffix` | string | yes | Appended to base branch name (slugified) |
| `iteration_budget` | integer | yes | Max iterations for this slice |
| `issues` | list[issue] | yes | Linear issues within this slice (min 1) |

### `slices[].issues`

Each issue maps to a Linear issue that will be created by `run-orchestration`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Issue title (appears in Linear) |
| `description` | string | no | Issue description |
| `labels` | list[string] | no | Labels to apply in Linear |
| `acceptance_criteria` | list[string] | no | Issue-level acceptance criteria |
| `tasks` | list[task] | yes | Implementation tasks (min 1) |

### `slices[].issues[].tasks`

Individual work units dispatched to worker agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Local task ID within the slice (e.g., `"T001"`) |
| `title` | string | yes | Short task description |
| `worker_persona` | string | yes | Persona from worker mapping table |
| `depends_on` | list[string] | no | Task IDs this task depends on (within same issue) |
| `size` | string | yes | One of: `"small"`, `"medium"`. No large tasks — break them |
| `acceptance_criteria` | string | yes | What "done" looks like for this task |

```yaml
slices:
  - name: "Foundation — batch state infrastructure"
    branch_suffix: "batch-state-infrastructure"
    iteration_budget: 6
    issues:
      - title: "Batch State Enum and Transitions"
        description: "Add Cancelling and Cancelled states to BatchStatus"
        labels: ["backend", "domain"]
        acceptance_criteria:
          - "New states exist in enum"
          - "State machine validates transitions"
        tasks:
          - id: "T001"
            title: "Add Cancelling/Cancelled to BatchStatus enum"
            worker_persona: "backend_engineer"
            depends_on: []
            size: "small"
            acceptance_criteria: "Enum includes new states, existing code compiles"
          - id: "T002"
            title: "Implement state transition validation"
            worker_persona: "backend_engineer"
            depends_on: ["T001"]
            size: "small"
            acceptance_criteria: "Invalid transitions throw, valid transitions succeed"
```

## `quality_gates`

Commands run to validate each slice before PR creation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tech_lead_review` | boolean | no | Dispatch code-reviewer after each batch. Default: `true` |
| `qa_lead_review_interval` | integer | no | QA review every N iterations. Default: `3` |
| `build_command` | string | no | Build validation command (e.g., `"dotnet build"`, `"just build"`) |
| `test_command` | string | no | Test validation command (e.g., `"dotnet test"`, `"just test"`) |
| `lint_command` | string\|null | no | Lint command. `null` to skip |

```yaml
quality_gates:
  tech_lead_review: true
  qa_lead_review_interval: 3
  build_command: "dotnet build"
  test_command: "dotnet test"
  lint_command: null
```

## `circuit_breakers`

Automatic guardrails that pause execution when things go wrong.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stall_threshold` | integer | no | Iterations with 0 completions before pause. Default: `3` |
| `failure_cascade_threshold` | float | no | Failure rate that triggers pause. Default: `0.5` (50%) |
| `failure_cascade_window` | integer | no | Consecutive iterations for cascade check. Default: `2` |
| `max_task_retries` | integer | no | Retries before marking task dead. Default: `3` |
| `drift_alarm_window` | integer | no | Consecutive off-track QA reports before pause. Default: `2` |

```yaml
circuit_breakers:
  stall_threshold: 3
  failure_cascade_threshold: 0.5
  failure_cascade_window: 2
  max_task_retries: 3
  drift_alarm_window: 2
```

## `skills`

Skill references that control HOW each role performs its work. Each value is a skill name resolved from `~/.cursor/skills/`, `.cursor/skills/`, or ADLC plugin skills via `adlc:` prefix. Set to `null` to disable a role.

Both `dev` and `run-orchestration` read this section. Fields marked with a workflow indicator show which skill consumes them.

| Field | Type | Default | Used By | Description |
|-------|------|---------|---------|-------------|
| `plan` | string\|null | `"dev-plan"` | `dev` | Skill for implementation planning (Phase 2) |
| `review` | string\|null | `"dev-review"` | `dev` | Skill for code review (Phase 4) |
| `task_execution` | string\|null | `"task-execution"` | both | Skill for executing individual tasks |
| `tech_lead_review` | string\|null | `"code-review-gate"` | `run-orchestration` | Skill for Tech Lead quality gates |
| `qa_lead_review` | string\|null | `"qa-review-gate"` | both | Skill for QA health assessments |
| `ticket_creation` | string\|null | `null` | `run-orchestration` | Skill for creating PM tickets (null = built-in) |

**Default config (general-purpose):**

```yaml
skills:
  # Used by dev (single-pass)
  plan: "dev-plan"
  review: "dev-review"

  # Used by run-orchestration (multi-slice) — also available to dev via flags
  task_execution: "task-execution"
  tech_lead_review: "code-review-gate"
  qa_lead_review: "qa-review-gate"
  ticket_creation: null
```

**Override example (ADLC TDD workflow):**

```yaml
skills:
  plan: "adlc:technical-planning"                   # ADLC planning process
  review: "adlc:requesting-code-review"             # ADLC review process
  task_execution: "adlc:executing-tasks"            # Strict TDD (RED-GREEN-REFACTOR)
  tech_lead_review: "adlc:requesting-code-review"   # ADLC review for orchestration
  qa_lead_review: "qa-review-gate"                  # Keep default
  ticket_creation: "adlc:creating-tickets"           # ADLC ticket format
```

**Minimal config (dev only — no slices needed):**

```yaml
version: "1.0"
skills:
  plan: "dev-plan"
  review: "code-review-gate"
  task_execution: "adlc:executing-tasks"
quality_gates:
  test_command: "just test"
  lint_command: "just lint"
```

**Skill resolution order:**
1. `~/.cursor/skills/{name}/SKILL.md` (personal skills)
2. `.cursor/skills/{name}/SKILL.md` (project skills)
3. For `adlc:` prefix: ADLC plugin cache at `~/.claude/plugins/cache/AgenticEngineeringAcademy/adlc/*/skills/{name}/SKILL.md`

## `workers`

Worker agent concurrency and persona configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `max_concurrent` | integer | no | Max parallel worker agents. Default: `4` |
| `persona_mapping` | object | no | Override persona → subagent type mapping |

```yaml
workers:
  max_concurrent: 4
  persona_mapping:
    backend_engineer: "backend-engineer"
    frontend_engineer: "frontend-engineer"
    devops_engineer: "platform-engineer"
    qa_engineer: "qa-engineer"
    domain_expert: "generalPurpose"
    database_engineer: "backend-engineer"
    security_engineer: "code-reviewer"
```

## `dev_state`

**Written by `dev`. Ignored by `run-orchestration`.**

Lightweight state for cascading between `dev` phases across sessions. The full plan lives in a separate markdown file (`.orchestration/plan.md`); this section stores only references, phase status, and summaries.

| Field | Type | Written By | Description |
|-------|------|-----------|-------------|
| `phase` | string | All phases | Current state: `"plan_complete"`, `"implement_complete"`, `"review_complete"`, `"qa_complete"` |
| `objective` | string | `dev plan` | The original description/objective (1-2 sentences) |
| `plan_file` | string | `dev plan` | Path to the full plan: `.orchestration/plan.md` |
| `linear_issue` | string\|null | `dev plan` | Parent Linear issue ID if `--linear` was used, null otherwise |
| `linear_children` | list[string] | `dev plan` | Child Linear issue IDs (one per implementation phase), empty if no `--linear` |
| `flags` | object | `dev plan` | Resolved flags for consistency across phases |
| `flags.tdd` | boolean | `dev plan` | Whether TDD mode is active |
| `flags.qa` | boolean | `dev plan` | Whether QA pass is enabled |
| `flags.plan_skill` | string | `dev plan` | Resolved planning skill name |
| `flags.review_skill` | string | `dev plan` | Resolved review skill name |
| `flags.linear_project` | string\|null | `dev plan` | Linear project name if specified |
| `review` | object\|null | `dev review` | Review summary (slim -- detail is in conversation/diff) |
| `review.verdict` | string | `dev review` | `"approved"` or `"needs_revision"` |
| `review.finding_count` | integer | `dev review` | Number of findings |
| `qa` | object\|null | `dev qa` | QA summary |
| `qa.on_track` | boolean | `dev qa` | Whether the work is on track |
| `qa.summary` | string | `dev qa` | 1-sentence health assessment |

```yaml
dev_state:
  phase: "plan_complete"
  objective: "Add caching layer to reduce database load"
  plan_file: ".orchestration/plan.md"
  linear_issue: "PROJ-100"
  linear_children:
    - "PROJ-101"
    - "PROJ-102"
    - "PROJ-103"
    - "PROJ-104"
  flags:
    tdd: false
    qa: true
    plan_skill: "dev-plan"
    review_skill: "dev-review"
    linear_project: "ALM Testing Framework Pyramid"
  review:
    verdict: "needs_revision"
    finding_count: 3
  qa:
    on_track: true
    summary: "Implementation follows plan. High-severity finding addressed."
```

**The full plan** lives in `.orchestration/plan.md`. In local mode this is the full plan; in Linear mode it's a summary with links to the Linear issues (the detail lives in issue descriptions).

**Lifecycle:**
1. `dev plan "X"` → writes `.orchestration/plan.md` + slim `dev_state`. If `--linear`, decomposes plan into parent + child Linear issues and stores IDs.
2. `dev implement` → reads plan from `.orchestration/plan.md`, updates `phase: "implement_complete"`. If linear, moves issues to "In Progress".
3. `dev review` → reads objective from `dev_state`, writes `review` summary. If linear, adds comment on parent.
4. `dev qa` → reads objective + review from `dev_state`, writes `qa` summary. If linear, adds comment and moves parent to "Done".
5. `dev "X"` (full pipeline) → writes state at each phase transition.
6. Next `dev plan "Y"` → overwrites `dev_state` and `plan.md` (fresh start). Existing Linear issues are not deleted.

## Validation Rules

### Shared (both `dev` and `run-orchestration`)

1. `version` must be `"1.0"`
2. `skills.*` values must be non-empty strings or `null`
3. `skills.*` string values must resolve to an existing skill (warn if not found, don't block)

### `run-orchestration` only

4. `source.type` must be one of: `linear`, `notion`, `file`, `inline`
5. `mandate.objective` must be non-empty
6. `mandate.acceptance_criteria` must have at least one entry
7. `slices` must have at least one slice
8. Each slice must have at least one issue
9. Each issue must have at least one task
10. Task IDs must be unique within a slice
11. `depends_on` references must resolve to task IDs within the same issue
12. `size` must be `"small"` or `"medium"`
13. `worker_persona` must be a key in `workers.persona_mapping`
14. `iteration_budget` must be a positive integer

### `dev` only

`dev` reads `skills:`, `quality_gates:`, and `dev_state:` sections. Missing sections use built-in defaults. No validation errors — just defaults. `dev_state` is always overwritten (not merged) when `dev plan` runs.
