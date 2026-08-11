#!/usr/bin/env bash
# Report drift between the installed Claude skill and the repository source.
# Standalone operational tool: NOT_INSTALLED exits 0 (machine without Claude),
# DRIFT exits 1 so a caller can gate on freshness explicitly.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
target="$target_home/.claude/skills/aisoft-platform"
refs_source="$root/skill-for-codex/references"

if [[ ! -d "$target" ]]; then
  echo 'NOT_INSTALLED'
  exit 0
fi

drift=0
if ! diff -q "$root/skill-for-claude/SKILL.md" "$target/SKILL.md" >/dev/null 2>&1; then
  echo "DRIFT: SKILL.md"
  drift=1
fi
for ref in "$refs_source"/*.md; do
  name="$(basename "$ref")"
  if ! diff -q "$ref" "$target/references/$name" >/dev/null 2>&1; then
    echo "DRIFT: references/$name"
    drift=1
  fi
done

if [[ "$drift" == "0" ]]; then
  echo 'CLEAN'
  exit 0
fi
exit 1
