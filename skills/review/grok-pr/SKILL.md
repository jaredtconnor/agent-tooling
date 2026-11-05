---
name: grok-pr
description: Reviews someone else's pull request through an interactive HTML guide. Distills intent from the linked issue, PR description and commits, judges whether the code achieves it, narrates the diff as ordered steps, diagrams structural changes, and writes findings as postable review comments with the expected shape of each fix. The reviewer triages findings in the page (accept, skip, edit) and posts the accepted ones as one pending GitHub review. Use when the user asks to grok, understand, walk through, visualize or review a PR, branch or commit range they did not write.
---

# Grok PR (review)

Turn someone else's PR into a guided review page that answers four questions in order: what is it trying to do, does it do it, how does the change reshape the code, and what is wrong with it. Then post what the reviewer accepts.

## When To Use

- "Grok / walk me through / visualize / review PR 252", a GitHub PR URL, a Linear review URL, a branch, or a commit range.
- The PR is the user's own (author is `gh api user -q .login`): use `grok-pr-self`. Comments already left on the user's PR: use `grok-pr-feedback`. Say so and switch.
- Not for writing a PR description.

## Process

Read `../grok-pr-core/references/process.md` (`CORE` is `../grok-pr-core` from this skill's directory) and run steps 0 to 9 with `mode: "review"`. Nothing to add or replace before step 9.

After step 9, the user triages and clicks "Post review" in the served page. That creates one pending review: inline comments for accepted findings on diff lines, everything else (the review summary, findings outside the diff) in the review body. The user submits it on GitHub. If the user asks you to post instead, run `python $CORE/scripts/grok_pr.py post "$WORK"`; run it with `--dry-run` first when unsure what will go out. Posting refuses if the PR diff changed since the guide was built; re-run the review then.

## Report

In chat: the served URL, the TL;DR, one verdict line, and blockers and majors as `path:line title`. After posting: the count of comments and the PR link.

## Stop Conditions

The shared stop conditions in `process.md`.
