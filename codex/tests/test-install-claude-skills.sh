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

mkdir -p "$tmp_home/invalid-home/.claude/skills"
printf '%s\n' 'not-a-directory' >"$tmp_home/invalid-home/.claude/skills/aisoft-platform"
set +e
invalid_target_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home/invalid-home" 2>&1)"
invalid_target_status=$?
set -e
[[ "$invalid_target_status" == 1 ]] || fail 'non-directory skill target must make check-drift fail'
grep -Fqx 'DRIFT: invalid target' <<<"$invalid_target_output" ||
  fail 'check-drift must distinguish an invalid target from NOT_INSTALLED'

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

printf '%s\n' 'stale' >"$tmp_home/.claude/skills/aisoft-platform/references/stale.md"
set +e
extra_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
extra_status=$?
set -e
[[ "$extra_status" == 1 ]] || fail 'unexpected target file must make check-drift fail'
grep -Fqx 'DRIFT: unexpected references/stale.md' <<<"$extra_output" ||
  fail 'check-drift must identify the unexpected target file'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
[[ ! -e "$tmp_home/.claude/skills/aisoft-platform/references/stale.md" ]] ||
  fail 'install.sh must prune unexpected target files'
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'reinstall after stale-file pruning must be CLEAN'

printf '%s\n' 'content-drift' >>"$tmp_home/.claude/skills/aisoft-platform/SKILL.md"
set +e
content_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
content_status=$?
set -e
[[ "$content_status" == 1 ]] || fail 'changed installed content must make check-drift fail'
grep -Fqx 'DRIFT: SKILL.md' <<<"$content_output" ||
  fail 'check-drift must identify changed SKILL.md content'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
rm -f -- "$tmp_home/.claude/skills/aisoft-platform/references/private-gitea-access.md"
set +e
missing_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
missing_status=$?
set -e
[[ "$missing_status" == 1 ]] || fail 'missing installed reference must make check-drift fail'
grep -Fqx 'DRIFT: references/private-gitea-access.md' <<<"$missing_output" ||
  fail 'check-drift must identify the missing installed reference'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'final exact reinstall must be CLEAN'

rm -f -- "$tmp_home/.claude/skills/aisoft-platform/SKILL.md"
ln -s "$root/skill-for-claude/SKILL.md" \
  "$tmp_home/.claude/skills/aisoft-platform/SKILL.md"
set +e
skill_symlink_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
skill_symlink_status=$?
set -e
[[ "$skill_symlink_status" == 1 ]] || fail 'symlink SKILL.md must make check-drift fail'
grep -Fqx 'DRIFT: SKILL.md' <<<"$skill_symlink_output" ||
  fail 'check-drift must reject a byte-identical SKILL.md symlink'
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'reinstall must repair a symlink SKILL.md'

mv "$tmp_home/.claude/skills/aisoft-platform/references" \
  "$tmp_home/references-symlink-destination"
ln -s "$tmp_home/references-symlink-destination" \
  "$tmp_home/.claude/skills/aisoft-platform/references"
set +e
refs_symlink_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
refs_symlink_status=$?
set -e
[[ "$refs_symlink_status" == 1 ]] || fail 'symlink references directory must make check-drift fail'
grep -Fqx 'DRIFT: references' <<<"$refs_symlink_output" ||
  fail 'check-drift must reject a references directory symlink'
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'reinstall must repair a symlink references directory'

mkdir -p "$tmp_home/symlink-home/.claude/skills" "$tmp_home/symlink-destination"
printf '%s\n' 'keep' >"$tmp_home/symlink-destination/sentinel"
ln -s "$tmp_home/symlink-destination" \
  "$tmp_home/symlink-home/.claude/skills/aisoft-platform"
set +e
root_symlink_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home/symlink-home" 2>&1)"
root_symlink_status=$?
set -e
[[ "$root_symlink_status" == 1 ]] || fail 'symlink skill target must make check-drift fail'
grep -Fqx 'DRIFT: symlink target' <<<"$root_symlink_output" ||
  fail 'check-drift must reject a symlink skill target explicitly'
set +e
symlink_output="$(bash "$root/skill-for-claude/install.sh" "$tmp_home/symlink-home" 2>&1)"
symlink_status=$?
set -e
[[ "$symlink_status" == 1 ]] || fail 'installer must reject a symlink skill target'
grep -Fq 'refusing symlink skill target' <<<"$symlink_output" ||
  fail 'symlink target rejection must be explicit'
grep -Fqx 'keep' "$tmp_home/symlink-destination/sentinel" ||
  fail 'installer must not mutate a symlink destination'

echo 'claude skill install tests passed'
