#!/usr/bin/env bash
# Install the Claude-side aisoft-platform skill from the repository source.
# References are copied from skill-for-codex/references (single source of truth).
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

install -d -m 755 "$target" "$target/references"
install -m 644 "$root/skill-for-claude/SKILL.md" "$target/SKILL.md"
for ref in "$refs_source"/*.md; do
  install -m 644 "$ref" "$target/references/$(basename "$ref")"
done

printf 'Claude aisoft-platform skill installed in %s\n' "$target"
printf '%s\n' 'References copied from skill-for-codex/references (single source).'
printf '%s\n' 'No credentials, runtime, or provider state was installed.'
