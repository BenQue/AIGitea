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
set -euo pipefail
set +x

fail() {
  printf 'ERROR: apply-classification: %s\n' "$*" >&2
  exit 1
}

tool_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo=""
range=""
project="aisoft-platform"
apply=0
issues=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo="${2:-}"; shift 2 ;;
    --range) range="${2:-}"; shift 2 ;;
    --project) project="${2:-}"; shift 2 ;;
    --apply) apply=1; shift ;;
    --) shift; break ;;
    -*) fail "unknown option: $1" ;;
    *) issues+=("$1"); shift ;;
  esac
done
issues+=("$@")

if [ -z "$repo" ]; then
  repo="$(cd -- "$tool_dir/../.." && pwd)"
fi
[ -d "$repo/docs/changes" ] || fail "no docs/changes under $repo; --repo must be a change checkout"
for binary in jq git python3; do
  command -v "$binary" >/dev/null 2>&1 || fail "$binary is required"
done

# Same-directory first, matching the flat install layout the other tools use.
if [ -x "$tool_dir/host-access-broker.sh" ]; then
  broker="$tool_dir/host-access-broker.sh"
elif [ -x /usr/local/libexec/aisoft/host-access-broker ]; then
  broker=/usr/local/libexec/aisoft/host-access-broker
else
  broker=""
fi
# Unlike mark-completed-issues.sh, the broker is needed in both modes: the plan
# reports whether each Issue is still open, and an Issue's state is only
# knowable through it. A plan that listed an Issue this tool would then refuse
# to write would be worse than no plan.
[ -n "$broker" ] || fail 'host access broker is unavailable; it is needed to read Issue state'

# The runtime supplies resolve-documents. Repository layout first; otherwise
# whatever PYTHONPATH the install already exports, as the VM agents do.
if [ -d "$tool_dir/../runtime" ]; then
  PYTHONPATH="$(cd -- "$tool_dir/../runtime" && pwd)${PYTHONPATH:+:$PYTHONPATH}"
  export PYTHONPATH
fi

# Each Closes #N on its own line, with the change/N-slug branch name in the
# subject as fallback — the same convention 02 §9 documents for merge messages.
if [ -n "$range" ]; then
  while IFS= read -r candidate; do
    [ -n "$candidate" ] && issues+=("$candidate")
  done < <(
    git -C "$repo" log --format=%B "$range" |
      awk '
        /^Closes #[1-9][0-9]*$/ { print substr($0, 9); next }
        /change\/[1-9][0-9]*/ {
          if (match($0, /change\/[1-9][0-9]*/)) {
            print substr($0, RSTART + 7, RLENGTH - 7)
          }
        }
      '
  )
fi

if [ "${#issues[@]}" -eq 0 ]; then
  fail 'no Issue selector given; pass Issue numbers or --range <git range>'
fi

emit() {
  jq -cn --argjson issue "$1" --arg action "$2" --arg reason "$3" \
    --arg detail "$4" --argjson applied "$5" --arg result "$6" \
    --arg change_type "$7" --arg complexity "$8" '
    {issue: $issue, action: $action, applied: $applied}
    + (if $reason == "" then {} else {reason: $reason} end)
    + (if $detail == "" then {} else {detail: $detail} end)
    + (if $result == "" then {} else {result: $result} end)
    + (if $change_type == "" then {} else {change_type: $change_type} end)
    + (if $complexity == "" then {} else {complexity: $complexity} end)
  '
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
for issue in "${issues[@]}"; do
  case "$issue" in
    [1-9]*[!0-9]* | *[!0-9]* | '') fail "not an Issue number: $issue" ;;
  esac
  case " $seen " in *" $issue "*) continue ;; esac
  seen="$seen $issue"

  documents=""
  if ! documents="$(
    python3 -m aisoft_loop.cli resolve-documents "$issue" --repo "$repo" 2>/dev/null
  )"; then
    emit "$issue" skip documents-unresolved \
      "no mapped change documents for Issue #$issue under $repo" false '' '' ''
    continue
  fi
  summary_name="$(jq -r '.summary // empty' <<<"$documents")"
  if [ -z "$summary_name" ]; then
    emit "$issue" skip documents-unresolved \
      "Issue #$issue has no mapped summary document" false '' '' ''
    continue
  fi
  summary_path="$(
    find "$repo/docs/changes" -maxdepth 2 -type f -name "$summary_name" -print -quit
  )"
  if [ -z "$summary_path" ]; then
    emit "$issue" skip documents-unresolved \
      "mapped summary $summary_name is missing from the checkout" false '' '' ''
    continue
  fi

  # change_type and effective_complexity are the判定 source of record: they are
  # the analyzer's own output fields, so the labels follow the classification
  # instead of a fresh human opinion about the change.
  change_type="$(front_matter_scalar "$summary_path" change_type)"
  complexity="$(front_matter_scalar "$summary_path" effective_complexity)"
  if [ -z "$change_type" ]; then
    emit "$issue" skip classification-missing \
      "summary $summary_name declares no change_type" false '' '' ''
    continue
  fi
  if [ -z "$complexity" ]; then
    # A deliberately absent effective_complexity is the needs-human-decision
    # case (contract_effect: unclear). There is no complexity to project yet,
    # and inventing one would put a decision the analyzer refused to make onto
    # the Issue as if it had been made.
    emit "$issue" skip classification-incomplete \
      "summary $summary_name declares no effective_complexity; the analysis is awaiting a human decision" \
      false '' "$change_type" ''
    continue
  fi

  # A closed Issue's classification is history. Backfilling it changes the
  # record without adding information: the judgement is already in the merged
  # summary, and list-issues only ever asks for open Issues (state=open), so a
  # label written here would not even be reachable by the retrieval this exists
  # to serve. There is deliberately no override flag.
  state=""
  if ! state="$(
    "$broker" --project "$project" --operation gitea.issue.read --number "$issue" 2>/dev/null |
      jq -r '.state // empty'
  )" || [ -z "$state" ]; then
    emit "$issue" skip state-unreadable \
      "broker could not read the state of Issue #$issue" false '' \
      "$change_type" "$complexity"
    failed=1
    continue
  fi
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
  written=""
  if ! written="$(
    "$broker" --project "$project" --operation gitea.issue.labels.classify \
      --number "$issue" --change-type "$change_type" --complexity "$complexity"
  )"; then
    emit "$issue" set-classification broker-refused \
      "broker refused the write for Issue #$issue" false '' \
      "$change_type" "$complexity"
    failed=1
    continue
  fi
  emit "$issue" set-classification '' '' true \
    "$(jq -r '.result // "unknown"' <<<"$written")" "$change_type" "$complexity"
done

exit "$failed"
