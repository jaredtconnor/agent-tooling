---
description: Create a pull request with comprehensive description, diagrams, and visual documentation
---

# PR - Pull Request Creation Command

Create a pull request with a clear, human-readable description that effectively communicates what was implemented using diagrams and visual aids.

## Usage

```bash
/pr                       # Create PR for current branch
/pr --draft               # Create draft PR
/pr --title "Custom title"  # Override generated title
/pr --base develop        # Specify base branch
```

## Requirements

**GitHub CLI (`gh`):**

- Installed and authenticated
- Access to repository

**Git repository with:**

- Commits on current branch not in default branch
- Clean working directory (or explicitly allow dirty)
- Remote repository configured

**Optional:**

- PM system (Linear/JIRA) MCP for issue context
- PR template in `.github/pull_request_template.md`

## How It Works

This command invokes the `creating-pull-requests` skill to:

1. **Gather context** - Branch, commits, diffs, PM system issues
2. **Detect PR template** - Check standard locations
3. **Analyze changes** - Categorize by type (features/fixes/refactors/tests/docs/chores)
4. **Generate description** - Comprehensive PR body with diagrams
5. **Create PR** - Push branch and create PR via `gh` CLI
6. **Add labels** - Based on change types detected
7. **Report success** - PR URL and next steps

**See:** `skills/creating-pull-requests/SKILL.md` for complete workflow details.

## Orchestration Steps

```bash
# 1. Announce skill invocation
echo "I'm using the creating-pull-requests skill to create a pull request."

# 2. Gather PR context
CURRENT_BRANCH=$(git branch --show-current)
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git log $DEFAULT_BRANCH..HEAD --oneline
git diff $DEFAULT_BRANCH...HEAD --stat

# 3. Invoke creating-pull-requests skill
# Skill handles:
# - PR template detection
# - Change analysis and categorization
# - Description generation with diagrams
# - PM system integration
# - PR creation via gh CLI
# - Label application

# 4. Report PR URL and next steps
echo "✅ Pull request created!"
echo "PR URL: <url>"
echo "Next steps:"
echo "1. Review description and edit if needed"
echo "2. Request reviewers: gh pr edit <number> --add-reviewer @username"
echo "3. Track feedback: /address-feedback <number>"
```

## Error Handling

### No Commits on Branch

```
ERROR: No commits on current branch different from {base}

Options:
1. Make changes and commit them first
2. Check if you're on the correct branch: git branch
3. Check if changes were already merged: git log {base}..HEAD
```

### PR Already Exists

```
⚠️ Pull request already exists for this branch

Existing PR: #145 "feat: Add user authentication"
URL: https://github.com/org/repo/pull/145

Options:
1. Update existing PR (new commits auto-added)
2. Cancel
```

### GitHub CLI Not Authenticated

```
ERROR: GitHub CLI not authenticated

Please authenticate with GitHub:
gh auth login

Then retry: /pr
```

### No Remote Branch

```
Branch not pushed to remote yet.

Pushing branch to origin...
✓ Branch pushed: {branch} → origin/{branch}

Continuing with PR creation...
```

### Dirty Working Directory

```
⚠️ Uncommitted changes in working directory

Files with changes:
- src/file.ts (modified)
- tests/test.ts (modified)

Options:
1. Commit changes first (recommended)
2. Stash changes: git stash
3. Create PR anyway (uncommitted changes not included)
4. Cancel
```

## Advanced Options

### Custom Title

Override automatic title generation:

```bash
/pr --title "feat(auth): implement OAuth2 flow"
```

### Draft PR

Create as draft (not ready for review):

```bash
/pr --draft
```

Then mark ready later:

```bash
gh pr ready {number}
```

### Specify Base Branch

Use non-default base branch:

```bash
/pr --base develop
```

### Add Reviewers After Creation

```bash
/pr
# Then:
gh pr edit {number} --add-reviewer @alice,@bob
```

### Add to Project Board

```bash
/pr
# Then:
gh pr edit {number} --add-project "Sprint 23"
```

## PR Title Format

**Automatic format:** `[type]: Brief description`

**Types:**

- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `docs` - Documentation only
- `test` - Test changes
- `chore` - Maintenance/tooling
- `perf` - Performance improvement

**Override with `--title` flag** (see Advanced Options above).

## Integration

**Uses:**

- `creating-pull-requests` skill for PR generation logic
- `gh` CLI for GitHub operations
- `git` commands for repository analysis
- PM system MCP (optional) for issue context

**Called by:**

- User directly: `/pr`
- `/execute` at end of execution (with confirmation)

**Pairs with:**

- `/address-feedback` - Process review comments
- `/execute` - Implementation that leads to PR

## Best Practices

1. **Run when ready** - All tests passing, code reviewed by self
2. **Clean branch** - Rebase/squash commits if needed before PR
3. **Link issues** - Ensure commits reference issue IDs
4. **Review description** - Edit generated description if needed
5. **Add reviewers** - Request reviews promptly after creation
6. **Use draft** - Mark as draft if not ready for review
7. **Update template** - If project has template, keep it current

## Remember

- Comprehensive descriptions make review easier
- Diagrams clarify complex changes significantly
- Use project's PR template if it exists
- Link related PM system issues
- Test information is crucial for reviewers
- Breaking changes need clear migration guides
- Screenshots help for UI changes
- PR creation is the last step after implementation is complete
