#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

bash "$root/codex/install-skills.sh" "$test_root/home" >/dev/null

for skill in \
  aisoft-platform \
  gitea-analyze-change \
  gitea-spec-plan \
  gitea-development-loop \
  gitea-implement-change \
  gitea-platform-ops \
  issue-session-flow; do
  test -f "$test_root/home/.agents/skills/$skill/SKILL.md"
done

test ! -e "$test_root/home/.config/systemd"
test ! -e "$test_root/home/.config/aisoft"
test ! -e "$test_root/home/.git-credentials"
test ! -e "$test_root/home/agent"

first_manifest="$test_root/first.manifest"
second_manifest="$test_root/second.manifest"
find "$test_root/home/.agents/skills" -type f -print0 |
  sort -z |
  xargs -0 shasum >"$first_manifest"
bash "$root/codex/install-skills.sh" "$test_root/home" >/dev/null
find "$test_root/home/.agents/skills" -type f -print0 |
  sort -z |
  xargs -0 shasum >"$second_manifest"
cmp "$first_manifest" "$second_manifest"

printf '%s\n' 'install-skills tests passed'
