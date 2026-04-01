---
name: plan-trip
description: Plan and create a trip using TREK MCP tools. Use when the user wants to plan a trip, create an itinerary, research destinations, or organize travel logistics.
---

# Trip Planner

Plan and create a trip for: $ARGUMENTS

## Workflow

Follow these steps in order. Present findings to the user before proceeding at each stage.

### 1. Gather Requirements

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

### 2. Research

Use available tools to research:
- **WebSearch**: Destinations, seasonal info, scenic routes, activities, flight prices
- **Google Maps MCP**:
  - `maps_search_places` — find places, get ratings and place IDs
  - `maps_place_details` — get reviews, opening hours, website, phone number (use the `place_id` from search results)
  - `maps_directions` / `maps_distance_matrix` — drive times, routes between stops
- **Airbnb MCP**: Search accommodation options and pricing

When comparing candidate places (restaurants, activities, etc.), use `maps_place_details` to check ratings, reviews, and opening hours to help choose the best options.

Present a proposed itinerary outline to the user for feedback before building.

### 3. Create Trip in TREK

Use TREK MCP tools in this order:

**Step 1 — Create trip:**
- `create_trip` with title, description, start_date, end_date, currency

**Step 2 — Get trip context:**
- `get_trip_summary` to retrieve the trip with auto-generated day IDs

**Step 3 — Set day titles:**
- `update_day` to give each day a descriptive title (e.g., "Day 3: Kusatsu Onsen & Route 292")

**Step 4 — Build each day (places and notes in order):**

Process each day sequentially. For each day, add items in itinerary order.

**Important:** The first item on Day 1 must be the starting location (e.g., home address) created as a place, so TREK can draw the first leg of the journey on the map. Without this geo point, the route starts at the first destination instead of where the traveler actually departs from.

- For **places**:
  1. `maps_search_places` to find the place (returns address, lat, lng, place_id, rating)
  2. `maps_place_details` with the `place_id` to get website, phone, opening hours, reviews
  3. `create_place` with all the collected data (name, address, lat, lng, website, phone, description)
  4. `assign_place_to_day` to link to the current day
  5. `update_assignment_time` to set visit start/end times
- For **notes** (timing, logistics, drive times, tips):
  - `create_day_note` with text, time, and icon

After all items for a day are added:
- `reorder_day_assignments` to confirm the correct order within the day

**Step 5 — Add budget items:**
- `create_budget_item` for each cost category:
  - Transport (flights, car rental, fuel, tolls)
  - Accommodation (hotels, ryokans, hostels)
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

### 4. Save Plan Locally

Save a backup JSON in `plans/<destination-year>/<trip_name>.json` using the schema from `core/system_prompt.txt`.

### 5. Present Summary

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

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- Currency should match the destination (JPY for Japan, EUR for Europe, etc.)
- Use `maps_search_places` → `maps_place_details` to get full place info (don't geocode manually)
- Check reviews and ratings via `maps_place_details` when choosing between similar places
- Budget items should reflect per-person costs when persons > 1
- Include practical notes: opening hours, prices, local customs, drive times
