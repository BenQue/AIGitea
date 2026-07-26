#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
target_root="$target_home/.agents/skills"

install -d -m 700 "$target_home/.agents"
install -d -m 755 "$target_root"

for skill in "$root"/codex/skills/*; do
  [[ -d "$skill" ]] || continue
  target="$target_root/$(basename "$skill")"
  install -d -m 755 "$target"
  cp -a "$skill/." "$target/"
done

if [[ -f "$root/skill-for-codex/SKILL.md" ]]; then
  install -d -m 755 "$target_root/aisoft-platform"
  cp -a "$root/skill-for-codex/." "$target_root/aisoft-platform/"
fi

printf 'AISoftPlatform skills installed in %s\n' "$target_root"
printf '%s\n' 'No credentials, runtime, systemd unit, profile, provider, or timer was installed.'
