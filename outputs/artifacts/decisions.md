# Decisions log

## Source suggestions (Step 2b)
One row per suggestion you accepted, rejected or revised, with your reason. Use the page's own wording for the reason.

| Suggestion (publisher, URL) | Need, window | Decision | Reason |
|---|---|---|---|
| Eurostat (`ec.europa.eu`), `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hlth_cd_iap?format=JSON&lang=EN&geo=IT` | N6, prototype/production | accept | Page states "Health impacts of air pollution" (`ESTAT`, annual `2005`-`2023`, `PM2_5`, `YLL` and `PMD` for `IT`); accepted as parent Eurostat table of `sdg_11_52` for N6 macro health context. |
| EEA Discomap (`discomap.eea.europa.eu`), `https://discomap.eea.europa.eu/map/fme/AirQualityExport.htm` | N1, prototype/production | reject | Page covers national EU Air Quality e-Reporting (`E1a`/`E2a`) rather than Valdena's local civic station network, and host is outside our minimal allowlist. |
| OpenAQ (`openaq.org`), `https://openaq.org/` | N1, prototype/production | reject | Third-party aggregator with heterogeneous upstream regional ARPA licences and host outside the minimal allowlist. |

Inspected through the workflow (at least one accepted extra source): `link.europa_hlth_cd_iap_e7ca1d` (`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hlth_cd_iap?format=JSON&lang=EN&geo=IT`) was inspected via `python -m discovery_agent tool inspect_dataset_link`, added to `outputs/UC1/links.json` and `outputs/UC1/gate_decisions.json`, and profiled via `--from-stage profile --only link.europa_hlth_cd_iap_e7ca1d`.

## G1 and G3: one edge case in each function
- **G1, `extract_licence`**: When a portal landing page (such as the Kaggle fixture `kaggle_dataset_landing_page.html`) embeds schema.org JSON-LD with `"license": "Unknown"`, `extract_licence` explicitly treats `"Unknown"` (and empty/placeholder strings) as missing rather than a valid licence name, returning `licence_name: null`, `found_in: "json-ld"`, and preserving the `"Unknown"` snippet so `rule_licence` raises `LIC-UNKNOWN` instead of falsely passing a dataset without verified terms.
- **G3, `jsonstat_summary`**: When a JSON-stat 2.0 response provides `value` as a dense list containing `None` entries (missing cells) alongside a `status` dictionary and dict-form dimension category indexes (`{"2011": 1, "2010": 0}`), `jsonstat_summary` sorts category codes by their integer index order (`["2010", "2011"]`), counts non-null entries in `value_count` without treating `None` as `0`, increments `missing_cells`, tallies `status_counts`, and emits `MISSING_CELLS` and `NON_ISO_GEO_CODES` (when Eurostat codes like `EL` or `UK` appear).

## G4-G5: feasible for one need or window, not another
- **Source and the rule or calibration decision:** `link.uci_360` (UCI Air Quality dataset 360) evaluated under `rule_temporal_coverage` (G4) and Calibration Rules 3 and 5 (G5).
- **Feasible for (need, window), and why:** Feasible with conditions for `N1` (and secondary `N3`) in the `prototype` window (`2004-03-10` to `2005-04-04`). Although `rule_temporal_coverage` raises `FRS-STALE` (data ends 21.5 years before `as_of = 2026-10-15`), Calibration Rule 5 specifies that stale public benchmarks targeted at a historical `prototype` window are `feasible_with_conditions` for offline method building once `-200` sentinels are cleaned and Legal clears the research-only note.
- **Not feasible for (need, window), and why:** Not feasible for `N1` in the `production` window (`2024-01-01` to `2025-12-31`), because `2004-03-10..2005-04-04` has zero overlap with `2024-01-01..2025-12-31` (`COV-OUT-OF-WINDOW`), which Calibration Rule 3 classifies as `not_feasible`.
- **Reason for each red flag you dismissed:** No deterministic rule flags were silently dropped; minor operational/DST notes on `internal.traffic.hourly_counts` (`DQ-DST-ARTEFACTS`) and attribution notes (`LIC-ATTRIBUTION`) were retained as `minor` flags and addressed via ingestion conditions rather than blocking feasibility.

## G6: Allowlist changes
Exact hosts only. For each host: what it provides and why a broader domain is not needed.

| Host added | Needed for (source, page) | Why nothing broader | Date |
|---|---|---|---|
| `ec.europa.eu` | `link.europa_sdg_11_52_099aa6` and `link.europa_hlth_cd_iap_e7ca1d` (Eurostat JSON-stat API and copyright notice) | Exact host serves both Eurostat API endpoints and copyright pages; avoids broadening to `europa.eu` or wildcarding unrelated EU institutions. | 2026-11-18 |

Hosts you chose **not** to add, and why:
- `catalog.data.gov`: Host for the Chicago US air-quality distractor link (`link.data_open_air_chicago_hour_aggre_d4970b`). Intentionally excluded so the guardrail refusal (`DOMAIN_NOT_ALLOWLISTED`) is recorded as a finding, and Chicago data fails `UC1` geography (`IT`).
- `discomap.eea.europa.eu` and `openaq.org`: Step 2b search candidates rejected during screening because Valdena requires local municipal station data rather than national/aggregated portals.

## G5: Verdict calibration
- **What you changed in `prompts/risk_assessor.md`, and the reasoning behind each rule:** Added 9 explicit numbered rules under `## Verdict calibration rules` covering: (1) unresolved `blocker` flags forcing `not_feasible`, (2) scoped consent gaps requiring an explicit filterable consent flag, (3) zero overlap across all target windows forcing `not_feasible`, (4) `COV-PARTIAL-WINDOW` resolving to `feasible_with_conditions` with explicit uncovered-date fallbacks, (5) `FRS-STALE` public benchmarks targeted at historical `prototype` windows resolving to `feasible_with_conditions` instead of `not_feasible`, (6) `COV-GRAIN-MISMATCH` forcing `not_feasible` on core `must` needs, (7) actionable `major` flags (`ACC-RESTRICTED`, `DQ-SENTINEL-VALUES`, `DQ-METADATA-CONTRADICTION`, `INT-JOIN-KEY-MISMATCH`, `LIC-MIXED`) resolving to `feasible_with_conditions` with named owners, (8) superseded duplicates (`INT-DUPLICATE-SOURCE`), and (9) `minor`-only flags permitting `feasible`.
- **Verdicts that changed after you re-ran `--from-stage assess` (source: before -> after, why):** `link.uci_360` (`not_feasible` -> `feasible_with_conditions` for `prototype` benchmarking under Rule 5 instead of being rejected for `FRS-STALE`), and `api.open_meteo_archive` in UC2 (`feasible` -> `not_feasible` under Rule 1 because `LIC-NONCOMMERCIAL` blocks commercial retail production without a paid subscription).

## G7: One agent failure, fixed at its cause
- **Symptom (what was wrong in the output):** Multiple Profiler agents (`profiler__api.open_meteo_archive`, `profiler__link.uci_360`, `profiler__link.europa_sdg_11_52_099aa6`) failed their initial `submit_catalog_record` tool call with JSON schema validation errors (`'unknowns' is a required property`, `provenance: '[...]' is not of type 'array'`, and unallowed extra keys such as `temporal.start_date_note` and `ownership.notes`), causing wasted retry turns and inflated token usage.
- **Evidence (trace event or transcript excerpt, with file and line or turn):** `outputs/UC1/trace.jsonl` line 63 (`profiler__api.open_meteo_archive`, `"ok": false`), line 92 (`profiler__link.europa_sdg_11_52_099aa6`, `"ok": false`), line 98 (`profiler__link.uci_360`, `"ok": false`), and lines 204 & 206 (`"ok": false`).
- **Root cause (prompt, tool description, validator, rule, or missing tool):** `discovery_agent/prompts/profiler.md` listed semantic field guidelines but did not instruct the model that `submit_catalog_record` validates strictly against `additionalProperties: false` and requires `provenance`, `unknowns`, `documentation_excerpts`, and `quality_notes` to be native JSON arrays rather than JSON-encoded strings.
- **Fix (file and diff summary):** Added a `## Submission schema rules` section to `discovery_agent/prompts/profiler.md` requiring native JSON arrays for list fields, all mandatory top-level keys, and strict adherence to allowed schema properties.
- **Re-run (command):** `python -m discovery_agent run --use-case UC1 --from-stage profile --links-file outputs/UC1/links.json --no-input`
- **Before / after (measured):**
  - Before (`run_history.jsonl` entry `2026-11-18T06:35:00Z`): `profile` stage took `84.0s`, `30` LLM calls, `340,513` input tokens, `62,465` output tokens, `26` tool calls, `3` tool errors; both `profiler__api.open_meteo_archive` and `profiler__link.uci_360` failed Turn 1 `submit_catalog_record`.
  - After (`run_history.jsonl` entry `2026-11-18T06:46:34Z`): `profile` stage took `66.2s`, `27` LLM calls, `295,241` input tokens, `57,734` output tokens, `23` tool calls, `2` tool errors - saving `17.8s`, `3` LLM calls, `45,272` input tokens, and `4,731` output tokens, with `profiler__api.open_meteo_archive` (trace line 268) and `profiler__link.uci_360` (trace line 282) passing schema validation on their first submit attempt.
- **Decision this failure could affect:** Eliminates premature turn-limit failures (`no valid submit_catalog_record after N turns`) that would otherwise omit a valid source record from `discovery_results.json` and falsely mark a `must` need as `unmet`.
- **Related source or test checked:** Verified `profiler__link.uci_360` and `profiler__api.open_meteo_archive` in `outputs/UC1/trace.jsonl` (both `ok: true` on first submit) and confirmed `pytest tests/ -v` passes all 52 tests.

## Other decisions
- Kept all caps and request budgets in `config/settings.json` unchanged, and kept default coordinates in `config/external_sources_register.json` unchanged while flagging the placeholder coordinates as an open condition for Valdena Civic Health Office and Valdena Gelato Shop.
