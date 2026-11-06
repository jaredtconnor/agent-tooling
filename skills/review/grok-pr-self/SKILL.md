---
name: grok-pr-self
description: Self-reviews your own branch or pull request before you ship it, against the repo's coding standards, testing rules and PR and commit conventions, through the same interactive HTML guide as grok-pr. Findings are triaged in the page (accept, skip, edit) and the accepted ones are fixed in the working tree; nothing is posted to GitHub. Use when the user asks to self-review, check, tighten or grok their own branch, PR or changes before review or merge.
---

# Grok PR (self-review)

Review your own change the way a strict reviewer would, then fix what you accept, so the PR that goes out is already clean.

## When To Use

- "Self-review my branch", "check my PR before I ship it", "what would a reviewer flag here", or `grok-pr` on a PR the user wrote.
- With no target: the current branch's PR (`gh pr view`), else the current branch against its base.
- Reviewer comments already on the PR: use `grok-pr-feedback`.

## Process

Read `../grok-pr-core/references/process.md` (`CORE` is `../grok-pr-core` from this skill's directory) and run steps 0 to 9 with `mode: "self"`, with these changes:

- **Step 1:** the branch is usually checked out, so read the working tree, and include uncommitted changes when the user wants them reviewed (`git diff <base>` instead of `<base>...<head>`). Untracked new files are not in that diff: append `git diff --no-index -- /dev/null <file>` for each one in scope. When the tree also holds unrelated edits, pass the reviewed paths after `--` and say which files you left out. Read the repo's PR and commit rules as well as the coding standards: AGENTS.md and every contributing or workflow doc it links.
- **Step 6:** run the `standards` pass in full: the PR title and description, commit messages, branch name and story key against the git workflow rules; logging, data access, naming and test conventions against the coding standards. Cite the rule in each finding. Run the repo's build and the tests covering the change (`syntax`, `tests`); do not leave `quality.compiles` unchecked when the build can run here.
- **Step 7:** the verdict answers "is this ready to request review?". `reviewBody` describes the root-cause change you would make, not a comment to post.

After step 9, the user triages. When they say to fix the accepted items (or paste the "Copy fix list" output), follow "Applying accepted items as fixes" in step 9. Fix `standards` findings about the PR title or description by proposing the new text in chat; change the PR only if asked.

## Keeping the page current

Once a guide exists, any change to the reviewed code in this session (applied fixes, edits the user asks for, formatter rewrites) updates the page before you report, without being asked:

1. Regenerate `$WORK/pr.diff` exactly as in step 1, with the same paths and untracked files plus any new files the change added.
2. Re-run `hunks`. Hunk IDs shift, so rebuild `chapters` from the new list instead of patching the old IDs.
3. Re-run step 6 on the changed hunks, and re-run the build and the tests that cover them. Remove findings the change resolved, add any it introduced, and record each resolved one as a `keyChanges` entry (`Round N major fixed: ...`), because the schema has no resolved state.
4. Bring `tldr`, `intent.criteria`, `verdict`, `structure`, `canvas` and `verification` in line with the new diff and the commands you just ran. Drop `reviewBody` when its root cause is gone.
5. If findings were added or removed, move `decisions.json` to `decisions.round<N>.json` before rendering. Decision keys are positional (`f0`, `f1`, ...), so stale decisions would attach to the wrong finding.
6. Re-render with the step 8 command. The running server re-reads `index.html` and `decisions.json` on every request, so do not restart it. Tell the user to refresh, because an open tab writes its old decisions back on its next click.

Report the round in chat: what was resolved, any new findings, and the new verdict.

## Report

In chat: the served URL, the TL;DR, the verdict, and blockers and majors as `path:line title`. After fixes: each item fixed (with the test or command) or declined (with the reason), and what still blocks shipping.

## Stop Conditions

- The shared stop conditions in `process.md`.
- Never post to GitHub in this mode; the server refuses anyway.
- Never commit, push or amend unless asked.
