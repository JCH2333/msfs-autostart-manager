from __future__ import annotations

import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ConfigLocation:
    label: str
    path: Path


@dataclass
class LaunchEntry:
    element: ET.Element
    name: str
    path: str
    arguments: str
    disabled: bool
    manual_load: bool
    new_console: bool

    @property
    def exists(self) -> bool:
        return Path(os.path.expandvars(self.path.strip().strip('"'))).is_file()


def discover_configs() -> list[ConfigLocation]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    roaming = Path(os.environ.get("APPDATA", ""))
    candidates = [
        ConfigLocation(
            "MSFS 2024 - Microsoft Store / Xbox",
            local / "Packages" / "Microsoft.Limitless_8wekyb3d8bbwe" / "LocalCache" / "exe.xml",
        ),
        ConfigLocation(
            "MSFS 2024 - Steam",
            roaming / "Microsoft Flight Simulator 2024" / "exe.xml",
        ),
        ConfigLocation(
            "MSFS 2020 - Microsoft Store / Xbox",
            local / "Packages" / "Microsoft.FlightSimulator_8wekyb3d8bbwe" / "LocalCache" / "exe.xml",
        ),
        ConfigLocation(
            "MSFS 2020 - Steam",
            roaming / "Microsoft Flight Simulator" / "exe.xml",
        ),
    ]
    return [item for item in candidates if item.path.is_file()]


class ExeXmlDocument:
    def __init__(self, path: Path):
        self.path = path
        self.tree: ET.ElementTree
        self.root: ET.Element
        self.load()

    def load(self) -> None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.root = ET.Element("SimBase.Document", {"Type": "SimConnect", "version": "1,0"})
            ET.SubElement(self.root, "Descr").text = "Auto launch external applications on MSFS start"
            ET.SubElement(self.root, "Filename").text = "exe.xml"
            ET.SubElement(self.root, "Disabled").text = "False"
            self.tree = ET.ElementTree(self.root)
            return
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()
        if self.root.tag != "SimBase.Document":
            raise ValueError("Invalid MSFS exe.xml configuration file.")

    def entries(self) -> list[LaunchEntry]:
        result: list[LaunchEntry] = []
        for element in self.root.findall("Launch.Addon"):
            result.append(
                LaunchEntry(
                    element=element,
                    name=self._text(element, "Name"),
                    path=self._text(element, "Path"),
                    arguments=self._text(element, "CommandLine"),
                    disabled=self._bool(element, "Disabled"),
                    manual_load=self._bool(element, "ManualLoad"),
                    new_console=self._bool(element, "NewConsole"),
                )
            )
        return result

    def add(self, name: str, path: str, arguments: str = "") -> LaunchEntry:
        element = ET.SubElement(self.root, "Launch.Addon")
        ET.SubElement(element, "Name").text = name
        ET.SubElement(element, "Disabled").text = "False"
        ET.SubElement(element, "Path").text = path
        if arguments:
            ET.SubElement(element, "CommandLine").text = arguments
        return self.entries()[-1]

    def update(self, entry: LaunchEntry, name: str, path: str, arguments: str) -> None:
        self._set(entry.element, "Name", name)
        self._set(entry.element, "Path", path)
        self._set_optional(entry.element, "CommandLine", arguments)

    def toggle(self, entry: LaunchEntry) -> None:
        self._set(entry.element, "Disabled", "False" if entry.disabled else "True")

    def remove(self, entry: LaunchEntry) -> None:
        self.root.remove(entry.element)

    def save(self) -> Path | None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        backup: Path | None = None
        if self.path.exists() and self.path.stat().st_size:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = self.path.with_name(f"exe.xml.backup-{stamp}")
            shutil.copy2(self.path, backup)

        ET.indent(self.tree, space="  ")
        handle, temp_name = tempfile.mkstemp(prefix="exe-", suffix=".xml", dir=self.path.parent)
        os.close(handle)
        temp_path = Path(temp_name)
        try:
            self.tree.write(temp_path, encoding="utf-8", xml_declaration=True)
            os.replace(temp_path, self.path)
        finally:
            temp_path.unlink(missing_ok=True)
        return backup

    @staticmethod
    def _text(element: ET.Element, tag: str) -> str:
        child = element.find(tag)
        return (child.text or "").strip() if child is not None else ""

    @classmethod
    def _bool(cls, element: ET.Element, tag: str) -> bool:
        return cls._text(element, tag).lower() in {"true", "1", "yes"}

    @staticmethod
    def _set(element: ET.Element, tag: str, value: str) -> None:
        child = element.find(tag)
        if child is None:
            child = ET.SubElement(element, tag)
        child.text = value

    @staticmethod
    def _set_optional(element: ET.Element, tag: str, value: str) -> None:
        child = element.find(tag)
        if value:
            if child is None:
                child = ET.SubElement(element, tag)
            child.text = value
        elif child is not None:
            element.remove(child)
