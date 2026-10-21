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
  "$platform/templates/docs/agents" "$platform/skills/demo/agents" "$platform/skills/codexonly"
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
printf 'interface: {}\n' >"$platform/skills/demo/agents/openai.yaml"
printf 'codex only v1\n' >"$platform/skills/codexonly/SKILL.md"
printf 'demo claude,codex\ncodexonly codex\n' >"$platform/skills/skills.manifest"
cat >"$platform/usage/bundle.json" <<'JSON'
{
  "contract_version": "aisoft-usage-bundle/v1",
  "lock_path": ".aisoft/platform-usage.lock.json",
  "members": [
    {"source": "usage/CONTRACT.md", "mode": "exact", "target": ".aisoft/platform-usage.md", "check": "platform-pin"},
    {"source": "templates/project/AGENTS.md", "mode": "pointer", "target": "AGENTS.md", "check": "pointer-sections"},
    {"source": "templates/docs/changes/_template/summary.md", "mode": "exact", "target": "docs/changes/_template/summary.md", "check": "change-templates"},
    {"source": "templates/docs/agents/domain.md", "mode": "seed", "target": "docs/agents/domain.md"},
    {"source": "skills/skills.manifest", "mode": "skill"},
    {"source": "skills/demo/SKILL.md", "mode": "skill"},
    {"source": "skills/demo/agents/openai.yaml", "mode": "skill"},
    {"source": "skills/codexonly/SKILL.md", "mode": "skill"}
  ],
  "releases": []
}
JSON
p=(--platform-root "$platform")

# 1. No release yet: verify fails and says how to fix it.
run 1 "${p[@]}" --verify
expect_contains '--release'

# 2. First release, then verify passes.
run 0 "${p[@]}" --release 1.0.0 --today 2026-10-18 --compatibility minor --notes n
expect_contains 'RELEASED 1.0.0 sha256:'
run 0 "${p[@]}" --verify
digest_v1="$(python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["releases"][-1]["bundle_digest"])' "$platform/usage/bundle.json")"

# 3. Releasing identical contents again is refused; so is a non-increasing version.
run 1 "${p[@]}" --release 1.0.1 --today 2026-10-18 --compatibility minor --notes n
expect_contains '不需要发布新版本'
printf 'summary v2\n' >"$platform/templates/docs/changes/_template/summary.md"
run 1 "${p[@]}" --release 1.0.0 --today 2026-10-19 --compatibility minor --notes n
expect_contains '必须大于最新版本'
run 1 "${p[@]}" --release 1.0 --today 2026-10-19 --compatibility minor --notes n
expect_contains 'MAJOR.MINOR.PATCH'

# 4. A member changed without a release: verify names the file and the fix.
run 1 "${p[@]}" --verify
expect_contains 'templates/docs/changes/_template/summary.md'
expect_contains '--release <新版本>'

# 5. Every distributed byte is versioned: even a project-facts placeholder in
# the pointer template is a member change.
printf 'summary v1\n' >"$platform/templates/docs/changes/_template/summary.md"
cp "$platform/templates/project/AGENTS.md" "$tmp/agents.orig"
printf -- '- 新增项目事实行\n' >>"$platform/templates/project/AGENTS.md"
run 1 "${p[@]}" --verify
expect_contains 'templates/project/AGENTS.md'
cp "$tmp/agents.orig" "$platform/templates/project/AGENTS.md"
run 0 "${p[@]}" --verify

# 6. Build exports the latest release deterministically, refuses a non-empty dir.
run 0 "${p[@]}" --build "$tmp/build1"
run 0 "${p[@]}" --build "$tmp/build2"
diff -r "$tmp/build1" "$tmp/build2" >/dev/null || fail 'two builds differ'
[[ -f "$tmp/build1/project/.aisoft/platform-usage.md" ]] || fail 'contract copy missing'
[[ -f "$tmp/build1/project/docs/agents/domain.md" ]] || fail 'seed missing'
# #379: one skill source, three project-level landings. Codex keeps its agents/
# metadata; Claude and Cursor get only what their declaration allows.
for landing in .claude/skills .agents/skills .cursor/skills; do
  [[ -f "$tmp/build1/project/$landing/demo/SKILL.md" ]] || fail "skill missing in $landing"
done
[[ -f "$tmp/build1/project/.agents/skills/demo/agents/openai.yaml" ]] || fail 'codex metadata missing'
[[ ! -e "$tmp/build1/project/.claude/skills/demo/agents" ]] || fail 'claude landing got codex metadata'
[[ ! -e "$tmp/build1/project/.cursor/skills/demo/agents" ]] || fail 'cursor landing got codex metadata'
[[ -f "$tmp/build1/project/.agents/skills/codexonly/SKILL.md" ]] || fail 'codex-only skill missing'
[[ ! -e "$tmp/build1/project/.claude/skills/codexonly" ]] || fail 'codex-only skill leaked to claude'
[[ ! -e "$tmp/build1/project/.cursor/skills/codexonly" ]] || fail 'codex-only skill leaked to cursor'
[[ ! -e "$tmp/build1/skills" ]] || fail 'skills must land inside the project tree'
[[ ! -e "$tmp/build1/project/skills.manifest" ]] || fail 'the landing declaration has no project copy'
# The declaration decides the landings, so it is a member: changing only the
# targets without a new release must fail verify (and therefore build).
cp "$platform/skills/skills.manifest" "$tmp/skills.manifest.saved"
printf 'demo codex\ncodexonly codex\n' >"$platform/skills/skills.manifest"
run 1 "${p[@]}" --verify
run 1 "${p[@]}" --build "$tmp/build-targets-only"
cp "$tmp/skills.manifest.saved" "$platform/skills/skills.manifest"
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
run 0 "${p[@]}" --release 1.1.0 --today 2026-10-19 --compatibility minor --notes n
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

# 11b. #409: the project may add legacy_changes_before; any other extra key or a
# malformed threshold leaves the lock unsupported.
lock_variant() {
  python3 -B - "$project/.aisoft/platform-usage.lock.json" "$unpinned/.aisoft/platform-usage.lock.json" "$1" "$2" <<'PY'
import json, sys
lock = json.load(open(sys.argv[1]))
lock[sys.argv[3]] = json.loads(sys.argv[4])
open(sys.argv[2], "w").write(json.dumps(lock))
PY
}
lock_variant legacy_changes_before 57
run 0 "${p[@]}" --project-status "$unpinned"
expect_contains $'platform-pin\tPASS\tpin 1.0.0'
for bad in 0 true '"57"' 1.5; do
  lock_variant legacy_changes_before "$bad"
  run 0 "${p[@]}" --project-status "$unpinned"
  expect_contains '格式不受支持'
done
lock_variant unknown_key 1
run 0 "${p[@]}" --project-status "$unpinned"
expect_contains '格式不受支持'

# 12. A pinned project whose contract copy drifted fails platform-pin.
printf 'edited\n' >"$project/.aisoft/platform-usage.md"
run 0 "${p[@]}" --project-status "$project"
expect_contains $'platform-pin\tGAP\t.aisoft/platform-usage.md 与 1.0.0 不一致'

# 13. Rewriting history is detected (on a copy; later cases need a valid platform).
rewritten="$tmp/rewritten"
cp -R "$platform" "$rewritten"
python3 -B - "$rewritten/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"][0]["members"][0]["sha256"] = "0" * 64
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 --platform-root "$rewritten" --verify
expect_contains '历史被改写'
python3 -B - "$rewritten/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"].reverse()
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 --platform-root "$rewritten" --verify
expect_contains '历史只能追加'

# 14. Declaration rules: an exact member must belong to a check, and every
# check must have at least one member.
declared="$tmp/declared"
cp -R "$platform" "$declared"
python3 -B - "$declared/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"] = []
del bundle["members"][0]["check"]
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 --platform-root "$declared" --release 2.0.0 --today 2026-10-20 --compatibility minor --notes n
expect_contains 'exact 成员必须归入一个核对项'
python3 -B - "$declared/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["members"] = bundle["members"][1:]
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 --platform-root "$declared" --release 2.0.0 --today 2026-10-20 --compatibility minor --notes n
expect_contains '缺少归入 platform-pin 的成员'

# 15. Pointer boundaries follow awk's LF-only records: a U+2028 before the
# next heading does not end the pointer, and CRLF headings do not match.
lsep="$(printf '\342\200\250')"
pointer_project="$tmp/pointer-project"
cp -R "$tmp/build1/project" "$pointer_project"
python3 -B - "$pointer_project/AGENTS.md" "$lsep" <<'PY'
import sys
path, lsep = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
text = text.replace("path v1\n\n## 项目事实", "path v1" + lsep + "## 项目事实\n注入内容" + lsep + "\n## 项目事实", 1)
open(path, "w", encoding="utf-8").write(text)
PY
run 0 "${p[@]}" --project-status "$pointer_project"
expect_contains $'pointer-sections\tGAP'
cp "$tmp/build1/project/AGENTS.md" "$pointer_project/AGENTS.md"
sed 's/$/\r/' "$tmp/build1/project/AGENTS.md" >"$pointer_project/AGENTS.md"
run 0 "${p[@]}" --project-status "$pointer_project"
expect_contains $'pointer-sections\tGAP\tAGENTS.md 缺少常驻指针两节'

# 16. With --baseline-ref, releases published on that ref are immutable even
# when every digest is recomputed consistently.
anchored="$tmp/anchored"
cp -R "$platform" "$anchored"
python3 -B - "$anchored/usage/bundle.json" <<'PY'
import json, sys
path = sys.argv[1]
bundle = json.load(open(path))
bundle["releases"] = bundle["releases"][:0]
open(path, "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
printf 'summary v1\n' >"$anchored/templates/docs/changes/_template/summary.md"
a=(--platform-root "$anchored")
run 0 "${a[@]}" --release 1.0.0 --today 2026-10-18 --compatibility minor --notes n
git -C "$anchored" init -q -b main
git -C "$anchored" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$anchored" -c user.name=t -c user.email=t@example.invalid commit -q -m base
run 0 "${a[@]}" --verify --baseline-ref main
run 1 "${a[@]}" --verify --baseline-ref no-such-ref
expect_contains '基线 no-such-ref 不存在'
# Rewrite 1.0.0 consistently: change a member, recompute its digests in place.
printf 'contract rewritten\n' >"$anchored/usage/CONTRACT.md"
python3 -B - "$root/codex/tools/usage-bundle.py" "$anchored" <<'PY'
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("ub", sys.argv[1])
ub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ub)
root = Path(sys.argv[2])
bundle = json.loads((root / "usage/bundle.json").read_text(encoding="utf-8"))
members = ub.current_members(root, bundle)
bundle["releases"][0]["members"] = members
bundle["releases"][0]["bundle_digest"] = ub.compute_bundle_digest(members)
(root / "usage/bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
run 0 "${a[@]}" --verify
run 1 "${a[@]}" --verify --baseline-ref main
expect_contains '已发布的版本被改写或删除'
# Appending after the published prefix is fine.
git -C "$anchored" checkout -q -- usage/bundle.json usage/CONTRACT.md
printf 'contract v2\n' >"$anchored/usage/CONTRACT.md"
run 0 "${a[@]}" --release 1.1.0 --today 2026-10-19 --compatibility minor --notes n
run 0 "${a[@]}" --verify --baseline-ref main

# The lock location is fixed by the contract version.
sed 's#"lock_path": ".aisoft/platform-usage.lock.json"#"lock_path": ".aisoft/other-lock.json"#' \
  "$anchored/usage/bundle.json" >"$tmp/moved.json"
cp "$tmp/moved.json" "$anchored/usage/bundle.json"
run 1 "${a[@]}" --verify
expect_contains 'lock_path 在 aisoft-usage-bundle/v1 中固定为'

# 18. #392: vendored skill packs. The member is the snapshot manifest; build
# re-verifies the snapshot and lands Matt in .agents and .cursor, superpowers
# only in .cursor, and neither in .claude.
vplatform="$tmp/vplatform"
cp -R "$platform" "$vplatform"
mkdir -p "$vplatform/codex/vendor/mattpocock" "$vplatform/codex/vendor/superpowers"
cp -R "$root/codex/vendor/mattpocock/v1.3.1" "$vplatform/codex/vendor/mattpocock/"
cp -R "$root/codex/vendor/superpowers/v7.0.0" "$vplatform/codex/vendor/superpowers/"
add_member() {
  python3 -B - "$vplatform/usage/bundle.json" "$1" <<'PY'
import json, sys
path, member = sys.argv[1], json.loads(sys.argv[2])
bundle = json.load(open(path))
bundle["members"].append(member)
open(path, "w").write(json.dumps(bundle, indent=2) + "\n")
PY
}
v=(--platform-root "$vplatform")
add_member '{"source": "codex/vendor/mattpocock/v1.3.1/manifest.json", "mode": "vendor"}'
add_member '{"source": "codex/vendor/superpowers/v7.0.0/manifest.json", "mode": "vendor"}'
run 0 "${v[@]}" --release 9.0.0 --today 2026-10-20 --compatibility minor --notes n
run 0 "${v[@]}" --build "$tmp/vbuild"
vp="$tmp/vbuild/project"
for landing in .agents/skills .cursor/skills; do
  [[ -f "$vp/$landing/triage/SKILL.md" ]] || fail "matt missing in $landing"
done
[[ -f "$vp/.cursor/skills/using-superpowers/SKILL.md" ]] || fail 'superpowers missing in .cursor/skills'
[[ -x "$vp/.cursor/skills/brainstorming/scripts/start-server.sh" ]] || fail 'superpowers script lost its mode'
[[ ! -x "$vp/.cursor/skills/brainstorming/SKILL.md" ]] || fail 'a document was exported executable'
# Modes come from the bytes, not the platform tree: a lost execute bit changes
# neither the release digest nor what the release exports.
chmod 644 "$vplatform/codex/vendor/superpowers/v7.0.0/skills/brainstorming/scripts/start-server.sh"
run 0 "${v[@]}" --build "$tmp/vbuild-mode"
[[ -x "$tmp/vbuild-mode/project/.cursor/skills/brainstorming/scripts/start-server.sh" ]] ||
  fail 'export mode followed the platform tree instead of the release'
[[ ! -e "$vp/.agents/skills/using-superpowers" ]] || fail 'superpowers must not land in .agents/skills'
[[ ! -e "$vp/.claude/skills/using-superpowers" && ! -e "$vp/.claude/skills/triage" ]] || fail 'vendor packs must not land in .claude/skills'
diff -r "$root/codex/vendor/superpowers/v7.0.0/skills/systematic-debugging" \
  "$vp/.cursor/skills/systematic-debugging" >/dev/null || fail 'superpowers landing differs from the snapshot'
[[ -f "$vp/.cursor/skills/demo/SKILL.md" ]] || fail 'platform skill landing lost'
# A changed snapshot byte fails verify and build without a manifest change.
printf '\n' >>"$vplatform/codex/vendor/superpowers/v7.0.0/skills/using-superpowers/SKILL.md"
run 1 "${v[@]}" --verify
expect_contains 'vendor 快照与 manifest 不符'
run 1 "${v[@]}" --build "$tmp/vbuild-tampered"
cp "$root/codex/vendor/superpowers/v7.0.0/skills/using-superpowers/SKILL.md" \
  "$vplatform/codex/vendor/superpowers/v7.0.0/skills/using-superpowers/SKILL.md"
run 0 "${v[@]}" --verify
# Only known packs, only their manifest, and never a project target.
cp "$vplatform/usage/bundle.json" "$tmp/vbundle.json"
add_member '{"source": "codex/vendor/other/v1.0.0/manifest.json", "mode": "vendor"}'
run 1 "${v[@]}" --verify
expect_contains 'vendor 成员必须是'
cp "$tmp/vbundle.json" "$vplatform/usage/bundle.json"
add_member '{"source": "codex/vendor/superpowers/v7.0.0/LICENSE", "mode": "vendor"}'
run 1 "${v[@]}" --verify
expect_contains 'vendor 成员必须是'
cp "$tmp/vbundle.json" "$vplatform/usage/bundle.json"
python3 -B - "$vplatform/usage/bundle.json" <<'PY'
import json, sys
bundle = json.load(open(sys.argv[1]))
bundle["members"][-1]["target"] = ".cursor/skills"
open(sys.argv[1], "w").write(json.dumps(bundle, indent=2) + "\n")
PY
run 1 "${v[@]}" --verify
expect_contains 'vendor 成员没有项目落点'
cp "$tmp/vbundle.json" "$vplatform/usage/bundle.json"
# A vendored skill may not share a name with a platform skill.
mkdir -p "$vplatform/skills/triage"
printf 'platform triage\n' >"$vplatform/skills/triage/SKILL.md"
printf 'demo claude,codex\ncodexonly codex\ntriage codex\n' >"$vplatform/skills/skills.manifest"
add_member '{"source": "skills/triage/SKILL.md", "mode": "skill"}'
run 0 "${v[@]}" --release 9.1.0 --today 2026-10-20 --compatibility minor --notes n
run 1 "${v[@]}" --build "$tmp/vbuild-collision"
expect_contains '落点冲突'

# 19. #402: every new release carries one line of notes and a compatibility
# level; a pinned project behind a major release is a GAP, otherwise a NOTE.
cplatform="$tmp/cplatform"
cp -R "$platform" "$cplatform"
c=(--platform-root "$cplatform")
printf 'contract c2\n' >"$cplatform/usage/CONTRACT.md"
run 1 "${c[@]}" --release 3.0.0 --today 2026-10-21
expect_contains '--compatibility patch|minor|major --notes TEXT'
run 1 "${c[@]}" --release 3.0.0 --today 2026-10-21 --compatibility huge --notes n
expect_contains '--compatibility 必须是 patch|minor|major'
run 1 "${c[@]}" --release 3.0.0 --today 2026-10-21 --compatibility patch --notes ' '
expect_contains '--notes 必须是一句非空说明'
cpinned="$tmp/cpinned"
cp -R "$project" "$cpinned"
cp "$tmp/build1/project/.aisoft/platform-usage.md" "$cpinned/.aisoft/platform-usage.md"
run 0 "${c[@]}" --release 1.2.0 --today 2026-10-21 --compatibility patch --notes 'patch release'
run 0 "${c[@]}" --project-status "$cpinned"
expect_contains $'platform-pin\tPASS\tpin 1.0.0'
expect_contains '落后区间最高兼容级别 minor'
printf 'contract c3\n' >"$cplatform/usage/CONTRACT.md"
run 0 "${c[@]}" --release 2.0.0 --today 2026-10-21 --compatibility major --notes 'major release'
run 0 "${c[@]}" --project-status "$cpinned"
expect_contains $'platform-pin\tGAP\t已 pin 1.0.0，落后区间含 major（2.0.0）'
grep -Fq '"compatibility": "major"' "$cplatform/usage/bundle.json" || fail 'compatibility not recorded'
# Published releases without the two keys stay valid; a half-declared one does not.
python3 -B - "$cplatform/usage/bundle.json" <<'PY'
import json, sys
bundle = json.load(open(sys.argv[1]))
del bundle["releases"][-1]["notes"]
open(sys.argv[1], "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 "${c[@]}" --verify
expect_contains '可另带 notes 与 compatibility'

# 20. #402: the session tool. tool-provenance members land under .aisoft/,
# keep an executable mode derived from their bytes, and a project's copy must
# equal the pinned release byte for byte. A release older than the tool is a NOTE.
tplatform="$tmp/tplatform"
cp -R "$platform" "$tplatform"
t=(--platform-root "$tplatform")
mkdir -p "$tplatform/codex/tools" "$tplatform/codex/runtime/demo"
printf '#!/usr/bin/env bash\necho demo v1\n' >"$tplatform/codex/tools/aisoft"
printf 'VALUE = 1\n' >"$tplatform/codex/runtime/demo/mod.py"
add_tool_member() {
  python3 -B - "$tplatform/usage/bundle.json" "$1" <<'PY'
import json, sys
path, member = sys.argv[1], json.loads(sys.argv[2])
bundle = json.load(open(path))
bundle["members"].append(member)
open(path, "w").write(json.dumps(bundle, indent=2) + "\n")
PY
}
cp "$tplatform/usage/bundle.json" "$tmp/tbundle.json"
add_tool_member '{"source": "codex/tools/aisoft", "mode": "exact", "target": "bin/aisoft", "check": "tool-provenance"}'
run 1 "${t[@]}" --verify
expect_contains 'tool-provenance 成员必须是 exact，落在 .aisoft/bin/ 或 .aisoft/lib/ 下'
cp "$tmp/tbundle.json" "$tplatform/usage/bundle.json"
add_tool_member '{"source": "codex/tools/aisoft", "mode": "exact", "target": ".aisoft/bin/aisoft", "check": "tool-provenance"}'
add_tool_member '{"source": "codex/runtime/demo/mod.py", "mode": "exact", "target": ".aisoft/lib/codex/runtime/demo/mod.py", "check": "tool-provenance"}'
run 0 "${t[@]}" --release 1.2.0 --today 2026-10-21 --compatibility minor --notes 'session tool'
run 0 "${t[@]}" --build "$tmp/tbuild"
tp="$tmp/tbuild/project"
[[ -x "$tp/.aisoft/bin/aisoft" ]] || fail 'session tool entry not executable'
[[ ! -x "$tp/.aisoft/lib/codex/runtime/demo/mod.py" ]] || fail 'a module was exported executable'
grep -Fq '"bundle_version": "1.2.0"' "$tp/.aisoft/lib/provenance.json" || fail 'provenance version'
python3 -B -c 'import json,sys; r=json.load(open(sys.argv[1]))["releases"]; assert [x["version"] for x in r]==["1.0.0","1.1.0","1.2.0"]' \
  "$tp/.aisoft/lib/usage/bundle.json" || fail 'history copy'
run 0 "${t[@]}" --project-status "$tp"
expect_contains $'tool-provenance\tPASS\t1.2.0'
printf 'VALUE = 2\n' >"$tp/.aisoft/lib/codex/runtime/demo/mod.py"
run 0 "${t[@]}" --project-status "$tp"
expect_contains $'tool-provenance\tGAP\t.aisoft/lib/codex/runtime/demo/mod.py 与 1.2.0 不一致'
printf 'VALUE = 1\n' >"$tp/.aisoft/lib/codex/runtime/demo/mod.py"
printf '{}\n' >"$tp/.aisoft/lib/provenance.json"
run 0 "${t[@]}" --project-status "$tp"
expect_contains '.aisoft/lib/provenance.json 的版本与 1.2.0 不符'
run 0 "${t[@]}" --project-status "$project"
expect_contains $'tool-provenance\tNOTE\t1.0.0 早于会话工具'

# 21. #402: --adopt writes the latest release into a clean checkout: pointer
# sections replaced in place, project facts and existing seeds kept, legacy
# templates and tool files the release no longer ships removed.
adopted="$tmp/adopted"
mkdir -p "$adopted/docs/changes/_template" "$adopted/docs/agents" "$adopted/.aisoft/lib/codex/old"
cat >"$adopted/AGENTS.md" <<'MD'
# AGENTS.md · Demo

## 平台声明（常驻指针）

old pointer

## 每 Issue 开发路径

old path

## 项目事实（按项目填写）

- 技术栈：本项目自己的事实
MD
printf 'project domain\n' >"$adopted/docs/agents/domain.md"
printf 'legacy\n' >"$adopted/docs/changes/_template/00-summary.md"
printf 'stale\n' >"$adopted/.aisoft/lib/codex/old/gone.py"
git -C "$adopted" init -q -b main
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid commit -q -m base
printf 'dirty\n' >"$adopted/untracked.txt"
run 1 "${t[@]}" --adopt "$adopted"
expect_contains '工作树不干净'
rm "$adopted/untracked.txt"
run 0 "${t[@]}" --adopt "$adopted"
expect_contains $'REMOVED\t.aisoft/lib/codex/old/gone.py'
expect_contains $'NOTE\tdocs/changes/_template/00-summary.md'
[[ -f "$adopted/docs/changes/_template/00-summary.md" ]] || fail 'adopt deleted a legacy template'
expect_contains $'KEPT\tdocs/agents/domain.md'
expect_contains $'WROTE\tAGENTS.md\t只替换常驻指针两节'
expect_contains $'tool-provenance\tPASS\t1.2.0'
expect_contains $'pointer-sections\tPASS\t1.2.0'
expect_contains 'ADOPTED 1.2.0'
grep -Fq -- '- 技术栈：本项目自己的事实' "$adopted/AGENTS.md" || fail 'adopt dropped project facts'
grep -Fq 'pointer v1' "$adopted/AGENTS.md" || fail 'adopt did not write the pointer'
! grep -Fq 'old pointer' "$adopted/AGENTS.md" || fail 'adopt kept the old pointer'
[[ "$(cat "$adopted/docs/agents/domain.md")" == 'project domain' ]] || fail 'adopt overwrote a seed'
[[ -x "$adopted/.aisoft/bin/aisoft" ]] || fail 'adopted tool entry not executable'
expect_contains $'CHANGED\t'
[[ -f "$adopted/.claude/skills/demo/SKILL.md" && -f "$adopted/.agents/skills/demo/SKILL.md" ]] || fail 'default tools are claude and codex'
[[ ! -e "$adopted/.cursor" ]] || fail 'cursor landing written without --tools cursor'
# Adopting the same release again on the committed result changes nothing.
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid commit -q -m adopt
run 0 "${t[@]}" --adopt "$adopted"
[[ -z "$(git -C "$adopted" status --porcelain)" ]] || fail 'second adopt changed the checkout'
# #409: re-adoption keeps the project's legacy threshold in the lock.
python3 -B - "$adopted/.aisoft/platform-usage.lock.json" <<'PY'
import json, sys
lock = json.load(open(sys.argv[1]))
lock["legacy_changes_before"] = 42
lock["bundle_version"] = "0.0.0"
open(sys.argv[1], "w").write(json.dumps(lock, indent=2) + "\n")
PY
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid commit -q -am legacy
run 0 "${t[@]}" --adopt "$adopted"
expect_contains 'legacy_changes_before=42'
jq -e '.legacy_changes_before == 42 and .bundle_version != "0.0.0"' "$adopted/.aisoft/platform-usage.lock.json" >/dev/null ||
  fail 'adopt dropped legacy_changes_before or kept the stale pin'
git -C "$adopted" -c user.name=t -c user.email=t@example.invalid commit -q -am readopt
run 64 "${t[@]}" --adopt "$tmp/does-not-exist"
# Codex #402 round 1: nothing is written through a symbolic link, inside the
# checkout (a template linked to AGENTS.md) or out of it (.aisoft elsewhere).
linked="$tmp/linked"
mkdir -p "$linked/docs/changes/_template" "$tmp/outside"
printf '# AGENTS.md · Linked\n\n- 技术栈：保留\n' >"$linked/AGENTS.md"
ln -s ../../../AGENTS.md "$linked/docs/changes/_template/summary.md"
git -C "$linked" init -q -b main
git -C "$linked" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$linked" -c user.name=t -c user.email=t@example.invalid commit -q -m base
cp "$linked/AGENTS.md" "$tmp/linked-agents.before"
run 1 "${t[@]}" --adopt "$linked"
expect_contains '--adopt 拒绝经符号链接写入：docs/changes/_template/summary.md'
cmp -s "$linked/AGENTS.md" "$tmp/linked-agents.before" || fail 'adopt wrote through a symbolic link'
[[ ! -e "$linked/.aisoft" ]] || fail 'adopt wrote before the symbolic link check finished'
rm "$linked/docs/changes/_template/summary.md"
ln -s "$tmp/outside" "$linked/.aisoft"
git -C "$linked" -c user.name=t -c user.email=t@example.invalid add -A
git -C "$linked" -c user.name=t -c user.email=t@example.invalid commit -q -m relink
run 1 "${t[@]}" --adopt "$linked"
expect_contains '--adopt 拒绝经符号链接写入：.aisoft'
[[ -z "$(ls -A "$tmp/outside")" ]] || fail 'adopt wrote outside the checkout'

# A release that shipped the session tool cannot be followed by one, or a
# declaration, that drops every tool-provenance member.
dropped="$tmp/dropped"
cp -R "$tplatform" "$dropped"
python3 -B - "$dropped/usage/bundle.json" <<'PY'
import json, sys
bundle = json.load(open(sys.argv[1]))
bundle["members"] = [m for m in bundle["members"] if m.get("check") != "tool-provenance"]
open(sys.argv[1], "w").write(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
PY
run 1 --platform-root "$dropped" --verify
expect_contains '不能整项删除 tool-provenance 成员'
run 1 "${t[@]}" --adopt "$adopted" --tools claude,vim
expect_contains '--tools 只能取'
run 0 "${t[@]}" --adopt "$adopted" --tools cursor
[[ -f "$adopted/.cursor/skills/demo/SKILL.md" ]] || fail '--tools cursor did not write the cursor landing'

# 17. Usage errors.
run 64 "${p[@]}"
run 64 "${p[@]}" --project-status "$tmp/does-not-exist"

echo 'test-usage-bundle: PASS'
