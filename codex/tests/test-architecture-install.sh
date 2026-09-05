#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEST_ROOT"' EXIT
PREFIX="$TEST_ROOT/prefix"

bash "$ROOT/architecture/install.sh" --prefix "$PREFIX" >/dev/null
FIRST_MANIFEST="$TEST_ROOT/first"
find "$PREFIX" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$FIRST_MANIFEST"

bash "$ROOT/architecture/install.sh" --prefix "$PREFIX" >/dev/null
SECOND_MANIFEST="$TEST_ROOT/second"
find "$PREFIX" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$SECOND_MANIFEST"
cmp "$FIRST_MANIFEST" "$SECOND_MANIFEST"

"$PREFIX/bin/aisoft-architecture" validate \
  --catalog "$PREFIX/share/aisoft-architecture/catalog.json" \
  --profiles-dir "$PREFIX/share/aisoft-architecture/profiles" \
  --schema-dir "$PREFIX/share/aisoft-architecture/schemas" \
  --project "$PREFIX/share/aisoft-architecture/templates/project-architecture.example.json" \
  --today 2026-09-05 >/dev/null

[[ ! -e "$PREFIX/.aisoft" ]]
[[ ! -e "$PREFIX/architecture.lock.json" ]]
echo "architecture installer idempotence: PASS"
