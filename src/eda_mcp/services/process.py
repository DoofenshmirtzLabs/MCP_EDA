import asyncio
import shutil
from pathlib import Path
from typing import Sequence

from eda_mcp.config import EXECUTABLES, LOG_ROOT, WORKSPACE_ROOT

async def run_eda(
    tool: str,
    args: Sequence[str],
    cwd: Path,
    timeout_s: int = 120,
) -> dict:
    """Run one allowlisted EDA executable without a shell."""
    if tool not in EXECUTABLES:
        raise ValueError(f"Executable is not allowlisted: {tool}")
    executable = shutil.which(EXECUTABLES[tool])
    if executable is None:
        return {
            "status": "unavailable",
            "tool": tool,
            "message": f"{tool} is not installed or is not on PATH.",
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }

    cwd = cwd.resolve()
    if cwd != WORKSPACE_ROOT and WORKSPACE_ROOT not in cwd.parents:
        raise ValueError("EDA commands may only run inside the EDA workspace.")

    proc = await asyncio.create_subprocess_exec(
        executable,
        *[str(x) for x in args],
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        status = "success" if proc.returncode == 0 else "failed"
        return {
            "status": status,
            "tool": tool,
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace")[-20000:],
            "stderr": stderr.decode(errors="replace")[-20000:],
        }
    except asyncio.TimeoutError:
        proc.kill()
        stdout, stderr = await proc.communicate()
        return {
            "status": "timeout",
            "tool": tool,
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace")[-20000:],
            "stderr": stderr.decode(errors="replace")[-20000:],
            "message": f"Process exceeded {timeout_s} seconds and was terminated.",
        }

def executable_status() -> dict:
    return {
        key: {"installed": shutil.which(exe) is not None, "path": shutil.which(exe)}
        for key, exe in EXECUTABLES.items()
    }
