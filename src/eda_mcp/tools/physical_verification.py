from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def run_klayout_drc(project_name: str, drc_script: str, timeout_s: int = 600) -> dict:
        """Run a PDK-specific KLayout DRC Ruby script from config/."""
        if not drc_script.startswith("config/") or not drc_script.endswith(".rb"):
            raise ValueError("drc_script must be a Ruby script inside config/.")
        if not project_file(project_name, drc_script).is_file():
            raise FileNotFoundError(drc_script)
        return await run_eda("klayout", ["-b", "-r", drc_script], project_dir(project_name), timeout_s)

    @mcp.tool
    def run_magic_drc(project_name: str, magic_script: str) -> dict:
        """Reserved adapter: Magic DRC requires a PDK-specific deck and invocation; use OpenLane's configured DRC flow until that adapter is configured."""
        if not magic_script.startswith("config/") or not magic_script.endswith((".tcl", ".magic")):
            raise ValueError("magic_script must be a PDK-specific script under config/.")
        if not project_file(project_name, magic_script).is_file():
            raise FileNotFoundError(magic_script)
        return {
            "status": "not_configured",
            "message": "Magic DRC invocation is PDK/flow-specific. Use the OpenLane physical verification flow for now; we will add the correct Magic batch adapter once the target PDK deck is available.",
            "script": magic_script,
        }

    @mcp.tool
    async def run_netgen_lvs(
        project_name: str,
        layout_file: str,
        layout_top: str,
        schematic_file: str,
        schematic_top: str,
        setup_file: str,
        report_file: str = "reports/lvs.rpt",
        timeout_s: int = 600,
    ) -> dict:
        """Compare layout and schematic/netlist with Netgen using a PDK-specific setup file."""
        import re
        for name in (layout_top, schematic_top):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", name):
                raise ValueError("Cell names must be valid identifiers.")
        if not layout_file.startswith(("layout/", "build/")):
            raise ValueError("layout_file must be under layout/ or build/.")
        if not schematic_file.startswith(("build/", "rtl/")):
            raise ValueError("schematic_file must be under build/ or rtl/.")
        if not setup_file.startswith("config/"):
            raise ValueError("setup_file must be under config/.")
        for item in (layout_file, schematic_file, setup_file):
            if not project_file(project_name, item).is_file():
                raise FileNotFoundError(item)
        project_file(project_name, report_file).parent.mkdir(parents=True, exist_ok=True)
        args = [
            "-batch", "lvs",
            f"{layout_file} {layout_top}",
            f"{schematic_file} {schematic_top}",
            setup_file, report_file,
        ]
        return await run_eda("netgen", args, project_dir(project_name), timeout_s)

    @mcp.tool
    async def inspect_layout(project_name: str, layout_file: str) -> dict:
        """Check that a GDS/OASIS layout artifact exists and return basic file metadata."""
        if not layout_file.startswith(("layout/", "build/")) or not layout_file.endswith((".gds", ".gdsii", ".oas")):
            raise ValueError("layout_file must be a GDS/OASIS file under layout/ or build/.")
        path = project_file(project_name, layout_file)
        if not path.is_file():
            raise FileNotFoundError(layout_file)
        return {"status": "success", "path": layout_file, "size_bytes": path.stat().st_size,
                "note": "Use KLayout GUI or a configured batch script for geometric inspection."}
