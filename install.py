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
import re
import shutil
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
    backup_file(path)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_file(path)
    path.write_text(text, encoding="utf-8")


def backup_file(path: Path):
    if not path.exists():
        return
    backup = path.with_name(path.name + ".smart-lms.bak")
    if not backup.exists():
        shutil.copy2(path, backup)

HOME = Path.home()


# ── MCP entry ─────────────────────────────────────────────────────────────────

def mcp_env(repo: Path) -> dict:
    return {"PYTHONPATH": str(repo)}


def mcp_entry(repo: Path, *, include_type: bool = False) -> dict:
    entry = {
        "command": sys.executable,
        "args": ["-m", "smart_lms.server"],
        "cwd": str(repo),
        "env": mcp_env(repo),
    }
    if include_type:
        entry = {"type": "stdio", **entry}
    return entry


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


def remove_json_mcp_server(path: Path, name: str) -> bool:
    cfg = read_json(path)
    servers = cfg.get("mcpServers")
    if not isinstance(servers, dict) or name not in servers:
        return False
    del servers[name]
    if not servers:
        del cfg["mcpServers"]
    write_json(path, cfg)
    return True


def install_claude(path: Path, repo: Path, uninstall: bool) -> str:
    """Claude Code user-scoped MCP lives in ~/.claude.json."""
    cfg = read_json(path)
    servers = cfg.setdefault("mcpServers", {})
    if uninstall:
        if "smart-lms" in servers:
            del servers["smart-lms"]
            if not servers:
                del cfg["mcpServers"]
            write_json(path, cfg)
            remove_json_mcp_server(HOME / ".claude" / "settings.json", "smart-lms")
            return "removed"
        remove_json_mcp_server(HOME / ".claude" / "settings.json", "smart-lms")
        return "not registered"

    servers["smart-lms"] = mcp_entry(repo, include_type=True)
    write_json(path, cfg)
    remove_json_mcp_server(HOME / ".claude" / "settings.json", "smart-lms")
    return "registered"


def toml_string(value: str) -> str:
    return json.dumps(value)


def remove_codex_server_block(text: str) -> str:
    lines = text.splitlines()
    kept = []
    skip = False
    table_header = re.compile(r"^\s*\[")
    smart_lms_header = re.compile(
        r"^\s*\[\s*mcp_servers\.(?:smart-lms|\"smart-lms\")(?:\.|\])"
    )

    for line in lines:
        if table_header.match(line):
            skip = bool(smart_lms_header.match(line))
            if skip:
                continue
        if not skip:
            kept.append(line)

    return "\n".join(kept).rstrip() + ("\n" if kept else "")


def install_codex(path: Path, repo: Path, uninstall: bool) -> str:
    """OpenAI Codex reads MCP servers from ~/.codex/config.toml."""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    had_entry = "mcp_servers.smart-lms" in existing or 'mcp_servers."smart-lms"' in existing
    text = remove_codex_server_block(existing)

    if uninstall:
        if had_entry:
            write_text(path, text)
            return "removed"
        return "not registered"

    block = textwrap.dedent(
        f"""
        [mcp_servers.smart-lms]
        command = {toml_string(sys.executable)}
        args = ["-m", "smart_lms.server"]
        cwd = {toml_string(str(repo))}
        startup_timeout_sec = 30

        [mcp_servers.smart-lms.env]
        PYTHONPATH = {toml_string(str(repo))}
        """
    ).strip()

    write_text(path, (text.rstrip() + "\n\n" + block + "\n").lstrip())
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
        "command": sys.executable,
        "args": ["-m", "smart_lms.server"],
        "env": mcp_env(repo),
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
            HOME / ".claude.json",
            install_claude,
        ),
        (
            "Codex CLI (OpenAI)",
            HOME / ".codex",
            HOME / ".codex" / "config.toml",
            install_codex,
        ),
        (
            "Gemini CLI",
            HOME / ".gemini",
            HOME / ".gemini" / "settings.json",
            install_json_mcpServers,
        ),
        (
            "Cursor",
            HOME / ".cursor",
            HOME / ".cursor" / "mcp.json",
            install_json_mcpServers,
        ),
        (
            "Windsurf (Codeium)",
            HOME / ".codeium" / "windsurf",
            HOME / ".codeium" / "windsurf" / "mcp_config.json",
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


SKILL_MD = """\
---
name: smart-lms
description: Launch a browser-based LMS study assistant. The agent teaches,
  quizzes, and examines using the student's Moodle course materials, Google
  Drive, and NotebookLM as sources. Output is rendered as flashcards, quiz
  cards, summaries, and mock exams.
trigger: /smart-lms
---

# Smart LMS Skill

You are a student study assistant. When this skill is invoked, follow the
boot sequence and then run the study loop.

## MCP Server

This skill requires the smart-lms MCP server. It must be registered in
your tool's MCP settings pointing to:
  python -m smart_lms.server
from the SmartLMSSystem repo directory.

## Boot Sequence

1. Call `start_ui()` — launches the browser UI and returns
   `{session_id, url, port}`. Save `session_id` for the rest of the session.
2. Call `list_courses()` to confirm LMS credentials are working.
   If the result is empty, tell the user: "Your LMS credentials are not set.
   Please configure them using one of these methods: (1) run
   `python setup_credentials.py` in the terminal, or (2) click the ⚙ gear
   icon in the bottom-left of the browser UI. Your password is stored
   securely and never needs to be typed in this chat."
3. Call `create_session(title="New session", course="")` to start
   persisting this conversation.

## Study Loop (repeat until user closes the browser or says goodbye)

### Step 1 — Wait for user input
Call `wait_for_prompt(session_id)`.
Returns: `{text, course_ids, doc_ids, drive_files}`

### Step 2 — Gather sources
For each selected course_id, call `get_material_text(course_id, doc_ids)`
to get `[{title, text}]`. Concatenate all text as `<SOURCE_TEXT>`.

### Step 3 — Interpret intent and generate card blocks

Use `<SOURCE_TEXT>` as the knowledge base. Do NOT make up facts.

- "teach me X" / "explain X": 4-8 flashcards + 1 summary block
- "quiz me" / "test me" / "examine me": 1 quiz block + 1 exam block
- "summarize X": 1 summary block only
- Other: reply in prose

### Step 4 — Render and persist

Call `render(session_id, blocks)` to push card blocks to the browser.
Call `save_turn(session_id, "user", <user text>, <source list>, null)`
Call `save_turn(session_id, "assistant", <prose reply>, [], blocks)`

Go back to Step 1.
"""


def install_skill(repo: Path, uninstall: bool):
    """Copy SKILL.md to interoperable user skill directories."""
    agent_skill_file = repo / ".agents" / "skills" / "smart-lms" / "SKILL.md"
    content = (
        agent_skill_file.read_text(encoding="utf-8")
        if agent_skill_file.exists()
        else SKILL_MD
    )

    targets = [
        ("Claude Code skill", HOME / ".claude" / "skills" / "smart-lms" / "SKILL.md"),
        ("Agent Skills user skill", HOME / ".agents" / "skills" / "smart-lms" / "SKILL.md"),
        ("Gemini CLI skill", HOME / ".gemini" / "skills" / "smart-lms" / "SKILL.md"),
        (
            "Antigravity CLI skill",
            HOME / ".gemini" / "antigravity-cli" / "skills" / "smart-lms" / "SKILL.md",
        ),
        ("Codex legacy skill", HOME / ".codex" / "skills" / "smart-lms" / "SKILL.md"),
    ]

    for label, dest in targets:
        if uninstall:
            if dest.exists():
                dest.unlink()
                print(f"  {green('ok')} {label} removed")
            else:
                print(f"  {dim('--')} {label} (not installed)")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"  {green('ok')} {label}")
            print(dim(f"    {dest}"))

    # Gemini CLI — append/remove skill block in ~/.gemini/GEMINI.md
    gemini_md = HOME / ".gemini" / "GEMINI.md"
    marker_start = "# [smart-lms skill]"
    marker_end   = "# [/smart-lms skill]"

    existing = gemini_md.read_text(encoding="utf-8") if gemini_md.exists() else ""
    if marker_start in existing and marker_end in existing:
        start = existing.index(marker_start)
        end = existing.index(marker_end) + len(marker_end)
        write_text(gemini_md, (existing[:start] + existing[end:]).strip() + "\n")
        print(f"  {green('ok')} removed old Gemini GEMINI.md skill block")


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
        result = handler(cfg_path, repo, args.uninstall)
        verb = {"registered": "ok", "removed": "ok", "not registered": "--"}[result]
        color = green if result in ("registered", "removed") else dim
        print(f"  {color(verb)} {name} MCP")
        print(dim(f"    {cfg_path}"))
        if result in ("registered", "removed"):
            registered.append(name)

    print()
    print(bold("  Skills:"))
    install_skill(repo, args.uninstall)

    print()
    if registered:
        print(bold(f"  {action} complete for: {', '.join(registered)}"))
    if skipped:
        print(dim(f"  Skipped (not installed): {', '.join(skipped)}"))

    if not args.uninstall:
        print()
        print(bold("  Next steps:"))
        print("  1. Reload / restart your AI coding tool")
        print("  2. Set your Moodle credentials (choose one):")
        print(dim("     python setup_credentials.py          ← terminal (recommended)"))
        print(dim("     or click ⚙ in the browser UI sidebar  ← after /smart-lms"))
        print("  3. Type  /smart-lms  to launch the study UI")
        print()


if __name__ == "__main__":
    main()
