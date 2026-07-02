"""Explicit file-list source: the user picks individual PDFs or drags them in.

Unlike ``FolderSource`` (point at a directory) this takes an exact list of
files. It backs both the "Add…" file-picker button and drag-and-drop in the
GUI — the widget collects paths, this source just converts the ones it's given.
The files stay where they are; nothing is downloaded or moved.
"""

import os

from sources.base import Source, FetchedFile, INPUT_FILES


class FilesSource(Source):
    name          = "Files (pick / drag & drop)"
    key           = "files"
    input_mode    = INPUT_FILES
    input_label   = "Selected PDFs:"
    convert_label = "  Convert  "

    def __init__(self, files: list[str]):
        self.files = files

    def fetch(self, dest_dir: str, log_fn=lambda _msg: None) -> list[FetchedFile]:
        # Files are already local; ``dest_dir`` is unused. Skip any that
        # vanished between selection and conversion instead of aborting.
        out: list[FetchedFile] = []
        for p in self.files:
            if not os.path.isfile(p):
                log_fn(f"  Skipped (not found): {p}")
                continue
            out.append(FetchedFile(path=p, name=os.path.basename(p)))
        log_fn(f"{len(out)} file(s) selected for conversion.")
        return out

    @classmethod
    def build(cls, gui_input) -> "FilesSource":
        pdfs = [f for f in (gui_input or []) if f.lower().endswith(".pdf")]
        if not pdfs:
            raise ValueError("No PDF files selected.\nAdd at least one .pdf file.")
        return cls(pdfs)
