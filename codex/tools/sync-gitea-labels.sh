#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/codex/config/gitea-labels.json"
ENV_FILE="${AGENT_ENV_FILE:-$HOME/.agent.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo 'agent environment file is required' >&2
  exit 1
fi

# The environment file is trusted configuration. Suppress its standard output so
# this command's successful output remains a single machine-readable summary.
# shellcheck disable=SC1090
source "$ENV_FILE" >/dev/null

require_env() {
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      printf '%s is required\n' "$name" >&2
      exit 1
    fi
  done
}

require_env GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN

if ! command -v jq >/dev/null; then
  echo 'jq is required' >&2
  exit 1
fi
if ! command -v curl >/dev/null; then
  echo 'curl is required' >&2
  exit 1
fi

API="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
AUTH_HEADER="Authorization: token $GITEA_TOKEN"
current_labels="$(
  curl --fail --silent --show-error \
    --header "$AUTH_HEADER" \
    "$API/labels?limit=100"
)"

created=0
existing=0
while IFS= read -r label; do
  name="$(jq -r '.name' <<<"$label")"
  if jq -e --arg name "$name" 'any(.[]; .name == $name)' <<<"$current_labels" >/dev/null; then
    existing=$((existing + 1))
    continue
  fi

  curl --fail --silent --show-error \
    --output /dev/null \
    --request POST \
    --header "$AUTH_HEADER" \
    --header 'Content-Type: application/json' \
    --data "$label" \
    "$API/labels"
  created=$((created + 1))
done < <(jq -c '.[]' "$MANIFEST")

existing=$((existing + created))
printf 'created=%d existing=%d\n' "$created" "$existing"
