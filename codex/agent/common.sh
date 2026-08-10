#!/usr/bin/env bash
# Shared environment and isolated worktree helpers. Never constructs auth argv.
set -euo pipefail

secure_agent_file() {
  local path="$1" label="$2" metadata mode
  [[ -f "$path" && ! -L "$path" ]] || {
    printf 'BLOCKED_EXTERNAL: %s must be a regular non-symlink file\n' "$label" >&2
    return 20
  }
  if metadata="$(stat -f '%Lp' "$path" 2>/dev/null)"; then
    mode="$metadata"
  else
    mode="$(stat -c '%a' "$path")"
  fi
  case "$mode" in
    400|600) ;;
    *)
      printf 'BLOCKED_EXTERNAL: %s mode must be 400 or 600\n' "$label" >&2
      return 20
      ;;
  esac
}

require_issue_number() {
  if [[ ! "${1:-}" =~ ^[1-9][0-9]*$ ]]; then
    echo 'issue number must be a positive integer' >&2
    exit 2
  fi
}

load_agent_env() {
  local env_file="${AGENT_ENV_FILE:-$HOME/.agent.env}"
  set +x
  secure_agent_file "$env_file" 'project profile' || exit $?
  [[ -r "$env_file" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: project profile is not readable' >&2
    exit 20
  }
  unset GITEA_TOKEN
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  local name
  for name in AISOFT_PROJECT_ID GITEA_URL GITEA_OWNER GITEA_REPO GITEA_IDENTITY GITEA_TOKEN_FILE; do
    if [[ -z "${!name:-}" ]]; then
      printf 'BLOCKED_EXTERNAL: missing project profile field: %s\n' "$name" >&2
      exit 20
    fi
  done
  [[ -z "${GITEA_TOKEN:-}" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: inline GITEA_TOKEN is forbidden; use the fixed token file' >&2
    exit 20
  }
  secure_agent_file "$GITEA_TOKEN_FILE" 'project token file' || exit $?
  GITEA_TOKEN="$(<"$GITEA_TOKEN_FILE")"
  [[ "$GITEA_TOKEN" =~ ^[A-Za-z0-9._-]+$ ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: project token format is invalid' >&2
    exit 20
  }
  export GITEA_TOKEN
  AGENT_REPO_DIR="${AGENT_REPO_DIR:-$HOME/work/$GITEA_REPO}"
  export AGENT_REPO_DIR
}

host_access_manifest() {
  local script_dir="$1"
  if [[ -f "$script_dir/../config/host-access-broker.json" ]]; then
    printf '%s\n' "$script_dir/../config/host-access-broker.json"
  else
    printf '%s\n' "$HOME/.local/share/aisoft/host-access-broker.json"
  fi
}

governance_manifest() {
  local script_dir="$1"
  if [[ -f "$script_dir/../config/gitea-governance.json" ]]; then
    printf '%s\n' "$script_dir/../config/gitea-governance.json"
  else
    printf '%s\n' "$HOME/.local/share/aisoft/gitea-governance.json"
  fi
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
  local issue="$1" allow_create="${2:-false}" slug="${3:-}"
  local state_dir worktree_root worktree branch expected_branch="" remote_exists=false
  local output ref parsed_branch
  local -a branches=()
  require_issue_number "$issue"
  state_dir="${AISOFT_LOOP_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop}"
  worktree_root="${LOOP_WORKTREE_ROOT:-$state_dir/worktrees}"
  install -d -m 700 "$state_dir" "$worktree_root"
  git -C "$AGENT_REPO_DIR" fetch -q origin main
  if [[ -n "$slug" ]]; then
    expected_branch="$(python3 -m aisoft_loop.cli change-name "$issue" "$slug")"
  fi
  if ! output="$(git -C "$AGENT_REPO_DIR" ls-remote --heads origin \
    "refs/heads/change/$issue" "refs/heads/change/$issue-*")"; then
    printf 'cannot enumerate remote change names for Issue #%s\n' "$issue" >&2
    exit 2
  fi
  while IFS=$'\t' read -r _ ref; do
    [[ -n "$ref" ]] || continue
    if [[ "$ref" == "refs/heads/change/$issue" || \
          "$ref" == "refs/heads/change/$issue-"* ]]; then
      if ! parsed_branch="$(python3 -m aisoft_loop.cli parse-change-branch \
        "${ref#refs/heads/}")"; then
        printf 'invalid remote change ref for Issue #%s\n' "$issue" >&2
        exit 2
      fi
      branches+=("$parsed_branch")
    fi
  done <<<"$output"
  if (( ${#branches[@]} > 1 )); then
    printf 'CHANGE_NAME_CONFLICT for Issue #%s: %s\n' "$issue" "${branches[*]}" >&2
    exit 2
  elif (( ${#branches[@]} == 1 )); then
    branch="${branches[0]}"
    remote_exists=true
    if [[ -n "$expected_branch" && "$branch" != "$expected_branch" ]]; then
      printf 'CHANGE_NAME_CONFLICT for Issue #%s: expected %s, found %s\n' \
        "$issue" "$expected_branch" "$branch" >&2
      exit 2
    fi
  elif [[ "$allow_create" == true && -n "$expected_branch" ]]; then
    branch="$expected_branch"
  else
    printf 'remote change branch for Issue #%s is missing\n' "$issue" >&2
    exit 2
  fi
  worktree="$worktree_root/issue-${branch#change/}"
  if [[ "$remote_exists" == true ]]; then
    git -C "$AGENT_REPO_DIR" fetch -q origin "$branch"
  fi
  if [[ ! -e "$worktree/.git" ]]; then
    if git -C "$AGENT_REPO_DIR" show-ref --verify --quiet "refs/heads/$branch"; then
      if [[ "$remote_exists" == true ]]; then
        git -C "$AGENT_REPO_DIR" branch -f "$branch" "origin/$branch" >/dev/null
      fi
      git -C "$AGENT_REPO_DIR" worktree add "$worktree" "$branch" >/dev/null
    elif [[ "$remote_exists" == true ]]; then
      git -C "$AGENT_REPO_DIR" worktree add -b "$branch" "$worktree" "origin/$branch" >/dev/null
    elif [[ "$allow_create" == true ]]; then
      git -C "$AGENT_REPO_DIR" worktree add -b "$branch" "$worktree" origin/main >/dev/null
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
