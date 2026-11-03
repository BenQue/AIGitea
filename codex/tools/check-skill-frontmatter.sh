#!/usr/bin/env bash
# Parse every platform skill's frontmatter (and agents/*.yaml) with a real,
# strict YAML parser (#438). Read-only; writes no caches or report files.
#
#   check-skill-frontmatter.sh [--root DIR]   default: this repository
#
# Exit 0 PASS, 1 a skill fails, 2 no YAML backend or a usage error.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B "$ROOT/codex/tools/check-skill-frontmatter.py" --default-root "$ROOT" "$@"
