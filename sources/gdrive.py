"""Google Drive ingestion source.

Lists PDF files in a configured Drive folder and downloads them. After a file
is converted successfully it is MOVED into a "Done" subfolder, so it is no
longer listed and "Fetch new" never reprocesses it. Requires write scope.
"""

import io
import os

from config import (
    GDRIVE_FOLDER_ID,
    GDRIVE_DONE_FOLDER_NAME,
    GDRIVE_SCOPES,
)
from sources.base import Source, FetchedFile, INPUT_PATH
from sources.google_auth import get_credentials, GoogleAuthError

PDF_MIME    = "application/pdf"
FOLDER_MIME = "application/vnd.google-apps.folder"


class GoogleDriveSource(Source):
    name          = "Google Drive"
    key           = "gdrive"
    input_mode    = INPUT_PATH
    input_label   = "Download to:"
    convert_label = "  Fetch & Convert  "

    def __init__(self, folder_id: str = GDRIVE_FOLDER_ID,
                 done_folder_name: str = GDRIVE_DONE_FOLDER_NAME):
        self.folder_id        = folder_id
        self.done_folder_name = done_folder_name
        self._service         = None
        self._done_folder_id  = None

    @classmethod
    def build(cls, gui_input) -> "GoogleDriveSource":
        # ``gui_input`` is the local staging folder downloads are written to.
        path = (gui_input or "").strip()
        if not path:
            raise ValueError("Please choose a download folder.")
        os.makedirs(path, exist_ok=True)
        return cls()

    # ── Drive plumbing ─────────────────────────────────────────────────────────

    def _build_service(self):
        if self._service is not None:
            return self._service
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GoogleAuthError(
                "Google libraries are not installed. Run:\n"
                "  pip install -r requirements.txt"
            ) from exc
        creds = get_credentials(GDRIVE_SCOPES)
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def _list_pdfs(self, service) -> list[dict]:
        """Return [{id, name}, …] for every PDF directly in the folder (paged)."""
        query = f"'{self.folder_id}' in parents and mimeType='{PDF_MIME}' and trashed=false"
        files, page_token = [], None
        while True:
            resp = service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                pageSize=100,
            ).execute()
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return files

    def _ensure_done_folder(self, service) -> str:
        """Find the 'Done' subfolder under the source folder, creating it once."""
        if self._done_folder_id is not None:
            return self._done_folder_id

        safe_name = self.done_folder_name.replace("'", "\\'")
        query = (
            f"'{self.folder_id}' in parents and name='{safe_name}' "
            f"and mimeType='{FOLDER_MIME}' and trashed=false"
        )
        resp = service.files().list(
            q=query, spaces="drive", fields="files(id)", pageSize=1,
        ).execute()
        found = resp.get("files", [])
        if found:
            self._done_folder_id = found[0]["id"]
        else:
            meta = {
                "name": self.done_folder_name,
                "mimeType": FOLDER_MIME,
                "parents": [self.folder_id],
            }
            created = service.files().create(body=meta, fields="id").execute()
            self._done_folder_id = created["id"]
        return self._done_folder_id

    def _download(self, service, file_id: str, dest_path: str) -> None:
        from googleapiclient.http import MediaIoBaseDownload
        request = service.files().get_media(fileId=file_id)
        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _status, done = downloader.next_chunk()

    def _move_to_done(self, service, file_id: str, done_id: str) -> None:
        service.files().update(
            fileId=file_id,
            addParents=done_id,
            removeParents=self.folder_id,
            fields="id, parents",
        ).execute()

    # ── Source interface ───────────────────────────────────────────────────────

    def fetch(self, dest_dir: str, log_fn=lambda _msg: None) -> list[FetchedFile]:
        if not self.folder_id:
            raise GoogleAuthError(
                "GDRIVE_FOLDER_ID is not set in config.py.\n"
                "Copy it from the Drive folder URL:\n"
                "  https://drive.google.com/drive/folders/<FOLDER_ID>"
            )

        service = self._build_service()
        pdfs    = self._list_pdfs(service)
        log_fn(f"Drive folder: {len(pdfs)} new PDF(s) to fetch.")

        os.makedirs(dest_dir, exist_ok=True)
        fetched: list[FetchedFile] = []

        for f in pdfs:
            file_id, name = f["id"], f["name"]
            local_name = self._unique_name(dest_dir, name)
            local_path = os.path.join(dest_dir, local_name)
            try:
                self._download(service, file_id, local_path)
                fetched.append(FetchedFile(path=local_path, name=name, source_id=file_id))
                log_fn(f"  Downloaded: {name}")
            except Exception as exc:  # one bad file shouldn't stop the batch
                log_fn(f"  ERROR downloading {name}: {exc}")
                if os.path.exists(local_path):
                    os.remove(local_path)

        return fetched

    def mark_processed(self, files: list[FetchedFile]) -> None:
        """Move successfully converted files into the 'Done' subfolder."""
        if not files:
            return
        service = self._build_service()
        done_id = self._ensure_done_folder(service)
        failures = []
        for f in files:
            if not f.source_id:
                continue
            try:
                self._move_to_done(service, f.source_id, done_id)
            except Exception as exc:
                # Non-fatal: the file stays in the folder and is retried next run.
                failures.append(f"{f.name} ({exc})")
        if failures:
            raise RuntimeError(
                f"could not move {len(failures)} file(s) to "
                f"'{self.done_folder_name}': " + "; ".join(failures))

    @staticmethod
    def _unique_name(dest_dir: str, name: str) -> str:
        """Avoid clobbering when two Drive files share a name."""
        if not os.path.exists(os.path.join(dest_dir, name)):
            return name
        stem, ext = os.path.splitext(name)
        i = 1
        while os.path.exists(os.path.join(dest_dir, f"{stem} ({i}){ext}")):
            i += 1
        return f"{stem} ({i}){ext}"
