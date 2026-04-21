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
- **Own vehicle:** VW ID.4 (EV, needs CCS charging)
- **Driver's license countries:** CH, EU

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
