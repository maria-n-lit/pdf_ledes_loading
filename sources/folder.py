"""Local-folder ingestion source: the original behaviour, as a Source."""

import os

from sources.base import Source, FetchedFile


class FolderSource(Source):
    name = "Local folder"

    def __init__(self, folder: str):
        self.folder = folder

    def fetch(self, dest_dir: str, log_fn=lambda _msg: None) -> list[FetchedFile]:
        if not os.path.isdir(self.folder):
            raise FileNotFoundError(f"Input folder not found:\n{self.folder}")
        pdfs = sorted(
            f for f in os.listdir(self.folder)
            if f.lower().endswith(".pdf")
        )
        log_fn(f"Found {len(pdfs)} PDF file(s) in folder.")
        return [
            FetchedFile(path=os.path.join(self.folder, f), name=f)
            for f in pdfs
        ]
