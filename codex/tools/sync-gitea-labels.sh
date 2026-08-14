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

# Shared canonical label manifest access (#108), same dual-path convention.
if [[ -f "$TOOL_DIR/gitea-label-manifest.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/gitea-label-manifest.sh"
elif [[ -f "$TOOL_DIR/../agent/gitea-label-manifest.sh" ]]; then
  # shellcheck disable=SC1090,SC1091
  source "$TOOL_DIR/../agent/gitea-label-manifest.sh"
else
  echo 'shared gitea label manifest library is unavailable' >&2
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

# Validate before the first API call so a malformed manifest can never leave the
# remote repository half-provisioned.
aisoft_label_manifest_validate "$MANIFEST"

API="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"

curl_with_auth() {
  printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
    curl --config - "$@"
}

# Read every page rather than assuming one. The safety bound mirrors the
# labels-readback check in aisoft-project-check.sh.
PAGE_SIZE=50
MAX_PAGES=20

current_labels='[]'
page=1
while ((page <= MAX_PAGES)); do
  page_body="$(
    curl_with_auth --fail --silent --show-error \
      "$API/labels?limit=$PAGE_SIZE&page=$page"
  )"
  if ! jq -e 'type == "array" and all(.[];
    (.name | type == "string") and
    (.color | type == "string") and
    (.description | type == "string"))' <<<"$page_body" >/dev/null 2>&1; then
    echo 'remote label response is not in the expected shape' >&2
    exit 1
  fi
  current_labels="$(jq -c -s '.[0] + .[1]' <<<"$current_labels"$'\n'"$page_body")"
  page_count="$(jq 'length' <<<"$page_body")"
  ((page_count < PAGE_SIZE)) && break
  page=$((page + 1))
done
if ((page > MAX_PAGES)); then
  echo 'remote label pagination exceeded the safety bound' >&2
  exit 1
fi

# Gitea accepts colors with or without a leading '#' and in either case; compare
# on a normalized form so cosmetic differences never look like drift and never
# trigger an endless repair loop.
normalize() {
  jq -c '{
    name: .name,
    color: (.color | ltrimstr("#") | ascii_downcase),
    description: (.description | sub("^\\s+"; "") | sub("\\s+$"; ""))
  }'
}

created=0
updated=0
unchanged=0
while IFS= read -r label; do
  name="$(jq -r '.name' <<<"$label")"
  remote="$(
    jq -c --arg name "$name" 'map(select(.name == $name)) | first // empty' \
      <<<"$current_labels"
  )"

  if [[ -z "$remote" ]]; then
    curl_with_auth --fail --silent --show-error \
      --output /dev/null \
      --request POST \
      --header 'Content-Type: application/json' \
      --data "$label" \
      "$API/labels"
    created=$((created + 1))
    continue
  fi

  want="$(normalize <<<"$label")"
  have="$(jq -c '{name, color, description}' <<<"$remote" | normalize)"
  if [[ "$want" == "$have" ]]; then
    unchanged=$((unchanged + 1))
    continue
  fi

  label_id="$(jq -r '.id' <<<"$remote")"
  if [[ -z "$label_id" || "$label_id" == 'null' ]]; then
    printf 'remote label %s has no id; cannot repair drift\n' "$name" >&2
    exit 1
  fi
  curl_with_auth --fail --silent --show-error \
    --output /dev/null \
    --request PATCH \
    --header 'Content-Type: application/json' \
    --data "$label" \
    "$API/labels/$label_id"
  updated=$((updated + 1))
done < <(aisoft_label_manifest_canonical "$MANIFEST")

# Retired values are reported, never deleted. There is deliberately no DELETE
# path in this tool: migrating a retired label off the Issues that still carry
# it is a human decision, and a tool that could silently remove it would make
# that decision invisible (#108 AC-7).
retired_present=0
while IFS= read -r retired_name; do
  [[ -n "$retired_name" ]] || continue
  if jq -e --arg name "$retired_name" 'any(.[]; .name == $name)' \
    <<<"$current_labels" >/dev/null; then
    printf 'NOTICE: retired label %s still exists remotely; migrate its Issues before removing it by hand\n' \
      "$retired_name" >&2
    retired_present=$((retired_present + 1))
  fi
done < <(aisoft_label_manifest_retired "$MANIFEST")

printf 'created=%d updated=%d unchanged=%d retired_present=%d\n' \
  "$created" "$updated" "$unchanged" "$retired_present"
