---
description: Stage and commit the current work with a message matching the repository's commit convention (prefers Conventional Commits, else the repo's existing style). Commits only; pushes only when asked.
---

# Commit - Convention-Aware Git Commit

Create one well-formed commit for the current changes, using the repository's own commit conventions.

## Usage

```bash
/commit                 # inspect changes, detect convention, commit
/commit <message hint>  # commit using the hint as the summary basis
/commit and push        # commit, then push the current branch
```

## Behaviour

This command uses the `commit` skill, which:

1. Inspects staged and unstaged changes to understand the work.
2. Detects the repo's commit convention from recent history.
3. Prefers Conventional Commits when there is no clear house style; otherwise matches the existing style exactly.
4. Stages the coherent set of relevant files (never blindly `git add -A`, never secrets).
5. Writes an imperative subject (and a body only when it adds information).
6. Commits without any AI attribution trailers, then reports the SHA.

Pushes only when the user asks (e.g. `/commit and push`). Never bypasses failing pre-commit hooks unless told to.

## Examples

```bash
/commit
/commit "quiet the external refresh"
/commit and push
```
