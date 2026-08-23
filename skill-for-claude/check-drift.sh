#!/usr/bin/env bash
# Report drift between the installed Claude skills and the repository source.
# Standalone operational tool: NOT_INSTALLED exits 0 (machine without Claude),
# DRIFT exits 1 so a caller can gate on freshness explicitly.
# Every DRIFT line is qualified by skill name, because more than one skill is
# managed. Only declared skills are inspected; anything else under
# .claude/skills is out of scope and never reported.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
source_root="$root/skill-for-claude"
manifest="$source_root/skills.manifest"
refs_source="$root/skill-for-codex/references"
skills_root="$target_home/.claude/skills"

fail() {
  printf '%s\n' "$*" >&2
  exit 2
}

[[ -f "$manifest" ]] || fail "missing skill manifest: $manifest"
[[ -d "$refs_source" ]] || fail "missing shared references: $refs_source"

names=()
modes=()
while read -r name mode extra || [[ -n "$name" ]]; do
  [[ -n "$name" && "$name" != \#* ]] || continue
  [[ -z "$extra" ]] || fail "malformed manifest line: $name $mode $extra"
  case "$mode" in
    shared | none) ;;
    *) fail "invalid references mode for $name: ${mode:-<empty>}" ;;
  esac
  names+=("$name")
  modes+=("$mode")
done <"$manifest"

[[ "${#names[@]}" -gt 0 ]] || fail "no skills declared in $manifest"

# NOT_INSTALLED means this machine has none of the declared skills. A partial
# install is drift, not absence: reporting it as NOT_INSTALLED would hide the
# skill that failed to land.
present=0
for name in "${names[@]}"; do
  [[ ! -e "$skills_root/$name" && ! -L "$skills_root/$name" ]] || present=1
done
if [[ "$present" == 0 ]]; then
  echo 'NOT_INSTALLED'
  exit 0
fi

drift=0

is_expected_relative() {
  local mode="$1" relative="$2" name
  case "$relative" in
    SKILL.md) return 0 ;;
    references)
      [[ "$mode" == shared ]]
      return
      ;;
    references/*.md)
      [[ "$mode" == shared ]] || return 1
      name="${relative#references/}"
      [[ "$name" != */* && -f "$refs_source/$name" ]]
      return
      ;;
  esac
  return 1
}

for index in "${!names[@]}"; do
  name="${names[$index]}"
  mode="${modes[$index]}"
  target="$skills_root/$name"

  if [[ -L "$target" ]]; then
    echo "DRIFT: $name symlink target"
    drift=1
    continue
  fi
  if [[ ! -e "$target" ]]; then
    echo "DRIFT: $name missing"
    drift=1
    continue
  fi
  if [[ ! -d "$target" ]]; then
    echo "DRIFT: $name invalid target"
    drift=1
    continue
  fi

  if [[ ! -f "$target/SKILL.md" || -L "$target/SKILL.md" ]] ||
    ! diff -q "$source_root/$name/SKILL.md" "$target/SKILL.md" >/dev/null 2>&1; then
    echo "DRIFT: $name/SKILL.md"
    drift=1
  fi

  if [[ "$mode" == shared ]]; then
    if [[ ! -d "$target/references" || -L "$target/references" ]]; then
      echo "DRIFT: $name/references"
      drift=1
    else
      for ref in "$refs_source"/*.md; do
        reference_name="$(basename -- "$ref")"
        if [[ ! -f "$target/references/$reference_name" || -L "$target/references/$reference_name" ]] ||
          ! diff -q "$ref" "$target/references/$reference_name" >/dev/null 2>&1; then
          echo "DRIFT: $name/references/$reference_name"
          drift=1
        fi
      done
    fi
  fi

  while IFS= read -r -d '' installed_path; do
    relative="${installed_path#"$target"/}"
    if ! is_expected_relative "$mode" "$relative"; then
      echo "DRIFT: $name unexpected $relative"
      drift=1
    fi
  done < <(find "$target" -mindepth 1 -print0)
done

if [[ "$drift" == "0" ]]; then
  echo 'CLEAN'
  exit 0
fi
exit 1
