import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from smart_lms.tools.ui_bridge import start_web_server, _web_started, _prompt_events, _prompt_data

def wait_for_any_prompt():
    port = 8742
    if not _web_started.is_set():
        print(f"Starting server on {port}...")
        start_web_server(port)
    
    print("READY_TO_RECEIVE")
    
    # Poll for any set event
    while True:
        for sid, event in list(_prompt_events.items()):
            if event.is_set():
                data = _prompt_data.pop(sid, {})
                data['session_id'] = sid
                _prompt_events.pop(sid, None)
                
                # Print the data so the CLI agent can read it
                print("PROMPT_DATA_START")
                print(json.dumps(data))
                print("PROMPT_DATA_END")
                return # Exit so CLI agent can take over
        
        time.sleep(0.5)

if __name__ == "__main__":
    wait_for_any_prompt()
