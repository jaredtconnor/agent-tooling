# AI Tooling

Shared AI skills, agents, commands, and hooks used by both **Claude Code** and **Cursor**. Everything in this directory is symlinked into `~/.claude/` and `~/.cursor/` via Dotbot -- there is no plugin system; these are just files on disk.

## How It Works

Dotbot creates directory-level symlinks so both tools see the same source of truth:

| Source | Claude Code | Cursor |
|--------|-------------|--------|
| `tools/ai/skills/` | `~/.claude/skills` | `~/.cursor/skills` |
| `tools/ai/agents/` | `~/.claude/agents` | `~/.cursor/agents` |
| `tools/ai/commands/` | `~/.claude/commands` | -- |
| `tools/ai/hooks/` | registered in `.claude/settings.local.json` | -- |
| `tools/ai/claude/` | `~/.claude/settings.json` | -- |
| `tools/ai/cursor/rules/` | -- | `~/.cursor/rules/` |
| `tools/ai/ccstatusline/` | `~/.config/ccstatusline/settings.json` | -- |

Adding a file in the right directory makes it available immediately after `just link`.

## Directory Structure

```
tools/ai/
  skills/              Shared skills (SKILL.md format)
  agents/              Shared subagent definitions (.md with YAML frontmatter)
    core/              General-purpose (debugger, code-searcher, datetime, UI/UX)
    languages/         Language specialists (Go, Rust, Python, JS, C#, Ruby)
    orchestration/     Coordination (project-analyst, team-configurator, tech-lead)
    specialists/       Domain experts (AI/ML, security, performance, search, git)
  commands/            Claude Code slash commands (invoked via /command-name)
  hooks/               Shell scripts triggered by Claude Code events
  claude/              Claude Code global settings (settings.json)
  cursor/              Cursor-specific config (rules/*.mdc)
  ccstatusline/        Claude Code status line config
```

## Inventory by Domain

Check this inventory before creating anything new to avoid duplicates.

### Software Development Lifecycle (SDLC)

Planning, implementation, review, and QA workflow skills.

| Name | Type | Purpose |
|------|------|---------|
| `dev` | skill | Composable pipeline: plan, implement, review, qa (cascading phases) |
| `dev-plan` | skill | Architecture and planning step for the dev workflow |
| `dev-review` | skill | Lightweight code review (categorizes findings by severity) |
| `code-review-gate` | skill | Tech Lead review gate (approved/needs_revision/rejected) |
| `qa-review-gate` | skill | QA Lead health assessment (pattern analysis, drift detection) |
| `tdd` | skill | Test-driven development with red-green-refactor loop |
| `lint` | command | Python linter (flake8, black, isort, pylint, mypy) |
| `test` | command | Python test runner (pytest, unittest, Django) |
| `check-best-practices` | command | Language-specific best practices review |
| `security-audit` | command | OWASP checklist and vulnerability scanning |

### Agent Orchestration and Task Management

Decomposing complex work into slices and coordinating multi-agent execution.

| Name | Type | Purpose |
|------|------|---------|
| `orchestration-setup` | skill | Decompose work into slices, write `.orchestration/config.yaml` |
| `run-orchestration` | skill | Execute orchestration plan slice-by-slice with quality gates |
| `task-execution` | skill | Generic task execution for orchestration workers |
| `create-subagent` | skill | Create new subagent definitions |
| `create-skill` | skill | Skill creation workflow |
| `create-rule` | skill | Cursor rule creation |
| `project-analyst` | agent | Tech-stack detection and architecture pattern recognition |
| `team-configurator` | agent | AI team setup, auto-detects stack, updates CLAUDE.md |
| `tech-lead-orchestrator` | agent | Senior lead for multi-step development and task delegation |

### Code Intelligence and Analysis

Understanding, exploring, and refactoring codebases.

| Name | Type | Purpose |
|------|------|---------|
| `repo-explorer` | skill | Deep codebase exploration with parallel subagents |
| `analyze-codebase` | command | Comprehensive directory structure analysis |
| `refactor-code` | command | Analysis-only refactoring planning (generates reports) |
| `extract-git-lessons` | command | Mine commit history for patterns and lessons |
| `code-searcher` | agent | Elite codebase analysis with Chain of Draft methodology |
| `debugger` | agent | Root cause analysis specialist |

### Language Specialists

Agents with deep expertise in specific languages and ecosystems.

| Name | Type | Languages/Ecosystem |
|------|------|---------------------|
| `csharp-pro` | agent | C#, .NET, SOLID patterns |
| `golang-pro` | agent | Go, concurrency, channels, interfaces |
| `javascript-pro` | agent | ES6+, async patterns, Node.js |
| `python-specialist` | agent | Type hints, async, decorators, design patterns |
| `ruby-pro` | agent | Metaprogramming, Rails, gems |
| `rust-pro` | agent | Ownership, lifetimes, async/Tokio |

### Domain Specialists

Agents with deep expertise in specific technical domains.

| Name | Type | Domain |
|------|------|--------|
| `ai-ml-engineer` | agent | LLM integration, recommendation systems, RAG |
| `performance-engineer` | agent | Profiling, load testing, caching, CDN |
| `search-specialist` | agent | Web research, fact verification, synthesis |
| `security-specialist` | agent | OWASP, prompt injection, Trivy, Azure security |
| `ui-designer` | agent | Visual design for rapid sprints |
| `ux-design-expert` | agent | UX optimization, design systems, Tailwind, Highcharts |

### Tooling and Utilities

Workspace management, git hygiene, and tool configuration.

| Name | Type | Purpose |
|------|------|---------|
| `shell` | skill | Shell command wrapper |
| `install-linctl` | skill | Linear CLI installer |
| `skill-installer` | skill | Install skills from shared Notion database |
| `skill-publisher` | skill | Publish skills to shared Notion database |
| `update-cursor-settings` | skill | Modify Cursor/VSCode settings.json |
| `unify-agent-docs` | skill | Consolidate CLAUDE.md and AGENTS.md |
| `git-clean-coauthors` | skill | Scrub AI co-author trailers from git history |
| `git-history-cleaner` | agent | AI co-author cleanup with git-filter-repo |
| `get-current-datetime` | agent | TZ-aware date/time |
| `update-claudemd` | command | Auto-update CLAUDE.md based on git changes |
| `update-memory-bank` | command | Update memory bank files |
| `cleanup-context` | command | Memory bank context optimization |

## Hooks

Hook scripts live in `tools/ai/hooks/` and are registered in `.claude/settings.local.json` under the `hooks` key. They are **not** loaded from a separate hooks.json.

| Script | Triggers On | Purpose |
|--------|-------------|---------|
| `tech-lead-check.sh` | UserPromptSubmit, PreToolUse | Suggests tech-lead-orchestrator for coordination |
| `enforce-best-practices.sh` | PostToolUse (Write/Edit) | Notifies on significant changes |
| `memory-sync.sh` | PostToolUse (Write/Edit) | Monitors memory bank file sizes |
| `compound-engineering.sh` | PostToolUse (Write/Edit/Task) | Captures lessons from code changes |

## Manifest Formats

### Skill (SKILL.md)

Each skill lives in its own directory: `tools/ai/skills/<skill-name>/SKILL.md`.

```yaml
---
name: skill-name
description: >-
  When this skill should be invoked. Be specific -- this text is used
  for auto-invocation matching.
argument-hint: '[optional] "args hint"'    # optional
version: 1.0.0                             # optional
---

# Skill Title

Instructions for the AI agent when this skill is invoked...
```

Complex skills can include supporting docs:

```
skills/my-skill/
  SKILL.md              # Required: skill definition
  references/           # Optional: supporting docs loaded on demand
    example.md
  scripts/              # Optional: helper scripts
    helper.py
```

### Agent (.md)

Single markdown files in `tools/ai/agents/<category>/<agent-name>.md`.

Categories: `core`, `languages`, `orchestration`, `specialists`.

```yaml
---
name: agent-name
description: What this agent does and when to use it
tools: Read, Edit, Bash, Grep, Glob    # optional: restrict available tools
model: sonnet                           # optional: sonnet (default), opus, haiku
color: red                              # optional: terminal color
---

System prompt for the agent when spawned as a subagent...
```

### Command (.md)

Single markdown files in `tools/ai/commands/<command-name>.md`. Invoked via `/command-name` in Claude Code. Commands are plain markdown with no YAML frontmatter.

```markdown
# Command Title

Instructions for what the command does when invoked...
```

### Hook (.sh)

Shell scripts in `tools/ai/hooks/`. Registered in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.dotfiles/tools/ai/hooks/my-hook.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Adding New Items

1. **Check the inventory above first** -- avoid creating duplicates or near-duplicates
2. **Pick the right type**: skill (interactive workflow), agent (spawnable specialist), command (one-shot slash command), hook (automatic trigger)
3. **Pick the right category** for agents: core, languages, orchestration, specialists
4. **Follow the manifest format** above exactly
5. **Run `just link`** to update symlinks after adding new files
6. **Update this README** with the new item in the appropriate domain table
