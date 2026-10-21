#!/usr/bin/env bash
# Safe local cleanup for merged worktrees. Default is dry-run.
#
# Usage: aigitea-cleanup-merged.sh [REPO] [--branches] [--remote-branches]
#          [--apply] [--min-age MINUTES] [--remote NAME]
#
# Never touches the network (#397): it compares against the cached
# <remote>/main, so fetch main through the host-access broker first
# (git.fetch.main). Without --remote it uses the single remote whose URL is
# exactly this checkout's repository per the manifests (the access manifest's
# mac_checkout entry under the governance base URL and owner), and stops if
# that cannot be proved for exactly one remote. Worktrees on a branch or on a detached HEAD are removable only
# when merged, clean and not modified within --min-age minutes.
# --remote-branches lists merged remote-tracking change/* refs; it deletes
# nothing, the refs may be stale, and deleting a remote branch is a human step.
set -euo pipefail

REPO=""
REMOTE=""
APPLY=""
DO_BRANCHES=""
DO_REMOTE_BRANCHES=""
AGE=60
while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --branches) DO_BRANCHES=1; shift ;;
    --remote-branches) DO_REMOTE_BRANCHES=1; shift ;;
    --min-age) AGE="${2:?--min-age requires minutes}"; shift 2 ;;
    --remote) REMOTE="${2:?--remote requires a value}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) [ -z "$REPO" ] || { echo "unexpected argument: $1" >&2; exit 2; }
       REPO="$1"; shift ;;
  esac
done
REPO="${REPO:-$PWD}"

cd "$REPO"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
  { echo "not a git repository: $REPO" >&2; exit 2; }
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [ -z "$REMOTE" ]; then
  # The exact repository comes from the access manifest entry whose Mac
  # checkout is this one; any other repository, even under the same owner, is
  # not proof.
  config_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../config" && pwd)"
  governance="${AISOFT_GOVERNANCE_MANIFEST:-$config_dir/gitea-governance.json}"
  access="${AISOFT_HOST_ACCESS_MANIFEST:-$config_dir/host-access-broker.json}"
  common="$(git rev-parse --git-common-dir)"
  checkout="$(cd -- "$common/.." && pwd -P)"
  expected="$(jq -er --arg checkout "$checkout" --slurpfile g "$governance" '
    [.projects[] | select(.mac_checkout == $checkout) | .repository] as $repos
    | if ($repos | length) == 1
      then "\($g[0].base_url | rtrimstr("/"))/\($g[0].owner)/\($repos[0])" else error("unmapped") end' \
    "$access" 2>/dev/null)" ||
    { echo "cannot prove the platform remote from the manifests; pass --remote NAME" >&2; exit 2; }
  CANDIDATES=()
  while IFS= read -r name; do
    git rev-parse --verify -q "refs/remotes/$name/main" >/dev/null || continue
    url="$(git remote get-url "$name" 2>/dev/null || true)"
    [ "$url" = "$expected" ] || [ "$url" = "$expected.git" ] || continue
    CANDIDATES+=("$name")
  done < <(git remote)
  [ "${#CANDIDATES[@]}" -eq 1 ] ||
    { echo "cannot infer the platform remote; pass --remote NAME" >&2; exit 2; }
  REMOTE="${CANDIDATES[0]}"
fi
git rev-parse --verify -q "$REMOTE/main" >/dev/null ||
  { echo "missing $REMOTE/main" >&2; exit 2; }

printf 'repository: %s\nbase: %s/main (cached; fetch main through the broker first)\n' "$ROOT" "$REMOTE"
[ -n "$APPLY" ] && echo "mode: APPLY" || echo "mode: DRY-RUN"

MAIN_WT="$(git rev-parse --show-toplevel)"
REMOVE=()
SKIP_DIRTY=()
SKIP_UNMERGED=()
SKIP_ACTIVE=()
ORPHAN=()
while IFS=$'\t' read -r wt br; do
  [ "$wt" = "$MAIN_WT" ] && continue
  bn="${br#refs/heads/}"
  if [ ! -d "$wt" ]; then ORPHAN+=("$wt"); continue; fi
  # A directory whose .git link is gone is prunable too; prune drops only the
  # metadata, and whatever files remain there are left to a human.
  # Inside another checkout git would walk up to it, so the worktree must
  # resolve to itself.
  top="$(git -C "$wt" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ ! -e "$wt/.git" ] || [ -z "$top" ] ||
    [ "$(cd -- "$top" && pwd -P)" != "$(cd -- "$wt" && pwd -P)" ]; then
    ORPHAN+=("$wt (leftover files not removed)")
    continue
  fi
  dirty="$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$dirty" != "0" ]; then SKIP_DIRTY+=("$wt|${bn:-detached}|$dirty"); continue; fi
  # A detached worktree is judged by its HEAD commit.
  ref="${bn:-$(git -C "$wt" rev-parse --verify -q HEAD || true)}"
  bn="${bn:-detached}"
  if [ -n "$ref" ] && git merge-base --is-ancestor "$ref" "$REMOTE/main" 2>/dev/null; then
    if [ -n "$(find "$wt" -maxdepth 2 -newermt "-$AGE minutes" -print -quit 2>/dev/null)" ]; then
      SKIP_ACTIVE+=("$wt|$bn")
      continue
    fi
    REMOVE+=("$wt|$bn")
  else
    ahead="$(git rev-list --count "$REMOTE/main..$ref" 2>/dev/null || echo "?")"
    SKIP_UNMERGED+=("$wt|$bn|$ahead")
  fi
done < <(git worktree list --porcelain |
  awk '/^worktree /{w=substr($0, 10); b=""} /^branch /{b=$2} /^$/{if (w != "") print w"\t"b; w=""}
       END{if (w != "") print w"\t"b}')

if [ "${#SKIP_DIRTY[@]}" -gt 0 ]; then
  for e in "${SKIP_DIRTY[@]}"; do
    IFS='|' read -r w b d <<<"$e"
    printf 'skip dirty: %s [%s] changes=%s\n' "$w" "$b" "$d"
  done
fi
if [ "${#SKIP_UNMERGED[@]}" -gt 0 ]; then
  for e in "${SKIP_UNMERGED[@]}"; do
    IFS='|' read -r w b a <<<"$e"
    printf 'skip unmerged: %s [%s] ahead=%s\n' "$w" "$b" "$a"
  done
fi
if [ "${#SKIP_ACTIVE[@]}" -gt 0 ]; then
  for e in "${SKIP_ACTIVE[@]}"; do
    IFS='|' read -r w b <<<"$e"
    printf 'skip active: %s [%s]\n' "$w" "$b"
  done
fi
if [ "${#ORPHAN[@]}" -gt 0 ]; then
  for w in "${ORPHAN[@]}"; do printf 'orphan: %s\n' "$w"; done
fi
if [ "${#REMOVE[@]}" -gt 0 ]; then
  for e in "${REMOVE[@]}"; do
    IFS='|' read -r w b <<<"$e"
    printf 'removable: %s [%s]\n' "$w" "$b"
  done
fi

# macOS Bash 3.2 expands an empty array under set -u as an unbound variable.
# Guard the loop explicitly so --apply --branches continues to branch cleanup.
if [ -n "$APPLY" ] && [ "${#REMOVE[@]}" -gt 0 ]; then
  for e in "${REMOVE[@]}"; do
    IFS='|' read -r w b <<<"$e"
    git worktree remove "$w"
    printf 'removed: %s\n' "$w"
  done
fi
if [ -n "$APPLY" ] && [ "${#ORPHAN[@]}" -gt 0 ]; then
  git worktree prune -v
fi

if [ -n "$DO_REMOTE_BRANCHES" ]; then
  while IFS= read -r ref; do
    printf 'merged remote-tracking branch (may be stale; deletion is a human step): %s\n' "$ref"
  done < <(git for-each-ref --format='%(refname:short)' --merged "$REMOTE/main" "refs/remotes/$REMOTE/change/")
fi

if [ -z "$DO_BRANCHES" ]; then
  echo "branch cleanup skipped; add --branches to opt in"
  exit 0
fi

INUSE="$(git worktree list --porcelain |
  awk '/^branch /{sub("refs/heads/","",$2); print $2}')"
CAND=()
while IFS= read -r branch; do
  [ -n "$branch" ] || continue
  case "$branch" in main|master) continue ;; esac
  grep -qx "$branch" <<<"$INUSE" && continue
  CAND+=("$branch")
done < <(git branch --format='%(refname:short)' --merged "$REMOTE/main")

if [ "${#CAND[@]}" -gt 0 ]; then
  for branch in "${CAND[@]}"; do
    printf 'merged local branch: %s\n' "$branch"
    if [ -n "$APPLY" ]; then
      if git worktree list --porcelain |
        awk '/^branch /{sub("refs/heads/","",$2); print $2}' |
        grep -qx "$branch"; then
        printf 'skip newly active branch: %s\n' "$branch"
        continue
      fi
      git branch -d "$branch"
    fi
  done
fi
