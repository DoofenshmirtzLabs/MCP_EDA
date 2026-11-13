import json
from fastmcp import FastMCP
from eda_mcp.services.workspace import project_file

def register(mcp: FastMCP) -> None:
    @mcp.tool
    def get_design_report(project_name: str, report_file: str) -> dict:
        """Read a text report or JSON metrics file from reports/ or build/."""
        if not report_file.startswith(("reports/", "build/")):
            raise ValueError("report_file must be under reports/ or build/.")
        path = project_file(project_name, report_file)
        if not path.is_file():
            raise FileNotFoundError(report_file)
        if path.stat().st_size > 2_000_000:
            raise ValueError("Report exceeds the 2 MB read limit.")
        content = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".json":
            try:
                return {"status": "success", "path": report_file, "metrics": json.loads(content)}
            except json.JSONDecodeError:
                pass
        return {"status": "success", "path": report_file, "content": content[-30000:]}
