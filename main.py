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


# ── Worker ────────────────────────────────────────────────────────────────────

def run_conversion(input_dir: str, output_dir: str, log_fn, done_fn):
    """Run in a background thread; calls log_fn for each status line."""
    pdf_files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        log_fn("No PDF files found in the input folder.")
        done_fn(0, 0)
        return

    log_fn(f"Found {len(pdf_files)} PDF file(s). Starting conversion...\n")
    ok = 0
    errors = 0

    for filename in pdf_files:
        filepath = os.path.join(input_dir, filename)
        log_fn(f"  Processing: {filename}")
        try:
            invoice = parse_pdf(filepath)
            out_path = save_ledes(invoice, output_dir)
            log_fn(f"    OK → {os.path.basename(out_path)}"
                   f"  (items: {len(invoice.line_items)}, total: {invoice.total:.2f})")
            ok += 1
        except Exception as exc:
            log_fn(f"    ERROR: {exc}")
            errors += 1

    done_fn(ok, errors)


# ── GUI ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF → LEDES 98B Converter")
        self.resizable(True, True)
        self.minsize(680, 460)
        self._build_ui()
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ── Folder selectors ──────────────────────────────────────────────────
        frame_dirs = ttk.LabelFrame(self, text="Folders", padding=8)
        frame_dirs.pack(fill="x", **pad)
        frame_dirs.columnconfigure(1, weight=1)

        ttk.Label(frame_dirs, text="Input (PDF):").grid(row=0, column=0, sticky="w")
        self.var_input = tk.StringVar(value=DEFAULT_INPUT_DIR)
        ttk.Entry(frame_dirs, textvariable=self.var_input).grid(
            row=0, column=1, sticky="ew", padx=(6, 4))
        ttk.Button(frame_dirs, text="Browse…",
                   command=self._browse_input).grid(row=0, column=2)

        ttk.Label(frame_dirs, text="Output (LEDES):").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.var_output = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        ttk.Entry(frame_dirs, textvariable=self.var_output).grid(
            row=1, column=1, sticky="ew", padx=(6, 4), pady=(4, 0))
        ttk.Button(frame_dirs, text="Browse…",
                   command=self._browse_output).grid(row=1, column=2, pady=(4, 0))

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
        w, h = 780, 520
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

    def _start_conversion(self):
        input_dir = self.var_input.get().strip()
        output_dir = self.var_output.get().strip()

        if not input_dir or not os.path.isdir(input_dir):
            messagebox.showerror("Error", f"Input folder not found:\n{input_dir}")
            return

        # Create output dir if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        self.btn_convert.configure(state="disabled")
        self.progress.start(12)
        self._log(f"Input:  {input_dir}")
        self._log(f"Output: {output_dir}")
        self._log("-" * 60)

        thread = threading.Thread(
            target=run_conversion,
            args=(input_dir, output_dir, self._log_from_thread, self._on_done),
            daemon=True,
        )
        thread.start()

    def _log_from_thread(self, text: str):
        # Thread-safe log call
        self.after(0, self._log, text)

    def _on_done(self, ok: int, errors: int):
        def _finish():
            self.progress.stop()
            self.btn_convert.configure(state="normal")
            self._log("-" * 60)
            self._log(f"Conversion complete.")
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
