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

echo 'Codex platform static smoke checks passed.'
