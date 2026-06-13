# Smart LMS

An MCP server + skill that turns any AI coding tool into a personal study assistant for Işık University's Moodle LMS.

Type `/smart-lms` and get a browser chat UI that renders your course materials as **flashcards, quizzes, summaries, and mock exams** — grounded entirely in your own lecture notes and slides, never hallucinated.

---

## One-line install

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.ps1 | iex
```

From `cmd.exe` or a locked-down PowerShell profile:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.ps1 | iex"
```

**macOS / Linux / Git Bash:**

```bash
curl -fsSL https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.sh | bash
```

Installs the MCP server **and** the `/smart-lms` skill in user/global locations for common AI coding tools:

| Tool                         | Config written                                                    |
| ---------------------------- | ----------------------------------------------------------------- |
| Claude Code                  | `~/.claude.json` + `~/.claude/skills/smart-lms/SKILL.md`          |
| Codex CLI (OpenAI)           | `~/.codex/config.toml` + `~/.agents/skills/smart-lms/SKILL.md`    |
| Gemini CLI / Antigravity CLI | `~/.gemini/settings.json` + `~/.agents/skills/smart-lms/SKILL.md` |
| Cursor                       | `~/.cursor/mcp.json`                                              |
| Windsurf (Codeium)           | `~/.codeium/windsurf/mcp_config.json`                             |
| Zed                          | `~/.config/zed/settings.json`                                     |
| Continue                     | `~/.continue/config.json`                                         |

Or if you already cloned the repo:

```bash
python install.py
```

To uninstall from all tools:

```bash
python install.py --uninstall
```

---

## Requirements

- Python 3.11+
- Git
- Moodle LMS credentials (stored in OS keychain — never on disk)

---

## First run

After installing, reload your AI coding tool and:

1. **Set your Moodle credentials** — choose either method:

   **Option A — Terminal (recommended):**
   ```bash
   python setup_credentials.py
   ```
   You'll be prompted for your username and password. The password input is hidden (not echoed) and is stored directly in the OS keychain — it never appears in any chat or log.

   **Option B — Browser UI:**
   Type `/smart-lms` to open the study UI, then click the **⚙ gear icon** in the bottom-left corner of the sidebar. Enter your credentials in the settings panel that appears.

   > **Security note:** Your password (typically your TC ID) is stored in the system keychain only. It is never sent to or seen by the AI.

2. Type `/smart-lms` to open the study UI in your browser.

3. Select courses at the bottom of the chat bar, then ask:
   - `teach me MATH1112 derivatives`
   - `quiz me on PHYS1101 kinematics`
   - `examine me for CS1102 finals`
   - `summarize Week 3 slides`

---

## How it works

```
/smart-lms  →  host agent (Claude / Codex / Gemini)
                    ↓ calls MCP tools
              smart_lms MCP server
                    ↓ serves
              browser UI (localhost:8742)
                    ↓ renders
              flashcards · quizzes · summaries · exams
```

The MCP server exposes 16 tools across five modules:

| Module       | Tools                                                                                |
| ------------ | ------------------------------------------------------------------------------------ |
| LMS          | `list_courses` `list_materials` `get_material_text`                                  |
| Sessions     | `create_session` `save_turn` `list_sessions` `load_session`                          |
| UI bridge    | `start_ui` `wait_for_prompt` `render`                                                |
| Google Drive | `connect_google_drive` `search_drive_files` `get_drive_file_text`                    |
| NotebookLM   | `connect_notebooklm` `list_notebooks` `get_notebook_content` (stub — API in preview) |

Credentials are managed outside the AI via `setup_credentials.py` (CLI) or the browser UI settings panel — not through a tool call.

The host agent is the reasoning brain — it calls tools to gather source text, generates card-block JSON, and pushes it to the browser via SSE. No AI runs inside the MCP server itself.

---

## Card block schema

```jsonc
// flashcard_set
{ "type": "flashcard_set", "heading": "...", "cards": [{ "tag": "Rule", "front": "...", "back": "..." }] }

// quiz
{ "type": "quiz", "heading": "...", "questions": [
    { "kind": "mcq", "text": "...", "options": ["A","B","C","D"], "correct": 1, "explanation": "..." },
    { "kind": "true_false", "text": "...", "correct": true, "explanation": "..." }
]}

// summary
{ "type": "summary", "heading": "...", "sections": [{ "title": "...", "body": "..." }] }

// exam
{ "type": "exam", "heading": "...", "duration_minutes": 60, "questions": [...], "answer_key": [{ "q": 1, "answer": "B" }] }
```

---

## Google Drive

Connect your Drive to pull in lecture notes, tutor PDFs, or shared resources:

```
call connect_google_drive()
```

This opens a browser OAuth flow. Your token is stored in `~/.smart-lms/google_token.json` — never in the repo.

You'll need a `google_client.json` OAuth credentials file from [Google Cloud Console](https://console.cloud.google.com/) placed at `~/.smart-lms/google_client.json`.

---

## Sessions

Every conversation is persisted at `~/.smart-lms/sessions/<uuid>.json`. The sidebar shows your recent sessions and lets you resume them.

---

## Development

```bash
git clone https://github.com/berkanpak/SmartLMSSystem.git
cd SmartLMSSystem
pip install -r requirements.txt
python -m pytest tests/ -v
```

```
smart_lms/
  server.py          # FastMCP entry point
  config.py          # ~/.smart-lms/ setup, keyring helpers
  tools/
    lms.py           # Moodle REST scraping
    documents.py     # PDF + PPTX text extraction
    sessions.py      # Session persistence
    ui_bridge.py     # FastAPI SSE bridge + MCP tools
    drive.py         # Google Drive OAuth
    notebooklm.py    # NotebookLM stubs
  ui/
    index.html       # Chat shell
    app.js           # Card renderer, SSE, API calls
    styles.css       # Clay theme, Phosphor Icons
    icons/           # Phosphor Icons (local, no CDN)
```

---

## License

MIT — see [LICENSE](LICENSE).
