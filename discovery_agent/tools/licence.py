"""Licence and structured-metadata extraction from dataset landing pages."""
from __future__ import annotations

import json
import re

from .base import NotImplementedTool


def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""
    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"), "description": clip(d.get("description")),
        "license": d.get("license"), "creator": name_of(d.get("creator")), "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"), "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"), "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"), "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [{k: x.get(k) for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                          if isinstance(x, dict) and x.get(k) is not None} for x in dist[:10]],
    }


# ---------------------------------------------------------------------------
# LEARNER TODO (G1): find the licence of ANY dataset from its landing page
# ---------------------------------------------------------------------------
_LICENCE_HOSTS = (
    "creativecommons.org",
    "opendatacommons.org",
    "nationalarchives.gov.uk",
    "choosealicense.com",
    "opensource.org/licenses",
    "spdx.org/licenses",
)

_UNKNOWN_TOKENS = {"unknown", "unspecified", "not specified", "none", "other", "n/a"}


def _clip_snippet(value: str | None, limit: int = 400) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(re.sub(r"<[^>]+>", " ", str(value)).split())
    return cleaned[:limit] if cleaned else None


def _normalise_licence(raw: str | None) -> str | None:
    if not raw:
        return None
    text = raw.strip()
    low = text.lower()
    if low in _UNKNOWN_TOKENS:
        return None

    if re.search(r"(?:publicdomain/zero/1\.0|licenses/cc0-1\.0|\bcc0(?:\s*1\.0)?\b|creative commons zero)", low):
        return "CC0 1.0"

    if re.search(r"(?:opendatacommons\.org/licenses/odbl|\bodbl(?:\s*v?1\.0)?\b|open database licen[cs]e)", low):
        return "ODbL 1.0"

    m_ogl = re.search(
        r"(?:open-government-licence/version/|(?:\bopen government licen[cs]e|\bogl)\s*v?)(\d+(?:\.\d+)?)",
        low,
    )
    if m_ogl:
        ver = m_ogl.group(1)
        if "." not in ver:
            ver = f"{ver}.0"
        return f"OGL v{ver}"

    m_cc_url = re.search(
        r"(?:creativecommons\.org/licenses/|choosealicense\.com/licenses/cc-)(by(?:-[a-z]+)*)[/-](\d+\.\d+)",
        low,
    )
    if m_cc_url:
        mods = m_cc_url.group(1).upper()
        ver = m_cc_url.group(2)
        return f"CC {mods} {ver}"

  
    m_cc_short = re.search(
        r"\bcc[\s-](by(?:-(?:nc|sa|nd)){0,3})(?:\s*v?(\d+\.\d+))?\b",
        low,
    )
    if m_cc_short:
        mods = m_cc_short.group(1).upper()
        ver = m_cc_short.group(2) or "4.0"
        return f"CC {mods} {ver}"
    # if m_cc_short:
    #     tokens = re.findall(r"\b(?:by|nc|sa|nd)\b", m_cc_short.group(0).upper())
    #     mods = tokens[0] + (("-" + "-".join(tokens[1:])) if len(tokens) > 1 else "")
    #     ver = m_cc_short.group(1) or "4.0"
    #     return f"CC {mods} {ver}"

    m_cc_full = re.search(
        r"creative commons attribution((?:-(?:noncommercial|sharealike|noderivatives|noderivs))*)(?:\s+(\d+\.\d+))?",
        low,
    )
    if m_cc_full:
        mod_str = m_cc_full.group(1) or ""
        ver = m_cc_full.group(2) or "4.0"
        parts = ["BY"]
        if "noncommercial" in mod_str:
            parts.append("NC")
        if "sharealike" in mod_str:
            parts.append("SA")
        if "noderiv" in mod_str:
            parts.append("ND")
        mods = parts[0] + (("-" + "-".join(parts[1:])) if len(parts) > 1 else "")
        return f"CC {mods} {ver}"

    if re.search(r"(?:licenses/mit\b|\bmit\s+licen[cs]e\b)", low):
        return "MIT"
    if re.search(r"(?:licenses/apache-2\.0\b|\bapache\s+licen[cs]e(?:,?\s*version)?\s*2\.0\b|\bapache-2\.0\b)", low):
        return "Apache-2.0"

    return None


def _extract_from_jsonld(datasets: list[dict]) -> dict | None:
    for ds in datasets:
        if not isinstance(ds, dict):
            continue
        lic = ds.get("license")
        if lic is None:
            continue
        entries = lic if isinstance(lic, list) else [lic]
        for entry in entries:
            if isinstance(entry, str) and entry.strip():
                raw = entry.strip()
                norm = _normalise_licence(raw)
                is_url = raw.startswith(("http://", "https://"))
                if norm or raw.lower() in _UNKNOWN_TOKENS:
                    return {
                        "licence_name": norm,
                        "licence_url": raw if is_url else None,
                        "snippet": _clip_snippet(raw),
                        "found_in": "json-ld",
                    }
            elif isinstance(entry, dict):
                name = str(entry.get("name") or "").strip()
                url = str(entry.get("url") or entry.get("@id") or "").strip()
                norm = _normalise_licence(name) or _normalise_licence(url)
                raw_snip = name or url or json.dumps(entry, ensure_ascii=False)
                if norm or name.lower() in _UNKNOWN_TOKENS:
                    return {
                        "licence_name": norm,
                        "licence_url": url if url.startswith(("http://", "https://")) else None,
                        "snippet": _clip_snippet(raw_snip),
                        "found_in": "json-ld",
                    }
    return None


def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    datasets = jsonld_datasets(html) if jsonld is None else jsonld
    from_ld = _extract_from_jsonld(datasets)
    if from_ld is not None:
        return from_ld

    for m in re.finditer(r"""(?is)<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", html):
        href = m.group(1).strip()
        anchor_text = _clip_snippet(m.group(2)) or ""
        if any(host in href.lower() for host in _LICENCE_HOSTS):
            norm = _normalise_licence(href) or _normalise_licence(anchor_text)
            if norm:
                return {
                    "licence_name": norm,
                    "licence_url": href,
                    "snippet": _clip_snippet(anchor_text or href),
                    "found_in": "link",
                }

    plain = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", html)
    plain = " ".join(re.sub(r"<[^>]+>", " ", plain).split())
    for sent in re.split(r"(?<=[.!?])\s+|\n+", plain):
        if re.search(r"\b(?:licen[cs]e[d]?|creative commons|cc\s+by|cc0|odbl|open government|ogl|mit|apache)\b", sent, re.I):
            norm = _normalise_licence(sent)
            if norm:
                return {
                    "licence_name": norm,
                    "licence_url": None,
                    "snippet": _clip_snippet(sent),
                    "found_in": "text",
                }

    return {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}
