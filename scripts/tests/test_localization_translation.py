import copy
from contextlib import redirect_stdout
import io
import tempfile
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("translator", ROOT / "scripts/translate-localization.py")
translator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(translator)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.glossary = translator.read_json(ROOT / "docs/localization-glossary.json")

    def test_domain_terms_reject_literal_dictionary_meanings(self):
        for source, good, bad in [("Screen", "滤色", "屏幕"), ("Multiply", "正片叠底", "乘法"),
                                  ("Stroke", "描边", "笔画"), ("Clipping Mask", "剪贴蒙版", "剪切遮罩")]:
            self.assertEqual(translator.check_translation(source, good, self.glossary), [])
            self.assertTrue(translator.check_translation(source, bad, self.glossary))

    def test_placeholders_preserve_position_multiplicity_type_and_precision(self):
        self.assertEqual(translator.format_signature("%lld %@"), translator.format_signature("%2$@ %1$lld"))
        for original, bad in [("%@", "%@ %@"), ("%@ %@", "%1$@ %1$@"), ("%lld", "%d"),
                              ("%.2f", "%.0f"), ("100%% %@", "100% %@")]:
            self.assertNotEqual(translator.format_signature(original), translator.format_signature(bad))

    def test_shortcuts_protected_names_and_numbers_are_checked(self):
        source = "New blank layer (⇧⌘N)"
        self.assertEqual(translator.check_translation(source, "新建空白图层（⇧⌘N）", self.glossary), [])
        self.assertTrue(translator.check_translation(source, "新建空白图层（⌘N）", self.glossary))
        self.assertTrue(translator.check_translation(source, "新建空白图层（⇧⌘M）", self.glossary))
        self.assertTrue(translator.check_translation("Move / Transform (V)", "移动/变换（M）", self.glossary))
        self.assertTrue(translator.check_translation("Export PNG…", "导出 JPEG…", self.glossary))
        self.assertTrue(translator.check_translation("Width 300 px", "宽度 30 px", self.glossary))
        self.assertEqual(translator.check_translation("Foreground color", "前景色", self.glossary), [])

    def test_ordinary_screen_and_dimension_summary_have_correct_context(self):
        self.assertEqual(translator.check_translation("Each pixel of the screen", "屏幕上的每个像素", self.glossary), [])
        self.assertTrue(translator.check_translation("Screen blend mode", "屏幕混合模式", self.glossary))
        source = "New: %lld × %lld pixels · %@ uncompressed"
        self.assertTrue(translator.check_translation(source, "新建：%lld × %lld 像素 · %@ 未压缩", self.glossary))
        self.assertEqual(translator.check_translation(source, "新尺寸：%lld × %lld 像素 · %@ 未压缩", self.glossary), [])

    def test_pending_queue_skips_existing_translations_and_nontranslatable_entries(self):
        catalog = {"strings": {
            "New Label": {},
            "Translated": {"localizations": {"zh-Hans": {"stringUnit": {"state": "translated", "value": "已有译文"}}}},
            "Do Not Translate": {"shouldTranslate": False},
            "Old Label": {"extractionState": "stale"},
            "%lld%%": {},
        }}
        original = copy.deepcopy(catalog)
        self.assertEqual(translator.pending_items(catalog), [{"source": "New Label", "context": ""}])
        self.assertEqual(catalog, original)

    def test_semantic_catalog_keys_are_preserved_and_plural_structures_are_not_flattened(self):
        catalog = {"strings": {"action.export": {"localizations": {"en": {"stringUnit": {"value": "Export…"}}}}}}
        self.assertEqual(translator.pending_items(catalog), [{"key": "action.export", "source": "Export…", "context": ""}])
        catalog["strings"]["action.export"]["localizations"]["en"] = {"variations": {"plural": {}}}
        with self.assertRaises(ValueError):
            translator.pending_items(catalog)

    def test_no_missing_entries_makes_no_request_without_credentials(self):
        with patch("sys.argv", ["translator"]), patch.object(translator, "api_key") as credentials, patch.object(translator, "translate") as request, redirect_stdout(io.StringIO()):
            translator.main()
        credentials.assert_not_called()
        request.assert_not_called()

    def test_candidate_report_preserves_catalog_respects_limits_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            catalog = Path(folder) / "source.xcstrings"
            output = Path(folder) / "candidate.json"
            catalog.write_text(json.dumps({"sourceLanguage": "en", "strings": {"Screen": {}, "Multiply": {}}}))
            before = catalog.read_bytes()
            candidates = [{"source": "Screen", "translation": "滤色", "checks": "passed", "status": "needs_review"}]
            args = ["translator", "--catalog", str(catalog), "--output", str(output), "--batch-size", "1"]
            with patch("sys.argv", args), patch.object(translator, "api_key", return_value="test-only"), patch.object(translator, "translate", return_value=(candidates, {"usage": {}})) as request, redirect_stdout(io.StringIO()):
                translator.main()
            self.assertEqual(request.call_count, 1)
            report = json.loads(output.read_text())
            self.assertEqual(report["selected"], 1)
            self.assertEqual(report["remaining"], 1)
            self.assertEqual(report["status"], "needs_review")
            self.assertEqual(catalog.read_bytes(), before)
            old_report = output.read_bytes()
            with patch("sys.argv", args), patch.object(translator, "api_key", return_value="test-only"), patch.object(translator, "translate") as request, redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    translator.main()
            request.assert_not_called()
            self.assertEqual(output.read_bytes(), old_report)
            self.assertFalse(Path(str(output) + ".lock").exists())

    def test_incomplete_empty_and_duplicate_responses_are_rejected(self):
        class Response:
            def __init__(self, value): self.value = value
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps(self.value).encode()
        for reason, content in [("length", '{"translations":[]}'), ("stop", ""),
                                ("stop", '{"translations":[{"id":"s000","text":"滤色"},{"id":"s000","text":"滤色"}]}'),
                                ("stop", '{"translations":[]}')]:
            response = {"choices": [{"finish_reason": reason, "message": {"content": content}}]}
            with patch.object(translator.urllib.request, "urlopen", return_value=Response(response)):
                with self.assertRaises(ValueError):
                    translator.translate([{"source": "Screen"}], self.glossary, "test-only-not-a-key", "deepseek-flash", 100)


if __name__ == "__main__":
    unittest.main()
