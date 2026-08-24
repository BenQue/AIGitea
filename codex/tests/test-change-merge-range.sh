#!/usr/bin/env bash
set -euo pipefail

# change-merge-range.sh turns a git range into a sha-attributed Issue list and
# an immutable selector for the rerun (#175). Every case here runs against a
# fixture repository; the library touches no Issue and no broker.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

# shellcheck disable=SC1091
. "$ROOT/codex/agent/change-merge-range.sh"

REPO="$TMP/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.invalid
git -C "$REPO" config user.name test
git -C "$REPO" commit -q --allow-empty -m 'base'

# Two merge shapes, the same two 02 §9 documents: an explicit Closes #N line,
# and the change/N-slug branch name as fallback.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 600

Closes #501'
sha_501="$(git -C "$REPO" rev-parse HEAD)"
git -C "$REPO" commit -q --allow-empty -m 'Merge branch change/502-deployed-change into main'
sha_502="$(git -C "$REPO" rev-parse HEAD)"

# --- AC-2: the plan says which commit each Issue came from --------------------

# Called directly, never inside "$(...)": the subshell a command substitution
# forks would discard the parsed Issue list the library sets.
aisoft_merge_range_resolve "$REPO" 'HEAD~2..HEAD'
selector="$AISOFT_MERGE_RANGE_SELECTOR"

jq -e '.selector == "range" and .range == "HEAD~2..HEAD"' <<<"$selector" >/dev/null
jq -e '.commits | length == 2' <<<"$selector" >/dev/null

# Each covered commit carries its own sha, its subject, and the Issues it names,
# so nothing has to be reconstructed with a second git log.
jq -e --arg sha "$sha_501" '
  .commits[] | select(.commit == $sha)
  | .issues == [501] and (.subject | test("Merge pull request 600"))
' <<<"$selector" >/dev/null
jq -e --arg sha "$sha_502" '
  .commits[] | select(.commit == $sha) | .issues == [502]
' <<<"$selector" >/dev/null

# The globals are index-aligned: same order, and each Issue maps to the commit
# that produced it.
[ "${AISOFT_MERGE_RANGE_ISSUES[*]}" = '502 501' ]
[ "$(aisoft_merge_range_commit_for 501)" = "$sha_501" ]
[ "$(aisoft_merge_range_commit_for 502)" = "$sha_502" ]
[ "$AISOFT_MERGE_RANGE_COMMIT_COUNT" = 2 ]

# An Issue this resolution did not produce has no commit to report. That is how
# a bare Issue number stays distinguishable from a range-derived one.
if aisoft_merge_range_commit_for 503 >/dev/null; then
  echo 'an unresolved Issue must not report a commit' >&2
  exit 1
fi

# --- AC-1: pinned is the immutable rerun selector ----------------------------
#
# This is the whole point of #175. The plan is read with --range; the rerun uses
# the Issue numbers the plan derived, because Issue numbers cannot move.

[ "$(jq -r '.pinned' <<<"$selector")" = '502 501' ]

# The moving-ref failure itself, made deterministic: another session merges once
# between the two commands. The identical --range argument now covers a
# different merge and names a different Issue -- silently, and with no error.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 601

Closes #503'

aisoft_merge_range_resolve "$REPO" 'HEAD~1..HEAD'
before="$AISOFT_MERGE_RANGE_SELECTOR"
[ "$(jq -r '.pinned' <<<"$before")" = '503' ]

git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 602

Closes #504'

aisoft_merge_range_resolve "$REPO" 'HEAD~1..HEAD'
after="$AISOFT_MERGE_RANGE_SELECTOR"
if [ "$(jq -r '.pinned' <<<"$after")" = "$(jq -r '.pinned' <<<"$before")" ]; then
  echo 'the fixture failed to reproduce a moving range; the rest of this test is vacuous' >&2
  exit 1
fi
[ "$(jq -r '.pinned' <<<"$after")" = '504' ]

# The range moved; the pinned selector did not. Re-resolving by the pinned
# number is what closes the plan -> --apply window, and the commit attribution
# is what would have made the move visible before --apply.
[ "$(jq -r '.commits[0].commit' <<<"$before")" != "$(jq -r '.commits[0].commit' <<<"$after")" ]

# --- Empty and malformed ranges ---------------------------------------------
#
# A range that covers nothing resolves successfully to an empty set: the caller
# decides what to say about it, but the selector line is emitted either way,
# because "it matched nothing" is exactly the evidence an operator needs.
aisoft_merge_range_resolve "$REPO" 'HEAD..HEAD'
empty="$AISOFT_MERGE_RANGE_SELECTOR"
jq -e '.commits == [] and .pinned == ""' <<<"$empty" >/dev/null
[ "$AISOFT_MERGE_RANGE_COMMIT_COUNT" = 0 ]
[ "${#AISOFT_MERGE_RANGE_ISSUES[@]}" = 0 ]

# Commits that carry no Issue reference at all are still reported, with an empty
# issues list. Distinguishing "covered nothing" from "covered commits that name
# no Issue" is the difference between a mis-aimed range and a range aimed at
# ordinary commits.
git -C "$REPO" commit -q --allow-empty -m 'docs: no Issue reference here'
aisoft_merge_range_resolve "$REPO" 'HEAD~1..HEAD'
plain="$AISOFT_MERGE_RANGE_SELECTOR"
jq -e '(.commits | length) == 1 and .commits[0].issues == [] and .pinned == ""' \
  <<<"$plain" >/dev/null
[ "$AISOFT_MERGE_RANGE_COMMIT_COUNT" = 1 ]

# A range git itself cannot resolve is an error, not an empty success.
rc=0
bad="$(aisoft_merge_range_resolve "$REPO" 'no-such-ref..HEAD' 2>&1)" || rc=$?
# Captured in a subshell on purpose: this case asserts the diagnostic and the
# exit status, and reads none of the globals the fork discards.
[ "$rc" -ne 0 ]
grep -Fq 'merge-range: git cannot resolve range' <<<"$bad"

# --- Duplicates ---------------------------------------------------------------
#
# One batched merge may close several Issues, and the same Issue may be named
# twice. Each Issue appears once, owned by the first commit that named it.
git -C "$REPO" commit -q --allow-empty -m 'Merge pull request 603

Closes #505
Closes #506
Closes #505'
sha_batch="$(git -C "$REPO" rev-parse HEAD)"
aisoft_merge_range_resolve "$REPO" 'HEAD~1..HEAD'
batch="$AISOFT_MERGE_RANGE_SELECTOR"
jq -e --arg sha "$sha_batch" '
  .commits[0].commit == $sha and .commits[0].issues == [505, 506]
' <<<"$batch" >/dev/null
[ "$(jq -r '.pinned' <<<"$batch")" = '505 506' ]

# --- The library keeps its hands off the caller's shell ----------------------
#
# Same posture as gitea-token.sh and gitea-label-manifest.sh: sourced, never an
# entry point, and it must not alter -e/-u/pipefail for the caller.
before_opts="$(set +o)"
. "$ROOT/codex/agent/change-merge-range.sh"
[ "$(set +o)" = "$before_opts" ]

# The globals survive because the call is not forked. Pinning this keeps a
# future caller from quietly reintroducing x="$(aisoft_merge_range_resolve ...)"
# and getting an empty Issue list with no error.
aisoft_merge_range_resolve "$REPO" 'HEAD~1..HEAD'
[ -n "$AISOFT_MERGE_RANGE_SELECTOR" ]
[ "${#AISOFT_MERGE_RANGE_ISSUES[@]}" -gt 0 ]

echo 'change-merge-range: OK'
