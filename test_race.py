import asyncio
import httpx
import threading
import time
import json
import sys
from pathlib import Path

# Add current dir to path for imports
sys.path.insert(0, str(Path.cwd()))

from smart_lms.tools.ui_bridge import (
    start_web_server, _web_port, _sse_queues, _prompt_events, _prompt_data
)
from smart_lms.config import find_free_port

async def test_race_condition(base_url, session_id):
    print(f"\nTesting RACE CONDITION (Prompt before Wait) for session {session_id}")
    
    # 1. Send prompt first
    async with httpx.AsyncClient() as client:
        print(f"Sending POST to /api/prompt/{session_id} BEFORE wait_for_prompt logic starts")
        r = await client.post(f"{base_url}/api/prompt/{session_id}", json={"text": "early prompt"})
        print(f"POST response: {r.status_code}")

    # 2. Now simulate wait_for_prompt logic
    def simulated_wait_for_prompt(sid):
        event = threading.Event()
        _prompt_events[sid] = event
        _prompt_data.pop(sid, None) # This is the problem! It clears existing data.
        print(f"DEBUG: _prompt_events[{sid}] set to {event}")
        print(f"DEBUG: Waiting for event...")
        event.wait(timeout=2)
        print(f"DEBUG: Event state after wait: {event.is_set()}")
        return _prompt_data.pop(sid, {})

    loop = asyncio.get_running_loop()
    wait_task = loop.run_in_executor(None, simulated_wait_for_prompt, session_id)
    
    try:
        print("Waiting to see if simulated_wait_for_prompt returns 'early prompt'...")
        result = await asyncio.wait_for(wait_task, timeout=3)
        print(f"Result returned: {result}")
        if not result:
            print("CONFIRMED: Prompt was lost due to race condition.")
            return True
        return result.get("text") == "early prompt"
    except asyncio.TimeoutError:
        print("CONFIRMED: wait_for_prompt HUNG (Race Condition confirmed)")
        if session_id in _prompt_events:
            _prompt_events[session_id].set() 
        return True

async def main():
    port = find_free_port(8747)
    start_web_server(port)
    base_url = f"http://127.0.0.1:{port}"
    await asyncio.sleep(1)
    
    await test_race_condition(base_url, "test-race-session")

if __name__ == "__main__":
    asyncio.run(main())
