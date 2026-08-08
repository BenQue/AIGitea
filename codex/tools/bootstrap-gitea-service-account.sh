#!/usr/bin/env bash
set -euo pipefail
set +x

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
manifest=''
username=''
token_kind=''
credential_output=''

usage() {
  printf '%s\n' \
    "usage: $0 --manifest FILE --username NAME --token-kind manager-audit|manager-mutation|project-agent --credential-output FILE" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --manifest) manifest="${2:-}"; shift 2 ;;
    --username) username="${2:-}"; shift 2 ;;
    --token-kind) token_kind="${2:-}"; shift 2 ;;
    --credential-output) credential_output="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$manifest" && -n "$username" && -n "$token_kind" && -n "$credential_output" ]] || usage
[[ "${AISOFT_ACCOUNT_BOOTSTRAP_MODE:-}" == "approved-issue-35" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-35 is required' >&2
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
output_parent="$(cd -- "$(dirname -- "$credential_output")" && pwd -P)"
expected_basename="$username-$token_kind.token"
[[ "$output_parent" == "$credential_root" && "$(basename -- "$credential_output")" == "$expected_basename" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: credential output must use the exact managed root and filename' >&2
  exit 2
}
[[ ! -L "$credential_output" ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: credential output must not be a symlink' >&2
  exit 2
}

export PYTHONPATH="$ROOT/codex/runtime${PYTHONPATH:+:$PYTHONPATH}"
spec="$(python3 -m aisoft_gitea_governance.cli --manifest "$manifest" account-spec \
  --username "$username" --token-kind "$token_kind")" || exit 2
[[ "$(jq -r '.username' <<<"$spec")" == "$username" ]] || exit 2
scopes="$(jq -r '.scopes | join(",")' <<<"$spec")"
[[ -n "$scopes" && "$scopes" != all && "$scopes" != *write:admin* ]] || {
  printf '%s\n' 'BLOCKED_EXTERNAL: unsafe service account scopes' >&2
  exit 2
}

account_marker="$credential_root/$username.account-created-by-issue-35"
token_marker="$credential_root/$username-$token_kind.token-created-by-issue-35"

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
      printf '%s\n' 'BLOCKED_EXTERNAL: account exists without an Issue #35 ownership marker' >&2
      exit 2
    }
    ;;
  404)
    [[ ! -e "$account_marker" && ! -e "$credential_output" && ! -e "$token_marker" ]] || {
      printf '%s\n' 'BLOCKED_EXTERNAL: account state conflicts with existing managed files' >&2
      exit 2
    }
    # The caller-owned mode 700 temp directory intentionally receives stdout;
    # sudo is only for the Gitea database operation, not the redirection.
    # shellcheck disable=SC2024
    sudo -n -u git "$GITEA_BIN" --config "$GITEA_CONFIG" admin user create \
      --username "$username" \
      --email "$username@aisoft.local" \
      --user-type bot \
      --random-password >"$tmp_dir/account-create.log"
    install -m 600 /dev/null "$account_marker"
    printf 'issue=35\nusername=%s\n' "$username" >"$account_marker"
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
    --token-name "issue-35-$token_kind" \
    --scopes "$scopes" \
    --raw >"$tmp_dir/token"
  token="$(tr -d '\r\n' <"$tmp_dir/token")"
  [[ "$token" =~ ^[A-Za-z0-9._-]+$ ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: generated token format is invalid' >&2
    exit 2
  }
  install -m 600 "$tmp_dir/token" "$credential_output"
  install -m 600 /dev/null "$token_marker"
  printf 'issue=35\nusername=%s\ntoken_kind=%s\n' "$username" "$token_kind" >"$token_marker"
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
