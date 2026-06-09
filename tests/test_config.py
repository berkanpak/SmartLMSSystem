import json
import pytest
from unittest.mock import patch
import mcp.config as cfg_mod


@pytest.fixture(autouse=True)
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_mod, "SMART_LMS_DIR", tmp_path / ".smart-lms")
    monkeypatch.setattr(cfg_mod, "SESSIONS_DIR", tmp_path / ".smart-lms" / "sessions")
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / ".smart-lms" / "config.json")


def test_ensure_dirs_creates_directories():
    cfg_mod.ensure_dirs()
    assert cfg_mod.SMART_LMS_DIR.exists()
    assert cfg_mod.SESSIONS_DIR.exists()


def test_get_config_returns_defaults_on_first_run():
    result = cfg_mod.get_config()
    assert result["lms_base_url"] == cfg_mod.DEFAULT_LMS_URL
    assert result["google_drive_connected"] is False


def test_save_and_reload_config():
    cfg_mod.save_config({"lms_username": "testuser", "port": 9000})
    result = cfg_mod.get_config()
    assert result["lms_username"] == "testuser"
    assert result["port"] == 9000


def test_get_lms_credentials_none_when_no_username():
    u, p = cfg_mod.get_lms_credentials()
    assert u is None and p is None


def test_store_and_get_lms_credentials():
    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password", return_value="secret"):
        cfg_mod.store_lms_credentials("alice", "secret")
        mock_set.assert_called_once_with(
            cfg_mod.KEYCHAIN_SERVICE, "alice", "secret"
        )
        u, p = cfg_mod.get_lms_credentials()
        assert u == "alice" and p == "secret"


def test_find_free_port_returns_preferred_when_available():
    port = cfg_mod.find_free_port(9999)
    assert isinstance(port, int)
    assert port > 0


def test_store_lms_credentials_raises_on_keyring_failure():
    with patch("keyring.set_password", side_effect=Exception("no keyring")):
        with pytest.raises(RuntimeError, match="system keychain"):
            cfg_mod.store_lms_credentials("bob", "pass")
