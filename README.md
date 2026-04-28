# Trek Planner

AI-powered trip planning using [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [TREK](https://github.com/mauriceboe/TREK).

Tell Claude what kind of trip you want, and it will research destinations, build a day-by-day itinerary, and create it in your TREK instance — complete with places, budget, packing list, reservations, and day notes.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- A [TREK](https://github.com/mauriceboe/TREK) instance with the MCP addon enabled
- [Node.js](https://nodejs.org/) 22+ (for MCP server packages) — use [nvm](https://github.com/nvm-sh/nvm) to manage versions
- A [Google Maps API key](https://console.cloud.google.com/) (for place search, details, directions)

## Setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd trek-planner
cp .env.example .env
```

If you use [nvm](https://github.com/nvm-sh/nvm), the `.nvmrc` will automatically select the right Node version:

```bash
nvm install
```

Edit `.env` and fill in your values:

```
TREK_URL=https://your-trek-instance.com
TREK_MCP_TOKEN=your_trek_mcp_token
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

**Where to get these:**
- `TREK_URL` — The URL of your TREK instance
- `TREK_MCP_TOKEN` — In TREK: Admin Panel → Addons → enable MCP, then Settings → MCP Configuration → generate token
- `GOOGLE_MAPS_API_KEY` — [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials

### 2. Register MCP servers

```bash
./setup-mcp.sh
```

This registers the three MCP servers (TREK, Google Maps, Airbnb) with Claude Code. You only need to run this once after cloning.

### 3. Start Claude Code

```bash
claude
```

The MCP servers connect automatically when Claude Code starts from this directory.

## Usage

### Pre-loading your personal defaults (optional)

`/plan-trip` reads `profile/USER_PROFILE.md` at the start of every run. Fill in stable personal info there (traveler count, home address, vehicle, vacation style, budget tier, dietary needs…) and Claude will stop asking the same questions every trip. Values are pre-filled as defaults and still shown in the Phase 1 confirmation summary, tagged `(from profile)` — override any of them per-trip. See `profile/README.md` for details.

### Planning a trip

Use `/plan-trip` in Claude Code to research and plan an itinerary:

```
/plan-trip 2 weeks in Japan, scenic driving and onsens, budget 3-4k CHF per person
```

```
/plan-trip long weekend in Barcelona, food and architecture, mid-range budget
```

```
/plan-trip 10 days road trip through Scotland, castles and whisky
```

You can also just describe what you want in natural language — Claude will use the trip planning skill automatically.

`/plan-trip` will:
1. Gather your requirements (starting point, destination, dates, budget, interests)
2. Research destinations, routes, activities, and pricing via web search
3. Look up places via Google Maps (ratings, reviews, opening hours, directions)
4. Present a full itinerary for your approval — iterate until you're happy
5. Save the approved plan as a JSON file in `plans/` (with an empty `accommodations` array — hotels are picked next)

### Finding accommodations

Once the itinerary is approved, use `/find-accommodation` to research and pick hotels for each stay:

```
/find-accommodation plans/japan-2026/japan_road_trip.json
```

`/find-accommodation` will:
1. Detect the distinct stays from your itinerary and confirm them with you
2. Research candidates via Google Maps (hotels, ryokans, B&Bs) and Airbnb (apartments, unique stays)
3. Present the top 3 options per stay with pros/cons, per-night prices, ratings
4. Patch the plan JSON in place with your picks and add per-hotel rows to the budget

### Building the trip in TREK

Once both itinerary and accommodations are in the plan JSON, use `/build-trip` to create it in your TREK instance:

```
/build-trip plans/japan-2026/japan_road_trip.json
```

`/build-trip` will:
1. Read and validate the plan JSON
2. Check if the trip already exists in TREK (for recovery after interruptions)
3. Create the trip with all places, day assignments, accommodations, budget, packing list, reservations, and notes
4. Present a summary with the trip URL

The three-step flow (`/plan-trip` → `/find-accommodation` → `/build-trip`) keeps each phase focused and prevents context overflow on longer trips. Each step runs in its own conversation, so even a 2-week itinerary won't run out of steam.

## MCP Servers

Three MCP servers are configured in `.claude/settings.json`:

| Server | Purpose |
|:---|:---|
| **trek** | Trip management via TREK (34 tools — trips, places, days, budget, packing, reservations, notes) |
| **google-maps** | Place search, place details (reviews, hours, phone), directions, distance matrix |
| **airbnb** | Accommodation search and listing details |

## Troubleshooting

### Verify MCP servers are connected

In Claude Code, type `/mcp` to see the status of all MCP servers. All three should show as connected.

### TREK MCP hangs or stops responding

The TREK MCP server accepts a limited number of connections. If it becomes unresponsive (tools time out or hang indefinitely), restart the TREK Docker container:

```bash
docker restart <your-trek-container>
```

This is the only way to reset the connections for now.

### TREK tools not appearing

If TREK tools aren't available after starting Claude Code:

1. **Check your `.env`** — make sure `TREK_URL` and `TREK_MCP_TOKEN` are set correctly
2. **Test the connection manually:**
   ```bash
   ./core/trek-mcp.sh
   ```
   This should start without errors. Press `Ctrl+C` to stop it.
3. **Verify TREK MCP addon is enabled** — In TREK: Admin Panel → Addons → MCP should be toggled on
4. **Regenerate the token** — In TREK: Settings → MCP Configuration → generate a new token and update `.env`

### Google Maps not working

If Google Maps tools aren't available after starting Claude Code:

1. **Check your `.env`** — make sure `GOOGLE_MAPS_API_KEY` is set
2. **Test the connection manually:**
   ```bash
   ./core/google-maps-mcp.sh
   ```
   This should start without errors. Press `Ctrl+C` to stop it.
3. **Enable the required APIs** in [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services:
   - **Places API** (place search and details — ratings, reviews, opening hours)
   - **Directions API** (routes and drive times)
   - **Geocoding API** (address lookups)

### Node.js errors

The MCP servers require Node.js 22+ and `npx`. If you use nvm, run `nvm install` from the project root — the `.nvmrc` pins the correct version. Both MCP launcher scripts load nvm automatically so `npx` is available even in non-interactive shells.

## Project Structure

```
.claude/
  settings.json                # MCP server configurations (auto-loaded by Claude Code)
  skills/plan-trip/SKILL.md          # /plan-trip — research & plan an itinerary
  skills/find-accommodation/SKILL.md # /find-accommodation — research & pick hotels for a planned trip
  skills/build-trip/SKILL.md         # /build-trip — create a planned trip in TREK
profile/
  USER_PROFILE.md              # Personal defaults pre-loaded by /plan-trip (optional)
  README.md                    # How the profile is used
core/
  trek-mcp.sh                  # TREK MCP server launcher (reads config from .env)
  google-maps-mcp.sh           # Google Maps MCP server launcher (reads API key from .env)
  system_prompt.txt            # Trip creation workflow and JSON backup schema
plans/                         # Local trip plan JSONs (gitignored)
```
