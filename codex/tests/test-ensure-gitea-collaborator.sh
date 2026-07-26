#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/codex/tools/ensure-gitea-collaborator.sh"
ADMIN_SENTINEL='ADMIN_TOKEN_MUST_NOT_LEAK_6d94d4'
BOT_SENTINEL='BOT_TOKEN_MUST_NOT_LEAK_7e15a2'
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

mkdir -p "$TMP/bin"
: >"$TMP/argv.log"
: >"$TMP/calls.log"

cat >"$TMP/bin/curl" <<'MOCK_CURL'
#!/usr/bin/env bash
set -euo pipefail

auth_line=''
IFS= read -r auth_line
case "$auth_line" in
  *"$MOCK_ADMIN_SENTINEL"*) role=admin ;;
  *"$MOCK_BOT_SENTINEL"*) role=bot ;;
  *)
    echo 'curl mock received an unknown credential' >&2
    exit 97
    ;;
esac

method=GET
output_file=''
payload=''
endpoint=''
previous=''
for argument in "$@"; do
  printf '%s\n' "$argument" >>"$MOCK_ARGV_LOG"
  case "$previous" in
    --request) method="$argument" ;;
    --output) output_file="$argument" ;;
    --data) payload="$argument" ;;
  esac
  case "$argument" in
    http://*|https://*) endpoint="$argument" ;;
  esac
  previous="$argument"
done

[[ -n "$output_file" && -n "$endpoint" ]] || {
  echo 'curl mock did not receive output file and endpoint' >&2
  exit 96
}

printf '%s %s %s\n' "$role" "$method" "$endpoint" >>"$MOCK_CALLS_LOG"

respond() {
  local status="$1"
  local body="$2"
  printf '%s\n' "$body" >"$output_file"
  printf '%s' "$status"
}

permission="$(jq -r '.permission' "$MOCK_STATE")"
bot_access="$(jq -r '.bot_access' "$MOCK_STATE")"
puts="$(jq -r '.puts' "$MOCK_STATE")"

case "$method $endpoint" in
  "GET http://mock.gitea.invalid/api/v1/repos/owner/repo")
    if [[ "$role" == bot &&
      ("$permission" != write || "$bot_access" != true) ]]; then
      respond 403 '{}'
    else
      respond 200 \
        '{"full_name":"owner/repo","default_branch":"main","private":true}'
    fi
    ;;
  "GET http://mock.gitea.invalid/api/v1/repos/owner/repo/collaborators/ci-bot/permission")
    if [[ "$role" == bot &&
      ("$permission" != write || "$bot_access" != true) ]]; then
      respond 403 '{}'
    elif [[ "$permission" == missing ]]; then
      respond 404 '{}'
    else
      respond 200 "{\"permission\":\"$permission\",\"role_name\":\"$permission\"}"
    fi
    ;;
  "PUT http://mock.gitea.invalid/api/v1/repos/owner/repo/collaborators/ci-bot")
    [[ "$role" == admin ]] || {
      respond 403 '{}'
      exit 0
    }
    [[ "$payload" == '{"permission":"write"}' ]] || {
      echo 'unexpected collaborator payload' >&2
      exit 95
    }
    jq '.permission = "write" | .puts += 1' \
      "$MOCK_STATE" >"$MOCK_STATE.next"
    mv "$MOCK_STATE.next" "$MOCK_STATE"
    respond 204 ''
    ;;
  "GET http://mock.gitea.invalid/api/v1/repos/owner/repo/branch_protections/main")
    if [[ "$role" == bot &&
      ("$permission" != write || "$bot_access" != true) ]]; then
      respond 403 '{}'
    elif [[ "$(jq -r '.protection_exists' "$MOCK_STATE")" != true ]]; then
      respond 404 '{}'
    elif [[ "$(jq -r '.change_protection_after_put' "$MOCK_STATE")" == true &&
      "$puts" -gt 0 ]]; then
      jq '.protection.enable_force_push = true | .protection' \
        "$MOCK_STATE" >"$output_file"
      printf '200'
    else
      jq '.protection' "$MOCK_STATE" >"$output_file"
      printf '200'
    fi
    ;;
  *)
    respond 404 '{}'
    ;;
esac
MOCK_CURL
chmod +x "$TMP/bin/curl"

cat >"$TMP/profile.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_TOKEN=$BOT_SENTINEL
EOF
cat >"$TMP/admin.credentials" <<EOF
admin token: $ADMIN_SENTINEL
EOF
chmod 600 "$TMP/profile.env" "$TMP/admin.credentials"

reset_state() {
  local permission="$1"
  local bot_access="${2:-true}"
  local protection_exists="${3:-true}"
  local change_after_put="${4:-false}"
  jq -n \
    --arg permission "$permission" \
    --argjson bot_access "$bot_access" \
    --argjson protection_exists "$protection_exists" \
    --argjson change_after_put "$change_after_put" \
    '{
      permission: $permission,
      bot_access: $bot_access,
      protection_exists: $protection_exists,
      change_protection_after_put: $change_after_put,
      puts: 0,
      protection: {
        rule_name: "main",
        branch_name: "main",
        enable_push: false,
        enable_push_whitelist: false,
        push_whitelist_deploy_keys: false,
        push_whitelist_usernames: [],
        push_whitelist_teams: [],
        enable_force_push: false,
        enable_force_push_allowlist: false,
        force_push_allowlist_deploy_keys: false,
        force_push_allowlist_usernames: [],
        force_push_allowlist_teams: [],
        enable_status_check: true,
        status_check_contexts: ["CI / test (pull_request)"],
        required_approvals: 0,
        dismiss_stale_approvals: false,
        ignore_stale_approvals: false,
        block_on_rejected_reviews: false,
        block_on_outdated_branch: false,
        block_on_official_review_requests: false,
        enable_approvals_whitelist: false,
        approvals_whitelist_username: [],
        approvals_whitelist_teams: [],
        enable_merge_whitelist: true,
        merge_whitelist_usernames: ["admin"],
        merge_whitelist_teams: [],
        block_admin_merge_override: false,
        require_signed_commits: false,
        protected_file_patterns: "",
        unprotected_file_patterns: ""
      }
    }' >"$TMP/state.json"
  : >"$TMP/calls.log"
}

run_tool() {
  local stdout_file="$1"
  local stderr_file="$2"
  shift 2
  PATH="$TMP/bin:$PATH" \
    AGENT_ENV_FILE="$TMP/profile.env" \
    GITEA_EXPECT_URL=http://mock.gitea.invalid \
    GITEA_EXPECT_OWNER=owner \
    GITEA_EXPECT_REPO=repo \
    GITEA_ADMIN_CREDENTIAL_FILE="$TMP/admin.credentials" \
    AISOFT_ONBOARDING_MODE=software-repository \
    MOCK_ADMIN_SENTINEL="$ADMIN_SENTINEL" \
    MOCK_BOT_SENTINEL="$BOT_SENTINEL" \
    MOCK_STATE="$TMP/state.json" \
    MOCK_ARGV_LOG="$TMP/argv.log" \
    MOCK_CALLS_LOG="$TMP/calls.log" \
    bash -x "$SCRIPT" "$@" >"$stdout_file" 2>"$stderr_file"
}

assert_blocked() {
  local stdout_file="$1"
  local stderr_file="$2"
  shift 2
  if run_tool "$stdout_file" "$stderr_file" "$@"; then
    echo 'expected BLOCKED_EXTERNAL failure' >&2
    exit 1
  fi
  grep -Fq 'BLOCKED_EXTERNAL:' "$stderr_file"
}

reset_state missing
run_tool "$TMP/missing.stdout" "$TMP/missing.stderr"
grep -Fq 'permission=write action=added' "$TMP/missing.stdout"
[[ "$(jq -r '.permission' "$TMP/state.json")" == write ]]
[[ "$(jq -r '.puts' "$TMP/state.json")" == 1 ]]

run_tool "$TMP/repeat.stdout" "$TMP/repeat.stderr"
grep -Fq 'permission=write action=unchanged' "$TMP/repeat.stdout"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 1 ]]

reset_state read
run_tool "$TMP/read.stdout" "$TMP/read.stderr"
grep -Fq 'permission=write action=updated' "$TMP/read.stdout"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 1 ]]

reset_state write
run_tool "$TMP/write.stdout" "$TMP/write.stderr"
grep -Fq 'permission=write action=unchanged' "$TMP/write.stdout"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 0 ]]

reset_state missing
run_tool "$TMP/check.stdout" "$TMP/check.stderr" --check
grep -Fq \
  'current_permission=missing planned_action=add-write main_protection=verified onboarding_gate=ready mode=check' \
  "$TMP/check.stdout"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 0 ]]
if grep -Fq 'bot ' "$TMP/calls.log"; then
  echo 'check mode must not require or use the bot credential' >&2
  exit 1
fi

reset_state admin
assert_blocked "$TMP/admin.stdout" "$TMP/admin.stderr"
grep -Fq 'manual downgrade is required' "$TMP/admin.stderr"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 0 ]]

reset_state owner
assert_blocked "$TMP/unknown.stdout" "$TMP/unknown.stderr"
grep -Fq 'unknown permission level' "$TMP/unknown.stderr"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 0 ]]

reset_state missing false
assert_blocked "$TMP/bot-fail.stdout" "$TMP/bot-fail.stderr"
grep -Fq 'ci-bot repository access failed' "$TMP/bot-fail.stderr"

reset_state missing true false
assert_blocked "$TMP/no-protection.stdout" "$TMP/no-protection.stderr"
grep -Fq 'main branch protection does not enforce' \
  "$TMP/no-protection.stderr"
[[ "$(jq -r '.puts' "$TMP/state.json")" == 0 ]]

reset_state missing true true true
assert_blocked "$TMP/changed-protection.stdout" "$TMP/changed-protection.stderr"
grep -Fq 'main branch protection does not enforce' \
  "$TMP/changed-protection.stderr"

reset_state write
jq '.protection.enable_merge_whitelist = false' \
  "$TMP/state.json" >"$TMP/state.next"
mv "$TMP/state.next" "$TMP/state.json"
assert_blocked "$TMP/unsafe-protection.stdout" "$TMP/unsafe-protection.stderr"
grep -Fq 'main branch protection does not enforce' \
  "$TMP/unsafe-protection.stderr"

run_tool "$TMP/unsafe-check.stdout" "$TMP/unsafe-check.stderr" --check
grep -Fq \
  'current_permission=write planned_action=none main_protection=blocked onboarding_gate=blocked mode=check' \
  "$TMP/unsafe-check.stdout"

reset_state write
chmod 644 "$TMP/admin.credentials"
assert_blocked "$TMP/mode.stdout" "$TMP/mode.stderr"
grep -Fq 'mode 400 or 600' "$TMP/mode.stderr"
chmod 600 "$TMP/admin.credentials"

reset_state write
if PATH="$TMP/bin:$PATH" \
  AGENT_ENV_FILE="$TMP/profile.env" \
  GITEA_EXPECT_URL=http://mock.gitea.invalid \
  GITEA_EXPECT_OWNER=wrong-owner \
  GITEA_EXPECT_REPO=repo \
  GITEA_ADMIN_CREDENTIAL_FILE="$TMP/admin.credentials" \
  AISOFT_ONBOARDING_MODE=software-repository \
  bash -x "$SCRIPT" >"$TMP/target.stdout" 2>"$TMP/target.stderr"; then
  echo 'target mismatch must fail' >&2
  exit 1
fi
grep -Fq 'BLOCKED_EXTERNAL:' "$TMP/target.stderr"
grep -Fq 'expected target' "$TMP/target.stderr"

reset_state write
if PATH="$TMP/bin:$PATH" \
  AGENT_ENV_FILE="$TMP/profile.env" \
  GITEA_EXPECT_URL=http://mock.gitea.invalid \
  GITEA_EXPECT_OWNER=owner \
  GITEA_EXPECT_REPO=repo \
  GITEA_ADMIN_CREDENTIAL_FILE="$TMP/admin.credentials" \
  bash -x "$SCRIPT" >"$TMP/mode-gate.stdout" 2>"$TMP/mode-gate.stderr"; then
  echo 'explicit software-repository onboarding mode must be required' >&2
  exit 1
fi
grep -Fq 'BLOCKED_EXTERNAL:' "$TMP/mode-gate.stderr"
grep -Fq 'AISOFT_ONBOARDING_MODE=software-repository is required' \
  "$TMP/mode-gate.stderr"

if rg -F "$ADMIN_SENTINEL" "$TMP/argv.log" "$TMP"/*.stdout "$TMP"/*.stderr ||
  rg -F "$BOT_SENTINEL" "$TMP/argv.log" "$TMP"/*.stdout "$TMP"/*.stderr; then
  echo 'credential sentinel leaked through argv, stdout, or stderr' >&2
  exit 1
fi

printf '%s\n' 'ensure-gitea-collaborator tests passed'
