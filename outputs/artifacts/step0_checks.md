# Step 0 Tooling & Environment Checks

- **Python & Virtual Environment:** Python 3.13.x inside `.venv` (`requirements.txt` installed: `anthropic`, `jsonschema`, `pytest`).
- **Gateway Variables:** `ANTHROPIC_BASE_URL=https://api.ai-gateway.tigeranalytics.com`, `ANTHROPIC_AUTH_TOKEN` set in shell (redacted), `ANTHROPIC_MODEL=claude-haiku-5-5`.
- **Use-Case Validation:**
  - `python -m discovery_agent validate-use-case UC1` -> `UC1: OK`
  - `python -m discovery_agent validate-use-case UC2` -> `UC2: OK`
- **Offline Tool Smoke Checks:**
  - `python -m discovery_agent tool inspect_dataset_link '{"url": "https://archive.ics.uci.edu/dataset/360/air+quality"}' --use-case UC1` -> `status: 200`, `link_type: uci_dataset_page`, `canonical_ref: uci:360`.
  - `python -m discovery_agent tool inspect_dataset_link '{"url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hlth_cd_iap?format=JSON&lang=EN&geo=IT"}' --use-case UC1` -> `status: 200`, `link_type: json_stat`, `72` values, `0` missing cells.
- **Test Suite Status:**
  - Before gaps closed (`outputs/artifacts/pytest_before.txt`): 52 collected, 32 passed, 20 failed (`tests/test_learner_gaps.py`).
  - After gaps closed (`outputs/artifacts/pytest_after.txt`): 52 collected, 52 passed, 0 failed.
