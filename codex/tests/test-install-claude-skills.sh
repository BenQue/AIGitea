#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT

skills="$tmp_home/.claude/skills"
platform="$skills/aisoft-platform"
session="$skills/issue-session-flow"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'NOT_INSTALLED' ||
  fail 'check-drift must report NOT_INSTALLED for a home without any declared skill'

mkdir -p "$tmp_home/invalid-home/.claude/skills"
printf '%s\n' 'not-a-directory' >"$tmp_home/invalid-home/.claude/skills/aisoft-platform"
set +e
invalid_target_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home/invalid-home" 2>&1)"
invalid_target_status=$?
set -e
[[ "$invalid_target_status" == 1 ]] || fail 'non-directory skill target must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform invalid target' <<<"$invalid_target_output" ||
  fail 'check-drift must distinguish an invalid target from NOT_INSTALLED'
# One skill present and one absent is drift, never NOT_INSTALLED: reporting
# absence would hide the skill that failed to land.
grep -Fqx 'DRIFT: issue-session-flow missing' <<<"$invalid_target_output" ||
  fail 'check-drift must report a partially installed skill set as drift'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
first="$(cd "$skills" && find . -type f | LC_ALL=C sort)"
first_hash="$(cd "$skills" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256)"

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
second="$(cd "$skills" && find . -type f | LC_ALL=C sort)"
second_hash="$(cd "$skills" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256)"

[[ "$first" == "$second" && "$first_hash" == "$second_hash" ]] ||
  fail 'install.sh must be idempotent across two runs'

[[ -f "$platform/SKILL.md" ]] || fail 'aisoft-platform SKILL.md was not installed'
[[ -f "$session/SKILL.md" ]] || fail 'issue-session-flow SKILL.md was not installed'
[[ -f "$platform/references/onboarding-runbook.md" ]] ||
  fail 'shared onboarding runbook was not installed'
[[ -f "$platform/references/private-gitea-access.md" ]] ||
  fail 'shared private-gitea-access reference was not installed'
# A skill declared "none" gets no references directory at all.
[[ ! -e "$session/references" ]] ||
  fail 'a skill declared without shared references must not get a references directory'

diff -q "$root/skill-for-codex/references/onboarding-runbook.md" \
  "$platform/references/onboarding-runbook.md" >/dev/null ||
  fail 'installed runbook must be byte-identical to the single source'
diff -q "$root/skill-for-claude/issue-session-flow/SKILL.md" "$session/SKILL.md" >/dev/null ||
  fail 'installed issue-session-flow must be byte-identical to the source'

# The cross-reference is what keeps the two skills from being found in
# isolation; losing it is a silent discovery regression.
grep -Fq 'issue-session-flow' "$platform/SKILL.md" ||
  fail 'aisoft-platform SKILL.md must cross-reference issue-session-flow'

if grep -RIlE 'GITEA_TOKEN=|Authorization: token|BEGIN (OPENSSH|RSA) PRIVATE KEY' \
  "$skills" >/dev/null 2>&1; then
  fail 'installed skills must not contain credentials'
fi

"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'check-drift must report CLEAN right after install'

# The managed boundary stops at each declared skill directory. A skill the user
# installed by hand must survive install and stay invisible to check-drift.
mkdir -p "$skills/unrelated-skill"
printf '%s\n' 'keep me' >"$skills/unrelated-skill/SKILL.md"
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
grep -Fqx 'keep me' "$skills/unrelated-skill/SKILL.md" ||
  fail 'install.sh must not prune skills this repository does not declare'
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'an undeclared skill directory must not be reported as drift'

printf '%s\n' 'stale' >"$platform/references/stale.md"
set +e
extra_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
extra_status=$?
set -e
[[ "$extra_status" == 1 ]] || fail 'unexpected target file must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform unexpected references/stale.md' <<<"$extra_output" ||
  fail 'check-drift must identify the unexpected target file'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
[[ ! -e "$platform/references/stale.md" ]] ||
  fail 'install.sh must prune unexpected target files'
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'reinstall after stale-file pruning must be CLEAN'

printf '%s\n' 'stray' >"$session/stray.md"
set +e
session_extra_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
session_extra_status=$?
set -e
[[ "$session_extra_status" == 1 ]] || fail 'unexpected file in a none-references skill must fail'
grep -Fqx 'DRIFT: issue-session-flow unexpected stray.md' <<<"$session_extra_output" ||
  fail 'check-drift must qualify unexpected files by skill'
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
[[ ! -e "$session/stray.md" ]] || fail 'install.sh must prune strays in every declared skill'

# A references directory under a "none" skill is unmanaged content, not an
# expected entry: it must be pruned like any other stray.
mkdir -p "$session/references"
printf '%s\n' 'nope' >"$session/references/onboarding-runbook.md"
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
[[ ! -e "$session/references" ]] ||
  fail 'a references directory under a none-mode skill must be pruned'

printf '%s\n' 'content-drift' >>"$platform/SKILL.md"
set +e
content_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
content_status=$?
set -e
[[ "$content_status" == 1 ]] || fail 'changed installed content must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform/SKILL.md' <<<"$content_output" ||
  fail 'check-drift must identify changed SKILL.md content'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
printf '%s\n' 'content-drift' >>"$session/SKILL.md"
set +e
session_content_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
session_content_status=$?
set -e
[[ "$session_content_status" == 1 ]] || fail 'changed issue-session-flow content must fail'
grep -Fqx 'DRIFT: issue-session-flow/SKILL.md' <<<"$session_content_output" ||
  fail 'check-drift must identify the drifting skill by name'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
rm -f -- "$platform/references/private-gitea-access.md"
set +e
missing_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
missing_status=$?
set -e
[[ "$missing_status" == 1 ]] || fail 'missing installed reference must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform/references/private-gitea-access.md' <<<"$missing_output" ||
  fail 'check-drift must identify the missing installed reference'

bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'final exact reinstall must be CLEAN'

rm -f -- "$platform/SKILL.md"
ln -s "$root/skill-for-claude/aisoft-platform/SKILL.md" "$platform/SKILL.md"
set +e
skill_symlink_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
skill_symlink_status=$?
set -e
[[ "$skill_symlink_status" == 1 ]] || fail 'symlink SKILL.md must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform/SKILL.md' <<<"$skill_symlink_output" ||
  fail 'check-drift must reject a byte-identical SKILL.md symlink'
bash "$root/skill-for-claude/install.sh" "$tmp_home" >/dev/null
"$root/skill-for-claude/check-drift.sh" "$tmp_home" | grep -Fqx 'CLEAN' ||
  fail 'reinstall must repair a symlink SKILL.md'

mv "$platform/references" "$tmp_home/references-symlink-destination"
ln -s "$tmp_home/references-symlink-destination" "$platform/references"
set +e
refs_symlink_output="$("$root/skill-for-claude/check-drift.sh" "$tmp_home" 2>&1)"
refs_symlink_status=$?
set -e
[[ "$refs_symlink_status" == 1 ]] || fail 'symlink references directory must make check-drift fail'
grep -Fqx 'DRIFT: aisoft-platform/references' <<<"$refs_symlink_output" ||
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
grep -Fqx 'DRIFT: aisoft-platform symlink target' <<<"$root_symlink_output" ||
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
# The symlink is rejected before anything is written, so no other declared skill
# may be left half-installed behind it.
[[ ! -e "$tmp_home/symlink-home/.claude/skills/issue-session-flow" ]] ||
  fail 'a rejected symlink target must abort before installing any skill'

# Every skill source in the tree must be declared, or it would silently never
# install. This is the mirror of the prune rule.
undeclared_root="$(mktemp -d)"
cp -R "$root/skill-for-claude" "$undeclared_root/skill-for-claude"
cp -R "$root/skill-for-codex" "$undeclared_root/skill-for-codex"
mkdir -p "$undeclared_root/skill-for-claude/ghost-skill"
printf '%s\n' 'ghost' >"$undeclared_root/skill-for-claude/ghost-skill/SKILL.md"
set +e
undeclared_output="$(bash "$undeclared_root/skill-for-claude/install.sh" "$tmp_home/ghost-home" 2>&1)"
undeclared_status=$?
set -e
rm -rf "$undeclared_root"
[[ "$undeclared_status" == 1 ]] || fail 'an undeclared skill source must make install fail closed'
grep -Fq 'undeclared skill source: ghost-skill' <<<"$undeclared_output" ||
  fail 'install must name the undeclared skill source'

echo 'claude skill install tests passed'
