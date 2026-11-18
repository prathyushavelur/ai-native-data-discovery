"""Deterministic red-flag rules, run on every catalog record before the Risk Assessor agent.

Why rules and an agent? Rules are cheap, repeatable and testable, and they catch what can be
read from structured fields. The agent adds judgement flags (conflicts, consent gaps,
representativeness, ...) and may dismiss a rule flag only with a written reason, and the
orchestrator enforces that.

Each rule: (record, candidate, use_case, settings) -> list of {"code", "evidence"}.
"""
from __future__ import annotations

import re
from datetime import date

Flag = dict

GRAIN_ORDER = ["minute", "15min", "30min", "hourly", "daily", "weekly", "monthly", "quarterly", "annual"]
INACTIVE_STATUSES = {"deprecated", "archived", "frozen", "retired", "decommissioned", "superseded"}


def _flag(code: str, evidence: str) -> Flag:
    return {"code": code, "evidence": evidence}


def _d(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Provided rules (read these as worked examples)
# ---------------------------------------------------------------------------
def rule_licence(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal":
        return []
    lic = record.get("licence") or {}
    name = (lic.get("name") or "").strip()
    flags = []
    if not name or name.lower() in {"unknown", "none", "null", "not found", "n/a"}:
        flags.append(_flag("LIC-UNKNOWN", f"No licence established. Evidence field: {lic.get('evidence')!r}"))
    elif re.search(r"\bNC\b|non[- ]?commercial", name, re.I):
        flags.append(_flag("LIC-NONCOMMERCIAL", f"Licence {name!r} restricts commercial use"))
    elif re.search(r"\bBY\b|attribution|OGL|open government", name, re.I):
        flags.append(_flag("LIC-ATTRIBUTION", f"Licence {name!r} requires attribution"))
    if lic.get("mixed_sources"):
        flags.append(_flag("LIC-MIXED", "Record states that parts come from upstream providers with different terms"))
    return flags


def rule_agreement(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = ((record.get("licence") or {}).get("agreement_status") or "").lower()
    if record["kind"] == "vendor_feed" and status not in {"active", "signed"}:
        return [_flag("LIC-AGREEMENT-NOT-ACTIVE", f"Vendor feed with agreement_status={status or 'unknown'!r}")]
    return []


def rule_access(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    acc = record.get("access") or {}
    flags = []
    if acc.get("auth_required") or (acc.get("classification") or "").lower() == "restricted":
        flags.append(_flag("ACC-RESTRICTED", f"auth_required={acc.get('auth_required')}, "
                                             f"classification={acc.get('classification')}, process={acc.get('request_process')!r}"))
    if (acc.get("method") or "").lower() in {"manual_export", "manual", "spreadsheet", "email"}:
        flags.append(_flag("ACC-MANUAL", f"Access method {acc.get('method')!r}"))
    if acc.get("reachable") is False:
        flags.append(_flag("ACC-UNREACHABLE", "Record states the source could not be reached or restored"))
    return flags


def rule_payload(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    size = (record.get("access") or {}).get("approx_size_bytes")
    limit = settings["rules"]["large_payload_bytes"]
    if isinstance(size, int) and size > limit:
        return [_flag("OPS-LARGE-PAYLOAD", f"approx_size_bytes={size:,} > {limit:,}")]
    return []


def rule_pii(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    pii_fields = [f["name"] for f in (record.get("schema") or {}).get("fields", []) if f.get("pii") is True]
    declared = (record.get("declared_metadata") or {}).get("contains_pii")
    if pii_fields or declared is True:
        return [_flag("GOV-PII", f"PII fields: {pii_fields or 'declared contains_pii=true'}")]
    return []


def rule_owner(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal" and not ((record.get("ownership") or {}).get("owner") or "").strip():
        return [_flag("GOV-OWNER-UNKNOWN", "Internal source with no recorded owner")]
    return []


def rule_status(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = (record.get("status") or "").lower()
    if status in INACTIVE_STATUSES:
        return [_flag("GOV-DEPRECATED", f"status={status!r}")]
    return []


# ---------------------------------------------------------------------------
# LEARNER TODO (G4): three rules. tests/test_learner_gaps.py::test_g4_* checks them.
# ---------------------------------------------------------------------------



def _windows_by_id(uc: dict) -> dict[str, dict]:
    raw_windows = uc.get("windows") or {}
    if isinstance(raw_windows, dict):
        return raw_windows
    if isinstance(raw_windows, list):
        return {w["id"]: w for w in raw_windows if isinstance(w, dict) and w.get("id")}
    return {}


def _needs_by_id(uc: dict) -> dict[str, dict]:
    raw_needs = uc.get("needs") or []
    if isinstance(raw_needs, dict):
        return raw_needs
    if isinstance(raw_needs, list):
        return {n["id"]: n for n in raw_needs if isinstance(n, dict) and n.get("id")}
    return {}


def rule_temporal_coverage(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """Coverage of the candidate's target windows, plus staleness."""
    temporal = record.get("temporal") or {}
    grain = (temporal.get("grain") or "").strip().lower()
    if grain == "static":
        return []

    start_raw = temporal.get("start")
    start_dt = _d(start_raw)
    if start_dt is None:
        return []

    as_of_raw = uc.get("as_of")
    as_of_dt = _d(as_of_raw)
    end_raw = temporal.get("end")
    end_dt = _d(end_raw)
    effective_end_dt = end_dt if end_dt is not None else as_of_dt
    effective_end_str = end_raw[:10] if end_raw else f"{as_of_raw} (open-ended)"

    flags: list[Flag] = []
    windows_map = _windows_by_id(uc)
    target_ids = candidate.get("target_windows") or []
    threshold = float(settings["rules"]["partial_window_threshold"])

    fractions: list[tuple[str, float, str]] = []
    for win_id in target_ids:
        win = windows_map.get(win_id)
        if not win:
            continue
        w_start = _d(win.get("start"))
        w_end = _d(win.get("end"))
        if w_start is None or w_end is None or w_end < w_start:
            continue

        total_days = (w_end - w_start).days + 1
        if effective_end_dt is None or effective_end_dt < w_start or start_dt > w_end:
            frac = 0.0
        else:
            ov_start = max(start_dt, w_start)
            ov_end = min(effective_end_dt, w_end)
            covered_days = max(0, (ov_end - ov_start).days + 1)
            frac = covered_days / total_days

        detail = (
            f"window {win_id} [{win.get('start')}..{win.get('end')}] vs "
            f"record [{start_raw[:10]}..{effective_end_str}] ({frac:.1%} covered)"
        )
        fractions.append((win_id, frac, detail))

    if fractions:
        if all(frac == 0.0 for _, frac, _ in fractions):
            flags.append(_flag(
                "COV-OUT-OF-WINDOW",
                "Zero overlap with target windows: " + "; ".join(d for _, _, d in fractions),
            ))
        elif any(frac < threshold for _, frac, _ in fractions):
            short = [d for _, frac, d in fractions if frac < threshold]
            flags.append(_flag(
                "COV-PARTIAL-WINDOW",
                f"Coverage below {threshold:.0%} threshold: " + "; ".join(short),
            ))

    stale_years = float(settings["rules"]["stale_after_years"])
    if end_dt is not None and as_of_dt is not None:
        age_years = (as_of_dt - end_dt).days / 365.25
        if age_years > stale_years:
            flags.append(_flag(
                "FRS-STALE",
                f"Record end date {end_raw[:10]} is {age_years:.1f} years before uc as_of {as_of_raw} (limit {stale_years:g}y)",
            ))

    return flags


def rule_grain(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """COV-GRAIN-MISMATCH if the record's grain is coarser than min_grain of any need."""
    rec_grain = ((record.get("temporal") or {}).get("grain") or "").strip().lower()
    if rec_grain not in GRAIN_ORDER:
        return []

    rec_idx = GRAIN_ORDER.index(rec_grain)
    needs_map = _needs_by_id(uc)
    mismatches: list[str] = []

    for need_id in candidate.get("need_ids") or []:
        need = needs_map.get(need_id)
        if not need:
            continue
        req_grain = (need.get("min_grain") or "").strip().lower()
        if req_grain not in GRAIN_ORDER:
            continue
        req_idx = GRAIN_ORDER.index(req_grain)
        if rec_idx > req_idx:
            mismatches.append(f"{need_id} requires <= {req_grain}, record has {rec_grain}")

    if mismatches:
        return [_flag("COV-GRAIN-MISMATCH", "; ".join(mismatches))]
    return []


_NEGATED_MISSING_RE = re.compile(
    r"\b(?:no|without|zero|0|not\s+any|free\s+of|absent\s+of)\s+(?:missing|null|na|nan)\s*(?:values?|data|entries|cells|fields)?\b",
    re.I,
)

_POSITIVE_MISSING_RE = re.compile(
    r"(?:\bmissing\s+(?:values?|data|entries|observations|measurements)\b"
    r"|\babsence\s+of\s+value\b"
    r"|\btagged\s+with\s+-200\b"
    r"|(?:^|[\s(\[\"'])-200(?:$|[\s)\],.\"'])"
    r"|\?\s*(?:used\s+as\s+missing|denotes?\s+missing|for\s+missing)"
    r"|\bnan\b)",
    re.I,
)


def rule_metadata_contradiction(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """DQ-METADATA-CONTRADICTION when declared has_missing_values is 'no' but notes report missing values."""
    declared = (record.get("declared_metadata") or {}).get("has_missing_values")
    is_declared_no = (
        declared is False
        or (isinstance(declared, str) and declared.strip().lower() in {"no", "false", "0"})
    )
    if not is_declared_no:
        return []

    texts: list[str] = []
    for bucket in ("documentation_excerpts", "quality_notes"):
        val = record.get(bucket)
        if isinstance(val, list):
            texts.extend(str(item) for item in val if item)
        elif isinstance(val, str) and val.strip():
            texts.append(val)

    for raw_text in texts:
        cleaned = _NEGATED_MISSING_RE.sub(" ", raw_text)
        if _POSITIVE_MISSING_RE.search(cleaned):
            return [_flag(
                "DQ-METADATA-CONTRADICTION",
                f"declared_metadata.has_missing_values={declared!r} contradicts note: {raw_text[:200]!r}",
            )]

    return []

RULES = [rule_licence, rule_agreement, rule_access, rule_payload, rule_pii, rule_owner, rule_status,
         rule_temporal_coverage, rule_grain, rule_metadata_contradiction]


def evaluate(record: dict, candidate: dict, uc: dict, settings: dict) -> tuple[list[Flag], list[str]]:
    """Run every rule. Returns (flags, warnings). A rule that is not implemented yet is skipped with a warning."""
    flags: list[Flag] = []
    warnings: list[str] = []
    for rule in RULES:
        try:
            for f in rule(record, candidate, uc, settings):
                flags.append({**f, "raised_by": f"rule:{rule.__name__}"})
        except NotImplementedError as exc:
            warnings.append(f"{rule.__name__} skipped: {exc}")
    seen, unique = set(), []
    for f in flags:
        if f["code"] not in seen:
            seen.add(f["code"])
            unique.append(f)
    return unique, warnings
