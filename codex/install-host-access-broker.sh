#!/usr/bin/env bash
# Install only versioned broker candidates. Never bind credentials, profiles, services, or timers.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${AISOFT_HOST_ACCESS_INSTALL_ROOT:-/}"
LIB_ROOT="$INSTALL_ROOT/usr/local/lib/aisoft-host-access"
LIBEXEC_ROOT="$INSTALL_ROOT/usr/local/libexec/aisoft"
SHARE_ROOT="$INSTALL_ROOT/usr/local/share/aisoft"

# Source provenance and staleness gate (#162).
#
# install_versioned() below compares checkout-against-installed. That comparison
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
# The gate reads the remote-tracking ref already on disk and never fetches: this
# script runs under sudo, and remote access on this platform goes through the
# broker's typed git.fetch.* operations rather than through root. That bounds
# what it can prove -- a checkout that never fetched has a stale @{upstream} too
# -- which is why the commit is printed rather than merely checked. Anything the
# gate cannot determine (no upstream, detached HEAD, unresolvable ref, not a git
# checkout) degrades to a warning: a gate that could not tell 'behind' from
# 'unknowable' would refuse tarball and CI installs as well.

warn() {
  printf 'WARNING: install-host-access-broker: %s\n' "$1" >&2
}

source_commit='unknown'
sync_state='not a git checkout; staleness unchecked'
sync_unknown=1
behind=''
upstream=''

if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  source_commit="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || printf 'unknown')"
  branch="$(git -C "$ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  if [ -n "$branch" ]; then
    upstream="$(
      git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true
    )"
  fi

  if [ -z "$branch" ]; then
    sync_state='detached HEAD; staleness unchecked'
  elif [ -z "$upstream" ]; then
    sync_state="branch $branch has no upstream; staleness unchecked"
  elif ! git -C "$ROOT" rev-parse --verify --quiet "$upstream^{commit}" >/dev/null 2>&1; then
    sync_state="$upstream is not present locally; staleness unchecked"
  else
    behind="$(git -C "$ROOT" rev-list --count "HEAD..$upstream" 2>/dev/null || true)"
    ahead="$(git -C "$ROOT" rev-list --count "$upstream..HEAD" 2>/dev/null || true)"
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

source_operations="$(
  python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["operations"]))' \
    "$ROOT/codex/config/host-access-broker.json" 2>/dev/null || printf 'unknown'
)"
if [ -z "$source_operations" ]; then
  source_operations='unknown'
fi

# Printed on every path, including 'already current (no-op)': the no-op line is
# exactly the output the operator misread in #162, so provenance that appeared
# only when something changed would leave that path unreadable.
printf 'source checkout:   %s\n' "$ROOT"
printf 'source commit:     %s (%s)\n' "$source_commit" "$sync_state"
printf 'source operations: %s\n' "$source_operations"

if [ "$sync_unknown" = 1 ]; then
  warn "$sync_state; the printed commit is the only evidence of what is being installed"
elif [ -n "$behind" ] && [ "$behind" -gt 0 ]; then
  printf 'ERROR: install-host-access-broker: source checkout is %s commit(s) behind %s\n' \
    "$behind" "$upstream" >&2
  printf '%s\n' \
    "  Installing now would install this checkout's older contract and report success:" \
    "  the success output does not distinguish it from a correct install (#162)." \
    "  Fast-forward first, then re-run:" \
    "    git -C $ROOT merge --ff-only $upstream" \
    "  On a change branch, rebase onto the upstream instead:" \
    "    git -C $ROOT rebase $upstream" >&2
  exit 1
fi

install -d -m 0755 "$LIB_ROOT/aisoft_host_access" "$LIB_ROOT/aisoft_gitea_governance" \
  "$LIBEXEC_ROOT" "$SHARE_ROOT"

CHANGED=0

install_versioned() {
  local source="$1" target="$2" mode="$3"
  if [[ -f "$target" ]] && ! cmp -s "$source" "$target"; then
    install -m "$mode" "$target" "$target.previous"
  fi
  if [[ -f "$target" ]] && cmp -s "$source" "$target"; then
    return
  fi
  install -m "$mode" "$source" "$target"
  CHANGED=1
}

remove_legacy_keychain_helper() {
  local target
  for target in \
    "$LIBEXEC_ROOT/keychain-acl-audit" \
    "$LIBEXEC_ROOT/keychain-acl-audit.previous"; do
    if [[ -e "$target" || -L "$target" ]]; then
      rm -f -- "$target"
      CHANGED=1
    fi
  done
}

for source in "$ROOT"/codex/runtime/aisoft_host_access/*.py; do
  install_versioned "$source" "$LIB_ROOT/aisoft_host_access/$(basename "$source")" 0644
done
for source in "$ROOT"/codex/runtime/aisoft_gitea_governance/*.py; do
  install_versioned "$source" "$LIB_ROOT/aisoft_gitea_governance/$(basename "$source")" 0644
done
install_versioned "$ROOT/codex/runtime/aisoft_change_name.py" \
  "$LIB_ROOT/aisoft_change_name.py" 0644
install_versioned "$ROOT/codex/config/host-access-broker.json" \
  "$SHARE_ROOT/host-access-broker.json" 0644
install_versioned "$ROOT/codex/config/gitea-governance.json" \
  "$SHARE_ROOT/gitea-governance.json" 0644
install_versioned "$ROOT/codex/config/gitea-labels.json" \
  "$SHARE_ROOT/gitea-labels.json" 0644
install_versioned "$ROOT/codex/tools/host-access-broker.sh" \
  "$LIBEXEC_ROOT/host-access-broker" 0755
install_versioned "$ROOT/codex/tools/git-credential-aisoft-host.sh" \
  "$LIBEXEC_ROOT/git-credential-aisoft-host" 0755
install_versioned "$ROOT/codex/tools/project-profile-migration.sh" \
  "$LIBEXEC_ROOT/project-profile-migration" 0755
remove_legacy_keychain_helper

if [[ "$CHANGED" == 1 ]]; then
  printf '%s\n' 'installed host-access-broker/v1 candidate'
else
  printf '%s\n' 'host-access-broker/v1 candidate already current (no-op)'
fi
printf '%s\n' 'no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation was performed'
