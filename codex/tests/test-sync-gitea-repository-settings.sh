#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
printf 'false\n' >"$TMP/state"

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
read -r _auth
printf '%s\n' "$*" >>"$MOCK_ROOT/argv.log"
method=GET
data=""
previous=""
for argument in "$@"; do
  if [ "$previous" = "--request" ]; then method="$argument"; fi
  if [ "$previous" = "--data" ]; then data="$argument"; fi
  previous="$argument"
done
if [ "$method" = PATCH ]; then
  printf '%s' "$data" | jq -r '.default_delete_branch_after_merge' >"$MOCK_ROOT/state"
else
  value="$(cat "$MOCK_ROOT/state")"
  printf '{"default_delete_branch_after_merge":%s}\n' "$value"
fi
MOCK
chmod +x "$TMP/bin/curl"

export MOCK_ROOT="$TMP"
export PATH="$TMP/bin:$PATH"
export GITEA_URL="http://gitea.test"
export GITEA_OWNER="owner"
export GITEA_REPO="repo"
export GITEA_TOKEN="sentinel-settings-token"

result="$(bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh")"
[ "$result" = "default_delete_branch_after_merge=true" ]
[ "$(cat "$TMP/state")" = true ]
result="$(bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh" --disable)"
[ "$result" = "default_delete_branch_after_merge=false" ]
[ "$(cat "$TMP/state")" = false ]
if grep -Fq "$GITEA_TOKEN" "$TMP/argv.log"; then
  echo "token leaked" >&2
  exit 1
fi
echo "repository settings tests passed"
