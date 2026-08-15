#!/usr/bin/env bash
set -euo pipefail

# Structural contract for the schema_version 2 canonical label manifest (#108).
# Every case runs against a temporary copy; the real manifest is never mutated.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/codex/config/gitea-labels.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# shellcheck disable=SC1090,SC1091
source "$ROOT/codex/agent/gitea-label-manifest.sh"

fail() {
  printf 'label manifest contract: %s\n' "$1" >&2
  exit 1
}

# expect_invalid <case name> <jq program>
# Applies the mutation to the real manifest and asserts the validator fails
# closed with return code 3.
expect_invalid() {
  local name="$1" program="$2" candidate="$TMP/candidate.json" rc=0
  jq "$program" "$MANIFEST" >"$candidate"
  aisoft_label_manifest_validate "$candidate" 2>"$TMP/stderr" || rc=$?
  [[ "$rc" == 3 ]] ||
    fail "$name should fail closed with rc=3, got rc=$rc"
  grep -Fq 'label manifest is invalid' "$TMP/stderr" ||
    fail "$name did not explain the violation on stderr"
}

# The shipped manifest is valid and its accessors agree with it.
aisoft_label_manifest_validate "$MANIFEST" ||
  fail 'the shipped manifest must validate'

canonical_count="$(aisoft_label_manifest_canonical "$MANIFEST" | wc -l | tr -d ' ')"
[[ "$canonical_count" == 27 ]] ||
  fail "expected 27 canonical labels, got $canonical_count"

prefixes="$(aisoft_label_manifest_prefixes "$MANIFEST" | LC_ALL=C sort | paste -sd, -)"
[[ "$prefixes" == 'area/,priority/' ]] ||
  fail "unexpected declared extension prefixes: $prefixes"

retired="$(aisoft_label_manifest_retired "$MANIFEST" | LC_ALL=C sort | paste -sd, -)"
[[ "$retired" == 'complexity/standard' ]] ||
  fail "unexpected retired labels: $retired"

# Managed namespaces are a closed set owned by the platform.
for managed in type/security complexity/small triage/wontfix; do
  aisoft_label_is_managed_namespace "$managed" ||
    fail "$managed must be recognised as a managed namespace"
done
for extension in area/web priority/high approved deployed; do
  if aisoft_label_is_managed_namespace "$extension"; then
    fail "$extension must not be treated as a managed namespace"
  fi
done

# schema_version 1 bare arrays are rejected, not auto-upgraded: a half-migrated
# manifest would let labels-readback produce a confidently wrong answer.
legacy_rc=0
jq '.canonical' "$MANIFEST" >"$TMP/legacy.json"
aisoft_label_manifest_validate "$TMP/legacy.json" 2>"$TMP/legacy.stderr" ||
  legacy_rc=$?
[[ "$legacy_rc" == 3 ]] ||
  fail "bare-array manifest should fail closed with rc=3, got rc=$legacy_rc"
grep -Fq 'schema_version 1' "$TMP/legacy.stderr" ||
  fail 'bare-array rejection must name the legacy schema explicitly'

missing_rc=0
aisoft_label_manifest_validate "$TMP/does-not-exist.json" 2>/dev/null ||
  missing_rc=$?
[[ "$missing_rc" == 3 ]] ||
  fail "missing manifest should fail closed with rc=3, got rc=$missing_rc"

expect_invalid 'wrong schema_version' '.schema_version = 3'
expect_invalid 'empty canonical' '.canonical = []'
expect_invalid 'missing project_extensions' 'del(.project_extensions)'
expect_invalid 'missing retired' 'del(.retired)'
expect_invalid 'duplicate canonical name' '.canonical += [.canonical[0]]'
expect_invalid 'empty description' '.canonical[0].description = ""'
expect_invalid 'non-hex color' '.canonical[0].color = "xyzxyz"'
expect_invalid 'short color' '.canonical[0].color = "abc"'
expect_invalid 'prefix without trailing slash' \
  '.project_extensions.allowed_prefixes += [{"prefix":"team","description":"x"}]'
expect_invalid 'retired label also canonical' \
  '.retired += [{"name":"approved"}]'

# A declared extension prefix must never reopen a managed namespace: neither by
# matching it exactly nor by nesting inside it.
expect_invalid 'prefix equals managed namespace' \
  '.project_extensions.allowed_prefixes += [{"prefix":"type/","description":"x"}]'
expect_invalid 'prefix inside managed namespace' \
  '.project_extensions.allowed_prefixes += [{"prefix":"type/sub/","description":"x"}]'

# The third direction — a declared prefix that would swallow a managed namespace
# — is unreachable with today's single-segment managed prefixes, because the
# only string ending in "/" that prefixes "type/" is "type/" itself. Cover the
# branch against a hypothetical multi-segment managed namespace so the guard
# cannot silently rot if one is ever introduced.
(
  # Consumed by the sourced validator, not by this file.
  # shellcheck disable=SC2034
  AISOFT_LABEL_MANAGED_PREFIXES=('type/core/')
  swallow_rc=0
  jq '.project_extensions.allowed_prefixes += [{"prefix":"type/","description":"x"}]' \
    "$MANIFEST" >"$TMP/swallow.json"
  aisoft_label_manifest_validate "$TMP/swallow.json" 2>"$TMP/swallow.stderr" ||
    swallow_rc=$?
  [[ "$swallow_rc" == 3 ]] ||
    fail "prefix swallowing a managed namespace should fail closed, got rc=$swallow_rc"
  grep -Fq 'overlaps managed namespace type/core/' "$TMP/swallow.stderr" ||
    fail 'swallow rejection must name the managed namespace it protects'
)

echo 'gitea-label-manifest contract passed.'
