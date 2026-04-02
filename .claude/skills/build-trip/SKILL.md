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
3. Print a brief summary: trip title, dates, number of days, number of places. Ask the user to confirm before creating.

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

**Step 3 — Add trip details:**
- `create_budget_item` for each entry in the `budget` array
- `create_reservation` for each entry in the `reservations` array; `link_hotel_accommodation` for hotel reservations
- `create_packing_item` for each entry in the `packing` array
- `create_collab_note` for each entry in the `collab_notes` array

### Phase 4 — Present Summary

Present the completed trip with:
- Trip URL on TREK
- Budget breakdown (per person and total)
- Day-by-day highlights (title + number of places)
- Any items that were skipped (already existed) or failed (with error details)

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- **Day 1 MUST start with the departure location** as the first assigned place — never skip this
- Currency comes from the plan JSON — don't override it
- If a `create_place` or other call fails, log the error, continue with the next item, and report all failures at the end
- Budget items: use the `amount` and `notes` from the plan directly
- If the plan has `accommodation` entries on days, create those as places and assign them to the appropriate day
