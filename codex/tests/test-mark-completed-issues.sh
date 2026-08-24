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

# Fixture governance manifest. The tool reads exactly two things out of it —
# a repository entry by name, and that entry's deployment_lifecycle — so the
# fixture carries only those. It is deliberately NOT a copy of the real
# manifest: what the real one declares is pinned in
# codex/runtime/tests/test_deployment_lifecycle.py instead.
#
# The fixture's aisoft-platform entry declares application-deploy because the
# scaffolding below needs one project whose verification-declaring Issue is
# skipped, and after #192 the undeclared default is no longer that project: an
# undeclared repository now lands in the selective branch and reaches completed.
# The default therefore gets its own entry (UndeclaredRepository) and its own
# assertions rather than being borrowed by every case above.
# base_url and owner join the fixture (#184): they are what a checkout's Git
# remote is compared against when the target project is derived rather than
# defaulted.
FIXTURE_BASE_URL='http://gitea-fixture.invalid:3000'
FIXTURE_OWNER=fixtureowner
MANIFEST="$TMP/gitea-governance.json"
cat >"$MANIFEST" <<JSON
{
  "base_url": "$FIXTURE_BASE_URL",
  "owner": "$FIXTURE_OWNER",
  "repositories": [
    {"name": "aisoft-platform", "deployment_lifecycle": "application-deploy"},
    {"name": "NoDeployRepository", "deployment_lifecycle": "none"},
    {"name": "ExplicitDeployRepository", "deployment_lifecycle": "application-deploy"},
    {"name": "SelectiveRepository",
     "deployment_lifecycle": "application-deploy-selective"},
    {"name": "UndeclaredRepository"},
    {"name": "UnknownLifecycleRepository", "deployment_lifecycle": "ship-it-later"}
  ]
}
JSON

# Fixture host access manifest (#172). --project carries a project id; the
# governance manifest is keyed by repository name; the tool derives one from the
# other. Two of the three mappings deliberately have a repository name that is
# NOT the project id, so every assertion below travels the derivation. The third
# keeps the coinciding shape that hid the bug for as long as it did — four of the
# ten real projects still have it, and they must keep working.
ACCESS_MANIFEST="$TMP/host-access-broker.json"
cat >"$ACCESS_MANIFEST" <<'JSON'
{
  "projects": [
    {"project_id": "aisoft-platform", "repository": "aisoft-platform"},
    {"project_id": "no-deploy-project", "repository": "NoDeployRepository"},
    {"project_id": "explicit-deploy-project", "repository": "ExplicitDeployRepository"},
    {"project_id": "selective-project", "repository": "SelectiveRepository"},
    {"project_id": "undeclared-project", "repository": "UndeclaredRepository"},
    {"project_id": "unknown-lifecycle-project", "repository": "UnknownLifecycleRepository"},
    {"project_id": "dangling-project", "repository": "DanglingRepository"}
  ]
}
JSON

# $REPO deliberately has no Git remote, so it cannot say which project it
# belongs to and --project has to (#184). That is the shape every assertion
# below wants: it lets one fixture checkout stand in for four different
# projects. The injected --project is a floor, not a lock -- a later --project in
# "$@" wins, which is how the cases below select no-deploy-project and friends.
run() {
  PYTHONPATH="$ROOT/codex/runtime" AISOFT_GOVERNANCE_MANIFEST="$MANIFEST" \
    AISOFT_ACCESS_MANIFEST="$ACCESS_MANIFEST" \
    bash "$BIN/mark-completed-issues.sh" --repo "$REPO" \
    --project aisoft-platform "$@"
}

run_with_manifest() {
  local manifest="$1"
  shift
  PYTHONPATH="$ROOT/codex/runtime" AISOFT_GOVERNANCE_MANIFEST="$manifest" \
    AISOFT_ACCESS_MANIFEST="$ACCESS_MANIFEST" \
    bash "$BIN/mark-completed-issues.sh" --repo "$REPO" \
    --project aisoft-platform "$@"
}

run_with_access_manifest() {
  local access_manifest="$1"
  shift
  PYTHONPATH="$ROOT/codex/runtime" AISOFT_GOVERNANCE_MANIFEST="$MANIFEST" \
    AISOFT_ACCESS_MANIFEST="$access_manifest" \
    bash "$BIN/mark-completed-issues.sh" --repo "$REPO" \
    --project aisoft-platform "$@"
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
if grep -Eq 'required_docs|verification|--repo|docs/changes|deployment_lifecycle' \
  "$TMP/broker.log"; then
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

# --- Issue #175: a range says what it covered, and hands back a fixed anchor --
#
# origin/main~N is evaluated when the tool starts, not when the operator fetched
# and not when the operator approved the plan. Two windows follow, and main
# moving in either one slides the range onto somebody else's merge -- silently,
# because completed is very often the label that Issue should have anyway.

sha_501="$(git -C "$REPO" rev-parse HEAD~1)"
sha_502="$(git -C "$REPO" rev-parse HEAD)"

# AC-2: the selector line names the range as given and every commit it covered,
# so mis-aiming is visible without a second git log.
selector_line="$(jq -c 'select(.selector == "range")' <<<"$range_output")"
jq -e '.range == "HEAD~2..HEAD" and (.commits | length) == 2' <<<"$selector_line" >/dev/null
jq -e --arg sha "$sha_501" '.commits[] | select(.commit == $sha) | .issues == [501]' \
  <<<"$selector_line" >/dev/null

# AC-2: and every per-Issue line stands alone -- it names the commit it came
# from, so one line is enough to tell whether it was derived from the merge the
# operator meant.
jq -e --arg sha "$sha_501" 'select(.issue == 501) | .commit == $sha' <<<"$range_output" >/dev/null
jq -e --arg sha "$sha_502" 'select(.issue == 502) | .commit == $sha' <<<"$range_output" >/dev/null

# A bare Issue number was not derived from any commit, so it reports none, and
# no selector line is emitted at all.
bare_output="$(run 501)"
jq -e 'select(.issue == 501) | has("commit") | not' <<<"$bare_output" >/dev/null
if jq -e 'select(.selector == "range")' <<<"$bare_output" >/dev/null 2>&1; then
  echo 'a run without --range must not emit a selector line' >&2
  exit 1
fi

# The slide itself, made deterministic. C is the operator's own merge; the plan
# is read; then another session merges D; then the operator runs --apply.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 601

Closes #501'
sha_c="$(git -C "$REPO" rev-parse HEAD)"
: >"$TMP/broker.log"
plan_before="$(run --range 'HEAD~1..HEAD')"
[ "$(jq -r 'select(.selector == "range") | .pinned' <<<"$plan_before")" = 501 ]
jq -e --arg sha "$sha_c" 'select(.issue == 501) | .action == "set-completed" and .commit == $sha' \
  <<<"$plan_before" >/dev/null

git -C "$REPO" commit -q --allow-empty -m 'Merge branch change/502-deployed-change into main'
sha_d="$(git -C "$REPO" rev-parse HEAD)"

# Same argument, different target. If this ever stops holding, the fixture has
# stopped reproducing the bug and everything below it is vacuous.
plan_after="$(run --range 'HEAD~1..HEAD')"
[ "$(jq -r 'select(.selector == "range") | .pinned' <<<"$plan_after")" = 502 ]
jq -e --arg sha "$sha_d" 'select(.selector == "range") | .commits[0].commit == $sha' \
  <<<"$plan_after" >/dev/null

# AC-1: the operator reruns with the pinned number the plan handed back, not
# with the range. The Issue number cannot move, so --apply writes the Issue the
# approved plan showed -- not the one the range now points at.
: >"$TMP/broker.log"
apply_pinned="$(run --apply 501)"
jq -e 'select(.issue == 501) | .applied == true' <<<"$apply_pinned" >/dev/null
grep -Fq -- '--number 501' "$TMP/broker.log"
if grep -Fq -- '--number 502' "$TMP/broker.log"; then
  echo 'the pinned rerun must not reach the Issue the range slid onto' >&2
  exit 1
fi

# And the contrast that makes the point: rerunning --apply with the same range
# the plan was read from now selects a different Issue entirely.
: >"$TMP/broker.log"
apply_range="$(run --apply --range 'HEAD~1..HEAD')"
jq -e 'select(.issue == 502) | .action == "skip"' <<<"$apply_range" >/dev/null
if jq -e 'select(.issue == 501)' <<<"$apply_range" >/dev/null 2>&1; then
  echo 'the fixture no longer demonstrates the slide' >&2
  exit 1
fi

# AC-3: nothing new crosses the broker argument surface. The commit attribution
# is the tool's report to the operator, not an input to the write.
if grep -Eq -- 'commit|--range|[0-9a-f]{40}' "$TMP/broker.log"; then
  echo 'range resolution leaked into the broker argument surface' >&2
  exit 1
fi

# A range that covers nothing is its own failure, not "no Issue selector given".
# That message says the argument was missing; here it was present and aimed at
# an empty set, which is the mis-aim of #175 at its most extreme.
: >"$TMP/broker.log"
rc=0
empty_range="$(run --range 'HEAD..HEAD' 2>&1)" || rc=$?
[ "$rc" -ne 0 ]
grep -Fq 'covers no commits' <<<"$empty_range"
grep -Fq 'origin/main~N' <<<"$empty_range"
# The evidence is printed before the refusal, not withheld by it.
grep -Fq '"selector":"range"' <<<"$empty_range"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# Commits that name no Issue are a different failure again: the range was aimed
# at real commits, they simply close nothing.
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

# --- Issue #163: verification no longer means "deployed" on its own ----------
#
# Before #163 the single condition below decided both "does this change owe a
# verification document" and "does this change travel a deployment chain". A
# project without such a chain had neither terminal state written by anyone.

# AC-2/AC-3: same Issue #502, same required_docs, project declares no chain →
# completed becomes reachable, and the plan says on what grounds.
: >"$TMP/broker.log"
no_chain_plan="$(run --project no-deploy-project 502)"
jq -e 'select(.issue == 502) | .action == "set-completed" and .applied == false
  and .reason == "no-deployment-chain"' <<<"$no_chain_plan" >/dev/null
grep -Fq 'deployment_lifecycle none' \
  <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$no_chain_plan")"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

no_chain_apply="$(run --project no-deploy-project --apply 502)"
jq -e 'select(.issue == 502) | .applied == true and .result == "updated"
  and .reason == "no-deployment-chain"' <<<"$no_chain_apply" >/dev/null
grep -Fq -- '--lifecycle completed' "$TMP/broker.log"
grep -Fq -- '--number 502' "$TMP/broker.log"

# AC-2: the declaration is read as a value, not merely as presence. A project
# that declares application-deploy is the one branch that still waits — see the
# #192 section below for why the undeclared default no longer joins it.
explicit_plan="$(run --project explicit-deploy-project 502)"
jq -e 'select(.issue == 502) | .action == "skip" and .reason == "requires-deployment"' \
  <<<"$explicit_plan" >/dev/null

# AC-4: a change that owes no verification document is unaffected by the
# declaration — it reaches completed with no reason attached, as before.
plain_plan="$(run --project no-deploy-project 501)"
jq -e 'select(.issue == 501) | .action == "set-completed" and has("reason") == false' \
  <<<"$plain_plan" >/dev/null

# The production resolution path, with no override at all: a manifest sitting
# where a repository checkout puts it relative to the tool. $BIN is the flat
# install directory, so $BIN/../config is exactly the repository-layout branch —
# this is what a session gets when it runs the tool out of the platform
# checkout, and a typo in that path would otherwise reach nothing but production.
mkdir -p "$TMP/config"
cp "$MANIFEST" "$TMP/config/gitea-governance.json"
cp "$ACCESS_MANIFEST" "$TMP/config/host-access-broker.json"
layout_plan="$(
  env -u AISOFT_GOVERNANCE_MANIFEST -u AISOFT_ACCESS_MANIFEST \
    PYTHONPATH="$ROOT/codex/runtime" \
    bash "$BIN/mark-completed-issues.sh" --repo "$REPO" \
    --project no-deploy-project 502
)"
jq -e 'select(.issue == 502) | .reason == "no-deployment-chain"' \
  <<<"$layout_plan" >/dev/null
rm -rf "$TMP/config"

# AC-5: a manifest this tool cannot read is an error, not a silent skip.
# Silently doing nothing is the failure #163 exists to fix, so it must never be
# how an unreadable prerequisite presents itself. Absence of the key is a
# different thing entirely and stays a default, covered above.
printf '%s\n' 'not json' >"$TMP/broken-manifest.json"
for bad_case in "$TMP/absent-manifest.json" "$TMP/broken-manifest.json"; do
  rc=0
  bad_output="$(run_with_manifest "$bad_case" 501 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "an unreadable governance manifest must fail: $bad_case" >&2
    exit 1
  }
  grep -Fq 'mark-completed:' <<<"$bad_output"
done

# --- Issue #192: waiting is only correct when the wait is guaranteed to end --
#
# #163 gave the repository the question "is there a deployment chain at all".
# That is not the question a skip depends on: skipping parks the Issue until
# something writes deployed, so what has to hold is that a deployment will cover
# THIS merge. In a repository that deploys only some of its merges the two
# diverge, and every change that lands in the gap gets neither terminal state --
# the exact failure #163 exists to fix, one class of repository over.

# AC-2: an explicit selective declaration reaches completed, and says on what
# grounds. The detail has to name the gap, because "completed" on a change that
# may yet ship is only defensible if the reader can see the reasoning.
: >"$TMP/broker.log"
selective_plan="$(run --project selective-project 502)"
jq -e 'select(.issue == 502) | .action == "set-completed" and .applied == false
  and .reason == "deployment-not-guaranteed"' <<<"$selective_plan" >/dev/null
selective_detail="$(jq -r 'select(.issue == 502) | .detail' <<<"$selective_plan")"
grep -Fq 'SelectiveRepository' <<<"$selective_detail"
grep -Fq 'only some merges' <<<"$selective_detail"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

selective_apply="$(run --project selective-project --apply 502)"
jq -e 'select(.issue == 502) | .applied == true and .result == "updated"
  and .reason == "deployment-not-guaranteed"' <<<"$selective_apply" >/dev/null
grep -Fq -- '--lifecycle completed' "$TMP/broker.log"
grep -Fq -- '--number 502' "$TMP/broker.log"

# AC-2: the undeclared repository lands in that same branch. This is the default
# change itself, and it is why the real-manifest LocalWMS case above resolves.
# The two verdicts are compared rather than re-asserted, so a default that later
# drifts away from the declaration it is supposed to mean fails right here.
undeclared_plan="$(run --project undeclared-project 502)"
verdict() { jq -r 'select(.issue == 502) | .action + " " + .reason' <<<"$1"; }
[ "$(verdict "$undeclared_plan")" = "$(verdict "$selective_plan")" ]
[ "$(verdict "$undeclared_plan")" = 'set-completed deployment-not-guaranteed' ]
grep -Fq 'UndeclaredRepository' \
  <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$undeclared_plan")"

# AC-4: none of this touches a change that owes no verification document. It
# reaches completed with no reason attached under every declaration, exactly as
# before -- the first condition of the conjunction still decides on its own.
for lifecycle_project in selective-project undeclared-project explicit-deploy-project; do
  jq -e 'select(.issue == 501) | .action == "set-completed" and has("reason") == false' \
    <<<"$(run --project "$lifecycle_project" 501)" >/dev/null
done

# AC-3: a declared value this tool does not understand is an error, in every
# mode and regardless of which Issue was asked for. The check is up front, before
# any Issue is read: this tool writes a terminal label off that declaration, so a
# typo that fell into either branch would read as a decision rather than a
# mistake. #163's own posture, applied to the value instead of the file.
: >"$TMP/broker.log"
for mode_args in "502" "--apply 502" "501"; do
  rc=0
  # shellcheck disable=SC2086
  unknown_lifecycle="$(run --project unknown-lifecycle-project $mode_args 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo 'an unsupported deployment_lifecycle must fail rather than be judged' >&2
    exit 1
  }
  grep -Fq 'ship-it-later' <<<"$unknown_lifecycle"
  grep -Fq 'UnknownLifecycleRepository' <<<"$unknown_lifecycle"
done
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# --- Issue #172: --project names a project id, and only that -----------------
#
# Every assertion above already travels the derivation: no-deploy-project and
# explicit-deploy-project map to repository names that are nothing like them, so
# a tool that fed --project straight to the governance lookup would have failed
# out well before here. What follows covers the two ways the derivation itself
# can come up empty, which used to be indistinguishable from each other.

# AC-2: the verdict is decided by the repository the project id resolves to, not
# by the project id. Same Issue, same required_docs, two project ids whose
# repositories differ only in their declaration — the conclusions must diverge.
jq -e 'select(.issue == 502) | .reason == "no-deployment-chain"' <<<"$no_chain_plan" >/dev/null
grep -Fq 'NoDeployRepository' \
  <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$no_chain_plan")"
grep -Fq 'ExplicitDeployRepository' \
  <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$explicit_plan")"

# AC-3, access side: a project id the host access manifest does not describe is
# unresolvable, in both modes, and says so against the access manifest. Before
# #172 this surfaced as a governance-manifest complaint about a missing
# repository entry, which sent the reader off to edit the wrong file.
: >"$TMP/broker.log"
for mode_args in "501" "--apply 501"; do
  rc=0
  # shellcheck disable=SC2086
  unknown_output="$(run --project absent-project $mode_args 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo 'an unknown project id must fail rather than be judged' >&2
    exit 1
  }
  grep -Fq 'host-access-broker.json' <<<"$unknown_output"
  grep -Fq 'absent-project' <<<"$unknown_output"
  if grep -Fq 'deployment_lifecycle' <<<"$unknown_output"; then
    echo 'a missing project id must not be reported against the governance manifest' >&2
    exit 1
  fi
done
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# AC-3, governance side: a project id that resolves to a repository the
# governance manifest does not describe fails naming the repository, so the
# reader knows which of the two files is short an entry. aisoft_host_access
# rejects this shape at load time (contract.py: "repository is absent from
# governance"), but this tool reads the file itself and must not assume it was
# ever validated.
for mode_args in "501" "--apply 501"; do
  rc=0
  # shellcheck disable=SC2086
  dangling_output="$(run --project dangling-project $mode_args 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo 'a repository absent from governance must fail rather than be judged' >&2
    exit 1
  }
  grep -Fq 'DanglingRepository' <<<"$dangling_output"
  grep -Fq 'deployment_lifecycle' <<<"$dangling_output"
done
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# An access manifest this tool cannot read is an error too — same posture the
# governance manifest already has, for the same reason.
printf '%s\n' 'not json' >"$TMP/broken-access-manifest.json"
for bad_case in "$TMP/absent-access-manifest.json" "$TMP/broken-access-manifest.json"; do
  rc=0
  bad_output="$(run_with_access_manifest "$bad_case" 501 2>&1)" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "an unreadable host access manifest must fail: $bad_case" >&2
    exit 1
  }
  grep -Fq 'mark-completed:' <<<"$bad_output"
done

# AC-1/AC-2 on the real pair. localwms -> LocalWMS is the mapping that made this
# Issue: it is one of six real projects whose id differs from its repository, and
# before #172 this exact invocation exited 1 without reaching an Issue. Only the
# derivation and the resulting verdict are asserted here — what the real
# manifests contain stays pinned in
# codex/runtime/tests/test_deployment_lifecycle.py, so the fixture above is
# still not a copy of production.
: >"$TMP/broker.log"
real_plan="$(
  PYTHONPATH="$ROOT/codex/runtime" \
    AISOFT_GOVERNANCE_MANIFEST="$ROOT/codex/config/gitea-governance.json" \
    AISOFT_ACCESS_MANIFEST="$ROOT/codex/config/host-access-broker.json" \
    bash "$BIN/mark-completed-issues.sh" --repo "$REPO" --project localwms 501 502
)"
jq -e 'select(.issue == 501) | .action == "set-completed"' <<<"$real_plan" >/dev/null
# LocalWMS declares no deployment_lifecycle, so it is also the real-manifest case
# for #192: before it, this exact invocation skipped #502 and nothing else ever
# wrote a terminal label -- five merged LocalWMS Issues are closed with no label
# at all because of it. The verdict is now completed, on stated grounds.
jq -e 'select(.issue == 502)
  | .action == "set-completed" and .reason == "deployment-not-guaranteed"' \
  <<<"$real_plan" >/dev/null
grep -Fq 'LocalWMS' <<<"$(jq -r 'select(.issue == 502) | .detail' <<<"$real_plan")"
[ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]

# --- #184: which repository this run is allowed to write to ------------------
#
# Every case above hands the tool an explicit --project because $REPO has no Git
# remote to derive one from. That covers the override path. What follows covers
# the derivation itself, and the two refusals that replace the old default.
#
# This tool writes a terminal lifecycle label, so the default it used to carry
# did not merely misreport: pointed at another project's checkout without
# --project, it stamped that checkout's finishing verdict onto the platform
# repository's same-numbered Issue.
REPO_REMOTE="$TMP/repo-with-remote"
cp -R "$REPO" "$REPO_REMOTE"
git -C "$REPO_REMOTE" remote add origin \
  "$FIXTURE_BASE_URL/$FIXTURE_OWNER/NoDeployRepository.git"

run_repo() {
  local repo="$1"
  shift
  PYTHONPATH="$ROOT/codex/runtime" AISOFT_GOVERNANCE_MANIFEST="$MANIFEST" \
    AISOFT_ACCESS_MANIFEST="$ACCESS_MANIFEST" \
    bash "$BIN/mark-completed-issues.sh" --repo "$repo" "$@"
}

# AC-1/AC-5: with no --project at all, the checkout decides, and every line says
# which project and repository it decided on. NoDeployRepository is nothing like
# no-deploy-project, so this travels the mapping rather than coinciding with it.
: >"$TMP/broker.log"
derived_plan="$(run_repo "$REPO_REMOTE" 502)"
jq -e 'select(.issue == 502)
  | .action == "set-completed" and .reason == "no-deployment-chain"
    and .project == "no-deploy-project" and .repository == "NoDeployRepository"' \
  <<<"$derived_plan" >/dev/null

derived_apply="$(run_repo "$REPO_REMOTE" --apply 502)"
jq -e 'select(.issue == 502)
  | .applied == true and .project == "no-deploy-project"' <<<"$derived_apply" >/dev/null
grep -Fq -- '--project no-deploy-project' "$TMP/broker.log"
if grep -Fq -- '--project aisoft-platform' "$TMP/broker.log"; then
  echo 'the tool wrote against a repository the checkout does not belong to' >&2
  exit 1
fi

# AC-3: a --project contradicting the checkout is a full stop, in both modes.
# Nothing is printed and the broker is not called -- a write refused after the
# fact is still a write.
for mode_args in "502" "--apply 502"; do
  : >"$TMP/broker.log"
  rc=0
  # shellcheck disable=SC2086
  mismatch_output="$(
    run_repo "$REPO_REMOTE" --project explicit-deploy-project $mode_args 2>"$TMP/mc-mismatch.err"
  )" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "--project contradicting the checkout must fail: $mode_args" >&2
    exit 1
  }
  [ -z "$mismatch_output" ]
  [ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]
  grep -Fq 'no-deploy-project' "$TMP/mc-mismatch.err"
  grep -Fq 'explicit-deploy-project' "$TMP/mc-mismatch.err"
done

# AC-4: no remote and no --project is a refusal carrying its own remedy, not a
# silent fall back to whichever project the tool was written in.
for mode_args in "501" "--apply 501"; do
  : >"$TMP/broker.log"
  rc=0
  # shellcheck disable=SC2086
  undetermined="$(run_repo "$REPO" $mode_args 2>"$TMP/mc-undetermined.err")" || rc=$?
  [ "$rc" -ne 0 ] || {
    echo "an undeterminable target must fail: $mode_args" >&2
    exit 1
  }
  [ -z "$undetermined" ]
  [ "$(wc -l <"$TMP/broker.log" | tr -d ' ')" = 0 ]
  grep -Fq -- '--project' "$TMP/mc-undetermined.err"
done

echo 'mark-completed tests passed'
