# Parallel Execution Pattern

Advanced pattern for PR-per-task workflows with multiple concurrent tasks.

## When to Use

- Parent issue with multiple sub-issues
- Need separate PR for each task
- Tasks can be worked on in parallel

## Two-Level Hierarchy

```
~/worktrees/my-repo/
├── feature-PROJ-123/                    # Executor (feature branch)
├── feature-PROJ-123-task-124-auth/      # Task 1 → PR to feature
├── feature-PROJ-123-task-125-api/       # Task 2 → PR to feature
└── feature-PROJ-123-task-126-ui/        # Task 3 → PR to feature
```

## Flow

1. Create executor worktree for feature branch
2. For each task:
   - Create task branch from feature
   - Create task worktree
   - Implement, create PR to feature branch
   - On merge, cleanup task worktree
3. After all tasks: PR feature → main
4. Cleanup executor worktree

## Task Branch Creation

```bash
# From executor worktree, create task branch from current feature branch
cd ~/worktrees/my-repo/feature-PROJ-123
git gtr new "feature/PROJ-123-task-124-auth" --from-current
```

## Simpler Alternative

For most workflows, a single worktree per feature is sufficient:

```bash
git gtr new feature/my-feature
# Do all work here
# Create single PR to main
```

Use the two-level pattern only when you need:
- Separate PRs per task for review
- Parallel work on multiple tasks
- Clear isolation between sub-issues
