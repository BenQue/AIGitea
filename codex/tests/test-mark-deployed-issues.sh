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
unset MOCK_FAIL

# Inline form keeps working through the transition but prints the deprecation
# notice (#111).
grep -Fq 'DEPRECATED: inline GITEA_TOKEN is deprecated' <<<"$output"

# Token-file form (#111): file only, labels are marked, no deprecation notice.
FILE_TOKEN='sentinel-file-secret-token'
printf '%s\n' "$FILE_TOKEN" >"$TMP/token"
chmod 600 "$TMP/token"
printf '%s\n' 'Closes #77' >"$TMP/message"
file_output="$(env -u GITEA_TOKEN GITEA_TOKEN_FILE="$TMP/token" \
  bash "$ROOT/codex/tools/mark-deployed-issues.sh" 2>&1)"
grep -Fq 'marked deployed: #77' <<<"$file_output"
grep -Fq '/issues/77/labels' "$TMP/puts.log"
if grep -Fq 'DEPRECATED' <<<"$file_output"; then
  echo 'file form must not print the deprecation notice' >&2
  exit 1
fi

# Permissive token file: refuse the credential, warn, never fail deployment,
# and never call the API.
chmod 644 "$TMP/token"
puts_before="$(wc -l <"$TMP/puts.log" | tr -d ' ')"
rc=0
perm_output="$(env -u GITEA_TOKEN GITEA_TOKEN_FILE="$TMP/token" \
  bash "$ROOT/codex/tools/mark-deployed-issues.sh" 2>&1)" || rc=$?
[ "$rc" -eq 0 ]
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE mode must be 400 or 600' \
  <<<"$perm_output"
grep -Fq 'deployment result is unchanged' <<<"$perm_output"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = "$puts_before" ]

# Missing both forms: warn and keep the deployment green.
rc=0
missing_output="$(env -u GITEA_TOKEN \
  bash "$ROOT/codex/tools/mark-deployed-issues.sh" 2>&1)" || rc=$?
[ "$rc" -eq 0 ]
grep -Fq 'usable GITEA_TOKEN_FILE or GITEA_TOKEN is unavailable' \
  <<<"$missing_output"

# Lifecycle names come from the shared manifest (#115 AC-7), so the manifest is
# now a prerequisite. It must join the other missing-prerequisite cases — warn,
# leave the successful deployment green, issue no PUT — rather than falling back
# to a private copy of the eight names, which is exactly the second source of
# truth this change removes.
flat="$TMP/flat"
mkdir -p "$flat"
cp "$ROOT/codex/tools/mark-deployed-issues.sh" \
  "$ROOT/codex/agent/gitea-token.sh" \
  "$ROOT/codex/agent/gitea-label-manifest.sh" "$flat/"
printf '%s\n' 'Closes #88' >"$TMP/message"

puts_before="$(wc -l <"$TMP/puts.log" | tr -d ' ')"
rc=0
absent_output="$(bash "$flat/mark-deployed-issues.sh" 2>&1)" || rc=$?
[ "$rc" -eq 0 ]
grep -Fq 'label manifest is unavailable' <<<"$absent_output"
grep -Fq 'deployment result is unchanged' <<<"$absent_output"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = "$puts_before" ]

# A malformed manifest is refused rather than partially read: deriving the
# lifecycle set from a half-valid manifest would strip the wrong labels.
printf '%s\n' '{"schema_version": 1}' >"$flat/gitea-labels.json"
rc=0
invalid_output="$(bash "$flat/mark-deployed-issues.sh" 2>&1)" || rc=$?
[ "$rc" -eq 0 ]
grep -Fq 'label manifest is unusable' <<<"$invalid_output"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = "$puts_before" ]

# A manifest that validates but declares no deployed state would make the tool
# add deployed without stripping completed, leaving both mutually exclusive
# terminal states on one Issue. Refuse instead of writing that.
jq '(.canonical[] | select(.name == "deployed") | .name) = "area/deployed"' \
  "$ROOT/codex/config/gitea-labels.json" >"$flat/gitea-labels.json"
rc=0
undeclared_output="$(bash "$flat/mark-deployed-issues.sh" 2>&1)" || rc=$?
[ "$rc" -eq 0 ]
grep -Fq 'declares no deployed lifecycle state' <<<"$undeclared_output"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = "$puts_before" ]

# With the manifest beside it, the flat install layout marks deployed normally.
cp "$ROOT/codex/config/gitea-labels.json" "$flat/gitea-labels.json"
flat_output="$(bash "$flat/mark-deployed-issues.sh" 2>&1)"
grep -Fq 'marked deployed: #88' <<<"$flat_output"
grep -Fq '/issues/88/labels' "$TMP/puts.log"

# --- Issue #175 AC-4: this tool has no --range, and must not grow one --------
#
# The two operator-run label tools take a range and were taught to report what
# it resolved to. This one is anchored on the commit the deployment checked out,
# so an argument that looks like a range must stay inert: if it were ever
# honoured, a deployment hook would become steerable by whatever string reached
# its argv, which is exactly the mis-aim #175 removed from the other two.
puts_before="$(wc -l <"$TMP/puts.log" | tr -d ' ')"
# Its own message file: earlier cases rewrote $TMP/message, and this assertion
# is only meaningful against a message whose Issue it names itself.
cat >"$TMP/message-175" <<'EOF'
Merge pull request 604

Closes #91
EOF
export MERGE_MESSAGE_FILE="$TMP/message-175"
range_output="$(bash "$ROOT/codex/tools/mark-deployed-issues.sh" --range 'HEAD~9..HEAD' 2>&1)"
grep -Fq 'marked deployed: #91' <<<"$range_output"
[ "$(wc -l <"$TMP/puts.log" | tr -d ' ')" = "$((puts_before + 1))" ]
# The anchor stayed the merge message, not the argument.
if grep -Fq 'HEAD~9' "$TMP/argv.log"; then
  echo 'mark-deployed must not act on a range argument' >&2
  exit 1
fi

if grep -Fq "$FILE_TOKEN" "$TMP/argv.log" ||
  grep -Fq "$FILE_TOKEN" <<<"$file_output$perm_output"; then
  echo "file token leaked" >&2
  exit 1
fi
echo "mark-deployed tests passed"
