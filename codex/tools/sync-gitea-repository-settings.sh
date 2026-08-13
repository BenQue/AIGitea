#!/usr/bin/env bash
set -euo pipefail
set +x

enabled=true
if [ "${1:-}" = "--disable" ]; then
  enabled=false
  shift
fi
[ "$#" -eq 0 ] || { echo "usage: $0 [--disable]" >&2; exit 2; }

# Shared token resolution (#111): same-directory copy first (flat VM install
# layout), then the repository layout.
TOOL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$TOOL_DIR/gitea-token.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$TOOL_DIR/gitea-token.sh"
elif [ -f "$TOOL_DIR/../agent/gitea-token.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$TOOL_DIR/../agent/gitea-token.sh"
else
  echo 'shared gitea token resolver is unavailable' >&2
  exit 1
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO; do
  [ -n "${!name:-}" ] || { printf '%s is required\n' "$name" >&2; exit 2; }
done
token_rc=0
aisoft_resolve_gitea_token || token_rc=$?
if [ "$token_rc" -eq 1 ]; then
  echo 'GITEA_TOKEN_FILE or GITEA_TOKEN is required' >&2
  exit 2
elif [ "$token_rc" -ne 0 ]; then
  exit "$token_rc"
fi
command -v curl >/dev/null || { echo "curl is required" >&2; exit 2; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 2; }

api="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
curl_auth() {
  printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
    curl --config - "$@"
}

payload="$(jq -cn --argjson enabled "$enabled" \
  '{default_delete_branch_after_merge:$enabled}')"
curl_auth --fail --silent --show-error --output /dev/null \
  --request PATCH --header 'Content-Type: application/json' \
  --data "$payload" "$api"
actual="$(
  curl_auth --fail --silent --show-error "$api" |
    jq -r '.default_delete_branch_after_merge'
)"
[ "$actual" = "$enabled" ] || {
  printf 'repository setting read-back mismatch: expected=%s actual=%s\n' \
    "$enabled" "$actual" >&2
  exit 1
}
printf 'default_delete_branch_after_merge=%s\n' "$actual"
