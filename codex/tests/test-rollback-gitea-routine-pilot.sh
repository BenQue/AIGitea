#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/credentials/manager" \
  "$TMP/credentials/projects/newemaint" "$TMP/protected"
chmod 700 "$TMP/credentials" "$TMP/credentials/manager" \
  "$TMP/credentials/projects" "$TMP/credentials/projects/newemaint"
touch "$TMP/protected/gitea.ini" "$TMP/snapshot.json"
chmod 600 "$TMP/protected/gitea.ini" "$TMP/snapshot.json"

jq '(.repositories[] | select(.name == "NewEMaint") |
  .routine_auto_merge_enabled) = false' \
  "$ROOT/codex/config/gitea-governance.json" >"$TMP/disabled.json"

cat >"$TMP/bin/python3" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/python.log"
case "$*" in
  *"aisoft_host_access.cli"*"validate"*) printf '{}\n' ;;
  *"aisoft_gitea_governance.cli"*"verify-merged"*) printf '{"result":"PASS"}\n' ;;
  *"aisoft_gitea_governance.cli"*" rollback "*)
    printf '{"result":"rollback-applied"}\n'
    ;;
  *"aisoft_gitea_governance.cli"*" check "*)
    printf '%s\n' '{
      "result":"PASS",
      "cross_project_write_violations":[],
      "repositories":[{
        "planned_actions":[],"blockers":[],
        "expected":{"routine_auto_merge_enabled":false,"merge_allowlist_usernames":["admin"]},
        "current":{
          "collaborators":{"newemaint-routine-merger":"missing"},
          "protection":{"merge_whitelist_usernames":["admin"]}
        }
      }],
      "routine_accounts":[{"state":"present-non-admin"}]
    }'
    ;;
  *) exit 2 ;;
esac
MOCK

cat >"$TMP/bin/git" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  *"merge-base --is-ancestor"*) exit 0 ;;
  *"show "*) cat "$MOCK_ROLLOUT_MANIFEST" ;;
  *) exit 2 ;;
esac
MOCK

cat >"$TMP/bin/sudo" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[[ "$1" == -n && "$2" == -u && "$3" == git ]]
shift 3
if [[ "$1" == test ]]; then exit 0; fi
printf '%s\n' "$*" >>"$MOCK_ROOT/gitea.log"
[[ "$*" == *"admin user delete --username newemaint-routine-merger"* ]]
touch "$MOCK_ROOT/account-deleted"
MOCK

cat >"$TMP/bin/gitea" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK

cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_ROOT/curl.log"
output=''
url="${!#}"
for ((index=1; index<=$#; index++)); do
  if [[ "${!index}" == --output ]]; then
    next=$((index + 1)); output="${!next}"
  fi
done
if [[ "$url" == */api/v1/token ]]; then
  read -r auth
  read -r request
  [[ "$auth" == *sentinel-routine-token* && "$request" == *DELETE* ]]
  printf 204
elif [[ "$url" == */api/v1/user ]]; then
  read -r auth
  [[ "$auth" == *sentinel-routine-token* ]]
  printf 401
elif [[ "$url" == */api/v1/users/newemaint-routine-merger ]]; then
  if [[ -f "$MOCK_ROOT/account-deleted" ]]; then
    printf 404
  else
    [[ -n "$output" ]]
    identity="${MOCK_ACCOUNT_IDENTITY:-}"
    [[ -n "$identity" ]] || identity='{"login":"newemaint-routine-merger","is_admin":false}'
    printf '%s\n' "$identity" >"$output"
    printf 200
  fi
else
  exit 2
fi
MOCK

chmod +x "$TMP/bin/"*
export MOCK_ROOT="$TMP"
export MOCK_ROLLOUT_MANIFEST="$ROOT/codex/config/gitea-governance.json"
export PATH="$TMP/bin:$PATH"
export AISOFT_ROUTINE_ROLLBACK_MODE=approved-issue-213
export AISOFT_CREDENTIAL_ROOT="$TMP/credentials"
export GITEA_BIN="$TMP/bin/gitea"
export GITEA_CONFIG="$TMP/protected/gitea.ini"
export GITEA_LOCAL_URL=http://127.0.0.1:3000
printf 'manager-token\n' >"$TMP/credentials/manager/mutation.token"
chmod 600 "$TMP/credentials/manager/mutation.token"

prepare_managed_files() {
  local root="$TMP/credentials/projects/newemaint"
  printf 'sentinel-routine-token\n' >"$root/routine-merge-agent.token"
  printf 'issue=213\nusername=newemaint-routine-merger\ntoken_kind=routine-merge-agent\n' \
    >"$root/routine-merge-agent.token-created-by-issue-213"
  printf 'issue=213\nusername=newemaint-routine-merger\n' \
    >"$root/newemaint-routine-merger.account-created-by-issue-213"
  printf 'issue=213\nusername=newemaint-routine-merger\npolicy=must-change-password-unset\n' \
    >"$root/newemaint-routine-merger.must-change-password-unset-by-issue-213"
  chmod 600 "$root/"*
}

prepare_managed_files
receipt="$(bash "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
  --manifest "$TMP/disabled.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --platform-root "$ROOT" \
  --merged-sha bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
  --rollout-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --snapshot "$TMP/snapshot.json")"
[[ "$(jq -r '.result' <<<"$receipt")" == rollback-accepted ]]
[[ "$(jq -r '.account_policy' <<<"$receipt")" == retain ]]
[[ "$(jq -r '.account_state' <<<"$receipt")" == present-non-admin ]]
[[ "$(jq -r '.revoke_mutation_count' <<<"$receipt")" == 1 ]]
[[ "$(jq -r '.fallback_count' <<<"$receipt")" == 0 ]]
[[ ! -e "$TMP/credentials/projects/newemaint/routine-merge-agent.token" ]]
[[ -e "$TMP/credentials/projects/newemaint/newemaint-routine-merger.account-created-by-issue-213" ]]

prepare_managed_files
rm -f "$TMP/account-deleted"
receipt="$(bash "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
  --manifest "$TMP/disabled.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --platform-root "$ROOT" \
  --merged-sha bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
  --rollout-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --snapshot "$TMP/snapshot.json" --account-policy delete)"
[[ "$(jq -r '.account_policy' <<<"$receipt")" == delete ]]
[[ "$(jq -r '.account_state' <<<"$receipt")" == missing ]]
[[ "$(jq -r '.account_delete_mutation_count' <<<"$receipt")" == 1 ]]
grep -Fq 'admin user delete --username newemaint-routine-merger' "$TMP/gitea.log"
if grep -Fq -- '--purge' "$TMP/gitea.log" ||
   grep -F -- '--username ' "$TMP/gitea.log" |
     grep -Fvq -- '--username newemaint-routine-merger'; then
  printf '%s\n' 'unsafe account deletion surface detected' >&2
  exit 1
fi

line_count() {
  local path="$1"
  if [[ -f "$path" ]]; then
    wc -l <"$path" | tr -d ' '
  else
    printf '0\n'
  fi
}

rollback_call_count() {
  awk '/ rollback / {count += 1} END {print count + 0}' "$TMP/python.log"
}

managed_rollback_state() {
  local root="$TMP/credentials/projects/newemaint"
  local path
  while IFS= read -r path; do
    printf '%s %s ' "${path#"$root"}" \
      "$(stat -c '%a' "$path" 2>/dev/null || stat -f '%Lp' "$path")"
    if [[ -f "$path" ]]; then shasum -a 256 "$path"; else printf '\n'; fi
  done < <(find "$root" -mindepth 1 -print | LC_ALL=C sort)
}

assert_account_identity_rejected() {
  local policy="$1"
  local variant="$2"
  local payload="$3"
  local state_before
  local gitea_before
  local rollback_before
  prepare_managed_files
  rm -f "$TMP/account-deleted"
  state_before="$(managed_rollback_state)"
  gitea_before="$(line_count "$TMP/gitea.log")"
  rollback_before="$(rollback_call_count)"
  if MOCK_ACCOUNT_IDENTITY="$payload" \
     bash "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
      --manifest "$TMP/disabled.json" \
      --access-manifest "$ROOT/codex/config/host-access-broker.json" \
      --platform-root "$ROOT" \
      --merged-sha bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
      --rollout-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
      --snapshot "$TMP/snapshot.json" --account-policy "$policy" \
      >"$TMP/account-identity-$policy-$variant.out" \
      2>"$TMP/account-identity-$policy-$variant.err"; then
    printf 'unsafe routine identity unexpectedly allowed %s rollback: %s\n' \
      "$policy" "$variant" >&2
    exit 1
  fi
  grep -Fq 'routine account preflight read-back must be the exact non-admin service identity' \
    "$TMP/account-identity-$policy-$variant.err"
  [[ "$(line_count "$TMP/gitea.log")" == "$gitea_before" ]]
  [[ "$(rollback_call_count)" == "$rollback_before" ]]
  [[ "$(managed_rollback_state)" == "$state_before" ]]
  [[ ! -e "$TMP/account-deleted" ]]
}

for policy in retain delete; do
  assert_account_identity_rejected "$policy" missing \
    '{"login":"newemaint-routine-merger"}'
  assert_account_identity_rejected "$policy" string-false \
    '{"login":"newemaint-routine-merger","is_admin":"false"}'
  assert_account_identity_rejected "$policy" number \
    '{"login":"newemaint-routine-merger","is_admin":0}'
  assert_account_identity_rejected "$policy" list \
    '{"login":"newemaint-routine-merger","is_admin":[]}'
  assert_account_identity_rejected "$policy" site-admin \
    '{"login":"newemaint-routine-merger","is_admin":true}'
  assert_account_identity_rejected "$policy" wrong-login \
    '{"login":"admin","is_admin":false}'
  assert_account_identity_rejected "$policy" root-list '[]'
done

assert_password_marker_delete_rejected() {
  local variant="$1"
  local gitea_before
  local rollback_before
  gitea_before="$(line_count "$TMP/gitea.log")"
  rollback_before="$(rollback_call_count)"
  if bash "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
    --manifest "$TMP/disabled.json" \
    --access-manifest "$ROOT/codex/config/host-access-broker.json" \
    --platform-root "$ROOT" \
    --merged-sha bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
    --rollout-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
    --snapshot "$TMP/snapshot.json" --account-policy delete \
    >"$TMP/password-marker-$variant.out" \
    2>"$TMP/password-marker-$variant.err"; then
    printf 'unsafe password-policy marker unexpectedly allowed delete: %s\n' \
      "$variant" >&2
    exit 1
  fi
  grep -Fq 'password-policy ownership marker' \
    "$TMP/password-marker-$variant.err"
  [[ "$(line_count "$TMP/gitea.log")" == "$gitea_before" ]]
  [[ "$(rollback_call_count)" == "$rollback_before" ]]
  [[ ! -e "$TMP/account-deleted" ]]
}

password_marker="$TMP/credentials/projects/newemaint/newemaint-routine-merger.must-change-password-unset-by-issue-213"
prepare_managed_files
rm -f "$TMP/account-deleted"
chmod 644 "$password_marker"
assert_password_marker_delete_rejected unsafe-mode

prepare_managed_files
rm -f "$TMP/account-deleted"
printf '\n' >>"$password_marker"
assert_password_marker_delete_rejected unsafe-content

if bash "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
  --manifest "$ROOT/codex/config/gitea-governance.json" \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --platform-root "$ROOT" \
  --merged-sha bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
  --rollout-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --snapshot "$TMP/snapshot.json" >"$TMP/enabled.out" 2>"$TMP/enabled.err"; then
  printf '%s\n' 'enabled pilot source unexpectedly allowed rollback' >&2
  exit 1
fi
grep -Fq 'merged source must disable the exact NewEMaint pilot first' "$TMP/enabled.err"

if grep -Fq sentinel-routine-token "$TMP/python.log" ||
   grep -Fq sentinel-routine-token "$TMP/gitea.log" ||
   grep -Fq sentinel-routine-token <<<"$receipt"; then
  printf '%s\n' 'routine token leaked through argv or receipt' >&2
  exit 1
fi

printf '%s\n' 'routine pilot rollback tests passed'
