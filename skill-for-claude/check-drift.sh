#!/usr/bin/env bash
# Report drift between the installed Claude skills and the single skill source.
# Standalone operational tool: NOT_INSTALLED exits 0 (machine without Claude),
# DRIFT exits 1 so a caller can gate on freshness explicitly.
# Every DRIFT line is qualified by skill name, because more than one skill is
# managed. Only skills skills/skills.manifest declares for claude are inspected;
# anything else under .claude/skills is out of scope and never reported.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
source_root="$root/skills"
skills_root="$target_home/.claude/skills"

# shellcheck disable=SC1091
source "$root/codex/lib/skills-manifest.sh"
aisoft_skills_manifest_load "$root" claude || exit 2
names=(${AISOFT_SKILL_NAMES[@]+"${AISOFT_SKILL_NAMES[@]}"})
if [[ "${#names[@]}" == 0 ]]; then
  printf 'no skills declared for claude in %s\n' "$source_root/skills.manifest" >&2
  exit 2
fi

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
  local skill="$1" relative="$2" name
  case "$relative" in
    SKILL.md) return 0 ;;
    references)
      [[ -d "$source_root/$skill/references" ]]
      return
      ;;
    references/*.md)
      name="${relative#references/}"
      [[ "$name" != */* && -f "$source_root/$skill/references/$name" ]]
      return
      ;;
  esac
  return 1
}

for name in "${names[@]}"; do
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

  if [[ -d "$source_root/$name/references" ]]; then
    if [[ ! -d "$target/references" || -L "$target/references" ]]; then
      echo "DRIFT: $name/references"
      drift=1
    else
      for ref in "$source_root/$name/references"/*.md; do
        [[ -f "$ref" ]] || continue
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
    if ! is_expected_relative "$name" "$relative"; then
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
