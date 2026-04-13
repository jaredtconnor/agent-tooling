# Team Deployment Reference

Task agent and code reviewer prompt templates for team execution strategy.

## Task Agent Prompt Template

Each task agent (teammate) receives this prompt when spawned:

```
You are a task agent executing tasks for phase {phase_id}.

PROTOCOL:
1. Check TaskList for available tasks
2. Claim a pending, unblocked task (TaskUpdate status=in_progress)
3. Read the task description for full context
4. Execute using the Tier 3 skill:
   - feature → Skill('dlc:executing-tasks')
   - bug → Skill('dlc:executing-bug-fixes')
   - chore → Skill('dlc:executing-chores')
5. Git pull --rebase before committing, push after
6. Mark task complete (TaskUpdate status=completed)
7. Claim next available task or go idle

PHASE CONTEXT:
- Phase ticket ID: {phase_id}
- Phase branch: {phase_branch}
- Feature branch: {feature_branch}
- Phase label: {phase_label}

SPECIFICATION EXCERPT:
{spec}

TECHNICAL PLAN EXCERPT:
{plan}

CODEBASE PATTERNS:
{patterns}

GIT WORKFLOW:
- Before starting each task: git pull --rebase origin {phase_branch}
- Tier 3 skill handles the commit (one commit per task)
- After task commit: git push origin {phase_branch}
- If push fails (conflict): git pull --rebase origin {phase_branch} && git push
```

## Code Reviewer Prompt Template

Dispatched after all tasks in a phase complete:

```
Review all changes on the phase branch.

PHASE: {phase_id} — {phase_title}
DIFF: git diff {base_branch}...{phase_branch}
ACCEPTANCE CRITERIA:
{acceptance_criteria}

SPECIFICATION EXCERPT:
{spec}

TECHNICAL PLAN EXCERPT:
{plan}

CHECKLIST:
- [ ] TDD compliance: tests written before implementation, tests fail first
- [ ] Test coverage: all acceptance criteria have corresponding tests
- [ ] Code quality: SOLID principles, no circular dependencies
- [ ] Security: no hardcoded secrets, input validation at boundaries
- [ ] Naming: clear, consistent with codebase conventions
- [ ] No over-engineering: minimal code for requirements

REPORT FORMAT:
Produce a severity-tagged report:
- 🔴 Critical: Security, data loss, broken functionality → FIX DIRECTLY
- 🟡 Major: Architecture, patterns, maintainability → FIX DIRECTLY
- 🟢 Minor: Style, naming, documentation → COMMENT ONLY

Fix critical and major issues with commits on the phase branch.
Report minor issues as comments in the PR.
```

## Task List Setup

```python
tasks = parse_tasks(phase.description)
for task in tasks:
    TaskCreate(
        subject=f"Task {task['index']}: {task['title']}",
        description=f"""
TASK CONTEXT:
- Phase: {phase_id} ({phase_label})
- Task: {task['index']} — {task['title']}

TASK BODY:
{task['body']}

UNIT TESTS: {task.get('tests', [])}
FILES: {task.get('files', [])}
LAYERS: {task.get('layers', [])}
REFERENCE: {task.get('reference', '')}

CODEBASE PATTERNS:
{format_patterns(accumulated_patterns)}
""",
        activeForm=f"Executing {task['title']}"
    )

# Set up dependencies
dependencies = parse_parallelisation_notes(phase.description)
for task_id, blocked_by in dependencies.items():
    TaskUpdate(taskId=task_id, addBlockedBy=blocked_by)
```

## Teammate Spawn

```python
max_teammates = min(len(tasks), 4)
for i in range(max_teammates):
    spawn_teammate(model="sonnet", prompt=TASK_AGENT_PROMPT)
```

## Git Coordination

All teammates work on the same phase branch:

```bash
# Before each task
git pull --rebase origin {phase_branch}

# After commit
git push origin {phase_branch}

# If push fails
git pull --rebase origin {phase_branch}
git push origin {phase_branch}

# If rebase conflicts are unresolvable
# Report failure, lead spawns replacement
```

**Key:** No per-teammate branches. Well-structured vertical slices minimize conflicts.

## Strategy Resolution

```python
def resolve_strategy(flags, config, phase):
    if flags.get("strategy"):
        return flags["strategy"]
    if config.get("execution.strategy"):
        return config["execution.strategy"]

    strategy = "team"

    if not env_var_set("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"):
        return "sequential"
    if is_headless_or_conductor():
        return "sequential"
    if len(parse_tasks(phase.description)) <= 1:
        return "sequential"

    return strategy
```
