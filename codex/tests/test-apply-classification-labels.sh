#!/usr/bin/env bash
set -euo pipefail

# apply-classification-labels.sh decides which Issues have a projectable
# classification and what its two label values are, and never touches a real
# Issue while deciding. Every case here runs against a fixture repository and a
# mock broker.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

# The tool is exercised from a flat directory holding a mock broker, the same
# same-directory-first convention the other platform tools use (#111). Nothing
# here is a test-only hook in the tool.
BIN="$TMP/bin"
mkdir -p "$BIN"
cp "$ROOT/codex/tools/apply-classification-labels.sh" "$BIN/"
cat >"$BIN/host-access-broker.sh" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/broker.log"
number=""
operation=""
previous=""
for argument in "$@"; do
  case "$previous" in
    --number) number="$argument" ;;
    --operation) operation="$argument" ;;
  esac
  previous="$argument"
done
# A broker install whose operation table predates this operation refuses it
# exactly like this: typed JSON on stderr, exit 20, and a code an ACL problem
# would also use.
if [ -f "$MOCK_ROOT/stale-$operation" ]; then
  printf '%s\n' \
    '{"code": "REQUEST_DENIED", "message": "requested operation is not allowlisted", "status": "BLOCKED_EXTERNAL"}' >&2
  exit 20
fi
if [ "$operation" = gitea.issue.read ]; then
  state=open
  if [ -f "$MOCK_ROOT/state-$number" ]; then state="$(cat "$MOCK_ROOT/state-$number")"; fi
  printf '{"number":%s,"state":"%s"}\n' "$number" "$state"
  exit 0
fi
if [ "$operation" = gitea.issue.labels.read ]; then
  if [ -f "$MOCK_ROOT/labels-$number" ]; then
    cat "$MOCK_ROOT/labels-$number"
  else
    printf '[]\n'
  fi
  exit 0
fi
printf '{"issue":%s,"before":["pr-open"],"after":["complexity/complex","pr-open","type/platform"],"result":"updated","status":"PASS"}\n' \
  "$number"
MOCK
chmod +x "$BIN/host-access-broker.sh"
export MOCK_ROOT="$TMP"
: >"$TMP/broker.log"

# Fixture repository. 501 is a complete open classification, 502 is the same but
# closed, 504 is the needs-human-decision shape (no effective_complexity), 505
# has no change_type, and 503 has no documents at all.
REPO="$TMP/repo"
summary() {
  local issue="$1" slug="$2" change_type_line="$3" complexity_line="$4"
  mkdir -p "$REPO/docs/changes/$issue-$slug"
  cat >"$REPO/docs/changes/$issue-$slug/summary-$slug-260823.md" <<EOF
---
issue: $issue
${change_type_line}
requested_complexity: auto
assessed_complexity: complex
${complexity_line}
contract_effect: add
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-$slug-260823.md
status: approved
branch: change/$issue-$slug
created: 2026-08-23
updated: 2026-08-23
---

# $issue

change_type: never-read-from-the-body
effective_complexity: never-read-from-the-body
EOF
}
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.invalid
git -C "$REPO" config user.name test
summary 501 open-change 'change_type: platform' 'effective_complexity: complex'
summary 502 closed-change 'change_type: bugfix' 'effective_complexity: small'
summary 504 unclear-change 'change_type: platform' ''
summary 505 typeless-change '' 'effective_complexity: small'
printf 'closed\n' >"$TMP/state-502"

# Read-back fixtures (#167). 506 is already projected, 507 carries no
# classification labels at all, 508 carries a complexity the summary does not
# declare, and 509 is the one that matters: closed with the window shut.
summary 506 projected-change 'change_type: platform' 'effective_complexity: complex'
summary 507 unprojected-change 'change_type: platform' 'effective_complexity: complex'
summary 508 drifted-change 'change_type: platform' 'effective_complexity: complex'
summary 509 missed-change 'change_type: platform' 'effective_complexity: complex'
printf '%s\n' \
  '[{"name":"type/platform"},{"name":"complexity/complex"},{"name":"pr-open"}]' \
  >"$TMP/labels-506"
printf '%s\n' \
  '[{"name":"type/platform"},{"name":"complexity/small"}]' >"$TMP/labels-508"
printf 'closed\n' >"$TMP/state-509"

git -C "$REPO" add -A
git -C "$REPO" commit -qm 'fixture documents'

run() {
  PYTHONPATH="$ROOT/codex/runtime" bash "$BIN/apply-classification-labels.sh" \
    --repo "$REPO" "$@"
}

writes() {
  grep -c -- '--operation gitea.issue.labels.classify' "$TMP/broker.log" || true
}

# AC-6: the default is a plan, not a write. No --apply means the write operation
# is never reached, even though state reads are.
plan_output="$(run 501 502 503 504 505)"
[ "$(writes)" = 0 ]

# The plan shows the values it would project, so they can be checked before any
# write happens.
jq -e 'select(.issue == 501)
  | .action == "set-classification" and .applied == false
    and .change_type == "platform" and .complexity == "complex"' \
  <<<"$plan_output" >/dev/null

# AC-7, four distinguishable skip reasons.
#
# A closed Issue is history: the judgement is already in the merged summary, and
# list-issues only asks for open Issues, so a label written here serves nothing.
jq -e 'select(.issue == 502) | .action == "skip" and .reason == "issue-closed"' \
  <<<"$plan_output" >/dev/null

jq -e 'select(.issue == 503) | .action == "skip" and .reason == "documents-unresolved"' \
  <<<"$plan_output" >/dev/null

# An absent effective_complexity is the needs-human-decision case. Skipped with
# its own reason rather than defaulted to either complexity.
jq -e 'select(.issue == 504)
  | .action == "skip" and .reason == "classification-incomplete"
    and .change_type == "platform" and (has("complexity") | not)' \
  <<<"$plan_output" >/dev/null

jq -e 'select(.issue == 505) | .action == "skip" and .reason == "classification-missing"' \
  <<<"$plan_output" >/dev/null

# --apply writes, and only for the Issue the plan selected.
: >"$TMP/broker.log"
apply_output="$(run --apply 501 502 503 504 505)"
[ "$(writes)" = 1 ]
grep -Fq -- '--number 501 --change-type platform --complexity complex' "$TMP/broker.log"
if grep -- '--operation gitea.issue.labels.classify' "$TMP/broker.log" | grep -Fq -- '--number 502'; then
  echo 'a closed Issue must never be written' >&2
  exit 1
fi
jq -e 'select(.issue == 501) | .applied == true and .result == "updated"' \
  <<<"$apply_output" >/dev/null

# AC-2 of the Issue: the caller cannot hand the tool a label. The values reach
# the broker as the bare front matter values, and no part of the judgement —
# the checkout, the documents, the field names — crosses the argument surface.
if grep -Eq 'required_docs|effective_complexity|--repo|docs/changes|--label' "$TMP/broker.log"; then
  echo 'judgement leaked into the broker argument surface' >&2
  exit 1
fi
if grep -Fq -- '--change-type type/platform' "$TMP/broker.log"; then
  echo 'the tool must pass bare front matter values, not label names' >&2
  exit 1
fi

# The values come from the front matter block alone. Both fixtures repeat the
# keys in the body with a different value; picking those up would be silent.
if grep -Fq 'never-read-from-the-body' "$TMP/broker.log"; then
  echo 'front matter parsing escaped the closing fence' >&2
  exit 1
fi

# Rerunning is safe: same decision, same single write, and the broker is what
# turns an already-correct Issue into a no-op.
: >"$TMP/broker.log"
repeat_output="$(run --apply 501)"
[ "$(writes)" = 1 ]
[ "$repeat_output" = "$(jq -ce 'select(.issue == 501)' <<<"$apply_output")" ]

# A merge range is parsed the same way the other tools parse one: each Closes #N
# on its own line, with the change/N-slug branch name as fallback.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 600

Closes #501'
git -C "$REPO" commit -q --allow-empty -m 'Merge branch change/502-closed-change into main'
: >"$TMP/broker.log"
range_output="$(run --range 'HEAD~2..HEAD')"
jq -e 'select(.issue == 501) | .action == "set-classification"' <<<"$range_output" >/dev/null
jq -e 'select(.issue == 502) | .reason == "issue-closed"' <<<"$range_output" >/dev/null
[ "$(writes)" = 0 ]

# Refusing to guess: no Issue selector at all is an error, not an empty
# successful run that reads as "nothing to do".
rc=0
empty_output="$(run 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'no Issue selector' <<<"$empty_output"

# --- #167: the read-back and the stale-install translation ----------------
#
# The plan mode cannot answer "is this Issue's classification visible right
# now": for 506 (projected) and 507 (never projected) it emits the same line.
: >"$TMP/broker.log"
[ "$(run 506)" = "$(run 507 | sed 's/507/506/g')" ]

# AC-1: four distinguishable read-back outcomes.
: >"$TMP/broker.log"
rc=0
projected_output="$(run --verify 506)" || rc=$?
[ "$rc" -eq 0 ]
jq -e 'select(.issue == 506)
  | .action == "verify" and .result == "projected" and .applied == false
    and (has("reason") | not) and (has("remedy") | not)' \
  <<<"$projected_output" >/dev/null

rc=0
missing_output="$(run --verify 507)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 507)
  | .action == "verify" and .reason == "projection-missing"
    and .remedy == "codex/tools/apply-classification-labels.sh --apply 507"' \
  <<<"$missing_output" >/dev/null

# A dimension carrying a value the summary does not declare is its own outcome:
# reporting it as "missing" would send the reader looking for an absent label.
rc=0
mismatch_output="$(run --verify 508)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 508)
  | .action == "verify" and .reason == "projection-mismatch"
    and (.detail | contains("complexity/small"))
    and (.detail | contains("complexity/complex"))
    and (has("remedy"))' \
  <<<"$mismatch_output" >/dev/null

# The Issue this change exists for. Closed and never projected: reported loudly,
# and with no remedy, because #160 offers none and this change does not add one.
rc=0
closed_output="$(run --verify 509)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 509)
  | .action == "verify" and .reason == "projection-window-closed"
    and (has("remedy") | not)
    and .change_type == "platform" and .complexity == "complex"' \
  <<<"$closed_output" >/dev/null

# One non-projected Issue in a batch fails the whole run, so a gate cannot pass
# by reading only the last line.
rc=0
batch_output="$(run --verify 506 507)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 506) | .result == "projected"' <<<"$batch_output" >/dev/null

# AC-1a: verify is read-only. It never reaches the write operation, for any
# outcome -- including the closed Issue, which --apply also refuses.
[ "$(writes)" = 0 ]
grep -Fq -- '--operation gitea.issue.labels.read' "$TMP/broker.log"

# Verify and apply are separate modes; running both would report on a state the
# same run had just created.
rc=0
both_output="$(run --verify --apply 506 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'separate modes' <<<"$both_output"

# "I cannot tell" is not "yes": in verify mode an unresolvable Issue fails,
# where the plan mode reads the same condition as nothing to project.
rc=0
unresolved_verify="$(run --verify 503)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 503)
  | .action == "verify" and .reason == "documents-unresolved"' \
  <<<"$unresolved_verify" >/dev/null
rc=0
run 503 >/dev/null || rc=$?
[ "$rc" -eq 0 ]

# AC-2: a broker whose operation table predates the operation is named as a
# stale install, not left as a bare REQUEST_DENIED that reads like an ACL
# problem. This is the condition that cost #163 its window.
: >"$TMP/broker.log"
touch "$TMP/stale-gitea.issue.labels.classify"
rc=0
stale_output="$(run --apply 501)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 501)
  | .action == "set-classification" and .applied == false
    and .reason == "broker-operation-missing"
    and (.detail | contains("install-host-access-broker.sh"))
    and (.detail | contains("not a permission problem"))' \
  <<<"$stale_output" >/dev/null
rm -f "$TMP/stale-gitea.issue.labels.classify"

# The same translation covers every operation the tool calls, including the
# read-back's own.
touch "$TMP/stale-gitea.issue.labels.read"
rc=0
stale_verify="$(run --verify 506)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 506) | .reason == "broker-operation-missing"' \
  <<<"$stale_verify" >/dev/null
rm -f "$TMP/stale-gitea.issue.labels.read"

# A broker that cannot answer is a failure, not a silent skip: exit status
# carries it so an operator cannot read the run as complete.
: >"$TMP/broker.log"
printf '#!/usr/bin/env bash\nexit 20\n' >"$BIN/host-access-broker.sh"
chmod +x "$BIN/host-access-broker.sh"
rc=0
unreadable_output="$(run 501)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 501) | .action == "skip" and .reason == "state-unreadable"' \
  <<<"$unreadable_output" >/dev/null

echo 'apply-classification tests passed'
