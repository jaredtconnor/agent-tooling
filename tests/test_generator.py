"""Unit tests for scripts/generate_cursor_rules.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_cursor_rules import emit_mdc, generate, parse_skill


SAMPLE_SKILL = """---
name: refine
description: Refine rough issue descriptions into fully-formed specifications.
when_to_use: when partner provides issue ID that needs requirements refinement
---

# Refining Issues

## Overview

Transform rough issue descriptions into fully-formed specifications.
"""


def test_parse_frontmatter_extracts_name_and_description():
    fm, body = parse_skill(SAMPLE_SKILL)
    assert fm["name"] == "refine"
    assert fm["description"].startswith("Refine rough issue descriptions")
    assert "# Refining Issues" in body
    assert "---" not in body.split("\n")[0]


def test_emit_mdc_has_cursor_frontmatter_with_alwaysApply_false():
    fm = {"name": "refine", "description": "Refine stuff."}
    body = "# Refine\n\nHello."
    out = emit_mdc(fm, body)

    assert out.startswith("---\n")
    assert "description: Refine stuff." in out
    assert "alwaysApply: false" in out
    # Second --- closes frontmatter
    assert out.count("---\n") >= 2


def test_emit_mdc_preserves_body_content():
    fm = {"name": "x", "description": "d"}
    body = "# Heading\n\nParagraph with `code` and [a link](foo.md)."
    out = emit_mdc(fm, body)
    assert "# Heading" in out
    assert "Paragraph with `code` and [a link](foo.md)." in out


def test_idempotent_regeneration_produces_no_diff(tmp_path: Path):
    src = tmp_path / "skills" / "refine" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(SAMPLE_SKILL)

    out = tmp_path / ".cursor" / "rules" / "refine.mdc"

    generate(src, out)
    first = out.read_text()

    generate(src, out)
    second = out.read_text()

    assert first == second
