# Smart LMS — Agent Skill + MCP Design Spec
**Date:** 2026-06-09  
**Status:** Approved for implementation planning

---

## 1. Problem Statement

The existing SmartLMSSystem is a Streamlit app that calls Gemini directly. It needs to be re-architected so that:

- A CLI agent (Claude Code, or any MCP-capable agent) is the reasoning brain
- The Moodle LMS scraper and document parsing code are reused as MCP tools
- A browser-based chat UI replaces Streamlit, with source selection (courses, documents, Google Drive, NotebookLM) and structured card output (flashcards, quizzes, summaries, mock exams)
- A global `~/.smart-lms/` folder persists all sessions

The system is launched with a single slash command: `/smart-lms`.

---

## 2. Architecture Overview

```
User types /smart-lms
       |
  Host Agent (Claude Code / any MCP agent)
  loads the Skill → runs orchestration loop
       |
  MCP Server (Python, FastMCP) — three roles:
  +---------+----------+-------------+
  | LMS     | UI       | Session     |
  | tools   | bridge   | storage     |
  +---------+----------+-------------+
       |          |
  Moodle     Local web server
  REST API   serves browser UI
             + SSE push to UI
             + wait_for_prompt (long-poll)
       |
  Browser UI (static HTML/CSS/JS)
  - Left sidebar: recent sessions
  - Center: chat thread (user right / agent left)
  - Bottom: prompt bar with course/doc/connect pickers
  - Card renderer: flashcards, quiz cards, summaries, exam
```

**Flow per turn:**
1. Agent calls `wait_for_prompt` (blocks until user submits in browser; returns text + selected course IDs + doc IDs)
2. Agent calls `get_material_text(course_ids, doc_ids)` to pull and parse relevant sources
3. (Optional) Agent calls `get_drive_files(query)` or `get_notebooklm_content(notebook_id)` for extra sources
4. Agent generates card-block JSON using the schema defined in Section 5
5. Agent calls `render(session_id, blocks)` — server pushes blocks to browser via SSE
6. Agent calls `save_turn(session_id, user_text, sources, blocks)` to persist
7. Back to step 1

---

## 3. The Skill (`/smart-lms`)

**Location:** `~/.claude/skills/smart-lms/SKILL.md`

**Responsibilities:**
- Boot: call `start_ui` (launches local web server on a free port, opens browser, returns session_id)
- Run the turn loop described above
- Interpret user intent:
  - "teach me X" → generate flashcards + summary
  - "quiz me / examine me for X" → generate quiz cards + mock exam
  - "summarize X" → generate summary only
  - Free chat → answer in prose (no card blocks required)
- Emit card-block JSON strictly per the schema (Section 5)
- Store credentials lookup key in skill instructions (actual secrets live in OS keychain)

**Tool order for source gathering:**
1. LMS tools (primary — always available if credentials set)
2. Google Drive tools (if user has connected)
3. NotebookLM tools (if user has connected and API is available)

---

## 4. The MCP Server

**Language:** Python 3.11+  
**Framework:** FastMCP  
**File structure:**
```
mcp/
  server.py            # FastMCP app, registers all tools
  tools/
    lms.py             # Moodle REST API tools (reuse lms_scraper.py)
    documents.py       # PDF/PPTX parsing (reuse document_parser.py)
    drive.py           # Google Drive API tools
    notebooklm.py      # NotebookLM API tools (stretch, see Section 4.4)
    ui_bridge.py       # start_ui, wait_for_prompt, render
    sessions.py        # save_turn, list_sessions, load_session
  ui/
    index.html         # The browser UI (productionized mockup)
    app.js
    styles.css
  config.py            # keyring reads, port selection
```

### 4.1 LMS Tools

Wraps the existing `lms_scraper.py` logic. Credentials read from OS keychain via `keyring.get_password("smart-lms-moodle", username)`.

| Tool | Parameters | Returns |
|------|-----------|---------|
| `setup_lms_credentials(username, password)` | str, str | success bool (stores in keychain) |
| `list_courses()` | — | `[{id, name, shortname}]` |
| `list_materials(course_id)` | int | `[{id, title, type, section}]` |
| `get_material_text(course_id, material_ids)` | int, list[int] | `[{title, text}]` (parsed text from PDF/PPTX) |

### 4.2 Google Drive Tools

Uses OAuth2 via `google-auth-oauthlib`. Credentials stored in `~/.smart-lms/google_token.json`.

| Tool | Parameters | Returns |
|------|-----------|---------|
| `connect_google_drive()` | — | OAuth URL for user to open (or auto-opens) |
| `search_drive_files(query)` | str | `[{id, name, mimeType}]` |
| `get_drive_file_text(file_id)` | str | extracted text string |

### 4.3 UI Bridge Tools

The MCP server runs a local HTTP + SSE server (FastAPI, port auto-selected). The browser connects to it.

| Tool | Parameters | Returns |
|------|-----------|---------|
| `start_ui(session_id?)` | optional str | `{session_id, url, port}` — also opens browser |
| `wait_for_prompt(session_id)` | str | `{text, course_ids, doc_ids, drive_files}` — blocks until user submits |
| `render(session_id, blocks)` | str, list | pushes card blocks to browser via SSE, returns ok |

### 4.4 NotebookLM Tools (stretch — v1.x)

**Investigation path:** Google provides a NotebookLM API (`notebooklm.googleapis.com`) currently in limited preview. Also: the Gemini API can access Google Workspace content which may include Notebook sources. We will:
1. Investigate `notebooklm.googleapis.com` API availability
2. Fall back to Gemini API with appropriate Google Workspace scope if available
3. If neither is accessible without a preview program, implement via Playwright automation as last resort

The UI "Connect NotebookLM" button shows "coming soon" in v1.0 but the tool scaffolding is stubbed.

| Tool | Parameters | Returns |
|------|-----------|---------|
| `connect_notebooklm()` | — | auth URL or status |
| `list_notebooks()` | — | `[{id, title}]` |
| `get_notebook_content(notebook_id)` | str | extracted text |

### 4.5 Session Storage Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `save_turn(session_id, user_text, sources, blocks)` | ... | ok |
| `list_sessions()` | — | `[{id, title, course_name, timestamp, turn_count}]` |
| `load_session(session_id)` | str | full session JSON |

**Storage format:** `~/.smart-lms/sessions/<session_id>.json`

```json
{
  "id": "uuid",
  "title": "MATH1112 — Derivatives",
  "course": "MATH1112",
  "created_at": "2026-06-09T14:00:00Z",
  "turns": [
    {
      "role": "user",
      "text": "Teach me MATH1112 Derivatives",
      "sources": ["course:1234", "doc:45", "doc:46"]
    },
    {
      "role": "assistant",
      "text": "Here's a focused walkthrough...",
      "blocks": [...]
    }
  ]
}
```

---

## 5. Card Block Schema

The agent emits a JSON array of blocks. The UI renders each block by type.

```json
[
  {
    "type": "flashcard_set",
    "heading": "Flashcards · Derivatives",
    "cards": [
      { "tag": "Definition", "front": "What is f′(x)?", "back": "The instantaneous rate of change..." }
    ]
  },
  {
    "type": "quiz",
    "heading": "Quiz yourself · 1 of 3",
    "questions": [
      {
        "kind": "mcq",
        "text": "What is the derivative of f(x) = 3x² + 5x − 7?",
        "options": ["6x + 5x", "6x + 5", "3x + 5", "6x + 5x − 7"],
        "correct": 1,
        "explanation": "Apply power rule term by term..."
      },
      {
        "kind": "true_false",
        "text": "The derivative of a constant is 0.",
        "correct": true,
        "explanation": "Constants have no rate of change."
      }
    ]
  },
  {
    "type": "summary",
    "heading": "Key Concepts",
    "sections": [
      { "title": "Power Rule", "body": "d/dx[xⁿ] = nxⁿ⁻¹" },
      { "title": "Product Rule", "body": "(fg)′ = f′g + fg′" }
    ]
  },
  {
    "type": "exam",
    "heading": "MATH1112 Finals — Mock Exam",
    "duration_minutes": 60,
    "questions": [...],
    "answer_key": [...]
  }
]
```

---

## 6. The Browser UI

Productionized version of the mockup at `mockups/smart-lms-mockup.html`.

**Key behaviors:**
- Source pills shown under each user message (what was used)
- User message: right-aligned bubble
- Agent text: left-aligned prose, then full-width card blocks below it
- Flashcard flip: CSS 3D transform on click
- Quiz answer: click option → grades immediately (correct green / wrong red + explanation reveal)
- Sidebar "Recent" list: loaded from `list_sessions()` on UI boot
- Courses picker popover: loaded from `list_courses()` on UI boot
- Documents picker: loads `list_materials(course_id)` when a course is selected
- Connect buttons: Google Drive (OAuth popup) + NotebookLM (coming soon in v1)

**Icon library:** Phosphor Icons installed as local package (no CDN).  
**No framework:** vanilla HTML/CSS/JS only (the MCP server serves static files — no npm build needed).

---

## 7. Global Folder Layout

```
~/.smart-lms/
  config.json              # LMS base URL, port preference, connected sources flags
  google_token.json        # Google OAuth token (gitignored)
  sessions/
    <uuid>.json            # One file per study session
```

Credentials (LMS password, API keys) are **never** written to disk — stored in the OS keychain only (Windows Credential Manager via `keyring`).

---

## 8. Dependencies

| Package | Purpose |
|---------|---------|
| `fastmcp` | MCP server framework |
| `fastapi` + `uvicorn` | HTTP + SSE server for UI bridge |
| `keyring` | OS keychain for LMS credentials |
| `requests` | Moodle REST API calls (existing) |
| `pymupdf` | PDF text extraction (existing) |
| `python-pptx` | PPTX text extraction (existing) |
| `google-auth-oauthlib` | Google Drive OAuth |
| `google-api-python-client` | Drive API |
| `python-dotenv` | Fallback .env for non-keychain envs |

---

## 9. Implementation Strategy

Code is written by **Haiku subagents** — each given a specific, bounded task with clear input/output contracts. The orchestrating agent (Opus/Sonnet) reviews results before proceeding to the next task.

**Phase 1 — MCP Core**
- Haiku Agent A: migrate `lms_scraper.py` into `mcp/tools/lms.py` as FastMCP tools with keyring credential lookup
- Haiku Agent B: migrate `document_parser.py` into `mcp/tools/documents.py`
- Haiku Agent C: build `mcp/tools/sessions.py` (save/load/list from `~/.smart-lms/sessions/`)
- Haiku Agent D: build `mcp/server.py` wiring FastMCP + register all tools

**Phase 2 — UI Bridge**
- Haiku Agent E: build `mcp/tools/ui_bridge.py` — `start_ui`, SSE push endpoint, `wait_for_prompt` long-poll
- Haiku Agent F: productionize `mcp/ui/index.html` from mockup (local Phosphor, card renderer, SSE listener)

**Phase 3 — Integrations**
- Haiku Agent G: build `mcp/tools/drive.py` (Google Drive OAuth + search + read)
- Haiku Agent H: stub `mcp/tools/notebooklm.py` + investigate NotebookLM API availability

**Phase 4 — Skill**
- Write `~/.claude/skills/smart-lms/SKILL.md` (orchestration instructions for the host agent)

---

## 10. Out of Scope for v1

- Mobile / responsive UI (desktop-first)
- Multi-user / shared sessions
- NotebookLM (stub only — see Section 4.4)
- Non-Moodle LMS platforms
- Offline mode (requires internet for LMS + Drive)
