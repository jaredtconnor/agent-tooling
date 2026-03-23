---
name: skill-installer
description: Install Cursor skills and sub-agent prompts from the team's shared Notion database to the local filesystem. Resolves and installs dependencies automatically. Use when the user wants to install, list, or browse shared team skills, or mentions installing from Notion.
model: inherit
version: 1.0.0
---

# Skill Installer

Install skills and sub-agent prompts published to the team's Notion database. Resolves dependency graphs and writes files to the correct locations.

## Constants

| Key | Value |
|-----|-------|
| Database data source | `collection://30ab0a7b-c8b2-8060-ae1e-000bc63e5294` |
| Database URL | `https://www.notion.so/30ab0a7bc8b280b09211f1055369fc6b` |

## Entry Types

The database stores two types:

| Type | Installed to | Format |
|------|-------------|--------|
| **Skill** (`Type` = `Skill`) | `{skills-dir}/{skill-id}/SKILL.md` + sub-page files | Folder with frontmatter SKILL.md |
| **Sub-Agent Prompt** (`Type` = `Sub-Agent Prompt`) | `~/.cursor/agents/{skill-id}.md` | Flat file with frontmatter |

Each entry has a **`Project`** property (e.g. "Planning", "Dataverse", "FIS", "All Projects"). Always show the Project value when listing entries so the user can distinguish project-specific versions.

## Workflow

### Step 1 — Find the Entry

**User provides a name or ID** — query for an exact `Skill ID` match first:

```sql
SELECT url, "Skill Name", "Skill ID", "Description", "Category", "Scope", "Type", "Project", "Dependencies"
FROM "collection://30ab0a7b-c8b2-8060-ae1e-000bc63e5294"
WHERE "Skill ID" = '{user_input}'
```

If no exact match, try fuzzy on `Skill Name`:

```sql
SELECT url, "Skill Name", "Skill ID", "Description", "Category", "Scope", "Type", "Project", "Dependencies"
FROM "collection://30ab0a7b-c8b2-8060-ae1e-000bc63e5294"
WHERE "Skill Name" LIKE '%{user_input}%'
```

**User does not specify** — list everything:

```sql
SELECT url, "Skill Name", "Skill ID", "Description", "Category", "Scope", "Type", "Project", "Dependencies"
FROM "collection://30ab0a7b-c8b2-8060-ae1e-000bc63e5294"
ORDER BY "Type", "Project", "Skill Name"
```

Present as a numbered list grouped by type, then project:

- **Skills** — Skill Name, Project, Category, Description (truncated), Scope, dependency count
- **Sub-Agent Prompts** — Skill Name, Project, Description (truncated)

If multiple project-specific versions of the same skill exist, highlight this so the user picks the right one (e.g. "brand-mockup-generator (Planning)" vs "brand-mockup-generator (Dataverse)").

Ask the user to pick one.

### Step 2 — Resolve Dependencies

Check the selected entry's `Dependencies` property (comma-separated Skill IDs):

1. For each dependency ID, query:

```sql
SELECT url, "Skill Name", "Skill ID", "Description", "Type"
FROM "collection://30ab0a7b-c8b2-8060-ae1e-000bc63e5294"
WHERE "Skill ID" = '{dep_id}'
```

2. Build the install list: **dependencies first, parent last**.

3. Present the install plan:

```
Installing "ADO Pull Request Code Review" with 3 dependencies:
  1. bug-scanner-prompt (Sub-Agent Prompt) → ~/.cursor/agents/bug-scanner-prompt.md
  2. sql-standards-prompt (Sub-Agent Prompt) → ~/.cursor/agents/sql-standards-prompt.md
  3. silent-failure-prompt (Sub-Agent Prompt) → ~/.cursor/agents/silent-failure-prompt.md
  4. pr-code-review (Skill) → ~/.cursor/skills/pr-code-review/

Skills install to: ~/.cursor/skills/  |  Sub-agent prompts install to: ~/.cursor/agents/
```

4. If a dependency is not found, warn the user and ask whether to continue without it.

### Step 3 — Choose Install Location

**Sub-agent prompts** always go to `~/.cursor/agents/{skill-id}.md`. Not configurable.

**Skills** — ask the user, using the `Scope` property as the suggested default:

| Scope | Default | Path |
|-------|---------|------|
| `Personal` | Personal | `~/.cursor/skills/{skill-id}/` |
| `Project` | Project | `.cursor/skills/{skill-id}/` (workspace root) |
| `Universal` | Personal | `~/.cursor/skills/{skill-id}/` |
| Not set | Ask | Either |

On Windows, `~` resolves to `%USERPROFILE%` (e.g. `C:\Users\{username}`).

### Step 4 — Check for Existing Installs

For each entry in the install list:

- **Skills**: check if `{install_path}/{skill-id}/` exists
- **Sub-agent prompts**: check if `~/.cursor/agents/{skill-id}.md` exists

If exists: warn and ask — overwrite, skip, or abort all.
If a dependency is already installed from a previous skill install, report "already present" and skip unless the user requests an update.

### Step 5 — Fetch and Write

Process each entry (dependencies first, parent last).

#### 5a: Fetch from Notion

1. Fetch the page using its URL from the query result
2. Extract from the fetched page:
   - **Properties**: `Skill ID`, `Description`, `Type`
   - **Body content**: everything in the page content
   - **Sub-pages**: `<page url="...">Title</page>` elements (skills only — ignored for sub-agent prompts)
3. For skills: fetch each sub-page to get additional file contents

#### 5b: Write — Skills

Create directory: `{install_path}/{skill-id}/`

**SKILL.md** — frontmatter + page body:

```markdown
---
name: {Skill ID}
description: {Description}
---

{page body content from Notion}
```

The page body IS the SKILL.md content (minus frontmatter). Write it directly — do not wrap in code blocks or add extra formatting.

**Additional files from sub-pages:**

For each sub-page:
1. Sub-page **title** = **filename** (e.g. `design-tokens.md`, `agent-prompts.md`)
2. Fetch the sub-page content
3. Extract file content using the rules in [references/file-extraction-rules.md](references/file-extraction-rules.md)
4. Write to `{install_path}/{skill-id}/{filename}`

#### 5c: Write — Sub-Agent Prompts

Ensure `~/.cursor/agents/` directory exists (create if needed).

Write to `~/.cursor/agents/{skill-id}.md`:

```markdown
---
name: {Skill ID}
description: {Description}
model: inherit
color: green
---

{page body content from Notion}
```

No sub-pages are fetched or written for sub-agent prompts.

### Step 6 — Verify

1. List all files created, split by type:

```
~/.cursor/skills/
└── pr-code-review/
    ├── SKILL.md
    └── agent-prompts.md

~/.cursor/agents/
├── bug-scanner-prompt.md
├── sql-standards-prompt.md
└── silent-failure-prompt.md
```

2. Confirm each entry is discoverable in its target folder.

3. Report the dependency graph:

```
pr-code-review
├── depends on: bug-scanner-prompt ✓
├── depends on: sql-standards-prompt ✓
└── depends on: silent-failure-prompt ✓
```

4. If any dependencies failed to install, warn clearly.

## Notion Content Handling

When converting Notion page content to local markdown:

- Notion tables (`<table>`) → markdown tables where possible
- Callout blocks (`<callout>`) → blockquotes or leave as-is
- Code blocks → as-is (standard markdown fencing)
- Toggle blocks → details/summary or headers with content
- Most Notion markdown is valid standard markdown and needs no conversion

## Error Handling

| Scenario | Action |
|----------|--------|
| Skill not found | Suggest checking spelling or listing all available skills |
| Sub-page fetch fails | Warn but continue (partial install > no install) |
| Dependency not found | Warn, offer to continue without it |
| File write fails (permissions) | Suggest alternative install location |
| Target already exists | Never overwrite without explicit user confirmation |
| Dependency already installed | Report "already present", skip unless user requests update |
