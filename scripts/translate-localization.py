#!/usr/bin/env python3
"""Propose missing Simplified Chinese translations with DeepSeek. Never edits the catalog."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catalog_validation", ROOT / "scripts/validate-localization.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)
# Include widths, precision, positional arguments, and Foundation's object specifier.
FORMAT = re.compile(r"%(?:(\d+)\$)?[-+ #0]*(?:\d+)?(?:\.\d+)?(hh|ll|h|l|L|z|t|j)?([@diuoxXfFeEgGaAcsp%])")
KEYS = re.compile(r"\b(?:Command|Cmd|Option|Alt|Shift|Control|Ctrl|Tab|Escape|Enter|Return)\b|[⌘⌥⇧⌃⌫⇥⎋]|…|›")
CHORDS = re.compile(r"[⌘⌥⇧⌃]+[A-Za-z0-9+−=\[\]]")
TOOL_KEYS = re.compile(r"[（(]([A-Z])[）)]")
NUMBERS = re.compile(r"\d+(?:\.\d+)?")


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=validation.unique_object)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def format_signature(text):
    result, next_index = Counter(), 1
    for match in FORMAT.finditer(text):
        index, length, kind = match.groups()
        if kind == "%":
            result[(0, "%")] += 1
            continue
        position = int(index) if index else next_index
        next_index += index is None
        result[(position, re.sub(r"^%\d+\$", "%", match[0]))] += 1
    return result


def required_terms(source, glossary):
    spans, result = [], {}
    for term, translated in sorted(glossary["terms"].items(), key=lambda pair: -len(pair[0])):
        scope = glossary.get("scoped_terms", {}).get(term)
        if scope and source.strip().rstrip("…").casefold() != term.casefold() and not re.search(scope["context_pattern"], source, re.IGNORECASE):
            continue
        pattern = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
        for match in re.finditer(pattern, source, re.IGNORECASE):
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            spans.append(match.span())
            result[term] = translated
    return result


def check_translation(source, translated, glossary):
    errors = []
    if not isinstance(translated, str) or not translated.strip():
        return ["Empty or non-string translation"]
    if format_signature(source) != format_signature(translated):
        errors.append("Placeholder type, index, multiplicity or escaped percent changed")
    if Counter(KEYS.findall(source)) != Counter(KEYS.findall(translated)):
        errors.append("Key name, shortcut symbol, ellipsis or command path separator changed")
    if Counter(CHORDS.findall(source)) != Counter(CHORDS.findall(translated)) or Counter(TOOL_KEYS.findall(source)) != Counter(TOOL_KEYS.findall(translated)):
        errors.append("Shortcut or tool key changed")
    if Counter(NUMBERS.findall(FORMAT.sub("", source))) != Counter(NUMBERS.findall(FORMAT.sub("", translated))):
        errors.append("Numeric value changed")
    if source.count("\n") != translated.count("\n"):
        errors.append("Newline count changed")
    for term, required in required_terms(source, glossary).items():
        if required not in translated:
            errors.append(f"Terminology mismatch: {term} must use {required}")
    for required in glossary.get("label_requirements", {}).get(source, []):
        if required not in translated:
            errors.append(f"Label context mismatch: must use {required}")
    for term in glossary["preserve"]:
        pattern = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
        if len(re.findall(pattern, source)) != len(re.findall(pattern, translated)):
            errors.append(f"Protected name or unit changed: {term}")
    if re.search(r"[A-Za-z]", source) and not re.search(r"[\u3400-\u9fff]", translated):
        # Brand names and format labels should stay in their original language.
        remainder = source
        for term in glossary["preserve"]:
            remainder = remainder.replace(term, "")
        if re.search(r"[A-Za-z]", FORMAT.sub("", remainder)):
            errors.append("No Chinese text in a translatable label")
    return errors


def pending_items(catalog):
    items = []
    for key, entry in catalog["strings"].items():
        if entry.get("shouldTranslate") is False or entry.get("extractionState") == "stale":
            continue
        languages = entry.get("localizations", {})
        if any("variations" in language or "substitutions" in language for language in languages.values()):
            raise ValueError("Structured plural or device variants require separate review")
        unit = languages.get("zh-Hans", {}).get("stringUnit", {})
        if unit.get("state") == "translated" and unit.get("value"):
            continue
        source = languages.get("en", {}).get("stringUnit", {}).get("value", key)
        if not isinstance(source, str):
            raise ValueError("Invalid English source value")
        if not re.search(r"[A-Za-z]", FORMAT.sub("", source)):
            continue
        item = {"source": source, "context": entry.get("comment", "")}
        if source != key:
            item["key"] = key  # Preserve semantic catalog IDs; translate the English value, never the ID.
        items.append(item)
    return items


def api_key(env_file):
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key and env_file:
        for line in Path(env_file).read_text().splitlines():
            match = re.match(r"(?:export\s+)?DEEPSEEK_API_KEY\s*=\s*(.*)", line.strip())
            if match:
                key = match[1].strip().strip("\"'")
    if not key or "\n" in key or "\r" in key:
        raise ValueError("Missing or invalid DEEPSEEK_API_KEY")
    return key


def translate(items, glossary, key, model, max_tokens):
    system = "你是 macOS 图像合成和照片编辑软件的简体中文本地化译者。\n" + json.dumps(glossary, ensure_ascii=False)
    system += '\n只输出 JSON，格式为 {"translations":[{"id":"s000","text":"译文","review":""}]}。每个输入 id 必须恰好返回一次。'
    numbered = [dict(item, id=f"s{index:03}", context=glossary.get("contexts", {}).get(item["source"], item.get("context", "")))
                for index, item in enumerate(items)]
    body = {"model": model, "thinking": {"type": "disabled"}, "temperature": 0,
            "max_tokens": max_tokens, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps({"items": numbered}, ensure_ascii=False)}]}
    encoded = json.dumps(body).encode()
    if len(encoded) > 60000:
        raise ValueError("Request exceeds 60 KB limit; use a smaller batch")
    request = urllib.request.Request("https://api.deepseek.com/chat/completions", data=encoded,
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Provider bodies and request headers may contain secrets; never echo them.
        raise ValueError(f"DeepSeek HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("DeepSeek connection failed or timed out; no automatic retry") from None
    elapsed = time.perf_counter() - start
    choice = result.get("choices", [{}])[0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("DeepSeek output incomplete; no candidate accepted or automatic retry")
    content = choice.get("message", {}).get("content")
    if not content:
        raise ValueError("DeepSeek returned empty content; no candidate accepted")
    data = json.loads(content, object_pairs_hook=validation.unique_object)
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON response object")
    translations = data.get("translations")
    if not isinstance(translations, list):
        raise ValueError("Invalid translations response")
    by_id = {}
    for item in translations:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in by_id:
            raise ValueError("Duplicate or malformed response ID")
        by_id[item.get("id")] = item
    if set(by_id) != {item["id"] for item in numbered}:
        raise ValueError("Missing or unexpected response IDs")
    candidates = []
    for item in numbered:
        output = by_id[item["id"]]
        text = output.get("text")
        issues = check_translation(item["source"], text, glossary)
        if not isinstance(output.get("review", ""), str):
            issues.append("Invalid review field")
        candidates.append({"key": item.get("key", item["source"]), "source": item["source"], "translation": text, "context": item.get("context", ""),
                           "checks": "rejected" if issues else "passed", "issues": issues,
                           "review": output.get("review", ""), "status": "needs_review"})
    return candidates, {"model": result.get("model"), "elapsed_seconds": round(elapsed, 3),
                        "request_bytes": len(encoded), "usage": result.get("usage", {})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "Compositor/Localizable.xcstrings")
    parser.add_argument("--glossary", type=Path, default=ROOT / "docs/localization-glossary.json")
    parser.add_argument("--sample", type=Path, help="Evaluate provided [{source, context}] without changing the catalog")
    parser.add_argument("--env-file", type=Path, help="Read only DEEPSEEK_API_KEY from a private existing env file")
    parser.add_argument("--output", type=Path, help="New candidate report file; existing files are never overwritten")
    parser.add_argument("--dry-run", action="store_true", help="Show queue size; no API call and no credential needed")
    parser.add_argument("--limit", type=int, default=40, help="At most 200 items per invocation")
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--max-requests", type=int, default=1, help="At most 5 calls; no automatic retries")
    parser.add_argument("--max-tokens", type=int, default=4096, help="At most 8192 output tokens per call")
    parser.add_argument("--model", choices=["deepseek-flash"], default="deepseek-flash")
    args = parser.parse_args()
    if not (1 <= args.limit <= 200 and 1 <= args.batch_size <= 40 and 1 <= args.max_requests <= 5 and 1 <= args.max_tokens <= 8192):
        parser.error("Invalid item, batch, request or token limit")
    catalog, glossary = read_json(args.catalog), read_json(args.glossary)
    if catalog.get("sourceLanguage") != "en":
        parser.error("Only English source catalogs are supported")
    items = read_json(args.sample) if args.sample else pending_items(catalog)
    if not isinstance(items, list) or any(not isinstance(i, dict) or not isinstance(i.get("source"), str) or not isinstance(i.get("context", ""), str) for i in items):
        parser.error("Input must be a list of source/context objects")
    selected = items[:min(args.limit, args.batch_size * args.max_requests)]
    print(f"Pending {len(items)}; selected {len(selected)}; API calls limited to {args.max_requests}.")
    if args.dry_run or not selected:
        print("No API call made." if args.dry_run else "No missing translations; no API call made.")
        return
    if not args.output:
        parser.error("--output is required for candidate reports")
    key = api_key(args.env_file)
    lock = Path(str(args.output) + ".lock")
    # Reserve a separate lock before billing. Publish a complete JSON receipt atomically, without replacing a report.
    with lock.open("x"):
        try:
            if args.output.exists():
                raise ValueError("Candidate report already exists; choose a new output")
            report = {"created_at": datetime.now(timezone.utc).isoformat(), "mode": "evaluation" if args.sample else "missing",
                      "catalog_sha256": digest(args.catalog), "glossary_sha256": digest(args.glossary),
                      "pending": len(items), "selected": len(selected), "remaining": len(items) - len(selected),
                      "status": "incomplete", "requests": [], "candidates": []}
            try:
                for offset in range(0, len(selected), args.batch_size):
                    candidates, receipt = translate(selected[offset:offset + args.batch_size], glossary, key, args.model, args.max_tokens)
                    report["candidates"].extend(candidates)
                    report["requests"].append(receipt)
                report["status"] = "needs_review"
            except (ValueError, OSError) as error:
                report["error"] = str(error) if isinstance(error, ValueError) else "Request or file operation failed"
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, delete=False) as destination:
                    temporary = Path(destination.name)
                    destination.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
                    destination.flush()
                    os.fsync(destination.fileno())
                os.link(temporary, args.output)  # Exclusive publication; a concurrent file is never overwritten.
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        finally:
            lock.unlink()
    rejected = sum(item["checks"] == "rejected" for item in report["candidates"])
    print(f"Report: {len(report['candidates'])} candidates, {rejected} rejected; catalog unchanged.")
    if report["status"] == "incomplete" or rejected:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error) if isinstance(error, ValueError) else "Local file operation failed", file=sys.stderr)
        raise SystemExit(1)
