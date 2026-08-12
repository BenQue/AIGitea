#!/usr/bin/env bash
set -euo pipefail
set +x

[ "${1:-get}" = get ] || exit 0
: "${AISOFT_CREDENTIAL_USERNAME:?AISOFT_CREDENTIAL_USERNAME is required}"
: "${AISOFT_CREDENTIAL_TOKEN_FILE:?AISOFT_CREDENTIAL_TOKEN_FILE is required}"

mode() {
  local path="$1" actual

  if actual="$(stat -c '%a' "$path" 2>/dev/null)" &&
    [[ "$actual" =~ ^[0-7]{3,4}$ ]]; then
    printf '%s\n' "$actual"
    return 0
  fi
  if actual="$(stat -f '%Lp' "$path" 2>/dev/null)" &&
    [[ "$actual" =~ ^[0-7]{3,4}$ ]]; then
    printf '%s\n' "$actual"
    return 0
  fi
  return 1
}
actual_mode="$(mode "$AISOFT_CREDENTIAL_TOKEN_FILE")" || {
  echo 'credential file mode could not be determined' >&2
  exit 1
}
case "$actual_mode" in 400|600) ;; *) echo "credential file mode must be 400 or 600" >&2; exit 1 ;; esac

token="$(<"$AISOFT_CREDENTIAL_TOKEN_FILE")"
[ -n "$token" ] || { echo "credential file is empty" >&2; exit 1; }
printf 'username=%s\npassword=%s\n' "$AISOFT_CREDENTIAL_USERNAME" "$token"
