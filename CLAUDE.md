# trek-planner

Skills that plan a trip and build it into Roald's TREK instance. Agents run them from Paperclip; Roald can still run them on his laptop (README, "Laptop mode").

## Where things live

- `plans/<slug>/` – one folder per trip, committed: brief, research notes, plan JSON, validation, TREK manifest, build report, roadbook, lessons.
- `.claude/skills/<skill>/SKILL.md` – the skills. Target flow: `trip-brief` → `research-itinerary` → `validate-plan` → `build-trip --skeleton` → `route-check` → `find-stays` → `validate-plan` → `generate-roadbook` → `build-trip --complete` → `trip-retro`. Until those land, the repo has `plan-trip`, `find-accommodation`, `build-trip` and `generate-roadbook`.
- `profile/USER_PROFILE.md` – Roald's defaults (gitignored); `profile/USER_PROFILE.example.md` shows the shape.
- `docs/` – pacing thresholds, call budgets, sources, lessons, skill changelog.

Every skill states the files it found, writes its output into `plans/<slug>/`, and ends with the files it wrote and the exact next command. If an input is missing, it stops and names the skill that produces it.

## Board rules (Paperclip's `TOOLS.md`, outside this repo, wins over this file)

- Work on a branch and open a pull request. Never push to `main`. Roald merges.
- End every commit with `Assisted-by: Paperclip <role>` and `Co-Authored-By: Paperclip <noreply@paperclip.ing>`.
- TREK is Roald's real planner. Every trip an agent creates is titled `[paperclip] <title>`. Write only to trips whose title starts with `[paperclip] `; read others, never edit them.
- Never call TREK delete, share, member or user/instance settings tools; Paperclip blocks them. Do not retry a blocked call. List what Roald should remove under **Safe to delete** in the issue.
- `update_roadtrip_settings` is a trip setting and allowed, but only with the values Roald confirmed at checkpoint 0.
- Google-billed calls (`search_place` with `provider: "google"`, `get_place_details`) only when the task needs them, never in a loop. Limits: `docs/call-budgets.md`.
- ArtCraft first: use the `*craft-cli` apps for documents, spreadsheets, PDFs and images. Run `<app>-cli --help` first; if an app fails, say so and name the fallback.
- Airbnb, AirTrail and Dawarich are not used (`docs/sources.md`).
- Secrets come only as environment variables. Never print or commit them.

## TREK timeout and retry rule

Paperclip cuts every TREK call at 10 s and reports `mcp_remote_fetch_failed`.

1. Treat `mcp_remote_fetch_failed` as a timeout, not a tool error.
2. Wait about 30 s, then repeat the same call with the same arguments **once**.
3. If the retry fails too, record the tool, the arguments (no secrets) and both timestamps in the step's output file (`plans/<slug>/validation.md`, `plans/<slug>/build-report.md` or `plans/<slug>/trek-route.json`), use the fallback the skill names, and go on. Never retry a third time.
4. "Remote MCP session expired" after a TREK restart: retry once.

A retried write is safe only because the TREK manifest makes writes idempotent: look for the item's `plan:<plan_id>/<item_id>` note in `get_trip_summary` before writing it again. The first `calculate_roadtrip` after a change is the slow one, so make it early in a run.

## Checkpoints

Roald decides at three points, all in Paperclip (issue questions, approvals, comments), never by chat phrases:

0. **Brief and driving settings** – after `trip-brief`: one question set with the trip's proposed driving settings and any missing brief field. No settings reach TREK before he confirms.
1. **Plan approval** – a Paperclip approval on the plan PR, with the roadbook PDF attached and the `[paperclip]` draft trip in TREK.
2. **Trip review** – after the complete build, Roald comments on the issue; fixes go into a follow-up build.

Between checkpoints, proceed unless Roald objects on the issue.

## Write files, not prose

Results live in files under `plans/<slug>/`, not in chat. Every trip run ends with entries in `plans/<slug>/lessons.md`, copied to `docs/lessons/`. Every skill change goes through a PR and a line in `docs/skills/CHANGELOG.md`.
