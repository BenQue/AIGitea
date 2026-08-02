#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

command -v rg >/dev/null

optional_runtime_sources=(
  "$ROOT/codex/agent/analyze-codex.sh"
  "$ROOT/codex/agent/codex-analyzer.sh"
  "$ROOT/codex/agent/codex-provider.sh"
  "$ROOT/codex/agent/common.sh"
  "$ROOT/codex/agent/loop-controller.sh"
  "$ROOT/codex/agent/provider-poll.sh"
  "$ROOT/codex/install-vm.sh"
  "$ROOT/docker-release/bin/aisoft-docker-release"
  "$ROOT/docker-release/install.sh"
  "$ROOT/codex/tests/test-docker-release-install.sh"
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
for script in \
  "$ROOT/codex/tools/mark-deployed-issues.sh" \
  "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
  "$ROOT/codex/tools/ensure-gitea-collaborator.sh" \
  "$ROOT/codex/tools/aigitea-cleanup-merged.sh" \
  "$ROOT/codex/tests/test-mark-deployed-issues.sh" \
  "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh" \
  "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh" \
  "$ROOT/codex/tests/test-cleanup-merged.sh" \
  "$ROOT"/sync/*.sh \
  "$ROOT"/sync/tests/*.sh; do
  bash -n "$script"
done
if command -v shellcheck >/dev/null; then
  shellcheck \
    "$ROOT"/codex/agent/*.sh \
    "$ROOT/codex/install-vm.sh" \
    "$ROOT/codex/tools/sync-gitea-labels.sh" \
    "$ROOT/codex/tools/mark-deployed-issues.sh" \
    "$ROOT/codex/tools/sync-gitea-repository-settings.sh" \
    "$ROOT/codex/tools/ensure-gitea-collaborator.sh" \
    "$ROOT/codex/tools/aigitea-cleanup-merged.sh" \
    "$ROOT/codex/tests/test-sync-gitea-labels.sh" \
    "$ROOT/codex/tests/test-mark-deployed-issues.sh" \
    "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh" \
    "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh" \
    "$ROOT/codex/tests/test-cleanup-merged.sh" \
    "$ROOT/codex/tests/test-agent-runtime.sh"
  shellcheck "$ROOT"/sync/*.sh "$ROOT"/sync/tests/*.sh
  shellcheck \
    "$ROOT/docker-release/bin/aisoft-docker-release" \
    "$ROOT/docker-release/install.sh" \
    "$ROOT/codex/tests/test-docker-release-install.sh"
fi
bash "$ROOT/codex/tests/test-sync-gitea-labels.sh"
bash "$ROOT/codex/tests/test-agent-runtime.sh"
bash "$ROOT/codex/tests/test-mark-deployed-issues.sh"
bash "$ROOT/codex/tests/test-sync-gitea-repository-settings.sh"
bash "$ROOT/codex/tests/test-ensure-gitea-collaborator.sh"
bash "$ROOT/codex/tests/test-cleanup-merged.sh"
bash "$ROOT/codex/tests/test-gitea-readonly.sh"
bash "$ROOT/codex/tests/test-install-skills.sh"
bash "$ROOT/codex/tests/test-docker-release-install.sh"
bash "$ROOT/sync/tests/test-inbound-sync.sh"
bash "$ROOT/sync/tests/test-install.sh"
PYTHONPATH="$ROOT/codex/runtime" python3 -m unittest discover \
  -s "$ROOT/codex/runtime/tests" -v

jq -e '
  length == 17 and
  (map(.name) | unique | length == 17) and
  (map(.name) | sort) == [
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
    "type/bugfix",
    "type/docs",
    "type/feature",
    "type/maintenance",
    "type/platform",
    "type/refactor",
    "type/test"
  ] and
  all(.[];
    (.name | length > 0) and
    (.description | type == "string" and length > 0) and
    (.color | test("^[0-9a-fA-F]{6}$"))
  )
' "$ROOT/codex/config/gitea-labels.json" >/dev/null

if rg -n -g '!**/tests/smoke.sh' \
  'dangerously-bypass|--yolo|danger-full-access|dangerously-skip-permissions|permission-mode +bypassPermissions' \
  "$ROOT/codex"; then
  echo '检测到禁止的 provider 绕过参数' >&2
  exit 1
fi

for skill in gitea-analyze-change gitea-spec-plan gitea-development-loop gitea-implement-change gitea-platform-ops; do
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
grep -Fq 'BLOCKED_EXTERNAL' \
  "$ROOT/codex/tools/ensure-gitea-collaborator.sh"
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
[[ "$(fixture_required_docs "$small_fixture")" == '00-summary.md' ]]
[[ "$(fixture_required_docs "$unclear_fixture")" == '00-summary.md' ]]
[[ "$(fixture_required_docs "$complex_fixture")" == $'00-summary.md\n01-spec.md\n02-plan.md' ]]

for template in 00-summary.md 01-spec.md 02-plan.md 03-verification.md; do
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

summary_template="$ROOT/templates/docs/changes/_template/00-summary.md"
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
