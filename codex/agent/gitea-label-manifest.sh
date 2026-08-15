#!/usr/bin/env bash
# Shared canonical label manifest access for platform tools (#108).
#
# Sourced library, never an executable entry point. It does not alter caller
# shell options (-e/-u/pipefail).
#
# The manifest at codex/config/gitea-labels.json is schema_version 2:
#
#   {
#     "schema_version": 2,
#     "canonical":          [ {name, color, description}, ... ],
#     "project_extensions": { "allowed_prefixes": [ {prefix, description} ] },
#     "retired":            [ {name, superseded_by, retired_in, description} ]
#   }
#
# schema_version 1 was a bare array of canonical labels. It is rejected rather
# than auto-upgraded: under a half-migrated manifest the readback check would
# still produce an answer, and a confidently wrong governance answer is worse
# than a hard failure.
#
# Managed namespaces (type/, complexity/, triage/) are closed sets owned by the
# platform. project_extensions.allowed_prefixes declares which OTHER prefixes a
# project may define values under; the platform never enumerates those values.
# A declared prefix that overlaps a managed namespace is a contract violation,
# because it would let a project reopen a closed set.
#
# All functions write machine-readable data to stdout and diagnostics to stderr.
# jq is required; callers already depend on it.

AISOFT_LABEL_MANAGED_PREFIXES=('type/' 'complexity/' 'triage/')

# Shared jq prelude defining aisoft_label_norm. Gitea accepts colors with or
# without a leading '#' and in either case, and round-trips descriptions with
# incidental whitespace. Both the provisioner (which decides whether to PATCH)
# and the readback check (which decides whether to report drift) must answer
# "is this label aligned?" identically; a checker that flags drift the
# provisioner considers a no-op would produce a permanently red project with no
# command that fixes it. Hence one definition, sourced by both.
# shellcheck disable=SC2034  # consumed by sourcing tools, not by this library
AISOFT_LABEL_JQ_NORMALIZE='
  def aisoft_label_norm:
    {
      name: .name,
      color: (.color | ltrimstr("#") | ascii_downcase),
      description: (.description | sub("^\\s+"; "") | sub("\\s+$"; ""))
    };
'

aisoft_label_manifest_invalid() {
  printf 'label manifest is invalid: %s\n' "$1" >&2
  return 3
}

# aisoft_label_manifest_validate <manifest_path>
# Fails closed on any structural violation. Returns 0 and prints nothing on
# success.
aisoft_label_manifest_validate() {
  local manifest="$1" problem

  if [[ ! -f "$manifest" ]]; then
    aisoft_label_manifest_invalid "file not found: $manifest"
    return 3
  fi

  if ! jq -e 'type == "object"' "$manifest" >/dev/null 2>&1; then
    if jq -e 'type == "array"' "$manifest" >/dev/null 2>&1; then
      aisoft_label_manifest_invalid \
        'bare-array (schema_version 1) manifests are no longer supported; migrate to the schema_version 2 object (#108)'
      return 3
    fi
    aisoft_label_manifest_invalid 'root must be a JSON object'
    return 3
  fi

  problem="$(
    jq -r '
      def bad(msg): msg;
      [
        (if .schema_version == 2 then empty
         else bad("schema_version must be exactly 2") end),

        (if (.canonical | type) == "array" and (.canonical | length) > 0 then empty
         else bad("canonical must be a non-empty array") end),

        (if (.project_extensions | type) == "object" then empty
         else bad("project_extensions must be an object") end),

        (if (.project_extensions.allowed_prefixes | type) == "array" then empty
         else bad("project_extensions.allowed_prefixes must be an array") end),

        (if (.retired | type) == "array" then empty
         else bad("retired must be an array") end)
      ] | first // empty
    ' "$manifest" 2>/dev/null
  )"
  if [[ -n "$problem" ]]; then
    aisoft_label_manifest_invalid "$problem"
    return 3
  fi

  problem="$(
    jq -r '
      def names: [.canonical[].name];
      [
        (.canonical[]
         | select(((.name | type) != "string") or ((.name | length) == 0))
         | "canonical entry has an empty or non-string name"),

        (.canonical[]
         | select(((.description | type) != "string") or ((.description | length) == 0))
         | "canonical label \(.name) has an empty or non-string description"),

        (.canonical[]
         | select(((.color | type) != "string") or ((.color | test("^[0-9a-fA-F]{6}$")) | not))
         | "canonical label \(.name) has a color that is not 6 hex digits"),

        (if (names | length) == (names | unique | length) then empty
         else "canonical contains duplicate label names" end),

        (.project_extensions.allowed_prefixes[]
         | select(((.prefix | type) != "string") or ((.prefix | endswith("/")) | not))
         | "allowed prefix \(.prefix // "<missing>") must be a string ending in /"),

        (.retired[]
         | select(((.name | type) != "string") or ((.name | length) == 0))
         | "retired entry has an empty or non-string name"),

        (.retired[] as $r | names as $c
         | select($c | index($r.name))
         | "retired label \($r.name) must not also appear in canonical")
      ] | first // empty
    ' "$manifest" 2>/dev/null
  )"
  if [[ -n "$problem" ]]; then
    aisoft_label_manifest_invalid "$problem"
    return 3
  fi

  # A declared extension prefix must not reopen a managed namespace. Checked in
  # shell rather than jq so the managed list stays a single source of truth.
  local prefix managed
  while IFS= read -r prefix; do
    [[ -n "$prefix" ]] || continue
    for managed in "${AISOFT_LABEL_MANAGED_PREFIXES[@]}"; do
      if [[ "$prefix" == "$managed" || "$prefix" == "$managed"* ||
        "$managed" == "$prefix"* ]]; then
        aisoft_label_manifest_invalid \
          "allowed prefix $prefix overlaps managed namespace $managed"
        return 3
      fi
    done
  done < <(jq -r '.project_extensions.allowed_prefixes[].prefix' "$manifest")

  return 0
}

# aisoft_label_manifest_canonical <manifest_path>
# Emits one compact JSON object per canonical label.
aisoft_label_manifest_canonical() {
  jq -c '.canonical[]' "$1"
}

# aisoft_label_manifest_prefixes <manifest_path>
# Emits one declared extension prefix per line.
aisoft_label_manifest_prefixes() {
  jq -r '.project_extensions.allowed_prefixes[].prefix' "$1"
}

# aisoft_label_manifest_retired <manifest_path>
# Emits one retired label name per line.
aisoft_label_manifest_retired() {
  jq -r '.retired[].name' "$1"
}

# aisoft_label_manifest_lifecycle <manifest_path>
# Emits one delivery-lifecycle label name per line (#115).
#
# The lifecycle dimension is exactly the unprefixed canonical names. Every other
# dimension carries a namespace — the managed type/, complexity/ and triage/ sets
# above, and whatever project_extensions declares — so "belongs to no namespace"
# is what makes a canonical label a delivery state, and the rule stays correct
# when a project declares a new prefix.
#
# aisoft_loop.contract.LIFECYCLE_LABELS is the Python half of the same set and is
# pinned to this identical rule by codex/runtime/tests/test_contract.py. Both
# halves derive; neither transcribes. A consumer that needs the eight names calls
# one of them rather than writing a third list.
aisoft_label_manifest_lifecycle() {
  jq -r '.canonical[].name | select(contains("/") | not)' "$1"
}

# aisoft_label_is_managed_namespace <label_name>
# Returns 0 when the name falls inside a platform-owned closed set.
aisoft_label_is_managed_namespace() {
  local name="$1" managed
  for managed in "${AISOFT_LABEL_MANAGED_PREFIXES[@]}"; do
    if [[ "$name" == "$managed"* ]]; then
      return 0
    fi
  done
  return 1
}

# aisoft_label_source_manifest_lib <tool_dir>
# Dual-path locator matching the gitea-token.sh convention (#111): the flat VM
# install layout keeps every library beside the tool, the repository layout
# keeps them under codex/agent/.
aisoft_label_manifest_lib_path() {
  local tool_dir="$1"
  if [[ -f "$tool_dir/gitea-label-manifest.sh" ]]; then
    printf '%s\n' "$tool_dir/gitea-label-manifest.sh"
    return 0
  fi
  if [[ -f "$tool_dir/../agent/gitea-label-manifest.sh" ]]; then
    printf '%s\n' "$tool_dir/../agent/gitea-label-manifest.sh"
    return 0
  fi
  return 1
}
