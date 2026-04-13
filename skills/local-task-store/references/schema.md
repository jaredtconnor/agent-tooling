# Local Task Store Schema Reference

## config.yaml

The config file holds the task breakdown. Written by `breakdown` in local mode, read by `execution`.

```yaml
version: "1.0"

# Where the work came from
source:
  type: "linear"              # linear | inline | file
  ref: "FEAT-100"             # Linear issue ID, description, or file path
  raw_title: "Add user authentication"

# What to build (pulled from Linear spec or provided inline)
mandate:
  objective: "Add user authentication with email/password"
  constraints:
    - "Must support OAuth2 in future"
    - "Session tokens expire after 24h"
  acceptance_criteria:
    - "Users can register with email/password"
    - "Users can log in and receive JWT"
    - "Invalid credentials return 401"
  context:
    - "Existing User model in models/user.py"
    - "API follows REST conventions in routes/"

# Platform and sync configuration
platform:
  git_remote: "github"            # github | azure-devops
  cli_tool: "gh"                  # gh | az — CLI tool for PR operations
  default_branch: "main"
  linear:                         # Set to null to disable all Linear sync
    team: "ENG"                   # Linear team key
    project: "My Project"         # Linear project name (optional)
    parent_issue: "FEAT-100"      # Parent issue stays in Linear
    sync_phases: true             # Create/update phase-level issues in Linear
    sync_tasks: false             # NEVER push task-level to Linear (key setting)

# Full task breakdown — phases with tasks
phases:
  - name: "Register a user"
    branch_suffix: "phase-1-register"
    label: "feature"                     # feature | chore | bug — determines Tier 3 routing
    linear_issue: "FEAT-101"             # Optional: phase-level Linear issue for PM visibility
    scope: "After this phase, users can register with email/password"
    whats_demoable:
      - "User fills out registration form"
      - "Form validates and shows errors"
      - "Successful submission creates user record"
    acceptance_criteria:
      - "POST /api/users with valid data -> 201, user in DB"
      - "Missing fields -> 422 with validation errors"
      - "Duplicate email -> 409"
    tasks:
      - id: "T001"
        title: "Add users table migration"
        worker_persona: "backend_engineer"    # Maps to subagent type
        depends_on: []                        # Task IDs within same phase
        size: "small"                         # small | medium (no large)
        acceptance_criteria: "Migration applies (table exists), rolls back (table gone)"
        files:
          - "db/migrations/"
        tests:
          - "test_migration_applies"
          - "test_migration_rollback"
        reference_examples:
          - "db/migrations/001_initial.py"
      - id: "T002"
        title: "Implement User model"
        worker_persona: "backend_engineer"
        depends_on: ["T001"]
        size: "small"
        acceptance_criteria: "User model with email validation and password hashing"
        files:
          - "models/user.py"
        tests:
          - "test_create_valid_user"
          - "test_email_required"
          - "test_password_hashed"
          - "test_email_unique"
        reference_examples:
          - "models/base.py"
      - id: "T003"
        title: "Implement POST /api/users endpoint"
        worker_persona: "backend_engineer"
        depends_on: ["T002"]
        size: "medium"
        acceptance_criteria: "Register endpoint with validation, error handling"
        files:
          - "routes/users.py"
          - "routes/__init__.py"
        tests:
          - "test_register_201"
          - "test_missing_fields_422"
          - "test_duplicate_email_409"
          - "test_invalid_email_422"
        reference_examples:
          - "routes/health.py"
    parallelisation_notes: "T001 before T002 (creates table). T002 before T003 (imports model)."
    dependencies:
      blocked_by: []
      blocks: ["Phase 2: Log in"]

  - name: "Log in"
    branch_suffix: "phase-2-login"
    label: "feature"
    linear_issue: "FEAT-102"
    scope: "After this phase, users can log in and receive a JWT"
    # ... (same structure as above)

# Quality gates — verification commands
quality_gates:
  test_command: "just test"
  lint_command: "just lint"
  build_command: "just build"
  tech_lead_review: true
  qa_lead_review_interval: 3

# Skill overrides
skills:
  plan: "dev-plan"
  review: "dev-review"
  task_execution: "task-execution"           # or "adlc:executing-tasks" for TDD
  tech_lead_review: "code-review-gate"
  qa_lead_review: "qa-review-gate"

# Circuit breakers — automatic pause thresholds
circuit_breakers:
  stall_threshold: 3                # Iterations with 0 completions → pause
  failure_cascade_threshold: 0.5    # >50% failure rate → pause
  failure_cascade_window: 2         # Over consecutive iterations
  max_task_retries: 3               # Retries before marking task dead

# Worker concurrency (for team strategy)
workers:
  max_concurrent: 4
  persona_mapping:
    backend_engineer: "backend-engineer"
    frontend_engineer: "frontend-engineer"
    devops_engineer: "platform-engineer"
    qa_engineer: "qa-engineer"
    database_engineer: "backend-engineer"
    security_engineer: "code-reviewer"

# Workflow state — persists issue context and flags across commands
dev_state:
  phase: "plan_complete"             # refine_complete | plan_complete | breakdown_complete | execute_complete
  issue_id: "ALM-153"               # Current issue being worked on
  objective: "1-2 sentence summary"
  spec_file: "specs/spec-alm-153.md"    # Relative path (from .agents/) to active spec file. Null if spec is in Linear only.
  plan_file: "plans/plan-alm-153.md"    # Relative path (from .agents/) to active plan file. Null if plan is in Linear only.
  flags:
    local: false                     # true if --local was used — persisted across commands
    strategy: null                   # Persisted --strategy flag (execute only)
```

### Validation Rules

- `version` must be `"1.0"`
- `phases` must have at least one entry
- Each phase must have `name`, `label`, `tasks[]`
- Each task must have `id`, `title`, `worker_persona`, `size`
- Task `id` must be unique within a phase
- `depends_on` must reference task IDs within the same phase
- `size` must be `"small"` or `"medium"` — no large tasks (split them)
- `label` must be `"feature"`, `"chore"`, or `"bug"`

---

## state.yaml

The state file tracks runtime progress. Written by `execution` during task dispatch and completion.

```yaml
version: "1.0"
config_hash: "a1b2c3d4..."           # SHA-256 of config.yaml at execution start
started_at: "2026-03-18T10:00:00Z"
last_updated: "2026-03-18T11:30:00Z"

phases:
  - name: "Register a user"
    status: "completed"               # pending | in_progress | in_review | completed | blocked
    branch: "feature/FEAT-100-auth/phase-1-register"
    pr_url: "https://github.com/org/repo/pull/42"
    pr_number: 42
    linear_issue: "FEAT-101"
    iterations_used: 3
    tasks:
      T001: "completed"              # queued | in_progress | completed | failed | dead
      T002: "completed"
      T003: "completed"
    task_reports:
      T001:
        status: "success"
        deliverable: "Users table migration with up/down"
        files_changed:
          - "db/migrations/002_users.py (new)"
        tests_added:
          - "tests/test_migrations.py — test_users_migration_applies, test_users_migration_rollback"
        completed_at: "2026-03-18T10:15:00Z"
      T002:
        status: "success"
        deliverable: "User model with email validation and bcrypt hashing"
        files_changed:
          - "models/user.py (new)"
        tests_added:
          - "tests/test_user_model.py — 4 tests"
        completed_at: "2026-03-18T10:35:00Z"
      T003:
        status: "success"
        deliverable: "POST /api/users endpoint with full validation"
        files_changed:
          - "routes/users.py (new)"
          - "routes/__init__.py (modified)"
        tests_added:
          - "tests/test_register_endpoint.py — 4 tests"
        completed_at: "2026-03-18T11:00:00Z"

  - name: "Log in"
    status: "in_progress"
    branch: "feature/FEAT-100-auth/phase-2-login"
    pr_url: null
    pr_number: null
    linear_issue: "FEAT-102"
    iterations_used: 1
    tasks:
      T001: "completed"
      T002: "in_progress"
      T003: "queued"
    task_reports:
      T001:
        status: "success"
        deliverable: "Session model and JWT utilities"
        files_changed:
          - "models/session.py (new)"
          - "utils/jwt.py (new)"
        tests_added:
          - "tests/test_session.py — 3 tests"
        completed_at: "2026-03-18T11:15:00Z"
```

### Task Status Transitions

```
queued → in_progress → completed
                    → failed → (retry) → in_progress
                             → (max retries) → dead
```

### Phase Status Transitions

```
pending → in_progress → in_review → completed
                     → blocked (manual intervention needed)
       in_review → in_progress (changes requested on PR)
```

### Resumption Protocol

1. Load `state.yaml` and `config.yaml`
2. Verify config hash — warn if config changed
3. Find first non-completed phase
4. Within phase: skip completed tasks, re-dispatch in_progress tasks, start queued tasks
5. Continue normal execution flow
