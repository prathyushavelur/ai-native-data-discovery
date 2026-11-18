# Memo Review: UC1 (Air Quality and Traffic)

## Agreements
- **`api.open_meteo_archive` (feasible with conditions):** Agree. The API covers hourly temperature and humidity across both prototype (2004-2005) and production (2024-2025), but requires Valdena site coordinates (replacing the Milan probe placeholder), client acceptance of reanalysis over station data, and Legal sign-off on mixed upstream provider terms (`LIC-MIXED`).
- **`internal.airq.station_readings` & `internal.traffic.hourly_counts` (feasible with conditions):** Agree. Both internal tables require warehouse access tickets, join lookups (`INT-NO-JOIN-KEY`), reconciliation of the wiki note on station VR-03 stopping on 2024-06-30 (`GOV-CATALOG-WIKI-CONFLICT`), and adjustment for the 2024-03-18 traffic counting basis change (`DQ-SEMANTIC-ENCODING`).
- **`vendor.atmosdata_pro` (not feasible):** Agree. Contract AD-2021-114 expired and its API key was revoked on 2026-01-01; the agent properly respected the guardrail and never called it.

## Overrules & Nuances
- **`link.uci_360` (feasible with conditions for prototype only):** Agree with the calibrated verdict restricting UCI 360 to offline prototype benchmarking (`N1`/`N3`). Overrule any attempt to treat `C6H6(GT)` as clean: all `-200` sentinel values (366 rows) must be converted to null alongside `CO(GT)`, `NOx(GT)`, and `NO2(GT)`, and `NMHC(GT)` (~90% missing) dropped.

## Dataset Link Verdicts & Gate Decisions
1. **`https://archive.ics.uci.edu/dataset/360/air+quality` (`link.uci_360`) - Accepted at gate -> `feasible_with_conditions`:** Usable only for prototype/offline benchmarking after `-200` sentinel cleaning, attribution to De Vito et al. (2008), and Legal clearance of the research-only note.
2. **`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sdg_11_52?format=JSON&lang=EN&geo=IT` (`link.europa_sdg_11_52_099aa6`) - Accepted at gate -> `not_feasible`:** Annual grain (`COV-GRAIN-MISMATCH`), 0% coverage of 2024-2025 production (`COV-PARTIAL-WINDOW`), and unresolved Eurostat copyright notice (`LIC-UNKNOWN`).
3. **`https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations` (`link.data_open_air_chicago_hour_aggre_d4970b`) - Accepted at gate on purpose -> `not_feasible`:** Refused with `DOMAIN_NOT_ALLOWLISTED` (`ACC-UNREACHABLE`) and wrong geography (`COV-GEO-MISMATCH`, Chicago US vs northern Italy). The refusal is recorded as a finding.
4. **`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hlth_cd_iap?format=JSON&lang=EN&geo=IT` (`link.europa_hlth_cd_iap_e7ca1d`, Step 2b accepted) - Accepted at gate -> `not_feasible`:** Same annual grain and 2005-2023 window limitation for production `N6` context.

## Overall Gate Decision
- **Verdict:** `proceed_with_conditions` (recorded in `outputs/UC1/signoff.json`).
