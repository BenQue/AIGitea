#!/usr/bin/env bash
set -euo pipefail

# Issue #190：上游广播机制的行为闸门。用一个合成的平台根目录跑**真实的**脚本，
# 而不是复述它的逻辑——脚本从 BASH_SOURCE 推导 ROOT，把它复制进 fixture 就足以
# 把三份 manifest 和模板源全部换成受控内容，不碰本机的真实项目 checkout。

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL_SOURCE="$ROOT/codex/tools/change-template-sync.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

case_count=0
last_output=''

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

run_case() {
  local expected_status="$1"
  shift
  case_count=$((case_count + 1))
  set +e
  "$@" >"$TMP/case.stdout" 2>"$TMP/case.stderr"
  local actual_status=$?
  set -e
  last_output="$(cat "$TMP/case.stdout" "$TMP/case.stderr")"
  if [[ "$actual_status" != "$expected_status" ]]; then
    printf '%s\n' "$last_output" >&2
    fail "case $case_count expected status $expected_status, got $actual_status"
  fi
}

expect_contains() {
  grep -Fq -e "$1" <<<"$last_output" || fail "case $case_count missing text: $1"
}

expect_absent() {
  if grep -Fq -e "$1" <<<"$last_output"; then
    fail "case $case_count unexpectedly contains: $1"
  fi
}

# 断言一行「仓库 状态 细节」，但不把列宽写死——列宽是排版，不是合同。
expect_row() {
  local name="$1" status="$2" detail="${3:-}"
  local pattern="^$name +$status"
  if [[ -n "$detail" ]]; then
    pattern="$pattern +$detail"
  fi
  grep -Eq "$pattern" <<<"$last_output" ||
    fail "case $case_count missing row: $name $status $detail"
}

# 一个合成平台根：只有工具本身、三份 manifest 与模板源。
platform="$TMP/platform"
mkdir -p "$platform/codex/tools" "$platform/codex/config" \
  "$platform/templates/docs/changes/_template"
cp "$TOOL_SOURCE" "$platform/codex/tools/change-template-sync.sh"
tool="$platform/codex/tools/change-template-sync.sh"

for document in summary spec plan verification; do
  printf 'fixture %s v1\n' "$document" \
    >"$platform/templates/docs/changes/_template/$document.md"
done

cat >"$platform/codex/config/change-template-sync.json" <<'JSON'
{
  "contract_version": "change-template-sync/v1",
  "template_root": "templates/docs/changes/_template",
  "documents": ["summary.md", "spec.md", "plan.md", "verification.md"],
  "template_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "digest_updated": "2026-01-01",
  "downstream_required_check": "forbidden"
}
JSON

# holder-current 已同步；holder-stale 副本过期；holder-absent 没有 checkout；
# source-repo 显式声明不持有副本，必须完全不出现在清单里。
cat >"$platform/codex/config/gitea-governance.json" <<'JSON'
{
  "repositories": [
    {"name": "source-repo", "vendors_change_templates": false},
    {"name": "holder-current"},
    {"name": "holder-stale"},
    {"name": "holder-absent"}
  ]
}
JSON

downstream="$TMP/downstream"
for name in holder-current holder-stale; do
  mkdir -p "$downstream/$name/docs/changes/_template"
done
cat >"$platform/codex/config/host-access-broker.json" <<JSON
{
  "projects": [
    {"repository": "source-repo", "mac_checkout": "$downstream/source-repo"},
    {"repository": "holder-current", "mac_checkout": "$downstream/holder-current"},
    {"repository": "holder-stale", "mac_checkout": "$downstream/holder-stale"},
    {"repository": "holder-absent", "mac_checkout": null}
  ]
}
JSON

sync_copies() {
  local name="$1"
  cp "$platform/templates/docs/changes/_template/"*.md \
    "$downstream/$name/docs/changes/_template/"
}

sync_copies holder-current
sync_copies holder-stale
printf 'drifted\n' >>"$downstream/holder-stale/docs/changes/_template/spec.md"

# 1. 钉住的 digest 是占位值 → verify 必须红，并给出补救命令。
run_case 3 bash "$tool" --verify-digest
expect_contains 'digest 漂移'
expect_contains '--refresh-digest'

# 2. 刷新之后 verify 转绿，且 manifest 写进了传入的日期。
run_case 3 bash "$tool" --refresh-digest --today 2026-02-03
expect_contains 'digest: 已刷新'
grep -Fq '"digest_updated": "2026-02-03"' \
  "$platform/codex/config/change-template-sync.json" ||
  fail 'refresh 没有写入 --today 指定的日期'
run_case 0 bash "$tool" --verify-digest
expect_contains 'digest: pinned sha256:'

# 3. 幂等：digest 已是当前值时一个字节都不写。
before="$(cat "$platform/codex/config/change-template-sync.json")"
run_case 3 bash "$tool" --refresh-digest --today 2026-09-09
expect_contains 'manifest 未改动'
[[ "$before" == "$(cat "$platform/codex/config/change-template-sync.json")" ]] ||
  fail 'digest 未变化时 refresh 仍然改写了 manifest'

# 4. 清单按声明枚举 holder：声明不持有副本的仓库不出现，没有 checkout 的仓库
#    报 unverified 而不是被当成已同步。
run_case 3 bash "$tool"
expect_contains 'holders: 3（另有 1 个仓库声明不持有副本）'
expect_absent 'source-repo'
expect_row holder-current current
expect_row holder-stale stale 'spec[.]md'
expect_row holder-absent unverified
expect_contains 'result: current=1 stale=1 missing=0 unverified=1'
expect_contains 'unverified 不等于已同步'

# 5. 副本全部同步后退出码转绿；unverified 不阻止绿，但仍然如实列出。
sync_copies holder-stale
run_case 0 bash "$tool"
expect_contains 'result: current=2 stale=0 missing=0 unverified=1'
expect_row holder-absent unverified

# 6. 改模板之后：每个 holder 按定义全部过期，本机读不到的那个也在清单里。
printf 'v2\n' >>"$platform/templates/docs/changes/_template/summary.md"
run_case 3 bash "$tool" --refresh-digest --today 2026-02-04
expect_row holder-current stale 'summary[.]md'
expect_row holder-stale stale 'summary[.]md'
expect_row holder-absent unverified
sync_copies holder-current
sync_copies holder-stale

# 7. missing 与 stale 分开：目录整个不在，不能读成「内容不一致」。
rm -rf "$downstream/holder-current/docs/changes/_template"
run_case 3 bash "$tool"
expect_row holder-current missing
expect_contains 'result: current=1 stale=0 missing=1 unverified=1'
sync_copies_dir="$downstream/holder-current/docs/changes/_template"
mkdir -p "$sync_copies_dir"
sync_copies holder-current

# 8. porcelain 是制表符流，且不掺入散文行。
run_case 0 bash "$tool" --porcelain
expect_contains "$(printf 'holder-stale\tcurrent\t')"
expect_absent 'result:'
expect_absent 'holders:'

# 9. 非阻塞是合同面：声明被改掉时工具停机，而不是安静继续跑。
python3 - "$platform/codex/config/change-template-sync.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["downstream_required_check"] = "required"
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
PY
run_case 1 bash "$tool"
expect_contains 'downstream_required_check 必须是 forbidden'
run_case 1 bash "$tool" --verify-digest
expect_contains 'downstream_required_check 必须是 forbidden'
python3 - "$platform/codex/config/change-template-sync.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
manifest = json.loads(path.read_text(encoding="utf-8"))
manifest["downstream_required_check"] = "forbidden"
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
PY

# 10. 合同源缺失一份模板必须硬错，而不是把 digest 算成「少一份也一样」。
mv "$platform/templates/docs/changes/_template/plan.md" "$TMP/plan.md.bak"
run_case 1 bash "$tool" --verify-digest
expect_contains '合同源模板缺失'
mv "$TMP/plan.md.bak" "$platform/templates/docs/changes/_template/plan.md"

# 11. 用法错误。
run_case 64 bash "$tool" --verify-digest --refresh-digest
run_case 64 bash "$tool" --verify-digest --porcelain
run_case 64 bash "$tool" --today
run_case 64 bash "$tool" --today 2026-13-99
run_case 64 bash "$tool" --unknown-flag

printf 'PASS: change-template-sync (%s cases)\n' "$case_count"
