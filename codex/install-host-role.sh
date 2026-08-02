#!/usr/bin/env bash
# Install the credential-free host-role guard and contract. No live profile is created.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${AISOFT_HOST_ROLE_INSTALL_ROOT:-/}"
LIBEXEC_DIR="$INSTALL_ROOT/usr/local/libexec/aisoft"
SHARE_DIR="$INSTALL_ROOT/usr/local/share/aisoft"
CONFIG_DIR="$INSTALL_ROOT/etc/aisoft"

install -d -m 0755 "$LIBEXEC_DIR" "$SHARE_DIR" "$CONFIG_DIR"
install -m 0755 "$ROOT/codex/tools/verify-host-role.sh" \
  "$LIBEXEC_DIR/verify-host-role"
install -m 0644 "$ROOT/codex/config/host-role.schema.json" \
  "$SHARE_DIR/host-role.schema.json"
install -m 0644 "$ROOT/codex/config/host-capabilities.json" \
  "$SHARE_DIR/host-capabilities.json"
install -m 0644 "$ROOT/templates/hosts/host-profile.example.json" \
  "$CONFIG_DIR/host-profile.example.json"

printf '%s\n' 'installed host-role guard, schema, catalog and example'
printf '%s\n' 'no live host-profile.json, credential, service, timer or deployment action was created'
