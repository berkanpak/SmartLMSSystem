import time
from pathlib import Path
import json

PROMPT_FILE = Path("prompt.json")

def wait():
    print("Waiting for you to click Send in Chrome...")
    while not PROMPT_FILE.exists():
        time.sleep(1)
    
    data = json.loads(PROMPT_FILE.read_text(encoding="utf-8"))
    print("\n--- NEW PROMPT DETECTED ---")
    print(f"Session ID: {data.get('session_id')}")
    print(f"Text: {data.get('text')}")
    print(f"Course IDs: {data.get('course_ids')}")
    print(f"Doc IDs: {data.get('doc_ids')}")
    print("---------------------------\n")

if __name__ == "__main__":
    wait()
