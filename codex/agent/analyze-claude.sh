#!/usr/bin/env bash
# Analyze one Issue, render its named summary on change/N, then apply deterministic routing.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

N="${1:-}"
require_issue_number "$N"
load_agent_env
RUNTIME_DIR="$(runtime_dir "$SCRIPT_DIR")"
export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"

WORKTREE="$(prepare_change_worktree "$N" true)"
if [[ -n "$(git -C "$WORKTREE" status --porcelain)" ]]; then
  echo 'analysis worktree is dirty; refusing to overwrite it' >&2
  exit 2
fi

ISSUE_FILE="$(mktemp)"
RESULT_FILE="$(mktemp)"
trap 'rm -f "$ISSUE_FILE" "$RESULT_FILE"' EXIT
python3 -m aisoft_loop.cli get-issue "$N" "$ISSUE_FILE"
"$SCRIPT_DIR/claude-analyzer.sh" "$ISSUE_FILE" "$RESULT_FILE" "$WORKTREE"

SUMMARY_DIR="$WORKTREE/docs/changes/$N"
SUMMARY_FILE="$(python3 -m aisoft_loop.cli render-analysis "$ISSUE_FILE" "$RESULT_FILE" "$SUMMARY_DIR")"
[[ "$SUMMARY_FILE" == "$SUMMARY_DIR"/summary-*.md ]] || {
  echo 'rendered summary path violates the named document contract' >&2
  exit 2
}
SUMMARY_NAME="${SUMMARY_FILE##*/}"
git -C "$WORKTREE" add "docs/changes/$N/$SUMMARY_NAME"
if ! git -C "$WORKTREE" diff --cached --quiet; then
  git -C "$WORKTREE" commit -m "docs: analyze issue #$N"
fi
git -C "$WORKTREE" push -u origin "change/$N"

SUMMARY_URL="$GITEA_URL/$GITEA_OWNER/$GITEA_REPO/src/branch/change%2F$N/docs/changes/$N/$SUMMARY_NAME"
python3 -m aisoft_loop.cli apply-analysis "$N" "$RESULT_FILE" "$SUMMARY_URL"
printf 'Claude analysis completed for Issue #%s on change/%s\n' "$N" "$N"
