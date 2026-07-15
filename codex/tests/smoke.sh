#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

command -v rg >/dev/null

for script in "$ROOT"/codex/agent/*.sh "$ROOT"/codex/install-vm.sh; do
  bash -n "$script"
done

if rg -n -g '!**/tests/smoke.sh' 'dangerously-bypass|--yolo|danger-full-access' "$ROOT/codex"; then
  echo '检测到禁止的 Codex 绕过参数' >&2
  exit 1
fi

for skill in gitea-analyze-change gitea-spec-plan gitea-development-loop gitea-implement-change gitea-platform-ops; do
  [[ -f "$ROOT/codex/skills/$skill/SKILL.md" ]]
  [[ -f "$ROOT/codex/skills/$skill/agents/openai.yaml" ]]
  grep -Fq "\$$skill" "$ROOT/codex/skills/$skill/agents/openai.yaml"
done

[[ -f "$ROOT/skill-for-codex/SKILL.md" ]]
[[ -f "$ROOT/skill-for-codex/agents/openai.yaml" ]]
grep -Fq '/mnt/mac/Users/benque/Documents/AISoftPlatform/' "$ROOT/codex/global-AGENTS.md"

grep -Fq "ANALYSIS_PROVIDER=\"\${ANALYSIS_PROVIDER:-claude}\"" "$ROOT/codex/agent/provider-poll.sh"
grep -Fq "IMPLEMENT_PROVIDER=\"\${IMPLEMENT_PROVIDER:-none}\"" "$ROOT/codex/agent/provider-poll.sh"
grep -Fq "if [[ \"\$sandbox\" == read-only" "$ROOT/codex/agent/common.sh"
grep -Fq "args+=(--add-dir \"\$platform_docs\")" "$ROOT/codex/agent/common.sh"
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

echo 'Codex platform static smoke checks passed.'
