# Agent Tooling

Personal engineering skills, commands, hooks, and specialist personas for Claude
Code, Cursor, Codex, Gemini, and other AI coding agents.

The repo follows the same mental model as `addyosmani/agent-skills`:

| Layer | Directory | Job |
| --- | --- | --- |
| Skills | `skills/<phase>/<name>/SKILL.md` | The how: workflows with steps and evidence requirements |
| Agents | `agents/<group>/<name>.md` | The who: personas with a role and output format |
| Commands | `commands/*.md` | The when: user-facing entry points |
| References | `references/*.md` | Shared checklists and reusable guidance |
| Hooks | `hooks/` | Runtime automation |

## Claude Code Plugin

Install this repo as a Claude Code plugin after it is published:

```text
/plugin marketplace add jaredtconnor/agent-tooling
/plugin install agent-tooling@jared-agent-tooling
```

For local development:

```bash
claude --plugin-dir /Users/jaredconnor/.agent-tooling
```

The plugin manifest lives in `.claude-plugin/plugin.json`; marketplace metadata
lives in `.claude-plugin/marketplace.json`.

## Common Commands

```bash
just list          # show skills discovered by npx skills
just verify        # validate skills, agents, plugin metadata, and discovery
just plugin-check  # print Claude plugin install commands
just link          # run dotagents for runtime symlink repair
just install vercel-labs/agent-skills
```

## Skills

Skills are grouped by development lifecycle:

```text
skills/
  define/    # clarify what to build
  plan/      # design and decompose work
  build/     # implement changes
  verify/    # prove behavior and diagnose failures
  review/    # review and respond to feedback
  ship/      # PRs, status updates, release hygiene
  tooling/   # skills for maintaining agent tooling itself
```

Each skill uses the open Agent Skills format:

```markdown
---
name: skill-name
description: What this skill does and when to use it.
---

# Skill Name
```

Run `just verify` after adding or moving skills.

## Agents

Agent personas live in `agents/` and are grouped by role:

```text
agents/
  core/
  languages/
  orchestration/
  specialists/
```

See `agents/README.md` for composition rules. The short version: skills are the
workflow, agents are the perspective, and commands orchestrate. Personas should
not invoke other personas.

## Commands

Commands live in `commands/` as tool-neutral Markdown where possible. The
`.claude/commands` path is a symlink projection for Claude Code compatibility.

## References

Shared material belongs in `references/` when it applies to multiple skills or
agents. Skill-local examples and scripts should stay inside the relevant skill
directory.

## Runtime Projection

The readable root folders are the source of truth. The `.agents/` directory is a
compatibility projection made of symlinks for tools like `dotagents`.

Do not edit generated runtime targets such as `~/.claude/skills`,
`~/.cursor/skills`, or `~/.codex/skills` directly. Update this repo, then run
`just link` if runtime symlinks need repair.

## Work Overlay

Keep public/personal reusable assets here. Put company-specific or private assets
in a separate work repo based on the template created alongside this repo. That
keeps this repo publishable while still giving the work repo the same structure.
