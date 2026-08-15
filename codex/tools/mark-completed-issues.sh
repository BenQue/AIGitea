#!/usr/bin/env bash
# Advance merged Issues that need no deployment to the completed terminal state
# (#115).
#
# This is the merged-phase executor. Nothing else is in a position to be one:
# the controller's lifecycle writes all live inside the Loop, and the Loop ends
# when it opens the pull request; mark-deployed-issues.sh only covers changes
# that actually ship. So an Issue whose contract requires no deployment had no
# component able to observe its merge and move it off pr-open.
#
# Posture differs from mark-deployed-issues.sh on purpose. That one is a
# deployment hook and must never fail an already successful deployment, so every
# missing prerequisite is a warning and exit 0. This one is run deliberately by
# an operator: a prerequisite it cannot satisfy is an error, because silently
# doing nothing would read as "every Issue was already correct".
#
# The judgement lives here, never in the broker: which Issues are candidates,
# and whether each one's contract required a verification document. The broker
# performs one constrained write and knows nothing about change documents.
set -euo pipefail
set +x

fail() {
  printf 'ERROR: mark-completed: %s\n' "$*" >&2
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
    --arg detail "$4" --argjson applied "$5" --arg result "$6" '
    {issue: $issue, action: $action, applied: $applied}
    + (if $reason == "" then {} else {reason: $reason} end)
    + (if $detail == "" then {} else {detail: $detail} end)
    + (if $result == "" then {} else {result: $result} end)
  '
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
      "no mapped change documents for Issue #$issue under $repo" false ''
    continue
  fi
  summary_name="$(jq -r '.summary // empty' <<<"$documents")"
  if [ -z "$summary_name" ]; then
    emit "$issue" skip documents-unresolved \
      "Issue #$issue has no mapped summary document" false ''
    continue
  fi
  summary_path="$(
    find "$repo/docs/changes" -maxdepth 2 -type f -name "$summary_name" -print -quit
  )"
  if [ -z "$summary_path" ]; then
    emit "$issue" skip documents-unresolved \
      "mapped summary $summary_name is missing from the checkout" false ''
    continue
  fi

  # required_docs is the判定 source of record: it is the same field the triage
  # contract already uses to say whether this change owes a verification
  # document, so the terminal state follows the contract instead of a fresh
  # human opinion about the change.
  required_docs="$(
    awk '
      /^---[[:space:]]*$/ { fence++; next }
      fence == 1 && /^required_docs:[[:space:]]*$/ { collecting = 1; next }
      fence == 1 && collecting && /^[[:space:]]*-[[:space:]]/ {
        sub(/^[[:space:]]*-[[:space:]]*/, ""); print; next
      }
      fence == 1 && collecting { collecting = 0 }
      fence >= 2 { exit }
    ' "$summary_path"
  )"
  if [ -z "$required_docs" ]; then
    emit "$issue" skip required-docs-missing \
      "summary $summary_name declares no required_docs" false ''
    continue
  fi
  if grep -Fxq 'verification' <<<"$required_docs"; then
    emit "$issue" skip requires-deployment \
      "required_docs contains verification, so this change ships and its terminal state is deployed, not completed" \
      false ''
    continue
  fi

  if [ "$apply" -eq 0 ]; then
    emit "$issue" set-completed '' '' false ''
    continue
  fi
  [ -n "$broker" ] || fail 'host access broker is unavailable; --apply needs it to write'
  written=""
  if ! written="$(
    "$broker" --project "$project" --operation gitea.issue.labels.set \
      --number "$issue" --lifecycle completed
  )"; then
    emit "$issue" set-completed broker-refused \
      "broker refused the write for Issue #$issue" false ''
    failed=1
    continue
  fi
  emit "$issue" set-completed '' '' true "$(jq -r '.result // "unknown"' <<<"$written")"
done

exit "$failed"
