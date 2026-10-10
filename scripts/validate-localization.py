#!/usr/bin/env python3
"""Validate the maintained catalog without requiring Xcode. Does not validate runtime UI."""
import json
from pathlib import Path
import re

CATALOG = Path(__file__).resolve().parents[1] / "Compositor" / "Localizable.xcstrings"
TOKEN = re.compile(r"%(?:(\d+)\$)?(lld|ld|d|@|f|g|%)")


def placeholders(text):
    result = {}
    next_position = 1
    for match in TOKEN.finditer(text):
        position, kind = match.groups()
        if kind == "%":
            continue
        index = int(position) if position else next_position
        next_position += position is None
        if index in result and result[index] != kind:
            raise ValueError(f"Conflicting placeholder {index}")
        result[index] = kind
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate catalog key: {key}")
        result[key] = value
    return result


def main():
    # Positive and negative controls prove the placeholder check before accepting a clean result.
    assert placeholders("%lld %@") == placeholders("%2$@ %1$lld")
    assert placeholders("%lld %@") != placeholders("%1$@ %2$lld")
    assert placeholders("100%%") == {}
    catalog = json.loads(CATALOG.read_text(), object_pairs_hook=unique_object)
    assert catalog["sourceLanguage"] == "en"
    for key, entry in catalog["strings"].items():
        for language in ("en", "zh-Hans"):
            unit = entry["localizations"][language]["stringUnit"]
            assert unit["state"] == "translated" and (unit["value"] or entry.get("shouldTranslate") is False), (key, language)
            assert placeholders(key) == placeholders(unit["value"]), (key, language)
    print(f"Validated {len(catalog['strings'])} English / Simplified Chinese catalog entries and placeholders.")


if __name__ == "__main__":
    main()
