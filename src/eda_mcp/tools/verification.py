from fastmcp import FastMCP
from eda_mcp.services.workspace import project_dir, project_file
from eda_mcp.services.process import run_eda

def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def run_simulation(project_name: str, testbench_file: str, top_module: str, source_files: list[str]) -> dict:
        """Compile and run a Verilog testbench using Icarus Verilog and VVP."""
        base = project_dir(project_name)
        tb = project_file(project_name, testbench_file)
        if not tb.is_file() or not testbench_file.startswith("tb/"):
            raise ValueError("testbench_file must exist inside tb/.")
        if not source_files:
            raise ValueError("At least one RTL source file is required.")
        for src in source_files:
            if not src.startswith("rtl/") or not project_file(project_name, src).is_file():
                raise ValueError(f"Missing or invalid RTL source: {src}")
        build = base / "build"
        build.mkdir(exist_ok=True)
        output = "build/simulation.vvp"
        compile_result = await run_eda(
            "iverilog",
            ["-g2012", "-s", top_module, "-o", output, *source_files, testbench_file],
            base,
            90,
        )
        if compile_result["status"] != "success":
            return {"status": "compile_failed", "compile": compile_result}
        run_result = await run_eda("vvp", [output], base, 90)
        return {"status": run_result["status"], "compile": compile_result, "simulation": run_result}

    @mcp.tool
    async def run_formal_verification(project_name: str, config_file: str, timeout_s: int = 300) -> dict:
        """Run SymbiYosys using an existing .sby configuration under formal/."""
        if not config_file.startswith("formal/") or not config_file.endswith(".sby"):
            raise ValueError("config_file must be a .sby file inside formal/.")
        path = project_file(project_name, config_file)
        if not path.is_file():
            raise FileNotFoundError(config_file)
        return await run_eda("sby", ["-f", config_file], project_dir(project_name), timeout_s)

    @mcp.tool
    async def run_equivalence_check(project_name: str, config_file: str, timeout_s: int = 300) -> dict:
        """Run EQY using an existing .eqy configuration under formal/."""
        if not config_file.startswith("formal/") or not config_file.endswith(".eqy"):
            raise ValueError("config_file must be an .eqy file inside formal/.")
        path = project_file(project_name, config_file)
        if not path.is_file():
            raise FileNotFoundError(config_file)
        return await run_eda("eqy", ["-f", config_file], project_dir(project_name), timeout_s)
