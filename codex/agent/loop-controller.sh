#!/usr/bin/env bash
# Prepare one isolated change/N worktree, then run or resume the deterministic controller.
set -euo pipefail

N="${1:-}"
if [[ ! "$N" =~ ^[1-9][0-9]*$ ]]; then
  echo 'issue number must be a positive integer' >&2
  exit 2
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN AGENT_REPO_DIR; do
  if [[ -z "${!name:-}" ]]; then
    printf 'missing environment: %s\n' "$name" >&2
    exit 2
  fi
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${AISOFT_LOOP_RUNTIME_DIR:-$SCRIPT_DIR/../runtime}"
STATE_DIR="${AISOFT_LOOP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop}"
WORKTREE_ROOT="${LOOP_WORKTREE_ROOT:-$STATE_DIR/worktrees}"
WORKTREE="$WORKTREE_ROOT/issue-$N"
BRANCH="change/$N"

install -d -m 700 "$STATE_DIR" "$WORKTREE_ROOT"
git -C "$AGENT_REPO_DIR" fetch -q origin main "$BRANCH"

if [[ ! -e "$WORKTREE/.git" ]]; then
  if git -C "$AGENT_REPO_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$AGENT_REPO_DIR" worktree add "$WORKTREE" "$BRANCH"
  else
    git -C "$AGENT_REPO_DIR" worktree add -b "$BRANCH" "$WORKTREE" "origin/$BRANCH"
  fi
fi

current_branch="$(git -C "$WORKTREE" branch --show-current)"
if [[ "$current_branch" != "$BRANCH" ]]; then
  printf 'controller worktree branch mismatch: expected %s, got %s\n' \
    "$BRANCH" "${current_branch:-detached}" >&2
  exit 2
fi

export AISOFT_LOOP_STATE_DIR="$STATE_DIR"
export CODEX_PROVIDER_SCRIPT="${CODEX_PROVIDER_SCRIPT:-$SCRIPT_DIR/codex-provider.sh}"
export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m aisoft_loop.cli run "$N" --repo "$WORKTREE"
