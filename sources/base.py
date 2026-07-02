"""Source abstraction: produce local PDF paths for the conversion pipeline."""

from dataclasses import dataclass


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
    """

    name = "source"

    def fetch(self, dest_dir: str, log_fn=lambda _msg: None) -> list[FetchedFile]:
        """Download/collect new PDFs into ``dest_dir`` and return them."""
        raise NotImplementedError
