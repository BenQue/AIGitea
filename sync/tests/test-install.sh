#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export AISOFT_SYNC_INSTALL_ROOT="$TMP/root"
first="$(bash "$ROOT/sync/install.sh")"
grep -Fq 'timer remains disabled and inactive' <<<"$first"
manifest_one="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
second="$(bash "$ROOT/sync/install.sh")"
grep -Fq 'timer remains disabled and inactive' <<<"$second"
manifest_two="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
[ "$manifest_one" = "$manifest_two" ]
mode="$(stat -f '%Lp' "$TMP/root/etc/aisoft-sync/keys" 2>/dev/null ||
  stat -c '%a' "$TMP/root/etc/aisoft-sync/keys")"
[ "$mode" = 700 ]
[ ! -e "$TMP/root/etc/systemd/system/timers.target.wants/aisoft-inbound-sync@.timer" ]
grep -Fq 'NoNewPrivileges=true' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
grep -Fq 'ProtectSystem=strict' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
grep -Fq 'ProtectHome=true' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
echo "inbound sync install tests passed"
