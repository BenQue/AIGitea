#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
target_root="$target_home/.agents/skills"
matt_version="v1.2.2"
matt_source="$root/codex/vendor/mattpocock/$matt_version"
matt_manifest="$matt_source/manifest.json"
matt_vendor_root="$target_home/.agents/vendor/mattpocock"
matt_release="$matt_vendor_root/releases/$matt_version"

install -d -m 700 "$target_home/.agents"
install -d -m 755 "$target_root"

for skill in "$root"/codex/skills/*; do
  [[ -d "$skill" ]] || continue
  target="$target_root/$(basename "$skill")"
  install -d -m 755 "$target"
  cp -a "$skill/." "$target/"
done

if [[ ! -f "$matt_manifest" ]]; then
  printf 'Matt snapshot manifest is missing: %s\n' "$matt_manifest" >&2
  exit 1
fi
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$root/codex/runtime" \
  python3 -m aisoft_loop.matt_snapshot verify "$matt_source" "$matt_manifest" \
  >/dev/null

install -d -m 755 "$matt_vendor_root/releases"
if [[ ! -d "$matt_release" ]]; then
  matt_stage="$(mktemp -d "$matt_vendor_root/releases/.${matt_version}.stage.XXXXXX")"
  cp -a "$matt_source/." "$matt_stage/"
  chmod -R u=rwX,go=rX "$matt_stage"
  mv "$matt_stage" "$matt_release"
fi
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$root/codex/runtime" \
  python3 -m aisoft_loop.matt_snapshot verify \
  "$matt_release" "$matt_release/manifest.json" >/dev/null

while IFS=$'\t' read -r skill_name skill_directory; do
  target="$target_root/$skill_name"
  if [[ -e "$target" && ! -L "$target" ]]; then
    printf 'refusing to overwrite unmanaged Matt skill: %s\n' "$target" >&2
    exit 1
  fi
  if [[ -L "$target" && "$(readlink "$target")" != ../vendor/mattpocock/* ]]; then
    printf 'refusing to replace unrelated skill symlink: %s\n' "$target" >&2
    exit 1
  fi
  [[ -f "$matt_release/$skill_directory/SKILL.md" ]] || {
    printf 'Matt skill path is missing: %s\n' "$skill_directory" >&2
    exit 1
  }
done < <(jq -r '.skills[] | [.name, (.path | sub("/SKILL.md$"; ""))] | @tsv' "$matt_manifest")

if [[ -L "$matt_vendor_root/current" ]] \
  && [[ "$(readlink "$matt_vendor_root/current")" != "releases/$matt_version" ]]; then
  ln -sfn "$(readlink "$matt_vendor_root/current")" "$matt_vendor_root/previous"
fi
ln -sfn "releases/$matt_version" "$matt_vendor_root/current"

while IFS=$'\t' read -r skill_name skill_directory; do
  ln -sfn \
    "../vendor/mattpocock/current/$skill_directory" \
    "$target_root/$skill_name"
done < <(jq -r '.skills[] | [.name, (.path | sub("/SKILL.md$"; ""))] | @tsv' "$matt_manifest")

if [[ -f "$root/skill-for-codex/SKILL.md" ]]; then
  install -d -m 755 "$target_root/aisoft-platform"
  cp -a "$root/skill-for-codex/." "$target_root/aisoft-platform/"
fi

printf 'AISoftPlatform skills installed in %s\n' "$target_root"
printf 'Matt Pocock skills %s activated from the verified snapshot\n' "$matt_version"
printf '%s\n' 'No credentials, runtime, systemd unit, profile, provider, or timer was installed.'
