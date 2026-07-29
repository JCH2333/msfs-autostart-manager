import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from msfs_autostart.config import ExeXmlDocument, discover_configs


SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<SimBase.Document Type="SimConnect" version="1,0">
  <Descr>Test</Descr>
  <Filename>exe.xml</Filename>
  <Disabled>False</Disabled>
  <Launch.Addon>
    <Name>Tool A</Name>
    <Disabled>false</Disabled>
    <Path>C:\\Tools\\a.exe</Path>
    <CommandLine>--auto</CommandLine>
    <VendorField>preserve me</VendorField>
  </Launch.Addon>
</SimBase.Document>
"""


class ExeXmlDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "exe.xml"
        self.path.write_text(SAMPLE, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_reads_and_toggles_entry(self):
        document = ExeXmlDocument(self.path)
        entry = document.entries()[0]
        self.assertEqual(entry.name, "Tool A")
        self.assertFalse(entry.disabled)
        document.toggle(entry)
        document.save()
        reloaded = ExeXmlDocument(self.path)
        self.assertTrue(reloaded.entries()[0].disabled)
        self.assertEqual(reloaded.root.find("Launch.Addon/VendorField").text, "preserve me")

    def test_add_update_remove_and_backup(self):
        document = ExeXmlDocument(self.path)
        added = document.add("Tool B", "C:\\Tools\\b.exe", "--silent")
        document.update(added, "Tool B2", "D:\\b.exe", "")
        backup = document.save()
        self.assertIsNotNone(backup)
        self.assertTrue(backup.exists())
        reloaded = ExeXmlDocument(self.path)
        second = reloaded.entries()[1]
        self.assertEqual((second.name, second.path, second.arguments), ("Tool B2", "D:\\b.exe", ""))
        reloaded.remove(second)
        reloaded.save()
        self.assertEqual(len(ExeXmlDocument(self.path).entries()), 1)

    def test_empty_file_gets_valid_document(self):
        self.path.write_bytes(b"")
        document = ExeXmlDocument(self.path)
        document.add("Tool", "C:\\tool.exe")
        document.save()
        self.assertEqual(len(ExeXmlDocument(self.path).entries()), 1)


class ConfigDiscoveryTests(unittest.TestCase):
    def test_discovers_all_four_supported_editions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "Local"
            roaming = root / "Roaming"
            expected = [
                local / "Packages" / "Microsoft.Limitless_8wekyb3d8bbwe" / "LocalCache" / "exe.xml",
                roaming / "Microsoft Flight Simulator 2024" / "exe.xml",
                local / "Packages" / "Microsoft.FlightSimulator_8wekyb3d8bbwe" / "LocalCache" / "exe.xml",
                roaming / "Microsoft Flight Simulator" / "exe.xml",
            ]
            for path in expected:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            with patch.dict("os.environ", {"LOCALAPPDATA": str(local), "APPDATA": str(roaming)}):
                locations = discover_configs()

            self.assertEqual([item.path for item in locations], expected)
            self.assertEqual(
                [item.label for item in locations],
                [
                    "MSFS 2024 - Microsoft Store / Xbox",
                    "MSFS 2024 - Steam",
                    "MSFS 2020 - Microsoft Store / Xbox",
                    "MSFS 2020 - Steam",
                ],
            )

if __name__ == "__main__":
    unittest.main()
