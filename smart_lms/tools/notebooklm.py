from fastmcp import FastMCP

NOTEBOOKLM_STATUS = "coming_soon"
# Set to "available" when notebooklm.googleapis.com is accessible
# without preview program enrollment.


def register_notebooklm_tools(mcp: FastMCP):

    @mcp.tool()
    def connect_notebooklm() -> dict:
        """Connect to NotebookLM as an additional source.
        Currently requires preview access to notebooklm.googleapis.com.
        Returns status."""
        return {
            "status": NOTEBOOKLM_STATUS,
            "message": (
                "NotebookLM API integration is coming soon. "
                "To enable, enroll in the notebooklm.googleapis.com "
                "preview program and set NOTEBOOKLM_STATUS = 'available' "
                "in this file."
            ),
        }

    @mcp.tool()
    def list_notebooks() -> list[dict]:
        """List NotebookLM notebooks. Currently stubbed."""
        if NOTEBOOKLM_STATUS != "available":
            return []
        return []

    @mcp.tool()
    def get_notebook_content(notebook_id: str) -> str:
        """Get text content of a NotebookLM notebook. Currently stubbed."""
        if NOTEBOOKLM_STATUS != "available":
            return ""
        return ""
