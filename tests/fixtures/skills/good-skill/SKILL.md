---
name: good-skill
description: >
  Fixture skill that passes every lint rule.
---

# Good skill

Call `list_trips`, then `mcp__trek__get_trip_summary`, then `create_place()`
and `assign_place_to_day`. Set the drive with `update_roadtrip_settings`.

Plan fields such as `check_in_day` and Google tools such as
`maps_directions` are not TREK tools. Never call `delete_*` tools.

Read `profile/USER_PROFILE.md` (git-ignored) and `scripts/lint_skills.py`.
Write to `plans/<slug>/plan.json`. See [the tool list](../../trek-tools.txt).
