#!/usr/bin/env bash
set -euo pipefail

# Never inherit xtrace across profile or credential loading.
set +x

resource="${1:-repo}"
env_file="${AGENT_ENV_FILE:-}"

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

secure_mode() {
  local path="$1"
  local mode
  [[ -f "$path" ]] || fail "required file not found: $path"
  if ! mode="$(stat -c '%a' "$path" 2>/dev/null)"; then
    mode="$(stat -f '%Lp' "$path" 2>/dev/null)" ||
      fail "cannot read file mode: $path"
  fi
  case "$mode" in
    400|600) ;;
    *) fail "credential or profile file must have mode 400 or 600: $path" ;;
  esac
}

if [[ -n "$env_file" ]]; then
  secure_mode "$env_file"
  # The selected profile is trusted configuration. Suppress any accidental
  # output so the helper returns only the requested API response.
  # shellcheck disable=SC1090
  source "$env_file" >/dev/null 2>&1
  set +x
fi

for name in GITEA_URL GITEA_OWNER GITEA_REPO; do
  [[ -n "${!name:-}" ]] || fail "$name is required"
done

[[ "$GITEA_OWNER" =~ ^[A-Za-z0-9._-]+$ ]] ||
  fail 'GITEA_OWNER contains unsafe characters'
[[ "$GITEA_REPO" =~ ^[A-Za-z0-9._-]+$ ]] ||
  fail 'GITEA_REPO contains unsafe characters'
case "$GITEA_URL" in
  http://*|https://*) ;;
  *) fail 'GITEA_URL must use http or https' ;;
esac
[[ "$GITEA_URL" != *"@"* ]] ||
  fail 'GITEA_URL must not contain embedded credentials'

if [[ -n "${GITEA_EXPECT_OWNER:-}" && "$GITEA_OWNER" != "$GITEA_EXPECT_OWNER" ]]; then
  fail 'selected profile owner does not match the expected target'
fi
if [[ -n "${GITEA_EXPECT_REPO:-}" && "$GITEA_REPO" != "$GITEA_EXPECT_REPO" ]]; then
  fail 'selected profile repository does not match the expected target'
fi

case "$resource" in
  repo)
    endpoint="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO"
    ;;
  *)
    [[ "$resource" != /* && "$resource" != *".."* && "$resource" != *"://"* ]] ||
      fail 'resource must be a safe repository-relative API path'
    [[ "$resource" != *"%2e"* && "$resource" != *"%2E"* ]] ||
      fail 'resource must not contain encoded path traversal'
    [[ "$resource" =~ ^[A-Za-z0-9._~?=\&/%:+,-]+$ ]] ||
      fail 'resource contains unsafe characters'
    endpoint="${GITEA_URL%/}/api/v1/repos/$GITEA_OWNER/$GITEA_REPO/$resource"
    ;;
esac

token="${GITEA_TOKEN:-}"
if [[ -z "$token" && -n "${GITEA_TOKEN_FILE:-}" ]]; then
  # Post-#61 project profiles carry GITEA_IDENTITY plus a fixed GITEA_TOKEN_FILE instead of
  # an inline GITEA_TOKEN. Read that file through the same mode gate the profile itself uses
  # so the preferred ladder step keeps working after profile migration.
  secure_mode "$GITEA_TOKEN_FILE"
  token="$(<"$GITEA_TOKEN_FILE")"
  token="${token%%$'\n'*}"
fi
if [[ -z "$token" ]]; then
  credential_file="${GITEA_CREDENTIAL_FILE:-/home/benque/gitea-ci-credentials.txt}"
  secure_mode "$credential_file"
  token="$(awk '/^admin token:/ {print $NF; exit}' "$credential_file")"
fi
[[ -n "$token" ]] || fail 'no Gitea token is available'
[[ "$token" =~ ^[A-Za-z0-9._-]+$ ]] ||
  fail 'Gitea token contains unsafe characters'

# Send the token to curl through stdin configuration, never argv or output.
printf 'header = "Authorization: token %s"\n' "$token" |
  curl --config - --fail --silent --show-error --request GET "$endpoint"
