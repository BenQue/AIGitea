#!/usr/bin/env bash
# Install the Claude landing of every skill skills/skills.manifest declares for
# claude (#379: skills/ is the single source for every provider).
# Each declared skill directory is an exact managed tree: SKILL.md plus, when
# the source has them, references/*.md. Stale files inside it are pruned before
# install; Codex-only metadata (agents/) is never copied here. The managed
# boundary stops at those directories -- ~/.claude/skills itself is never
# pruned, so skills this repository does not declare are left untouched.
# No credentials, runtime, or provider state is installed.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target_home="${1:-$HOME}"
source_root="$root/skills"
manifest="$source_root/skills.manifest"
skills_root="$target_home/.claude/skills"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

[[ -f "$manifest" ]] || fail "missing skill manifest: $manifest"

# Source provenance and staleness gate (#162, #171, #254). Must stay before the
# first filesystem write below; both the prune loop and the `install -d` that
# precedes it count as writes. This installer is the one where a stale source
# does more than install an older file: each declared skill tree is exact, so
# the prune deletes the entries only the newer contract has, and the success
# lines below still print. check-drift.sh compares the same stale checkout
# afterwards, so nothing else in the repository can catch it.
#
# It also runs before the manifest is parsed. A stale checkout can carry an
# older manifest, and a format complaint about that manifest would send the
# operator after the wrong defect; the gate answers first.
#
# skills/ ships no version-bearing JSON, so there is no revision scalar to print
# and the readable quantities are file counts, with the commit line the guard
# always prints carrying which version this is: every SKILL.md in the single
# source (the guard runs before the manifest is parsed, so it cannot yet know
# which of them land on Claude) and every reference file copied into a Claude
# landing.
# shellcheck disable=SC1091
source "$root/codex/lib/install-source-guard.sh"

aisoft_install_source_guard skill-for-claude/install "$root" \
  skills "$(aisoft_install_source_file_count "$source_root"/*/SKILL.md)" \
  references "$(aisoft_install_source_file_count "$source_root"/*/references/*.md)"

# The manifest is the only place the skill set is written down; every
# installer and drift checker reads it through the same parser.
# shellcheck disable=SC1091
source "$root/codex/lib/skills-manifest.sh"
aisoft_skills_manifest_load "$root" claude || exit 1
names=(${AISOFT_SKILL_NAMES[@]+"${AISOFT_SKILL_NAMES[@]}"})
[[ "${#names[@]}" -gt 0 ]] || fail "no skills declared for claude in $manifest"

is_expected_entry() {
  local skill="$1" relative="$2" path="$3" name
  case "$relative" in
    SKILL.md)
      [[ -f "$path" && ! -L "$path" ]]
      return
      ;;
    references)
      [[ -d "$source_root/$skill/references" && -d "$path" && ! -L "$path" ]]
      return
      ;;
    references/*.md)
      name="${relative#references/}"
      [[ "$name" != */* && -f "$source_root/$skill/references/$name" && -f "$path" && ! -L "$path" ]]
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
for name in "${names[@]}"; do
  target="$skills_root/$name"

  install -d -m 755 "$target"
  while IFS= read -r -d '' installed_path; do
    relative="${installed_path#"$target"/}"
    if is_expected_entry "$name" "$relative" "$installed_path"; then
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
  if [[ -d "$source_root/$name/references" ]]; then
    install -d -m 755 "$target/references"
    for ref in "$source_root/$name/references"/*.md; do
      [[ -f "$ref" ]] || continue
      install -m 644 "$ref" "$target/references/$(basename -- "$ref")"
    done
  fi
  printf 'installed skill %s in %s\n' "$name" "$target"
done

printf 'Claude skills installed from %s: %s\n' "$manifest" "${names[*]}"
printf '%s\n' 'Installed from the single skill source skills/ (Claude landing: SKILL.md and references).'
printf 'Pruned %s stale entries; each declared skill tree is exact.\n' "$pruned"
printf '%s\n' 'Undeclared skills under .claude/skills were not read or modified.'
printf '%s\n' 'No credentials, runtime, or provider state was installed.'
