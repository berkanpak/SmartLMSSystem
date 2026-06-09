import sys
from pathlib import Path
import importlib.util

# First, import fastmcp before the project directory is in the path
# This prevents the local mcp folder from shadowing the SDK's mcp
import pytest
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

# Now load the lms module directly from the file to avoid import issues
project_root = Path(__file__).parent.parent
lms_path = project_root / "mcp" / "tools" / "lms.py"

# Add project root to path for the module to use when importing
sys.path.insert(0, str(project_root))

# Load the module directly
spec = importlib.util.spec_from_file_location("lms_module", lms_path)
lms_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lms_module)

register_lms_tools = lms_module.register_lms_tools
_material_id = lms_module._material_id
_list_courses_raw = lms_module._list_courses_raw


@pytest.fixture
def mcp_app():
    app = FastMCP("test")
    register_lms_tools(app)
    return app


def test_material_id_is_deterministic():
    assert _material_id("http://a.com/f") == _material_id("http://a.com/f")
    assert len(_material_id("http://a.com/f")) == 12


def test_list_courses_raw_returns_empty_when_no_creds():
    with patch.object(lms_module, "get_lms_credentials", return_value=(None, None)):
        assert _list_courses_raw() == []


def test_list_courses_raw_calls_scraper():
    mock_scraper = MagicMock()
    mock_scraper.get_courses.return_value = [
        {"id": 1, "name": "MATH1112", "link": "..."}
    ]
    with patch.object(lms_module, "get_lms_credentials", return_value=("user", "pass")), \
         patch.object(lms_module, "_get_scraper", return_value=mock_scraper):
        result = _list_courses_raw()
        assert result == [{"id": 1, "name": "MATH1112"}]
