#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/\n' >&2
  exit 127
fi
exec uv run --no-project --with-editable . -- python -m eda_mcp.server
