"""Verify that .cursor/rules/*.mdc matches what the generator would produce.

Used as a pre-commit hook: regenerates into a temp dir, diffs against the
committed tree, and exits non-zero if anything drifts.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

from scripts.generate_cursor_rules import generate_all


def check_fresh(skills_dir: Path, committed_rules_dir: Path) -> list[str]:
    """Return a list of drifted/extra/missing files; empty list means fresh."""
    with tempfile.TemporaryDirectory() as td:
        fresh_dir = Path(td) / "rules"
        generate_all(skills_dir, fresh_dir)

        fresh_files = {p.name for p in fresh_dir.glob("*.mdc")}
        committed_files = {p.name for p in committed_rules_dir.glob("*.mdc")}

        drift: list[str] = []

        for missing in sorted(fresh_files - committed_files):
            drift.append(f"MISSING: .cursor/rules/{missing} (generator would create it)")

        for extra in sorted(committed_files - fresh_files):
            drift.append(
                f"STALE:   .cursor/rules/{extra} (no matching SKILL.md — delete or add source)"
            )

        for name in sorted(fresh_files & committed_files):
            if not filecmp.cmp(fresh_dir / name, committed_rules_dir / name, shallow=False):
                drift.append(f"DIFFERS: .cursor/rules/{name} (content drift — regenerate)")

        return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"))
    parser.add_argument("--rules-dir", type=Path, default=Path(".cursor/rules"))
    args = parser.parse_args(argv)

    drift = check_fresh(args.skills_dir, args.rules_dir)
    if drift:
        print("Cursor rules are out of sync with skills/:", file=sys.stderr)
        for line in drift:
            print(f"  {line}", file=sys.stderr)
        print("\nRegenerate with: uv run python scripts/generate_cursor_rules.py skills/", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
