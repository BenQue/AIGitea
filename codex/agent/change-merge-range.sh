#!/usr/bin/env bash
# Shared merge-range resolution for the finishing-path label tools (#175).
#
# Sourced library, never an executable entry point. It does not alter caller
# shell options (-e/-u/pipefail).
#
# The problem it exists to solve is not parsing. Both callers could already
# parse a range; they each carried a byte-identical copy of the awk below, which
# is how one defect came to live in two places. The problem is that a range like
# origin/main~1..origin/main is resolved when the tool starts, not when the
# operator fetched and not when the operator approved the plan. Two windows
# follow, and main moving in either one slides the range onto somebody else's
# Issue:
#
#   W1  git.fetch.main  -> plan run      (#167 hit this one: the plan reported
#                                         Issue 168 while the operator was
#                                         finishing Issue 167)
#   W2  plan run        -> --apply run   (longer: the contract puts a human
#                                         confirmation between them, and --apply
#                                         re-resolves the symbolic ref from
#                                         scratch)
#
# Printing what the range resolved to closes W1 only. W2 closes because the
# resolution also hands back `pinned`: the Issue numbers it derived, which both
# tools already accept as bare arguments and which no ref movement can change.
# The plan is what the operator reads; `pinned` is what the operator reruns.
#
# Order matters and is not interchangeable: `commits` is the evidence for
# deciding whether the range aimed where it was meant to, `pinned` merely fixes
# a conclusion that has already been looked at. A `pinned` produced by a
# mis-aimed range faithfully pins the wrong Issue -- that is the point of
# emitting both on the same line.
#
# The awk rules are carried over verbatim from the two callers: each Closes #N
# on its own line, with the change/N-slug branch name as fallback, the same
# convention 02 §9 documents for merge messages. Which Issues a range selects is
# deliberately unchanged by #175.
#
# Results come back through globals rather than stdout, and that is forced
# rather than stylistic: a caller capturing stdout writes x="$(resolve ...)",
# which forks a subshell, and the parsed Issue list set inside it would be
# discarded along with the fork. The selector line is therefore handed back as a
# string for the caller to print at the moment it chooses. Diagnostics still go
# to stderr. git and jq are required; both callers already depend on them.

# Index-aligned, not an associative array: macOS ships bash 3.2. Initialised at
# source time so ${#...[@]} is safe before the first resolve, which matters
# because under set -u an empty array still cannot be expanded with [@].
AISOFT_MERGE_RANGE_ISSUES=()
AISOFT_MERGE_RANGE_COMMITS=()
AISOFT_MERGE_RANGE_COMMIT_COUNT=0
AISOFT_MERGE_RANGE_SELECTOR=''

# Issue numbers named by one commit message, read on stdin, deduplicated within
# that message. Callers dedupe across commits separately, keeping the first.
aisoft_merge_range_issue_numbers() {
  awk '
    /^Closes #[1-9][0-9]*$/ { n = substr($0, 9); if (!seen[n]++) print n; next }
    /change\/[1-9][0-9]*/ {
      if (match($0, /change\/[1-9][0-9]*/)) {
        n = substr($0, RSTART + 7, RLENGTH - 7)
        if (!seen[n]++) print n
      }
    }
  '
}

# The commit an already-resolved Issue number came from, or non-zero if this
# resolution did not produce that Issue (it was passed as a bare number).
aisoft_merge_range_commit_for() {
  local wanted="$1" index=0
  [ "${#AISOFT_MERGE_RANGE_ISSUES[@]}" -gt 0 ] || return 1
  while [ "$index" -lt "${#AISOFT_MERGE_RANGE_ISSUES[@]}" ]; do
    if [ "${AISOFT_MERGE_RANGE_ISSUES[$index]}" = "$wanted" ]; then
      printf '%s' "${AISOFT_MERGE_RANGE_COMMITS[$index]}"
      return 0
    fi
    index=$((index + 1))
  done
  return 1
}

# Resolve <range> in <repo>, setting the four globals above. Returns non-zero
# only when git itself could not resolve the range: a range that resolves to
# nothing is a successful resolution of an empty set, and the caller decides
# what to say about it -- but AISOFT_MERGE_RANGE_SELECTOR is populated either
# way, because an empty result is exactly the evidence an operator needs to see.
# Call it directly, never inside "$(...)": the subshell would swallow the
# globals and leave the caller with an empty Issue list.
aisoft_merge_range_resolve() {
  local repo="$1" range="$2"
  local shas sha subject candidate commit_records commits_json pinned

  AISOFT_MERGE_RANGE_ISSUES=()
  AISOFT_MERGE_RANGE_COMMITS=()
  AISOFT_MERGE_RANGE_COMMIT_COUNT=0
  AISOFT_MERGE_RANGE_SELECTOR=''

  if ! shas="$(git -C "$repo" log --format=%H "$range" 2>&1)"; then
    printf 'merge-range: git cannot resolve range %s in %s: %s\n' \
      "$range" "$repo" "$shas" >&2
    return 1
  fi

  commit_records=""
  while IFS= read -r sha; do
    [ -n "$sha" ] || continue
    AISOFT_MERGE_RANGE_COMMIT_COUNT=$((AISOFT_MERGE_RANGE_COMMIT_COUNT + 1))
    subject="$(git -C "$repo" log -1 --format=%s "$sha")"
    local here=()
    while IFS= read -r candidate; do
      [ -n "$candidate" ] || continue
      here+=("$candidate")
      # First commit naming an Issue owns it, matching the callers' own
      # first-wins dedupe over the assembled Issue list.
      if ! aisoft_merge_range_commit_for "$candidate" >/dev/null; then
        AISOFT_MERGE_RANGE_ISSUES+=("$candidate")
        AISOFT_MERGE_RANGE_COMMITS+=("$sha")
      fi
    done < <(
      git -C "$repo" log -1 --format=%B "$sha" | aisoft_merge_range_issue_numbers
    )
    local here_json='[]'
    if [ "${#here[@]}" -gt 0 ]; then
      here_json="$(printf '%s\n' "${here[@]}" | jq -sc 'map(tonumber)')"
    fi
    commit_records="$commit_records$(
      jq -cn --arg commit "$sha" --arg subject "$subject" --argjson issues "$here_json" \
        '{commit: $commit, subject: $subject, issues: $issues}'
    )
"
  done <<EOF
$shas
EOF

  commits_json='[]'
  if [ -n "$commit_records" ]; then
    commits_json="$(printf '%s' "$commit_records" | jq -sc '.')"
  fi
  pinned=""
  if [ "${#AISOFT_MERGE_RANGE_ISSUES[@]}" -gt 0 ]; then
    pinned="${AISOFT_MERGE_RANGE_ISSUES[*]}"
  fi

  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_MERGE_RANGE_SELECTOR="$(
    jq -cn --arg range "$range" --argjson commits "$commits_json" --arg pinned "$pinned" '
      {selector: "range", range: $range, commits: $commits, pinned: $pinned}
    '
  )"
}
