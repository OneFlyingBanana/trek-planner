---
name: generate-roadbook
description: Generate a polished, self-contained HTML "roadbook" presentation of a planned trip — day-by-day legs, stays, budget, packing, an accurate route map, and hover previews. Use to visually review and validate a plan. Reads a plan JSON (from /plan-trip, ideally after /find-accommodation), publishes an artifact, and saves one standalone double-clickable HTML file.
---

# Roadbook Generator — Visual Trip Presentation

Generate a roadbook for the plan at: $ARGUMENTS

A roadbook is a single-file, offline-capable HTML page that renders an entire trip as an editorial rally-style presentation: hero with an accurate geographic route map, day-by-day legs with pace-notes and linked stops (hover previews), a stays table, an animated budget breakdown, and a packing list. It is a **validation tool** — seeing the whole trip laid out surfaces gaps (a night with no bed, a park that's a 3-hour detour, a lopsided budget) before the trip is built in TREK.

## Critical Directives

**READ `artifact-design` FIRST.** Before writing or editing any page markup, invoke the `artifact-design` skill to calibrate design investment. This skill produces a design-forward deliverable — treat it as such.

**NO SUB-AGENTS:** Do ALL work directly. NEVER use the Agent tool to delegate any step.

**NO RESEARCH — RENDER WHAT'S IN THE PLAN:** This skill does not research destinations, prices, or ratings. Every fact on the page comes from the plan JSON. If a place lacks a `lat`/`lng`, a stay lacks a price, or the plan has no `accommodations`/`budget`, render what exists and flag the gap to the user — do not invent data. (Ratings/descriptions/URLs that the plan doesn't carry may be left blank; the page degrades gracefully.)

**SELF-CONTAINED, OFFLINE ONLY:** The artifact sandbox blocks ALL external requests (CDNs, remote images, fonts, fetch, iframes, live link-preview cards). Everything is inline: illustrations are inline SVG (never remote photos), and hover previews are built from plan data, not fetched `og:image`. Do not add any external asset. This is non-negotiable — an external reference breaks the page silently.

**START FROM THE TEMPLATE — DON'T REBUILD:** Copy `assets/roadbook-template.html` (a proven, working roadbook) and replace only the four data arrays, the hero block, and the section sub-headers. The engine below the data (`art`, `esc`, render loops, preview card, `drawMap`, theme toggle) is reusable as-is. Rewriting the engine from scratch wastes context and reintroduces solved bugs (CSS-var-in-SVG-attribute, dark-theme typos, projection math).

## What the template already gives you (do not rebuild)

`assets/roadbook-template.html` is body-only HTML (a `<style>` block, the hero/sections markup, then one `<script>`). The publish step wraps it in `<!doctype html><head>…</head><body>`. The script contains, in order:

- **`gmap(name,lat,lng)`** — builds a Google Maps search URL. Use for any stop without its own website.
- **The four DATA arrays** — `DAYS`, `STAYS`, `BUDGET`, `PACKING` (+ `CAT_COLOR`). **These are the only per-trip edits in the script.**
- **`art(kind)`** — returns an inline-SVG illustration for a place `kind`. Supported keys: `track charge harbour castle cabin coast windmill park pines bog lake sauna city island home` (plus a green default). Pick the closest key; add a new `case` only if a trip genuinely needs a new scene type.
- **`esc`, `el`** — HTML-escape + element helpers.
- **Render loops** — build the legs, stays table, budget bars, and packing columns from the arrays. Untouched.
- **Preview card** — delegated hover/focus cards from `data-pv-*` attributes; auto-disabled on touch. Untouched.
- **`drawMap()`** — the geographic route map. **Trip-specific — see Phase 4.**
- **Theme toggle** — light/dark with `data-theme` override; redraws the map on toggle. Untouched.

Styling: paper/pine/rust/brass/sky palette, serif display + mono data, full light/dark theming. Leave the `<style>` alone unless the user asks for a restyle.

## Workflow

### Phase 1 — Load & Validate Plan

1. Read the plan JSON from `$ARGUMENTS`. If no path is given, ask the user (offer the most recent file under `plans/`).
2. Confirm `schema_version` == `1`; if missing/different, warn (as the sibling skills do) before proceeding.
3. Note what's present: `title`, `start_date`, `end_date`, `currency`, `travelers`, `starting_location`, `days[]`, `accommodations[]`, `budget[]`, `packing[]`.
4. **Warn on gaps, don't block:**
   - `accommodations` empty → the Stays table will be empty. Suggest running `/find-accommodation <path>` first for a complete roadbook, but offer to proceed.
   - `budget` empty → the budget section renders a zero total; say so.
   - Any place missing `lat`/`lng` → it can't appear on the map or carry a preview; list which ones.

### Phase 2 — Derive the Data Arrays

Map the plan JSON onto the four arrays. Preserve the plan's `currency` in all money labels.

**`DAYS`** — one object per day, in itinerary order:
```js
{ n:1, date:"Thu 1 Oct", cls:"drive-heavy", title:"<day title>",
  items:[
    // pace-note (a drive or an info line — no map pin):
    {t:"pace", ico:"🚗", m:"647 km · ~7 h", x:"<the pace-note text>"},
    {t:"pace", ico:"ℹ️", cls:"info", x:"<a soft info line>"},        // cls:"info" | "bridge" for tolls/crossings
    // a stop (renders an illustration + a hover-preview link):
    {t:"place", art:"park", tag:"park", name:"<place name>", rate:"★4.7",
     lat:57.76, lng:15.59, url:"<website or gmap(...)>",
     kind:"National park · primeval forest", desc:"<one-line character>",
     note:"<practical on-the-day note>", warn:true }   // warn:true tints the note rust for caveats
  ]}
```
Deriving each field:
- `n` = day number; `date` = short human date from `start_date` + offset (e.g. `"Thu 1 Oct"`).
- `cls`: `"drive-heavy"` for long transit days, `"track"`/`"home"` for special days, `""` otherwise. Cosmetic accent only.
- `title` = the plan day's title.
- **Pace-notes** come from the plan's day notes about *driving/logistics* (distance, roads, tolls, EV charging). `ico` = a single emoji; `m` = the short metric shown bold (distance·time), optional.
- **Places** come from the day's assigned places. `art` = closest `art()` key for the place type. `tag` = short lowercase label (`park track stay food stop reserve island village boat sauna home` …) — controls the tag chip colour. `kind` = a "Type · subtype" caption. `desc` = the place description (one line). `note` = the practical note. `url` = the place's `website` if present, else `gmap(name, lat, lng)`.
- Every place with a `url` automatically gets a hover preview — no extra work.

**`STAYS`** — one row per entry in `accommodations[]` (a multi-night stay is one row):
```js
{ name:"<hotel>", loc:"<City, CC>", nights:2, dates:"1–3 Oct", rate:"★4.6",
  ppn:120, total:240, url:"<website or gmap>", free:true /* only for free stays */ }
```
`ppn` = `price_per_night`, `total` = `total_price`, `nights` from the check-in/out day span, `dates` = the human date range. Free stays: `ppn:0, total:0, free:true`.

**`BUDGET`** — one row per `budget[]` entry: `{ cat:"Accommodation", name:"<label>", amt:1372, opt:true /* optional line */ }`. `cat` must be one of `CAT_COLOR`'s keys (`Accommodation Food Transport Activities Other`) so the bar gets a colour — map the plan's category onto the nearest one. `opt:true` renders a line as an optional add-on excluded from the headline total.

**`PACKING`** — group `packing[]` by category: `{ cat:"Clothing", items:["…","…"] }`.

### Phase 3 — Fill the Hero & Section Sub-heads

In the body markup, replace the trip-specific text:
- Hero `eyebrow` = the date range; `<h1>` = a title (wrap a couple of words in `<span class="hl">…</span>` for the rust accent); `.lede` = a one-sentence summary.
- **Hero stats** (`.stat-row`): 4–5 `.stat` tiles — compute from the plan. Good defaults: total days, approximate total km (sum the pace-note distances, round), a headline count (national parks / cities / countries), ferries/flights, travelers. Only show stats the plan supports.
- Section sub-heads (`.sec-head` h2/p for Stays, Budget, Packing) and the `.callout` — rewrite to match this trip, or drop the callout if there's nothing to flag.
- The footer `.fnote`.

### Phase 4 — Adapt the Map (the one geography-specific step)

`drawMap()` projects real coordinates with Web-Mercator into a fixed viewBox, over hand-traced coastlines. It is currently bounded to **Western Europe + Scandinavia** (`LON0=4.0, LON1=18.5, LAT0=45.3, LAT1=59.8`) with coastlines for Scandinavia, Jutland, Zealand, Funen, Öland, and continental Europe.

Decide, based on the plan's geography:

- **Trip fits the existing bounds (Alps ↔ Nordics, roughly lon 4–18, lat 45–60):** keep the projection and coastlines. Just update:
  - `S` — the true `[lat,lng]` of each overnight/major stop (from the plan).
  - `W` — intermediate waypoints so drawn roads follow real geography (motorway hubs, bridges).
  - `outbound` / `ret` — ordered key lists tracing the actual route.
  - `labels` — which stops get a text label, with `[text, dx, dy, anchor]` nudges to avoid overlaps.
- **Trip is elsewhere but still one coherent region:** re-fit `LON0/LON1/LAT0/LAT1` to the trip's bounding box (min/max of all stop coords + a margin), and replace the coastline arrays (`SCAND`, `JUT`, `CONT`, …) with simplified `[lat,lng]` traces of that region's coasts, or drop coastlines and keep just the sea backdrop + route if tracing isn't worth it. The projection math (`merc`, `P`, `scale/offX/offY`) auto-fits any bounds — only the bounds and coastlines change.
- **Trip has no meaningful geography for a route map** (single city, flights-only) or accurate coastlines aren't feasible: **remove the map** rather than ship an inaccurate one. Delete the `.map-frame` block from the hero and switch `.hero-grid` to a single column. An inaccurate map is worse than none — the user has explicitly rejected inaccurate maps before.

Colours in the map are read from computed CSS (`col.pine` etc.) — **never** set SVG presentation attributes to `var(--…)`; that does not resolve. Keep passing resolved hex/rgb strings via `setAttribute`, as the template does.

### Phase 5 — Assemble, Publish & Save

Work in the scratchpad, then save one standalone file to the plan's folder.

1. **Assemble** the body-only file (scratchpad `roadbook.html`) from the edited template. Sanity-check in the shell with `node`: the script parses, there are no `setAttribute(...,'var(--` occurrences, and the file has exactly one `<style>`/one `<script>`.
2. **Publish the artifact** with the `Artifact` tool (favicon 🏁, a one-line description). The tool wraps the body in the head/skeleton — pass the body-only scratchpad file. Give the user the URL.
3. **Save the standalone, double-click-to-open copy** next to the plan — this is the ONLY local file: `plans/<trip-folder>/roadbook.html`. It is the scratchpad body wrapped in a full document (`<!doctype html><html lang="en"><head>` with charset, viewport, a `<title>`, a minimal CSS reset, then `<body>…</body></html>`). Validate it (starts with doctype, single body, JS parses). Deliver it with `SendUserFile` (`display: "attach"`), captioned as the offline copy. Do NOT also save a body-only copy — the user wants a single double-clickable file, not a duplicate.
4. **Report** to the user: artifact URL, the one local path, and any gaps you flagged in Phase 1 (empty stays, missing coords, map removed/re-fitted).

## Tips
- **The roadbook mirrors the plan — it never edits it.** If reviewing the roadbook reveals a real problem (a night with no bed, a park too far), fix it in the plan JSON (or via `/plan-trip` / `/find-accommodation`) and regenerate — don't paper over it in the HTML.
- **Regenerating:** to update an already-published roadbook in place, re-edit the body-only scratchpad file and call `Artifact` again with the **same file path** (keep the 🏁 favicon) so it redeploys to the same URL — then re-wrap and overwrite the local standalone `roadbook.html`.
- **Currency:** every price label uses the plan's `currency`. Don't convert unless the plan already stored converted values.
- **Illustrations over photos:** always. Photos would need to be remote (blocked) or huge inline data-URIs. The `art()` scenes keep the file small and fully offline.
- **Keep the engine boring:** the further you drift from the template's render loops and preview machinery, the more you re-solve bugs already fixed here.
