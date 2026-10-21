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

run_tool "$project" 64 --help
for subcommand in change-name resolve-documents check-change-documents open-pr backfill-pr-url claim-worktree \
  scan-worktrees classify complete project-check 'bundle status' version; do
  expect_contains "  $subcommand"
done
for subcommand in change-name resolve-documents check-change-documents open-pr backfill-pr-url claim-worktree \
  scan-worktrees classify complete project-check bundle version; do
  run_tool "$project" 0 "$subcommand" --help
  expect_contains "  $subcommand"
done
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

# Success paths of the two broker-backed commands. The broker is a mock placed
# where the wrapped tools look first (the same directory), the manifests are
# the synthetic fixtures copied out of the platform tree and named through the
# tools' own override variables; the shipped bytes are not edited.
mkdir -p "$TMP/manifests"
cp "$ROOT/codex/tests/fixtures/manifests/host-access-broker.json" \
  "$ROOT/codex/tests/fixtures/manifests/gitea-governance.json" "$TMP/manifests/"
base_url="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["base_url"])' "$TMP/manifests/gitea-governance.json")"
owner="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["owner"])' "$TMP/manifests/gitea-governance.json")"
flow="$TMP/flow"
make_project "$flow"
git -C "$flow" remote add origin "$base_url/$owner/AlphaApp.git"
git -C "$flow" checkout -q -b change/7-demo-change
printf 'demo\n' >"$flow/demo.txt"
git -C "$flow" -c user.name=t -c user.email=t@example.invalid add demo.txt
git -C "$flow" -c user.name=t -c user.email=t@example.invalid commit -q -m 'demo change'
git -C "$flow" checkout -q main
git -C "$flow" -c user.name=t -c user.email=t@example.invalid merge -q --no-ff change/7-demo-change \
  -m "Merge pull request 'demo' (#9) from change/7-demo-change into main"
cat >"$flow/.aisoft/lib/codex/tools/host-access-broker.sh" <<'MOCK'
#!/usr/bin/env bash
case " $* " in
  *" gitea.issue.read "*) printf '{"number":7,"state":"open"}\n' ;;
  *" gitea.issue.labels.read "*) printf '[{"name":"type/docs"},{"name":"complexity/small"}]\n' ;;
  *) echo "unexpected broker call: $*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$flow/.aisoft/lib/codex/tools/host-access-broker.sh"
run_flow() {
  local expected="$1" status=0
  shift
  (cd -- "$flow" && env -i HOME="$TMP/home" PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin" \
    AISOFT_ACCESS_MANIFEST="$TMP/manifests/host-access-broker.json" \
    AISOFT_GOVERNANCE_MANIFEST="$TMP/manifests/gitea-governance.json" \
    ${sandbox[@]+"${sandbox[@]}"} .aisoft/bin/aisoft "$@") >"$TMP/out" 2>&1 || status=$?
  [[ "$status" == "$expected" ]] || {
    cat "$TMP/out" >&2
    fail "expected status $expected, got $status for: aisoft $*"
  }
}
run_flow 0 classify --verify 7
expect_contains '"result":"projected"'
run_flow 0 complete --project alphaapp --range HEAD~1..HEAD
expect_contains '"pinned":"7"'
expect_contains '"action":"set-completed"'
# The architecture validator travels with the tool too.
cp "$ROOT/architecture/reference/sqlite/architecture.json" "$ROOT/architecture/reference/sqlite/architecture.lock.json" \
  "$flow/.aisoft/"
git -C "$flow" -c user.name=t -c user.email=t@example.invalid add .aisoft/architecture.json .aisoft/architecture.lock.json
git -C "$flow" -c user.name=t -c user.email=t@example.invalid commit -q -m architecture
run_flow 1 project-check --today 2026-09-12
expect_contains 'PASS: architecture-lock'
expect_contains 'PASS: tool-provenance'
# claim-worktree speaks about --repo, not about the shell's directory.
git -C "$flow" worktree add -q -b change/8-other-change "$TMP/wt2" main
run_tool "$project" 0 --repo "$TMP/wt2" claim-worktree --branch change/8-other-change --session test-session
expect_contains "\"worktree\": \"$(cd -- "$TMP/wt2" && pwd -P)\""
# An explicit --worktree=DIR is the caller's choice and is not overridden.
git -C "$flow" worktree add -q -b change/9-third-change "$TMP/wt3" main
run_tool "$project" 0 claim-worktree --branch change/9-third-change --session test-session --worktree="$TMP/wt3"
expect_contains "\"worktree\": \"$(cd -- "$TMP/wt3" && pwd -P)\""

# #408: open-pr pushes, opens the PR, backfills the summary and pushes again,
# all through the broker. The mock logs every call; a flag file makes
# pull.create fail. The mock is excluded from the worktree status so the
# clean-worktree precondition still holds.
pr_wt="$TMP/wt-pr"
git -C "$flow" worktree add -q "$pr_wt" change/7-demo-change
printf '.aisoft/lib/codex/tools/host-access-broker.sh\n' >>"$(git -C "$pr_wt" rev-parse --git-common-dir)/info/exclude"
cat >"$pr_wt/.aisoft/lib/codex/tools/host-access-broker.sh" <<MOCK
#!/usr/bin/env bash
op="" prev=""
for arg in "\$@"; do [[ "\$prev" == --operation ]] && op="\$arg"; prev="\$arg"; done
printf '%s|%s\n' "\$(pwd -P)" "\$op" >>"$TMP/broker.log"
case " \$* " in
  *" git.push.change "*)
    # Like the real broker: a dirty worktree is never pushed.
    [[ -z "\$(git status --porcelain)" ]] || { echo '{"code":"WORKTREE_DIRTY"}' >&2; exit 1; }
    printf '{"status":"PASS"}\n' ;;
  *" gitea.pull.create "*)
    [[ -e "$TMP/fail-create" ]] && { echo '{"error":"TRANSPORT_ERROR"}' >&2; exit 1; }
    printf '{"number":12,"state":"open"}\n' ;;
  *) echo "unexpected broker call: \$*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$pr_wt/.aisoft/lib/codex/tools/host-access-broker.sh"
run_pr() {
  local expected="$1" status=0
  shift
  (cd -- "$pr_wt" && env -i HOME="$TMP/home" PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin" \
    GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid \
    AISOFT_ACCESS_MANIFEST="$TMP/manifests/host-access-broker.json" \
    AISOFT_GOVERNANCE_MANIFEST="$TMP/manifests/gitea-governance.json" \
    ${sandbox[@]+"${sandbox[@]}"} .aisoft/bin/aisoft "$@") >"$TMP/out" 2>&1 || status=$?
  [[ "$status" == "$expected" ]] || {
    cat "$TMP/out" >&2
    fail "expected status $expected, got $status for: aisoft $*"
  }
}
pr_summary="docs/changes/7-demo-change/summary-demo-change-261021.md"
printf 'Demo.\n\nCloses #7\n\nSummary: %s\n' "$pr_summary" >"$TMP/body.md"
printf 'Demo without the closing line.\n\nSummary: %s\n' "$pr_summary" >"$TMP/bad-body.md"
start="$(git -C "$pr_wt" rev-parse HEAD)"
: >"$TMP/broker.log"
run_pr 2 open-pr 7 --title demo --body-file "$TMP/bad-body.md"
expect_contains "exactly one line 'Closes #7'"
[[ ! -s "$TMP/broker.log" ]] || fail 'open-pr called the broker with a body that breaks the contract'
# Bodies the broker would refuse are refused before any broker call: a CR, a
# summary link glued to other path characters, a second summary link.
printf 'Demo.\r\n\r\nCloses #7\r\n\r\nSummary: %s\r\n' "$pr_summary" >"$TMP/crlf-body.md"
printf 'Demo.\n\nCloses #7\n\nSummary: x%s\n' "$pr_summary" >"$TMP/glued-body.md"
printf 'Demo.\n\nCloses #7\n\n%s\n%s\n' "$pr_summary" "docs/changes/7-demo-change/summary-demo-change-261022.md" >"$TMP/two-body.md"
for bad in crlf-body glued-body two-body; do
  run_pr 2 open-pr 7 --title demo --body-file "$TMP/$bad.md"
done
[[ ! -s "$TMP/broker.log" ]] || fail 'open-pr called the broker with a body the broker would refuse'
touch "$TMP/fail-create"
run_pr 1 open-pr 7 --title demo --body-file "$TMP/body.md"
expect_contains 'pull.create refused'
[[ "$(git -C "$pr_wt" rev-parse HEAD)" == "$start" ]] || fail 'a failed pull.create left a commit behind'
grep -Fq 'status: approved' "$pr_wt/$pr_summary" || fail 'a failed pull.create touched the summary'
rm -f "$TMP/fail-create"
: >"$TMP/broker.log"
# A backfill commit that fails (here a refusing pre-commit hook) leaves only
# the summary's pr_url and status changed; after the cause is fixed a rerun
# finishes the job.
hook="$(git -C "$pr_wt" rev-parse --git-common-dir)/hooks/pre-commit"
mkdir -p "$(dirname "$hook")"
printf '#!/bin/sh\nexit 1\n' >"$hook"
chmod +x "$hook"
run_pr 1 open-pr 7 --title demo --body-file "$TMP/body.md"
expect_contains 'committing the backfilled summary failed'
[[ "$(git -C "$pr_wt" rev-parse HEAD)" == "$start" ]] || fail 'a refused commit moved HEAD'
rm -f "$hook"
run_pr 0 open-pr 7 --title demo --body-file "$TMP/body.md"
expect_contains 'PR 12'
grep -Fq 'pr_url: http://gitea.invalid/o/r/pulls/12' "$pr_wt/$pr_summary" || fail 'open-pr did not backfill pr_url'
grep -Fq 'status: pr-open' "$pr_wt/$pr_summary" || fail 'open-pr did not advance status'
[[ "$(git -C "$pr_wt" rev-list --count "$start..HEAD")" == 1 ]] || fail 'open-pr must add exactly one commit'
[[ "$(git -C "$pr_wt" diff --name-only "$start" HEAD)" == "$pr_summary" ]] || fail 'the backfill commit touched more than the summary'
calls="$(cut -d'|' -f2 "$TMP/broker.log" | tr '\n' ' ')"
# First run: push and create, then the commit is refused; the rerun commits
# first and pushes once, without a second pull.create.
[[ "$calls" == "git.push.change gitea.pull.create git.push.change " ]] || fail "unexpected broker sequence: $calls"
[[ "$(cut -d'|' -f1 "$TMP/broker.log" | sort -u)" == "$(cd -- "$pr_wt" && pwd -P)" ]] || fail 'the broker must run from inside the checkout'
# A rerun is idempotent: no second commit.
head="$(git -C "$pr_wt" rev-parse HEAD)"
run_pr 0 open-pr 7 --title demo --body-file "$TMP/body.md"
[[ "$(git -C "$pr_wt" rev-parse HEAD)" == "$head" ]] || fail 'a rerun of open-pr committed again'

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

pattern = re.compile(r"PYTHONPATH=codex/runtime|codex/tools/|aisoft-loop |aisoft_loop\.cli")
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
