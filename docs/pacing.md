# Pacing

Thresholds `validate-plan` and `route-check` use to judge whether a day is drivable. Agents may tune them by PR; say which lesson in `docs/lessons/` motivates the change.

Driving times come from TREK's `calculate_roadtrip` (`method: trek` on a leg). The formula estimate below is only the rough check before a skeleton trip exists, and the fallback when the calculator fails twice under the retry rule (`CLAUDE.md`).

## Rules

| Rule | Level | Threshold |
|---|---|---|
| Move day: calculator minutes exceed the trip's `roadtrip_day_minutes` | error | 480 min with Roald's starting values; TREK would pause the day, so a place is unreachable |
| Move day: driving time | warning | over 4 h |
| Consecutive long move days | warning | more than two in a row over 3 h |
| Arrival and departure days | warning | more than one activity |
| Rest rhythm | warning | every fifth day has more than one activity |
| Opening days | warning | a place is closed on the day's weekday (hours from `search_pois`) |
| Stay arrival | warning | calculator arrival after the stay's check-in window |
| Stay distance | warning | stay more than 30 km from the day's calculated end, unless the plan marks it deliberate |
| Routing failure on a day | error | the step stops for that day; usually a place without coordinates |

## Charging and service stops

- EV trips search the corridor for `charging` on days whose calculator output has a fuel warning or whose distance exceeds TREK's charging interval (about 290 km with Roald's starting values, `profile/USER_PROFILE.example.md`).
- `rest_area` is searched on days with a leg over `roadtrip_leg_minutes` (150 min with the starting values).

## Fallback estimate

Used only before the skeleton build or when `calculate_roadtrip` fails twice:

- distance = great-circle distance × 1.3
- speed = 75 km/h
- EVs: one 30-minute charge per 300 km

Legs keep `method: estimate`, and the roadbook says "driving times estimated".

## Baseline from Roald's driving

To be filled in by round 2.4 from trip 11 (Sweden road trip 2026), read-only: `get_trip_summary(11)` and one `calculate_roadtrip(11)` under the retry rule. The result goes here as "Roald drove up to X h on move days and Y h on average", and the thresholds above are then set from it.
