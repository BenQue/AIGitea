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
# #397: the platform remote is proved by the governance manifest's base URL and
# owner (a synthetic one here); pushes keep going to the local bare repo.
printf '{"base_url":"http://gitea.example/","owner":"admin"}\n' >"$TMP/governance.json"
export AISOFT_GOVERNANCE_MANIFEST="$TMP/governance.json"
jq -n --arg checkout "$TMP/repo" \
  '{projects: [{repository: "repo", mac_checkout: $checkout}, {repository: "other", mac_checkout: "/elsewhere"}]}' \
  >"$TMP/access.json"
export AISOFT_HOST_ACCESS_MANIFEST="$TMP/access.json"
git -C "$TMP/repo" config remote.gitea.pushurl "$TMP/remote.git"
git -C "$TMP/repo" config remote.gitea.url http://gitea.example/admin/repo.git
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
git -C "$TMP/repo" update-ref refs/remotes/gitea/change/5-done main
git -C "$TMP/repo" worktree add --detach "$TMP/detached" main >/dev/null 2>&1
# A worktree nested inside the checkout that lost its .git must not be judged
# by the enclosing checkout git would walk up to.
git -C "$TMP/repo" worktree add --detach "$TMP/repo/.nested/wt" main >/dev/null 2>&1
rm "$TMP/repo/.nested/wt/.git"
git -C "$TMP/repo" worktree add -b change/6-gone "$TMP/gone" main >/dev/null 2>&1
rm "$TMP/gone/.git"
mv "$TMP/remote.git" "$TMP/remote-offline.git" # any fetch would now fail
sleep 1 # --min-age 0 still needs every file to be older than "now"
out="$(bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" --remote-branches --min-age 0)"
grep -Fq 'base: gitea/main (cached' <<<"$out"
grep -Fq "removable: $TMP/detached [detached]" <<<"$out"
grep -Fq "orphan: $TMP/gone (leftover files not removed)" <<<"$out"
grep -Fq "orphan: $TMP/repo/.nested/wt (leftover files not removed)" <<<"$out"
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
if git -C "$TMP/repo" worktree list --porcelain | grep -Fq "$TMP/repo/.nested/wt"; then
  echo "nested leftover worktree metadata was not pruned" >&2
  exit 1
fi
# Remotes outside the manifest's Gitea owner never count, however unique.
for other in github=https://github.com/example/mirror.git fork=http://other.example/admin/repo.git \
  sibling=http://gitea.example/someone/repo.git backup=http://gitea.example/admin/repo-backup.git \
  peer=http://gitea.example/admin/other.git; do
  git -C "$TMP/repo" remote add "${other%%=*}" "${other#*=}"
  git -C "$TMP/repo" update-ref "refs/remotes/${other%%=*}/main" HEAD
done
out="$(bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo")"
grep -Fq 'base: gitea/main' <<<"$out"
# Without the exact repository, a same-owner sibling must not stand in for it.
git -C "$TMP/repo" remote remove gitea
if bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" 2>/dev/null; then
  echo "a remote other than the exact repository was accepted" >&2
  exit 1
fi
# An unmapped checkout cannot prove anything either.
git -C "$TMP/repo" remote add exact http://gitea.example/admin/repo.git
git -C "$TMP/repo" update-ref refs/remotes/exact/main HEAD
if AISOFT_HOST_ACCESS_MANIFEST="$TMP/governance.json" \
  bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo" 2>/dev/null; then
  echo "an unmapped checkout inferred a remote" >&2
  exit 1
fi
out="$(bash "$ROOT/codex/tools/aigitea-cleanup-merged.sh" "$TMP/repo")"
grep -Fq 'base: exact/main' <<<"$out"
git -C "$TMP/repo" remote add second http://gitea.example/admin/repo.git
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
