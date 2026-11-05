# Review comment style

`detail`, `suggestion`, `proposal.note` and `reviewBody` are posted to the PR as written. Write them the way a senior reviewer who read the whole change would: short, concrete, about the code's behavior.

## Shape of one comment

1. **The failure, as a chain.** Trigger, then mechanism, then consequence, with real values. Use `→` for the chain when it has three or more steps.
2. **Why it matters here.** One clause on the blast radius: rollout, running instances, data written, callers outside the diff.
3. **The fix, in one sentence.** Start with "Suggest", "Consider" or "Either … or …". Add a code block (`proposal`) only when it is shorter or clearer than the sentence.

One to four sentences in total. A long comment means two findings, or a summary-level point.

## Rules

- Lead with the behavior, never with "I think", "It seems" or the finding's title. The page shows the title; the comment does not repeat it.
- Name the exact input that breaks it: `PUT {tag: '5.2.0-linux'}` with no `os`, an empty list, a second concurrent call.
- Compare with the codebase's own precedent when one exists: "Unlike `RetryMode`, which is returned raw, this one is resolved before it is returned, so it doesn't round-trip."
- State uncertain claims with the evidence that makes them likely: "Looks unused: the call site passes a string, and the mapper handles string-to-enum natively."
- Point at related comments instead of repeating them: "Goes away if the column is NOT NULL (see review summary)."
- Prefix nits with `Nit:` (the page adds it for `severity: "nit"` when missing). Keep nits to one or two sentences.
- No praise, greetings, apologies, severity labels, "the agent", "verified", or narration of how you found it. That goes in `evidence`, which the page shows but never posts.
- Backtick identifiers, values and paths. Plain words for everything else.

## The review summary (`reviewBody`)

Post-level comment. Use it when several findings share one root cause, and propose the single change that removes all of them:

> Suggestion that covers the three `os` issues below (tag guard, config default, promote round-trip): make `Versions.Os` NOT NULL.
>
> - Migration: backfill NULLs to `'Windows'`, then `ALTER COLUMN … NOT NULL` with a `DEFAULT 'Windows'` constraint, so old code that inserts without the column keeps working during rollout
> - Make `Version.Os` non-nullable; drop `Defaults:Os` and `ResolveOs`
> - PUT: an omitted `os` keeps the stored value on update and defaults to Windows on insert

Leave it empty when findings are independent. Never summarize the PR back to its author.

## Examples

Correctness, with a chain and the blast radius:

> A PUT that omits `os` but sends a new tag passes this guard (the tag differs), so an explicitly Linux version is saved as NULL and resolves to Windows. E.g. a script PUTs `{tag: '5.2.0-linux'}` → Windows container groups with a Linux image → every create fails.
>
> Suggest: an omitted `os` on an existing row keeps the stored value instead of falling back to the default.

Design, operational consequence:

> Changing this setting changes the OS of every inheriting (NULL) version without a tag change, which is exactly what the PUT guard rejects. Running workers are never retired because their tag still matches, and every new create gets the wrong OS. Suggest removing the global default and storing the OS per row (see review summary).

Dead code, hedged with evidence and two options:

> Looks unused: the upsert passes `os?.ToString()` as a string, and the mapper converts string columns to enums without a type handler. Either drop it and its registrations, or pass the enum directly so it is actually used.

Performance nit:

> Nit: this database read runs before the cheap count checks, and the aggregate check calls `GetAllAsync` again afterwards. Consider moving it after the pure validations.

Duplication nit, with the replacement inline:

> Nit: nearly duplicates `TryParseRetryMode`. `!int.TryParse(s, out _) && Enum.TryParse<Os>(s.Trim(), true, out var v) && Enum.IsDefined(v)` does the same.

## Too much (rewrite these)

> The agent found that `CreateReader` returns a reader whose command is already disposed. Verified with a throwaway test: passes on base, fails on head with "Invalid attempt to call FieldCount when reader is closed". The agent's report also lists similar patterns in four other classes…

Becomes `detail`:

> `using var cmd` disposes the command when `CreateReader` returns, and the new provider closes the open reader with it (the old one left it open) → every `CreateReader*` caller gets a closed reader. Same pattern at lines 194, 303 and 314.

and `evidence`: "Throwaway test passes on base, fails on head: 'Invalid attempt to call FieldCount when reader is closed'."
