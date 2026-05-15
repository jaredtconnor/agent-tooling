# Agent Tooling Repository

This repository is the source of truth for reusable AI tooling.

## Source Layout

- `skills/` contains Agent Skills-compatible workflows with `SKILL.md` files.
- `agents/` contains reusable personas and subagent prompts.
- `commands/` contains user-facing workflow entry points.
- `hooks/` contains runtime automation scripts.
- `references/` contains shared guidance used by multiple assets.
- `.agents/` is a compatibility projection, not the editing source.

## Working Rules

- Edit the readable root folders first, then refresh projections.
- Keep generated runtime targets out of source control unless they are intentionally part of the repo contract.
- Prefer `npx skills` for skill discovery and installation workflows.
- Use repo-managed projection logic for agents, commands, hooks, and plugin metadata.
- Run `just verify` before committing structural changes.
