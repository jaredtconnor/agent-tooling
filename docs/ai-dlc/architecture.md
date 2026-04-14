# AI DLC — Dual-tool skill architecture

**Status:** accepted · **Date:** 2026-04-13 · **Linear:** [OIS-462](https://linear.app/over-index-software/project/ai-dlc-ebdb7596f4de)

## Context

The `~/.skills/` repo holds a library of AI skills (prompt recipes for refine / plan / breakdown / execute, code review, TDD, debugging, etc.). Two coding agents — **Claude Code** and **Cursor** — want to consume these skills, but they look in different places and use different rule formats:

- **Claude Code** reads `skills/<name>/SKILL.md` directly (via the `~/.claude/skills/` symlink into this repo).
- **Cursor** reads `.cursor/rules/<name>.mdc` with its own frontmatter keys (`description`, `globs`, `alwaysApply`).

Hand-maintaining two parallel sources was the first instinct. It guarantees drift. This document records the alternative design and the reasoning behind each choice.

## Decision

**`SKILL.md` is the single canonical source. A generator produces `.cursor/rules/*.mdc`. Generator output is committed and enforced fresh by a pre-commit hook.**

```
skills/<name>/SKILL.md  ──parse──►  scripts/generate_cursor_rules.py
                                               │
                                               ▼
                                 .cursor/rules/<name>.mdc
                                 (committed, auto-attach)
                                               ▲
                         pre-commit hook ──freshness check──┘
```

## Detailed design

### 1. Canonical source

- `skills/<name>/SKILL.md` is the only file a skill author edits.
- Required frontmatter: `name`, `description`.
- Optional: `when_to_use`, arbitrary freeform keys.
- Body is standard markdown; references to `resources/<file>` are kept as relative paths.

### 2. Generator

- `scripts/generate_cursor_rules.py` — single Python 3.11+ script, PyYAML.
- Walks `skills/*/SKILL.md`.
- Emits `.cursor/rules/<name>.mdc` with:
  - `description:` copied verbatim from source.
  - `globs: ""` (reserved for future use).
  - `alwaysApply: false` — rules auto-attach **by description match**, never always-on.
- Prepends a **Cursor-compatibility banner** when the body references Claude-only features (regex match on `Task(` dispatch or `Skill(` cross-calls).

### 3. Freshness enforcement

- `scripts/check_cursor_rules_fresh.py` regenerates into a tempdir and diffs against the committed `.cursor/rules/` tree.
- `.pre-commit-config.yaml` wires the check to run when any `skills/**/SKILL.md` or generator script changes.
- Commit is blocked when the committed tree drifts from the generator output.

### 4. Error policy — fail loudly

All of these raise non-zero with a file path and reason:
- Malformed YAML frontmatter.
- Missing `name:` or `description:` field.
- Two skills declaring the same frontmatter `name:` (collision listed with both paths).

No silent fallbacks. A broken source blocks the commit until the author fixes it.

### 5. Output location

`.cursor/rules/` (Cursor's convention). The earlier non-standard `cursor/rules/` placeholder has been removed.

## Rationale

**Why committed output, not ephemeral?**
A fresh `git clone` must work in Cursor without running any setup script. That rules out "regen on first use."

**Why pre-commit, not CI-only?**
CI-only lets the author ship broken rules through the local flow, then discover it later. The failure should land as close to the mistake as possible.

**Why `alwaysApply: false` for everything?**
Per the spec review, auto-attach by description matches Claude Code's slash-command discipline most closely. "Always on" rules would ambient-context every session.

**Why flag Claude-only features instead of stripping them?**
Skills that dispatch subagents (e.g. `requesting-code-review`) are still useful in Cursor as guidance — the author can follow the process manually. Stripping would hide intent; silence would mislead. A banner is the honest middle ground.

**Why fail loudly instead of graceful degradation?**
Tolerance accumulates drift. A strict front-door is cheaper than a quarantined back-door.

## Consequences

- **Good:** one file to edit per skill; zero drift between Claude and Cursor consumption; malformed sources fail at commit time with an actionable message; new skill authors have one clear workflow.
- **Trade-off:** pre-commit adds a dependency (`pre-commit` framework) for anyone cloning and authoring skills. Consumers (people who only read the rules) have no such dependency.
- **Out of scope:** generators for other agents (Copilot, Windsurf, JetBrains AI). Canonical source is set up to extend later; the Cursor generator is enough for now.

## Implementation

See:

- `scripts/generate_cursor_rules.py`
- `scripts/check_cursor_rules_fresh.py`
- `.pre-commit-config.yaml`
- `tests/test_generator.py`, `tests/test_freshness.py`

Tests are runnable with `uv run pytest`.
