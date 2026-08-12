#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
export AISOFT_HOST_ROLE_INSTALL_ROOT="$TMP/root"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

if ! first="$(bash "$ROOT/codex/install-host-role.sh")"; then
  fail 'first host-role installation failed'
fi
grep -Fq 'no live host-profile.json' <<<"$first" ||
  fail 'first install did not preserve the no-live-profile boundary'
manifest_one="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
if ! second="$(bash "$ROOT/codex/install-host-role.sh")"; then
  fail 'second host-role installation failed'
fi
grep -Fq 'no live host-profile.json' <<<"$second" ||
  fail 'second install did not preserve the no-live-profile boundary'
manifest_two="$(
  find "$TMP/root" -type f -print0 |
    sort -z |
    xargs -0 shasum -a 256
)"
[[ "$manifest_one" == "$manifest_two" ]] || fail 'host-role install must be idempotent'

[[ -x "$TMP/root/usr/local/libexec/aisoft/verify-host-role" ]] ||
  fail 'installed guard must be executable'
[[ -f "$TMP/root/usr/local/share/aisoft/host-role.schema.json" ]] ||
  fail 'installed host-role schema is missing'
[[ -f "$TMP/root/usr/local/share/aisoft/host-capabilities.json" ]] ||
  fail 'installed host capability catalog is missing'
[[ -f "$TMP/root/etc/aisoft/host-profile.example.json" ]] ||
  fail 'installed host profile example is missing'
[[ ! -e "$TMP/root/etc/aisoft/host-profile.json" ]] ||
  fail 'installer must not create a live host profile'
[[ ! -d "$TMP/root/etc/systemd/system" ]] ||
  fail 'installer must not create systemd units'

guard_mode="$(stat -c '%a' "$TMP/root/usr/local/libexec/aisoft/verify-host-role" 2>/dev/null ||
  stat -f '%Lp' "$TMP/root/usr/local/libexec/aisoft/verify-host-role")"
[[ "$guard_mode" == 755 ]] || fail "installed guard mode is $guard_mode instead of 755"

printf '%s\n' 'host-role installer tests passed'
