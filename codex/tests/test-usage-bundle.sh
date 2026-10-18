#!/usr/bin/env bash
# #377: versioned platform usage bundle. Every case runs against a fabricated
# platform tree and fabricated project checkouts; the real usage/bundle.json is
# only verified, never rewritten.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

tool="$root/codex/tools/usage-bundle.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

# run <expected status> <args...>; output in $tmp/out
run() {
  local expected="$1" status=0
  shift
  bash "$tool" "$@" >"$tmp/out" 2>&1 || status=$?
  [[ "$status" == "$expected" ]] || {
    cat "$tmp/out" >&2
    fail "expected status $expected, got $status for: $*"
  }
}

expect_contains() {
  grep -Fq -- "$1" "$tmp/out" || {
    cat "$tmp/out" >&2
    fail "missing output: $1"
  }
}

# 0. The real bundle is consistent with the real members.
run 0 --verify
expect_contains 'VERIFIED '

# A minimal platform: one pointer template, one exact template, one seed, one skill.
platform="$tmp/platform"
mkdir -p "$platform/usage" "$platform/templates/project" "$platform/templates/docs/changes/_template" \
  "$platform/templates/docs/agents" "$platform/skills/demo"
cat >"$platform/templates/project/AGENTS.md" <<'MD'
# AGENTS.md · <项目名>

## 平台声明（常驻指针）

pointer v1

## 每 Issue 开发路径

path v1

## 项目事实（按项目填写）

- 技术栈：<语言>
MD
printf 'contract v1\n' >"$platform/usage/CONTRACT.md"
printf 'summary v1\n' >"$platform/templates/docs/changes/_template/summary.md"
printf 'seed v1\n' >"$platform/templates/docs/agents/domain.md"
printf 'skill v1\n' >"$platform/skills/demo/SKILL.md"
cat >"$platform/usage/bundle.json" <<'JSON'
{
  "contract_version": "aisoft-usage-bundle/v1",
  "lock_path": ".aisoft/platform-usage.lock.json",
  "members": [
    {"source": "usage/CONTRACT.md", "mode": "exact", "target": ".aisoft/platform-usage.md", "check": "platform-pin"},
    {"source": "templates/project/AGENTS.md", "mode": "pointer", "target": "AGENTS.md", "check": "pointer-sections"},
    {"source": "templates/docs/changes/_template/summary.md", "mode": "exact", "target": "docs/changes/_template/summary.md", "check": "change-templates"},
    {"source": "templates/docs/agents/domain.md", "mode": "seed", "target": "docs/agents/domain.md"},
    {"source": "skills/demo/SKILL.md", "mode": "skill"}
  ],
  "releases": []
}
JSON
p=(--platform-root "$platform")

# 1. No release yet: verify fails and says how to fix it.
run 1 "${p[@]}" --verify
expect_contains '--release'

# 2. First release, then verify passes.
run 0 "${p[@]}" --release 1.0.0 --today 2026-10-18
expect_contains 'RELEASED 1.0.0 sha256:'
run 0 "${p[@]}" --verify
digest_v1="$(python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["releases"][-1]["bundle_digest"])' "$platform/usage/bundle.json")"

# 3. Releasing identical contents again is refused; so is a non-increasing version.
run 1 "${p[@]}" --release 1.0.1 --today 2026-10-18
expect_contains '不需要发布新版本'
printf 'summary v2\n' >"$platform/templates/docs/changes/_template/summary.md"
run 1 "${p[@]}" --release 1.0.0 --today 2026-10-19
expect_contains '必须大于最新版本'
run 1 "${p[@]}" --release 1.0 --today 2026-10-19
expect_contains 'MAJOR.MINOR.PATCH'

# 4. A member changed without a release: verify names the file and the fix.
run 1 "${p[@]}" --verify
expect_contains 'templates/docs/changes/_template/summary.md'
expect_contains '--release <新版本>'

# 5. A pointer template change outside the pointer sections is not a member change.
printf 'summary v1\n' >"$platform/templates/docs/changes/_template/summary.md"
printf -- '- 新增项目事实行\n' >>"$platform/templates/project/AGENTS.md"
run 0 "${p[@]}" --verify

# 6. Build exports the latest release deterministically, refuses a non-empty dir.
run 0 "${p[@]}" --build "$tmp/build1"
run 0 "${p[@]}" --build "$tmp/build2"
diff -r "$tmp/build1" "$tmp/build2" >/dev/null || fail 'two builds differ'
[[ -f "$tmp/build1/project/.aisoft/platform-usage.md" ]] || fail 'contract copy missing'
[[ -f "$tmp/build1/project/docs/agents/domain.md" ]] || fail 'seed missing'
[[ -f "$tmp/build1/skills/skills/demo/SKILL.md" ]] || fail 'skill missing'
grep -Fq '"bundle_version": "1.0.0"' "$tmp/build1/project/.aisoft/platform-usage.lock.json" || fail 'lock version'
grep -Fq "\"bundle_digest\": \"$digest_v1\"" "$tmp/build1/project/.aisoft/platform-usage.lock.json" || fail 'lock digest'
run 1 "${p[@]}" --build "$tmp/build1"
expect_contains '必须不存在或为空'

# 7. A project copied from the build passes all three checks.
project="$tmp/project"
cp -R "$tmp/build1/project" "$project"
run 0 "${p[@]}" --project-status "$project"
expect_contains $'platform-pin\tPASS\tpin 1.0.0'
expect_contains $'pointer-sections\tPASS\t1.0.0'
expect_contains $'change-templates\tPASS\t1.0.0'

# 8. Project facts are the project's own; edits outside the pointer sections still pass.
printf -- '- 健康端点：/health\n' >>"$project/AGENTS.md"
run 0 "${p[@]}" --project-status "$project"
expect_contains $'pointer-sections\tPASS'

# 9. The platform moves to 1.1.0: a project pinned to 1.0.0 still passes, with a NOTE.
printf 'summary v2\n' >"$platform/templates/docs/changes/_template/summary.md"
run 0 "${p[@]}" --release 1.1.0 --today 2026-10-19
run 0 "${p[@]}" --project-status "$project"
expect_contains $'change-templates\tPASS\t1.0.0'
expect_contains $'platform-pin\tNOTE\t已 pin 1.0.0，平台最新版本 1.1.0'

# 10. Without a lock the project is checked against the latest release.
unpinned="$tmp/unpinned"
cp -R "$project" "$unpinned"
rm "$unpinned/.aisoft/platform-usage.lock.json"
run 0 "${p[@]}" --project-status "$unpinned"
expect_contains $'platform-pin\tGAP\t缺少 .aisoft/platform-usage.lock.json'
expect_contains $'change-templates\tGAP\tdocs/changes/_template/summary.md 与 1.1.0 不一致'

# 11. A lock naming an unknown version or carrying the wrong digest is a GAP.
sed 's/"1.0.0"/"9.9.9"/' "$project/.aisoft/platform-usage.lock.json" >"$unpinned/.aisoft/platform-usage.lock.json"
run 0 "${p[@]}" --project-status "$unpinned"
expect_contains '不在平台发布历史中'
sed 's/sha256:[0-9a-f]*/sha256:0000/' "$project/.aisoft/platform-usage.lock.json" >"$unpinned/.aisoft/platform-usage.lock.json"
run 0 "${p[@]}" --project-status "$unpinned"
expect_contains '摘要与平台记录的 1.0.0 不符'

# 12. A pinned project whose contract copy drifted fails platform-pin.
printf 'edited\n' >"$project/.aisoft/platform-usage.md"
run 0 "${p[@]}" --project-status "$project"
expect_contains $'platform-pin\tGAP\t.aisoft/platform-usage.md 与 1.0.0 不一致'

# 13. Rewriting history is detected; a missing pointer section is a GAP.
python3 -B - "$platform/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"][0]["members"][0]["sha256"] = "0" * 64
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 "${p[@]}" --verify
expect_contains '历史被改写'
python3 -B - "$platform/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"].reverse()
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 "${p[@]}" --verify
expect_contains '历史只能追加'

# 14. Usage errors.
run 64 "${p[@]}"
run 64 "${p[@]}" --project-status "$tmp/does-not-exist"

echo 'test-usage-bundle: PASS'
