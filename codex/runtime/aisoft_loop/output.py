"""Normalize provider CLI output down to the single JSON object the validators expect.

Adapters own their CLI's quirks. A model that explains itself before emitting the
object is still contract-compliant once the adapter isolates that object, so this
keeps the shared result validators strict rather than teaching them to be lenient.
"""

from __future__ import annotations

import json


class OutputError(ValueError):
    """Provider output contained no usable JSON object."""


def extract_last_json_object(text: str) -> str:
    """Return the last top-level JSON object in `text`, serialized.

    Scans forward and skips over each decoded object so that nested braces are
    never mistaken for the result.
    """
    decoder = json.JSONDecoder()
    found: list[dict[str, object]] = []
    index = 0
    while True:
        start = text.find("{", index)
        if start == -1:
            break
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict):
            found.append(value)
        index = end
    if not found:
        raise OutputError("provider output contained no JSON object")
    return json.dumps(found[-1], ensure_ascii=False)
