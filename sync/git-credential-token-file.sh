#!/usr/bin/env bash
set -euo pipefail
set +x

[ "${1:-get}" = get ] || exit 0
: "${AISOFT_CREDENTIAL_USERNAME:?AISOFT_CREDENTIAL_USERNAME is required}"
: "${AISOFT_CREDENTIAL_TOKEN_FILE:?AISOFT_CREDENTIAL_TOKEN_FILE is required}"

mode() {
  stat -f '%Lp' "$1" 2>/dev/null || stat -c '%a' "$1"
}
actual_mode="$(mode "$AISOFT_CREDENTIAL_TOKEN_FILE")"
case "$actual_mode" in 400|600) ;; *) echo "credential file mode must be 400 or 600" >&2; exit 1 ;; esac

token="$(<"$AISOFT_CREDENTIAL_TOKEN_FILE")"
[ -n "$token" ] || { echo "credential file is empty" >&2; exit 1; }
printf 'username=%s\npassword=%s\n' "$AISOFT_CREDENTIAL_USERNAME" "$token"
