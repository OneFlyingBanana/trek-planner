# Trek Planner

AI-powered trip planning using [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [TREK](https://github.com/mauriceboe/TREK).

Tell Claude what kind of trip you want, and it will research destinations, build a day-by-day itinerary, and create it in your TREK instance — complete with places, budget, packing list, reservations, and day notes.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- A [TREK](https://github.com/mauriceboe/TREK) instance with the MCP addon enabled
- [Node.js](https://nodejs.org/) (for MCP server packages)
- A [Google Maps API key](https://console.cloud.google.com/) (for geocoding places)

## Setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd trek-planner
cp .env.example .env
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

### 2. Start Claude Code

```bash
claude
```

The MCP servers are pre-configured in `.claude/settings.json` and connect automatically when Claude Code starts from this directory.

## Usage

Use the `/plan-trip` command in Claude Code:

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

### What happens

1. Claude gathers your requirements (destination, dates, budget, interests)
2. Researches destinations, routes, activities, and pricing via web search
3. Geocodes locations via Google Maps
4. Creates the full trip in TREK with places, day assignments, budget, packing list, reservations, and notes
5. Saves a local JSON backup in `plans/`

## MCP Servers

Three MCP servers are configured in `.claude/settings.json`:

| Server | Purpose |
|:---|:---|
| **trek** | Trip management via TREK (34 tools — trips, places, days, budget, packing, reservations, notes) |
| **google-maps** | Geocoding, directions, place search |
| **airbnb** | Accommodation search and listing details |

## Troubleshooting

### Verify MCP servers are connected

In Claude Code, type `/mcp` to see the status of all MCP servers. All three should show as connected.

### TREK tools not appearing

If TREK tools aren't available after starting Claude Code:

1. **Check your `.env`** — make sure `TREK_URL` and `TREK_MCP_TOKEN` are set correctly
2. **Test the connection manually:**
   ```bash
   bash core/trek-mcp.sh
   ```
   This should start without errors. Press `Ctrl+C` to stop it.
3. **Verify TREK MCP addon is enabled** — In TREK: Admin Panel → Addons → MCP should be toggled on
4. **Regenerate the token** — In TREK: Settings → MCP Configuration → generate a new token and update `.env`

### Google Maps not working

Make sure your API key has the Geocoding API enabled in [Google Cloud Console](https://console.cloud.google.com/).

### Node.js errors

The MCP servers require Node.js and `npx`. Install from [nodejs.org](https://nodejs.org/) (LTS version recommended).

## Project Structure

```
.claude/
  settings.json               # MCP server configurations (auto-loaded by Claude Code)
  skills/plan-trip/SKILL.md   # The /plan-trip skill
core/
  trek-mcp.sh                 # TREK MCP server launcher (reads config from .env)
  system_prompt.txt           # Trip creation workflow and JSON backup schema
plans/                        # Local trip backups (gitignored)
```
