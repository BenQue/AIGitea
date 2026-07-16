#!/usr/bin/env bash
# Select one project profile, namespace its state, then run the shared poller.
set -euo pipefail
set +x

PROFILE="${1:-}"
if [[ ! "$PROFILE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]]; then
  echo 'project profile must use 1-64 letters, digits, dots, underscores, or hyphens' >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_ROOT="${AISOFT_PROJECT_CONFIG_ROOT:-$HOME/.config/aisoft/projects}"
ENV_FILE="$CONFIG_ROOT/$PROFILE.env"
if [[ ! -r "$ENV_FILE" ]]; then
  printf 'project profile is not readable: %s\n' "$ENV_FILE" >&2
  exit 2
fi
if mode="$(stat -f '%Lp' "$ENV_FILE" 2>/dev/null)"; then
  :
else
  mode="$(stat -c '%a' "$ENV_FILE")"
fi
case "$mode" in
  400|600) ;;
  *)
    printf 'project profile must have mode 400 or 600, got %s\n' "$mode" >&2
    exit 2
    ;;
esac

PROJECT_STATE_ROOT="${AISOFT_PROJECT_STATE_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop/projects}"
export AGENT_ENV_FILE="$ENV_FILE"
export AISOFT_LOOP_STATE_DIR="${AISOFT_LOOP_STATE_DIR:-$PROJECT_STATE_ROOT/$PROFILE}"
export LOOP_WORKTREE_ROOT="${LOOP_WORKTREE_ROOT:-$AISOFT_LOOP_STATE_DIR/worktrees}"

exec "$SCRIPT_DIR/provider-poll.sh"
