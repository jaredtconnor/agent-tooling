#!/usr/bin/env python3
"""Validate the agent tooling repo's source layout and projection metadata."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = ("skills", "agents", "commands", "hooks", "references", ".claude-plugin")
REQUIRED_FILES = ("AGENTS.md", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is invalid JSON: {exc}")


def has_frontmatter_field(text: str, field: str) -> bool:
    return frontmatter_field(text, field) is not None


def frontmatter_field(text: str, field: str) -> str | None:
    if not text.startswith("---\n"):
        return None

    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        return None

    for line in frontmatter.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip().strip("\"'")

    return None


def fail_duplicate_exports(kind: str, exports: dict[str, list[Path]]) -> None:
    duplicates = {name: paths for name, paths in exports.items() if len(paths) > 1}
    if not duplicates:
        return

    lines = [f"duplicate {kind} exports detected:"]
    for name, paths in sorted(duplicates.items()):
        joined = ", ".join(str(path.relative_to(ROOT)) for path in paths)
        lines.append(f"  {name}: {joined}")
    fail("\n".join(lines))


def command_invokes_skill(command_text: str, skill_name: str) -> bool:
    escaped = re.escape(skill_name)
    patterns = (
        rf"\bSkill\(\s*{escaped}\s*[,)]",
        rf"`{escaped}` skill",
        rf"uses the `{escaped}` skill",
    )
    return any(re.search(pattern, command_text, re.IGNORECASE) for pattern in patterns)


def validate_source_layout() -> None:
    for directory in REQUIRED_DIRS:
        path = ROOT / directory
        if not path.is_dir():
            fail(f"missing required directory: {directory}")

    for file_name in REQUIRED_FILES:
        path = ROOT / file_name
        if not path.is_file():
            fail(f"missing required file: {file_name}")


def validate_skills() -> None:
    skill_files = sorted((ROOT / "skills").glob("**/SKILL.md"))
    if not skill_files:
        fail("no skills found under skills/**/SKILL.md")

    skill_exports: dict[str, list[Path]] = {}
    for path in skill_files:
        text = path.read_text()
        rel = path.relative_to(ROOT)
        name = frontmatter_field(text, "name")
        if not name:
            fail(f"{rel} is missing frontmatter field: name")
        if not has_frontmatter_field(text, "description"):
            fail(f"{rel} is missing frontmatter field: description")
        skill_exports.setdefault(name, []).append(path)

    fail_duplicate_exports("skill", skill_exports)


def validate_agents() -> None:
    agent_files = sorted((ROOT / "agents").glob("**/*.md"))
    if not agent_files:
        fail("no agent personas found under agents/**/*.md")

    agent_exports: dict[str, list[Path]] = {}
    for path in agent_files:
        if path.name == "README.md":
            continue

        text = path.read_text()
        rel = path.relative_to(ROOT)
        name = frontmatter_field(text, "name")
        if not name:
            fail(f"{rel} is missing frontmatter field: name")
        if not has_frontmatter_field(text, "description"):
            fail(f"{rel} is missing frontmatter field: description")
        agent_exports.setdefault(name, []).append(path)

    fail_duplicate_exports("agent", agent_exports)


def validate_commands() -> None:
    command_files = sorted((ROOT / "commands").glob("*.md"))
    if not command_files:
        fail("no commands found under commands/*.md")

    command_exports: dict[str, list[Path]] = {}
    for path in command_files:
        command_exports.setdefault(path.stem, []).append(path)

    fail_duplicate_exports("command", command_exports)


def validate_command_skill_pairs() -> None:
    skills = {
        frontmatter_field(path.read_text(), "name"): path
        for path in sorted((ROOT / "skills").glob("**/SKILL.md"))
    }
    commands = {path.stem: path for path in sorted((ROOT / "commands").glob("*.md"))}
    overlaps = sorted(name for name in skills.keys() & commands.keys() if name)

    for name in overlaps:
        command_text = commands[name].read_text()
        if not command_invokes_skill(command_text, name):
            fail(
                "command/skill name overlap must be intentional and documented: "
                f"{name} ({commands[name].relative_to(ROOT)} and {skills[name].relative_to(ROOT)})"
            )


def validate_external_skills_manifest() -> None:
    path = ROOT / "external-skills.json"
    if not path.is_file():
        return  # manifest is optional

    data = read_json(path)
    if data.get("version") != 1:
        fail("external-skills.json must declare version: 1")

    sources = data.get("sources")
    if not isinstance(sources, list):
        fail("external-skills.json must contain a 'sources' array")

    seen_names: set[str] = set()
    seen_sources: set[str] = set()
    for entry in sources:
        if not isinstance(entry, dict):
            fail(f"external-skills.json source must be an object: {entry!r}")
        name = entry.get("name")
        source = entry.get("source")
        if not name or not isinstance(name, str):
            fail(f"external-skills.json entry missing 'name': {entry!r}")
        if not source or not isinstance(source, str):
            fail(f"external-skills.json entry '{name}' missing 'source'")
        if name in seen_names:
            fail(f"external-skills.json has duplicate name: {name}")
        if source in seen_sources:
            fail(f"external-skills.json has duplicate source: {source}")
        seen_names.add(name)
        seen_sources.add(source)
        skills = entry.get("skills")
        if skills is not None and not (
            isinstance(skills, list) and all(isinstance(s, str) for s in skills)
        ):
            fail(f"external-skills.json entry '{name}' has invalid 'skills' field")


def validate_plugin_metadata() -> None:
    plugin = read_json(ROOT / ".claude-plugin/plugin.json")
    marketplace = read_json(ROOT / ".claude-plugin/marketplace.json")

    if plugin.get("name") != "agent-tooling":
        fail(".claude-plugin/plugin.json name must be agent-tooling")
    if plugin.get("skills") != "./skills":
        fail(".claude-plugin/plugin.json must point skills to ./skills")
    if plugin.get("commands") != "./commands":
        fail(".claude-plugin/plugin.json must point commands to ./commands")

    agent_paths = plugin.get("agents")
    if not isinstance(agent_paths, list) or not agent_paths:
        fail(".claude-plugin/plugin.json must include explicit agent paths")
    for agent_path in agent_paths:
        if not (ROOT / agent_path).is_file():
            fail(f"plugin references missing agent file: {agent_path}")

    if marketplace.get("name") != "jared-agent-tooling":
        fail(".claude-plugin/marketplace.json name must be jared-agent-tooling")


def main() -> None:
    validate_source_layout()
    validate_skills()
    validate_agents()
    validate_commands()
    validate_command_skill_pairs()
    validate_external_skills_manifest()
    validate_plugin_metadata()
    print("agent tooling metadata is valid")


if __name__ == "__main__":
    main()
