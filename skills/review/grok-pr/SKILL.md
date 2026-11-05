---
name: grok-pr
description: Builds an interactive HTML guide for understanding and reviewing a pull request. Distills intent from the linked issue, PR description and commits, judges whether the code achieves it, narrates the diff as ordered steps, diagrams structural changes, and lists findings (correctness, syntax, performance, design, tests, security) plus a review-canvas checklist. Use when the user asks to grok, understand, walk through, visualize or deeply review a PR, branch or commit range.
---

# Grok PR

Turn a PR into a guided review page that answers four questions in order: what is it trying to do, does it do it, how does the change reshape the code, and what is wrong with it.

The agent does the analysis and writes `guide.json`. `scripts/grok_pr.py` (in this skill's directory) validates it against the diff, renders one self-contained HTML file and opens it in the browser.

## When To Use

- "Grok / walk me through / visualize / review PR 252", a GitHub PR URL, a Linear review URL, a branch, or a commit range.
- With no target, use the current branch's PR (`gh pr view`), else the current branch against the default branch.
- Not for writing your own PR description or replying to review comments.

## Process

Keep every artifact in a work directory outside the reviewed repo: `WORK=~/Documents/pr-guides/<repo>-<pr-or-branch>`.

### 1. Gather context

- PR metadata: `gh pr view <n> --json number,title,body,author,baseRefName,headRefName,url,commits,files,closingIssuesReferences`
- Diff, GitHub: `gh pr diff <n> --color=never > "$WORK/pr.diff"`. Local: `git diff --find-renames --output="$WORK/pr.diff" <base>...<head>`. The script also reads the UTF-16 files Windows PowerShell 5 redirection produces.
- Linear review URL: resolve it with the Linear MCP `get_diff` tool to the repo and PR, then fetch as above.
- Issues: collect keys from the title, branch, body and commits (`ABC-123`, `#45`). Linear: `get_issue` plus `list_comments`. GitHub: `gh issue view <n> --comments`. Read acceptance criteria and the discussion, not just the title.
- Commits: `git log --reverse --format='%h %s%n%b' <base>..<head>`. Fixup and revert commits show where the author struggled.
- Code: read the head version of each non-trivial changed file (`git show <head>:<path>` when the branch is not checked out) and the callers of changed symbols (LSP references when available). The diff alone hides broken callers.
- Repo rules: AGENTS.md and the coding standards it points to. Findings cite them.

### 2. Distill intent before judging code

Write `intent.statement` (one or two sentences) using the issue first, then the PR body, then commits. Extract testable `intent.criteria`. With no issue and no description, set `source: "inferred"`, add a quality signal, and do not invent requirements.

### 3. Map the diff into steps

Run `python scripts/grok_pr.py hunks "$WORK/pr.diff"` to list hunk IDs (`path#N`). Use `python3` where `python` is not on PATH.

Order chapters as a story, not by file:

1. the core behavior change
2. callers and wiring that adopt it
3. tests that prove it
4. mechanical changes last, in one chapter: renames, formatting, generated files, lockfiles

Title each chapter after the idea ("Share one retry policy across HTTP clients"). The summary says why the step exists and what to check, in one to three sentences. Each hunk belongs to one chapter; aim for 3 to 8 chapters. Reference a whole file by path when all its hunks belong together.

### 4. Check the code against the intent

Give each criterion a status (met, partial, missing, unclear) and evidence: a chapter, a test name or `path:line`. Changes no criterion explains become `scope` findings.

### 5. Describe the structure

List structural changes: added or removed types and public members, signature changes, new dependencies between modules, data-flow, schema and contract changes. Add a Mermaid diagram only when the shape changed (new component, new call path, changed data flow). Prefer the new path as a flowchart with changed nodes marked by `classDef`, or a before/after pair. Keep each diagram under about 15 nodes and quote labels containing punctuation.

### 6. Find problems, one category per pass

| Category | Look for |
| --- | --- |
| correctness | logic errors; null, empty and boundary cases; concurrency; broken callers; behavior changes outside the intent |
| syntax | build, typecheck and lint results. Run the repo's checks on the head when it is checked out (or in a temporary `git worktree`) and fast enough; record each run in `verification`. Otherwise leave `quality.compiles` as `unchecked`. |
| performance | allocations, queries or IO inside loops; complexity changes; N+1 access; unbounded caches or collections |
| design | wrong layer, a second convention for an existing pattern, leaky abstractions, needless indirection, contract changes |
| tests | changed behavior without tests, bug fixes without a regression test, tests that assert implementation details |
| security | injection, unvalidated input, secrets or PII in code or logs, missing authorization |
| scope | unrelated edits, refactor mixed with behavior change |
| docs | comments or docs made stale by the change |

Every finding needs a severity, `path` and `line` on the side where the problem lives, evidence in `detail`, and a concrete `suggestion`. Set `confidence: "inferred"` unless you confirmed it by reading the callers and tests or by running code. Skip style nits the repo standards do not require.

For PRs over roughly 1,500 changed lines, give each chapter's findings pass to a subagent with the intent, the chapter's hunk IDs and the category table, then merge and dedupe.

### 7. Fill the canvas and the verdict

Read `assets/canvas.json` and give every item a status (pass, concern, fail, na, unchecked) with a one-line evidence note. Unverified is `unchecked`, never `pass`.

Write the verdict plainly. A PR that misses its issue, mixes concerns, or lacks a description or tests gets `prQuality: "poor"` and `request-changes` or `rethink`, with the reasons in `qualitySignals`.

### 8. Render

Write `$WORK/guide.json` following [references/guide-schema.md](references/guide-schema.md), then run:

```bash
python scripts/grok_pr.py render "$WORK/guide.json" "$WORK/pr.diff"
```

It writes `index.html` next to `guide.json` and opens it (`--out` and `--no-open` change that). Exit code 2 lists schema errors: fix `guide.json` and rerun. Treat `WARN` lines about unnarrated hunks or off-diff findings as defects unless intended.

## The page

Tabs: Overview (TL;DR, intent and criteria, verdict, salient changes, risks, verification), Guide (one step at a time, narrative beside the diff, findings inline), Structure, Findings (filter by severity and category, click to jump), Canvas (readiness gauge, overridable statuses), Files (every diff). Keys: `1` to `6` switch tabs, `j`/`k` next and previous step, `r` marks a step reviewed. Split or unified diff toggle. Reviewed state and canvas overrides persist in the browser. "Copy review notes" copies the verdict, findings and canvas concerns as Markdown. Highlight.js and Mermaid load from jsDelivr; offline, code renders plain and diagrams show their source.

## Report

In chat: the HTML path, the TL;DR, one verdict line, and blockers and majors as `path:line title`.

## Stop Conditions

- The diff cannot be fetched (no access, unknown PR): stop and name the failing command.
- Do not post comments, approve, or edit the PR unless asked.
- Do not switch branches in a working tree with uncommitted changes; read with `git show` or build in a temporary worktree.
