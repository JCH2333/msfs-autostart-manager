from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import ConfigLocation, ExeXmlDocument, LaunchEntry, discover_configs
from .i18n import translator
from .settings import load_language, save_language


BG = "#101820"
PANEL = "#18232d"
PANEL_2 = "#202d38"
TEXT = "#eef4f7"
MUTED = "#9db0bd"
CYAN = "#36d6c4"
AMBER = "#f2b84b"
RED = "#ff6b6b"


class EntryDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        translate: Callable[..., str],
        entry: LaunchEntry | None = None,
    ):
        super().__init__(parent)
        self.t = translate
        self.result: tuple[str, str, str] | None = None
        self.title(title)
        self.geometry("620x294")
        self.resizable(False, False)
        self.configure(bg=PANEL)
        self.transient(parent)
        self.grab_set()

        self.name_var = tk.StringVar(value=entry.name if entry else "")
        self.path_var = tk.StringVar(value=entry.path if entry else "")
        self.args_var = tk.StringVar(value=entry.arguments if entry else "")

        body = ttk.Frame(self, padding=24, style="Panel.TFrame")
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=title, style="DialogTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 18))
        ttk.Label(body, text=self.t("display_name"), style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=7)
        name_entry = ttk.Entry(body, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=7)
        ttk.Label(body, text=self.t("program_path"), style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=7)
        ttk.Entry(body, textvariable=self.path_var).grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Button(body, text=self.t("browse"), command=self._browse, style="Secondary.TButton").grid(row=2, column=2, padx=(8, 0), pady=7)
        ttk.Label(body, text=self.t("startup_args"), style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Entry(body, textvariable=self.args_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=7)

        actions = ttk.Frame(body, style="Panel.TFrame")
        actions.grid(row=4, column=0, columnspan=3, sticky="e", pady=(20, 0))
        ttk.Button(actions, text=self.t("cancel"), command=self.destroy, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text=self.t("save"), command=self._save, style="Accent.TButton").pack(side="left")
        body.columnconfigure(1, weight=1)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Return>", lambda _event: self._save())
        name_entry.focus_set()

    def _browse(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title=self.t("browse_program"),
            filetypes=[(self.t("windows_program"), "*.exe"), (self.t("all_files"), "*.*")],
        )
        if selected:
            self.path_var.set(selected)
            if not self.name_var.get().strip():
                self.name_var.set(Path(selected).stem)

    def _save(self) -> None:
        name = self.name_var.get().strip()
        path = os.path.expandvars(self.path_var.get().strip().strip('"'))
        if not name:
            messagebox.showwarning(self.t("missing_name"), self.t("missing_name_body"), parent=self)
            return
        if not path:
            messagebox.showwarning(self.t("missing_path"), self.t("missing_path_body"), parent=self)
            return
        if Path(path).suffix.lower() != ".exe":
            if not messagebox.askyesno(self.t("not_exe"), self.t("not_exe_body"), parent=self):
                return
        self.result = (name, path, self.args_var.get().strip())
        self.destroy()


class LanguageSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.result: str | None = None
        self.title("Language / 语言")
        self.geometry("520x320")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        frame = tk.Frame(self, bg=BG, padx=38, pady=34)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="Choose your language",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            frame,
            text="选择界面语言",
            bg=BG,
            fg=MUTED,
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", pady=(5, 26))

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill="x")
        self._language_button(buttons, "中文", "简体中文", "zh").pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._language_button(buttons, "English", "English", "en").pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _language_button(self, parent: tk.Misc, title: str, subtitle: str, language: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=f"{title}\n{subtitle}",
            command=lambda: self._select(language),
            bg=PANEL_2,
            activebackground=CYAN,
            fg=TEXT,
            activeforeground="#07120f",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Microsoft YaHei UI" if language == "zh" else "Segoe UI", 13, "bold"),
            height=4,
        )
        button.bind("<Enter>", lambda _event: button.configure(bg="#2c3c48"))
        button.bind("<Leave>", lambda _event: button.configure(bg=PANEL_2))
        return button

    def _select(self, language: str) -> None:
        save_language(language)
        self.result = language
        self.destroy()


class MainWindow(tk.Tk):
    def __init__(self, language: str):
        super().__init__()
        self.language = language
        self.t = translator(language)
        self.next_language: str | None = None
        self.font_family = "Microsoft YaHei UI" if language == "zh" else "Segoe UI"
        self.title(self.t("app_title"))
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG)
        self.locations: list[ConfigLocation] = []
        self.document: ExeXmlDocument | None = None
        self.entries: list[LaunchEntry] = []
        self.status_var = tk.StringVar(value=self.t("starting"))
        self.config_var = tk.StringVar()
        self._configure_styles()
        self._build_ui()
        self.after(80, self._discover)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Root.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(self.font_family, 21, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=(self.font_family, 10))
        style.configure("DialogTitle.TLabel", background=PANEL, foreground=TEXT, font=(self.font_family, 15, "bold"))
        style.configure("Field.TLabel", background=PANEL, foreground=MUTED, font=(self.font_family, 9))
        style.configure("Status.TLabel", background=BG, foreground=MUTED, font=(self.font_family, 9))
        style.configure("Accent.TButton", background=CYAN, foreground="#07120f", padding=(15, 9), font=(self.font_family, 9, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#6ee5d7"), ("disabled", "#41645f")])
        style.configure("Secondary.TButton", background=PANEL_2, foreground=TEXT, padding=(13, 9), font=(self.font_family, 9), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#2c3c48")])
        style.configure("Danger.TButton", background="#4a262b", foreground="#ffb4b4", padding=(13, 9), font=(self.font_family, 9), borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#633038")])
        style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT, arrowcolor=CYAN, padding=7)
        style.configure("TEntry", fieldbackground=PANEL_2, foreground=TEXT, insertcolor=TEXT, bordercolor="#344652", padding=7)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=42, borderwidth=0, font=(self.font_family, 9))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, relief="flat", padding=(8, 10), font=(self.font_family, 9, "bold"))
        style.map("Treeview", background=[("selected", "#245a5a")], foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", "#293945")])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=(28, 24, 28, 20), style="Root.TFrame")
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root, style="Root.TFrame")
        header.pack(fill="x", pady=(0, 20))
        titles = ttk.Frame(header, style="Root.TFrame")
        titles.pack(side="left")
        ttk.Label(titles, text=self.t("app_title"), style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text=self.t("subtitle"), style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        picker = ttk.Frame(header, style="Root.TFrame")
        picker.pack(side="right", fill="x")
        ttk.Label(picker, text=self.t("config_source"), style="Subtitle.TLabel").pack(anchor="w")
        picker_row = ttk.Frame(picker, style="Root.TFrame")
        picker_row.pack(pady=(5, 0))
        self.config_combo = ttk.Combobox(picker_row, textvariable=self.config_var, state="readonly", width=38)
        self.config_combo.pack(side="left")
        self.config_combo.bind("<<ComboboxSelected>>", self._on_config_selected)
        ttk.Button(
            picker_row,
            text=self.t("switch_language"),
            command=self._switch_language,
            style="Secondary.TButton",
        ).pack(side="left", padx=(8, 0))

        table_wrap = ttk.Frame(root, style="Panel.TFrame")
        table_wrap.pack(fill="both", expand=True)
        columns = ("status", "name", "path", "args", "file")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", selectmode="browse")
        headings = {
            "status": self.t("status"),
            "name": self.t("program"),
            "path": self.t("path"),
            "args": self.t("arguments"),
            "file": self.t("file"),
        }
        for column, label in headings.items():
            self.tree.heading(column, text=label)
        self.tree.column("status", width=82, minwidth=72, stretch=False, anchor="center")
        self.tree.column("name", width=185, minwidth=120)
        self.tree.column("path", width=440, minwidth=220)
        self.tree.column("args", width=180, minwidth=100)
        self.tree.column("file", width=86, minwidth=72, stretch=False, anchor="center")
        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure("disabled", foreground="#71828e")
        self.tree.tag_configure("missing", foreground="#ff9a9a")
        self.tree.bind("<Double-1>", lambda _event: self._edit())
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._sync_buttons())

        actions = ttk.Frame(root, style="Root.TFrame")
        actions.pack(fill="x", pady=(18, 0))
        self.add_button = ttk.Button(actions, text=self.t("add_program"), command=self._add, style="Accent.TButton")
        self.add_button.pack(side="left")
        self.edit_button = ttk.Button(actions, text=self.t("edit"), command=self._edit, style="Secondary.TButton")
        self.edit_button.pack(side="left", padx=(8, 0))
        self.toggle_button = ttk.Button(actions, text=self.t("disable"), command=self._toggle, style="Secondary.TButton")
        self.toggle_button.pack(side="left", padx=(8, 0))
        self.open_button = ttk.Button(actions, text=self.t("open_location"), command=self._open_location, style="Secondary.TButton")
        self.open_button.pack(side="left", padx=(8, 0))
        self.delete_button = ttk.Button(actions, text=self.t("delete"), command=self._delete, style="Danger.TButton")
        self.delete_button.pack(side="left", padx=(8, 0))
        ttk.Button(actions, text=self.t("choose_config"), command=self._choose_config, style="Secondary.TButton").pack(side="right")
        ttk.Button(actions, text=self.t("refresh"), command=self._reload, style="Secondary.TButton").pack(side="right", padx=(0, 8))
        ttk.Label(root, textvariable=self.status_var, style="Status.TLabel").pack(fill="x", pady=(14, 0))
        self._sync_buttons()

    def _discover(self) -> None:
        self.locations = discover_configs()
        self._update_combo()
        if not self.locations:
            self.status_var.set(self.t("no_configs"))
            return
        best = next(
            (index for index, item in enumerate(self.locations) if item.path.stat().st_size > 0),
            0,
        )
        self.config_combo.current(best)
        self._load(self.locations[best].path)

    def _update_combo(self) -> None:
        self.config_combo["values"] = [f"{item.label}  |  {item.path}" for item in self.locations]

    def _on_config_selected(self, _event: tk.Event) -> None:
        index = self.config_combo.current()
        if index >= 0:
            self._load(self.locations[index].path)

    def _choose_config(self) -> None:
        selected = filedialog.askopenfilename(
            title=self.t("choose_msfs_config"),
            filetypes=[(self.t("msfs_config"), "exe.xml"), (self.t("xml_file"), "*.xml")],
        )
        if not selected:
            return
        path = Path(selected)
        for index, item in enumerate(self.locations):
            if item.path == path:
                self.config_combo.current(index)
                self._load(path)
                return
        self.locations.append(ConfigLocation(self.t("custom_config"), path))
        self._update_combo()
        self.config_combo.current(len(self.locations) - 1)
        self._load(path)

    def _load(self, path: Path) -> None:
        try:
            self.document = ExeXmlDocument(path)
            self._refresh_table()
            self.status_var.set(self.t("loaded", count=len(self.entries), path=path))
        except (OSError, ValueError, Exception) as exc:
            self.document = None
            self.entries = []
            self._refresh_table()
            messagebox.showerror(self.t("read_error"), self.t("read_error_body", error=exc), parent=self)
            self.status_var.set(self.t("load_failed"))

    def _reload(self) -> None:
        if self.document:
            self._load(self.document.path)
        else:
            self._discover()

    def _refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.entries = self.document.entries() if self.document else []
        for index, entry in enumerate(self.entries):
            status = self.t("disabled") if entry.disabled else self.t("enabled")
            file_state = self.t("exists") if entry.exists else self.t("missing")
            tags = ("missing",) if not entry.exists else (("disabled",) if entry.disabled else ())
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(status, entry.name or self.t("unnamed"), entry.path, entry.arguments or "-", file_state),
                tags=tags,
            )
        self._sync_buttons()

    def _selected(self) -> LaunchEntry | None:
        selection = self.tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        return self.entries[index] if index < len(self.entries) else None

    def _sync_buttons(self) -> None:
        entry = self._selected()
        state = "normal" if entry else "disabled"
        for button in (self.edit_button, self.toggle_button, self.open_button, self.delete_button):
            button.configure(state=state)
        self.add_button.configure(state="normal" if self.document else "disabled")
        if entry:
            self.toggle_button.configure(text=self.t("enable") if entry.disabled else self.t("disable"))

    def _add(self) -> None:
        if not self.document:
            return
        dialog = EntryDialog(self, self.t("add_dialog"), self.t)
        self.wait_window(dialog)
        if dialog.result:
            self.document.add(*dialog.result)
            self._commit("added")

    def _edit(self) -> None:
        entry = self._selected()
        if not entry or not self.document:
            return
        dialog = EntryDialog(self, self.t("edit_dialog"), self.t, entry)
        self.wait_window(dialog)
        if dialog.result:
            self.document.update(entry, *dialog.result)
            self._commit("modified")

    def _toggle(self) -> None:
        entry = self._selected()
        if entry and self.document:
            self.document.toggle(entry)
            self._commit("enabled_message" if entry.disabled else "disabled_message")

    def _delete(self) -> None:
        entry = self._selected()
        if not entry or not self.document:
            return
        if messagebox.askyesno(
            self.t("delete_title"),
            self.t("delete_body", name=entry.name or self.t("unnamed")),
            icon="warning",
            parent=self,
        ):
            self.document.remove(entry)
            self._commit("deleted")

    def _open_location(self) -> None:
        entry = self._selected()
        if not entry:
            return
        path = Path(os.path.expandvars(entry.path.strip().strip('"')))
        if not path.exists():
            messagebox.showwarning(self.t("file_missing"), self.t("file_missing_body", path=path), parent=self)
            return
        subprocess.Popen(["explorer", "/select,", str(path)])

    def _commit(self, message_key: str) -> None:
        if not self.document:
            return
        try:
            backup = self.document.save()
            self._refresh_table()
            suffix = f"  |  {self.t('backup', name=backup.name)}" if backup else ""
            self.status_var.set(self.t(message_key) + suffix)
        except OSError as exc:
            messagebox.showerror(self.t("save_failed"), self.t("save_failed_body", error=exc), parent=self)
            self._reload()

    def _switch_language(self) -> None:
        selected = "en" if self.language == "zh" else "zh"
        save_language(selected)
        self.next_language = selected
        self.destroy()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("This tool supports Windows only.")

    language = load_language()
    if language is None:
        selector = LanguageSelector()
        selector.mainloop()
        language = selector.result
    while language:
        app = MainWindow(language)
        app.mainloop()
        language = app.next_language
