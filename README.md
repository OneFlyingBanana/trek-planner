# Trek Planner

Trip planning skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that build trips in [TREK](https://github.com/mauriceboe/TREK).

Agents run the skills from **Paperclip**: Roald describes a trip on a Paperclip issue, the agents research and plan it, build a `[paperclip]` draft trip in TREK, and hand it back for review. All plan files are committed to this repo through pull requests. The rules agents follow are in `CLAUDE.md`.

## How it runs in Paperclip

- **TREK** is reached through Paperclip's TREK connection. Agents need no TREK URL, token or `.env` file.
- **Google Maps** data comes through TREK's own tools (`search_place` with `provider: "google"`, `get_place_details`), billed to Roald's key and capped per trip (`docs/call-budgets.md`). No separate Google Maps server is used.
- **Airbnb, AirTrail and Dawarich** are not used (`docs/sources.md`).
- **Documents** (PDFs, spreadsheets, the roadbook) are made with the ArtCraft `*craft-cli` apps in the agent container.
- Every TREK call can time out after 10 s with `mcp_remote_fetch_failed`; the retry rule is in `CLAUDE.md`.

### The flow

1. Roald opens a Paperclip issue with the trip brief.
2. Agents propose the brief and the trip's driving settings. **Checkpoint 0:** Roald confirms them.
3. Agents research the itinerary, build a skeleton `[paperclip] <title>` trip in TREK, check the route with TREK's calculator, pick stays and render the roadbook. All of it lands in `plans/<slug>/` on a `trip/<slug>` branch.
4. **Checkpoint A:** Roald approves the plan PR in Paperclip.
5. Agents complete the trip in TREK (stays, budget, todos, packing, notes).
6. **Checkpoint B:** Roald reviews the trip in TREK and comments on the issue. A retro writes lessons to `docs/lessons/`.

The skills for steps 2, 3 and 6 are being rebuilt in rounds (design on Paperclip issue ISD-4). Today the repo has:

| Skill | Does | Runs in Paperclip? |
|---|---|---|
| `build-trip` | creates a planned trip in TREK from a plan JSON | yes (TREK tools only) |
| `plan-trip` | researches and plans an itinerary, writes the plan JSON | laptop only for now: uses the Google Maps server |
| `find-accommodation` | picks stays and patches the plan JSON | laptop only for now: uses the Google Maps and Airbnb servers; replaced by `find-stays` |
| `generate-roadbook` | renders the plan as an HTML roadbook | laptop only for now: needs the Claude.ai `Artifact` tool; moving to ArtCraft PDF |

### Personal defaults

`profile/USER_PROFILE.example.md` shows the profile format, including Roald's driving settings. They are starting values: they are proposed for each trip and confirmed by Roald at checkpoint 0 before anything is written to TREK. Copy the example to `profile/USER_PROFILE.md` (gitignored) and fill it in; see `profile/README.md`.

## Documentation

| File | Contents |
|---|---|
| `CLAUDE.md` | rules for agents: board rules, retry rule, checkpoints |
| `docs/pacing.md` | thresholds for drivable days, charging, fallback estimate |
| `docs/call-budgets.md` | per-trip and per-build call limits |
| `docs/sources.md` | research and accommodation sources and Roald's decisions on them |
| `docs/lessons/README.md` | format of the per-trip lessons |
| `docs/skills/CHANGELOG.md` | one line per skill change |

## Project structure

```
CLAUDE.md                                  rules for agents
.claude/settings.json                      MCP servers and tool allowlist (laptop mode)
.claude/skills/plan-trip/SKILL.md          research and plan an itinerary
.claude/skills/find-accommodation/SKILL.md pick stays for a planned trip
.claude/skills/build-trip/SKILL.md         create a planned trip in TREK
.claude/skills/generate-roadbook/SKILL.md  render the plan as a roadbook
docs/                                      pacing, call budgets, sources, lessons, skill changelog
profile/USER_PROFILE.example.md            profile format and driving starting values
profile/README.md                          how the profile is used
.mcp.json                                  TREK over HTTP (laptop mode)
setup-mcp.sh, core/, .env.example, .nvmrc  laptop mode launchers
```

Trip folders (`plans/<slug>/`) are committed through pull requests once the first trip is planned.

---

## Appendix: laptop mode

Roald can still run the skills in Claude Code on his own machine, with locally launched MCP servers. Agents do not use this path.

### Prerequisites

- Claude Code
- A TREK instance with the MCP addon enabled
- Node.js 22+ (`.nvmrc` pins the version; run `nvm install`)
- A Google Maps API key, if you run `plan-trip` or `find-accommodation`

### Setup

```bash
cp .env.example .env
nvm install
./setup-mcp.sh
claude
```

Fill in `.env`:

```
TREK_URL=https://your-trek-instance.com
TREK_MCP_TOKEN=your_trek_mcp_token
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

- `TREK_MCP_TOKEN`: in TREK, Admin Panel → Addons → enable MCP, then Settings → MCP Configuration → generate token.
- `GOOGLE_MAPS_API_KEY`: Google Cloud Console → APIs & Services → Credentials. Enable the Places, Directions and Geocoding APIs.

`setup-mcp.sh` registers three servers with Claude Code: `trek` (`core/trek-mcp.sh`), `google-maps` (`core/google-maps-mcp.sh`) and `airbnb`. The Airbnb server is still registered for the current `find-accommodation` skill, but Airbnb is no longer a planning source (`docs/sources.md`); you can skip it.

### Usage

```
/plan-trip 10 days road trip through Scotland, castles and whisky
/find-accommodation plans/<slug>/<plan>.json
/generate-roadbook plans/<slug>/<plan>.json
/build-trip plans/<slug>/<plan>.json
```

Each skill runs in its own conversation; the plan JSON is the hand-off between them.

### Troubleshooting

- **Servers connected?** Type `/mcp` in Claude Code.
- **TREK MCP hangs.** The TREK MCP server accepts a limited number of connections. Restart the TREK container: `docker restart <your-trek-container>`.
- **TREK or Google Maps tools missing.** Check `.env`, then run `./core/trek-mcp.sh` or `./core/google-maps-mcp.sh` by hand; each should start without errors (`Ctrl+C` to stop). In TREK, check that the MCP addon is on, or generate a new token.
- **Node.js errors.** The launchers need Node.js 22+ and `npx`; both load nvm themselves.
