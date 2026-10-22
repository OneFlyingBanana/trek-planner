import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"

_spec = importlib.util.spec_from_file_location("lint_skills", REPO_ROOT / "scripts" / "lint_skills.py")
lint_skills = importlib.util.module_from_spec(_spec)
sys.modules["lint_skills"] = lint_skills
_spec.loader.exec_module(lint_skills)

FIXTURE_TOOLS = lint_skills.load_tool_names(FIXTURES / "trek-tools.txt")


def lint_fixture(name):
    return lint_skills.lint_skill(FIXTURES / "skills" / name / "SKILL.md", REPO_ROOT, FIXTURE_TOOLS)


def test_tool_list_normalizes_hyphens_and_skips_comments():
    assert "list_trips" in FIXTURE_TOOLS
    assert not any(name.startswith("#") or "-" in name for name in FIXTURE_TOOLS)


def test_good_fixture_passes():
    assert lint_fixture("good-skill") == []


def test_bad_fixture_reports_every_rule():
    messages = {(f.rule, f.message) for f in lint_fixture("bad-skill")}
    assert messages == {
        ("frontmatter", "`name: not-the-directory-name` does not match directory `bad-skill`"),
        ("frontmatter", "missing `description`"),
        ("unknown-tool", "`create_transport` is not in the TREK tool list"),
        ("blocked-tool", "`delete_place`: delete tools are blocked"),
        ("blocked-tool", "`get_share_link`: sharing tools are blocked"),
        ("blocked-tool", "`add_trip_member`: tools that add or remove people are blocked"),
        ("blocked-tool", "`update_display_settings`: user and instance settings tools are blocked"),
        ("missing-path", "`assets/missing-template.html` does not exist"),
        ("missing-path", "`docs/nowhere.md` does not exist"),
    }


def test_missing_frontmatter(tmp_path):
    skill = tmp_path / "bare" / "SKILL.md"
    skill.parent.mkdir()
    skill.write_text("# No frontmatter\n")
    findings = lint_skills.check_frontmatter(skill, skill.read_text())
    assert [f.message for f in findings] == ["missing `---` frontmatter block"]


@pytest.mark.parametrize(
    "tool",
    [
        "delete_trip",
        "get_share_link",
        "get_journey_share_link",
        "set_packing_item_sharing",
        "get_trip_invite_link",
        "add_trip_member",
        "remove_collaborator",
        "update_display_settings",
        "get_vacay_year_settings",
    ],
)
def test_blocked_tools(tool):
    assert lint_skills.blocked_reason(tool)


@pytest.mark.parametrize(
    "tool",
    [
        "update_roadtrip_settings",
        "get_roadtrip_settings",
        "create_budget_item_with_members",
        "set_bag_members",
        "list_trip_members",
        "available_collection_users",
        "create_place",
    ],
)
def test_allowed_tools(tool):
    assert lint_skills.blocked_reason(tool) is None


def test_cli_fails_on_bad_fixture(capsys):
    exit_code = lint_skills.main(
        [
            "--root", str(REPO_ROOT),
            "--tools", str(FIXTURES / "trek-tools.txt"),
            str(FIXTURES / "skills" / "bad-skill"),
        ]
    )
    assert exit_code == 1
    assert "1 skill(s) checked, 9 error(s)" in capsys.readouterr().out


def test_repo_skills_pass(capsys):
    """Uses docs/trek-tools.txt when present; before it lands the unknown-tool check is skipped."""
    assert lint_skills.main(["--root", str(REPO_ROOT)]) == 0
