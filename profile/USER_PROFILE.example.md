# User Profile

This file pre-loads `/plan-trip` with stable defaults so Claude stops asking the same questions every trip. Every field is **optional** — leave blank to have Claude ask as normal. Profile values are treated as **defaults to confirm**, not silent assumptions: you will still see every value in the Phase 1 confirmation summary and can override for any individual trip.

Edit values below. Remove or leave blank anything you don't want pre-filled. Commented-out lines (`<!-- ... -->`) are examples.

---

## Travelers

- **Default traveler count:** 2
- **Names / ages:** Alex (38), Sam (36)
- **Pets:** dog named Biscuit (travels with us)

## Origin

- **Home address:** Rue Example 12, 1955 Chamoson, Switzerland
- **Home lat/lng:** 46.2017, 7.2260
- **Nearest airports:** GVA (Geneva), ZRH (Zurich)

## Style & Preferences

- **Vacation style:** balanced
- **Pace:** slow mornings, no activities before 10:00
- **Accommodation style:** mid-range, prefer boutique hotels and guesthouses
- **Interests:** food & dining, nature & outdoors, culture & history

## Transport

- **Default transport mode:** own car for regional trips, rental car for long-haul
- **Own vehicle:** Polestar 2 MY25 Long Range Dual Motor (EV, CCS charging)
- **Driver's license countries:** CH, EU

## Driving settings

**Proposed per trip, confirmed by Roald at checkpoint 0.** These are starting values, not defaults that are copied silently. `trip-brief` puts this table into the checkpoint 0 question for every new trip, adjusted for what the brief says (a ferry to avoid, a hire car, a different pace) with a reason next to each changed row. Only the set Roald confirms is written to the trip with `update_roadtrip_settings`.

| Setting | Starting value | Note |
|---|---|---|
| `roadtrip_vehicle` | `electric` | Polestar 2 MY25 Long Range Dual Motor |
| `roadtrip_battery_kwh` | 79 | usable capacity |
| `roadtrip_kwh_per_100` | 21 | motorway at 120 to 130 km/h, planned on the safe side |
| `roadtrip_battery_degradation` | 3 | percent |
| `roadtrip_fill_percent` | 80 | |
| `roadtrip_leg_minutes` | 150 | |
| `roadtrip_day_minutes` | 480 | |
| `roadtrip_day_start` / `roadtrip_day_end` | 09:00 / 19:00 | |
| `roadtrip_day_end_mode` | `stop` | |
| `roadtrip_hotel_bookends` | `true` | days start and end at the stay once stays exist |
| `roadtrip_avoid` | `""` | set `ferry` or `toll` per trip when needed |
| `roadtrip_service_stops_in_days` | `true` (proposed) | not in Roald's list; decided per trip |
| `roadtrip_show_hazards` | `true` (proposed) | not in Roald's list; decided per trip |

With these values TREK derives about 290 km between charging stops.

## Budget

- **Home currency:** CHF
- **Typical tier:** €€
- **Typical per-person-per-day range:** 150-200 CHF

## Special Needs

- **Dietary restrictions:** one vegetarian, no other restrictions
- **Accessibility needs:** none
- **Language preferences:** English, French, some German

---

## How this is used

When you run `/plan-trip`, Phase 0 reads this file and pre-fills Phase 1 requirements. In the confirmation summary, profile-sourced values are tagged `(from profile)` so you can see exactly what was loaded vs. what you provided for this trip. Override any value per-trip — the profile file is **not** auto-updated.

To disable for a session, rename the file or remove its fields.
