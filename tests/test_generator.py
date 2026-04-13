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


# --- Phase 2: full coverage + error handling ---

from scripts.generate_cursor_rules import generate_all, NameCollisionError


def _make_skill(dir: Path, name: str, desc: str = "Desc.") -> Path:
    (dir / "skills" / name).mkdir(parents=True)
    p = dir / "skills" / name / "SKILL.md"
    p.write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nBody.\n")
    return p


def test_generator_produces_mdc_for_every_skill(tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")
    _make_skill(tmp_path, "gamma")

    generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")

    outs = sorted((tmp_path / ".cursor" / "rules").glob("*.mdc"))
    assert [p.name for p in outs] == ["alpha.mdc", "beta.mdc", "gamma.mdc"]


def test_name_collision_exits_nonzero_with_conflict_paths(tmp_path: Path):
    _make_skill(tmp_path, "dup-a").write_text(
        "---\nname: duplicate\ndescription: A\n---\n\nBody A\n"
    )
    (tmp_path / "skills" / "dup-b").mkdir(parents=True)
    (tmp_path / "skills" / "dup-b" / "SKILL.md").write_text(
        "---\nname: duplicate\ndescription: B\n---\n\nBody B\n"
    )

    try:
        generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")
    except NameCollisionError as e:
        msg = str(e)
        assert "duplicate" in msg
        assert "dup-a" in msg
        assert "dup-b" in msg
    else:
        raise AssertionError("expected NameCollisionError")


import pytest


def test_malformed_yaml_exits_nonzero_with_file_and_reason(tmp_path: Path):
    (tmp_path / "skills" / "broken").mkdir(parents=True)
    src = tmp_path / "skills" / "broken" / "SKILL.md"
    src.write_text("---\nname: broken\ndescription: [unclosed\n---\n\nBody.\n")

    with pytest.raises(ValueError) as excinfo:
        generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")

    msg = str(excinfo.value)
    assert "broken" in msg


def test_missing_name_field_exits_nonzero(tmp_path: Path):
    (tmp_path / "skills" / "noname").mkdir(parents=True)
    src = tmp_path / "skills" / "noname" / "SKILL.md"
    src.write_text("---\ndescription: No name here\n---\n\nBody.\n")

    with pytest.raises(ValueError) as excinfo:
        generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")

    msg = str(excinfo.value)
    assert "name" in msg
    assert "noname" in msg


def test_missing_description_field_exits_nonzero(tmp_path: Path):
    (tmp_path / "skills" / "nodesc").mkdir(parents=True)
    src = tmp_path / "skills" / "nodesc" / "SKILL.md"
    src.write_text("---\nname: nodesc\n---\n\nBody.\n")

    with pytest.raises(ValueError) as excinfo:
        generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")

    msg = str(excinfo.value)
    assert "description" in msg
    assert "nodesc" in msg


# --- T2.3: Claude-compat note detection + resource path preservation ---

from scripts.generate_cursor_rules import has_claude_only_features, COMPAT_NOTE_MARKER


def test_skill_with_Task_dispatch_gets_compat_note(tmp_path: Path):
    (tmp_path / "skills" / "uses-task").mkdir(parents=True)
    src = tmp_path / "skills" / "uses-task" / "SKILL.md"
    src.write_text(
        "---\nname: uses-task\ndescription: Dispatches an agent.\n---\n\n"
        "Call Task(subagent_type='backend-engineer', prompt='...')\n"
    )

    generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")
    mdc = (tmp_path / ".cursor" / "rules" / "uses-task.mdc").read_text()

    assert COMPAT_NOTE_MARKER in mdc


def test_skill_with_Skill_agent_reference_gets_compat_note(tmp_path: Path):
    (tmp_path / "skills" / "calls-agent").mkdir(parents=True)
    src = tmp_path / "skills" / "calls-agent" / "SKILL.md"
    src.write_text(
        "---\nname: calls-agent\ndescription: Calls reviewer.\n---\n\n"
        "Use Skill(code-reviewer) to review.\n"
    )

    generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")
    mdc = (tmp_path / ".cursor" / "rules" / "calls-agent.mdc").read_text()

    assert COMPAT_NOTE_MARKER in mdc


def test_skill_without_claude_features_has_no_compat_note(tmp_path: Path):
    _make_skill(tmp_path, "plain")
    generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")
    mdc = (tmp_path / ".cursor" / "rules" / "plain.mdc").read_text()

    assert COMPAT_NOTE_MARKER not in mdc


def test_resource_paths_preserved_verbatim(tmp_path: Path):
    (tmp_path / "skills" / "has-res").mkdir(parents=True)
    src = tmp_path / "skills" / "has-res" / "SKILL.md"
    body = (
        "# Has Resources\n\n"
        "See [resources/example.md](resources/example.md) for details.\n"
        "Also [examples](resources/more/deep.md).\n"
    )
    src.write_text(f"---\nname: has-res\ndescription: Has resources.\n---\n\n{body}")

    generate_all(tmp_path / "skills", tmp_path / ".cursor" / "rules")
    mdc = (tmp_path / ".cursor" / "rules" / "has-res.mdc").read_text()

    assert "[resources/example.md](resources/example.md)" in mdc
    assert "[examples](resources/more/deep.md)" in mdc


def test_has_claude_only_features_detects_patterns():
    assert has_claude_only_features("Call Task(subagent_type='x')")
    assert has_claude_only_features("Use Skill(code-reviewer) here")
    assert has_claude_only_features("Dispatch Skill(executing-tasks, args=...)")
    assert not has_claude_only_features("Plain markdown body, no dispatch.")
    assert not has_claude_only_features("We use Skills (plural noun) without parens.")
