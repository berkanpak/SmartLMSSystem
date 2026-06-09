# Smart LMS

An MCP server + skill that turns any AI coding tool into a personal study assistant for Işık University's Moodle LMS.

Type `/smart-lms` and get a browser chat UI that renders your course materials as **flashcards, quizzes, summaries, and mock exams** — grounded entirely in your own lecture notes and slides, never hallucinated.

---

## One-line install

```bash
curl -fsSL https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.sh | bash
```

Works on macOS, Linux, and Windows (Git Bash / WSL). Detects and registers the MCP server in every AI coding tool found on your machine:

| Tool | Config written |
|------|---------------|
| Claude Code | `~/.claude/settings.json` |
| Codex CLI (OpenAI) | `~/.codex/config.json` |
| Gemini CLI | `~/.gemini/settings.json` |
| Cursor | `~/.cursor/mcp.json` |
| Windsurf (Codeium) | `~/.codeium/windsurf/mcp_config.json` |
| Zed | `~/.config/zed/settings.json` |
| Continue | `~/.continue/config.json` |

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

1. Set your Moodle credentials once:
   ```
   call setup_lms_credentials("student@isik.edu.tr", "yourpassword")
   ```

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

The MCP server exposes 17 tools across five modules:

| Module | Tools |
|--------|-------|
| LMS | `setup_lms_credentials` `list_courses` `list_materials` `get_material_text` |
| Sessions | `create_session` `save_turn` `list_sessions` `load_session` |
| UI bridge | `start_ui` `wait_for_prompt` `render` |
| Google Drive | `connect_google_drive` `search_drive_files` `get_drive_file_text` |
| NotebookLM | `connect_notebooklm` `list_notebooks` `get_notebook_content` (stub — API in preview) |

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
