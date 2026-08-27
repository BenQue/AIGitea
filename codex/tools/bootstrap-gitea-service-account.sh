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

usage() {
  printf '%s\n' \
    "usage: $0 --manifest FILE [--access-manifest FILE --project-id ID] --username NAME --token-kind manager-audit|manager-mutation|project-agent|routine-merge-agent --credential-output FILE" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --manifest) manifest="${2:-}"; shift 2 ;;
    --access-manifest) access_manifest="${2:-}"; shift 2 ;;
    --project-id) project_id="${2:-}"; shift 2 ;;
    --username) username="${2:-}"; shift 2 ;;
    --token-kind) token_kind="${2:-}"; shift 2 ;;
    --credential-output) credential_output="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$manifest" && -n "$username" && -n "$token_kind" && -n "$credential_output" ]] || usage
approval_issue=35
required_mode=approved-issue-35
if [[ "$token_kind" == routine-merge-agent ]]; then
  approval_issue=208
  required_mode=approved-issue-208
fi
[[ "${AISOFT_ACCOUNT_BOOTSTRAP_MODE:-}" == "$required_mode" ]] || {
  printf 'BLOCKED_EXTERNAL: AISOFT_ACCOUNT_BOOTSTRAP_MODE=%s is required\n' "$required_mode" >&2
  exit 2
}

for command in python3 jq curl sudo install mktemp; do
  command -v "$command" >/dev/null || {
    printf 'BLOCKED_EXTERNAL: required command is missing: %s\n' "$command" >&2
    exit 2
  }
done

GITEA_BIN="${GITEA_BIN:-/usr/local/bin/gitea}"
GITEA_CONFIG="${GITEA_CONFIG:-/etc/gitea/app.ini}"
GITEA_LOCAL_URL="${GITEA_LOCAL_URL:-http://127.0.0.1:3000}"
credential_root="${AISOFT_CREDENTIAL_ROOT:-/home/benque/.config/aisoft/credentials}"
export PYTHONPATH="$ROOT/codex/runtime${PYTHONPATH:+:$PYTHONPATH}"

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

mkdir -p "$credential_root"
chmod 700 "$credential_root"
credential_root="$(cd -- "$credential_root" && pwd -P)"
expected_basename="$username-$token_kind.token"
marker_root="$credential_root"
if [[ "$token_kind" == routine-merge-agent ]]; then
  [[ -n "$access_manifest" && -n "$project_id" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine merger requires --access-manifest and --project-id' >&2
    exit 2
  }
  [[ "$project_id" =~ ^[A-Za-z0-9._-]+$ ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: unsafe project id' >&2
    exit 2
  }
  python3 -m aisoft_host_access.cli \
    --access-manifest "$access_manifest" \
    --governance-manifest "$manifest" validate >/dev/null || exit 2
  bound_identity="$(jq -er --arg project_id "$project_id" '
    [.projects[] | select(.project_id == $project_id) | .routine_merge_agent]
    | if length == 1 and .[0] != null then .[0] else error("missing binding") end
  ' "$access_manifest")" || {
    printf '%s\n' 'BLOCKED_EXTERNAL: project has no exact routine merger binding' >&2
    exit 2
  }
  [[ "$bound_identity" == "$username" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: routine merger identity does not match project binding' >&2
    exit 2
  }
  mkdir -p "$credential_root/projects/$project_id"
  chmod 700 "$credential_root/projects" "$credential_root/projects/$project_id"
  marker_root="$(cd -- "$credential_root/projects/$project_id" && pwd -P)"
  expected_basename=routine-merge-agent.token
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

tmp_dir="$(mktemp -d)"
chmod 700 "$tmp_dir"
trap 'rm -rf -- "$tmp_dir"' EXIT
umask 077

case "$account_status" in
  200)
    [[ -f "$account_marker" ]] || {
      printf 'BLOCKED_EXTERNAL: account exists without an Issue #%s ownership marker\n' "$approval_issue" >&2
      exit 2
    }
    ;;
  404)
    [[ ! -e "$account_marker" && ! -e "$password_policy_marker" &&
       ! -e "$credential_output" && ! -e "$token_marker" ]] || {
      printf '%s\n' 'BLOCKED_EXTERNAL: account state conflicts with existing managed files' >&2
      exit 2
    }
    # The caller-owned mode 700 temp directory intentionally receives stdout;
    # sudo is only for the Gitea database operation, not the redirection.
    # shellcheck disable=SC2024
    sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user create \
      --username "$username" \
      --email "$username@aisoft.local" \
      --user-type bot >"$tmp_dir/account-create.log"
    install -m 600 /dev/null "$account_marker"
    printf 'issue=%s\nusername=%s\n' "$approval_issue" "$username" >"$account_marker"
    account_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
      "$GITEA_LOCAL_URL/api/v1/users/$username")"
    [[ "$account_status" == 200 ]] || {
      printf '%s\n' 'BLOCKED_EXTERNAL: created account read-back failed' >&2
      exit 2
    }
    ;;
  *)
    printf 'BLOCKED_EXTERNAL: account existence check returned HTTP %s\n' "$account_status" >&2
    exit 2
    ;;
esac

if [[ -e "$password_policy_marker" || -L "$password_policy_marker" ]]; then
  [[ -f "$password_policy_marker" && ! -L "$password_policy_marker" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: password policy marker is not a regular file' >&2
    exit 2
  }
  mode="$(stat -c '%a' "$password_policy_marker" 2>/dev/null || stat -f '%Lp' "$password_policy_marker")"
  [[ "$mode" == 600 || "$mode" == 400 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: password policy marker mode must be 400 or 600' >&2
    exit 2
  }
  expected_policy_marker="$(printf 'issue=%s\nusername=%s\npolicy=must-change-password-unset' "$approval_issue" "$username")"
  [[ "$(cat "$password_policy_marker")" == "$expected_policy_marker" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: password policy marker content mismatch' >&2
    exit 2
  }
else
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
  [[ -f "$credential_output" && ! -L "$credential_output" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: existing credential is not a regular file' >&2
    exit 2
  }
  mode="$(stat -c '%a' "$credential_output" 2>/dev/null || stat -f '%Lp' "$credential_output")"
  [[ "$mode" == 600 || "$mode" == 400 ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: existing credential mode must be 400 or 600' >&2
    exit 2
  }
  [[ -f "$token_marker" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: credential exists without a token ownership marker' >&2
    exit 2
  }
  token="$(tr -d '\r\n' <"$credential_output")"
  result=no-op
else
  [[ ! -e "$token_marker" ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: token marker exists but credential is missing; rotate explicitly' >&2
    exit 2
  }
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

jq -cn --arg username "$username" --arg token_kind "$token_kind" --arg result "$result" \
  '{username:$username,token_kind:$token_kind,result:$result,site_admin:false,credential_mode:"600"}'
