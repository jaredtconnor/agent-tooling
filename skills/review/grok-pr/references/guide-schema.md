# guide.json schema

Only `title`, `tldr` and `chapters` are required. Every other field renders when present. Text fields accept light Markdown: `code`, `**bold**`, `[text](https://…)`, and blank-line paragraphs. Fields marked *posted* become PR comment text; write them per [comment-style.md](comment-style.md).

```jsonc
{
  "id": "owner/repo#252",                 // localStorage key for reviewed state; defaults to url, then title
  "mode": "review",                       // review (default) | self | respond; see SKILL.md
  "title": "Share one retry policy across HTTP clients",
  "url": "https://github.com/owner/repo/pull/252",
  "author": "Jane Doe",
  "base": "release/v2026",                // target branch
  "head": "dev/jane/model-load",          // source branch
  "issues": [{ "key": "ABC-715", "title": "Model load is slow", "url": "https://…" }],

  "tldr": "One or two sentences: what changes and the effect, in plain words.",

  "intent": {
    "statement": "What the PR is trying to achieve, from the issue and description.",
    "source": "issue",                    // issue | pr-description | commits | inferred
    "criteria": [
      { "text": "Billing and search clients retry with the same backoff",
        "status": "met",                  // met | partial | missing | unclear
        "evidence": "Step 1; `RetryPolicyTests`" }
    ]
  },

  "verdict": {
    "intentMet": "partial",               // yes | partial | no | unclear
    "recommendation": "request-changes",  // approve | approve-with-nits | request-changes | rethink
    "prQuality": "ok",                    // good | ok | poor
    "rationale": "Two or three sentences a reviewer can act on.",
    "qualitySignals": ["Mixes a refactor with a behavior change", "No regression test for the bug"]
  },

  "reviewBody": "Suggestion that covers the three retry issues below: …",  // posted; post-level comment for a shared root cause

  "keyChanges": [{ "text": "Retry logic moves into one shared policy", "chapter": 0 }],
  "risks": ["Search requests now retry on 429; confirm the upstream rate limit tolerates it"],

  "chapters": [
    {
      "title": "Share one retry policy",  // names the idea, not the file
      "summary": "Why this step exists and what to look at.",
      "hunks": ["src/Retry.cs#0", "src/Retry.cs#2", "tests/RetryPolicyTests.cs"]  // hunk IDs or whole file paths
    }
  ],

  "structure": {
    "changes": [
      { "kind": "added",                  // added | removed | changed | moved | renamed
        "symbol": "RetryPolicy.Execute()",
        "path": "src/Retry.cs",
        "note": "Single policy used by both clients" }
    ],
    "diagrams": [
      { "title": "Request retries, after",
        "mermaid": "flowchart LR\n  A[BillingClient] --> R[RetryPolicy.Execute]\n  B[SearchClient] --> R\n  classDef changed stroke:#f2c94c,stroke-width:2px\n  class R changed",
        "caption": "Both clients now call one policy." }
    ]
  },

  "findings": [
    {
      "severity": "major",                // blocker | major | minor | nit
      "category": "correctness",          // correctness | syntax | performance | design | tests | security | scope | standards | docs
      "path": "src/Rules.cs",
      "line": 172,                        // line number on `side`
      "side": "new",                      // new (default) | old, for deleted lines
      "title": "Non-idempotent POST is retried",  // page only
      "detail": "`Execute` retries every verb, so a POST that times out after the server committed → duplicate charge.",  // posted
      "suggestion": "Suggest skipping the policy for non-idempotent requests.",  // posted
      "evidence": "Read all three call sites; BillingClient.Charge is a POST.",  // page only, never posted
      "confidence": "verified",           // verified | inferred
      "proposal": {                       // optional: expected shape of the fix
        "code": "if (!request.IsIdempotent)\n    return await send(request);\nreturn await _policy.Execute(() => send(request));",
        "replaces": [168, 174],           // optional: head lines it rewrites; the page shows current vs expected
        "path": "tests/RetryPolicyTests.cs", // optional: where new code goes when it is not the finding's file
        "note": "Setup caveats, or which APIs were not verified."  // optional
      }
    }
  ],

  "canvas": {
    "context.intent-achieved": { "status": "concern", "note": "Criterion 2 has no test." }
    // keys are item ids from assets/canvas.json; status: pass | concern | fail | na | unchecked
  },

  "verification": [
    { "command": "dotnet build -p:Platform=x64", "result": "pass", "note": "0 warnings in changed projects" }
    // result: pass | fail | not-run
  ]
}
```

## `respond` mode items

Each item in `findings` is one piece of feedback. On top of the fields above (`detail`, `suggestion` and `proposal` describe impact, reasoning and the fix; they are not posted):

```jsonc
{
  "thread": "PRRT_kwDO…",          // review thread node id from `grok_pr.py threads`; omit for review-level feedback
  "author": "reviewer-login",
  "url": "https://github.com/…#discussion_r123",
  "quote": "The reviewer's comment, verbatim.",
  "assessment": "agree",            // required: agree | partly | disagree | question
  "reply": "Kept the stored value when `os` is omitted on update; covered by `Put_OmittedOs_KeepsStoredValue`."  // required; posted
}
```

## Rules the renderer enforces

- Unknown hunk IDs or file paths in `chapters[].hunks`, unknown `severity`, `category` or `mode`, invalid canvas statuses, a `proposal` without `code` or with a malformed `replaces`, and in `respond` mode an item without `reply` or a valid `assessment` are errors (exit 2).
- `proposal.replaces` shows the current lines from `--repo`/`--ref`, else from the diff when the whole range is inside hunks; otherwise the page shows only the expected code, with a warning.
- Hunks no chapter references go into an auto "Other changes" chapter, with a warning.
- A finding appears inline in the diff only when its `line` falls inside a hunk on its `side`. Other findings, including those whose `path` is not in the diff, render in the Files tab under "Findings outside the diff", with source lines from `render --repo … --ref …` when given.
