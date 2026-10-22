#!/usr/bin/env python3
"""Validate a trek-planner plan JSON and print ``validation.md``.

Implements the deterministic checks of design ISD-4 (revision 4):

* section 2.5: schema v2, required cross-field rules, the driving-settings
  gate for ``build-trip --skeleton``;
* section 4.3: night coverage, stay check-in days, stay distance and arrival,
  stay budget rows;
* section 5.2: pacing rules, with thresholds mirrored from ``docs/pacing.md``.

Two modes:

* ``estimate``: before the skeleton build. Driving times come from legs with
  ``method: estimate`` or from the fallback formula; pacing findings are
  warnings because the numbers are rough.
* ``trek``: after route-check. Driving times come from legs with
  ``method: trek`` (TREK's calculator); exceeding the trip's
  ``roadtrip_day_minutes`` is an error.

``--mode auto`` (the default) picks ``trek`` when any leg has ``method: trek``.

v1 plans (``schema_version: 1``) are accepted with warnings: v2 schema
differences are reported as warnings, the cross-field checks still run.

Exit codes: 0 no errors (warnings allowed), 1 errors found, 2 the plan could
not be read.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "plan.v2.schema.json"

# Thresholds mirrored from docs/pacing.md; change both together.
LONG_DAY_MIN = 240
CONSECUTIVE_LONG_DAY_MIN = 180
MAX_CONSECUTIVE_LONG_DAYS = 2
REST_DAY_EVERY = 5
MAX_ACTIVITIES_ON_REST_DAY = 1
MAX_ACTIVITIES_ON_TRAVEL_DAY = 1
STAY_MAX_KM = 30.0

# Fallback estimate from docs/pacing.md.
ROAD_FACTOR = 1.3
ESTIMATE_SPEED_KMH = 75.0
EV_CHARGE_EVERY_KM = 300.0
EV_CHARGE_MIN = 30.0

SAME_PLACE_KM = 1.0
MONEY_TOLERANCE = 0.5
SERVICE_STOP_TYPES = {"fuel", "charging", "rest_area"}
NOT_ACTIVITY_STOP_TYPES = SERVICE_STOP_TYPES | {"restaurant", "hotel", "campsite"}

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    level: str
    check: str
    where: str
    message: str


@dataclass
class DayDrive:
    day_number: int
    move: bool
    minutes: float
    km: float
    source: str
    leg_minutes: list[float]


@dataclass
class Report:
    plan_path: str
    title: str
    plan_id: str
    schema_label: str
    mode: str
    for_skeleton: bool
    findings: list[Finding]
    drives: list[DayDrive]
    nights: list[tuple[int, str, str]]
    budget_lines: list[tuple[str, float]]
    budget_total: float | None
    skeleton_gate: tuple[bool, str]
    call_estimate: dict[str, int]
    skipped: list[str]

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == WARNING]


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _dicts(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict)]


def _coords(entry: Any) -> tuple[float, float] | None:
    if not isinstance(entry, dict):
        return None
    lat, lng = _number(entry.get("lat")), _number(entry.get("lng"))
    if lat is None or lng is None:
        return None
    return lat, lng


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def estimate_drive(km_great_circle: float, ev: bool) -> tuple[float, float]:
    """Return (road km, minutes) for the fallback formula in docs/pacing.md."""
    road_km = km_great_circle * ROAD_FACTOR
    minutes = road_km / ESTIMATE_SPEED_KMH * 60
    if ev:
        minutes += math.floor(road_km / EV_CHARGE_EVERY_KM) * EV_CHARGE_MIN
    return road_km, minutes


def _parse_date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _minutes_of_day(value: Any) -> int | None:
    try:
        hours, minutes = str(value).split(":")
        return int(hours) * 60 + int(minutes)
    except ValueError:
        return None


def _pointer(path: Iterable[Any]) -> str:
    return "/" + "/".join(str(part) for part in path)


def _describe_schema_error(error: jsonschema.ValidationError) -> list[tuple[str, str]]:
    """Turn one schema error into readable (pointer, message) pairs.

    A ``oneOf``/``anyOf`` failure is reported through the branch whose
    ``type`` discriminator matches (a place item is described as a place, not
    as a note); without a discriminator the branch messages are joined.
    """
    where = _pointer(error.absolute_path)
    if error.validator == "not":
        return [(where, f"must not match {json.dumps(error.validator_value)}")]
    if not error.context:
        return [(where, error.message)]
    branches: dict[Any, list[jsonschema.ValidationError]] = {}
    for sub in error.context:
        branches.setdefault(sub.relative_schema_path[0], []).append(sub)
    discriminated = [
        errors for errors in branches.values()
        if not any(e.validator == "const" and list(e.relative_path) == ["type"] for e in errors)
    ]
    if len(discriminated) == 1:
        return [pair for sub in discriminated[0] for pair in _describe_schema_error(sub)]
    messages = sorted({jsonschema.exceptions.best_match(errors).message for errors in branches.values()})
    return [(where, " or ".join(messages))]


class PlanValidator:
    def __init__(self, plan: dict, plan_path: str, mode: str, for_skeleton: bool):
        self.plan = plan
        self.plan_path = plan_path
        self.for_skeleton = for_skeleton
        self.findings: list[Finding] = []
        self.skipped: list[str] = []
        self.legacy = plan.get("schema_version") == 1
        self.days = _dicts(plan.get("days"))
        self.stays_key = "stays" if "stays" in plan else "accommodations"
        self.stays = _dicts(plan.get(self.stays_key))
        brief = plan.get("brief") if isinstance(plan.get("brief"), dict) else {}
        self.brief = brief
        driving = brief.get("driving_settings")
        self.driving = driving if isinstance(driving, dict) else {}
        settings = self.driving.get("settings")
        self.settings = settings if isinstance(settings, dict) else {}
        self.home = _coords(plan.get("starting_location"))
        self.mode = self._resolve_mode(mode)

    def _add(self, level: str, check: str, where: str, message: str) -> None:
        self.findings.append(Finding(level, check, where, message))

    def _resolve_mode(self, mode: str) -> str:
        if mode != "auto":
            return mode
        for day in self.days:
            if any(leg.get("method") == "trek" for leg in _dicts(day.get("legs"))):
                return "trek"
        return "estimate"

    def _is_home(self, coords: tuple[float, float] | None) -> bool:
        return bool(self.home and coords and haversine_km(self.home, coords) <= SAME_PLACE_KM)

    def _places(self, day: dict) -> list[dict]:
        return [i for i in _dicts(day.get("items")) if i.get("type") == "place"]

    def _is_ev(self) -> bool:
        vehicle = self.brief.get("vehicle")
        if isinstance(vehicle, dict) and vehicle.get("ev") is True:
            return True
        return self.settings.get("roadtrip_vehicle") == "electric"

    def _day_minutes_limit(self) -> float | None:
        limit = _number(self.settings.get("roadtrip_day_minutes"))
        return limit if limit else _number(self.brief.get("max_driving_min_per_day")) or None

    def _leg_minutes_limit(self) -> float | None:
        limit = _number(self.settings.get("roadtrip_leg_minutes"))
        return limit if limit else _number(self.brief.get("max_driving_min_per_leg")) or None

    def _day_end_time(self) -> int | None:
        value = self.settings.get("roadtrip_day_end") or self.brief.get("day_end")
        return _minutes_of_day(value) if value else None

    def _stay_for_night(self, night: int) -> dict | None:
        for stay in self.stays:
            check_in, check_out = stay.get("check_in_day"), stay.get("check_out_day")
            if isinstance(check_in, int) and isinstance(check_out, int) and check_in <= night < check_out:
                return stay
        return None

    def run(self) -> Report:
        self.check_schema()
        self.check_identity()
        self.check_days_and_dates()
        self.check_items()
        self.check_first_day_start()
        self.check_currency()
        self.check_stays()
        nights = self.check_night_coverage()
        budget_lines, budget_total = self.check_budget()
        drives = self.check_pacing()
        self.check_activity_rhythm()
        gate = self.check_skeleton_gate()
        self.skipped.append(
            "Opening days (docs/pacing.md): plan v2 has no opening-hours field on items yet."
        )
        return Report(
            plan_path=self.plan_path,
            title=str(self.plan.get("title") or "(untitled)"),
            plan_id=str(self.plan.get("plan_id") or "(none)"),
            schema_label="v1 (legacy, accepted with warnings)" if self.legacy else "v2",
            mode=self.mode,
            for_skeleton=self.for_skeleton,
            findings=self.findings,
            drives=drives,
            nights=nights,
            budget_lines=budget_lines,
            budget_total=budget_total,
            skeleton_gate=gate,
            call_estimate=self.estimate_calls(),
            skipped=self.skipped,
        )

    # Section 2.5: contract

    def check_schema(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft7Validator(schema)
        version = self.plan.get("schema_version")
        if version not in (1, 2):
            self._add(ERROR, "schema", "/schema_version", f"unknown schema_version {version!r}; expected 2 (or 1 for legacy plans)")
        level = WARNING if self.legacy else ERROR
        check = "schema v2 (legacy plan)" if self.legacy else "schema"
        if self.legacy:
            self._add(WARNING, "legacy", "/schema_version", "v1 plan: accepted with warnings; migrate to schema v2 before the next build")
        described = [
            pair
            for error in validator.iter_errors(self.plan)
            if not (self.legacy and list(error.absolute_path) == ["schema_version"])
            for pair in _describe_schema_error(error)
        ]
        for where, message in sorted(described):
            self._add(level, check, where, message)

    def check_identity(self) -> None:
        title, trek_title = self.plan.get("title"), self.plan.get("trek_title")
        if self.legacy:
            return
        if isinstance(title, str) and isinstance(trek_title, str) and trek_title != f"[paperclip] {title}":
            self._add(ERROR, "trek_title", "/trek_title", f"must be '[paperclip] ' + title, i.e. {('[paperclip] ' + title)!r}")
        brief_travelers = self.brief.get("travelers")
        if brief_travelers is not None and brief_travelers != self.plan.get("travelers"):
            self._add(WARNING, "travelers", "/brief/travelers", f"brief says {brief_travelers}, plan says {self.plan.get('travelers')}")

    def check_days_and_dates(self) -> None:
        numbers = [d.get("day_number") for d in self.days]
        expected = list(range(1, len(self.days) + 1))
        if numbers != expected:
            self._add(ERROR, "day numbers", "/days", f"day_number must run 1..{len(self.days)} in order; found {numbers}")
        start, end = _parse_date(self.plan.get("start_date")), _parse_date(self.plan.get("end_date"))
        if not start or not end:
            self._add(ERROR, "dates", "/start_date", "start_date and end_date must be ISO dates; day count and day dates not checked")
            return
        span = (end - start).days + 1
        if span != len(self.days):
            self._add(ERROR, "dates", "/days", f"{start} to {end} is {span} days but the plan has {len(self.days)}")
        for index, day in enumerate(self.days):
            date = day.get("date")
            expected_date = (start + dt.timedelta(days=index)).isoformat()
            if date is not None and date != expected_date:
                self._add(ERROR, "dates", f"/days/{index}/date", f"Day {index + 1} should be {expected_date}, found {date}")

    def check_items(self) -> None:
        seen: dict[str, str] = {}
        for d_index, day in enumerate(self.days):
            day_number = day.get("day_number")
            ids_today: set[str] = set()
            place_ids_today: set[str] = set()
            for i_index, item in enumerate(_dicts(day.get("items"))):
                where = f"/days/{d_index}/items/{i_index}"
                if item.get("type") == "place" and _coords(item) is None:
                    self._add(ERROR, "coordinates", where, f"place {item.get('name', '(unnamed)')!r} has no lat/lng")
                item_id = item.get("id")
                if not isinstance(item_id, str):
                    continue
                if item_id in seen:
                    self._add(ERROR, "item ids", where, f"id {item_id} already used at {seen[item_id]}")
                seen[item_id] = where
                ids_today.add(item_id)
                if item.get("type") == "place":
                    place_ids_today.add(item_id)
                if isinstance(day_number, int) and not item_id.startswith(f"d{day_number:02d}-"):
                    self._add(ERROR, "item ids", where, f"id {item_id} does not belong to Day {day_number} (expected prefix d{day_number:02d}-)")
            if not self.legacy and day.get("move") is True and len(self._places(day)) < 2:
                self._add(ERROR, "move day", f"/days/{d_index}", f"Day {day_number} is a move day with fewer than two places; TREK cannot draw the route")
            for l_index, leg in enumerate(_dicts(day.get("legs"))):
                for end in ("from_id", "to_id"):
                    ref = leg.get(end)
                    if isinstance(ref, str) and ref not in place_ids_today:
                        self._add(ERROR, "leg ids", f"/days/{d_index}/legs/{l_index}/{end}", f"{ref} is not a place on Day {day_number}")
            references = [(f"vias/{v}", via) for v, via in enumerate(_dicts(day.get("vias")))]
            if isinstance(day.get("day_end"), dict):
                references.append(("day_end", day["day_end"]))
            for path, entry in references:
                ref = entry.get("after_item_id")
                if isinstance(ref, str) and ref not in ids_today:
                    self._add(ERROR, "via ids", f"/days/{d_index}/{path}/after_item_id", f"{ref} is not an item on Day {day_number}")

    def check_first_day_start(self) -> None:
        if not self.days:
            return
        if self.home is None:
            self._add(ERROR, "day 1 start", "/starting_location", "starting_location has no coordinates; Day 1 start not checked")
            return
        places = self._places(self.days[0])
        first = _coords(places[0]) if places else None
        if first is None:
            self._add(ERROR, "day 1 start", "/days/0/items", "Day 1 has no first place with coordinates")
        elif not self._is_home(first):
            distance = haversine_km(self.home, first)
            self._add(ERROR, "day 1 start", "/days/0/items/0", f"Day 1 must start at starting_location {self.plan['starting_location'].get('name')!r}; first place is {distance:.1f} km away")

    def check_currency(self) -> None:
        currency = self.plan.get("currency")
        entries: list[tuple[str, Any]] = []
        for d_index, day in enumerate(self.days):
            for i_index, item in enumerate(_dicts(day.get("items"))):
                entries.append((f"/days/{d_index}/items/{i_index}/currency", item.get("currency")))
        for t_index, transport in enumerate(_dicts(self.plan.get("transport"))):
            entries.append((f"/transport/{t_index}/currency", transport.get("currency")))
        for where, value in entries:
            if value is not None and value != currency:
                self._add(ERROR, "currency", where, f"{value!r} differs from the plan currency {currency!r}; a plan uses one currency")

    # Section 4.3: stays

    def check_stays(self) -> None:
        if self.stays_key == "accommodations" and not self.legacy:
            self._add(WARNING, "stays", "/accommodations", "accommodations is the v1 name; rename to stays")
        day_count = len(self.days)
        for s_index, stay in enumerate(self.stays):
            where = f"/{self.stays_key}/{s_index}"
            name = stay.get("name", "(unnamed)")
            check_in, check_out, nights = stay.get("check_in_day"), stay.get("check_out_day"), stay.get("nights")
            if not (isinstance(check_in, int) and isinstance(check_out, int)):
                self._add(ERROR, "stay days", where, f"{name!r} needs integer check_in_day and check_out_day")
                continue
            if not 1 <= check_in < check_out <= day_count:
                self._add(ERROR, "stay days", where, f"{name!r}: check-in Day {check_in}, check-out Day {check_out} must satisfy 1 <= in < out <= {day_count}")
            if isinstance(nights, int) and nights != check_out - check_in:
                self._add(ERROR, "stay nights", where, f"{name!r}: nights is {nights} but Day {check_in} to Day {check_out} is {check_out - check_in}")
            total, per_night = _number(stay.get("total_price")), _number(stay.get("price_per_night"))
            if total is not None and per_night is not None and isinstance(nights, int) and nights > 0:
                if abs(total - per_night * nights) > MONEY_TOLERANCE:
                    self._add(WARNING, "stay price", where, f"{name!r}: total_price {total:g} is not {nights} × {per_night:g}")
            self._check_stay_position(stay, where, check_in, check_out)

    def _check_stay_position(self, stay: dict, where: str, check_in: int, check_out: int) -> None:
        name = stay.get("name", "(unnamed)")
        stay_at = _coords(stay)
        if stay_at is None or stay.get("deliberate_distance") is True:
            return
        for night in range(check_in, min(check_out, len(self.days) + 1)):
            base = _coords(self.days[night - 1].get("base"))
            if base and haversine_km(base, stay_at) > STAY_MAX_KM:
                self._add(WARNING, "stay distance", where, f"{name!r} is {haversine_km(base, stay_at):.0f} km from the Day {night} base; mark deliberate_distance if intended")
        if self.mode != "trek" or not 1 <= check_in <= len(self.days):
            return
        day = self.days[check_in - 1]
        end = self._calculated_day_end(day)
        if end and haversine_km(end, stay_at) > STAY_MAX_KM:
            self._add(WARNING, "stay distance", where, f"{name!r} is {haversine_km(end, stay_at):.0f} km from where Day {check_in} ends")
        arrival = self._last_arrival(day)
        window_end = self._day_end_time()
        if arrival is not None and window_end is not None and arrival > window_end:
            self._add(WARNING, "stay arrival", where, f"Day {check_in} arrives {arrival // 60:02d}:{arrival % 60:02d}, after the check-in window ends at the trip's day end")

    def _calculated_day_end(self, day: dict) -> tuple[float, float] | None:
        if isinstance(day.get("day_end"), dict):
            return _coords(day["day_end"])
        legs = _dicts(day.get("legs"))
        places = {p.get("id"): p for p in self._places(day)}
        if legs and legs[-1].get("to_id") in places:
            return _coords(places[legs[-1]["to_id"]])
        last = self._places(day)
        return _coords(last[-1]) if last else None

    def _last_arrival(self, day: dict) -> int | None:
        arrivals = [_minutes_of_day(leg.get("arrival")) for leg in _dicts(day.get("legs")) if leg.get("method") == "trek" and leg.get("arrival")]
        arrivals = [a for a in arrivals if a is not None]
        return arrivals[-1] if arrivals else None

    def check_night_coverage(self) -> list[tuple[int, str, str]]:
        rows: list[tuple[int, str, str]] = []
        if len(self.days) < 2:
            return rows
        if not self.stays:
            self._add(WARNING, "night coverage", f"/{self.stays_key}", "no stays yet (find-stays has not run); night coverage not checked")
            return rows
        for night in range(1, len(self.days)):
            day = self.days[night - 1]
            base = day.get("base") if isinstance(day.get("base"), dict) else {}
            covering = [
                s for s in self.stays
                if isinstance(s.get("check_in_day"), int) and isinstance(s.get("check_out_day"), int)
                and s["check_in_day"] <= night < s["check_out_day"]
            ]
            names = ", ".join(str(s.get("name")) for s in covering)
            if self._is_home(_coords(base)) and not covering:
                rows.append((night, str(base.get("name", "")), "home"))
                continue
            rows.append((night, str(base.get("name", "(no base)")), names or "MISSING"))
            if not covering:
                self._add(ERROR, "night coverage", f"/days/{night - 1}", f"night after Day {night} has no stay")
            elif len(covering) > 1:
                self._add(ERROR, "night coverage", f"/days/{night - 1}", f"night after Day {night} has {len(covering)} stays: {names}")
        return rows

    # Section 2.5 and 5.3: budget

    def check_budget(self) -> tuple[list[tuple[str, float]], float | None]:
        totals: dict[str, float] = {}
        for row in _dicts(self.plan.get("budget")):
            amount = _number(row.get("amount"))
            if amount is not None:
                category = str(row.get("category", "(none)"))
                totals[category] = totals.get(category, 0.0) + amount
        rows_sum = sum(totals.values())
        headline = self.plan.get("budget_total")
        total = _number(headline.get("amount")) if isinstance(headline, dict) else None
        if headline is None:
            self._add(WARNING, "budget total", "/budget_total", "no budget_total; row sum not compared with a headline total")
        elif total is None:
            self._add(ERROR, "budget total", "/budget_total/amount", "budget_total.amount is not a number")
        elif abs(total - rows_sum) > MONEY_TOLERANCE:
            self._add(ERROR, "budget total", "/budget_total/amount", f"budget rows sum to {rows_sum:g}, budget_total says {total:g}")
        stays_sum = sum(_number(s.get("total_price")) or 0.0 for s in self.stays)
        accommodation = totals.get("Accommodation", 0.0)
        if self.stays and abs(stays_sum - accommodation) > MONEY_TOLERANCE:
            self._add(ERROR, "stay budget", "/budget", f"Accommodation rows sum to {accommodation:g}, stays' total_price sums to {stays_sum:g}")
        return sorted(totals.items()), total

    # Section 5.2: pacing

    def _night_location(self, day_index: int) -> tuple[float, float] | None:
        if day_index == 0:
            return self.home
        previous = self.days[day_index - 1]
        base = _coords(previous.get("base"))
        if base:
            return base
        stay = self._stay_for_night(day_index)
        if stay and _coords(stay):
            return _coords(stay)
        places = self._places(previous)
        return _coords(places[-1]) if places else None

    def _day_drive(self, day_index: int) -> DayDrive:
        day = self.days[day_index]
        legs = _dicts(day.get("legs"))
        if legs:
            minutes = [_number(leg.get("min")) or 0.0 for leg in legs]
            km = sum(_number(leg.get("km")) or 0.0 for leg in legs)
            methods = sorted({str(leg.get("method")) for leg in legs})
            source = "legs: " + ", ".join(methods)
            total = sum(minutes)
        else:
            chain = [self._night_location(day_index)]
            chain += [_coords(p) for p in self._places(day)]
            end = _coords(day.get("base"))
            if end is None:
                stay = self._stay_for_night(day_index + 1)
                end = _coords(stay) if stay else None
            chain.append(end)
            points = [p for p in chain if p is not None]
            great_circle = sum(haversine_km(a, b) for a, b in zip(points, points[1:]))
            km, total = estimate_drive(great_circle, self._is_ev())
            minutes = []
            source = "formula"
        move = day.get("move")
        if not isinstance(move, bool):
            move = km > 2 * STAY_MAX_KM
        return DayDrive(day.get("day_number", day_index + 1), move, total, km, source, minutes)

    def check_pacing(self) -> list[DayDrive]:
        drives = [self._day_drive(i) for i in range(len(self.days))]
        day_limit, leg_limit = self._day_minutes_limit(), self._leg_minutes_limit()
        rough = self.mode == "estimate"
        streak = 0
        for index, drive in enumerate(drives):
            where = f"/days/{index}"
            day = self.days[index]
            if self.mode == "trek" and drive.move:
                for l_index, leg in enumerate(_dicts(day.get("legs"))):
                    if leg.get("method") != "trek":
                        self._add(WARNING, "pacing", f"{where}/legs/{l_index}", f"Day {drive.day_number} leg is method {leg.get('method')!r}, not from TREK's calculator")
                    for warning in leg.get("warnings") or []:
                        if isinstance(warning, str) and "rout" in warning.lower() and "fail" in warning.lower():
                            self._add(ERROR, "routing failure", f"{where}/legs/{l_index}", f"Day {drive.day_number}: {warning}")
                if not _dicts(day.get("legs")):
                    self._add(WARNING, "pacing", where, f"Day {drive.day_number} is a move day without calculator legs")
            label = "estimated " if rough else ""
            if day_limit and drive.minutes > day_limit:
                level = WARNING if rough else ERROR
                self._add(level, "pacing", where, f"Day {drive.day_number}: {label}{drive.minutes:.0f} min driving exceeds roadtrip_day_minutes {day_limit:g}")
            elif drive.minutes > LONG_DAY_MIN:
                self._add(WARNING, "pacing", where, f"Day {drive.day_number}: {label}{drive.minutes:.0f} min driving, over {LONG_DAY_MIN // 60} h")
            if leg_limit:
                for l_index, leg_minutes in enumerate(drive.leg_minutes):
                    if leg_minutes > leg_limit:
                        self._add(WARNING, "pacing", f"{where}/legs/{l_index}", f"Day {drive.day_number}: leg of {leg_minutes:.0f} min exceeds roadtrip_leg_minutes {leg_limit:g}; plan a rest stop")
            streak = streak + 1 if drive.move and drive.minutes > CONSECUTIVE_LONG_DAY_MIN else 0
            if streak == MAX_CONSECUTIVE_LONG_DAYS + 1:
                self._add(WARNING, "pacing", where, f"Day {drive.day_number}: more than {MAX_CONSECUTIVE_LONG_DAYS} consecutive move days over {CONSECUTIVE_LONG_DAY_MIN // 60} h")
        return drives

    def _activities(self, day: dict) -> list[dict]:
        return [
            p for p in self._places(day)
            if p.get("stop_type") not in NOT_ACTIVITY_STOP_TYPES and not self._is_home(_coords(p))
        ]

    def check_activity_rhythm(self) -> None:
        last = len(self.days) - 1
        for index, day in enumerate(self.days):
            count = len(self._activities(day))
            number = day.get("day_number", index + 1)
            if index in (0, last) and count > MAX_ACTIVITIES_ON_TRAVEL_DAY:
                kind = "arrival" if index == 0 else "departure"
                self._add(WARNING, "pacing", f"/days/{index}", f"Day {number} is the {kind} day and has {count} activities (at most {MAX_ACTIVITIES_ON_TRAVEL_DAY})")
            elif (index + 1) % REST_DAY_EVERY == 0 and count > MAX_ACTIVITIES_ON_REST_DAY:
                self._add(WARNING, "pacing", f"/days/{index}", f"Day {number} is a rest-rhythm day (every {REST_DAY_EVERY}th) and has {count} activities (at most {MAX_ACTIVITIES_ON_REST_DAY})")

    # Section 2.5 and 3.3: build gate and call estimate

    def check_skeleton_gate(self) -> tuple[bool, str]:
        confirmed_on = self.driving.get("confirmed_on")
        if self.legacy:
            reason = "v1 plan has no brief.driving_settings; migrate to v2 and confirm settings at checkpoint 0"
        elif not self.settings:
            reason = "brief.driving_settings.settings is empty"
        elif _parse_date(confirmed_on) is None:
            reason = "brief.driving_settings.confirmed_on is empty; Roald has not confirmed this trip's driving settings (checkpoint 0)"
        elif self.driving.get("confirmed_by") != "roald":
            reason = "brief.driving_settings.confirmed_by must be 'roald'"
        else:
            return True, f"driving settings confirmed by roald on {confirmed_on}"
        self._add(ERROR if self.for_skeleton else WARNING, "skeleton gate", "/brief/driving_settings", f"build-trip --skeleton blocked: {reason}")
        return False, reason

    def estimate_calls(self) -> dict[str, int]:
        places = [p for day in self.days for p in self._places(day)]
        service = [p for p in places if p.get("stop_type") in SERVICE_STOP_TYPES]
        counts = {
            "fixed": 4,
            "days × 2": 2 * len(self.days),
            "places × 1.3": math.ceil(1.3 * (len(places) - len(service))),
            "stays × 4": 4 * len(self.stays),
            "service stops": len(service),
            "vias": sum(len(_dicts(d.get("vias"))) for d in self.days),
            "budget rows": len(_dicts(self.plan.get("budget"))),
            "packing items": len(_dicts(self.plan.get("packing"))),
            "todos": len(_dicts(self.plan.get("todos"))),
        }
        counts["total"] = sum(counts.values())
        return counts


def render_markdown(report: Report) -> str:
    errors, warnings = report.errors, report.warnings
    if errors:
        result = f"FAIL ({len(errors)} errors, {len(warnings)} warnings)"
    elif warnings:
        result = f"PASS with {len(warnings)} warnings"
    else:
        result = "PASS"
    lines = [
        f"# Validation: {report.title}",
        "",
        f"- Plan: `{report.plan_path}`",
        f"- Plan id: `{report.plan_id}`",
        f"- Schema: {report.schema_label}",
        f"- Mode: {report.mode}" + (" (driving times are rough estimates)" if report.mode == "estimate" else " (driving times from TREK's calculator)"),
        f"- Result: **{result}**",
        "",
        "## Build gate",
        "",
        f"- `build-trip --skeleton`: {'allowed' if report.skeleton_gate[0] else 'blocked'} ({report.skeleton_gate[1]})",
        "",
    ]
    for heading, findings in (("Errors", errors), ("Warnings", warnings)):
        lines += [f"## {heading}", ""]
        if not findings:
            lines += ["None.", ""]
            continue
        lines += ["| # | Check | Where | Message |", "|---|---|---|---|"]
        for number, finding in enumerate(findings, 1):
            message = finding.message.replace("|", "\\|")
            lines.append(f"| {number} | {finding.check} | `{finding.where}` | {message} |")
        lines.append("")
    lines += ["## Pacing", "", "| Day | Move | Driving min | km | Source |", "|---|---|---|---|---|"]
    for drive in report.drives:
        lines.append(f"| {drive.day_number} | {'yes' if drive.move else 'no'} | {drive.minutes:.0f} | {drive.km:.0f} | {drive.source} |")
    lines += ["", "## Night coverage", ""]
    if report.nights:
        lines += ["| Night after day | Base | Stay |", "|---|---|---|"]
        lines += [f"| {night} | {base} | {stay} |" for night, base, stay in report.nights]
    else:
        lines.append("Not checked.")
    lines += ["", "## Budget", "", "| Category | Rows sum |", "|---|---|"]
    lines += [f"| {category} | {amount:g} |" for category, amount in report.budget_lines]
    rows_sum = sum(amount for _, amount in report.budget_lines)
    headline = "none" if report.budget_total is None else f"{report.budget_total:g}"
    lines += [f"| **All rows** | **{rows_sum:g}** (headline total: {headline}) |", ""]
    lines += ["## Pre-build TREK write estimate", "", "| Part | Calls |", "|---|---|"]
    lines += [f"| {part} | {count} |" for part, count in report.call_estimate.items()]
    lines += ["", "## Checks not run", ""]
    lines += [f"- {reason}" for reason in report.skipped]
    lines.append("")
    return "\n".join(lines)


def validate_file(path: Path, mode: str = "auto", for_skeleton: bool = False) -> Report:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise ValueError("plan JSON must be an object")
    return PlanValidator(plan, str(path), mode, for_skeleton).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", type=Path, help="path to plan.json")
    parser.add_argument("--mode", choices=("auto", "estimate", "trek"), default="auto")
    parser.add_argument("--for-skeleton", action="store_true", help="treat unconfirmed driving settings as an error (gate for build-trip --skeleton)")
    parser.add_argument("-o", "--output", type=Path, help="also write the report to this file, e.g. plans/<slug>/validation.md")
    args = parser.parse_args(argv)
    try:
        report = validate_file(args.plan, args.mode, args.for_skeleton)
    except (OSError, ValueError) as exc:
        print(f"validate_plan: cannot read {args.plan}: {exc}", file=sys.stderr)
        return 2
    markdown = render_markdown(report)
    print(markdown)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
