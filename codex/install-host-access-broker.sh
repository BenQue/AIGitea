#!/usr/bin/env bash
# Install only versioned broker candidates. Never bind credentials, profiles, services, or timers.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${AISOFT_HOST_ACCESS_INSTALL_ROOT:-/}"
LIB_ROOT="$INSTALL_ROOT/usr/local/lib/aisoft-host-access"
LIBEXEC_ROOT="$INSTALL_ROOT/usr/local/libexec/aisoft"
SHARE_ROOT="$INSTALL_ROOT/usr/local/share/aisoft"
PAT_HELPER_ARTIFACT=''
if [[ $# -gt 0 ]]; then
  [[ $# == 2 && "$1" == --pat-helper-artifact ]] || {
    printf '%s\n' 'BLOCKED_EXTERNAL: only --pat-helper-artifact <pinned Linux binary> is accepted' >&2
    exit 2
  }
  PAT_HELPER_ARTIFACT="$2"
fi

# Source provenance and staleness gate (#162), shared with every other
# installer since #171. The rationale lives with the implementation.
# shellcheck disable=SC1091
source "$ROOT/codex/lib/install-source-guard.sh"

aisoft_install_source_guard install-host-access-broker "$ROOT" \
  operations "$(
    aisoft_install_source_json_count "$ROOT/codex/config/host-access-broker.json" operations
  )"

# Validate optional Linux artifact before any install mutation. Omitted artifact
# leaves rotation fail-closed; ordinary broker installation still works.
ROTATION_METADATA="$(PYTHONPATH="$ROOT/codex/runtime" python3 - "$ROOT" "$PAT_HELPER_ARTIFACT" <<'PY'
import json, sys
from aisoft_host_access.credential_rotation import installation_metadata
try:
    print(json.dumps(installation_metadata(sys.argv[1], sys.argv[2] or None), sort_keys=True))
except Exception:
    print('BLOCKED_EXTERNAL: pinned PAT helper artifact validation failed', file=sys.stderr)
    sys.exit(2)
PY
)" || exit 2

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
install_versioned "$ROOT/codex/runtime/aisoft_worktree_owner.py" \
  "$LIB_ROOT/aisoft_worktree_owner.py" 0644
install_versioned "$ROOT/codex/runtime/aisoft_main_integration.py" \
  "$LIB_ROOT/aisoft_main_integration.py" 0644
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
install_versioned "$ROOT/codex/tools/bootstrap-gitea-service-account.sh" \
  "$LIBEXEC_ROOT/bootstrap-gitea-service-account" 0755
install_versioned "$ROOT/codex/tools/rollback-gitea-routine-pilot.sh" \
  "$LIBEXEC_ROOT/rollback-gitea-routine-pilot" 0755
install_versioned "$ROOT/codex/tools/rotate-gitea-service-account.sh" \
  "$LIBEXEC_ROOT/rotate-gitea-service-account" 0755
if [[ -n "$PAT_HELPER_ARTIFACT" ]]; then
  install_versioned "$PAT_HELPER_ARTIFACT" "$LIBEXEC_ROOT/gitea-pat-helper" 0755
fi
METADATA_FILE="$(mktemp "$SHARE_ROOT/.rotation-source.XXXXXX")"
trap 'rm -f -- "$METADATA_FILE"' EXIT
printf '%s\n' "$ROTATION_METADATA" >"$METADATA_FILE"
install_versioned "$METADATA_FILE" "$SHARE_ROOT/credential-rotation-source.json" 0644
remove_legacy_keychain_helper

if [[ "$CHANGED" == 1 ]]; then
  printf '%s\n' 'installed host-access-broker/v1 candidate'
else
  printf '%s\n' 'host-access-broker/v1 candidate already current (no-op)'
fi
printf '%s\n' 'no credential, Git config, project profile, token, service, timer, VM, merge, or deployment mutation was performed'
