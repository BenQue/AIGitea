#!/usr/bin/env bash
# #375: external skill pack version report. Every case runs against a
# fabricated home, fabricated CLIs and an isolated PATH; the real ~/.claude and
# ~/.codex are never read here.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'chmod -R u+rwx "$tmp" 2>/dev/null || true; rm -rf "$tmp"' EXIT

checker="$root/codex/tools/check-external-skill-versions.sh"
adapted="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["superpowers"]["adapted_version"])' \
  "$root/codex/config/external-skill-adaptation.json")"
pin="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' \
  "$root/codex/vendor/mattpocock/v1.3.1/manifest.json")"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

# Only bash, python3 and dirname, plus whichever fake CLIs a case adds.
bin="$tmp/bin"
mkdir -p "$bin"
for tool in bash python3 dirname; do
  ln -s "$(command -v "$tool")" "$bin/$tool"
done
fake_cli() {
  printf '#!/bin/sh\necho "%s"\n' "$2" >"$bin/$1"
  chmod +x "$bin/$1"
}
fake_cli claude '9.8.7 (Claude Code)'
fake_cli codex 'codex-cli 1.2.3'

# home <name> <claude superpowers version|-> <codex marketplace state: registered|unregistered|disabled|-> <codex cached version>
home() {
  local dir="$tmp/$1" claude_version="$2" codex_state="$3" cached="$4"
  mkdir -p "$dir"
  if [[ "$claude_version" != "-" ]]; then
    mkdir -p "$dir/.claude/plugins"
    cat >"$dir/.claude/plugins/installed_plugins.json" <<JSON
{"version": 2, "plugins": {
  "superpowers@claude-plugins-official": [{"scope": "user", "version": "$claude_version"}],
  "mattpocock-skills@aisoft-platform": [{"scope": "user", "version": "1.3.1", "gitCommitSha": "$pin"}]
}}
JSON
  fi
  if [[ "$codex_state" != "-" ]]; then
    mkdir -p "$dir/.codex/plugins/cache/curated/superpowers/abc123/.codex-plugin"
    printf '{"name": "superpowers", "version": "%s"}\n' "$cached" \
      >"$dir/.codex/plugins/cache/curated/superpowers/abc123/.codex-plugin/plugin.json"
    {
      [[ "$codex_state" == registered ]] && printf '[marketplaces.curated]\nsource = "x"\n\n'
      local enabled=true
      [[ "$codex_state" == disabled ]] && enabled=false
      printf '[plugins."superpowers@curated"]\nenabled = %s\n' "$enabled"
    } >"$dir/.codex/config.toml"
  fi
  printf '%s\n' "$dir"
}

# check <label> <status> <home> <expected lines...>
check() {
  local label="$1" want_status="$2" dir="$3" status line
  shift 3
  set +e
  output="$(PATH="$bin" bash "$checker" --home "$dir" 2>&1)"
  status=$?
  set -e
  [[ "$status" == "$want_status" ]] || fail "$label: exit $status, expected $want_status: $output"
  for line in "$@"; do
    grep -Fqx -- "$line" <<<"$output" || fail "$label: missing line '$line' in: $output"
  done
}

snapshot() {
  (cd "$1" && find . -print0 | LC_ALL=C sort -z | xargs -0 ls -ld | awk '{print $1, $5, $NF}'
   find . -type f -print0 | LC_ALL=C sort -z | xargs -0 cat | cksum)
}

newer="$(python3 -B -c 'import sys; p=sys.argv[1].split("."); p[0]=str(int(p[0])+1); print(".".join(p))' "$adapted")"
older="0.1.0"

dir="$(home adapted "$adapted" registered "$adapted")"
before="$(snapshot "$dir")"
check adapted 0 "$dir" \
  "CLI claude 9.8.7" \
  "CLI codex 1.2.3" \
  "SUPERPOWERS claude ADAPTED installed=$adapted adapted=$adapted" \
  "SUPERPOWERS codex ADAPTED enabled=superpowers@curated marketplace=registered installed=$adapted adapted=$adapted" \
  "MATT claude PIN_CLEAN" \
  "RESULT PASS"
[[ "$(snapshot "$dir")" == "$before" ]] || fail "zero-write: the home changed during a read"
[[ ! -e "$root/codex/tools/__pycache__" ]] || fail "zero-write: a bytecode cache appeared next to the tool"

check claude-newer 1 "$(home claude-newer "$newer" registered "$adapted")" \
  "SUPERPOWERS claude REVIEW_NEEDED installed=$newer adapted=$adapted" \
  "RESULT REVIEW_NEEDED"

check codex-newer 1 "$(home codex-newer "$adapted" registered "$newer")" \
  "SUPERPOWERS codex REVIEW_NEEDED enabled=superpowers@curated marketplace=registered installed=$newer adapted=$adapted" \
  "RESULT REVIEW_NEEDED"

check claude-behind 0 "$(home claude-behind "$older" registered "$adapted")" \
  "SUPERPOWERS claude BEHIND installed=$older adapted=$adapted" \
  "RESULT PASS"

check codex-not-loaded 0 "$(home codex-not-loaded "$adapted" unregistered "$older")" \
  "SUPERPOWERS codex NOT_LOADED enabled=superpowers@curated marketplace=unregistered cached=$older adapted=$adapted" \
  "RESULT PASS"

check codex-disabled 0 "$(home codex-disabled "$adapted" disabled "$adapted")" \
  "SUPERPOWERS codex NOT_INSTALLED enabled=none adapted=$adapted" \
  "RESULT PASS"

# Nothing installed: superpowers is simply absent, but the Matt pin is not clean.
check empty 1 "$(home empty - - -)" \
  "SUPERPOWERS claude NOT_INSTALLED adapted=$adapted" \
  "SUPERPOWERS codex NOT_INSTALLED config=absent" \
  "MATT claude PIN_NOT_INSTALLED" \
  "RESULT REVIEW_NEEDED"

# #379: Cursor (usage layer only) is read from its plugin cache. Absent is
# informational; behind is informational; newer than the record or the pin, or
# an unrecognised cache, fails like the other tools.
matt_pin_version="$(awk -F'"v' '/^matt_version=/ { sub(/"$/, "", $2); print $2 }' "$root/codex/install-skills.sh")"
cursor_cache() {
  local dir="$1" marketplace="$2" plugin="$3" manifest="$4" version="$5"
  mkdir -p "$dir/.cursor/plugins/cache/$marketplace/$plugin/c0ffee/$(dirname "$manifest")"
  printf '{"name": "%s", "version": "%s"}\n' "$plugin" "$version" \
    >"$dir/.cursor/plugins/cache/$marketplace/$plugin/c0ffee/$manifest"
}
dir="$(home cursor-absent "$adapted" registered "$adapted")"
check cursor-absent 0 "$dir" \
  "SUPERPOWERS cursor NOT_INSTALLED adapted=$adapted" \
  "MATT cursor NOT_INSTALLED pinned=$matt_pin_version" \
  "RESULT PASS"
dir="$(home cursor-behind "$adapted" registered "$adapted")"
cursor_cache "$dir" cursor-public superpowers .cursor-plugin/plugin.json "$older"
cursor_cache "$dir" mattpocock mattpocock-skills .claude-plugin/plugin.json 1.2.0
before="$(snapshot "$dir")"
check cursor-behind 0 "$dir" \
  "SUPERPOWERS cursor BEHIND cached=$older adapted=$adapted" \
  "MATT cursor BEHIND cached=1.2.0 pinned=$matt_pin_version" \
  "RESULT PASS"
[[ "$(snapshot "$dir")" == "$before" ]] || fail "zero-write: the Cursor cache changed during a read"
dir="$(home cursor-current "$adapted" registered "$adapted")"
cursor_cache "$dir" cursor-public superpowers package.json "$adapted"
cursor_cache "$dir" mattpocock mattpocock-skills .claude-plugin/plugin.json "$matt_pin_version"
check cursor-current 0 "$dir" \
  "SUPERPOWERS cursor ADAPTED cached=$adapted adapted=$adapted" \
  "MATT cursor ADAPTED cached=$matt_pin_version pinned=$matt_pin_version" \
  "RESULT PASS"
dir="$(home cursor-newer "$adapted" registered "$adapted")"
cursor_cache "$dir" cursor-public superpowers .cursor-plugin/plugin.json "$newer"
check cursor-newer 1 "$dir" \
  "SUPERPOWERS cursor REVIEW_NEEDED cached=$newer adapted=$adapted" \
  "RESULT REVIEW_NEEDED"
dir="$(home cursor-no-manifest "$adapted" registered "$adapted")"
mkdir -p "$dir/.cursor/plugins/cache/mattpocock/mattpocock-skills/c0ffee"
check cursor-no-manifest 1 "$dir" "RESULT REVIEW_NEEDED"
grep -q '^MATT cursor UNKNOWN (' <<<"$output" || fail "cursor-no-manifest: Matt side is not UNKNOWN: $output"
dir="$(home cursor-two-versions "$adapted" registered "$adapted")"
cursor_cache "$dir" cursor-public superpowers .cursor-plugin/plugin.json "$adapted"
cursor_cache "$dir" other-market superpowers .cursor-plugin/plugin.json "$older"
check cursor-two-versions 1 "$dir" "RESULT REVIEW_NEEDED"
grep -q '^SUPERPOWERS cursor UNKNOWN (' <<<"$output" || fail "cursor-two-versions: not UNKNOWN: $output"

dir="$(home unreadable "$adapted" registered "$adapted")"
sed -i.bak 's/"version": 2/"version": 3/' "$dir/.claude/plugins/installed_plugins.json"
rm -f "$dir/.claude/plugins/installed_plugins.json.bak"
check unreadable 1 "$dir" "RESULT REVIEW_NEEDED"
grep -Fq 'SUPERPOWERS claude UNKNOWN (installed_plugins.json schema is not version 2)' <<<"$output" ||
  fail "unreadable: claude side is not UNKNOWN: $output"

# Malformed inputs never pass: each one is UNKNOWN and fails the run.
unknown_case() {
  local label="$1" side="$2" dir="$3"
  check "$label" 1 "$dir" "RESULT REVIEW_NEEDED"
  grep -q "^SUPERPOWERS $side UNKNOWN (" <<<"$output" || fail "$label: $side side is not UNKNOWN: $output"
}
dir="$(home claude-bare-key "$adapted" registered "$adapted")"
sed -i.bak 's/"superpowers@claude-plugins-official"/"superpowers"/' "$dir/.claude/plugins/installed_plugins.json"
rm -f "$dir/.claude/plugins/installed_plugins.json.bak"
unknown_case claude-bare-key claude "$dir"
dir="$(home codex-string-enabled "$adapted" registered "$adapted")"
sed -i.bak 's/^enabled = true$/enabled = "true"/' "$dir/.codex/config.toml"
rm -f "$dir/.codex/config.toml.bak"
unknown_case codex-string-enabled codex "$dir"
dir="$(home codex-scalar-setting "$adapted" registered "$adapted")"
printf '[marketplaces.curated]\nsource = "x"\n\n[plugins]\n"superpowers@curated" = true\n' >"$dir/.codex/config.toml"
unknown_case codex-scalar-setting codex "$dir"
dir="$(home codex-scalar-marketplace "$adapted" registered "$adapted")"
printf '[marketplaces]\ncurated = 42\n\n[plugins."superpowers@curated"]\nenabled = true\n' >"$dir/.codex/config.toml"
unknown_case codex-scalar-marketplace codex "$dir"
if [[ "$(id -u)" != 0 ]]; then
  dir="$(home codex-unlistable-cache "$adapted" registered "$adapted")"
  chmod 000 "$dir/.codex/plugins/cache/curated/superpowers"
  unknown_case codex-unlistable-cache codex "$dir"
  chmod 755 "$dir/.codex/plugins/cache/curated/superpowers"
fi

fake_cli claude 'no version here'
check cli-unknown 1 "$(home cli-unknown "$adapted" registered "$adapted")" \
  "CLI claude UNKNOWN" \
  "RESULT REVIEW_NEEDED"

rm -f "$bin/claude" "$bin/codex"
check no-cli 0 "$(home no-cli "$adapted" registered "$adapted")" \
  "CLI claude NOT_FOUND" \
  "CLI codex NOT_FOUND" \
  "RESULT PASS"

# Source-only and a malformed record, in a copied tree so the real record stays untouched.
tree="$tmp/tree"
mkdir -p "$tree/codex/tools" "$tree/codex/config"
cp "$root/codex/tools/check-external-skill-versions.sh" "$root/codex/tools/check-external-skill-versions.py" "$tree/codex/tools/"
cp "$root/codex/config/external-skill-adaptation.json" "$tree/codex/config/"
output="$(bash "$tree/codex/tools/check-external-skill-versions.sh" --source-only)"
[[ "$output" == "RECORD_OK superpowers adapted=$adapted" ]] || fail "source-only: $output"
printf '{"schema_version": 1, "superpowers": {"adapted_version": "latest", "issue": 375}}\n' \
  >"$tree/codex/config/external-skill-adaptation.json"
set +e
output="$(bash "$tree/codex/tools/check-external-skill-versions.sh" --source-only)"
status=$?
set -e
[[ "$status" == 2 && "$output" == RECORD_INVALID:* ]] || fail "malformed record: exit $status: $output"
printf '{"schema_version": 1, "superpowers": {"adapted_version": "7.0.0", "issue": 375, "pin": true}}\n' \
  >"$tree/codex/config/external-skill-adaptation.json"
set +e
output="$(bash "$tree/codex/tools/check-external-skill-versions.sh" --source-only)"
status=$?
set -e
[[ "$status" == 2 && "$output" == RECORD_INVALID:* ]] || fail "unknown record key: exit $status: $output"

for args in "--bogus" "--home" "--source-only extra"; do
  set +e
  # shellcheck disable=SC2086 # split on purpose: each entry is an argument list
  bash "$checker" $args >/dev/null 2>&1
  status=$?
  set -e
  [[ "$status" == 2 ]] || fail "usage: '$args' exit $status, expected 2"
done

echo "external skill versions tests passed"
