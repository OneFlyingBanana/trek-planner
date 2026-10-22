# Call budgets

Limits per trip or per build pass. Each skill repeats the limits it is bound by; `validate-plan`'s pre-build estimate uses them so the build report can show planned against actual. Agents may tune them by PR, except the Google cap, which is Roald's.

| Budget | Limit | Reason |
|---|---|---|
| Google-billed calls per trip (`search_place` with `provider: "google"`, `get_place_details`) | at most 1 per final place + 1 per stay; hard cap 60 (agreed by Roald) | billed to Roald; only when needed, never in a loop |
| `get_place_details` with `expand: true` | 0 unless Roald asks for reviews | Enterprise SKU |
| `preview_google_maps_route` | 1 per link in the brief, at most 8 stops per link | does not use the Google key; TREK's Nominatim fallback geocodes about one stop per second, so long links can pass the 10 s cut |
| `import_google_maps_route` | 1 per day, at most 8 stops | same geocoding limit |
| `search_pois` | at most 2 per base (one call, several categories) | free, but large payloads |
| `calculate_roadtrip` | at most 3 per build pass (after skeleton, after route-check, final), each with one retry | cold calls on long trips exceed the 10 s gateway cut; the warm retry is fast |
| `search_roadtrip_corridor` | at most 3 pages per day per category | paged six rectangles at a time; free of Google |
| `lookup_roadtrip_charging_info` | 1 per chosen charger | |
| `get_roadtrip_hazards` | 1 per route-check, 1 at roadbook time | current notices only, not forecasts |
| TREK write calls per build | about 4 + days × 2 + places × 1.3 + stays × 4 + service stops + vias + budget rows + packing + todos | report the estimate before building |
| WebFetch per stay | at most 4 (official site, one or two booking pages, one review page) | context |

Discovery uses OSM (`search_pois`, `search_place` without `provider`), Roald's Collections and the corridor search. Google only confirms final picks; candidate lists never go through Google.

Every retry under the rule in `CLAUDE.md` counts against the budget of the call it repeats.
