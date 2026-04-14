"""Tests for scripts/check_cursor_rules_fresh.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_cursor_rules_fresh import check_fresh
from scripts.generate_cursor_rules import generate_all


SKILL_TEMPLATE = "---\nname: {name}\ndescription: {name} skill.\n---\n\n# {name}\n\nBody.\n"


def _make_skill(root: Path, name: str) -> None:
    d = root / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=name))


def test_freshness_check_passes_when_committed_matches_generator(tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")

    rules_dir = tmp_path / ".cursor" / "rules"
    generate_all(tmp_path / "skills", rules_dir)

    drift = check_fresh(tmp_path / "skills", rules_dir)
    assert drift == []


def test_freshness_check_fails_when_committed_is_stale(tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    rules_dir = tmp_path / ".cursor" / "rules"
    generate_all(tmp_path / "skills", rules_dir)

    # Simulate source drift: edit the SKILL.md after the last regen.
    src = tmp_path / "skills" / "alpha" / "SKILL.md"
    src.write_text(src.read_text().replace("Body.", "Body changed."))

    drift = check_fresh(tmp_path / "skills", rules_dir)
    assert any("DIFFERS" in line and "alpha" in line for line in drift)


def test_freshness_check_detects_missing_output(tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    rules_dir = tmp_path / ".cursor" / "rules"
    rules_dir.mkdir(parents=True)
    # No generation done — committed dir is empty.

    drift = check_fresh(tmp_path / "skills", rules_dir)
    assert any("MISSING" in line and "alpha" in line for line in drift)


def test_freshness_check_detects_stale_extra(tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    rules_dir = tmp_path / ".cursor" / "rules"
    generate_all(tmp_path / "skills", rules_dir)
    # Orphan .mdc left behind after a SKILL.md was deleted.
    (rules_dir / "ghost.mdc").write_text("---\ndescription: orphan\n---\n\nBody.\n")

    drift = check_fresh(tmp_path / "skills", rules_dir)
    assert any("STALE" in line and "ghost" in line for line in drift)
