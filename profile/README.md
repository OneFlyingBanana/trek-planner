# Profile

`USER_PROFILE.md` in this folder pre-loads `/plan-trip` with your stable personal defaults — traveler count, home address, vehicle, vacation style, budget tier, dietary needs, etc. — so Claude stops asking the same questions every trip.

## Usage

1. Open `USER_PROFILE.md` and fill in whichever fields apply. All fields are optional.
2. Run `/plan-trip` as usual. The skill reads the profile in Phase 0, pre-fills Phase 1 defaults, and only asks for what's missing.
3. The confirmation summary tags profile-sourced values with `(from profile)` so you can review and override for the specific trip. The profile file is not auto-modified.

## Privacy

The profile is plaintext markdown and lives in this repo. If you don't want it committed, add it to `.gitignore`:

```
profile/USER_PROFILE.md
```

Keep sensitive data (full address, ID numbers) out if that's a concern — a rough city/region is enough for most trip planning.

## Disabling

Rename the file or clear its fields. When Phase 0 finds no profile (or an empty one), `/plan-trip` falls back to asking every question as before.
