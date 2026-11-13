from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def run_physical_design(project_name: str, config_file: str, timeout_s: int = 1800) -> dict:
        """Run OpenLane 2 with an existing JSON config inside the project config/ directory."""
        if not config_file.startswith("config/") or not config_file.endswith(".json"):
            raise ValueError("config_file must be a JSON file inside config/.")
        path = project_file(project_name, config_file)
        if not path.is_file():
            raise FileNotFoundError(config_file)
        return await run_eda("openlane", [config_file], project_dir(project_name), timeout_s)

    @mcp.tool
    async def run_openroad_script(project_name: str, script_file: str, timeout_s: int = 600) -> dict:
        """Run an explicit Tcl script with OpenROAD from the project's config/ directory."""
        if not script_file.startswith("config/") or not script_file.endswith((".tcl", ".script")):
            raise ValueError("script_file must be a Tcl/script file inside config/.")
        if not project_file(project_name, script_file).is_file():
            raise FileNotFoundError(script_file)
        return await run_eda("openroad", ["-exit", script_file], project_dir(project_name), timeout_s)
