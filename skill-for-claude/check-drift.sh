#!/usr/bin/env bash
# Report drift between the installed Claude skill and the repository source.
# Standalone operational tool: NOT_INSTALLED exits 0 (machine without Claude),
# DRIFT exits 1 so a caller can gate on freshness explicitly.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
target="$target_home/.claude/skills/aisoft-platform"
refs_source="$root/skill-for-codex/references"

if [[ -L "$target" ]]; then
  echo 'DRIFT: symlink target'
  exit 1
fi
if [[ ! -e "$target" ]]; then
  echo 'NOT_INSTALLED'
  exit 0
fi
if [[ ! -d "$target" ]]; then
  echo 'DRIFT: invalid target'
  exit 1
fi

drift=0
is_expected_relative() {
  local relative="$1" name
  case "$relative" in
    SKILL.md|references) return 0 ;;
    references/*.md)
      name="${relative#references/}"
      [[ "$name" != */* && -f "$refs_source/$name" ]]
      return
      ;;
  esac
  return 1
}

if [[ ! -f "$target/SKILL.md" || -L "$target/SKILL.md" ]] ||
  ! diff -q "$root/skill-for-claude/SKILL.md" "$target/SKILL.md" >/dev/null 2>&1; then
  echo "DRIFT: SKILL.md"
  drift=1
fi
if [[ ! -d "$target/references" || -L "$target/references" ]]; then
  echo 'DRIFT: references'
  drift=1
else
  for ref in "$refs_source"/*.md; do
    name="$(basename "$ref")"
    if [[ ! -f "$target/references/$name" || -L "$target/references/$name" ]] ||
      ! diff -q "$ref" "$target/references/$name" >/dev/null 2>&1; then
      echo "DRIFT: references/$name"
      drift=1
    fi
  done
fi

while IFS= read -r -d '' installed_path; do
  relative="${installed_path#"$target"/}"
  if ! is_expected_relative "$relative"; then
    echo "DRIFT: unexpected $relative"
    drift=1
  fi
done < <(find "$target" -mindepth 1 -print0)

if [[ "$drift" == "0" ]]; then
  echo 'CLEAN'
  exit 0
fi
exit 1
