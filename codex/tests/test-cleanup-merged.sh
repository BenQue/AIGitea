#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git init --bare "$TMP/remote.git" >/dev/null
git init -b main "$TMP/repo" >/dev/null
git -C "$TMP/repo" config user.name test
git -C "$TMP/repo" config user.email test@example.invalid
printf 'base\n' >"$TMP/repo/file.txt"
git -C "$TMP/repo" add file.txt
git -C "$TMP/repo" commit -m base >/dev/null
git -C "$TMP/repo" remote add gitea "$TMP/remote.git"
git -C "$TMP/repo" push -u gitea main >/dev/null
git -C "$TMP/repo" branch merged-local

dry="$(bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" --branches)"
grep -Fq 'mode: DRY-RUN' <<<"$dry"
git -C "$TMP/repo" show-ref --verify --quiet refs/heads/merged-local

bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" \
  "$TMP/repo" --branches --apply >/dev/null
if git -C "$TMP/repo" show-ref --verify --quiet refs/heads/merged-local; then
  echo "merged branch was not deleted after empty REMOVE array" >&2
  exit 1
fi

if rg -n -- '--force|branch -D|git clean' \
  "$ROOT/codex/tools/aigitea-cleanup-merged.sh"; then
  echo "destructive cleanup command found" >&2
  exit 1
fi
echo "cleanup tests passed"
