import json
import queue
import threading
import uuid
import webbrowser
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP

from smart_lms.config import find_free_port, get_config

_prompt_events: dict[str, threading.Event] = {}
_prompt_data: dict[str, dict] = {}
_sse_queues: dict[str, queue.Queue] = {}
_web_port: int = 0
_web_started = threading.Event()

app = FastAPI()
UI_DIR = Path(__file__).parent.parent / "ui"

if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index = UI_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>UI not built</h1>")


@app.get("/api/events/{session_id}")
async def sse_events(session_id: str, request: Request):
    import asyncio
    q: queue.Queue = queue.Queue()
    _sse_queues[session_id] = q

    async def generate():
        loop = asyncio.get_event_loop()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await loop.run_in_executor(None, lambda: q.get(timeout=30))
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            _sse_queues.pop(session_id, None)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/prompt/{session_id}")
async def receive_prompt(session_id: str, request: Request):
    body = await request.json()
    _prompt_data[session_id] = body
    if session_id not in _prompt_events:
        _prompt_events[session_id] = threading.Event()
    _prompt_events[session_id].set()
    return JSONResponse({"ok": True})


@app.get("/api/credential-status")
def api_credential_status():
    from smart_lms.config import get_lms_credentials, get_config
    username, password = get_lms_credentials()
    cfg = get_config()
    connected = bool(username and password)
    return JSONResponse({
        "connected": connected,
        "username": username or "",
        "lms_url": cfg.get("lms_base_url", ""),
    })


@app.post("/api/setup-credentials")
async def api_setup_credentials(request: Request):
    from smart_lms.config import store_lms_credentials
    from smart_lms.tools.lms import _get_scraper
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()
        if not username or not password:
            return JSONResponse({"ok": False, "error": "Username and password are required."}, status_code=400)
        store_lms_credentials(username, password)
        scraper = _get_scraper()
        ok = scraper.login_test(username, password)
        if not ok:
            return JSONResponse({"ok": False, "error": "Login failed. Check your credentials."}, status_code=401)
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/sessions")
def api_sessions():
    from smart_lms.tools.sessions import _list_sessions_raw
    return JSONResponse(_list_sessions_raw())


@app.get("/api/courses")
def api_courses():
    from smart_lms.tools.lms import _list_courses_raw
    return JSONResponse(_list_courses_raw())


@app.get("/api/materials/{course_id}")
def api_materials(course_id: str):
    from smart_lms.tools.lms import _list_materials_raw
    return JSONResponse(_list_materials_raw(int(course_id)))


@app.post("/api/sessions")
async def api_create_session(request: Request):
    from smart_lms.tools.sessions import _create_session
    try:
        body = await request.json()
        title = body.get("title", "New Study Session")
        course = body.get("course", "")
        session_id = _create_session(title, course)
        return JSONResponse({"id": session_id})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/sessions/{session_id}")
def api_load_session(session_id: str):
    from smart_lms.tools.sessions import _load_session
    try:
        data = _load_session(session_id)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.delete("/api/sessions/{session_id}")
def api_delete_session(session_id: str):
    from smart_lms.tools.sessions import _session_path
    try:
        path = _session_path(session_id)
        if path.exists():
            path.unlink()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/api/sessions/{session_id}/rename")
async def api_rename_session(session_id: str, request: Request):
    from smart_lms.tools.sessions import _session_path
    try:
        body = await request.json()
        new_title = body.get("title", "Untitled")
        path = _session_path(session_id)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["title"] = new_title
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


def _run_web_server(port: int):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    _web_started.set()
    server.run()


def start_web_server(port: int):
    global _web_port
    _web_port = port
    t = threading.Thread(target=_run_web_server, args=(port,), daemon=True)
    t.start()
    _web_started.wait(timeout=5)


def register_ui_bridge_tools(mcp: FastMCP):

    @mcp.tool()
    def start_ui(session_id: Optional[str] = None) -> dict:
        """Launch the browser UI. Returns {session_id, url, port}.
        Starts web server on first call."""
        global _web_port
        if not _web_started.is_set():
            port = find_free_port(get_config().get("port", 8742))
            start_web_server(port)
        sid = session_id or str(uuid.uuid4())
        url = f"http://127.0.0.1:{_web_port}?session={sid}"
        webbrowser.open(url)
        return {"session_id": sid, "url": url, "port": _web_port}

    @mcp.tool()
    def wait_for_prompt(session_id: str) -> dict:
        """Block until user submits a prompt in the browser.
        Returns {text, course_ids, doc_ids, drive_files}."""
        event = threading.Event()
        _prompt_events[session_id] = event
        _prompt_data.pop(session_id, None)
        event.wait()
        _prompt_events.pop(session_id, None)
        return _prompt_data.pop(session_id, {})

    @mcp.tool()
    def render(session_id: str, blocks: list) -> str:
        """Push card blocks to the browser via SSE."""
        payload = json.dumps({"type": "blocks", "blocks": blocks})
        q = _sse_queues.get(session_id)
        if q:
            q.put(payload)
        return "ok"
