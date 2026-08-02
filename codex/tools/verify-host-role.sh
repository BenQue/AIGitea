#!/usr/bin/env bash
# Fail-closed host-role decision point. This tool never executes the requested action.
set -euo pipefail

PROFILE_PATH=/etc/aisoft/host-profile.json
SCHEMA_PATH=/usr/local/share/aisoft/host-role.schema.json
CATALOG_PATH=/usr/local/share/aisoft/host-capabilities.json
MACHINE_ID_PATH=/etc/machine-id

EXIT_ALLOWED=0
EXIT_DENIED=20
EXIT_INVALID_PROFILE=30
EXIT_IDENTITY_MISMATCH=40
EXIT_USAGE=64

usage() {
  cat <<'EOF'
Usage: verify-host-role --action ACTION --resource RESOURCE

Exit codes:
  0   allowed
  20  denied by the role capability allowlist
  30  invalid request, profile, schema, catalog, ownership or permissions
  40  hostname or machine identity mismatch
  64  command-line usage error

The production profile path is fixed at /etc/aisoft/host-profile.json.
This command only returns a decision; it never runs a mutation.
EOF
}

invalid_result() {
  printf 'decision=invalid-profile reason=%s\n' "$1" >&2
  return "$EXIT_INVALID_PROFILE"
}

identity_result() {
  printf 'decision=identity-mismatch reason=%s\n' "$1" >&2
  return "$EXIT_IDENTITY_MISMATCH"
}

path_uid_mode() {
  local target="$1"
  if stat -c '%u %a' "$target" >/dev/null 2>&1; then
    stat -c '%u %a' "$target"
    return
  fi
  stat -f '%u %Lp' "$target"
}

read_actual_hostname() {
  hostname -s
}

read_actual_host_id() {
  tr -d '[:space:]' <"$MACHINE_ID_PATH" | tr '[:upper:]' '[:lower:]'
}

mode_is_not_writable_by_group_or_other() {
  local mode="$1"
  [[ "$mode" =~ ^[0-7]{3}$ ]] || return 1
  case "${mode:1:1}" in 2|3|6|7) return 1 ;; esac
  case "${mode:2:1}" in 2|3|6|7) return 1 ;; esac
  return 0
}

secure_contract_path() {
  local target="$1"
  local kind="$2"
  local metadata owner_uid mode parent metadata_parent parent_uid parent_mode

  [[ -f "$target" && ! -L "$target" ]] || return 1
  metadata="$(path_uid_mode "$target")" || return 1
  owner_uid="${metadata%% *}"
  mode="${metadata##* }"
  [[ "$owner_uid" == 0 ]] || return 1

  if [[ "$kind" == profile ]]; then
    case "$mode" in 400|440|600|640) ;; *) return 1 ;; esac
  else
    case "$mode" in 400|440|444|600|640|644) ;; *) return 1 ;; esac
  fi

  parent="$(dirname -- "$target")"
  metadata_parent="$(path_uid_mode "$parent")" || return 1
  parent_uid="${metadata_parent%% *}"
  parent_mode="${metadata_parent##* }"
  [[ "$parent_uid" == 0 ]] || return 1
  mode_is_not_writable_by_group_or_other "$parent_mode"
}

catalog_is_valid() {
  jq -e '
    . as $catalog |
    type == "object" and
    ((keys | sort) == ["capabilities", "contract_version", "roles"]) and
    (.contract_version | type == "string" and length > 0) and
    (.capabilities | type == "object" and length > 0) and
    (.roles | type == "object" and length == 3) and
    ((.roles | keys | sort) == ["appserver-prod", "appserver-test", "scm-ci"]) and
    all($catalog.capabilities[];
      type == "object" and
      ((keys | sort) == ["action", "description", "mutation", "resource"]) and
      (.action | type == "string" and test("^[a-z][a-z0-9-]*$")) and
      (.resource | type == "string" and test("^[a-z][a-z0-9-]*$")) and
      (.mutation | type == "boolean") and
      (.description | type == "string" and length > 0)
    ) and
    ([ $catalog.capabilities[] | [.action, .resource] ] | unique | length) ==
      ($catalog.capabilities | length) and
    all($catalog.roles[];
      type == "object" and
      ((keys | sort) == ["allowed_capabilities", "description", "environment"]) and
      (.environment | type == "string" and length > 0) and
      (.description | type == "string" and length > 0) and
      (.allowed_capabilities | type == "array" and length > 0 and
        (unique | length) == length) and
      all(.allowed_capabilities[]; $catalog.capabilities[.] != null)
    )
  ' "$CATALOG_PATH" >/dev/null
}

schema_is_valid() {
  jq -e '
    type == "object" and
    .["$schema"] == "https://json-schema.org/draft/2020-12/schema" and
    (.additionalProperties == false) and
    (.required | sort) == [
      "allowed_capabilities",
      "contract_version",
      "host_id",
      "hostname",
      "managed_by",
      "profile_revision",
      "role"
    ] and
    (.properties.contract_version.const | type == "string") and
    (.properties.managed_by.const == "aisoft-platform") and
    (.properties.role.enum | sort) == ["appserver-prod", "appserver-test", "scm-ci"]
  ' "$SCHEMA_PATH" >/dev/null
}

profile_shape_is_valid() {
  local contract_version="$1"
  jq -e --arg contract_version "$contract_version" '
    type == "object" and
    ((keys | sort) == [
      "allowed_capabilities",
      "contract_version",
      "host_id",
      "hostname",
      "managed_by",
      "profile_revision",
      "role"
    ]) and
    (.contract_version == $contract_version) and
    (.host_id | type == "string" and test("^[0-9a-f]{32}$")) and
    (.hostname | type == "string" and length >= 1 and length <= 253 and
      test("^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")) and
    (.role | type == "string") and
    (.allowed_capabilities | type == "array" and length > 0 and
      all(.[]; type == "string" and test("^[a-z][a-z0-9-]*\\.[a-z][a-z0-9-]*$")) and
      (unique | length) == length) and
    (.profile_revision | type == "number" and floor == . and . >= 1) and
    (.managed_by == "aisoft-platform")
  ' "$PROFILE_PATH" >/dev/null
}

verify_host_role_main() {
  local action='' resource='' contract_version schema_version role
  local profile_capabilities role_capabilities expected_hostname expected_host_id
  local actual_hostname actual_host_id capability

  PATH=/usr/sbin:/usr/bin:/sbin:/bin
  export PATH
  LC_ALL=C
  export LC_ALL

  while (($#)); do
    case "$1" in
      --action)
        [[ $# -ge 2 ]] || { usage >&2; return "$EXIT_USAGE"; }
        action="$2"
        shift 2
        ;;
      --resource)
        [[ $# -ge 2 ]] || { usage >&2; return "$EXIT_USAGE"; }
        resource="$2"
        shift 2
        ;;
      -h|--help)
        usage
        return 0
        ;;
      *)
        usage >&2
        return "$EXIT_USAGE"
        ;;
    esac
  done

  [[ -n "$action" && -n "$resource" ]] || {
    usage >&2
    return "$EXIT_USAGE"
  }
  [[ "$action" =~ ^[a-z][a-z0-9-]*$ &&
    "$resource" =~ ^[a-z][a-z0-9-]*$ ]] || {
    invalid_result 'invalid-action-or-resource-syntax'
    return "$EXIT_INVALID_PROFILE"
  }
  command -v jq >/dev/null 2>&1 || {
    invalid_result 'jq-unavailable'
    return "$EXIT_INVALID_PROFILE"
  }

  secure_contract_path "$PROFILE_PATH" profile || {
    invalid_result 'profile-path-owner-or-mode'
    return "$EXIT_INVALID_PROFILE"
  }
  secure_contract_path "$SCHEMA_PATH" contract || {
    invalid_result 'schema-path-owner-or-mode'
    return "$EXIT_INVALID_PROFILE"
  }
  secure_contract_path "$CATALOG_PATH" contract || {
    invalid_result 'catalog-path-owner-or-mode'
    return "$EXIT_INVALID_PROFILE"
  }
  jq empty "$PROFILE_PATH" "$SCHEMA_PATH" "$CATALOG_PATH" >/dev/null 2>&1 || {
    invalid_result 'invalid-json'
    return "$EXIT_INVALID_PROFILE"
  }
  schema_is_valid || {
    invalid_result 'invalid-schema-contract'
    return "$EXIT_INVALID_PROFILE"
  }
  catalog_is_valid || {
    invalid_result 'invalid-capability-catalog'
    return "$EXIT_INVALID_PROFILE"
  }

  contract_version="$(jq -r '.contract_version' "$CATALOG_PATH")"
  schema_version="$(jq -r '.properties.contract_version.const' "$SCHEMA_PATH")"
  [[ "$contract_version" == "$schema_version" ]] || {
    invalid_result 'contract-version-mismatch'
    return "$EXIT_INVALID_PROFILE"
  }
  profile_shape_is_valid "$contract_version" || {
    invalid_result 'profile-schema-mismatch'
    return "$EXIT_INVALID_PROFILE"
  }

  role="$(jq -r '.role' "$PROFILE_PATH")"
  jq -e --arg role "$role" '.roles[$role] != null' "$CATALOG_PATH" >/dev/null || {
    invalid_result 'unknown-role'
    return "$EXIT_INVALID_PROFILE"
  }
  profile_capabilities="$(jq -c '.allowed_capabilities | sort' "$PROFILE_PATH")"
  role_capabilities="$(jq -c --arg role "$role" '.roles[$role].allowed_capabilities | sort' "$CATALOG_PATH")"
  [[ "$profile_capabilities" == "$role_capabilities" ]] || {
    invalid_result 'role-capability-set-mismatch'
    return "$EXIT_INVALID_PROFILE"
  }

  expected_hostname="$(jq -r '.hostname' "$PROFILE_PATH")"
  expected_host_id="$(jq -r '.host_id' "$PROFILE_PATH")"
  actual_hostname="$(read_actual_hostname 2>/dev/null || true)"
  actual_host_id="$(read_actual_host_id 2>/dev/null || true)"
  [[ -n "$actual_hostname" && -n "$actual_host_id" ]] || {
    identity_result 'identity-read-failed'
    return "$EXIT_IDENTITY_MISMATCH"
  }
  [[ "$actual_hostname" == "$expected_hostname" ]] || {
    identity_result 'hostname-mismatch'
    return "$EXIT_IDENTITY_MISMATCH"
  }
  [[ "$actual_host_id" == "$expected_host_id" ]] || {
    identity_result 'machine-id-mismatch'
    return "$EXIT_IDENTITY_MISMATCH"
  }

  capability="$(
    jq -r --arg action "$action" --arg resource "$resource" '
      [
        .capabilities | to_entries[] |
        select(.value.action == $action and .value.resource == $resource) |
        .key
      ] |
      if length == 1 then .[0] else empty end
    ' "$CATALOG_PATH"
  )"
  [[ -n "$capability" ]] || {
    invalid_result 'unknown-action-resource-pair'
    return "$EXIT_INVALID_PROFILE"
  }

  if jq -e --arg capability "$capability" \
    '.allowed_capabilities | index($capability) != null' \
    "$PROFILE_PATH" >/dev/null; then
    printf 'decision=allow host=%s role=%s action=%s resource=%s\n' \
      "$expected_hostname" "$role" "$action" "$resource"
    return "$EXIT_ALLOWED"
  fi

  printf 'decision=deny host=%s role=%s action=%s resource=%s\n' \
    "$expected_hostname" "$role" "$action" "$resource" >&2
  return "$EXIT_DENIED"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  verify_host_role_main "$@"
fi
