import importlib
import json
import sys
import tomllib
from pathlib import Path

import install


def reload_installer(monkeypatch, tmp_path):
    monkeypatch.setattr(install, "HOME", tmp_path)
    return install


def test_claude_code_registers_user_scoped_mcp_in_claude_json(tmp_path, monkeypatch):
    installer = reload_installer(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()

    tools = {name: (cfg, handler) for name, _detect, cfg, handler in installer.tools(repo)}
    cfg_path, handler = tools["Claude Code"]

    assert cfg_path == tmp_path / ".claude.json"
    assert handler(cfg_path, repo, uninstall=False) == "registered"

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    entry = data["mcpServers"]["smart-lms"]
    assert entry["type"] == "stdio"
    assert entry["command"] == sys.executable
    assert entry["args"] == ["-m", "smart_lms.server"]
    assert entry["cwd"] == str(repo)
    assert entry["env"]["PYTHONPATH"] == str(repo)


def test_codex_registers_mcp_in_config_toml(tmp_path, monkeypatch):
    installer = reload_installer(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg_path = tmp_path / ".codex" / "config.toml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(
        'model = "gpt-5"\n\n[mcp_servers.old]\ncommand = "old"\n',
        encoding="utf-8",
    )

    assert installer.install_codex(cfg_path, repo, uninstall=False) == "registered"

    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    entry = data["mcp_servers"]["smart-lms"]
    assert entry["command"] == sys.executable
    assert entry["args"] == ["-m", "smart_lms.server"]
    assert entry["cwd"] == str(repo)
    assert entry["env"]["PYTHONPATH"] == str(repo)


def test_codex_registration_replaces_existing_smart_lms_block(tmp_path, monkeypatch):
    installer = reload_installer(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg_path = tmp_path / ".codex" / "config.toml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(
        '\n[mcp_servers.smart-lms]\ncommand = "bad"\n\n'
        '[mcp_servers.smart-lms.env]\nPYTHONPATH = "bad"\n\n'
        '[mcp_servers.keep]\ncommand = "keep"\n',
        encoding="utf-8",
    )

    installer.install_codex(cfg_path, repo, uninstall=False)
    text = cfg_path.read_text(encoding="utf-8")

    assert text.count("[mcp_servers.smart-lms]") == 1
    data = tomllib.loads(text)
    assert data["mcp_servers"]["keep"]["command"] == "keep"
    assert data["mcp_servers"]["smart-lms"]["cwd"] == str(repo)


def test_skill_installs_to_interoperable_user_skill_locations(tmp_path, monkeypatch):
    installer = reload_installer(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    skill_source = repo / ".agents" / "skills" / "smart-lms" / "SKILL.md"
    skill_source.parent.mkdir(parents=True)
    skill_source.write_text(installer.SKILL_MD, encoding="utf-8")

    installer.install_skill(repo, uninstall=False)

    expected = [
        tmp_path / ".claude" / "skills" / "smart-lms" / "SKILL.md",
        tmp_path / ".agents" / "skills" / "smart-lms" / "SKILL.md",
        tmp_path / ".gemini" / "skills" / "smart-lms" / "SKILL.md",
        tmp_path / ".gemini" / "antigravity-cli" / "skills" / "smart-lms" / "SKILL.md",
        tmp_path / ".codex" / "skills" / "smart-lms" / "SKILL.md",
    ]
    for path in expected:
        assert path.read_text(encoding="utf-8").startswith("---\nname: smart-lms")


def test_zed_uses_current_context_server_schema(tmp_path, monkeypatch):
    installer = reload_installer(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg_path = tmp_path / "zed" / "settings.json"

    assert installer.install_zed(cfg_path, repo, uninstall=False) == "registered"

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    entry = data["context_servers"]["smart-lms"]
    assert entry["command"] == sys.executable
    assert entry["args"] == ["-m", "smart_lms.server"]
    assert entry["env"]["PYTHONPATH"] == str(repo)
