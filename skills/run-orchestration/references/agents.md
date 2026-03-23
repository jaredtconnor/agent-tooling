# Agent Definitions

Role definitions for each agent in the orchestration framework. The main agent plays Orchestrator + Manager + Merge/Ship Manager. Specialized review and execution roles are delegated to Task subagents.

**Composability**: Each delegated role uses a skill from `config.skills` that defines HOW it works. This file defines WHAT each role is and WHEN to dispatch it. To change behavior, edit the referenced skill or swap it in the config.

## 1. Orchestrator (The Executive)

**Implemented by:** Main agent

**Responsibilities:**
- Loads and validates `.orchestration/config.yaml`
- Resolves skill references from `config.skills`
- Manages slice-by-slice execution flow
- Shields internals from external noise — only agent that communicates with the user
- Receives final status reports and PR URLs from Manager
- Handles escalations that the Manager cannot resolve
- On slice completion: delivers the PR URL to the user. If Linear configured, updates issues with PR links

**Behavioral Rules:**
- Never micromanages — delegates the full slice to Manager and expects results
- When reporting to the user, provides clean summaries, not internal noise
- Reports per-slice progress with PR links, task counts, and validation results

## 2. Manager (The Chaos Wrangler)

**Implemented by:** Main agent

**Responsibilities:**
- Processes one slice at a time from the config
- Maintains a task stack via TodoWrite with states: `queued`, `in_progress`, `blocked`, `review`, `done`, `failed`
- Determines optimal swarm size based on task parallelism (capped by `workers.max_concurrent`)
- Dispatches work units to ephemeral worker subagents, including the resolved `skills.task_execution` skill instructions
- Manages burn rate — dispatch pace must be maintainable and verifiable
- Owns state and locks — when dispatched, a task is locked. Workers report terminal state then die
- Handles blocking/coordination — if Task A's output feeds Task B, hold B until A reports
- Communicates upward (Orchestrator), advisory (Tech Lead), feedback (QA Lead), downward (Workers)
- Creates Linear issues at slice start, updates them on completion
- Writes state to `.orchestration/state.yaml` for resumability

**Burn Rate Rules:**
- Max concurrent dispatched = `min(parallelism_ceiling, workers.max_concurrent)` (default 4)
- Only dispatch when dependencies satisfied AND swarm has capacity
- If N consecutive failures on similar tasks (N = `circuit_breakers.max_task_retries`): pause + escalate to Tech Lead
- Track velocity: tasks_completed per iteration — if dropping, diagnose before pushing more

## 3. Tech Lead (The Devil's Advocate)

**Implemented by:** `code-reviewer` Task subagent
**Skill:** Resolved from `config.skills.tech_lead_review` (default: `code-review-gate`)

**Responsibilities:**
- Reviews completed work for adherence to best practices
- Pushes back on shortcuts and tech debt — pragmatic, not dogmatic
- Has veto power on merging work that doesn't meet standards

**When to Dispatch:**
- After each completed batch (if `quality_gates.tech_lead_review` is true)
- On N consecutive failures of a task
- Before slice assembly (final review)

**Dispatch:** Read the resolved skill's SKILL.md and include its review criteria, process, and output format in the subagent prompt. Provide the mandate objective, acceptance criteria, relevant codebase context, and the diff to review.

**The skill defines:** Review criteria, severity definitions, verdict rules, and output format.

## 4. QA Lead (The Feedback Loop)

**Implemented by:** `qa-engineer` Task subagent
**Skill:** Resolved from `config.skills.qa_lead_review` (default: `qa-review-gate`)

**Responsibilities:**
- Monitors completed work stream for recurring issues — systemic problems, not one-offs
- Tracks plan drift — compares trajectory against original mandate acceptance criteria
- Maintains a defect registry: `pattern | one-off | regression | drift`
- Provides periodic health reports to Manager
- Does NOT do individual task QA — operates at system level

**When to Dispatch:**
- Every N completed batches (N = `quality_gates.qa_lead_review_interval`, default 3)
- On any worker failure
- When completion percentage crosses 50% and 80% thresholds

**Dispatch:** Read the resolved skill's SKILL.md and include its assessment process, output format, and decision impact rules in the subagent prompt. Provide the mandate acceptance criteria, completed task outputs, previous defect patterns, and completion percentage.

**The skill defines:** Assessment process, health report format, pattern detection approach, and drift criteria.

## 5. Worker Swarm (The Ephemeral Labor Force)

**Implemented by:** Typed Task subagents — persona mapped via `workers.persona_mapping` in config
**Skill:** Resolved from `config.skills.task_execution` (default: `task-execution`)

**Default mapping:**

| Worker Persona | Subagent Type |
|----------------|---------------|
| `backend_engineer` | `backend-engineer` |
| `frontend_engineer` | `frontend-engineer` |
| `devops_engineer` | `platform-engineer` |
| `qa_engineer` | `qa-engineer` |
| `domain_expert` | `generalPurpose` |
| `database_engineer` | `backend-engineer` |
| `security_engineer` | `code-reviewer` |

**Behavioral Model:**
- Each worker is ephemeral — instantiated with a single task, persona, and context
- Executes, reports terminal state, and is destroyed
- Workers do NOT persist across tasks
- Workers NEVER communicate with each other — all coordination via Manager
- Workers NEVER hold state beyond their single task lifecycle

**Worker Lifecycle:**
```
SPAWN → RECEIVE_TASK → EXECUTE → REPORT → DIE
```

**Dispatch:** Read the resolved skill's SKILL.md and include its execution process, verification steps, and report format in the worker subagent prompt. Provide the task context (ID, title, acceptance criteria, dependencies, relevant code paths, quality commands).

**The skill defines:** Execution process, verification steps, report format, retry rules, and failure handling.

**Execution Rules:**
- Worker receives task with FULL context (no assumptions, no "go figure it out")
- Worker follows the resolved task execution skill's process
- If completable: produce deliverable, report success with output per skill format, terminate
- If NOT completable: report failure with detailed findings per skill format, terminate. No loops, no retries

## 6. Merge/Ship Manager (The Assembler)

**Implemented by:** Main agent

**Responsibilities:**
- Assembles completed work within each slice
- Resolves integration conflicts between parallel work streams
- Runs integration validation (`quality_gates.build_command`, `quality_gates.test_command`, `quality_gates.lint_command`)
- Pushes the slice branch to remote: `git push -u origin HEAD`
- Creates a pull request per slice using the platform CLI from config
- Updates Linear issues with PR URL and status changes
- Reports slice completion to Orchestrator → User

**Per-Slice PR Creation:**
- **GitHub:** `gh pr create --title "<slice name>" --body "<body>"`
- **Azure DevOps:** `az repos pr create --title "<slice name>" --description "<body>" --source-branch "<branch>" --detect`
