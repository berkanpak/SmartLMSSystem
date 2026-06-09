import json
import time

import pytest

import smart_lms.config as cfg_mod
import smart_lms.tools.sessions as sess_mod
from smart_lms.tools.sessions import (
    _create_session,
    _list_sessions_raw,
    _load_session,
    _save_turn,
    _session_path,
)


@pytest.fixture(autouse=True)
def tmp_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_mod, "SMART_LMS_DIR", tmp_path / ".smart-lms")
    monkeypatch.setattr(cfg_mod, "SESSIONS_DIR", tmp_path / ".smart-lms" / "sessions")
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / ".smart-lms" / "config.json")
    monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path / ".smart-lms" / "sessions")
    cfg_mod.ensure_dirs()


def test_create_session_returns_uuid():
    sid = _create_session("Test", "X")
    assert len(sid) == 36
    assert _session_path(sid).exists()
    data = json.loads(_session_path(sid).read_text())
    assert data["title"] == "Test"
    assert data["course"] == "X"
    assert data["turns"] == []


def test_save_and_load_turn():
    sid = _create_session("T")
    _save_turn(sid, "user", "Hello", ["course:1"])
    session = _load_session(sid)
    assert session["turns"][0]["text"] == "Hello"
    assert session["turns"][0]["role"] == "user"
    assert session["turns"][0]["sources"] == ["course:1"]


def test_list_sessions_returns_newest_first():
    sid1 = _create_session("A")
    time.sleep(0.02)
    sid2 = _create_session("B")
    sessions = _list_sessions_raw()
    assert len(sessions) == 2
    assert sessions[0]["id"] == sid2


def test_load_missing_session_returns_empty():
    import uuid
    missing_id = str(uuid.uuid4())
    result = _load_session(missing_id)
    assert result == {}
