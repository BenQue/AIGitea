#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
lib="$root/codex/agent/gitea-token.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

FILE_SENTINEL='sentinel-file-token-3a9c'
INLINE_SENTINEL='sentinel-inline-token-8d4e'

cat >"$test_root/driver.sh" <<'DRIVER'
#!/usr/bin/env bash
set -u
# shellcheck disable=SC1090
source "$LIB_PATH"
rc=0
aisoft_resolve_gitea_token || rc=$?
if [[ "${EXPECT_RC:-0}" != "$rc" ]]; then
  printf 'unexpected rc: got %s want %s\n' "$rc" "${EXPECT_RC:-0}" >&2
  exit 90
fi
if [[ -n "${EXPECT_TOKEN:-}" && "${GITEA_TOKEN:-}" != "$EXPECT_TOKEN" ]]; then
  printf '%s\n' 'unexpected resolved token value' >&2
  exit 91
fi
if [[ "${EXPECT_UNSET:-}" == 1 && -n "${GITEA_TOKEN:-}" ]]; then
  printf '%s\n' 'GITEA_TOKEN should remain unset' >&2
  exit 92
fi
exit 0
DRIVER
chmod 755 "$test_root/driver.sh"

run_case() {
  # usage: run_case <label> [ENV=value ...]
  local label="$1"
  shift
  if ! env -u GITEA_TOKEN -u GITEA_TOKEN_FILE \
    LIB_PATH="$lib" "$@" \
    bash "$test_root/driver.sh" \
    >"$test_root/out" 2>"$test_root/err"; then
    printf 'case failed: %s\n' "$label" >&2
    cat "$test_root/err" >&2
    exit 1
  fi
  if [[ -s "$test_root/out" ]]; then
    printf 'case %s wrote to stdout\n' "$label" >&2
    exit 1
  fi
}

token_file="$test_root/token"
printf '%s\n' "$FILE_SENTINEL" >"$token_file"
chmod 600 "$token_file"

# 1. file-only form (mode 600) resolves silently.
run_case file-600 EXPECT_RC=0 EXPECT_TOKEN="$FILE_SENTINEL" \
  GITEA_TOKEN_FILE="$token_file"
[[ ! -s "$test_root/err" ]]

# 2. file-only form (mode 400) resolves.
chmod 400 "$token_file"
run_case file-400 EXPECT_RC=0 EXPECT_TOKEN="$FILE_SENTINEL" \
  GITEA_TOKEN_FILE="$token_file"
chmod 600 "$token_file"

# 3. file wins over inline; inline value is ignored with a notice.
run_case file-beats-inline EXPECT_RC=0 EXPECT_TOKEN="$FILE_SENTINEL" \
  GITEA_TOKEN_FILE="$token_file" GITEA_TOKEN="$INLINE_SENTINEL"
grep -Fq 'NOTICE: GITEA_TOKEN_FILE is set; ignoring inline GITEA_TOKEN' \
  "$test_root/err"
if grep -Fq 'DEPRECATED' "$test_root/err"; then
  echo 'file form must not print the deprecation notice' >&2
  exit 1
fi

# 4. inline-only form resolves with a deprecation notice.
run_case inline-only EXPECT_RC=0 EXPECT_TOKEN="$INLINE_SENTINEL" \
  GITEA_TOKEN="$INLINE_SENTINEL"
grep -Fq 'DEPRECATED: inline GITEA_TOKEN is deprecated' "$test_root/err"

# 5. neither form -> rc 1, silent.
run_case neither EXPECT_RC=1 EXPECT_UNSET=1
[[ ! -s "$test_root/err" ]]

# 6. permissive mode fails closed even when an inline fallback exists.
chmod 644 "$token_file"
run_case file-permissive EXPECT_RC=20 \
  GITEA_TOKEN_FILE="$token_file" GITEA_TOKEN="$INLINE_SENTINEL"
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE mode must be 400 or 600' \
  "$test_root/err"
chmod 600 "$token_file"

# 7. symlinked token file is rejected.
ln -s "$token_file" "$test_root/token-link"
run_case file-symlink EXPECT_RC=20 GITEA_TOKEN_FILE="$test_root/token-link"
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE must be a regular non-symlink file' \
  "$test_root/err"

# 8. missing token file is rejected.
run_case file-missing EXPECT_RC=20 GITEA_TOKEN_FILE="$test_root/no-such-file"
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE must be a regular non-symlink file' \
  "$test_root/err"

# 9. empty token file is rejected.
: >"$test_root/empty-token"
chmod 600 "$test_root/empty-token"
run_case file-empty EXPECT_RC=20 GITEA_TOKEN_FILE="$test_root/empty-token"
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE is empty' "$test_root/err"

# 10. unsafe charset in the file is rejected.
printf '%s\n' 'bad token with spaces' >"$test_root/bad-token"
chmod 600 "$test_root/bad-token"
run_case file-bad-charset EXPECT_RC=20 GITEA_TOKEN_FILE="$test_root/bad-token"
grep -Fq 'BLOCKED_EXTERNAL: Gitea token format is invalid' "$test_root/err"

# 11. unsafe charset inline is rejected.
run_case inline-bad-charset EXPECT_RC=20 GITEA_TOKEN='bad token'
grep -Fq 'BLOCKED_EXTERNAL: Gitea token format is invalid' "$test_root/err"

# 12. only the first line of a multi-line token file is used.
printf '%s\nsecond-line-must-be-ignored\n' "$FILE_SENTINEL" \
  >"$test_root/multi-token"
chmod 600 "$test_root/multi-token"
run_case file-multiline EXPECT_RC=0 EXPECT_TOKEN="$FILE_SENTINEL" \
  GITEA_TOKEN_FILE="$test_root/multi-token"

# 13. xtrace must not leak token bytes: resolver disables -x before reading.
if ! env -u GITEA_TOKEN -u GITEA_TOKEN_FILE \
  LIB_PATH="$lib" EXPECT_RC=0 EXPECT_TOKEN="$FILE_SENTINEL" \
  GITEA_TOKEN_FILE="$token_file" \
  bash -x "$test_root/driver.sh" \
  >"$test_root/out" 2>"$test_root/err"; then
  echo 'xtrace case failed' >&2
  cat "$test_root/err" >&2
  exit 1
fi
if grep -Fq "$FILE_SENTINEL" "$test_root/out" "$test_root/err"; then
  echo 'token leaked through xtrace or stdout' >&2
  exit 1
fi

printf '%s\n' 'gitea-token lib tests passed'
