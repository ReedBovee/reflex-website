"""Media Buddy desktop interface (Tkinter).

Plug in a customer drive, pick the whole drive or one folder, scan, scroll the
live list, and export it as CSV.
"""

import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .export import write_csv
from .scanner import ScanOptions, human_size, list_drives, scan

# Reflex Technologies palette
BG = "#0f1214"
PANEL = "#171c1f"
FIELD = "#1f262a"
LINE = "#2b3439"
TEXT = "#e8eef0"
MUTED = "#8a979d"
TEAL = "#15ebdf"
AMBER = "#e6a24a"

COLUMNS = [
    # id, heading, width, anchor, stretch
    ("name", "File Name", 340, "w", True),
    ("type", "Type", 160, "w", False),
    ("ext", "Ext", 70, "w", False),
    ("size", "Size", 110, "e", False),
    ("created", "Created", 160, "w", False),
    ("modified", "Modified", 160, "w", False),
    ("frames", "Frames", 170, "e", False),
    ("folder", "Folder", 380, "w", True),
]

SORT_KEYS = {
    "name": lambda r: r.name.lower(),
    "type": lambda r: (r.category, r.name.lower()),
    "ext": lambda r: (r.ext, r.name.lower()),
    "size": lambda r: r.size,
    "created": lambda r: r.created or datetime.min,
    "modified": lambda r: r.modified or datetime.min,
    "frames": lambda r: r.frames,
    "folder": lambda r: (r.folder.lower(), r.name.lower()),
}

ALL_TYPES = "All types"
ROWS_PER_TICK = 1500


def _fmt_dt(value):
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


class MediaBuddyApp:
    def __init__(self, root):
        self.root = root
        self.records = []          # every record found in the current scan
        self.visible = []          # records currently shown, in display order
        self.pending = []          # records waiting to be inserted into the tree
        self.queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker = None
        self.scan_started = 0.0
        self.sort_col = None
        self.sort_reverse = False
        self.drive_paths = []

        root.title("Media Buddy  |  Reflex Technologies")
        root.configure(bg=BG)
        root.geometry("1280x800")
        root.minsize(900, 600)
        if sys.platform == "win32":
            root.state("zoomed")  # fill the tablet screen

        self._init_style()
        self._build()
        self.refresh_drives()
        self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------------ UI
    def _init_style(self):
        self.base_font = ("Segoe UI", 12) if sys.platform == "win32" else ("Helvetica", 12)
        bold = (self.base_font[0], 12, "bold")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, fieldbackground=FIELD,
                        bordercolor=LINE, lightcolor=PANEL, darkcolor=PANEL,
                        font=self.base_font)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED)
        style.configure("Status.TLabel", background=BG, foreground=MUTED,
                        font=(self.base_font[0], 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT,
                        font=(self.base_font[0], 22, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=TEAL,
                        font=(self.base_font[0], 11, "bold"))
        style.configure("Summary.TLabel", background=BG, foreground=TEXT, font=bold)

        style.configure("TRadiobutton", background=PANEL, foreground=TEXT, padding=6)
        style.map("TRadiobutton", background=[("active", PANEL)],
                  indicatorbackground=[("selected", TEAL), ("!selected", FIELD)],
                  indicatorforeground=[("selected", BG), ("!selected", FIELD)])
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT, padding=6)
        style.map("TCheckbutton", background=[("active", PANEL)],
                  indicatorbackground=[("selected", TEAL), ("!selected", FIELD)],
                  indicatorforeground=[("selected", BG), ("!selected", FIELD)])

        style.configure("TEntry", padding=8, foreground=TEXT, insertcolor=TEXT)
        style.configure("TCombobox", padding=8, foreground=TEXT, arrowcolor=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", FIELD)],
                  foreground=[("readonly", TEXT)], selectbackground=[("readonly", FIELD)])
        self.root.option_add("*TCombobox*Listbox.background", FIELD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.font", self.base_font)

        for name, bg, fg, hover in (
            ("TButton", FIELD, TEXT, LINE),
            ("Teal.TButton", TEAL, "#04201f", "#5ff3ea"),
            ("Amber.TButton", AMBER, "#2a1a05", "#f0bd78"),
        ):
            style.configure(name, background=bg, foreground=fg, padding=(16, 10),
                            borderwidth=0, focusthickness=0, font=bold)
            style.map(name, background=[("disabled", LINE), ("active", hover)],
                      foreground=[("disabled", MUTED)])

        # Tall rows and a wide scrollbar so the list is usable by finger.
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=32, borderwidth=0,
                        font=self.base_font)
        style.map("Treeview", background=[("selected", "#0d4d4a")],
                  foreground=[("selected", TEXT)])
        style.configure("Treeview.Heading", background=FIELD, foreground=TEAL,
                        relief="flat", padding=8, font=bold)
        style.map("Treeview.Heading", background=[("active", LINE)])
        style.configure("Vertical.TScrollbar", background=LINE, troughcolor=PANEL,
                        arrowcolor=TEXT, width=24, arrowsize=24)
        style.map("Vertical.TScrollbar", background=[("active", MUTED)])
        style.configure("Horizontal.TScrollbar", background=LINE, troughcolor=PANEL,
                        arrowcolor=TEXT, width=18, arrowsize=18)
        style.map("Horizontal.TScrollbar", background=[("active", MUTED)])
        style.configure("Horizontal.TProgressbar", background=TEAL, troughcolor=FIELD)

    def _build(self):
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        # --- Header -----------------------------------------------------
        header = ttk.Frame(root, padding=(18, 14, 18, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="MEDIA BUDDY", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"REFLEX TECHNOLOGIES  ·  DRIVE INVENTORY  ·  v{__version__}",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w")
        jobbox = ttk.Frame(header)
        jobbox.grid(row=0, column=2, rowspan=2, sticky="e")
        ttk.Label(jobbox, text="Job / Work Order #", foreground=MUTED).pack(anchor="e")
        self.job_var = tk.StringVar()
        ttk.Entry(jobbox, textvariable=self.job_var, width=18,
                  font=(self.base_font[0], 14)).pack(anchor="e")

        # --- Source + options -----------------------------------------
        panel = ttk.Frame(root, style="Panel.TFrame", padding=14)
        panel.grid(row=1, column=0, sticky="ew", padx=18, pady=6)
        panel.columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar(value="drive")
        ttk.Radiobutton(panel, text="Entire drive", value="drive", variable=self.mode_var,
                        command=self._mode_changed).grid(row=0, column=0, sticky="w")
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(panel, textvariable=self.drive_var, state="readonly")
        self.drive_combo.grid(row=0, column=1, sticky="ew", padx=8)
        self.drive_combo.bind("<<ComboboxSelected>>", lambda e: self.mode_var.set("drive"))
        ttk.Button(panel, text="Refresh drives", command=self.refresh_drives).grid(
            row=0, column=2, sticky="ew")

        ttk.Radiobutton(panel, text="One folder", value="folder", variable=self.mode_var,
                        command=self._mode_changed).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.folder_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.folder_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(8, 0))
        ttk.Button(panel, text="Choose folder…", command=self.choose_folder).grid(
            row=1, column=2, sticky="ew", pady=(8, 0))

        opts = ttk.Frame(panel, style="Panel.TFrame")
        opts.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.opt_video = tk.BooleanVar(value=True)
        self.opt_images = tk.BooleanVar(value=True)
        self.opt_audio = tk.BooleanVar(value=False)
        self.opt_group = tk.BooleanVar(value=True)
        self.opt_hidden = tk.BooleanVar(value=False)
        for text, var in (
            ("Video", self.opt_video),
            ("Still images + RAW", self.opt_images),
            ("Audio", self.opt_audio),
            ("Collapse film-scan frame sequences", self.opt_group),
            ("Include hidden/system folders", self.opt_hidden),
        ):
            ttk.Checkbutton(opts, text=text, variable=var).pack(side="left", padx=(0, 12))

        btns = ttk.Frame(panel, style="Panel.TFrame")
        btns.grid(row=2, column=2, sticky="e", pady=(10, 0))
        self.start_btn = ttk.Button(btns, text="▶  Start Scan", style="Teal.TButton",
                                    command=self.start_scan)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(btns, text="■  Stop", command=self.stop_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        # --- Filter bar ------------------------------------------------
        fbar = ttk.Frame(root, padding=(18, 4))
        fbar.grid(row=2, column=0, sticky="ew")
        fbar.columnconfigure(1, weight=1)
        ttk.Label(fbar, text="Search").grid(row=0, column=0, padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._schedule_refilter())
        ttk.Entry(fbar, textvariable=self.search_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(fbar, text="Show").grid(row=0, column=2, padx=(16, 8))
        self.type_var = tk.StringVar(value=ALL_TYPES)
        self.type_combo = ttk.Combobox(fbar, textvariable=self.type_var, state="readonly",
                                       width=18, values=[ALL_TYPES])
        self.type_combo.grid(row=0, column=3)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refilter())

        # --- Results list ----------------------------------------------
        table = ttk.Frame(root, padding=(18, 4))
        table.grid(row=3, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="extended")
        for cid, heading, width, anchor, stretch in COLUMNS:
            self.tree.heading(cid, text=heading, command=lambda c=cid: self.sort_by(c))
            self.tree.column(cid, width=width, anchor=anchor, stretch=stretch, minwidth=60)
        self.tree.tag_configure("odd", background="#1a2023")
        self.tree.tag_configure("gap", foreground=AMBER)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<Double-1>", self._open_selected)
        self._enable_touch_scroll()

        # --- Footer: summary + export ----------------------------------
        footer = ttk.Frame(root, padding=(18, 10))
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.summary_var = tk.StringVar(value="No scan yet. Plug in a drive, pick a source, and press Start Scan.")
        ttk.Label(footer, textvariable=self.summary_var, style="Summary.TLabel",
                  wraplength=850, justify="left").grid(row=0, column=0, sticky="w")
        self.export_btn = ttk.Button(footer, text="⬇  Export as CSV", style="Amber.TButton",
                                     command=self.export_csv, state="disabled")
        self.export_btn.grid(row=0, column=1, sticky="e")

        status = ttk.Frame(root, padding=(18, 0, 18, 10))
        status.grid(row=5, column=0, sticky="ew")
        status.columnconfigure(1, weight=1)
        self.progress = ttk.Progressbar(status, mode="indeterminate", length=160)
        self.progress.grid(row=0, column=0, padx=(0, 10))
        self.progress.grid_remove()  # only shown while a scan runs
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=1, sticky="w")

    def _enable_touch_scroll(self):
        """Drag-to-scroll on the list, like a phone, for the tablet."""
        state = {"y": None, "moved": False}

        def press(event):
            state["y"], state["moved"] = event.y, False

        def drag(event):
            if state["y"] is None:
                return
            delta = state["y"] - event.y
            if abs(delta) >= 32:
                self.tree.yview_scroll(int(delta / 32), "units")
                state["y"], state["moved"] = event.y, True

        def release(_event):
            state["y"] = None

        self.tree.bind("<ButtonPress-1>", press, add="+")
        self.tree.bind("<B1-Motion>", drag, add="+")
        self.tree.bind("<ButtonRelease-1>", release, add="+")

    # ------------------------------------------------------------ Sources
    def refresh_drives(self):
        try:
            drives = list_drives()
        except Exception as exc:  # never let a flaky drive query kill the app
            drives = []
            self.status_var.set(f"Could not list drives: {exc}")
        self.drive_paths = [p for p, _ in drives]
        self.drive_combo["values"] = [label for _, label in drives]
        if drives:
            # Default to the last drive: on Windows that's usually the external one.
            self.drive_combo.current(len(drives) - 1)

    def choose_folder(self):
        start = self.folder_var.get() or (self._selected_drive() or os.path.expanduser("~"))
        path = filedialog.askdirectory(parent=self.root, initialdir=start,
                                       title="Choose a folder to inventory")
        if path:
            self.folder_var.set(os.path.normpath(path))
            self.mode_var.set("folder")

    def _selected_drive(self):
        idx = self.drive_combo.current()
        return self.drive_paths[idx] if 0 <= idx < len(self.drive_paths) else None

    def _mode_changed(self):
        if self.mode_var.get() == "folder" and not self.folder_var.get():
            self.choose_folder()

    # --------------------------------------------------------------- Scan
    def start_scan(self):
        if self.worker and self.worker.is_alive():
            return
        if self.mode_var.get() == "drive":
            root_path = self._selected_drive()
            if not root_path:
                messagebox.showwarning("Media Buddy", "Pick a drive first (try Refresh drives).")
                return
        else:
            root_path = self.folder_var.get().strip()
            if not root_path or not os.path.isdir(root_path):
                messagebox.showwarning("Media Buddy", "Choose a folder that exists.")
                return

        options = ScanOptions(
            include_video=self.opt_video.get(),
            include_images=self.opt_images.get(),
            include_audio=self.opt_audio.get(),
            group_sequences=self.opt_group.get(),
            include_hidden=self.opt_hidden.get(),
        )
        if not (options.include_video or options.include_images or options.include_audio):
            messagebox.showwarning("Media Buddy", "Tick at least one of Video, Images, or Audio.")
            return

        self.records.clear()
        self.visible.clear()
        self.pending.clear()
        self.tree.delete(*self.tree.get_children())
        self.type_combo["values"] = [ALL_TYPES]
        self.type_var.set(ALL_TYPES)
        self.sort_col = None
        self._update_headings()
        self.scan_root = root_path
        self.cancel_event = threading.Event()
        self.scan_started = time.monotonic()

        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])
        self.export_btn.state(["disabled"])
        self.progress.grid()
        self.progress.start(12)
        self.status_var.set(f"Scanning {root_path} …")

        def run():
            try:
                stats = scan(
                    root_path, options,
                    on_batch=lambda batch: self.queue.put(("batch", batch)),
                    on_folder=lambda path: self.queue.put(("folder", path)),
                    cancel_event=self.cancel_event,
                )
                self.queue.put(("done", stats))
            except Exception as exc:
                self.queue.put(("error", exc))

        self.worker = threading.Thread(target=run, daemon=True)
        self.worker.start()

    def stop_scan(self):
        self.cancel_event.set()
        self.status_var.set("Stopping…")

    def _poll_queue(self):
        last_folder = None
        got_batch = False
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "batch":
                    self.records.extend(payload)
                    self.pending.extend(payload)
                    got_batch = True
                elif kind == "folder":
                    last_folder = payload
                elif kind == "done":
                    last_folder = None
                    self._finish(payload)
                elif kind == "error":
                    last_folder = None
                    self._finish(None, payload)
        except queue.Empty:
            pass

        if last_folder and not self.cancel_event.is_set():
            self.status_var.set(f"Scanning: {last_folder}")
        if got_batch:
            self._refresh_type_choices()
        if self.pending:
            chunk, self.pending = self.pending[:ROWS_PER_TICK], self.pending[ROWS_PER_TICK:]
            self._insert_rows([r for r in chunk if self._passes(r)])
            self._update_summary()
        self.root.after(100, self._poll_queue)

    def _finish(self, stats, error=None):
        self.progress.stop()
        self.progress.grid_remove()
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])
        elapsed = time.monotonic() - self.scan_started
        self._refresh_type_choices()
        if error:
            self.status_var.set(f"Scan failed: {error}")
            messagebox.showerror("Media Buddy", f"The scan stopped with an error:\n{error}")
        else:
            verb = "Stopped" if self.cancel_event.is_set() else "Finished"
            msg = (f"{verb} in {elapsed:.1f}s  ·  {stats.folders:,} folders  ·  "
                   f"{stats.files_seen:,} files checked")
            if stats.errors:
                msg += f"  ·  {len(stats.errors)} unreadable (permissions)"
            self.status_var.set(msg)
        if self.records:
            self.export_btn.state(["!disabled"])
        self._update_summary()

    # --------------------------------------------------- List / filtering
    def _passes(self, rec):
        wanted = self.type_var.get()
        if wanted != ALL_TYPES and rec.category != wanted:
            return False
        needle = self.search_var.get().strip().lower()
        return not needle or needle in rec.name.lower() or needle in rec.folder.lower()

    def _row_values(self, r):
        frames = f"{r.frames:,}" if r.frames > 1 else ""
        if r.missing_frames:
            frames += f"  ({r.missing_frames} missing)"
        return (r.name, r.category, r.ext.upper(), human_size(r.size),
                _fmt_dt(r.created), _fmt_dt(r.modified), frames, r.folder)

    def _insert_rows(self, rows):
        for r in rows:
            idx = len(self.visible)
            self.visible.append(r)
            tags = ["odd"] if idx % 2 else []
            if r.missing_frames:
                tags.append("gap")
            self.tree.insert("", "end", iid=str(idx), values=self._row_values(r), tags=tags)

    def _schedule_refilter(self):
        if getattr(self, "_refilter_job", None):
            self.root.after_cancel(self._refilter_job)
        self._refilter_job = self.root.after(250, self.refilter)

    def refilter(self):
        self._refilter_job = None
        self.tree.delete(*self.tree.get_children())
        self.visible = []
        # Rebuild from every record found so far; rows still queued for live
        # insertion are included here, so drop the queue to avoid duplicates.
        self.pending = []
        shown = [r for r in self.records if self._passes(r)]
        if self.sort_col:
            shown.sort(key=SORT_KEYS[self.sort_col], reverse=self.sort_reverse)
        self._insert_rows(shown)
        self._update_summary()

    def sort_by(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col, self.sort_reverse = col, col in ("size", "created", "modified", "frames")
        self._update_headings()
        self.refilter()

    def _update_headings(self):
        for cid, heading, *_ in COLUMNS:
            arrow = ""
            if cid == self.sort_col:
                arrow = "  ▼" if self.sort_reverse else "  ▲"
            self.tree.heading(cid, text=heading + arrow)

    def _refresh_type_choices(self):
        cats = sorted({r.category for r in self.records})
        self.type_combo["values"] = [ALL_TYPES] + cats

    def _update_summary(self):
        if not self.records:
            if not (self.worker and self.worker.is_alive()):
                self.summary_var.set("No matching media found.")
            return
        counts = {}
        for r in self.visible:
            n, size = counts.get(r.category, (0, 0))
            counts[r.category] = (n + 1, size + r.size)
        total = sum(r.size for r in self.visible)
        parts = [f"{n:,} {cat}" for cat, (n, _) in sorted(counts.items())]
        shown = f"{len(self.visible):,} items  ·  {human_size(total)}"
        if len(self.visible) != len(self.records):
            shown += f"   (filtered from {len(self.records):,})"
        self.summary_var.set(shown + ("\n" + "   ·   ".join(parts) if parts else ""))

    def _open_selected(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        rec = self.visible[int(item)]
        target = rec.path if os.path.exists(rec.path) else rec.folder
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", target])
            else:
                subprocess.Popen(["xdg-open", rec.folder])
        except OSError as exc:
            self.status_var.set(f"Could not open folder: {exc}")

    # ------------------------------------------------------------- Export
    def export_csv(self):
        if not self.visible:
            messagebox.showinfo("Media Buddy", "Nothing to export. The list is empty.")
            return
        job = self.job_var.get().strip()
        source = os.path.basename(os.path.normpath(self.scan_root)) or \
            self.scan_root.replace(":", "").strip("\\/") or "drive"
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        default = "_".join(p for p in ("MediaBuddy", job, source, stamp) if p)
        default = "".join(c if c.isalnum() or c in "-_." else "_" for c in default) + ".csv"
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save inventory as CSV", defaultextension=".csv",
            initialfile=default, initialdir=os.path.expanduser("~"),
            filetypes=[("CSV spreadsheet", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            n = write_csv(path, self.visible, job)
        except OSError as exc:
            messagebox.showerror("Media Buddy", f"Could not save the file:\n{exc}")
            return
        self.status_var.set(f"Exported {n:,} rows to {path}")
        if messagebox.askyesno("Media Buddy", f"Saved {n:,} rows.\n\n{path}\n\nOpen it now?"):
            try:
                if sys.platform == "win32":
                    os.startfile(path)  # opens in Excel / default spreadsheet app
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            except OSError:
                pass


def main():
    if sys.platform == "win32":
        # Crisp text on high-DPI tablet screens instead of blurry bitmap scaling.
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    MediaBuddyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
