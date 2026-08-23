#!/usr/bin/env bash
# Install the Claude-side skills declared by skill-for-claude/skills.manifest.
# Each declared skill directory is an exact managed tree: stale files inside it
# are pruned before install. The managed boundary stops at those directories --
# ~/.claude/skills itself is never pruned, so skills this repository does not
# declare are left untouched.
# References are copied from skill-for-codex/references (single source of truth).
# No credentials, runtime, or provider state is installed.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
source_root="$root/skill-for-claude"
manifest="$source_root/skills.manifest"
refs_source="$root/skill-for-codex/references"
skills_root="$target_home/.claude/skills"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

[[ -f "$manifest" ]] || fail "missing skill manifest: $manifest"
[[ -d "$refs_source" ]] || fail "missing shared references: $refs_source"

# The manifest is the only place the skill set is written down; both this
# installer and check-drift.sh read it rather than carrying their own copy.
names=()
modes=()
while read -r name mode extra || [[ -n "$name" ]]; do
  [[ -n "$name" && "$name" != \#* ]] || continue
  [[ -z "$extra" ]] || fail "malformed manifest line: $name $mode $extra"
  [[ "$name" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || fail "invalid skill name: $name"
  case "$mode" in
    shared | none) ;;
    *) fail "invalid references mode for $name: ${mode:-<empty>}" ;;
  esac
  [[ -f "$source_root/$name/SKILL.md" ]] || fail "missing source: $source_root/$name/SKILL.md"
  names+=("$name")
  modes+=("$mode")
done <"$manifest"

[[ "${#names[@]}" -gt 0 ]] || fail "no skills declared in $manifest"

# Fail closed on the reverse mismatch too: a skill added to the tree but not to
# the manifest would otherwise be silently left uninstalled.
while IFS= read -r -d '' source_skill; do
  candidate="$(basename -- "$(dirname -- "$source_skill")")"
  declared=0
  for name in "${names[@]}"; do
    [[ "$name" == "$candidate" ]] && declared=1 && break
  done
  [[ "$declared" == 1 ]] || fail "undeclared skill source: $candidate (add it to $manifest)"
done < <(find "$source_root" -mindepth 2 -maxdepth 2 -name SKILL.md -print0)

is_expected_entry() {
  local mode="$1" relative="$2" path="$3" name
  case "$relative" in
    SKILL.md)
      [[ -f "$path" && ! -L "$path" ]]
      return
      ;;
    references)
      [[ "$mode" == shared && -d "$path" && ! -L "$path" ]]
      return
      ;;
    references/*.md)
      [[ "$mode" == shared ]] || return 1
      name="${relative#references/}"
      [[ "$name" != */* && -f "$refs_source/$name" && -f "$path" && ! -L "$path" ]]
      return
      ;;
  esac
  return 1
}

# Reject every symlink target before installing anything, so a bad target never
# leaves a half-installed skill set behind.
for name in "${names[@]}"; do
  [[ ! -L "$skills_root/$name" ]] || fail "refusing symlink skill target: $skills_root/$name"
done

pruned=0
for index in "${!names[@]}"; do
  name="${names[$index]}"
  mode="${modes[$index]}"
  target="$skills_root/$name"

  install -d -m 755 "$target"
  while IFS= read -r -d '' installed_path; do
    relative="${installed_path#"$target"/}"
    if is_expected_entry "$mode" "$relative" "$installed_path"; then
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

  install -m 644 "$source_root/$name/SKILL.md" "$target/SKILL.md"
  if [[ "$mode" == shared ]]; then
    install -d -m 755 "$target/references"
    for ref in "$refs_source"/*.md; do
      install -m 644 "$ref" "$target/references/$(basename -- "$ref")"
    done
  fi
  printf 'installed skill %s in %s\n' "$name" "$target"
done

printf 'Claude skills installed from %s: %s\n' "$manifest" "${names[*]}"
printf '%s\n' 'Shared references copied from skill-for-codex/references (single source).'
printf 'Pruned %s stale entries; each declared skill tree is exact.\n' "$pruned"
printf '%s\n' 'Undeclared skills under .claude/skills were not read or modified.'
printf '%s\n' 'No credentials, runtime, or provider state was installed.'
