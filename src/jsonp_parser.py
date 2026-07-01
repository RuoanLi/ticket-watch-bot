from __future__ import annotations

import json
import re

_JSONP_PATTERN = re.compile(r"^\s*(?:/\*.*?\*/\s*)?\w+\((.*)\)\s*;?\s*$", re.DOTALL)


def parse_jsonp(raw_text: str) -> dict:
    """Strip a JSONP callback wrapper like someCallback({...}) and return the parsed dict.

    Some servers prefix responses with a `/**/` comment before the callback name - that's
    stripped too.
    """
    match = _JSONP_PATTERN.match(raw_text)
    if not match:
        raise ValueError("Response does not look like JSONP: " + raw_text[:200])
    return json.loads(match.group(1))


def extract_summary(payload: dict) -> list[dict]:
    """Pull the per-section remaining-count summary out of the parsed payload."""
    try:
        return payload["summary"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Unexpected payload shape, missing summary: {exc}") from exc
