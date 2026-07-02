"""Source abstraction: produce local PDF paths for the conversion pipeline."""

from dataclasses import dataclass

# Input modes — tell the GUI how to collect this source's input:
INPUT_PATH  = "path"    # a single directory string (Entry + Browse button)
INPUT_FILES = "files"   # an explicit list of file paths (list + Add/drag&drop)


@dataclass
class FetchedFile:
    """A single PDF made available locally, plus where it came from."""
    path:        str           # local filesystem path to the downloaded PDF
    name:        str           # original file name (for logs / output naming)
    source_id:   str = ""      # opaque id in the origin (e.g. Drive file id)


class Source:
    """Interface every ingestion source implements.

    A source is responsible for putting PDFs on the local filesystem and
    returning their paths. It must not raise for an empty result — it returns
    an empty list. Per-file download errors should be reported via ``log_fn``
    and skipped, not aborted.

    Sources are *self-describing*: the class attributes below let the GUI build
    its controls (radio button label, input widget, convert-button text) purely
    from the registry, without hardcoding any single source. Add a new source =
    new subclass + one line in ``sources.REGISTRY``.
    """

    name          = "source"          # human-readable, shown in the radio button
    key           = "source"          # stable id used as the radio value
    input_mode    = INPUT_PATH        # INPUT_PATH or INPUT_FILES
    input_label   = "Input (PDF):"    # label for the path field (path mode)
    convert_label = "  Convert  "     # text on the action button in this mode

    def fetch(self, dest_dir: str, log_fn=lambda _msg: None) -> list[FetchedFile]:
        """Download/collect new PDFs into ``dest_dir`` and return them."""
        raise NotImplementedError

    @classmethod
    def build(cls, gui_input) -> "Source":
        """Construct a source from the GUI input value.

        ``gui_input`` is a directory string for ``INPUT_PATH`` sources, or a
        list of file paths for ``INPUT_FILES`` sources. Raise ``ValueError``
        with a user-facing message if the input is not usable.
        """
        raise NotImplementedError
