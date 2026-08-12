#!/usr/bin/env bash
# Install the Claude-side aisoft-platform skill from the repository source.
# References are copied from skill-for-codex/references (single source of truth).
# The destination is an exact managed tree: stale files are pruned before install.
# No credentials, runtime, or provider state is installed.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
target="$target_home/.claude/skills/aisoft-platform"
refs_source="$root/skill-for-codex/references"

[[ -f "$root/skill-for-claude/SKILL.md" ]] || {
  printf 'missing source: %s\n' "$root/skill-for-claude/SKILL.md" >&2
  exit 1
}
[[ -d "$refs_source" ]] || {
  printf 'missing shared references: %s\n' "$refs_source" >&2
  exit 1
}

[[ ! -L "$target" ]] || {
  printf 'refusing symlink skill target: %s\n' "$target" >&2
  exit 1
}

is_expected_entry() {
  local path="$1" relative name
  relative="${path#"$target"/}"
  case "$relative" in
    SKILL.md)
      [[ -f "$path" && ! -L "$path" ]]
      return
      ;;
    references)
      [[ -d "$path" && ! -L "$path" ]]
      return
      ;;
    references/*.md)
      name="${relative#references/}"
      [[ "$name" != */* && -f "$refs_source/$name" && -f "$path" && ! -L "$path" ]]
      return
      ;;
  esac
  return 1
}

install -d -m 755 "$target"
pruned=0
while IFS= read -r -d '' installed_path; do
  if is_expected_entry "$installed_path"; then
    continue
  fi
  if [[ -f "$installed_path" || -L "$installed_path" ]]; then
    rm -f -- "$installed_path"
  elif [[ -d "$installed_path" ]]; then
    rmdir -- "$installed_path" 2>/dev/null || {
      printf 'cannot prune non-empty unmanaged directory: %s\n' "$installed_path" >&2
      exit 1
    }
  else
    printf 'refusing unmanaged special file: %s\n' "$installed_path" >&2
    exit 1
  fi
  pruned=$((pruned + 1))
done < <(find "$target" -mindepth 1 -depth -print0)

install -d -m 755 "$target/references"
install -m 644 "$root/skill-for-claude/SKILL.md" "$target/SKILL.md"
for ref in "$refs_source"/*.md; do
  install -m 644 "$ref" "$target/references/$(basename "$ref")"
done

printf 'Claude aisoft-platform skill installed in %s\n' "$target"
printf '%s\n' 'References copied from skill-for-codex/references (single source).'
printf 'Pruned %s stale target entries; installed tree is exact.\n' "$pruned"
printf '%s\n' 'No credentials, runtime, or provider state was installed.'
