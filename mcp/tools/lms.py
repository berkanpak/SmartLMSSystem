import hashlib
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

import requests
from fastmcp import FastMCP

# Get absolute path to project root
project_root = Path(__file__).parent.parent.parent.resolve()

# Add project root to path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import lms_scraper from project root
try:
    from lms_scraper import LMSScraper
except ImportError:
    # Try loading directly
    lms_scraper_path = project_root / "lms_scraper.py"
    spec = importlib.util.spec_from_file_location("lms_scraper", lms_scraper_path)
    lms_scraper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lms_scraper_module)
    LMSScraper = lms_scraper_module.LMSScraper

# Import from our local mcp.config and mcp.tools.documents
# Load these directly to avoid import conflicts
config_path = project_root / "mcp" / "config.py"
documents_path = project_root / "mcp" / "tools" / "documents.py"

spec_config = importlib.util.spec_from_file_location("local_config", config_path)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)

spec_docs = importlib.util.spec_from_file_location("local_documents", documents_path)
documents_module = importlib.util.module_from_spec(spec_docs)
spec_docs.loader.exec_module(documents_module)

get_config = config_module.get_config
get_lms_credentials = config_module.get_lms_credentials
store_lms_credentials = config_module.store_lms_credentials
extract_document_text = documents_module.extract_document_text


def _material_id(file_url: str) -> str:
    return hashlib.md5(file_url.encode()).hexdigest()[:12]


def _get_scraper() -> LMSScraper:
    return LMSScraper(base_url=get_config()["lms_base_url"])


def _list_courses_raw() -> list[dict]:
    username, password = get_lms_credentials()
    if not username:
        return []
    scraper = _get_scraper()
    courses = scraper.get_courses(username, password)
    return [{"id": c["id"], "name": c["name"]} for c in courses]


def _list_materials_raw(course_id: int) -> list[dict]:
    username, password = get_lms_credentials()
    if not username:
        return []
    scraper = _get_scraper()
    link = f"{get_config()['lms_base_url']}/course/view.php?id={course_id}"
    materials = scraper.get_materials(username, password, link)
    return [
        {
            "id": _material_id(m["link"]),
            "title": m["title"],
            "link": m["link"],
        }
        for m in materials
    ]


def register_lms_tools(mcp: FastMCP):

    @mcp.tool()
    def setup_lms_credentials(username: str, password: str) -> bool:
        """Store Moodle credentials in the OS keychain and verify login."""
        store_lms_credentials(username, password)
        scraper = _get_scraper()
        return scraper.login_test(username, password)

    @mcp.tool()
    def list_courses() -> list[dict]:
        """List all enrolled courses. Returns [{id, name}]."""
        return _list_courses_raw()

    @mcp.tool()
    def list_materials(course_id: int) -> list[dict]:
        """List downloadable materials for a course. Returns [{id, title, link}]."""
        return _list_materials_raw(course_id)

    @mcp.tool()
    def get_material_text(course_id: int, material_ids: list[str]) -> list[dict]:
        """Download and extract text from selected materials.
        Returns [{title, text}] or [{title, text, error}] on failure."""
        all_mats = _list_materials_raw(course_id)
        selected = [m for m in all_mats if m["id"] in material_ids]
        results = []
        with tempfile.TemporaryDirectory() as tmp:
            for mat in selected:
                try:
                    resp = requests.get(mat["link"], stream=True, timeout=30)
                    resp.raise_for_status()
                    fpath = os.path.join(tmp, mat["title"])
                    with open(fpath, "wb") as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                    text = extract_document_text(fpath)
                    if text.strip():
                        results.append({"title": mat["title"], "text": text})
                except Exception as e:
                    results.append({"title": mat["title"], "text": "", "error": str(e)})
        return results
