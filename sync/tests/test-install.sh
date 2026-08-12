#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export AISOFT_SYNC_INSTALL_ROOT="$TMP/root"
mkdir -p "$TMP/bin"
real_stat="$(command -v stat)"
probe_file="$TMP/stat-probe"
: >"$probe_file"
chmod 600 "$probe_file"
if real_mode="$("$real_stat" -c '%a' "$probe_file" 2>/dev/null)" &&
  [[ "$real_mode" =~ ^[0-7]{3,4}$ ]]; then
  real_stat_style=gnu
else
  real_stat_style=bsd
fi
export REAL_STAT="$real_stat" REAL_STAT_STYLE="$real_stat_style"
cat >"$TMP/bin/stat" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${AISOFT_TEST_USE_REAL_STAT:-0}" == 1 ]]; then
  exec "$REAL_STAT" "$@"
fi

case "${1:-}" in
  -c)
    [[ "${2:-}" == '%a' && "$#" == 3 ]] || exit 64
    if [[ "$REAL_STAT_STYLE" == gnu ]]; then
      "$REAL_STAT" -c '%a' "$3"
    else
      "$REAL_STAT" -f '%Lp' "$3"
    fi
    ;;
  -f)
    printf 'File: "%s"\nID: deadbeef Namelen: 255 Type: fake\n' "${3:-unknown}"
    ;;
  *) exit 64 ;;
esac
MOCK
chmod +x "$TMP/bin/stat"
export PATH="$TMP/bin:$PATH"

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
mode="$(stat -c '%a' "$TMP/root/etc/aisoft-sync/keys" 2>/dev/null ||
  stat -f '%Lp' "$TMP/root/etc/aisoft-sync/keys")"
[ "$mode" = 700 ]
[ ! -e "$TMP/root/etc/systemd/system/timers.target.wants/aisoft-inbound-sync@.timer" ]
grep -Fq 'NoNewPrivileges=true' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
grep -Fq 'ProtectSystem=strict' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
grep -Fq 'ProtectHome=true' \
  "$TMP/root/etc/systemd/system/aisoft-inbound-sync@.service"
echo "inbound sync install tests passed"
