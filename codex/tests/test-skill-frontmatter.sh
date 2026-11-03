#!/usr/bin/env bash
# #438: every platform skill's frontmatter must be strict YAML. Each case runs
# against a fabricated skills/ tree in a temporary directory, once per YAML
# backend this host has (PyYAML and/or Ruby Psych); the real repository is
# only read for the regression case built from the pre-#438 bytes.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

checker="$root/codex/tools/check-skill-frontmatter.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

backends=()
if python3 -I -B -c 'import yaml' 2>/dev/null; then
  backends+=(python)
fi
if command -v ruby >/dev/null 2>&1 && ruby -Eutf-8 -ryaml -rjson -e '' 2>/dev/null; then
  backends+=(ruby)
fi

# A forced backend this host lacks is a usage error, never a silent fallback.
for missing in python ruby; do
  case " ${backends[*]-} " in
    *" $missing "*) ;;
    *)
      set +e
      AISOFT_YAML_BACKEND="$missing" bash "$checker" --root "$root" >"$tmp/out" 2>&1
      rc=$?
      set -e
      [[ "$rc" == 2 ]] || fail "missing backend $missing exits $rc, want 2"
      grep -Fq "$missing" "$tmp/out" || fail "missing backend $missing is not named"
      ;;
  esac
done
set +e
AISOFT_YAML_BACKEND=perl bash "$checker" --root "$root" >"$tmp/out" 2>&1
rc=$?
set -e
[[ "$rc" == 2 ]] || fail "unknown backend exits $rc, want 2"

if [[ "${#backends[@]}" == 0 ]]; then
  # The checker must refuse rather than pass; nothing else can be shown here.
  set +e
  bash "$checker" --root "$root" >"$tmp/out" 2>&1
  rc=$?
  set -e
  [[ "$rc" == 2 ]] || fail "no YAML backend exits $rc, want 2"
  echo 'test-skill-frontmatter: no YAML backend on this host; only the refusal was checked' >&2
  exit 1
fi

# tree <name>: a minimal valid skills/ tree with two declared skills.
tree() {
  local dir="$tmp/$1"
  mkdir -p "$dir/skills/alpha/agents" "$dir/skills/beta"
  cat >"$dir/skills/skills.manifest" <<'EOF'
# comment lines and blank lines are ignored

alpha claude,codex
beta codex
EOF
  cat >"$dir/skills/alpha/SKILL.md" <<'EOF'
---
name: alpha
description: Alpha skill — handles analysis, routing and plans. 触发词：甲、乙。
---

# Alpha

Body text: a colon here is fine, it is not frontmatter.
EOF
  cat >"$dir/skills/alpha/agents/openai.yaml" <<'EOF'
interface:
  display_name: "Alpha"
EOF
  cat >"$dir/skills/beta/SKILL.md" <<'EOF'
---
name: beta
description: >-
  Beta skill: a folded block scalar may carry ": " safely.
---
EOF
  printf '%s\n' "$dir"
}

# expect <backend> <dir> <rc> [phrase]
expect() {
  local backend="$1" dir="$2" want="$3" phrase="${4:-}" rc
  set +e
  AISOFT_YAML_BACKEND="$backend" bash "$checker" --root "$dir" >"$tmp/out" 2>&1
  rc=$?
  set -e
  if [[ "$rc" != "$want" ]]; then
    cat "$tmp/out" >&2
    fail "$backend $(basename "$dir"): exit $rc, want $want"
  fi
  if [[ -n "$phrase" ]] && ! grep -Fq -- "$phrase" "$tmp/out"; then
    cat "$tmp/out" >&2
    fail "$backend $(basename "$dir"): output lacks '$phrase'"
  fi
}

for backend in "${backends[@]}"; do
  ok="$(tree "ok-$backend")"
  expect "$backend" "$ok" 0 'RESULT PASS'

  bad="$(tree "colon-$backend")"
  sed -i.bak 's/^description: Alpha skill — handles/description: Alpha skill: handles analysis: routing/' \
    "$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'skills/alpha/SKILL.md'

  bad="$(tree "name-$backend")"
  sed -i.bak 's/^name: alpha$/name: gamma/' "$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'name'

  bad="$(tree "nodesc-$backend")"
  sed -i.bak '/^description:/d' "$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'description'

  bad="$(tree "emptydesc-$backend")"
  sed -i.bak "s/^description: .*/description: ''/" "$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'description'

  bad="$(tree "unclosed-$backend")"
  printf -- '---\nname: alpha\ndescription: no closing fence\n\n# Alpha\n' >"$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'skills/alpha/SKILL.md'

  bad="$(tree "nofence-$backend")"
  printf -- '# Alpha\n\nname: alpha\n' >"$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'skills/alpha/SKILL.md'

  bad="$(tree "list-$backend")"
  printf -- '---\n- name\n- alpha\n---\n' >"$bad/skills/alpha/SKILL.md"
  expect "$backend" "$bad" 1 'mapping'

  bad="$(tree "missing-$backend")"
  rm "$bad/skills/beta/SKILL.md"
  expect "$backend" "$bad" 1 'skills/beta/SKILL.md'

  bad="$(tree "undeclared-$backend")"
  mkdir -p "$bad/skills/delta"
  printf -- '---\nname: delta\ndescription: undeclared: still parsed\n---\n' >"$bad/skills/delta/SKILL.md"
  expect "$backend" "$bad" 1 'skills/delta/SKILL.md'

  bad="$(tree "agents-$backend")"
  printf 'interface:\n  display_name: "Alpha\n' >"$bad/skills/alpha/agents/openai.yaml"
  expect "$backend" "$bad" 1 'skills/alpha/agents/openai.yaml'

  bad="$(tree "agentslist-$backend")"
  printf -- '- one\n- two\n' >"$bad/skills/alpha/agents/openai.yaml"
  expect "$backend" "$bad" 1 'skills/alpha/agents/openai.yaml'

  bad="$(tree "nomanifest-$backend")"
  rm "$bad/skills/skills.manifest"
  expect "$backend" "$bad" 1 'skills.manifest'

  # Regression: the aisoft-platform frontmatter as it was before #438.
  bad="$(tree "pre438-$backend")"
  mkdir -p "$bad/skills/aisoft-platform"
  printf 'aisoft-platform claude,codex\n' >>"$bad/skills/skills.manifest"
  {
    printf -- '---\nname: aisoft-platform\n'
    printf 'description: Also use to operate or onboard projects on the AISoft self-hosted Gitea delivery platform: Issue analysis, small-or-complex routing.\n'
    printf -- '---\n'
  } >"$bad/skills/aisoft-platform/SKILL.md"
  expect "$backend" "$bad" 1 'skills/aisoft-platform/SKILL.md'
done

# The checker never writes into the tree it reads.
before="$(find "$tmp/ok-${backends[0]}" -type f | LC_ALL=C sort | xargs cksum | cksum)"
AISOFT_YAML_BACKEND="${backends[0]}" bash "$checker" --root "$tmp/ok-${backends[0]}" >/dev/null
after="$(find "$tmp/ok-${backends[0]}" -type f | LC_ALL=C sort | xargs cksum | cksum)"
[[ "$before" == "$after" ]] || fail 'checker modified the tree it read'

echo "test-skill-frontmatter: PASS (backends: ${backends[*]})"
