import json
import re
import uuid
from datetime import datetime, timezone
from fastmcp import FastMCP
from smart_lms.config import SESSIONS_DIR, ensure_dirs

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def _session_path(session_id: str):
    if not _UUID_RE.match(session_id):
        raise ValueError(f"Invalid session_id: {session_id!r}")
    return SESSIONS_DIR / f"{session_id}.json"


_SESSIONS_CACHE: list[dict] | None = None


def _list_sessions_raw() -> list[dict]:
    """Internal helper used by ui_bridge API route."""
    global _SESSIONS_CACHE
    if _SESSIONS_CACHE is not None:
        return _SESSIONS_CACHE

    ensure_dirs()
    sessions = []
    for p in sorted(SESSIONS_DIR.glob("*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append({
                "id": data["id"],
                "title": data.get("title", "Untitled"),
                "course": data.get("course", ""),
                "created_at": data.get("created_at", ""),
                "turn_count": len(data.get("turns", [])),
            })
        except Exception:
            continue
    _SESSIONS_CACHE = sessions
    return _SESSIONS_CACHE


def _create_session(title: str, course: str = "") -> str:
    global _SESSIONS_CACHE
    ensure_dirs()
    session_id = str(uuid.uuid4())
    data = {
        "id": session_id,
        "title": title,
        "course": course,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "turns": [],
    }
    _session_path(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    # Update cache
    new_entry = {
        "id": session_id,
        "title": title,
        "course": course,
        "created_at": data["created_at"],
        "turn_count": 0,
    }
    if _SESSIONS_CACHE is not None:
        _SESSIONS_CACHE.insert(0, new_entry)
    
    return session_id


def _save_turn(session_id: str, role: str, text: str,
               sources: list[str],
               blocks: list[dict] | None = None) -> str:
    global _SESSIONS_CACHE
    path = _session_path(session_id)
    if not path.exists():
        raise FileNotFoundError(f"Session {session_id} not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    turn = {"role": role, "text": text, "sources": sources}
    if blocks:
        turn["blocks"] = blocks
    data["turns"].append(turn)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    # Update cache turn count
    if _SESSIONS_CACHE is not None:
        for s in _SESSIONS_CACHE:
            if s["id"] == session_id:
                s["turn_count"] = len(data["turns"])
                break
    
    return session_id


def _load_session(session_id: str) -> dict:
    path = _session_path(session_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def register_session_tools(mcp: FastMCP):

    @mcp.tool()
    def create_session(title: str, course: str = "") -> str:
        """Create a new study session. Returns session_id."""
        return _create_session(title, course)

    @mcp.tool()
    def save_turn(session_id: str, role: str, text: str,
                  sources: list[str],
                  blocks: list[dict] | None = None) -> str:
        """Append a turn to a session. role: 'user'|'assistant'. Returns session_id."""
        return _save_turn(session_id, role, text, sources, blocks)

    @mcp.tool()
    def list_sessions() -> list[dict]:
        """List all study sessions, newest first."""
        return _list_sessions_raw()

    @mcp.tool()
    def load_session(session_id: str) -> dict:
        """Load a full session including all turns."""
        return _load_session(session_id)
