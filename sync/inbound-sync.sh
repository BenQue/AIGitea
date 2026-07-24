#!/usr/bin/env bash
set -Eeuo pipefail
set +x

[ "${1:-}" = reconcile ] && [ "$#" -eq 2 ] || {
  echo "usage: $0 reconcile <profile>" >&2
  exit 2
}
profile="$2"
[[ "$profile" =~ ^[a-z0-9][a-z0-9_-]{0,63}$ ]] || {
  echo "unsafe profile name" >&2
  exit 2
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${AISOFT_SYNC_CONFIG_DIR:-/etc/aisoft-sync}"
STATE_ROOT="${AISOFT_SYNC_STATE_ROOT:-/var/lib/aisoft-sync}"
config="$CONFIG_DIR/$profile.env"

file_mode() {
  stat -f '%Lp' "$1" 2>/dev/null || stat -c '%a' "$1"
}
require_private_file() {
  local path="$1" kind="$2" actual
  [ -f "$path" ] || { echo "$kind file is missing" >&2; exit 1; }
  actual="$(file_mode "$path")"
  case "$actual" in 400|600) ;; *) echo "$kind file mode must be 400 or 600" >&2; exit 1 ;; esac
}

require_private_file "$config" "profile"
# shellcheck disable=SC1090
source "$config"
set +x

for name in GITHUB_URL GITHUB_REF GITHUB_USERNAME GITHUB_TOKEN_FILE \
  GITEA_URL GITEA_OWNER GITEA_REPO GITEA_GIT_URL GITEA_USERNAME GITEA_TOKEN_FILE; do
  [ -n "${!name:-}" ] || { echo "$name is required" >&2; exit 1; }
done
[ "$GITHUB_REF" = "refs/heads/main" ] || {
  echo "GITHUB_REF must be refs/heads/main" >&2
  exit 1
}
require_private_file "$GITHUB_TOKEN_FILE" "GitHub token"
require_private_file "$GITEA_TOKEN_FILE" "Gitea token"
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }

state="$STATE_ROOT/$profile"
repo="$state/repository.git"
mkdir -p "$state"
chmod 700 "$state"

lock="$state/lock"
if command -v flock >/dev/null 2>&1; then
  exec 9>"$lock"
  flock -n 9 || { echo "profile is already reconciling" >&2; exit 75; }
else
  mkdir "$lock.d" 2>/dev/null || { echo "profile is already reconciling" >&2; exit 75; }
  trap 'rmdir "$lock.d" 2>/dev/null || true' EXIT
fi

[ -d "$repo" ] || git init --bare "$repo" >/dev/null
git_config=(-c "credential.helper=$SCRIPT_DIR/git-credential-token-file.sh")

github_git() {
  AISOFT_CREDENTIAL_USERNAME="$GITHUB_USERNAME" \
  AISOFT_CREDENTIAL_TOKEN_FILE="$GITHUB_TOKEN_FILE" \
    git "${git_config[@]}" --git-dir="$repo" "$@"
}
gitea_git() {
  AISOFT_CREDENTIAL_USERNAME="$GITEA_USERNAME" \
  AISOFT_CREDENTIAL_TOKEN_FILE="$GITEA_TOKEN_FILE" \
    git "${git_config[@]}" --git-dir="$repo" "$@"
}
atomic_write() {
  local destination="$1" value="$2" temporary
  temporary="$destination.tmp.$$"
  printf '%s\n' "$value" >"$temporary"
  chmod 600 "$temporary"
  mv "$temporary" "$destination"
}
curl_gitea() {
  local token
  token="$(<"$GITEA_TOKEN_FILE")"
  printf 'header = "Authorization: token %s"\n' "$token" |
    curl --config - "$@"
}

github_git fetch --quiet --no-tags "$GITHUB_URL" \
  "+$GITHUB_REF:refs/remotes/github/main"
github_sha="$(git --git-dir="$repo" rev-parse refs/remotes/github/main)"
[[ "$github_sha" =~ ^[0-9a-f]{40}$ ]] || { echo "invalid GitHub SHA" >&2; exit 1; }

gitea_git fetch --quiet --no-tags "$GITEA_GIT_URL" \
  "refs/heads/main:refs/remotes/gitea/main"
gitea_main="$(git --git-dir="$repo" rev-parse refs/remotes/gitea/main)"
[[ "$gitea_main" =~ ^[0-9a-f]{40}$ ]] || { echo "invalid Gitea main SHA" >&2; exit 1; }

last_file="$state/last-successful-sha"
if [ -s "$last_file" ]; then
  last="$(<"$last_file")"
  [[ "$last" =~ ^[0-9a-f]{40}$ ]] || { echo "invalid last successful SHA" >&2; exit 1; }
  git --git-dir="$repo" merge-base --is-ancestor "$last" "$github_sha" || {
    echo "GitHub history rewrite detected; no mutation performed" >&2
    exit 1
  }
fi
git --git-dir="$repo" merge-base "$github_sha" "$gitea_main" >/dev/null || {
  echo "GitHub and Gitea main have no common history; no mutation performed" >&2
  exit 1
}

if git --git-dir="$repo" merge-base --is-ancestor "$github_sha" "$gitea_main"; then
  atomic_write "$last_file" "$github_sha"
  rm -f "$state/pending-sha"
  echo "already present in Gitea main: $github_sha"
  exit 0
fi

branch="sync/github/$github_sha"
remote_sha="$(
  gitea_git ls-remote "$GITEA_GIT_URL" "refs/heads/$branch" |
    awk 'NR == 1 {print $1}'
)"
if [ -n "$remote_sha" ] && [ "$remote_sha" != "$github_sha" ]; then
  echo "conflicting immutable sync branch; no mutation performed" >&2
  exit 1
fi

api="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
pulls="$(
  curl_gitea --fail --silent --show-error \
    "$api/pulls?state=open&limit=50"
)"
same_pr="$(printf '%s' "$pulls" | jq -r --arg branch "$branch" \
  '[.[] | select(.head.ref == $branch)] | first | .number // empty')"
if [ -n "$same_pr" ]; then
  atomic_write "$last_file" "$github_sha"
  rm -f "$state/pending-sha"
  printf 'existing sync PR #%s for %s\n' "$same_pr" "$github_sha"
  exit 0
fi
active_pr="$(printf '%s' "$pulls" | jq -r \
  '[.[] | select(.head.ref | startswith("sync/github/"))] | first | .number // empty')"
if [ -n "$active_pr" ]; then
  atomic_write "$state/pending-sha" "$github_sha"
  printf 'active sync PR #%s; recorded pending SHA %s\n' "$active_pr" "$github_sha"
  exit 0
fi

if [ -z "$remote_sha" ]; then
  gitea_git push --quiet "$GITEA_GIT_URL" \
    "$github_sha:refs/heads/$branch"
fi
body="$(
  jq -rn \
    --arg github_url "$GITHUB_URL" \
    --arg source_ref "$GITHUB_REF" \
    --arg sha "$github_sha" \
    --arg range "$gitea_main..$github_sha" '
      "GitHub URL: \($github_url)\n" +
      "Source ref: \($source_ref)\n" +
      "Source SHA: \($sha)\n" +
      "Compare range: \($range)\n\n" +
      "This is a new intranet PR. GitHub review is provenance only and does not authorize an intranet release."
    '
)"
payload="$(
  jq -cn --arg base main --arg head "$branch" \
    --arg title "sync: import GitHub ${github_sha:0:12}" \
    --arg body "$body" '{base:$base,head:$head,title:$title,body:$body}'
)"
created="$(
  curl_gitea --fail --silent --show-error \
    --request POST --header 'Content-Type: application/json' \
    --data "$payload" "$api/pulls"
)"
pr_number="$(printf '%s' "$created" | jq -r '.number')"
[[ "$pr_number" =~ ^[1-9][0-9]*$ ]] || {
  echo "Gitea returned invalid PR response" >&2
  exit 1
}
atomic_write "$last_file" "$github_sha"
rm -f "$state/pending-sha"
printf 'created sync PR #%s for %s\n' "$pr_number" "$github_sha"
