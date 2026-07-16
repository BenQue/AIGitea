#!/usr/bin/env bash
# Shared environment and isolated worktree helpers. Never constructs auth argv.
set -euo pipefail

require_issue_number() {
  if [[ ! "${1:-}" =~ ^[1-9][0-9]*$ ]]; then
    echo 'issue number must be a positive integer' >&2
    exit 2
  fi
}

load_agent_env() {
  local env_file="${AGENT_ENV_FILE:-$HOME/.agent.env}"
  set +x
  if [[ ! -r "$env_file" ]]; then
    printf 'agent environment is not readable: %s\n' "$env_file" >&2
    exit 2
  fi
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  local name
  for name in GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN; do
    if [[ -z "${!name:-}" ]]; then
      printf 'missing environment: %s\n' "$name" >&2
      exit 2
    fi
  done
  AGENT_REPO_DIR="${AGENT_REPO_DIR:-$HOME/work/$GITEA_REPO}"
  export AGENT_REPO_DIR
}

runtime_dir() {
  local script_dir="$1"
  if [[ -n "${AISOFT_LOOP_RUNTIME_DIR:-}" ]]; then
    printf '%s\n' "$AISOFT_LOOP_RUNTIME_DIR"
  elif [[ -d "$script_dir/../runtime/aisoft_loop" ]]; then
    printf '%s\n' "$script_dir/../runtime"
  else
    printf '%s\n' "$HOME/.local/lib/aisoft-loop"
  fi
}

prepare_change_worktree() {
  local issue="$1" allow_create="${2:-false}"
  local state_dir worktree_root worktree branch remote_exists=false
  require_issue_number "$issue"
  state_dir="${AISOFT_LOOP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop}"
  worktree_root="${LOOP_WORKTREE_ROOT:-$state_dir/worktrees}"
  worktree="$worktree_root/issue-$issue"
  branch="change/$issue"
  install -d -m 700 "$state_dir" "$worktree_root"
  git -C "$AGENT_REPO_DIR" fetch -q origin main
  if git -C "$AGENT_REPO_DIR" fetch -q origin "$branch"; then
    remote_exists=true
  fi
  if [[ ! -e "$worktree/.git" ]]; then
    if git -C "$AGENT_REPO_DIR" show-ref --verify --quiet "refs/heads/$branch"; then
      if [[ "$remote_exists" == true ]]; then
        git -C "$AGENT_REPO_DIR" branch -f "$branch" "origin/$branch" >/dev/null
      fi
      git -C "$AGENT_REPO_DIR" worktree add "$worktree" "$branch"
    elif [[ "$remote_exists" == true ]]; then
      git -C "$AGENT_REPO_DIR" worktree add -b "$branch" "$worktree" "origin/$branch"
    elif [[ "$allow_create" == true ]]; then
      git -C "$AGENT_REPO_DIR" worktree add -b "$branch" "$worktree" origin/main
    else
      printf 'remote branch %s is missing\n' "$branch" >&2
      exit 2
    fi
  fi
  local current
  current="$(git -C "$worktree" branch --show-current)"
  if [[ "$current" != "$branch" ]]; then
    printf 'worktree branch mismatch: expected %s, got %s\n' \
      "$branch" "${current:-detached}" >&2
    exit 2
  fi
  printf '%s\n' "$worktree"
}
