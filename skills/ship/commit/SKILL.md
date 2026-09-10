---
name: commit
description: Stage the current work and create a single well-formed git commit whose message matches the repository's own commit convention. Use when the user says "commit", "/commit", "commit this", "commit my changes", or wants work committed in the repo's style. Detects the convention from recent history, prefers Conventional Commits when there is no clear house style, and never adds AI attribution trailers. Commits only; does not push unless explicitly asked.
---

# Commit

Create one clean, correctly formatted commit for the current changes, using the repository's own commit conventions.

## Message-style precedence

Decide the format in this order:

1. **Match the repo's established convention.** Read recent history and follow whatever the project already does. A clear house style is the repository standard and always wins.
2. **Default to Conventional Commits** when history shows no clear, consistent convention, or the repo has no commits yet.
3. When the established convention already is Conventional Commits, the two rules agree — use it.

In short: prefer Conventional Commits, but a clear existing style takes priority.

## Workflow

### 1. Inspect the work

```bash
git status --short
git diff --stat
git diff            # unstaged
git diff --staged   # already staged
```

Understand what changed and why before writing anything. If there is nothing to commit, say so and stop. If a merge/rebase is in progress with unresolved conflicts, stop and report — do not commit a conflicted tree.

### 2. Detect the convention

Read the recent, non-merge history:

```bash
git log --no-merges --pretty=format:'%s' -20
```

Classify the subjects:

- **Conventional Commits** if most match `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\([^)]+\))?!?: .+` (roughly 60%+ of the sample).
- **Custom house style** if they consistently follow another shape. Common example: `scope: lowercase summary` where the prefix is a component or file, not a Conventional type (e.g. `sync-chezmoi: quiet external refresh`, `ssh(config.tmpl): per-host identity override`). Match that shape, including how scopes are written.
- **No clear convention** (mixed, or empty repo): use Conventional Commits.

### 3. Decide what to stage

- If changes are already staged and match the intended commit, commit those.
- If nothing is staged, stage the files that belong to this change: tracked edits with `git add -u`, plus new files that are clearly part of the work.
- Do not blindly `git add -A`. Leave unrelated edits, scratch files, build output, and secrets out. When the working tree mixes several unrelated changes, stage only the coherent set and note what you left behind.
- Never stage files matching obvious secret patterns (`.env`, `*.pem`, key material). If the diff appears to contain a secret, stop and warn.

### 4. Write the message

Subject line:

- Match the detected convention exactly (type/scope shape, capitalization).
- Imperative mood, concise, no trailing period, target 50 and keep under ~72 chars.
- Conventional: `type(scope): summary`. Choose the type from the change (`feat` new behavior, `fix` bug, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `style`, `revert`). Scope is optional; use a real module/component name when the repo does.

Body (only when it adds information the diff doesn't):

- Separate from the subject with one blank line; wrap at ~72 chars.
- Explain what changed and why, not a line-by-line restatement of the diff.
- Skip the body entirely for small, self-explanatory changes.

Footers:

- Breaking change: add `!` after type/scope and a `BREAKING CHANGE: <description>` footer.
- Reference issues/tickets in the footer only if the repo already does.

Never add AI attribution: no `Co-Authored-By`, `Generated-by`, `Made-with`, or tool trailers. Keep the author as the repo's configured identity.

### 5. Commit

Prefer a file-based message to preserve blank lines and wrapping:

```bash
git commit -F <(printf '%s\n' "<subject>" "" "<body>")
```

For a subject-only commit, `git commit -m "<subject>"` is fine.

If a pre-commit hook rewrites files (formatters), re-stage the affected files and retry the commit once. If a hook fails, report its output and stop; do not bypass with `--no-verify` unless the user asks.

### 6. Report

State the commit subject and short SHA (`git log --oneline -1`), and note anything left unstaged. Do not push. If the user asked to push (e.g. "commit and push"), push the current branch to its upstream after the commit succeeds.

## Notes

- One logical change per commit. If the staged work spans clearly separate concerns, propose splitting into multiple commits.
- This skill commits; it does not open PRs. Use the pull-request workflow for that.
