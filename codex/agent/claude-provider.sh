#!/usr/bin/env bash
# One provider turn: Claude uses Matt implement and owns local commits only.
set -euo pipefail

REQUEST_FILE="${1:-}"
RESULT_FILE="${2:-}"
WORKTREE="${3:-}"
if [[ ! -r "$REQUEST_FILE" || -z "$RESULT_FILE" || ! -d "$WORKTREE" ]]; then
  echo 'usage: claude-provider.sh REQUEST_JSON RESULT_JSON WORKTREE' >&2
  exit 2
fi
command -v claude >/dev/null || { echo 'claude CLI is not installed' >&2; exit 2; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${AISOFT_LOOP_RUNTIME_DIR:-}" ]]; then
  DEFAULT_RUNTIME_DIR="$AISOFT_LOOP_RUNTIME_DIR"
elif [[ -d "$SCRIPT_DIR/../runtime/aisoft_loop" ]]; then
  DEFAULT_RUNTIME_DIR="$SCRIPT_DIR/../runtime"
else
  DEFAULT_RUNTIME_DIR="$HOME/.local/lib/aisoft-loop"
fi
RUNTIME_DIR="$DEFAULT_RUNTIME_DIR"
RAW_RESULT="$(mktemp)"
CLEAN_RESULT="$(mktemp)"
trap 'rm -f "$RAW_RESULT" "$CLEAN_RESULT"' EXIT

args=(
  --print
  --output-format text
  --permission-mode acceptEdits
)
if [[ -n "${CLAUDE_MODEL:-}" ]]; then
  args+=(--model "$CLAUDE_MODEL")
fi

{
  printf '%s\n' \
    "Use \$implement for exactly one bounded provider turn for the AISoft Development Loop." \
    'Read AGENTS.md and the immutable request JSON below.' \
    'Work only inside the requested contract. Run useful local checks, but do not claim they replace the outer verifier.' \
    'Commit the verified ticket changes to the current exact readable change branch using the request commit requirements.' \
    'Do not edit any governing AGENTS.md. Do not push, change Issue labels, open/merge a PR, rebase, force-push, or deploy.' \
    'Finish with only one JSON object using exactly these fields:' \
    '{"status":"CONTINUE|COMPLETE|NEEDS_HUMAN_DECISION|BLOCKED_EXTERNAL","summary":"...","changed_files":["relative/path"],"root_cause":"","escalation":""}' \
    '' \
    'REQUEST JSON:'
  cat "$REQUEST_FILE"
} | claude "${args[@]}" >"$RAW_RESULT"

export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
python3 -m aisoft_loop.cli extract-json "$RAW_RESULT" "$CLEAN_RESULT"
python3 -m aisoft_loop.cli validate-provider "$CLEAN_RESULT" "$RESULT_FILE"
