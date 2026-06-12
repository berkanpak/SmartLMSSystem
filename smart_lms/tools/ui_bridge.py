import json
import queue
import threading
import uuid
import webbrowser
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP

from smart_lms.config import find_free_port, get_config

_prompt_events: Dict[str, threading.Event] = {}
_prompt_buffers: Dict[str, queue.Queue] = {}
_sse_subscribers: Dict[str, List[queue.Queue]] = {}
_web_port: int = 0
_web_started = threading.Event()

# Aliases for backward compatibility with daemon and wait_loop
_prompt_data = _prompt_buffers
_sse_queues = _sse_subscribers

app = FastAPI()
UI_DIR = Path(__file__).parent.parent / "ui"

if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index = UI_DIR / "index.html"
    if index.exists():
        content = await asyncio.to_thread(index.read_text, encoding="utf-8")
        return HTMLResponse(content)
    return HTMLResponse("<h1>UI not built</h1>")


@app.get("/api/events/{session_id}")
async def sse_events(session_id: str, request: Request):
    q: queue.Queue = queue.Queue()
    if session_id not in _sse_subscribers:
        _sse_subscribers[session_id] = []
    _sse_subscribers[session_id].append(q)
    print(f"SSE: New subscriber for {session_id}. Total: {len(_sse_subscribers[session_id])}", file=sys.stderr)

    async def generate():
        loop = asyncio.get_event_loop()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Priority 1: Check queue with small timeout
                    data = await loop.run_in_executor(None, lambda: q.get(timeout=2.0))
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    # Priority 2: Keepalive only if empty
                    yield ": keepalive\n\n"
        finally:
            if session_id in _sse_subscribers:
                if q in _sse_subscribers[session_id]:
                    _sse_subscribers[session_id].remove(q)
                if not _sse_subscribers[session_id]:
                    _sse_subscribers.pop(session_id)
            print(f"SSE: Subscriber disconnected for {session_id}", file=sys.stderr)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/prompt/{session_id}")
async def receive_prompt(session_id: str, request: Request):
    body = await request.json()
    print(f"API: Received prompt for {session_id}: {body.get('text', '')[:20]}...", file=sys.stderr)
    if session_id not in _prompt_buffers:
        _prompt_buffers[session_id] = queue.Queue()
    
    _prompt_buffers[session_id].put(body)
    
    if session_id not in _prompt_events:
        _prompt_events[session_id] = threading.Event()
    
    print(f"API: Triggering event for {session_id}", file=sys.stderr)
    _prompt_events[session_id].set()
    
    return JSONResponse({"ok": True})


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


def _delete_session_data(session_id: str):
    """Purge all global memory buffers for a session."""
    _prompt_buffers.pop(session_id, None)
    _prompt_events.pop(session_id, None)
    _sse_subscribers.pop(session_id, None)


@app.delete("/api/sessions/{session_id}")
def api_delete_session(session_id: str):
    from smart_lms.tools.sessions import _session_path, _turns_path, _clear_session_cache
    try:
        path = _session_path(session_id)
        if path.exists():
            path.unlink()
        t_path = _turns_path(session_id)
        if t_path.exists():
            t_path.unlink()
        
        _delete_session_data(session_id)
        _clear_session_cache()
        
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
            data_str = await asyncio.to_thread(path.read_text, encoding="utf-8")
            data = json.loads(data_str)
            data["title"] = new_title
            await asyncio.to_thread(path.write_text, json.dumps(data, indent=2), encoding="utf-8")
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


def _run_web_server(port: int):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
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
    def check_prompt(session_id: str) -> dict:
        """Check if user submitted a prompt in the browser. Returns immediately.
        Returns {text, course_ids, doc_ids, drive_files} or {"status": "no_prompt"}."""
        if session_id in _prompt_buffers:
            try:
                return _prompt_buffers[session_id].get_nowait()
            except queue.Empty:
                pass
        return {"status": "no_prompt"}

    @mcp.tool()
    def wait_for_prompt(session_id: str, timeout: int = 60) -> dict:
        """Wait for the user to submit a prompt in the browser. Blocks until a prompt is received or timeout.
        Returns the prompt data or {"status": "timeout"}."""
        if session_id not in _prompt_events:
            _prompt_events[session_id] = threading.Event()
        
        # Check if there's already something in the buffer
        if session_id in _prompt_buffers and not _prompt_buffers[session_id].empty():
            try:
                return _prompt_buffers[session_id].get_nowait()
            except queue.Empty:
                pass

        print(f"WAIT: Waiting for prompt on {session_id} (timeout={timeout}s)...", file=sys.stderr)
        event = _prompt_events[session_id]
        event.clear() # Clear before waiting
        
        if event.wait(timeout=timeout):
            print(f"WAIT: Prompt received for {session_id}", file=sys.stderr)
            event.clear()
            if session_id in _prompt_buffers:
                try:
                    return _prompt_buffers[session_id].get_nowait()
                except queue.Empty:
                    pass
        
        return {"status": "timeout"}

    @mcp.tool()
    def render(session_id: str, blocks: list) -> str:
        """Push card blocks to the browser via SSE."""
        payload = json.dumps({"type": "blocks", "blocks": blocks})
        subs = _sse_subscribers.get(session_id, [])
        for q in subs:
            q.put(payload)
        return "ok"
