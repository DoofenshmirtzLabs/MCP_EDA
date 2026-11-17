# EDA MCP Server

A modular, secure **Model Context Protocol (MCP)** server built with **FastMCP** that connects Large Language Model (LLM) agents (such as Claude Desktop, Cursor, and custom AI agents) directly to open-source Electronic Design Automation (EDA) silicon engineering toolchains.

The server enables LLMs to autonomously create projects, author Verilog/SystemVerilog RTL, run functional simulations, verify formal assertions, synthesize gate-level netlists, perform static timing analysis (STA), execute automated physical design (Place & Route), and verify layout sign-off rules (DRC & LVS).

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Safety & Sandbox Boundaries](#safety--sandbox-boundaries)
- [Project Workspace Structure](#project-workspace-structure)
- [EDA Tools Breakdown](#eda-tools-breakdown)
- [Exposed MCP Tools](#exposed-mcp-tools)
- [End-to-End Design Workflow](#end-to-end-design-workflow)
- [Primary Use Cases](#primary-use-cases)
- [Installation & Prerequisites](#installation--prerequisites)
- [Running the Server](#running-the-server)
- [Claude Desktop Integration (Windows + WSL)](#claude-desktop-integration-windows--wsl)
- [PDK & Integration Notes](#pdk--integration-notes)

---

## Architectural Overview

LLMs interact with `eda-mcp` through the standard JSON-RPC MCP protocol over standard I/O (`stdio`). Rather than granting the agent raw shell access, `eda-mcp` acts as a deterministic, safety-enforced gateway:

```
┌────────────────────────────────┐
│   LLM Client (Claude Desktop)   │
└──────────────┬─────────────────┘
               │ JSON-RPC (stdio)
               ▼
┌────────────────────────────────────────────────────────┐
│                   EDA MCP Server                       │
│  ┌────────────────────────┐  ┌───────────────────────┐ │
│  │   Workspace Manager    │  │  Allowlisted Process  │ │
│  │   (Path traversal &    │  │  Runner (Asyncio,     │ │
│  │   sandbox validation)  │  │  Timeouts, No Shell)  │ │
│  └────────────────────────┘  └───────────────────────┘ │
└──────────────┬─────────────────────────────────────────┘
               │ Execution via Subprocess Executables
               ▼
┌────────────────────────────────────────────────────────┐
│                 Linux / WSL EDA Tools                  │
│   iverilog · vvp · verilator · yosys · openlane        │
│   openroad · sta · klayout · magic · netgen · sby · eqy │
└────────────────────────────────────────────────────────┘
```

---

## Safety & Sandbox Boundaries

Running compilers and physical design pipelines via autonomous agents requires strict defensive controls:

1. **No Arbitrary Shell Execution (`shell=False`)**: Commands are invoked directly via `asyncio.create_subprocess_exec` using tokenized argument arrays. Shell expansion, piping, and command injection are structurally impossible.
2. **Strict Executable Allowlist**: Only 12 pre-approved EDA binaries defined in `config.py` can be executed.
3. **Workspace Isolation & Path Traversal Guards**: 
   - Projects and filenames are validated against strict alphanumeric regex identifiers.
   - All paths are resolved and verified to remain strictly within the project directory or the managed `workspace/` root.
4. **Execution Timeouts**: Every process is bounded by a timeout (ranging from 60 seconds for linting to 1,800 seconds for complete physical design runs) to prevent infinite loops from hanging the agent.
5. **Output Truncation & Memory Safety**: Outputs and logs are safely captured, filtered, and truncated (tail up to 20,000 characters) to avoid overflowing the LLM context window.

---

## Project Workspace Structure

Each project initialized via `create_project` follows a standardized, modular directory hierarchy:

```
workspace/<project_name>/
├── project.json          # Project metadata and top-module designation
├── rtl/                  # Verilog and SystemVerilog design source files (.v, .sv)
├── tb/                   # Simulation testbenches (.v, .sv)
├── constraints/          # Timing constraints (.sdc) and pin configurations
├── config/               # PDK configurations, OpenLane configs (.json), STA scripts (.tcl)
├── build/                # Intermediate artifacts (synthesized netlists, simulation binaries)
├── reports/              # Timing, area, power, DRC, and LVS reports (.rpt, .json)
├── layout/               # Generated layout stream files (.gds, .oas, .def)
└── formal/               # SymbiYosys (.sby) and Equivalence (.eqy) proof scripts
```

---

## EDA Tools Breakdown

The server wraps the entire modern open-source silicon compilation and verification stack:

| Tool | Category | Role in Pipeline | Key Inputs | Key Outputs |
| :--- | :--- | :--- | :--- | :--- |
| **`iverilog`** | Simulation | IEEE-1364 Verilog compiler front-end | `.v`, `.sv` source | `.vvp` bytecode |
| **`vvp`** | Simulation | Runtime engine executing compiled testbench bytecode | `.vvp` bytecode | Console logs, `.vcd` waveform |
| **`verilator`** | Lint & Fast Sim | Cycle-accurate linter and high-speed C++ model compiler | `.v`, `.sv` RTL | Lint diagnostics, C++ models |
| **`yosys`** | Synthesis | RTL synthesis, Boolean optimization, tech mapping | Verilog RTL, `.lib` | Gate-level netlist (`synthesized.v`) |
| **`sby`** | Formal | SymbiYosys formal verification driver (BMC & induction) | `.sby`, RTL assertions | Proof results, counterexample traces |
| **`eqy`** | Formal | Equivalence checking between RTL and gate netlists | `.eqy`, Golden & Rev RTL | Functional equivalence report |
| **`sta`** | Timing | Static Timing Analysis (OpenSTA) engine | Netlist, `.lib`, `.sdc` | Slack, WNS, TNS, critical paths |
| **`openroad`** | PnR | Automated floorplanning, placement, CTS, and routing | Netlist, LEF, DEF, SDC | Routed DEF, timing-closed layout |
| **`openlane`** | Flow Driver | Automated RTL-to-GDSII flow orchestration framework | Config JSON, RTL, PDK | Final GDSII, metrics, sign-off reports |
| **`klayout`** | Layout & DRC | High-performance GDS/OASIS viewer and batch DRC engine | `.gds`, `.oas`, `.rb` | DRC violation markers, layout metadata |
| **`magic`** | Layout & DRC | VLSI layout editor, physical extraction, and sign-off DRC | GDSII, tech files | Extracted `.spice`, DRC reports |
| **`netgen`** | LVS | Layout Versus Schematic comparison engine | Extracted SPICE, Netlist | Device & net matching report (`.rpt`) |

---

## Exposed MCP Tools

The server registers modular tool suites with FastMCP:

### 1. Environment & Project Management
- **`check_eda_environment()`**: Probes the host system and returns the installation status and paths of all 12 allowlisted EDA tools.
- **`create_project(project_name, top_module)`**: Scaffolds a new project directory structure and initializes `project.json`.
- **`list_projects()`**: Lists all projects present in the managed workspace.

### 2. RTL Authoring & Linting
- **`write_rtl(project_name, file_name, verilog_source)`**: Safely writes synthesizable RTL into the project's `rtl/` folder.
- **`read_design_file(project_name, relative_path)`**: Reads project text files up to 1 MB.
- **`validate_rtl(project_name, top_module, rtl_file)`**: Runs strict static linting via `verilator --lint-only -Wall`.

### 3. Functional & Formal Verification
- **`run_simulation(project_name, testbench_file, top_module, source_files)`**: Compiles with `iverilog` and executes with `vvp`.
- **`run_formal_verification(project_name, config_file, timeout_s)`**: Executes Bounded Model Checking (BMC) or induction via `sby`.
- **`run_equivalence_check(project_name, config_file, timeout_s)`**: Mathematically proves equivalence between revisions with `eqy`.

### 4. Synthesis & Timing
- **`synthesize_design(project_name, top_module, rtl_files)`**: Synthesizes RTL with `yosys` and ABC into `build/synthesized.v`.
- **`analyze_timing(project_name, sta_script, timeout_s)`**: Executes OpenSTA on synthesized netlists using project Tcl constraints.
- **`extract_parasitics(project_name, openroad_script, timeout_s)`**: Runs PDK-level SPEF parasitic extraction using OpenROAD.

### 5. Physical Design & Verification
- **`run_physical_design(project_name, config_file, timeout_s)`**: Runs OpenLane 2 automated RTL-to-GDSII flow using `config/*.json`.
- **`run_openroad_script(project_name, script_file, timeout_s)`**: Runs customized PnR steps using OpenROAD Tcl scripts.
- **`run_klayout_drc(project_name, drc_script, timeout_s)`**: Runs batch 2D geometric Design Rule Checks using KLayout Ruby decks.
- **`run_netgen_lvs(project_name, layout_file, layout_top, schematic_file, schematic_top, setup_file, report_file)`**: Runs Layout Versus Schematic comparison.
- **`inspect_layout(project_name, layout_file)`**: Inspects and validates generated `.gds` or `.oas` layout artifacts.

### 6. Reports & Metrics
- **`get_design_report(project_name, report_file)`**: Reads human-readable reports (`.rpt`) or structured design metrics (`.json`).

---

## End-to-End Design Workflow

An LLM agent can autonomously drive an entire ASIC design cycle:

```
  1. Initialize Workspace
     └─► create_project("alu_8bit", "alu_top")
  
  2. Author RTL & Lint
     ├─► write_rtl("alu_8bit", "alu_top.v", "...")
     └─► validate_rtl("alu_8bit", "alu_top", "rtl/alu_top.v") [Verilator]

  3. Simulate & Verify
     ├─► write_rtl("alu_8bit", "alu_tb.v", "...") (into tb/)
     ├─► run_simulation(...) [Icarus Verilog + VVP]
     └─► run_formal_verification(...) [SymbiYosys]

  4. Synthesize
     └─► synthesize_design("alu_8bit", "alu_top", ["rtl/alu_top.v"]) [Yosys]

  5. Timing Analysis
     └─► analyze_timing("alu_8bit", "config/sta.tcl") [OpenSTA]

  6. Physical Design & Sign-Off
     ├─► run_physical_design("alu_8bit", "config/config.json") [OpenLane 2]
     ├─► run_klayout_drc(...) [KLayout DRC]
     ├─► run_netgen_lvs(...) [Netgen LVS]
     └─► inspect_layout(...) [GDS Validation]

  7. Inspect Reports & Close Loop
     └─► get_design_report("alu_8bit", "reports/metrics.json")
```

---

## Primary Use Cases

1. **Autonomous RTL Debugging & Iteration Loop**:
   The LLM writes Verilog, triggers `run_simulation`, reads failing assertion or compilation logs from the tool return, identifies logic bugs, and rewrites the RTL until all testbench vectors pass.
2. **Formal Verification Property Proving**:
   Rather than manually writing testbenches, the agent writes formal SystemVerilog Assertions (`assert property (...)`), configures SymbiYosys, and proves properties across arbitrary cycles.
3. **Synthesis Optimization & Architecture Exploration**:
   The agent tests multiple Verilog coding architectures (e.g., carry-lookahead vs. ripple-carry adders), synthesizes both with Yosys, and compares gate count, area, and cell statistics.
4. **Timing Closure Assistant**:
   The agent parses OpenSTA slack reports, identifies critical timing paths, calculates negative slack (WNS/TNS), and inserts pipeline register stages into the RTL to achieve target clock frequencies.
5. **RTL-to-GDSII Physical Implementation**:
   Orchestrating end-to-end chip layouts through OpenLane 2, verifying DRC cleanliness and LVS equivalence against the golden schematic netlist.
6. **Educational & Interactive Hardware Companion**:
   Assisting students and digital designers by explaining timing violations, synthesis warnings, and DRC errors in real time with actual tool runs.

---

## Installation & Prerequisites

### 1. System Requirements
- Linux or **Windows Subsystem for Linux (WSL2 with Ubuntu 22.04 or 24.04)**.
- `uv` (fast Python package manager) or Python `>= 3.11`.

### 2. Install EDA Toolchain
Install the open-source EDA tool packages in your Linux/WSL environment:

```bash
sudo apt update
sudo apt install -y curl ca-certificates build-essential \
  iverilog verilator yosys klayout netgen magic
```

*(For full backend flows, install OpenLane 2 and OpenROAD according to their official PDK installation guides for SkyWater 130nm or IHP 130nm).*

### 3. Install `uv` (Recommended)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Running the Server

### Direct Execution with `uv`
The repository includes a launcher script (`run_mcp.sh`) that uses `uv` to manage an isolated, cached environment on the fly without manual virtual environments:

```bash
chmod +x run_mcp.sh
./run_mcp.sh
```

### Running Tests
To run the automated test suite:

```bash
uv run --with-editable . -- pytest
```

---

## Claude Desktop Integration (Windows + WSL)

If your EDA tools and repository reside in WSL, configure Claude Desktop for Windows to communicate with the WSL server via stdio.

Add or merge the following into `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "eda-mcp": {
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

> [!IMPORTANT]
> - Ensure `run_mcp.sh` has executable permissions (`chmod +x run_mcp.sh`).
> - Restart Claude Desktop completely (quit from the Windows system tray) after updating the configuration.

---

## PDK & Integration Notes

- **Process Design Kits (PDKs)**: OpenLane, OpenSTA, KLayout DRC, Magic DRC, and Netgen LVS configurations require target-specific technology files (LEF, GDS, tech files, and rule decks).
- Common supported open-source PDKs:
  - **SkyWater SKY130** (130nm CMOS)
  - **IHP SG13G2** (130nm BiCMOS)
  - **SCL 180nm**
- Place your PDK rule decks, `.lib` timing libraries, and `.sdc` timing constraints in your project's `config/` and `constraints/` folders to enable physical sign-off.
