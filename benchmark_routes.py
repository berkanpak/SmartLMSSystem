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

async def benchmark_endpoint(url, name, rps=5, duration=2):
    print(f"\nBenchmarking {name} at {url} ({rps} RPS for {duration}s)")
    # Increased timeout to 20s to see if courses eventually returns
    async with httpx.AsyncClient(timeout=20.0) as client:
        start_time = time.time()
        tasks = []
        while time.time() - start_time < duration:
            tasks.append(client.get(url))
            await asyncio.sleep(1/rps)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        stats = {}
        for r in responses:
            if isinstance(r, httpx.Response):
                stats[r.status_code] = stats.get(r.status_code, 0) + 1
            else:
                err_name = type(r).__name__
                stats[err_name] = stats.get(err_name, 0) + 1
        
        print(f"Finished {name} results: {stats}")
        return stats

async def test_sse_stability(base_url, session_id):
    print(f"\nTesting SSE stability for session {session_id}")
    url = f"{base_url}/api/events/{session_id}"
    
    received_messages = []
    
    async def listen_sse():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            received_messages.append(line[6:])
                        elif line.startswith(": keepalive"):
                            pass
        except Exception as e:
            # print(f"SSE Listener error: {e}")
            pass
    
    listener_task = asyncio.create_task(listen_sse())
    
    # Wait for connection to be registered in _sse_queues
    print("Waiting for SSE connection registration...")
    for _ in range(50):
        if session_id in _sse_queues:
            break
        await asyncio.sleep(0.1)
    
    if session_id not in _sse_queues:
        print("FAILED: SSE connection never registered in _sse_queues")
        listener_task.cancel()
        return 0, 10

    # Send multiple messages via simulated render
    num_messages = 10
    print(f"Sending {num_messages} messages via SSE...")
    for i in range(num_messages):
        payload = json.dumps({"type": "blocks", "blocks": [{"type": "text", "text": f"msg {i}"}]})
        q = _sse_queues.get(session_id)
        if q:
            q.put(payload)
        await asyncio.sleep(0.05) # Faster sending
    
    await asyncio.sleep(1)
    listener_task.cancel()
    
    print(f"SSE Received {len(received_messages)}/{num_messages} messages")
    if len(received_messages) < num_messages:
        print("CONFIRMED: SSE dropped messages or failed to receive all.")
    else:
        print("SSE looks stable for this load.")
    return len(received_messages), num_messages

async def test_prompt_trigger(base_url, session_id):
    print(f"\nTesting prompt trigger for session {session_id}")
    
    # Simulate wait_for_prompt tool logic
    event = threading.Event()
    _prompt_events[session_id] = event
    _prompt_data.pop(session_id, None)
    
    def wait_on_event():
        print("Waiting on event...")
        return event.wait(timeout=5)
    
    loop = asyncio.get_running_loop()
    wait_task = loop.run_in_executor(None, wait_on_event)
    
    await asyncio.sleep(0.5)
    
    async with httpx.AsyncClient() as client:
        print(f"Sending POST to /api/prompt/{session_id}")
        r = await client.post(f"{base_url}/api/prompt/{session_id}", json={"text": "test prompt"})
        print(f"POST /api/prompt response: {r.status_code}")
    
    success = await wait_task
    if success:
        data = _prompt_data.pop(session_id, {})
        print(f"Event triggered! Data: {data}")
        return data.get("text") == "test prompt"
    else:
        print("CONFIRMED: wait_for_prompt TIMEOUT - trigger failed")
        return False

async def main():
    port = find_free_port(8745)
    start_web_server(port)
    base_url = f"http://127.0.0.1:{port}"
    
    print(f"Server started at {base_url}")
    await asyncio.sleep(1)
    
    await benchmark_endpoint(f"{base_url}/api/sessions", "GET /api/sessions", rps=10, duration=2)
    await benchmark_endpoint(f"{base_url}/api/courses", "GET /api/courses", rps=10, duration=2)
    
    await test_sse_stability(base_url, "test-sse-session")
    
    await test_prompt_trigger(base_url, "test-prompt-session")

if __name__ == "__main__":
    asyncio.run(main())
