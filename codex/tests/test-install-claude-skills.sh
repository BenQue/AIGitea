#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'NOT_INSTALLED' ||
  fail 'check-drift must report NOT_INSTALLED for a home without the skill'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
first="$(cd "$tmp_home/.claude/skills/aisoft-platform" && find . -type f | LC_ALL=C sort)"
first_hash="$(cd "$tmp_home/.claude/skills/aisoft-platform" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256)"

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
second="$(cd "$tmp_home/.claude/skills/aisoft-platform" && find . -type f | LC_ALL=C sort)"
second_hash="$(cd "$tmp_home/.claude/skills/aisoft-platform" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256)"

[[ "$first" == "$second" && "$first_hash" == "$second_hash" ]] ||
  fail 'install.sh must be idempotent across two runs'

[[ -f "$tmp_home/.claude/skills/aisoft-platform/SKILL.md" ]] ||
  fail 'SKILL.md was not installed'
[[ -f "$tmp_home/.claude/skills/aisoft-platform/references/onboarding-runbook.md" ]] ||
  fail 'shared onboarding runbook was not installed'
[[ -f "$tmp_home/.claude/skills/aisoft-platform/references/private-gitea-access.md" ]] ||
  fail 'shared private-gitea-access reference was not installed'

diff -q "$root/skill-for-codex/references/onboarding-runbook.md" \
  "$tmp_home/.claude/skills/aisoft-platform/references/onboarding-runbook.md" >/dev/null ||
  fail 'installed runbook must be byte-identical to the single source'

if grep -RIlE 'GITEA_TOKEN=|Authorization: token|BEGIN (OPENSSH|RSA) PRIVATE KEY' \
  "$tmp_home/.claude/skills/aisoft-platform" >/dev/null 2>&1; then
  fail 'installed skill must not contain credentials'
fi

"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'check-drift must report CLEAN right after install'

echo 'claude skill install tests passed'
