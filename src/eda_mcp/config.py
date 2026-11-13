from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(os.environ.get("EDA_WORKSPACE", PROJECT_ROOT / "workspace")).resolve()
LOG_ROOT = Path(os.environ.get("EDA_LOGS", PROJECT_ROOT / "logs")).resolve()

WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
LOG_ROOT.mkdir(parents=True, exist_ok=True)

# Executable names are fixed here. MCP callers cannot choose arbitrary commands.
EXECUTABLES = {
    "iverilog": "iverilog",
    "vvp": "vvp",
    "verilator": "verilator",
    "yosys": "yosys",
    "openlane": "openlane",
    "openroad": "openroad",
    "sta": "sta",
    "klayout": "klayout",
    "magic": "magic",
    "netgen": "netgen",
    "sby": "sby",
    "eqy": "eqy",
}
