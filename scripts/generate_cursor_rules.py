"""Generate Cursor .mdc rules from canonical SKILL.md files.

Single source of truth: skills/<name>/SKILL.md
Output: .cursor/rules/<name>.mdc (auto-attached by description match).

See docs/ai-dlc/architecture.md for the full design rationale.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def parse_skill(content: str) -> tuple[dict, str]:
    """Split a SKILL.md into (frontmatter_dict, body)."""
    if not content.startswith("---"):
        raise ValueError("SKILL.md must start with a YAML frontmatter block (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter is not properly closed with a second ---")

    frontmatter = yaml.safe_load(parts[1]) or {}
    if not isinstance(frontmatter, dict):
        raise ValueError("SKILL.md frontmatter must parse to a YAML mapping")

    body = parts[2].lstrip("\n")
    return frontmatter, body


def emit_mdc(frontmatter: dict, body: str) -> str:
    """Render Cursor-compatible .mdc content from parsed source.

    Cursor frontmatter convention:
      description: <text>    # used for auto-attach matching
      globs:                 # optional file-glob triggers
      alwaysApply: false     # auto-attach by description, never always-on
    """
    description = frontmatter.get("description", "").strip()

    out_fm = {
        "description": description,
        "globs": "",
        "alwaysApply": False,
    }

    fm_yaml = yaml.safe_dump(
        out_fm,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    return f"---\n{fm_yaml}---\n\n{body.rstrip()}\n"


def generate(source: Path, output: Path) -> None:
    """Read a SKILL.md, write the corresponding .mdc."""
    content = source.read_text(encoding="utf-8")
    frontmatter, body = parse_skill(content)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_mdc(frontmatter, body), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Cursor .mdc rules from canonical SKILL.md files."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to a SKILL.md file or a skills/ directory (future: walk all skills)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".cursor/rules"),
        help="Output directory for .mdc files (default: .cursor/rules)",
    )
    args = parser.parse_args(argv)

    src: Path = args.source
    if src.is_dir():
        # Phase 2 work — for now the happy path is single-file.
        print(f"error: directory input not supported yet (Phase 2 scope): {src}", file=sys.stderr)
        return 2

    if not src.exists():
        print(f"error: source not found: {src}", file=sys.stderr)
        return 2

    # Derive skill name from parent directory (skills/<name>/SKILL.md)
    skill_name = src.parent.name
    output = args.output_dir / f"{skill_name}.mdc"

    try:
        generate(src, output)
    except ValueError as e:
        print(f"error: {src}: {e}", file=sys.stderr)
        return 1

    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
