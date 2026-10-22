# Lessons

One file per trip run, named `<YYYY-MM-DD>-<slug>.md`. `trip-retro` writes it to `plans/<slug>/lessons.md` and copies it here, so lessons survive if a trip folder is removed.

## Format

Three lists:

1. **What the skills got wrong**
2. **What Roald had to fix by hand** (from his checkpoint comments and a `get_trip_summary` diff against the TREK manifest)
3. **What cost the most calls or wakes**

Every item ends with `skill change: yes|no, issue: ISD-<n>`. A "no" needs a one-line reason ("won't fix: ...").

Lines starting with `default change:` (for example "default change: Roald never wants activities before 10:00") are proposed to `profile/USER_PROFILE.md` by the next `trip-brief` run.

## How lessons are used

- `trip-brief` reads the last three lesson files at the start of every trip.
- Each lesson marked `skill change: yes` has a Paperclip `skill-change` issue; the resulting PR adds a line to `docs/skills/CHANGELOG.md`.
- The Evaluator checks each round that every open lesson has an issue or a written "won't fix".
