from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def analyze_timing(project_name: str, sta_script: str, timeout_s: int = 300) -> dict:
        """Run OpenSTA using a project Tcl script that loads libraries, netlist and constraints."""
        if not sta_script.startswith("config/") or not sta_script.endswith(".tcl"):
            raise ValueError("sta_script must be a .tcl file inside config/.")
        if not project_file(project_name, sta_script).is_file():
            raise FileNotFoundError(sta_script)
        return await run_eda("sta", ["-no_splash", "-exit", sta_script], project_dir(project_name), timeout_s)

    @mcp.tool
    async def extract_parasitics(project_name: str, openroad_script: str, timeout_s: int = 600) -> dict:
        """Run an OpenROAD Tcl script that performs the PDK-configured parasitic extraction flow."""
        if not openroad_script.startswith("config/") or not openroad_script.endswith(".tcl"):
            raise ValueError("openroad_script must be a .tcl file inside config/.")
        if not project_file(project_name, openroad_script).is_file():
            raise FileNotFoundError(openroad_script)
        return await run_eda("openroad", ["-exit", openroad_script], project_dir(project_name), timeout_s)
