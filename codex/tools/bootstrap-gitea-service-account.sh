#!/usr/bin/env bash
set -euo pipefail
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
manifest=''
access_manifest=''
project_id=''
username=''
token_kind=''
credential_output=''
merged_sha=''
platform_root=''

usage() {
  printf '%s\n' \
    "usage: $0 --manifest FILE [--access-manifest FILE --project-id ID --merged-sha SHA --platform-root DIR] --username NAME --token-kind manager-audit|manager-mutation|project-agent|routine-merge-agent --credential-output FILE" >&2
  exit 2
}

render_owned_marker() {
  case "$1" in
    account)
      printf 'issue=%s\nusername=%s\n' "$approval_issue" "$username"
      ;;
    password-policy)
      printf 'issue=%s\nusername=%s\npolicy=must-change-password-unset\n' \
        "$approval_issue" "$username"
      ;;
    token)
      printf 'issue=%s\nusername=%s\ntoken_kind=%s\n' \
        "$approval_issue" "$username" "$token_kind"
      ;;
    *)
      printf '%s\n' 'BLOCKED_EXTERNAL: unknown ownership marker kind' >&2
      return 2
      ;;
  esac
}

validate_owned_marker() {
  local marker_path="$1"
  local marker_label="$2"
  local marker_kind="$3"
  local marker_mode

  [[ -f "$marker_path" && ! -L "$marker_path" ]] || {
    printf 'BLOCKED_EXTERNAL: %s ownership marker must be a non-symlink regular file\n' "$marker_label" >&2
    exit 2
  }
  marker_mode="$(stat -c '%a' "$marker_path" 2>/dev/null || stat -f '%Lp' "$marker_path")"
  [[ "$marker_mode" == 600 || "$marker_mode" == 400 ]] || {
    printf 'BLOCKED_EXTERNAL: %s ownership marker mode must be 400 or 600\n' "$marker_label" >&2
    exit 2
  }
  if ! render_owned_marker "$marker_kind" | cmp -s "$marker_path" -; then
    printf 'BLOCKED_EXTERNAL: %s ownership marker content mismatch\n' "$marker_label" >&2
    exit 2
  fi
}

while (($#)); do
  case "$1" in
    --manifest) manifest="${2:-}"; shift 2 ;;
    --access-manifest) access_manifest="${2:-}"; shift 2 ;;
    --project-id) project_id="${2:-}"; shift 2 ;;
    --username) username="${2:-}"; shift 2 ;;
    --token-kind) token_kind="${2:-}"; shift 2 ;;
    --credential-output) credential_output="${2:-}"; shift 2 ;;
    --merged-sha) merged_sha="${2:-}"; shift 2 ;;
    --platform-root) platform_root="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$manifest" && -n "$username" && -n "$token_kind" && -n "$credential_output" ]] || usage
approval_issue=35
required_mode=approved-issue-35

for command in python3 jq curl sudo install mktemp cmp; do
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

[[ -x "$GITEA_BIN" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: Gitea binary is unavailable to the caller' >&2
  exit 2
}
if ! sudo -n -u git test -f "$GITEA_CONFIG" ||
   ! sudo -n -u git test -r "$GITEA_CONFIG"; then
  printf '%s\n' 'BLOCKED_EXTERNAL: Gitea config is unavailable to the service user' >&2
  exit 2
fi
[[ "$GITEA_LOCAL_URL" == http://127.0.0.1:* || "$GITEA_LOCAL_URL" == https://127.0.0.1:* ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: GITEA_LOCAL_URL must use loopback' >&2
  exit 2
}
[[ "$username" =~ ^[A-Za-z0-9._-]+$ ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: unsafe service account username' >&2
  exit 2
}

expected_basename="$username-$token_kind.token"
marker_root="$credential_root"
bound_repository=''
if [[ "$token_kind" == routine-merge-agent ]]; then
  [[ -n "$access_manifest" && -n "$project_id" && -n "$merged_sha" &&
     -n "$platform_root" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine merger requires access/project/merged-source binding' >&2
    exit 2
  }
  [[ "$project_id" =~ ^[A-Za-z0-9._-]+$ ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: unsafe project id' >&2
    exit 2
  }
  python3 -m aisoft_host_access.cli \
    --access-manifest "$access_manifest" \
    --governance-manifest "$manifest" validate >/dev/null || exit 2
  binding="$(jq -cer --arg project_id "$project_id" '
    [.projects[] | select(.project_id == $project_id)]
    | if length == 1 and .[0].routine_merge_agent != null
      then {identity:.[0].routine_merge_agent,repository:.[0].repository}
      else error("missing binding") end
  ' "$access_manifest")" || {
    printf '%s\n' 'BLOCKED_EXTERNAL: project has no exact routine merger binding' >&2
    exit 2
  }
  bound_identity="$(jq -r '.identity' <<<"$binding")"
  bound_repository="$(jq -r '.repository' <<<"$binding")"
  [[ "$bound_identity" == "$username" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine merger identity does not match project binding' >&2
    exit 2
  }
  pilot="$(jq -cer --arg repository "$bound_repository" --arg project_id "$project_id" \
    --arg username "$username" '
    [.repositories[] | select(.name == $repository)]
    | if length == 1
         and .[0].routine_auto_merge_enabled == true
         and .[0].routine_merge_agent == $username
         and .[0].routine_live_pilot.project_id == $project_id
      then .[0].routine_live_pilot
      else error("not the enabled routine live pilot") end
  ' "$manifest")" || {
    printf '%s\n' 'BLOCKED_EXTERNAL: project is not the exact enabled routine live pilot' >&2
    exit 2
  }
  approval_issue="$(jq -r '.rollout_issue' <<<"$pilot")"
  required_mode="approved-issue-$approval_issue"
  python3 -m aisoft_gitea_governance.cli --manifest "$manifest" verify-merged \
    --repository "$bound_repository" --issue "$approval_issue" \
    --merged-sha "$merged_sha" --platform-root "$platform_root" >/dev/null || exit 2
  expected_basename=routine-merge-agent.token
fi
[[ "${AISOFT_ACCOUNT_BOOTSTRAP_MODE:-}" == "$required_mode" ]] || {
  printf 'BLOCKED_EXTERNAL: AISOFT_ACCOUNT_BOOTSTRAP_MODE=%s is required\n' "$required_mode" >&2
  exit 2
}
mkdir -p "$credential_root"
chmod 700 "$credential_root"
credential_root="$(cd -- "$credential_root" && pwd -P)"
marker_root="$credential_root"
if [[ "$token_kind" == routine-merge-agent ]]; then
  mkdir -p "$credential_root/projects/$project_id"
  chmod 700 "$credential_root/projects" "$credential_root/projects/$project_id"
  marker_root="$(cd -- "$credential_root/projects/$project_id" && pwd -P)"
fi
output_parent="$(cd -- "$(dirname -- "$credential_output")" && pwd -P)"
[[ "$output_parent" == "$credential_root" && "$(basename -- "$credential_output")" == "$expected_basename" ]] || {
  if [[ "$token_kind" == routine-merge-agent && "$output_parent" == "$marker_root" &&
        "$(basename -- "$credential_output")" == "$expected_basename" ]]; then
    :
  else
  printf '%s\n' 'BLOCKED_EXTERNAL: credential output must use the exact managed root and filename' >&2
  exit 2
  fi
}
[[ ! -L "$credential_output" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: credential output must not be a symlink' >&2
  exit 2
}

spec="$(python3 -m aisoft_gitea_governance.cli --manifest "$manifest" account-spec \
  --username "$username" --token-kind "$token_kind")" || exit 2
[[ "$(jq -r '.username' <<<"$spec")" == "$username" ]] || exit 2
scopes="$(jq -r '.scopes | join(",")' <<<"$spec")"
[[ -n "$scopes" && "$scopes" != all && "$scopes" != *write:admin* ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: unsafe service account scopes' >&2
  exit 2
}

account_marker="$marker_root/$username.account-created-by-issue-$approval_issue"
password_policy_marker="$marker_root/$username.must-change-password-unset-by-issue-$approval_issue"
token_marker="$credential_output-created-by-issue-$approval_issue"

account_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  "$GITEA_LOCAL_URL/api/v1/users/$username")" || {
  printf '%s\n' 'BLOCKED_EXTERNAL: account existence check failed' >&2
  exit 2
}

case "$account_status" in
  200)
    validate_owned_marker "$account_marker" account account
    ;;
  404)
    [[ ! -e "$account_marker" && ! -e "$password_policy_marker" &&
       ! -e "$credential_output" && ! -e "$token_marker" ]] || {
      printf '%s\n' 'BLOCKED_EXTERNAL: account state conflicts with existing managed files' >&2
      exit 2
    }
    ;;
  *)
    printf 'BLOCKED_EXTERNAL: account existence check returned HTTP %s\n' "$account_status" >&2
    exit 2
    ;;
esac

if [[ -e "$password_policy_marker" || -L "$password_policy_marker" ]]; then
  validate_owned_marker "$password_policy_marker" 'password policy' password-policy
fi
if [[ -e "$credential_output" ]]; then
  [[ -f "$credential_output" && ! -L "$credential_output" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: existing credential is not a regular file' >&2
    exit 2
  }
  mode="$(stat -c '%a' "$credential_output" 2>/dev/null || stat -f '%Lp' "$credential_output")"
  [[ "$mode" == 600 || "$mode" == 400 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: existing credential mode must be 400 or 600' >&2
    exit 2
  }
  validate_owned_marker "$token_marker" token token
elif [[ -e "$token_marker" || -L "$token_marker" ]]; then
  printf '%s\n' 'BLOCKED_EXTERNAL: token marker exists but credential is missing; rotate explicitly' >&2
  exit 2
fi

tmp_dir="$(mktemp -d)"
chmod 700 "$tmp_dir"
trap 'rm -rf -- "$tmp_dir"' EXIT
umask 077
account_mutation_count=0
pat_mutation_count=0

if [[ "$account_status" == 404 ]]; then
  # The caller-owned mode 700 temp directory intentionally receives stdout;
  # sudo is only for the Gitea database operation, not the redirection.
  # shellcheck disable=SC2024
  sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user create \
    --username "$username" \
    --email "$username@aisoft.local" \
    --user-type bot >"$tmp_dir/account-create.log"
  install -m 600 /dev/null "$account_marker"
  printf 'issue=%s\nusername=%s\n' "$approval_issue" "$username" >"$account_marker"
  account_mutation_count=1
  account_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    "$GITEA_LOCAL_URL/api/v1/users/$username")"
  [[ "$account_status" == 200 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: created account read-back failed' >&2
    exit 2
  }
fi

if [[ ! -e "$password_policy_marker" && ! -L "$password_policy_marker" ]]; then
  # Gitea 1.26.4 can create bot users with MustChangePassword=true even though
  # password flags are rejected for bots. Use the dedicated policy command;
  # this does not set a password and is recorded before any PAT is generated.
  # shellcheck disable=SC2024
  sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user must-change-password \
    --unset "$username" >"$tmp_dir/account-password-policy.log"
  install -m 600 /dev/null "$password_policy_marker"
  printf 'issue=%s\nusername=%s\npolicy=must-change-password-unset\n' "$approval_issue" "$username" >"$password_policy_marker"
fi

if [[ -e "$credential_output" ]]; then
  token="$(tr -d '\r\n' <"$credential_output")"
  result=no-op
else
  # Capture the raw token in the caller-owned mode 700 temp directory without
  # placing it in argv or stdout. The redirect intentionally is not sudo-owned.
  # shellcheck disable=SC2024
  sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user generate-access-token \
    --username "$username" \
    --token-name "issue-$approval_issue-$token_kind" \
    --scopes "$scopes" \
    --raw >"$tmp_dir/token"
  token="$(tr -d '\r\n' <"$tmp_dir/token")"
  [[ "$token" =~ ^[A-Za-z0-9._-]+$ ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: generated token format is invalid' >&2
    exit 2
  }
  install -m 600 "$tmp_dir/token" "$credential_output"
  install -m 600 /dev/null "$token_marker"
  printf 'issue=%s\nusername=%s\ntoken_kind=%s\n' "$approval_issue" "$username" "$token_kind" >"$token_marker"
  result=created
  pat_mutation_count=1
fi

identity_file="$tmp_dir/identity.json"
printf 'header = "Authorization: token %s"\n' "$token" |
  curl --config - --fail --silent --show-error "$GITEA_LOCAL_URL/api/v1/user" >"$identity_file"
unset token
[[ "$(jq -r '.login' "$identity_file")" == "$username" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: token identity read-back mismatch' >&2
  exit 2
}
[[ "$(jq -r '.is_admin' "$identity_file")" == false ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: service account unexpectedly has site-admin permission' >&2
  exit 2
}

observed_scopes='not-probed'
if [[ "$token_kind" == routine-merge-agent ]]; then
  scope_file="$tmp_dir/scope.json"
  token="$(tr -d '\r\n' <"$credential_output")"
  scope_status="$(printf 'header = "Authorization: token %s"\n' "$token" |
    curl --config - --silent --show-error --output "$scope_file" \
      --write-out '%{http_code}' "$GITEA_LOCAL_URL/api/v1/notifications")" || {
    unset token
    printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT scope read-back failed' >&2
    exit 2
  }
  unset token
  [[ "$scope_status" == 403 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT scope probe did not fail closed' >&2
    exit 2
  }
  scope_message="$(jq -er '.message' "$scope_file")" || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT scope evidence is unavailable' >&2
    exit 2
  }
  observed_scopes="$(sed -nE 's/.*token scope=([A-Za-z0-9:,_-]+).*/\1/p' <<<"$scope_message")"
  [[ "$scopes" == write:repository && "$observed_scopes" == "$scopes" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine PAT scope must equal write:repository' >&2
    exit 2
  }
fi

jq -cn --arg username "$username" --arg token_kind "$token_kind" --arg result "$result" \
  --arg project_id "$project_id" --arg repository "$bound_repository" \
  --arg scopes "$observed_scopes" --argjson issue "$approval_issue" \
  --argjson account_mutations "$account_mutation_count" \
  --argjson pat_mutations "$pat_mutation_count" \
  '{username:$username,token_kind:$token_kind,result:$result,site_admin:false,
    credential_mode:"600",approval_issue:$issue,
    project_id:($project_id | if length>0 then . else null end),
    repository:($repository | if length>0 then . else null end),observed_scopes:$scopes,
    bootstrap_operation_count:1,account_mutation_count:$account_mutations,
    pat_mutation_count:$pat_mutations}'
