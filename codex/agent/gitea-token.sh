#!/usr/bin/env bash
# Shared Gitea token resolution for platform tools (#111).
#
# Sourced library, never an executable entry point. It does not alter caller
# shell options (-e/-u/pipefail) except disabling xtrace inside the resolver so
# token bytes can never leak through `bash -x`, matching the script-level
# `set +x` contract every consumer already follows.
#
# aisoft_resolve_gitea_token resolution ladder:
#   1. GITEA_TOKEN_FILE set -> security gate: regular non-symlink file, mode
#      400/600 (GNU stat first, BSD fallback), non-empty first line, safe
#      charset. Any violation prints BLOCKED_EXTERNAL to stderr and returns 20
#      WITHOUT falling back to the inline form (fail closed). On success the
#      file's first line overwrites and exports GITEA_TOKEN, returns 0.
#   2. Inline GITEA_TOKEN set -> charset gate, then a deprecation notice on
#      stderr (transitional form until every project profile is migrated to
#      GITEA_IDENTITY + GITEA_TOKEN_FILE), returns 0.
#   3. Neither -> returns 1 silently; callers own the missing-credential
#      wording and exit contract.
#
# Token values only ever reach shell variables; transport must stay on the
# existing curl stdin-config pattern. These functions never write to stdout.

aisoft_gitea_token_blocked() {
  printf 'BLOCKED_EXTERNAL: %s\n' "$1" >&2
  return 20
}

aisoft_resolve_gitea_token() {
  set +x
  local token_file="${GITEA_TOKEN_FILE:-}" token mode
  if [[ -n "$token_file" ]]; then
    if [[ ! -f "$token_file" || -L "$token_file" ]]; then
      aisoft_gitea_token_blocked \
        'GITEA_TOKEN_FILE must be a regular non-symlink file'
      return 20
    fi
    if ! mode="$(stat -c '%a' "$token_file" 2>/dev/null)"; then
      if ! mode="$(stat -f '%Lp' "$token_file" 2>/dev/null)"; then
        aisoft_gitea_token_blocked 'cannot read GITEA_TOKEN_FILE mode'
        return 20
      fi
    fi
    case "$mode" in
      400|600) ;;
      *)
        aisoft_gitea_token_blocked 'GITEA_TOKEN_FILE mode must be 400 or 600'
        return 20
        ;;
    esac
    token="$(<"$token_file")" || token=''
    token="${token%%$'\n'*}"
    if [[ -z "$token" ]]; then
      aisoft_gitea_token_blocked 'GITEA_TOKEN_FILE is empty'
      return 20
    fi
    if [[ ! "$token" =~ ^[A-Za-z0-9._-]+$ ]]; then
      aisoft_gitea_token_blocked 'Gitea token format is invalid'
      return 20
    fi
    if [[ -n "${GITEA_TOKEN:-}" ]]; then
      printf '%s\n' \
        'NOTICE: GITEA_TOKEN_FILE is set; ignoring inline GITEA_TOKEN' >&2
    fi
    GITEA_TOKEN="$token"
    export GITEA_TOKEN
    return 0
  fi
  if [[ -n "${GITEA_TOKEN:-}" ]]; then
    if [[ ! "$GITEA_TOKEN" =~ ^[A-Za-z0-9._-]+$ ]]; then
      aisoft_gitea_token_blocked 'Gitea token format is invalid'
      return 20
    fi
    printf '%s\n' \
      'DEPRECATED: inline GITEA_TOKEN is deprecated; migrate this profile to GITEA_IDENTITY + GITEA_TOKEN_FILE (#61, #111)' >&2
    export GITEA_TOKEN
    return 0
  fi
  return 1
}
