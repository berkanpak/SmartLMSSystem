import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from smart_lms.tools.ui_bridge import start_web_server, _web_started, _prompt_events, _prompt_buffers

def wait_for_any_prompt():
    port = 8742
    
    # Check if server is already running by trying to connect or checking a flag
    # In this context, if we get a bind error, we should just proceed to poll
    if not _web_started.is_set():
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            is_open = s.connect_ex(('127.0.0.1', port)) == 0
        
        if not is_open:
            print(f"Starting server on {port}...")
            start_web_server(port)
        else:
            print(f"Server already running on {port}, joining...")
            _web_started.set()
    
    print("READY_TO_RECEIVE")
    
    # Poll for any set event
    while True:
        for sid, event in list(_prompt_events.items()):
            if event.is_set():
                q = _prompt_buffers.get(sid)
                try:
                    data = q.get_nowait() if q else {}
                except:
                    data = {}
                data['session_id'] = sid
                event.clear()
                
                # Print the data so the CLI agent can read it
                print("PROMPT_DATA_START")
                print(json.dumps(data))
                print("PROMPT_DATA_END")
                return # Exit so CLI agent can take over
        
        time.sleep(0.5)

if __name__ == "__main__":
    wait_for_any_prompt()
