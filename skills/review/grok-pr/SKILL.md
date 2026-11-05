---
name: grok-pr
description: Builds an interactive HTML guide for understanding a pull request and acting on it. Distills intent from the linked issue, PR description and commits, judges whether the code achieves it, narrates the diff as ordered steps, diagrams structural changes, and lists findings with the expected shape of each fix. Findings are triaged in the page (accept, skip, edit), then posted to GitHub as a pending review, or handed back as a fix list. Three modes: review someone else's PR, self-review your own branch or PR against the repo's standards before shipping, or respond to review feedback received on your PR with assessments, fixes and proposed replies. Use when the user asks to grok, understand, walk through, visualize, review or self-review a PR, branch or commit range, or to go through, assess or answer review comments on their PR.
---

# Grok PR

Turn a PR into a guided review page that answers four questions in order: what is it trying to do, does it do it, how does the change reshape the code, and what is wrong with it.

The agent does the analysis and writes `guide.json`. `scripts/grok_pr.py` (in this skill's directory) validates it against the diff, renders one self-contained HTML file, and serves it so triage decisions can be posted or turned into fixes.

## Modes

Set `mode` in `guide.json`:

| Mode | When | Items are | Accept means |
| --- | --- | --- | --- |
| `review` | someone else's PR | findings | post as an inline comment in a pending review |
| `self` | your own branch or PR before review ("self-review", "review my branch") | findings, also against the repo's standards and PR rules | fix it in the working tree |
| `respond` | review comments on your own PR ("go through the feedback", "answer the review") | the reviewer's threads, each assessed | fix it, and post the reply in a pending review |

Pick the mode from the request. With no explicit request, use `self` when the PR author is the current user (`gh api user -q .login`) or there is no PR, else `review`. Use `respond` only when asked about feedback, or when it is your PR and it has unresolved threads; say which you picked.

## When To Use

- "Grok / walk me through / visualize / review PR 252", a GitHub PR URL, a Linear review URL, a branch, or a commit range.
- "Self-review my branch", "check my PR before I ship it": `self`.
- "Go through the feedback on my PR", "help me answer these review comments": `respond`.
- With no target, use the current branch's PR (`gh pr view`), else the current branch against the default branch.
- Not for writing your own PR description.

## Process

Keep every artifact in a work directory outside the reviewed repo: `WORK=~/Documents/pr-guides/<repo>-<pr-or-branch>`.

### 1. Gather context

- PR metadata: `gh pr view <n> --json number,title,body,author,baseRefName,headRefName,headRefOid,url,commits,files,closingIssuesReferences`
- Diff, GitHub: `gh pr diff <n> --color=never > "$WORK/pr.diff"`. Local: `git diff --find-renames --output="$WORK/pr.diff" <base>...<head>`. The script also reads the UTF-16 files Windows PowerShell 5 redirection produces.
- Linear review URL: resolve it with the Linear MCP `get_diff` tool to the repo and PR, then fetch as above.
- Issues: collect keys from the title, branch, body and commits (`ABC-123`, `#45`). Linear: `get_issue` plus `list_comments`. GitHub: `gh issue view <n> --comments`. Read acceptance criteria and the discussion, not just the title.
- Commits: `git log --reverse --format='%h %s%n%b' <base>..<head>`. Fixup and revert commits show where the author struggled.
- Code: read the head version of each non-trivial changed file (`git show <head>:<path>` when the branch is not checked out) and the callers of changed symbols (LSP references when available). The diff alone hides broken callers.
- Repo rules: AGENTS.md and the coding standards, testing and git workflow docs it points to. Findings cite them. In `self` mode, check them as findings in their own right (category `standards`): PR title and description, commit messages, branch name, story key, logging and test conventions.
- `respond` mode: `python scripts/grok_pr.py threads <pr-url> > "$WORK/threads.json"` lists unresolved review threads (thread id, path, current line, side, outdated flag, every comment) and review-level bodies. Add `--all` for resolved threads.
- Scrutiny: `python scripts/grok_pr.py config --repo <repo>` prints the effective preset (`light` by default; set `scrutiny` to `light`, `standard` or `strict` in `~/.config/grok-pr/config.json` or a repo's `.grok-pr.json`, and override `minSeverity` or `autoAccept` there if needed). Report only findings at or above `minSeverity`; `autoAccept` severities start accepted in the page.

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
| standards | violations of the repo's written conventions: AGENTS.md, coding standards, PR and commit rules (always cite the rule) |
| docs | comments or docs made stale by the change |

Every finding needs a severity, `path` and `line` on the side where the problem lives, a short `title` for the page, and a `detail` and `suggestion` written as the PR comment itself. Read [references/comment-style.md](references/comment-style.md) before writing any: the failure as a chain with real values, why it matters, the fix in one sentence, one to four sentences in total. Put how you know (test runs, commands, which callers you read) in `evidence`, which the page shows but never posts. Set `confidence: "inferred"` unless you confirmed it by reading the callers and tests or by running code. Skip style nits the repo standards do not require.

Add a `proposal` with the expected shape of the code to every blocker and major, and to any design, tests or scope finding whose fix is structural: a refactor, a moved responsibility, a new method boundary, a missing test. It is what the reviewer pastes into the PR comment, so write the shape, not a full patch: real names from the repo, signatures and the lines that decide the behavior, `// ...` for bodies that do not matter. When it rewrites existing code, set `replaces: [start, end]` (head line numbers) so the page shows current against expected. When it adds code elsewhere, such as a new test, set `path` to where it goes. Put setup caveats in `note` (for example, which existing helper a test must use to build its fixture). Check that every API the proposal calls exists; if you could not, say so in `note`. Skip proposals for nits and for fixes the `suggestion` already states in full.

For PRs over roughly 1,500 changed lines, give each chapter's findings pass to a subagent with the intent, the chapter's hunk IDs and the category table, then merge and dedupe.

### 6b. `respond` mode: assess each piece of feedback

Instead of hunting for findings, make one item per unresolved thread, and one per review-level body that asks for something. For each, read the commented code at head and the callers it affects, then fill:

- `thread`, `path`, `line`, `side`, `author`, `url` from `threads.json`, and `quote`: the reviewer's comment (with later replies summarized in `evidence` when the thread already has a back-and-forth). Review-level items have no `thread`, `path` or `line`.
- `assessment`: `agree`, `partly`, `disagree` or `question`. Disagreeing is fine when the code or tests show the reviewer is wrong; say why in `detail`.
- `severity`: the impact if it is not addressed, not how strongly it was worded.
- `detail`: impact and reasoning, for you only. `suggestion` and `proposal`: the fix and its shape, as in step 6.
- `reply`: the text posted on the thread, in the comment-style tone, written as if the fix is done: what changed and why, the test that proves it, or for `disagree` the evidence and an alternative. One to three sentences. No thanks or apologies.

`respond` still needs `title`, `tldr` (what the feedback amounts to) and `chapters` over the PR diff, so the page can show each thread in context.

### 7. Fill the canvas and the verdict

Read `assets/canvas.json` and give every item a status (pass, concern, fail, na, unchecked) with a one-line evidence note. Unverified is `unchecked`, never `pass`.

Write the verdict plainly. A PR that misses its issue, mixes concerns, or lacks a description or tests gets `prQuality: "poor"` and `request-changes` or `rethink`, with the reasons in `qualitySignals`.

When several findings share one root cause, write `reviewBody`: the post-level comment that proposes the single change removing all of them (see the style guide). Leave it out when findings are independent.

### 8. Render

Write `$WORK/guide.json` following [references/guide-schema.md](references/guide-schema.md), then run:

```bash
python scripts/grok_pr.py render "$WORK/guide.json" "$WORK/pr.diff" --repo <repo> --ref <headRefOid> --no-open
```

`--repo`/`--ref` let the page show source lines around findings on unchanged lines or in files the PR does not touch; if the head commit is missing locally, `git fetch origin pull/<n>/head` first. Omit both when no checkout exists; those findings then render without code. `--repo` also picks up the repo's `.grok-pr.json`. The script writes `index.html` next to `guide.json` (`--out` changes that). Pass `--no-open` and open the served page instead (step 9). Exit code 2 lists schema errors: fix `guide.json` and rerun. Treat `WARN` lines about unnarrated hunks as defects unless intended.

### 9. Triage, then post or fix

Start the server in the background; it runs until stopped:

```bash
python scripts/grok_pr.py serve "$WORK"
```

It opens the page on `http://127.0.0.1:<port>/` and saves every accept, skip and edit to `$WORK/decisions.json`. Tell the user the URL and wait while they triage.

- `review` and `respond`: the page's "Post review" / "Post replies" button creates one pending review on GitHub (inline comments, or replies on each thread; anything without a diff line or thread goes in the review body). The user submits it on GitHub. `python scripts/grok_pr.py post "$WORK" [--dry-run]` does the same from the shell. Posting refuses if the PR diff changed since the guide was built; re-run the review then.
- `self` and `respond`: when the user says to fix the accepted items, run `python scripts/grok_pr.py fixes "$WORK"` and apply each item in the working tree on the PR branch: minimal change, the repo's conventions, run the tests that cover it. Do not commit or push unless asked. Report each item as fixed (with the test) or declined (with the reason). In `respond`, fix before the replies are posted, and edit any reply the fix made inaccurate.

## The page

Tabs: Overview (TL;DR, intent and criteria, verdict, review summary comment, salient changes, risks, verification), Guide (one step at a time, narrative beside the diff, findings inline), Structure, Findings, or Feedback in `respond` (search with `/`; filter by status, severity and category; `j`/`k` move, `y` accept, `n` skip, `e` edit the text, `u` undo, Enter opens the item in Files; the "step N" chip opens the guide step), Canvas (readiness gauge, overridable statuses), Files (a "Findings outside the diff" section with source excerpts, then every diff). Findings with a `proposal` show an "Expected shape" block: current against expected when it replaces lines, else the code to add. `respond` items show the reviewer's comment, the assessment, the fix and the proposed reply. The copy button on each item copies exactly what would be posted (detail with `Nit:` for nits, suggestion, fenced code, note; the reply in `respond`), never the title or evidence. "Copy fix list" (`self`, `respond`) copies the accepted items as agent instructions. Keys: `1` to `6` switch tabs; in the Guide `j`/`k` move between steps and `r` marks a step reviewed. Split or unified diff toggle. Reviewed state and canvas overrides persist in the browser; triage decisions persist in `decisions.json` when served, else in the browser. Highlight.js and Mermaid load from jsDelivr; offline, code renders plain and diagrams show their source.

## Report

In chat: the mode, the served URL (or HTML path), the TL;DR, one verdict line, and blockers and majors as `path:line title`. After fixes: each item fixed or declined, with evidence.

## Stop Conditions

- The diff cannot be fetched (no access, unknown PR): stop and name the failing command.
- Never submit a review, approve, request changes, resolve threads or edit the PR. Posting creates a pending review only, and only from the user's click or an explicit request to post.
- `self` mode never posts.
- Do not switch branches in a working tree with uncommitted changes; read with `git show` or build in a temporary worktree.
