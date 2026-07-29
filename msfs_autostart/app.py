from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import ConfigLocation, ExeXmlDocument, LaunchEntry, discover_configs


BG = "#101820"
PANEL = "#18232d"
PANEL_2 = "#202d38"
TEXT = "#eef4f7"
MUTED = "#9db0bd"
CYAN = "#36d6c4"
AMBER = "#f2b84b"
RED = "#ff6b6b"


class EntryDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, entry: LaunchEntry | None = None):
        super().__init__(parent)
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
        ttk.Label(body, text="显示名称", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=7)
        name_entry = ttk.Entry(body, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=7)
        ttk.Label(body, text="程序路径", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=7)
        ttk.Entry(body, textvariable=self.path_var).grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Button(body, text="浏览...", command=self._browse, style="Secondary.TButton").grid(row=2, column=2, padx=(8, 0), pady=7)
        ttk.Label(body, text="启动参数", style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Entry(body, textvariable=self.args_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=7)

        actions = ttk.Frame(body, style="Panel.TFrame")
        actions.grid(row=4, column=0, columnspan=3, sticky="e", pady=(20, 0))
        ttk.Button(actions, text="取消", command=self.destroy, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="保存", command=self._save, style="Accent.TButton").pack(side="left")
        body.columnconfigure(1, weight=1)
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Return>", lambda _event: self._save())
        name_entry.focus_set()

    def _browse(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="选择要随 MSFS 启动的程序",
            filetypes=[("Windows 程序", "*.exe"), ("所有文件", "*.*")],
        )
        if selected:
            self.path_var.set(selected)
            if not self.name_var.get().strip():
                self.name_var.set(Path(selected).stem)

    def _save(self) -> None:
        name = self.name_var.get().strip()
        path = os.path.expandvars(self.path_var.get().strip().strip('"'))
        if not name:
            messagebox.showwarning("缺少名称", "请输入程序的显示名称。", parent=self)
            return
        if not path:
            messagebox.showwarning("缺少路径", "请选择程序文件。", parent=self)
            return
        if Path(path).suffix.lower() != ".exe":
            if not messagebox.askyesno("不是 EXE 文件", "所选文件不是 .exe 程序，仍要添加吗？", parent=self):
                return
        self.result = (name, path, self.args_var.get().strip())
        self.destroy()


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MSFS 自启动管理器")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG)
        self.locations: list[ConfigLocation] = []
        self.document: ExeXmlDocument | None = None
        self.entries: list[LaunchEntry] = []
        self.status_var = tk.StringVar(value="正在查找配置...")
        self.config_var = tk.StringVar()
        self._configure_styles()
        self._build_ui()
        self.after(80, self._discover)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Root.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 10))
        style.configure("DialogTitle.TLabel", background=PANEL, foreground=TEXT, font=("Microsoft YaHei UI", 15, "bold"))
        style.configure("Field.TLabel", background=PANEL, foreground=MUTED, font=("Microsoft YaHei UI", 9))
        style.configure("Status.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 9))
        style.configure("Accent.TButton", background=CYAN, foreground="#07120f", padding=(15, 9), font=("Microsoft YaHei UI", 9, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#6ee5d7"), ("disabled", "#41645f")])
        style.configure("Secondary.TButton", background=PANEL_2, foreground=TEXT, padding=(13, 9), font=("Microsoft YaHei UI", 9), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#2c3c48")])
        style.configure("Danger.TButton", background="#4a262b", foreground="#ffb4b4", padding=(13, 9), font=("Microsoft YaHei UI", 9), borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#633038")])
        style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=TEXT, arrowcolor=CYAN, padding=7)
        style.configure("TEntry", fieldbackground=PANEL_2, foreground=TEXT, insertcolor=TEXT, bordercolor="#344652", padding=7)
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=42, borderwidth=0, font=("Microsoft YaHei UI", 9))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, relief="flat", padding=(8, 10), font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#245a5a")], foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", "#293945")])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=(28, 24, 28, 20), style="Root.TFrame")
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root, style="Root.TFrame")
        header.pack(fill="x", pady=(0, 20))
        titles = ttk.Frame(header, style="Root.TFrame")
        titles.pack(side="left")
        ttk.Label(titles, text="MSFS 自启动管理器", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="管理 MSFS 2020 / 2024 随模拟器启动的外部程序", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        picker = ttk.Frame(header, style="Root.TFrame")
        picker.pack(side="right", fill="x")
        ttk.Label(picker, text="配置来源", style="Subtitle.TLabel").pack(anchor="w")
        self.config_combo = ttk.Combobox(picker, textvariable=self.config_var, state="readonly", width=42)
        self.config_combo.pack(pady=(5, 0))
        self.config_combo.bind("<<ComboboxSelected>>", self._on_config_selected)

        table_wrap = ttk.Frame(root, style="Panel.TFrame")
        table_wrap.pack(fill="both", expand=True)
        columns = ("status", "name", "path", "args", "file")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", selectmode="browse")
        headings = {"status": "状态", "name": "程序", "path": "路径", "args": "启动参数", "file": "文件"}
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
        self.add_button = ttk.Button(actions, text="+ 添加程序", command=self._add, style="Accent.TButton")
        self.add_button.pack(side="left")
        self.edit_button = ttk.Button(actions, text="编辑", command=self._edit, style="Secondary.TButton")
        self.edit_button.pack(side="left", padx=(8, 0))
        self.toggle_button = ttk.Button(actions, text="停用", command=self._toggle, style="Secondary.TButton")
        self.toggle_button.pack(side="left", padx=(8, 0))
        self.open_button = ttk.Button(actions, text="打开位置", command=self._open_location, style="Secondary.TButton")
        self.open_button.pack(side="left", padx=(8, 0))
        self.delete_button = ttk.Button(actions, text="删除", command=self._delete, style="Danger.TButton")
        self.delete_button.pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="选择其他 exe.xml", command=self._choose_config, style="Secondary.TButton").pack(side="right")
        ttk.Button(actions, text="刷新", command=self._reload, style="Secondary.TButton").pack(side="right", padx=(0, 8))
        ttk.Label(root, textvariable=self.status_var, style="Status.TLabel").pack(fill="x", pady=(14, 0))
        self._sync_buttons()

    def _discover(self) -> None:
        self.locations = discover_configs()
        self._update_combo()
        if not self.locations:
            self.status_var.set("未自动找到 MSFS 2020 / 2024 配置，可点击“选择其他 exe.xml”。")
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
        selected = filedialog.askopenfilename(title="选择 MSFS exe.xml", filetypes=[("MSFS 配置", "exe.xml"), ("XML 文件", "*.xml")])
        if not selected:
            return
        path = Path(selected)
        for index, item in enumerate(self.locations):
            if item.path == path:
                self.config_combo.current(index)
                self._load(path)
                return
        self.locations.append(ConfigLocation("自定义配置", path))
        self._update_combo()
        self.config_combo.current(len(self.locations) - 1)
        self._load(path)

    def _load(self, path: Path) -> None:
        try:
            self.document = ExeXmlDocument(path)
            self._refresh_table()
            self.status_var.set(f"已载入 {len(self.entries)} 个程序  |  {path}")
        except (OSError, ValueError, Exception) as exc:
            self.document = None
            self.entries = []
            self._refresh_table()
            messagebox.showerror("无法读取配置", f"配置文件无法读取：\n\n{exc}", parent=self)
            self.status_var.set("配置载入失败。")

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
            status = "已停用" if entry.disabled else "已启用"
            file_state = "存在" if entry.exists else "缺失"
            tags = ("missing",) if not entry.exists else (("disabled",) if entry.disabled else ())
            self.tree.insert("", "end", iid=str(index), values=(status, entry.name, entry.path, entry.arguments or "-", file_state), tags=tags)
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
            self.toggle_button.configure(text="启用" if entry.disabled else "停用")

    def _add(self) -> None:
        if not self.document:
            return
        dialog = EntryDialog(self, "添加自启动程序")
        self.wait_window(dialog)
        if dialog.result:
            self.document.add(*dialog.result)
            self._commit("程序已添加")

    def _edit(self) -> None:
        entry = self._selected()
        if not entry or not self.document:
            return
        dialog = EntryDialog(self, "编辑自启动程序", entry)
        self.wait_window(dialog)
        if dialog.result:
            self.document.update(entry, *dialog.result)
            self._commit("修改已保存")

    def _toggle(self) -> None:
        entry = self._selected()
        if entry and self.document:
            self.document.toggle(entry)
            self._commit("程序已启用" if entry.disabled else "程序已停用")

    def _delete(self) -> None:
        entry = self._selected()
        if not entry or not self.document:
            return
        if messagebox.askyesno("删除自启动项", f"确定从 MSFS 自启动配置中删除“{entry.name}”吗？\n\n不会删除程序本身。", icon="warning", parent=self):
            self.document.remove(entry)
            self._commit("自启动项已删除，程序文件未受影响")

    def _open_location(self) -> None:
        entry = self._selected()
        if not entry:
            return
        path = Path(os.path.expandvars(entry.path.strip().strip('"')))
        if not path.exists():
            messagebox.showwarning("文件不存在", f"找不到程序：\n{path}", parent=self)
            return
        subprocess.Popen(["explorer", "/select,", str(path)])

    def _commit(self, message: str) -> None:
        if not self.document:
            return
        try:
            backup = self.document.save()
            self._refresh_table()
            suffix = f"  |  备份：{backup.name}" if backup else ""
            self.status_var.set(message + suffix)
        except OSError as exc:
            messagebox.showerror("保存失败", f"无法写入配置文件：\n\n{exc}", parent=self)
            self._reload()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("此工具仅支持 Windows。")
    app = MainWindow()
    app.mainloop()
