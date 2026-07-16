#!/usr/bin/env bash
# Single poller: analyzer and controller are explicitly selected; no automatic fallback.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
load_agent_env

ANALYSIS_PROVIDER="${ANALYSIS_PROVIDER:-none}"
IMPLEMENT_PROVIDER="${IMPLEMENT_PROVIDER:-none}"
case "$ANALYSIS_PROVIDER" in claude|codex|none) ;; *) echo "invalid ANALYSIS_PROVIDER=$ANALYSIS_PROVIDER" >&2; exit 2 ;; esac
case "$IMPLEMENT_PROVIDER" in codex|none) ;; *) echo 'Claude implementation remains disabled until Codex parity passes' >&2; exit 2 ;; esac

RUNTIME_DIR="$(runtime_dir "$SCRIPT_DIR")"
STATE_DIR="${AISOFT_LOOP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop}"
install -d -m 700 "$STATE_DIR"
export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
if command -v flock >/dev/null; then
  exec 9>"$STATE_DIR/poll.lock"
  flock -n 9 || { echo 'previous poll is still running; skipping'; exit 0; }
else
  POLL_LOCK_DIR="$STATE_DIR/poll.lock.d"
  mkdir "$POLL_LOCK_DIR" 2>/dev/null || { echo 'previous poll is still running; skipping'; exit 0; }
  trap 'rmdir "$POLL_LOCK_DIR" 2>/dev/null || true' EXIT
fi

list_issues() {
  python3 -m aisoft_loop.cli list-issues "$1"
}

if [[ "$ANALYSIS_PROVIDER" != none ]]; then
  while IFS= read -r issue; do
    [[ -n "$issue" ]] || continue
    if [[ "$ANALYSIS_PROVIDER" == codex ]]; then
      "$SCRIPT_DIR/analyze-codex.sh" "$issue" || echo "Codex analysis #$issue failed" >&2
    else
      "$SCRIPT_DIR/analyze.sh" "$issue" || echo "Claude analysis #$issue failed" >&2
    fi
  done < <(list_issues needs-analysis)
fi

if [[ "$IMPLEMENT_PROVIDER" == codex ]]; then
  while IFS= read -r issue; do
    [[ -n "$issue" ]] || continue
    "$SCRIPT_DIR/loop-controller.sh" "$issue" || echo "Codex Loop #$issue stopped" >&2
  done < <(list_issues approved)
fi
