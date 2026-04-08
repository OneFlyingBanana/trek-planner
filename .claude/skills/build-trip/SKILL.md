---
name: build-trip
description: Build a pre-planned trip in TREK from a plan JSON file. Use after /plan-trip has created and saved an approved itinerary.
---

# Trip Builder — Create in TREK

Build a trip in TREK from: $ARGUMENTS

## Critical Directives

**NO SUB-AGENTS:** Do ALL work directly. NEVER use the Agent tool to delegate any step. You must perform every tool call yourself.

**SEQUENTIAL MCP CALLS:** NEVER call MCP tools in parallel. MCP servers are unreliable under concurrent requests. Execute all MCP tool calls one at a time, sequentially.

**NO RESEARCH:** This skill does NOT research. All data comes from the plan JSON. If the plan JSON is missing critical data (like lat/lng for a place), flag it to the user rather than doing research.

## Workflow

### Phase 1 — Load & Validate Plan

1. Read the plan JSON file from the path provided in $ARGUMENTS. If no path is provided, ask the user.
2. Validate the plan has all required fields:
   - `title`, `start_date`, `end_date`, `currency`
   - `starting_location` with `lat` and `lng`
   - `days` array with at least one day
   - Each place item has `lat` and `lng`
   - `accommodations` array with at least one entry (each with `check_in_day`, `check_out_day`, lat/lng)
   - `budget` array with entries
3. Present a detailed summary and **wait for user confirmation before creating anything**:

```
## Ready to Build — Please Confirm

**Trip:** [title]
**Dates:** [start] → [end] ([N] days)
**Currency:** [X]
**Places:** [N] across [N] days
**Accommodations:** [N] hotels covering [N] nights
**Budget:** [total] ([per person] per person)

Accommodation coverage:
- Night 1-2: Hotel Name
- Night 3: Other Hotel
- ...

Proceed with building this trip in TREK?
```

**DO NOT proceed to Phase 2 until the user confirms.**

### Phase 2 — Check for Existing Trip (Recovery)

Before creating anything, check if this trip already exists:
1. `list_trips` — look for a trip with a matching title
2. If found: `get_trip_summary` to see what's already been created
3. Compare existing trip state against the plan JSON:
   - Which days have titles set?
   - Which places already exist and are assigned?
   - Which budget items, packing items, and notes exist?
4. Report to the user what already exists and what still needs to be created
5. Skip items that already exist; create only what's missing

If no existing trip is found, proceed with full creation.

### Phase 3 — Create Trip in TREK

Use TREK MCP tools to build the trip using data from the plan JSON.

**Step 1 — Create and configure trip:**
1. `create_trip` with title, description, start_date, end_date, currency
2. `get_trip_summary` to retrieve auto-generated day IDs
3. `update_day` for each day with the title from the plan JSON

**Step 2 — Build each day (sequentially, in itinerary order):**

> **CRITICAL — Starting location:** The FIRST item on Day 1 MUST be the starting location from `starting_location` in the plan JSON, created as a place with accurate lat/lng. Without this geo point, TREK cannot draw the first leg of the journey on the map.

> **Minimum 2 places per day (when traveling):** Any day that involves moving between locations MUST have at least 2 assigned places so TREK can draw driving routes between them. For travel/driving days, add both departure and arrival places. **Exception:** Rest days or days spent entirely in one location (e.g., beach day, resort day, city exploration on foot) can have just 1 place — TREK will show a map marker without a route line, which is correct for stationary days.

For each day, add items in itinerary order:
- **Places:** `create_place` (with name, description, address, lat, lng, website, phone from plan) → `assign_place_to_day` → `update_assignment_time` (with time_start/time_end from plan)
- **Notes:** `create_day_note` for each note item in the plan
- After all items: `reorder_day_assignments` to confirm correct order

**Step 3 — Create accommodations and link to days:**

For each entry in the plan's `accommodations` array:

1. `search_place` to find the Google Place ID for the hotel
2. `create_place` with name, description, address, lat, lng, google_place_id, website, phone, **category_id=1** (Hotel)
3. `assign_place_to_day` on the **check-in day** — hotel appears as the last place (where you arrive in the evening)
4. `assign_place_to_day` on the **check-out day** — hotel needs to be the first place (where you depart from in the morning)
5. `reorder_day_assignments` on the **check-out day** to move the hotel assignment to position 0 (first)
6. `create_reservation` with:
   - `type: "hotel"`
   - `place_id` from step 2
   - `start_day_id` (check-in day ID) and `end_day_id` (check-out day ID) — this auto-creates the accommodation link in TREK
   - `check_in` and `check_out` times from the plan
   - `notes` with pricing and booking info

**Important:**
- Do NOT assign hotels to intermediate days of multi-night stays (e.g., for a 3-night stay on days 9-11, only assign to day 9 and day 12)
- The check-out day assignment + reorder ensures each day shows the correct start/end driving points on the TREK map
- Skip step 4-5 for the last accommodation if its check-out day is the departure day and the departure airport is already assigned as the first place

**Step 4 — Add remaining trip details:**
- `create_budget_item` for each entry in the `budget` array. Use the `name` field from the plan for clear per-item descriptions (e.g., "Hotel Kajikaso (2 nights, Nov 3-4)" instead of generic "Accommodation").
- `create_reservation` for each non-hotel entry in the `reservations` array (flights, restaurants, etc.)
- `create_packing_item` for each entry in the `packing` array
- `create_collab_note` for each entry in the `collab_notes` array

### Phase 4 — Present Summary

Present the completed trip with:
- Trip URL on TREK
- **Accommodation coverage:** Verify every night has a linked accommodation (use `get_trip_summary` to confirm). Flag any gaps.
- Budget breakdown (per person and total)
- Day-by-day highlights (title + number of places + accommodation for that night)
- Any items that were skipped (already existed) or failed (with error details)

### Phase 5 — Offer Route Detailing (Driving Trips Only)

**Skip this phase entirely if the trip does not involve driving** (e.g., public transit, flights only, city walks).

If the trip involves driving between locations (rental car, road trip, etc.), offer the user the option to add detailed waypoints along driving segments. This makes TREK show a step-by-step route through scenic stops instead of just start/end points.

Present this to the user:

> **Route detailing available:** This trip has driving segments that could benefit from detailed waypoints (viewpoints, scenic stops, roadside stations) along each route. This helps TREK show the exact path you'll drive.
>
> To add detailed route waypoints, paste this prompt into a fresh conversation:

Then generate a handoff prompt using this template (fill in the actual values):

~~~
I need you to add detailed driving waypoints to my trip in TREK.

**Trip ID:** [trip_id]
**Plan file:** [path to plan JSON]

Load the trip with `get_trip_summary` (trip ID [trip_id]) to see the current state. For each driving segment between stops, research whether there are notable waypoints DIRECTLY ON THE ROUTE (viewpoints, scenic stops, roadside stations, landmarks) that would add value. Only add stops you are confident are on the route — no detours unless flagged as such.

For each waypoint found:
1. `create_place` with accurate name, description, lat/lng, google_place_id, and category
2. `assign_place_to_day` to the correct day
3. `update_assignment_time` with realistic times
4. Update the day note to reflect the new stops

Skip segments that are:
- Short urban drives (under 30 min)
- Already have detailed waypoints
- Flat expressway with no scenic alternative

Focus on segments where stops genuinely improve the route visibility on the map and the driving experience.
~~~

**Do not perform the route detailing yourself.** The research is context-heavy and best handled in a fresh conversation that can dedicate its full context to it.

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- **Day 1 MUST start with the departure location** as the first assigned place — never skip this
- Currency comes from the plan JSON — don't override it
- If a `create_place` or other call fails, log the error, continue with the next item, and report all failures at the end
- Budget items: use the `amount` and `notes` from the plan directly
- Accommodations are in the top-level `accommodations` array (not per-day) — see Step 3 for the full creation flow
