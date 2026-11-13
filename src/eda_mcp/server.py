from fastmcp import FastMCP

from eda_mcp.tools import (
    environment, projects, rtl, verification, synthesis,
    physical_design, timing, physical_verification, reports,
)

mcp = FastMCP("EDA MCP Server")

for module in (
    environment, projects, rtl, verification, synthesis,
    physical_design, timing, physical_verification, reports,
):
    module.register(mcp)

if __name__ == "__main__":
    # stdio is the expected transport for Claude Desktop local MCP servers.
    mcp.run()
