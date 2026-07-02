"""
File-ingestion sources.

Each source knows how to obtain invoice PDFs from somewhere (local folder,
Google Drive, …) and hand back local file paths. The conversion pipeline
(``parse_pdf`` → ``save_ledes``) is unchanged; only "where the PDFs come from"
lives here.
"""

from sources.base import Source, FetchedFile

__all__ = ["Source", "FetchedFile"]
