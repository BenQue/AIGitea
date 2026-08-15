#!/usr/bin/env bash
set -u
set +x

warn() {
  printf 'WARN: mark-deployed: %s\n' "$*" >&2
}

# Shared token resolution (#111): same-directory copy first (flat VM install
# layout), then the repository layout. This tool never fails the deployment.
tool_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$tool_dir/gitea-token.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/gitea-token.sh"
elif [ -f "$tool_dir/../agent/gitea-token.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/../agent/gitea-token.sh"
else
  warn "shared gitea token resolver is unavailable; deployment result is unchanged"
  exit 0
fi

# Shared canonical label manifest access (#108), same dual-path convention. The
# lifecycle names this tool strips are derived from the manifest rather than
# transcribed here (#115 AC-7).
if [ -f "$tool_dir/gitea-label-manifest.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/gitea-label-manifest.sh"
elif [ -f "$tool_dir/../agent/gitea-label-manifest.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/../agent/gitea-label-manifest.sh"
else
  warn "shared gitea label manifest library is unavailable; deployment result is unchanged"
  exit 0
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO; do
  if [ -z "${!name:-}" ]; then
    warn "$name is unavailable; deployment result is unchanged"
    exit 0
  fi
done
token_rc=0
aisoft_resolve_gitea_token || token_rc=$?
if [ "$token_rc" -ne 0 ]; then
  warn "usable GITEA_TOKEN_FILE or GITEA_TOKEN is unavailable; deployment result is unchanged"
  exit 0
fi
if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
  warn "curl and jq are required; deployment result is unchanged"
  exit 0
fi

# The lifecycle dimension is read from the canonical manifest, the same source
# the provisioner and the Loop's contract use. A missing or malformed manifest
# joins the other unavailable prerequisites above: warn and leave the already
# successful deployment untouched. It must never fall back to a private copy of
# the names — that copy drifting out of the manifest is the failure this reads
# the manifest to avoid.
if [ -f "$tool_dir/gitea-labels.json" ]; then
  manifest="$tool_dir/gitea-labels.json"
elif [ -f "$tool_dir/../config/gitea-labels.json" ]; then
  manifest="$tool_dir/../config/gitea-labels.json"
else
  warn "label manifest is unavailable; deployment result is unchanged"
  exit 0
fi
manifest_rc=0
aisoft_label_manifest_validate "$manifest" || manifest_rc=$?
if [ "$manifest_rc" -ne 0 ]; then
  warn "label manifest is unusable; deployment result is unchanged"
  exit 0
fi
lifecycle="$(
  aisoft_label_manifest_lifecycle "$manifest" |
    jq -Rsc 'split("\n") | map(select(length > 0))'
)"
# Without deployed in the derived set the projection below would add deployed
# while leaving completed in place, putting both mutually exclusive terminal
# states on one Issue. Refuse rather than write that.
if ! printf '%s' "$lifecycle" | jq -e 'index("deployed")' >/dev/null 2>&1; then
  warn "label manifest declares no deployed lifecycle state; deployment result is unchanged"
  exit 0
fi

if [ -n "${MERGE_MESSAGE_FILE:-}" ]; then
  if [ ! -r "$MERGE_MESSAGE_FILE" ]; then
    warn "merge message file is unreadable; deployment result is unchanged"
    exit 0
  fi
  message="$(<"$MERGE_MESSAGE_FILE")"
else
  message="$(git log -1 --format=%B HEAD 2>/dev/null || true)"
fi

issues="$(
  printf '%s\n' "$message" |
    awk '/^Closes #[1-9][0-9]*$/ {n=substr($0, 9); if (!seen[n]++) print n}'
)"
if [ -z "$issues" ]; then
  subject="$(printf '%s\n' "$message" | sed -n '1p')"
  fallback="$(printf '%s\n' "$subject" | sed -nE 's#.*(^|[^[:alnum:]_])change/([1-9][0-9]*)([^0-9]|$).*#\2#p')"
  issues="$fallback"
fi
if [ -z "$issues" ]; then
  warn "no linked Issue found; deployment result is unchanged"
  exit 0
fi

api="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
curl_auth() {
  printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
    curl --config - "$@"
}

labels="$(curl_auth --fail --silent --show-error "$api/labels?limit=100" 2>/dev/null || true)"
deployed_id="$(printf '%s' "$labels" | jq -r '.[] | select(.name == "deployed") | .id' 2>/dev/null | head -1)"
if [ -z "$deployed_id" ]; then
  warn "deployed label is unavailable; deployment result is unchanged"
  exit 0
fi

failed=0
while IFS= read -r issue_number; do
  [ -n "$issue_number" ] || continue
  issue="$(
    curl_auth --fail --silent --show-error "$api/issues/$issue_number" 2>/dev/null || true
  )"
  if ! printf '%s' "$issue" | jq -e '.labels | type == "array"' >/dev/null 2>&1; then
    warn "cannot read Issue #$issue_number"
    failed=1
    continue
  fi
  ids="$(
    printf '%s' "$issue" |
      jq -c --argjson lifecycle "$lifecycle" --argjson deployed "$deployed_id" '
        ([.labels[] | select((.name as $name | $lifecycle | index($name)) | not) | .id]
         + [$deployed]) | unique
      '
  )"
  payload="$(jq -cn --argjson labels "$ids" '{labels:$labels}')"
  if ! curl_auth --fail --silent --show-error --output /dev/null \
    --request PUT --header 'Content-Type: application/json' \
    --data "$payload" "$api/issues/$issue_number/labels" 2>/dev/null; then
    warn "cannot update Issue #$issue_number"
    failed=1
  else
    printf 'marked deployed: #%s\n' "$issue_number"
  fi
done <<EOF
$issues
EOF

if [ "$failed" -ne 0 ]; then
  warn "one or more Issue updates failed; deployment remains successful"
fi
exit 0
