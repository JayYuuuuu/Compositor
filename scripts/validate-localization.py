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



def dynamic_display_keys(source_root):
    """Closed source strings used by runtime display lookups; never scan user content or serialized values."""
    keys = set()
    literal = re.compile(r'"([^"\\]*)"')
    for path in (source_root / "Compositor").rglob("*.swift"):
        source = path.read_text()
        for match in re.finditer(r'L10n\.(?:text|format)\(', source):
            depth, quoted, end = 1, False, match.end()
            while end < len(source) and depth:
                char = source[end]
                if char == "\\" and quoted:
                    end += 2; continue
                if char == '"': quoted = not quoted
                if not quoted:
                    if char == "(": depth += 1
                    elif char == ")": depth -= 1
                end += 1
            for value in literal.findall(source[match.end():end - 1]):
                if re.search(r"[A-Za-z]", value): keys.add(value)
        # Explicit raw values of these iterable enums are UI choices, not rewritten model data.
        for match in re.finditer(r'enum \w+: [^{]*String[^\{]*CaseIterable[^\{]*\{', source):
            declarations = re.split(r'\b(?:var|let|func|init)\b|\}', source[match.end():], 1)[0]
            keys.update(re.findall(r'\w+\s*=\s*"([^"\\]+)"', declarations))
        # History names are app actions looked up when composing Undo/Redo.
        for match in re.finditer(r'beginEdit\(([^\n]*)', source):
            keys.update(value for value in literal.findall(match[1]) if re.search(r"[A-Za-z]", value))
    # Keyboard labels are fixed English identities; only their display is localized.
    shortcuts = (source_root / "Compositor/UI/KeyboardShortcuts.swift").read_text()
    fixed = shortcuts[shortcuts.index("static let all:"):shortcuts.index("@MainActor @Observable")]
    keys.update(re.findall(r'entry\("([^"\\]+)"', fixed))
    keys.update(re.findall(r'\("([^"\\]+)", "', fixed))
    keys.update(re.findall(r'title: "([^"\\]+)"', fixed))
    keys.update(["Menus", "Canvas & Layers", "Text Editing"])
    return keys


def main():
    # Positive and negative controls prove the placeholder check before accepting a clean result.
    assert placeholders("%lld %@") == placeholders("%2$@ %1$lld")
    assert placeholders("%lld %@") != placeholders("%1$@ %2$lld")
    assert placeholders("100%%") == {}
    catalog = json.loads(CATALOG.read_text(), object_pairs_hook=unique_object)
    assert catalog["sourceLanguage"] == "en"
    missing = dynamic_display_keys(CATALOG.parents[1]) - catalog["strings"].keys()
    assert not missing, ("Uncataloged dynamic display strings", sorted(missing))
    for key, entry in catalog["strings"].items():
        for language in ("en", "zh-Hans"):
            unit = entry["localizations"][language]["stringUnit"]
            assert unit["state"] == "translated" and (unit["value"] or entry.get("shouldTranslate") is False), (key, language)
            assert placeholders(key) == placeholders(unit["value"]), (key, language)
    print(f"Validated {len(catalog['strings'])} English / Simplified Chinese catalog entries and placeholders.")


if __name__ == "__main__":
    main()
