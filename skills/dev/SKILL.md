---
name: dev
description: >-
  Composable development workflow with cascading phases. Run the full pipeline
  or invoke phases individually: dev plan, dev implement, dev review, dev qa.
  Plan output goes to .orchestration/plan.md; with --linear, the plan is
  decomposed into Linear issues (parent + children) for tracking. Slim state
  persists to .orchestration/config.yaml for cross-session cascading. Same
  sub-skills as run-orchestration. Use when the user says 'dev', wants to
  implement a feature, fix a bug, review changes, or plan an approach.
argument-hint: '[phase] "description" [--flags]'
version: 1.0.0
---

# Development Workflow

Composable single-pass pipeline with cascading phases. Slim state persists to `.orchestration/config.yaml` so the next phase can pick it up -- even across sessions. Two plan output modes:

- **Local** (default): Plan goes to `.orchestration/plan.md`
- **Linear** (`--linear`): Plan is decomposed into Linear issues (parent + children) — Linear is the source of truth

## How Cascading Works

### Local mode (default)

```
dev plan "add caching"
  │  Writes: .orchestration/plan.md (full plan, readable markdown)
  │  Writes: slim dev_state to config (phase, objective, plan_file, flags)
  │  User can: read/edit plan.md, then continue
  ▼
dev implement
  │  Reads: plan from .orchestration/plan.md
  ▼
dev review → dev qa → done
```

### Linear mode (`--linear`)

```
dev plan "add caching" --linear="My Project"
  │  Decomposes: plan into implementation phases
  │  Creates: parent Linear issue (objective + approach)
  │           child Linear issues (one per phase, with files + acceptance criteria)
  │  Writes: slim dev_state to config (phase, objective, flags, parent + child IDs)
  │  Writes: .orchestration/plan.md (summary with Linear issue links)
  │  User can: review/reorder/edit issues in Linear, then continue
  ▼
dev implement
  │  Reads: plan from .orchestration/plan.md (includes Linear links)
  │  Updates: child issues to "In Progress" as they're worked
  ▼
dev review
  │  Adds: review summary as comment on parent issue
  ▼
dev qa
     Adds: QA assessment as comment on parent issue
     Moves: parent to "Done"/"In Review" if approved
```

**State lives in:**
- `.orchestration/config.yaml` → `dev_state` key: lightweight references, phase status, summaries
- `.orchestration/plan.md` → full plan in readable markdown (local mode) or summary with Linear links (Linear mode)
- **Linear** (if `--linear`) → the plan structure lives as issues, reviewable and trackable in Linear

This is the same config file `run-orchestration` uses -- `dev_state` is ignored by orchestration, and `slices` are ignored by dev.

## State Persistence

### What gets written

| Phase | Config (`dev_state`) | Plan file | Linear (if `--linear`) |
|-------|---------------------|-----------|------------------------|
| `dev plan` | `phase`, `objective`, `plan_file`, `flags`, `linear_issue`, `linear_children` | `.orchestration/plan.md` | Creates parent + child issues |
| `dev implement` | Updates `phase` | -- | Moves child issues to "In Progress" |
| `dev review` | `review` (verdict + finding_count), updates `phase` | -- | Adds review comment on parent |
| `dev qa` | `qa` (on_track + summary), updates `phase` | -- | Adds QA comment, moves parent to "Done" |

### How state is read

| Phase | Reads |
|-------|-------|
| `dev implement` | `.orchestration/plan.md` for what to build, `dev_state.flags` for skill config |
| `dev review` | `dev_state.objective` for review context, `dev_state.flags` for skill config, `git diff` for changes |
| `dev qa` | `dev_state.objective` + `dev_state.review` (verdict + finding_count) for QA context |

### File creation

- If `.orchestration/` doesn't exist, `dev plan` creates the directory.
- If `config.yaml` doesn't exist, `dev plan` creates it with `version`, `skills`, `quality_gates`, and `dev_state`.
- If `config.yaml` already exists, `dev plan` updates/overwrites the `dev_state` section only (preserving `skills`, `quality_gates`, `slices`, etc.).
- `dev plan` always writes/overwrites `.orchestration/plan.md`.
- Each subsequent phase updates `dev_state` fields only.

### Local vs Linear plan file

- **Local mode**: `plan.md` contains the full plan (approach, files, decisions, risks, implementation order).
- **Linear mode**: `plan.md` contains a summary with links to the Linear issues. The full detail lives in the issue descriptions.

### Fresh start

Running `dev plan "new description"` overwrites `dev_state` and `plan.md` entirely -- it's a fresh start for a new task. The `skills` and `quality_gates` sections persist. Existing Linear issues are NOT deleted (they're external state).

## Invocation

### Full pipeline

```
dev "description" [--flags]
```

Runs all phases: understand → plan → approve → implement → review → fix → summary. Writes state at each transition.

### Individual phases (cascading)

| Command | Reads from | Writes to | Next step |
|---------|-----------|----------|-----------|
| `dev plan "description"` | -- | `plan.md` + slim `dev_state` | `dev implement` |
| `dev implement` | `.orchestration/plan.md` | `dev_state.phase` | `dev review` |
| `dev implement "description"` | Description directly | `dev_state.phase` + objective | `dev review` |
| `dev review` | `dev_state.objective` + git diff | `dev_state.review` (slim) | `dev qa` or done |
| `dev qa` | `dev_state.objective` + `dev_state.review` | `dev_state.qa` (slim) | Done |

### Phase detection

Parse the first token of `$ARGUMENTS`:

| First token | Mode | What runs |
|-------------|------|-----------|
| `plan` | Plan only | Explore + plan, write state, stop |
| `implement` | Implement only | Read plan from state, build, verify, stop |
| `review` | Review only | Read objective from state, review diff, stop |
| `qa` | QA only | Read objective + findings from state, assess, stop |
| Anything else | Full pipeline | All phases in sequence |

### Cascading rules

1. **`dev implement` without a description**: Read `.orchestration/plan.md`. If found and `dev_state.phase` is `"plan_complete"`, implement that plan. If no plan file, ask the user what to implement.

2. **`dev implement "description"`**: Bypass the plan — write the description as `dev_state.objective` and implement directly.

3. **`dev review`**: Read `dev_state.objective` from config for review context. Always uses `git diff` for the actual changes. If no config exists, reviews the diff without objective context.

4. **`dev qa`**: Read `dev_state.objective` and `dev_state.review` (verdict + finding_count) from config. If review hasn't been run, runs QA without review context.

5. **Each isolated phase ends with a "Next" suggestion:**
   - `dev plan` → "Plan written to `.orchestration/plan.md`. Run `dev implement` to build it, or edit the plan first."
   - `dev implement` → "Implementation complete. Run `dev review` to check the changes."
   - `dev review` → "Review complete. Summary written to config. Run `dev qa` for health assessment."
   - `dev qa` → "QA complete. Assessment above."

6. **Full pipeline `dev "X"`** writes state at each transition but doesn't stop between phases (except the plan approval gate).

7. **Linear cascading**: If `dev_state.linear_issue` exists, subsequent phases update Linear automatically (child issue statuses, review/QA comments on parent). No extra flags needed after `dev plan --linear`.

## Configuration

Skills resolved in priority order (highest wins):

### 1. Inline Flags

```
dev "add batch cancellation" --tdd --qa
dev plan "refactor data layer" --plan=adlc:technical-planning
dev review --review=code-review-gate
```

| Flag | Effect |
|------|--------|
| `--tdd` | Sets task execution to `adlc:executing-tasks` (strict TDD) |
| `--qa` | Enables QA pass using `qa-review-gate` |
| `--linear` | Decomposes plan into Linear issues (parent + children), subsequent phases track via Linear |
| `--linear=<project>` | Same as `--linear` but targets a specific Linear project |
| `--plan=<skill>` | Override planning skill (default: `dev-plan`) |
| `--review=<skill>` | Override review skill (default: `dev-review`) |
| `--task=<skill>` | Override task execution skill |
| `--no-review` | Skip review (full pipeline only) |
| `--no-plan` | Skip planning (full pipeline only) |

Flags are persisted to `dev_state.flags` so subsequent phases use the same configuration.

### 2. YAML Config (fallback)

If `.orchestration/config.yaml` exists, reads `skills:` and `quality_gates:` for defaults.

```yaml
skills:
  plan: "dev-plan"
  review: "dev-review"
  task_execution: "task-execution"
  qa_lead_review: "qa-review-gate"

quality_gates:
  test_command: "just test"
  lint_command: "just lint"
  build_command: "just build"
```

### 3. Built-in Defaults

| Role | Default |
|------|---------|
| Planning | `dev-plan` |
| Review | `dev-review` |
| Task execution | Main agent (direct) |
| QA | Disabled (enable with `--qa` or `dev qa`) |

## Sub-Skills

Same building blocks as `run-orchestration`. Edit a sub-skill to change behavior without touching this workflow.

| Role | Default | Alternatives |
|------|---------|--------------|
| Planning | `dev-plan` | `adlc:technical-planning` |
| Review | `dev-review` | `code-review-gate`, `adlc:requesting-code-review` |
| Task execution | *(main agent)* | `task-execution`, `adlc:executing-tasks` (TDD), `adlc:executing-chores` |
| QA | `qa-review-gate` | Custom QA skill |

---

## Phase 1: Understand

**Runs in**: full pipeline only.

**Goal**: Parse input, resolve skills, assess clarity.

**Actions**:

1. **Parse arguments** — detect mode (phase keyword or full), extract description and flags.
2. **Resolve skills** — flags > `dev_state.flags` (from config) > YAML `skills:` section > defaults.
3. **Create a todo list** covering active phases.
4. **Assess the request**:
   - **Clear**: Summarize in 1-2 sentences, proceed to Phase 2.
   - **Ambiguous**: Ask targeted questions. Wait for answers before proceeding.

---

## Phase 2: Plan

**Runs in**: `dev plan "..."` or full pipeline (unless `--no-plan`).

**Sub-skill**: Resolved planning skill (default: `dev-plan`).

**Actions**:
1. Launch 1-2 `explore` subagents in parallel:
   - Trace relevant code comprehensively
   - Return 5-10 key files each

2. Read all key files identified.

3. Launch a `generalPurpose` subagent with the planning skill:
   - Provide requirement summary + exploration findings
   - Returns a single decisive implementation plan

4. Present the plan:
   - Files to create/modify
   - Approach and key decisions
   - Trade-offs or risks

5. **Write outputs** — two paths depending on `--linear`:

   #### Local mode (no `--linear`)

   Write `.orchestration/plan.md` with the full plan:
   ```markdown
   # Plan: <objective>

   ## Approach
   <chosen approach description>

   ## Files to Create
   - `path/file.ts` -- purpose

   ## Files to Modify
   - `path/existing.ts` -- what changes

   ## Key Decisions
   1. Decision and rationale

   ## Risks
   - Risk or open question

   ## Implementation Order
   1. First step
   2. Second step
   ```

   #### Linear mode (`--linear`)

   Decompose the plan into implementation phases. Each phase becomes a child issue. Then:

   a. **Create parent Linear issue** — the overall objective:
      - Title: the objective (1-2 sentences)
      - Description: approach summary, key decisions, risks
      - Project: from `--linear=<project>` if specified
      - Via `linctl issue create` or Linear MCP

   b. **Create child Linear issues** — one per implementation phase:
      - Title: phase name (e.g., "Phase 1: Add Redis connection config")
      - Description: files to create/modify, approach for this phase, acceptance criteria
      - Parent: the issue created in (a)
      - Each child is an independently implementable unit of work

      Example decomposition for "add caching layer":
      ```
      PROJ-100: Add caching layer to reduce database load (parent)
        ├─ PROJ-101: Phase 1 — Redis connection and config
        ├─ PROJ-102: Phase 2 — Cache wrapper implementation
        ├─ PROJ-103: Phase 3 — Integrate cache into UserRepository
        └─ PROJ-104: Phase 4 — Cache invalidation on writes
      ```

   c. **Write `.orchestration/plan.md`** — summary with Linear links:
      ```markdown
      # Plan: <objective>

      ## Approach
      <approach summary>

      ## Linear Issues
      - [PROJ-100](<linear-url>) — Parent: <objective>
        - [PROJ-101](<linear-url>) — Phase 1: Redis connection and config
        - [PROJ-102](<linear-url>) — Phase 2: Cache wrapper implementation
        - [PROJ-103](<linear-url>) — Phase 3: Integrate cache into UserRepository
        - [PROJ-104](<linear-url>) — Phase 4: Cache invalidation on writes

      ## Key Decisions
      1. Decision and rationale

      ## Risks
      - Risk or open question
      ```

6. **Write slim state** to `.orchestration/config.yaml`:
   - If config exists, read it and update `dev_state` only
   - If config doesn't exist, create it with `version`, resolved `skills`, `quality_gates`, and `dev_state`
   - Write slim `dev_state`:
     ```yaml
     dev_state:
       phase: "plan_complete"
       objective: "<1-2 sentence summary>"
       plan_file: ".orchestration/plan.md"
       linear_issue: null              # "PROJ-100" if --linear (parent issue)
       linear_children: []             # ["PROJ-101", "PROJ-102", ...] if --linear
       flags:
         tdd: false
         qa: false
         plan_skill: "dev-plan"
         review_skill: "dev-review"
         linear_project: null          # "My Project" if --linear=<project>
     ```

**Isolated (`dev plan`):** Present the plan and stop.
- **Local**: "Plan written to `.orchestration/plan.md`. Run `dev implement` to build it, or edit the plan first."
- **Linear**: "Plan decomposed into N Linear issues under PROJ-100. Review them in Linear, then run `dev implement`."

**Full pipeline:** Wait for user approval, then continue to Phase 3.

---

## Phase 3: Implement

**Runs in**: `dev implement [description]` or full pipeline.

**Sub-skill**: Resolved task execution skill (if `--tdd` or `--task`), otherwise main agent.

**Context from state**: If no description provided, read from persisted state:
- `.orchestration/plan.md` — full plan (approach, files, implementation order)
- `dev_state.flags` — skill configuration (tdd, review skill, etc.)
- `dev_state.objective` — the original description

If no plan file or no config, ask the user what to implement.

**Actions**:
1. Read `.orchestration/plan.md` and extract file lists and implementation order.
2. Read relevant source files identified in the plan (or explore if no plan).
3. Implement following plan/description and codebase conventions.
4. If task execution skill is active (`--tdd` or `dev_state.flags.tdd`), follow its process.
5. Run verification if quality gates are configured:
   ```
   {test_command}    # e.g., just test
   {lint_command}    # e.g., just lint
   {build_command}   # e.g., just build
   ```
6. **Write state**: Update `dev_state.phase: "implement_complete"`. If description was provided directly (no prior plan), also write `dev_state.objective`.
7. **Linear** (if `dev_state.linear_issue` exists):
   - Move parent issue to "In Progress" via `linctl issue update <id> --status "In Progress"`
   - As each phase/child is completed, move the corresponding child issue to "Done"

**Isolated (`dev implement`):** Present verification results and stop.
- Next: "Implementation complete. Run `dev review` to check the changes."

**Full pipeline:** Continue to Phase 4.

---

## Phase 4: Review & Fix

**Runs in**: `dev review`, `dev qa`, or full pipeline (unless `--no-review`).

**Sub-skill**: Resolved review skill (default: `dev-review`).

### Review (max 2 passes)

**Context from state**: Read `dev_state.objective` and `dev_state.flags` from config. Uses `git diff` for the actual changes.

1. Launch `code-reviewer` subagent with review skill:
   - Provide objective (from state), implementation summary, `git diff`
   - Returns categorized findings

2. Act on findings:
   - **Critical / blocking**: Fix immediately.
   - **Medium / warning**: Fix if straightforward, note for user otherwise.

3. Pass 2: Re-launch to verify fixes and catch anything missed.
   - Do not run a 3rd pass.

4. **Write state** (slim — detail stays in conversation output):
   ```yaml
   review:
     verdict: "needs_revision"   # or "approved"
     finding_count: 3
   ```
   Update `dev_state.phase: "review_complete"`.

5. **Linear** (if `dev_state.linear_issue` exists): Add a comment with review summary via `linctl issue comment <id> "Review: <verdict>, <N> findings"`.

**Isolated (`dev review`):** Present findings and stop. Do NOT auto-fix.
- Next: "Review complete. Summary written to config. Run `dev qa` for health assessment."

**Full pipeline:** Auto-fix findings, then continue to QA (if flagged) or summary.

### QA

**Runs in**: `dev qa` or full pipeline with `--qa`.

**Context from state**: Read `dev_state.objective` and `dev_state.review` (verdict + finding_count) from config.

6. Launch `qa-engineer` subagent with QA skill (default: `qa-review-gate`):
   - Provide objective, acceptance criteria, all changes, review summary (from state)
   - Returns health assessment

7. Act on QA report:
   - `on_track: false` → pause and report to user
   - Recurring patterns → fix the systemic issue

8. **Write state** (slim):
   ```yaml
   qa:
     on_track: true
     summary: "Implementation follows plan. High-severity finding addressed."
   ```
   Update `dev_state.phase: "qa_complete"`.

9. **Linear** (if `dev_state.linear_issue` exists):
   - Add QA assessment as comment via `linctl issue comment <id> "QA: <on_track>, <summary>"`
   - If `on_track: true` and review `verdict: "approved"`, move ticket to "Done" or "In Review"

**Isolated (`dev qa`):** Present health report and stop.
- Next: "QA complete. Assessment written to config."

### Summary (full pipeline only)

10. Mark all todos complete.
11. Present:
    - What was built/changed
    - Key decisions made
    - Files modified
    - Skills used
    - Review findings (if any remaining)
    - QA assessment (if `--qa`)
    - Linear ticket link (if `--linear`)
    - Suggested next steps

---

## Progression Ladder

Test skills → chain phases → full pipeline → orchestration.

### Level 1: Test individual skills

```
dev plan "add user authentication"
# → Plan written to .orchestration/plan.md (read it!)
# → Slim state in .orchestration/config.yaml

dev review
# → Findings presented. Slim summary in config.

dev qa
# → Health report. Assessment in config.
```

### Level 2: Chain phases across sessions

```
dev plan "add user authentication"
# → Edit .orchestration/plan.md if needed, close the chat, come back later.

dev implement
# → Reads plan from .orchestration/plan.md. Implements it.

dev review
# → Reviews the implementation against the original objective.

dev qa
# → QA uses review summary from config.
```

### Level 3: Full single-pass pipeline

```
dev "add user authentication"
dev "add user authentication" --tdd --qa
```

### Level 3b: Linear-tracked pipeline

```
dev plan "add user authentication" --linear="My Project"
# → Decomposes into parent PROJ-100 + child issues PROJ-101..104 in Linear
# → Review/reorder issues in Linear, then:

dev implement
# → Implements each phase, moves child issues to "Done" as completed

dev review
# → Adds review summary as comment on PROJ-100

dev qa
# → Adds QA assessment, moves PROJ-100 to "Done"

# Or run the whole thing end-to-end:
dev "add user authentication" --tdd --qa --linear="My Project"
```

### Level 4: Scale to orchestration

```
orchestration-setup "add full auth system"     # Create config with slices
# → Review .orchestration/config.yaml (skills, quality_gates carry over)

run-orchestration --dry-run                    # Validate without executing
run-orchestration --slice 1 --budget 4         # One slice, limited iterations
run-orchestration                              # All slices
```
