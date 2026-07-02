"""Shared Google OAuth handling for Drive (and later Gmail).

First run opens a browser for consent; the resulting token is cached in
``token.json`` so subsequent runs are silent until it expires/revokes.
"""

import os

from config import (
    GDRIVE_CLIENT_ID,
    GDRIVE_CLIENT_SECRET,
    GDRIVE_CREDENTIALS_FILE,
    GDRIVE_TOKEN_FILE,
    GDRIVE_SCOPES,
)

# Standard, non-secret OAuth endpoints for an "installed" (desktop) app.
# Only client_id/client_secret vary between projects.
_INSTALLED_APP_DEFAULTS = {
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"],
}


class GoogleAuthError(RuntimeError):
    """Raised when credentials are missing or the OAuth flow cannot complete."""


def get_credentials(scopes: list[str] | None = None,
                    credentials_file: str = GDRIVE_CREDENTIALS_FILE,
                    token_file: str = GDRIVE_TOKEN_FILE):
    """Return valid Google OAuth credentials, running the consent flow if needed.

    Imports the Google libraries lazily so the rest of the app still runs when
    they aren't installed (the folder source has no such dependency).
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise GoogleAuthError(
            "Google libraries are not installed. Run:\n"
            "  pip install -r requirements.txt"
        ) from exc

    scopes = scopes or GDRIVE_SCOPES
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    # ``valid`` only checks expiry, not which scopes were granted. Require the
    # token to already cover every requested scope too — so widening scopes
    # (e.g. adding Gmail later) re-triggers consent instead of failing with a
    # 403 at API call time.
    if creds and creds.valid and creds.has_scopes(scopes):
        return creds

    # A refresh keeps the token's existing scopes, so it only helps when the
    # token is merely expired and already covers what we need; otherwise we run
    # the full consent flow.
    if creds and creds.expired and creds.refresh_token and creds.has_scopes(scopes):
        creds.refresh(Request())
    else:
        flow = _build_flow(InstalledAppFlow, scopes, credentials_file)
        creds = flow.run_local_server(port=0)

    with open(token_file, "w", encoding="utf-8") as fh:
        fh.write(creds.to_json())

    return creds


def _build_flow(InstalledAppFlow, scopes, credentials_file):
    """Prefer client_id/secret from .env; otherwise use the credentials file."""
    if GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET:
        client_config = {
            "installed": {
                "client_id": GDRIVE_CLIENT_ID,
                "client_secret": GDRIVE_CLIENT_SECRET,
                **_INSTALLED_APP_DEFAULTS,
            }
        }
        return InstalledAppFlow.from_client_config(client_config, scopes)

    if not os.path.exists(credentials_file):
        raise GoogleAuthError(
            "No OAuth client configured. Either set GDRIVE_CLIENT_ID and "
            "GDRIVE_CLIENT_SECRET in .env, or save the Desktop-app "
            f"credentials.json at:\n  {credentials_file}"
        )
    return InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
