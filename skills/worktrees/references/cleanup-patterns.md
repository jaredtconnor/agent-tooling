# Cleanup Patterns

Strategies for worktree cleanup.

## Quick Cleanup

```bash
# See what would be cleaned
git gtr clean --merged --dry-run

# Clean all merged
git gtr clean --merged
```

## By Category

### Task Worktrees (After PR Merge)

```bash
# Single task
git gtr rm "feature-PROJ-123-task-1-auth" --delete-branch

# All merged tasks for a feature
for wt in ~/worktrees/$REPO_NAME/feature-PROJ-123-task-*; do
    branch=$(basename "$wt")
    state=$(gh pr view "$branch" --json state -q '.state' 2>/dev/null)
    [ "$state" = "MERGED" ] && git gtr rm "$branch" --delete-branch
done
```

### Executor Worktrees (After Feature Merge)

```bash
git gtr rm "feature-PROJ-123" --delete-branch
```

### Stale Worktrees (No Activity)

```bash
# List all worktrees and review manually
git gtr list
```

## Full Cleanup Script

```bash
#!/bin/bash
# cleanup_all.sh

REPO_NAME=$(basename $(git rev-parse --show-toplevel))

echo "=== Cleanup for $REPO_NAME ==="

# 1. Clean merged worktrees
echo "Cleaning merged worktrees..."
git gtr clean --merged

# 2. Prune git references
echo "Pruning references..."
git worktree prune
git remote prune origin

# 3. Clean state files (DLC)
if [ -d ".claude/executor-state" ]; then
    echo "Cleaning executor state files..."
    find .claude/executor-state -name "*.json" -mtime +7 -delete
fi

echo "Done!"
```

## Safety Checklist

Before cleanup, verify:
- [ ] No uncommitted changes in worktree
- [ ] PR is actually merged (not just closed)
- [ ] Not the current working directory
- [ ] Not main/master branch
