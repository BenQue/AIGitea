#!/usr/bin/env bash
# #355: the Claude-side Matt plugin pin. Every case runs against a copied source
# tree or a fabricated home; the real ~/.claude is never read here.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'chmod -R u+rwx "$tmp" 2>/dev/null || true; rm -rf "$tmp"' EXIT

checker="$root/skill-for-claude/check-plugin-pin.sh"
ref="v1.3.1"
pin="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' \
  "$root/codex/vendor/mattpocock/$ref/manifest.json")"
other="0000000000000000000000000000000000000001"
sentinel='AISOFT-FIXTURE-SECRET-355'
expected="expected: mattpocock-skills@aisoft-platform ref=$ref commit=$pin"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

# check <label> <status> <first line> <command...>
check() {
  local label="$1" want_status="$2" want_first="$3" status
  shift 3
  set +e
  output="$("$@" 2>&1)"
  status=$?
  set -e
  [[ "$status" == "$want_status" ]] ||
    fail "$label: exit $status, expected $want_status: $output"
  [[ "$(head -n 1 <<<"$output")" == "$want_first"* ]] ||
    fail "$label: first line is not $want_first: $output"
}

edit_json() {
  python3 -B - "$1" "$2" <<'PY'
import json
import sys

path, statement = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as handle:
    doc = json.load(handle)
exec(statement)
with open(path, "w", encoding="utf-8") as handle:
    json.dump(doc, handle)
PY
}

# ---- source: marketplace entry == vendor manifest == installer version ----

check 'current tree' 0 'PIN_SOURCE_OK' bash "$checker" --source-only
grep -Fqx "$expected" <<<"$output" || fail 'source mode must print the agreed pin'

make_tree() {
  mkdir -p "$1/skill-for-claude" "$1/.claude-plugin" "$1/codex/vendor/mattpocock/$ref"
  cp "$root/skill-for-claude/check-plugin-pin.sh" "$root/skill-for-claude/check-plugin-pin.py" \
    "$1/skill-for-claude/"
  cp "$root/.claude-plugin/marketplace.json" "$1/.claude-plugin/"
  cp "$root/codex/install-skills.sh" "$1/codex/"
  cp "$root/codex/vendor/mattpocock/$ref/manifest.json" "$1/codex/vendor/mattpocock/$ref/"
}

source_case() {
  local label="$1" tree="$tmp/tree-$1"
  make_tree "$tree"
  "$2" "$tree"
  check "source $label" 1 'PIN_SOURCE_MISMATCH: ' bash "$tree/skill-for-claude/check-plugin-pin.sh" --source-only
  # An installation cannot be judged against a pin the source does not agree on.
  check "installed over $label" 2 'PIN_SOURCE_MISMATCH: ' \
    bash "$tree/skill-for-claude/check-plugin-pin.sh" "$tmp/home-clean"
}

intact="$tmp/tree-intact"
make_tree "$intact"
check 'copied tree' 0 'PIN_SOURCE_OK' bash "$intact/skill-for-claude/check-plugin-pin.sh" --source-only

mutate_sha() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'][0]['source']['sha'] = '$other'"; }
mutate_ref() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'][0]['source']['ref'] = 'v1.2.2'"; }
mutate_short_sha() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'][0]['source']['sha'] = '${pin:0:12}'"; }
mutate_branch_ref() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'][0]['source']['ref'] = 'main'"; }
mutate_url() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'][0]['source']['url'] = 'https://github.com/example/skills.git'"; }
mutate_duplicate() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'].append(dict(doc['plugins'][0]))"; }
mutate_removed() { edit_json "$1/.claude-plugin/marketplace.json" "doc['plugins'] = []"; }
mutate_name() { edit_json "$1/.claude-plugin/marketplace.json" "doc['name'] = 'another-marketplace'"; }
mutate_manifest_commit() { edit_json "$1/codex/vendor/mattpocock/$ref/manifest.json" "doc['commit'] = '$other'"; }
mutate_manifest_tag() { edit_json "$1/codex/vendor/mattpocock/$ref/manifest.json" "doc['tag'] = 'v9.9.9'"; }
mutate_installer() { printf '%s\n' 'matt_version="v1.2.2"' >"$1/codex/install-skills.sh"; }
mutate_installer_twice() { printf '%s\n' "matt_version=\"$ref\"" "matt_version=\"$ref\"" >"$1/codex/install-skills.sh"; }
mutate_missing_marketplace() { rm -f -- "$1/.claude-plugin/marketplace.json"; }
mutate_broken_marketplace() { printf '%s\n' '{"name": ' >"$1/.claude-plugin/marketplace.json"; }

# The clean home exists before the source cases so each of them can prove that
# a home which would otherwise read PIN_CLEAN is not reported as such.
clean_home="$tmp/home-clean"
mkdir -p "$clean_home/.claude/plugins"
cat >"$clean_home/.claude/plugins/installed_plugins.json" <<JSON
{"version": 2, "plugins": {
  "mattpocock-skills@aisoft-platform": [
    {"scope": "user", "version": "1.3.1", "gitCommitSha": "$pin",
     "installPath": "/$sentinel/cache", "token": "$sentinel"},
    {"scope": "project", "version": "1.3.1", "gitCommitSha": "$pin", "projectPath": "/$sentinel/project"}
  ],
  "superpowers@claude-plugins-official": [
    {"scope": "user", "version": "6.4.1", "gitCommitSha": "$other", "note": "$sentinel"}
  ]
}}
JSON

for mutation in sha ref short_sha branch_ref url duplicate removed name manifest_commit manifest_tag \
  installer installer_twice missing_marketplace broken_marketplace; do
  source_case "$mutation" "mutate_$mutation"
done

# ---- installed: the three situations of AC-2, then the fail-closed ones ----

installed_case() {
  local label="$1" want_status="$2" want_first="$3" home="$tmp/home-$1"
  mkdir -p "$home/.claude/plugins"
  cat >"$home/.claude/plugins/installed_plugins.json"
  check "installed $label" "$want_status" "$want_first" bash "$checker" "$home"
}

# consistent
printf '%s\n' "{\"env\": {\"TOKEN\": \"$sentinel\"}}" >"$clean_home/.claude/settings.json"
printf '%s\n' "$sentinel" >"$clean_home/.claude/.credentials.json"
chmod 000 "$clean_home/.claude/settings.json" "$clean_home/.claude/.credentials.json"
before="$(cd "$clean_home" && find . | LC_ALL=C sort)"
check 'installed clean' 0 'PIN_CLEAN' bash "$checker" "$clean_home"
[[ "$output" == "PIN_CLEAN"$'\n'"$expected"$'\n'"installed: mattpocock-skills@aisoft-platform scope=user version=1.3.1 commit=$pin"$'\n'"installed: mattpocock-skills@aisoft-platform scope=project version=1.3.1 commit=$pin" ]] ||
  fail "a clean installation must list exactly its own records: $output"
[[ "$output" != *"$sentinel"* ]] || fail 'credential-shaped values must never be printed'
[[ "$before" == "$(cd "$clean_home" && find . | LC_ALL=C sort)" ]] ||
  fail 'the checker must not create anything under the target home'

# missing
check 'installed nothing' 0 'PIN_NOT_INSTALLED' bash "$checker" "$tmp/home-absent"
[[ ! -e "$tmp/home-absent" ]] || fail 'the checker must not create a missing target home'
installed_case other-plugins-only 0 'PIN_NOT_INSTALLED' <<JSON
{"version": 2, "plugins": {"superpowers@claude-plugins-official": [{"scope": "user", "version": "6.4.1"}]}}
JSON
installed_case empty-record-list 0 'PIN_NOT_INSTALLED' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": []}}
JSON

# inconsistent: pinned marketplace, another commit
installed_case wrong-commit 1 'PIN_DRIFT' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": [
  {"scope": "user", "version": "1.3.1", "gitCommitSha": "$other"}]}}
JSON
grep -Fqx "DRIFT: mattpocock-skills@aisoft-platform scope=user version=1.3.1 commit=$other expected=$pin" \
  <<<"$output" || fail "a wrong commit must be named with the expected one: $output"

# inconsistent: another marketplace, even at the pinned commit
installed_case other-marketplace 1 'PIN_DRIFT' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@claude-plugins-official": [
  {"scope": "user", "version": "1.3.1", "gitCommitSha": "$pin"}]}}
JSON
grep -Fqx "DRIFT: mattpocock-skills@claude-plugins-official scope=user version=1.3.1 commit=$pin expected=$pin" \
  <<<"$output" || fail "an unpinned marketplace must be drift whatever its commit: $output"

# inconsistent: the pinned record is fine but an unpinned one sits beside it
installed_case mixed 1 'PIN_DRIFT' <<JSON
{"version": 2, "plugins": {
  "mattpocock-skills@aisoft-platform": [{"scope": "user", "version": "1.3.1", "gitCommitSha": "$pin"}],
  "mattpocock-skills@claude-plugins-official": [{"scope": "project", "version": "1.2.3", "gitCommitSha": "$other"}]
}}
JSON
[[ "$(grep -c '^DRIFT: ' <<<"$output")" == 1 ]] || fail "only the unpinned record is drift: $output"

# inconsistent: no recorded commit is not evidence of the pinned one
installed_case no-commit 1 'PIN_DRIFT' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": [{"scope": "user", "version": "1.3.1"}]}}
JSON
grep -Fq 'commit=missing' <<<"$output" || fail "an absent commit must be reported as missing: $output"

# fail closed: nothing this reader does not recognise may read as clean
installed_case schema-3 2 'PIN_UNREADABLE: ' <<JSON
{"version": 3, "plugins": {"mattpocock-skills@aisoft-platform": [
  {"scope": "user", "version": "1.3.1", "gitCommitSha": "$pin"}]}}
JSON
installed_case schema-true 2 'PIN_UNREADABLE: ' <<JSON
{"version": true, "plugins": {}}
JSON
installed_case plugins-list 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": []}
JSON
installed_case record-not-object 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": ["$pin"]}}
JSON
installed_case broken-json 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins":
JSON
installed_case duplicate-key 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": {
  "mattpocock-skills@aisoft-platform": [{"scope": "user", "gitCommitSha": "$other"}],
  "mattpocock-skills@aisoft-platform": [{"scope": "user", "gitCommitSha": "$pin"}]
}}
JSON
installed_case uppercase-commit 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": [
  {"scope": "user", "version": "1.3.1", "gitCommitSha": "$(tr 'a-f' 'A-F' <<<"$pin")"}]}}
JSON
# A value that is not what its field claims to be is refused, not echoed.
installed_case secret-as-version 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@aisoft-platform": [
  {"scope": "user", "version": "token $sentinel", "gitCommitSha": "$pin"}]}}
JSON
[[ "$output" != *"$sentinel"* ]] || fail 'an unrecognised version must not be echoed'
installed_case secret-as-marketplace 2 'PIN_UNREADABLE: ' <<JSON
{"version": 2, "plugins": {"mattpocock-skills@bad $sentinel": [{"scope": "user", "gitCommitSha": "$pin"}]}}
JSON
[[ "$output" != *"$sentinel"* ]] || fail 'an unrecognised marketplace must not be echoed'

mkdir -p "$tmp/home-symlink/.claude/plugins"
ln -s "$clean_home/.claude/plugins/installed_plugins.json" \
  "$tmp/home-symlink/.claude/plugins/installed_plugins.json"
check 'installed symlink' 2 'PIN_UNREADABLE: ' bash "$checker" "$tmp/home-symlink"

check 'unknown option' 2 'usage: ' bash "$checker" --installed
check 'too many arguments' 2 'usage: ' bash "$checker" "$clean_home" "$clean_home"

if find "$root/skill-for-claude" -name '__pycache__' -print -quit | grep -q .; then
  fail 'the checker must not leave bytecode beside the skill sources'
fi

echo 'PASS: test-claude-plugin-pin'
