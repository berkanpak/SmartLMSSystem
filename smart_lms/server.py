from fastmcp import FastMCP
from smart_lms.tools.lms import register_lms_tools
from smart_lms.tools.sessions import register_session_tools
from smart_lms.tools.ui_bridge import register_ui_bridge_tools
from smart_lms.tools.drive import register_drive_tools
from smart_lms.tools.notebooklm import register_notebooklm_tools

mcp = FastMCP(
    "smart-lms",
    instructions=(
        "Smart LMS - tools for teaching students using their Moodle LMS course "
        "materials. Start a session with start_ui, check for prompts with "
        "check_prompt, render content with render."
    ),
)

register_lms_tools(mcp)
register_session_tools(mcp)
register_ui_bridge_tools(mcp)
register_drive_tools(mcp)
register_notebooklm_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
