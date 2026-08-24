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
# The shared merge-range library travels with the tool, exercising the
# same-directory-first branch of its lookup (#175). The project target library
# travels the same way (#184).
cp "$ROOT/codex/agent/change-merge-range.sh" "$BIN/"
cp "$ROOT/codex/agent/aisoft-project-target.sh" "$BIN/"
cat >"$BIN/host-access-broker.sh" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/broker.log"
number=""
operation=""
project=""
previous=""
for argument in "$@"; do
  case "$previous" in
    --number) number="$argument" ;;
    --operation) operation="$argument" ;;
    --project) project="$argument" ;;
  esac
  previous="$argument"
done
# Keyed by project as well as number, because #184 is exactly the case where two
# repositories hold a different Issue under the same number. A mock that ignored
# --project could not tell a right answer from a wrong one.
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
  if [ -f "$MOCK_ROOT/state-$project-$number" ]; then
    state="$(cat "$MOCK_ROOT/state-$project-$number")"
  fi
  printf '{"number":%s,"state":"%s"}\n' "$number" "$state"
  exit 0
fi
if [ "$operation" = gitea.issue.labels.read ]; then
  if [ -f "$MOCK_ROOT/labels-$project-$number" ]; then
    cat "$MOCK_ROOT/labels-$project-$number"
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
printf 'closed\n' >"$TMP/state-fixture-project-502"

# Read-back fixtures (#167). 506 is already projected, 507 carries no
# classification labels at all, 508 carries a complexity the summary does not
# declare, and 509 is the one that matters: closed with the window shut.
summary 506 projected-change 'change_type: platform' 'effective_complexity: complex'
summary 507 unprojected-change 'change_type: platform' 'effective_complexity: complex'
summary 508 drifted-change 'change_type: platform' 'effective_complexity: complex'
summary 509 missed-change 'change_type: platform' 'effective_complexity: complex'
printf '%s\n' \
  '[{"name":"type/platform"},{"name":"complexity/complex"},{"name":"pr-open"}]' \
  >"$TMP/labels-fixture-project-506"
printf '%s\n' \
  '[{"name":"type/platform"},{"name":"complexity/small"}]' >"$TMP/labels-fixture-project-508"
printf 'closed\n' >"$TMP/state-fixture-project-509"

# #184's own fixture. 601 is the false-pass shape, and it is the reason this
# file has two manifests and a Git remote at all: a checkout whose summary
# declares platform/complex, whose own project has no classification labels, and
# whose *other* project happens to carry exactly type/platform +
# complexity/complex under the same number. That coincidence is not contrived --
# in the real platform repository it is the most common pair there is, which is
# why the pre-#184 default read back a clean "projected" on Issues that had
# never been projected at all.
summary 601 falsepass-change 'change_type: platform' 'effective_complexity: complex'
printf '%s\n' '[{"name":"type/platform"},{"name":"complexity/complex"}]' \
  >"$TMP/labels-aisoft-platform-601"

git -C "$REPO" add -A
git -C "$REPO" commit -qm 'fixture documents'

# A second checkout of the same documents with no Git remote at all. It is what
# a clone without a Gitea remote looks like -- rsdesign-new is the real one --
# and it is the only way to run the counterfactual below, where the tool is told
# the wrong project and has no evidence with which to refuse.
REPO_NOREMOTE="$TMP/repo-no-remote"
cp -R "$REPO" "$REPO_NOREMOTE"

# Fixture manifests (#184). The tool reads exactly three things out of them --
# base_url and owner to build the expected remote URL, and the project_id ->
# repository mapping -- so the fixtures carry only those. FixtureRepository is
# deliberately not named like its project id, so every derivation below travels
# the mapping rather than coinciding with it.
FIXTURE_BASE_URL='http://gitea-fixture.invalid:3000'
FIXTURE_OWNER=fixtureowner
ACCESS_MANIFEST="$TMP/host-access-broker.json"
cat >"$ACCESS_MANIFEST" <<'JSON'
{
  "projects": [
    {"project_id": "fixture-project", "repository": "FixtureRepository"},
    {"project_id": "aisoft-platform", "repository": "aisoft-platform"}
  ]
}
JSON
GOVERNANCE_MANIFEST="$TMP/gitea-governance.json"
cat >"$GOVERNANCE_MANIFEST" <<JSON
{
  "base_url": "$FIXTURE_BASE_URL",
  "owner": "$FIXTURE_OWNER"
}
JSON

# The checkout states which repository it belongs to. Everything below relies on
# this and passes no --project at all, which is exactly the invocation #184 was
# reported against.
git -C "$REPO" remote add origin \
  "$FIXTURE_BASE_URL/$FIXTURE_OWNER/FixtureRepository.git"

run_repo() {
  local repo="$1"
  shift
  PYTHONPATH="$ROOT/codex/runtime" \
    AISOFT_ACCESS_MANIFEST="$ACCESS_MANIFEST" \
    AISOFT_GOVERNANCE_MANIFEST="$GOVERNANCE_MANIFEST" \
    bash "$BIN/apply-classification-labels.sh" --repo "$repo" "$@"
}

run() {
  run_repo "$REPO" "$@"
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

# --- Issue #175: a range says what it covered, and hands back a fixed anchor --

sha_501="$(git -C "$REPO" rev-parse HEAD~1)"
sha_502="$(git -C "$REPO" rev-parse HEAD)"

# AC-2: the selector line names the range as given and every commit it covered;
# AC-1: pinned is the Issue numbers, which no ref movement can change.
selector_line="$(jq -c 'select(.selector == "range")' <<<"$range_output")"
jq -e '.range == "HEAD~2..HEAD" and (.commits | length) == 2 and .pinned == "502 501"' \
  <<<"$selector_line" >/dev/null
jq -e --arg sha "$sha_501" '.commits[] | select(.commit == $sha) | .issues == [501]' \
  <<<"$selector_line" >/dev/null

# Every per-Issue line stands alone, in the skip path as much as the write path.
jq -e --arg sha "$sha_501" 'select(.issue == 501) | .commit == $sha' <<<"$range_output" >/dev/null
jq -e --arg sha "$sha_502" 'select(.issue == 502) | .commit == $sha' <<<"$range_output" >/dev/null

# A bare Issue number reports no commit and emits no selector line.
bare_output="$(run 501)"
jq -e 'select(.issue == 501) | has("commit") | not' <<<"$bare_output" >/dev/null
if jq -e 'select(.selector == "range")' <<<"$bare_output" >/dev/null 2>&1; then
  echo 'a run without --range must not emit a selector line' >&2
  exit 1
fi

# --verify carries the same exposure, and it is the worse one. The gate exists
# because the classification window shuts at merge and never reopens (#167); a
# verify aimed by a slid range reads back somebody else's Issue and exits 0.
# A false green here is worse than no gate at all.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 601

Closes #507'
sha_507="$(git -C "$REPO" rev-parse HEAD)"
rc=0
verify_before="$(run --verify --range 'HEAD~1..HEAD')" || rc=$?
[ "$rc" -ne 0 ]
jq -e --arg sha "$sha_507" \
  'select(.issue == 507) | .reason == "projection-missing" and .commit == $sha' \
  <<<"$verify_before" >/dev/null
[ "$(jq -r 'select(.selector == "range") | .pinned' <<<"$verify_before")" = 507 ]

# Another session merges. 506 is already projected, so the identical --verify
# now passes -- for an Issue the operator was never finishing.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 602

Closes #506'
sha_506="$(git -C "$REPO" rev-parse HEAD)"
rc=0
verify_after="$(run --verify --range 'HEAD~1..HEAD')" || rc=$?
[ "$rc" -eq 0 ]
jq -e 'select(.issue == 506) | .result == "projected"' <<<"$verify_after" >/dev/null
if jq -e 'select(.issue == 507)' <<<"$verify_after" >/dev/null 2>&1; then
  echo 'the fixture no longer demonstrates the slide' >&2
  exit 1
fi

# What #175 adds is that the false green is no longer silent: the line says
# which commit it came from, and it is not the operator's merge.
jq -e --arg sha "$sha_506" 'select(.issue == 506) | .commit == $sha' <<<"$verify_after" >/dev/null
[ "$sha_506" != "$sha_507" ]

# AC-1: verifying by the pinned Issue number instead reaches the Issue the
# operator is actually finishing, whatever main has done since.
rc=0
verify_pinned="$(run --verify 507)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 507) | .reason == "projection-missing"' <<<"$verify_pinned" >/dev/null

# AC-3: the window posture is untouched. A closed, never-projected Issue still
# reports the window shut and still offers no remedy, whether it arrived by
# number or by range.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 603

Closes #509'
rc=0
verify_closed="$(run --verify --range 'HEAD~1..HEAD')" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 509) | .reason == "projection-window-closed" and (has("remedy") | not)' \
  <<<"$verify_closed" >/dev/null

# AC-3: nothing new crosses the broker argument surface. The commit attribution
# is the tool's report to the operator, not an input to any read or write.
if grep -Eq -- 'commit|--range|[0-9a-f]{40}' "$TMP/broker.log"; then
  echo 'range resolution leaked into the broker argument surface' >&2
  exit 1
fi

# A range that covers nothing is its own failure, not "no Issue selector given",
# and the evidence is printed before the refusal rather than withheld by it.
rc=0
empty_range="$(run --range 'HEAD..HEAD' 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'covers no commits' <<<"$empty_range"
grep -Fq '"selector":"range"' <<<"$empty_range"

# Commits that name no Issue are a different failure again.
git -C "$REPO" commit -q --allow-empty -m 'docs: no Issue reference here'
rc=0
plain_range="$(run --range 'HEAD~1..HEAD' 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'none of which names an Issue' <<<"$plain_range"

# A range git cannot resolve at all fails loudly rather than selecting nothing.
rc=0
bad_range="$(run --range 'no-such-ref..HEAD' 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'cannot resolve --range' <<<"$bad_range"

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

# --- #184: which repository this run is allowed to speak about ---------------
#
# Every assertion above already travels the derivation: none of them passes
# --project, and FixtureRepository is nothing like fixture-project, so a tool
# that still defaulted the project id would have been asking the mock about
# aisoft-platform this whole time.

# AC-5: every line names the project and the repository it is about, in all
# three modes. Before #184 nothing in the output distinguished a conclusion
# about this checkout's repository from a conclusion about a different one, so
# the only way to notice was to already suspect it.
: >"$TMP/broker.log"
for mode_args in "501" "--apply 501" "--verify 506"; do
  # shellcheck disable=SC2086
  jq -e '.project == "fixture-project" and .repository == "FixtureRepository"' \
    <<<"$(run $mode_args)" >/dev/null
done

# AC-1: the broker is only ever asked about the project the checkout belongs to.
grep -Fq -- '--project fixture-project' "$TMP/broker.log"
if grep -Fq -- '--project aisoft-platform' "$TMP/broker.log"; then
  echo 'the tool asked the broker about a repository the checkout does not belong to' >&2
  exit 1
fi

# AC-2, the Issue this change exists for. 601's own project carries no
# classification at all, so the read-back must fail and say what is missing.
: >"$TMP/broker.log"
rc=0
falsepass_output="$(run --verify 601)" || rc=$?
[ "$rc" -ne 0 ]
jq -e 'select(.issue == 601)
  | .reason == "projection-missing" and .project == "fixture-project"
    and .repository == "FixtureRepository" and (has("result") | not)' \
  <<<"$falsepass_output" >/dev/null
if grep -Fq -- '--project aisoft-platform' "$TMP/broker.log"; then
  echo 'the read-back gate reached another repository' >&2
  exit 1
fi

# ...and the counterfactual, executed rather than argued. Told the wrong project
# by an operator, on a checkout carrying no evidence to refuse with, the very
# same Issue reads back as a clean pass with exit 0. That is what the removed
# default produced on every project except aisoft-platform, and it is why a gate
# whose window shuts permanently at merge could be walked straight past.
#
# It is also AC-6: an explicit --project remains authoritative when the checkout
# cannot answer, which is the only reason a no-remote clone is still usable.
rc=0
counterfactual="$(run_repo "$REPO_NOREMOTE" --project aisoft-platform --verify 601)" || rc=$?
[ "$rc" -eq 0 ]
jq -e 'select(.issue == 601)
  | .result == "projected" and .project == "aisoft-platform"
    and .repository == "aisoft-platform"' <<<"$counterfactual" >/dev/null

# AC-3: a --project that contradicts the checkout is a full stop, in every mode.
# Not a warning and not a preference -- either the operator named the wrong
# project or pointed at the wrong checkout, and both readings end in a
# conclusion about a repository nobody meant to touch. No Issue line is printed
# and the broker is not called at all, not even to read.
for mode_args in "601" "--apply 601" "--verify 601"; do
  : >"$TMP/broker.log"
  rc=0
  # shellcheck disable=SC2086
  mismatch_output="$(run --project aisoft-platform $mode_args 2>"$TMP/mismatch.err")" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "--project contradicting the checkout must fail: $mode_args" >&2
    exit 1
  }
  [ -z "$mismatch_output" ]
  [ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]
  grep -Fq 'fixture-project' "$TMP/mismatch.err"
  grep -Fq 'aisoft-platform' "$TMP/mismatch.err"
done

# AC-4: no evidence and no --project is a refusal, not a default. The refusal
# carries the one thing that fixes it.
for mode_args in "601" "--apply 601" "--verify 601"; do
  : >"$TMP/broker.log"
  rc=0
  # shellcheck disable=SC2086
  undetermined="$(run_repo "$REPO_NOREMOTE" $mode_args 2>"$TMP/undetermined.err")" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "an undeterminable target must fail: $mode_args" >&2
    exit 1
  }
  [ -z "$undetermined" ]
  [ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]
  grep -Fq -- '--project' "$TMP/undetermined.err"
done

# A manifest this tool cannot read is an error too. Falling back to a default
# here would reintroduce the whole bug through the back door.
: >"$TMP/broker.log"
for bad_env in AISOFT_ACCESS_MANIFEST AISOFT_GOVERNANCE_MANIFEST; do
  rc=0
  bad_output="$(
    env PYTHONPATH="$ROOT/codex/runtime" \
      AISOFT_ACCESS_MANIFEST="$ACCESS_MANIFEST" \
      AISOFT_GOVERNANCE_MANIFEST="$GOVERNANCE_MANIFEST" \
      "$bad_env=$TMP/absent-manifest.json" \
      bash "$BIN/apply-classification-labels.sh" --repo "$REPO" 501 2>&1
  )" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "an unreadable manifest must fail: $bad_env" >&2
    exit 1
  }
  grep -Fq 'apply-classification:' <<<"$bad_output"
done
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

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
