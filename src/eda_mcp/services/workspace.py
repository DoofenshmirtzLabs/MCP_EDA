from pathlib import Path
import re
from eda_mcp.config import WORKSPACE_ROOT

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_FILE = re.compile(r"^[A-Za-z0-9_./-]{1,180}$")

def validate_name(name: str) -> str:
    if not _NAME.fullmatch(name) or name in {".", ".."}:
        raise ValueError("Invalid project name. Use letters, numbers, dot, dash or underscore.")
    return name

def project_dir(project_name: str) -> Path:
    name = validate_name(project_name)
    path = (WORKSPACE_ROOT / name).resolve()
    if path.parent != WORKSPACE_ROOT:
        raise ValueError("Project path escapes workspace.")
    return path

def project_file(project_name: str, relative_path: str) -> Path:
    base = project_dir(project_name)
    if not _FILE.fullmatch(relative_path):
        raise ValueError("Invalid relative file path.")
    candidate = (base / relative_path).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("File path escapes project directory.")
    return candidate
