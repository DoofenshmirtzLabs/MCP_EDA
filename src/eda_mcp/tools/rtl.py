from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    def write_rtl(project_name: str, file_name: str, verilog_source: str) -> dict:
        """Write Verilog/SystemVerilog source into a project's rtl directory."""
        if not file_name.endswith((".v", ".sv")) or "/" in file_name or "\\" in file_name:
            raise ValueError("file_name must be a simple .v or .sv filename.")
        path = project_file(project_name, f"rtl/{file_name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(verilog_source, encoding="utf-8")
        return {"status": "success", "file": str(path), "bytes_written": path.stat().st_size}

    @mcp.tool
    def read_design_file(project_name: str, relative_path: str) -> dict:
        """Read a text file from the project workspace."""
        path = project_file(project_name, relative_path)
        if not path.is_file():
            raise FileNotFoundError(relative_path)
        if path.stat().st_size > 1_000_000:
            raise ValueError("File is larger than the 1 MB read limit.")
        return {"status": "success", "path": relative_path, "content": path.read_text(encoding="utf-8")}

    @mcp.tool
    async def validate_rtl(project_name: str, top_module: str, rtl_file: str) -> dict:
        """Lint RTL using Verilator. rtl_file is relative to the project directory."""
        if not rtl_file.startswith("rtl/") or not rtl_file.endswith((".v", ".sv")):
            raise ValueError("rtl_file must point to a .v/.sv file inside rtl/.")
        path = project_file(project_name, rtl_file)
        if not path.is_file():
            raise FileNotFoundError(rtl_file)
        return await run_eda("verilator", ["--lint-only", "-Wall", "--top-module", top_module, rtl_file], project_dir(project_name), 60)
