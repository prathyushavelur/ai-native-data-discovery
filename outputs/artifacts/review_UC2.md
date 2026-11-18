# Memo Review: UC2 (Ice-Cream Sales, Weather and Holidays)

## Agreements
- **`internal.sales.daily_by_product` & `internal.sales.products` (feasible with conditions):** Agree. Daily sales exist from 2022-01-01, but historical analysis across 2023-06-01 to 2025-05-31 is blocked until Retail Operations approves access, documents closed-day vs till-outage rows (2024-02-05 to 2024-03-10), and delivers a signed-off crosswalk for the 2024-04-01 product code change (`INT-JOIN-KEY-MISMATCH`).
- **`internal.store.calendar` (feasible with conditions):** Agree. Requires Store Operations access approval, reconciliation of ~1,500 rows against ~1,750 calendar days (`DQ-METADATA-CONTRADICTION`), and documentation of `is_open` and `event_name`.
- **`api.open_meteo_archive` (not feasible on free tier):** Agree. Open-Meteo's terms restrict the free API to non-commercial use (`LIC-NONCOMMERCIAL`), whereas Valdena Gelato Shop is a commercial business; requires a paid subscription, Legal sign-off, and confirmed shop coordinates.
- **`api.nager_public_holidays` (not feasible without licence confirmation):** Agree. The GitHub repository carries an MIT software licence, but the holiday dataset itself has no stated data licence (`LIC-UNKNOWN`), and 2025 holiday counts must be verified.

## Overrules
- None. All source verdicts and red flags align with the catalog records, wiki notes, and G5 calibration rules.

## Dataset Link Verdicts & Gate Decisions
- No external dataset links were supplied (`links_expected: false` in `use_cases/UC2_ice_cream.json`).

## Overall Gate Decision
- **Verdict:** `proceed_with_conditions` (recorded in `outputs/UC2/signoff.json`).
