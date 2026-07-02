"""
File-ingestion sources.

Each source knows how to obtain invoice PDFs from somewhere (local folder,
Google Drive, an explicit file selection, …) and hand back local file paths.
The conversion pipeline (``parse_pdf`` → ``save_ledes``) is unchanged; only
"where the PDFs come from" lives here.

``REGISTRY`` is the single list the GUI reads to build its source controls.
To add a source: create a ``Source`` subclass, then append it here.
"""

from sources.base import Source, FetchedFile, INPUT_PATH, INPUT_FILES
from sources.folder import FolderSource
from sources.gdrive import GoogleDriveSource
from sources.files import FilesSource

# Order here = order of the radio buttons in the GUI.
REGISTRY = [FolderSource, GoogleDriveSource, FilesSource]


def get_source_class(key: str):
    """Look up a source class by its ``key`` (the radio-button value)."""
    for cls in REGISTRY:
        if cls.key == key:
            return cls
    raise KeyError(f"Unknown source: {key!r}")


__all__ = [
    "Source", "FetchedFile", "INPUT_PATH", "INPUT_FILES",
    "REGISTRY", "get_source_class",
]
