#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
CHECKER="$ROOT/codex/tools/aisoft-project-check.sh"
SENTINEL='PROJECT_CHECK_TOKEN_MUST_NOT_LEAK_106'
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

case_count=0
last_output=''

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

run_case() {
  local expected_status="$1"
  shift
  case_count=$((case_count + 1))
  set +e
  "$@" >"$TMP/case.stdout" 2>"$TMP/case.stderr"
  actual_status=$?
  set -e
  last_output="$(cat "$TMP/case.stdout" "$TMP/case.stderr")"
  if [[ "$actual_status" != "$expected_status" ]]; then
    safe_output="${last_output//$SENTINEL/[REDACTED]}"
    printf '%s\n' "$safe_output" >&2
    fail "case $case_count expected status $expected_status, got $actual_status"
  fi
}

expect_line() {
  local expected="$1"
  grep -Fqx "$expected" <<<"$last_output" ||
    fail "case $case_count missing line: $expected"
}

expect_contains() {
  local expected="$1"
  grep -Fq "$expected" <<<"$last_output" ||
    fail "case $case_count missing text: $expected"
}

make_aligned_repo() {
  local repo="$1"
  mkdir -p "$repo/docs/changes/_template" "$repo/.aisoft"
  awk '
    /^# AGENTS\.md · <项目名>$/ {
      print "# AGENTS.md · TestProject"
      next
    }
    /^  <docker-release\/v2/ {
      print "  docker-release/v2;"
      next
    }
    { print }
  ' "$ROOT/templates/project/AGENTS.md" >"$repo/AGENTS.md"
  cp "$ROOT/templates/project/CLAUDE.md" "$repo/CLAUDE.md"
  for document in summary spec plan verification; do
    cp "$ROOT/templates/docs/changes/_template/$document.md" \
      "$repo/docs/changes/_template/$document.md"
  done
  cp "$ROOT/architecture/reference/sqlite/architecture.json" \
    "$repo/.aisoft/architecture.json"
  cp "$ROOT/architecture/reference/sqlite/architecture.lock.json" \
    "$repo/.aisoft/architecture.lock.json"
  git -C "$repo" init -b main >/dev/null
  git -C "$repo" config user.name project-check-test
  git -C "$repo" config user.email project-check@example.invalid
  git -C "$repo" add .
  git -C "$repo" commit -m fixture >/dev/null
}

copy_fixture() {
  local name="$1"
  local destination="$TMP/$name"
  cp -R "$TMP/aligned" "$destination"
  printf '%s' "$destination"
}

mkdir -p "$TMP/bin"
cat >"$TMP/bin/curl" <<'MOCK_CURL'
#!/usr/bin/env bash
set -euo pipefail

args=("$@")
output_file=''
url=''
consume_config=false
index=0
for argument in "${args[@]}"; do
  printf '%s\n' "$argument" >>"$MOCK_ARGV_LOG"
done
while ((index < ${#args[@]})); do
  argument="${args[$index]}"
  case "$argument" in
    --config)
      index=$((index + 1))
      [[ "${args[$index]}" == '-' ]] && consume_config=true
      ;;
    --output)
      index=$((index + 1))
      output_file="${args[$index]}"
      ;;
    http://*|https://*) url="$argument" ;;
  esac
  index=$((index + 1))
done

[[ "$consume_config" == true && -n "$output_file" && -n "$url" ]] || exit 91
saw_token=false
while IFS= read -r config_line; do
  [[ "$config_line" == *"$MOCK_SENTINEL"* ]] && saw_token=true
done
[[ "$saw_token" == true ]] || exit 92

case "$url" in
  */labels\?*)
    if [[ "${MOCK_TRANSPORT_FAIL:-0}" == 1 ]]; then
      echo 'curl mock transport failure' >&2
      exit 7
    fi
    cp "$MOCK_LABELS" "$output_file"
    printf '200'
    ;;
  */branch_protections/main)
    if [[ "${MOCK_PROTECTION_STATUS:-200}" == 403 ]]; then
      printf '{}\n' >"$output_file"
      printf '403'
    else
      cp "$MOCK_PROTECTION" "$output_file"
      printf '200'
    fi
    ;;
  *) exit 93 ;;
esac
MOCK_CURL
chmod +x "$TMP/bin/curl"

cat >"$TMP/agent.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=NewEMaint
GITEA_TOKEN=$SENTINEL
EOF
chmod 600 "$TMP/agent.env"
: >"$TMP/curl.argv"
cp "$ROOT/codex/config/gitea-labels.json" "$TMP/labels.json"
jq -n '{
  enable_push: false,
  enable_status_check: true,
  status_check_contexts: ["CI / verify (pull_request)"]
}' >"$TMP/protection.json"

remote_check() {
  env \
    PATH="$TMP/bin:$PATH" \
    AGENT_ENV_FILE="${MOCK_ENV_FILE:-$TMP/agent.env}" \
    MOCK_ARGV_LOG="$TMP/curl.argv" \
    MOCK_LABELS="$TMP/labels.json" \
    MOCK_PROTECTION="$TMP/protection.json" \
    MOCK_SENTINEL="$SENTINEL" \
    MOCK_PROTECTION_STATUS="${MOCK_PROTECTION_STATUS:-200}" \
    MOCK_TRANSPORT_FAIL="${MOCK_TRANSPORT_FAIL:-0}" \
    bash "$CHECKER" --today 2026-08-12 "$@"
}

local_check() {
  bash "$CHECKER" --today 2026-08-12 "$@"
}

make_aligned_repo "$TMP/aligned"

run_case 0 remote_check --repo "$TMP/aligned" --remote
for check_id in pointer-sections change-templates architecture-lock labels-readback ci-context delivery-profile; do
  expect_line "PASS: $check_id"
done
expect_line 'result: pass=6 gap=0 skip=0'
expect_contains 'DEPRECATED: inline GITEA_TOKEN is deprecated'

# Token-file profile (#111): the remote checks must run when the env file only
# provides GITEA_TOKEN_FILE (post-#61 migrated profile shape).
printf '%s\n' "$SENTINEL" >"$TMP/agent.token"
chmod 600 "$TMP/agent.token"
cat >"$TMP/agent-file.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=NewEMaint
GITEA_TOKEN_FILE=$TMP/agent.token
EOF
chmod 600 "$TMP/agent-file.env"
MOCK_ENV_FILE="$TMP/agent-file.env" \
  run_case 0 remote_check --repo "$TMP/aligned" --remote
expect_line 'PASS: labels-readback'
expect_line 'PASS: ci-context'
expect_line 'result: pass=6 gap=0 skip=0'
if grep -Fq 'DEPRECATED' <<<"$last_output"; then
  fail 'token-file profile must not print the deprecation notice'
fi

# Permissive token file fails the remote gate closed with an explicit reason.
chmod 644 "$TMP/agent.token"
MOCK_ENV_FILE="$TMP/agent-file.env" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'GAP: labels-readback — GITEA_TOKEN_FILE 未通过安全闸门'
expect_line 'GAP: ci-context — GITEA_TOKEN_FILE 未通过安全闸门'
chmod 600 "$TMP/agent.token"

# Missing both token forms reports the full accepted configuration set.
cat >"$TMP/agent-missing.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=NewEMaint
EOF
chmod 600 "$TMP/agent-missing.env"
MOCK_ENV_FILE="$TMP/agent-missing.env" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'GAP: labels-readback — 远程配置缺失: GITEA_TOKEN_FILE 或 GITEA_TOKEN'
expect_line 'GAP: ci-context — 远程配置缺失: GITEA_TOKEN_FILE 或 GITEA_TOKEN'

pointer_repo="$(copy_fixture pointer-gap)"
awk '
  !changed && /本仓库由 AISoft 平台治理/ {
    print "本仓库的平台指针发生漂移。"
    changed = 1
    next
  }
  { print }
' "$pointer_repo/AGENTS.md" >"$pointer_repo/AGENTS.md.next"
mv "$pointer_repo/AGENTS.md.next" "$pointer_repo/AGENTS.md"
run_case 1 local_check --repo "$pointer_repo"
expect_contains 'GAP: pointer-sections —'

template_repo="$(copy_fixture template-gap)"
printf '\n# drift\n' >>"$template_repo/docs/changes/_template/spec.md"
run_case 1 local_check --repo "$template_repo"
expect_contains 'GAP: change-templates —'

architecture_repo="$(copy_fixture architecture-gap)"
printf '{\n' >"$architecture_repo/.aisoft/architecture.json"
run_case 1 local_check --repo "$architecture_repo"
expect_contains 'GAP: architecture-lock —'

uncommitted_lock_repo="$(copy_fixture uncommitted-lock)"
printf '\n' >>"$uncommitted_lock_repo/.aisoft/architecture.lock.json"
run_case 1 local_check --repo "$uncommitted_lock_repo"
expect_line 'GAP: architecture-lock — .aisoft/architecture.lock.json 存在未提交变更'

labels_repo="$(copy_fixture labels-gap)"
jq '.[1:]' "$ROOT/codex/config/gitea-labels.json" >"$TMP/labels.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback —'

jq '.[0].color = "ffffff"' "$ROOT/codex/config/gitea-labels.json" >"$TMP/labels.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback —'

jq '. + [{name:"complexity/standard",color:"ffffff",description:"conflict"}]' \
  "$ROOT/codex/config/gitea-labels.json" >"$TMP/labels.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback —'

cp "$ROOT/codex/config/gitea-labels.json" "$TMP/labels.json"
jq '.status_check_contexts = ["wrong"]' "$TMP/protection.json" \
  >"$TMP/protection.next"
mv "$TMP/protection.next" "$TMP/protection.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: ci-context —'

jq -n '{enable_push:true,enable_status_check:true,status_check_contexts:["CI / verify (pull_request)"]}' \
  >"$TMP/protection.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: ci-context —'

jq -n '{enable_push:false,enable_status_check:true,status_check_contexts:["CI / verify (pull_request)"]}' \
  >"$TMP/protection.json"
delivery_repo="$(copy_fixture delivery-gap)"
sed 's|  docker-release/v2;|  <delivery-profile>;|' "$delivery_repo/AGENTS.md" \
  >"$delivery_repo/AGENTS.md.next"
mv "$delivery_repo/AGENTS.md.next" "$delivery_repo/AGENTS.md"
run_case 1 local_check --repo "$delivery_repo"
expect_contains 'GAP: delivery-profile —'

custom_delivery_repo="$(copy_fixture custom-delivery)"
sed 's|  docker-release/v2;|  systemd service;|' "$custom_delivery_repo/AGENTS.md" \
  >"$custom_delivery_repo/AGENTS.md.next"
mv "$custom_delivery_repo/AGENTS.md.next" "$custom_delivery_repo/AGENTS.md"
run_case 0 local_check --repo "$custom_delivery_repo"
expect_line 'PASS: delivery-profile'

heading_boundary_repo="$(copy_fixture heading-boundary)"
sed \
  -e 's|  docker-release/v2;|  systemd service;|' \
  -e '/^- 禁改边界:/i\
### 后续项目章节\
\
<outside-delivery-placeholder>' \
  "$heading_boundary_repo/AGENTS.md" >"$heading_boundary_repo/AGENTS.md.next"
mv "$heading_boundary_repo/AGENTS.md.next" "$heading_boundary_repo/AGENTS.md"
run_case 0 local_check --repo "$heading_boundary_repo"
expect_line 'PASS: delivery-profile'

bullet_boundary_repo="$(copy_fixture bullet-boundary)"
sed \
  -e 's|  docker-release/v2;|  systemd service;|' \
  -e '/^- 禁改边界:/i\
* 后续项目事实：<outside-delivery-placeholder>' \
  "$bullet_boundary_repo/AGENTS.md" >"$bullet_boundary_repo/AGENTS.md.next"
mv "$bullet_boundary_repo/AGENTS.md.next" "$bullet_boundary_repo/AGENTS.md"
run_case 0 local_check --repo "$bullet_boundary_repo"
expect_line 'PASS: delivery-profile'

run_case 0 remote_check --repo "$TMP/aligned" --kind docs --remote
expect_line 'SKIP: architecture-lock — docs 仓库不要求 architecture lock'
expect_line 'SKIP: delivery-profile — docs 仓库不声明交付形态'
expect_line 'result: pass=4 gap=0 skip=2'

run_case 0 local_check --repo "$TMP/aligned"
expect_line 'SKIP: labels-readback — 未启用 --remote'
expect_line 'SKIP: ci-context — 未启用 --remote'
expect_line 'result: pass=4 gap=0 skip=2'

run_case 64 bash "$CHECKER"
expect_contains 'usage:'

run_case 64 bash "$CHECKER" --repo "$TMP/aligned" --unknown
expect_contains 'usage:'

run_case 64 bash "$CHECKER" --repo "$TMP/aligned" --today 2026-13-40
expect_contains 'usage:'

run_case 1 bash "$CHECKER" --repo "$TMP/aligned" --today 2026-11-07
expect_contains 'GAP: architecture-lock —'

MOCK_PROTECTION_STATUS=403 run_case 0 remote_check --repo "$TMP/aligned" --remote
expect_line 'SKIP: ci-context — 需要 manager/audit 权限'
expect_line 'result: pass=5 gap=0 skip=1'

jq '. + [{name:"project/local",color:"ffffff",description:"local"}]' \
  "$ROOT/codex/config/gitea-labels.json" >"$TMP/labels.json"
run_case 0 remote_check --repo "$TMP/aligned" --remote
expect_line 'INFO: labels-readback — 非受管标签 project/local'
expect_line 'result: pass=6 gap=0 skip=0'

cp "$ROOT/codex/config/gitea-labels.json" "$TMP/labels.json"
MOCK_TRANSPORT_FAIL=1 run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'GAP: labels-readback — 远程标签读取失败'
if grep -Fq 'curl mock transport failure' <<<"$last_output"; then
  fail 'curl transport stderr escaped the structured output contract'
fi

if grep -Fq "$SENTINEL" "$TMP/curl.argv" "$TMP/case.stdout" "$TMP/case.stderr"; then
  fail 'sentinel token leaked through curl argv, stdout, or stderr'
fi

printf 'project check tests passed (%d cases)\n' "$case_count"
