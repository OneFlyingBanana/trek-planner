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
1. `airbnb_search` — search by location, dates, and number of guests
2. `airbnb_listing_details` — get full details for promising listings

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

### Phase 3 — Present & Approve

Present the full proposed itinerary to the user, including:
- **Day-by-day plan** with selected places, times, and drive times between stops
- **Place selections** with ratings, review highlights, and opening hours
- **Accommodation options** (top 3 per location with price/rating/pros-cons)
- **Budget estimate** broken down by category
- **Flagged issues** (long drives, low-rated places, opening hours conflicts, missing info)

**STOP. Wait for user feedback and approval before proceeding to Phase 4.**

The user may want to swap places, adjust timing, pick different accommodations, or change the route. Iterate until they are satisfied.

### Phase 4 — Create Trip in TREK

Use TREK MCP tools in this order, using all the data gathered in Phase 2:

**Step 1 — Create trip:**
- `create_trip` with title, description, start_date, end_date, currency

**Step 2 — Get trip context:**
- `get_trip_summary` to retrieve the trip with auto-generated day IDs

**Step 3 — Set day titles:**
- `update_day` to give each day a descriptive title (e.g., "Day 3: Kusatsu Onsen & Route 292")

**Step 4 — Build each day (places and notes in order):**

Process each day sequentially. For each day, add items in itinerary order.

> **CRITICAL — Starting location:** The FIRST item on Day 1 MUST be the starting location (e.g., home address) created as a place with accurate lat/lng (use `maps_geocode` if needed). Without this geo point, TREK cannot draw the first leg of the journey on the map — the route would start at the first destination instead of where the traveler actually departs from. This is a non-negotiable step.

- For **places**:
  1. `create_place` with all pre-researched data (name, address, lat, lng, website, phone, description)
  2. `assign_place_to_day` to link to the current day
  3. `update_assignment_time` to set visit start/end times
- For **notes** (timing, logistics, drive times, tips):
  - `create_day_note` with text, time, and icon

After all items for a day are added:
- `reorder_day_assignments` to confirm the correct order within the day

**Step 5 — Add budget items:**
- `create_budget_item` for each cost category:
  - Transport (flights, car rental, fuel, tolls)
  - Accommodation (hotels, Airbnb, hostels)
  - Food & drinks
  - Activities & attractions
  - Miscellaneous & buffer (~10%)

**Step 6 — Add reservations (if known):**
- `create_reservation` for flights, hotels, restaurants, activities
- `link_hotel_accommodation` to connect hotel reservations to check-in/check-out days

**Step 7 — Create packing list:**
- `create_packing_item` for essential items (documents, gear, clothing, etc.)

**Step 8 — Add collaborative notes:**
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

## TREK MCP Tools Reference (34 tools)

### Trip Management
| Tool | Description |
|:---|:---|
| `create_trip` | Create a new trip (returns trip with generated days) |
| `update_trip` | Update trip details |
| `delete_trip` | Delete a trip (owner only) |
| `list_trips` | List all trips you own or are a member of |
| `get_trip_summary` | Full denormalized trip summary in one call |

### Places & Locations
| Tool | Description |
|:---|:---|
| `create_place` | Add a place/POI to a trip |
| `update_place` | Update an existing place |
| `delete_place` | Remove a place from a trip |

### Day Assignments
| Tool | Description |
|:---|:---|
| `assign_place_to_day` | Assign a place to a specific day |
| `unassign_place` | Remove a place from a day |
| `reorder_day_assignments` | Reorder places within a day |
| `update_assignment_time` | Set start/end time for a place visit |
| `update_day` | Set a day's title |

### Budget
| Tool | Description |
|:---|:---|
| `create_budget_item` | Add a budget/expense item |
| `update_budget_item` | Update a budget item |
| `delete_budget_item` | Remove a budget item |

### Packing
| Tool | Description |
|:---|:---|
| `create_packing_item` | Add item to packing checklist |
| `update_packing_item` | Rename or recategorize a packing item |
| `toggle_packing_item` | Check/uncheck a packing item |
| `delete_packing_item` | Remove a packing item |

### Reservations
| Tool | Description |
|:---|:---|
| `create_reservation` | Add a reservation (flight, hotel, restaurant, etc.) |
| `update_reservation` | Update a reservation |
| `delete_reservation` | Remove a reservation |
| `link_hotel_accommodation` | Link hotel to check-in/check-out days |

### Notes
| Tool | Description |
|:---|:---|
| `create_day_note` | Add a note to a specific day |
| `update_day_note` | Edit a day note |
| `delete_day_note` | Remove a day note |
| `create_collab_note` | Create a shared trip note |
| `update_collab_note` | Edit a collaborative note |
| `delete_collab_note` | Remove a collaborative note |

### Personal Travel
| Tool | Description |
|:---|:---|
| `create_bucket_list_item` | Add to your travel bucket list |
| `delete_bucket_list_item` | Remove from bucket list |
| `mark_country_visited` | Mark a country as visited (Atlas) |
| `unmark_country_visited` | Remove from visited countries |

## Google Maps MCP Tools Reference (7 tools)

| Tool | Description |
|:---|:---|
| `maps_search_places` | Search for places — returns name, address, lat/lng, place_id, rating |
| `maps_place_details` | Get full details for a place_id — reviews, opening hours, website, phone |
| `maps_directions` | Get directions between two points |
| `maps_distance_matrix` | Calculate travel distance and time for multiple origin/destination pairs |
| `maps_geocode` | Convert an address to coordinates (prefer `maps_search_places` instead) |
| `maps_reverse_geocode` | Convert coordinates to an address |
| `maps_elevation` | Get elevation data for locations |

## Airbnb MCP Tools Reference (2 tools)

| Tool | Description |
|:---|:---|
| `airbnb_search` | Search listings by location, dates, guests, price range |
| `airbnb_listing_details` | Get full details for a specific listing |

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- **Day 1 MUST start with the departure location** (home address) as the first assigned place — never skip this
- Currency should match the destination (JPY for Japan, EUR for Europe, etc.)
- Use `maps_search_places` → `maps_place_details` to get full place info (don't geocode manually)
- Check reviews and ratings via `maps_place_details` when choosing between similar places
- Budget items should reflect per-person costs when persons > 1
- Include practical notes: opening hours, prices, local customs, drive times
- **Traveling with pets:** When travelers have dogs/animals, research pet-friendly accommodations, beaches, trails, and restaurants. Note leash policies, pet fees, and accessibility for pet carriers/strollers
