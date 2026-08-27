#!/usr/bin/env bash
# Deterministic NewEMaint routine pilot rollback. This tool has no generic
# username, repository, token-id, URL, or purge surface.
set -euo pipefail
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
manifest=''
access_manifest=''
platform_root=''
merged_sha=''
rollout_sha=''
snapshot=''
account_policy=retain

usage() {
  printf '%s\n' \
    "usage: $0 --manifest FILE --access-manifest FILE --platform-root DIR --merged-sha SHA --rollout-sha SHA --snapshot FILE [--account-policy retain|delete]" >&2
  exit 2
}

render_rollback_marker() {
  case "$1" in
    account)
      printf 'issue=213\nusername=newemaint-routine-merger\n'
      ;;
    password-policy)
      printf 'issue=213\nusername=newemaint-routine-merger\npolicy=must-change-password-unset\n'
      ;;
    token)
      printf 'issue=213\nusername=newemaint-routine-merger\ntoken_kind=routine-merge-agent\n'
      ;;
    *)
      printf '%s\n' 'BLOCKED_EXTERNAL: unknown rollback marker kind' >&2
      return 2
      ;;
  esac
}

validate_rollback_marker() {
  local marker_path="$1"
  local marker_label="$2"
  local marker_kind="$3"
  local marker_mode

  [[ -f "$marker_path" && ! -L "$marker_path" ]] || {
    printf 'BLOCKED_EXTERNAL: %s marker must be a non-symlink regular file\n' \
      "$marker_label" >&2
    exit 2
  }
  marker_mode="$(stat -c '%a' "$marker_path" 2>/dev/null || stat -f '%Lp' "$marker_path")"
  [[ "$marker_mode" == 600 || "$marker_mode" == 400 ]] || {
    printf 'BLOCKED_EXTERNAL: %s marker mode must be 400 or 600\n' \
      "$marker_label" >&2
    exit 2
  }
  if ! render_rollback_marker "$marker_kind" | cmp -s "$marker_path" -; then
    printf 'BLOCKED_EXTERNAL: %s marker content mismatch\n' "$marker_label" >&2
    exit 2
  fi
}

validate_non_admin_identity() {
  local identity_path="$1"
  local expected_login="$2"
  local identity_label="$3"

  jq -e --arg login "$expected_login" '
    type == "object"
    and (.login | type) == "string"
    and .login == $login
    and (.is_admin | type) == "boolean"
    and .is_admin == false
  ' "$identity_path" >/dev/null || {
    printf 'BLOCKED_EXTERNAL: %s must be the exact non-admin service identity\n' \
      "$identity_label" >&2
    exit 2
  }
}

while (($#)); do
  case "$1" in
    --manifest) manifest="${2:-}"; shift 2 ;;
    --access-manifest) access_manifest="${2:-}"; shift 2 ;;
    --platform-root) platform_root="${2:-}"; shift 2 ;;
    --merged-sha) merged_sha="${2:-}"; shift 2 ;;
    --rollout-sha) rollout_sha="${2:-}"; shift 2 ;;
    --snapshot) snapshot="${2:-}"; shift 2 ;;
    --account-policy) account_policy="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$manifest" && -n "$access_manifest" && -n "$platform_root" &&
   -n "$merged_sha" && -n "$rollout_sha" && -n "$snapshot" ]] || usage
[[ "$account_policy" == retain || "$account_policy" == delete ]] || usage
[[ "${AISOFT_ROUTINE_ROLLBACK_MODE:-}" == approved-issue-213 ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: AISOFT_ROUTINE_ROLLBACK_MODE=approved-issue-213 is required' >&2
  exit 2
}

for command in python3 jq curl sudo git install mktemp cmp; do
  command -v "$command" >/dev/null || {
    printf 'BLOCKED_EXTERNAL: required command is missing: %s\n' "$command" >&2
    exit 2
  }
done

GITEA_BIN="${GITEA_BIN:-/usr/local/bin/gitea}"
GITEA_CONFIG="${GITEA_CONFIG:-/etc/gitea/app.ini}"
GITEA_LOCAL_URL="${GITEA_LOCAL_URL:-http://127.0.0.1:3000}"
credential_root="${AISOFT_CREDENTIAL_ROOT:-/home/benque/.config/aisoft/credentials}"
if [[ -d "$ROOT/codex/runtime" ]]; then
  export PYTHONPATH="$ROOT/codex/runtime${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="/usr/local/lib/aisoft-host-access${PYTHONPATH:+:$PYTHONPATH}"
fi

[[ "$GITEA_LOCAL_URL" == http://127.0.0.1:* ||
   "$GITEA_LOCAL_URL" == https://127.0.0.1:* ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: GITEA_LOCAL_URL must use loopback' >&2
  exit 2
}
[[ -x "$GITEA_BIN" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: Gitea binary is unavailable to the caller' >&2
  exit 2
}
if ! sudo -n -u git test -f "$GITEA_CONFIG" ||
   ! sudo -n -u git test -r "$GITEA_CONFIG"; then
  printf '%s\n' 'BLOCKED_EXTERNAL: Gitea config is unavailable to the service user' >&2
  exit 2
fi

python3 -m aisoft_host_access.cli \
  --access-manifest "$access_manifest" \
  --governance-manifest "$manifest" validate >/dev/null || exit 2

binding="$(jq -cer '
  [.projects[] | select(.project_id == "newemaint")]
  | if length == 1 and .[0].repository == "NewEMaint"
       and .[0].routine_merge_agent == "newemaint-routine-merger"
    then .[0] else error("NewEMaint binding mismatch") end
' "$access_manifest")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: exact NewEMaint rollback binding is unavailable' >&2
  exit 2
}
[[ -n "$binding" ]]

pilot="$(jq -cer '
  [.repositories[] | select(.name == "NewEMaint")]
  | if length == 1
       and .[0].routine_auto_merge_enabled == false
       and .[0].routine_merge_agent == "newemaint-routine-merger"
       and .[0].routine_live_pilot.project_id == "newemaint"
       and .[0].routine_live_pilot.rollout_issue == 213
       and .[0].routine_live_pilot.canary_issue == 74
    then .[0].routine_live_pilot
    else error("pilot source is not disabled") end
' "$manifest")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: merged source must disable the exact NewEMaint pilot first' >&2
  exit 2
}

python3 -m aisoft_gitea_governance.cli --manifest "$manifest" verify-merged \
  --repository NewEMaint --issue 213 --merged-sha "$merged_sha" \
  --platform-root "$platform_root" >/dev/null || exit 2
git -C "$platform_root" merge-base --is-ancestor "$rollout_sha" "$merged_sha" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: rollout SHA is not an ancestor of disabled source SHA' >&2
  exit 2
}

tmp_dir="$(mktemp -d)"
chmod 700 "$tmp_dir"
trap 'rm -rf -- "$tmp_dir"' EXIT
umask 077
git -C "$platform_root" show \
  "$rollout_sha:codex/config/gitea-governance.json" >"$tmp_dir/rollout-manifest.json" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: rollout manifest is unavailable at the exact SHA' >&2
  exit 2
}
rollout_pilot="$(jq -cer '
  [.repositories[] | select(.name == "NewEMaint")]
  | if length == 1 and .[0].routine_auto_merge_enabled == true
    then .[0].routine_live_pilot else error("rollout pilot was not enabled") end
' "$tmp_dir/rollout-manifest.json")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: rollout SHA does not contain the enabled pilot' >&2
  exit 2
}
[[ "$rollout_pilot" == "$pilot" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: disabled source changed immutable pilot metadata' >&2
  exit 2
}

manager_token="$credential_root/manager/mutation.token"
credential_file="$credential_root/projects/newemaint/routine-merge-agent.token"
token_marker="$credential_file-created-by-issue-213"
marker_root="$credential_root/projects/newemaint"
account_marker="$marker_root/newemaint-routine-merger.account-created-by-issue-213"
password_marker="$marker_root/newemaint-routine-merger.must-change-password-unset-by-issue-213"
for path in "$manager_token" "$credential_file"; do
  [[ -f "$path" && ! -L "$path" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: exact managed rollback file is missing or unsafe' >&2
    exit 2
  }
done
validate_rollback_marker "$token_marker" 'token ownership' token
validate_rollback_marker "$account_marker" 'account ownership' account
if [[ "$account_policy" == delete ]]; then
  validate_rollback_marker "$password_marker" 'password-policy ownership' password-policy
fi

# Identity is a pre-mutation hard gate: unsafe account data must stop before
# repository rollback, PAT revoke, credential removal, or account deletion.
account_file="$tmp_dir/account.json"
account_status="$(curl --silent --show-error --output "$account_file" \
  --write-out '%{http_code}' "$GITEA_LOCAL_URL/api/v1/users/newemaint-routine-merger")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: routine account preflight read-back failed' >&2
  exit 2
}
[[ "$account_status" == 200 ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: exact managed routine account is missing' >&2
  exit 2
}
validate_non_admin_identity "$account_file" newemaint-routine-merger \
  'routine account preflight read-back'

rollback_receipt="$(AISOFT_ROUTINE_LIVE_MODE=approved-issue-213-rollback \
  python3 -m aisoft_gitea_governance.cli --manifest "$manifest" rollback \
  --token-file "$manager_token" --repository NewEMaint --issue 213 \
  --merged-sha "$merged_sha" --platform-root "$platform_root" \
  --snapshot "$snapshot")" || exit 2
[[ "$(jq -r '.result' <<<"$rollback_receipt")" == rollback-applied ]] || exit 2

check_file="$tmp_dir/check.json"
python3 -m aisoft_gitea_governance.cli --manifest "$manifest" check \
  --token-file "$manager_token" --repository NewEMaint >"$check_file" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: human-only repository rollback read-back failed' >&2
  exit 2
}
jq -e '
  .result == "PASS"
  and .cross_project_write_violations == []
  and (.repositories | length == 1)
  and .repositories[0].planned_actions == []
  and .repositories[0].blockers == []
  and .repositories[0].expected.routine_auto_merge_enabled == false
  and .repositories[0].expected.merge_allowlist_usernames == ["admin"]
  and .repositories[0].current.collaborators["newemaint-routine-merger"] == "missing"
  and .repositories[0].current.protection.merge_whitelist_usernames == ["admin"]
  and (.routine_accounts | length == 1)
  and .routine_accounts[0].state == "present-non-admin"
' "$check_file" >/dev/null || {
  printf '%s\n' 'BLOCKED_EXTERNAL: rollback read-back is incomplete or unsafe' >&2
  exit 2
}

mode="$(stat -c '%a' "$credential_file" 2>/dev/null || stat -f '%Lp' "$credential_file")"
[[ "$mode" == 600 || "$mode" == 400 ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: routine credential mode must be 400 or 600' >&2
  exit 2
}
token="$(tr -d '\r\n' <"$credential_file")"
[[ "$token" =~ ^[A-Za-z0-9._-]+$ ]] || {
  unset token
  printf '%s\n' 'BLOCKED_EXTERNAL: routine credential format is invalid' >&2
  exit 2
}
revoke_status="$(printf 'header = "Authorization: token %s"\nrequest = "DELETE"\n' "$token" |
  curl --config - --silent --show-error --output /dev/null --write-out '%{http_code}' \
    "$GITEA_LOCAL_URL/api/v1/token")" || {
  unset token
  printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT self-revoke failed' >&2
  exit 2
}
[[ "$revoke_status" == 204 ]] || {
  unset token
  printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT self-revoke did not return 204' >&2
  exit 2
}
revoked_readback="$(printf 'header = "Authorization: token %s"\n' "$token" |
  curl --config - --silent --show-error --output /dev/null --write-out '%{http_code}' \
    "$GITEA_LOCAL_URL/api/v1/user")" || revoked_readback='transport-error'
unset token
[[ "$revoked_readback" == 401 ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: revoked PAT did not read back as 401' >&2
  exit 2
}
rm -f -- "$credential_file" "$token_marker"

account_status="$(curl --silent --show-error --output "$account_file" \
  --write-out '%{http_code}' "$GITEA_LOCAL_URL/api/v1/users/newemaint-routine-merger")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: routine account read-back failed' >&2
  exit 2
}
account_delete_mutation_count=0
if [[ "$account_policy" == retain ]]; then
  [[ "$account_status" == 200 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: retained account is missing' >&2
    exit 2
  }
  validate_non_admin_identity "$account_file" newemaint-routine-merger \
    'retained account read-back'
  account_state=present-non-admin
else
  [[ "$account_status" == 200 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: exact managed account is missing before delete' >&2
    exit 2
  }
  validate_non_admin_identity "$account_file" newemaint-routine-merger \
    'delete account read-back'
  # The mode 700 caller-owned temp directory intentionally receives stdout;
  # sudo is only for the Gitea database operation, not the redirection.
  validate_non_admin_identity "$account_file" newemaint-routine-merger \
    'immediate pre-delete account read-back'
  # shellcheck disable=SC2024
  sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user delete \
    --username newemaint-routine-merger >"$tmp_dir/account-delete.log"
  account_delete_mutation_count=1
  account_status="$(curl --silent --show-error --output /dev/null \
    --write-out '%{http_code}' "$GITEA_LOCAL_URL/api/v1/users/newemaint-routine-merger")"
  [[ "$account_status" == 404 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: deleted account did not read back as 404' >&2
    exit 2
  }
  rm -f -- "$account_marker" "$password_marker"
  account_state=missing
fi

jq -cn --arg policy "$account_policy" --arg account_state "$account_state" \
  --arg rollout_sha "$rollout_sha" --arg merged_sha "$merged_sha" \
  --argjson account_delete_count "$account_delete_mutation_count" \
  '{result:"rollback-accepted",repository:"admin/NewEMaint",project_id:"newemaint",
    rollout_issue:213,rollout_sha:$rollout_sha,disabled_source_sha:$merged_sha,
    repository_rollback_operation_count:1,revoke_mutation_count:1,
    revoked_pat_readback_http:401,account_policy:$policy,account_state:$account_state,
    account_delete_mutation_count:$account_delete_count,fallback_count:0,
    deploy_count:0,merge_post_count:0}'
