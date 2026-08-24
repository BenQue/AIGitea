#!/usr/bin/env bash
# Source provenance output and staleness gate shared by every installer (#162, #171).
#
# Sourced, never executed: this file only defines functions and performs no
# action of its own.
#
# Every installer in this repository takes its sources from $ROOT, the checkout
# it is being run from, and compares checkout-against-installed. That comparison
# is correct, but it answers a different question than the operator is asking,
# which is whether the *merged* contract got installed. The two answers coincide
# until the checkout falls behind, and then they diverge invisibly: on
# 2026-08-23 both the Mac and the gitea-ci VM printed 'installed ... candidate'
# while writing the pre-#161 29-operation manifest, because the checkout's main
# was three commits behind origin/main and the VM mounts that same checkout
# through /mnt/mac. Idempotence is a false positive here -- 'already current'
# proves installed == checkout, not installed == merged. So print what is about
# to be installed, and refuse outright when the source is known to be behind.
#
# #162 fixed install-host-access-broker.sh alone and left the others to a
# follow-up. #171 is that follow-up, and it extracts rather than copies: five
# near-identical copies of this logic would drift, which is the next defect
# rather than a fix for this one. Only two things vary between installers -- the
# name that appears in the WARNING/ERROR prefix, and the readable quantity that
# says *which version* is being installed (operations, capabilities, skills,
# catalog revision, ...). Both are parameters.
#
# The gate reads the remote-tracking ref already on disk and never fetches: some
# of these scripts run under sudo, and remote access on this platform goes
# through the broker's typed git.fetch.* operations rather than through root.
# That bounds what it can prove -- a checkout that never fetched has a stale
# @{upstream} too -- which is why the commit is printed rather than merely
# checked. Anything the gate cannot determine (no upstream, detached HEAD,
# unresolvable ref, not a git checkout) degrades to a warning: a gate that could
# not tell 'behind' from 'unknowable' would refuse tarball and CI installs as
# well.
set -euo pipefail

# All values start at column 20. Padding the label to 11 reproduces #162's
# hand-aligned output byte for byte ('checkout:' + 3 spaces, 'commit:' + 5,
# 'operations:' + 1); longer labels simply fall back to a single space.
aisoft_install_source_line() {
  printf 'source %-11s %s\n' "$1:" "$2"
}

# Readable-quantity helpers. Each degrades to 'unknown' rather than failing:
# provenance that could abort an install would be a worse gate than no
# provenance at all. python3 only -- no installer may gain a jq dependency it
# does not already have.
aisoft_install_source_json_count() {
  local value
  value="$(
    python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))[sys.argv[2]]))' \
      "$1" "$2" 2>/dev/null || true
  )"
  printf '%s' "${value:-unknown}"
}

aisoft_install_source_json_value() {
  local value
  value="$(
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
      "$1" "$2" 2>/dev/null || true
  )"
  printf '%s' "${value:-unknown}"
}

# Counts the regular files among its arguments, so callers can pass an unmatched
# glob without inflating the count by one literal.
aisoft_install_source_file_count() {
  local count=0 candidate
  for candidate in "$@"; do
    if [ -f "$candidate" ]; then
      count=$((count + 1))
    fi
  done
  printf '%s' "$count"
}

# aisoft_install_source_guard <installer-name> <source-root> [<label> <value>]...
#
# Prints provenance on every path -- including the idempotent no-op, which is
# exactly the output misread in #162 -- then either returns, warns, or exits
# non-zero without having written anything. Call it before the first filesystem
# write; `install -d` counts as a write.
aisoft_install_source_guard() {
  local installer="$1" root="$2"
  shift 2

  if [ "$(($# % 2))" -ne 0 ]; then
    printf 'ERROR: %s: source guard takes label/value pairs\n' "$installer" >&2
    exit 1
  fi

  local source_commit='unknown'
  local sync_state='not a git checkout; staleness unchecked'
  local sync_unknown=1
  local branch='' upstream='' behind='' ahead=''

  if command -v git >/dev/null 2>&1 && git -C "$root" rev-parse --git-dir >/dev/null 2>&1; then
    source_commit="$(git -C "$root" rev-parse --short HEAD 2>/dev/null || printf 'unknown')"
    branch="$(git -C "$root" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    if [ -n "$branch" ]; then
      upstream="$(
        git -C "$root" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true
      )"
    fi

    if [ -z "$branch" ]; then
      sync_state='detached HEAD; staleness unchecked'
    elif [ -z "$upstream" ]; then
      sync_state="branch $branch has no upstream; staleness unchecked"
    elif ! git -C "$root" rev-parse --verify --quiet "$upstream^{commit}" >/dev/null 2>&1; then
      sync_state="$upstream is not present locally; staleness unchecked"
    else
      behind="$(git -C "$root" rev-list --count "HEAD..$upstream" 2>/dev/null || true)"
      ahead="$(git -C "$root" rev-list --count "$upstream..HEAD" 2>/dev/null || true)"
      if [ -z "$behind" ] || [ -z "$ahead" ]; then
        behind=''
        sync_state="cannot compare $branch with $upstream; staleness unchecked"
      else
        sync_unknown=0
        if [ "$behind" -gt 0 ]; then
          sync_state="$behind commit(s) BEHIND $upstream"
        elif [ "$ahead" -gt 0 ]; then
          sync_state="$ahead commit(s) ahead of $upstream"
        else
          sync_state="level with $upstream"
        fi
      fi
    fi
  fi

  aisoft_install_source_line checkout "$root"
  aisoft_install_source_line commit "$source_commit ($sync_state)"
  while [ "$#" -ge 2 ]; do
    aisoft_install_source_line "$1" "$2"
    shift 2
  done

  if [ "$sync_unknown" = 1 ]; then
    printf 'WARNING: %s: %s; the printed commit is the only evidence of what is being installed\n' \
      "$installer" "$sync_state" >&2
    return 0
  fi

  if [ -n "$behind" ] && [ "$behind" -gt 0 ]; then
    printf 'ERROR: %s: source checkout is %s commit(s) behind %s\n' \
      "$installer" "$behind" "$upstream" >&2
    printf '%s\n' \
      "  Installing now would install this checkout's older contract and report success:" \
      "  the success output does not distinguish it from a correct install (#162)." \
      "  Fast-forward first, then re-run:" \
      "    git -C $root merge --ff-only $upstream" \
      "  On a change branch, rebase onto the upstream instead:" \
      "    git -C $root rebase $upstream" >&2
    exit 1
  fi
}
