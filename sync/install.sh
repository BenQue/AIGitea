#!/usr/bin/env bash
set -euo pipefail

SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SOURCE/.." && pwd)"
DEST_ROOT="${AISOFT_SYNC_INSTALL_ROOT:-/}"
RUNTIME_DIR="$DEST_ROOT/opt/aisoft-sync"
CONFIG_DIR="$DEST_ROOT/etc/aisoft-sync"
STATE_DIR="$DEST_ROOT/var/lib/aisoft-sync"
SYSTEMD_DIR="$DEST_ROOT/etc/systemd/system"

# Source provenance and staleness gate (#162, #171, #250). Must stay before the
# first filesystem write below; `install -d` counts as a write. This installer
# writes systemd units and a credential helper, so a stale source is not spent
# on one command's output -- it lands on every later timer-driven sync on the VM.
#
# sync/ ships no version-bearing JSON, so there is no catalog- or matrix-revision
# scalar to print. The readable quantities are file counts instead: they are what
# an operator compares against the two install destinations
# (/etc/systemd/system/aisoft-inbound-sync@* and /opt/aisoft-sync/), while the
# commit line the guard always prints carries which version this is.
# shellcheck disable=SC1091
source "$REPO_ROOT/codex/lib/install-source-guard.sh"

aisoft_install_source_guard sync/install "$REPO_ROOT" \
  units "$(aisoft_install_source_file_count "$SOURCE"/systemd/*)" \
  'runtime scripts' "$(
    aisoft_install_source_file_count \
      "$SOURCE/inbound-sync.sh" "$SOURCE/git-credential-token-file.sh"
  )"

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
