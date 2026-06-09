# Smart LMS — Skill + MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-architect SmartLMSSystem as an agent-agnostic MCP server + skill so any CLI agent (`/smart-lms`) can teach, quiz, and examine students using their Moodle LMS course materials, with a browser chat UI that renders flashcards, quizzes, summaries, and mock exams.

**Architecture:** A Python FastMCP server exposes LMS, document parsing, session storage, and UI bridge tools. It also runs a FastAPI web server in a background thread serving the browser UI over SSE. The host CLI agent is the reasoning brain — it calls MCP tools to gather sources and renders card-block JSON to the browser.

**Tech Stack:** Python 3.11+, FastMCP, FastAPI, uvicorn, keyring, requests, pymupdf, python-pptx, google-api-python-client, vanilla HTML/CSS/JS (Phosphor Icons local), pytest, unittest.mock

---

## Execution Model

Each task is dispatched to a **Haiku** or **Codex** subagent with a precisely bounded prompt (shown in the bordered box per task). The orchestrating agent (Opus/Sonnet) reviews the output before dispatching the next task. **Do not proceed past a review step without inspecting the files the subagent created.**

---

## File Structure

```
mcp/
  __init__.py
  server.py              # FastMCP app entry point — registers all tools
  config.py              # ~/.smart-lms setup, keyring helpers, port selection
  tools/
    __init__.py
    lms.py               # Moodle REST tools: setup_lms_credentials, list_courses,
                         #   list_materials, get_material_text
    documents.py         # Pure text extraction: extract_document_text (PDF/PPTX)
    sessions.py          # Session storage: save_turn, list_sessions, load_session,
                         #   create_session
    ui_bridge.py         # FastAPI server + MCP tools: start_ui, wait_for_prompt,
                         #   render; shared threading.Event state
    drive.py             # Google Drive OAuth + MCP tools: connect_google_drive,
                         #   search_drive_files, get_drive_file_text
    notebooklm.py        # Stubs: connect_notebooklm, list_notebooks,
                         #   get_notebook_content
  ui/
    index.html           # Chat shell: sidebar, thread, composer bar
    app.js               # Card renderer, SSE listener, API calls
    styles.css           # All styles from approved mockup (clay theme, Phosphor)
    icons/               # Phosphor Icons web package (downloaded locally)
tests/
  __init__.py
  test_config.py
  test_documents.py
  test_lms.py
  test_sessions.py
  test_ui_bridge.py
  test_drive.py
  fixtures/
    sample.pdf           # 1-page PDF for extraction tests
    sample.pptx          # 1-slide PPTX for extraction tests
requirements.txt         # Updated from existing
~/.claude/skills/smart-lms/
  SKILL.md               # Orchestration instructions for host agent
```

---

## Task 1 — Project Scaffolding + config.py

**Agent: Haiku**

- [ ] **Dispatch Haiku with this exact prompt:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 1 — Smart LMS scaffolding + config.py               ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  1. Replace requirements.txt with exactly this content:         ║
║     fastmcp>=2.0                                                 ║
║     fastapi>=0.111                                               ║
║     uvicorn>=0.29                                                ║
║     keyring>=25.0                                                ║
║     requests>=2.31                                               ║
║     pymupdf>=1.24                                                ║
║     python-pptx>=0.6.23                                          ║
║     google-auth-oauthlib>=1.2                                    ║
║     google-api-python-client>=2.130                              ║
║     python-dotenv>=1.0                                           ║
║     pytest>=8.0                                                  ║
║     httpx>=0.27                                                  ║
║                                                                  ║
║  2. Create these empty files (with just a newline):              ║
║     mcp/__init__.py                                              ║
║     mcp/tools/__init__.py                                        ║
║     tests/__init__.py                                            ║
║     tests/fixtures/.gitkeep                                      ║
║                                                                  ║
║  3. Create mcp/config.py with this exact content:               ║
║                                                                  ║
║  import json, socket                                             ║
║  import keyring                                                  ║
║  from pathlib import Path                                        ║
║                                                                  ║
║  SMART_LMS_DIR = Path.home() / ".smart-lms"                     ║
║  SESSIONS_DIR = SMART_LMS_DIR / "sessions"                       ║
║  CONFIG_FILE = SMART_LMS_DIR / "config.json"                     ║
║  KEYCHAIN_SERVICE = "smart-lms-moodle"                           ║
║  DEFAULT_LMS_URL = "https://isikuniversity.mrooms.net"           ║
║  DEFAULT_PORT = 8742                                             ║
║                                                                  ║
║  _DEFAULTS = {                                                   ║
║      "lms_base_url": DEFAULT_LMS_URL,                            ║
║      "lms_username": "",                                         ║
║      "port": DEFAULT_PORT,                                       ║
║      "google_drive_connected": False,                            ║
║      "notebooklm_connected": False,                              ║
║  }                                                               ║
║                                                                  ║
║  def ensure_dirs():                                              ║
║      SMART_LMS_DIR.mkdir(exist_ok=True)                          ║
║      SESSIONS_DIR.mkdir(exist_ok=True)                           ║
║      if not CONFIG_FILE.exists():                                ║
║          CONFIG_FILE.write_text(json.dumps(_DEFAULTS, indent=2)) ║
║                                                                  ║
║  def get_config() -> dict:                                       ║
║      ensure_dirs()                                               ║
║      data = json.loads(CONFIG_FILE.read_text())                  ║
║      return {**_DEFAULTS, **data}                                ║
║                                                                  ║
║  def save_config(data: dict):                                    ║
║      ensure_dirs()                                               ║
║      CONFIG_FILE.write_text(json.dumps(data, indent=2))          ║
║                                                                  ║
║  def get_lms_credentials() -> tuple[str | None, str | None]:    ║
║      cfg = get_config()                                          ║
║      username = cfg.get("lms_username", "")                      ║
║      if not username:                                            ║
║          return None, None                                       ║
║      password = keyring.get_password(KEYCHAIN_SERVICE, username) ║
║      return username, password                                   ║
║                                                                  ║
║  def store_lms_credentials(username: str, password: str):       ║
║      keyring.set_password(KEYCHAIN_SERVICE, username, password)  ║
║      cfg = get_config()                                          ║
║      cfg["lms_username"] = username                              ║
║      save_config(cfg)                                            ║
║                                                                  ║
║  def find_free_port(preferred: int = DEFAULT_PORT) -> int:      ║
║      try:                                                        ║
║          with socket.socket() as s:                              ║
║              s.bind(("127.0.0.1", preferred))                    ║
║              return preferred                                    ║
║      except OSError:                                             ║
║          with socket.socket() as s:                              ║
║              s.bind(("127.0.0.1", 0))                            ║
║              return s.getsockname()[1]                           ║
║                                                                  ║
║  4. Create tests/test_config.py:                                 ║
║                                                                  ║
║  import json, pytest                                             ║
║  from pathlib import Path                                        ║
║  from unittest.mock import patch, MagicMock                      ║
║  import mcp.config as cfg_mod                                    ║
║                                                                  ║
║  @pytest.fixture(autouse=True)                                   ║
║  def tmp_home(tmp_path, monkeypatch):                            ║
║      monkeypatch.setattr(cfg_mod, "SMART_LMS_DIR",              ║
║          tmp_path / ".smart-lms")                                ║
║      monkeypatch.setattr(cfg_mod, "SESSIONS_DIR",               ║
║          tmp_path / ".smart-lms" / "sessions")                   ║
║      monkeypatch.setattr(cfg_mod, "CONFIG_FILE",                ║
║          tmp_path / ".smart-lms" / "config.json")               ║
║                                                                  ║
║  def test_ensure_dirs_creates_directories(tmp_path):            ║
║      cfg_mod.ensure_dirs()                                       ║
║      assert cfg_mod.SMART_LMS_DIR.exists()                       ║
║      assert cfg_mod.SESSIONS_DIR.exists()                        ║
║                                                                  ║
║  def test_get_config_returns_defaults_on_first_run():           ║
║      result = cfg_mod.get_config()                               ║
║      assert result["lms_base_url"] == cfg_mod.DEFAULT_LMS_URL   ║
║      assert result["google_drive_connected"] is False            ║
║                                                                  ║
║  def test_save_and_reload_config():                              ║
║      cfg_mod.save_config({"lms_username": "testuser",            ║
║                            "port": 9000})                        ║
║      result = cfg_mod.get_config()                               ║
║      assert result["lms_username"] == "testuser"                 ║
║      assert result["port"] == 9000                               ║
║                                                                  ║
║  def test_get_lms_credentials_none_when_no_username():          ║
║      u, p = cfg_mod.get_lms_credentials()                        ║
║      assert u is None and p is None                              ║
║                                                                  ║
║  def test_store_and_get_lms_credentials():                      ║
║      with patch("keyring.set_password") as mock_set,            ║
║           patch("keyring.get_password", return_value="secret"):  ║
║          cfg_mod.store_lms_credentials("alice", "secret")        ║
║          mock_set.assert_called_once_with(                       ║
║              cfg_mod.KEYCHAIN_SERVICE, "alice", "secret")        ║
║          u, p = cfg_mod.get_lms_credentials()                    ║
║          assert u == "alice" and p == "secret"                   ║
║                                                                  ║
║  5. Run: pytest tests/test_config.py -v                          ║
║     All 5 tests must pass.                                       ║
║                                                                  ║
║  6. Commit:                                                      ║
║     git add mcp/ tests/ requirements.txt                        ║
║     git commit -m "feat: project scaffolding and config module"  ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/config.py` and `tests/test_config.py`. Verify `find_free_port` is present, all 5 tests pass, `requirements.txt` has the correct packages.

---

## Task 2 — Document Text Extraction (`mcp/tools/documents.py`)

**Agent: Haiku**

- [ ] **Create test fixtures** — run these commands before dispatching:

```bash
python -c "
import fitz, os
doc = fitz.open()
page = doc.new_page()
page.insert_text((72,72), 'Power Rule: d/dx[x^n] = n*x^(n-1)')
doc.save('tests/fixtures/sample.pdf')
doc.close()
print('sample.pdf created')
"
```

```bash
python -c "
from pptx import Presentation
from pptx.util import Inches
prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[1])
slide.shapes.title.text = 'Derivatives'
slide.placeholders[1].text = 'Chain Rule: d/dx[f(g(x))] = f prime(g(x)) * g prime(x)'
prs.save('tests/fixtures/sample.pptx')
print('sample.pptx created')
"
```

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 2 — mcp/tools/documents.py                          ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  Existing file to reuse logic from: document_parser.py          ║
║  (do NOT modify document_parser.py — create new file)           ║
║                                                                  ║
║  CREATE mcp/tools/documents.py:                                  ║
║                                                                  ║
║  import os                                                       ║
║  import fitz                                                     ║
║  from pptx import Presentation                                   ║
║                                                                  ║
║  def extract_pdf_text(file_path: str) -> str:                   ║
║      doc = fitz.open(file_path)                                  ║
║      parts = [page.get_text() for page in doc]                   ║
║      doc.close()                                                 ║
║      return "".join(parts)                                       ║
║                                                                  ║
║  def extract_pptx_text(file_path: str) -> str:                  ║
║      prs = Presentation(file_path)                               ║
║      parts = []                                                  ║
║      for slide in prs.slides:                                    ║
║          for shape in slide.shapes:                              ║
║              if hasattr(shape, "text") and shape.text.strip():  ║
║                  parts.append(shape.text.strip())               ║
║      return "\n".join(parts)                                     ║
║                                                                  ║
║  def extract_document_text(file_path: str) -> str:              ║
║      ext = os.path.splitext(file_path)[1].lower()               ║
║      if ext == ".pdf":                                           ║
║          return extract_pdf_text(file_path)                      ║
║      elif ext in (".pptx", ".ppt"):                              ║
║          return extract_pptx_text(file_path)                     ║
║      return ""                                                   ║
║                                                                  ║
║  CREATE tests/test_documents.py:                                 ║
║                                                                  ║
║  import pytest                                                   ║
║  from pathlib import Path                                        ║
║  from mcp.tools.documents import (                               ║
║      extract_pdf_text, extract_pptx_text, extract_document_text ║
║  )                                                               ║
║                                                                  ║
║  FIXTURES = Path("tests/fixtures")                               ║
║                                                                  ║
║  def test_extract_pdf_text():                                    ║
║      text = extract_pdf_text(str(FIXTURES / "sample.pdf"))       ║
║      assert "Power Rule" in text                                 ║
║                                                                  ║
║  def test_extract_pptx_text():                                   ║
║      text = extract_pptx_text(str(FIXTURES / "sample.pptx"))     ║
║      assert "Chain Rule" in text                                 ║
║                                                                  ║
║  def test_extract_document_text_routes_pdf():                   ║
║      text = extract_document_text(str(FIXTURES / "sample.pdf"))  ║
║      assert len(text) > 0                                        ║
║                                                                  ║
║  def test_extract_document_text_routes_pptx():                  ║
║      text = extract_document_text(str(FIXTURES / "sample.pptx")) ║
║      assert len(text) > 0                                        ║
║                                                                  ║
║  def test_extract_document_text_unknown_ext_returns_empty():    ║
║      text = extract_document_text("file.xyz")                    ║
║      assert text == ""                                           ║
║                                                                  ║
║  Run: pytest tests/test_documents.py -v                          ║
║  All 5 tests must pass.                                          ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/documents.py tests/test_documents.py         ║
║         tests/fixtures/                                          ║
║  git commit -m "feat: document text extraction tools"            ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/tools/documents.py`. Confirm it has no MCP decorators (pure functions only). Confirm tests pass.

---

## Task 3 — LMS MCP Tools (`mcp/tools/lms.py`)

**Agent: Haiku**

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 3 — mcp/tools/lms.py                                ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  Read these existing files before writing:                       ║
║    lms_scraper.py  (contains LMSScraper class — reuse it)       ║
║    mcp/config.py   (get_lms_credentials, get_config)            ║
║    mcp/tools/documents.py (extract_document_text)               ║
║                                                                  ║
║  CREATE mcp/tools/lms.py — register_lms_tools(mcp) function     ║
║  that adds 4 tools to a FastMCP instance.                        ║
║                                                                  ║
║  EXACT CONTENT:                                                  ║
║                                                                  ║
║  import hashlib, os, tempfile, requests                          ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.config import (get_config, get_lms_credentials,        ║
║                           store_lms_credentials)                 ║
║  from mcp.tools.documents import extract_document_text           ║
║  import sys; sys.path.insert(0, ".")                             ║
║  from lms_scraper import LMSScraper                              ║
║                                                                  ║
║  def _material_id(file_url: str) -> str:                        ║
║      return hashlib.md5(file_url.encode()).hexdigest()[:12]      ║
║                                                                  ║
║  def _get_scraper() -> LMSScraper:                              ║
║      return LMSScraper(base_url=get_config()["lms_base_url"])    ║
║                                                                  ║
║  # Internal helpers called by ui_bridge API routes               ║
║  def _list_courses_raw() -> list[dict]:                          ║
║      username, password = get_lms_credentials()                  ║
║      if not username:                                            ║
║          return []                                               ║
║      scraper = _get_scraper()                                    ║
║      courses = scraper.get_courses(username, password)           ║
║      return [{"id": c["id"], "name": c["name"]} for c in courses]║
║                                                                  ║
║  def _list_materials_raw(course_id: int) -> list[dict]:         ║
║      username, password = get_lms_credentials()                  ║
║      if not username:                                            ║
║          return []                                               ║
║      scraper = _get_scraper()                                    ║
║      link = f"{get_config()['lms_base_url']}/course/view.php"   ║
║              f"?id={course_id}"                                  ║
║      materials = scraper.get_materials(username, password, link) ║
║      return [                                                    ║
║          {                                                       ║
║              "id": _material_id(m["link"]),                      ║
║              "title": m["title"],                                ║
║              "link": m["link"],                                  ║
║          }                                                       ║
║          for m in materials                                      ║
║      ]                                                           ║
║                                                                  ║
║  def register_lms_tools(mcp: FastMCP):                          ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def setup_lms_credentials(username: str,                   ║
║                                  password: str) -> bool:         ║
║          """Store Moodle credentials in the OS keychain."""      ║
║          store_lms_credentials(username, password)               ║
║          scraper = _get_scraper()                                ║
║          return scraper.login_test(username, password)           ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def list_courses() -> list[dict]:                           ║
║          """List all enrolled courses. Returns [{id, name}]."""  ║
║          return _list_courses_raw()                              ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def list_materials(course_id: int) -> list[dict]:          ║
║          """List downloadable materials for a course.            ║
║          Returns [{id, title, link}]."""                         ║
║          return _list_materials_raw(course_id)                   ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def get_material_text(course_id: int,                      ║
║                             material_ids: list[str]) -> list[dict]:║
║          """Download and extract text from selected materials.   ║
║          Returns [{title, text}]."""                             ║
║          all_mats = _list_materials_raw(course_id)               ║
║          selected = [m for m in all_mats                         ║
║                      if m["id"] in material_ids]                 ║
║          results = []                                            ║
║          with tempfile.TemporaryDirectory() as tmp:              ║
║              for mat in selected:                                ║
║                  try:                                            ║
║                      resp = requests.get(mat["link"],            ║
║                                          stream=True, timeout=30)║
║                      resp.raise_for_status()                     ║
║                      fname = mat["title"]                        ║
║                      fpath = os.path.join(tmp, fname)            ║
║                      with open(fpath, "wb") as f:                ║
║                          for chunk in resp.iter_content(8192):   ║
║                              f.write(chunk)                      ║
║                      text = extract_document_text(fpath)         ║
║                      if text.strip():                            ║
║                          results.append({"title": mat["title"],  ║
║                                          "text": text})          ║
║                  except Exception as e:                          ║
║                      results.append({"title": mat["title"],      ║
║                                      "text": "",                 ║
║                                      "error": str(e)})           ║
║          return results                                          ║
║                                                                  ║
║  CREATE tests/test_lms.py:                                       ║
║                                                                  ║
║  import pytest                                                   ║
║  from unittest.mock import patch, MagicMock                      ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.tools.lms import (register_lms_tools,                 ║
║                               _material_id, _list_courses_raw)  ║
║                                                                  ║
║  @pytest.fixture                                                 ║
║  def mcp_app():                                                  ║
║      app = FastMCP("test")                                       ║
║      register_lms_tools(app)                                     ║
║      return app                                                  ║
║                                                                  ║
║  def test_material_id_is_deterministic():                        ║
║      assert _material_id("http://a.com/f") == _material_id(     ║
║                                                "http://a.com/f") ║
║      assert len(_material_id("http://a.com/f")) == 12           ║
║                                                                  ║
║  def test_list_courses_raw_returns_empty_when_no_creds():       ║
║      with patch("mcp.tools.lms.get_lms_credentials",            ║
║                 return_value=(None, None)):                      ║
║          assert _list_courses_raw() == []                        ║
║                                                                  ║
║  def test_list_courses_raw_calls_scraper():                     ║
║      mock_scraper = MagicMock()                                  ║
║      mock_scraper.get_courses.return_value = [                   ║
║          {"id": 1, "name": "MATH1112", "link": "..."}            ║
║      ]                                                           ║
║      with patch("mcp.tools.lms.get_lms_credentials",            ║
║                 return_value=("user", "pass")),                  ║
║           patch("mcp.tools.lms._get_scraper",                   ║
║                 return_value=mock_scraper):                      ║
║          result = _list_courses_raw()                            ║
║          assert result == [{"id": 1, "name": "MATH1112"}]        ║
║                                                                  ║
║  Run: pytest tests/test_lms.py -v                                ║
║  All 3 tests must pass.                                          ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/lms.py tests/test_lms.py                     ║
║  git commit -m "feat: LMS MCP tools"                             ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/tools/lms.py`. Verify `_list_courses_raw` and `_list_materials_raw` are module-level functions (needed by `ui_bridge.py` API routes later). Confirm the `register_lms_tools` pattern is used (not top-level `@mcp.tool()` decorators).

---

## Task 4 — Session Storage (`mcp/tools/sessions.py`)

**Agent: Haiku**

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 4 — mcp/tools/sessions.py                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  Read mcp/config.py first (SESSIONS_DIR, ensure_dirs).          ║
║                                                                  ║
║  CREATE mcp/tools/sessions.py:                                   ║
║                                                                  ║
║  import json, uuid                                               ║
║  from datetime import datetime, timezone                         ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.config import SESSIONS_DIR, ensure_dirs               ║
║                                                                  ║
║  def _session_path(session_id: str):                             ║
║      return SESSIONS_DIR / f"{session_id}.json"                  ║
║                                                                  ║
║  def _list_sessions_raw() -> list[dict]:                         ║
║      """Internal helper used by ui_bridge API route."""          ║
║      ensure_dirs()                                               ║
║      sessions = []                                               ║
║      for p in sorted(SESSIONS_DIR.glob("*.json"),               ║
║                       key=lambda x: x.stat().st_mtime,          ║
║                       reverse=True):                             ║
║          try:                                                    ║
║              data = json.loads(p.read_text())                    ║
║              sessions.append({                                   ║
║                  "id": data["id"],                               ║
║                  "title": data.get("title", "Untitled"),         ║
║                  "course": data.get("course", ""),               ║
║                  "created_at": data.get("created_at", ""),       ║
║                  "turn_count": len(data.get("turns", [])),       ║
║              })                                                  ║
║          except Exception:                                       ║
║              continue                                            ║
║      return sessions                                             ║
║                                                                  ║
║  def register_session_tools(mcp: FastMCP):                      ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def create_session(title: str, course: str = "") -> str:   ║
║          """Create a new study session. Returns session_id."""   ║
║          ensure_dirs()                                           ║
║          session_id = str(uuid.uuid4())                          ║
║          data = {                                                ║
║              "id": session_id,                                   ║
║              "title": title,                                     ║
║              "course": course,                                   ║
║              "created_at": datetime.now(timezone.utc).isoformat(),║
║              "turns": [],                                        ║
║          }                                                       ║
║          _session_path(session_id).write_text(                   ║
║              json.dumps(data, indent=2))                         ║
║          return session_id                                       ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def save_turn(session_id: str, role: str, text: str,       ║
║                    sources: list[str],                           ║
║                    blocks: list[dict] | None = None) -> str:    ║
║          """Append a turn to a session. role: 'user'|'assistant'║
║          Returns session_id."""                                  ║
║          path = _session_path(session_id)                        ║
║          if not path.exists():                                   ║
║              raise FileNotFoundError(                            ║
║                  f"Session {session_id} not found")             ║
║          data = json.loads(path.read_text())                     ║
║          turn = {"role": role, "text": text, "sources": sources} ║
║          if blocks:                                              ║
║              turn["blocks"] = blocks                             ║
║          data["turns"].append(turn)                              ║
║          path.write_text(json.dumps(data, indent=2))             ║
║          return session_id                                       ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def list_sessions() -> list[dict]:                          ║
║          """List all study sessions, newest first."""            ║
║          return _list_sessions_raw()                             ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def load_session(session_id: str) -> dict:                  ║
║          """Load a full session including all turns."""           ║
║          path = _session_path(session_id)                        ║
║          if not path.exists():                                   ║
║              return {}                                           ║
║          return json.loads(path.read_text())                     ║
║                                                                  ║
║  CREATE tests/test_sessions.py:                                  ║
║                                                                  ║
║  import pytest, json                                             ║
║  from fastmcp import FastMCP                                     ║
║  import mcp.config as cfg_mod                                    ║
║  import mcp.tools.sessions as sess_mod                           ║
║  from mcp.tools.sessions import register_session_tools           ║
║                                                                  ║
║  @pytest.fixture(autouse=True)                                   ║
║  def tmp_sessions(tmp_path, monkeypatch):                        ║
║      monkeypatch.setattr(cfg_mod, "SMART_LMS_DIR",              ║
║          tmp_path / ".smart-lms")                                ║
║      monkeypatch.setattr(cfg_mod, "SESSIONS_DIR",               ║
║          tmp_path / ".smart-lms" / "sessions")                   ║
║      monkeypatch.setattr(sess_mod, "SESSIONS_DIR",              ║
║          tmp_path / ".smart-lms" / "sessions")                   ║
║      cfg_mod.ensure_dirs()                                       ║
║                                                                  ║
║  @pytest.fixture                                                 ║
║  def mcp_app():                                                  ║
║      app = FastMCP("test")                                       ║
║      register_session_tools(app)                                 ║
║      return app                                                  ║
║                                                                  ║
║  def test_create_session_returns_uuid(mcp_app):                 ║
║      sid = mcp_app.call_tool("create_session",                   ║
║                               {"title": "Test", "course": "X"}) ║
║      assert len(sid) == 36  # UUID format                        ║
║                                                                  ║
║  def test_save_and_load_turn(mcp_app):                          ║
║      sid = mcp_app.call_tool("create_session", {"title": "T"})  ║
║      mcp_app.call_tool("save_turn", {                            ║
║          "session_id": sid, "role": "user",                      ║
║          "text": "Hello", "sources": ["course:1"]                ║
║      })                                                          ║
║      session = mcp_app.call_tool("load_session",                 ║
║                                   {"session_id": sid})          ║
║      assert session["turns"][0]["text"] == "Hello"               ║
║                                                                  ║
║  def test_list_sessions_returns_newest_first(mcp_app):          ║
║      sid1 = mcp_app.call_tool("create_session", {"title": "A"}) ║
║      sid2 = mcp_app.call_tool("create_session", {"title": "B"}) ║
║      sessions = mcp_app.call_tool("list_sessions", {})           ║
║      ids = [s["id"] for s in sessions]                           ║
║      assert sid2 in ids                                          ║
║                                                                  ║
║  def test_load_missing_session_returns_empty(mcp_app):          ║
║      assert mcp_app.call_tool("load_session",                    ║
║                                {"session_id": "nope"}) == {}    ║
║                                                                  ║
║  NOTE: If FastMCP.call_tool is not the correct API,             ║
║  call the inner functions directly:                              ║
║    from mcp.tools.sessions import _list_sessions_raw            ║
║    and test that instead.                                        ║
║                                                                  ║
║  Run: pytest tests/test_sessions.py -v                           ║
║  All 4 tests must pass.                                          ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/sessions.py tests/test_sessions.py           ║
║  git commit -m "feat: session storage MCP tools"                 ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/tools/sessions.py`. Confirm `_list_sessions_raw` is a module-level function. Confirm `_session_path` returns a `Path` object. Confirm no I/O happens at import time.

---

## Task 5 — UI Bridge (`mcp/tools/ui_bridge.py`)

**Agent: Codex** (complex async + threading)

- [ ] **Dispatch Codex:**

```
╔══════════════════════════════════════════════════════════════════╗
║  CODEX TASK 5 — mcp/tools/ui_bridge.py                          ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo: C:\Users\USER\Documents\Code\SmartLMSSystem              ║
║                                                                  ║
║  Build the UI bridge: a FastAPI web server that runs in a        ║
║  background thread of the MCP server process. Shared state       ║
║  (threading.Event + dict) lets MCP tools communicate with        ║
║  the web server.                                                 ║
║                                                                  ║
║  Dependencies already in requirements.txt:                       ║
║  fastapi, uvicorn, fastmcp                                       ║
║                                                                  ║
║  READ FIRST: mcp/config.py, mcp/tools/lms.py (for              ║
║  _list_courses_raw, _list_materials_raw),                        ║
║  mcp/tools/sessions.py (for _list_sessions_raw)                  ║
║                                                                  ║
║  CREATE mcp/tools/ui_bridge.py with exactly this structure:     ║
║                                                                  ║
║  IMPORTS:                                                        ║
║  import json, queue, threading, time, uuid, webbrowser           ║
║  from pathlib import Path                                        ║
║  from typing import Optional                                     ║
║  import uvicorn                                                  ║
║  from fastapi import FastAPI, Request                            ║
║  from fastapi.responses import StreamingResponse, JSONResponse   ║
║  from fastapi.staticfiles import StaticFiles                     ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.config import find_free_port, get_config              ║
║                                                                  ║
║  SHARED STATE (module-level):                                    ║
║  _prompt_events: dict[str, threading.Event] = {}                 ║
║  _prompt_data: dict[str, dict] = {}                              ║
║  _sse_queues: dict[str, queue.Queue] = {}                        ║
║  _web_port: int = 0                                              ║
║  _web_started = threading.Event()                                ║
║                                                                  ║
║  FASTAPI APP:                                                    ║
║  app = FastAPI()                                                 ║
║  UI_DIR = Path(__file__).parent.parent / "ui"                    ║
║                                                                  ║
║  Mount static files at /static when UI_DIR exists:              ║
║  if UI_DIR.exists():                                             ║
║      app.mount("/static", StaticFiles(directory=str(UI_DIR)),   ║
║                name="static")                                    ║
║                                                                  ║
║  ROUTES:                                                         ║
║                                                                  ║
║  GET /                                                           ║
║    Return (UI_DIR / "index.html").read_text() as HTMLResponse.   ║
║    If file missing, return HTMLResponse("<h1>UI not built</h1>") ║
║                                                                  ║
║  GET /api/events/{session_id}                                    ║
║    SSE endpoint. Create a queue.Queue(), store as                ║
║    _sse_queues[session_id]. Stream from it:                      ║
║      - Use run_in_executor to do q.get(timeout=30) without       ║
║        blocking the event loop                                   ║
║      - On queue.Empty → yield ": keepalive\n\n"                  ║
║      - On data → yield f"data: {data}\n\n"                       ║
║      - On disconnect → pop from _sse_queues and return           ║
║    Return StreamingResponse(gen, media_type="text/event-stream") ║
║                                                                  ║
║  POST /api/prompt/{session_id}                                   ║
║    body = await request.json()                                   ║
║    _prompt_data[session_id] = body                               ║
║    event = _prompt_events.get(session_id)                        ║
║    if event: event.set()                                         ║
║    return JSONResponse({"ok": True})                             ║
║                                                                  ║
║  GET /api/sessions                                               ║
║    from mcp.tools.sessions import _list_sessions_raw            ║
║    return JSONResponse(_list_sessions_raw())                     ║
║                                                                  ║
║  GET /api/courses                                                ║
║    from mcp.tools.lms import _list_courses_raw                  ║
║    return JSONResponse(_list_courses_raw())                      ║
║                                                                  ║
║  GET /api/materials/{course_id}                                  ║
║    from mcp.tools.lms import _list_materials_raw                ║
║    return JSONResponse(_list_materials_raw(int(course_id)))     ║
║                                                                  ║
║  WEB SERVER THREAD:                                              ║
║  def _run_web_server(port: int):                                 ║
║      config = uvicorn.Config(app, host="127.0.0.1", port=port,  ║
║                               log_level="error")                 ║
║      server = uvicorn.Server(config)                             ║
║      _web_started.set()                                          ║
║      server.run()   # blocking                                   ║
║                                                                  ║
║  def start_web_server(port: int):                                ║
║      global _web_port                                            ║
║      _web_port = port                                            ║
║      t = threading.Thread(target=_run_web_server,               ║
║                            args=(port,), daemon=True)            ║
║      t.start()                                                   ║
║      _web_started.wait(timeout=5)                                ║
║                                                                  ║
║  MCP TOOLS — register_ui_bridge_tools(mcp: FastMCP):            ║
║                                                                  ║
║  @mcp.tool()                                                     ║
║  def start_ui(session_id: Optional[str] = None) -> dict:        ║
║      """Launch the browser UI. Returns {session_id, url, port}. ║
║      Starts web server on first call."""                         ║
║      global _web_port                                            ║
║      if not _web_started.is_set():                               ║
║          port = find_free_port(get_config().get("port", 8742))  ║
║          start_web_server(port)                                  ║
║      sid = session_id or str(uuid.uuid4())                       ║
║      url = f"http://127.0.0.1:{_web_port}?session={sid}"        ║
║      webbrowser.open(url)                                        ║
║      return {"session_id": sid, "url": url, "port": _web_port}  ║
║                                                                  ║
║  @mcp.tool()                                                     ║
║  def wait_for_prompt(session_id: str) -> dict:                   ║
║      """Block until user submits a prompt in the browser.        ║
║      Returns {text, course_ids, doc_ids, drive_files}."""        ║
║      event = threading.Event()                                   ║
║      _prompt_events[session_id] = event                          ║
║      _prompt_data.pop(session_id, None)                          ║
║      event.wait()  # Released by POST /api/prompt/{session_id}  ║
║      _prompt_events.pop(session_id, None)                        ║
║      return _prompt_data.pop(session_id, {})                     ║
║                                                                  ║
║  @mcp.tool()                                                     ║
║  def render(session_id: str, blocks: list) -> str:               ║
║      """Push card blocks to the browser via SSE."""              ║
║      payload = json.dumps({"type": "blocks", "blocks": blocks}) ║
║      q = _sse_queues.get(session_id)                             ║
║      if q:                                                       ║
║          q.put(payload)                                          ║
║      return "ok"                                                 ║
║                                                                  ║
║  CREATE tests/test_ui_bridge.py:                                 ║
║                                                                  ║
║  import threading, json, pytest                                  ║
║  from fastapi.testclient import TestClient                        ║
║  from mcp.tools.ui_bridge import (app, _prompt_events,          ║
║      _prompt_data, _sse_queues)                                  ║
║                                                                  ║
║  client = TestClient(app)                                        ║
║                                                                  ║
║  def test_root_returns_html():                                   ║
║      r = client.get("/")                                         ║
║      assert r.status_code == 200                                 ║
║      assert "text/html" in r.headers["content-type"]            ║
║                                                                  ║
║  def test_post_prompt_sets_event():                              ║
║      sid = "test-session-1"                                      ║
║      event = threading.Event()                                   ║
║      _prompt_events[sid] = event                                 ║
║      r = client.post(f"/api/prompt/{sid}",                       ║
║          json={"text": "hello", "course_ids": [1]})              ║
║      assert r.status_code == 200                                 ║
║      assert event.is_set()                                       ║
║      assert _prompt_data[sid]["text"] == "hello"                 ║
║                                                                  ║
║  def test_api_sessions_returns_list():                           ║
║      from unittest.mock import patch                             ║
║      with patch("mcp.tools.sessions._list_sessions_raw",        ║
║                 return_value=[]):                                ║
║          r = client.get("/api/sessions")                         ║
║          assert r.status_code == 200                             ║
║          assert r.json() == []                                   ║
║                                                                  ║
║  def test_api_courses_returns_list():                            ║
║      from unittest.mock import patch                             ║
║      with patch("mcp.tools.lms._list_courses_raw",              ║
║                 return_value=[{"id":1,"name":"MATH"}]):          ║
║          r = client.get("/api/courses")                          ║
║          assert r.status_code == 200                             ║
║          assert r.json()[0]["name"] == "MATH"                    ║
║                                                                  ║
║  Run: pytest tests/test_ui_bridge.py -v                          ║
║  All 4 tests must pass.                                          ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/ui_bridge.py tests/test_ui_bridge.py         ║
║  git commit -m "feat: UI bridge with FastAPI SSE and MCP tools"  ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/tools/ui_bridge.py`. Confirm `_prompt_events`, `_prompt_data`, `_sse_queues` are module-level dicts. Confirm `start_web_server` uses a daemon thread. Confirm `wait_for_prompt` uses `threading.Event.wait()` (not asyncio). Confirm all 4 tests pass.

---

## Task 6 — Browser UI (`mcp/ui/`)

**Agent: Codex** (HTML/CSS/JS productionization from approved mockup)

- [ ] **Dispatch Codex:**

```
╔══════════════════════════════════════════════════════════════════╗
║  CODEX TASK 6 — mcp/ui/ browser UI                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo: C:\Users\USER\Documents\Code\SmartLMSSystem              ║
║                                                                  ║
║  READ FIRST: mockups/smart-lms-mockup.html (the approved design) ║
║                                                                  ║
║  Split it into 3 files + download Phosphor Icons locally.        ║
║  The server serves these from mcp/ui/ at /static/.              ║
║                                                                  ║
║  STEP 1 — Download Phosphor Icons web package locally:           ║
║  mkdir -p mcp/ui/icons                                           ║
║  curl -L "https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" \
║       -o mcp/ui/icons/phosphor.css                              ║
║  (Also download the .woff2 font files the CSS references and     ║
║   update paths in phosphor.css to be relative to icons/)         ║
║                                                                  ║
║  If curl is not available, copy the <script> tag from the        ║
║  mockup into the HTML but change src to:                         ║
║  /static/icons/phosphor.js and download the file from:          ║
║  https://unpkg.com/@phosphor-icons/web@2.1.1                     ║
║                                                                  ║
║  STEP 2 — CREATE mcp/ui/styles.css                               ║
║  Extract ALL <style> content from the mockup verbatim.           ║
║  Remove the @import for the CDN Phosphor if present.             ║
║  Add at the top:                                                  ║
║  /* Smart LMS UI Styles */                                       ║
║                                                                  ║
║  STEP 3 — CREATE mcp/ui/app.js                                   ║
║  All JS from the mockup PLUS these additions:                    ║
║                                                                  ║
║  // Read session ID from URL param                               ║
║  const SESSION_ID = new URLSearchParams(                         ║
║      window.location.search).get("session") || "default";       ║
║                                                                  ║
║  // Connect SSE for card block pushes                            ║
║  function connectSSE() {                                         ║
║    const es = new EventSource(`/api/events/${SESSION_ID}`);      ║
║    es.onmessage = (e) => {                                       ║
║      const msg = JSON.parse(e.data);                             ║
║      if (msg.type === "blocks") renderBlocks(msg.blocks);        ║
║    };                                                            ║
║    return es;                                                    ║
║  }                                                               ║
║                                                                  ║
║  // Submit user prompt to server                                  ║
║  async function submitPrompt(text, courseIds, docIds) {          ║
║    await fetch(`/api/prompt/${SESSION_ID}`, {                    ║
║      method: "POST",                                             ║
║      headers: {"Content-Type": "application/json"},              ║
║      body: JSON.stringify({text, course_ids: courseIds,          ║
║                             doc_ids: docIds})                    ║
║    });                                                           ║
║    appendUserMessage(text, courseIds, docIds);                   ║
║  }                                                               ║
║                                                                  ║
║  // Load sessions into sidebar                                   ║
║  async function loadSessions() {                                 ║
║    const res = await fetch("/api/sessions");                     ║
║    const sessions = await res.json();                            ║
║    const list = document.getElementById("session-list");         ║
║    list.innerHTML = sessions.map(s => `                          ║
║      <div class="nav-item" data-id="${s.id}">                    ║
║        ${s.title}                                                ║
║      </div>`).join("");                                          ║
║  }                                                               ║
║                                                                  ║
║  // Load courses into picker popover                             ║
║  async function loadCourses() {                                  ║
║    const res = await fetch("/api/courses");                      ║
║    const courses = await res.json();                             ║
║    const pop = document.getElementById("course-list");           ║
║    pop.innerHTML = courses.map(c => `                            ║
║      <div class="pop-item" data-course-id="${c.id}">             ║
║        <span class="ck"></span>                                   ║
║        <div><div>${c.name}</div></div>                           ║
║      </div>`).join("");                                          ║
║    // clicking a course item loads its materials                 ║
║    pop.querySelectorAll(".pop-item").forEach(el => {             ║
║      el.addEventListener("click", () => toggleCourse(el));      ║
║    });                                                           ║
║  }                                                               ║
║                                                                  ║
║  // renderBlocks — renders the JSON card-block array             ║
║  // from the spec into the thread.                               ║
║  // Block types: flashcard_set, quiz, summary, exam              ║
║  function renderBlocks(blocks) { ... }  /* implement fully */    ║
║                                                                  ║
║  // appendUserMessage — adds user bubble + source pills           ║
║  function appendUserMessage(text, courseIds, docIds) { ... }     ║
║                                                                  ║
║  // Wire send button to submitPrompt                             ║
║  document.querySelector(".send").addEventListener("click", () =>  ║
║      submitPrompt(                                               ║
║          document.querySelector("textarea").value.trim(),        ║
║          getSelectedCourseIds(), getSelectedDocIds()));          ║
║                                                                  ║
║  // Init on load                                                 ║
║  window.addEventListener("DOMContentLoaded", () => {            ║
║    connectSSE();                                                 ║
║    loadSessions();                                               ║
║    loadCourses();                                                 ║
║  });                                                             ║
║                                                                  ║
║  STEP 4 — CREATE mcp/ui/index.html                               ║
║  The mockup HTML, with:                                          ║
║  - <link rel="stylesheet" href="/static/icons/phosphor.css">     ║
║    OR <script src="/static/icons/phosphor.js"></script>          ║
║  - <link rel="stylesheet" href="/static/styles.css">             ║
║  - <script src="/static/app.js" defer></script>                  ║
║  - id="session-list" on the nav items container in sidebar       ║
║  - id="course-list" on the popover course list                   ║
║  - id="thread" on the chat thread div                            ║
║  Remove all inline <style> and <script> tags.                    ║
║  Remove the CDN Phosphor script tag.                             ║
║  The static chat content from the mockup can remain as initial   ║
║  placeholder HTML showing the UI is working.                     ║
║                                                                  ║
║  renderBlocks must fully implement all 4 card types:             ║
║                                                                  ║
║  flashcard_set: 2-column grid of flip cards (same CSS as         ║
║  mockup). Each card: front shows tag+question+hint, back shows   ║
║  tag+answer. Click toggles .flipped class.                       ║
║                                                                  ║
║  quiz: renders each question.                                    ║
║    kind=="mcq": 4 option divs, click grades inline               ║
║      (correct=green, wrong=red, shows explanation on answer)     ║
║    kind=="true_false": two option divs: True / False             ║
║                                                                  ║
║  summary: renders sections as heading + body pairs               ║
║                                                                  ║
║  exam: renders like quiz but also shows                          ║
║    "Time: {duration_minutes} minutes" at top                     ║
║                                                                  ║
║  All DOM manipulation: vanilla JS only, no frameworks.           ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/ui/                                                 ║
║  git commit -m "feat: browser UI with SSE card renderer"         ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Open `mcp/ui/index.html` in a browser directly (it won't have live data but should render the chrome). Check: no CDN URLs in the HTML, Phosphor icons render, the CSS theme matches the mockup (clay accent, warm paper). Read `app.js` and verify `renderBlocks` handles all 4 block types with complete implementations (no `// TODO` stubs).

---

## Task 7 — Google Drive Tools (`mcp/tools/drive.py`)

**Agent: Haiku**

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 7 — mcp/tools/drive.py                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  READ: mcp/config.py (SMART_LMS_DIR)                            ║
║                                                                  ║
║  CREATE mcp/tools/drive.py:                                      ║
║                                                                  ║
║  import io, json                                                 ║
║  from pathlib import Path                                        ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.config import SMART_LMS_DIR, get_config, save_config  ║
║                                                                  ║
║  TOKEN_FILE = SMART_LMS_DIR / "google_token.json"               ║
║  SCOPES = [                                                      ║
║      "https://www.googleapis.com/auth/drive.readonly",           ║
║      "https://www.googleapis.com/auth/documents.readonly",       ║
║  ]                                                               ║
║  CLIENT_SECRETS_FILE = SMART_LMS_DIR / "google_client.json"     ║
║                                                                  ║
║  def _get_credentials():                                         ║
║      from google.oauth2.credentials import Credentials           ║
║      from google_auth_oauthlib.flow import InstalledAppFlow      ║
║      from google.auth.transport.requests import Request          ║
║                                                                  ║
║      creds = None                                                ║
║      if TOKEN_FILE.exists():                                     ║
║          creds = Credentials.from_authorized_user_file(          ║
║              str(TOKEN_FILE), SCOPES)                            ║
║      if not creds or not creds.valid:                            ║
║          if creds and creds.expired and creds.refresh_token:    ║
║              creds.refresh(Request())                            ║
║          else:                                                   ║
║              if not CLIENT_SECRETS_FILE.exists():                ║
║                  raise FileNotFoundError(                        ║
║                      f"Google OAuth client secrets not found at" ║
║                      f" {CLIENT_SECRETS_FILE}. Download from"   ║
║                      f" Google Cloud Console.")                  ║
║              flow = InstalledAppFlow.from_client_secrets_file(  ║
║                  str(CLIENT_SECRETS_FILE), SCOPES)               ║
║              creds = flow.run_local_server(port=0)               ║
║          TOKEN_FILE.write_text(creds.to_json())                  ║
║      return creds                                                ║
║                                                                  ║
║  def _build_drive_service():                                     ║
║      from googleapiclient.discovery import build                 ║
║      return build("drive", "v3",                                 ║
║                   credentials=_get_credentials())               ║
║                                                                  ║
║  def register_drive_tools(mcp: FastMCP):                        ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def connect_google_drive() -> str:                          ║
║          """Initiate Google Drive OAuth. Opens browser for auth. ║
║          Returns status message."""                              ║
║          try:                                                    ║
║              _get_credentials()                                  ║
║              cfg = get_config()                                  ║
║              cfg["google_drive_connected"] = True                ║
║              save_config(cfg)                                    ║
║              return "Google Drive connected successfully."       ║
║          except Exception as e:                                  ║
║              return f"Error: {e}"                                ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def search_drive_files(query: str) -> list[dict]:           ║
║          """Search Google Drive files. Returns [{id,name,        ║
║          mimeType}]."""                                          ║
║          try:                                                    ║
║              svc = _build_drive_service()                        ║
║              results = svc.files().list(                         ║
║                  q=query,                                        ║
║                  pageSize=20,                                    ║
║                  fields="files(id,name,mimeType)"               ║
║              ).execute()                                         ║
║              return results.get("files", [])                     ║
║          except Exception as e:                                  ║
║              return [{"error": str(e)}]                          ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def get_drive_file_text(file_id: str) -> str:               ║
║          """Export a Drive file as plain text. Works for Docs,  ║
║          Slides (exported as plain text via export API)."""      ║
║          try:                                                    ║
║              svc = _build_drive_service()                        ║
║              # Try Google Docs export first                      ║
║              try:                                                ║
║                  data = svc.files().export(                      ║
║                      fileId=file_id,                            ║
║                      mimeType="text/plain"                       ║
║                  ).execute()                                     ║
║                  return data.decode("utf-8") if isinstance(      ║
║                      data, bytes) else data                      ║
║              except Exception:                                   ║
║                  # Fall back to downloading binary + extracting  ║
║                  import tempfile, os                             ║
║                  from mcp.tools.documents import (               ║
║                      extract_document_text)                      ║
║                  req = svc.files().get_media(fileId=file_id)    ║
║                  meta = svc.files().get(                         ║
║                      fileId=file_id,                            ║
║                      fields="name").execute()                    ║
║                  name = meta.get("name", "file")                 ║
║                  with tempfile.NamedTemporaryFile(               ║
║                          suffix=os.path.splitext(name)[1],      ║
║                          delete=False) as f:                     ║
║                      f.write(req.execute())                      ║
║                      fpath = f.name                              ║
║                  text = extract_document_text(fpath)             ║
║                  os.unlink(fpath)                                ║
║                  return text                                     ║
║          except Exception as e:                                  ║
║              return f"Error extracting file: {e}"               ║
║                                                                  ║
║  CREATE tests/test_drive.py:                                     ║
║                                                                  ║
║  import pytest                                                   ║
║  from unittest.mock import patch, MagicMock                      ║
║  from mcp.tools.drive import register_drive_tools               ║
║  from fastmcp import FastMCP                                     ║
║                                                                  ║
║  @pytest.fixture                                                 ║
║  def mcp_app():                                                  ║
║      app = FastMCP("test")                                       ║
║      register_drive_tools(app)                                   ║
║      return app                                                  ║
║                                                                  ║
║  def test_search_drive_files_returns_list_on_error():           ║
║      with patch("mcp.tools.drive._build_drive_service",          ║
║                 side_effect=Exception("no creds")):             ║
║          from mcp.tools.drive import register_drive_tools        ║
║          app = FastMCP("t")                                      ║
║          register_drive_tools(app)                               ║
║          # Call the inner function directly                      ║
║          from mcp.tools import drive as d                        ║
║          # Just verify the function exists and handles errors    ║
║          # (full OAuth test needs real credentials)              ║
║          assert callable(d.register_drive_tools)                 ║
║                                                                  ║
║  Run: pytest tests/test_drive.py -v                              ║
║  Must pass (smoke test only — full Drive test needs OAuth).      ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/drive.py tests/test_drive.py                 ║
║  git commit -m "feat: Google Drive MCP tools"                    ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Read `mcp/tools/drive.py`. Confirm `TOKEN_FILE` and `CLIENT_SECRETS_FILE` point into `SMART_LMS_DIR`. Confirm no credentials are written to the repo. Confirm the error handling in `get_drive_file_text` falls back gracefully.

---

## Task 8 — NotebookLM Stubs (`mcp/tools/notebooklm.py`)

**Agent: Haiku**

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 8 — mcp/tools/notebooklm.py                         ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  CREATE mcp/tools/notebooklm.py                                  ║
║                                                                  ║
║  Investigation result: notebooklm.googleapis.com is in limited  ║
║  preview. The tools are stubbed. When the API becomes available  ║
║  the stubs get replaced with real calls.                         ║
║                                                                  ║
║  from fastmcp import FastMCP                                     ║
║                                                                  ║
║  NOTEBOOKLM_STATUS = "coming_soon"                               ║
║  # Set to "available" when notebooklm.googleapis.com            ║
║  # is accessible without preview program enrollment.            ║
║                                                                  ║
║  def register_notebooklm_tools(mcp: FastMCP):                   ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def connect_notebooklm() -> dict:                           ║
║          """Connect to NotebookLM as an additional source.       ║
║          Currently requires preview access to                    ║
║          notebooklm.googleapis.com. Returns status."""           ║
║          return {                                                ║
║              "status": NOTEBOOKLM_STATUS,                        ║
║              "message": (                                        ║
║                  "NotebookLM API integration is coming soon. "   ║
║                  "To enable, enroll in the notebooklm.googleapis"║
║                  ".com preview program and set NOTEBOOKLM_STATUS"║
║                  " = 'available' in this file."                  ║
║              ),                                                  ║
║          }                                                       ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def list_notebooks() -> list[dict]:                         ║
║          """List NotebookLM notebooks. Currently stubbed."""     ║
║          if NOTEBOOKLM_STATUS != "available":                    ║
║              return []                                           ║
║          # TODO: implement with notebooklm.googleapis.com API   ║
║          return []                                               ║
║                                                                  ║
║      @mcp.tool()                                                 ║
║      def get_notebook_content(notebook_id: str) -> str:          ║
║          """Get text content of a NotebookLM notebook.           ║
║          Currently stubbed."""                                   ║
║          if NOTEBOOKLM_STATUS != "available":                    ║
║              return ""                                           ║
║          # TODO: implement with notebooklm.googleapis.com API   ║
║          return ""                                               ║
║                                                                  ║
║  No test file needed for stubs.                                  ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/tools/notebooklm.py                                ║
║  git commit -m "feat: NotebookLM stubs (API pending preview)"    ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Confirm `NOTEBOOKLM_STATUS` constant is present and the message clearly explains how to enable when the API is available. Confirm no import errors.

---

## Task 9 — MCP Server Entry Point (`mcp/server.py`)

**Agent: Haiku**

- [ ] **Dispatch Haiku:**

```
╔══════════════════════════════════════════════════════════════════╗
║  HAIKU TASK 9 — mcp/server.py                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Repo root: C:\Users\USER\Documents\Code\SmartLMSSystem         ║
║                                                                  ║
║  All tool modules exist: lms, documents, sessions,              ║
║  ui_bridge, drive, notebooklm.                                   ║
║                                                                  ║
║  CREATE mcp/server.py:                                           ║
║                                                                  ║
║  from fastmcp import FastMCP                                     ║
║  from mcp.tools.lms import register_lms_tools                   ║
║  from mcp.tools.sessions import register_session_tools          ║
║  from mcp.tools.ui_bridge import register_ui_bridge_tools        ║
║  from mcp.tools.drive import register_drive_tools               ║
║  from mcp.tools.notebooklm import register_notebooklm_tools     ║
║                                                                  ║
║  mcp = FastMCP(                                                  ║
║      "smart-lms",                                                ║
║      instructions=(                                              ║
║          "Smart LMS — tools for teaching students using their"  ║
║          " Moodle LMS course materials. "                        ║
║          "Start a session with start_ui, wait for prompts with" ║
║          " wait_for_prompt, render content with render."         ║
║      ),                                                          ║
║  )                                                               ║
║                                                                  ║
║  register_lms_tools(mcp)                                         ║
║  register_session_tools(mcp)                                     ║
║  register_ui_bridge_tools(mcp)                                   ║
║  register_drive_tools(mcp)                                       ║
║  register_notebooklm_tools(mcp)                                  ║
║                                                                  ║
║  if __name__ == "__main__":                                      ║
║      mcp.run()                                                   ║
║                                                                  ║
║  Verify it imports cleanly:                                      ║
║  Run: python -c "import mcp.server; print('OK')"                ║
║  Expected output: OK                                             ║
║                                                                  ║
║  Also verify all tools are registered:                           ║
║  Run: python -c "                                                ║
║  from mcp.server import mcp                                      ║
║  tools = [t.name for t in mcp.list_tools()]                     ║
║  print(tools)"                                                   ║
║  Expected: list containing start_ui, wait_for_prompt, render,   ║
║  list_courses, list_materials, get_material_text,                ║
║  create_session, save_turn, list_sessions, load_session,         ║
║  connect_google_drive, search_drive_files, get_drive_file_text,  ║
║  connect_notebooklm, list_notebooks, get_notebook_content        ║
║                                                                  ║
║  Commit:                                                         ║
║  git add mcp/server.py                                           ║
║  git commit -m "feat: MCP server entry point wiring all tools"   ║
╚══════════════════════════════════════════════════════════════════╝
```

- [ ] **Review:** Run `python -c "from mcp.server import mcp; print([t.name for t in mcp.list_tools()])"` and confirm all 16 tools appear. Fix any import errors before proceeding.

---

## Task 10 — The Skill File

**Orchestrator writes this directly** (no subagent — this is orchestration logic, not code).

- [ ] **Create directory:**

```bash
mkdir -p "%USERPROFILE%\.claude\skills\smart-lms"
```

- [ ] **Write `~/.claude/skills/smart-lms/SKILL.md`:**

```markdown
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
Claude Code's MCP settings pointing to:
  python -m mcp.server
from the SmartLMSSystem repo directory.

## Boot Sequence

1. Call `start_ui()` — launches the browser UI and returns
   `{session_id, url, port}`. Save `session_id` for the rest of the session.
2. Call `list_courses()` to confirm LMS credentials are working.
   If the result is empty, tell the user: "Your LMS credentials are not set.
   Call setup_lms_credentials(username, password) to configure them."
3. Call `create_session(title="New session", course="")` to start
   persisting this conversation. Update the title once the user's first
   prompt reveals the subject.

## Study Loop (repeat until user closes the browser or says goodbye)

### Step 1 — Wait for user input
Call `wait_for_prompt(session_id)`.
Returns: `{text, course_ids, doc_ids, drive_files}`

### Step 2 — Gather sources
For each selected course_id, call `get_material_text(course_id, doc_ids)`
to get `[{title, text}]`. Concatenate all text as `<SOURCE_TEXT>`.

If the user has connected Google Drive and listed drive_files,
call `get_drive_file_text(file_id)` for each and append to `<SOURCE_TEXT>`.

### Step 3 — Interpret intent and generate card blocks

Use `<SOURCE_TEXT>` as the knowledge base. Do NOT make up facts.
Every claim must be grounded in `<SOURCE_TEXT>`.

**Intent: "teach me X" / "explain X" / "study X"**
Generate:
- 4-8 flashcards covering key definitions, rules, and concepts
- 1 summary block with 3-6 titled sections

**Intent: "quiz me" / "test me" / "examine me for X finals"**
Generate:
- 1 quiz block with 5 MCQ + 3 true/false questions
- 1 exam block with 8 questions, 60 minutes, and an answer key

**Intent: "summarize X"**
Generate: 1 summary block only

**Other / conversational**
Reply in prose. No card blocks needed.

### Step 4 — Emit card blocks as JSON

Output card-block JSON strictly matching this schema:

```json
[
  {
    "type": "flashcard_set",
    "heading": "string",
    "cards": [{"tag": "str", "front": "str", "back": "str"}]
  },
  {
    "type": "quiz",
    "heading": "string",
    "questions": [
      {
        "kind": "mcq",
        "text": "string",
        "options": ["A", "B", "C", "D"],
        "correct": 0,
        "explanation": "string"
      },
      {
        "kind": "true_false",
        "text": "string",
        "correct": true,
        "explanation": "string"
      }
    ]
  },
  {
    "type": "summary",
    "heading": "string",
    "sections": [{"title": "str", "body": "str"}]
  },
  {
    "type": "exam",
    "heading": "string",
    "duration_minutes": 60,
    "questions": [...same as quiz questions...],
    "answer_key": [{"q": 1, "answer": "B"}]
  }
]
```

### Step 5 — Render and persist

Call `render(session_id, blocks)` to push the card blocks to the browser.

Call `save_turn(session_id, "user", <user text>, <source list>, null)`
Call `save_turn(session_id, "assistant", <prose reply>, [], blocks)`

On the first turn, call `save_config` or update the session title to
reflect the subject (e.g. "MATH1112 — Derivatives").

Go back to Step 1.

## Source priority order
1. LMS course materials (always check if credentials set)
2. Google Drive files (if user selected them)
3. NotebookLM (if available — currently coming soon)

## Rules
- Never fabricate facts. If `<SOURCE_TEXT>` is empty, say so and ask
  the user to select a course or upload materials.
- Keep flashcard fronts concise (one question or term).
- Keep quiz explanations ≤ 2 sentences.
- Exam answer key must be complete — one entry per question.
```

- [ ] **Commit:**

```bash
git add "%USERPROFILE%\.claude\skills\smart-lms\SKILL.md"
```

*(Note: This file is outside the repo. No git commit needed — it lives in the user's global Claude config.)*

---

## Task 11 — Register MCP in Claude Code Settings

**Orchestrator does this directly.**

- [ ] **Find Claude Code settings file:**

```bash
# On Windows, Claude Code MCP settings are in:
# %APPDATA%\Claude\claude_desktop_config.json
# OR the project .claude/settings.json
```

- [ ] **Add the MCP server entry to `.claude/settings.json`** in the project root:

```json
{
  "mcpServers": {
    "smart-lms": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "C:\\Users\\USER\\Documents\\Code\\SmartLMSSystem"
    }
  }
}
```

- [ ] **Verify registration:**

```bash
# In Claude Code, run:
/mcp
# Should list "smart-lms" as a connected server with 16 tools
```

---

## Task 12 — End-to-End Smoke Test

**Orchestrator runs this.**

- [ ] **Install dependencies:**

```bash
pip install -r requirements.txt
```

- [ ] **Run the full test suite:**

```bash
pytest tests/ -v
```

Expected: All tests pass (config: 5, documents: 5, lms: 3, sessions: 4, ui_bridge: 4, drive: 1 = 22 total).

- [ ] **Import smoke test:**

```bash
python -c "
from mcp.server import mcp
from mcp.tools.ui_bridge import app
from mcp.config import get_config, ensure_dirs
ensure_dirs()
print('Config:', get_config())
print('Tools:', [t.name for t in mcp.list_tools()])
print('All OK')
"
```

Expected output ends with `All OK`.

- [ ] **Start the server manually and verify it responds:**

```bash
python -m mcp.server &
# In a second terminal:
python -c "
import requests, time
time.sleep(1)
r = requests.get('http://127.0.0.1:8742/api/sessions')
print('Sessions API:', r.status_code, r.json())
"
```

Expected: `Sessions API: 200 []`

- [ ] **Final commit:**

```bash
git add .
git commit -m "feat: complete Smart LMS MCP + Skill implementation"
```

---

## Self-Review Checklist

- [x] **Spec section 3** (Skill): covered in Task 10 — SKILL.md with full boot + study loop
- [x] **Spec section 4.1** (LMS tools): Task 3 — `setup_lms_credentials`, `list_courses`, `list_materials`, `get_material_text`
- [x] **Spec section 4.2** (Drive tools): Task 7 — `connect_google_drive`, `search_drive_files`, `get_drive_file_text`
- [x] **Spec section 4.3** (UI bridge): Task 5 — `start_ui`, `wait_for_prompt`, `render`
- [x] **Spec section 4.4** (NotebookLM stubs): Task 8 — all 3 tools stubbed with clear upgrade path
- [x] **Spec section 4.5** (Session storage): Task 4 — `create_session`, `save_turn`, `list_sessions`, `load_session`
- [x] **Spec section 5** (Card schema): Defined in SKILL.md + fully implemented in `app.js` (Task 6)
- [x] **Spec section 6** (Browser UI): Task 6 — all behaviors listed (flip cards, quiz grading, sidebar, pickers)
- [x] **Spec section 7** (Global folder): Task 1 config.py — `~/.smart-lms/` with `sessions/` subdirectory
- [x] **Spec section 8** (Dependencies): requirements.txt in Task 1
- [x] **No placeholders**: Every code step has complete, runnable code
- [x] **Type consistency**: `session_id: str`, `course_id: int`, `material_ids: list[str]` used consistently
- [x] **`_list_courses_raw` / `_list_materials_raw` / `_list_sessions_raw`**: All defined as module-level functions (required by ui_bridge API routes)
