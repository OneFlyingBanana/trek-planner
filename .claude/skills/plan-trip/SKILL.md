---
name: plan-trip
description: Research and plan a trip itinerary. Use when the user wants to plan a trip, research destinations, or organize travel logistics. Outputs an approved plan JSON that can be built in TREK with /build-trip.
---

# Trip Planner — Research & Plan

Plan a trip for: $ARGUMENTS

## Critical Directives

**NO SUB-AGENTS:** Do ALL work directly. NEVER use the Agent tool to delegate research, creation, or any other step. You must perform every tool call yourself.

**SEQUENTIAL MCP CALLS:** NEVER call MCP tools in parallel. MCP servers are unreliable under concurrent requests. Execute all MCP tool calls (Google Maps, Airbnb) one at a time, sequentially.

**CONTEXT EFFICIENCY:** You are doing research-heavy work. Manage your context carefully:
- Shortlist candidates using `maps_search_places` ratings BEFORE calling `maps_place_details` — only deep-dive your top 2-3 picks per slot.
- Group web searches by theme (e.g., one search for "best restaurants in Takayama" rather than one per restaurant).
- After each research sub-phase, write a brief summary of your findings and decisions. Do not rely on raw API responses staying in context.
- Drop rejected candidates from consideration immediately — do not carry them forward.

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

Do ALL research in this phase. Build up a running summary of selected places, accommodations, and route info as you go.

#### 2a. Web Research
Use **WebSearch** to gather:
- Destination overviews, seasonal info, local events during travel dates
- Scenic routes and must-see attractions
- Flight/transport prices and options
- Entry fees, menu price ranges, and activity costs (Google Maps does not provide prices)
- Pet-friendly options if traveling with animals (accommodations, restaurants, trails, policies)

**After web research:** Write a summary of key findings — best areas, seasonal considerations, price ranges, must-sees. This is your research foundation.

#### 2b. Place Research (Google Maps)

**Shortlist first, then deep-dive:**
1. `maps_search_places` — search for candidates in each category (attractions, restaurants, etc.)
2. Review the search results (name, rating, address) and pick your top 2-3 candidates per slot
3. `maps_place_details` — get full details ONLY for your shortlisted picks (ratings, reviews, opening hours, website, phone)

**Use ratings and reviews to make informed selections:**
- Compare candidates by rating — prefer places rated 4.0+
- Flag any place with rating below 4.0 or with concerning review patterns (recent negative trends, safety issues, closures mentioned)
- Read review text for practical tips (best time to visit, what to order, things to avoid)
- Cross-reference planned visit times with opening hours — flag conflicts immediately

When choosing between similar places (e.g., two ramen shops near the same area), use the ratings, review quality, and opening hours to pick the best fit for the itinerary.

**After place research:** Summarize your selected places per day with name, address, lat/lng, rating, key notes, and planned visit time.

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
## [Trip Title] — Proposed Itinerary

**Dates:** [start] → [end] ([N] days)
**Travelers:** [count]
**Transport:** [mode]

---

### Day 1: [Title]
| Time | Activity | Details |
|------|----------|---------|
| 09:00 | [Place/Activity] | [rating] · [drive time from previous] · [key note] |
| ... | ... | ... |

**Accommodation:** [Name] — [price/night] · [rating] · [1-line why]

*(repeat for each day)*

---

### Accommodation Options
For each location, top 3 picks with: price, rating, pros/cons, source (Maps/Airbnb)

### Budget Estimate
| Category | Per Person | Total |
|----------|-----------|-------|
| Transport | ... | ... |
| Accommodation | ... | ... |
| Food | ... | ... |
| Activities | ... | ... |
| Buffer (10%) | ... | ... |
| **Total** | ... | ... |

### Flagged Issues
- [Any long drives, low-rated places, opening hours conflicts, unverified info]
```

**STOP. Wait for user feedback and approval before proceeding to Phase 4.**

The user may want to swap places, adjust timing, pick different accommodations, or change the route. Iterate until they are satisfied.

### Phase 4 — Save Approved Plan

After the user approves the itinerary, save the complete plan as JSON to `plans/<destination-year>/<trip_name>.json`.

This file is the **handoff artifact** — it must contain everything needed to build the trip in TREK without any further research.

**JSON Schema:**

```json
{
  "title": "Trip Title",
  "description": "Short description of the trip",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "currency": "EUR",
  "travelers": 2,
  "transport": "rental car",
  "starting_location": {
    "name": "Home, Chamoson",
    "address": "1955 Chamoson, Switzerland",
    "lat": 46.2017,
    "lng": 7.2260
  },
  "days": [
    {
      "day_number": 1,
      "title": "Day 1: Arrival & Old Town",
      "items": [
        {
          "type": "place",
          "name": "Eiffel Tower",
          "description": "Iconic iron lattice tower on the Champ de Mars",
          "address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris",
          "lat": 48.8584,
          "lng": 2.2945,
          "time_start": "09:00",
          "time_end": "11:00",
          "notes": "Go early to avoid crowds. Entry: 26 EUR.",
          "website": "https://www.toureiffel.paris",
          "phone": "+33 892 70 12 39"
        },
        {
          "type": "note",
          "text": "30 min drive to restaurant",
          "icon": "car"
        }
      ],
      "accommodation": {
        "name": "Hotel & Spa Le Bouclier d'Or",
        "address": "1 Rue du Bouclier, 67000 Strasbourg",
        "lat": 48.5850,
        "lng": 7.7458,
        "price_per_night": 150,
        "rating": 4.6,
        "source": "google_maps",
        "booking_url": "https://example.com",
        "notes": "Parking available, breakfast included"
      }
    }
  ],
  "budget": [
    {
      "category": "Transport",
      "amount": 200,
      "notes": "Fuel + tolls for 800km total"
    },
    {
      "category": "Accommodation",
      "amount": 450,
      "notes": "3 nights at ~150/night"
    },
    {
      "category": "Food",
      "amount": 300,
      "notes": "~50/person/day"
    },
    {
      "category": "Activities",
      "amount": 100,
      "notes": "Entry fees and tours"
    },
    {
      "category": "Buffer",
      "amount": 105,
      "notes": "~10% contingency"
    }
  ],
  "packing": [
    { "name": "Passport", "category": "Documents" },
    { "name": "Hiking boots", "category": "Footwear" },
    { "name": "Rain jacket", "category": "Clothing" }
  ],
  "collab_notes": [
    {
      "title": "Trip Logistics",
      "content": "Emergency contacts, check-in times, parking info..."
    }
  ],
  "reservations": [
    {
      "type": "hotel",
      "name": "Hotel & Spa Le Bouclier d'Or",
      "date": "2026-06-15",
      "confirmation": "ABC123",
      "notes": "Check-in 15:00, check-out 11:00"
    }
  ]
}
```

**Rules:**
- Dates in YYYY-MM-DD format
- Day numbers sequential from 1
- All places MUST have lat/lng coordinates
- Currency matches destination (JPY, EUR, USD, CHF, etc.)
- Budget amounts are TOTAL (not per person) unless noted
- Include all data the build skill needs — names, addresses, coordinates, times, notes, websites, phones

After saving, tell the user:

> Plan saved to `plans/<path>/<file>.json`. To create this trip in TREK, run: `/build-trip plans/<path>/<file>.json`

## Tips
- **Day 1 MUST start with the departure location** (home address) as the first item — the build skill needs it for map routing
- Currency should match the destination (JPY for Japan, EUR for Europe, etc.)
- Use `maps_search_places` → `maps_place_details` to get full place info (don't geocode manually)
- Check reviews and ratings via `maps_place_details` when choosing between similar places
- Budget items should reflect total costs; note per-person breakdown in the notes field
- Include practical notes: opening hours, prices, local customs, drive times
- **Traveling with pets:** Research pet-friendly accommodations, beaches, trails, and restaurants. Note leash policies, pet fees, and accessibility
