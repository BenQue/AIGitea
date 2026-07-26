#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
read -r _auth
printf '%s\n' "$*" >>"$MOCK_ROOT/argv.log"
url="${*: -1}"
data=""
previous=""
for argument in "$@"; do
  if [ "$previous" = "--data" ]; then data="$argument"; fi
  previous="$argument"
done
case "$url" in
  */labels?limit=100)
    printf '%s\n' '[{"id":50,"name":"deployed"},{"id":4,"name":"completed"},{"id":3,"name":"approved"}]'
    ;;
  */issues/*/labels)
    if [ "${MOCK_FAIL:-0}" = 1 ]; then exit 22; fi
    printf '%s\t%s\n' "$url" "$data" >>"$MOCK_ROOT/puts.log"
    ;;
  */issues/*)
    printf '%s\n' '{"labels":[{"id":1,"name":"type/platform"},{"id":2,"name":"complexity/complex"},{"id":4,"name":"completed"},{"id":9,"name":"priority/high"}]}'
    ;;
  *) exit 22 ;;
esac
MOCK
chmod +x "$TMP/bin/curl"

cat >"$TMP/message" <<'EOF'
Merge coordinated platform changes

Closes #12
Closes #13
Closes #12
EOF

export MOCK_ROOT="$TMP"
export PATH="$TMP/bin:$PATH"
export GITEA_URL="http://gitea.test"
export GITEA_OWNER="owner"
export GITEA_REPO="repo"
export GITEA_TOKEN="sentinel-secret-token"
export MERGE_MESSAGE_FILE="$TMP/message"

output="$(bash "$ROOT/codex/tools/mark-deployed-issues.sh" 2>&1)"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = 2 ]
grep -Fq '/issues/12/labels' "$TMP/puts.log"
grep -Fq '/issues/13/labels' "$TMP/puts.log"
grep -Fq '{"labels":[1,2,9,50]}' "$TMP/puts.log"

bash "$ROOT/codex/tools/mark-deployed-issues.sh" >/dev/null 2>&1
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = 4 ]

printf '%s\n' 'Merge branch change/42 into main' >"$TMP/message"
bash "$ROOT/codex/tools/mark-deployed-issues.sh" >/dev/null 2>&1
grep -Fq '/issues/42/labels' "$TMP/puts.log"

export MOCK_FAIL=1
printf '%s\n' 'Closes #99' >"$TMP/message"
failure_output="$(bash "$ROOT/codex/tools/mark-deployed-issues.sh" 2>&1)"
grep -Fq 'deployment remains successful' <<<"$failure_output"
if grep -Fq "$GITEA_TOKEN" "$TMP/argv.log" || grep -Fq "$GITEA_TOKEN" <<<"$output$failure_output"; then
  echo "token leaked" >&2
  exit 1
fi
echo "mark-deployed tests passed"
