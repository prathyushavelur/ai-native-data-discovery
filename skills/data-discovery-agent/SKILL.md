---
name: data-discovery-agent
description: >
  Reusable skill for Stack AI Rewire, Assignment: AI-Native Data Discovery. Runs the first
  stage of any AI/DS project: locate, catalog and assess the feasibility of internal and
  external data sources for a business problem, before any pipeline is built. Works for
  any use case written to the use-case contract (use_cases/<ID>_*.json + brief + internal
  estate). It sets up and checks the agent, frames the use case, runs planning and scouting,
  suggests external sources for unmet needs (Step 2b), then pauses for human review. It
  deliberately does NOT cover profiling, risk assessment, the memo or the learner gaps (G1–G7).
  The learner builds those with Claude directly, and the learner's deliverable includes
  extending this file with Steps 3–5.
---

# AI-Native Data Discovery: Assignment Runner (Steps 0–2b only)

You are Claude, running the first steps of **Stack AI Rewire, Assignment: AI-Native Data
Discovery** in Claude Code, against the learner's copy of this repo. The repo
contains a multi-agent discovery system (`discovery_agent/`): Planner → Scout (internal catalog,
wiki, external register) → **candidate gate, where the human adds dataset links (any URL)** →
Profiler (one per source) → deterministic rules → Risk Assessor → Memo Writer, then a human review gate.

This skill gets a use case ready, checks the tooling, runs **plan + scout**, and suggests external
sources for the needs that remain unmet (Step 2b). Profiling, red-flag assessment, the feasibility
memo and the learner gaps are done in a normal Claude Code session, guided by `README.md`.

The skill is **use-case agnostic**. UC1 (air quality and traffic) and UC2 (ice-cream sales, weather and holidays) ship with
the repo, but any business problem written to the contract below runs the same way.

## Required input
- `use_cases/<ID>_<slug>.json`: the machine-readable use case (windows, needs, grains, geography).
  Contract: `use_cases/_TEMPLATE_use_case.json`.
- `use_cases/<ID>_<slug>.md`: the business brief: problem, decisions supported, scope, out of scope.
- `internal/<ID>_<client>/catalog_export.json` + `internal/<ID>_<client>/wiki/*.md`: the client's
  internal catalog export and documentation (metadata only, never data values).
- `config/external_sources_register.json`: the external sources the client has agreements for or
  has approved, tagged with the use case id.
- **Dataset links** (any https URL): supplied by the human at the candidate gate, from their own
  search or accepted from the Step 2b suggestions. For UC1 and UC2, README.md section 4 lists links
  whose expected assessment is known.
- **The learner's search script** `scripts/web_search.py` for Step 2b. It is not provided: the learner
  generates it with Claude Code (Assignment Task 3; the prompt is in README.md, section 4, "Suggest
  sources (Step 2b)"). Claude Code's built-in `WebSearch` does not work with the gateway key, so do not
  use it. If the script is missing, fails, or returns no citations, stop at Step 2b and tell the learner
  to generate or fix it. Do not write suggestions without search results.
- `config/allowlist.json`, `config/red_flags.json`, `config/settings.json`: provided. Do not loosen
  the allowlist or the caps to make a run pass.
- Gateway credentials in the environment: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_MODEL`. Never print, log or commit the token.

## Repo scaffold this skill produces
```
.
├── use_cases/<ID>_*.json, <ID>_*.md         <- provided, or written by you in Step 1 (new use case)
├── internal/<ID>_<client>/                  <- provided, or assembled in Step 1 (new use case)
├── outputs/<ID>/
│   ├── use_case_validation.txt              <- Step 1
│   ├── search_plan.json                     <- Step 2 (Planner)
│   ├── candidates.json                      <- Step 2 (Scout)
│   ├── trace.jsonl, transcripts/            <- Step 2 (evidence of every LLM/tool/HTTP call)
│   ├── run_summary.json                     <- Step 2 (tokens, tool calls, warnings)
│   ├── links.json                           <- Step 2 (copy of the prescribed links) and Step 2b (accepted suggestions appended): the ONE links file
└── outputs/artifacts/step0_checks.md        <- Step 0
```
Everything after `candidates.json` (records/, rule_flags.json, risk_assessment.json,
discovery_results.json, feasibility_memo.md) is produced later, outside this skill.

---

## Step 0: Set up and check the tooling (no LLM calls)
1. If no environment is active: `python3 -m venv .venv && source .venv/bin/activate`, then
   `pip install -r requirements.txt`.
2. Check that the gateway variables are **set**, without printing their values:
   `python -c "import os;print({k: bool(os.environ.get(k)) for k in ['ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_MODEL']})"`.
   If any is `False`, stop and tell the learner which one. Do not ask them to paste the token.
3. Run the offline tests: `python -m pytest tests/ -q`. `tests/test_tools_offline.py` and
   `tests/test_agent_loop.py` must pass. `tests/test_learner_gaps.py` is **expected to fail** until
   the learner implements G1, G3, G4, G5 and G6. Report which gap tests fail; do not implement them here.
4. Smoke-test the tools without the LLM:
   - `python -m discovery_agent tool search_internal_catalog '{"query": "<a need from the brief>"}' --use-case <ID>`
   - `python -m discovery_agent tool inspect_dataset_link '{"url": "https://archive.ics.uci.edu/dataset/360/air+quality"}' --use-case <ID>`
   - `python -m discovery_agent tool list_external_register '{}' --use-case <ID>`
   Each must return JSON, not a traceback. A `DOMAIN_NOT_ALLOWLISTED` result is the guardrail
   working, not a bug.
5. Write `outputs/artifacts/step0_checks.md`: test results (pass/fail counts per file), the tool
   smoke results (one line each), and the model id in use. Never write the token.

## Step 1: Frame the use case against the contract
**Existing use case** (UC1 or UC2, where `use_cases/<ID>_*.json`
and `internal/<ID>_*/` already exist): check that the files exist, then do item 4 and item 5 below.
Do not rewrite a contract that someone else wrote. If item 4 fails, report the error and ask the
learner before you change any input.

**New use case** (the learner gives you a business problem): write the inputs, do not invent data.
1. Copy `use_cases/_TEMPLATE_use_case.json` to `use_cases/<ID>_<slug>.json` and fill every field:
   - `windows`: one per analysis period, with ISO dates and a purpose. Do not use a single
     open-ended window to dodge coverage checks.
   - `needs`: one row per data need, in business words, with `priority` (must/should/could),
     `min_grain` (one of `minute, 15min, 30min, hourly, daily, weekly, monthly, quarterly, annual,
     event, static`) and the `windows` it applies to. Aim for 5–12 needs. Split compound needs.
   - `as_of`: the date the discovery is valid for. It drives staleness checks.
2. Write `use_cases/<ID>_<slug>.md` with the same sections as the UC1 brief: business problem,
   decisions supported, scope, needs table, where to look, out of scope.
3. Internal estate: if the learner has a real catalog export, convert it to the
   `catalog_export.json` entry shape used in `internal/UC1_valdena_health/` (null where the catalog
   holds nothing, never a guess), and put the documentation pages in `wiki/` with the same front
   matter (`page_id`, `title`, `owner`, `last_edited`). Add the client's approved external sources
   to `config/external_sources_register.json` with the new use-case id and their real
   `agreement_status`. If the learner has no internal estate, stop and ask. Do not fabricate one.
4. Validate: `python -m discovery_agent validate-use-case <ID> | tee outputs/<ID>/use_case_validation.txt`.
   Fix every error it reports in the inputs, not in the validator.
5. Show the learner the needs table (id, name, priority, min_grain, windows) and the windows.
   **Pause** (for a human learner in an interactive session; in a non-interactive run, write the table and stop). Wait for them to confirm or change it. The needs list decides what the agents
   search for and what the rules check, so a wrong need here gives wrong verdicts later.

## Step 2: Plan and scout, then stop at the candidate gate
1. Run: `python -m discovery_agent run --use-case <ID> --stop-after scout --no-input`.
   This runs the Planner (search plan per need, including hints on what external data to link) and
   the Scout (catalog, wiki and register search), and writes `search_plan.json`, `candidates.json`, `trace.jsonl` and `transcripts/`.
2. If the run fails, read the last events in `outputs/<ID>/trace.jsonl` and the failing agent's
   transcript before changing anything. Fix the cause (credentials, model id, a prompt, a tool
   bug) and re-run. Do not raise `max_turns` or the HTTP caps as a first response.
3. Review `candidates.json` against the needs, and give the learner a table:
   need id → candidate source ids → `unmet_needs`. Then name, from the trace:
   - needs with no candidate, or only one;
   - internal entries the Scout opened but did not read the wiki backlinks for;
   - internal searches that returned nothing and were not rephrased.
4. Show the learner the `unmet_needs` and the planner's `external_data_hints`. If a need is already met
   by internal or register sources, say so. Then ask: **do you already have dataset links that fill any
   of these needs?** For UC1, name the three prescribed links in README.md section 4; UC2 has none. Ask whether
   the learner will use them. Each link needs need ids and windows. If the learner uses them, copy
   `links/UC1_example_links.json` to `outputs/<ID>/links.json` once, only if that file does not exist yet (for UC2, start from `[]`). Never copy over it: it may already hold accepted suggestions. The Chicago
   link in README.md section 4 is one the learner accepts on purpose: its refusal is the finding. Claude
   does not make that decision for the learner. **STOP and wait for the reply.**
   Only then go to Step 2b.

## Step 2b: Suggest external sources (only for needs still unmet)
1. Only after the learner has answered Step 2, item 4. Check that `scripts/web_search.py` exists in the
   learner's repo. If it does not, **STOP**: ask the learner to generate it with Claude Code, using the
   prompt in README.md ("Suggest sources (Step 2b)"), and wait for it. Do not write the script yourself.
   Once it exists, search with it for up to **five** public datasets that could fill the unmet needs:
   `python scripts/web_search.py "<query>"`. Use the planner's `external_data_hints` as starting queries.
   Each result is a lead from a search model, not a verified source. Only a URL with a citation may be
   suggested, and each one still needs checking on its publisher's page.
2. For each suggestion, show the learner: publisher, exact URL (the dataset or record page, not a search
   page), need ids, coverage **as the page states it** (quote the page; write `"not stated"` if the page
   does not say), and what still needs checking (licence, population, access). Do not download data.
3. **STOP and wait.** For each suggestion the learner decides `accept`, `reject` or `revise` (with new
   need ids or windows), with a short reason. The learner may also add links they found. Never decide,
   and never write a reason, for the learner. Silence is not acceptance.
4. Record every decision and reason in `outputs/artifacts/decisions.md` under "Source suggestions". Append each
   accepted suggestion to `outputs/<ID>/links.json` (the same file as Step 2), in the shape of
   `links/_TEMPLATE_links.json`, with the learner's reason as `note`. Never overwrite the prescribed links.
   The **learner** writes `outputs/<ID>/gate_decisions.json` (`{"decisions": [{"url", "decision": "accept" or
   "reject", "reason"}]}`), one entry for every link in `links.json`, after inspecting each link themselves.
   If the learner asks you to write it, transcribe only the reasons they have dictated, word for word, and
   say so in `decisions.md`. Never write a reason the learner did not give. The pipeline refuses to profile
   a link without one.
5. For each accepted link, check its host is on `config/allowlist.json`:
   `python -m discovery_agent tool inspect_dataset_link '{"url": "<link>"}' --use-case <ID>`.
   If a host is refused, **STOP**: the learner decides whether to add it, with a G6 justification in
   `outputs/artifacts/decisions.md`. Do not add hosts yourself, and do not try an alternate URL. The Chicago host (`catalog.data.gov`) is refused by design: record that refusal as a finding. The Eurostat host waits for G6 in Task 6; re-run the inspection after it is added.

**Then stop.** Tell the learner the candidate list and accepted links are ready for review, and give
them the command for the next stage:
`python -m discovery_agent run --use-case <ID> --from-stage profile --links-file outputs/<ID>/links.json`
(the same file as Step 2; it must hold every link the learner has decided on).
This skill has nothing further to do. Profiling, rules, risk assessment, the memo and the gaps
happen in a normal session from here, guided by `README.md`.

---

## Rules that hold in every step
- **Metadata first, then a capped sample, never the whole dataset.** Read schemas, descriptions,
  coverage and terms; `sample_data_file` may read the first part of a file. Do not download whole
  datasets or copy personal data into any output.
- **Provenance on every claim.** Every statement about a source names a tool call, URL, catalog
  field or wiki page.
- **Unknown stays unknown.** Never infer a licence, owner, refresh cadence or consent. Use null and
  list it under unknowns.
- **Guardrails are not obstacles.** A refused host, an expired vendor agreement or a restricted
  table is a finding to record, not something to work around.
- **The agents are the product.** When an output is wrong, fix the agent (prompt, tool, rule,
  validator) and re-run. Never hand-edit `candidates.json`, records or results to look right.
- **A suggestion is not a verified source.** Selecting it grants no host access and no permission to
  use the data. Keep the exact-host allowlist.

---

## Step 3: Profile sources and run deterministic rules
1. Verify `outputs/<ID>/gate_decisions.json` exists (whenever `outputs/<ID>/links.json` is non-empty) and contains one entry per URL in `links.json` with `decision` (`"accept"` or `"reject"`) and a human-written `reason` of at least 20 characters.
2. Run profiling and deterministic risk rules:
   `python -m discovery_agent run --use-case <ID> --from-stage profile --stop-after profile --links-file outputs/<ID>/links.json --no-input`
   (To re-profile a single source after fixing a prompt or tool, append `--only <source_id>`.)
3. Inspect every generated record in `outputs/<ID>/records/<source_id>.json`:
   - Confirm at least three `provenance` entries naming exact tool calls, URLs, catalog fields, or wiki pages.
   - Verify `licence.name`, `licence.url`, `licence.commercial_use`, and `licence.evidence` (with `found_in` from `inspect_dataset_link`); ensure unknown terms stay `null` and appear in `unknowns`.
   - Check `temporal.start`, `temporal.end`, `temporal.grain`, and `spatial.code_system` against the use-case windows and needs.
   - Compare `sample_findings` (sentinel values such as `-200`, negative quantities, date format mismatches, missing shares) against `declared_metadata` and `documentation_excerpts`.
   - Confirm link-type handling: `uci_dataset_page` samples the data CSV (`<= 2 MB`), `json_stat` records dimension/time/geo summaries without treating `None` cells as zero, `landing_page` inspects schema.org JSON-LD first, and refused/login-walled links record `access.reachable = false` or `ACC-RESTRICTED` without retrying or bypassing guardrails.
4. Run deterministic rules and inspect `outputs/<ID>/rule_flags.json`:
   `python -m discovery_agent run --use-case <ID> --from-stage assess --stop-after assess --links-file outputs/<ID>/links.json --no-input`
   Verify that `rule_flags.json` raises `COV-OUT-OF-WINDOW`, `COV-PARTIAL-WINDOW`, `FRS-STALE`, `COV-GRAIN-MISMATCH`, `DQ-METADATA-CONTRADICTION`, `LIC-UNKNOWN`, `LIC-NONCOMMERCIAL`, and `ACC-UNREACHABLE` where warranted, with zero `NOT_IMPLEMENTED` warnings.

## Step 4: Calibrate verdicts, draft the memo, and review at the gate
1. Confirm `discovery_agent/prompts/risk_assessor.md` contains the `## Verdict calibration rules` section governing unresolved blockers (`not_feasible`), scoped consent gaps, zero-overlap windows (`not_feasible`), partial window coverage (`feasible_with_conditions`), historical `prototype` benchmarks (`FRS-STALE` -> `feasible_with_conditions` when cleaned and cleared), grain mismatches on `must` needs (`not_feasible`), actionable `major` flags with named owners (`feasible_with_conditions`), superseded sources, and `minor`-only flags (`feasible`).
2. Run assessment and memo generation:
   `python -m discovery_agent run --use-case <ID> --from-stage assess --links-file outputs/<ID>/links.json --no-input`
3. Review `outputs/<ID>/risk_assessment.json`, `outputs/<ID>/discovery_results.json`, and `outputs/<ID>/feasibility_memo.md` against the source records and `outputs/<ID>/trace.jsonl`:
   - Verify every claim in the memo traces to a record field or tool output, and check all seven required sections (`1. Executive summary`, `2. Need coverage`, `3. Source assessments`, `4. Red-flag register`, `5. Conditions and owners`, `6. Recommended next steps`, `7. Open questions for the human reviewer`) plus the `Human review gate` block.
   - Record every dismissed minor flag and its justification.
4. **STOP at the human review gate.** Write `outputs/artifacts/review_<ID>.md` documenting where you agree with the agent, where you overrule it and why, your verdict per dataset link, and your overall gate decision (`proceed`, `proceed_with_conditions`, or `stop`).

## Step 5: Evaluate, verify guardrails, and hand off
1. Copy `outputs/artifacts/_TEMPLATE_signoff.json` to `outputs/<ID>/signoff.json` and fill in `reviewer`, `verdict`, `conditions` (with `text`, `owner`, `due`), `agreements` / `overrides`, and `traced_conclusion` (`source_id` in `discovery_results.json`, existing dotted `record_field`, and `could_change_if` >= 20 chars).
2. Run the automated self-check and save its JSON output:
   `python -m discovery_agent check <ID> > outputs/artifacts/check_<ID>.json`
   Confirm `"problems": []` (exit code 0), zero email-like PII strings, and no repeated retries of refused URLs.
3. Audit `outputs/<ID>/trace.jsonl`, `outputs/<ID>/transcripts/`, and `outputs/<ID>/run_history.jsonl`:
   - Confirm refused hosts (such as `catalog.data.gov`) were blocked by `HttpClient` (`DOMAIN_NOT_ALLOWLISTED`), expired vendor endpoints (`vendor.atmosdata_pro`) were never called, and no secret or `ANTHROPIC_AUTH_TOKEN` value appears anywhere.
   - Record before/after evidence for any agent failure fixed at its root cause (prompt, tool, rule, or validator) in `outputs/artifacts/decisions.md`.
4. Ensure all non-code evidence is saved in `outputs/artifacts/` (`decisions.md`, `step0_checks.md`, `check_<ID>.json`, `review_<ID>.md`, `walkthrough.md`, `pytest_before.txt`, `pytest_after.txt`), keep `outputs/<ID>/` intact, and complete `README.md` Submission notes and the Evaluation Rubric before packaging.
