#!/usr/bin/env bash
set -euo pipefail
set +x

enabled=true
if [ "${1:-}" = "--disable" ]; then
  enabled=false
  shift
fi
[ "$#" -eq 0 ] || { echo "usage: $0 [--disable]" >&2; exit 2; }

for name in GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN; do
  [ -n "${!name:-}" ] || { printf '%s is required\n' "$name" >&2; exit 2; }
done
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
