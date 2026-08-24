#!/usr/bin/env bash
# Resolve which project a change checkout belongs to (#184).
#
# Sourced, never executed. Two operator tools — apply-classification-labels.sh
# and mark-completed-issues.sh — read their judgement out of a checkout given as
# --repo and then act on Issues through the broker's --project. Both used to
# default --project to aisoft-platform, and nothing ever checked that default
# against the checkout sitting right next to it. Pointed at any other project's
# checkout without --project, they read one repository's change documents and
# then spoke about a different repository's Issues, in a well-formed and
# entirely self-consistent way.
#
# That is worse than a crash. A crash sends the operator looking; a wrong answer
# reads as "this step is already done". #167's --verify is the sharpest case:
# it is the only check that distinguishes "projected" from "never projected",
# the window it guards shuts permanently at merge, and against another
# repository it returns a clean pass whenever that repository's same-numbered
# Issue happens to carry the same two labels — type/platform + complexity/complex
# in the platform repository, which is the most common pair there is.
#
# The fix is not a warning. It is a different source of evidence: a checkout's
# Git remote states which repository it belongs to, and that repository is
# exactly the one whose Issues are about to be read or written. So the target is
# derived, --project is demoted from default to override, and the two
# disagreeing is a full stop rather than a preference.
#
# Namespace is unchanged from #172: --project names a host access manifest
# project_id and nothing else. The repository is derived from it, never passed.

# Populated by aisoft_resolve_project_target on success; the error string is
# populated instead on failure so the caller reports it through its own fail().
# shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
AISOFT_PROJECT_ID=""
AISOFT_PROJECT_REPOSITORY=""
AISOFT_PROJECT_SOURCE=""
AISOFT_PROJECT_TARGET_ERROR=""

# Same three-level order the broker and mark-completed-issues.sh already use: an
# explicit override first so tests never reach the installed manifest, then the
# repository layout, then the flat install.
aisoft_project_target_manifest() {
  local override="$1" tool_dir="$2" name="$3"
  if [ -n "$override" ]; then
    printf '%s\n' "$override"
    return 0
  fi
  if [ -f "$tool_dir/../config/$name" ]; then
    printf '%s\n' "$(cd -- "$tool_dir/../config" && pwd)/$name"
    return 0
  fi
  printf '%s\n' "/usr/local/share/aisoft/$name"
}

# Compared forms, not raw strings: a remote written with a trailing slash or
# without the .git suffix names the same repository, and treating those as
# different would send the operator to --project for a checkout that had already
# answered the question.
aisoft_project_target_normalize_url() {
  local url="$1"
  url="${url%/}"
  url="${url%.git}"
  url="${url%/}"
  printf '%s\n' "$url"
}

# Every remote, both its fetch and its push URLs. Not just origin: newemaint,
# rsdesign-new and sfm-digital-board declare git_remote_name "gitea", so their
# Gitea remote is not origin at all, and origin points at an unrelated GitHub
# mirror. Reading only origin would derive nothing on exactly the projects that
# most need this.
aisoft_project_target_remote_urls() {
  local repo="$1" name url
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    while IFS= read -r url; do
      [ -n "$url" ] || continue
      aisoft_project_target_normalize_url "$url"
    done < <(
      git -C "$repo" remote get-url --all "$name" 2>/dev/null
      git -C "$repo" remote get-url --push --all "$name" 2>/dev/null
    )
  done < <(git -C "$repo" remote 2>/dev/null)
}

# tool_dir, checkout, explicit --project value (may be empty).
aisoft_resolve_project_target() {
  local tool_dir="$1" repo="$2" explicit="$3"
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_ID=""
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_REPOSITORY=""
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_SOURCE=""
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_TARGET_ERROR=""

  local access governance
  access="$(
    aisoft_project_target_manifest "${AISOFT_ACCESS_MANIFEST:-}" "$tool_dir" \
      host-access-broker.json
  )"
  governance="$(
    aisoft_project_target_manifest "${AISOFT_GOVERNANCE_MANIFEST:-}" "$tool_dir" \
      gitea-governance.json
  )"
  if [ ! -f "$access" ]; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="host access manifest not found: $access"
    return 1
  fi
  if [ ! -f "$governance" ]; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="governance manifest not found: $governance"
    return 1
  fi

  # base_url and owner build the same URL aisoft_host_access.broker builds in
  # _expected_git_url, so a remote this agrees with is a remote the broker would
  # also accept as the project's own. Reading them here rather than transcribing
  # them keeps the one copy in the manifest.
  local prefix
  if ! prefix="$(
    jq -er '"\(.base_url)/\(.owner)"' "$governance" 2>&1
  )"; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="cannot read base_url and owner from $governance: $prefix"
    return 1
  fi
  prefix="${prefix%/}"

  local remotes
  remotes="$(aisoft_project_target_remote_urls "$repo")"

  local candidates
  if ! candidates="$(
    jq -er --arg prefix "$prefix" '
      .projects[] | "\(.project_id)\t\($prefix)/\(.repository)"
    ' "$access" 2>&1
  )"; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="cannot read projects from $access: $candidates"
    return 1
  fi

  local derived="" derived_count=0 candidate_id candidate_url
  while IFS=$'\t' read -r candidate_id candidate_url; do
    [ -n "$candidate_id" ] || continue
    candidate_url="$(aisoft_project_target_normalize_url "$candidate_url")"
    if printf '%s\n' "$remotes" | grep -Fxq -- "$candidate_url"; then
      derived="${derived:+$derived, }$candidate_id"
      derived_count=$((derived_count + 1))
    fi
  done <<CANDIDATES
$candidates
CANDIDATES

  # More than one match means the checkout carries remotes for two manifest
  # repositories. There is no defensible way to pick one, and picking is exactly
  # the failure this exists to stop.
  if [ "$derived_count" -gt 1 ]; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="$repo has Git remotes for more than one manifest project ($derived); pass --project <project_id> to name the target explicitly"
    return 1
  fi

  if [ -n "$explicit" ]; then
    local repository
    if ! repository="$(
      jq -er --arg id "$explicit" '
        [.projects[] | select(.project_id == $id)] as $entries
        | if ($entries | length) == 1
          then $entries[0].repository
          else error("not exactly one manifest project with id " + $id)
          end
      ' "$access" 2>&1
    )"; then
      # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
      AISOFT_PROJECT_TARGET_ERROR="cannot resolve repository for project id $explicit from $access: $repository"
      return 1
    fi
    # Disagreement is a full stop, not a preference. Either the operator named
    # the wrong project or pointed at the wrong checkout, and both readings end
    # with a conclusion about a repository nobody meant to touch.
    if [ "$derived_count" -eq 1 ] && [ "$derived" != "$explicit" ]; then
      # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
      AISOFT_PROJECT_TARGET_ERROR="--project $explicit does not match the project this checkout belongs to: $repo has the Git remote of $derived. Refusing to report on one repository's Issues from another repository's change documents"
      return 1
    fi
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_ID="$explicit"
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_REPOSITORY="$repository"
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_SOURCE=operator
    return 0
  fi

  # No override and nothing to derive from. A default here is what #184 is: it
  # would be a guess that reads as a fact, and the tools have no way to notice
  # they guessed wrong.
  if [ "$derived_count" -eq 0 ]; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="cannot determine the target project from $repo: none of its Git remotes matches a project in $access. Pass --project <project_id> to name the target explicitly"
    return 1
  fi

  local repository
  if ! repository="$(
    jq -er --arg id "$derived" '
      [.projects[] | select(.project_id == $id)] as $entries
      | if ($entries | length) == 1
        then $entries[0].repository
        else error("not exactly one manifest project with id " + $id)
        end
    ' "$access" 2>&1
  )"; then
    # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
    AISOFT_PROJECT_TARGET_ERROR="cannot resolve repository for project id $derived from $access: $repository"
    return 1
  fi
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_ID="$derived"
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_REPOSITORY="$repository"
  # shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
  AISOFT_PROJECT_SOURCE=checkout
  return 0
}
