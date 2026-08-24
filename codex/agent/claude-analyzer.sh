#!/usr/bin/env bash
# One read-only Claude analyzer turn; the deterministic wrapper owns all mutation.
set -euo pipefail

ISSUE_FILE="${1:-}"
RESULT_FILE="${2:-}"
REPO="${3:-}"
if [[ ! -r "$ISSUE_FILE" || -z "$RESULT_FILE" || ! -d "$REPO" ]]; then
  echo 'usage: claude-analyzer.sh ISSUE_JSON RESULT_JSON REPO' >&2
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
  --permission-mode plan
)
if [[ -n "${CLAUDE_MODEL:-}" ]]; then
  args+=(--model "$CLAUDE_MODEL")
fi

{
  printf '%s\n' \
    'Analyze this Issue in read-only mode for the AISoft platform.' \
    'Read AGENTS.md, relevant code, tests, and the Issue JSON below.' \
    'Do not edit files or mutate Git/Gitea state.' \
    'Return only one JSON object with exactly these fields:' \
    '{"classification":"the canonical classification YAML string","document_slug":"two-to-four-short-words","problem_summary":"...","impact":"...","approach":"...","risks":["..."],"evidence":["repo evidence"],"missing_acceptance_criteria":[]}' \
    'The classification YAML must use semantic required_docs roles: summary; add spec and plan for complex; add verification when the acceptance evidence cannot be reproduced by diff review and required CI, which always includes deployment and migration but is not limited to them. Omit effective_complexity for needs-human-decision.' \
    'document_slug must be a meaningful lowercase kebab-case slug with 2-4 English words, preferably at most 24 and never more than 32 characters.' \
    '' \
    'ISSUE JSON:'
  cat "$ISSUE_FILE"
} | (cd "$REPO" && claude "${args[@]}") >"$RAW_RESULT"

export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
python3 -m aisoft_loop.cli extract-json "$RAW_RESULT" "$CLEAN_RESULT"
python3 -m aisoft_loop.cli validate-analysis "$CLEAN_RESULT" "$RESULT_FILE"
