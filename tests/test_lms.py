import pytest
from unittest.mock import patch, MagicMock
from fastmcp import FastMCP

from smart_lms.tools import lms as lms_module
from smart_lms.tools.lms import register_lms_tools, _material_id, _list_courses_raw


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
