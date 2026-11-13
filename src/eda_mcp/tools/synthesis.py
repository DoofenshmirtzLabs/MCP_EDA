import re
from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def synthesize_design(project_name: str, top_module: str, rtl_files: list[str]) -> dict:
        """Synthesize RTL with Yosys and ABC; write a gate-level Verilog netlist."""
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", top_module):
            raise ValueError("top_module must be a valid Verilog identifier.")
        if not rtl_files:
            raise ValueError("At least one RTL file is required.")
        base = project_dir(project_name)
        for item in rtl_files:
            if not item.startswith("rtl/") or not project_file(project_name, item).is_file():
                raise ValueError(f"Missing or invalid RTL file: {item}")
        (base / "build").mkdir(exist_ok=True)
        netlist = "build/synthesized.v"
        # All paths are constrained to the project's rtl/ subtree.
        script = (
            "read_verilog -sv " + " ".join(rtl_files) + "; "
            f"hierarchy -check -top {top_module}; "
            f"synth -top {top_module}; "
            "stat; "
            f"write_verilog -noattr {netlist}"
        )
        result = await run_eda("yosys", ["-p", script], base, 180)
        result["netlist"] = netlist if result["status"] == "success" else None
        return result
