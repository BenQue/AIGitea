#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
action="${2:-install}"
[[ "$#" -le 2 && ( "$action" == install || "$action" == --rollback ) ]] || {
  printf '%s\n' 'Usage: install-skills.sh [target-home] [--rollback]' >&2
  exit 2
}
target_root="$target_home/.agents/skills"
matt_version="v1.3.1"
matt_source="$root/codex/vendor/mattpocock/$matt_version"

# Source provenance/staleness remains before the first filesystem write.
# shellcheck disable=SC1091
source "$root/codex/lib/install-source-guard.sh"
aisoft_install_source_guard install-skills "$root" \
  skills "$(aisoft_install_source_file_count "$root"/codex/skills/*/SKILL.md "$root/skill-for-codex/SKILL.md")" \
  'matt snapshot' "$matt_version" action "$action"

matt_snapshot() {
  if [[ "$action" == --rollback ]]; then
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$root/codex/runtime" \
      python3 -m aisoft_loop.matt_snapshot "$1" "$matt_source" "$target_home" --rollback
  else
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$root/codex/runtime" \
      python3 -m aisoft_loop.matt_snapshot "$1" "$matt_source" "$target_home"
  fi
}

# Fail before copying adapters for bad source, unmanaged entries or pointer drift.
matt_snapshot preflight-install >/dev/null
for skill in "$root"/codex/skills/* "$root/skill-for-codex"; do
  [[ -d "$skill" ]] || continue
  name="$(basename "$skill")"
  [[ "$name" != skill-for-codex ]] || name=aisoft-platform
  target="$target_root/$name"
  if [[ -L "$target" || ( -e "$target" && ! -d "$target" ) ]]; then
    printf 'refusing linked or non-directory adapter target: %s\n' "$target" >&2
    exit 1
  fi
done

# A rollback restores Matt's N-1 snapshot and exact owned entrance set. It does
# not install new adapter bytes or modify any independent provider plugin.
if [[ "$action" != --rollback ]]; then
  install -d -m 700 "$target_home/.agents"
  install -d -m 755 "$target_root"
  for skill in "$root"/codex/skills/* "$root/skill-for-codex"; do
    [[ -d "$skill" ]] || continue
    name="$(basename "$skill")"
    [[ "$name" != skill-for-codex ]] || name=aisoft-platform
    install -d -m 755 "$target_root/$name"
    cp -a "$skill/." "$target_root/$name/"
  done
fi

matt_snapshot install
printf 'AISoftPlatform skills are in %s\n' "$target_root"
printf '%s\n' 'No credentials, runtime, systemd unit, profile, provider, timer, or independent Claude plugin was installed.'
