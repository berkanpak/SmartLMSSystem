import os
import tempfile
from pathlib import Path
from fastmcp import FastMCP
from smart_lms.config import SMART_LMS_DIR, get_config, save_config

TOKEN_FILE = SMART_LMS_DIR / "google_token.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]
CLIENT_SECRETS_FILE = SMART_LMS_DIR / "google_client.json"


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"Google OAuth client secrets not found at {CLIENT_SECRETS_FILE}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def _build_drive_service():
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=_get_credentials())


def register_drive_tools(mcp: FastMCP):

    @mcp.tool()
    def connect_google_drive() -> str:
        """Initiate Google Drive OAuth. Opens browser for auth. Returns status message."""
        try:
            _get_credentials()
            cfg = get_config()
            cfg["google_drive_connected"] = True
            save_config(cfg)
            return "Google Drive connected successfully."
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def search_drive_files(query: str) -> list[dict]:
        """Search Google Drive files. Returns [{id, name, mimeType}]."""
        try:
            svc = _build_drive_service()
            results = svc.files().list(
                q=query,
                pageSize=20,
                fields="files(id,name,mimeType)"
            ).execute()
            return results.get("files", [])
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def get_drive_file_text(file_id: str) -> str:
        """Export a Drive file as plain text. Works for Docs and Slides."""
        try:
            svc = _build_drive_service()
            try:
                data = svc.files().export(
                    fileId=file_id,
                    mimeType="text/plain"
                ).execute()
                return data.decode("utf-8") if isinstance(data, bytes) else data
            except Exception:
                from smart_lms.tools.documents import extract_document_text
                req = svc.files().get_media(fileId=file_id)
                meta = svc.files().get(fileId=file_id, fields="name").execute()
                name = meta.get("name", "file")
                with tempfile.NamedTemporaryFile(
                        suffix=os.path.splitext(name)[1], delete=False) as f:
                    f.write(req.execute())
                    fpath = f.name
                text = extract_document_text(fpath)
                os.unlink(fpath)
                return text
        except Exception as e:
            return f"Error extracting file: {e}"
