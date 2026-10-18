#!/usr/bin/env bash
# Compare the Codex landing of every skill skills/skills.manifest declares for
# codex with its installed copy (#379: skills/ is the single source).
# NOT_INSTALLED is informational (exit 0); any partial or byte-level drift exits 1.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
skills_root="$target_home/.agents/skills"

# shellcheck disable=SC1091
source "$root/codex/lib/skills-manifest.sh"
aisoft_skills_manifest_load "$root" codex || exit 2
names=(${AISOFT_SKILL_NAMES[@]+"${AISOFT_SKILL_NAMES[@]}"})
if [[ "${#names[@]}" == 0 ]]; then
  echo 'no skills declared for codex in skills/skills.manifest' >&2
  exit 2
fi
sources=()
for name in "${names[@]}"; do
  sources+=("$root/skills/$name")
done

present=0
for name in "${names[@]}"; do
  [[ ! -e "$skills_root/$name" && ! -L "$skills_root/$name" ]] || present=1
done
if [[ "$present" == "0" ]]; then
  echo 'NOT_INSTALLED'
  exit 0
fi

drift=0
for index in "${!names[@]}"; do
  name="${names[$index]}"
  source_path="${sources[$index]}"
  target="$skills_root/$name"

  if [[ -L "$target" || ! -d "$target" ]]; then
    echo "DRIFT: $name invalid-or-missing-target"
    drift=1
    continue
  fi

  while IFS= read -r -d '' source_file; do
    relative="${source_file#"$source_path"/}"
    installed_file="$target/$relative"
    if [[ ! -f "$installed_file" || -L "$installed_file" ]] ||
      ! cmp -s "$source_file" "$installed_file"; then
      echo "DRIFT: $name/$relative"
      drift=1
    fi
  done < <(find "$source_path" -type f -print0)

  while IFS= read -r -d '' installed_file; do
    relative="${installed_file#"$target"/}"
    if [[ ! -f "$source_path/$relative" || -L "$installed_file" ]]; then
      echo "DRIFT: $name unexpected $relative"
      drift=1
    fi
  done < <(find "$target" \( -type f -o -type l \) -print0)
done

if [[ "$drift" == "0" ]]; then
  echo 'CLEAN'
  exit 0
fi
exit 1
