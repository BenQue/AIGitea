#!/usr/bin/env bash
# Black-box download gates: optimize mode cannot bypass checksum/path checks.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
mkdir -p "$TMP/bin" "$TMP/repo/codex/tests" "$TMP/repo/codex/tools/gitea-pat-helper"
cp "$ROOT/codex/tests/test-gitea-pat-helper-linux.sh" "$TMP/repo/codex/tests/"
cat >"$TMP/bin/uname" <<'SH'
#!/usr/bin/env bash
[[ "$1" == -s ]] && printf 'Linux\n' || printf 'x86_64\n'
SH
cat >"$TMP/bin/curl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
touch "$GATE_CURL_CALLED"
[[ -z "${GATE_CURL_FAIL:-}" ]] || exit 7
previous=''
for value in "$@"; do
  if [[ "$previous" == -o ]]; then cp "$GATE_ARCHIVE" "$value"; exit 0; fi
  previous="$value"
done
exit 2
SH
cat >"$TMP/bin/tar" <<'SH'
#!/usr/bin/env bash
touch "$GATE_TAR_CALLED"
exit 2
SH
chmod +x "$TMP/bin/"*
export GATE_ARCHIVE="$TMP/archive.tar.gz" GATE_TAR_CALLED="$TMP/tar-called" GATE_CURL_CALLED="$TMP/curl-called"
for scenario in checksum traversal; do
  python3 - "$TMP" "$scenario" <<'PY'
import hashlib, io, json, sys, tarfile
from pathlib import Path
root=Path(sys.argv[1])
archive=root/'archive.tar.gz'
with tarfile.open(archive, 'w:gz') as packed:
 member=tarfile.TarInfo('go/../../escape')
 member.size=1
 packed.addfile(member, io.BytesIO(b'x'))
digest='0'*64 if sys.argv[2]=='checksum' else hashlib.sha256(archive.read_bytes()).hexdigest()
(root/'repo/codex/tools/gitea-pat-helper/build-lock.json').write_text(json.dumps({
 'version':'go1.26.3','files':[{'filename':'go1.26.3.linux-amd64.tar.gz','os':'linux','sha256':digest}]}))
PY
  if PATH="$TMP/bin:$PATH" PYTHONOPTIMIZE=1 bash "$TMP/repo/codex/tests/test-gitea-pat-helper-linux.sh" \
      --output "$TMP/no-artifact" >"$TMP/stdout" 2>"$TMP/stderr"; then
    printf '%s\n' 'FAIL: unsafe archive accepted' >&2; exit 1
  fi
  # bash 3.2 does not errexit on a failing [[ ]], so every assertion fails explicitly.
  [[ ! -e "$GATE_TAR_CALLED" && ! -e "$TMP/no-artifact" ]] || fail "$scenario: extracted or built"
  case "$scenario" in
    checksum) rg -q '^TOOLCHAIN_ARCHIVE_MISMATCH$' "$TMP/stderr" ;;
    traversal) rg -q '^TOOLCHAIN_ARCHIVE_UNSAFE$' "$TMP/stderr" ;;
  esac
done
# #370 cache: a pinned cached archive is used without any download, and a cached
# archive that no longer matches the pin is evicted and replaced by a verified one.
CACHE="$TMP/cache"
for scenario in hit evict; do
  rm -rf -- "$CACHE" "$GATE_TAR_CALLED" "$GATE_CURL_CALLED"
  mkdir -p "$CACHE/go-toolchain"
  python3 - "$TMP" "$scenario" <<'PY'
import hashlib, io, json, sys, tarfile
from pathlib import Path
root=Path(sys.argv[1])
archive=root/'archive.tar.gz'
with tarfile.open(archive, 'w:gz') as packed:
 member=tarfile.TarInfo('go/VERSION')
 member.size=8
 packed.addfile(member, io.BytesIO(b'go1.26.3'))
cached=root/'cache/go-toolchain/go1.26.3.linux-amd64.tar.gz'
cached.write_bytes(archive.read_bytes() if sys.argv[2]=='hit' else b'poisoned')
(root/'repo/codex/tools/gitea-pat-helper/build-lock.json').write_text(json.dumps({
 'version':'go1.26.3','files':[{'filename':'go1.26.3.linux-amd64.tar.gz','os':'linux',
 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}]}))
PY
  if [[ "$scenario" == hit ]]; then export GATE_CURL_FAIL=1; else unset GATE_CURL_FAIL; fi
  if PATH="$TMP/bin:$PATH" PYTHONOPTIMIZE=1 AISOFT_CI_DOWNLOAD_CACHE="$CACHE" \
      bash "$TMP/repo/codex/tests/test-gitea-pat-helper-linux.sh" \
      --output "$TMP/no-artifact" >"$TMP/stdout" 2>"$TMP/stderr"; then
    printf '%s\n' 'FAIL: fake tar cannot succeed' >&2; exit 1
  fi
  # Reaching the fake tar means the archive passed the checksum/path gates.
  [[ -e "$GATE_TAR_CALLED" && ! -e "$TMP/no-artifact" ]] || fail "$scenario: verified archive not extracted"
  cmp -s "$GATE_ARCHIVE" "$CACHE/go-toolchain/go1.26.3.linux-amd64.tar.gz" || fail "$scenario: cache not verified archive"
  case "$scenario" in
    hit) rg -q '^TOOLCHAIN_CACHE_HIT$' "$TMP/stdout"; [[ ! -e "$GATE_CURL_CALLED" ]] || fail 'hit: downloaded' ;;
    evict) rg -q '^TOOLCHAIN_CACHE_EVICTED$' "$TMP/stderr"; [[ -e "$GATE_CURL_CALLED" ]] || fail 'evict: not re-downloaded' ;;
  esac
done
# A cache entry that is a symlink or a directory is refused before any download
# or write-back, so nothing lands outside the cache.
for scenario in link dir; do
  rm -rf -- "$CACHE" "$TMP/elsewhere" "$GATE_TAR_CALLED" "$GATE_CURL_CALLED"
  mkdir -p "$CACHE/go-toolchain" "$TMP/elsewhere"
  case "$scenario" in
    link) ln -s "$TMP/elsewhere" "$CACHE/go-toolchain/go1.26.3.linux-amd64.tar.gz" ;;
    dir) mkdir "$CACHE/go-toolchain/go1.26.3.linux-amd64.tar.gz" ;;
  esac
  if PATH="$TMP/bin:$PATH" AISOFT_CI_DOWNLOAD_CACHE="$CACHE" \
      bash "$TMP/repo/codex/tests/test-gitea-pat-helper-linux.sh" \
      --output "$TMP/no-artifact" >"$TMP/stdout" 2>"$TMP/stderr"; then
    fail "$scenario: unsafe cache entry accepted"
  fi
  rg -q '^DOWNLOAD_CACHE_SYMLINK$' "$TMP/stderr" || fail "$scenario: wrong refusal"
  [[ ! -e "$GATE_CURL_CALLED" && -z "$(ls -A "$TMP/elsewhere")" ]] || fail "$scenario: wrote through the entry"
done
printf '%s\n' 'PASS: optimized Linux download checksum/path gates reject before extraction; cache hit skips download, stale cache is evicted, unsafe cache entries are refused'
