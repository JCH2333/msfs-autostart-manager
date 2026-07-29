import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msfs_autostart.i18n import TRANSLATIONS, translator
from msfs_autostart.settings import load_language, save_language, settings_path


class TranslationTests(unittest.TestCase):
    def test_languages_have_identical_keys(self):
        self.assertEqual(set(TRANSLATIONS["zh"]), set(TRANSLATIONS["en"]))

    def test_translator_formats_values(self):
        self.assertEqual(translator("en")("loaded", count=3, path="C:\\exe.xml"), "Loaded 3 programs  |  C:\\exe.xml")
        self.assertIn("3", translator("zh")("loaded", count=3, path="C:\\exe.xml"))


class LanguageSettingsTests(unittest.TestCase):
    def test_first_run_has_no_language(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"LOCALAPPDATA": temp}):
            self.assertIsNone(load_language())

    def test_saves_and_loads_each_language(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"LOCALAPPDATA": temp}):
            save_language("en")
            self.assertEqual(load_language(), "en")
            save_language("zh")
            self.assertEqual(load_language(), "zh")
            self.assertEqual(settings_path(), Path(temp) / "MSFS Autostart Manager" / "settings.json")

    def test_invalid_setting_returns_none(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"LOCALAPPDATA": temp}):
            path = settings_path()
            path.parent.mkdir(parents=True)
            path.write_text('{"language": "fr"}', encoding="utf-8")
            self.assertIsNone(load_language())


if __name__ == "__main__":
    unittest.main()
