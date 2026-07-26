#!/usr/bin/env bash
set -euo pipefail

# Never inherit xtrace across profile or credential loading. Tokens are sent to
# curl through stdin configuration and never appear in argv or command output.
set +x

mode=apply
case "${1:-}" in
  '')
    ;;
  --check)
    mode=check
    ;;
  *)
    printf 'usage: %s [--check]\n' "$0" >&2
    exit 2
    ;;
esac

collaborator="${GITEA_COLLABORATOR:-ci-bot}"
env_file="${AGENT_ENV_FILE:-}"
default_credential_file="/home/benque/gitea-ci-credentials.txt"
admin_credential_file="${GITEA_ADMIN_CREDENTIAL_FILE:-$default_credential_file}"
bot_credential_file="${GITEA_BOT_CREDENTIAL_FILE:-"$admin_credential_file"}"

blocked() {
  printf 'BLOCKED_EXTERNAL: %s\n' "$1" >&2
  exit 1
}

secure_mode() {
  local path="$1"
  local mode_value
  [[ -f "$path" ]] || blocked "required credential or profile file is missing"
  if ! mode_value="$(stat -c '%a' "$path" 2>/dev/null)"; then
    mode_value="$(stat -f '%Lp' "$path" 2>/dev/null)" ||
      blocked "cannot read credential or profile file mode"
  fi
  case "$mode_value" in
    400|600) ;;
    *) blocked "credential or profile file must have mode 400 or 600" ;;
  esac
}

read_role_token() {
  local path="$1"
  local role="$2"
  local token_value

  secure_mode "$path"
  token_value="$(
    awk -v role="$role" '
      role == "admin" && /^admin token:[[:space:]]*/ {
        print $NF
        found = 1
        exit
      }
      role == "ci-bot" && /^ci-bot token:[[:space:]]*/ {
        print $NF
        found = 1
        exit
      }
      END {
        if (!found) {
          exit 1
        }
      }
    ' "$path"
  )" || true

  if [[ -z "$token_value" ]]; then
    token_value="$(
      awk '
        NF == 1 && $1 ~ /^[A-Za-z0-9._-]+$/ {
          value = $1
          count += 1
        }
        END {
          if (count == 1) {
            print value
          } else {
            exit 1
          }
        }
      ' "$path"
    )" || true
  fi

  [[ -n "$token_value" ]] ||
    blocked "required credential role is unavailable"
  [[ "$token_value" =~ ^[A-Za-z0-9._-]+$ ]] ||
    blocked "credential contains unsafe characters"
  printf '%s' "$token_value"
}

if [[ -n "$env_file" ]]; then
  secure_mode "$env_file"
  # The explicitly selected profile is trusted configuration. Suppress any
  # accidental output so only sanitized summaries leave this tool.
  # shellcheck disable=SC1090
  source "$env_file" >/dev/null 2>&1
  set +x
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO \
  GITEA_EXPECT_URL GITEA_EXPECT_OWNER GITEA_EXPECT_REPO; do
  [[ -n "${!name:-}" ]] || blocked "$name is required"
done

[[ "$collaborator" == "ci-bot" ]] ||
  blocked "only the managed ci-bot collaborator is allowed"
[[ "$GITEA_OWNER" =~ ^[A-Za-z0-9._-]+$ ]] ||
  blocked "GITEA_OWNER contains unsafe characters"
[[ "$GITEA_REPO" =~ ^[A-Za-z0-9._-]+$ ]] ||
  blocked "GITEA_REPO contains unsafe characters"
case "$GITEA_URL" in
  http://*|https://*) ;;
  *) blocked "GITEA_URL must use http or https" ;;
esac
[[ "$GITEA_URL" != *"@"* ]] ||
  blocked "GITEA_URL must not contain embedded credentials"
[[ "${GITEA_URL%/}" == "${GITEA_EXPECT_URL%/}" ]] ||
  blocked "selected profile URL does not match the expected target"
[[ "$GITEA_OWNER" == "$GITEA_EXPECT_OWNER" ]] ||
  blocked "selected profile owner does not match the expected target"
[[ "$GITEA_REPO" == "$GITEA_EXPECT_REPO" ]] ||
  blocked "selected profile repository does not match the expected target"

if [[ "$mode" == apply &&
  "${AISOFT_ONBOARDING_MODE:-}" != "software-repository" ]]; then
  blocked "AISOFT_ONBOARDING_MODE=software-repository is required"
fi

command -v curl >/dev/null || blocked "curl is required"
command -v jq >/dev/null || blocked "jq is required"

admin_token="${GITEA_ADMIN_TOKEN:-}"
if [[ -z "$admin_token" ]]; then
  admin_token="$(read_role_token "$admin_credential_file" admin)"
fi
[[ "$admin_token" =~ ^[A-Za-z0-9._-]+$ ]] ||
  blocked "administrator credential contains unsafe characters"

bot_token=''
if [[ "$mode" == apply ]]; then
  bot_token="${GITEA_BOT_TOKEN:-${GITEA_TOKEN:-}}"
  if [[ -z "$bot_token" ]]; then
    bot_token="$(read_role_token "$bot_credential_file" ci-bot)"
  fi
  [[ "$bot_token" =~ ^[A-Za-z0-9._-]+$ ]] ||
    blocked "ci-bot credential contains unsafe characters"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "$tmp_dir"' EXIT
api="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"

api_request() {
  local token_value="$1"
  local method="$2"
  local endpoint="$3"
  local output_file="$4"
  local payload="${5:-}"

  if [[ -n "$payload" ]]; then
    printf 'header = "Authorization: token %s"\n' "$token_value" |
      curl --config - --silent --show-error \
        --output "$output_file" --write-out '%{http_code}' \
        --request "$method" --header 'Content-Type: application/json' \
        --data "$payload" "$endpoint"
  else
    printf 'header = "Authorization: token %s"\n' "$token_value" |
      curl --config - --silent --show-error \
        --output "$output_file" --write-out '%{http_code}' \
        --request "$method" "$endpoint"
  fi
}

require_status() {
  local actual="$1"
  local expected="$2"
  local operation="$3"
  [[ "$actual" == "$expected" ]] ||
    blocked "$operation failed with HTTP $actual"
}

permission_with_admin() {
  local output_file="$1"
  local status
  local permission_value

  status="$(
    api_request "$admin_token" GET \
      "$api/collaborators/$collaborator/permission" "$output_file"
  )" || blocked "collaborator permission read failed"
  case "$status" in
    200)
      permission_value="$(jq -er '.permission' "$output_file" 2>/dev/null)" ||
        blocked "collaborator permission response is invalid"
      printf '%s' "$permission_value"
      ;;
    404)
      printf 'missing'
      ;;
    *)
      blocked "collaborator permission read failed with HTTP $status"
      ;;
  esac
}

normalize_protection() {
  local input_file="$1"
  jq -ceS '
    {
      rule_name,
      branch_name,
      enable_push,
      enable_push_whitelist,
      push_whitelist_deploy_keys,
      push_whitelist_usernames: ((.push_whitelist_usernames // []) | sort),
      push_whitelist_teams: ((.push_whitelist_teams // []) | sort),
      enable_force_push,
      enable_force_push_allowlist,
      force_push_allowlist_deploy_keys,
      force_push_allowlist_usernames:
        ((.force_push_allowlist_usernames // []) | sort),
      force_push_allowlist_teams:
        ((.force_push_allowlist_teams // []) | sort),
      enable_status_check,
      status_check_contexts: ((.status_check_contexts // []) | sort),
      required_approvals,
      dismiss_stale_approvals,
      ignore_stale_approvals,
      block_on_rejected_reviews,
      block_on_outdated_branch,
      block_on_official_review_requests,
      enable_approvals_whitelist,
      approvals_whitelist_username:
        ((.approvals_whitelist_username // []) | sort),
      approvals_whitelist_teams:
        ((.approvals_whitelist_teams // []) | sort),
      enable_merge_whitelist,
      merge_whitelist_usernames:
        ((.merge_whitelist_usernames // []) | sort),
      merge_whitelist_teams: ((.merge_whitelist_teams // []) | sort),
      block_admin_merge_override,
      require_signed_commits,
      protected_file_patterns,
      unprotected_file_patterns
    }
  ' "$input_file" 2>/dev/null ||
    blocked "main branch protection response is invalid"
}

protection_contract_ok() {
  local input_file="$1"
  jq -e --arg collaborator "$collaborator" '
    (.rule_name == "main" or .branch_name == "main") and
    (.enable_push == false) and
    (.enable_force_push == false) and
    (.enable_merge_whitelist == true) and
    (((.push_whitelist_usernames // []) | index($collaborator)) == null) and
    (((.force_push_allowlist_usernames // []) | index($collaborator)) == null) and
    (((.merge_whitelist_usernames // []) | index($collaborator)) == null)
  ' "$input_file" >/dev/null 2>&1
}

repo_before="$tmp_dir/repo-before.json"
status="$(
  api_request "$admin_token" GET "$api" "$repo_before"
)" || blocked "repository read failed"
require_status "$status" 200 "repository read"
default_branch="$(jq -er '.default_branch' "$repo_before" 2>/dev/null)" ||
  blocked "repository response is invalid"
[[ "$default_branch" == "main" ]] ||
  blocked "repository default branch is not main"

protection_before_file="$tmp_dir/protection-before.json"
status="$(
  api_request "$admin_token" GET \
    "$api/branch_protections/main" "$protection_before_file"
)" || blocked "main branch protection read failed"
case "$status" in
  200)
    if protection_contract_ok "$protection_before_file"; then
      protection_state=verified
    else
      protection_state=blocked
    fi
    protection_before="$(normalize_protection "$protection_before_file")"
    ;;
  404)
    protection_state=missing
    protection_before=''
    ;;
  *)
    blocked "main branch protection read failed with HTTP $status"
    ;;
esac

permission_before_file="$tmp_dir/permission-before.json"
permission_before="$(permission_with_admin "$permission_before_file")"
case "$permission_before" in
  missing) planned_action=add-write ;;
  read) planned_action=update-write ;;
  write) planned_action=none ;;
  admin) planned_action=manual-downgrade ;;
  *) planned_action=manual-review ;;
esac

if [[ "$mode" == check ]]; then
  if [[ "$protection_state" == verified ]]; then
    gate_state=ready
  else
    gate_state=blocked
  fi
  printf \
    'repository=%s/%s collaborator=%s current_permission=%s planned_action=%s main_protection=%s onboarding_gate=%s mode=check\n' \
    "$GITEA_OWNER" "$GITEA_REPO" "$collaborator" "$permission_before" \
    "$planned_action" "$protection_state" "$gate_state"
  exit 0
fi

[[ "$protection_state" == verified ]] ||
  blocked "main branch protection does not enforce the ci-bot safety boundary"

case "$permission_before" in
  missing|read)
    payload='{"permission":"write"}'
    put_output="$tmp_dir/permission-put.json"
    status="$(
      api_request "$admin_token" PUT \
        "$api/collaborators/$collaborator" "$put_output" "$payload"
    )" || blocked "collaborator write configuration failed"
    require_status "$status" 204 "collaborator write configuration"
    if [[ "$permission_before" == missing ]]; then
      action=added
    else
      action=updated
    fi
    ;;
  write)
    action=unchanged
    ;;
  admin)
    blocked "ci-bot has admin permission; manual downgrade is required"
    ;;
  *)
    blocked "ci-bot has an unknown permission level"
    ;;
esac

permission_after_file="$tmp_dir/permission-after.json"
permission_after="$(permission_with_admin "$permission_after_file")"
[[ "$permission_after" == write ]] ||
  blocked "collaborator permission read-back did not return write"

protection_after_file="$tmp_dir/protection-after.json"
status="$(
  api_request "$admin_token" GET \
    "$api/branch_protections/main" "$protection_after_file"
)" || blocked "main branch protection read-back failed"
require_status "$status" 200 "main branch protection read-back"
protection_contract_ok "$protection_after_file" ||
  blocked "main branch protection does not enforce the ci-bot safety boundary"
protection_after="$(normalize_protection "$protection_after_file")"
[[ "$protection_after" == "$protection_before" ]] ||
  blocked "main branch protection changed during collaborator configuration"

bot_repo_file="$tmp_dir/bot-repo.json"
status="$(
  api_request "$bot_token" GET "$api" "$bot_repo_file"
)" || blocked "ci-bot repository access failed"
require_status "$status" 200 "ci-bot repository access"
bot_full_name="$(jq -er '.full_name' "$bot_repo_file" 2>/dev/null)" ||
  blocked "ci-bot repository response is invalid"
[[ "$bot_full_name" == "$GITEA_OWNER/$GITEA_REPO" ]] ||
  blocked "ci-bot repository response target mismatch"

bot_permission_file="$tmp_dir/bot-permission.json"
status="$(
  api_request "$bot_token" GET \
    "$api/collaborators/$collaborator/permission" "$bot_permission_file"
)" || blocked "ci-bot permission read-back failed"
require_status "$status" 200 "ci-bot permission read-back"
bot_permission="$(jq -er '.permission' "$bot_permission_file" 2>/dev/null)" ||
  blocked "ci-bot permission response is invalid"
[[ "$bot_permission" == write ]] ||
  blocked "ci-bot permission read-back did not return write"

printf \
  'repository=%s/%s collaborator=%s permission=write action=%s main_protection=verified bot_access=verified\n' \
  "$GITEA_OWNER" "$GITEA_REPO" "$collaborator" "$action"
