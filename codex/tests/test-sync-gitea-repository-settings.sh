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

# Inline form keeps working through the transition but must print the
# deprecation notice (#111).
inline_stderr="$(bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh" 2>&1 >/dev/null)"
grep -Fq 'DEPRECATED: inline GITEA_TOKEN is deprecated' <<<"$inline_stderr"

# Token-file form (#111): file only, no inline token, no deprecation notice.
FILE_TOKEN='sentinel-settings-file-token'
printf '%s\n' "$FILE_TOKEN" >"$TMP/token"
chmod 600 "$TMP/token"
result="$(env -u GITEA_TOKEN GITEA_TOKEN_FILE="$TMP/token" \
  bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh" 2>"$TMP/file.stderr")"
[ "$result" = "default_delete_branch_after_merge=true" ]
[ "$(cat "$TMP/state")" = true ]
if grep -Fq 'DEPRECATED' "$TMP/file.stderr"; then
  echo "file form must not print the deprecation notice" >&2
  exit 1
fi
if grep -Fq "$FILE_TOKEN" "$TMP/argv.log"; then
  echo "file token leaked" >&2
  exit 1
fi

# Permissive token file fails closed even though an inline fallback exists.
chmod 644 "$TMP/token"
rc=0
GITEA_TOKEN_FILE="$TMP/token" \
  bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
  >"$TMP/perm.out" 2>"$TMP/perm.err" || rc=$?
[ "$rc" -eq 20 ]
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE mode must be 400 or 600' \
  "$TMP/perm.err"

# Missing both forms is a hard usage error.
rc=0
env -u GITEA_TOKEN bash "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
  >"$TMP/missing.out" 2>"$TMP/missing.err" || rc=$?
[ "$rc" -eq 2 ]
grep -Fq 'GITEA_TOKEN_FILE or GITEA_TOKEN is required' "$TMP/missing.err"

echo "repository settings tests passed"
