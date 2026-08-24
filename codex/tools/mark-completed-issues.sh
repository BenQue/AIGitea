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
# whether each one's contract required a verification document, and whether the
# project even has a deployment chain that could write deployed instead. The
# broker performs one constrained write and knows nothing about change documents
# or the governance manifest.
set -euo pipefail
set +x

fail() {
  printf 'ERROR: mark-completed: %s\n' "$*" >&2
  exit 1
}

tool_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo=""
range=""
# No default (#184). This tool writes a terminal lifecycle label, so a project id
# that is never checked against --repo does not merely misreport: it stamps one
# repository's finishing verdict onto another repository's same-numbered Issue.
project=""
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

# --project names one thing and one thing only: a project id in the host access
# manifest. It used to name two, which is what #172 fixed. The broker takes the
# project id; the governance manifest is keyed by repository name; and those two
# coincide for only four of the ten projects, so on the other six every run died
# in the lookup below before it reached a single Issue.
#
# The repository is therefore derived, never passed. The host access manifest
# already declares the mapping and aisoft_host_access.contract already enforces
# that it is a bijection whose values all exist in the governance manifest
# (duplicate project_id / duplicate repository mapping / repository is absent
# from governance). Reading that declaration costs one lookup; asking the caller
# for the repository as well would re-derive a guarantee that exists, and hand
# the caller a second name to get wrong.
#
# #184 removes the other half of the same problem: which project id. It is now
# derived from the checkout's own Git remote, and --project is an override that
# must agree rather than a default nothing checks. Both derivations live in the
# shared library, sourced with the same same-directory-first convention as the
# merge range one above.
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
project="$AISOFT_PROJECT_ID"
repository="$AISOFT_PROJECT_REPOSITORY"

# Whether a project has an application deployment chain that writes deployed is a
# property of the repository, not of any single change, so it is declared once in
# the governance manifest (#163), keyed by repository name — hence the lookup
# above. AISOFT_GOVERNANCE_MANIFEST is the variable aisoft_loop/change_control.py
# already defines for this file, so there is one name for "where the manifest is".
manifest="${AISOFT_GOVERNANCE_MANIFEST:-}"
if [ -z "$manifest" ]; then
  if [ -f "$tool_dir/../config/gitea-governance.json" ]; then
    manifest="$(cd -- "$tool_dir/../config" && pwd)/gitea-governance.json"
  else
    manifest=/usr/local/share/aisoft/gitea-governance.json
  fi
fi

# Read once, up front. A manifest this tool cannot read leaves it unable to tell
# whether deployed is reachable at all, and skipping silently in that state is
# precisely the bug #163 exists to fix, so it is an error — the same posture the
# header states for every other prerequisite. A manifest that simply does not
# declare the key is not an error: absence means the stricter default, and only
# the narrowing value "none" is read here so the default has no second copy
# outside aisoft_gitea_governance.contract.
[ -f "$manifest" ] || fail "governance manifest not found: $manifest"
declared_lifecycle=""
if ! declared_lifecycle="$(
  jq -er --arg name "$repository" '
    [.repositories[] | select(.name == $name)] as $entries
    | if ($entries | length) == 1
      then ($entries[0].deployment_lifecycle // "")
      else error("not exactly one manifest repository named " + $name)
      end
  ' "$manifest" 2>&1
)"; then
  fail "cannot read deployment_lifecycle for repository $repository (project $project) from $manifest: $declared_lifecycle"
fi

# A range is resolved once, up front, and what it resolved to is reported before
# anything else happens (#175). origin/main~N is evaluated when this process
# starts, not when the operator fetched and not when the operator approved a
# plan, so a range anchored on it can silently cover somebody else's merge. The
# selector line names every commit the range actually covered and hands back
# `pinned` -- the Issue numbers, which no ref movement can change -- for the
# --apply rerun. Not called inside "$(...)": the fork would discard the result.
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
# line of one iteration reports the same commit, and threading it through eight
# call sites would say nothing the loop variable does not.
issue_commit=""
# project and repository are read from the resolver, not passed in: "which
# repository is this line about" is precisely the question #184 answered wrongly
# and silently, and a field a call site could forget to fill would be no answer.
emit() {
  jq -cn --argjson issue "$1" --arg action "$2" --arg reason "$3" \
    --arg detail "$4" --argjson applied "$5" --arg result "$6" \
    --arg commit "$issue_commit" \
    --arg project "$project" --arg repository "$repository" '
    {issue: $issue, project: $project, repository: $repository,
     action: $action, applied: $applied}
    + (if $commit == "" then {} else {commit: $commit} end)
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
  # Empty for an Issue passed as a bare number: it was not derived from any
  # commit, so there is no commit to name.
  issue_commit="$(aisoft_merge_range_commit_for "$issue" || true)"

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
  # Two questions, and before #163 this one condition was made to answer both.
  # "Does this change owe a verification document?" is what required_docs says.
  # "Does this change travel an application deployment chain?" is not a property
  # of the change at all — in a project without such a chain no change ever does
  # — so it is answered once by that project's manifest declaration. Conflating
  # them left every verification-declaring platform change with neither terminal
  # state: mark-completed skipped it and no deployment ever ran to write the
  # other one.
  completed_reason=""
  completed_detail=""
  if grep -Fxq 'verification' <<<"$required_docs"; then
    if [ "$declared_lifecycle" != none ]; then
      emit "$issue" skip requires-deployment \
        "required_docs contains verification and $repository has an application deployment chain, so this change ships and its terminal state is deployed, not completed" \
        false ''
      continue
    fi
    completed_reason=no-deployment-chain
    completed_detail="required_docs contains verification, but $repository declares deployment_lifecycle none: nothing writes deployed there, so completed is the only reachable terminal state"
  fi

  if [ "$apply" -eq 0 ]; then
    emit "$issue" set-completed "$completed_reason" "$completed_detail" false ''
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
  emit "$issue" set-completed "$completed_reason" "$completed_detail" true \
    "$(jq -r '.result // "unknown"' <<<"$written")"
done

exit "$failed"
