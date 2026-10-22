# Plan fixtures

Three plan files that exercise `schema/plan.v2.schema.json` (design ISD-4, sections 2.5, 4.3, 5.2) and, from round 1.2b on, `scripts/validate_plan.py`.

| File | Expected result against the v2 schema | Used by |
|---|---|---|
| `valid-3day-polestar.json` | valid | the standing `[paperclip] fixture` trip (1.5, 1.5b, 1.6); validator happy path |
| `legacy-v1.json` | invalid (it is a v1 plan) | validator "accept v1 with warnings" path |
| `broken-v2.json` | invalid, many errors | validator error path; every defect listed below |

Check them with any JSON Schema draft-07 tool, for example:

```bash
npx --yes ajv-cli@5 validate -s schema/plan.v2.schema.json -d tests/fixtures/plans/valid-3day-polestar.json
npx --yes ajv-cli@5 validate -s schema/plan.v2.schema.json -d tests/fixtures/plans/broken-v2.json --all-errors --errors=text
```

## valid-3day-polestar.json

Chamoson → Château de Chillon → Annecy (night 1) → Sallanches → Mer de Glace → Chamonix (night 2) → Aiguille du Midi → Martigny → Chamoson. Own car, the Polestar 2.

- `brief.driving_settings.settings` holds the Polestar starting values from design 5.2, copyable as the `settings` argument of `update_roadtrip_settings`. `confirmed_on` is `2026-10-22` and `confirmed_by` is `roald`: Roald's approval of design revision 4 counts as the checkpoint 0 confirmation for this fixture only (design section 9, assumption 4). No other plan may copy that confirmation.
- Coordinates and prices are approximate and were not looked up in TREK or on the web. The skeleton build pins places with `search_place`; prices are marked `estimated`. The fixture tests the pipeline, not the trip.
- Legs are `method: estimate`. After route-check they become `method: trek` with `arrival` set.
- Budget rows sum to `budget_total.amount` (968 CHF).

## legacy-v1.json

The shape `/plan-trip` wrote before this schema: `schema_version: 1`, `accommodations[]`, no `plan_id`, `trek_title`, `brief`, item ids, `base`, `move`, `basis` or `confidence`. ajv reports exactly those missing fields. The validator (1.2b) must accept this file with warnings and must not treat it as broken.

## broken-v2.json

Every defect and the schema rule that catches it:

| Path | Defect | Rule |
|---|---|---|
| `/` | both `stays` and `accommodations` present | top-level `not` |
| `/` | `unknown_top_level_field` | `additionalProperties: false` |
| `/plan_id` | `"Broken Fixture"` | slug pattern |
| `/trek_title` | missing `[paperclip] ` prefix | pattern |
| `/start_date` | `2026-5-15` | date pattern |
| `/currency` | lower case | `^[A-Z]{3}$` |
| `/travelers` | 0 | minimum 1 |
| `/starting_location` | no `lng` | required |
| `/brief/pace` | `relaxed` | enum |
| `/brief/vehicle` | no `ev` | required |
| `/brief/sources/travelers` | `guess` | enum profile/issue/answer |
| `/brief/driving_settings/settings` | `roadtrip_range` (unknown key), `roadtrip_vehicle: ev`, `roadtrip_fill_percent: 120`, `roadtrip_day_start: 9:00`, `roadtrip_avoid: tolls` | mirror of the TREK tool argument |
| `/brief/driving_settings/confirmed_on` | `""` | null or date |
| `/brief/driving_settings/confirmed_by` | `agent` | null or `roald` |
| `/days/0/base` | no `lng` | required |
| `/days/0/move` | `"yes"` | boolean |
| `/days/0/items/0` | id `p1`, `stop_type: castle`, `origin: guess`, empty `source` | item id pattern, enums, `minProperties` |
| `/days/0/items/1` | place without `id`, `lng`, `origin` | required |
| `/days/0/items/2` | note without `text` | required |
| `/days/0/legs/0` | `method: trek` without `arrival` | `if/then` |
| `/days/0/legs/1` | `km: -5`, `method: google` | minimum, enum |
| `/days/0/vias/0` | no `reason` | required |
| `/stays/0` | no `total_price`, `check_out_day` 1, `nights` 0, `confidence: guessed`, bare `price_source_url` | required, minimums, enum, URL pattern |
| `/transport/0` | `source: pdf` without `source_file`, lower-case IATA code, empty `to` | `if/then`, pattern, `anyOf` |
| `/budget/0` | category `Hotels`, negative amount, no `basis` or `confidence` | enum, minimum, required |
| `/budget_total/amount` | string | type |

What the schema cannot see and the validator (1.2b) must check: night coverage, Day 1 starting at `starting_location`, two places on `move` days, budget rows summing to `budget_total`, leg ids pointing at items of the same day, and `confirmed_on` being set before `build-trip --skeleton`.
