# Input Sources

The orchestration setup skill accepts work from four input types. It parses the input during Phase 1 (Intake) and normalizes it into a mandate regardless of source.

## Linear Ticket Parsing

When given a ticket identifier (e.g., `CAL-123`, `ENG-456`):

**Preferred: `linctl` CLI** (significantly faster than MCP):
1. Check availability: `linctl --version`
2. Fetch the issue: `linctl issue get CAL-123 --json`
3. Extract: **title** → objective, **description** → scope + context + acceptance criteria, **labels** → constraints/categorization
4. If the ticket has sub-issues, list them: `linctl issue list --json` and filter by parent
5. Store the ticket ID for: branch naming, YAML `source.ref`, and Linear config in YAML

**Fallback: Linear MCP** (if `linctl` is not installed):
1. Fetch the issue using `get_issue` from the Linear MCP tools
2. If the ticket has sub-issues, use `list_issues` with `parentId` to fetch them

**What to extract for the YAML:**
- `source.type`: `"linear"`
- `source.ref`: the ticket ID (e.g., `"CAL-123"`)
- `source.raw_title`: the ticket title as-is
- `mandate.objective`: derived from title + description
- `mandate.constraints`: from labels, priority, linked issues
- `mandate.acceptance_criteria`: from description (look for "AC", "Acceptance Criteria", checkbox lists)
- `platform.linear.team`: from the ticket's team
- `platform.linear.project`: from the ticket's project (if any)
- `platform.linear.parent_issue`: the ticket ID itself (slices create child issues)

## Notion Page Parsing

When given a Notion URL (contains `notion.so` or `notion.site`) or a Notion page ID (UUID format):

1. Fetch the page using `notion-fetch` with the URL or ID
2. Extract: **page title** → objective, **page content** → scope, context, acceptance criteria
3. Parse the page's markdown content looking for structured sections: headings like "Goal", "Scope", "Requirements", "Constraints", "Acceptance Criteria"
4. If the page is in a database, extract relevant properties (status, priority, assignee, tags) as additional mandate context
5. If the page contains child pages or linked databases, note them as potential sub-task references

**What to extract for the YAML:**
- `source.type`: `"notion"`
- `source.ref`: the Notion URL
- `source.raw_title`: the page title
- `mandate.*`: from parsed page content
- `platform.linear`: set to null unless user specifies Linear integration separately

## Markdown Plan File

When given a file path, read it and extract structure. The file can be either:

**Structured YAML frontmatter:**
```yaml
---
objective: "Clear goal statement"
scope:
  - "Deliverable 1"
  - "Deliverable 2"
constraints:
  - "Must maintain backward compatibility"
acceptance_criteria:
  - "All tests pass"
  - "PR approved"
context:
  - "Relevant codebase info"
---
Additional details in markdown body...
```

**Free-form markdown** — extract structure from headings, lists, and content. Look for headings like "Goal", "Scope", "Requirements", "Constraints", "Acceptance Criteria".

**What to extract for the YAML:**
- `source.type`: `"file"`
- `source.ref`: the file path
- `source.raw_title`: from frontmatter `objective` or first heading
- `mandate.*`: from frontmatter fields or parsed markdown sections

## Inline Description

When the input doesn't match any of the above patterns, treat it as an inline description.

1. Parse the quoted string as the mandate objective
2. Infer scope and constraints from the description where possible
3. If ambiguous, ask the user for clarification BEFORE generating the YAML

**What to extract for the YAML:**
- `source.type`: `"inline"`
- `source.ref`: the description string
- `source.raw_title`: the description string
- `mandate.objective`: the description
- `mandate.constraints`: inferred or asked
- `mandate.acceptance_criteria`: inferred or asked

## Source Detection Logic

```
input matches /^[A-Z]+-\d+$/     → Linear ticket
input contains "notion.so"        → Notion page
input contains "notion.site"      → Notion page
input matches UUID format          → Notion page ID
input contains "/" or "\" AND ends in ".md" → Markdown file
input starts with "./"             → Markdown file
otherwise                          → Inline description
```
