# Technical Plan: Phase 1 — Cross-tool architecture

**Issue:** OIS-462 (parent) + OIS-469 (architecture spec), OIS-470 (generator), OIS-471 (README docs)
**Date:** 2026-04-13
**Mode:** local

## Specification Summary

Per OIS-469's refined spec: every skill has a single canonical `SKILL.md`. A generator produces `.mdc` files for Cursor that are committed to the repo, stay fresh via a pre-commit hook, and auto-attach by description matching. Output covers every skill; skills using Claude-only features (Task-tool dispatch, `Skill()` cross-calls) get a visible compatibility note. Generator fails loudly on malformed source. Resources are referenced by path, not inlined. Target audience: me + any machine I clone the repo to.

## Architecture Overview

Three small parts: a **Python generator script**, a **pre-commit integration**, and **documentation**. The generator is a single file (~150 lines) that discovers `skills/*/SKILL.md`, parses YAML frontmatter, emits one `.mdc` per skill into `.cursor/rules/`, and uses the `pre-commit.com` framework to run automatically. Claude-compat detection is a simple static scan: if a SKILL.md body contains `Task(` or `Skill()` cross-references to agent-dispatching skills, prepend a warning banner. No runtime service, no network calls, no state — just a deterministic transformation from `skills/` to `.cursor/rules/`.

Flow:

```
skills/<name>/SKILL.md  ──parse──>  frontmatter + body
                                         │
                                         ▼
                     ┌───────────────────────────┐
                     │ scripts/generate_cursor_  │
                     │    rules.py               │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                         .cursor/rules/<name>.mdc
                         (committed, auto-attach)
                                   ▲
            pre-commit hook ──regen+verify──┘
```

## Key Technology Choices

**Language — Python 3.13** (already in environment, PyYAML 6.0.3 installed). No alternative considered; matches the user's toolchain (`uv`, mise). Bash would require shelling out for YAML parsing; Node would introduce a dependency footprint.

**YAML parsing — PyYAML** (already installed). Handles frontmatter parsing + graceful error messages for the fail-loudly requirement.

**Pre-commit framework — `pre-commit.com`** (portable, distributes via `.pre-commit-config.yaml` that travels with the repo). Rejected alternative: hand-rolled git hook in `.git/hooks/pre-commit` (doesn't travel with clones, fails the portability requirement from OIS-469 spec).

**Output location — `.cursor/rules/`** per Cursor's convention. The existing non-standard `cursor/rules/` placeholder will be removed. Open question confirmed as recommendation, not open — proceeding with `.cursor/rules/`.

**Frontmatter mapping** — generator reads source `name`, `description`, and optional `cursor:` block. Emits Cursor-compatible frontmatter: `description:` (copied), `globs:` (from `cursor.globs` if present, else omitted), `alwaysApply: false` (per OIS-469 decision to auto-attach by description, not always-on).

**Testing — pytest** (install via `uv tool install pytest` or project venv). TDD per OIS-470.

## Implementation Approach

**Key components to build:**

- `scripts/generate_cursor_rules.py` — the generator. Walks `skills/*/SKILL.md`, parses frontmatter, emits `.cursor/rules/<name>.mdc`. Detects Claude-only patterns via regex on body (`Task\(`, `Skill\([^)]+\)` referencing agent-dispatching skills like `code-reviewer`, `executing-*`, `conducting`). Exits non-zero with path + reason on malformed input, missing required fields, or name collision.
- `scripts/check_cursor_rules_fresh.py` — a tiny sibling that runs the generator into a temp dir and diffs against committed `.cursor/rules/`. Used by pre-commit to enforce freshness without mutating the worktree during the hook.
- `.pre-commit-config.yaml` — declares both scripts as repo-local hooks, runs on changes to `skills/**/SKILL.md` or the generator itself.
- `tests/test_generator.py` — covers: valid SKILL.md → valid .mdc; custom `cursor.globs` → passed through; no cursor metadata → defaults (auto-attach, no globs); malformed YAML → exit non-zero; missing `name` or `description` → exit non-zero; name collision → exit non-zero; resource links preserved as paths; Claude-only detection fires when expected; idempotency (running twice = no diff).
- Updated `README.md` (OIS-471) — "Dual-tool architecture" section with diagram, authoring instructions, and pre-commit setup.

**Critical dependencies:**

- OIS-469 (architecture decision) must land before OIS-470 (generator) — the script implements decisions from the spec. [Already refined in Linear.]
- OIS-470 (generator) must work before OIS-471 (README) — docs describe actual behavior.
- OIS-472–476 (Phase 2 Cursor wiring) depend on a working generator.

**Suggested approach:** Start with a thin end-to-end tracer: generator that handles the happy path for a single skill (`refine`), pre-commit wired in, one test. Then extend: (a) compatibility-note detection, (b) error paths, (c) the remaining edge cases, (d) run across all 50+ skills. Move the `cursor/` placeholder to `.cursor/rules/` early to avoid re-doing path wiring.

## Testing Strategy

TDD per the OIS-462 Feature label and OIS-470's explicit "tests first" requirement. Unit tests cover the pure transformation logic (frontmatter → .mdc). One integration test runs the generator against the real `skills/` tree and asserts each skill produces a valid `.mdc` with required fields. A freshness test confirms running the generator twice produces byte-identical output (idempotency). No e2e tests — the Cursor smoke test in OIS-476 validates activation behavior, which is out of scope for this phase.

## Key Patterns

- **Existing pre-commit hook in `~/.config/git/githooks/pre-commit`** — reference for git-hook style, though we're using `pre-commit.com` framework instead for portability.
- **`~/.skills/skills/refine/SKILL.md`** — canonical frontmatter example: `name`, `description`, `when_to_use`. Generator should treat `when_to_use` as informational (not required) and preserve it in the body or as a `description` extension.
- **`~/.skills/cursor/rules/.gitkeep`** — existing placeholder; replace with `.cursor/rules/` early.
- **`pyproject.toml` / `uv` conventions** — user's Python projects use `uv`; the scripts should be runnable standalone without a package install (`python3 scripts/generate_cursor_rules.py`).
