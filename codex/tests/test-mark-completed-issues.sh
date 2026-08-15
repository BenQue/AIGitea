#!/usr/bin/env bash
set -euo pipefail

# mark-completed-issues.sh decides which merged Issues have actually reached the
# completed terminal state, and never touches a real Issue while deciding.
# Every case here runs against a fixture repository and a mock broker.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

# The tool is exercised from a flat directory holding a mock broker, the same
# same-directory-first convention the other platform tools use (#111). Nothing
# here is a test-only hook in the tool.
BIN="$TMP/bin"
mkdir -p "$BIN"
cp "$ROOT/codex/tools/mark-completed-issues.sh" "$BIN/"
cat >"$BIN/host-access-broker.sh" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/broker.log"
number=""
previous=""
for argument in "$@"; do
  if [ "$previous" = "--number" ]; then number="$argument"; fi
  previous="$argument"
done
printf '{"issue":%s,"before":["pr-open"],"after":["completed"],"result":"updated","status":"PASS"}\n' \
  "$number"
MOCK
chmod +x "$BIN/host-access-broker.sh"
export MOCK_ROOT="$TMP"
: >"$TMP/broker.log"

# Fixture repository. 501 needs no deployment, 502 does, 503 has no documents.
REPO="$TMP/repo"
summary() {
  local issue="$1" slug="$2" extra="$3"
  mkdir -p "$REPO/docs/changes/$issue-$slug"
  cat >"$REPO/docs/changes/$issue-$slug/summary-$slug-260815.md" <<EOF
---
issue: $issue
change_type: platform
effective_complexity: complex
required_docs:
  - summary
  - spec
  - plan
$extra
documents:
  summary: summary-$slug-260815.md
  spec: spec-$slug-260815.md
  plan: plan-$slug-260815.md
status: approved
branch: change/$issue-$slug
created: 2026-08-15
updated: 2026-08-15
---

# $issue
EOF
  local role
  for role in spec plan; do
    cat >"$REPO/docs/changes/$issue-$slug/$role-$slug-260815.md" <<EOF
---
issue: $issue
created: 2026-08-15
updated: 2026-08-15
---

# $role $issue
EOF
  done
}
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.invalid
git -C "$REPO" config user.name test
summary 501 no-deploy-change ''
summary 502 deployed-change '  - verification'
git -C "$REPO" add -A
git -C "$REPO" commit -qm 'fixture documents'

run() {
  PYTHONPATH="$ROOT/codex/runtime" bash "$BIN/mark-completed-issues.sh" \
    --repo "$REPO" "$@"
}

# AC-8: the default is a plan, not a write. No --apply means no broker call at
# all — the operation surface is never even reached.
plan_output="$(run 501 502 503)"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

jq -e 'select(.issue == 501) | .action == "set-completed" and .applied == false' \
  <<<"$plan_output" >/dev/null

# AC-6: the skip decision comes from required_docs, and it says why. A change
# whose contract requires a verification document is a change that ships, so
# its terminal state is deployed and this tool must not claim it.
jq -e 'select(.issue == 502) | .action == "skip" and .reason == "requires-deployment"' \
  <<<"$plan_output" >/dev/null
grep -Fq 'verification' <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$plan_output")"

# An Issue with no mapped documents is skipped with its own reason rather than
# defaulted into either terminal state.
jq -e 'select(.issue == 503) | .action == "skip" and .reason == "documents-unresolved"' \
  <<<"$plan_output" >/dev/null

# --apply writes, and only for the Issue the plan selected.
apply_output="$(run --apply 501 502 503)"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 1 ]
grep -Fq -- '--operation gitea.issue.labels.set' "$TMP/broker.log"
grep -Fq -- '--number 501' "$TMP/broker.log"
grep -Fq -- '--lifecycle completed' "$TMP/broker.log"
if grep -Fq -- '--number 502' "$TMP/broker.log"; then
  echo 'an Issue requiring deployment must never be written' >&2
  exit 1
fi
jq -e 'select(.issue == 501) | .applied == true and .result == "updated"' \
  <<<"$apply_output" >/dev/null

# The tool decides; the broker only writes. Nothing about required_docs or the
# merge range crosses the broker argument surface.
if grep -Eq 'required_docs|verification|--repo|docs/changes' "$TMP/broker.log"; then
  echo 'judgement leaked into the broker argument surface' >&2
  exit 1
fi

# A merge range is parsed the same way the deployment hook parses one: each
# Closes #N on its own line, with the change/N-slug branch name as fallback.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 600

Closes #501'
git -C "$REPO" commit -q --allow-empty -m 'Merge branch change/502-deployed-change into main'
: >"$TMP/broker.log"
range_output="$(run --range 'HEAD~2..HEAD')"
jq -e 'select(.issue == 501) | .action == "set-completed"' <<<"$range_output" >/dev/null
jq -e 'select(.issue == 502) | .action == "skip"' <<<"$range_output" >/dev/null
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# Refusing to guess: no Issue selector at all is an error, not an empty
# successful run that reads as "nothing to do".
rc=0
empty_output="$(run 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'no Issue selector' <<<"$empty_output"

echo 'mark-completed tests passed'
