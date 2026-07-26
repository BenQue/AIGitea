#!/usr/bin/env bash
set -u
set +x

warn() {
  printf 'WARN: mark-deployed: %s\n' "$*" >&2
}

for name in GITEA_URL GITEA_OWNER GITEA_REPO GITEA_TOKEN; do
  if [ -z "${!name:-}" ]; then
    warn "$name is unavailable; deployment result is unchanged"
    exit 0
  fi
done
if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
  warn "curl and jq are required; deployment result is unchanged"
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

lifecycle='["needs-analysis","awaiting-triage","spec-drafting","spec-review","approved","pr-open","completed","deployed"]'
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
