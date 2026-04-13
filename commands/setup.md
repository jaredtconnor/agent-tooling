---
description: Initialize repository with comprehensive AI-optimized documentation and tooling setup
---

# Initialize Repository

Complete setup workflow: verify tooling, generate documentation, create justfiles, configure pre-commit hooks.

**Philosophy: Start Minimal, Expand on Request**

## Workflow Overview

Sequential phases (each must complete before proceeding):

0. **Initial Setup Check** - Detect existing artifacts, ask user preference
1. **Project Management Setup** - Configure Linear/JIRA/GitHub integration
2. **Generate Documentation** - Create CLAUDE.md system
3. **Setup Justfiles** - Create command runners
4. **Setup Pre-commit Hooks** - Configure quality checks

---

## Phase 0: Initial Setup Check

**Detect existing artifacts:**

```bash
test -f CLAUDE.md && echo "CLAUDE.md exists"
test -f justfile && echo "justfile exists"
test -f .pre-commit-config.yaml && echo ".pre-commit-config.yaml exists"
```

**If artifacts exist, ask user:**

- **Continue**: Update/amend (ask before overwriting each file)
- **Skip**: Exit gracefully
- **Start fresh**: Backup to `.setup-backups/$(date +%Y%m%d-%H%M%S)/` then proceed

```bash
# Backup command (if "Start fresh" selected)
mkdir -p .setup-backups/$(date +%Y%m%d-%H%M%S)
mv CLAUDE.md justfile .pre-commit-config.yaml .setup-backups/$(date +%Y%m%d-%H%M%S)/ 2>/dev/null || true
```

---

## Phase 1: Project Management Setup

**Invoke skill:**

```
Skill(configuring-project-management)
```

**Skill handles:** User interview (Linear/JIRA/GitHub/None), MCP verification, authentication, project/epic ID recording.

**On failure:** If MCP not installed → provide instructions and stop. If auth fails → ask user to fix. User can decline PM setup (optional).

---

## Phase 2: Generate Documentation

**Check existing docs:**

```bash
find . -name "CLAUDE*.md" | sort
```

If exists → ask user to update/skip. Only proceed if confirmed.

**Invoke skill:**

```
Skill(generating-agent-documentation)
```

**Skill handles:** Repository scan, module discovery, tooling detection, interactive confirmation, minimal doc generation (CLAUDE.md by default), optional additional files (asks first).

---

## Phase 3: Setup Justfiles

**Check existing build automation:**

```bash
find . -name "justfile" -o -name "Makefile" | sort
```

If exists → ask user to update/skip. Show recipes and offer additions.

**Invoke skill:**

```
Skill(writing-justfiles)
```

**Skill handles:** Tooling detection, minimal justfile creation (only existing tooling), user prompts for additions, root orchestration, verification via `just --list`.

---

## Phase 4: Setup Pre-commit Hooks

**Check existing config:**

```bash
test -f .pre-commit-config.yaml
```

**If exists, ask user:** Keep as-is / Add hooks / Replace completely

**If not exists, ask user:** "Set up pre-commit hooks?" (Yes/No)

If declined or "Keep as-is" → skip to Final Verification.

**Invoke skill:**

```
Skill(setting-up-pre-commit)
```

**Skill handles:** Tooling detection, minimal config (conventional commits + basic checks), language-specific hook suggestions, installation, initial run, justfile recipe addition.

---

## Final Verification

**Run checks for completed phases:**

```bash
# 1. Backup verification
ls -la .setup-backups/ 2>/dev/null || echo "No backups"

# 2. PM metadata check
grep -A 5 "## Project Management" CLAUDE.md 2>/dev/null

# 3. Documentation verification
find . -name "CLAUDE*.md" | sort

# 4. Justfile verification
just --list
for dir in $(find . -name justfile -exec dirname {} \;); do
    (cd "$dir" && just --list)
done

# 5. Pre-commit verification (if configured)
pre-commit --version && ls -la .git/hooks/pre-commit .git/hooks/commit-msg
pre-commit run --all-files

# 6. Smoke test
cd [module-dir] && just lint && just format && just test
```

---

## Summary Report

```markdown
# Repository Setup Complete

## Phase 0: Initial Setup Check
✅ Artifacts: [List / None]
✅ Decision: [Continue/Skip/Start Fresh]
✅ Backups: [Path / N/A]

## Phase 1: Project Management Setup
✅ Tool: [Linear/JIRA/GitHub/None]
✅ Project/Epic: [ID / N/A]
✅ MCP Status: [Verified / N/A]

## Phase 2: Documentation Generated
✅ Repository type: [monorepo/multi-module/single]
✅ Top-level CLAUDE.md: [Created/Updated/Kept]
✅ Module docs: [N modules]
✅ Additional docs: [List / None]

## Phase 3: Justfiles Created
✅ Root justfile: [Created/Updated/Kept]
✅ Module justfiles: [N modules]
✅ Commands verified: [Yes/Partial]

## Phase 4: Pre-commit Hooks Setup
✅ Configuration: [Created/Updated/Kept/Skipped]
✅ Hooks: [List / N/A]
✅ Status: [Installed / Skipped]

## Available Commands

Root: `just --list`, `install`, `format`, `lint`, `test`, `build`, `pre-commit-install`, `pre-commit-run`

Module: `just install`, `format`, `lint`, `test [PATH]`, `build`, `dev`, `clean`

## Next Steps

1. Review CLAUDE*.md files
2. Test justfile commands
3. Commit: `git add CLAUDE*.md justfile .pre-commit-config.yaml && git commit -m "chore: initialize repository foundations"`
```

---

## Error Handling

**Phase 0:** Backup fails → ask alternative location. User skip → exit. Detection fails → manual confirm.

**Phase 1:** MCP not installed → instructions and stop. Auth fails → fix and retry. User declines → continue (optional).

**Phase 2:** User rejects structure → re-scan. Tooling fails → ask clarification. Doc conflicts → ask resolution.

**Phase 3:** Show failed module and missing tooling. Justfile conflicts → ask resolution. Continue with remaining.

**Phase 4:** Install fails → manual instructions. Hook fails → offer skip. Config conflicts → ask resolution. Continue to verification (non-critical).

---

## Notes

**Orchestrates skills only. Implementation in:**

- `Skill(configuring-project-management)`
- `Skill(generating-agent-documentation)`
- `Skill(writing-justfiles)`
- `Skill(setting-up-pre-commit)`
