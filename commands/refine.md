---
description: Refine feature ideas into specifications focusing on WHAT to build not HOW
---

# Refine - Issue Refinement Command

Transform rough ideas into validated specifications (WHAT to build), ready for technical planning.

## Usage

```bash
/refine <issue-id>           # Refine existing issue → write spec to Linear
/refine <issue-id> --local   # Refine + persist --local flag for downstream commands
/refine <free text>          # Create new issue and refine it
/refine <free text> --local  # Create new issue, refine, persist --local flag
```

## Overview

This command uses the `refine` skill to:

1. Load or create issue in Linear/JIRA
2. Ask questions about user needs (WHAT, not HOW)
3. Explore expected behaviors and edge cases
4. Present specification for validation
5. Write specification to issue
6. Offer to chain to `/plan`
7. **In `--local` mode: write spec to `.agents/specs/spec-<id>.md`**
8. Persist workflow state (issue_id + --local flag) to `.agents/config.yaml`

**Focus:** Requirements, behaviors, success criteria (NOT technology or architecture)

## How It Works

### Step 1: Parse Arguments & Load State

```python
local_flag = '--local' in args
issue_id = parse_issue_id(args)   # None if free-text description given

state = read_workflow_state()   # from local-task-store skill

# Detect issue change
if issue_id:
    changed, old_id = detect_issue_change(issue_id)
    if changed:
        WARN: "Previously working on {old_id}. Starting fresh for {issue_id}."
        reset_workflow_state(issue_id)
        state = {'issue_id': issue_id}

# Inherit --local
local_mode = local_flag or state.get('flags', {}).get('local', False)
```

### Step 2: Load or Create Issue

**Existing issue:**

```python
issue = mcp__linear-server__get_issue(id=issue_id)
```

**New issue from text:**

```python
# Determine team (from CLAUDE.md or ask user)
issue = mcp__linear-server__create_issue(title, description, team)
issue_id = issue.id
```

### Step 3: Run Refining-Issues Skill

```bash
Skill(refine)
```

The skill handles:

- Understanding user needs
- Exploring behaviors and edge cases
- Presenting specification
- **Default mode:** Writing to issue with "Specification" section
- **Local mode:** Producing specification content as text (command writes the file in Step 4)

### Step 4: Write Local Spec File (local mode only)

**Skip this step entirely if `local_mode` is false.**

After the skill returns the validated specification, write it to a local file.

**Determine file name:**

```python
def spec_filename(issue_id, branch_name=None):
    """Generate spec filename. Issue ID preferred, branch name as fallback."""
    if issue_id:
        return f"spec-{issue_id.lower()}.md"
    elif branch_name:
        return f"spec-{branch_name}.md"
    else:
        return "spec-unnamed.md"
```

**Write the spec file:**

```
.agents/specs/spec-<issue-id>.md
```

Use the specification content produced by the skill in Step 3. Create the `specs/` directory if it doesn't exist.

**Update config.yaml with spec_file pointer:**

```python
write_workflow_state({
    'spec_file': f"specs/{spec_filename(issue_id)}"
})
```

**Verify:** Read the spec file to confirm it exists and is non-empty.

### Step 5: Persist Workflow State

```python
write_workflow_state({
    'phase': 'refine_complete',
    'issue_id': issue_id,
    'objective': '<1-2 sentence summary of what is being built>',
    'spec_file': f"specs/{spec_filename(issue_id)}" if local_mode else None,
    'flags': {'local': local_mode}
})
```

### Step 6: Offer Next Step

**Default mode:**
```markdown
✓ Specification written to issue <ISSUE-ID>

Ready to create technical plan? Run `/plan <ISSUE-ID>`
```

**Local mode:**
```markdown
✓ Specification written to .agents/specs/spec-<issue-id>.md
✓ .agents/config.yaml updated (spec_file, issue_id, local: true)

--local is persisted — run `/plan <ISSUE-ID>` and it will be inherited automatically.

Ready to create technical plan?
```

**If user agrees, chain to `/plan`**

## Error Handling

### No PM System

```markdown
ERROR: No project management system configured

Install Linear or JIRA MCP server:
- Linear: https://github.com/modelcontextprotocol/servers/tree/main/src/linear
- Configure API key in Claude Code settings
- Restart Claude Code
```

### Issue Not Found

```markdown
ERROR: Issue <ISSUE-ID> not found

Check issue ID format:
- Linear: TEAM-123
- JIRA: PROJECT-456

Or create new: `/refine "your feature description"`
```

## Integration

**Requires:**

- Linear/JIRA MCP configured
- `refine` skill

**Chains to:**

- `/plan` (optional)

## Remember

- Use `refine` skill for all refinement work
- Focus on WHAT not HOW
- Specification drives tests later
- Chain to `/plan` (not `/breakdown`)
- **Default mode:** Spec written to PM system only (no local files)
- **`--local` mode:** Spec written to `.agents/specs/spec-<id>.md`, PM system NOT updated. Flag persisted for downstream commands.
- Spec files accumulate per-issue — switching issues preserves old files
