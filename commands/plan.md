---
description: Create technical implementation plan from refined specification - translates WHAT to HOW
---

# Plan - Technical Implementation Planning Command

Create technical plan from specification, defining HOW to build what's been specified.

## Usage

```bash
/plan <issue-id>           # Create technical plan → write to Linear issue
/plan <issue-id> --local   # Create technical plan → write to .agents/plans/plan-<id>.md
```

## Overview

This command uses the `plan` skill to:

1. Load issue and verify Specification exists
2. Create Technical Plan (architecture, patterns, phases)
3. Write Technical Plan output — to Linear/JIRA (default) or return as text (`--local`)
4. **In `--local` mode: this command writes both output files** (skill returns content only)
5. Offer to chain to `/breakdown`

**`--local` mode:** Keeps Linear clean. The skill produces plan content; **this command** writes it to `.agents/plans/plan-<id>.md` (issue-specific naming) and writes workflow state to `.agents/config.yaml`. Linear is NOT updated. The `--local` flag is persisted in `dev_state` so `/breakdown` and `/execute` inherit it automatically.

## How It Works

### Step 1: Parse Arguments & Load State

```python
local_flag = '--local' in args
issue_id = parse_issue_id(args)

state = read_workflow_state()   # from local-task-store skill

# Detect issue change — if switching issues, ALWAYS reset and overwrite
if issue_id:
    changed, old_id = detect_issue_change(issue_id)
    if changed:
        WARN: "Previously working on {old_id}. Starting fresh for {issue_id}."
        ASK: "Switch from {old_id} to {issue_id}? (Old plans preserved in .agents/plans/, dev_state reset)"
        # If user confirms (or no existing files): proceed
        # If user declines: STOP
        reset_workflow_state(issue_id)
        state = {'issue_id': issue_id}

# Inherit --local from saved state
local_mode = local_flag or state.get('flags', {}).get('local', False)
```

### Step 2: Verify Prerequisites

```bash
# Load issue
issue = mcp__linear-server__get_issue(id)

# Verify Specification exists
if "## Specification" not in issue.description:
    ERROR: Run `/refine <issue-id>` first
    STOP

# Check if plan already exists (only relevant in default/Linear mode)
if not local_mode and "## Technical Plan" in issue.description:
    WARNING: Technical Plan already exists
    ASK: Replace or cancel?
```

### Step 3: Run Technical-Planning Skill

```bash
Skill(plan, args={ local_mode: local_mode })
```

In **default mode** the skill writes the plan directly to the Linear/JIRA issue.

In **local mode** the skill outputs the plan content as text and returns — it does NOT write files. This command is responsible for all file writes in local mode (see Step 4).

### Step 4: Write Local Files (local mode only)

**Skip this step entirely if `local_mode` is false.**

After the skill returns, you (the command) write BOTH files. Do this yourself using the Write tool — do not re-invoke the skill.

**Determine plan file name:**

```python
def plan_filename(issue_id, branch_name=None):
    """Generate plan filename. Issue ID preferred, branch name as fallback."""
    if issue_id:
        return f"plan-{issue_id.lower()}.md"
    elif branch_name:
        return f"plan-{branch_name}.md"
    else:
        return "plan-unnamed.md"
```

**File 1 — write the plan content to an issue-specific path:**

```
.agents/plans/plan-<issue-id>.md
```

Use the plan content produced by the skill in Step 3. Create the `plans/` directory if it doesn't exist. If the file already exists (same issue, re-running plan), overwrite it.

**File 2 — write workflow state:**

```
.agents/config.yaml
```

If the file already exists, read it first and update only the `dev_state` key — preserve all other keys (`phases`, `quality_gates`, `skills`, etc.). If it does not exist, create it:

```yaml
version: "1.0"
dev_state:
  phase: "plan_complete"
  objective: "<1-2 sentence summary>"
  plan_file: "plans/plan-<issue-id>.md"
  issue_id: "<ISSUE-ID>"
  flags:
    local: true
```

Note: `plan_file` is a **relative path** from `.agents/` (not an absolute path).

**After writing both files, verify:**

1. Read `.agents/plans/plan-<id>.md` — confirm it exists and is non-empty
2. Read `.agents/config.yaml` — confirm `dev_state.plan_file`, `dev_state.issue_id`, and `dev_state.flags.local: true` are present

If either file is missing or wrong, write it now before proceeding.

### Step 5: Offer Next Step

**Default mode (Linear):**

```markdown
✓ Technical Plan written to issue <ISSUE-ID>

Ready to break this down into implementation tasks? Run `/breakdown <ISSUE-ID>`
```

**Local mode:**

```markdown
✓ .agents/plans/plan-<issue-id>.md written
✓ .agents/config.yaml updated (plan_file, issue_id: <ISSUE-ID>, local: true)

--local is persisted — run `/breakdown <ISSUE-ID>` and it will be inherited automatically.

Ready to break this down into implementation tasks?
```

**If user agrees, chain to `/breakdown`**

## Error Handling

### No PM System

```markdown
ERROR: No project management system configured
Set up Linear or JIRA MCP server first.
```

### Missing Specification

```markdown
ERROR: Issue missing Specification section

Run `/refine <issue-id>` first to create specification (WHAT to build).
Then run `/plan <issue-id>` to create technical plan (HOW to build it).
```

### Plan Already Exists

```markdown
WARNING: Issue already has Technical Plan

Options:
1. Replace (destructive)
2. Update/extend (preserves content)
3. Cancel (keep existing)
```

## Examples

### Example: Create Plan

```bash
/plan AUTH-123
```

Output:

```
Loaded AUTH-123: "User authentication"
✓ Specification found

Using plan skill...

✓ Technical Plan written
  - 4 components defined
  - 3 API endpoints specified
  - 5 implementation phases

Ready to break down into tasks?
```

### Example: Missing Spec

```bash
/plan FEAT-45
```

Output:

```
Loaded FEAT-45: "Notifications"
✗ Specification missing

ERROR: Run `/refine FEAT-45` first
```

## Integration

**Requires:**

- Linear/JIRA MCP configured
- Issue with Specification section
- `plan` skill

**Chains to:**

- `/breakdown` (optional)

## Remember

- Use `plan` skill for all planning work
- Requires Specification (from `/refine`)
- Creates Technical Plan (HOW)
- **In `--local` mode: YOU (the command) write the files**, not the skill. Skill returns text. Command writes `.agents/plans/plan-<id>.md` then `.agents/config.yaml`. Verify both after writing. Plan files use issue-specific naming and accumulate per-issue.
- In default mode: all in PM system (no separate files)
- Offer `/breakdown` but don't force
