---
description: Fix bugs systematically using TDD, root cause analysis, and automatic testing
---

# Bug-Fix Command

Orchestrates systematic bug fixing using `Skill(executing-bug-fixes)`.

## Usage

```bash
/bug-fix <issue-id>          # Fix bug from Linear/JIRA
/bug-fix <description>       # Create issue and fix
```

## Overview

1. Load or create bug issue (MCP integration)
2. Setup progress tracking (TodoWrite)
3. Invoke `Skill(executing-bug-fixes)` (investigation, TDD, review, commit)
4. Offer to create PR

**Implementation:** All bug-fixing logic in `Skill(executing-bug-fixes)`

## Requirements

- PM MCP (linear-server or jira)
- Test framework configured
- Justfile (recommended)

## Workflow

### 1. Load or Create Issue

**Existing issue:**

```bash
# Detect PM MCP
if mcp__linear-server: issue = get_issue(id)
elif jira MCP: issue = jira_get_issue(id)
else: ERROR("No PM MCP")

# Present
"Loaded: ${id} - ${title}"
"Expected: ${expected} | Actual: ${actual}"
```

**New issue from description:**

```bash
# Extract or ask: what's broken, expected, actual, team, priority
issue = create_issue(
    title: <extracted>,
    description: "## Bug\n${desc}\n## Expected\n${exp}\n## Actual\n${act}",
    team: <ask>, labels: ["bug"], priority: <ask>
)
"Created: ${id} - ${title}"
```

### 2. Setup Tracking

```bash
TodoWrite:
    ${issue.id} Bug Fix:
    - [ ] Root Cause Investigation
    - [ ] Reproduce with Tests
    - [ ] Implement Fix
    - [ ] Verify & Review
    - [ ] Commit & Update
```

### 3. Execute Bug-Fixing

```bash
Read: skills/dlc/executing-bug-fixes/SKILL.md

# Skill handles:
# - Root cause (systematic-debugging)
# - Reproduce test (TDD RED)
# - Fix (TDD GREEN)
# - Review & commit
# - Update ticket

# Update TodoWrite after each phase
```

### 4. Present Summary

```markdown
Bug fix complete!

**Issue:** ${id} - ${title}
**Root Cause:** ${cause}
**Fix:** ${summary}
**Tests:** ${count} passing
**Commit:** ${sha}
**Files:** ${files}

Ready to create PR?
```

### 5. Optional PR

**If yes:**

```bash
git push -u origin fix/${issue.id}
gh pr create --title "fix: ${desc} [${id}]" --body "
Fixes ${id}
Root Cause: ${cause}
Solution: ${solution}
Testing: ${tests}
"
```

## Error Handling

| Error | Response |
|-------|----------|
| **No PM MCP** | "Need Linear/JIRA MCP. Setup: <docs>. Alternative: /bug-fix \"description\"" |
| **Issue not found** | "Verify ID (TEAM-123), access, existence. Create new: /bug-fix \"desc\"" |
| **Cannot reproduce** | executing-bug-fixes reports: "Tests pass. Reasons: Fixed/Env/Steps. Options: Details/Env/Close" |
| **Breaking changes** | executing-bug-fixes reports: "Architectural flaw. Use /refine, /breakdown, or workaround" |

## Integration

**Required:** PM MCP, test framework

**Uses:**

- `Skill(executing-bug-fixes)` - Core
- `Skill(systematic-debugging)` - Investigation
- `Skill(test-driven-development)` - TDD
- TodoWrite, Git, gh CLI

## Examples

### Fix from ID

```bash
$ /bug-fix TEAM-456

Loaded: TEAM-456 - "CSV export includes deleted records"
[executing-bug-fixes runs]
Root cause: Missing deleted_at filter
Commit: abc123def
Ready to create PR?
```

### Create and Fix

```bash
$ /bug-fix "Upload fails >1MB (limit 5MB)"

Creating issue... Team? > Product | Priority? > High
Created: UPLOAD-78
[executing-bug-fixes runs]
Root cause: Using DEFAULT_SIZE not MAX_FILE_SIZE
Commit: def456abc
Ready to create PR?
```

## Key Principles

- **Orchestration only** - Logic in executing-bug-fixes skill
- **Systematic** - Investigation before fixes
- **TDD mandatory** - Test first, watch fail, minimal fix
- **Review automatic** - Built into skill
- **Root cause docs** - Code + commit
- **TodoWrite tracking** - Progress visibility
- **Offer PR** - User decides

## Related

- `Skill(executing-bug-fixes)` - Bug fix workflow
- `Skill(systematic-debugging)` - Root cause investigation
- `Skill(test-driven-development)` - TDD methodology
