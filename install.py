#!/usr/bin/env python3
"""
Smart LMS — one-shot MCP installer.

Registers the smart-lms MCP server into every detected AI coding tool:
  Claude Code, Codex CLI, Gemini CLI, Cursor, Windsurf, Zed, Continue.

Usage:
  python install.py                  # auto-detect repo location
  python install.py --repo /path     # explicit repo path
  python install.py --uninstall      # remove from all tools
"""
import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

import io, sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    try: _sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

def bold(s): return f"\033[1m{s}\033[0m"
def green(s): return f"\033[32m{s}\033[0m"
def yellow(s): return f"\033[33m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

HOME = Path.home()


# ── MCP entry ─────────────────────────────────────────────────────────────────

def mcp_entry(repo: Path) -> dict:
    return {
        "command": sys.executable,
        "args": ["-m", "smart_lms.server"],
        "cwd": str(repo),
    }


# ── Tool registrations ────────────────────────────────────────────────────────

def install_json_mcpServers(path: Path, repo: Path, uninstall: bool) -> str:
    """Generic handler for tools that use {mcpServers: {name: entry}} JSON."""
    cfg = read_json(path)
    servers = cfg.setdefault("mcpServers", {})
    if uninstall:
        if "smart-lms" in servers:
            del servers["smart-lms"]
            write_json(path, cfg)
            return "removed"
        return "not registered"
    servers["smart-lms"] = mcp_entry(repo)
    write_json(path, cfg)
    return "registered"


def install_zed(path: Path, repo: Path, uninstall: bool) -> str:
    """Zed uses context_servers with a different shape."""
    cfg = read_json(path)
    servers = cfg.setdefault("context_servers", {})
    if uninstall:
        if "smart-lms" in servers:
            del servers["smart-lms"]
            write_json(path, cfg)
            return "removed"
        return "not registered"
    servers["smart-lms"] = {
        "command": {
            "path": sys.executable,
            "args": ["-m", "smart_lms.server"],
            "env": {"PYTHONPATH": str(repo)},
        }
    }
    write_json(path, cfg)
    return "registered"


def install_continue(path: Path, repo: Path, uninstall: bool) -> str:
    """Continue.dev uses mcpServers as a list, not a dict."""
    cfg = read_json(path)
    servers = cfg.setdefault("mcpServers", [])
    existing = next((i for i, s in enumerate(servers) if s.get("name") == "smart-lms"), None)
    if uninstall:
        if existing is not None:
            servers.pop(existing)
            write_json(path, cfg)
            return "removed"
        return "not registered"
    entry = {"name": "smart-lms", **mcp_entry(repo)}
    if existing is not None:
        servers[existing] = entry
    else:
        servers.append(entry)
    write_json(path, cfg)
    return "registered"


# ── Tool catalogue ────────────────────────────────────────────────────────────

def tools(repo: Path):
    """
    Returns list of (display_name, detect_path, config_path, handler).
    detect_path: if this exists, the tool is considered installed.
    config_path: where to write the config (created if absent).
    """
    W = os.name == "nt"
    APPDATA = Path(os.environ.get("APPDATA", HOME / "AppData" / "Roaming"))
    LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData" / "Local"))
    XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))

    return [
        (
            "Claude Code",
            HOME / ".claude",
            HOME / ".claude" / "settings.json",
            install_json_mcpServers,
        ),
        (
            "Codex CLI (OpenAI)",
            HOME / ".codex",
            HOME / ".codex" / "config.json",
            install_json_mcpServers,
        ),
        (
            "Gemini CLI",
            HOME / ".gemini",
            HOME / ".gemini" / "settings.json",
            install_json_mcpServers,
        ),
        (
            "Cursor",
            (APPDATA / "Cursor") if W else (HOME / ".config" / "Cursor"),
            (APPDATA / "Cursor" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "mcp_settings.json")
                if W else (HOME / ".cursor" / "mcp.json"),
            install_json_mcpServers,
        ),
        (
            "Windsurf (Codeium)",
            (APPDATA / "Windsurf") if W else (HOME / ".codeium" / "windsurf"),
            (APPDATA / "Windsurf" / "User" / "globalStorage" / "codeium.codeium" / "mcp_config.json")
                if W else (HOME / ".codeium" / "windsurf" / "mcp_config.json"),
            install_json_mcpServers,
        ),
        (
            "Zed",
            (APPDATA / "Zed") if W else (XDG_CONFIG / "zed"),
            (APPDATA / "Zed" / "settings.json") if W else (XDG_CONFIG / "zed" / "settings.json"),
            install_zed,
        ),
        (
            "Continue",
            HOME / ".continue",
            HOME / ".continue" / "config.json",
            install_continue,
        ),
    ]


# ── main ──────────────────────────────────────────────────────────────────────

def install_deps(repo: Path):
    req = repo / "requirements.txt"
    if not req.exists():
        return
    print(bold("  Installing Python dependencies…"))
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
        stderr=subprocess.DEVNULL,
    )
    print(green("  [ok] dependencies installed"))


def main():
    parser = argparse.ArgumentParser(description="Smart LMS MCP installer")
    parser.add_argument("--repo", type=Path,
                        default=Path(__file__).parent.resolve(),
                        help="Path to the SmartLMSSystem repo")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove smart-lms from all tools")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Skip pip install")
    args = parser.parse_args()

    repo = args.repo.resolve()
    action = "Uninstalling" if args.uninstall else "Installing"

    print()
    print(bold(f"  Smart LMS MCP — {action}"))
    print(dim(f"  repo: {repo}"))
    print()

    if not args.uninstall and not args.skip_deps:
        install_deps(repo)
        print()

    registered = []
    skipped = []

    for name, detect, cfg_path, handler in tools(repo):
        if not detect.exists():
            skipped.append(name)
            continue
        result = handler(cfg_path, repo, args.uninstall)
        verb = {"registered": "ok", "removed": "ok", "not registered": "--"}[result]
        color = green if result in ("registered", "removed") else dim
        print(f"  {color(verb)} {name}")
        print(dim(f"    {cfg_path}"))
        registered.append(name)

    print()
    if registered:
        print(bold(f"  {action} complete for: {', '.join(registered)}"))
    if skipped:
        print(dim(f"  Skipped (not installed): {', '.join(skipped)}"))

    if not args.uninstall:
        print()
        print(bold("  Next steps:"))
        print("  1. Reload / restart your AI coding tool")
        print("  2. Set your Moodle credentials once:")
        print(dim('     call setup_lms_credentials("your@email.com", "password")'))
        print("  3. Type  /smart-lms  to launch the study UI")
        print()


if __name__ == "__main__":
    main()
