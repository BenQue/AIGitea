#!/usr/bin/env bash
# Report whether the Claude-side Matt plugin is the commit this repository pins.
# Read-only; do not create caches, temporary files or report files.
#
#   check-plugin-pin.sh --source-only   marketplace entry == vendor manifest == installer version
#   check-plugin-pin.sh [target-home]   the above, then the plugin records under target-home
#
# Separate from check-drift.sh on purpose: that one compares the skills this
# repository installs, this one inspects a plugin Claude Code installs itself.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$ROOT/skill-for-claude/check-plugin-pin.py" "$@"
