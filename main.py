"""
PDF → LEDES 98B Converter
GUI application built with tkinter.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
from pdf_parser import parse_pdf
from ledes_converter import save_ledes
from sources import REGISTRY, get_source_class, INPUT_FILES

# Drag-and-drop is optional: if tkinterdnd2 is installed the window accepts
# dropped files; otherwise the app runs unchanged and users use "Add…".
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_AVAILABLE = True
    _BaseTk = TkinterDnD.Tk
except ImportError:
    _DND_AVAILABLE = False
    _BaseTk = tk.Tk


# ── Worker ────────────────────────────────────────────────────────────────────

def run_conversion(source, staging_dir: str, output_dir: str, log_fn, done_fn):
    """Run in a background thread; calls log_fn for each status line.

    ``source`` is a Source (folder, Google Drive, …). It yields local PDF paths
    which are then converted. Sources that support de-duplication
    (``mark_processed``) are told which files converted successfully.
    """
    try:
        files = source.fetch(staging_dir, log_fn)
    except Exception as exc:
        log_fn(f"Could not fetch files: {exc}")
        done_fn(0, 0, fetch_error=str(exc))
        return

    if not files:
        log_fn("No new PDF files to convert.")
        done_fn(0, 0)
        return

    log_fn(f"Starting conversion of {len(files)} file(s)...\n")
    ok = 0
    errors = 0
    succeeded = []

    for f in files:
        log_fn(f"  Processing: {f.name}")
        try:
            invoice = parse_pdf(f.path)
            out_path = save_ledes(invoice, output_dir)
            log_fn(f"    OK → {os.path.basename(out_path)}"
                   f"  (items: {len(invoice.line_items)}, total: {invoice.total:.2f})")
            ok += 1
            succeeded.append(f)
        except Exception as exc:
            log_fn(f"    ERROR: {exc}")
            errors += 1

    mark = getattr(source, "mark_processed", None)
    if mark is not None and succeeded:
        try:
            mark(succeeded)
        except Exception as exc:
            log_fn(f"  (warning: could not record processed files: {exc})")

    done_fn(ok, errors)


# ── GUI ───────────────────────────────────────────────────────────────────────

class App(_BaseTk):
    def __init__(self):
        super().__init__()
        self.title("PDF → LEDES 98B Converter")
        self.resizable(True, True)
        self.minsize(680, 500)
        self._build_ui()
        self._on_source_change()      # sync controls to the default source
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ── Source selector (built from the registry) ──────────────────────────
        frame_src = ttk.LabelFrame(self, text="Source", padding=8)
        frame_src.pack(fill="x", **pad)

        self.var_source = tk.StringVar(value=REGISTRY[0].key)
        for i, cls in enumerate(REGISTRY):
            ttk.Radiobutton(
                frame_src, text=cls.name, value=cls.key,
                variable=self.var_source, command=self._on_source_change,
            ).pack(side="left", padx=(0 if i == 0 else 12, 0))

        # ── Input / Output ─────────────────────────────────────────────────────
        frame_io = ttk.LabelFrame(self, text="Input / Output", padding=8)
        frame_io.pack(fill="x", **pad)
        frame_io.columnconfigure(0, weight=1)

        # Path input (Entry + Browse) — for folder / Google Drive.
        self.path_frame = ttk.Frame(frame_io)
        self.path_frame.grid(row=0, column=0, sticky="ew")
        self.path_frame.columnconfigure(1, weight=1)
        self.lbl_input = ttk.Label(self.path_frame, text="Input (PDF):")
        self.lbl_input.grid(row=0, column=0, sticky="w")
        self.var_input = tk.StringVar(value=DEFAULT_INPUT_DIR)
        ttk.Entry(self.path_frame, textvariable=self.var_input).grid(
            row=0, column=1, sticky="ew", padx=(6, 4))
        self.btn_browse_input = ttk.Button(self.path_frame, text="Browse…",
                                           command=self._browse_input)
        self.btn_browse_input.grid(row=0, column=2)

        # File-list input (Listbox + buttons) — for the "Files" source.
        self.files_frame = ttk.Frame(frame_io)
        self.files_frame.grid(row=0, column=0, sticky="ew")
        self.files_frame.columnconfigure(0, weight=1)
        self.lbl_files = ttk.Label(self.files_frame, text="Selected PDFs:")
        self.lbl_files.grid(row=0, column=0, columnspan=2, sticky="w")
        self.files_list = tk.Listbox(self.files_frame, height=4, selectmode="extended")
        self.files_list.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        files_btns = ttk.Frame(self.files_frame)
        files_btns.grid(row=1, column=1, sticky="n", padx=(6, 0))
        ttk.Button(files_btns, text="Add…", width=8,
                   command=self._add_files).pack(fill="x")
        ttk.Button(files_btns, text="Remove", width=8,
                   command=self._remove_files).pack(fill="x", pady=(4, 0))
        ttk.Button(files_btns, text="Clear", width=8,
                   command=self._clear_files).pack(fill="x")

        if _DND_AVAILABLE:
            self.files_list.drop_target_register(DND_FILES)
            self.files_list.dnd_bind("<<Drop>>", self._on_drop)

        # Output row (always visible).
        out_frame = ttk.Frame(frame_io)
        out_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        out_frame.columnconfigure(1, weight=1)
        ttk.Label(out_frame, text="Output (LEDES):").grid(row=0, column=0, sticky="w")
        self.var_output = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        ttk.Entry(out_frame, textvariable=self.var_output).grid(
            row=0, column=1, sticky="ew", padx=(6, 4))
        ttk.Button(out_frame, text="Browse…",
                   command=self._browse_output).grid(row=0, column=2)

        # ── Progress bar ──────────────────────────────────────────────────────
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(0, 4))

        # ── Log area ──────────────────────────────────────────────────────────
        frame_log = ttk.LabelFrame(self, text="Log", padding=4)
        frame_log.pack(fill="both", expand=True, **pad)

        self.log_box = scrolledtext.ScrolledText(
            frame_log, state="disabled", font=("Consolas", 9),
            wrap="word", background="#1e1e1e", foreground="#d4d4d4",
            insertbackground="white",
        )
        self.log_box.pack(fill="both", expand=True)

        # ── Buttons (placed BEFORE the log so they are always visible) ─────
        frame_btn = ttk.Frame(self)
        frame_btn.pack(fill="x", padx=10, pady=(6, 10), side="bottom")

        self.btn_convert = ttk.Button(frame_btn, text="  Convert  ",
                                      command=self._start_conversion)
        self.btn_convert.pack(side="left")

        ttk.Button(frame_btn, text="Clear Log",
                   command=self._clear_log).pack(side="left", padx=(6, 0))

        ttk.Button(frame_btn, text="Open Output Folder",
                   command=self._open_output).pack(side="right")

    def _center(self):
        self.update_idletasks()
        w, h = 780, 560
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Folder dialogs ────────────────────────────────────────────────────────

    def _browse_input(self):
        d = filedialog.askdirectory(
            title="Select input folder with PDF files",
            initialdir=self.var_input.get(),
        )
        if d:
            self.var_input.set(d)

    def _browse_output(self):
        d = filedialog.askdirectory(
            title="Select output folder for LEDES files",
            initialdir=self.var_output.get(),
        )
        if d:
            self.var_output.set(d)

    # ── File-list handlers (Files source) ───────────────────────────────────────

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF invoices",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        self._add_paths(paths)

    def _add_paths(self, paths):
        """Add PDF paths to the list, ignoring non-PDFs and duplicates."""
        existing = set(self.files_list.get(0, "end"))
        for p in paths:
            if p.lower().endswith(".pdf") and p not in existing:
                self.files_list.insert("end", p)
                existing.add(p)

    def _remove_files(self):
        for i in reversed(self.files_list.curselection()):
            self.files_list.delete(i)

    def _clear_files(self):
        self.files_list.delete(0, "end")

    def _on_drop(self, event):
        # tkinterdnd2 passes a Tcl list; splitlist handles brace-quoted paths.
        self._add_paths(self.tk.splitlist(event.data))

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ── Conversion ────────────────────────────────────────────────────────────

    def _on_source_change(self):
        """Swap the input widget and relabel controls for the chosen source."""
        cls = get_source_class(self.var_source.get())
        self.btn_convert.configure(text=cls.convert_label)

        if cls.input_mode == INPUT_FILES:
            self.path_frame.grid_remove()
            self.files_frame.grid()
            self.lbl_files.configure(
                text="Selected PDFs (drag & drop here or Add…):"
                if _DND_AVAILABLE else "Selected PDFs (Add… to choose files):")
        else:
            self.files_frame.grid_remove()
            self.path_frame.grid()
            self.lbl_input.configure(text=cls.input_label)

    def _start_conversion(self):
        output_dir = self.var_output.get().strip()
        cls = get_source_class(self.var_source.get())

        if cls.input_mode == INPUT_FILES:
            gui_input   = list(self.files_list.get(0, "end"))
            staging_dir = output_dir            # unused by file-list sources
            desc        = f"{len(gui_input)} file(s) selected"
        else:
            gui_input   = self.var_input.get().strip()
            staging_dir = gui_input
            desc        = f"{cls.input_label} {gui_input}"

        try:
            source = cls.build(gui_input)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        # Create output dir if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        self.btn_convert.configure(state="disabled")
        self.progress.start(12)
        self._log(f"Source: {source.name}")
        self._log(desc)
        self._log(f"Output: {output_dir}")
        self._log("-" * 60)

        thread = threading.Thread(
            target=run_conversion,
            args=(source, staging_dir, output_dir,
                  self._log_from_thread, self._on_done),
            daemon=True,
        )
        thread.start()

    def _log_from_thread(self, text: str):
        # Thread-safe log call
        self.after(0, self._log, text)

    def _on_done(self, ok: int, errors: int, fetch_error: str | None = None):
        def _finish():
            self.progress.stop()
            self.btn_convert.configure(state="normal")
            self._log("-" * 60)

            if fetch_error:
                self._log(f"Could not fetch files: {fetch_error}")
                messagebox.showerror(
                    "Fetch failed",
                    f"Could not fetch files from the source:\n\n{fetch_error}")
                return

            self._log("Conversion complete.")
            self._log(f"  Successfully converted : {ok}")
            self._log(f"  Failed                 : {errors}")
            if ok:
                self._log(f"  Output folder          : {self.var_output.get()}")

            total = ok + errors
            summary = (
                f"Conversion complete.\n\n"
                f"Total files processed : {total}\n"
                f"Successfully converted: {ok}\n"
                f"Failed                : {errors}"
            )
            if errors and ok:
                messagebox.showwarning("Done with errors", summary)
            elif errors and not ok:
                messagebox.showerror("Conversion failed", summary)
            else:
                messagebox.showinfo("Done", summary)
        self.after(0, _finish)

    def _open_output(self):
        output_dir = self.var_output.get().strip()
        if not os.path.isdir(output_dir):
            messagebox.showinfo("Info", "Output folder does not exist yet.")
            return
        if sys.platform == "win32":
            os.startfile(output_dir)
        elif sys.platform == "darwin":
            os.system(f'open "{output_dir}"')
        else:
            os.system(f'xdg-open "{output_dir}"')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
