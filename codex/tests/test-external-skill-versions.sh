#!/usr/bin/env bash
# #375: external skill pack version report; #392: every tool against the
# platform pin. Every case runs against a fabricated home, fabricated CLIs,
# fabricated project checkouts and an isolated PATH; the real ~/.claude,
# ~/.codex and ~/.cursor are never read here.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'chmod -R u+rwx "$tmp" 2>/dev/null || true; rm -rf "$tmp"' EXIT

checker="$root/codex/tools/check-external-skill-versions.sh"
adapted="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["superpowers"]["adapted_version"])' \
  "$root/codex/config/external-skill-adaptation.json")"
pin="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' \
  "$root/codex/vendor/mattpocock/v1.3.1/manifest.json")"
sp_snapshot="$root/codex/vendor/superpowers/v$adapted"
sp_commit="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' \
  "$sp_snapshot/manifest.json")"

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

# home <name> <claude superpowers version|-> <codex marketplace state: registered|unregistered|disabled|-> <codex cached version> [claude commit]
home() {
  local dir="$tmp/$1" claude_version="$2" codex_state="$3" cached="$4" claude_commit="${5:-$sp_commit}"
  mkdir -p "$dir"
  if [[ "$claude_version" != "-" ]]; then
    mkdir -p "$dir/.claude/plugins"
    cat >"$dir/.claude/plugins/installed_plugins.json" <<JSON
{"version": 2, "plugins": {
  "superpowers@claude-plugins-official": [{"scope": "user", "version": "$claude_version", "gitCommitSha": "$claude_commit"}],
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

# check <label> <status> <home> <expected lines...>; set repo_args=(--repo DIR) to add a checkout
repo_args=()
check() {
  local label="$1" want_status="$2" dir="$3" status line
  shift 3
  set +e
  output="$(PATH="$bin" bash "$checker" --home "$dir" ${repo_args[@]+"${repo_args[@]}"} 2>&1)"
  status=$?
  set -e
  [[ "$status" == "$want_status" ]] || fail "$label: exit $status, expected $want_status: $output"
  for line in "$@"; do
    grep -Fqx -- "$line" <<<"$output" || fail "$label: missing line '$line' in: $output"
  done
}

unknown_case() {
  local label="$1" side="$2" dir="$3"
  check "$label" 1 "$dir" "RESULT REVIEW_NEEDED"
  grep -q "^SUPERPOWERS $side UNKNOWN (" <<<"$output" || fail "$label: $side side is not UNKNOWN: $output"
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
  "SUPERPOWERS claude PIN_CLEAN installed=$adapted commit=pinned pinned=$adapted" \
  "SUPERPOWERS codex PIN_CLEAN enabled=superpowers@curated marketplace=registered installed=$adapted pinned=$adapted" \
  "MATT claude PIN_CLEAN" \
  "RESULT PASS"
[[ "$(snapshot "$dir")" == "$before" ]] || fail "zero-write: the home changed during a read"
[[ ! -e "$root/codex/tools/__pycache__" ]] || fail "zero-write: a bytecode cache appeared next to the tool"

# A different version or a different commit than the pin is drift on either side.
check claude-newer 1 "$(home claude-newer "$newer" registered "$adapted")" \
  "SUPERPOWERS claude PIN_DRIFT installed=$newer commit=pinned pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
check claude-older 1 "$(home claude-older "$older" registered "$adapted")" \
  "SUPERPOWERS claude PIN_DRIFT installed=$older commit=pinned pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
check claude-other-commit 1 "$(home claude-other-commit "$adapted" registered "$adapted" "$(printf 'a%.0s' {1..40})")" \
  "SUPERPOWERS claude PIN_DRIFT installed=$adapted commit=differs pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
check codex-newer 1 "$(home codex-newer "$adapted" registered "$newer")" \
  "SUPERPOWERS codex PIN_DRIFT enabled=superpowers@curated marketplace=registered installed=$newer pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
check codex-older 1 "$(home codex-older "$adapted" registered "$older")" \
  "SUPERPOWERS codex PIN_DRIFT enabled=superpowers@curated marketplace=registered installed=$older pinned=$adapted" \
  "RESULT REVIEW_NEEDED"

# Enabled from an unregistered marketplace, or registered with nothing cached:
# Codex has no superpowers loaded. That informs, it does not fail.
check codex-not-loaded 0 "$(home codex-not-loaded "$adapted" unregistered "$older")" \
  "SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@curated marketplace=unregistered cached=$older pinned=$adapted" \
  "RESULT PASS"
dir="$(home codex-no-cache "$adapted" registered "$adapted")"
rm -rf "$dir/.codex/plugins/cache/curated/superpowers/abc123"
check codex-no-cache 0 "$dir" \
  "SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@curated marketplace=registered cached=none pinned=$adapted" \
  "RESULT PASS"
check codex-disabled 0 "$(home codex-disabled "$adapted" disabled "$adapted")" \
  "SUPERPOWERS codex PIN_NOT_INSTALLED enabled=none pinned=$adapted" \
  "RESULT PASS"

# #429: the official remote marketplace uses a new directory while the enable
# declaration can still name openai-curated. An old cache is not the new install.
remote_home() {
  local dir version="$2" marketplace="${3:-openai-curated}"
  dir="$(home "$1" "$adapted" - -)"
  mkdir -p "$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$version/.codex-plugin"
  printf '{"schema_version":1,"remote_plugin_id":"fixture-superpowers"}\n' \
    >"$dir/.codex/plugins/cache/openai-curated-remote/superpowers/.codex-remote-plugin-install.json"
  printf '[plugins."superpowers@%s"]\nenabled = true\n' "$marketplace" >"$dir/.codex/config.toml"
  printf '{"name":"superpowers","version":"%s"}\n' "$version" \
    >"$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$version/.codex-plugin/plugin.json"
  printf '%s\n' "$dir"
}
dir="$(remote_home codex-remote-newer "$newer")"
mkdir -p "$dir/.codex/plugins/cache/openai-curated/superpowers/old/.codex-plugin"
printf '{"name":"superpowers","version":"5.1.3"}\n' \
  >"$dir/.codex/plugins/cache/openai-curated/superpowers/old/.codex-plugin/plugin.json"
before="$(snapshot "$dir")"
check codex-remote-newer 1 "$dir" \
  "SUPERPOWERS codex PIN_DRIFT enabled=superpowers@openai-curated marketplace=builtin layout=openai-curated-remote installed=$newer pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
[[ "$(snapshot "$dir")" == "$before" ]] || fail "zero-write: remote plugin state changed"

for marketplace in openai-curated openai-curated-remote; do
  dir="$(remote_home "remote-clean-$marketplace" "$adapted" "$marketplace")"
  check "remote-clean-$marketplace" 0 "$dir" \
    "SUPERPOWERS codex PIN_CLEAN enabled=superpowers@$marketplace marketplace=builtin layout=openai-curated-remote installed=$adapted pinned=$adapted" \
    "RESULT PASS"
done
# The installation marker is metadata, never a version or a linked read target.
for state in linked directory; do
  dir="$(remote_home "remote-marker-$state" "$adapted")"
  path="$dir/.codex/plugins/cache/openai-curated-remote/superpowers/.codex-remote-plugin-install.json"
  rm "$path"
  case "$state" in
    linked) ln -s "$tmp/not-a-marker" "$path" ;;
    directory) mkdir "$path" ;;
  esac
  unknown_case "remote-marker-$state" codex "$dir"
done
# A cache is insufficient without an explicit, valid enable declaration.
for state in disabled undeclared absent; do
  dir="$(remote_home "remote-$state" "$adapted")"
  expected="enabled=none"
  case "$state" in
    disabled) printf '[plugins."superpowers@openai-curated"]\nenabled = false\n' >"$dir/.codex/config.toml" ;;
    undeclared) printf '[plugins]\n' >"$dir/.codex/config.toml" ;;
    absent) rm "$dir/.codex/config.toml"; expected="config=absent" ;;
  esac
  check "remote-$state" 0 "$dir" \
    "SUPERPOWERS codex PIN_NOT_INSTALLED $expected pinned=$adapted" "RESULT PASS"
done
dir="$(remote_home remote-other-market "$adapted" other-market)"
check remote-other-market 0 "$dir" \
  "SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@other-market marketplace=unregistered cached=none pinned=$adapted" \
  "RESULT PASS"
# Missing remote layout still accepts the registered legacy marketplace.
dir="$(remote_home remote-legacy-fallback "$adapted")"
mv "$dir/.codex/plugins/cache/openai-curated-remote" "$dir/.codex/plugins/cache/openai-curated"
printf '[marketplaces.openai-curated]\nsource = "x"\n[plugins."superpowers@openai-curated"]\nenabled = true\n' >"$dir/.codex/config.toml"
check remote-legacy-fallback 0 "$dir" \
  "SUPERPOWERS codex PIN_CLEAN enabled=superpowers@openai-curated marketplace=registered installed=$adapted pinned=$adapted" \
  "RESULT PASS"

# Present but ambiguous or invalid remote metadata cannot fall back to an old
# clean cache, and must never choose the highest version.
dir="$(remote_home remote-multiple "$adapted")"
release="$dir/.codex/plugins/cache/openai-curated-remote/superpowers"
mkdir -p "$release/$newer/.codex-plugin"
printf '{"name":"superpowers","version":"%s"}\n' "$newer" >"$release/$newer/.codex-plugin/plugin.json"
unknown_case remote-multiple codex "$dir"
dir="$(remote_home remote-empty "$adapted")"
rm -rf "$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$adapted"
unknown_case remote-empty codex "$dir"
dir="$(remote_home remote-nonnumeric "$adapted")"
mv "$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$adapted" \
  "$dir/.codex/plugins/cache/openai-curated-remote/superpowers/latest"
unknown_case remote-nonnumeric codex "$dir"
metadata_cases=(
  'not-json' '[]' '{}' '{"version":"7.0.0"}' '{"name":"elsewhere","version":"7.0.0"}'
  '{"name":"superpowers"}' '{"name":"superpowers","version":true}'
  '{"name":"superpowers","version":"latest"}'
  "{\"name\":\"superpowers\",\"version\":\"$older\"}"
  "{\"name\":\"superpowers\",\"version\":\"$adapted\",\"version\":\"$adapted\"}"
)
for index in "${!metadata_cases[@]}"; do
  dir="$(remote_home "remote-bad-json-$index" "$adapted")"
  printf '%s\n' "${metadata_cases[$index]}" \
    >"$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$adapted/.codex-plugin/plugin.json"
  mkdir -p "$dir/.codex/plugins/cache/openai-curated/superpowers/old/.codex-plugin"
  printf '{"name":"superpowers","version":"%s"}\n' "$adapted" \
    >"$dir/.codex/plugins/cache/openai-curated/superpowers/old/.codex-plugin/plugin.json"
  printf '[marketplaces.openai-curated]\nsource = "x"\n' >>"$dir/.codex/config.toml"
  unknown_case "remote-bad-json-$index" codex "$dir"
done
# Every component of the new plugin path is checked before metadata is read.
remote_parts=(
  .codex .codex/plugins .codex/plugins/cache .codex/plugins/cache/openai-curated-remote
  .codex/plugins/cache/openai-curated-remote/superpowers
  ".codex/plugins/cache/openai-curated-remote/superpowers/$adapted"
  ".codex/plugins/cache/openai-curated-remote/superpowers/$adapted/.codex-plugin"
  ".codex/plugins/cache/openai-curated-remote/superpowers/$adapted/.codex-plugin/plugin.json"
)
for index in "${!remote_parts[@]}"; do
  dir="$(remote_home "remote-linked-$index" "$adapted")"
  path="$dir/${remote_parts[$index]}"
  target="$tmp/remote-link-target-$index"
  mkdir -p "$target"
  mv "$path" "$target/content"
  ln -s "$target/content" "$path"
  before="$(snapshot "$target")"
  unknown_case "remote-linked-$index" codex "$dir"
  [[ "$(snapshot "$target")" == "$before" ]] ||
    fail "zero-write: linked remote target changed"
done
# Reject a linked .codex before opening its config. UNKNOWN/zero-write alone
# would miss a read that happened before the later plugin-path validation.
dir="$(remote_home remote-root-link-no-read "$adapted")"
mv "$dir/.codex" "$tmp/outside-codex"
ln -s "$tmp/outside-codex" "$dir/.codex"
PATH="$bin" python3 -B - "${checker%.sh}.py" "$dir" "$tmp/outside-codex/config.toml" <<'PY' >"$tmp/root-link-audit.out"
import os
import runpy
import sys

checker, home, forbidden = sys.argv[1:]
forbidden = os.path.realpath(forbidden)
opened = []

def audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)) and os.path.realpath(args[0]) == forbidden:
        opened.append(args[0])
        raise AssertionError("linked Codex config must never be opened")

sys.addaudithook(audit)
sys.argv = [checker, "--home", home]
try:
    runpy.run_path(checker, run_name="__main__")
except SystemExit as result:
    assert result.code == 1, result.code
else:
    raise AssertionError("checker did not report UNKNOWN")
assert not opened, opened
PY
grep -Fqx 'SUPERPOWERS codex UNKNOWN (.codex is not a real directory)' "$tmp/root-link-audit.out" ||
  fail "remote-root-link-no-read: parent link not rejected"
for state in missing directory fifo; do
  dir="$(remote_home "remote-metadata-$state" "$adapted")"
  path="$dir/.codex/plugins/cache/openai-curated-remote/superpowers/$adapted/.codex-plugin/plugin.json"
  rm "$path"
  case "$state" in
    directory) mkdir "$path" ;;
    fifo) mkfifo "$path" ;;
  esac
  unknown_case "remote-metadata-$state" codex "$dir"
done
dir="$(remote_home remote-file-parent "$adapted")"
rm -rf "$dir/.codex/plugins/cache/openai-curated-remote/superpowers"
printf 'x\n' >"$dir/.codex/plugins/cache/openai-curated-remote/superpowers"
unknown_case remote-file-parent codex "$dir"
for config in '[broken' '[plugins."superpowers@openai-curated"]\nenabled = "true"' \
  '[marketplaces]\nopenai-curated = 42\n[plugins."superpowers@openai-curated"]\nenabled = true' \
  '[plugins."superpowers@openai-curated"]\nenabled = true\n[plugins."superpowers@openai-curated-remote"]\nenabled = true'; do
  dir="$(remote_home remote-bad-config "$adapted")"
  printf '%b\n' "$config" >"$dir/.codex/config.toml"
  unknown_case remote-bad-config codex "$dir"
done
if [[ "$(id -u)" != 0 ]]; then
  for part in "superpowers" "superpowers/$adapted/.codex-plugin/plugin.json"; do
    dir="$(remote_home remote-unreadable "$adapted")"
    path="$dir/.codex/plugins/cache/openai-curated-remote/$part"
    chmod 000 "$path"
    unknown_case remote-unreadable codex "$dir"
    chmod u+rwx "$path"
  done
fi

# Nothing installed: superpowers is simply absent, but the Matt pin is not clean.
check empty 1 "$(home empty - - -)" \
  "SUPERPOWERS claude PIN_NOT_INSTALLED pinned=$adapted" \
  "SUPERPOWERS codex PIN_NOT_INSTALLED config=absent pinned=$adapted" \
  "MATT claude PIN_NOT_INSTALLED" \
  "RESULT REVIEW_NEEDED"

# A superpowers record without a commit cannot be compared with the pin.
dir="$(home claude-no-commit "$adapted" registered "$adapted")"
sed -i.bak "s/, \"gitCommitSha\": \"$sp_commit\"//" "$dir/.claude/plugins/installed_plugins.json"
rm -f "$dir/.claude/plugins/installed_plugins.json.bak"
check claude-no-commit 1 "$dir" "RESULT REVIEW_NEEDED"
grep -Fq 'SUPERPOWERS claude UNKNOWN (a superpowers record has no gitCommitSha)' <<<"$output" ||
  fail "claude-no-commit: not UNKNOWN: $output"

# #379/#392: Cursor has project-level landings only. Without --repo the lines
# are NOT_CHECKED and the user-level plugin cache is an annotation, whatever
# its state. With --repo the checkout's .cursor/skills is hashed against each
# snapshot manifest.
matt_pin_version="$(awk -F'"v' '/^matt_version=/ { sub(/"$/, "", $2); print $2 }' "$root/codex/install-skills.sh")"
cursor_cache() {
  local dir="$1" marketplace="$2" plugin="$3" manifest="$4" version="$5"
  mkdir -p "$dir/.cursor/plugins/cache/$marketplace/$plugin/c0ffee/$(dirname "$manifest")"
  printf '{"name": "%s", "version": "%s"}\n' "$plugin" "$version" \
    >"$dir/.cursor/plugins/cache/$marketplace/$plugin/c0ffee/$manifest"
}
dir="$(home cursor-absent "$adapted" registered "$adapted")"
check cursor-absent 0 "$dir" \
  "SUPERPOWERS cursor NOT_CHECKED cache=none pinned=$adapted" \
  "MATT cursor NOT_CHECKED cache=none pinned=$matt_pin_version" \
  "RESULT PASS"
dir="$(home cursor-cached "$adapted" registered "$adapted")"
cursor_cache "$dir" cursor-public superpowers .cursor-plugin/plugin.json "$older"
cursor_cache "$dir" mattpocock mattpocock-skills .claude-plugin/plugin.json 1.2.0
before="$(snapshot "$dir")"
check cursor-cached 0 "$dir" \
  "SUPERPOWERS cursor NOT_CHECKED cache=$older pinned=$adapted" \
  "MATT cursor NOT_CHECKED cache=1.2.0 pinned=$matt_pin_version" \
  "RESULT PASS"
[[ "$(snapshot "$dir")" == "$before" ]] || fail "zero-write: the Cursor cache changed during a read"
dir="$(home cursor-cache-unreadable "$adapted" registered "$adapted")"
mkdir -p "$dir/.cursor/plugins/cache/cursor-public"
printf 'x\n' >"$dir/.cursor/plugins/cache/cursor-public/superpowers"
check cursor-cache-unreadable 0 "$dir" \
  "SUPERPOWERS cursor NOT_CHECKED cache=unknown pinned=$adapted" \
  "RESULT PASS"

# project <name>: a checkout whose .cursor/skills holds both pinned packs.
project() {
  local repo="$tmp/$1" item
  mkdir -p "$repo/.cursor/skills"
  for item in "$sp_snapshot"/skills/*/; do
    cp -R "${item%/}" "$repo/.cursor/skills/"
  done
  while IFS= read -r item; do
    cp -R "$root/codex/vendor/mattpocock/v$matt_pin_version/$item" "$repo/.cursor/skills/"
  done < <(python3 -B -c 'import json, sys, os
for s in json.load(open(sys.argv[1]))["skills"]: print(os.path.dirname(s["path"]))' \
    "$root/codex/vendor/mattpocock/v$matt_pin_version/manifest.json")
  printf '%s\n' "$repo"
}
dir="$(home repo-home "$adapted" registered "$adapted")"
sp_count="$(find "$sp_snapshot/skills" -name SKILL.md | wc -l | tr -d ' ')"
matt_count="$(python3 -B -c 'import json, sys; print(json.load(open(sys.argv[1]))["skill_count"])' \
  "$root/codex/vendor/mattpocock/v$matt_pin_version/manifest.json")"
repo="$(project repo-clean)"
before="$(snapshot "$repo")"
repo_args=(--repo "$repo")
check repo-clean 0 "$dir" \
  "SUPERPOWERS cursor PIN_CLEAN skills=$sp_count cache=none pinned=$adapted" \
  "MATT cursor PIN_CLEAN skills=$matt_count cache=none pinned=$matt_pin_version" \
  "RESULT PASS"
[[ "$(snapshot "$repo")" == "$before" ]] || fail "zero-write: the checkout changed during a read"
printf '\n' >>"$repo/.cursor/skills/using-superpowers/SKILL.md"
rm -rf "$repo/.cursor/skills/writing-skills"
check repo-drift 1 "$dir" \
  "SUPERPOWERS cursor PIN_DRIFT differs=using-superpowers,writing-skills cache=none pinned=$adapted" \
  "MATT cursor PIN_CLEAN skills=$matt_count cache=none pinned=$matt_pin_version" \
  "RESULT REVIEW_NEEDED"
repo="$tmp/repo-empty"
mkdir -p "$repo"
repo_args=(--repo "$repo")
check repo-empty 0 "$dir" \
  "SUPERPOWERS cursor PIN_NOT_INSTALLED cache=none pinned=$adapted" \
  "MATT cursor PIN_NOT_INSTALLED cache=none pinned=$matt_pin_version" \
  "RESULT PASS"
repo="$(project repo-linked)"
mv "$repo/.cursor/skills/brainstorming" "$repo/brainstorming"
ln -s "$repo/brainstorming" "$repo/.cursor/skills/brainstorming"
repo_args=(--repo "$repo")
check repo-linked 1 "$dir" \
  "SUPERPOWERS cursor PIN_DRIFT differs=brainstorming cache=none pinned=$adapted" \
  "RESULT REVIEW_NEEDED"
# A checkout whose .cursor/skills is not a directory is unreadable, never absent.
repo="$tmp/repo-file-root"
mkdir -p "$repo/.cursor"
printf 'x\n' >"$repo/.cursor/skills"
repo_args=(--repo "$repo")
check repo-file-root 1 "$dir" "RESULT REVIEW_NEEDED"
grep -Fqx "SUPERPOWERS cursor UNKNOWN (.cursor/skills is not a directory)" <<<"$output" ||
  fail "repo-file-root: not UNKNOWN: $output"
repo_args=()

dir="$(home unreadable "$adapted" registered "$adapted")"
sed -i.bak 's/"version": 2/"version": 3/' "$dir/.claude/plugins/installed_plugins.json"
rm -f "$dir/.claude/plugins/installed_plugins.json.bak"
check unreadable 1 "$dir" "RESULT REVIEW_NEEDED"
grep -Fq 'SUPERPOWERS claude UNKNOWN (installed_plugins.json schema is not version 2)' <<<"$output" ||
  fail "unreadable: claude side is not UNKNOWN: $output"

# Malformed inputs never pass: each one is UNKNOWN and fails the run.
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
mkdir -p "$tree/usage" "$tree/codex/vendor/superpowers/v$adapted" "$tree/codex/vendor/mattpocock/v$matt_pin_version"
cp "$root/usage/bundle.json" "$tree/usage/"
cp "$sp_snapshot/manifest.json" "$tree/codex/vendor/superpowers/v$adapted/"
cp "$root/codex/vendor/mattpocock/v$matt_pin_version/manifest.json" "$tree/codex/vendor/mattpocock/v$matt_pin_version/"
cp "$root/codex/install-skills.sh" "$tree/codex/"
output="$(bash "$tree/codex/tools/check-external-skill-versions.sh" --source-only)"
[[ "$output" == "RECORD_OK superpowers adapted=$adapted pinned=$adapted commit=$sp_commit" ]] || fail "source-only: $output"
# The record must name the pinned version.
printf '{"schema_version": 1, "superpowers": {"adapted_version": "%s", "issue": 392}}\n' "$older" \
  >"$tree/codex/config/external-skill-adaptation.json"
set +e
output="$(bash "$tree/codex/tools/check-external-skill-versions.sh" --source-only)"
status=$?
set -e
[[ "$status" == 2 && "$output" == "RECORD_INVALID: superpowers.adapted_version $older is not the pinned $adapted" ]] ||
  fail "record off the pin: exit $status: $output"
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

# #408 (08 §7.1): --capabilities adds one CAPABILITY line per tool and RESULT
# follows them. The fixtures install every item; each case breaks one.
fake_cli claude '9.8.7 (Claude Code)'
fake_cli codex 'codex-cli 1.2.3'
for tool in jq rg git; do
  if command -v "$tool" >/dev/null; then ln -s "$(command -v "$tool")" "$bin/$tool"; fi
done
cat >"$bin/cursor-agent" <<'SH'
#!/bin/sh
case "$1" in
  --version) echo "2026.10.19-test" ;;
  status) if [ -e "$CURSOR_LOGGED_OUT" ]; then echo "Not logged in"; exit 1; fi; echo "Logged in as someone" ;;
esac
SH
chmod +x "$bin/cursor-agent"
export CURSOR_LOGGED_OUT="$tmp/cursor-logged-out"
skill_names() {
  awk -v want="$1" '!/^#/ && NF == 2 { n = split($2, t, ","); for (i = 1; i <= n; i++) if (t[i] == want) print $1 }' \
    "$root/skills/skills.manifest"
}
# installed <home>: maintainer-layer landings and the Codex Matt snapshot.
installed() {
  local dir="$1" name
  for name in $(skill_names claude); do
    mkdir -p "$dir/.claude/skills/$name"
    cp "$root/skills/$name/SKILL.md" "$dir/.claude/skills/$name/"
    if [[ -d "$root/skills/$name/references" ]]; then
      mkdir -p "$dir/.claude/skills/$name/references"
      cp "$root/skills/$name/references/"*.md "$dir/.claude/skills/$name/references/"
    fi
  done
  for name in $(skill_names codex); do
    mkdir -p "$dir/.agents/skills"
    cp -R "$root/skills/$name" "$dir/.agents/skills/"
  done
  mkdir -p "$dir/.agents/vendor/mattpocock/releases"
  cp -R "$root/codex/vendor/mattpocock/v$matt_pin_version" "$dir/.agents/vendor/mattpocock/releases/"
  ln -s "releases/v$matt_pin_version" "$dir/.agents/vendor/mattpocock/current"
  while IFS=' ' read -r name ref; do
    ln -s "../vendor/mattpocock/current/$ref" "$dir/.agents/skills/$name"
  done < <(python3 -B -c 'import json, sys, os
for s in json.load(open(sys.argv[1]))["skills"]: print(s["name"], os.path.dirname(s["path"]))' \
    "$root/codex/vendor/mattpocock/v$matt_pin_version/manifest.json")
}
# cursor_project <name>: project() plus the platform skills Cursor receives.
cursor_project() {
  local repo name
  repo="$(project "$1")"
  for name in $(skill_names claude); do
    mkdir -p "$repo/.cursor/skills/$name"
    cp "$root/skills/$name/SKILL.md" "$repo/.cursor/skills/$name/"
    if [[ -d "$root/skills/$name/references" ]]; then
      mkdir -p "$repo/.cursor/skills/$name/references"
      cp "$root/skills/$name/references/"*.md "$repo/.cursor/skills/$name/references/"
    fi
  done
  printf '%s\n' "$repo"
}
caps() {
  local label="$1" want_status="$2" dir="$3" line
  shift 3
  set +e
  output="$(PATH="$bin" bash "$checker" --home "$dir" --repo "$repo" --capabilities 2>&1)"
  status=$?
  set -e
  [[ "$status" == "$want_status" ]] || fail "$label: exit $status, expected $want_status: $output"
  for line in "$@"; do
    grep -Fq -- "$line" <<<"$output" || fail "$label: missing '$line' in: $output"
  done
}
dir="$(home caps-pass "$adapted" registered "$adapted")"
installed "$dir"
repo="$(cursor_project caps-repo)"
before="$(snapshot "$dir")$(snapshot "$repo")"
caps caps-pass 0 "$dir" \
  "CAPABILITY claude PASS platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=OK smoke=" \
  "CAPABILITY codex PASS platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=OK smoke=" \
  "CAPABILITY cursor PASS platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=OK" \
  "RESULT "
[[ "$(snapshot "$dir")$(snapshot "$repo")" == "$before" ]] || fail "zero-write: --capabilities changed the home or checkout"
if [[ -x "$bin/jq" && -x "$bin/rg" && -x "$bin/git" ]]; then
  grep -Fqx "RESULT PASS" <<<"$output" || fail "caps-pass: not RESULT PASS: $output"
fi
# Codex without superpowers is the registered external cause: KNOWN_EXTERNAL, not a GAP.
dir="$(home caps-known "$adapted" - -)"
installed "$dir"
caps caps-known 0 "$dir" \
  "CAPABILITY codex KNOWN_EXTERNAL platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=[PIN_NOT_INSTALLED config=absent pinned=$adapted]" \
  "(#392 Codex official marketplace does not offer the pinned version; the platform does not install it)"
# The new official layout's actual drift must not inherit the absence exemption.
dir="$(remote_home caps-remote-gap "$newer")"
installed "$dir"
caps caps-remote-gap 1 "$dir" \
  "CAPABILITY codex GAP platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=[PIN_DRIFT enabled=superpowers@openai-curated marketplace=builtin layout=openai-curated-remote installed=$newer pinned=$adapted]" \
  "RESULT GAP"
# Any other unmet item is a GAP: a drifted Claude landing, a drifted Codex
# Matt link, a logged-out Cursor, a Codex superpowers off the pin.
dir="$(home caps-gap "$adapted" registered "$newer")"
installed "$dir"
printf '\n' >>"$dir/.claude/skills/issue-session-flow/SKILL.md"
ln -sfn releases/v1.2.2 "$dir/.agents/vendor/mattpocock/current"
touch "$CURSOR_LOGGED_OUT"
caps caps-gap 1 "$dir" \
  "CAPABILITY claude GAP platform-skills=[PIN_DRIFT differs=issue-session-flow]" \
  "CAPABILITY codex GAP platform-skills=PIN_CLEAN matt=[PIN_DRIFT current=releases/v1.2.2] superpowers=[PIN_DRIFT" \
  "CAPABILITY cursor GAP platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=[NOT_LOGGED_IN]" \
  "RESULT GAP"
rm -f "$CURSOR_LOGGED_OUT"
# Codex Matt is the whole snapshot plus its load links, not only the manifest.
dir="$(home caps-matt-content "$adapted" registered "$adapted")"
installed "$dir"
printf '\n' >>"$dir/.agents/vendor/mattpocock/releases/v$matt_pin_version/skills/engineering/tdd/SKILL.md"
rm "$dir/.agents/skills/grill-me"
caps caps-matt-content 1 "$dir" "CAPABILITY codex GAP platform-skills=PIN_CLEAN matt=[PIN_DRIFT differs=grill-me,tdd]"
# A lock that is a link is not trusted: never a silent fallback to the latest release.
repo="$(cursor_project caps-linked-lock)"
mkdir -p "$repo/.aisoft"
printf '{"contract_version": 1, "bundle_version": "1.8.0", "bundle_digest": "x"}\n' >"$tmp/elsewhere-lock.json"
ln -s "$tmp/elsewhere-lock.json" "$repo/.aisoft/platform-usage.lock.json"
dir="$(home caps-linked-lock "$adapted" registered "$adapted")"
installed "$dir"
caps caps-linked-lock 1 "$dir" "CAPABILITY cursor GAP platform-skills=[UNKNOWN (.aisoft/platform-usage.lock.json is not a regular file)]"
# A checkout without Cursor landings: every Cursor item is PIN_NOT_INSTALLED, a GAP.
repo="$tmp/repo-empty"
dir="$(home caps-no-cursor "$adapted" registered "$adapted")"
installed "$dir"
caps caps-no-cursor 1 "$dir" "CAPABILITY cursor GAP platform-skills=[PIN_NOT_INSTALLED unpinned]" "RESULT GAP"
# Reverse proof: without the registration the same Codex state is a GAP.
caps_tree="$tmp/caps-tree"
mkdir -p "$caps_tree/codex/tools" "$caps_tree/codex/runtime" "$caps_tree/skill-for-claude"
cp -R "$root/skills" "$root/usage" "$caps_tree/"
cp -R "$root/codex/config" "$root/codex/vendor" "$caps_tree/codex/"
cp -R "$root/codex/runtime/aisoft_loop" "$caps_tree/codex/runtime/"
cp "$root/codex/install-skills.sh" "$caps_tree/codex/"
cp "$root/skill-for-claude/check-plugin-pin.sh" "$caps_tree/skill-for-claude/"
cp "$root/codex/tools/check-external-skill-versions.sh" "$caps_tree/codex/tools/"
python3 -B - "$root/codex/tools/check-external-skill-versions.py" "$caps_tree/codex/tools/check-external-skill-versions.py" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
emptied, count = re.subn(r"KNOWN_EXTERNAL = \{\n.*?\n\}\n", "KNOWN_EXTERNAL = {}\n", text, flags=re.S)
assert count == 1, "KNOWN_EXTERNAL block not found"
open(sys.argv[2], "w", encoding="utf-8").write(emptied)
PY
repo="$(cursor_project caps-repo-reverse)"
dir="$(home caps-reverse "$adapted" - -)"
installed "$dir"
set +e
output="$(PATH="$bin" bash "$caps_tree/codex/tools/check-external-skill-versions.sh" --home "$dir" --repo "$repo" --capabilities 2>&1)"
status=$?
set -e
if [[ "$status" != 1 ]] || ! grep -Fq "CAPABILITY codex GAP" <<<"$output"; then
  fail "reverse proof: an unregistered external cause must be a GAP: exit $status: $output"
fi
for args in "--capabilities" "--home /x --capabilities"; do
  set +e
  # shellcheck disable=SC2086 # split on purpose
  bash "$checker" $args >/dev/null 2>&1
  status=$?
  set -e
  [[ "$status" == 2 ]] || fail "usage: '$args' exit $status, expected 2"
done

for args in "--bogus" "--home" "--source-only extra" "--repo" "--repo /x --repo /y" "--home /x --source-only"; do
  set +e
  # shellcheck disable=SC2086 # split on purpose: each entry is an argument list
  bash "$checker" $args >/dev/null 2>&1
  status=$?
  set -e
  [[ "$status" == 2 ]] || fail "usage: '$args' exit $status, expected 2"
done

echo "external skill versions tests passed"
