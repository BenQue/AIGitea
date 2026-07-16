#!/usr/bin/env bash
# One provider turn: Codex may edit the worktree but owns no Git/Gitea/deploy mutation.
set -euo pipefail

REQUEST_FILE="${1:-}"
RESULT_FILE="${2:-}"
WORKTREE="${3:-}"
if [[ ! -r "$REQUEST_FILE" || -z "$RESULT_FILE" || ! -d "$WORKTREE" ]]; then
  echo 'usage: codex-provider.sh REQUEST_JSON RESULT_JSON WORKTREE' >&2
  exit 2
fi
command -v codex >/dev/null || { echo 'codex CLI is not installed' >&2; exit 2; }

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
trap 'rm -f "$RAW_RESULT"' EXIT

args=(
  --ask-for-approval never
  exec
  --cd "$WORKTREE"
  --sandbox workspace-write
  --ephemeral
  --output-last-message "$RAW_RESULT"
)
if [[ -n "${CODEX_MODEL:-}" ]]; then
  args+=(--model "$CODEX_MODEL")
fi

{
  printf '%s\n' \
    "Use \$gitea-development-loop for exactly one bounded provider turn." \
    'Read AGENTS.md and the immutable request JSON below.' \
    'Work only inside the requested contract. Run useful local checks, but do not claim they replace the outer verifier.' \
    'Do not edit any governing AGENTS.md. Do not commit, push, change Issue labels, open/merge a PR, or deploy.' \
    'Finish with only one JSON object using exactly these fields:' \
    '{"status":"CONTINUE|COMPLETE|NEEDS_HUMAN_DECISION|BLOCKED_EXTERNAL","summary":"...","changed_files":["relative/path"],"root_cause":"","escalation":""}' \
    '' \
    'REQUEST JSON:'
  cat "$REQUEST_FILE"
} | codex "${args[@]}" -

PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m aisoft_loop.cli validate-provider "$RAW_RESULT" "$RESULT_FILE"
