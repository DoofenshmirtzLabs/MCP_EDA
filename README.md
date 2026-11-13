# EDA MCP Server starter

A modular FastMCP server exposing project, RTL, simulation, synthesis, physical-design,
timing, verification and report tools.

## Install

Install `uv` in the same environment that will run the server (for example, inside
WSL if you use the WSL launcher below):

```bash
sudo apt update
sudo apt install -y curl ca-certificates build-essential \
  iverilog verilator yosys klayout
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new terminal after installing `uv`, or follow the installer instructions to
add it to your `PATH`. No manual Python installation, `pip install`, or project
`.venv` activation is needed. The launcher uses `uv`'s cached, isolated run
environment, so it does not create a `.venv` in this project.

OpenLane 2, OpenROAD, OpenSTA, Magic, Netgen, SymbiYosys and EQY should be installed
using their documented, mutually compatible tool/PDK flow. The MCP server detects
missing executables and returns `unavailable`; it does not pretend to run them.

## Run

```bash
./run_mcp.sh
```

The server uses stdio. Do not print debug messages to stdout.

## Claude Desktop on Windows with WSL

If the server files and `uv` are in WSL, add this entry to
`%APPDATA%\Claude\claude_desktop_config.json` on Windows. Merge the `eda` entry
into the existing `mcpServers` object if you already have one. Update the path if
your project is in a different location:

```json
{
  "mcpServers": {
    "eda": {
      "command": "wsl.exe",
      "args": [
        "-e",
        "bash",
        "-lc",
        "cd /mnt/c/Users/saikr/mtech-learnings/projects/eda_mcp_starter/mcp_server && exec ./run_mcp.sh"
      ]
    }
  }
}
```

Restart Claude Desktop after saving the configuration. The `uv` executable must
be available on `PATH` in the WSL login shell.

## Current safety boundaries

- No shell=True or arbitrary shell command tool.
- Executables are allowlisted.
- Commands run only inside the managed workspace.
- Project-relative file paths are checked against traversal.
- Timeouts terminate stuck processes.
- Tool calls return stdout/stderr and actual exit status.

## Important integration note

PDK-specific OpenLane, OpenSTA, KLayout DRC, Magic DRC and Netgen LVS configurations
must be supplied and validated for the chosen process. Generic scripts are not
interchangeable between SKY130, IHP SG13G2 and SCL 180nm.
