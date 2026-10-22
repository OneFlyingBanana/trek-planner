#!/usr/bin/env python3
"""Lint the Claude Code skills in `.claude/skills/`.

Checks every SKILL.md for:

- frontmatter: present, with a non-empty `name` equal to the skill's
  directory name and a non-empty `description`;
- TREK tool names: each one named must exist in `docs/trek-tools.txt`;
- blocked tools: no delete, share, invite, add-member or user/instance
  settings tool may be named (design ISD-4, section 6.5);
- referenced paths: each relative file path in an inline code span or a
  Markdown link must exist, next to the skill or from the repo root.
  Paths git ignores (runtime outputs such as `profile/USER_PROFILE.md`)
  are skipped.

Usage:
    python scripts/lint_skills.py [--root DIR] [--tools FILE] [SKILL ...]

SKILL is a skill directory or a SKILL.md file; the default is every skill
under `<root>/.claude/skills/`. Exits 1 when any error is found.
Standard library only, so CI needs no install step for it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TOOLS_FILE = Path("docs/trek-tools.txt")
SKILLS_DIR = Path(".claude/skills")

# First word of every TREK tool name. A backticked snake_case identifier
# starting with one of these is read as a tool name; anything else (plan
# fields such as `check_in_day`, Google Maps tools such as
# `maps_directions`) is left alone.
TOOL_VERBS = frozenset(
    """
    add apply assign available bulk calculate close copy create delete export
    find freeze get import invite link list locate lookup mark move preview
    rate react read reanchor remove reorder reset resolve restore reverse save
    search set share sync toggle unassign unlink unmark update upload vote
    """.split()
)

# Trip-level road-trip settings are allowed (design 6.5); every other
# settings tool belongs to Roald or the instance.
ALLOWED_SETTINGS_TOOLS = frozenset({"get_roadtrip_settings", "update_roadtrip_settings"})

QUALIFIED_TREK_TOOL = re.compile(r"\bmcp__trek__([A-Za-z0-9_-]+)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
TOOL_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")
PROSE_WORD = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
PATH_SEGMENT = re.compile(r"[A-Za-z0-9_.-]+")
FILE_EXTENSION = re.compile(r"\.[A-Za-z0-9]+$")
NAME_FORMAT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_KEY = re.compile(r"^([A-Za-z][\w-]*):[ \t]*(.*)$")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    message: str

    def format(self, root: Path) -> str:
        try:
            shown = self.path.resolve().relative_to(root.resolve())
        except ValueError:
            shown = self.path
        return f"{shown}:{self.line}: [{self.rule}] {self.message}"


def normalize_tool_name(name: str) -> str:
    """Paperclip lists TREK tools with hyphens, skills name them with underscores."""
    return name.strip().replace("-", "_")


def load_tool_names(tools_file: Path) -> frozenset[str]:
    """Read one tool name per line; blank lines and `#` comments are ignored."""
    names = set()
    for raw in tools_file.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            names.add(normalize_tool_name(line))
    return frozenset(names)


def blocked_reason(tool: str) -> str | None:
    """Return why `tool` is blocked for agents, or None if it is not."""
    words = tool.split("_")
    if words[0] == "delete":
        return "delete tools are blocked"
    if any(word.startswith("shar") for word in words):
        return "sharing tools are blocked"
    if "invite" in words:
        return "invite tools are blocked"
    adds_people = words[0] in {"add", "remove"} and any(
        word.startswith(("member", "collaborator", "user")) for word in words
    )
    if adds_people:
        return "tools that add or remove people are blocked"
    if ("settings" in words or "admin" in words) and tool not in ALLOWED_SETTINGS_TOOLS:
        return "user and instance settings tools are blocked"
    return None


def split_frontmatter(text: str) -> tuple[list[str], int] | None:
    """Return the frontmatter lines and the line number of the closing `---`."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], index + 1
    return None


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    """Parse top-level `key: value` pairs, folding indented continuation lines."""
    fields: dict[str, str] = {}
    key = None
    for line in lines:
        match = FRONTMATTER_KEY.match(line)
        if match:
            key = match.group(1)
            fields[key] = match.group(2).strip()
        elif key and line[:1] in (" ", "\t"):
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    for key, value in fields.items():
        if value[:1] in (">", "|"):
            value = value[1:].lstrip("+-").strip()
        fields[key] = value.strip("\"'").strip()
    return fields


def check_frontmatter(skill_file: Path, text: str) -> list[Finding]:
    split = split_frontmatter(text)
    if split is None:
        return [Finding(skill_file, 1, "frontmatter", "missing `---` frontmatter block")]
    fields = parse_frontmatter(split[0])
    findings = []
    name = fields.get("name", "")
    expected = skill_file.parent.name
    if not name:
        findings.append(Finding(skill_file, 1, "frontmatter", "missing `name`"))
    elif name != expected:
        findings.append(
            Finding(skill_file, 1, "frontmatter", f"`name: {name}` does not match directory `{expected}`")
        )
    elif not NAME_FORMAT.match(name):
        findings.append(
            Finding(skill_file, 1, "frontmatter", f"`name: {name}` must be lowercase words joined by hyphens")
        )
    if not fields.get("description"):
        findings.append(Finding(skill_file, 1, "frontmatter", "missing `description`"))
    return findings


def named_tools(line: str) -> set[str]:
    """Tool names a line refers to: `mcp__trek__x` anywhere, or `` `verb_object` `` in code."""
    tools = {normalize_tool_name(m) for m in QUALIFIED_TREK_TOOL.findall(line)}
    for span in INLINE_CODE.findall(line):
        candidate = span.strip().removesuffix("()").split("(", 1)[0]
        if TOOL_IDENTIFIER.fullmatch(candidate) and candidate.split("_", 1)[0] in TOOL_VERBS:
            tools.add(candidate)
    return tools


def check_tools(skill_file: Path, text: str, known_tools: frozenset[str] | None) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        tools = named_tools(line)
        # Blocked names are caught in plain prose too, not only in code spans.
        tools |= {
            word
            for word in PROSE_WORD.findall(line)
            if word.split("_", 1)[0] in TOOL_VERBS and blocked_reason(word)
        }
        for tool in sorted(tools):
            reason = blocked_reason(tool)
            if reason:
                findings.append(Finding(skill_file, number, "blocked-tool", f"`{tool}`: {reason}"))
            elif known_tools is not None and tool not in known_tools:
                findings.append(
                    Finding(skill_file, number, "unknown-tool", f"`{tool}` is not in the TREK tool list")
                )
    return findings


def looks_like_path(token: str) -> bool:
    """True for a relative file or directory path with no placeholders."""
    if token.startswith(("/", "~", "#")) or "://" in token:
        return False
    token = token.split("#", 1)[0]
    if "/" not in token:
        return False
    segments = token.rstrip("/").split("/")
    if not all(PATH_SEGMENT.fullmatch(segment) for segment in segments):
        return False
    return token.endswith("/") or bool(FILE_EXTENSION.search(segments[-1]))


def is_git_ignored(root: Path, relative: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--no-index", relative],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def check_paths(skill_file: Path, text: str, root: Path) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        tokens = [span.strip() for span in INLINE_CODE.findall(line)] + MARKDOWN_LINK.findall(line)
        for token in tokens:
            if not looks_like_path(token):
                continue
            relative = token.split("#", 1)[0]
            if (skill_file.parent / relative).exists() or (root / relative).exists():
                continue
            if is_git_ignored(root, relative):
                continue
            findings.append(Finding(skill_file, number, "missing-path", f"`{relative}` does not exist"))
    return findings


def lint_skill(skill_file: Path, root: Path, known_tools: frozenset[str] | None) -> list[Finding]:
    text = skill_file.read_text(encoding="utf-8")
    return (
        check_frontmatter(skill_file, text)
        + check_tools(skill_file, text, known_tools)
        + check_paths(skill_file, text, root)
    )


def resolve_skill_files(root: Path, targets: list[str]) -> list[Path]:
    if not targets:
        return sorted((root / SKILLS_DIR).glob("*/SKILL.md"))
    files = []
    for target in targets:
        path = Path(target)
        files.append(path / "SKILL.md" if path.is_dir() else path)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("skills", nargs="*", help="skill directories or SKILL.md files")
    parser.add_argument("--root", type=Path, default=Path("."), help="repo root (default: .)")
    parser.add_argument("--tools", type=Path, help=f"TREK tool list (default: <root>/{DEFAULT_TOOLS_FILE})")
    args = parser.parse_args(argv)

    root = args.root
    tools_file = args.tools or root / DEFAULT_TOOLS_FILE
    known_tools = None
    if tools_file.is_file():
        known_tools = load_tool_names(tools_file)
    else:
        print(f"warning: {tools_file} not found; unknown-tool check skipped", file=sys.stderr)

    skill_files = resolve_skill_files(root, args.skills)
    findings = []
    for skill_file in skill_files:
        if not skill_file.is_file():
            findings.append(Finding(skill_file, 0, "missing-skill", "SKILL.md not found"))
            continue
        findings.extend(lint_skill(skill_file, root, known_tools))

    for finding in findings:
        print(finding.format(root))
    print(f"{len(skill_files)} skill(s) checked, {len(findings)} error(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
