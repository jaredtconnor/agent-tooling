---
name: spec-to-linear
description: "Turn markdown specs, PRDs, or feature documents into a fully structured Linear project with milestones, epics, issues, and sub-issues. Analyzes the current (or referenced) codebase to understand what exists, performs gap analysis against the spec, decomposes work into vertical slices, identifies parallelizable tasks, and creates everything in Linear with proper hierarchy and priorities. Use this skill whenever the user has a markdown document describing something they want to build and wants to plan or track that work in Linear. Also trigger when users mention 'plan this in linear', 'create issues from this spec', 'break this PRD into linear issues', 'scope this feature', 'turn this doc into tasks', or have markdown files they want translated into project management structure. Even if they just say 'I have this spec and want to track the work' -- this is the skill for that."
---

# Spec to Linear

Turn markdown specifications into structured, prioritized Linear work items by analyzing the spec against the actual codebase.

## Overview

This skill bridges the gap between "here's what we want to build" (a markdown document) and "here's the organized work to get there" (Linear project with milestones, issues, and dependencies). It does this by actually reading the codebase to understand what exists, so the resulting work items reflect real implementation effort rather than abstract wishful thinking.

## Prerequisites

Before doing anything else, verify Linear access. Try these in order:

1. **Check for `linctl`**: Run `which linctl`. If found, verify auth with `linctl me`. If that fails, tell the user to run `linctl auth` and try again.
2. **Check for Linear MCP**: If `linctl` is not available, check whether Linear MCP tools are accessible (try listing teams). If MCP works, use that instead.
3. **If neither works**: Tell the user they need Linear access set up. Suggest the `install-linctl` skill if available, or point them to Linear MCP configuration.

Prefer `linctl` when available because it is faster for bulk operations and avoids MCP round-trips. Fall back to MCP tools (`mcp__claude_ai_Linear__*`) when `linctl` is not installed.

## The Workflow

### Step 1: Gather Inputs

Identify the markdown file(s) the user wants to plan from. These might be:
- A single spec or PRD file
- Multiple related documents (e.g., a spec + API design + data model)
- Inline markdown the user pastes into the conversation

Read all input documents thoroughly. As you read, build a mental model of:
- **What is being proposed** -- features, systems, integrations, migrations
- **Implicit dependencies** -- things that must exist before other things can work
- **Scope signals** -- is this a weekend project or a multi-month initiative?
- **Ambiguities** -- things the spec leaves unclear that affect implementation

### Step 2: Explore the Codebase

Explore the current repository (or the one referenced in the spec) to understand what already exists. Focus on:

- **Tech stack and architecture** -- frameworks, languages, patterns in use
- **Relevant existing code** -- modules, services, or components that relate to the spec
- **Testing patterns** -- how tests are structured, what coverage looks like
- **Infrastructure** -- deployment setup, CI/CD, database schemas

Use parallel exploration agents when the codebase is large. The goal is to understand the delta between "what exists" and "what the spec describes" -- not to read every file.

### Step 3: Gap Analysis

Compare the spec against the codebase and produce a structured gap analysis:

- **Already exists**: Parts of the spec that the codebase already satisfies (partially or fully)
- **Needs modification**: Existing code that needs changes to meet the spec
- **Net new**: Things that don't exist at all and must be built from scratch
- **Infrastructure/tooling**: Supporting work like migrations, config changes, new dependencies
- **Unknowns**: Areas where you can't determine the gap without more information

Present this analysis to the user before proceeding. It shapes everything downstream, so it is worth getting right.

### Step 4: Decompose into Vertical Slices

Break the work into vertical slices -- each slice should deliver a coherent, testable increment of value. A good vertical slice:

- Touches all necessary layers (data, backend, frontend, tests) for one piece of functionality
- Can be developed and reviewed independently
- Has a clear "done" definition
- Ideally can be shipped or demonstrated on its own

Avoid horizontal slices like "set up all database tables" or "build all API endpoints" -- these create integration risk and delay feedback. The exception is foundational infrastructure work (like setting up a new service or database) that genuinely blocks everything else; put that in its own slice and mark it as a blocker.

For each slice, determine:
- **Dependencies**: Which slices block which others
- **Parallelizability**: Which slices can be worked on simultaneously by different people
- **Relative size**: T-shirt estimate (XS, S, M, L, XL) based on your understanding of the codebase
- **Risk level**: Where are the unknowns, complex integrations, or performance concerns

### Step 5: Map to Linear Hierarchy

Translate the decomposition into Linear's organizational structure:

**Project**: One project per spec/initiative. This is the top-level container.
- Name it clearly after the feature or initiative
- Write a description summarizing the goal and linking to the source spec
- Set appropriate priority

**Milestones**: Group slices into milestones that represent meaningful checkpoints.
- Milestone 1 is typically "Foundation" -- the blocking infrastructure work
- Subsequent milestones represent phases of feature delivery
- The final milestone often includes polish, documentation, and cleanup
- Set target dates if the spec includes timeline information

**Issues**: Each vertical slice becomes one or more issues.
- Title format: clear, action-oriented (e.g., "Implement user authentication flow" not "Auth")
- Description includes: acceptance criteria, relevant context from the spec, pointers to existing code
- Set priority (1=Urgent through 4=Low)
- Apply labels for categorization (e.g., `frontend`, `backend`, `infra`, `database`)
- Set estimates based on t-shirt sizing
- Link blocking relationships between issues

**Sub-issues**: Break large issues into implementable sub-tasks.
- Each sub-issue should be completable in roughly a day of focused work
- Include enough context that someone unfamiliar with the full spec could pick it up
- Only create sub-issues when an issue is genuinely too large to work on as a single unit -- do not over-decompose simple work

### Step 6: Dry Run

Before creating anything in Linear, present the full plan to the user:

```
Project: [name]
  Milestone 1: Foundation
    - [Issue title] (priority, size, labels)
      - [Sub-issue]
      - [Sub-issue]
    - [Issue title] (priority, size, labels)
  Milestone 2: [name]
    - [Issue title] blocks: [other issue]
    ...

Parallelizable work:
  - [Issue A] and [Issue B] can be worked simultaneously
  - [Issue C] and [Issue D] can be worked simultaneously after Milestone 1

Total: X issues, Y sub-issues across Z milestones
```

Ask the user to confirm, modify, or abort. Common adjustments:
- Changing scope (removing or deferring items)
- Adjusting priorities
- Renaming things
- Collapsing or expanding the hierarchy
- Changing milestone boundaries

### Step 7: Create in Linear

Once the user approves, create everything in Linear in the correct order:

1. **Discover the team**: List teams and use the appropriate one. If multiple teams exist and it is not obvious which to use, ask.
2. **Create the project** with description and priority
3. **Create milestones** within the project, with target dates if available
4. **Create issues** top-down:
   - Create parent issues first (so you have IDs for sub-issues)
   - Set milestone, project, labels, priority, and estimate on each
   - Add blocking relationships after all issues exist (you need the IDs)
5. **Create sub-issues** linked to their parents
6. **Add blocking relations** between issues that depend on each other

When using `linctl`, batch operations where possible:
```bash
# Example linctl commands
linctl issue create --title "..." --team "..." --project "..." --priority 2 --label backend
linctl issue create --title "..." --parent [PARENT-ID] --team "..."
```

When using MCP, call `mcp__claude_ai_Linear__save_issue` for each issue. Create parents first, then children with `parentId` set.

### Step 8: Summary

After creating everything, provide a summary:
- Link to the new Linear project
- Count of items created (project, milestones, issues, sub-issues)
- Suggested starting point: which issues to tackle first
- Any flagged risks or open questions from the spec

## Handling Edge Cases

**Spec is vague or incomplete**: Point out the gaps explicitly. Create issues for the parts that are clear, and create a separate "Spike" or "Research" issue for areas that need clarification. Do not invent requirements -- flag them.

**Spec is massive**: If decomposition yields more than ~30 issues, suggest phasing. Create a project for Phase 1 with the highest-priority slices, and note what is deferred. Better to have a focused, actionable plan than an overwhelming backlog.

**Multiple repos**: If the spec spans multiple repositories, note which issues belong to which repo in the issue descriptions. Create all issues in one Linear project but use labels to distinguish repos.

**Existing Linear project**: If the user wants to add to an existing project rather than create a new one, list their projects and let them choose. Skip project creation and add issues to the selected project.

**No codebase context**: If there is no repository to explore (greenfield project), skip the gap analysis and go straight from spec to decomposition. Note in the issues that there is no existing code to reference.

## Labels

Create or use these label categories as appropriate:
- **Layer**: `frontend`, `backend`, `database`, `infra`, `devops`
- **Type**: `feature`, `bug`, `chore`, `spike`, `documentation`
- **Risk**: `high-risk` for items with significant unknowns

Check existing labels in the workspace before creating new ones to avoid duplicates.

## Priority Guidelines

- **Urgent (1)**: Blocks everything else, or has an immovable deadline
- **High (2)**: Core functionality, on the critical path
- **Normal (3)**: Important but not blocking, standard feature work
- **Low (4)**: Nice-to-have, polish, non-essential improvements

Default most feature work to Normal (3). Foundational/blocking work gets High (2). Only use Urgent for genuine emergencies or hard deadlines.
