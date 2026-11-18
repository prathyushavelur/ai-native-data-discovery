#!/usr/bin/env python3
"""Stdlib-only web search helper via Tiger AI Gateway for Step 2b."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('Usage: python scripts/web_search.py "<query>"', file=sys.stderr)
        return 1

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip().rstrip("/")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    if not base_url:
        print("Error: ANTHROPIC_BASE_URL is not set.", file=sys.stderr)
        return 1
    if not token:
        print("Error: ANTHROPIC_AUTH_TOKEN is not set.", file=sys.stderr)
        return 1

    model = os.environ.get("WEB_SEARCH_MODEL", "").strip() or "gemini-3.8-flash"
    query = sys.argv[1].strip()

    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_text = exc.read().decode("utf-8", errors="replace")[:500]
        print(f"HTTP {exc.code} error from gateway: {err_text}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    choices = body.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    answer = message.get("content") or ""
    print(answer.strip())

    urls: list[str] = []
    for key in ("citations", "citation_urls"):
        val = body.get(key) or message.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str) and item.startswith("http"):
                    urls.append(item)
                elif isinstance(item, dict):
                    u = item.get("url") or item.get("uri")
                    if isinstance(u, str) and u.startswith("http"):
                        urls.append(u)

    annotations = message.get("annotations") or []
    if isinstance(annotations, list):
        for ann in annotations:
            if isinstance(ann, dict):
                url_cit = ann.get("url_citation") or ann
                u = url_cit.get("url") or url_cit.get("uri")
                if isinstance(u, str) and u.startswith("http"):
                    urls.append(u)

    seen = set()
    unique_urls = [u for u in urls if not (u in seen or seen.add(u))]
    print("\nCitations:")
    if unique_urls:
        for u in unique_urls:
            print(f"- {u}")
    else:
        print("- (none returned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())