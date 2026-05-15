# AI DLC — Agent Tooling Architecture

**Status:** current · **Date:** 2026-05-07

## Decision

The readable root tree is the source of truth:

```text
skills/       workflows
agents/       personas and subagents
commands/     user-facing entry points
references/   shared checklists and examples
hooks/        runtime automation
```

`.agents/` is a compatibility projection for tools that expect that directory
shape. It is not where authors should make changes.

## Model

| Layer | Directory | Role |
| --- | --- | --- |
| Skills | `skills/<phase>/<name>/SKILL.md` | The how |
| Agents | `agents/<group>/<name>.md` | The who |
| Commands | `commands/*.md` | The when |
| References | `references/*.md` | Shared support material |

This follows the structure used by production skill repos such as
`addyosmani/agent-skills`: keep concepts distinct, then project them into each
tool's preferred runtime paths.

## Plugin Packaging

Claude Code plugin metadata lives in `.claude-plugin/`:

```text
.claude-plugin/
  marketplace.json
  plugin.json
```

Expected install flow after publishing:

```text
/plugin marketplace add jaredtconnor/agent-tooling
/plugin install agent-tooling@jared-agent-tooling
```

`plugin.json` points Claude Code at:

- `commands`
- `skills`
- explicit agent persona files under `agents`

## Skills Layout

Skills are grouped by lifecycle:

```text
skills/
  define/
  plan/
  build/
  verify/
  review/
  ship/
  tooling/
```

`npx skills` discovers nested `SKILL.md` files under `skills/`, so lifecycle
folders improve readability without breaking installability.

## Repo Boundary

Use this repo for reusable personal/public assets. Use a separate private work
repo for company-specific skills, browser automation, internal tools, and
anything that should not be published.

Avoid splitting by agent tool. The same source content should be projected into
Claude Code, Cursor, Codex, Gemini, and other tools.

## Verification

```bash
just verify
just plugin-check
npx skills add . --list
```
