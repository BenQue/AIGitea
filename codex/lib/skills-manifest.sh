# shellcheck shell=bash
# Read skills/skills.manifest, the single declaration of platform skills and
# their maintainer-layer landings (#379, ADR 0001 D8). Sourced by both skill
# installers and both check-drift scripts so the skill set is parsed one way.
#
#   aisoft_skills_manifest_load <repo-root> <target>
#
# <target> is claude or codex. On success AISOFT_SKILL_NAMES holds, in manifest
# order, every skill declared for that target. Any malformed line, unknown
# target, missing source or undeclared skills/<name>/SKILL.md fails closed by
# printing a reason to stderr and returning 2: a skill added to the tree but not
# to the manifest would otherwise be left silently uninstalled.

aisoft_skills_manifest_load() {
  local root="$1" wanted="$2" manifest name targets extra target seen candidate declared
  local -a target_list=()
  local -a all_names=()
  manifest="$root/skills/skills.manifest"
  AISOFT_SKILL_NAMES=()
  case "$wanted" in
    claude | codex) ;;
    *)
      printf 'unknown skill target: %s\n' "$wanted" >&2
      return 2
      ;;
  esac
  if [[ ! -f "$manifest" ]]; then
    printf 'missing skill manifest: %s\n' "$manifest" >&2
    return 2
  fi
  while read -r name targets extra || [[ -n "$name" ]]; do
    [[ -n "$name" && "$name" != \#* ]] || continue
    if [[ -n "$extra" || -z "$targets" ]]; then
      printf 'malformed manifest line: %s %s %s\n' "$name" "$targets" "$extra" >&2
      return 2
    fi
    if [[ ! "$name" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
      printf 'invalid skill name: %s\n' "$name" >&2
      return 2
    fi
    for seen in ${all_names[@]+"${all_names[@]}"}; do
      if [[ "$seen" == "$name" ]]; then
        printf 'duplicate skill in manifest: %s\n' "$name" >&2
        return 2
      fi
    done
    if [[ ! -f "$root/skills/$name/SKILL.md" ]]; then
      printf 'missing source: %s\n' "$root/skills/$name/SKILL.md" >&2
      return 2
    fi
    all_names+=("$name")
    declared=0
    IFS=, read -r -a target_list <<<"$targets"
    for target in "${target_list[@]}"; do
      case "$target" in
        claude | codex) ;;
        *)
          printf 'invalid target for %s: %s\n' "$name" "${target:-<empty>}" >&2
          return 2
          ;;
      esac
      [[ "$target" != "$wanted" ]] || declared=1
    done
    [[ "$declared" == 0 ]] || AISOFT_SKILL_NAMES+=("$name")
  done <"$manifest"

  if [[ "${#all_names[@]}" == 0 ]]; then
    printf 'no skills declared in %s\n' "$manifest" >&2
    return 2
  fi
  while IFS= read -r -d '' candidate; do
    candidate="$(basename -- "$(dirname -- "$candidate")")"
    declared=0
    for seen in "${all_names[@]}"; do
      [[ "$seen" != "$candidate" ]] || declared=1
    done
    if [[ "$declared" == 0 ]]; then
      printf 'undeclared skill source: %s (add it to %s)\n' "$candidate" "$manifest" >&2
      return 2
    fi
  done < <(find "$root/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print0)
  return 0
}
