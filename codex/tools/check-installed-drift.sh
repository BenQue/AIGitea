#!/usr/bin/env bash
# Read-only; do not create caches, temporary files or report files.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$ROOT/codex/tools/check-installed-drift.py" "$@"
