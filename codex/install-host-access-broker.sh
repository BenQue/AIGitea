#!/usr/bin/env bash
# Install only versioned broker candidates. Never bind credentials, profiles, services, or timers.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${AISOFT_HOST_ACCESS_INSTALL_ROOT:-/}"
LIB_ROOT="$INSTALL_ROOT/usr/local/lib/aisoft-host-access"
LIBEXEC_ROOT="$INSTALL_ROOT/usr/local/libexec/aisoft"
SHARE_ROOT="$INSTALL_ROOT/usr/local/share/aisoft"
BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/aisoft-host-access.XXXXXX")"
trap 'rm -rf -- "$BUILD_ROOT"' EXIT

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

for source in "$ROOT"/codex/runtime/aisoft_host_access/*.py; do
  install_versioned "$source" "$LIB_ROOT/aisoft_host_access/$(basename "$source")" 0644
done
for source in "$ROOT"/codex/runtime/aisoft_gitea_governance/*.py; do
  install_versioned "$source" "$LIB_ROOT/aisoft_gitea_governance/$(basename "$source")" 0644
done
/usr/bin/clang -Wall -Wextra -Werror -Wno-deprecated-declarations \
  -fmodules-cache-path="$BUILD_ROOT/module-cache" \
  -framework Security -framework CoreFoundation \
  -o "$BUILD_ROOT/keychain-acl-audit" \
  "$ROOT/codex/runtime/aisoft_host_access/keychain_acl_audit.c"
install_versioned "$BUILD_ROOT/keychain-acl-audit" \
  "$LIBEXEC_ROOT/keychain-acl-audit" 0755
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

if [[ "$CHANGED" == 1 ]]; then
  printf '%s\n' 'installed host-access-broker/v1 candidate'
else
  printf '%s\n' 'host-access-broker/v1 candidate already current (no-op)'
fi
printf '%s\n' 'no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation was performed'
