#!/usr/bin/env bash
# Versioned platform usage bundle (#377, ADR 0001 D7): verify, release, build
# and per-project status. See codex/tools/usage-bundle.py for the contract.
#
#   usage-bundle.sh --verify                       platform CI gate
#   usage-bundle.sh --release VERSION --today D    append a release
#   usage-bundle.sh --build DIR                    export the latest release
#   usage-bundle.sh --project-status REPO          read-only, for aisoft-project-check.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$ROOT/codex/tools/usage-bundle.py" "$@"
