#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin" "$TMP/config" "$TMP/state"
git init --bare "$TMP/github.git" >/dev/null
git init --bare "$TMP/gitea.git" >/dev/null
git init -b main "$TMP/source" >/dev/null
git -C "$TMP/source" config user.name test
git -C "$TMP/source" config user.email test@example.invalid
printf 'base\n' >"$TMP/source/file.txt"
git -C "$TMP/source" add file.txt
git -C "$TMP/source" commit -m base >/dev/null
git -C "$TMP/source" remote add github "$TMP/github.git"
git -C "$TMP/source" remote add gitea "$TMP/gitea.git"
git -C "$TMP/source" push github main >/dev/null
git -C "$TMP/source" push gitea main >/dev/null
printf 'candidate\n' >>"$TMP/source/file.txt"
git -C "$TMP/source" commit -am candidate >/dev/null
git -C "$TMP/source" push github main >/dev/null
candidate="$(git -C "$TMP/source" rev-parse HEAD)"

printf '%s\n' 'github-sentinel-secret' >"$TMP/github-token"
printf '%s\n' 'gitea-sentinel-secret' >"$TMP/gitea-token"
chmod 600 "$TMP/github-token" "$TMP/gitea-token"
cat >"$TMP/config/project.env" <<EOF
GITHUB_URL=$TMP/github.git
GITHUB_REF=refs/heads/main
GITHUB_USERNAME=github-sync
GITHUB_TOKEN_FILE=$TMP/github-token
GITEA_URL=http://gitea.test
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_GIT_URL=$TMP/gitea.git
GITEA_USERNAME=aisoft-sync
GITEA_TOKEN_FILE=$TMP/gitea-token
EOF
chmod 600 "$TMP/config/project.env"
printf '%s\n' '[]' >"$TMP/pulls.json"

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
read -r _auth
printf '%s\n' "$*" >>"$MOCK_ROOT/curl-argv.log"
[ "${MOCK_FAIL:-0}" = 0 ] || exit 22
method=GET
data=""
previous=""
for argument in "$@"; do
  if [ "$previous" = "--request" ]; then method="$argument"; fi
  if [ "$previous" = "--data" ]; then data="$argument"; fi
  previous="$argument"
done
if [ "$method" = POST ]; then
  printf '%s\n' "$data" >"$MOCK_ROOT/last-payload.json"
  head="$(printf '%s' "$data" | jq -r '.head')"
  jq -cn --arg head "$head" '[{number:1,head:{ref:$head}}]' >"$MOCK_ROOT/pulls.json"
  printf '%s\n' '{"number":1}'
else
  cat "$MOCK_ROOT/pulls.json"
fi
MOCK
chmod +x "$TMP/bin/curl"

export MOCK_ROOT="$TMP"
export PATH="$TMP/bin:$PATH"
export AISOFT_SYNC_CONFIG_DIR="$TMP/config"
export AISOFT_SYNC_STATE_ROOT="$TMP/state"

if bash "$ROOT/sync/inbound-sync.sh" reconcile '../unsafe' >/dev/null 2>&1; then
  echo "unsafe profile unexpectedly succeeded" >&2
  exit 1
fi
cp "$TMP/config/project.env" "$TMP/config/badmode.env"
chmod 644 "$TMP/config/badmode.env"
if bash "$ROOT/sync/inbound-sync.sh" reconcile badmode >/dev/null 2>&1; then
  echo "insecure profile mode unexpectedly succeeded" >&2
  exit 1
fi

first="$(bash "$ROOT/sync/inbound-sync.sh" reconcile project 2>&1)"
grep -Fq 'created sync PR #1' <<<"$first"
[ "$(git --git-dir="$TMP/gitea.git" rev-parse "refs/heads/sync/github/$candidate")" = "$candidate" ]
jq -e --arg sha "$candidate" '
  .base == "main" and
  .head == ("sync/github/" + $sha) and
  (.body | contains("GitHub review is provenance only"))
' "$TMP/last-payload.json" >/dev/null

second="$(bash "$ROOT/sync/inbound-sync.sh" reconcile project 2>&1)"
grep -Fq 'existing sync PR #1' <<<"$second"
[ "$(wc -l <"$TMP/curl-argv.log" | tr -d ' ')" -eq 3 ]

git -C "$TMP/source" checkout main >/dev/null
printf 'newer\n' >>"$TMP/source/file.txt"
git -C "$TMP/source" commit -am newer >/dev/null
git -C "$TMP/source" push github main >/dev/null
newer="$(git -C "$TMP/source" rev-parse HEAD)"
export MOCK_FAIL=1
if bash "$ROOT/sync/inbound-sync.sh" reconcile project >/dev/null 2>&1; then
  echo "API failure unexpectedly succeeded" >&2
  exit 1
fi
unset MOCK_FAIL
pending="$(bash "$ROOT/sync/inbound-sync.sh" reconcile project 2>&1)"
grep -Fq 'recorded pending SHA' <<<"$pending"
[ "$(cat "$TMP/state/project/pending-sha")" = "$newer" ]

printf 'conflict\n' >>"$TMP/source/file.txt"
git -C "$TMP/source" commit -am conflict >/dev/null
git -C "$TMP/source" push github main >/dev/null
conflict_sha="$(git -C "$TMP/source" rev-parse HEAD)"
base_sha="$(git --git-dir="$TMP/gitea.git" rev-parse refs/heads/main)"
git --git-dir="$TMP/gitea.git" update-ref \
  "refs/heads/sync/github/$conflict_sha" "$base_sha"
if bash "$ROOT/sync/inbound-sync.sh" reconcile project >"$TMP/conflict.log" 2>&1; then
  echo "conflicting immutable branch unexpectedly succeeded" >&2
  exit 1
fi
grep -Fq 'conflicting immutable sync branch' "$TMP/conflict.log"

git -C "$TMP/source" checkout --orphan rewritten >/dev/null
git -C "$TMP/source" rm -rf . >/dev/null
printf 'rewrite\n' >"$TMP/source/rewrite.txt"
git -C "$TMP/source" add rewrite.txt
git -C "$TMP/source" commit -m rewrite >/dev/null
git -C "$TMP/source" push --force github rewritten:main >/dev/null
if bash "$ROOT/sync/inbound-sync.sh" reconcile project >"$TMP/rewrite.log" 2>&1; then
  echo "history rewrite unexpectedly succeeded" >&2
  exit 1
fi
grep -Fiq 'history rewrite detected' "$TMP/rewrite.log"

cp "$TMP/config/project.env" "$TMP/config/nocommon.env"
chmod 600 "$TMP/config/nocommon.env"
if bash "$ROOT/sync/inbound-sync.sh" reconcile nocommon >"$TMP/nocommon.log" 2>&1; then
  echo "unrelated histories unexpectedly succeeded" >&2
  exit 1
fi
grep -Fq 'have no common history' "$TMP/nocommon.log"

if grep -R -Fq 'github-sentinel-secret' "$TMP/curl-argv.log" "$TMP/state" ||
  grep -R -Fq 'gitea-sentinel-secret' "$TMP/curl-argv.log" "$TMP/state"; then
  echo "secret leaked" >&2
  exit 1
fi
if rg -n 'push .*(--force|--mirror|refs/heads/main)|/pulls/[0-9]+/merge' \
  "$ROOT/sync/inbound-sync.sh"; then
  echo "forbidden sync mutation found" >&2
  exit 1
fi
echo "inbound sync tests passed"
