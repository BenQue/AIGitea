#!/usr/bin/env bash
# Install only versioned broker candidates. Never bind credentials, profiles, services, or timers.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${AISOFT_HOST_ACCESS_INSTALL_ROOT:-/}"
LIB_ROOT="$INSTALL_ROOT/usr/local/lib/aisoft-host-access"
LIBEXEC_ROOT="$INSTALL_ROOT/usr/local/libexec/aisoft"
SHARE_ROOT="$INSTALL_ROOT/usr/local/share/aisoft"

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
