#!/usr/bin/env bash
# Reference deployment failure / rollback notifier (#397, platform 05 §1).
#
# Call it from the failure or rollback step of a project's deployment job:
#
#   bash scripts/ci/deploy-notify.sh --result failed --stage health-check \
#     --run-url "$RUN_URL"
#   bash scripts/ci/deploy-notify.sh --result rolled-back --stage rollback
#
# It finds the Issues this deployment shipped the same way the platform's
# mark-deployed hook does (each exact `Closes #N` line of the merge message,
# else `change/N` in its subject) and posts one comment per Issue carrying only
# the result, the stage, the short commit and the run link. Gitea then mails
# the Issue's participants (05 §1). No log text, no environment, no secret.
#
# Inputs: GITEA_URL, GITEA_OWNER, GITEA_REPO, and GITEA_TOKEN or a readable
# GITEA_TOKEN_FILE; MERGE_MESSAGE_FILE optionally replaces `git log -1 HEAD`.
# It must never change a deployment's outcome: every missing prerequisite,
# bad argument or failed request is a warning and exit 0.
set -u
set +x

warn() {
  printf 'WARN: deploy-notify: %s\n' "$*" >&2
}

result=""
stage=""
run_url=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --result | --stage | --run-url)
      if [ "$#" -lt 2 ]; then
        warn "$1 needs a value; nothing sent"
        exit 0
      fi
      case "$1" in
        --result) result="$2" ;;
        --stage) stage="$2" ;;
        --run-url) run_url="$2" ;;
      esac
      shift 2
      ;;
    *)
      warn "unknown argument; nothing sent"
      exit 0
      ;;
  esac
done

case "$result" in
  failed) headline='Deployment failed' ;;
  rolled-back) headline='Deployment rolled back' ;;
  *)
    warn "--result must be failed or rolled-back; nothing sent"
    exit 0
    ;;
esac
# Free text never reaches the comment: the stage is a short token and the run
# link a plain http(s) URL, otherwise they are dropped.
if ! printf '%s' "$stage" | grep -Eqx '[A-Za-z0-9._-]{1,40}'; then
  stage="unspecified"
fi
if [ "${#run_url}" -gt 300 ] ||
  ! printf '%s' "$run_url" | grep -Eqx 'https?://[A-Za-z0-9._~:/?#@!$&()*+,;=%-]+'; then
  run_url=""
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO; do
  if [ -z "${!name:-}" ]; then
    warn "$name is unavailable; nothing sent"
    exit 0
  fi
done
token="${GITEA_TOKEN:-}"
if [ -z "$token" ] && [ -n "${GITEA_TOKEN_FILE:-}" ] && [ -r "$GITEA_TOKEN_FILE" ]; then
  token="$(head -n 1 "$GITEA_TOKEN_FILE")"
fi
if [ -z "$token" ]; then
  warn "GITEA_TOKEN or a readable GITEA_TOKEN_FILE is unavailable; nothing sent"
  exit 0
fi
if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
  warn "curl and jq are required; nothing sent"
  exit 0
fi

if [ -n "${MERGE_MESSAGE_FILE:-}" ]; then
  if [ ! -r "$MERGE_MESSAGE_FILE" ]; then
    warn "merge message file is unreadable; nothing sent"
    exit 0
  fi
  message="$(cat "$MERGE_MESSAGE_FILE")"
else
  message="$(git log -1 --format=%B HEAD 2>/dev/null || true)"
fi
commit="$(git rev-parse --short=12 HEAD 2>/dev/null || echo unknown)"

issues="$(
  printf '%s\n' "$message" |
    awk '/^Closes #[1-9][0-9]*$/ {n=substr($0, 9); if (!seen[n]++) print n}'
)"
if [ -z "$issues" ]; then
  subject="$(printf '%s\n' "$message" | sed -n '1p')"
  issues="$(printf '%s\n' "$subject" | sed -nE 's#.*(^|[^[:alnum:]_])change/([1-9][0-9]*)([^0-9]|$).*#\2#p')"
fi
if [ -z "$issues" ]; then
  warn "no linked Issue found; nothing sent"
  exit 0
fi

body="$(jq -rn --arg h "$headline" --arg s "$stage" --arg c "$commit" --arg u "$run_url" \
  '"**\($h)**\n\n- stage: `\($s)`\n- commit: `\($c)`" + (if $u == "" then "" else "\n- run: \($u)" end)')"
payload="$(jq -cn --arg body "$body" '{body: $body}')"
api="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"

while IFS= read -r number; do
  [ -n "$number" ] || continue
  if printf 'header = "Authorization: token %s"\n' "$token" |
    curl --config - --fail --silent --show-error --output /dev/null \
      --request POST --header 'Content-Type: application/json' \
      --data "$payload" "$api/issues/$number/comments" 2>/dev/null; then
    printf 'notified: #%s %s\n' "$number" "$result"
  else
    warn "cannot comment on Issue #$number"
  fi
done <<EOF
$issues
EOF
exit 0
