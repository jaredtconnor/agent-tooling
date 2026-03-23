#!/usr/bin/env python3
"""
Clean AI co-author trailers and fix non-matching authors in git history.

Uses git-filter-repo to rewrite commits across all branches.

Usage:
    python3 clean_history.py --dry-run     # Preview changes
    python3 clean_history.py               # Rewrite history
    python3 clean_history.py --ai-only     # Only fix AI-looking authors
"""

import argparse
import re
import subprocess
import sys
import textwrap

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Trailer patterns to remove from commit messages (matched against each line)
AI_TRAILER_PATTERNS = [
    # Claude (any model/version) or Anthropic emails
    r"Co-Authored-By:.*(?:Claude|noreply@anthropic\.com|anthropic)",
    # GitHub Copilot
    r"Co-Authored-By:.*(?:Copilot|copilot|GitHub Copilot)",
    # Cursor
    r"Co-Authored-By:.*(?:Cursor|cursor\.com)",
    # Codeium / Windsurf
    r"Co-Authored-By:.*(?:Codeium|Windsurf|codeium)",
    # Amazon Q / CodeWhisperer
    r"Co-Authored-By:.*(?:Amazon Q|CodeWhisperer|amazon)",
    # Generic bot/noreply emails in co-author lines
    r"Co-Authored-By:.*(?:noreply@|bot@|\[bot\])",
    # Made-with trailers (any value)
    r"Made-with:.*",
    # Generated-by trailers mentioning AI tools
    r"Generated-by:.*(?:Claude|Copilot|Cursor|AI|Codeium|Windsurf)",
]

# Author name/email patterns that look like AI tools
AI_AUTHOR_PATTERNS = [
    r"claude",
    r"copilot",
    r"cursor",
    r"anthropic",
    r"codeium",
    r"windsurf",
    r"amazon.q",
    r"codewhisperer",
    r"noreply@",
    r"bot@",
    r"\[bot\]",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def git_config(key):
    """Read a git config value, or None if not set."""
    try:
        return (
            subprocess.check_output(
                ["git", "config", key], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


def is_ai_author(name, email):
    """Return True if name/email looks like an AI tool."""
    combined = f"{name} {email}".lower()
    return any(re.search(p, combined) for p in AI_AUTHOR_PATTERNS)


def line_is_ai_trailer(line):
    """Return True if a commit message line matches an AI trailer pattern."""
    stripped = line.strip()
    return any(re.match(p, stripped, re.IGNORECASE) for p in AI_TRAILER_PATTERNS)


def get_remote_url():
    """Get the origin remote URL, or None."""
    try:
        return (
            subprocess.check_output(
                ["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------------------------
# Scan (dry-run)
# ---------------------------------------------------------------------------


def scan(user_name, user_email, ai_only):
    """Scan git history and report what would be changed."""
    result = subprocess.run(
        [
            "git",
            "log",
            "--all",
            "--format=%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x00%x01",
        ],
        capture_output=True,
        text=True,
    )

    commits = result.stdout.split("\x01")

    trailer_hits = []  # (sha_short, subject, trailer_line)
    author_hits = []  # (sha_short, subject, current_author)
    seen_shas = set()

    for entry in commits:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x00", 5)
        if len(parts) < 6:
            continue

        sha, a_name, a_email, c_name, c_email, message = parts
        sha_short = sha[:10]
        subject = message.split("\n")[0][:72]

        # Check for AI trailers
        for line in message.split("\n"):
            if line_is_ai_trailer(line):
                trailer_hits.append((sha_short, subject, line.strip()))
                seen_shas.add(sha_short)

        # Check author
        if ai_only:
            author_mismatch = is_ai_author(a_name, a_email)
        else:
            author_mismatch = a_name != user_name or a_email != user_email

        if author_mismatch:
            author_hits.append((sha_short, subject, f"{a_name} <{a_email}>"))
            seen_shas.add(sha_short)

    # Report
    print(f"\n{'=' * 64}")
    print("  Git History Scan")
    print(f"{'=' * 64}")
    print(f"\n  Target identity : {user_name} <{user_email}>")
    print(f"  Author fix mode : {'AI-only' if ai_only else 'all non-matching'}")

    print(f"\n  AI Trailers Found: {len(trailer_hits)}")
    print(f"  {'-' * 60}")
    for sha, subj, trailer in trailer_hits:
        print(f"  {sha}  {subj}")
        print(f"             -> {trailer}")

    print(f"\n  Author Mismatches: {len(author_hits)}")
    print(f"  {'-' * 60}")
    for sha, subj, author in author_hits:
        print(f"  {sha}  {subj}")
        print(f"             -> {author}")

    total = len(seen_shas)
    print(f"\n  Total commits to rewrite: {total}")
    print(f"{'=' * 64}\n")

    return total


# ---------------------------------------------------------------------------
# Clean (rewrite)
# ---------------------------------------------------------------------------


def clean(user_name, user_email, ai_only, restore_remote):
    """Run git filter-repo to rewrite history."""
    remote_url = get_remote_url() if restore_remote else None

    # Build the commit callback as a string for --commit-callback.
    # This code runs inside git-filter-repo's Python environment with
    # 'commit' as the callback parameter and 're' available.
    callback = textwrap.dedent(f"""\
        import re

        AI_TRAILER_PATTERNS = {AI_TRAILER_PATTERNS!r}
        AI_AUTHOR_PATTERNS = {AI_AUTHOR_PATTERNS!r}
        TARGET_NAME = {user_name!r}.encode("utf-8")
        TARGET_EMAIL = {user_email!r}.encode("utf-8")
        AI_ONLY = {ai_only!r}

        def _is_ai(name, email):
            combined = (name + " " + email).lower()
            return any(re.search(p, combined) for p in AI_AUTHOR_PATTERNS)

        def _line_match(line):
            s = line.strip()
            return any(re.match(p, s, re.IGNORECASE) for p in AI_TRAILER_PATTERNS)

        # --- clean message ---
        msg = commit.message.decode("utf-8", errors="replace")
        lines = msg.split("\\n")
        cleaned = [l for l in lines if not _line_match(l)]
        result = "\\n".join(cleaned)
        result = re.sub(r"\\n{{3,}}", "\\n\\n", result)
        result = result.rstrip() + "\\n"
        commit.message = result.encode("utf-8")

        # --- fix author ---
        a_name = commit.author_name.decode("utf-8", errors="replace")
        a_email = commit.author_email.decode("utf-8", errors="replace")
        if AI_ONLY:
            if _is_ai(a_name, a_email):
                commit.author_name = TARGET_NAME
                commit.author_email = TARGET_EMAIL
        else:
            if a_name != {user_name!r} or a_email != {user_email!r}:
                commit.author_name = TARGET_NAME
                commit.author_email = TARGET_EMAIL

        # --- fix committer ---
        c_name = commit.committer_name.decode("utf-8", errors="replace")
        c_email = commit.committer_email.decode("utf-8", errors="replace")
        if AI_ONLY:
            if _is_ai(c_name, c_email):
                commit.committer_name = TARGET_NAME
                commit.committer_email = TARGET_EMAIL
        else:
            if c_name != {user_name!r} or c_email != {user_email!r}:
                commit.committer_name = TARGET_NAME
                commit.committer_email = TARGET_EMAIL
    """)

    print("Running git filter-repo across all branches...")
    result = subprocess.run(
        ["git", "filter-repo", "--force", "--commit-callback", callback],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR: git filter-repo failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print("History rewritten successfully.")

    # Restore remote
    if remote_url:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            capture_output=True,
        )
        print(f"Remote 'origin' restored: {remote_url}")

    print("\nNext step: review the result, then 'git push --force-with-lease --all'")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Clean AI co-author trailers and fix authors in git history."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report only; do not rewrite history.",
    )
    parser.add_argument(
        "--ai-only",
        action="store_true",
        help="Only fix authors that look like AI tools (not all non-matching).",
    )
    parser.add_argument(
        "--no-restore-remote",
        action="store_true",
        help="Don't re-add origin remote after filter-repo.",
    )
    args = parser.parse_args()

    user_name = git_config("user.name")
    user_email = git_config("user.email")

    if not user_name or not user_email:
        print(
            "ERROR: git user.name and user.email must be configured.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.dry_run:
        total = scan(user_name, user_email, args.ai_only)
        sys.exit(0 if total == 0 else 2)
    else:
        # Run scan first to show what will change
        total = scan(user_name, user_email, args.ai_only)
        if total == 0:
            print("Nothing to clean. History is already tidy.")
            sys.exit(0)
        clean(user_name, user_email, args.ai_only, not args.no_restore_remote)


if __name__ == "__main__":
    main()
