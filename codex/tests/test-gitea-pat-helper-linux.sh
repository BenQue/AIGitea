#!/usr/bin/env bash
# Native, pinned Linux build/test only. No installation or live Gitea access.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$(uname -s)" == Linux ]] || { printf '%s\n' 'LINUX_TEST_HOST_REQUIRED' >&2; exit 2; }
[[ $# == 2 && "$1" == --output && "$2" == /* ]] || { printf '%s\n' 'LINUX_TEST_OUTPUT_REQUIRED' >&2; exit 2; }
OUTPUT="$2"
HELPER="$ROOT/codex/tools/gitea-pat-helper"
TMP="$(mktemp -d)"
cleanup() {
  local result=$?
  trap - EXIT
  # Go module directories are read-only. Touch only this mktemp-owned tree,
  # never a caller-supplied GOPATH/GOCACHE, and preserve an earlier failure.
  chmod -R u+w "$TMP" || { if (( result == 0 )); then result=1; fi; }
  rm -rf -- "$TMP" || { if (( result == 0 )); then result=1; fi; }
  exit "$result"
}
trap cleanup EXIT
case "$(uname -m)" in
  x86_64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
  *) printf '%s\n' 'LINUX_TEST_ARCH_UNSUPPORTED' >&2; exit 2 ;;
esac
ARCHIVE="go1.26.3.linux-$ARCH.tar.gz"
python3 -I - "$HELPER/build-lock.json" "$ARCHIVE" >"$TMP/pin" <<'PY'
import json, sys
lock=json.load(open(sys.argv[1]))
pins=[p for p in lock['files'] if p['filename']==sys.argv[2] and p['os']=='linux']
if lock['version']!='go1.26.3' or len(pins)!=1:
 raise SystemExit('TOOLCHAIN_PIN_MISMATCH')
print(pins[0]['sha256'])
PY
# #370: optional persistent download cache owned by the runner user. A cached
# archive is copied first and the copy is what gets verified, so the pin check
# below never trusts a file that can change after it was read.
CACHE="${AISOFT_CI_DOWNLOAD_CACHE:-}"
[[ -z "$CACHE" || "$CACHE" == /* ]] || { printf '%s\n' 'DOWNLOAD_CACHE_PATH_NOT_ABSOLUTE' >&2; exit 2; }
for entry in "$CACHE" "$CACHE/go-toolchain" "$CACHE/go-mod"; do
  [[ -z "$CACHE" || ! -L "$entry" ]] || { printf '%s\n' 'DOWNLOAD_CACHE_SYMLINK' >&2; exit 2; }
done
CACHED_ARCHIVE="${CACHE:+$CACHE/go-toolchain/$ARCHIVE}"
fetch_toolchain() {
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --retry 3 --retry-all-errors --retry-delay 5 \
    --connect-timeout 15 --max-time 300 "https://go.dev/dl/$ARCHIVE" -o "$TMP/$ARCHIVE"
}
FROM_CACHE=0
if [[ -n "$CACHE" && -f "$CACHED_ARCHIVE" && ! -L "$CACHED_ARCHIVE" ]]; then
  cp -- "$CACHED_ARCHIVE" "$TMP/$ARCHIVE"
  if python3 -I -c 'import hashlib,sys; sys.exit(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()!=open(sys.argv[2]).read().strip())' \
      "$TMP/$ARCHIVE" "$TMP/pin"; then
    FROM_CACHE=1
    printf '%s\n' 'TOOLCHAIN_CACHE_HIT'
  else
    printf '%s\n' 'TOOLCHAIN_CACHE_EVICTED' >&2
    rm -f -- "$CACHED_ARCHIVE" "$TMP/$ARCHIVE"
  fi
fi
(( FROM_CACHE )) || fetch_toolchain
python3 -I - "$TMP/$ARCHIVE" "$TMP/pin" <<'PY'
from pathlib import Path, PurePosixPath
import hashlib, sys, tarfile
archive=Path(sys.argv[1])
if hashlib.sha256(archive.read_bytes()).hexdigest()!=Path(sys.argv[2]).read_text().strip():
 raise SystemExit('TOOLCHAIN_ARCHIVE_MISMATCH')
with tarfile.open(archive) as source:
 for member in source:
  parts=PurePosixPath(member.name).parts
  if not (parts and parts[0]=='go' and '..' not in parts and (member.isfile() or member.isdir())):
   raise SystemExit('TOOLCHAIN_ARCHIVE_UNSAFE')
PY
# Only a verified download is written back, via rename inside the cache directory.
if [[ -n "$CACHE" ]] && (( ! FROM_CACHE )); then
  mkdir -p -- "$CACHE/go-toolchain"
  PARTIAL="$(mktemp -- "$CACHE/go-toolchain/.partial.XXXXXXXX")"
  cat -- "$TMP/$ARCHIVE" >"$PARTIAL"
  mv -f -- "$PARTIAL" "$CACHED_ARCHIVE"
fi
tar -xzf "$TMP/$ARCHIVE" -C "$TMP"
export GOROOT="$TMP/go" GOTOOLCHAIN=local GOENV=off GOWORK=off GOFLAGS='' CGO_ENABLED=1
# A CI job uses a private module/build cache unless its isolated caller supplied one.
export GOPATH="${GOPATH:-$TMP/gopath}" GOCACHE="${GOCACHE:-$TMP/go-cache}"
# #370: modules may persist across jobs; the build cache stays private.
[[ -z "$CACHE" || -n "${GOMODCACHE:-}" ]] || export GOMODCACHE="$CACHE/go-mod"
# go.mod/go.sum are the trust anchor for every cached module: filling the cache
# must never record a new hash, so any change to them fails the job.
module_inputs() { python3 -I -c 'import hashlib,sys; print(hashlib.sha256(b"".join(open(f,"rb").read() for f in sys.argv[1:])).hexdigest())' "$HELPER/go.mod" "$HELPER/go.sum"; }
MODULE_INPUTS="$(module_inputs)"
# Fill the module cache first (offline attempt, then up to three online tries),
# so that every later go command can run with GOPROXY=off.
if (cd "$HELPER" && GOPROXY=off "$TMP/go/bin/go" mod download) 2>/dev/null; then
  printf '%s\n' 'GO_MODULE_CACHE_HIT'
else
  for attempt in 1 2 3; do
    if (cd "$HELPER" && "$TMP/go/bin/go" mod download); then break; fi
    (( attempt < 3 )) || { printf '%s\n' 'GO_MODULE_DOWNLOAD_FAILED' >&2; exit 1; }
    sleep 5
  done
  printf '%s\n' 'GO_MODULE_CACHE_FILLED'
fi
[[ "$(module_inputs)" == "$MODULE_INPUTS" ]] || { printf '%s\n' 'GO_MODULE_INPUTS_CHANGED' >&2; exit 1; }
(cd "$HELPER" && "$TMP/go/bin/go" mod verify)
export GOPROXY=off
python3 -I -m unittest discover -s "$HELPER" -p test_build.py
python3 -I "$HELPER/build.py" --go "$TMP/go/bin/go" --toolchain-archive "$TMP/$ARCHIVE" --output "$OUTPUT"
(cd "$HELPER" && "$TMP/go/bin/go" test -mod=readonly -race -tags sqlite,sqlite_unlock_notify ./...)
# Export a synthetic upstream-model DB for an optional disposable-container
# process test; this .test-fixture.db is not a release/installation artifact.
[[ ! -e "$OUTPUT.test-fixture.db" ]] || { printf '%s\n' 'PROCESS_FIXTURE_ALREADY_EXISTS' >&2; exit 2; }
(cd "$HELPER" && AISOFT_HELPER_PROCESS_FIXTURE="$OUTPUT.test-fixture.db" \
  "$TMP/go/bin/go" test -mod=readonly -tags sqlite,sqlite_unlock_notify -run '^TestExportProcessFixture$' ./...)
python3 -I "$ROOT/codex/tests/integration/test-gitea-pat-helper-process.py" --binary "$OUTPUT"
printf '%s\n' 'PASS: pinned native Linux helper build/model/race/process checks (no installation/live)'
