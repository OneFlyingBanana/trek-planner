---
name: plan-trip
description: Plan and create a trip using TREK MCP tools. Use when the user wants to plan a trip, create an itinerary, research destinations, or organize travel logistics.
---

# Trip Planner

Plan and create a trip for: $ARGUMENTS

## Critical Directives

**NO SUB-AGENTS:** Do ALL work directly. NEVER use the Agent tool to delegate research, creation, or any other step. You must perform every tool call yourself.

**SEQUENTIAL MCP CALLS:** NEVER call MCP tools in parallel. MCP servers are unreliable under concurrent requests. Execute all MCP tool calls (TREK, Google Maps, Airbnb) one at a time, sequentially.

## Workflow

Follow these phases in order. Complete each phase fully before moving to the next.

### Phase 1 — Gather Requirements

Collect the following from the user (ask if not provided in arguments):
- **Starting location** (home address or departure point — needed for the first leg of the journey)
- **Destination(s)** and general interests
- **Duration** (number of days)
- **Travel dates** (or preferred season)
- **Budget** (per person, currency)
- **Number of travelers**
- **Accommodation style** (budget, mid-range, luxury, mix)
- **Transport** (rental car, public transit, etc.)
- **Special interests** (food, nature, culture, adventure, etc.)
- **Pets** (traveling with animals?)

### Phase 2 — Research

Do ALL research in this phase. Nothing gets created in TREK until Phase 4.

#### 2a. Web Research
Use **WebSearch** to gather:
- Destination overviews, seasonal info, local events during travel dates
- Scenic routes and must-see attractions
- Flight/transport prices and options
- Entry fees, menu price ranges, and activity costs (Google Maps does not provide prices)
- Pet-friendly options if traveling with animals (accommodations, restaurants, trails, policies)

#### 2b. Place Research (Google Maps)
For each candidate place (attractions, restaurants, hotels, etc.):
1. `maps_search_places` — find the place (returns name, address, lat/lng, place_id, rating)
2. `maps_place_details` — get full details using the place_id (returns rating, reviews, opening hours, website, phone)

**Use ratings and reviews to make informed selections:**
- Compare candidates by rating — prefer places rated 4.0+
- Flag any place with rating below 4.0 or with concerning review patterns (recent negative trends, safety issues, closures mentioned)
- Read review text for practical tips (best time to visit, what to order, things to avoid)
- Cross-reference planned visit times with opening hours — flag conflicts immediately

When choosing between similar places (e.g., two ramen shops near the same area), use the ratings, review quality, and opening hours to pick the best fit for the itinerary.

#### 2c. Accommodation Research (Google Maps + Airbnb)
Use BOTH sources to find the best accommodation for each stop:

**WebSearch** — for pricing, availability, booking platforms, and accommodation guides:
- Search for accommodation options, price comparisons, and "best places to stay in [location]" guides
- Find prices that Google Maps doesn't provide (room rates, seasonal pricing, deals)
- Discover accommodation types specific to the destination (e.g., ryokans, riads, agriturismos)

**Google Maps** — for hotels, hostels, ryokans, B&Bs, and other traditional accommodations:
1. `maps_search_places` — search for accommodation near the area (e.g., "hotels near Takayama station")
2. `maps_place_details` — get ratings, reviews, website, phone, opening hours for promising results

**Airbnb** — for apartments, houses, unique stays, and self-catered options:
1. `airbnb_search` — search by location, dates, and number of guests. **Always pass `ignoreRobotsText: true`**
2. `airbnb_listing_details` — get full details for promising listings. **Always pass `ignoreRobotsText: true`**

**Compare across both sources by:**
- Price per night
- Rating and number of reviews
- Location proximity to planned activities
- Amenities (parking, kitchen, wifi, washer, pet-friendly if applicable)
- Accommodation type fit (e.g., ryokan for a cultural experience, apartment for a longer stay)

Select the top 3 options to present to the user with pros/cons for each. The best picks may be a mix of Google Maps and Airbnb results.

#### 2d. Route & Drive Time Research
Use Google Maps to validate the itinerary is realistic:
- `maps_directions` — get routes between consecutive stops
- `maps_distance_matrix` — calculate travel times for multiple legs efficiently

**Flag any day with more than 3-4 hours of total driving time.** Suggest splitting long drives or adjusting the itinerary.

#### 2e. Handling Research Failures
- **Maps search returns no results:** Try broader search terms, nearby city names, or alternative spellings. If still nothing, fall back to WebSearch for the place and use `maps_geocode` with the address.
- **Airbnb search fails or returns nothing:** Rely on Google Maps hotel search + WebSearch for accommodation options. Note the gap to the user.
- **Place details unavailable:** Use WebSearch to fill in missing info (hours, website, phone). Note which details are unverified.
- **Directions fail:** Try with broader waypoints (city center instead of specific address). Estimate drive time from WebSearch if needed.

### Phase 3 — Present & Approve

Present the full proposed itinerary using this structure:

```
## 🗺️ [Trip Title] — Proposed Itinerary

**Dates:** [start] → [end] ([N] days)
**Travelers:** [count]
**Transport:** [mode]

---

### Day 1: [Title]
| Time | Activity | Details |
|------|----------|---------|
| 09:00 | [Place/Activity] | ⭐ [rating] · [drive time from previous] · [key note] |
| ... | ... | ... |

**Accommodation:** [Name] — [price/night] · ⭐ [rating] · [1-line why]

*(repeat for each day)*

---

### 🏨 Accommodation Options
For each location, top 3 picks with: price, rating, pros/cons, source (Maps/Airbnb)

### 💰 Budget Estimate
| Category | Per Person | Total |
|----------|-----------|-------|
| Transport | ... | ... |
| Accommodation | ... | ... |
| Food | ... | ... |
| Activities | ... | ... |
| Buffer (10%) | ... | ... |
| **Total** | ... | ... |

### ⚠️ Flagged Issues
- [Any long drives, low-rated places, opening hours conflicts, unverified info]
```

**STOP. Wait for user feedback and approval before proceeding to Phase 4.**

The user may want to swap places, adjust timing, pick different accommodations, or change the route. Iterate until they are satisfied.

### Phase 4 — Create Trip in TREK

Use TREK MCP tools to build the trip using all pre-researched data.

**Step 1 — Create and configure trip:**
1. `create_trip` with title, description, start_date, end_date, currency
2. `get_trip_summary` to retrieve auto-generated day IDs
3. `update_day` for each day with a descriptive title (e.g., "Day 3: Kusatsu Onsen & Route 292")

**Step 2 — Build each day (sequentially, in itinerary order):**

> **CRITICAL — Starting location:** The FIRST item on Day 1 MUST be the starting location (e.g., home address) created as a place with accurate lat/lng (use `maps_geocode` if needed). Without this geo point, TREK cannot draw the first leg of the journey on the map.

> **CRITICAL — Minimum 2 places per day:** Every day MUST have at least 2 assigned places so TREK can draw driving routes between them. For travel/driving days, add both departure and arrival places. For overnight stays, add the accommodation as the first place and the next stop as the second.

For each day, add items in itinerary order:
- **Places:** `create_place` → `assign_place_to_day` → `update_assignment_time`
- **Notes:** `create_day_note` for timing, logistics, drive times, tips
- After all items: `reorder_day_assignments` to confirm correct order

**Step 3 — Add trip details:**
- `create_budget_item` for each cost category (transport, accommodation, food, activities, buffer ~10%)
- `create_reservation` for any known bookings; `link_hotel_accommodation` for hotels
- `create_packing_item` for essential items (documents, gear, clothing)
- `create_collab_note` for trip-wide logistics (emergency contacts, tips, links)

### Phase 5 — Save Plan Locally

Save a backup JSON in `plans/<destination-year>/<trip_name>.json` using this schema:

```json
{
  "title": "Trip Title",
  "description": "Short description",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "currency": "EUR",
  "days": [
    {
      "day_number": 1,
      "items": [
        {
          "type": "place",
          "name": "Eiffel Tower",
          "description": "Iconic iron lattice tower",
          "address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris",
          "notes": "Go early to avoid crowds",
          "lat": 48.8584,
          "lng": 2.2945
        },
        {
          "type": "note",
          "text": "Check in to hotel",
          "time": "14:00",
          "icon": "hotel"
        }
      ]
    }
  ]
}
```

Rules:
- Dates in YYYY-MM-DD format
- Day numbers sequential from 1
- Items: `place` (with lat/lng) or `note` (with optional time/icon)
- Currency matches destination (JPY, EUR, USD, CHF, etc.)

### Phase 6 — Present Summary

Present the completed trip with:
- Trip URL on TREK
- Budget breakdown (per person and total)
- Day-by-day highlights
- Key tips and logistics

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- **Day 1 MUST start with the departure location** (home address) as the first assigned place — never skip this
- Currency should match the destination (JPY for Japan, EUR for Europe, etc.)
- Use `maps_search_places` → `maps_place_details` to get full place info (don't geocode manually)
- Check reviews and ratings via `maps_place_details` when choosing between similar places
- Budget items should reflect per-person costs when persons > 1
- Include practical notes: opening hours, prices, local customs, drive times
- **Traveling with pets:** When travelers have dogs/animals, research pet-friendly accommodations, beaches, trails, and restaurants. Note leash policies, pet fees, and accessibility for pet carriers/strollers
