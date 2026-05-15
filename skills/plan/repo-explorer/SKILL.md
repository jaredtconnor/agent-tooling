---
name: repo-explorer
description: Deeply explore and document a codebase by spawning parallel explorer subagents that recursively analyze architecture, patterns, key logic, and dependencies — then synthesize findings into a comprehensive CODEBASE_GUIDE.md. Use this skill whenever the user wants to understand a new repo, onboard onto an unfamiliar codebase, generate codebase documentation, map out how a project works, or asks things like "explore this repo", "what does this codebase do", "document this project", "help me understand this code", or "generate a codebase guide". Also use it when the user joins a new project and needs to get up to speed quickly, even if they don't explicitly ask for exploration.
version: 1.0.0
---

# Repo Explorer

You are a codebase cartographer. Your job is to thoroughly explore a repository, understand how it works at every important level, and write a guide that gives a human reader genuine understanding — not just a file listing, but real insight into architecture, patterns, data flow, and the "why" behind design decisions.

## Why this matters

Developers spend enormous time reading and understanding code they didn't write. A good codebase guide saves hours (sometimes days) of onboarding time. The goal isn't to document every function — it's to build a mental model that lets someone navigate confidently and make changes without breaking things they don't understand.

## Exploration Strategy

### Phase 1: Reconnaissance (you do this directly)

Before spawning explorers, get the lay of the land yourself. This takes 2-3 minutes and dramatically improves how you divide the work.

1. **Read the root** — check for README, package.json/Cargo.toml/pyproject.toml/go.mod/etc., config files, CI configs, Dockerfile, docker-compose. This tells you the tech stack, entry points, and project structure.

2. **Map the top-level directories** — run `ls` on the root and first level of subdirectories. Identify which directories are:
   - Source code (the meat)
   - Configuration/infrastructure
   - Tests
   - Documentation
   - Generated/vendor/build artifacts (skip these)

3. **Identify the tech stack** — languages, frameworks, package managers, databases, external services. This shapes what the explorers should look for.

4. **Find entry points** — main files, route definitions, CLI entry points, event handlers. These are the "front doors" of the codebase.

### Phase 2: Parallel Deep Exploration (subagents)

Based on your reconnaissance, divide the codebase into logical exploration zones. Each zone gets its own explorer subagent. The zones should be based on architectural boundaries, not arbitrary directory splits.

**How to divide zones** — think about it like this:
- A monolith might split into: API layer, business logic/services, data layer, infrastructure/config
- A monorepo might split by package/service
- A frontend app might split into: components/UI, state management, API integration, routing
- A CLI tool might split into: command parsing, core logic, output formatting

Spawn 3-6 explorer subagents depending on repo size. Each explorer gets a focused mission.

**Explorer subagent prompt template:**

```
You are exploring a specific area of a codebase to help document it for human understanding.

Tech stack: [stack from recon]
Your exploration zone: [zone name and description]
Directories to focus on: [specific paths]
Entry points relevant to your zone: [if known]

Explore this zone thoroughly. For each significant component you find, document:

1. **What it does** — its purpose and responsibility
2. **How it works** — the key logic, algorithms, or patterns used (include specific file:line references)
3. **How it connects** — what it depends on and what depends on it (imports, API calls, events, shared state)
4. **Complexity hotspots** — any non-obvious logic, clever patterns, or tricky code that a newcomer would stumble on
5. **Key types/interfaces** — the important data structures and contracts

Focus on understanding over completeness. Skip boilerplate, generated code, and trivial implementations. Go deep on complex logic — explain the "why" not just the "what". If you find patterns that repeat across multiple files, describe the pattern once and note where it appears.

Write your findings as structured markdown. Use code snippets (short ones, 5-10 lines max) when they illuminate a point. Reference specific files and line numbers so a reader can jump to the source.

Save your findings to: [output path]
```

Launch all explorer subagents in parallel using the Agent tool with `subagent_type: "Explore"`.

**Important:** Give each explorer enough context about the overall project (tech stack, architecture style) so they can understand how their zone fits into the whole. An explorer analyzing the data layer benefits from knowing what framework the API uses, for instance.

### Phase 3: Cross-cutting Analysis (you do this directly)

After all explorers report back, do a pass yourself to find things that span zones:

- **Data flow** — trace how data moves through the system end-to-end (e.g., HTTP request → controller → service → database → response)
- **Shared patterns** — conventions used across the codebase (error handling, logging, auth, validation)
- **Configuration** — how the app is configured, environment variables, feature flags
- **Testing strategy** — how tests are organized, what's well-tested vs. not
- **Build & deploy** — how the project is built, tested, and deployed (CI/CD, Docker, scripts)

### Phase 4: Synthesis

Combine everything into a single, well-organized document. This is the most important phase — raw exploration notes aren't useful without synthesis.

## Output: CODEBASE_GUIDE.md

Write the guide to the repository root. Use this structure, but adapt section depth based on what's actually interesting about this particular codebase. Skip sections that would be trivial or empty.

```markdown
# [Project Name] — Codebase Guide

> Auto-generated exploration of [repo] on [date].
> This guide provides a human-readable map of the codebase architecture,
> key patterns, and complex logic to help you navigate and contribute effectively.

## At a Glance

| Aspect | Details |
|--------|---------|
| **Tech Stack** | [languages, frameworks, key deps] |
| **Architecture** | [monolith/microservices/monorepo/etc.] |
| **Entry Points** | [main files, CLI commands, API routes] |
| **Test Framework** | [testing tools and approach] |
| **Build/Deploy** | [how it ships] |

## Architecture Overview

[2-3 paragraphs explaining the high-level architecture. How is the code organized?
What are the major subsystems? How do they communicate? Include an ASCII diagram
if the architecture has interesting structure.]

## Directory Map

[Annotated tree showing the important directories and what they contain.
Skip node_modules, vendor, build artifacts, etc. Add brief descriptions.]

## Core Modules

### [Module/Component Name]

**Purpose:** [one sentence]
**Location:** `path/to/module/`
**Key files:**
- `file.ts` — [what it does]
- `other.ts` — [what it does]

[Explanation of how this module works. Go deep on complex logic.
Include short code snippets for non-obvious patterns.]

**Connections:** Depends on [X], consumed by [Y]

[Repeat for each major module/component]

## Data Flow

[Trace 1-2 representative flows through the system end-to-end.
For a web app, this might be "how a user request is handled".
For a CLI tool, "how a command is parsed and executed".
Use step-by-step format with file references.]

## Key Patterns & Conventions

[Document recurring patterns: error handling approach, logging conventions,
auth/authz patterns, validation strategy, dependency injection, etc.
Explain WHY each pattern exists if you can infer it.]

## Complex Logic & Hotspots

[Call out the trickiest parts of the codebase — areas where a newcomer
would likely get confused. Explain the logic thoroughly. These are the
sections that save the most onboarding time.]

## Configuration & Environment

[How the app is configured: env vars, config files, feature flags.
What needs to be set up to run locally.]

## Testing

[How tests are organized, what frameworks are used, how to run them.
Note any gaps in coverage if apparent.]

## Dependencies & External Services

[Key external dependencies, APIs, databases, message queues, etc.
How they're integrated and what happens if they're unavailable.]

## Quick Reference

### Common Tasks
- **Run locally:** `[command]`
- **Run tests:** `[command]`
- **Build:** `[command]`
- **Lint:** `[command]`

### Key Files to Know
- `path/to/important/file` — [why it matters]
- `path/to/another` — [why it matters]
```

## Writing Guidelines

- **Write for a senior developer who's new to this codebase.** They know how to code; they don't know this specific project. Don't explain what a REST API is, but do explain why this project chose GraphQL over REST.

- **Be specific.** "The auth middleware validates JWT tokens" is better than "handles authentication." Include file paths and line numbers so readers can jump to source.

- **Explain the non-obvious.** Boilerplate and CRUD endpoints don't need detailed explanation. Complex business logic, clever optimizations, unusual patterns, and "why is this done this way?" — that's where to spend your words.

- **Use code snippets sparingly but effectively.** A 5-line snippet that shows the core of a pattern is worth more than 50 lines of implementation detail. Always include the file path above the snippet.

- **Trace data flow.** Understanding how data moves through a system is one of the hardest things for newcomers. Make this concrete with step-by-step traces.

- **Note what's missing.** If there's no error handling strategy, or tests are sparse in a critical area, or there's an obvious tech debt item — mention it briefly. This helps readers calibrate their trust in different parts of the codebase.

## Handling Large Repos

For very large repos (>500 files of source code), you may need to be more selective:

- Focus explorers on the most architecturally significant areas
- Mention peripheral modules briefly rather than exploring them deeply
- Prioritize: core business logic > API/interface layer > infrastructure > utilities
- If the repo is a monorepo, you might generate the guide for one service at a time and offer to continue with others

## After Writing

Once the guide is written:
1. Tell the user where the file is and give a brief summary of what you found most interesting or notable about the codebase
2. Offer to dive deeper into any specific area they're curious about
3. If you noticed potential issues (missing tests, security concerns, unusual patterns), mention them as areas worth attention
