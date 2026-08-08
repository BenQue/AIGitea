#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
cleanup() {
  chmod 700 "$TMP/protected-config" 2>/dev/null || true
  rm -rf -- "$TMP"
}
trap cleanup EXIT
mkdir -p "$TMP/bin" "$TMP/credentials" "$TMP/protected-config"
chmod 700 "$TMP/credentials"
touch "$TMP/protected-config/gitea.ini"
chmod 600 "$TMP/protected-config/gitea.ini"
chmod 000 "$TMP/protected-config"

cat >"$TMP/bin/sudo" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[[ "$1" == -n && "$2" == -u && "$3" == git ]]
shift 3
if [[ "${1:-}" == test && ( "${2:-}" == -f || "${2:-}" == -r ) &&
      "${3:-}" == "$MOCK_GITEA_CONFIG" ]]; then
  printf '%s\n' "$*" >>"$MOCK_ROOT/sudo-config-check.log"
  exit 0
fi
exec "$@"
MOCK

cat >"$TMP/bin/gitea" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/gitea-argv.log"
case "$*" in
  *"admin user create"*)
    touch "$MOCK_ROOT/account-present"
    touch "$MOCK_ROOT/must-change-password-present"
    printf 'generated password: do-not-log-this-password\n'
    ;;
  *"admin user must-change-password --unset hsdb-agent"*)
    rm -f "$MOCK_ROOT/must-change-password-present"
    printf 'updated one user\n'
    ;;
  *"admin user generate-access-token"*)
    printf 'sentinel-generated-token\n'
    ;;
  *) exit 2 ;;
esac
MOCK

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/curl-argv.log"
case "$*" in
  *"/api/v1/users/hsdb-agent"*)
    if [[ -f "$MOCK_ROOT/account-present" ]]; then printf 200; else printf 404; fi
    ;;
  *"/api/v1/user"*)
    read -r auth
    [[ "$auth" == *sentinel-generated-token* ]]
    [[ ! -e "$MOCK_ROOT/must-change-password-present" ]]
    printf '{"login":"hsdb-agent","is_admin":false}\n'
    ;;
  *) exit 2 ;;
esac
MOCK

chmod +x "$TMP/bin/sudo" "$TMP/bin/gitea" "$TMP/bin/curl"
export MOCK_ROOT="$TMP"
export MOCK_GITEA_CONFIG="$TMP/protected-config/gitea.ini"
export PATH="$TMP/bin:$PATH"
export AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-35
export AISOFT_CREDENTIAL_ROOT="$TMP/credentials"
export GITEA_BIN="$TMP/bin/gitea"
export GITEA_CONFIG="$MOCK_GITEA_CONFIG"
export GITEA_LOCAL_URL=http://127.0.0.1:3000

output="$TMP/credentials/hsdb-agent-project-agent.token"
result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username hsdb-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == created ]]
[[ "$(cat "$output")" == sentinel-generated-token ]]
mode="$(stat -c '%a' "$output" 2>/dev/null || stat -f '%Lp' "$output")"
[[ "$mode" == 600 ]]
[[ -f "$TMP/credentials/hsdb-agent.account-created-by-issue-35" ]]
policy_marker="$TMP/credentials/hsdb-agent.must-change-password-unset-by-issue-35"
[[ -f "$policy_marker" ]]
[[ "$(stat -c '%a' "$policy_marker" 2>/dev/null || stat -f '%Lp' "$policy_marker")" == 600 ]]
[[ -f "$TMP/credentials/hsdb-agent-project-agent.token-created-by-issue-35" ]]
[[ "$(grep -c '^test -f ' "$TMP/sudo-config-check.log")" == 1 ]]
[[ "$(grep -c '^test -r ' "$TMP/sudo-config-check.log")" == 1 ]]
create_argv="$(grep 'admin user create' "$TMP/gitea-argv.log")"
[[ "$create_argv" == *"--user-type bot"* ]]
if [[ "$create_argv" == *"password"* ]]; then
  printf '%s\n' 'bot create argv must omit all password flags' >&2
  exit 1
fi
policy_argv="$(grep 'admin user must-change-password' "$TMP/gitea-argv.log")"
[[ "$policy_argv" == *"admin user must-change-password --unset hsdb-agent"* ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 1 ]]

result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username hsdb-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == no-op ]]
[[ "$(grep -c 'generate-access-token' "$TMP/gitea-argv.log")" == 1 ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 1 ]]

rm "$policy_marker"
touch "$TMP/must-change-password-present"
result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username hsdb-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == no-op ]]
[[ -f "$policy_marker" ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 2 ]]

chmod 644 "$policy_marker"
if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username hsdb-agent \
  --token-kind project-agent \
  --credential-output "$output" \
  >"$TMP/policy-marker-negative.out" 2>"$TMP/policy-marker-negative.err"; then
  printf '%s\n' 'unsafe password policy marker mode unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'password policy marker mode must be 400 or 600' "$TMP/policy-marker-negative.err"
chmod 600 "$policy_marker"

if grep -Fq sentinel-generated-token "$TMP/gitea-argv.log" ||
   grep -Fq sentinel-generated-token "$TMP/curl-argv.log" ||
   grep -Fq do-not-log-this-password <<<"$result"; then
  printf '%s\n' 'secret leaked through argv or stdout' >&2
  exit 1
fi

if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username unknown-agent \
  --token-kind project-agent \
  --credential-output "$TMP/credentials/unknown-agent-project-agent.token" \
  >"$TMP/negative.out" 2>"$TMP/negative.err"; then
  printf '%s\n' 'undeclared account unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'not declared' "$TMP/negative.err"

printf '%s\n' 'bootstrap Gitea service account tests passed'
