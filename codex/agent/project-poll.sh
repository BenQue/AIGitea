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
  printf '%s\n' 'BLOCKED_EXTERNAL: project profile is not readable' >&2
  exit 20
fi

# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
secure_agent_file "$ENV_FILE" 'project profile' || exit $?

PROJECT_STATE_ROOT="${AISOFT_PROJECT_STATE_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/aisoft-loop/projects}"
export AGENT_ENV_FILE="$ENV_FILE"
export AISOFT_LOOP_STATE_DIR="${AISOFT_LOOP_STATE_DIR:-$PROJECT_STATE_ROOT/$PROFILE}"
export LOOP_WORKTREE_ROOT="${LOOP_WORKTREE_ROOT:-$AISOFT_LOOP_STATE_DIR/worktrees}"

RUNTIME_DIR="$(runtime_dir "$SCRIPT_DIR")"
ACCESS_MANIFEST="$(host_access_manifest "$SCRIPT_DIR")"
GOVERNANCE_MANIFEST="$(governance_manifest "$SCRIPT_DIR")"
[[ -f "$ACCESS_MANIFEST" && -f "$GOVERNANCE_MANIFEST" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: installed host access manifests are missing' >&2
  exit 20
}
export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
if ! python3 -m aisoft_host_access.cli \
  --access-manifest "$ACCESS_MANIFEST" \
  --governance-manifest "$GOVERNANCE_MANIFEST" \
  profile-consume-check --profile-name "$PROFILE" >/dev/null; then
  printf '%s\n' 'BLOCKED_EXTERNAL: project profile identity or target validation failed' >&2
  exit 20
fi

exec "$SCRIPT_DIR/provider-poll.sh"
