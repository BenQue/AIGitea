#!/usr/bin/env bash
# Safe local cleanup for merged worktrees. Default is dry-run.
set -euo pipefail

REPO=""
REMOTE="gitea"
APPLY=""
DO_BRANCHES=""
AGE=60
while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --branches) DO_BRANCHES=1; shift ;;
    --min-age) AGE="${2:?--min-age requires minutes}"; shift 2 ;;
    --remote) REMOTE="${2:?--remote requires a value}"; shift 2 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
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
git rev-parse --verify -q "$REMOTE/main" >/dev/null ||
  { echo "missing $REMOTE/main" >&2; exit 2; }

printf 'repository: %s\nbase: %s/main\n' "$ROOT" "$REMOTE"
[ -n "$APPLY" ] && echo "mode: APPLY" || echo "mode: DRY-RUN"
git fetch --prune "$REMOTE" >/dev/null 2>&1 || true

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
  dirty="$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$dirty" != "0" ]; then SKIP_DIRTY+=("$wt|$bn|$dirty"); continue; fi
  if [ -n "$bn" ] && git merge-base --is-ancestor "$bn" "$REMOTE/main" 2>/dev/null; then
    if [ -n "$(find "$wt" -maxdepth 2 -newermt "-$AGE minutes" -print -quit 2>/dev/null)" ]; then
      SKIP_ACTIVE+=("$wt|$bn")
      continue
    fi
    REMOVE+=("$wt|$bn")
  else
    ahead="$(git rev-list --count "$REMOTE/main..$bn" 2>/dev/null || echo "?")"
    SKIP_UNMERGED+=("$wt|$bn|$ahead")
  fi
done < <(git worktree list --porcelain |
  awk '/^worktree /{w=$2} /^branch /{print w"\t"$2}')

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
