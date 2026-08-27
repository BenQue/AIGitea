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
  *"admin user create"*"--username newemaint-routine-merger"*)
    touch "$MOCK_ROOT/routine-account-present"
    touch "$MOCK_ROOT/routine-must-change-password-present"
    printf 'generated password: do-not-log-this-password\n'
    ;;
  *"admin user create"*)
    touch "$MOCK_ROOT/account-present"
    touch "$MOCK_ROOT/must-change-password-present"
    printf 'generated password: do-not-log-this-password\n'
    ;;
  *"admin user must-change-password --unset newemaint-routine-merger"*)
    rm -f "$MOCK_ROOT/routine-must-change-password-present"
    printf 'updated one user\n'
    ;;
  *"admin user must-change-password --unset hsdb-agent"*)
    rm -f "$MOCK_ROOT/must-change-password-present"
    printf 'updated one user\n'
    ;;
  *"admin user generate-access-token"*"issue-213-routine-merge-agent"*)
    printf 'sentinel-routine-token\n'
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
output=''
for ((index=1; index<=$#; index++)); do
  if [[ "${!index}" == --output ]]; then
    next=$((index + 1)); output="${!next}"
  fi
done
case "$*" in
  *"/api/v1/users/newemaint-routine-merger"*)
    if [[ -f "$MOCK_ROOT/routine-account-present" ]]; then
      [[ -n "$output" ]]
      identity="${MOCK_ACCOUNT_IDENTITY:-}"
      [[ -n "$identity" ]] || identity='{"login":"newemaint-routine-merger","is_admin":false}'
      printf '%s\n' "$identity" >"$output"
      printf 200
    else
      printf 404
    fi
    ;;
  *"/api/v1/users/hsdb-agent"*)
    if [[ -f "$MOCK_ROOT/account-present" ]]; then
      [[ -n "$output" ]]
      identity="${MOCK_ACCOUNT_IDENTITY:-}"
      [[ -n "$identity" ]] || identity='{"login":"hsdb-agent","is_admin":false}'
      printf '%s\n' "$identity" >"$output"
      printf 200
    else
      printf 404
    fi
    ;;
  *"/api/v1/user"*)
    read -r auth
    if [[ "$auth" == *sentinel-routine-token* ]]; then
      [[ ! -e "$MOCK_ROOT/routine-must-change-password-present" ]]
      printf '{"login":"newemaint-routine-merger","is_admin":false}\n'
    else
      [[ "$auth" == *sentinel-generated-token* ]]
      [[ ! -e "$MOCK_ROOT/must-change-password-present" ]]
      printf '{"login":"hsdb-agent","is_admin":false}\n'
    fi
    ;;
  *"/api/v1/notifications"*)
    read -r auth
    [[ "$auth" == *sentinel-routine-token* ]]
    output=''
    while (($#)); do
      if [[ "$1" == --output ]]; then output="$2"; shift 2; else shift; fi
    done
    [[ -n "$output" ]]
    printf '{"message":"token does not have required scope, token scope=%s"}\n' \
      "${MOCK_ROUTINE_SCOPE:-write:repository}" >"$output"
    printf 403
    ;;
  *) exit 2 ;;
esac
MOCK

chmod +x "$TMP/bin/sudo" "$TMP/bin/gitea" "$TMP/bin/curl"

cat >"$TMP/bin/git" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  *"merge-base --is-ancestor"*) exit 0 ;;
  *"show "*) cat "$MOCK_GOVERNANCE_MANIFEST" ;;
  *) exec /usr/bin/git "$@" ;;
esac
MOCK
chmod +x "$TMP/bin/git"
export MOCK_ROOT="$TMP"
export MOCK_GITEA_CONFIG="$TMP/protected-config/gitea.ini"
export MOCK_GOVERNANCE_MANIFEST="$ROOT/codex/config/gitea-governance.json"
export MOCK_ROUTINE_SCOPE=write:repository
export PATH="$TMP/bin:$PATH"
export AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-35
export AISOFT_CREDENTIAL_ROOT="$TMP/credentials"
export GITEA_BIN="$TMP/bin/gitea"
export GITEA_CONFIG="$MOCK_GITEA_CONFIG"
export GITEA_LOCAL_URL=http://127.0.0.1:3000

line_count() {
  local path="$1"
  if [[ -f "$path" ]]; then
    wc -l <"$path" | tr -d ' '
  else
    printf '0\n'
  fi
}

unauthorized_root="$TMP/unauthorized-credentials"
mkdir -p "$unauthorized_root"
chmod 755 "$unauthorized_root"
printf '%s\n' sentinel >"$unauthorized_root/state"
unauthorized_mode_before="$(stat -c '%a' "$unauthorized_root" 2>/dev/null || stat -f '%Lp' "$unauthorized_root")"
unauthorized_state_before="$(shasum -a 256 "$unauthorized_root/state")"
gitea_count_before="$(line_count "$TMP/gitea-argv.log")"
curl_count_before="$(line_count "$TMP/curl-argv.log")"
if AISOFT_ACCOUNT_BOOTSTRAP_MODE=not-authorized \
   AISOFT_CREDENTIAL_ROOT="$unauthorized_root" \
   bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
    --manifest "$ROOT/codex/config/gitea-governance.json" \
    --username hsdb-agent \
    --token-kind project-agent \
    --credential-output "$unauthorized_root/hsdb-agent-project-agent.token" \
    >"$TMP/unauthorized.out" 2>"$TMP/unauthorized.err"; then
  printf '%s\n' 'unauthorized bootstrap unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-35 is required' "$TMP/unauthorized.err"
[[ "$(stat -c '%a' "$unauthorized_root" 2>/dev/null || stat -f '%Lp' "$unauthorized_root")" == "$unauthorized_mode_before" ]]
[[ "$(shasum -a 256 "$unauthorized_root/state")" == "$unauthorized_state_before" ]]
[[ "$(find "$unauthorized_root" -mindepth 1 -maxdepth 1 -print | wc -l | tr -d ' ')" == 1 ]]
[[ "$(line_count "$TMP/gitea-argv.log")" == "$gitea_count_before" ]]
[[ "$(line_count "$TMP/curl-argv.log")" == "$curl_count_before" ]]

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
grep -Fq 'password policy ownership marker mode must be 400 or 600' "$TMP/policy-marker-negative.err"
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

export AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-213
routine_output="$TMP/credentials/projects/newemaint/routine-merge-agent.token"
routine_result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --project-id newemaint \
  --username newemaint-routine-merger \
  --token-kind routine-merge-agent \
  --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --platform-root "$ROOT" \
  --credential-output "$routine_output")"
[[ "$(jq -r '.result' <<<"$routine_result")" == created ]]
[[ "$(jq -r '.approval_issue' <<<"$routine_result")" == 213 ]]
[[ "$(jq -r '.observed_scopes' <<<"$routine_result")" == write:repository ]]
[[ "$(jq -r '.account_mutation_count' <<<"$routine_result")" == 1 ]]
[[ "$(jq -r '.pat_mutation_count' <<<"$routine_result")" == 1 ]]
[[ "$(cat "$routine_output")" == sentinel-routine-token ]]
[[ "$(stat -c '%a' "$routine_output" 2>/dev/null || stat -f '%Lp' "$routine_output")" == 600 ]]
[[ -f "$TMP/credentials/projects/newemaint/newemaint-routine-merger.account-created-by-issue-213" ]]
[[ -f "$routine_output-created-by-issue-213" ]]
grep -Fq 'issue-213-routine-merge-agent' "$TMP/gitea-argv.log"

routine_result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --project-id newemaint \
  --username newemaint-routine-merger \
  --token-kind routine-merge-agent \
  --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --platform-root "$ROOT" \
  --credential-output "$routine_output")"
[[ "$(jq -r '.result' <<<"$routine_result")" == no-op ]]
[[ "$(jq -r '.account_mutation_count' <<<"$routine_result")" == 0 ]]
[[ "$(jq -r '.pat_mutation_count' <<<"$routine_result")" == 0 ]]
[[ "$(grep -c 'issue-213-routine-merge-agent' "$TMP/gitea-argv.log")" == 1 ]]

routine_account_marker="$TMP/credentials/projects/newemaint/newemaint-routine-merger.account-created-by-issue-213"
routine_token_marker="$routine_output-created-by-issue-213"
routine_policy_marker="$TMP/credentials/projects/newemaint/newemaint-routine-merger.must-change-password-unset-by-issue-213"

managed_routine_state() {
  local managed_path
  for managed_path in \
    "$routine_output" "$routine_token_marker" \
    "$routine_account_marker" "$routine_policy_marker"; do
    printf '%s %s ' "$managed_path" \
      "$(stat -c '%a' "$managed_path" 2>/dev/null || stat -f '%Lp' "$managed_path")"
    shasum -a 256 "$managed_path"
  done
}

identity_gate_root="$TMP/identity-gate-credentials"
mkdir -p "$identity_gate_root/projects/newemaint"
chmod 700 "$identity_gate_root" "$identity_gate_root/projects" \
  "$identity_gate_root/projects/newemaint"
identity_gate_marker="$identity_gate_root/projects/newemaint/newemaint-routine-merger.account-created-by-issue-213"
printf 'issue=213\nusername=newemaint-routine-merger\n' >"$identity_gate_marker"
chmod 600 "$identity_gate_marker"

identity_gate_state() {
  local path
  while IFS= read -r path; do
    printf '%s %s ' "${path#"$identity_gate_root"}" \
      "$(stat -c '%a' "$path" 2>/dev/null || stat -f '%Lp' "$path")"
    if [[ -f "$path" ]]; then shasum -a 256 "$path"; else printf '\n'; fi
  done < <(find "$identity_gate_root" -mindepth 1 -print | LC_ALL=C sort)
}

assert_identity_gate_rejected() {
  local variant="$1"
  local payload="$2"
  local state_before
  local gitea_before
  local pat_before
  state_before="$(identity_gate_state)"
  gitea_before="$(line_count "$TMP/gitea-argv.log")"
  pat_before="$(grep -c 'generate-access-token' "$TMP/gitea-argv.log" || true)"
  if MOCK_ACCOUNT_IDENTITY="$payload" \
     AISOFT_CREDENTIAL_ROOT="$identity_gate_root" \
     bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
      --manifest "$ROOT/codex/config/gitea-governance.json" \
      --access-manifest "$ROOT/codex/config/host-access-broker.json" \
      --project-id newemaint \
      --username newemaint-routine-merger \
      --token-kind routine-merge-agent \
      --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
      --platform-root "$ROOT" \
      --credential-output "$identity_gate_root/projects/newemaint/routine-merge-agent.token" \
      >"$TMP/identity-gate-$variant.out" \
      2>"$TMP/identity-gate-$variant.err"; then
    printf 'unsafe account identity unexpectedly generated a PAT: %s\n' \
      "$variant" >&2
    exit 1
  fi
  grep -Fq 'existing account read-back must be the exact non-admin service identity' \
    "$TMP/identity-gate-$variant.err"
  [[ "$(grep -c 'generate-access-token' "$TMP/gitea-argv.log" || true)" == "$pat_before" ]]
  [[ "$(line_count "$TMP/gitea-argv.log")" == "$gitea_before" ]]
  [[ "$(identity_gate_state)" == "$state_before" ]]
}

assert_identity_gate_rejected missing \
  '{"login":"newemaint-routine-merger"}'
assert_identity_gate_rejected string-false \
  '{"login":"newemaint-routine-merger","is_admin":"false"}'
assert_identity_gate_rejected number \
  '{"login":"newemaint-routine-merger","is_admin":0}'
assert_identity_gate_rejected list \
  '{"login":"newemaint-routine-merger","is_admin":[]}'
assert_identity_gate_rejected site-admin \
  '{"login":"newemaint-routine-merger","is_admin":true}'
assert_identity_gate_rejected wrong-login \
  '{"login":"admin","is_admin":false}'
assert_identity_gate_rejected root-list '[]'

assert_corrupt_account_marker_rejected() {
  local variant="$1"
  local state_before
  local gitea_before
  state_before="$(managed_routine_state)"
  gitea_before="$(line_count "$TMP/gitea-argv.log")"
  if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
    --manifest "$ROOT/codex/config/gitea-governance.json" \
    --access-manifest "$ROOT/codex/config/host-access-broker.json" \
    --project-id newemaint \
    --username newemaint-routine-merger \
    --token-kind routine-merge-agent \
    --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
    --platform-root "$ROOT" \
    --credential-output "$routine_output" \
    >"$TMP/routine-account-marker-$variant.out" \
    2>"$TMP/routine-account-marker-$variant.err"; then
    printf 'corrupt routine account marker unexpectedly succeeded: %s\n' "$variant" >&2
    exit 1
  fi
  grep -Fq 'account ownership marker content mismatch' \
    "$TMP/routine-account-marker-$variant.err"
  [[ "$(line_count "$TMP/gitea-argv.log")" == "$gitea_before" ]]
  [[ "$(managed_routine_state)" == "$state_before" ]]
}

printf 'issue=213\nusername=newemaint-routine-merger\n\n' >"$routine_account_marker"
assert_corrupt_account_marker_rejected extra-newline
printf 'issue=213\nusername=newemaint-routine-merger\n' >"$routine_account_marker"
printf '\0' >>"$routine_account_marker"
assert_corrupt_account_marker_rejected nul-suffix
printf 'prefix\nissue=213\nusername=newemaint-routine-merger\n' >"$routine_account_marker"
assert_corrupt_account_marker_rejected prefix
printf 'issue=213\nusername=newemaint-routine-merger\nsuffix\n' >"$routine_account_marker"
assert_corrupt_account_marker_rejected suffix
printf 'issue=213\nusername=newemaint-routine-merger\n' >"$routine_account_marker"

chmod 644 "$routine_token_marker"
gitea_count_before="$(line_count "$TMP/gitea-argv.log")"
if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --project-id newemaint \
  --username newemaint-routine-merger \
  --token-kind routine-merge-agent \
  --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --platform-root "$ROOT" \
  --credential-output "$routine_output" \
  >"$TMP/routine-token-marker-negative.out" 2>"$TMP/routine-token-marker-negative.err"; then
  printf '%s\n' 'unsafe routine token ownership marker mode unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'token ownership marker mode must be 400 or 600' "$TMP/routine-token-marker-negative.err"
[[ "$(line_count "$TMP/gitea-argv.log")" == "$gitea_count_before" ]]
chmod 600 "$routine_token_marker"

export MOCK_ROUTINE_SCOPE=read:repository
if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --project-id newemaint \
  --username newemaint-routine-merger \
  --token-kind routine-merge-agent \
  --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --platform-root "$ROOT" \
  --credential-output "$routine_output" \
  >"$TMP/routine-scope-negative.out" 2>"$TMP/routine-scope-negative.err"; then
  printf '%s\n' 'unsafe routine scope unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'routine PAT scope must equal write:repository' "$TMP/routine-scope-negative.err"
export MOCK_ROUTINE_SCOPE=write:repository

if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --project-id localwms \
  --username newemaint-routine-merger \
  --token-kind routine-merge-agent \
  --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --platform-root "$ROOT" \
  --credential-output "$TMP/credentials/projects/localwms/routine-merge-agent.token" \
  >"$TMP/routine-binding-negative.out" 2>"$TMP/routine-binding-negative.err"; then
  printf '%s\n' 'cross-project routine merger binding unexpectedly succeeded' >&2
  exit 1
fi
grep -Fq 'identity does not match project binding' "$TMP/routine-binding-negative.err"

if grep -Fq sentinel-routine-token "$TMP/gitea-argv.log" ||
   grep -Fq sentinel-routine-token "$TMP/curl-argv.log" ||
   grep -Fq sentinel-routine-token <<<"$routine_result"; then
  printf '%s\n' 'routine merger secret leaked through argv or stdout' >&2
  exit 1
fi

printf '%s\n' 'bootstrap Gitea service account tests passed'
