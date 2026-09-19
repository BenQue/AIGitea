#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"

# Issue #227: this script is part of the required check `CI / verify`, and
# gitea-ci runs one instance-level runner with maxParallel=1. Any unbounded wait
# here stalls CI for every repository, so the script must always fail in bounded
# time with a searchable marker rather than hang. The watchdog is a backstop;
# the real fixes are the bounded, fail-closed mocks below.
AISOFT_TEST_DEADLINE_SECONDS="${AISOFT_TEST_DEADLINE_SECONDS:-600}"
watchdog_pid=''

kill_descendants() {
  local parent="$1"
  # The watchdog is itself a child of the script it guards, so it must be able
  # to exclude its own pid. Without this it kills itself before it ever signals
  # the target, and the hang it was meant to bound survives forever.
  local exclude="${2:-}"
  local child
  for child in $(ps -Ao pid=,ppid= 2>/dev/null | awk -v p="$parent" '$2 == p {print $1}'); do
    if [[ -n "$exclude" && "$child" == "$exclude" ]]; then
      continue
    fi
    kill_descendants "$child" "$exclude"
    kill -KILL "$child" 2>/dev/null || true
  done
}

cleanup() {
  if [[ -n "$watchdog_pid" ]]; then
    kill_descendants "$watchdog_pid"
    kill -KILL "$watchdog_pid" 2>/dev/null || true
    watchdog_pid=''
  fi
  chmod 700 "$TMP/protected-config" 2>/dev/null || true
  rm -rf -- "$TMP"
}
trap cleanup EXIT
# Turn a delivered TERM into an ordinary exit so the EXIT trap still cleans up.
trap 'exit 143' TERM

start_deadline_watchdog() {
  local deadline="$1"
  local target=$$
  local step=5
  local pid_file="$TMP/.deadline-watchdog.pid"
  [[ "$deadline" -gt 0 ]] || return 0
  (
    waited=0
    while ((waited < deadline)); do
      sleep "$step"
      kill -0 "$target" 2>/dev/null || exit 0
      waited=$((waited + step))
    done
    printf 'AISOFT_TEST_DEADLINE_EXCEEDED: %s exceeded %ss; killing pid %s and its descendants\n' \
      "${BASH_SOURCE[0]}" "$deadline" "$target" >&2
    # bash 3.2 has no BASHPID, so the parent hands the watchdog its own pid
    # through a file it writes right after backgrounding this subshell.
    self_pid=''
    [[ ! -f "$pid_file" ]] || self_pid="$(cat "$pid_file")"
    kill_descendants "$target" "$self_pid"
    kill -TERM "$target" 2>/dev/null || true
    sleep 2
    kill -KILL "$target" 2>/dev/null || true
  ) &
  watchdog_pid=$!
  printf '%s\n' "$watchdog_pid" >"$pid_file"
  # Detach it so reaping the watchdog never prints a job notice into CI logs.
  disown "$watchdog_pid" 2>/dev/null || true
}
start_deadline_watchdog "$AISOFT_TEST_DEADLINE_SECONDS"

if [[ -n "${AISOFT_TEST_SELFTEST_HANG:-}" ]]; then
  # Fault injection for the deadline self-check at the end of this file. It
  # blocks in open() on a FIFO with no partner, which is the exact syscall the
  # 2026-08-29 outage was stuck in (wait_for_partner -> fifo_open).
  mkfifo "$TMP/selftest-hang.fifo"
  exec 9<"$TMP/selftest-hang.fifo"
  printf '%s\n' 'AISOFT_TEST_SELFTEST_HANG failed to block' >&2
  exit 1
fi

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
  *"admin user delete --username newemaint-routine-merger"*)
    if [[ "${MOCK_COMPENSATION_DELETE_FAIL:-0}" == 1 ]]; then exit 3; fi
    if [[ "${MOCK_COMPENSATION_DELETE_LEAVES_ACCOUNT:-0}" != 1 ]]; then
      rm -f "$MOCK_ROOT/routine-account-present" \
        "$MOCK_ROOT/routine-must-change-password-present"
    fi
    printf 'deleted one user\n'
    ;;
  *"admin user delete --username localwms-agent"*)
    if [[ "${MOCK_COMPENSATION_DELETE_FAIL:-0}" == 1 ]]; then exit 3; fi
    if [[ "${MOCK_COMPENSATION_DELETE_LEAVES_ACCOUNT:-0}" != 1 ]]; then
      rm -f "$MOCK_ROOT/account-present" "$MOCK_ROOT/must-change-password-present"
    fi
    printf 'deleted one user\n'
    ;;
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
  *"admin user must-change-password --unset localwms-agent"*)
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

# Issue #227: dispatch on the exact API endpoint, never on a glob over the whole
# argv. The old `*"/api/v1/user"*` arm also swallowed /api/v1/users/<any third
# username> and then blocked forever in `read` on inherited stdin, which is an
# unbounded wait inside a required-CI script. Unknown URLs now fail closed
# before any stdin read, and the reads that remain are bounded.
output=''
url=''
argv=("$@")
index=0
while ((index < ${#argv[@]})); do
  case "${argv[index]}" in
    --output) output="${argv[index + 1]:-}"; index=$((index + 2)) ;;
    http://*|https://*) url="${argv[index]}"; index=$((index + 1)) ;;
    *) index=$((index + 1)) ;;
  esac
done

endpoint="${url#*/api/v1}"
if [[ -z "$url" || "$endpoint" == "$url" ]]; then
  printf 'MOCK_CURL_UNEXPECTED_URL: %s\n' "${url:-<none>}" >&2
  exit 2
fi

auth=''
require_config_header() {
  # The tool always pipes `--config -` payloads in. If a caller ever forgets,
  # fail in bounded time with a searchable marker instead of hanging forever.
  if ! IFS= read -r -t "${MOCK_CURL_STDIN_TIMEOUT:-10}" auth; then
    printf 'MOCK_CURL_MISSING_CONFIG_STDIN: %s\n' "$endpoint" >&2
    exit 3
  fi
}

case "$endpoint" in
  /users/newemaint-routine-merger)
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
  /users/localwms-agent)
    if [[ -f "$MOCK_ROOT/account-present" ]]; then
      [[ -n "$output" ]]
      identity="${MOCK_ACCOUNT_IDENTITY:-}"
      [[ -n "$identity" ]] || identity='{"login":"localwms-agent","is_admin":false}'
      printf '%s\n' "$identity" >"$output"
      printf 200
    else
      printf 404
    fi
    ;;
  /user)
    require_config_header
    if [[ "$auth" == *sentinel-routine-token* ]]; then
      [[ ! -e "$MOCK_ROOT/routine-must-change-password-present" ]]
      printf '{"login":"newemaint-routine-merger","is_admin":false}\n'
    else
      [[ "$auth" == *sentinel-generated-token* ]]
      [[ ! -e "$MOCK_ROOT/must-change-password-present" ]]
      printf '{"login":"localwms-agent","is_admin":false}\n'
    fi
    ;;
  /notifications)
    require_config_header
    [[ "$auth" == *sentinel-routine-token* ]]
    [[ -n "$output" ]]
    printf '{"message":"token does not have required scope, token scope=%s"}\n' \
      "${MOCK_ROUTINE_SCOPE:?routine scope mock must be set by the caller}" >"$output"
    printf 403
    ;;
  *)
    printf 'MOCK_CURL_UNEXPECTED_URL: %s\n' "$url" >&2
    exit 2
    ;;
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
# The routine PAT mock stands for a token Gitea actually issued, so it has to
# follow the manifest rather than a hand-written string: a scope set that
# cannot pass the broker identity gate must go red here too (#313).
MANIFEST_ROUTINE_SCOPES="$(jq -r '.routine_merge_agent_policy.token_scopes | join(",")' \
  "$ROOT/codex/config/gitea-governance.json")"
export MOCK_ROUTINE_SCOPE="$MANIFEST_ROUTINE_SCOPES"
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
sudo_config_count_before="$(line_count "$TMP/sudo-config-check.log")"
if AISOFT_ACCOUNT_BOOTSTRAP_MODE=not-authorized \
   AISOFT_CREDENTIAL_ROOT="$unauthorized_root" \
   bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
    --manifest "$ROOT/codex/config/gitea-governance.json" \
    --username localwms-agent \
    --token-kind project-agent \
    --credential-output "$unauthorized_root/localwms-agent-project-agent.token" \
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
[[ "$(line_count "$TMP/sudo-config-check.log")" == "$sudo_config_count_before" ]]

output="$TMP/credentials/localwms-agent-project-agent.token"
result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username localwms-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == created ]]
[[ "$(cat "$output")" == sentinel-generated-token ]]
mode="$(stat -c '%a' "$output" 2>/dev/null || stat -f '%Lp' "$output")"
[[ "$mode" == 600 ]]
[[ -f "$TMP/credentials/localwms-agent.account-created-by-issue-35" ]]
policy_marker="$TMP/credentials/localwms-agent.must-change-password-unset-by-issue-35"
[[ -f "$policy_marker" ]]
[[ "$(stat -c '%a' "$policy_marker" 2>/dev/null || stat -f '%Lp' "$policy_marker")" == 600 ]]
[[ -f "$TMP/credentials/localwms-agent-project-agent.token-created-by-issue-35" ]]
[[ "$(grep -c '^test -f ' "$TMP/sudo-config-check.log")" == 1 ]]
[[ "$(grep -c '^test -r ' "$TMP/sudo-config-check.log")" == 1 ]]
create_argv="$(grep 'admin user create' "$TMP/gitea-argv.log")"
[[ "$create_argv" == *"--user-type bot"* ]]
if [[ "$create_argv" == *"password"* ]]; then
  printf '%s\n' 'bot create argv must omit all password flags' >&2
  exit 1
fi
policy_argv="$(grep 'admin user must-change-password' "$TMP/gitea-argv.log")"
[[ "$policy_argv" == *"admin user must-change-password --unset localwms-agent"* ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 1 ]]

result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username localwms-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == no-op ]]
[[ "$(grep -c 'generate-access-token' "$TMP/gitea-argv.log")" == 1 ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 1 ]]

rm "$policy_marker"
touch "$TMP/must-change-password-present"
result="$(bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username localwms-agent \
  --token-kind project-agent \
  --credential-output "$output")"
[[ "$(jq -r '.result' <<<"$result")" == no-op ]]
[[ -f "$policy_marker" ]]
[[ "$(grep -c 'admin user must-change-password' "$TMP/gitea-argv.log")" == 2 ]]

chmod 644 "$policy_marker"
if bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --username localwms-agent \
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
[[ "$(jq -r '.observed_scopes' <<<"$routine_result")" == "$MANIFEST_ROUTINE_SCOPES" ]]
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

gitea_command_count() {
  local pattern="$1"
  grep -c -- "$pattern" "$TMP/gitea-argv.log" 2>/dev/null || true
}

new_account_root="$TMP/new-account-credentials"
mkdir -p "$new_account_root/projects/newemaint"
chmod 700 "$new_account_root" "$new_account_root/projects" \
  "$new_account_root/projects/newemaint"

new_account_tree_state() {
  local path
  while IFS= read -r path; do
    printf '%s %s ' "${path#"$new_account_root"}" \
      "$(stat -c '%a' "$path" 2>/dev/null || stat -f '%Lp' "$path")"
    if [[ -f "$path" ]]; then shasum -a 256 "$path"; else printf '\n'; fi
  done < <(find "$new_account_root" -mindepth 1 -print | LC_ALL=C sort)
}

assert_new_account_identity_compensated() {
  local variant="$1"
  local payload="$2"
  local state_before
  local create_before
  local delete_before
  local pat_before
  rm -f "$TMP/routine-account-present" \
    "$TMP/routine-must-change-password-present"
  state_before="$(new_account_tree_state)"
  create_before="$(gitea_command_count 'admin user create')"
  delete_before="$(gitea_command_count 'admin user delete')"
  pat_before="$(gitea_command_count 'generate-access-token')"
  if MOCK_ACCOUNT_IDENTITY="$payload" \
     AISOFT_CREDENTIAL_ROOT="$new_account_root" \
     bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
      --manifest "$ROOT/codex/config/gitea-governance.json" \
      --access-manifest "$ROOT/codex/config/host-access-broker.json" \
      --project-id newemaint \
      --username newemaint-routine-merger \
      --token-kind routine-merge-agent \
      --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
      --platform-root "$ROOT" \
      --credential-output "$new_account_root/projects/newemaint/routine-merge-agent.token" \
      >"$TMP/new-account-$variant.out" \
      2>"$TMP/new-account-$variant.err"; then
    printf 'unsafe newly created identity unexpectedly succeeded: %s\n' \
      "$variant" >&2
    exit 1
  fi
  grep -Fq 'compensated (create=1, delete=1, final account absent)' \
    "$TMP/new-account-$variant.err"
  [[ "$(gitea_command_count 'admin user create')" == "$((create_before + 1))" ]]
  [[ "$(gitea_command_count 'admin user delete')" == "$((delete_before + 1))" ]]
  [[ "$(gitea_command_count 'generate-access-token')" == "$pat_before" ]]
  [[ "$(new_account_tree_state)" == "$state_before" ]]
  [[ ! -e "$TMP/routine-account-present" ]]
}

assert_new_account_identity_compensated missing \
  '{"login":"newemaint-routine-merger"}'
assert_new_account_identity_compensated string-false \
  '{"login":"newemaint-routine-merger","is_admin":"false"}'
assert_new_account_identity_compensated number \
  '{"login":"newemaint-routine-merger","is_admin":0}'
assert_new_account_identity_compensated list \
  '{"login":"newemaint-routine-merger","is_admin":[]}'
assert_new_account_identity_compensated site-admin \
  '{"login":"newemaint-routine-merger","is_admin":true}'
assert_new_account_identity_compensated wrong-login \
  '{"login":"admin","is_admin":false}'
assert_new_account_identity_compensated root-list '[]'

assert_compensation_failure_blocks() {
  local variant="$1"
  local failure_variable="$2"
  local state_before
  local create_before
  local delete_before
  local pat_before
  rm -f "$TMP/routine-account-present" \
    "$TMP/routine-must-change-password-present"
  state_before="$(new_account_tree_state)"
  create_before="$(gitea_command_count 'admin user create')"
  delete_before="$(gitea_command_count 'admin user delete')"
  pat_before="$(gitea_command_count 'generate-access-token')"
  if env MOCK_ACCOUNT_IDENTITY='{"login":"newemaint-routine-merger","is_admin":true}' \
     "$failure_variable=1" AISOFT_CREDENTIAL_ROOT="$new_account_root" \
     bash "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
      --manifest "$ROOT/codex/config/gitea-governance.json" \
      --access-manifest "$ROOT/codex/config/host-access-broker.json" \
      --project-id newemaint \
      --username newemaint-routine-merger \
      --token-kind routine-merge-agent \
      --merged-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
      --platform-root "$ROOT" \
      --credential-output "$new_account_root/projects/newemaint/routine-merge-agent.token" \
      >"$TMP/new-account-$variant.out" \
      2>"$TMP/new-account-$variant.err"; then
    printf 'failed account compensation unexpectedly succeeded: %s\n' \
      "$variant" >&2
    exit 1
  fi
  grep -Fq 'manually verify' "$TMP/new-account-$variant.err"
  [[ "$(gitea_command_count 'admin user create')" == "$((create_before + 1))" ]]
  [[ "$(gitea_command_count 'admin user delete')" == "$((delete_before + 1))" ]]
  [[ "$(gitea_command_count 'generate-access-token')" == "$pat_before" ]]
  [[ "$(new_account_tree_state)" == "$state_before" ]]
  [[ -e "$TMP/routine-account-present" ]]
}

assert_compensation_failure_blocks delete-failed \
  MOCK_COMPENSATION_DELETE_FAIL
rm -f "$TMP/routine-account-present" "$TMP/routine-must-change-password-present"
assert_compensation_failure_blocks confirm-not-404 \
  MOCK_COMPENSATION_DELETE_LEAVES_ACCOUNT
rm -f "$TMP/routine-account-present" "$TMP/routine-must-change-password-present"

# Restore the existing-account fixture for the zero-mutation identity matrix.
touch "$TMP/routine-account-present"

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
grep -Fq 'routine PAT scope must equal the manifest set including read:user' \
  "$TMP/routine-scope-negative.err"
export MOCK_ROUTINE_SCOPE="$MANIFEST_ROUTINE_SCOPES"

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

# Issue #227 AC-4: the deadline watchdog must actually bound an injected hang.
# The child blocks in open() on a partnerless FIFO, the same syscall the outage
# was stuck in, and must die with a searchable marker well inside the deadline.
guard_log="$TMP/deadline-guard.log"
guard_started="$(date +%s)"
if AISOFT_TEST_SELFTEST_HANG=1 AISOFT_TEST_DEADLINE_SECONDS=5 \
   bash "$ROOT/codex/tests/test-bootstrap-gitea-service-account.sh" \
   >"$guard_log" 2>&1; then
  printf '%s\n' 'deadline watchdog did not fail an injected hang' >&2
  exit 1
fi
guard_elapsed=$(( $(date +%s) - guard_started ))
if ((guard_elapsed > 60)); then
  printf 'deadline watchdog took %ss, which is not a bounded failure\n' "$guard_elapsed" >&2
  exit 1
fi
grep -Fq 'AISOFT_TEST_DEADLINE_EXCEEDED' "$guard_log"

printf '%s\n' 'bootstrap Gitea service account tests passed'
