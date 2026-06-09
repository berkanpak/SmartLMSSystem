import sys
import json
import uuid
import webbrowser
import threading
import time
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from smart_lms.tools.ui_bridge import start_web_server, _web_port, _web_started, _prompt_events, _prompt_data, _sse_queues
from smart_lms.tools.lms import _list_courses_raw
from smart_lms.tools.sessions import _create_session
from smart_lms.config import find_free_port, get_config

PROMPT_FILE = Path("prompt.json")
RESPONSE_FILE = Path("response.json")

def daemon():
    # 1. Start web server
    port = find_free_port(get_config().get("port", 8742))
    print(f"DAEMON_STARTING_ON: {port}")
    start_web_server(port)
    
    # 2. Prepare session
    session_id = str(uuid.uuid4())
    url = f"http://127.0.0.1:{port}?session={session_id}"
    
    # 3. Boot sequence
    courses = _list_courses_raw()
    sid = _create_session(title="Study Session", course="")
    
    print(f"SESSION_ID: {session_id}")
    print(f"URL: {url}")
    
    while True:
        # Check if we need to wait for a prompt across all sessions
        current_sessions = list(_prompt_events.keys())
        for sid in current_sessions:
            event = _prompt_events.get(sid)
            if event and event.is_set():
                data = _prompt_data.pop(sid, {})
                data["session_id"] = sid
                PROMPT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
                _prompt_events.pop(sid, None)
                print(f"PROMPT_RECEIVED_FOR: {sid}")

        # Check if we have a response to render
        if RESPONSE_FILE.exists():
            try:
                resp_data = json.loads(RESPONSE_FILE.read_text(encoding="utf-8"))
                target_sid = resp_data.get("session_id")
                blocks = resp_data.get("blocks", [])

                # Push to SSE
                payload = json.dumps({"type": "blocks", "blocks": blocks})

                # If target_sid is specified, send to it, otherwise send to all active SSE queues
                sent = False
                if target_sid and target_sid in _sse_queues:
                    _sse_queues[target_sid].put(payload)
                    sent = True
                
                if not sent:
                    for q in _sse_queues.values():
                        q.put(payload)
                
                RESPONSE_FILE.unlink()
                print(f"RENDERED_RESPONSE_FOR: {target_sid}")
            except Exception as e:
                print(f"RENDER_ERROR: {e}")
                if RESPONSE_FILE.exists(): RESPONSE_FILE.unlink()

        time.sleep(0.5)

if __name__ == "__main__":
    daemon()
