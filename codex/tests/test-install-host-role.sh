#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
export AISOFT_HOST_ROLE_INSTALL_ROOT="$TMP/root"

first="$(bash "$ROOT/codex/install-host-role.sh")"
grep -Fq 'no live host-profile.json' <<<"$first"
manifest_one="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
second="$(bash "$ROOT/codex/install-host-role.sh")"
grep -Fq 'no live host-profile.json' <<<"$second"
manifest_two="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
[[ "$manifest_one" == "$manifest_two" ]]

[[ -x "$TMP/root/usr/local/libexec/aisoft/verify-host-role" ]]
[[ -f "$TMP/root/usr/local/share/aisoft/host-role.schema.json" ]]
[[ -f "$TMP/root/usr/local/share/aisoft/host-capabilities.json" ]]
[[ -f "$TMP/root/etc/aisoft/host-profile.example.json" ]]
[[ ! -e "$TMP/root/etc/aisoft/host-profile.json" ]]
[[ ! -d "$TMP/root/etc/systemd/system" ]]

guard_mode="$(stat -f '%Lp' "$TMP/root/usr/local/libexec/aisoft/verify-host-role" 2>/dev/null ||
  stat -c '%a' "$TMP/root/usr/local/libexec/aisoft/verify-host-role")"
[[ "$guard_mode" == 755 ]]

printf '%s\n' 'host-role installer tests passed'
