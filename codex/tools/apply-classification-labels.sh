#!/usr/bin/env bash
# Project one AI classification onto an Issue's type/ and complexity/ labels
# (#160).
#
# This is the interactive-session executor. Nothing else was in a position to be
# one: aisoft_loop's apply-analysis is the only other writer of these two
# dimensions and it runs inside the Development Loop, which a Mac session does
# not run. So an Issue opened from a session kept its classification in the
# summary front matter and nowhere else, and the four-dimension label contract
# (03 §9) went unmet on every one of them.
#
# Posture matches mark-completed-issues.sh: run deliberately by an operator, so
# a prerequisite it cannot satisfy is an error rather than a warning — silently
# doing nothing would read as "every Issue was already correct".
#
# The judgement lives here, never in the broker: which Issues are candidates,
# which values to project, and whether a closed Issue may be rewritten. The
# broker performs one constrained write and knows nothing about change
# documents. It does check the two values against the installed label manifest,
# which is a different question — what the label contract allows, not what this
# Issue was judged to be.
#
# The values are never a caller argument. They are read out of the Issue's
# mapped summary front matter, which is where the analysis put them; a human who
# wants a different label changes the classification, not the label.
#
# --verify (#167) reads back what is actually on the Issue and compares it to
# that same summary. The plan mode cannot do this: it only reports what it would
# write, so an Issue that was never projected and one that was projected an hour
# ago produce byte-identical output. Nothing could therefore assert "this Issue's
# classification is visible" before the window closes -- and it closes at merge,
# permanently, because a closed Issue is never rewritten. Read-only: it reaches
# for gitea.issue.read and gitea.issue.labels.read, both of which predate
# gitea.issue.labels.classify, so the gate still works on a broker install too
# stale to perform the write it is asking about.
set -euo pipefail
set +x

fail() {
  printf 'ERROR: apply-classification: %s\n' "$*" >&2
  exit 1
}

tool_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo=""
range=""
# No default (#184). --repo already names a checkout, and a project id that is
# never checked against it turns "I do not know" into a confident conclusion
# about a repository nobody meant to touch.
project=""
apply=0
verify=0
issues=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo="${2:-}"; shift 2 ;;
    --range) range="${2:-}"; shift 2 ;;
    --project) project="${2:-}"; shift 2 ;;
    --apply) apply=1; shift ;;
    --verify) verify=1; shift ;;
    --) shift; break ;;
    -*) fail "unknown option: $1" ;;
    *) issues+=("$1"); shift ;;
  esac
done
issues+=("$@")

# One mode per run. Verifying and writing in the same pass would report on a
# state this run had just created, which is not a read-back of anything.
if [ "$apply" -eq 1 ] && [ "$verify" -eq 1 ]; then
  fail '--verify and --apply are separate modes; --verify reads back what is on the Issue, --apply writes it'
fi

if [ -z "$repo" ]; then
  repo="$(cd -- "$tool_dir/../.." && pwd)"
fi
[ -d "$repo/docs/changes" ] || fail "no docs/changes under $repo; --repo must be a change checkout"
for binary in jq git python3; do
  command -v "$binary" >/dev/null 2>&1 || fail "$binary is required"
done

# Shared project target resolution (#184), same same-directory-first convention.
# It decides which repository this run may speak about, from the checkout rather
# than from a default, and it does so before a single Issue is read: a run that
# cannot name its target must produce no lines at all, because a line is what
# gets believed.
if [ -f "$tool_dir/aisoft-project-target.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/aisoft-project-target.sh"
elif [ -f "$tool_dir/../agent/aisoft-project-target.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/../agent/aisoft-project-target.sh"
else
  fail 'shared project target library aisoft-project-target.sh is unavailable'
fi
aisoft_resolve_project_target "$tool_dir" "$repo" "$project" ||
  fail "$AISOFT_PROJECT_TARGET_ERROR"

# Same-directory first, matching the flat install layout the other tools use.
if [ -x "$tool_dir/host-access-broker.sh" ]; then
  broker="$tool_dir/host-access-broker.sh"
elif [ -x /usr/local/libexec/aisoft/host-access-broker ]; then
  broker=/usr/local/libexec/aisoft/host-access-broker
else
  broker=""
fi
# Unlike mark-completed-issues.sh, the broker is needed in every mode: the plan
# reports whether each Issue is still open, and an Issue's state is only
# knowable through it. A plan that listed an Issue this tool would then refuse
# to write would be worse than no plan.
[ -n "$broker" ] || fail 'host access broker is unavailable; it is needed to read Issue state'

broker_stderr_file="$(mktemp)"
trap 'rm -f -- "$broker_stderr_file"' EXIT
broker_stdout=""
broker_stderr=""
broker_reason=""
broker_detail=""

# The broker writes its typed refusal as JSON on stderr and exits non-zero. A
# caller that only captures stdout therefore sees an empty string and has to
# report "unreadable" for a condition the broker had already described exactly.
run_broker() {
  local operation="$1"
  shift
  local status=0
  broker_stdout=""
  broker_stderr=""
  broker_reason=""
  broker_detail=""
  : >"$broker_stderr_file"
  broker_stdout="$(
    "$broker" --project "$AISOFT_PROJECT_ID" --operation "$operation" "$@" 2>"$broker_stderr_file"
  )" || status=1
  broker_stderr="$(cat "$broker_stderr_file")"
  if [ "$status" -ne 0 ]; then
    broker_failure_reason "$operation"
  fi
  return "$status"
}

# An installed broker's operation table is fixed at install time, so a typed
# operation the running install does not carry is refused with REQUEST_DENIED --
# the same code a credential or ACL problem produces. Reading that as a
# permission problem sends the operator to the wrong place; #167 is the Issue
# where exactly that cost a classification window. Naming the difference is the
# whole job here (06 踩坑 20).
broker_failure_reason() {
  case "$broker_stderr" in
    *REQUEST_DENIED*'not allowlisted'*)
      broker_reason='broker-operation-missing'
      broker_detail="the installed host-access-broker does not carry $1; its operation table is fixed at install time, so this is a stale install and not a permission problem. Reinstall on both Mac and gitea-ci with: sudo bash codex/install-host-access-broker.sh (06 踩坑 20), then rerun."
      ;;
    *)
      broker_reason=""
      broker_detail=""
      ;;
  esac
}

# Shared merge-range resolution (#175), same same-directory-first convention.
# It is not optional: without it a --range run has no way to report which
# commits it covered, and reporting that is the whole reason the range is
# resolved up front rather than piped straight into the Issue list.
if [ -f "$tool_dir/change-merge-range.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/change-merge-range.sh"
elif [ -f "$tool_dir/../agent/change-merge-range.sh" ]; then
  # shellcheck disable=SC1090,SC1091
  . "$tool_dir/../agent/change-merge-range.sh"
else
  fail 'shared merge range library change-merge-range.sh is unavailable'
fi

# The runtime supplies resolve-documents. Repository layout first; otherwise
# whatever PYTHONPATH the install already exports, as the VM agents do.
if [ -d "$tool_dir/../runtime" ]; then
  PYTHONPATH="$(cd -- "$tool_dir/../runtime" && pwd)${PYTHONPATH:+:$PYTHONPATH}"
  export PYTHONPATH
fi

# A range is resolved once, up front, and what it resolved to is reported before
# anything else happens (#175). origin/main~N is evaluated when this process
# starts, not when the operator fetched and not when the operator approved a
# plan, so a range anchored on it can silently cover somebody else's merge. The
# selector line names every commit the range actually covered and hands back
# `pinned` -- the Issue numbers, which no ref movement can change -- for the
# --apply rerun. Not called inside "$(...)": the fork would discard the result.
#
# --verify carries the same exposure and the same fix. A verify run aimed by a
# slid range reads back somebody else's Issue and reports it as projected, which
# is worse than no gate at all: #167 exists because that gate is the last thing
# standing between a classification and a window that never reopens.
if [ -n "$range" ]; then
  aisoft_merge_range_resolve "$repo" "$range" ||
    fail "cannot resolve --range $range against $repo"
  printf '%s\n' "$AISOFT_MERGE_RANGE_SELECTOR"
  if [ "${#AISOFT_MERGE_RANGE_ISSUES[@]}" -gt 0 ]; then
    issues+=("${AISOFT_MERGE_RANGE_ISSUES[@]}")
  fi
fi

# A range that selected nothing is not the same failure as no selector at all,
# and saying so is the point: "you gave none" sends the operator to look for a
# missing argument, when in fact the argument was there and aimed somewhere
# empty. That is the mis-aim of #175 in its most extreme form.
if [ "${#issues[@]}" -eq 0 ]; then
  if [ -n "$range" ]; then
    if [ "$AISOFT_MERGE_RANGE_COMMIT_COUNT" -eq 0 ]; then
      fail "--range $range covers no commits in $repo; see the selector line above. A range anchored on a moving ref such as origin/main~N resolves when this command runs, not when you fetched."
    fi
    fail "--range $range covers $AISOFT_MERGE_RANGE_COMMIT_COUNT commit(s), none of which names an Issue; see the selector line above for what it covered."
  fi
  fail 'no Issue selector given; pass Issue numbers or --range <git range>'
fi

# issue_commit is set by the loop below and read here rather than passed: every
# line of one iteration reports the same commit, and threading it through every
# call site would say nothing the loop variable does not. It is also read by
# verify_issue and unresolved, which already read the loop's other per-Issue
# state the same way.
issue_commit=""
# project and repository are read from the resolver, not passed in: "which
# repository is this line about" is precisely the question #184 answered wrongly
# and silently, and a field a call site could forget to fill would be no answer.
emit() {
  jq -cn --argjson issue "$1" --arg action "$2" --arg reason "$3" \
    --arg detail "$4" --argjson applied "$5" --arg result "$6" \
    --arg change_type "$7" --arg complexity "$8" --arg remedy "${9:-}" \
    --arg commit "$issue_commit" \
    --arg project "$AISOFT_PROJECT_ID" --arg repository "$AISOFT_PROJECT_REPOSITORY" '
    {issue: $issue, project: $project, repository: $repository,
     action: $action, applied: $applied}
    + (if $commit == "" then {} else {commit: $commit} end)
    + (if $reason == "" then {} else {reason: $reason} end)
    + (if $detail == "" then {} else {detail: $detail} end)
    + (if $result == "" then {} else {result: $result} end)
    + (if $change_type == "" then {} else {change_type: $change_type} end)
    + (if $complexity == "" then {} else {complexity: $complexity} end)
    + (if $remedy == "" then {} else {remedy: $remedy} end)
  '
}

# Verify mode answers one question per Issue -- is this classification visible
# on the Issue right now -- so a line that cannot answer it is a failure, not a
# quiet skip. Plan mode keeps its own reading: there, an unresolvable document
# simply means there is nothing to project, which is not an error.
unresolved() {
  emit "$1" "$line_action" "$2" "$3" false '' "$4" "$5"
  if [ "$verify" -eq 1 ]; then
    failed=1
  fi
}

# The read-back itself, over the loop's current Issue. Each dimension is
# compared as a whole set rather than "does it contain": the contract is exactly
# one type/ and exactly one complexity/ label, so two type/ labels is a mismatch
# and not a match with something extra.
verify_issue() {
  local observed_type observed_complexity observed remedy
  if ! run_broker gitea.issue.labels.read --number "$issue"; then
    emit "$issue" verify "${broker_reason:-labels-unreadable}" \
      "${broker_detail:-broker could not read the labels of Issue #$issue}" false '' \
      "$change_type" "$complexity"
    failed=1
    return
  fi
  observed_type="$(
    jq -r '[.[]? | .name? // empty | select(startswith("type/"))] | sort | join(",")' \
      <<<"$broker_stdout" 2>/dev/null || true
  )"
  observed_complexity="$(
    jq -r '[.[]? | .name? // empty | select(startswith("complexity/"))] | sort | join(",")' \
      <<<"$broker_stdout" 2>/dev/null || true
  )"
  observed="type=${observed_type:-<none>} complexity=${observed_complexity:-<none>}"

  if [ "$observed_type" = "type/$change_type" ] &&
    [ "$observed_complexity" = "complexity/$complexity" ]; then
    emit "$issue" verify '' \
      "Issue #$issue carries the classification its merged summary declares" \
      false projected "$change_type" "$complexity"
    return
  fi

  # Closed and unprojected is the one outcome with no remedy. #160 does not
  # rewrite a closed Issue and offers no override, so the window that shut at
  # merge stays shut; an absent remedy field is how that is said in machine
  # terms. The judgement is not lost -- it is in the merged summary -- and this
  # line is the report that says which Issues that applies to.
  if [ "$state" != open ]; then
    emit "$issue" verify projection-window-closed \
      "Issue #$issue is $state and its classification was never projected; the window closed at merge. The judgement stays in the merged summary and is not rewritten here (#160, 03 §11). Observed: $observed" \
      false '' "$change_type" "$complexity"
    failed=1
    return
  fi

  remedy="codex/tools/apply-classification-labels.sh --apply $issue"
  if { [ -n "$observed_type" ] && [ "$observed_type" != "type/$change_type" ]; } ||
    { [ -n "$observed_complexity" ] && [ "$observed_complexity" != "complexity/$complexity" ]; }; then
    emit "$issue" verify projection-mismatch \
      "Issue #$issue carries a classification its merged summary does not declare. Expected: type/$change_type complexity/$complexity. Observed: $observed" \
      false '' "$change_type" "$complexity" "$remedy"
    failed=1
    return
  fi
  emit "$issue" verify projection-missing \
    "Issue #$issue is missing a classification dimension; the judgement is still only in the summary, and the window closes when this Issue is merged and closed. Expected: type/$change_type complexity/$complexity. Observed: $observed" \
    false '' "$change_type" "$complexity" "$remedy"
  failed=1
}

# One scalar out of the first front matter block. Anchored at column zero so a
# nested key under documents: or risk_flags: cannot be mistaken for a top-level
# one, and bounded by the closing fence so prose below it is never read.
front_matter_scalar() {
  awk -v key="$2" '
    /^---[[:space:]]*$/ { fence++; next }
    fence >= 2 { exit }
    fence == 1 && index($0, key ":") == 1 {
      value = substr($0, length(key) + 2)
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      if (value ~ /^".*"$/ || value ~ /^'"'"'.*'"'"'$/) {
        value = substr(value, 2, length(value) - 2)
      }
      print value
      exit
    }
  ' "$1"
}

seen=""
failed=0
line_action=skip
if [ "$verify" -eq 1 ]; then
  line_action=verify
fi
for issue in "${issues[@]}"; do
  case "$issue" in
    [1-9]*[!0-9]* | *[!0-9]* | '') fail "not an Issue number: $issue" ;;
  esac
  case " $seen " in *" $issue "*) continue ;; esac
  seen="$seen $issue"
  # Empty for an Issue passed as a bare number: it was not derived from any
  # commit, so there is no commit to name.
  issue_commit="$(aisoft_merge_range_commit_for "$issue" || true)"

  documents=""
  if ! documents="$(
    python3 -m aisoft_loop.cli resolve-documents "$issue" --repo "$repo" 2>/dev/null
  )"; then
    unresolved "$issue" documents-unresolved \
      "no mapped change documents for Issue #$issue under $repo" '' ''
    continue
  fi
  summary_name="$(jq -r '.summary // empty' <<<"$documents")"
  if [ -z "$summary_name" ]; then
    unresolved "$issue" documents-unresolved \
      "Issue #$issue has no mapped summary document" '' ''
    continue
  fi
  summary_path="$(
    find "$repo/docs/changes" -maxdepth 2 -type f -name "$summary_name" -print -quit
  )"
  if [ -z "$summary_path" ]; then
    unresolved "$issue" documents-unresolved \
      "mapped summary $summary_name is missing from the checkout" '' ''
    continue
  fi

  # change_type and effective_complexity are the判定 source of record: they are
  # the analyzer's own output fields, so the labels follow the classification
  # instead of a fresh human opinion about the change.
  change_type="$(front_matter_scalar "$summary_path" change_type)"
  complexity="$(front_matter_scalar "$summary_path" effective_complexity)"
  if [ -z "$change_type" ]; then
    unresolved "$issue" classification-missing \
      "summary $summary_name declares no change_type" '' ''
    continue
  fi
  if [ -z "$complexity" ]; then
    # A deliberately absent effective_complexity is the needs-human-decision
    # case (contract_effect: unclear). There is no complexity to project yet,
    # and inventing one would put a decision the analyzer refused to make onto
    # the Issue as if it had been made.
    unresolved "$issue" classification-incomplete \
      "summary $summary_name declares no effective_complexity; the analysis is awaiting a human decision" \
      "$change_type" ''
    continue
  fi

  state=""
  if run_broker gitea.issue.read --number "$issue"; then
    state="$(jq -r '.state // empty' <<<"$broker_stdout" 2>/dev/null || true)"
  fi
  if [ -z "$state" ]; then
    emit "$issue" "$line_action" "${broker_reason:-state-unreadable}" \
      "${broker_detail:-broker could not read the state of Issue #$issue}" false '' \
      "$change_type" "$complexity"
    failed=1
    continue
  fi

  if [ "$verify" -eq 1 ]; then
    verify_issue
    continue
  fi

  # A closed Issue's classification is history. Backfilling it changes the
  # record without adding information: the judgement is already in the merged
  # summary, and list-issues only ever asks for open Issues (state=open), so a
  # label written here would not even be reachable by the retrieval this exists
  # to serve. There is deliberately no override flag.
  if [ "$state" != open ]; then
    emit "$issue" skip issue-closed \
      "Issue #$issue is $state; its classification is recorded in the merged summary and is not rewritten here" \
      false '' "$change_type" "$complexity"
    continue
  fi

  if [ "$apply" -eq 0 ]; then
    emit "$issue" set-classification '' '' false '' "$change_type" "$complexity"
    continue
  fi
  if ! run_broker gitea.issue.labels.classify \
    --number "$issue" --change-type "$change_type" --complexity "$complexity"; then
    emit "$issue" set-classification "${broker_reason:-broker-refused}" \
      "${broker_detail:-broker refused the write for Issue #$issue}" false '' \
      "$change_type" "$complexity"
    failed=1
    continue
  fi
  emit "$issue" set-classification '' '' true \
    "$(jq -r '.result // "unknown"' <<<"$broker_stdout")" "$change_type" "$complexity"
done

exit "$failed"
