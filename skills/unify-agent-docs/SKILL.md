---
name: unify-agent-docs
description: Consolidate CLAUDE.md and AGENTS.md into a single source of truth so both Claude Code and Cursor (and other coding agents) read the same instructions. Use this skill whenever the user mentions combining, merging, unifying, or deduplicating CLAUDE.md and AGENTS.md files, or when they want both tools to share the same project context. Also use when someone asks about setting up AGENTS.md or CLAUDE.md in a new repo and wants cross-tool compatibility.
---

# Unify Agent Docs

Merges CLAUDE.md and AGENTS.md into one file, then symlinks (or copies) so both Claude Code and Cursor see the same content.

## Why this matters

CLAUDE.md is auto-loaded by Claude Code every session. AGENTS.md is the emerging standard recognized by Cursor, Copilot, Windsurf, and other coding agents. Maintaining both separately leads to drift -- instructions diverge, one gets updated while the other goes stale. A single source of truth with a symlink (or copy) for the other filename solves this.

## Workflow

### 1. Assess the current state

Check what exists in the repo root:

```bash
ls -la CLAUDE.md AGENTS.md 2>/dev/null
```

Possible states:
- **Both files exist (separate)** -- need to merge and link
- **Only CLAUDE.md exists** -- create AGENTS.md as symlink/copy
- **Only AGENTS.md exists** -- create CLAUDE.md as symlink/copy
- **One is already a symlink to the other** -- already unified, verify and stop
- **Neither exists** -- help the user create one from scratch, then link

### 2. Detect the platform

Symlinks work differently across platforms:

- **macOS/Linux**: `ln -s` works without special permissions
- **Windows**: Symlinks require Developer Mode enabled or admin privileges. Test with:
  ```bash
  # In PowerShell or cmd
  mklink test_symlink_check CLAUDE.md 2>nul && del test_symlink_check && echo "symlinks OK" || echo "no symlink support"
  ```

If symlinks are not available (Windows without Developer Mode), fall back to file duplication with a header comment noting the canonical source.

### 3. Choose the canonical file

Ask the user which file should be canonical. Default recommendation:

- **CLAUDE.md** as canonical if the user primarily uses Claude Code (most common)
- **AGENTS.md** as canonical if the user primarily uses Cursor or other agents

The other file becomes the symlink (or copy).

### 4. Merge content

If both files exist with different content, merge them intelligently:

1. Read both files
2. Identify sections that overlap (e.g., both describe directory structure, both list conventions)
3. Deduplicate -- keep the more detailed version of overlapping sections
4. Organize the merged content logically:
   - Project overview and quick reference first
   - User preferences and workspace facts (from AGENTS.md "Learned" sections)
   - Directory layout and structure
   - How-to guides (adding symlinks, creating skills/agents)
   - Conventions and rules
   - Issue tracking / workflow sections
   - Session completion / workflow

Present the merged draft to the user for review before writing.

### 5. Create the link (or copy)

**macOS/Linux (symlink):**
```bash
# If CLAUDE.md is canonical:
rm AGENTS.md  # or git rm if tracked
ln -s CLAUDE.md AGENTS.md
```

**Windows (symlink if available):**
```powershell
Remove-Item AGENTS.md
cmd /c mklink AGENTS.md CLAUDE.md
```

**Windows (copy fallback):**
If symlinks are unavailable, copy the file and add a header comment:
```markdown
<!-- AUTO-GENERATED: This file is a copy of CLAUDE.md. Edit CLAUDE.md instead. -->
<!-- To regenerate: copy CLAUDE.md AGENTS.md -->
```

Then warn the user that they'll need to keep the copy in sync manually (or add a git hook/script to do it).

### 6. Verify

After creating the link/copy:

```bash
# Verify symlink
ls -la AGENTS.md CLAUDE.md

# Verify content matches
diff CLAUDE.md AGENTS.md
```

If using git, check that the symlink is tracked correctly:
```bash
git add AGENTS.md
git status
```

Git tracks symlinks natively on all platforms, so even if a Windows user clones the repo, git will recreate the symlink (or create a text file containing the target path if symlinks aren't supported).

### 7. Handle git

Stage and report what changed. Do NOT commit automatically -- let the user decide when to commit. Suggest a commit message like:

```
chore: unify CLAUDE.md and AGENTS.md into single source of truth
```

## Edge cases

- **Submodules or monorepos**: Each package/submodule may have its own CLAUDE.md or AGENTS.md. Only unify at the level the user specifies.
- **Existing symlink in wrong direction**: If AGENTS.md -> CLAUDE.md but the user wants CLAUDE.md -> AGENTS.md, reverse it.
- **CI/CD that reads AGENTS.md**: Warn the user if their CI config references AGENTS.md -- symlinks should work but copies are safer in CI environments.
- **`.gitattributes`**: If the repo has `.gitattributes` with special handling for .md files, the symlink should still work, but mention it.

## Cross-tool compatibility notes

| Tool | File it reads | Symlink support |
|------|--------------|-----------------|
| Claude Code | CLAUDE.md (auto-loaded) | Yes |
| Cursor | AGENTS.md or .cursorrules | Yes |
| GitHub Copilot | AGENTS.md | Yes |
| Windsurf | AGENTS.md or .windsurfrules | Yes |
| Cody | AGENTS.md | Yes |
