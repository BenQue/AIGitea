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
    /^  <Linux 容器化/ {
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
  */issues\?*)
    if [[ "${MOCK_ISSUES_FAIL:-0}" == 1 ]]; then
      printf '{}\n' >"$output_file"
      printf '500'
      exit 0
    fi
    query="${url#*\?}"
    label=''
    while IFS= read -r parameter; do
      [[ "$parameter" == labels=* ]] && label="${parameter#labels=}"
    done < <(tr '&' '\n' <<<"$query")
    if [[ -n "$label" && -f "$MOCK_ISSUES_DIR/$label.json" ]]; then
      cp "$MOCK_ISSUES_DIR/$label.json" "$output_file"
    else
      printf '[]\n' >"$output_file"
    fi
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
mkdir -p "$TMP/issues"

# The mocked GET /labels response is the canonical array, not the manifest file:
# schema_version 2 wraps canonical in an object (#108), and the remote API keeps
# returning a bare array.
canonical_labels() {
  jq "${1:-.}" <<<"$(jq '.canonical' "$ROOT/codex/config/gitea-labels.json")"
}
canonical_labels >"$TMP/labels.json"

# check_ci_context compares the mocked live protection against THIS repository's
# own governance manifest, so every fixture that expects PASS has to equal what
# the manifest declares for that exact repository. A literal copy goes stale the
# moment a project gains a required context, and the failure lands here rather
# than where the manifest changed: #312 added NewEMaint's second context and
# turned four unrelated cases red. Positive fixtures derive; negative ones keep
# their literal wrong values, which is the whole point of them.
manifest_contexts() {
  jq -ce --arg repo "$1" \
    '[.repositories[] | select(.name == $repo)] | .[0].status_check_contexts' \
    "$ROOT/codex/config/gitea-governance.json"
}

protection_fixture() {
  jq -n --argjson contexts "$(manifest_contexts "$1")" --argjson outdated "$2" '{
    enable_push: false,
    enable_status_check: ($contexts | length > 0),
    status_check_contexts: $contexts,
    block_on_outdated_branch: $outdated
  }'
}

protection_fixture NewEMaint true >"$TMP/protection.json"

remote_check() {
  env \
    PATH="$TMP/bin:$PATH" \
    AGENT_ENV_FILE="${MOCK_ENV_FILE:-$TMP/agent.env}" \
    MOCK_ARGV_LOG="$TMP/curl.argv" \
    MOCK_LABELS="$TMP/labels.json" \
    MOCK_ISSUES_DIR="$TMP/issues" \
    MOCK_PROTECTION="${MOCK_PROTECTION:-$TMP/protection.json}" \
    MOCK_SENTINEL="$SENTINEL" \
    MOCK_PROTECTION_STATUS="${MOCK_PROTECTION_STATUS:-200}" \
    MOCK_TRANSPORT_FAIL="${MOCK_TRANSPORT_FAIL:-0}" \
    MOCK_ISSUES_FAIL="${MOCK_ISSUES_FAIL:-0}" \
    bash "$CHECKER" --today 2026-09-12 "$@"
}

local_check() {
  bash "$CHECKER" --today 2026-09-12 "$@"
}

make_aligned_repo "$TMP/aligned"

run_case 0 remote_check --repo "$TMP/aligned" --remote
for check_id in pointer-sections change-templates architecture-lock labels-readback ci-context ci-outdated-branch delivery-profile change-documents change-pr-url; do
  expect_line "PASS: $check_id"
done
expect_line 'result: pass=9 gap=0 skip=2'
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
expect_line 'result: pass=9 gap=0 skip=2'
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
canonical_labels '.[1:]' >"$TMP/labels.json"
missing_label="$(jq -r '.canonical[0].name' "$ROOT/codex/config/gitea-labels.json")"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains "GAP: labels-readback — 缺失或漂移: $missing_label"

canonical_labels '.[0].color = "ffffff"' >"$TMP/labels.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback — 缺失或漂移:'

# Cosmetic-only differences must never read as drift: the checker and the
# provisioner share one normalization (#108), so a '#'-prefixed uppercase color
# and a padded description are aligned, not a repair loop.
canonical_labels '
  .[0].color = ("#" + (.[0].color | ascii_upcase)) |
  .[0].description = "  " + .[0].description + " "
' >"$TMP/labels.json"
run_case 0 remote_check --repo "$labels_repo" --remote
expect_line 'PASS: labels-readback'

# AC-5: a managed-namespace conflict names the Issues that carry it.
canonical_labels '. + [{name:"type/legacy",color:"ffffff",description:"conflict"}]' \
  >"$TMP/labels.json"
jq -n '[{number:12},{number:7}]' >"$TMP/issues/type%2Flegacy.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback — 受管命名空间冲突: type/legacy(#7,#12)'

# AC-5: a retired value still in use is reported as retired (not merely as a
# namespace conflict) and likewise carries its Issue list.
canonical_labels '
  . + [{name:"complexity/standard",color:"ffffff",description:"retired"}]
' >"$TMP/labels.json"
jq -n '[{number:31}]' >"$TMP/issues/complexity%2Fstandard.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback — 退役取值仍在用: complexity/standard(#31)'

# An offending label nobody references is stated as such, never silently
# rendered as an empty list.
canonical_labels '. + [{name:"type/orphan",color:"ffffff",description:"conflict"}]' \
  >"$TMP/labels.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback — 受管命名空间冲突: type/orphan(无 Issue 引用)'

# An unreadable Issue list is reported, not collapsed into "no references".
MOCK_ISSUES_FAIL=1 run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: labels-readback — 受管命名空间冲突: type/orphan(Issue 清单读取失败)'

canonical_labels >"$TMP/labels.json"
jq '.status_check_contexts = ["wrong"]' "$TMP/protection.json" \
  >"$TMP/protection.next"
mv "$TMP/protection.next" "$TMP/protection.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: ci-context —'

protection_fixture NewEMaint true \
  | jq '.enable_push = true' >"$TMP/protection.json"
run_case 1 remote_check --repo "$labels_repo" --remote
expect_contains 'GAP: ci-context —'

protection_fixture NewEMaint true >"$TMP/protection.json"
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

# #142: the change document front matter contract is now a gate. A change that
# resolve-documents cannot parse, or a summary that claims a PR without carrying
# its URL, used to merge into main with nothing saying a word.
make_change_repo() {
  local repo="$1" status="$2" pr_url="$3"
  make_aligned_repo "$repo"
  local directory="$repo/docs/changes/57-matt-flow"
  mkdir -p "$directory"
  cat >"$directory/summary-matt-flow-260808.md" <<EOF
---
issue: 57
gitea_url: http://mock.gitea.invalid/admin/NewEMaint/issues/57
documents:
  summary: summary-matt-flow-260808.md
  spec: spec-matt-flow-260808.md
status: $status
branch: change/57-matt-flow
pr_url:$pr_url
created: 2026-08-08
---

# Summary
EOF
  cat >"$directory/spec-matt-flow-260808.md" <<'EOF'
---
issue: 57
branch: change/57-matt-flow
created: 2026-08-08
---

# Spec
EOF
}

change_ok_repo="$TMP/change-ok"
make_change_repo "$change_ok_repo" approved ''
run_case 0 local_check --repo "$change_ok_repo"
expect_line 'PASS: change-documents'
expect_line 'PASS: change-pr-url'

change_broken_repo="$TMP/change-broken"
make_change_repo "$change_broken_repo" approved ''
printf '# spec without front matter\n' \
  >"$change_broken_repo/docs/changes/57-matt-flow/spec-matt-flow-260808.md"
run_case 1 local_check --repo "$change_broken_repo"
expect_contains 'GAP: change-documents —'
expect_contains '57-matt-flow'
expect_contains 'spec-matt-flow-260808.md'

change_pr_repo="$TMP/change-pr-url"
make_change_repo "$change_pr_repo" pr-open ''
run_case 1 local_check --repo "$change_pr_repo"
expect_line 'PASS: change-documents'
expect_contains 'GAP: change-pr-url —'
expect_contains 'status 为 pr-open 但 pr_url 为空'

change_pr_filled_repo="$TMP/change-pr-url-filled"
make_change_repo "$change_pr_filled_repo" pr-open \
  ' http://mock.gitea.invalid/admin/NewEMaint/pulls/58'
run_case 0 local_check --repo "$change_pr_filled_repo"
expect_line 'PASS: change-pr-url'

# A repository without docs/changes at all is skipped rather than reported as
# clean: "the checker found nothing to look at" and "the repository is fine" are
# different answers. Such a repository is by definition not aligned yet, so the
# template check GAPs alongside it — that is the honest result, not a regression.
no_changes_repo="$TMP/no-changes"
make_aligned_repo "$no_changes_repo"
rm -rf "$no_changes_repo/docs/changes"
run_case 1 local_check --repo "$no_changes_repo"
expect_line 'SKIP: change-documents — 仓库尚无 docs/changes'
expect_line 'SKIP: change-pr-url — 仓库尚无 docs/changes'

run_case 0 remote_check --repo "$TMP/aligned" --kind docs --remote
expect_line 'SKIP: architecture-lock — docs 仓库不要求 architecture lock'
expect_line 'SKIP: delivery-profile — docs 仓库不声明交付形态'
expect_line 'result: pass=7 gap=0 skip=4'

run_case 0 local_check --repo "$TMP/aligned"
expect_line 'SKIP: labels-readback — 未启用 --remote'
expect_line 'SKIP: ci-context — 未启用 --remote'
expect_line 'SKIP: ci-outdated-branch — 未启用 --remote'
expect_line 'result: pass=6 gap=0 skip=5'

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
expect_line 'SKIP: ci-outdated-branch — 需要 manager/audit 权限'
expect_line 'result: pass=7 gap=0 skip=4'

# AC-4: a value under a declared extension prefix is legitimate — the platform
# owns the dimension, the project owns the values.
canonical_labels '
  . + [{name:"area/web",color:"ffffff",description:"project dimension"},
       {name:"priority/p1",color:"ffffff",description:"project dimension"}]
' >"$TMP/labels.json"
run_case 0 remote_check --repo "$TMP/aligned" --remote
expect_line 'INFO: labels-readback — 声明扩展标签 area/web'
expect_line 'INFO: labels-readback — 声明扩展标签 priority/p1'
expect_line 'result: pass=9 gap=0 skip=2'

# AC-4: a near-miss of a declared prefix is undeclared, not a project dimension.
# This is the case a prefix-only allow list would wave through.
canonical_labels '. + [{name:"aera/web",color:"ffffff",description:"typo"}]' \
  >"$TMP/labels.json"
jq -n '[{number:5}]' >"$TMP/issues/aera%2Fweb.json"
run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_contains 'GAP: labels-readback — 未声明标签: aera/web(#5)'

# The bare prefix itself declares nothing; it is not a usable label value.
canonical_labels '. + [{name:"area/",color:"ffffff",description:"bare prefix"}]' \
  >"$TMP/labels.json"
run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_contains 'GAP: labels-readback — 未声明标签: area/(无 Issue 引用)'

# #223 ci-merge-preview. The check judges the mechanism, not one spelling of it,
# and it must never report a repository that runs the PR head as protected — a
# false PASS here tells a project it is covered when the next pair of parallel
# PRs will still turn main red.

write_workflow() {
  local repo="$1" name="$2"
  mkdir -p "$repo/.gitea/workflows"
  cat >"$repo/.gitea/workflows/$name"
}

# The shipped reference must satisfy the shipped checker (AC-2, AC-7).
reference_repo="$(copy_fixture merge-preview-reference)"
mkdir -p "$reference_repo/.gitea/workflows" "$reference_repo/scripts/ci"
cp "$ROOT/templates/project/ci/ci.yml" "$reference_repo/.gitea/workflows/ci.yml"
cp "$ROOT/templates/project/ci/merge-preview.sh" "$reference_repo/scripts/ci/merge-preview.sh"
run_case 0 local_check --repo "$reference_repo"
expect_line 'PASS: ci-merge-preview'

# refs/pull/N/merge is the other accepted shape.
merge_ref_repo="$(copy_fixture merge-preview-ref)"
write_workflow "$merge_ref_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
          fetch-depth: 0
      - run: echo project checks
WORKFLOW
run_case 0 local_check --repo "$merge_ref_repo"
expect_line 'PASS: ci-merge-preview'

# The pre-#223 shape every project independently reproduced.
head_repo="$(copy_fixture merge-preview-head)"
write_workflow "$head_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: echo project checks
WORKFLOW
run_case 1 local_check --repo "$head_repo"
expect_contains 'GAP: ci-merge-preview — .gitea/workflows/ci.yml'

# A hand-rolled checkout runs the PR head just the same. Skipping it would let
# the repositories that never adopted actions/checkout look clean.
hand_rolled_repo="$(copy_fixture merge-preview-hand-rolled)"
write_workflow "$hand_rolled_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout from local Gitea
        run: |
          git init .
          git remote add origin "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git"
          git fetch --no-tags --depth=1 origin "$GITHUB_REF"
          git checkout --detach FETCH_HEAD
      - run: echo project checks
WORKFLOW
run_case 1 local_check --repo "$hand_rolled_repo"
expect_contains 'GAP: ci-merge-preview — .gitea/workflows/ci.yml'

# A preview that may fail silently is not a gate.
tolerant_repo="$(copy_fixture merge-preview-tolerant)"
mkdir -p "$tolerant_repo/scripts/ci"
cp "$ROOT/templates/project/ci/merge-preview.sh" "$tolerant_repo/scripts/ci/merge-preview.sh"
write_workflow "$tolerant_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check out merge preview
        continue-on-error: true
        run: bash scripts/ci/merge-preview.sh
      - run: echo project checks
WORKFLOW
run_case 1 local_check --repo "$tolerant_repo"
expect_contains 'GAP: ci-merge-preview — .gitea/workflows/ci.yml'

# git merge-base only asks for the common ancestor; it is not a merge.
ancestor_repo="$(copy_fixture merge-preview-ancestor)"
write_workflow "$ancestor_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: MERGE_PREVIEW look-alike
        run: git merge-base origin/main HEAD
      - run: echo project checks
WORKFLOW
run_case 1 local_check --repo "$ancestor_repo"
expect_contains 'GAP: ci-merge-preview — .gitea/workflows/ci.yml'

# Not judged: no workflow directory, push-only, and pull_request without a
# checkout. None of those runs a tree that could be wrong about the merge.
push_repo="$(copy_fixture merge-preview-push-only)"
write_workflow "$push_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  push:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo project checks
WORKFLOW
run_case 0 local_check --repo "$push_repo"
expect_line 'SKIP: ci-merge-preview — 没有既由 pull_request 触发又检出仓库的 workflow'

no_checkout_repo="$(copy_fixture merge-preview-no-checkout)"
write_workflow "$no_checkout_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - run: echo no tree is checked out here
WORKFLOW
run_case 0 local_check --repo "$no_checkout_repo"
expect_line 'SKIP: ci-merge-preview — 没有既由 pull_request 触发又检出仓库的 workflow'

run_case 0 local_check --repo "$TMP/aligned"
expect_line 'SKIP: ci-merge-preview — 仓库没有 .gitea/workflows 或 .github/workflows'

# #201 ci-registry-preflight. 暖缓存让 registry 停机在 CI 上完全不可见：
# 只用既有依赖的 PR 照样全绿。本检查判的是「装依赖之前有没有一条真的会去
# registry 取东西的断言」，顺序和「真的发请求」两条缺一不可——一个排在
# npm ci 之后、或者只回显标记的步骤，护不住那次安装。

write_npm_workflow() {
  local repo="$1"
  mkdir -p "$repo/.gitea/workflows" "$repo/scripts/ci"
  cp "$ROOT/templates/project/ci/registry-preflight.sh" \
    "$repo/scripts/ci/registry-preflight.sh"
  write_workflow "$repo" ci.yml
}

# 出厂的 ci.yml 必须满足出厂的检查器。模板里的占位步骤换成一次真实的
# npm ci——项目采纳模板后就是这个形状——之后那一步 Registry preflight
# 必须被认出来。这条用例是模板与检查器之间唯一的连接点：少了它，
# 两边可以各自「正确」而合起来判错。
shipped_repo="$(copy_fixture registry-preflight-shipped)"
mkdir -p "$shipped_repo/.gitea/workflows" "$shipped_repo/scripts/ci"
cp "$ROOT/templates/project/ci/registry-preflight.sh" \
  "$shipped_repo/scripts/ci/registry-preflight.sh"
cp "$ROOT/templates/project/ci/merge-preview.sh" \
  "$shipped_repo/scripts/ci/merge-preview.sh"
sed "s|run: echo '换成本项目自己的测试命令'|run: npm ci|" \
  "$ROOT/templates/project/ci/ci.yml" >"$shipped_repo/.gitea/workflows/ci.yml"
grep -Fq 'npm ci' "$shipped_repo/.gitea/workflows/ci.yml" \
  || fail '出厂 ci.yml 的占位步骤没被替换成依赖安装，本用例会退化成 SKIP'
run_case 0 local_check --repo "$shipped_repo"
expect_line 'PASS: ci-registry-preflight'
expect_line 'PASS: ci-merge-preview'

# 出厂参考加上一次真实的依赖安装：项目采纳模板后就是这个形状。
preflight_ok_repo="$(copy_fixture registry-preflight-ok)"
write_npm_workflow "$preflight_ok_repo" <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
env:
  NPM_CONFIG_REGISTRY: http://gitea-ci.orb.local:4873/
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - name: Registry preflight
        run: bash scripts/ci/registry-preflight.sh
      - name: Install dependencies
        run: npm ci
WORKFLOW
run_case 0 local_check --repo "$preflight_ok_repo"
expect_line 'PASS: ci-registry-preflight'

# 没有断言：这正是 2026-08 那次故障里每一个仓库的形状。
preflight_missing_repo="$(copy_fixture registry-preflight-missing)"
write_npm_workflow "$preflight_missing_repo" <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - name: Install dependencies
        run: npm ci
WORKFLOW
run_case 1 local_check --repo "$preflight_missing_repo"
expect_contains 'GAP: ci-registry-preflight — .gitea/workflows/ci.yml'
expect_contains '暖缓存'

# 排在安装之后等于没有：npm ci 已经先失败了 70 秒。
preflight_late_repo="$(copy_fixture registry-preflight-late)"
write_npm_workflow "$preflight_late_repo" <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - name: Install dependencies
        run: npm ci
      - name: Registry preflight
        run: bash scripts/ci/registry-preflight.sh
WORKFLOW
run_case 1 local_check --repo "$preflight_late_repo"
expect_contains 'GAP: ci-registry-preflight — .gitea/workflows/ci.yml'

# 可以静默失败的断言不是闸门，与 #223 对合并预览的判法一致。
preflight_soft_repo="$(copy_fixture registry-preflight-soft)"
write_npm_workflow "$preflight_soft_repo" <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - name: Registry preflight
        continue-on-error: true
        run: bash scripts/ci/registry-preflight.sh
      - name: Install dependencies
        run: npm ci
WORKFLOW
run_case 1 local_check --repo "$preflight_soft_repo"
expect_contains 'GAP: ci-registry-preflight — .gitea/workflows/ci.yml'

# 只回显标记而不发请求的桩：标记好抄，断言不好抄。
preflight_stub_repo="$(copy_fixture registry-preflight-stub)"
mkdir -p "$preflight_stub_repo/.gitea/workflows"
write_workflow "$preflight_stub_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - name: Registry preflight
        run: echo AISOFT_REGISTRY_PREFLIGHT_OK
      - name: Install dependencies
        run: npm ci
WORKFLOW
run_case 1 local_check --repo "$preflight_stub_repo"
expect_contains 'GAP: ci-registry-preflight — .gitea/workflows/ci.yml'

# 不装 npm 依赖的仓库与本故障无关，跳过而不是报干净。
preflight_no_npm_repo="$(copy_fixture registry-preflight-no-npm)"
write_workflow "$preflight_no_npm_repo" ci.yml <<'WORKFLOW'
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
      - run: bash codex/tests/smoke.sh
WORKFLOW
run_case 0 local_check --repo "$preflight_no_npm_repo"
expect_line 'SKIP: ci-registry-preflight — 没有安装 npm 依赖的 workflow'

run_case 0 local_check --repo "$TMP/aligned"
expect_line 'SKIP: ci-registry-preflight — 仓库没有 .gitea/workflows 或 .github/workflows'

# #223 ci-outdated-branch. An expired green is still a valid green until this
# flag is on: base moves, nothing reruns the workflow, and the merge lands on a
# tree no run ever saw. #299 narrowed the ruling: an internal application
# (the aligned fixture is NewEMaint) may leave the flag off once its
# pull_request workflow checks out the merge preview, and the checker then
# reports the value as SKIP naming the ruling — not GAP, and not a silent PASS
# that would hide the value from a later main-red reconstruction.
# The label mock is shared mutable state; earlier cases leave an undeclared
# label behind, and these cases assert the whole run's exit status.
canonical_labels >"$TMP/labels.json"
protection_fixture NewEMaint false >"$TMP/protection-open.json"
preview_open_repo="$(copy_fixture outdated-with-preview)"
mkdir -p "$preview_open_repo/.gitea/workflows" "$preview_open_repo/scripts/ci"
cp "$ROOT/templates/project/ci/ci.yml" "$preview_open_repo/.gitea/workflows/ci.yml"
cp "$ROOT/templates/project/ci/merge-preview.sh" "$preview_open_repo/scripts/ci/merge-preview.sh"
MOCK_PROTECTION="$TMP/protection-open.json" \
  run_case 0 remote_check --repo "$preview_open_repo" --remote
expect_line 'PASS: ci-merge-preview'
expect_line 'PASS: ci-context'
expect_line 'SKIP: ci-outdated-branch — block_on_outdated_branch 未打开；#299 裁决已有合并预览的 internal-application 不再要求，残余风险见 06 踩坑集 #299 条目'

# A missing key is not an implicit true; it reads the same as false.
protection_fixture NewEMaint false \
  | jq 'del(.block_on_outdated_branch)' >"$TMP/protection-silent.json"
MOCK_PROTECTION="$TMP/protection-silent.json" \
  run_case 0 remote_check --repo "$preview_open_repo" --remote
expect_line 'SKIP: ci-outdated-branch — block_on_outdated_branch 未打开；#299 裁决已有合并预览的 internal-application 不再要求，残余风险见 06 踩坑集 #299 条目'

# Without the merge preview both #223 gaps are open at once — the incident
# itself — so an internal application still reads GAP (the aligned fixture has
# no workflow, so ci-merge-preview is SKIP there, which is not PASS).
MOCK_PROTECTION="$TMP/protection-open.json" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'SKIP: ci-merge-preview — 仓库没有 .gitea/workflows 或 .github/workflows'
expect_line 'GAP: ci-outdated-branch — block_on_outdated_branch 未打开且 pull_request 未检出合并预览，两道保证同时缺失；#299 只允许 ci-merge-preview PASS 的 internal-application 关闭'
expect_line 'result: pass=8 gap=1 skip=2'

# The platform repository stays under the #223 requirement: its own CI only
# runs on pull_request, so an expired green would land on main unobserved.
cat >"$TMP/agent-platform.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=aisoft-platform
GITEA_TOKEN=$SENTINEL
EOF
chmod 600 "$TMP/agent-platform.env"
# The platform repository declares its own contexts, which are not NewEMaint's
# (#312); reusing NewEMaint's fixture here would read as a ci-context GAP and
# hide what these two cases are actually about.
protection_fixture aisoft-platform false >"$TMP/protection-platform-open.json"
protection_fixture aisoft-platform true >"$TMP/protection-platform.json"
MOCK_ENV_FILE="$TMP/agent-platform.env" MOCK_PROTECTION="$TMP/protection-platform-open.json" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'PASS: ci-context'
expect_line 'GAP: ci-outdated-branch — block_on_outdated_branch 未打开，base 前进后过期的绿仍可合并'
MOCK_ENV_FILE="$TMP/agent-platform.env" MOCK_PROTECTION="$TMP/protection-platform.json" \
  run_case 0 remote_check --repo "$TMP/aligned" --remote
expect_line 'PASS: ci-outdated-branch'

# The 2026-09-05 ruling covers the platform repository and internal
# applications; a public test repository is outside it and must not read as a
# finding.
cat >"$TMP/agent-public-test.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=myapp
GITEA_TOKEN=$SENTINEL
EOF
chmod 600 "$TMP/agent-public-test.env"
MOCK_ENV_FILE="$TMP/agent-public-test.env" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'SKIP: ci-outdated-branch — classification=public-test 不在裁定范围内'

# A repository outside the manifest is a GAP, not a silent pass.
cat >"$TMP/agent-unknown.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=admin
GITEA_REPO=not-in-manifest
GITEA_TOKEN=$SENTINEL
EOF
chmod 600 "$TMP/agent-unknown.env"
MOCK_ENV_FILE="$TMP/agent-unknown.env" \
  run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'GAP: ci-outdated-branch — 仓库不在 governance manifest 或坐标不匹配'

canonical_labels >"$TMP/labels.json"
MOCK_TRANSPORT_FAIL=1 run_case 1 remote_check --repo "$TMP/aligned" --remote
expect_line 'GAP: labels-readback — 远程标签读取失败'
if grep -Fq 'curl mock transport failure' <<<"$last_output"; then
  fail 'curl transport stderr escaped the structured output contract'
fi

if grep -Fq "$SENTINEL" "$TMP/curl.argv" "$TMP/case.stdout" "$TMP/case.stderr"; then
  fail 'sentinel token leaked through curl argv, stdout, or stderr'
fi

printf 'project check tests passed (%d cases)\n' "$case_count"
