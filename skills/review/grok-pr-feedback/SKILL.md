---
name: grok-pr-feedback
description: Works through review feedback received on your own pull request. Turns each unresolved review thread and review summary into an item with the reviewer's comment, an assessment (agree, partly, disagree, question), the impact and reasoning, the shape of the fix, and a proposed reply, in the same interactive HTML guide as grok-pr. Accepted items are fixed in the working tree and their replies posted on each thread as one pending GitHub review. Use when the user asks to go through, assess, address, fix or answer review comments or feedback on their PR.
---

# Grok PR (feedback)

Decide what to do with each review comment on your PR, fix what you accept, and answer every thread in the reviewer's own register.

## When To Use

- "Go through the feedback on my PR", "help me answer these review comments", "address the review on PR 80".
- No reviewer comments yet: use `grok-pr-self`. Someone else's PR: use `grok-pr`.

## Process

Read `../grok-pr-core/references/process.md` (`CORE` is `../grok-pr-core` from this skill's directory) and run steps 0 to 9 with `mode: "respond"`, with these changes:

- **Step 1:** also run `python $CORE/scripts/grok_pr.py threads <pr-url> > "$WORK/threads.json"`. It lists unresolved review threads (thread id, path, current line, side, outdated flag, every comment) and review-level bodies; add `--all` for resolved ones.
- **Steps 3 to 5:** still required, so the page can show each thread in its place in the diff. Keep them brief.
- **Step 6 is replaced:** make one item per unresolved thread, and one per review-level body that asks for something. For each, read the commented code at head and the callers it affects, then fill:
  - `thread`, `path`, `line`, `side`, `author`, `url` from `threads.json`, and `quote`: the reviewer's comment, verbatim. Summarize any later back-and-forth in `evidence`. Review-level items have no `thread`, `path` or `line`. For outdated threads, find where the code moved and use that line, or omit `line` if it is gone.
  - `assessment`: `agree`, `partly`, `disagree` or `question`. Disagreeing is fine when the code or tests show the reviewer is wrong; say why in `detail`.
  - `severity`: the impact if it is not addressed, not how strongly it was worded.
  - `detail`: impact and reasoning, for you only. `suggestion` and `proposal`: the fix and its shape, as in step 6 of `process.md`.
  - `reply`: what gets posted on the thread, per `comment-style.md`, written as if the fix is done: what changed and why, and the test that proves it; for `disagree`, the evidence and an alternative; for `question`, the answer. One to three sentences, no thanks or apologies. Match the precedent in the repo's history when replying to a "done" request: "Done. `X` now … Covered by `Test_Name`."
  - `tldr`: what the feedback amounts to overall.
- **Step 7:** the canvas is optional. The verdict says how much of the feedback is accepted and what is left open.

After step 9, the user triages. Then, in this order:

1. When they say to fix, follow "Applying accepted items as fixes" in step 9. Edit any `reply` the actual fix made inaccurate (test names, what changed), and re-render.
2. When the fixes are pushed, the user clicks "Post replies" (or asks you to run `python $CORE/scripts/grok_pr.py post "$WORK"`). That creates one pending review holding a reply on each accepted thread, with replies to review-level feedback in the review body under a quote of what they answer. The user submits it on GitHub.

## Report

In chat: the served URL, each item as `assessment · path:line · title`, and what you recommend skipping and why. After fixes: fixed (with test) or declined (with reason). After posting: the count of replies and the PR link.

## Stop Conditions

- The shared stop conditions in `process.md`.
- Never resolve threads, and never post replies before the user has seen them in the page.
- Never commit, push or amend unless asked.
