import json
import socket
import keyring
from pathlib import Path

SMART_LMS_DIR = Path.home() / ".smart-lms"
SESSIONS_DIR = SMART_LMS_DIR / "sessions"
CONFIG_FILE = SMART_LMS_DIR / "config.json"
KEYCHAIN_SERVICE = "smart-lms-moodle"
DEFAULT_LMS_URL = "https://isikuniversity.mrooms.net"
DEFAULT_PORT = 8742

_DEFAULTS = {
    "lms_base_url": DEFAULT_LMS_URL,
    "lms_username": "",
    "port": DEFAULT_PORT,
    "google_drive_connected": False,
    "notebooklm_connected": False,
}


def ensure_dirs():
    try:
        SMART_LMS_DIR.mkdir(exist_ok=True)
        SESSIONS_DIR.mkdir(exist_ok=True)
    except OSError as e:
        raise OSError(f"Cannot create Smart LMS data directory: {e}") from e
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(_DEFAULTS, indent=2))


def get_config() -> dict:
    ensure_dirs()
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        data = {}
    return {**_DEFAULTS, **data}


def save_config(data: dict):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_lms_credentials() -> tuple[str | None, str | None]:
    cfg = get_config()
    username = cfg.get("lms_username", "")
    if not username:
        return None, None
    password = keyring.get_password(KEYCHAIN_SERVICE, username)
    return username, password


def store_lms_credentials(username: str, password: str):
    try:
        keyring.set_password(KEYCHAIN_SERVICE, username, password)
    except Exception as e:
        raise RuntimeError(
            f"Failed to store credentials in system keychain: {e}"
        ) from e
    cfg = get_config()
    cfg["lms_username"] = username
    save_config(cfg)


def find_free_port(preferred: int = DEFAULT_PORT) -> int:
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", preferred))
            return preferred
    except OSError:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
