#!/usr/bin/env bash
# #402: the session tool a project receives (.aisoft/bin/aisoft + .aisoft/lib)
# is closed over everything it runs. The real release is exported into an
# empty directory, a synthetic project checkout is made from it, and every
# subcommand runs with a clean environment. On macOS the run is also wrapped
# in a sandbox profile that denies reading the platform checkout, so a hidden
# absolute path back into it fails instead of silently working. Removing one
# shipped module must turn the run red (reverse proof).
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

bash "$ROOT/codex/tools/usage-bundle.sh" --build "$TMP/export" >/dev/null

make_project() {
  local repo="$1"
  mkdir -p "$repo"
  cp -R "$TMP/export/project/." "$repo/"
  mkdir -p "$repo/docs/changes/7-demo-change"
  sed -e 's/ISSUE_NUMBER/7/g' -e 's#ISSUE_URL#http://gitea.invalid/o/r/issues/7#' \
    -e 's/CHANGE_TYPE/docs/' -e 's/ASSESSED_COMPLEXITY/small/' -e 's/EFFECTIVE_COMPLEXITY/small/' \
    -e 's/CONTRACT_EFFECT/restore/' -e 's/CLASSIFICATION_REASON/合成测试/' \
    -e 's/SHORT-SLUG-YYMMDD/demo-change-261021/' -e 's/SHORT-SLUG/demo-change/' \
    -e 's/ROUTE_PROCESS/small-direct/' -e 's/ROUTE_TIER/standard/' -e 's/ROUTE_EFFORT/medium/' \
    -e 's/ROUTE_SKILLS/verification-before-completion/' -e 's/ROUTE_METHOD/implement-only/' \
    -e 's/ROUTE_VERIFY/targeted/' -e 's/ROUTE_REVIEW/human-merge/' -e 's/CONFIDENCE/high/' \
    -e 's/^status: analyzed$/status: approved/' -e 's/YYYY-MM-DD/2026-10-21/g' \
    "$repo/docs/changes/_template/summary.md" >"$repo/docs/changes/7-demo-change/summary-demo-change-261021.md"
  git -C "$repo" init -q -b main
  git -C "$repo" -c user.name=t -c user.email=t@example.invalid add -A
  git -C "$repo" -c user.name=t -c user.email=t@example.invalid commit -q -m base
}

# The sandbox exists only on macOS; elsewhere the clean environment and the
# copied tree are the isolation, and the output says which one ran.
sandbox=()
if command -v sandbox-exec >/dev/null 2>&1; then
  cat >"$TMP/deny.sb" <<EOF
(version 1)
(allow default)
(deny file-read* (subpath "$(cd -- "$ROOT" && pwd -P)"))
EOF
  sandbox=(sandbox-exec -f "$TMP/deny.sb")
  echo 'test-aisoft-entry: platform checkout denied by sandbox-exec'
else
  echo 'test-aisoft-entry: sandbox-exec unavailable; clean environment only'
fi

# run_tool <repo> <expected status> <args...>; output in $TMP/out
run_tool() {
  local repo="$1" expected="$2" status=0
  shift 2
  (cd -- "$repo" && env -i HOME="$TMP/home" PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin" \
    ${sandbox[@]+"${sandbox[@]}"} .aisoft/bin/aisoft "$@") >"$TMP/out" 2>&1 || status=$?
  [[ "$status" == "$expected" ]] || {
    cat "$TMP/out" >&2
    fail "expected status $expected, got $status for: aisoft $*"
  }
}

expect_contains() {
  grep -Fq -- "$1" "$TMP/out" || {
    cat "$TMP/out" >&2
    fail "missing output: $1"
  }
}

mkdir -p "$TMP/home"
project="$TMP/project"
make_project "$project"

run_tool "$project" 0 version
expect_contains $'layout\tproject'
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["releases"][-1]["version"])' "$ROOT/usage/bundle.json")"
expect_contains $'bundle_version\t'"$version"
run_tool "$project" 0 change-name 7 demo-change
expect_contains 'change/7-demo-change'
run_tool "$project" 0 resolve-documents 7
expect_contains '"summary": "summary-demo-change-261021.md"'
run_tool "$project" 0 check-change-documents
expect_contains 'result: changes=1 pass=2 gap=0'
run_tool "$project" 0 bundle status
expect_contains $'tool-provenance\tPASS\t'"$version"
run_tool "$project" 0 project-check --kind docs
expect_contains 'PASS: tool-provenance'
run_tool "$project" 0 scan-worktrees
git -C "$project" worktree add -q -b change/7-demo-change "$TMP/wt" main
run_tool "$TMP/wt" 0 claim-worktree --branch change/7-demo-change --session test-session
expect_contains '"result": "created"'
run_tool "$TMP/wt" 0 backfill-pr-url 7 --pr-url http://gitea.invalid/o/r/pulls/9
expect_contains 'changed '
grep -Fq 'status: pr-open' "$TMP/wt/docs/changes/7-demo-change/summary-demo-change-261021.md" || fail 'backfill did not advance status'
# The route card is read from the summary before the projection tool runs; the
# synthetic project is not registered, so the tool itself must refuse by name.
run_tool "$project" 1 classify 7
expect_contains '路由 #7: small-direct · standard/medium · implement-only'
expect_contains 'ERROR: apply-classification:'
run_tool "$project" 1 complete --project demo --range HEAD~1..HEAD
expect_contains 'ERROR:'
if grep -Eq 'No such file|not found|unavailable' "$TMP/out"; then
  cat "$TMP/out" >&2
  fail 'a wrapped tool could not find one of its own files'
fi
[[ -z "$(git -C "$project" status --porcelain)" ]] || fail 'the tool wrote into the project checkout'

# Reverse proof: one shipped module gone is a failure, not a silent pass.
broken="$TMP/broken"
make_project "$broken"
rm "$broken/.aisoft/lib/codex/runtime/aisoft_change_name.py"
run_tool "$broken" 1 check-change-documents
run_tool "$broken" 0 bundle status
expect_contains $'tool-provenance\tGAP'

# AC-2: exported skills tell a project session to run aisoft, never the
# platform tree. Platform paths are allowed only under a heading that says
# 维护层 (steps a platform maintainer runs in the platform checkout).
platform_paths() {
  python3 - "$@" <<'PY'
import re
import sys
from pathlib import Path

pattern = re.compile(r"PYTHONPATH=codex/runtime|codex/tools/")
for root in sys.argv[1:]:
    for path in sorted(Path(root).rglob("*.md")):
        stack, fenced = [], False
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if line.startswith("```"):
                fenced = not fenced
            heading = None if fenced else re.match(r"^(#{1,6}) ", line)
            if heading:
                level = len(heading.group(1))
                stack = [entry for entry in stack if entry[0] < level] + [(level, "维护层" in line)]
            if pattern.search(line) and not any(maintenance for _, maintenance in stack):
                print(f"{path}:{number}: {line}")
PY
}
hits="$(platform_paths "$TMP/export/project/.claude/skills")"
[[ -z "$hits" ]] || {
  printf '%s\n' "$hits" >&2
  fail 'exported skills name the platform tree outside a 维护层 section'
}
probe="$TMP/probe-skills"
mkdir -p "$probe"
# shellcheck disable=SC2016 # the backticks are literal Markdown
printf '# 技能\n\n## 维护层：示例\n\n`codex/tools/x.sh`\n\n## 会话步骤\n\n`codex/tools/y.sh`\n' >"$probe/SKILL.md"
hits="$(platform_paths "$probe")"
grep -Fq 'codex/tools/y.sh' <<<"$hits" || fail 'the skill path guard missed a session step'
if grep -Fq 'codex/tools/x.sh' <<<"$hits"; then
  fail 'the skill path guard flagged a 维护层 section'
fi

echo 'test-aisoft-entry: PASS'
