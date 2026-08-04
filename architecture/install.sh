#!/usr/bin/env bash
# Install the offline architecture validator and versioned data only.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${AISOFT_ARCH_PREFIX:-}"

usage() {
  echo "usage: $0 --prefix ABSOLUTE_PATH" >&2
}

while (($#)); do
  case "$1" in
    --prefix)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      PREFIX="$2"
      shift 2
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[[ -n "$PREFIX" && "$PREFIX" == /* ]] || { usage; exit 2; }

RUNTIME_DIR="$PREFIX/lib/aisoft-architecture/aisoft_architecture"
SHARE_DIR="$PREFIX/share/aisoft-architecture"
install -d -m 755 "$PREFIX/bin" "$RUNTIME_DIR" "$SHARE_DIR"

for source_file in "$ROOT"/codex/runtime/aisoft_architecture/*.py; do
  install -m 644 "$source_file" "$RUNTIME_DIR/$(basename "$source_file")"
done
install -m 755 "$ROOT/architecture/bin/aisoft-architecture" "$PREFIX/bin/aisoft-architecture"
install -m 644 "$ROOT/architecture/catalog.json" "$SHARE_DIR/catalog.json"

for directory in profiles schemas templates decisions; do
  install -d -m 755 "$SHARE_DIR/$directory"
  for source_file in "$ROOT/architecture/$directory"/*; do
    [[ -f "$source_file" ]] || continue
    install -m 644 "$source_file" "$SHARE_DIR/$directory/$(basename "$source_file")"
  done
done

echo "Architecture validator installed in $PREFIX"
echo "No project declaration, lock, credential, service, timer, database, image, server, or deployment was modified."
