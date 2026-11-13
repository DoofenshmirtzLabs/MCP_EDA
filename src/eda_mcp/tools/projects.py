import json
import re
from fastmcp import FastMCP
from eda_mcp.config import WORKSPACE_ROOT
from eda_mcp.services.workspace import project_dir

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

def register(mcp: FastMCP) -> None:
    @mcp.tool
    def create_project(project_name: str, top_module: str) -> dict:
        """Create a project workspace and starter directories for an RTL design."""
        if not _IDENTIFIER.fullmatch(top_module):
            raise ValueError("top_module must be a valid Verilog identifier.")
        path = project_dir(project_name)
        if path.exists():
            raise ValueError("Project already exists.")
        for folder in ("rtl", "tb", "constraints", "config", "build", "reports", "layout", "formal"):
            (path / folder).mkdir(parents=True, exist_ok=True)
        (path / "project.json").write_text(
            json.dumps({"project": project_name, "top_module": top_module}, indent=2), encoding="utf-8"
        )
        return {"status": "success", "project": project_name, "path": str(path), "top_module": top_module}

    @mcp.tool
    def list_projects() -> dict:
        """List projects in the managed EDA workspace."""
        projects = sorted(p.name for p in WORKSPACE_ROOT.iterdir() if p.is_dir())
        return {"status": "success", "projects": projects, "count": len(projects)}
