import platform
import sys
from fastmcp import FastMCP
from eda_mcp.services.process import executable_status

def register(mcp: FastMCP) -> None:
    @mcp.tool
    def check_eda_environment() -> dict:
        """Check availability of RTL, verification, synthesis and backend EDA tools."""
        tools = executable_status()
        installed = [name for name, item in tools.items() if item["installed"]]
        missing = [name for name, item in tools.items() if not item["installed"]]
        return {
            "status": "success",
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "installed_tools": installed,
            "missing_tools": missing,
            "tools": tools,
        }
