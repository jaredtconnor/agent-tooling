#!/usr/bin/env python3
"""Validate the agent tooling repo's source layout and projection metadata."""

from __future__ import annotations

import json
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
    if not text.startswith("---\n"):
        return False

    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        return False

    return any(line.startswith(f"{field}:") for line in frontmatter.splitlines())


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

    for path in skill_files:
        text = path.read_text()
        rel = path.relative_to(ROOT)
        if not has_frontmatter_field(text, "name"):
            fail(f"{rel} is missing frontmatter field: name")
        if not has_frontmatter_field(text, "description"):
            fail(f"{rel} is missing frontmatter field: description")


def validate_agents() -> None:
    agent_files = sorted((ROOT / "agents").glob("**/*.md"))
    if not agent_files:
        fail("no agent personas found under agents/**/*.md")

    for path in agent_files:
        if path.name == "README.md":
            continue

        text = path.read_text()
        rel = path.relative_to(ROOT)
        if not has_frontmatter_field(text, "name"):
            fail(f"{rel} is missing frontmatter field: name")
        if not has_frontmatter_field(text, "description"):
            fail(f"{rel} is missing frontmatter field: description")


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
    validate_plugin_metadata()
    print("agent tooling metadata is valid")


if __name__ == "__main__":
    main()
