# OIS-462 Phase 3 — Cursor smoke test results

**Status:** pending manual verification
**Date:** 2026-04-13

## Purpose

Validate that the 3 core pipeline rules auto-attach correctly in a real Cursor session, confirming the activation-by-description-match decision from OIS-469.

## Rules under test

- `.cursor/rules/refine.mdc`
- `.cursor/rules/plan.mdc`
- `.cursor/rules/breakdown.mdc`

## Protocol

Open this repo (or any workspace with `.cursor/rules/` present) in Cursor, then issue each trigger prompt below to Cursor's agent. Observe whether the expected rule auto-attaches (usually shown in the chat sidebar or an "attached rules" indicator).

| # | Trigger prompt (natural language) | Expected rule to auto-attach |
|---|-----------------------------------|------------------------------|
| 1 | "Help me refine this rough feature idea into a proper spec." | `refine.mdc` |
| 2 | "I have a refined spec already; create the technical plan for it." | `plan.mdc` |
| 3 | "Break this plan down into sub-issues with vertical slices." | `breakdown.mdc` |

## Results

_Fill in after running manually._

| # | Expected | Actual | Pass/Fail | Notes |
|---|----------|--------|-----------|-------|
| 1 | refine   |        |           |       |
| 2 | plan     |        |           |       |
| 3 | breakdown |       |           |       |

## Known limitations

- Cursor's rule-selection algorithm is opaque; false positives (wrong rule attaching) and false negatives (no rule attaching) are possible based on description phrasing.
- If any test fails, the description field of the corresponding SKILL.md is the first thing to tune. Regenerate with `uv run python -m scripts.generate_cursor_rules skills/`.

## Follow-ups

- If tests 1-3 pass cleanly, expand to the full pipeline (execute, conduct, debugging skills) and document in OIS-476 (Phase 2 end-to-end Cursor smoke test).
- If tests fail, amend OIS-469's spec to note description-engineering constraints.
