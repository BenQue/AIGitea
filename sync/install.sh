#!/usr/bin/env bash
set -euo pipefail

SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="${AISOFT_SYNC_INSTALL_ROOT:-/}"
RUNTIME_DIR="$DEST_ROOT/opt/aisoft-sync"
CONFIG_DIR="$DEST_ROOT/etc/aisoft-sync"
STATE_DIR="$DEST_ROOT/var/lib/aisoft-sync"
SYSTEMD_DIR="$DEST_ROOT/etc/systemd/system"

install -d -m 0755 "$RUNTIME_DIR" "$CONFIG_DIR" "$SYSTEMD_DIR"
install -d -m 0700 "$CONFIG_DIR/keys" "$STATE_DIR"
install -m 0755 "$SOURCE/inbound-sync.sh" "$RUNTIME_DIR/inbound-sync.sh"
install -m 0755 "$SOURCE/git-credential-token-file.sh" \
  "$RUNTIME_DIR/git-credential-token-file.sh"
install -m 0644 "$SOURCE/templates/project.env.example" \
  "$CONFIG_DIR/project.env.example"
install -m 0644 "$SOURCE/systemd/aisoft-inbound-sync@.service" \
  "$SYSTEMD_DIR/aisoft-inbound-sync@.service"
install -m 0644 "$SOURCE/systemd/aisoft-inbound-sync@.timer" \
  "$SYSTEMD_DIR/aisoft-inbound-sync@.timer"

echo "installed inbound sync runtime; timer remains disabled and inactive"
