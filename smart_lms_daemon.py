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

from smart_lms.tools.ui_bridge import (
    start_web_server, _web_port, _web_started, 
    _prompt_events, _prompt_buffers, _sse_subscribers
)
from smart_lms.tools.lms import _list_courses_raw
from smart_lms.tools.sessions import _create_session
from smart_lms.config import find_free_port, get_config

PROMPT_FILE = Path("prompt.json")
RESPONSE_FILE = Path("response.json")

def session_worker(session_id: str):
    """
    Acts as the autonomous agent for a specific session.
    Follows the logic defined in SKILL.md:
    Wait for Prompt -> Gather Sources -> Interpret -> Render
    """
    print(f"AGENT_STARTED_FOR: {session_id}")
    while True:
        # This part usually requires an LLM call. 
        # In this daemon, we bridge the prompt to a file for the CLI agent to pick up,
        # OR we could integrate a direct LLM call here if API keys were provided.
        # For now, we follow the user's request to have an 'agent' waiting.
        event = _prompt_events.get(session_id)
        if event and event.is_set():
            q = _prompt_buffers.get(session_id)
            try:
                data = q.get_nowait() if q else {}
                data["session_id"] = session_id
                # Signal to the CLI that a prompt is ready for this specific session
                PROMPT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
                event.clear()
                print(f"PROMPT_READY: {session_id}")
            except:
                pass
        time.sleep(0.5)

def daemon():
    # 1. Start web server
    port = find_free_port(get_config().get("port", 8742))
    print(f"DAEMON_STARTING_ON: {port}")
    start_web_server(port)
    
    active_workers = {}
    
    print("DAEMON_READY")
    
    while True:
        # Monitor for new sessions and start workers
        for sid in list(_prompt_events.keys()):
            if sid not in active_workers:
                t = threading.Thread(target=session_worker, args=(sid,), daemon=True)
                t.start()
                active_workers[sid] = t
        
        # Check for response to render (from CLI agent)
        if RESPONSE_FILE.exists():
            # ... (existing render logic) ...


if __name__ == "__main__":
    daemon()
