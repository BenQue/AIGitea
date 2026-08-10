#!/usr/bin/env bash
# Resolve one evidence-backed change name, prepare its isolated worktree, then run the controller.
set -euo pipefail
set +x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
N="${1:-}"
require_issue_number "$N"
load_agent_env
RUNTIME_DIR="$(runtime_dir "$SCRIPT_DIR")"
STATE_DIR="${AISOFT_LOOP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop}"
WORKTREE="$(prepare_change_worktree "$N" false)"

export AISOFT_LOOP_STATE_DIR="$STATE_DIR"
export CODEX_PROVIDER_SCRIPT="${CODEX_PROVIDER_SCRIPT:-$SCRIPT_DIR/codex-provider.sh}"
export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m aisoft_loop.cli run "$N" --repo "$WORKTREE"
