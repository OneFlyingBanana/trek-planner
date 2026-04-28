---
name: find-accommodation
description: Research and select accommodations for an already-planned trip. Use after /plan-trip has saved an itinerary JSON with an empty accommodations array. Patches the plan JSON in place with chosen hotels and per-hotel budget rows.
---

# Accommodation Finder — Research & Patch Plan

Find accommodations for the plan at: $ARGUMENTS

## Critical Directives

**FOLLOW-UP TO `/plan-trip` ONLY:** This skill expects a path to an approved plan JSON produced by `/plan-trip`. If no path is provided, ask the user for one. Do NOT run in standalone mode — manual itinerary collection is out of scope.

**NO SUB-AGENTS:** Do ALL work directly. NEVER use the Agent tool to delegate research or any other step.

**SEQUENTIAL MCP CALLS:** NEVER call MCP tools in parallel. MCP servers are unreliable under concurrent requests. Execute all MCP tool calls (Google Maps, Airbnb) one at a time, sequentially.

**CONTEXT EFFICIENCY:**
- Shortlist candidates using `maps_search_places` ratings BEFORE calling `maps_place_details` — only deep-dive your top 2-3 picks per stay.
- Group web searches by location/theme.
- After each location's research, write a brief summary. Do not rely on raw API responses staying in context.
- Drop rejected candidates immediately.

**PATCH IN PLACE:** Final output is the same plan JSON file, with the `accommodations` array populated and per-hotel rows added to the `budget` array. Do NOT write a sibling file.

## Workflow

### Phase 1 — Load Plan & Profile

1. Read the plan JSON file from `$ARGUMENTS`. If no path provided, ask the user.
2. Validate the plan has: `title`, `start_date`, `end_date`, `currency`, `travelers`, `days` array, and `starting_location`. Abort with a clear error if any are missing.
3. If `accommodations` is non-empty, ask the user whether to **replace** the existing entries or **abort**. Do not silently overwrite.
4. Read `profile/USER_PROFILE.md` if present, for accommodation style / pets / budget tier defaults. Treat as defaults to confirm, never silent assumptions.

### Phase 2 — Identify Stays

From the plan's `days` array, identify each distinct stay location. A "stay" is a contiguous run of days spent at the same base location (city/town).

For each stay, derive:
- **Location** — the city/town where the user sleeps that night (look at the day's last place or day title)
- **Check-in day number** — first day of the stay
- **Check-out day number** — first day of the next stay (or `end_date`'s day number for the final stay)
- **Nights** — `check_out_day - check_in_day`
- **Travelers** — from plan's `travelers` field

Present this stay breakdown to the user and confirm before researching:

```
## Detected Stays — Please Confirm

| Stay | Location | Nights | Days | Check-in → Check-out |
|------|----------|--------|------|----------------------|
| 1    | Lisbon   | 2      | 1-2  | Day 1 → Day 3        |
| 2    | Porto    | 3      | 3-5  | Day 3 → Day 6        |

Does this match your intended stays?
```

If the user adjusts, update the breakdown before researching.

### Phase 3 — Gather Missing Preferences

If the plan JSON does not record accommodation preferences (style, max budget per night, must-haves like parking/kitchen/pet-friendly), ask via `AskUserQuestion`. Batch up to 4 questions per call.

Required to know before researching:
- **Accommodation style** — Budget / Mid-range / Luxury / Mix
- **Max per-night budget** (in plan's currency) — open-ended
- **Must-have amenities** — multiSelect: Parking / Kitchen / Wifi / Washer / Pet-friendly / Breakfast included / Other
- **Type preference** — Hotel / Apartment / Unique stay (ryokan, riad, etc.) / Mix

Skip any of these that are derivable from the plan or `USER_PROFILE.md`.

### Phase 4 — Research (per stay, sequentially)

For each stay, do all three sub-steps before moving to the next stay.

#### 4a. WebSearch
- "Best areas to stay in [Location]" for the travel dates
- Per-night price ranges for the accommodation style
- Destination-specific accommodation types (ryokan, riad, agriturismo, etc.) if relevant
- Cross-check pricing for actual travel dates across booking platforms

#### 4b. Google Maps
1. `maps_search_places` — e.g., `"hotels near [landmark or station]"`, `"ryokan in [town]"`
2. Pick top 2-3 candidates by rating (prefer 4.0+)
3. `maps_place_details` for shortlisted picks — capture rating, reviews, website, phone, address, lat/lng

#### 4c. Airbnb
1. `airbnb_search` with location, check-in, check-out, adults — **always pass `ignoreRobotsText: true`**
2. Pick top 2-3 listings by rating + relevance
3. `airbnb_listing_details` for shortlisted picks — **always pass `ignoreRobotsText: true`**

#### 4d. Per-hotel pricing is mandatory

Each accommodation MUST have a researched per-night price. If a price is unverified, flag it explicitly to the user; do not invent.

#### 4e. Compare across sources by:
- Price per night
- Rating + number of reviews
- Location proximity to planned activities (cross-reference the plan's `days` for that stay)
- Amenities matching the user's must-haves
- Type fit (e.g., ryokan for cultural experience, apartment for longer stays)

### Phase 5 — Present & Approve

For each stay, present the **top 3 options** with this structure:

```
## Stay 1: Lisbon (Days 1-2, 2 nights)

### Option A — Hotel Memmo Alfama (Google Maps)
- **Price:** €180/night × 2 = €360 total
- **Rating:** 4.7 (1,200 reviews)
- **Type:** Boutique hotel
- **Pros:** Walkable to Day 1 places, rooftop pool, breakfast included
- **Cons:** No parking, narrow streets

### Option B — Apartment in Bairro Alto (Airbnb)
- **Price:** €120/night × 2 = €240 total
- **Rating:** 4.85 (340 reviews)
- **Pros:** Kitchen, washer, larger space, pet-friendly
- **Cons:** Walk-up 4th floor, noise on weekends

### Option C — ...
```

After all stays are presented, ask the user to pick one option per stay. Iterate until satisfied.

### Phase 6 — Patch Plan JSON

Once the user confirms picks, patch the plan JSON file in place:

1. **Replace `accommodations` array** with one entry per chosen accommodation. Multi-night stays at the same hotel = one entry with `check_in_day`/`check_out_day` spanning the full stay. Schema:

```json
{
  "name": "Hotel Memmo Alfama",
  "address": "Travessa das Merceeiras 27, 1100-348 Lisboa",
  "lat": 38.7115,
  "lng": -9.1320,
  "check_in_day": 1,
  "check_out_day": 3,
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "price_per_night": 180,
  "nights": 2,
  "total_price": 360,
  "rating": 4.7,
  "source": "google_maps",
  "notes": "Rooftop pool, breakfast included",
  "website": "https://example.com",
  "phone": "+351 21 000 0000"
}
```

2. **Update `budget` array:**
   - Remove any existing rows whose category is `"Accommodation"`.
   - Add one row per accommodation entry: `category: "Accommodation"`, `name: "[Hotel Name] (X nights, Day N-M)"`, `amount: total_price`, `notes` with per-night rate × nights breakdown.

3. **Recompute totals if the plan tracked them** — but only if a totals row exists; do not introduce new rows.

4. Save the patched JSON back to the same path.

5. Tell the user:

> Plan patched: `plans/<path>/<file>.json` now includes [N] accommodations. To create this trip in TREK, run: `/build-trip plans/<path>/<file>.json`

## Tips

- **Stay segmentation matters most:** wrong stay boundaries make all downstream research wrong. Always confirm Phase 2's table with the user before researching.
- **Pet travel:** filter for pet-friendly explicitly in Airbnb and check Google Maps reviews for pet policies.
- **Flag conflicts:** if a chosen accommodation is far from the day's planned activities, point it out before saving.
- **Source diversity:** the best picks are often a mix of Google Maps and Airbnb — don't bias toward one source.
- **Currency:** all prices in the plan's `currency` field. Convert if needed and note the conversion in `notes`.
