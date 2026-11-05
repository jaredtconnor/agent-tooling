---
name: grok-pr-core
description: Shared engine for the grok-pr, grok-pr-self and grok-pr-feedback skills (renderer, local triage server, GitHub posting, schema, comment style, scrutiny config). Not a workflow on its own; use one of those three skills, which send you here for the shared steps.
---

# Grok PR core

Shared tooling for three skills that sit next to this directory:

| Skill | Mode | For |
| --- | --- | --- |
| `grok-pr` | `review` | someone else's PR: findings become a pending GitHub review |
| `grok-pr-self` | `self` | your own branch or PR before review: findings become fixes |
| `grok-pr-feedback` | `respond` | review comments on your PR: assessments, fixes and replies |

## Contents

- [references/process.md](references/process.md): the shared steps (setup, context, intent, chapters, structure, findings, canvas, render, serve, the page). Each skill says which steps it changes.
- [references/guide-schema.md](references/guide-schema.md): `guide.json` fields, including `respond` items.
- [references/comment-style.md](references/comment-style.md): how anything that gets posted is written.
- `scripts/grok_pr.py`: `hunks`, `render`, `serve`, `post`, `fixes`, `config`, `threads`. Standard library plus `gh`. Run with `--help`.
- `assets/template.html`, `assets/canvas.json`: the page and the review-canvas checklist.

## Config

One config for all three skills: `~/.config/grok-pr/config.json`, then a repo's `.grok-pr.json` on top. `scrutiny` is `light` (default: report major and up; blockers and majors start accepted), `standard` (minor and up) or `strict` (everything; nothing starts accepted). `minSeverity` and `autoAccept` override the preset. `grok_pr.py config --repo <repo>` prints the effective values.
