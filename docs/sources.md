# Sources

Where research and accommodation data come from, and Roald's decisions on each. Do not re-propose a source marked "not used" without a new decision from Roald.

## Decisions

| Source | Status | Decided | Note |
|---|---|---|---|
| Airbnb | not used | Roald, 2026-10-21 | "We won't use Airbnb anymore." No Airbnb server, connection or scraping; no robots override. |
| AirTrail (flights) | not used | Roald, 2026-10-21 | The addon is being removed. Flights come from the brief text or an attached booking PDF (`pdfcraft-cli text`). |
| Dawarich (location history) | not used | Roald, 2026-10-21 | The addon is being removed. Pacing baselines come from `get_trip_summary` and `calculate_roadtrip`. |
| Google Maps via TREK | allowed, billed | Roald, 2026-10-21 | Final picks only; hard cap 60 calls per trip (`docs/call-budgets.md`). |
| `preview_google_maps_route` | allowed, free | Roald, 2026-10-21 | Does not use the Google key; at most 8 stops per link. |

The `find-accommodation` skill still names Airbnb tools; it is replaced by `find-stays` in round 2.

## Accommodation sources, in order

| Source | Tool | What it gives | Cost |
|---|---|---|---|
| Roald's saved lists | `find_place_in_collections`, `get_collection`, `copy_collection_places_to_trip` | stays he already picked out, with his ratings | free |
| OSM hotels, guest houses, campsites | `search_pois`, `search_roadtrip_corridor` | name, website, phone, position on the actual road | free |
| Official sites and aggregators | WebFetch | price for the exact dates, cancellation terms | free, fragile |
| Google rating and website for the pick | `get_place_details` | rating, review count, website, hours | billed, 1 per pick |
| TREK plugins | `search_places_via_plugins` | whatever providers Roald has enabled in TREK | depends on plugin |

A price is `quoted` only if it was read from a fetched page that showed the trip dates; otherwise it is `estimated`. An unpriced candidate can be a runner-up, never the recommendation. Record the source URL and the date checked with every price.

## Research sources

| Need | Tool | Cost |
|---|---|---|
| Places, opening hours, website, phone, EV sockets | `search_pois` | free (OSM) |
| Coordinates and ids | `search_place` without `provider`, always with `locationBias` | free |
| Final pick missing in OSM | `search_place` with `provider: "google"` | billed |
| Hours or rating for a final pick | `get_place_details` without `expand` | billed |
| Public transport | `search_transit_routes` | free |
| Airports | `search_airports` | free |
| Weather inside the forecast window | `get_weather`, `get_detailed_weather` | free |
| Background, seasons, prices | WebSearch, WebFetch | free |
