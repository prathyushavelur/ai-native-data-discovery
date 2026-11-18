"""Summarisers for self-describing metadata formats the supplementary URLs use.

The tool wrappers (fetch + call) are provided. The pure functions that do the
summarising are LEARNER TODOs (G3). The data-package summary is not graded in this version. They are pure so you can test them offline
against tests/fixtures/ without network or LLM.
"""
from __future__ import annotations
import math
from collections import Counter
from .base import NotImplementedTool, ToolContext, tool

LARGE_RESOURCE_BYTES = 100_000_000


# ---------------------------------------------------------------------------
# Not graded in this version (former G2). Left as a stub: no graded link uses a data package.
# ---------------------------------------------------------------------------
# Spec: https://specs.frictionlessdata.io/data-package/
# Return a dict with EXACTLY these keys (tests/test_learner_gaps.py checks them):
#   title, version, profile          : str | None, copied from the package
#   declared_licences                : the package's "licenses" list, or None if absent/empty
#   temporal                         : {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} from package["temporal"], or None
#   resources                        : [{"name", "path", "format", "bytes", "field_count"}] one per resource
#   total_bytes                      : sum of resource bytes (missing bytes count as 0)
#   largest_resource_bytes           : max resource bytes
#   matching_fields                  : fields whose name starts with any prefix in field_filter (all resources,
#                                      de-duplicated by name, max 60): [{"resource", "name", "unit", "source"}]
#                                      where "source" is field["source"]["name"] if present. [] if field_filter is None.
#   upstream_sources                 : sorted distinct field["source"]["name"] values across ALL fields
#   warnings                         : list containing (when they apply)
#                                        "NO_PACKAGE_LICENCE"         no package-level licence declared
#                                        "LARGE_RESOURCE"             any resource > LARGE_RESOURCE_BYTES
#                                        "MULTIPLE_UPSTREAM_SOURCES"  more than one upstream source
def datapackage_summary(package: dict, field_filter: list[str] | None = None) -> dict:
    raise NotImplementedTool("datapackage_summary is not implemented in this version (former G2).")


# ---------------------------------------------------------------------------
# LEARNER TODO (G3): JSON-stat 2.0 dataset -> summary
# ---------------------------------------------------------------------------
_ISO_3166_1_ALPHA2 = frozenset({
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS",
    "BT", "BV", "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE",
    "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF",
    "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT", "JE", "JM",
    "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC",
    "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ", "NA",
    "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG",
    "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS",
    "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO",
    "TR", "TT", "TV", "TW", "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW",
})


def _ordered_category_codes(category: dict) -> list[str]:
    index = category.get("index")
    labels = category.get("label") or {}
    if isinstance(index, list):
        return [str(code) for code in index]
    if isinstance(index, dict):
        return [str(code) for code, _ in sorted(index.items(), key=lambda item: item[1])]
    if isinstance(labels, dict):
        return [str(code) for code in labels.keys()]
    return []


def jsonstat_summary(dataset: dict) -> dict:
    dim_ids = list(dataset.get("id") or [])
    dim_sizes = list(dataset.get("size") or [])
    dim_map = dataset.get("dimension") or {}

    dimensions = []
    codes_by_dim: dict[str, list[str]] = {}

    for idx, dim_id in enumerate(dim_ids):
        dim_obj = dim_map.get(dim_id) or {}
        cat = dim_obj.get("category") or {}
        cat_labels = cat.get("label") or {}
        ordered_codes = _ordered_category_codes(cat)
        codes_by_dim[dim_id] = ordered_codes

        size_val = dim_sizes[idx] if idx < len(dim_sizes) else len(ordered_codes)
        preview_labels = [f"{code}: {cat_labels.get(code, code)}" for code in ordered_codes[:10]]
        dimensions.append({
            "id": dim_id,
            "size": size_val,
            "labels": preview_labels,
        })

    time_codes = sorted(codes_by_dim.get("time", []))
    time_summary = (
        {"first": time_codes[0], "last": time_codes[-1], "values": time_codes}
        if time_codes
        else None
    )

    geo_codes = list(codes_by_dim.get("geo", []))

    expected_cells = math.prod(dim_sizes) if dim_sizes else 0
    raw_values = dataset.get("value")
    if isinstance(raw_values, dict):
        value_count = sum(1 for v in raw_values.values() if v is not None)
    elif isinstance(raw_values, list):
        value_count = sum(1 for v in raw_values if v is not None)
    else:
        value_count = 0

    missing_cells = max(0, expected_cells - value_count)

    raw_status = dataset.get("status")
    status_counter: Counter[str] = Counter()
    if isinstance(raw_status, dict):
        for code in raw_status.values():
            if code is not None and str(code) != "":
                status_counter[str(code)] += 1
    elif isinstance(raw_status, list):
        for code in raw_status:
            if code is not None and str(code) != "":
                status_counter[str(code)] += 1
    elif isinstance(raw_status, str) and raw_status != "":
        status_counter[raw_status] = expected_cells

    warnings: list[str] = []
    if missing_cells > 0:
        warnings.append("MISSING_CELLS")
    if any(code not in _ISO_3166_1_ALPHA2 for code in geo_codes):
        warnings.append("NON_ISO_GEO_CODES")

    return {
        "label": dataset.get("label"),
        "updated": dataset.get("updated"),
        "source": dataset.get("source"),
        "dimensions": dimensions,
        "time": time_summary,
        "geo_codes": geo_codes,
        "expected_cells": expected_cells,
        "value_count": value_count,
        "missing_cells": missing_cells,
        "status_counts": dict(status_counter),
        "warnings": warnings,
    }

# ---------------------------------------------------------------------------
# Tool wrappers (provided)
# ---------------------------------------------------------------------------
@tool("summarize_datapackage",
      "Summarise a Frictionless Data Package descriptor (datapackage.json): licence declarations, temporal coverage, "
      "resource sizes, matching fields and their upstream sources. Reads only the descriptor, never the data files.",
      {"url": {"type": "string"},
       "field_filter": {"type": "array", "items": {"type": "string"},
                        "description": "Field-name prefixes to list, e.g. ['AB_', 'CD_load']"}},
      ["url"])
def summarize_datapackage(ctx: ToolContext, args: dict) -> dict:
    package, res = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], "last_modified_header": res.headers.get("last-modified"),
            **datapackage_summary(package, args.get("field_filter"))}


@tool("summarize_jsonstat",
      "Summarise a JSON-stat 2.0 dataset (for example from the Eurostat dissemination API): dimensions, time coverage, "
      "geo codes, missing cells and status flags.",
      {"url": {"type": "string"}}, ["url"])
def summarize_jsonstat(ctx: ToolContext, args: dict) -> dict:
    dataset, _ = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], **jsonstat_summary(dataset)}
