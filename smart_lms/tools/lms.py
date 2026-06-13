import hashlib
import os
import sys
import tempfile
from pathlib import Path

import requests
from fastmcp import FastMCP

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from lms_scraper import LMSScraper  # noqa: E402

from smart_lms.config import get_config, get_lms_credentials, store_lms_credentials
from smart_lms.tools.documents import extract_document_text


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


import concurrent.futures


def _get_material_text_raw(course_id: int, material_ids: list[str]) -> list[dict]:
    """Download and extract text from selected materials in parallel.
    Returns [{title, text}] or [{title, text, error}] on failure."""
    all_mats = _list_materials_raw(course_id)
    selected = [m for m in all_mats if m["id"] in material_ids]
    
    def process_material(mat, tmp_dir):
        try:
            resp = requests.get(mat["link"], stream=True, timeout=30)
            resp.raise_for_status()
            fpath = os.path.join(tmp_dir, mat["title"])
            with open(fpath, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            text = extract_document_text(fpath)
            if text.strip():
                return {"title": mat["title"], "text": text}
        except Exception as e:
            return {"title": mat["title"], "text": "", "error": str(e)}
        return None

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_material, mat, tmp) for mat in selected]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)
    return results


def register_lms_tools(mcp: FastMCP):

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
        return _get_material_text_raw(course_id, material_ids)
