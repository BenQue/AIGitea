#!/usr/bin/env bash
set -euo pipefail

# Do not inherit caller-provided xtrace across credential loading or API calls.
# The token is intentionally transported to curl through stdin configuration,
# never through argv, stdout, or stderr.
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/codex/config/gitea-labels.json"
ENV_FILE="${AGENT_ENV_FILE:-$HOME/.agent.env}"

# Shared token resolution (#111): same-directory copy first (flat VM install
# layout), then the repository layout.
TOOL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$TOOL_DIR/gitea-token.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/gitea-token.sh"
elif [[ -f "$TOOL_DIR/../agent/gitea-token.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/../agent/gitea-token.sh"
else
  echo 'shared gitea token resolver is unavailable' >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo 'agent environment file is required' >&2
  exit 1
fi

# The environment file is trusted configuration. Suppress its standard output so
# this command's successful output remains a single machine-readable summary.
# shellcheck disable=SC1090
source "$ENV_FILE" >/dev/null 2>&1
set +x

require_env() {
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      printf '%s is required\n' "$name" >&2
      exit 1
    fi
  done
}

require_env GITEA_URL GITEA_OWNER GITEA_REPO

token_rc=0
aisoft_resolve_gitea_token || token_rc=$?
if [[ "$token_rc" -eq 1 ]]; then
  echo 'GITEA_TOKEN_FILE or GITEA_TOKEN is required' >&2
  exit 1
elif [[ "$token_rc" -ne 0 ]]; then
  exit "$token_rc"
fi

if ! command -v jq >/dev/null; then
  echo 'jq is required' >&2
  exit 1
fi
if ! command -v curl >/dev/null; then
  echo 'curl is required' >&2
  exit 1
fi

API="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"

curl_with_auth() {
  printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
    curl --config - "$@"
}

current_labels="$(
  curl_with_auth --fail --silent --show-error \
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

  curl_with_auth --fail --silent --show-error \
    --output /dev/null \
    --request POST \
    --header 'Content-Type: application/json' \
    --data "$label" \
    "$API/labels"
  created=$((created + 1))
done < <(jq -c '.[]' "$MANIFEST")

existing=$((existing + created))
printf 'created=%d existing=%d\n' "$created" "$existing"
