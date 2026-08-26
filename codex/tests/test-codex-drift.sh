#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

not_installed="$(bash "$root/codex/check-drift.sh" "$test_root/empty-home")"
[[ "$not_installed" == "NOT_INSTALLED" ]]

bash "$root/codex/install-skills.sh" "$test_root/home" >/dev/null
clean="$(bash "$root/codex/check-drift.sh" "$test_root/home")"
[[ "$clean" == "CLEAN" ]]

printf '\nlocal drift\n' >>"$test_root/home/.agents/skills/gitea-analyze-change/SKILL.md"
set +e
drift="$(bash "$root/codex/check-drift.sh" "$test_root/home")"
status=$?
set -e
[[ "$status" == "1" ]]
grep -Fq 'DRIFT: gitea-analyze-change/SKILL.md' <<<"$drift"

printf '%s\n' 'codex drift tests passed'
