#!/usr/bin/env bash
# Report external skill pack versions on both providers against the last
# 08 §5 adaptation record (#375). Read-only; do not create caches, temporary
# files or report files, and never install or fetch anything.
#
#   check-external-skill-versions.sh --source-only   adaptation record structure only
#   check-external-skill-versions.sh [--home <dir>]  CLIs, superpowers on both sides, Matt pin
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$ROOT/codex/tools/check-external-skill-versions.py" "$@"
