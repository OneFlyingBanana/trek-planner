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
- **Google Maps MCP**: Geocode places, get directions, calculate drive times
- **Airbnb MCP**: Search accommodation options and pricing

Present a proposed itinerary outline to the user for feedback before building.

### 3. Create Trip in TREK

Use TREK MCP tools in this order:

**Step 1 — Create trip:**
- `create_trip` with title, description, start_date, end_date, currency

**Step 2 — Get trip context:**
- `get_trip_summary` to retrieve the trip with auto-generated day IDs

**Step 3 — Set day titles:**
- `update_day` to give each day a descriptive title (e.g., "Day 3: Kusatsu Onsen & Route 292")

**Step 4 — Add places with geocoded coordinates:**
- `create_place` for each location (name, description, address, lat, lng)
- Use Google Maps MCP or curl for geocoding:
  ```bash
  source .env && curl -s "https://maps.googleapis.com/maps/api/geocode/json?address=PLACE+NAME&key=$GOOGLE_MAPS_API_KEY"
  ```

**Step 5 — Assign places to days with times:**
- `assign_place_to_day` to link each place to its day
- `update_assignment_time` to set visit start/end times
- `reorder_day_assignments` to set the correct order within each day

**Step 6 — Add day notes:**
- `create_day_note` for timing, tips, logistics, drive times per day

**Step 7 — Add budget items:**
- `create_budget_item` for each cost category:
  - Transport (flights, car rental, fuel, tolls)
  - Accommodation (hotels, ryokans, hostels)
  - Food & drinks
  - Activities & attractions
  - Miscellaneous & buffer (~10%)

**Step 8 — Add reservations (if known):**
- `create_reservation` for flights, hotels, restaurants, activities
- `link_hotel_accommodation` to connect hotel reservations to check-in/check-out days

**Step 9 — Create packing list:**
- `create_packing_item` for essential items (documents, gear, clothing, etc.)

**Step 10 — Add collaborative notes:**
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

## Tips
- Always start with `get_trip_summary` when working with an existing trip
- Currency should match the destination (JPY for Japan, EUR for Europe, etc.)
- Geocode every place for accurate map pins
- Budget items should reflect per-person costs when persons > 1
- Include practical notes: opening hours, prices, local customs, drive times
