import threading
from unittest.mock import patch

from fastapi.testclient import TestClient

from smart_lms.tools.ui_bridge import app, _prompt_data, _prompt_events, _sse_queues

client = TestClient(app)


def test_root_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_post_prompt_sets_event():
    sid = "test-session-1"
    event = threading.Event()
    _prompt_events[sid] = event
    r = client.post(f"/api/prompt/{sid}", json={"text": "hello", "course_ids": [1]})
    assert r.status_code == 200
    assert event.is_set()
    assert _prompt_data[sid]["text"] == "hello"
    _prompt_events.pop(sid, None)
    _prompt_data.pop(sid, None)


def test_api_sessions_returns_list():
    with patch("smart_lms.tools.sessions._list_sessions_raw", return_value=[]):
        r = client.get("/api/sessions")
        assert r.status_code == 200
        assert r.json() == []


def test_api_courses_returns_list():
    with patch("smart_lms.tools.lms._list_courses_raw",
               return_value=[{"id": 1, "name": "MATH"}]):
        r = client.get("/api/courses")
        assert r.status_code == 200
        assert r.json()[0]["name"] == "MATH"
