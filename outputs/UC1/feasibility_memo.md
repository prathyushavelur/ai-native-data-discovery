
# UC1 Initial Data-Feasibility Memo: Air quality and traffic

**Client:** Valdena Civic Health Office (fictional, northern Italy)
**As-of date:** 2026-10-15
**Basis:** Discovery run generated 2026-11-18 (model claude-haiku-5-5), catalog export, wiki pages, register entries, dataset links and record summaries. No whole-dataset downloads. Only metadata and a capped sample of the UCI file were read.

## 1. Executive summary

**Verdict: feasible with conditions. The method can be prototyped only after one licence question is answered, and production depends on four internal access grants and data fixes. No source is cleared without conditions.**

Facts driving the verdict:

1. **All three must needs (N1, N2, N3) are met only with conditions.** None is unmet, and none is met without conditions. The should need (N4) is also met with conditions. N5 and N6 (could) are unmet.
2. **The prototype rests on one public dataset.** The UCI "Air Quality" dataset (link.uci_360) is the only source for N1 and the N1/N3 hourly readings in 2004-03-10 to 2005-04-04. Its CC BY 4.0 licence conflicts with a "research-only, no commercial use" note on the same page. Legal must confirm use by the client before any prototype work. Until then, N1 prototype is unmet.
3. **Production relies on internal sources that are not yet accessible.** The station readings (N1), traffic counts (N2) and clinic counts (N4) all carry "auth_required" and are unreached. Access reachability was not tested for any of them.
4. **Known data faults must be fixed before profiling.** The station network has a VR-03 outage from 2024-06-30 that the catalog does not show. Traffic counters changed from per-direction to combined counts on 2024-03-18, inside the production window, with no adjustment documented. UCI uses -200 as a missing-value code, and its metadata says there are no missing values.
5. **Two needs have no usable source.** Patient-level records (N5) are excluded by clinic policy. For N6, both Eurostat tables have unresolved licences and end in 2023. The Chicago link is not in Italy and its host was refused.

## 2. Need coverage

| Need ID | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations | must | met with conditions | link.uci_360 (prototype); internal.airq.station_readings (production) | Prototype: one unnamed city, one road-level device, -200 sentinels, research-only note vs CC BY 4.0, Legal confirmation pending. Production: access not granted, VR-03 has no readings after 2024-06-30. |
| N2 | Hourly vehicle traffic near stations | must | met with conditions | internal.traffic.hourly_counts | Access not granted. Counter-to-station mapping absent. Per-direction to combined break on 2024-03-18 inside production window. Municipality not confirmed. |
| N3 | Hourly temperature and humidity | must | met with conditions | api.open_meteo_archive; link.uci_360 (prototype) | Open-Meteo is gridded reanalysis at an undefined Valdena point, with mixed upstream licences. Only 3-day probes run. No station-based weather source found for production. |
| N4 | Daily respiratory clinic visits by district | should | met with conditions | internal.clinic.resp_visits_daily | Access pending. Diagnosis definition, district scheme and small-cell suppression undocumented. Data-sharing basis "to be confirmed". Holiday calendar is not usable until its licence is found. |
| N5 | Patient-level clinic visit records | could | unmet | none | clinic.patient_visits excluded by clinic_data_policy. No other event-level clinic source. |
| N6 | National yearly context: PM2.5 deaths | could | unmet | none | Both Eurostat candidates have unknown licences (LIC-UNKNOWN). Records end 2023, so they do not cover the production window. |

## 3. Source assessments

Order: feasible (none), then with conditions, then not feasible.

### Feasible
No source was rated feasible without conditions.

### With conditions

**internal.airq.station_readings: City station readings (hourly)**
- **What it is (catalog summary):** Hourly NO2 and PM2.5 from the city's own monitoring stations, keyed by station and UTC hour start. About 4.2 million rows. Catalog coverage from 2023-01-01, no end date, hourly refresh. Owner: Environment Monitoring Unit. Licence: internal.
- **Verdict:** feasible with conditions. Covers N1 in production only.
- **Key flags:**
  - ACC-RESTRICTED (major, rule): auth required, request via the Environment Monitoring Unit. Store reachability not tested.
  - GOV-CATALOG-WIKI-CONFLICT (major, judgement): catalog says "active", no end date, hourly refresh (exported 2026-10-14). Wiki station_network (last edited 2024-07-01) says VR-03 was switched off on 2024-06-30 and has no readings after that date.
- **Conditions:** approval from the Environment Monitoring Unit and reachability test; confirm VR-03 status (restored, replaced or retired; if retired, about 18 months missing in production); station list, coordinates and district mapping; pollutant method, QA flags and sentinel encoding (catalog has no QA fields); catalog status update.

**internal.traffic.hourly_counts: Road traffic counts (hourly)**
- **What it is:** Hourly vehicle counts per counter, local time. Catalog coverage from 2021-01-01, no end date, hourly refresh, about 15 million rows. Owner: Mobility Office. Access via warehouse SQL on request. Not sampled.
- **Verdict:** feasible with conditions. The only internal hourly traffic source for N2.
- **Key flags:**
  - ACC-RESTRICTED (major, rule): auth required. Reachability not tested.
  - GOV-CATALOG-WIKI-CONFLICT (major, judgement): wiki counter_replacement_2024 (edited 2024-04-02) says counters were replaced on 2024-03-18 and counting changed from per-direction to combined. Catalog does not mention this. Catalog last refreshed 2026-10-12.
  - COV-GEO-MISMATCH (major, judgement): no counter-to-station mapping or distances. Municipality assumed, not stated.
  - DQ-DST-ARTEFACTS (minor, judgement): ts_local has no documented UTC offset or DST handling.
- **Conditions:** access and schema check; documented adjustment method for the 2024-03-18 break (required, since pre- and post-change counts cannot be compared without it); counter locations and station mapping; confirm Valdena; confirm timezone, DST and outage coding (zero vs missing); add break to catalog.

**internal.clinic.resp_visits_daily: Respiratory visits (daily, by district)**
- **What it is:** Daily respiratory visit counts per district of residence, Azure warehouse, about 40,000 rows. Columns: visit_date, district, visit_count. No patient identifiers per catalog. Coverage from 2022-01-01, no end date, daily refresh. Owner per catalog: Clinical Analytics. Licence: internal.
- **Verdict:** feasible with conditions. The only internal source for N4.
- **Key flags:**
  - ACC-RESTRICTED (major, rule): auth required, request to Clinical Analytics. Store access not tested.
  - GOV-PURPOSE-LIMITATION (major, judgement): wiki clinic_data_policy (edited 2025-02-01) permits only daily district counts for this purpose. Patient postcode and age band must not leave clinic systems.
  - GOV-CATALOG-WIKI-CONFLICT (major, judgement): catalog owner Clinical Analytics; wiki policy owned by Data Protection Office.
  - DQ-UNDOCUMENTED-SCHEMA (major, judgement): diagnosis definition, district scheme and small-cell suppression not documented. District count not stated.
- **Conditions:** access grant and reachability test; written data-sharing basis ("to be confirmed" in candidate note); extract only visit_date, district and visit_count; document diagnosis definition, district scheme and suppression rule, and apply suppression before any output leaves clinic systems; resolve owner conflict.

**api.open_meteo_archive: Open-Meteo Historical Weather API (reanalysis archive)**
- **What it is:** JSON API giving hourly historical weather for any coordinates. Values are gridded reanalysis, not station observations. Probes returned hourly temperature_2m and relative_humidity_2m for 72-hour windows in 2004-03-10 to 2004-03-12 and 2024-01-01 to 2024-01-03. The grid cell was about 0.02 degrees from the requested point. Licence: CC BY 4.0. Owner: unknown.
- **Verdict:** feasible with conditions. Covers N3 in both windows, as a fallback only.
- **Key flags:**
  - LIC-MIXED (major, rule): licence page lists upstream providers with different terms. C3S is shown without a name. UK Met Office is CC-BY-SA.
  - LIC-ATTRIBUTION (minor, rule): attribution "Weather data by Open-Meteo.com" required.
  - COV-GEO-MISMATCH (major, judgement): no Valdena location in any source. Probes used Milan-area coordinates for endpoint testing only, not as a location decision.
- **Conditions:** confirm upstream provider and licence terms; Legal sign-off; set and document a justified Valdena coordinate (register default Lisbon must be overridden); request temperature_2m and relative_humidity_2m explicitly; validate against city station data and run a full-window completeness check. Coverage start 2004-03-10 was probed, not confirmed across the whole archive.

### Not feasible

**link.uci_360: UCI ML Repository 360 "Air Quality" (prototype only)**
- **What it is:** Hourly readings from one road-level multisensor device in an unnamed Italian city, with co-located reference values for CO, NMHC, benzene, NOx and NO2, plus T, RH and AH. Whole file read as a sample: 9,357 rows, 15 columns, 2004-03-10 to 2005-04-04. Licence: CC BY 4.0.
- **Verdict in the discovery record:** feasible with conditions. This assessment sits in section 3 with conditions because it is the only prototype source and the discovery verdict says so. It is conditional on the Legal decision below. If Legal refuses, it becomes not feasible and N1 prototype is unmet.
- **Key flags:**
  - GOV-PURPOSE-LIMITATION (major, judgement): dataset notes say "exclusively for research purposes. Commercial purposes are fully excluded." This conflicts with the CC BY 4.0 field. Commercial use is recorded as unknown.
  - DQ-SENTINEL-VALUES (major, judgement): missing values coded -200. Sample counts include NMHC(GT) about 90% of rows. C6H6(GT) minimum -200 is not counted as missing by the profiler.
  - DQ-METADATA-CONTRADICTION (major, rule): metadata says has_missing_values = no, which contradicts the notes.
  - DQ-UNDOCUMENTED-SCHEMA (major, judgement): documented date format DD/MM/YYYY, sample parses as M/D/YYYY. Sensor columns typed Categorical or Integer. Row count 9,358 documented vs 9,357 in sample.
  - FRS-STALE (major, rule): ends 2005-04-04. Permitted for prototype under calibration rule 5 only.
  - INT-REPRESENTATIVENESS (major, judgement): one station, one device location. Not usable for district joins.
  - COV-GEO-MISMATCH (major, judgement): city not named. Valdena not confirmed.
  - LIC-ATTRIBUTION (minor, rule): citation required (Vito / De Vito et al. 2008, DOI 10.24432/C59K5F).
- **Conditions:** prototype and offline benchmarking only, not production. Recode -200 to null in all columns, including C6H6(GT). Written Legal/UC Irvine confirmation on research-only note. Use GT reference columns only for N1. Describe that the site is not Valdena and that sensor columns are not calibrated.

**api.nager_public_holidays: Nager.Date public holidays API (Italy)**
- **What it is:** REST API returning Italian national public holidays, 13 per year in probes for 2024 and 2025. Regional and municipal closures not covered. Licence: null (only the software MIT licence was found). Owner: null.
- **Verdict:** not feasible (blocker: licence unknown). Under calibration rule 1, the record forces not feasible.
- **Key flags:**
  - LIC-UNKNOWN (blocker, rule): data licence for holiday data and API output not stated. API docs page not read.
  - GOV-OWNER-UNKNOWN (major, judgement): owner, steward and SLA unknown.
  - COV-PARTIAL-WINDOW (minor, judgement): national holidays only.
- **Conditions:** if licence is found, usable only as a calendar covariate alongside N4 counts, not as a substitute. Legal sign-off still needed. N4 can proceed without it.

**link.europa_hlth_cd_iap_e7ca1d: Eurostat hlth_cd_iap (PM2.5 health impacts, Italy, annual)**
- **What it is:** Annual national indicators for PM2.5 health impacts (years of life lost and premature deaths, as number and rate). 72 cells, 2005 to 2023. Last updated 2025-12-09 per Eurostat label.
- **Verdict:** not feasible. Blocker: licence unknown.
- **Key flags:**
  - LIC-UNKNOWN (blocker, rule): copyright page redirected to EU Login, no licence text. Eurostat not on the register.
  - COV-PARTIAL-WINDOW (major, rule): record 2005 to 2023. Prototype overlap only 2005 (24.0%). Production 0.0%. 2006 absent.
- **Conditions:** reconsider only if licence is confirmed and Legal approves. Would serve N6 only.
- **Note:** the candidate note calls this an "accepted Step 2b source". No licence evidence in the record supports that.

**link.europa_sdg_11_52_099aa6: Eurostat sdg_11_52 (premature deaths due to PM2.5, Italy)**
- **What it is:** Annual national premature deaths due to PM2.5, number and rate. 36 cells (18 years x 2 units), 2005 to 2023. Owner unknown. Last updated 2025-12-09.
- **Verdict:** not feasible. Blocker: licence unknown. Also redundant with the parent table.
- **Key flags:**
  - LIC-UNKNOWN (blocker, rule): copyright page returned script only. Licence not established.
  - COV-PARTIAL-WINDOW (major, rule): 2005 to 2023 only. Production 0.0%, prototype 24.0%. 2004 and 2006 missing.
  - INT-DUPLICATE-SOURCE (minor, judgement): likely a subset of the parent table. Values not compared cell by cell.
- **Conditions:** none viable within the project. Superseded by link.europa_hlth_cd_iap_e7ca1d if its licence clears.

**link.data_open_air_chicago_hour_aggre_d4970b: Open Air Chicago hourly aggregations (not profiled)**
- **What it is:** Link to a data.gov entry described as hourly air-quality data from Chicago, USA. Content, schema, period, licence and owner are unverified.
- **Verdict:** not feasible.
- **Key flags:**
  - ACC-UNREACHABLE (blocker, rule): host catalog.data.gov refused (DOMAIN_NOT_ALLOWLISTED). No metadata or files obtained.
  - LIC-UNKNOWN (blocker, rule): licence not read, as the host was refused.
  - COV-GEO-MISMATCH (major, judgement): US city, not Italy. Would not cover Valdena.
- **Conditions:** none pursued. This refusal is a guardrail finding. No alternative route was taken.

## 4. Red-flag register

| Source ID | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| api.nager_public_holidays | LIC-UNKNOWN | blocker | No data licence found; only software MIT licence | rule |
| api.nager_public_holidays | GOV-OWNER-UNKNOWN | major | Owner and steward null | judgement |
| api.nager_public_holidays | COV-PARTIAL-WINDOW | minor | National holidays only | judgement |
| api.open_meteo_archive | LIC-MIXED | major | Mixed upstream licences; C3S unnamed | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | Attribution text required | rule |
| api.open_meteo_archive | COV-GEO-MISMATCH | major | No Valdena point set; grid cell, not station | judgement |
| internal.airq.station_readings | ACC-RESTRICTED | major | Auth required; store not tested | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Catalog "active"; wiki says VR-03 off since 2024-06-30 | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | Auth required; store not tested | rule |
| internal.clinic.resp_visits_daily | GOV-PURPOSE-LIMITATION | major | Only daily district counts permitted | judgement |
| internal.clinic.resp_visits_daily | GOV-CATALOG-WIKI-CONFLICT | major | Owner: Clinical Analytics vs Data Protection Office | judgement |
| internal.clinic.resp_visits_daily | DQ-UNDOCUMENTED-SCHEMA | major | Diagnosis, district scheme, suppression undocumented | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | Auth required; reachability not tested | rule |
| internal.traffic.hourly_counts | GOV-CATALOG-WIKI-CONFLICT | major | 2024-03-18 per-direction to combined break not in catalog | judgement |
| internal.traffic.hourly_counts | COV-GEO-MISMATCH | major | No counter-to-station mapping; municipality not stated | judgement |
| internal.traffic.hourly_counts | DQ-DST-ARTEFACTS | minor | No UTC offset or DST handling documented | judgement |
| link.uci_360 | FRS-STALE | major | Ends 2005-04-04 | rule |
| link.uci_360 | DQ-SENTINEL-VALUES | major | -200 codes in many columns | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Metadata says no missing values; notes say -200 | rule |
| link.uci_360 | DQ-UNDOCUMENTED-SCHEMA | major | Date format conflict; numeric columns typed as categorical | judgement |
| link.uci_360 | GOV-PURPOSE-LIMITATION | major | Research-only note vs CC BY 4.0 | judgement |
| link.uci_360 | COV-GEO-MISMATCH | major | City unnamed; Valdena not confirmed | judgement |
| link.uci_360 | INT-REPRESENTATIVENESS | major | One station, one device | judgement |
| link.uci_360 | LIC-ATTRIBUTION | minor | Citation required | rule |
| link.europa_hlth_cd_iap_e7ca1d | LIC-UNKNOWN | blocker | Licence text not reached | rule |
| link.europa_hlth_cd_iap_e7ca1d | COV-PARTIAL-WINDOW | major | Ends 2023; production 0% covered | rule |
| link.europa_sdg_11_52_099aa6 | LIC-UNKNOWN | blocker | Licence not established | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Ends 2023; production 0% covered | rule |
| link.europa_sdg_11_52_099aa6 | INT-DUPLICATE-SOURCE | minor | Likely subset of parent table | judgement |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | Host refused (DOMAIN_NOT_ALLOWLISTED) | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | Licence not read | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | US city, not Italy | judgement |

## 5. Conditions and owners

Owners below are taken from catalog or wiki records. The discovery run did not assign resolvers.

| Condition | Source(s) | Who can resolve | Blocking which need |
|---|---|---|---|
| Legal/UC Irvine written confirmation on research-only note vs CC BY 4.0 | link.uci_360 | Legal (client) with UC Irvine | N1 prototype; N3 prototype |
| Access approval and reachability test | internal.airq.station_readings | Environment Monitoring Unit (steward Giulia Rossi per record) | N1 production |
| Confirm VR-03 status; correct catalog status | internal.airq.station_readings | Environment Monitoring Unit | N1 production (partial) |
| Station list, coordinates, district mapping | internal.airq.station_readings | Environment Monitoring Unit | N1 production; N4 joins |
| Access and schema check | internal.traffic.hourly_counts | Mobility Office | N2 |
| Documented adjustment for 2024-03-18 break | internal.traffic.hourly_counts | Mobility Office | N2 |
| Counter locations, station mapping, Valdena confirmation | internal.traffic.hourly_counts | Mobility Office | N2 |
| Timezone, DST and outage coding | internal.traffic.hourly_counts | Mobility Office | N2 (partial) |
| Access grant and reachability test | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Written data-sharing basis | internal.clinic.resp_visits_daily | Client / Data Protection Office | N4 |
| Diagnosis definition, district scheme, suppression rule | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Owner conflict resolution | internal.clinic.resp_visits_daily | Clinical Analytics and Data Protection Office | N4 (governance) |
| Valdena coordinate set and documented in decisions.md | api.open_meteo_archive | Analytics lead (client decision) | N3 |
| Upstream provider and licence check; Legal sign-off | api.open_meteo_archive | Legal (client) | N3 |
| Full-window completeness check and station validation | api.open_meteo_archive | Analytics team | N3 |
| Recode -200 to null, including C6H6(GT) | link.uci_360 | Analytics team | N1 prototype |
| Licence statement for holiday data | api.nager_public_holidays | Not identified in record | N4 covariate only (optional) |
| Licence statement for Eurostat tables | link.europa_hlth_cd_iap_e7ca1d; link.europa_sdg_11_52_099aa6 | Legal; Eurostat | N6 |
| Patient-level records | clinic.patient_visits | Excluded by clinic_data_policy | N5 (unmet) |

## 6. Recommended next steps

1. **Raise a Legal request now.** Ask for a written decision on whether the UCI research-only note permits the client's civic health office to use link.uci_360 for the prototype. Prototype work on N1 and N3 waits for this answer.
2. **Raise access requests in parallel:**
   - Environment Monitoring Unit: station_readings access and VR-03 status.
   - Mobility Office: traffic.hourly_counts access, the break adjustment method and counter mapping.
   - Clinical Analytics: resp_visits_daily access, with the Data Protection Office copied on the policy boundary.
3. **Take the decisions below to the Health Office.**
   - Choose and justify the Valdena coordinate. Record it in decisions.md. Override the Lisbon default. No Valdena coordinate was set in this run.
   - Decide whether N5 (patient-level) stays unmet. Policy excludes it.
   - Decide whether N6 is worth pursuing, given both Eurostat licences are unknown and coverage ends 2023.
   - Decide whether the holiday calendar is needed at all, since its licence is unknown.
4. **Start Legal review of Open-Meteo.** Confirm the upstream provider, licence terms and attribution, and document the Valdena point.
5. **Profiling order once the gate is passed:**
   1. Test store reachability for all three internal sources. Nothing else can start without this.
   2. Station readings: check VR-03 after 2024-06-30 and the sentinel encoding.
   3. Traffic counts: check the 2024-03-18 break and timezone handling.
   4. Clinic counts: check the district scheme and suppression.
   5. UCI (only if cleared): recode -200 and check the date format.
   6. Open-Meteo: full-window completeness check against the city station data.
6. **Do not proceed** with the Chicago link or the Eurostat tables for production. Do not work around the refused host.

## 7. Open questions for the human reviewer

1. Does the UCI "research-only, commercial purposes excluded" note allow the civic health office to use link.uci_360 for the prototype, given CC BY 4.0 is also stated? Legal must answer this.
2. Which latitude and longitude should represent Valdena for the Open-Meteo calls? No source names the city, and this has not been decided.
3. Has VR-03 been restored, replaced or permanently retired since 2024-06-30? This decides whether about 18 months of N1 production data are missing at that station.
4. What adjustment method should be used for the 2024-03-18 traffic counter change, and are the counters located in Valdena?
5. Does the client have a written data-sharing basis for the daily clinic counts? Who owns the clinic source: Clinical Analytics or the Data Protection Office?
6. Who is the licence holder for the Nager holiday data, and is the calendar covariate worth pursuing at all?
7. Is there any licence statement for the Eurostat tables that Legal can accept? If not, should N6 be dropped?
8. Is N5 (patient-level records) confirmed out of scope, given the clinic policy?
9. Should the prototype proceed on UCI alone if Legal says no, or should N1 prototype wait for production data?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-18T06:52:37Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. Does the UCI 'research-only, commercial purposes excluded' note allow the civic health office to use link.uci_360 for the prototype, given the CC BY 4.0 licence field? Legal/UC Irvine must answer.
2. Which latitude and longitude should represent Valdena for the Open-Meteo calls? No source names the city; no Valdena coordinate was set in this run.
3. Has station VR-03 been restored, replaced or permanently retired since 2024-06-30? This determines whether about 18 months of production N1 data are missing at that station.
4. What adjustment method should be used for the 2024-03-18 traffic counter change (per-direction to combined), and are the counters located in Valdena?
5. Is there a written data-sharing basis for the daily clinic counts, and who owns the clinic source (Clinical Analytics or the Data Protection Office)?
6. Who holds the licence for the Nager.Date holiday data, and is the holiday calendar covariate worth pursuing at all?
7. Is there any Eurostat licence statement Legal can accept? If not, should N6 be dropped?
8. Is N5 (patient-level records) confirmed out of scope under the clinic data policy?
9. If Legal does not clear the UCI dataset, should N1 prototype wait for production data or proceed another way?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
