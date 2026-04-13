---
description: Break down refined and planned issues into implementation sub-issues with dependencies in Linear/JIRA or locally
---

# Breakdown - Implementation Task Creation Command

Transform refined specification and technical plan into executable sub-issues with dependencies.

## Usage

```bash
/breakdown <issue-id>                # Break down into Linear sub-issues (default)
/breakdown <issue-id> --local        # Break down into local .agents/config.yaml
/breakdown <issue-id> --local --sync-phases  # Local tasks + lightweight Linear phase issues
```

## Overview

This command uses the `breakdown` skill to:

1. Load issue and verify Specification + Technical Plan exist
2. Break Technical Plan phases into independent, implementable tasks
3. Each task is a complete feature/behavior (TDD: tests + implementation together)
4. Create sub-issues in Linear/JIRA **or** write to local `.agents/config.yaml`
5. Map dependencies between tasks
6. Optionally chain to `/execute`

### Local Mode (`--local`)

When `--local` is set, tasks are written to `.agents/config.yaml` instead of creating full Linear sub-issues. This keeps Linear clean for PM/lead visibility:

- **Task-level breakdown** stays local in config.yaml
- **Phase-level issues** optionally created in Linear (with `--sync-phases`, default when Linear is configured)
- **Developer works against local files** during execution
- **Phase status** synced back to Linear only on completion

## Requirements

**The parent issue MUST have:**

- "Specification" section (from `/refine` - defines WHAT)
- "Technical Plan" section (from `/plan` - defines HOW)

**If missing:** Suggests running `/refine` and/or `/plan` first.

## Core Concept

**Vertical phases, horizontal tasks:**

- **Phases** are vertical slices — each delivers independently demoable end-to-end functionality (DB + API + UI as needed)
- **Tasks** within each phase are horizontal layer-specific units — one TDD cycle per task (e.g., "add migration", "implement endpoint", "create form component")
- Each phase becomes one sub-issue under the parent feature. Tasks are checklist items within the phase sub-issue — never separate tickets.

## How It Works

### Step 1: Parse Arguments & Load State

```python
local_flag = '--local' in args
sync_phases_flag = '--sync-phases' in args
issue_id = parse_issue_id(args)

state = read_workflow_state()   # from local-task-store skill

# Detect issue change
if issue_id:
    changed, old_id = detect_issue_change(issue_id)
    if changed:
        WARN: "Previously working on {old_id}. Starting fresh for {issue_id}."
        reset_workflow_state(issue_id)
        state = {'issue_id': issue_id}

# Inherit --local from saved state
local_mode = local_flag or state.get('flags', {}).get('local', False)

if local_mode and not local_flag:
    INFO: "--local inherited from saved workflow state (started with /plan --local)"
```

### Step 2: Verify Prerequisites

```python
# Load issue (always from PM for spec/plan — local mode only affects task storage)
if mcp__linear-server available:
    issue = mcp__linear-server__get_issue(id=issue_id)
elif jira available:
    issue = jira_get_issue(id=issue_id)
else:
    ERROR: No PM system configured

if "## Specification" not in issue.description:
    ERROR: Run `/refine <issue-id>` first
    STOP
if "## Technical Plan" not in issue.description:
    # Check for local plan file as fallback
    if local_mode:
        state = read_workflow_state()
        plan_file = state.get('plan_file')
        if plan_file and exists(f'.agents/{plan_file}'):
            INFO: f"Technical Plan not in Linear — reading from .agents/{plan_file}"
    else:
        ERROR: Run `/plan <issue-id>` first
        STOP
```

### Step 3: Run Breakdown-Planning Skill

```bash
Skill(breakdown)
```

The skill handles:

- Slicing into vertical phases (each phase = one demoable end-to-end behavior)
- Breaking each phase into horizontal tasks by layer (DB, API, service, UI)
- Each task includes full TDD workflow (tests + implementation)
- Creating phase sub-issues with Specification context + Technical Plan guidance
- Defining acceptance criteria and acceptance tests per phase
- Mapping dependencies between phases

### Step 4: Persist Workflow State

```python
write_workflow_state({
    'phase': 'breakdown_complete',
    'issue_id': issue_id,
    'flags': {'local': local_mode}
})
```

### Step 5: Offer Next Step

**Default mode:**

```markdown
✓ Breakdown complete: 18 sub-issues created

Ready to begin execution? Run `/execute <issue-id>`
```

**Local mode:**

```markdown
✓ Breakdown written to .agents/config.yaml
  (--local persisted — /execute will automatically use local mode)

Ready to begin execution? Run `/execute`
```

**If user agrees, chain to `/execute`**

## Error Handling

### No PM System

```markdown
ERROR: No project management system configured
Set up Linear or JIRA MCP server first.
```

### Missing Sections

```markdown
ERROR: Issue missing required sections

Run in order:
1. `/refine <issue-id>` - Create Specification (WHAT)
2. `/plan <issue-id>` - Create Technical Plan (HOW)
3. `/breakdown <issue-id>` - Create tasks

Missing: [Specification | Technical Plan | Both]
```

### Already Has Sub-Issues

```markdown
WARNING: Issue already has sub-issues

Options:
1. Skip (use existing)
2. Add more (append)
3. Replace (delete and recreate)
```

## Examples

### Example: Successful Breakdown

```bash
/breakdown AUTH-123
```

Output:

```
Loaded AUTH-123: "User authentication"
✓ Specification found
✓ Technical Plan found

Using breakdown skill...

Created 5 phase sub-issues (vertical slices):
- Phase 1: Register a user (5 tasks) - no dependencies
- Phase 2: Log in and receive session (6 tasks) - blocked by Phase 1
- Phase 3: View and edit profile (4 tasks) - blocked by Phase 2
- Phase 4: Log out and session management (4 tasks) - blocked by Phase 2
- Phase 5: Reset password via email (6 tasks) - blocked by Phase 1

Each phase is independently demoable end-to-end.
Phases 3-5 can run in parallel after their dependencies complete.

Ready to execute? Run `/execute AUTH-123`
```

### Example: Missing Plan

```bash
/breakdown FEAT-45
```

Output:

```
Loaded FEAT-45: "Notifications"
✓ Specification found
✗ Technical Plan missing

ERROR: Run `/plan FEAT-45` first to create technical plan
```

## Integration

**Requires:**

- Linear/JIRA MCP configured (or `--local` for local-only mode)
- Issue with Specification + Technical Plan
- `breakdown` skill
- `local-task-store` skill (for `--local` mode)

**Chains to:**

- `/execute` (optional — `--local` is inherited automatically from saved workflow state)

## Remember

- Use `breakdown` skill for all breakdown work
- Each phase sub-issue = one vertical slice delivering demoable e2e functionality
- Tasks within a phase = horizontal layer-specific units (DB, service, API, UI)
- Tasks are checklist items in the phase sub-issue, never separate tickets
- Each task includes BOTH tests and implementation (TDD, not split)
- Sub-issues include both WHAT (spec) and HOW (technical plan) context
- Each phase has clear acceptance criteria and acceptance tests
- `--local` writes tasks to config.yaml, keeps Linear clean for PM
- `--sync-phases` creates lightweight Linear issues for phase-level PM visibility
- Offer `/execute` but don't force
