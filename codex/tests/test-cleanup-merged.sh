#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(cd -- "$(mktemp -d)" && pwd -P)"
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

# #397: no network, remote inferred, detached and leftover worktrees, remote list.
git -C "$TMP/repo" push gitea main:refs/heads/change/5-done >/dev/null
git -C "$TMP/repo" fetch gitea >/dev/null 2>&1
git -C "$TMP/repo" worktree add --detach "$TMP/detached" main >/dev/null 2>&1
git -C "$TMP/repo" worktree add -b change/6-gone "$TMP/gone" main >/dev/null 2>&1
rm "$TMP/gone/.git"
mv "$TMP/remote.git" "$TMP/remote-offline.git" # any fetch would now fail
sleep 1 # --min-age 0 still needs every file to be older than "now"
out="$(bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" --remote-branches --min-age 0)"
grep -Fq 'base: gitea/main (cached' <<<"$out"
grep -Fq "removable: $TMP/detached [detached]" <<<"$out"
grep -Fq "orphan: $TMP/gone (leftover files not removed)" <<<"$out"
grep -Fq 'merged remote-tracking branch (may be stale; deletion is a human step): gitea/change/5-done' <<<"$out"
bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" --branches --apply --min-age 0 >/dev/null
[[ ! -d "$TMP/detached" ]]
if git -C "$TMP/repo" worktree list --porcelain | grep -Fq "$TMP/gone"; then
  echo "leftover worktree metadata was not pruned" >&2
  exit 1
fi
git -C "$TMP/repo" show-ref --verify --quiet refs/heads/change/6-gone && {
  echo "merged branch of a pruned worktree survived" >&2
  exit 1
}
git -C "$TMP/repo" remote add github https://github.com/example/mirror.git
git -C "$TMP/repo" update-ref refs/remotes/github/main HEAD
bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" >/dev/null
git -C "$TMP/repo" remote add second "$TMP/elsewhere.git"
git -C "$TMP/repo" update-ref refs/remotes/second/main HEAD
if bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" 2>/dev/null; then
  echo "ambiguous platform remote was not refused" >&2
  exit 1
fi
bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" --remote second >/dev/null

if rg -n -- '--force|branch -D|git clean|git fetch' \
  "$ROOT/codex/tools/aigitea-cleanup-merged.sh"; then
  echo "destructive cleanup command found" >&2
  exit 1
fi
echo "cleanup tests passed"
