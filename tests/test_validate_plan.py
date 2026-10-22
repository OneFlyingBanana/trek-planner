import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANS = REPO_ROOT / "tests" / "fixtures" / "plans"
SCRIPT = REPO_ROOT / "scripts" / "validate_plan.py"

_spec = importlib.util.spec_from_file_location("validate_plan", SCRIPT)
validate_plan = importlib.util.module_from_spec(_spec)
sys.modules["validate_plan"] = validate_plan
_spec.loader.exec_module(validate_plan)


def load(name):
    return json.loads((PLANS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture
def valid_plan():
    return load("valid-3day-polestar")


def run(plan, mode="auto", for_skeleton=False):
    return validate_plan.PlanValidator(copy.deepcopy(plan), "plan.json", mode, for_skeleton).run()


def checks(findings):
    return {(f.check, f.where) for f in findings}


def messages(findings):
    return " | ".join(f.message for f in findings)


# The three fixtures


def test_valid_fixture_has_no_errors(valid_plan):
    report = run(valid_plan)
    assert report.errors == []
    assert report.mode == "estimate"
    assert report.skeleton_gate[0] is True


def test_valid_fixture_warnings_are_only_the_travel_day_rule(valid_plan):
    report = run(valid_plan)
    assert checks(report.warnings) == {("pacing", "/days/0"), ("pacing", "/days/2")}
    assert "Day 1 is the arrival day and has 2 activities" in messages(report.warnings)


def test_valid_fixture_budget_and_nights(valid_plan):
    report = run(valid_plan)
    assert sum(amount for _, amount in report.budget_lines) == report.budget_total == 968
    assert report.nights == [
        (1, "Annecy", "Hôtel du Palais de l'Isle"),
        (2, "Chamonix-Mont-Blanc", "Hôtel Le Morgane"),
    ]


def test_legacy_v1_is_accepted_with_warnings():
    report = run(load("legacy-v1"))
    assert report.errors == []
    assert report.schema_label.startswith("v1")
    found = messages(report.warnings)
    for expected in (
        "v1 plan: accepted with warnings",
        "'plan_id' is a required property",
        "'brief' is a required property",
        "no budget_total",
        "build-trip --skeleton blocked",
    ):
        assert expected in found
    assert all(f.check != "schema" for f in report.findings)
    assert report.skeleton_gate[0] is False


def test_legacy_v1_pacing_uses_the_formula():
    report = run(load("legacy-v1"))
    assert [d.source for d in report.drives] == ["formula", "formula"]
    assert all(d.minutes > validate_plan.LONG_DAY_MIN for d in report.drives)


@pytest.mark.parametrize(
    "where, fragment",
    [
        ("/", "unknown_top_level_field"),
        ("/", "must not match"),
        ("/plan_id", "does not match"),
        ("/trek_title", "does not match"),
        ("/start_date", "does not match"),
        ("/currency", "does not match"),
        ("/travelers", "less than the minimum"),
        ("/starting_location", "'lng' is a required property"),
        ("/brief/pace", "'relaxed'"),
        ("/brief/vehicle", "'ev' is a required property"),
        ("/brief/sources/travelers", "'guess'"),
        ("/brief/driving_settings/settings", "roadtrip_range"),
        ("/brief/driving_settings/settings/roadtrip_vehicle", "'ev'"),
        ("/brief/driving_settings/settings/roadtrip_fill_percent", "120"),
        ("/brief/driving_settings/settings/roadtrip_day_start", "'9:00'"),
        ("/brief/driving_settings/settings/roadtrip_avoid", "'tolls'"),
        ("/brief/driving_settings/confirmed_on", "''"),
        ("/brief/driving_settings/confirmed_by", "'agent'"),
        ("/days/0/base", "'lng' is a required property"),
        ("/days/0/move", "'yes'"),
        ("/days/0/items/0/id", "'p1'"),
        ("/days/0/items/0/stop_type", "'castle'"),
        ("/days/0/items/0/origin", "'guess'"),
        ("/days/0/items/0/source", "non-empty"),
        ("/days/0/items/1", "'id' is a required property"),
        ("/days/0/items/1", "'origin' is a required property"),
        ("/days/0/items/2", "'text' is a required property"),
        ("/days/0/legs/0", "'arrival' is a required property"),
        ("/days/0/legs/1/km", "-5"),
        ("/days/0/legs/1/method", "'google'"),
        ("/days/0/vias/0", "'reason' is a required property"),
        ("/stays/0", "'total_price' is a required property"),
        ("/stays/0/check_out_day", "minimum"),
        ("/stays/0/nights", "minimum"),
        ("/stays/0/confidence", "'guessed'"),
        ("/stays/0/price_source_url", "booking.com"),
        ("/transport/0", "'source_file' is a required property"),
        ("/transport/0/from/code", "'gva'"),
        ("/transport/0/to", "'code' is a required property"),
        ("/budget/0/category", "'Hotels'"),
        ("/budget/0/amount", "-180"),
        ("/budget/0", "'basis' is a required property"),
        ("/budget_total/amount", "'968'"),
    ],
)
def test_broken_fixture_reports_every_schema_defect_in_the_readme(where, fragment):
    report = run(load("broken-v2"))
    at_path = [f.message for f in report.errors if f.check == "schema" and f.where == where]
    assert any(fragment in message for message in at_path), at_path


def test_broken_fixture_cross_field_errors():
    report = run(load("broken-v2"))
    assert {
        ("trek_title", "/trek_title"),
        ("item ids", "/days/0/items/0"),
        ("coordinates", "/days/0/items/1"),
        ("leg ids", "/days/0/legs/0/from_id"),
        ("via ids", "/days/0/vias/0/after_item_id"),
        ("day 1 start", "/starting_location"),
        ("stay days", "/stays/0"),
        ("budget total", "/budget_total/amount"),
    } <= checks(report.errors)


# Section 2.5: contract checks on mutated copies of the valid fixture


def test_trek_title_must_be_prefix_plus_title(valid_plan):
    valid_plan["trek_title"] = "[paperclip] something else"
    assert ("trek_title", "/trek_title") in checks(run(valid_plan).errors)


def test_move_day_needs_two_places(valid_plan):
    day = valid_plan["days"][1]
    day["items"] = day["items"][:1]
    day["legs"] = []
    assert ("move day", "/days/1") in checks(run(valid_plan).errors)


def test_day_one_must_start_at_home(valid_plan):
    valid_plan["days"][0]["items"].pop(0)
    valid_plan["days"][0]["legs"].pop(0)
    report = run(valid_plan)
    assert ("day 1 start", "/days/0/items/0") in checks(report.errors)


def test_budget_rows_must_sum_to_total(valid_plan):
    valid_plan["budget_total"]["amount"] = 1000
    report = run(valid_plan)
    assert "budget rows sum to 968, budget_total says 1000" in messages(report.errors)


def test_one_currency_per_plan(valid_plan):
    valid_plan["days"][0]["items"][1]["currency"] = "EUR"
    assert ("currency", "/days/0/items/1/currency") in checks(run(valid_plan).errors)


def test_leg_must_point_at_a_place_of_the_same_day(valid_plan):
    valid_plan["days"][0]["legs"][1]["to_id"] = "d02-p01"
    assert ("leg ids", "/days/0/legs/1/to_id") in checks(run(valid_plan).errors)


def test_item_id_must_carry_its_day_number(valid_plan):
    valid_plan["days"][1]["items"][0]["id"] = "d05-p01"
    valid_plan["days"][1]["legs"][0]["from_id"] = "d05-p01"
    assert ("item ids", "/days/1/items/0") in checks(run(valid_plan).errors)


def test_day_count_must_match_dates(valid_plan):
    valid_plan["end_date"] = "2026-05-18"
    assert "is 4 days but the plan has 3" in messages(run(valid_plan).errors)


@pytest.mark.parametrize("confirmed_on", [None, ""])
def test_unconfirmed_settings_block_the_skeleton_build(valid_plan, confirmed_on):
    valid_plan["brief"]["driving_settings"]["confirmed_on"] = confirmed_on
    advisory = run(valid_plan)
    assert advisory.skeleton_gate[0] is False
    assert ("skeleton gate", "/brief/driving_settings") in checks(advisory.warnings)
    gated = run(valid_plan, for_skeleton=True)
    assert ("skeleton gate", "/brief/driving_settings") in checks(gated.errors)


def test_confirmed_settings_pass_the_skeleton_gate(valid_plan):
    assert run(valid_plan, for_skeleton=True).errors == []


# Section 4.3: stays


def test_uncovered_night_is_an_error(valid_plan):
    valid_plan["stays"].pop(1)
    valid_plan["budget"] = [r for r in valid_plan["budget"] if "Morgane" not in r["name"]]
    valid_plan["budget_total"]["amount"] = 808
    report = run(valid_plan)
    assert "night after Day 2 has no stay" in messages(report.errors)
    assert (2, "Chamonix-Mont-Blanc", "MISSING") in report.nights


def test_double_covered_night_is_an_error(valid_plan):
    extra = copy.deepcopy(valid_plan["stays"][0])
    extra["name"] = "Second hotel"
    valid_plan["stays"].append(extra)
    assert "night after Day 1 has 2 stays" in messages(run(valid_plan).errors)


def test_empty_stays_skip_coverage_with_a_warning(valid_plan):
    valid_plan["stays"] = []
    valid_plan["budget"] = [r for r in valid_plan["budget"] if r["category"] != "Accommodation"]
    valid_plan["budget_total"]["amount"] = 628
    report = run(valid_plan)
    assert report.errors == []
    assert "find-stays has not run" in messages(report.warnings)


def test_nights_must_match_check_in_and_out(valid_plan):
    valid_plan["stays"][0]["nights"] = 2
    assert ("stay nights", "/stays/0") in checks(run(valid_plan).errors)


def test_stay_budget_rows_must_match_stay_totals(valid_plan):
    valid_plan["stays"][0]["total_price"] = 200
    valid_plan["stays"][0]["price_per_night"] = 200
    report = run(valid_plan)
    assert "Accommodation rows sum to 340, stays' total_price sums to 360" in messages(report.errors)


def test_far_stay_is_a_warning_unless_deliberate(valid_plan):
    valid_plan["stays"][0].update(lat=46.2044, lng=6.1432)  # Geneva, about 34 km from Annecy
    assert ("stay distance", "/stays/0") in checks(run(valid_plan).warnings)
    valid_plan["stays"][0]["deliberate_distance"] = True
    assert ("stay distance", "/stays/0") not in checks(run(valid_plan).warnings)


# Section 5.2: pacing, estimate mode and trek mode


def trek_legs(plan, minutes_day_one, arrival="17:00"):
    for day in plan["days"]:
        for leg in day["legs"]:
            leg.update(method="trek", arrival="12:00")
    plan["days"][0]["legs"][1].update(min=minutes_day_one, arrival=arrival)
    return plan


def test_auto_mode_switches_to_trek_when_legs_come_from_the_calculator(valid_plan):
    report = run(trek_legs(valid_plan, 100))
    assert report.mode == "trek"
    assert report.errors == []


def test_day_over_day_minutes_is_an_error_in_trek_mode(valid_plan):
    report = run(trek_legs(valid_plan, 500))
    assert "545 min driving exceeds roadtrip_day_minutes 480" in messages(report.errors)


def test_day_over_day_minutes_is_only_a_warning_in_estimate_mode(valid_plan):
    valid_plan["days"][0]["legs"][1]["min"] = 500
    report = run(valid_plan, mode="estimate")
    assert report.errors == []
    assert "estimated 545 min driving exceeds roadtrip_day_minutes 480" in messages(report.warnings)


def test_long_day_and_long_leg_warnings(valid_plan):
    report = run(trek_legs(valid_plan, 260))
    found = messages(report.warnings)
    assert "305 min driving, over 4 h" in found
    assert "leg of 260 min exceeds roadtrip_leg_minutes 150" in found


def test_three_long_move_days_in_a_row_warn(valid_plan):
    for day in valid_plan["days"]:
        day["legs"][0]["min"] = 190
    assert "more than 2 consecutive move days over 3 h" in messages(run(valid_plan).warnings)


def test_estimate_leg_in_trek_mode_warns(valid_plan):
    trek_legs(valid_plan, 100)
    valid_plan["days"][2]["legs"][0]["method"] = "estimate"
    assert ("pacing", "/days/2/legs/0") in checks(run(valid_plan).warnings)


def test_routing_failure_is_an_error(valid_plan):
    trek_legs(valid_plan, 100)
    valid_plan["days"][1]["legs"][0]["warnings"] = ["Routing failed: no road to this place"]
    assert ("routing failure", "/days/1/legs/0") in checks(run(valid_plan).errors)


def test_late_arrival_at_the_stay_warns(valid_plan):
    report = run(trek_legs(valid_plan, 100, arrival="20:15"))
    assert "Day 1 arrives 20:15, after the check-in window" in messages(report.warnings)


def test_every_fifth_day_is_a_rest_day(valid_plan):
    plan = valid_plan
    template = plan["days"][1]
    for number in range(4, 7):
        day = copy.deepcopy(template)
        day["day_number"] = number
        day["date"] = f"2026-05-{14 + number}"
        for item in day["items"]:
            item["id"] = item["id"].replace("d02-", f"d{number:02d}-")
        for leg in day["legs"]:
            leg["from_id"] = leg["from_id"].replace("d02-", f"d{number:02d}-")
            leg["to_id"] = leg["to_id"].replace("d02-", f"d{number:02d}-")
        plan["days"].insert(number - 1, day)
    plan["end_date"] = "2026-05-20"
    plan["stays"].clear()
    plan["budget"] = [r for r in plan["budget"] if r["category"] != "Accommodation"]
    plan["budget_total"]["amount"] = 628
    report = run(plan)
    assert "Day 5 is a rest-rhythm day" in messages(report.warnings)


def test_formula_estimate_matches_docs_pacing():
    km, minutes = validate_plan.estimate_drive(250, ev=True)
    assert km == pytest.approx(325)
    assert minutes == pytest.approx(325 / 75 * 60 + 30)


# CLI


def test_cli_prints_and_writes_validation_md(tmp_path):
    output = tmp_path / "validation.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(PLANS / "valid-3day-polestar.json"), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("# Validation: fixture")
    assert result.stdout == output.read_text(encoding="utf-8") + "\n"
    for heading in ("## Build gate", "## Errors", "## Warnings", "## Pacing", "## Night coverage", "## Budget"):
        assert heading in result.stdout


@pytest.mark.parametrize(
    "fixture, code",
    [("valid-3day-polestar", 0), ("legacy-v1", 0), ("broken-v2", 1)],
)
def test_cli_exit_codes(fixture, code):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(PLANS / f"{fixture}.json")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == code


def test_cli_for_skeleton_fails_on_legacy_plan():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(PLANS / "legacy-v1.json"), "--for-skeleton"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "`build-trip --skeleton`: blocked" in result.stdout


def test_cli_unreadable_plan_exits_2(tmp_path):
    bad = tmp_path / "plan.json"
    bad.write_text("{not json", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True)
    assert result.returncode == 2
    assert "cannot read" in result.stderr
