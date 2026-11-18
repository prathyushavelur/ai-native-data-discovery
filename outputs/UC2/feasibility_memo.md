## 1. Executive summary

Overall verdict: **not feasible today** for UC2. Two must needs are unmet (N2 and N3). The verdict would move to feasible with conditions if the weather licence is cleared, a product-code crosswalk is built, and a licensed holiday source is found.

Facts that drive it:

1. **N3 (daily max temperature, must) is unmet.** The only candidate is Open-Meteo. Its free tier is restricted to non-commercial use (terms page, licence.commercial_use = "no"). The client is a commercial shop and no paid subscription exists.
2. **N2 (product code mapping, must) is unmet.** Codes ending in "L" were replaced on 2024-04-01. The wiki says no mapping table exists. The product list holds current codes only. The history window (2023-06-01 onward) straddles the change.
3. **N1 (daily sales by product, must) is met with conditions.** `internal.sales.daily_by_product` is the only source for units and revenue. Access is not yet granted and was not tested. Closed-day semantics and the 2024-02-05 to 2024-03-10 till outage are undocumented.
4. **N4 (public holidays, should) is unmet.** The Nager.Date API has no licence statement for the holiday data itself. Its 2025 calendar was not probed, although 2025 falls inside both windows.
5. **N5 (shop calendar, should) is met with conditions.** Row count (about 1,500) is below the roughly 1,750 days in the declared coverage. The meaning of `is_open` and `event_name` is not documented.

## 2. Need coverage

| need id | need | priority | status | best source(s) | gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met with conditions | internal.sales.daily_by_product | Access approval pending. Closed-day semantics and the 2024 outage need confirmation. |
| N2 | Mapping of product codes before and after the 2024 code change | must | unmet | internal.sales.products; internal.sales.daily_by_product | No documented mapping. A Retail Operations crosswalk must be built and signed off. Names are not unique. |
| N3 | Daily maximum temperature | must | unmet | api.open_meteo_archive | Only candidate. Free tier is non-commercial. No paid subscription. Coordinates are an assumption. |
| N4 | Public holidays in Italy | should | unmet | api.nager_public_holidays; internal.store.calendar | Nager has no data licence on record. Calendar holds no national holidays. 2025 not probed. |
| N5 | Shop opening days and local events | should | met with conditions | internal.store.calendar | Access pending. Completeness and field semantics unverified. |

## 3. Source assessments

### internal.sales.daily_by_product
- **What it is:** Till-system export of units and revenue (EUR) per product code per day for the shop. About 310,000 rows. Owner: Retail Operations. Catalog coverage starts 2022-01-01, open-ended, daily refresh (last refreshed 2026-10-14). Data was not accessed.
- **Verdict:** feasible with conditions.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required, classification confidential. Reachability not tested.
  - INT-JOIN-KEY-MISMATCH (major): no mapping between old and new codes (wiki product_codes_2024).
  - DQ-UNDOCUMENTED-SCHEMA (major): no closed-day field. Unclear whether closed days are absent rows or zero rows.
  - DQ-SEMANTIC-ENCODING (major): wiki says treat the 2024-02-05 to 2024-03-10 outage as missing, not zero. It does not separate outage from closure.
- **Conditions:** Retail Operations approves access. Confirms closed-day encoding and outage scope. Builds the N2 crosswalk. Confirms earliest sale date (catalog says 2022-01-01, unverified) and runs a column-level profile on a capped sample.

### internal.sales.products
- **What it is:** Static product master of current product codes, names and categories. About 64 rows. Owner: Retail Operations. Last metadata update 2025-03-31. No temporal coverage recorded.
- **Verdict:** feasible with conditions, as a supporting reference only.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required, classification internal. Access not tested.
  - INT-JOIN-KEY-MISMATCH (major): current codes only. Cannot join pre-2024-04-01 "L" codes.
- **Conditions:** Access granted to analytics. Use for current names and categories in the recent window and as a building block for the N2 crosswalk. Do not use as N2 evidence on its own. Verify the row count and whether the 2025-03-31 refresh added legacy codes.

### internal.store.calendar
- **What it is:** Daily calendar of shop open/closed status and local events. Owner: Store Operations. Catalog coverage from 2022-01-01, open-ended. Last refreshed 2026-10-10, weekly cadence. Holds no sales, temperature or national holiday data.
- **Verdict:** feasible with conditions.
- **Key flags:**
  - ACC-RESTRICTED (major): auth required, classification internal. Reachability not tested.
  - DQ-UNDOCUMENTED-SCHEMA (major): one-line field descriptions. Unknown whether `is_open = false` means closure or missing, and whether `event_name` is the event date or the announcement date.
  - DQ-METADATA-CONTRADICTION (major): row count about 1,500 against about 1,750 calendar days from 2022-01-01 to 2026-10-10.
- **Conditions:** Store Operations approves access. Confirms one row per day for 2023-06-01 to 2026-03-31. Documents `is_open` and `event_name`. Treats absent days as missing, not closed. Cross-checks holiday flags once a holiday source exists.

### api.open_meteo_archive
- **What it is:** Modelled (reanalysis) daily maximum temperature at a single point, endpoint archive-api.open-meteo.com/v1/archive. Probe returned a 9 km-class grid cell (45.448N, 9.169E, 138 m), not a station. Probes used Milan-area placeholder coordinates. Owner: not stated.
- **Verdict:** not feasible.
- **Key flags:**
  - LIC-NONCOMMERCIAL (blocker): the terms page says the free API is for non-commercial use only. Commercial use is "no".
  - LIC-MIXED (major): the register records `not_required_open_data` with production approved. This conflicts with the terms page. The register is less specific and the terms page governs. Both are recorded here. The terms page is undated.
  - DQ-METADATA-CONTRADICTION (major): same conflict, unresolved.
  - COV-GEO-MISMATCH (major): shop city unknown. Grid cell may not match the shop.
- **Conditions:** Commercial subscription, with Legal written confirmation that it covers production use. Shop coordinates confirmed and recorded in decisions.md. Do not use the register default (Lisbon). Attribution "Weather data by Open-Meteo.com" shown when used. Coverage 2023-06-01 to 2026-03-31 was checked only at sample dates.

### api.nager_public_holidays
- **What it is:** Public REST endpoint for national public holidays in Italy (v3). Owner: Nager.Date open-source project. One row per holiday, national scope only. No regional or patron-saint days.
- **Verdict:** not feasible.
- **Key flags:**
  - LIC-UNKNOWN (blocker): licence.name is null. The only licence seen is MIT for the software repository, not the data. Commercial use unknown. Register "not_required_open_data" is not a licence statement.
  - GOV-PURPOSE-LIMITATION (major): register lists prototyping and production, but production still needs Legal sign-off.
  - DQ-METADATA-CONTRADICTION (major): record counts are 13 (2023), 13 (2024), 14 (2026). The difference is unexplained. The 2025 calendar was not probed.
  - FRS-METADATA-DATE-MISLEADING (minor): no last-updated date. Refresh cadence unknown.
- **Conditions:** Written licence or terms statement covering the holiday data (not the software repo). Reconcile counts against an official Italian calendar, including 2025. Confirm whether v3 is deprecated (README mentions v4). Check whether any holiday falls on a Sunday.

## 4. Red-flag register

| source_id | code | severity | evidence | raised by (rule or judgement) |
|---|---|---|---|---|
| api.open_meteo_archive | LIC-NONCOMMERCIAL | blocker | Terms: free API non-commercial only. Commercial use "no". | rule |
| api.open_meteo_archive | LIC-MIXED | major | Register says production approved. Terms say non-commercial. Unresolved. | rule |
| api.open_meteo_archive | DQ-METADATA-CONTRADICTION | major | Register "not_required_open_data" vs terms paid plan for commercial use. | judgement |
| api.open_meteo_archive | COV-GEO-MISMATCH | major | Placeholder coordinates. Shop city unknown. Model cell, not station. | judgement |
| api.nager_public_holidays | LIC-UNKNOWN | blocker | No licence for the data. Commercial use unknown. | rule |
| api.nager_public_holidays | DQ-METADATA-CONTRADICTION | major | 13 / 13 / 14 records by year. 2025 not probed. | judgement |
| api.nager_public_holidays | GOV-PURPOSE-LIMITATION | major | Production use needs Legal sign-off. | judgement |
| api.nager_public_holidays | FRS-METADATA-DATE-MISLEADING | minor | No last-updated date. Cadence unknown. | judgement |
| internal.sales.daily_by_product | ACC-RESTRICTED | major | Confidential. Access request needed. Not tested. | rule |
| internal.sales.daily_by_product | INT-JOIN-KEY-MISMATCH | major | No old-to-new code mapping (wiki). | judgement |
| internal.sales.daily_by_product | DQ-UNDOCUMENTED-SCHEMA | major | No closed-day field. Absent vs zero rows unknown. | judgement |
| internal.sales.daily_by_product | DQ-SEMANTIC-ENCODING | major | 2024-02-05 to 2024-03-10 outage. Outage vs closure not separated. | judgement |
| internal.sales.products | ACC-RESTRICTED | major | Internal. Access not tested. | rule |
| internal.sales.products | INT-JOIN-KEY-MISMATCH | major | Current codes only. | judgement |
| internal.store.calendar | ACC-RESTRICTED | major | Internal. Reachability not tested. | rule |
| internal.store.calendar | DQ-UNDOCUMENTED-SCHEMA | major | `is_open` and `event_name` undefined. | judgement |
| internal.store.calendar | DQ-METADATA-CONTRADICTION | major | About 1,500 rows vs about 1,750 days. | judgement |

## 5. Conditions and owners

| condition | source(s) | who can resolve it | blocking which need |
|---|---|---|---|
| Commercial Open-Meteo subscription, plus Legal written confirmation for production use | api.open_meteo_archive | Shop owner (purchase); Legal | N3 |
| Shop city or coordinates confirmed and recorded in decisions.md | api.open_meteo_archive | Shop owner | N3 |
| Written licence or terms covering holiday data itself | api.nager_public_holidays | Legal or data owner (Nager.Date) | N4 |
| Licensed alternative holiday source, if Nager is not cleared | api.nager_public_holidays | Analytics lead with Legal | N4 |
| 2025 holiday calendar probed and counts reconciled | api.nager_public_holidays | Analytics team | N4 |
| Product code crosswalk pre/post 2024-04-01, signed off | internal.sales.daily_by_product; internal.sales.products | Retail Operations with Store Operations | N2 (and N1 for product-level history) |
| Analytics access approved and reachability tested | internal.sales.daily_by_product; internal.sales.products; internal.store.calendar | Retail Operations (sales, products); Store Operations (calendar) | N1, N2, N5 |
| Closed-day encoding and 2024 outage scope confirmed | internal.sales.daily_by_product | Retail Operations | N1 |
| `is_open` and `event_name` semantics documented; one row per day confirmed | internal.store.calendar | Store Operations | N5 |

## 6. Recommended next steps

1. Raise an access request with Retail Operations for the daily sales table and the product list. Ask for reachability to be tested.
2. Raise an access request with Store Operations for the shop calendar.
3. Ask Retail Operations to build and sign off the pre/post-2024-04-01 product code crosswalk. Ask them to state whether closed days are absent rows or zero rows, and to confirm the 2024 outage scope.
4. Ask Legal for a decision on Open-Meteo. Either buy a commercial subscription and get written production clearance, or record N3 as blocked.
5. Ask Legal or the data owner for a written licence statement for the Nager holiday data. If none, identify a licensed holiday source.
6. Decide the shop location for weather coordinates and record it in decisions.md.
7. Once the gate is passed, profile in this order: (a) the calendar, for one row per day and the `is_open` encoding; (b) the sales table on a capped sample, for closed-day and outage rows, negative units, zero-unit rows and duplicates; (c) the product list against the crosswalk; (d) the weather series at the chosen coordinates, for coverage over both windows; (e) the 2025 holiday calendar.
8. Re-run this discovery when the blockers clear, to update the verdict.

## 7. Open questions for the human reviewer

1. Will the business pay for a commercial Open-Meteo subscription, and does Legal accept it for production use?
2. Which city is the shop in? Coordinates for the weather call depend on it.
3. Will Retail Operations build and sign off the product code crosswalk, and by when?
4. Does Legal accept the Nager data licence position, or is a licensed holiday source needed?
5. Are closed days absent rows or zero-sale rows in the till export? Is the 2024-02-05 to 2024-03-10 gap only an outage?
6. Does `is_open = false` mean closure, and is `event_name` the event date or the announcement date?
7. Does the shop close on any public holiday or Sunday, and does the calendar record that?
8. Is the Nager v3 endpoint deprecated, and which version should be used?

Note on source records: no source states a data owner or refresh cadence for the Open-Meteo and Nager records. These are recorded as unknown, not inferred.

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-18T06:17:44Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. Will the business pay for a commercial Open-Meteo subscription, and does Legal accept it for production use?
2. Which city is the shop in? The weather coordinates depend on it.
3. Will Retail Operations build and sign off the pre/post-2024-04-01 product code crosswalk, and by when?
4. Does Legal accept the Nager data licence position, or is a licensed holiday source needed?
5. Are closed days absent rows or zero-sale rows in the till export? Is the 2024-02-05 to 2024-03-10 gap only a till outage?
6. Does is_open = false mean closure, and is event_name the event date or the announcement date?
7. Does the shop close on public holidays or Sundays, and does the calendar record that?
8. Is the Nager v3 endpoint deprecated, and which version should be used?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
