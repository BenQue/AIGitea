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
case "$IMPLEMENT_PROVIDER" in claude|codex|none) ;; *) echo "invalid IMPLEMENT_PROVIDER=$IMPLEMENT_PROVIDER" >&2; exit 2 ;; esac

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
  if ! analysis_issues="$(list_issues needs-analysis)"; then
    echo 'BLOCKED_EXTERNAL: failed to list needs-analysis Issues' >&2
    exit 20
  fi
  while IFS= read -r issue; do
    [[ -n "$issue" ]] || continue
    if ! "$SCRIPT_DIR/analyze-$ANALYSIS_PROVIDER.sh" "$issue"; then
      echo "BLOCKED_EXTERNAL: $ANALYSIS_PROVIDER analysis #$issue failed" >&2
      exit 20
    fi
  done <<<"$analysis_issues"
fi

if [[ "$IMPLEMENT_PROVIDER" != none ]]; then
  if ! implementation_issues="$(list_issues approved)"; then
    echo 'BLOCKED_EXTERNAL: failed to list approved Issues' >&2
    exit 20
  fi
  while IFS= read -r issue; do
    [[ -n "$issue" ]] || continue
    if ! "$SCRIPT_DIR/loop-controller.sh" "$issue"; then
      echo "BLOCKED_EXTERNAL: $IMPLEMENT_PROVIDER Loop #$issue stopped" >&2
      exit 20
    fi
  done <<<"$implementation_issues"
fi
