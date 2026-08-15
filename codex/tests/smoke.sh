#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

command -v rg >/dev/null

bash -n \
  "$ROOT/architecture/bin/aisoft-architecture" \
  "$ROOT/architecture/install.sh" \
  "$ROOT/codex/tests/test-architecture-install.sh"

optional_runtime_sources=(
  "$ROOT/codex/agent/analyze-codex.sh"
  "$ROOT/codex/agent/codex-analyzer.sh"
  "$ROOT/codex/agent/codex-provider.sh"
  "$ROOT/codex/agent/common.sh"
  "$ROOT/codex/agent/loop-controller.sh"
  "$ROOT/codex/agent/provider-poll.sh"
  "$ROOT/codex/tools/host-access-broker.sh"
  "$ROOT/codex/tools/project-profile-migration.sh"
  "$ROOT/codex/tools/git-credential-aisoft-host.sh"
  "$ROOT/codex/install-host-access-broker.sh"
  "$ROOT/codex/install-vm.sh"
  "$ROOT/docker-release/bin/aisoft-docker-release"
  "$ROOT/docker-release/bin/aisoft-docker-release-gate"
  "$ROOT/docker-release/install.sh"
  "$ROOT/codex/tests/test-docker-release-install.sh"
  "$ROOT/codex/tests/test-docker-image-store-e2e-harness.sh"
  "$ROOT/codex/tests/integration/test-docker-image-store-e2e.sh"
  "$ROOT/codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh"
  "$ROOT/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh"
  "$ROOT/codex/tests/fixtures/docker-release-v2-lifecycle/docker-wrapper.sh"
  "$ROOT/codex/tests/fixtures/docker-release-v2-lifecycle/migrate.sh"
)
runtime_source_count=0
for script in "${optional_runtime_sources[@]}"; do
  if [[ -f "$script" ]]; then
    bash -n "$script"
    runtime_source_count=$((runtime_source_count + 1))
  fi
done
if ((runtime_source_count == 0)); then
  echo 'SKIP: optional untracked codex/agent runtime sources and codex/install-vm.sh are absent.'
fi

bash -n "$ROOT/codex/tools/sync-gitea-labels.sh"
bash -n "$ROOT/codex/tests/test-sync-gitea-labels.sh"
bash -n "$ROOT/codex/agent/gitea-label-manifest.sh"
bash -n "$ROOT/codex/tests/test-gitea-label-manifest.sh"
bash -n "$ROOT/codex/tools/aisoft-project-check.sh"
bash -n "$ROOT/codex/tests/test-project-check.sh"
for script in \
  "$ROOT/codex/install-host-role.sh" \
  "$ROOT/codex/install-host-access-broker.sh" \
  "$ROOT/codex/tools/mark-deployed-issues.sh" \
  "$ROOT/codex/tools/mark-completed-issues.sh" \
  "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
  "$ROOT/codex/tools/gitea-governance.sh" \
  "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
  "$ROOT/codex/tools/ensure-gitea-collaborator.sh" \
  "$ROOT/codex/tools/aigitea-cleanup-merged.sh" \
  "$ROOT/codex/tools/artifact-retention-dry-run.sh" \
  "$ROOT/codex/tools/verify-host-role.sh" \
  "$ROOT/codex/tools/host-access-broker.sh" \
  "$ROOT/codex/tools/project-profile-migration.sh" \
  "$ROOT/codex/tools/git-credential-aisoft-host.sh" \
  "$ROOT/codex/agent/gitea-token.sh" \
  "$ROOT/codex/tests/test-gitea-token-lib.sh" \
  "$ROOT/codex/tests/test-gitea-token-consumers.sh" \
  "$ROOT/codex/tests/test-mark-deployed-issues.sh" \
  "$ROOT/codex/tests/test-mark-completed-issues.sh" \
  "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh" \
  "$ROOT/codex/tests/test-bootstrap-gitea-service-account.sh" \
  "$ROOT/codex/tests/test-sync-gitea-service-policy.sh" \
  "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh" \
  "$ROOT/codex/tests/test-cleanup-merged.sh" \
  "$ROOT/codex/tests/test-artifact-retention-dry-run.sh" \
  "$ROOT/codex/tests/test-host-role-guard.sh" \
  "$ROOT/codex/tests/test-install-host-role.sh" \
  "$ROOT/codex/tests/test-host-access-broker.sh" \
  "$ROOT"/sync/*.sh \
  "$ROOT"/sync/tests/*.sh; do
  bash -n "$script"
done
if command -v shellcheck >/dev/null; then
  shellcheck \
    "$ROOT"/codex/agent/*.sh \
    "$ROOT/codex/install-vm.sh" \
    "$ROOT/codex/install-host-role.sh" \
    "$ROOT/codex/install-host-access-broker.sh" \
    "$ROOT/codex/tools/sync-gitea-labels.sh" \
    "$ROOT/codex/tools/mark-deployed-issues.sh" \
    "$ROOT/codex/tools/mark-completed-issues.sh" \
    "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
    "$ROOT/codex/tools/gitea-governance.sh" \
    "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
    "$ROOT/codex/tools/sync-gitea-service-policy.sh" \
    "$ROOT/codex/tools/ensure-gitea-collaborator.sh" \
    "$ROOT/codex/tools/aigitea-cleanup-merged.sh" \
    "$ROOT/codex/tools/artifact-retention-dry-run.sh" \
    "$ROOT/codex/tools/verify-host-role.sh" \
    "$ROOT/codex/tools/host-access-broker.sh" \
    "$ROOT/codex/tools/project-profile-migration.sh" \
    "$ROOT/codex/tools/git-credential-aisoft-host.sh" \
    "$ROOT/codex/tools/aisoft-project-check.sh" \
    "$ROOT/codex/tests/test-sync-gitea-labels.sh" \
    "$ROOT/codex/tests/test-gitea-label-manifest.sh" \
    "$ROOT/codex/tests/test-project-check.sh" \
    "$ROOT/codex/tests/test-mark-deployed-issues.sh" \
    "$ROOT/codex/tests/test-mark-completed-issues.sh" \
    "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh" \
    "$ROOT/codex/tests/test-bootstrap-gitea-service-account.sh" \
    "$ROOT/codex/tests/test-sync-gitea-service-policy.sh" \
    "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh" \
    "$ROOT/codex/tests/test-cleanup-merged.sh" \
    "$ROOT/codex/tests/test-artifact-retention-dry-run.sh" \
    "$ROOT/codex/tests/test-host-role-guard.sh" \
    "$ROOT/codex/tests/test-install-host-role.sh" \
    "$ROOT/codex/tests/test-host-access-broker.sh" \
    "$ROOT/codex/tests/test-agent-runtime.sh" \
    "$ROOT/codex/tests/test-gitea-token-lib.sh" \
    "$ROOT/codex/tests/test-gitea-token-consumers.sh"
  shellcheck "$ROOT"/sync/*.sh "$ROOT"/sync/tests/*.sh
  shellcheck \
    "$ROOT/docker-release/bin/aisoft-docker-release" \
    "$ROOT/docker-release/bin/aisoft-docker-release-gate" \
    "$ROOT/docker-release/install.sh" \
    "$ROOT/codex/tests/test-docker-release-install.sh" \
    "$ROOT/codex/tests/test-docker-image-store-e2e-harness.sh" \
    "$ROOT/codex/tests/integration/test-docker-image-store-e2e.sh" \
    "$ROOT/codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh" \
    "$ROOT/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh" \
    "$ROOT/codex/tests/fixtures/docker-release-v2-lifecycle/docker-wrapper.sh" \
    "$ROOT/codex/tests/fixtures/docker-release-v2-lifecycle/migrate.sh" \
    "$ROOT/architecture/bin/aisoft-architecture" \
    "$ROOT/architecture/install.sh" \
    "$ROOT/codex/tests/test-architecture-install.sh"
fi
bash "$ROOT/codex/tests/test-architecture-install.sh"
bash "$ROOT/codex/tests/test-gitea-label-manifest.sh"
bash "$ROOT/codex/tests/test-sync-gitea-labels.sh"
bash "$ROOT/codex/tests/test-project-check.sh"
bash "$ROOT/codex/tests/test-agent-runtime.sh"
bash "$ROOT/codex/tests/test-mark-deployed-issues.sh"
bash "$ROOT/codex/tests/test-mark-completed-issues.sh"
bash "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh"
bash "$ROOT/codex/tests/test-bootstrap-gitea-service-account.sh"
bash "$ROOT/codex/tests/test-sync-gitea-service-policy.sh"
bash "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh"
bash "$ROOT/codex/tests/test-cleanup-merged.sh"
bash "$ROOT/codex/tests/test-artifact-retention-dry-run.sh"
bash "$ROOT/codex/tests/test-gitea-readonly.sh"
bash "$ROOT/codex/tests/test-gitea-token-lib.sh"
bash "$ROOT/codex/tests/test-gitea-token-consumers.sh"
bash "$ROOT/codex/tests/test-install-skills.sh"
bash -n "$ROOT/skill-for-claude/install.sh" "$ROOT/skill-for-claude/check-drift.sh"
bash "$ROOT/codex/tests/test-install-claude-skills.sh"
bash "$ROOT/codex/tests/test-host-role-guard.sh"
bash "$ROOT/codex/tests/test-install-host-role.sh"
bash "$ROOT/codex/tests/test-host-access-broker.sh"
bash "$ROOT/codex/tests/test-docker-release-install.sh"
bash "$ROOT/codex/tests/test-docker-image-store-e2e-harness.sh"
harness_output="$(bash "$ROOT/codex/tests/integration/test-docker-image-store-e2e.sh")"
grep -Fq 'NOT RUN: Docker image-store E2E' <<<"$harness_output"
bash "$ROOT/codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh"
lifecycle_harness_output="$(bash "$ROOT/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")"
grep -Fq 'NOT RUN: Docker release v2 lifecycle E2E requires separate Issue #65 authorization.' \
  <<<"$lifecycle_harness_output"
bash "$ROOT/sync/tests/test-inbound-sync.sh"
bash "$ROOT/sync/tests/test-install.sh"
PYTHONPATH="$ROOT/codex/runtime" python3 -m unittest discover \
  -s "$ROOT/codex/runtime/tests" -v

PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_gitea_governance.cli \
  --manifest "$ROOT/codex/config/gitea-governance.json" validate >/dev/null
jq empty "$ROOT/codex/config/gitea-governance.json"
PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_host_access.cli \
  --access-manifest "$ROOT/codex/config/host-access-broker.json" \
  --governance-manifest "$ROOT/codex/config/gitea-governance.json" \
  validate >/dev/null
jq empty "$ROOT/codex/config/host-access-broker.json"

while IFS= read -r json_file; do
  jq empty "$json_file"
done < <(find "$ROOT/architecture" -type f -name '*.json' ! -path '*/fixtures/invalid/duplicate-key.json' | sort)

while IFS= read -r json_file; do
  jq empty "$json_file"
done < <(
  find "$ROOT/docker-release" "$ROOT/codex/tests/fixtures/docker-release" \
    -type f -name '*.json' | sort
)

jq -e '
  .contract_version == "docker-image-store-compatibility/v1" and
  .matrix_revision == "2026.08.3" and
  (.rows | length == 3) and
  ([.rows[].row_id] | sort) == [
    "engine-29-classic-linux-amd64",
    "engine-29-containerd-linux-amd64",
    "engine-29.7.1-compose-5.1.4-containerd-linux-amd64"
  ] and
  (.rows[] | select(.row_id == "engine-29-containerd-linux-amd64") |
    .image_store == "containerd" and
    .status == "supported" and
    .evidence.kind == "real-e2e" and
    .evidence.evidence_id == "issue-27-containerd-a75181cd7209" and
    .evidence.source == "docs/changes/27/03-verification.md") and
  (.rows[] | select(.row_id == "engine-29-classic-linux-amd64") |
    .image_store == "classic" and
    .status == "rejected" and
    .evidence == null) and
  (.rows[] | select(.row_id == "engine-29.7.1-compose-5.1.4-containerd-linux-amd64") |
    .engine == {"minimum": "29.7.1", "maximum_exclusive": "29.7.2"} and
    .compose == {"minimum": "5.1.4", "maximum_exclusive": "5.1.5"} and
    .os == "linux" and
    .architecture == "amd64" and
    .image_store == "containerd" and
    .status == "supported" and
    .evidence.kind == "real-e2e" and
    .evidence.evidence_id == "issue-65-compose-5.1.4-97445947fff7" and
    .evidence.source == "docs/changes/65/verification-compose-514-lifecycle-260808.md")
' "$ROOT/docker-release/compatibility/image-stores-v1.json" >/dev/null

if rg -n '(^|[[:space:]])(import yaml|from yaml)' \
  "$ROOT/codex/runtime/aisoft_architecture" "$ROOT/architecture"; then
  echo 'Architecture V1 must not introduce a YAML parser.' >&2
  exit 1
fi

for reference in newemaint/target-candidate windows sqlite; do
  "$ROOT/architecture/bin/aisoft-architecture" validate \
    --catalog "$ROOT/architecture/catalog.json" \
    --profiles-dir "$ROOT/architecture/profiles" \
    --schema-dir "$ROOT/architecture/schemas" \
    --project "$ROOT/architecture/reference/$reference/architecture.json" \
    --lock "$ROOT/architecture/reference/$reference/architecture.lock.json" \
    --today 2026-08-06 >/dev/null
done

jq -e '
  .schema_version == 2 and
  (.canonical | length) == 27 and
  ([.canonical[].name] | unique | length == 27) and
  ([.canonical[].name] | sort) == [
    "approved",
    "awaiting-triage",
    "completed",
    "complexity/complex",
    "complexity/small",
    "deployed",
    "needs-analysis",
    "pr-open",
    "spec-drafting",
    "spec-review",
    "triage/bug",
    "triage/enhancement",
    "triage/needs-info",
    "triage/needs-triage",
    "triage/ready-for-agent",
    "triage/ready-for-human",
    "triage/wontfix",
    "type/bugfix",
    "type/data",
    "type/docs",
    "type/feature",
    "type/maintenance",
    "type/platform",
    "type/refactor",
    "type/reliability",
    "type/security",
    "type/test"
  ] and
  ([.project_extensions.allowed_prefixes[].prefix] | sort) == [
    "area/",
    "priority/"
  ] and
  ([.retired[].name] | sort) == ["complexity/standard"] and
  all(.canonical[];
    (.name | length > 0) and
    (.description | type == "string" and length > 0) and
    (.color | test("^[0-9a-fA-F]{6}$"))
  )
' "$ROOT/codex/config/gitea-labels.json" >/dev/null

# 生命周期八个标签名必须只有一处事实源（#115 AC-7）。任何枚举全套名字的文件都是一份副本，
# 因此把「枚举全套」的文件集合整个钉死，新增一份必须显式改这里、被 review 看见。
#
# 允许的四份分两类，缺一不可：
#   - 事实源与其镜像：gitea-labels.json 是 manifest 本身；contract.py 的 LIFECYCLE_LABELS 是
#     Python 侧字面量，由 codex/runtime/tests/test_contract.py 反向钉回 manifest。
#   - 钉住事实源的测试：本文件上面那段 manifest 内容断言；test-gitea-label-manifest.sh 钉住
#     aisoft_label_manifest_lifecycle 的输出。二者的字面量是断言而不是可被消费的来源——测试
#     若改成同样「派生」就成了自证，无法发现派生规则本身写错。
#
# 生产消费者一律调用 aisoft_label_manifest_lifecycle 或 aisoft_loop.contract.LIFECYCLE_LABELS，
# 不得再抄一遍（#115 前 mark-deployed-issues.sh 就是这样漂移出第五份的）。
lifecycle_sources=()
while IFS= read -r candidate; do
  lifecycle_hits=0
  for lifecycle_name in needs-analysis awaiting-triage spec-drafting spec-review \
    approved pr-open completed deployed; do
    if grep -Eq "(^|[^a-zA-Z0-9_/-])$lifecycle_name([^a-zA-Z0-9_/-]|\$)" "$candidate"; then
      lifecycle_hits=$((lifecycle_hits + 1))
    fi
  done
  if [[ "$lifecycle_hits" == 8 ]]; then
    lifecycle_sources+=("${candidate#"$ROOT/"}")
  fi
done < <(rg -l --no-messages 'needs-analysis' "$ROOT/codex")
if [[ "$(printf '%s\n' "${lifecycle_sources[@]}" | LC_ALL=C sort)" != 'codex/config/gitea-labels.json
codex/runtime/aisoft_loop/contract.py
codex/tests/smoke.sh
codex/tests/test-gitea-label-manifest.sh' ]]; then
  echo '生命周期标签列表出现第二处硬编码副本（#115 AC-7）；应从 label manifest 派生。枚举全套名字的文件：' >&2
  printf '%s\n' "${lifecycle_sources[@]}" | LC_ALL=C sort >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/codex/runtime" \
  python3 -m aisoft_loop.matt_snapshot verify \
  "$ROOT/codex/vendor/mattpocock/v1.2.2" \
  "$ROOT/codex/vendor/mattpocock/v1.2.2/manifest.json" >/dev/null

if rg -n -g '!**/tests/smoke.sh' \
  'dangerously-bypass|--yolo|danger-full-access|dangerously-skip-permissions|permission-mode +bypassPermissions' \
  "$ROOT/codex"; then
  echo '检测到禁止的 provider 绕过参数' >&2
  exit 1
fi

for skill in aisoft-matt-workflow gitea-analyze-change gitea-spec-plan gitea-development-loop gitea-implement-change gitea-platform-ops; do
  [[ -f "$ROOT/codex/skills/$skill/SKILL.md" ]]
  [[ -f "$ROOT/codex/skills/$skill/agents/openai.yaml" ]]
  grep -Fq "\$$skill" "$ROOT/codex/skills/$skill/agents/openai.yaml"
done

[[ -f "$ROOT/CLAUDE.md" ]]
grep -Fq '@AGENTS.md' "$ROOT/CLAUDE.md"
if [[ "$(grep -c . "$ROOT/CLAUDE.md")" -gt 5 ]]; then
  echo 'CLAUDE.md 必须只导入共享规范源，不得复制第二套合同' >&2
  exit 1
fi

[[ -f "$ROOT/skill-for-codex/SKILL.md" ]]
[[ -f "$ROOT/skill-for-codex/agents/openai.yaml" ]]
[[ -f "$ROOT/skill-for-codex/references/private-gitea-access.md" ]]
grep -Fq "private-repository \`404\`" "$ROOT/skill-for-codex/SKILL.md"
grep -Fq 'never begin with anonymous API access' \
  "$ROOT/codex/skills/gitea-platform-ops/SKILL.md"
grep -Fq 'gitea-readonly.sh' \
  "$ROOT/skill-for-codex/references/private-gitea-access.md"
grep -Fq 'ensure-gitea-collaborator.sh' \
  "$ROOT/skill-for-codex/references/onboarding-runbook.md"
grep -Fq 'gitea-governance.json' \
  "$ROOT/skill-for-codex/references/onboarding-runbook.md"
grep -Fq 'gitea.labels.provision' \
  "$ROOT/skill-for-codex/references/onboarding-runbook.md"
if rg -n '建七个类型标签|建两个互斥的复杂度标签|建八个标签|建七个 Matt triage 标签' \
  "$ROOT/skill-for-codex/references/onboarding-runbook.md"; then
  echo 'onboarding runbook §5 仍保留手工建标签散文步骤（#108 AC-6）' >&2
  exit 1
fi
grep -Fq 'retire-shared-bot' \
  "$ROOT/codex/skills/gitea-platform-ops/SKILL.md"
grep -Fq 'BLOCKED_EXTERNAL' \
  "$ROOT/codex/tools/ensure-gitea-collaborator.sh"
grep -Fq 'BLOCKED_EXTERNAL' \
  "$ROOT/codex/tools/bootstrap-gitea-service-account.sh"
grep -Fq 'AISOFT_ONBOARDING_MODE=software-repository' \
  "$ROOT/skill-for-codex/SKILL.md"
grep -Fq '/mnt/mac/Users/benque/MyDocs/AISoftPlatform/' "$ROOT/codex/global-AGENTS.md"

if [[ -f "$ROOT/codex/agent/provider-poll.sh" ]]; then
  grep -Fq "ANALYSIS_PROVIDER=\"\${ANALYSIS_PROVIDER:-none}\"" "$ROOT/codex/agent/provider-poll.sh"
  grep -Fq "IMPLEMENT_PROVIDER=\"\${IMPLEMENT_PROVIDER:-none}\"" "$ROOT/codex/agent/provider-poll.sh"
  for provider in claude codex; do
    [[ -f "$ROOT/codex/agent/analyze-$provider.sh" ]]
    [[ -f "$ROOT/codex/agent/$provider-analyzer.sh" ]]
    [[ -f "$ROOT/codex/agent/$provider-provider.sh" ]]
  done
else
  echo 'SKIP: optional runtime contract checks for codex/agent/provider-poll.sh.'
fi
if [[ -f "$ROOT/codex/agent/common.sh" ]]; then
  grep -Fq 'set +x' "$ROOT/codex/agent/common.sh"
  if rg -n 'Authorization: token|AUTH=' "$ROOT/codex/agent"; then
    echo 'shell runtime must not construct token-bearing auth argv' >&2
    exit 1
  fi
else
  echo 'SKIP: optional runtime contract checks for codex/agent/common.sh.'
fi
grep -Fq 'READY_FOR_REVIEW' "$ROOT/codex/skills/gitea-development-loop/SKILL.md"
grep -Fq '生产环境只运行' "$ROOT/AGENTS.md"

root_agents="$ROOT/AGENTS.md"
global_agents="$ROOT/codex/global-AGENTS.md"
literal_dollar='$'
literal_backtick='`'
for instruction in "$root_agents" "$global_agents"; do
  grep -Fq '<role>-<short-description>-<YYMMDD>.md' "$instruction"
  grep -Fq "${literal_dollar}aisoft-matt-workflow" "$instruction"
  grep -Fq "${literal_dollar}setup-matt-pocock-skills" "$instruction"
  grep -Fq 'templates/docs/agents/issue-tracker.md' "$instruction"
  grep -Fq 'templates/docs/agents/triage-labels.md' "$instruction"
  grep -Fq 'templates/docs/agents/domain.md' "$instruction"
  grep -Fq "${literal_dollar}triage #N" "$instruction"
  grep -Fq "${literal_dollar}to-spec #N" "$instruction"
  grep -Fq "${literal_dollar}to-tickets #N" "$instruction"
  grep -Fq "${literal_dollar}implement #N Txx" "$instruction"
  grep -Fq 'gitea-analyze-change' "$instruction"
  grep -Fq 'gitea-spec-plan' "$instruction"
  grep -Fq 'gitea-development-loop' "$instruction"
  grep -Fq 'gitea-implement-change' "$instruction"
  grep -Fq 'gitea-platform-ops' "$instruction"
  grep -Fq 'triage/ready-for-agent' "$instruction"
  grep -Fq 'approved' "$instruction"
  grep -Fq "exact ${literal_backtick}change/N-short-description${literal_backtick}" "$instruction"
  grep -Fq 'Controller' "$instruction"
  grep -Fq 'IMPLEMENT_PROVIDER=none' "$instruction"
  for legacy_basename in 00-summary.md 01-spec.md 02-plan.md 03-verification.md; do
    grep -Fq "$legacy_basename" "$instruction"
  done
done
grep -Fq "${literal_backtick}documents${literal_backtick}" "$root_agents"
grep -Fq "documents${literal_backtick} field" "$global_agents"
grep -Fq "tracker 选择 ${literal_backtick}Other${literal_backtick}" "$root_agents"
grep -Fq "select tracker ${literal_backtick}Other${literal_backtick}" "$global_agents"
grep -Fq 'small 变更可按平台合同跳过 spec/plan' "$root_agents"
grep -Fq 'small work may skip spec/plan' "$global_agents"
grep -Fq '兼容 adapter' "$root_agents"
grep -Fq 'compatibility adapters' "$global_agents"
grep -Fq 'fast-forward push' "$root_agents"
grep -Fq 'fast-forward push' "$global_agents"
grep -Fq '最终 merge 只由人操作' "$root_agents"
grep -Fq 'Only a human may merge' "$global_agents"
grep -Fq 'force-push' "$root_agents"
grep -Fq 'force-push' "$global_agents"
grep -Fq '静默安装或更新全局 skills' "$root_agents"
grep -Fq 'silently install or update global skills' "$global_agents"
grep -Fq '部署需要独立授权' "$root_agents"
grep -Fq 'deployment requires separate authorization' "$global_agents"

analyze_skill="$ROOT/codex/skills/gitea-analyze-change/SKILL.md"
spec_skill="$ROOT/codex/skills/gitea-spec-plan/SKILL.md"
loop_skill="$ROOT/codex/skills/gitea-development-loop/SKILL.md"

declared_analyzer_headings="$(
  awk '
    /Produce exactly these five level-two Markdown sections/ {
      in_output_section_list = 1
      next
    }
    in_output_section_list && /^[0-9]+\./ { exit }
    in_output_section_list && match($0, /`## [^`]+`/) {
      print substr($0, RSTART + 1, RLENGTH - 2)
    }
  ' "$analyze_skill"
)"
expected_analyzer_headings="$(
  printf '%s\n' \
    '## 问题/需求总结' \
    '## 影响范围' \
    '## 初步方案与建议' \
    '## 风险' \
    '## AI 判级'
)"
if [[ "$declared_analyzer_headings" != "$expected_analyzer_headings" ]]; then
  echo 'Analyzer 输出节列表必须且只能按规定顺序包含五个二级标题' >&2
  exit 1
fi
if grep -Fq '## 复杂度建议' "$analyze_skill"; then
  exit 1
fi

classification_schema="$(
  awk '
    /emit one YAML block using this schema and field order:/ {
      waiting_for_schema = 1
      next
    }
    waiting_for_schema && $0 == "```yaml" {
      in_schema = 1
      next
    }
    in_schema && $0 == "```" { exit }
    in_schema { print }
  ' "$analyze_skill"
)"
classification_fields="$(
  awk -F: '/^[a-z_]+:/ { print $1 }' <<<"$classification_schema"
)"
expected_classification_fields="$(
  printf '%s\n' \
    change_type \
    requested_complexity \
    assessed_complexity \
    effective_complexity \
    contract_effect \
    reason \
    risk_flags \
    required_docs \
    confidence \
    override_reason
)"
if [[ "$classification_fields" != "$expected_classification_fields" ]]; then
  echo 'Analyzer 分类 YAML 必须按规定顺序包含全部顶层字段' >&2
  exit 1
fi

for sample_field in \
  'change_type: bugfix' \
  'requested_complexity: auto' \
  'assessed_complexity: small' \
  'effective_complexity: small' \
  'contract_effect: restore' \
  'reason: 恢复已经明确的既有行为' \
  'risk_flags: []' \
  'required_docs:' \
  'confidence: high' \
  "override_reason: ''"; do
  grep -Fxq "$sample_field" <<<"$classification_schema"
done

grep -Fq 'needs-human-decision' "$analyze_skill"
omit_effective="omit \`effective_complexity\`"
grep -Fq "$omit_effective" "$analyze_skill"
grep -Fq 'contract_effect: unclear' "$analyze_skill"
grep -Fq 'type/feature' "$analyze_skill"
grep -Fq 'effective_complexity: complex' "$spec_skill"
grep -Fq 'NEEDS_HUMAN_DECISION' "$loop_skill"
grep -Fq 'NEXT: reclassify as complex and create spec/plan' "$loop_skill"

safe_classification_fields="$expected_classification_fields"
unclear_classification_fields="$(
  printf '%s\n' \
    change_type \
    requested_complexity \
    assessed_complexity \
    contract_effect \
    reason \
    risk_flags \
    required_docs \
    confidence \
    override_reason
)"

fixture_fields() {
  awk -F: '/^[a-z_]+:/ { print $1 }' "$1"
}

fixture_required_docs() {
  awk '
    /^required_docs:/ { in_docs = 1; next }
    in_docs && /^  - / { sub(/^  - /, ""); print; next }
    in_docs { exit }
  ' "$1"
}

small_fixture="$ROOT/codex/tests/fixtures/classification/small.yaml"
complex_fixture="$ROOT/codex/tests/fixtures/classification/complex.yaml"
unclear_fixture="$ROOT/codex/tests/fixtures/classification/unclear.yaml"

[[ "$(fixture_fields "$small_fixture")" == "$safe_classification_fields" ]]
[[ "$(fixture_fields "$complex_fixture")" == "$safe_classification_fields" ]]
[[ "$(fixture_fields "$unclear_fixture")" == "$unclear_classification_fields" ]]
grep -Fxq 'effective_complexity: small' "$small_fixture"
grep -Fxq 'effective_complexity: complex' "$complex_fixture"
if grep -Eq '^effective_complexity:' "$unclear_fixture"; then
  echo 'Unclear classification fixture must omit effective_complexity' >&2
  exit 1
fi
grep -Fxq 'contract_effect: unclear' "$unclear_fixture"
[[ "$(fixture_required_docs "$small_fixture")" == 'summary' ]]
[[ "$(fixture_required_docs "$unclear_fixture")" == 'summary' ]]
[[ "$(fixture_required_docs "$complex_fixture")" == $'summary\nspec\nplan' ]]

for template in summary.md spec.md plan.md verification.md; do
  file="$ROOT/templates/docs/changes/_template/$template"
  front_matter="$(
    awk '
      NR == 1 && $0 == "---" { in_front_matter = 1; next }
      in_front_matter && $0 == "---" { found_end = 1; exit }
      in_front_matter { print }
      END { if (!in_front_matter || !found_end) exit 1 }
    ' "$file"
  )"
  for field in change_type requested_complexity assessed_complexity effective_complexity contract_effect confidence risk_flags; do
    grep -Eq "^${field}:" <<<"$front_matter"
  done
done
! rg -n 'complexity_recommendation:' "$ROOT/templates/docs/changes/_template" || exit 1

summary_template="$ROOT/templates/docs/changes/_template/summary.md"
grep -Fq 'WRAPPER_CONDITIONAL' "$summary_template"
grep -Fq 'delete every' "$summary_template"
grep -Fq "\`effective_complexity:\` key from both the front matter and the \`## AI 判级\`" "$summary_template"
grep -Eq '^reason:' "$summary_template"
grep -Eq '^required_docs:' "$summary_template"

grep -Fq 'type/feature' "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md"
grep -Fq 'complexity/complex' "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md"
grep -Fq 'requested_complexity' "$ROOT/04-Agent编排与定时任务.md"
grep -Fq '功能性更改' "$ROOT/AGENTS.md"

if rg -n 'complexity_recommendation|最终 `complexity` 由人|人确认 Issue 验收标准与 complexity=small' \
  "$ROOT/AGENTS.md" "$ROOT/README.md" \
  "$ROOT/03-Issue-Spec-Plan与单闸门开发流程.md" \
  "$ROOT/04-Agent编排与定时任务.md"; then
  echo '检测到旧的人工确认或复杂度建议合同' >&2
  exit 1
fi

grep -Fq '首次部署' "$ROOT/02-CI与自动部署流水线.md"
grep -Fq 'READY_FOR_REVIEW' "$ROOT/05-通知与多人协作.md"
grep -Fq '标准故障包' "$ROOT/06-运维手册与踩坑集.md"
grep -Fq '生产环境只执行版本化、已验证、可回滚的确定性脚本，不安装或调用 AI' \
  "$ROOT/07-内网与生产平移路线.md"

if rg -n '对应闸门|三道闸门可以分派' "$ROOT/05-通知与多人协作.md"; then
  echo '通知分册仍包含 v2 三闸门现行合同' >&2
  exit 1
fi

test -x "$ROOT/codex/agent/project-poll.sh"
test -f "$ROOT/codex/systemd/aisoft-agent@.service"
test -f "$ROOT/codex/systemd/aisoft-agent@.timer"
test -f "$ROOT/templates/agent/project.env.example"
grep -Fq 'project-poll.sh %i' "$ROOT/codex/systemd/aisoft-agent@.service"
grep -Fq 'IMPLEMENT_PROVIDER=none' "$ROOT/templates/agent/project.env.example"
grep -Fq 'explicit project profile' "$ROOT/codex/global-AGENTS.md"
if rg -ni 'rsdesign' \
  "$ROOT/codex/agent" \
  "$ROOT/codex/runtime/aisoft_loop" \
  "$ROOT/codex/systemd" \
  "$ROOT/templates/agent"; then
  echo '通用 runtime 入口不得硬编码 rsDesign pilot' >&2
  exit 1
fi

echo 'Codex platform static smoke checks passed.'
