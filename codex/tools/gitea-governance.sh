#!/usr/bin/env bash
set -euo pipefail
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$ROOT/codex/runtime${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m aisoft_gitea_governance.cli "$@"
